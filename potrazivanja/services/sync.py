"""Full, serialized and atomic publication of the legacy collections contract."""
from collections import defaultdict
from contextlib import contextmanager
from copy import copy
from decimal import Decimal
import logging
from threading import Lock
import unicodedata

from django.db import connection, transaction, models
from django.db.models import Value
from django.db.models.functions import Cast
from django.utils import timezone

from finansije.services.sync import SyncBusy
from potrazivanja.models import (
    BalanceSnapshot, CollectionState, CollectionSyncRun, CollectionSyncStep,
    FinancePartnerIdentity, ReceivablePosting, ReceivablePosition, InvoiceDocument,
    DueDateEvidence, SourceDataset, SourceRow, ImportIssue,
)
from .source import day, digest, extract, fingerprint, integer, money, payload, text, FINANCIAL_SOURCES

logger = logging.getLogger(__name__)
_local_lock = Lock()


@contextmanager
def sync_lock():
    if connection.vendor == "sqlite":
        if not _local_lock.acquire(blocking=False):
            raise SyncBusy("Sinhronizacija Potraživanja je već pokrenuta.")
        try:
            yield
        finally:
            _local_lock.release()
        return
    if connection.vendor != "microsoft":
        raise RuntimeError("Sinhronizacija zahteva SQL Server.")
    with connection.cursor() as cursor:
        cursor.execute("DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'potrazivanja.full.sync', @LockMode='Exclusive', @LockOwner='Session', @LockTimeout=0; SELECT @r")
        while cursor.description is None:
            if not cursor.nextset():
                raise RuntimeError("Nema rezultata zaključavanja.")
        if cursor.fetchone()[0] < 0:
            raise SyncBusy("Sinhronizacija Potraživanja je već pokrenuta.")
    try:
        yield
    finally:
        try:
            with connection.cursor() as cursor:
                cursor.execute("EXEC sys.sp_releaseapplock @Resource=N'potrazivanja.full.sync', @LockOwner='Session'")
        except Exception:
            connection.close()
            logger.exception("Releasing collections sync lock failed")


def bulk_create(model, objects):
    # Explicit decimal casts avoid ODBC NULL/money type inference overflows.
    decimal_fields = [f for f in model._meta.fields if isinstance(f, models.DecimalField)]
    for offset in range(0, len(objects), 100):
        batch = objects[offset:offset + 100]
        if connection.vendor == "microsoft" and decimal_fields:
            batch = [copy(obj) for obj in batch]
            for obj in batch:
                for field in decimal_fields:
                    setattr(obj, field.name, Cast(Value(getattr(obj, field.name), output_field=field), output_field=field))
        model.objects.bulk_create(batch, batch_size=100)


def fold(value):
    # Legacy Latin1_General_CI_AI treats case/accents and trailing spaces equally.
    return "".join(c for c in unicodedata.normalize("NFKD", str(value or "").rstrip().casefold())
                   if not unicodedata.combining(c))


def bucket(due, as_of):
    if due is None or due >= as_of:
        return "0.1"  # Deliberately preserves legacy unknown-date bucket.
    days = (as_of - due).days
    for limit in (30, 45, 60, 90, 180):
        if days <= limit:
            return str(limit)
    return "181"


def source_key(row):
    return (integer(row["god"]), text(row["sif_vrs"]), integer(row["br_naloga"]), integer(row["stavka"]))


def issue(run, code, table, key, message, raw=None):
    return ImportIssue.objects.create(run=run, code=code, severity="warning", source_table=table,
                                     source_key=str(key), message=message, raw_data=payload(raw or {}))


def archive_sources(data, run, progress):
    for name, rows in data.items():
        signature = fingerprint(rows)
        dataset = SourceDataset.objects.filter(name=name, fingerprint=signature).first()
        reused = dataset is not None
        if not reused:
            dataset = SourceDataset.objects.create(name=name, fingerprint=signature, row_count=len(rows), first_run=run)
            records = []
            for i, row in enumerate(rows, 1):
                code = row.get("sif_par", row.get("sifra partnera", row.get("sifra_partnera")))
                records.append(SourceRow(dataset=dataset, ordinal=i, partner_code=integer(code),
                                         job_code=text(row.get("sif_pos")), raw_data=payload(row)))
            bulk_create(SourceRow, records)
            saved = list(dataset.rows.values_list("raw_data", flat=True))
            if len(saved) != len(rows) or fingerprint(saved) != signature:
                raise ValueError(f"Kontrola kompletnog sadržaja izvora {name} nije prošla.")
        CollectionSyncStep.objects.create(run=run, code=name, status="success", source_rows=len(rows),
                                           created_rows=0 if reused else len(rows), finished_at=timezone.now(),
                                           details={"dataset_id": dataset.pk, "fingerprint": signature, "reused": reused})
        progress(f"Sačuvan izvor {name}: {len(rows)} redova" + (" (postojeći identičan snimak)" if reused else ""))


def sync_partners(data, run):
    rows = [r for r in data["partneri"] if integer(r["sif_pred"]) == 1 and integer(r["grupa"]) == 1]
    existing = {i.partner_code: i for i in FinancePartnerIdentity.objects.filter(company=1, partner_group=1, source_system="baza_ims")}
    seen = set()
    create, change = [], []
    fields = ["source_name", "source_tax_id", "source_registration_number", "source_address", "source_city", "source_country", "source_hash", "active", "last_seen_run"]
    for row in rows:
        code = integer(row["sif_par"])
        if code is None or code in seen:
            raise ValueError("Neispravan/dupliran pun ključ partnera.")
        seen.add(code)
        values = dict(source_name=text(row.get("naz_par")), source_tax_id=text(row.get("pib")),
                      source_registration_number=text(row.get("mb")), source_address=text(row.get("ulica_par")),
                      source_city=text(row.get("mesto_par")), source_country=text(row.get("zemlja")),
                      source_hash=digest(row), active=True, last_seen_run=run)
        obj = existing.get(code)
        if obj is None:
            create.append(FinancePartnerIdentity(company=1, partner_group=1, partner_code=code, **values))
        elif obj.source_hash != values["source_hash"] or not obj.active:
            for name, value in values.items():
                setattr(obj, name, value)
            change.append(obj)
    bulk_create(FinancePartnerIdentity, create)
    if change:
        FinancePartnerIdentity.objects.bulk_update(change, fields, batch_size=40)
    # NOT IN avoids SQL Server's parameter limit by using last_seen_run in small batches.
    ids = [obj.pk for code, obj in existing.items() if code not in seen and obj.active]
    for offset in range(0, len(ids), 500):
        FinancePartnerIdentity.objects.filter(pk__in=ids[offset:offset+500]).update(active=False)
    FinancePartnerIdentity.objects.filter(company=1, partner_group=1, source_system="baza_ims", active=True).update(last_seen_run=run)
    result = {i.partner_code: i for i in FinancePartnerIdentity.objects.filter(company=1, partner_group=1, source_system="baza_ims")}
    # Financial facts may reference a deleted catalog entry. Preserve the confirmed
    # company/group from baza; do not guess the identity of orphan operational data.
    for name in ("baza", "ispravke", "dodela_baketa"):
        for row in data[name]:
            code = integer(row.get("sif_par"))
            if code is None:
                raise ValueError(f"{name}: finansijski red bez šifre partnera.")
            if code not in result:
                result[code] = FinancePartnerIdentity.objects.create(company=1, partner_group=1, partner_code=code,
                    source_name=text(row.get("naz_par")), active=False, last_seen_run=run)
                issue(run, "missing_partner", name, code, "Partner postoji u finansijskim podacima, ali nije u šifarniku.", row)
    return result


def _cvorovi_registra():
    """Sifra posla → cvor registra organizacije (samo citanje; prazno ako registar nije uvezen).

    Stavke i pozicije se upisuju masovno, pa se veza `org_node` postavlja ovde, zajedno sa
    `center_code` — signal pri cuvanju tu ne radi.
    """
    from organizacija.services.report import job_code_to_node

    return job_code_to_node(1)


def sync_postings(data, run, partners, centers):
    cvorovi = _cvorovi_registra()
    existing = {(p.year, p.journal_type, p.journal_number, p.line_number): p
                for p in ReceivablePosting.objects.filter(company=1, source_system="baza_ims")}
    seen, created, updated = set(), [], 0
    invoices = defaultdict(list)
    for table in ("baza", "ispravke"):
        for row in data[table]:
            key = source_key(row)
            if key in seen or None in key:
                raise ValueError(f"Dupliran/neispravan izvorni ključ knjiženja u {table}: {key}")
            seen.add(key)
            code = integer(row["sif_par"])
            job = text(row.get("sif_pos"))
            values = dict(year=key[0], journal_type=key[1], journal_number=key[2], line_number=key[3],
                company=1, partner_group=1, partner_code=code, identity_id=partners[code].pk,
                account=text(row["knt"]), account_name=text(row.get("naz_knt")),
                organizational_unit=text(row.get("oj")), job_code=job, center_code=centers.get(job, ""),
                reference=text(row.get("vez_dok")), document_date=day(row.get("datum")),
                booking_date=day(row.get("dat_naloga")), due_date=day(row.get("dpo")),
                debit=money(row["dug"]), credit=money(row["pot"]),
                change_status=text(row.get("promena")), description=text(row.get("kom")),
                source_hash=digest(row), active=True, removed_at=None, last_seen_run=run)
            if values["booking_date"] is None:
                raise ValueError(f"Knjiženje {key} nema datum knjiženja.")
            old = existing.get(key)
            cvor = cvorovi.get(job)
            if old is None:
                created.append(ReceivablePosting(**values, org_node_id=cvor))
            elif (old.source_hash != values["source_hash"] or not old.active or old.center_code != values["center_code"]
                  or old.org_node_id != cvor):
                # Changed rows only. Single-row UPDATE preserves Decimal binding.
                ReceivablePosting.objects.filter(pk=old.pk).update(**values, org_node_id=cvor)
                updated += 1
            if table == "baza" and key[1] == "IF":
                invoices[(key[0], key[2], code, values["reference"])].append(values)
    bulk_create(ReceivablePosting, created)
    removed = [p.pk for key, p in existing.items() if key not in seen and p.active]
    for offset in range(0, len(removed), 500):
        ReceivablePosting.objects.filter(pk__in=removed[offset:offset+500]).update(active=False, removed_at=timezone.now())
    ReceivablePosting.objects.filter(company=1, source_system="baza_ims", active=True).update(last_seen_run=run)
    CollectionSyncStep.objects.create(run=run, code="postings", status="success", source_rows=len(seen),
        created_rows=len(created), updated_rows=updated, inactive_rows=len(removed), finished_at=timezone.now(),
        details={"absence_means": "Van tekućeg obuhvata view-a; nije dokaz brisanja iz ERP-a."})
    # A real IF document is grouped by year/journal/partner/reference, on receivable
    # accounts only. v_if.saldo is deliberately NOT used as invoice amount.
    old_docs = {d.source_key: d for d in InvoiceDocument.objects.filter(company=1, source_system="baza_ims")}
    new_docs, doc_keys = [], set()
    for key, lines in invoices.items():
        source = digest(key)
        doc_keys.add(source)
        dues = [v["due_date"] for v in lines if v["due_date"]]
        dates = [v["document_date"] for v in lines if v["document_date"]]
        values = dict(company=1, identity_id=partners[key[2]].pk, year=key[0], number=str(key[1]),
            reference=key[3], document_date=min(dates) if dates else None,
            due_date=min(dues) if dues else None, amount_rsd=sum((v["debit"]-v["credit"] for v in lines), Decimal(0)),
            currency="RSD", source_hash=digest(lines_without_run(lines)), active=True, last_seen_run=run)
        old = old_docs.get(source)
        if old is None:
            new_docs.append(InvoiceDocument(source_key=source, **values))
        elif old.source_hash != values["source_hash"] or not old.active:
            InvoiceDocument.objects.filter(pk=old.pk).update(**values)
    bulk_create(InvoiceDocument, new_docs)
    for key, doc in old_docs.items():
        if key not in doc_keys and doc.active:
            InvoiceDocument.objects.filter(pk=doc.pk).update(active=False)
    InvoiceDocument.objects.filter(company=1, source_system="baza_ims", active=True).update(last_seen_run=run)


def lines_without_run(lines):
    return [{k: v for k, v in line.items() if k != "last_seen_run"} for line in lines]


def validate_postings(data):
    expected = {}
    for name in ("baza", "ispravke"):
        for r in data[name]:
            expected[source_key(r)] = (integer(r["sif_par"]), text(r["knt"]), text(r.get("sif_pos")),
                text(r.get("vez_dok")), day(r.get("dat_naloga")), day(r.get("dpo")), money(r["dug"]), money(r["pot"]))
    actual = {}
    for p in ReceivablePosting.objects.filter(company=1, source_system="baza_ims", active=True):
        actual[(p.year, p.journal_type, p.journal_number, p.line_number)] = (
            p.partner_code, p.account, p.job_code, p.reference, p.booking_date, p.due_date, p.debit, p.credit)
    differences = sum(expected.get(key) != actual.get(key) for key in set(expected) | set(actual))
    if differences:
        raise ValueError(f"Kontrola prenetih knjiženja: {differences} razlika.")
    return {"groups": len(expected), "differences": differences}


def position_key(code, reference, job, family):
    return (code, fold(reference), fold(job), family)


def compare_maps(expected, actual, label):
    keys = set(expected) | set(actual)
    differing = [key for key in keys if expected.get(key, Decimal(0)) != actual.get(key, Decimal(0))]
    if differing:
        raise ValueError(f"Kontrola {label}: {len(differing)} razlika. Snimak nije objavljen.")
    return {"groups": len(keys), "differences": 0}


def publish_positions(data, run, partners, centers, observed):
    cvorovi = _cvorovi_registra()
    snapshot = BalanceSnapshot.objects.create(run=run, company=1, as_of_date=observed.date(),
        source_observed_at=observed, rules_version="naplata-views-v1")
    base = defaultdict(Decimal)
    for row in data["baza"]:
        key = position_key(integer(row["sif_par"]), row.get("vez_dok"), row.get("sif_pos"), text(row["knt"])[:3])
        base[key] += money(row["dug"]) - money(row["pot"])
    expected, due_keys, amounts, positions, seen = {}, {}, {}, [], set()
    for row in data["dodela_baketa"]:
        code, job = integer(row["sif_par"]), text(row.get("sif_pos"))
        family = "204" if integer(row["ino"]) == 0 else "205"
        key = position_key(code, row.get("vez_dok"), job, family)
        if key in seen:
            raise ValueError("Više redova za isti ključ pozicije; potrebno razrešiti izvor, bez tihog spajanja.")
        seen.add(key)
        due = day(row.get("dpo"))
        if Decimal(bucket(due, observed.date())) != Decimal(str(row["baket"])):
            raise ValueError("Baket izvora ne odgovara datumu snimka.")
        debit, credit, balance = money(row["duguje"]), money(row["potrazuje"]), money(row["saldo"])
        if balance != debit-credit:
            raise ValueError("Saldo izvora nije jednak duguje - potražuje.")
        expected[key] = balance
        amounts[key] = (debit, credit)
        due_keys[key] = due
        positions.append(ReceivablePosition(snapshot=snapshot, identity_id=partners[code].pk,
            reference=text(row.get("vez_dok")), job_code=job, center_code=centers.get(job, ""),
            org_node_id=cvorovi.get(job), account_family=family,
            debit=debit, credit=credit, balance=balance, due_date=due, due_date_method="legacy_views",
            resolution_details={"source": "dodela_baketa", "bucket": bucket(due, observed.date()),
                "category": integer(row.get("kategorija")), "unknown_due": due is None}))
    controls = {"baza_to_positions": compare_maps(base, expected, "knjiženja → otvorene pozicije")}
    bulk_create(ReceivablePosition, positions)
    actual, source_groups, target_groups = {}, defaultdict(Decimal), defaultdict(Decimal)
    date_differences = 0
    for key, balance in expected.items():
        source_groups[(key[0], key[2], key[3], bucket(due_keys[key], observed.date()))] += balance
    code_by_id = {i.pk: code for code, i in partners.items()}
    rows = list(snapshot.positions.values("identity_id", "reference", "job_code", "account_family", "balance", "debit", "credit", "due_date"))
    for row in rows:
        key = position_key(code_by_id[row["identity_id"]], row["reference"], row["job_code"], row["account_family"])
        actual[key] = row["balance"]
        if (row["debit"], row["credit"]) != amounts.get(key):
            raise ValueError("Razlika duguje/potražuje nakon prenosa pozicija.")
        date_differences += row["due_date"] != due_keys.get(key)
        target_groups[(key[0], key[2], key[3], bucket(row["due_date"], observed.date()))] += row["balance"]
    controls["positions"] = compare_maps(expected, actual, "pozicije")
    controls["partner_job_buckets"] = compare_maps(source_groups, target_groups, "partner/posao/baket")
    if date_differences:
        raise ValueError("Razlika u datumima dospeća posle prenosa.")
    controls["due_dates"] = {"groups": len(rows), "differences": date_differences}
    controls["debit_credit"] = {"groups": len(rows), "differences": 0}
    controls["postings"] = validate_postings(data)
    controls["totals"] = {"positions": len(rows), "partners": len({r["identity_id"] for r in rows}),
        "balance": str(sum((r["balance"] for r in rows), Decimal(0))),
        "debit": str(sum((r["debit"] for r in rows), Decimal(0))),
        "credit": str(sum((r["credit"] for r in rows), Decimal(0))),
        "unknown_due_count": sum(r["due_date"] is None for r in rows)}
    snapshot.totals = controls
    snapshot.status = "published"
    snapshot.published_at = timezone.now()
    snapshot.save()
    CollectionState.objects.update_or_create(company=1, defaults={"current_snapshot": snapshot})
    return controls


def sync_collections(*, trigger="manual", requested_by=None, task_id="", progress=None, include_legacy=False):
    """Same plain function for the POST button, management command and Celery."""
    progress = progress or (lambda message: logger.info(message))
    run = CollectionSyncRun.objects.create(dataset="full", trigger=trigger, requested_by=requested_by,
        task_id=task_id, status="running", scope={"company": 1, "group": 1, "mode": "initial_import" if include_legacy else "financial_only"})
    try:
        with sync_lock():
            if include_legacy and CollectionState.objects.filter(company=1, operations_independent_at__isnull=False).exists():
                raise ValueError("Potraživanja već samostalno vode operativne podatke. Ponovni uvoz iz Naplate je isključen.")
            CollectionSyncRun.objects.filter(status="running").exclude(pk=run.pk).update(
                status="failed", finished_at=timezone.now(), error="Prethodno pokretanje prekinuto; nema aktivnog zaključavanja.")
            data, observed = extract(progress, include_legacy=include_legacy)
            if not include_legacy:
                data = {name: rows for name, rows in data.items() if name in FINANCIAL_SOURCES}
            if not data["partneri"] or not data["baza"]:
                raise ValueError("Prazan osnovni izvor; postojeći podaci ostaju objavljeni.")
            run.source_counts = {name: len(rows) for name, rows in data.items()}
            run.scope.update(baza_years=sorted({integer(r["god"]) for r in data["baza"]}),
                             ispravke_years=sorted({integer(r["god"]) for r in data["ispravke"]}))
            run.save(update_fields=["source_counts", "scope"])
            centers = {}
            for job in data["posao"]:
                code = text(job["sif_pos"])
                if not code or code in centers:
                    raise ValueError("Duplirana/prazna šifra posla u izvornom šifarniku.")
                centers[code] = text(job.get("blok"))
            with transaction.atomic():
                archive_sources(data, run, progress)
                partners = sync_partners(data, run)
                progress("Prenos knjiženja i faktura")
                sync_postings(data, run, partners, centers)
                if include_legacy:
                    from .operations import sync_operations
                    sync_operations(data, run, partners)
                progress("Poređenje salda, partnera, šifara posla, baketa i dospeća")
                run.control_totals = publish_positions(data, run, partners, centers, observed)
                run.status = "success"
                run.finished_at = timezone.now()
                run.save()
            progress(f"Sinhronizacija #{run.pk}: uspešna")
    except SyncBusy as exc:
        run.status = "skipped"
        run.error = str(exc)
        run.finished_at = timezone.now()
        run.save()
        raise
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)[:8000]
        run.finished_at = timezone.now()
        run.save()
        raise
    return run
