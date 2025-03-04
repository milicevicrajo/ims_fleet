from django.urls import path
from .views import *
from fleet import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, register_converter
class FloatConverter:
    regex = r'\d+(\.\d+)?'
    def to_python(self, value):
        return float(value)
    def to_url(self, value):
        return str(value)

register_converter(FloatConverter, 'float')

urlpatterns = [
    path('vozila/', VehicleListView.as_view(), name='vehicle_list'),
    path('vehicle/<int:pk>/', VehicleDetailView.as_view(), name='vehicle_detail'),
    path('vozila/novo/', VehicleCreateView.as_view(), name='vehicle_create'),
    path('vozila/izmeni/<int:pk>/', VehicleUpdateView.as_view(), name='vehicle_update'),
    path('vozila/<int:pk>/', VehicleDetailView.as_view(), name='vehicle_detail'),
    path('vozila/obrisi/<int:pk>/', VehicleDeleteView.as_view(), name='vehicle_delete'),

    path('saobracajne-dozvole/', TrafficCardListView.as_view(), name='trafficcard_list'),
    path('saobracajne-dozvole/novo/', TrafficCardCreateView.as_view(), name='trafficcard_create'),
    path('saobracajne-dozvole/izmeni/<int:pk>/', TrafficCardUpdateView.as_view(), name='trafficcard_update'),
    path('saobracajne-dozvole/<int:pk>/', TrafficCardDetailView.as_view(), name='trafficcard_detail'),
    path('saobracajne-dozvole/obrisi/<int:pk>/', TrafficCardDeleteView.as_view(), name='trafficcard_delete'),

    path('sifre-poslova/', JobCodeListView.as_view(), name='jobcode_list'),
    path('sifre-poslova/novo/', JobCodeCreateView.as_view(), name='jobcode_create'),
    path('sifre-poslova/izmeni/<int:pk>/', JobCodeUpdateView.as_view(), name='jobcode_update'),
    path('sifre-poslova/<int:pk>/', JobCodeDetailView.as_view(), name='jobcode_detail'),
    path('sifre-poslova/obrisi/<int:pk>/', JobCodeDeleteView.as_view(), name='jobcode_delete'),

    path('zakupi/', LeaseListView.as_view(), name='lease_list'),
    path('zakupi/novo/', LeaseCreateView.as_view(), name='lease_create'),
    path('zakupi/izmeni/<int:pk>/', LeaseUpdateView.as_view(), name='lease_update'),
    path('zakupi/<int:pk>/', LeaseDetailView.as_view(), name='lease_detail'),
    path('zakupi/obrisi/<int:pk>/', LeaseDeleteView.as_view(), name='lease_delete'),

    path('azuriranje', fetch_vehicle_value_view, name='fetch_vehicle_value'),
    
    path('polise/', PolicyListView.as_view(), name='policy_list'),
    path('polise/nedovrseno/', PolicyFixingListView.as_view(), name='policy_fixing_list'),
    path('dopuna-polise/<int:pk>/', DraftPolicyUpdateView.as_view(), name='draft_policy_update'),
    path('polise/novo/', PolicyCreateView.as_view(), name='policy_create'),
    path('polise/izmeni/<int:pk>/', PolicyUpdateView.as_view(), name='policy_update'),
    path('polise/<int:pk>/', PolicyDetailView.as_view(), name='policy_detail'),
    path('polise/obrisi/<int:pk>/', PolicyDeleteView.as_view(), name='policy_delete'),
    path('polise/istek/', ExpiringAndNotRenewedPolicyView.as_view(), name='expiring_and_not_renewed_policies'),

    path('potrosnja-goriva/', FuelConsumptionListView.as_view(), name='fuelconsumption_list'),
    path('fuel-transactions/', FuelTransactionsListView.as_view(), name='fuel_transactions_list'),
    path('potrosnja-goriva/novo/', FuelConsumptionCreateView.as_view(), name='fuelconsumption_create'),
    path('potrosnja-goriva/izmeni/<int:pk>/', FuelConsumptionUpdateView.as_view(), name='fuelconsumption_update'),
    path('potrosnja-goriva/<int:pk>/', FuelConsumptionDetailView.as_view(), name='fuelconsumption_detail'),
    path('potrosnja-goriva/obrisi/<int:pk>/', FuelConsumptionDeleteView.as_view(), name='fuelconsumption_delete'),

    path('zaposleni/', EmployeeListView.as_view(), name='employee_list'),
    path('zaposleni/novo/', EmployeeCreateView.as_view(), name='employee_create'),
    path('zaposleni/izmeni/<int:pk>/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('zaposleni/<int:pk>/', EmployeeDetailView.as_view(), name='employee_detail'),
    path('zaposleni/obrisi/<int:pk>/', EmployeeDeleteView.as_view(), name='employee_delete'),

    path('incidenti/', IncidentListView.as_view(), name='incident_list'),
    path('incidenti/novo/', IncidentCreateView.as_view(), name='incident_create'),
    path('incidenti/izmeni/<int:pk>/', IncidentUpdateView.as_view(), name='incident_update'),
    path('incidenti/<int:pk>/', IncidentDetailView.as_view(), name='incident_detail'),
    path('incidenti/obrisi/<int:pk>/', IncidentDeleteView.as_view(), name='incident_delete'),

    path('putni-nalozi/', PutniNalogListView.as_view(), name='putninalog_list'),
    path('putni-nalozi/novo/', PutniNalogCreateView.as_view(), name='putninalog_create'),
    path('putni-nalozi/izmeni/<int:pk>/', PutniNalogUpdateView.as_view(), name='putninalog_update'),
    path('putni-nalozi/<int:pk>/', PutniNalogDetailView.as_view(), name='putninalog_detail'),
    path('putni-nalozi/obrisi/<int:pk>/', PutniNalogDeleteView.as_view(), name='putninalog_delete'),
    path('putni-nalog/<int:pk>/download/', download_travel_order_excel, name='download_travel_order_excel'),

    path('tipovi-servisa/', ServiceTypeListView.as_view(), name='servicetype_list'),
    path('tipovi-servisa/novo/', ServiceTypeCreateView.as_view(), name='servicetype_create'),
    path('tipovi-servisa/izmeni/<int:pk>/', ServiceTypeUpdateView.as_view(), name='servicetype_update'),
    path('tipovi-servisa/<int:pk>/', ServiceTypeDetailView.as_view(), name='servicetype_detail'),
    path('tipovi-servisa/obrisi/<int:pk>/', ServiceTypeDeleteView.as_view(), name='servicetype_delete'),

    
    path('servisi/', ServiceListView.as_view(), name='service_list'),
    
    # path('servisi/novo/', ServiceCreateView.as_view(), name='service_create'),
    # path('servisi/izmeni/<int:pk>/', ServiceUpdateView.as_view(), name='service_update'),
    # path('servisi/<int:pk>/', ServiceDetailView.as_view(), name='service_detail'),
    # path('servisi/obrisi/<int:pk>/', ServiceDeleteView.as_view(), name='service_delete'),

    path('service-transactions/', ServiceTransactionListView.as_view(), name='service_transaction_list'),
    path('servisi/nedovrseno/', ServiceTransactionFixingListView.as_view(), name='service_fixing_list'),
    path('servisi-nedovrseno/<int:pk>/edit/', DraftServiceTransactionUpdateView.as_view(), name='draft_service_transaction_update'),
    path('service-transactions/add/', ServiceTransactionCreateView.as_view(), name='service_transaction_add'),
    path('service-transactions/<int:pk>/edit/', ServiceTransactionUpdateView.as_view(), name='service_transaction_update'),
    path('service-transactions/<int:pk>/delete/', ServiceTransactionDeleteView.as_view(), name='service_transaction_delete'),

    # FETCHING
    path('fetch-data/', views.fetch_data_view, name='fetch_data'),
    path('fetch-policies/', views.fetch_policy_data_view, name='fetch_policies'),
    path('fetch-services/', views.fetch_service_data_view, name='fetch_services'),
    path('fetch-requisitions/', views.fetch_requisition_data_view, name='fetch_requisitions'),
    path('fetch-vehicle-value/', views.fetch_vehicle_value_view, name='fetch_vehicle_value'),
    path('fetch-lease-interest/', views.fetch_lease_interest_data, name='fetch_lease_interest'),

    path('requisitions/', RequisitionListView.as_view(), name='requisition_list'),
    path('requisitions/nedovrseno/', RequisitionFixingListView.as_view(), name='requisition_fixing_list'),
    path('requisitions-nedovrseno/<int:pk>/edit/', DraftRequisitionUpdateView.as_view(), name='draft_requisition_update'),
    path('requisitions/create/', RequisitionCreateView.as_view(), name='requisition_create'),
    path('requisitions/<int:pk>/edit/', RequisitionUpdateView.as_view(), name='requisition_update'),
    path('requisitions/<int:pk>/delete/', RequisitionDeleteView.as_view(), name='requisition_delete'),
    
    # IZVESTAJI
    path('izvestaji/', views.reports_index, name='reports_index'),
    path('izvestaji/omv_putnicka/', views.omv_putnicka_view, name='omv_putnicka'),
    path('izvestaji/nis_putnicka/', views.nis_putnicka_view, name='nis_putnicka'),
    path('izvestaji/omv_teretna/', views.omv_teretna_view, name='omv_teretna'),
    path('izvestaji/kasko_rate/', views.kasko_rate_view, name='kasko_rate'),
    path('izvestaji/zatvoreni_putni/', views.zatvoren_putni_view, name='zatvoreni_putni'),
    path('izvestaji/magacin/', views.magacin_view, name='magacin'),
    path('izvestaji/otpis/', views.otpis_view, name='otpis'),
    path('izvestaji/tro_gorivo_mesec/', views.tro_gorivo_mesec_view, name='tro_gorivo_mesec'),
    path('izvestaji/troskovi_svi/', views.troskovi_svi_view, name='troskovi_svi'),
    path('izvestaji/tro_pracenja_vozila/', views.tro_pracenja_vozila_view, name='tro_pracenja_vozila'),
    path('izvestaji/troskovi_tahograf/', views.tahograf_partneri_view, name='troskovi_tahograf'),
    path('izvestaji/tro_zarade/', views.tro_zarade_view, name='tro_zarade'),
    path('izvestaji/tro_parking/', views.tro_parking_view, name='tro_parking'),
    path('izvestaji/potrazivanje_ddor/', views.potrazivanje_ddor_view, name='potrazivanje_ddor'),
    path('izvestaji/po_dobavljacima/', views.po_dobavljacima_view, name='po_dobavljacima'),

    path('dugovanja/', lista_dugovanja, name='lista_dugovanja'),
    path('partner/<int:sif_par>/', detalji_partner, name='detalji_partner'),
    path('dugovanja_po_bucketima/', lista_dugovanja_po_bucketima, name='lista_dugovanja_po_bucketima'),
    # path('dugovanje/<int:sif_par>/', detalji_dugovanja, name='detalji_dugovanja'),

    path('kontakti/', lista_kontakata, name='lista_kontakata'),
    path('kontakti/dodaj/', dodaj_kontakt, name='dodaj_kontakt'),
    path('kontakti/izmeni/<float:sif_par>/', izmeni_kontakt, name='izmeni_kontakt'),
    path('kontakti/obrisi/<float:sif_par>/', obrisi_kontakt, name='obrisi_kontakt'),

    path('napomene/', lista_napomena, name='lista_napomena'),
    path('napomene/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_napomenu, name='dodaj_napomenu'),
    path('napomene/izmeni/<int:id>/', izmeni_napomenu, name='izmeni_napomenu'),
    path('napomene/obrisi/<int:id>/', obrisi_napomenu, name='obrisi_napomenu'),

    path('opomene/', lista_opomena, name='lista_opomena'),
    path('opomene/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_opomenu, name='dodaj_opomenu'),
    path('opomene/izmeni/<int:id>/', izmeni_opomenu, name='izmeni_opomenu'),
    path('opomene/obrisi/<int:id>/', obrisi_opomenu, name='obrisi_opomenu'),

    path('poziv_pismo/', lista_pozivnih_pisma, name='lista_pozivnih_pisma'),
    path('poziv_pismo/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_poziv_pismo, name='dodaj_poziv_pismo'),
    path('poziv_pismo/izmeni/<int:id>/', izmeni_poziv_pismo, name='izmeni_poziv_pismo'),
    path('poziv_pismo/obrisi/<int:id>/', obrisi_poziv_pismo, name='obrisi_poziv_pismo'),

    path('pozivi_tel/', lista_poziva, name='lista_poziva'),
    path('pozivi_tel/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_poziv, name='dodaj_poziv'),
    path('pozivi_tel/izmeni/<int:id>/', izmeni_poziv, name='izmeni_poziv'),
    path('pozivi_tel/obrisi/<int:id>/', obrisi_poziv, name='obrisi_poziv'),

    path('tuzbe/', lista_tuzbi, name='lista_tuzbi'),
    path('tuzbe/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_tuzbu, name='dodaj_tuzbu'),
    path('tuzbe/izmeni/<int:id>/', izmeni_tuzbu, name='izmeni_tuzbu'),
    path('tuzbe/obrisi/<int:id>/', obrisi_tuzbu, name='obrisi_tuzbu'),
    
    path('', views.dashboard, name='dashboard'),
    path('center_statistics/<str:center_code>/', center_statistics, name='center_statistics'),
    
    path('users/', UserListView.as_view(), name='user_list'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

# Dodavanje URL pravila za medijske fajlove tokom razvoja
if settings.DEBUG:  # Ovo će raditi samo dok je DEBUG=True
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)