from django.urls import path

from .views import IsplataNeoporezovanihView


app_name = "isplate"

urlpatterns = [
    path("", IsplataNeoporezovanihView.as_view(), name="neoporezive_isplate"),
]
