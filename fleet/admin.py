from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin

from core.models import CustomUser, PermissionCode, Role, RolePermission
from hr.models import Employee, EmployeeCVItem

from .models import (
    FuelConsumption,
    JobCode,
    Kvar,
    Lease,
    Policy,
    PutniNalog,
    PutniNalogSequence,
    Service,
    ServiceType,
    TrafficCard,
    Vehicle,
    VehicleTenderDocument,
    VehicleTravelOrder,
)
from core.tasks import sync_permission_codes_task

class CustomUserAdmin(UserAdmin):
    # Add the allowed_centers field to the admin form
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('employee', 'allowed_centers', 'allowed_center_codes', 'must_change_password', 'roles')}),
    )
    autocomplete_fields = ('employee',)


class EmployeeCVItemInline(admin.TabularInline):
    model = EmployeeCVItem
    extra = 0


class EmployeeAdmin(admin.ModelAdmin):
    search_fields = ('employee_code', 'first_name', 'last_name')
    inlines = [EmployeeCVItemInline]

admin.site.register(CustomUser, CustomUserAdmin)
class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1


class RoleAdmin(admin.ModelAdmin):
    inlines = [RolePermissionInline]


@admin.action(description="Pokreni sync kodova dozvola (Celery)")
def run_permission_code_sync(modeladmin, request, queryset):
    task = sync_permission_codes_task.delay()
    modeladmin.message_user(
        request,
        f"Pokrenut task za sync dozvola. Task ID: {task.id}",
        level=messages.SUCCESS,
    )


class PermissionCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "label")
    search_fields = ("code", "label")
    actions = [run_permission_code_sync]


admin.site.register(Role, RoleAdmin)
admin.site.register(PermissionCode, PermissionCodeAdmin)
admin.site.register(PutniNalogSequence)
admin.site.register(Vehicle)
admin.site.register(TrafficCard)
admin.site.register(VehicleTenderDocument)
admin.site.register(JobCode)
admin.site.register(Lease)
admin.site.register(Policy)
admin.site.register(FuelConsumption)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(PutniNalog)
admin.site.register(VehicleTravelOrder)
admin.site.register(ServiceType)
admin.site.register(Service)
admin.site.register(Kvar)
