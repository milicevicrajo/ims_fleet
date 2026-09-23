from django.contrib import admin

from .models import DisciplinskiPostupak, Postupak, PromenaPostupka, TokPostupka


@admin.register(Postupak)
class PostupakAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tip",
        "broj_predmeta",
        "sud",
        "naziv_partnera",
        "sifra_partnera",
        "arhivirano",
        "created_at",
    )
    list_filter = ("tip", "arhivirano", "valuta")
    search_fields = ("broj_predmeta", "sud", "naziv_partnera", "=sifra_partnera", "tuzilac")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    exclude = ("created_by",)


@admin.register(PromenaPostupka)
class PromenaPostupkaAdmin(admin.ModelAdmin):
    list_display = ("id", "datum", "postupak", "kratka_promena", "created_at")
    list_filter = ("datum", "postupak__tip")
    search_fields = (
        "promena",
        "postupak__broj_predmeta",
        "postupak__naziv_partnera",
        "=postupak__sifra_partnera",
    )
    ordering = ("-datum", "-created_at")
    readonly_fields = ("created_at",)
    raw_id_fields = ("postupak",)
    exclude = ("created_by",)

    @admin.display(description="Promena")
    def kratka_promena(self, obj):
        text = obj.promena or ""
        return text if len(text) <= 60 else f"{text[:60]}..."


class TokPostupkaInline(admin.TabularInline):
    model = TokPostupka
    extra = 0
    fields = ("datum", "opis")
    ordering = ("datum", "id")


@admin.register(DisciplinskiPostupak)
class DisciplinskiPostupakAdmin(admin.ModelAdmin):
    list_display = ("id", "zaposleni", "centar", "datum_podnosenja", "podnosilac", "mera_datum", "arhivirano")
    list_filter = ("centar", "arhivirano", "datum_podnosenja")
    search_fields = (
        "zaposleni__first_name",
        "zaposleni__last_name",
        "=zaposleni__employee_code",
        "mera_opis",
    )
    ordering = ("-datum_podnosenja", "-id")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("zaposleni", "podnosilac")
    exclude = ("created_by",)
    inlines = [TokPostupkaInline]
