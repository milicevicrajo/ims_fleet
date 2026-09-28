from celery import shared_task

from fleet.tasks import _run_with_singleton_lock
from organizacija.services import sync


@shared_task
def sync_organizacija_task():
    """Sinhronizacija organizacije, 01:40 — jedini vlasnik organizacije od 28.09.2026.

    Osvezava registar, veze svih modula, centar na knjizenjima, zaposlene i `OrganizationalUnit`.
    Stara sinhronizacija (`fleet.tasks.fetch_job_codes`, 01:30) je ugasena.
    """
    return _run_with_singleton_lock(
        task_name="sync_organizacija_task",
        lock_ttl_seconds=90 * 60,
        fn=lambda: sync.poruka(sync.sinhronizuj()),
    )
