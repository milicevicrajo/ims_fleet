from celery import shared_task
from finansije.services.sync import SyncBusy
from .services.sync import sync_collections


@shared_task(bind=True, name="potrazivanja.tasks.sync_collections_task")
def sync_collections_task(self):
    try:
        run = sync_collections(trigger="celery", task_id=self.request.id or "")
    except SyncBusy:
        return {"status": "skipped"}
    return {"status": run.status, "run_id": run.pk}
