from decimal import Decimal

from django.db.models import Case, IntegerField, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import ExtractMonth, ExtractYear

from ..models import JobCode, TransactionNIS, TransactionOMV, Vehicle
from .fuel import filter_nis_fuel_queryset, filter_omv_fuel_queryset


VEHICLE_TYPE_PASSENGER = "putnicka"
VEHICLE_TYPE_TRUCK = "teretna"
SUPPLIER_OMV = "omv"
SUPPLIER_NIS = "nis"


def vehicle_type_label(vehicle_type):
    return "Putnička vozila" if vehicle_type == VEHICLE_TYPE_PASSENGER else "Teretna vozila"


def supplier_label(supplier):
    return "OMV" if supplier == SUPPLIER_OMV else "NIS"


def _vehicle_type_filter(vehicle_type):
    if vehicle_type == VEHICLE_TYPE_PASSENGER:
        return Q(vehicle__category=Vehicle.Category.PASSENGER)
    return Q(vehicle__category=Vehicle.Category.CARGO)


def _period_filter(queryset, date_field, form):
    if not form.is_valid():
        return queryset

    godina = form.cleaned_data.get("godina")
    mesec = form.cleaned_data.get("mesec")
    polovina = form.cleaned_data.get("polovina")

    if godina:
        queryset = queryset.filter(**{f"{date_field}__year": int(godina)})
    if mesec:
        queryset = queryset.filter(**{f"{date_field}__month": int(mesec)})
    if polovina == "1":
        queryset = queryset.filter(**{f"{date_field}__day__lte": 15})
    elif polovina == "2":
        queryset = queryset.filter(**{f"{date_field}__day__gt": 15})

    return queryset


def _historical_job_code_subqueries(date_field):
    historical_job = JobCode.objects.filter(
        vehicle_id=OuterRef("vehicle_id"),
        assigned_date__lte=OuterRef(date_field),
    ).order_by("-assigned_date", "-id")
    return {
        "sifpos": Subquery(historical_job.values("organizational_unit__code")[:1]),
        "naziv_sifre_posla": Subquery(historical_job.values("organizational_unit__name")[:1]),
        "datum_dodele_sifre": Subquery(historical_job.values("assigned_date")[:1]),
    }


def _common_annotations(date_field):
    return {
        "godina": ExtractYear(date_field),
        "mesec": ExtractMonth(date_field),
        **_historical_job_code_subqueries(date_field),
    }


def _half_month_case(date_field):
    return Case(
        When(**{f"{date_field}__day__lte": 15}, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )


def _normalize_summary_row(row, supplier, vehicle_type):
    return {
        "supplier": supplier_label(supplier),
        "tipvozila": vehicle_type_label(vehicle_type),
        "sifpos": row["sifpos"] or "Bez sifre",
        "naziv_sifre_posla": row["naziv_sifre_posla"] or "",
        "godina": row["godina"],
        "mesec": row["mesec"],
        "polovina": row["polovina"],
        "broj_transakcija": row["broj_transakcija"],
        "kolicina": row["kolicina"] or Decimal("0.00"),
        "bruto": row["bruto"] or Decimal("0.00"),
        "neto": row["neto"] or Decimal("0.00"),
    }


def _annotate_omv_queryset(form, vehicle_type):
    qs = filter_omv_fuel_queryset(TransactionOMV.objects.select_related("vehicle"))
    qs = qs.filter(vehicle__isnull=False).filter(_vehicle_type_filter(vehicle_type))
    qs = _period_filter(qs, "transaction_date", form)
    return qs.annotate(**_common_annotations("transaction_date")).annotate(polovina=_half_month_case("transaction_date"))


def _annotate_nis_queryset(form, vehicle_type):
    qs = filter_nis_fuel_queryset(TransactionNIS.objects.select_related("vehicle"))
    qs = qs.filter(vehicle__isnull=False).filter(_vehicle_type_filter(vehicle_type))
    qs = _period_filter(qs, "datum_transakcije", form)
    return qs.annotate(**_common_annotations("datum_transakcije")).annotate(polovina=_half_month_case("datum_transakcije"))


def _summary_from_detail_rows(detail_rows, supplier, vehicle_type):
    grouped = {}
    for row in detail_rows:
        key = (row["sifpos"], row["naziv_sifre_posla"], row["godina"], row["mesec"], row["polovina"])
        if key not in grouped:
            grouped[key] = {
                "sifpos": row["sifpos"],
                "naziv_sifre_posla": row["naziv_sifre_posla"],
                "godina": row["godina"],
                "mesec": row["mesec"],
                "polovina": row["polovina"],
                "broj_transakcija": 0,
                "kolicina": Decimal("0.00"),
                "bruto": Decimal("0.00"),
                "neto": Decimal("0.00"),
            }
        grouped[key]["broj_transakcija"] += 1
        grouped[key]["kolicina"] += row["kolicina"] or Decimal("0.00")
        grouped[key]["bruto"] += row["bruto"] or Decimal("0.00")
        grouped[key]["neto"] += row["neto"] or Decimal("0.00")

    return [
        _normalize_summary_row(row, supplier, vehicle_type)
        for row in sorted(grouped.values(), key=lambda item: (item["godina"] or 0, item["mesec"] or 0, item["polovina"] or 0, item["sifpos"] or ""))
    ]


def _detail_from_omv(qs, sifpos):
    if sifpos:
        qs = qs.filter(sifpos=sifpos if sifpos != "Bez sifre" else None)
    rows = []
    for trx in qs.order_by("transaction_date", "vehicle__id", "id"):
        rows.append(
            {
                "supplier": "OMV",
                "tipvozila": trx.vehicle.get_category_display() if trx.vehicle else "",
                "sifpos": trx.sifpos or "Bez sifre",
                "naziv_sifre_posla": trx.naziv_sifre_posla or "",
                "regozn": trx.license_plate_no,
                "vozilo": f"{trx.vehicle.brand} {trx.vehicle.model}" if trx.vehicle else "",
                "kartica": trx.card,
                "datum": trx.transaction_date,
                "godina": trx.godina,
                "mesec": trx.mesec,
                "polovina": trx.polovina,
                "proizvod": trx.product_inv,
                "kolicina": trx.quantity or Decimal("0.00"),
                "cena": trx.unit_price,
                "bruto": trx.gross_cc or Decimal("0.00"),
                "neto": trx.amount or Decimal("0.00"),
                "kilometraza": trx.mileage,
                "datum_dodele_sifre": trx.datum_dodele_sifre,
            }
        )
    return rows


def _detail_from_nis(qs, sifpos):
    if sifpos:
        qs = qs.filter(sifpos=sifpos if sifpos != "Bez sifre" else None)
    rows = []
    for trx in qs.order_by("datum_transakcije", "vehicle__id", "id"):
        rows.append(
            {
                "supplier": "NIS",
                "tipvozila": trx.vehicle.get_category_display() if trx.vehicle else "",
                "sifpos": trx.sifpos or "Bez sifre",
                "naziv_sifre_posla": trx.naziv_sifre_posla or "",
                "regozn": trx.registarska_oznaka_vozila,
                "vozilo": f"{trx.vehicle.brand} {trx.vehicle.model}" if trx.vehicle else "",
                "kartica": trx.broj_kartice,
                "datum": trx.datum_transakcije,
                "godina": trx.godina,
                "mesec": trx.mesec,
                "polovina": trx.polovina,
                "proizvod": trx.naziv_proizvoda,
                "kolicina": trx.kolicina or Decimal("0.00"),
                "cena": trx.cena,
                "bruto": trx.total_sa_kase or Decimal("0.00"),
                "neto": trx.total or Decimal("0.00"),
                "kilometraza": trx.kilometraza,
                "datum_dodele_sifre": trx.datum_dodele_sifre,
            }
        )
    return rows


def fuel_job_code_report(form, *, supplier, vehicle_type, sifpos=None):
    if supplier == SUPPLIER_OMV:
        qs = _annotate_omv_queryset(form, vehicle_type)
        all_detail = _detail_from_omv(qs, None)
        summary = _summary_from_detail_rows(all_detail, supplier, vehicle_type)
        detail = [row for row in all_detail if row["sifpos"] == sifpos] if sifpos else []
    else:
        qs = _annotate_nis_queryset(form, vehicle_type)
        all_detail = _detail_from_nis(qs, None)
        summary = _summary_from_detail_rows(all_detail, supplier, vehicle_type)
        detail = [row for row in all_detail if row["sifpos"] == sifpos] if sifpos else []

    return summary, detail
