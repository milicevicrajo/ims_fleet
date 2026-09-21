from datetime import date, datetime, time
from decimal import Decimal as D

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from fleet.models import TransactionOMV, VehicleAnalysisProfile
from fleet.support.vehicle_consumption import vehicle_consumption
from fleet.support.vehicle_mileage import vehicle_mileage
from fleet.test_cost_fixes import fueling
from fleet.test_vehicle_onboarding import vehicle


class VehicleConsumptionTests(TestCase):
    def setUp(self):
        self.car = vehicle()
        self.today = date(2026, 3, 15)

    def fuel(self, day, km, liters, product='OMV Diesel', **extra):
        values = dict(vehicle=self.car, transaction_date=timezone.make_aware(datetime.combine(day,time(12))),
            mileage=km, quantity=liters, product_inv=product, license_plate_no='CONSUMPTION', card='1',
            invoice_no=day.isoformat(), voucher=day.isoformat(), gross_cc=100, vat=0)
        values.update(extra)
        return TransactionOMV.objects.create(**values)

    def result(self, start='2026-01-01', end='2026-01-31'):
        mileage = vehicle_mileage(self.car, {'mileage_from':start,'mileage_to':end}, today=self.today)
        return vehicle_consumption(self.car, mileage)

    def test_excludes_initial_fill_adblue_and_duplicate_omv_lines(self):
        self.fuel(date(2026,1,1),1000,60)
        self.fuel(date(2026,1,15),1500,30)
        self.fuel(date(2026,1,31),2000,40,voucher=None)
        self.fuel(date(2026,1,31),2000,40,voucher=None)  # NULL voucher bypasses SQL uniqueness.
        self.fuel(date(2026,1,31),2000,10,product='AdBlue')
        self.fuel(date(2026,1,31),2000,5,product='Pranje')
        result = self.result()
        self.assertEqual(result['liters'],70)
        self.assertEqual(result['rate'],7)
        self.assertEqual(result['adblue'],10)
        self.assertEqual(result['count'],2)

    def test_nearest_outside_dates_use_matching_liters_and_km(self):
        self.fuel(date(2025,12,31),1000,60)
        self.fuel(date(2026,1,15),1500,30)
        self.fuel(date(2026,2,1),2000,40)
        self.fuel(date(2026,2,15),2500,80)
        result = self.result()
        self.assertEqual(result['liters'],70)
        self.assertEqual(result['rate'],7)
        self.assertTrue(result['mileage']['approximate'])
        self.assertEqual(result['mileage']['coverage_end'],date(2026,2,1))

    def test_total_is_weighted_and_shared_boundary_fuel_is_counted_once(self):
        self.fuel(date(2026,1,1),1000,100)
        self.fuel(date(2026,1,31),2000,50)
        self.fuel(date(2026,3,2),5000,240)
        result = self.result(end='2026-03-02')
        self.assertEqual(result['rate'],D('7.25'))
        self.assertEqual(sum(p['liters'] for p in result['intervals']),290)
        self.assertEqual(sorted(p['rate'] for p in result['intervals']),[5,8])

    def test_selected_legacy_source_is_not_added_to_direct_source(self):
        VehicleAnalysisProfile.objects.create(vehicle=self.car,effective_from=date(2026,1,1),
            purpose='laboratory',fuel_source='legacy')
        for day,km in [(date(2026,1,1),1000),(date(2026,1,31),2000)]:
            self.fuel(day,km,80)
            record=fueling(self.car,day,km,amount='50')
            record.fuel_type='Diesel';record.save()
        self.assertEqual(self.result()['rate'],5)
        self.assertEqual(self.result()['count'],1)

    def test_profile_change_selects_one_source_per_date(self):
        VehicleAnalysisProfile.objects.create(vehicle=self.car,effective_from=date(2026,1,1),
            purpose='laboratory',fuel_source='legacy')
        VehicleAnalysisProfile.objects.create(vehicle=self.car,effective_from=date(2026,1,20),
            purpose='laboratory',fuel_source='transactions')
        for day,km in [(date(2026,1,1),1000),(date(2026,1,15),1500),(date(2026,1,31),2000)]:
            self.fuel(day,km,40)
            record=fueling(self.car,day,km,amount='30')
            record.fuel_type='Diesel';record.save()
        self.assertEqual(self.result()['liters'],70)

    def test_missing_or_negative_quantity_does_not_produce_partial_rate(self):
        self.fuel(date(2026,1,1),1000,60)
        last=self.fuel(date(2026,1,31),2000,None)
        self.assertIsNone(self.result()['rate'])
        last.quantity=-10;last.save()
        self.assertIsNone(self.result()['rate'])
        self.assertTrue(self.result()['incomplete'])

    def test_drop_or_zero_distance_blocks_consumption(self):
        self.fuel(date(2026,1,1),1000,60)
        last=self.fuel(date(2026,1,31),1000,40)
        self.assertIsNone(self.result()['rate'])
        last.mileage=900;last.save()
        self.assertIsNone(self.result()['rate'])
        self.assertEqual(self.result()['mileage']['issue_count'],1)

    def test_no_fuel_or_invalid_filter_is_not_zero_consumption(self):
        self.assertIsNone(self.result()['rate'])
        self.fuel(date(2026,1,1),1000,60)
        self.fuel(date(2026,1,31),2000,10,product='AdBlue')
        self.assertIsNone(self.result()['rate'])
        result=self.result(start='bad')
        self.assertFalse(result['mileage']['valid'])
        self.assertEqual(result['rows'],[])
        self.assertIsNone(result['rate'])

    def test_detail_replaces_mileage_tab_and_renders_consumption(self):
        self.fuel(date(2026,1,1),1000,60)
        self.fuel(date(2026,1,31),2000,70)
        self.client.force_login(get_user_model().objects.create_superuser('consumption-admin',password='test'))
        response=self.client.get(reverse('vehicle_detail',args=[self.car.pk]),
            {'mileage_from':'2026-01-01','mileage_to':'2026-01-31'})
        self.assertContains(response,'>Potrošnja goriva</button>')
        self.assertNotContains(response,'>Kilometraža</button>')
        self.assertContains(response,'7,00 l/100 km')
        self.assertContains(response,'vehicleConsumptionPeriods')
        self.assertContains(response,'Usvojena očitavanja')
