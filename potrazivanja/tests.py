from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from pravna.models import Postupak
from ugovori.models import Partner
from .models import (AgingRule, BalanceSnapshot, CollectionActivity, CollectionContact,
                     CollectionNotice, CollectionNoticeItem, CollectionProfile, CollectionState,
                     CollectionSyncRun, DueDateEvidence, ElectronicInvoiceStatus,
                     FinancePartnerIdentity, ImportIssue, InvoiceDocument, LegacyImportMap,
                     LegalCaseLink, ReceivablePosition, ReceivablePosting)


class CollectionsSchemaTests(TestCase):
    def setUp(self):
        self.run = CollectionSyncRun.objects.create(dataset="ledger", trigger="import")
        self.identity = FinancePartnerIdentity.objects.create(company=1, partner_group=1, partner_code=42)

    def invoice(self, **changes):
        values = dict(company=1, source_key="2026/IF/1", identity=self.identity, year=2026, number="1")
        values.update(changes)
        return InvoiceDocument.objects.create(**values)

    def snapshot(self, **changes):
        values = dict(run=self.run, company=1, as_of_date=date(2026, 9, 18),
                      source_observed_at=timezone.now(), rules_version="legacy-v1")
        values.update(changes)
        return BalanceSnapshot.objects.create(**values)

    def posting(self, **changes):
        values = dict(company=1, year=2026, journal_type="IF", journal_number=1, line_number=1,
                      identity=self.identity, partner_group=1, partner_code=42, account="20400",
                      booking_date=date(2026, 9, 18), debit=Decimal("100.01"), credit=Decimal("150.02"),
                      source_hash="a" * 64, last_seen_run=self.run)
        values.update(changes)
        return ReceivablePosting.objects.create(**values)

    def test_financial_identity_includes_company_and_group(self):
        FinancePartnerIdentity.objects.create(company=2, partner_group=1, partner_code=42)
        FinancePartnerIdentity.objects.create(company=1, partner_group=10, partner_code=42)
        with self.assertRaises(IntegrityError), transaction.atomic():
            FinancePartnerIdentity.objects.create(company=1, partner_group=1, partner_code=42)

    def test_existing_partner_can_have_multiple_financial_identities(self):
        partner = Partner.objects.create(name="Postojeći partner")
        self.identity.partner = partner
        self.identity.save()
        FinancePartnerIdentity.objects.create(company=1, partner_group=10, partner_code=42, partner=partner)
        self.assertEqual(partner.finance_identities.count(), 2)
        with self.assertRaises(ProtectedError):
            partner.delete()

    def test_document_number_can_repeat_across_years_but_source_key_cannot(self):
        self.invoice()
        self.invoice(year=2025, source_key="2025/IF/1")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.invoice(number="changed")

    def test_posting_key_retains_year_and_preserves_signed_decimals(self):
        posting = self.posting(debit=Decimal("-100.01"))
        posting.refresh_from_db()
        self.assertEqual(posting.debit, Decimal("-100.01"))
        self.posting(year=2025)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.posting(credit=Decimal("0"))

    def test_cross_partner_or_company_links_are_rejected_by_validation(self):
        other = FinancePartnerIdentity.objects.create(company=2, partner_group=1, partner_code=42)
        document = self.invoice()
        document.identity = other
        with self.assertRaises(ValidationError):
            document.clean()
        posting = self.posting(identity=other)
        with self.assertRaises(ValidationError):
            posting.clean()

    def test_legacy_records_without_partner_can_be_preserved(self):
        contact = CollectionContact.objects.create(name="Nasleđeni kontakt", legacy_partner_name="Neusaglašen naziv")
        CollectionActivity.objects.create(kind="note", text="Originalna napomena")
        notice = CollectionNotice.objects.create(kind="reminder", original_invoice_text="IF-1; nejasna veza")
        LegacyImportMap.objects.create(source_table="kontakti", source_key="123", target_model=contact._meta.label_lower,
                                       target_pk=contact.pk, source_hash="b" * 64, first_run=self.run, last_run=self.run,
                                       raw_data={"sif_par": None, "kontakt": "original"})
        ImportIssue.objects.create(run=self.run, code="unresolved_partner", source_table="kontakti", source_key="123",
                                   message="Partner nije utvrđen.")
        self.assertIsNone(contact.identity_id)
        self.assertEqual(notice.original_invoice_text, "IF-1; nejasna veza")
        with self.assertRaises(IntegrityError), transaction.atomic():
            LegacyImportMap.objects.create(source_table="kontakti", source_key="123", target_model="different",
                                           target_pk=1, source_hash="c" * 64, first_run=self.run, last_run=self.run)

    def test_important_customer_and_review_marker_belong_to_profile(self):
        profile = CollectionProfile.objects.create(identity=self.identity, important_customer=True, needs_review=True)
        CollectionActivity.objects.create(identity=self.identity, kind="note", text="Druga napomena")
        profile.refresh_from_db()
        self.assertTrue(profile.important_customer)
        self.assertTrue(profile.needs_review)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CollectionProfile.objects.create(identity=self.identity)

    def test_due_evidence_keeps_repeated_source_rows_without_guessing_missing_dates(self):
        values = dict(import_run=self.run, source_table="tabela_if", source_key="d" * 64, year=2006, partner_code=42)
        DueDateEvidence.objects.create(**values)
        DueDateEvidence.objects.create(**values, occurrence=2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DueDateEvidence.objects.create(**values)
        evidence = DueDateEvidence.objects.first()
        self.assertIsNone(evidence.due_date)
        self.assertIsNone(evidence.company)
        evidence.identity = self.identity
        with self.assertRaises(ValidationError):
            evidence.clean()

    def test_negative_open_balance_and_exact_arithmetic_constraint(self):
        snapshot = self.snapshot()
        values = dict(snapshot=snapshot, identity=self.identity, reference="IF-1", job_code="436111",
                      account_family="204", debit=Decimal("100.01"), credit=Decimal("150.02"))
        position = ReceivablePosition.objects.create(**values, balance=Decimal("-50.01"))
        position.refresh_from_db()
        self.assertEqual(position.balance, Decimal("-50.01"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            ReceivablePosition.objects.create(**dict(values, reference="IF-2"), balance=Decimal("0.00"))

    def test_snapshot_current_pointer_requires_published_matching_company(self):
        snapshot = self.snapshot()
        state = CollectionState(company=1, current_snapshot=snapshot)
        with self.assertRaises(ValidationError):
            state.clean()
        snapshot.status = "published"
        snapshot.published_at = timezone.now()
        snapshot.save()
        state.clean()
        state.company = 2
        with self.assertRaises(ValidationError):
            state.clean()

    def test_publication_and_run_time_database_constraints(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.snapshot(status="published")
        with self.assertRaises(IntegrityError), transaction.atomic():
            CollectionSyncRun.objects.create(dataset="ledger", trigger="manual", finished_at=timezone.now() - timedelta(days=1))

    def test_notice_lines_keep_original_amount_and_require_same_partner(self):
        document = self.invoice(amount_rsd=Decimal("100.00"))
        notice = CollectionNotice.objects.create(identity=self.identity, kind="reminder")
        item = CollectionNoticeItem.objects.create(notice=notice, document=document, line_number=1, amount_snapshot=Decimal("100.00"))
        document.amount_rsd = Decimal("80.00")
        document.save()
        item.refresh_from_db()
        self.assertEqual(item.amount_snapshot, Decimal("100.00"))
        with self.assertRaises(ProtectedError):
            document.delete()
        notice.identity = FinancePartnerIdentity.objects.create(company=1, partner_group=1, partner_code=43)
        notice.save()
        item.notice = notice
        with self.assertRaises(ValidationError):
            item.clean()

    def test_sef_key_is_original_id_not_printed_invoice_number(self):
        values = dict(company=1, eid="2026IF1", year=2026, observed_at=timezone.now(), last_seen_run=self.run)
        ElectronicInvoiceStatus.objects.create(source_id=1, **values)
        ElectronicInvoiceStatus.objects.create(source_id=2, **values)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ElectronicInvoiceStatus.objects.create(source_id=1, **dict(values, eid="changed"))

    def test_legal_case_link_preserves_existing_case(self):
        case = Postupak.objects.create(tip="tuzeni", broj_predmeta="P 1/2026")
        link = LegalCaseLink.objects.create(legacy_case_id=case.pk, identity=self.identity)
        original_id = case.pk
        case.delete()
        link.refresh_from_db()
        self.assertEqual(link.legacy_case_id, original_id)

    def test_seven_seeded_aging_ranges_cover_boundaries_once(self):
        rules = list(AgingRule.objects.all())
        self.assertEqual(len(rules), 7)
        for days in [-5, 0, 1, 30, 31, 45, 46, 60, 61, 90, 91, 180, 181, 999]:
            matches = [r for r in rules if (r.min_days is None or days >= r.min_days) and (r.max_days is None or days <= r.max_days)]
            self.assertEqual(len(matches), 1, days)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AgingRule.objects.create(code="invalid", name="invalid", min_days=5, max_days=2, sort_order=99)
