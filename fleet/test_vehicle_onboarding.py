import datetime
import importlib
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import OrganizationalUnit
from hr.models import Employee
from ugovori.models import Contract, ContractType
from .models import Vehicle, TrafficCard, VehicleHolding, Lease, JobCode
from .forms.vehicles import TrafficCardForm
from .forms.onboarding import VehicleTechnicalForm, VehicleBasisForm
from .forms.onboarding import VehicleIdentityForm
from .support.analytics import fixed_cost_per_km_threshold, cost_per_km_status


def vehicle(suffix='1'):
    return Vehicle.objects.create(chassis_number=f'WVWZZZTEST000{suffix}', brand='VW', model='Test', year_of_manufacture=2020, category='putnicko')


def sample_photo():
    from PIL import Image
    data = BytesIO()
    Image.new('RGB', (30, 20), 'gray').save(data, format='PNG')
    return SimpleUploadedFile('vehicle.png', data.getvalue(), content_type='image/png')


def card(car, number='1', plate='BG123-AA', issued=datetime.date(2020, 1, 1)):
    return TrafficCard.objects.create(vehicle=car, registration_number=plate, issue_date=issued, traffic_card_number=number, serial_number=number, owner='IMS')


class TrafficCardHistoryTests(TestCase):
    def test_same_plate_multiple_documents_resolves_one_vehicle(self):
        car = vehicle()
        old = card(car)
        latest = card(car, '2', issued=datetime.date(2022, 1, 1))
        self.assertEqual(TrafficCard.objects.for_plate('BG 123 AA').pk, latest.pk)
        self.assertEqual(car.traffic_cards.first(), latest)
        self.assertEqual(TrafficCard.objects.plate_vehicle_map(lambda x: x), {'BG123-AA': car.pk})
        self.assertTrue(TrafficCard.objects.filter(pk=old.pk).exists())

    def test_old_plate_still_resolves_after_plate_change(self):
        car = vehicle()
        card(car)
        card(car, '2', 'BG456-BB', datetime.date(2022, 1, 1))
        self.assertEqual(TrafficCard.objects.for_plate('BG123-AA').vehicle, car)
        self.assertTrue(str(car).startswith('BG456-BB'))

    def test_same_plate_cannot_be_assigned_to_another_vehicle(self):
        card(vehicle())
        with self.assertRaises(ValidationError):
            card(vehicle('2'))

    def test_ambiguous_legacy_plate_fails_closed(self):
        card(vehicle())
        other = card(vehicle('2'), plate='BG456-BB')
        TrafficCard.objects.filter(pk=other.pk).update(registration_number='BG123-AA')
        with self.assertRaises(TrafficCard.MultipleObjectsReturned):
            TrafficCard.objects.for_plate('BG123-AA')
        self.assertNotIn('BG123-AA', TrafficCard.objects.plate_vehicle_map(lambda x: x))

    def test_form_allows_replacement_and_document_without_expiry(self):
        car = vehicle()
        card(car)
        form = TrafficCardForm(data={'vehicle': car.pk, 'registration_number': 'BG123-AA', 'issue_date': '01.01.2022', 'traffic_card_number': '2', 'serial_number': '2', 'owner': 'IMS'})
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(car.traffic_cards.count(), 2)

    def test_future_issue_date_is_rejected(self):
        with self.assertRaises(ValidationError):
            card(vehicle(), issued=datetime.date.today() + datetime.timedelta(days=2))


class VehicleHoldingTests(TestCase):
    def test_overlap_requires_closing_previous_period(self):
        car = vehicle()
        holding = VehicleHolding.objects.create(vehicle=car, basis='owned', start_date=datetime.date(2020, 1, 1))
        with self.assertRaises(ValidationError):
            VehicleHolding.objects.create(vehicle=car, basis='owned', start_date=datetime.date(2022, 1, 1))
        holding.end_date = datetime.date(2021, 12, 31)
        holding.save()
        VehicleHolding.objects.create(vehicle=car, basis='owned', start_date=datetime.date(2022, 1, 1))
        self.assertEqual(car.holdings.count(), 2)

    def test_contract_must_belong_to_same_vehicle(self):
        car, other = vehicle(), vehicle('2')
        lease = Lease.objects.create(vehicle=other, partner_code='1', partner_name='Test', contract_number='1', current_payment_amount=100, start_date=datetime.date(2020, 1, 1), end_date=datetime.date(2022, 1, 1))
        with self.assertRaises(ValidationError):
            VehicleHolding.objects.create(vehicle=car, basis='contract', lease=lease, start_date=lease.start_date, end_date=lease.end_date)

    def test_migration_copies_only_unambiguous_information(self):
        car, conflicted, owned_unknown = vehicle(), vehicle('2'), vehicle('3')
        first = card(car)
        TrafficCard.objects.filter(pk=first.pk).update(homologation_number='HOM-A')
        a, b = card(conflicted, plate='BG456-BB'), card(conflicted, '2', 'BG456-BB')
        TrafficCard.objects.filter(pk=a.pk).update(homologation_number='HOM-B')
        TrafficCard.objects.filter(pk=b.pk).update(homologation_number='HOM-C')
        Lease.objects.create(vehicle=car, partner_code='1', partner_name='Test', contract_number='1', current_payment_amount=100, start_date=datetime.date(2020, 1, 1), end_date=datetime.date(2022, 1, 1))
        migration = importlib.import_module('fleet.migrations.0074_vehicle_onboarding_data')
        migration.copy_unambiguous_data(apps, SimpleNamespace(connection=connection))
        car.refresh_from_db()
        conflicted.refresh_from_db()
        self.assertEqual(car.homologation_number, 'HOM-A')
        self.assertEqual(conflicted.homologation_number, '')
        self.assertEqual(car.holdings.count(), 1)
        self.assertFalse(owned_unknown.holdings.exists())


class VehicleWizardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(username='wizard', password='test-password', email='wizard@example.test')
        self.client.force_login(self.user)
        self.media = tempfile.TemporaryDirectory()
        self.uploads = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(self.media.cleanup)
        self.addCleanup(self.uploads.cleanup)
        self.storage_patch = patch('fleet.views.vehicle_onboarding.STORAGE', FileSystemStorage(location=self.uploads.name))
        self.storage_patch.start()
        self.addCleanup(self.storage_patch.stop)

    def start(self):
        response = self.client.get(reverse('vehicle_create'))
        self.assertEqual(response.status_code, 302)
        self.token = response.url.split('draft=')[1]
        page = self.client.get(response.url)
        self.assertEqual(page.status_code, 200)

    def step(self, index, data):
        return self.client.post(reverse('vehicle_create'), {'draft_token': self.token, 'step': index, 'action': 'next', **data})

    def prepare(self, category='putnicko', basis=None, document=None, assignment=None, photo=None):
        self.start()
        steps = [
            {'category': category, 'chassis_number': 'WVWZZZTEST000001', 'brand': 'VW', 'model': 'Test', 'year_of_manufacture': '2020'},
            basis or {'basis': 'owned', 'start_date': '01.01.2020', 'financing': 'own_funds'},
            {'color': 'Bela', 'service_interval': '15000'},
            document or {},
            assignment or {},
        ]
        if photo:
            steps[0]['photo'] = photo
        for index, data in enumerate(steps):
            response = self.step(index, data)
            self.assertEqual(response.status_code, 302, getattr(response, 'context', None) and response.context['form'].errors)
        self.assertEqual(Vehicle.objects.count(), 0)
        summary = self.client.get(f'{reverse("vehicle_create")}?draft={self.token}')
        self.assertEqual(summary.status_code, 200)
        self.assertContains(summary, 'Sačuvaj vozilo')

    def test_complete_owned_without_document_and_repeated_submit(self):
        self.prepare()
        result = self.step(5, {})
        self.assertEqual(result.status_code, 302)
        car = Vehicle.objects.get()
        self.assertIsNone(car.inventory_number)
        self.assertIsNone(car.purchase_value)
        self.assertEqual(car.color, 'Bela')
        self.assertEqual(car.holdings.get().basis, 'owned')
        self.assertFalse(car.traffic_cards.exists())
        self.assertEqual(self.step(5, {}).url, result.url)
        self.assertEqual(Vehicle.objects.count(), 1)
        detail = self.client.get(result.url)
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, 'Vlasništvo IMS')

    def test_trailer_does_not_require_motor(self):
        self.prepare(category='prikljucno')
        self.assertEqual(self.step(5, {}).status_code, 302)
        car = Vehicle.objects.get()
        self.assertIsNone(car.engine_number)
        self.assertIsNone(car.engine_volume)

    def test_rental_creates_lease_and_period_without_purchase_value(self):
        self.prepare(basis={'basis': 'contract', 'start_date': '01.01.2020', 'end_date': '31.12.2026', 'partner_code': '10', 'partner_name': 'Najmodavac', 'lease_type': 'dugorocni', 'contract_number': 'UG-1', 'current_payment_amount': '10000'})
        self.assertEqual(self.step(5, {}).status_code, 302)
        holding = VehicleHolding.objects.get()
        self.assertEqual(holding.lease.contract_number, 'UG-1')
        self.assertIsNone(holding.vehicle.purchase_value)
        self.assertEqual(holding.financing, '')

    def test_upload_survives_steps_and_is_cleaned_after_commit(self):
        self.prepare(document={'add_document': 'on', 'registration_number': 'BG123-AA', 'issue_date': '01.01.2020', 'traffic_card_number': '1', 'serial_number': '1', 'owner': 'IMS', 'traffic_card_pdf': SimpleUploadedFile('card.pdf', b'%PDF-1.4 test', content_type='application/pdf')})
        self.assertEqual(self.step(5, {}).status_code, 302)
        doc = TrafficCard.objects.get()
        with doc.traffic_card_pdf.open('rb') as file:
            self.assertEqual(file.read(), b'%PDF-1.4 test')
        self.assertFalse(any(p.is_file() for p in Path(self.uploads.name).rglob('*')))

    def test_late_failure_rolls_back_all_records_and_final_files(self):
        unit = OrganizationalUnit.objects.create(code='100', name='Test', center='1')
        self.prepare(photo=sample_photo(), document={'add_document': 'on', 'registration_number': 'BG123-AA', 'issue_date': '01.01.2020', 'traffic_card_number': '1', 'serial_number': '1', 'owner': 'IMS', 'traffic_card_pdf': SimpleUploadedFile('card.pdf', b'%PDF-1.4 test')}, assignment={'organizational_unit': unit.pk, 'assigned_date': '01.01.2020'})
        with patch('fleet.services.vehicle_onboarding.JobCode.objects.create', side_effect=ValidationError('Test prekida')):
            response = self.step(5, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vehicle.objects.count(), 0)
        self.assertEqual(VehicleHolding.objects.count(), 0)
        self.assertEqual(TrafficCard.objects.count(), 0)
        self.assertFalse(any(p.is_file() for p in Path(self.media.name).rglob('*')))
        self.assertEqual(self.step(5, {}).status_code, 302)

    def test_photo_survives_skipping_document_and_return_to_identity(self):
        self.prepare(photo=sample_photo())
        response = self.client.post(reverse('vehicle_create'), {'draft_token': self.token, 'action': 'edit:0'})
        self.assertContains(response, 'vehicle.png')
        data = {key: values[0] for key, values in self.client.session['vehicle_onboarding'][self.token]['steps']['0'].items() if values}
        self.assertEqual(self.step(0, data).status_code, 302)
        for index in range(1, 5):
            data = {key: values[0] for key, values in self.client.session['vehicle_onboarding'][self.token]['steps'][str(index)].items() if values}
            self.assertEqual(self.step(index, data).status_code, 302)
        response = self.step(5, {})
        car = Vehicle.objects.get()
        with car.photo.open('rb') as file:
            self.assertEqual(file.read(), sample_photo().read())
        self.assertContains(self.client.get(response.url), 'class="vd-vehicle-photo"')
        self.assertFalse(any(p.is_file() for p in Path(self.uploads.name).rglob('*')))

    def test_photo_can_be_removed_without_losing_traffic_card_upload(self):
        self.prepare(photo=sample_photo(), document={'add_document': 'on', 'registration_number': 'BG123-AA', 'issue_date': '01.01.2020', 'traffic_card_number': '1', 'serial_number': '1', 'owner': 'IMS', 'traffic_card_pdf': SimpleUploadedFile('card.pdf', b'%PDF-1.4 test')})
        self.client.post(reverse('vehicle_create'), {'draft_token': self.token, 'action': 'edit:0'})
        data = {key: values[0] for key, values in self.client.session['vehicle_onboarding'][self.token]['steps']['0'].items() if values}
        self.assertEqual(self.step(0, {**data, 'remove_photo': 'on'}).status_code, 302)
        draft = self.client.session['vehicle_onboarding'][self.token]
        self.assertNotIn('photo', draft['files'])
        self.assertIn('traffic_card_pdf', draft['files'])

    def test_photo_validation_rejects_non_image_and_oversized_image(self):
        data = {'category': 'putnicko', 'chassis_number': 'WVWZZZTEST000001', 'brand': 'VW', 'model': 'Test', 'year_of_manufacture': '2020'}
        for file in [SimpleUploadedFile('bad.png', b'not an image'), SimpleUploadedFile('large.png', sample_photo().read() + b'0' * (5 * 1024 * 1024))]:
            form = VehicleIdentityForm(data=data, files={'photo': file})
            self.assertFalse(form.is_valid())
            self.assertIn('photo', form.errors)

    def test_cancel_discards_uncommitted_vehicle(self):
        self.prepare()
        response = self.client.post(reverse('vehicle_create'), {'draft_token': self.token, 'action': 'cancel'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Vehicle.objects.exists())
        self.assertNotIn(self.token, self.client.session['vehicle_onboarding'])

    def test_document_step_initially_offers_document_entry(self):
        self.start()
        self.step(0, {'category': 'putnicko', 'chassis_number': 'WVWZZZTEST000001', 'brand': 'VW', 'model': 'Test', 'year_of_manufacture': '2020'})
        self.step(1, {'basis': 'owned', 'start_date': '01.01.2020', 'financing': 'own_funds'})
        self.step(2, {'color': 'Bela', 'service_interval': '15000'})
        response = self.client.get(f'{reverse("vehicle_create")}?draft={self.token}')
        self.assertFalse(response.context['form'].is_bound)
        self.assertTrue(response.context['form']['add_document'].value())

    def test_duplicate_chassis_is_rejected_before_save(self):
        Vehicle.objects.create(chassis_number='WVWZZZTEST000001', brand='VW', model='Test', year_of_manufacture=2020, category='putnicko')
        self.start()
        response = self.step(0, {'category': 'putnicko', 'chassis_number': 'wvwzzztest000001', 'brand': 'VW', 'model': 'Test', 'year_of_manufacture': '2020'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'već postoji')
        self.assertEqual(Vehicle.objects.count(), 1)

    def test_permission_is_required(self):
        self.user.is_superuser = False
        self.user.save()
        self.assertEqual(self.client.get(reverse('vehicle_create')).status_code, 403)

    def test_unknown_mass_has_no_cost_threshold(self):
        self.assertIsNone(fixed_cost_per_km_threshold(None))
        self.assertEqual(cost_per_km_status(30, None), 'Nema praga')

    def test_electric_vehicle_clears_displacement(self):
        form = VehicleTechnicalForm(data={'fuel_type': 'Električno', 'engine_volume': '100', 'service_interval': '15000'}, category='putnicko')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['engine_volume'])

    def test_credit_records_financing_without_creating_a_lease(self):
        kind = ContractType.objects.create(code='CREDIT', name='Kredit')
        contract = Contract.objects.create(contract_type=kind, contract_number='K-1', title='Kredit za vozilo', contract_date=datetime.date(2020, 1, 1))
        self.prepare(basis={'basis': 'owned', 'start_date': '01.01.2020', 'financing': 'credit', 'financing_contract': contract.pk, 'purchase_value': '100000'})
        self.assertEqual(self.step(5, {}).status_code, 302)
        holding = VehicleHolding.objects.get()
        self.assertEqual(holding.financing_contract, contract)
        self.assertEqual(holding.basis, 'owned')
        self.assertFalse(Lease.objects.exists())

    def test_assignment_and_employee_are_created_with_vehicle(self):
        unit = OrganizationalUnit.objects.create(code='100', name='Test', center='1')
        employee = Employee.objects.create(employee_code=1, first_name='Test', last_name='Vozač', position='Vozač', department_code=1, gender='M', date_of_birth=datetime.date(1990, 1, 1), date_of_joining=datetime.date(2019, 1, 1))
        self.prepare(assignment={'organizational_unit': unit.pk, 'assigned_date': '01.01.2020', 'assign_employee': 'on', 'employee': employee.pk, 'created_at': '01.01.2020', 'start_mileage': '0'})
        self.assertEqual(self.step(5, {}).status_code, 302)
        car = Vehicle.objects.get()
        self.assertEqual(car.job_codes.get().organizational_unit, unit)
        order = car.vehicle_travel_orders.get()
        self.assertEqual(order.employee, employee)
        self.assertEqual(order.start_mileage, 0)

    def test_registration_list_shows_history_only_on_request(self):
        car = vehicle()
        card(car)
        latest = card(car, '2', issued=datetime.date(2022, 1, 1))
        url = reverse('trafficcard_data')
        result = self.client.get(url).json()
        self.assertEqual(result['recordsTotal'], 1)
        self.assertEqual(result['data'][0]['traffic_card_number'], latest.traffic_card_number)
        history = self.client.get(url, {'history': '1'}).json()
        self.assertEqual(history['recordsTotal'], 2)

    def test_changes_in_identity_revalidate_later_steps(self):
        self.prepare()
        self.client.post(reverse('vehicle_create'), {'draft_token': self.token, 'action': 'edit:0'})
        response = self.step(0, {'category': 'prikljucno', 'chassis_number': 'WVWZZZTEST000001', 'brand': 'VW', 'model': 'Prikolica', 'year_of_manufacture': '2020'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Vehicle.objects.exists())
        session = self.client.session
        self.assertEqual(session['vehicle_onboarding'][self.token]['step'], 1)

    def test_existing_contract_number_can_be_taken_from_registry(self):
        kind = ContractType.objects.create(code='RENT', name='Najam')
        contract = Contract.objects.create(contract_type=kind, contract_number='N-1', title='Najam', contract_date=datetime.date(2020, 1, 1), valid_to=datetime.date(2026, 12, 31))
        self.prepare(basis={'basis': 'contract', 'start_date': '01.01.2020', 'partner_code': '10', 'partner_name': 'Najmodavac', 'lease_type': 'dugorocni', 'contract': contract.pk, 'current_payment_amount': '10000'})
        self.assertEqual(self.step(5, {}).status_code, 302)
        lease = Lease.objects.get()
        self.assertEqual(lease.contract, contract)
        self.assertEqual(lease.contract_number, 'N-1')
