import datetime

from django import forms
from django.utils import timezone
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.initial.setdefault("year", today.year)
        self.initial.setdefault("month", today.month)


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
            "link_status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["employee"]
        field.label_from_instance = self._employee_label
        field.widget = forms.Select(attrs={"class": "form-select form-control"})
        field.queryset = Employee.objects.order_by("last_name", "first_name", "employee_code")

    @staticmethod
    def _employee_label(employee):
        name = str(employee).strip() or employee.original_full_name or "/"
        return f"{employee.employee_code} - {name}"

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get("employee")
        employee_code = cleaned_data.get("employee_code")
        link_status = cleaned_data.get("link_status")

        if link_status == MobileUser.LinkStatus.NON_EMPLOYEE:
            cleaned_data["employee"] = None
        elif link_status == MobileUser.LinkStatus.MANUAL and not employee:
            self.add_error("employee", "Izaberi zaposlenog za rucnu vezu.")
        elif employee and employee_code and employee.employee_code != employee_code:
            cleaned_data["link_status"] = MobileUser.LinkStatus.MANUAL
        elif employee and employee_code and employee.employee_code == employee_code:
            cleaned_data["link_status"] = MobileUser.LinkStatus.AUTO
        elif link_status == MobileUser.LinkStatus.AUTO and not employee:
            cleaned_data["link_status"] = MobileUser.LinkStatus.UNMATCHED

        return cleaned_data


class MobilePackageChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        label = obj.name
        if obj.valid_from:
            label = f"{label} ({obj.valid_from:%d.%m.%Y})"
        return label


class MobileUserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        name = obj.full_name or "/"
        link = obj.get_link_status_display()
        return f"{obj.employee_code} - {name} ({link})"


class MobileAssignmentForm(forms.ModelForm):
    package = MobilePackageChoiceField(
        queryset=MobilePackage.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Paket",
        required=True,
    )
    mobile_user = MobileUserChoiceField(
        queryset=MobileUser.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Korisnik mobilnog",
        required=False,
    )

    class Meta:
        model = MobileAssignment
        fields = [
            "year",
            "month",
            "phone_number",
            "number_active",
            "package",
            "mobile_user",
            "source_employee_code",
            "source_full_name",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["package"].queryset = MobilePackage.objects.order_by("name", "-valid_from", "-id")
        self.fields["mobile_user"].queryset = MobileUser.objects.select_related("employee").order_by(
            "full_name",
            "employee_code",
        )

    def clean_phone_number(self):
        value = _clean_mobile_phone_number(self.cleaned_data["phone_number"])
        if not value:
            raise forms.ValidationError("Unesi broj telefona.")
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.mobile_user_id:
            instance.employee = instance.mobile_user.employee if instance.mobile_user.employee_id else None
            if instance.source_employee_code is None:
                instance.source_employee_code = instance.mobile_user.employee_code
            if not instance.source_full_name:
                instance.source_full_name = instance.mobile_user.full_name
        else:
            instance.employee = None
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class MobileUsageForm(forms.ModelForm):
    class Meta:
        model = MobileUsage
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)
        assignment = instance.assignment
        if assignment:
            instance.employee = assignment.linked_employee
        else:
            instance.employee = None
        if commit:
            instance.save()
            self.save_m2m()
        return instance


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
            .select_related("employee", "mobile_user", "mobile_user__employee")
        )
        for assignment in assignments:
            phone_number = _clean_mobile_phone_number(assignment.phone_number)
            if not phone_number or phone_number in excluded_numbers or phone_number in choices_by_number:
                continue
            label = phone_number
            employee_code = assignment.display_employee_code
            employee_name = assignment.display_employee_name
            if employee_code or employee_name:
                label = f"{label} - {employee_code or '/'} {employee_name or '/'}"
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
