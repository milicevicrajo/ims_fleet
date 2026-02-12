from django import forms
from django.db import transaction
from .models import *
import django_filters
from django_select2.forms import Select2Widget
from django.utils.translation import gettext_lazy as _
from datetime import date
class VehicleForm(forms.ModelForm):
    first_registration_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum prve registracije"
    )
    purchase_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum kupovine"
    )
    class Meta:
        model = Vehicle
        fields = '__all__'

class TrafficCardForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo",
        required=False
    )
    issue_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum izdavanja"
    )
    valid_until = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Važi do"
    )
    class Meta:
        model = TrafficCard
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.issue_date:
                self.initial['issue_date'] = self.instance.issue_date.strftime('%d.%m.%Y')
            if self.instance.valid_until:
                self.initial['valid_until'] = self.instance.valid_until.strftime('%d.%m.%Y')

        # Prolazi kroz sva polja u formi i postavlja ih kao obavezna
        for field_name, field in self.fields.items():
            field.required = True

class VehicleTenderDocumentForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label=_("Vozilo")
    )
    taken_at = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label=_("Datum fotografisanja")
    )

    class Meta:
        model = VehicleTenderDocument
        fields = ['vehicle', 'document_type', 'title', 'image', 'description', 'taken_at', 'is_active']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.taken_at:
            self.initial['taken_at'] = self.instance.taken_at.strftime('%d.%m.%Y')

class OrganizationalUnitForm(forms.ModelForm):
    class Meta:
        model = OrganizationalUnit
        fields = '__all__'
class JobCodeForm(forms.ModelForm):

    organizational_unit = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Organizaciona jedinica"
    )
    assigned_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum dodele"
    )
    class Meta:
        model = JobCode
        fields = '__all__'

class LeaseForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum početka"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum završetka"
    )
    class Meta:
        model = Lease
        fields = '__all__'
        widgets = {
            'lease_type': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.start_date:
                self.initial['start_date'] = self.instance.start_date.strftime('%d.%m.%Y')
            if self.instance.end_date:
                self.initial['end_date'] = self.instance.end_date.strftime('%d.%m.%Y')

class PolicyForm(forms.ModelForm):
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )

    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    issue_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum izdavanja"
    )
    start_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum početka"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum završetka"
    )
    is_renewable = models.BooleanField(
        default=True,
        choices=YES_NO_CHOICES,  # Dodato choices
        verbose_name=_("Da li se polisa obnavlja?")
    )
    class Meta:
        model = Policy
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.issue_date:
                self.initial['issue_date'] = self.instance.issue_date.strftime('%d.%m.%Y')
            if self.instance.start_date:
                self.initial['start_date'] = self.instance.start_date.strftime('%d.%m.%Y')
            if self.instance.end_date:
                self.initial['end_date'] = self.instance.end_date.strftime('%d.%m.%Y')
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
    order_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum izdavanja naloga"
    )

    transport_type = forms.ChoiceField(
        label="Odaberi prevozno sredstvo",
        required=False,
        choices=(
            ("ims", "Auto IMS"),
            ("other", "Ostalo"),
        ),
        widget=forms.RadioSelect()
    )
    employee_type = forms.ChoiceField(
        label="Odaberi zaposlenog",
        required=False,
        choices=(
            ("ims", "Zaposleni IMS"),
            ("other", "Ostali"),
        ),
        widget=forms.RadioSelect()
    )
    order_number = forms.CharField(
        label="Broj naloga",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
    )
    start_sequence = forms.IntegerField(
        label="Početni broj naloga",
        required=False,
        widget=forms.HiddenInput(),
        help_text="Unesi samo prvi broj za centar/godinu ako ne postoji prethodni.",
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo",
        required=False
    )
    other_vehicle = forms.CharField(
        label="Prevozno sredstvo (ostalo)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Zaposleni",
        required=False
    )
    other_employee_name = forms.CharField(
        label="Zaposleni (ostalo)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    job_code = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Troškovi idu na teret"
    )
    travel_date = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum putovanja"
    )

    class Meta:
        model = PutniNalog
        fields = '__all__'
        widgets = {
            'order_date': forms.HiddenInput(),  # Sakriva polje od korisnika
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('opravdan', None)
        if self.instance and getattr(self.instance, "employee", None):
            inactive_employee = Employee.objects.filter(
                pk=self.instance.employee_id,
                is_active=False
            )
            if inactive_employee.exists():
                self.fields['employee'].queryset = (
                    self.fields['employee'].queryset | inactive_employee
                )
        
        # Automatski postavlja datum za order_date (novo ili iz postojećeg naloga)
        if self.instance and self.instance.pk:
            if self.instance.order_date:
                self.initial['order_date'] = self.instance.order_date.strftime('%d.%m.%Y')
            if self.instance.travel_date:
                self.initial['travel_date'] = self.instance.travel_date.strftime('%d.%m.%Y')
        elif not self.is_bound:
            self.initial.setdefault('order_date', date.today().strftime('%d.%m.%Y'))


        # Sva polja su obavezna osim eksplicitno izuzetih
        optional_fields = {
            'order_date', 'order_number', 'start_sequence', 'vehicle', 'other_vehicle',
            'transport_type', 'is_weekly', 'employee', 'other_employee_name', 'employee_type'
        }
        for field_name, field in self.fields.items():
            if field_name not in optional_fields:
                field.required = True

        if self.instance and self.instance.pk:
            if self.instance.vehicle:
                self.initial['transport_type'] = 'ims'
            elif self.instance.other_vehicle:
                self.initial['transport_type'] = 'other'
        elif not self.is_bound:
            self.initial.setdefault('transport_type', 'ims')

        if self.instance and getattr(self.instance, 'employee', None):
            self.initial.setdefault('employee_type', 'ims')
        elif self.instance and getattr(self.instance, 'other_employee_name', None):
            self.initial.setdefault('employee_type', 'other')
        elif not self.is_bound:
            self.initial.setdefault('employee_type', 'ims')

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('order_date'):
            if self.instance and self.instance.pk and self.instance.order_date:
                cleaned['order_date'] = self.instance.order_date
            else:
                cleaned['order_date'] = date.today()
        job_code = cleaned.get('job_code')
        travel_date = cleaned.get('travel_date')
        start_sequence = cleaned.get('start_sequence')
        vehicle = cleaned.get('vehicle')
        other_vehicle = cleaned.get('other_vehicle')
        transport_type = cleaned.get('transport_type')

        if vehicle and other_vehicle:
            self.add_error('vehicle', "Možeš izabrati samo jedno prevozno sredstvo.")
            self.add_error('other_vehicle', "Možeš uneti samo jedno prevozno sredstvo.")
        elif not vehicle and not other_vehicle:
            self.add_error('vehicle', "Obavezno je uneti vozilo (Auto IMS) ili ostalo prevozno sredstvo.")
            self.add_error('other_vehicle', "Obavezno je uneti vozilo (Auto IMS) ili ostalo prevozno sredstvo.")

        if transport_type == 'ims' and other_vehicle:
            self.add_error('other_vehicle', "Kada je izabrano Auto IMS, polje 'Ostalo' mora biti prazno.")
        if transport_type == 'other' and vehicle:
            self.add_error('vehicle', "Kada je izabrano Ostalo, polje 'Vozilo' mora biti prazno.")

        employee_type = cleaned.get('employee_type') or 'ims'
        employee = cleaned.get('employee')
        other_employee_name = cleaned.get('other_employee_name')

        if employee_type == 'ims':
            if not employee:
                self.add_error('employee', "Obavezno izaberi zaposlenog iz IMS.")
            cleaned['other_employee_name'] = None
        elif employee_type == 'other':
            if not other_employee_name:
                self.add_error('other_employee_name', "Unesi ime zaposlenog.")
            cleaned['employee'] = None

        if job_code and travel_date:
            center_code = getattr(job_code, 'center', None)
            year = travel_date.year
            if center_code:
                center_code = str(center_code).strip()
                prefix = f"{center_code}/{year}-"
                exists = PutniNalog.objects.filter(
                    order_number__startswith=prefix
                ).exists()
                has_any_for_center = PutniNalog.objects.filter(
                    order_number__startswith=f"{center_code}/"
                ).exists()
                if not exists and not start_sequence and not has_any_for_center:
                    self.add_error(
                        'start_sequence',
                        "Unesi početni broj za ovaj centar/godinu (ne postoji prethodni broj)."
                    )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        job_code = self.cleaned_data.get('job_code')
        travel_date = self.cleaned_data.get('travel_date')
        start_sequence = self.cleaned_data.get('start_sequence')
        if start_sequence:
            instance._start_sequence = start_sequence

        if commit:
            instance.save()
            self.save_m2m()
        return instance


class VehicleTravelOrderForm(forms.ModelForm):
    pn_number = forms.IntegerField(
        label="PN broj",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo",
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Zaposleni",
    )
    start_mileage = forms.IntegerField(
        required=False,
        label="Početna kilometraža",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'km'}),
    )

    class Meta:
        model = VehicleTravelOrder
        fields = ['pn_number', 'employee', 'vehicle', 'start_mileage']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, "employee", None):
            inactive_employee = Employee.objects.filter(
                pk=self.instance.employee_id,
                is_active=False
            )
            if inactive_employee.exists():
                self.fields['employee'].queryset = (
                    self.fields['employee'].queryset | inactive_employee
                )
        if not self.instance.pk:
            last_number = (
                VehicleTravelOrder.objects.order_by('-pn_number')
                .values_list('pn_number', flat=True)
                .first()
                or 0
            )
            self.initial.setdefault('pn_number', last_number + 1)
        self.fields['pn_number'].disabled = True


class VehicleTravelOrderCloseForm(forms.ModelForm):
    closed_at = forms.DateField(
        required=True,
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum zatvaranja",
    )
    end_mileage = forms.IntegerField(
        required=False,
        label="Krajnja kilometraža",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'km'}),
    )

    class Meta:
        model = VehicleTravelOrder
        fields = ['closed_at', 'end_mileage']
class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = '__all__'

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = '__all__'

class KvarForm(forms.ModelForm):
    VAN_IMS_CHOICES = [
        ("False", "IMS garaza"),
        ("True", "Van IMS-a"),
    ]
    WORK_TYPE_CHOICES = [
        ("mali_servis", "Mali servis"),
        ("veliki_servis", "Veliki servis"),
        ("popravka", "Popravka"),
    ]

    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    work_type = forms.ChoiceField(
        choices=WORK_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Vrsta intervencije",
        initial="popravka"
    )
    kilometraza = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Kilometraza"
    )
    opis = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Opis kvara"
    )
    napomena = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Napomena"
    )
    van_ims = forms.TypedChoiceField(
        choices=VAN_IMS_CHOICES,
        coerce=lambda val: val == "True",
        empty_value=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Popravka van IMS-a"
    )

    class Meta:
        model = Kvar
        fields = ["vehicle", "work_type", "kilometraza", "opis", "napomena", "van_ims"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default na "False" (IMS gara�a) ako nije zadato
        if self.initial.get("van_ims") is None:
            self.initial["van_ims"] = "False"


class KvarPartForm(forms.ModelForm):
    class Meta:
        model = KvarPart
        fields = ["name", "quantity", "uom"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Naziv dela"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "uom": forms.TextInput(attrs={"class": "form-control", "placeholder": "kom/l/kg"}),
        }


class ProcurementRequestForm(forms.ModelForm):
    class Meta:
        model = ProcurementRequest
        fields = ["job_code", "note"]
        widgets = {
            "job_code": forms.Select(attrs={"class": "form-select"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            default_oj = OrganizationalUnit.objects.filter(code="832111").first()
        except Exception:
            default_oj = None
        if default_oj and not self.initial.get("job_code") and not getattr(self.instance, "job_code_id", None):
            self.initial["job_code"] = default_oj.pk


class ProcurementItemForm(forms.ModelForm):
    class Meta:
        model = ProcurementItem
        fields = ["name", "uom", "quantity", "note"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Naziv materijala / usluge"}),
            "uom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Jedinica mere"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "note": forms.TextInput(attrs={"class": "form-control", "placeholder": "Napomena (opciono)"}),
        }

class ServiceTransactionForm(forms.ModelForm):
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )

    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    datum = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    nije_garaza = models.BooleanField(
        default=True,
        choices=YES_NO_CHOICES,  # Dodato choices
        verbose_name=_("Da li se polisa obnavlja?")
    )
    class Meta:
        model = ServiceTransaction
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.datum:
                self.initial['datum'] = self.instance.datum.strftime('%d.%m.%Y')

        # # Prolazi kroz sva polja u formi i postavlja ih kao obavezna
        # for field_name, field in self.fields.items():
        #     field.required = True


class DraftServiceTransactionForm(forms.ModelForm):
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )

    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    datum = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    nije_garaza = models.BooleanField(
        default=True,
        choices=YES_NO_CHOICES,  # Dodato choices
        verbose_name=_("Da li se polisa obnavlja?")
    )
    class Meta:
        model = DraftServiceTransaction
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.datum:
                self.initial['datum'] = self.instance.datum.strftime('%d.%m.%Y')

        if not self.initial.get('sif_vrs') and not getattr(self.instance, 'sif_vrs', None):
            self.initial['sif_vrs'] = 'EUF'

        # Prolazi kroz sva polja u formi i postavlja ih kao obavezna
        for field_name, field in self.fields.items():
            field.required = False


class ServiceFixingFilterForm(forms.Form):
    datum_od = forms.DateField(
        required=False,
        label="Datum od",
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    )
    datum_do = forms.DateField(
        required=False,
        label="Datum do",
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    )
    partner = forms.CharField(
        required=False,
        label="Naziv partnera"
    )
    nije_garaza = forms.BooleanField(
        required=False,
        label="Samo servisi van garaže"
    )


class RequisitionForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    kvar = forms.ModelChoiceField(
        queryset=Kvar.objects.filter(van_ims=False),
        required=False,
        widget=Select2Widget(attrs={'class': 'select2-method', 'data-placeholder': 'Izaberi IMS kvar'}),
        label="Kvar (IMS)"
    )
    datum_trebovanja = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    class Meta:
        model = Requisition
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.datum_trebovanja:
                self.initial['datum_trebovanja'] = self.instance.datum_trebovanja.strftime('%d.%m.%Y')
        # Prolazi kroz sva polja u formi i postavlja ih kao obavezna osim Boolean polja
        for field_name, field in self.fields.items():
            if not isinstance(field, forms.BooleanField):  # Ignoriše Boolean polja
                field.required = True

class DraftRequisitionForm(forms.ModelForm):
    YES_NO_CHOICES = (
        (True, _("Ne")),
        (False, _("Da")),
    )


    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Vozilo"
    )
    datum_trebovanja = forms.DateField(
        widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control js-date'}),
        input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
        label="Datum"
    )
    mesec_unosa = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Mesec unosa"
    )
    popravka_kategorija = forms.ModelChoiceField(
        queryset=ServiceType.objects.all(),
        widget=Select2Widget(attrs={'class': 'select2-method'}),
        label="Kategorija popravke"
    )
    kvar = forms.ModelChoiceField(
        queryset=Kvar.objects.filter(van_ims=False),
        required=False,
        widget=Select2Widget(attrs={'class': 'select2-method', 'data-placeholder': 'Izaberi IMS kvar'}),
        label="Kvar (IMS)"
    )
    
    kilometraza = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Kilometraža"
    )

    nije_garaza = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Izaberite opciju: 'Da' ako se odnosi na važnu napomenu, ili ostavite prazno.",
        label="Garaža"
    )

    napomena = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Napomena"
    )

    class Meta:
        model = DraftRequisition
        fields = ['vehicle','datum_trebovanja', 'mesec_unosa', 'popravka_kategorija', 'kilometraza', 'nije_garaza', 'napomena', 'kvar']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Check if instance is being updated
            if self.instance.datum_trebovanja:
                self.initial['datum_trebovanja'] = self.instance.datum_trebovanja.strftime('%d.%m.%Y')

        # Prolazi kroz sva polja u formi i postavlja ih kao obavezna
        for field_name, field in self.fields.items():
            field.required = False



from django import forms

class OMVPutnickaFilterForm(forms.Form):
    GODINA_CHOICES = [(str(y), str(y)) for y in range(2020, 2031)]
    MESEC_CHOICES = [(str(m), str(m)) for m in range(1, 13)]
    POLOVINA_CHOICES = [
        ('1', 'Prva polovina'),
        ('2', 'Druga polovina'),
    ]

    godina = forms.ChoiceField(choices=GODINA_CHOICES, required=False, label='Godina')
    mesec = forms.ChoiceField(choices=MESEC_CHOICES, required=False, label='Mesec')
    polovina = forms.ChoiceField(choices=POLOVINA_CHOICES, required=False, label='Polovina meseca')


class PutnickaFilterForm(forms.Form):
    GODINA_CHOICES = [(str(y), str(y)) for y in range(2020, 2031)]
    MESEC_CHOICES = [(str(m), str(m)) for m in range(1, 13)]
    POLOVINA_CHOICES = [
        ('1', 'Prva polovina'),
        ('2', 'Druga polovina'),
    ]

    godina = forms.ChoiceField(choices=GODINA_CHOICES, required=False, label='Godina')
    mesec = forms.ChoiceField(choices=MESEC_CHOICES, required=False, label='Mesec')
    polovina = forms.ChoiceField(choices=POLOVINA_CHOICES, required=False, label='Polovina meseca')



from django import forms
from .models import Insurance, DraftInsurance

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
