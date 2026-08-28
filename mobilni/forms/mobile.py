import datetime

from django import forms
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from fleet.models import Employee
from ugovori.models import Contract

from ..models import MobileAssignment, MobilePackage, MobileParkingExemption, MobileUsage, MobileUser


MONTH_CHOICES = [(month, f"{month:02d}") for month in range(1, 13)]


def _clean_mobile_phone_number(value):
    value = str(value or "").strip()
    if value.endswith(".0"):
        value = value[:-2]
    return "".join(ch for ch in value if ch.isdigit())


def year_choices():
    current_year = datetime.date.today().year
    return [(year, year) for year in range(current_year - 5, current_year + 3)]


class MobilePeriodImportForm(forms.Form):
    year = forms.ChoiceField(label="Godina", choices=year_choices)
    month = forms.ChoiceField(label="Mesec", choices=MONTH_CHOICES)
    file = forms.FileField(label="Fajl")


class MobileSimpleImportForm(forms.Form):
    file = forms.FileField(label="Fajl")


class MobilePackageForm(forms.ModelForm):
    valid_from = localized_date_field(label="Važi od", required=False)
    valid_to = localized_date_field(label="Važi do", required=False)

    class Meta:
        model = MobilePackage
        fields = [
            "partner_code",
            "partner_name",
            "name",
            "valid_from",
            "valid_to",
            "net_amount",
            "gross_amount",
            "description",
            "contract",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contract"].queryset = Contract.objects.filter(
            kind=Contract.MAIN,
        ).order_by("-contract_date", "contract_number")
        self.fields["contract"].widget = Select2Widget(attrs={"class": "select2-method"})


class MobileUserForm(forms.ModelForm):
    departure_date = localized_date_field(label="Datum odlaska", required=False)

    class Meta:
        model = MobileUser
        fields = [
            "organizational_unit",
            "employee_code",
            "full_name",
            "personal_number",
            "is_active",
            "departure_date",
            "employee",
        ]


class MobilePackageChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        label = obj.name
        if obj.valid_from:
            label = f"{label} ({obj.valid_from:%d.%m.%Y})"
        return label


class EmployeeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        name = str(obj).strip() or obj.original_full_name or "/"
        return f"{obj.employee_code} - {name}"


class MobileAssignmentForm(forms.ModelForm):
    package = MobilePackageChoiceField(
        queryset=MobilePackage.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Paket",
        required=True,
    )
    employee = EmployeeChoiceField(
        queryset=Employee.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Zaposleni",
        required=True,
    )

    class Meta:
        model = MobileAssignment
        fields = [
            "year",
            "month",
            "phone_number",
            "number_active",
            "package",
            "employee",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["package"].queryset = MobilePackage.objects.order_by("name", "-valid_from", "-id")
        self.fields["employee"].queryset = Employee.objects.order_by("last_name", "first_name", "employee_code")

    def clean_phone_number(self):
        value = _clean_mobile_phone_number(self.cleaned_data["phone_number"])
        if not value:
            raise forms.ValidationError("Unesi broj telefona.")
        return value


class MobileUsageForm(forms.ModelForm):
    class Meta:
        model = MobileUsage
        fields = "__all__"


class MobileParkingExemptionForm(forms.ModelForm):
    phone_number = forms.CharField(
        label="Broj telefona",
        widget=Select2Widget(
            attrs={
                "class": "select2-method",
                "data-placeholder": "Izaberi broj telefona",
            }
        ),
    )

    class Meta:
        model = MobileParkingExemption
        fields = ["phone_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_value = _clean_mobile_phone_number(getattr(self.instance, "phone_number", ""))
        self.fields["phone_number"].widget.choices = self._phone_choices(current_value)
        if current_value:
            self.initial["phone_number"] = current_value

    def _phone_choices(self, current_value):
        excluded_numbers = {
            _clean_mobile_phone_number(value)
            for value in MobileParkingExemption.objects.exclude(phone_number=current_value).values_list(
                "phone_number",
                flat=True,
            )
        }
        choices_by_number = {}
        assignments = (
            MobileAssignment.objects.exclude(phone_number="")
            .order_by("-year", "-month", "phone_number", "-id")
            .select_related("employee")
        )
        for assignment in assignments:
            phone_number = _clean_mobile_phone_number(assignment.phone_number)
            if not phone_number or phone_number in excluded_numbers or phone_number in choices_by_number:
                continue
            label = phone_number
            employee = assignment.employee
            if employee:
                employee_name = str(employee).strip() or employee.original_full_name or "/"
                label = f"{label} - {employee.employee_code} {employee_name}"
            if assignment.year and assignment.month:
                label = f"{label} ({assignment.month:02d}/{assignment.year})"
            choices_by_number[phone_number] = label

        if current_value and current_value not in choices_by_number:
            choices_by_number[current_value] = current_value

        return [("", "Izaberi broj telefona")] + sorted(choices_by_number.items(), key=lambda item: item[1])

    def clean_phone_number(self):
        value = _clean_mobile_phone_number(self.cleaned_data["phone_number"])
        if not value:
            raise forms.ValidationError("Unesi broj telefona.")
        return value
