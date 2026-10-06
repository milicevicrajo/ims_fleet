"""Nazivi konta i otvaranje konta po dubini (od 05.10.2026.).

Kontni plan se čita iz izvora (`{SOURCE}.konto`, samo SELECT) i pamti u kešu: ima nazive za sve
nivoe — klasa (5), grupa (52), sintetika (520) i konto (52000). Knjiženja su na punom kontu.
Kada izvor nije dostupan, koriste se nazivi sa knjiženja (`LedgerEntry.account_name`), pa zbirni
nivoi ostaju bez naziva, ali izveštaj radi.
"""
import logging

from django.conf import settings
from django.core.cache import cache
from django.db import connections

from .source import SOURCE

logger = logging.getLogger(__name__)

# Nivo → naziv. „5” je pun konto (analitika, kako je knjiženo; može imati i 6 cifara).
NIVOI = (("1", "Klasa"), ("2", "Grupa"), ("3", "Sintetika"), ("5", "Konto"))
TRAJANJE_KESA = 6 * 60 * 60


def nazivi_konta(company=None):
    """{konto: naziv} za sve nivoe kontnog plana."""
    company = company or getattr(settings, "FINANSIJE_COMPANY", 1)
    kljuc = f"finansije:kontni_plan:{company}"
    plan = cache.get(kljuc)
    if plan is not None:
        return plan
    try:
        alias = getattr(settings, "FINANSIJE_SOURCE_DB", "server_db")
        with connections[alias].cursor() as cursor:
            cursor.execute(f"SELECT knt, naz_knt FROM {SOURCE}.konto WHERE sif_pred=%s", [company])
            plan = {str(k or "").strip(): " ".join(str(n or "").split()) for k, n in cursor.fetchall() if str(k or "").strip()}
    except Exception:  # izvor nedostupan ili nije podešen (npr. testovi): nazivi sa knjiženja
        logger.warning("Kontni plan iz izvora nije dostupan; koriste se nazivi sa knjiženja.")
        from finansije.models import LedgerEntry

        plan = dict(LedgerEntry.objects.filter(company=company).order_by().exclude(account_name="")
                    .values_list("account", "account_name").distinct())
        cache.set(kljuc, plan, 5 * 60)  # ponovni pokušaj izvora za 5 minuta
        return plan
    cache.set(kljuc, plan, TRAJANJE_KESA)
    return plan


def naziv_konta(code, plan, rezerva=""):
    return plan.get(code) or rezerva or ""


def nivo_konta(filters):
    """Nivo grupisanja: izabran, ili jedan nivo dublje od početka konta u filteru."""
    izabran = filters.get("nivo")
    if izabran:
        return izabran
    pocetak = filters.get("account") or ""
    if filters.get("account_exact"):
        return "5"
    return next((nivo for nivo, _ in NIVOI if nivo != "5" and int(nivo) > len(pocetak)), "5")


def sledeci_nivo(nivo):
    redosled = [n for n, _ in NIVOI]
    return redosled[redosled.index(nivo) + 1] if nivo in redosled and nivo != "5" else None


def putanja_konta(pocetak, plan):
    """Za „5”, „52”, „520”: [(5, RASHODI), (52, …), (520, …)] — nivoi kroz koje se otvaralo."""
    return [(pocetak[:duzina], naziv_konta(pocetak[:duzina], plan))
            for duzina in (1, 2, 3, 5, 6) if len(pocetak) >= duzina and (duzina < 5 or len(pocetak) == duzina)]
