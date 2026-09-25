"""Plan prelaska na registar, korak 3: ekran dodela — odobravanje, rucna dodela, opoziv, istorija."""
import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse

from organizacija.models import DodelaUloge
from organizacija.services import dodele, flota, prava
from organizacija.services.importer import run_import
from organizacija.test_prava import centar, cvor, uloga_sa_dozvolom
from organizacija.tests import ImportTestCase

DOZVOLE_EKRANA = ("organizacija:dodele", "organizacija:dodele_korisnika", "organizacija:dodele_odobri",
                  "organizacija:dodela_opozovi")


class DodeleTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        flota.povezi(modul="finansije")
        User = get_user_model()
        self.uloga = uloga_sa_dozvolom("finansije-uloga", "finansije:dashboard")
        self.korisnik = User.objects.create_user("sa-centrom", password="x", allowed_center_codes="43")
        self.korisnik.roles.add(self.uloga)
        self.admin_uloga = uloga_sa_dozvolom("admin-dodela", *DOZVOLE_EKRANA)
        self.admin = User.objects.create_user("administrator", password="x")
        self.admin.roles.add(self.admin_uloga)
        prava.prevedi()

    def test_odobren_nacrt_postaje_aktivan_i_prevod_ga_ne_dira(self):
        self.assertEqual(dodele.odobri(self.korisnik, self.admin), 1)
        dodela = DodelaUloge.objects.get(korisnik=self.korisnik)
        self.assertEqual((dodela.status, dodela.odobrio), (DodelaUloge.STATUS_AKTIVNA, self.admin))
        self.assertTrue(prava.obuhvat(self.korisnik, "finansije:dashboard").centri)
        # Stara prava se promene, ali odobren korisnik ostaje kako ga je administrator potvrdio.
        self.korisnik.allowed_center_codes = "41"
        self.korisnik.save()
        self.assertEqual(prava.prevedi()["odobreni"], 1)
        self.assertEqual(list(DodelaUloge.objects.filter(korisnik=self.korisnik).values_list("cvor_id", flat=True)),
                         [centar("43")])

    def test_opoziv_cuva_istoriju_a_nacrt_se_brise(self):
        nacrt = DodelaUloge.objects.get(korisnik=self.korisnik)
        self.assertEqual(dodele.opozovi(nacrt, self.admin), "obrisan")
        rucna = dodele.dodaj(self.korisnik, self.uloga, centar("41"), False, datetime.date(2026, 1, 1), None, self.admin)
        self.assertEqual(dodele.opozovi(rucna, self.admin, dan=datetime.date(2026, 6, 1)), "opozvana")
        rucna.refresh_from_db()
        self.assertEqual((rucna.vazi_do, rucna.opozvao), (datetime.date(2026, 6, 1), self.admin))
        self.assertTrue(prava.obuhvat(self.korisnik, "finansije:dashboard", dan=datetime.date(2026, 7, 1)).prazan)
        self.assertTrue(prava.obuhvat(self.korisnik, "finansije:dashboard", dan=datetime.date(2026, 5, 1)).centri)

    def test_ekran_trazi_dozvolu(self):
        self.client.force_login(self.korisnik)
        self.assertEqual(self.client.get(reverse("organizacija:dodele")).status_code, 403)
        self.client.force_login(self.admin)
        odgovor = self.client.get(reverse("organizacija:dodele"))
        self.assertContains(odgovor, "sa-centrom")
        self.assertContains(self.client.get(reverse("organizacija:dodele") + "?senka=1"), "Senka uključena")

    def test_rucna_dodela_kroz_formu_i_zabrana_duplikata(self):
        self.client.force_login(self.admin)
        adresa = reverse("organizacija:dodele_korisnika", args=[self.korisnik.pk])
        self.assertContains(self.client.get(adresa), "Nacrt")
        podaci = {"uloga": self.uloga.pk, "obuhvat": str(cvor("410001")), "vazi_od": "2026-01-01"}
        self.assertEqual(self.client.post(adresa, podaci).status_code, 302)
        dodela = DodelaUloge.objects.get(korisnik=self.korisnik, cvor_id=cvor("410001"))
        self.assertEqual((dodela.status, dodela.izvor), (DodelaUloge.STATUS_AKTIVNA, DodelaUloge.IZVOR_RUCNO))
        self.assertContains(self.client.post(adresa, podaci), "već ima tu ulogu")
        # Neaktivna sifra se ne nudi (odluka 8), a uloga koju korisnik nema ne moze da se izabere.
        self.assertNotIn(str(cvor("431112")), {v for _, g in dodele.izbor_obuhvata()[1:] for v, _ in g})
        tudja = uloga_sa_dozvolom("tudja", "potrazivanja:dashboard")
        odgovor = self.client.post(adresa, {**podaci, "uloga": tudja.pk, "obuhvat": "firma"})
        self.assertEqual(odgovor.status_code, 200)
        self.assertFalse(DodelaUloge.objects.filter(uloga=tudja).exists())

    def test_odobravanje_i_opoziv_kroz_ekran(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("organizacija:dodele_odobri", args=[self.korisnik.pk]))
        dodela = DodelaUloge.objects.get(korisnik=self.korisnik)
        self.assertEqual(dodela.status, DodelaUloge.STATUS_AKTIVNA)
        self.assertEqual(self.client.get(reverse("organizacija:dodela_opozovi", args=[dodela.pk])).status_code, 405)
        self.client.post(reverse("organizacija:dodela_opozovi", args=[dodela.pk]))
        dodela.refresh_from_db()
        self.assertIsNotNone(dodela.opozvano)
        self.assertContains(self.client.get(reverse("organizacija:dodele_korisnika", args=[self.korisnik.pk])), "Opozvana")
