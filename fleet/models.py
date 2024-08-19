from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

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
    purchase_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Vrednost vozila"))

    def __str__(self):
        return f"{self.brand} {self.model} ({self.chassis_number})"

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
        verbose_name=_("Registracioni broj")
    )
    issue_date = models.DateField(verbose_name=_("Datum izdavanja"))
    valid_until = models.DateField(verbose_name=_("Važi do"))
    traffic_card_number = models.CharField(max_length=50, verbose_name=_("Broj saobraćajne dozvole"))
    serial_number = models.CharField(max_length=50, verbose_name=_("Serijski broj"))
    owner = models.CharField(max_length=100, verbose_name=_("Vlasnik"))
    homologation_number = models.CharField(max_length=50, verbose_name=_("Homologacioni broj"))

    def __str__(self):
        return f"{self.registration_number} valid until {self.valid_until}"

class JobCode(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='job_codes', verbose_name=_("Vozilo"))
    job_code = models.CharField(max_length=20, verbose_name=_("Šifra posla"))
    assigned_date = models.DateField(verbose_name=_("Datum dodele"))

    def __str__(self):
        return f"{self.job_code} assigned to {self.vehicle.chassis_number} from {self.assigned_date}"

class Lease(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='leases', verbose_name=_("Vozilo"))
    partner_code = models.CharField(max_length=20, verbose_name=_("Šifra partnera"))
    partner_name = models.CharField(max_length=100, verbose_name=_("Naziv partnera"))
    job_code = models.CharField(max_length=20, verbose_name=_("Šifra posla"))
    contract_number = models.CharField(max_length=50, verbose_name=_("Broj ugovora"))
    start_date = models.DateField(verbose_name=_("Datum početka"))
    end_date = models.DateField(verbose_name=_("Datum završetka"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))

    def __str__(self):
        return f"Lease for {self.vehicle.chassis_number} with {self.partner_name} from {self.start_date} to {self.end_date}"

class Policy(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='policies', verbose_name=_("Vozilo"))
    partner_pib = models.CharField(max_length=20, verbose_name=_("PIB partnera"))
    partner_name = models.CharField(max_length=100, verbose_name=_("Naziv partnera"))
    invoice_id = models.IntegerField(verbose_name=_("ID fakture"))
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

    def __str__(self):
        return f"Policy {self.policy_number} for {self.vehicle.chassis_number} with {self.partner_name}"

class FuelConsumption(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_consumptions', verbose_name=_("Vozilo"))
    date = models.DateField(verbose_name=_("Datum"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Količina"))
    fuel_type = models.CharField(max_length=20, verbose_name=_("Tip goriva"))
    supplier = models.CharField(max_length=50, verbose_name=_("Dobavljač"))

    def __str__(self):
        return f"Fuel consumption for {self.vehicle.chassis_number} on {self.date}"

class Employee(models.Model):
    GENDER_CHOICES = [
        ('M', 'Muški'),
        ('F', 'Ženski'),
    ]

    employee_code = models.CharField(max_length=20, unique=True, verbose_name=_("Šifra zaposlenog"))
    name = models.CharField(max_length=100, verbose_name=_("Ime i prezime"))
    position = models.CharField(max_length=100, verbose_name=_("Pozicija"))
    department_code = models.IntegerField(verbose_name=_("Šifra odeljenja"))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Pol"))
    date_of_birth = models.DateField(verbose_name=_("Datum rođenja"))
    date_of_joining = models.DateField(verbose_name=_("Datum zapošljavanja"))
    phone_number = models.CharField(max_length=20, verbose_name=_("Broj telefona"))

    def __str__(self):
        return self.name

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
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='travel_orders', verbose_name=_("Zaposleni"))
    job_code = models.CharField(max_length=20, verbose_name=_("Šifra posla"))
    travel_location = models.CharField(max_length=100, verbose_name=_("Mesto putovanja"))
    contract_offer = models.CharField(max_length=50, verbose_name=_("Ugovor/ponuda"))
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='travel_orders', verbose_name=_("Vozilo"))
    travel_date = models.DateField(verbose_name=_("Datum putovanja"))
    number_of_days = models.IntegerField(verbose_name=_("Broj dana"))
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Avans"))
    travel_expenses = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Troškovi putovanja"))
    settlement_date = models.DateField(verbose_name=_("Datum likvidacije"))

    def __str__(self):
        return f"Travel Order for {self.employee.name} on {self.travel_date}"

class ServiceType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Naziv tipa servisa"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))

    def __str__(self):
        return self.name

class Service(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='services', verbose_name=_("Vozilo"))
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='services', verbose_name=_("Tip servisa"))
    service_date = models.DateField(verbose_name=_("Datum servisa"))
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Trošak"))
    provider = models.CharField(max_length=100, verbose_name=_("Dobavljač"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))

    def __str__(self):
        return f"{self.service_type.name} for {self.vehicle.chassis_number} on {self.service_date}"
