from django import forms
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field

from ..models import (
    DraftServiceTransaction,
    Kvar,
    Requisition,
    Service,
    ServiceTransaction,
    ServiceType,
    Vehicle,
)
from .layout import FieldsetMixin

# Isti raspored i objasnjenja za konacnu i za nedovrsenu servisnu stavku.
SERVICE_FIELDSETS = (
    ('Vozilo i datum', 'Na koje vozilo se trošak odnosi i kada je nastao.',
     ('vehicle', 'datum', 'kilometraza')),
    ('Dobavljač koji potražuje', 'Ko je pružio uslugu i po kom kontu se knjiži.',
     ('sif_par_pl', 'naz_par_pl', 'knt_pl', 'potrazuje')),
    ('Protivstavka', 'Druga strana knjiženja. Popunjava se kada knjiženje ima obe strane.',
     ('sif_par_npl', 'knt_npl', 'duguje', 'konto_vozila')),
    ('Nalog knjiženja', 'Odakle stavka dolazi u knjigovodstvu.',
     ('god', 'sif_vrs', 'br_naloga', 'vez_dok')),
    ('Razvrstavanje', 'Podaci po kojima se trošak grupiše u izveštajima.',
     ('popravka_kategorija', 'nije_garaza', 'kom', 'napomena')),
)

SERVICE_HELP = {
    'datum': 'Datum stavke u knjigovodstvu. Po njemu trošak ulazi u izabrani period.',
    'kilometraza': 'Stanje brojača u trenutku servisa, ako je poznato.',
    'sif_par_pl': 'Šifra partnera koji POTRAŽUJE — dobavljača usluge ili dela.',
    'naz_par_pl': 'Naziv tog partnera.',
    'knt_pl': 'Konto na koji se knjiži potraživanje dobavljača.',
    'potrazuje': 'Iznos koji dobavljač potražuje. Ovo je trošak vozila.',
    'sif_par_npl': 'Šifra partnera na protivstavci, ako postoji.',
    'knt_npl': 'Konto protivstavke.',
    'duguje': 'Iznos na strani duguje. Kod redovnog troška je najčešće prazno.',
    'konto_vozila': 'Konto na kojem se vodi samo vozilo.',
    'god': 'Poslovna godina knjiženja.',
    'sif_vrs': 'Šifra vrste naloga iz knjigovodstva (na primer EUF, UF, KA).',
    'br_naloga': 'Broj naloga za knjiženje.',
    'vez_dok': 'Broj dokumenta na koji se stavka poziva — faktura ili radni nalog.',
    'popravka_kategorija': 'Vrsta zahvata. Po njoj se trošak grupiše u strukturi održavanja.',
    'kom': 'Komada, odnosno kratak opis stavke. Polje prima i duži tekst.',
    'napomena': 'Slobodna napomena za ovu stavku.',
}


class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = "__all__"


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = "__all__"


class ServiceTransactionForm(FieldsetMixin, forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    datum = localized_date_field(label="Datum stavke")

    fieldsets = SERVICE_FIELDSETS

    class Meta:
        model = ServiceTransaction
        fields = "__all__"
        help_texts = SERVICE_HELP
        labels = {'nije_garaza': 'Servis van garaže IMS-a'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.datum:
            self.initial["datum"] = self.instance.datum.strftime("%d.%m.%Y")


class DraftServiceTransactionForm(FieldsetMixin, forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    datum = localized_date_field(label="Datum stavke")

    fieldsets = SERVICE_FIELDSETS

    class Meta:
        model = DraftServiceTransaction
        fields = "__all__"
        help_texts = SERVICE_HELP
        # Isti naziv kao u ServiceTransactionForm. Ranije je ovde stajalo
        # "Da li ovaj servis pripada garaži?", sto je SUPROTNO znacenje polja.
        labels = {'nije_garaza': 'Servis van garaže IMS-a'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.datum:
            self.initial["datum"] = self.instance.datum.strftime("%d.%m.%Y")

        if not self.initial.get("sif_vrs") and not getattr(self.instance, "sif_vrs", None):
            self.initial["sif_vrs"] = "EUF"

        for field_name, field in self.fields.items():
            field.required = False


class ServiceFixingFilterForm(forms.Form):
    datum_od = localized_date_field(
        required=False,
        label="Datum od",
    )
    datum_do = localized_date_field(
        required=False,
        label="Datum do",
    )
    partner = forms.CharField(
        required=False,
        label="Naziv partnera",
    )
    nije_garaza = forms.BooleanField(
        required=False,
        label="Samo servisi van garaže",
    )


class RequisitionForm(FieldsetMixin, forms.ModelForm):
    fieldsets = (
        ('Vozilo i datum', 'Na koje vozilo se trebovanje odnosi i kada je izdato.',
         ('vehicle', 'datum_trebovanja', 'mesec_unosa', 'kilometraza')),
        ('Artikal', 'Šta je uzeto iz magacina.',
         ('sif_vrsart', 'sif_art', 'naz_art', 'kol')),
        ('Iznos', 'Vrednost nabavke je količina puta jedinična cena.',
         ('cena', 'vrednost_nab')),
        ('Dokument', 'Odakle trebovanje dolazi u evidenciji.',
         ('sif_pred', 'god', 'br_dok', 'stavka')),
        ('Razvrstavanje', None,
         ('popravka_kategorija', 'kvar', 'nije_garaza', 'napomena')),
    )

    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    kvar = forms.ModelChoiceField(
        queryset=Kvar.objects.filter(van_ims=False),
        required=False,
        widget=Select2Widget(attrs={"class": "select2-method", "data-placeholder": "Izaberi IMS kvar"}),
        label="Kvar (IMS)",
    )
    datum_trebovanja = localized_date_field(label="Datum trebovanja")

    class Meta:
        model = Requisition
        fields = "__all__"
        labels = {'nije_garaza': 'Servis van garaže IMS-a'}
        help_texts = {
            'mesec_unosa': 'Obračunski mesec (1–12) na koji se trebovanje odnosi. Ne mora biti mesec unosa u sistem.',
            'sif_pred': 'Šifra preduzeća iz izvorne evidencije.',
            'god': 'Poslovna godina dokumenta.',
            'br_dok': 'Broj dokumenta trebovanja.',
            'stavka': 'Redni broj stavke unutar dokumenta.',
            'sif_vrsart': 'Šifra vrste artikla — na primer rezervni deo ili gorivo.',
            'sif_art': 'Šifra artikla iz magacinskog šifarnika.',
            'naz_art': 'Naziv artikla.',
            'kol': 'Izdata količina.',
            'cena': 'Jedinična cena artikla.',
            'vrednost_nab': 'Ukupna vrednost = količina × jedinična cena. Ovaj iznos ulazi u trošak vozila.',
            'kilometraza': 'Stanje brojača pri trebovanju, ako je poznato.',
            'popravka_kategorija': 'Vrsta zahvata, radi grupisanja u strukturi održavanja.',
            'kvar': 'Povezani kvar iz garaže IMS-a, ako postoji.',
            'napomena': 'Slobodna napomena.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.datum_trebovanja:
            self.initial["datum_trebovanja"] = self.instance.datum_trebovanja.strftime("%d.%m.%Y")
