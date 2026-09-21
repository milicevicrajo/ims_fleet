from datetime import date
from django import forms
from django.core.validators import validate_email
from django.utils import timezone
from .forms import ReportDateField
from .models import BankContact, BankAccountRule, BankBillPlacement


class BankPeriodForm(forms.Form):
    date_from = ReportDateField(label="Od")
    date_to = ReportDateField(label="Do")

    def __init__(self, data=None, **kwargs):
        today = timezone.localdate()
        data = data.copy() if data is not None else {}
        data.setdefault("date_from", date(today.year, 1, 1).isoformat())
        data.setdefault("date_to", today.isoformat())
        super().__init__(data, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean(self):
        values = super().clean()
        start, end = values.get("date_from"), values.get("date_to")
        if start and end and (start > end or start.year != end.year or start.year < 2025 or end > timezone.localdate()):
            raise forms.ValidationError("Izaberite period unutar jedne godine, od 2025. do danas.")
        return values


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 3


class BankContactForm(StyledModelForm):
    class Meta:
        model = BankContact
        fields = ["segment", "name", "position", "email", "phone", "shared_emails", "note"]

    def clean_shared_emails(self):
        raw = self.cleaned_data["shared_emails"]
        emails = [s.strip() for s in raw.replace(";", "\n").replace(",", "\n").splitlines() if s.strip()]
        for email in emails:
            validate_email(email)
        return "\n".join(dict.fromkeys(emails))

    def clean(self):
        values = super().clean()
        if not any(values.get(key) for key in ("name", "email", "phone", "shared_emails")):
            raise forms.ValidationError("Unesite osobu, telefon ili email segmenta.")
        return values


class BankAccountRuleForm(StyledModelForm):
    bank_code = forms.TypedChoiceField(label="Banka", coerce=int, empty_value=None, required=False)
    account = forms.ChoiceField(label="Konto")

    class Meta:
        model = BankAccountRule
        fields = ["account", "bank_code", "segment", "note"]

    def __init__(self, *args, banks, accounts, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bank_code"].choices = [("", "Bez veze sa jednom bankom")] + [(b["code"], f'{b["code"]} — {b["name"]}') for b in banks]
        self.fields["account"].choices = [(code, f"{code} — {name}") for code, name in accounts]

    def clean(self):
        values = super().clean()
        code = values.get("account", "")
        if values.get("bank_code") and (code == "24100" or code.startswith(("2419", "2449", "243", "246"))):
            raise forms.ValidationError("Zbirno konto i prelazni računi ne mogu se pripisati jednoj banci.")
        if values.get("segment") == "excluded" and values.get("bank_code"):
            raise forms.ValidationError("Konto označeno kao van bankarskih računa ne može imati banku.")
        return values


class BankBillPlacementForm(StyledModelForm):
    delivered_on = ReportDateField(label="Datum predaje")
    returned_on = ReportDateField(label="Datum vraćanja", required=False)

    class Meta:
        model = BankBillPlacement
        fields = ["bill", "incoming_bill", "delivered_on", "returned_on", "note"]
        labels = {"bill": "Menica iz registra menica", "incoming_bill": "Menica iz posebne ulazne evidencije"}

    def clean(self):
        values = super().clean()
        if bool(values.get("bill")) == bool(values.get("incoming_bill")):
            raise forms.ValidationError("Izaberite jednu menicu iz jedne od dve evidencije.")
        start, end = values.get("delivered_on"), values.get("returned_on")
        if start and end and end < start:
            raise forms.ValidationError("Datum vraćanja ne može biti pre predaje.")
        return values
