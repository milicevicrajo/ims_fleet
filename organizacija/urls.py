from django.urls import path

from . import views

app_name = "organizacija"
urlpatterns = [
    path("", views.stablo, name="stablo"),
    path("cvor/<int:pk>/", views.cvor, name="cvor"),
]
