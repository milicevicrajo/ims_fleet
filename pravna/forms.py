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
    ('datum_podnosenja', 'Datum'),
    ('podnosilac', 'Podnosilac'),
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
    datum_podnosenja = _date_field(label='Datum', required=True)
    centar = forms.ChoiceField(required=False, label='Centar')

    class Meta:
        model = DisciplinskiPostupak
        fields = ['zaposleni', 'centar', 'datum_podnosenja', 'podnosilac']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Zaposleni koji vise nije aktivan mora ostati vidljiv na svom postupku.
        keep = (self.instance.zaposleni_id, self.instance.podnosilac_id) if self.instance.pk else ()
        for name in ('zaposleni', 'podnosilac'):
            self.fields[name].queryset = _employee_queryset(keep)
            self.fields[name].widget.attrs['class'] = 'form-select select2-method'
        from fleet.services.employee_user_profiles import available_centers, infer_center
        from core.models import OrganizationalUnit
        centers = available_centers()
        registry = {str(code).strip(): str(center or '').strip()
                    for code, center in OrganizationalUnit.objects.values_list('code', 'center')}
        self.employee_centers = {str(e.pk): registry.get(str(e.org_unit_code or e.department_code or '').strip())
            or infer_center(e.org_unit_code or e.department_code, centers=centers)[0]
            for e in self.fields['zaposleni'].queryset}
        if self.instance.centar and self.instance.centar.strip() not in centers:
            centers.append(self.instance.centar.strip())
        self.fields['centar'].choices = [('', 'Preuzmi prema zaposlenom')] + [(c, f'Centar {c}') for c in centers]
        self.fields['centar'].help_text = 'Centar se bira automatski prema zaposlenom. Po potrebi izaberite drugi.'
        if self.instance.pk:
            self.initial['centar'] = self.instance.centar.strip()

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
    """Zatvaranje zahteva jednu od mera iz člana 77 dostavljenog pravilnika."""

    mera_datum = _date_field(label='Datum zatvaranja', required=True)
    mera_vrsta = forms.ChoiceField(label='Izrečena mera', choices=DisciplinskiPostupak.Mera.choices,
        required=True, widget=forms.RadioSelect(attrs={'class': 'legal-measure-options'}))

    class Meta:
        model = DisciplinskiPostupak
        fields = ['mera_vrsta', 'mera_datum']

    def clean_mera_datum(self):
        datum = self.cleaned_data['mera_datum']
        if self.instance.datum_podnosenja and datum < self.instance.datum_podnosenja:
            raise forms.ValidationError('Datum zatvaranja ne može biti pre datuma pokretanja postupka.')
        return datum
