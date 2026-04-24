from django.urls import path

from .views import (
    IzlazneMeniceSyncView,
    MenicaCreateView,
    MenicaDeleteView,
    MenicaDetailView,
    MenicaListView,
    MenicaUpdateView,
    UlaznaMenicaCreateView,
    UlaznaMenicaDeleteView,
    UlaznaMenicaListView,
    UlaznaMenicaUpdateView,
)


app_name = "menice"

urlpatterns = [
    path("izlazna/azuriraj/", IzlazneMeniceSyncView.as_view(), name="izlazne_sync"),
    path("ulazne/", UlaznaMenicaListView.as_view(), name="ulazna_menica_list"),
    path("ulazne/nova/", UlaznaMenicaCreateView.as_view(), name="ulazna_menica_create"),
    path("ulazne/<int:pk>/izmena/", UlaznaMenicaUpdateView.as_view(), name="ulazna_menica_update"),
    path("ulazne/<int:pk>/brisanje/", UlaznaMenicaDeleteView.as_view(), name="ulazna_menica_delete"),
    path("<slug:tip>/", MenicaListView.as_view(), name="menica_list"),
    path("<slug:tip>/nova/", MenicaCreateView.as_view(), name="menica_create"),
    path("<slug:tip>/<int:pk>/", MenicaDetailView.as_view(), name="menica_detail"),
    path("<slug:tip>/<int:pk>/izmena/", MenicaUpdateView.as_view(), name="menica_update"),
    path("<slug:tip>/<int:pk>/brisanje/", MenicaDeleteView.as_view(), name="menica_delete"),
]
