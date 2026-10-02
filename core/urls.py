from django.urls import path
from .views import pocetna, switch_app

urlpatterns = [
    path("", pocetna, name="pocetna"),
    path("switch-app/<slug:app_slug>/", switch_app, name="switch_app"),
]
