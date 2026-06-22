from django.contrib import admin

from .models import (
    EufItemSnapshot,
    GoodsSnapshot,
    ProcurementCase,
    ProcurementInvoice,
    ProcurementInvoiceContractLink,
    ProcurementInvoiceJobCodeLink,
    ProcurementInvoiceLink,
    ProcurementItem,
    ProcurementItemInvoiceLink,
    ProcurementStatusLog,
    PublicProcurementPlanItem,
    PublicProcurementPlanVersion,
    PurchaseOrder,
    UfInvoiceSnapshot,
)


class ProcurementItemInline(admin.TabularInline):
    model = ProcurementItem
    extra = 1


@admin.register(ProcurementCase)
class ProcurementCaseAdmin(admin.ModelAdmin):
    list_display = ["case_number", "title", "case_type", "status", "supplier", "created_at"]
    list_filter = ["case_type", "status", "currency"]
    search_fields = ["case_number", "title", "supplier__name"]
    inlines = [ProcurementItemInline]


@admin.register(ProcurementInvoiceLink)
class ProcurementInvoiceLinkAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "supplier_name", "amount", "procurement_case", "created_at"]
    list_filter = ["source"]
    search_fields = ["invoice_number", "supplier_name", "euf_key", "procurement_case__case_number"]


@admin.register(ProcurementInvoice)
class ProcurementInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "supplier_name",
        "amount",
        "invoice_date",
        "center_name",
        "goes_to_warehouse",
        "source",
        "synced_at",
    ]
    list_filter = ["source", "invoice_date", "goes_to_warehouse"]
    search_fields = ["invoice_number", "supplier_name", "euf_key", "center_name"]


@admin.register(EufItemSnapshot)
class EufItemSnapshotAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "partner_name", "document_date", "item_name", "quantity", "value", "account", "uf_invoice"]
    list_filter = ["document_date", "account"]
    search_fields = ["invoice_number", "partner_name", "partner_pib", "item_name", "account", "uf_invoice__invoice_number"]


@admin.register(UfInvoiceSnapshot)
class UfInvoiceSnapshotAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "partner_name", "document_date", "payment_amount", "item_value_total", "item_count", "accounts"]
    list_filter = ["document_date"]
    search_fields = ["invoice_number", "partner_name", "partner_pib", "accounts"]


@admin.register(GoodsSnapshot)
class GoodsSnapshotAdmin(admin.ModelAdmin):
    list_display = ["document_date", "document_number", "organizational_unit", "partner_name", "article_code", "article_name", "quantity", "price"]
    list_filter = ["document_date", "document_type", "organizational_unit", "article_type"]
    search_fields = ["document_number", "partner_name", "linked_document", "article_code", "article_name"]


@admin.register(ProcurementItemInvoiceLink)
class ProcurementItemInvoiceLinkAdmin(admin.ModelAdmin):
    list_display = ["invoice", "procurement_item", "created_by", "created_at"]
    search_fields = [
        "invoice__invoice_number",
        "invoice__supplier_name",
        "procurement_item__name",
        "procurement_item__procurement_case__case_number",
    ]


@admin.register(ProcurementInvoiceContractLink)
class ProcurementInvoiceContractLinkAdmin(admin.ModelAdmin):
    list_display = ["invoice", "contract", "created_by", "created_at"]
    search_fields = ["invoice__invoice_number", "invoice__supplier_name", "contract__contract_number"]


@admin.register(ProcurementInvoiceJobCodeLink)
class ProcurementInvoiceJobCodeLinkAdmin(admin.ModelAdmin):
    list_display = ["invoice", "job_code", "kind", "is_returned", "returned_by", "returned_at", "created_by", "created_at"]
    list_filter = ["kind", "is_returned"]
    search_fields = ["invoice__invoice_number", "invoice__supplier_name", "job_code__code", "job_code__name"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "procurement_case", "supplier", "status", "amount", "order_date"]
    list_filter = ["status", "currency"]
    search_fields = ["order_number", "procurement_case__case_number", "supplier__name"]


@admin.register(PublicProcurementPlanVersion)
class PublicProcurementPlanVersionAdmin(admin.ModelAdmin):
    list_display = [
        "year",
        "version_number",
        "source_filename",
        "total_rows",
        "added_count",
        "changed_count",
        "removed_count",
        "imported_at",
    ]
    list_filter = ["year"]
    search_fields = ["source_filename", "note"]


@admin.register(PublicProcurementPlanItem)
class PublicProcurementPlanItemAdmin(admin.ModelAdmin):
    list_display = [
        "version",
        "plan_type",
        "diff_status",
        "item_number",
        "title",
        "estimated_value",
        "source_sheet",
        "source_row",
    ]
    list_filter = ["version__year", "plan_type", "diff_status", "source_sheet"]
    search_fields = ["item_number", "title", "cpv", "technique", "note"]


@admin.register(ProcurementStatusLog)
class ProcurementStatusLogAdmin(admin.ModelAdmin):
    list_display = ["procurement_case", "old_status", "new_status", "created_by", "created_at"]
    list_filter = ["new_status"]
