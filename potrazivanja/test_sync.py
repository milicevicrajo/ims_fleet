from copy import deepcopy
from datetime import datetime, date, timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from core.models import Role, PermissionCode, RolePermission, OrganizationalUnit
from .models import (CollectionState, CollectionSyncRun, CollectionContact, CollectionActivity,
                     CollectionProfile, SourceDataset, SourceRow, ImportIssue, ReceivablePosting,
                     InvoiceDocument, LegacyImportMap)
from .services.source import SOURCES
from .services.sync import sync_collections, bucket, sync_lock
from finansije.services.sync import SyncBusy

OBSERVED = datetime(2026, 9, 18, 10, tzinfo=timezone.utc)


def fixture():
    data = {name: [] for name in SOURCES}
    data['partneri'] = [dict(sif_pred=1, grupa=1, sif_par=42, naz_par='Kupac'),
                        dict(sif_pred=1, grupa=1, sif_par=43, naz_par='Drugi')]
    data['posao'] = [dict(sif_pred=1, sif_pos='436111', blok='43')]
    base = dict(god=2026, sif_par=42, naz_par='Kupac', sif_vrs='IF', br_naloga=1,
                dat_naloga=date(2026, 9, 1), stavka=1, vez_dok='IF-1', datum=date(2026, 9, 1),
                oj=43, dpo=date(2026, 9, 10), knt='20400', dug=Decimal('100.01'), pot=Decimal('0'), sif_pos='436111')
    data['baza'] = [base]
    data['dodela_baketa'] = [dict(sif_par=42, naz_par='Kupac', vez_dok='IF-1', sif_pos='436111',
        duguje=Decimal('100.01'), potrazuje=Decimal('0'), saldo=Decimal('100.01'),
        dpo=date(2026,9,10), danasnji_datum=OBSERVED, broj_dana=8, baket=30, kategorija=1, ino=0)]
    data['kontakti'] = [dict(id=1,sif_par=42,naz_par='Kupac',kontakt='Ime / 123',email='x@example.test',napomena='Staro')]
    data['napomene'] = [dict(id=1,sif_par=42,naz_par='Kupac',napomene='Napomena',veliki='da')]
    data['pozivi_tel'] = [dict(id=1,sif_par=42,naz_par='Kupac',datum=datetime(2026,9,1,12),napomena='Poziv')]
    data['opomene'] = [dict(id=1,sif_par=42,naz_par='Kupac',god=2026,br_opomene=5,datum=date(2026,9,1),iznos=100.01,fakture='IF-1; IF-2',napomene='')]
    data['avans_klijent'] = [dict(id=1,sif_par=42,note='Proveri')]
    data['tabela_if'] = [dict(god=2006,sif_par=42,vez_dok='STARA',dpo=None,saldo=Decimal('999999999999999999.99'))]
    return data


class FullSyncTests(TestCase):
    def setUp(self):
        self.data = fixture()
        OrganizationalUnit.objects.create(code='436111', center='43', name='Posao')

    def sync(self):
        with patch('potrazivanja.services.sync.extract', return_value=(deepcopy(self.data), OBSERVED)):
            return sync_collections(trigger='import', include_legacy=True)

    def test_full_sync_and_repeat_preserve_keys_history_and_exact_amounts(self):
        first = self.sync()
        counts = (SourceDataset.objects.count(), SourceRow.objects.count())
        contact_pk = CollectionContact.objects.get().pk
        posting_pk = ReceivablePosting.objects.get().pk
        second = self.sync()
        self.assertEqual((SourceDataset.objects.count(), SourceRow.objects.count()), counts)
        self.assertEqual(CollectionContact.objects.get().pk, contact_pk)
        self.assertEqual(ReceivablePosting.objects.get().pk, posting_pk)
        self.assertEqual(ReceivablePosting.objects.get().last_seen_run_id, second.pk)
        self.assertEqual(InvoiceDocument.objects.get().amount_rsd, Decimal('100.01'))
        self.assertEqual(CollectionState.objects.get().current_snapshot.run_id, second.pk)
        self.assertEqual(first.snapshots.get().positions.get().balance, Decimal('100.01'))
        self.assertEqual(second.control_totals['partner_job_buckets']['differences'], 0)
        self.assertFalse(ImportIssue.objects.filter(code='local_edit_conflict').exists())
        self.assertTrue(CollectionProfile.objects.get().important_customer)
        self.assertTrue(CollectionProfile.objects.get().needs_review)
        self.assertEqual(LegacyImportMap.objects.count(), 5)

    def test_source_changes_and_deletions_keep_original_history(self):
        self.sync()
        self.data['kontakti'][0]['napomena'] = 'Izmenjeno'
        self.sync()
        self.assertEqual(CollectionContact.objects.get().note, 'Izmenjeno')
        self.data['kontakti'] = []
        self.sync()
        self.assertFalse(CollectionContact.objects.get().active)
        self.assertEqual(SourceDataset.objects.filter(name='kontakti').count(), 3)
        self.data['kontakti'] = fixture()['kontakti']
        self.sync()
        self.assertTrue(CollectionContact.objects.get().active)

    def test_local_edits_are_never_overwritten(self):
        self.sync()
        CollectionContact.objects.update(note='Lokalna izmena')
        self.data['kontakti'][0]['napomena'] = 'Druga izvorna izmena'
        run = self.sync()
        self.assertEqual(CollectionContact.objects.get().note, 'Lokalna izmena')
        self.assertTrue(run.issues.filter(code='local_edit_conflict').exists())

    def test_failed_reconciliation_rolls_back_all_published_changes(self):
        first = self.sync()
        self.data['kontakti'][0]['napomena'] = 'Ne sme se objaviti'
        self.data['dodela_baketa'][0].update(duguje=Decimal('120'),saldo=Decimal('120'))
        with self.assertRaisesMessage(ValueError,'Kontrola'):
            self.sync()
        self.assertEqual(CollectionState.objects.get().current_snapshot.run_id, first.pk)
        self.assertEqual(CollectionContact.objects.get().note, 'Staro')
        self.assertEqual(CollectionSyncRun.objects.first().status, 'failed')

    def test_orphan_is_preserved_without_guessing_identity(self):
        self.data['kontakti'][0]['sif_par'] = 42.5
        run = self.sync()
        self.assertIsNone(CollectionContact.objects.get().identity)
        self.assertTrue(run.issues.filter(code='unlinked_operation').exists())

    def test_closed_positions_disappear_but_postings_remain(self):
        self.sync()
        self.data['baza'][0]['pot'] = Decimal('100.01')
        self.data['dodela_baketa'] = []
        run = self.sync()
        self.assertEqual(run.snapshots.get().positions.count(), 0)
        self.assertEqual(ReceivablePosting.objects.count(), 1)
        self.assertTrue(ReceivablePosting.objects.get().active)

    def test_missing_due_and_negative_balances_match_legacy(self):
        self.data['baza'][0].update(dug=Decimal('0'), pot=Decimal('150.02'))
        self.data['dodela_baketa'][0].update(duguje=Decimal('0'),potrazuje=Decimal('150.02'),saldo=Decimal('-150.02'),dpo=None,baket=Decimal('0.1'))
        run = self.sync()
        self.assertEqual(run.control_totals['totals']['balance'], '-150.02')
        self.assertEqual(run.control_totals['totals']['unknown_due_count'], 1)

    def test_concurrent_sync_is_skipped(self):
        with sync_lock():
            with self.assertRaises(SyncBusy):
                self.sync()
        self.assertEqual(CollectionSyncRun.objects.get().status, 'skipped')

    def test_duplicate_posting_cannot_be_published(self):
        self.data['baza'].append(deepcopy(self.data['baza'][0]))
        with self.assertRaisesMessage(ValueError,'Dupliran'):
            self.sync()
        self.assertFalse(CollectionState.objects.exists())

    def test_bucket_boundaries(self):
        from datetime import timedelta
        today = OBSERVED.date()
        for days, expected in [(0,'0.1'),(1,'30'),(30,'30'),(31,'45'),(45,'45'),(46,'60'),(60,'60'),(61,'90'),(90,'90'),(91,'180'),(180,'180'),(181,'181')]:
            self.assertEqual(bucket(today-timedelta(days=days),today), expected)

    def test_source_catalog_maps_jobs_missing_in_organizational_units(self):
        OrganizationalUnit.objects.all().delete()
        run = self.sync()
        self.assertEqual(run.snapshots.get().positions.get().center_code, '43')

    def test_locally_edited_customer_flags_are_preserved(self):
        self.sync()
        CollectionProfile.objects.update(important_customer=False)
        run = self.sync()
        self.assertFalse(CollectionProfile.objects.get().important_customer)
        self.assertTrue(run.issues.filter(code='local_profile_conflict').exists())

    def test_readback_catches_incorrect_normalized_amounts(self):
        from .services.sync import bulk_create
        def corrupt(model, objects):
            if model is ReceivablePosting:
                for obj in objects:
                    obj.credit += Decimal('1')
            return bulk_create(model, objects)
        with patch('potrazivanja.services.sync.bulk_create', side_effect=corrupt):
            with self.assertRaisesMessage(ValueError, 'Kontrola prenetih'):
                self.sync()
        self.assertFalse(CollectionState.objects.exists())


class ParallelViewsTests(TestCase):
    # Keep the view fixture independent of external SQL/legacy unmanaged models.
    def setUp(self):
        self.data = fixture()
        OrganizationalUnit.objects.create(code='436111', center='43', name='Posao')
        self.run = FullSyncTests.sync(self)
        self.admin = get_user_model().objects.create_user(username='collections-admin',is_superuser=True)
        self.user = get_user_model().objects.create_user(username='collections-scoped')
        role = Role.objects.create(name='Scoped collections',slug='pregled-naplate')
        perm = PermissionCode.objects.create(code='potrazivanja:dashboard')
        RolePermission.objects.create(role=role,permission=perm)
        self.user.roles.add(role)

    def test_empty_scope_does_not_expose_any_money(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('potrazivanja:table_data'))
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['recordsTotal'],0)
        self.assertEqual(self.client.get(reverse('potrazivanja:table_data'), {'kind':'contacts'}).status_code,403)
        self.assertEqual(self.client.post(reverse('potrazivanja:sync_status')).status_code,403)

    def test_scope_is_applied_on_direct_ajax_and_detail(self):
        self.client.force_login(self.user)
        partner = ReceivablePosting.objects.get().identity
        self.assertEqual(self.client.get(reverse('potrazivanja:partner_detail',args=[partner.pk])).status_code,403)
        self.user.allowed_center_codes='43';self.user.save()
        response=self.client.get(reverse('potrazivanja:table_data'),{'kind':'positions'})
        self.assertEqual(response.json()['recordsTotal'],1)
        self.assertEqual(self.client.get(reverse('potrazivanja:partner_detail',args=[partner.pk])).status_code,200)

    def test_pages_and_all_tabs_render_and_ajax_has_numeric_sort(self):
        self.client.force_login(self.admin)
        from .views import TABLES
        for kind in TABLES:
            with self.subTest(kind=kind):
                self.assertEqual(self.client.get(reverse('potrazivanja:dashboard'),{'view':kind}).status_code,200)
                response=self.client.get(reverse('potrazivanja:table_data'),{'kind':kind})
                self.assertEqual(response.status_code,200)
        data=self.client.get(reverse('potrazivanja:table_data')).json()['data']
        self.assertEqual(data[0][-1]['sort'],'100.01')
        self.assertEqual(self.client.get(reverse('potrazivanja:sync_status')).status_code,200)
        partner=ReceivablePosting.objects.get().identity
        self.assertEqual(self.client.get(reverse('potrazivanja:partner_detail',args=[partner.pk])).status_code,200)

    def test_sync_button_calls_plain_function(self):
        self.client.force_login(self.admin)
        with patch('potrazivanja.views.sync_collections',return_value=self.run) as sync:
            response=self.client.post(reverse('potrazivanja:sync_status'))
        self.assertEqual(response.status_code,302)
        sync.assert_called_once_with(requested_by=self.admin)

    def test_negative_values_sort_numerically_not_lexically(self):
        rows = [[{'kind':'money','display':str(v),'sort':str(v)}]*12 for v in (-2,-100,-20,10)]
        self.client.force_login(self.admin)
        with patch('potrazivanja.views.rows_for', return_value=rows):
            response = self.client.get(reverse('potrazivanja:table_data'),{'order[0][column]':11,'order[0][dir]':'asc'})
        self.assertEqual([r[0]['sort'] for r in response.json()['data']],['-100','-20','-2','10'])

    def test_source_job_catalog_is_used_for_center_scoped_ajax(self):
        OrganizationalUnit.objects.all().delete()
        self.user.allowed_center_codes = '43';self.user.save()
        self.client.force_login(self.user)
        response=self.client.get(reverse('potrazivanja:table_data'),{'kind':'postings'})
        self.assertEqual(response.json()['recordsTotal'],1)
