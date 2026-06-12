from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256

from django.db import connections, transaction
from django.utils import timezone


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def _decimal(value, places="0.01"):
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal(places))


def _date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _clean(value)
    for date_format in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def _source_key(*values):
    raw = "|".join(_clean(value) for value in values)
    return sha256(raw.encode("utf-8")).hexdigest()


def _limit(value, default=10000):
    return min(max(int(value or default), 1), 20000)


def _chunks(values, size=1000):
    for index in range(0, len(values), size):
        yield values[index:index + size]


@transaction.atomic
def _bulk_upsert(model, rows):
    if not rows:
        return []

    rows = list({values["source_key"]: values for values in rows}.values())
    synced_at = timezone.now()
    source_keys = [values["source_key"] for values in rows]
    existing_by_key = model.objects.in_bulk(source_keys, field_name="source_key")
    update_fields = [field for field in rows[0] if field != "source_key"]
    to_create = []
    to_update = []
    unchanged_ids = []

    for values in rows:
        obj = existing_by_key.get(values["source_key"])
        if obj is None:
            to_create.append(model(**values, synced_at=synced_at))
            continue
        changed = any(getattr(obj, field) != value for field, value in values.items() if field != "source_key")
        if not changed:
            unchanged_ids.append(obj.pk)
            continue
        for field, value in values.items():
            if field != "source_key":
                setattr(obj, field, value)
        obj.synced_at = synced_at
        obj.updated_at = synced_at
        to_update.append(obj)

    for obj in to_create:
        obj.save()
    for obj in to_update:
        obj.save(update_fields=[*update_fields, "synced_at", "updated_at"])
    for ids in _chunks(unchanged_ids):
        model.objects.filter(pk__in=ids).update(synced_at=synced_at)
    return [*to_create, *existing_by_key.values()]


def list_euf_items(q=None, limit=10000):
    q = _clean(q)
    params = []
    where = ""
    if q:
        where = """
            WHERE LTRIM(RTRIM([broj_fakutre])) LIKE %s
               OR LTRIM(RTRIM([partnerime])) LIKE %s
               OR [naziv] LIKE %s
               OR LTRIM(RTRIM([konto])) LIKE %s
        """
        like_value = f"%{q}%"
        params.extend([like_value] * 4)

    sql = f"""
        SELECT TOP ({_limit(limit)})
            purchaseinvoiceid,
            creationdate,
            datum_dok,
            duedate,
            note,
            ContractDocumentReference,
            broj_fakutre,
            brojtendera,
            partnerpib,
            partnermb,
            partnerime,
            ukupno,
            osnovica,
            zaplacanje,
            jm,
            naziv,
            kol,
            cena,
            vrednost,
            konto
        FROM dbo.nbv_EUF_stavke
        {where}
        ORDER BY datum_dok DESC, LTRIM(RTRIM(broj_fakutre))
    """
    with connections["server_db"].cursor() as cursor:
        cursor.execute(sql, params)
        return [_euf_item_values(row) for row in cursor.fetchall()]


def _euf_item_values(row):
    values = {
        "purchase_invoice_id": _clean(row[0]),
        "creation_date": _date(row[1]),
        "document_date": _date(row[2]),
        "due_date": _date(row[3]),
        "note": _clean(row[4]),
        "contract_document_reference": _clean(row[5]),
        "invoice_number": _clean(row[6]),
        "tender_number": _clean(row[7]),
        "partner_pib": _clean(row[8]),
        "partner_mb": _clean(row[9]),
        "partner_name": _clean(row[10]),
        "total": _decimal(row[11]),
        "base_amount": _decimal(row[12]),
        "payment_amount": _decimal(row[13]),
        "uom": _clean(row[14]),
        "item_name": _clean(row[15]),
        "quantity": _decimal(row[16], "0.001"),
        "price": _decimal(row[17]),
        "value": _decimal(row[18]),
        "account": _clean(row[19]),
    }
    values["source_key"] = _source_key(*row)
    return values


def _uf_invoice_group_key(item):
    invoice_number = _clean(item.invoice_number)
    partner_key = _clean(item.partner_pib) or _clean(item.partner_mb) or _clean(item.partner_name)
    fallback = _clean(item.purchase_invoice_id) or _clean(item.source_key)
    return _source_key(invoice_number or fallback, partner_key)


def _pick_latest_date(values):
    dates = [value for value in values if value]
    return max(dates) if dates else None


def _pick_first_text(values):
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _pick_first_decimal(values):
    for value in values:
        if value is not None:
            return value
    return None


@transaction.atomic
def rebuild_uf_invoice_snapshots():
    from nabavka.models import EufItemSnapshot, ProcurementItem, UfInvoiceSnapshot

    groups = {}
    for item in EufItemSnapshot.objects.all().order_by("invoice_number", "partner_name", "id"):
        source_key = _uf_invoice_group_key(item)
        groups.setdefault(source_key, []).append(item)

    invoice_ids = []
    synced_at = timezone.now()
    for source_key, items in groups.items():
        values = {
            "purchase_invoice_id": _pick_first_text(item.purchase_invoice_id for item in items),
            "invoice_number": _pick_first_text(item.invoice_number for item in items),
            "partner_pib": _pick_first_text(item.partner_pib for item in items),
            "partner_mb": _pick_first_text(item.partner_mb for item in items),
            "partner_name": _pick_first_text(item.partner_name for item in items),
            "document_date": _pick_latest_date(item.document_date for item in items),
            "creation_date": _pick_latest_date(item.creation_date for item in items),
            "due_date": _pick_latest_date(item.due_date for item in items),
            "total": _pick_first_decimal(item.total for item in items),
            "base_amount": _pick_first_decimal(item.base_amount for item in items),
            "payment_amount": _pick_first_decimal(item.payment_amount for item in items),
            "item_value_total": sum((item.value or Decimal("0.00")) for item in items),
            "item_count": len(items),
            "accounts": ", ".join(sorted({account for account in (_clean(item.account) for item in items) if account})),
            "synced_at": synced_at,
        }
        invoice, _ = UfInvoiceSnapshot.objects.update_or_create(
            source_key=source_key,
            defaults=values,
        )
        invoice_ids.append(invoice.pk)
        item_ids = [item.pk for item in items]
        EufItemSnapshot.objects.filter(pk__in=item_ids).update(uf_invoice=invoice)
        ProcurementItem.objects.filter(uf_item_id__in=item_ids, uf_invoice__isnull=True).update(uf_invoice=invoice)

    if invoice_ids:
        UfInvoiceSnapshot.objects.exclude(pk__in=invoice_ids).delete()
    else:
        UfInvoiceSnapshot.objects.all().delete()
    return invoice_ids


def sync_euf_item_snapshots(q=None, limit=10000):
    from nabavka.models import EufItemSnapshot

    snapshots = _bulk_upsert(EufItemSnapshot, list_euf_items(q=q, limit=limit))
    rebuild_uf_invoice_snapshots()
    return snapshots



def list_goods(q=None, limit=10000):
    q = _clean(q)
    params = []
    where = ""
    if q:
        where = """
            WHERE CONVERT(nvarchar(20), [br_dok]) LIKE %s
               OR LTRIM(RTRIM([naz_par])) LIKE %s
               OR LTRIM(RTRIM([sif_art])) LIKE %s
               OR LTRIM(RTRIM([naz_art])) LIKE %s
               OR LTRIM(RTRIM([vez_dok])) LIKE %s
        """
        like_value = f"%{q}%"
        params.extend([like_value] * 5)

    sql = f"""
        SELECT TOP ({_limit(limit)})
            god,
            br_dok,
            sif_vrs,
            oj,
            sif_par,
            naz_par,
            datum,
            vez_dok,
            potrazuje,
            skr_naz,
            deviza,
            sif_pred,
            stavka,
            sif_art,
            sif_vrsart,
            naz_art,
            kol,
            cena
        FROM dbo.nbv_roba
        {where}
        ORDER BY datum DESC, br_dok DESC, stavka
    """
    with connections["server_db"].cursor() as cursor:
        cursor.execute(sql, params)
        return [_goods_values(row) for row in cursor.fetchall()]


def _goods_values(row):
    values = {
        "year": _clean(row[0]),
        "document_number": row[1],
        "document_type": _clean(row[2]),
        "organizational_unit": row[3],
        "partner_code": row[4],
        "partner_name": _clean(row[5]),
        "document_date": _date(row[6]),
        "linked_document": _clean(row[7]),
        "debit": _decimal(row[8]),
        "currency": _clean(row[9]),
        "foreign_currency_amount": _decimal(row[10]),
        "subject_code": row[11],
        "line_number": row[12],
        "article_code": _clean(row[13]),
        "article_type": _clean(row[14]),
        "article_name": _clean(row[15]),
        "quantity": _decimal(row[16]),
        "price": _decimal(row[17]),
    }
    values["source_key"] = _source_key(*row)
    return values


def sync_goods_snapshots(q=None, limit=10000):
    from nabavka.models import GoodsSnapshot

    return _bulk_upsert(GoodsSnapshot, list_goods(q=q, limit=limit))
