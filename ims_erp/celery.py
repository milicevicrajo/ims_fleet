from __future__ import absolute_import, unicode_literals

import logging
import os
import sys
import time

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun


if sys.stdin is None:
    sys.stdin = open(os.devnull)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ims_erp.settings.production")

app = Celery("ims_erp")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

logger = logging.getLogger("celery.task_audit")
_task_start_times = {}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@task_prerun.connect
def log_task_start(sender=None, task_id=None, task=None, args=None, kwargs=None, **_extra):
    task_name = getattr(sender, "name", None) or getattr(task, "name", None) or "unknown"
    _task_start_times[task_id] = time.monotonic()
    logger.info(
        "CELERY_TASK_START task=%s id=%s args=%s kwargs=%s",
        task_name,
        task_id,
        args or (),
        kwargs or {},
    )


@task_postrun.connect
def log_task_finish(sender=None, task_id=None, task=None, retval=None, state=None, **_extra):
    task_name = getattr(sender, "name", None) or getattr(task, "name", None) or "unknown"
    started = _task_start_times.pop(task_id, None)
    elapsed = time.monotonic() - started if started is not None else None
    logger.info(
        "CELERY_TASK_FINISH task=%s id=%s state=%s elapsed=%s retval=%s",
        task_name,
        task_id,
        state,
        f"{elapsed:.2f}s" if elapsed is not None else "-",
        retval,
    )


@task_failure.connect
def log_task_failure(sender=None, task_id=None, exception=None, traceback=None, args=None, kwargs=None, **_extra):
    task_name = getattr(sender, "name", None) or "unknown"
    logger.error(
        "CELERY_TASK_FAILURE task=%s id=%s args=%s kwargs=%s error=%r",
        task_name,
        task_id,
        args or (),
        kwargs or {},
        exception,
        exc_info=(type(exception), exception, traceback) if exception and traceback else None,
    )
