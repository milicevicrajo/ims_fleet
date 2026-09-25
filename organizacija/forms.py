"""Forma nove dodele uloge sa obuhvatom (ekran dodela, plan prelaska na registar, korak 3)."""

from django import forms
from django.utils import timezone

from organizacija.models import OrgNode, OrgNodeVersion
from organizacija.services import dodele as dodele_service


class DodelaForm(forms.Form):
    uloga = forms.ModelChoiceField(queryset=None, label="Uloga",
                                   widget=forms.Select(attrs={"class": "form-select"}))
    obuhvat = forms.ChoiceField(label="Obuhvat", widget=forms.Select(attrs={"class": "form-select select2-method"}))
    vazi_od = forms.DateField(label="Važi od", widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"))
    vazi_do = forms.DateField(label="Važi do (isključivo)", required=False,
                              widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"))
    napomena = forms.CharField(label="Napomena", required=False, max_length=300,
                               widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, korisnik, **kwargs):
        super().__init__(*args, **kwargs)
        self.korisnik = korisnik
        # Samo uloge koje korisnik vec ima: dozvole i dalje daju stare uloge, dodela im dodaje obuhvat.
        self.fields["uloga"].queryset = korisnik.roles.filter(is_active=True).order_by("name")
        self.fields["obuhvat"].choices = [("", "— izaberite —")] + dodele_service.izbor_obuhvata()
        self.fields["vazi_od"].initial = timezone.localdate()

    def clean(self):
        data = super().clean()
        obuhvat = data.get("obuhvat")
        data["cela_firma"] = obuhvat == "firma"
        data["cvor_id"] = None
        if obuhvat and not data["cela_firma"]:
            cvor = int(obuhvat)
            verzija = OrgNodeVersion.objects.filter(node_id=cvor, valid_to__isnull=True).first()
            if verzija is None or (verzija.node.level == OrgNode.LEVEL_JOB and not verzija.is_active):
                raise forms.ValidationError("Izabrani obuhvat nije aktivan čvor registra.")
            data["cvor_id"] = cvor
        od, do = data.get("vazi_od"), data.get("vazi_do")
        if od and do and do <= od:
            self.add_error("vazi_do", "Kraj mora biti posle početka.")
        if data.get("uloga") and obuhvat and od and not self.errors and dodele_service.preklapanje(
                self.korisnik, data["uloga"], data["cvor_id"], data["cela_firma"], od, do):
            raise forms.ValidationError("Korisnik već ima tu ulogu sa istim obuhvatom u tom periodu.")
        return data
