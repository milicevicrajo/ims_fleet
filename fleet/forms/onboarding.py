from django import forms
from django.utils import timezone

from core.form_fields import localized_date_field
from core.models import OrganizationalUnit
from hr.models import Employee
from ugovori.models import Contract
from ..models import Vehicle, TrafficCard, Lease, VehicleHolding


IDENTITY_FIELDS = ['photo', 'category', 'chassis_number', 'brand', 'model', 'year_of_manufacture', 'inventory_number']
TECHNICAL_FIELDS = ['color', 'homologation_number', 'first_registration_date', 'fuel_type', 'engine_number', 'engine_volume', 'engine_power', 'weight', 'load_capacity', 'maximum_permissible_weight', 'number_of_axles', 'number_of_seats', 'service_interval', 'description']
PURCHASE_FIELDS = ['purchase_date', 'purchase_value', 'partner_code', 'partner_name', 'invoice_number']
CARD_FIELDS = ['registration_number', 'issue_date', 'valid_until', 'registration_valid_until', 'traffic_card_number', 'serial_number', 'owner', 'traffic_card_pdf', 'traffic_card_front_image', 'traffic_card_back_image']


class VehicleIdentityForm(forms.ModelForm):
    photo = forms.ImageField(label='Slika vozila', required=False, help_text='Opciono. JPG, PNG ili WebP, do 5 MB.', widget=forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}))
    remove_photo = forms.BooleanField(label='Ukloni prethodno izabranu sliku', required=False)

    class Meta:
        model = Vehicle
        fields = IDENTITY_FIELDS

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Slika može imati najviše 5 MB.')
            if photo.image.format not in ('JPEG', 'PNG', 'WEBP'):
                raise forms.ValidationError('Izaberite JPG, PNG ili WebP sliku.')
        return photo

    def clean(self):
        data = super().clean()
        if data.get('remove_photo'):
            data['photo'] = None
        return data

    def clean_chassis_number(self):
        value = self.cleaned_data['chassis_number'].strip().upper()
        if Vehicle.objects.filter(chassis_number__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Vozilo sa ovom šasijom već postoji. Otvorite njegovu karticu.')
        return value

    def clean_inventory_number(self):
        value = (self.cleaned_data.get('inventory_number') or '').strip() or None
        if value and Vehicle.objects.filter(inventory_number__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Inventarski broj već postoji.')
        return value

    def clean_year_of_manufacture(self):
        year = self.cleaned_data['year_of_manufacture']
        if not 1886 <= year <= timezone.localdate().year + 1:
            raise forms.ValidationError('Proverite godinu proizvodnje.')
        return year


class VehicleTechnicalForm(forms.ModelForm):
    first_registration_date = localized_date_field(label='Datum prve registracije', required=False)

    class Meta:
        model = Vehicle
        fields = TECHNICAL_FIELDS
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, category=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category or self.instance.category
        if self.category == Vehicle.Category.TRAILER:
            for key in ['fuel_type', 'engine_number', 'engine_volume', 'engine_power', 'number_of_seats', 'service_interval']:
                self.fields.pop(key, None)

    def clean_engine_number(self):
        return (self.cleaned_data.get('engine_number') or '').strip() or None

    def clean(self):
        data = super().clean()
        for key in ['engine_volume', 'engine_power', 'weight', 'load_capacity', 'maximum_permissible_weight', 'number_of_axles', 'number_of_seats', 'service_interval']:
            if data.get(key) is not None and data[key] < 0:
                self.add_error(key, 'Vrednost ne može biti negativna.')
        if data.get('weight') is not None and data.get('maximum_permissible_weight') is not None and data['weight'] > data['maximum_permissible_weight']:
            self.add_error('maximum_permissible_weight', 'Maksimalna masa ne može biti manja od mase vozila.')
        if data.get('first_registration_date') and data['first_registration_date'] > timezone.localdate():
            self.add_error('first_registration_date', 'Datum prve registracije ne može biti u budućnosti.')
        if (data.get('fuel_type') or '').strip().lower() in {'električno', 'elektricno', 'electric', 'električna energija'}:
            data['engine_volume'] = None
        return data


class VehicleBasisForm(forms.Form):
    basis = forms.ChoiceField(label='Osnov raspolaganja', choices=VehicleHolding.BASIS_CHOICES)
    start_date = localized_date_field(label='Datum početka raspolaganja')
    evidence = forms.CharField(label='Dokument / osnov sticanja ili preuzimanja', max_length=255, required=False)
    financing = forms.ChoiceField(label='Finansiranje nabavke', choices=VehicleHolding.FINANCING_CHOICES, required=False)
    financing_contract = forms.ModelChoiceField(label='Postojeći ugovor o finansiranju', queryset=Contract.objects.all(), required=False)
    purchase_date = localized_date_field(label='Datum nabavke', required=False)
    purchase_value = forms.DecimalField(label='Nabavna vrednost (RSD)', max_digits=12, decimal_places=2, min_value=0, required=False)
    partner_code = forms.CharField(label='Šifra dobavljača / davaoca lizinga ili najma', max_length=20, required=False)
    partner_name = forms.CharField(label='Naziv dobavljača / davaoca lizinga ili najma', max_length=100, required=False)
    invoice_number = forms.CharField(label='Broj fakture nabavke', max_length=50, required=False)
    lease_type = forms.ChoiceField(label='Vrsta lizinga / najma', choices=[('', 'Izaberite')] + Lease.LEASE_TYPE_CHOICES, required=False)
    contract_number = forms.CharField(label='Broj ugovora o lizingu / najmu', max_length=50, required=False)
    contract = forms.ModelChoiceField(label='Postojeći ugovor iz evidencije Ugovori', queryset=Contract.objects.all(), required=False)
    end_date = localized_date_field(label='Datum završetka ugovora', required=False)
    current_payment_amount = forms.DecimalField(label='Iznos naknade / otplate (RSD)', help_text='Za dugoročni najam: mesečna naknada. Za operativni: ukupan iznos za period. Finansijski lizing: iznos rate; kamata se vodi odvojeno.', max_digits=10, decimal_places=2, min_value=0, required=False)
    note = forms.CharField(label='Napomena', widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def clean(self):
        data = super().clean()
        if data.get('basis') == 'contract':
            contract = data.get('contract')
            if contract:
                if not data.get('contract_number'):
                    data['contract_number'] = contract.contract_number
                if len(data['contract_number']) > 50:
                    self.add_error('contract_number', 'Broj ugovora u evidenciji flote može imati najviše 50 znakova.')
                if not data.get('end_date'):
                    data['end_date'] = contract.valid_to
                if data.get('start_date') and contract.valid_from and data['start_date'] < contract.valid_from:
                    self.add_error('start_date', 'Početak raspolaganja je pre početka ugovora.')
                if data.get('end_date') and contract.valid_to and data['end_date'] > contract.valid_to:
                    self.add_error('end_date', 'Period raspolaganja prelazi rok ugovora.')
            for key in ['partner_code', 'partner_name', 'lease_type', 'contract_number', 'end_date', 'current_payment_amount']:
                if data.get(key) in (None, ''):
                    self.add_error(key, 'Obavezno za korišćenje po ugovoru.')
            if data.get('start_date') and data.get('end_date') and data['end_date'] < data['start_date']:
                self.add_error('end_date', 'Završetak ne može biti pre početka.')
            if contract and contract.currency != 'RSD':
                self.add_error('contract', 'Postojeći obračun flote koristi RSD. Potrebno je usaglasiti valutni obračun pre povezivanja ovog ugovora.')
            data['financing'] = ''
            data['financing_contract'] = None
            for key in ['purchase_date', 'purchase_value', 'invoice_number']:
                data[key] = None
        else:
            if not data.get('financing'):
                self.add_error('financing', 'Izaberite način finansiranja nabavke.')
            if data.get('financing') != 'credit':
                data['financing_contract'] = None
            for key in ['lease_type', 'contract_number', 'end_date', 'current_payment_amount', 'contract']:
                data[key] = None
        return data


class OnboardingTrafficCardForm(forms.ModelForm):
    add_document = forms.BooleanField(label='Unosim saobraćajnu sada', required=False, initial=True)
    issue_date = localized_date_field(label='Datum izdavanja', required=False)
    valid_until = localized_date_field(label='Rok važenja saobraćajne, ako je naveden', required=False)
    registration_valid_until = localized_date_field(label='Registracija važi do', required=False)

    class Meta:
        model = TrafficCard
        fields = CARD_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
        self.order_fields(['add_document'] + CARD_FIELDS)

    def clean_registration_number(self):
        from ..support.vehicle import format_license_plate
        value = self.cleaned_data.get('registration_number') or ''
        return format_license_plate(value) if value else ''

    def clean(self):
        data = super().clean()
        if data.get('add_document'):
            for key in ['registration_number', 'issue_date', 'traffic_card_number', 'serial_number', 'owner']:
                if not data.get(key):
                    self.add_error(key, 'Obavezno pri unosu saobraćajne.')
            if data.get('registration_number') and TrafficCard.objects.filter(registration_number=data['registration_number']).exists():
                self.add_error('registration_number', 'Tablice su već evidentirane. Proverite postojeće vozilo.')
        else:
            for key in CARD_FIELDS:
                data[key] = None if key not in ['registration_number', 'traffic_card_number', 'serial_number', 'owner'] else ''
        return data


class VehicleAssignmentForm(forms.Form):
    organizational_unit = forms.ModelChoiceField(label='Šifra posla / organizaciona jedinica', queryset=OrganizationalUnit.objects.all(), required=False)
    assigned_date = localized_date_field(label='Datum dodele šifre posla', required=False)
    assign_employee = forms.BooleanField(label='Odmah zaduži zaposlenog', required=False)
    employee = forms.ModelChoiceField(label='Zaposleni', queryset=Employee.objects.filter(is_active=True), required=False)
    created_at = localized_date_field(label='Datum preuzimanja vozila', required=False)
    start_mileage = forms.IntegerField(label='Kilometraža pri preuzimanju', min_value=0, required=False)

    def clean(self):
        data = super().clean()
        if data.get('organizational_unit') and not data.get('assigned_date'):
            self.add_error('assigned_date', 'Unesite datum od kog važi šifra posla.')
        if data.get('assign_employee'):
            for key in ['employee', 'created_at', 'start_mileage']:
                if data.get(key) is None:
                    self.add_error(key, 'Obavezno za prvo zaduženje.')
        else:
            for key in ['employee', 'created_at', 'start_mileage']:
                data[key] = None
        return data


class VehicleHoldingForm(forms.ModelForm):
    start_date = localized_date_field(label='Važi od')
    end_date = localized_date_field(label='Važi do (uključivo)', required=False)

    class Meta:
        model = VehicleHolding
        fields = ['basis', 'start_date', 'end_date', 'lease', 'financing', 'financing_contract', 'evidence', 'note']

    def __init__(self, *args, vehicle, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.vehicle = vehicle
        self.fields['lease'].queryset = Lease.objects.filter(vehicle=vehicle)
