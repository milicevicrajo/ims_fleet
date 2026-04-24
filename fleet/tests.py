import datetime
from decimal import Decimal

from django.test import TestCase
from django.test import RequestFactory
from django.utils import timezone

from .forms import VehicleTravelOrderForm
from .models import TransactionNIS, TransactionOMV
from .models import Employee, Vehicle, VehicleTravelOrder
from .utils import filter_nis_fuel_queryset, filter_omv_fuel_queryset
from .views_garaza import VehicleTravelOrderCreateView, VehicleTravelOrderDetailView


class FuelProductFilterTests(TestCase):
	@staticmethod
	def _dt(year, month, day, hour, minute):
		return timezone.make_aware(datetime.datetime(year, month, day, hour, minute))

	def test_filter_omv_fuel_queryset_excludes_putarina_and_adblue(self):
		fuel = TransactionOMV.objects.create(
			issuer="OMV",
			customer="IMS",
			card="123",
			license_plate_no="BG2024-OT",
			transaction_date=self._dt(2026, 4, 21, 9, 15),
			product_inv="OMV EVRO DIZEL",
			quantity=Decimal("43.33"),
			gross_cc=Decimal("9402.61"),
			vat=Decimal("1567.10"),
			voucher="00294721",
			mileage=Decimal("61610"),
			unit_price=Decimal("217.00"),
			amount=Decimal("9402.61"),
		)
		TransactionOMV.objects.create(
			issuer="OMV",
			customer="IMS",
			card="123",
			license_plate_no="BG2024-OT",
			transaction_date=self._dt(2026, 4, 21, 17, 45),
			product_inv="Putarina",
			quantity=Decimal("4700.00"),
			gross_cc=Decimal("4700.00"),
			vat=Decimal("783.33"),
			voucher="00210358",
			mileage=Decimal("0"),
			unit_price=Decimal("1.00"),
			amount=Decimal("4700.00"),
		)
		TransactionOMV.objects.create(
			issuer="OMV",
			customer="IMS",
			card="123",
			license_plate_no="BG2024-OT",
			transaction_date=self._dt(2026, 4, 23, 8, 0),
			product_inv="AdBlue Kanister",
			quantity=Decimal("1.00"),
			gross_cc=Decimal("999.00"),
			vat=Decimal("166.50"),
			voucher="00210359",
			mileage=Decimal("0"),
			unit_price=Decimal("999.00"),
			amount=Decimal("999.00"),
		)

		filtered_ids = list(filter_omv_fuel_queryset(TransactionOMV.objects.all()).values_list("id", flat=True))

		self.assertEqual(filtered_ids, [fuel.id])

	def test_filter_nis_fuel_queryset_excludes_non_fuel_products(self):
		fuel = TransactionNIS.objects.create(
			kupac="IMS",
			sifra_kupca="107248",
			broj_kartice="123",
			kompanijski_kod_kupca="217",
			zemlja_sipanja="SR",
			benzinska_stanica="MARTINCI 2",
			id_transakcije="1",
			app_kod="APP",
			datum_transakcije=self._dt(2026, 4, 23, 18, 10),
			tociono_mesto="1",
			registarska_oznaka_vozila="BG2024-OT",
			broj_racuna="00211066",
			kilometraza=62423,
			sipanje_van_rezervoara=False,
			naziv_proizvoda="OMV EVRO DIZEL",
			kolicina=Decimal("46.27"),
			popust=Decimal("0.00"),
			primenjen_popust="",
			cena_sa_kase=Decimal("217.00"),
			cena=Decimal("217.00"),
			total_sa_kase=Decimal("10040.59"),
			total=Decimal("10040.59"),
			valuta="RSD",
			aktivirano_prekoracenje=False,
			kolicinsko_prekoracenje=False,
			finansijsko_prekoracenje=False,
			nacin_ocitavanja_kartice="manual",
		)
		TransactionNIS.objects.create(
			kupac="IMS",
			sifra_kupca="107248",
			broj_kartice="123",
			kompanijski_kod_kupca="217",
			zemlja_sipanja="SR",
			benzinska_stanica="MARTINCI 2",
			id_transakcije="2",
			app_kod="APP",
			datum_transakcije=self._dt(2026, 4, 21, 17, 45),
			tociono_mesto="1",
			registarska_oznaka_vozila="BG2024-OT",
			broj_racuna="00210358",
			kilometraza=0,
			sipanje_van_rezervoara=False,
			naziv_proizvoda="Putarina",
			kolicina=Decimal("4700.00"),
			popust=Decimal("0.00"),
			primenjen_popust="",
			cena_sa_kase=Decimal("1.00"),
			cena=Decimal("1.00"),
			total_sa_kase=Decimal("4700.00"),
			total=Decimal("4700.00"),
			valuta="RSD",
			aktivirano_prekoracenje=False,
			kolicinsko_prekoracenje=False,
			finansijsko_prekoracenje=False,
			nacin_ocitavanja_kartice="manual",
		)

		filtered_ids = list(filter_nis_fuel_queryset(TransactionNIS.objects.all()).values_list("id", flat=True))

		self.assertEqual(filtered_ids, [fuel.id])


class VehicleTravelOrderCreateViewTests(TestCase):
	def setUp(self):
		self.vehicle = Vehicle.objects.create(
			inventory_number="INV-1",
			chassis_number="WF0XXXTEST0000001",
			brand="Ford",
			model="Transit",
			year_of_manufacture=2020,
			first_registration_date=datetime.date(2020, 1, 1),
			color="Bela",
			number_of_axles=2,
			engine_volume=Decimal("1999.00"),
			engine_number="ENG-1",
			weight=Decimal("2500.00"),
			engine_power=Decimal("96.00"),
			load_capacity=Decimal("1200.00"),
			category="TERETNO VOZILO",
			maximum_permissible_weight=Decimal("3500.00"),
			fuel_type="DIZEL",
			number_of_seats=3,
			purchase_value=Decimal("10000.00"),
			value=Decimal("9000.00"),
		)
		self.employee = Employee.objects.create(
			employee_code=1,
			first_name="Pera",
			last_name="Peric",
			position="Vozac",
			department_code=10,
			gender="M",
			date_of_birth=datetime.date(1990, 1, 1),
			date_of_joining=datetime.date(2020, 1, 1),
			is_active=True,
		)

	def test_new_travel_order_closes_previous_and_copies_start_mileage(self):
		previous_order = VehicleTravelOrder.objects.create(
			created_at=datetime.date(2026, 4, 20),
			start_mileage=61500,
			employee=self.employee,
			vehicle=self.vehicle,
		)

		form = VehicleTravelOrderForm(
			data={
				"created_at": "24.04.2026",
				"employee": self.employee.pk,
				"vehicle": self.vehicle.pk,
				"start_mileage": 62423,
			}
		)
		self.assertTrue(form.is_valid(), form.errors)

		view = VehicleTravelOrderCreateView()
		response = view.form_valid(form)

		previous_order.refresh_from_db()
		new_order = view.object

		self.assertEqual(response.status_code, 302)
		self.assertEqual(previous_order.closed_at, new_order.created_at)
		self.assertEqual(previous_order.end_mileage, new_order.start_mileage)


class VehicleTravelOrderConsumptionTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.vehicle = Vehicle.objects.create(
			inventory_number="INV-2",
			chassis_number="WF0XXXTEST0000002",
			brand="Ford",
			model="Transit",
			year_of_manufacture=2020,
			first_registration_date=datetime.date(2020, 1, 1),
			color="Bela",
			number_of_axles=2,
			engine_volume=Decimal("1999.00"),
			engine_number="ENG-2",
			weight=Decimal("2500.00"),
			engine_power=Decimal("96.00"),
			load_capacity=Decimal("1200.00"),
			category="TERETNO VOZILO",
			maximum_permissible_weight=Decimal("3500.00"),
			fuel_type="DIZEL",
			number_of_seats=3,
			purchase_value=Decimal("10000.00"),
			value=Decimal("9000.00"),
		)
		self.employee = Employee.objects.create(
			employee_code=2,
			first_name="Mika",
			last_name="Mikic",
			position="Vozac",
			department_code=10,
			gender="M",
			date_of_birth=datetime.date(1991, 1, 1),
			date_of_joining=datetime.date(2020, 1, 1),
			is_active=True,
		)

	def test_consumption_is_total_liters_per_100_kilometers(self):
		order = VehicleTravelOrder.objects.create(
			created_at=datetime.date(2026, 4, 20),
			closed_at=datetime.date(2026, 4, 21),
			start_mileage=1000,
			end_mileage=1100,
			employee=self.employee,
			vehicle=self.vehicle,
		)
		TransactionOMV.objects.create(
			vehicle=self.vehicle,
			issuer="OMV",
			customer="IMS",
			card="123",
			license_plate_no="BG000-AA",
			transaction_date=timezone.make_aware(datetime.datetime(2026, 4, 20, 10, 0)),
			product_inv="OMV EVRO DIZEL",
			quantity=Decimal("20.00"),
			gross_cc=Decimal("4000.00"),
			vat=Decimal("666.67"),
			voucher="R1",
			mileage=Decimal("1050"),
			unit_price=Decimal("200.00"),
			amount=Decimal("4000.00"),
		)

		request = self.factory.get("/")
		view = VehicleTravelOrderDetailView()
		view.request = request
		view.object = order

		context = view.get_context_data()

		self.assertEqual(context["distance"], 100)
		self.assertEqual(context["total_liters"], Decimal("20"))
		self.assertEqual(context["consumption"], Decimal("20"))
