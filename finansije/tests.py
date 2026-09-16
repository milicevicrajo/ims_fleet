from datetime import date
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from core.models import OrganizationalUnit, PermissionCode, Role
from .models import FinanceJob, LedgerEntry, SyncRun
from .services.reports import base_querysets, summary
from .services.source import SOURCE_FIELDS, fetch_source, fingerprint, totals_for
from .services.sync import SyncBusy, sync_ledger, sync_lock


def posting(number=1, **changes):
    row = dict(
        company=1, year=2026, journal_type="IF", journal_number=number, line_number=1,
        organizational_unit=41, organizational_unit_name="OJ 41", account="61000", account_name="Prihod",
        partner_group=1, partner_code=123, partner_name="Partner", document_date=date(2026, 1, 8),
        document_reference=f"IF-{number}", debit=Decimal("0.00"), credit=Decimal("100.00"),
        currency="RSD", foreign_amount=None, description="", linked_line=None, due_date=None,
        change_status="O", job_code="410001", job_name="Posao A", center="41", booking_date=date(2026, 2, 10),
        debit_credit_flag="P", source_paid_amount=None,
    )
    row.update(changes)
    return row


def job(code="410001", center="41", **changes):
    row = dict(company=1, code=code, name="Posao A", center=center, active=True, profit_type="P")
    row.update(changes)
    return row


def save_entry(**changes):
    row = posting(**changes)
    return LedgerEntry.objects.create(**row, source_hash=fingerprint(row), changed_at=timezone.now())


class SyncTests(TestCase):
    def run_sync(self, rows, jobs=None, **kwargs):
        with patch("finansije.services.sync.fetch_source", return_value=(rows, jobs if jobs is not None else [job()])):
            return sync_ledger(year_from=2025, year_to=2026, **kwargs)

    def test_repeat_update_remove_and_reactivate_preserve_identity(self):
        run = self.run_sync([posting(), posting(2)])
        self.assertEqual((run.created, run.source_rows, run.status), (2, 2, "success"))
        entry = LedgerEntry.objects.get(journal_number=1)
        original_pk, original_changed = entry.pk, entry.changed_at
        run = self.run_sync([posting(), posting(2)])
        self.assertEqual((run.created, run.updated, run.unchanged), (0, 0, 2))
        entry.refresh_from_db()
        self.assertEqual(entry.changed_at, original_changed)
        run = self.run_sync([posting(credit=Decimal("150.00"))])
        self.assertEqual((run.updated, run.removed), (1, 1))
        entry.refresh_from_db()
        self.assertEqual(entry.pk, original_pk)
        self.assertEqual(entry.credit, Decimal("150.00"))
        self.assertFalse(LedgerEntry.objects.get(journal_number=2).active)
        run = self.run_sync([posting(credit=Decimal("150.00")), posting(2)])
        self.assertEqual(run.updated, 1)
        restored = LedgerEntry.objects.get(journal_number=2)
        self.assertTrue(restored.active)
        self.assertIsNone(restored.removed_at)

    def test_current_year_refresh_does_not_remove_prior_year(self):
        self.run_sync([posting(year=2025, booking_date=date(2025, 2, 1)), posting(2)])
        with patch("finansije.services.sync.fetch_source", return_value=([posting(3)], [job()])):
            sync_ledger(year_from=2026, year_to=2026)
        self.assertTrue(LedgerEntry.objects.get(year=2025).active)
        self.assertFalse(LedgerEntry.objects.get(journal_number=2).active)

    def test_empty_source_does_not_erase_existing_scope(self):
        self.run_sync([posting()])
        with self.assertRaisesMessage(ValueError, "Izvor je prazan"):
            self.run_sync([])
        self.assertTrue(LedgerEntry.objects.get().active)
        self.assertEqual(SyncRun.objects.first().status, "failed")

    def test_duplicate_source_fails_before_publishing(self):
        self.run_sync([posting()])
        with self.assertRaisesMessage(ValueError, "Dupliran"):
            self.run_sync([posting(), posting()])
        self.assertEqual(LedgerEntry.objects.count(), 1)
        self.assertEqual(SyncRun.objects.first().status, "failed")

    def test_source_failure_preserves_previous_report(self):
        self.run_sync([posting()])
        with patch("finansije.services.sync.fetch_source", side_effect=ConnectionError("Izvor nedostupan")):
            with self.assertRaises(ConnectionError):
                sync_ledger(year_from=2025, year_to=2026)
        self.assertEqual(LedgerEntry.objects.get().credit, Decimal("100"))
        self.assertEqual(SyncRun.objects.filter(status="success").count(), 1)

    def test_failed_reconciliation_rolls_back_entries_and_dimensions(self):
        self.run_sync([posting()])
        wrong = totals_for([posting(credit=Decimal("999"))])
        with patch("finansije.services.sync.totals_for", return_value=wrong):
            with self.assertRaisesMessage(ValueError, "Kontrolni zbir"):
                self.run_sync([posting(credit=Decimal("200"))], [job(name="Izmenjen naziv")])
        self.assertEqual(LedgerEntry.objects.get().credit, Decimal("100"))
        self.assertEqual(FinanceJob.objects.get().name, "Posao A")

    def test_missing_dimension_is_not_dropped(self):
        self.run_sync([posting(job_code="", job_name="", center="", account_name="")], [])
        self.assertEqual(LedgerEntry.objects.count(), 1)

    def test_database_enforces_source_identity(self):
        self.run_sync([posting()])
        with self.assertRaises(IntegrityError), transaction.atomic():
            save_entry()

    def test_overlapping_run_is_rejected(self):
        with sync_lock():
            with self.assertRaises(SyncBusy):
                self.run_sync([posting()])
        self.assertEqual(SyncRun.objects.count(), 0)

    def test_out_of_scope_rows_rejected(self):
        with self.assertRaisesMessage(ValueError, "van zahtevanog"):
            self.run_sync([posting(company=2)])
        self.assertFalse(LedgerEntry.objects.exists())

    def test_changed_center_and_name_are_refreshed(self):
        self.run_sync([posting()])
        run = self.run_sync([posting(center="42", job_name="Novi naziv")], [job(center="42", name="Novi naziv")])
        self.assertEqual(run.updated, 1)
        self.assertEqual(LedgerEntry.objects.get().center, "42")

    def test_mixed_nullable_amounts_survive_roundtrip(self):
        self.run_sync([
            posting(foreign_amount=Decimal("1000.00"), debit=Decimal("5160400.00")),
            posting(2, foreign_amount=None, source_paid_amount=None),
        ])
        self.assertEqual(LedgerEntry.objects.get(journal_number=1).foreign_amount, Decimal("1000.00"))
        self.assertIsNone(LedgerEntry.objects.get(journal_number=2).foreign_amount)
        self.run_sync([
            posting(foreign_amount=None, debit=Decimal("5160400.00")),
            posting(2, foreign_amount=Decimal("1000.00"), source_paid_amount=None),
        ])
        self.assertIsNone(LedgerEntry.objects.get(journal_number=1).foreign_amount)
        self.assertEqual(LedgerEntry.objects.get(journal_number=2).foreign_amount, Decimal("1000.00"))


class SourceReadTests(TestCase):
    def mock_cursor(self, connections, expected_credit=Decimal("100")):
        cursor = connections.__getitem__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.side_effect = [
            [("410001 ", "Posao A", "41 ", "D", "P")],
            [("61000 ", "Prihod")], [("2026", 41, "OJ 41")], [(1, 123, "Partner")],
            [("2026", "61000 ", 1, Decimal("0"), expected_credit)],
        ]
        row = posting()
        raw = [row[name] for name in SOURCE_FIELDS]
        raw[1], raw[6], raw[19] = "2026", "61000 ", "410001 "
        cursor.fetchmany.side_effect = [[tuple(raw)], []]
        return cursor

    @patch("finansije.services.source.connections")
    def test_source_normalizes_keys_and_uses_only_parameterized_reads(self, connections):
        cursor = self.mock_cursor(connections)
        rows, jobs = fetch_source(1, 2025, 2026)
        self.assertEqual(rows[0]["center"], "41")
        self.assertEqual(rows[0]["account"], "61000")
        self.assertEqual(jobs[0]["code"], "410001")
        for call in cursor.execute.call_args_list:
            self.assertTrue(call.args[0].lstrip().startswith("SELECT"))
            self.assertTrue(call.args[1])

    @patch("finansije.services.source.connections")
    def test_source_change_during_read_is_detected(self, connections):
        self.mock_cursor(connections, Decimal("101"))
        with self.assertRaisesMessage(ValueError, "Izvor je izmenjen"):
            fetch_source(1, 2025, 2026)


class FinancePermissionSetupTests(TestCase):
    def test_setup_is_scoped_idempotent_and_restricted_by_default(self):
        from core.permissions import sync_finance_permissions

        other = Role.objects.create(name="Drugi modul", slug="other-module")
        other.permissions.add(PermissionCode.objects.create(code="other:view"))
        sync_finance_permissions()
        sync_finance_permissions()
        finance = Role.objects.get(slug="finansije")
        self.assertSetEqual(set(finance.permissions.values_list("code", flat=True)), {
            "finansije:dashboard", "finansije:ledger", "finansije:export",
        })
        self.assertTrue(Role.objects.get(slug="uprava").permissions.filter(code="finansije:view_all").exists())
        self.assertEqual(list(other.permissions.values_list("code", flat=True)), ["other:view"])


class ReportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("finance-admin", "finance@example.invalid", "test")
        FinanceJob.objects.create(**job())
        FinanceJob.objects.create(**job("420001", "42", name="Posao B"))
        FinanceJob.objects.create(**job("410002", "41", name="Bez prometa"))
        save_entry()
        save_entry(number=2, account="51000", debit=Decimal("40"), credit=Decimal("0"))
        save_entry(number=3, account="51000", debit=Decimal("0"), credit=Decimal("10"))
        save_entry(number=4, debit=Decimal("20"), credit=Decimal("0"))
        save_entry(number=5, center="42", job_code="420001", job_name="Posao B", credit=Decimal("120"))
        save_entry(number=6, account="20400", debit=Decimal("500"), credit=Decimal("0"))
        self.params = {"date_from": "2026-02-01", "date_to": "2026-02-28", "group": "center", "kind": "pnl"}
        self.client.force_login(self.user)

    def test_net_amounts_and_shares_with_reversals(self):
        response = self.client.get(reverse("finansije:dashboard"), self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["totals"], {"revenue": Decimal("200"), "expense": Decimal("30"), "result": Decimal("170"), "count": 5})
        row = response.context["rows"][0]
        self.assertEqual(row["revenue_share"], Decimal("40"))
        self.assertEqual(row["expense_share"], Decimal("100"))
        self.assertContains(response, "Finansijska analitika")

    def test_booking_date_drives_period_not_document_date(self):
        response = self.client.get(reverse("finansije:dashboard"), dict(self.params, date_from="2026-01-01", date_to="2026-01-31"))
        self.assertEqual(response.context["totals"]["count"], 0)

    def test_month_report_and_detail_drilldown(self):
        response = self.client.get(reverse("finansije:dashboard"), dict(self.params, group="month"))
        row = response.context["rows"][0]
        self.assertEqual(row["code"], "2026-02")
        detail = self.client.get(row["ledger_url"])
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.context["page_obj"].paginator.count, 5)

    def test_account_link_matches_exact_account(self):
        save_entry(number=7, account="610001", credit=Decimal("777"))
        response = self.client.get(reverse("finansije:dashboard"), dict(self.params, group="account"))
        row = next(r for r in response.context["rows"] if r["code"] == "61000")
        detail = self.client.get(row["ledger_url"])
        self.assertEqual(detail.context["totals"]["revenue"], Decimal("200"))

    def test_zero_jobs_are_optional_and_zero_denominator_is_undefined(self):
        response = self.client.get(reverse("finansije:dashboard"), dict(self.params, group="job", include_empty="1", kind="expense"))
        self.assertEqual(len(response.context["rows"]), 3)
        self.assertTrue(all(r["revenue_share"] is None for r in response.context["rows"]))

    def test_invalid_period_and_account_do_not_show_unfiltered_results(self):
        for changes in ({"date_from": "2026-03-01"}, {"date_from": "2024-01-01"}, {"account": "5';DELETE"}):
            response = self.client.get(reverse("finansije:dashboard"), dict(self.params, **changes))
            self.assertFalse(response.context["valid"])
            self.assertEqual(response.context["totals"]["count"], 0)

    def test_all_postings_option_keeps_pnl_separate_from_turnover(self):
        response = self.client.get(reverse("finansije:ledger"), dict(self.params, kind="all"))
        self.assertEqual(response.context["page_obj"].paginator.count, 6)
        self.assertEqual(response.context["totals"]["revenue"], Decimal("200"))
        self.assertEqual(response.context["movements"]["debit"], Decimal("560"))

    def test_excel_amounts_are_numeric_and_external_text_is_not_formula(self):
        LedgerEntry.objects.filter(journal_number=1).update(partner_name="=1+1")
        response = self.client.get(reverse("finansije:export"), dict(self.params, report="ledger"))
        self.assertEqual(response.status_code, 200)
        book = load_workbook(BytesIO(response.content))
        sheet = book.active
        self.assertEqual(sheet.cell(4, 13).value, "=1+1")
        self.assertEqual(sheet.cell(4, 13).data_type, "s")
        self.assertEqual(sheet.cell(4, 17).data_type, "n")

    def test_removed_rows_are_not_reported(self):
        LedgerEntry.objects.filter(journal_number=5).update(active=False)
        response = self.client.get(reverse("finansije:dashboard"), self.params)
        self.assertEqual(response.context["totals"]["revenue"], Decimal("80"))

    def test_incomplete_years_are_visible(self):
        SyncRun.objects.create(company=1, year_from=2026, year_to=2026, status="success", finished_at=timezone.now())
        response = self.client.get(reverse("finansije:dashboard"), dict(self.params, date_from="2025-01-01"))
        self.assertEqual(response.context["missing_years"], [2025])

    def test_first_import_shows_progress_without_reading_unpublished_rows(self):
        SyncRun.objects.create(company=1, year_from=2025, year_to=2026, status="running")
        response = self.client.get(reverse("finansije:dashboard"), self.params)
        self.assertContains(response, "Sinhronizacija je u toku")
        self.assertEqual(response.context["totals"]["count"], 0)

    def test_scope_applies_to_totals_choices_links_and_export(self):
        user = get_user_model().objects.create_user("finance-limited", password="test", allowed_center_codes=" 41 ; ")
        role = Role.objects.create(name="Finansije test", slug="finance-test")
        for name in ("dashboard", "ledger", "export", "sync_status"):
            role.permissions.add(PermissionCode.objects.create(code=f"finansije:{name}"))
        user.roles.add(role)
        self.client.force_login(user)
        response = self.client.get(reverse("finansije:dashboard"), self.params)
        self.assertEqual(response.context["totals"]["revenue"], Decimal("80"))
        self.assertNotContains(response, "Posao B")
        self.assertNotIn(("42", "42"), response.context["form"].fields["center"].choices)
        forged = self.client.get(reverse("finansije:ledger"), dict(self.params, center="42"))
        self.assertEqual(forged.context["page_obj"].paginator.count, 0)
        export = self.client.get(reverse("finansije:export"), self.params)
        sheet = load_workbook(BytesIO(export.content)).active
        self.assertEqual(sheet.max_row, 4)
        self.assertEqual(sheet.cell(4, 4).value, 80)
        self.assertEqual(self.client.get(reverse("finansije:sync_status")).status_code, 403)
        user.allowed_center_codes = ""
        user.save()
        response = self.client.get(reverse("finansije:dashboard"), self.params)
        self.assertEqual(response.context["totals"]["count"], 0)

    def test_m2m_centers_with_source_padding_are_supported(self):
        user = get_user_model().objects.create_user("finance-unit", password="test")
        unit = OrganizationalUnit.objects.create(code="410001 ", name="Unit", center="41   ")
        user.allowed_centers.add(unit)
        entries, _ = base_querysets(user)
        self.assertEqual(summary(entries)["revenue"], Decimal("80"))

    def test_no_role_is_denied_and_anonymous_redirects(self):
        user = get_user_model().objects.create_user("finance-no-role", password="test")
        self.client.force_login(user)
        for route in ("dashboard", "ledger", "export", "sync_status"):
            self.assertEqual(self.client.get(reverse(f"finansije:{route}")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("finansije:dashboard")).status_code, 302)

    def test_view_all_permission_allows_complete_report(self):
        user = get_user_model().objects.create_user("finance-management", password="test")
        role = Role.objects.create(name="Uprava test", slug="finance-management")
        for name in ("dashboard", "view_all"):
            role.permissions.add(PermissionCode.objects.create(code=f"finansije:{name}"))
        user.roles.add(role)
        self.client.force_login(user)
        response = self.client.get(reverse("finansije:dashboard"), self.params)
        self.assertEqual(response.context["totals"]["revenue"], Decimal("200"))
