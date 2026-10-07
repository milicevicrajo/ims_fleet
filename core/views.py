from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, redirect_to_login
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.csrf import csrf_failure as django_csrf_failure
from django.views.decorators.http import require_GET, require_POST


def csrf_failure(request, reason="", template_name=None):
    """Posle odjave stari obrazac pada na CSRF proveri; to je istekla sesija, ne greška."""
    if not getattr(request.user, "is_authenticated", False):
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
    return django_csrf_failure(request, reason=reason)


class RequiredPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("my_employee_profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=["must_change_password"])
        messages.success(self.request, "Lozinka je promenjena.")
        return response


@require_GET
@login_required
def switch_app(request, app_slug):
    allowed = {"fleet", "naplata", "potrazivanja", "isplate", "pravna", "kadrovi", "administracija", "menice", "ugovori", "nabavka", "mobilni", "finansije", "organizacija", "arhiva"}
    if app_slug in allowed:
        request.session["current_app"] = app_slug
    # posle promene aplikacije vodi na dashboard koji će birati pravi template
    return redirect(request.GET.get("next") or "dashboard")


@login_required
def pocetna(request):
    """Početna strana aplikacije: opis, moduli, uloge i dozvole korisnika; bez bočnog menija.

    Ovde vodi prijava (`LOGIN_REDIRECT_URL = "/"`) i logo u zaglavlju. Stranu vidi svaki
    prijavljeni korisnik, pa nema sopstvenu proveru dozvole.
    """
    from core.pocetna import pocetna as podaci

    return render(request, "pocetna.html", {**podaci(request.user), "title": "IMS ERP — početna",
                                            "bez_menija": True, "current_app": "pocetna"})


@login_required
@require_POST
def novosti_procitano(request):
    """„Razumem” na obaveštenju o novostima modula: potvrda se čuva i novost se više ne prikazuje."""
    from .models import ProcitanaNovost
    from .novosti import NOVOSTI

    poznati = {n["kljuc"] for n in NOVOSTI}
    for kljuc in request.POST.getlist("kljuc"):
        if kljuc in poznati:
            ProcitanaNovost.objects.get_or_create(user=request.user, kljuc=kljuc)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    nazad = request.POST.get("next") or "/"
    return redirect(nazad if url_has_allowed_host_and_scheme(nazad, allowed_hosts={request.get_host()}) else "/")
