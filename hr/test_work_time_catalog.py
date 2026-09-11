from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from hr.forms import WorkTimeSheetLineForm
from hr.models import Employee, RecipientType, WorkTimeCategory, WorkTimeElement, WorkTimeSheet, WorkTimeSheetLine
from hr.services.work_time_catalog import import_work_time_catalog, sync_employee_recipient_types
from hr.sync import sync_employees_from_hr_view


class WorkTimeCatalogTests(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(employee_code=901, first_name='Test', last_name='Osoba', department_code=1, recipient_code='01', date_of_birth=date(1990,1,1), date_of_joining=date(2020,1,1))
        self.recipient = RecipientType.objects.create(code='01', name='Zaposleno lice')
        self.pensioner = RecipientType.objects.create(code='09', name='Lice penzioner fonda zaposlenih')
        self.category = WorkTimeCategory.objects.create(code='redovan_rad', name='Redovan rad')
        WorkTimeElement.objects.create(recipient_type=self.recipient, category=self.category, payroll_code=1, payroll_name='REDOVAN RAD')
        self.user = get_user_model().objects.create_user('employee-test', employee=self.employee)
        self.admin = get_user_model().objects.create_superuser('admin-test', 'admin@example.test', 'test')

    def make_workbook(self, rows):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / 'elements.xlsx'
        book = Workbook()
        book.active.append(['sif_prim','naz_prim','napomena','elsif','elnaz'])
        for row in rows:
            book.active.append(row)
        book.save(path)
        book.close()
        return path

    def test_import_normalizes_notes_and_preserves_local_edits_on_repeat(self):
        path = self.make_workbook([
            ['01','Zaposleno lice',' bolovanje ',77,'BOLOVANJE DO 30 DANA'],
            [1,'Zaposleno lice','bolovanje',143,'BOLOVANJE PREKO 30 DANA'],
            ['09','Lice penzioner fonda zaposlenih','topli obrok',211,'TOPLI OBROK'],
        ])
        result = import_work_time_catalog(path)
        self.assertEqual(result['elements_created'], 3)
        category = WorkTimeCategory.objects.get(code='bolovanje')
        self.assertEqual(category.name, 'Bolovanje')
        self.assertEqual(category.elements.count(), 2)
        self.assertFalse(WorkTimeCategory.objects.get(code='topli_obrok').employee_selectable)
        category.name = 'Bolovanje - prilagođeni naziv'
        category.save()
        self.recipient.name = 'Lokalni naziv primaoca'
        self.recipient.save()
        result = import_work_time_catalog(path)
        self.assertEqual(result['elements_created'], 0)
        self.assertEqual(result['existing_preserved'], 3)
        category.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(category.name, 'Bolovanje - prilagođeni naziv')
        self.assertEqual(self.recipient.name, 'Lokalni naziv primaoca')

    def test_invalid_or_conflicting_workbook_does_not_import_partial_rows(self):
        for invalid in [
            ['01','Zaposleno lice','nepoznato',77,'NAZIV'],
            ['01','Zaposleno lice','placeno odsustvo',77,'DRUGI NAZIV'],
        ]:
            path = self.make_workbook([['01','Zaposleno lice','bolovanje',77,'BOLOVANJE'], invalid])
            with self.assertRaises(ValidationError):
                import_work_time_catalog(path)
            self.assertFalse(WorkTimeCategory.objects.filter(code='bolovanje').exists())

    def test_dropdown_limits_recipient_and_excludes_payroll_only_and_inactive(self):
        other = WorkTimeCategory.objects.create(code='other', name='Drugi primalac')
        automatic = WorkTimeCategory.objects.create(code='regres', name='Regres', employee_selectable=False)
        inactive = WorkTimeCategory.objects.create(code='inactive', name='Neaktivno', is_active=False)
        WorkTimeElement.objects.create(recipient_type=self.pensioner, category=other, payroll_code=210, payroll_name='OTHER')
        for index, category in enumerate([automatic, inactive], 14):
            WorkTimeElement.objects.create(recipient_type=self.recipient, category=category, payroll_code=index, payroll_name='ELEMENT')
        form = WorkTimeSheetLineForm(employee=self.employee)
        self.assertEqual(list(form.fields['work_category'].queryset), [self.category])
        form = WorkTimeSheetLineForm(data={'line_number':1, 'work_category':other.pk}, employee=self.employee)
        self.assertFalse(form.is_valid())
        self.assertIn('work_category', form.errors)

    def test_historical_inactive_selection_is_preserved(self):
        sheet = WorkTimeSheet.objects.create(employee=self.employee, year=2026, month=5)
        line = WorkTimeSheetLine.objects.create(sheet=sheet, line_number=1, work_category=self.category, note='Dodatno')
        self.category.is_active = False
        self.category.save()
        self.assertIn(self.category, WorkTimeSheetLineForm(instance=line).fields['work_category'].queryset)
        self.assertNotIn(self.category, WorkTimeSheetLineForm(employee=self.employee).fields['work_category'].queryset)
        self.assertEqual(line.display_note, 'Redovan rad — Dodatno')

    @patch('hr.views.get_clock_events', return_value=[])
    def test_superuser_without_employee_can_open_save_and_print_selected_sheet(self, clock):
        self.client.force_login(self.admin)
        url = reverse('hr:employee_work_time_sheet', args=[self.employee.pk])
        response = self.client.get(url, {'year':2026,'month':5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['employee'], self.employee)
        sheet = response.context['sheet']
        data = {'month':5,'year':2026,'status':'draft','lines-TOTAL_FORMS':12,'lines-INITIAL_FORMS':12,'lines-MIN_NUM_FORMS':12,'lines-MAX_NUM_FORMS':12}
        for index, line in enumerate(sheet.lines.all()):
            data[f'lines-{index}-id'] = line.pk
            data[f'lines-{index}-line_number'] = line.line_number
        data.update({'lines-0-work_category':self.category.pk,'lines-0-note':'Dodatna napomena','lines-0-day_4':8})
        response = self.client.post(url, data)
        self.assertRedirects(response, url+'?month=5&year=2026', fetch_redirect_response=False)
        line = sheet.lines.get(line_number=1)
        self.assertEqual(line.work_category, self.category)
        self.assertEqual(line.day_4, 8)
        sheet.refresh_from_db()
        self.assertEqual(sheet.updated_by, self.admin)
        response = self.client.get(reverse('hr:work_time_sheet_print',args=[sheet.pk]))
        self.assertContains(response, 'Redovan rad — Dodatna napomena')
        clock.assert_called_once_with(date_from=date(2026,5,1), date_to=date(2026,6,1), employee_code=901)

    def test_regular_user_cannot_open_or_save_selected_employee_route(self):
        self.client.force_login(self.user)
        url = reverse('hr:employee_work_time_sheet', args=[self.employee.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {'year':2026,'month':5}).status_code, 403)
        self.assertFalse(WorkTimeSheet.objects.exists())

    def test_catalog_permissions_and_editable_labels(self):
        url = reverse('hr:work_time_catalog')
        edit = reverse('hr:work_time_catalog_edit', args=['recipients',self.recipient.pk])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code,403)
        self.assertEqual(self.client.post(edit, {'name':'Unauthorized'}).status_code,403)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(url),'DatatableWorkTimeElements')
        for kind in ['recipients','categories','elements']:
            self.assertEqual(self.client.get(reverse('hr:work_time_catalog_create',args=[kind])).status_code,200)
        self.assertRedirects(self.client.post(edit, {'code':'99','name':'Novi naziv','is_active':'on'}),url+'#recipients')
        self.recipient.refresh_from_db()
        self.assertEqual(self.recipient.code,'01')
        self.assertEqual(self.recipient.name,'Novi naziv')

    @patch('hr.services.work_time_catalog.connections')
    def test_targeted_sync_changes_only_new_fields_and_preserves_dictionary(self, connections):
        cursor = connections.__getitem__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(901,'09','Izvorni naziv'), (99999,'01','Neimportovana osoba')]
        counts = sync_employee_recipient_types()
        self.employee.refresh_from_db()
        self.pensioner.refresh_from_db()
        self.assertEqual(counts['updated'],1)
        self.assertEqual(self.employee.recipient_code,'09')
        self.assertEqual(self.employee.recipient_name,'Izvorni naziv')
        self.assertEqual(self.employee.first_name,'Test')
        self.assertEqual(Employee.objects.count(),1)
        self.assertEqual(self.pensioner.name,'Lice penzioner fonda zaposlenih')

    @patch('hr.services.work_time_catalog.connections')
    def test_conflicting_source_recipient_aborts_sync(self, connections):
        cursor = connections.__getitem__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(901,'09','Prvi'), (901,'01','Drugi')]
        with self.assertRaises(ValidationError):
            sync_employee_recipient_types()
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.recipient_code,'01')

    @patch('hr.sync.connections')
    @patch('hr.sync._hr_employee_columns')
    def test_regular_hr_sync_reads_new_columns_and_preserves_them_when_source_lacks_columns(self, columns, connections):
        cursor = connections.__getitem__.return_value.cursor.return_value.__enter__.return_value
        row = [901,'Osoba Test',None,None,'1','M',date(1990,1,1),date(2020,1,1),None,'D',None,None,None,None,None,None,None,None,None,None,'09','Vrsta iz izvora']
        columns.return_value = {'sif_prim':'sif_prim','naz_prim':'naz_prim'}
        cursor.fetchall.return_value = [row]
        sync_employees_from_hr_view()
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.recipient_code,'09')
        self.assertEqual(self.employee.recipient_name,'Vrsta iz izvora')
        columns.return_value = {}
        cursor.fetchall.return_value = [row[:-2]+[None,None]]
        sync_employees_from_hr_view()
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.recipient_code,'09')
        self.assertEqual(self.employee.recipient_name,'Vrsta iz izvora')
