from django import forms
from django.utils import timezone
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from core.models import OrganizationalUnit
from fleet.models import Vehicle
from ugovori.models import Contract, Partner

from .models import (
    EufItemSnapshot,
    GoodsSnapshot,
    ProcurementCase,
    ProcurementInvoice,
    ProcurementInvoiceContractLink,
    ProcurementItem,
    ProcurementStatusLog,
    PurchaseOrder,
)


PROCUREMENT_CASE_TYPE_CHOICES = [
    (ProcurementCase.CaseType.PROCUREMENT, "Zahtev za nabavku"),
    (ProcurementCase.CaseType.SERVICE, "Zahtev za uslugu"),
    (ProcurementCase.CaseType.EQUIPMENT, "Predlog za nabavku"),
]


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
    needed_by = localized_date_field(label="Datum zahteva", required=False)

    class Meta:
        model = ProcurementCase
        fields = [
            "case_type",
            "is_garage",
            "status",
            "title",
            "description",
            "job_code",
            "supplier",
            "vehicle",
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
        if not self.is_bound and not self.instance.pk:
            default_needed_by = timezone.localdate()
            self.initial.setdefault("needed_by", default_needed_by.strftime("%d.%m.%Y"))
        self.fields["case_type"].choices = PROCUREMENT_CASE_TYPE_CHOICES
        self.fields["job_code"].required = True
        self.fields["supplier"].required = False
        self.fields["job_code"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["job_code"].queryset = OrganizationalUnit.objects.all().order_by("code")
        self.fields["supplier"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["supplier"].queryset = Partner.objects.filter(is_active=True).order_by("name")
        self.fields["vehicle"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["vehicle"].queryset = Vehicle.objects.all().order_by("brand", "model")
        _style_fields(self.fields)

    def clean(self):
        cleaned_data = super().clean()
        is_garage = cleaned_data.get("is_garage")

        if not cleaned_data.get("needed_by"):
            cleaned_data["needed_by"] = timezone.localdate()
        if not is_garage:
            cleaned_data["vehicle"] = None
        return cleaned_data


class ProcurementItemForm(forms.ModelForm):
    class Meta:
        model = ProcurementItem
        fields = ["name", "uom", "quantity", "estimated_unit_price", "note"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Naziv artikla/usluge"}),
            "uom": forms.TextInput(attrs={"placeholder": "kom/l/kg"}),
            "quantity": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "estimated_unit_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "Napomena"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_fields(self.fields)


class ProcurementItemSourceLinkForm(forms.Form):
    source_type = forms.ChoiceField(
        required=False,
        label="Tip povezivanja",
        choices=ProcurementItem.SOURCE_CHOICES,
    )
    source_reference = forms.CharField(required=False, label="Povezi sa zapisom")

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get("source_type") or ""
        source_reference = cleaned_data.get("source_reference") or ""
        source_models = {
            ProcurementItem.SOURCE_EUF: ("euf_invoice", ProcurementInvoice),
            ProcurementItem.SOURCE_UF: ("uf_item", EufItemSnapshot),
            ProcurementItem.SOURCE_GOODS: ("goods_item", GoodsSnapshot),
        }
        if not source_type:
            if source_reference:
                self.add_error("source_reference", "Izaberite tip povezivanja.")
            return cleaned_data
        if not source_reference:
            self.add_error("source_reference", "Izaberite zapis za povezivanje.")
            return cleaned_data

        field_name, model = source_models[source_type]
        try:
            cleaned_data["source_object"] = model.objects.get(pk=source_reference)
            cleaned_data["source_field"] = field_name
        except (model.DoesNotExist, ValueError, TypeError):
            self.add_error("source_reference", "Izabrani zapis ne postoji.")
        return cleaned_data


class EufInvoiceItemLinkForm(forms.Form):
    procurement_item = forms.ModelChoiceField(
        queryset=ProcurementItem.objects.none(),
        widget=Select2Widget(attrs={"class": "select2-method"}),
        label="Stavka zahteva",
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        label="Napomena",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["procurement_item"].queryset = (
            ProcurementItem.objects.select_related("procurement_case")
            .filter(invoice_link__isnull=True)
            .exclude(procurement_case__status=ProcurementCase.Status.COMPLETED)
            .order_by("-procurement_case__created_at", "procurement_case__case_number", "id")
        )


class ProcurementInvoiceForm(forms.ModelForm):
    class Meta:
        model = ProcurementInvoice
        fields = ["job_code", "is_garage", "vehicle", "goes_to_warehouse", "internal_note"]
        widgets = {
            "internal_note": forms.Textarea(attrs={"rows": 3}),
            "job_code": Select2Widget(attrs={"class": "select2-method"}),
            "vehicle": Select2Widget(attrs={"class": "select2-method"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["job_code"].required = False
        self.fields["job_code"].queryset = OrganizationalUnit.objects.all().order_by("code")
        self.fields["vehicle"].required = False
        self.fields["vehicle"].queryset = Vehicle.objects.all().order_by("brand", "model")
        _style_fields(self.fields)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("is_garage"):
            cleaned_data["vehicle"] = None
        return cleaned_data


class ProcurementInvoiceContractLinkForm(forms.ModelForm):
    class Meta:
        model = ProcurementInvoiceContractLink
        fields = ["contract", "note"]

    def __init__(self, *args, invoice=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Contract.objects.filter(contract_type__code__startswith="KUP").order_by("-contract_date")
        if invoice is not None:
            queryset = queryset.exclude(nabavka_invoice_links__invoice=invoice)
        self.fields["contract"].queryset = queryset
        self.fields["contract"].widget = forms.Select(attrs={"class": "form-select select2-method"})
        self.fields["contract"].widget.choices = self.fields["contract"].choices
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
        self.fields["contract"].queryset = Contract.objects.filter(
            contract_type__code__startswith="KUP",
        ).order_by("-contract_date")
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
