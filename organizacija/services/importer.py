"""Uvoz sifarnika u centralni registar.

Faza 1. Uvoz **cita** `finansije.FinanceJob`, `finansije.LedgerEntry` i
`fleet.OrganizationalUnit`, a **pise iskljucivo** u tabele aplikacije `organizacija`.
Nijedan postojeci model se ne menja.

Uvoz je ponovljiv: cvor se pronalazi preko `ExternalOrgMapping`, pa ponovno pokretanje
nad nepromenjenim izvorom ne pravi ni cvorove ni verzije.
"""

from collections import defaultdict

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from organizacija.models import (
    ExternalOrgMapping,
    JobActivityReview,
    LegacyOrgLink,
    OrgImportRun,
    OrgNode,
    OrgNodeVersion,
    UnresolvedOrgCode,
)
from organizacija.services import classification as klas
from organizacija.services import pravilnik

DEFAULT_COMPANY = 1

# Naziv drugog nivoa se uzima samo iz pouzdanog izvora: Pravilnika o organizaciji (gde se
# poklapaju broj i sadrzaj), Kadrova (radnik u nauci) ili korena naucne sifre. Inace ostaje prazan.
UNIT_NAME_UNKNOWN = ""
UNIT_NOTE = "Naziv drugog nivoa nije potvrdjen; segment je treci znak sifre."


class MissingSourceData(RuntimeError):
    """Uvoz ne moze da pocne jer nedostaje izvor."""


def collect_known_units(company=DEFAULT_COMPANY):
    """Organizacione jedinice prvog nivoa i njihovi nazivi, iz knjizenja.

    Nazivi centara ne postoje ni u `FinanceJob` ni u `OrganizationalUnit`; jedini izvor
    je `LedgerEntry.organizational_unit_name`. Za svaku jedinicu uzima se naziv koji se
    javlja u najvise redova.
    """
    from finansije.models import LedgerEntry

    counts = defaultdict(lambda: defaultdict(int))
    rows = (
        LedgerEntry.objects.filter(company=company)
        .values("organizational_unit", "organizational_unit_name")
        .annotate(n=Count("*"))
    )
    for row in rows:
        unit = str(row["organizational_unit"]).strip()
        name = (row["organizational_unit_name"] or "").strip()
        if unit and name:
            counts[unit][name] += row["n"]

    return {unit: max(names.items(), key=lambda item: item[1])[0] for unit, names in counts.items()}


@transaction.atomic
def run_import(company=DEFAULT_COMPANY, known_units=None, valid_from=None, link_fleet_units=True):
    """Uvozi sifarnik i vraca `OrgImportRun`.

    `valid_from` je datum od kog vaze prve verzije. To je **migracioni snimak**, ne dokaz
    organizacije koja je vazila ranije — zato se i belezi u napomeni verzije.
    """
    if known_units is None:
        known_units = collect_known_units(company)
    if not known_units:
        raise MissingSourceData(
            "Nema nijedne organizacione jedinice u knjizenjima. Prvo pokreni sync_finansije, "
            "pa onda uvoz organizacije."
        )
    valid_from = valid_from or timezone.localdate()

    run = OrgImportRun.objects.create()
    report = []
    created_nodes = created_versions = unchanged = 0
    try:
        classified = _classify_source(company, known_units)
        needed = sorted({item[1].center for item in classified if item[1].center})
        skipped = sorted(set(known_units) - set(needed))
        if skipped:
            # Npr. `1 IMS` je cela ustanova, javlja se kao jedinica knjizenja ali nema
            # nijednu sifru posla. Cvor se ne pravi da se ne bi tvrdilo da je centar.
            report.append(
                "Jedinice iz knjizenja bez ijedne sifre posla, nisu unete u stablo: "
                + ", ".join(skipped)
            )

        centers, made = _ensure_centers(company, known_units, needed, valid_from)
        created_nodes += made["nodes"]
        created_versions += made["versions"]
        unchanged += made["unchanged"]
        report.append(f"Prvi nivo: {len(centers)} centara, novih {made['nodes']}.")

        units, jobs, made, unresolved = _import_jobs(
            company, classified, centers, valid_from, run
        )
        created_nodes += made["nodes"]
        created_versions += made["versions"]
        unchanged += made["unchanged"]
        report.append(f"Drugi nivo: {len(units)} jedinica, novih {made['units_created']}.")
        report.append(f"Treci nivo: {len(jobs)} poslova, novih {made['jobs_created']}.")
        report.append(f"Na listi za razresenje: {unresolved}.")

        if link_fleet_units:
            linked, missing = _link_fleet_units(company)
            report.append(
                f"Povezano sa fleet.OrganizationalUnit: {linked}; bez para u registru: {missing}."
            )

        from organizacija.services import putanja

        bilo, sada, promenjeno = putanja.izgradi(company)
        report.append(f"Putanje sifara do centra: {sada}" + (" (uskladjeno)." if promenjeno else ", bez promene."))

        run.source_rows = _source_row_count(company)
        run.nodes_created = created_nodes
        run.versions_created = created_versions
        run.unchanged = unchanged
        run.unresolved = unresolved
        run.status = OrgImportRun.STATUS_DONE
        run.finished_at = timezone.now()
        run.report = "\n".join(report)
        run.save()
    except Exception as exc:
        run.status = OrgImportRun.STATUS_FAILED
        run.finished_at = timezone.now()
        run.report = "\n".join(report + [f"PREKINUTO: {exc}"])
        run.save()
        raise
    return run


def _source_row_count(company):
    from finansije.models import FinanceJob

    return FinanceJob.objects.filter(company=company).count()


def _classify_source(company, known_units):
    """Razvrstava ceo sifarnik pre ijednog upisa, da se zna koji centri su potrebni."""
    from finansije.models import FinanceJob

    units = set(known_units)
    rows = list(FinanceJob.objects.filter(company=company).order_by("code"))
    return [(row, klas.classify(row.code, units, name=row.name)) for row in rows]


def _ensure_centers(company, known_units, needed, valid_from):
    """Prvi nivo. Kljuc mapiranja je jedinica knjizenja; oznaka centra je `oznaka_centra`
    (jedinice `20` i `30` su centri `2` i `3`)."""
    made = {"nodes": 0, "versions": 0, "unchanged": 0}
    centers = {}
    for unit in sorted(needed):
        node, created = _get_or_create_node(
            company=company,
            level=OrgNode.LEVEL_CENTER,
            source=ExternalOrgMapping.SOURCE_LEDGER_UNIT,
            source_key=unit,
            raw_value=unit,
            valid_from=valid_from,
        )
        centers[unit] = node
        if created:
            made["nodes"] += 1
        version_made = _ensure_version(
            node=node,
            parent=None,
            segment=klas.oznaka_centra(unit),
            full_code=klas.oznaka_centra(unit),
            name=pravilnik.naziv_centra(klas.oznaka_centra(unit)) or known_units[unit],
            is_active=True,
            is_profit=None,
            valid_from=valid_from,
            note=_napomena_centra(klas.oznaka_centra(unit)),
            ispravka_naziva=True,
        )
        made["versions" if version_made else "unchanged"] += 1
    return centers, made


def _import_jobs(company, classified, centers, valid_from, run):
    made = {"nodes": 0, "versions": 0, "unchanged": 0, "units_created": 0, "jobs_created": 0}
    units = {}
    jobs = {}
    unresolved = 0
    # Lokalni nalazi o obrtu. Gde nalaz postoji, **on odlucuje o aktivnosti**, a ne
    # oznaka iz izvora. Inace bi se dve strane smenjivale iz uvoza u uvoz i istorija bi
    # se punila verzijama bez stvarne promene.
    reviewed = dict(
        JobActivityReview.objects.values_list("node_id", "has_turnover")
    )

    for row, result in classified:
        raw = row.code or ""
        code = klas.normalize_code(raw)

        if not result.in_tree:
            UnresolvedOrgCode.objects.create(
                run=run,
                company=company,
                code=code,
                raw_code=raw,
                name=(row.name or "").strip(),
                source_center=(row.center or "").strip(),
                family=result.family,
                reason=result.reason,
                is_active=row.active,
            )
            unresolved += 1
            continue

        center_code, unit_digit, _job_segment = result.segments
        center_node = centers.get(center_code)
        if center_node is None:
            UnresolvedOrgCode.objects.create(
                run=run,
                company=company,
                code=code,
                raw_code=raw,
                name=(row.name or "").strip(),
                source_center=(row.center or "").strip(),
                family=klas.FAMILY_EXCEPTION,
                reason=klas.REASON_UNKNOWN_CENTER,
                is_active=row.active,
            )
            unresolved += 1
            continue

        unit_code = result.unit_code
        if unit_code not in units:
            unit_node, created = _get_or_create_node(
                company=company,
                level=OrgNode.LEVEL_UNIT,
                source=ExternalOrgMapping.SOURCE_DERIVED,
                source_key=f"jedinica:{unit_code}",
                raw_value=unit_code,
                valid_from=valid_from,
            )
            units[unit_code] = unit_node
            if created:
                made["nodes"] += 1
                made["units_created"] += 1
            unit_name, unit_note = _naziv_jedinice(unit_code, result)
            version_made = _ensure_version(
                node=unit_node,
                parent=center_node,
                segment=unit_digit,
                full_code=unit_code,
                name=unit_name,
                is_active=True,
                is_profit=None,
                valid_from=valid_from,
                note=unit_note,
                ispravka_naziva=True,
            )
            made["versions" if version_made else "unchanged"] += 1

        job_node, created = _get_or_create_node(
            company=company,
            level=OrgNode.LEVEL_JOB,
            source=ExternalOrgMapping.SOURCE_FINANCE_JOB,
            source_key=code,
            raw_value=raw,
            valid_from=valid_from,
        )
        jobs[code] = job_node
        if created:
            made["nodes"] += 1
            made["jobs_created"] += 1
        turnover = reviewed.get(job_node.pk)
        if turnover is None:
            is_active = bool(row.active)
            note = "Migracioni snimak; ranija istorija nije poznata."
        else:
            is_active = turnover
            note = (
                "Aktivno lokalno: ima obrta u posmatranom prozoru."
                if turnover
                else "Ugaseno lokalno: nema obrta u posmatranom prozoru."
            )
        version_made = _ensure_version(
            node=job_node,
            parent=units[unit_code],
            segment=result.job,
            full_code=code,
            name=(row.name or "").strip(),
            is_active=is_active,
            is_profit=_profit_flag(row.profit_type),
            valid_from=valid_from,
            note=note,
        )
        made["versions" if version_made else "unchanged"] += 1
        _ensure_legacy_link(LegacyOrgLink.LEGACY_FINANCE_JOB, row.pk, job_node)

    return units, jobs, made, unresolved


def _napomena_centra(oznaka):
    if pravilnik.naziv_centra(oznaka):
        clan = pravilnik.CENTRI[oznaka][2]
        return f"Naziv: {pravilnik.IZVOR} ({clan})." if clan != "šifarnik" else "Naziv iz sifarnika."
    return "Naziv iz knjizenja (organizational_unit_name)."


def _naziv_jedinice(unit_code, result):
    """Naziv jedinice drugog nivoa i napomena o izvoru; prazno kad pouzdanog izvora nema."""
    if result.family == klas.FAMILY_SCIENCE:
        if unit_code.startswith(klas.PREFIKS_PROJEKTA):
            return UNIT_NAME_UNKNOWN, (f"Naucni projekat {result.segments[1]}; broj projekta je slobodan unos, "
                                       "naziv nije potvrdjen.")
        return UNIT_NAME_UNKNOWN, f"Zbirni nosilac {result.segments[1]} — institutske teme."
    naziv = pravilnik.naziv_jedinice(unit_code)
    if naziv:
        return naziv, f"Naziv: {pravilnik.IZVOR}, {pravilnik.JEDINICE[unit_code][0]}."
    return UNIT_NAME_UNKNOWN, UNIT_NOTE


def _profit_flag(profit_type):
    """`P` profitni, `N` neprofitni, sve ostalo ostaje nepoznato — ne pretvara se u N."""
    value = (profit_type or "").strip().upper()
    if value == "P":
        return True
    if value == "N":
        return False
    return None


def _link_fleet_units(company):
    """Povezuje `fleet.OrganizationalUnit` sa cvorom po sifri, gde par postoji."""
    from core.models import OrganizationalUnit

    linked = missing = 0
    by_code = {
        mapping.source_key: mapping.node_id
        for mapping in ExternalOrgMapping.objects.filter(
            source=ExternalOrgMapping.SOURCE_FINANCE_JOB, company=company, valid_to__isnull=True
        )
    }
    for unit in OrganizationalUnit.objects.all():
        code = klas.normalize_code(unit.code)
        node_id = by_code.get(code)
        if node_id is None:
            missing += 1
            continue
        _, created = LegacyOrgLink.objects.get_or_create(
            legacy_label=LegacyOrgLink.LEGACY_FLEET_UNIT,
            legacy_id=unit.pk,
            defaults={"node_id": node_id},
        )
        linked += 1 if created else 0
    return linked, missing


def _get_or_create_node(company, level, source, source_key, raw_value, valid_from):
    """Cvor se nalazi preko mapiranja; identitet se nikad ne izvodi iz sifre."""
    mapping = ExternalOrgMapping.objects.filter(
        source=source, company=company, source_key=source_key, valid_to__isnull=True
    ).first()
    if mapping is not None:
        return mapping.node, False

    node = OrgNode.objects.create(company=company, level=level)
    ExternalOrgMapping.objects.create(
        source=source,
        company=company,
        source_key=source_key,
        raw_value=raw_value,
        node=node,
        valid_from=valid_from,
    )
    return node, True


def _ensure_version(node, parent, segment, full_code, name, is_active, is_profit, valid_from, note,
                    ispravka_naziva=False):
    """Pravi novu verziju samo ako se nesto stvarno promenilo.

    Vraca True ako je verzija napravljena. Postojeca otvorena verzija se **ne prepravlja**:
    zatvara se danom promene i pravi se nova, pa istorija ostaje citljiva.

    `ispravka_naziva`: naziv iz pouzdanog izvora (pravilnik, Kadrovi) zamenjuje nepoznat ili
    priblizan naziv migracionog snimka. Kad se razlikuje **samo** naziv, to nije promena
    organizacije nego ispravka, pa se verzija ispravlja na mestu, bez lazne istorije.
    """
    current = node.versions.filter(valid_to__isnull=True).order_by("-valid_from").first()
    fields = (parent.pk if parent else None, segment, full_code, name, is_active, is_profit)
    if current is not None:
        existing = (
            current.parent_id,
            current.segment,
            current.full_code,
            current.name,
            current.is_active,
            current.is_profit,
        )
        if existing == fields:
            if ispravka_naziva and current.note != note:
                current.note = note
                current.save(update_fields=["note"])
            return False
        if ispravka_naziva and existing[:3] + existing[4:] == fields[:3] + fields[4:]:
            current.name = name
            current.note = note
            current.save(update_fields=["name", "note"])
            return False
        if current.valid_from >= valid_from:
            # Ista granica vazenja: ispravka jos neobjavljenog snimka, bez lazne istorije.
            current.parent = parent
            current.segment = segment
            current.full_code = full_code
            current.name = name
            current.is_active = is_active
            current.is_profit = is_profit
            current.save()
            return False
        current.valid_to = valid_from
        current.save(update_fields=["valid_to"])

    OrgNodeVersion.objects.create(
        node=node,
        parent=parent,
        segment=segment,
        full_code=full_code,
        name=name,
        is_active=is_active,
        is_profit=is_profit,
        valid_from=valid_from,
        note=note,
    )
    return True


def _ensure_legacy_link(label, legacy_id, node):
    LegacyOrgLink.objects.get_or_create(
        legacy_label=label, legacy_id=legacy_id, defaults={"node": node}
    )
