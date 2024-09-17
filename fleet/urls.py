from django.urls import path
from .views import *
from fleet import views
from django.contrib.auth import views as auth_views

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

    
    path('polise/', PolicyListView.as_view(), name='policy_list'),
    path('policies/nedovrseno/', PolicyFixingListView.as_view(), name='policy_fixing_list'),
    path('polise/novo/', PolicyCreateView.as_view(), name='policy_create'),
    path('polise/izmeni/<int:pk>/', PolicyUpdateView.as_view(), name='policy_update'),
    path('polise/<int:pk>/', PolicyDetailView.as_view(), name='policy_detail'),
    path('polise/obrisi/<int:pk>/', PolicyDeleteView.as_view(), name='policy_delete'),

    path('potrosnja-goriva/', FuelConsumptionListView.as_view(), name='fuelconsumption_list'),
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
    path('service-transactions/add/', ServiceTransactionCreateView.as_view(), name='service_transaction_add'),
    path('service-transactions/<int:pk>/edit/', ServiceTransactionUpdateView.as_view(), name='service_transaction_update'),
    path('service-transactions/<int:pk>/delete/', ServiceTransactionDeleteView.as_view(), name='service_transaction_delete'),

    # FETCHING
    path('fetch-policies/', views.fetch_policies_view, name='fetch_policies'),
    path('fetch-services/', views.fetch_service_data_view, name='fetch_services'),
    path('fetch-requisitions/', fetch_requisition_data_view, name='fetch_requisitions'),
    path('fetch-vehicle-value/', fetch_vehicle_value_view, name='fetch_vehicle_value'),
    path('fetch-lease-interest/', fetch_lease_interest_data, name='fetch_lease_interest'),

    path('requisitions/', RequisitionListView.as_view(), name='requisition_list'),
    path('requisitions/nedovrseno/', RequisitionFixingListView.as_view(), name='requisition_fixing_list'),
    path('requisitions/create/', RequisitionCreateView.as_view(), name='requisition_create'),
    path('requisitions/<int:pk>/edit/', RequisitionUpdateView.as_view(), name='requisition_update'),
    path('requisitions/<int:pk>/delete/', RequisitionDeleteView.as_view(), name='requisition_delete'),
    
    path('', views.dashboard, name='dashboard'),

    path('users/', UserListView.as_view(), name='user_list'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]