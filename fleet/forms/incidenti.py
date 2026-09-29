import os

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django_select2.forms import Select2Widget

from core.form_fields import localized_date_field
from hr.models import Employee

from ..models import Incident, Vehicle
from ..support import obuhvat as obuhvat_flote
from .layout import FieldsetMixin


class IncidentForm(FieldsetMixin, forms.ModelForm):
    fieldsets = (
        ("Vozilo i datum", "Tablica i datum sa zapisnika ili rešenja o kazni.", ("vehicle", "date", "location")),
        ("Vozač", "Predlog vozača dolazi iz zaduženja vozila i putnih naloga za taj dan.", ("employee",)),
        ("Prekršaj i kazna", None, ("violation", "fine_amount", "note")),
        ("Prilog", "Zapisnik, rešenje o kazni ili fotografija — PDF ili slika, najviše 20 MB.", ("prilog",)),
    )
    DOZVOLJENI_PRILOZI = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic"}
    NAJVECI_PRILOG_MB = 20

    vehicle = forms.ModelChoiceField(queryset=Vehicle.objects.none(), label="Vozilo",
                                     widget=Select2Widget(attrs={"class": "select2-method"}))
    employee = forms.ModelChoiceField(queryset=Employee.objects.none(), label="Zaposleni (vozač)",
                                      widget=Select2Widget(attrs={"class": "select2-method"}))
    date = localized_date_field(label="Datum prekršaja")

    class Meta:
        model = Incident
        fields = ["vehicle", "date", "location", "employee", "violation", "fine_amount", "note", "prilog"]
        widgets = {
            "location": forms.TextInput(attrs={"placeholder": "Mesto prekršaja"}),
            "violation": forms.Textarea(attrs={"rows": 3, "placeholder": "Opis prekršaja sa zapisnika"}),
            "fine_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "note": forms.Textarea(attrs={"rows": 2}),
            "prilog": forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png,.tif,.tiff,.heic"}),
        }
        labels = {"fine_amount": "Iznos kazne (RSD)"}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        vozila = Vehicle.objects.order_by("brand", "model")
        if user is not None:
            vozila = obuhvat_flote.po_vozilu(vozila, user, "pk")
        if self.instance.vehicle_id:
            vozila = vozila | Vehicle.objects.filter(pk=self.instance.vehicle_id)
        self.fields["vehicle"].queryset = vozila.distinct()
        zaposleni = Employee.objects.filter(is_active=True)
        if self.instance.employee_id:
            zaposleni = zaposleni | Employee.objects.filter(pk=self.instance.employee_id)
        self.fields["employee"].queryset = zaposleni.distinct().order_by("last_name", "first_name")
        if self.instance.pk and self.instance.date:
            self.initial["date"] = self.instance.date.strftime("%d.%m.%Y")

    def clean_prilog(self):
        fajl = self.cleaned_data.get("prilog")
        if isinstance(fajl, UploadedFile):
            if os.path.splitext(fajl.name)[1].lower() not in self.DOZVOLJENI_PRILOZI:
                raise forms.ValidationError("Prilog može biti PDF ili slika (JPG, PNG, TIFF, HEIC).")
            if fajl.size > self.NAJVECI_PRILOG_MB * 1024 * 1024:
                raise forms.ValidationError(f"Prilog je veći od {self.NAJVECI_PRILOG_MB} MB.")
        return fajl

    def clean_fine_amount(self):
        iznos = self.cleaned_data["fine_amount"]
        if iznos is not None and iznos < 0:
            raise forms.ValidationError("Iznos kazne ne može biti negativan.")
        return iznos
