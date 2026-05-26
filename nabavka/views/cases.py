from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin

from ..filters import ProcurementCaseFilter
from ..forms import ProcurementCaseForm, ProcurementContractLinkForm, ProcurementItemForm, ProcurementStatusLogForm
from ..models import ProcurementCase, ProcurementContractLink, ProcurementItem, ProcurementStatusLog


class NabavkaContextMixin:
    current_app = "nabavka"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_app"] = "nabavka"
        ctx["sidebar_template"] = "sidebar_nabavka.html"
        return ctx


class DashboardView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": "Nabavka",
                "total_cases": ProcurementCase.objects.count(),
                "open_cases": ProcurementCase.objects.exclude(
                    status__in=[ProcurementCase.Status.COMPLETED, ProcurementCase.Status.CANCELLED]
                ).count(),
                "waiting_invoice": ProcurementCase.objects.filter(
                    status=ProcurementCase.Status.WAITING_INVOICE
                ).count(),
                "recent_cases": ProcurementCase.objects.select_related(
                    "supplier", "job_code", "responsible"
                )[:8],
            }
        )
        return ctx


class ProcurementCaseListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, FilterView):
    model = ProcurementCase
    template_name = "nabavka/case_list.html"
    context_object_name = "cases"
    filterset_class = ProcurementCaseFilter
    paginate_by = 50

    def get_queryset(self):
        return ProcurementCase.objects.select_related(
            "supplier", "contract", "vehicle", "job_code", "responsible"
        ).order_by("-created_at", "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Zahtevi i procesi nabavke"
        return ctx


class ProcurementCaseCreateView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ProcurementCase
    form_class = ProcurementCaseForm
    template_name = "nabavka/case_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if not form.instance.responsible_id:
            form.instance.responsible = self.request.user
        response = super().form_valid(form)
        ProcurementStatusLog.objects.create(
            procurement_case=self.object,
            old_status=None,
            new_status=self.object.status,
            comment="Kreiran predmet nabavke.",
            created_by=self.request.user,
        )
        messages.success(self.request, "Predmet nabavke je sačuvan.")
        return response

    def get_success_url(self):
        return reverse("nabavka:case_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi predmet nabavke"
        ctx["submit_button_label"] = "Sačuvaj"
        return ctx


class ProcurementCaseUpdateView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = ProcurementCase
    form_class = ProcurementCaseForm
    template_name = "nabavka/case_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.old_status = self.get_object().status
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.old_status != self.object.status:
            ProcurementStatusLog.objects.create(
                procurement_case=self.object,
                old_status=self.old_status,
                new_status=self.object.status,
                comment="Status promenjen kroz izmenu predmeta.",
                created_by=self.request.user,
            )
        messages.success(self.request, "Predmet nabavke je ažuriran.")
        return response

    def get_success_url(self):
        return reverse("nabavka:case_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Izmena: {self.object.case_number}"
        ctx["submit_button_label"] = "Sačuvaj izmene"
        return ctx


class ProcurementCaseDetailView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = ProcurementCase
    template_name = "nabavka/case_detail.html"
    context_object_name = "case"

    def get_queryset(self):
        return ProcurementCase.objects.select_related(
            "supplier",
            "contract",
            "vehicle",
            "job_code",
            "responsible",
            "created_by",
            "fleet_procurement_request",
        ).prefetch_related(
            "items",
            "invoice_links",
            "contract_links__contract",
            "purchase_orders",
            "status_logs__created_by",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": str(self.object),
                "item_form": ProcurementItemForm(),
                "contract_link_form": ProcurementContractLinkForm(procurement_case=self.object),
                "status_log_form": ProcurementStatusLogForm(initial={"new_status": self.object.status}),
            }
        )
        return ctx


class ProcurementCaseDeleteView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = ProcurementCase
    template_name = "nabavka/confirm_delete.html"
    success_url = reverse_lazy("nabavka:case_list")
    context_object_name = "object"


class ProcurementItemCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        form = ProcurementItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.procurement_case = procurement_case
            item.save()
            messages.success(request, "Stavka je dodata.")
        else:
            messages.error(request, "Stavka nije sačuvana. Proverite unete podatke.")
        return redirect("nabavka:case_detail", pk=procurement_case.pk)


class ProcurementItemDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk, item_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        get_object_or_404(ProcurementItem, pk=item_pk, procurement_case=procurement_case).delete()
        messages.success(request, "Stavka je obrisana.")
        return redirect("nabavka:case_detail", pk=procurement_case.pk)


class ProcurementContractLinkCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        form = ProcurementContractLinkForm(request.POST, procurement_case=procurement_case)
        if form.is_valid():
            link = form.save(commit=False)
            link.procurement_case = procurement_case
            link.created_by = request.user
            link.save()
            messages.success(request, "Ugovor je povezan.")
        else:
            messages.error(request, "Ugovor nije povezan. Proverite unete podatke.")
        return redirect("nabavka:case_detail", pk=procurement_case.pk)


class ProcurementContractLinkDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk, link_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        get_object_or_404(ProcurementContractLink, pk=link_pk, procurement_case=procurement_case).delete()
        messages.success(request, "Veza ugovora je obrisana.")
        return redirect("nabavka:case_detail", pk=procurement_case.pk)


class ProcurementStatusLogCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        form = ProcurementStatusLogForm(request.POST)
        if form.is_valid():
            old_status = procurement_case.status
            new_status = form.cleaned_data["new_status"]
            comment = form.cleaned_data.get("comment")
            procurement_case.status = new_status
            procurement_case.save(update_fields=["status", "updated_at"])
            ProcurementStatusLog.objects.create(
                procurement_case=procurement_case,
                old_status=old_status,
                new_status=new_status,
                comment=comment,
                created_by=request.user,
            )
            messages.success(request, "Status je ažuriran.")
        else:
            messages.error(request, "Status nije ažuriran.")
        return redirect("nabavka:case_detail", pk=procurement_case.pk)
