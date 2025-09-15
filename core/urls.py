from django.urls import path
from .views import switch_app

urlpatterns = [
    path("switch-app/<slug:app_slug>/", switch_app, name="switch_app"),
]
