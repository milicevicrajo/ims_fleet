from datetime import date, datetime, time as datetime_time
from decimal import Decimal

from django.db.models import Case, CharField, Count, Exists, F, Max, OuterRef, Q, Subquery, Sum, Value, When
from django.db.models.functions import Concat, TruncDate
from django.utils import timezone as django_timezone

from ..models import TrafficCard, TransactionNIS, TransactionOMV


FUEL_PRODUCT_KEYWORDS = (
    "dizel",
    "diesel",
    "benzin",
    "petrol",
    "maxxmotion",
    "maxxm",
    "bmb",
    "lpg",
    "autogas",
    "cng",
    "tng",
    "ngv",
)


def _fuel_product_filter(field_name):
    product_filter = Q()
    for keyword in FUEL_PRODUCT_KEYWORDS:
        product_filter |= Q(**{f"{field_name}__icontains": keyword})
    return product_filter


def is_fuel_product_name(value):
    text = str(value or "").casefold()
    return any(keyword in text for keyword in FUEL_PRODUCT_KEYWORDS)


def is_omv_invoice_date_stale(transaction_date, invoice_date):
    if not transaction_date or not invoice_date:
        return False
    transaction_day = transaction_date.date() if hasattr(transaction_date, "date") else transaction_date
    return invoice_date < transaction_day


def omv_stale_invoice_queryset(queryset):
    return queryset.annotate(_transaction_day=TruncDate("transaction_date")).filter(
        invoice_date__isnull=False,
        transaction_date__isnull=False,
        invoice_date__lt=F("_transaction_day"),
    )


def _dedupe_omv_transaction_lines(queryset):
    preferred_line = (
        _exclude_omv_stale_invoice_dates(TransactionOMV.objects.using(queryset.db).all())
        .filter(
            license_plate_no=OuterRef("license_plate_no"),
            transaction_date=OuterRef("transaction_date"),
            product_inv=OuterRef("product_inv"),
            voucher=OuterRef("voucher"),
            quantity=OuterRef("quantity"),
        )
        .order_by("-invoiced", "-invoice_date", "-id")
        .values("id")[:1]
    )
    return queryset.filter(id=Subquery(preferred_line))


def _exclude_omv_receipt_echoes(queryset):
    final_receipt_match = (
        TransactionOMV.objects.using(queryset.db).filter(
            license_plate_no=OuterRef("license_plate_no"),
            product_inv=OuterRef("product_inv"),
            voucher=OuterRef("voucher"),
            quantity=OuterRef("quantity"),
            gross_cc=OuterRef("gross_cc"),
            amount=OuterRef("amount"),
            mileage=OuterRef("mileage"),
            invoice_date=OuterRef("invoice_date"),
            invoiced=True,
        )
        .filter(invoice_no__isnull=False)
        .exclude(invoice_no="")
        .exclude(id=OuterRef("id"))
        .exclude(invoice_no=F("voucher"))
    )
    return (
        queryset.annotate(_has_final_receipt_match=Exists(final_receipt_match))
        .exclude(
            Q(_has_final_receipt_match=True)
            & (Q(invoiced=False) | Q(invoiced__isnull=True))
            & Q(invoice_no=F("voucher"))
        )
    )


def _exclude_omv_stale_invoice_dates(queryset):
    return queryset.exclude(id__in=omv_stale_invoice_queryset(queryset).values("id"))


def filter_omv_fuel_queryset(queryset):
    return _exclude_omv_receipt_echoes(
        _dedupe_omv_transaction_lines(
            _exclude_omv_stale_invoice_dates(queryset.filter(_fuel_product_filter("product_inv")))
        )
    )


def filter_nis_fuel_queryset(queryset):
    return queryset.filter(_fuel_product_filter("naziv_proizvoda"))


def format_receipt_identifier(value):
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace(",", "")
    if text.isdigit() and len(text) > 1 and text.startswith("0"):
        return text
    try:
        decimal_value = Decimal(text)
    except Exception:
        return text
    if decimal_value == decimal_value.to_integral_value():
        return str(decimal_value.to_integral_value())
    return text


def format_omv_receipt_number(invoice_no, voucher):
    invoice_no = format_receipt_identifier(invoice_no)
    voucher = format_receipt_identifier(voucher)
    if invoice_no and voucher and invoice_no != voucher:
        return f"{invoice_no} / {voucher}"
    return invoice_no or voucher


def omv_receipt_number_expression():
    return Case(
        When(
            Q(invoice_no__isnull=False)
            & ~Q(invoice_no="")
            & Q(voucher__isnull=False)
            & ~Q(voucher="")
            & ~Q(invoice_no=F("voucher")),
            then=Concat("invoice_no", Value(" / "), "voucher"),
        ),
        When(Q(invoice_no__isnull=False) & ~Q(invoice_no=""), then=F("invoice_no")),
        default=F("voucher"),
        output_field=CharField(),
    )


def date_range_for_datetime_field(start_date=None, end_date=None):
    def _to_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    def _aware(value, bound):
        value = _to_date(value)
        if value is None:
            return None
        dt = datetime.combine(value, datetime_time.min if bound == "start" else datetime_time.max)
        return django_timezone.make_aware(dt) if django_timezone.is_naive(dt) else dt

    return _aware(start_date, "start"), _aware(end_date, "end")


def calculate_average_fuel_consumption(vehicle):
    last_10_consumptions = vehicle.fuel_consumptions.order_by("-date")[:10]

    if len(last_10_consumptions) < 10:
        return None

    first_entry = last_10_consumptions[0]
    start_entry = None
    for i in range(9):
        if last_10_consumptions[i].mileage > 0:
            first_entry = last_10_consumptions[9 - i]
            start_entry = 9 - i
            break

    last_entry = last_10_consumptions[9]
    end_entry = None
    for i in range(9):
        if last_10_consumptions[i].mileage > 0:
            last_entry = last_10_consumptions[i]
            end_entry = i
            break

    if start_entry is not None and end_entry is not None and start_entry >= end_entry:
        total_amount = sum(c.amount for c in last_10_consumptions[end_entry : start_entry + 1])
        total_mileage = last_entry.mileage - first_entry.mileage
        if total_mileage > 0:
            return total_amount / total_mileage * 100
    return None


def calculate_average_fuel_consumption_ever(vehicle):
    fueling_count = vehicle.fuel_consumptions.count()

    if fueling_count < 2:
        return None

    fuel_consumptions = vehicle.fuel_consumptions.order_by("-date")
    first_entry = None
    last_entry = None

    for i in range(fueling_count):
        if fuel_consumptions[i].mileage > 0:
            first_entry = fuel_consumptions[i]
            break

    for i in range(fueling_count):
        if fuel_consumptions[fueling_count - i - 1].mileage > 0:
            last_entry = fuel_consumptions[fueling_count - i - 1]
            break

    if first_entry is not None and last_entry is not None and first_entry != last_entry:
        total_amount = sum(c.amount for c in fuel_consumptions if c.date <= first_entry.date and c.date >= last_entry.date)
        total_mileage = first_entry.mileage - last_entry.mileage
        if total_mileage > 0:
            return total_amount / total_mileage * 100
    return None


def get_fuel_consumption_queryset(start_date=None, end_date=None):
    start_dt, end_dt = date_range_for_datetime_field(start_date, end_date)

    latest_traffic_card_subquery = TrafficCard.objects.filter(
        vehicle=OuterRef("vehicle")
    ).order_by("-issue_date").values("registration_number")[:1]

    omv_receipt_number = omv_receipt_number_expression()

    omv_queryset = filter_omv_fuel_queryset(TransactionOMV.objects.all()).annotate(
        registration_number=Subquery(latest_traffic_card_subquery),
        annotated_transaction_date=F("transaction_date"),
        annotated_receipt_number=omv_receipt_number,
        annotated_quantity=F("quantity"),
        price_per_liter=F("unit_price"),
        total_net=F("amount"),
        total_gross=F("gross_cc"),
        annotated_supplier=Value("OMV", output_field=CharField()),
        annotated_mileage=F("mileage"),
    )

    if start_dt:
        omv_queryset = omv_queryset.filter(transaction_date__gte=start_dt)
    if end_dt:
        omv_queryset = omv_queryset.filter(transaction_date__lte=end_dt)

    omv_queryset = omv_queryset.values(
        "registration_number",
        "annotated_transaction_date",
        "annotated_receipt_number",
        "annotated_quantity",
        "price_per_liter",
        "total_net",
        "total_gross",
        "annotated_supplier",
        "annotated_mileage",
    )

    nis_queryset = filter_nis_fuel_queryset(TransactionNIS.objects.all()).annotate(
        registration_number=Subquery(latest_traffic_card_subquery),
        annotated_transaction_date=F("datum_transakcije"),
        annotated_receipt_number=F("broj_racuna"),
        annotated_quantity=F("kolicina"),
        price_per_liter=F("cena"),
        total_net=F("total"),
        total_gross=F("total_sa_kase"),
        annotated_supplier=Value("NIS", output_field=CharField()),
        annotated_mileage=F("kilometraza"),
    )

    if start_dt:
        nis_queryset = nis_queryset.filter(datum_transakcije__gte=start_dt)
    if end_dt:
        nis_queryset = nis_queryset.filter(datum_transakcije__lte=end_dt)

    nis_queryset = nis_queryset.values(
        "registration_number",
        "annotated_transaction_date",
        "annotated_receipt_number",
        "annotated_quantity",
        "price_per_liter",
        "total_net",
        "total_gross",
        "annotated_supplier",
        "annotated_mileage",
    )

    return omv_queryset.union(nis_queryset)


def get_fuel_invoice_queryset(vehicle_id=None, search_value=""):
    latest_traffic_card_subquery = TrafficCard.objects.filter(
        vehicle=OuterRef("vehicle")
    ).order_by("-issue_date").values("registration_number")[:1]

    search_value = str(search_value or "").strip()

    omv_queryset = filter_omv_fuel_queryset(TransactionOMV.objects.all()).annotate(
        registration_number=Subquery(latest_traffic_card_subquery),
        receipt_number=omv_receipt_number_expression(),
        supplier_name=Value("OMV", output_field=CharField()),
    )
    nis_queryset = filter_nis_fuel_queryset(TransactionNIS.objects.all()).annotate(
        registration_number=Subquery(latest_traffic_card_subquery),
        receipt_number=F("broj_racuna"),
        supplier_name=Value("NIS", output_field=CharField()),
    )

    if vehicle_id:
        omv_queryset = omv_queryset.filter(vehicle_id=vehicle_id)
        nis_queryset = nis_queryset.filter(vehicle_id=vehicle_id)

    if search_value:
        omv_queryset = omv_queryset.filter(
            Q(registration_number__icontains=search_value)
            | Q(receipt_number__icontains=search_value)
            | Q(supplier__icontains=search_value)
            | Q(product_inv__icontains=search_value)
        )
        nis_queryset = nis_queryset.filter(
            Q(registration_number__icontains=search_value)
            | Q(receipt_number__icontains=search_value)
            | Q(naziv_proizvoda__icontains=search_value)
        )

    omv_invoices = (
        omv_queryset.values("vehicle_id", "registration_number", "receipt_number", "supplier_name")
        .annotate(
            latest_date=Max("transaction_date"),
            quantity_total=Sum("quantity"),
            total_net=Sum("amount"),
            total_gross=Sum("gross_cc"),
            max_mileage=Max("mileage"),
            line_count=Count("id"),
        )
        .values(
            "vehicle_id",
            "registration_number",
            "receipt_number",
            "supplier_name",
            "latest_date",
            "quantity_total",
            "total_net",
            "total_gross",
            "max_mileage",
            "line_count",
        )
    )

    nis_invoices = (
        nis_queryset.values("vehicle_id", "registration_number", "receipt_number", "supplier_name")
        .annotate(
            latest_date=Max("datum_transakcije"),
            quantity_total=Sum("kolicina"),
            total_net=Sum("total"),
            total_gross=Sum("total_sa_kase"),
            max_mileage=Max("kilometraza"),
            line_count=Count("id"),
        )
        .values(
            "vehicle_id",
            "registration_number",
            "receipt_number",
            "supplier_name",
            "latest_date",
            "quantity_total",
            "total_net",
            "total_gross",
            "max_mileage",
            "line_count",
        )
    )

    return omv_invoices.union(nis_invoices)


def get_fuel_invoice_lines(supplier, receipt_number, vehicle_id=None):
    supplier = str(supplier or "").strip().upper()
    receipt_number = str(receipt_number or "").strip()

    if supplier == "OMV":
        queryset = filter_omv_fuel_queryset(TransactionOMV.objects.select_related("vehicle"))
        if " / " in receipt_number:
            invoice_no, voucher = [part.strip() for part in receipt_number.split(" / ", 1)]
            queryset = queryset.filter(invoice_no=invoice_no, voucher=voucher)
        else:
            queryset = queryset.filter(Q(invoice_no=receipt_number) | Q(voucher=receipt_number))
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        return [
            {
                "supplier": "OMV",
                "vehicle": row.vehicle,
                "date": row.transaction_date,
                "receipt_number": format_omv_receipt_number(row.invoice_no, row.voucher),
                "product": row.product_inv,
                "quantity": row.quantity,
                "price_per_liter": row.unit_price,
                "total_net": row.amount,
                "total_gross": row.gross_cc,
                "mileage": row.mileage,
            }
            for row in queryset.order_by("transaction_date", "id")
        ]

    if supplier == "NIS":
        queryset = filter_nis_fuel_queryset(TransactionNIS.objects.select_related("vehicle")).filter(
            broj_racuna=receipt_number
        )
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        return [
            {
                "supplier": "NIS",
                "vehicle": row.vehicle,
                "date": row.datum_transakcije,
                "receipt_number": format_receipt_identifier(row.broj_racuna),
                "product": row.naziv_proizvoda,
                "quantity": row.kolicina,
                "price_per_liter": row.cena,
                "total_net": row.total,
                "total_gross": row.total_sa_kase,
                "mileage": row.kilometraza,
            }
            for row in queryset.order_by("datum_transakcije", "id")
        ]

    return []


def get_vehicle_fuel_transaction_rows(vehicle):
    omv_receipt_number = Case(
        When(
            Q(invoice_no__isnull=False)
            & ~Q(invoice_no="")
            & Q(voucher__isnull=False)
            & ~Q(voucher="")
            & ~Q(invoice_no=F("voucher")),
            then=Concat("invoice_no", Value(" / "), "voucher"),
        ),
        When(Q(invoice_no__isnull=False) & ~Q(invoice_no=""), then=F("invoice_no")),
        default=F("voucher"),
        output_field=CharField(),
    )

    omv_rows = filter_omv_fuel_queryset(TransactionOMV.objects.filter(vehicle=vehicle)).annotate(
        receipt_number=omv_receipt_number,
        supplier_name=Value("OMV", output_field=CharField()),
    ).values(
        "transaction_date",
        "receipt_number",
        "quantity",
        "unit_price",
        "amount",
        "gross_cc",
        "supplier_name",
        "mileage",
    )

    nis_rows = filter_nis_fuel_queryset(TransactionNIS.objects.filter(vehicle=vehicle)).annotate(
        supplier_name=Value("NIS", output_field=CharField()),
    ).values(
        "datum_transakcije",
        "broj_racuna",
        "kolicina",
        "cena",
        "total",
        "total_sa_kase",
        "supplier_name",
        "kilometraza",
    )

    rows = [
        {
            "date": row["transaction_date"],
            "receipt_number": format_receipt_identifier(row["receipt_number"]),
            "amount": row["quantity"],
            "price_per_liter": row["unit_price"],
            "cost_neto": row["amount"],
            "cost_bruto": row["gross_cc"],
            "supplier": row["supplier_name"],
            "mileage": row["mileage"],
        }
        for row in omv_rows
    ]
    rows.extend(
        {
            "date": row["datum_transakcije"],
            "receipt_number": format_receipt_identifier(row["broj_racuna"]),
            "amount": row["kolicina"],
            "price_per_liter": row["cena"],
            "cost_neto": row["total"],
            "cost_bruto": row["total_sa_kase"],
            "supplier": row["supplier_name"],
            "mileage": row["kilometraza"],
        }
        for row in nis_rows
    )
    return sorted(rows, key=lambda row: (row["date"], row["supplier"], row["receipt_number"] or ""), reverse=True)
