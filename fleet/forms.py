from django import forms
from .models import *

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = '__all__'

class TrafficCardForm(forms.ModelForm):
    class Meta:
        model = TrafficCard
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
    class Meta:
        model = Policy
        fields = '__all__'

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
    class Meta:
        model = PutniNalog
        fields = '__all__'

class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = '__all__'

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = '__all__'


