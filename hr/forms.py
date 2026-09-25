import re
import unicodedata

from django import forms
from django.forms import inlineformset_factory
from django.db.models import Q
from django.utils import timezone

from core.models import OrganizationalUnit
from .form_layout import SekcijeMixin

from .models import Employee, EmployeeCVItem, WorkTimeSheet, WorkTimeSheetLine, WorkTimeCategory


WORK_TIME_SHEET_LINE_COUNT = 12
WORK_TIME_SHEET_DAY_FIELDS = [f"day_{day}" for day in range(1, 32)]

# Polja koja HR sinhronizacija (hr/sync.py) prepisuje pri svakom pokretanju. Forma ih označava,
# da korisnik zna da će ručna izmena trajati samo do sledeće sinhronizacije.
HR_SYNC_FIELDS = frozenset({
    "title", "original_full_name", "first_name", "last_name", "position", "department_code", "org_unit_code",
    "system_code", "system_name", "gender", "date_of_birth", "date_of_joining", "phone_number", "mobile_phone",
    "is_active", "personal_number", "account_number", "address", "education", "job_code", "job_title",
    "status_code", "status_name", "slava", "residence_municipality", "recipient_code", "recipient_name",
})


class EmployeeForm(SekcijeMixin, forms.ModelForm):
    # (naslov, kratak opis, polja, uputstvo, ikonica)
    SECTIONS = (
        ("identitet", "Identitet", "Ko je zaposleni.", (
            "employee_code", "title", "first_name", "last_name", "gender", "date_of_birth", "personal_number",
            "is_active"),
         "Šifra zaposlenog je ključ za HR sinhronizaciju, radne liste i prolaze — ne menja se posle unosa. "
         "Ime, pol, datum rođenja i JMBG dolaze iz HR-a i biće vraćeni pri sledećoj sinhronizaciji, osim ako "
         "je u sekciji „Prikaz imena“ uključeno „Ne ažuriraj ime, prezime, titulu i pol iz HR-a“.",
         "mdi-account-outline"),
        ("prikaz", "Prikaz imena i ćirilica", "Kako se ime prikazuje u aplikaciji i u rešenjima.", (
            "display_first_name_override", "display_last_name_override", "full_name_cyrillic",
            "original_full_name", "skip_hr_identity_update"),
         "Ime i prezime za prikaz služe samo za ispravku kvačica (npr. Petrovic → Petrović); HR ih ne prepisuje. "
         "Ime ćirilicom koristi se u rešenjima kada automatsko preslovljavanje pogreši kod lj, nj i dž.",
         "mdi-format-letter-case"),
        ("zaposlenje", "Zaposlenje i organizacija", "Gde radi i na kom radnom mestu.", (
            "date_of_joining", "position", "org_unit_code", "department_code", "job_code", "job_title",
            "status_code", "status_name", "system_code", "system_name"),
         "OJ određuje centar zaposlenog, obuhvat pristupa i podrazumevanu šifru posla na radnoj listi. "
         "Svi podaci ove sekcije dolaze iz HR-a.",
         "mdi-office-building-outline"),
        ("obracun", "Obračun zarada", "Veza sa obračunom i vrste rada na radnoj listi.", (
            "recipient_code", "recipient_name", "account_number"),
         "Vrsta primaoca određuje koje vrste rada i odsustva zaposleni vidi u radnoj listi (Elementi RL).",
         "mdi-cash-multiple"),
        ("kontakt", "Kontakt i adresa", None, (
            "phone_number", "mobile_phone", "address", "residence_municipality"),
         "Kontakt podaci dolaze iz HR-a; izmena ovde traje do sledeće sinhronizacije.",
         "mdi-phone-outline"),
        ("dodatno", "Obrazovanje i slava", "Slava se u radnoj listi predlaže kao verski praznik.", (
            "education", "slava", "slava_datum"),
         "Naziv slave dolazi iz HR-a, a datum slave se upisuje ovde i HR ga ne menja. Od datuma se koriste samo "
         "dan i mesec. Za poznate slave sa stalnim datumom (Sv. Nikola, Đurđevdan, Aranđelovdan…) datum se "
         "predlaže iz naziva; pokretne slave (Spasovdan, Trojice) upišite ručno.",
         "mdi-church"),
    )

    class Meta:
        model = Employee
        fields = "__all__"
        labels = {
            "display_first_name_override": "Ime za prikaz",
            "display_last_name_override": "Prezime za prikaz",
            "skip_hr_identity_update": "Ne ažuriraj ime, prezime, titulu i pol iz HR-a",
            "is_active": "Aktivan zaposleni",
        }
        help_texts = {
            "recipient_code": "Preuzima se iz polja sif_prim u HR izvoru; sinhronizacija ažurira ovu vrednost.",
            "recipient_name": "Izvorni naziv iz HR-a. Naziv šifrarnika se zasebno uređuje u Elementima RL.",
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
        self.access_user = user
        for name in ("date_of_birth", "date_of_joining", "slava_datum"):
            if name in self.fields:
                self.fields[name].input_formats = ["%d.%m.%Y", "%d.%m.%Y.", "%Y-%m-%d"]
                self.fields[name].widget = forms.DateInput(format="%d.%m.%Y", attrs={
                    "class": "form-control js-date", "autocomplete": "off", "placeholder": "dd.mm.gggg"})
        for name in HR_SYNC_FIELDS:
            if name in self.fields:
                self.fields[name].hr_sync = True
        self.slava_predlog = False
        if self.instance.pk and not self.instance.slava_datum and "slava_datum" in self.fields:
            from datetime import date
            from hr.services.praznici import predlog_datuma_slave
            predlog = predlog_datuma_slave(self.instance.slava)
            if predlog:
                # Samo predlog u formi; upisuje se tek kada korisnik sačuva.
                self.initial["slava_datum"] = date(timezone.localdate().year, predlog[1], predlog[0])
                self.slava_predlog = True
                attrs = self.fields["slava_datum"].widget.attrs
                attrs["class"] = f'{attrs.get("class", "")} ef-predlog'.strip()
                self.fields["slava_datum"].help_text = (f"Predloženo iz naziva slave „{self.instance.slava}“ — "
                                                        "proverite i sačuvajte. Godina nije bitna.")
        if not getattr(user, "is_superuser", False):
            self.fields.pop("display_first_name_override", None)
            self.fields.pop("display_last_name_override", None)
            self.fields.pop("skip_hr_identity_update", None)

    def clean(self):
        data = super().clean()
        from hr.access import allowed_unit_codes, has_restricted_scope
        if self.access_user and has_restricted_scope(self.access_user):
            code = str(data.get('org_unit_code') or data.get('department_code') or '').strip()
            if code not in allowed_unit_codes(self.access_user):
                self.add_error('org_unit_code', 'Organizaciona jedinica nije u vašem dozvoljenom obuhvatu.')
        return data


class EmployeeCVItemForm(SekcijeMixin, forms.ModelForm):
    SECTIONS = (
        ("posao", "Posao ili projekat", "Gde ste radili i na kojoj ulozi.", ("title", "organization", "role"),
         "Naziv je ono što se vidi u pregledu CV-a (npr. „Nadzor nad izgradnjom mosta“). Organizacija može biti "
         "Institut IMS ili drugi poslodavac, a uloga je vaša funkcija na tom poslu.", "mdi-briefcase-outline"),
        ("period", "Period", "Od kada do kada.", ("start_date", "end_date"),
         "Za posao koji još traje ostavite datum završetka prazan.", "mdi-calendar-range"),
        ("opis", "Opis i veštine", None, ("description", "skills"),
         "Opišite zadatke i rezultate u nekoliko rečenica; veštine navedite odvojene zarezom.", "mdi-text-box-outline"),
    )

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


class EmployeeNameCorrectionForm(SekcijeMixin, forms.ModelForm):
    SECTIONS = (
        ("ime", "Ime i prezime", "Ispravka kvačica u prikazu imena.", ("display_first_name_override", "display_last_name_override"),
         "Možete ispraviti samo dijakritike (npr. Petrovic → Petrović), bez izmene slova ili redosleda. Izvorna HR "
         "vrednost ostaje sačuvana, a naredna sinhronizacija neće pregaziti ovu korekciju.", "mdi-format-letter-case"),
    )

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
            "work_category",
        ]
        widgets = {
            "line_number": forms.HiddenInput(),
            "organizational_unit": forms.Select(
                attrs={"class": "form-select form-select-sm work-code-select select2-method"}
            ),
            "work_conditions": forms.TextInput(attrs={"class": "form-control form-control-sm work-condition-input"}),
            "work_category": forms.Select(attrs={"class": "form-select form-select-sm select2-method work-category-select", "data-placeholder": "Vrsta rada / odsustva", "data-allow-clear": "true"}),
        }

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        employee = employee or (self.instance.sheet.employee if self.instance.sheet_id else None)
        available = WorkTimeCategory.objects.filter(
            is_active=True, employee_selectable=True,
            elements__is_active=True, elements__recipient_type__is_active=True,
            elements__recipient_type__code=getattr(employee, "recipient_code", ""),
        ).values_list("pk", flat=True)
        # Keep an already selected historical/inactive category visible, without offering it on new rows.
        self.fields["work_category"].queryset = WorkTimeCategory.objects.filter(
            Q(pk__in=available) | Q(pk=self.instance.work_category_id)
        ).distinct()
        self.fields["work_category"].empty_label = ""
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
