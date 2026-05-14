from django.contrib import messages
from django.http import Http404, JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.html import escape
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin, role_permission_required

from .filters import ContractFilter
from .forms import AnnexForm, ContractForm, ContractPartyFormSet, ContractTypeForm, PartnerForm
from .models import Contract, ContractParty, ContractType, Partner
from .services import count_finance_partners, sync_finance_partner_batch, sync_finance_partners


# ---------------------------------------------------------------------------
# Partner views
# ---------------------------------------------------------------------------

class PartnerListView(RolePermissionRequiredMixin, ListView):
    model = Partner
    template_name = "ugovori/partner_list.html"
    context_object_name = "partneri"

    def get_queryset(self):
        qs = Partner.objects.all()
        q = self.request.GET.get("q", "").strip()
        if q:
            partner_query = (
                Q(name__icontains=q)
                | Q(pib__icontains=q)
                | Q(maticni_broj__icontains=q)
                | Q(jmbg__icontains=q)
            )
            if q.isdigit():
                partner_query |= Q(external_sif_par=int(q))
            qs = qs.filter(partner_query)
        active = self.request.GET.get("active", "")
        if active == "1":
            qs = qs.filter(is_active=True)
        elif active == "0":
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Partneri"
        ctx["q"] = self.request.GET.get("q", "")
        ctx["active_filter"] = self.request.GET.get("active", "")
        ctx["current_app"] = "ugovori"
        return ctx


def _partner_filtered_qs(request):
    qs = Partner.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        partner_query = (
            Q(name__icontains=q)
            | Q(pib__icontains=q)
            | Q(maticni_broj__icontains=q)
            | Q(jmbg__icontains=q)
        )
        if q.isdigit():
            partner_query |= Q(external_sif_par=int(q))
        qs = qs.filter(partner_query)

    active = request.GET.get("active", "")
    if active == "1":
        qs = qs.filter(is_active=True)
    elif active == "0":
        qs = qs.filter(is_active=False)
    return qs


def _partner_badge_html(partner):
    if partner.is_active:
        return '<span class="assignment-status open"><i class="mdi mdi-check-circle"></i> Aktivan</span>'
    return '<span class="assignment-status closed"><i class="mdi mdi-close-circle"></i> Neaktivan</span>'


def _partner_type_html(partner):
    if partner.partner_type == Partner.LEGAL_ENTITY:
        icon = "mdi-domain"
        css_class = "legal"
    else:
        icon = "mdi-account"
        css_class = "person"
    return (
        f'<span class="partner-chip {css_class}"><i class="mdi {icon}"></i> '
        f'{escape(partner.get_partner_type_display())}</span>'
    )


def _partner_residency_html(partner):
    if partner.residency == Partner.DOMESTIC:
        icon = "mdi-map-marker-check"
        css_class = "domestic"
    else:
        icon = "mdi-earth"
        css_class = "foreign"
    return (
        f'<span class="partner-chip {css_class}"><i class="mdi {icon}"></i> '
        f'{escape(partner.get_residency_display())}</span>'
    )


@role_permission_required("ugovori:partner_list")
def partner_datatable_data(request):
    qs = _partner_filtered_qs(request)
    records_total = qs.count()

    search_value = request.GET.get("search[value]", "").strip()
    if search_value:
        search_q = (
            Q(name__icontains=search_value)
            | Q(pib__icontains=search_value)
            | Q(maticni_broj__icontains=search_value)
            | Q(jmbg__icontains=search_value)
            | Q(city__icontains=search_value)
            | Q(phone__icontains=search_value)
        )
        if search_value.isdigit():
            search_q |= Q(external_sif_par=int(search_value))
        qs = qs.filter(search_q)

    records_filtered = qs.count()

    order_map = {
        "0": "external_sif_par",
        "1": "name",
        "2": "is_active",
        "3": "partner_type",
        "4": "residency",
        "5": "pib",
        "6": "maticni_broj",
        "7": "city",
        "8": "phone",
    }
    order_column = request.GET.get("order[0][column]", "1")
    order_dir = request.GET.get("order[0][dir]", "asc")
    order_field = order_map.get(order_column, "name")
    if order_dir == "desc":
        order_field = f"-{order_field}"
    qs = qs.order_by(order_field, "id")

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

    data = []
    for partner in qs[start:start + length]:
        detail_url = reverse("ugovori:partner_detail", kwargs={"pk": partner.pk})
        update_url = reverse("ugovori:partner_update", kwargs={"pk": partner.pk})
        delete_url = reverse("ugovori:partner_delete", kwargs={"pk": partner.pk})
        data.append({
            "DT_RowClass": "" if partner.is_active else "assignment-closed",
            "external_sif_par": partner.external_sif_par or "",
            "name": (
                f'<a href="{detail_url}" class="btn btn-sm btn-outline-primary">'
                f'<i class="mdi mdi-eye"></i> {escape(partner.name)}</a>'
            ),
            "status": _partner_badge_html(partner),
            "partner_type": _partner_type_html(partner),
            "residency": _partner_residency_html(partner),
            "pib": escape(partner.pib or "/"),
            "identification": escape(partner.maticni_broj or partner.jmbg or "/"),
            "city": escape(partner.city or "/"),
            "phone": escape(partner.phone or "/"),
            "actions": (
                f'<a class="btn btn-outline-primary btn-sm" href="{update_url}">'
                '<i class="mdi mdi-pencil"></i> Izmeni</a> '
                f'<a class="btn btn-outline-danger btn-sm" href="{delete_url}">'
                '<i class="mdi mdi-delete"></i> Obrisi</a>'
            ),
        })

    try:
        draw = int(request.GET.get("draw", 0))
    except (TypeError, ValueError):
        draw = 0

    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data,
    })


class PartnerCreateView(RolePermissionRequiredMixin, CreateView):
    model = Partner
    form_class = PartnerForm
    template_name = "ugovori/partner_form.html"
    success_url = reverse_lazy("ugovori:partner_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Partner je uspešno sačuvan.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi partner"
        ctx["cancel_url"] = reverse_lazy("ugovori:partner_list")
        ctx["current_app"] = "ugovori"
        return ctx


class PartnerUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Partner
    form_class = PartnerForm
    template_name = "ugovori/partner_form.html"

    def get_success_url(self):
        return reverse_lazy("ugovori:partner_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Partner je uspešno ažuriran.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Izmena: {self.object.name}"
        ctx["cancel_url"] = reverse_lazy("ugovori:partner_detail", kwargs={"pk": self.object.pk})
        ctx["current_app"] = "ugovori"
        return ctx


class PartnerDetailView(RolePermissionRequiredMixin, DetailView):
    model = Partner
    template_name = "ugovori/partner_detail.html"
    context_object_name = "partner"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.object.name
        ctx["contracts"] = (
            Contract.objects.filter(parties__partner=self.object, kind=Contract.MAIN)
            .distinct()
            .select_related("contract_type")
            .prefetch_related("annexes", "parties__partner")
        )
        ctx["current_app"] = "ugovori"
        return ctx


class PartnerDeleteView(RolePermissionRequiredMixin, DeleteView):
    model = Partner
    template_name = "ugovori/partner_confirm_delete.html"
    success_url = reverse_lazy("ugovori:partner_list")

    def post(self, request, *args, **kwargs):
        partner = self.get_object()
        if partner.contract_parties.exists():
            messages.error(
                request,
                "Partner ne može biti obrisan jer je vezan za postojeće ugovore. "
                "Deaktivirajte ga umesto brisanja.",
            )
            return redirect("ugovori:partner_detail", pk=partner.pk)
        messages.success(request, "Partner je obrisan.")
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Brisanje partnera: {self.object.name}"
        ctx["current_app"] = "ugovori"
        return ctx


@require_POST
@role_permission_required("ugovori:partner_list")
def sync_finansijski_partneri_view(request):
    try:
        result = sync_finance_partners(commit=True)
    except Exception as exc:
        messages.error(request, f"Sinhronizacija partnera nije uspela: {exc}")
        return redirect("ugovori:partner_list")

    messages.success(
        request,
        (
            "Sinhronizacija partnera zavrsena. "
            f"Ucitanih: {result.loaded}, novo: {result.created}, "
            f"azurirano: {result.updated}, bez izmene: {result.unchanged}, "
            f"preskoceno: {result.skipped}."
        ),
    )
    return redirect("ugovori:partner_list")


@require_POST
@role_permission_required("ugovori:partner_list")
def sync_finansijski_partneri_start(request):
    try:
        total = count_finance_partners()
    except Exception as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=500)
    return JsonResponse({"ok": True, "total": total, "batch_size": 250})


@require_POST
@role_permission_required("ugovori:partner_list")
def sync_finansijski_partneri_batch(request):
    try:
        offset = max(int(request.POST.get("offset", 0)), 0)
    except (TypeError, ValueError):
        offset = 0
    try:
        batch_size = int(request.POST.get("batch_size", 250))
    except (TypeError, ValueError):
        batch_size = 250
    batch_size = min(max(batch_size, 1), 500)

    try:
        result = sync_finance_partner_batch(offset=offset, limit=batch_size, commit=True)
    except Exception as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=500)

    return JsonResponse({
        "ok": True,
        "processed": result.loaded,
        "created": result.created,
        "updated": result.updated,
        "unchanged": result.unchanged,
        "skipped": result.skipped,
    })


# ---------------------------------------------------------------------------
# ContractType views
# ---------------------------------------------------------------------------

class ContractTypeListView(RolePermissionRequiredMixin, ListView):
    model = ContractType
    template_name = "ugovori/contract_type_list.html"
    context_object_name = "tipovi"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Tipovi ugovora"
        ctx["current_app"] = "ugovori"
        return ctx


class ContractTypeCreateView(RolePermissionRequiredMixin, CreateView):
    model = ContractType
    form_class = ContractTypeForm
    template_name = "ugovori/contract_type_form.html"
    success_url = reverse_lazy("ugovori:contract_type_list")

    def form_valid(self, form):
        messages.success(self.request, "Tip ugovora je uspešno sačuvan.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi tip ugovora"
        ctx["cancel_url"] = reverse_lazy("ugovori:contract_type_list")
        ctx["current_app"] = "ugovori"
        return ctx


class ContractTypeUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = ContractType
    form_class = ContractTypeForm
    template_name = "ugovori/contract_type_form.html"
    success_url = reverse_lazy("ugovori:contract_type_list")

    def form_valid(self, form):
        messages.success(self.request, "Tip ugovora je uspešno ažuriran.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Izmena: {self.object.name}"
        ctx["cancel_url"] = reverse_lazy("ugovori:contract_type_list")
        ctx["current_app"] = "ugovori"
        return ctx


class ContractTypeDeleteView(RolePermissionRequiredMixin, DeleteView):
    model = ContractType
    template_name = "ugovori/contract_type_confirm_delete.html"
    success_url = reverse_lazy("ugovori:contract_type_list")

    def post(self, request, *args, **kwargs):
        tip = self.get_object()
        if tip.contracts.exists():
            messages.error(
                request,
                "Tip ugovora ne može biti obrisan jer postoje ugovori tog tipa.",
            )
            return redirect("ugovori:contract_type_list")
        messages.success(request, "Tip ugovora je obrisan.")
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Brisanje tipa: {self.object.name}"
        ctx["current_app"] = "ugovori"
        return ctx


# ---------------------------------------------------------------------------
# Contract views
# ---------------------------------------------------------------------------

class ContractListView(RolePermissionRequiredMixin, FilterView):
    model = Contract
    template_name = "ugovori/contract_list.html"
    context_object_name = "ugovori"
    filterset_class = ContractFilter

    def get_queryset(self):
        return (
            Contract.objects.all()
            .select_related("contract_type", "parent_contract")
            .prefetch_related("parties__partner")
            .distinct()
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Ugovori"
        ctx["current_app"] = "ugovori"
        return ctx


class _ContractFormMixin:
    """Shared logic for ContractCreateView and ContractUpdateView."""

    def get_formset(self, **formset_kwargs):
        if self.request.method == "POST":
            return ContractPartyFormSet(
                self.request.POST,
                instance=getattr(self, "object", None),
                **formset_kwargs,
            )
        return ContractPartyFormSet(
            instance=getattr(self, "object", None),
            **formset_kwargs,
        )

    def form_valid(self, form):
        formset = self.get_formset()
        if not formset.is_valid():
            return self.form_invalid_with_formset(form, formset)
        self.object = form.save(commit=False)
        if not self.object.pk:
            self.object.created_by = self.request.user
        self.object.save()
        formset.instance = self.object
        formset.save()
        messages.success(self.request, "Ugovor je uspešno sačuvan.")
        return redirect(self.get_success_url())

    def form_invalid_with_formset(self, form, formset):
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = self.get_formset()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid_with_formset(form, formset)


class ContractCreateView(_ContractFormMixin, RolePermissionRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = "ugovori/contract_form.html"

    def get_success_url(self):
        return reverse_lazy("ugovori:contract_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi ugovor"
        ctx["cancel_url"] = reverse_lazy("ugovori:contract_list")
        ctx["current_app"] = "ugovori"
        if "formset" not in ctx:
            ctx["formset"] = self.get_formset()
        return ctx


class ContractUpdateView(_ContractFormMixin, RolePermissionRequiredMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = "ugovori/contract_form.html"

    def get_success_url(self):
        return reverse_lazy("ugovori:contract_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Izmena: {self.object.contract_number}"
        ctx["cancel_url"] = reverse_lazy(
            "ugovori:contract_detail", kwargs={"pk": self.object.pk}
        )
        ctx["current_app"] = "ugovori"
        if "formset" not in ctx:
            ctx["formset"] = self.get_formset()
        return ctx


class ContractDetailView(RolePermissionRequiredMixin, DetailView):
    model = Contract
    template_name = "ugovori/contract_detail.html"
    context_object_name = "ugovor"

    def get_queryset(self):
        return (
            Contract.objects.select_related("contract_type", "parent_contract", "created_by")
            .prefetch_related("parties__partner", "annexes__contract_type", "annexes__parties__partner")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = str(self.object)
        ctx["annexes"] = self.object.annexes.all().select_related("contract_type").prefetch_related("parties__partner")
        ctx["current_app"] = "ugovori"
        return ctx


class ContractDeleteView(RolePermissionRequiredMixin, DeleteView):
    model = Contract
    template_name = "ugovori/contract_confirm_delete.html"
    success_url = reverse_lazy("ugovori:contract_list")

    def post(self, request, *args, **kwargs):
        contract = self.get_object()
        if contract.annexes.exists():
            messages.error(
                request,
                "Ugovor ne može biti obrisan jer ima anekse. Prvo obrišite anekse.",
            )
            return redirect("ugovori:contract_detail", pk=contract.pk)
        messages.success(request, "Ugovor je obrisan.")
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Brisanje: {self.object.contract_number}"
        ctx["current_app"] = "ugovori"
        return ctx


class AnnexCreateView(RolePermissionRequiredMixin, CreateView):
    model = Contract
    template_name = "ugovori/contract_form.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.parent_contract = get_object_or_404(
            Contract, pk=kwargs["parent_pk"], kind=Contract.MAIN
        )

    def get_form_class(self):
        return AnnexForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["parent_contract"] = self.parent_contract
        return kwargs

    def get_formset(self):
        if self.request.method == "POST":
            return ContractPartyFormSet(self.request.POST, instance=None)
        return ContractPartyFormSet(instance=None)

    def form_valid(self, form):
        formset = self.get_formset()
        if not formset.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, formset=formset)
            )
        self.object = form.save(commit=False)
        self.object.kind = Contract.ANNEX
        self.object.parent_contract = self.parent_contract
        self.object.created_by = self.request.user
        self.object.save()
        formset.instance = self.object
        formset.save()
        messages.success(self.request, "Aneks je uspešno sačuvan.")
        return redirect("ugovori:contract_detail", pk=self.object.pk)

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = self.get_formset()
        if form.is_valid():
            return self.form_valid(form)
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Novi aneks za: {self.parent_contract.contract_number}"
        ctx["parent_contract"] = self.parent_contract
        ctx["cancel_url"] = reverse_lazy(
            "ugovori:contract_detail", kwargs={"pk": self.parent_contract.pk}
        )
        ctx["current_app"] = "ugovori"
        if "formset" not in ctx:
            ctx["formset"] = self.get_formset()
        return ctx

    def get_success_url(self):
        return reverse_lazy("ugovori:contract_detail", kwargs={"pk": self.object.pk})
