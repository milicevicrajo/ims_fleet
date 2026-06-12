from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from openpyxl import load_workbook

from fleet.models import JobCode, OrganizationalUnit, Vehicle
from .models import (
    EufItemSnapshot,
    ProcurementCase,
    ProcurementInvoice,
    ProcurementInvoiceJobCodeLink,
    ProcurementItem,
    UfInvoiceSnapshot,
)
from .services.source_snapshots import rebuild_uf_invoice_snapshots
from .views.reports import fetch_partner_job_code_rows


class PartnerJobCodeReportQueryTests(SimpleTestCase):
    @patch("nabavka.views.reports.connections")
    def test_fetch_partner_job_code_rows_filters_by_partner_name(self, connections):
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            (" 100 ", " Partner DOO ", " 01-001 "),
        ]
        connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = cursor

        rows = fetch_partner_job_code_rows(partner_name="Partner")

        sql, params = cursor.execute.call_args.args
        self.assertIn("dbo.nbv_sif_pos_par", sql)
        self.assertIn("naz_par", sql)
        self.assertEqual(params, ["%Partner%"])
        self.assertEqual(rows, [{"partner_code": "100", "partner_name": "Partner DOO", "job_code": "01-001"}])


@override_settings(ALLOWED_HOSTS=["testserver"])
class PartnerJobCodeReportViewTests(TestCase):
    @patch("nabavka.views.reports.fetch_partner_job_code_rows")
    def test_report_page_renders_rows(self, fetch_rows):
        fetch_rows.return_value = [
            {"partner_code": "100", "partner_name": "Partner DOO", "job_code": "01-001"},
        ]
        user = get_user_model().objects.create_user(
            username="nabavka-report",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("nabavka:partner_job_code_check_report"),
            {"partner": "Partner"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Provera sifre posla za partnera")
        self.assertContains(response, "Partner DOO")
        fetch_rows.assert_called_once_with(partner_name="Partner")


@override_settings(ALLOWED_HOSTS=["testserver"])
class ProcurementInvoiceJobCodeLinkTests(TestCase):
    @staticmethod
    def _create_vehicle(suffix="1"):
        return Vehicle.objects.create(
            inventory_number=f"INV-{suffix}",
            chassis_number=f"CHASSIS{suffix:0>10}"[:17],
            brand="Test",
            model="Auto",
            year_of_manufacture=2024,
            first_registration_date=date(2024, 1, 1),
            color="Bela",
            number_of_axles=2,
            engine_volume=Decimal("1600.00"),
            engine_number=f"ENG-{suffix}",
            weight=Decimal("1200.00"),
            engine_power=Decimal("80.00"),
            load_capacity=Decimal("400.00"),
            category="Putnicko",
            maximum_permissible_weight=Decimal("1600.00"),
            fuel_type="Dizel",
            number_of_seats=5,
            purchase_value=Decimal("10000.00"),
        )

    def test_invoice_can_be_linked_to_additional_job_code(self):
        primary_job_code = OrganizationalUnit.objects.create(
            code="100",
            name="Primarna sifra",
            center="10",
        )
        additional_job_code = OrganizationalUnit.objects.create(
            code="200",
            name="Dodatna sifra",
            center="20",
        )
        invoice = ProcurementInvoice.objects.create(
            source=ProcurementInvoice.SOURCE_EUF,
            euf_key="euf-1",
            invoice_number="IF-1",
            supplier_name="Partner DOO",
            job_code=primary_job_code,
        )
        user = get_user_model().objects.create_user(
            username="invoice-job-code",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(user)

        detail_url = reverse("nabavka:euf_invoice_detail", args=[invoice.pk])
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)
        detail_html = detail_response.content.decode()
        self.assertNotIn('id="id_job_code"', detail_html)
        self.assertIn('id="id_job_code_link-job_code"', detail_html)
        self.assertIn(f'value="{additional_job_code.pk}"', detail_html)

        response = self.client.post(
            detail_url,
            {
                "action": "link_job_code",
                "job_code_link-job_code": str(additional_job_code.pk),
                "job_code_link-note": "Podela troska",
            },
        )

        self.assertRedirects(response, reverse("nabavka:euf_invoice_detail", args=[invoice.pk]))
        link = ProcurementInvoiceJobCodeLink.objects.get(invoice=invoice, job_code=additional_job_code)
        self.assertEqual(link.note, "Podela troska")
        self.assertEqual(link.created_by, user)
        invoice.refresh_from_db()
        self.assertEqual(invoice.job_code, primary_job_code)

    def test_primary_job_code_is_vehicle_snapshot_only(self):
        first_job_code = OrganizationalUnit.objects.create(
            code="301",
            name="Prva sifra auta",
            center="31",
        )
        newer_job_code = OrganizationalUnit.objects.create(
            code="302",
            name="Nova sifra auta",
            center="32",
        )
        vehicle = self._create_vehicle()
        JobCode.objects.create(
            vehicle=vehicle,
            organizational_unit=first_job_code,
            assigned_date=date(2026, 1, 1),
        )
        invoice = ProcurementInvoice.objects.create(
            source=ProcurementInvoice.SOURCE_EUF,
            euf_key="euf-auto-snapshot",
            invoice_number="IF-AUTO",
            supplier_name="Partner DOO",
        )
        user = get_user_model().objects.create_user(
            username="invoice-auto-job-code",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(user)
        detail_url = reverse("nabavka:euf_invoice_detail", args=[invoice.pk])

        self.client.post(
            detail_url,
            {
                "action": "update_details",
                "is_garage": "on",
                "vehicle": str(vehicle.pk),
            },
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.job_code, first_job_code)
        self.assertEqual(invoice.job_code_source, ProcurementInvoice.JOB_CODE_SOURCE_VEHICLE_SNAPSHOT)
        self.assertEqual(invoice.vehicle_job_code_assigned_date, date(2026, 1, 1))

        JobCode.objects.create(
            vehicle=vehicle,
            organizational_unit=newer_job_code,
            assigned_date=date(2026, 6, 1),
        )
        self.client.post(
            detail_url,
            {
                "action": "update_details",
                "is_garage": "on",
                "vehicle": str(vehicle.pk),
                "internal_note": "Naknadna dopuna",
            },
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.job_code, first_job_code)
        self.assertEqual(invoice.internal_note, "Naknadna dopuna")


@override_settings(ALLOWED_HOSTS=["testserver"])
class EufInvoiceListControlsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="invoice-controls",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(self.user)
        self.invoice = ProcurementInvoice.objects.create(
            source=ProcurementInvoice.SOURCE_EUF,
            euf_key="euf-controls-1",
            invoice_number="IF-CTRL-1",
            supplier_name="Partner DOO",
            amount="1200.00",
        )

    def test_data_includes_returned_checkbox(self):
        response = self.client.get(reverse("nabavka:euf_invoice_data"))

        self.assertEqual(response.status_code, 200)
        row = response.json()["data"][0]
        self.assertIn("is_returned", row)
        self.assertIn("js-invoice-returned", row["is_returned"])

    def test_returned_toggle_updates_invoice(self):
        response = self.client.post(
            reverse("nabavka:euf_invoice_returned_toggle", args=[self.invoice.pk]),
            {"is_returned": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_returned"])
        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.is_returned)

    def test_export_returns_filtered_excel(self):
        response = self.client.get(
            reverse("nabavka:euf_invoice_export"),
            {"invoice_search": "IF-CTRL"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        workbook = load_workbook(BytesIO(response.content))
        worksheet = workbook.active
        headers = [cell.value for cell in worksheet[1]]
        self.assertIn("Vraceno", headers)
        self.assertEqual(worksheet["C2"].value, "IF-CTRL-1")


@override_settings(ALLOWED_HOSTS=["testserver"])
class UfInvoiceSnapshotTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="uf-invoices",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(self.user)

    def test_rebuild_groups_uf_items_by_invoice(self):
        first_item = EufItemSnapshot.objects.create(
            source_key="uf-item-1",
            invoice_number="UF-1",
            partner_name="Partner DOO",
            partner_pib="123",
            document_date=date(2026, 6, 10),
            payment_amount=Decimal("150.00"),
            value=Decimal("50.00"),
            account="5120",
            item_name="Prva stavka",
        )
        second_item = EufItemSnapshot.objects.create(
            source_key="uf-item-2",
            invoice_number="UF-1",
            partner_name="Partner DOO",
            partner_pib="123",
            document_date=date(2026, 6, 10),
            payment_amount=Decimal("150.00"),
            value=Decimal("100.00"),
            account="5120",
            item_name="Druga stavka",
        )

        rebuild_uf_invoice_snapshots()

        invoice = UfInvoiceSnapshot.objects.get(invoice_number="UF-1")
        self.assertEqual(invoice.item_count, 2)
        self.assertEqual(invoice.item_value_total, Decimal("150.00"))
        first_item.refresh_from_db()
        second_item.refresh_from_db()
        self.assertEqual(first_item.uf_invoice, invoice)
        self.assertEqual(second_item.uf_invoice, invoice)

    def test_source_search_and_link_use_uf_invoice(self):
        uf_invoice = UfInvoiceSnapshot.objects.create(
            source_key="uf-invoice-1",
            invoice_number="UF-2",
            partner_name="Partner DOO",
            partner_pib="123",
            payment_amount=Decimal("200.00"),
            item_count=3,
        )
        org_unit = OrganizationalUnit.objects.create(code="300", name="OJ", center="30")
        procurement_case = ProcurementCase.objects.create(
            title="Zahtev",
            job_code=org_unit,
            created_by=self.user,
        )
        procurement_item = ProcurementItem.objects.create(
            procurement_case=procurement_case,
            name="Materijal",
            uom="kom",
            quantity=Decimal("1"),
            estimated_unit_price=Decimal("200.00"),
        )

        search_response = self.client.get(
            reverse("nabavka:item_source_data"),
            {"source_type": ProcurementItem.SOURCE_UF, "q": "UF-2"},
        )
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.json()["results"][0]["id"], uf_invoice.pk)

        response = self.client.post(
            reverse("nabavka:item_source_link", args=[procurement_case.pk, procurement_item.pk]),
            {
                "source_type": ProcurementItem.SOURCE_UF,
                "source_reference": str(uf_invoice.pk),
            },
        )

        self.assertRedirects(response, reverse("nabavka:case_detail", args=[procurement_case.pk]))
        procurement_item.refresh_from_db()
        self.assertEqual(procurement_item.uf_invoice, uf_invoice)
        self.assertIsNone(procurement_item.uf_item)

    def test_uf_invoice_list_links_to_detail_and_detail_renders_items(self):
        uf_invoice = UfInvoiceSnapshot.objects.create(
            source_key="uf-invoice-detail",
            invoice_number="UF-DETAIL",
            partner_name="Partner Detail",
            item_count=1,
            item_value_total=Decimal("50.00"),
        )
        EufItemSnapshot.objects.create(
            source_key="uf-detail-item",
            uf_invoice=uf_invoice,
            invoice_number="UF-DETAIL",
            partner_name="Partner Detail",
            item_name="Detaljna stavka",
            value=Decimal("50.00"),
        )

        data_response = self.client.get(reverse("nabavka:euf_item_data"))
        self.assertEqual(data_response.status_code, 200)
        self.assertIn(reverse("nabavka:uf_invoice_detail", args=[uf_invoice.pk]), data_response.json()["data"][0]["actions"])

        detail_response = self.client.get(reverse("nabavka:uf_invoice_detail", args=[uf_invoice.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "UF-DETAIL")
        self.assertContains(detail_response, "Detaljna stavka")
