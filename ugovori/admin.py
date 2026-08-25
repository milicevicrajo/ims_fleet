from django.contrib import admin
from .models import (
    Contract,
    ContractDocument,
    ContractGuarantee,
    ContractMenicaLink,
    ContractParty,
    ContractType,
    Partner,
)


class ContractPartyInline(admin.TabularInline):
    model = ContractParty
    extra = 1


class ContractMenicaLinkInline(admin.TabularInline):
    model = ContractMenicaLink
    extra = 0
    autocomplete_fields = ["menica", "ulazna_menica"]


class ContractGuaranteeInline(admin.TabularInline):
    model = ContractGuarantee
    extra = 0


class ContractDocumentInline(admin.TabularInline):
    model = ContractDocument
    extra = 0
    readonly_fields = ["original_filename", "uploaded_at", "uploaded_by"]


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "partner_type", "residency", "pib", "maticni_broj", "is_active"]
    list_filter = ["partner_type", "residency", "is_active"]
    search_fields = ["name", "pib", "maticni_broj", "jmbg"]


@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "sort_order"]
    list_filter = ["is_active"]


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "contract_number",
        "title",
        "kind",
        "status",
        "value_type",
        "has_incoming_menice",
        "has_outgoing_menice",
        "has_guarantees",
        "contract_date",
    ]
    list_filter = [
        "kind",
        "status",
        "value_type",
        "contract_type",
        "has_incoming_menice",
        "has_outgoing_menice",
        "has_guarantees",
    ]
    search_fields = ["contract_number", "title"]
    inlines = [
        ContractPartyInline,
        ContractDocumentInline,
        ContractMenicaLinkInline,
        ContractGuaranteeInline,
    ]


@admin.register(ContractParty)
class ContractPartyAdmin(admin.ModelAdmin):
    list_display = ["contract", "partner", "role", "party_contract_number"]
    list_filter = ["role"]


@admin.register(ContractDocument)
class ContractDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "contract",
        "document_type",
        "description",
        "original_filename",
        "uploaded_at",
        "uploaded_by",
    ]
    list_filter = ["document_type", "uploaded_at"]
    search_fields = [
        "contract__contract_number",
        "description",
        "original_filename",
    ]
    autocomplete_fields = ["contract"]


@admin.register(ContractMenicaLink)
class ContractMenicaLinkAdmin(admin.ModelAdmin):
    list_display = ["contract", "instrument_serial", "instrument_type_display", "created_at"]
    search_fields = [
        "contract__contract_number",
        "menica__serijski_broj_menice",
        "ulazna_menica__serijski_broj_menice",
    ]
    autocomplete_fields = ["contract", "menica", "ulazna_menica"]


@admin.register(ContractGuarantee)
class ContractGuaranteeAdmin(admin.ModelAdmin):
    list_display = ["contract", "guarantee_number", "issuer", "amount", "currency", "valid_to", "status"]
    list_filter = ["status", "currency"]
    search_fields = ["contract__contract_number", "guarantee_number", "issuer", "beneficiary"]
