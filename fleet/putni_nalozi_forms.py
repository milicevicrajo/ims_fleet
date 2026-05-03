from datetime import date

from django import forms
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from core.models import OrganizationalUnit

from hr.models import Employee

from .models import PutniNalog, Vehicle


class PutniNalogForm(forms.ModelForm):
    order_date = localized_date_field(label="Datum izdavanja naloga")

    transport_type = forms.ChoiceField(
        label="Odaberi prevozno sredstvo",
        required=False,
        choices=(
            ("ims", "Auto IMS"),
            ("other", "Ostalo"),
        ),
        widget=forms.RadioSelect(),
    )
    employee_type = forms.ChoiceField(
        label="Odaberi zaposlenog",
        required=False,
        choices=(
            ("ims", "Zaposleni IMS"),
            ("other", "Ostali"),
        ),
        widget=forms.RadioSelect(),
    )
    order_number = forms.CharField(
        label="Broj naloga",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
    )
    start_sequence = forms.IntegerField(
        label="PoÄetni broj naloga",
        required=False,
        widget=forms.HiddenInput(),
        help_text="Unesi samo prvi broj za centar/godinu ako ne postoji prethodni.",
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
        required=False,
    )
    other_vehicle = forms.CharField(
        label="Prevozno sredstvo (ostalo)",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Zaposleni",
        required=False,
    )
    other_employee_name = forms.CharField(
        label="Zaposleni (ostalo)",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    job_code = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="TroÅ¡kovi idu na teret",
    )
    travel_date = localized_date_field(label="Datum putovanja")
    napomena = forms.CharField(
        label="Napomena",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    class Meta:
        model = PutniNalog
        fields = "__all__"
        widgets = {
            "order_date": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("opravdan", None)
        self.fields.pop("storniran", None)
        if self.instance and getattr(self.instance, "employee", None):
            inactive_employee = Employee.objects.filter(pk=self.instance.employee_id, is_active=False)
            if inactive_employee.exists():
                self.fields["employee"].queryset = self.fields["employee"].queryset | inactive_employee

        if self.instance and self.instance.pk:
            if self.instance.order_date:
                self.initial["order_date"] = self.instance.order_date.strftime("%d.%m.%Y")
            if self.instance.travel_date:
                self.initial["travel_date"] = self.instance.travel_date.strftime("%d.%m.%Y")
        elif not self.is_bound:
            self.initial.setdefault("order_date", date.today().strftime("%d.%m.%Y"))

        optional_fields = {
            "order_date",
            "order_number",
            "start_sequence",
            "vehicle",
            "other_vehicle",
            "transport_type",
            "is_weekly",
            "employee",
            "other_employee_name",
            "employee_type",
            "napomena",
        }
        for field_name, field in self.fields.items():
            if field_name not in optional_fields:
                field.required = True

        if self.instance and self.instance.pk:
            if self.instance.vehicle:
                self.initial["transport_type"] = "ims"
            elif self.instance.other_vehicle:
                self.initial["transport_type"] = "other"
        elif not self.is_bound:
            self.initial.setdefault("transport_type", "ims")

        if self.instance and getattr(self.instance, "employee", None):
            self.initial.setdefault("employee_type", "ims")
        elif self.instance and getattr(self.instance, "other_employee_name", None):
            self.initial.setdefault("employee_type", "other")
        elif not self.is_bound:
            self.initial.setdefault("employee_type", "ims")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("order_date"):
            if self.instance and self.instance.pk and self.instance.order_date:
                cleaned["order_date"] = self.instance.order_date
            else:
                cleaned["order_date"] = date.today()

        job_code = cleaned.get("job_code")
        travel_date = cleaned.get("travel_date")
        start_sequence = cleaned.get("start_sequence")
        vehicle = cleaned.get("vehicle")
        other_vehicle = cleaned.get("other_vehicle")
        transport_type = cleaned.get("transport_type")

        if vehicle and other_vehicle:
            self.add_error("vehicle", "MoÅ¾eÅ¡ izabrati samo jedno prevozno sredstvo.")
            self.add_error("other_vehicle", "MoÅ¾eÅ¡ uneti samo jedno prevozno sredstvo.")
        elif not vehicle and not other_vehicle:
            self.add_error("vehicle", "Obavezno je uneti vozilo (Auto IMS) ili ostalo prevozno sredstvo.")
            self.add_error("other_vehicle", "Obavezno je uneti vozilo (Auto IMS) ili ostalo prevozno sredstvo.")

        if transport_type == "ims" and other_vehicle:
            self.add_error("other_vehicle", "Kada je izabrano Auto IMS, polje 'Ostalo' mora biti prazno.")
        if transport_type == "other" and vehicle:
            self.add_error("vehicle", "Kada je izabrano Ostalo, polje 'Vozilo' mora biti prazno.")

        employee_type = cleaned.get("employee_type") or "ims"
        employee = cleaned.get("employee")
        other_employee_name = cleaned.get("other_employee_name")

        if employee_type == "ims":
            if not employee:
                self.add_error("employee", "Obavezno izaberi zaposlenog iz IMS.")
            cleaned["other_employee_name"] = None
        elif employee_type == "other":
            if not other_employee_name:
                self.add_error("other_employee_name", "Unesi ime zaposlenog.")
            cleaned["employee"] = None

        if job_code and travel_date:
            center_code = getattr(job_code, "center", None)
            year = travel_date.year
            if center_code:
                center_code = str(center_code).strip()
                prefix = f"{center_code}/{year}-"
                exists = PutniNalog.objects.filter(order_number__startswith=prefix).exists()
                has_any_for_center = PutniNalog.objects.filter(order_number__startswith=f"{center_code}/").exists()
                if not exists and not start_sequence and not has_any_for_center:
                    self.add_error(
                        "start_sequence",
                        "Unesi poÄetni broj za ovaj centar/godinu (ne postoji prethodni broj).",
                    )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        start_sequence = self.cleaned_data.get("start_sequence")
        if start_sequence:
            instance._start_sequence = start_sequence

        if commit:
            instance.save()
            self.save_m2m()
        return instance
