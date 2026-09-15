"""Read-only browser verification with synthetic evaluation data; never saves evaluations."""
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
    from datetime import date
    from decimal import Decimal
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.contrib.staticfiles import finders
    from django.template.loader import render_to_string
    from django.test import RequestFactory
    from django.urls import reverse, resolve
    from django.utils import timezone
    from hr.models import Employee, EmployeeEvaluation, EvaluationGroup, EvaluationCriterion, EvaluationScale
    from hr.evaluation_forms import EvaluationValuesForm, EvaluationApprovalForm
    from hr.evaluation_views import EvaluationListView, EvaluationCreateView, EvaluationCatalogView, EvaluationCatalogEditView
    from hr.services.evaluations import build_snapshot, sign_snapshot, STAGES, MONTHS

    user = get_user_model()(pk=2147483600, username='Provera prikaza',is_superuser=True,is_active=True)
    factory = RequestFactory()
    pages = {}
    for name, view, kwargs in [
        ('hr:evaluation_list',EvaluationListView,{}),
        ('hr:evaluation_create',EvaluationCreateView,{}),
        ('hr:evaluation_catalog',EvaluationCatalogView,{}),
        ('hr:evaluation_catalog_create',EvaluationCatalogEditView,{'kind':'scales'}),
    ]:
        url = reverse(name, kwargs=kwargs)
        request = factory.get(url,{'year':2026,'month':9})
        request.user = user
        request.session = {'current_app':'kadrovi'}
        request.resolver_match = resolve(url)
        response = view.as_view()(request,**kwargs)
        response.render()
        assert response.status_code == 200
        pages[name] = response.content.decode('utf-8')
    # Synthetic objects only. No production employee details in screenshots.
    people = []
    for index, name in enumerate(['Primer','Rukovodilac','Direktor','Generalni']):
        key = 2147483646-index
        assert not Employee.objects.filter(pk=key).exists()
        people.append(Employee(pk=key,employee_code=0,first_name=name,last_name='Provera',
            org_unit_code='PRIMER',department_code=100,position='Istraživač',education='Visoka stručna sprema',
            gender='M',date_of_birth=date(1990,1,1),date_of_joining=date(2020,1,1)))
    assert not EmployeeEvaluation.objects.filter(pk=2147483646).exists()
    snapshot = build_snapshot(employee=people[0],group=EvaluationGroup.objects.get(code='employee'),
        year=2026,month=9,supervisor=people[1],director=people[2],general_director=people[3])
    common = {'sidebar_template':'sidebar_kadrovi.html','snapshot':snapshot}
    pages['values'] = render_to_string('hr/evaluation_form.html',dict(common,
        values_form=EvaluationValuesForm(snapshot=snapshot,token=sign_snapshot(snapshot,user))),request=request)
    item = EmployeeEvaluation(pk=2147483646,employee=people[0],year=2026,month=9,revision=1,
        snapshot=snapshot,unit_code='PRIMER',stimulation=Decimal(0),personal_coefficient=Decimal(1),created_at=timezone.now())
    item.approval_rows = [{'stage':stage,'name':snapshot['reviewers'][stage]['name'],'approval':None} for stage in STAGES]
    item.is_final = False
    item.final_coefficient = Decimal(1)
    common.update(evaluation=item,versions=[item],can_revise=True,can_approve=True,approval_form=EvaluationApprovalForm())
    pages['detail'] = render_to_string('hr/evaluation_detail.html',common,request=request)
    pages['print'] = render_to_string('hr/evaluation_print.html',common,request=request)
    pages['summary'] = render_to_string('hr/evaluation_list.html',dict(common,evaluations=[item],
        year=2026,month=9,months=list(enumerate(MONTHS,1)),units=['PRIMER'],can_create=True,
        can_catalog=True,bulk_form=EvaluationApprovalForm()),request=request)
    static = {path:str(storage.path(path)) for path,storage in finders.get_finder('django.contrib.staticfiles.finders.AppDirectoriesFinder').list([])}
    for folder in settings.STATICFILES_DIRS:
        folder = Path(folder)
        for path in folder.rglob('*'):
            if path.is_file(): static.setdefault(path.relative_to(folder).as_posix(),str(path))
    print(json.dumps({'pages':pages,'static':static,'counts':{'groups':EvaluationGroup.objects.count(),
        'criteria':EvaluationCriterion.objects.count(),'scales':EvaluationScale.objects.count()}}))


def browser_check():
    import mimetypes
    import subprocess
    from urllib.parse import unquote,urlparse
    from playwright.sync_api import sync_playwright
    payload = json.loads(subprocess.check_output([str(ROOT/'.venv/Scripts/python.exe'),'-X','utf8',__file__,'--render'],cwd=ROOT,text=True,encoding='utf-8'))
    checks = {'counts':payload['counts'],'browser':{}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={'width':1920,'height':1080})
        errors = []
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('dialog',lambda dialog:(errors.append(dialog.message),dialog.dismiss()))
        current = {}
        def handle(route):
            parsed = urlparse(route.request.url)
            if parsed.path.startswith('/static/'):
                filename = payload['static'].get(unquote(parsed.path[8:]))
                if filename:
                    return route.fulfill(path=filename,content_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream')
            if parsed.netloc == 'evaluation-preview.test' and parsed.path == '/':
                return route.fulfill(body=current['html'],content_type='text/html; charset=utf-8')
            return route.abort()
        page.route('**/*',handle)
        for name,html in payload['pages'].items():
            current['html'] = html
            page.goto('http://evaluation-preview.test/')
            page.locator('.preloader').wait_for(state='hidden')
            if page.locator('#appNewsModal.show').count():
                page.locator('#appNewsModal [data-bs-dismiss="modal"]').first.click()
                page.locator('#appNewsModal').wait_for(state='hidden')
                page.locator('.modal-backdrop').wait_for(state='hidden')
            if name in ('hr:evaluation_list','summary','hr:evaluation_catalog'):
                table = 'EvaluationCatalogTable' if name == 'hr:evaluation_catalog' else 'EvaluationListTable'
                page.wait_for_function('jQuery.fn.DataTable.isDataTable('+json.dumps('#'+table)+')')
                rows = page.evaluate('jQuery('+json.dumps('#'+table)+').DataTable().rows().count()')
                if name == 'hr:evaluation_catalog': assert rows == 60
                if name == 'summary': assert rows == 1
                checks['browser'][name] = {'datatable':True,'rows':rows}
            elif name in ('hr:evaluation_create','hr:evaluation_catalog_create'):
                page.wait_for_function("jQuery('select.select2-method').first().hasClass('select2-hidden-accessible')")
                checks['browser'][name] = {'select2':True}
            elif name == 'values':
                assert page.locator('#evaluation-coefficient').inner_text() == '1,00000'
                assert page.locator('.evaluation-points').count() == 6
                for select in page.locator('.evaluation-points').all(): select.select_option('4')
                assert page.locator('#evaluation-coefficient').inner_text() == '1,30000'
                page.screenshot(path=str(ROOT/'dokumentacija/kadrovi_ocenjivanje.png'),full_page=True)
                checks['browser'][name] = {'six_criteria':True,'neutral':'1,00000','maximum':'1,30000'}
            elif name == 'print':
                assert page.locator('.evaluation-report h2').inner_text() == 'IZVEŠTAJ O OCENJIVANJU'
                page.pdf(path=str(ROOT/'dokumentacija/Primer ocenjivanja - stampa.pdf'),format='A4',prefer_css_page_size=True)
                checks['browser'][name] = {'cyrillic':True,'pdf':True}
            else:
                assert page.locator('.evaluation-report').count() == 1
                checks['browser'][name] = {'report':True}
        browser.close()
    checks['browser_errors'] = errors
    (ROOT/'izvestaji/provera_ocenjivanja_20260911.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False))
    assert not errors,errors


if __name__ == '__main__':
    render_pages() if '--render' in sys.argv else browser_check()
