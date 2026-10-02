"""Početna strana aplikacije: posle prijave, bez bočnog menija, moduli po dozvolama, uloge i dozvole."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

from core.models import PermissionCode, Role


class PocetnaTests(TestCase):
    def setUp(self):
        self.korisnik = get_user_model().objects.create_user("pera", password="lozinka-123")
        uloga = Role.objects.create(name="Nabavka — referent", slug="nabavka-referent")
        for kod in ("nabavka:dashboard", "nabavka:case_list"):
            uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        self.korisnik.roles.add(uloga)

    def test_prijava_vodi_na_pocetnu(self):
        self.assertEqual(resolve(settings.LOGIN_REDIRECT_URL).view_name, "pocetna")
        odgovor = self.client.post(reverse("login"), {"username": "pera", "password": "lozinka-123"})
        self.assertRedirects(odgovor, reverse("pocetna"), fetch_redirect_response=False)
        self.assertEqual(reverse("dashboard"), "/flota/")  # kontrolna tabla Flote je i dalje ista ruta

    def test_moduli_uloge_i_dozvole(self):
        self.client.force_login(self.korisnik)
        odgovor = self.client.get(reverse("pocetna"))
        self.assertEqual(odgovor.status_code, 200)
        moduli = {m["slug"]: m for m in odgovor.context["moduli"]}
        self.assertTrue(moduli["nabavka"]["dostupan"])
        self.assertTrue(moduli["kadrovi"]["dostupan"])  # Kadrovi → Pregled vide svi
        self.assertFalse(moduli["finansije"]["dostupan"])
        self.assertFalse(moduli["administracija"]["dostupan"])
        self.assertIn(f"{reverse('switch_app', args=['nabavka'])}?next={reverse('nabavka:dashboard')}", moduli["nabavka"]["url"])
        self.assertEqual(odgovor.context["broj_dozvola"], 2)
        self.assertEqual(odgovor.context["dozvole"], [("Nabavka", ["nabavka:case_list", "nabavka:dashboard"])])
        self.assertContains(odgovor, "Nabavka — referent")
        self.assertContains(odgovor, "Nemate pristup")
        self.assertNotContains(odgovor, 'id="sidebarnav"')  # bez bočnog menija
        self.assertContains(odgovor, f'href="{reverse("pocetna")}"')  # logo i „Početna” u zaglavlju

    def test_administrator_vidi_sve_module(self):
        admin = get_user_model().objects.create_superuser("admin", password="x")
        self.client.force_login(admin)
        odgovor = self.client.get(reverse("pocetna"))
        self.assertTrue(all(m["dostupan"] for m in odgovor.context["moduli"]))
        self.assertContains(odgovor, "Administrator")

    def test_neprijavljen_ide_na_prijavu(self):
        self.assertRedirects(self.client.get(reverse("pocetna")), f"{settings.LOGIN_URL}?next=/", fetch_redirect_response=False)

    def dodeli_samo(self, *kodovi, aktivna=True):
        self.korisnik.roles.clear()
        uloga = Role.objects.create(name="Pojedinačni ekrani", slug="ekrani", is_active=aktivna)
        for kod in kodovi:
            uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        self.korisnik.roles.add(uloga)
        self.client.force_login(self.korisnik)

    def test_ekran_bez_pocetne_dozvole_modula(self):
        self.dodeli_samo("arhiva:pisarnica", "nabavka:case_list", "finansije:ledger")
        odgovor = self.client.get(reverse("pocetna"))
        moduli = {m["slug"]: m for m in odgovor.context["moduli"]}
        for slug, ruta in [("arhiva", "arhiva:pisarnica"), ("nabavka", "nabavka:case_list"),
                           ("finansije", "finansije:ledger")]:
            modul = moduli[slug]
            self.assertFalse(modul["dostupan"])
            self.assertTrue(modul["ima_pristup"])
            self.assertEqual(len(modul["ekrani"]), 1)
            link = modul["ekrani"][0]["url"]
            self.assertContains(odgovor, f'href="{link}"')
            self.assertRedirects(self.client.get(link), reverse(ruta), fetch_redirect_response=False)
            self.assertEqual(self.client.session["current_app"], slug)
        self.assertEqual(odgovor.context["broj_dostupnih"], sum(m["ima_pristup"] for m in moduli.values()))

    def test_neaktivna_uloga_i_dozvola_akcije_ne_nude_ekran(self):
        self.dodeli_samo("arhiva:pisarnica", aktivna=False)
        odgovor = self.client.get(reverse("pocetna"))
        self.assertFalse(next(m for m in odgovor.context["moduli"] if m["slug"] == "arhiva")["ima_pristup"])
        self.korisnik.roles.clear()
        uloga = Role.objects.create(name="Akcija", slug="akcija")
        uloga.permissions.add(PermissionCode.objects.get_or_create(code="arhiva:akt_add")[0])
        self.korisnik.roles.add(uloga)
        odgovor = self.client.get(reverse("pocetna"))
        self.assertFalse(next(m for m in odgovor.context["moduli"] if m["slug"] == "arhiva")["ima_pristup"])

    def test_stvarni_kod_dozvole_za_uf_stavke_i_robu(self):
        self.dodeli_samo("nabavka:euf_invoice_list")
        odgovor = self.client.get(reverse("pocetna"))
        modul = next(m for m in odgovor.context["moduli"] if m["slug"] == "nabavka")
        self.assertEqual({e["naziv"] for e in modul["ekrani"]}, {"Preuzete EUF", "UF stavke", "Roba"})

    def test_sef_trazi_i_obuhvat_cele_firme(self):
        from unittest.mock import patch
        self.dodeli_samo("finansije:sef_list")
        for obuhvat in [False, True]:
            with self.subTest(obuhvat=obuhvat), patch("finansije.access.can_view_all", return_value=obuhvat):
                odgovor = self.client.get(reverse("pocetna"))
                modul = next(m for m in odgovor.context["moduli"] if m["slug"] == "finansije")
                self.assertEqual(modul["ima_pristup"], obuhvat)

    def test_katalog_ekrana_sadrzi_ispravne_rute(self):
        from core.pocetna_ekrani import EKRANI
        for ekrani in EKRANI.values():
            for ruta, _, argumenti, _ in ekrani:
                self.assertEqual(resolve(reverse(ruta, kwargs=argumenti)).view_name, ruta)
