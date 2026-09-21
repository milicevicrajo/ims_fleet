from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase, SimpleTestCase
from django.urls import reverse

from core.models import PermissionCode, Role
from menice.models import Menica, UlaznaMenica
from .bank_forms import BankContactForm, BankPeriodForm
from .models import BankAccountRule, BankBillPlacement, BankContact
from .services.banks import build_report, bank_entries, suggested_bank
from .tests import save_entry

BANKS = [dict(code=2, name="Raiffeisen banka", zr="908-1", fields=[]), dict(code=3, name="NLB banka", zr="908-2", fields=[])]


def row(**changes):
    result = dict(account="24100", account_name="Tekući račun", partner_group=11, partner_code=2,
                  currency="DIN", debit_credit_flag="d", debit=Decimal("0"), credit=Decimal("0"), foreign_amount=Decimal("0"),
                  booking_date=date(2026, 1, 1), journal_type="IZ2", pk=1)
    result.update(changes)
    return result


class BankCalculationTests(SimpleTestCase):
    def calculate(self, entries, rules=(), start=date(2026, 1, 1), end=date(2026, 6, 30)):
        return build_report(entries, BANKS, rules, start, end, today=date(2026, 9, 21))

    def test_opening_is_not_turnover_and_balance_reconciles(self):
        report = self.calculate([row(journal_type="POC", debit=Decimal("100")), row(debit=Decimal("50")), row(credit=Decimal("20"), debit_credit_flag="p")])
        totals = report["banks"][0]["totals"]
        self.assertEqual((totals["opening"], totals["inflow"], totals["outflow"], totals["turnover"], totals["balance"]), (100, 50, 20, 70, 130))

    def test_period_and_ytd_are_separate(self):
        report = self.calculate([row(journal_type="POC", debit=Decimal("100")), row(debit=Decimal("20")),
            row(booking_date=date(2026, 4, 1), debit=Decimal("30")), row(booking_date=date(2026, 8, 1), credit=Decimal("10"))], start=date(2026, 4, 1))
        total = report["banks"][0]["totals"]
        self.assertEqual((total["opening"], total["turnover"], total["balance"], total["ytd_inflow"], total["ytd_outflow"]), (120, 30, 150, 50, 10))

    def test_foreign_currency_and_reversal_keep_correct_sides(self):
        rule = SimpleNamespace(account="24404", bank_code=2, segment="foreign")
        rows = [row(account="24404", partner_group=0, partner_code=0, currency="EUR", debit=Decimal("11700"), foreign_amount=Decimal("100")),
                row(account="24404", partner_group=0, partner_code=0, currency="EUR", credit=Decimal("2340"), foreign_amount=Decimal("20"), debit_credit_flag="p"),
                row(account="24404", partner_group=0, partner_code=0, currency="EUR", debit=Decimal("-1170"), foreign_amount=Decimal("10"))]
        item = self.calculate(rows, [rule])["banks"][0]["accounts"][0]
        self.assertEqual((item["fx"]["inflow"], item["fx"]["outflow"], item["fx"]["balance"]), (90, 20, 70))
        self.assertEqual(item["rsd"]["balance"], 8190)

    def test_eur_and_usd_are_never_added_as_one_currency(self):
        result = self.calculate([row(account="24404", currency="EUR", foreign_amount=Decimal("100")), row(account="24404", currency="USD", foreign_amount=Decimal("200"))])
        self.assertEqual({a["currency"] for a in result["banks"][0]["accounts"]}, {"EUR", "USD"})

    def test_missing_deviza_is_explicit(self):
        result = self.calculate([row(currency="EUR", foreign_amount=None)])
        self.assertTrue(result["banks"][0]["accounts"][0]["fx_missing"])

    def test_other_partner_group_cannot_be_assigned_by_numeric_code_or_rule(self):
        rule = SimpleNamespace(account="24404", bank_code=2, segment="foreign")
        result = self.calculate([row(account="24404", partner_group=1, partner_code=2, debit=Decimal("99"))], [rule])
        self.assertEqual(result["banks"][0]["totals"]["balance"], 0)
        self.assertEqual(result["unmapped"][0]["rsd"]["balance"], 99)

    def test_explicit_partner_wins_over_account_rule(self):
        rule = SimpleNamespace(account="24404", bank_code=3, segment="foreign")
        result = self.calculate([row(account="24404", debit=Decimal("20"))], [rule])
        self.assertEqual(result["banks"][0]["totals"]["balance"], 20)
        self.assertEqual(result["banks"][1]["totals"]["balance"], 0)

    def test_unmapped_and_clearing_amounts_are_retained_for_control(self):
        result = self.calculate([row(debit=Decimal("10")), row(account="24408", partner_group=0, partner_code=0, debit=Decimal("20")),
            row(account="24190", account_name="Prelazni račun", partner_group=0, partner_code=0, debit=Decimal("30"))])
        self.assertEqual(result["banks"][0]["totals"]["balance"], 10)
        self.assertEqual(result["unmapped"][0]["rsd"]["balance"], 20)
        self.assertEqual(result["excluded"][0]["rsd"]["balance"], 30)

    def test_ambiguous_bank_is_not_guessed(self):
        banks = [dict(code=15, name="Aikbank", zr="908-1"), dict(code=16, name="Aikbank", zr="908-1")]
        self.assertIsNone(suggested_bank("Devizni račun AIK banka EUR", banks))

    def test_shared_email_only_contact_and_validation(self):
        form = BankContactForm(dict(segment="Garancije", shared_emails="garancije@example.com; tim@example.com"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["shared_emails"], "garancije@example.com\ntim@example.com")
        self.assertFalse(BankContactForm(dict(segment="Garancije", shared_emails="nije email")).is_valid())

    def test_invalid_cross_year_and_future_periods(self):
        self.assertFalse(BankPeriodForm(dict(date_from="2025-12-01", date_to="2026-01-01")).is_valid())
        self.assertFalse(BankPeriodForm(dict(date_from="2099-01-01", date_to="2099-01-02")).is_valid())


@patch("finansije.bank_views.service.fetch_banks", return_value=BANKS)
class BankViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("bank-reader", password="test", allowed_center_codes="41")
        self.role = Role.objects.create(name="Bank test", slug="bank-test")
        self.user.roles.add(self.role)
        self.client.force_login(self.user)

    def grant(self, *codes):
        for code in codes:
            permission, _ = PermissionCode.objects.get_or_create(code=code)
            self.role.permissions.add(permission)

    def test_no_permission_denies_before_source_read(self, source):
        self.assertEqual(self.client.get(reverse("finansije:bank_list")).status_code, 403)
        source.assert_not_called()

    def test_bank_list_obeys_company_scope_and_active_flags(self, source):
        self.grant("finansije:bank_list", "finansije:bank_detail")
        for i, changes in enumerate([{}, {"center": "42"}, {"company": 2}, {"journal_type": "ZAT"}], 1):
            save_entry(number=i, account="24100", partner_group=11, partner_code=2, debit=Decimal("10"), credit=Decimal("0"), **changes)
        removed = save_entry(number=5, account="24100", partner_group=11, partner_code=2)
        removed.active = False; removed.save()
        response = self.client.get(reverse("finansije:bank_list"), {"date_from": "2026-01-01", "date_to": "2026-06-30"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["banks"][0]["totals"]["inflow"], 10)
        self.assertContains(response, "Banke")

    def test_bank_detail_rejects_non_bank_code(self, source):
        self.grant("finansije:bank_detail")
        self.assertEqual(self.client.get(reverse("finansije:bank_detail", args=[999])).status_code, 404)

    def test_tabs_render_and_preserve_period(self, source):
        self.grant("finansije:bank_detail")
        for tab in ("basic", "contacts", "turnover", "bills", "guarantees", "deposits"):
            response = self.client.get(reverse("finansije:bank_detail", args=[2]), {"tab": tab, "date_from": "2026-01-01", "date_to": "2026-06-30"})
            self.assertEqual(response.status_code, 200, tab)
            self.assertContains(response, "date_from=2026-01-01")

    def test_multiple_contacts_are_kept_for_one_segment(self, source):
        self.grant("finansije:bank_contact_edit", "finansije:view_all")
        url = reverse("finansije:bank_contact_edit", args=[2])
        for name in ("Osoba A", "Osoba B"):
            self.assertEqual(self.client.post(url, {"segment": "Devizno", "name": name}).status_code, 302)
        self.assertEqual(BankContact.objects.filter(bank_code=2, segment="Devizno").count(), 2)

    def test_contact_cannot_be_edited_through_another_bank(self, source):
        self.grant("finansije:bank_contact_edit", "finansije:view_all")
        contact = BankContact.objects.create(company=1, bank_code=2, segment="Devizno", name="Osoba")
        self.assertEqual(self.client.post(reverse("finansije:bank_contact_edit", args=[3, contact.pk]), {"segment": "Novo", "name": "Promena"}).status_code, 404)
        contact.refresh_from_db()
        self.assertEqual(contact.segment, "Devizno")

    def test_read_permission_cannot_write_contacts(self, source):
        self.grant("finansije:bank_list", "finansije:bank_detail", "finansije:view_all")
        self.assertEqual(self.client.post(reverse("finansije:bank_contact_edit", args=[2]), {"segment": "X", "name": "Y"}).status_code, 403)

    def test_mapping_requires_global_scope_and_rejects_shared_account(self, source):
        self.grant("finansije:bank_accounts")
        self.assertEqual(self.client.get(reverse("finansije:bank_accounts")).status_code, 403)
        self.grant("finansije:view_all")
        save_entry(account="24100", account_name="Tekući račun")
        response = self.client.post(reverse("finansije:bank_accounts"), {"account": "24100", "bank_code": 2, "segment": "dinar"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(BankAccountRule.objects.exists())

    def test_bill_registration_is_not_automatically_custody(self, source):
        self.grant("finansije:bank_detail", "finansije:view_all", "menice:menica_list", "menice:ulazna_menica_list")
        Menica.objects.create(tip="izlazna", naziv_banke="Raiffeisen banka", serijski_broj_menice="AA")
        response = self.client.get(reverse("finansije:bank_detail", args=[2]), {"tab": "bills"})
        self.assertEqual(response.context["placements"].count(), 0)
        self.assertEqual(response.context["registered_bills"].count(), 1)

    def test_both_bill_sources_and_duplicate_custody(self, source):
        self.grant("finansije:bank_bill_edit", "finansije:view_all", "menice:menica_list", "menice:ulazna_menica_list")
        bill = Menica.objects.create(tip="izlazna", serijski_broj_menice="AA")
        incoming = UlaznaMenica.objects.create(serijski_broj_menice="BB")
        url = reverse("finansije:bank_bill_edit", args=[2])
        for field, obj in (("bill", bill), ("incoming_bill", incoming)):
            response = self.client.post(url, {field: obj.pk, "delivered_on": "2026-01-01"})
            self.assertEqual(response.status_code, 302)
        self.assertEqual(BankBillPlacement.objects.count(), 2)
        response = self.client.post(reverse("finansije:bank_bill_edit", args=[3]), {"bill": bill.pk, "delivered_on": "2026-01-02"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BankBillPlacement.objects.count(), 2)
