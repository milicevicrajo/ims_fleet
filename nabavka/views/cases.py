from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
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

from core.mixins import RolePermissionRequiredMixin, user_has_role_permission

from ..filters import ProcurementCaseFilter
from ..forms import (
    ProcurementCaseForm,
    ProcurementItemForm,
    ProcurementItemSourceLinkForm,
    ProcurementStatusLogForm,
)
from ..models import (
    EufItemSnapshot,
    GoodsSnapshot,
    ProcurementCase,
    ProcurementInvoice,
    ProcurementItem,
    ProcurementStatusLog,
)


class NabavkaContextMixin:
    current_app = "nabavka"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_app"] = "nabavka"
        ctx["sidebar_template"] = "sidebar_nabavka.html"
        return ctx


def _is_zahtev_only_user(user):
    return (
        not user.is_superuser
        and user.roles.filter(slug="zahtev").exists()
        and not user_has_role_permission(user, "nabavka:case_update")
    )


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
    actions = []
    if user_has_role_permission(request.user, "nabavka:case_print"):
        actions.append(
            f'<a class="btn btn-outline-secondary btn-sm" href="{print_url}" target="_blank" title="Stampa">'
            '<i class="mdi mdi-printer"></i></a>'
        )
    if user_has_role_permission(request.user, "nabavka:case_repeat"):
        actions.append(
            f'<form method="post" action="{repeat_url}" class="d-inline">'
            f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'
            '<button class="btn btn-outline-info btn-sm" type="submit" title="Ponovi zahtev">'
            '<i class="mdi mdi-content-copy"></i></button></form>'
        )
    if user_has_role_permission(request.user, "nabavka:case_update"):
        actions.append(
            f'<a class="btn btn-outline-primary btn-sm" href="{update_url}">'
            '<i class="mdi mdi-pencil"></i> Izmeni</a>'
        )
    return " ".join(actions)


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
        form.instance.status = ProcurementCase.Status.DRAFT
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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields.pop("status", None)
        return form

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
            Prefetch(
                "items",
                queryset=ProcurementItem.objects.select_related(
                    "euf_invoice", "uf_item", "goods_item"
                ).order_by("id"),
            ),
            "invoice_links",
            "purchase_orders",
            "status_logs__created_by",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        can_manage_request_items = (
            not _is_zahtev_only_user(self.request.user)
            or (
                self.object.created_by_id == self.request.user.id
                and self.object.status == ProcurementCase.Status.DRAFT
            )
        )
        ctx.update(
            {
                "title": str(self.object),
                "source_unlinked_items_count": self.object.items.filter(source_type="").count(),
                "can_link_sources": user_has_role_permission(self.request.user, "nabavka:euf_invoice_list"),
                "can_add_items": user_has_role_permission(self.request.user, "nabavka:item_create") and can_manage_request_items,
                "can_delete_items": user_has_role_permission(self.request.user, "nabavka:item_delete") and can_manage_request_items,
                "can_change_status": user_has_role_permission(self.request.user, "nabavka:status_log_create"),
                "can_repeat": user_has_role_permission(self.request.user, "nabavka:case_repeat"),
                "can_update": user_has_role_permission(self.request.user, "nabavka:case_update"),
                "can_create_purchase_order": user_has_role_permission(self.request.user, "nabavka:purchase_order_create"),
                "can_view_euf": user_has_role_permission(self.request.user, "nabavka:euf_invoice_list"),
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
        if (
            _is_zahtev_only_user(request.user)
            and (
                self.procurement_case.created_by_id != request.user.id
                or self.procurement_case.status != ProcurementCase.Status.DRAFT
            )
        ):
            raise PermissionDenied("Stavke mozete menjati samo na svom zahtevu u statusu Nacrt.")
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


class ProcurementItemSourceDataView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:euf_invoice_list"

    def get(self, request):
        source_type = request.GET.get("source_type", "")
        query = (request.GET.get("q") or "").strip()
        limit = 30
        try:
            page = max(int(request.GET.get("page", 1)), 1)
        except (TypeError, ValueError):
            page = 1
        offset = (page - 1) * limit

        def paginate(queryset):
            items = list(queryset[offset : offset + limit + 1])
            return items[:limit], len(items) > limit

        if source_type == ProcurementItem.SOURCE_EUF:
            queryset = ProcurementInvoice.objects.all()
            if query:
                queryset = queryset.filter(
                    Q(invoice_number__icontains=query) | Q(supplier_name__icontains=query)
                )
            items, has_more = paginate(queryset.order_by("-invoice_date", "-id"))
            results = [
                {
                    "id": item.pk,
                    "text": f"{item.invoice_number} - {item.supplier_name or '/'} - {item.amount or '/'}",
                }
                for item in items
            ]
        elif source_type == ProcurementItem.SOURCE_UF:
            queryset = EufItemSnapshot.objects.all()
            if query:
                queryset = queryset.filter(
                    Q(invoice_number__icontains=query)
                    | Q(partner_name__icontains=query)
                    | Q(item_name__icontains=query)
                )
            items, has_more = paginate(queryset.order_by("-document_date", "-id"))
            results = [
                {
                    "id": item.pk,
                    "text": f"{item.invoice_number or item.purchase_invoice_id or '/'} - {item.partner_name or '/'} - {item.item_name or '/'}",
                    "name": item.item_name or "",
                    "uom": item.uom or "",
                    "quantity": str(item.quantity or ""),
                    "price": str(item.price or ""),
                }
                for item in items
            ]
        elif source_type == ProcurementItem.SOURCE_GOODS:
            queryset = GoodsSnapshot.objects.all()
            if query:
                queryset = queryset.filter(
                    Q(article_code__icontains=query)
                    | Q(article_name__icontains=query)
                    | Q(partner_name__icontains=query)
                )
            items, has_more = paginate(queryset.order_by("-document_date", "-id"))
            results = [
                {
                    "id": item.pk,
                    "text": f"{item.article_code or '/'} - {item.article_name or '/'} - {item.partner_name or '/'}",
                    "name": item.article_name or "",
                    "quantity": str(item.quantity or ""),
                    "price": str(item.price or ""),
                }
                for item in items
            ]
        else:
            results = []
            has_more = False
        return JsonResponse({"results": results, "pagination": {"more": has_more}})


class ProcurementItemSourceLinkView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:euf_invoice_list"

    def post(self, request, case_pk, item_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        procurement_item = get_object_or_404(
            ProcurementItem,
            pk=item_pk,
            procurement_case=procurement_case,
        )
        form = ProcurementItemSourceLinkForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Veza nije sacuvana. Proverite izbor tipa i zapisa.")
            return redirect("nabavka:case_detail", pk=procurement_case.pk)

        procurement_item.source_type = form.cleaned_data["source_type"]
        procurement_item.euf_invoice = None
        procurement_item.uf_item = None
        procurement_item.goods_item = None
        source_field = form.cleaned_data.get("source_field")
        if source_field:
            setattr(procurement_item, source_field, form.cleaned_data["source_object"])
        procurement_item.full_clean()
        procurement_item.save(
            update_fields=["source_type", "euf_invoice", "uf_item", "goods_item"]
        )
        messages.success(
            request,
            "Veza stavke je sacuvana." if procurement_item.source_type else "Veza stavke je uklonjena.",
        )
        return redirect("nabavka:case_detail", pk=procurement_case.pk)


class ProcurementCaseSourceLinkView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:euf_invoice_list"

    def post(self, request, case_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        form = ProcurementItemSourceLinkForm(request.POST)
        if not form.is_valid() or not form.cleaned_data.get("source_type"):
            messages.error(request, "Veza nije sacuvana. Izaberite tip i zapis.")
            return redirect("nabavka:case_detail", pk=procurement_case.pk)

        source_field = form.cleaned_data["source_field"]
        source_object = form.cleaned_data["source_object"]
        values = {
            "source_type": form.cleaned_data["source_type"],
            "euf_invoice": None,
            "uf_item": None,
            "goods_item": None,
            source_field: source_object,
        }
        updated = ProcurementItem.objects.filter(
            procurement_case=procurement_case,
            source_type="",
        ).update(**values)
        if updated:
            messages.success(request, f"Povezano je {updated} nepovezanih stavki.")
        else:
            messages.warning(request, "Nema nepovezanih stavki.")
        return redirect("nabavka:case_detail", pk=procurement_case.pk)


class ProcurementItemDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, case_pk, item_pk):
        procurement_case = get_object_or_404(ProcurementCase, pk=case_pk)
        if (
            _is_zahtev_only_user(request.user)
            and (
                procurement_case.created_by_id != request.user.id
                or procurement_case.status != ProcurementCase.Status.DRAFT
            )
        ):
            raise PermissionDenied("Stavke mozete menjati samo na svom zahtevu u statusu Nacrt.")
        get_object_or_404(ProcurementItem, pk=item_pk, procurement_case=procurement_case).delete()
        messages.success(request, "Stavka je obrisana.")
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
