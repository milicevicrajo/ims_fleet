import datetime

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Employee, EmployeeCVItem


class HrAppTests(SimpleTestCase):
    def test_hr_app_imports(self):
        import hr

        self.assertIsNotNone(hr)

    def test_employee_form_and_views_import(self):
        from .forms import EmployeeForm
        from .models import Employee
        from .views import EmployeeListView

        self.assertIsNotNone(Employee)
        self.assertIsNotNone(EmployeeForm)
        self.assertIsNotNone(EmployeeListView)

    def test_hr_sync_backward_compatible_import(self):
        from fleet.models import Employee as FleetEmployee
        from fleet.sync.hr import sync_employees_from_hr_view as fleet_sync
        from .models import Employee as HrEmployee
        from .sync import sync_employees_from_hr_view as hr_sync

        self.assertIs(FleetEmployee, HrEmployee)
        self.assertIs(fleet_sync, hr_sync)

    def test_employee_command_aliases_are_available(self):
        from fleet.management.commands.fetch_employee_data import Command as FetchCommand
        from hr.management.commands.fetch_employee_data import Command as HrFetchCommand
        from fleet.management.commands.sync_hr_employees import Command as FleetSyncHrCommand
        from hr.management.commands.sync_hr_employees import Command as HrSyncHrCommand
        from fleet.management.commands.sync_employees import Command as SyncCommand
        from hr.querysets import employee_list_queryset, employees_for_travel_orders
        from hr.management.commands.sync_employees import Command as HrSyncCommand

        self.assertIn("sync_hr_employees", FetchCommand.help)
        self.assertIn("sync_hr_employees", SyncCommand.help)
        self.assertTrue(issubclass(FetchCommand, HrFetchCommand))
        self.assertTrue(issubclass(FleetSyncHrCommand, HrSyncHrCommand))
        self.assertTrue(issubclass(SyncCommand, HrSyncCommand))
        self.assertIsNotNone(employee_list_queryset)
        self.assertIsNotNone(employees_for_travel_orders)


@override_settings(ALLOWED_HOSTS=["testserver"])
class MyEmployeeProfileTests(TestCase):
    def create_employee(self, code, first_name="Petar", last_name="Petrovic"):
        return Employee.objects.create(
            employee_code=code,
            first_name=first_name,
            last_name=last_name,
            position="Inzenjer",
            department_code=1,
            gender="M",
            date_of_birth=datetime.date(1990, 1, 1),
            date_of_joining=datetime.date(2020, 1, 1),
        )

    def test_linked_user_can_open_own_profile(self):
        employee = self.create_employee(100)
        user = get_user_model().objects.create_user("petar", password="test", employee=employee)
        self.client.force_login(user)

        response = self.client.get(reverse("my_employee_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Radna biografija")
        self.assertEqual(response.context["employee"], employee)

    def test_unlinked_user_gets_explanation(self):
        user = get_user_model().objects.create_user("bezprofila", password="test")
        self.client.force_login(user)

        response = self.client.get(reverse("my_employee_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "jos nije povezan")

    def test_cv_item_is_created_for_logged_in_employee(self):
        employee = self.create_employee(101)
        user = get_user_model().objects.create_user("cvuser", password="test", employee=employee)
        self.client.force_login(user)

        response = self.client.post(
            reverse("employee_cv_item_create"),
            {
                "title": "ERP projekat",
                "organization": "IMS",
                "role": "Analiticar",
                "description": "Implementacija procesa.",
                "skills": "Django",
            },
        )

        self.assertRedirects(response, f"{reverse('my_employee_profile')}#cv")
        self.assertTrue(EmployeeCVItem.objects.filter(employee=employee, title="ERP projekat").exists())

    def test_user_cannot_edit_another_employee_cv_item(self):
        employee = self.create_employee(102)
        other_employee = self.create_employee(103, first_name="Milan")
        user = get_user_model().objects.create_user("owner", password="test", employee=employee)
        item = EmployeeCVItem.objects.create(
            employee=other_employee,
            title="Tudja stavka",
            description="Ne sme da se menja.",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("employee_cv_item_update", args=[item.pk]))

        self.assertEqual(response.status_code, 404)

    def test_regular_user_cannot_open_employee_list(self):
        employee = self.create_employee(104)
        user = get_user_model().objects.create_user("regular", password="test", employee=employee)
        self.client.force_login(user)

        response = self.client.get(reverse("employee_list"))

        self.assertEqual(response.status_code, 403)

    def test_contracts_are_linked_through_employee_partner_code(self):
        from ugovori.models import Contract, ContractParty, ContractType, Partner

        employee = self.create_employee(105)
        user = get_user_model().objects.create_user("ugovori", password="test", employee=employee)
        contract_type = ContractType.objects.create(code="RAD", name="Radni odnos")
        employee_partner = Partner.objects.create(
            name="Petar Petrovic",
            external_sif_par=employee.employee_code,
        )
        employee_contract = Contract.objects.create(
            contract_type=contract_type,
            contract_number="UG-EMPLOYEE",
            title="Ugovor zaposlenog",
            contract_date=datetime.date(2026, 1, 1),
        )
        ContractParty.objects.create(
            contract=employee_contract,
            partner=employee_partner,
            role="ostalo",
        )
        unrelated_contract = Contract.objects.create(
            contract_type=contract_type,
            contract_number="UG-CREATED-BY",
            title="Ugovor koji je korisnik samo uneo",
            contract_date=datetime.date(2026, 1, 2),
            created_by=user,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("my_employee_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(employee_contract, response.context["contracts"])
        self.assertNotIn(unrelated_contract, response.context["contracts"])
        self.assertNotIn("Ugovor", [item["category"] for item in response.context["activities"]])

    def test_user_can_correct_only_own_name_diacritics(self):
        employee = self.create_employee(106, last_name="Petrovic")
        user = get_user_model().objects.create_user("dijakritika", password="test", employee=employee)
        self.client.force_login(user)

        response = self.client.post(
            reverse("my_employee_name_correction"),
            {
                "display_first_name_override": "Petar",
                "display_last_name_override": "Petrović",
            },
        )

        self.assertRedirects(response, reverse("my_employee_profile"))
        employee.refresh_from_db()
        self.assertEqual(employee.last_name, "Petrovic")
        self.assertEqual(employee.display_last_name, "Petrović")

    def test_user_cannot_change_name_letters(self):
        employee = self.create_employee(107, last_name="Petrovic")
        user = get_user_model().objects.create_user("slova", password="test", employee=employee)
        self.client.force_login(user)

        response = self.client.post(
            reverse("my_employee_name_correction"),
            {
                "display_first_name_override": "Petar",
                "display_last_name_override": "Petrovski",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mozes promeniti samo dijakritike")
        employee.refresh_from_db()
        self.assertEqual(employee.display_last_name_override, "")

    def test_hr_source_update_does_not_overwrite_display_name_override(self):
        employee = self.create_employee(108, last_name="Petrovic")
        employee.display_last_name_override = "Petrović"
        employee.save(update_fields=["display_last_name_override"])

        Employee.objects.update_or_create(
            employee_code=employee.employee_code,
            defaults={"last_name": "PETROVIC"},
        )

        employee.refresh_from_db()
        self.assertEqual(employee.last_name, "PETROVIC")
        self.assertEqual(employee.display_last_name, "Petrović")
