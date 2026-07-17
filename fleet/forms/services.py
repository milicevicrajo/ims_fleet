from django import forms
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field

from ..models import (
    DraftServiceTransaction,
    Kvar,
    Requisition,
    Service,
    ServiceTransaction,
    ServiceType,
    Vehicle,
)


class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = "__all__"


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = "__all__"


class ServiceTransactionForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    datum = localized_date_field(label="Datum")

    class Meta:
        model = ServiceTransaction
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.datum:
            self.initial["datum"] = self.instance.datum.strftime("%d.%m.%Y")


class DraftServiceTransactionForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    datum = localized_date_field(label="Datum")

    class Meta:
        model = DraftServiceTransaction
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.datum:
            self.initial["datum"] = self.instance.datum.strftime("%d.%m.%Y")

        if not self.initial.get("sif_vrs") and not getattr(self.instance, "sif_vrs", None):
            self.initial["sif_vrs"] = "EUF"

        for field_name, field in self.fields.items():
            field.required = False


class ServiceFixingFilterForm(forms.Form):
    datum_od = localized_date_field(
        required=False,
        label="Datum od",
    )
    datum_do = localized_date_field(
        required=False,
        label="Datum do",
    )
    partner = forms.CharField(
        required=False,
        label="Naziv partnera",
    )
    nije_garaza = forms.BooleanField(
        required=False,
        label="Samo servisi van garaže",
    )


class RequisitionForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    kvar = forms.ModelChoiceField(
        queryset=Kvar.objects.filter(van_ims=False),
        required=False,
        widget=Select2Widget(attrs={"class": "select2-method", "data-placeholder": "Izaberi IMS kvar"}),
        label="Kvar (IMS)",
    )
    datum_trebovanja = localized_date_field(label="Datum")

    class Meta:
        model = Requisition
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.datum_trebovanja:
            self.initial["datum_trebovanja"] = self.instance.datum_trebovanja.strftime("%d.%m.%Y")
