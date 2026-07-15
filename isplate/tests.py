import datetime
import json
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import OrganizationalUnit, PermissionCode, Role
from fleet.models import PutniNalog
from hr.models import Employee

from .services.converters import convert_virman_txt_to_internal_json
from .services.virman import RECORD_LENGTH, build_detail_line, build_virman_file, validate_order_for_virman


def create_employee(code=9001, account_number="160-5100103391558-82"):
    return Employee.objects.create(
        employee_code=code,
        original_full_name="CAVRAK JELENA",
        first_name="Jelena",
        last_name="Cavrak",
        position="Inzenjer",
        department_code=1,
        gender="F",
        date_of_birth=datetime.date(1990, 1, 1),
        date_of_joining=datetime.date(2020, 1, 1),
        account_number=account_number,
        residence_municipality="Vracar",
    )


def create_order(employee=None, order_number="01/2026-1", amount=Decimal("63139.86"), center="01"):
    job_code = OrganizationalUnit.objects.create(
        code=f"JC{center}{order_number.split('-')[-1]}",
        name="Test centar",
        center=center,
    )
    return PutniNalog.objects.create(
        order_number=order_number,
        order_date=datetime.date(2026, 5, 20),
        employee=employee or create_employee(),
        job_code=job_code,
        travel_location="Beograd",
        task="Sluzbeni put",
        travel_date=datetime.date(2026, 5, 20),
        number_of_days=1,
        advance_payment=amount,
        advance_payment_currency="RSD",
        daily_allowance=Decimal("2600.00"),
    )


class VirmanServiceTests(TestCase):
    def test_builds_fixed_width_lines(self):
        order = create_order()
        payment_date = datetime.date(2026, 5, 20)
        generated_at = timezone.datetime(2026, 5, 20, 10, 30, tzinfo=datetime.UTC)

        virman_file = build_virman_file([order], payment_date, generated_at)
        lines = virman_file.content.splitlines()

        self.assertEqual(len(lines), 3)
        self.assertTrue(all(len(line) == RECORD_LENGTH for line in lines))
        self.assertEqual(lines[2][:18], "160510010339155882")
        self.assertIn("CAVRAK JELENA", lines[2])
        self.assertEqual(lines[2][53:63].strip(), "VRACAR")
        self.assertEqual(lines[1][63:78], "000000006313986")
        self.assertEqual(lines[1][78:83], "00001")
        self.assertEqual(lines[2][88:123].strip(), "NEOPOREZIVA PRIMANJA ZAPOSLENIH")
        self.assertEqual(lines[2][130:133], "241")
        self.assertEqual(lines[2][135:148], "0000006313986")
        self.assertEqual(lines[2][148:169], "1".rjust(21))

    def test_detail_line_uses_only_travel_order_sequence_as_reference(self):
        order = create_order(order_number="43/2026-1316")

        line = build_detail_line(order, datetime.date(2026, 5, 20))

        self.assertEqual(line[148:169], "1316".rjust(21))

    def test_rejects_employee_without_account(self):
        order = create_order(employee=create_employee(account_number=""))

        with self.assertRaises(ValidationError):
            validate_order_for_virman(order)

    def test_detail_line_rejects_non_rsd(self):
        order = create_order()
        order.advance_payment_currency = "EUR"

        with self.assertRaises(ValidationError):
            build_detail_line(order, datetime.date(2026, 5, 20))

    def test_detail_line_uses_employee_residence_municipality_instead_of_travel_location(self):
        employee = create_employee(code=9010, account_number="160-5100103391558-82")
        order = create_order(employee=employee, order_number="01/2026-10")
        order.travel_location = "Nis"

        line = build_detail_line(order, datetime.date(2026, 5, 20))

        self.assertEqual(line[53:63].strip(), "VRACAR")

    def test_rejects_generated_order_without_explicit_regenerate(self):
        order = create_order()
        order.virman_generated = True
        order.save(update_fields=["virman_generated"])

        with self.assertRaises(ValidationError):
            build_virman_file([order], datetime.date(2026, 5, 20), timezone.now())

    def test_allows_generated_order_with_explicit_regenerate(self):
        order = create_order()
        order.virman_generated = True
        order.save(update_fields=["virman_generated"])

        virman_file = build_virman_file(
            [order],
            datetime.date(2026, 5, 20),
            timezone.now(),
            allow_regenerate=True,
        )

        self.assertEqual(len(virman_file.content.splitlines()), 3)

    def test_virman_uses_supplied_payment_date_instead_of_order_date(self):
        order = create_order()
        order.order_date = datetime.date(2026, 5, 21)
        order.save(update_fields=["order_date"])

        virman_file = build_virman_file(
            [order],
            datetime.date(2026, 6, 15),
            timezone.datetime(2026, 5, 20, 10, 30, tzinfo=datetime.UTC),
        )
        lines = virman_file.content.splitlines()

        self.assertEqual(lines[0][63:69], "150626")
        self.assertEqual(lines[2][172:180], "15062601")

    def test_virman_allows_orders_with_different_order_dates_when_payment_date_is_selected(self):
        first_order = create_order(order_number="01/2026-11")
        second_order = create_order(
            employee=create_employee(code=9011, account_number="325-9300600276066-68"),
            order_number="01/2026-12",
        )
        second_order.order_date = datetime.date(2026, 5, 21)
        second_order.save(update_fields=["order_date"])

        virman_file = build_virman_file([first_order, second_order], datetime.date(2026, 5, 20), timezone.now())

        self.assertEqual(len(virman_file.content.splitlines()), 4)


class TxtJsonConverterTests(TestCase):
    def test_converts_fixed_width_virman_txt_to_internal_json_records(self):
        sample_path = Path(__file__).resolve().parent.parent / "Virman-165-B5-2.TXT"
        uploaded_file = SimpleUploadedFile(
            "Virman-165-B5-2.TXT",
            sample_path.read_bytes(),
            content_type="text/plain",
        )

        conversion = convert_virman_txt_to_internal_json(uploaded_file)

        self.assertEqual(len(conversion.records), 19)
        first = conversion.records[0]
        self.assertEqual(first["PaymentBasis"], "Upl.zarade")
        self.assertEqual(first["PaymentCode"], 240)
        self.assertEqual(first["Amount"], 71054.57)
        self.assertEqual(first["DebtorBankAccount"], "205000000001445485")
        self.assertIsNone(first["DebtorCodeModel"])
        self.assertEqual(first["DebtorCode"], "")
        self.assertEqual(first["CreditorName"], "DELIC-NIKOLIC IVANA")
        self.assertEqual(first["CreditorAddress"], "GROCKA")
        self.assertEqual(first["CreditorBankAccount"], "325930060005536258")
        self.assertEqual(first["CreditorCodeModel"], 97)
        self.assertEqual(first["CreditorCode"], "6891000000063670692")
        self.assertIs(first["UrgentPayment"], True)
        self.assertEqual(first["ExpectedPaymentDate"], "2026-07-10")
        self.assertIsNone(first["ExternalId"])
        self.assertIsNone(first["UserGroupName"])
        self.assertEqual(first["UserTags"], "")
        self.assertEqual(first["Comment"], "")

        parsed_json = json.loads(conversion.json_text)
        self.assertEqual(parsed_json[0]["CreditorName"], "DELIC-NIKOLIC IVANA")


@override_settings(ALLOWED_HOSTS=["testserver"])
class IsplataNeoporezovanihViewTests(TestCase):
    def create_isplate_user(self, username="blagajna", permission_code="isplate:neoporezive_isplate"):
        permission = PermissionCode.objects.create(code=permission_code)
        role = Role.objects.create(name="Blagajna", slug="blagajna")
        role.permissions.add(permission)
        user = get_user_model().objects.create_user(username=username, password="test")
        user.roles.add(role)
        return user

    def test_isplate_permission_sees_all_centers_without_center_scope(self):
        order = create_order(order_number="77/2026-10", center="77")
        user = self.create_isplate_user()
        self.client.force_login(user)

        response = self.client.get(reverse("isplate:neoporezive_isplate"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.order_number)

    def test_year_filter_and_list_date_use_order_date_not_travel_date(self):
        included_order = create_order(
            employee=create_employee(code=9020, account_number="160-5100103391558-82"),
            order_number="01/2026-20",
        )
        included_order.order_date = datetime.date(2026, 1, 15)
        included_order.travel_date = datetime.date(2025, 12, 31)
        included_order.save(update_fields=["order_date", "travel_date"])
        excluded_order = create_order(
            employee=create_employee(code=9021, account_number="325-9300600276066-68"),
            order_number="01/2025-21",
        )
        excluded_order.order_date = datetime.date(2025, 12, 31)
        excluded_order.travel_date = datetime.date(2026, 1, 15)
        excluded_order.save(update_fields=["order_date", "travel_date"])
        user = self.create_isplate_user()
        self.client.force_login(user)

        response = self.client.get(reverse("isplate:neoporezive_isplate"), {"year": "2026"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Datum izdavanja")
        self.assertContains(response, "15.01.2026")
        self.assertContains(response, included_order.order_number)
        self.assertNotContains(response, excluded_order.order_number)

    def test_non_rsd_orders_are_not_listed(self):
        rsd_order = create_order(order_number="01/2026-22")
        eur_order = create_order(
            employee=create_employee(code=9022, account_number="325-9300600276066-68"),
            order_number="01/2026-23",
        )
        eur_order.advance_payment_currency = "EUR"
        eur_order.save(update_fields=["advance_payment_currency"])
        user = self.create_isplate_user()
        self.client.force_login(user)

        response = self.client.get(reverse("isplate:neoporezive_isplate"), {"status": "all"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, rsd_order.order_number)
        self.assertNotContains(response, eur_order.order_number)

    def test_non_rsd_selected_order_is_rejected_as_unavailable(self):
        order = create_order()
        order.advance_payment_currency = "EUR"
        order.save(update_fields=["advance_payment_currency"])
        user = get_user_model().objects.create_user(
            username="isplate-non-rsd",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("isplate:neoporezive_isplate"),
            {
                "order_ids": [str(order.pk)],
                "payment_date": "15.06.2026",
            },
        )

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertFalse(order.virman_generated)

    def test_post_generates_file_and_marks_order(self):
        order = create_order()
        user = get_user_model().objects.create_user(
            username="isplate",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("isplate:neoporezive_isplate"),
            {
                "order_ids": [str(order.pk)],
                "payment_date": "2026-05-20",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=windows-1250")
        self.assertIn("Virman-putni-nalozi-", response["Content-Disposition"])
        content = response.content.decode("cp1250")
        self.assertTrue(all(len(line) == RECORD_LENGTH for line in content.splitlines()))

        order.refresh_from_db()
        self.assertTrue(order.virman_generated)
        self.assertEqual(order.virman_generated_by, user)
        self.assertIsNotNone(order.virman_generated_at)

    def test_post_accepts_flatpickr_payment_date_format(self):
        order = create_order(order_number="01/2026-31")
        user = get_user_model().objects.create_user(
            username="isplate-flatpickr",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("isplate:neoporezive_isplate"),
            {
                "order_ids": [str(order.pk)],
                "payment_date": "15.06.2026",
            },
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("cp1250")
        lines = content.splitlines()
        self.assertEqual(lines[0][63:69], "150626")
        self.assertEqual(lines[2][172:180], "15062601")

    def test_pending_for_date_generates_unmarked_orders_without_selection(self):
        pending_order = create_order(
            employee=create_employee(code=9002, account_number="325-9300600276066-68"),
            order_number="01/2026-2",
        )
        generated_order = create_order(
            employee=create_employee(code=9003, account_number="160-5100103391558-82"),
            order_number="01/2026-3",
        )
        generated_order.virman_generated = True
        generated_order.save(update_fields=["virman_generated"])
        user = get_user_model().objects.create_user(
            username="isplate-bulk",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("isplate:neoporezive_isplate"),
            {
                "payment_date": "2026-05-20",
                "virman_action": "pending_for_date",
            },
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("cp1250")
        self.assertEqual(len(content.splitlines()), 3)
        pending_order.refresh_from_db()
        generated_order.refresh_from_db()
        self.assertTrue(pending_order.virman_generated)
        self.assertTrue(generated_order.virman_generated)

    def test_post_rejects_generated_order_without_regenerate_flag(self):
        order = create_order()
        order.virman_generated = True
        order.save(update_fields=["virman_generated"])
        user = get_user_model().objects.create_user(
            username="isplate2",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("isplate:neoporezive_isplate"),
            {
                "order_ids": [str(order.pk)],
                "payment_date": "2026-05-20",
            },
        )

        self.assertEqual(response.status_code, 302)

    def test_post_allows_generated_order_with_regenerate_flag(self):
        order = create_order()
        order.virman_generated = True
        order.save(update_fields=["virman_generated"])
        user = get_user_model().objects.create_user(
            username="isplate3",
            password="test",
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("isplate:neoporezive_isplate"),
            {
                "order_ids": [str(order.pk)],
                "payment_date": "2026-05-20",
                "allow_regenerate": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Virman-putni-nalozi-", response["Content-Disposition"])

    def test_converter_page_downloads_json_from_uploaded_txt(self):
        sample_path = Path(__file__).resolve().parent.parent / "Virman-165-B5-2.TXT"
        user = self.create_isplate_user(
            username="converter",
            permission_code="isplate:converter",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("isplate:converter"),
            {
                "txt_file": SimpleUploadedFile(
                    "Virman-165-B5-2.TXT",
                    sample_path.read_bytes(),
                    content_type="text/plain",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json; charset=utf-8")
        self.assertIn('filename="Virman-165-B5-2.json"', response["Content-Disposition"])
        records = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(records), 19)
        self.assertEqual(records[0]["CreditorName"], "DELIC-NIKOLIC IVANA")
