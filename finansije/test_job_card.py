from datetime import date
from decimal import Decimal
from unittest.mock import patch
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import OrganizationalUnit, PermissionCode, Role
from fleet.models import JobCode, PutniNalog, Vehicle, VehicleTravelOrder
from hr.models import Employee
from .forms import JobMonthForm
from .models import FinanceJob, LedgerEntry, SyncRun
from .services.job_card import assigned_vehicles
from .tests import job, save_entry


class JobCardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("job-admin", "job@example.invalid", "test")
        self.client.force_login(self.user)
        self.url = reverse("finansije:job_card")
        FinanceJob.objects.create(**job())
        FinanceJob.objects.create(**job("420001", "42", name="Other job"))
        SyncRun.objects.create(company=1, year_from=2025, year_to=2026, status="success")
        self.collections = patch("finansije.services.job_tables.job_balances", return_value={'snapshot': None, 'rows': []})
        self.collections_mock = self.collections.start()
        self.addCleanup(self.collections.stop)

    def get_card(self, **params):
        return self.client.get(self.url, {"job": "410001", "year": 2026, "month": 2, **params})

    def get_table(self, table, **params):
        return self.client.get(reverse("finansije:job_table", args=[table]), {"job": "410001", "year": 2026, "month": 2, **params})

    def test_monthly_totals_exclude_closings_other_jobs_years_and_inactive_rows(self):
        save_entry()
        save_entry(number=2, account="51200", debit=Decimal("40"), credit=Decimal("0"))
        save_entry(number=3, account="51201", credit=Decimal("10"))
        save_entry(number=4, journal_type="ZAT", account="51200", credit=Decimal("900"))
        save_entry(number=5, account="59900", debit=Decimal("500"), credit=Decimal("0"))
        save_entry(number=6, job_code="420001", center="42", credit=Decimal("1000"))
        save_entry(number=7, booking_date=date(2026, 3, 1), credit=Decimal("1000"))
        save_entry(number=8, year=2025, booking_date=date(2025, 2, 1), credit=Decimal("1000"))
        save_entry(number=10, company=2, credit=Decimal("1000"))
        inactive = save_entry(number=9, credit=Decimal("1000"))
        LedgerEntry.objects.filter(pk=inactive.pk).update(active=False)
        response = self.get_card()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["totals"]["revenue"], Decimal("100"))
        self.assertEqual(response.context["totals"]["expense"], Decimal("30"))
        self.assertEqual(response.context["totals"]["result"], Decimal("70"))
        expenses = self.get_table("expenses").json()["data"]
        self.assertEqual([(r[0]["sort"], Decimal(r[1]["sort"]), Decimal(r[2]["sort"])) for r in expenses], [("512", Decimal("-30"), Decimal("100"))])
        self.assertIn("finance-amount-negative", expenses[0][1]["display"])
        self.assertContains(response, "28.02.2026.")
        self.assertContains(response, "Interne fakture · ON")

    def test_if_uses_document_month_and_only_agreed_receivable_accounts(self):
        save_entry(document_date=date(2026, 2, 9))
        save_entry(line_number=2, account="20400", debit=Decimal("120"), credit=Decimal("0"), document_date=date(2026, 2, 9))
        save_entry(line_number=3, account="47000", credit=Decimal("20"), document_date=date(2026, 2, 9))
        save_entry(line_number=4, job_code="420001", center="42", credit=Decimal("800"), document_date=date(2026, 2, 9))
        save_entry(number=2, document_date=date(2026, 1, 31))
        save_entry(number=3, journal_type="ON", document_date=date(2026, 2, 9))
        save_entry(number=4, account="20500", debit=Decimal("60"), credit=Decimal("10"), document_date=date(2026, 2, 28))
        save_entry(number=5, account="204001", debit=Decimal("900"), document_date=date(2026, 2, 9))
        save_entry(number=6, account="20400", debit=Decimal("900"), document_date=date(2026, 1, 31))
        save_entry(number=7, account="20400", debit=Decimal("900"), document_date=date(2026, 2, 9), year=2025)
        save_entry(number=8, account="20400", debit=Decimal("900"), document_date=date(2026, 2, 9), company=2)
        save_entry(number=9, account="20400", debit=Decimal("900"), document_date=date(2026, 2, 9), job_code="420001", center="42")
        inactive = save_entry(number=10, account="20400", debit=Decimal("900"), document_date=date(2026, 2, 9))
        LedgerEntry.objects.filter(pk=inactive.pk).update(active=False)
        response = self.get_table("invoices")
        invoices = response.json()["data"]
        self.assertEqual(len(invoices), 2)
        self.assertEqual(Decimal(invoices[0][4]["sort"]), Decimal("120"))
        self.assertEqual(Decimal(invoices[1][4]["sort"]), Decimal("50"))
        self.assertIn("170", response.json()["footer"]["invoice_amount"])
        self.assertEqual(invoices[0][0]["sort"], "2026-02-09")

    def test_if_keeps_separate_documents_partners_and_negative_corrections(self):
        save_entry(account="20400", document_date=date(2026, 2, 1), debit=Decimal("100"), credit=Decimal("0"))
        save_entry(account="20400", line_number=2, document_reference="IF-B", document_date=date(2026, 2, 1), debit=Decimal("-20"), credit=Decimal("0"))
        save_entry(account="20500", line_number=3, partner_code=222, document_date=date(2026, 2, 1), debit=Decimal("30"), credit=Decimal("0"))
        data = self.get_table("invoices").json()
        self.assertEqual(len(data["data"]), 3)
        self.assertEqual(sum(Decimal(r[4]["sort"]) for r in data["data"]), Decimal("110"))

    def test_internal_invoices_use_all_four_exact_accounts_and_preserve_negative_amounts(self):
        for line, account in enumerate(("61420", "61421", "61521", "64002"), 1):
            save_entry(journal_type="ON", line_number=line, account=account,
                       document_date=date(2026, 2, 9), credit=Decimal("-20"), debit=Decimal("5"))
        for number, changes in enumerate((
                {"account": "614200"}, {"account": "61300"}, {"journal_type": "IF"},
                {"year": 2025}, {"company": 2}, {"job_code": "420001", "center": "42"},
                {"document_date": date(2026, 3, 1)}), 2):
            values = dict(journal_type="ON", account="61420", document_date=date(2026, 2, 9))
            save_entry(number=number, **{**values, **changes})
        inactive = save_entry(number=20, journal_type="ON", account="64002", document_date=date(2026, 2, 9))
        LedgerEntry.objects.filter(pk=inactive.pk).update(active=False)
        data = self.get_table("internal_invoices").json()
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0][2]["sort"], "2026/ON/1")
        self.assertEqual(Decimal(data["data"][0][4]["sort"]), Decimal("-100"))
        self.assertIn("finance-amount-negative", data["data"][0][4]["display"])
        self.assertIn("100", data["footer"]["internal_invoice_amount"])
        save_entry(number=21, journal_type="ON", account="61521", document_date=date(2026, 8, 1))
        self.assertEqual(len(self.get_table("internal_invoices", month="").json()["data"]), 3)
        SyncRun.objects.all().delete()
        self.assertEqual(self.get_table("internal_invoices").status_code, 409)

    def test_uncovered_year_is_missing_not_zero_and_empty_synchronized_job_is_zero(self):
        response = self.get_card()
        self.assertTrue(response.context["finance_available"])
        self.assertEqual(response.context["totals"]["result"], Decimal("0"))
        SyncRun.objects.all().delete()
        response = self.get_card()
        self.assertFalse(response.context["finance_available"])
        self.assertNotContains(response, 'id="JobInvoices"')
        self.assertContains(response, "Nema potvrđenih sinhronizovanih")
        self.assertEqual(self.get_table("invoices").status_code, 409)

    def test_invalid_or_unauthorized_choice_does_not_query_other_modules(self):
        for params in ({"job": "unknown"}, {"month": 13}, {"year": 2024}, {"month": "bad"}):
            response = self.get_card(**params)
            self.assertFalse(response.context["valid"])
            self.assertNotIn("totals", response.context)
        self.collections_mock.assert_not_called()

    def test_leap_february_and_year_end(self):
        with patch("finansije.forms.timezone.localdate", return_value=date(2028, 3, 1)):
            form = JobMonthForm({"year": 2028, "month": 2}, choices=[])
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data["date_to"], date(2028, 2, 29))
        form = JobMonthForm({"year": 2025, "month": 12}, choices=[])
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["date_to"], date(2025, 12, 31))

    def test_finance_job_scope_and_module_permissions_are_preserved(self):
        user = get_user_model().objects.create_user("job-limited", allowed_center_codes="41")
        role = Role.objects.create(name="Job viewer", slug="job-viewer")
        role.permissions.add(PermissionCode.objects.create(code="finansije:dashboard"))
        user.roles.add(role)
        self.client.force_login(user)
        response = self.get_card()
        self.assertEqual(response.status_code, 200)
        for flag in ("can_collections", "can_vehicles", "can_custody", "can_employees", "can_travel", "can_ledger"):
            self.assertFalse(response.context[flag])
        self.collections_mock.assert_not_called()
        response = self.get_card(job="420001")
        self.assertFalse(response.context["valid"])
        self.assertNotContains(response, "Other job")
        user.roles.clear()
        self.assertEqual(self.get_card().status_code, 403)
        self.client.logout()
        self.assertEqual(self.get_card().status_code, 302)

    def test_current_collections_are_scoped_and_not_reported_as_monthly_cash(self):
        self.collections_mock.return_value = {'snapshot': SimpleNamespace(pk=91, as_of_date=date(2026,9,18), source_observed_at=timezone.now()),
            'rows': [{'identity_id': 123, 'partner_code': 123, 'partner_name': 'Partner', 'amounts': [Decimal(i) for i in range(1,10)]}]}
        response = self.get_card()
        self.collections_mock.assert_not_called()
        row = self.get_table("collections").json()["data"][0]
        self.collections_mock.assert_called_once_with(self.user, "410001", company=1)
        self.assertEqual([Decimal(c["sort"]) for c in row[1:]], list(map(Decimal, range(1, 10))))
        self.assertContains(response, "Ovaj deo se ne filtrira po izabranom mesecu")
        self.assertIn('/potrazivanja/partner/123/?snapshot=91', row[0]['display'])

    def test_collections_failure_keeps_monthly_finance_available(self):
        save_entry()
        self.collections_mock.side_effect = DatabaseError("unavailable")
        response = self.get_card()
        with self.assertLogs("finansije.views", level="ERROR"):
            ajax = self.get_table("collections")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ajax.status_code, 503)
        self.assertEqual(response.context["totals"]["revenue"], Decimal("100"))

    def test_vehicle_assignment_stops_when_moved_to_another_job_and_can_return(self):
        a = OrganizationalUnit.objects.create(code="410001", name="A", center="41")
        b = OrganizationalUnit.objects.create(code="420001", name="B", center="42")
        vehicle = Vehicle.objects.create(chassis_number="JOBTEST001", brand="Test", model="Car", year_of_manufacture=2020, category="putnicko")
        for unit, assigned in [(a, date(2026, 1, 1)), (b, date(2026, 2, 15)), (a, date(2026, 2, 25))]:
            JobCode.objects.create(vehicle=vehicle, organizational_unit=unit, assigned_date=assigned)
        rows = assigned_vehicles("410001", date(2026, 2, 1), date(2026, 2, 28))
        self.assertEqual([(r["from"], r["to"]) for r in rows], [
            (date(2026, 2, 1), date(2026, 2, 14)), (date(2026, 2, 25), date(2026, 2, 28)),
        ])
        self.assertEqual(assigned_vehicles("420001", date(2026, 3, 1), date(2026, 3, 31)), [])

    def make_custody(self):
        employee = Employee.objects.create(employee_code=9001, first_name="Test", last_name="Person",
            position="Test", department_code=41, gender="M", date_of_birth=date(1980, 1, 1),
            date_of_joining=date(2020, 1, 1))
        vehicle = Vehicle.objects.create(chassis_number="CUSTODY001", brand="Test", model="Car",
                                        year_of_manufacture=2020, category="putnicko")
        a = OrganizationalUnit.objects.create(code="410001", name="A", center="41")
        b = OrganizationalUnit.objects.create(code="420001", name="B", center="42")
        for unit, assigned in [(a, date(2026, 1, 1)), (b, date(2026, 2, 15)), (a, date(2026, 2, 25))]:
            JobCode.objects.create(vehicle=vehicle, organizational_unit=unit, assigned_date=assigned)
        return VehicleTravelOrder.objects.create(employee=employee, vehicle=vehicle,
            created_at=date(2026, 1, 20), closed_at=date(2026, 2, 26))

    def test_custody_intersects_job_history_and_period_and_splits_return(self):
        order = self.make_custody()
        rows = self.get_table("custody").json()["data"]
        self.assertEqual([(r[6]["sort"], r[7]["sort"]) for r in rows], [
            ("2026-02-01", "2026-02-14"), ("2026-02-25", "2026-02-26")])
        self.assertEqual(rows[0][0]["sort"], "2026-01-20")
        self.assertIn("9001", rows[0][4]["sort"])
        self.assertEqual(rows[0][8]["sort"], "Zatvoreno")
        self.assertEqual(self.get_table("custody", month=3).json()["data"], [])
        order.closed_at = None
        order.save()
        rows = self.get_table("custody", month="").json()["data"]
        self.assertEqual(rows[-1][7]["sort"], "2026-12-31")
        self.assertEqual(rows[-1][8]["sort"], "Otvoreno")

    def test_custody_preserves_source_visibility(self):
        self.make_custody()
        with patch("fleet.views.vehicle_travel_orders._vehicle_travel_order_base_qs",
                   return_value=VehicleTravelOrder.objects.none()):
            self.assertEqual(self.get_table("custody").json()["data"], [])

    def test_custody_requires_both_permissions(self):
        user = get_user_model().objects.create_user("custody-limited", allowed_center_codes="41")
        role = Role.objects.create(name="Custody viewer", slug="custody-viewer")
        role.permissions.add(PermissionCode.objects.create(code="finansije:dashboard"),
                             PermissionCode.objects.create(code="vehicle_travel_order_list"))
        user.roles.add(role)
        self.client.force_login(user)
        self.assertEqual(self.get_table("custody").status_code, 403)
        role.permissions.add(PermissionCode.objects.create(code="jobcode_list"))
        self.assertEqual(self.get_table("custody").status_code, 200)

    def test_employees_are_background_loaded_scoped_and_counted_once_for_year(self):
        with patch("finansije.services.job_tables.payroll_employees", return_value={"rows": [
            (1, 12, "<script>name</script>", 2), (2, 12, "<script>name</script>", 1),
            (2, 13, "Another", 1),
        ], "closed_months": [1, 2], "open_months": [3]}) as source:
            self.assertContains(self.get_card(), 'id="JobEmployees"')
            source.assert_not_called()
            response = self.get_table("employees", month="")
            source.assert_called_once_with(1, "410001", date(2026, 1, 1), date(2026, 12, 31))
            data = response.json()
            self.assertEqual(data["footer"]["employee_count"], "2")
            self.assertEqual(data["data"][0][0]["sort"], "2026-01-01")
            self.assertIn("&lt;script&gt;", data["data"][0][2]["display"])
            self.assertEqual(data["data"][0][3]["sort"], "2")
            self.assertIn("Nepotpun obuhvat", data["footer"]["payroll_coverage"])
            self.assertIn("Otvoreni obračuni", data["footer"]["payroll_coverage"])

    def test_missing_payroll_runs_are_not_zero_employees(self):
        with patch("finansije.services.job_tables.payroll_employees", return_value={
                "rows": [], "closed_months": [], "open_months": [2]}):
            data = self.get_table("employees").json()
            self.assertEqual(data["footer"]["employee_count"], "—")
            self.assertIn("Broj zaposlenih nije potvrđen", data["footer"]["payroll_coverage"])

    def test_employee_source_failure_does_not_hide_finance_or_expose_database_details(self):
        with patch("finansije.services.job_tables.payroll_employees", side_effect=DatabaseError("private detail")):
            self.assertEqual(self.get_card().status_code, 200)
            with self.assertLogs("finansije.views", level="ERROR"):
                response = self.get_table("employees")
            self.assertEqual(response.status_code, 503)
            self.assertNotContains(response, "private detail", status_code=503)

    def test_job_table_links_open_card_for_last_month_of_report(self):
        response = self.client.get(reverse("finansije:report"), {"group": "job", "include_empty": "1", "date_from": "2026-01-01", "date_to": "2026-02-28"})
        self.assertContains(response, "/finansije/posao/?job=410001&amp;year=2026&amp;month=2")

    def test_ledger_links_use_posting_month_and_are_escaped(self):
        save_entry()
        response = self.client.get(reverse("finansije:ledger"), {
            "date_from": "2026-01-01", "date_to": "2026-12-31", "draw": 1,
        })
        cell = response.json()["data"][0][3]
        self.assertIn('/finansije/posao/?job=410001&amp;year=2026&amp;month=2', cell)
        self.assertIn('title="Detalj šifre posla"', cell)

    def test_month_rows_and_account_report_link_to_job_detail(self):
        save_entry()
        params = {"job": "410001", "date_from": "2026-01-01", "date_to": "2026-03-31"}
        response = self.client.get(reverse("finansije:report"), {**params, "group": "month"})
        self.assertEqual(response.context["rows"][0]["card_url"], "/finansije/posao/?job=410001&year=2026&month=2")
        response = self.client.get(reverse("finansije:report"), {**params, "group": "account"})
        self.assertContains(response, "Detalj šifre 410001")
        self.assertEqual(response.context["job_detail_url"], "/finansije/posao/?job=410001&year=2026&month=3")

    def test_travel_orders_use_travel_month_job_scope_and_exclude_cancellations(self):
        a = OrganizationalUnit.objects.create(code="410001", name="A", center="41")
        b = OrganizationalUnit.objects.create(code="420001", name="B", center="42")
        base = {"job_code": a, "order_date": date(2026, 1, 31), "travel_date": date(2026, 2, 1),
                "travel_location": "Test", "task": "Test", "number_of_days": 1, "advance_payment": Decimal("0")}
        for number, changes in enumerate(({}, {"job_code": b}, {"travel_date": date(2026, 3, 1)}, {"storniran": True}), 1):
            PutniNalog.objects.create(order_number=f"PN/2026-{number}", **{**base, **changes})
        rows = self.get_table("travel").json()["data"]
        self.assertEqual([r[1]["sort"] for r in rows], ["PN/2026-1"])
        self.assertEqual(rows[0][0]["sort"], "2026-02-01")

    def test_initial_page_does_not_load_any_table_data(self):
        with patch("finansije.services.job_tables.monthly_invoices", side_effect=AssertionError("eager invoices")), \
                patch("finansije.services.job_tables.monthly_expenses", side_effect=AssertionError("eager expenses")), \
                patch("finansije.services.job_tables.assigned_vehicles", side_effect=AssertionError("eager vehicles")), \
                patch("fleet.views.putni_nalozi._putninalog_base_qs", side_effect=AssertionError("eager travel")):
            response = self.get_card()
        self.assertEqual(response.status_code, 200)
        self.collections_mock.assert_not_called()
        self.assertContains(response, "data-ajax-source=", count=8)
        self.assertContains(response, "<tbody></tbody>", count=8)
        self.assertContains(response, 'id="JobInternalInvoices"')
        self.assertNotContains(response, "Čeka se pomoćna tabela")

    def test_ajax_rechecks_scope_and_module_permissions_on_every_request(self):
        user = get_user_model().objects.create_user("ajax-limited", allowed_center_codes="41")
        role = Role.objects.create(name="Ajax viewer", slug="ajax-viewer")
        role.permissions.add(PermissionCode.objects.create(code="finansije:dashboard"))
        user.roles.add(role)
        self.client.force_login(user)
        for table in ("invoices", "internal_invoices", "expenses", "vehicles", "custody", "employees", "travel", "collections", "shared", "cash"):
            self.assertEqual(self.get_table(table, job="420001").status_code, 404)
        for table in ("vehicles", "custody", "employees", "travel", "collections"):
            self.assertEqual(self.get_table(table).status_code, 403)
        self.assertEqual(self.get_table("invoices").status_code, 200)
        self.assertEqual(self.get_table("internal_invoices").status_code, 200)
        self.collections_mock.assert_not_called()
        user.roles.clear()
        self.assertEqual(self.get_table("invoices").status_code, 403)
        self.assertEqual(self.get_table("internal_invoices").status_code, 403)

    def test_ajax_rejects_invalid_periods_and_unknown_tables(self):
        self.assertEqual(self.get_table("bad").status_code, 404)
        for table in ("invoices", "internal_invoices", "expenses", "vehicles", "custody", "employees", "travel", "collections", "shared", "cash"):
            self.assertEqual(self.get_table(table, month=13).status_code, 400)
            self.assertEqual(self.get_table(table, job="").status_code, 400)
        self.collections_mock.assert_not_called()

    def test_ajax_escapes_source_text_and_keeps_raw_sort_values(self):
        save_entry(document_date=date(2026, 2, 9), partner_name='<img src=x onerror="bad()">',
                   document_reference='<script>bad</script>', account="20400", debit=Decimal("-1200.50"), credit=Decimal("0"))
        response = self.get_table("invoices")
        row = response.json()["data"][0]
        self.assertNotIn("<script>", row[1]["display"])
        self.assertIn("&lt;script&gt;", row[1]["display"])
        self.assertNotIn("<img", row[3]["display"])
        self.assertEqual(Decimal(row[4]["sort"]), Decimal("-1200.50"))
        self.assertEqual(row[0]["sort"], "2026-02-09")
        self.assertIn("09.02.2026.", row[0]["filter"])
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_blank_month_covers_whole_year_and_ajax_keeps_blank_month(self):
        save_entry(document_date=date(2026, 2, 9))
        save_entry(number=2, booking_date=date(2026, 8, 1), document_date=date(2026, 8, 1))
        save_entry(line_number=2, account="20400", debit=Decimal("120"), credit=Decimal("0"), document_date=date(2026, 2, 9))
        save_entry(number=2, line_number=2, account="20400", debit=Decimal("120"), credit=Decimal("0"), document_date=date(2026, 8, 1))
        response = self.get_card(month="")
        self.assertEqual(response.context["period_from"], date(2026, 1, 1))
        self.assertEqual(response.context["period_to"], date(2026, 12, 31))
        self.assertEqual(response.context["totals"]["revenue"], Decimal("200"))
        self.assertContains(response, "Cela godina")
        for url in response.context["table_urls"].values():
            self.assertTrue(url.endswith("month="))
        self.assertEqual(len(self.get_table("invoices", month="").json()["data"]), 2)

    def test_shared_cost_uses_company_pool_but_only_returns_authorized_job_allocation(self):
        save_entry()
        save_entry(number=2, job_code="pool", center="3", account="55000", debit=Decimal("1000"), credit=Decimal("0"))
        from .test_shared_costs import rule
        with patch("finansije.services.shared_costs.allocation_rules", return_value=(
                [rule("pool", month=2, criterion="1"), rule("410001", month=2)],
                (Decimal("40"), Decimal("0"), Decimal("0")))) as source:
            response = self.get_table("shared")
        self.assertEqual(response.status_code, 200)
        source.assert_called_once_with(1, 2026, 2, 2, "410001")
        self.assertIn("100", response.json()["metrics"]["shared_cost"])
        self.assertIn("finance-amount-negative", response.json()["metrics"]["shared_cost"])
        self.assertIn("finance-amount-zero", response.json()["metrics"]["result_after_shared"])
        self.assertNotIn("pool", response.content.decode())

    def test_cash_metrics_load_separately_with_signed_outflow_for_month_and_year(self):
        values = {"available": True, "inflow": Decimal("100"), "outflow": Decimal("150"),
                  "net": Decimal("-50"), "note": "52nt"}
        with patch("finansije.services.job_tables.cash_flow", return_value=values) as calculate:
            page = self.get_card()
            calculate.assert_not_called()
            self.assertContains(page, "data-cash-source=")
            response = self.get_table("cash")
            calculate.assert_called_once_with(1, "410001", date(2026, 2, 1), date(2026, 2, 28))
            metrics = response.json()["metrics"]
            self.assertIn("finance-amount-positive", metrics["inflow"])
            self.assertIn("finance-amount-negative", metrics["outflow"])
            self.assertIn("finance-amount-negative", metrics["net_cash"])
            self.assertEqual(self.get_table("cash", month="").status_code, 200)
            calculate.assert_called_with(1, "410001", date(2026, 1, 1), date(2026, 12, 31))

    def test_cash_failure_is_isolated_and_missing_coverage_does_not_call_source(self):
        with patch("finansije.services.job_tables.cash_flow", side_effect=DatabaseError("private database detail")) as calculate:
            self.assertEqual(self.get_card().status_code, 200)
            calculate.assert_not_called()
            with self.assertLogs("finansije.views", level="ERROR"):
                response = self.get_table("cash")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("private database detail", response.content.decode())
            calculate.reset_mock()
            SyncRun.objects.all().delete()
            self.assertEqual(self.get_table("cash").status_code, 409)
            calculate.assert_not_called()

    def test_cash_unavailable_and_partial_month_evidence(self):
        with patch("finansije.services.job_tables.cash_flow", return_value={"available": False, "note": "Inactive"}):
            self.assertEqual(set(self.get_table("cash").json()["metrics"].values()), {"Nema podataka"})
        with patch("finansije.services.job_tables.cash_flow", return_value={"available": True, "inflow": Decimal("0"),
                "outflow": Decimal("0"), "net": Decimal("0"), "note": "Partial", "complete": False}):
            response = self.get_table("cash")
            self.assertFalse(response.json()["complete"])
            self.assertIn("finance-amount-zero", response.json()["metrics"]["net_cash"])
