from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.exporting import rows_to_xlsx_response
from core.mixins import RolePermissionRequiredMixin

from ..forms.lease import LeaseForm
from ..models import Lease
from ..support.lease_queries import lease_monthly_costs_rows

LONG_TERM_LEASE_TYPES = set(Lease.LONG_TERM_LEASE_TYPE_VALUES)


class LeaseListView(LoginRequiredMixin, ListView):
    model = Lease
    template_name = "fleet/lease_list.html"
    context_object_name = "leases"

    @staticmethod
    def _is_truthy(value):
        return str(value).lower() in {"1", "true", "yes", "on", "da"}

    def _show_expired(self):
        return self._is_truthy(self.request.GET.get("prikazi_istekle"))

    def _build_url(self, url_name, tip=None, show_expired=None):
        params = {}
        if tip:
            params["tip"] = tip
        if show_expired is None:
            show_expired = self._show_expired()
        if show_expired:
            params["prikazi_istekle"] = "1"

        url = reverse(url_name)
        if params:
            return f"{url}?{urlencode(params)}"
        return url

    def get_queryset(self):
        qs = super().get_queryset().select_related("vehicle")
        tip = self.request.GET.get("tip")
        if tip == "dugorocni":
            qs = qs.filter(lease_type__in=LONG_TERM_LEASE_TYPES)
        elif tip in {"finansijski", "operativni"}:
            qs = qs.filter(lease_type=tip)

        if not self._show_expired():
            qs = qs.filter(end_date__gte=timezone.localdate())
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Lizing i najam ugovori"
        active_tip = self.request.GET.get("tip")
        show_expired = self._show_expired()
        ctx["active_tip"] = active_tip
        ctx["show_expired"] = show_expired
        ctx["export_url"] = self._build_url("export_leases")
        ctx["lease_filter_links"] = {
            "all": self._build_url("lease_list"),
            "finansijski": self._build_url("lease_list", "finansijski"),
            "operativni": self._build_url("lease_list", "operativni"),
            "dugorocni": self._build_url("lease_list", "dugorocni"),
        }
        ctx["only_active_url"] = self._build_url("lease_list", tip=active_tip, show_expired=False)
        ctx["show_expired_url"] = self._build_url("lease_list", tip=active_tip, show_expired=True)
        return ctx


class LeaseCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Lease
    form_class = LeaseForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("lease_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiraj novi zakup"
        context["submit_button_label"] = "Dodaj zakup"
        return context


def export_leases_to_excel(request):
    tip = request.GET.get("tip")
    show_expired = LeaseListView._is_truthy(request.GET.get("prikazi_istekle"))
    leases = Lease.objects.select_related("vehicle").all()
    if tip == "dugorocni":
        leases = leases.filter(lease_type__in=LONG_TERM_LEASE_TYPES)
    elif tip in {"finansijski", "operativni"}:
        leases = leases.filter(lease_type=tip)

    if not show_expired:
        leases = leases.filter(end_date__gte=timezone.localdate())

    headers = [
        "Vozilo (sasija)",
        "Šifra partnera",
        "Naziv partnera",
        "Šifra posla",
        "Broj ugovora",
        "Trenutna vrednost otplate",
        "Vrsta lizinga",
        "Datum početka",
        "Datum završetka",
        "Napomena",
    ]
    rows = [
        [
            lease.vehicle.chassis_number if lease.vehicle else "",
            lease.partner_code,
            lease.partner_name,
            lease.job_code,
            lease.contract_number,
            float(lease.current_payment_amount or 0),
            lease.lease_type_label,
            lease.start_date.strftime("%d.%m.%Y") if lease.start_date else "",
            lease.end_date.strftime("%d.%m.%Y") if lease.end_date else "",
            lease.note or "",
        ]
        for lease in leases
    ]

    fname = f"lizing_ugovori_{tip or 'svi'}.xlsx"
    return rows_to_xlsx_response(fname, "Lizing ugovori", headers, rows, quoted=True)


class LeaseUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Lease
    form_class = LeaseForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("lease_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni zakup"
        context["submit_button_label"] = "Sacuvaj izmene"
        return context


class LeaseDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Lease
    template_name = "fleet/lease_detail.html"
    context_object_name = "lease"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Detalji zakupa {self.object.partner_name}"
        return context


class LeaseDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Lease
    success_url = reverse_lazy("lease_list")
    template_name = "fleet/lease_confirm_delete.html"
    context_object_name = "lease"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obrisi zakup"
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)


class LeaseMonthlyCostsView(LoginRequiredMixin, ListView):
    template_name = "fleet/reports/lease_monthly_costs.html"
    context_object_name = "rows"
    paginate_by = 200

    def get_queryset(self):
        return lease_monthly_costs_rows(self.request)
