from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


def _clean_mobile_phone_number(value):
    value = "" if value is None else str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return "".join(ch for ch in value if ch.isdigit()) or value


class MobilePackage(models.Model):
    partner_code = models.CharField(_("Šifra partnera"), max_length=20, blank=True)
    partner_name = models.CharField(_("Partner"), max_length=150, blank=True)
    name = models.CharField(_("Paket"), max_length=100)
    valid_from = models.DateField(_("Važi od"), null=True, blank=True)
    valid_to = models.DateField(_("Važi do"), null=True, blank=True)
    net_amount = models.DecimalField(_("Iznos neto"), max_digits=12, decimal_places=2, null=True, blank=True)
    gross_amount = models.DecimalField(_("Iznos bruto"), max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(_("Opis"), blank=True)
    contract = models.ForeignKey(
        "ugovori.Contract",
        on_delete=models.SET_NULL,
        related_name="mobile_packages",
        verbose_name=_("Ugovor"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    class Meta:
        ordering = ["name", "valid_from", "id"]
        verbose_name = _("Mobilni paket")
        verbose_name_plural = _("Mobilni paketi")
        constraints = [
            models.UniqueConstraint(
                fields=["partner_code", "name", "valid_from"],
                name="uniq_mobilni_package_partner_name_from",
            )
        ]

    def __str__(self):
        return self.name


class MobileUser(models.Model):
    class LinkStatus(models.TextChoices):
        AUTO = "auto", _("Automatski")
        MANUAL = "manual", _("Rucno povezano")
        UNMATCHED = "unmatched", _("Nepovezano")
        NON_EMPLOYEE = "non_employee", _("Nezaposleni")
        AMBIGUOUS = "ambiguous", _("Nejasno")

    organizational_unit = models.CharField(_("OJ"), max_length=20, blank=True)
    employee_code = models.IntegerField(_("Šifra radnika"), unique=True)
    full_name = models.CharField(_("Ime i prezime"), max_length=150)
    personal_number = models.CharField(_("JMBG"), max_length=13, blank=True)
    is_active = models.BooleanField(_("Aktivan"), default=True)
    departure_date = models.DateField(_("Datum odlaska"), null=True, blank=True)
    employee = models.ForeignKey(
        "fleet.Employee",
        on_delete=models.SET_NULL,
        related_name="mobile_users",
        verbose_name=_("Zaposleni"),
        null=True,
        blank=True,
    )
    link_status = models.CharField(
        _("Status veze"),
        max_length=20,
        choices=LinkStatus.choices,
        default=LinkStatus.UNMATCHED,
    )
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    class Meta:
        ordering = ["full_name", "employee_code"]
        verbose_name = _("Korisnik mobilnog")
        verbose_name_plural = _("Korisnici mobilnih")
        indexes = [
            models.Index(fields=["employee_code"]),
            models.Index(fields=["full_name"]),
        ]

    def __str__(self):
        return f"{self.employee_code} - {self.full_name}"


class MobileAssignment(models.Model):
    year = models.PositiveSmallIntegerField(
        _("Godina"),
        validators=[MinValueValidator(2020), MaxValueValidator(2100)],
    )
    month = models.PositiveSmallIntegerField(
        _("Mesec"),
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    phone_number = models.CharField(_("Broj"), max_length=30)
    number_active = models.BooleanField(_("Aktivan broj"), default=True)
    package = models.ForeignKey(
        MobilePackage,
        on_delete=models.SET_NULL,
        related_name="assignments",
        verbose_name=_("Paket"),
        null=True,
        blank=True,
    )
    mobile_user = models.ForeignKey(
        MobileUser,
        on_delete=models.SET_NULL,
        related_name="assignments",
        verbose_name=_("Korisnik mobilnog"),
        null=True,
        blank=True,
    )
    source_employee_code = models.IntegerField(_("Sifra iz dodele"), null=True, blank=True)
    source_full_name = models.CharField(_("Ime iz dodele"), max_length=150, blank=True, default="")
    employee = models.ForeignKey(
        "fleet.Employee",
        on_delete=models.SET_NULL,
        related_name="mobile_assignments",
        verbose_name=_("Zaposleni"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "phone_number"]
        verbose_name = _("Dodela mobilnog broja")
        verbose_name_plural = _("Dodele mobilnih brojeva")
        constraints = [
            models.UniqueConstraint(
                fields=["year", "month", "phone_number"],
                name="uniq_mobilni_assignment_period_number",
            )
        ]
        indexes = [
            models.Index(fields=["year", "month"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["employee"]),
            models.Index(fields=["mobile_user"]),
            models.Index(fields=["source_employee_code"]),
        ]

    def __str__(self):
        return f"{self.phone_number} ({self.month:02d}/{self.year})"

    @property
    def linked_employee(self):
        if self.mobile_user_id:
            if self.mobile_user.link_status == MobileUser.LinkStatus.NON_EMPLOYEE:
                return None
            return self.mobile_user.employee if self.mobile_user.employee_id else None
        if self.employee_id:
            return self.employee
        return None

    @property
    def linked_employee_id(self):
        employee = self.linked_employee
        return employee.pk if employee else None

    @property
    def display_employee_code(self):
        employee = self.linked_employee
        if employee:
            return employee.employee_code
        if self.source_employee_code is not None:
            return self.source_employee_code
        if self.mobile_user_id:
            return self.mobile_user.employee_code
        return None

    @property
    def display_employee_name(self):
        employee = self.linked_employee
        if employee:
            return str(employee).strip() or employee.original_full_name or ""
        if self.mobile_user_id and self.mobile_user.full_name:
            return self.mobile_user.full_name
        return self.source_full_name or ""

    @property
    def display_personal_number(self):
        employee = self.linked_employee
        if employee:
            return employee.personal_number or ""
        if self.mobile_user_id:
            return self.mobile_user.personal_number
        return ""


class MobileUsage(models.Model):
    year = models.PositiveSmallIntegerField(
        _("Godina"),
        validators=[MinValueValidator(2020), MaxValueValidator(2100)],
    )
    month = models.PositiveSmallIntegerField(
        _("Mesec"),
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    phone_number = models.CharField(_("Broj"), max_length=30)
    assignment = models.ForeignKey(
        MobileAssignment,
        on_delete=models.SET_NULL,
        related_name="usages",
        verbose_name=_("Dodela"),
        null=True,
        blank=True,
    )
    employee = models.ForeignKey(
        "fleet.Employee",
        on_delete=models.SET_NULL,
        related_name="mobile_usages",
        verbose_name=_("Zaposleni"),
        null=True,
        blank=True,
    )
    onnet = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mts_network = models.DecimalField(_("U MTS mreži"), max_digits=12, decimal_places=2, default=0)
    outside_mts = models.DecimalField(_("Van MTS mreže"), max_digits=12, decimal_places=2, default=0)
    kim = models.DecimalField(_("Ka KIM"), max_digits=12, decimal_places=2, default=0)
    special = models.DecimalField(_("Ka specijalnim"), max_digits=12, decimal_places=2, default=0)
    international = models.DecimalField(_("Internacionalni"), max_digits=12, decimal_places=2, default=0)
    roaming = models.DecimalField(_("Roaming"), max_digits=12, decimal_places=2, default=0)
    gprs = models.DecimalField(_("GPRS"), max_digits=12, decimal_places=2, default=0)
    sms = models.DecimalField(_("SMS"), max_digits=12, decimal_places=2, default=0)
    sms_international = models.DecimalField(_("SMS internac."), max_digits=12, decimal_places=2, default=0)
    sms_roaming = models.DecimalField(_("SMS u roamingu"), max_digits=12, decimal_places=2, default=0)
    mms = models.DecimalField(_("MMS"), max_digits=12, decimal_places=2, default=0)
    vas_sms = models.DecimalField(_("VAS SMS"), max_digits=12, decimal_places=2, default=0)
    discount_traffic = models.DecimalField(_("Saobraćaj za popust"), max_digits=12, decimal_places=2, default=0)
    fixed_discount = models.DecimalField(_("Fiksni popust"), max_digits=12, decimal_places=2, default=0)
    variable_discount = models.DecimalField(_("Varijabilni popust"), max_digits=12, decimal_places=2, default=0)
    services = models.DecimalField(_("Usluge"), max_digits=12, decimal_places=2, default=0)
    dispatch_notes = models.DecimalField(_("Otpremnice"), max_digits=12, decimal_places=2, default=0)
    parking = models.DecimalField(_("Parking"), max_digits=12, decimal_places=2, default=0)
    nzrd = models.DecimalField(_("NZRD"), max_digits=12, decimal_places=2, default=0)
    vat_base = models.DecimalField(_("Osnovica za PDV"), max_digits=12, decimal_places=2, default=0)
    vat = models.DecimalField(_("PDV"), max_digits=12, decimal_places=2, default=0)
    installments = models.DecimalField(_("Plaćanje na rate"), max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(_("Ukupno za naplatu"), max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "phone_number"]
        verbose_name = _("Potrošnja mobilnog")
        verbose_name_plural = _("Potrošnja mobilnih")
        constraints = [
            models.UniqueConstraint(
                fields=["year", "month", "phone_number"],
                name="uniq_mobilni_usage_period_number",
            )
        ]
        indexes = [
            models.Index(fields=["year", "month"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["employee"]),
        ]

    def __str__(self):
        return f"{self.phone_number} - {self.total} ({self.month:02d}/{self.year})"


class MobileParkingExemption(models.Model):
    phone_number = models.CharField(_("Broj telefona"), max_length=30, unique=True)
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Azurirano"), auto_now=True)

    class Meta:
        ordering = ["phone_number"]
        verbose_name = _("Izuzetak parkinga")
        verbose_name_plural = _("Izuzeci parkinga")

    def save(self, *args, **kwargs):
        self.phone_number = _clean_mobile_phone_number(self.phone_number)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone_number


class MobileImportLog(models.Model):
    class ImportType(models.TextChoices):
        PACKAGES = "packages", _("Paketi")
        USERS = "users", _("Korisnici")
        ASSIGNMENTS = "assignments", _("Dodele")
        USAGES = "usages", _("Potrošnja")

    import_type = models.CharField(_("Tip importa"), max_length=20, choices=ImportType.choices)
    year = models.PositiveSmallIntegerField(_("Godina"), null=True, blank=True)
    month = models.PositiveSmallIntegerField(_("Mesec"), null=True, blank=True)
    source_file = models.CharField(_("Fajl"), max_length=255, blank=True)
    imported_count = models.PositiveIntegerField(_("Uvezeno"), default=0)
    updated_count = models.PositiveIntegerField(_("Ažurirano"), default=0)
    skipped_count = models.PositiveIntegerField(_("Preskoceno"), default=0)
    error_message = models.TextField(_("Greška"), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="mobile_import_logs",
        verbose_name=_("Kreirao"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("Log importa mobilnih")
        verbose_name_plural = _("Logovi importa mobilnih")

    def __str__(self):
        period = f" {self.month:02d}/{self.year}" if self.year and self.month else ""
        return f"{self.get_import_type_display()}{period}"
