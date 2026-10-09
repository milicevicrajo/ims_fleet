from django.urls import path

from . import views

app_name = "knjizenje"

# Kod dozvole = naziv rute (core.permissions); uloga Knjiženje dobija sve kodove modula.
urlpatterns = [
    path("", views.RacuniView.as_view(), name="racuni"),
    path("izvoz/", views.izvoz, name="izvoz"),
    # Od 08.10.2026. nema ručnog knjiženja: štampa proknjižava račun koji čeka (knjiži se u drugom programu).
    path("stampaj/", views.stampaj, name="stampaj"),
    path("stampa/", views.stampa, name="stampa"),
    path("racun/<int:pk>/", views.racun, name="racun"),
    path("racun/<int:pk>/vrati/", views.vrati, name="vrati"),
    path("racun/<int:pk>/ponisti/", views.ponisti, name="ponisti"),
]
