from datetime import date

from django import forms
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from core.models import OrganizationalUnit

from .fuel import FuelConsumptionForm
from .garaza import (
    KvarForm,
    KvarPartForm,
    ProcurementItemForm,
    ProcurementRequestForm,
    VehicleTravelOrderCloseForm,
    VehicleTravelOrderForm,
)
from .lease import LeaseForm
from .putni_nalozi import PutniNalogForm
from ..models import (
    DraftInsurance,
    Insurance,
)
from .policy import PolicyForm
from .vehicles import JobCodeForm, TrafficCardForm, VehicleForm, VehicleTenderDocumentForm
from .services import (
    DraftRequisitionForm,
    DraftServiceTransactionForm,
    RequisitionForm,
    ServiceFixingFilterForm,
    ServiceForm,
    ServiceTransactionForm,
    ServiceTypeForm,
)

class OrganizationalUnitForm(forms.ModelForm):
    class Meta:
        model = OrganizationalUnit
        fields = '__all__'
class ReportPeriodFilterForm(forms.Form):
    GODINA_CHOICES = [(str(y), str(y)) for y in range(2020, 2031)]
    MESEC_CHOICES = [(str(m), str(m)) for m in range(1, 13)]
    POLOVINA_CHOICES = [
        ('1', 'Prva polovina'),
        ('2', 'Druga polovina'),
    ]

    godina = forms.ChoiceField(choices=GODINA_CHOICES, required=False, label='Godina')
    mesec = forms.ChoiceField(choices=MESEC_CHOICES, required=False, label='Mesec')
    polovina = forms.ChoiceField(choices=POLOVINA_CHOICES, required=False, label='Polovina meseca')


class OMVPutnickaFilterForm(ReportPeriodFilterForm):
    pass


class PutnickaFilterForm(ReportPeriodFilterForm):
    pass


class InsuranceForm(forms.ModelForm):
    class Meta:
        model = Insurance
        fields = [
            "vehicle",
            "god", "sif_vrs", "br_naloga", "stavka", "oj", "knt",
            "datum", "vez_dok", "potrazuje", "kola",
        ]

class DraftInsuranceForm(forms.ModelForm):
    KOLO_CHOICES = [
        ("", "---------"),  # prazno = None
        ("True", "Da"),
        ("False", "Ne"),
    ]
    kola = forms.ChoiceField(
        choices=KOLO_CHOICES,
        required=False,
        label="Odnosi se na auto"
    )

    class Meta:
        model = DraftInsurance
        fields = [
            "vehicle",
            "god", "sif_vrs", "br_naloga", "stavka", "oj", "knt",
            "datum", "vez_dok", "potrazuje", "kola",
        ]

    def clean_kola(self):
        value = self.cleaned_data["kola"]
        if value == "True":
            return True
        elif value == "False":
            return False
        return None
