from django.contrib import admin

from .models import MobileAssignment, MobileImportLog, MobilePackage, MobileUsage, MobileUser


admin.site.register(MobilePackage)
admin.site.register(MobileUser)
admin.site.register(MobileAssignment)
admin.site.register(MobileUsage)
admin.site.register(MobileImportLog)

