"""Refresh only the fixed IMS_ERP source table; never dispatch arbitrary SQL."""
from contextlib import contextmanager
import logging

from django.conf import settings
from django.db import connections
from django.utils import timezone

from finansije.models import NalogZRefreshRun
from .sync import SyncBusy

logger = logging.getLogger(__name__)
TASK_NAME = "finansije.tasks.refresh_nalog_z_task"
SCHEDULE_NAME = "Finansije - osvezavanje nalog_z u 10 i 11"
LOCK_RESOURCE = "IMS_ERP.dbo.sp_AzurirajNalogZ"


@contextmanager
def procedure_timeout(db):
    native = db.connection
    previous = native.timeout
    native.timeout = settings.FINANSIJE_NALOG_Z_TIMEOUT
    try:
        yield
    finally:
        if db.connection is native:
            native.timeout = previous


def scalar_result(cursor):
    while cursor.description is None:
        if not cursor.nextset():
            raise RuntimeError("SQL Server nije vratio status zaključavanja.")
    return cursor.fetchone()[0]


@contextmanager
def procedure_cursor():
    # Acquire and release in IMS_ERP, on the SAME session that runs the procedure.
    db = connections["server_db"]
    if db.vendor != "microsoft" or not db.get_autocommit():
        raise RuntimeError("Osvežavanje nalog_z zahteva SQL Server vezu van spoljne transakcije.")
    with procedure_timeout(db), db.cursor() as cursor:
        cursor.execute("""DECLARE @result int;
            EXEC @result = [IMS_ERP].sys.sp_getapplock @Resource=%s,
                @LockMode='Exclusive', @LockOwner='Session', @LockTimeout=0;
            SELECT @result;""", [LOCK_RESOURCE])
        result = scalar_result(cursor)
        if result == -1:
            raise SyncBusy("Osvežavanje nalog_z je već pokrenuto.")
        if result < 0:
            raise RuntimeError(f"SQL zaključavanje nije uspelo (kod {result}).")
        try:
            yield cursor
        finally:
            try:
                cursor.execute("""DECLARE @result int;
                    EXEC @result = [IMS_ERP].sys.sp_releaseapplock
                        @Resource=%s, @LockOwner='Session';
                    SELECT @result;""", [LOCK_RESOURCE])
                if scalar_result(cursor) < 0:
                    raise RuntimeError("SQL zaključavanje nije oslobođeno.")
            except Exception:
                # Closing the owning session also releases a session-owned lock.
                logger.exception("Neuspešno oslobađanje nalog_z zaključavanja; zatvaranje veze.")
                db.close()


def execute_refresh(cursor):
    cursor.execute("EXEC [IMS_ERP].[dbo].[sp_AzurirajNalogZ]")
    required = ("OdGodine", "DoGodine", "BrojAzuriranihRedova", "BrojDodatihRedova")
    result = None
    # Consume ALL result sets: SQL/ODBC can surface an error on nextset().
    while True:
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            if all(name in columns for name in required):
                rows = cursor.fetchall()
                if len(rows) != 1 or result is not None:
                    raise RuntimeError("Procedura je vratila neočekivan broj rezultata.")
                values = dict(zip(columns, rows[0]))
                result = [int(values[name]) for name in required]
                if not 1 <= result[0] <= result[1] <= 9999 or min(result[2:]) < 0:
                    raise RuntimeError("Procedura je vratila neispravne brojače.")
        if not cursor.nextset():
            break
    if result is None:
        raise RuntimeError("Procedura nije vratila očekivane godine i brojače; proverite stanje baze.")
    return result


def refresh_nalog_z(*, trigger="manual", requested_by="", task_id=""):
    """Shared synchronous service for HTTP and Celery. No automatic retries."""
    if trigger not in ("manual", "celery"):
        raise ValueError("Nepoznat način pokretanja.")
    run = None
    metadata = dict(trigger=trigger, requested_by=str(requested_by)[:255], task_id=str(task_id)[:255])
    try:
        with procedure_cursor() as cursor:
            # A previous crashed worker may have left a running history row.
            # The acquired SQL lock proves that no participating runner is active.
            NalogZRefreshRun.objects.filter(status="running").update(
                status="unknown", finished_at=timezone.now(),
                error="Prethodno izvršavanje nije zabeležilo završetak. Proverite podatke u bazi.",
            )
            run = NalogZRefreshRun.objects.create(**metadata)
            try:
                run.year_from, run.year_to, run.updated_rows, run.inserted_rows = execute_refresh(cursor)
            except Exception as exc:
                run.status, run.error = "failed", str(exc)
                raise
            else:
                run.status = "success"
            finally:
                run.finished_at = timezone.now()
                run.save()
    except SyncBusy as exc:
        NalogZRefreshRun.objects.create(**metadata, status="skipped", finished_at=timezone.now(), error=str(exc))
        raise
    except Exception as exc:
        if run is None:
            NalogZRefreshRun.objects.create(**metadata, status="failed", finished_at=timezone.now(), error=str(exc))
        raise
    return run
