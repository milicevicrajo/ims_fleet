import datetime
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from core.models import OrganizationalUnit
from hr.forms import EmployeeForm
from hr.models import Employee, RecipientType, WorkTimeCategory, WorkTimeElement, WorkTimeSheet
from hr.services.attendance import DailyClockHours
from hr.services.praznici import datum_slave, neradni_praznici, pravoslavni_vaskrs, predlog_datuma_slave
from hr.services.work_time_prefill import predlog


class PrazniciTests(SimpleTestCase):
    def test_pravoslavni_vaskrs(self):
        self.assertEqual(pravoslavni_vaskrs(2024), date(2024, 5, 5))
        self.assertEqual(pravoslavni_vaskrs(2025), date(2025, 4, 20))
        self.assertEqual(pravoslavni_vaskrs(2026), date(2026, 4, 12))

    def test_neradni_dani_2026(self):
        praznici = neradni_praznici(2026)
        for datum in (date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 7), date(2026, 2, 15), date(2026, 2, 16),
                      date(2026, 4, 10), date(2026, 4, 13), date(2026, 5, 1), date(2026, 5, 2), date(2026, 11, 11)):
            self.assertIn(datum, praznici)
        # 15. februar 2026. je nedelja, 16. je već praznik, pa se ne radi u utorak 17.
        self.assertEqual(praznici[date(2026, 2, 17)], 'Sretenje — Dan državnosti (prenet sa nedelje)')

    def test_prenos_sa_nedelje_2022(self):
        praznici = neradni_praznici(2022)
        self.assertIn(date(2022, 1, 3), praznici)      # 2. januar je nedelja
        self.assertIn(date(2022, 5, 3), praznici)      # 1. maj je nedelja, 2. maj je već praznik

    def test_datum_slave_iz_neujednacenih_naziva(self):
        for naziv, ocekivano in (('Sv.Nikola', (19, 12)), ('SV.JOVAN', (20, 1)), ('ARAN?ELOVDAN', (21, 11)),
                                 ('?UR?IC', (16, 11)), ('Djurdjevdan', (6, 5)), ('?urdevdan', (6, 5)),
                                 ('Sv.Andrej Prvozvani', (13, 12)), ('ZACECE SV JOVANA KRS', (6, 10)),
                                 ('Sveti Kozma i Damjan', (14, 11)), ('SV.VASILIJE OSTROSKI', (12, 5))):
            self.assertEqual(predlog_datuma_slave(naziv), ocekivano, naziv)

    def test_nesigurna_i_pokretna_slava_nema_predlog(self):
        for naziv in ('BAJRAM', 'Sv. Kliment', 'Sv.Grigorije', '', None):
            self.assertIsNone(predlog_datuma_slave(naziv), naziv)


class PredlogTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.unit = OrganizationalUnit.objects.create(code='430', name='Centar za puteve', center='43')
        tip = RecipientType.objects.create(code='01', name='Zaposleni')
        cls.vrste = {}
        for broj, (code, name) in enumerate((('redovan_rad', 'Redovan rad'), ('bolovanje', 'Bolovanje'),
                                             ('drzavni_i_verski_praznik', 'Državni i verski praznik')), 1):
            vrsta = WorkTimeCategory.objects.create(code=code, name=name)
            WorkTimeElement.objects.create(recipient_type=tip, category=vrsta, payroll_code=broj, payroll_name=name)
            cls.vrste[code] = vrsta
        cls.employee = Employee.objects.create(employee_code=500, first_name='Petar', last_name='Petrović',
            position='Inženjer', department_code=430, org_unit_code='430', gender='M', recipient_code='01',
            slava='SV.VASILIJE OSTROSKI', date_of_birth=date(1990, 1, 1), date_of_joining=date(2020, 1, 1))

    @staticmethod
    def prolaz(datum, minuta):
        return DailyClockHours(date=datum, employee_code=500, employee_name='', total_minutes=minuta,
                               pair_count=1, issue_count=0)

    def maj(self, **kwargs):
        podaci = dict(
            prolazi_po_danu={date(2026, 5, 4): self.prolaz(date(2026, 5, 4), 510),
                             date(2026, 5, 5): self.prolaz(date(2026, 5, 5), 240),
                             date(2026, 5, 9): self.prolaz(date(2026, 5, 9), 300)},
            putni_nalozi_po_danu={date(2026, 5, 8): ['PN'], date(2026, 5, 9): ['PN']},
            bolovanja_po_danu={date(2026, 5, 6): ['B'], date(2026, 5, 7): ['B']},
        )
        podaci.update(kwargs)
        return predlog(self.employee, 2026, 5, 31, **podaci)


class PredlogTests(PredlogTestBase):
    def test_pravila_po_danima(self):
        rezultat = self.maj()
        redovi = {red['kljuc']: red for red in rezultat['redovi']}
        # 5. maj ima samo 4 h prolazaka, ali se predlaže pun dan.
        self.assertEqual(redovi['redovan_rad']['sati'], {'4': 8, '5': 8, '8': 8})
        self.assertEqual(redovi['bolovanje']['sati'], {'6': 8, '7': 8})
        # 1. maj (Praznik rada) i slava Sv. Vasilije Ostroški, 12. maj, datum predložen iz naziva.
        self.assertEqual(redovi['drzavni_i_verski_praznik']['sati'], {'1': 8, '12': 8})
        self.assertEqual(rezultat['teren_dana'], 2)
        for red in redovi.values():
            self.assertEqual(red['sifra_id'], self.unit.pk)
            self.assertEqual(red['vrsta_id'], self.vrste[red['kljuc']].pk)

    def test_napomene(self):
        napomene = ' '.join(self.maj()['napomene'])
        self.assertIn('09.05. (vikend) ima prolaze', napomene)
        self.assertIn('predložen iz naziva', napomene)

    def test_upisan_datum_slave_ima_prednost(self):
        self.employee.slava_datum = date(2000, 5, 14)    # godina se ne koristi
        rezultat = self.maj()
        praznik = next(red for red in rezultat['redovi'] if red['kljuc'] == 'drzavni_i_verski_praznik')
        self.assertEqual(praznik['sati'], {'1': 8, '14': 8})
        self.assertEqual(datum_slave(self.employee, 2026), (date(2026, 5, 14), False))

    def test_bolovanje_ima_prednost_nad_prolazima(self):
        rezultat = self.maj(bolovanja_po_danu={date(2026, 5, 4): ['B']})
        redovi = {red['kljuc']: red for red in rezultat['redovi']}
        self.assertNotIn('4', redovi['redovan_rad']['sati'])
        self.assertEqual(redovi['bolovanje']['sati'], {'4': 8})

    def test_bez_sifre_ostaje_prazno(self):
        self.employee.org_unit_code = '999'
        self.employee.department_code = 999
        rezultat = self.maj()
        self.assertTrue(all(red['sifra_id'] is None for red in rezultat['redovi']))
        self.assertIn('nema podrazumevanu šifru posla', ' '.join(rezultat['napomene']))

    def test_nedostupna_vrsta_se_ne_predlaze(self):
        self.employee.recipient_code = '99'
        rezultat = self.maj()
        self.assertEqual([red['kljuc'] for red in rezultat['redovi']], ['redovan_rad'])
        self.assertIsNone(rezultat['redovi'][0]['vrsta_id'])
        self.assertIn('Bolovanje: vrsta nije dostupna', ' '.join(rezultat['napomene']))

    def test_bez_prolazaka_ostaju_putni_nalog_bolovanje_i_praznici(self):
        rezultat = self.maj(prolazi_po_danu={}, prolazi_ucitani=False)
        redovan = next(red for red in rezultat['redovi'] if red['kljuc'] == 'redovan_rad')
        self.assertEqual(redovan['sati'], {'8': 8})
        self.assertIn('Prolazi nisu učitani', rezultat['napomene'][0])


class EkranTests(PredlogTestBase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('rl-predlog', password='x', employee=self.employee)
        self.client.force_login(self.user)

    @patch('hr.views.get_clock_events', return_value=[])
    def test_prazna_lista_dobija_predlog_odmah(self, _events):
        odgovor = self.client.get(reverse('hr:work_time_sheet'), {'month': 5, 'year': 2026})
        self.assertEqual(odgovor.status_code, 200)
        self.assertTrue(odgovor.context['prefill_auto'])
        self.assertContains(odgovor, 'id="prefill-data"')
        self.assertContains(odgovor, 'Predlog popunjavanja')
        self.assertContains(odgovor, 'Praznik · Praznik rada')
        self.assertEqual(WorkTimeSheet.objects.get().lines.filter(day_1__isnull=False).count(), 0)

    @patch('hr.views.get_clock_events', return_value=[])
    def test_popunjena_lista_se_ne_popunjava_sama(self, _events):
        self.client.get(reverse('hr:work_time_sheet'), {'month': 5, 'year': 2026})
        WorkTimeSheet.objects.get().lines.filter(line_number=1).update(day_4=6)
        odgovor = self.client.get(reverse('hr:work_time_sheet'), {'month': 5, 'year': 2026})
        self.assertFalse(odgovor.context['prefill_auto'])
        self.assertContains(odgovor, 'id="prefill-apply"')


class SlavaFormaTests(PredlogTestBase):
    def _podaci(self, **kwargs):
        podaci = {polje: getattr(self.employee, polje) for polje in
                  ('employee_code', 'first_name', 'last_name', 'position', 'department_code', 'org_unit_code',
                   'gender', 'recipient_code', 'slava')}
        podaci.update(date_of_birth='1990-01-01', date_of_joining='2020-01-01', is_active='on',
                      display_first_name_override='', display_last_name_override='', original_full_name='',
                      full_name_cyrillic='', recipient_name='')
        podaci.update(kwargs)
        return podaci

    def test_forma_predlaze_datum_iz_naziva(self):
        forma = EmployeeForm(instance=self.employee)
        predlog = forma.initial['slava_datum']
        self.assertEqual((predlog.day, predlog.month), (12, 5))
        self.assertTrue(forma.slava_predlog)

    def test_nepostojeci_datum_se_odbija(self):
        forma = EmployeeForm(data=self._podaci(slava_datum='31.04.2026'), instance=self.employee)
        self.assertFalse(forma.is_valid())
        self.assertIn('slava_datum', forma.errors)

    def test_ispravan_datum_se_cuva(self):
        forma = EmployeeForm(data=self._podaci(slava_datum='19.12.2026'), instance=self.employee)
        self.assertTrue(forma.is_valid(), forma.errors)
        forma.save()
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.slava_datum, date(2026, 12, 19))
        self.assertEqual(datum_slave(self.employee, 2027), (date(2027, 12, 19), False))

    def test_forma_je_u_sekcijama_i_nijedno_polje_ne_ispada(self):
        forma = EmployeeForm(instance=self.employee)
        sekcije = forma.sections
        prikazana = [polje.name for sekcija in sekcije for polje in sekcija['fields']]
        self.assertEqual(sorted(prikazana), sorted(forma.fields))
        self.assertEqual([sekcija['key'] for sekcija in sekcije],
                         ['identitet', 'prikaz', 'zaposlenje', 'obracun', 'kontakt', 'dodatno'])
        self.assertTrue(forma.fields['first_name'].hr_sync)
        self.assertFalse(getattr(forma.fields['slava_datum'], 'hr_sync', False))


class EmployeeFormEkranTests(PredlogTestBase):
    def test_izmena_zaposlenog_se_otvara_u_sekcijama(self):
        admin = get_user_model().objects.create_superuser('ef-admin', 'a@example.com', 'x')
        self.client.force_login(admin)
        odgovor = self.client.get(reverse('employee_update', args=[self.employee.pk]))
        self.assertEqual(odgovor.status_code, 200)
        for tekst in ('id="ef-identitet"', 'id="ef-dodatno"', 'Uputstvo', 'iz HR-a', 'ef-toggle'):
            self.assertContains(odgovor, tekst)
        detalj = self.client.get(reverse('employee_detail', args=[self.employee.pk]))
        self.assertContains(detalj, 'Datum slave')
