from django.test import SimpleTestCase


class HrAppTests(SimpleTestCase):
    def test_hr_app_imports(self):
        import hr

        self.assertIsNotNone(hr)

    def test_employee_form_and_views_import(self):
        from .forms import EmployeeForm
        from .views import EmployeeListView

        self.assertIsNotNone(EmployeeForm)
        self.assertIsNotNone(EmployeeListView)

    def test_hr_sync_backward_compatible_import(self):
        from fleet.sync.hr import sync_employees_from_hr_view as fleet_sync
        from .sync import sync_employees_from_hr_view as hr_sync

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
