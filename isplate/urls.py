from django.urls import path

from .fiskalni_views import FiskalniPutniNaloziView, fiskalni_izvoz, fiskalni_proknjizi
from .putni_nalozi_views import (PutniNaloziPravdanjeView, putni_nalog_opravdaj, putni_nalog_racun_dodaj,
                                 putni_nalog_racun_ukloni, putni_nalog_racuni)
from .views import IsplataNeoporezovanihView, IsplateConverterView


app_name = "isplate"

urlpatterns = [
    path("", IsplataNeoporezovanihView.as_view(), name="neoporezive_isplate"),
    path("konverter/", IsplateConverterView.as_view(), name="converter"),
    path("putni-nalozi/", PutniNaloziPravdanjeView.as_view(), name="putni_nalozi_pravdanje"),
    path("putni-nalozi/<int:pk>/racuni/", putni_nalog_racuni, name="putni_nalog_racuni"),
    path("putni-nalozi/<int:pk>/racuni/dodaj/", putni_nalog_racun_dodaj, name="putni_nalog_racun_dodaj"),
    path("putni-nalozi/<int:pk>/racuni/<int:racun_pk>/ukloni/", putni_nalog_racun_ukloni, name="putni_nalog_racun_ukloni"),
    path("putni-nalozi/<int:pk>/opravdaj/", putni_nalog_opravdaj, name="putni_nalog_opravdaj"),
    path("fiskalni-racuni/", FiskalniPutniNaloziView.as_view(), name="fiskalni_putni_nalozi"),
    path("fiskalni-racuni/izvoz/", fiskalni_izvoz, name="fiskalni_izvoz"),
    path("fiskalni-racuni/<int:pk>/proknjizeno/", fiskalni_proknjizi, name="fiskalni_proknjizi"),
]
