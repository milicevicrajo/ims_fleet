from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin

from ..models import ProcurementCase
from .cases import NabavkaContextMixin


class AlertsView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/alerts.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": "Alarmi nabavke",
                "waiting_invoice_cases": ProcurementCase.objects.filter(
                    status=ProcurementCase.Status.WAITING_INVOICE
                ).select_related("supplier", "responsible", "job_code"),
            }
        )
        return ctx
