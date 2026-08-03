"""Compatibility re-exports for fleet view imports."""

from ..support.fuel import (
    calculate_average_fuel_consumption,
    calculate_average_fuel_consumption_ever,
    date_range_for_datetime_field,
)
from ..support.dashboard import cost_per_km_period_analysis, vehicle_cost_per_km_rows
from .analytics import fleet_analytics
from .center_statistics import center_statistics
from .dashboard import dashboard
from .fuel import (
    FuelConsumptionCreateView,
    FuelConsumptionDeleteView,
    FuelConsumptionDetailView,
    FuelConsumptionListView,
    FuelConsumptionUpdateView,
    FuelTransactionDetailView,
    FuelTransactionsListView,
)
from .kvar import (
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
)
from .vehicle_travel_orders import (
    PreviousVehicleTravelOrderCreateView,
    VehicleTravelOrderCloseView,
    VehicleTravelOrderCreateView,
    VehicleTravelOrderDeleteView,
    VehicleTravelOrderDetailView,
    VehicleTravelOrderFuelReportView,
    VehicleTravelOrderListView,
    VehicleTravelOrderRequestView,
    VehicleTravelOrderUpdateView,
)
from .insurance import (
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
from .lease import (
    LeaseCreateView,
    LeaseDeleteView,
    LeaseDetailView,
    LeaseListView,
    LeaseMonthlyCostsView,
    LeaseUpdateView,
    export_leases_to_excel,
)
from .policy import (
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
from .putni_nalozi import (
    PutniNalogCreateView,
    PutniNalogDeleteView,
    PutniNalogDetailView,
    PutniNalogForeignPrintView,
    PutniNalogListView,
    PutniNalogPrintView,
    PutniNalogUpdateView,
    putninalog_print_list,
    putninalog_set_opravdan,
    putninalog_storniraj,
)
from .reference import (
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
from .services import (
    DraftServiceTransactionUpdateView,
    RequisitionCreateView,
    RequisitionDeleteView,
    RequisitionDetailView,
    RequisitionFixingListView,
    RequisitionListView,
    RequisitionUpdateView,
    ServiceCreateView,
    ServiceDeleteView,
    ServiceDetailView,
    ServiceFixingListView,
    ServiceListView,
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
    ServiceUpdateView,
    fetch_requisition_data_view,
    fetch_service_data_view,
)
from ..sync.views import (
    fetch_data_view,
    fetch_lease_interest_data,
    fetch_policy_data_view,
    fetch_vehicle_value_view,
    import_nis_excel_view,
    import_omv_putnicka_csv_view,
    import_omv_teretna_csv_view,
)
from .users import UserListView
from .vehicles import (
    VehicleCreateView,
    VehicleDeleteView,
    VehicleDetailView,
    VehicleListView,
    VehicleTogleStatusView,
    VehicleUpdateView,
    vehicle_export_csv,
)
