from celery import shared_task
from django.utils import timezone

from .services.sync import SyncBusy, sync_ledger
from .services.nalog_z import refresh_nalog_z


def _sync(year_from, year_to=None):
    try:
        run = sync_ledger(year_from=year_from, year_to=year_to)
    except SyncBusy:
        return "Task skipped: sinhronizacija finansija je već pokrenuta."
    return f"Finansije: preuzeto={run.source_rows}, novo={run.created}, izmenjeno={run.updated}, uklonjeno={run.removed}."


@shared_task
def sync_ledger_task(year_from=2025, year_to=None):
    """Celery entry point to the same service used by the manual sync button."""
    return _sync(year_from, year_to)


@shared_task
def sync_current_year():
    return _sync(timezone.localdate().year)


@shared_task
def sync_all_years():
    return _sync(2025)


@shared_task(bind=True)
def refresh_nalog_z_task(self):
    try:
        run = refresh_nalog_z(trigger="celery", task_id=self.request.id or "")
    except SyncBusy:
        return "Task skipped: osvežavanje nalog_z je već pokrenuto."
    return (f"nalog_z {run.year_from}–{run.year_to}: "
            f"ažurirano={run.updated_rows}, dodato={run.inserted_rows}.")
