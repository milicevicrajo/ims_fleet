from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from core.models import OrganizationalUnit
from hr.models import Employee, Pismo, Potpisnik, Resenje, ResenjeDan, VrstaResenja
from hr.services.resenja import (build_document, izdaj_resenje, opis_perioda, pripremi_resenje, razresi,
    to_cyrillic, u_pismu, uskladi_digrafe, visible_resenja)


class PreslovljavanjeTests(TestCase):
    def test_digrafi_idu_pre_pojedinacnih_slova(self):
        self.assertEqual(to_cyrillic('Ljubomir Njegoš Džamija'), 'Љубомир Његош Џамија')

    def test_verzal_digrafa_daje_jedno_slovo(self):
        self.assertEqual(to_cyrillic('LJUBOMIR NJEGOŠ'), 'ЉУБОМИР ЊЕГОШ')

    def test_dijakritici_se_preslovljavaju(self):
        self.assertEqual(to_cyrillic('Čačak Šabac Đorđe Ćuprija Žitište'), 'Чачак Шабац Ђорђе Ћуприја Житиште')

    def test_strana_slova_ostaju_netaknuta(self):
        self.assertEqual(to_cyrillic('IMS a.d. 43'), 'ИМС а.д. 43')


class DigrafiUVerzaluTests(TestCase):
    def test_verzal_dobija_oba_slova_velika(self):
        self.assertEqual(uskladi_digrafe('REŠENjE'), 'REŠENJE')
        self.assertEqual(uskladi_digrafe('MILjANA'), 'MILJANA')
        self.assertEqual(uskladi_digrafe('NjEGOŠ'), 'NJEGOŠ')

    def test_obicna_rec_ostaje_netaknuta(self):
        self.assertEqual(uskladi_digrafe('Njegoš Ljubomir Džamija'), 'Njegoš Ljubomir Džamija')
        self.assertEqual(uskladi_digrafe('konj i ljudi'), 'konj i ljudi')

    def test_naslov_resenja_u_latinici(self):
        self.assertEqual(u_pismu('РЕШЕЊЕ', Pismo.LATINICA), 'REŠENJE')
        self.assertEqual(u_pismu('РЕШЕЊЕ', Pismo.CIRILICA), 'РЕШЕЊЕ')


class CuvariMestaTests(TestCase):
    def test_rod_bira_oblik_po_polu(self):
        self.assertEqual(razresi('{rod:дужан|дужна}', {}, 'M'), 'дужан')
        self.assertEqual(razresi('{rod:дужан|дужна}', {}, 'F'), 'дужна')

    def test_nepoznat_pol_nudi_oba_oblika(self):
        self.assertEqual(razresi('{rod:дужан|дужна}', {}, ''), 'дужан/дужна')

    def test_nepoznat_cuvar_ostaje_vidljiv(self):
        self.assertEqual(razresi('{nepostojeci}', {}, 'M'), '{nepostojeci}')

    def test_uslovni_segment_otpada_kada_je_vrednost_prazna(self):
        obrazac = 'ради[[dani_verski| и {dani_verski} на верски празник]]'
        self.assertEqual(razresi(obrazac, {'dani_verski': ''}, 'M'), 'ради')
        self.assertEqual(razresi(obrazac, {'dani_verski': '07.01.2025.'}, 'M'),
                         'ради и 07.01.2025. на верски празник')


class ResenjeTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        OrganizationalUnit.objects.create(code='430', name='Centar za puteve i geotehniku', center='43')
        cls.employee = Employee.objects.create(employee_code=900, first_name='Lazar', last_name='Živanović',
            department_code=430, org_unit_code='430', position='Inženjer', gender='M',
            date_of_birth=date(1985, 5, 5), date_of_joining=date(2015, 1, 1))
        cls.direktor = Employee.objects.create(employee_code=901, first_name='Dragan', last_name='Bojović',
            department_code=100, org_unit_code='100', position='Generalni direktor', gender='M',
            date_of_birth=date(1970, 1, 1), date_of_joining=date(2000, 1, 1))
        cls.user = get_user_model().objects.create_superuser('kadrovik-test', 'k@example.com', 'test-pass')
        cls.potpisnik = Potpisnik.objects.create(zaposleni=cls.direktor, funkcija='Генерални директор',
            ime_cirilica='др Драган Бојовић, дипл.инж.', vazi_od=date(2024, 1, 1))
        cls.vrsta = VrstaResenja.objects.get(kod='praznik')

    def napravi(self, **kwargs):
        podaci = dict(zaposleni=self.employee, vrsta=self.vrsta, broj='43-15238',
            datum_resenja=date(2024, 12, 27), pismo=Pismo.CIRILICA, zahtev_broj='43-15238',
            zahtev_datum=date(2024, 12, 27), created_by=self.user)
        podaci.update(kwargs)
        resenje = Resenje(**podaci)
        pripremi_resenje(resenje)
        resenje.save()
        return resenje


class SifrarnikTests(ResenjeTestBase):
    def test_hr_unit_without_job_code_uses_existing_center_mapping(self):
        self.employee.org_unit_code = '431 '
        self.employee.save(update_fields=['org_unit_code'])
        resenje = self.napravi()
        self.assertEqual(resenje.oj_kod, '431')
        self.assertEqual(resenje.centar, '43')

    def test_unknown_hr_unit_does_not_guess_a_center(self):
        self.employee.org_unit_code = '999'
        self.employee.save(update_fields=['org_unit_code'])
        self.assertEqual(self.napravi().centar, '')

    def test_migracija_puni_svih_sedam_obrazaca(self):
        self.assertEqual(VrstaResenja.objects.count(), 7)

    def test_svaki_obrazac_ima_pravni_osnov_i_dispozitiv(self):
        for vrsta in VrstaResenja.objects.all():
            self.assertTrue(vrsta.pravni_osnov.strip(), vrsta.kod)
            self.assertTrue(vrsta.dispozitiv.strip(), vrsta.kod)


class PripremaTests(ResenjeTestBase):
    def test_podaci_o_jedinici_se_preuzimaju_iz_evidencije(self):
        resenje = self.napravi()
        self.assertEqual(resenje.oj_kod, '430')
        self.assertEqual(resenje.centar, '43')
        self.assertEqual(resenje.oj_naziv, 'ЦЕНТАР ЗА ПУТЕВЕ И ГЕОТЕХНИКУ')

    def test_ime_se_preslovljava_kada_nema_rucnog_unosa(self):
        self.assertEqual(self.napravi().zaposleni_tekst, 'ЛАЗАР ЖИВАНОВИЋ')

    def test_rucno_unet_cirilicni_oblik_ima_prednost(self):
        self.employee.full_name_cyrillic = 'Лазар Н. Живановић'
        self.employee.save(update_fields=['full_name_cyrillic'])
        self.assertEqual(self.napravi().zaposleni_tekst, 'ЛАЗАР Н. ЖИВАНОВИЋ')

    def test_potpisnik_se_bira_po_datumu_resenja(self):
        Potpisnik.objects.create(zaposleni=self.direktor, funkcija='в.д. Генералног директора',
            vazi_od=date(2020, 1, 1), vazi_do=date(2024, 1, 1))
        resenje = self.napravi(datum_resenja=date(2023, 6, 1))
        self.assertEqual(resenje.potpisnik.funkcija, 'в.д. Генералног директора')

    def test_bez_potpisnika_resenje_se_ne_izdaje(self):
        Potpisnik.objects.all().delete()
        resenje = self.napravi()
        with self.assertRaises(ValidationError):
            izdaj_resenje(resenje, self.user)


class DokumentTests(ResenjeTestBase):
    def test_pol_razresava_oblike_u_tekstu(self):
        resenje = self.napravi()
        ResenjeDan.objects.create(resenje=resenje, datum=date(2025, 1, 1), vrsta_dana='drzavni')
        dokument = build_document(resenje)
        self.assertIn('запослен ', dokument['tacke'][0])
        self.assertNotIn('запослен-а', dokument['tacke'][0])

    def test_zenski_rod_daje_druge_oblike(self):
        self.employee.gender = 'F'
        self.employee.save(update_fields=['gender'])
        resenje = self.napravi()
        ResenjeDan.objects.create(resenje=resenje, datum=date(2025, 1, 1), vrsta_dana='drzavni')
        dokument = build_document(resenje)
        self.assertIn('запослена', dokument['tacke'][0])
        self.assertIn('дужна', dokument['tacke'][0])

    def test_verski_praznik_otpada_kada_nema_takvih_dana(self):
        resenje = self.napravi()
        ResenjeDan.objects.create(resenje=resenje, datum=date(2025, 1, 1), vrsta_dana='drzavni')
        tacka = build_document(resenje)['tacke'][0]
        self.assertIn('на дан државног празника', tacka)
        self.assertNotIn('верског празника', tacka)

    def test_oba_praznika_ulaze_u_istu_tacku(self):
        resenje = self.napravi()
        ResenjeDan.objects.create(resenje=resenje, datum=date(2025, 1, 1), vrsta_dana='drzavni')
        ResenjeDan.objects.create(resenje=resenje, datum=date(2025, 1, 7), vrsta_dana='verski')
        tacka = build_document(resenje)['tacke'][0]
        self.assertIn('01.01.2025.', tacka)
        self.assertIn('07.01.2025.', tacka)
        self.assertIn('верског празника', tacka)

    def test_latinicno_resenje_preslovljava_ceo_dokument(self):
        resenje = self.napravi(pismo=Pismo.LATINICA)
        ResenjeDan.objects.create(resenje=resenje, datum=date(2025, 1, 1), vrsta_dana='drzavni')
        dokument = build_document(resenje)
        self.assertEqual(dokument['zaglavlje']['institut'], 'Institut za ispitivanje materijala a.d.')
        self.assertEqual(dokument['potpis']['ime'], 'dr Dragan Bojović, dipl.inž.')
        self.assertNotIn('ћ', ' '.join(dokument['tacke']))

    def test_prazan_red_ne_ostavlja_praznu_tacku(self):
        resenje = self.napravi(napomena='')
        ResenjeDan.objects.create(resenje=resenje, datum=date(2025, 1, 1), vrsta_dana='drzavni')
        self.assertTrue(all(pasus.strip() for pasus in build_document(resenje)['obrazlozenje']))

    def test_centar_ulazi_u_spisak_dostavljanja(self):
        resenje = self.napravi()
        self.assertIn('Ц 43', build_document(resenje)['dostavljeno'])


class OpisPeriodaTests(ResenjeTestBase):
    def test_period_od_do(self):
        resenje = self.napravi(datum_od=date(2026, 2, 1), datum_do=date(2026, 2, 28))
        self.assertEqual(opis_perioda(resenje, []), 'у периоду од 01.02.2026. до 28.02.2026. године')

    def test_do_zavrsetka_posla(self):
        resenje = self.napravi(datum_od=date(2016, 6, 23), do_zavrsetka_posla=True)
        self.assertEqual(opis_perioda(resenje, []), 'почев од 23.06.2016. до завршетка посла')

    def test_pojedinacni_dani_se_nabrajaju(self):
        resenje = self.napravi()
        dani = [ResenjeDan.objects.create(resenje=resenje, datum=dan, vrsta_dana='vikend')
                for dan in (date(2026, 6, 20), date(2026, 6, 21))]
        self.assertEqual(opis_perioda(resenje, dani), '20.06.2026. и 21.06.2026. године')


class IzdavanjeTests(ResenjeTestBase):
    def test_izdavanje_pamti_dokument_i_zakljucava_resenje(self):
        resenje = self.napravi()
        ResenjeDan.objects.create(resenje=resenje, datum=date(2025, 1, 1), vrsta_dana='drzavni')
        izdaj_resenje(resenje, self.user)
        resenje.refresh_from_db()
        self.assertEqual(resenje.status, Resenje.Status.IZDATO)
        self.assertTrue(resenje.je_zakljucano)
        self.assertTrue(resenje.dokument['tacke'])

    def test_izmena_sifrarnika_ne_menja_vec_izdato_resenje(self):
        resenje = self.napravi()
        ResenjeDan.objects.create(resenje=resenje, datum=date(2025, 1, 1), vrsta_dana='drzavni')
        izdaj_resenje(resenje, self.user)
        snimljeno = resenje.dokument['tacke'][0]
        self.vrsta.dispozitiv = 'Потпуно нов текст.'
        self.vrsta.save(update_fields=['dispozitiv'])
        resenje.refresh_from_db()
        self.assertEqual(resenje.dokument['tacke'][0], snimljeno)

    def test_dva_puta_izdato_resenje_je_greska(self):
        resenje = self.napravi()
        izdaj_resenje(resenje, self.user)
        with self.assertRaises(ValidationError):
            izdaj_resenje(resenje, self.user)


class VidljivostTests(ResenjeTestBase):
    def test_korisnik_bez_centara_vidi_samo_svoja_resenja(self):
        resenje = self.napravi()
        drugi = get_user_model().objects.create_user('drugi-kadrovik', password='test-pass')
        self.assertNotIn(resenje, visible_resenja(drugi))
        self.assertIn(resenje, visible_resenja(self.user))

    def test_dozvoljen_centar_otvara_resenja_tog_centra(self):
        resenje = self.napravi()
        drugi = get_user_model().objects.create_user('centar-43', password='test-pass')
        drugi.allowed_center_codes = '43'
        drugi.save(update_fields=['allowed_center_codes'])
        self.assertIn(resenje, visible_resenja(drugi))


class EkraniTests(ResenjeTestBase):
    def setUp(self):
        self.client.force_login(self.user)

    def test_lista_se_otvara(self):
        self.napravi()
        odgovor = self.client.get(reverse('hr:resenje_list'))
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, '43-15238')

    def test_detalj_prikazuje_dokument_i_pre_izdavanja(self):
        resenje = self.napravi()
        odgovor = self.client.get(reverse('hr:resenje_detail', args=[resenje.pk]))
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, 'ЛАЗАР ЖИВАНОВИЋ')

    def test_izdato_resenje_se_ne_otvara_za_izmenu(self):
        resenje = self.napravi()
        izdaj_resenje(resenje, self.user)
        self.assertEqual(self.client.get(reverse('hr:resenje_edit', args=[resenje.pk])).status_code, 404)

    def test_stampa_vraca_dokument(self):
        resenje = self.napravi()
        odgovor = self.client.get(reverse('hr:resenje_print', args=[resenje.pk]))
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, 'РЕШЕЊЕ')

    def test_grupno_izdavanje_pravi_nacrt_za_svakog_izabranog(self):
        podaci = {'vrsta': self.vrsta.pk, 'datum_resenja': '2026-06-19', 'pismo': Pismo.CIRILICA,
                  'dani': '20.06.2026, 21.06.2026', 'vrsta_dana': 'vikend', 'zahtev_broj': '82-6992',
                  'zahtev_datum': '2026-06-18', 'zaposleni': [self.employee.pk],
                  f'broj_{self.employee.pk}': '82-7001'}
        odgovor = self.client.post(reverse('hr:resenje_bulk_create'), podaci)
        self.assertEqual(odgovor.status_code, 302)
        resenje = Resenje.objects.get(broj='82-7001')
        self.assertEqual(resenje.status, Resenje.Status.NACRT)
        self.assertEqual(resenje.dani.count(), 2)

    def _forma_podaci(self, **kwargs):
        podaci = {'vrsta': self.vrsta.pk, 'zaposleni': self.employee.pk, 'broj': '43-20001',
                  'datum_resenja': '2025-01-03', 'pismo': Pismo.CIRILICA,
                  'zaposleni_tekst': '', 'oj_naziv': '', 'radno_mesto': '',
                  'zahtev_broj': '43-15238', 'zahtev_datum': '2024-12-27', 'napomena': '',
                  'dani-TOTAL_FORMS': '1', 'dani-INITIAL_FORMS': '0',
                  'dani-MIN_NUM_FORMS': '0', 'dani-MAX_NUM_FORMS': '1000',
                  'dani-0-datum': '2025-01-01', 'dani-0-vrsta_dana': 'drzavni'}
        podaci.update(kwargs)
        return podaci

    def test_unos_kroz_formu_pravi_nacrt_sa_danima(self):
        odgovor = self.client.post(reverse('hr:resenje_create'), self._forma_podaci())
        self.assertEqual(odgovor.status_code, 302)
        resenje = Resenje.objects.get(broj='43-20001')
        self.assertEqual(resenje.status, Resenje.Status.NACRT)
        self.assertEqual(resenje.dani.count(), 1)
        self.assertEqual(resenje.centar, '43')

    def test_forma_prihvata_lokalne_datume_i_vise_od_cetiri_dana(self):
        podaci = self._forma_podaci(datum_resenja='03.01.2025', zahtev_datum='27.12.2024.')
        podaci['dani-TOTAL_FORMS'] = '6'
        for index in range(6):
            podaci[f'dani-{index}-datum'] = f'{index + 1:02d}.01.2025'
            podaci[f'dani-{index}-vrsta_dana'] = 'drzavni'
        podaci['dani-1-DELETE'] = 'on'
        odgovor = self.client.post(reverse('hr:resenje_create'), podaci)
        self.assertEqual(odgovor.status_code, 302)
        resenje = Resenje.objects.get(broj='43-20001')
        self.assertEqual(resenje.datum_resenja, date(2025, 1, 3))
        self.assertEqual(resenje.zahtev_datum, date(2024, 12, 27))
        self.assertEqual(list(resenje.dani.values_list('datum', flat=True)),
                         [date(2025, 1, day) for day in (1, 3, 4, 5, 6)])

    def test_grupna_forma_cuva_izbor_i_brojeve_posle_greske(self):
        podaci = {'vrsta': self.vrsta.pk, 'datum_resenja': '', 'pismo': Pismo.CIRILICA,
                  'zaposleni': [self.employee.pk], f'broj_{self.employee.pk}': '43-20002'}
        odgovor = self.client.post(reverse('hr:resenje_bulk_create'), podaci)
        self.assertEqual(odgovor.status_code, 200)
        row = next(row for row in odgovor.context['employee_rows'] if row['employee'] == self.employee)
        self.assertTrue(row['selected'])
        self.assertEqual(row['broj'], '43-20002')
        self.assertFalse(Resenje.objects.exists())

    def test_vrsta_koja_trazi_dane_ne_prolazi_bez_njih(self):
        odgovor = self.client.post(reverse('hr:resenje_create'),
            self._forma_podaci(**{'dani-TOTAL_FORMS': '0', 'dani-0-datum': '', 'dani-0-vrsta_dana': ''}))
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, 'traži bar jedan dan')
        self.assertFalse(Resenje.objects.filter(broj='43-20001').exists())

    def test_grupno_izdavanje_trazi_broj_za_svakog(self):
        podaci = {'vrsta': self.vrsta.pk, 'datum_resenja': '2026-06-19', 'pismo': Pismo.CIRILICA,
                  'dani': '20.06.2026', 'vrsta_dana': 'vikend', 'zaposleni': [self.employee.pk]}
        odgovor = self.client.post(reverse('hr:resenje_bulk_create'), podaci)
        self.assertEqual(odgovor.status_code, 200)
        self.assertFalse(Resenje.objects.exists())
