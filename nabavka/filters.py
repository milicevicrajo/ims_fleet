import django_filters
from django import forms
from django.db.models import Q
from django_select2.forms import Select2Widget

from core.models import OrganizationalUnit
from ugovori.models import Partner

from .models import ProcurementCase, ProcurementInvoiceLink, PurchaseOrder


class ProcurementCaseFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q", label="Pretraga")
    case_type = django_filters.ChoiceFilter(choices=[("", "Svi tipovi")] + list(ProcurementCase.CaseType.choices), label="Tip")
    status = django_filters.ChoiceFilter(choices=[("", "Svi statusi")] + list(ProcurementCase.Status.choices), label="Status")
    supplier = django_filters.ModelChoiceFilter(queryset=Partner.objects.filter(is_active=True), label="Dobavljač")
    job_code = django_filters.ModelChoiceFilter(queryset=OrganizationalUnit.objects.all().order_by("code"), label="OJ")

    class Meta:
        model = ProcurementCase
        fields = ["q", "case_type", "status", "supplier", "job_code"]

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
        model = ProcurementInvoiceLink
        fields = ["q"]

    def filter_q(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(invoice_number__icontains=value)
            | Q(supplier_name__icontains=value)
            | Q(procurement_case__case_number__icontains=value)
            | Q(procurement_case__title__icontains=value)
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.fields["q"].widget.attrs.setdefault("class", "form-control")
