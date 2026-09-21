"""Kontrolni izvestaj registra.

Uvoz bez ovoga nema dokaz. Provere su one iz plana
(`dokumentacija/plan-registra-sifara-posla.md`, odeljak 2.5); svaka vraca broj, ne ocenu.

Najvaznija je poslednja: nijedno knjizenje ne sme **nestati** pri prelasku na registar.
Zato se ne poredi samo zbir po centru nego i koliko redova i koliko novca **ne moze** da
se razresi — taj iznos ostaje vidljiv umesto da se precuti.
"""

from collections import defaultdict
from decimal import Decimal

from django.db.models import Count, Sum

from organizacija.models import ExternalOrgMapping, OrgNode, OrgNodeVersion, UnresolvedOrgCode

ZERO = Decimal("0.00")


def node_center_map(company=1):
    """Za svaki cvor treceg nivoa vraca oznaku njegovog centra, preko vazecih verzija."""
    versions = {
        version.node_id: version
        for version in OrgNodeVersion.objects.filter(valid_to__isnull=True).select_related("node")
        if version.node.company == company
    }
    centers = {}
    for node_id, version in versions.items():
        if version.node.level != OrgNode.LEVEL_JOB:
            continue
        unit = versions.get(version.parent_id)
        if unit is None:
            continue
        center = versions.get(unit.parent_id)
        if center is None:
            continue
        centers[node_id] = center.full_code
    return centers


def job_code_to_node(company=1):
    """Sifra posla → cvor, preko vazecih mapiranja iz `FinanceJob`."""
    return {
        mapping.source_key: mapping.node_id
        for mapping in ExternalOrgMapping.objects.filter(
            source=ExternalOrgMapping.SOURCE_FINANCE_JOB,
            company=company,
            valid_to__isnull=True,
        )
    }


def structural_checks(company=1):
    """Provere koje ne zavise od knjizenja."""
    open_versions = list(
        OrgNodeVersion.objects.filter(valid_to__isnull=True, node__company=company).select_related(
            "node"
        )
    )
    by_level = defaultdict(list)
    for version in open_versions:
        by_level[version.node.level].append(version)

    codes = defaultdict(int)
    for version in open_versions:
        codes[version.full_code] += 1
    duplicates = sorted(code for code, count in codes.items() if count > 1)

    orphans = []
    node_ids = {version.node_id for version in open_versions}
    for version in open_versions:
        if version.node.level == OrgNode.LEVEL_CENTER:
            if version.parent_id is not None:
                orphans.append(version.full_code)
        elif version.parent_id is None or version.parent_id not in node_ids:
            orphans.append(version.full_code)

    nameless = sorted(
        version.full_code
        for version in by_level[OrgNode.LEVEL_JOB]
        if not (version.name or "").strip()
    )

    return {
        "centers": len(by_level[OrgNode.LEVEL_CENTER]),
        "units": len(by_level[OrgNode.LEVEL_UNIT]),
        "jobs": len(by_level[OrgNode.LEVEL_JOB]),
        "duplicate_codes": duplicates,
        "orphans": sorted(orphans),
        "jobs_without_name": nameless,
    }


def ledger_reconciliation(company=1):
    """Poredi knjizenja preko registra sa ukupnim zbirom iz izvora.

    Vraca i **sta se ne moze razresiti**, po sifri, sa iznosom. Prazno je ovde jedini
    prihvatljiv rezultat za porodicu A; sve ostalo mora imati obrazlozenje.
    """
    from finansije.models import LedgerEntry

    mapping = job_code_to_node(company)
    centers = node_center_map(company)

    rows = (
        LedgerEntry.objects.filter(company=company)
        .values("job_code")
        .annotate(n=Count("*"), debit=Sum("debit"), credit=Sum("credit"))
    )

    total_rows = resolved_rows = 0
    total_debit = total_credit = ZERO
    resolved_debit = resolved_credit = ZERO
    per_center = defaultdict(lambda: {"rows": 0, "debit": ZERO, "credit": ZERO})
    unresolved = []

    for row in rows:
        code = (row["job_code"] or "").strip()
        count = row["n"]
        debit = row["debit"] or ZERO
        credit = row["credit"] or ZERO
        total_rows += count
        total_debit += debit
        total_credit += credit

        node_id = mapping.get(code)
        center = centers.get(node_id) if node_id else None
        if center is None:
            unresolved.append(
                {"job_code": code, "rows": count, "debit": debit, "credit": credit}
            )
            continue
        resolved_rows += count
        resolved_debit += debit
        resolved_credit += credit
        bucket = per_center[center]
        bucket["rows"] += count
        bucket["debit"] += debit
        bucket["credit"] += credit

    unresolved.sort(key=lambda item: -item["rows"])
    return {
        "total_rows": total_rows,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "resolved_rows": resolved_rows,
        "resolved_debit": resolved_debit,
        "resolved_credit": resolved_credit,
        "unresolved_rows": total_rows - resolved_rows,
        "unresolved_debit": total_debit - resolved_debit,
        "unresolved_credit": total_credit - resolved_credit,
        "per_center": dict(per_center),
        "unresolved": unresolved,
    }


def unresolved_summary(run=None):
    """Sazetak liste za razresenje, po porodici."""
    queryset = UnresolvedOrgCode.objects.all()
    if run is not None:
        queryset = queryset.filter(run=run)
    return {
        row["family"]: row["n"]
        for row in queryset.values("family").annotate(n=Count("*")).order_by("family")
    }


def build_report(company=1, run=None):
    return {
        "structure": structural_checks(company),
        "ledger": ledger_reconciliation(company),
        "unresolved": unresolved_summary(run),
    }
