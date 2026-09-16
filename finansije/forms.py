from datetime import date

from django import forms
from django.utils import timezone


GROUPS = [("center", "Po centrima / OJ"), ("job", "Po šiframa posla"), ("account", "Po kontima"), ("month", "Po mesecima")]
KINDS = [("pnl", "Prihodi i rashodi"), ("revenue", "Samo prihodi"), ("expense", "Samo rashodi")]


class ReportFilters(forms.Form):
    date_from = forms.DateField(label="Datum knjiženja od", widget=forms.DateInput(attrs={"type": "date"}), input_formats=["%Y-%m-%d"])
    date_to = forms.DateField(label="Datum knjiženja do", widget=forms.DateInput(attrs={"type": "date"}), input_formats=["%Y-%m-%d"])
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
        self.fields["center"].choices = [("", "Svi dostupni centri")] + [(c or "__none__", c or "Neraspoređeno") for c in sorted(centers)]
        job_choices = {j.code: j.name for j in jobs}
        for code, name in entries.order_by().values_list("job_code", "job_name").distinct():
            job_choices.setdefault(code, name)
        self.fields["job"].choices = [("", "Sve dostupne šifre")] + [(code or "__none__", f"{code} — {name}" if code else "Bez šifre posla") for code, name in sorted(job_choices.items())]
        self.fields["unit"].choices = [("", "Sve OJ knjiženja")] + [(str(code), f"{code} — {name}") for code, name in entries.order_by("organizational_unit").values_list("organizational_unit", "organizational_unit_name").distinct()]
        if ledger:
            self.fields["kind"].choices = [*KINDS, ("all", "Sva knjiženja")]
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-check-input" if isinstance(field, forms.BooleanField) else "form-select" if isinstance(field, forms.ChoiceField) else "form-control"

    def clean(self):
        data = super().clean()
        start, end = data.get("date_from"), data.get("date_to")
        if start and start < date(2025, 1, 1):
            self.add_error("date_from", "Podaci su dostupni od 01.01.2025.")
        if start and end and start > end:
            raise forms.ValidationError("Početni datum mora biti pre krajnjeg datuma.")
        return data
