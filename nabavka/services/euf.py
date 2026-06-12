from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256

from django.db import connections
from django.utils import timezone


@dataclass(frozen=True)
class EufInvoice:
    euf_key: str
    datum_raw: str
    datum: date | None
    naziv_partnera: str
    broj_fakture: str
    iznos: Decimal | None
    centar: str
    magacin: str
    registracija: str


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _clean(value)
    if not text:
        return None
    for date_format in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%b %d %Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def make_euf_key(datum, naziv_partnera, broj_fakture, iznos):
    amount = "" if iznos is None else str(Decimal(str(iznos)).quantize(Decimal("0.01")))
    raw = "|".join([
        _clean(datum),
        _clean(naziv_partnera),
        _clean(broj_fakture),
        amount,
    ])
    return sha256(raw.encode("utf-8")).hexdigest()


def _row_to_invoice(row):
    datum_raw = _clean(row[0])
    naziv_partnera = _clean(row[1])
    broj_fakture = _clean(row[2])
    iznos = Decimal(str(row[3])).quantize(Decimal("0.01")) if row[3] is not None else None
    return EufInvoice(
        euf_key=make_euf_key(datum_raw, naziv_partnera, broj_fakture, iznos),
        datum_raw=datum_raw,
        datum=_parse_date(row[0]),
        naziv_partnera=naziv_partnera,
        broj_fakture=broj_fakture,
        iznos=iznos,
        centar=_clean(row[4]),
        magacin=_clean(row[5]),
        registracija=_clean(row[6]),
    )


def list_euf_invoices(q=None, limit=500):
    q = _clean(q)
    limit = min(max(int(limit or 500), 1), 2000)
    params = []
    where = ""
    if q:
        where = """
            WHERE LTRIM(RTRIM([broj_fakutre])) LIKE %s
               OR LTRIM(RTRIM([naziv_partnera])) LIKE %s
        """
        like_value = f"%{q}%"
        params.extend([like_value, like_value])

    sql = f"""
        SELECT TOP ({limit})
            datum,
            naziv_partnera,
            broj_fakutre,
            iznos,
            centar,
            magacin,
            registracija
        FROM dbo.nbv_preuzete_EUF
        {where}
        ORDER BY TRY_CONVERT(date, datum) DESC, LTRIM(RTRIM(broj_fakutre))
    """
    with connections["server_db"].cursor() as cursor:
        cursor.execute(sql, params)
        return [_row_to_invoice(row) for row in cursor.fetchall()]


def get_euf_invoice(euf_key):
    wanted = _clean(euf_key)
    if not wanted:
        return None
    for invoice in list_euf_invoices(limit=2000):
        if invoice.euf_key == wanted:
            return invoice
    return None


def upsert_euf_invoice_snapshot(invoice):
    from nabavka.models import ProcurementInvoice

    obj, created = ProcurementInvoice.objects.get_or_create(
        source=ProcurementInvoice.SOURCE_EUF,
        euf_key=invoice.euf_key,
        defaults={
            "invoice_number": invoice.broj_fakture,
            "invoice_date": invoice.datum,
            "invoice_date_raw": invoice.datum_raw,
            "supplier_name": invoice.naziv_partnera,
            "amount": invoice.iznos,
            "center": invoice.centar,
            "warehouse": invoice.magacin,
            "registration": invoice.registracija,
            "center_name": invoice.centar,
            "goes_to_warehouse": bool(invoice.magacin),
            "is_returned": False,
            "synced_at": timezone.now(),
        },
    )
    if not created:
        obj.invoice_number = invoice.broj_fakture
        obj.invoice_date = invoice.datum
        obj.invoice_date_raw = invoice.datum_raw
        obj.supplier_name = invoice.naziv_partnera
        obj.amount = invoice.iznos
        obj.center = invoice.centar
        obj.warehouse = invoice.magacin
        obj.registration = invoice.registracija
        obj.synced_at = timezone.now()
        obj.save(
            update_fields=[
                "invoice_number",
                "invoice_date",
                "invoice_date_raw",
                "supplier_name",
                "amount",
                "center",
                "warehouse",
                "registration",
                "synced_at",
                "updated_at",
            ]
        )
    return obj


def sync_euf_invoice_snapshots(q=None, limit=2000):
    invoices = list_euf_invoices(q=q, limit=limit)
    return [upsert_euf_invoice_snapshot(invoice) for invoice in invoices]
