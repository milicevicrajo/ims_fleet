from datetime import date, timedelta, datetime, time
from decimal import Decimal as D
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase, SimpleTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from core.models import OrganizationalUnit, PermissionCode, Role, RolePermission
from hr.models import Employee
from fleet.models import (VehicleAnalysisProfile, VehicleHolding, Lease, LeaseChargePeriod,
    LeaseInterest, Policy, VehicleTravelOrder, VehicleDowntime, JobCode,
    VehicleEconomicAssessment, VehicleEconomicScenario, TransactionOMV, Insurance)
from fleet.test_vehicle_onboarding import vehicle
from fleet.test_cost_fixes import fueling
from fleet.services.economics import period_analysis, fleet_summary, compare_scenarios, visible_vehicles
from fleet.forms.economics import AnalysisProfileForm
from fleet.support.fuel import get_vehicle_fuel_transaction_rows


class EconomicsFixture(TestCase):
    start, end = date(2026, 1, 1), date(2026, 1, 31)

    def setUp(self):
        self.car = vehicle()
        self.profile = VehicleAnalysisProfile.objects.create(vehicle=self.car, effective_from=self.start,
            purpose='laboratory', fuel_source='legacy')
        self.holding = VehicleHolding.objects.create(vehicle=self.car, basis='owned', start_date=self.start)
        self.unit = OrganizationalUnit.objects.create(code='P1', name='Posao jedan', center='01')
        self.employee = Employee.objects.create(employee_code=9021, first_name='Test', last_name='Vozač',
            position='Vozač', department_code=1, gender='M', date_of_birth=date(1980,1,1), date_of_joining=date(2020,1,1))

    def row(self, start=None, end=None):
        return period_analysis([self.car], start or self.start, end or self.end)[0]

    def fuel(self):
        fueling(self.car, self.start, 10000, cost='1000')
        fueling(self.car, self.end, 11000, cost='2100')

    def order(self, **kwargs):
        values = dict(vehicle=self.car, employee=self.employee, created_at=self.start, closed_at=self.end,
            start_mileage=10000, end_mileage=11000, job_code=self.unit)
        values.update(kwargs)
        return VehicleTravelOrder.objects.create(**values)

    def lease(self, start=None, end=None, kind='operativni'):
        return Lease.objects.create(vehicle=self.car, lease_type=kind, contract_number='L1',
            partner_code='P', partner_name='Partner', job_code='P1', current_payment_amount=31000,
            start_date=start or self.start, end_date=end or self.end)

class FleetEconomicsTests(EconomicsFixture):
    def test_no_values_are_unknown_and_not_free_ownership(self):
        self.holding.delete()
        row = self.row()
        self.assertIsNone(row['total'])
        self.assertIsNone(row['per_km'])
        self.assertIsNone(row['downtime_days'])
        self.assertEqual(row['basis'], 'Nije potvrđeno')
        self.assertIn('Osnov raspolaganja', ' '.join(row['warnings']))
        self.assertTrue(all(m['included'] is None for m in row['monthly']))
        self.order()
        self.assertIsNone(self.row()['jobs'][0]['amount'])

    def test_aligned_km_and_monthly_and_job_totals_reconcile(self):
        self.fuel()
        self.order()
        row = self.row()
        self.assertEqual(row['total'], D('3100'))
        self.assertEqual(row['distance'], 1000)
        self.assertEqual(row['per_km'], D('3.1'))
        self.assertEqual(row['per_day'], 100)
        self.assertEqual(row['booked_days'], 31)
        self.assertEqual(sum(m['included'] for m in row['monthly']), row['total'])
        self.assertEqual(sum(j['amount'] for j in row['jobs']) + row['unallocated'], row['total'])
        self.assertEqual(row['unallocated'], 0)

    def test_costs_are_not_attached_to_current_assignment_without_order_job(self):
        self.fuel()
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.unit, assigned_date=self.start)
        self.order(job_code=None)
        row = self.row()
        self.assertEqual(row['jobs'], [])
        self.assertEqual(row['unallocated'], row['total'])

    def test_overlapping_orders_count_days_once_and_conflicting_jobs_are_unallocated(self):
        self.fuel()
        self.order()
        other = OrganizationalUnit.objects.create(code='P2', name='Drugi', center='01')
        self.order(created_at=date(2026,1,20), job_code=other)
        row = self.row()
        self.assertEqual(row['booked_days'], 31)
        self.assertEqual(row['jobs'][0]['days'], 19)
        self.assertEqual(row['unallocated'], 1200)
        self.assertIn('Preklapanje', ' '.join(row['warnings']))

    def test_missing_boundaries_or_internal_odometer_drop_blocks_unit_rate(self):
        fueling(self.car, date(2026,1,2), 10000, cost='100')
        fueling(self.car, self.end, 11000, cost='100')
        self.assertIsNone(self.row()['per_km'])
        fueling(self.car, self.start, 10500, cost='100')
        self.assertIsNone(self.row()['per_km'])
        self.assertIn('opadaju', ' '.join(self.row()['warnings']))

    def test_genuine_zero_cost_is_distinct_from_no_evidence(self):
        fueling(self.car, self.start, 1000, cost='0')
        fueling(self.car, self.end, 2000, cost='0')
        self.assertEqual(self.row()['per_km'], 0)
        self.assertEqual(fleet_summary([self.row()])['known_count'], 1)

    def test_direct_fuel_period_and_corrected_odometer_do_not_double_count_legacy(self):
        self.profile.fuel_source='transactions';self.profile.save()
        self.fuel()  # A second representation of fuel must not be added.
        for day, mileage, cost in [(self.start-timedelta(days=1),900,9000),(self.start,1000,100),(self.end,2000,200),(self.end+timedelta(days=1),3000,9000)]:
            TransactionOMV.objects.create(vehicle=self.car,transaction_date=timezone.make_aware(datetime.combine(day,time(23,59,59))),
                product_inv='OMV Diesel',quantity=10,gross_cc=cost,vat=0,mileage=0,corrected_mileage=mileage,
                invoice_no=day.isoformat(),voucher=day.isoformat(),license_plate_no='TEST',card='1')
        records=get_vehicle_fuel_transaction_rows(self.car,start=self.start,end=self.end)
        self.assertEqual(len(records),2)
        row=self.row()
        self.assertEqual(row['ledger']['totals']['fuel'],300)
        self.assertEqual(row['distance'],1000)
        self.assertEqual(row['per_km'],D('0.3'))

    def test_insurance_recovery_does_not_reduce_operating_rate(self):
        self.fuel()
        Insurance.objects.create(vehicle=self.car,kola=True,datum=self.end,potrazuje=D(5000))
        row=self.row()
        self.assertEqual(row['total'],3100)
        self.assertEqual(row['per_km'],D('3.1'))
        self.assertEqual(row['net_after_recovery'],-1900)

    def test_policy_includes_single_day_and_leap_year(self):
        Policy.objects.create(vehicle=self.car, invoice_id=5001, premium_amount=D('36600'),
            start_date=date(2024,1,1), end_date=date(2024,12,31))
        self.assertEqual(self.row(date(2024,2,29), date(2024,2,29))['policy'], 100)

    def test_unknown_lease_amount_is_not_interpreted_as_monthly_or_total(self):
        self.holding.delete()
        lease = self.lease()
        VehicleHolding.objects.create(vehicle=self.car, basis='contract', lease=lease, start_date=self.start, end_date=self.end)
        row = self.row()
        self.assertIsNone(row['contract'])
        self.assertIsNone(row['total'])
        self.assertIn('naknada', ' '.join(row['warnings']))

    def test_contract_periods_follow_holding_and_inclusive_single_day(self):
        self.holding.end_date = date(2026,1,15)
        self.holding.save()
        lease = self.lease(start=date(2026,1,1))
        VehicleHolding.objects.create(vehicle=self.car, basis='contract', lease=lease,
            start_date=date(2026,1,16), end_date=self.end)
        LeaseChargePeriod.objects.create(lease=lease, start=self.start, end=self.end,
            amount=31000, basis='monthly', evidence='Ponuda')
        self.assertEqual(self.row()['contract'], 16000)
        self.assertEqual(self.row(self.end,self.end)['contract'], 1000)

    def test_zero_contract_charge_is_recorded_zero(self):
        self.holding.delete()
        lease = self.lease()
        VehicleHolding.objects.create(vehicle=self.car, basis='contract', lease=lease, start_date=self.start, end_date=self.end)
        LeaseChargePeriod.objects.create(lease=lease, start=self.start, end=self.end, amount=0, basis='total', evidence='Bez naknade')
        self.assertEqual(self.row()['total'], 0)

    def test_interest_only_during_financial_holding(self):
        self.holding.end_date = date(2026,1,15)
        self.holding.save()
        lease = self.lease(kind='finansijski')
        VehicleHolding.objects.create(vehicle=self.car, basis='contract', lease=lease, start_date=date(2026,1,16), end_date=self.end)
        LeaseInterest.objects.create(lease=lease, year=2026, interest_amount=D('36500'))
        self.assertEqual(self.row()['interest'], 1600)

    def test_contract_period_overlap_rejected(self):
        lease = self.lease()
        LeaseChargePeriod.objects.create(lease=lease, start=self.start, end=self.end, amount=100, basis='total', evidence='Test')
        with self.assertRaises(ValidationError):
            LeaseChargePeriod.objects.create(lease=lease, start=self.end, end=self.end, amount=100, basis='monthly', evidence='Test')

    def test_downtime_union_does_not_double_count_or_infer_productivity(self):
        VehicleDowntime.objects.create(vehicle=self.car, start=self.start, end=date(2026,1,3), reason='Kvar')
        VehicleDowntime.objects.create(vehicle=self.car, start=date(2026,1,2), end=date(2026,1,4), reason='Servis')
        self.assertEqual(self.row()['downtime_days'], 4)
        self.assertEqual(self.row()['booked_days'], 0)

    def test_threshold_requires_basis_and_is_disabled_across_profile_change(self):
        self.fuel()
        self.profile.cost_limit_km = D('1')
        with self.assertRaises(ValidationError):
            self.profile.save()
        self.profile.criterion_source = 'Kontrolni primer istog obuhvata'
        self.profile.criterion_basis = 'owned'
        self.profile.save()
        self.assertTrue(self.row()['criteria'][0]['exceeded'])
        VehicleAnalysisProfile.objects.create(vehicle=self.car, effective_from=date(2026,1,20), purpose='supervision', fuel_source='legacy', cost_limit_km=1, criterion_source='Test', criterion_basis='owned')
        self.assertEqual(self.row()['criteria'], [])

    def test_drilling_has_no_cost_per_km_criterion(self):
        self.profile.purpose = 'drilling'
        self.profile.cost_limit_km = D('1')
        self.profile.criterion_source = 'Test'
        self.profile.criterion_basis = 'owned'
        with self.assertRaises(ValidationError):
            self.profile.save()

    def test_criterion_is_specific_to_holding_combination(self):
        self.fuel()
        self.profile.cost_limit_km = 1
        self.profile.criterion_source = 'Prag najma sa servisom'
        self.profile.criterion_basis = 'dugorocni'
        self.profile.save()
        self.assertEqual(self.row()['criteria'], [])
        self.assertIn('drugačije raspolaganje', ' '.join(self.row()['warnings']))

    def test_profile_duplicate_date_is_form_error_not_save_exception(self):
        form = AnalysisProfileForm(data={'effective_from':'2026-01-01','purpose':'laboratory','fuel_source':'legacy'}, instance=VehicleAnalysisProfile(vehicle=self.car))
        self.assertFalse(form.is_valid())
        self.assertIn('effective_from', form.errors)

    def test_batch_query_count_does_not_grow_per_vehicle(self):
        cars = [self.car] + [vehicle(str(i)) for i in range(2, 12)]
        with CaptureQueriesContext(connection) as single:
            period_analysis([self.car], self.start, self.end)
        with CaptureQueriesContext(connection) as batch:
            period_analysis(cars, self.start, self.end)
        self.assertLessEqual(len(batch), len(single) + 1)

    def test_weighted_fleet_rate_excludes_missing_denominators(self):
        summary = fleet_summary([
            dict(total=D(100), distance=D(10), per_km=D(10), warnings=[],criteria=[]),
            dict(total=D(900), distance=D(30), per_km=D(30), warnings=[],criteria=[]),
            dict(total=D(800), distance=None, per_km=None, warnings=[],criteria=[]),
        ])
        self.assertEqual(summary['total'], 1800)
        self.assertEqual(summary['per_km'], 25)
        self.assertEqual(summary['comparable_count'], 2)


class EconomicsReviewFixesTests(EconomicsFixture):
    """Ispravke iz pregleda koda 19.09.2026.

    Svaki test opisuje sta je bilo pogresno, da se ne bi vratilo.
    """

    def test_vehicle_without_assignment_stays_visible(self):
        # Vozilo bez ijedne dodele nema centar. Ranije ga je filter po centru
        # izbacivao (NULL IN (...) nije tacno), pa je davalo 404 na detalju.
        user = get_user_model().objects.create_user('ogranicen', password='t')
        user.allowed_center_codes = '01'
        user.save()
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.unit, assigned_date=self.start)
        neraspoređeno = vehicle('9')

        visible = list(visible_vehicles(user))

        self.assertIn(self.car, visible)
        self.assertIn(neraspoređeno, visible, msg='vozilo bez dodele ne sme da nestane')

    def test_vehicle_in_another_center_stays_hidden(self):
        # Kontrola uz prethodni test: propustanje praznog centra ne sme da otvori
        # vozila tudjeg centra.
        user = get_user_model().objects.create_user('ogranicen2', password='t')
        user.allowed_center_codes = '01'
        user.save()
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.unit, assigned_date=self.start)
        tudje = vehicle('8')
        drugi = OrganizationalUnit.objects.create(code='P2', name='Drugi', center='02')
        JobCode.objects.create(vehicle=tudje, organizational_unit=drugi, assigned_date=self.start)

        self.assertNotIn(tudje, list(visible_vehicles(user)))

    def test_handover_day_is_not_counted_as_overlap(self):
        # Pri predaji vozila zatvoren nalog dobija closed_at jednak created_at
        # sledeceg. Ranije su oba naloga tog dana bila "aktivna", pa je vozilo
        # dobijalo upozorenje o preklapanju i trosak tog dana je ostajao
        # neraspodeljen kada nalozi imaju razlicite poslove.
        self.fuel()
        drugi_posao = OrganizationalUnit.objects.create(code='P3', name='Treci', center='01')
        predaja = date(2026, 1, 16)
        self.order(created_at=self.start, closed_at=predaja, job_code=self.unit)
        self.order(created_at=predaja, closed_at=self.end, job_code=drugi_posao)

        row = self.row()

        self.assertNotIn('Preklapanje naloga', ' '.join(row['warnings']))
        self.assertEqual(row['unallocated'], D('0'), msg='dan primopredaje ne sme ostati neraspodeljen')
        dani = {job['code']: job['days'] for job in row['jobs']}
        # 01-15 prvom poslu, 16-31 drugom: ukupno 31 dan, bez dupliranja.
        self.assertEqual(dani['P1'], 15)
        self.assertEqual(dani['P3'], 16)
        self.assertEqual(sum(dani.values()), 31)

    def test_real_overlap_is_still_reported(self):
        # Kontrola uz prethodni test: stvarno preklapanje mora i dalje da se javi.
        self.fuel()
        drugi_posao = OrganizationalUnit.objects.create(code='P4', name='Cetvrti', center='01')
        self.order(created_at=self.start, closed_at=self.end, job_code=self.unit)
        self.order(created_at=date(2026, 1, 10), closed_at=self.end, job_code=drugi_posao)

        row = self.row()

        self.assertIn('Preklapanje naloga', ' '.join(row['warnings']))
        self.assertGreater(row['unallocated'], D('0'))

    def test_single_day_order_keeps_its_day(self):
        self.fuel()
        self.order(created_at=date(2026, 1, 10), closed_at=date(2026, 1, 10), job_code=self.unit)

        row = self.row()

        self.assertEqual({job['code']: job['days'] for job in row['jobs']}['P1'], 1)

    def test_closed_order_without_successor_keeps_last_day(self):
        self.fuel()
        self.order(created_at=self.start, closed_at=date(2026, 1, 10), job_code=self.unit)

        row = self.row()

        # 01-10 ukljucivo = 10 dana; bez naslednika poslednji dan pripada nalogu.
        self.assertEqual({job['code']: job['days'] for job in row['jobs']}['P1'], 10)

    def test_legacy_fuel_rows_carry_all_displayed_columns(self):
        # Kartica goriva na detalju vozila prikazuje jedinicnu cenu i neto iznos;
        # ranije su za raniju evidenciju obe kolone bile prazne.
        self.fuel()

        row = self.row()

        self.assertTrue(row['fuel'])
        for entry in row['fuel']:
            self.assertIn('cost_neto', entry)
            self.assertIn('price_per_liter', entry)
        first = row['fuel'][0]
        self.assertIsNotNone(first['cost_neto'])
        self.assertIsNotNone(first['price_per_liter'])

    def test_saved_assessment_does_not_copy_methodology(self):
        # Metodologija je vezana za version i cita se iz koda; ranije se cela
        # tabela upisivala u svaki snimak.
        assessment = SimpleNamespace(discount_percent=D('0'), years=5, as_of=self.start,
            annual_km=20000, annual_days=200, scope='Isti posao', assumptions='Izvor')
        scenario = SimpleNamespace(name='Zadržavanje', kind='keep', feasible=True,
            initial_cost=D('1000000'), annual_cost=D('300000'), residual_value=D('200000'),
            evidence='Procena')

        snapshot = compare_scenarios(assessment, [scenario])

        self.assertNotIn('methodology', snapshot)
        self.assertIn('version', snapshot)


class OrderJobCodePreservedTests(EconomicsFixture):
    """Suzavanje izbora po centru ne sme da obrise postojecu sifru posla."""

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user('centar01', password='t')
        self.user.allowed_center_codes = '01'
        self.user.save()
        self.tudji_posao = OrganizationalUnit.objects.create(code='P7', name='Tudji', center='02')

    def test_analysis_form_keeps_job_code_from_another_center(self):
        from fleet.forms.economics import OrderJobForm

        order = self.order(job_code=self.tudji_posao)
        form = OrderJobForm(instance=order, user=self.user)

        self.assertIn(self.tudji_posao, form.fields['job_code'].queryset)
        self.assertIn(self.unit, form.fields['job_code'].queryset)

        bound = OrderJobForm({'job_code': self.tudji_posao.pk}, instance=order, user=self.user)
        self.assertTrue(bound.is_valid(), bound.errors)
        bound.save()
        order.refresh_from_db()
        self.assertEqual(order.job_code, self.tudji_posao)

    def test_garage_form_keeps_job_code_from_another_center(self):
        from fleet.forms.garaza import VehicleTravelOrderForm

        order = self.order(job_code=self.tudji_posao)
        form = VehicleTravelOrderForm(instance=order, user=self.user)

        self.assertIn(self.tudji_posao, form.fields['job_code'].queryset)

    def test_form_without_instance_still_limits_to_own_centers(self):
        from fleet.forms.economics import OrderJobForm

        order = self.order(job_code=self.unit)
        form = OrderJobForm(instance=order, user=self.user)

        self.assertNotIn(self.tudji_posao, form.fields['job_code'].queryset)


class AnalysisSettingsLookupTests(EconomicsFixture):
    """Neispravan kljuc u adresi daje 404, ne gresku 500."""

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_superuser('admin-analitika', password='t')
        self.client.force_login(self.user)

    def test_non_numeric_ids_return_404(self):
        url = reverse('vehicle_analysis_settings', args=[self.car.pk])
        for parameter in ('downtime', 'charge', 'order'):
            with self.subTest(parameter=parameter):
                response = self.client.get(url, {parameter: 'abc'})
                self.assertEqual(response.status_code, 404)

    def test_valid_page_still_opens(self):
        response = self.client.get(reverse('vehicle_analysis_settings', args=[self.car.pk]))
        self.assertEqual(response.status_code, 200)


class EconomicScenarioTests(SimpleTestCase):
    def test_zero_discount_control_example_and_unfeasible_alternative(self):
        assessment = SimpleNamespace(years=5, discount_percent=D(0), annual_km=20000,
            annual_days=200, as_of=date(2026,1,1), scope='Isti posao', assumptions='Kontrolni primer')
        scenarios = [SimpleNamespace(name='Zadržavanje',kind='keep',initial_cost=D(1000000),annual_cost=D(300000),residual_value=D(200000),feasible=True,evidence='Procena'),
            SimpleNamespace(name='Najam',kind='lease',initial_cost=D(0),annual_cost=D(400000),residual_value=D(0),feasible=True,evidence='Ponuda'),
            SimpleNamespace(name='Nedostupno',kind='outsource',initial_cost=D(0),annual_cost=D(10),residual_value=D(0),feasible=False,evidence='Nema raspoloživosti')]
        result = compare_scenarios(assessment, scenarios)
        self.assertEqual(D(result['scenarios'][0]['present_cost']), 2300000)
        self.assertEqual(D(result['scenarios'][0]['annual_equivalent']), 460000)
        self.assertEqual(D(result['annual_saving']), 60000)
        self.assertIn('Najam', result['recommendation'])

    def test_positive_discount_and_end_of_year_residual(self):
        assessment = SimpleNamespace(years=1,discount_percent=D(10),annual_km=None,annual_days=None,
            as_of=date(2026,1,1),scope='Test',assumptions='Test')
        item = SimpleNamespace(name='Zadržavanje',kind='keep',initial_cost=D(1000),annual_cost=D(200),residual_value=D(100),feasible=True,evidence='Test')
        result = compare_scenarios(assessment, [item])
        self.assertAlmostEqual(D(result['scenarios'][0]['annual_equivalent']),D(1200),places=10)
        self.assertIsNone(result['annual_saving'])


class EconomicsViewsTests(EconomicsFixture):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_superuser('economic-admin', password='test')
        self.client.force_login(self.user)

    def test_fleet_and_vehicle_use_identical_costs_and_methodology(self):
        self.fuel()
        params = {'start':'2026-01-01','end':'2026-01-31'}
        fleet = self.client.get(reverse('fleet_analytics'), params)
        detail = self.client.get(reverse('vehicle_detail', args=[self.car.pk]), params)
        self.assertEqual(fleet.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(fleet.context['rows'][0]['total'], detail.context['economics']['total'])
        for response in [fleet, detail]:
            self.assertContains(response, 'Metodologija proračuna i kriterijumi')
            self.assertNotContains(response, 'Neisplativo')

    def test_filters_reject_bad_period_without_substituting_results(self):
        response = self.client.get(reverse('fleet_analytics'), {'start':'2026-02-01','end':'2026-01-01'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['period_valid'])
        self.assertEqual(response.context['rows'], [])

    def test_edit_and_scenario_pages_render(self):
        for name in ['vehicle_analysis_settings','vehicle_assessment_create']:
            response = self.client.get(reverse(name,args=[self.car.pk]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Metodologija')

    def test_center_analysis_uses_same_costs_and_historical_center(self):
        self.fuel()
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.unit, assigned_date=self.start)
        other = OrganizationalUnit.objects.create(code='NEW',name='Novi centar',center='02')
        JobCode.objects.create(vehicle=self.car, organizational_unit=other, assigned_date=date(2026,2,1))
        params={'start':'2026-01-01','end':'2026-01-31'}
        response=self.client.get(reverse('center_statistics',args=['01']),params)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.context['summary']['total'],D('3100'))
        self.assertEqual(self.client.get(reverse('center_statistics',args=['02']),params).context['summary']['count'],0)

    def test_filters_combine_purpose_and_holding(self):
        params={'start':'2026-01-01','end':'2026-01-31','purpose':'laboratory','basis':'owned'}
        self.assertEqual(self.client.get(reverse('fleet_analytics'),params).context['summary']['count'],1)
        params['basis']='operativni'
        self.assertEqual(self.client.get(reverse('fleet_analytics'),params).context['summary']['count'],0)

    def test_center_and_role_limits_cover_fleet_details_and_edit(self):
        JobCode.objects.create(vehicle=self.car,organizational_unit=self.unit,assigned_date=self.start)
        other = vehicle('2')
        unit = OrganizationalUnit.objects.create(code='X',name='Drugi',center='02')
        JobCode.objects.create(vehicle=other,organizational_unit=unit,assigned_date=self.start)
        self.user.is_superuser=False;self.user.save()
        self.user.allowed_center_codes='01';self.user.save()
        role = Role.objects.create(name='Test analitika',slug='test-analytics')
        # Kod dozvole je naziv rute; sync_permission_codes te kodove izvodi iz
        # vehicle_update / vehicle_detail — vidi test_new_fleet_routes_inherit_permissions.
        for code in ['fleet_analytics','vehicle_detail','vehicle_update',
                     'vehicle_analysis_settings','vehicle_assessment_create','vehicle_assessment_detail']:
            perm,_=PermissionCode.objects.get_or_create(code=code)
            RolePermission.objects.create(role=role,permission=perm)
        self.user.roles.add(role)
        self.assertEqual(list(visible_vehicles(self.user)),[self.car])
        for name in ['vehicle_detail','vehicle_analysis_settings','vehicle_assessment_create']:
            self.assertEqual(self.client.get(reverse(name,args=[other.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('fleet_analytics')).status_code,200)
        self.user.roles.clear()
        self.assertEqual(self.client.get(reverse('fleet_analytics')).status_code,403)

    def test_new_fleet_routes_inherit_permissions(self):
        """Uloga koja je smela da menja vozilo dobija i nove ekrane, bez rucne dodele."""
        from core.permissions import sync_permission_codes

        role = Role.objects.create(name='Samo vozila',slug='samo-vozila')
        for code in ['vehicle_update','vehicle_detail']:
            perm,_=PermissionCode.objects.get_or_create(code=code)
            RolePermission.objects.create(role=role,permission=perm)

        sync_permission_codes()

        granted = set(RolePermission.objects.filter(role=role).values_list('permission__code',flat=True))
        for code in ['vehicle_analysis_settings','vehicle_assessment_create',
                     'vehicle_assessment_detail','fleet_analytics','center_statistics']:
            self.assertIn(code, granted, msg=f'nedostaje dozvola {code}')

    def test_saved_assessment_preserves_inputs_and_comparison(self):
        data = {'as_of':'2026-01-01','title':'Kontrolna procena','years':'5','discount_percent':'0',
            'annual_km':'20000','annual_days':'200','scope':'Isti posao','assumptions':'Test izvor',
            'scenarios-TOTAL_FORMS':'2','scenarios-INITIAL_FORMS':'0','scenarios-MIN_NUM_FORMS':'0','scenarios-MAX_NUM_FORMS':'6'}
        for i, (kind,name,initial,annual,residual) in enumerate([('keep','Zadržavanje','1000000','300000','200000'),('lease','Najam','0','400000','0')]):
            for key,value in dict(kind=kind,name=name,initial_cost=initial,annual_cost=annual,residual_value=residual,feasible='on',evidence='Procena / ponuda').items():
                data[f'scenarios-{i}-{key}']=value
        response=self.client.post(reverse('vehicle_assessment_create',args=[self.car.pk]),data)
        self.assertEqual(response.status_code,302)
        assessment=VehicleEconomicAssessment.objects.get()
        self.assertEqual(assessment.scenarios.count(),2)
        self.assertEqual(D(assessment.snapshot['annual_saving']),60000)
        self.car.value=D(1);self.car.save()
        saved=self.client.get(response.url)
        self.assertEqual(saved.status_code,200)
        self.assertEqual(D(saved.context['snapshot']['annual_saving']),60000)

    def test_posting_job_of_other_vehicle_is_rejected(self):
        other=vehicle('2')
        order=self.order(vehicle=other)
        response=self.client.post(reverse('vehicle_analysis_settings',args=[self.car.pk]),
            {'action':'job','order_id':order.pk,'job-job_code':self.unit.pk})
        self.assertEqual(response.status_code,404)

    def test_profile_can_be_created_and_duplicate_shows_error(self):
        url=reverse('vehicle_analysis_settings',args=[self.car.pk])
        data={'action':'profile','profile-effective_from':'2026-02-01','profile-purpose':'supervision','profile-fuel_source':'legacy'}
        self.assertEqual(self.client.post(url,data).status_code,302)
        response=self.client.post(url,data)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Profil za ovaj datum već postoji')
