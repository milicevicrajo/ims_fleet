import datetime as dt
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import OrganizationalUnit
from hr.models import Employee
from fleet.models import JobCode, Policy, VehicleTravelOrder
from fleet.test_vehicle_onboarding import vehicle, card
from fleet.support.fleet_snapshot import fleet_snapshot


class FleetSnapshotTests(TestCase):
    today = dt.date(2026, 9, 10)

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='snapshot', password='test')
        self.a = OrganizationalUnit.objects.create(code='A1', name='Prvi', center='01')
        self.b = OrganizationalUnit.objects.create(code='B1', name='Drugi', center='02')

    def test_centers_use_current_assignment_and_reconcile_with_active_fleet(self):
        first, second, archived = vehicle(), vehicle('2'), vehicle('3')
        JobCode.objects.create(vehicle=first, organizational_unit=self.a, assigned_date=dt.date(2026,1,1))
        JobCode.objects.create(vehicle=first, organizational_unit=self.b, assigned_date=dt.date(2027,1,1))
        second.category='prikljucno'; second.save()
        archived.otpis=True; archived.save()
        s=fleet_snapshot(self.user,self.today)
        self.assertEqual({c['code']:c['count'] for c in s['centers']},{'01':1,None:1})
        self.assertEqual(s['totals']['count'],2)
        self.assertEqual(sum(c['count'] for c in s['centers']),2)
        self.assertEqual(s['totals']['trailer'],1)
        self.assertEqual(s['archived_count'],1)

    def test_restricted_centers_hide_other_vehicles_and_their_warnings(self):
        first, second = vehicle(), vehicle('2')
        for car,unit in [(first,self.a),(second,self.b)]:JobCode.objects.create(vehicle=car,organizational_unit=unit,assigned_date=dt.date(2020,1,1))
        self.user.allowed_centers.add(self.a)
        s=fleet_snapshot(self.user,self.today)
        self.assertEqual([v.pk for v in s['vehicles']],[first.pk])
        self.assertEqual(s['totals']['count'],1)
        self.assertNotIn(second.chassis_number,str(s['warning_groups']))

    def test_missing_values_and_invalid_years_do_not_become_zero_observations(self):
        first, second = vehicle(), vehicle('2')
        first.value=Decimal('0');first.save()
        second.year_of_manufacture=2099;second.save()
        s=fleet_snapshot(self.user,self.today)
        self.assertEqual(s['totals']['book_value'],0)
        self.assertEqual(s['totals']['value_known'],1)
        self.assertEqual(s['totals']['age_known'],1)
        self.assertEqual(s['totals']['age'],6)

    def test_ao_is_current_and_registration_uses_latest_document(self):
        car=vehicle();old=card(car)
        old.registration_valid_until=dt.date(2028,1,1);old.save()
        card(car,number='2',issued=dt.date(2022,1,1))
        Policy.objects.create(vehicle=car,invoice_id=1,insurance_type='POLISA AUTOKASKA',start_date=dt.date(2026,1,1),end_date=dt.date(2027,1,1))
        Policy.objects.create(vehicle=car,invoice_id=2,insurance_type='POLISA AUTOODGOVORNOSTI',start_date=dt.date(2026,10,1),end_date=dt.date(2027,10,1))
        s=fleet_snapshot(self.user,self.today)
        self.assertEqual(s['totals']['ao'],0)
        self.assertIsNone(s['vehicles'][0].registration_until)

    def test_continuous_policy_extension_suppresses_expiry_warning(self):
        car=vehicle()
        Policy.objects.create(vehicle=car,invoice_id=1,insurance_type='POLISA AUTOODGOVORNOSTI ',start_date=dt.date(2026,1,1),end_date=dt.date(2026,9,20))
        extension=Policy.objects.create(vehicle=car,invoice_id=2,insurance_type='POLISA AUTOODGOVORNOSTI',start_date=dt.date(2026,9,21),end_date=dt.date(2027,9,20))
        s=fleet_snapshot(self.user,self.today)
        self.assertEqual(s['totals']['ao'],1)
        self.assertFalse(any('nastavka' in group['title'] for group in s['warning_groups']))
        extension.start_date=dt.date(2026,9,25);extension.save()
        self.assertTrue(any('nastavka' in group['title'] for group in fleet_snapshot(self.user,self.today)['warning_groups']))

    def test_duplicate_assignments_count_one_vehicle_and_dashboard_renders(self):
        car=vehicle()
        employee=Employee.objects.create(employee_code=1,first_name='Test',last_name='Vozac',position='Vozac',department_code=1,gender='M',date_of_birth=dt.date(1990,1,1),date_of_joining=dt.date(2020,1,1))
        for _ in range(2):VehicleTravelOrder.objects.create(vehicle=car,employee=employee,created_at=dt.date(2026,1,1))
        s=fleet_snapshot(self.user,self.today)
        self.assertEqual(s['totals']['assigned'],1)
        self.assertEqual(s['open_order_count'],2)
        self.assertTrue(any('istovremenih' in g['title'] for g in s['warning_groups']))
        self.client.force_login(self.user)
        response=self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,'Crvenoj')
        self.assertContains(response,'Raspored po centrima')
