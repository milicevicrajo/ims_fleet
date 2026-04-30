from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, Group, Permission
import datetime

# <!-- ======================================================================= -->
#                 <!-- MODELI SAMOSTALNE APLIKACIJE -->
# <!-- ======================================================================= -->
class Vehicle(models.Model):
    inventory_number = models.CharField(max_length=20, unique=True, verbose_name=_("Inventarski broj"))
    chassis_number = models.CharField(max_length=17, unique=True, verbose_name=_("Broj šasije"))
    brand = models.CharField(max_length=50, verbose_name=_("Marka"))
    model = models.CharField(max_length=50, verbose_name=_("Model"))
    year_of_manufacture = models.IntegerField(verbose_name=_("Godina proizvodnje"))
    first_registration_date = models.DateField(verbose_name=_("Datum prve registracije"))
    color = models.CharField(max_length=30, verbose_name=_("Boja"))
    number_of_axles = models.IntegerField(verbose_name=_("Broj osovina"))
    engine_volume = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_("Zapremina motora (cm³)"))
    engine_number = models.CharField(max_length=50, unique=True, verbose_name=_("Broj motora"))
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Masa (kg)"))
    engine_power = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_("Snaga motora (kW)"))
    load_capacity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Nosivost (kg)"))
    category = models.CharField(max_length=50, verbose_name=_("Kategorija vozila"))
    maximum_permissible_weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Maksimalna dozvoljena masa (kg)"))
    fuel_type = models.CharField(max_length=20, verbose_name=_("Vrsta goriva"))
    number_of_seats = models.IntegerField(verbose_name=_("Broj sedišta"))
    purchase_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Nabavna vrednost"))
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Knjigovodstvena vrednost"), null=True)
    service_interval = models.IntegerField(verbose_name=_("Servisni interval (km)"), default=15000)
    
    # Nova polja
    purchase_date = models.DateField(verbose_name=_("Datum nabavke"), null=True)
    partner_code = models.CharField(max_length=20, verbose_name=_("Šifra partnera"), null=True)
    partner_name = models.CharField(max_length=100, verbose_name=_("Naziv partnera"), null=True)
    invoice_number = models.CharField(max_length=50, verbose_name=_("Broj fakture"), null=True)
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))

    otpis = models.BooleanField(_("Otpis"), default=False, editable=False)


    def __str__(self):
        traffic_card = self.traffic_cards.first()
        if traffic_card:
            return f"{traffic_card.registration_number} - {self.brand} {self.model}"
        return f"{self.chassis_number} - {self.brand} {self.model}"


class TrafficCard(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='traffic_cards',
        verbose_name=_("Vozilo")
    )

    registration_number = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2}\d{3,4}-[A-Z]{2}$',
                message=_("Registracioni broj mora biti u formatu AA999-AA ili AA9999-AA")
            )
        ],
        verbose_name=_("Registracioni broj"),
        unique=True
    )

    issue_date = models.DateField(verbose_name=_("Datum izdavanja"))
    valid_until = models.DateField(verbose_name=_("Važi do"))
    traffic_card_number = models.CharField(max_length=50, verbose_name=_("Broj saobraćajne dozvole"))
    serial_number = models.CharField(max_length=50, verbose_name=_("Serijski broj"))
    owner = models.CharField(max_length=100, verbose_name=_("Vlasnik"))
    homologation_number = models.CharField(max_length=50, verbose_name=_("Homologacioni broj"))

    traffic_card_pdf = models.FileField(
        upload_to='traffic_cards/',
        verbose_name=_("PDF saobraćajne dozvole"),
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.registration_number} valid until {self.valid_until}"


class VehicleTenderDocument(models.Model):
    class DocumentType(models.TextChoices):
        LICENSE_PLATE = 'license_plate', _("Slika tablica")
        STICKER = 'sticker', _("Slika nalepnice")
        OTHER = 'other', _("Drugo")

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='tender_documents',
        verbose_name=_("Vozilo"),
    )

    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.LICENSE_PLATE,
        verbose_name=_("Tip dokumenta"),
    )

    title = models.CharField(max_length=255, verbose_name=_("Naziv"))
    image = models.ImageField(upload_to='vehicle_tender_documents/%Y/%m/', verbose_name=_("Slika"))
    description = models.TextField(blank=True, verbose_name=_("Opis"))
    taken_at = models.DateField(null=True, blank=True, verbose_name=_("Datum fotografisanja"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktivan"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Ažurirano"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Tender dokument vozila")
        verbose_name_plural = _("Tender dokumenti vozila")

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.title}"




class OrganizationalUnit(models.Model):
    name = models.CharField(verbose_name=_("Naziv"), max_length=100)
    code = models.CharField(verbose_name=_("Šifra organizacione jedinice"), max_length=10, unique=True)
    center = models.CharField(verbose_name=_("Šifra centra"), max_length=10)

    def __str__(self):
        return f"{self.code} - {self.name}"


class JobCode(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        verbose_name=_("Vozilo"),
        on_delete=models.SET_NULL,
        related_name='job_codes',
        null=True
    )

    organizational_unit = models.ForeignKey(
        OrganizationalUnit,
        verbose_name=_("Organizaciona jedinica"),
        on_delete=models.SET_NULL,
        related_name='vehicle_assignments',
        null=True
    )

    assigned_date = models.DateField(verbose_name=_("Datum dodele"))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["vehicle", "assigned_date"], name="unique_vehicle_assigned_date"),
        ]
        indexes = [
            models.Index(fields=["vehicle", "-assigned_date", "-id"]),
            models.Index(fields=["organizational_unit"]),
        ]

    def __str__(self):
        return f"{self.vehicle} -> {self.organizational_unit} (Datum dodele: {self.assigned_date})"



class Lease(models.Model):
    LONG_TERM_LEASE_TYPE_VALUES = ('dugorocni', 'dugoročni', 'dugoročnI')
    LEASE_TYPE_CHOICES = [
        ('finansijski', 'Finansijski'),
        ('operativni', 'Operativni'),
        ('dugorocni', 'Dugoročni najam'),
    ]

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='leases',
        verbose_name=_("Vozilo")
    )

    partner_code = models.CharField(max_length=20, verbose_name=_("Šifra partnera"))
    partner_name = models.CharField(max_length=100, verbose_name=_("Naziv partnera"))
    job_code = models.CharField(max_length=20, verbose_name=_("Šifra posla"))
    contract_number = models.CharField(max_length=50, verbose_name=_("Broj ugovora"))
    current_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Trenutna rata / iznos otplate"))

    lease_type = models.CharField(
        max_length=20,
        choices=LEASE_TYPE_CHOICES,
        default='finansijski',
        verbose_name=_("Vrsta lizinga")
    )

    start_date = models.DateField(verbose_name=_("Datum početka"))
    end_date = models.DateField(verbose_name=_("Datum završetka"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))

    def __str__(self):
        return f"Lizing za {self.vehicle.chassis_number} ({self.lease_type}) – {self.partner_name}"

    @property
    def is_long_term_rental(self):
        return self.lease_type in self.LONG_TERM_LEASE_TYPE_VALUES

    @property
    def lease_type_label(self):
        if self.is_long_term_rental:
            return "Dugoročni najam"
        return self.get_lease_type_display()


class LeaseInterest(models.Model):
    lease = models.ForeignKey(
        Lease,
        on_delete=models.CASCADE,
        related_name='lease_interests',
        verbose_name=_("Lizing")
    )
    year = models.IntegerField(verbose_name=_("Godina"))
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Iznos kamate"))

    class Meta:
        unique_together = ('year', 'lease')

    def __str__(self):
        return f"Kamata za ugovor {self.lease.contract_number} za godinu {self.year}"


class Policy(models.Model):
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='policies',
        verbose_name=_("Vozilo")
    )
    partner_pib = models.IntegerField(verbose_name=_("PIB partnera"))
    partner_name = models.CharField(max_length=100, verbose_name=_("Naziv partnera"))
    invoice_id = models.IntegerField(verbose_name=_("ID fakture"), unique=True)
    invoice_number = models.CharField(max_length=50, verbose_name=_("Broj fakture"))
    issue_date = models.DateField(verbose_name=_("Datum izdavanja"))
    insurance_type = models.CharField(max_length=50, verbose_name=_("Tip osiguranja"))
    policy_number = models.CharField(max_length=50, verbose_name=_("Broj polise"))
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos premije"))
    start_date = models.DateField(verbose_name=_("Datum početka"))
    end_date = models.DateField(verbose_name=_("Datum završetka"))
    first_installment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos prve rate"))
    other_installments_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos ostalih rata"))
    number_of_installments = models.IntegerField(verbose_name=_("Broj rata"))
    is_renewable = models.BooleanField(
        default=True,
        choices=YES_NO_CHOICES,
        verbose_name=_("Da li se polisa obnavlja?")
    )

    def __str__(self):
        return f"Polisa {self.policy_number} – {self.partner_name}"


class DraftPolicy(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name='draft_policies',
        verbose_name=_("Vozilo"),
        null=True, blank=True
    )
    partner_pib = models.IntegerField(verbose_name=_("PIB partnera"), null=True, blank=True)
    partner_name = models.CharField(max_length=100, verbose_name=_("Naziv partnera"), null=True, blank=True)
    invoice_id = models.IntegerField(verbose_name=_("ID fakture"), unique=True, null=True, blank=True)
    invoice_number = models.CharField(max_length=50, verbose_name=_("Broj fakture"), null=True, blank=True)
    issue_date = models.DateField(verbose_name=_("Datum izdavanja"), null=True, blank=True)
    insurance_type = models.CharField(max_length=50, verbose_name=_("Tip osiguranja"), null=True, blank=True)
    policy_number = models.CharField(max_length=50, verbose_name=_("Broj polise"), null=True, blank=True)
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos premije"), null=True, blank=True)
    start_date = models.DateField(verbose_name=_("Datum početka"), null=True, blank=True)
    end_date = models.DateField(verbose_name=_("Datum završetka"), null=True, blank=True)
    first_installment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos prve rate"), null=True, blank=True)
    other_installments_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos ostalih rata"), null=True, blank=True)
    number_of_installments = models.IntegerField(verbose_name=_("Broj rata"), null=True, blank=True)

    def is_complete(self):
        return all(
            getattr(self, field_name)
            for field_name in [
                'partner_pib',
                'partner_name',
                'invoice_id',
                'invoice_number',
                'issue_date',
                'insurance_type',
                'policy_number',
                'premium_amount',
                'start_date',
                'end_date',
                'first_installment_amount',
                'other_installments_amount',
                'number_of_installments'
            ]
        )

class FuelConsumption(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='fuel_consumptions',
        verbose_name=_("Vozilo")
    )
    date = models.DateTimeField(verbose_name=_("Datum"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Količina"))
    fuel_type = models.CharField(max_length=20, verbose_name=_("Vrsta goriva"))
    cost_bruto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos – bruto"))
    cost_neto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos – neto"))
    supplier = models.CharField(max_length=50, verbose_name=_("Dobavljač"))
    job_code = models.CharField(max_length=50, verbose_name=_("Šifra posla"), blank=True, null=True)
    mileage = models.IntegerField(verbose_name=_("Kilometraža"))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['date', 'cost_bruto', 'amount'], name='unique_fuel_consumption')
        ]

    def __str__(self):
        return f"Potrošnja goriva {self.vehicle.chassis_number} – {self.date}"


class Employee(models.Model):
    GENDER_CHOICES = [
        ('M', 'Muški'),
        ('F', 'Ženski'),
    ]

    employee_code = models.IntegerField(unique=True, verbose_name=_("Šifra zaposlenog"))
    title = models.CharField(max_length=20, verbose_name=_("Titula"), blank=True, null=True)
    first_name = models.CharField(max_length=50, verbose_name=_("Ime"), blank=True, null=True)
    last_name = models.CharField(max_length=50, verbose_name=_("Prezime"), blank=True, null=True)
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
    education = models.CharField(max_length=255, verbose_name=_("Škola"), blank=True, null=True)
    job_code = models.CharField(max_length=20, verbose_name=_("Šifra zanimanja"), blank=True, null=True)
    job_title = models.CharField(max_length=255, verbose_name=_("Naziv zanimanja"), blank=True, null=True)
    status_code = models.CharField(max_length=10, verbose_name=_("Šifra statusa"), blank=True, null=True)
    status_name = models.CharField(max_length=255, verbose_name=_("Naziv statusa"), blank=True, null=True)
    slava = models.CharField(max_length=100, verbose_name=_("Slava"), blank=True, null=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Incident(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='incidents',
        verbose_name=_("Zaposleni")
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='incidents',
        verbose_name=_("Vozilo")
    )
    violation = models.TextField(verbose_name=_("Prekršaj"))
    date = models.DateField(verbose_name=_("Datum"))
    location = models.CharField(max_length=100, verbose_name=_("Lokacija"))
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos kazne"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))

    def __str__(self):
        # Employee nema polje `name`, pa koristimo __str__ iz Employee
        return f"Incident – {self.employee} / {self.vehicle.chassis_number} ({self.date})"


class PutniNalog(models.Model):
    CURRENCY_CHOICES = [
        ("RSD", "RSD"),
        ("USD", "USD"),
        ("EUR", "EUR"),
    ]
    order_number = models.CharField(
        max_length=20,
        verbose_name=_("Broj naloga"),
        unique=True
    )
    order_date = models.DateField(
        verbose_name=_("Datum izdavanja naloga"),
        default=timezone.now
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='travel_orders',
        verbose_name=_ ("Zaposleni"),
        null=True,
        blank=True
    )
    other_employee_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name=_ ("Zaposleni (ostalo)")
    )
    job_code = models.ForeignKey(
        OrganizationalUnit,
        on_delete=models.CASCADE,
        related_name='travel_order_job_code',
        verbose_name=_("Troškovi idu na teret")
    )
    travel_location = models.CharField(max_length=100, verbose_name=_("Mesto putovanja"))
    task = models.TextField(verbose_name=_("Zadatak"))
    napomena = models.TextField(verbose_name=_("Napomena"), blank=True, null=True)
    contract_offer = models.CharField(max_length=50, verbose_name=_("Ugovor / ponuda"), blank=True, null=True)

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='travel_orders',
        verbose_name=_("Vozilo"),
        null=True,
        blank=True
    )
    other_vehicle = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Prevozno sredstvo (ostalo)")
    )
    
    travel_date = models.DateField(verbose_name=_("Datum putovanja"))
    number_of_days = models.PositiveIntegerField(verbose_name=_("Broj dana"))
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Isplata/Akontacija"))
    advance_payment_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="RSD",
        verbose_name=_ ("Valuta akontacije")
    )

    daily_allowance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Dnevnica"),
        default=2600
    )

    is_weekly = models.BooleanField(
        default=False,
        verbose_name=_("Nedeljni nalog")
    )

    opravdan = models.BooleanField(
        default=False,
        verbose_name=_("Opravdan")
    )

    storniran = models.BooleanField(
        default=False,
        verbose_name=_("Storniran")
    )

    def generate_order_number(self):
        center_code = getattr(self.job_code, "center", None)
        if not center_code:
            raise ValueError("Nedostaje centar za putni nalog.")

        center_code = str(center_code).strip()

        year = (self.travel_date or datetime.date.today()).year
        prefix = f"{center_code}/{year}-"
        existing = PutniNalog.objects.filter(order_number__startswith=prefix).values_list(
            "order_number", flat=True
        )
        max_number = 0
        for order_number in existing:
            try:
                num_part = order_number.split(prefix, 1)[1]
                max_number = max(max_number, int(num_part))
            except Exception:
                continue

        start_sequence = getattr(self, "_start_sequence", None)
        if max_number == 0:
            if not start_sequence:
                has_any_for_center = PutniNalog.objects.filter(
                    order_number__startswith=f"{center_code}/"
                ).exists()
                if not has_any_for_center:
                    raise ValueError("Nedostaje početni broj za izabrani centar/godinu.")
                current_number = 1
            else:
                current_number = int(start_sequence)
        else:
            current_number = max_number + 1

        return f"{center_code}/{year}-{current_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Nalog {self.order_number} - {self.employee} ({self.travel_date})"


class PutniNalogSequence(models.Model):
    center_code = models.CharField(max_length=10, verbose_name=_("Šifra centra"))
    year = models.PositiveIntegerField(verbose_name=_("Godina"))
    next_number = models.PositiveIntegerField(verbose_name=_("Sledeći broj"), default=1)

    class Meta:
        verbose_name = _("Brojač putnih naloga")
        verbose_name_plural = _("Brojači putnih naloga")
        unique_together = ("center_code", "year")

    def __str__(self):
        return f"{self.center_code}/{self.year} -> {self.next_number}"


class VehicleTravelOrder(models.Model):
    pn_number = models.PositiveIntegerField(
        verbose_name=_("PN broj"),
        unique=True,
        blank=True,
        null=True,
    )
    created_at = models.DateField(
        default=timezone.localdate,
        verbose_name=_("Datum otvaranja naloga"),
    )
    closed_at = models.DateField(
        verbose_name=_("Datum zatvaranja naloga"),
        blank=True,
        null=True,
    )
    start_mileage = models.IntegerField(
        verbose_name=_("Početna kilometraža"),
        blank=True,
        null=True,
    )
    end_mileage = models.IntegerField(
        verbose_name=_("Krajnja kilometraža"),
        blank=True,
        null=True,
    )
    rbz = models.CharField(
        max_length=32,
        verbose_name=_("R.b.z."),
        unique=True,
        blank=True,
        null=True,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="vehicle_travel_orders",
        verbose_name=_("Zaposleni"),
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="vehicle_travel_orders",
        verbose_name=_("Vozilo"),
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("Putni nalog vozila")
        verbose_name_plural = _("Putni nalozi vozila")

    def __str__(self):
        return f"PN {self.pn_number} - {self.vehicle}"

    def save(self, *args, **kwargs):
        if not self.pn_number:
            with transaction.atomic():
                last_number = (
                    VehicleTravelOrder.objects.select_for_update()
                    .order_by("-pn_number")
                    .values_list("pn_number", flat=True)
                    .first()
                    or 0
                )
                self.pn_number = last_number + 1
                if not self.rbz:
                    self.rbz = f"PN-{self.pn_number}"
                return super().save(*args, **kwargs)
        if not self.rbz:
            self.rbz = f"PN-{self.pn_number}"
        return super().save(*args, **kwargs)


class ServiceType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Naziv tipa servisa"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))

    def __str__(self):
        return self.name


class Service(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name='services',
        verbose_name=_("Vozilo"),
        blank=True,
        null=True
    )
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name=_("Tip servisa"),
        null=True
    )
    service_date = models.DateField(verbose_name=_("Datum servisa"), null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Trošak"))
    provider = models.CharField(max_length=100, verbose_name=_("Dobavljač"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))

    def __str__(self):
        return f"{self.service_type.name} za {self.vehicle.chassis_number} na datum: {self.service_date}"


class ServiceTransaction(models.Model):
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='service_transactions',
        verbose_name=_("Vozilo")
    )
    god = models.IntegerField(verbose_name=_("Godina"))

    sif_par_pl = models.CharField(max_length=20, verbose_name=_("Šifra partnera (PL)"))
    naz_par_pl = models.CharField(max_length=255, verbose_name=_("Naziv partnera (PL)"))
    datum = models.DateField(verbose_name=_("Datum"))
    sif_vrs = models.CharField(max_length=10, verbose_name=_("Šifra vrste"))
    br_naloga = models.CharField(max_length=50, verbose_name=_("Broj naloga"))
    vez_dok = models.CharField(max_length=50, verbose_name=_("Vezani dokument"))
    knt_pl = models.CharField(max_length=20, verbose_name=_("Konto PL"))
    potrazuje = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Potražuje"))

    sif_par_npl = models.CharField(max_length=20, verbose_name=_("Šifra partnera (NPL)"))
    knt_npl = models.CharField(max_length=20, verbose_name=_("Konto NPL"))
    duguje = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Duguje"))

    konto_vozila = models.CharField(max_length=20, verbose_name=_("Konto vozila"))
    kom = models.TextField(verbose_name=_("Komada"), blank=True, null=True)

    popravka_kategorija = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Kategorija popravke (povezana)")
    )

    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), blank=True, null=True)

    nije_garaza = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_("Nije garaža")
    )

    napomena = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['datum', 'duguje', 'vez_dok', 'br_naloga'],
                name='unique_service_transaction'
            )
        ]

    def __str__(self):
        return f"{self.br_naloga} - {self.naz_par_pl} ({self.datum})"



class Kvar(models.Model):
    """Prijava kvara na vozilu (garaza)."""
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )

    class WorkType(models.TextChoices):
        MALI_SERVIS = ("mali_servis", _("Mali servis"))
        VELIKI_SERVIS = ("veliki_servis", _("Veliki servis"))
        POPRAVKA = ("popravka", _("Popravka"))

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="kvarovi",
        verbose_name=_("Vozilo"),
    )
    work_type = models.CharField(
        max_length=20,
        choices=WorkType.choices,
        default=WorkType.POPRAVKA,
        verbose_name=_("Vrsta intervencije"),
    )
    kilometraza = models.PositiveIntegerField(verbose_name=_("Kilometraža"))
    opis = models.TextField(verbose_name=_("Opis kvara"))
    napomena = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))
    van_ims = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_("Popravka van IMS-a"),
        help_text=_("Označi 'Da' ako se kvar rešava van IMS garaže."),
    )
    rbz = models.CharField(max_length=32, verbose_name=_("R.b.z."), blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Datum i vreme prijave"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Kvar vozila")
        verbose_name_plural = _("Kvarovi vozila")

    def __str__(self):
        return f"Kvar {self.vehicle} ({self.created_at:%d.%m.%Y %H:%M})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.rbz and self.pk:
            self.rbz = f"PK-{self.pk}/{timezone.now().year}"
            super().save(update_fields=["rbz"])


class KvarPart(models.Model):
    """Stavke delova vezane za prijavu kvara (radni nalog)."""
    kvar = models.ForeignKey(Kvar, on_delete=models.CASCADE, related_name="parts", verbose_name=_("Kvar"))
    name = models.CharField(max_length=255, verbose_name=_("Naziv dela"))
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1, verbose_name=_("Količina"))
    uom = models.CharField(max_length=30, default="kom", verbose_name=_("Jedinica mere"))

    class Meta:
        verbose_name = _("Deo za kvar")
        verbose_name_plural = _("Delovi za kvar")

    def __str__(self):
        return f"{self.name} ({self.quantity})"


class ProcurementRequest(models.Model):
    """Zahtev za nabavku (GZN)."""

    job_code = models.ForeignKey(
        OrganizationalUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="procurement_requests",
        verbose_name=_("Sifra posla (OJ)"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Datum kreiranja"))
    number = models.CharField(max_length=32, verbose_name=_("Broj GZN"), unique=True, blank=True, null=True)
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("Zahtev za nabavku")
        verbose_name_plural = _("Zahtevi za nabavku")

    def __str__(self):
        return self.number or f"GZN - {self.pk}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number and self.pk:
            self.number = f"GZN-{self.pk}/{timezone.now().year}"
            super().save(update_fields=["number"])


class ProcurementItem(models.Model):
    request = models.ForeignKey(
        ProcurementRequest,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Zahtev za nabavku"),
    )
    name = models.CharField(max_length=255, verbose_name=_("Naziv materijala / usluge"))
    uom = models.CharField(max_length=30, verbose_name=_("Jedinica mere"))
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Kolicina"))
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Napomena"))

    class Meta:
        verbose_name = _("Stavka zahteva za nabavku")
        verbose_name_plural = _("Stavke zahteva za nabavku")

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.uom})"


class DraftServiceTransaction(models.Model):
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name='draft_service_transactions',
        verbose_name=_("Vozilo"),
        null=True,
        blank=True
    )

    god = models.IntegerField(verbose_name=_("Godina"), null=True, blank=True)
    sif_par_pl = models.CharField(max_length=20, verbose_name=_("Šifra partnera (PL)"), null=True, blank=True)
    naz_par_pl = models.CharField(max_length=255, verbose_name=_("Naziv partnera (PL)"), null=True, blank=True)

    datum = models.DateField(verbose_name=_("Datum"))
    sif_vrs = models.CharField(max_length=10, verbose_name=_("Šifra vrste"), null=True, blank=True)
    br_naloga = models.CharField(max_length=50, verbose_name=_("Broj naloga"))

    vez_dok = models.CharField(max_length=50, verbose_name=_("Vezani dokument"), blank=True, null=True)

    knt_pl = models.CharField(max_length=20, verbose_name=_("Konto PL"), null=True, blank=True)
    potrazuje = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Potražuje"), null=True, blank=True)

    sif_par_npl = models.CharField(max_length=20, verbose_name=_("Šifra partnera (NPL)"), null=True, blank=True)
    knt_npl = models.CharField(max_length=20, verbose_name=_("Konto NPL"), null=True, blank=True)
    duguje = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Duguje"), null=True, blank=True)

    konto_vozila = models.CharField(max_length=20, verbose_name=_("Konto vozila"), null=True, blank=True)

    kom = models.TextField(verbose_name=_("Komada"), blank=True, null=True)

    popravka_kategorija = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Kategorija popravke (povezana)")
    )

    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), null=True, blank=True)

    nije_garaza = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_("Da li ovaj servis pripada garaži?")
    )

    napomena = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['datum', 'duguje', 'vez_dok', 'br_naloga'],
                name='unique_draft_service_transaction'
            )
        ]

    def is_complete(self):
        # Polja kom i napomena se ne uzimaju u obzir
        return all([
            self.god,
            self.sif_par_pl,
            self.naz_par_pl,
            self.knt_pl,
            self.potrazuje,
            self.knt_npl,
            self.duguje,
            self.konto_vozila,
        ])


class Requisition(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='requisitions',
        verbose_name=_("Vozilo")
    )
    sif_pred = models.IntegerField(verbose_name=_("Šifra predmeta"))
    god = models.IntegerField(verbose_name=_("Godina"))
    br_dok = models.CharField(max_length=50, verbose_name=_("Broj dokumenta"))
    sif_vrsart = models.CharField(max_length=20, verbose_name=_("Šifra vrste artikla"))
    stavka = models.IntegerField(verbose_name=_("Stavka"))
    sif_art = models.CharField(max_length=20, verbose_name=_("Šifra artikla"))
    naz_art = models.CharField(max_length=255, verbose_name=_("Naziv artikla"))
    kol = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Količina"))
    cena = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Cena"))
    vrednost_nab = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Vrednost nabavke"))
    mesec_unosa = models.IntegerField(verbose_name=_("Mesec unosa"))
    datum_trebovanja = models.DateField(verbose_name=_("Datum trebovanja"))
    popravka_kategorija = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Kategorija popravke (povezana)")
    )
    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), null=True, blank=True)
    nije_garaza = models.BooleanField(verbose_name=_("Nije garaža"))
    napomena = models.TextField(verbose_name=_("Napomena"), blank=True, null=True)
    kvar = models.ForeignKey(
        Kvar,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requisitions",
        verbose_name=_("Kvar (IMS)")
    )

    def __str__(self):
        return f"Requisition {self.br_dok} for {self.naz_art} ({self.god})"


class DraftRequisition(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='draft_requisitions',
        verbose_name=_("Vozilo"),
        blank=True,
        null=True
    )
    sif_pred = models.IntegerField(verbose_name=_("Šifra predmeta"), blank=True, null=True)
    god = models.IntegerField(verbose_name=_("Godina"), null=True, blank=True)
    br_dok = models.CharField(max_length=50, verbose_name=_("Broj dokumenta"))
    sif_vrsart = models.CharField(max_length=50, verbose_name=_("Šifra vrste artikla"), null=True, blank=True)
    stavka = models.CharField(max_length=50, verbose_name=_("Stavka"), null=True, blank=True)
    sif_art = models.CharField(max_length=50, verbose_name=_("Šifra artikla"), null=True, blank=True)
    naz_art = models.CharField(max_length=255, verbose_name=_("Naziv artikla"), null=True, blank=True)
    kol = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Količina"), null=True, blank=True)
    cena = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Cena"), null=True, blank=True)
    vrednost_nab = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_("Vrednost nabavke"), null=True, blank=True)
    popravka_kategorija = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Kategorija popravke (povezana)")
    )
    mesec_unosa = models.IntegerField(verbose_name=_("Mesec unosa"), null=True, blank=True)
    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), null=True, blank=True)
    nije_garaza = models.BooleanField(verbose_name=_("Nije garaža"), default=False)
    datum_trebovanja = models.DateField(verbose_name=_("Datum trebovanja"), null=True, blank=True)
    napomena = models.TextField(verbose_name=_("Napomena"), null=True, blank=True)
    kvar = models.ForeignKey(
        Kvar,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="draft_requisitions",
        verbose_name=_("Kvar (IMS)")
    )

    def __str__(self):
        return f"Requisition {self.br_dok} for {self.naz_art} ({self.god})"

    def is_complete(self):
        return all([
            self.vehicle is not None,
            bool(self.popravka_kategorija),
            self.mesec_unosa is not None,
            self.datum_trebovanja is not None,
            self.kvar is not None,
        ])

    
class TransactionOMV(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name='omv_transactions',
        verbose_name=_("Vozilo"),
        blank=True,
        null=True
    )
    issuer = models.CharField(max_length=255, verbose_name=_("Issuer"))
    customer = models.CharField(max_length=255, verbose_name=_("Customer"))
    card = models.CharField(max_length=255, verbose_name=_("Card"))
    license_plate_no = models.CharField(max_length=20, verbose_name=_("License plate No"))
    transaction_date = models.DateTimeField(verbose_name=_("Transaction date"))
    product_inv = models.CharField(max_length=255, verbose_name=_("Product INV"), blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Quantity"), blank=True, null=True)
    gross_cc = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Gross CC"), blank=True, null=True)
    vat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("VAT"), blank=True, null=True)
    voucher = models.CharField(max_length=255, verbose_name=_("Voucher"), blank=True, null=True)
    mileage = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Mileage"), blank=True, null=True)
    corrected_mileage = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Corrected mileage"), blank=True, null=True)
    additional_info = models.TextField(verbose_name=_("Additional info"), blank=True, null=True)
    supply_country = models.CharField(max_length=255, verbose_name=_("Supply country"), blank=True, null=True)
    site_town = models.CharField(max_length=255, verbose_name=_("Site Town"), blank=True, null=True)
    product_del = models.CharField(max_length=255, verbose_name=_("Product DEL"), blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Unit price"), blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Amount"), blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Discount"), blank=True, null=True)
    surcharge = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Surcharge"), blank=True, null=True)
    vat_2010 = models.CharField(max_length=20, verbose_name=_("VAT2010"), blank=True, null=True)
    supplier_currency = models.CharField(max_length=20, verbose_name=_("Supplier currency"), blank=True, null=True)
    invoice_no = models.CharField(max_length=50, verbose_name=_("Invoice No"), blank=True, null=True)
    invoice_date = models.DateField(verbose_name=_("Invoice date"), blank=True, null=True)
    invoiced = models.BooleanField(default=False, verbose_name=_("Invoiced?"), blank=True, null=True)
    state = models.CharField(max_length=255, verbose_name=_("State"), blank=True, null=True)
    supplier = models.CharField(max_length=255, verbose_name=_("Supplier"), blank=True, null=True)
    cost_1 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Cost 1"), blank=True, null=True)
    cost_2 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Cost 2"), blank=True, null=True)
    reference_no = models.CharField(max_length=255, verbose_name=_("Reference No"), blank=True, null=True)
    record_type = models.CharField(max_length=50, verbose_name=_("Record type"), blank=True, null=True)
    amount_other = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Amount other"), blank=True, null=True)
    is_list_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Is list price?"), blank=True, null=True)
    approval_code = models.CharField(max_length=50, verbose_name=_("Approval code"), blank=True, null=True)
    date_to = models.DateField(verbose_name=_("Date to"), blank=True, null=True)
    final_trx = models.CharField(max_length=50, verbose_name=_("Final Trx"), blank=True, null=True)
    lpi = models.CharField(max_length=50, verbose_name=_("LPI"), blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['license_plate_no', 'transaction_date', 'product_inv'],
                name='unique_license_plate_transaction'
            )
        ]

    def __str__(self):
        return f"Transakcija za {self.license_plate_no} na dan {self.transaction_date}"


class TransactionNIS(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name='nis_transactions',
        verbose_name=_("Vozilo"),
        blank=True,
        null=True
    )
    kupac = models.CharField(max_length=255, verbose_name=_("Kupac"))
    sifra_kupca = models.CharField(max_length=50, verbose_name=_("Šifra kupca"))
    broj_kartice = models.CharField(max_length=50, verbose_name=_("Broj kartice"))
    kompanijski_kod_kupca = models.CharField(max_length=50, verbose_name=_("Kompanijski kod kupca"))
    zemlja_sipanja = models.CharField(max_length=50, verbose_name=_("Zemlja sipanja"))
    benzinska_stanica = models.CharField(max_length=255, verbose_name=_("Benzinska stanica"))
    id_transakcije = models.CharField(max_length=100, verbose_name=_("ID transakcije"))
    app_kod = models.CharField(max_length=50, verbose_name=_("App kod"))
    datum_transakcije = models.DateTimeField(verbose_name=_("Datum transakcije"))
    tociono_mesto = models.CharField(max_length=50, verbose_name=_("Točeno mesto"))
    naziv_kartice = models.CharField(max_length=100, verbose_name=_("Naziv kartice"), blank=True, null=True)
    licenca = models.CharField(max_length=50, verbose_name=_("Licenca"), blank=True, null=True)
    broj_gazdinstva = models.CharField(max_length=50, verbose_name=_("Broj gazdinstva"), blank=True, null=True)
    registarska_oznaka_vozila = models.CharField(max_length=50, verbose_name=_("Registarska oznaka vozila"))
    broj_racuna = models.CharField(max_length=50, verbose_name=_("Broj računa"))
    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), blank=True, null=True)
    sipanje_van_rezervoara = models.BooleanField(verbose_name=_("Sipanje van rezervoara"))
    naziv_proizvoda = models.CharField(max_length=255, verbose_name=_("Naziv proizvoda"))
    kolicina = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Količina"))
    kolicina_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Količina (kg)"), blank=True, null=True)
    popust = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Popust"))
    primenjen_popust = models.CharField(max_length=255, verbose_name=_("Primenjen popust"))
    cena_sa_kase = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Cena sa kase"))
    cena = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Cena"))
    total_sa_kase = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Total sa kase"))
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Total"))
    valuta = models.CharField(max_length=10, verbose_name=_("Valuta"))
    aktivirano_prekoracenje = models.BooleanField(verbose_name=_("Aktivirano prekoračenje"))
    kolicinsko_prekoracenje = models.BooleanField(verbose_name=_("Količinsko prekoračenje"))
    finansijsko_prekoracenje = models.BooleanField(verbose_name=_("Finansijsko prekoračenje"))
    nacin_ocitavanja_kartice = models.CharField(max_length=50, verbose_name=_("Način očitavanja kartice"))

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['datum_transakcije', 'registarska_oznaka_vozila', 'naziv_proizvoda'],
                name='unique_transaction'
            )
        ]

    def __str__(self):
        return f"Transakcija za {self.registarska_oznaka_vozila} na dan {self.datum_transakcije}"


class KaskoRate(models.Model):
    contract_number = models.CharField(max_length=255)
    year = models.IntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = '[dbo].[kasko_rate]'
        app_label = 'fleet'



class KontaVozila(models.Model):
    knt = models.CharField(_("Konto"), max_length=10, primary_key=True)
    naz_knt = models.CharField(_("Naziv konta"), max_length=200)

    class Meta:
        verbose_name = "Konto vozila"
        verbose_name_plural = "Konta vozila"

    def __str__(self):
        return f"{self.knt} - {self.naz_knt}"


class DraftInsurance(models.Model):
    vehicle = models.ForeignKey(
        "fleet.Vehicle",
        on_delete=models.CASCADE,
        related_name="draft_insurances",
        verbose_name=_("Vozilo"),
        blank=True,
        null=True,
    )

    god = models.IntegerField(_("Godina"), null=True, blank=True)
    sif_vrs = models.CharField(_("Šifra vrste"), max_length=20, null=True, blank=True)
    br_naloga = models.CharField(_("Broj naloga"), max_length=50)
    stavka = models.CharField(_("Stavka"), max_length=50, null=True, blank=True)
    oj = models.CharField(_("OJ"), max_length=50, null=True, blank=True)
    knt = models.CharField(_("Konto"), max_length=50, null=True, blank=True)
    datum = models.DateField(_("Datum"), null=True, blank=True)
    vez_dok = models.CharField(_("Vezani dokument"), max_length=50, null=True, blank=True)
    potrazuje = models.DecimalField(
        _("Potražuje"),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )
    kola = models.BooleanField(
        _("Odnosi se na auto"),
        default=True,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Draft osiguranje")
        verbose_name_plural = _("Draft osiguranja")
        indexes = [
            models.Index(fields=["god", "sif_vrs", "br_naloga", "stavka", "knt"]),
            models.Index(fields=["br_naloga"]),
        ]

    def __str__(self):
        return f"DraftInsurance {self.br_naloga}/{self.stavka} ({self.god})"

    def is_complete(self) -> bool:
        return all([
            self.vehicle is not None,
            self.datum is not None,
        ])


class Insurance(models.Model):
    vehicle = models.ForeignKey(
        "fleet.Vehicle",
        on_delete=models.PROTECT,
        related_name="insurances",
        verbose_name=_("Vozilo"),
    )

    god = models.IntegerField(_("Godina"), null=True, blank=True)
    sif_vrs = models.CharField(_("Šifra vrste"), max_length=20, null=True, blank=True)
    br_naloga = models.CharField(_("Broj naloga"), max_length=50)
    stavka = models.CharField(_("Stavka"), max_length=50, null=True, blank=True)
    oj = models.CharField(_("OJ"), max_length=50, null=True, blank=True)
    knt = models.CharField(_("Konto"), max_length=50, null=True, blank=True)
    datum = models.DateField(_("Datum"), null=True, blank=True)
    vez_dok = models.CharField(_("Vezani dokument"), max_length=50, null=True, blank=True)
    potrazuje = models.DecimalField(
        _("Potražuje"),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )
    kola = models.BooleanField(
        _("Odnosi se na auto"),
        default=True,
    )

    class Meta:
        verbose_name = _("Osiguranje")
        verbose_name_plural = _("Osiguranja")
        indexes = [
            models.Index(fields=["god", "sif_vrs", "br_naloga", "stavka", "knt"]),
            models.Index(fields=["br_naloga"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["god", "sif_vrs", "br_naloga", "stavka", "knt"],
                name="uniq_insurance_key",
            )
        ]

    def __str__(self):
        return f"Insurance {self.br_naloga}/{self.stavka} ({self.god})"



class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Naziv uloge"))
    slug = models.SlugField(max_length=120, unique=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktivna"))
    permissions = models.ManyToManyField(
        "PermissionCode",
        through="RolePermission",
        blank=True,
        related_name="roles",
        verbose_name=_("Dozvole"),
    )

    class Meta:
        verbose_name = _("Uloga")
        verbose_name_plural = _("Uloge")

    def __str__(self):
        return self.name


class PermissionCode(models.Model):
    code = models.CharField(max_length=150, unique=True, verbose_name=_("Kod dozvole"))
    label = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Naziv"))

    class Meta:
        verbose_name = _("Kod dozvole")
        verbose_name_plural = _("Kodovi dozvola")

    def __str__(self):
        return self.label or self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(PermissionCode, on_delete=models.CASCADE, related_name="role_permissions")

    class Meta:
        verbose_name = _( "Dozvola uloge")
        verbose_name_plural = _( "Dozvole uloga")
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role.slug}:{self.permission.code}"


class CustomUser(AbstractUser):
    allowed_centers = models.ManyToManyField(
        'OrganizationalUnit',
        blank=True,
        verbose_name=_("Dozvoljene organizacione jedinice"),
    )

    allowed_center_codes = models.CharField(
        _("Dozvoljeni centri (šifre)"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Unesi šifre centara odvojene zarezom, npr: 43, 12, 77"),
    )

    roles = models.ManyToManyField(
        Role,
        blank=True,
        verbose_name=_("Uloge"),
        related_name="users",
    )

    def __str__(self):
        return self.username









