from django.urls import path

from . import views

app_name = "arhiva"

urlpatterns = [
    path("", views.DelovodnikView.as_view(), name="delovodnik"),
    path("pisarnica/", views.PisarnicaView.as_view(), name="pisarnica"),
    path("predmeti/<int:pk>/", views.PredmetDetailView.as_view(), name="predmet_detail"),
    path("predmeti/<int:pk>/akt/", views.akt_add, name="akt_add"),
    path("predmeti/<int:pk>/storno/", views.predmet_storniraj, name="predmet_storniraj"),
    path("kategorije/", views.KategorijeView.as_view(), name="kategorije"),
]
