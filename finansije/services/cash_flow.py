"""Read-only equivalent of SPFINizv52nt's job cash-flow preparation.

Preserves its VAT, payroll and account replacements, including their signs.
Never writes the shared posao_mes P&L/cash-flow fields.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.db import connections, DataError

from .source import SOURCE, clean

ZERO = Decimal("0")
ON_ACCOUNTS = {"61420", "61300", "61520", "52901", "52991", "52610", "52620",
               "57910", "53011", "61211", "61421", "61521"}
REPLACEMENTS = (
    ({"46520", "48923", "48900", "48903"}, "52400"),
    ({"46510", "48920", "48981"}, "52300"),
    ({"46500", "48921", "48980"}, "52200"),
    ({"46400", "48960"}, "52600"),
)
WAGE_LIABILITIES = {"45000", "45100", "45200", "45220", "45210", "45310", "45312", "45314"}
REFUND_ACCOUNTS = {"22500", "22510", "22520", "23837"}
REFUND_REPLACEMENTS = {"45400", "45410", "45420", "45503", "45600"} | REFUND_ACCOUNTS


def vat_period(first, last):
    """Exactly the payment-month shift used by 52nt, including January rollover."""
    previous = 12 if first == 1 else -1
    lower, upper = (first or 0) - 1, (last or 0) - 1
    return (-1 if lower == 0 else lower), (-1 if upper == 0 else upper), previous


def unique_map(rows):
    result = {}
    for key, value in rows:
        key = clean(key)
        if key in result:
            raise DataError("Dupliran šifarnik za obračun novčanih tokova.")
        result[key] = clean(value) if value is not None else None
    return result


def fetch_inputs(company, code, start, end):
    if start.year != end.year or start > end or start.year < 2025:
        raise ValueError("Neispravan period novčanih tokova.")
    # Empty source job codes are assigned to 111111 by the original procedure.
    job_filter = "(sif_pos=%s OR (%s='111111' AND (sif_pos IS NULL OR LTRIM(RTRIM(sif_pos))='')))"
    with connections["server_db"].cursor() as cursor:
        cursor.execute(f"""SELECT knt,dat_naloga,sif_vrs,SUM(duguje),SUM(potrazuje)
            FROM {SOURCE}.nalog_z WHERE sif_pred=%s AND god=%s AND dat_naloga BETWEEN %s AND %s
            AND {job_filter} GROUP BY knt,dat_naloga,sif_vrs""", [company, str(start.year), start, end, code, code])
        postings = [{"account": clean(r[0]), "date": r[1].date() if hasattr(r[1], "date") else r[1],
                     "kind": clean(r[2]), "debit": r[3] or ZERO, "credit": r[4] or ZERO} for r in cursor.fetchall()]
        cursor.execute(f"SELECT knt,nt FROM {SOURCE}.konto WHERE sif_pred=%s", [company])
        accounts = unique_map(cursor.fetchall())
        cursor.execute(f"SELECT v.sif_vrs,t.sif_tipnal FROM {SOURCE}.vrsta_naloga v INNER JOIN {SOURCE}.tipnal t ON v.sif_tipnal=t.sif_tipnal")
        types = unique_map(cursor.fetchall())
        cursor.execute("SELECT DISTINCT knt_troska FROM [PUTGEO-SERVER].[bazaldims].dbo.element WHERE knt_troska NOT IN ('52024','52026')")
        wages = {clean(r[0]) for r in cursor.fetchall()} | {"52100"}
        cursor.execute(f"""SELECT MIN(MONTH(dat_naloga)),MAX(MONTH(dat_naloga)) FROM {SOURCE}.nalog_z
            WHERE sif_pred=%s AND god=%s AND knt='47900' AND duguje<>0 AND dat_naloga BETWEEN %s AND %s""",
            [company, str(start.year), start, end])
        lower, upper, previous = vat_period(*cursor.fetchone())
        cursor.execute(f"""SELECT SUM(CASE WHEN tip='I' THEN pdv+pdv8 ELSE -(pdv+pdv8) END)
            FROM {SOURCE}.pdv_arhiva WHERE sif_pred=%s AND pdv_nacoporez='S' AND br_obr<>0
            AND ((god=%s AND br_obr BETWEEN %s AND %s) OR (god=%s AND br_obr=%s)) AND {job_filter}""",
            [company, str(start.year), lower, upper, str(start.year - 1), previous, code, code])
        vat = cursor.fetchone()[0] or ZERO
        cursor.execute(f"SELECT mesec FROM {SOURCE}.posao_mes WHERE sif_pred=%s AND god=%s AND sif_pos=%s AND aktivan='D' AND mesec BETWEEN %s AND %s",
                       [company, str(start.year), code, start.month, end.month])
        active = [r[0] for r in cursor.fetchall()]
        if len(active) != len(set(active)):
            raise DataError("Duplirana mesečna evidencija novčanih tokova.")
    return postings, accounts, types, wages, vat, set(active)


def calculate(postings, accounts, types, wages, vat, active_months, end):
    if not active_months:
        return {"available": False, "note": "Nema aktivne mesečne evidencije ove šifre za obračun novčanih tokova."}
    rows = []
    for row in postings:
        account, kind = row["account"], row["kind"]
        if account not in accounts or kind not in types:
            continue
        if types[kind] == "NT" and accounts[account] is not None and accounts[account] != "NT":
            rows.append(row)
        if kind == "ON" and account in ON_ACCOUNTS:
            rows.append(row)
    rows = [r for r in rows if r["account"] != "47900"]
    rows.append({"account": "47900", "date": end, "debit": vat, "credit": ZERO})
    for excluded, replacement in REPLACEMENTS:
        rows = [r for r in rows if r["account"] not in excluded]
        rows.extend({**r, "credit": ZERO} for r in postings if r["account"] == replacement)
    rows = [r for r in rows if r["account"] not in WAGE_LIABILITIES]
    rows.extend({**r, "credit": ZERO} for r in postings if r["account"] in wages)
    rows = [r for r in rows if r["account"] not in REFUND_REPLACEMENTS]
    rows.extend({**r, "debit": ZERO, "credit": r["credit"] - r["debit"]}
                for r in postings if r["account"] in REFUND_ACCOUNTS and r["kind"] in types)
    rows = [r for r in rows if not r["account"].startswith("241") and r["account"] in accounts
            and r["date"].month in active_months]
    inflow = sum((r["credit"] for r in rows), ZERO).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    outflow = sum((r["debit"] for r in rows), ZERO).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"available": True, "inflow": inflow, "outflow": outflow, "net": inflow - outflow,
            "note": "Novčani tokovi prema obračunu 52nt, sa njegovim korekcijama PDV-a i zarada; nisu isto što i zbir bankovnih uplata/isplata."}


def cash_flow(company, code, start, end):
    inputs = fetch_inputs(company, code, start, end)
    result = calculate(*inputs, end=end)
    if result["available"] and len(inputs[-1]) < end.month - start.month + 1:
        result["complete"] = False
        result["note"] += f" Aktivna mesečna evidencija postoji za {len(inputs[-1])} od {end.month - start.month + 1} meseci perioda."
    return result


def cash_flow_many(company, codes, start, end):
    """Read period inputs once; apply the same 52nt calculation to each requested job."""
    if start.year != end.year or start > end or start.year < 2025:
        raise ValueError("Neispravan period novčanih tokova.")
    codes = set(codes)
    if not codes:
        return {}
    postings, vat, active = {code: [] for code in codes}, {}, {code: [] for code in codes}
    with connections["server_db"].cursor() as cursor:
        cursor.execute(f"""SELECT sif_pos,knt,dat_naloga,sif_vrs,SUM(duguje),SUM(potrazuje)
            FROM {SOURCE}.nalog_z WHERE sif_pred=%s AND god=%s AND dat_naloga BETWEEN %s AND %s
            GROUP BY sif_pos,knt,dat_naloga,sif_vrs""", [company, str(start.year), start, end])
        for row in cursor.fetchall():
            code = clean(row[0]) or "111111"
            if code in codes:
                postings[code].append({"account": clean(row[1]), "date": row[2].date() if hasattr(row[2], "date") else row[2],
                                       "kind": clean(row[3]), "debit": row[4] or ZERO, "credit": row[5] or ZERO})
        cursor.execute(f"SELECT knt,nt FROM {SOURCE}.konto WHERE sif_pred=%s", [company])
        accounts = unique_map(cursor.fetchall())
        cursor.execute(f"SELECT v.sif_vrs,t.sif_tipnal FROM {SOURCE}.vrsta_naloga v INNER JOIN {SOURCE}.tipnal t ON v.sif_tipnal=t.sif_tipnal")
        types = unique_map(cursor.fetchall())
        cursor.execute("SELECT DISTINCT knt_troska FROM [PUTGEO-SERVER].[bazaldims].dbo.element WHERE knt_troska NOT IN ('52024','52026')")
        wages = {clean(row[0]) for row in cursor.fetchall()} | {"52100"}
        cursor.execute(f"""SELECT MIN(MONTH(dat_naloga)),MAX(MONTH(dat_naloga)) FROM {SOURCE}.nalog_z
            WHERE sif_pred=%s AND god=%s AND knt='47900' AND duguje<>0 AND dat_naloga BETWEEN %s AND %s""",
            [company, str(start.year), start, end])
        lower, upper, previous = vat_period(*cursor.fetchone())
        cursor.execute(f"""SELECT sif_pos,SUM(CASE WHEN tip='I' THEN pdv+pdv8 ELSE -(pdv+pdv8) END)
            FROM {SOURCE}.pdv_arhiva WHERE sif_pred=%s AND pdv_nacoporez='S' AND br_obr<>0
            AND ((god=%s AND br_obr BETWEEN %s AND %s) OR (god=%s AND br_obr=%s)) GROUP BY sif_pos""",
            [company, str(start.year), lower, upper, str(start.year - 1), previous])
        for code, amount in cursor.fetchall():
            code = clean(code) or "111111"
            if code in codes:
                vat[code] = vat.get(code, ZERO) + (amount or ZERO)
        cursor.execute(f"""SELECT sif_pos,mesec FROM {SOURCE}.posao_mes WHERE sif_pred=%s AND god=%s
            AND aktivan='D' AND mesec BETWEEN %s AND %s""", [company, str(start.year), start.month, end.month])
        for code, month in cursor.fetchall():
            code = clean(code)
            if code in codes:
                active[code].append(month)
    results = {}
    for code in codes:
        months = active[code]
        if len(months) != len(set(months)):
            results[code] = {"available": False, "note": "Duplirana mesečna evidencija novčanih tokova."}
            continue
        result = calculate(postings[code], accounts, types, wages, vat.get(code, ZERO), set(months), end)
        if result["available"]:
            result["complete"] = len(months) == end.month - start.month + 1
            if not result["complete"]:
                result["note"] += f" Aktivna evidencija: {len(months)} od {end.month - start.month + 1} meseci."
        results[code] = result
    return results
