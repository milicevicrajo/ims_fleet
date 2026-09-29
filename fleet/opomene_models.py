"""Opomene vozačima za nepravilno unetu kilometražu pri točenju (od 29.09.2026.).

Jedan zapis je jedno točenje (NIS ili OMV) sa nepravilnošću: kilometraža nije uneta, manja je od
prethodnog točenja, nerealan skok ili ista kao prethodni put. Opomena ide samo vozaču — onom sa
putnog naloga za taj dan, a ako naloga nema, onom ko je zadužio vozilo. Za sada je samo opomena
(bez ispravke). Logika: `fleet/support/opomene.py`.
"""
from django.db import models


class OpomenaGoriva(models.Model):
    class Izvor(models.TextChoices):
        NIS = "nis", "NIS"
        OMV = "omv", "OMV"

    class Vrsta(models.TextChoices):
        BEZ_KM = "bez_km", "Kilometraža nije uneta"
        MANJA = "manja", "Manja od prethodnog točenja"
        SKOK = "skok", "Nerealan skok kilometraže"
        ISTA = "ista", "Ista kao prethodno točenje"

    class Status(models.TextChoices):
        ZA_SLANJE = "za_slanje", "Pripremljena"
        POSLATA = "poslata", "Poslata"
        BEZ_VOZACA = "bez_vozaca", "Vozač nije poznat"
        BEZ_KONTAKTA = "bez_kontakta", "Vozač nema kontakt"
        GRESKA = "greska", "Greška pri slanju"

    izvor = models.CharField(max_length=5, choices=Izvor.choices)
    transakcija_id = models.BigIntegerField(verbose_name="Točenje (ID u tabeli izvora)")
    vehicle = models.ForeignKey("fleet.Vehicle", on_delete=models.CASCADE, related_name="opomene_goriva", verbose_name="Vozilo")
    vreme_tocenja = models.DateTimeField(verbose_name="Vreme točenja")
    stanica = models.CharField(max_length=255, blank=True, default="", verbose_name="Stanica")
    kolicina = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Količina (l)")
    vrsta = models.CharField(max_length=10, choices=Vrsta.choices, db_index=True, verbose_name="Nepravilnost")
    uneta_km = models.IntegerField(null=True, blank=True, verbose_name="Uneta kilometraža")
    prethodna_km = models.IntegerField(null=True, blank=True, verbose_name="Prethodno točenje (km)")
    prethodni_datum = models.DateField(null=True, blank=True, verbose_name="Prethodno točenje (datum)")
    employee = models.ForeignKey("fleet.Employee", on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="opomene_goriva", verbose_name="Vozač")
    vozac_izvor = models.CharField(max_length=120, blank=True, default="", verbose_name="Odakle je vozač")
    poruka = models.TextField(verbose_name="Tekst opomene")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ZA_SLANJE, db_index=True)
    kanal = models.CharField(max_length=20, blank=True, default="", verbose_name="Kanal")
    poslato = models.DateTimeField(null=True, blank=True, verbose_name="Poslato")
    greska = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "fleet"
        db_table = "fleet_opomena_goriva"
        ordering = ["-vreme_tocenja", "-pk"]
        constraints = [models.UniqueConstraint(fields=["izvor", "transakcija_id"], name="fleet_opomena_jedno_tocenje")]
        verbose_name = "Opomena za gorivo"
        verbose_name_plural = "Opomene za gorivo"

    def __str__(self):
        return f"{self.get_vrsta_display()} · {self.vehicle_id} · {self.vreme_tocenja:%d.%m.%Y}"
