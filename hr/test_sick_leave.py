from datetime import date, datetime
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from openpyxl import Workbook

from core.models import PermissionCode,Role
from fleet.models import PutniNalog,OrganizationalUnit
from hr.models import Employee,SickLeave,SickLeaveImport,WorkTimeSheetLine
from hr.services.attendance import ClockEvent
from hr.services.sick_leave import import_rfzo_workbook,normalize_personal_number,parse_rfzo_workbook,sick_leaves_by_day

HEADERS=['Ид','Пацијент','ЈМБГ','Статус','Узрок','Датум почетка боловања','Датум закључења боловања','Укупно дана','Лекар','Здравствена установа','Филијала']


def workbook_bytes(*rows):
    book=Workbook();sheet=book.active;sheet.append(HEADERS)
    for row in rows:sheet.append(row)
    buf=BytesIO();book.save(buf);book.close();return buf.getvalue()


def source_row(identity='100',jmbg='0000000000001',start='2026-08-30',end='2026-09-02',status='Zaključeno'):
    return [identity,'Ne preuzimati ime',jmbg,status,'Ne preuzimati dijagnozu',start,end,'4','Ne preuzimati lekara','Ustanova','Filijala']


def employee(code=1,jmbg='0000000000001'):
    return Employee.objects.create(employee_code=code,first_name='Test',last_name=f'Zaposleni {code}',
        position='Test',department_code=1,gender='M',date_of_birth=date(1990,1,1),
        date_of_joining=date(2020,1,1),personal_number=jmbg)


class RfzoParserTests(SimpleTestCase):
    def test_reads_cyrillic_rfzo_headers_and_only_required_data(self):
        parsed=parse_rfzo_workbook(workbook_bytes(source_row()))[0]
        self.assertEqual(parsed['start_date'],date(2026,8,30))
        self.assertEqual(parsed['source_total_days'],4)
        self.assertNotIn('diagnosis',parsed)
        self.assertNotIn('Ne preuzimati',str(parsed))

    def test_numeric_jmbg_preserves_leading_zero_and_rejects_invalid_values(self):
        self.assertEqual(normalize_personal_number(101990123456),'0101990123456')
        for value in ['bad','123',12.25,True]:self.assertIsNone(normalize_personal_number(value))

    def test_dates_accept_excel_dates_and_dmy(self):
        row=source_row(start=datetime(2026,8,30),end='02.09.2026.')
        self.assertEqual(parse_rfzo_workbook(workbook_bytes(row))[0]['end_date'],date(2026,9,2))

    def test_invalid_later_row_rejects_entire_input(self):
        with self.assertRaises(ValidationError):
            parse_rfzo_workbook(workbook_bytes(source_row(),source_row('101',end='2026-01-01')))

    def test_duplicate_source_identity_conflicts_are_rejected(self):
        with self.assertRaises(ValidationError):
            parse_rfzo_workbook(workbook_bytes(source_row(),source_row(end='2026-09-03')))
        self.assertEqual(len(parse_rfzo_workbook(workbook_bytes(source_row(),source_row()))),1)

    def test_missing_headers_or_invalid_file_are_rejected(self):
        with self.assertRaises(ValidationError):parse_rfzo_workbook(b'not an excel')
        book=Workbook();book.active.append(['Missing headers']);buf=BytesIO();book.save(buf)
        with self.assertRaises(ValidationError):parse_rfzo_workbook(buf.getvalue())


class SickLeaveImportTests(TestCase):
    def setUp(self):
        self.employee=employee()

    def load(self,*rows,**kwargs):
        return import_rfzo_workbook(workbook_bytes(*(rows or [source_row()])),filename='rfzo.xlsx',
            source_date=kwargs.pop('source_date',date(2026,9,10)),**kwargs)

    def test_repeat_is_idempotent_and_matches_employee(self):
        first=self.load();second=self.load()
        self.assertEqual(first.created_count,1);self.assertEqual(second.unchanged_count,1)
        self.assertEqual(SickLeave.objects.count(),1)
        self.assertEqual(SickLeave.objects.get().employee,self.employee)

    def test_existing_id_updates_end_and_status(self):
        self.load(source_row(status='Aktivno'))
        batch=self.load(source_row(end='2026-09-04'))
        self.assertEqual(batch.updated_count,1)
        self.assertEqual(SickLeave.objects.get().end_date,date(2026,9,4))

    def test_jmbg_identity_change_rolls_back_all_rows(self):
        self.load()
        with self.assertRaises(ValidationError):
            self.load(source_row('101'),source_row(jmbg='0000000000002'))
        self.assertEqual(SickLeave.objects.count(),1)
        self.assertEqual(SickLeaveImport.objects.count(),1)

    def test_older_export_cannot_replace_newer_period(self):
        self.load()
        with self.assertRaises(ValidationError):self.load(source_date=date(2026,9,9))

    def test_missing_and_ambiguous_jmbg_are_not_guessed(self):
        employee(2)
        batch=self.load(source_row(),source_row('101',jmbg='0000000000009'))
        self.assertEqual(batch.unlinked_count,2)
        self.assertEqual(SickLeave.objects.filter(employee__isnull=True).count(),2)

    def test_repeat_resolves_previously_unmatched_employee(self):
        self.load(source_row(jmbg='0000000000002'))
        linked=employee(2,'0000000000002')
        self.load(source_row(jmbg='0000000000002'))
        self.assertEqual(SickLeave.objects.get().employee,linked)

    def test_dry_run_and_bad_file_do_not_write(self):
        result=self.load(dry_run=True)
        self.assertEqual(result['created_count'],1)
        self.assertFalse(SickLeave.objects.exists());self.assertFalse(SickLeaveImport.objects.exists())
        with self.assertRaises(ValidationError):self.load(source_row(),source_row('101',jmbg='bad'))
        self.assertFalse(SickLeave.objects.exists())

    def test_calendar_clips_to_month_and_includes_both_ends(self):
        self.load()
        days=sick_leaves_by_day(self.employee,2026,9)
        self.assertEqual(set(days),{date(2026,9,1),date(2026,9,2)})

    def test_open_interval_stops_at_source_date_and_cancelled_is_excluded(self):
        self.load(source_row(end=None,status='Aktivno'))
        self.assertEqual(len(sick_leaves_by_day(self.employee,2026,9)),10)
        self.load(source_row(status='Stornirano'))
        self.assertFalse(sick_leaves_by_day(self.employee,2026,9))


class SickLeaveViewTests(TestCase):
    def setUp(self):
        self.employee=employee()
        self.user=get_user_model().objects.create_user('absence-test',password='test',employee=self.employee)
        self.client.force_login(self.user)
        import_rfzo_workbook(workbook_bytes(source_row()),filename='rfzo.xlsx',source_date=date(2026,9,10))

    def grant(self,*codes):
        role=Role.objects.create(name='Test odsustva',slug='test-odsustva')
        for code in codes:
            permission,_=PermissionCode.objects.get_or_create(code=code)
            role.permissions.add(permission)
        self.user.roles.add(role)

    def test_list_and_import_require_explicit_permissions(self):
        self.assertEqual(self.client.get(reverse('hr:sick_leave_list')).status_code,403)
        self.assertEqual(self.client.post(reverse('hr:sick_leave_import'),{}).status_code,403)

    def test_authorized_list_hides_full_jmbg(self):
        self.grant('hr:sick_leave_list')
        response=self.client.get(reverse('hr:sick_leave_list'))
        self.assertContains(response,'Zaposleni 1')
        self.assertNotContains(response,'0000000000001')

    def test_authorized_upload_updates_without_duplicates(self):
        self.grant('hr:sick_leave_import','hr:sick_leave_list')
        response=self.client.post(reverse('hr:sick_leave_import'),{
            'source_date':'2026-09-10','file':SimpleUploadedFile('rfzo.xlsx',workbook_bytes(source_row()))})
        self.assertRedirects(response,reverse('hr:sick_leave_list'))
        self.assertEqual(SickLeave.objects.count(),1)
        self.assertEqual(SickLeaveImport.objects.first().created_by,self.user)

    @patch('hr.views.get_clock_events',return_value=[])
    def test_work_sheet_annotations_keep_trip_and_do_not_fill_hours(self,mock):
        unit=OrganizationalUnit.objects.create(code='100',name='Test',center='10')
        PutniNalog.objects.create(order_number='TEST-PN',order_date=date(2026,9,1),employee=self.employee,
            job_code=unit,travel_location='Test',task='Test',travel_date=date(2026,9,1),number_of_days=1,advance_payment=0)
        response=self.client.get(reverse('hr:work_time_sheet'),{'year':2026,'month':9})
        self.assertContains(response,'Bolovanje · RFZO 100')
        self.assertContains(response,'Putni nalog TEST-PN')
        self.assertEqual(sum(l.total_hours for l in WorkTimeSheetLine.objects.all()),0)
        row=response.context['clock_attendance_rows'][0]
        self.assertEqual(row['status'],'Bolovanje')

    @patch('hr.views.get_clock_events',side_effect=DatabaseError('private connection details'))
    def test_annotations_stay_visible_when_clock_source_is_unavailable(self,mock):
        response=self.client.get(reverse('hr:work_time_sheet'),{'year':2026,'month':9})
        self.assertContains(response,'Bolovanje · RFZO 100')
        self.assertNotContains(response,'private connection details')
        self.assertEqual(response.context['clock_attendance_rows'][0]['hours_label'],'—')

    @patch('hr.views.get_clock_events',return_value=[])
    def test_user_cannot_read_other_employee_absences_by_query_parameter(self,mock):
        other=employee(2,'0000000000002')
        import_rfzo_workbook(workbook_bytes(source_row('999',jmbg=other.personal_number)),filename='rfzo.xlsx',source_date=date(2026,9,10))
        response=self.client.get(reverse('hr:work_time_sheet'),{'year':2026,'month':9,'employee':other.pk})
        self.assertContains(response,'RFZO 100')
        self.assertNotContains(response,'RFZO 999')
