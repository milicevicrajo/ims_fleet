from celery import shared_task

from core.tasks import _run_with_singleton_lock


@shared_task(name="hr.tasks.sync_ugovori_zaposlenih_task")
def sync_ugovori_zaposlenih_task():
    """Ugovori zaposlenih iz kadrovske baze (v_hr_RadStaz); nocu u 01:15, posle zaposlenih (od 29.09.2026.)."""
    def _runner():
        from .services.ugovori import poruka, sinhronizuj

        return poruka(sinhronizuj())

    return _run_with_singleton_lock(task_name="hr_sync_ugovori_zaposlenih_task", lock_ttl_seconds=30 * 60, fn=_runner)
