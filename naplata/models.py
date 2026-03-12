from django.db import models
from django.conf import settings

# Create your models here.
class Kontakti(models.Model):
    id = models.AutoField(primary_key=True)  # Automatski ID
    sif_par = models.IntegerField()  # Više kontakata može imati istu šifru partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    kontakt = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    email = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomena = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kontakti'



class Napomene(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(db_column='naz_par', max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomene = models.CharField(db_column='napomene', max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    veliki = models.CharField(db_column='veliki', max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'napomene'


class Opomene(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    god = models.IntegerField(blank=True, null=True)
    br_opomene = models.IntegerField(blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    iznos = models.FloatField(blank=True, null=True)
    fakture = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomene = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'opomene'



class PozivPismo(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    god = models.IntegerField(blank=True, null=True)
    br_pisma = models.IntegerField(blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    iznos = models.FloatField(blank=True, null=True)
    fakture = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomene = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'poziv_pismo'


class PoziviTel(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    napomena = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pozivi_tel'


class SifBaket(models.Model):
    br_kategorije = models.FloatField(blank=True, null=True)
    baket = models.FloatField(blank=True, null=True)
    baket_rang = models.FloatField(blank=True, null=True)
    opis = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    akcija = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sif_baket'


class SifKategorija(models.Model):
    br_kategorije = models.FloatField(blank=True, null=True)
    kategorija = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sif_kategorija'


class Tuzbe(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    god = models.IntegerField(blank=True, null=True)
    br_opomene = models.IntegerField(blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    iznos = models.FloatField(blank=True, null=True)
    fakture = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomene = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tuzbe'


# <!-- ======================================================================= -->
#                            <!-- VIEWS IZ BAZA NAPLATA -->
# <!-- ======================================================================= -->

# View za bazu dugovanja
class Baza(models.Model):
    god = models.IntegerField()
    sif_par = models.IntegerField()
    naz_par = models.CharField(max_length=255)
    sif_vrs = models.CharField(max_length=50, blank=True, null=True)
    br_naloga = models.IntegerField()
    dat_naloga = models.DateTimeField()
    stavka = models.IntegerField()
    vez_dok = models.CharField(max_length=255, blank=True, null=True)
    datum = models.DateTimeField()
    oj = models.IntegerField()
    dpo = models.DateTimeField()
    kom = models.CharField(max_length=255, blank=True, null=True)
    skr_naz = models.CharField(max_length=255, blank=True, null=True)
    deviza = models.CharField(max_length=50, blank=True, null=True)
    promena = models.DecimalField(max_digits=15, decimal_places=2)
    stavka_k = models.CharField(max_length=255, blank=True, null=True)
    d_p = models.CharField(max_length=10, blank=True, null=True)
    knt = models.CharField(max_length=255, blank=True, null=True)
    dug = models.DecimalField(max_digits=15, decimal_places=2)  # Zamenjuje "saldo"
    pot = models.DecimalField(max_digits=15, decimal_places=2)
    sif_pos = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'baza'


# View za dodelu baketa
class DodelaBucketa(models.Model):
    sif_par = models.IntegerField()
    naz_par = models.CharField(max_length=255)
    vez_dok = models.CharField(max_length=255, blank=True, null=True)
    sif_pos = models.CharField(max_length=255, blank=True, null=True)
    duguje = models.DecimalField(max_digits=15, decimal_places=2)
    potrazuje = models.DecimalField(max_digits=15, decimal_places=2)
    saldo = models.DecimalField(max_digits=15, decimal_places=2)
    dpo = models.DateTimeField()
    danasnji_datum = models.DateTimeField()
    broj_dana = models.IntegerField()
    baket = models.FloatField()  # Ovo određuje koji je bucket
    kategorija = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dodela_bucketa'



# View za ispravke
class Ispravke(models.Model):
    god = models.IntegerField()
    sif_par = models.IntegerField()
    naz_par = models.CharField(max_length=255)
    sif_vrs = models.CharField(max_length=50, blank=True, null=True)
    br_naloga = models.IntegerField()
    dat_naloga = models.DateTimeField()
    stavka = models.IntegerField()
    vez_dok = models.CharField(max_length=255, blank=True, null=True)
    datum = models.DateTimeField()
    oj = models.IntegerField()
    dpo = models.DateTimeField()
    kom = models.CharField(max_length=255, blank=True, null=True)
    skr_naz = models.CharField(max_length=255, blank=True, null=True)
    deviza = models.CharField(max_length=50, blank=True, null=True)
    promena = models.DecimalField(max_digits=15, decimal_places=2)
    stavka_k = models.CharField(max_length=255, blank=True, null=True)
    d_p = models.CharField(max_length=10, blank=True, null=True)
    knt = models.CharField(max_length=255, blank=True, null=True)
    naz_knt = models.CharField(max_length=255, blank=True, null=True)
    dug = models.DecimalField(max_digits=15, decimal_places=2)
    pot = models.DecimalField(max_digits=15, decimal_places=2)
    sif_pos = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ispravke'



# View za partnere
class Partneri(models.Model):
    sif_pred = models.IntegerField()
    grupa = models.IntegerField()
    sif_par = models.IntegerField()
    naz_par = models.CharField(max_length=255)
    ulica_par = models.CharField(max_length=255, blank=True, null=True)
    p_b_par = models.CharField(max_length=50, blank=True, null=True)  # Poštanski broj
    mesto_par = models.CharField(max_length=255, blank=True, null=True)
    zr = models.CharField(max_length=255, blank=True, null=True)  # Žiro račun
    mb = models.CharField(max_length=255, blank=True, null=True)  # Matični broj
    telefon = models.CharField(max_length=255, blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    lice = models.CharField(max_length=255, blank=True, null=True)  # Kontakt osoba
    web = models.CharField(max_length=255, blank=True, null=True)
    proc_rabata = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    br_dana = models.IntegerField(blank=True, null=True)
    vlasnik = models.CharField(max_length=255, blank=True, null=True)
    pib = models.CharField(max_length=50, blank=True, null=True)
    zemlja = models.CharField(max_length=50, blank=True, null=True)
    proc_rabata1 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    proc_rabata2 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    pdv_obveznik = models.CharField(max_length=50, blank=True, null=True)
    sif_ter = models.CharField(max_length=255, blank=True, null=True)
    JBKJS = models.CharField(max_length=255, blank=True, null=True)
    CRF = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'partneri'


class AvansKlijent(models.Model):
    sif_par = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'avans_klijent'
        verbose_name = 'Avans klijent'
        verbose_name_plural = 'Avans klijenti'


# <!-- ======================================================================= -->
#                            <!-- PRAVNA SLUŽBA -->
# <!-- ======================================================================= -->

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

