from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from core.mixins import user_has_role_permission
from hr.access import visible_employees
from hr.form_layout import SekcijeMixin

from hr.models import Employee, Pismo, Potpisnik, Resenje, ResenjeDan, VrstaResenja
from hr.services.resenja import (dodatna_polja, ime_zaposlenog, naziv_jedinice, normalizuj_pol, organizaciona_jedinica,
    parsiraj_dodatna_polja, to_cyrillic)

DATE_ATTRS = {'class': 'form-control js-date', 'autocomplete': 'off', 'placeholder': 'dd.mm.gggg'}


def _ukrasi(form):
    for field in form.fields.values():
        if isinstance(field, forms.DateField):
            field.input_formats = ['%d.%m.%Y', '%d.%m.%Y.', '%Y-%m-%d']
            field.widget.format = '%d.%m.%Y'
            field.widget.attrs.update(DATE_ATTRS)
        elif isinstance(field, forms.TimeField):
            field.input_formats = ['%H:%M', '%H:%M:%S']
            field.widget = forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': 'form-control'})
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


def validiraj_period(form, data):
    od, do = data.get('datum_od'), data.get('datum_do')
    if do and not od:
        form.add_error('datum_od', 'Unesite početak perioda.')
    if od and not do and not data.get('do_zavrsetka_posla'):
        form.add_error('datum_do', 'Unesite kraj perioda ili označite „do završetka posla“.')
    if od and do and do < od:
        form.add_error('datum_do', 'Kraj perioda ne može biti pre početka.')
    if data.get('do_zavrsetka_posla') and (not od or do):
        form.add_error('do_zavrsetka_posla', 'Unesite početak i ostavite kraj perioda prazan.')
    start, end = data.get('vreme_od'), data.get('vreme_do')
    if bool(start) != bool(end):
        form.add_error('vreme_do' if start else 'vreme_od', 'Unesite oba vremena: od i do.')
    if start and end and start == end:
        form.add_error('vreme_do', 'Početak i kraj rada ne mogu biti isti.')


class DodatnaPoljaMixin:
    """Polja `dp_<oznaka>` iz šifrarnika vrsta. Prikazuju se sva, a obavezna su samo polja izabrane vrste."""

    def dodaj_dodatna_polja(self, vrste, podaci=None):
        self.dodatne_oznake = {}
        for vrsta in vrste:
            for oznaka, naziv in dodatna_polja(vrsta):
                self.dodatne_oznake.setdefault(oznaka, naziv)
        podaci = podaci or {}
        for oznaka, naziv in self.dodatne_oznake.items():
            self.fields['dp_' + oznaka] = forms.CharField(required=False, max_length=500, label=naziv,
                initial=podaci.get(oznaka, ''), help_text='Unesite u pismu dokumenta.')

    def dodatna_polja_forme(self):
        return [self['dp_' + oznaka] for oznaka in getattr(self, 'dodatne_oznake', {})]

    def ocisti_dodatna_polja(self, vrsta):
        rezultat = {}
        for oznaka, _ in dodatna_polja(vrsta):
            vrednost = (self.cleaned_data.get('dp_' + oznaka) or '').strip()
            if not vrednost and 'dp_' + oznaka in self.fields:
                self.add_error('dp_' + oznaka, 'Ova vrsta traži ovaj podatak.')
            rezultat[oznaka] = vrednost
        return rezultat


def izbor_oj(actor, dodatne=()):
    """Organizacione jedinice zaposlenih koje korisnik vidi, za izbor OJ u tekstu dokumenta."""
    employees = visible_employees(actor, unrestricted=user_has_role_permission(actor, 'hr:resenje_view_all')) if actor else Employee.objects.all()
    codes = {str(c or d or '').strip() for c, d in employees.values_list('org_unit_code', 'department_code')}
    codes.update(kod for kod in dodatne if kod)
    return [('', 'Preuzmi OJ zaposlenog')] + [(c, f'OJ {c}') for c in sorted(codes - {''})]


def ocisti_vrstu_sa_poljima(form):
    """Provera teksta `dodatna_polja` u šifrarniku rešenja i zahteva."""
    _, greske = parsiraj_dodatna_polja(form.cleaned_data.get('dodatna_polja'))
    for greska in greske:
        form.add_error('dodatna_polja', greska)


class ResenjeForm(DodatnaPoljaMixin, forms.ModelForm):
    oj_kod = forms.ChoiceField(required=False, label='Organizaciona jedinica',
        help_text='Podrazumevano se preuzima OJ izabranog zaposlenog.')
    novi_potpisnik = forms.ModelChoiceField(queryset=Employee.objects.none(), required=False, label='Osoba koja potpisuje')
    funkcija_potpisnika = forms.CharField(required=False, max_length=120, label='Funkcija u potpisu', initial='Generalni direktor')
    class Meta:
        model = Resenje
        fields = ['vrsta', 'zaposleni', 'broj', 'datum_resenja', 'pismo', 'pol', 'oj_kod', 'zaposleni_tekst', 'oj_naziv', 'radno_mesto',
                  'datum_od', 'datum_do', 'vreme_od', 'vreme_do', 'do_zavrsetka_posla', 'broj_radnih_dana', 'datum_povratka',
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
        actor = kwargs.pop('actor', None)
        super().__init__(*args, **kwargs)
        self.fields['vrsta'].queryset = VrstaResenja.objects.filter(je_aktivna=True)
        self.fields['zaposleni'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['potpisnik'].queryset = Potpisnik.objects.select_related('zaposleni')
        self.fields['potpisnik'].required = False
        self.fields['potpisnik'].label = 'Ko potpisuje rešenje'
        self.fields['potpisnik'].empty_label = 'Automatski prema datumu rešenja'
        self.fields['potpisnik'].help_text = 'Potpisnik je odgovorna osoba čije ime i funkcija stoje na kraju dokumenta.'
        self.fields['pol'].choices = [('', 'Preuzmi iz evidencije'), ('M', 'Muški'), ('F', 'Ženski')]
        self.fields['pol'].help_text = 'Određuje oblike „zaposlen/zaposlena“, „dužan/dužna“ i ostali tekst.'
        self.fields['oj_kod'].choices = izbor_oj(actor, [self.instance.oj_kod] if self.instance.pk else [])
        self.can_add_signer = bool(actor and user_has_role_permission(actor, 'hr:resenje_catalog_create'))
        if self.can_add_signer:
            self.fields['novi_potpisnik'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        else:
            self.fields.pop('novi_potpisnik')
            self.fields.pop('funkcija_potpisnika')
        self.initial.setdefault('datum_resenja', timezone.localdate())
        self.fields['zaposleni_tekst'].required = False
        self.fields['oj_naziv'].required = False
        self.fields['radno_mesto'].required = False
        self.fields['zahtev_broj'].label = 'Broj zahteva'
        self.fields['zahtev_broj'].help_text = 'Preuzeto iz povezanog zahteva.'
        vrste = list(VrstaResenja.objects.filter(je_aktivna=True))
        if self.instance.pk and self.instance.vrsta_id and self.instance.vrsta not in vrste:
            vrste.append(self.instance.vrsta)
        self.dodaj_dodatna_polja(vrste, self.instance.dodatni_podaci)
        self.po_zahtevu = bool(self.instance.pk and self.instance.zahtev_id)
        if self.po_zahtevu:
            # Zaposleni, broj i zahtev dolaze iz zahteva i ne menjaju se u rešenju.
            for naziv in ('zaposleni', 'broj', 'zahtev_broj', 'zahtev_datum'):
                self.fields[naziv].disabled = True
            self.fields['broj'].help_text = 'Podbroj zahteva, dodeljen automatski.'
        _ukrasi(self)

    def clean(self):
        data = super().clean()
        vrsta = data.get('vrsta')
        if not vrsta:
            return data
        self.instance.dodatni_podaci = self.ocisti_dodatna_polja(vrsta)
        if vrsta.trazi_period and not data.get('datum_od'):
            self.add_error('datum_od', 'Ova vrsta rešenja traži početak perioda.')
        if vrsta.trazi_period and not data.get('datum_do') and not data.get('do_zavrsetka_posla'):
            self.add_error('datum_do', 'Unesi kraj perioda ili označi „do završetka posla“.')
        if vrsta.trazi_radne_dane and not data.get('broj_radnih_dana'):
            self.add_error('broj_radnih_dana', 'Ova vrsta rešenja traži broj radnih dana.')
        validiraj_period(self, data)
        employee = data.get('zaposleni')
        if employee and not normalizuj_pol(data.get('pol') or employee.gender):
            self.add_error('pol', 'Pol nije poznat u evidenciji. Izaberite oblik teksta za ovo rešenje.')
        potpisnik, dan = data.get('potpisnik'), data.get('datum_resenja')
        if potpisnik and dan and not data.get('novi_potpisnik') and (dan < potpisnik.vazi_od or (potpisnik.vazi_do and dan >= potpisnik.vazi_do)):
            self.add_error('potpisnik', 'Izabrani potpisnik ne važi na datum rešenja.')
        if data.get('novi_potpisnik') and not data.get('funkcija_potpisnika'):
            self.add_error('funkcija_potpisnika', 'Unesite funkciju osobe koja potpisuje.')
        return data

    def postavi_potpisnika(self, resenje):
        if self.can_add_signer and self.cleaned_data.get('novi_potpisnik'):
            resenje.potpisnik, _ = Potpisnik.objects.get_or_create(
                zaposleni=self.cleaned_data['novi_potpisnik'],
                funkcija=to_cyrillic(self.cleaned_data['funkcija_potpisnika']),
                vazi_od=resenje.datum_resenja, vazi_do=None)


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


CUVARI_UPUTSTVO = ('Tekst se unosi ćirilicom; latinica nastaje preslovljavanjem. Čuvari mesta u vitičastim zagradama '
    '({zaposleni}, {oj}, {period}, {dani}…) zamenjuju se podacima, {rod:дужан|дужна} bira oblik po polu, a '
    '[[naziv|tekst]] ostaje samo kada podatak postoji. Svaka tačka dispozitiva i svaki pasus su u svom redu.')


class VrstaResenjaForm(SekcijeMixin, forms.ModelForm):
    SECTIONS = (
        ('osnovno', 'Osnovno', 'Oznaka, naziv u listama i redosled.', ('kod', 'naziv', 'redosled', 'podrazumevano_pismo', 'je_aktivna'),
         'Oznaka se ne menja posle unosa, jer je koriste zahtevi i izdata rešenja. Neaktivna vrsta se ne nudi za nova '
         'rešenja, a već izdata ostaju nepromenjena.', 'mdi-tag-outline'),
        ('tekst', 'Tekst rešenja', 'Delovi dokumenta redom kako se štampaju.', ('naslov', 'podnaslov', 'pravni_osnov', 'dispozitiv',
         'obrazlozenje', 'pravna_pouka', 'dostavljeno'), CUVARI_UPUTSTVO, 'mdi-file-document-edit-outline'),
        ('podaci', 'Podaci koje traži', 'Šta se unosi pri izradi rešenja.', ('trazi_period', 'trazi_dane', 'trazi_radne_dane', 'dodatna_polja'),
         'Dodatna polja se pišu kao oznaka|Naziv, svako u svom redu (npr. poslovi|Poslovi koje preuzima), a u tekstu se '
         'koriste kao {oznaka}. Polje koje vrsta traži je obavezno pri unosu.', 'mdi-form-textbox'),
    )

    class Meta:
        model = VrstaResenja
        fields = ['kod', 'naziv', 'naslov', 'podnaslov', 'pravni_osnov', 'dispozitiv', 'obrazlozenje',
                  'pravna_pouka', 'dostavljeno', 'trazi_period', 'trazi_dane', 'trazi_radne_dane',
                  'dodatna_polja', 'podrazumevano_pismo', 'redosled', 'je_aktivna']
        widgets = {
            'pravni_osnov': forms.Textarea(attrs={'rows': 3}),
            'dispozitiv': forms.Textarea(attrs={'rows': 8}),
            'obrazlozenje': forms.Textarea(attrs={'rows': 5}),
            'pravna_pouka': forms.Textarea(attrs={'rows': 3}),
            'dostavljeno': forms.Textarea(attrs={'rows': 4}),
            'dodatna_polja': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['kod'].disabled = True
        _ukrasi(self)

    def clean(self):
        data = super().clean()
        ocisti_vrstu_sa_poljima(self)
        return data


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
        self.fields['zaposleni'].label = 'Osoba koja potpisuje rešenja'
        self.initial.setdefault('vazi_od', timezone.localdate())
        _ukrasi(self)

    def clean(self):
        data = super().clean()
        vazi_od, vazi_do = data.get('vazi_od'), data.get('vazi_do')
        if vazi_od and vazi_do and vazi_do <= vazi_od:
            self.add_error('vazi_do', 'Kraj važenja mora biti posle početka.')
        return data


class GrupnoResenjeForm(DodatnaPoljaMixin, forms.Form):
    """Jedna vrsta i jedan period za više zaposlenih odjednom."""

    vrsta = forms.ModelChoiceField(queryset=VrstaResenja.objects.filter(je_aktivna=True), label='Vrsta rešenja')
    datum_resenja = forms.DateField(label='Datum rešenja', widget=forms.DateInput(attrs=DATE_ATTRS))
    pismo = forms.ChoiceField(choices=Pismo.choices, label='Pismo')
    datum_od = forms.DateField(required=False, label='Period od', widget=forms.DateInput(attrs=DATE_ATTRS))
    datum_do = forms.DateField(required=False, label='Period do', widget=forms.DateInput(attrs=DATE_ATTRS))
    vreme_od = forms.TimeField(required=False, label='Vreme rada od')
    vreme_do = forms.TimeField(required=False, label='Vreme rada do')
    do_zavrsetka_posla = forms.BooleanField(required=False, label='Do završetka posla')
    dani = forms.CharField(required=False, label='Pojedinačni dani',
        help_text='Datumi odvojeni zarezom, u obliku 01.02.2026.',
        widget=forms.TextInput(attrs={'placeholder': '20.06.2026, 21.06.2026'}))
    vrsta_dana = forms.ChoiceField(choices=ResenjeDan.VrstaDana.choices, required=False, label='Vrsta dana')
    broj_radnih_dana = forms.IntegerField(required=False, min_value=1, max_value=31, label='Broj radnih dana')
    datum_povratka = forms.DateField(required=False, label='Datum javljanja na posao',
        widget=forms.DateInput(attrs=DATE_ATTRS))
    zahtev_broj = forms.CharField(required=False, max_length=255, label='Zahtev (broj ili opis)')
    potpisnik = forms.ModelChoiceField(queryset=Potpisnik.objects.select_related('zaposleni'), required=False,
        label='Ko potpisuje rešenja', empty_label='Automatski prema datumu rešenja')
    zahtev_datum = forms.DateField(required=False, label='Datum zahteva', widget=forms.DateInput(attrs=DATE_ATTRS))
    napomena = forms.CharField(required=False, label='Napomena uz obrazloženje', widget=forms.Textarea(attrs={'rows': 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dodaj_dodatna_polja(VrstaResenja.objects.filter(je_aktivna=True))
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
        if vrsta.trazi_dane and not data.get('dani') and (not data.get('datum_od') or vrsta.kod == 'praznik'):
            self.add_error('dani', 'Ova vrsta rešenja traži bar jedan dan.')
        if vrsta.trazi_radne_dane and not data.get('broj_radnih_dana'):
            self.add_error('broj_radnih_dana', 'Ova vrsta rešenja traži broj radnih dana.')
        validiraj_period(self, data)
        data['dodatni_podaci'] = self.ocisti_dodatna_polja(vrsta)
        signer, day = data.get('potpisnik'), data.get('datum_resenja')
        if signer and day and (day < signer.vazi_od or (signer.vazi_do and day >= signer.vazi_do)):
            self.add_error('potpisnik', 'Izabrani potpisnik ne važi na datum rešenja.')
        return data


def predlog_teksta(employee, pismo):
    """Vrednosti koje forma nudi za ime, organizacionu jedinicu i radno mesto."""
    kod, jedinica = organizaciona_jedinica(employee)
    naziv = naziv_jedinice(kod, pismo)
    radno = (employee.position or employee.job_title or '').upper()
    if pismo != Pismo.LATINICA:
        naziv, radno = to_cyrillic(naziv), to_cyrillic(radno)
    return {'zaposleni_tekst': ime_zaposlenog(employee, pismo), 'oj_naziv': naziv, 'oj_kod': kod,
            'radno_mesto': radno, 'pol': normalizuj_pol(employee.gender)}
