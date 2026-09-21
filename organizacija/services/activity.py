"""Nalaz o obrtu: koji poslovi nemaju kretanja novca u posmatranom prozoru.

Obrt se meri po **datumu knjizenja** (`booking_date`), jer je to datum po kom modul
Finansija filtrira knjizenja. Broji se svako knjizenje sa iznosom razlicitim od nule na
bilo kojoj strani.

**Odluka narucioca 21.09.2026.: obrt je merodavan u oba smera.** Sifra koja ima podatke
je aktivna, ona koja ih nema je neaktivna — bez obzira na oznaku u izvoru. Ranije je
pravilo bilo jednosmerno (samo gasi); posto izvor drzi neaktivnim i sifre na kojima se
novac krece, ta oznaka se pokazala nepouzdanijom od samih knjizenja.

Gde se nalaz i izvor razilaze, to se **prijavljuje** (`disagreements`) — razlika ostaje
vidljiva umesto da se precuti.
"""

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from organizacija.models import (
    ExternalOrgMapping,
    JobActivityReview,
    OrgNode,
    OrgNodeVersion,
)

ZERO = Decimal("0.00")
DEFAULT_MONTHS = 12
NOTE_OFF = "Ugaseno lokalno: nema obrta u posmatranom prozoru."
NOTE_ON = "Aktivno lokalno: ima obrta u posmatranom prozoru."


def window(months=DEFAULT_MONTHS, today=None):
    """Prozor posmatranja, oba kraja ukljucivo."""
    end = today or timezone.localdate()
    return end - timedelta(days=int(round(months * 365 / 12))), end


def turnover_by_code(company, window_from, window_to):
    """Knjizenja sa iznosom razlicitim od nule, po sifri posla."""
    from finansije.models import LedgerEntry

    rows = (
        LedgerEntry.objects.filter(
            company=company, booking_date__gte=window_from, booking_date__lte=window_to
        )
        .exclude(job_code="")
        .exclude(Q(debit=0) & Q(credit=0))
        .values("job_code")
        .annotate(rows=Count("*"), debit=Sum("debit"), credit=Sum("credit"))
    )
    return {
        (row["job_code"] or "").strip(): {
            "rows": row["rows"],
            "debit": row["debit"] or ZERO,
            "credit": row["credit"] or ZERO,
        }
        for row in rows
    }


def measure(company=1, months=DEFAULT_MONTHS, today=None):
    """Meri obrt za svaki posao u stablu. Ne menja nista.

    Obrt se sabira po **svim siframa koje je posao ikada nosio**, da promena sifre ne
    bi izgledala kao prestanak rada.
    """
    window_from, window_to = window(months, today)
    turnover = turnover_by_code(company, window_from, window_to)

    current = {
        version.node_id: version
        for version in OrgNodeVersion.objects.filter(
            valid_to__isnull=True, node__level=OrgNode.LEVEL_JOB, node__company=company
        ).select_related("node")
    }
    all_codes = {}
    for version in OrgNodeVersion.objects.filter(
        node__level=OrgNode.LEVEL_JOB, node__company=company
    ):
        all_codes.setdefault(version.node_id, set()).add(version.full_code)

    source_active = _source_active(company)

    findings = []
    for node_id, version in current.items():
        totals = {"rows": 0, "debit": ZERO, "credit": ZERO}
        for code in all_codes.get(node_id, {version.full_code}):
            hit = turnover.get(code)
            if hit:
                totals["rows"] += hit["rows"]
                totals["debit"] += hit["debit"]
                totals["credit"] += hit["credit"]
        findings.append(
            {
                "node_id": node_id,
                "version": version,
                "code": version.full_code,
                "name": version.name,
                # Sta registar trenutno kaze i sta kaze izvor — namerno odvojeno, jer
                # posle prvog nalaza to vise nije ista stvar.
                "current_active": version.is_active,
                "source_active": source_active.get(node_id, version.is_active),
                "has_turnover": totals["rows"] > 0,
                **totals,
            }
        )
    findings.sort(key=lambda item: item["code"])
    return {"window_from": window_from, "window_to": window_to, "findings": findings}


def _source_active(company):
    """Aktivnost kakvu kaze izvorni sifarnik, po cvoru — kroz potvrdjeno mapiranje."""
    from finansije.models import FinanceJob

    by_code = {
        job.code.strip(): bool(job.active)
        for job in FinanceJob.objects.filter(company=company)
    }
    result = {}
    for mapping in ExternalOrgMapping.objects.filter(
        source=ExternalOrgMapping.SOURCE_FINANCE_JOB, company=company, valid_to__isnull=True
    ):
        if mapping.source_key in by_code:
            result[mapping.node_id] = by_code[mapping.source_key]
    return result


def summarize(result):
    findings = result["findings"]
    without = [item for item in findings if not item["has_turnover"]]
    with_turnover = [item for item in findings if item["has_turnover"]]
    return {
        "jobs": len(findings),
        "with_turnover": len(with_turnover),
        "without_turnover": len(without),
        # Sta se stvarno menja u registru pri sledecoj primeni.
        "to_deactivate": [item for item in without if item["current_active"]],
        "to_activate": [item for item in with_turnover if not item["current_active"]],
        "already_inactive": [item for item in without if not item["current_active"]],
        # Sve gde se nalaz i izvor razilaze, da razlika ostane vidljiva.
        "disagreements": [
            item for item in findings if item["has_turnover"] != item["source_active"]
        ],
    }


@transaction.atomic
def apply_reviews(company=1, months=DEFAULT_MONTHS, today=None):
    """Upisuje nalaze i, gde treba, zatvara verziju i pravi novu sa `is_active=False`.

    Vraca isti sazetak kao `summarize`, dopunjen brojem stvarno izmenjenih verzija.
    """
    result = measure(company, months, today)
    summary = summarize(result)
    effective_day = today or timezone.localdate()
    changed = 0

    for item in result["findings"]:
        JobActivityReview.objects.update_or_create(
            node_id=item["node_id"],
            defaults={
                "window_from": result["window_from"],
                "window_to": result["window_to"],
                "has_turnover": item["has_turnover"],
                "rows": item["rows"],
                "debit": item["debit"],
                "credit": item["credit"],
                "note": NOTE_ON if item["has_turnover"] else NOTE_OFF,
            },
        )
        version = item["version"]
        # Obrt odlucuje, ne oznaka iz izvora.
        should_be_active = item["has_turnover"]
        if version.is_active == should_be_active:
            continue
        changed += _close_and_reopen(version, should_be_active, effective_day)

    summary["window_from"] = result["window_from"]
    summary["window_to"] = result["window_to"]
    summary["versions_changed"] = changed
    return summary


def _close_and_reopen(version, is_active, day):
    """Zatvara tekucu verziju i otvara novu sa izmenjenom aktivnoscu.

    Ako bi nova verzija pocela istog dana kad i tekuca, tekuca se **ispravlja** umesto da
    se pravi verzija nultog trajanja — prazan interval nije istorija nego smece.
    """
    if version.valid_from >= day:
        version.is_active = is_active
        version.note = NOTE_ON if is_active else NOTE_OFF
        version.save(update_fields=["is_active", "note"])
        return 1

    version.valid_to = day
    version.save(update_fields=["valid_to"])
    OrgNodeVersion.objects.create(
        node=version.node,
        parent=version.parent,
        segment=version.segment,
        full_code=version.full_code,
        name=version.name,
        is_active=is_active,
        is_profit=version.is_profit,
        valid_from=day,
        note=NOTE_ON if is_active else NOTE_OFF,
    )
    return 1
