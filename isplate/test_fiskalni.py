"""Putni nalozi: dodavanje računa pri pravdanju i knjiženje (Isplate), zaključavanje (Nabavka)."""
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import ActivityLog, OrganizationalUnit, PermissionCode, Role
from isplate.tests import create_employee, create_order
from nabavka.models import FiskalniRacun
from nabavka.services import fiskalni
from nabavka.test_fiskalni import LINK, lazni_suf, napravi_link

PRAVDANJE = ("isplate:putni_nalozi_pravdanje", "isplate:putni_nalog_racuni", "isplate:putni_nalog_racun_dodaj",
             "isplate:putni_nalog_racun_ukloni", "isplate:putni_nalog_opravdaj")
ISPLATE = ("isplate:fiskalni_putni_nalozi", "isplate:fiskalni_proknjizi", "isplate:fiskalni_izvoz")
NABAVKA = ("nabavka:fiskalni_detail", "nabavka:fiskalni_update", "nabavka:fiskalni_delete")


def korisnik_sa(ime, *kodovi):
    uloga = Role.objects.create(name=ime, slug=ime)
    for kod in kodovi:
        uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
    korisnik = get_user_model().objects.create_user(ime, password="x")
    korisnik.roles.add(uloga)
    return korisnik


class FiskalniPutnogNalogaTests(TestCase):
    def setUp(self):
        self.nalog = create_order(employee=create_employee(), order_number="43/2026-7", center="43")
        self.nikolina = korisnik_sa("nikolina", *PRAVDANJE)
        self.knjigovodja = korisnik_sa("bilja", *ISPLATE, *NABAVKA)
        self.client.force_login(self.nikolina)

    def ocitaj(self, link=LINK, nalog=None):
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            return self.client.post(reverse("isplate:putni_nalog_racun_dodaj", args=[(nalog or self.nalog).pk]), {"link": link},
                                    HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_novi_racun_dobija_sifru_posla_naloga(self):
        odgovor = self.ocitaj()
        self.assertEqual(odgovor.status_code, 200, odgovor.content)
        self.assertFalse(odgovor.json()["vezan_postojeci"])
        racun = FiskalniRacun.objects.get()
        self.assertEqual((racun.putni_nalog, racun.job_code, racun.created_by), (self.nalog, self.nalog.job_code, self.nikolina))
        self.assertEqual(odgovor.json()["iznos"], "1.804,50")  # kao poruka posle učitavanja u Nabavci
        racuni = self.client.get(reverse("isplate:putni_nalog_racuni", args=[self.nalog.pk])).json()
        self.assertEqual([r["broj"] for r in racuni["racuni"]], [racun.broj_racuna])
        self.assertEqual(racuni["zbir"], "1.804,50")
        self.assertEqual(self.client.get(reverse("isplate:putni_nalozi_pravdanje")).status_code, 200)
        tabela = self.client.get(reverse("isplate:putni_nalozi_pravdanje"), {"draw": 1}).json()  # DataTables
        self.assertEqual((tabela["recordsFiltered"], tabela["data"][0]["nalog"]), (1, "<strong>43/2026-7</strong>"))
        self.assertIn("1 · 1.804,50", tabela["data"][0]["racuni"])
        self.assertIn("Opravdaj", tabela["data"][0]["akcije"])

    def test_postojeci_racun_se_samo_veze_i_zadrzava_sifru(self):
        druga = OrganizationalUnit.objects.create(code="410001", name="Druga", center="41")
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            fiskalni.upisi(LINK, druga, self.knjigovodja)  # učitan ranije u Nabavci
        odgovor = self.ocitaj()
        self.assertTrue(odgovor.json()["vezan_postojeci"])
        racun = FiskalniRacun.objects.get()
        self.assertEqual((racun.putni_nalog, racun.job_code), (self.nalog, druga))
        self.assertEqual(self.ocitaj().status_code, 400)  # već je na ovom nalogu

    def test_racun_sa_drugog_naloga_i_storniran_nalog_se_odbijaju(self):
        self.ocitaj()
        drugi = create_order(employee=create_employee(code=9002), order_number="43/2026-8", center="43")
        odgovor = self.ocitaj(nalog=drugi)
        self.assertEqual(odgovor.status_code, 400)
        self.assertIn("43/2026-7", odgovor.json()["poruka"])
        drugi.storniran = True
        drugi.save(update_fields=["storniran"])
        odgovor = self.ocitaj(link=napravi_link(brojac=99), nalog=drugi)
        self.assertEqual(odgovor.status_code, 400)
        self.assertIn("storniran", odgovor.json()["poruka"])

    def test_skidanje_sa_naloga_samo_dok_nije_proknjizen(self):
        self.ocitaj()
        racun = FiskalniRacun.objects.get()
        fiskalni.oznaci_proknjizeno(racun, self.knjigovodja)
        self.assertEqual(self.client.post(reverse("isplate:putni_nalog_racun_ukloni", args=[self.nalog.pk, racun.pk])).status_code, 400)
        racun.refresh_from_db()
        self.assertEqual(racun.putni_nalog, self.nalog)  # proknjižen ostaje
        fiskalni.oznaci_proknjizeno(racun, self.knjigovodja, False)
        self.client.post(reverse("isplate:putni_nalog_racun_ukloni", args=[self.nalog.pk, racun.pk]))
        racun.refresh_from_db()
        self.assertIsNone(racun.putni_nalog)
        self.assertTrue(FiskalniRacun.objects.filter(pk=racun.pk).exists())  # ostaje u Nabavci

    def test_opravdan_nalog_je_zakljucan(self):
        self.ocitaj()
        odgovor = self.client.post(reverse("isplate:putni_nalog_opravdaj", args=[self.nalog.pk]), {"next": "https://zlo.example/"})
        self.assertRedirects(odgovor, reverse("isplate:putni_nalozi_pravdanje"), fetch_redirect_response=False)  # samo unutar aplikacije
        self.nalog.refresh_from_db()
        self.assertTrue(self.nalog.opravdan)
        odgovor = self.ocitaj(link=napravi_link(brojac=77))
        self.assertEqual(odgovor.status_code, 400)
        self.assertIn("opravdan", odgovor.json()["poruka"])
        racun = FiskalniRacun.objects.get()
        self.assertEqual(self.client.post(reverse("isplate:putni_nalog_racun_ukloni", args=[self.nalog.pk, racun.pk])).status_code, 400)
        racuni = self.client.get(reverse("isplate:putni_nalog_racuni", args=[self.nalog.pk])).json()
        self.assertTrue(racuni["zakljucan"])
        self.assertEqual(racuni["racuni"][0]["ukloni_url"], "")
        tabela = self.client.get(reverse("isplate:putni_nalozi_pravdanje"), {"draw": 1}).json()
        self.assertEqual(tabela["recordsFiltered"], 0)  # podrazumevano neopravdani
        tabela = self.client.get(reverse("isplate:putni_nalozi_pravdanje"), {"draw": 1, "status": "svi"}).json()
        self.assertNotIn("Opravdaj", tabela["data"][0]["akcije"])

    def test_opravdavanje_iz_tabele(self):
        odgovor = self.client.post(reverse("isplate:putni_nalog_opravdaj", args=[self.nalog.pk]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertTrue(odgovor.json()["ok"])
        self.nalog.refresh_from_db()
        self.assertTrue(self.nalog.opravdan)

    def test_ucitavanje_iz_naloga_za_isplatu(self):
        """U Isplati neoporezovanih svaki nalog ima dugme za fiskalne račune (isti prozor kao na pravdanju)."""
        self.nikolina.roles.first().permissions.add(PermissionCode.objects.get_or_create(code="isplate:neoporezive_isplate")[0])
        strana = self.client.get(reverse("isplate:neoporezive_isplate"))
        self.assertContains(strana, "Dodaj račun")
        self.assertContains(strana, reverse("isplate:putni_nalog_racun_dodaj", args=[self.nalog.pk]))
        self.assertContains(strana, 'id="ispRacuniModal"')
        self.ocitaj()
        self.assertContains(self.client.get(reverse("isplate:neoporezive_isplate")), "1 · 1.804,50")
        self.client.force_login(korisnik_sa("blagajnik", "isplate:neoporezive_isplate"))  # bez prava na račune
        self.assertNotContains(self.client.get(reverse("isplate:neoporezive_isplate")), 'id="ispRacuniModal"')

    def test_isplate_knjizenje(self):
        self.ocitaj()
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):  # račun iz Nabavke, bez naloga
            fiskalni.upisi(napravi_link(brojac=55), self.nalog.job_code, self.knjigovodja)
        self.client.force_login(self.knjigovodja)
        spisak = self.client.get(reverse("isplate:fiskalni_putni_nalozi"))
        self.assertEqual(spisak.context["zbir"]["broj"], 1)  # samo računi sa putnih naloga
        tabela = self.client.get(reverse("isplate:fiskalni_putni_nalozi"), {"draw": 1}).json()  # DataTables
        self.assertEqual((tabela["recordsTotal"], tabela["recordsFiltered"], tabela["zbir"]["iznos"]), (1, 1, "1.804,50"))
        self.assertIn("43/2026-7", tabela["data"][0]["nalog"])
        self.assertNotIn("disabled", tabela["data"][0]["knjizenje"])
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_putni_nalozi"),
                                         {"draw": 2, "search[value]": "nema-takvog"}).json()["recordsFiltered"], 0)
        racun = FiskalniRacun.objects.get(putni_nalog=self.nalog)
        odgovor = self.client.post(reverse("isplate:fiskalni_proknjizi", args=[racun.pk]), {"proknjizeno": "1"}).json()
        self.assertTrue(odgovor["proknjizeno"])
        racun.refresh_from_db()
        self.assertEqual((racun.proknjizeno, racun.proknjizio), (True, self.knjigovodja))
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_putni_nalozi")).context["zbir"]["broj"], 0)  # podrazumevano neproknjiženi
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_putni_nalozi"), {"knjizenje": "da"}).context["zbir"]["broj"], 1)
        self.client.post(reverse("isplate:fiskalni_proknjizi", args=[racun.pk]), {"proknjizeno": "0"})
        racun.refresh_from_db()
        self.assertEqual((racun.proknjizeno, racun.proknjizio, racun.proknjizeno_at), (False, None, None))
        self.assertTrue(ActivityLog.objects.filter(action=ActivityLog.ACTION_MANUAL, object_pk=str(racun.pk),
                                                   description__contains="Poništena").exists())
        izvoz = self.client.get(reverse("isplate:fiskalni_izvoz"), {"knjizenje": "sve"})
        self.assertEqual(izvoz.status_code, 200)
        self.assertIn("spreadsheetml", izvoz["Content-Type"])

    def test_proknjizen_racun_se_ne_menja_ni_brise_u_nabavci(self):
        self.ocitaj()
        racun = FiskalniRacun.objects.get()
        fiskalni.oznaci_proknjizeno(racun, self.knjigovodja)
        self.client.force_login(self.knjigovodja)
        detalj = self.client.get(reverse("nabavka:fiskalni_detail", args=[racun.pk]))
        self.assertContains(detalj, "Putni nalog")
        self.assertContains(detalj, "43/2026-7")
        self.assertNotContains(detalj, "Obriši račun")
        self.client.post(reverse("nabavka:fiskalni_delete", args=[racun.pk]))
        self.client.post(reverse("nabavka:fiskalni_update", args=[racun.pk]), {"akcija": "obrada", "napomena": "izmena"})
        racun.refresh_from_db()
        self.assertEqual(racun.napomena, "")
        self.assertTrue(FiskalniRacun.objects.filter(pk=racun.pk).exists())

    def test_bez_dozvole(self):
        drugi = get_user_model().objects.create_user("bez", password="x")
        self.client.force_login(drugi)
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_putni_nalozi")).status_code, 403)
        self.assertEqual(self.client.get(reverse("isplate:putni_nalozi_pravdanje")).status_code, 403)
        self.assertEqual(self.ocitaj().status_code, 403)
        self.assertEqual(Decimal("0"), sum((r.iznos for r in FiskalniRacun.objects.all()), Decimal("0")))
