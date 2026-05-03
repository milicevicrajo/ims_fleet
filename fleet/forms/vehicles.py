from django import forms
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from core.models import OrganizationalUnit

from ..models import JobCode, TrafficCard, Vehicle, VehicleTenderDocument


class VehicleForm(forms.ModelForm):
    first_registration_date = localized_date_field(label="Datum prve registracije")
    purchase_date = localized_date_field(label="Datum kupovine")

    class Meta:
        model = Vehicle
        fields = "__all__"


class TrafficCardForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
        required=False,
    )
    issue_date = localized_date_field(label="Datum izdavanja")
    valid_until = localized_date_field(label="Važi do")

    class Meta:
        model = TrafficCard
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.issue_date:
                self.initial["issue_date"] = self.instance.issue_date.strftime("%d.%m.%Y")
            if self.instance.valid_until:
                self.initial["valid_until"] = self.instance.valid_until.strftime("%d.%m.%Y")

        for field_name, field in self.fields.items():
            field.required = True


class VehicleTenderDocumentForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label=_("Vozilo"),
    )
    taken_at = localized_date_field(
        required=False,
        label=_("Datum fotografisanja"),
    )

    class Meta:
        model = VehicleTenderDocument
        fields = ["vehicle", "document_type", "title", "image", "description", "taken_at", "is_active"]
        widgets = {
            "document_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.taken_at:
            self.initial["taken_at"] = self.instance.taken_at.strftime("%d.%m.%Y")


class JobCodeForm(forms.ModelForm):
    organizational_unit = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Organizaciona jedinica",
    )
    assigned_date = localized_date_field(label="Datum dodele")

    class Meta:
        model = JobCode
        fields = "__all__"
