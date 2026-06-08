from datetime import date, datetime, time as datetime_time

from django.db.models import Case, CharField, F, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import Concat
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
    "adblue",
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


def _dedupe_omv_transaction_lines(queryset):
    preferred_line = (
        TransactionOMV.objects.filter(
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


def filter_omv_fuel_queryset(queryset):
    return _dedupe_omv_transaction_lines(queryset.filter(_fuel_product_filter("product_inv")))


def filter_nis_fuel_queryset(queryset):
    return queryset.filter(_fuel_product_filter("naziv_proizvoda"))


def format_omv_receipt_number(invoice_no, voucher):
    invoice_no = str(invoice_no or "").strip()
    voucher = str(voucher or "").strip()
    if invoice_no and voucher and invoice_no != voucher:
        return f"{invoice_no} / {voucher}"
    return invoice_no or voucher


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
