"""UF SEF (Nabavka): samo ulazne fakture sa SEF-a; bez sifre posla, pa ih na registru vidi samo cela firma."""
import datetime
import shutil
import tempfile
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from finansije.sef_models import SefFaktura
from finansije.services import sef as servis
from nabavka.access import ulazne_sef
from organizacija.models import DodelaUloge
from organizacija.services.importer import run_import
from organizacija.test_prava import centar, uloga_sa_dozvolom
from organizacija.tests import ImportTestCase

DANAS = datetime.date(2026, 10, 1)
KODOVI = ("nabavka:uf_sef_list", "nabavka:uf_sef_data", "nabavka:uf_sef_pdf")


def faktura(smer, sef_id, broj, **polja):
    return SefFaktura.objects.create(smer=smer, sef_id=sef_id, broj=broj, sinhronizovano=timezone.now(),
                                     datum_prometa=polja.pop("datum_prometa", DANAS), **polja)


class UfSefTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media = override_settings(MEDIA_ROOT=tempfile.mkdtemp())
        cls._media.enable()

    @classmethod
    def tearDownClass(cls):
        from django.conf import settings

        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        cls._media.disable()
        super().tearDownClass()

    def setUp(self):
        self.ulazna = faktura("ulazna", 1, "F-2026-0815", partner_naziv="Dobavljac doo", partner_pib="100000001",
                              iznos=Decimal("1200.00"), valuta="RSD", status="New", vrsta="Invoice",
                              datum_slanja=timezone.make_aware(datetime.datetime(2026, 10, 1, 9, 30)))
        self.druga = faktura("ulazna", 2, "77/2026", partner_naziv="Gorivo ad", iznos=Decimal("300.00"),
                             status="Approved", datum_prometa=datetime.date(2026, 8, 1))
        self.izlazna = faktura("izlazna", 3, "2650707001-325", partner_naziv="Putevi Srbije", iznos=Decimal("50.00"))
        korisnik = get_user_model().objects.create_user("nabavka-uf", password="x")
        korisnik.roles.add(uloga_sa_dozvolom("nabavka-uf", *KODOVI))
        self.client.force_login(korisnik)

    def podaci(self, **parametri):
        return self.client.get(reverse("nabavka:uf_sef_data"), {"draw": 1, **parametri}).json()

    def test_samo_ulazne_fakture(self):
        odgovor = self.client.get(reverse("nabavka:uf_sef_list"))
        self.assertContains(odgovor, "UF SEF — ulazne fakture")
        self.assertContains(odgovor, f'href="{reverse("nabavka:uf_sef_list")}"')  # stavka u meniju
        self.assertEqual(odgovor.context["zbir"], {"broj": 2, "iznos": Decimal("1500.00")})
        podaci = self.podaci()
        self.assertEqual((podaci["recordsTotal"], podaci["recordsFiltered"]), (2, 2))
        brojevi = " ".join(red["broj"] for red in podaci["data"])
        self.assertIn("F-2026-0815", brojevi)
        self.assertNotIn("2650707001-325", brojevi)
        self.assertIn("Dobavljac doo", podaci["data"][0]["dobavljac"])  # najnovija prva
        self.assertIn("01.10.2026. 09:30", podaci["data"][0]["primljena"])

    def test_filteri_i_pretraga(self):
        self.assertEqual(self.podaci(q="Dobavljac")["recordsFiltered"], 1)
        self.assertEqual(self.podaci(q="Putevi")["recordsFiltered"], 0)  # izlazna se ne nalazi ni pretragom
        self.assertEqual(self.podaci(status="Approved")["recordsFiltered"], 1)
        self.assertEqual(self.podaci(od="2026-09-01")["recordsFiltered"], 1)
        self.assertEqual(self.podaci(**{"search[value]": "100000001"})["recordsFiltered"], 1)
        self.assertEqual(self.podaci(knjizenje="da")["recordsFiltered"], 0)

    def test_pdf_ulazne_a_izlazna_nije_dostupna(self):
        with mock.patch.object(servis.Klijent, "pdf", return_value=(b"%PDF-1.4 UF", "")):
            odgovor = self.client.get(reverse("nabavka:uf_sef_pdf", args=[self.ulazna.pk]))
        self.assertEqual(odgovor.status_code, 200)
        self.assertEqual(b"".join(odgovor.streaming_content), b"%PDF-1.4 UF")
        self.assertEqual(self.client.get(reverse("nabavka:uf_sef_pdf", args=[self.izlazna.pk])).status_code, 404)

    def test_pdf_u_pripremi_vraca_na_spisak(self):
        with mock.patch.object(servis.Klijent, "pdf", return_value=(None, "SEF priprema PDF.")):
            odgovor = self.client.get(reverse("nabavka:uf_sef_pdf", args=[self.ulazna.pk]), follow=True)
        self.assertRedirects(odgovor, reverse("nabavka:uf_sef_list"))
        self.assertContains(odgovor, "SEF priprema PDF.")


@override_settings(PRAVA_PO_REGISTRU={"nabavka": True})
class UfSefObuhvatTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        self.ulazna = faktura("ulazna", 1, "F-1")
        self.uloga = uloga_sa_dozvolom("nabavka-uf-centar", *KODOVI)
        self.korisnik = get_user_model().objects.create_user("nabavka-uf-43", password="x")
        self.korisnik.roles.add(self.uloga)

    def dodeli(self, **obuhvat):
        DodelaUloge.objects.create(korisnik=self.korisnik, uloga=self.uloga, vazi_od=datetime.date(2026, 1, 1),
                                   status=DodelaUloge.STATUS_AKTIVNA, **obuhvat)

    def vidi(self):
        return set(ulazne_sef(SefFaktura.objects.all(), get_user_model().objects.get(pk=self.korisnik.pk)))

    def test_centar_ne_vidi_ulazne(self):
        self.assertEqual(self.vidi(), set())  # bez dodele — nista
        self.dodeli(cvor_id=centar("43"))
        self.assertEqual(self.vidi(), set())  # ulazna nema sifru posla
        self.client.force_login(self.korisnik)
        self.assertEqual(self.client.get(reverse("nabavka:uf_sef_pdf", args=[self.ulazna.pk])).status_code, 404)

    def test_cela_firma_vidi_ulazne(self):
        self.dodeli(cela_firma=True)
        self.assertEqual(self.vidi(), {self.ulazna})
