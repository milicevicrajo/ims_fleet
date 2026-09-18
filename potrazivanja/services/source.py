"""Read-only capture of the existing Naplata contract, including legacy evidence.

No view is rewritten and no SQL supplied by the browser is executed. Full means
all rows of these sources, not only open invoices or rows changed since last run.
"""
from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal
import hashlib
import json

from django.db import connections
from django.utils import timezone

SOURCES = (
    "partneri", "baza", "ispravke", "v_tuzeni", "v_if", "v_duplikati",
    "dodela_baketa", "v_neodobreneIF", "tabela_if", "duplikati18",
    "kontakti", "napomene", "opomene", "poziv_pismo", "pozivi_tel", "tuzbe",
    "sif_baket", "sif_kategorija", "avans_klijent", "postupak", "promena_postupka", "posao",
)
LEGACY_SOURCES = {"kontakti", "napomene", "opomene", "poziv_pismo", "pozivi_tel", "tuzbe", "avans_klijent", "postupak", "promena_postupka"}
FINANCIAL_SOURCES = tuple(name for name in SOURCES if name not in LEGACY_SOURCES)


def text(value):
    return "" if value is None else str(value).strip()


def integer(value):
    if value is None or value == "":
        return None
    number = Decimal(str(value))
    if not number.is_finite() or number != number.to_integral_value():
        return None
    return int(number)


def money(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def day(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def timestamp(value):
    if not value:
        return None
    if not isinstance(value, datetime):
        value = datetime.fromisoformat(str(value))
    return timezone.make_aware(value) if timezone.is_naive(value) else value


def serial(value):
    if isinstance(value, datetime) and timezone.is_aware(value):
        return str(value.astimezone(dt_timezone.utc))
    if isinstance(value, (Decimal, datetime, date)):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    raise TypeError(type(value).__name__)


def payload(value):
    return json.loads(json.dumps(value, default=serial, ensure_ascii=False))


def digest(value):
    return hashlib.sha256(json.dumps(value, default=serial, sort_keys=True,
                                    ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def fingerprint(rows):
    # Ignore ordering, preserve duplicates. GETDATE is capture metadata, not content.
    hashes = sorted(digest({k: v for k, v in row.items() if k != "danasnji_datum"}) for row in rows)
    return hashlib.sha256("".join(hashes).encode()).hexdigest()


def read_table(cursor, name):
    if name not in SOURCES:
        raise ValueError("Nepoznat izvor.")
    if name == "posao":
        cursor.execute("SELECT * FROM [PUTGEO-SERVER].[bazaims].dbo.posao WHERE sif_pred=1")
    else:
        cursor.execute(f"SELECT * FROM dbo.[{name}]")
    columns = [column[0].lower() for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def extract(progress=None, *, include_legacy=False):
    data = {}
    db = connections["server_db"]
    db.ensure_connection()
    previous_timeout = db.connection.timeout
    db.connection.timeout = 900
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT GETDATE()")
            observed = timestamp(cursor.fetchone()[0])
            for name in (SOURCES if include_legacy else FINANCIAL_SOURCES):
                data[name] = read_table(cursor, name)
                if progress:
                    progress(f"Izvor {name}: {len(data[name])} redova")
            # Detect changes during extraction instead of publishing mixed balances.
            for name in ("baza", "ispravke", "dodela_baketa"):
                if fingerprint(read_table(cursor, name)) != fingerprint(data[name]):
                    raise ValueError(f"Izvor {name} se promenio tokom čitanja. Ponovite sinhronizaciju.")
            cursor.execute("SELECT GETDATE()")
            if day(cursor.fetchone()[0]) != observed.date():
                raise ValueError("Datum izvora promenjen tokom čitanja; ponovite sinhronizaciju.")
    finally:
        db.connection.timeout = previous_timeout
    return data, observed
