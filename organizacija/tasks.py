from celery import shared_task

from fleet.tasks import _run_with_singleton_lock
from organizacija.services import sync


@shared_task
def sync_organizacija_task():
    """Nova sinhronizacija organizacije, 01:40 — posle stare (`fleet.tasks.fetch_job_codes`, 01:30).

    Stara ostaje nepromenjena i merodavna; ova samo osvezava registar i poredi ga sa starom.
    """
    return _run_with_singleton_lock(
        task_name="sync_organizacija_task",
        lock_ttl_seconds=90 * 60,
        fn=lambda: sync.poruka(sync.sinhronizuj()),
    )
