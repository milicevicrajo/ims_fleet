from django import forms
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field

from .models import Policy, Vehicle


class PolicyForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    issue_date = localized_date_field(label="Datum izdavanja")
    start_date = localized_date_field(label="Datum poÄetka")
    end_date = localized_date_field(label="Datum zavrÅ¡etka")

    class Meta:
        model = Policy
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.issue_date:
                self.initial["issue_date"] = self.instance.issue_date.strftime("%d.%m.%Y")
            if self.instance.start_date:
                self.initial["start_date"] = self.instance.start_date.strftime("%d.%m.%Y")
            if self.instance.end_date:
                self.initial["end_date"] = self.instance.end_date.strftime("%d.%m.%Y")

        for field_name, field in self.fields.items():
            field.required = True
