from celery import shared_task
from django.utils import timezone

from .services.sync import SyncBusy, sync_ledger


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
