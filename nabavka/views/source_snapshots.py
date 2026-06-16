from datetime import datetime
from urllib.parse import parse_qsl, urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import CharField, Q
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.utils.html import escape
from django.views import View
from django.views.generic import DetailView, ListView

from core.mixins import RolePermissionRequiredMixin

from ..models import EufItemSnapshot, GoodsSnapshot, ProcurementInvoice, UfInvoiceSnapshot
from ..services.source_snapshots import sync_euf_item_snapshots, sync_goods_snapshots
from .cases import NabavkaContextMixin


def _parse_filter_date(value):
    parsed = parse_date(value or "")
    if parsed:
        return parsed
    try:
        return datetime.strptime(value or "", "%d.%m.%Y").date()
    except ValueError:
        return None


def _filter_context(request):
    date_from = _parse_filter_date(request.GET.get("date_from"))
    date_to = _parse_filter_date(request.GET.get("date_to"))
    return {
        "q": (request.GET.get("source_search") or "").strip(),
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
        "partner": (request.GET.get("partner") or "").strip(),
    }


def _redirect_to_list(request, view_name):
    query_string = urlencode(parse_qsl(request.POST.get("next_query") or "", keep_blank_values=False))
    redirect_url = reverse(view_name)
    return redirect(f"{redirect_url}?{query_string}" if query_string else redirect_url)


def _hover_text(value, max_length=50):
    text = str(value or "")
    visible = f"{text[:max_length]}..." if len(text) > max_length else text
    return f'<span title="{escape(text)}">{escape(visible)}</span>'


def _normalize_match_value(value):
    return " ".join(str(value or "").split()).casefold()


def _datatable_page(request, queryset, order_map):
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
    order_field = order_map.get(request.GET.get("order[0][column]", "0"), next(iter(order_map.values())))
    if request.GET.get("order[0][dir]", "desc") == "desc":
        order_field = f"-{order_field}"
    return queryset.order_by(order_field, "-id")[start:start + length]


def _datatable_response(request, records_total, records_filtered, rows):
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


def _filter_uf_invoices(request):
    q = (request.GET.get("source_search") or "").strip()
    partner = (request.GET.get("partner") or "").strip()
    account = (request.GET.get("account") or "").strip()
    date_from = _parse_filter_date(request.GET.get("date_from"))
    date_to = _parse_filter_date(request.GET.get("date_to"))
    invoices = UfInvoiceSnapshot.objects.all()
    if q:
        invoices = invoices.filter(
            Q(invoice_number__icontains=q)
            | Q(partner_name__icontains=q)
            | Q(partner_pib__icontains=q)
            | Q(accounts__icontains=q)
        )
    if partner:
        invoices = invoices.filter(partner_name__icontains=partner)
    if account:
        invoices = invoices.filter(accounts__icontains=account)
    if date_from:
        invoices = invoices.filter(document_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(document_date__lte=date_to)
    return invoices


class EufItemSnapshotListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    required_permission_code = "nabavka:euf_invoice_list"
    model = UfInvoiceSnapshot
    template_name = "nabavka/euf_item_list.html"
    context_object_name = "invoices"

    def get_queryset(self):
        return UfInvoiceSnapshot.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_filter_context(self.request))
        ctx.update(
            {
                "title": "UF fakture",
                "account": (self.request.GET.get("account") or "").strip(),
            }
        )
        return ctx


class EufItemSnapshotDataView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:euf_invoice_list"

    def get(self, request):
        invoices = _filter_uf_invoices(request)
        search_value = request.GET.get("search[value]", "").strip()
        if search_value:
            invoices = invoices.filter(
                Q(invoice_number__icontains=search_value)
                | Q(partner_name__icontains=search_value)
                | Q(partner_pib__icontains=search_value)
                | Q(accounts__icontains=search_value)
            )
        records_total = UfInvoiceSnapshot.objects.count()
        records_filtered = invoices.count()
        page = _datatable_page(
            request,
            invoices,
            {
                "0": "document_date",
                "1": "invoice_number",
                "2": "partner_name",
                "3": "partner_pib",
                "4": "payment_amount",
                "5": "item_value_total",
                "6": "item_count",
                "7": "accounts",
            },
        )
        rows = [
            {
                "actions": (
                    f'<a class="btn btn-outline-primary btn-sm" href="'
                    f'{reverse("nabavka:uf_invoice_detail", kwargs={"pk": item.pk})}">'
                    '<i class="mdi mdi-eye"></i> Detalj</a>'
                ),
                "document_date": item.document_date.strftime("%d.%m.%Y") if item.document_date else "",
                "invoice_number": escape(item.invoice_number or item.purchase_invoice_id or ""),
                "partner_name": _hover_text(item.partner_name),
                "partner_pib": escape(item.partner_pib or ""),
                "payment_amount": str(item.payment_amount or item.total or ""),
                "item_value_total": str(item.item_value_total or ""),
                "item_count": item.item_count,
                "accounts": escape(item.accounts or ""),
            }
            for item in page
        ]
        return _datatable_response(request, records_total, records_filtered, rows)


class UfInvoiceSnapshotDetailView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    required_permission_code = "nabavka:euf_invoice_list"
    model = UfInvoiceSnapshot
    template_name = "nabavka/uf_invoice_detail.html"
    context_object_name = "invoice"

    def get_queryset(self):
        return UfInvoiceSnapshot.objects.prefetch_related(
            "items",
            "procurement_items__procurement_case",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": f"UF faktura {self.object.invoice_number or self.object.purchase_invoice_id or self.object.pk}",
                "items": self.object.items.all().order_by("id"),
                "linked_items": self.object.procurement_items.select_related("procurement_case").order_by(
                    "procurement_case__case_number",
                    "id",
                ),
            }
        )
        return ctx


class EufItemSnapshotSyncView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:euf_invoice_list"

    def post(self, request):
        q = (request.POST.get("source_search") or "").strip()
        try:
            snapshots = sync_euf_item_snapshots(q=q)
        except Exception as exc:
            messages.error(request, f"UF stavke nisu preuzete iz view-a: {exc}")
        else:
            messages.success(request, f"UF stavke su osvezene. Obradjeno zapisa: {len(snapshots)}.")
        return _redirect_to_list(request, "nabavka:euf_item_list")


def _filter_goods(request):
    q = (request.GET.get("source_search") or "").strip()
    partner = (request.GET.get("partner") or "").strip()
    organizational_unit = (request.GET.get("organizational_unit") or "").strip()
    article_type = (request.GET.get("article_type") or "").strip()
    date_from = _parse_filter_date(request.GET.get("date_from"))
    date_to = _parse_filter_date(request.GET.get("date_to"))
    goods = GoodsSnapshot.objects.annotate(
        document_number_text=Cast("document_number", output_field=CharField()),
    )
    if q:
        goods = goods.filter(
            Q(document_number_text__icontains=q)
            | Q(partner_name__icontains=q)
            | Q(article_code__icontains=q)
            | Q(article_name__icontains=q)
            | Q(linked_document__icontains=q)
        )
    if partner:
        goods = goods.filter(partner_name__icontains=partner)
    if organizational_unit:
        goods = goods.filter(organizational_unit=organizational_unit)
    if article_type:
        goods = goods.filter(article_type__icontains=article_type)
    if date_from:
        goods = goods.filter(document_date__gte=date_from)
    if date_to:
        goods = goods.filter(document_date__lte=date_to)
    return goods


def _goods_invoice_match_badges(goods_items):
    match_keys = {
        item.pk: (
            _normalize_match_value(item.linked_document),
            _normalize_match_value(item.partner_name),
        )
        for item in goods_items
        if _normalize_match_value(item.linked_document) and _normalize_match_value(item.partner_name)
    }
    linked_documents = {
        (item.linked_document or "").strip()
        for item in goods_items
        if item.pk in match_keys
    }
    if not linked_documents:
        return {}

    matches = {item_id: {"uf": [], "euf": []} for item_id in match_keys}
    uf_invoices = UfInvoiceSnapshot.objects.filter(
        Q(invoice_number__in=linked_documents) | Q(purchase_invoice_id__in=linked_documents)
    ).values("id", "invoice_number", "purchase_invoice_id", "partner_name")
    for invoice in uf_invoices:
        invoice_partner = _normalize_match_value(invoice["partner_name"])
        for invoice_document in {invoice["invoice_number"], invoice["purchase_invoice_id"]}:
            invoice_document = _normalize_match_value(invoice_document)
            for item_id, (linked_document, partner_name) in match_keys.items():
                if invoice_document != linked_document or invoice_partner != partner_name:
                    continue
                url = reverse("nabavka:uf_invoice_detail", kwargs={"pk": invoice["id"]})
                matches[item_id]["uf"].append(
                    f'<a class="goods-source-badge uf" href="{url}" '
                    'title="Potvrdjeno brojem fakture i partnerom">UF</a>'
                )

    euf_invoices = ProcurementInvoice.objects.filter(
        source=ProcurementInvoice.SOURCE_EUF,
        invoice_number__in=linked_documents,
    ).values("id", "invoice_number", "supplier_name")
    for invoice in euf_invoices:
        invoice_document = _normalize_match_value(invoice["invoice_number"])
        invoice_partner = _normalize_match_value(invoice["supplier_name"])
        for item_id, (linked_document, partner_name) in match_keys.items():
            if invoice_document != linked_document or invoice_partner != partner_name:
                continue
            url = reverse("nabavka:euf_invoice_detail", kwargs={"pk": invoice["id"]})
            matches[item_id]["euf"].append(
                f'<a class="goods-source-badge euf" href="{url}" '
                'title="Potvrdjeno brojem fakture i partnerom">EUF</a>'
            )

    badges_by_item = {}
    for item_id, source_matches in matches.items():
        uf_badges = list(dict.fromkeys(source_matches["uf"]))
        euf_badges = list(dict.fromkeys(source_matches["euf"]))
        if bool(uf_badges) == bool(euf_badges):
            continue
        source_badges = uf_badges or euf_badges
        if len(source_badges) == 1:
            badges_by_item[item_id] = source_badges[0]
    return badges_by_item


class GoodsSnapshotListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    required_permission_code = "nabavka:euf_invoice_list"
    model = GoodsSnapshot
    template_name = "nabavka/goods_list.html"
    context_object_name = "goods"

    def get_queryset(self):
        return GoodsSnapshot.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_filter_context(self.request))
        ctx.update(
            {
                "title": "Roba",
                "organizational_unit": (self.request.GET.get("organizational_unit") or "").strip(),
                "article_type": (self.request.GET.get("article_type") or "").strip(),
            }
        )
        return ctx


class GoodsSnapshotDataView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:euf_invoice_list"

    def get(self, request):
        goods = _filter_goods(request)
        search_value = request.GET.get("search[value]", "").strip()
        if search_value:
            goods = goods.filter(
                Q(document_number_text__icontains=search_value)
                | Q(partner_name__icontains=search_value)
                | Q(linked_document__icontains=search_value)
                | Q(article_code__icontains=search_value)
                | Q(article_name__icontains=search_value)
                | Q(article_type__icontains=search_value)
            )
        records_total = GoodsSnapshot.objects.count()
        records_filtered = goods.count()
        page = _datatable_page(
            request,
            goods,
            {
                "0": "document_date",
                "1": "document_number",
                "2": "document_type",
                "3": "organizational_unit",
                "4": "partner_name",
                "5": "linked_document",
                "6": "article_code",
                "7": "article_name",
                "8": "article_type",
                "9": "quantity",
                "10": "price",
            },
        )
        page_items = list(page)
        match_badges = _goods_invoice_match_badges(page_items)
        rows = []
        for item in page_items:
            linked_document = (item.linked_document or "").strip()
            badges = match_badges.get(item.pk, "")
            rows.append(
                {
                "document_date": item.document_date.strftime("%d.%m.%Y") if item.document_date else "",
                "document": f"{escape(item.year or '')}/{item.document_number or ''}",
                "document_type": escape(item.document_type or ""),
                "organizational_unit": item.organizational_unit or "",
                "partner_name": _hover_text(item.partner_name),
                "linked_document": (
                    f'{escape(linked_document)} <span class="goods-source-badges">{badges}</span>'
                    if badges
                    else escape(linked_document)
                ),
                "article_code": escape(item.article_code or ""),
                "article_name": _hover_text(item.article_name, 45),
                "article_type": escape(item.article_type or ""),
                "quantity": str(item.quantity) if item.quantity is not None else "",
                "price": str(item.price) if item.price is not None else "",
                "DT_RowClass": "goods-has-invoice-match" if badges else "",
                }
            )
        return _datatable_response(request, records_total, records_filtered, rows)


class GoodsSnapshotSyncView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:euf_invoice_list"

    def post(self, request):
        q = (request.POST.get("source_search") or "").strip()
        try:
            snapshots = sync_goods_snapshots(q=q)
        except Exception as exc:
            messages.error(request, f"Roba nije preuzeta iz view-a: {exc}")
        else:
            messages.success(request, f"Roba je osvezena. Obradjeno zapisa: {len(snapshots)}.")
        return _redirect_to_list(request, "nabavka:goods_list")
