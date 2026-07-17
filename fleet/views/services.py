import csv
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_filters.views import FilterView

from core.exporting import csv_attachment_response
from core.mixins import RolePermissionRequiredMixin

from ..filters import ServiceFixingFilter, ServiceMonthlyCostsFilter
from ..forms.services import (
    DraftServiceTransactionForm,
    RequisitionForm,
    ServiceForm,
    ServiceTransactionForm,
    ServiceTypeForm,
)
from ..models import (
    DraftServiceTransaction,
    Requisition,
    Service,
    ServiceTransaction,
    ServiceType,
)
from ..support.service_queries import service_monthly_costs_rows
from ..sync import (
    fetch_requisition_data,
    fetch_service_data,
    migrate_draft_to_service_transaction,
)

logger = logging.getLogger(__name__)


class ServiceTypeListView(LoginRequiredMixin, ListView):
    model = ServiceType
    template_name = "fleet/servicetype_list.html"
    context_object_name = "service_types"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista tipova servisa"
        return context


class ServiceTypeCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("servicetype_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dodaj tip servisa"
        context["submit_button_label"] = "Dodaj"
        return context


class ServiceTypeUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("servicetype_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni tip servisa"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class ServiceTypeDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = ServiceType
    template_name = "fleet/servicetype_detail.html"
    context_object_name = "service_type"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Detalji tipa servisa {self.object.name}"
        return context


class ServiceTypeDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = ServiceType
    success_url = reverse_lazy("servicetype_list")
    template_name = "fleet/servicetype_confirm_delete.html"
    context_object_name = "service_type"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obriši tip servisa"
        return context


class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = "fleet/service_list.html"
    context_object_name = "services"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista servisa"
        return context


class ServiceFixingListView(LoginRequiredMixin, FilterView):
    model = DraftServiceTransaction
    template_name = "fleet/draft_service_transactions_list.html"
    context_object_name = "service_transactions"
    filterset_class = ServiceFixingFilter

    def get_queryset(self):
        return (
            DraftServiceTransaction.objects.select_related("vehicle", "popravka_kategorija")
            .order_by("-datum", "-id")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = ctx["filter"].form
        return ctx


class ServiceCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("service_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dodaj servis"
        context["submit_button_label"] = "Dodaj"
        return context


class ServiceUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("service_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni servis"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class ServiceDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Service
    template_name = "fleet/service_detail.html"
    context_object_name = "service"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Detalji servisa {self.object.service_date}"
        return context


class ServiceDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Service
    success_url = reverse_lazy("service_list")
    template_name = "fleet/service_confirm_delete.html"
    context_object_name = "service"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obriši servis"
        return context


class ServiceTransactionListView(LoginRequiredMixin, ListView):
    model = ServiceTransaction
    template_name = "fleet/service_transactions_list.html"
    context_object_name = "service_transactions"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista servisa - popravke van IMS-a"
        return context


@method_decorator(never_cache, name="dispatch")
class ServiceTransactionFixingListView(LoginRequiredMixin, FilterView):
    model = DraftServiceTransaction
    template_name = "fleet/draft_service_transactions_list.html"
    context_object_name = "service_transactions"
    filterset_class = ServiceFixingFilter

    def get_queryset(self):
        return (
            DraftServiceTransaction.objects.select_related("vehicle", "popravka_kategorija")
            .order_by("-datum", "-id")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Lista servisa koje morate dopuniti"
        ctx["form"] = ctx["filter"].form
        return ctx


class ServiceTransactionCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ServiceTransaction
    form_class = ServiceTransactionForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("service_transaction_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiranje servisa"
        context["submit_button_label"] = "Sačuvaj insformacije o servisu"
        return context


class ServiceTransactionUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = ServiceTransaction
    form_class = ServiceTransactionForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("service_transaction_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmena servisa"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class ServiceTransactionDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = ServiceTransaction
    template_name = "service_transaction_confirm_delete.html"
    success_url = reverse_lazy("service_transaction_list")


class DraftServiceTransactionUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = DraftServiceTransaction
    form_class = DraftServiceTransactionForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("service_fixing_list")

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return str(self.success_url)

    def form_valid(self, form):
        draft = form.save(commit=False)
        logger.info("Izmene sačuvane u draft tabeli.")

        is_complete = all(
            [
                draft.vehicle_id is not None,
                draft.god is not None,
                draft.sif_par_pl not in [None, ""],
                draft.naz_par_pl not in [None, ""],
                draft.datum is not None,
                draft.sif_vrs not in [None, ""],
                draft.br_naloga not in [None, ""],
                draft.vez_dok not in [None, ""],
                draft.knt_pl not in [None, ""],
                draft.potrazuje is not None,
                draft.sif_par_npl not in [None, ""],
                draft.knt_npl not in [None, ""],
                draft.duguje is not None,
                draft.konto_vozila not in [None, ""],
                draft.popravka_kategorija not in [None, ""],
            ]
        )

        if is_complete:
            draft.save()
            migrate_draft_to_service_transaction(draft.id)
            logger.info("Podaci migrirani u glavnu tabelu.")
            messages.success(self.request, "✅ Podaci su uspešno migrirani u glavnu tabelu.")
            return redirect(self.get_success_url())

        logger.info("Podaci nisu kompletni, ostaju u draft tabeli.")
        messages.warning(self.request, "⚠️ Podaci nisu kompletni, ostaju u draft tabeli.")
        draft.save()
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dopunite informacije o servisu"
        context["submit_button_label"] = "Sačuvaj insformacije o servisu"
        return context


class RequisitionListView(LoginRequiredMixin, ListView):
    model = Requisition
    template_name = "fleet/requisition_list.html"
    context_object_name = "requisitions"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Trebovanja"
        return context


class RequisitionDetailView(LoginRequiredMixin, ListView):
    model = Requisition
    template_name = "fleet/requisition_detail.html"
    context_object_name = "stavke"

    def get_queryset(self):
        return Requisition.objects.filter(
            br_dok=self.kwargs["br_dok"],
            god=self.kwargs["god"],
        ).order_by("stavka")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["br_dok"] = self.kwargs["br_dok"]
        context["god"] = self.kwargs["god"]
        return context


class RequisitionFixingListView(LoginRequiredMixin, ListView):
    model = Requisition
    template_name = "fleet/requisition_fixing_list.html"
    context_object_name = "requisitions"

    def get_queryset(self):
        return (
            Requisition.objects.select_related("vehicle", "popravka_kategorija")
            .filter(nije_garaza=False)
            .filter(vehicle__isnull=True)
            .order_by("-datum_trebovanja", "-id")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Trebovanja bez povezanog vozila"
        return context


class RequisitionCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Requisition
    form_class = RequisitionForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("requisition_list")
    success_message = "Requisition successfully created."


class RequisitionUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Requisition
    form_class = RequisitionForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("requisition_list")
    success_message = "Trebovanje uspešno izmenjeno!"

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return str(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmena trebovanja"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class RequisitionDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Requisition
    template_name = "requisition/requisition_confirm_delete.html"
    success_url = reverse_lazy("requisition_list")
    success_message = "Requisition successfully deleted."


def fetch_service_data_view(request):
    if request.method == "POST":
        days_str = request.POST.get("days", "").strip()

        days = None
        if days_str:
            try:
                days = int(days_str)
                if days <= 0:
                    messages.error(request, "Broj dana mora biti pozitivan broj.")
                    return redirect("fetch_service_data")
            except ValueError:
                messages.error(request, "Uneta vrednost za broj dana nije validna.")
                return redirect("fetch_service_data")

        result = fetch_service_data(last_24_hours=(days is None), days=days)
        messages.success(request, result)
        return redirect("service_transaction_list")

    return render(request, "fleet/fetch_service_data.html")


def fetch_requisition_data_view(request):
    if request.method == "POST":
        days = request.POST.get("days", None)
        if days:
            try:
                days = int(days)
            except ValueError:
                messages.error(request, "Uneta vrednost za broj dana nije validna.")
                return redirect("fetch_policies")

        result = fetch_requisition_data(last_24_hours=False, days=days)
        messages.success(request, result)
        return redirect("requisition_list")

    return render(request, "fleet/fetch_data.html")


class ServiceMonthlyCostsView(LoginRequiredMixin, FilterView):
    template_name = "fleet/reports/service_monthly_costs.html"
    context_object_name = "rows"
    filterset_class = ServiceMonthlyCostsFilter

    def get_queryset(self):
        return service_monthly_costs_rows(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Mesečni troškovi servisa po centru"
        return ctx


@login_required
def service_monthly_costs_csv(request):
    rows = service_monthly_costs_rows(request)

    resp = csv_attachment_response("service_monthly_costs.csv", charset=None, quoted=True)
    w = csv.writer(resp)
    w.writerow(["Godina", "Mesec", "OJ", "Centar", "Ukupan trosak"])

    for r in rows:
        w.writerow([
            r["year"],
            r["month"],
            r.get("oj_code_txt") or "",
            r.get("center_code_txt") or "",
            f"{r['iznos']:.2f}",
        ])

    return resp
