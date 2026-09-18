"""Guard local-only reads and bounded partner hydration for the detail tabs."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from .models import FinancePartnerIdentity, CollectionContact
from .services.sync import sync_collections
from .test_sync import fixture, OBSERVED
from .views import rows_for


class LocalReadTests(TestCase):
    def setUp(self):
        with patch('potrazivanja.services.sync.extract', return_value=(fixture(), OBSERVED)):
            self.snapshot = sync_collections(trigger='import').snapshots.get()
        self.user = get_user_model().objects.create_user(username='local-reads', is_superuser=True)
        self.partner = FinancePartnerIdentity.objects.get(partner_code=42)
        FinancePartnerIdentity.objects.bulk_create([
            FinancePartnerIdentity(company=1, partner_group=1, partner_code=n, source_name='Unrelated')
            for n in range(100, 120)
        ])
        CollectionContact.objects.create(identity=self.partner, name='Contact')

    def request(self, **params):
        request = RequestFactory().get('/potrazivanja/podaci/', params)
        request.user = self.user
        return request

    def test_partner_tabs_never_load_unrelated_directory_records(self):
        original = FinancePartnerIdentity.from_db
        loaded = []

        def track(*args, **kwargs):
            obj = original(*args, **kwargs)
            loaded.append(obj.pk)
            return obj

        # Django disallows server_db access in these tests: every read must be local.
        with patch.object(FinancePartnerIdentity, 'from_db', side_effect=track):
            for kind in ('postings', 'ispravke', 'sef', 'cases', 'contacts', 'activities', 'notices'):
                rows_for(self.request(partner=self.partner.pk), self.snapshot, kind)
        self.assertTrue(loaded)
        self.assertEqual(set(loaded), {self.partner.pk})

    def test_positions_and_partner_buckets_do_not_issue_per_row_queries(self):
        for kind in ('partners', 'positions'):
            with self.subTest(kind=kind), self.assertNumQueries(1):
                rows = rows_for(self.request(), self.snapshot, kind)
                self.assertEqual(rows[0][-1]['sort'], '100.01')

    def test_global_financial_table_only_loads_referenced_partners(self):
        original = FinancePartnerIdentity.from_db
        loaded = []

        def track(*args, **kwargs):
            obj = original(*args, **kwargs)
            loaded.append(obj.pk)
            return obj

        with patch.object(FinancePartnerIdentity, 'from_db', side_effect=track):
            rows = rows_for(self.request(), self.snapshot, 'postings')
        self.assertEqual(loaded, [self.partner.pk])
        self.assertEqual(rows[0][-1]['sort'], '100.01')
