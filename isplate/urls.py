from django.urls import path

from .views import IsplataNeoporezovanihView, IsplateConverterView


app_name = "isplate"

urlpatterns = [
    path("", IsplataNeoporezovanihView.as_view(), name="neoporezive_isplate"),
    path("konverter/", IsplateConverterView.as_view(), name="converter"),
]
