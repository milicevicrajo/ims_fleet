import logging

from celery import shared_task

from core.tasks import _run_with_singleton_lock
from .services.euf import sync_euf_invoice_snapshots
from .services.source_snapshots import sync_euf_item_snapshots, sync_goods_snapshots


logger = logging.getLogger(__name__)


def _sync_result_message(label, snapshots):
    count = len(snapshots)
    message = f"{label}: sinhronizovano={count}"
    logger.info(message)
    return message


@shared_task
def sync_euf_invoices_task(q=None, limit=2000):
    def _runner():
        snapshots = sync_euf_invoice_snapshots(q=q, limit=limit)
        return _sync_result_message("EUF fakture", snapshots)

    return _run_with_singleton_lock(
        task_name="nabavka_sync_euf_invoices_task",
        lock_ttl_seconds=2 * 60 * 60,
        fn=_runner,
    )


@shared_task
def sync_uf_items_task(q=None, limit=10000):
    def _runner():
        snapshots = sync_euf_item_snapshots(q=q, limit=limit)
        return _sync_result_message("UF stavke", snapshots)

    return _run_with_singleton_lock(
        task_name="nabavka_sync_uf_items_task",
        lock_ttl_seconds=3 * 60 * 60,
        fn=_runner,
    )


@shared_task
def sync_goods_task(q=None, limit=10000):
    def _runner():
        snapshots = sync_goods_snapshots(q=q, limit=limit)
        return _sync_result_message("Roba", snapshots)

    return _run_with_singleton_lock(
        task_name="nabavka_sync_goods_task",
        lock_ttl_seconds=3 * 60 * 60,
        fn=_runner,
    )
