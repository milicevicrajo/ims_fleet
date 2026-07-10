from django.urls import path

from .views import MyWorkTimeSheetView, WorkTimeSheetPrintView

app_name = "hr"

urlpatterns = [
    path("radna-lista/", MyWorkTimeSheetView.as_view(), name="work_time_sheet"),
    path("radna-lista/<int:pk>/stampa/", WorkTimeSheetPrintView.as_view(), name="work_time_sheet_print"),
]
