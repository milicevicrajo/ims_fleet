from decimal import Decimal

from django.conf import settings
from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import ExtractMonth, ExtractYear

from finansije.access import visible_scope
from finansije.models import FinanceJob, LedgerEntry


ZERO = Decimal("0.00")
# Confirmed in the source ledger: ZAT closes income/expense accounts, while
# 59900/69900 transfer their balances to the result (also posted through ON).
# Ordinary ON postings and corrections on 59120/69120 must remain included.
CLOSING_POSTINGS = Q(journal_type="ZAT") | Q(account__in=("59900", "69900"))


def base_querysets(user):
    company = getattr(settings, "FINANSIJE_COMPANY", 1)
    entries = visible_scope(LedgerEntry.objects.filter(company=company, active=True), user)
    jobs = visible_scope(FinanceJob.objects.filter(company=company), user, "code")
    return entries, jobs


def apply_filters(entries, filters):
    entries = entries.filter(booking_date__range=(filters["date_from"], filters["date_to"]))
    if filters["kind"] != "all":
        entries = entries.exclude(CLOSING_POSTINGS)
    for name, field in (("center", "center"), ("job", "job_code")):
        if filters.get(name):
            entries = entries.filter(**{field: "" if filters[name] == "__none__" else filters[name]})
    if filters.get("unit"):
        entries = entries.filter(organizational_unit=int(filters["unit"]))
    if filters.get("account"):
        entries = entries.filter(**{"account" if filters.get("account_exact") else "account__startswith": filters["account"]})
    if filters["kind"] == "revenue":
        entries = entries.filter(account__startswith="6")
    elif filters["kind"] == "expense":
        entries = entries.filter(account__startswith="5")
    elif filters["kind"] == "pnl":
        entries = entries.filter(Q(account__startswith="5") | Q(account__startswith="6"))
    return entries


def expressions():
    amount = DecimalField(max_digits=24, decimal_places=2)
    return {
        "revenue": Sum(Case(When(Q(account__startswith="6") & ~CLOSING_POSTINGS, then=F("credit") - F("debit")), default=Value(ZERO), output_field=amount)),
        "expense": Sum(Case(When(Q(account__startswith="5") & ~CLOSING_POSTINGS, then=F("debit") - F("credit")), default=Value(ZERO), output_field=amount)),
        "count": Count("pk"),
    }


def summary(entries):
    result = entries.aggregate(**expressions())
    result["revenue"] = result["revenue"] or ZERO
    result["expense"] = result["expense"] or ZERO
    result["result"] = result["revenue"] - result["expense"]
    return result


def grouped_report(entries, jobs, filters):
    group = filters["group"]
    fields = {"center": ["center"], "job": ["job_code", "job_name", "center"], "account": ["account", "account_name"]}
    if group == "month":
        grouped = entries.annotate(report_year=ExtractYear("booking_date"), report_month=ExtractMonth("booking_date")).values("report_year", "report_month").annotate(**expressions()).order_by("report_year", "report_month")
    else:
        grouped = entries.order_by().values(*fields[group]).annotate(**expressions()).order_by(*fields[group])
    totals = summary(entries)
    rows = []
    if group == "center":
        from fleet.support.registar import Registar

        registar = Registar()
    for item in grouped:
        if group == "center":
            # Kljuc je i dalje `center` sa knjizenja; iz registra je samo naziv centra.
            code, label = item["center"], (registar.oznaka_centra(item["center"]) if item["center"] else "Neraspoređeno")
        elif group == "job":
            code, label = item["job_code"], item["job_name"] or "Bez naziva"
        elif group == "account":
            code, label = item["account"], item["account_name"] or "Bez naziva konta"
        else:
            code = label = f"{item['report_year']}-{item['report_month']:02d}"
        rows.append(dict(item, code=code, label=label))
    if group == "job" and filters.get("include_empty"):
        present = {row["code"] for row in rows}
        if filters.get("center"):
            jobs = jobs.filter(center="" if filters["center"] == "__none__" else filters["center"])
        if filters.get("job"):
            jobs = jobs.filter(code="" if filters["job"] == "__none__" else filters["job"])
        # Units are posting attributes, not job attributes. Never invent a job→OJ mapping.
        if filters.get("unit"):
            jobs = jobs.filter(code__in=LedgerEntry.objects.filter(company=getattr(settings, "FINANSIJE_COMPANY", 1), active=True, organizational_unit=int(filters["unit"])).values("job_code"))
        rows.extend(dict(code=job.code, label=job.name or "Bez naziva", center=job.center, revenue=ZERO, expense=ZERO, count=0) for job in jobs if job.code not in present)
        rows.sort(key=lambda row: row["code"])
    for row in rows:
        row["revenue"] = row["revenue"] or ZERO
        row["expense"] = row["expense"] or ZERO
        row["result"] = row["revenue"] - row["expense"]
        row["revenue_share"] = row["revenue"] / totals["revenue"] * 100 if totals["revenue"] else None
        row["expense_share"] = row["expense"] / totals["expense"] * 100 if totals["expense"] else None
    return totals, rows
