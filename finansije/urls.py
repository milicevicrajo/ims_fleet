from django.urls import path
from . import views

app_name = "finansije"
urlpatterns = [
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
