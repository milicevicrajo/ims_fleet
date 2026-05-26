from django import forms
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from core.models import OrganizationalUnit
from fleet.models import ProcurementRequest, Vehicle
from ugovori.models import Contract, Partner

from .models import (
    ProcurementCase,
    ProcurementContractLink,
    ProcurementInvoiceLink,
    ProcurementItem,
    ProcurementStatusLog,
    PurchaseOrder,
)


def _style_fields(fields):
    for field in fields.values():
        widget = field.widget
        if isinstance(widget, Select2Widget):
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} select2-method".strip()
        elif isinstance(widget, forms.Select):
            widget.attrs.setdefault("class", "form-select")
        elif isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "form-check-input")
        else:
            widget.attrs.setdefault("class", "form-control")


class ProcurementCaseForm(forms.ModelForm):
    needed_by = localized_date_field(label="Potrebno do", required=False)

    class Meta:
        model = ProcurementCase
        fields = [
            "case_type",
            "status",
            "title",
            "description",
            "job_code",
            "supplier",
            "contract",
            "vehicle",
            "fleet_procurement_request",
            "responsible",
            "estimated_value",
            "currency",
            "needed_by",
            "note",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "note": forms.Textarea(attrs={"rows": 3}),
            "case_type": Select2Widget(attrs={"class": "select2-method"}),
            "status": Select2Widget(attrs={"class": "select2-method"}),
            "currency": Select2Widget(attrs={"class": "select2-method"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["job_code"].queryset = OrganizationalUnit.objects.all().order_by("code")
        self.fields["job_code"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["supplier"].queryset = Partner.objects.filter(is_active=True).order_by("name")
        self.fields["supplier"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["contract"].queryset = Contract.objects.all().order_by("-contract_date")
        self.fields["contract"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["vehicle"].queryset = Vehicle.objects.all().order_by("brand", "model")
        self.fields["vehicle"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["fleet_procurement_request"].queryset = ProcurementRequest.objects.all().order_by("-created_at")
        self.fields["fleet_procurement_request"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["responsible"].widget = Select2Widget(attrs={"class": "select2-method"})
        _style_fields(self.fields)


class ProcurementItemForm(forms.ModelForm):
    class Meta:
        model = ProcurementItem
        fields = ["name", "uom", "quantity", "estimated_unit_price", "note"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Naziv artikla/usluge"}),
            "uom": forms.TextInput(attrs={"placeholder": "kom/l/kg"}),
            "quantity": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "estimated_unit_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_fields(self.fields)


class EufInvoiceLinkForm(forms.Form):
    procurement_case = forms.ModelChoiceField(
        queryset=ProcurementCase.objects.exclude(status=ProcurementCase.Status.COMPLETED).order_by("-created_at"),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Predmet nabavke",
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        label="Napomena",
    )


class ProcurementContractLinkForm(forms.ModelForm):
    class Meta:
        model = ProcurementContractLink
        fields = ["contract", "invoice_link", "note"]

    def __init__(self, *args, procurement_case=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contract"].queryset = Contract.objects.all().order_by("-contract_date")
        self.fields["contract"].widget = Select2Widget(attrs={"class": "select2-method"})
        if procurement_case is not None:
            self.fields["invoice_link"].queryset = procurement_case.invoice_links.all()
        self.fields["invoice_link"].required = False
        self.fields["invoice_link"].widget = Select2Widget(attrs={"class": "select2-method"})
        _style_fields(self.fields)


class PurchaseOrderForm(forms.ModelForm):
    order_date = localized_date_field(label="Datum narudžbenice")

    class Meta:
        model = PurchaseOrder
        fields = [
            "procurement_case",
            "order_number",
            "order_date",
            "supplier",
            "contract",
            "status",
            "amount",
            "currency",
            "note",
        ]
        widgets = {
            "status": Select2Widget(attrs={"class": "select2-method"}),
            "currency": Select2Widget(attrs={"class": "select2-method"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, procurement_case=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["procurement_case"].queryset = ProcurementCase.objects.all().order_by("-created_at")
        self.fields["procurement_case"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["supplier"].queryset = Partner.objects.filter(is_active=True).order_by("name")
        self.fields["supplier"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["contract"].queryset = Contract.objects.all().order_by("-contract_date")
        self.fields["contract"].widget = Select2Widget(attrs={"class": "select2-method"})
        if procurement_case is not None:
            self.fields["procurement_case"].initial = procurement_case
            self.fields["procurement_case"].widget = forms.HiddenInput()
            self.fields["supplier"].initial = procurement_case.supplier
            self.fields["contract"].initial = procurement_case.contract
        _style_fields(self.fields)


class ProcurementStatusLogForm(forms.ModelForm):
    class Meta:
        model = ProcurementStatusLog
        fields = ["new_status", "comment"]
        widgets = {
            "new_status": Select2Widget(attrs={"class": "select2-method"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
