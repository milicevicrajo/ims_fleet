import django_filters
from .models import FuelConsumption, JobCode, OrganizationalUnit
from django import forms
from datetime import timedelta
from django.utils import timezone
from datetime import date, timedelta

class VehicleFilterForm(forms.Form):
    org_unit = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.all().order_by('code'),  # Uzimamo sve JobCode sortirane po šifri
        required=False,
        label='Organizaciona jedinica'
    )
    fuel_in_last_6_months = forms.ChoiceField(
        choices=[
            ('', '----'),  # Ovo predstavlja opciju da filter nije primenjen
            ('yes', 'Da'),
            ('no', 'Ne')
        ],
        required=False,
        label='Sipano gorivo u poslednjih 6 meseci'
    )
    center_code = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.values_list('center', flat=True).distinct().order_by('center'),  # Distinktne šifre centara
        required=False,
        label='Centar'
    )


class TrafficCardFilterForm(forms.Form):
    organizational_unit = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.all().order_by('name'),
        required=False,
        label='Organizaciona jedinica',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    center = forms.ChoiceField(
        choices=[],
        required=False,
        label='Centar',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        centers = OrganizationalUnit.objects.values_list('center', flat=True).distinct().order_by('center')
        self.fields['center'].choices = [('', '--- Svi centri ---')] + [(c, c) for c in centers]

class FuelFilterForm(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='gte', 
        label='Od datuma',
        widget=forms.DateInput(
            format='%d/%m/%Y',
            attrs={
                'type': 'date',
                'placeholder': 'Od datuma',
                'value': (timezone.now() - timedelta(days=40)).strftime('%Y-%m-%d')  # 40 dana pre
            }
        ),
        input_formats=['%Y-%m-%d'],
    )
    end_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte', 
        label='Do datuma',
        widget=forms.DateInput(
            format='%d/%m/%Y',
            attrs={
                'type': 'date',
                'placeholder': 'Do datuma',
                'value': timezone.now().strftime('%Y-%m-%d')  # Današnji datum
            }
        ),
        input_formats=['%Y-%m-%d'],
    )

    class Meta:
        model = FuelConsumption
        fields = ['start_date', 'end_date',]


class FuelTransactionFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Od datuma"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Do datuma"
    )

class FuelTransactionFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Od datuma'
            }
        ),
        label="Od datuma"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Do datuma'
            }
        ),
        label="Do datuma"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data.get('start_date'):
            self.initial['start_date'] = date.today() - timedelta(days=40)
        if not self.data.get('end_date'):
            self.initial['end_date'] = date.today()