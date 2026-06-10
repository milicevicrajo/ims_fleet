from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('fleet.urls')),  # Ovo povezuje URLs iz fleet aplikacije
    path("hr/", include(("hr.urls", "hr"), namespace="hr")),
    path("naplata/", include(("naplata.urls", "naplata"), namespace="naplata")),
    path("isplate/", include(("isplate.urls", "isplate"), namespace="isplate")),
    path("menice/", include(("menice.urls", "menice"), namespace="menice")),
    path("ugovori/", include(("ugovori.urls", "ugovori"), namespace="ugovori")),
    path("nabavka/", include(("nabavka.urls", "nabavka"), namespace="nabavka")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
