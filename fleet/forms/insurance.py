from django import forms

from ..models import DraftInsurance, Insurance


class InsuranceForm(forms.ModelForm):
    class Meta:
        model = Insurance
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


class DraftInsuranceForm(forms.ModelForm):
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
