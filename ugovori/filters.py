import django_filters
from django.db.models import Q
from django_filters import CharFilter, ChoiceFilter, DateFilter, ModelChoiceFilter

from .models import BusinessRequest, Contract, ContractType, Offer


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
    center = ChoiceFilter(
        method="filter_center",
        label="Centar",
        empty_label=None,
    )
    year = ChoiceFilter(
        method="filter_year",
        label="Godina",
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
        fields = ["partner", "contract_type", "kind", "status", "center", "year"]

    @staticmethod
    def _contract_center(contract_number):
        if not contract_number or "-" not in contract_number:
            return ""
        return contract_number.split("-", 1)[0].strip()

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

    def filter_center(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(contract_number__startswith=f"{value}-")

    def filter_year(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(contract_date__year=value)

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(contract_number__icontains=value) | Q(title__icontains=value)
            )
        return queryset

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        center_values = sorted(
            {
                center
                for center in (
                    self._contract_center(contract_number)
                    for contract_number in Contract.objects.values_list("contract_number", flat=True)
                )
                if center
            },
            key=lambda value: (not value.isdigit(), int(value) if value.isdigit() else value),
        )
        year_values = [
            date_value.year
            for date_value in Contract.objects.dates("contract_date", "year", order="DESC")
        ]
        self.form.fields["center"].choices = [("", "---------")] + [
            (value, value) for value in center_values
        ]
        self.form.fields["year"].choices = [("", "---------")] + [
            (str(value), str(value)) for value in year_values
        ]
        for field in self.form.fields.values():
            if hasattr(field, "widget"):
                from django.forms import Select, TextInput
                if isinstance(field.widget, Select):
                    field.widget.attrs.setdefault("class", "form-select")
                elif isinstance(field.widget, TextInput):
                    field.widget.attrs.setdefault("class", "form-control")


class BusinessRequestFilter(django_filters.FilterSet):
    partner = CharFilter(method="filter_partner", label="Partner")
    request_type = ChoiceFilter(
        choices=[("", "---------")] + BusinessRequest.REQUEST_TYPE_CHOICES,
        label="Tip",
        empty_label=None,
    )
    status = ChoiceFilter(
        choices=[("", "---------")] + BusinessRequest.STATUS_CHOICES,
        label="Status",
        empty_label=None,
    )
    request_date_from = DateFilter(
        field_name="request_date",
        lookup_expr="gte",
        label="Datum od",
    )
    request_date_to = DateFilter(
        field_name="request_date",
        lookup_expr="lte",
        label="Datum do",
    )
    search = CharFilter(method="filter_search", label="Pretraga")

    class Meta:
        model = BusinessRequest
        fields = ["partner", "request_type", "status"]

    def filter_partner(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        query = (
            Q(partner__name__icontains=value)
            | Q(partner__pib__icontains=value)
            | Q(partner__maticni_broj__icontains=value)
            | Q(external_partner_name__icontains=value)
        )
        if value.isdigit():
            query |= Q(partner__external_sif_par=int(value))
        return queryset.filter(query)

    def filter_search(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(request_number__icontains=value)
            | Q(subject__icontains=value)
            | Q(description__icontains=value)
            | Q(center__icontains=value)
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.values():
            if hasattr(field, "widget"):
                from django.forms import Select, TextInput
                if isinstance(field.widget, Select):
                    field.widget.attrs.setdefault("class", "form-select")
                elif isinstance(field.widget, TextInput):
                    field.widget.attrs.setdefault("class", "form-control")


class OfferFilter(django_filters.FilterSet):
    partner = CharFilter(method="filter_partner", label="Partner")
    direction = ChoiceFilter(
        choices=[("", "---------")] + Offer.DIRECTION_CHOICES,
        label="Smer",
        empty_label=None,
    )
    offer_type = ChoiceFilter(
        choices=[("", "---------")] + Offer.OFFER_TYPE_CHOICES,
        label="Tip",
        empty_label=None,
    )
    status = ChoiceFilter(
        choices=[("", "---------")] + Offer.STATUS_CHOICES,
        label="Status",
        empty_label=None,
    )
    offer_date_from = DateFilter(
        field_name="offer_date",
        lookup_expr="gte",
        label="Datum od",
    )
    offer_date_to = DateFilter(
        field_name="offer_date",
        lookup_expr="lte",
        label="Datum do",
    )
    search = CharFilter(method="filter_search", label="Pretraga")

    class Meta:
        model = Offer
        fields = ["partner", "direction", "offer_type", "status"]

    def filter_partner(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        query = (
            Q(partner__name__icontains=value)
            | Q(partner__pib__icontains=value)
            | Q(partner__maticni_broj__icontains=value)
            | Q(external_partner_name__icontains=value)
        )
        if value.isdigit():
            query |= Q(partner__external_sif_par=int(value))
        return queryset.filter(query)

    def filter_search(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(offer_number__icontains=value)
            | Q(subject__icontains=value)
            | Q(description__icontains=value)
            | Q(request__request_number__icontains=value)
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.values():
            if hasattr(field, "widget"):
                from django.forms import Select, TextInput
                if isinstance(field.widget, Select):
                    field.widget.attrs.setdefault("class", "form-select")
                elif isinstance(field.widget, TextInput):
                    field.widget.attrs.setdefault("class", "form-control")
