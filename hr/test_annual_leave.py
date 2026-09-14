from datetime import date, datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from hr.models import AnnualLeaveAllowance, AnnualLeaveDecision, AnnualLeaveSync, Employee, WorkTimeSheet, WorkTimeSheetLine
from hr.forms import WorkTimeSheetLineForm
from hr.services.annual_leave import sync_annual_leave


def allocation(code=701, year=2026, days=25):
    return (1, str(year), code, 20, 2, 1, 1, 1, 0, days, 0, 'TEST OSOBA')


def decision(code=701, year=2026, days=5, start=None):
    return (1, str(year), code, start or datetime(year, 7, 6), datetime(year, 7, 10), days, 'Prvi deo')


class AnnualLeaveSyncTests(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(employee_code=701, first_name='Test', last_name='Osoba', department_code=1,
            date_of_birth=date(1990,1,1), date_of_joining=date(2020,1,1))

    def run_sync(self, allocations=None, decisions=None, **kwargs):
        with patch('hr.services.annual_leave.fetch_source', return_value=(allocations if allocations is not None else [allocation()], decisions if decisions is not None else [decision()])):
            return sync_annual_leave(**kwargs)

    def test_import_is_idempotent_and_preserves_employee_links_and_source_components(self):
        first = self.run_sync()
        self.assertEqual(first['allocations']['created'], 1)
        self.assertEqual(first['decisions']['created'], 1)
        item = AnnualLeaveAllowance.objects.get()
        self.assertEqual(item.employee, self.employee)
        self.assertEqual(item.allocated_days, 25)
        self.assertEqual(item.source_day_1, 20)
        item_pk = AnnualLeaveDecision.objects.get().pk
        second = self.run_sync()
        self.assertEqual(second['allocations']['unchanged'], 1)
        self.assertEqual(second['decisions']['unchanged'], 1)
        self.assertEqual(AnnualLeaveDecision.objects.get().pk, item_pk)
        self.assertEqual(AnnualLeaveSync.objects.count(), 2)

    def test_source_corrections_update_existing_keys(self):
        self.run_sync()
        old_pk = AnnualLeaveDecision.objects.get().pk
        corrected = list(decision(days=4))
        corrected[4] = datetime(2026,7,9)
        result = self.run_sync([allocation(days=26)], [corrected])
        self.assertEqual(result['allocations']['updated'], 1)
        self.assertEqual(result['decisions']['updated'], 1)
        self.assertEqual(AnnualLeaveDecision.objects.get().pk, old_pk)
        self.assertEqual(AnnualLeaveDecision.objects.get().end_date, date(2026,7,9))

    def test_year_sync_does_not_withdraw_other_years_and_can_restore_missing_record(self):
        self.run_sync([allocation(),allocation(year=2025)], [decision(),decision(year=2025)])
        result = self.run_sync([allocation()], [], year=2026)
        self.assertEqual(result['decisions']['withdrawn'], 1)
        self.assertFalse(AnnualLeaveDecision.objects.get(year=2026).source_present)
        self.assertTrue(AnnualLeaveDecision.objects.get(year=2025).source_present)
        self.assertTrue(AnnualLeaveAllowance.objects.get(year=2025).source_present)
        result = self.run_sync(year=2026)
        self.assertEqual(result['decisions']['updated'], 1)
        self.assertEqual(AnnualLeaveDecision.objects.filter(year=2026).count(),1)
        self.assertTrue(AnnualLeaveDecision.objects.get(year=2026).source_present)

    def test_changed_start_key_retains_previous_decision_as_withdrawn(self):
        self.run_sync()
        result = self.run_sync(decisions=[decision(start=datetime(2026,7,7))])
        self.assertEqual(result['decisions']['created'],1)
        self.assertEqual(result['decisions']['withdrawn'],1)
        self.assertEqual(AnnualLeaveDecision.objects.count(),2)

    def test_source_datetime_key_preserves_time_precision(self):
        self.run_sync(decisions=[decision(start=datetime(2026,7,6,8,0,0,123000)),decision(start=datetime(2026,7,6,9))])
        self.assertEqual(AnnualLeaveDecision.objects.count(),2)

    def test_legacy_zero_employee_code_is_preserved_as_unlinked(self):
        self.employee.employee_code = 0
        self.employee.save()
        result = self.run_sync(decisions=[decision(code=0)])
        self.assertEqual(result['decisions']['unlinked'], 1)
        self.assertIsNone(AnnualLeaveDecision.objects.get().employee_id)

    def test_unknown_employee_is_preserved_and_linked_on_later_sync(self):
        result = self.run_sync([allocation(code=702)],[decision(code=702)])
        self.assertEqual(result['allocations']['unlinked'],1)
        self.assertEqual(result['decisions']['unlinked'],1)
        self.assertIsNone(AnnualLeaveAllowance.objects.get().employee_id)
        self.employee.employee_code = 702
        self.employee.save()
        self.run_sync([allocation(code=702)],[decision(code=702)])
        self.assertEqual(AnnualLeaveAllowance.objects.get().employee,self.employee)
        self.assertEqual(AnnualLeaveDecision.objects.get().employee,self.employee)

    def test_invalid_duplicate_or_empty_source_leaves_previous_snapshot_intact(self):
        self.run_sync()
        invalid_period = list(decision())
        invalid_period[4] = datetime(2026,7,1)
        cases = [([allocation(days=26)],[invalid_period]), ([allocation(),allocation()], [decision()]),
                 ([allocation()],[decision(),decision()]), ([],[]), ([allocation()], [decision(year=2025)])]
        for allocations, decisions in cases:
            with self.subTest(allocations=len(allocations),decisions=len(decisions)):
                with self.assertRaises(ValidationError):
                    self.run_sync(allocations,decisions,year=2026)
                self.assertEqual(AnnualLeaveAllowance.objects.get().allocated_days,25)
                self.assertTrue(AnnualLeaveDecision.objects.get().source_present)
                self.assertEqual(AnnualLeaveSync.objects.count(),1)

    @patch('hr.services.annual_leave.fetch_source', side_effect=DatabaseError('offline'))
    def test_failed_source_does_not_change_local_records(self, source):
        with self.assertRaises(DatabaseError):
            sync_annual_leave()
        self.assertFalse(AnnualLeaveSync.objects.exists())

    def test_write_failure_rolls_back_both_tables_and_log(self):
        self.run_sync()
        with patch('hr.services.annual_leave.AnnualLeaveDecision.objects.bulk_update', side_effect=DatabaseError('write failed')):
            with self.assertRaises(DatabaseError):
                self.run_sync([allocation(days=29)],[decision(days=4)])
        self.assertEqual(AnnualLeaveAllowance.objects.get().allocated_days,25)
        self.assertEqual(AnnualLeaveSync.objects.count(),1)

    def test_dry_run_rolls_back_every_local_write(self):
        result = self.run_sync(dry_run=True)
        self.assertEqual(result['allocations']['created'],1)
        self.assertFalse(AnnualLeaveAllowance.objects.exists())
        self.assertFalse(AnnualLeaveDecision.objects.exists())
        self.assertFalse(AnnualLeaveSync.objects.exists())

    def test_removed_note_cannot_be_edited_and_historical_text_is_preserved(self):
        sheet = WorkTimeSheet.objects.create(employee=self.employee,year=2026,month=7)
        line = WorkTimeSheetLine.objects.create(sheet=sheet,line_number=1,note='Ranija beleška')
        form = WorkTimeSheetLineForm(data={'line_number':1,'note':'Promena kroz POST'},instance=line,employee=self.employee)
        self.assertTrue(form.is_valid(),form.errors)
        form.save()
        line.refresh_from_db()
        self.assertEqual(line.note,'Ranija beleška')
        self.assertEqual(line.display_note,'')


class AnnualLeaveViewTests(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(employee_code=701,first_name='Test',last_name='Osoba',department_code=1,
            date_of_birth=date(1990,1,1),date_of_joining=date(2020,1,1))
        self.other = Employee.objects.create(employee_code=702,first_name='Druga',last_name='Osoba',department_code=1,
            date_of_birth=date(1990,1,1),date_of_joining=date(2020,1,1))
        self.user = get_user_model().objects.create_user('employee-annual',employee=self.employee)
        self.admin = get_user_model().objects.create_superuser('admin-annual','admin@example.test','test')
        with patch('hr.services.annual_leave.fetch_source',return_value=([allocation(),allocation(code=702)],[decision(),decision(code=702)])):
            sync_annual_leave()

    def test_regular_user_cannot_view_global_list_or_sync(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('hr:annual_leave_list')).status_code,403)
        self.assertEqual(self.client.post(reverse('hr:annual_leave_sync')).status_code,403)
        self.assertEqual(AnnualLeaveSync.objects.count(),1)

    def test_superuser_sees_filtered_table_and_sync_is_post_only(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('hr:annual_leave_list'),{'year':2026,'q':'701'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.context['allocation_count'],1)
        self.assertContains(response,'DatatableAnnualDecision')
        self.assertContains(response,'06.07.2026')
        self.assertContains(response,'preostali saldo se još ne obračunava')
        self.assertEqual(self.client.get(reverse('hr:annual_leave_sync')).status_code,405)

    def test_employee_filters_combine_status_unit_recipient_and_name(self):
        self.employee.org_unit_code = '100'
        self.employee.recipient_code = '01'
        self.employee.save()
        self.other.org_unit_code = '200'
        self.other.is_active = False
        self.other.save()
        self.client.force_login(self.admin)
        response = self.client.get(reverse('employee_list'), {'status':'all','oj':'100','recipient':'01','q':'Test Osoba'})
        self.assertEqual(list(response.context['employees']), [self.employee])
        self.assertContains(response, 'HrEmployeeTable')
        response = self.client.get(reverse('employee_list'), {'inactive':'1'})
        self.assertEqual(list(response.context['employees']), [self.other])

    def test_own_profile_only_shows_own_annual_leave(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('my_employee_profile'),{'employee':self.other.pk})
        self.assertEqual(list(response.context['annual_allowances'].values_list('employee_id',flat=True)),[self.employee.pk])
        self.assertEqual(list(response.context['annual_decisions'].values_list('employee_id',flat=True)),[self.employee.pk])
        self.assertContains(response,'Godišnji odmori')

    @patch('hr.annual_leave_views.sync_annual_leave',side_effect=DatabaseError('unavailable'))
    def test_sync_error_shows_message_without_changing_data(self, sync):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('hr:annual_leave_sync'),{'year':2026},follow=True)
        self.assertContains(response,'Prethodno sinhronizovani podaci ostali su sačuvani')
        self.assertEqual(AnnualLeaveAllowance.objects.count(),2)

    @patch('hr.services.annual_leave.fetch_source',return_value=([allocation(days=26)],[decision()]))
    def test_superuser_can_sync_selected_year(self, source):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('hr:annual_leave_sync'),{'year':2026})
        self.assertRedirects(response,reverse('hr:annual_leave_list')+'?year=2026')
        self.assertEqual(AnnualLeaveAllowance.objects.get(employee=self.employee).allocated_days,26)
        self.assertEqual(AnnualLeaveSync.objects.first().created_by,self.admin)
