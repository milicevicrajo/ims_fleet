from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from urllib.parse import quote
from django_filters.views import FilterView
from django.views import View
from django.views.generic import CreateView, UpdateView, TemplateView

from .filters import KvarFilter
from .forms import KvarForm
from .models import Kvar, JobCode


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


class KvarPrintView(LoginRequiredMixin, TemplateView):
    template_name = "fleet/kvar_print.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kvar = get_object_or_404(
            Kvar.objects.select_related("vehicle"),
            pk=kwargs.get("pk"),
        )
        vehicle = kvar.vehicle
        traffic_card = vehicle.traffic_cards.order_by("-issue_date", "-id").first()
        latest_jobcode = (
            JobCode.objects.select_related("organizational_unit")
            .filter(vehicle=vehicle)
            .order_by("-assigned_date", "-id")
            .first()
        )

        ctx.update(
            {
                "kvar": kvar,
                "vehicle": vehicle,
                "registration_number": getattr(traffic_card, "registration_number", ""),
                "center": getattr(latest_jobcode.organizational_unit, "center", "")
                if latest_jobcode and latest_jobcode.organizational_unit
                else "",
                "organizational_unit": getattr(latest_jobcode, "organizational_unit", None),
                "next_url": self.request.GET.get("next") or reverse("kvar_list"),
                "auto_print": self.request.GET.get("auto") == "1",
            }
        )
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

    def form_valid(self, form):
        response = super().form_valid(form)
        print_url = reverse("kvar_print", args=[self.object.pk])
        next_url = quote(str(reverse("kvar_list")))
        return redirect(f"{print_url}?auto=1&next={next_url}")


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
