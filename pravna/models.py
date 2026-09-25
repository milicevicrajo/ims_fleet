from django.conf import settings
from django.db import models


class Postupak(models.Model):
    """
    Univerzalni model za pravne postupke.
    Različiti tipovi koriste različite podskupove polja.
    Polja partnera (naziv u bazi, mesto, PIB) se vuku dinamički iz Partneri tabele.
    """

    TIP_CHOICES = [
        ('tuzeni', 'Tuženi'),
        ('tuzili', 'Tužili'),
        ('stecaj', 'Stečaj'),
        ('uppr', 'UPPR'),
    ]

    VALUTA_CHOICES = [
        ('RSD', 'RSD'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
    ]

    tip = models.CharField(max_length=20, choices=TIP_CHOICES, default='tuzeni', db_index=True)

    # --- Zajednička polja ---
    sud = models.CharField(max_length=255, blank=True, null=True, verbose_name='Sud')
    broj_predmeta = models.CharField(max_length=100, blank=True, null=True, verbose_name='Broj predmeta')
    sifra_partnera = models.IntegerField(blank=True, null=True, db_index=True, verbose_name='Šifra partnera')
    naziv_partnera = models.CharField(max_length=255, blank=True, null=True, verbose_name='Naziv partnera')
    valuta = models.CharField(max_length=10, choices=VALUTA_CHOICES, default='RSD', verbose_name='Valuta')
    osnovni_dug = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name='Osnovni dug (glavnica)')
    arhivirano = models.BooleanField(default=False, verbose_name='Arhivirano')

    # --- Tuženi ---
    izvrsiteljski_broj = models.CharField(max_length=100, blank=True, null=True, verbose_name='Izvršiteljski broj')
    datum_pokretanja = models.DateField(blank=True, null=True, verbose_name='Datum pokretanja postupka')
    predmet_spora = models.TextField(blank=True, null=True, verbose_name='Predmet spora')

    # --- Tužili ---
    tuzilac = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tužilac')
    vrednost_spora = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name='Vrednost spora')
    datum_podnosenja_tuzbe = models.DateField(blank=True, null=True, verbose_name='Datum podnošenja tužbe')

    # --- Stečaj ---
    vece = models.CharField(max_length=100, blank=True, null=True, verbose_name='Veće')
    kamata = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name='Kamata')
    troskovi = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name='Troškovi')
    ukupan_dug = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name='Ukupan dug')
    datum_otvaranja_stecaja = models.DateField(blank=True, null=True, verbose_name='Datum otvaranja stečajnog postupka')
    prijava_potrazivanja = models.TextField(blank=True, null=True, verbose_name='Prijava potraživanja')

    # --- UPPR ---
    novi_broj = models.CharField(max_length=100, blank=True, null=True, verbose_name='Novi broj')
    pib = models.CharField(max_length=20, blank=True, null=True, verbose_name='PIB')

    # --- Meta ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='postupci_kreirani',
    )

    class Meta:
        db_table = 'postupak'
        verbose_name = 'Postupak'
        verbose_name_plural = 'Postupci'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tip_display()} - {self.naziv_partnera or self.sifra_partnera} ({self.broj_predmeta or 'bez broja'})"


class PromenaPostupka(models.Model):
    """Istorija promena za postupak"""

    postupak = models.ForeignKey(
        Postupak,
        on_delete=models.CASCADE,
        related_name='promene',
        verbose_name='Postupak',
    )
    datum = models.DateField(verbose_name='Datum')
    promena = models.TextField(verbose_name='Promena')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='promene_postupaka',
    )

    class Meta:
        db_table = 'promena_postupka'
        verbose_name = 'Promena postupka'
        verbose_name_plural = 'Promene postupaka'
        ordering = ['-datum', '-created_at']

    def __str__(self):
        return f"{self.datum} - {self.promena[:50]}..."


def centar_zaposlenog(zaposleni):
    """Centar se izvodi iz organizacione jedinice zaposlenog, pa se pamti na postupku."""
    from core.models import OrganizationalUnit

    from fleet.services.employee_user_profiles import infer_center
    code = str(getattr(zaposleni, 'org_unit_code', '') or getattr(zaposleni, 'department_code', '') or '').strip()
    if not code:
        return ''
    exact = OrganizationalUnit.objects.filter(code=code).values_list('center', flat=True).first()
    return str(exact or '').strip() or infer_center(code)[0]


class DisciplinskiPostupak(models.Model):
    """Disciplinski postupak protiv zaposlenog, zatvoren izborom mere i datuma."""

    class Mera(models.TextChoices):
        OPOMENA = '1', 'Pisana opomena'
        UDALJENJE = '2', 'Udaljenje sa rada bez naknade zarade od 1 do 15 radnih dana'
        NOVCANA = '3', 'Novčana kazna do 20% osnovne zarade za mesec u kome je izrečena, u trajanju do 3 meseca'
        PRESTANAK = '4', 'Prestanak radnog odnosa'

    zaposleni = models.ForeignKey(
        'fleet.Employee',
        on_delete=models.PROTECT,
        related_name='disciplinski_postupci',
        verbose_name='Zaposleni',
    )
    # Centar se predlaže iz OJ zaposlenog, ali ostaje zapisan kakav je bio na dan zahteva.
    centar = models.CharField(max_length=10, blank=True, verbose_name='Centar')
    datum_podnosenja = models.DateField(verbose_name='Datum podnošenja zahteva')
    podnosilac = models.ForeignKey(
        'fleet.Employee',
        on_delete=models.PROTECT,
        related_name='podneti_disciplinski_postupci',
        verbose_name='Podnosilac',
    )

    mera_datum = models.DateField(blank=True, null=True, verbose_name='Datum disciplinske mere')
    mera_opis = models.TextField(blank=True, verbose_name='Disciplinska mera')
    mera_vrsta = models.CharField(max_length=1, choices=Mera.choices, blank=True, verbose_name='Izrečena mera')

    arhivirano = models.BooleanField(default=False, verbose_name='Arhivirano')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='disciplinski_postupci_kreirani',
    )

    class Meta:
        verbose_name = 'Disciplinski postupak'
        verbose_name_plural = 'Disciplinski postupci'
        ordering = ['-datum_podnosenja', '-id']
        indexes = [
            models.Index(fields=['centar'], name='pravna_disc_centar_idx'),
            models.Index(fields=['datum_podnosenja'], name='pravna_disc_datum_idx'),
        ]

    def __str__(self):
        return f"Disciplinski postupak - {self.zaposleni} ({self.datum_podnosenja:%d.%m.%Y.})"

    @property
    def zatvoren(self):
        return self.mera_datum is not None

    @property
    def datum_statusa(self):
        return self.mera_datum or self.datum_podnosenja

    def save(self, *args, **kwargs):
        if not self.centar and self.zaposleni_id:
            self.centar = centar_zaposlenog(self.zaposleni)
        super().save(*args, **kwargs)


class TokPostupka(models.Model):
    """Jedan zapis u toku disciplinskog postupka."""

    postupak = models.ForeignKey(
        DisciplinskiPostupak,
        on_delete=models.CASCADE,
        related_name='tok',
        verbose_name='Disciplinski postupak',
    )
    datum = models.DateField(verbose_name='Datum')
    opis = models.TextField(verbose_name='Opis')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tok_disciplinskih_postupaka',
    )

    class Meta:
        verbose_name = 'Tok postupka'
        verbose_name_plural = 'Tok postupka'
        ordering = ['datum', 'id']

    def __str__(self):
        return f"{self.datum:%d.%m.%Y.} - {self.opis[:50]}"
