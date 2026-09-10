import datetime as dt
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from fleet.models import Policy, Lease
from fleet.test_vehicle_onboarding import vehicle, card
from fleet.support.vehicle_detail import VehiclePeriodForm, recorded_analytics


class RecordedVehicleAnalyticsTests(SimpleTestCase):
    start = dt.date(2026, 1, 1)
    end = dt.date(2026, 3, 31)

    def test_inclusive_period_reconciles_months_categories_and_signed_amounts(self):
        services = [SimpleNamespace(datum=self.start, potrazuje=Decimal('120'), popravka_kategorija='Delovi'),
                    SimpleNamespace(datum=self.end, potrazuje=Decimal('-20'), popravka_kategorija='Delovi'),
                    SimpleNamespace(datum=dt.date(2025,12,31), potrazuje=Decimal('999'), popravka_kategorija='Van')]
        reqs = [SimpleNamespace(datum_trebovanja=self.end, vrednost_nab=Decimal('50'), popravka_kategorija=None)]
        recoveries = [SimpleNamespace(datum=self.end, potrazuje=Decimal('200'))]
        result = recorded_analytics([], services, reqs, recoveries, self.start, self.end)
        self.assertEqual(result['maintenance'], Decimal('150'))
        self.assertEqual(result['net_maintenance'], Decimal('-50'))
        self.assertEqual(sum(r['maintenance'] for r in result['monthly']), result['maintenance'])
        self.assertEqual(sum(r['amount'] for r in result['categories']), result['maintenance'])
        self.assertEqual(len(result['monthly']), 3)
        self.assertIsNone(result['monthly'][1]['service'])
        self.assertEqual(result['counts']['service'], 2)

    def test_missing_amount_is_not_a_recorded_zero(self):
        rows = [SimpleNamespace(datum=self.start, potrazuje=None), SimpleNamespace(datum=self.end, potrazuje=Decimal('0'))]
        result = recorded_analytics([], [], [], rows, self.start, self.end)
        self.assertIsNone(result['monthly'][0]['recovery'])
        self.assertEqual(result['monthly'][2]['recovery'], 0)
        self.assertEqual(result['counts']['recovery'], 1)

    def test_odometer_coverage_is_observed_not_extrapolated(self):
        fuel = [{'date':dt.date(2026,1,15), 'mileage':1000, 'cost_bruto':Decimal('100')},
                {'date':dt.date(2026,3,15), 'mileage':1600, 'cost_bruto':Decimal('200')}]
        result = recorded_analytics(fuel, [], [], [], self.start, self.end)
        self.assertEqual(result['mileage']['km'], 600)
        self.assertEqual(result['mileage']['start'], dt.date(2026,1,15))
        fuel.append({'date':dt.date(2026,2,15), 'mileage':500, 'cost_bruto':0})
        result = recorded_analytics(fuel, [], [], [], self.start, self.end)
        self.assertIsNone(result['mileage'])
        self.assertTrue(result['mileage_issue'])

    def test_bad_filters_rejected(self):
        for data in [{'start':'bad','end':'2026-01-01'}, {'start':'2026-03-01','end':'2026-01-01'},
                     {'start':'2020-01-01','end':'2026-01-01'}, {'start':'2026-01-01','end':'2099-01-01'}]:
            self.assertFalse(VehiclePeriodForm(data).is_valid())


class VehicleDetailTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(username='detail', password='test')
        self.client.force_login(self.user)
        self.vehicle = vehicle()
        self.url = reverse('vehicle_detail', args=[self.vehicle.pk])

    def test_empty_vehicle_renders_without_invented_values(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rok nije evidentiran')
        self.assertEqual(response.context['holding_label'], 'Vlasništvo IMS')
        self.assertNotContains(response, 'Neisplativo')
        self.assertNotContains(response, 'Proračun isplativosti')
        self.assertIsNone(response.context['analytics']['mileage'])

    def test_invalid_filter_has_no_silent_default_results(self):
        response = self.client.get(self.url, {'start':'2026-03-01','end':'2026-01-01'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['period_valid'])
        self.assertIsNone(response.context['analytics'])
        self.assertContains(response, 'Ispravite period')

    @patch('django.utils.timezone.localdate', return_value=dt.date(2026,3,1))
    def test_default_is_twelve_calendar_months_and_future_policy_not_active(self, _):
        for number,start,end in [(1,dt.date(2026,1,1),dt.date(2026,5,1)),(2,dt.date(2026,4,1),dt.date(2027,4,1))]:
            Policy.objects.create(vehicle=self.vehicle, invoice_id=number, start_date=start, end_date=end)
        response = self.client.get(self.url)
        self.assertEqual(response.context['period_start'], dt.date(2025,4,1))
        self.assertEqual(len(response.context['analytics']['monthly']), 12)
        self.assertEqual(response.context['active_policies'].count(), 1)
        self.assertEqual(response.context['policies'].count(), 2)

    def test_document_expiry_does_not_become_registration_expiry(self):
        document = card(self.vehicle)
        document.valid_until = dt.date(2030,1,1)
        document.save()
        response = self.client.get(self.url)
        self.assertIsNone(response.context['registration_days'])
        self.assertContains(response, 'Rok nije evidentiran')

    def test_ao_fallback_has_explicit_source_and_ignores_casco(self):
        today = dt.date.today()
        ao = Policy.objects.create(vehicle=self.vehicle, invoice_id=1, insurance_type='POLISA AUTOODGOVORNOSTI ', start_date=today, end_date=today+dt.timedelta(days=300))
        Policy.objects.create(vehicle=self.vehicle, invoice_id=2, insurance_type='POLISA AUTOKASKA ', start_date=today, end_date=today+dt.timedelta(days=400))
        response = self.client.get(self.url)
        self.assertEqual(response.context['ao_policy'], ao)
        self.assertIsNone(response.context['registration_days'])
        self.assertContains(response, 'Rok iz polise autoodgovornosti')

    def test_legacy_active_lease_takes_precedence_over_default_ownership(self):
        today = dt.date.today()
        lease = Lease.objects.create(vehicle=self.vehicle, contract_number='L1', current_payment_amount=100, start_date=today, end_date=today+dt.timedelta(days=300))
        response = self.client.get(self.url)
        self.assertEqual(response.context['holding_lease'], lease)
        self.assertEqual(response.context['holding_label'], 'Ugovorno raspolaganje')
        Lease.objects.filter(pk=lease.pk).update(start_date=today-dt.timedelta(days=300), end_date=today-dt.timedelta(days=1))
        self.assertEqual(self.client.get(self.url).context['holding_label'], 'Vlasništvo IMS')

    def test_only_previous_documents_appear_in_optional_history(self):
        first = card(self.vehicle)
        response = self.client.get(self.url)
        self.assertNotContains(response, 'id="previous-traffic-cards"')
        latest = card(self.vehicle, number='2', issued=dt.date(2022,1,1))
        response = self.client.get(self.url)
        self.assertEqual(response.context['latest_traffic_card'], latest)
        self.assertEqual(list(response.context['previous_traffic_cards']), [first])
        self.assertContains(response, 'id="previous-traffic-cards"')
