"""SEF — Sistem elektronskih faktura (efaktura.mfin.gov.rs), od 30.09.2026.

Finansije **samo citaju** ulazne i izlazne fakture sa SEF-a kroz njegov API (`finansije/services/sef.py`);
nista ne salju, ne prihvataju i ne odbijaju. Sa knjizenjima se fakture vezuju **meko, preko broja
dokumenta** (`LedgerEntry.document_reference`), bez stranog kljuca.
"""
import re

from django.conf import settings
from django.db import models

# Izlazna faktura na SEF-u nosi ispred broja iz knjizenja jos cetiri cifre (godina + serija):
# SEF `2650707001-325` = IF knjizenje `707001-325` (sifra posla + redni broj), provereno 30.09.2026.
IZLAZNI_PREFIKS = re.compile(r"^\d{4}(\d{6}-\d+)$")
DUZINA_BROJA_KNJIZENJA = 20  # LedgerEntry.document_reference


def kljuc_broja(broj):
    """Broj dokumenta za poredjenje: bez razmaka na krajevima i velikim slovima."""
    return (broj or "").strip().upper()


def broj_u_knjizenju(broj):
    """Oblik broja kakav stoji u knjizenju: izlazna bez cetiri cifre ispred, inace skracen na 20 znakova."""
    kljuc = kljuc_broja(broj)
    izlazni = IZLAZNI_PREFIKS.match(kljuc)
    return izlazni.group(1) if izlazni else kljuc[:DUZINA_BROJA_KNJIZENJA]


class SefFaktura(models.Model):
    class Smer(models.TextChoices):
        ULAZNA = "ulazna", "Ulazna"
        IZLAZNA = "izlazna", "Izlazna"

    smer = models.CharField(max_length=10, choices=Smer.choices, db_index=True)
    sef_id = models.BigIntegerField(verbose_name="ID na SEF-u")
    glob_uniq_id = models.CharField(max_length=64, blank=True, default="")
    broj = models.CharField(max_length=100, blank=True, default="", verbose_name="Broj dokumenta")
    broj_kljuc = models.CharField(max_length=100, blank=True, default="", db_index=True, editable=False)
    # Oblik broja u knjizenju (meka veza): filter „proknjizene” poredi ovo i ceo broj sa `document_reference`.
    broj_knjizenja = models.CharField(max_length=100, blank=True, default="", editable=False)
    vrsta = models.CharField(max_length=30, blank=True, default="", verbose_name="Vrsta dokumenta")
    status = models.CharField(max_length=30, blank=True, default="", db_index=True)
    cir_id = models.CharField(max_length=40, blank=True, default="", verbose_name="CRF identifikator")
    partner_naziv = models.CharField(max_length=255, blank=True, default="", verbose_name="Partner")
    partner_pib = models.CharField(max_length=20, blank=True, default="", db_index=True, verbose_name="PIB partnera")
    partner_mb = models.CharField(max_length=20, blank=True, default="", verbose_name="Matični broj partnera")
    iznos = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    osnovica = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    pdv = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    valuta = models.CharField(max_length=3, blank=True, default="")
    datum_izdavanja = models.DateField(null=True, blank=True)
    datum_prometa = models.DateField(null=True, blank=True)
    datum_dospeca = models.DateField(null=True, blank=True)
    datum_slanja = models.DateTimeField(null=True, blank=True, db_index=True)
    izmenjeno_na_sefu = models.DateTimeField(null=True, blank=True)
    sinhronizovano = models.DateTimeField()
    # PDF sa SEF-a, preuzet pri prvom otvaranju detalja (SEF ga prvi put tek pripremi).
    pdf = models.FileField(upload_to="finansije/sef/%Y/%m/", max_length=255, blank=True)
    pdf_preuzet = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "finansije_sef_faktura"
        ordering = ["-datum_slanja", "-sef_id"]
        constraints = [models.UniqueConstraint(fields=["smer", "sef_id"], name="fin_sef_faktura_kljuc")]
        verbose_name = "SEF faktura"
        verbose_name_plural = "SEF fakture"

    def __str__(self):
        return f"{self.get_smer_display()} {self.broj or self.sef_id}"

    def save(self, *args, **kwargs):
        self.broj_kljuc = kljuc_broja(self.broj)
        self.broj_knjizenja = broj_u_knjizenju(self.broj) if self.broj_kljuc else ""
        super().save(*args, **kwargs)


class SefPromena(models.Model):
    """Promena statusa sa SEF-a (`.../changes`), kako je SEF prijavi, radi istorije."""
    smer = models.CharField(max_length=10, choices=SefFaktura.Smer.choices)
    event_id = models.BigIntegerField()
    sef_id = models.BigIntegerField(db_index=True)
    datum = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, blank=True, default="")
    komentar = models.TextField(blank=True, default="")

    class Meta:
        db_table = "finansije_sef_promena"
        ordering = ["-datum", "-event_id"]
        constraints = [models.UniqueConstraint(fields=["smer", "event_id"], name="fin_sef_promena_kljuc")]


class SefSinhronizacija(models.Model):
    STATUS = [("running", "U toku"), ("success", "Uspešno"), ("error", "Greška"), ("stopped", "Zaustavljeno")]
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="running")
    korisnik = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="+")
    od = models.DateField()
    do = models.DateField()
    counts = models.JSONField(default=dict)
    error = models.TextField(blank=True, default="")
    # Korisnik je trazio zaustavljanje; preuzimanje staje posle koraka koji upravo radi.
    zaustavi = models.BooleanField(default=False)

    class Meta:
        db_table = "finansije_sef_sinhronizacija"
        ordering = ["-started_at", "-pk"]
