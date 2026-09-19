from django import forms
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field

from ..models import Policy, Vehicle
from .layout import FieldsetMixin


class PolicyForm(FieldsetMixin, forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Vozilo",
    )
    issue_date = localized_date_field(
        label="Datum izdavanja",
        help_text="Datum kada je polisa izdata. Ne mora biti isti kao početak važenja.",
    )
    start_date = localized_date_field(label="Datum početka", help_text="Prvi dan važenja polise.")
    end_date = localized_date_field(
        label="Datum završetka",
        help_text="Poslednji dan važenja — taj dan je uključen. Premija se u trošak deli po danima ovog perioda.",
    )

    fieldsets = (
        ('Vozilo i osiguravač', None, ('vehicle', 'partner_pib', 'partner_name')),
        ('Faktura', 'Podaci fakture kojom je polisa naplaćena.',
         ('invoice_id', 'invoice_number')),
        ('Polisa', 'Šta je osigurano i koliko dugo.',
         ('insurance_type', 'policy_number', 'issue_date', 'start_date', 'end_date', 'is_renewable')),
        ('Iznosi', 'Premija je ukupan iznos polise. Rate su način plaćanja te iste premije — ne dodaju se na nju.',
         ('premium_amount', 'number_of_installments', 'first_installment_amount', 'other_installments_amount')),
    )

    class Meta:
        model = Policy
        fields = "__all__"
        help_texts = {
            "invoice_id": "Identifikator fakture iz knjigovodstva (broj). Mora biti jedinstven — po njemu se prepoznaje ista polisa pri ponovnom uvozu.",
            "invoice_number": "Broj fakture onako kako piše na dokumentu.",
            "insurance_type": "Na primer: autoodgovornost, kasko, nezgoda. Upisuje se slobodnim tekstom, pa pišite dosledno.",
            "premium_amount": "Ukupan iznos premije za ceo period važenja polise.",
            "number_of_installments": "Na koliko rata je premija podeljena. Upišite 1 ako se plaća odjednom.",
            "first_installment_amount": "Iznos prve rate. Deo je premije, ne dodatni trošak.",
            "other_installments_amount": "Iznos JEDNE od preostalih rata, ne njihov zbir.",
            "is_renewable": "Označite ako se polisa obnavlja po isteku.",
            "partner_pib": "PIB osiguravajućeg društva.",
        }

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
