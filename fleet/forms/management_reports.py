from django import forms
from django.utils import timezone


class ReportForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            if isinstance(field, forms.DateField):
                field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control', 'data-native-date': 'true'})


class VehicleInsuranceReportForm(ReportForm):
    as_of = forms.DateField(label='Datum preseka', initial=timezone.localdate)
    center = forms.CharField(label='Centar', required=False)
    category = forms.ChoiceField(label='Kategorija', required=False)
    ownership = forms.ChoiceField(label='Osnov vlasništva', choices=[('all', 'Sva IMS vlasnička vozila'), ('confirmed', 'Samo evidentirano vlasništvo')], initial='all')

    def __init__(self, *args, **kwargs):
        from fleet.models import Vehicle
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = [('', 'Sve kategorije'), *Vehicle.Category.choices]

    def clean_as_of(self):
        day = self.cleaned_data['as_of']
        if day > timezone.localdate():
            raise forms.ValidationError('Izaberite današnji ili raniji datum.')
        return day


class PeriodReportForm(ReportForm):
    date_from = forms.DateField(label='Datum od')
    date_to = forms.DateField(label='Datum do')

    def clean(self):
        data = super().clean()
        start, end = data.get('date_from'), data.get('date_to')
        if start and end and (start > end or (end - start).days > 1095):
            raise forms.ValidationError('Period mora biti pravilno poređan i najviše tri godine.')
        if end and end > timezone.localdate():
            raise forms.ValidationError('Završetak perioda ne može biti posle današnjeg dana.')
        return data


class FleetFuelReportForm(PeriodReportForm):
    supplier = forms.ChoiceField(label='Dobavljač', required=False, choices=[('', 'NIS i OMV'), ('nis', 'NIS'), ('omv', 'OMV')])
    fuel_type = forms.ChoiceField(label='Vrsta proizvoda', choices=[('fuel', 'Gorivo (bez AdBlue i ostalog)'), ('all', 'Svi proizvodi — odvojeno po vrsti'), ('diesel', 'Dizel'), ('petrol', 'Benzin'), ('lpg', 'TNG / LPG'), ('cng', 'CNG'), ('adblue', 'AdBlue'), ('other', 'Ostalo / nerazvrstano')])
    product = forms.CharField(label='Naziv proizvoda sadrži', required=False)
    center = forms.CharField(label='Centar', required=False)
    job_code = forms.CharField(label='Šifra posla', required=False)
    group_by = forms.ChoiceField(label='Prikaz', choices=[('month', 'Po mesecima'), ('center', 'Po centrima'), ('job', 'Po šiframa posla'), ('product', 'Po proizvodima'), ('month_center', 'Mesec i centar'), ('month_job', 'Mesec i šifra posla'), ('detail', 'Pojedinačne transakcije')])


class SupplierPartsReportForm(PeriodReportForm):
    source = forms.ChoiceField(label='Izvor', choices=[('uf', 'Stavke ulaznih faktura iz Nabavke'), ('goods', 'Robne stavke iz Nabavke')])
    supplier = forms.ChoiceField(label='Dobavljač', required=False)
    article = forms.CharField(label='Naziv dela / stavke sadrži', required=False)

    def __init__(self, *args, supplier_choices=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].choices = [('', 'Izaberite dobavljača'), *supplier_choices]
