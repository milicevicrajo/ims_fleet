from django.contrib import admin
from .models import *


class NaplataAdmin(admin.ModelAdmin):
	using = "naplata_db"

	def get_queryset(self, request):
		return super().get_queryset(request).using(self.using)

	def save_model(self, request, obj, form, change):
		obj.save(using=self.using)

	def delete_model(self, request, obj):
		obj.delete(using=self.using)


admin.site.register(Kontakti, NaplataAdmin)
admin.site.register(Napomene, NaplataAdmin)
admin.site.register(Opomene, NaplataAdmin)
admin.site.register(PozivPismo, NaplataAdmin)
admin.site.register(PoziviTel, NaplataAdmin)
admin.site.register(SifBaket, NaplataAdmin)
admin.site.register(SifKategorija, NaplataAdmin)
admin.site.register(Tuzbe, NaplataAdmin)