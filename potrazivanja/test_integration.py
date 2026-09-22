from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Role, PermissionCode
from finansije.models import FinanceJob
from finansije.tests import job
from finansije.services.job_tables import collection_data
from .models import (CollectionState, BalanceSnapshot, ReceivablePosition, FinancePartnerIdentity,
                     CollectionSyncRun, SourceDataset, SourceRow, CollectionSyncStep)
from .permissions import configure_permissions
from .access import can_view_job
from .services.reports import job_balances


class PermissionPropagationTests(TestCase):
    def role(self, slug, *codes):
        role=Role.objects.create(slug=slug,name=slug)
        for code in codes:role.permissions.add(PermissionCode.objects.get_or_create(code=code)[0])
        return role

    def test_all_legacy_roles_receive_entry_and_keep_old_grants_and_scope(self):
        legal=self.role('legal-only','naplata:pravna_detalj','naplata:pravna_izmeni')
        review=self.role('pregled-naplate','naplata:lista_dugovanja_po_bucketima','naplata:izvestaj_po_siframa_posla')
        editor=self.role('collections-editor','naplata:lista_dugovanja_po_bucketima','naplata:dodaj_kontakt')
        other=self.role('other','finansije:dashboard')
        old={role.pk:set(role.permissions.values_list('code',flat=True)) for role in (legal,review,editor,other)}
        configure_permissions();first={r.pk:set(r.permissions.values_list('code',flat=True)) for r in (legal,review,editor,other)}
        configure_permissions()
        for role in (legal,review,editor):
            codes=set(role.permissions.values_list('code',flat=True))
            self.assertIn('potrazivanja:dashboard',codes)
            self.assertEqual({p for p in codes if p.startswith('naplata:')},old[role.pk])
            self.assertEqual(codes,first[role.pk])
        self.assertFalse(review.permissions.filter(code='potrazivanja:view_all').exists())
        self.assertFalse(review.permissions.filter(code='potrazivanja:contact_create').exists())
        self.assertTrue(editor.permissions.filter(code='potrazivanja:contact_create').exists())
        self.assertEqual(set(other.permissions.values_list('code',flat=True)),old[other.pk])

    def test_header_keeps_new_app_and_legacy_link_is_in_sidebar_only(self):
        user=get_user_model().objects.create_user(username='navigation',is_superuser=True)
        self.client.force_login(user)
        response=self.client.get(reverse('potrazivanja:dashboard'))
        html=response.content.decode()
        self.assertNotIn('title="Naplata"',html)
        self.assertIn('title="Potraživanja"',html)
        self.assertIn('Stara Naplata (legacy)',html)
        self.assertIn(reverse('naplata:lista_dugovanja_po_bucketima'),html)


class LocalFinanceAdapterTests(TestCase):
    def setUp(self):
        self.admin=get_user_model().objects.create_user(username='adapter-admin',is_superuser=True)
        self.run=CollectionSyncRun.objects.create(dataset='full',trigger='import',status='success')
        self.today=date(2026,9,18)
        self.snapshot=BalanceSnapshot.objects.create(run=self.run,company=1,as_of_date=self.today,
            source_observed_at=timezone.now(),published_at=timezone.now(),status='published')
        CollectionState.objects.create(company=1,current_snapshot=self.snapshot)
        self.partner=FinancePartnerIdentity.objects.create(company=1,partner_group=1,partner_code=42,source_name='Kupac')
        self.sequence=0

    def position(self, amount, days, job_code='436111', center='43', family='204', snapshot=None):
        self.sequence+=1;amount=Decimal(str(amount))
        return ReceivablePosition.objects.create(snapshot=snapshot or self.snapshot,identity=self.partner,
            reference=str(self.sequence),job_code=job_code,center_code=center,account_family=family,
            due_date=self.today-timedelta(days=days) if days is not None else None,
            debit=max(amount,Decimal(0)),credit=max(-amount,Decimal(0)),balance=amount,due_date_method='legacy_views')

    def limited_user(self, center='43'):
        user=get_user_model().objects.create_user(username='adapter-scoped',allowed_center_codes=center)
        role=Role.objects.create(name='Scoped new app',slug='scoped-new')
        for code in ('potrazivanja:dashboard','finansije:dashboard'):
            role.permissions.add(PermissionCode.objects.get_or_create(code=code)[0])
        user.roles.add(role)
        return user

    def test_basic_partner_table_matches_legacy_columns_and_keeps_exact_source_amounts(self):
        self.position('100.51', 8)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('potrazivanja:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="DugovanjaBuketi" class="display compact collections-legacy-table"')
        self.assertContains(response, '<th>Šifra partnera</th><th>Partner</th><th>Nedospelo</th>')
        self.assertContains(response, '<th>Ukupno Dospelo</th><th>Ukupno</th><th>Veliki</th><th>INO</th>')
        self.assertContains(response, 'id="total_ukupno"')
        self.assertContains(response, '<td>101</td>', count=3, html=True)
        self.assertEqual(response.context['legacy_partner_rows'][0]['amounts'][-1], Decimal('100.51'))
        self.assertContains(response, 'collections-summary')
        self.assertContains(response, 'fleet-list-hero')

    def test_basic_partner_table_uses_the_same_center_scope_as_the_report(self):
        self.position('100.51', 8, center='43')
        self.position('9999', 8, center='42')
        self.client.force_login(self.limited_user('43'))
        response = self.client.get(reverse('potrazivanja:dashboard'))
        self.assertEqual(response.status_code, 200)
        rows = response.context['legacy_partner_rows']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['amounts'][-1], Decimal('100.51'))
        self.assertNotContains(response, '<th>Provera</th>')

    def test_exact_buckets_negative_and_unknown_dates_only_current_snapshot_and_job(self):
        for amount,days in [(1,0),(2,30),(3,45),(4,60),(5,90),(6,180),(7,181),(-10,None)]:self.position(amount,days)
        self.position(999,1,job_code='other')
        old=BalanceSnapshot.objects.create(run=self.run,company=1,as_of_date=date(2026,8,1),source_observed_at=timezone.now(),published_at=timezone.now(),status='published')
        self.position(999,1,snapshot=old)
        report=job_balances(self.admin,'436111')
        self.assertEqual(report['rows'][0]['amounts'],list(map(Decimal,[-9,2,3,4,5,6,7,27,18])))
        self.assertEqual(report['snapshot'].pk,self.snapshot.pk)
        self.position(20,1,family='205')
        self.assertEqual(len(job_balances(self.admin,'436111')['rows']),2)
        # Only default is allowed in this test: external source reads fail immediately.
        rendered=collection_data(self.admin,'436111')
        self.assertIn('18.09.2026.',rendered['footer']['collections_as_of'])
        self.assertIn('/potrazivanja/partner/',rendered['data'][0][0]['display'])

    def capture(self, name, rows, run=None):
        run = run or self.run
        dataset = SourceDataset.objects.create(name=name, fingerprint=f'{name}-{run.pk}',
                                               row_count=len(rows), first_run=run)
        for index, row in enumerate(rows, 1):
            SourceRow.objects.create(dataset=dataset, ordinal=index, partner_code=row.get('sif_par'),
                                     job_code=row.get('sif_pos', ''), raw_data=row)
        CollectionSyncStep.objects.create(run=run, code=name, details={'dataset_id': dataset.pk})

    def test_partner_tabs_match_naplata_and_basic_data_uses_full_identity_key(self):
        self.capture('partneri', [
            {'sif_pred': 1, 'grupa': 11, 'sif_par': 42, 'naz_par': 'Pogrešna grupa', 'zr': 'BANKA'},
            {'sif_pred': 2, 'grupa': 1, 'sif_par': 42, 'naz_par': 'Druga firma', 'zr': 'DRUGA'},
            {'sif_pred': 1, 'grupa': 1, 'sif_par': 42, 'naz_par': 'Kupac iz snimka',
             'zr': '160-123-45', 'telefon': '011123456', 'proc_rabata': 0},
        ])
        self.client.force_login(self.admin)
        response = self.client.get(reverse('potrazivanja:partner_detail', args=[self.partner.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([tab['title'] for tab in response.context['tabs']][:11], [
            'Osnovni podaci', 'Kontakti', 'Napomene', 'Opomene', 'Pozivi', 'Pozivi/pisma',
            'Tužbe', 'Dugovanja', 'Dugovanja - Baketi', 'Dugovanja po fakturama', 'Otpisana potraživanja',
        ])
        self.assertContains(response, 'Kupac iz snimka')
        self.assertContains(response, '160-123-45')
        self.assertNotContains(response, 'Pogrešna grupa')
        self.assertEqual(dict(response.context['basic_fields'])['Procenat rabata'], 0)
        for code in ('181', '180', '90', '60'):
            self.assertContains(response, f'data-kind="invoices_{code}"')

    def test_partner_invoices_and_buckets_keep_snapshot_scope_and_negative_values(self):
        first = self.position('100.51', 181)
        second = self.position('-20.25', 181, family='205')
        second.reference = first.reference
        second.save(update_fields=['reference'])
        self.position('9999', 181, job_code='426111', center='42')
        self.position('17', 180)
        self.position('13', 60)
        self.position('11', None)
        self.capture('sif_baket', [{'baket': '181.00', 'opis': 'Preko 180', 'akcija': 'Provera'}])
        self.client.force_login(self.limited_user())
        detail = self.client.get(reverse('potrazivanja:partner_detail', args=[self.partner.pk]))
        self.assertNotIn('contacts', [tab['kind'] for tab in detail.context['tabs']])
        url = reverse('potrazivanja:table_data')
        params = {'partner': self.partner.pk, 'snapshot': self.snapshot.pk, 'kind': 'invoices_181'}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        rows = response.json()['data']
        self.assertEqual(len(rows), 1)
        self.assertEqual([c['sort'] for c in rows[0][-3:]], ['100.51', '20.25', '80.26'])
        params['kind'] = 'invoices_180'
        self.assertEqual(self.client.get(url, params).json()['data'][0][-1]['sort'], '17.00')
        params['kind'] = 'buckets'
        rows = self.client.get(url, params).json()['data']
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(Decimal(row[7]['sort']) for row in rows), Decimal('121.26'))
        self.assertEqual(sum(row[-1]['display'] == 'Provera' for row in rows), 2)
        ordered = self.client.get(url, {**params, 'order[0][column]': 1, 'order[0][dir]': 'asc'}).json()['data']
        self.assertEqual([row[1]['sort'] for row in ordered], [0.1, 60, 180, 181, 181])
        # A requested historical snapshot must never read today's positions.
        old = BalanceSnapshot.objects.create(run=self.run, company=1, as_of_date=date(2026, 8, 1),
            source_observed_at=timezone.now(), published_at=timezone.now(), status='published')
        self.position('777', 250, snapshot=old)
        params.update(kind='invoices_181', snapshot=old.pk)
        self.assertEqual(self.client.get(url, params).json()['data'][0][-1]['sort'], '777.00')

    def test_partner_debts_use_local_capture_with_job_and_center_scope(self):
        self.position('12', 8)
        self.capture('posao', [{'sif_pos': '436111', 'blok': '43'}, {'sif_pos': '426111', 'blok': '42'}])
        self.capture('baza', [dict(sif_par=42, sif_pos=job_code, god=2026, oj='01', sif_vrs='IF',
                                 datum='2026-01-02', dpo='2026-02-02', vez_dok='IF-1',
                                 skr_naz='RSD', dug='12.50', pot='0.50')
                             for job_code in ('436111', '426111')])
        self.client.force_login(self.limited_user())
        url = reverse('potrazivanja:table_data')
        params = {'kind': 'debts', 'partner': self.partner.pk}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['recordsTotal'], 1)
        row = response.json()['data'][0]
        self.assertEqual(row[2]['display'], '436111')
        self.assertEqual(row[6]['display'], '02.02.2026.')
        self.assertEqual(row[-2]['sort'], '12.50')
        self.client.force_login(self.admin)
        params['job'] = '426111'
        rows = self.client.get(url, params).json()['data']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2]['display'], '426111')

    def test_new_permissions_and_center_scope_work_without_any_legacy_permission(self):
        user=self.limited_user();self.position(100,1);self.position(999,1,'426111','42')
        self.assertFalse(user.roles.filter(permissions__code__startswith='naplata:').exists())
        self.assertEqual(job_balances(user,'436111')['rows'][0]['amounts'][-1],Decimal(100))
        with self.assertRaises(PermissionDenied):job_balances(user,'426111')
        FinanceJob.objects.create(**job('436111','43'))
        self.client.force_login(user)
        response=self.client.get(reverse('finansije:job_table',args=['collections']),{'job':'436111','year':2026,'month':2})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['as_of_date'],'2026-09-18')
        self.assertEqual(response.json()['data'][0][-1]['sort'],'100.00')

    def test_empty_job_is_authorized_from_local_source_catalog(self):
        user=self.limited_user()
        dataset=SourceDataset.objects.create(name='posao',fingerprint='a'*64,row_count=1,first_run=self.run)
        SourceRow.objects.create(dataset=dataset,ordinal=1,job_code='436111',raw_data={'sif_pos':'436111','blok':'43'})
        CollectionSyncStep.objects.create(run=self.run,code='posao',details={'dataset_id':dataset.pk})
        self.assertTrue(can_view_job(user,'436111'))
        self.assertEqual(job_balances(user,'436111')['rows'],[])

    def test_missing_snapshot_is_not_reported_as_zero_and_module_denial_is_enforced(self):
        CollectionState.objects.update(current_snapshot=None)
        result=collection_data(self.admin,'436111')
        self.assertFalse(result['available']);self.assertIn('nisu dostupni',result['footer']['collections_as_of'])
        user=get_user_model().objects.create_user(username='no-collections',allowed_center_codes='43')
        with self.assertRaises(PermissionDenied):job_balances(user,'436111')
