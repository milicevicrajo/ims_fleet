"""Overview charts and rankings from authorized ledger entries only."""
from decimal import Decimal

from django.db.models import Max

from .reports import ZERO, expressions


METRICS = (("revenue", "Prihodi"), ("expense", "Rashodi"), ("result", "Neto rezultat"))


def overview_data(entries, totals):
    groups = []
    for dimension, field, heading in (
        ("center", "center", "Centri / organizacione jedinice"),
        ("job", "job_code", "Šifre posla"),
    ):
        annotations = expressions()
        if dimension == "job":
            annotations["name"] = Max("job_name")
        records = entries.order_by().values(field).annotate(**annotations)
        rows = []
        for record in records:
            revenue, expense = record["revenue"] or ZERO, record["expense"] or ZERO
            code = record[field]
            rows.append({
                "code": code,
                "label": (f"Centar {code}" if code else "Neraspoređeno") if dimension == "center" else code or "Bez šifre posla",
                "name": record.get("name", ""), "revenue": revenue, "expense": expense,
                "result": revenue - expense, "count": record["count"],
            })
        # Keep the same entity on each line across all three columns.
        rows.sort(key=lambda row: (-row["result"], row["code"]))
        # Each full track is 100% of that metric's total, not the largest row.
        # Net participation can exceed 100% when other jobs/centers have losses.
        for row in rows:
            row["metrics"] = []
            for metric, title in METRICS:
                value = row[metric]
                share = value / totals[metric] * 100 if totals[metric] else None
                row["metrics"].append({
                    "key": metric, "title": title, "value": value,
                    "share": share,
                    "width": format(min(abs(share), Decimal("100")) if share is not None else ZERO, ".4f"),
                    "overflow": share is not None and abs(share) > 100,
                    "negative": value < 0,
                })
        # Missing codes remain in charts/totals, but are not ranked as actual jobs/centers.
        ranked = [row for row in rows if row["code"] and (row["revenue"] or row["expense"])]
        top_count = 3 if dimension == "job" else 1
        best = ranked[:top_count]
        worst = sorted(ranked, key=lambda row: (row["result"], row["code"]))[:top_count]
        visible_count = 8 if dimension == "job" else len(rows)
        groups.append({
            "dimension": dimension, "heading": heading, "rows": rows,
            "visible": rows[:visible_count], "remaining": rows[visible_count:],
            "has_overflow": any(metric["overflow"] for row in rows for metric in row["metrics"]),
            "best": best, "worst": worst,
        })
    centers, jobs = groups
    return {
        "chart_groups": groups,
        "rankings": [
            {"title": "Najbolje 3 šifre posla", "rows": jobs["best"], "kind": "best", "icon": "mdi-trending-up"},
            {"title": "Najgore 3 šifre posla", "rows": jobs["worst"], "kind": "worst", "icon": "mdi-trending-down"},
            {"title": "Najbolji centar", "rows": centers["best"], "kind": "best", "icon": "mdi-trophy-outline"},
            {"title": "Najgori centar", "rows": centers["worst"], "kind": "worst", "icon": "mdi-chart-bar"},
        ],
    }
