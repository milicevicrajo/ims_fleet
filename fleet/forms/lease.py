from django import forms

from core.form_fields import localized_date_field

from ..models import Lease


class LeaseForm(forms.ModelForm):
    start_date = localized_date_field(label="Datum početka")
    end_date = localized_date_field(label="Datum završetka")

    class Meta:
        model = Lease
        fields = "__all__"
        widgets = {
            "lease_type": forms.Select(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
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
