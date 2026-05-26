from django.contrib import admin

from .models import (
    ProcurementCase,
    ProcurementContractLink,
    ProcurementInvoice,
    ProcurementInvoiceLink,
    ProcurementItem,
    ProcurementItemInvoiceLink,
    ProcurementStatusLog,
    PurchaseOrder,
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


@admin.register(ProcurementItemInvoiceLink)
class ProcurementItemInvoiceLinkAdmin(admin.ModelAdmin):
    list_display = ["invoice", "procurement_item", "created_by", "created_at"]
    search_fields = [
        "invoice__invoice_number",
        "invoice__supplier_name",
        "procurement_item__name",
        "procurement_item__procurement_case__case_number",
    ]


@admin.register(ProcurementContractLink)
class ProcurementContractLinkAdmin(admin.ModelAdmin):
    list_display = ["procurement_case", "contract", "invoice_link", "created_at"]
    search_fields = ["procurement_case__case_number", "contract__contract_number"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "procurement_case", "supplier", "status", "amount", "order_date"]
    list_filter = ["status", "currency"]
    search_fields = ["order_number", "procurement_case__case_number", "supplier__name"]


@admin.register(ProcurementStatusLog)
class ProcurementStatusLogAdmin(admin.ModelAdmin):
    list_display = ["procurement_case", "old_status", "new_status", "created_by", "created_at"]
    list_filter = ["new_status"]
