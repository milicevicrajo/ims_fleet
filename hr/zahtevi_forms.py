from datetime import datetime

from django import forms
from django.db.models import Max
from django.forms import inlineformset_factory
from django.utils import timezone

from hr.models import BrojacZahteva, Employee, Pismo, Potpisnik, ResenjeDan, VrstaResenja, VrstaZahteva, Zahtev, ZahtevDan
from hr.form_layout import SekcijeMixin
from hr.resenja_forms import (CUVARI_UPUTSTVO, DATE_ATTRS, DodatnaPoljaMixin, _ukrasi, izbor_oj, ocisti_vrstu_sa_poljima,
    validiraj_period)
from hr.services.resenja import normalizuj_pol


def _osobe():
    return Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')


def _aktivne_vrste(instance=None):
    vrste = list(VrstaZahteva.objects.filter(je_aktivna=True).select_related('vrsta_resenja'))
    if instance is not None and instance.pk and instance.vrsta_id and instance.vrsta not in vrste:
        vrste.append(instance.vrsta)
    return vrste


def proveri_vrstu(form, data, *, ima_dane):
    """Podaci koje izabrana vrsta zahteva traži. `ima_dane` govori da li su uneti pojedinačni dani."""
    vrsta = data.get('vrsta')
    if not vrsta:
        return
    if vrsta.trazi_period and not data.get('datum_od'):
        form.add_error('datum_od', 'Ova vrsta zahteva traži početak perioda.')
    if vrsta.trazi_period and not data.get('datum_do') and not data.get('do_zavrsetka_posla'):
        form.add_error('datum_do', 'Unesi kraj perioda ili označi „do završetka posla“.')
    if vrsta.trazi_dane and not ima_dane and not data.get('datum_od'):
        form.add_error(None, 'Ova vrsta zahteva traži bar jedan dan ili period.')
    if vrsta.trazi_radne_dane and not data.get('broj_radnih_dana'):
        form.add_error('broj_radnih_dana', 'Ova vrsta zahteva traži broj radnih dana.')
    validiraj_period(form, data)


class ZahtevForm(DodatnaPoljaMixin, forms.ModelForm):
    oj_kod = forms.ChoiceField(required=False, label='Organizaciona jedinica',
        help_text='Podrazumevano se preuzima OJ izabranog zaposlenog.')

    class Meta:
        model = Zahtev
        fields = ['vrsta', 'zaposleni', 'datum_zahteva', 'pismo', 'pol', 'oj_kod', 'zaposleni_tekst', 'oj_naziv',
                  'radno_mesto', 'datum_od', 'datum_do', 'vreme_od', 'vreme_do', 'do_zavrsetka_posla',
                  'broj_radnih_dana', 'datum_povratka', 'razlog', 'podnosilac', 'podnosilac_funkcija',
                  'odobrava', 'odobrava_funkcija', 'napomena']
        widgets = {
            'datum_zahteva': forms.DateInput(attrs=DATE_ATTRS),
            'datum_od': forms.DateInput(attrs=DATE_ATTRS),
            'datum_do': forms.DateInput(attrs=DATE_ATTRS),
            'datum_povratka': forms.DateInput(attrs=DATE_ATTRS),
            'razlog': forms.Textarea(attrs={'rows': 2}),
            'napomena': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        actor = kwargs.pop('actor', None)
        super().__init__(*args, **kwargs)
        vrste = _aktivne_vrste(self.instance)
        self.fields['vrsta'].queryset = VrstaZahteva.objects.filter(pk__in=[vrsta.pk for vrsta in vrste])
        self.fields['zaposleni'].queryset = _osobe()
        self.fields['podnosilac'].queryset = _osobe()
        self.fields['odobrava'].queryset = _osobe()
        self.fields['odobrava'].required = False
        self.fields['odobrava'].empty_label = 'Potpisnik rešenja na datum zahteva'
        self.fields['odobrava'].help_text = 'Kome se zahtev upućuje i ko ga odobrava.'
        self.fields['odobrava_funkcija'].required = False
        self.fields['pol'].choices = [('', 'Preuzmi iz evidencije'), ('M', 'Muški'), ('F', 'Ženski')]
        self.fields['oj_kod'].choices = izbor_oj(actor, [self.instance.oj_kod] if self.instance.pk else [])
        for naziv in ('zaposleni_tekst', 'oj_naziv', 'radno_mesto'):
            self.fields[naziv].required = False
        self.initial.setdefault('datum_zahteva', timezone.localdate())
        self.dodaj_dodatna_polja(vrste, self.instance.dodatni_podaci)
        self.ima_resenja = bool(self.instance.pk and self.instance.resenja.exists())
        if self.ima_resenja:
            # Rešenja nose ime zaposlenog i broj zahteva; zaposleni se posle toga ne menja.
            self.fields['zaposleni'].disabled = True
        _ukrasi(self)

    def clean(self):
        data = super().clean()
        vrsta = data.get('vrsta')
        if vrsta:
            self.instance.dodatni_podaci = self.ocisti_dodatna_polja(vrsta)
        # Pojedinačne dane proverava view, jer su u posebnom skupu formi.
        proveri_vrstu(self, data, ima_dane=True)
        employee = data.get('zaposleni')
        if employee and not normalizuj_pol(data.get('pol') or employee.gender):
            self.add_error('pol', 'Pol nije poznat u evidenciji. Izaberite oblik teksta za ovaj zahtev.')
        dan = data.get('datum_zahteva')
        if self.instance.redni_broj and dan and dan.year != self.instance.godina:
            self.add_error('datum_zahteva', f'Broj zahteva je iz {self.instance.godina}. godine; godina se ne menja.')
        if data.get('odobrava') and not data.get('odobrava_funkcija'):
            self.add_error('odobrava_funkcija', 'Unesite funkciju osobe koja odobrava.')
        return data


class ZahtevDanForm(forms.ModelForm):
    class Meta:
        model = ZahtevDan
        fields = ['datum', 'vrsta_dana']
        widgets = {
            'datum': forms.DateInput(attrs=DATE_ATTRS),
            'vrsta_dana': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _ukrasi(self)


ZahtevDanFormSet = inlineformset_factory(Zahtev, ZahtevDan, form=ZahtevDanForm, extra=1, can_delete=True)


def parsiraj_dane(vrednost):
    datumi = []
    for deo in (vrednost or '').replace(';', ',').split(','):
        deo = deo.strip().rstrip('.')
        if not deo:
            continue
        try:
            datumi.append(datetime.strptime(deo, '%d.%m.%Y').date())
        except ValueError:
            raise forms.ValidationError(f'Datum „{deo}“ nije u obliku 01.02.2026.')
    return sorted(set(datumi))


class GrupniZahtevForm(DodatnaPoljaMixin, forms.Form):
    """Isti zahtev za više zaposlenih: svaki zaposleni dobija svoj zahtev i svoj broj."""

    vrsta = forms.ModelChoiceField(queryset=VrstaZahteva.objects.filter(je_aktivna=True), label='Vrsta zahteva')
    datum_zahteva = forms.DateField(label='Datum zahteva', widget=forms.DateInput(attrs=DATE_ATTRS))
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
    razlog = Zahtev._meta.get_field('razlog').formfield(widget=forms.Textarea(attrs={'rows': 2}))
    podnosilac = forms.ModelChoiceField(queryset=Employee.objects.none(), label='Ko podnosi zahtev')
    podnosilac_funkcija = forms.CharField(required=False, max_length=120, label='Funkcija podnosioca')
    odobrava = forms.ModelChoiceField(queryset=Employee.objects.none(), required=False, label='Ko odobrava zahtev',
        empty_label='Potpisnik rešenja na datum zahteva')
    odobrava_funkcija = forms.CharField(required=False, max_length=120, label='Funkcija onoga ko odobrava')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['podnosilac'].queryset = _osobe()
        self.fields['odobrava'].queryset = _osobe()
        self.dodaj_dodatna_polja(VrstaZahteva.objects.filter(je_aktivna=True))
        _ukrasi(self)

    def clean_dani(self):
        return parsiraj_dane(self.cleaned_data.get('dani'))

    def clean(self):
        data = super().clean()
        proveri_vrstu(self, data, ima_dane=bool(data.get('dani')))
        if data.get('vrsta'):
            data['dodatni_podaci'] = self.ocisti_dodatna_polja(data['vrsta'])
        if data.get('odobrava') and not data.get('odobrava_funkcija'):
            self.add_error('odobrava_funkcija', 'Unesite funkciju osobe koja odobrava.')
        return data


class ResenjaIzZahtevaForm(forms.Form):
    """Rešenje iz jednog ili više zahteva; vrsta se podrazumevano uzima iz vrste zahteva."""

    datum_resenja = forms.DateField(label='Datum rešenja', widget=forms.DateInput(attrs=DATE_ATTRS))
    vrsta = forms.ModelChoiceField(queryset=VrstaResenja.objects.filter(je_aktivna=True), required=False,
        label='Vrsta rešenja', empty_label='Prema vrsti zahteva')
    potpisnik = forms.ModelChoiceField(queryset=Potpisnik.objects.select_related('zaposleni'), required=False,
        label='Ko potpisuje rešenje', empty_label='Automatski prema datumu rešenja')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial.setdefault('datum_resenja', timezone.localdate())
        _ukrasi(self)

    def clean(self):
        data = super().clean()
        signer, day = data.get('potpisnik'), data.get('datum_resenja')
        if signer and day and (day < signer.vazi_od or (signer.vazi_do and day >= signer.vazi_do)):
            self.add_error('potpisnik', 'Izabrani potpisnik ne važi na datum rešenja.')
        return data


class VrstaZahtevaForm(SekcijeMixin, forms.ModelForm):
    SECTIONS = (
        ('osnovno', 'Osnovno', 'Oznaka, naziv i rešenje koje se po zahtevu izdaje.', ('kod', 'naziv', 'vrsta_resenja', 'redosled',
         'podrazumevano_pismo', 'je_aktivna'),
         'Vrsta rešenja se predlaže pri „Dodaj rešenje iz zahteva“; kadrovik može izabrati i drugu.', 'mdi-tag-outline'),
        ('tekst', 'Tekst zahteva', 'Predmet i pasusi dopisa.', ('predmet', 'tekst'),
         CUVARI_UPUTSTVO + ' Zahtev dodatno ima {razlog}, {podnosilac}, {podnosilac_funkcija}, {odobrava} i '
         '{odobrava_funkcija}.', 'mdi-file-document-edit-outline'),
        ('podaci', 'Podaci koje traži', 'Šta se unosi pri izradi zahteva.', ('trazi_period', 'trazi_dane', 'trazi_radne_dane', 'dodatna_polja'),
         'Dodatna polja se pišu kao oznaka|Naziv; iste oznake u vrsti rešenja prenose vrednost iz zahteva u rešenje.',
         'mdi-form-textbox'),
    )

    class Meta:
        model = VrstaZahteva
        fields = ['kod', 'naziv', 'predmet', 'tekst', 'vrsta_resenja', 'trazi_period', 'trazi_dane',
                  'trazi_radne_dane', 'dodatna_polja', 'podrazumevano_pismo', 'redosled', 'je_aktivna']
        widgets = {
            'tekst': forms.Textarea(attrs={'rows': 8}),
            'dodatna_polja': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['kod'].disabled = True
        self.fields['vrsta_resenja'].queryset = VrstaResenja.objects.all()
        _ukrasi(self)

    def clean(self):
        data = super().clean()
        ocisti_vrstu_sa_poljima(self)
        return data


class BrojacZahtevaForm(forms.ModelForm):
    """Početak numeracije u godini, npr. da se nastavi na broj iz postojećeg delovodnika."""

    class Meta:
        model = BrojacZahteva
        fields = ['godina', 'poslednji_broj']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['godina'].disabled = True
        self.fields['poslednji_broj'].help_text = 'Sledeći zahtev dobija ovaj broj uvećan za jedan.'
        _ukrasi(self)

    def clean(self):
        data = super().clean()
        godina, broj = data.get('godina'), data.get('poslednji_broj')
        if godina is not None and broj is not None:
            najveci = Zahtev.objects.filter(godina=godina).aggregate(n=Max('redni_broj'))['n'] or 0
            if broj < najveci:
                self.add_error('poslednji_broj', f'U {godina}. već postoji zahtev sa rednim brojem {najveci}; '
                                                 'brojač ne može ići unazad.')
        return data
