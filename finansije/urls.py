from django.urls import path
from . import views, bank_views

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
