from django.urls import path
from .views import *
from django.conf import settings
from django.urls import path

urlpatterns = [
    path('dugovanja/', lista_dugovanja, name='lista_dugovanja'),
    path('partner/<int:sif_par>/', detalji_partner, name='detalji_partner'),
    path('dugovanja_po_bucketima/', lista_dugovanja_po_bucketima, name='lista_dugovanja_po_bucketima'),
    path('naplata/export-excel/', export_dugovanja_bucketi_excel, name='export_dugovanja_excel'),
    path('naplata/utuzene/<int:sif_par>', export_utuzene_fakture_excel, name='export_utuzene_fakture'),
    path('naplata/opomene/<int:sif_par>', export_opomene_excel, name='export_opomene_fakture'),
    path('naplata/baket90/<int:sif_par>/', export_baket_90_excel, name='export_baket_90_excel'),
    path('naplata/baket60/<int:sif_par>/', export_baket_60_excel, name='export_baket_60_excel'),

    path('kontakti/', lista_kontakata, name='lista_kontakata'),
    path('kontakti/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_kontakt, name='dodaj_kontakt'),
    path('kontakti/izmeni/<int:id>/', izmeni_kontakt, name='izmeni_kontakt'),
    path('kontakti/obrisi/<int:id>/', obrisi_kontakt, name='obrisi_kontakt'),

    path('napomene/', lista_napomena, name='lista_napomena'),
    path('napomene/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_napomenu, name='dodaj_napomenu'),
    path('napomene/izmeni/<int:id>/', izmeni_napomenu, name='izmeni_napomenu'),
    path('napomene/obrisi/<int:id>/', obrisi_napomenu, name='obrisi_napomenu'),

    path('opomene/', lista_opomena, name='lista_opomena'),
    path('opomene/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_opomenu, name='dodaj_opomenu'),
    path('opomene/izmeni/<int:id>/', izmeni_opomenu, name='izmeni_opomenu'),
    path('opomene/obrisi/<int:id>/', obrisi_opomenu, name='obrisi_opomenu'),

    path('poziv_pismo/', lista_pozivnih_pisma, name='lista_pozivnih_pisma'),
    path('poziv_pismo/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_poziv_pismo, name='dodaj_poziv_pismo'),
    path('poziv_pismo/izmeni/<int:id>/', izmeni_poziv_pismo, name='izmeni_poziv_pismo'),
    path('poziv_pismo/obrisi/<int:id>/', obrisi_poziv_pismo, name='obrisi_poziv_pismo'),

    path('pozivi_tel/', lista_poziva, name='lista_poziva'),
    path('pozivi_tel/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_poziv, name='dodaj_poziv'),
    path('pozivi_tel/izmeni/<int:id>/', izmeni_poziv, name='izmeni_poziv'),
    path('pozivi_tel/obrisi/<int:id>/', obrisi_poziv, name='obrisi_poziv'),

    path('tuzbe/', lista_tuzbi, name='lista_tuzbi'),
    path('tuzbe/dodaj/<int:sif_par>/<str:naz_par>/', dodaj_tuzbu, name='dodaj_tuzbu'),
    path('tuzbe/izmeni/<int:id>/', izmeni_tuzbu, name='izmeni_tuzbu'),
    path('tuzbe/obrisi/<int:id>/', obrisi_tuzbu, name='obrisi_tuzbu'),
]