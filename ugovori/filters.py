import django_filters
from django.db.models import Q
from django_filters import CharFilter, ChoiceFilter, DateFilter, ModelChoiceFilter

from .models import Contract, ContractType


class ContractFilter(django_filters.FilterSet):
    partner = CharFilter(
        method="filter_partner",
        label="Partner",
    )
    contract_type = ModelChoiceFilter(
        queryset=ContractType.objects.filter(is_active=True),
        label="Tip ugovora",
    )
    kind = ChoiceFilter(
        choices=[("", "---------")] + Contract.KIND_CHOICES,
        label="Vrsta",
        empty_label=None,
    )
    status = ChoiceFilter(
        choices=[("", "---------")] + Contract.STATUS_CHOICES,
        label="Status",
        empty_label=None,
    )
    contract_date_from = DateFilter(
        field_name="contract_date",
        lookup_expr="gte",
        label="Datum od",
    )
    contract_date_to = DateFilter(
        field_name="contract_date",
        lookup_expr="lte",
        label="Datum do",
    )
    search = CharFilter(method="filter_search", label="Pretraga (broj / naslov)")

    class Meta:
        model = Contract
        fields = ["partner", "contract_type", "kind", "status"]

    def filter_partner(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset

        query = (
            Q(parties__partner__name__icontains=value)
            | Q(parties__partner__pib__icontains=value)
            | Q(parties__partner__maticni_broj__icontains=value)
        )
        if value.isdigit():
            query |= Q(parties__partner__external_sif_par=int(value))
        return queryset.filter(query).distinct()

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(contract_number__icontains=value) | Q(title__icontains=value)
            )
        return queryset

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.values():
            if hasattr(field, "widget"):
                from django.forms import Select, TextInput
                if isinstance(field.widget, Select):
                    field.widget.attrs.setdefault("class", "form-select")
                elif isinstance(field.widget, TextInput):
                    field.widget.attrs.setdefault("class", "form-control")
