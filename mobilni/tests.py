import datetime
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from core.models import PermissionCode, Role
from mobilni.models import MobileAssignment, MobilePackage, MobileUsage, MobileUser
from mobilni.withholdings import (
    REPORT_ALL,
    REPORT_EMPLOYEES,
    REPORT_FORMER_EMPLOYEES,
    calculate_withholding,
    get_withholding_rows,
)
from ugovori.models import Contract, ContractType


class MobilePermissionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("mobile-test", password="test")
        self.client.force_login(self.user)

    def test_mobile_dashboard_requires_mobile_permission(self):
        response = self.client.get(reverse("mobilni:mobile_dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_mobile_role_can_open_dashboard(self):
        permission = PermissionCode.objects.create(code="mobilni:mobile_dashboard")
        role = Role.objects.create(name="Mobilni", slug="mobilni")
        role.permissions.add(permission)
        self.user.roles.add(role)

        response = self.client.get(reverse("mobilni:mobile_dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_mobile_export_requires_its_permission(self):
        response = self.client.get(reverse("mobilni:mobile_assignment_export"))

        self.assertEqual(response.status_code, 403)

    def test_contract_delete_unlinks_mobile_packages_before_delete(self):
        contract_type = ContractType.objects.create(name="Mobilna telefonija")
        contract = Contract.objects.create(
            contract_type=contract_type,
            contract_number="20-test",
            title="Test ugovor",
            contract_date=datetime.date(2026, 1, 1),
        )
        package = MobilePackage.objects.create(name="Test paket", contract=contract)
        permission = PermissionCode.objects.create(code="ugovori:contract_delete")
        role = Role.objects.create(name="Brisanje ugovora", slug="brisanje-ugovora")
        role.permissions.add(permission)
        self.user.roles.add(role)

        response = self.client.post(reverse("ugovori:contract_delete", args=[contract.pk]))

        self.assertRedirects(
            response,
            reverse("ugovori:contract_list"),
            fetch_redirect_response=False,
        )
        self.assertFalse(Contract.objects.filter(pk=contract.pk).exists())
        package.refresh_from_db()
        self.assertIsNone(package.contract_id)


class MobileWithholdingTests(TestCase):
    def setUp(self):
        self.package = MobilePackage.objects.create(
            partner_code="1",
            partner_name="MTS",
            name="Paket 1",
            net_amount=Decimal("100.00"),
        )

    def create_usage(
        self,
        *,
        employee_code=500,
        phone_number="381631234567",
        employee_active=True,
        departure_date=None,
        vat_base=Decimal("150.00"),
        parking=Decimal("20.00"),
        nzrd=Decimal("5.00"),
        total=Decimal("200.00"),
        package=None,
    ):
        package = package or self.package
        mobile_user = MobileUser.objects.create(
            employee_code=employee_code,
            full_name=f"Radnik {employee_code}",
            is_active=employee_active,
            departure_date=departure_date,
        )
        assignment = MobileAssignment.objects.create(
            year=2026,
            month=6,
            phone_number=phone_number,
            package=package,
            package_name=package.name,
            package_net_amount=package.net_amount,
            mobile_user=mobile_user,
            employee_code=employee_code,
            employee_name=mobile_user.full_name,
            employee_active=employee_active,
        )
        return MobileUsage.objects.create(
            year=2026,
            month=6,
            phone_number=phone_number,
            assignment=assignment,
            vat_base=vat_base,
            parking=parking,
            nzrd=nzrd,
            total=total,
        )

    def grant_permission(self, user, code):
        permission = PermissionCode.objects.create(code=code)
        role = Role.objects.create(name=f"Role {code}", slug=code.replace(":", "-"))
        role.permissions.add(permission)
        user.roles.add(role)

    def test_calculate_withholding_matches_source_view_formula(self):
        usage = self.create_usage()

        self.assertEqual(calculate_withholding(usage), Decimal("75.00"))

    def test_calculate_withholding_applies_parking_and_phone_exceptions(self):
        parking_exempt = self.create_usage(employee_code=141, phone_number="381631111111")
        special_phone = self.create_usage(employee_code=501, phone_number="381637781481")

        self.assertEqual(calculate_withholding(parking_exempt), Decimal("55.00"))
        self.assertEqual(calculate_withholding(special_phone), Decimal("175.00"))

    def test_reports_separate_current_and_former_employees(self):
        active = self.create_usage(employee_code=500, phone_number="381631111111")
        former = self.create_usage(
            employee_code=501,
            phone_number="381632222222",
            employee_active=False,
            departure_date=datetime.date(2026, 5, 31),
        )
        self.create_usage(
            employee_code=502,
            phone_number="381633333333",
            employee_active=False,
            departure_date=datetime.date(2026, 6, 30),
        )

        employee_rows = get_withholding_rows(REPORT_EMPLOYEES, year=2026, month=6)
        former_rows = get_withholding_rows(REPORT_FORMER_EMPLOYEES, year=2026, month=6)

        self.assertEqual([row.usage for row in employee_rows], [active])
        self.assertEqual([row.usage for row in former_rows], [former])

    def test_employee_report_excludes_unassigned_active_numbers(self):
        usage = self.create_usage()
        usage.assignment.employee_code = None
        usage.assignment.save(update_fields=["employee_code"])

        rows = get_withholding_rows(REPORT_EMPLOYEES, year=2026, month=6)

        self.assertEqual(rows, [])

    def test_employee_csv_contains_only_required_columns(self):
        self.create_usage()
        user = get_user_model().objects.create_user("withholding-export", password="test")
        self.grant_permission(user, "mobilni:mobile_withholding_employees_export")
        self.client.force_login(user)

        response = self.client.get(
            reverse("mobilni:mobile_withholding_employees_export"),
            {"year": 2026, "month": 6},
        )

        self.assertEqual(response.status_code, 200)
        lines = response.content.decode("utf-8-sig").splitlines()
        self.assertEqual(lines[0], "Godina;Mesec;Šifra radnika;Iznos obustave")
        self.assertEqual(lines[1], "2026;6;500;75.00")

    def test_usage_accounting_csv_uses_period_and_phone_filter(self):
        self.create_usage(employee_code=500, phone_number="381631111111")
        self.create_usage(employee_code=501, phone_number="381632222222")
        user = get_user_model().objects.create_user("usage-accounting-export", password="test")
        self.grant_permission(user, "mobilni:mobile_usage_accounting_csv")
        self.client.force_login(user)

        response = self.client.get(
            reverse("mobilni:mobile_usage_accounting_csv"),
            {"year": 2026, "month": 6, "phone_number": "1111"},
        )

        self.assertEqual(response.status_code, 200)
        lines = response.content.decode("utf-8-sig").splitlines()
        self.assertEqual(lines[0], "Godina;Mesec;Šifra radnika;Iznos obustave")
        self.assertEqual(lines[1], "2026;6;500;75.00")
        self.assertEqual(len(lines), 2)

    def test_employee_report_page_renders_calculated_row(self):
        self.create_usage()
        user = get_user_model().objects.create_user("withholding-report", password="test")
        self.grant_permission(user, "mobilni:mobile_withholding_employees")
        self.client.force_login(user)

        response = self.client.get(
            reverse("mobilni:mobile_withholding_employees"),
            {"year": 2026, "month": 6},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Radnik 500")
        self.assertContains(response, "75.00")
        self.assertContains(response, "Šifra radnika")

    def test_withholding_report_page_uses_phone_filter(self):
        self.create_usage(employee_code=500, phone_number="381631111111")
        self.create_usage(employee_code=501, phone_number="381632222222")
        user = get_user_model().objects.create_user("withholding-phone-filter", password="test")
        self.grant_permission(user, "mobilni:mobile_withholding_all")
        self.client.force_login(user)

        response = self.client.get(
            reverse("mobilni:mobile_withholding_all"),
            {"year": 2026, "month": 6, "phone_number": "1111"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="withholding-phone"')
        self.assertContains(response, "Broj telefona")
        self.assertContains(response, "381631111111")
        self.assertNotContains(response, "381632222222")
        self.assertEqual(response.context["phone_number"], "1111")

    def test_all_report_can_be_filtered_by_phone_employee_and_package(self):
        matching = self.create_usage(employee_code=500, phone_number="381631111111")
        other_package = MobilePackage.objects.create(
            partner_code="1",
            partner_name="MTS",
            name="Paket 2",
            net_amount=Decimal("50.00"),
        )
        self.create_usage(
            employee_code=501,
            phone_number="381632222222",
            package=other_package,
        )

        rows = get_withholding_rows(
            REPORT_ALL,
            year=2026,
            month=6,
            phone_number="1111",
            employee="Radnik 500",
            package_id=self.package.pk,
        )

        self.assertEqual([row.usage for row in rows], [matching])

    def test_usage_page_uses_phone_filter(self):
        self.create_usage(employee_code=500, phone_number="381631111111")
        self.create_usage(employee_code=501, phone_number="381632222222")
        user = get_user_model().objects.create_user("usage-list", password="test")
        self.grant_permission(user, "mobilni:mobile_usage_list")
        self.client.force_login(user)

        response = self.client.get(
            reverse("mobilni:mobile_usage_list"),
            {"year": 2026, "month": 6, "phone_number": "1111"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="usage-phone"')
        self.assertContains(response, "Broj telefona")
        self.assertContains(response, "Potrošnja mobilnih")
        self.assertContains(response, "Šifra radnika")
        self.assertEqual(len(response.context["usages"]), 1)
        self.assertContains(response, "381631111111")
        self.assertNotContains(response, "381632222222")

    def test_usage_excel_contains_obustava_and_respects_phone_filter(self):
        self.create_usage(employee_code=500, phone_number="381631111111")
        self.create_usage(employee_code=501, phone_number="381632222222")
        user = get_user_model().objects.create_user("usage-export", password="test")
        self.grant_permission(user, "mobilni:mobile_usage_export")
        self.client.force_login(user)

        response = self.client.get(
            reverse("mobilni:mobile_usage_export"),
            {"year": 2026, "month": 6, "phone_number": "1111"},
        )
        workbook = load_workbook(BytesIO(response.content), read_only=True)
        rows = list(workbook.active.iter_rows(values_only=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(workbook.active.title, "Potrošnja")
        self.assertIn("Šifra radnika", rows[0])
        self.assertEqual(rows[0][-1], "Obustava")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][6], "381631111111")
        self.assertEqual(rows[1][-1], 75)

    def test_dashboard_calculates_package_and_institute_totals(self):
        self.create_usage(
            employee_code=500,
            phone_number="381631111111",
            total=Decimal("200.00"),
        )
        self.create_usage(
            employee_code=501,
            phone_number="381632222222",
            vat_base=Decimal("130.00"),
            parking=Decimal("0.00"),
            nzrd=Decimal("0.00"),
            total=Decimal("180.00"),
        )
        user = get_user_model().objects.create_user("mobile-dashboard", password="test")
        self.grant_permission(user, "mobilni:mobile_dashboard")
        self.client.force_login(user)

        response = self.client.get(
            reverse("mobilni:mobile_dashboard"),
            {"year": 2026, "month": 6},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="mobile-phone"')
        self.assertContains(response, "Broj telefona")
        self.assertEqual(response.context["usage_total"], Decimal("380.00"))
        self.assertEqual(response.context["withholding_total"], Decimal("105.00"))
        self.assertEqual(response.context["institute_total"], Decimal("275.00"))
        self.assertEqual(response.context["active_number_count"], 2)
        self.assertEqual(response.context["contracted_number_count"], 2)
        self.assertEqual(response.context["package_summary"][0]["number_count"], 2)
