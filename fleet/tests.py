import csv
import datetime
import os
import tempfile
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import VehicleTravelOrderCloseForm, VehicleTravelOrderForm
from .forms.reports import OMVPutnickaFilterForm, PutnickaFilterForm
from hr.models import Employee
from .models import FuelConsumption, TrafficCard, TransactionNIS, TransactionOMV
from .models import Vehicle, VehicleTravelOrder
from .support.dashboard import vehicle_cost_per_km_rows
from .support.report_helpers import date_period_filtered_query, report_period_filtered_query
from .report_exports import NIS_TERETNA_EXPORT, OMV_PUTNICKA_EXPORT, report_export_rows
from .views.reports import _export_secondary_report, _render_secondary_report, _render_simple_secondary_report
from .support.fuel import filter_nis_fuel_queryset, filter_omv_fuel_queryset, format_omv_receipt_number
from .templatetags.form_filters import receipt_number
from .views.vehicle_travel_orders import (
	VehicleTravelOrderCreateView,
	VehicleTravelOrderDeleteView,
	VehicleTravelOrderDetailView,
	VehicleTravelOrderUpdateView,
)
from .sync.selenium import import_omv_transactions_from_csv


class SecondaryReportViewHelperTests(SimpleTestCase):
	def setUp(self):
		self.factory = RequestFactory()

	@patch("fleet.views.reports.render")
	@patch("fleet.views.reports.get_data_from_secondary_db")
	def test_render_secondary_report_renders_template_with_context(self, get_data_mock, render_mock):
		request = self.factory.get("/fleet/report/")
		form = PutnickaFilterForm()
		get_data_mock.return_value = [{"sifpos": "832111"}]
		render_mock.return_value = "rendered"

		response = _render_secondary_report(
			request,
			form=form,
			query="SELECT * FROM x WHERE 1=1",
			filter_query=report_period_filtered_query,
			template_name="fleet/reports/omv_putnicka.html",
			title="Test report",
			export_filename="test.xlsx",
			export_sheet="Test",
		)

		self.assertEqual(response, "rendered")
		render_mock.assert_called_once()
		get_data_mock.assert_called_once()

	@patch("fleet.views.reports.report_xlsx_response")
	@patch("fleet.views.reports.get_data_from_secondary_db")
	def test_export_secondary_report_returns_xlsx_response(self, get_data_mock, export_mock):
		form = PutnickaFilterForm({"godina": "2026"})
		get_data_mock.return_value = [{"sifpos": "832111"}]
		export_mock.return_value = "xlsx"

		response = _export_secondary_report(
			form=form,
			query="SELECT * FROM x WHERE 1=1",
			filter_query=report_period_filtered_query,
			export_spec=OMV_PUTNICKA_EXPORT,
		)

		self.assertEqual(response, "xlsx")
		export_mock.assert_called_once()
		get_data_mock.assert_called_once()

	@patch("fleet.views.reports.render")
	@patch("fleet.views.reports.get_data_from_secondary_db")
	def test_render_simple_secondary_report_uses_given_db_alias_and_template(self, get_data_mock, render_mock):
		request = self.factory.get("/fleet/simple-report/")
		get_data_mock.return_value = [{"id": 1}]
		render_mock.return_value = "simple-rendered"

		response = _render_simple_secondary_report(
			request,
			query="SELECT * FROM y",
			db_alias="server_db",
			template_name="fleet/reports/otpis.html",
		)

		self.assertEqual(response, "simple-rendered")
		get_data_mock.assert_called_once_with("SELECT * FROM y", "server_db")
		render_mock.assert_called_once()


class ReportExportRowsTests(SimpleTestCase):
	def test_report_export_rows_uses_spec_field_order(self):
		data = [
			{
				"sifpos": "832111",
				"godina": 2026,
				"mesec": 4,
				"tipvozila": "PUTNICKO",
				"polovina": 2,
				"bruto": Decimal("1200.00"),
				"neto": Decimal("1000.00"),
			}
		]

		rows = list(report_export_rows(data, OMV_PUTNICKA_EXPORT))

		self.assertEqual(
			rows,
			[["832111", 2026, 4, "PUTNICKO", 2, Decimal("1200.00"), Decimal("1000.00")]],
		)

	def test_report_export_rows_uses_nis_teretna_summary_fields(self):
		data = [
			{
				"tipvozila": "TERETNO",
				"sifpos": "832111",
				"godina": 2026,
				"mesec": 4,
				"polovina": 2,
				"bruto": Decimal("8400.00"),
				"neto": Decimal("7000.00"),
			}
		]

		rows = list(report_export_rows(data, NIS_TERETNA_EXPORT))

		self.assertEqual(
			rows,
			[[
				"TERETNO",
				"832111",
				2026,
				4,
				2,
				Decimal("8400.00"),
				Decimal("7000.00"),
			]],
		)


class VehicleCostPerKmMileageTests(TestCase):
	def create_vehicle(self, inventory_number="A-1", chassis_number="CHASSIS000000001", engine_number="ENGINE-1"):
		return Vehicle.objects.create(
			inventory_number=inventory_number,
			chassis_number=chassis_number,
			brand="Test",
			model="Vozilo",
			year_of_manufacture=2020,
			first_registration_date=datetime.date(2020, 1, 1),
			color="Bela",
			number_of_axles=2,
			engine_volume=Decimal("1600.00"),
			engine_number=engine_number,
			weight=Decimal("1200.00"),
			engine_power=Decimal("80.00"),
			load_capacity=Decimal("500.00"),
			category=Vehicle.Category.PASSENGER,
			maximum_permissible_weight=Decimal("1800.00"),
			fuel_type="Dizel",
			number_of_seats=5,
			purchase_value=Decimal("1000000.00"),
			value=Decimal("800000.00"),
			service_interval=15000,
			purchase_date=datetime.date(2020, 1, 1),
		)

	def create_fuel(self, vehicle, when, mileage, cost=Decimal("1000.00")):
		return FuelConsumption.objects.create(
			vehicle=vehicle,
			date=timezone.make_aware(datetime.datetime.combine(when, datetime.time(12, 0))),
			amount=Decimal("10.00"),
			fuel_type="Dizel",
			cost_bruto=cost,
			cost_neto=cost,
			supplier="NIS",
			mileage=mileage,
		)

	def test_cost_per_km_ignores_zero_fuel_mileage_and_estimates_period_km(self):
		vehicle = self.create_vehicle()
		self.create_fuel(vehicle, datetime.date(2026, 1, 1), 10000)
		self.create_fuel(vehicle, datetime.date(2026, 6, 1), 0)
		self.create_fuel(vehicle, datetime.date(2027, 1, 1), 20000)

		rows = vehicle_cost_per_km_rows(
			datetime.date(2026, 1, 1),
			datetime.date(2027, 1, 1),
			vehicle_ids=[vehicle.id],
		)

		self.assertEqual(len(rows), 1)
		self.assertAlmostEqual(rows[0]["annual_km"], 10000)
		self.assertEqual(rows[0]["mileage_source"], "Točenja (okvirno)")
		self.assertIn("0 su ignorisana", rows[0]["mileage_issue"])

	def test_cost_per_km_uses_vehicle_travel_order_mileage_when_fuel_mileage_is_invalid(self):
		vehicle = self.create_vehicle("A-2", "CHASSIS000000002", "ENGINE-2")
		employee = Employee.objects.create(
			employee_code=9901,
			first_name="Test",
			last_name="Vozac",
			position="Vozac",
			department_code=1,
			gender="M",
			date_of_birth=datetime.date(1990, 1, 1),
			date_of_joining=datetime.date(2020, 1, 1),
		)
		self.create_fuel(vehicle, datetime.date(2026, 6, 1), 0)
		VehicleTravelOrder.objects.create(
			vehicle=vehicle,
			employee=employee,
			created_at=datetime.date(2026, 1, 1),
			closed_at=datetime.date(2027, 1, 1),
			start_mileage=1000,
			end_mileage=4650,
		)

		rows = vehicle_cost_per_km_rows(
			datetime.date(2026, 1, 1),
			datetime.date(2027, 1, 1),
			vehicle_ids=[vehicle.id],
		)

		self.assertEqual(len(rows), 1)
		self.assertAlmostEqual(rows[0]["annual_km"], 3650)
		self.assertEqual(rows[0]["mileage_source"], "Zaduženja (okvirno)")


class ReportPeriodFilterHelperTests(SimpleTestCase):
	base_query = "SELECT * FROM report WHERE 1=1"

	def test_report_period_filter_appends_column_conditions_with_string_params(self):
		form = PutnickaFilterForm({"godina": "2026", "mesec": "4", "polovina": "2"})

		query, params = report_period_filtered_query(self.base_query, form)

		self.assertEqual(
			query,
			self.base_query + " AND godina = %s AND mesec = %s AND polovina = %s",
		)
		self.assertEqual(params, ["2026", "4", "2"])

	def test_report_period_filter_casts_export_params_to_int(self):
		form = PutnickaFilterForm({"godina": "2026", "mesec": "4", "polovina": "2"})

		query, params = report_period_filtered_query(self.base_query, form, cast_params=True)

		self.assertEqual(
			query,
			self.base_query + " AND godina = %s AND mesec = %s AND polovina = %s",
		)
		self.assertEqual(params, [2026, 4, 2])

	def test_date_period_filter_applies_view_polovina_condition(self):
		form = PutnickaFilterForm({"godina": "2026", "mesec": "4", "polovina": "2"})

		query, params = date_period_filtered_query(self.base_query, form)

		self.assertEqual(
			query,
			self.base_query + " AND YEAR(datum) = %s AND MONTH(datum) = %s AND DAY(datum) > 15",
		)
		self.assertEqual(params, ["2026", "4"])

	def test_omv_and_putnicka_period_forms_share_fields(self):
		omv_form = OMVPutnickaFilterForm()
		putnicka_form = PutnickaFilterForm()

		self.assertEqual(list(omv_form.fields), list(putnicka_form.fields))
		self.assertEqual(
			list(omv_form.fields["polovina"].choices),
			list(putnicka_form.fields["polovina"].choices),
		)

	def test_date_period_filter_casts_export_polovina_to_day_condition(self):
		form = PutnickaFilterForm({"godina": "2026", "mesec": "4", "polovina": "2"})

		query, params = date_period_filtered_query(self.base_query, form, cast_params=True)

		self.assertEqual(
			query,
			self.base_query + " AND YEAR(datum) = %s AND MONTH(datum) = %s AND DAY(datum) > 15",
		)
		self.assertEqual(params, [2026, 4])


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

	def test_format_omv_receipt_number_combines_invoice_and_voucher(self):
		self.assertEqual(format_omv_receipt_number("8916372386", "00168851"), "8916372386 / 00168851")
		self.assertEqual(format_omv_receipt_number("8916372386", ""), "8916372386")
		self.assertEqual(format_omv_receipt_number("", "00168851"), "00168851")

	def test_receipt_number_keeps_omv_leading_zeroes(self):
		self.assertEqual(receipt_number("00282457"), "00282457")
		self.assertEqual(receipt_number("7562133.0"), "7562133")


class OMVTransactionImportTests(TestCase):
	@staticmethod
	def _dt(year, month, day, hour, minute):
		return timezone.make_aware(datetime.datetime(year, month, day, hour, minute))

	def setUp(self):
		self.vehicle = Vehicle.objects.create(
			inventory_number="INV-OMV-1",
			chassis_number="WF0XXXOMV0000001",
			brand="Ford",
			model="Focus",
			year_of_manufacture=2021,
			first_registration_date=datetime.date(2021, 1, 1),
			color="Bela",
			number_of_axles=2,
			engine_volume=Decimal("1599.00"),
			engine_number="ENG-OMV-1",
			weight=Decimal("1400.00"),
			engine_power=Decimal("88.00"),
			load_capacity=Decimal("500.00"),
			category=Vehicle.Category.PASSENGER,
			maximum_permissible_weight=Decimal("1900.00"),
			fuel_type="DIZEL",
			number_of_seats=5,
			purchase_value=Decimal("10000.00"),
			value=Decimal("9000.00"),
		)
		TrafficCard.objects.create(
			vehicle=self.vehicle,
			registration_number="BG1007-KX",
			issue_date=datetime.date(2021, 1, 1),
			valid_until=datetime.date(2031, 1, 1),
			traffic_card_number="TC-1",
			serial_number="SER-1",
			owner="IMS",
			homologation_number="HOM-1",
		)

	def test_import_updates_existing_omv_transaction_when_invoice_arrives(self):
		headers = [
			"Issuer", "Customer", "Card", "License plate No", "Transactiondate", "Product INV",
			"Quantity", "Gross CC", "VAT", "Voucher", "Mileage", "Corrected mileage",
			"Additional info", "Supply country", "Site Town", "Product DEL", "Unitprice",
			"Amount", "Discount", "Surcharge", "VAT2010", "Suppliercurrency", "Invoice No",
			"Invoice date", "Invoiced?", "State", "Supplier", "Cost 1", "Cost 2",
			"Reference No", "Recordtype", "Amount other", "is listprice ?", "Approval code",
			"Date to", "Final Trx.", "LPI",
		]
		base_row = {
			"Issuer": "710111",
			"Customer": "107248",
			"Card": "123",
			"License plate No": "BG 1007 - KX",
			"Transactiondate": "2026-02-28 12:37:00",
			"Product INV": "OMV EVRO DIZEL",
			"Quantity": "43.02",
			"Gross CC": "8604.00",
			"VAT": "1434.00",
			"Voucher": "00289548",
			"Mileage": "222866",
			"Corrected mileage": "222866",
			"Additional info": "",
			"Supply country": "SR",
			"Site Town": "BEOGRAD",
			"Product DEL": "OMV EVRO DIZEL",
			"Unitprice": "200.00",
			"Amount": "8604.00",
			"Discount": "0.00",
			"Surcharge": "0.00",
			"VAT2010": "NO",
			"Suppliercurrency": "RSD",
			"Invoice No": "",
			"Invoice date": "",
			"Invoiced?": "NO",
			"State": "217",
			"Supplier": "OMV-RS",
			"Cost 1": "",
			"Cost 2": "",
			"Reference No": "",
			"Recordtype": "D",
			"Amount other": "0.00",
			"is listprice ?": "No",
			"Approval code": "700001",
			"Date to": "2026-02-28",
			"Final Trx.": "1",
			"LPI": "",
		}
		final_row = {
			**base_row,
			"Gross CC": "8302.86",
			"VAT": "1383.81",
			"Unitprice": "193.00",
			"Amount": "8302.86",
			"Amount other": "8604.00",
			"is listprice ?": "Yes",
			"Invoice No": "8916357590",
			"Invoice date": "2026-02-28",
			"Invoiced?": "YES",
		}

		with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8-sig", suffix=".csv", delete=False) as handle:
			writer = csv.DictWriter(handle, fieldnames=headers, delimiter=";")
			writer.writeheader()
			writer.writerow(base_row)
			writer.writerow(final_row)
			csv_path = handle.name

		try:
			result = import_omv_transactions_from_csv(csv_path)
		finally:
			os.unlink(csv_path)

		self.assertEqual(result["created"], 1)
		self.assertEqual(result["updated"], 1)
		self.assertEqual(TransactionOMV.objects.count(), 1)
		transaction = TransactionOMV.objects.get()
		self.assertEqual(transaction.invoice_no, "8916357590")
		self.assertEqual(transaction.gross_cc, Decimal("8302.86"))
		self.assertEqual(transaction.quantity, Decimal("43.02"))
		self.assertEqual(transaction.amount, Decimal("8604.00"))
		self.assertEqual(transaction.unit_price, Decimal("200.00"))

	def test_import_does_not_overwrite_final_list_price_transaction_with_regular_row(self):
		TransactionOMV.objects.create(
			vehicle=self.vehicle,
			issuer="710111",
			customer="107248",
			card="123",
			license_plate_no="BG1007-KX",
			transaction_date=self._dt(2026, 2, 28, 12, 37),
			product_inv="OMV EVRO DIZEL",
			quantity=Decimal("43.02"),
			gross_cc=Decimal("8302.86"),
			vat=Decimal("1383.81"),
			voucher="00289548",
			mileage=Decimal("222866"),
			unit_price=Decimal("200.00"),
			amount=Decimal("8604.00"),
			amount_other=Decimal("8604.00"),
			is_list_price=Decimal("1"),
			invoice_no="8916357590",
			invoiced=True,
		)
		headers = [
			"Issuer", "Customer", "Card", "License plate No", "Transactiondate", "Product INV",
			"Quantity", "Gross CC", "VAT", "Voucher", "Mileage", "Corrected mileage",
			"Additional info", "Supply country", "Site Town", "Product DEL", "Unitprice",
			"Amount", "Discount", "Surcharge", "VAT2010", "Suppliercurrency", "Invoice No",
			"Invoice date", "Invoiced?", "State", "Supplier", "Cost 1", "Cost 2",
			"Reference No", "Recordtype", "Amount other", "is listprice ?", "Approval code",
			"Date to", "Final Trx.", "LPI",
		]
		row = {
			"Issuer": "710111",
			"Customer": "107248",
			"Card": "123",
			"License plate No": "BG 1007 - KX",
			"Transactiondate": "2026-02-28 12:37:00",
			"Product INV": "OMV EVRO DIZEL",
			"Quantity": "43.02",
			"Gross CC": "8604.00",
			"VAT": "1434.00",
			"Voucher": "00289548",
			"Mileage": "222866",
			"Corrected mileage": "222866",
			"Additional info": "",
			"Supply country": "SR",
			"Site Town": "BEOGRAD",
			"Product DEL": "OMV EVRO DIZEL",
			"Unitprice": "200.00",
			"Amount": "8604.00",
			"Discount": "0.00",
			"Surcharge": "0.00",
			"VAT2010": "NO",
			"Suppliercurrency": "RSD",
			"Invoice No": "",
			"Invoice date": "",
			"Invoiced?": "NO",
			"State": "217",
			"Supplier": "OMV-RS",
			"Cost 1": "",
			"Cost 2": "",
			"Reference No": "",
			"Recordtype": "D",
			"Amount other": "0.00",
			"is listprice ?": "No",
			"Approval code": "700001",
			"Date to": "2026-02-28",
			"Final Trx.": "1",
			"LPI": "",
		}

		with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8-sig", suffix=".csv", delete=False) as handle:
			writer = csv.DictWriter(handle, fieldnames=headers, delimiter=";")
			writer.writeheader()
			writer.writerow(row)
			csv_path = handle.name

		try:
			result = import_omv_transactions_from_csv(csv_path)
		finally:
			os.unlink(csv_path)

		transaction = TransactionOMV.objects.get()
		self.assertEqual(result["preserved_final"], 1)
		self.assertEqual(result["updated"], 0)
		self.assertEqual(transaction.invoice_no, "8916357590")
		self.assertEqual(transaction.invoiced, True)
		self.assertEqual(transaction.amount, Decimal("8604.00"))
		self.assertEqual(transaction.amount_other, Decimal("8604.00"))
		self.assertEqual(transaction.unit_price, Decimal("200.00"))

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
			category=Vehicle.Category.CARGO,
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

	def test_new_travel_order_does_not_close_later_open_order(self):
		later_open_order = VehicleTravelOrder.objects.create(
			created_at=datetime.date(2026, 4, 25),
			start_mileage=70000,
			employee=self.employee,
			vehicle=self.vehicle,
		)

		form = VehicleTravelOrderForm(
			data={
				"created_at": "24.04.2026",
				"employee": self.employee.pk,
				"vehicle": self.vehicle.pk,
				"start_mileage": 70100,
			}
		)
		self.assertTrue(form.is_valid(), form.errors)

		view = VehicleTravelOrderCreateView()
		response = view.form_valid(form)

		later_open_order.refresh_from_db()

		self.assertEqual(response.status_code, 302)
		self.assertIsNone(later_open_order.closed_at)
		self.assertIsNone(later_open_order.end_mileage)


class VehicleTravelOrderCloseFormTests(TestCase):
	def setUp(self):
		self.vehicle = Vehicle.objects.create(
			inventory_number="INV-3",
			chassis_number="WF0XXXTEST0000003",
			brand="Ford",
			model="Transit",
			year_of_manufacture=2020,
			first_registration_date=datetime.date(2020, 1, 1),
			color="Bela",
			number_of_axles=2,
			engine_volume=Decimal("1999.00"),
			engine_number="ENG-3",
			weight=Decimal("2500.00"),
			engine_power=Decimal("96.00"),
			load_capacity=Decimal("1200.00"),
			category=Vehicle.Category.CARGO,
			maximum_permissible_weight=Decimal("3500.00"),
			fuel_type="DIZEL",
			number_of_seats=3,
			purchase_value=Decimal("10000.00"),
			value=Decimal("9000.00"),
		)
		self.employee = Employee.objects.create(
			employee_code=3,
			first_name="Zika",
			last_name="Zikic",
			position="Vozac",
			department_code=10,
			gender="M",
			date_of_birth=datetime.date(1992, 1, 1),
			date_of_joining=datetime.date(2020, 1, 1),
			is_active=True,
		)
		self.order = VehicleTravelOrder.objects.create(
			created_at=datetime.date(2026, 4, 24),
			employee=self.employee,
			vehicle=self.vehicle,
		)

	def test_close_form_rejects_date_before_open_date(self):
		form = VehicleTravelOrderCloseForm(
			instance=self.order,
			data={
				"closed_at": "23.04.2026",
				"end_mileage": 70500,
			},
		)

		self.assertFalse(form.is_valid())
		self.assertIn("closed_at", form.errors)


class VehicleTravelOrderUpdateViewTests(TestCase):
	def test_get_success_url_redirects_to_order_detail(self):
		vehicle = Vehicle.objects.create(
			inventory_number="INV-4",
			chassis_number="WF0XXXTEST0000004",
			brand="Ford",
			model="Transit",
			year_of_manufacture=2020,
			first_registration_date=datetime.date(2020, 1, 1),
			color="Bela",
			number_of_axles=2,
			engine_volume=Decimal("1999.00"),
			engine_number="ENG-4",
			weight=Decimal("2500.00"),
			engine_power=Decimal("96.00"),
			load_capacity=Decimal("1200.00"),
			category=Vehicle.Category.CARGO,
			maximum_permissible_weight=Decimal("3500.00"),
			fuel_type="DIZEL",
			number_of_seats=3,
			purchase_value=Decimal("10000.00"),
			value=Decimal("9000.00"),
		)
		employee = Employee.objects.create(
			employee_code=4,
			first_name="Laza",
			last_name="Lazic",
			position="Vozac",
			department_code=10,
			gender="M",
			date_of_birth=datetime.date(1993, 1, 1),
			date_of_joining=datetime.date(2020, 1, 1),
			is_active=True,
		)
		order = VehicleTravelOrder.objects.create(
			created_at=datetime.date(2026, 4, 24),
			employee=employee,
			vehicle=vehicle,
		)

		request = RequestFactory().post("/")
		view = VehicleTravelOrderUpdateView()
		view.request = request
		view.object = order

		self.assertEqual(view.get_success_url(), reverse("vehicle_travel_order_detail", args=[order.pk]))

	def test_closed_order_update_is_allowed_only_for_superuser(self):
		vehicle = Vehicle.objects.create(
			inventory_number="INV-40",
			chassis_number="WF0XXXTEST0000040",
			brand="Ford",
			model="Transit",
			year_of_manufacture=2020,
			first_registration_date=datetime.date(2020, 1, 1),
			color="Bela",
			number_of_axles=2,
			engine_volume=Decimal("1999.00"),
			engine_number="ENG-40",
			weight=Decimal("2500.00"),
			engine_power=Decimal("96.00"),
			load_capacity=Decimal("1200.00"),
			category=Vehicle.Category.CARGO,
			maximum_permissible_weight=Decimal("3500.00"),
			fuel_type="DIZEL",
			number_of_seats=3,
			purchase_value=Decimal("10000.00"),
			value=Decimal("9000.00"),
		)
		employee = Employee.objects.create(
			employee_code=40,
			first_name="Marko",
			last_name="Markovic",
			position="Vozac",
			department_code=10,
			gender="M",
			date_of_birth=datetime.date(1993, 1, 1),
			date_of_joining=datetime.date(2020, 1, 1),
			is_active=True,
		)
		order = VehicleTravelOrder.objects.create(
			created_at=datetime.date(2026, 4, 24),
			closed_at=datetime.date(2026, 4, 25),
			employee=employee,
			vehicle=vehicle,
		)
		user = get_user_model().objects.create_user(username="regular", password="x")
		request = RequestFactory().get("/")
		request.user = user

		view = VehicleTravelOrderUpdateView()

		with self.assertRaises(PermissionDenied):
			view.dispatch(request, pk=order.pk)


class VehicleTravelOrderDeleteViewTests(TestCase):
	def test_closed_order_delete_is_allowed_only_for_superuser(self):
		vehicle = Vehicle.objects.create(
			inventory_number="INV-41",
			chassis_number="WF0XXXTEST0000041",
			brand="Ford",
			model="Transit",
			year_of_manufacture=2020,
			first_registration_date=datetime.date(2020, 1, 1),
			color="Bela",
			number_of_axles=2,
			engine_volume=Decimal("1999.00"),
			engine_number="ENG-41",
			weight=Decimal("2500.00"),
			engine_power=Decimal("96.00"),
			load_capacity=Decimal("1200.00"),
			category=Vehicle.Category.CARGO,
			maximum_permissible_weight=Decimal("3500.00"),
			fuel_type="DIZEL",
			number_of_seats=3,
			purchase_value=Decimal("10000.00"),
			value=Decimal("9000.00"),
		)
		employee = Employee.objects.create(
			employee_code=41,
			first_name="Jovan",
			last_name="Jovanovic",
			position="Vozac",
			department_code=10,
			gender="M",
			date_of_birth=datetime.date(1993, 1, 1),
			date_of_joining=datetime.date(2020, 1, 1),
			is_active=True,
		)
		order = VehicleTravelOrder.objects.create(
			created_at=datetime.date(2026, 4, 24),
			closed_at=datetime.date(2026, 4, 25),
			employee=employee,
			vehicle=vehicle,
		)
		user = get_user_model().objects.create_user(username="regular-delete", password="x")
		request = RequestFactory().get("/")
		request.user = user

		view = VehicleTravelOrderDeleteView()

		with self.assertRaises(PermissionDenied):
			view.dispatch(request, pk=order.pk)


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
			category=Vehicle.Category.CARGO,
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

	def test_consumption_uses_fuel_transactions_inside_period(self):
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
			invoice_no="8916372386",
			voucher="R1",
			mileage=Decimal("1050"),
			unit_price=Decimal("200.00"),
			amount=Decimal("4000.00"),
		)
		TransactionOMV.objects.create(
			vehicle=self.vehicle,
			issuer="OMV",
			customer="IMS",
			card="123",
			license_plate_no="BG000-AA",
			transaction_date=timezone.make_aware(datetime.datetime(2026, 4, 19, 10, 0)),
			product_inv="OMV EVRO DIZEL",
			quantity=Decimal("10.00"),
			gross_cc=Decimal("2000.00"),
			vat=Decimal("333.33"),
			voucher="R0",
			mileage=Decimal("990"),
			unit_price=Decimal("200.00"),
			amount=Decimal("2000.00"),
		)
		TransactionOMV.objects.create(
			vehicle=self.vehicle,
			issuer="OMV",
			customer="IMS",
			card="123",
			license_plate_no="BG000-AA",
			transaction_date=timezone.make_aware(datetime.datetime(2026, 4, 21, 10, 0)),
			product_inv="OMV EVRO DIZEL",
			quantity=Decimal("30.00"),
			gross_cc=Decimal("6000.00"),
			vat=Decimal("1000.00"),
			voucher="R2",
			mileage=Decimal("1100"),
			unit_price=Decimal("200.00"),
			amount=Decimal("6000.00"),
		)

		request = self.factory.get("/")
		view = VehicleTravelOrderDetailView()
		view.request = request
		view.object = order

		context = view.get_context_data()

		self.assertEqual(context["distance"], 100)
		self.assertEqual(context["total_liters"], Decimal("50"))
		self.assertEqual(context["consumption"], Decimal("50"))
		self.assertEqual([row["invoice"] for row in context["fuel_rows"]], ["8916372386 / R1", "R2"])
