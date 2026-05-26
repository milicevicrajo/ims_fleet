from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin

from ..filters import ProcurementInvoiceLinkFilter
from ..forms import EufInvoiceLinkForm
from ..models import ProcurementCase, ProcurementInvoiceLink
from ..services.euf import get_euf_invoice, list_euf_invoices
from .cases import NabavkaContextMixin


class EufInvoiceListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/euf_invoice_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        invoices = list_euf_invoices(q=q, limit=500)
        linked_keys = set(
            ProcurementInvoiceLink.objects.filter(
                source=ProcurementInvoiceLink.SOURCE_EUF,
                euf_key__in=[invoice.euf_key for invoice in invoices],
            ).values_list("euf_key", flat=True)
        )
        ctx.update(
            {
                "title": "Preuzete EUF fakture",
                "invoices": invoices,
                "q": q,
                "linked_keys": linked_keys,
            }
        )
        return ctx


class EufInvoiceLinkView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/euf_invoice_link.html"

    def dispatch(self, request, *args, **kwargs):
        self.invoice = get_euf_invoice(kwargs["euf_key"])
        if self.invoice is None:
            messages.error(request, "EUF faktura nije pronađena.")
            return redirect("nabavka:euf_invoice_list")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = EufInvoiceLinkForm(request.POST)
        if form.is_valid():
            procurement_case = form.cleaned_data["procurement_case"]
            link, created = ProcurementInvoiceLink.objects.get_or_create(
                procurement_case=procurement_case,
                source=ProcurementInvoiceLink.SOURCE_EUF,
                euf_key=self.invoice.euf_key,
                defaults={
                    "invoice_number": self.invoice.broj_fakture,
                    "invoice_date": self.invoice.datum,
                    "supplier_name": self.invoice.naziv_partnera,
                    "amount": self.invoice.iznos,
                    "note": form.cleaned_data.get("note"),
                    "created_by": request.user,
                },
            )
            if created and procurement_case.status == ProcurementCase.Status.WAITING_INVOICE:
                procurement_case.status = ProcurementCase.Status.INVOICE_LINKED
                procurement_case.save(update_fields=["status", "updated_at"])
            messages.success(request, "Faktura je povezana." if created else "Faktura je već povezana sa tim predmetom.")
            return redirect("nabavka:case_detail", pk=procurement_case.pk)
        messages.error(request, "Faktura nije povezana. Proverite izbor predmeta.")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Povezivanje EUF fakture"
        ctx["invoice"] = self.invoice
        ctx["form"] = kwargs.get("form") or EufInvoiceLinkForm()
        return ctx


class ProcurementInvoiceLinkListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, FilterView):
    model = ProcurementInvoiceLink
    template_name = "nabavka/invoice_link_list.html"
    context_object_name = "links"
    filterset_class = ProcurementInvoiceLinkFilter
    paginate_by = 50

    def get_queryset(self):
        return ProcurementInvoiceLink.objects.select_related("procurement_case", "created_by")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Povezane fakture"
        return ctx


class ProcurementInvoiceLinkDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        link = get_object_or_404(ProcurementInvoiceLink, pk=pk)
        case_pk = link.procurement_case_id
        link.delete()
        messages.success(request, "Veza fakture je obrisana.")
        return redirect(request.POST.get("next") or reverse("nabavka:case_detail", kwargs={"pk": case_pk}))
