"""Izvodi banke (od 06.11.2026.): spisak izvoda za banku i godinu iz pogleda `dbo.v_izvodi_banka`, samo SELECT.

Pogled (vlasnik: knjigovodstvo, u bazi IMS_ERP) sabira stavke konta 24100 partnera grupe 11 po godini, datumu,
broju naloga i partneru, od 2026. Čita lokalnu kopiju `nalog_z` (osvežava je `sp_AzurirajNalogZ` u 10:00 i 11:00),
ne udaljeni izvor — izvodi knjiženi posle poslednjeg osvežavanja još se ne vide.
"""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.db import connections
from django.utils import timezone

PRVA_GODINA = 2026  # pogled ima samo god >= 2026
ZERO = Decimal("0.00")


@dataclass
class Izvod:
    datum: date
    broj_naloga: str
    duguje: Decimal
    potrazuje: Decimal


def godine():
    return list(range(timezone.localdate().year, PRVA_GODINA - 1, -1))


def godina(tekst):
    """Izabrana godina iz zahteva; van ponuđenih — tekuća."""
    try:
        broj = int(tekst)
    except (TypeError, ValueError):
        return timezone.localdate().year
    return broj if broj in godine() else timezone.localdate().year


def izvodi(sifra_banke, god):
    alias = getattr(settings, "FINANSIJE_SOURCE_DB", "server_db")
    with connections[alias].cursor() as cursor:
        cursor.execute(
            "SELECT datum, br_naloga, duguje, potrazuje FROM dbo.v_izvodi_banka "
            "WHERE sif_par=%s AND god=%s ORDER BY datum, br_naloga", [sifra_banke, str(god)])
        redovi = cursor.fetchall()
    return [Izvod(datum=d.date() if isinstance(d, datetime) else d, broj_naloga=str(broj).strip() if broj is not None else "",
                  duguje=duguje or ZERO, potrazuje=potrazuje or ZERO) for d, broj, duguje, potrazuje in redovi]


def zbir(spisak):
    return {"broj": len(spisak), "duguje": sum((i.duguje for i in spisak), ZERO),
            "potrazuje": sum((i.potrazuje for i in spisak), ZERO)}
