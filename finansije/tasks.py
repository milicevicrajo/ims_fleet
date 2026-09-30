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


@shared_task(name="finansije.tasks.sync_sef_task")
def sync_sef_task():
    """SEF fakture (ulazne i izlazne, poslednjih 45 dana) i promene statusa; ujutru, posle nocne pauze SEF-a."""
    from core.tasks import _run_with_singleton_lock

    def _runner():
        from .services import sef

        try:
            run = sef.sinhronizuj()
        except sef.SefNijePodesen as exc:
            return f"Task skipped: {exc}"
        # PDF-ovi za fakture iz istog perioda koje ga jos nemaju (nove, i ranije neuspele).
        from .sef_models import SefFaktura

        bez_pdf = sef.sa_datumom(SefFaktura.objects.filter(pdf="")).filter(datum_dok__gte=run.od, datum_dok__lte=run.do)
        return f"{sef.poruka(run)}. {sef.poruka_pdf(sef.preuzmi_pdfove(list(bez_pdf[:1000])))}"

    return _run_with_singleton_lock(task_name="finansije_sync_sef_task", lock_ttl_seconds=90 * 60, fn=_runner)


@shared_task(name="finansije.tasks.sef_pdf_task")
def sef_pdf_task(od, do, smer=""):
    """PDF-ovi koji nedostaju za period (dugme „Preuzmi PDF-ove” u Finansije → SEF fakture)."""
    from core.tasks import _run_with_singleton_lock

    def _runner():
        import datetime

        from .sef_models import SefFaktura
        from .services import sef

        qs = sef.sa_datumom(SefFaktura.objects.filter(pdf="")).filter(
            datum_dok__gte=datetime.date.fromisoformat(od), datum_dok__lte=datetime.date.fromisoformat(do))
        if smer in SefFaktura.Smer.values:
            qs = qs.filter(smer=smer)
        return f"{od}–{do}: {sef.poruka_pdf(sef.preuzmi_pdfove(list(qs)))}"

    return _run_with_singleton_lock(task_name="finansije_sef_pdf_task", lock_ttl_seconds=4 * 60 * 60, fn=_runner)


@shared_task(bind=True)
def refresh_nalog_z_task(self):
    try:
        run = refresh_nalog_z(trigger="celery", task_id=self.request.id or "")
    except SyncBusy:
        return "Task skipped: osvežavanje nalog_z je već pokrenuto."
    return (f"nalog_z {run.year_from}–{run.year_to}: "
            f"ažurirano={run.updated_rows}, dodato={run.inserted_rows}.")
