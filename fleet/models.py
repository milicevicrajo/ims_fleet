from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, Group, Permission
import datetime

# <!-- ======================================================================= -->
#                 <!-- MODELI SAMOSTALNE APLIKACIJE -->
# <!-- ======================================================================= -->
class Vehicle(models.Model):
    inventory_number = models.CharField(max_length=20, unique=True, verbose_name=_("Inventarni broj"))
    chassis_number = models.CharField(max_length=17, unique=True, verbose_name=_("Broj šasije"))
    brand = models.CharField(max_length=50, verbose_name=_("Marka"))
    model = models.CharField(max_length=50, verbose_name=_("Model"))
    year_of_manufacture = models.IntegerField(verbose_name=_("Godina proizvodnje"))
    first_registration_date = models.DateField(verbose_name=_("Datum prve registracije"))
    color = models.CharField(max_length=30, verbose_name=_("Boja"))
    number_of_axles = models.IntegerField(verbose_name=_("Broj osovina"))
    engine_volume = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_("Zapremina motora"))
    engine_number = models.CharField(max_length=50, unique=True, verbose_name=_("Broj motora"))
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Masa"))
    engine_power = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_("Snaga motora"))
    load_capacity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Nosivost"))
    category = models.CharField(max_length=50, verbose_name=_("Kategorija"))
    maximum_permissible_weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Maksimalna dozvoljena masa"))
    fuel_type = models.CharField(max_length=20, verbose_name=_("Tip goriva"))
    number_of_seats = models.IntegerField(verbose_name=_("Broj sedišta"))
    purchase_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Nabavna vrednost vozila"))
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Knjigovodstvena vrednost vozila"), null=True)
    service_interval = models.IntegerField(verbose_name=_("Servisni interval"),default=15000)
    # Nova polja
    purchase_date = models.DateField(verbose_name=_("Datum nabavke"), null=True)  # Ovo je datum kada je vozilo nabavljeno
    partner_code = models.CharField(max_length=20, verbose_name=_("Šifra partnera"), null=True)  # Šifra partnera
    partner_name = models.CharField(max_length=100, verbose_name=_("Naziv partnera"), null=True)  # Naziv partnera
    invoice_number = models.CharField(max_length=50, verbose_name=_("Broj fakture"), null=True)  # Broj fakture
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))  # Opis
    
    otpis = models.BooleanField(_("Otpis"), default=False, editable=False)

    def __str__(self):
        # Pronađi registraciju vozila iz TrafficCard modela, ako postoji
        traffic_card = self.traffic_cards.first()
        if traffic_card:
            return f"{traffic_card.registration_number} - {self.brand} {self.model}"
        else:
            return f"{self.chassis_number} - {self.brand} {self.model}"

class TrafficCard(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='traffic_cards', verbose_name=_("Vozilo"))
    registration_number = models.CharField(
        max_length=10,  # Povećajte maksimalnu dužinu za dodatni karakter crtice
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2}\d{3,4}-[A-Z]{2}$',
                message=_('Registracioni broj mora biti u formatu AA999-AA ili AA9999-AA')
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

    # Polje za kačenje PDF-a saobraćajne dozvole
    traffic_card_pdf = models.FileField(
        upload_to='traffic_cards/',  # Folder gde će se čuvati datoteke
        verbose_name=_("PDF Saobraćajne dozvole"),
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.registration_number} valid until {self.valid_until}"

class OrganizationalUnit(models.Model):
    name = models.CharField(verbose_name=_("Naziv"), max_length=100)
    code = models.CharField(verbose_name=_("Šifra organizacione jedinice"), max_length=10, unique=True)
    center = models.CharField(verbose_name=_("Šifra centra"), max_length=10)

    
    def __str__(self):
        return f"{self.code}- {self.name}"

class JobCode(models.Model):
    vehicle = models.ForeignKey(Vehicle, verbose_name=_("Vozilo"), on_delete=models.SET_NULL, related_name='job_codes', null=True)
    organizational_unit = models.ForeignKey(OrganizationalUnit, verbose_name=_("Organizaciona jedinica"), on_delete=models.SET_NULL, related_name='vehicle_assignments', null=True)
    assigned_date = models.DateField(verbose_name=_("Datum dodele"))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['vehicle', 'assigned_date'], name='unique_vehicle_assigned_date')
        ]

    def __str__(self):
        return f"{self.vehicle} -> {self.organizational_unit} (Assigned on {self.assigned_date})"


class Lease(models.Model):
    LEASE_TYPE_CHOICES = [
        ('finansijski', 'Finansijski'),
        ('operativni', 'Operativni'),
        ('dugorocni', 'Dugoročni najam'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='leases', verbose_name=_("Vozilo"))
    partner_code = models.CharField(max_length=20, verbose_name=_("Šifra partnera"))
    partner_name = models.CharField(max_length=100, verbose_name=_("Naziv partnera"))
    job_code = models.CharField(max_length=20, verbose_name=_("Šifra posla"))
    contract_number = models.CharField(max_length=50, verbose_name=_("Broj ugovora"))
    current_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Trenutna vrednost otplate"))

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
        return f"Lizing za {self.vehicle.chassis_number} ({self.lease_type}) sa {self.partner_name} od {self.start_date} do {self.end_date}"




class LeaseInterest(models.Model):
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='lease_interests', verbose_name=_("Lizing"))
    year = models.IntegerField(verbose_name=_("Godina"))
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Iznos kamate"))

    class Meta:
        unique_together = ('year', 'lease')  # Kombinacija godina i broj ugovora mora biti jedinstvena

    def __str__(self):
        return f"Kamata za ugovor {self.lesae.contract_number} za godinu {self.year}"

class Policy(models.Model):
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )


    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='policies', verbose_name=_("Vozilo"))
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
        choices=YES_NO_CHOICES,  # Dodato choices
        verbose_name=_("Da li se polisa obnavlja?")
    )
    def __str__(self):
        return f"Polisa {self.policy_number} sa {self.partner_name}"

class DraftPolicy(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, related_name='draft_policies', verbose_name=_("Vozilo"), null=True, blank=True)
    partner_pib = models.IntegerField(verbose_name="PIB partnera", null=True, blank=True)
    partner_name = models.CharField(max_length=100, verbose_name="Naziv partnera", null=True, blank=True)
    invoice_id = models.IntegerField(verbose_name="ID fakture", unique=True, null=True, blank=True)
    invoice_number = models.CharField(max_length=50, verbose_name="Broj fakture", null=True, blank=True)
    issue_date = models.DateField(verbose_name="Datum izdavanja", null=True, blank=True)
    insurance_type = models.CharField(max_length=50, verbose_name="Tip osiguranja", null=True, blank=True)
    policy_number = models.CharField(max_length=50, verbose_name="Broj polise", null=True, blank=True)
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Iznos premije", null=True, blank=True)
    start_date = models.DateField(verbose_name="Datum početka", null=True, blank=True)
    end_date = models.DateField(verbose_name="Datum završetka", null=True, blank=True)
    first_installment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Iznos prve rate", null=True, blank=True)
    other_installments_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Iznos ostalih rata", null=True, blank=True)
    number_of_installments = models.IntegerField(verbose_name="Broj rata", null=True, blank=True)

    def is_complete(self):
        return all(
            getattr(self, field_name) is not None and getattr(self, field_name) != ''
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
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_consumptions', verbose_name=_("Vozilo"))
    date = models.DateTimeField(verbose_name=_("Datum"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Količina"))
    fuel_type = models.CharField(max_length=20, verbose_name=_("Tip goriva"))
    cost_bruto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos - Bruto"))
    cost_neto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos - Neto"))
    supplier = models.CharField(max_length=50, verbose_name=_("Dobavljač"))
    job_code = models.CharField(max_length=50, verbose_name=_("Šifra posla"),blank=True, null=True)
    mileage = models.IntegerField(verbose_name=_("Kilometraža"))
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['date', 'cost_bruto', 'amount'], name='unique_fuel_consumption')
        ]
    def __str__(self):
        return f"Potrosnja goriva {self.vehicle.chassis_number} na {self.date}"

class Employee(models.Model):
    GENDER_CHOICES = [
        ('M', 'Muški'),
        ('F', 'Ženski'),
    ]

    employee_code = models.IntegerField(unique=True, verbose_name=_("Šifra zaposlenog"))
    first_name = models.CharField(max_length=50, verbose_name=_("Ime"),blank=True, null=True)
    last_name = models.CharField(max_length=50, verbose_name=_("Preziime"),blank=True, null=True)
    position = models.CharField(max_length=100, verbose_name=_("Pozicija"))
    department_code = models.IntegerField(verbose_name=_("Šifra odeljenja"))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Pol"))
    date_of_birth = models.DateField(verbose_name=_("Datum rođenja"))
    date_of_joining = models.DateField(verbose_name=_("Datum zapošljavanja"))
    phone_number = models.CharField(max_length=20, verbose_name=_("Broj telefona"), blank=True, null=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

class Incident(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='incidents', verbose_name=_("Zaposleni"))
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='incidents', verbose_name=_("Vozilo"))
    violation = models.TextField(verbose_name=_("Prekršaj"))
    date = models.DateField(verbose_name=_("Datum"))
    location = models.CharField(max_length=100, verbose_name=_("Lokacija"))
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Iznos kazne"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))

    def __str__(self):
        return f"Incident for {self.employee.name} with vehicle {self.vehicle.chassis_number} on {self.date}"

class PutniNalog(models.Model):
    order_number = models.CharField(max_length=20, verbose_name=_("Broj naloga"), unique=True)
    order_date = models.DateField(verbose_name=_("Datum izdavanja naloga"), auto_now_add=True)

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='travel_orders', verbose_name=_("Zaposleni")
    )
    job_code = models.ForeignKey(
        OrganizationalUnit, on_delete=models.CASCADE, related_name='travel_order_job_code', verbose_name=_("Troškovi idu na teret"))
    travel_location = models.CharField(max_length=100, verbose_name=_("Mesto putovanja"))
    task = models.TextField(verbose_name=_("Zadatak"))
    contract_offer = models.CharField(max_length=50, verbose_name=_("Ugovor/ponuda"))
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name='travel_orders', verbose_name=_("Vozilo")
    )
    travel_date = models.DateField(verbose_name=_("Datum putovanja"))
    number_of_days = models.PositiveIntegerField(verbose_name=_("Broj dana"))
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Isplata"))

    daily_allowance = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Dnevnica"), default=2600
    )

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Nalog {self.order_number} - {self.employee.name} ({self.travel_date})"

class ServiceType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Naziv tipa servisa"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))

    def __str__(self):
        return self.name

class Service(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, related_name='services', verbose_name=_("Vozilo"), blank=True, null=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='services', verbose_name=_("Tip servisa"),null=True)
    service_date = models.DateField(verbose_name=_("Datum servisa"), null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Trošak"))
    provider = models.CharField(max_length=100, verbose_name=_("Dobavljač"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))

    def __str__(self):
        return f"{self.service_type.name} za {self.vehicle.chassis_number} Na datum: {self.service_date}"

class ServiceTransaction(models.Model):
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='service_transactions', verbose_name=_("Vozilo"))  # Dodata veza na Vehicle
    god = models.IntegerField(verbose_name=_("Godina"))
    sif_par_pl = models.CharField(max_length=20, verbose_name=_("Šifra partnera (pl)"))
    naz_par_pl = models.CharField(max_length=255, verbose_name=_("Naziv partnera (pl)"))
    datum = models.DateField(verbose_name=_("Datum"))
    sif_vrs = models.CharField(max_length=10, verbose_name=_("Šifra vrste"))
    br_naloga = models.CharField(max_length=50, verbose_name=_("Broj naloga"))
    vez_dok = models.CharField(max_length=50, verbose_name=_("Vezani dokument"))
    knt_pl = models.CharField(max_length=20, verbose_name=_("Konto pl"))
    potrazuje = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Potražuje"))
    sif_par_npl = models.CharField(max_length=20, verbose_name=_("Šifra partnera (npl)"))
    knt_npl = models.CharField(max_length=20, verbose_name=_("Konto npl"))
    duguje = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Duguje"))
    konto_vozila = models.CharField(max_length=20, verbose_name=_("Konto vozila"))
    kom = models.TextField(verbose_name=_("Komada"), blank=True, null=True)      
    popravka_kategorija = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kategorija popravke (povezana)"
    )
    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), blank=True, null=True)
    nije_garaza = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,  # Dodato choices
        verbose_name=_("Nije garaža")
    )
    napomena = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['datum', 'duguje', 'vez_dok', 'br_naloga'], name='unique_service_transaction')
        ]

    def __str__(self):
        return f"{self.br_naloga} - {self.naz_par_pl} ({self.datum})"
    
class DraftServiceTransaction(models.Model):
    YES_NO_CHOICES = (
        (True, _("Da")),
        (False, _("Ne")),
    )
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, related_name='draft_service_transactions', verbose_name=_("Vozilo"), null=True, blank=True)  # Dodata veza na Vehicle
    god = models.IntegerField(verbose_name="Godina", null=True, blank=True)
    sif_par_pl = models.CharField(max_length=20, verbose_name="Šifra partnera (pl)", null=True, blank=True)
    naz_par_pl = models.CharField(max_length=255, verbose_name="Naziv partnera (pl)", null=True, blank=True)
    datum = models.DateField(verbose_name=_("Datum"))
    sif_vrs = models.CharField(max_length=10, verbose_name="Šifra vrste", null=True, blank=True)
    br_naloga = models.CharField(max_length=50, verbose_name="Broj naloga")
    vez_dok = models.CharField(max_length=50, verbose_name="Vezani dokument", blank=True, null=True)
    knt_pl = models.CharField(max_length=20, verbose_name="Konto pl", null=True, blank=True)
    potrazuje = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Potražuje", null=True, blank=True)
    sif_par_npl = models.CharField(max_length=20, verbose_name="Šifra partnera (npl)", blank=True, null=True)
    knt_npl = models.CharField(max_length=20, verbose_name="Konto npl", null=True, blank=True)
    duguje = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Duguje", null=True, blank=True)
    konto_vozila = models.CharField(max_length=20, verbose_name="Konto vozila", null=True, blank=True)
    kom = models.TextField(verbose_name="Komada", blank=True, null=True)      
    popravka_kategorija = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kategorija popravke (povezana)"
    )

    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), null=True, blank=True)
    nije_garaza = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,  # Dodato choices
        verbose_name=_("Da li se ovaj servis ne pripada garaži?")
    )
    napomena = models.TextField(blank=True, null=True, verbose_name="Napomena")
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['datum', 'duguje', 'vez_dok', 'br_naloga'], name='unique_draft_service_transaction')
        ]

    def is_complete(self):
        # Polja `kom` i `napomena` se ne uzimaju u obzir za `is_complete` proveru
        return all([
            self.god, self.sif_par_pl, self.naz_par_pl, self.knt_pl, self.potrazuje, 
            self.knt_npl, self.duguje, self.konto_vozila
        ])

class Requisition(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='requisitions', verbose_name=_("Vozilo"))
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
        verbose_name="Kategorija popravke (povezana)"
    )
    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), null=True, blank=True)
    nije_garaza = models.BooleanField(verbose_name=_("Nije garaža"))
    napomena = models.TextField(verbose_name=_("Napomena"),blank=True, null=True )

    def __str__(self):
        return f"Requisition {self.br_dok} for {self.naz_art} ({self.god})"

class DraftRequisition(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='draft_requisitions', verbose_name=_("Vozilo"), blank=True, null=True)
    sif_pred = models.IntegerField(verbose_name=_("Šifra predmeta"), blank=True, null=True)
    god = models.IntegerField(null=True, blank=True)
    br_dok = models.CharField(max_length=50)
    sif_vrsart = models.CharField(max_length=50, null=True, blank=True)
    stavka = models.CharField(max_length=50, null=True, blank=True)
    sif_art = models.CharField(max_length=50, null=True, blank=True)
    naz_art = models.CharField(max_length=255, null=True, blank=True)
    kol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cena = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vrednost_nab = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    popravka_kategorija = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kategorija popravke (povezana)"
    )
    mesec_unosa = models.IntegerField(verbose_name=_("Mesec unosa"), null=True, blank=True)
    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), null=True, blank=True)
    nije_garaza = models.BooleanField(verbose_name=_("Nije garaža"), default=False)
    datum_trebovanja = models.DateField(null=True, blank=True)
    napomena = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Requisition {self.br_dok} for {self.naz_art} ({self.god})"
    
    def is_complete(self):
        return all([
            self.vehicle is not None,
            bool(self.popravka_kategorija),  # nije None i nije ""
            self.mesec_unosa is not None,
            self.datum_trebovanja is not None
        ])
    
class TransactionOMV(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, related_name='omv_transactions', verbose_name=_("Vozilo"), blank=True, null=True)
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
            models.UniqueConstraint(fields=['license_plate_no', 'transaction_date', 'product_inv'], name='unique_license_plate_transaction')
        ]

    def __str__(self):
        return f"Transakcija za {self.license_plate_no} na dan  {self.transaction_date}"

class TransactionNIS(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, related_name='nis_transactions', verbose_name=_("Vozilo"), blank=True, null=True)
    kupac = models.CharField(max_length=255, verbose_name=_("Kupac"))
    sifra_kupca = models.CharField(max_length=50, verbose_name=_("Šifra kupca"))
    broj_kartice = models.CharField(max_length=50, verbose_name=_("Broj kartice"))
    kompanijski_kod_kupca = models.CharField(max_length=50, verbose_name=_("Kompanijski kod kupca"))
    zemlja_sipanja = models.CharField(max_length=50, verbose_name=_("Zemlja sipanja"))
    benzinska_stanica = models.CharField(max_length=255, verbose_name=_("Benzinska stanica"))
    id_transakcije = models.CharField(max_length=100, verbose_name=_("ID transakcije"))
    app_kod = models.CharField(max_length=50, verbose_name=_("App kod"))
    datum_transakcije = models.DateTimeField(verbose_name=_("Datum transakcije"))
    tociono_mesto = models.CharField(max_length=50, verbose_name=_("Točiono mesto"))
    naziv_kartice = models.CharField(max_length=100, verbose_name=_("Naziv kartice"), blank=True, null=True)
    licenca = models.CharField(max_length=50, verbose_name=_("Licenca"), blank=True, null=True)
    broj_gazdinstva = models.CharField(max_length=50, verbose_name=_("Broj gazdinstva"), blank=True, null=True)
    registarska_oznaka_vozila = models.CharField(max_length=50, verbose_name=_("Registarska oznaka vozila"))
    broj_racuna = models.CharField(max_length=50, verbose_name=_("Broj računa"))
    kilometraza = models.IntegerField(verbose_name=_("Kilometraža"), blank=True, null=True)
    sipanje_van_rezervoara = models.BooleanField(verbose_name=_("Sipanje van rezervoara"))
    naziv_proizvoda = models.CharField(max_length=255, verbose_name=_("Naziv proizvoda"))
    kolicina = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Količina"))
    kolicina_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Količina KG"), blank=True, null=True)
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
        managed = False  # Django won't try to create or manage this table
        db_table = '[dbo].[kasko_rate]'  # Exact name of the view in the database
        app_label = 'your_app_name'



class CustomUser(AbstractUser):
    allowed_centers = models.ManyToManyField('OrganizationalUnit', blank=True)

    def __str__(self):
        return self.username



# <!-- ======================================================================= -->
#                            <!-- MODELI ZA NAPLATU -->
# <!-- ======================================================================= -->

class Kontakti(models.Model):
    id = models.AutoField(primary_key=True)  # Automatski ID
    sif_par = models.IntegerField()  # Više kontakata može imati istu šifru partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    kontakt = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    email = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomena = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kontakti'



class Napomene(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(db_column='naz_par', max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomene = models.CharField(db_column='napomene', max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    veliki = models.CharField(db_column='veliki', max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'napomene'


class Opomene(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    god = models.IntegerField(blank=True, null=True)
    br_opomene = models.IntegerField(blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    iznos = models.FloatField(blank=True, null=True)
    fakture = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomene = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'opomene'



class PozivPismo(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    god = models.IntegerField(blank=True, null=True)
    br_pisma = models.IntegerField(blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    iznos = models.FloatField(blank=True, null=True)
    fakture = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomene = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'poziv_pismo'


class PoziviTel(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    napomena = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pozivi_tel'


class SifBaket(models.Model):
    br_kategorije = models.FloatField(blank=True, null=True)
    baket = models.FloatField(blank=True, null=True)
    baket_rang = models.FloatField(blank=True, null=True)
    opis = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    akcija = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sif_baket'


class SifKategorija(models.Model):
    br_kategorije = models.FloatField(blank=True, null=True)
    kategorija = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sif_kategorija'


class Tuzbe(models.Model):
    id = models.AutoField(primary_key=True)  # Primarni ključ
    sif_par = models.FloatField(db_column='sif_par', blank=True, null=True)  # Šifra partnera
    naz_par = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    god = models.IntegerField(blank=True, null=True)
    br_opomene = models.IntegerField(blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    iznos = models.FloatField(blank=True, null=True)
    fakture = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)
    napomene = models.CharField(max_length=255, db_collation='Latin1_General_CI_AI', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tuzbe'


# <!-- ======================================================================= -->
#                            <!-- VIEWS IZ BAZA NAPLATA -->
# <!-- ======================================================================= -->

# View za bazu dugovanja
class Baza(models.Model):
    god = models.IntegerField()
    sif_par = models.IntegerField()
    naz_par = models.CharField(max_length=255)
    sif_vrs = models.CharField(max_length=50, blank=True, null=True)
    br_naloga = models.IntegerField()
    dat_naloga = models.DateTimeField()
    stavka = models.IntegerField()
    vez_dok = models.CharField(max_length=255, blank=True, null=True)
    datum = models.DateTimeField()
    oj = models.IntegerField()
    dpo = models.DateTimeField()
    kom = models.CharField(max_length=255, blank=True, null=True)
    skr_naz = models.CharField(max_length=255, blank=True, null=True)
    deviza = models.CharField(max_length=50, blank=True, null=True)
    promena = models.DecimalField(max_digits=15, decimal_places=2)
    stavka_k = models.CharField(max_length=255, blank=True, null=True)
    d_p = models.CharField(max_length=10, blank=True, null=True)
    knt = models.CharField(max_length=255, blank=True, null=True)
    dug = models.DecimalField(max_digits=15, decimal_places=2)  # Zamenjuje "saldo"
    pot = models.DecimalField(max_digits=15, decimal_places=2)
    sif_pos = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'baza'


# View za dodelu baketa
class DodelaBucketa(models.Model):
    sif_par = models.IntegerField()
    naz_par = models.CharField(max_length=255)
    vez_dok = models.CharField(max_length=255, blank=True, null=True)
    sif_pos = models.CharField(max_length=255, blank=True, null=True)
    duguje = models.DecimalField(max_digits=15, decimal_places=2)
    potrazuje = models.DecimalField(max_digits=15, decimal_places=2)
    saldo = models.DecimalField(max_digits=15, decimal_places=2)
    dpo = models.DateTimeField()
    danasnji_datum = models.DateTimeField()
    broj_dana = models.IntegerField()
    baket = models.FloatField()  # Ovo određuje koji je bucket
    kategorija = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dodela_bucketa'



# View za ispravke
class Ispravke(models.Model):
    god = models.IntegerField()
    sif_par = models.IntegerField()
    naz_par = models.CharField(max_length=255)
    sif_vrs = models.CharField(max_length=50, blank=True, null=True)
    br_naloga = models.IntegerField()
    dat_naloga = models.DateTimeField()
    stavka = models.IntegerField()
    vez_dok = models.CharField(max_length=255, blank=True, null=True)
    datum = models.DateTimeField()
    oj = models.IntegerField()
    dpo = models.DateTimeField()
    kom = models.CharField(max_length=255, blank=True, null=True)
    skr_naz = models.CharField(max_length=255, blank=True, null=True)
    deviza = models.CharField(max_length=50, blank=True, null=True)
    promena = models.DecimalField(max_digits=15, decimal_places=2)
    stavka_k = models.CharField(max_length=255, blank=True, null=True)
    d_p = models.CharField(max_length=10, blank=True, null=True)
    knt = models.CharField(max_length=255, blank=True, null=True)
    naz_knt = models.CharField(max_length=255, blank=True, null=True)
    dug = models.DecimalField(max_digits=15, decimal_places=2)
    pot = models.DecimalField(max_digits=15, decimal_places=2)
    sif_pos = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ispravke'



# View za partnere
class Partneri(models.Model):
    sif_pred = models.IntegerField()
    grupa = models.IntegerField()
    sif_par = models.IntegerField()
    naz_par = models.CharField(max_length=255)
    ulica_par = models.CharField(max_length=255, blank=True, null=True)
    p_b_par = models.CharField(max_length=50, blank=True, null=True)  # Poštanski broj
    mesto_par = models.CharField(max_length=255, blank=True, null=True)
    zr = models.CharField(max_length=255, blank=True, null=True)  # Žiro račun
    mb = models.CharField(max_length=255, blank=True, null=True)  # Matični broj
    telefon = models.CharField(max_length=255, blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    lice = models.CharField(max_length=255, blank=True, null=True)  # Kontakt osoba
    web = models.CharField(max_length=255, blank=True, null=True)
    proc_rabata = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    br_dana = models.IntegerField(blank=True, null=True)
    vlasnik = models.CharField(max_length=255, blank=True, null=True)
    pib = models.CharField(max_length=50, blank=True, null=True)
    zemlja = models.CharField(max_length=50, blank=True, null=True)
    proc_rabata1 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    proc_rabata2 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    pdv_obveznik = models.CharField(max_length=50, blank=True, null=True)
    sif_ter = models.CharField(max_length=255, blank=True, null=True)
    JBKJS = models.CharField(max_length=255, blank=True, null=True)
    CRF = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'partneri'

