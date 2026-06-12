from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connections
from django.db.models import Count, Sum
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin

from ..models import ProcurementCase, ProcurementInvoice, PurchaseOrder
from .cases import NabavkaContextMixin


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def fetch_partner_job_code_rows(partner_name="", limit=2000):
    partner_name = _clean(partner_name)
    params = []
    where = ""
    if partner_name:
        where = "WHERE LTRIM(RTRIM(naz_par)) LIKE %s"
        params.append(f"%{partner_name}%")

    sql = f"""
        SELECT TOP ({int(limit)})
            sif_par,
            naz_par,
            sif_pos
        FROM dbo.nbv_sif_pos_par
        {where}
        ORDER BY LTRIM(RTRIM(naz_par)), sif_pos
    """
    with connections["server_db"].cursor() as cursor:
        cursor.execute(sql, params)
        return [
            {
                "partner_code": _clean(row[0]),
                "partner_name": _clean(row[1]),
                "job_code": _clean(row[2]),
            }
            for row in cursor.fetchall()
        ]


class ReportsView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/reports.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": "Izveštaji nabavke",
                "by_status": ProcurementCase.objects.values("status").annotate(count=Count("id")).order_by("status"),
                "by_type": ProcurementCase.objects.values("case_type").annotate(count=Count("id")).order_by("case_type"),
                "invoice_total": ProcurementInvoice.objects.filter(item_links__isnull=False).distinct().aggregate(total=Sum("amount"))["total"],
                "order_total": PurchaseOrder.objects.aggregate(total=Sum("amount"))["total"],
            }
        )
        return ctx


class PartnerJobCodeCheckReportView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    required_permission_code = "nabavka:reports"
    template_name = "nabavka/reports_partner_job_code_check.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        partner_name = (self.request.GET.get("partner") or "").strip()
        rows = fetch_partner_job_code_rows(partner_name=partner_name)
        ctx.update(
            {
                "title": "Provera sifre posla za partnera",
                "partner": partner_name,
                "rows": rows,
                "rows_count": len(rows),
            }
        )
        return ctx
