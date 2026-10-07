from django.urls import path

from . import views

app_name = "knjizenje"

# Kod dozvole = naziv rute (core.permissions); uloga Knjiženje dobija sve kodove modula.
urlpatterns = [
    path("", views.RacuniView.as_view(), name="racuni"),
    path("izvoz/", views.izvoz, name="izvoz"),
    path("proknjizi/", views.proknjizi, name="proknjizi"),
    path("racun/<int:pk>/", views.racun, name="racun"),
    path("racun/<int:pk>/vrati/", views.vrati, name="vrati"),
    path("racun/<int:pk>/ponisti/", views.ponisti, name="ponisti"),
]
