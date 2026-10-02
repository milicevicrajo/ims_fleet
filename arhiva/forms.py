from django import forms
from django.utils import timezone

from arhiva import oj
from arhiva.models import Kategorija, Predmet, Smer

DATUM = {"type": "date", "class": "form-control"}


def izbor_kategorija():
    kategorije = (Kategorija.objects.filter(verzija__aktivna=True, aktivna=True).select_related("grupa")
                  .order_by("redni_broj"))
    return [("", "— kategorija se može izabrati i pri završetku predmeta —")] + [
        (str(k.pk), f"{k.redni_broj}. {k.naziv[:90]} · {k.rok_tekst}") for k in kategorije]


class PisarnicaForm(forms.Form):
    """Brzi unos u delovodnik. Broj daje servis; forma samo prikuplja podatke."""

    smer = forms.ChoiceField(choices=Smer.choices, initial=Smer.ULAZNI, widget=forms.RadioSelect, label="Pošta")
    datum_zavodjenja = forms.DateField(label="Datum zavođenja", widget=forms.DateInput(attrs=DATUM, format="%Y-%m-%d"))
    naslov = forms.CharField(max_length=500, label="Predmet",
                             widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True, "autocomplete": "off",
                                                           "placeholder": "Kratak sadržaj akta"}))
    korespondent = forms.CharField(max_length=255, required=False, label="Pošiljalac / primalac",
                                   widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off",
                                                                 "placeholder": "Ime i prezime ili naziv"}))
    mesto = forms.CharField(max_length=100, required=False, label="Mesto",
                            widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    broj_akta_posiljaoca = forms.CharField(max_length=100, required=False, label="Broj akta pošiljaoca",
                                           widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    datum_akta_posiljaoca = forms.DateField(required=False, label="Datum akta pošiljaoca",
                                            widget=forms.DateInput(attrs=DATUM, format="%Y-%m-%d"))
    glavna_oj = forms.ChoiceField(label="Organizaciona jedinica", widget=forms.Select(attrs={"class": "form-select select2-method"}))
    kategorija = forms.ChoiceField(required=False, label="Kategorija (rok čuvanja)",
                                   widget=forms.Select(attrs={"class": "form-select select2-method"}))
    napomena = forms.CharField(required=False, label="Napomena",
                               widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["glavna_oj"].choices = [("", "— izaberite centar ili OJ —")] + oj.izbor()
        self.fields["kategorija"].choices = izbor_kategorija()
        self.initial.setdefault("datum_zavodjenja", timezone.localdate())

    def clean(self):
        from organizacija.models import OrgNode

        data = super().clean()
        if data.get("glavna_oj"):
            data["glavna_oj"] = OrgNode.objects.get(pk=data["glavna_oj"])
        data["kategorija"] = Kategorija.objects.filter(pk=data["kategorija"]).first() if data.get("kategorija") else None
        if data.get("smer") == Smer.ULAZNI and not data.get("korespondent"):
            self.add_error("korespondent", "Za ulaznu poštu unesite pošiljaoca.")
        return data


class AktForm(forms.Form):
    datum = forms.DateField(label="Datum", widget=forms.DateInput(attrs=DATUM, format="%Y-%m-%d"))
    opis = forms.CharField(max_length=500, label="Opis akta",
                           widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "npr. Odgovor na dopis"}))
    smer = forms.ChoiceField(choices=Smer.choices, initial=Smer.IZLAZNI, label="Smer",
                             widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial.setdefault("datum", timezone.localdate())


class StornoForm(forms.Form):
    razlog = forms.CharField(label="Razlog storna", widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))


class FilterDelovodnikaForm(forms.Form):
    godina = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    smer = forms.ChoiceField(required=False, choices=[("", "Svi smerovi")] + list(Smer.choices),
                             widget=forms.Select(attrs={"class": "form-select"}))
    status = forms.ChoiceField(required=False, choices=[("", "Svi statusi")] + list(Predmet.Status.choices),
                               widget=forms.Select(attrs={"class": "form-select"}))
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "class": "form-control", "placeholder": "Broj, predmet, pošiljalac ili primalac"}))
