"""Radna mesta zaposlenog iz kadrovske baze (od 07.10.2026.), samo čitanje izvora.

Radnik u starom programu može biti raspoređen na do pet ravnopravnih radnih mesta: `radnik.sif_sis` i
`sif_sis1`–`sif_sis4`, uz OJ u `oj` i `oj1`–`oj4` (`oj1`–`oj4` su uglavnom prazne — tada važi `oj`).
Nazivi radnih mesta su u `Sistemat` (po preduzeću), nazivi OJ u `ob_jedin` (po godini).
Rezultat se upisuje u `Employee.radna_mesta` pri sinhronizaciji Kadrova, redom kao u izvoru (1–5).
"""
from collections import defaultdict

from django.db import connections
from django.utils import timezone

from hr.models import Employee
from hr.services.ugovori import IZVOR, OJ_SQL, SISTEMATIZACIJA_SQL, _ceo, _nazivi_oj, _tekst

RADNA_MESTA_SQL = (f"SELECT sif_pred, rasif, oj, sif_sis, oj1, sif_sis1, oj2, sif_sis2, oj3, sif_sis3, oj4, sif_sis4 "
                   f"FROM {IZVOR}.[radnik]")


def _sifra(vrednost):
    tekst = _tekst(vrednost)
    return "" if tekst in ("", "0") else tekst


def radna_mesta(redovi, oj_redovi, sistematizacija, danas=None):
    """(preduzeće, broj radnika) -> [{sifra, naziv, oj, naziv_oj}] redom iz izvora, bez praznih i ponovljenih."""
    danas = danas or timezone.localdate()
    nazivi_oj = _nazivi_oj(oj_redovi, danas.year)
    nazivi_rm = {(_ceo(p), _tekst(s)): " ".join(_tekst(n).split()) for p, s, n in sistematizacija}
    rezultat = {}
    for red in redovi:
        preduzece, broj = _ceo(red[0]), _ceo(red[1])
        if broj is None:
            continue
        oj_radnika = _sifra(red[2])
        mesta, vidjena = [], set()
        for oj, sif_sis in zip(red[2::2], red[3::2]):
            sifra = _sifra(sif_sis)
            oj = _sifra(oj) or oj_radnika
            if not sifra or (sifra, oj) in vidjena:
                continue
            vidjena.add((sifra, oj))
            mesta.append({"sifra": sifra, "naziv": nazivi_rm.get((preduzece, sifra), ""),
                          "oj": oj, "naziv_oj": " ".join(nazivi_oj.get((preduzece, oj), "").split())})
        rezultat[(preduzece, broj)] = mesta
    return rezultat


def procitaj_radna_mesta(using=None):
    from hr.sync import _resolve_hr_db_alias

    with connections[_resolve_hr_db_alias(using)].cursor() as cursor:
        cursor.execute(RADNA_MESTA_SQL)
        redovi = cursor.fetchall()
        cursor.execute(OJ_SQL)
        oj_redovi = cursor.fetchall()
        cursor.execute(SISTEMATIZACIJA_SQL)
        sistematizacija = cursor.fetchall()
    return radna_mesta(redovi, oj_redovi, sistematizacija)


def osvezi_radna_mesta(po_radniku):
    """Upisuje radna mesta na zaposlenja (preduzeće + broj). Vraća broj izmenjenih zaposlenja."""
    izmenjeno = 0
    for employee in Employee.objects.only("pk", "preduzece", "employee_code", "radna_mesta"):
        mesta = po_radniku.get((employee.preduzece, employee.employee_code))
        if mesta is None or mesta == (employee.radna_mesta or []):
            continue
        Employee.objects.filter(pk=employee.pk).update(radna_mesta=mesta)
        izmenjeno += 1
    return izmenjeno


