from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.exporting import rows_to_xlsx_response
from core.mixins import RolePermissionRequiredMixin

from ..lease_forms import LeaseForm
from ..models import Lease
from ..queries import lease_monthly_costs_rows

LONG_TERM_LEASE_TYPES = set(Lease.LONG_TERM_LEASE_TYPE_VALUES)


class LeaseListView(LoginRequiredMixin, ListView):
    model = Lease
    template_name = "fleet/lease_list.html"
    context_object_name = "leases"

    def get_queryset(self):
        qs = super().get_queryset().select_related("vehicle")
        tip = self.request.GET.get("tip")
        if tip == "dugorocni":
            qs = qs.filter(lease_type__in=LONG_TERM_LEASE_TYPES)
        elif tip in {"finansijski", "operativni"}:
            qs = qs.filter(lease_type=tip)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Lizing i najam ugovori"
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
    leases = Lease.objects.select_related("vehicle").all()
    if tip == "dugorocni":
        leases = leases.filter(lease_type__in=LONG_TERM_LEASE_TYPES)
    elif tip in {"finansijski", "operativni"}:
        leases = leases.filter(lease_type=tip)

    headers = [
        "Vozilo (sasija)",
        "Sifra partnera",
        "Naziv partnera",
        "Sifra posla",
        "Broj ugovora",
        "Trenutna vrednost otplate",
        "Vrsta lizinga",
        "Datum pocetka",
        "Datum zavrsetka",
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
