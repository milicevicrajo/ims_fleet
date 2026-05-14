from django.urls import path

from .views import (
    AnnexCreateView,
    ContractCreateView,
    ContractDeleteView,
    ContractDetailView,
    ContractListView,
    ContractTypeCreateView,
    ContractTypeDeleteView,
    ContractTypeListView,
    ContractTypeUpdateView,
    ContractUpdateView,
    PartnerCreateView,
    PartnerDeleteView,
    PartnerDetailView,
    PartnerListView,
    PartnerUpdateView,
    partner_datatable_data,
    sync_finansijski_partneri_batch,
    sync_finansijski_partneri_start,
    sync_finansijski_partneri_view,
)

app_name = "ugovori"

urlpatterns = [
    # Partneri
    path("partneri/", PartnerListView.as_view(), name="partner_list"),
    path("partneri/data/", partner_datatable_data, name="partner_data"),
    path("partneri/sync-finansije/", sync_finansijski_partneri_view, name="partner_sync_finansije"),
    path("partneri/sync-finansije/start/", sync_finansijski_partneri_start, name="partner_sync_finansije_start"),
    path("partneri/sync-finansije/batch/", sync_finansijski_partneri_batch, name="partner_sync_finansije_batch"),
    path("partneri/novi/", PartnerCreateView.as_view(), name="partner_create"),
    path("partneri/<int:pk>/", PartnerDetailView.as_view(), name="partner_detail"),
    path("partneri/<int:pk>/izmeni/", PartnerUpdateView.as_view(), name="partner_update"),
    path("partneri/<int:pk>/obrisi/", PartnerDeleteView.as_view(), name="partner_delete"),

    # Tipovi ugovora
    path("tipovi/", ContractTypeListView.as_view(), name="contract_type_list"),
    path("tipovi/novi/", ContractTypeCreateView.as_view(), name="contract_type_create"),
    path("tipovi/<int:pk>/izmeni/", ContractTypeUpdateView.as_view(), name="contract_type_update"),
    path("tipovi/<int:pk>/obrisi/", ContractTypeDeleteView.as_view(), name="contract_type_delete"),

    # Ugovori
    path("", ContractListView.as_view(), name="contract_list"),
    path("novi/", ContractCreateView.as_view(), name="contract_create"),
    path("<int:pk>/", ContractDetailView.as_view(), name="contract_detail"),
    path("<int:pk>/izmeni/", ContractUpdateView.as_view(), name="contract_update"),
    path("<int:pk>/obrisi/", ContractDeleteView.as_view(), name="contract_delete"),
    path("<int:parent_pk>/aneks/novi/", AnnexCreateView.as_view(), name="annex_create"),
]
