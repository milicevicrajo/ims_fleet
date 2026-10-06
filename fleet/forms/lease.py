from django import forms

from core.form_fields import localized_date_field

from ..models import Lease
from .layout import FieldsetMixin
from .ugovor import UgovorField, poruka_iznosa, strana_valuta


class LeaseForm(FieldsetMixin, forms.ModelForm):
    start_date = localized_date_field(label="Datum početka")
    end_date = localized_date_field(
        label="Datum završetka",
        help_text="Poslednji dan važenja ugovora — taj dan je uključen.",
    )
    contract = UgovorField(
        label="Ugovor iz evidencije Ugovori", valuta_za="id_current_payment_amount",
        help_text="Pretraga po broju ili nazivu. Ugovor u stranoj valuti se povezuje, a iznos se unosi u dinarima.",
    )

    fieldsets = (
        ('Vozilo i ugovor', 'Na koje vozilo se ugovor odnosi i koji je to ugovor.',
         ('vehicle', 'contract_number', 'contract', 'lease_type')),
        ('Davalac lizinga / najma', None,
         ('partner_code', 'partner_name')),
        ('Trajanje', 'Oba datuma su uključena u period važenja.',
         ('start_date', 'end_date')),
        ('Iznos i knjiženje', 'Naknada se obračunava neposredno iz ovog ugovora i njegovog perioda važenja.',
         ('payment_basis', 'current_payment_amount', 'job_code')),
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
                "Izaberite da li unosite mesečni iznos ili ukupni iznos ugovora. "
                "Za finansijski lizing glavnica ne ulazi u trošak; kamata se vodi odvojeno."
            ),
            "job_code": "Šifra posla kao slobodan tekst, onako kako stoji u knjigovodstvu.",
            "partner_code": "Šifra partnera iz knjigovodstva.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.start_date:
                self.initial["start_date"] = self.instance.start_date.strftime("%d.%m.%Y")
            if self.instance.end_date:
                self.initial["end_date"] = self.instance.end_date.strftime("%d.%m.%Y")
        # Za ugovor u stranoj valuti poruka obaveznog iznosa kaže da se iznos unosi u dinarima.
        valuta = strana_valuta(self._izabran_ugovor())
        self.fields["current_payment_amount"].error_messages["required"] = (
            poruka_iznosa(valuta) if valuta else "Unesite iznos naknade u dinarima (RSD).")

    def _izabran_ugovor(self):
        pk = self.data.get(self.add_prefix("contract")) if self.is_bound else getattr(self.instance, "contract_id", None)
        return self.fields["contract"].queryset.filter(pk=pk).first() if str(pk or "").isdigit() else None

    def clean(self):
        data = super().clean()
        start, end = data.get('start_date'), data.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'Završetak ne može biti pre početka.')
        if data.get('current_payment_amount') is not None and data['current_payment_amount'] < 0:
            self.add_error('current_payment_amount', 'Iznos ne može biti negativan.')
        if data.get('lease_type') != 'finansijski' and not data.get('payment_basis'):
            self.add_error('payment_basis', 'Izaberite mesečni ili ukupni iznos ugovora.')
        if self.instance.pk and data.get('vehicle') and data['vehicle'].pk != self.instance.vehicle_id:
            # Ugovor je istorija raspolaganja tog vozila (vlasništvo = bez važećeg ugovora); ne premešta se.
            self.add_error('vehicle', 'Ugovor pripada istoriji raspolaganja ovog vozila; ne može se premestiti na drugo vozilo.')
        return data


class LeaseInterestForm(forms.Form):
    """Kamata finansijskog lizinga po kalendarskoj godini ugovora (stvarni iznos za tu godinu, RSD).

    Obračun deli upisanu kamatu na dane ugovora u toj godini (`lease_costs.interest_daily_amount`),
    pa se za delimičnu prvu i poslednju godinu upisuje stvarna kamata, bez preračuna na celu godinu.
    Prazno polje briše upis za tu godinu.
    """

    def __init__(self, *args, instance, **kwargs):
        super().__init__(*args, **kwargs)
        from ..support.lease_costs import lease_days_in_year

        self.lease = instance
        postojece = {r.year: r.interest_amount for r in instance.lease_interests.all()}
        for godina in range(instance.start_date.year, instance.end_date.year + 1):
            dana = lease_days_in_year(instance, godina)
            self.fields[f'godina_{godina}'] = forms.DecimalField(
                label=f'Kamata za {godina}. (RSD)', required=False, min_value=0, max_digits=12, decimal_places=2,
                initial=postojece.get(godina),
                help_text=f'Ugovor važi {dana} dana u {godina}.' + ('' if dana >= 365 else ' Upišite stvarnu kamatu za taj deo godine.'))

    def save(self):
        from ..models import LeaseInterest

        for naziv, iznos in self.cleaned_data.items():
            godina = int(naziv.removeprefix('godina_'))
            if iznos is None:
                LeaseInterest.objects.filter(lease=self.lease, year=godina).delete()
            else:
                LeaseInterest.objects.update_or_create(lease=self.lease, year=godina, defaults={'interest_amount': iznos})
        return self.lease
