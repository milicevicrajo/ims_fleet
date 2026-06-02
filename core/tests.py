from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase
from openpyxl import load_workbook

from .exporting import (
    csv_attachment_response,
    dataframe_xlsx_response,
    rows_to_xlsx_response,
    xlsx_attachment_response,
)
from .mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from .models import CustomUser, OrganizationalUnit, PermissionCode, Role, RolePermission


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


class OrganizationalUnitLocationTests(SimpleTestCase):
    def test_organizational_unit_keeps_fleet_app_label(self):
        self.assertEqual(OrganizationalUnit._meta.app_label, "fleet")

    def test_organizational_unit_is_reexported_from_fleet_models(self):
        from fleet.models import OrganizationalUnit as FleetOrganizationalUnit

        self.assertIs(FleetOrganizationalUnit, OrganizationalUnit)


class FleetAuthModelLocationTests(SimpleTestCase):
    def test_fleet_auth_models_keep_fleet_app_label(self):
        self.assertEqual(CustomUser._meta.app_label, "fleet")
        self.assertEqual(Role._meta.app_label, "fleet")
        self.assertEqual(PermissionCode._meta.app_label, "fleet")
        self.assertEqual(RolePermission._meta.app_label, "fleet")

    def test_fleet_auth_models_are_reexported_from_fleet_models(self):
        from fleet.models import (
            CustomUser as FleetCustomUser,
            PermissionCode as FleetPermissionCode,
            Role as FleetRole,
            RolePermission as FleetRolePermission,
        )

        self.assertIs(FleetCustomUser, CustomUser)
        self.assertIs(FleetRole, Role)
        self.assertIs(FleetPermissionCode, PermissionCode)
        self.assertIs(FleetRolePermission, RolePermission)
