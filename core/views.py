from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

@require_GET
@login_required
def switch_app(request, app_slug):
    allowed = {"fleet", "naplata", "kadrovi", "administracija"}
    if app_slug in allowed:
        request.session["current_app"] = app_slug
    # posle promene aplikacije vodi na dashboard koji će birati pravi template
    return redirect(request.GET.get("next") or "dashboard")
