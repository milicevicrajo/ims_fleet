"""Uloga Rukovodilac: jedna dodela na cvor daje isti obuhvat u Finansijama, Floti, Kadrovima i Potrazivanjima."""
import datetime

from django.contrib.auth import get_user_model
from django.test import override_settings

from core.mixins import user_has_role_permission
from core.permissions import RUKOVODILAC_CODES, sync_rukovodilac_role
from finansije import access as finansije_access
from fleet.support import obuhvat as obuhvat_flote
from hr.access import visible_employees
from hr.test_registar import radnik
from organizacija.models import DodelaUloge
from organizacija.services import prava
from organizacija.services.importer import run_import
from organizacija.test_prava import centar
from organizacija.tests import ImportTestCase
from potrazivanja import access as potrazivanja_access

NA_REGISTRU = override_settings(PRAVA_PO_REGISTRU={"finansije": True, "flota": True, "kadrovi": True,
                                                   "potrazivanja": True})


@NA_REGISTRU
class RukovodilacTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        self.uloga = sync_rukovodilac_role()
        self.korisnik = get_user_model().objects.create_user("rukovodilac-43", password="x")
        self.korisnik.roles.add(self.uloga)
        self.u431, self.u41 = radnik(1, "431"), radnik(2, "41")

    def svez(self):
        return get_user_model().objects.get(pk=self.korisnik.pk)

    def test_samo_citanje(self):
        kodovi = set(self.uloga.permissions.values_list("code", flat=True))
        self.assertEqual(kodovi, set(RUKOVODILAC_CODES))
        self.assertFalse({"finansije:view_all", "potrazivanja:view_all", "finansije:sync_run", "finansije:bank_list",
                          "finansije:sef_list", "putninalog_update", "vehicle_update", "employee_update"} & kodovi)
        self.assertNotIn("rukovodilac", prava.ULOGE_CELE_FIRME)  # obuhvat je cvor iz dodele, ne cela firma
        sync_rukovodilac_role()
        self.assertEqual(self.uloga.permissions.count(), len(RUKOVODILAC_CODES))  # ponovljivo

    def test_bez_dodele_ne_vidi_nista(self):
        korisnik = self.svez()
        self.assertTrue(user_has_role_permission(korisnik, "finansije:dashboard"))
        self.assertEqual(prava.sifre_obuhvata(finansije_access._obuhvat(korisnik)), set())
        self.assertEqual(potrazivanja_access.sifre_u_obuhvatu(korisnik), set())
        self.assertTrue(obuhvat_flote.obuhvat(korisnik).prazan)
        self.assertFalse(visible_employees(korisnik).exists())

    def test_dodela_na_centar_vazi_u_svim_modulima(self):
        DodelaUloge.objects.create(korisnik=self.korisnik, uloga=self.uloga, cvor_id=centar("43"),
                                   vazi_od=datetime.date(2026, 1, 1), status=DodelaUloge.STATUS_AKTIVNA)
        korisnik = self.svez()
        sifre = prava.sifre_obuhvata(finansije_access._obuhvat(korisnik))
        self.assertIn("430111", sifre)
        self.assertNotIn("410001", sifre)
        self.assertFalse(finansije_access.can_view_all(korisnik))
        self.assertEqual(potrazivanja_access.sifre_u_obuhvatu(korisnik), sifre)
        self.assertFalse(potrazivanja_access.can_view_all(korisnik))
        self.assertEqual(obuhvat_flote.obuhvat(korisnik).centri, {centar("43")})
        self.assertEqual(obuhvat_flote.centri(korisnik), {"43"})
        self.assertEqual(list(visible_employees(korisnik)), [self.u431])
