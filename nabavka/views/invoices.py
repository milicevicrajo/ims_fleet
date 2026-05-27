from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from core.mixins import RolePermissionRequiredMixin

from ..forms import EufInvoiceItemLinkForm, ProcurementInvoiceForm
from ..models import ProcurementCase, ProcurementInvoice, ProcurementItemInvoiceLink
from ..services.euf import sync_euf_invoice_snapshots
from .cases import NabavkaContextMixin


class EufInvoiceListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    template_name = "nabavka/euf_invoice_list.html"
    context_object_name = "invoices"
    paginate_by = 50

    def get_queryset(self):
        q = (self.request.GET.get("q") or "").strip()
        invoices = ProcurementInvoice.objects.filter(source=ProcurementInvoice.SOURCE_EUF)
        if q:
            invoices = invoices.filter(
                Q(invoice_number__icontains=q)
                | Q(supplier_name__icontains=q)
                | Q(center_name__icontains=q)
                | Q(center__icontains=q)
            )
        return invoices.annotate(
            item_links_total=Count("item_links", distinct=True),
            garage_item_links_total=Count(
                "item_links",
                filter=Q(item_links__procurement_item__procurement_case__is_garage=True),
                distinct=True,
            ),
        ).order_by("-invoice_date", "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        ctx.update(
            {
                "title": "EUF fakture",
                "q": q,
            }
        )
        return ctx


class EufInvoiceSyncView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    required_permission_code = "nabavka:euf_invoice_list"

    def post(self, request):
        q = (request.POST.get("q") or "").strip()
        try:
            invoices = sync_euf_invoice_snapshots(q=q, limit=2000)
        except Exception as exc:
            messages.error(request, f"EUF fakture nisu povucene iz view-a: {exc}")
        else:
            messages.success(request, f"EUF fakture su osvezene. Obradjeno zapisa: {len(invoices)}.")
        redirect_url = reverse("nabavka:euf_invoice_list")
        return redirect(f"{redirect_url}?q={q}" if q else redirect_url)


class EufInvoiceDetailView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = ProcurementInvoice
    template_name = "nabavka/euf_invoice_detail.html"
    context_object_name = "invoice"

    def get_queryset(self):
        return ProcurementInvoice.objects.prefetch_related(
            "item_links__procurement_item__procurement_case",
            "item_links__created_by",
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")

        if action == "update_details":
            form = ProcurementInvoiceForm(request.POST, instance=self.object)
            if form.is_valid():
                form.save()
                messages.success(request, "Detalji fakture su sacuvani.")
            else:
                messages.error(request, "Detalji fakture nisu sacuvani. Proverite unete podatke.")
                return self.render_to_response(self.get_context_data(invoice_form=form))

        elif action == "link_item":
            form = EufInvoiceItemLinkForm(request.POST)
            if form.is_valid():
                procurement_item = form.cleaned_data["procurement_item"]
                procurement_case = procurement_item.procurement_case
                link, created = ProcurementItemInvoiceLink.objects.get_or_create(
                    procurement_item=procurement_item,
                    defaults={
                        "invoice": self.object,
                        "note": form.cleaned_data.get("note"),
                        "created_by": request.user,
                    },
                )
                if created and procurement_case.status == ProcurementCase.Status.WAITING_INVOICE:
                    procurement_case.status = ProcurementCase.Status.INVOICE_LINKED
                    procurement_case.save(update_fields=["status", "updated_at"])
                messages.success(
                    request,
                    "Stavka je povezana sa fakturom." if created else "Stavka je vec povezana sa fakturom.",
                )
            else:
                messages.error(request, "Stavka nije povezana. Proverite izbor stavke.")
                return self.render_to_response(self.get_context_data(item_link_form=form))

        return redirect("nabavka:euf_invoice_detail", pk=self.object.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": f"Faktura {self.object.invoice_number}",
                "invoice_form": kwargs.get("invoice_form") or ProcurementInvoiceForm(instance=self.object),
                "item_link_form": kwargs.get("item_link_form") or EufInvoiceItemLinkForm(),
                "item_links": self.object.item_links.select_related(
                    "procurement_item",
                    "procurement_item__procurement_case",
                    "created_by",
                ),
            }
        )
        return ctx


class ProcurementInvoiceLinkDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        link = get_object_or_404(ProcurementItemInvoiceLink, pk=pk)
        invoice_pk = link.invoice_id
        next_url = request.POST.get("next")
        link.delete()
        messages.success(request, "Veza stavke i fakture je obrisana.")
        return redirect(next_url or reverse("nabavka:euf_invoice_detail", kwargs={"pk": invoice_pk}))
