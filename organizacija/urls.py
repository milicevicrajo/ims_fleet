from django.urls import path

from . import views

app_name = "organizacija"
urlpatterns = [
    path("", views.stablo, name="stablo"),
    path("cvor/<int:pk>/", views.cvor, name="cvor"),
    path("sema/", views.sema, name="sema"),
    path("flota/", views.flota, name="flota"),
    path("dodele/", views.dodele, name="dodele"),
    path("dodele/korisnik/<int:pk>/", views.dodele_korisnika, name="dodele_korisnika"),
    path("dodele/korisnik/<int:pk>/odobri/", views.dodele_odobri, name="dodele_odobri"),
    path("dodele/<int:pk>/opozovi/", views.dodela_opozovi, name="dodela_opozovi"),
]
