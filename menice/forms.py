from django import forms
from django.db import connections
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from core.models import OrganizationalUnit

from .models import Menica, UlaznaMenica


PARTNER_SELECT_EMPTY = ""


def get_partner_choices():
    choices = [(PARTNER_SELECT_EMPTY, "Rucni unos / bez izbora partnera")]
    partner_lookup = {}
    try:
        with connections["server_db"].cursor() as cursor:
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
    datum_ugovora = localized_date_field(label="Datum ugovora", required=False)
    oj = forms.ChoiceField(
        label="OJ",
        required=False,
        choices=[],
        widget=Select2Widget(attrs={"class": "select2-method"}),
    )
    interni_status = forms.TypedChoiceField(
        label="Status",
        choices=Menica.INTERNI_STATUS_CHOICES,
        coerce=int,
        required=True,
        widget=Select2Widget(attrs={"class": "select2-method"}),
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
            "fizicka_lokacija": Select2Widget(attrs={"class": "select2-method"}),
            "napomena": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "Bez izbora OJ")]
        choices.extend(
            (unit.code.strip(), f"{unit.code.strip()} - {unit.name}")
            for unit in OrganizationalUnit.objects.all().order_by("code")
        )
        current_oj = (self.instance.oj or "").strip() if self.instance else ""
        if current_oj and current_oj not in {value for value, _ in choices}:
            choices.append((current_oj, f"{current_oj} - postojeca vrednost"))
        self.fields["oj"].choices = choices


class UlaznaMenicaForm(forms.ModelForm):
    datum_prijema_menice = localized_date_field(label="Datum prijema menice", required=False)
    datum_ugovora = localized_date_field(label="Datum ugovora", required=False)
    ugovor_vazi_do = localized_date_field(label="Ugovor vazi do", required=False)
    sifra_centra = forms.ChoiceField(
        label="Sifra centra",
        required=False,
        choices=[],
        widget=Select2Widget(attrs={"class": "select2-method"}),
    )
    jedinica_vrednosti = forms.ChoiceField(
        label="Jedinica vrednosti",
        choices=UlaznaMenica.JEDINICA_VREDNOSTI_CHOICES,
        widget=Select2Widget(attrs={"class": "select2-method"}),
    )
    partner = forms.ChoiceField(
        label="Poslovni partner",
        required=False,
        choices=[(PARTNER_SELECT_EMPTY, "Rucni unos / bez izbora partnera")],
    )

    class Meta:
        model = UlaznaMenica
        exclude = ["created_at", "updated_at", "naziv_pravnog_lica"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices, self.partner_lookup = get_partner_choices()
        self.fields["partner"].choices = choices
        self.fields["partner"].widget.attrs.update({"class": "select2-method"})
        self.fields["sifra_poslovnog_partnera"].widget = forms.HiddenInput()

        field_order = ["partner"] + [name for name in self.fields if name != "partner"]
        field_order.remove("jedinica_vrednosti")
        amount_index = field_order.index("procenat_iznos")
        field_order.insert(amount_index, "jedinica_vrednosti")
        self.order_fields(field_order)

        if self.instance and self.instance.pk and self.instance.sifra_poslovnog_partnera:
            self.initial["partner"] = str(self.instance.sifra_poslovnog_partnera)

        centers = sorted(
            {
                center.strip()
                for center in OrganizationalUnit.objects.exclude(center__isnull=True).exclude(center="")
                .values_list("center", flat=True)
                if center.strip()
            }
        )
        center_choices = [("", "Bez izbora centra")] + [(center, center) for center in centers]
        current_center = (self.instance.sifra_centra or "").strip() if self.instance else ""
        if current_center and current_center not in {value for value, _ in center_choices}:
            center_choices.append((current_center, f"{current_center} - postojeca vrednost"))
        self.fields["sifra_centra"].choices = center_choices

    def clean(self):
        cleaned_data = super().clean()
        partner_key = cleaned_data.get("partner")
        partner_data = self.partner_lookup.get(partner_key)
        if partner_data:
            cleaned_data["sifra_poslovnog_partnera"] = partner_data["sifra_partnera"]
            self.instance.naziv_pravnog_lica = partner_data["naziv_duznika"]
        return cleaned_data
