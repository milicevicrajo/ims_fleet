from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.middleware.csrf import get_token
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin

from ..filters import ProcurementCaseFilter
from ..forms import ProcurementCaseForm, ProcurementItemForm, ProcurementItemInvoiceLinkForm, ProcurementStatusLogForm
from ..models import (
    ProcurementCase,
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
    def get_queryset(self):
        return ProcurementCase.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Zahtevi za nabavku i uslugu"
        return ctx


def _procurement_case_base_queryset():
    return (
        ProcurementCase.objects.select_related(
            "supplier", "contract", "vehicle", "job_code", "responsible"
        )
        .prefetch_related("vehicle__traffic_cards")
    )


def _truncate_text(value, max_length):
    text = str(value or "")
    visible = f"{text[:max_length]}..." if len(text) > max_length else text
    return f'<span title="{escape(text)}">{escape(visible)}</span>'


def _case_type_html(procurement_case):
    icon = {
        ProcurementCase.CaseType.SERVICE: "mdi-briefcase-check",
        ProcurementCase.CaseType.EQUIPMENT: "mdi-tools",
    }.get(procurement_case.case_type, "mdi-cart-outline")
    return (
        '<span class="assignment-status type">'
        f'<i class="mdi {icon}"></i> {escape(procurement_case.get_case_type_display())}'
        "</span>"
    )


def _case_status_html(procurement_case):
    icon = {
        ProcurementCase.Status.COMPLETED: "mdi-check-circle",
        ProcurementCase.Status.CANCELLED: "mdi-close-circle",
        ProcurementCase.Status.WAITING_INVOICE: "mdi-file-document-check",
        ProcurementCase.Status.INVOICE_LINKED: "mdi-file-document-check",
        ProcurementCase.Status.IN_PROGRESS: "mdi-progress-clock",
    }.get(procurement_case.status, "mdi-file-document-outline")
    return (
        f'<span class="assignment-status {escape(procurement_case.status)}">'
        f'<i class="mdi {icon}"></i> {escape(procurement_case.get_status_display())}'
        "</span>"
    )


def _case_garage_html(procurement_case):
    if not procurement_case.is_garage:
        return '<span class="assignment-status regular"><i class="mdi mdi-domain"></i> Ne</span>'
    traffic_card = next(iter(procurement_case.vehicle.traffic_cards.all()), None) if procurement_case.vehicle else None
    registration = (
        f'<span class="case-muted">{escape(traffic_card.registration_number)}</span>'
        if traffic_card
        else ""
    )
    return f'<span class="assignment-status garage"><i class="mdi mdi-car-wrench"></i> Da</span>{registration}'


def _case_job_code_html(procurement_case):
    if not procurement_case.job_code:
        return "/"
    name = procurement_case.job_code.name or ""
    return (
        f'<span class="badge bg-light text-dark border" title="{escape(name)}">'
        f"{escape(procurement_case.job_code.code)}</span>"
        + (f'<span class="case-muted">{_truncate_text(name, 48)}</span>' if name else "")
    )


def _case_actions_html(request, procurement_case):
    print_url = reverse("nabavka:case_print", kwargs={"pk": procurement_case.pk})
    repeat_url = reverse("nabavka:case_repeat", kwargs={"pk": procurement_case.pk})
    update_url = reverse("nabavka:case_update", kwargs={"pk": procurement_case.pk})
    csrf_token = escape(get_token(request))
    return (
        f'<a class="btn btn-outline-secondary btn-sm" href="{print_url}" target="_blank" title="Stampa">'
        '<i class="mdi mdi-printer"></i></a> '
        f'<form method="post" action="{repeat_url}" class="d-inline">'
        f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'
        '<button class="btn btn-outline-info btn-sm" type="submit" title="Ponovi zahtev">'
        '<i class="mdi mdi-content-copy"></i></button></form> '
        f'<a class="btn btn-outline-primary btn-sm" href="{update_url}">'
        '<i class="mdi mdi-pencil"></i> Izmeni</a>'
    )


class ProcurementCaseDataView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:case_list"

    def get(self, request):
        cases = ProcurementCaseFilter(request.GET, queryset=_procurement_case_base_queryset()).qs
        search_value = request.GET.get("search[value]", "").strip()
        if search_value:
            cases = cases.filter(
                Q(case_number__icontains=search_value)
                | Q(title__icontains=search_value)
                | Q(description__icontains=search_value)
                | Q(supplier__name__icontains=search_value)
                | Q(job_code__code__icontains=search_value)
                | Q(job_code__name__icontains=search_value)
                | Q(vehicle__traffic_cards__registration_number__icontains=search_value)
            ).distinct()

        records_total = ProcurementCase.objects.count()
        records_filtered = cases.count()
        order_map = {
            "0": "case_number",
            "1": "title",
            "2": "case_type",
            "3": "status",
            "4": "is_garage",
            "5": "job_code__code",
            "6": "supplier__name",
            "7": "needed_by",
        }
        order_field = order_map.get(request.GET.get("order[0][column]", "0"), "created_at")
        if request.GET.get("order[0][dir]", "desc") == "desc":
            order_field = f"-{order_field}"
        cases = cases.order_by(order_field, "-id")

        try:
            start = max(int(request.GET.get("start", 0)), 0)
        except (TypeError, ValueError):
            start = 0
        try:
            length = int(request.GET.get("length", 50))
        except (TypeError, ValueError):
            length = 50
        if length < 0:
            length = 50
        length = min(length, 200)

        rows = []
        for procurement_case in cases[start:start + length]:
            detail_url = reverse("nabavka:case_detail", kwargs={"pk": procurement_case.pk})
            amount = (
                f'<span class="case-muted">{procurement_case.estimated_value:.2f} '
                f"{escape(procurement_case.currency)}</span>"
                if procurement_case.estimated_value is not None
                else ""
            )
            rows.append(
                {
                    "case_number": (
                        f'<a href="{detail_url}" class="btn btn-sm btn-outline-primary">'
                        f'<i class="mdi mdi-eye"></i> {escape(procurement_case.case_number or procurement_case.pk)}</a>'
                    ),
                    "title": f'<strong class="case-title">{_truncate_text(procurement_case.title, 20)}</strong>{amount}',
                    "case_type": _case_type_html(procurement_case),
                    "status": _case_status_html(procurement_case),
                    "is_garage": _case_garage_html(procurement_case),
                    "job_code": _case_job_code_html(procurement_case),
                    "supplier": _truncate_text(procurement_case.supplier.name, 50) if procurement_case.supplier else "/",
                    "needed_by": procurement_case.needed_by.strftime("%d.%m.%Y") if procurement_case.needed_by else "/",
                    "actions": _case_actions_html(request, procurement_case),
                    "DT_RowClass": (
                        "assignment-closed"
                        if procurement_case.status in {
                            ProcurementCase.Status.COMPLETED,
                            ProcurementCase.Status.CANCELLED,
                        }
                        else ""
                    ),
                }
            )
        try:
            draw = int(request.GET.get("draw", 0))
        except (TypeError, ValueError):
            draw = 0
        return JsonResponse(
            {
                "draw": draw,
                "recordsTotal": records_total,
                "recordsFiltered": records_filtered,
                "data": rows,
            }
        )


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
                "unlinked_items_count": self.object.items.filter(invoice_link__isnull=True).count(),
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


class ProcurementCaseMaterialRequisitionPrintView(ProcurementCasePrintView):
    template_name = "nabavka/material_requisition_print.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["print_date"] = timezone.localdate()
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


class ProcurementCaseInvoiceLinkCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:item_invoice_link_create"

    def post(self, request, case_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        invoice = get_object_or_404(ProcurementInvoice, pk=request.POST.get("invoice"))
        note = (request.POST.get("note") or "").strip()
        items = list(
            ProcurementItem.objects.filter(
                procurement_case=procurement_case,
                invoice_link__isnull=True,
            ).order_by("id")
        )

        if not items:
            messages.warning(request, "Sve stavke su vec povezane sa fakturom.")
            return redirect("nabavka:case_detail", pk=procurement_case.pk)

        ProcurementItemInvoiceLink.objects.bulk_create(
            [
                ProcurementItemInvoiceLink(
                    procurement_item=item,
                    invoice=invoice,
                    note=note,
                    created_by=request.user,
                )
                for item in items
            ]
        )

        if procurement_case.status == ProcurementCase.Status.WAITING_INVOICE:
            procurement_case.status = ProcurementCase.Status.INVOICE_LINKED
            procurement_case.save(update_fields=["status", "updated_at"])

        messages.success(
            request,
            f"Faktura {invoice.invoice_number} je povezana sa {len(items)} stavki.",
        )
        return redirect("nabavka:case_detail", pk=procurement_case.pk)


class ProcurementItemInvoiceLinkDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk, item_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        procurement_item = get_object_or_404(ProcurementItem, pk=item_pk, procurement_case=procurement_case)
        link = get_object_or_404(ProcurementItemInvoiceLink, procurement_item=procurement_item)
        link.delete()
        messages.success(request, "Veza stavke i fakture je obrisana.")
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
