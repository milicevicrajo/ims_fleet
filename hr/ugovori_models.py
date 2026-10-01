"""Ugovori zaposlenih (Kadrovi → Ugovori, od 29.09.2026.).

Jedan red je jedan period rada iz kadrovske baze (`dbo.v_hr_RadStaz` → `RadStaz` na
PUTGEO-SERVER.bazaldims), kljuc je sifra radnika + redni broj. Sinhronizacija
(`hr/services/ugovori.py`) menja samo polja iz izvora; ono sto Kadrovi unesu ne dira.

OJ i radno mesto po sistematizaciji (sifre i nazivi) upisuju se kada se red prvi put pojavi,
iz trenutnog stanja radnika u kadrovskoj bazi, i posle se sami ne menjaju — ostaju kao istorija.
Kadrovi ih mogu rucno ispraviti.

Radnik moze da radi na vise radnih mesta: ta polja na ugovoru su prvo (glavno) radno mesto i
njega uzimaju izvestaji, a druga i dalja unose Kadrovi rucno (`DodatnoRadnoMesto`, za
bezbednost i zdravlje na radu). Sinhronizacija ih ne dira.
"""
import datetime

from django.conf import settings
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

# Kadrovska baza period na neodredjeno vodi sa datumom 01.01.3000.
NEODREDJENO_OD_GODINE = 2999


class UgovoriSinhronizacija(models.Model):
    """Zapis svake sinhronizacije ugovora (nocne i rucne): kada, ko i sa kojim brojevima."""
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="hr_ugovori_sinhronizacije")
    counts = models.JSONField(default=dict)

    class Meta:
        db_table = "hr_ugovori_sinhronizacija"
        ordering = ["-created_at", "-pk"]
        verbose_name = "Sinhronizacija ugovora zaposlenih"


class UgovorZaposlenog(models.Model):
    class Kategorija(models.TextChoices):
        RADNI_ODNOS = "radni_odnos", "Radni odnos"
        VAN_RADNOG_ODNOSA = "van_radnog_odnosa", "Van radnog odnosa"

    class Poreklo(models.TextChoices):
        SINHRONIZACIJA = "sinhronizacija", "Iz kadrovske baze"
        RUCNO = "rucno", "Uneto ručno"

    # --- iz izvora (menja samo sinhronizacija) ---
    employee_code = models.IntegerField(verbose_name="Šifra radnika")
    redni_broj = models.IntegerField(verbose_name="Redni broj perioda")
    employee = models.ForeignKey("fleet.Employee", null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="ugovori", verbose_name="Zaposleni")
    ime_prezime = models.CharField(max_length=150, blank=True, default="", verbose_name="Ime i prezime (kadrovska baza)")
    kategorija = models.CharField(max_length=20, choices=Kategorija.choices, default=Kategorija.RADNI_ODNOS,
                                  db_index=True, verbose_name="Kategorija")
    datum_od = models.DateField(verbose_name="Od")
    datum_do = models.DateField(null=True, blank=True, verbose_name="Do")
    na_neodredjeno = models.BooleanField(default=False, verbose_name="Na neodređeno")
    opis = models.CharField(max_length=255, blank=True, default="", verbose_name="Opis iz kadrovske baze")
    staz_godina = models.PositiveSmallIntegerField(null=True, blank=True)
    staz_meseci = models.PositiveSmallIntegerField(null=True, blank=True)
    staz_dana = models.PositiveSmallIntegerField(null=True, blank=True)
    u_izvoru = models.BooleanField(default=True, db_index=True, verbose_name="Postoji u kadrovskoj bazi")
    radnik_aktivan = models.BooleanField(default=False, db_index=True, verbose_name="Radnik aktivan")
    # Datum pocetka se promenio posle unosa (red je u izvoru prenumerisan ili izmenjen) — proveriti.
    prethodni_datum_od = models.DateField(null=True, blank=True, verbose_name="Raniji datum početka")
    sinhronizovano = models.DateTimeField(null=True, blank=True)

    # --- OJ i radno mesto: zabelezeno jednom, posle se ne menja samo ---
    oj = models.CharField(max_length=20, blank=True, default="", verbose_name="OJ")
    naziv_oj = models.CharField(max_length=255, blank=True, default="", verbose_name="Naziv OJ")
    sifra_sistematizacije = models.CharField(max_length=20, blank=True, default="", verbose_name="Šifra po sistematizaciji")
    naziv_radnog_mesta = models.CharField(max_length=255, blank=True, default="", verbose_name="Naziv radnog mesta")
    podaci_poreklo = models.CharField(max_length=20, choices=Poreklo.choices, blank=True, default="",
                                      verbose_name="Poreklo OJ i radnog mesta")
    podaci_zabelezeni = models.DateField(null=True, blank=True, verbose_name="OJ i radno mesto zabeleženi")

    # --- unose Kadrovi ---
    broj_ugovora = models.CharField(max_length=100, blank=True, default="", db_index=True, verbose_name="Broj ugovora")
    datum_ugovora = models.DateField(null=True, blank=True, verbose_name="Datum ugovora")
    broj_aneksa = models.CharField(max_length=100, blank=True, default="", verbose_name="Broj aneksa")
    glavni_ugovor = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                      related_name="aneksi", verbose_name="Glavni ugovor")
    dokument = models.FileField(upload_to="hr/ugovori/%Y/%m/", max_length=255, blank=True, verbose_name="Skeniran dokument")
    dokument_naziv = models.CharField(max_length=255, blank=True, default="", verbose_name="Naziv fajla")
    napomena = models.TextField(blank=True, default="", verbose_name="Napomena")
    izmenio = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="hr_ugovori_izmenjeni", verbose_name="Izmenio")
    izmenjeno = models.DateTimeField(null=True, blank=True, verbose_name="Izmenjeno")

    class Meta:
        db_table = "hr_ugovor_zaposlenog"
        ordering = ["employee_code", "redni_broj"]
        constraints = [models.UniqueConstraint(fields=["employee_code", "redni_broj"], name="hr_ugovor_izvor_kljuc")]
        indexes = [models.Index(fields=["employee_code", "datum_od"])]
        verbose_name = "Ugovor zaposlenog"
        verbose_name_plural = "Ugovori zaposlenih"

    def __str__(self):
        broj = self.broj_ugovora or f"period {self.redni_broj}"
        return f"{self.employee_code} · {broj} · {self.datum_od:%d.%m.%Y}"

    @property
    def je_aneks(self):
        return bool(self.broj_aneksa)

    @property
    def unet(self):
        """Kadrovi su uneli broj ugovora ili dokument."""
        return bool(self.broj_ugovora or self.dokument)

    @property
    def staz(self):
        delovi = [(self.staz_godina, "g"), (self.staz_meseci, "m"), (self.staz_dana, "d")]
        return " ".join(f"{v} {o}" for v, o in delovi if v) or ""

    @staticmethod
    def datum_do_iz_izvora(vrednost):
        """(datum_do, na_neodredjeno) iz datuma kadrovske baze (01.01.3000. = na neodređeno)."""
        if vrednost is None:
            return None, False
        if isinstance(vrednost, datetime.datetime):
            vrednost = vrednost.date()
        if vrednost.year >= NEODREDJENO_OD_GODINE:
            return None, True
        return vrednost, False

    def save(self, *args, **kwargs):
        stari = None
        if self.pk:
            stari = type(self).objects.filter(pk=self.pk).values_list("dokument", flat=True).first()
        super().save(*args, **kwargs)
        if stari and stari != (self.dokument.name if self.dokument else ""):
            _obrisi_fajl_posle(self._meta.get_field("dokument").storage, stari)


class DodatnoRadnoMesto(models.Model):
    """Drugo i dalje radno mesto istog perioda (za BZR). Izvestaji uzimaju prvo — polja na ugovoru."""
    ugovor = models.ForeignKey(UgovorZaposlenog, on_delete=models.CASCADE, related_name="dodatna_radna_mesta",
                               verbose_name="Ugovor")
    oj = models.CharField(max_length=20, blank=True, default="", verbose_name="OJ")
    naziv_oj = models.CharField(max_length=255, blank=True, default="", verbose_name="Naziv OJ")
    sifra_sistematizacije = models.CharField(max_length=20, blank=True, default="", verbose_name="Šifra po sistematizaciji")
    naziv_radnog_mesta = models.CharField(max_length=255, blank=True, default="", verbose_name="Naziv radnog mesta")

    class Meta:
        db_table = "hr_ugovor_dodatno_radno_mesto"
        ordering = ["ugovor", "pk"]
        verbose_name = "Dodatno radno mesto"
        verbose_name_plural = "Dodatna radna mesta"

    def __str__(self):
        return f"{self.sifra_sistematizacije} {self.naziv_radnog_mesta}".strip()


def _obrisi_fajl_posle(storage, ime):
    transaction.on_commit(lambda: storage.delete(ime) if storage.exists(ime) else None)


@receiver(post_delete, sender=UgovorZaposlenog)
def obrisi_dokument_ugovora(sender, instance, **kwargs):
    if instance.dokument:
        _obrisi_fajl_posle(instance.dokument.storage, instance.dokument.name)
