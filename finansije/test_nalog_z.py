from datetime import datetime, timezone as dt_timezone
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from core.models import PermissionCode, Role
from .models import NalogZRefreshRun, SyncRun
from .services.nalog_z import (LOCK_RESOURCE, SCHEDULE_NAME, TASK_NAME, execute_refresh,
                               procedure_cursor, refresh_nalog_z)
from .services.sync import SyncBusy
from .tasks import refresh_nalog_z_task


class ProcedureSQLTests(SimpleTestCase):
    def test_consumes_sets_and_returns_exact_procedure_counts(self):
        cursor = MagicMock()
        names = ["DoGodine", "BrojDodatihRedova", "OdGodine", "BrojAzuriranihRedova"]
        cursor.description = [(name,) for name in names]
        cursor.fetchall.return_value = [(2026, 7, 2025, 120)]
        cursor.nextset.return_value = False
        self.assertEqual(execute_refresh(cursor), [2025, 2026, 120, 7])
        cursor.execute.assert_called_once_with("EXEC [IMS_ERP].[dbo].[sp_AzurirajNalogZ]")

    def test_sql_error_after_result_is_not_success(self):
        cursor = MagicMock()
        cursor.description = [(name,) for name in ("OdGodine", "DoGodine", "BrojAzuriranihRedova", "BrojDodatihRedova")]
        cursor.fetchall.return_value = [(2026, 2026, 10, 1)]
        cursor.nextset.side_effect = RuntimeError("late SQL error")
        with self.assertRaisesMessage(RuntimeError, "late SQL error"):
            execute_refresh(cursor)

    def test_missing_result_is_not_reported_as_zero_success(self):
        cursor = MagicMock(description=None)
        cursor.nextset.return_value = False
        with self.assertRaisesMessage(RuntimeError, "nije vratila"):
            execute_refresh(cursor)

    def connection(self, status=0):
        db = MagicMock(vendor="microsoft")
        db.get_autocommit.return_value = True
        db.connection.timeout = 90
        cursor = db.cursor.return_value.__enter__.return_value
        cursor.description = [("result",)]
        cursor.fetchone.return_value = (status,)
        return db, cursor

    def test_same_sql_session_lock_releases_on_error_and_restores_timeout(self):
        db, cursor = self.connection()
        with patch("finansije.services.nalog_z.connections", {"server_db": db}):
            with self.assertRaisesMessage(ValueError, "procedure failed"):
                with procedure_cursor() as held:
                    self.assertIs(held, cursor)
                    self.assertEqual(db.connection.timeout, settings.FINANSIJE_NALOG_Z_TIMEOUT)
                    raise ValueError("procedure failed")
        queries = cursor.execute.call_args_list
        self.assertIn("[IMS_ERP].sys.sp_getapplock", queries[0].args[0])
        self.assertEqual(queries[0].args[1], [LOCK_RESOURCE])
        self.assertIn("sp_releaseapplock", queries[1].args[0])
        self.assertEqual(db.connection.timeout, 90)

    def test_busy_and_lock_failure_never_enter_procedure(self):
        for status, error in [(-1, SyncBusy), (-999, RuntimeError)]:
            db, cursor = self.connection(status)
            with patch("finansije.services.nalog_z.connections", {"server_db": db}):
                with self.assertRaises(error):
                    with procedure_cursor():
                        self.fail("Entered without a SQL lock")
            self.assertEqual(cursor.execute.call_count, 1)

    def test_release_failure_closes_session(self):
        db, cursor = self.connection()
        cursor.fetchone.side_effect = [(0,), (-999,)]
        with patch("finansije.services.nalog_z.connections", {"server_db": db}), self.assertLogs("finansije.services.nalog_z"):
            with procedure_cursor():
                pass
        db.close.assert_called_once()


class RefreshHistoryTests(TestCase):
    @patch("finansije.services.nalog_z.procedure_cursor")
    @patch("finansije.services.nalog_z.execute_refresh", return_value=[2025, 2026, 30, 4])
    def test_success_and_abandoned_history(self, execute, lock):
        previous = NalogZRefreshRun.objects.create(trigger="manual")
        run = refresh_nalog_z(requested_by="admin")
        previous.refresh_from_db()
        self.assertEqual(previous.status, "unknown")
        self.assertEqual((run.status, run.updated_rows, run.inserted_rows), ("success", 30, 4))
        self.assertEqual((run.year_from, run.year_to, run.requested_by), (2025, 2026, "admin"))
        self.assertIsNotNone(run.finished_at)
        self.assertFalse(SyncRun.objects.exists())

    @patch("finansije.services.nalog_z.procedure_cursor")
    @patch("finansije.services.nalog_z.execute_refresh", side_effect=RuntimeError("SQL failed"))
    def test_failure_preserves_history_and_propagates(self, execute, lock):
        with self.assertRaisesMessage(RuntimeError, "SQL failed"):
            refresh_nalog_z(trigger="celery", task_id="task-123")
        run = NalogZRefreshRun.objects.get()
        self.assertEqual((run.status, run.task_id, run.error), ("failed", "task-123", "SQL failed"))
        self.assertIsNone(run.updated_rows)
        self.assertIsNotNone(run.finished_at)

    @patch("finansije.services.nalog_z.execute_refresh")
    def test_busy_preserves_active_run_and_records_skip(self, execute):
        active = NalogZRefreshRun.objects.create(trigger="manual")
        with patch("finansije.services.nalog_z.procedure_cursor", side_effect=SyncBusy("busy")):
            with self.assertRaises(SyncBusy):
                refresh_nalog_z()
        active.refresh_from_db()
        self.assertEqual(active.status, "running")
        self.assertEqual(NalogZRefreshRun.objects.first().status, "skipped")
        execute.assert_not_called()

    def test_connection_failure_is_recorded(self):
        with patch("finansije.services.nalog_z.procedure_cursor", side_effect=RuntimeError("offline")):
            with self.assertRaises(RuntimeError):
                refresh_nalog_z()
        self.assertEqual(NalogZRefreshRun.objects.get().status, "failed")


class RefreshEndpointTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("source-admin", "source@example.invalid", "test")
        self.client.force_login(self.user)
        self.url = reverse("finansije:nalog_z_refresh")

    @patch("finansije.views.refresh_nalog_z")
    @patch("finansije.tasks.refresh_nalog_z_task.delay")
    def test_direct_service_post_without_dispatch_and_get_is_read_only(self, delay, refresh):
        refresh.return_value = SimpleNamespace(year_from=2026, year_to=2026, updated_rows=5, inserted_rows=2)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertContains(self.client.get(reverse("finansije:sync_status")), "Osveži nalog_z")
        refresh.assert_not_called()
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        refresh.assert_called_once_with(requested_by="source-admin")
        delay.assert_not_called()

    @patch("finansije.views.refresh_nalog_z")
    def test_permission_scope_and_csrf(self, refresh):
        limited = get_user_model().objects.create_user("source-limited", password="test", allowed_center_codes="43")
        role = Role.objects.create(name="source limited", slug="source-limited")
        role.permissions.add(PermissionCode.objects.create(code="finansije:sync_status"))
        limited.roles.add(role)
        self.client.force_login(limited)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertEqual(self.client.get(reverse("finansije:sync_status"), {"draw": "1", "source": "nalog_z"}).status_code, 403)
        limited.roles.clear()
        self.assertEqual(self.client.post(self.url).status_code, 403)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        self.assertEqual(csrf_client.post(self.url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post(self.url).status_code, 302)
        refresh.assert_not_called()

    def test_busy_error_and_redirect(self):
        for error, expected in [(SyncBusy("busy"), 409), (RuntimeError("private SQL detail"), 500)]:
            with patch("finansije.views.refresh_nalog_z", side_effect=error):
                response = self.client.post(self.url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            self.assertEqual(response.status_code, expected)
            self.assertNotIn("private SQL detail", response.content.decode())
        with patch("finansije.views.refresh_nalog_z", side_effect=SyncBusy("busy")):
            self.assertRedirects(self.client.post(self.url), reverse("finansije:sync_status"))

    def test_history_native_date_sort_and_escaped_error(self):
        first = NalogZRefreshRun.objects.create(trigger="manual", status="failed", error="<script>alert(1)</script>")
        second = NalogZRefreshRun.objects.create(trigger="celery", status="success", updated_rows=10, inserted_rows=2)
        NalogZRefreshRun.objects.filter(pk=first.pk).update(started_at=datetime(2025, 12, 31, tzinfo=dt_timezone.utc))
        NalogZRefreshRun.objects.filter(pk=second.pk).update(started_at=datetime(2026, 1, 1, tzinfo=dt_timezone.utc))
        response = self.client.get(reverse("finansije:sync_status"), {
            "draw": 1, "source": "nalog_z", "order[0][column]": 0, "order[0][dir]": "asc",
        }).json()
        self.assertEqual(response["recordsTotal"], 2)
        self.assertTrue(response["data"][0][0].startswith("31.12.2025"))
        self.assertIn("&lt;script&gt;", response["data"][0][4])


class RefreshScheduleTests(TestCase):
    def test_targeted_configuration_is_idempotent_and_does_not_enable_other_tasks(self):
        interval = IntervalSchedule.objects.create(every=1, period="hours")
        other = PeriodicTask.objects.create(name="unrelated", task="other.task", enabled=False, interval=interval)
        for _ in range(2):
            call_command("configure_finansije", enable_nalog_z_schedule=True, stdout=StringIO())
        other.refresh_from_db()
        self.assertFalse(other.enabled)
        self.assertEqual(PeriodicTask.objects.count(), 2)
        task = PeriodicTask.objects.get(name=SCHEDULE_NAME)
        self.assertEqual((task.task, task.queue, task.enabled), (TASK_NAME, "sync", True))
        self.assertEqual((task.crontab.hour, task.crontab.minute, str(task.crontab.timezone)), ("10,11", "0", "Europe/Belgrade"))
        self.assertFalse(task.one_off)
        self.assertEqual(settings.CELERY_TASK_ROUTES[TASK_NAME]["queue"], "sync")

    @patch("finansije.tasks.refresh_nalog_z")
    def test_celery_calls_same_service_and_handles_skip_but_propagates_failure(self, refresh):
        refresh.return_value = SimpleNamespace(year_from=2026, year_to=2026, updated_rows=3, inserted_rows=1)
        self.assertIn("ažurirano=3", refresh_nalog_z_task.run())
        refresh.assert_called_once_with(trigger="celery", task_id="")
        refresh.side_effect = SyncBusy("busy")
        self.assertTrue(refresh_nalog_z_task.run().startswith("Task skipped"))
        refresh.side_effect = RuntimeError("failed")
        with self.assertRaises(RuntimeError):
            refresh_nalog_z_task.run()
