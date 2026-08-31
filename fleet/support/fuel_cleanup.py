import datetime

from django.db import transaction
from django.db.models import Count, Exists, OuterRef

from ..models import FuelConsumption, TransactionOMV
from .fuel import (
    _fuel_product_filter,
    filter_omv_fuel_queryset,
    is_omv_invoice_date_stale,
    omv_stale_invoice_queryset,
)


OMV_RECEIPT_IDENTITY_FIELDS = (
    "license_plate_no",
    "card",
    "product_inv",
    "voucher",
    "quantity",
    "gross_cc",
    "amount",
    "mileage",
    "invoice_no",
)


def _delete_ids(model, ids, *, using):
    ids = list(dict.fromkeys(ids))
    deleted = 0
    for start in range(0, len(ids), 1000):
        chunk = ids[start:start + 1000]
        if chunk:
            deleted += model.objects.using(using).filter(id__in=chunk).delete()[0]
    return deleted


def _identity_filter(group):
    filters = {}
    for field in OMV_RECEIPT_IDENTITY_FIELDS:
        value = group[field]
        if value is None:
            filters[f"{field}__isnull"] = True
        else:
            filters[field] = value
    return filters


def _transaction_sort_key(row):
    max_datetime = datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)
    return (
        is_omv_invoice_date_stale(row.transaction_date, row.invoice_date),
        row.transaction_date or max_datetime,
        not bool(row.invoiced),
        row.id,
    )


def _matching_fuel_consumption_ids_for_transactions(transaction_ids, *, using):
    ids = set()
    transactions = TransactionOMV.objects.using(using).filter(id__in=transaction_ids)
    for tx in transactions.iterator():
        if not tx.vehicle_id or not tx.transaction_date or tx.quantity is None or not tx.product_inv:
            continue
        filters = {
            "vehicle_id": tx.vehicle_id,
            "supplier": "OMV",
            "date": tx.transaction_date,
            "amount": tx.quantity,
            "fuel_type": tx.product_inv,
        }
        if tx.gross_cc is not None:
            filters["cost_bruto"] = tx.gross_cc
        ids.update(FuelConsumption.objects.using(using).filter(**filters).values_list("id", flat=True))
    return ids


def _duplicate_omv_transaction_ids(*, using, vehicle_id=None):
    base_qs = TransactionOMV.objects.using(using).all()
    if vehicle_id:
        base_qs = base_qs.filter(vehicle_id=vehicle_id)

    duplicate_groups = (
        base_qs.values(*OMV_RECEIPT_IDENTITY_FIELDS)
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
    )

    duplicate_ids = set()
    kept_ids = set()
    for group in duplicate_groups.iterator():
        rows = list(base_qs.filter(**_identity_filter(group)))
        if len(rows) < 2:
            continue
        keep = sorted(rows, key=_transaction_sort_key)[0]
        kept_ids.add(keep.id)
        duplicate_ids.update(row.id for row in rows if row.id != keep.id)

    return duplicate_ids, kept_ids


def _non_fuel_consumption_ids(*, using, vehicle_id=None):
    queryset = FuelConsumption.objects.using(using).filter(supplier="OMV").exclude(_fuel_product_filter("fuel_type"))
    if vehicle_id:
        queryset = queryset.filter(vehicle_id=vehicle_id)
    return set(queryset.values_list("id", flat=True))


def _orphan_duplicate_fuel_consumption_ids(transaction_delete_ids, *, using, vehicle_id=None):
    clean_transactions = filter_omv_fuel_queryset(
        TransactionOMV.objects.using(using).exclude(id__in=transaction_delete_ids)
    )
    if vehicle_id:
        clean_transactions = clean_transactions.filter(vehicle_id=vehicle_id)

    queryset = (
        FuelConsumption.objects.using(using)
        .filter(supplier="OMV")
        .filter(_fuel_product_filter("fuel_type"))
        .annotate(
            has_exact_omv_transaction=Exists(
                clean_transactions.filter(
                    vehicle_id=OuterRef("vehicle_id"),
                    transaction_date=OuterRef("date"),
                    product_inv=OuterRef("fuel_type"),
                    quantity=OuterRef("amount"),
                )
            ),
            has_same_omv_payload=Exists(
                clean_transactions.filter(
                    vehicle_id=OuterRef("vehicle_id"),
                    product_inv=OuterRef("fuel_type"),
                    quantity=OuterRef("amount"),
                    gross_cc=OuterRef("cost_bruto"),
                    mileage=OuterRef("mileage"),
                )
            ),
        )
        .filter(has_exact_omv_transaction=False, has_same_omv_payload=True)
    )
    if vehicle_id:
        queryset = queryset.filter(vehicle_id=vehicle_id)
    return set(queryset.values_list("id", flat=True))


def cleanup_omv_fuel_data(*, apply=False, using="default", vehicle_id=None):
    transaction_base_qs = TransactionOMV.objects.using(using).all()
    if vehicle_id:
        transaction_base_qs = transaction_base_qs.filter(vehicle_id=vehicle_id)

    stale_transaction_ids = set(
        omv_stale_invoice_queryset(transaction_base_qs).values_list("id", flat=True)
    )
    duplicate_transaction_ids, kept_duplicate_transaction_ids = _duplicate_omv_transaction_ids(
        using=using,
        vehicle_id=vehicle_id,
    )
    transaction_delete_ids = stale_transaction_ids | duplicate_transaction_ids

    fuel_from_deleted_transactions = _matching_fuel_consumption_ids_for_transactions(
        transaction_delete_ids,
        using=using,
    )
    non_fuel_consumption_ids = _non_fuel_consumption_ids(using=using, vehicle_id=vehicle_id)
    orphan_duplicate_consumption_ids = _orphan_duplicate_fuel_consumption_ids(
        transaction_delete_ids,
        using=using,
        vehicle_id=vehicle_id,
    )
    fuel_consumption_delete_ids = (
        fuel_from_deleted_transactions
        | non_fuel_consumption_ids
        | orphan_duplicate_consumption_ids
    )

    result = {
        "apply": apply,
        "using": using,
        "vehicle_id": vehicle_id,
        "stale_omv_transactions": len(stale_transaction_ids),
        "duplicate_omv_transactions": len(duplicate_transaction_ids),
        "kept_duplicate_omv_transactions": len(kept_duplicate_transaction_ids),
        "omv_transactions_to_delete": len(transaction_delete_ids),
        "fuel_consumptions_from_deleted_transactions": len(fuel_from_deleted_transactions),
        "non_fuel_consumptions": len(non_fuel_consumption_ids),
        "orphan_duplicate_fuel_consumptions": len(orphan_duplicate_consumption_ids),
        "fuel_consumptions_to_delete": len(fuel_consumption_delete_ids),
        "deleted_omv_transactions": 0,
        "deleted_fuel_consumptions": 0,
    }

    if apply and (transaction_delete_ids or fuel_consumption_delete_ids):
        with transaction.atomic(using=using):
            result["deleted_fuel_consumptions"] = _delete_ids(
                FuelConsumption,
                fuel_consumption_delete_ids,
                using=using,
            )
            result["deleted_omv_transactions"] = _delete_ids(
                TransactionOMV,
                transaction_delete_ids,
                using=using,
            )

    return result
