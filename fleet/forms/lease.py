from django import forms

from core.form_fields import localized_date_field

from ..models import Lease
from .layout import FieldsetMixin


class LeaseForm(FieldsetMixin, forms.ModelForm):
    start_date = localized_date_field(label="Datum početka")
    end_date = localized_date_field(
        label="Datum završetka",
        help_text="Poslednji dan važenja ugovora — taj dan je uključen.",
    )

    fieldsets = (
        ('Vozilo i ugovor', 'Na koje vozilo se ugovor odnosi i koji je to ugovor.',
         ('vehicle', 'contract_number', 'contract', 'lease_type')),
        ('Davalac lizinga / najma', None,
         ('partner_code', 'partner_name')),
        ('Trajanje', 'Oba datuma su uključena u period važenja.',
         ('start_date', 'end_date')),
        ('Iznos i knjiženje', 'Iznos ovde je samo evidencija. Za obračun troškova unosi se naknada sa periodom — vidi objašnjenje ispod iznosa.',
         ('current_payment_amount', 'job_code')),
        ('Napomena', None, ('note',)),
    )

    class Meta:
        model = Lease
        fields = "__all__"
        widgets = {
            "lease_type": forms.Select(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        help_texts = {
            "current_payment_amount": (
                "Za dugoročni najam: mesečna naknada. Za operativni lizing: ukupan iznos za period. "
                "Za finansijski lizing: iznos rate; kamata se vodi odvojeno. "
                "VAŽNO: obračun troškova NE koristi ovo polje, jer njegovo značenje nije potvrđeno. "
                "Naknada za obračun se unosi na ekranu „Namena, kriterijumi i evidencija“, "
                "gde se uz iznos bira i da li je mesečni ili ukupan."
            ),
            "job_code": "Šifra posla kao slobodan tekst, onako kako stoji u knjigovodstvu.",
            "contract": "Ako ugovor već postoji u evidenciji Ugovori, povežite ga — broj i rok se tada preuzimaju.",
            "partner_code": "Šifra partnera iz knjigovodstva.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.start_date:
                self.initial["start_date"] = self.instance.start_date.strftime("%d.%m.%Y")
            if self.instance.end_date:
                self.initial["end_date"] = self.instance.end_date.strftime("%d.%m.%Y")

    def clean(self):
        data = super().clean()
        start, end = data.get('start_date'), data.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'Završetak ne može biti pre početka.')
        if data.get('current_payment_amount') is not None and data['current_payment_amount'] < 0:
            self.add_error('current_payment_amount', 'Iznos ne može biti negativan.')
        if self.instance.pk:
            for holding in self.instance.holdings.all():
                if data.get('vehicle') and data['vehicle'].pk != holding.vehicle_id:
                    self.add_error('vehicle', 'Ugovor je povezan sa istorijom ovog vozila; ne može se premestiti.')
                if start and end and (holding.start_date < start or not holding.end_date or holding.end_date > end):
                    self.add_error('end_date', 'Najpre usaglasite period povezanog osnova raspolaganja.')
        return data
