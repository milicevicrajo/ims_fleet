import django_filters
from django_filters import CharFilter, ChoiceFilter, DateFilter, ModelChoiceFilter

from .models import Contract, ContractType, Partner


class ContractFilter(django_filters.FilterSet):
    partner = ModelChoiceFilter(
        queryset=Partner.objects.filter(is_active=True),
        field_name="parties__partner",
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
        widget=django_filters.widgets.DateRangeWidget,
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

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                contract_number__icontains=value
            ) | queryset.filter(title__icontains=value)
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
