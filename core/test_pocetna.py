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
