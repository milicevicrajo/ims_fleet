from django.urls import path

from .views.alerts import AlertsView
from .views.cases import (
    DashboardView,
    ProcurementCaseCreateView,
    ProcurementCaseDeleteView,
    ProcurementCaseDetailView,
    ProcurementCaseListView,
    ProcurementCasePrintView,
    ProcurementCaseRepeatView,
    ProcurementCaseUpdateView,
    ProcurementContractLinkCreateView,
    ProcurementContractLinkDeleteView,
    ProcurementItemCreateView,
    ProcurementItemDeleteView,
    ProcurementItemInvoiceLinkCreateView,
    ProcurementItemInvoiceLinkDeleteView,
    ProcurementStatusLogCreateView,
)
from .views.invoices import (
    EufInvoiceDetailView,
    EufInvoiceListView,
    EufInvoiceSyncView,
    ProcurementInvoiceLinkDeleteView,
)
from .views.orders import (
    PurchaseOrderCreateView,
    PurchaseOrderDetailView,
    PurchaseOrderListView,
    PurchaseOrderUpdateView,
)
from .views.reports import ReportsView

app_name = "nabavka"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("zahtevi/", ProcurementCaseListView.as_view(), name="case_list"),
    path("zahtevi/novi/", ProcurementCaseCreateView.as_view(), name="case_create"),
    path("zahtevi/<int:pk>/", ProcurementCaseDetailView.as_view(), name="case_detail"),
    path("zahtevi/<int:pk>/stampaj/", ProcurementCasePrintView.as_view(), name="case_print"),
    path("zahtevi/<int:pk>/ponovi/", ProcurementCaseRepeatView.as_view(), name="case_repeat"),
    path("zahtevi/<int:pk>/izmeni/", ProcurementCaseUpdateView.as_view(), name="case_update"),
    path("zahtevi/<int:pk>/obrisi/", ProcurementCaseDeleteView.as_view(), name="case_delete"),
    path("zahtevi/<int:case_pk>/stavke/dodaj/", ProcurementItemCreateView.as_view(), name="item_create"),
    path("zahtevi/<int:case_pk>/stavke/<int:item_pk>/obrisi/", ProcurementItemDeleteView.as_view(), name="item_delete"),
    path("zahtevi/<int:case_pk>/stavke/<int:item_pk>/faktura/", ProcurementItemInvoiceLinkCreateView.as_view(), name="item_invoice_link_create"),
    path("zahtevi/<int:case_pk>/stavke/<int:item_pk>/faktura/obrisi/", ProcurementItemInvoiceLinkDeleteView.as_view(), name="item_invoice_link_delete"),
    path("zahtevi/<int:case_pk>/ugovori/dodaj/", ProcurementContractLinkCreateView.as_view(), name="contract_link_create"),
    path("zahtevi/<int:case_pk>/ugovori/<int:link_pk>/obrisi/", ProcurementContractLinkDeleteView.as_view(), name="contract_link_delete"),
    path("zahtevi/<int:case_pk>/status/", ProcurementStatusLogCreateView.as_view(), name="status_log_create"),
    path("euf-fakture/", EufInvoiceListView.as_view(), name="euf_invoice_list"),
    path("euf-fakture/sync/", EufInvoiceSyncView.as_view(), name="euf_invoice_sync"),
    path("euf-fakture/<int:pk>/", EufInvoiceDetailView.as_view(), name="euf_invoice_detail"),
    path("euf-fakture/veze/<int:pk>/obrisi/", ProcurementInvoiceLinkDeleteView.as_view(), name="invoice_link_delete"),
    path("narudzbenice/", PurchaseOrderListView.as_view(), name="purchase_order_list"),
    path("narudzbenice/nova/", PurchaseOrderCreateView.as_view(), name="purchase_order_create"),
    path("narudzbenice/<int:pk>/", PurchaseOrderDetailView.as_view(), name="purchase_order_detail"),
    path("narudzbenice/<int:pk>/izmeni/", PurchaseOrderUpdateView.as_view(), name="purchase_order_update"),
    path("izvestaji/", ReportsView.as_view(), name="reports"),
    path("alarmi/", AlertsView.as_view(), name="alerts"),
]
