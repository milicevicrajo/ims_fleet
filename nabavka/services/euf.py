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
    naziv_dokumenta: str = ""


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
        naziv_dokumenta=_clean(row[7]) if len(row) > 7 else "",
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
            registracija,
            Naziv
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
            "document_type": invoice.naziv_dokumenta or None,
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
        if invoice.naziv_dokumenta:
            obj.document_type = invoice.naziv_dokumenta
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
                "document_type",
                "synced_at",
                "updated_at",
            ]
        )
    return obj


def sync_euf_invoice_snapshots(q=None, limit=2000):
    invoices = list_euf_invoices(q=q, limit=limit)
    snapshots = [upsert_euf_invoice_snapshot(invoice) for invoice in invoices]
    dopuni_vrstu_i_pib()
    return snapshots


def _pibovi_partnera():
    """(broj fakture, partner) → PIB iz izvorne EUF tabele; pogled nbv_preuzete_EUF PIB ne daje.

    Samo citanje. Ako izvor nije dostupan, vraca prazno (PIB ostaje kakav je bio).
    """
    sql = """
        SELECT LTRIM(RTRIM([InvID])), LTRIM(RTRIM([PartnerIme])), LTRIM(RTRIM([PartnerPIB]))
        FROM [putgeo-server].[EFaktura].[dbo].[EUL_Dok]
        WHERE YEAR([CreationDate]) >= 2026
    """
    try:
        with connections["server_db"].cursor() as cursor:
            cursor.execute(sql)
            return {(broj or "", partner or ""): pib or "" for broj, partner, pib in cursor.fetchall()}
    except Exception:  # povezani server nedostupan — ne rusi preuzimanje faktura
        return {}


def dopuni_vrstu_i_pib():
    """Vrsta dokumenta i PIB partnera za SVE preuzete EUF fakture (ne samo poslednjih 2.000).

    Menja samo redove koji se razlikuju. Vraca broj izmenjenih faktura.
    """
    from nabavka.models import ProcurementInvoice

    with connections["server_db"].cursor() as cursor:
        cursor.execute("SELECT datum, naziv_partnera, broj_fakutre, iznos, centar, magacin, registracija, Naziv "
                       "FROM dbo.nbv_preuzete_EUF")
        izvor = [_row_to_invoice(row) for row in cursor.fetchall()]
    pibovi = _pibovi_partnera()
    po_kljucu = {i.euf_key: (i.naziv_dokumenta or None, pibovi.get((i.broj_fakture, i.naziv_partnera)) or None)
                 for i in izvor}
    izmenjeno = 0
    for pk, kljuc, vrsta, pib in ProcurementInvoice.objects.filter(source=ProcurementInvoice.SOURCE_EUF).values_list(
            "pk", "euf_key", "document_type", "partner_pib"):
        if kljuc not in po_kljucu:
            continue
        nova_vrsta, novi_pib = po_kljucu[kljuc]
        nova_vrsta, novi_pib = nova_vrsta or vrsta, novi_pib or pib
        if (nova_vrsta, novi_pib) != (vrsta, pib):
            izmenjeno += ProcurementInvoice.objects.filter(pk=pk).update(document_type=nova_vrsta, partner_pib=novi_pib)
    return izmenjeno


def pib_banaka():
    """PIB-ovi banaka: `select pib from partneri where grupa = 11` (samo citanje, keš 1 h)."""
    from django.core.cache import cache

    pibovi = cache.get("nabavka:pib_banaka")
    if pibovi is None:
        try:
            with connections["server_db"].cursor() as cursor:
                cursor.execute("SELECT DISTINCT LTRIM(RTRIM(CAST(pib AS varchar(20)))) FROM dbo.partneri WHERE grupa = 11")
                pibovi = {pib for (pib,) in cursor.fetchall() if pib}
        except Exception:
            pibovi = set()
        cache.set("nabavka:pib_banaka", pibovi, 60 * 60)
    return pibovi


def oznake_reda(invoice, banke):
    """Vrsta isticanja reda u spisku i izvozu: avans (po nazivu dokumenta) i banka (po PIB-u)."""
    oznake = []
    if (invoice.document_type or "").strip().lower().startswith("avans"):
        oznake.append("avans")
    if invoice.partner_pib and invoice.partner_pib.strip() in banke:
        oznake.append("banka")
    return oznake
