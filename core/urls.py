from django.urls import path
from .views import novosti_procitano, pocetna, switch_app

urlpatterns = [
    path("", pocetna, name="pocetna"),
    path("switch-app/<slug:app_slug>/", switch_app, name="switch_app"),
    # Bez posebne dozvole: svaki prijavljen korisnik potvrđuje svoje novosti.
    path("novosti/procitano/", novosti_procitano, name="novosti_procitano"),
]
