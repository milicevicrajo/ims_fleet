import django_filters
from django import forms
from django.db.models import Q
from core.models import OrganizationalUnit
from ugovori.models import Contract, Partner

from .models import ProcurementCase, ProcurementItemInvoiceLink, PurchaseOrder


PROCUREMENT_CASE_TYPE_FILTER_CHOICES = [
    ("", "Svi tipovi"),
    (ProcurementCase.CaseType.PROCUREMENT, "Zahtev za nabavku"),
    (ProcurementCase.CaseType.SERVICE, "Nabavka usluga"),
    (ProcurementCase.CaseType.EQUIPMENT, "Predlog za nabavku"),
]


GARAGE_FILTER_CHOICES = [
    ("", "Sve"),
    ("yes", "Garaža"),
    ("no", "Nije garaža"),
]


class ProcurementCaseFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q", label="Pretraga")
    case_type = django_filters.ChoiceFilter(choices=PROCUREMENT_CASE_TYPE_FILTER_CHOICES, label="Tip")
    status = django_filters.ChoiceFilter(choices=[("", "Svi statusi")] + list(ProcurementCase.Status.choices), label="Status")
    is_garage = django_filters.ChoiceFilter(choices=GARAGE_FILTER_CHOICES, method="filter_is_garage", label="Garaža")
    supplier = django_filters.CharFilter(method="filter_supplier", label="Dobavljač")
    job_code = django_filters.ModelChoiceFilter(queryset=OrganizationalUnit.objects.all().order_by("code"), label="OJ")

    class Meta:
        model = ProcurementCase
        fields = ["q", "case_type", "status", "is_garage", "supplier", "job_code"]

    def filter_q(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(case_number__icontains=value)
            | Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(supplier__name__icontains=value)
        )

    def filter_is_garage(self, queryset, name, value):
        if value == "yes":
            return queryset.filter(is_garage=True)
        if value == "no":
            return queryset.filter(is_garage=False)
        return queryset

    def filter_supplier(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        query = (
            Q(supplier__name__icontains=value)
            | Q(supplier__pib__icontains=value)
            | Q(supplier__maticni_broj__icontains=value)
        )
        if value.isdigit():
            query |= Q(supplier__external_sif_par=int(value))
        return queryset.filter(query)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class PurchaseOrderFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q", label="Pretraga")
    status = django_filters.ChoiceFilter(choices=[("", "Svi statusi")] + list(PurchaseOrder.Status.choices), label="Status")
    supplier = django_filters.ModelChoiceFilter(queryset=Partner.objects.filter(is_active=True), label="Dobavljač")

    class Meta:
        model = PurchaseOrder
        fields = ["q", "status", "supplier"]

    def filter_q(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(order_number__icontains=value)
            | Q(procurement_case__case_number__icontains=value)
            | Q(procurement_case__title__icontains=value)
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class ProcurementInvoiceLinkFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q", label="Pretraga")

    class Meta:
        model = ProcurementItemInvoiceLink
        fields = ["q"]

    def filter_q(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(invoice__invoice_number__icontains=value)
            | Q(invoice__supplier_name__icontains=value)
            | Q(procurement_item__name__icontains=value)
            | Q(procurement_item__procurement_case__case_number__icontains=value)
            | Q(procurement_item__procurement_case__title__icontains=value)
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.fields["q"].widget.attrs.setdefault("class", "form-control")


class PurchaseContractFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q", label="Pretraga")
    partner = django_filters.CharFilter(method="filter_partner", label="Partner")
    kind = django_filters.ChoiceFilter(choices=[("", "Sve")] + list(Contract.KIND_CHOICES), label="Vrsta")
    status = django_filters.ChoiceFilter(choices=[("", "Svi statusi")] + list(Contract.STATUS_CHOICES), label="Status")
    year = django_filters.ChoiceFilter(method="filter_year", label="Godina")

    class Meta:
        model = Contract
        fields = ["q", "partner", "kind", "status", "year"]

    def filter_q(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(contract_number__icontains=value)
            | Q(title__icontains=value)
            | Q(subject__icontains=value)
            | Q(parties__party_contract_number__icontains=value)
        ).distinct()

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

    def filter_year(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(contract_date__year=value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        years = [
            date_value.year
            for date_value in Contract.objects.filter(contract_type__code__startswith="KUP")
            .dates("contract_date", "year", order="DESC")
        ]
        self.form.fields["year"].choices = [("", "Sve godine")] + [(str(year), str(year)) for year in years]
        for field in self.form.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")
