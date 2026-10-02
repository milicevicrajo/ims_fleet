"""Kadrovi → Pregled: početna strana modula (brojke i spiskovi samo uz dozvole, u obuhvatu)."""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from hr.models import AnnualLeaveDecision, Employee, SickLeave
from hr.services.pregled import pregled
from hr.ugovori_models import UgovorZaposlenog


def zaposleni(sifra, prezime, pol="F", aktivan=True, zaposlen=datetime.date(2020, 1, 1)):
    return Employee.objects.create(employee_code=sifra, original_full_name=prezime.upper(), first_name="Ana",
                                   last_name=prezime, position="Inženjer", department_code=1, gender=pol,
                                   date_of_birth=datetime.date(1990, 1, 1), date_of_joining=zaposlen, is_active=aktivan)


class KadroviPregledTests(TestCase):
    def setUp(self):
        self.danas = timezone.localdate()
        self.ana = zaposleni(1, "Anić")
        self.marko = zaposleni(2, "Marković", pol="M", zaposlen=self.danas - datetime.timedelta(days=5))
        zaposleni(3, "Bivši", aktivan=False)
        AnnualLeaveDecision.objects.create(year=self.danas.year, employee_code=1, employee=self.ana, last_seen_at=timezone.now(),
                                           source_start_key="k1", start_date=self.danas - datetime.timedelta(days=2),
                                           end_date=self.danas + datetime.timedelta(days=3), approved_days=5)
        SickLeave.objects.create(rfzo_id="r1", employee=self.marko, personal_number="0000000000002",
                                 start_date=self.danas - datetime.timedelta(days=1), source_status="Otvoreno",
                                 source_date=self.danas)
        SickLeave.objects.create(rfzo_id="r2", employee=self.ana, personal_number="0000000000001",  # završeno
                                 start_date=self.danas - datetime.timedelta(days=30), end_date=self.danas - datetime.timedelta(days=20),
                                 source_status="Zaključeno", source_date=self.danas)
        istice = self.danas + datetime.timedelta(days=10)
        UgovorZaposlenog.objects.create(employee_code=1, redni_broj=1, employee=self.ana, datum_od=datetime.date(2025, 1, 1),
                                        datum_do=istice, radnik_aktivan=True, naziv_radnog_mesta="Referent")
        UgovorZaposlenog.objects.create(employee_code=2, redni_broj=1, employee=self.marko, datum_od=datetime.date(2025, 1, 1),
                                        datum_do=istice, radnik_aktivan=True)
        UgovorZaposlenog.objects.create(employee_code=2, redni_broj=2, employee=self.marko,  # produžen — ne ističe
                                        datum_od=istice + datetime.timedelta(days=1), na_neodredjeno=True, radnik_aktivan=True)
        self.admin = get_user_model().objects.create_superuser("admin", password="x")

    def test_pregled_za_kadrove(self):
        ctx = pregled(self.admin, self.danas)
        self.assertEqual((ctx["zaposleni"]["aktivni"], ctx["zaposleni"]["zene"], ctx["zaposleni"]["muskarci"]), (2, 1, 1))
        self.assertEqual([e.pk for e in ctx["zaposleni"]["novi"]], [self.marko.pk])
        self.assertEqual(sum(c["broj"] for c in ctx["zaposleni"]["struktura"]), 2)
        self.assertEqual((ctx["odsutni"]["ukupno"], ctx["odsutni"]["godisnji"], ctx["odsutni"]["bolovanje"]), (2, 1, 1))
        self.assertEqual([u.employee_id for u in ctx["ugovori"]["redovi"]], [self.ana.pk])
        self.assertEqual(ctx["ugovori"]["redovi"][0].preostalo, 10)
        self.assertEqual(ctx["zahtevi"]["cekaju_ukupno"], 0)

        self.client.force_login(self.admin)
        strana = self.client.get(reverse("hr:pregled"))
        self.assertContains(strana, "Aktivni zaposleni")
        self.assertContains(strana, "Godišnji odmor")
        self.assertContains(strana, "Referent")
        self.assertContains(strana, "Moja radna lista")

    def test_bez_dozvola_samo_licni_deo(self):
        korisnik = get_user_model().objects.create_user("obican", password="x")
        self.assertEqual(set(pregled(korisnik, self.danas)) & {"zaposleni", "odsutni", "ugovori", "zahtevi", "resenja"}, set())
        self.client.force_login(korisnik)
        strana = self.client.get(reverse("hr:pregled"))
        self.assertEqual(strana.status_code, 200)
        self.assertNotContains(strana, "Aktivni zaposleni")
        self.assertNotContains(strana, "Anić")
        self.assertContains(strana, "Moj profil")

    def test_kadrovi_otvaraju_pregled_a_moj_profil_je_na_dnu_menija(self):
        self.client.force_login(self.admin)
        odgovor = self.client.get(reverse("switch_app", args=["kadrovi"]), {"next": reverse("hr:pregled")})
        self.assertRedirects(odgovor, reverse("hr:pregled"))
        html = self.client.get(reverse("hr:pregled")).content.decode()
        self.assertIn(f"?next={reverse('hr:pregled')}", html)  # link „Kadrovi” u zaglavlju
        meni = html[html.index('id="sidebarnav"'):]
        self.assertLess(meni.index("Pregled"), meni.index("Spisak zaposlenih"))
        self.assertGreater(meni.index("Moj profil"), meni.index("Ugovori"))


class MojProfilPregledTests(TestCase):
    """Moj profil → Pregled: brze akcije, godišnji odmor, ugovor i stanje meseca."""

    def setUp(self):
        from core.models import PermissionCode, Role

        self.danas = timezone.localdate()
        self.ana = zaposleni(1, "Anić", zaposlen=datetime.date(2019, 3, 1))
        self.korisnik = get_user_model().objects.create_user("ana", password="x", employee=self.ana)
        uloga = Role.objects.create(name="zaposleni", slug="zaposleni")
        uloga.permissions.add(PermissionCode.objects.get_or_create(code="hr:zahtev_create")[0])
        self.korisnik.roles.add(uloga)
        from hr.models import AnnualLeaveAllowance

        AnnualLeaveAllowance.objects.create(year=self.danas.year, employee_code=1, employee=self.ana, last_seen_at=timezone.now(),
                                            allocated_days=24)
        AnnualLeaveDecision.objects.create(year=self.danas.year, employee_code=1, employee=self.ana, last_seen_at=timezone.now(),
                                           source_start_key="k1", start_date=self.danas + datetime.timedelta(days=10),
                                           end_date=self.danas + datetime.timedelta(days=16), approved_days=5)
        UgovorZaposlenog.objects.create(employee_code=1, redni_broj=1, employee=self.ana, datum_od=datetime.date(2019, 3, 1),
                                        na_neodredjeno=True, radnik_aktivan=True, naziv_radnog_mesta="Samostalni referent",
                                        broj_ugovora="12/2019")
        self.client.force_login(self.korisnik)

    def test_pregled_je_prva_kartica(self):
        odgovor = self.client.get(reverse("my_employee_profile"))
        moj = odgovor.context["moj"]
        self.assertEqual(moj["godisnji"]["godine"][0]["preostalo"], 19)  # 24 dodeljeno − 5 po rešenjima
        self.assertEqual(moj["godisnji"]["sledeci"].approved_days, 5)
        self.assertEqual(moj["ugovor"].broj_ugovora, "12/2019")
        self.assertIsNone(moj["radna_lista"])
        html = odgovor.content.decode()
        self.assertLess(html.index('data-bs-target="#pregled"'), html.index('data-bs-target="#basic-info"'))
        self.assertIn('id="pregled"', html)
        self.assertIn("Samostalni referent", html)
        self.assertIn(f"{reverse('hr:zahtev_create')}?zaposleni={self.ana.pk}", html)
        self.assertIn(reverse("hr:work_time_sheet"), html)
        self.assertNotIn("getOrCreateInstance(", html)  # Bootstrap 5.0 beta

    def test_tudji_profil_nema_licni_pregled(self):
        admin = get_user_model().objects.create_superuser("admin", password="x")
        self.client.force_login(admin)
        odgovor = self.client.get(reverse("employee_detail", args=[self.ana.pk]))
        self.assertNotIn("moj", odgovor.context)
        self.assertNotContains(odgovor, 'id="pregled"')

    def test_zahtev_iz_profila_ima_izabranog_zaposlenog(self):
        from unittest import mock

        with mock.patch("hr.zahtevi_views._zaposleni_u_obuhvatu", return_value=Employee.objects.all()):
            odgovor = self.client.get(reverse("hr:zahtev_create"), {"zaposleni": self.ana.pk})
        self.assertEqual(odgovor.status_code, 200)
        self.assertEqual(odgovor.context["form"].initial.get("zaposleni"), self.ana.pk)
