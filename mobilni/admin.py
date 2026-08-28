from django.contrib import admin

from .models import MobileAssignment, MobileImportLog, MobilePackage, MobileParkingExemption, MobileUsage, MobileUser


admin.site.register(MobilePackage)
admin.site.register(MobileUser)
admin.site.register(MobileAssignment)
admin.site.register(MobileUsage)
admin.site.register(MobileImportLog)


@admin.register(MobileParkingExemption)
class MobileParkingExemptionAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "created_at")
    search_fields = ("phone_number",)
