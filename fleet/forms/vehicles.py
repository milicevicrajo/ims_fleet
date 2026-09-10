from django import forms
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from core.models import OrganizationalUnit

from ..models import JobCode, TrafficCard, Vehicle, VehicleTenderDocument


class VehicleForm(forms.ModelForm):
    first_registration_date = localized_date_field(label="Datum prve registracije", required=False)
    purchase_date = localized_date_field(label="Datum kupovine", required=False)

    class Meta:
        model = Vehicle
        fields = ['inventory_number', 'chassis_number', 'brand', 'model', 'year_of_manufacture', 'category', 'color', 'homologation_number', 'first_registration_date', 'number_of_axles', 'engine_volume', 'engine_number', 'weight', 'engine_power', 'load_capacity', 'maximum_permissible_weight', 'fuel_type', 'number_of_seats', 'service_interval', 'purchase_value', 'value', 'purchase_date', 'partner_code', 'partner_name', 'invoice_number', 'description']

    def clean_inventory_number(self):
        return (self.cleaned_data.get('inventory_number') or '').strip() or None

    def clean_engine_number(self):
        return (self.cleaned_data.get('engine_number') or '').strip() or None

    def clean_chassis_number(self):
        from .onboarding import VehicleIdentityForm
        return VehicleIdentityForm.clean_chassis_number(self)

    def clean_year_of_manufacture(self):
        from .onboarding import VehicleIdentityForm
        return VehicleIdentityForm.clean_year_of_manufacture(self)

    def clean(self):
        data = super().clean()
        for key in ['engine_volume', 'engine_power', 'weight', 'load_capacity', 'maximum_permissible_weight', 'number_of_axles', 'number_of_seats', 'purchase_value', 'value', 'service_interval']:
            if data.get(key) is not None and data[key] < 0:
                self.add_error(key, 'Vrednost ne može biti negativna.')
        if data.get('category') == Vehicle.Category.TRAILER:
            for key in ['engine_number', 'engine_volume', 'engine_power', 'number_of_seats']:
                data[key] = None
            data['fuel_type'] = ''
        if (data.get('fuel_type') or '').strip().lower() in {'električno', 'elektricno', 'electric', 'električna energija'}:
            data['engine_volume'] = None
        return data


class TrafficCardForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
        required=False,
    )
    issue_date = localized_date_field(label="Datum izdavanja")
    valid_until = localized_date_field(label="Rok važenja saobraćajne, ako je naveden", required=False)
    registration_valid_until = localized_date_field(label="Registracija važi do", required=False)

    class Meta:
        model = TrafficCard
        fields = ['vehicle', 'registration_number', 'issue_date', 'valid_until', 'registration_valid_until', 'traffic_card_number', 'serial_number', 'owner', 'traffic_card_pdf', 'traffic_card_front_image', 'traffic_card_back_image']

    def clean_registration_number(self):
        from ..support.vehicle import format_license_plate
        return format_license_plate(self.cleaned_data['registration_number'])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.issue_date:
                self.initial["issue_date"] = self.instance.issue_date.strftime("%d.%m.%Y")
            if self.instance.valid_until:
                self.initial["valid_until"] = self.instance.valid_until.strftime("%d.%m.%Y")

        self.fields['vehicle'].required = True

        for field_name in ("traffic_card_pdf", "traffic_card_front_image", "traffic_card_back_image"):
            if field_name in self.fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget.attrs.update({"class": "form-control"})


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
