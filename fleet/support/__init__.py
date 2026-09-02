from fleet.support.analytics import (
    cost_per_km_status,
    cost_per_km_thresholds,
    is_red_zone,
    net_maintenance_cost,
)
from fleet.support.dashboard import (
    LONG_TERM_LEASE_TYPES,
    cost_per_km_period_analysis,
    vehicle_cost_per_km_rows,
)
from fleet.support.fuel import (
    calculate_average_fuel_consumption,
    calculate_average_fuel_consumption_ever,
    date_range_for_datetime_field,
    filter_nis_fuel_queryset,
    filter_nis_travel_order_fuel_queryset,
    filter_omv_fuel_queryset,
    filter_omv_travel_order_fuel_queryset,
    get_fuel_consumption_queryset,
)
from fleet.support.garaza import (
    ensure_auto_parts,
    get_vehicle_center_code,
    get_vehicle_latest_organizational_unit,
)
from fleet.support.lease_queries import lease_monthly_costs_rows
from fleet.support.policy_queries import _filtered_qs, policies_monthly_costs_qs
from fleet.support.report_helpers import (
    date_period_filtered_query,
    get_data_from_secondary_db,
    report_period_filtered_query,
)
from fleet.support.report_queries import (
    KASKO_RATE_SQL,
    MAGACIN_SQL,
    NIS_PUTNICKA_SQL,
    NIS_TERETNA_SQL,
    OMV_PUTNICKA_SQL,
    OMV_TERETNA_SQL,
    OTPIS_SQL,
    PO_DOBAVLJACIMA_SQL,
    POTRAZIVANJE_DDOR_SQL,
    TAHOGRAF_PARTNERI_SQL,
    TROSKOVI_SVI_SQL,
    TRO_GORIVO_MESEC_SQL,
    TRO_PARKING_SQL,
    TRO_PRACENJA_VOZILA_SQL,
    TRO_ZARADE_SQL,
    ZATVOREN_PUTNI_SQL,
)
from fleet.support.service_queries import service_monthly_costs_rows
from fleet.support.vehicle import format_license_plate

__all__ = [
    "KASKO_RATE_SQL",
    "LONG_TERM_LEASE_TYPES",
    "MAGACIN_SQL",
    "NIS_PUTNICKA_SQL",
    "NIS_TERETNA_SQL",
    "OMV_PUTNICKA_SQL",
    "OMV_TERETNA_SQL",
    "OTPIS_SQL",
    "PO_DOBAVLJACIMA_SQL",
    "POTRAZIVANJE_DDOR_SQL",
    "TAHOGRAF_PARTNERI_SQL",
    "TROSKOVI_SVI_SQL",
    "TRO_GORIVO_MESEC_SQL",
    "TRO_PARKING_SQL",
    "TRO_PRACENJA_VOZILA_SQL",
    "TRO_ZARADE_SQL",
    "ZATVOREN_PUTNI_SQL",
    "_filtered_qs",
    "calculate_average_fuel_consumption",
    "calculate_average_fuel_consumption_ever",
    "cost_per_km_status",
    "cost_per_km_thresholds",
    "cost_per_km_period_analysis",
    "date_period_filtered_query",
    "date_range_for_datetime_field",
    "ensure_auto_parts",
    "filter_nis_fuel_queryset",
    "filter_nis_travel_order_fuel_queryset",
    "filter_omv_fuel_queryset",
    "filter_omv_travel_order_fuel_queryset",
    "format_license_plate",
    "get_vehicle_center_code",
    "get_vehicle_latest_organizational_unit",
    "get_data_from_secondary_db",
    "get_fuel_consumption_queryset",
    "is_red_zone",
    "lease_monthly_costs_rows",
    "net_maintenance_cost",
    "policies_monthly_costs_qs",
    "report_period_filtered_query",
    "service_monthly_costs_rows",
    "vehicle_cost_per_km_rows",
]
