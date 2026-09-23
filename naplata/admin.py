from django.contrib import admin

from .models import (
    Kontakti,
    Napomene,
    Opomene,
    PozivPismo,
    PoziviTel,
    SifBaket,
    SifKategorija,
    Tuzbe,
)


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
