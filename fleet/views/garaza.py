"""Compatibility re-exports for garage-related fleet views."""

from .kvar import (
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
)
from .vehicle_travel_orders import (
    VehicleTravelOrderCloseView,
    VehicleTravelOrderCreateView,
    VehicleTravelOrderDeleteView,
    VehicleTravelOrderDetailView,
    VehicleTravelOrderFuelReportView,
    VehicleTravelOrderListView,
    VehicleTravelOrderRequestView,
    VehicleTravelOrderUpdateView,
)
