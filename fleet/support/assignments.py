"""Dodela vozila sifri posla na dan — jedno pravilo za uvoz goriva i njegovu ispravku.

Vazi poslednja dodela sa `assigned_date` do tog dana (ukljucivo), a kod iste dodele po datumu
novija po redosledu unosa — isto kao u izvestajima o gorivu (`fuel_reports.py`).
"""
import datetime
from bisect import bisect_right

from django.utils import timezone


def dan(vreme):
    """Datum u lokalnoj vremenskoj zoni; prima datum, naivno ili svesno vreme ili None (danas)."""
    if vreme is None:
        return timezone.localdate()
    if isinstance(vreme, datetime.datetime):
        return timezone.localtime(vreme).date() if timezone.is_aware(vreme) else vreme.date()
    return vreme


def sifra_vozila_na_dan(vehicle, na_dan=None):
    """Sifra OJ dodele vazece na dan, ili None ako vozilo tada nije imalo dodelu."""
    dodela = (
        vehicle.job_codes.filter(assigned_date__lte=dan(na_dan), organizational_unit__isnull=False)
        .select_related("organizational_unit")
        .order_by("-assigned_date", "-pk")
        .first()
    )
    return dodela.organizational_unit.code if dodela else None


class DodeleVozila:
    """Sve dodele ucitane jednom, za ispravku mnogo zapisa bez upita po redu."""

    def __init__(self, vehicle_ids=None):
        from fleet.models import JobCode

        qs = JobCode.objects.filter(organizational_unit__isnull=False)
        if vehicle_ids is not None:
            qs = qs.filter(vehicle_id__in=vehicle_ids)
        self._po_vozilu = {}
        for vozilo, datum, sifra in qs.order_by("vehicle_id", "assigned_date", "pk").values_list(
            "vehicle_id", "assigned_date", "organizational_unit__code"
        ):
            datumi, sifre = self._po_vozilu.setdefault(vozilo, ([], []))
            datumi.append(datum)
            sifre.append(sifra)

    def sifra(self, vehicle_id, na_dan):
        datumi, sifre = self._po_vozilu.get(vehicle_id, ([], []))
        mesto = bisect_right(datumi, dan(na_dan))
        return sifre[mesto - 1] if mesto else None
