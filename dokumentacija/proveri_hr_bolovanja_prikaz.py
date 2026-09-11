"""Read-only rendering of the new HR pages and aggregate annual-leave checks."""
import os,sys,json
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));os.environ.setdefault('DJANGO_SETTINGS_MODULE','ims_erp.settings.development')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import RequestFactory
from django.urls import resolve,reverse
from hr.absence_views import SickLeaveListView,SickLeaveImportView
from hr.models import SickLeave,SickLeaveImport
from hr.services.sick_leave import sick_leaves_by_day
from core.models import Role

user=get_user_model().objects.filter(is_superuser=True,is_active=True).first()
factory=RequestFactory();result={'checked_at':'2026-09-11','render':{}}
for name,view in [('hr:sick_leave_list',SickLeaveListView),('hr:sick_leave_import',SickLeaveImportView)]:
    request=factory.get(reverse(name));request.user=user;request.session={};request.resolver_match=resolve(reverse(name))
    response=view.as_view()(request);response.render()
    result['render'][name]={'status':response.status_code,'bytes':len(response.content)}
    # Keep only aggregate render checks; do not save employee health HTML.
result['sick_leave']={'count':SickLeave.objects.count(),'unlinked':SickLeave.objects.filter(employee__isnull=True).count(),
 'import_batches':SickLeaveImport.objects.count(),
 'uprava_permissions':list(Role.objects.get(slug='uprava').permissions.filter(code__startswith='hr:sick_leave').values_list('code',flat=True))}
with connections['default'].cursor() as c:
    for table in ('Godmor','GodmorKor'):
        c.execute(f'SELECT sif_pred, COUNT_BIG(*) FROM [putgeo-server].[BazaLDIMS].[dbo].[{table}] GROUP BY sif_pred')
        result[table+'_companies']=[list(r) for r in c.fetchall()]
        c.execute(f'SELECT god, COUNT_BIG(*) FROM [putgeo-server].[BazaLDIMS].[dbo].[{table}] WHERE god >= %s GROUP BY god ORDER BY god',['2024'])
        result[table+'_recent_years']=[list(r) for r in c.fetchall()]
    c.execute('SELECT COUNT_BIG(*) FROM [putgeo-server].[BazaLDIMS].[dbo].[Godmor] g LEFT JOIN fleet_employee e ON e.employee_code=g.rasif WHERE g.god=%s AND e.id IS NULL',['2026'])
    result['annual_allowance_2026_missing_employee']=c.fetchone()[0]
    c.execute('SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE FROM [putgeo-server].[BazaLDIMS].INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME IN (%s,%s) ORDER BY TABLE_NAME,ORDINAL_POSITION',['Zarada','Zarada1'])
    result['possible_payroll_source_columns']=[list(r) for r in c.fetchall()]
print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
(ROOT/'izvestaji/provera_hr_bolovanja_prikaz_20260911.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
