"""Kadrovska rešenja: šifrarnik vrsta i izdata rešenja sa nepromenljivim snimkom.

Tekstovi u šifrarniku se čuvaju ćirilicom, jer je preslovljavanje ćirilica → latinica
jednoznačno (`hr.services.evaluations.latin`), dok je obrnut smer dvosmislen zbog
digrafa lj, nj i dž. Rešenje koje se štampa latinicom nastaje preslovljavanjem pri
izradi dokumenta, a ne drugim skupom tekstova u šifrarniku.
"""
from django.conf import settings
from django.db import models


class Pismo(models.TextChoices):
    CIRILICA = 'cirilica', 'Ćirilica'
    LATINICA = 'latinica', 'Latinica'


class VrstaResenja(models.Model):
    """Jedan obrazac rešenja. Kadrovik ga uređuje bez izmene koda."""

    kod = models.SlugField(max_length=40, unique=True, verbose_name='Oznaka')
    naziv = models.CharField(max_length=120, verbose_name='Naziv vrste (za listu)')
    naslov = models.CharField(max_length=120, default='РЕШЕЊЕ', verbose_name='Naslov (ćirilica)')
    podnaslov = models.CharField(max_length=255, blank=True, verbose_name='Podnaslov (ćirilica)')
    pravni_osnov = models.TextField(verbose_name='Pravni osnov (ćirilica)')
    dispozitiv = models.TextField(verbose_name='Dispozitiv (ćirilica)',
        help_text='Svaka tačka u svom redu. Čuvari mesta: {zaposleni}, {oj}, {radno_mesto}, {centar}, '
                  '{period}, {dani}, {dani_vikend}, {dani_drzavni}, {dani_verski}, {radni_dani}, {datum_povratka}. '
                  'Oblik po polu: {rod:дужан|дужна}. Uslovni deo: [[dani_verski| и {dani_verski} на дан верског празника]].')
    obrazlozenje = models.TextField(blank=True, verbose_name='Obrazloženje (ćirilica)',
        help_text='Čuvari mesta: {zahtev_broj}, {zahtev_datum}, {razlog_zahteva}, {podnosilac}, '
                  '{podnosilac_funkcija}, {napomena} i dodatna polja.')
    pravna_pouka = models.TextField(blank=True, verbose_name='Pravna pouka (ćirilica)')
    dostavljeno = models.TextField(blank=True, verbose_name='Dostavljeno (ćirilica)',
        help_text='Svaka stavka u svom redu. Čuvar mesta {centar} daje šifru centra zaposlenog.')
    trazi_period = models.BooleanField(default=False, verbose_name='Traži period od–do')
    trazi_dane = models.BooleanField(default=False, verbose_name='Traži pojedinačne dane')
    trazi_radne_dane = models.BooleanField(default=False, verbose_name='Traži broj radnih dana i povratak')
    dodatna_polja = models.TextField(blank=True, verbose_name='Dodatna polja',
        help_text='Svako polje u svom redu, u obliku oznaka|Naziv polja (npr. poslovi|Poslovi koje preuzima). '
                  'U tekstu se koristi kao {oznaka}.')
    podrazumevano_pismo = models.CharField(max_length=10, choices=Pismo.choices, default=Pismo.CIRILICA,
        verbose_name='Podrazumevano pismo')
    redosled = models.PositiveSmallIntegerField(default=0, verbose_name='Redosled')
    je_aktivna = models.BooleanField(default=True, verbose_name='Aktivna')

    class Meta:
        ordering = ['redosled', 'naziv']
        verbose_name = 'Vrsta rešenja'
        verbose_name_plural = 'Vrste rešenja'

    def __str__(self):
        return self.naziv


class Potpisnik(models.Model):
    """Ko potpisuje rešenja i u kom periodu. Period važenja čuva stara rešenja tačnim."""

    zaposleni = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='potpisi_resenja',
        verbose_name='Zaposleni')
    funkcija = models.CharField(max_length=120, default='Генерални директор', verbose_name='Funkcija (ćirilica)')
    ime_cirilica = models.CharField(max_length=150, blank=True, verbose_name='Ime u potpisu (ćirilica)',
        help_text='Npr. „др Драган Бојовић, дипл.инж.“. Ostavi prazno za automatsko preslovljavanje.')
    vazi_od = models.DateField(verbose_name='Važi od')
    vazi_do = models.DateField(null=True, blank=True, verbose_name='Važi do (isključivo)')

    class Meta:
        ordering = ['-vazi_od', 'pk']
        verbose_name = 'Potpisnik rešenja'
        verbose_name_plural = 'Potpisnici rešenja'

    def __str__(self):
        return f'{self.funkcija} — {self.zaposleni}'

    @classmethod
    def za_datum(cls, dan):
        return (cls.objects.filter(vazi_od__lte=dan)
                .filter(models.Q(vazi_do__isnull=True) | models.Q(vazi_do__gt=dan))
                .select_related('zaposleni').order_by('-vazi_od').first())


class Resenje(models.Model):
    class Status(models.TextChoices):
        NACRT = 'nacrt', 'Nacrt'
        IZDATO = 'izdato', 'Izdato'
        STORNIRANO = 'stornirano', 'Stornirano'

    zaposleni = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='resenja',
        verbose_name='Zaposleni')
    vrsta = models.ForeignKey(VrstaResenja, on_delete=models.PROTECT, related_name='resenja', verbose_name='Vrsta rešenja')
    zahtev = models.ForeignKey('hr.Zahtev', on_delete=models.PROTECT, related_name='resenja',
        verbose_name='Zahtev')
    podbroj = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Podbroj zahteva')
    broj = models.CharField(max_length=40, verbose_name='Broj rešenja',
        help_text='Rešenje dobija broj automatski, kao podbroj zahteva (npr. 43-17/1).')
    datum_resenja = models.DateField(verbose_name='Datum rešenja')
    pismo = models.CharField(max_length=10, choices=Pismo.choices, default=Pismo.CIRILICA, verbose_name='Pismo')
    pol = models.CharField(max_length=1, choices=[('M', 'Muški'), ('F', 'Ženski')], blank=True,
        verbose_name='Pol za tekst rešenja')
    zaposleni_tekst = models.CharField(max_length=200, verbose_name='Zaposleni u tekstu rešenja',
        help_text='Popunjava se automatski; ispravi ručno kada je potreban drugi padež.')
    oj_naziv = models.CharField(max_length=200, blank=True, verbose_name='Organizaciona jedinica u tekstu')
    radno_mesto = models.CharField(max_length=200, blank=True, verbose_name='Radno mesto u tekstu')
    oj_kod = models.CharField(max_length=20, blank=True, verbose_name='Šifra OJ')
    centar = models.CharField(max_length=10, blank=True, verbose_name='Šifra centra')
    datum_od = models.DateField(null=True, blank=True, verbose_name='Period od')
    datum_do = models.DateField(null=True, blank=True, verbose_name='Period do')
    vreme_od = models.TimeField(null=True, blank=True, verbose_name='Vreme rada od')
    vreme_do = models.TimeField(null=True, blank=True, verbose_name='Vreme rada do')
    do_zavrsetka_posla = models.BooleanField(default=False, verbose_name='Do završetka posla')
    broj_radnih_dana = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Broj radnih dana')
    datum_povratka = models.DateField(null=True, blank=True, verbose_name='Datum javljanja na posao')
    zahtev_broj = models.CharField(max_length=255, blank=True, verbose_name='Zahtev (broj ili opis)')
    zahtev_datum = models.DateField(null=True, blank=True, verbose_name='Datum zahteva')
    potpisnik = models.ForeignKey(Potpisnik, on_delete=models.PROTECT, null=True, blank=True, related_name='resenja',
        verbose_name='Potpisnik')
    napomena = models.TextField(blank=True, verbose_name='Napomena uz obrazloženje')
    dodatni_podaci = models.JSONField(default=dict, blank=True, verbose_name='Dodatni podaci')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.NACRT, verbose_name='Status')
    dokument = models.JSONField(null=True, blank=True, verbose_name='Snimak dokumenta')
    izdato_at = models.DateTimeField(null=True, blank=True, verbose_name='Izdato')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='izdata_resenja')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-datum_resenja', '-pk']
        verbose_name = 'Rešenje'
        verbose_name_plural = 'Rešenja'
        constraints = [
            models.UniqueConstraint(fields=['zahtev'], name='hr_resenje_jedan_po_zahtevu'),
            models.UniqueConstraint(fields=['broj', 'datum_resenja'], name='hr_resenje_broj_datum'),
            models.CheckConstraint(check=models.Q(datum_do__isnull=True) | models.Q(datum_od__isnull=True)
                | models.Q(datum_do__gte=models.F('datum_od')), name='hr_resenje_period'),
        ]

    def __str__(self):
        return f'{self.vrsta.naziv} {self.broj} — {self.zaposleni}'

    @property
    def je_zakljucano(self):
        return self.status != self.Status.NACRT


class ResenjeDan(models.Model):
    class VrstaDana(models.TextChoices):
        PREKOVREMENI = 'prekovremeni', 'Prekovremeni rad'
        NOCNI = 'nocni', 'Noćni rad'
        VIKEND = 'vikend', 'Rad vikendom'
        DRZAVNI_PRAZNIK = 'drzavni', 'Državni praznik'
        VERSKI_PRAZNIK = 'verski', 'Verski praznik'
        ODSUSTVO = 'odsustvo', 'Plaćeno odsustvo'

    resenje = models.ForeignKey(Resenje, on_delete=models.CASCADE, related_name='dani', verbose_name='Rešenje')
    datum = models.DateField(verbose_name='Datum')
    vrsta_dana = models.CharField(max_length=15, choices=VrstaDana.choices, default=VrstaDana.PREKOVREMENI,
        verbose_name='Vrsta dana')

    class Meta:
        ordering = ['datum', 'pk']
        verbose_name = 'Dan rešenja'
        verbose_name_plural = 'Dani rešenja'
        constraints = [models.UniqueConstraint(fields=['resenje', 'datum', 'vrsta_dana'], name='hr_resenje_dan_key')]

    def __str__(self):
        return f'{self.datum:%d.%m.%Y}. — {self.get_vrsta_dana_display()}'
