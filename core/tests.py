from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from openpyxl import load_workbook

from .exporting import (
    csv_attachment_response,
    dataframe_xlsx_response,
    rows_to_xlsx_response,
    xlsx_attachment_response,
)
from .mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from .models import ActivityLog, CustomUser, OrganizationalUnit, PermissionCode, Role, RolePermission


class ExportingTests(SimpleTestCase):
    def test_csv_attachment_response_sets_download_headers(self):
        response = csv_attachment_response("vozila.csv")

        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="vozila.csv"')

    def test_xlsx_attachment_response_sets_download_headers(self):
        response = xlsx_attachment_response("report.xlsx")

        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(response["Content-Disposition"], "attachment; filename=report.xlsx")

    def test_rows_to_xlsx_response_creates_valid_workbook(self):
        response = rows_to_xlsx_response(
            "report.xlsx",
            "Report",
            ["Name", "Value"],
            [["Alpha", 12]],
            bold_header=True,
            auto_width=True,
        )

        workbook = load_workbook(BytesIO(response.content))
        worksheet = workbook.active

        self.assertEqual(worksheet.title, "Report")
        self.assertEqual(worksheet["A1"].value, "Name")
        self.assertTrue(worksheet["A1"].font.bold)
        self.assertEqual(worksheet["A2"].value, "Alpha")
        self.assertEqual(worksheet["B2"].value, 12)

    def test_dataframe_xlsx_response_creates_valid_workbook(self):
        response = dataframe_xlsx_response(
            [{"Name": "Alpha", "Value": 12}],
            "data.xlsx",
            "Data",
        )

        workbook = load_workbook(BytesIO(response.content))
        worksheet = workbook.active

        self.assertEqual(worksheet.title, "Data")
        self.assertEqual(worksheet["A1"].value, "Name")
        self.assertEqual(worksheet["A2"].value, "Alpha")
        self.assertEqual(worksheet["B2"].value, 12)


class RolePermissionMixinTests(SimpleTestCase):
    def test_user_has_role_permission_returns_false_without_code(self):
        user = SimpleNamespace(is_authenticated=True, is_superuser=False, roles=Mock())

        self.assertFalse(user_has_role_permission(user, None))
        user.roles.filter.assert_not_called()

    def test_user_has_role_permission_uses_active_role_filter(self):
        filter_mock = Mock()
        filter_mock.exists.return_value = True
        roles = Mock()
        roles.filter.return_value = filter_mock
        user = SimpleNamespace(is_authenticated=True, is_superuser=False, roles=roles)

        self.assertTrue(user_has_role_permission(user, "fleet:vehicle_list"))
        roles.filter.assert_called_once_with(
            permissions__code="fleet:vehicle_list",
            is_active=True,
        )

    def test_role_permission_mixin_uses_resolver_match_view_name(self):
        filter_mock = Mock()
        filter_mock.exists.return_value = True
        roles = Mock()
        roles.filter.return_value = filter_mock
        user = SimpleNamespace(is_authenticated=True, is_superuser=False, roles=roles)
        request = SimpleNamespace(
            user=user,
            resolver_match=SimpleNamespace(view_name="naplata:lista_dugovanja"),
        )

        class TestMixin(RolePermissionRequiredMixin):
            def __init__(self, request):
                self.request = request

        self.assertTrue(TestMixin(request).test_func())
        roles.filter.assert_called_once_with(
            permissions__code="naplata:lista_dugovanja",
            is_active=True,
        )

    def test_role_permission_required_decorator_raises_without_permission(self):
        filter_mock = Mock()
        filter_mock.exists.return_value = False
        roles = Mock()
        roles.filter.return_value = filter_mock
        user = SimpleNamespace(is_authenticated=True, is_superuser=False, roles=roles)
        request = SimpleNamespace(
            user=user,
            resolver_match=SimpleNamespace(view_name="fleet:vehicle_list"),
        )

        @role_permission_required()
        def protected_view(request):
            return "ok"

        with self.assertRaises(PermissionDenied):
            protected_view(request)


class PermissionCodeSyncTests(TestCase):
    def test_sync_permission_codes_grants_employee_sync_to_sekretarijat(self):
        from .permissions import sync_permission_codes

        sync_permission_codes()

        role = Role.objects.get(slug="sekretarijat")
        codes = set(role.permissions.values_list("code", flat=True))
        self.assertIn("employee_list", codes)
        self.assertIn("employee_sync", codes)

    def test_sync_permission_codes_grants_isplate_permissions_to_blagajna(self):
        from .permissions import sync_permission_codes

        sync_permission_codes()

        role = Role.objects.get(slug="blagajna")
        codes = set(role.permissions.values_list("code", flat=True))
        self.assertIn("isplate:neoporezive_isplate", codes)
        self.assertIn("isplate:converter", codes)

    def test_sync_permission_codes_links_sekretarijat_group_users_to_role(self):
        from .permissions import sync_permission_codes

        group = Group.objects.create(name="Sekretarijat")
        user = get_user_model().objects.create_user("sekretar", password="test")
        user.groups.add(group)

        result = sync_permission_codes()

        self.assertEqual(result["sekretarijat_group_users_synced"], 1)
        self.assertTrue(user.roles.filter(slug="sekretarijat").exists())


class OrganizationalUnitLocationTests(SimpleTestCase):
    def test_organizational_unit_keeps_fleet_app_label(self):
        self.assertEqual(OrganizationalUnit._meta.app_label, "fleet")

    def test_organizational_unit_is_reexported_from_fleet_models(self):
        from fleet.models import OrganizationalUnit as FleetOrganizationalUnit

        self.assertIs(FleetOrganizationalUnit, OrganizationalUnit)


class FleetAuthModelLocationTests(SimpleTestCase):
    def test_fleet_auth_models_keep_fleet_app_label(self):
        self.assertEqual(ActivityLog._meta.app_label, "fleet")
        self.assertEqual(CustomUser._meta.app_label, "fleet")
        self.assertEqual(Role._meta.app_label, "fleet")
        self.assertEqual(PermissionCode._meta.app_label, "fleet")
        self.assertEqual(RolePermission._meta.app_label, "fleet")

    def test_fleet_auth_models_are_reexported_from_fleet_models(self):
        from fleet.models import (
            ActivityLog as FleetActivityLog,
            CustomUser as FleetCustomUser,
            PermissionCode as FleetPermissionCode,
            Role as FleetRole,
            RolePermission as FleetRolePermission,
        )

        self.assertIs(FleetActivityLog, ActivityLog)
        self.assertIs(FleetCustomUser, CustomUser)
        self.assertIs(FleetRole, Role)
        self.assertIs(FleetPermissionCode, PermissionCode)
        self.assertIs(FleetRolePermission, RolePermission)


class ActivityLogTests(TestCase):
    def test_log_activity_stores_actor_snapshot(self):
        from core.activity import log_activity

        user = get_user_model().objects.create_user(
            username="admin-test",
            first_name="Admin",
            last_name="Test",
            password="test",
        )

        log = log_activity(
            user=user,
            action=ActivityLog.ACTION_MANUAL,
            description="Test aktivnost",
            app_label="fleet",
            view_name="activity_log_list",
        )

        self.assertEqual(log.user, user)
        self.assertEqual(log.actor_username, "admin-test")
        self.assertEqual(log.actor_display_name, "Admin Test")
        self.assertEqual(log.description, "Test aktivnost")

    def test_activity_log_list_renders_for_superuser(self):
        user = get_user_model().objects.create_superuser(
            username="super-admin",
            email="admin@example.com",
            password="test-pass",
        )
        ActivityLog.objects.create(
            user=user,
            actor_username=user.username,
            action=ActivityLog.ACTION_MANUAL,
            description="Provera ekrana",
            app_label="fleet",
        )

        self.client.force_login(user)
        response = self.client.get(reverse("activity_log_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Provera ekrana")
