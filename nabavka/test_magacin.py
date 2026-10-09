"""Nabavka → Stanje u magacinu (09.10.2026.): pregled pogleda dbo.nbv_magacin."""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from core.models import PermissionCode, Role
from nabavka.services import magacin

D = Decimal
# god, sif_mag, naz_mag, mesto, oj, sif_art, naz_art, sif_vrsart, naz_vrsart, kolul, koliz, vrulnab, vriznab, mag_cena
IZVOR = [
    ("2026", 14, "Centralni magacin   ", "Beograd  ", 81, "100 ", "Rukavice ", "HTZ ", "HTZ oprema", D("10"), D("4"), D("1000.00"), D("400.00"), D("100.00")),
    ("2026", 14, "Centralni magacin   ", "Beograd  ", 81, "101 ", "Papir A4 ", "KAN ", "Kancelarijski", D("5"), D("5"), D("500.00"), D("500.00"), D("100.00")),
    ("2026", 2, "GOTOVI PROIZVODI -KOTVE", "Beograd", 44, "10574", "CAURA SPB S19/16", "GOT", "GOTOVI PROIZVODI", D("6"), D("4"), D("354311.10"), D("236207.40"), D("59051.85")),
]


class Kursor:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        assert "dbo.nbv_magacin" in sql

    def fetchall(self):
        return IZVOR


class Veza:
    def cursor(self):
        return Kursor()


@patch.dict("nabavka.services.magacin.connections", {"server_db": Veza()})
class MagacinTests(TestCase):
    def test_stanje_je_ulaz_minus_izlaz_i_filteri(self):
        p = magacin.pregled()
        self.assertEqual([(r["sifra"], r["stanje"], r["vrednost"]) for r in p["redovi"]],
                         [("100", D("6"), D("600.00")), ("10574", D("2"), D("118103.70"))])  # bez stanja nula, po magacinu
        self.assertEqual(p["ukupno"]["vrednost"], D("118703.70"))
        self.assertEqual([r["sifra"] for r in magacin.pregled(stanje="nula")["redovi"]], ["101"])
        self.assertEqual(len(magacin.pregled(stanje="sve", magacin="14")["redovi"]), 2)
        self.assertEqual([r["sifra"] for r in magacin.pregled(vrsta="HTZ")["redovi"]], ["100"])
        self.assertEqual(p["magacini"], [(2, "GOTOVI PROIZVODI -KOTVE", "Beograd"), (14, "Centralni magacin", "Beograd")])

    def test_ekran_i_dozvola(self):
        korisnik = get_user_model().objects.create_user("magacioner", password="x")
        self.client.force_login(korisnik)
        self.assertEqual(self.client.get(reverse("nabavka:magacin")).status_code, 403)
        uloga = Role.objects.create(name="Magacin", slug="magacin-pregled")
        uloga.permissions.add(PermissionCode.objects.create(code="nabavka:magacin"))
        korisnik.roles.add(uloga)
        odgovor = self.client.get(reverse("nabavka:magacin"), {"magacin": "14"})
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, "Rukavice")
        self.assertNotContains(odgovor, "CAURA SPB")
        self.assertContains(odgovor, "Stanje u magacinu")
        with patch("nabavka.services.magacin.procitaj", side_effect=DatabaseError("x")):
            self.assertContains(self.client.get(reverse("nabavka:magacin")), "nije dostupan")

    def test_uloga_nabavka_dobija_dozvolu(self):
        from core.permissions import sync_permission_codes

        sync_permission_codes()
        self.assertTrue(Role.objects.get(slug="nabavka").permissions.filter(code="nabavka:magacin").exists())
