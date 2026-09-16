from django.urls import path
from . import views

app_name = "finansije"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("knjizenja/", views.ledger, name="ledger"),
    path("izvoz/", views.export, name="export"),
    path("sinhronizacija/", views.sync_status, name="sync_status"),
]
