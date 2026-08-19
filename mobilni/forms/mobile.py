import datetime

from django import forms

from core.form_fields import localized_date_field

from ..models import MobileAssignment, MobilePackage, MobileUsage, MobileUser


MONTH_CHOICES = [(month, f"{month:02d}") for month in range(1, 13)]


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
    valid_from = localized_date_field(label="Vazi od", required=False)
    valid_to = localized_date_field(label="Vazi do", required=False)

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
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


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


class MobileAssignmentForm(forms.ModelForm):
    valid_from = localized_date_field(label="Paket od", required=False)
    valid_to = localized_date_field(label="Paket do", required=False)

    class Meta:
        model = MobileAssignment
        fields = [
            "year",
            "month",
            "phone_number",
            "number_active",
            "package",
            "package_name",
            "valid_from",
            "valid_to",
            "package_net_amount",
            "mobile_user",
            "employee",
            "employee_code",
            "employee_name",
            "employee_active",
            "personal_number",
            "note",
        ]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class MobileUsageForm(forms.ModelForm):
    class Meta:
        model = MobileUsage
        fields = "__all__"
