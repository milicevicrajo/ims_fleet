from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin, user_has_role_permission

from ..filters import PublicProcurementPlanItemFilter
from ..forms import PublicProcurementPlanImportForm
from ..models import PublicProcurementPlanItem, PublicProcurementPlanVersion
from ..services.public_procurements import import_public_procurement_plan
from .cases import NabavkaContextMixin


class PublicProcurementPlanListView(
    NabavkaContextMixin,
    RolePermissionRequiredMixin,
    LoginRequiredMixin,
    ListView,
):
    model = PublicProcurementPlanVersion
    template_name = "nabavka/public_procurement_plan_version_list.html"
    context_object_name = "versions"
    paginate_by = 50

    def get_queryset(self):
        queryset = PublicProcurementPlanVersion.objects.all().order_by("-year", "-version_number")
        year = (self.request.GET.get("year") or "").strip()
        if year:
            queryset = queryset.filter(year=year)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            queryset = queryset.filter(source_filename__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        years = (
            PublicProcurementPlanVersion.objects.order_by("-year")
            .values_list("year", flat=True)
            .distinct()
        )
        ctx.update(
            {
                "title": "Javne nabavke",
                "years": years,
                "import_form": PublicProcurementPlanImportForm(),
                "can_import": user_has_role_permission(
                    self.request.user,
                    "nabavka:public_procurement_import",
                ),
            }
        )
        return ctx


class PublicProcurementPlanDetailView(
    NabavkaContextMixin,
    RolePermissionRequiredMixin,
    LoginRequiredMixin,
    FilterView,
):
    model = PublicProcurementPlanItem
    template_name = "nabavka/public_procurement_plan_detail.html"
    context_object_name = "items"
    filterset_class = PublicProcurementPlanItemFilter
    paginate_by = 100
    required_permission_code = "nabavka:public_procurement_list"

    def dispatch(self, request, *args, **kwargs):
        self.version = get_object_or_404(PublicProcurementPlanVersion, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            PublicProcurementPlanItem.objects.filter(version=self.version)
            .select_related("version", "previous_item")
            .order_by("plan_type", "source_sheet", "item_number", "id")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": f"Javne nabavke {self.version.year} / v{self.version.version_number}",
                "selected_version": self.version,
            }
        )
        return ctx


class PublicProcurementPlanImportView(
    NabavkaContextMixin,
    RolePermissionRequiredMixin,
    LoginRequiredMixin,
    View,
):
    required_permission_code = "nabavka:public_procurement_import"

    def post(self, request, *args, **kwargs):
        form = PublicProcurementPlanImportForm(request.POST, request.FILES)
        if not form.is_valid():
            for error in form.errors.values():
                messages.error(request, " ".join(error))
            return redirect("nabavka:public_procurement_list")
        try:
            result = import_public_procurement_plan(
                excel_file=form.cleaned_data["excel_file"],
                year=form.cleaned_data["year"],
                imported_by=request.user,
                note=form.cleaned_data.get("note") or "",
            )
        except Exception as exc:
            messages.error(request, f"Plan javnih nabavki nije uvezen: {exc}")
            return redirect("nabavka:public_procurement_list")

        version = result["version"]
        messages.success(
            request,
            (
                f"Uvezena je verzija {version.version_number} za {version.year}. "
                f"Dodato: {version.added_count}, izmenjeno: {version.changed_count}, "
                f"bez izmene: {version.unchanged_count}, uklonjeno: {version.removed_count}."
            ),
        )
        if result["skipped_sheets"]:
            messages.warning(
                request,
                "Preskoceni sheetovi bez prepoznatog zaglavlja: "
                + ", ".join(result["skipped_sheets"]),
            )
        if result["duplicate_keys"]:
            messages.warning(
                request,
                "Pronadjeni su dupli kljucevi stavki; deo redova je razdvojen po Excel redu.",
            )
        return redirect("nabavka:public_procurement_detail", pk=version.pk)
