from decimal import Decimal

from django.conf import settings
from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import ExtractMonth, ExtractYear, Substr

from finansije.access import centar_sifre, centri_sifara, na_registru, polje_centra, uslov_centra, visible_scope
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
    if filters.get("center"):
        entries = entries.filter(uslov_centra(filters["center"]))
    if filters.get("job"):
        entries = entries.filter(job_code="" if filters["job"] == "__none__" else filters["job"])
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


def samo_aktivne_sifre(entries):
    """Izvestaj po siframa posla prikazuje samo aktivne sifre iz registra (odluka 25.09.2026.).

    Knjizenja neaktivnih sifara izostaju iz redova i iz zbira ispod tabele, pa se zbir i redovi
    slazu. Knjizenja bez sifre posla ostaju. Izvestaj po centrima, kontima i mesecima je ceo.
    """
    from fleet.support.registar import Registar

    registar = Registar()
    neaktivne = [code for code in entries.order_by().exclude(job_code="").values_list("job_code", flat=True).distinct()
                 if not registar.aktivna_sifra(code)]
    return entries.exclude(job_code__in=neaktivne) if neaktivne else entries


def grouped_report(entries, jobs, filters):
    group = filters["group"]
    if group == "job":
        entries = samo_aktivne_sifre(entries)
    centar = polje_centra()
    fields = {"center": [centar], "job": ["job_code", "job_name", centar], "account": ["account", "account_name"]}
    nivo = plan = None
    if group == "account":
        from .kontni_plan import nazivi_konta, nivo_konta

        nivo, plan = nivo_konta(filters), nazivi_konta()
    if group == "month":
        grouped = entries.annotate(report_year=ExtractYear("booking_date"), report_month=ExtractMonth("booking_date")).values("report_year", "report_month").annotate(**expressions()).order_by("report_year", "report_month")
    elif group == "account" and nivo != "5":
        # Otvaranje po dubini: klasa, grupa ili sintetika (prve 1, 2 ili 3 cifre konta).
        grouped = entries.annotate(konto=Substr("account", 1, int(nivo))).order_by().values("konto").annotate(**expressions()).order_by("konto")
    else:
        grouped = entries.order_by().values(*fields[group]).annotate(**expressions()).order_by(*fields[group])
    totals = summary(entries)
    rows = []
    if group == "center":
        from fleet.support.registar import Registar

        registar = Registar()
    for item in grouped:
        if group == "center":
            # Na registru je kljuc centar iz registra na datum knjizenja (`org_centar`), inace `center`.
            code, label = item[centar] or "", (registar.oznaka_centra(item[centar]) if item[centar] else "Neraspoređeno")
        elif group == "job":
            code, label = item["job_code"], item["job_name"] or "Bez naziva"
            item = dict(item, center=item[centar] or "")
        elif group == "account" and nivo != "5":
            code = item["konto"]
            label = plan.get(code) or "Bez naziva u kontnom planu"
        elif group == "account":
            code, label = item["account"], plan.get(item["account"]) or item["account_name"] or "Bez naziva konta"
        else:
            code = label = f"{item['report_year']}-{item['report_month']:02d}"
        rows.append(dict(item, code=code, label=label, nivo=nivo))
    if group == "job" and filters.get("include_empty"):
        present = {row["code"] for row in rows}
        mapa = centri_sifara() if na_registru() else None
        if filters.get("center"):
            trazeni = "" if filters["center"] == "__none__" else filters["center"]
            if mapa is None:
                jobs = jobs.filter(center=trazeni)
            elif trazeni:
                jobs = jobs.filter(code__in=[sifra for sifra, c in mapa.items() if c == trazeni])
            else:
                jobs = jobs.exclude(code__in=[sifra for sifra, c in mapa.items() if c])
        if filters.get("job"):
            jobs = jobs.filter(code="" if filters["job"] == "__none__" else filters["job"])
        # Units are posting attributes, not job attributes. Never invent a job→OJ mapping.
        if filters.get("unit"):
            jobs = jobs.filter(code__in=LedgerEntry.objects.filter(company=getattr(settings, "FINANSIJE_COMPANY", 1), active=True, organizational_unit=int(filters["unit"])).values("job_code"))
        from fleet.support.registar import Registar

        registar = Registar()
        rows.extend(dict(code=job.code, label=job.name or "Bez naziva", center=centar_sifre(job, mapa), revenue=ZERO, expense=ZERO, count=0)
                    for job in jobs if job.code not in present and registar.aktivna_sifra(job.code))
        rows.sort(key=lambda row: row["code"])
    for row in rows:
        row["revenue"] = row["revenue"] or ZERO
        row["expense"] = row["expense"] or ZERO
        row["result"] = row["revenue"] - row["expense"]
        row["revenue_share"] = row["revenue"] / totals["revenue"] * 100 if totals["revenue"] else None
        row["expense_share"] = row["expense"] / totals["expense"] * 100 if totals["expense"] else None
    return totals, rows
