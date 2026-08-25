from django import forms
from django.conf import settings
from django.forms import inlineformset_factory
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from menice.models import Menica, UlaznaMenica
from .models import (
    BusinessRequest,
    Contract,
    ContractDocument,
    ContractGuarantee,
    ContractMenicaLink,
    ContractParty,
    ContractType,
    Offer,
    Partner,
)


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


class BusinessRequestForm(forms.ModelForm):
    request_date = localized_date_field(label="Datum zahteva")

    class Meta:
        model = BusinessRequest
        fields = [
            "request_number",
            "request_date",
            "partner",
            "external_partner_name",
            "request_type",
            "subject",
            "description",
            "center",
            "status",
            "file",
        ]
        widgets = {
            "partner": Select2Widget(attrs={"class": "select2-method"}),
            "request_type": Select2Widget(attrs={"class": "select2-method"}),
            "status": Select2Widget(attrs={"class": "select2-method"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["partner"].queryset = Partner.objects.filter(is_active=True)
        self.fields["partner"].required = False
        self.fields["partner"].empty_label = "Izaberi partnera..."
        self.fields["external_partner_name"].required = False
        self.fields["description"].required = False
        self.fields["center"].required = False
        self.fields["file"].required = False
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, Select2Widget):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} select2-method".strip()
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            elif not isinstance(widget, (forms.FileInput, forms.Textarea)):
                widget.attrs.setdefault("class", "form-control")
        self.fields["description"].widget.attrs.setdefault("class", "form-control")

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if not uploaded_file:
            return uploaded_file

        max_size = getattr(settings, "MAX_CONTRACT_UPLOAD_SIZE", 50 * 1024 * 1024)
        if uploaded_file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise forms.ValidationError(
                f"Fajl zahteva je veci od dozvoljenih {max_mb:.0f} MB."
            )
        return uploaded_file


class OfferForm(forms.ModelForm):
    offer_date = localized_date_field(label="Datum ponude")
    valid_until = localized_date_field(label="Vazi do", required=False)

    class Meta:
        model = Offer
        fields = [
            "offer_number",
            "offer_date",
            "valid_until",
            "direction",
            "partner",
            "external_partner_name",
            "request",
            "offer_type",
            "subject",
            "description",
            "value",
            "currency",
            "status",
            "file",
        ]
        widgets = {
            "direction": Select2Widget(attrs={"class": "select2-method"}),
            "partner": Select2Widget(attrs={"class": "select2-method"}),
            "request": Select2Widget(attrs={"class": "select2-method"}),
            "offer_type": Select2Widget(attrs={"class": "select2-method"}),
            "currency": Select2Widget(attrs={"class": "select2-method"}),
            "status": Select2Widget(attrs={"class": "select2-method"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["partner"].queryset = Partner.objects.filter(is_active=True)
        self.fields["partner"].required = False
        self.fields["partner"].empty_label = "Izaberi partnera..."
        self.fields["request"].queryset = BusinessRequest.objects.order_by("-request_date", "-created_at")
        self.fields["request"].required = False
        self.fields["request"].empty_label = "Izaberi zahtev..."
        self.fields["external_partner_name"].required = False
        self.fields["valid_until"].required = False
        self.fields["description"].required = False
        self.fields["value"].required = False
        self.fields["file"].required = False
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, Select2Widget):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} select2-method".strip()
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            elif not isinstance(widget, (forms.FileInput, forms.Textarea)):
                widget.attrs.setdefault("class", "form-control")
        self.fields["description"].widget.attrs.setdefault("class", "form-control")

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if not uploaded_file:
            return uploaded_file

        max_size = getattr(settings, "MAX_CONTRACT_UPLOAD_SIZE", 50 * 1024 * 1024)
        if uploaded_file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise forms.ValidationError(
                f"Fajl ponude je veci od dozvoljenih {max_mb:.0f} MB."
            )
        return uploaded_file


class ContractForm(forms.ModelForm):
    contract_date = localized_date_field(label="Datum ugovora")
    link_outgoing_menica = forms.ModelChoiceField(
        queryset=Menica.objects.none(),
        required=False,
        label="Izlazna menica",
        widget=Select2Widget(attrs={"class": "select2-method"}),
    )
    link_ulazna_menica = forms.ModelChoiceField(
        queryset=UlaznaMenica.objects.none(),
        required=False,
        label="Ulazna menica",
        widget=Select2Widget(attrs={"class": "select2-method"}),
    )
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
            "value_type",
            "unit_price",
            "unit_label",
            "currency",
            "status",
            "has_incoming_menice",
            "has_outgoing_menice",
            "has_guarantees",
            "file",
            "note",
        ]
        widgets = {
            "subject": forms.Textarea(attrs={"rows": 3}),
            "note": forms.Textarea(attrs={"rows": 3}),
            "kind": Select2Widget(attrs={"class": "select2-method"}),
            "value_type": Select2Widget(attrs={"class": "select2-method"}),
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
        self.fields["link_outgoing_menica"].queryset = Menica.objects.filter(
            tip=Menica.TIP_IZLAZNA,
        ).order_by("-datum_registracije", "-created_at")
        self.fields["link_outgoing_menica"].empty_label = "Izaberi izlaznu menicu..."
        self.fields["link_outgoing_menica"].label_from_instance = self.menica_label_from_instance
        self.fields["link_ulazna_menica"].queryset = UlaznaMenica.objects.all().order_by(
            "-datum_prijema_menice",
            "-created_at",
        )
        self.fields["link_ulazna_menica"].empty_label = "Izaberi ulaznu menicu..."
        self.fields["link_ulazna_menica"].label_from_instance = self.ulazna_menica_label_from_instance

        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, Select2Widget):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} select2-method".strip()
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif not isinstance(widget, (forms.CheckboxInput, Select2Widget, forms.FileInput, forms.Textarea)):
                widget.attrs.setdefault("class", "form-control")

        # Textarea class
        for name in ("subject", "note"):
            self.fields[name].widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned_data = super().clean()
        value_type = cleaned_data.get("value_type")
        unit_price = cleaned_data.get("unit_price")
        unit_label = (cleaned_data.get("unit_label") or "").strip()
        unit_value_types = {
            Contract.VALUE_TYPE_HOURLY,
            Contract.VALUE_TYPE_MONTHLY,
            Contract.VALUE_TYPE_MAN_MONTH,
            Contract.VALUE_TYPE_UNIT,
        }

        if value_type == Contract.VALUE_TYPE_HOURLY and not unit_label:
            cleaned_data["unit_label"] = "radni sat"
        elif value_type == Contract.VALUE_TYPE_MONTHLY and not unit_label:
            cleaned_data["unit_label"] = "mesec"
        elif value_type == Contract.VALUE_TYPE_MAN_MONTH and not unit_label:
            cleaned_data["unit_label"] = "čovek mesec"
        elif value_type == Contract.VALUE_TYPE_UNIT and not unit_label:
            self.add_error("unit_label", "Unesite naziv jedinice.")

        if value_type in unit_value_types and unit_price is None:
            self.add_error("unit_price", "Unesite cenu po jedinici.")

        if value_type == Contract.VALUE_TYPE_FIXED:
            cleaned_data["unit_price"] = None
            cleaned_data["unit_label"] = ""
        elif value_type in unit_value_types:
            cleaned_data["value"] = None
        elif value_type == Contract.VALUE_TYPE_UNDEFINED:
            cleaned_data["value"] = None
            cleaned_data["unit_price"] = None
            cleaned_data["unit_label"] = ""

        if not cleaned_data.get("has_outgoing_menice"):
            cleaned_data["link_outgoing_menica"] = None
        if not cleaned_data.get("has_incoming_menice"):
            cleaned_data["link_ulazna_menica"] = None

        return cleaned_data

    @staticmethod
    def menica_label_from_instance(menica):
        details = [menica.get_tip_display()]
        if menica.naziv_duznika:
            details.append(menica.naziv_duznika)
        if menica.iznos_menice is not None:
            details.append(f"{menica.iznos_menice:.2f} {menica.valuta_menice or ''}".strip())
        return f"{menica.serijski_broj_menice or 'Bez serijskog broja'} ({', '.join(details)})"

    @staticmethod
    def ulazna_menica_label_from_instance(menica):
        details = []
        if menica.naziv_pravnog_lica:
            details.append(menica.naziv_pravnog_lica)
        if menica.broj_naseg_ugovora:
            details.append(f"ugovor {menica.broj_naseg_ugovora}")
        if menica.sifra_centra:
            details.append(f"centar {menica.sifra_centra}")
        suffix = f" ({', '.join(details)})" if details else ""
        return f"{menica.serijski_broj_menice}{suffix}"

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if not uploaded_file:
            return uploaded_file

        max_size = getattr(settings, "MAX_CONTRACT_UPLOAD_SIZE", 50 * 1024 * 1024)
        if uploaded_file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise forms.ValidationError(
                f"Fajl ugovora je veci od dozvoljenih {max_mb:.0f} MB."
            )
        return uploaded_file


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


class ContractFileForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ["file"]
        widgets = {
            "file": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = True

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if not uploaded_file:
            return uploaded_file

        max_size = getattr(settings, "MAX_CONTRACT_UPLOAD_SIZE", 50 * 1024 * 1024)
        if uploaded_file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise forms.ValidationError(
                f"Fajl ugovora je veci od dozvoljenih {max_mb:.0f} MB."
            )
        return uploaded_file


class ContractDocumentForm(forms.ModelForm):
    class Meta:
        model = ContractDocument
        fields = ["description", "file"]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Kratak opis dokumenta ili priloga",
                }
            ),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_description(self):
        return (self.cleaned_data.get("description") or "").strip()

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if not uploaded_file:
            return uploaded_file

        max_size = getattr(settings, "MAX_CONTRACT_UPLOAD_SIZE", 50 * 1024 * 1024)
        if uploaded_file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise forms.ValidationError(
                f"Dokument je veci od dozvoljenih {max_mb:.0f} MB."
            )
        return uploaded_file


class ContractPartyForm(forms.ModelForm):
    class Meta:
        model = ContractParty
        fields = ["partner", "role", "party_contract_number", "note"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["partner"].widget = Select2Widget(attrs={"class": "select2-method"})
        self.fields["partner"].queryset = Partner.objects.filter(is_active=True)
        self.fields["partner"].label_from_instance = self.partner_label_from_instance
        self.fields["role"].widget.attrs.setdefault("class", "form-select contract-party-role-select")
        self.fields["party_contract_number"].widget.attrs.setdefault("class", "form-control")
        self.fields["party_contract_number"].required = False
        self.fields["note"].widget.attrs.setdefault("class", "form-control")
        self.fields["note"].required = False

    @staticmethod
    def partner_label_from_instance(partner):
        details = []
        if partner.external_sif_par:
            details.append(f"Sifra: {partner.external_sif_par}")
        if partner.pib:
            details.append(f"PIB: {partner.pib}")
        if partner.maticni_broj:
            details.append(f"MB: {partner.maticni_broj}")
        if details:
            return f"{partner.name} ({', '.join(details)})"
        return partner.name


ContractPartyFormSet = inlineformset_factory(
    Contract,
    ContractParty,
    form=ContractPartyForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class ContractMenicaLinkForm(forms.ModelForm):
    class Meta:
        model = ContractMenicaLink
        fields = ["menica", "ulazna_menica", "note"]
        widgets = {
            "menica": Select2Widget(attrs={"class": "select2-method"}),
            "ulazna_menica": Select2Widget(attrs={"class": "select2-method"}),
            "note": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["menica"].required = False
        self.fields["menica"].empty_label = "Izaberi menicu..."
        self.fields["menica"].queryset = Menica.objects.all().order_by(
            "tip",
            "-datum_registracije",
            "-created_at",
        )
        self.fields["menica"].label_from_instance = self.menica_label_from_instance
        self.fields["ulazna_menica"].required = False
        self.fields["ulazna_menica"].empty_label = "Izaberi ulaznu menicu..."
        self.fields["ulazna_menica"].queryset = UlaznaMenica.objects.all().order_by(
            "-datum_prijema_menice",
            "-created_at",
        )
        self.fields["ulazna_menica"].label_from_instance = self.ulazna_menica_label_from_instance
        self.fields["note"].required = False

    def clean(self):
        cleaned_data = super().clean()
        menica = cleaned_data.get("menica")
        ulazna_menica = cleaned_data.get("ulazna_menica")
        if bool(menica) == bool(ulazna_menica):
            raise forms.ValidationError("Izaberite tacno jednu menicu.")
        return cleaned_data

    @staticmethod
    def menica_label_from_instance(menica):
        details = [menica.get_tip_display()]
        if menica.naziv_duznika:
            details.append(menica.naziv_duznika)
        if menica.iznos_menice is not None:
            details.append(f"{menica.iznos_menice:.2f} {menica.valuta_menice or ''}".strip())
        return f"{menica.serijski_broj_menice or 'Bez serijskog broja'} ({', '.join(details)})"

    @staticmethod
    def ulazna_menica_label_from_instance(menica):
        details = []
        if menica.naziv_pravnog_lica:
            details.append(menica.naziv_pravnog_lica)
        if menica.broj_naseg_ugovora:
            details.append(f"ugovor {menica.broj_naseg_ugovora}")
        if menica.sifra_centra:
            details.append(f"centar {menica.sifra_centra}")
        suffix = f" ({', '.join(details)})" if details else ""
        return f"{menica.serijski_broj_menice}{suffix}"


class ContractGuaranteeForm(forms.ModelForm):
    valid_from = localized_date_field(label="Vazi od", required=False)
    valid_to = localized_date_field(label="Vazi do", required=False)

    class Meta:
        model = ContractGuarantee
        fields = [
            "guarantee_number",
            "issuer",
            "beneficiary",
            "amount",
            "currency",
            "valid_from",
            "valid_to",
            "status",
            "note",
        ]
        widgets = {
            "currency": Select2Widget(attrs={"class": "select2-method"}),
            "status": Select2Widget(attrs={"class": "select2-method"}),
            "note": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, Select2Widget):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} select2-method".strip()
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            elif not isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "form-control")
