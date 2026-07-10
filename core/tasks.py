import logging
import os
import time
from io import StringIO

from celery import shared_task
from django.conf import settings
from django.core.management import call_command
from django.db import close_old_connections
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)
LOCK_PREFIX = "ims_erp:task-lock"


def _run_with_singleton_lock(task_name, lock_ttl_seconds, fn):
    lock_key = f"{LOCK_PREFIX}:{task_name}"
    lock = None
    pid = os.getpid()
    started_monotonic = time.monotonic()

    close_old_connections()
    try:
        redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
        redis = Redis.from_url(redis_url)
        lock = redis.lock(lock_key, timeout=lock_ttl_seconds, blocking=False)
        try:
            acquired = lock.acquire()
        except RedisError:
            logger.warning("%s lock unavailable; running without singleton lock.", task_name)
            lock = None
            logger.info("%s started pid=%s without lock", task_name, pid)
            return fn()

        if not acquired:
            logger.info("%s skipped because another run is active.", task_name)
            return "Task skipped: another run is already active."

        logger.info("%s started pid=%s", task_name, pid)
        return fn()
    finally:
        close_old_connections()
        if lock is not None:
            try:
                if getattr(lock, "owned", lambda: False)():
                    lock.release()
            except RedisError:
                logger.warning("%s lock release skipped because Redis is unavailable.", task_name)
        logger.info(
            "%s finished pid=%s duration=%.2fs",
            task_name,
            pid,
            time.monotonic() - started_monotonic,
        )


@shared_task
def sync_permission_codes_task():
    def _runner():
        output = StringIO()
        call_command("sync_permission_codes", stdout=output)
        call_command("sync_celery_periodic_tasks", stdout=output)
        return output.getvalue().strip()

    return _run_with_singleton_lock(
        task_name="sync_permission_codes_task",
        lock_ttl_seconds=30 * 60,
        fn=_runner,
    )
