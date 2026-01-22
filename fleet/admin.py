from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(UserAdmin):
    # Add the allowed_centers field to the admin form
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('allowed_centers', 'allowed_center_codes', 'roles')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1


class RoleAdmin(admin.ModelAdmin):
    inlines = [RolePermissionInline]


admin.site.register(Role, RoleAdmin)
admin.site.register(PermissionCode)
admin.site.register(PutniNalogSequence)
admin.site.register(Vehicle)
admin.site.register(TrafficCard)
admin.site.register(VehicleTenderDocument)
admin.site.register(JobCode)
admin.site.register(Lease)
admin.site.register(Policy)
admin.site.register(FuelConsumption)
admin.site.register(Employee)
admin.site.register(Incident)
admin.site.register(PutniNalog)
admin.site.register(VehicleTravelOrder)
admin.site.register(ServiceType)
admin.site.register(Service)
admin.site.register(Kvar)
