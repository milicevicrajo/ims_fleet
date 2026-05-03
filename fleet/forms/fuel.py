from django import forms

from ..models import FuelConsumption


class FuelConsumptionForm(forms.ModelForm):
    class Meta:
        model = FuelConsumption
        fields = "__all__"
