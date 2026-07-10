from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Employee(models.Model):
    GENDER_CHOICES = [
        ("M", "Muški"),
        ("F", "Ženski"),
    ]

    employee_code = models.IntegerField(unique=True, verbose_name=_("Šifra zaposlenog"))
    title = models.CharField(max_length=20, verbose_name=_("Titula"), blank=True, null=True)
    original_full_name = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name=_("Originalno ime i prezime"),
    )
    first_name = models.CharField(max_length=50, verbose_name=_("Ime"), blank=True, null=True)
    last_name = models.CharField(max_length=50, verbose_name=_("Prezime"), blank=True, null=True)
    display_first_name_override = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Ime za prikaz"),
    )
    display_last_name_override = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Prezime za prikaz"),
    )
    position = models.CharField(max_length=100, verbose_name=_("Pozicija"))
    department_code = models.IntegerField(verbose_name=_("Šifra odeljenja"))
    org_unit_code = models.CharField(max_length=20, verbose_name=_("OJ"), blank=True, null=True)
    system_code = models.CharField(max_length=10, verbose_name=_("Šifra sistema"), blank=True, null=True)
    system_name = models.CharField(max_length=255, verbose_name=_("Naziv sistema"), blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Pol"))
    skip_hr_identity_update = models.BooleanField(
        default=False,
        verbose_name=_("Ne azuriraj identitet iz HR-a"),
        help_text=_("Ako je ukljuceno, HR sinhronizacija ne menja titulu, ime, prezime i pol."),
    )
    date_of_birth = models.DateField(verbose_name=_("Datum rođenja"))
    date_of_joining = models.DateField(verbose_name=_("Datum zapošljavanja"))
    phone_number = models.CharField(max_length=20, verbose_name=_("Broj telefona"), blank=True, null=True)
    mobile_phone = models.CharField(max_length=50, verbose_name=_("Mobilni broj"), blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name=_("Aktivan"))
    personal_number = models.CharField(max_length=13, verbose_name=_("Matični broj"), blank=True, null=True)
    account_number = models.CharField(max_length=50, verbose_name=_("Partija"), blank=True, null=True)
    address = models.CharField(max_length=255, verbose_name=_("Adresa"), blank=True, null=True)
    residence_municipality = models.CharField(
        max_length=100,
        verbose_name=_("Opstina boravka"),
        blank=True,
        null=True,
    )
    education = models.CharField(max_length=255, verbose_name=_("Škola"), blank=True, null=True)
    job_code = models.CharField(max_length=20, verbose_name=_("Šifra zanimanja"), blank=True, null=True)
    job_title = models.CharField(max_length=255, verbose_name=_("Naziv zanimanja"), blank=True, null=True)
    status_code = models.CharField(max_length=10, verbose_name=_("Šifra statusa"), blank=True, null=True)
    status_name = models.CharField(max_length=255, verbose_name=_("Naziv statusa"), blank=True, null=True)
    slava = models.CharField(max_length=100, verbose_name=_("Slava"), blank=True, null=True)

    class Meta:
        app_label = "fleet"

    @property
    def display_first_name(self):
        return self.display_first_name_override or self.first_name or ""

    @property
    def display_last_name(self):
        return self.display_last_name_override or self.last_name or ""

    def __str__(self):
        return f"{self.display_last_name} {self.display_first_name}".strip()


class EmployeeCVItem(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="cv_items",
        verbose_name=_("Zaposleni"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Naziv posla ili projekta"))
    organization = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Organizacija / klijent"),
    )
    role = models.CharField(max_length=255, blank=True, verbose_name=_("Uloga"))
    start_date = models.DateField(blank=True, null=True, verbose_name=_("Period od"))
    end_date = models.DateField(blank=True, null=True, verbose_name=_("Period do"))
    description = models.TextField(verbose_name=_("Opis aktivnosti"))
    skills = models.TextField(blank=True, verbose_name=_("Znanja i vestine"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Azurirano"))

    class Meta:
        app_label = "fleet"
        ordering = ["-start_date", "-id"]
        verbose_name = _("CV stavka")
        verbose_name_plural = _("CV stavke")

    def __str__(self):
        return f"{self.employee} - {self.title}"


class WorkTimeSheet(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Popunjava se")
        SUBMITTED = "submitted", _("Predato")
        APPROVED = "approved", _("Odobreno")

    employee = models.ForeignKey(
        "fleet.Employee",
        on_delete=models.CASCADE,
        related_name="work_time_sheets",
        verbose_name=_("Zaposleni"),
    )
    year = models.PositiveSmallIntegerField(
        verbose_name=_("Godina"),
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )
    month = models.PositiveSmallIntegerField(
        verbose_name=_("Mesec"),
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Status"),
    )
    meal_days = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(31)],
        verbose_name=_("Topli obrok - broj dana"),
    )
    meal_organizational_unit = models.ForeignKey(
        "fleet.OrganizationalUnit",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="meal_work_time_sheets",
        verbose_name=_("Topli obrok - sifra posla"),
    )
    field_allowance_days = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(31)],
        verbose_name=_("Terenski dodatak - broj dana"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_work_time_sheets",
        verbose_name=_("Kreirao"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="updated_work_time_sheets",
        verbose_name=_("Azurirao"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Azurirano"))

    class Meta:
        ordering = ["-year", "-month", "employee__last_name", "employee__first_name"]
        unique_together = ("employee", "year", "month")
        verbose_name = _("Radna lista")
        verbose_name_plural = _("Radne liste")

    @property
    def total_hours(self):
        return sum((line.total_hours for line in self.lines.all()), 0)

    def __str__(self):
        return f"{self.employee} - {self.month:02d}/{self.year}"


class WorkTimeSheetLine(models.Model):
    sheet = models.ForeignKey(
        WorkTimeSheet,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name=_("Radna lista"),
    )
    line_number = models.PositiveSmallIntegerField(verbose_name=_("R.b."))
    organizational_unit = models.ForeignKey(
        "fleet.OrganizationalUnit",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="work_time_sheet_lines",
        verbose_name=_("Sifra posla"),
    )
    day_1 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_2 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_3 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_4 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_5 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_6 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_7 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_8 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_9 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_10 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_11 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_12 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_13 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_14 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_15 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_16 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_17 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_18 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_19 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_20 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_21 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_22 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_23 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_24 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_25 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_26 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_27 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_28 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_29 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_30 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_31 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    work_conditions = models.CharField(max_length=100, blank=True, verbose_name=_("Uslovi rada"))
    note = models.CharField(max_length=255, blank=True, verbose_name=_("Napomena"))

    class Meta:
        ordering = ["line_number"]
        unique_together = ("sheet", "line_number")
        verbose_name = _("Red radne liste")
        verbose_name_plural = _("Redovi radne liste")

    @property
    def total_hours(self):
        total = 0
        for day in range(1, 32):
            total += getattr(self, f"day_{day}") or 0
        return total

    def __str__(self):
        return f"{self.sheet} / {self.line_number}"
