from django import forms
from django.forms import inlineformset_factory

from hr.models import Employee, Pismo, Potpisnik, Resenje, ResenjeDan, VrstaResenja
from hr.services.resenja import ime_zaposlenog, organizaciona_jedinica, to_cyrillic

DATE_ATTRS = {'class': 'form-control js-date', 'autocomplete': 'off', 'placeholder': 'dd.mm.gggg'}


def _ukrasi(form):
    for field in form.fields.values():
        if isinstance(field, forms.DateField):
            field.input_formats = ['%d.%m.%Y', '%d.%m.%Y.', '%Y-%m-%d']
            field.widget.format = '%d.%m.%Y'
            field.widget.attrs.update(DATE_ATTRS)
        elif isinstance(field.widget, (forms.CheckboxInput,)):
            field.widget.attrs.setdefault('class', 'form-check-input')
        elif isinstance(field, forms.ModelChoiceField):
            field.widget.attrs.setdefault('class', 'form-select select2-method')
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs.setdefault('class', 'form-select')
        elif isinstance(field.widget, forms.Textarea):
            field.widget.attrs.setdefault('class', 'form-control')
            field.widget.attrs.setdefault('rows', 4)
        else:
            field.widget.attrs.setdefault('class', 'form-control')


class ResenjeForm(forms.ModelForm):
    class Meta:
        model = Resenje
        fields = ['vrsta', 'zaposleni', 'broj', 'datum_resenja', 'pismo', 'zaposleni_tekst', 'oj_naziv', 'radno_mesto',
                  'datum_od', 'datum_do', 'do_zavrsetka_posla', 'broj_radnih_dana', 'datum_povratka',
                  'zahtev_broj', 'zahtev_datum', 'potpisnik', 'napomena']
        widgets = {
            'datum_resenja': forms.DateInput(attrs=DATE_ATTRS),
            'datum_od': forms.DateInput(attrs=DATE_ATTRS),
            'datum_do': forms.DateInput(attrs=DATE_ATTRS),
            'datum_povratka': forms.DateInput(attrs=DATE_ATTRS),
            'zahtev_datum': forms.DateInput(attrs=DATE_ATTRS),
            'napomena': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vrsta'].queryset = VrstaResenja.objects.filter(je_aktivna=True)
        self.fields['zaposleni'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['potpisnik'].queryset = Potpisnik.objects.select_related('zaposleni')
        self.fields['potpisnik'].required = False
        self.fields['potpisnik'].help_text = 'Ostavi prazno da se preuzme potpisnik koji važi na datum rešenja.'
        self.fields['zaposleni_tekst'].required = False
        self.fields['oj_naziv'].required = False
        self.fields['radno_mesto'].required = False
        _ukrasi(self)

    def clean(self):
        data = super().clean()
        vrsta = data.get('vrsta')
        if not vrsta:
            return data
        if vrsta.trazi_period and not data.get('datum_od'):
            self.add_error('datum_od', 'Ova vrsta rešenja traži početak perioda.')
        if vrsta.trazi_period and not data.get('datum_do') and not data.get('do_zavrsetka_posla'):
            self.add_error('datum_do', 'Unesi kraj perioda ili označi „do završetka posla“.')
        if vrsta.trazi_radne_dane and not data.get('broj_radnih_dana'):
            self.add_error('broj_radnih_dana', 'Ova vrsta rešenja traži broj radnih dana.')
        datum_od, datum_do = data.get('datum_od'), data.get('datum_do')
        if datum_od and datum_do and datum_do < datum_od:
            self.add_error('datum_do', 'Kraj perioda ne može biti pre početka.')
        return data


class ResenjeDanForm(forms.ModelForm):
    class Meta:
        model = ResenjeDan
        fields = ['datum', 'vrsta_dana']
        widgets = {
            'datum': forms.DateInput(attrs=DATE_ATTRS),
            'vrsta_dana': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _ukrasi(self)


ResenjeDanFormSet = inlineformset_factory(Resenje, ResenjeDan, form=ResenjeDanForm, extra=1, can_delete=True)


class VrstaResenjaForm(forms.ModelForm):
    class Meta:
        model = VrstaResenja
        fields = ['kod', 'naziv', 'naslov', 'podnaslov', 'pravni_osnov', 'dispozitiv', 'obrazlozenje',
                  'pravna_pouka', 'dostavljeno', 'trazi_period', 'trazi_dane', 'trazi_radne_dane',
                  'podrazumevano_pismo', 'redosled', 'je_aktivna']
        widgets = {
            'pravni_osnov': forms.Textarea(attrs={'rows': 3}),
            'dispozitiv': forms.Textarea(attrs={'rows': 8}),
            'obrazlozenje': forms.Textarea(attrs={'rows': 5}),
            'pravna_pouka': forms.Textarea(attrs={'rows': 3}),
            'dostavljeno': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['kod'].disabled = True
        _ukrasi(self)


class PotpisnikForm(forms.ModelForm):
    class Meta:
        model = Potpisnik
        fields = ['zaposleni', 'funkcija', 'ime_cirilica', 'vazi_od', 'vazi_do']
        widgets = {
            'vazi_od': forms.DateInput(attrs=DATE_ATTRS),
            'vazi_do': forms.DateInput(attrs=DATE_ATTRS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['zaposleni'].queryset = Employee.objects.order_by('last_name', 'first_name')
        _ukrasi(self)

    def clean(self):
        data = super().clean()
        vazi_od, vazi_do = data.get('vazi_od'), data.get('vazi_do')
        if vazi_od and vazi_do and vazi_do <= vazi_od:
            self.add_error('vazi_do', 'Kraj važenja mora biti posle početka.')
        return data


class GrupnoResenjeForm(forms.Form):
    """Jedna vrsta i jedan period za više zaposlenih odjednom."""

    vrsta = forms.ModelChoiceField(queryset=VrstaResenja.objects.filter(je_aktivna=True), label='Vrsta rešenja')
    datum_resenja = forms.DateField(label='Datum rešenja', widget=forms.DateInput(attrs=DATE_ATTRS))
    pismo = forms.ChoiceField(choices=Pismo.choices, label='Pismo')
    datum_od = forms.DateField(required=False, label='Period od', widget=forms.DateInput(attrs=DATE_ATTRS))
    datum_do = forms.DateField(required=False, label='Period do', widget=forms.DateInput(attrs=DATE_ATTRS))
    do_zavrsetka_posla = forms.BooleanField(required=False, label='Do završetka posla')
    dani = forms.CharField(required=False, label='Pojedinačni dani',
        help_text='Datumi odvojeni zarezom, u obliku 01.02.2026.',
        widget=forms.TextInput(attrs={'placeholder': '20.06.2026, 21.06.2026'}))
    vrsta_dana = forms.ChoiceField(choices=ResenjeDan.VrstaDana.choices, required=False, label='Vrsta dana')
    broj_radnih_dana = forms.IntegerField(required=False, min_value=1, max_value=31, label='Broj radnih dana')
    datum_povratka = forms.DateField(required=False, label='Datum javljanja na posao',
        widget=forms.DateInput(attrs=DATE_ATTRS))
    zahtev_broj = forms.CharField(required=False, max_length=40, label='Broj zahteva')
    zahtev_datum = forms.DateField(required=False, label='Datum zahteva', widget=forms.DateInput(attrs=DATE_ATTRS))
    napomena = forms.CharField(required=False, label='Napomena uz obrazloženje', widget=forms.Textarea(attrs={'rows': 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _ukrasi(self)

    def clean_dani(self):
        from datetime import datetime
        vrednost = (self.cleaned_data.get('dani') or '').strip()
        if not vrednost:
            return []
        datumi = []
        for deo in vrednost.replace(';', ',').split(','):
            deo = deo.strip().rstrip('.')
            if not deo:
                continue
            try:
                datumi.append(datetime.strptime(deo, '%d.%m.%Y').date())
            except ValueError:
                raise forms.ValidationError(f'Datum „{deo}“ nije u obliku 01.02.2026.')
        return sorted(set(datumi))

    def clean(self):
        data = super().clean()
        vrsta = data.get('vrsta')
        if not vrsta:
            return data
        if vrsta.trazi_period and not data.get('datum_od'):
            self.add_error('datum_od', 'Ova vrsta rešenja traži početak perioda.')
        if vrsta.trazi_period and not data.get('datum_do') and not data.get('do_zavrsetka_posla'):
            self.add_error('datum_do', 'Unesi kraj perioda ili označi „do završetka posla“.')
        if vrsta.trazi_dane and not data.get('dani'):
            self.add_error('dani', 'Ova vrsta rešenja traži bar jedan dan.')
        if vrsta.trazi_radne_dane and not data.get('broj_radnih_dana'):
            self.add_error('broj_radnih_dana', 'Ova vrsta rešenja traži broj radnih dana.')
        return data


def predlog_teksta(employee, pismo):
    """Vrednosti koje forma nudi za ime, organizacionu jedinicu i radno mesto."""
    _, jedinica = organizaciona_jedinica(employee)
    naziv = jedinica.name.upper() if jedinica else ''
    radno = (employee.position or employee.job_title or '').upper()
    if pismo != Pismo.LATINICA:
        naziv, radno = to_cyrillic(naziv), to_cyrillic(radno)
    return {'zaposleni_tekst': ime_zaposlenog(employee, pismo), 'oj_naziv': naziv, 'radno_mesto': radno}
