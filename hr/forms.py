import re
import unicodedata

from django import forms
from django.forms import inlineformset_factory

from core.models import OrganizationalUnit

from .models import Employee, EmployeeCVItem, WorkTimeSheet, WorkTimeSheetLine


WORK_TIME_SHEET_LINE_COUNT = 12
WORK_TIME_SHEET_DAY_FIELDS = [f"day_{day}" for day in range(1, 32)]


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = "__all__"
        labels = {
            "display_first_name_override": "Ime za prikaz",
            "display_last_name_override": "Prezime za prikaz",
            "skip_hr_identity_update": "Ne azuriraj ime, prezime, titulu i pol iz HR-a",
        }
        help_texts = {
            "display_first_name_override": (
                "Ako je popunjeno, aplikacija prikazuje ovu vrednost i HR sinhronizacija je nece prepisati. "
                "Ostavi prazno za HR vrednost."
            ),
            "display_last_name_override": (
                "Ako je popunjeno, aplikacija prikazuje ovu vrednost i HR sinhronizacija je nece prepisati. "
                "Ostavi prazno za HR vrednost."
            ),
            "skip_hr_identity_update": (
                "Ukljuci kada rucno menjas titulu, ime, prezime ili pol i ne zelis da ih HR sync vrati."
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not getattr(user, "is_superuser", False):
            self.fields.pop("display_first_name_override", None)
            self.fields.pop("display_last_name_override", None)
            self.fields.pop("skip_hr_identity_update", None)


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


class WorkTimeSheetForm(forms.ModelForm):
    class Meta:
        model = WorkTimeSheet
        fields = ["status", "meal_days", "meal_organizational_unit", "field_allowance_days"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select form-select-sm work-status-select"}),
            "meal_days": forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm integer-input",
                    "inputmode": "numeric",
                    "pattern": "[0-9]*",
                    "autocomplete": "off",
                }
            ),
            "meal_organizational_unit": forms.Select(
                attrs={"class": "form-select form-select-sm meal-code-select select2-method"}
            ),
            "field_allowance_days": forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm integer-input",
                    "inputmode": "numeric",
                    "pattern": "[0-9]*",
                    "autocomplete": "off",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["meal_organizational_unit"].queryset = OrganizationalUnit.objects.order_by("code", "name")
        self.fields["meal_organizational_unit"].empty_label = ""
        self.fields["meal_organizational_unit"].label_from_instance = lambda obj: obj.code

    def clean(self):
        cleaned_data = super().clean()
        meal_days = cleaned_data.get("meal_days")
        meal_organizational_unit = cleaned_data.get("meal_organizational_unit")
        if meal_days and not meal_organizational_unit:
            self.add_error("meal_organizational_unit", "Izaberi sifru posla za topli obrok.")
        return cleaned_data


class WorkTimeSheetLineForm(forms.ModelForm):
    class Meta:
        model = WorkTimeSheetLine
        fields = [
            "line_number",
            "organizational_unit",
            *WORK_TIME_SHEET_DAY_FIELDS,
            "work_conditions",
            "note",
        ]
        widgets = {
            "line_number": forms.HiddenInput(),
            "organizational_unit": forms.Select(
                attrs={"class": "form-select form-select-sm work-code-select select2-method"}
            ),
            "work_conditions": forms.TextInput(attrs={"class": "form-control form-control-sm work-condition-input"}),
            "note": forms.TextInput(attrs={"class": "form-control form-control-sm note-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organizational_unit"].queryset = OrganizationalUnit.objects.order_by("code", "name")
        self.fields["organizational_unit"].empty_label = ""
        self.fields["organizational_unit"].label_from_instance = lambda obj: obj.code
        for field_name in WORK_TIME_SHEET_DAY_FIELDS:
            self.fields[field_name].widget = forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm hours-input integer-input",
                    "inputmode": "numeric",
                    "pattern": "[0-9]*",
                    "autocomplete": "off",
                }
            )

    def clean(self):
        cleaned_data = super().clean()
        for field_name in WORK_TIME_SHEET_DAY_FIELDS:
            value = cleaned_data.get(field_name)
            if value is not None and (value < 0 or value > 24):
                self.add_error(field_name, "Sati moraju biti izmedju 0 i 24.")
        return cleaned_data


WorkTimeSheetLineFormSet = inlineformset_factory(
    WorkTimeSheet,
    WorkTimeSheetLine,
    form=WorkTimeSheetLineForm,
    extra=0,
    can_delete=False,
    min_num=WORK_TIME_SHEET_LINE_COUNT,
    max_num=WORK_TIME_SHEET_LINE_COUNT,
    validate_min=True,
    validate_max=True,
)
