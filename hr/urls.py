from django.urls import path

from .views import MyWorkTimeSheetView, WorkTimeSheetPrintView
from .absence_views import SickLeaveImportView, SickLeaveListView
from .catalog_views import WorkTimeCatalogView, WorkTimeCatalogEditView
from .annual_leave_views import AnnualLeaveListView, annual_leave_sync_view
from .evaluation_views import (EvaluationListView, EvaluationCreateView, EvaluationDetailView, EvaluationPrintView,
    EvaluationCatalogView, EvaluationCatalogEditView, evaluation_approve_view, evaluation_bulk_approve_view)

app_name = "hr"

urlpatterns = [
    path("ocenjivanje/", EvaluationListView.as_view(), name="evaluation_list"),
    path("ocenjivanje/novo/", EvaluationCreateView.as_view(), name="evaluation_create"),
    path("ocenjivanje/saglasnost/", evaluation_bulk_approve_view, name="evaluation_bulk_approve"),
    path("ocenjivanje/<int:pk>/", EvaluationDetailView.as_view(), name="evaluation_detail"),
    path("ocenjivanje/<int:pk>/stampa/", EvaluationPrintView.as_view(), name="evaluation_print"),
    path("ocenjivanje/<int:pk>/saglasnost/", evaluation_approve_view, name="evaluation_approve"),
    path("ocenjivanje/sifrarnik/", EvaluationCatalogView.as_view(), name="evaluation_catalog"),
    path("ocenjivanje/sifrarnik/<str:kind>/novo/", EvaluationCatalogEditView.as_view(), name="evaluation_catalog_create"),
    path("ocenjivanje/sifrarnik/<str:kind>/<int:pk>/", EvaluationCatalogEditView.as_view(), name="evaluation_catalog_edit"),
    path("godisnji-odmori/", AnnualLeaveListView.as_view(), name="annual_leave_list"),
    path("godisnji-odmori/sinhronizacija/", annual_leave_sync_view, name="annual_leave_sync"),
    path("sifrarnici/elementi-rl/", WorkTimeCatalogView.as_view(), name="work_time_catalog"),
    path("sifrarnici/<str:kind>/novo/", WorkTimeCatalogEditView.as_view(), name="work_time_catalog_create"),
    path("sifrarnici/<str:kind>/<int:pk>/", WorkTimeCatalogEditView.as_view(), name="work_time_catalog_edit"),
    path("bolovanja/", SickLeaveListView.as_view(), name="sick_leave_list"),
    path("bolovanja/uvoz/", SickLeaveImportView.as_view(), name="sick_leave_import"),
    path("radna-lista/", MyWorkTimeSheetView.as_view(), name="work_time_sheet"),
    path("zaposleni/<int:employee_pk>/radna-lista/", MyWorkTimeSheetView.as_view(), name="employee_work_time_sheet"),
    path("radna-lista/<int:pk>/stampa/", WorkTimeSheetPrintView.as_view(), name="work_time_sheet_print"),
]
