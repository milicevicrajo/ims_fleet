"""Izveštaj za nadzorni odbor (od 02.11.2026.): pozicije po mapiranju konta, cela firma i profitni centri."""
from datetime import date
from decimal import Decimal as D
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from openpyxl import load_workbook

from core.models import PermissionCode, Role
from .models import NadzorniCentar, NadzorniGodina, NadzorniPlan
from .services import izvoz, nadzorni_odbor as no
from .tests import save_entry

KADROVI = "finansije.services.nadzorni_odbor.zaposleni_iz_kadrova"


def knjizi(broj, konto, dug="0", pot="0", centar="41", dan=date(2026, 3, 1), vrsta="IF", linija=1):
    return save_entry(journal_number=broj, line_number=linija, account=konto, debit=D(dug), credit=D(pot),
                      journal_type=vrsta, year=dan.year, booking_date=dan, document_date=dan, center=centar,
                      org_centar=centar)


class MapiranjeTests(SimpleTestCase):
    def test_svaka_pozicija_iz_mapiranja_postoji_i_klasa_odgovara_strani(self):
        for konto, kod in no.MAPIRANJE.items():
            self.assertIn(kod, no.NAZIV, konto)
            self.assertEqual(konto.startswith("6"), kod.startswith("P"), konto)

    def test_631_umanjuje_ostale_prihode_a_konto_bez_pozicije_se_ne_rasporedjuje(self):
        iznosi, nerasporedjeno = no.pozicije({"614": D("1000"), "679": D("50"), "631": D("-30"), "602": D("7"),
                                              "520": D("400"), "540": D("100")})
        self.assertEqual((iznosi["P1"], iznosi["P4"], iznosi["UP"]), (D("1000"), D("20"), D("1020")))
        self.assertEqual((iznosi["R4"], iznosi["R23"], iznosi["UR"]), (D("400"), D("100"), D("500")))
        self.assertEqual(nerasporedjeno, {"602": D("7")})


class ObracunTests(TestCase):
    def setUp(self):
        for godina, prihod in ((2025, "800"), (2026, "1000")):
            dan = date(godina, 3, 1)
            knjizi(1, "61400", pot=prihod, dan=dan)
            knjizi(2, "52000", dug="400", dan=dan)
            knjizi(3, "52000", dug="100", centar="81", dan=dan)  # zajednička služba
            knjizi(4, "65000", pot="50", centar="81", dan=dan)
            knjizi(5, "61400", pot="200", centar="43", dan=dan)
            knjizi(6, "59900", dug="999", dan=date(godina, 12, 31), vrsta="ZAT")  # zatvaranje se ne broji
        knjizi(7, "61400", pot="5000", dan=date(2026, 9, 1))  # van perioda

    @patch(KADROVI, return_value=(12, {"41": 7}))
    def test_cela_firma_isti_period_plan_i_indeksi(self, _):
        NadzorniPlan.objects.create(godina=2026, pozicija="P1", iznos=D("2.4"))  # 2.400 din. godišnje
        NadzorniGodina.objects.create(godina=2026, plan_zaposlenih=11)
        rezultat = no.izradi_firmu(date(2026, 1, 1), date(2026, 6, 30), broj_godina=3)
        nema, k2025, k2026 = rezultat["kolone"]
        self.assertIsNone(nema["iznosi"])
        self.assertEqual((k2026["iznosi"]["P1"], k2026["iznosi"]["P4"], k2026["iznosi"]["UR"]), (D("1200"), D("50"), D("500")))
        self.assertEqual(k2025["iznosi"]["P1"], D("1000"))
        self.assertEqual(k2026["plan_period"]["P1"], D("1200"))  # 6 od 12 meseci
        self.assertEqual(k2026["zaposleni"][0], 12)  # tekuća godina bez upisa: Kadrovi
        tabela = no.tabela_firme(rezultat, "dinari")
        naslovi = [k.puni_naziv for k in tabela["kolone"]]
        self.assertEqual(naslovi, ["2024 · Ostvareno", "2025 · Ostvareno", "2025 · % učešća", "Plan 2026 · Godišnji",
                                   "Plan 2026 · Za 6 mes.", "2026 · Ostvareno", "2026 · % učešća",
                                   "2026 · Indeks / plan", "2026 · Indeks / 2025"])
        p1 = tabela["redovi"][0]["vrednosti"]
        self.assertEqual(p1[3:9], [D("2400"), D("1200"), D("1200"), D("1200") / D("1250") * 100, D("100"), D("120")])
        zaposleni = tabela["redovi"][-1]
        self.assertEqual(zaposleni["vrednosti"][3:6], [11, 11, 12])

    @patch(KADROVI, return_value=(12, {"41": 7}))
    def test_po_centrima_zajednicko_po_koeficijentu(self, _):
        NadzorniCentar.objects.create(godina=2026, centar="41", koeficijent=D("60"), broj_zaposlenih=5)
        NadzorniCentar.objects.create(godina=2026, centar="43", koeficijent=D("40"))
        NadzorniCentar.objects.create(godina=2026, centar="3", koeficijent=D("0"))
        rezultat = no.izradi_centre(date(2026, 1, 1), date(2026, 6, 30), broj_godina=1)
        godina = rezultat["po_godini"][2026]
        self.assertEqual((godina["zp"], godina["zt"]), (D("50"), D("100")))
        c41 = godina["centri"]["41"]
        self.assertEqual((c41["zp"], c41["UP"], c41["zt"], c41["dobit"]), (D("30"), D("1030"), D("60"), D("570")))
        self.assertEqual(c41["zaposleni"], 5)
        self.assertEqual(godina["centri"]["3"]["dobit"], D("0"))
        self.assertEqual(godina["ukupno"]["dobit"], D("750"))  # = prihodi 1250 − rashodi 500 cele firme
        self.assertEqual(rezultat["kontrole"][0][2], True)
        tabela = no.tabela_centara(rezultat, "dinari")
        self.assertEqual([k.puni_naziv for k in tabela["kolone"]],
                         ["Centar 3 · 2026", "Centar 41 · 2026", "Centar 43 · 2026", "IMS – PC · 2026"])

    def test_zbir_koeficijenata_razlicit_od_100_je_greska_u_kontroli(self):
        NadzorniCentar.objects.create(godina=2026, centar="41", koeficijent=D("60"))
        with patch(KADROVI, return_value=(0, {})):
            rezultat = no.izradi_centre(date(2026, 1, 1), date(2026, 6, 30), broj_godina=1)
        self.assertIn("mora biti 100%", rezultat["kontrole"][0][1])
        self.assertFalse(rezultat["kontrole"][0][2])


@patch(KADROVI, return_value=(3, {}))
class EkranTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("no-reader", password="test")
        self.role = Role.objects.create(name="NO test", slug="no-test")
        self.user.roles.add(self.role)
        self.client.force_login(self.user)
        knjizi(1, "61400", pot="1500", dan=date(2026, 2, 1))
        knjizi(2, "54000", dug="300", dan=date(2026, 2, 1))

    def grant(self, *codes):
        for code in codes:
            self.role.permissions.add(PermissionCode.objects.get_or_create(code=code)[0])

    def test_trazi_dozvolu_i_celu_firmu(self, _):
        url = reverse("finansije:nadzorni_odbor")
        self.assertEqual(self.client.get(url).status_code, 403)
        self.grant("finansije:nadzorni_odbor")
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_izvestaj_i_excel(self, _):
        self.grant("finansije:nadzorni_odbor", "finansije:view_all")
        url = reverse("finansije:nadzorni_odbor")
        odgovor = self.client.get(url, {"datum_od": "01.01.2026", "datum_do": "30.06.2026", "broj_godina": "1",
                                        "jedinica": "dinari", "generisi": "1"})
        self.assertContains(odgovor, "UKUPAN PRIHOD")
        self.assertContains(odgovor, izvoz.prikaz(D("1500"), "iznos"))
        self.assertContains(odgovor, "Po profitnim centrima")
        odgovor = self.client.get(url, {"datum_od": "01.01.2026", "datum_do": "30.06.2026", "broj_godina": "1",
                                        "izvoz": "xlsx"})
        vrednosti = [c for r in load_workbook(BytesIO(odgovor.content)).active.iter_rows(values_only=True) for c in r
                     if c is not None]
        self.assertIn("DOBITAK − GUBITAK (I − II)", vrednosti)
        self.assertIn(1.2, vrednosti)  # 1.200 din. u hiljadama
        odgovor = self.client.get(url, {"prikaz": "centri", "datum_od": "01.01.2026", "datum_do": "30.06.2026",
                                        "broj_godina": "1", "generisi": "1"})
        self.assertContains(odgovor, "nisu upisani profitni centri")

    def test_podesavanja_cuvaju_plan_centre_i_proveravaju_zbir(self, _):
        self.grant("finansije:nadzorni_odbor_podesavanja", "finansije:view_all")
        url = reverse("finansije:nadzorni_odbor_podesavanja")
        podaci = {"godina": "2026", "broj_zaposlenih": "", "plan_zaposlenih": "300", "plan_P1": "1200000",
                  "centri-TOTAL_FORMS": "3", "centri-INITIAL_FORMS": "0",
                  "centri-0-centar": "41", "centri-0-koeficijent": "60", "centri-1-centar": "43",
                  "centri-1-koeficijent": "30", "centri-2-centar": ""}
        self.assertContains(self.client.post(url, podaci), "mora biti 100%")
        podaci["centri-1-koeficijent"] = "40"
        self.assertRedirects(self.client.post(url, podaci), f"{url}?godina=2026")
        self.assertEqual(NadzorniPlan.objects.get(godina=2026, pozicija="P1").iznos, D("1200000"))
        self.assertEqual(NadzorniGodina.objects.get(godina=2026).plan_zaposlenih, 300)
        self.assertEqual(dict(NadzorniCentar.objects.values_list("centar", "koeficijent")), {"41": D("60"), "43": D("40")})
        # Nova godina dobija predlog centara iz poslednje upisane godine.
        odgovor = self.client.get(url, {"godina": "2027"})
        self.assertContains(odgovor, "Predlog je preuzet iz poslednje upisane godine")
        self.assertEqual(odgovor.context["centri_forme"].forms[1].initial["centar"], "43")
