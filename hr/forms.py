import re
import unicodedata

from django import forms

from .models import Employee, EmployeeCVItem


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ["display_first_name_override", "display_last_name_override"]


class EmployeeCVItemForm(forms.ModelForm):
    class Meta:
        model = EmployeeCVItem
        fields = [
            "title",
            "organization",
            "role",
            "start_date",
            "end_date",
            "description",
            "skills",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "js-date"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "js-date"}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "skills": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "Datum zavrsetka ne moze biti pre datuma pocetka.")
        return cleaned_data


def _normalize_name_without_diacritics(value):
    value = (value or "").strip().casefold().replace("đ", "dj")
    value = "".join(
        character
        for character in unicodedata.normalize("NFD", value)
        if unicodedata.category(character) != "Mn"
    )
    return re.sub(r"\s+", " ", value)


class EmployeeNameCorrectionForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["display_first_name_override", "display_last_name_override"]
        labels = {
            "display_first_name_override": "Ime",
            "display_last_name_override": "Prezime",
        }
        help_texts = {
            "display_first_name_override": "Dozvoljena je samo korekcija dijakritika. Ostavi prazno za HR vrednost.",
            "display_last_name_override": "Dozvoljena je samo korekcija dijakritika. Ostavi prazno za HR vrednost.",
        }

    def _validate_diacritics_only(self, override_field, source_field):
        value = (self.cleaned_data.get(override_field) or "").strip()
        source_value = getattr(self.instance, source_field) or ""
        if value and _normalize_name_without_diacritics(value) != _normalize_name_without_diacritics(source_value):
            self.add_error(
                override_field,
                "Mozes promeniti samo dijakritike, bez izmene slova ili redosleda.",
            )
        return value

    def clean_display_first_name_override(self):
        return self._validate_diacritics_only("display_first_name_override", "first_name")

    def clean_display_last_name_override(self):
        return self._validate_diacritics_only("display_last_name_override", "last_name")
