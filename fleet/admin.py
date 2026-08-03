from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin

from core.models import ActivityLog, CustomUser, PermissionCode, Role, RolePermission, TaskHistory
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


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor_username", "action", "description", "status_code", "app_label", "path")
    list_filter = ("action", "app_label", "status_code", "created_at")
    search_fields = ("actor_username", "actor_display_name", "description", "path", "view_name", "object_repr")
    readonly_fields = [field.name for field in ActivityLog._meta.fields]
    date_hierarchy = "created_at"


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ("started_at", "display_name", "task_name", "status", "short_message", "elapsed_seconds")
    list_filter = ("status", "task_name", "started_at")
    search_fields = ("task_id", "task_name", "display_name", "short_message", "result", "error")
    readonly_fields = [field.name for field in TaskHistory._meta.fields]
    date_hierarchy = "started_at"


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
