"""Lizing — mesecni troskovi (izvestaj `lease_monthly_costs`).

Jedan lizing je jedno vozilo, pa je red izvestaja **jedan lizing u jednom mesecu** u kome traje:

- iznos lizinga za taj mesec iz postojeceg obracuna (`lease_costs.lease_amount_between`), isto
  kao u ekonomici vozila; kod nepoznatog znacenja iznosa (`payment_basis`) iznos je prazan;
- centar i OJ po dodeli vozila vazecoj poslednjeg dana lizinga u tom mesecu;
- prateci troskovi su servis (`ServiceTransaction.potrazuje`) i gorivo
  (`FuelConsumption.cost_bruto`) **tog vozila** u tom mesecu — isti izvori kao ekonomika.

Ranije je iznos prikazivan samo u mesecu pocetka lizinga, centar po poslednjoj dodeli, a prateci
troskovi zbir svih vozila trenutno u toj OJ.
"""
import calendar
import datetime
from bisect import bisect_right
from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear

from ..models import FuelConsumption, JobCode, Lease, ServiceTransaction
from .lease_costs import lease_amount_between

ZERO = Decimal("0")


def _meseci(pocetak, kraj):
    dan = pocetak.replace(day=1)
    while dan <= kraj:
        poslednji = dan.replace(day=calendar.monthrange(dan.year, dan.month)[1])
        yield max(dan, pocetak), min(poslednji, kraj)
        dan = poslednji + datetime.timedelta(days=1)


def _dodele(vehicle_ids):
    po_vozilu = defaultdict(list)
    for vozilo, datum, ou_id, code, name, center in (
        JobCode.objects.filter(vehicle_id__in=vehicle_ids, organizational_unit__isnull=False)
        .order_by("vehicle_id", "assigned_date", "pk")
        .values_list("vehicle_id", "assigned_date", "organizational_unit_id", "organizational_unit__code",
                     "organizational_unit__name", "organizational_unit__center")
    ):
        po_vozilu[vozilo].append((datum, ou_id, (code or "").strip(), (name or "").strip(), (center or "").strip()))
    return po_vozilu


def _dodela_na_dan(dodele, dan):
    mesto = bisect_right([d[0] for d in dodele], dan)
    return dodele[mesto - 1] if mesto else None


def _po_mesecu(queryset, polje_datuma, polje_iznosa):
    return {
        (red["vehicle_id"], red["godina"], red["mesec"]): red["iznos"] or ZERO
        for red in queryset.annotate(godina=ExtractYear(polje_datuma), mesec=ExtractMonth(polje_datuma))
        .values("vehicle_id", "godina", "mesec").annotate(iznos=Sum(polje_iznosa)).order_by()
    }


def _broj(vrednost):
    try:
        return int(vrednost)
    except (TypeError, ValueError):
        return None


def lease_monthly_costs_rows(request):
    year, month = _broj(request.GET.get("year")), _broj(request.GET.get("month"))
    center = (request.GET.get("center") or "").strip()
    oj_id = _broj(request.GET.get("oj"))
    lease_type = (request.GET.get("vrsta") or "").strip().lower()

    leases = list(Lease.objects.select_related("vehicle").order_by("start_date", "pk"))
    if lease_type:
        leases = [lease for lease in leases if (lease.lease_type or "").lower() == lease_type]
    vozila = {lease.vehicle_id for lease in leases}
    dodele = _dodele(vozila)
    servis = _po_mesecu(ServiceTransaction.objects.filter(vehicle_id__in=vozila), "datum", "potrazuje")
    gorivo = _po_mesecu(FuelConsumption.objects.filter(vehicle_id__in=vozila), "date", "cost_bruto")

    rows = []
    for lease in leases:
        if not lease.start_date or not lease.end_date or lease.end_date < lease.start_date:
            continue
        for od, do in _meseci(lease.start_date, lease.end_date):
            if (year and od.year != year) or (month and od.month != month):
                continue
            dodela = _dodela_na_dan(dodele.get(lease.vehicle_id, []), do)
            _, dodela_oj, dodela_sifra, dodela_naziv, dodela_centar = dodela or (None, None, "", "", "")
            if center and dodela_centar != center:
                continue
            if oj_id and dodela_oj != oj_id:
                continue
            kljuc = (lease.vehicle_id, od.year, od.month)
            prateci = servis.get(kljuc, ZERO) + gorivo.get(kljuc, ZERO)
            iznos = lease_amount_between(lease, od, do)
            rows.append({
                "year": od.year,
                "month": od.month,
                "center": dodela_centar,
                "oj_id": dodela_oj,
                "oj_code": dodela_sifra,
                "oj_name": dodela_naziv,
                "job_code": lease.job_code,
                "lease_type": lease.lease_type,
                "lease_id": lease.pk,
                "vehicle": lease.vehicle,
                "contract_number": lease.contract_number,
                "lease_amount": iznos,
                "service_total": servis.get(kljuc, ZERO),
                "fuel_total": gorivo.get(kljuc, ZERO),
                "accompanying_total": prateci,
                "total": (iznos + prateci) if iznos is not None else None,
            })
    return sorted(rows, key=lambda r: (r["year"], r["month"], r["center"] or "", r["oj_code"] or "", r["lease_id"]))
