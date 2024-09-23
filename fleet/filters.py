import django_filters
from .models import FuelConsumption, JobCode, OrganizationalUnit
from django import forms
from datetime import timedelta
from django.utils import timezone

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