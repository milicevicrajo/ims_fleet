from django import forms


class ReportPeriodFilterForm(forms.Form):
    GODINA_CHOICES = [(str(year), str(year)) for year in range(2020, 2031)]
    MESEC_CHOICES = [(str(month), str(month)) for month in range(1, 13)]
    POLOVINA_CHOICES = [
        ("1", "Prva polovina"),
        ("2", "Druga polovina"),
    ]

    godina = forms.ChoiceField(choices=GODINA_CHOICES, required=False, label="Godina")
    mesec = forms.ChoiceField(choices=MESEC_CHOICES, required=False, label="Mesec")
    polovina = forms.ChoiceField(choices=POLOVINA_CHOICES, required=False, label="Polovina meseca")


class OMVPutnickaFilterForm(ReportPeriodFilterForm):
    pass


class PutnickaFilterForm(ReportPeriodFilterForm):
    pass
