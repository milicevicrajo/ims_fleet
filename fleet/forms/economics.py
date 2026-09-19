from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from fleet.models import (VehicleAnalysisProfile, LeaseChargePeriod, VehicleDowntime,
    VehicleEconomicAssessment, VehicleEconomicScenario, Lease, Kvar, VehicleTravelOrder)
from fleet.support.vehicle_detail import VehiclePeriodForm


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            if isinstance(field, forms.DateField):
                field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 3


class AnalysisProfileForm(StyledModelForm):
    class Meta:
        model = VehicleAnalysisProfile
        exclude = ['vehicle', 'created_at']

    def clean(self):
        data = super().clean()
        if data.get('effective_from') and VehicleAnalysisProfile.objects.filter(
            vehicle_id=self.instance.vehicle_id, effective_from=data['effective_from']).exclude(pk=self.instance.pk).exists():
            self.add_error('effective_from', 'Profil za ovaj datum već postoji. Izaberite datum nove promene.')
        return data


class ChargePeriodForm(StyledModelForm):
    class Meta:
        model = LeaseChargePeriod
        fields = ['lease', 'start', 'end', 'amount', 'basis', 'evidence']

    def __init__(self, *args, vehicle, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lease'].queryset = Lease.objects.filter(vehicle=vehicle).exclude(lease_type='finansijski')


class DowntimeForm(StyledModelForm):
    class Meta:
        model = VehicleDowntime
        exclude = ['vehicle']

    def __init__(self, *args, vehicle, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['incident'].queryset = Kvar.objects.filter(vehicle=vehicle)


class OrderJobForm(StyledModelForm):
    class Meta:
        model = VehicleTravelOrder
        fields = ['job_code']

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        from fleet.support.management_reports import allowed_centers
        centers = allowed_centers(user)
        if centers:
            self.fields['job_code'].queryset = self.fields['job_code'].queryset.filter(center__in=centers)


class AssessmentForm(StyledModelForm):
    class Meta:
        model = VehicleEconomicAssessment
        fields = ['as_of', 'title', 'years', 'discount_percent', 'annual_km', 'annual_days', 'scope', 'assumptions']


class ScenarioForm(StyledModelForm):
    class Meta:
        model = VehicleEconomicScenario
        exclude = ['assessment']


class ScenarioSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        rows = [f.cleaned_data for f in self.forms if f.cleaned_data and not f.cleaned_data.get('DELETE')]
        if len(rows) < 2 or sum(r.get('kind') == 'keep' for r in rows) != 1:
            raise forms.ValidationError('Unesite najmanje dve alternative i tačno jedno zadržavanje postojećeg rešenja.')
        if len({r['name'].strip().casefold() for r in rows}) != len(rows):
            raise forms.ValidationError('Nazivi alternativa moraju biti različiti.')


ScenarioFormSet = inlineformset_factory(VehicleEconomicAssessment, VehicleEconomicScenario,
    form=ScenarioForm, formset=ScenarioSet, extra=3, min_num=0, max_num=6,
    validate_max=True, can_delete=False)


class FleetAnalysisForm(VehiclePeriodForm):
    center = forms.CharField(label='Centar (šifra)', required=False, max_length=30)
    basis = forms.ChoiceField(label='Raspolaganje', required=False, choices=[('', 'Svi osnovi'),
        ('owned', 'Vlasništvo IMS'), ('finansijski', 'Finansijski lizing'),
        ('operativni', 'Operativni lizing'), ('dugorocni', 'Dugoročni najam'), ('unknown', 'Nepotpuna istorija')])
    purpose = forms.ChoiceField(label='Poslovna namena', required=False,
        choices=[('', 'Sve namene'), ('unknown', 'Nerazvrstano')] + list(VehicleAnalysisProfile.Purpose.choices))
    include_retired = forms.BooleanField(label='Uključi i otpisana vozila', required=False)
