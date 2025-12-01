from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django_filters.views import FilterView
from django.views import View
from django.views.generic import CreateView, UpdateView, TemplateView

from .filters import KvarFilter
from .forms import KvarForm
from .models import Kvar


class KvarListView(LoginRequiredMixin, FilterView):
    model = Kvar
    template_name = "fleet/kvar_list.html"
    context_object_name = "kvarovi"
    filterset_class = KvarFilter

    def get_queryset(self):
        return (
            Kvar.objects.select_related("vehicle")
            .prefetch_related("vehicle__traffic_cards")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Kvarovi (garaza)"
        ctx["form"] = ctx["filter"].form
        return ctx


class GarazaHomeView(LoginRequiredMixin, TemplateView):
    template_name = "fleet/garaza_home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Poslovi garaze IMS"
        return ctx


class KvarCreateView(LoginRequiredMixin, CreateView):
    model = Kvar
    form_class = KvarForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("kvar_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Prijavi kvar"
        ctx["submit_button_label"] = "Sacuvaj"
        return ctx


class KvarUpdateView(LoginRequiredMixin, UpdateView):
    model = Kvar
    form_class = KvarForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("kvar_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmeni kvar"
        ctx["submit_button_label"] = "Sacuvaj izmene"
        return ctx


class KvarDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("kvar_list")

    def post(self, request, *args, **kwargs):
        kvar = get_object_or_404(Kvar, pk=kwargs.get("pk"))
        kvar.delete()
        messages.success(request, "Kvar je obrisan.")
        return redirect(self.success_url)

    def get(self, request, *args, **kwargs):
        return redirect(self.success_url)
