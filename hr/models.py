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
