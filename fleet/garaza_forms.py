from django import forms
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from core.models import OrganizationalUnit

from hr.models import Employee

from .models import (
    Kvar,
    KvarPart,
    ProcurementItem,
    ProcurementRequest,
    Vehicle,
    VehicleTravelOrder,
)


class VehicleTravelOrderForm(forms.ModelForm):
    created_at = localized_date_field(
        required=True,
        label="Datum otvaranja",
    )
    pn_number = forms.IntegerField(
        label="PN broj",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Zaposleni",
    )
    start_mileage = forms.IntegerField(
        required=False,
        label="PoÄetna kilometraÅ¾a",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "km"}),
    )

    class Meta:
        model = VehicleTravelOrder
        fields = ["pn_number", "created_at", "employee", "vehicle", "start_mileage"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, "employee", None):
            inactive_employee = Employee.objects.filter(pk=self.instance.employee_id, is_active=False)
            if inactive_employee.exists():
                self.fields["employee"].queryset = self.fields["employee"].queryset | inactive_employee
        if not self.instance.pk:
            last_number = (
                VehicleTravelOrder.objects.order_by("-pn_number").values_list("pn_number", flat=True).first() or 0
            )
            self.initial.setdefault("pn_number", last_number + 1)
        self.fields["pn_number"].disabled = True


class VehicleTravelOrderCloseForm(forms.ModelForm):
    closed_at = localized_date_field(
        required=True,
        label="Datum zatvaranja",
    )
    end_mileage = forms.IntegerField(
        required=False,
        label="Krajnja kilometraÅ¾a",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "km"}),
    )

    class Meta:
        model = VehicleTravelOrder
        fields = ["closed_at", "end_mileage"]


class KvarForm(forms.ModelForm):
    VAN_IMS_CHOICES = [
        ("False", "IMS garaza"),
        ("True", "Van IMS-a"),
    ]
    WORK_TYPE_CHOICES = [
        ("mali_servis", "Mali servis"),
        ("veliki_servis", "Veliki servis"),
        ("popravka", "Popravka"),
    ]

    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    work_type = forms.ChoiceField(
        choices=WORK_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Vrsta intervencije",
        initial="popravka",
    )
    kilometraza = forms.IntegerField(
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Kilometraza",
    )
    opis = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        label="Opis kvara",
    )
    napomena = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        label="Napomena",
    )
    van_ims = forms.TypedChoiceField(
        choices=VAN_IMS_CHOICES,
        coerce=lambda val: val == "True",
        empty_value=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Popravka van IMS-a",
    )

    class Meta:
        model = Kvar
        fields = ["vehicle", "work_type", "kilometraza", "opis", "napomena", "van_ims"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get("van_ims") is None:
            self.initial["van_ims"] = "False"


class KvarPartForm(forms.ModelForm):
    class Meta:
        model = KvarPart
        fields = ["name", "quantity", "uom"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Naziv dela"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "uom": forms.TextInput(attrs={"class": "form-control", "placeholder": "kom/l/kg"}),
        }


class ProcurementRequestForm(forms.ModelForm):
    class Meta:
        model = ProcurementRequest
        fields = ["job_code", "note"]
        widgets = {
            "job_code": forms.Select(attrs={"class": "form-select"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            default_oj = OrganizationalUnit.objects.filter(code="832111").first()
        except Exception:
            default_oj = None
        if default_oj and not self.initial.get("job_code") and not getattr(self.instance, "job_code_id", None):
            self.initial["job_code"] = default_oj.pk


class ProcurementItemForm(forms.ModelForm):
    class Meta:
        model = ProcurementItem
        fields = ["name", "uom", "quantity", "note"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Naziv materijala / usluge"}),
            "uom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Jedinica mere"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "note": forms.TextInput(attrs={"class": "form-control", "placeholder": "Napomena (opciono)"}),
        }
