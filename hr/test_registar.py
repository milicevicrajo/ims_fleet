"""Kadrovi na registru (plan prelaska na registar, korak 7): zaposleni pripada cvoru registra."""
import datetime

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from hr.access import visible_employees
from hr.models import Employee
from organizacija.models import DodelaUloge
from organizacija.services import zaposleni
from organizacija.services.importer import run_import
from organizacija.test_prava import centar, jedinica, uloga_sa_dozvolom
from organizacija.tests import ImportTestCase

NA_REGISTRU = override_settings(PRAVA_PO_REGISTRU={"kadrovi": True})


def radnik(sifra, oj):
    return Employee.objects.create(employee_code=sifra, first_name="Ime", last_name=f"Prezime{sifra}", position="Radnik",
                                   department_code=1, org_unit_code=oj, gender="M",
                                   date_of_birth=datetime.date(1980, 1, 1), date_of_joining=datetime.date(2020, 1, 1))


@NA_REGISTRU
class KadroviNaRegistruTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        self.u431, self.u4331, self.u41, self.institut = radnik(1, "431"), radnik(2, "4331"), radnik(3, "41"), radnik(4, "1")
        self.uloga = uloga_sa_dozvolom("kadrovi-centra", "employee_list", "hr:kadrovi_manage")
        self.korisnik = get_user_model().objects.create_user("kadrovi-43", password="x", allowed_center_codes="41")
        self.korisnik.roles.add(self.uloga)

    def svez(self):
        return get_user_model().objects.get(pk=self.korisnik.pk)

    def dodeli(self, **obuhvat):
        DodelaUloge.objects.create(korisnik=self.korisnik, uloga=self.uloga, vazi_od=datetime.date(2026, 1, 1),
                                   status=DodelaUloge.STATUS_AKTIVNA, **obuhvat)

    def test_zaposleni_dobija_cvor_iz_oj(self):
        self.u431.refresh_from_db()
        self.assertEqual(self.u431.org_node_id, jedinica("431"))  # pri cuvanju
        self.assertEqual(Employee.objects.get(pk=self.u4331.pk).org_node_id, centar("43"))  # prefiks centra
        self.assertEqual(Employee.objects.get(pk=self.u41.pk).org_node_id, centar("41"))
        self.assertIsNone(Employee.objects.get(pk=self.institut.pk).org_node_id)  # Institut kao celina
        self.assertEqual(zaposleni.cvor_oj("20", zaposleni.mape_registra()), centar("2"))
        self.assertEqual(zaposleni.povezi_zaposlene(), 0)  # nocno uskladjivanje — vec uskladjeno

    def test_obuhvat_iz_dodele(self):
        self.assertFalse(visible_employees(self.svez()).exists())  # stari centar 41 vise ne odlucuje
        self.dodeli(cvor_id=centar("43"))
        self.assertEqual(set(visible_employees(self.svez())), {self.u431, self.u4331})

    def test_cela_firma_vidi_i_institut(self):
        self.dodeli(cela_firma=True)
        self.assertEqual(visible_employees(self.svez()).count(), 4)

    def test_izmena_lokalnih_podataka_postuje_odobrenu_dodelu(self):
        from core.models import PermissionCode

        self.uloga.permissions.add(PermissionCode.objects.get_or_create(code="employee_update")[0])
        self.dodeli(cvor_id=centar("43"))
        self.client.force_login(self.korisnik)
        url = reverse("employee_update", args=[self.u431.pk])
        data = {"first_name": "Novo ime", "last_name": self.u431.last_name, "title": "dr",
                "org_unit_code": "41", "department_code": "41"}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.u431.refresh_from_db()
        self.assertEqual(self.u431.first_name, "Novo ime")
        self.assertTrue(self.u431.skip_hr_identity_update)
        self.assertEqual(self.u431.org_unit_code, "431")
        self.assertEqual(self.u431.org_node_id, jedinica("431"))
        self.assertEqual(self.client.post(reverse("employee_update", args=[self.u41.pk]), data).status_code, 404)
        DodelaUloge.objects.filter(korisnik=self.korisnik).delete()
        self.assertEqual(self.client.post(url, data).status_code, 404)

    def test_novi_nalog_zaposlenog_dobija_dodelu_centra(self):
        from core.models import Role
        from fleet.services.employee_user_profiles import create_user_profile_for_employee

        Role.objects.get_or_create(slug="zaposleni", defaults={"name": "Zaposleni"})
        korisnik, centar_oznaka, _ = create_user_profile_for_employee(self.u431, centers=["41", "43"])
        dodela = DodelaUloge.objects.get(korisnik=korisnik)
        self.assertEqual((dodela.cvor_id, dodela.status), (centar("43"), DodelaUloge.STATUS_AKTIVNA))
