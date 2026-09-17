"""Batch financial metrics for the authorized job overview."""
from datetime import date
from decimal import Decimal
import logging

from django.conf import settings
from django.db import DatabaseError
from django.utils.html import format_html

from finansije.templatetags.finance import amount_badge, finance_job_button
from .cash_flow import cash_flow_many
from .shared_costs import shared_cost_many
from .job_tables import cell, money


logger = logging.getLogger(__name__)
ZERO = Decimal("0")
METRICS = ("revenue", "expense", "result", "shared_cost", "after_shared", "inflow", "outflow", "net_cash")
LABELS = ("Prihodi", "Rashodi", "Rezultat bez ZT", "Zajednički troškovi", "Rezultat P − R − ZT",
          "Priliv", "Odliv", "Neto gotovina")


def enrich_jobs(rows, start, end, covered):
    company = getattr(settings, "FINANSIJE_COMPANY", 1)
    codes = {row["code"] for row in rows if row["code"]}
    parts = {code: {"shared": [], "cash": []} for code in codes}
    for year in range(start.year, end.year + 1):
        lower, upper = max(start, date(year, 1, 1)), min(end, date(year, 12, 31))
        for name, calculate in (("shared", shared_cost_many), ("cash", cash_flow_many)):
            if not codes:
                continue
            if year not in covered:
                data = {}
                note = f"Nema potvrđenih sinhronizovanih podataka za {year}."
            else:
                note = "Nema podataka za ovu šifru i period."
                try:
                    data = calculate(company, codes, lower, upper)
                except DatabaseError:
                    logger.exception("Zbirna analiza poslova nije dostupna: %s / %s", name, year)
                    data = {}
                    note = "Izvor obračuna trenutno nije dostupan. Pokušajte ponovo."
            for code in codes:
                parts[code][name].append(data.get(code, {"available": False, "note": note}))
    complete_ledger = all(year in covered for year in range(start.year, end.year + 1))
    for row in rows:
        row["metrics"] = {}
        for key in ("revenue", "expense", "result"):
            value = row[key] if complete_ledger else None
            row["metrics"][key] = {"value": -value if key == "expense" and value is not None else value,
                "complete": complete_ledger, "note": "" if complete_ledger else "Nedostaje sinhronizacija dela izabranog perioda."}
        for name, mapping in (("shared", {"shared_cost": "cost"}),
                              ("cash", {"inflow": "inflow", "outflow": "outflow", "net_cash": "net"})):
            results = parts.get(row["code"], {}).get(name, [])
            available = bool(results) and all(part["available"] for part in results)
            complete = available and all(part.get("complete", True) for part in results)
            note = " ".join(dict.fromkeys(part.get("note", "") for part in results)) or "Nema šifre posla za obračun."
            for key, field in mapping.items():
                value = sum((part[field] for part in results), ZERO) if available else None
                row["metrics"][key] = {"value": -value if key in ("shared_cost", "outflow") and value is not None else value,
                                       "complete": complete, "note": note}
        shared = row["metrics"]["shared_cost"]
        row["metrics"]["after_shared"] = {
            "value": row["result"] + shared["value"] if complete_ledger and shared["value"] is not None else None,
            "complete": complete_ledger and shared["complete"], "note": shared["note"],
        }
    return rows


def metric_cell(metric):
    if metric["value"] is None:
        return cell(None, format_html('<span class="text-muted" title="{}">—</span>', metric["note"]))
    result = money(metric["value"])
    if not metric["complete"]:
        result["display"] = str(format_html('{} <span class="text-warning" title="{}" aria-label="Nepotpun obračun">*</span>',
                                            amount_badge(metric["value"]), metric["note"]))
    return result


def table_data(rows):
    data = []
    for row in rows:
        url = row.get("card_url") if row["code"] else None
        code = cell(row["code"], finance_job_button(row["code"], url)) if url else cell("Bez šifre")
        cells = [code, cell(row["label"]), cell(row.get("center", ""))]
        cells.extend(metric_cell(row["metrics"][key]) for key in METRICS)
        data.append(cells)
    return {"data": data}
