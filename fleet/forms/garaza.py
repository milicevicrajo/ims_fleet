from django import forms
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from hr.models import Employee

from ..models import (
    Kvar,
    KvarPart,
    Vehicle,
    VehicleTravelOrder,
)


class VehicleTravelOrderForm(forms.ModelForm):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"

    status = forms.ChoiceField(
        choices=(
            (STATUS_OPEN, "Otvoren"),
            (STATUS_CLOSED, "Zatvoren"),
        ),
        required=False,
        label="Status",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
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
        label="Početna kilometraža",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "km"}),
    )

    class Meta:
        model = VehicleTravelOrder
        fields = ["pn_number", "created_at", "status", "employee", "vehicle", "start_mileage"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
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
        if self.instance.pk and getattr(self.user, "is_superuser", False):
            self.initial["status"] = self.STATUS_CLOSED if self.instance.closed_at else self.STATUS_OPEN
        else:
            self.fields.pop("status", None)
        self.fields["pn_number"].disabled = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if (
            self.instance.pk
            and getattr(self.user, "is_superuser", False)
            and self.cleaned_data.get("status") == self.STATUS_OPEN
        ):
            instance.closed_at = None
            instance.end_mileage = None
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class VehicleTravelOrderCloseForm(forms.ModelForm):
    closed_at = localized_date_field(
        required=True,
        label="Datum zatvaranja",
    )
    end_mileage = forms.IntegerField(
        required=False,
        label="Krajnja kilometraža",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "km"}),
    )

    class Meta:
        model = VehicleTravelOrder
        fields = ["closed_at", "end_mileage"]

    def clean(self):
        cleaned_data = super().clean()
        closed_at = cleaned_data.get("closed_at")
        created_at = getattr(self.instance, "created_at", None)

        if closed_at and created_at and closed_at < created_at:
            self.add_error(
                "closed_at",
                "Datum zatvaranja ne može biti raniji od datuma otvaranja naloga.",
            )

        return cleaned_data


class PreviousVehicleTravelOrderForm(forms.ModelForm):
    created_at = localized_date_field(
        required=True,
        label="Datum pocetka prethodnog zaduzenja",
        help_text="Unesite datum od kada je automobil bio zaduzen pre ovog naloga.",
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Zaposleni na prethodnom zaduzenju",
    )
    start_mileage = forms.IntegerField(
        required=True,
        label="Pocetna kilometraza prethodnog zaduzenja",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "km"}),
        help_text="Ovo je pocetna kilometraza za obracun goriva prethodnog perioda.",
    )

    class Meta:
        model = VehicleTravelOrder
        fields = ["created_at", "employee", "start_mileage"]

    def __init__(self, *args, next_order=None, **kwargs):
        self.next_order = next_order
        super().__init__(*args, **kwargs)
        if next_order and next_order.employee_id:
            self.initial.setdefault("employee", next_order.employee_id)

    def clean_created_at(self):
        created_at = self.cleaned_data["created_at"]
        if self.next_order and created_at >= self.next_order.created_at:
            raise forms.ValidationError(
                "Datum pocetka prethodnog zaduzenja mora biti pre datuma trenutnog zaduzenja."
            )
        return created_at


class KvarForm(forms.ModelForm):
    VAN_IMS_CHOICES = [
        ("False", "IMS garaža"),
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
        label="Kilometraža",
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
