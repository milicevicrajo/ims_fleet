"""Kartica jednog cvora: podaci, putanja, istorija i povezivanja.

Putanja se sklapa iz `parent` veza, nikad iz secenja sifre. Istorija prikazuje **sve**
verzije, sa periodom vazenja, i uz svaku sta se u odnosu na prethodnu promenilo — jer
je ceo smisao registra da promena naziva ili sifre ne izgubi identitet posla.
"""

from organizacija.models import (
    ExternalOrgMapping,
    JobActivityReview,
    LegacyOrgLink,
    OrgNode,
    OrgNodeVersion,
)

LEVEL_LABELS = {
    OrgNode.LEVEL_CENTER: "centar",
    OrgNode.LEVEL_UNIT: "organizaciona jedinica",
    OrgNode.LEVEL_JOB: "sifra posla",
}

# Sta se poredi izmedju dve verzije i kako se to zove u prikazu.
TRACKED_FIELDS = (
    ("full_code", "šifra"),
    ("name", "naziv"),
    ("parent_id", "nadređeni čvor"),
    ("is_active", "aktivnost"),
    ("is_profit", "profitnost"),
)


def node_detail(node_id):
    """Vraca sve za prikaz kartice ili None ako cvor ne postoji."""
    node = OrgNode.objects.filter(pk=node_id).first()
    if node is None:
        return None
    current = node.current_version
    return {
        "node": node,
        "level_label": LEVEL_LABELS.get(node.level, str(node.level)),
        "current": current,
        "path": build_path(current),
        "children": children_of(node),
        "history": history_of(node),
        "mappings": list(
            ExternalOrgMapping.objects.filter(node=node).order_by("source", "source_key")
        ),
        "legacy_links": list(
            LegacyOrgLink.objects.filter(node=node).order_by("legacy_label", "legacy_id")
        ),
        "codes": sorted(
            {version.full_code for version in node.versions.all()}
        ),
        "review": JobActivityReview.objects.filter(node=node).first(),
        "source_active": _source_active(node),
    }


def _source_active(node):
    """Aktivnost kakvu kaze izvorni sifarnik; None ako veza ne postoji.

    Drzi se odvojeno od `is_active` u registru jer se posle nalaza o obrtu to dvoje
    moze razilaziti — i to razilazenje je podatak, ne greska.
    """
    if node.level != OrgNode.LEVEL_JOB:
        return None
    from finansije.models import FinanceJob

    keys = list(
        ExternalOrgMapping.objects.filter(
            node=node, source=ExternalOrgMapping.SOURCE_FINANCE_JOB, valid_to__isnull=True
        ).values_list("source_key", flat=True)
    )
    if not keys:
        return None
    job = FinanceJob.objects.filter(company=node.company, code__in=keys).first()
    return bool(job.active) if job else None


def build_path(version):
    """Putanja od korena do cvora, kao lista verzija. Prazna ako cvor nema verziju."""
    if version is None:
        return []
    chain = [version]
    seen = {version.node_id}
    parent_id = version.parent_id
    while parent_id is not None and parent_id not in seen:
        seen.add(parent_id)
        parent = OrgNode.objects.filter(pk=parent_id).first()
        if parent is None:
            break
        parent_version = parent.current_version
        if parent_version is None:
            break
        chain.append(parent_version)
        parent_id = parent_version.parent_id
    return list(reversed(chain))


def children_of(node):
    """Deca po vazecim verzijama, sortirana po punoj sifri."""
    return list(
        OrgNodeVersion.objects.filter(parent=node, valid_to__isnull=True)
        .select_related("node")
        .order_by("full_code")
    )


def history_of(node):
    """Sve verzije, najstarija prva, uz spisak onoga sto se promenilo."""
    versions = list(node.versions.select_related("parent").order_by("valid_from", "pk"))
    rows = []
    previous = None
    for version in versions:
        rows.append(
            {
                "version": version,
                "is_current": version.valid_to is None,
                "changes": _changes(previous, version),
                "parent_code": _parent_code(version),
            }
        )
        previous = version
    return rows


def _changes(previous, version):
    if previous is None:
        return ["prvi upis"]
    changed = []
    for field, label in TRACKED_FIELDS:
        if getattr(previous, field) != getattr(version, field):
            changed.append(label)
    return changed or ["bez promene praćenih polja"]


def _parent_code(version):
    """Sifra roditelja kakva je bila kad je ova verzija pocela da vazi."""
    if version.parent_id is None:
        return ""
    parent_version = version.parent.version_on(version.valid_from)
    if parent_version is None:
        parent_version = version.parent.current_version
    return parent_version.full_code if parent_version else ""


def ledger_usage(detail, company=1):
    """Koliko knjizenja koristi bilo koju sifru ovog cvora.

    Broji se po **svim** siframa koje je cvor ikada nosio, ne samo po tekucoj — inace bi
    promena sifre izgledala kao da je posao nestao. Vraca None za cvorove koji nisu
    treci nivo, jer se knjizenja vezuju za sifru posla.
    """
    from django.db.models import Count, Sum

    if detail["node"].level != OrgNode.LEVEL_JOB or not detail["codes"]:
        return None
    from finansije.models import LedgerEntry

    row = LedgerEntry.objects.filter(company=company, job_code__in=detail["codes"]).aggregate(
        rows=Count("*"), debit=Sum("debit"), credit=Sum("credit")
    )
    return {
        "rows": row["rows"] or 0,
        "debit": row["debit"],
        "credit": row["credit"],
        "codes": detail["codes"],
    }
