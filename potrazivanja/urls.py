from django.urls import path
from . import views
from . import views_operations as ops
from . import views_files

app_name = "potrazivanja"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("partner/<int:pk>/", views.partner_detail, name="partner_detail"),
    path("podaci/", views.table_data, name="table_data"),
    path("sinhronizacija/", views.sync_status, name="sync_status"),
    path('partnerzy/', ops.partner_options, name='partner_options'),
    path('kontakty/', ops.contact_options, name='contact_options'),
    path('partner/<int:pk>/oznaki/', ops.profile_edit, name='profile_edit'),
    path('partner/<int:pk>/provera/', ops.review_toggle, name='review_toggle'),
    path('unos/<str:kind>/', ops.record_edit, name='record_create'),
    path('izmena/<str:kind>/<int:pk>/', ops.record_edit, name='record_update'),
    path('arhiva/<str:kind>/<int:pk>/', ops.record_archive, name='record_archive'),
    path('postupak/<int:pk>/', ops.legal_detail, name='legal_detail'),
    path('postupak/<int:case_pk>/promena/', ops.legal_event_edit, name='legal_event_create'),
    path('postupak/<int:case_pk>/promena/<int:pk>/', ops.legal_event_edit, name='legal_event_update'),
    path('postupak/<int:case_pk>/arhiva/<int:pk>/', ops.legal_event_archive, name='legal_event_archive'),
    path('dokument/<int:pk>/stampa/', ops.notice_print, name='notice_print'),
    path('izvoz/', views_files.export_table, name='export'),
    path('uvoz-opomena/', views_files.import_notices, name='notice_import'),
]
