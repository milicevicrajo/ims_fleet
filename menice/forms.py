from django import forms
from django.db import connections

from .models import Menica, UlaznaMenica


PARTNER_SELECT_EMPTY = ""


def get_partner_choices():
    choices = [(PARTNER_SELECT_EMPTY, "Rucni unos / bez izbora partnera")]
    partner_lookup = {}
    try:
        with connections["naplata_db"].cursor() as cursor:
            cursor.execute("""
                SELECT
                    sif_par,
                    LTRIM(RTRIM(naz_par)) AS naz_par,
                    LTRIM(RTRIM(mb)) AS mb,
                    LTRIM(RTRIM(pib)) AS pib
                FROM partneri
                WHERE naz_par IS NOT NULL
                ORDER BY LTRIM(RTRIM(naz_par))
            """)
            rows = cursor.fetchall()
    except Exception:
        return choices, partner_lookup

    for sif_par, naz_par, mb, pib in rows:
        if sif_par is None:
            continue
        key = str(int(sif_par)) if isinstance(sif_par, float) and sif_par.is_integer() else str(sif_par)
        partner_lookup[key] = {
            "sifra_partnera": int(float(sif_par)),
            "naziv_duznika": (naz_par or "").strip(),
            "maticni_broj_duznika": (mb or "").strip(),
            "poreski_broj_duznika": (pib or "").strip(),
        }
        label_parts = [key, partner_lookup[key]["naziv_duznika"]]
        if partner_lookup[key]["poreski_broj_duznika"]:
            label_parts.append(f"PIB {partner_lookup[key]['poreski_broj_duznika']}")
        choices.append((key, " - ".join(part for part in label_parts if part)))

    return choices, partner_lookup


class MenicaCreateForm(forms.ModelForm):
    partner = forms.ChoiceField(
        label="Poslovni partner",
        required=False,
        choices=[(PARTNER_SELECT_EMPTY, "Rucni unos / bez izbora partnera")],
    )

    class Meta:
        model = Menica
        exclude = ["tip", "created_at", "updated_at"]
        widgets = {
            "datum_izdavanja": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "datum_dospeca": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "datum_registracije": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "datum_ugovora": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "avalisti_detalji": forms.Textarea(attrs={"rows": 3}),
            "napomena": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices, self.partner_lookup = get_partner_choices()
        self.fields["partner"].choices = choices
        self.fields["partner"].widget.attrs.update({"class": "select2-method"})
        self.fields["sifra_partnera"].widget = forms.HiddenInput()

        field_order = ["partner"] + [name for name in self.fields if name != "partner"]
        self.order_fields(field_order)

    def clean(self):
        cleaned_data = super().clean()
        partner_key = cleaned_data.get("partner")
        partner_data = self.partner_lookup.get(partner_key)
        if partner_data:
            for field_name, value in partner_data.items():
                cleaned_data[field_name] = value
        return cleaned_data


class MenicaUpdateForm(forms.ModelForm):
    interni_status = forms.TypedChoiceField(
        label="Status",
        choices=Menica.INTERNI_STATUS_CHOICES,
        coerce=int,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Menica
        fields = [
            "broj_ugovora",
            "datum_ugovora",
            "oj",
            "fizicka_lokacija",
            "napomena",
            "interni_status",
        ]
        widgets = {
            "datum_ugovora": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "napomena": forms.Textarea(attrs={"rows": 3}),
        }


class UlaznaMenicaForm(forms.ModelForm):
    partner = forms.ChoiceField(
        label="Poslovni partner",
        required=False,
        choices=[(PARTNER_SELECT_EMPTY, "Rucni unos / bez izbora partnera")],
    )

    class Meta:
        model = UlaznaMenica
        exclude = ["created_at", "updated_at"]
        widgets = {
            "datum_prijema_menice": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "datum_ugovora": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "ugovor_vazi_do": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices, self.partner_lookup = get_partner_choices()
        self.fields["partner"].choices = choices
        self.fields["partner"].widget.attrs.update({"class": "select2-method"})
        self.fields["sifra_poslovnog_partnera"].widget = forms.HiddenInput()

        field_order = ["partner"] + [name for name in self.fields if name != "partner"]
        self.order_fields(field_order)

        if self.instance and self.instance.pk and self.instance.sifra_poslovnog_partnera:
            self.initial["partner"] = str(self.instance.sifra_poslovnog_partnera)

    def clean(self):
        cleaned_data = super().clean()
        partner_key = cleaned_data.get("partner")
        partner_data = self.partner_lookup.get(partner_key)
        if partner_data:
            cleaned_data["sifra_poslovnog_partnera"] = partner_data["sifra_partnera"]
            cleaned_data["naziv_pravnog_lica"] = partner_data["naziv_duznika"]
        return cleaned_data
