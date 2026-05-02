from fleet.utils import (
    fetch_policy_data, 
    fetch_service_data, 
    fetch_requisition_data,
    fetch_ddor_insurance_data,  
    process_vehicle_retirements
)
from fleet.selenium_integrations import (
    nis_data_import,
    omv_putnicka_data_import,
    omv_teretna_data_import,
    kerio_login,
)
from hr.sync import sync_employees_from_hr_view
from celery import shared_task
from django.core.management import call_command
from django.conf import settings
from django.db import close_old_connections
from io import StringIO
from redis import Redis
import logging
import os
import time


logger = logging.getLogger(__name__)
LOCK_PREFIX = "ims_erp:task-lock"


def _run_with_singleton_lock(task_name, lock_ttl_seconds, fn):
    """
    Sprečava preklapanje istog taska ako se prethodni izvršava predugo.
    Lock automatski ističe posle `lock_ttl_seconds`.
    """
    lock_key = f"{LOCK_PREFIX}:{task_name}"
    lock = None
    pid = os.getpid()
    started_monotonic = time.monotonic()

    # Celery worker može dugo da živi; očisti eventualno zastarele/stale konekcije
    # pre ulaska u posao kako bismo smanjili curenje socket-a.
    close_old_connections()
    logger.info("TASK_START: %s pid=%s ttl=%ss", task_name, pid, lock_ttl_seconds)

    try:
        redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
        lock = redis_client.lock(lock_key, timeout=lock_ttl_seconds)
        if not lock.acquire(blocking=False):
            msg = f"SKIP: task '{task_name}' je već aktivan."
            logger.warning(msg)
            return msg
    except Exception:
        # Fail-open: ako lock servis privremeno nije dostupan, task i dalje ide.
        logger.exception("Lock mehanizam nije dostupan za task '%s'.", task_name)
        try:
            result = fn()
            elapsed = time.monotonic() - started_monotonic
            logger.info("TASK_DONE: %s pid=%s elapsed=%.2fs (fail-open lock)", task_name, pid, elapsed)
            return result
        except Exception:
            elapsed = time.monotonic() - started_monotonic
            logger.exception("TASK_FAIL: %s pid=%s elapsed=%.2fs (fail-open lock)", task_name, pid, elapsed)
            raise
        finally:
            close_old_connections()

    try:
        result = fn()
        elapsed = time.monotonic() - started_monotonic
        logger.info("TASK_DONE: %s pid=%s elapsed=%.2fs", task_name, pid, elapsed)
        return result
    except Exception:
        elapsed = time.monotonic() - started_monotonic
        logger.exception("TASK_FAIL: %s pid=%s elapsed=%.2fs", task_name, pid, elapsed)
        raise
    finally:
        if lock is not None:
            try:
                lock.release()
            except Exception:
                # Lock je možda istekao pre završetka taska.
                logger.warning("Lock release preskočen za task '%s'.", task_name)
        close_old_connections()

@shared_task
def run_nis_command():
    return _run_with_singleton_lock(
        task_name="run_nis_command",
        lock_ttl_seconds=4 * 60 * 60,
        fn=nis_data_import,
    )


@shared_task
def run_omv_putnicka_command():
    return _run_with_singleton_lock(
        task_name="run_omv_putnicka_command",
        lock_ttl_seconds=4 * 60 * 60,
        fn=omv_putnicka_data_import,
    )

@shared_task
def run_omv_teretna_command():
    return _run_with_singleton_lock(
        task_name="run_omv_teretna_command",
        lock_ttl_seconds=4 * 60 * 60,
        fn=omv_teretna_data_import,
    )

# Zadaci za povlačenje podataka
@shared_task
def fetch_policy_data_task():
    def _runner():
        result = fetch_policy_data(last_24_hours=True)
        return f"Fetch Policy Data: {result}"

    return _run_with_singleton_lock(
        task_name="fetch_policy_data_task",
        lock_ttl_seconds=90 * 60,
        fn=_runner,
    )

@shared_task
def fetch_service_data_task():
    def _runner():
        result = fetch_service_data(last_24_hours=True)
        return f"Fetch Service Data: {result}"

    return _run_with_singleton_lock(
        task_name="fetch_service_data_task",
        lock_ttl_seconds=90 * 60,
        fn=_runner,
    )

@shared_task
def fetch_requisition_data_task():
    def _runner():
        result = fetch_requisition_data(last_24_hours=True)
        return f"Fetch Requisition Data: {result}"

    return _run_with_singleton_lock(
        task_name="fetch_requisition_data_task",
        lock_ttl_seconds=90 * 60,
        fn=_runner,
    )

@shared_task
def kerio_login_task():
    return _run_with_singleton_lock(
        task_name="kerio_login_task",
        lock_ttl_seconds=30 * 60,
        fn=kerio_login,
    )
				

@shared_task
def fetch_job_codes():
    def _runner():
        from fleet.utils import sync_organizational_units_from_view
        return sync_organizational_units_from_view()

    return _run_with_singleton_lock(
        task_name="fetch_job_codes",
        lock_ttl_seconds=60 * 60,
        fn=_runner,
    )

@shared_task
def proveri_otpis():
    return _run_with_singleton_lock(
        task_name="proveri_otpis",
        lock_ttl_seconds=60 * 60,
        fn=process_vehicle_retirements,
    )

@shared_task
def fetch_ddor_data_task():   # ← NOVI Celery task
    def _runner():
        result = fetch_ddor_insurance_data()
        return f"Fetch DDOR Insurance Data: {result}"

    return _run_with_singleton_lock(
        task_name="fetch_ddor_data_task",
        lock_ttl_seconds=90 * 60,
        fn=_runner,
    )


@shared_task
def sync_hr_employees_task():
    def _runner():
        result = sync_employees_from_hr_view()
        return (
            "Sync HR Employees: "
            f"ukupno={result['total']}, "
            f"kreirano={result['created']}, "
            f"azurirano={result['updated']}, "
            f"azurirano_neaktivni={result['updated_inactive']}, "
            f"preskoceno_neaktivni={result['skipped_inactive']}"
        )

    return _run_with_singleton_lock(
        task_name="sync_hr_employees_task",
        lock_ttl_seconds=90 * 60,
        fn=_runner,
    )


@shared_task
def sync_permission_codes_task():
    def _runner():
        output = StringIO()
        call_command("sync_permission_codes", stdout=output)
        return output.getvalue().strip()

    return _run_with_singleton_lock(
        task_name="sync_permission_codes_task",
        lock_ttl_seconds=30 * 60,
        fn=_runner,
    )


@shared_task
def create_garaza_group_task(usernames=None, clear_existing=True, dry_run=False):
    def _runner():
        output = StringIO()
        command_args = []

        if not clear_existing:
            command_args.append("--no-clear-existing")

        if dry_run:
            command_args.append("--dry-run")

        if usernames:
            command_args.append("--users")
            command_args.extend(list(usernames))

        call_command("create_garaza_group", *command_args, stdout=output)
        return output.getvalue().strip()

    return _run_with_singleton_lock(
        task_name="create_garaza_group_task",
        lock_ttl_seconds=30 * 60,
        fn=_runner,
    )
