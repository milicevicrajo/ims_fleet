from django.contrib import admin

from .models import Menica, UlaznaMenica


@admin.register(Menica)
class MenicaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tip",
        "sifra_partnera",
        "serijski_broj_menice",
        "naziv_duznika",
        "datum_izdavanja",
        "datum_dospeca",
        "iznos_menice",
        "valuta_menice",
        "fizicka_lokacija",
        "interni_status",
    )
    list_filter = ("tip", "interni_status", "fizicka_lokacija", "valuta_menice", "valuta_osnova")
    search_fields = (
        "serijski_broj_menice",
        "naziv_duznika",
        "maticni_broj_duznika",
        "poreski_broj_duznika",
        "broj_ugovora",
    )
    ordering = ("-datum_registracije", "-created_at")


@admin.register(UlaznaMenica)
class UlaznaMenicaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "serijski_broj_menice",
        "sifra_poslovnog_partnera",
        "naziv_pravnog_lica",
        "broj_naseg_ugovora",
        "datum_prijema_menice",
        "datum_ugovora",
        "ugovor_vazi_do",
        "lokacija_menice",
        "sifra_centra",
    )
    list_filter = ("lokacija_menice", "sifra_centra")
    search_fields = (
        "serijski_broj_menice",
        "naziv_pravnog_lica",
        "=sifra_poslovnog_partnera",
        "broj_naseg_ugovora",
        "sifra_centra",
    )
    ordering = ("-datum_prijema_menice", "-created_at")
