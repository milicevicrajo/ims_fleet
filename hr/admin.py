from django.contrib import admin

from .models import WorkTimeSheet, WorkTimeSheetLine


class WorkTimeSheetLineInline(admin.TabularInline):
    model = WorkTimeSheetLine
    extra = 0
    fields = ("line_number", "organizational_unit", "total_hours", "work_conditions", "note")
    readonly_fields = ("total_hours",)


@admin.register(WorkTimeSheet)
class WorkTimeSheetAdmin(admin.ModelAdmin):
    list_display = ("employee", "month", "year", "status", "total_hours", "updated_at")
    list_filter = ("year", "month", "status")
    search_fields = ("employee__first_name", "employee__last_name", "employee__employee_code")
    inlines = [WorkTimeSheetLineInline]
