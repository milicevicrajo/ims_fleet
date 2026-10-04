from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import OrganizationalUnit, PermissionCode, Role
from hr.forms import EmployeeForm
from hr.models import Employee
from hr.sync import _preserve_locked_identity_fields


class EmployeeLocalEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employee = Employee.objects.create(
            employee_code=901, first_name="Petar", last_name="Petrovic", title="mr",
            position="Inženjer", department_code=430, org_unit_code="430", gender="M",
            date_of_birth=date(1990, 1, 1), date_of_joining=date(2020, 1, 1),
            phone_number="011123456", slava="Sveti Nikola",
        )
        cls.user = get_user_model().objects.create_user("hr-editor", password="test")
        role = Role.objects.create(name="HR editor", slug="hr-editor")
        role.permissions.add(PermissionCode.objects.get_or_create(code="employee_update")[0])
        cls.user.roles.add(role)
        cls.url = reverse("employee_update", args=[cls.employee.pk])

    def setUp(self):
        self.client.force_login(self.user)

    def data(self, **changes):
        data = {name: getattr(self.employee, name) or "" for name in EmployeeForm.LOCAL_EDIT_FIELDS}
        data.update(changes)
        return data

    def test_hr_values_are_visible_outside_form_and_not_inputs(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        form_start = html.index('id="ef-form"')
        self.assertGreater(html.index('id="employee-hr-data"'), html.index('</form>', form_start))
        self.assertContains(response, "011123456")
        self.assertContains(response, "Inženjer")
        for name in ("employee_code", "gender", "position", "phone_number", "org_unit_code", "is_active"):
            self.assertNotContains(response, f'name="{name}"')

    def test_each_identity_change_enables_sync_protection(self):
        for name, value in (("first_name", "Jovan"), ("last_name", "Petrović"), ("title", "dr")):
            with self.subTest(field=name):
                Employee.objects.filter(pk=self.employee.pk).update(skip_hr_identity_update=False)
                response = self.client.post(self.url, self.data(**{name: value}))
                self.assertEqual(response.status_code, 302)
                saved = Employee.objects.get(pk=self.employee.pk)
                self.assertEqual(getattr(saved, name), value)
                self.assertTrue(saved.skip_hr_identity_update)
                defaults = {"first_name": "Izvor", "last_name": "Izvor", "title": "prof", "position": "Novo mesto"}
                _preserve_locked_identity_fields(saved, defaults)
                Employee.objects.filter(pk=saved.pk).update(**defaults)
                saved.refresh_from_db()
                self.assertEqual(getattr(saved, name), value)
                self.assertEqual(saved.position, "Novo mesto")

    def test_crafted_post_cannot_change_hr_fields_or_disable_lock(self):
        Employee.objects.filter(pk=self.employee.pk).update(skip_hr_identity_update=True)
        response = self.client.post(self.url, self.data(
            employee_code=999, gender="F", position="Direktor", department_code=999,
            org_unit_code="999", phone_number="0", is_active="", original_full_name="Izmenjeno",
            date_of_birth="2000-01-01", skip_hr_identity_update="",
        ))
        self.assertEqual(response.status_code, 302)
        saved = Employee.objects.get(pk=self.employee.pk)
        for name in ("employee_code", "gender", "position", "department_code", "org_unit_code",
                     "phone_number", "is_active", "original_full_name", "date_of_birth"):
            self.assertEqual(getattr(saved, name), getattr(self.employee, name), name)
        self.assertTrue(saved.skip_hr_identity_update)

    def test_local_only_changes_do_not_enable_identity_lock(self):
        response = self.client.post(self.url, self.data(
            full_name_cyrillic="Петар Петровић", slava_datum="19.12.2026",
            display_last_name_override="Petrović",
        ))
        self.assertEqual(response.status_code, 302)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.skip_hr_identity_update)
        self.assertEqual(self.employee.full_name_cyrillic, "Петар Петровић")
        self.assertEqual(self.employee.slava_datum, date(2026, 12, 19))
        self.assertEqual(self.employee.display_last_name, "Petrović")

    def test_changed_name_is_not_masked_by_old_display_override(self):
        Employee.objects.filter(pk=self.employee.pk).update(display_first_name_override="Pétar")
        response = self.client.post(self.url, self.data(first_name="Jovan", display_first_name_override="Pétar"))
        self.assertEqual(response.status_code, 302)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.display_first_name, "Jovan")

    def test_save_does_not_overwrite_a_newer_hr_update(self):
        form = EmployeeForm(data=self.data(title="dr"), instance=self.employee, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        Employee.objects.filter(pk=self.employee.pk).update(position="Novo radno mesto")
        form.save()
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.position, "Novo radno mesto")

    def test_scoped_editor_can_save_without_posting_org_unit(self):
        unit = OrganizationalUnit.objects.create(code="430", center="43", name="Centar")
        self.user.allowed_centers.add(unit)
        response = self.client.post(self.url, self.data(title="dr"))
        self.assertEqual(response.status_code, 302)
        Employee.objects.filter(pk=self.employee.pk).update(org_unit_code="999", department_code=999)
        self.assertEqual(self.client.post(self.url, self.data(title="prof")).status_code, 404)

    def test_superuser_retains_full_form(self):
        admin = get_user_model().objects.create_superuser("hr-admin", password="test")
        form = EmployeeForm(instance=self.employee, user=admin)
        self.assertIn("org_unit_code", form.fields)
        self.assertIn("skip_hr_identity_update", form.fields)
        self.assertFalse(form.local_edit_only)

    def test_invalid_local_data_keeps_hr_summary_and_does_not_save_identity(self):
        response = self.client.post(self.url, self.data(first_name="Jovan", slava_datum="31.02.2026"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("slava_datum", response.context["form"].errors)
        self.assertContains(response, "011123456")
        self.assertContains(response, "Podaci iz kadrovske evidencije")
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.first_name, "Petar")
        self.assertFalse(self.employee.skip_hr_identity_update)

    def test_no_change_does_not_enable_identity_lock(self):
        self.assertEqual(self.client.post(self.url, self.data()).status_code, 302)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.skip_hr_identity_update)
