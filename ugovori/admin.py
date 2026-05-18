from django.contrib import admin
from .models import Partner, ContractType, Contract, ContractParty


class ContractPartyInline(admin.TabularInline):
    model = ContractParty
    extra = 1


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
    list_display = ["contract_number", "title", "kind", "status", "value_type", "contract_date"]
    list_filter = ["kind", "status", "value_type", "contract_type"]
    search_fields = ["contract_number", "title"]
    inlines = [ContractPartyInline]


@admin.register(ContractParty)
class ContractPartyAdmin(admin.ModelAdmin):
    list_display = ["contract", "partner", "role"]
    list_filter = ["role"]
