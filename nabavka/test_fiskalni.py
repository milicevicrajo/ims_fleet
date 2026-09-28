"""Fiskalni racuni (Nabavka): ocitavanje QR koda, popravka rasporeda tastature, preuzimanje, ekrani."""
import base64
import hashlib
import json
import struct
import urllib.error
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import OrganizationalUnit, PermissionCode, Role
from nabavka.models import FiskalniRacun
from nabavka.services import fiskalni

LINK = ("https://suf.purs.gov.rs/v/?vl=A1RKRVlSS0tFVEpFWVJLS0X6zwIAXZsCAEhYEwEAAAAAAAABoLRUVcgAABIxMjoxMDAyMjM2MTc6"
        "ODE1NDGT1A2wCdBilQeGOyZRB2gkI7yuel5A9gat9RuDtOjC/NXAvtn/qs5DRCjMuA+l26O+cuBPuKyQx2uAC4mGLr9vaJRvcEE5IFitK6OL"
        "iIyoEUNSfNUTd4/L+xZTJ7J3+zrLUZWejp2FtsUu0SC7ZmtAvHc4Xi9Ummgp0+27JFioFCiba2FDtNRq58ngfYace21JLXHLtccTJyEAUu8k"
        "rEZh9HDAbMsFmHSiJEfW7sDVRuBP4KuuSbAm+e7oeToBQG2W9FKDTjqAibMmrBka1/P8SnWMPhJf4ZROnA46yE15ziltPyuvjFXfn6sZgja9"
        "19tXtyf9QKwRi+XVQbUCXKbTXipKsClLsEHim7LuZ7Bi+8jWOcUCZI7WCV6pqUAjH2Zu2Xp0pyECNDj369BEhCczjfnkE1VgeSUa/a93qQSJ"
        "C6mb2CpW/9EFCAJgfO08U0Fr9jwVf9iKCnNwHIoh55uHLLYgoHnEUW9C78WmWG/AAZJltrOH2Y9qwxt4AbrtQqS4SsbsYm0cON7jZrz7MvGR"
        "NW2zU89YEqSoGaUgMy4n4AyF/lXiFFnGO1eQbR4k926nZttSUNsv+8U7N4UkSEIR5W1S734DCr+QOOITthMP1nQhhxBsHaksretiYj+Syb56"
        "z3D8V0Bmjgm36gE+T+ibdMM+ibpFFfpDJT7Yo9o1ro1k+Ff464LFLdmm2MTNLNo=")

STRANICA = """<html><body>
<span id="tinLabel">110734511</span><span id="shopFullNameLabel">1080292-Okov centar</span>
<span id="addressLabel">ПАРТИЗАНСКЕ АВИЈАЦИЈЕ 2</span><span id="cityLabel">БЕОГРАД</span>
<span id="administrativeUnitLabel">Београд-Нови Београд</span><span id="invoiceCounterExtensionLabel">ПП</span>
<pre>============ ФИСКАЛНИ РАЧУН ============
               110734511
           OKOV INTERNATIONAL
Касир:                   kasir.test
ИД купца:             12:100223617:81541
ЕСИР број:                      644/20.1
Укупан износ:                   1.804,50
Пренос на рачун:                1.804,50
========================================
Укупан износ пореза:              221,93
</pre>
<script>viewModel.InvoiceNumber('TJEYRKKE-TJEYRKKE-184314'); viewModel.Token('token-123');</script>
</body></html>"""

STAVKE = {"success": True, "items": [
    {"gtin": "8606100992034", "name": "Zemlja za cveće 5l kom", "quantity": 4, "total": 1040.4, "unitPrice": 260.1,
     "label": "Е", "labelRate": 10, "taxBaseAmount": 945.82, "vatAmount": 94.58},
    {"gtin": "3838853400381", "name": "Petometar magnetni kom", "quantity": 1, "total": 764.1, "unitPrice": 764.1,
     "label": "Ђ", "labelRate": 20, "taxBaseAmount": 636.75, "vatAmount": 127.35}]}


def napravi_link(id_kupca="", iznos=100000, vrsta_transakcije=0, brojac=7):
    """QR sadrzaj kakav pravi PFR, sa ispravnim kontrolnim zbirom (za slucajeve kojih nema na pravom racunu)."""
    ms = int(datetime(2026, 9, 18, 11, 0, tzinfo=dt_timezone.utc).timestamp() * 1000)
    kupac = id_kupca.encode()
    telo = (bytes([3]) + b"ABCDEFGH" + b"ABCDEFGH" + struct.pack("<II", brojac, brojac) + struct.pack("<Q", iznos)
            + struct.pack(">Q", ms) + bytes([0, vrsta_transakcije, len(kupac)]) + kupac + bytes(256))
    return "https://suf.purs.gov.rs/v/?vl=" + base64.b64encode(telo + hashlib.md5(telo).digest()).decode()


def us_na_srpsku_latinicu(tekst):
    mapa = {us: sr for us, sr in zip(fiskalni._US, fiskalni._SR_LAT)}
    return "".join(mapa.get(z, z) for z in tekst)


def us_na_cirilicu(tekst):
    mapa = {**fiskalni._SR_CIR_SLOVA, ":": "Ч", "/": "-", "?": "_", "-": "'", "=": "+", "+": "*"}
    return "".join(mapa.get(z, z) for z in tekst)


class OcitavanjeTests(TestCase):
    def test_zaglavlje_iz_qr_koda(self):
        z = fiskalni.ocitaj_link(LINK)
        self.assertEqual(z.broj_racuna, "TJEYRKKE-TJEYRKKE-184314")
        self.assertEqual(z.iznos, Decimal("1804.50"))
        self.assertEqual((z.vrsta_racuna, z.vrsta_transakcije), (0, 0))
        self.assertEqual((z.id_kupca, z.pib_kupca), ("12:100223617:81541", "100223617"))
        self.assertEqual(z.pfr_vreme, datetime(2026, 9, 18, 11, 43, 41, 0, tzinfo=dt_timezone.utc).replace(
            microsecond=z.pfr_vreme.microsecond))

    def test_popravka_srpskog_rasporeda_tastature(self):
        for pokvaren in (us_na_srpsku_latinicu(LINK), us_na_cirilicu(LINK)):
            with self.subTest(pocetak=pokvaren[:12]):
                self.assertNotEqual(pokvaren, LINK)
                z = fiskalni.ocitaj_link(pokvaren)
                self.assertEqual(z.broj_racuna, "TJEYRKKE-TJEYRKKE-184314")
                self.assertEqual(fiskalni.ocitaj_link(z.link).broj_racuna, z.broj_racuna)  # sacuvan ispravan link

    def test_pogresno_ocitan_link_se_odbija(self):
        with self.assertRaises(fiskalni.GreskaOcitavanja):
            fiskalni.ocitaj_link(LINK.replace("Ummgp", "Ummgq"))
        with self.assertRaises(fiskalni.GreskaOcitavanja):
            fiskalni.ocitaj_link("")

    def test_citanje_stranice_za_proveru(self):
        podaci = fiskalni.procitaj_stranicu(STRANICA)
        self.assertEqual((podaci["pib_prodavca"], podaci["naziv_prodavca"], podaci["kasir"]),
                         ("110734511", "OKOV INTERNATIONAL", "kasir.test"))
        self.assertEqual((podaci["esir_broj"], podaci["token"]), ("644/20.1", "token-123"))
        self.assertEqual(podaci["nacin_placanja"], "Пренос на рачун: 1.804,50")
        self.assertEqual(podaci["pdv_ukupno"], Decimal("221.93"))


def lazni_suf(url, podaci=None):
    return json.dumps(STAVKE) if url.endswith("/specifications") else STRANICA


class UpisTests(TestCase):
    def setUp(self):
        self.sifra = OrganizationalUnit.objects.create(code="430111", name="Strucni nadzor", center="43")
        self.korisnik = get_user_model().objects.create_user("nabavka-fiskalni", password="x")

    def test_upis_racuna_sa_stavkama(self):
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            racun, upozorenja = fiskalni.upisi(LINK, self.sifra, self.korisnik)
        self.assertEqual(upozorenja, [])
        self.assertEqual((racun.status, racun.na_ims, racun.pib_prodavca), (FiskalniRacun.Status.POTVRDJEN, True, "110734511"))
        self.assertEqual(racun.stavke.count(), 2)
        self.assertEqual(sum(s.ukupno for s in racun.stavke.all()), racun.iznos)
        self.assertEqual(racun.link, LINK)
        with self.assertRaises(fiskalni.GreskaOcitavanja):  # isti racun se ne upisuje dva puta
            fiskalni.upisi(LINK, self.sifra, self.korisnik)

    def test_stranica_nedostupna_racun_ceka_proveru(self):
        with mock.patch.object(fiskalni, "_otvori", side_effect=urllib.error.URLError("nema veze")):
            racun, upozorenja = fiskalni.upisi(LINK, self.sifra, self.korisnik)
        self.assertEqual((racun.status, racun.iznos, racun.stavke.count()), (FiskalniRacun.Status.CEKA, Decimal("1804.50"), 0))
        self.assertTrue(any("nije dostupna" in u for u in upozorenja))
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            from nabavka.tasks import fiskalni_ponovi_task

            self.assertIn("preuzeto 1", fiskalni_ponovi_task())
        racun.refresh_from_db()
        self.assertEqual(racun.status, FiskalniRacun.Status.POTVRDJEN)

    def test_upozorenje_kad_racun_nije_na_ims(self):
        with mock.patch.object(fiskalni, "_otvori", side_effect=urllib.error.URLError("x")):
            fizicko, u1 = fiskalni.upisi(napravi_link(brojac=1), self.sifra, self.korisnik)
            drugi, u2 = fiskalni.upisi(napravi_link("10:101010101", brojac=2), self.sifra, self.korisnik)
            refund, u3 = fiskalni.upisi(napravi_link("10:100223617", brojac=3, vrsta_transakcije=1), self.sifra, self.korisnik)
        self.assertFalse(fizicko.na_ims)
        self.assertIn("fizičko lice", u1[0])
        self.assertIn("10:101010101", u2[0])
        self.assertTrue(refund.na_ims)
        self.assertTrue(any("refundacija" in u for u in u3))


class EkraniTests(TestCase):
    def setUp(self):
        self.aktivna = OrganizationalUnit.objects.create(code="430111", name="Strucni nadzor", center="43")
        uloga = Role.objects.create(name="Nabavka test", slug="nabavka-test")
        for kod in ("nabavka:fiskalni_list", "nabavka:fiskalni_data", "nabavka:fiskalni_scan", "nabavka:fiskalni_detail"):
            uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        self.korisnik = get_user_model().objects.create_user("nabavka-ekran", password="x")
        self.korisnik.roles.add(uloga)
        self.client.force_login(self.korisnik)

    def test_spisak_ocitavanje_i_detalj(self):
        odgovor = self.client.get(reverse("nabavka:fiskalni_list"))
        self.assertContains(odgovor, "Očitaj QR kod računa")
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            odgovor = self.client.post(reverse("nabavka:fiskalni_scan"), {"link": LINK, "job_code": self.aktivna.pk},
                                       HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(odgovor.status_code, 200, odgovor.content)
        self.assertTrue(odgovor.json()["ok"])
        racun = FiskalniRacun.objects.get()
        self.assertEqual(racun.created_by, self.korisnik)
        podaci = self.client.get(reverse("nabavka:fiskalni_data"), {"draw": 1, "start": 0, "length": 10}).json()
        self.assertEqual(podaci["recordsTotal"], 1)
        self.assertContains(self.client.get(reverse("nabavka:fiskalni_detail", args=[racun.pk])), "Zemlja za cveće")

    def test_sifra_posla_je_obavezna_i_bez_dozvole_nema_pristupa(self):
        odgovor = self.client.post(reverse("nabavka:fiskalni_scan"), {"link": LINK}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(odgovor.status_code, 400)
        self.assertFalse(FiskalniRacun.objects.exists())
        drugi = get_user_model().objects.create_user("bez-dozvole", password="x")
        self.client.force_login(drugi)
        self.assertEqual(self.client.get(reverse("nabavka:fiskalni_list")).status_code, 403)
