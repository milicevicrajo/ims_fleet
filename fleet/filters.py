import django_filters
from .models import FuelConsumption, JobCode, OrganizationalUnit
from django import forms
from datetime import timedelta
from django.utils import timezone
from datetime import date, timedelta

class VehicleFilterForm(forms.Form):
    org_unit = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.all().order_by('code'),  # Uzimamo sve JobCode sortirane po šifri
        required=False,
        label='Organizaciona jedinica'
    )
    fuel_in_last_6_months = forms.ChoiceField(
        choices=[
            ('', '----'),  # Ovo predstavlja opciju da filter nije primenjen
            ('yes', 'Da'),
            ('no', 'Ne')
        ],
        required=False,
        label='Sipano gorivo u poslednjih 6 meseci'
    )
    center_code = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.values_list('center', flat=True).distinct().order_by('center'),  # Distinktne šifre centara
        required=False,
        label='Centar'
    )


class TrafficCardFilterForm(forms.Form):
    organizational_unit = forms.ModelChoiceField(
        queryset=OrganizationalUnit.objects.all().order_by('name'),
        required=False,
        label='Organizaciona jedinica',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    center = forms.ChoiceField(
        choices=[],
        required=False,
        label='Centar',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        centers = OrganizationalUnit.objects.values_list('center', flat=True).distinct().order_by('center')
        self.fields['center'].choices = [('', '--- Svi centri ---')] + [(c, c) for c in centers]

class FuelFilterForm(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='gte', 
        label='Od datuma',
        widget=forms.DateInput(
            format='%d/%m/%Y',
            attrs={
                'type': 'date',
                'placeholder': 'Od datuma',
                'value': (timezone.now() - timedelta(days=40)).strftime('%Y-%m-%d')  # 40 dana pre
            }
        ),
        input_formats=['%Y-%m-%d'],
    )
    end_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte', 
        label='Do datuma',
        widget=forms.DateInput(
            format='%d/%m/%Y',
            attrs={
                'type': 'date',
                'placeholder': 'Do datuma',
                'value': timezone.now().strftime('%Y-%m-%d')  # Današnji datum
            }
        ),
        input_formats=['%Y-%m-%d'],
    )

    class Meta:
        model = FuelConsumption
        fields = ['start_date', 'end_date',]


class FuelTransactionFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Od datuma"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Do datuma"
    )

class FuelTransactionFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Od datuma'
            }
        ),
        label="Od datuma"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Do datuma'
            }
        ),
        label="Do datuma"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data.get('start_date'):
            self.initial['start_date'] = date.today() - timedelta(days=40)
        if not self.data.get('end_date'):
            self.initial['end_date'] = date.today()


import django_filters
from django import forms
from .models import OrganizationalUnit, Policy
from .queries import policies_monthly_costs_qs  # ili gde već živi tvoja funkcija

class PoliciesMonthlyCostsFilter(django_filters.FilterSet):
    # ChoiceFilter -> lep dropdown; vrednosti ćemo dinamički popuniti u __init__
    year   = django_filters.ChoiceFilter(label="Godina",   choices=[], method="filter_simple")
    month  = django_filters.ChoiceFilter(label="Mesec",    choices=[], method="filter_simple")
    center = django_filters.ChoiceFilter(label="Centar",   choices=[], method="filter_simple")

    # job_code kao contains (često je zgodno imati partial match)
    job_code = django_filters.CharFilter(
        label="Šifra posla", field_name="job_code", lookup_expr="icontains",
        widget=forms.TextInput(attrs={"placeholder": "npr. 83..."})
    )

    # OJ preko ModelChoiceFilter – filtriramo po oj_id (annotirano), ali biramo iz liste OJ
    oj = django_filters.ModelChoiceFilter(
        label="OJ",
        queryset=OrganizationalUnit.objects.all().order_by("code"),
        to_field_name="id",  # filterira po oj_id
        field_name="oj_id",
    )

    # Vrsta polise: kasko / autoodgovornost (plus bilo šta što ti u bazi postoji)
    vrsta = django_filters.ChoiceFilter(label="Vrsta", choices=[], method="filter_simple")

    class Meta:
        model = Policy          # model je potreban django-filter-u, iako filtriramo annotirana polja
        fields = []             # sve filtere smo eksplicitno definisali

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        annotated_qs = policies_monthly_costs_qs(Policy.objects.all())

        years   = set(annotated_qs.order_by().values_list("year", flat=True).distinct())
        months  = set(annotated_qs.order_by().values_list("month", flat=True).distinct())
        centers = set(annotated_qs.order_by().values_list("center", flat=True).distinct())
        vrste   = set(annotated_qs.order_by().values_list("vrsta", flat=True).distinct())

        # SR imena meseci
        month_names = {
            1: "Januar", 2: "Februar", 3: "Mart", 4: "April",
            5: "Maj", 6: "Jun", 7: "Jul", 8: "Avgust",
            9: "Septembar", 10: "Oktobar", 11: "Novembar", 12: "Decembar",
        }

        # Sortiranja: godine ↓, meseci 1→12, centri A→Z, vrste A→Z
        year_choices   = [("", "— sve —")] + [(y, y) for y in sorted([y for y in years if y is not None], reverse=True)]
        month_choices  = [("", "— svi —")] + [(m, month_names.get(m, m)) for m in sorted([m for m in months if m])]
        center_choices = [("", "— svi —")] + [(c, c) for c in sorted([c for c in centers if c])]
        vrsta_choices  = [("", "— sve —")] + [(v, v) for v in sorted([v for v in vrste if v])]

        self.filters["year"].extra["choices"]   = year_choices
        self.filters["month"].extra["choices"]  = month_choices
        self.filters["center"].extra["choices"] = center_choices
        self.filters["vrsta"].extra["choices"]  = vrsta_choices

        # Prazna vrednost za OJ (ModelChoiceFilter)
        self.filters["oj"].extra.setdefault("empty_label", "— sve —")


    def filter_simple(self, queryset, name, value):
        """Jednostavno filtriranje po jednakosti za ChoiceFilter-e (ako je vrednost zadana)."""
        if value in (None, ""):
            return queryset
        return queryset.filter(**{name: value})

from .models import DraftServiceTransaction, Vehicle, ServiceType

# fleet/filters.py
import django_filters
from django import forms
from django.db.models import Q
from .models import DraftServiceTransaction

class ServiceFixingFilter(django_filters.FilterSet):
    datum_od = django_filters.DateFilter(
        field_name="datum", lookup_expr="gte",
        label="Datum od", widget=forms.DateInput(attrs={"type": "date"})
    )
    datum_do = django_filters.DateFilter(
        field_name="datum", lookup_expr="lte",
        label="Datum do", widget=forms.DateInput(attrs={"type": "date"})
    )

    # Tekst pretraga vozila (brand, model, registracija, inventarski broj)
    vozilo = django_filters.CharFilter(
        label="Vozilo (brend/model/reg.)",
        method="filter_vozilo",
        widget=forms.TextInput(attrs={"placeholder": "npr. Fiat / BG-123-AB / 12345"})
    )

    partner = django_filters.CharFilter(
        field_name="naz_par_pl", lookup_expr="icontains",
        label="Partner (sadrži)",
        widget=forms.TextInput(attrs={"placeholder": "npr. NIS, DDOR..."})
    )

    VAN_GARAZE_CHOICES = (
        ("", "— svi —"),  # bez filtriranja
        ("True", "Da"),
        ("False", "Ne"),
    )
    nije_garaza = django_filters.ChoiceFilter(
        label="Van garaže",
        choices=VAN_GARAZE_CHOICES,
        method="filter_nije_garaza",
    )

    class Meta:
        model = DraftServiceTransaction
        fields = []

    def __init__(self, data=None, *args, **kwargs):
        # ako nema parametra u GET-u → default "False" (Ne)
        if data is not None and "nije_garaza" not in data:
            data = data.copy()         # QueryDict → mutable
            data["nije_garaza"] = "False"
        super().__init__(data, *args, **kwargs)

    def filter_nije_garaza(self, qs, name, value):
        if value == "True":
            return qs.filter(nije_garaza=True)
        if value == "False":
            return qs.filter(nije_garaza=False)
        return qs

    def filter_vozilo(self, qs, name, value):
        if not value:
            return qs
        # Vehicle nema registration_number polje, ali ima related 'traffic_cards'
        return qs.filter(
            Q(vehicle__brand__icontains=value) |
            Q(vehicle__model__icontains=value) |
            Q(vehicle__inventory_number__icontains=value) |
            Q(vehicle__traffic_cards__registration_number__icontains=value)
        ).distinct()
