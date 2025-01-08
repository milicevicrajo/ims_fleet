from django import forms
from .models import *
import django_filters
from django_select2.forms import Select2Widget

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = '__all__'

class TrafficCardForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    issue_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum izdavanja"
    )
    valid_until = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Važi do"
    )
    class Meta:
        model = TrafficCard
        fields = '__all__'

class OrganizationalUnitForm(forms.ModelForm):
    class Meta:
        model = OrganizationalUnit
        fields = '__all__'
class JobCodeForm(forms.ModelForm):
    class Meta:
        model = JobCode
        fields = '__all__'

class LeaseForm(forms.ModelForm):
    class Meta:
        model = Lease
        fields = '__all__'

class PolicyForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    issue_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum izdavanja"
    )
    start_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum početka"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum završetka"
    )
    class Meta:
        model = Policy
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.issue_date:
                self.initial['issue_date'] = self.instance.issue_date.strftime('%Y-%m-%d')
            if self.instance.start_date:
                self.initial['start_date'] = self.instance.start_date.strftime('%Y-%m-%d')
            if self.instance.end_date:
                self.initial['end_date'] = self.instance.end_date.strftime('%Y-%m-%d')
        # Prolazi kroz sva polja u formi i postavlja ih kao obavezna
        for field_name, field in self.fields.items():
            field.required = True
            
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

class FuelConsumptionForm(forms.ModelForm):
    class Meta:
        model = FuelConsumption
        fields = '__all__'


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = '__all__'

class PutniNalogForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Zaposleni"
    )
    travel_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum putovanja"
    )
    return_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum povratka"
    )

    class Meta:
        model = PutniNalog
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.travel_date:
                self.initial['travel_date'] = self.instance.travel_date.strftime('%Y-%m-%d')
            if self.instance.return_date:
                self.initial['return_date'] = self.instance.return_date.strftime('%Y-%m-%d')

        # Prolazi kroz sva polja u formi i postavlja ih kao obavezna
        for field_name, field in self.fields.items():
            field.required = True
class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = '__all__'

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = '__all__'

class ServiceTransactionForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    datum = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    class Meta:
        model = ServiceTransaction
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.datum:
                self.initial['datum'] = self.instance.datum.strftime('%Y-%m-%d')
        # Prolazi kroz sva polja u formi i postavlja ih kao obavezna
        for field_name, field in self.fields.items():
            field.required = True
class RequisitionForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    datum_trebovanja = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    class Meta:
        model = Requisition
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.datum_trebovanja:
                self.initial['datum_trebovanja'] = self.instance.datum_trebovanja.strftime('%Y-%m-%d')
        # Prolazi kroz sva polja u formi i postavlja ih kao obavezna osim Boolean polja
        for field_name, field in self.fields.items():
            if not isinstance(field, forms.BooleanField):  # Ignoriše Boolean polja
                field.required = True

class DraftRequisitionForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    datum_trebovanja = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    mesec_unosa = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Mesec unosa"
    )
    popravka_kategorija = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Kategorija popravke"
    )
    kilometraza = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Kilometraža"
    )
    nije_garaza = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Nije garaža"
    )
    napomena = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Napomena"
    )

    class Meta:
        model = DraftRequisition
        fields = ['vehicle','datum_trebovanja', 'mesec_unosa', 'popravka_kategorija', 'kilometraza', 'nije_garaza', 'napomena']
