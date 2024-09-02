import django_filters
from .models import FuelConsumption
from django import forms

class FuelFilterForm(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='gte', 
        label='Od datuma',
        widget=forms.DateInput(format='%d/%m/%Y',attrs={'type': 'date', 'placeholder': 'Od datuma'}),
        input_formats=['%Y-%m-%d'],
    )
    end_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte', 
        label='Do datuma',
        widget=forms.DateInput(format='%d/%m/%Y',attrs={'type': 'date', 'placeholder': 'Do datuma'}),
        input_formats=['%Y-%m-%d'],
    )

    class Meta:
        model = FuelConsumption
        fields = ['start_date', 'end_date',]