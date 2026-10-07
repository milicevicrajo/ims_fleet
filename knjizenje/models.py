"""Knjiženje (od 07.10.2026.): dokumenti koje drugi moduli šalju na knjiženje i podaci o njihovom knjiženju.

Za sada samo fiskalni računi iz Isplata (sa putnih naloga i ostali). Isplate račun šalju; knjigovodstvo ga
proknjižava ili vraća na doradu. Ništa se ne upisuje u knjigovodstvo starog ERP-a — ovde se samo pamti
ko je, kada i pod kojim nalogom za knjiženje račun proknjižio.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class KnjizenjeRacuna(models.Model):
    """Jedan zapis po fiskalnom računu, od slanja do knjiženja. `FiskalniRacun.proknjizeno` je oznaka koja
    zaključava račun (Nabavka, putni nalog) i drži se usklađenom sa statusom."""

    class Status(models.TextChoices):
        POSLATO = "poslato", _("Čeka knjiženje")
        VRACENO = "vraceno", _("Vraćeno na doradu")
        PROKNJIZENO = "proknjizeno", _("Proknjiženo")

    racun = models.OneToOneField("nabavka.FiskalniRacun", on_delete=models.CASCADE, related_name="knjizenje",
                                 verbose_name=_("Fiskalni račun"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.POSLATO, db_index=True,
                              verbose_name=_("Status"))
    poslao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="+", verbose_name=_("Poslao na knjiženje"))
    poslato_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Poslato na knjiženje"))
    datum_knjizenja = models.DateField(null=True, blank=True, verbose_name=_("Datum knjiženja"))
    broj_naloga = models.CharField(max_length=50, blank=True, default="", verbose_name=_("Broj naloga za knjiženje"))
    napomena = models.CharField(max_length=500, blank=True, default="", verbose_name=_("Napomena knjiženja"))
    knjizio = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="+", verbose_name=_("Proknjižio"))
    proknjizeno_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Proknjiženo (upis)"))
    razlog_vracanja = models.CharField(max_length=500, blank=True, default="", verbose_name=_("Razlog vraćanja"))
    vratio = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="+", verbose_name=_("Vratio na doradu"))
    vraceno_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Vraćeno na doradu"))

    class Meta:
        verbose_name = _("Knjiženje računa")
        verbose_name_plural = _("Knjiženja računa")

    def __str__(self):
        return f"{self.racun_id} · {self.get_status_display()}"


class DogadjajKnjizenja(models.Model):
    """Istorija: slanje, vraćanje na doradu, knjiženje i poništavanje — sa korisnikom i napomenom."""

    class Vrsta(models.TextChoices):
        POSLATO = "poslato", _("Poslato na knjiženje")
        VRACENO = "vraceno", _("Vraćeno na doradu")
        PROKNJIZENO = "proknjizeno", _("Proknjiženo")
        PONISTENO = "ponisteno", _("Poništeno knjiženje")

    knjizenje = models.ForeignKey(KnjizenjeRacuna, on_delete=models.CASCADE, related_name="dogadjaji",
                                  verbose_name=_("Knjiženje"))
    vrsta = models.CharField(max_length=20, choices=Vrsta.choices, verbose_name=_("Vrsta"))
    korisnik = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="+", verbose_name=_("Korisnik"))
    vreme = models.DateTimeField(default=timezone.now, verbose_name=_("Vreme"))
    napomena = models.CharField(max_length=500, blank=True, default="", verbose_name=_("Napomena"))

    class Meta:
        ordering = ["-vreme", "-pk"]
        verbose_name = _("Događaj knjiženja")
        verbose_name_plural = _("Događaji knjiženja")
