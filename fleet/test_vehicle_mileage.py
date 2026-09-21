from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from fleet.models import FuelConsumption, TransactionOMV, VehicleTravelOrder
from fleet.support.vehicle_mileage import observed_timeline, vehicle_mileage, nearest_period
from fleet.test_vehicle_onboarding import vehicle
from hr.models import Employee


def reading(day,km,source='NIS'):
    return {'date':date.fromisoformat(day),'value':Decimal(km),'source':source,'reference':'','url':None}


class MileageTimelineTests(SimpleTestCase):
    def test_nearest_dates_can_be_outside_period_and_ties_extend_outward(self):
        result=nearest_period([reading('2025-12-31','100'),reading('2026-01-02','150'),
            reading('2026-01-30','200'),reading('2026-02-01','250')],date(2026,1,1),date(2026,1,31))
        self.assertEqual(result['total_km'],150)
        self.assertEqual(result['adopted_start']['date'],date(2025,12,31))
        self.assertEqual(result['adopted_end']['date'],date(2026,2,1))
        self.assertEqual((result['start_offset'],result['end_offset']),(-1,1))
        self.assertTrue(result['approximate'])

    def test_same_nearest_reading_and_single_requested_day_do_not_invent_distance(self):
        readings=[reading('2026-01-01','100'),reading('2026-03-01','200')]
        result=nearest_period(readings,date(2026,1,5),date(2026,1,10))
        self.assertIsNone(result['total_km'])
        result=nearest_period(readings,date(2026,1,15),date(2026,1,15))
        self.assertIsNone(result['total_km'])
        self.assertIsNone(nearest_period([],date(2026,1,1),date(2026,1,31))['total_km'])

    def test_nearest_monthly_boundaries_are_actual_dates_and_do_not_double_count(self):
        result=observed_timeline([reading('2026-01-01','1000'),reading('2026-01-29','1300'),reading('2026-02-02','1400'),reading('2026-03-01','2000')])
        periods=list(reversed(result['intervals']))
        self.assertEqual([(p['start'],p['end']) for p in periods],[(date(2026,1,1),date(2026,1,29)),(date(2026,1,29),date(2026,3,1))])
        self.assertEqual([p['km'] for p in periods],[300,700])
        self.assertEqual(result['total_km'],1000)

    def test_sparse_readings_do_not_create_fake_months(self):
        result=observed_timeline([reading('2026-01-01','1000'),reading('2026-04-20','2000')])
        self.assertEqual(len(result['intervals']),1)
        self.assertEqual(result['intervals'][0]['days'],109)
        self.assertEqual(result['intervals'][0]['km'],1000)

    def test_internal_drop_blocks_positive_endpoint_difference(self):
        result=observed_timeline([reading('2026-01-01','1000'),reading('2026-01-10','900'),reading('2026-01-30','1200')])
        self.assertIsNone(result['intervals'][0]['km'])
        self.assertIsNone(result['total_km'])
        self.assertEqual(result['issue_count'],1)

    def test_multiple_same_day_readings_use_daily_maximum(self):
        result=observed_timeline([reading('2026-01-01','100'),reading('2026-01-01','150','Nalog'),reading('2026-01-01','150'),reading('2026-02-01','200')])
        self.assertEqual(result['intervals'][0]['km'],50)
        self.assertEqual(len(result['days']),2)
        self.assertIn('Nalog',result['intervals'][0]['start_source'])

    def test_current_reading_is_latest_not_lifetime_maximum(self):
        result=observed_timeline([reading('2026-01-01','1500'),reading('2026-02-01','900')])
        self.assertEqual(result['current']['value'],900)
        self.assertTrue(result['current']['needs_check'])

    def test_empty_and_single_day_have_no_invented_distance(self):
        self.assertIsNone(observed_timeline([])['current'])
        result=observed_timeline([reading('2026-01-01','0')])
        self.assertEqual(result['current']['value'],0)
        self.assertEqual(result['intervals'],[])
        self.assertIsNone(result['total_km'])


class VehicleMileageTests(TestCase):
    def setUp(self):
        self.car=vehicle()
        self.user=get_user_model().objects.create_superuser('mileage-admin',password='test')
        self.employee=Employee.objects.create(employee_code=99,first_name='Test',last_name='Vozac',position='Vozac',department_code=1,gender='M',date_of_birth=date(1990,1,1),date_of_joining=date(2020,1,1))
        self.order=VehicleTravelOrder.objects.create(vehicle=self.car,employee=self.employee,created_at=date(2026,1,1),closed_at=date(2026,2,1),start_mileage=0,end_mileage=200)
        TransactionOMV.objects.create(vehicle=self.car,issuer='Test',customer='Test',card='1',license_plate_no='BG1',transaction_date=timezone.make_aware(datetime(2026,1,15,12)),mileage=0,corrected_mileage=100)

    def test_sources_include_zero_start_corrected_fuel_and_real_close_date(self):
        data=vehicle_mileage(self.car,today=date(2026,2,1))
        self.assertEqual([r['value'] for r in data['readings']],[200,100,0])
        self.assertEqual(data['total_km'],200)
        self.assertEqual(data['current']['date'],date(2026,2,1))
        self.assertIn('korigovano',data['readings'][1]['source'])
        self.assertEqual(data['readings'][1]['original_value'], 0)
        self.order.closed_at=None;self.order.save()
        data=vehicle_mileage(self.car,today=date(2026,2,1))
        self.assertEqual(data['current']['value'],100)
        self.assertEqual(data['excluded'],1)

    def test_legacy_fuel_only_fills_days_without_direct_readings(self):
        for day,mileage in [(date(2026,1,15),90),(date(2026,1,20),150)]:
            FuelConsumption.objects.create(vehicle=self.car,date=timezone.make_aware(datetime.combine(day,datetime.min.time())),amount=10,fuel_type='Diesel',cost_bruto=1,cost_neto=1,supplier='OMV',mileage=mileage)
        data=vehicle_mileage(self.car,today=date(2026,2,1))
        self.assertNotIn(90,[r['value'] for r in data['readings']])
        self.assertIn(150,[r['value'] for r in data['readings']])

    def test_filter_keeps_latest_state_separate_and_rejects_invalid_range(self):
        data=vehicle_mileage(self.car,{'mileage_from':'2026-01-01','mileage_to':'2026-01-15'},today=date(2026,2,1))
        self.assertEqual(data['current']['value'],200)
        self.assertEqual(data['total_km'],100)
        data=vehicle_mileage(self.car,{'mileage_from':'2026-02-01','mileage_to':'2026-01-01'},today=date(2026,2,1))
        self.assertFalse(data['valid']);self.assertEqual(data['intervals'],[])

    def test_filter_adopts_nearest_order_and_fuel_readings_with_visible_evidence(self):
        params={'mileage_from':'2026-01-03','mileage_to':'2026-01-14'}
        data=vehicle_mileage(self.car,params,today=date(2026,2,1))
        self.assertEqual(data['total_km'],100)
        self.assertEqual(data['coverage_start'],date(2026,1,1))
        self.assertEqual(data['coverage_end'],date(2026,1,15))
        self.assertEqual(data['current']['value'],200)
        self.client.force_login(self.user)
        response=self.client.get(reverse('vehicle_detail',args=[self.car.pk]),params)
        self.assertContains(response,'Usvojena očitavanja')
        self.assertContains(response,'odstupanje -2 dana')
        self.assertContains(response,'približan period')

    def test_detail_renders_tab_even_when_cost_filter_is_invalid(self):
        self.client.force_login(self.user)
        response=self.client.get(reverse('vehicle_detail',args=[self.car.pk]),{'start':'bad','end':'bad'})
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'id="mileage-tab"')
        self.assertEqual(response.context['mileage']['current']['value'],200)

    def test_serbian_decimal_comma_preserves_fractional_distance_and_numeric_sort(self):
        from django.template.loader import render_to_string
        from django.utils.translation import override
        readings = [reading('2026-01-01','186900'), reading('2026-02-01','188682')]
        result = observed_timeline(readings)
        result.update(readings=readings)
        with override('sr-latn'):
            html = render_to_string('fleet/_vehicle_mileage.html', {'mileage':result, 'vehicle':self.car})
        self.assertIn('186.900,00', html)
        self.assertIn('188.682,00', html)
        self.assertIn('1.782,00', html)
        self.assertIn('data-order="1782"', html)
        self.assertNotIn('očitanje', html)
        self.assertNotIn('očitanja', html)
        result = observed_timeline([reading('2026-01-01','100.25'),reading('2026-02-01','101.75')])
        self.assertEqual(result['total_km'], Decimal('1.50'))
