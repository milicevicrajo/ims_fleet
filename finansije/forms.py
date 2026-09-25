from calendar import monthrange
from datetime import date, datetime

from django import forms
from django.utils import timezone


GROUPS = [("center", "Po centrima / OJ"), ("job", "Po šiframa posla"), ("account", "Po kontima"), ("month", "Po mesecima")]
KINDS = [("pnl", "Prihodi i rashodi"), ("revenue", "Samo prihodi"), ("expense", "Samo rashodi")]
DATE_FORMATS = ["%d.%m.%Y", "%d.%m.%Y.", "%Y-%m-%d"]


class ReportDateInput(forms.DateInput):
    """Use the shared Flatpickr display format, including for ISO query links."""
    def __init__(self):
        super().__init__(format="%d.%m.%Y", attrs={"placeholder": "DD.MM.GGGG", "autocomplete": "off"})

    def format_value(self, value):
        if isinstance(value, str):
            for pattern in DATE_FORMATS:
                try:
                    value = datetime.strptime(value.strip(), pattern).date()
                    break
                except ValueError:
                    continue
        return super().format_value(value)


class ReportDateField(forms.DateField):
    def __init__(self, **kwargs):
        super().__init__(widget=ReportDateInput(), input_formats=DATE_FORMATS,
                         error_messages={"invalid": "Unesite datum u formatu DD.MM.GGGG.", "required": "Unesite datum."}, **kwargs)


class SyncForm(forms.Form):
    scope = forms.ChoiceField(label="Obuhvat sinhronizacije", initial="current",
                             widget=forms.Select(attrs={"class": "form-select form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_year = timezone.localdate().year
        self.fields["scope"].choices = [
            ("current", f"Tekuća godina ({self.current_year})"),
            ("all", f"Sve godine (2025–{self.current_year})"),
        ]

    def sync_years(self):
        return {"year_from": self.current_year if self.cleaned_data["scope"] == "current" else 2025,
                "year_to": self.current_year}


class JobMonthForm(forms.Form):
    job = forms.ChoiceField(label="Šifra posla", required=False)
    year = forms.TypedChoiceField(label="Godina", coerce=int)
    month = forms.TypedChoiceField(label="Mesec", coerce=int, required=False, empty_value=None, choices=[("", "Cela godina")] + [
        (i, name) for i, name in enumerate([
            "Januar", "Februar", "Mart", "April", "Maj", "Jun", "Jul", "Avgust",
            "Septembar", "Oktobar", "Novembar", "Decembar",
        ], 1)
    ])

    def __init__(self, data, *, choices):
        values = data.copy()
        today = timezone.localdate()
        values.setdefault("year", str(today.year))
        values.setdefault("month", str(today.month))
        super().__init__(values)
        self.fields["job"].choices = [("", "Izaberite šifru posla")] + choices
        self.fields["year"].choices = [(y, y) for y in range(2025, today.year + 1)]
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select form-control select2-method"

    def clean(self):
        data = super().clean()
        if "year" in data and "month" in data:
            year, month = data["year"], data["month"]
            data["date_from"] = date(year, month or 1, 1)
            data["date_to"] = date(year, month, monthrange(year, month)[1]) if month else date(year, 12, 31)
        return data


class ReportFilters(forms.Form):
    date_from = ReportDateField(label="Datum knjiženja od")
    date_to = ReportDateField(label="Datum knjiženja do")
    center = forms.ChoiceField(label="Centar / OJ", required=False)
    job = forms.ChoiceField(label="Šifra posla", required=False)
    unit = forms.ChoiceField(label="OJ knjiženja", required=False)
    account = forms.RegexField(label="Konto ili početak konta", regex=r"^[0-9]{1,6}$", max_length=6, required=False)
    account_exact = forms.BooleanField(label="Tačno konto", required=False)
    kind = forms.ChoiceField(label="Vrsta knjiženja", choices=KINDS)
    group = forms.ChoiceField(label="Grupisanje", choices=GROUPS)
    include_empty = forms.BooleanField(label="Uključi šifre bez prometa", required=False)

    def __init__(self, data, *, jobs, entries, ledger=False):
        values = data.copy()
        today = timezone.localdate()
        for key, value in {"date_from": date(today.year, 1, 1).isoformat(), "date_to": today.isoformat(), "kind": "pnl", "group": "center"}.items():
            if key not in values:
                values[key] = value
        super().__init__(values)
        centers = set(jobs.values_list("center", flat=True)) | set(entries.order_by().values_list("center", flat=True).distinct())
        from fleet.support.registar import Registar

        registar = Registar()
        self.fields["center"].choices = [("", "Svi dostupni centri")] + [
            (c or "__none__", registar.oznaka_centra(c) if c else "Neraspoređeno") for c in sorted(centers)]
        job_choices = {j.code: j.name for j in jobs}
        for code, name in entries.order_by().values_list("job_code", "job_name").distinct():
            job_choices.setdefault(code, name)
        # Neaktivne sifre se ne nude (odluka 25.09.2026.); izabrana vrednost ostaje.
        izabrana = values.get("job") or ""
        job_choices = {code: name for code, name in job_choices.items()
                       if not code or code == izabrana or registar.aktivna_sifra(code)}
        self.fields["job"].choices = [("", "Sve dostupne šifre")] + [(code or "__none__", f"{code} — {name}" if code else "Bez šifre posla") for code, name in sorted(job_choices.items())]
        self.fields["unit"].choices = [("", "Sve OJ knjiženja")] + [(str(code), f"{code} — {name}") for code, name in entries.order_by("organizational_unit").values_list("organizational_unit", "organizational_unit_name").distinct()]
        if ledger:
            self.fields["kind"].choices = [*KINDS, ("all", "Sva knjiženja")]
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-check-input" if isinstance(field, forms.BooleanField) else "form-select form-control select2-method" if isinstance(field, forms.ChoiceField) else "form-control"
            if isinstance(field, ReportDateField):
                field.widget.attrs["class"] += " js-date"
        self.fields["account"].widget.attrs.update(placeholder="npr. 5 ili 51200", inputmode="numeric")
        for name in ("account_exact", "include_empty"):
            self.fields[name].widget.attrs["role"] = "switch"

    def clean(self):
        data = super().clean()
        start, end = data.get("date_from"), data.get("date_to")
        if start and start < date(2025, 1, 1):
            self.add_error("date_from", "Podaci su dostupni od 01.01.2025.")
        if start and end and start > end:
            raise forms.ValidationError("Početni datum mora biti pre krajnjeg datuma.")
        return data
