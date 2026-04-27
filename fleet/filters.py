import django_filters
from .models import FuelConsumption, JobCode, OrganizationalUnit, Kvar
from django import forms
from datetime import timedelta
from django.utils import timezone
from datetime import date, timedelta

# fleet/filters.py
import django_filters
from django import forms
from django.utils import timezone
from datetime import timedelta
from django.db.models import OuterRef, Subquery, Exists, F, Q
from django.db.models.functions import Trim
from django.http import QueryDict

from .models import Vehicle, JobCode, FuelConsumption, TrafficCard, Kvar, PutniNalog, Employee
# pretpostavka da OrganizationalUnit postoji:
from .models import OrganizationalUnit, ServiceTransaction
from .utils import date_range_for_datetime_field


class VehicleFilter(django_filters.FilterSet):
    latest_jobcode_qs = JobCode.objects.filter(vehicle=OuterRef('pk')).order_by('-assigned_date', '-pk')
    latest_org_unit_id_sq = Subquery(latest_jobcode_qs.values('organizational_unit_id')[:1])
    latest_center_code_sq = Subquery(latest_jobcode_qs.values('organizational_unit__center')[:1])

    # --- Osnovni filteri ---
    category = django_filters.CharFilter(
        label="Kategorija", lookup_expr="icontains"
    )

    engine_volume_min = django_filters.NumberFilter(
        field_name="engine_volume", lookup_expr="gte", label="Kubikaža od"
    )
    engine_volume_max = django_filters.NumberFilter(
        field_name="engine_volume", lookup_expr="lte", label="Kubikaža do"
    )

    year_min = django_filters.NumberFilter(
        field_name="year_of_manufacture", lookup_expr="gte", label="Godište od"
    )
    year_max = django_filters.NumberFilter(
        field_name="year_of_manufacture", lookup_expr="lte", label="Godište do"
    )

    # --- Status: aktivna / otpisana / sva ---
    STATUS_CHOICES = (
        ("active", "Aktivna"),
        ("archived", "Otpisana"),

    )
    status = django_filters.ChoiceFilter(
        label="Status", choices=STATUS_CHOICES, method="filter_status"
    )

    # Back-compat za stari parametar show_archived=yes
    show_archived = django_filters.CharFilter(method="filter_show_archived")

    # --- Gorivo u poslednjih 6 meseci ---
    YES_NO_CHOICES = (("yes","Da"), ("no","Ne"))
    fuel_in_last_6_months = django_filters.ChoiceFilter(
        label="Gorivo u 6m", choices=YES_NO_CHOICES, method="filter_fuel_6m"
    )

    # --- OJ & Centar (po NAJNOVIJEM JobCode) ---
    org_unit = django_filters.ModelChoiceFilter(
        label="Organizaciona Jedinica", queryset=OrganizationalUnit.objects.none(), method="filter_org_unit"
    )
    center_code = django_filters.ChoiceFilter(
        label="Centar", choices=[], method="filter_center_code"
    )

    class Meta:
        model = Vehicle
        fields = [
            "category",
            "engine_volume_min", "engine_volume_max",
            "year_min", "year_max",
            "status", "fuel_in_last_6_months",
            "org_unit", "center_code",
        ]

    # Dinamičke choice liste + inicijalni status na formi
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qs = self.queryset

        # -- osiguraj da imamo iste anotacije kao u view-u (fallback ako view nije anotirao) --
        if "current_ou_id" not in getattr(qs.query, "annotations", {}):
            qs = qs.annotate(current_ou_id=self.latest_org_unit_id_sq)
        if "latest_center" not in getattr(qs.query, "annotations", {}):
            qs = qs.annotate(latest_center=self.latest_center_code_sq)

        # ---- OJ choices: samo OJ koje su *trenutno* dodeljene (distinct) ----
        current_ou_ids = (
            qs.exclude(current_ou_id__isnull=True)
            .order_by()  # reset default ordering da DISTINCT radi čisto
            .values_list("current_ou_id", flat=True)
            .distinct()
        )
        self.filters["org_unit"].queryset = (
            OrganizationalUnit.objects
            .filter(pk__in=current_ou_ids)
            .only("id", "code", "name")
            .order_by("code")
        )

        # ---- Centri: samo oni koji zaista postoje u *trenutnim* dodelama ----
        centers = (
            qs.exclude(latest_center__isnull=True)
            .annotate(_center=Trim(F("latest_center")))  # skini eventualne razmake
            .order_by()
            .values_list("_center", flat=True)
            .distinct()
        )
        center_choices = [("", "— Svi centri —")] + [(c, c) for c in sorted(centers)]
        self.filters["center_code"].extra["choices"] = center_choices
        self.form.fields["center_code"].choices = center_choices

        # Kategorije kao select (kao što si već radio)
        cats = (Vehicle.objects
                .exclude(category__isnull=True).exclude(category="")
                .values_list("category", flat=True)
                .distinct().order_by("category"))
        self.form.fields["category"].widget = forms.Select(
            choices=[("", "— sve —")] + [(c, c) for c in cats]
        )

        if not self.data.get("status"):
            self.form.fields["status"].initial = "active"

        # CENTRI kao choices (distinct, sortirano)
        centers_qs = OrganizationalUnit.objects.exclude(center__isnull=True).values_list("center", flat=True)
        centers_clean = sorted({c.strip() for c in centers_qs if c and c.strip()})
        center_choices = [("", "--- Svi centri ---")] + [(c, c) for c in centers_clean]
        self.filters["center_code"].extra["choices"] = center_choices
        self.form.fields["center_code"].choices = center_choices

        # KATEGORIJE kao select (prijatnije nego plain text)
        cats = (Vehicle.objects
                .exclude(category__isnull=True).exclude(category="")
                .values_list("category", flat=True)
                .distinct().order_by("category"))
        # ako želiš select umesto text:
        self.form.fields["category"].widget = forms.Select(
            choices=[("", "— sve —")] + [(c, c) for c in cats]
        )

        # Ako korisnik NIJE poslao status, prikaži 'Aktivna' kao default u UI
        if not self.data.get("status"):
            self.form.fields["status"].initial = "active"

    # --- Metode filtera ---

    def filter_status(self, qs, name, value):
        if value == "active":
            return qs.filter(otpis=False)
        elif value == "archived":
            return qs.filter(otpis=True)
        # "all" -> bez ograničenja
        return qs

    def filter_show_archived(self, qs, name, value):
        # za kompatibilnost sa starim ?show_archived=yes
        if value == "yes":
            return qs.filter(otpis=True)
        return qs

    def filter_fuel_6m(self, qs, name, value):
        six_months_ago = timezone.now().date() - timedelta(days=180)
        if value == "yes":
            return qs.filter(fuel_consumptions__date__gte=six_months_ago).distinct()
        elif value == "no":
            return qs.exclude(fuel_consumptions__date__gte=six_months_ago).distinct()
        return qs


    def _ensure_current_ou(self, qs):
        return qs if "current_ou_id" in getattr(qs.query, "annotations", {}) else qs.annotate(current_ou_id=self.latest_org_unit_id_sq)

    def _ensure_latest_center(self, qs):
        return qs if "latest_center" in getattr(qs.query, "annotations", {}) else qs.annotate(latest_center=self.latest_center_code_sq)

    def filter_org_unit(self, qs, name, value):
        if not value:
            return qs
        ou_id = getattr(value, "pk", value)
        qs = self._ensure_current_ou(qs)
        return qs.filter(current_ou_id=ou_id)

    def filter_center_code(self, qs, name, value):
        if not value:
            return qs
        center = value.strip()
        if not center:
            return qs
        qs = self._ensure_latest_center(qs).annotate(_center_trim=Trim(F("latest_center")))
        return qs.filter(_center_trim=center)


class PutniNalogFilter(django_filters.FilterSet):
    center = django_filters.ChoiceFilter(
        label="Centar", method="filter_center"
    )
    job_code = django_filters.ChoiceFilter(
        label="Šifra posla", method="filter_job_code"
    )
    year = django_filters.ChoiceFilter(
        label="Godina", method="filter_year"
    )
    month = django_filters.ChoiceFilter(
        label="Mesec", method="filter_month"
    )
    employee = django_filters.ModelChoiceFilter(
        label="Zaposleni", queryset=Employee.objects.none(), method="filter_employee"
    )
    vehicle = django_filters.ModelChoiceFilter(
        label="Vozilo", queryset=Vehicle.objects.none(), method="filter_vehicle"
    )

    class Meta:
        model = PutniNalog
        fields = ["center", "job_code", "year", "month", "employee", "vehicle"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        qs = self.queryset

        centers = (
            qs.exclude(job_code__center__isnull=True)
            .values_list("job_code__center", flat=True)
            .distinct()
            .order_by("job_code__center")
        )
        self.filters["center"].extra["choices"] = [("", "Svi centri")] + [(c, c) for c in centers]

        job_codes = (
            OrganizationalUnit.objects
            .filter(travel_order_job_code__in=qs)
            .distinct()
            .order_by("code")
        )
        self.filters["job_code"].extra["choices"] = [("", "Sve šifre")] + [
            (u.code, f"{u.code} - {u.name}") for u in job_codes
        ]

        years = (
            qs.exclude(travel_date__isnull=True)
            .values_list("travel_date__year", flat=True)
            .distinct()
            .order_by("-travel_date__year")
        )
        self.filters["year"].extra["choices"] = [("", "Sve godine")] + [(y, y) for y in years]
        self.filters["month"].extra["choices"] = [("", "Svi meseci")] + [(m, m) for m in range(1, 13)]

        self.filters["employee"].queryset = (
            Employee.objects.filter(travel_orders__in=qs)
            .distinct()
            .order_by("last_name", "first_name")
        )
        self.filters["vehicle"].queryset = (
            Vehicle.objects.filter(travel_orders__in=qs)
            .distinct()
            .order_by("brand", "model")
        )

        for field_name in ["center", "job_code", "year", "month", "employee", "vehicle"]:
            field = self.form.fields.get(field_name)
            if field:
                field.widget.attrs.update({
                    "class": "form-select filter-select js-filter-select w-100",
                })

    def filter_center(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(job_code__center=value)

    def filter_job_code(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(job_code__code=value)

    def filter_year(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(travel_date__year=value)

    def filter_month(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(travel_date__month=value)

    def filter_employee(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(employee=value)

    def filter_vehicle(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(vehicle=value)


class KvarFilter(django_filters.FilterSet):
    datum_od = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Prijavljeno od",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    datum_do = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="Prijavljeno do",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    vozilo = django_filters.CharFilter(
        label="Vozilo (brend/model/reg.)",
        method="filter_vozilo",
        widget=forms.TextInput(attrs={"placeholder": "npr. Fiat / BG-123-AB / 12345"}),
    )
    kilometraza_od = django_filters.NumberFilter(
        field_name="kilometraza", lookup_expr="gte", label="Kilometraza od"
    )
    kilometraza_do = django_filters.NumberFilter(
        field_name="kilometraza", lookup_expr="lte", label="Kilometraza do"
    )
    opis = django_filters.CharFilter(
        field_name="opis", lookup_expr="icontains", label="Opis sadrzi"
    )
    napomena = django_filters.CharFilter(
        field_name="napomena", lookup_expr="icontains", label="Napomena sadrzi"
    )
    van_ims = django_filters.ChoiceFilter(
        choices=[
            ("", "Sve"),
            ("True", "Van IMS-a"),
            ("False", "IMS garaza"),
        ],
        label="Van IMS-a?",
        method="filter_van_ims",
    )

    class Meta:
        model = Kvar
        fields = []

    def filter_van_ims(self, qs, name, value):
        if value == "True":
            return qs.filter(van_ims=True)
        if value == "False":
            return qs.filter(van_ims=False)
        return qs

    def filter_vozilo(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(
            Q(vehicle__brand__icontains=value)
            | Q(vehicle__model__icontains=value)
            | Q(vehicle__inventory_number__icontains=value)
            | Q(vehicle__traffic_cards__registration_number__icontains=value)
        ).distinct()



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
        method='filter_start_date',
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
        method='filter_end_date',
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

    def filter_start_date(self, queryset, name, value):
        start_dt, _ = date_range_for_datetime_field(value)
        return queryset.filter(date__gte=start_dt) if start_dt else queryset

    def filter_end_date(self, queryset, name, value):
        _, end_dt = date_range_for_datetime_field(None, value)
        return queryset.filter(date__lte=end_dt) if end_dt else queryset


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



    def filter_simple(self, queryset, name, value):
        """Jednostavno filtriranje po jednakosti za ChoiceFilter-e (ako je vrednost zadana)."""
        if value in (None, ""):
            return queryset
        return queryset.filter(**{name: value})

from .models import DraftServiceTransaction, Vehicle, ServiceType

# fleet/filters.py
import django_filters
from django import forms
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
        widget=forms.TextInput(attrs={"placeholder": "npr. Auto Deki, Beoguma..."})
    )

    SIFRA_VRSTE_CHOICES = (
        ("", "Sve"),
        ("UF", "UF"),
        ("EUF", "EUF"),
    )
    sifra_vrste = django_filters.ChoiceFilter(
        label="Šifra vrste",
        choices=SIFRA_VRSTE_CHOICES,
        method="filter_sifra_vrste",
    )

    VAN_GARAZE_CHOICES = (
        ("True", "Ne"),
        ("False", "Da"),
    )
    nije_garaza = django_filters.ChoiceFilter(
        label="Garaza",
        choices=VAN_GARAZE_CHOICES,
        method="filter_nije_garaza",
    )

    class Meta:
        model = DraftServiceTransaction
        fields = []

    def __init__(self, data=None, *args, **kwargs):
        # ako nema parametara u GET-u → default nije_garaza=False i sifra_vrste=EUF
        # bitno: i kada je data=None, filter mora biti bound da bi se default ZAISTA primenio
        if data is None:
            data = QueryDict('', mutable=True)
        else:
            data = data.copy()         # QueryDict → mutable

        if "nije_garaza" not in data:
            data["nije_garaza"] = "False"
        if "sifra_vrste" not in data:
            data["sifra_vrste"] = "EUF"

        super().__init__(data, *args, **kwargs)
        # (opciono) postavi i initial, čisto da bude konzistentno
        self.form.fields["nije_garaza"].initial = "False"
        self.form.fields["sifra_vrste"].initial = "EUF"

    def filter_nije_garaza(self, qs, name, value):
        if value == "True":
            return qs.filter(nije_garaza=True)
        if value == "False":
            return qs.filter(nije_garaza=False)
        return qs

    def filter_sifra_vrste(self, qs, name, value):
        if not value:
            return qs
        return qs.annotate(_sif_vrs_trim=Trim("sif_vrs")).filter(_sif_vrs_trim__iexact=value)

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


# Ako baš želiš dropdown za mesece, koristi TypedChoiceFilter sa coerce=int
# Opcije za mesec: prazna vrednost + 1-12
MONTH_CHOICES = [('', 'Svi meseci')] + [(str(i), f'{i:02d}') for i in range(1, 13)]

class ServiceMonthlyCostsFilter(django_filters.FilterSet):
    year = django_filters.NumberFilter(field_name="year", label="Godina")
    month = django_filters.TypedChoiceFilter(
        field_name="month",
        choices=MONTH_CHOICES,
        coerce=lambda value: int(value) if value not in (None, '') else None,
        empty_value=None,
        required=False,
        label="Mesec",
    )

    oj = django_filters.CharFilter(field_name="oj_code_txt", lookup_expr="icontains", label="OJ")
    center = django_filters.CharFilter(field_name="center_code_txt", lookup_expr="icontains", label="Sifra posla")

    class Meta:
        model = ServiceTransaction
        fields = ["year", "month", "oj", "center"]
