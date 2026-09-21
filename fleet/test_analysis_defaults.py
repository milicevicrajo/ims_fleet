from datetime import date
from decimal import Decimal as D
from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import SimpleTestCase

from core.models import OrganizationalUnit
from fleet.models import JobCode, LeaseChargePeriod, VehicleAnalysisProfile
from fleet.support.analysis_defaults import estimated_purpose
from fleet.support.lease_costs import lease_amount_between
from fleet.test_economics import EconomicsFixture


class AssignmentCostTests(EconomicsFixture):
    def test_assignment_change_uses_document_date_even_without_orders(self):
        self.fuel()  # 1000 on Jan 1; 2100 on Jan 31.
        other = OrganizationalUnit.objects.create(code='P2', name='Drugi', center='02')
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.unit, assigned_date=self.start)
        JobCode.objects.create(vehicle=self.car, organizational_unit=other, assigned_date=date(2026,1,16))
        row = self.row()
        jobs = {j['code']: j for j in row['jobs']}
        self.assertEqual(jobs['P1']['amount'], 1000)
        self.assertEqual(jobs['P2']['amount'], 2100)
        self.assertEqual(jobs['P1']['days'], 15)
        self.assertEqual(jobs['P2']['days'], 16)
        self.assertEqual(row['unallocated'], 0)
        self.assertEqual(row['booked_days'], 0)

    def test_no_backfill_before_first_assignment_or_from_future(self):
        self.fuel()
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.unit, assigned_date=date(2026,1,16))
        row = self.row()
        self.assertEqual(row['unallocated'], 1000)
        self.assertEqual(row['jobs'][0]['amount'], 2100)
        self.assertEqual(sum(j['amount'] for j in row['jobs']) + row['unallocated'], row['total'])
        JobCode.objects.all().update(assigned_date=date(2026,2,1))
        self.assertEqual(self.row()['unallocated'], 3100)

    def test_null_assignment_ends_previous_assignment(self):
        self.fuel()
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.unit, assigned_date=self.start)
        JobCode.objects.create(vehicle=self.car, organizational_unit=None, assigned_date=date(2026,1,16))
        self.assertEqual(self.row()['unallocated'], 2100)

    def test_daily_contract_charge_follows_assignment_and_reconciles(self):
        self.lease()
        other = OrganizationalUnit.objects.create(code='P2', name='Drugi', center='02')
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.unit, assigned_date=self.start)
        JobCode.objects.create(vehicle=self.car, organizational_unit=other, assigned_date=date(2026,1,16))
        row = self.row()
        self.assertEqual([j['amount'] for j in row['jobs']], [15000, 16000])
        self.assertEqual(sum(m['included'] for m in row['monthly']), row['total'])

    def test_ownership_before_and_after_contract_without_holding_rows(self):
        self.holding.delete()
        self.lease(start=date(2026,1,10), end=date(2026,1,20), payment_basis='total')
        row = self.row()
        self.assertEqual(row['basis_codes'], {'owned', 'operativni'})
        self.assertAlmostEqual(row['contract'], D(31000), places=10)
        self.assertEqual(self.row(date(2026,1,21), self.end)['basis_codes'], {'owned'})

    def test_overlap_is_not_double_charged_or_assumed_owned(self):
        self.lease()
        self.lease(start=date(2026,1,16))
        row = self.row()
        self.assertEqual(row['contract'], 15000)
        self.assertIn('unknown', row['basis_codes'])
        self.assertTrue(any('Preklopljeni ugovori' in w for w in row['warnings']))

    def test_legacy_charge_table_is_not_an_additional_cost_source(self):
        lease = self.lease()
        LeaseChargePeriod.objects.create(lease=lease, start=self.start, end=self.end,
                                        amount=99999, basis='total', evidence='Stara evidencija')
        self.assertEqual(self.row()['contract'], 31000)

    def test_default_purpose_does_not_create_profile_or_require_downtime(self):
        self.profile.delete()
        self.car.category = 'prikljucno'
        self.car.save()
        row = self.row()
        self.assertEqual(row['purpose_code'], 'trailer')
        self.assertTrue(row['purpose_estimated'])
        self.assertFalse(VehicleAnalysisProfile.objects.exists())
        self.assertEqual(row['criteria'], [])
        self.assertNotIn('Evidencija zastoja', [i['label'] for i in row['readiness']])

    def test_explicit_profile_overrides_estimate(self):
        self.car.category = 'prikljucno'
        self.car.save()
        row = self.row()
        self.assertEqual(row['purpose_code'], 'laboratory')
        self.assertFalse(row['purpose_estimated'])

    def test_monthly_and_total_are_explicit_choices_on_existing_lease_form(self):
        from fleet.forms.lease import LeaseForm
        lease = self.lease()
        data = dict(vehicle=self.car.pk, contract_number='L1', lease_type='operativni',
                    partner_code='P', partner_name='Partner', job_code='P1',
                    current_payment_amount='31000', start_date='01.01.2026', end_date='31.01.2026')
        form = LeaseForm(data=data, instance=lease)
        self.assertFalse(form.is_valid())
        self.assertIn('payment_basis', form.errors)
        form = LeaseForm(data={**data, 'payment_basis': 'total'}, instance=lease)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(self.row()['contract'], 31000)

    def test_migration_classifies_existing_documented_lease_types_only(self):
        operating = self.lease(payment_basis='')
        rental = self.lease(kind='dugorocni', payment_basis='')
        financial = self.lease(kind='finansijski', payment_basis='')
        explicit = self.lease(kind='operativni', payment_basis='monthly')
        migration = import_module('fleet.migrations.0078_lease_payment_basis')
        migration.classify_existing_amounts(apps, SimpleNamespace(connection=connection))
        for lease in [operating, rental, financial, explicit]:
            lease.refresh_from_db()
        self.assertEqual(operating.payment_basis, 'total')
        self.assertEqual(rental.payment_basis, 'monthly')
        self.assertEqual(financial.payment_basis, '')
        self.assertEqual(explicit.payment_basis, 'monthly')


class ContractAmountTests(SimpleTestCase):
    def test_partial_months_and_leap_year_use_actual_calendar_days(self):
        lease = SimpleNamespace(start_date=date(2024,1,16), end_date=date(2024,3,15),
                                current_payment_amount=D(31000), payment_basis='monthly')
        self.assertEqual(lease_amount_between(lease, lease.start_date, lease.end_date), 62000)
        self.assertEqual(lease_amount_between(lease, date(2024,2,1), date(2024,2,29)), 31000)

    def test_total_contract_includes_both_end_dates(self):
        lease = SimpleNamespace(start_date=date(2026,1,1), end_date=date(2026,1,31),
                                current_payment_amount=D(31000), payment_basis='total')
        self.assertEqual(lease_amount_between(lease, date(2026,1,31), date(2026,1,31)), 1000)
        self.assertEqual(lease_amount_between(lease, date(2026,2,1), date(2026,2,28)), 0)

    def test_purpose_uses_assignment_evidence_and_not_weight(self):
        vehicle = SimpleNamespace(category='teretno', description='', weight=10000)
        assignment = SimpleNamespace(organizational_unit=SimpleNamespace(name='Laboratorija za beton'))
        self.assertEqual(estimated_purpose(vehicle, assignment)[0], 'laboratory')
        self.assertEqual(estimated_purpose(vehicle)[0], 'supervision')
