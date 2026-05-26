from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin

from ..filters import PurchaseOrderFilter
from ..forms import PurchaseOrderForm
from ..models import ProcurementCase, PurchaseOrder
from .cases import NabavkaContextMixin


class PurchaseOrderListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, FilterView):
    model = PurchaseOrder
    template_name = "nabavka/purchase_order_list.html"
    context_object_name = "orders"
    filterset_class = PurchaseOrderFilter
    paginate_by = 50

    def get_queryset(self):
        return PurchaseOrder.objects.select_related("procurement_case", "supplier", "contract", "created_by")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Narudžbenice"
        return ctx


class PurchaseOrderCreateView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = "nabavka/purchase_order_form.html"

    def dispatch(self, request, *args, **kwargs):
        case_id = request.GET.get("case") or request.POST.get("procurement_case")
        self.procurement_case = ProcurementCase.objects.filter(pk=case_id).first() if case_id else None
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.procurement_case is not None:
            kwargs["procurement_case"] = self.procurement_case
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Narudžbenica je sačuvana.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("nabavka:purchase_order_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nova narudžbenica"
        ctx["submit_button_label"] = "Sačuvaj"
        return ctx


class PurchaseOrderUpdateView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = "nabavka/purchase_order_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Narudžbenica je ažurirana.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("nabavka:purchase_order_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Izmena narudžbenice: {self.object.order_number}"
        ctx["submit_button_label"] = "Sačuvaj izmene"
        return ctx


class PurchaseOrderDetailView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = "nabavka/purchase_order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return PurchaseOrder.objects.select_related("procurement_case", "supplier", "contract", "created_by")
