import datetime
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from core.models import PermissionCode, Role
from fleet.models import Employee
from mobilni.forms.mobile import MobileParkingExemptionForm
from mobilni.models import MobileAssignment, MobilePackage, MobileParkingExemption, MobileUsage, MobileUser
from mobilni.support.mobile import import_assignments
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
        employee = self.create_employee(employee_code, is_active=employee_active)
        MobileUser.objects.update_or_create(
            employee_code=employee_code,
            defaults={
                "full_name": f"Radnik {employee_code}",
                "is_active": employee_active,
                "departure_date": departure_date,
                "employee": employee,
            },
        )
        assignment = MobileAssignment.objects.create(
            year=2026,
            month=6,
            phone_number=phone_number,
            package=package,
            employee=employee,
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

    def create_employee(self, employee_code, *, is_active=True):
        employee, _ = Employee.objects.update_or_create(
            employee_code=employee_code,
            defaults={
                "first_name": f"Radnik {employee_code}",
                "last_name": "",
                "position": "Referent",
                "department_code": 1,
                "org_unit_code": "1",
                "gender": "M",
                "date_of_birth": datetime.date(1990, 1, 1),
                "date_of_joining": datetime.date(2026, 1, 1),
                "personal_number": f"0101990{employee_code:06d}"[:13],
                "is_active": is_active,
            },
        )
        return employee

    def grant_permission(self, user, code):
        permission = PermissionCode.objects.create(code=code)
        role = Role.objects.create(name=f"Role {code}", slug=code.replace(":", "-"))
        role.permissions.add(permission)
        user.roles.add(role)

    def test_calculate_withholding_matches_source_view_formula(self):
        usage = self.create_usage()

        self.assertEqual(calculate_withholding(usage), Decimal("75.00"))

    def test_calculate_withholding_applies_parking_exemption_by_phone_number(self):
        MobileParkingExemption.objects.create(phone_number="381631111111")
        parking_exempt = self.create_usage(employee_code=999, phone_number="381631111111")

        self.assertEqual(calculate_withholding(parking_exempt), Decimal("55.00"))

    def test_calculate_withholding_applies_parking_exemption_while_number_exists(self):
        MobileParkingExemption.objects.create(phone_number="381 63 111 1111")
        usage = self.create_usage(employee_code=999, phone_number="381631111111")

        self.assertEqual(calculate_withholding(usage), Decimal("55.00"))

    def test_calculate_withholding_applies_special_phone_exception(self):
        special_phone = self.create_usage(employee_code=501, phone_number="381637781481")

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
        usage.assignment.employee = None
        usage.assignment.save(update_fields=["employee"])

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
        self.assertContains(response, "Obustava = osnovica za PDV - neto iznos paketa + parking + NZRD")
        self.assertContains(response, "381637781481")
        self.assertContains(response, "Šifra radnika")

    def test_withholding_report_page_uses_phone_filter(self):
        self.create_usage(employee_code=500, phone_number="381631111111")
        self.create_usage(employee_code=501, phone_number="381632222222")
        MobileParkingExemption.objects.create(phone_number="381631111111")
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
        self.assertContains(response, "Parking izuzet")
        self.assertContains(response, "Ne ide u obustavu")
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
        MobileParkingExemption.objects.create(phone_number="381631111111")
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
        self.assertContains(response, "Parking izuzet")
        self.assertContains(response, "Ne ide u obustavu")
        self.assertNotContains(response, "381632222222")

    def test_assignment_page_marks_parking_exempt_numbers(self):
        self.create_usage(employee_code=500, phone_number="381631111111")
        MobileParkingExemption.objects.create(phone_number="381631111111")
        user = get_user_model().objects.create_user("assignment-list", password="test")
        self.grant_permission(user, "mobilni:mobile_assignment_list")
        self.client.force_login(user)

        response = self.client.get(
            reverse("mobilni:mobile_assignment_list"),
            {"year": 2026, "month": 6},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "381631111111")
        self.assertContains(response, "Parking izuzet")

    def test_parking_exemption_form_uses_only_phone_number(self):
        self.create_usage(employee_code=500, phone_number="381631111111")
        form = MobileParkingExemptionForm(data={"phone_number": "381 63 111 1111"})
        choices = dict(MobileParkingExemptionForm().fields["phone_number"].widget.choices)

        self.assertTrue(form.is_valid())
        self.assertEqual(list(form.fields), ["phone_number"])
        self.assertEqual(form.cleaned_data["phone_number"], "381631111111")
        self.assertIn("select2-method", form.fields["phone_number"].widget.attrs["class"])
        self.assertIn("381631111111", choices)
        self.assertIn("Radnik 500", choices["381631111111"])

    def test_parking_exemption_page_renders_configured_numbers(self):
        MobileParkingExemption.objects.create(phone_number="381631111111")
        user = get_user_model().objects.create_user("parking-exemption-list", password="test")
        self.grant_permission(user, "mobilni:mobile_parking_exemption_list")
        self.client.force_login(user)

        response = self.client.get(reverse("mobilni:mobile_parking_exemption_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Izuzeci parkinga")
        self.assertContains(response, "381631111111")
        self.assertContains(response, "Parking izuzet")
        self.assertContains(response, "Parking se ne obracunava za obustavu")

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
        self.assertIn("Parking izuzet", rows[0])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][6], "381631111111")
        self.assertEqual(rows[1][7], "Ne")
        self.assertEqual(rows[1][-1], 75)

    def test_dashboard_calculates_package_and_institute_totals(self):
        self.create_usage(
            employee_code=500,
            phone_number="381631111111",
            total=Decimal("200.00"),
        )
        MobileParkingExemption.objects.create(phone_number="381631111111")
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
        self.assertContains(response, "Parking izuzet")
        self.assertEqual(response.context["usage_total"], Decimal("380.00"))
        self.assertEqual(response.context["withholding_total"], Decimal("85.00"))
        self.assertEqual(response.context["institute_total"], Decimal("295.00"))
        self.assertEqual(response.context["active_number_count"], 2)
        self.assertEqual(response.context["contracted_number_count"], 2)
        self.assertEqual(response.context["package_summary"][0]["number_count"], 2)

    def test_import_assignments_links_existing_employee_and_package(self):
        employee = self.create_employee(700)
        uploaded_file = SimpleUploadedFile(
            "dodele.csv",
            b"broj;paket;rasif\n381 63 999 9999;Paket 1;700\n",
            content_type="text/csv",
        )

        result = import_assignments(uploaded_file, year=2026, month=6)

        assignment = MobileAssignment.objects.get(phone_number="381639999999")
        self.assertEqual(result.imported, 1)
        self.assertEqual(result.updated, 0)
        self.assertEqual(assignment.employee, employee)
        self.assertEqual(assignment.package, self.package)

    def test_import_assignments_skips_row_without_existing_links(self):
        uploaded_file = SimpleUploadedFile(
            "dodele.csv",
            b"broj;paket;rasif\n381639999998;Nepostojeci;9999\n381639999997;Paket 1;9999\n",
            content_type="text/csv",
        )

        result = import_assignments(uploaded_file, year=2026, month=6)

        self.assertEqual(result.skipped, 2)
        self.assertFalse(MobileAssignment.objects.exists())
        self.assertIn("paket 'Nepostojeci' nije pronadjen", result.errors[0])
        self.assertIn("radnik '9999' nije pronadjen", result.errors[1])
