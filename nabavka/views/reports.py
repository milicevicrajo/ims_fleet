from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin

from ..models import ProcurementCase, ProcurementInvoiceLink, PurchaseOrder
from .cases import NabavkaContextMixin


class ReportsView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/reports.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": "Izveštaji nabavke",
                "by_status": ProcurementCase.objects.values("status").annotate(count=Count("id")).order_by("status"),
                "by_type": ProcurementCase.objects.values("case_type").annotate(count=Count("id")).order_by("case_type"),
                "invoice_total": ProcurementInvoiceLink.objects.aggregate(total=Sum("amount"))["total"],
                "order_total": PurchaseOrder.objects.aggregate(total=Sum("amount"))["total"],
            }
        )
        return ctx
