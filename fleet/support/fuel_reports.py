from decimal import Decimal

from django.db.models import Case, IntegerField, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import ExtractMonth, ExtractYear

from ..models import JobCode, TransactionNIS, TransactionOMV, Vehicle
from .fuel import (
    deduplicate_omv_transactions,
    filter_nis_fuel_queryset,
    filter_omv_fuel_queryset,
    nis_charged_gross_net_amounts,
    omv_charged_gross_net_amounts,
)


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
        bruto, neto = omv_charged_gross_net_amounts(trx.gross_cc, trx.vat)
        rows.append(
            {
                "supplier": "OMV",
                "tipvozila": trx.vehicle.get_category_display() if trx.vehicle else "",
                "sifpos": trx.sifpos or "Bez sifre",
                "naziv_sifre_posla": trx.naziv_sifre_posla or "",
                "regozn": trx.license_plate_no,
                "vozilo": f"{trx.vehicle.brand} {trx.vehicle.model}" if trx.vehicle else "",
                "vehicle_id": trx.vehicle_id,
                "kartica": trx.card,
                "datum": trx.transaction_date,
                "godina": trx.godina,
                "mesec": trx.mesec,
                "polovina": trx.polovina,
                "proizvod": trx.product_inv,
                "kolicina": trx.quantity or Decimal("0.00"),
                "cena": trx.unit_price,
                "bruto": bruto or Decimal("0.00"),
                "neto": neto or Decimal("0.00"),
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
        bruto, neto = nis_charged_gross_net_amounts(trx.total)
        rows.append(
            {
                "supplier": "NIS",
                "tipvozila": trx.vehicle.get_category_display() if trx.vehicle else "",
                "sifpos": trx.sifpos or "Bez sifre",
                "naziv_sifre_posla": trx.naziv_sifre_posla or "",
                "regozn": trx.registarska_oznaka_vozila,
                "vozilo": f"{trx.vehicle.brand} {trx.vehicle.model}" if trx.vehicle else "",
                "vehicle_id": trx.vehicle_id,
                "kartica": trx.broj_kartice,
                "datum": trx.datum_transakcije,
                "godina": trx.godina,
                "mesec": trx.mesec,
                "polovina": trx.polovina,
                "proizvod": trx.naziv_proizvoda,
                "kolicina": trx.kolicina or Decimal("0.00"),
                "cena": trx.cena,
                "bruto": bruto or Decimal("0.00"),
                "neto": neto or Decimal("0.00"),
                "kilometraza": trx.kilometraza,
                "datum_dodele_sifre": trx.datum_dodele_sifre,
            }
        )
    return rows


OMV_KUPCI = {"107248": "Putnička vozila", "107258": "Teretna vozila"}  # kartice kod OMV-a = kupac na fakturi


def omv_fakture(godina=None):
    """OMV fakture za izbor u izveštaju: broj, datum, kartica (kupac), broj stavki i naš bruto zbir."""
    from django.db.models import Count, Sum

    qs = TransactionOMV.objects.exclude(invoice_no__isnull=True).exclude(invoice_no="").filter(invoiced=True)
    if godina:
        qs = qs.filter(invoice_date__year=int(godina))
    return [dict(broj=r["invoice_no"], datum=r["invoice_date"], kupac=OMV_KUPCI.get(r["customer"], r["customer"]),
                 stavki=r["n"], bruto=r["bruto"])
            for r in qs.values("invoice_no", "invoice_date", "customer").annotate(n=Count("id"), bruto=Sum("gross_cc"))
            .order_by("-invoice_date", "invoice_no")[:60]]


def period_fakture(broj):
    """Period OMV fakture za filter i tabelu: godina, mesec i polovina po datumu fakture (OMV: do 13. = prva,
    do kraja meseca = druga) i stvarni raspon točenja na fakturi. None ako faktura nije u transakcijama."""
    from django.db.models import Max, Min
    from django.utils import timezone

    r = TransactionOMV.objects.filter(invoice_no=broj).aggregate(dan=Max("invoice_date"), od=Min("transaction_date"),
                                                                 do=Max("transaction_date"))
    if not r["dan"]:
        return None
    return {"godina": str(r["dan"].year), "mesec": str(r["dan"].month), "polovina": "1" if r["dan"].day <= 15 else "2",
            "od": timezone.localdate(r["od"]) if r["od"] else None, "do": timezone.localdate(r["do"]) if r["do"] else None}


def poslednji_fakturisani_period(supplier, vehicle_type):
    """Podrazumevani filter izveštaja: poslednji period za koji je izdata faktura (od 07.10.2026.).

    OMV: poslednja faktura kartice (putnička 107248 / teretna 107258). NIS: polovina meseca poslednje NIS
    fakture sa SEF-a (NIS fakturiše 1–15 i 16–kraj); bez nje — poslednja završena polovina pre današnjeg dana.
    """
    from django.utils import timezone

    if supplier == SUPPLIER_OMV:
        kupac = "107258" if vehicle_type == VEHICLE_TYPE_TRUCK else "107248"
        broj = (TransactionOMV.objects.filter(customer=kupac, invoiced=True).exclude(invoice_no__isnull=True)
                .exclude(invoice_no="").order_by("-invoice_date", "-invoice_no").values_list("invoice_no", flat=True).first())
        if broj:
            period = period_fakture(broj) or {}
            return {"faktura": broj, **{k: period[k] for k in ("godina", "mesec", "polovina") if k in period}}
    from finansije.sef_models import SefFaktura

    dan = (SefFaktura.objects.filter(smer="ulazna", partner_pib="104052135", vrsta="Invoice")
           .exclude(datum_prometa__isnull=True).order_by("-datum_prometa").values_list("datum_prometa", flat=True).first())
    if dan is None:
        danas = timezone.localdate()
        dan = danas.replace(day=15) if danas.day > 15 else danas.replace(day=1) - timezone.timedelta(days=1)
    return {"godina": str(dan.year), "mesec": str(dan.month), "polovina": "1" if dan.day <= 15 else "2"}


def omv_faktura_sef(broj):
    """Iznos iste fakture na SEF-u (ulazna, OMV), za poređenje sa zbirom transakcija; None ako je nema."""
    from finansije.sef_models import SefFaktura

    return SefFaktura.objects.filter(smer="ulazna", broj=broj, partner_naziv__icontains="OMV").first()


def _omv_po_fakturi(faktura):
    # Sve stavke fakture (gorivo, AdBlue, putarina, kartice), bez obzira na kategoriju vozila u Floti.
    qs = deduplicate_omv_transactions(TransactionOMV.objects.select_related("vehicle").filter(invoice_no=faktura))
    return qs.annotate(**_common_annotations("transaction_date")).annotate(polovina=_half_month_case("transaction_date"))


def _po_sifri(redovi):
    """Zbir po šifri posla, bez podele na mesece i polovine (cela faktura)."""
    grupe = {}
    for r in redovi:
        g = grupe.setdefault(r["sifpos"], {**r, "godina": None, "mesec": None, "polovina": None, "broj_transakcija": 0,
                                           "kolicina": Decimal("0.00"), "bruto": Decimal("0.00"), "neto": Decimal("0.00")})
        for polje in ("broj_transakcija", "kolicina", "bruto", "neto"):
            g[polje] += r[polje]
    return sorted(grupe.values(), key=lambda r: r["sifpos"] or "")


def ukupno(redovi):
    """Poslednji red izveštaja: zbir za knjiženje."""
    return {polje: sum((r[polje] for r in redovi), Decimal("0.00") if polje != "broj_transakcija" else 0)
            for polje in ("broj_transakcija", "kolicina", "bruto", "neto")}


def fuel_job_code_report(form, *, supplier, vehicle_type, sifpos=None):
    faktura = (form.cleaned_data.get("faktura") or "").strip() if form.is_valid() else ""
    if supplier == SUPPLIER_OMV and faktura:
        all_detail = _detail_from_omv(_omv_po_fakturi(faktura), None)
        summary = _po_sifri(_summary_from_detail_rows(all_detail, supplier, vehicle_type))
        period = period_fakture(faktura)
        if period:  # cela faktura u redu, ali sa mesecom i polovinom fakturisanog perioda
            for red in summary:
                red.update(godina=int(period["godina"]), mesec=int(period["mesec"]), polovina=int(period["polovina"]))
        detail = [row for row in all_detail if row["sifpos"] == sifpos] if sifpos else []
        return summary, detail
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
