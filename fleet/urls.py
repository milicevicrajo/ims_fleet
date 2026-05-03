from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path, register_converter
from hr.views import (
    EmployeeCreateView,
    EmployeeDeleteView,
    EmployeeDetailView,
    EmployeeListView,
    EmployeeUpdateView,
)

from .views.fuel import (
    FuelConsumptionCreateView,
    FuelConsumptionDeleteView,
    FuelConsumptionDetailView,
    FuelConsumptionListView,
    FuelConsumptionUpdateView,
    FuelTransactionsListView,
)
from .views.insurance import (
    DraftInsuranceUpdateView,
    InsuranceCreateView,
    InsuranceDeleteView,
    InsuranceDetailView,
    InsuranceFixingListView,
    InsuranceListView,
    InsuranceUpdateView,
    fetch_ddor_data_view,
    insurance_fetch_ddor_view,
    insurance_migrate_one_view,
)
from .views.reference import (
    JobCodeCreateView,
    JobCodeDeleteView,
    JobCodeDetailView,
    JobCodeListView,
    JobCodeUpdateView,
    KontoCreateView,
    KontoDeleteView,
    KontoListView,
    KontoUpdateView,
    OrganizationalUnitCreateView,
    OrganizationalUnitListView,
    OrganizationalUnitUpdateView,
    TrafficCardCreateView,
    TrafficCardDeleteView,
    TrafficCardDetailView,
    TrafficCardListView,
    TrafficCardUpdateView,
    VehicleTenderDocumentCreateView,
    VehicleTenderDocumentDeleteView,
    VehicleTenderDocumentDetailView,
    VehicleTenderDocumentListView,
    VehicleTenderDocumentUpdateView,
)
from .views.lease import (
    LeaseCreateView,
    LeaseDeleteView,
    LeaseDetailView,
    LeaseListView,
    LeaseMonthlyCostsView,
    LeaseUpdateView,
    export_leases_to_excel,
)
from .views.policy import (
    DraftPolicyUpdateView,
    ExpiringAndNotRenewedPolicyView,
    PoliciesMonthlyCostsView,
    PolicyCreateView,
    PolicyDeleteView,
    PolicyDetailView,
    PolicyFixingListView,
    PolicyListView,
    PolicyUpdateView,
    policies_monthly_costs_csv,
)
from .views.putni_nalozi import (
    PutniNalogCreateView,
    PutniNalogDeleteView,
    PutniNalogDetailView,
    PutniNalogListView,
    PutniNalogPrintView,
    PutniNalogUpdateView,
    putninalog_print_list,
    putninalog_set_opravdan,
    putninalog_storniraj,
)
from .views.services import (
    DraftRequisitionUpdateView,
    DraftServiceTransactionUpdateView,
    RequisitionCreateView,
    RequisitionDeleteView,
    RequisitionDetailView,
    RequisitionFixingListView,
    RequisitionListView,
    RequisitionUpdateView,
    ServiceListView,
    ServiceMonthlyCostsView,
    ServiceTransactionCreateView,
    ServiceTransactionDeleteView,
    ServiceTransactionFixingListView,
    ServiceTransactionListView,
    ServiceTransactionUpdateView,
    ServiceTypeCreateView,
    ServiceTypeDeleteView,
    ServiceTypeDetailView,
    ServiceTypeListView,
    ServiceTypeUpdateView,
    fetch_requisition_data_view,
    fetch_service_data_view,
    service_monthly_costs_csv,
)
from .views.sync import (
    fetch_data_view,
    fetch_lease_interest_data,
    fetch_policy_data_view,
    fetch_vehicle_value_view,
    import_nis_excel_view,
    import_omv_putnicka_csv_view,
    import_omv_teretna_csv_view,
)
from .views.vehicles import (
    VehicleCreateView,
    VehicleDeleteView,
    VehicleDetailView,
    VehicleListView,
    VehicleTogleStatusView,
    VehicleUpdateView,
    vehicle_export_csv,
)
from .views.garaza import (
    GarazaHomeView,
    KvarCreateView,
    KvarDeleteView,
    KvarDetailView,
    KvarIMSListView,
    KvarListView,
    KvarPrintView,
    KvarTrebovanjeView,
    KvarUpdateView,
    KvarVanIMSListView,
    KvarWorkOrderView,
    ProcurementRequestCreateView,
    ProcurementRequestDetailView,
    ProcurementRequestListView,
    ProcurementRequestPrintView,
    VehicleTravelOrderCloseView,
    VehicleTravelOrderCreateView,
    VehicleTravelOrderDeleteView,
    VehicleTravelOrderDetailView,
    VehicleTravelOrderFuelReportView,
    VehicleTravelOrderListView,
    VehicleTravelOrderRequestView,
    VehicleTravelOrderUpdateView,
)
from .views.users import UserListView
from .views.reports import (
    export_nis_putnicka_excel,
    export_nis_teretna_excel,
    export_omv_putnicka_excel,
    export_omv_teretna_excel,
    kasko_rate_view,
    magacin_view,
    nis_putnicka_view,
    nis_teretna_view,
    omv_putnicka_view,
    omv_teretna_view,
    otpis_view,
    po_dobavljacima_view,
    potrazivanje_ddor_view,
    reports_index,
    tahograf_partneri_view,
    tro_gorivo_mesec_view,
    tro_parking_view,
    tro_pracenja_vozila_view,
    tro_zarade_view,
    troskovi_svi_view,
    zatvoren_putni_view,
)
from .views import center_statistics, dashboard, fleet_analytics


class FloatConverter:
    regex = r'\d+(\.\d+)?'
    def to_python(self, value):
        return float(value)
    def to_url(self, value):
        return str(value)

register_converter(FloatConverter, 'float')

urlpatterns = [
    path('vozila/', VehicleListView.as_view(), name='vehicle_list'),
    path('vozila/export/csv/', vehicle_export_csv, name='vehicle_export_csv'),
    path('vozila/novo/', VehicleCreateView.as_view(), name='vehicle_create'),
    path('vozila/izmeni/<int:pk>/', VehicleUpdateView.as_view(), name='vehicle_update'),
    path('vozila/<int:pk>/', VehicleDetailView.as_view(), name='vehicle_detail'),
    path('vozila/tender-dokumenti/', VehicleTenderDocumentListView.as_view(), name='vehicle_tender_document_list'),
    path('vozila/tender-dokumenti/novo/<int:vehicle_id>/', VehicleTenderDocumentCreateView.as_view(), name='vehicle_tender_document_create_for_vehicle'),
    path('vozila/tender-dokumenti/novo/', VehicleTenderDocumentCreateView.as_view(), name='vehicle_tender_document_create'),
    path('vozila/tender-dokumenti/izmeni/<int:pk>/', VehicleTenderDocumentUpdateView.as_view(), name='vehicle_tender_document_update'),
    path('vozila/tender-dokumenti/obrisi/<int:pk>/', VehicleTenderDocumentDeleteView.as_view(), name='vehicle_tender_document_delete'),
    path('vozila/tender-dokumenti/<int:pk>/', VehicleTenderDocumentDetailView.as_view(), name='vehicle_tender_document_detail'),
    path('vozila/obrisi/<int:pk>/', VehicleDeleteView.as_view(), name='vehicle_delete'),
    path('vozila/<int:pk>/toggle-status', VehicleTogleStatusView.as_view(), name='vehicle_toggle_status'),

    path('saobracajne-dozvole/', TrafficCardListView.as_view(), name='trafficcard_list'),
    path('saobracajne-dozvole/novo/', TrafficCardCreateView.as_view(), name='trafficcard_create_manual'),
    path('saobracajne-dozvole/novo/<int:vehicle_id>/', TrafficCardCreateView.as_view(), name='trafficcard_create'),
    path('saobracajne-dozvole/izmeni/<int:pk>/', TrafficCardUpdateView.as_view(), name='trafficcard_update'),
    path('saobracajne-dozvole/<int:pk>/', TrafficCardDetailView.as_view(), name='trafficcard_detail'),
    path('saobracajne-dozvole/obrisi/<int:pk>/', TrafficCardDeleteView.as_view(), name='trafficcard_delete'),

    path('sifre-poslova/', JobCodeListView.as_view(), name='jobcode_list'),
    # path('sifre-poslova/novo/', JobCodeCreateView.as_view(), name='jobcode_create'),
    path('sifre-poslova/novo/<int:vehicle_id>/', JobCodeCreateView.as_view(), name='jobcode_create'),
    path('sifre-poslova/izmeni/<int:pk>/', JobCodeUpdateView.as_view(), name='jobcode_update'),
    path('sifre-poslova/<int:pk>/', JobCodeDetailView.as_view(), name='jobcode_detail'),
    path('sifre-poslova/obrisi/<int:pk>/', JobCodeDeleteView.as_view(), name='jobcode_delete'),

    path('zakupi/', LeaseListView.as_view(), name='lease_list'),
    path('zakupi/novo/', LeaseCreateView.as_view(), name='lease_create'),
    path('zakupi/izmeni/<int:pk>/', LeaseUpdateView.as_view(), name='lease_update'),
    path('zakupi/<int:pk>/', LeaseDetailView.as_view(), name='lease_detail'),
    path('zakupi/obrisi/<int:pk>/', LeaseDeleteView.as_view(), name='lease_delete'),
    path('export-leases/', export_leases_to_excel, name='export_leases'),

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

    path('garaza/', GarazaHomeView.as_view(), name='garaza_home'),
    path('garaza/kvarovi/', KvarListView.as_view(), name='kvar_list'),
    path('garaza/kvarovi/novo/', KvarCreateView.as_view(), name='kvar_create'),
    path('garaza/kvarovi/izmena/<int:pk>/', KvarUpdateView.as_view(), name='kvar_update'),
    path('garaza/kvarovi/<int:pk>/', KvarDetailView.as_view(), name='kvar_detail'),
    path('garaza/kvarovi/obrisi/<int:pk>/', KvarDeleteView.as_view(), name='kvar_delete'),
    path('garaza/kvarovi/<int:pk>/prijava/', KvarPrintView.as_view(), name='kvar_print'),
    path('garaza/kvarovi/<int:pk>/radni-nalog/', KvarWorkOrderView.as_view(), name='kvar_workorder'),
    path('garaza/kvarovi/ims/', KvarIMSListView.as_view(), name='kvar_list_ims'),
    path('garaza/kvarovi/van-ims/', KvarVanIMSListView.as_view(), name='kvar_list_van_ims'),
    path('garaza/kvarovi/<int:pk>/trebovanje/', KvarTrebovanjeView.as_view(), name='kvar_trebovanje'),

    # Zahtevi za nabavku (GZN)
    path('garaza/gzn/', ProcurementRequestListView.as_view(), name='gzn_list'),
    path('garaza/gzn/novo/', ProcurementRequestCreateView.as_view(), name='gzn_create'),
    path('garaza/gzn/<int:pk>/', ProcurementRequestDetailView.as_view(), name='gzn_detail'),
    path('garaza/gzn/<int:pk>/stampaj/', ProcurementRequestPrintView.as_view(), name='gzn_print'),

    path('garaza/putni-nalozi-vozila/otvoreni/', VehicleTravelOrderListView.as_view(), {'status': 'open'}, name='vehicle_travel_order_open_list'),
    path('garaza/putni-nalozi-vozila/zatvoreni/', VehicleTravelOrderListView.as_view(), {'status': 'closed'}, name='vehicle_travel_order_closed_list'),
    path('garaza/putni-nalozi-vozila/novo/', VehicleTravelOrderCreateView.as_view(), name='vehicle_travel_order_create'),
    path('garaza/putni-nalozi-vozila/<int:pk>/', VehicleTravelOrderDetailView.as_view(), name='vehicle_travel_order_detail'),
    path('garaza/putni-nalozi-vozila/<int:pk>/obracun/', VehicleTravelOrderFuelReportView.as_view(), name='vehicle_travel_order_fuel_report'),
    path('garaza/putni-nalozi-vozila/<int:pk>/izmena/', VehicleTravelOrderUpdateView.as_view(), name='vehicle_travel_order_update'),
    path('garaza/putni-nalozi-vozila/<int:pk>/zatvori/', VehicleTravelOrderCloseView.as_view(), name='vehicle_travel_order_close'),
    path('garaza/putni-nalozi-vozila/<int:pk>/zahtev/', VehicleTravelOrderRequestView.as_view(), name='vehicle_travel_order_request'),
    path('garaza/putni-nalozi-vozila/<int:pk>/brisanje/', VehicleTravelOrderDeleteView.as_view(), name='vehicle_travel_order_delete'),

    path('putni-nalozi/', PutniNalogListView.as_view(), name='putninalog_list'),
    path('putni-nalozi/print-list/', putninalog_print_list, name='putninalog_print_list'),
    path('putni-nalozi/novo/', PutniNalogCreateView.as_view(), name='putninalog_create'),
    path('putni-nalozi/izmeni/<int:pk>/', PutniNalogUpdateView.as_view(), name='putninalog_update'),
    path('putni-nalozi/<int:pk>/opravdan/', putninalog_set_opravdan, name='putninalog_set_opravdan'),
    path('putni-nalozi/<int:pk>/storniraj/', putninalog_storniraj, name='putninalog_storniraj'),
    path('putni-nalozi/<int:pk>/', PutniNalogDetailView.as_view(), name='putninalog_detail'),
    path('putni-nalozi/obrisi/<int:pk>/', PutniNalogDeleteView.as_view(), name='putninalog_delete'),
    path('putni-nalozi/<int:pk>/print/', PutniNalogPrintView.as_view(), name='putninalog_print'),


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
    
    # ORGANIZACIJA
    path('organizacione-jedinice', OrganizationalUnitListView.as_view(), name='organizational_unit_list'),
    path('organizacione-jedinice/novo/', OrganizationalUnitCreateView.as_view(), name='organizational_unit_create'),
    path('organizacione-jedinice/<int:pk>/izmeni/', OrganizationalUnitUpdateView.as_view(), name='organizational_unit_update'),
    # path('<int:pk>/delete/', OrganizationalUnitDeleteView.as_view(), name='organizational_unit_delete'),

    # FETCHING
    path('fetch-data/', fetch_data_view, name='fetch_data'),
    path('import-nis-excel/', import_nis_excel_view, name='import_nis_excel'),
    path('import-omv-putnicka-csv/', import_omv_putnicka_csv_view, name='import_omv_putnicka_csv'),
    path('import-omv-teretna-csv/', import_omv_teretna_csv_view, name='import_omv_teretna_csv'),
    path('fetch-policies/', fetch_policy_data_view, name='fetch_policies'),
    path('fetch-services/', fetch_service_data_view, name='fetch_services'),
    path('fetch-requisitions/', fetch_requisition_data_view, name='fetch_requisitions'),
    path('fetch-vehicle-value/', fetch_vehicle_value_view, name='fetch_vehicle_value'),
    path('fetch-lease-interest/', fetch_lease_interest_data, name='fetch_lease_interest'),

    path('requisitions/', RequisitionListView.as_view(), name='requisition_list'),
    path('requisition/<int:god>/<str:br_dok>/', RequisitionDetailView.as_view(), name='requisition_detail'),
    path('requisitions/nedovrseno/', RequisitionFixingListView.as_view(), name='requisition_fixing_list'),
    path('requisitions-nedovrseno/<int:pk>/edit/', DraftRequisitionUpdateView.as_view(), name='draft_requisition_update'),
    path('requisitions/create/', RequisitionCreateView.as_view(), name='requisition_create'),
    path('requisitions/<int:pk>/edit/', RequisitionUpdateView.as_view(), name='requisition_update'),
    path('requisitions/<int:pk>/delete/', RequisitionDeleteView.as_view(), name='requisition_delete'),

    path("konta/", KontoListView.as_view(), name="konta_list"),
    path("konta/novo/", KontoCreateView.as_view(), name="konta_create"),
    path("konta/<str:pk>/izmena/", KontoUpdateView.as_view(), name="konta_update"),
    path("konta/<str:pk>/brisanje/", KontoDeleteView.as_view(), name="konta_delete"),
    
    # IZVESTAJI 
    path('izvestaji/', reports_index, name='reports_index'),
    path('izvestaji/omv_putnicka/', omv_putnicka_view, name='omv_putnicka'),
    path('izvestaji/omv_putnicka/export', export_omv_putnicka_excel, name='export_omv_putnicka_excel'),
    path('izvestaji/nis_putnicka/', nis_putnicka_view, name='nis_putnicka'),
    path('izvestaji/nis_putnicka/export', export_nis_putnicka_excel, name='export_nis_putnicka_excel'),
    path('izvestaji/omv_teretna/', omv_teretna_view, name='omv_teretna'),
    path('izvestaji/omv_teretna/export', export_omv_teretna_excel, name='export_omv_teretna_excel'),
    path('export-nis-teretna/', export_nis_teretna_excel, name='export_nis_teretna'),
    path('izvestaji/nis_teretna/', nis_teretna_view, name='nis_teretna'),
    path('izvestaji/kasko_rate/', kasko_rate_view, name='kasko_rate'),
    path('izvestaji/zatvoreni_putni/', zatvoren_putni_view, name='zatvoreni_putni'),
    path('izvestaji/magacin/', magacin_view, name='magacin'),
    path('izvestaji/otpis/', otpis_view, name='otpis'),
    path('izvestaji/tro_gorivo_mesec/', tro_gorivo_mesec_view, name='tro_gorivo_mesec'),
    path('izvestaji/troskovi_svi/', troskovi_svi_view, name='troskovi_svi'),
    path('izvestaji/tro_pracenja_vozila/', tro_pracenja_vozila_view, name='tro_pracenja_vozila'),
    path('izvestaji/troskovi_tahograf/', tahograf_partneri_view, name='troskovi_tahograf'),
    path('izvestaji/tro_zarade/', tro_zarade_view, name='tro_zarade'),
    path('izvestaji/tro_parking/', tro_parking_view, name='tro_parking'),
    path('izvestaji/potrazivanje_ddor/', potrazivanje_ddor_view, name='potrazivanje_ddor'),
    path('izvestaji/po_dobavljacima/', po_dobavljacima_view, name='po_dobavljacima'),    
    path('izvestaji/policies-monthly-costs/', PoliciesMonthlyCostsView.as_view(), name='policies_monthly_costs'),
    path('izvestaji/policies-monthly-costs.csv', policies_monthly_costs_csv, name='policies_monthly_costs_csv'),

    # Dodan URL za mesečne troškove lizinga (LeaseMonthlyCostsView)
    path('izvestaji/lease-monthly-costs/', LeaseMonthlyCostsView.as_view(), name='lease_monthly_costs'),
    path("reports/service-monthly-costs/", ServiceMonthlyCostsView.as_view(), name="reports_service_monthly_costs"),
    path('reports/services/monthly.csv', service_monthly_costs_csv, name='reports_service_monthly_costs_csv'),
    
    path('', dashboard, name='dashboard'),
    path('analitika/', fleet_analytics, name='fleet_analytics'),
    path('center_statistics/<str:center_code>/', center_statistics, name='center_statistics'),
    
    path('users/', UserListView.as_view(), name='user_list'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Final
    path("insurance/", InsuranceListView.as_view(), name="insurance_list"),
    path("insurance/<int:god>/<str:br_naloga>/", InsuranceDetailView.as_view(), name="insurance_detail"),
    path("insurance/new/", InsuranceCreateView.as_view(), name="insurance_create"),
    path("insurance/<int:pk>/edit/", InsuranceUpdateView.as_view(), name="insurance_update"),
    path("insurance/<int:pk>/delete/", InsuranceDeleteView.as_view(), name="insurance_delete"),

    # Draft
    path("insurance/drafts/", InsuranceFixingListView.as_view(), name="insurance_fixing_list"),
    path("insurance/drafts/<int:pk>/edit/", DraftInsuranceUpdateView.as_view(), name="draft_insurance_update"),
    path("insurance/fetch-ddor/", insurance_fetch_ddor_view, name="insurance_fetch_ddor"),
    path("fetch-ddor/", fetch_ddor_data_view, name="fetch_ddor"),
    path("insurance/migrate-one/<int:draft_id>/<int:vehicle_id>/", insurance_migrate_one_view, name="insurance_migrate_one"),
]

# Dodavanje URL pravila za medijske fajlove tokom razvoja
if settings.DEBUG:  # Ovo će raditi samo dok je DEBUG=True
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
