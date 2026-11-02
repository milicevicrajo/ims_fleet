from calendar import monthrange
from datetime import date, datetime

from django import forms
from django.utils import timezone

from .services.source import PRVA_GODINA


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


def klase_polja(form):
    """Izgled polja kao u ostalim izveštajima Finansija: datum kroz Flatpickr (`js-date`), izbor kroz select2."""
    for field in form.fields.values():
        if isinstance(field, ReportDateField):
            field.widget.attrs["class"] = "form-control js-date"
        elif isinstance(field, forms.ChoiceField):
            field.widget.attrs["class"] = "form-select form-control select2-method"
        else:
            field.widget.attrs["class"] = "form-control"


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
        self.fields["year"].choices = [(y, y) for y in range(PRVA_GODINA, today.year + 1)]
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
    nivo = forms.ChoiceField(label="Nivo konta", required=False,
                             choices=[("", "Sledeći nivo (otvaranje po dubini)"), ("1", "Klasa"), ("2", "Grupa"),
                                      ("3", "Sintetika"), ("5", "Konto")])
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
        from finansije.access import centar_sifre, centri_sifara, na_registru, polje_centra

        mapa = centri_sifara() if na_registru() else None
        centers = {centar_sifre(j, mapa) for j in jobs} | {
            c or "" for c in entries.order_by().values_list(polje_centra(), flat=True).distinct()}
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
        if start and start < date(PRVA_GODINA, 1, 1):
            self.add_error("date_from", f"Podaci su dostupni od 01.01.{PRVA_GODINA}.")
        if start and end and start > end:
            raise forms.ValidationError("Početni datum mora biti pre krajnjeg datuma.")
        return data


class BrutoBilansForm(forms.Form):
    godina = forms.IntegerField(label="Godina", min_value=2000)
    datum_od = ReportDateField(label="Datum od")
    datum_do = ReportDateField(label="Datum do")
    oj_od = forms.IntegerField(label="OJ od", required=False, min_value=0)
    oj_do = forms.IntegerField(label="OJ do", required=False, min_value=0)
    konto_od = forms.RegexField(label="Od konta", regex=r"^\d{1,6}$", required=False,
                                error_messages={"invalid": "Konto ima do 6 cifara."})
    konto_do = forms.RegexField(label="Do konta", regex=r"^\d{1,6}$", required=False,
                                error_messages={"invalid": "Konto ima do 6 cifara."})
    nivo = forms.ChoiceField(label="Nivo", initial="konto")

    def __init__(self, *args, **kwargs):
        from .services.bruto_bilans import NIVOI

        super().__init__(*args, **kwargs)
        godina = timezone.localdate().year
        self.fields["godina"].initial = godina
        self.fields["datum_od"].initial = date(godina, 1, 1)
        self.fields["datum_do"].initial = date(godina, 12, 31)
        self.fields["nivo"].choices = NIVOI
        klase_polja(self)
        for naziv in ("oj_od", "oj_do", "konto_od", "konto_do"):
            self.fields[naziv].widget.attrs["placeholder"] = "sve"

    def clean(self):
        values = super().clean()
        godina, od, do = values.get("godina"), values.get("datum_od"), values.get("datum_do")
        if godina and od and do and (od > do or od.year != godina or do.year != godina):
            raise forms.ValidationError("Izaberite period unutar izabrane godine (datum od ne može biti posle datuma do).")
        return values


class BilansStanjaForm(forms.Form):
    na_dan = ReportDateField(label="Na dan")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["na_dan"].initial = timezone.localdate()
        klase_polja(self)


class BilansUspehaForm(forms.Form):
    datum_od = ReportDateField(label="Datum od")
    datum_do = ReportDateField(label="Datum do")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        danas = timezone.localdate()
        self.fields["datum_od"].initial = date(danas.year, 1, 1)
        self.fields["datum_do"].initial = danas
        klase_polja(self)

    def clean(self):
        values = super().clean()
        od, do = values.get("datum_od"), values.get("datum_do")
        if od and do and (od > do or od.year != do.year):
            raise forms.ValidationError("Izaberite period unutar jedne godine (datum od ne može biti posle datuma do).")
        return values


class NadzorniOdborForm(BilansUspehaForm):
    """Izveštaj za nadzorni odbor: period jedne godine, uporedo isti period prethodnih godina."""
    broj_godina = forms.IntegerField(label="Broj godina", min_value=1, max_value=6, initial=2)
    jedinica = forms.ChoiceField(label="Iznosi", required=False,
                                 choices=[("hiljade", "u hiljadama dinara"), ("dinari", "u dinarima")])

    def __init__(self, *args, jedinica="hiljade", **kwargs):
        super().__init__(*args, **kwargs)
        self.podrazumevana_jedinica = jedinica
        self.fields["jedinica"].initial = jedinica
        klase_polja(self)

    def clean_jedinica(self):
        return self.cleaned_data.get("jedinica") or self.podrazumevana_jedinica


class NadzorniGodinaForm(forms.Form):
    """Podešavanja izveštaja za nadzorni odbor za jednu godinu: broj zaposlenih i godišnji plan po poziciji."""
    broj_zaposlenih = forms.IntegerField(label="Broj zaposlenih (ostvareno)", min_value=0, required=False)
    plan_zaposlenih = forms.IntegerField(label="Planirani broj zaposlenih", min_value=0, required=False)

    def __init__(self, *args, pozicije=(), **kwargs):
        super().__init__(*args, **kwargs)
        for pozicija in pozicije:
            self.fields[f"plan_{pozicija.kod}"] = forms.DecimalField(
                label=pozicija.naziv, required=False, max_digits=14, decimal_places=2)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control form-control-sm text-end"


class NadzorniCentarForm(forms.Form):
    centar = forms.CharField(label="Centar", max_length=10, required=False)
    koeficijent = forms.DecimalField(label="Koeficijent (%)", min_value=0, max_value=100, max_digits=5,
                                     decimal_places=2, required=False)
    broj_zaposlenih = forms.IntegerField(label="Broj zaposlenih", min_value=0, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control form-control-sm"


class BaseNadzorniCentriFormSet(forms.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        vidjeni, zbir = set(), 0
        for forma in self.forms:
            centar = (forma.cleaned_data.get("centar") or "").strip()
            if not centar:
                continue
            if centar in vidjeni:
                raise forms.ValidationError(f"Centar {centar} je upisan dvaput.")
            vidjeni.add(centar)
            zbir += forma.cleaned_data.get("koeficijent") or 0
        if vidjeni and zbir != 100:
            raise forms.ValidationError(f"Zbir koeficijenata je {zbir}%, a mora biti 100% — inače deo zajedničkih "
                                        "prihoda i troškova ostaje neraspoređen.")


NadzorniCentriFormSet = forms.formset_factory(NadzorniCentarForm, formset=BaseNadzorniCentriFormSet, extra=3)
