"""Allocation rules from SPFINizv52/53, without their persistent UPDATE side effects.

The mutable posao_mes amounts can contain either cash flow or P&L. Reconstruct
the P&L pools from our reconciled ledger; read only the source allocation rules.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.core.cache import cache
from django.db import connections
from django.db.models.functions import ExtractMonth

from finansije.models import LedgerEntry
from .reports import expressions
from .source import SOURCE

ZERO = Decimal("0")
# Pravila raspodele (posao_mes, blokraspodela) menjaju se retko (mesečni koeficijenti), a povezani server je spor
# (merenje 07.10.2026.: 25–30 s po upitu sa spajanjem). Zato se čitaju za celu godinu jednim OPENQUERY upitom —
# spajanje radi udaljeni server — i pamte se sat vremena. Ključ uključuje firmu i godinu.
TRAJANJE_PRAVILA = 3600
LINKED_SERVER = "[PUTGEO-SERVER]"


def _openquery(upit):
    return f"SELECT * FROM OPENQUERY({LINKED_SERVER}, '{upit.replace(chr(39), chr(39) * 2)}')"


def pravila_godine(company, year):
    """(sva mesečna pravila godine, (sif_pos, koef1, koef2, koef3) za šifre sa centrom u raspodeli) — iz keša ili izvora."""
    company, year = int(company), int(year)  # samo celi brojevi ulaze u tekst upita
    kljuc = f"finansije:zt:pravila:{company}:{year}"
    podaci = cache.get(kljuc)
    if podaci is not None:
        return podaci
    with connections["server_db"].cursor() as cursor:
        cursor.execute(_openquery(
            "SELECT m.sif_pos, m.mesec, m.kriterijum, m.koef, m.koef2, m.koef3, m.profitni "
            "FROM bazaims.dbo.posao_mes m INNER JOIN bazaims.dbo.posao p ON p.sif_pred = m.sif_pred AND p.sif_pos = m.sif_pos "
            f"WHERE m.sif_pred = {company} AND m.god = '{year}' AND m.aktivan = 'D'"))
        pravila = [{"code": str(r[0]).strip(), "month": r[1], "criterion": str(r[2] or "").strip(),
                    "coefficients": tuple(r[i] or ZERO for i in (3, 4, 5)), "profit": str(r[6] or "").strip()}
                   for r in cursor.fetchall()]
        cursor.execute(_openquery(
            "SELECT p.sif_pos, b.koef1, b.koef2, b.koef3 FROM bazaims.dbo.posao p "
            "INNER JOIN bazaims.dbo.blokraspodela b ON b.sif_pred = p.sif_pred AND b.blok = p.blok "
            f"WHERE p.sif_pred = {company} AND b.god = '{year}'"))
        centri = [(str(r[0]).strip(), r[1], r[2], r[3]) for r in cursor.fetchall()]
    podaci = (pravila, centri)
    cache.set(kljuc, podaci, TRAJANJE_PRAVILA)
    return podaci


def allocation_rules(company, year, first_month, last_month, code):
    pravila, centri = pravila_godine(company, year)
    rules = [r for r in pravila if first_month <= r["month"] <= last_month]
    centers = [r for r in centri if code is None or r[0] == str(code).strip()]
    if code is None:
        grouped = {}
        for row in centers:
            grouped.setdefault(str(row[0]).strip(), []).append(tuple(v or ZERO for v in row[1:]))
        return rules, {key: values[0] if len(values) == 1 else None for key, values in grouped.items()}
    if len(centers) != 1:
        return rules, None
    return rules, tuple(v or ZERO for v in centers[0][1:])


def allocate(rules, center, balances, code, months):
    if center is None:
        return {"available": False, "note": "Nema jednoznačne raspodele za centar i godinu."}
    mapping = {}
    for rule in rules:
        key = (rule["code"], rule["month"])
        if key in mapping:
            return {"available": False, "note": "Postoje duplirani mesečni kriterijumi raspodele."}
        mapping[key] = rule
    own = [r for r in rules if r["code"] == code and r["profit"] == "P"]
    if not own:
        return {"available": False, "note": "Šifra nema aktivnu raspodelu za profitni posao u ovom periodu."}
    pools = [ZERO, ZERO, ZERO]
    for balance in balances:
        rule = mapping.get((balance["job_code"], balance["month"]))
        if rule and rule["criterion"] in ("1", "2", "3"):
            pools[int(rule["criterion"]) - 1] += (balance["revenue"] or ZERO) - (balance["expense"] or ZERO)
    # SPFINizv53: sums of active monthly job coefficients / number of months in the period.
    average = [sum((r["coefficients"][i] for r in own), ZERO) / months for i in range(3)]
    cost = -sum((pools[i] * center[i] * average[i] / Decimal("10000") for i in range(3)), ZERO)
    note = "Raspodela prema kriterijumima i koeficijentima 52/53, iz prihoda i rashoda izabranog perioda."
    coverage = len({r["month"] for r in own})
    if months > 1:
        note += f" Koeficijent posla je zbir mesečnih koeficijenata podeljen sa {months}."
    if coverage < months:
        note += f" Evidentirani aktivni koeficijenti: {coverage} od {months} meseci; raspodela je nepotpuna."
    return {"available": True, "cost": cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "note": note, "complete": coverage == months}


def shared_cost(company, code, start, end):
    rules, center = allocation_rules(company, start.year, start.month, end.month, code)
    # Pools are company-wide; expose only the authorized job's allocated cost.
    balances = (LedgerEntry.objects.filter(company=company, active=True, booking_date__range=(start, end))
                .order_by().annotate(month=ExtractMonth("booking_date")).values("job_code", "month")
                .annotate(**expressions()))
    return allocate(rules, center, balances, code, end.month - start.month + 1)


def shared_cost_many(company, codes, start, end):
    rules, centers = allocation_rules(company, start.year, start.month, end.month, None)
    balances = list(LedgerEntry.objects.filter(company=company, active=True, booking_date__range=(start, end))
                    .order_by().annotate(month=ExtractMonth("booking_date")).values("job_code", "month")
                    .annotate(**expressions()))
    return {code: allocate(rules, centers.get(code), balances, code, end.month - start.month + 1)
            for code in codes}
