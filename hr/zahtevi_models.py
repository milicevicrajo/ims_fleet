"""Zahtevi za izdavanje kadrovskih rešenja.

Tok je zahtev → rešenje: rešenje nastaje iz zahteva, preuzima njegove podatke i dobija
broj kao podbroj zahteva (`43-17/1`). Jedan zahtev se odnosi na jednog zaposlenog; za više
zaposlenih pravi se više istih zahteva odjednom, i svaki dobija svoj broj.

Brojevi se dodeljuju automatski i nikad se ne koriste ponovo, pa se zahtev ne briše,
nego stornira.
"""
from django.conf import settings
from django.db import models

from .resenja_models import Pismo, ResenjeDan, VrstaResenja


class VrstaZahteva(models.Model):
    """Obrazac zahteva. Tekstovi se čuvaju ćirilicom, kao kod vrsta rešenja."""

    kod = models.SlugField(max_length=40, unique=True, verbose_name='Oznaka')
    naziv = models.CharField(max_length=120, verbose_name='Naziv vrste (za listu)')
    predmet = models.CharField(max_length=255, verbose_name='Predmet (ćirilica)')
    tekst = models.TextField(verbose_name='Tekst zahteva (ćirilica)',
        help_text='Svaki pasus u svom redu. Čuvari mesta kao kod rešenja, uz {razlog}, {podnosilac}, '
                  '{podnosilac_funkcija}, {odobrava}, {odobrava_funkcija} i dodatna polja.')
    vrsta_resenja = models.ForeignKey(VrstaResenja, on_delete=models.PROTECT, null=True, blank=True,
        related_name='vrste_zahteva', verbose_name='Rešenje koje se izdaje po zahtevu')
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
        verbose_name = 'Vrsta zahteva'
        verbose_name_plural = 'Vrste zahteva'

    def __str__(self):
        return self.naziv


class BrojacZahteva(models.Model):
    """Poslednji dodeljeni redni broj zahteva u godini. Red se zaključava pri dodeli."""

    godina = models.PositiveSmallIntegerField(unique=True, verbose_name='Godina')
    poslednji_broj = models.PositiveIntegerField(default=0, verbose_name='Poslednji dodeljeni broj')

    class Meta:
        ordering = ['-godina']
        verbose_name = 'Brojač zahteva'
        verbose_name_plural = 'Brojači zahteva'

    def __str__(self):
        return f'{self.godina}: {self.poslednji_broj}'


class Zahtev(models.Model):
    class Status(models.TextChoices):
        NACRT = 'nacrt', 'Nacrt'
        PODNET = 'podnet', 'Podnet'
        STORNIRAN = 'storniran', 'Storniran'

    vrsta = models.ForeignKey(VrstaZahteva, on_delete=models.PROTECT, related_name='zahtevi', verbose_name='Vrsta zahteva')
    godina = models.PositiveSmallIntegerField(verbose_name='Godina')
    redni_broj = models.PositiveIntegerField(verbose_name='Redni broj')
    broj = models.CharField(max_length=40, verbose_name='Broj zahteva',
        help_text='Jedinstven u godini, kao u delovodniku: redni broj počinje od 1 svake godine.')
    datum_zahteva = models.DateField(verbose_name='Datum zahteva')
    pismo = models.CharField(max_length=10, choices=Pismo.choices, default=Pismo.CIRILICA, verbose_name='Pismo')
    zaposleni = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='zahtevi',
        verbose_name='Zaposleni')
    pol = models.CharField(max_length=1, choices=[('M', 'Muški'), ('F', 'Ženski')], blank=True,
        verbose_name='Pol za tekst zahteva')
    zaposleni_tekst = models.CharField(max_length=200, verbose_name='Zaposleni u tekstu zahteva',
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
    razlog = models.TextField(blank=True, verbose_name='Razlog zahteva',
        help_text='Npr. „потребе за радом већим од четрдесет сати недељно“. Ulazi u tekst zahteva i rešenja.')
    dodatni_podaci = models.JSONField(default=dict, blank=True, verbose_name='Dodatni podaci')
    podnosilac = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='podneti_zahtevi',
        verbose_name='Ko podnosi zahtev')
    podnosilac_funkcija = models.CharField(max_length=120, blank=True, verbose_name='Funkcija podnosioca',
        help_text='Npr. „Финансијски директор“, „Директор центра“.')
    odobrava = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='zahtevi_za_odobrenje',
        verbose_name='Ko odobrava zahtev')
    odobrava_funkcija = models.CharField(max_length=120, blank=True, default='Генерални директор',
        verbose_name='Funkcija onoga ko odobrava')
    napomena = models.TextField(blank=True, verbose_name='Interna napomena')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.NACRT, verbose_name='Status')
    dokument = models.JSONField(null=True, blank=True, verbose_name='Snimak dokumenta')
    podneto_at = models.DateTimeField(null=True, blank=True, verbose_name='Podneto')
    poslednji_podbroj = models.PositiveSmallIntegerField(default=0, verbose_name='Poslednji podbroj rešenja')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='uneti_zahtevi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-datum_zahteva', '-redni_broj']
        verbose_name = 'Zahtev'
        verbose_name_plural = 'Zahtevi'
        constraints = [
            models.UniqueConstraint(fields=['godina', 'redni_broj'], name='hr_zahtev_godina_redni_broj'),
            models.UniqueConstraint(fields=['godina', 'broj'], name='hr_zahtev_godina_broj'),
            models.CheckConstraint(check=models.Q(datum_do__isnull=True) | models.Q(datum_od__isnull=True)
                | models.Q(datum_do__gte=models.F('datum_od')), name='hr_zahtev_period'),
        ]

    def __str__(self):
        return f'Zahtev {self.broj} — {self.zaposleni}'

    @property
    def je_zakljucan(self):
        return self.status != self.Status.NACRT


class ZahtevDan(models.Model):
    zahtev = models.ForeignKey(Zahtev, on_delete=models.CASCADE, related_name='dani', verbose_name='Zahtev')
    datum = models.DateField(verbose_name='Datum')
    vrsta_dana = models.CharField(max_length=15, choices=ResenjeDan.VrstaDana.choices,
        default=ResenjeDan.VrstaDana.PREKOVREMENI, verbose_name='Vrsta dana')

    class Meta:
        ordering = ['datum', 'pk']
        verbose_name = 'Dan zahteva'
        verbose_name_plural = 'Dani zahteva'
        constraints = [models.UniqueConstraint(fields=['zahtev', 'datum', 'vrsta_dana'], name='hr_zahtev_dan_key')]

    def __str__(self):
        return f'{self.datum:%d.%m.%Y}. — {self.get_vrsta_dana_display()}'
