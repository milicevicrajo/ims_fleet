"""Read-only access to the accounting source. No business procedures are executed."""
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json

from django.conf import settings
from django.db import connections


KEY_FIELDS = ("company", "year", "journal_type", "journal_number", "line_number")
SOURCE_FIELDS = (
    "company", "year", "journal_type", "journal_number", "line_number",
    "organizational_unit", "account", "partner_group", "partner_code",
    "document_date", "document_reference", "debit", "credit", "currency",
    "foreign_amount", "description", "linked_line", "due_date", "change_status",
    "job_code", "booking_date", "debit_credit_flag", "source_paid_amount",
)
TEXT_FIELDS = {
    "journal_type", "account", "document_reference", "currency", "description",
    "change_status", "job_code", "debit_credit_flag",
}
MONEY_FIELDS = {"debit", "credit", "foreign_amount", "source_paid_amount"}
SOURCE = "[PUTGEO-SERVER].[bazaims].dbo"


def clean(value):
    return "" if value is None else str(value).strip()


def source_key(row):
    return tuple(row[name] for name in KEY_FIELDS)


def fingerprint(row):
    return sha256(json.dumps(row, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def totals_for(rows):
    totals = {}
    for row in rows:
        # Reconciliation by year and account catches redistribution between accounts.
        key = f"{row['year']}:{row['account']}"
        item = totals.setdefault(key, {"count": 0, "debit": Decimal("0"), "credit": Decimal("0")})
        item["count"] += 1
        item["debit"] += row["debit"]
        item["credit"] += row["credit"]
    return totals


def unique_map(rows, key_columns):
    result = {}
    for row in rows:
        key = tuple(clean(value) for value in row[:key_columns])
        if key in result:
            raise ValueError("Dupliran ključ izvornog šifarnika; sinhronizacija je zaustavljena.")
        result[key] = row[key_columns:]
    return result


def fetch_source(company, year_from, year_to):
    alias = getattr(settings, "FINANSIJE_SOURCE_DB", "server_db")
    with connections[alias].cursor() as cursor:
        cursor.execute(f"SELECT sif_pos, naz_pos, blok, aktivan, profitni FROM {SOURCE}.posao WHERE sif_pred=%s", [company])
        jobs = unique_map(cursor.fetchall(), 1)
        cursor.execute(f"SELECT knt, naz_knt FROM {SOURCE}.konto WHERE sif_pred=%s", [company])
        accounts = unique_map(cursor.fetchall(), 1)
        cursor.execute(f"SELECT god, oj, naz_oj FROM {SOURCE}.ob_jedin WHERE sif_pred=%s AND god BETWEEN %s AND %s", [company, str(year_from), str(year_to)])
        units = unique_map(cursor.fetchall(), 2)
        cursor.execute(f"SELECT grupa, sif_par, naz_par FROM {SOURCE}.partner WHERE sif_pred=%s", [company])
        partners = unique_map(cursor.fetchall(), 2)
        cursor.execute(f"""
            SELECT sif_pred, god, sif_vrs, br_naloga, stavka, oj, knt, grupa, sif_par,
                   datum, vez_dok, duguje, potrazuje, skr_naz, deviza, kom, stavka_k,
                   dpo, promena, sif_pos, dat_naloga, d_p, placeno
            FROM {SOURCE}.nalog_z
            WHERE sif_pred=%s AND god BETWEEN %s AND %s
        """, [company, str(year_from), str(year_to)])
        rows = []
        while True:
            batch = cursor.fetchmany(2000)
            if not batch:
                break
            for values in batch:
                row = dict(zip(SOURCE_FIELDS, values))
                row["year"] = int(row["year"])
                for name in TEXT_FIELDS:
                    row[name] = clean(row[name])
                for name in MONEY_FIELDS:
                    if row[name] is not None:
                        row[name] = Decimal(str(row[name])).quantize(Decimal("0.01"))
                for name in ("document_date", "booking_date", "due_date"):
                    if isinstance(row[name], datetime):
                        row[name] = row[name].date()
                job = jobs.get((row["job_code"],), ("", "", "", ""))
                row.update(
                    job_name=clean(job[0]), center=clean(job[1]),
                    account_name=clean(accounts.get((row["account"],), ("",))[0]),
                    organizational_unit_name=clean(units.get((str(row["year"]), str(row["organizational_unit"])), ("",))[0]),
                    partner_name=clean(partners.get((clean(row["partner_group"]), clean(row["partner_code"])), ("",))[0]),
                )
                rows.append(row)
        cursor.execute(f"""
            SELECT god, knt, COUNT_BIG(*), SUM(duguje), SUM(potrazuje)
            FROM {SOURCE}.nalog_z WHERE sif_pred=%s AND god BETWEEN %s AND %s
            GROUP BY god, knt
        """, [company, str(year_from), str(year_to)])
        expected = {
            f"{int(year)}:{clean(account)}": {"count": int(count), "debit": debit, "credit": credit}
            for year, account, count, debit, credit in cursor.fetchall()
        }
    if totals_for(rows) != expected:
        raise ValueError("Izvor je izmenjen tokom čitanja ili preuzimanje nije potpuno. Ponovite sinhronizaciju.")
    job_rows = [dict(company=company, code=key[0], name=clean(v[0]), center=clean(v[1]), active=clean(v[2]) == "D", profit_type=clean(v[3])) for key, v in jobs.items()]
    return rows, job_rows
