"""Flota na registru (plan prelaska na registar, korak 6): vozila i putni nalozi po obuhvatu dodela."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from core.models import OrganizationalUnit
from fleet.models import JobCode, Lease, Policy, PutniNalog, Vehicle
from fleet.support import obuhvat as obuhvat_flote
from fleet.test_vehicle_onboarding import vehicle
from organizacija.models import DodelaUloge
from organizacija.services.importer import run_import
from organizacija.test_prava import centar, uloga_sa_dozvolom
from organizacija.tests import ImportTestCase

NA_REGISTRU = override_settings(PRAVA_PO_REGISTRU={"flota": True})


@NA_REGISTRU
class FlotaNaRegistruTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        self.nadzor = OrganizationalUnit.objects.create(code="430111", name="Strucni nadzor", center="43")
        self.materijali = OrganizationalUnit.objects.create(code="410001", name="Amortizacija", center="41")
        run_import(company=1)
        self.vozilo_43, self.vozilo_41, self.bez_dodele = vehicle("1"), vehicle("2"), vehicle("3")
        JobCode.objects.create(vehicle=self.vozilo_43, organizational_unit=self.nadzor, assigned_date=datetime.date(2026, 1, 1))
        JobCode.objects.create(vehicle=self.vozilo_41, organizational_unit=self.materijali, assigned_date=datetime.date(2026, 1, 1))
        self.uloga = uloga_sa_dozvolom("pregled-flote", "vehicle_list", "vehicle_data", "vehicle_detail", "vehicle_update", "dashboard",
                                       "policy_list", "policy_detail", "putninalog_list", "putninalog_detail",
                                       "center_statistics")
        self.korisnik = get_user_model().objects.create_user("flota-43", password="x", allowed_center_codes="41")
        self.korisnik.roles.add(self.uloga)
        self.nalog_43 = self.putni_nalog(self.nadzor, "43/2026-1")
        self.nalog_41 = self.putni_nalog(self.materijali, "41/2026-1")

    def putni_nalog(self, jedinica, broj):
        return PutniNalog.objects.create(order_number=broj, job_code=jedinica, travel_location="Beograd", task="Test",
                                         travel_date=datetime.date(2026, 7, 10), number_of_days=1,
                                         advance_payment=Decimal("1000.00"))

    def dodeli(self, **obuhvat):
        DodelaUloge.objects.create(korisnik=self.korisnik, uloga=self.uloga, vazi_od=datetime.date(2026, 1, 1),
                                   status=DodelaUloge.STATUS_AKTIVNA, **obuhvat)

    def svez(self):
        return get_user_model().objects.get(pk=self.korisnik.pk)

    def test_bez_dodele_ne_vidi_nista(self):
        self.assertEqual(set(obuhvat_flote.po_vozilu(Vehicle.objects.all(), self.svez(), "pk")), set())
        self.assertFalse(obuhvat_flote.putni_nalozi(PutniNalog.objects.all(), self.svez()).exists())

    def test_vozila_i_putni_nalozi_po_obuhvatu(self):
        self.dodeli(cvor_id=centar("43"))
        korisnik = self.svez()
        # Vozilo bez dodele ostaje vidljivo, da tek uneto vozilo ne nestane.
        self.assertEqual(set(obuhvat_flote.po_vozilu(Vehicle.objects.all(), korisnik, "pk")), {self.vozilo_43, self.bez_dodele})
        self.assertEqual(set(obuhvat_flote.putni_nalozi(PutniNalog.objects.all(), korisnik)), {self.nalog_43})
        self.assertEqual(obuhvat_flote.centri(korisnik), {"43"})

    def test_cela_firma_vidi_sve(self):
        self.dodeli(cela_firma=True)
        self.assertEqual(obuhvat_flote.po_vozilu(Vehicle.objects.all(), self.svez(), "pk").count(), 3)

    def test_ekrani_postuju_obuhvat(self):
        self.dodeli(cvor_id=centar("43"))
        polisa_41 = Policy.objects.create(vehicle=self.vozilo_41, invoice_id=41, policy_number="P41", partner_name="Osiguranje",
                                          start_date=datetime.date(2026, 1, 1), end_date=datetime.date(2027, 1, 1))
        self.client.force_login(self.korisnik)
        self.assertEqual(self.client.get(reverse("vehicle_detail", args=[self.vozilo_43.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("vehicle_detail", args=[self.vozilo_41.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("policy_detail", args=[polisa_41.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("putninalog_detail", args=[self.nalog_41.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("putninalog_detail", args=[self.nalog_43.pk])).status_code, 302)  # detalj vodi na stampu
        podaci = self.client.get(reverse("vehicle_data"), {"draw": 1, "start": 0, "length": 10}).json()
        self.assertEqual(podaci["recordsTotal"], 2)
        from fleet.support.fleet_snapshot import fleet_snapshot

        self.assertEqual(fleet_snapshot(self.svez())["totals"]["count"], 2)  # kontrolna tabla: 43 i vozilo bez dodele
        self.assertEqual(self.client.get(reverse("center_statistics", args=["41"])).status_code, 403)
