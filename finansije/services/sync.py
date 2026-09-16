from contextlib import contextmanager
from copy import copy
from datetime import date
from decimal import Decimal
from threading import Lock

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Count, Sum, Value
from django.db.models.functions import Cast
from django.utils import timezone

from finansije.models import FinanceJob, LedgerEntry, SyncRun
from .source import KEY_FIELDS, fetch_source, fingerprint, source_key, totals_for


_local_lock = Lock()


class SyncBusy(Exception):
    pass


@contextmanager
def sync_lock():
    # Session-owned SQL Server lock covers extraction AND publishing; it is released
    # automatically if the worker dies. Never proceed unlocked after an error.
    if connection.vendor == "microsoft":
        with connection.cursor() as cursor:
            cursor.execute("""DECLARE @result int;
                EXEC @result = sys.sp_getapplock @Resource=N'finansije.ledger.sync',
                    @LockMode='Exclusive', @LockOwner='Session', @LockTimeout=0;
                SELECT @result;""")
            while cursor.description is None:
                if not cursor.nextset():
                    raise SyncBusy("Nije moguće proveriti zaključavanje sinhronizacije.")
            if cursor.fetchone()[0] < 0:
                raise SyncBusy("Sinhronizacija je već pokrenuta.")
        try:
            yield
        finally:
            with connection.cursor() as cursor:
                cursor.execute("EXEC sys.sp_releaseapplock @Resource=N'finansije.ledger.sync', @LockOwner='Session'")
    elif connection.vendor == "sqlite":
        # SQLite is used only by isolated tests/local development.
        if not _local_lock.acquire(blocking=False):
            raise SyncBusy("Sinhronizacija je već pokrenuta.")
        try:
            yield
        finally:
            _local_lock.release()
    else:
        raise RuntimeError("Sinhronizacija zahteva SQL Server.")


def chunks(items, size=30):
    for offset in range(0, len(items), size):
        yield items[offset:offset + size]


def prepare_amounts(entries):
    # Django 5 serializes Decimal as text. In a SQL Server VALUES/CASE expression,
    # an ODBC-bound NULL can force a narrow numeric type on the whole column,
    # overflowing valid amounts in adjacent rows. Explicit casts preserve 18,2
    # for BOTH non-null and null values, without converting money through float.
    if connection.vendor == "microsoft":
        entries = [copy(entry) for entry in entries]
        for entry in entries:
            for name in ("debit", "credit", "foreign_amount", "source_paid_amount"):
                field = LedgerEntry._meta.get_field(name)
                setattr(entry, name, Cast(Value(getattr(entry, name), output_field=field), output_field=field))
    return entries


def validate_payload(rows, jobs, company, year_from, year_to):
    keys = set()
    for row in rows:
        key = source_key(row)
        if key in keys:
            raise ValueError("Dupliran izvorni ključ knjiženja.")
        keys.add(key)
        if row["company"] != company or not year_from <= row["year"] <= year_to:
            raise ValueError("Knjiženje van zahtevanog obuhvata.")
        if not row["account"] or not row["journal_type"] or not isinstance(row["booking_date"], date):
            raise ValueError("Nedostaju obavezni podaci knjiženja.")
    job_keys = [(j["company"], j["code"]) for j in jobs]
    if len(job_keys) != len(set(job_keys)) or any(j["company"] != company or not j["code"] for j in jobs):
        raise ValueError("Neispravan šifarnik poslova.")


def publish(rows, jobs, run):
    """Publish a complete scope atomically; failures retain the previous report."""
    validate_payload(rows, jobs, run.company, run.year_from, run.year_to)
    expected = totals_for(rows)
    now = timezone.now()
    with transaction.atomic():
        scope = LedgerEntry.objects.filter(company=run.company, year__range=(run.year_from, run.year_to))
        old = {source_key(row): row for row in scope.values(*KEY_FIELDS, "pk", "source_hash", "active")}
        if not rows and any(row["active"] for row in old.values()):
            raise ValueError("Izvor je prazan, a lokalni podaci postoje. Podaci nisu uklonjeni.")
        existing_jobs = {j.code: j for j in FinanceJob.objects.filter(company=run.company)}
        for values in jobs:
            job = existing_jobs.pop(values["code"], None)
            if job is None:
                FinanceJob.objects.create(**values)
            elif any(getattr(job, k) != v for k, v in values.items()):
                for k, v in values.items():
                    setattr(job, k, v)
                job.save(update_fields=list(values))
        if existing_jobs:
            for batch in chunks([j.pk for j in existing_jobs.values()], 500):
                FinanceJob.objects.filter(pk__in=batch).update(active=False)
        creates, updates = [], []
        unchanged = 0
        for values in rows:
            digest = fingerprint(values)
            previous = old.pop(source_key(values), None)
            if previous and previous["source_hash"] == digest and previous["active"]:
                unchanged += 1
                continue
            entry = LedgerEntry(**values, source_hash=digest, active=True, removed_at=None, changed_at=now)
            if previous:
                entry.pk = previous["pk"]
                updates.append(entry)
            else:
                creates.append(entry)
        for batch in chunks(creates, 1000):
            LedgerEntry.objects.bulk_create(prepare_amounts(batch), batch_size=50)
        fields = [f.name for f in LedgerEntry._meta.concrete_fields if not f.primary_key]
        # Explicit outer batches also bound Django's CASE-expression memory usage.
        for batch in chunks(updates, 25):
            LedgerEntry.objects.bulk_update(prepare_amounts(batch), fields, batch_size=25)
        removed_ids = [v["pk"] for v in old.values() if v["active"]]
        for batch in chunks(removed_ids, 500):
            scope.filter(pk__in=batch).update(active=False, removed_at=now, changed_at=now)
        actual = {
            f"{r['year']}:{r['account']}": {
                "count": r["count"],
                "debit": r["debit"].quantize(Decimal("0.01")),
                "credit": r["credit"].quantize(Decimal("0.01")),
            }
            for r in scope.filter(active=True).values("year", "account").annotate(count=Count("pk"), debit=Sum("debit"), credit=Sum("credit"))
        }
        if actual != expected:
            raise ValueError("Kontrolni zbir lokalnih podataka ne odgovara izvoru; izmene su poništene.")
        run.source_rows = len(rows)
        run.created, run.updated, run.unchanged, run.removed = len(creates), len(updates), unchanged, len(removed_ids)
        run.source_totals = {k: {n: str(v) if isinstance(v, Decimal) else v for n, v in t.items()} for k, t in expected.items()}
        run.latest_booking_date = max((r["booking_date"] for r in rows), default=None)
        run.status, run.finished_at = "success", timezone.now()
        run.save()
    return run


def sync_ledger(year_from=2025, year_to=None, company=None):
    company = company or getattr(settings, "FINANSIJE_COMPANY", 1)
    year_to = year_to or timezone.localdate().year
    if not 2025 <= year_from <= year_to <= timezone.localdate().year:
        raise ValueError("Period sinhronizacije mora biti od 2025. do tekuće godine.")
    with sync_lock():
        # Any previous running record cannot still own this exclusive session lock.
        SyncRun.objects.filter(status="running").update(status="failed", finished_at=timezone.now(), error="Prethodni proces je prekinut pre završetka.")
        run = SyncRun.objects.create(company=company, year_from=year_from, year_to=year_to)
        try:
            rows, jobs = fetch_source(company, year_from, year_to)
            return publish(rows, jobs, run)
        except Exception as exc:
            SyncRun.objects.filter(pk=run.pk).update(status="failed", finished_at=timezone.now(), error=f"{type(exc).__name__}: {str(exc)[:1800]}")
            raise
