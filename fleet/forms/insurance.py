from django import forms

from ..models import DraftInsurance, Insurance
from .layout import FieldsetMixin

# Zajednicko za obe forme naknada: knjigovodstveni pojmovi koje korisnik ne mora znati.
RECOVERY_FIELDSETS = (
    ('Vozilo i namena', 'Da li se ova naknada uopšte odnosi na vozilo.', ('vehicle', 'kola')),
    ('Nalog knjiženja', 'Odakle stavka dolazi u knjigovodstvu.',
     ('god', 'sif_vrs', 'br_naloga', 'stavka', 'oj')),
    ('Dokument i iznos', None, ('datum', 'vez_dok', 'knt', 'potrazuje')),
)

RECOVERY_HELP = {
    "kola": "Da — naknada se odnosi na ovo vozilo i ulazi u pregled troškova. Ne — ne ulazi.",
    "god": "Poslovna godina knjiženja.",
    "sif_vrs": "Šifra vrste naloga iz knjigovodstva (na primer IF, ON, KA).",
    "br_naloga": "Broj naloga za knjiženje.",
    "stavka": "Redni broj stavke unutar naloga.",
    "oj": "Organizaciona jedinica na koju je stavka proknjižena.",
    "knt": "Konto na koji je stavka proknjižena.",
    "datum": "Datum evidencije stavke. Naknada se prikazuje po ovom datumu, a može se odnositi na raniju štetu.",
    "vez_dok": "Broj dokumenta na koji se stavka poziva (faktura, zapisnik).",
    "potrazuje": "Iznos naknade koji je odobren u korist IMS-a.",
}


class InsuranceForm(FieldsetMixin, forms.ModelForm):
    fieldsets = RECOVERY_FIELDSETS

    class Meta:
        model = Insurance
        help_texts = RECOVERY_HELP
        fields = [
            "vehicle",
            "god",
            "sif_vrs",
            "br_naloga",
            "stavka",
            "oj",
            "knt",
            "datum",
            "vez_dok",
            "potrazuje",
            "kola",
        ]


class DraftInsuranceForm(FieldsetMixin, forms.ModelForm):
    fieldsets = RECOVERY_FIELDSETS

    KOLO_CHOICES = [
        ("", "---------"),
        ("True", "Da"),
        ("False", "Ne"),
    ]

    kola = forms.ChoiceField(
        choices=KOLO_CHOICES,
        required=False,
        label="Odnosi se na auto",
    )

    class Meta:
        model = DraftInsurance
        help_texts = RECOVERY_HELP
        fields = [
            "vehicle",
            "god",
            "sif_vrs",
            "br_naloga",
            "stavka",
            "oj",
            "knt",
            "datum",
            "vez_dok",
            "potrazuje",
            "kola",
        ]

    def clean_kola(self):
        value = self.cleaned_data["kola"]
        if value == "True":
            return True
        if value == "False":
            return False
        return None
