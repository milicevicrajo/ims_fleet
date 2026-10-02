"""Nazivi organizacionih jedinica iz kadrovske baze (`ob_jedin` na PUTGEO-SERVER.bazaldims).

Kadrovska baza vodi spisak OJ sa oznakom `aktivan` ('D' / 'N') po godini i preduzeću. Aktivne
OJ tekuće godine su drugi pouzdan izvor naziva jedinice registra, posle Pravilnika o organizaciji
(`importer._naziv_jedinice`). Ovde se samo čita; ništa se ne upisuje u kadrovsku bazu.
"""
from django.db import DatabaseError, connections, transaction
from django.utils import timezone

IZVOR = "[putgeo-server].[BazaLDIMS].[dbo]"
NAPOMENA = "Naziv: kadrovska baza, aktivna OJ"


def _alias(using=None):
    from hr.sync import _resolve_hr_db_alias

    return _resolve_hr_db_alias(using)


def procitaj_aktivne(company=1, godina=None, using=None):
    """{šifra OJ: naziv} za aktivne OJ godine. Greška baze se prosleđuje pozivaocu."""
    godina = godina or timezone.localdate().year
    with connections[_alias(using)].cursor() as cursor:
        cursor.execute(f"SELECT oj, naz_oj FROM {IZVOR}.[ob_jedin] WHERE god = %s AND sif_pred = %s AND aktivan = 'D'",
                       [str(godina), company])
        redovi = cursor.fetchall()
    return {str(oj).strip(): " ".join(str(naziv or "").split()) for oj, naziv in redovi if str(oj or "").strip()}


def nazivi_ili_none(company=1, using=None):
    """Kao `procitaj_aktivne`, ali None kada kadrovska baza nije dostupna (registar tada zadržava
    već upisane nazive). Čitanje ide u sopstvenoj tački čuvanja, da greška ne pokvari transakciju."""
    try:
        with transaction.atomic(using=_alias(using)):
            return procitaj_aktivne(company, using=using)
    except DatabaseError:
        return None
