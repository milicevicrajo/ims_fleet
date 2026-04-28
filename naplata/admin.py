from django.contrib import admin
from .models import *


class NaplataAdmin(admin.ModelAdmin):
    using = "server_db"

    def get_queryset(self, request):
        return super().get_queryset(request).using(self.using)

    def save_model(self, request, obj, form, change):
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        obj.delete(using=self.using)

    def delete_queryset(self, request, queryset):
        queryset.delete()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        kwargs["using"] = self.using
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        kwargs["using"] = self.using
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Postupak)
class PostupakAdmin(NaplataAdmin):
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
class PromenaPostupkaAdmin(NaplataAdmin):
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
        text = (obj.promena or "").strip()
        return text[:80] + ("..." if len(text) > 80 else "")


admin.site.register(Kontakti, NaplataAdmin)
admin.site.register(Napomene, NaplataAdmin)
admin.site.register(Opomene, NaplataAdmin)
admin.site.register(PozivPismo, NaplataAdmin)
admin.site.register(PoziviTel, NaplataAdmin)
admin.site.register(SifBaket, NaplataAdmin)
admin.site.register(SifKategorija, NaplataAdmin)
admin.site.register(Tuzbe, NaplataAdmin)
