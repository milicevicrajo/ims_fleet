from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from core.mixins import RolePermissionRequiredMixin

from ..forms import EufInvoiceItemLinkForm, ProcurementInvoiceContractLinkForm, ProcurementInvoiceForm
from ..models import (
    ProcurementCase,
    ProcurementInvoice,
    ProcurementInvoiceContractLink,
    ProcurementItemInvoiceLink,
)
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
            "contract_links__contract__contract_type",
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

        elif action == "link_contract":
            form = ProcurementInvoiceContractLinkForm(request.POST, invoice=self.object)
            if form.is_valid():
                link = form.save(commit=False)
                link.invoice = self.object
                link.created_by = request.user
                link.save()
                messages.success(request, "Kupovni ugovor je povezan sa fakturom.")
            else:
                messages.error(request, "Ugovor nije povezan. Proverite izbor ugovora.")
                return self.render_to_response(self.get_context_data(contract_link_form=form))

        return redirect("nabavka:euf_invoice_detail", pk=self.object.pk)

    @staticmethod
    def _contract_execution_rows(invoice):
        rows = []
        links = invoice.contract_links.select_related("contract", "contract__contract_type")
        for link in links:
            contract = link.contract
            execution_total = (
                ProcurementInvoiceContractLink.objects.filter(contract=contract)
                .aggregate(total=Sum("invoice__amount"))
                .get("total")
                or 0
            )
            has_fixed_value = contract.value_type == contract.VALUE_TYPE_FIXED and contract.value is not None
            remaining = contract.value - execution_total if has_fixed_value else None
            percent = (execution_total / contract.value * 100) if has_fixed_value and contract.value else None
            rows.append(
                {
                    "link": link,
                    "contract": contract,
                    "execution_total": execution_total,
                    "remaining": remaining,
                    "percent": percent,
                    "has_fixed_value": has_fixed_value,
                }
            )
        return rows

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "title": f"Faktura {self.object.invoice_number}",
                "invoice_form": kwargs.get("invoice_form") or ProcurementInvoiceForm(instance=self.object),
                "item_link_form": kwargs.get("item_link_form") or EufInvoiceItemLinkForm(),
                "contract_link_form": kwargs.get("contract_link_form")
                or ProcurementInvoiceContractLinkForm(invoice=self.object),
                "contract_execution_rows": self._contract_execution_rows(self.object),
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


class ProcurementInvoiceContractLinkDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        link = get_object_or_404(ProcurementInvoiceContractLink, pk=pk)
        invoice_pk = link.invoice_id
        link.delete()
        messages.success(request, "Veza fakture i ugovora je obrisana.")
        return redirect("nabavka:euf_invoice_detail", pk=invoice_pk)
