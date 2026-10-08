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

    def test_pododeljenje_ide_u_svoju_jedinicu(self):
        # 08.10.2026.: OJ 4331/4332 su ljudi Laboratorije za puteve (433), ne celog centra 43.
        mape = ({"43": "c43", "41": "c41", "42": "c42"},
                {"433": ("j433", "c43"), "411": ("j411", "c41"), "4110": ("j4110", "c41")})
        self.assertEqual(zaposleni.cvor_oj("4331", mape), "j433")
        self.assertEqual(zaposleni.cvor_oj("4332", mape), "j433")
        self.assertEqual(zaposleni.cvor_oj("41101", mape), "j4110")  # najduzi prefiks jedinice
        self.assertEqual(zaposleni.cvor_oj("423", mape), "c42")      # bez svoje jedinice — centar
        self.assertEqual(zaposleni.cvor_oj("43", mape), "c43")
        self.assertIsNone(zaposleni.cvor_oj("10", mape))

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


@NA_REGISTRU
class ZahtevZaSebeTests(ImportTestCase):
    """Uloga Zaposleni podnosi zahtev za sebe; dodela na centar (zbog Flote) ne otvara kolege."""

    def setUp(self):
        from hr.access import DOZVOLE_ZAHTEVA_ZA_SEBE

        super().setUp()
        run_import(company=1)
        self.ja, self.kolega, self.direktor = radnik(1, "431"), radnik(2, "4331"), radnik(3, "1")
        self.korisnik = get_user_model().objects.create_user("zaposleni-1", password="x", employee=self.ja)
        uloga = uloga_sa_dozvolom("zaposleni-test", *DOZVOLE_ZAHTEVA_ZA_SEBE)
        self.korisnik.roles.add(uloga)
        DodelaUloge.objects.create(korisnik=self.korisnik, uloga=uloga, cvor_id=centar("43"), vazi_od=datetime.date(2026, 1, 1),
                                   status=DodelaUloge.STATUS_AKTIVNA)
        self.client.force_login(self.korisnik)

    def podaci(self, zaposleni):
        from hr.models import VrstaZahteva

        return {"vrsta": VrstaZahteva.objects.get(kod="prekovremeni-rad").pk, "zaposleni": zaposleni.pk,
                "datum_zahteva": "28.07.2026", "pismo": "latinica", "datum_od": "01.08.2026", "datum_do": "31.08.2026",
                "razlog": "potrebe posla", "podnosilac": self.ja.pk, "podnosilac_funkcija": "Radnik",
                "odobrava": self.direktor.pk, "odobrava_funkcija": "Generalni direktor",
                "dani-TOTAL_FORMS": "0", "dani-INITIAL_FORMS": "0", "dani-MIN_NUM_FORMS": "0", "dani-MAX_NUM_FORMS": "1000"}

    def test_zaposleni_podnosi_zahtev_samo_za_sebe(self):
        from hr.models import Zahtev
        from hr.services.zahtevi import visible_zahtevi

        self.assertFalse(visible_employees(self.korisnik).exists())  # dozvole zahteva ne daju obuhvat
        forma = self.client.get(reverse("hr:zahtev_create")).context["form"]
        self.assertEqual(list(forma.fields["zaposleni"].queryset), [self.ja])
        self.assertEqual((forma.initial["zaposleni"], forma.initial["podnosilac"]), (self.ja.pk, self.ja.pk))

        odgovor = self.client.post(reverse("hr:zahtev_create"), self.podaci(self.kolega))
        self.assertIn("zaposleni", odgovor.context["form"].errors)
        odgovor = self.client.post(reverse("hr:zahtev_create"), self.podaci(self.ja))
        zahtev = Zahtev.objects.get()
        self.assertRedirects(odgovor, reverse("hr:zahtev_detail", args=[zahtev.pk]))
        self.client.post(reverse("hr:zahtev_podnesi", args=[zahtev.pk]))
        self.assertEqual(Zahtev.objects.get().status, Zahtev.Status.PODNET)

        from hr.services.zahtevi import dodeli_broj, pripremi_zahtev

        tudji = Zahtev(vrsta=zahtev.vrsta, zaposleni=self.kolega, datum_zahteva=zahtev.datum_zahteva, podnosilac=self.kolega,
                       odobrava=self.direktor, created_by=get_user_model().objects.create_superuser("admin", password="x"))
        pripremi_zahtev(tudji)
        dodeli_broj(tudji)
        tudji.save()
        self.assertEqual(list(visible_zahtevi(self.korisnik)), [zahtev])
        self.assertEqual(self.client.get(reverse("hr:zahtev_detail", args=[tudji.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("hr:zahtev_storniraj", args=[zahtev.pk])).status_code, 403)
