from django import forms

from .models import DisciplinskiPostupak, Postupak, PromenaPostupka, TokPostupka, centar_zaposlenog


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

# Kolone liste disciplinskih postupaka. Isti oblik kao COLUMNS_BY_TIP,
# pa liste i izvestaji koriste isti sablon.
DISCIPLINSKI_COLUMNS = [
    ('zaposleni', 'Zaposleni'),
    ('centar', 'Centar'),
    ('datum_podnosenja', 'Datum podnošenja zahteva'),
    ('podnosilac', 'Podnosilac'),
    ('mera_datum', 'Datum disciplinske mere'),
    ('mera_opis', 'Disciplinska mera'),
]

DATE_ATTRS = {'class': 'form-control js-date', 'autocomplete': 'off'}
DATE_INPUT_FORMATS = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']


def _date_field(label=None, required=False):
    return forms.DateField(
        required=required,
        label=label,
        widget=forms.DateInput(format='%d.%m.%Y', attrs=DATE_ATTRS),
        input_formats=DATE_INPUT_FORMATS,
    )


class PostupakForm(forms.ModelForm):
    """Dinamička forma - prikazuje samo polja relevantna za dati tip."""

    datum_pokretanja = _date_field()
    datum_podnosenja_tuzbe = _date_field()
    datum_otvaranja_stecaja = _date_field()

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
    datum = _date_field(required=True)

    class Meta:
        model = PromenaPostupka
        fields = ['datum', 'promena']


def _employee_queryset(keep_ids=()):
    """Aktivni zaposleni, uz one koji su vec upisani na postupku."""
    from django.db.models import Q
    from hr.models import Employee

    condition = Q(is_active=True)
    kept = [pk for pk in keep_ids if pk]
    if kept:
        condition |= Q(pk__in=kept)
    return Employee.objects.filter(condition).order_by('last_name', 'first_name')


class DisciplinskiPostupakForm(forms.ModelForm):
    datum_podnosenja = _date_field(required=True)

    class Meta:
        model = DisciplinskiPostupak
        fields = ['zaposleni', 'centar', 'datum_podnosenja', 'podnosilac', 'arhivirano']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Zaposleni koji vise nije aktivan mora ostati vidljiv na svom postupku.
        keep = (self.instance.zaposleni_id, self.instance.podnosilac_id) if self.instance.pk else ()
        for name in ('zaposleni', 'podnosilac'):
            self.fields[name].queryset = _employee_queryset(keep)
            self.fields[name].widget.attrs['class'] = 'form-select select2-method'
        self.fields['centar'].required = False
        self.fields['centar'].help_text = 'Ostavi prazno da se preuzme iz organizacione jedinice zaposlenog.'

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('centar') and cleaned.get('zaposleni'):
            cleaned['centar'] = centar_zaposlenog(cleaned['zaposleni'])
        return cleaned


class TokPostupkaForm(forms.ModelForm):
    datum = _date_field(required=True)

    class Meta:
        model = TokPostupka
        fields = ['datum', 'opis']


class DisciplinskaMeraForm(forms.ModelForm):
    """Unos mere zatvara postupak; brisanje datuma ga vraca u rad."""

    mera_datum = _date_field(label='Datum disciplinske mere', required=True)

    class Meta:
        model = DisciplinskiPostupak
        fields = ['mera_datum', 'mera_opis']
        labels = {'mera_opis': 'Disciplinska mera'}
        widgets = {'mera_opis': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})}

    def clean_mera_opis(self):
        opis = (self.cleaned_data.get('mera_opis') or '').strip()
        if not opis:
            raise forms.ValidationError('Upišite koja je mera izrečena.')
        return opis
