from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin

from ..filters import ProcurementCaseFilter
from ..forms import ProcurementCaseForm, ProcurementContractLinkForm, ProcurementItemForm, ProcurementItemInvoiceLinkForm, ProcurementStatusLogForm
from ..models import (
    ProcurementCase,
    ProcurementContractLink,
    ProcurementInvoice,
    ProcurementItem,
    ProcurementItemInvoiceLink,
    ProcurementStatusLog,
)


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
        today = timezone.localdate()
        open_status_filter = {
            "status__in": [ProcurementCase.Status.COMPLETED, ProcurementCase.Status.CANCELLED]
        }
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
                "garage_cases": ProcurementCase.objects.filter(is_garage=True).count(),
                "overdue_cases": ProcurementCase.objects.exclude(**open_status_filter).filter(
                    needed_by__lt=today
                ).count(),
                "recent_cases": ProcurementCase.objects.select_related(
                    "supplier", "job_code", "responsible"
                ).order_by("-created_at", "-id")[:8],
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
        ).prefetch_related(
            Prefetch("items", queryset=ProcurementItem.objects.select_related("invoice_link__invoice").order_by("id")),
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
                "item_invoice_form": ProcurementItemInvoiceLinkForm(),
                "available_invoices": ProcurementInvoice.objects.all().order_by("-invoice_date", "-id")[:500],
                "item_invoice_links": ProcurementItemInvoiceLink.objects.select_related(
                    "procurement_item",
                    "invoice",
                    "created_by",
                ).filter(procurement_item__procurement_case=self.object),
                "contract_link_form": ProcurementContractLinkForm(procurement_case=self.object),
                "status_log_form": ProcurementStatusLogForm(initial={"new_status": self.object.status}),
            }
        )
        return ctx


class ProcurementCasePrintView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/case_print.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        procurement_case = get_object_or_404(
            ProcurementCase.objects.select_related("job_code"),
            pk=kwargs.get("pk"),
        )

        max_rows = 12
        items = list(procurement_case.items.all().order_by("id"))
        rows_pages = []

        if not items:
            rows_pages.append([None] * max_rows)
        else:
            for index in range(0, len(items), max_rows):
                chunk = items[index : index + max_rows]
                padded = chunk + [None] * max(0, max_rows - len(chunk))
                rows_pages.append(padded)

        job_code = procurement_case.job_code

        ctx.update(
            {
                "rows_pages": rows_pages,
                "proc_case": procurement_case,
                "job_code": job_code,
                "center": getattr(job_code, "center", "") if job_code else "",
                "auto_print": self.request.GET.get("auto") == "1",
                "next_url": self.request.GET.get("next") or reverse("nabavka:case_detail", kwargs={"pk": procurement_case.pk}),
            }
        )
        return ctx


class ProcurementCaseDeleteView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = ProcurementCase
    template_name = "nabavka/confirm_delete.html"
    success_url = reverse_lazy("nabavka:case_list")
    context_object_name = "object"


class ProcurementCaseRepeatView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:case_create"

    def post(self, request, pk):
        source = get_object_or_404(
            ProcurementCase.objects.select_related(
                "supplier",
                "contract",
                "vehicle",
                "job_code",
                "responsible",
            ).prefetch_related("items"),
            pk=pk,
        )

        with transaction.atomic():
            repeated_case = ProcurementCase.objects.create(
                case_type=source.case_type,
                status=ProcurementCase.Status.DRAFT,
                title=source.title,
                description=source.description,
                is_garage=source.is_garage,
                job_code=source.job_code,
                supplier=source.supplier,
                contract=source.contract,
                vehicle=source.vehicle,
                responsible=request.user,
                estimated_value=source.estimated_value,
                currency=source.currency,
                needed_by=timezone.localdate() + timedelta(days=7),
                note=source.note,
                created_by=request.user,
            )
            ProcurementItem.objects.bulk_create(
                [
                    ProcurementItem(
                        procurement_case=repeated_case,
                        name=item.name,
                        uom=item.uom,
                        quantity=item.quantity,
                        estimated_unit_price=item.estimated_unit_price,
                        note=item.note,
                    )
                    for item in source.items.all()
                ]
            )
            ProcurementStatusLog.objects.create(
                procurement_case=repeated_case,
                old_status=None,
                new_status=repeated_case.status,
                comment=f"Ponovljen zahtev {source.case_number}.",
                created_by=request.user,
            )

        messages.success(
            request,
            f"Kreiran je novi zahtev {repeated_case.case_number} sa kopiranim stavkama.",
        )
        return redirect("nabavka:case_detail", pk=repeated_case.pk)


class ProcurementItemCreateView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ProcurementItem
    form_class = ProcurementItemForm
    template_name = "nabavka/item_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.procurement_case = get_object_or_404(ProcurementCase, pk=kwargs["case_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.procurement_case = self.procurement_case
        messages.success(self.request, "Stavka je dodata.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("nabavka:case_detail", kwargs={"pk": self.procurement_case.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": f"Nova stavka - {self.procurement_case.case_number}",
                "procurement_case": self.procurement_case,
                "submit_button_label": "Dodaj stavku",
            }
        )
        return ctx


class ProcurementItemDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk, item_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        get_object_or_404(ProcurementItem, pk=item_pk, procurement_case=procurement_case).delete()
        messages.success(request, "Stavka je obrisana.")
        return redirect("nabavka:case_detail", pk=procurement_case.pk)


class ProcurementItemInvoiceLinkCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk, item_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        procurement_item = get_object_or_404(ProcurementItem, pk=item_pk, procurement_case=procurement_case)

        if hasattr(procurement_item, "invoice_link"):
            messages.warning(request, "Stavka je vec povezana sa fakturom.")
            return redirect("nabavka:case_detail", pk=procurement_case.pk)

        form = ProcurementItemInvoiceLinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.procurement_item = procurement_item
            link.created_by = request.user
            link.save()
            if procurement_case.status == ProcurementCase.Status.WAITING_INVOICE:
                procurement_case.status = ProcurementCase.Status.INVOICE_LINKED
                procurement_case.save(update_fields=["status", "updated_at"])
            messages.success(request, "Stavka je povezana sa fakturom.")
        else:
            messages.error(request, "Stavka nije povezana sa fakturom. Proverite izbor fakture.")
        return redirect("nabavka:case_detail", pk=procurement_case.pk)


class ProcurementItemInvoiceLinkDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk, item_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        procurement_item = get_object_or_404(ProcurementItem, pk=item_pk, procurement_case=procurement_case)
        link = get_object_or_404(ProcurementItemInvoiceLink, procurement_item=procurement_item)
        link.delete()
        messages.success(request, "Veza stavke i fakture je obrisana.")
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
