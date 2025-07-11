from django import forms
from .models import Kontakti, Napomene, Opomene, PozivPismo, PoziviTel, Tuzbe

class KontaktiForm(forms.ModelForm):
    class Meta:
        model = Kontakti
        fields = ['sif_par', 'naz_par', 'kontakt', 'email', 'napomena']
    
    def __init__(self, *args, **kwargs):
        super(KontaktiForm, self).__init__(*args, **kwargs)
        self.fields['sif_par'].widget.attrs['readonly'] = True  # Ne može se menjati
        self.fields['naz_par'].widget.attrs['readonly'] = True  # Ne može se menjati


from django import forms
from .models import Napomene

class NapomeneForm(forms.ModelForm):
    VELIKI_CHOICES = [
        ('da', 'Da'),
        ('', 'Ne'),
    ]

    veliki = forms.ChoiceField(
        choices=VELIKI_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Izaberite opciju: 'Da' ako se odnosi na važnu napomenu, ili ostavite prazno."
    )

    class Meta:
        model = Napomene
        fields = ['sif_par', 'naz_par', 'napomene', 'veliki']

    def __init__(self, *args, **kwargs):
        super(NapomeneForm, self).__init__(*args, **kwargs)
        self.fields['sif_par'].widget.attrs['readonly'] = True  # Ne može se menjati
        self.fields['naz_par'].widget.attrs['readonly'] = True  # Ne može se menjati



from datetime import datetime  # Ispravan import

class OpomeneForm(forms.ModelForm):
    datum = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    class Meta:
        model = Opomene
        fields = ['sif_par', 'naz_par', 'god', 'br_opomene', 'datum', 'iznos', 'fakture', 'napomene']
    
    def clean_datum(self):
        datum = self.cleaned_data['datum']
        return datetime.combine(datum, datetime.min.time())  # Dodaje 00:00:00 kao default
    
    def __init__(self, *args, **kwargs):
        super(OpomeneForm, self).__init__(*args, **kwargs)
        self.fields['sif_par'].widget.attrs['readonly'] = True
        self.fields['naz_par'].widget.attrs['readonly'] = True

class PozivPismoForm(forms.ModelForm):
    datum = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    class Meta:
        model = PozivPismo
        fields = ['sif_par', 'naz_par', 'god', 'br_pisma', 'datum', 'iznos', 'fakture', 'napomene']
    
    def clean_datum(self):
        datum = self.cleaned_data['datum']
        return datetime.combine(datum, datetime.min.time())  # Dodaje 00:00:00 kao default
    
    def __init__(self, *args, **kwargs):
        super(PozivPismoForm, self).__init__(*args, **kwargs)
        self.fields['sif_par'].widget.attrs['readonly'] = True
        self.fields['naz_par'].widget.attrs['readonly'] = True

class PoziviTelForm(forms.ModelForm):
    datum = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    class Meta:
        model = PoziviTel
        fields = ['sif_par', 'naz_par', 'datum', 'napomena']
    
    def clean_datum(self):
        datum = self.cleaned_data['datum']
        return datetime.combine(datum, datetime.min.time())  # Dodaje 00:00:00 kao default
    
    def __init__(self, *args, **kwargs):
        super(PoziviTelForm, self).__init__(*args, **kwargs)
        self.fields['sif_par'].widget.attrs['readonly'] = True
        self.fields['naz_par'].widget.attrs['readonly'] = True


class TuzbeForm(forms.ModelForm):
    datum = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    class Meta:
        model = Tuzbe
        fields = ['sif_par', 'naz_par', 'god', 'br_opomene', 'datum', 'iznos', 'fakture', 'napomene']
    
    def clean_datum(self):
        datum = self.cleaned_data['datum']
        return datetime.combine(datum, datetime.min.time())  # Dodaje 00:00:00 kao default
    
    def __init__(self, *args, **kwargs):
        super(TuzbeForm, self).__init__(*args, **kwargs)
        self.fields['sif_par'].widget.attrs['readonly'] = True
        self.fields['naz_par'].widget.attrs['readonly'] = True


from django import forms

class OMVPutnickaFilterForm(forms.Form):
    GODINA_CHOICES = [(str(y), str(y)) for y in range(2020, 2031)]
    MESEC_CHOICES = [(str(m), str(m)) for m in range(1, 13)]
    POLOVINA_CHOICES = [
        ('1', 'Prva polovina'),
        ('2', 'Druga polovina'),
    ]

    godina = forms.ChoiceField(choices=GODINA_CHOICES, required=False, label='Godina')
    mesec = forms.ChoiceField(choices=MESEC_CHOICES, required=False, label='Mesec')
    polovina = forms.ChoiceField(choices=POLOVINA_CHOICES, required=False, label='Polovina meseca')


class PutnickaFilterForm(forms.Form):
    GODINA_CHOICES = [(str(y), str(y)) for y in range(2020, 2031)]
    MESEC_CHOICES = [(str(m), str(m)) for m in range(1, 13)]
    POLOVINA_CHOICES = [
        ('1', 'Prva polovina'),
        ('2', 'Druga polovina'),
    ]

    godina = forms.ChoiceField(choices=GODINA_CHOICES, required=False, label='Godina')
    mesec = forms.ChoiceField(choices=MESEC_CHOICES, required=False, label='Mesec')
    polovina = forms.ChoiceField(choices=POLOVINA_CHOICES, required=False, label='Polovina meseca')