from django import forms
from .models import Postupak, PromenaPostupka


# Polja po tipu postupka
FIELDS_BY_TIP = {
    'tuzeni': [
        'sud', 'broj_predmeta', 'izvrsiteljski_broj',
        'sifra_partnera', 'naziv_partnera',
        'datum_pokretanja', 'predmet_spora', 'osnovni_dug', 'arhivirano',
    ],
    'tuzili': [
        'sud', 'broj_predmeta',
        'tuzilac', 'valuta', 'vrednost_spora',
        'datum_podnosenja_tuzbe', 'arhivirano',
    ],
    'stecaj': [
        'sud', 'broj_predmeta', 'vece',
        'sifra_partnera', 'naziv_partnera',
        'valuta', 'osnovni_dug', 'kamata', 'troskovi', 'ukupan_dug',
        'datum_otvaranja_stecaja', 'prijava_potrazivanja', 'arhivirano',
    ],
    'uppr': [
        'sud', 'broj_predmeta', 'novi_broj',
        'sifra_partnera', 'naziv_partnera',
        'pib', 'valuta', 'vrednost_spora', 'arhivirano',
    ],
}

# Kolone prikazane u tabeli liste po tipu
COLUMNS_BY_TIP = {
    'tuzeni': [
        ('sud', 'Sud'),
        ('broj_predmeta', 'Sudski broj'),
        ('izvrsiteljski_broj', 'Izvršiteljski broj'),
        ('naziv_partnera', 'Naziv partnera'),
        ('sifra_partnera', 'Šifra partnera'),
        ('datum_pokretanja', 'Datum pokretanja'),
        ('predmet_spora', 'Predmet spora'),
        ('osnovni_dug', 'Osnovni dug'),
    ],
    'tuzili': [
        ('sud', 'Sud'),
        ('broj_predmeta', 'Broj predmeta'),
        ('tuzilac', 'Tužilac'),
        ('valuta', 'Valuta'),
        ('vrednost_spora', 'Vrednost spora'),
        ('datum_podnosenja_tuzbe', 'Datum podnošenja tužbe'),
    ],
    'stecaj': [
        ('sud', 'Sud'),
        ('broj_predmeta', 'Broj predmeta'),
        ('vece', 'Veće'),
        ('naziv_partnera', 'Naziv partnera'),
        ('sifra_partnera', 'Šifra partnera'),
        ('valuta', 'Valuta'),
        ('osnovni_dug', 'Osnovni dug'),
        ('kamata', 'Kamata'),
        ('troskovi', 'Troškovi'),
        ('ukupan_dug', 'Ukupan dug'),
        ('datum_otvaranja_stecaja', 'Datum otvaranja'),
        ('prijava_potrazivanja', 'Prijava potraživanja'),
    ],
    'uppr': [
        ('sud', 'Sud'),
        ('broj_predmeta', 'Broj predmeta'),
        ('novi_broj', 'Novi broj'),
        ('naziv_partnera', 'Dužnik / Tuženi'),
        ('sifra_partnera', 'Šifra partnera'),
        ('pib', 'PIB'),
        ('valuta', 'Valuta'),
        ('vrednost_spora', 'Vrednost'),
    ],
}


DATE_ATTRS = {'class': 'form-control js-date', 'autocomplete': 'off'}


class PostupakForm(forms.ModelForm):
    """Dinamička forma - prikazuje samo polja relevantna za dati tip."""

    datum_pokretanja = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d.%m.%Y', attrs=DATE_ATTRS),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
    )
    datum_podnosenja_tuzbe = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d.%m.%Y', attrs=DATE_ATTRS),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
    )
    datum_otvaranja_stecaja = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d.%m.%Y', attrs=DATE_ATTRS),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
    )

    class Meta:
        model = Postupak
        fields = '__all__'
        exclude = ['tip', 'created_at', 'updated_at', 'created_by']

    def __init__(self, *args, tip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tip = tip or (self.instance.tip if self.instance.pk else 'tuzeni')
        allowed = FIELDS_BY_TIP.get(self.tip, [])
        for field_name in list(self.fields):
            if field_name not in allowed:
                del self.fields[field_name]


class PromenaPostupkaForm(forms.ModelForm):
    datum = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs=DATE_ATTRS),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
    )

    class Meta:
        model = PromenaPostupka
        fields = ['datum', 'promena']
