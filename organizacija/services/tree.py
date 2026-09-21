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


# Dozvoljene vrednosti filtera. Nepoznata vrednost se ignorise, ne ruši prikaz.
STATUS_CHOICES = ("aktivni", "neaktivni")
PROFIT_CHOICES = ("profitni", "neprofitni", "nepoznato")


def job_passes(job, status="", profit=""):
    """Da li posao prolazi filtere oznaka."""
    if status == "aktivni" and not job["is_active"]:
        return False
    if status == "neaktivni" and job["is_active"]:
        return False
    if profit == "profitni" and job["is_profit"] is not True:
        return False
    if profit == "neprofitni" and job["is_profit"] is not False:
        return False
    if profit == "nepoznato" and job["is_profit"] is not None:
        return False
    return True


def build_tree(company=1, query="", status="", profit=""):
    """Vraca listu centara sa jedinicama i poslovima.

    `query` filtrira po sifri ili nazivu na bilo kom nivou; grana se zadrzava ako
    sama odgovara ili ako joj neki potomak odgovara, da se pogodak vidi u kontekstu.

    `status` i `profit` filtriraju po oznakama posla. Kad je bilo koji filter ukljucen,
    prazne grane se **izbacuju** — inace bi ekran bio pun centara bez ijednog reda.
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
    status = status if status in STATUS_CHOICES else ""
    profit = profit if profit in PROFIT_CHOICES else ""
    flagged = bool(status or profit)
    filtering = bool(needle or flagged)

    tree = []
    for center in sorted(roots, key=lambda item: item.full_code):
        # Pogodak na centru zadrzava ceo njegov sadrzaj — inace bi pretraga po nazivu
        # centra vratila prazan centar umesto onoga sto se u njemu nalazi.
        center_hit = bool(needle) and _matches(center, needle)
        units = []
        for unit in sorted(children[center.node_id], key=lambda item: item.full_code):
            jobs = [_job(job, needle) for job in sorted(children[unit.node_id], key=lambda i: i.full_code)]
            if flagged:
                jobs = [job for job in jobs if job_passes(job, status, profit)]
            if needle and not center_hit:
                unit_hit = _matches(unit, needle)
                jobs = jobs if unit_hit else [job for job in jobs if job["match"]]
                if not unit_hit and not jobs:
                    continue
            if flagged and not jobs:
                continue
            units.append(_unit(unit, jobs))
        if filtering and not units:
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


# Redosled i nazivi filtera u prikazu. Svaki je veza, ne JavaScript — pa radi i sa
# otvaranjem u novoj kartici, i ostaje u istoriji pregledaca.
FILTER_BUTTONS = (
    ("status", "", "Svi"),
    ("status", "aktivni", "Samo aktivni"),
    ("status", "neaktivni", "Prikaži neaktivne"),
    ("profit", "profitni", "Profitni"),
    ("profit", "neprofitni", "Neprofitni"),
    ("profit", "nepoznato", "Oznaka nepoznata"),
)


def filter_links(query="", status="", profit=""):
    """Gradi spisak filtera sa upitnim delom adrese i oznakom da li je ukljucen.

    Klik na vec ukljucen filter ga **iskljucuje**, pa je svako dugme prekidac.
    """
    from urllib.parse import urlencode

    current = {"status": status, "profit": profit}
    links = []
    for field, value, label in FILTER_BUTTONS:
        active = current.get(field, "") == value
        params = dict(current)
        params[field] = "" if active and value else value
        if field == "status" and value == "":
            params = {"status": "", "profit": ""}
        if query:
            params["q"] = query
        query_string = urlencode({k: v for k, v in params.items() if v})
        links.append(
            {
                "label": label,
                "field": field,
                "value": value,
                "active": active if value else not (status or profit),
                "url": ("?" + query_string) if query_string else "?",
            }
        )
    return links
