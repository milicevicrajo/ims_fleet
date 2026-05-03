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
