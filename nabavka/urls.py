from django.urls import path

from .views.alerts import AlertsView
from .views.cases import (
    DashboardView,
    ProcurementCaseCreateView,
    ProcurementCaseDataView,
    ProcurementCaseDeleteView,
    ProcurementCaseDetailView,
    ProcurementCaseSourceLinkView,
    ProcurementCaseListView,
    ProcurementCaseMaterialRequisitionPrintView,
    ProcurementCasePrintView,
    ProcurementCaseRepeatView,
    ProcurementCaseUpdateView,
    ProcurementItemCreateView,
    ProcurementItemDeleteView,
    ProcurementItemSourceDataView,
    ProcurementItemSourceLinkView,
    ProcurementStatusLogCreateView,
)
from .views.contracts import PurchaseContractListView
from .views.invoices import (
    EufInvoiceDataView,
    EufInvoiceDetailView,
    EufInvoiceExportView,
    EufInvoiceListView,
    EufInvoiceReturnedToggleView,
    EufInvoiceSyncView,
    EufInvoiceUpdateView,
    ProcurementInvoiceContractLinkDeleteView,
    ProcurementInvoiceJobCodeLinkDeleteView,
    ProcurementInvoiceLinkDeleteView,
)
from .views.orders import (
    PurchaseOrderCreateView,
    PurchaseOrderDetailView,
    PurchaseOrderListView,
    PurchaseOrderUpdateView,
)
from .views.public_procurements import (
    PublicProcurementPlanDetailView,
    PublicProcurementPlanImportView,
    PublicProcurementPlanListView,
)
from .views.reports import PartnerJobCodeCheckReportView, ReportsView
from .views.source_snapshots import (
    EufItemSnapshotDataView,
    EufItemSnapshotListView,
    EufItemSnapshotSyncView,
    GoodsSnapshotDataView,
    GoodsSnapshotListView,
    GoodsSnapshotSyncView,
    UfInvoiceSnapshotDetailView,
)

app_name = "nabavka"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("zahtevi/", ProcurementCaseListView.as_view(), name="case_list"),
    path("zahtevi/data/", ProcurementCaseDataView.as_view(), name="case_data"),
    path("zahtevi/novi/", ProcurementCaseCreateView.as_view(), name="case_create"),
    path("zahtevi/<int:pk>/", ProcurementCaseDetailView.as_view(), name="case_detail"),
    path("zahtevi/<int:pk>/stampaj/", ProcurementCasePrintView.as_view(), name="case_print"),
    path("zahtevi/<int:pk>/trebovanje-materijala/", ProcurementCaseMaterialRequisitionPrintView.as_view(), name="case_material_requisition_print"),
    path("zahtevi/<int:pk>/ponovi/", ProcurementCaseRepeatView.as_view(), name="case_repeat"),
    path("zahtevi/<int:pk>/izmeni/", ProcurementCaseUpdateView.as_view(), name="case_update"),
    path("zahtevi/<int:pk>/obrisi/", ProcurementCaseDeleteView.as_view(), name="case_delete"),
    path("zahtevi/<int:case_pk>/stavke/dodaj/", ProcurementItemCreateView.as_view(), name="item_create"),
    path("zahtevi/stavke/izvori/data/", ProcurementItemSourceDataView.as_view(), name="item_source_data"),
    path("zahtevi/<int:case_pk>/stavke/izvor/", ProcurementCaseSourceLinkView.as_view(), name="case_source_link"),
    path("zahtevi/<int:case_pk>/stavke/<int:item_pk>/izvor/", ProcurementItemSourceLinkView.as_view(), name="item_source_link"),
    path("zahtevi/<int:case_pk>/stavke/<int:item_pk>/obrisi/", ProcurementItemDeleteView.as_view(), name="item_delete"),
    path("zahtevi/<int:case_pk>/status/", ProcurementStatusLogCreateView.as_view(), name="status_log_create"),
    path("euf-fakture/", EufInvoiceListView.as_view(), name="euf_invoice_list"),
    path("euf-fakture/data/", EufInvoiceDataView.as_view(), name="euf_invoice_data"),
    path("euf-fakture/export/", EufInvoiceExportView.as_view(), name="euf_invoice_export"),
    path("euf-fakture/sync/", EufInvoiceSyncView.as_view(), name="euf_invoice_sync"),
    path("euf-fakture/<int:pk>/vraceno/", EufInvoiceReturnedToggleView.as_view(), name="euf_invoice_returned_toggle"),
    path("euf-fakture/<int:pk>/izmeni/", EufInvoiceUpdateView.as_view(), name="euf_invoice_update"),
    path("euf-fakture/<int:pk>/", EufInvoiceDetailView.as_view(), name="euf_invoice_detail"),
    path("euf-fakture/veze/<int:pk>/obrisi/", ProcurementInvoiceLinkDeleteView.as_view(), name="invoice_link_delete"),
    path("euf-fakture/ugovori/<int:pk>/obrisi/", ProcurementInvoiceContractLinkDeleteView.as_view(), name="invoice_contract_link_delete"),
    path("euf-fakture/sifre-posla/<int:pk>/obrisi/", ProcurementInvoiceJobCodeLinkDeleteView.as_view(), name="invoice_job_code_link_delete"),
    path("uf-stavke/", EufItemSnapshotListView.as_view(), name="euf_item_list"),
    path("uf-stavke/data/", EufItemSnapshotDataView.as_view(), name="euf_item_data"),
    path("uf-stavke/sync/", EufItemSnapshotSyncView.as_view(), name="euf_item_sync"),
    path("uf-stavke/<int:pk>/", UfInvoiceSnapshotDetailView.as_view(), name="uf_invoice_detail"),
    path("roba/", GoodsSnapshotListView.as_view(), name="goods_list"),
    path("roba/data/", GoodsSnapshotDataView.as_view(), name="goods_data"),
    path("roba/sync/", GoodsSnapshotSyncView.as_view(), name="goods_sync"),
    path("kupovni-ugovori/", PurchaseContractListView.as_view(), name="purchase_contract_list"),
    path("javne-nabavke/", PublicProcurementPlanListView.as_view(), name="public_procurement_list"),
    path("javne-nabavke/uvoz/", PublicProcurementPlanImportView.as_view(), name="public_procurement_import"),
    path("javne-nabavke/<int:pk>/", PublicProcurementPlanDetailView.as_view(), name="public_procurement_detail"),
    path("narudzbenice/", PurchaseOrderListView.as_view(), name="purchase_order_list"),
    path("narudzbenice/nova/", PurchaseOrderCreateView.as_view(), name="purchase_order_create"),
    path("narudzbenice/<int:pk>/", PurchaseOrderDetailView.as_view(), name="purchase_order_detail"),
    path("narudzbenice/<int:pk>/izmeni/", PurchaseOrderUpdateView.as_view(), name="purchase_order_update"),
    path("izvestaji/", ReportsView.as_view(), name="reports"),
    path("izvestaji/provera-sifre-posla-partnera/", PartnerJobCodeCheckReportView.as_view(), name="partner_job_code_check_report"),
    path("alarmi/", AlertsView.as_view(), name="alerts"),
]
