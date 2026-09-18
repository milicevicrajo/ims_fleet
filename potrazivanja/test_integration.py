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
