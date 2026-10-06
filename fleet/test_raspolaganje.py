"""Raspolaganje vozilom: ugovor u stranoj valuti uz iznos u RSD, izbor ugovora pretragom, promena osnova sa kartice."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from ugovori.models import Contract, ContractType

from .forms.lease import LeaseForm
from .forms.onboarding import VehicleBasisForm
from .models import Lease, Vehicle
from .test_vehicle_onboarding import vehicle


def ugovor(broj, valuta='RSD'):
    vrsta, _ = ContractType.objects.get_or_create(code='LIZ', defaults={'name': 'Lizing'})
    return Contract.objects.create(contract_type=vrsta, contract_number=broj, title='Lizing vozila', currency=valuta,
                                   contract_date=datetime.date(2024, 1, 1), valid_to=datetime.date(2027, 12, 31))


class UgovorUStranojValutiTests(TestCase):
    def osnov(self, contract, iznos):
        return VehicleBasisForm(data={'basis': 'contract', 'start_date': '01.01.2024', 'partner_code': '10',
                                      'partner_name': 'Lizing kuća', 'lease_type': 'operativni', 'contract': contract.pk,
                                      'current_payment_amount': iznos, 'payment_basis': 'monthly'})

    def test_novo_vozilo_povezuje_eur_ugovor_uz_iznos_u_dinarima(self):
        eur = ugovor('L-EUR', 'EUR')
        bez_iznosa = self.osnov(eur, '')
        self.assertFalse(bez_iznosa.is_valid())
        self.assertIn('Ugovor je u EUR', bez_iznosa.errors['current_payment_amount'][0])
        self.assertNotIn('contract', bez_iznosa.errors)
        sa_iznosom = self.osnov(eur, '58500')
        self.assertTrue(sa_iznosom.is_valid(), sa_iznosom.errors)

    def test_forma_ugovora_trazi_iznos_u_dinarima_za_eur(self):
        car, eur = vehicle(), ugovor('L-EUR', 'EUR')
        podaci = {'vehicle': car.pk, 'contract_number': 'L-EUR', 'contract': eur.pk, 'lease_type': 'operativni',
                  'partner_code': '10', 'partner_name': 'Lizing kuća', 'start_date': '01.01.2024', 'end_date': '31.12.2026',
                  'payment_basis': 'monthly', 'current_payment_amount': '', 'job_code': '430'}
        forma = LeaseForm(data=podaci)
        self.assertFalse(forma.is_valid())
        self.assertEqual(forma.errors['current_payment_amount'], [
            'Ugovor je u EUR. Unesite iznos naknade u dinarima (RSD) — obračun flote vodi iznose u dinarima.'])
        forma = LeaseForm(data={**podaci, 'current_payment_amount': '58500'})
        self.assertTrue(forma.is_valid(), forma.errors)
        self.assertEqual(forma.save().contract, eur)

    def test_izbor_ugovora_je_select2_sa_valutom(self):
        ugovor('L-RSD')
        eur = ugovor('L-EUR', 'EUR')
        html = str(LeaseForm()['contract'])
        self.assertIn('select2-method', html)
        self.assertIn('data-ugovor-valuta="id_current_payment_amount"', html)
        self.assertIn(f'value="{eur.pk}" data-currency="EUR"', html)
        self.assertIn('L-EUR – Lizing vozila · EUR', html)


class RaspolaganjeIzUgovoraTests(TestCase):
    """Osnov raspolaganja sledi iz ugovora; promena je „Dodaj ugovor” / „Završi”."""

    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser('flota', password='x'))
        self.car = vehicle()
        self.detalj = reverse('vehicle_detail', args=[self.car.pk])
        danas = datetime.date.today()
        self.lease = Lease.objects.create(vehicle=self.car, contract_number='L1', partner_code='1', partner_name='P', job_code='430',
                                          current_payment_amount=1000, payment_basis='monthly', lease_type='operativni',
                                          start_date=danas - datetime.timedelta(days=10), end_date=danas + datetime.timedelta(days=300))

    def test_kartica_ima_jednu_listu_ugovora_sa_radnjama(self):
        odgovor = self.client.get(self.detalj)
        self.assertEqual(odgovor.context['holding_label'], 'Operativni')
        self.assertContains(odgovor, 'Osnov raspolaganja i ugovori')
        self.assertContains(odgovor, f"{reverse('lease_create')}?vehicle={self.car.pk}")
        self.assertContains(odgovor, f"{reverse('lease_update', args=[self.lease.pk])}?zavrsi=1")
        self.assertNotContains(odgovor, 'Promeni osnov')

    def test_zavrsi_ugovor_vraca_na_vozilo_i_menja_osnov(self):
        url = reverse('lease_update', args=[self.lease.pk]) + '?zavrsi=1'
        forma = self.client.get(url)
        self.assertContains(forma, 'Završi ugovor L1')
        kraj = datetime.date.today() - datetime.timedelta(days=1)
        podaci = {'vehicle': self.car.pk, 'contract_number': 'L1', 'lease_type': 'operativni', 'partner_code': '1',
                  'partner_name': 'P', 'start_date': self.lease.start_date.strftime('%d.%m.%Y'), 'end_date': kraj.strftime('%d.%m.%Y'),
                  'payment_basis': 'monthly', 'current_payment_amount': '1000', 'job_code': '430'}
        odgovor = self.client.post(url, podaci)
        self.assertRedirects(odgovor, self.detalj + '#holding-pane', fetch_redirect_response=False)
        self.assertEqual(self.client.get(self.detalj).context['holding_label'], 'Vlasništvo IMS')

    def test_ugovor_se_ne_premesta_na_drugo_vozilo(self):
        drugo = vehicle('2')
        podaci = {'vehicle': drugo.pk, 'contract_number': 'L1', 'lease_type': 'operativni', 'partner_code': '1', 'partner_name': 'P',
                  'start_date': self.lease.start_date.strftime('%d.%m.%Y'), 'end_date': self.lease.end_date.strftime('%d.%m.%Y'),
                  'payment_basis': 'monthly', 'current_payment_amount': '1000', 'job_code': '430'}
        forma = LeaseForm(data=podaci, instance=self.lease)
        self.assertFalse(forma.is_valid())
        self.assertIn('vehicle', forma.errors)

    def test_finansiranje_se_unosi_na_vozilu(self):
        kredit = ugovor('K-1')
        self.car.financing, self.car.financing_contract = 'own_funds', kredit
        with self.assertRaises(ValidationError):
            self.car.full_clean()
        self.car.financing = 'credit'
        self.car.full_clean()


class KamataLizingaTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser('kamate', password='x'))
        self.lease = Lease.objects.create(vehicle=vehicle(), contract_number='20304/22', partner_code='1', partner_name='Intesa',
                                          job_code='430', current_payment_amount=1, lease_type='finansijski',
                                          start_date=datetime.date(2022, 3, 30), end_date=datetime.date(2026, 3, 30))
        self.url = reverse('lease_interest_update', args=[self.lease.pk])

    def test_unos_po_godinama_i_brisanje_praznog(self):
        forma = self.client.get(self.url).context['form']
        self.assertEqual([f for f in forma.fields], [f'godina_{g}' for g in range(2022, 2027)])
        self.assertIn('277 dana', forma.fields['godina_2022'].help_text)  # 30.03.–31.12.2022.
        odgovor = self.client.post(self.url, {'godina_2022': '150000', 'godina_2023': '180000.50', 'godina_2024': ''})
        self.assertRedirects(odgovor, reverse('lease_detail', args=[self.lease.pk]))
        self.assertEqual(dict(self.lease.lease_interests.values_list('year', 'interest_amount')),
                         {2022: Decimal('150000'), 2023: Decimal('180000.50')})
        self.client.post(self.url, {'godina_2022': '150000'})
        self.assertEqual(list(self.lease.lease_interests.values_list('year', flat=True)), [2022])
        detalj = self.client.get(reverse('lease_detail', args=[self.lease.pk]))
        self.assertContains(detalj, 'Unesi kamate')
        self.assertContains(detalj, 'nije uneta')

    def test_samo_za_finansijski_lizing(self):
        Lease.objects.filter(pk=self.lease.pk).update(lease_type='operativni', payment_basis='total')
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_dozvola_izvedena_iz_izmene_ugovora(self):
        from core.models import PermissionCode, Role, RolePermission
        from core.permissions import sync_permission_codes

        uloga = Role.objects.create(name='Flota test', slug='flota-test')
        RolePermission.objects.create(role=uloga, permission=PermissionCode.objects.get_or_create(code='lease_update')[0])
        sync_permission_codes()
        self.assertTrue(uloga.permissions.filter(code='lease_interest_update').exists())


class MigracijaRaspolaganjaTests(TransactionTestCase):
    """0090: osnov raspolaganja se prenosi na vozilo i ugovor, pa se tabela briše."""

    def test_prenos_pre_brisanja(self):
        executor = MigrationExecutor(connection)
        executor.migrate([('fleet', '0089_opomene_goriva')])
        stare = executor.loader.project_state([('fleet', '0089_opomene_goriva')]).apps
        StaroVozilo, StariUgovor, Osnov = (stare.get_model('fleet', m) for m in ('Vehicle', 'Lease', 'VehicleHolding'))
        Vrsta, Ugovor = stare.get_model('ugovori', 'ContractType'), stare.get_model('ugovori', 'Contract')
        kredit = Ugovor.objects.create(contract_type=Vrsta.objects.create(code='K', name='Kredit'), contract_number='K-1',
                                       title='Kredit', contract_date=datetime.date(2020, 1, 1))
        vozilo = lambda n: StaroVozilo.objects.create(chassis_number=f'VIN{n:014d}', brand='VW', model='Test', year_of_manufacture=2020,
                                                  category='putnicko')
        svoje, lizing = vozilo(1), vozilo(2)
        Osnov.objects.create(vehicle=svoje, basis='owned', start_date=datetime.date(2021, 5, 3), financing='credit',
                               financing_contract=kredit, evidence='Kupoprodajni ugovor 7/2021')
        ugovor_l = StariUgovor.objects.create(vehicle=lizing, partner_code='1', partner_name='P', job_code='A', contract_number='L-9',
                                        current_payment_amount=1, start_date=datetime.date(2022, 1, 1), end_date=datetime.date(2025, 1, 1))
        Osnov.objects.create(vehicle=lizing, basis='contract', lease=ugovor_l, start_date=datetime.date(2022, 1, 1),
                               end_date=datetime.date(2025, 1, 1), evidence='Preneto iz postojeće evidencije lizinga (test)')
        executor = MigrationExecutor(connection)
        executor.migrate([('fleet', '0090_raspolaganje_iz_ugovora')])
        svoje = Vehicle.objects.get(pk=svoje.pk)
        self.assertEqual((svoje.financing, svoje.financing_contract_id, svoje.purchase_date),
                         ('credit', kredit.pk, datetime.date(2021, 5, 3)))
        self.assertIn('Kupoprodajni ugovor 7/2021', svoje.description)
        self.assertFalse(Lease.objects.get(pk=ugovor_l.pk).note)  # automatski tekst prenosa se ne prepisuje
        self.assertNotIn('fleet_vehicleholding', connection.introspection.table_names())
