from django import forms
from django.forms import inlineformset_factory
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from .models import Contract, ContractParty, ContractType, Partner


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = [
            "name",
            "partner_type",
            "residency",
            "external_sif_par",
            "pib",
            "maticni_broj",
            "jmbg",
            "passport_number",
            "foreign_tax_id",
            "country",
            "city",
            "address",
            "email",
            "phone",
            "contact_person",
            "note",
            "is_active",
        ]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
            "partner_type": Select2Widget(attrs={"class": "select2-method"}),
            "residency": Select2Widget(attrs={"class": "select2-method"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.Select)):
                field.widget.attrs.setdefault("class", "form-control")
            elif isinstance(field.widget, Select2Widget):
                existing = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing} select2-method".strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")


class ContractTypeForm(forms.ModelForm):
    class Meta:
        model = ContractType
        fields = ["code", "name", "description", "is_active", "sort_order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.Select)):
                field.widget.attrs.setdefault("class", "form-control")
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")


class ContractForm(forms.ModelForm):
    contract_date = localized_date_field(label="Datum ugovora")
    valid_from = localized_date_field(label="Važi od", required=False)
    valid_to = localized_date_field(label="Važi do", required=False)

    class Meta:
        model = Contract
        fields = [
            "kind",
            "contract_type",
            "parent_contract",
            "contract_number",
            "title",
            "subject",
            "contract_date",
            "valid_from",
            "valid_to",
            "value",
            "currency",
            "status",
            "file",
            "note",
        ]
        widgets = {
            "subject": forms.Textarea(attrs={"rows": 3}),
            "note": forms.Textarea(attrs={"rows": 3}),
            "kind": Select2Widget(attrs={"class": "select2-method"}),
            "status": Select2Widget(attrs={"class": "select2-method"}),
            "currency": Select2Widget(attrs={"class": "select2-method"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contract_type"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["contract_type"].queryset = ContractType.objects.filter(is_active=True)
        self.fields["parent_contract"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["parent_contract"].queryset = Contract.objects.filter(kind=Contract.MAIN)
        self.fields["parent_contract"].required = False

        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, Select2Widget):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} select2-method".strip()
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            elif not isinstance(widget, (forms.CheckboxInput, Select2Widget, forms.FileInput, forms.Textarea)):
                widget.attrs.setdefault("class", "form-control")

        # Textarea class
        for name in ("subject", "note"):
            self.fields[name].widget.attrs.setdefault("class", "form-control")


class AnnexForm(ContractForm):
    def __init__(self, *args, parent_contract=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kind"].initial = Contract.ANNEX
        self.fields["kind"].widget = forms.HiddenInput()
        self.fields["kind"].required = False

        if parent_contract is not None:
            self.fields["parent_contract"].initial = parent_contract
            self.fields["parent_contract"].widget = forms.HiddenInput()
            self.fields["parent_contract"].required = True

    def clean_kind(self):
        return Contract.ANNEX


class ContractPartyForm(forms.ModelForm):
    class Meta:
        model = ContractParty
        fields = ["partner", "role", "note"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["partner"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["partner"].queryset = Partner.objects.filter(is_active=True)
        self.fields["role"].widget.attrs.setdefault("class", "form-select contract-party-role-select")
        self.fields["note"].widget.attrs.setdefault("class", "form-control")
        self.fields["note"].required = False


ContractPartyFormSet = inlineformset_factory(
    Contract,
    ContractParty,
    form=ContractPartyForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)
