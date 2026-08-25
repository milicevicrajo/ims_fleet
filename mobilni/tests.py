import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import PermissionCode, Role
from mobilni.models import MobileAssignment, MobilePackage, MobileUsage, MobileUser
from mobilni.withholdings import (
    REPORT_EMPLOYEES,
    REPORT_FORMER_EMPLOYEES,
    calculate_withholding,
    get_withholding_rows,
)


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
    ):
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
            package=self.package,
            package_name=self.package.name,
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
        self.assertEqual(lines[0], "Godina;Mesec;Sifra radnika;Iznos obustave")
        self.assertEqual(lines[1], "2026;6;500;75.00")

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
