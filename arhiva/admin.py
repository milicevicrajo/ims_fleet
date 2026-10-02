from django.contrib import admin

from .models import Akt, EvidencionaKnjiga, GrupaKategorija, Kategorija, Predmet, VerzijaListe


@admin.register(VerzijaListe)
class VerzijaListeAdmin(admin.ModelAdmin):
    list_display = ("naziv", "datum_donosenja", "aktivna", "uvezeno_at")


@admin.register(GrupaKategorija)
class GrupaKategorijaAdmin(admin.ModelAdmin):
    list_display = ("klasifikaciona_oznaka", "naziv", "verzija")
    list_filter = ("verzija",)


@admin.register(Kategorija)
class KategorijaAdmin(admin.ModelAdmin):
    list_display = ("redni_broj", "naziv", "rok_tekst", "trajno", "verzija")
    list_filter = ("verzija", "trajno", "operativno", "pocetak_roka")
    search_fields = ("naziv",)


@admin.register(EvidencionaKnjiga)
class EvidencionaKnjigaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "vrsta", "godina", "status", "istorijska")


class AktInline(admin.TabularInline):
    model = Akt
    extra = 0
    readonly_fields = ("podbroj", "delovodni_broj", "datum", "opis", "smer", "zaveo")
    can_delete = False


@admin.register(Predmet)
class PredmetAdmin(admin.ModelAdmin):
    """Samo pregled: broj daje servis delovodnika, a brisanje ne postoji (storno)."""

    list_display = ("delovodni_broj", "datum_zavodjenja", "smer", "naslov", "status")
    list_filter = ("knjiga", "smer", "status")
    search_fields = ("delovodni_broj", "naslov", "korespondent")
    inlines = [AktInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
