from __future__ import absolute_import, unicode_literals

import logging
import os
import sys
import time
from datetime import timedelta

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun
from django.db import DatabaseError
from django.utils import timezone


if sys.stdin is None:
    sys.stdin = open(os.devnull)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ims_erp.settings.production")

app = Celery("ims_erp")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

logger = logging.getLogger("celery.task_audit")
_task_start_times = {}
_task_display_name_cache = {}


def _safe_json_value(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, (str, int, float, bool, list, tuple, dict)):
        try:
            import json

            json.dumps(value)
            return value
        except (TypeError, ValueError):
            pass
    return str(value)


def _task_display_name(task_name):
    if task_name in _task_display_name_cache:
        return _task_display_name_cache[task_name]
    display_name = task_name
    try:
        from django_celery_beat.models import PeriodicTask

        periodic_task = PeriodicTask.objects.filter(task=task_name).order_by("name").first()
        if periodic_task:
            display_name = periodic_task.name
    except Exception:
        pass
    _task_display_name_cache[task_name] = display_name
    return display_name


def _task_status_from_result(state, retval):
    text = str(retval or "")
    normalized = text.strip().lower()
    if state == "FAILURE":
        return "failure"
    if normalized.startswith("skip:") or normalized.startswith("task skipped"):
        return "skipped"
    return "success"


def _short_task_message(status, retval=None, error=None):
    if status == "started":
        return "Task je pokrenut."
    if status == "failure":
        return f"Neuspesan: {str(error)[:450]}" if error else "Task nije uspeo."
    if status == "skipped":
        return f"Preskocen: {str(retval)[:450]}" if retval else "Task je preskocen."

    text = str(retval or "").strip()
    if text:
        return text[:500]
    return "Task je uspesno zavrsen."


def _write_task_history(task_id, task_name, **values):
    if not task_id:
        return
    try:
        from core.models import TaskHistory

        defaults = {
            "task_name": task_name,
            "display_name": _task_display_name(task_name),
        }
        defaults.update(values)
        TaskHistory.objects.update_or_create(task_id=task_id, defaults=defaults)
    except DatabaseError:
        logger.debug("Task history write skipped for task_id=%s", task_id, exc_info=True)
    except Exception:
        logger.debug("Task history write failed for task_id=%s", task_id, exc_info=True)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@task_prerun.connect
def log_task_start(sender=None, task_id=None, task=None, args=None, kwargs=None, **_extra):
    task_name = getattr(sender, "name", None) or getattr(task, "name", None) or "unknown"
    started_monotonic = time.monotonic()
    started_at = timezone.now()
    _task_start_times[task_id] = (started_monotonic, started_at)
    _write_task_history(
        task_id,
        task_name,
        status="started",
        short_message=_short_task_message("started"),
        args=_safe_json_value(args or (), []),
        kwargs=_safe_json_value(kwargs or {}, {}),
        started_at=started_at,
        finished_at=None,
        elapsed_seconds=None,
        result="",
        error="",
    )
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
    if isinstance(started, tuple):
        started_monotonic, started_at = started
    else:
        started_monotonic, started_at = started, None
    elapsed = time.monotonic() - started_monotonic if started_monotonic is not None else None
    finished_at = timezone.now()
    status = _task_status_from_result(state, retval)
    _write_task_history(
        task_id,
        task_name,
        status=status,
        short_message=_short_task_message(status, retval=retval),
        result=str(retval or ""),
        started_at=started_at or (finished_at - timedelta(seconds=elapsed) if elapsed is not None else None),
        finished_at=finished_at,
        elapsed_seconds=elapsed,
    )
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
    started = _task_start_times.get(task_id)
    if isinstance(started, tuple):
        started_monotonic, started_at = started
    else:
        started_monotonic, started_at = started, None
    elapsed = time.monotonic() - started_monotonic if started_monotonic is not None else None
    finished_at = timezone.now()
    _write_task_history(
        task_id,
        task_name,
        status="failure",
        short_message=_short_task_message("failure", error=exception),
        error=str(exception or ""),
        args=_safe_json_value(args or (), []),
        kwargs=_safe_json_value(kwargs or {}, {}),
        started_at=started_at or (finished_at - timedelta(seconds=elapsed) if elapsed is not None else None),
        finished_at=finished_at,
        elapsed_seconds=elapsed,
    )
    logger.error(
        "CELERY_TASK_FAILURE task=%s id=%s args=%s kwargs=%s error=%r",
        task_name,
        task_id,
        args or (),
        kwargs or {},
        exception,
        exc_info=(type(exception), exception, traceback) if exception and traceback else None,
    )
