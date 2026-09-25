from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from hr.models import BrojacZahteva, Employee, Pismo, Resenje, VrstaResenja, VrstaZahteva, Zahtev, ZahtevDan
from hr.resenja_forms import VrstaResenjaForm
from hr.services.resenja import build_document, izdaj_resenje, storniraj_resenje
from hr.services.zahtevi import (build_zahtev_document, dodeli_broj, napravi_resenje, podnesi_zahtev,
    pripremi_zahtev, storniraj_zahtev, visible_zahtevi)
from hr.test_resenja import ResenjeTestBase
from hr.zahtevi_forms import BrojacZahtevaForm


class ZahtevTestBase(ResenjeTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.rukovodilac = Employee.objects.create(employee_code=902, first_name='Olivera', last_name='Pavlović',
            department_code=430, org_unit_code='430', position='Finansijski direktor', gender='F',
            date_of_birth=date(1975, 3, 3), date_of_joining=date(2005, 1, 1))
        cls.vrsta_zahteva = VrstaZahteva.objects.get(kod='prekovremeni-i-vikend')

    def zahtev(self, **kwargs):
        podaci = dict(vrsta=self.vrsta_zahteva, zaposleni=self.employee, datum_zahteva=date(2026, 7, 28),
            pismo=Pismo.CIRILICA, datum_od=date(2026, 8, 1), datum_do=date(2026, 8, 31),
            razlog='потребе за радом већим од четрдесет сати недељно', podnosilac=self.rukovodilac,
            podnosilac_funkcija='Финансијски директор', created_by=self.user)
        podaci.update(kwargs)
        zahtev = Zahtev(**podaci)
        pripremi_zahtev(zahtev)
        dodeli_broj(zahtev)
        zahtev.save()
        return zahtev


class SifrarnikZahtevaTests(ZahtevTestBase):
    def test_svaka_vrsta_resenja_ima_svoj_zahtev(self):
        self.assertEqual(VrstaZahteva.objects.count(), VrstaResenja.objects.count())
        for vrsta in VrstaZahteva.objects.all():
            self.assertIsNotNone(vrsta.vrsta_resenja, vrsta.kod)
            self.assertTrue(vrsta.predmet.strip() and vrsta.tekst.strip(), vrsta.kod)

    def test_zamena_je_resenje_sa_poljem_za_poslove(self):
        vrsta = VrstaZahteva.objects.get(kod='zamena-odsutnog')
        self.assertEqual(vrsta.vrsta_resenja.kod, 'zamena-odsutnog')
        self.assertIn('poslovi|', vrsta.dodatna_polja)
        self.assertIn('poslovi|', vrsta.vrsta_resenja.dodatna_polja)

    def test_neispravno_dodatno_polje_se_odbija(self):
        vrsta = VrstaResenja.objects.get(kod='vikend')
        podaci = {polje: getattr(vrsta, polje) for polje in VrstaResenjaForm._meta.fields}
        for oznaka in ('Poslovi|X', 'zaposleni|Ime', 'a|A\na|B'):
            podaci['dodatna_polja'] = oznaka
            self.assertFalse(VrstaResenjaForm(data=podaci, instance=vrsta).is_valid(), oznaka)


class BrojeviTests(ZahtevTestBase):
    def test_broj_je_centar_i_redni_broj_u_godini(self):
        prvi, drugi = self.zahtev(), self.zahtev()
        self.assertEqual((prvi.broj, drugi.broj), ('43-1', '43-2'))
        self.assertEqual(BrojacZahteva.objects.get(godina=2026).poslednji_broj, 2)

    def test_nova_godina_pocinje_od_jedan(self):
        self.zahtev()
        self.assertEqual(self.zahtev(datum_zahteva=date(2027, 1, 4)).broj, '43-1')

    def test_brojac_se_moze_nastaviti_na_delovodnik(self):
        BrojacZahteva.objects.create(godina=2026, poslednji_broj=15237)
        self.assertEqual(self.zahtev().broj, '43-15238')

    def test_brojac_ne_ide_unazad(self):
        self.zahtev()
        self.zahtev()
        brojac = BrojacZahteva.objects.get(godina=2026)
        forma = BrojacZahtevaForm(data={'godina': 2026, 'poslednji_broj': 1}, instance=brojac)
        self.assertFalse(forma.is_valid())

    def test_storniran_zahtev_ne_vraca_broj(self):
        prvi = self.zahtev()
        storniraj_zahtev(prvi, self.user)
        self.assertEqual(self.zahtev().broj, '43-2')


class DokumentZahtevaTests(ZahtevTestBase):
    def test_tekst_prati_obrazac_kadrovske(self):
        dokument = build_zahtev_document(self.zahtev())
        tekst = ' '.join(dokument['pasusi'])
        self.assertEqual(dokument['predmet'], 'Захтев за издавање решења за прековремени рад и рад викендом')
        self.assertIn('због потребе за радом већим од четрдесет сати недељно', tekst)
        self.assertIn('за запосленог: ЛАЗАР ЖИВАНОВИЋ', tekst)
        self.assertIn('од 01.08.2026. до 31.08.2026. године', tekst)
        self.assertEqual(dokument['broj'], '43-1')

    def test_potpisuje_podnosilac_a_odobrava_potpisnik_resenja(self):
        dokument = build_zahtev_document(self.zahtev())
        self.assertEqual(dokument['potpis']['funkcija'], 'Финансијски директор')
        self.assertIn('Павловић', dokument['potpis']['ime'])
        self.assertEqual(dokument['odobrenje']['ime'], 'др Драган Бојовић, дипл.инж.')
        self.assertEqual(dokument['odobrenje']['funkcija'], 'Генерални директор')

    def test_latinica(self):
        dokument = build_zahtev_document(self.zahtev(pismo=Pismo.LATINICA, zaposleni_tekst='LAZAR ŽIVANOVIĆ'))
        self.assertEqual(dokument['predmet'], 'Zahtev za izdavanje rešenja za prekovremeni rad i rad vikendom')
        self.assertEqual(dokument['oznake']['broj'], 'Naš znak:')

    def test_razlog_je_opcion(self):
        tekst = ' '.join(build_zahtev_document(self.zahtev(razlog=''))['pasusi'])
        self.assertIn('Молим Вас да издате решење', tekst)

    def test_podnet_zahtev_cuva_tekst(self):
        zahtev = self.zahtev()
        podnesi_zahtev(zahtev, self.user)
        self.rukovodilac.last_name = 'Promenjeno'
        self.rukovodilac.save(update_fields=['last_name'])
        zahtev.refresh_from_db()
        self.assertEqual(zahtev.status, Zahtev.Status.PODNET)
        self.assertIn('Павловић', zahtev.dokument['potpis']['ime'])


class ResenjeIzZahtevaTests(ZahtevTestBase):
    def test_jedan_zahtev_jedno_resenje_i_posle_storniranja(self):
        zahtev = self.zahtev()
        resenje = napravi_resenje(zahtev, self.user)
        for status in Resenje.Status.values:
            Resenje.objects.filter(pk=resenje.pk).update(status=status)
            with self.assertRaisesMessage(ValidationError, 'Zahtev već ima rešenje'):
                napravi_resenje(zahtev, self.user)
        zahtev.refresh_from_db()
        self.assertEqual(zahtev.poslednji_podbroj, 1)
        self.assertEqual(zahtev.resenja.count(), 1)

    def test_baza_odbija_drugo_resenje_i_resenje_bez_zahteva(self):
        zahtev = self.zahtev()
        resenje = napravi_resenje(zahtev, self.user)
        podaci = dict(zaposleni=self.employee, vrsta=resenje.vrsta, broj='drugo',
                      datum_resenja=date(2026, 9, 24), created_by=self.user)
        for veza in (zahtev, None):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Resenje.objects.create(zahtev=veza, **podaci)
        self.assertEqual(Resenje.objects.count(), 1)

    def test_resenje_je_podbroj_zahteva_i_preuzima_podatke(self):
        zahtev = self.zahtev()
        resenje = napravi_resenje(zahtev, self.user, datum_resenja=date(2026, 7, 30))
        self.assertEqual(resenje.broj, '43-1/1')
        self.assertEqual((resenje.zahtev, resenje.podbroj), (zahtev, 1))
        self.assertEqual(resenje.vrsta.kod, 'prekovremeni-i-vikend')
        self.assertEqual((resenje.datum_od, resenje.datum_do), (zahtev.datum_od, zahtev.datum_do))
        self.assertEqual((resenje.zahtev_broj, resenje.zahtev_datum), ('43-1', date(2026, 7, 28)))
        self.assertEqual(resenje.status, Resenje.Status.NACRT)
        obrazlozenje = ' '.join(build_document(resenje)['obrazlozenje'])
        self.assertIn('захтева бр. 43-1', obrazlozenje)

    def test_dani_zahteva_prelaze_u_resenje(self):
        zahtev = self.zahtev(vrsta=VrstaZahteva.objects.get(kod='vikend'), datum_od=None, datum_do=None)
        ZahtevDan.objects.create(zahtev=zahtev, datum=date(2026, 6, 20), vrsta_dana='vikend')
        ZahtevDan.objects.create(zahtev=zahtev, datum=date(2026, 6, 21), vrsta_dana='vikend')
        resenje = napravi_resenje(zahtev, self.user)
        self.assertEqual(list(resenje.dani.values_list('datum', flat=True)), [date(2026, 6, 20), date(2026, 6, 21)])

    def test_podbroj_se_ne_koristi_ponovo(self):
        zahtev = self.zahtev()
        napravi_resenje(zahtev, self.user).delete()
        self.assertEqual(napravi_resenje(zahtev, self.user).broj, '43-1/2')

    def test_izdavanje_resenja_zakljucava_zahtev(self):
        zahtev = self.zahtev()
        izdaj_resenje(napravi_resenje(zahtev, self.user, datum_resenja=date(2026, 7, 30)), self.user)
        zahtev.refresh_from_db()
        self.assertEqual(zahtev.status, Zahtev.Status.PODNET)
        self.assertTrue(zahtev.dokument)

    def test_zahtev_sa_resenjem_se_ne_stornira(self):
        zahtev = self.zahtev()
        resenje = napravi_resenje(zahtev, self.user, datum_resenja=date(2026, 7, 30))
        izdaj_resenje(resenje, self.user)
        with self.assertRaises(ValidationError):
            storniraj_zahtev(zahtev, self.user)
        storniraj_resenje(resenje, self.user)
        storniraj_zahtev(zahtev, self.user)
        self.assertEqual(zahtev.status, Zahtev.Status.STORNIRAN)

    def test_iz_storniranog_zahteva_nema_resenja(self):
        zahtev = self.zahtev()
        storniraj_zahtev(zahtev, self.user)
        with self.assertRaises(ValidationError):
            napravi_resenje(zahtev, self.user)

    def test_zamena_prenosi_poslove_u_resenje(self):
        vrsta = VrstaZahteva.objects.get(kod='zamena-odsutnog')
        zahtev = self.zahtev(vrsta=vrsta, razlog='коришћења годишњег одмора',
                             datum_od=date(2026, 8, 3), datum_do=date(2026, 8, 14),
                             dodatni_podaci={'poslovi': 'директора Финансија'})
        tekst = ' '.join(build_zahtev_document(zahtev)['pasusi'])
        self.assertIn('предлажем да послове директора Финансија у периоду од 03.08.2026. до 14.08.2026. године '
                      'обавља запослени ЛАЗАР ЖИВАНОВИЋ', tekst)
        resenje = napravi_resenje(zahtev, self.user, datum_resenja=date(2026, 7, 30))
        dokument = build_document(resenje)
        self.assertEqual(dokument['podnaslov'], 'О ЗАМЕНИ ОДСУТНОГ ЗАПОСЛЕНОГ')
        self.assertIn('обавља послове директора Финансија', dokument['tacke'][0])
        self.assertIn('због коришћења годишњег одмора', ' '.join(dokument['obrazlozenje']))


class VidljivostZahtevaTests(ZahtevTestBase):
    def test_zahtevi_se_vide_po_centru(self):
        zahtev = self.zahtev()
        drugi = get_user_model().objects.create_user('bez-centra', password='test-pass')
        centar = get_user_model().objects.create_user('centar-43-z', password='test-pass')
        centar.allowed_center_codes = '43'
        centar.save(update_fields=['allowed_center_codes'])
        self.assertNotIn(zahtev, visible_zahtevi(drugi))
        self.assertIn(zahtev, visible_zahtevi(centar))


class EkraniZahtevaTests(ZahtevTestBase):
    def setUp(self):
        self.client.force_login(self.user)

    def _podaci(self, **kwargs):
        podaci = {'vrsta': self.vrsta_zahteva.pk, 'zaposleni': self.employee.pk, 'datum_zahteva': '28.07.2026',
                  'pismo': Pismo.CIRILICA, 'zaposleni_tekst': '', 'oj_naziv': '', 'radno_mesto': '',
                  'datum_od': '01.08.2026', 'datum_do': '31.08.2026', 'razlog': 'потребе посла',
                  'podnosilac': self.rukovodilac.pk, 'podnosilac_funkcija': 'Финансијски директор',
                  'odobrava': '', 'odobrava_funkcija': '', 'napomena': '',
                  'dani-TOTAL_FORMS': '0', 'dani-INITIAL_FORMS': '0',
                  'dani-MIN_NUM_FORMS': '0', 'dani-MAX_NUM_FORMS': '1000'}
        podaci.update(kwargs)
        return podaci

    def test_unos_dodeljuje_broj_i_odobrava(self):
        odgovor = self.client.post(reverse('hr:zahtev_create'), self._podaci())
        self.assertEqual(odgovor.status_code, 302, getattr(odgovor, 'context', None) and odgovor.context['form'].errors)
        zahtev = Zahtev.objects.get()
        self.assertEqual(zahtev.broj, '43-1')
        self.assertEqual(zahtev.odobrava, self.direktor)
        self.assertEqual(zahtev.odobrava_funkcija, 'Генерални директор')

    def test_zamena_trazi_poslove(self):
        vrsta = VrstaZahteva.objects.get(kod='zamena-odsutnog')
        odgovor = self.client.post(reverse('hr:zahtev_create'), self._podaci(vrsta=vrsta.pk))
        self.assertEqual(odgovor.status_code, 200)
        self.assertFalse(Zahtev.objects.exists())
        odgovor = self.client.post(reverse('hr:zahtev_create'), self._podaci(vrsta=vrsta.pk, dp_poslovi='директора Финансија'))
        self.assertEqual(odgovor.status_code, 302)
        self.assertEqual(Zahtev.objects.get().dodatni_podaci, {'poslovi': 'директора Финансија'})

    def test_isti_zahtev_za_vise_zaposlenih(self):
        podaci = {'vrsta': self.vrsta_zahteva.pk, 'datum_zahteva': '28.07.2026', 'pismo': Pismo.CIRILICA,
                  'datum_od': '01.08.2026', 'datum_do': '31.08.2026', 'podnosilac': self.rukovodilac.pk,
                  'podnosilac_funkcija': 'Финансијски директор', 'zaposleni': [self.employee.pk, self.rukovodilac.pk]}
        odgovor = self.client.post(reverse('hr:zahtev_bulk_create'), podaci)
        self.assertEqual(odgovor.status_code, 302)
        self.assertEqual(sorted(Zahtev.objects.values_list('broj', flat=True)), ['43-1', '43-2'])

    def test_resenja_za_oznacene_zahteve(self):
        prvi, drugi = self.zahtev(), self.zahtev(zaposleni=self.rukovodilac)
        napravi_resenje(drugi, self.user)
        odgovor = self.client.post(reverse('hr:zahtev_bulk_resenja'),
                                   {'zahtev': [prvi.pk, drugi.pk], 'datum_resenja': '30.07.2026'})
        self.assertEqual(odgovor.status_code, 302)
        self.assertEqual(sorted(Resenje.objects.values_list('broj', flat=True)), ['43-1/1', '43-2/1'])

    def test_dodaj_resenje_iz_zahteva(self):
        zahtev = self.zahtev()
        detalj = reverse('hr:zahtev_detail', args=[zahtev.pk])
        self.assertContains(self.client.get(detalj), 'id="dodaj-resenje"')
        odgovor = self.client.post(reverse('hr:zahtev_resenje_create', args=[zahtev.pk]), {'datum_resenja': '30.07.2026'})
        resenje = Resenje.objects.get()
        self.assertRedirects(odgovor, reverse('hr:resenje_detail', args=[resenje.pk]))
        self.assertEqual(resenje.broj, '43-1/1')
        self.assertNotContains(self.client.get(detalj), 'id="dodaj-resenje"')
        ponovo = self.client.post(reverse('hr:zahtev_resenje_create', args=[zahtev.pk]), {'datum_resenja': '30.07.2026'})
        self.assertRedirects(ponovo, detalj)
        self.assertEqual(Resenje.objects.count(), 1)

    def test_stornirano_resenje_ne_oslobadja_zahtev_za_grupno_dodavanje(self):
        zahtev = self.zahtev()
        resenje = napravi_resenje(zahtev, self.user)
        storniraj_resenje(resenje, self.user)
        self.client.post(reverse('hr:zahtev_bulk_resenja'),
                         {'zahtev': [zahtev.pk], 'datum_resenja': '30.07.2026'})
        self.assertEqual(zahtev.resenja.count(), 1)
        self.assertNotContains(self.client.get(reverse('hr:zahtev_detail', args=[zahtev.pk])), 'id="dodaj-resenje"')
        odgovor = self.client.get(reverse('hr:zahtev_list'), {'resenje': 'bez'})
        self.assertNotIn(zahtev, odgovor.context['zahtevi'])

    def test_kadrovi_ne_mogu_praviti_resenje_za_tudji_centar(self):
        from core.permissions import sync_kadrovi_permissions
        korisnik = get_user_model().objects.create_user('kadrovi-41', allowed_center_codes='41')
        korisnik.roles.add(sync_kadrovi_permissions()['role'])
        zahtev = self.zahtev()
        self.client.force_login(korisnik)
        odgovor = self.client.post(reverse('hr:zahtev_resenje_create', args=[zahtev.pk]), {'datum_resenja': '30.07.2026'})
        self.assertEqual(odgovor.status_code, 404)
        self.assertFalse(Resenje.objects.exists())

    def test_ekrani_se_otvaraju(self):
        zahtev = self.zahtev()
        resenje = napravi_resenje(zahtev, self.user, datum_resenja=date(2026, 7, 30))
        for naziv, args in (('hr:zahtev_list', []), ('hr:zahtev_detail', [zahtev.pk]), ('hr:zahtev_print', [zahtev.pk]),
                            ('hr:zahtev_create', []), ('hr:zahtev_bulk_create', []), ('hr:zahtev_edit', [zahtev.pk]),
                            ('hr:resenje_catalog', []), ('hr:resenje_edit', [resenje.pk])):
            self.assertEqual(self.client.get(reverse(naziv, args=args)).status_code, 200, naziv)
        odgovor = self.client.get(reverse('hr:resenje_detail', args=[resenje.pk]))
        self.assertContains(odgovor, reverse('hr:zahtev_detail', args=[zahtev.pk]))
        self.assertContains(self.client.get(reverse('hr:zahtev_detail', args=[zahtev.pk])), '43-1/1')

    def test_podnet_zahtev_se_ne_menja(self):
        zahtev = self.zahtev()
        podnesi_zahtev(zahtev, self.user)
        self.assertEqual(self.client.get(reverse('hr:zahtev_edit', args=[zahtev.pk])).status_code, 404)

    def test_resenje_po_zahtevu_ne_menja_broj_ni_zaposlenog(self):
        zahtev = self.zahtev()
        resenje = napravi_resenje(zahtev, self.user, datum_resenja=date(2026, 7, 30))
        podaci = {'vrsta': resenje.vrsta_id, 'zaposleni': self.rukovodilac.pk, 'broj': 'drugi-broj',
                  'datum_resenja': '30.07.2026', 'pismo': Pismo.CIRILICA, 'zaposleni_tekst': resenje.zaposleni_tekst,
                  'oj_naziv': resenje.oj_naziv, 'radno_mesto': '', 'datum_od': '01.08.2026', 'datum_do': '31.08.2026',
                  'napomena': '', 'dani-TOTAL_FORMS': '0', 'dani-INITIAL_FORMS': '0',
                  'dani-MIN_NUM_FORMS': '0', 'dani-MAX_NUM_FORMS': '1000'}
        odgovor = self.client.post(reverse('hr:resenje_edit', args=[resenje.pk]), podaci)
        self.assertEqual(odgovor.status_code, 302)
        resenje.refresh_from_db()
        self.assertEqual((resenje.broj, resenje.zaposleni, resenje.zahtev_broj), ('43-1/1', self.employee, '43-1'))
