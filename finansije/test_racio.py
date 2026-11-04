"""Racio analiza (od 04.11.2026.): kontrolni primer izračunat ručno, preračun nepune godine, „—”, ekran i Excel."""
from datetime import date
from decimal import Decimal as D
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from openpyxl import load_workbook

from core.models import PermissionCode, Role
from .services import racio
from .services.bilansi import izracunaj
from .test_bilansi import knjizi

# Kontrolni primer (iznosi u dinarima):
# 31.12.2025: zgrada 1.000, materijal 100, kupci 200, gotovina 300 = kapital 1.200, dobavljači 200, kredit banke 200
# 31.12.2026: zgrada 1.000, materijal 300, kupci 400, gotovina 500 = kapital 1.200, dobitak 400, dobavljači 400,
#             kredit banke 200
# 2026: prihodi od usluga 2.000; materijal 300, proizvodne usluge 200, zarade 900, amortizacija 100, kamate 50;
#       porez na dobit 50 → poslovni rezultat 500, pre poreza 450, neto 400, EBIT 500, EBITDA 600
STANJE_PRE = {"02200": D("1000"), "10100": D("100"), "20400": D("200"), "24100": D("300"),
              "30000": D("-1200"), "43500": D("-200"), "42200": D("-200")}
STANJE = {"02200": D("1000"), "10100": D("300"), "20400": D("400"), "24100": D("500"),
          "30000": D("-1200"), "34100": D("-400"), "43500": D("-400"), "42200": D("-200")}
USPEH = {"61200": D("-2000"), "51100": D("300"), "53000": D("200"), "52000": D("900"), "54000": D("100"),
         "56200": D("50"), "721": D("50")}


def primer():
    bu = izracunaj("BU", USPEH)["iznosi"]
    return racio.velicine(izracunaj("BS", STANJE)["iznosi"], bu), racio.velicine(izracunaj("BS", STANJE_PRE)["iznosi"], bu)


class PokazateljiTests(SimpleTestCase):
    def assertBlizu(self, vrednost, ocekivano):
        self.assertAlmostEqual(float(vrednost), ocekivano, places=4)

    def test_pomocne_velicine_iz_aop(self):
        vel, _ = primer()
        self.assertEqual({k: vel[k] for k in ("stalna", "obrtna", "zalihe", "kupci", "gotovina", "aktiva", "kapital",
                                              "kratkorocne", "obaveze", "dobavljaci", "kamatonosni")},
                         {"stalna": 1000, "obrtna": 1200, "zalihe": 300, "kupci": 400, "gotovina": 500, "aktiva": 2200,
                          "kapital": 1600, "kratkorocne": 600, "obaveze": 600, "dobavljaci": 400, "kamatonosni": 200})
        self.assertEqual({k: vel[k] for k in ("prodaja", "poslovni_prihodi", "poslovni_rezultat", "kamate", "pre_poreza",
                                              "neto", "ebit", "ebitda")},
                         {"prodaja": 2000, "poslovni_prihodi": 2000, "poslovni_rezultat": 500, "kamate": 50,
                          "pre_poreza": 450, "neto": 400, "ebit": 500, "ebitda": 600})

    def test_kontrolni_primer(self):
        r = racio.pokazatelji(*primer())
        ocekivano = {
            "Opšti racio likvidnosti": 2, "Rigorozni (brzi) racio": 1.5, "Racio gotovine": 500 / 600,
            "Neto obrtni kapital": 600,
            "Učešće kapitala u izvorima": 1600 / 2200 * 100, "Stepen zaduženosti": 600 / 2200 * 100,
            "Dug / Kapital (D/E)": 0.375, "Pokriće stalne imovine kapitalom": 1.6, "Zlatno bilansno pravilo": 1.6,
            "Pokriće kamata": 10, "Neto dug / EBITDA": -0.5,
            "EBITDA marža": 30, "Poslovna (operativna) marža": 25, "Neto profitna marža": 20,
            "ROA": 400 / 1900 * 100, "ROE": 400 / 1400 * 100,
            "Obrt ukupne imovine": 2000 / 1900, "Obrt zaliha": 1.5, "Dani vezivanja zaliha": 365 / 1.5,
            "Dani naplate potraživanja (DSO)": 365 * 300 / 2400, "Dani plaćanja dobavljačima (DPO)": 365 * 300 / 600,
            "Ciklus konverzije gotovine": 365 / 1.5 + 365 * 300 / 2400 - 365 * 300 / 600,
        }
        self.assertEqual(set(r), set(ocekivano))  # bez prodaje robe nema bruto marže
        for naziv, vrednost in ocekivano.items():
            with self.subTest(naziv):
                self.assertBlizu(r[naziv], vrednost)

    def test_nepuna_godina_preracunava_tok_a_marze_ostaju(self):
        r = racio.pokazatelji(*primer(), faktor_godine=D("2"))
        self.assertBlizu(r["ROA"], 800 / 1900 * 100)
        self.assertBlizu(r["Neto profitna marža"], 20)
        self.assertBlizu(r["Pokriće kamata"], 10)
        self.assertBlizu(r["Opšti racio likvidnosti"], 2)

    def test_faktor_pdv(self):
        r = racio.pokazatelji(*primer(), pdv=D("1"))
        self.assertBlizu(r["Dani naplate potraživanja (DSO)"], 365 * 300 / 2000)

    def test_nula_ili_negativan_imenilac_i_bez_proseka(self):
        vel, vel_pre = primer()
        r = racio.pokazatelji({**vel, "kapital": D("-100"), "kamate": D("0")}, vel_pre)
        self.assertIsNone(r["Dug / Kapital (D/E)"])
        self.assertIsNone(r["Pokriće kamata"])
        self.assertBlizu(r["Učešće kapitala u izvorima"], -100 / 2200 * 100)  # negativan kapital se vidi
        r = racio.pokazatelji(vel, None)
        self.assertIsNone(r["ROA"])
        self.assertIsNone(r["Ciklus konverzije gotovine"])
        self.assertBlizu(r["Opšti racio likvidnosti"], 2)

    def test_bruto_marza_samo_uz_prodaju_robe_i_orijentiri(self):
        bu = izracunaj("BU", {**USPEH, "60400": D("-1000"), "50100": D("700")})["iznosi"]
        vel = racio.velicine(izracunaj("BS", STANJE)["iznosi"], bu)
        self.assertBlizu(racio.pokazatelji(vel, None)["Bruto marža na robi"], 30)
        likvidnost = next(p for p in racio.POKAZATELJI if p.naziv == "Opšti racio likvidnosti")
        self.assertEqual((racio.u_redu(likvidnost, D("1.4")), racio.u_redu(likvidnost, D("2")), racio.u_redu(likvidnost, None)),
                         (False, True, None))
        roe = next(p for p in racio.POKAZATELJI if p.naziv == "ROE")
        self.assertIsNone(racio.u_redu(roe, D("5")))


@patch("finansije.services.bilansi.nazivi_konta", return_value={})
class RacioEkranTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("racio-reader", password="test")
        self.role = Role.objects.create(name="Racio test", slug="racio-test")
        self.user.roles.add(self.role)
        self.client.force_login(self.user)
        knjizi(1, "24100", dug="1000", vrsta="POC", dan=date(2026, 1, 1))
        knjizi(1, "30000", pot="1000", vrsta="POC", dan=date(2026, 1, 1), linija=2)
        knjizi(2, "24100", dug="500", vrsta="IF", dan=date(2026, 5, 1))
        knjizi(2, "61200", pot="500", vrsta="IF", dan=date(2026, 5, 1), linija=2)

    def grant(self, *codes):
        for code in codes:
            self.role.permissions.add(PermissionCode.objects.get_or_create(code=code)[0])

    def test_trazi_dozvolu_i_celu_firmu(self, _):
        url = reverse("finansije:racio_analiza")
        self.assertEqual(self.client.get(url).status_code, 403)
        self.grant("finansije:racio_analiza")
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_godine_nepuna_godina_i_excel(self, _):
        self.grant("finansije:racio_analiza", "finansije:view_all")
        url = reverse("finansije:racio_analiza")
        self.assertNotContains(self.client.get(url), "Kontrole")
        odgovor = self.client.get(url, {"na_dan": "30.06.2026", "broj_godina": "2", "pdv": "1,20", "generisi": "1"})
        self.assertContains(odgovor, "Opšti racio likvidnosti")
        self.assertContains(odgovor, "2026 (do 30.06.)")
        self.assertContains(odgovor, "2025:</strong> Nema preuzetih knjiženja")
        self.assertContains(odgovor, "Nepuna godina (181 dana)")
        # ROA: neto 500 preračunat na godinu (× 365/181) / prosečna aktiva (1.500 + 1.000) / 2
        roa = next(s for _, stavke in odgovor.context["racio"]["odeljci"] for s in stavke if s["naziv"] == "ROA")
        self.assertAlmostEqual(float(roa["vrednosti"][1][0]), 500 * 365 / 181 / 1250 * 100, places=4)
        self.assertIsNone(roa["vrednosti"][0][0])
        odgovor = self.client.get(url, {"na_dan": "30.06.2026", "broj_godina": "2", "pdv": "1,20", "izvoz": "xlsx"})
        vrednosti = [c for r in load_workbook(BytesIO(odgovor.content)).active.iter_rows(values_only=True) for c in r if c is not None]
        self.assertIn("ROA (%)", vrednosti)
        self.assertIn("LIKVIDNOST", vrednosti)
        self.assertIn(1500.0, vrednosti)  # ukupna aktiva 30.06.2026.

    def test_broj_godina_i_pdv_se_proveravaju(self, _):
        self.grant("finansije:racio_analiza", "finansije:view_all")
        odgovor = self.client.get(reverse("finansije:racio_analiza"),
                                  {"na_dan": "30.06.2026", "broj_godina": "20", "pdv": "3", "generisi": "1"})
        self.assertIsNone(odgovor.context["racio"])
        self.assertEqual(set(odgovor.context["form"].errors), {"broj_godina", "pdv"})
