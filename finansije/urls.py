from django.urls import path
from . import views, bank_views, sef_views

app_name = "finansije"
urlpatterns = [
    path("banke/", bank_views.bank_list, name="bank_list"),
    path("banke/konta/", bank_views.bank_accounts, name="bank_accounts"),
    path("banke/<int:bank_code>/", bank_views.bank_detail, name="bank_detail"),
    path("banke/<int:bank_code>/kontakti/novi/", bank_views.bank_contact_edit, name="bank_contact_edit"),
    path("banke/<int:bank_code>/kontakti/<int:pk>/", bank_views.bank_contact_edit, name="bank_contact_edit"),
    path("banke/<int:bank_code>/kontakti/<int:pk>/obrisi/", bank_views.bank_contact_delete, name="bank_contact_delete"),
    path("banke/<int:bank_code>/menice/predaja/", bank_views.bank_bill_edit, name="bank_bill_edit"),
    path("banke/<int:bank_code>/menice/predaja/<int:pk>/", bank_views.bank_bill_edit, name="bank_bill_edit"),
    path("sef/", sef_views.sef_list, name="sef_list"),
    path("sef/sinhronizacija/", sef_views.sef_sync, name="sef_sync"),
    path("sef/izvoz/", sef_views.sef_izvoz, name="sef_izvoz"),
    path("sef/sinhronizacija/poslednje/", sef_views.sef_sync_poslednje, name="sef_sync_poslednje"),
    path("sef/sinhronizacija/<int:pk>/", sef_views.sef_sync_stanje, name="sef_sync_stanje"),
    path("sef/sinhronizacija/<int:pk>/zaustavi/", sef_views.sef_sync_zaustavi, name="sef_sync_zaustavi"),
    path("sef/<int:pk>/", sef_views.sef_detail, name="sef_detail"),
    path("sef/<int:pk>/pdf/preuzmi/", sef_views.sef_pdf_preuzmi, name="sef_pdf_preuzmi"),
    path("sef/<int:pk>/<str:vrsta>/", sef_views.sef_dokument, name="sef_dokument"),
    path("", views.dashboard, name="dashboard"),
    path("izvestaji/", views.report, name="report"),
    path("izvestaji/sifre-podaci/", views.jobs_data, name="jobs_data"),
    path("posao/", views.job_card, name="job_card"),
    path("posao/tabela/<str:table>/", views.job_table, name="job_table"),
    path("knjizenja/", views.ledger, name="ledger"),
    path("izvoz/", views.export, name="export"),
    path("sinhronizacija/", views.sync_status, name="sync_status"),
    path("sinhronizacija/pokreni/", views.sync_run, name="sync_run"),
    path("sinhronizacija/nalog-z/", views.nalog_z_refresh, name="nalog_z_refresh"),
]
