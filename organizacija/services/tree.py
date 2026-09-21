"""Stablo za prikaz: centar → jedinica → posao.

Cita **samo vazece verzije** (`valid_to IS NULL`) i slaze ih u ugnjezdenu strukturu.
Pripadnost se uzima iz `parent` veze u verziji, nikad iz secenja sifre — zato ovde i
nema nijednog rada sa prefiksima.
"""

from collections import defaultdict

from organizacija.models import OrgNode, OrgNodeVersion, UnresolvedOrgCode


def current_versions(company=1):
    return (
        OrgNodeVersion.objects.filter(valid_to__isnull=True, node__company=company)
        .select_related("node")
        .order_by("full_code")
    )


def build_tree(company=1, query=""):
    """Vraca listu centara sa jedinicama i poslovima.

    `query` filtrira po sifri ili nazivu na bilo kom nivou; grana se zadrzava ako
    sama odgovara ili ako joj neki potomak odgovara, da se pogodak vidi u kontekstu.
    """
    versions = list(current_versions(company))
    by_node = {version.node_id: version for version in versions}

    children = defaultdict(list)
    roots = []
    for version in versions:
        if version.node.level == OrgNode.LEVEL_CENTER:
            roots.append(version)
        elif version.parent_id in by_node:
            children[version.parent_id].append(version)

    needle = (query or "").strip().lower()
    tree = []
    for center in sorted(roots, key=lambda item: item.full_code):
        units = []
        for unit in sorted(children[center.node_id], key=lambda item: item.full_code):
            jobs = sorted(children[unit.node_id], key=lambda item: item.full_code)
            jobs = [_job(job, needle) for job in jobs]
            if needle:
                hit_unit = _matches(unit, needle)
                jobs_kept = jobs if hit_unit else [job for job in jobs if job["match"]]
                if not hit_unit and not jobs_kept:
                    continue
                jobs = jobs_kept
            units.append(_unit(unit, jobs))
        if needle and not _matches(center, needle) and not units:
            continue
        tree.append(_center(center, units))
    return tree


def _matches(version, needle):
    return needle in version.full_code.lower() or needle in (version.name or "").lower()


def _job(version, needle=""):
    return {
        "code": version.full_code,
        "segment": version.segment,
        "name": version.name,
        "is_active": version.is_active,
        "is_profit": version.is_profit,
        "node_id": version.node_id,
        "match": bool(needle) and _matches(version, needle),
    }


def _unit(version, jobs):
    return {
        "code": version.full_code,
        "segment": version.segment,
        "name": version.name,
        "node_id": version.node_id,
        "jobs": jobs,
        "job_count": len(jobs),
        "active_jobs": sum(1 for job in jobs if job["is_active"]),
    }


def _center(version, units):
    jobs = sum(unit["job_count"] for unit in units)
    return {
        "code": version.full_code,
        "name": version.name,
        "node_id": version.node_id,
        "units": units,
        "unit_count": len(units),
        "job_count": jobs,
        "active_jobs": sum(unit["active_jobs"] for unit in units),
    }


def totals(tree):
    return {
        "centers": len(tree),
        "units": sum(center["unit_count"] for center in tree),
        "jobs": sum(center["job_count"] for center in tree),
        "active_jobs": sum(center["active_jobs"] for center in tree),
    }


def unresolved_groups(run=None):
    """Nerazresene sifre iz poslednjeg uvoza, grupisane po porodici."""
    queryset = UnresolvedOrgCode.objects.all()
    if run is not None:
        queryset = queryset.filter(run=run)
    groups = defaultdict(list)
    for row in queryset.order_by("family", "code"):
        groups[row.family].append(row)
    labels = dict(UnresolvedOrgCode.FAMILY_CHOICES)
    return [
        {"family": family, "label": labels.get(family, family), "rows": rows, "count": len(rows)}
        for family, rows in sorted(groups.items())
    ]
