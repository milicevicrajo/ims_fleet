"""Read-only render/browser checks. The work sheet uses an unsaved synthetic employee."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render_pages():
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_erp.settings.development')
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.contrib.staticfiles import finders
    from django.db.models import Count
    from django.test import RequestFactory
    from django.template.loader import render_to_string
    from django.utils import timezone
    from django.urls import resolve, reverse
    from hr.catalog_views import WorkTimeCatalogView, WorkTimeCatalogEditView
    from hr.models import Employee, RecipientType, WorkTimeCategory, WorkTimeElement, WorkTimeSheet
    from hr.views import MyWorkTimeSheetView
    from hr.annual_leave_views import AnnualLeaveListView
    from hr.models import AnnualLeaveAllowance, AnnualLeaveDecision, AnnualLeaveSync, SickLeave
    from datetime import date
    from unittest.mock import patch

    user = get_user_model()(username='Provera prikaza', is_superuser=True, is_active=True)
    synthetic_pk = 2147483646
    assert not Employee.objects.filter(pk=synthetic_pk).exists()
    assert not WorkTimeSheet.objects.filter(pk=synthetic_pk).exists()
    employee = Employee(pk=synthetic_pk, employee_code=0, first_name='Primer', last_name='Radne liste', recipient_code='01', recipient_name='Zaposleno lice',department_code=100,org_unit_code='100',position='Primer radnog mesta',gender='M',date_of_birth=date(1990,1,1),date_of_joining=date(2020,1,1))
    sheet = WorkTimeSheet(pk=synthetic_pk, employee=employee, year=2026, month=9)
    factory = RequestFactory()
    pages = {}
    for name, view, kwargs in [
        ('hr:work_time_catalog', WorkTimeCatalogView, {}),
        ('hr:work_time_catalog_create', WorkTimeCatalogEditView, {'kind':'elements'}),
        ('hr:employee_work_time_sheet', MyWorkTimeSheetView, {'employee_pk':synthetic_pk}),
    ]:
        url = reverse(name, kwargs=kwargs)
        request = factory.get(url, {'month':9,'year':2026})
        request.user = user
        request.session = {'current_app':'kadrovi'}
        request.resolver_match = resolve(url)
        with patch.object(MyWorkTimeSheetView, 'get_employee', return_value=employee), patch.object(MyWorkTimeSheetView,'get_sheet',return_value=sheet), patch('hr.views.get_clock_events',return_value=[]):
            response = view.as_view()(request, **kwargs)
            response.render()
        pages[name] = response.content.decode('utf-8')
    annual_url = reverse('hr:annual_leave_list')
    request = factory.get(annual_url, {'year':2026})
    request.user = user
    request.session = {'current_app':'kadrovi'}
    request.resolver_match = resolve(annual_url)
    live_response = AnnualLeaveListView.as_view()(request)
    live_response.render()
    annual_render = {'status':live_response.status_code,'allocations_2026':live_response.context_data['allocation_count'],'decisions_2026':live_response.context_data['decision_count'],'unlinked_2026':live_response.context_data['unlinked_count']}
    allocation = AnnualLeaveAllowance(employee=employee,employee_code=0,year=2026,allocated_days=25,last_seen_at=timezone.now())
    decisions = [AnnualLeaveDecision(employee=employee,employee_code=0,year=2026,start_date=day,end_date=day,approved_days=1,source_comment='Primer rešenja') for day in [date(2026,5,31),date(2026,6,1)]]
    pages['hr:annual_leave_list'] = render_to_string('hr/annual_leave_list.html',{
        'annual_allowances':[allocation],'annual_decisions':decisions,'allocation_count':1,'decision_count':2,'unlinked_count':0,
        'selected_year':2026,'available_years':[2026],'can_sync':True,'can_view_employee':True,'sidebar_template':'sidebar_kadrovi.html',
    },request=request)
    pages['employee_list'] = render_to_string('hr/employee_list.html', {
        'employees':[employee], 'status':'active', 'oj_options':['100'], 'recipient_options':RecipientType.objects.all(),
        'can_sync_employees':True,'can_view_employee':True,'sidebar_template':'sidebar_kadrovi.html',
    },request=request)
    leave = SickLeave(employee=employee, rfzo_id='PRIMER', start_date=date(2026,8,3),end_date=date(2026,8,7),source_status='Zaključeno',source_total_days=5)
    pages['hr:sick_leave_list'] = render_to_string('hr/sick_leave_list.html', {
        'sick_leaves':[leave], 'total_count':1,'unlinked_count':0,'can_import':True,'can_view_employee':True,'sidebar_template':'sidebar_kadrovi.html',
    },request=request)
    # Static files only, no private uploads or employee data.
    static = {path: str(storage.path(path)) for path, storage in finders.get_finder('django.contrib.staticfiles.finders.AppDirectoriesFinder').list([])}
    from django.conf import settings
    for folder in settings.STATICFILES_DIRS:
        folder = Path(folder)
        for path in folder.rglob('*'):
            if path.is_file():
                static.setdefault(path.relative_to(folder).as_posix(),str(path))
    counts = {
        'annual_render':annual_render, 'annual_allowances':AnnualLeaveAllowance.objects.count(),
        'annual_decisions':AnnualLeaveDecision.objects.count(),'annual_sync_batches':AnnualLeaveSync.objects.count(),
        'recipients':RecipientType.objects.count(), 'categories':WorkTimeCategory.objects.count(),
        'elements':WorkTimeElement.objects.count(), 'selectable_categories':WorkTimeCategory.objects.filter(employee_selectable=True,is_active=True).count(),
        'employees_by_recipient':list(Employee.objects.values('recipient_code','is_active').annotate(total=Count('pk'))),
    }
    print(json.dumps({'pages':pages,'static':static,'counts':counts}))


def browser_check():
    import mimetypes
    import subprocess
    from urllib.parse import unquote, urlparse
    from playwright.sync_api import sync_playwright

    payload = json.loads(subprocess.check_output([str(ROOT/'.venv/Scripts/python.exe'),'-X','utf8',__file__,'--render'], cwd=ROOT, text=True, encoding='utf-8'))
    checks = {'counts':payload['counts'], 'browser':{}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={'width':1920,'height':1080})
        errors = []
        page.on('pageerror',lambda error: errors.append(str(error)))
        page.on('dialog',lambda dialog: (errors.append(dialog.message), dialog.dismiss()))
        current = {}

        def route_handler(route):
            parsed = urlparse(route.request.url)
            if parsed.path.startswith('/static/'):
                filename = payload['static'].get(unquote(parsed.path[len('/static/'):]))
                if filename:
                    return route.fulfill(path=filename, content_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream')
            if parsed.netloc == 'hr-preview.test' and parsed.path == '/':
                return route.fulfill(body=current['html'], content_type='text/html; charset=utf-8')
            return route.abort()

        page.route('**/*',route_handler)
        for name, html in payload['pages'].items():
            current['html'] = html
            page.goto('http://hr-preview.test/')
            page.locator('.preloader').wait_for(state='hidden')
            if page.locator('#appNewsModal.show').count():
                page.locator('#appNewsModal [data-bs-dismiss="modal"]').first.click()
                page.locator('#appNewsModal').wait_for(state='hidden')
            if name == 'hr:work_time_catalog':
                page.wait_for_function("jQuery.fn.DataTable.isDataTable('#DatatableWorkTimeElements')")
                count = page.evaluate("jQuery('#DatatableWorkTimeElements').DataTable().rows().count()")
                assert count == 27
                page.locator('a[href="#categories"][data-bs-toggle]').click()
                page.wait_for_function("document.querySelector('#categories').classList.contains('active')")
                assert page.locator('#categories .list-group-item').count() == 13
                page.locator('a[href="#recipients"][data-bs-toggle]').click()
                page.wait_for_function("document.querySelector('#recipients').classList.contains('active')")
                assert page.locator('#recipients .list-group-item').count() == 3
                page.locator('a[href="#elements"][data-bs-toggle]').click()
                page.wait_for_function("document.querySelector('#elements').classList.contains('active')")
                page.evaluate("jQuery('#DatatableWorkTimeElements').DataTable().search('nema-ovakve-stavke').draw()")
                assert page.evaluate("jQuery('#DatatableWorkTimeElements').DataTable().rows({search:'applied'}).count()") == 0
                page.evaluate("jQuery('#DatatableWorkTimeElements').DataTable().search('').draw()")
                page.screenshot(path=str(ROOT/'dokumentacija/kadrovi_elementi_rl.png'))
                checks['browser'][name] = {'rows':count,'tabs':3,'search_empty':True}
            elif name == 'hr:annual_leave_list':
                page.wait_for_function("jQuery.fn.DataTable.isDataTable('#DatatableAnnualDecision')")
                assert page.evaluate("jQuery('#DatatableAnnualDecision').DataTable().rows().count()") == 2
                assert page.locator('#DatatableAnnualDecision tbody tr').first.locator('td').nth(1).inner_text() == '01.06.2026'
                assert page.locator('form[action$="/godisnji-odmori/sinhronizacija/"] input[name="csrfmiddlewaretoken"]').count() == 1
                page.screenshot(path=str(ROOT/'dokumentacija/kadrovi_godisnji_odmori.png'))
                checks['browser'][name] = {'tables':2,'date_sort':True,'sync_form':True}
            elif name in ('employee_list','hr:sick_leave_list'):
                table = 'HrEmployeeTable' if name == 'employee_list' else 'DatatableSickLeave'
                page.wait_for_function('jQuery.fn.DataTable.isDataTable('+json.dumps('#'+table)+')')
                assert page.locator('.fleet-list-hero').count() == 1
                assert page.locator('.fleet-list-filter').count() == 1
                assert page.locator('.fleet-list-filter input[name="q"]').is_visible()
                assert page.locator('#'+table+' a.btn').count() == 1
                page.screenshot(path=str(ROOT/('dokumentacija/kadrovi_zaposleni.png' if name == 'employee_list' else 'dokumentacija/kadrovi_bolovanja.png')))
                if name == 'employee_list':
                    page.locator('#employee-status').select_option('inactive')
                    page.wait_for_url('**/?status=inactive*')
                    assert 'status=inactive' in page.url
                checks['browser'][name] = {'table':True,'hero':True,'filter':True,'detail_button':True}
            elif name == 'hr:employee_work_time_sheet':
                page.wait_for_function("jQuery('.work-category-select').first().hasClass('select2-hidden-accessible')")
                assert page.locator('.work-category-select').count() == 12
                assert page.locator('.note-input').count() == 0
                options = page.locator('.work-category-select').first.locator('option').all_text_contents()
                assert len(options) == 11 and 'Godišnji odmor' in options and 'Regres' not in options
                page.locator('.hours-input').first.fill('8')
                assert page.locator('#grand-total').inner_text() == '8'
                page.evaluate("document.querySelector('.work-sheet-table-wrap').scrollLeft=3000")
                select_id = page.locator('.work-category-select').first.get_attribute('id')
                page.locator('#select2-'+select_id+'-container').click()
                page.get_by_role('option',name='Godišnji odmor',exact=True).click()
                assert page.locator('.work-category-select').first.locator('option:checked').inner_text() == 'Godišnji odmor'
                page.screenshot(path=str(ROOT/'dokumentacija/kadrovi_radna_lista_izbor.png'))
                checks['browser'][name] = {'selectors':12,'available_categories':10,'selection_and_hours':True}
            else:
                page.wait_for_function("jQuery('select.select2-method').first().hasClass('select2-hidden-accessible')")
                checks['browser'][name] = {'form_rendered':True}
        browser.close()
    checks['browser_errors'] = errors
    (ROOT/'izvestaji/provera_hr_sifrarnika_20260911.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False))
    assert not errors, errors


if __name__ == '__main__':
    if '--render' in sys.argv:
        render_pages()
    else:
        browser_check()
