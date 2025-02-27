from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(UserAdmin):
    # Add the allowed_centers field to the admin form
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('allowed_centers',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Vehicle)
admin.site.register(TrafficCard)
admin.site.register(JobCode)
admin.site.register(Lease)
admin.site.register(Policy)
admin.site.register(FuelConsumption)
admin.site.register(Employee)
admin.site.register(Incident)
admin.site.register(PutniNalog)
admin.site.register(ServiceType)
admin.site.register(Service)
admin.site.register(Kontakti)
admin.site.register(Napomene)
admin.site.register(Opomene)
admin.site.register(PozivPismo)
admin.site.register(PoziviTel)
admin.site.register(SifBaket)
admin.site.register(SifKategorija)
admin.site.register(Tuzbe)