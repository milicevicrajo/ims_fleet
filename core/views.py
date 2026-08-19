from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET


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
    allowed = {"fleet", "naplata", "isplate", "pravna", "kadrovi", "administracija", "menice", "ugovori", "nabavka", "mobilni"}
    if app_slug in allowed:
        request.session["current_app"] = app_slug
    # posle promene aplikacije vodi na dashboard koji će birati pravi template
    return redirect(request.GET.get("next") or "dashboard")
