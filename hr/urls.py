from django.urls import path

from .views import MyWorkTimeSheetView, WorkTimeSheetPrintView
from .absence_views import SickLeaveImportView, SickLeaveListView
from .catalog_views import WorkTimeCatalogView, WorkTimeCatalogEditView

app_name = "hr"

urlpatterns = [
    path("sifrarnici/elementi-rl/", WorkTimeCatalogView.as_view(), name="work_time_catalog"),
    path("sifrarnici/<str:kind>/novo/", WorkTimeCatalogEditView.as_view(), name="work_time_catalog_create"),
    path("sifrarnici/<str:kind>/<int:pk>/", WorkTimeCatalogEditView.as_view(), name="work_time_catalog_edit"),
    path("bolovanja/", SickLeaveListView.as_view(), name="sick_leave_list"),
    path("bolovanja/uvoz/", SickLeaveImportView.as_view(), name="sick_leave_import"),
    path("radna-lista/", MyWorkTimeSheetView.as_view(), name="work_time_sheet"),
    path("zaposleni/<int:employee_pk>/radna-lista/", MyWorkTimeSheetView.as_view(), name="employee_work_time_sheet"),
    path("radna-lista/<int:pk>/stampa/", WorkTimeSheetPrintView.as_view(), name="work_time_sheet_print"),
]
