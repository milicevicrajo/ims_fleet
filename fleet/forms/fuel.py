from django import forms

from ..models import FuelConsumption
from .layout import FieldsetMixin


class FuelConsumptionForm(FieldsetMixin, forms.ModelForm):
    fieldsets = (
        ('Vozilo i datum', None, ('vehicle', 'date', 'job_code')),
        ('Točenje', 'Količina i vrsta goriva, i stanje brojača u trenutku točenja.',
         ('amount', 'fuel_type', 'mileage')),
        ('Iznos i dobavljač', 'Bruto je iznos sa PDV-om, neto bez njega.',
         ('cost_bruto', 'cost_neto', 'supplier')),
    )

    class Meta:
        model = FuelConsumption
        fields = "__all__"
        help_texts = {
            "amount": "Natočena količina u litrima. Za AdBlue upisati stvarnu količinu — ne sabira se sa gorivom u potrošnji.",
            "mileage": "Stanje brojača kilometara pri točenju. Nula znači da nije očitano — takvo točenje ne ulazi u obračun prosečne potrošnje.",
            "cost_bruto": "Iznos sa PDV-om, onako kako stoji na računu.",
            "cost_neto": "Iznos bez PDV-a.",
            "fuel_type": "Na primer: dizel, benzin, TNG, AdBlue. Za električna vozila upisati „električno“ — sistem tu vrednost prepoznaje.",
            "job_code": "Šifra posla kao slobodan tekst. Ako se ne unese, trošak se vezuje samo za vozilo.",
        }
