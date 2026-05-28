from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Prefetch, Sum
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin
from ugovori.models import Contract, ContractParty

from ..filters import PurchaseContractFilter
from .cases import NabavkaContextMixin


class PurchaseContractListView(
    NabavkaContextMixin,
    RolePermissionRequiredMixin,
    LoginRequiredMixin,
    FilterView,
):
    model = Contract
    template_name = "nabavka/purchase_contract_list.html"
    context_object_name = "contracts"
    filterset_class = PurchaseContractFilter
    paginate_by = 50

    def get_queryset(self):
        parties = ContractParty.objects.select_related("partner").order_by("role", "partner__name")
        return (
            Contract.objects.filter(contract_type__code__startswith="KUP")
            .select_related("contract_type", "parent_contract")
            .prefetch_related(Prefetch("parties", queryset=parties))
            .annotate(
                linked_invoice_count=Count("nabavka_invoice_links__invoice", distinct=True),
                linked_invoice_amount=Sum("nabavka_invoice_links__invoice__amount"),
            )
            .order_by("-contract_date", "-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Kupovni ugovori"
        return ctx
