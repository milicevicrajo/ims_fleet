"""Statistika rodne ravnopravnosti (Obrazac 1) iz kadrovske baze (od 07.10.2026.)."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import PermissionCode, Role

from .services.rodna_ravnopravnost import statistika

PRAZNO, NIKAD = date(1900, 1, 1), date(3000, 1, 1)
DANAS = date(2026, 10, 7)
RAZLOZI = {"1": "PENZIJA", "6": "ISTEK RADA NA ODREDJENO VREME"}


def radnik(broj, pol, rodjen, dolazak, odlazak=PRAZNO, *, aktivan=True, pred=1, jmbg=None, sprema=71, polozaj=False, razlog=""):
    return {"preduzece": pred, "broj": broj, "jmbg": jmbg or f"JMBG{broj}", "pol": pol, "rodjen": rodjen,
            "dolazak": dolazak, "odlazak": odlazak, "aktivan": aktivan, "sprema": sprema, "polozaj": polozaj,
            "razlog": razlog}


RADNICI = [
    radnik(1, "Z", date(1990, 5, 1), date(2015, 1, 1), sprema=80, polozaj=True),
    radnik(2, "M", date(1985, 1, 1), date(2010, 1, 1), NIKAD, sprema=40),
    radnik(3, "M", date(1960, 1, 1), date(2000, 1, 1), date(2025, 3, 31), aktivan=False, razlog="1"),  # penzija 2025.
    radnik(4, "Z", date(1999, 6, 1), date(2025, 2, 1), sprema=60),                                    # prijem 2025.
    radnik(5, "M", date(1980, 1, 1), date(2022, 1, 1), date(2021, 6, 30), sprema=30),                  # ponovo zaposlen
    radnik(6, "M", date(1970, 1, 1), date(2018, 1, 1), aktivan=False),                                 # ne zna se kad je otišao
    # ista osoba u oba preduzeća: van radnog odnosa do 31.01.2025., pa radni odnos od 01.02.2025.
    radnik(7, "Z", date(1995, 1, 1), date(2023, 1, 1), date(2025, 1, 31), aktivan=False, pred=2, jmbg="ISTA", razlog="6"),
    radnik(8, "Z", date(1995, 1, 1), date(2025, 2, 1), pred=1, jmbg="ISTA", sprema=72),
]


class StatistikaTests(TestCase):
    def test_obrazac_za_2025(self):
        s = statistika(2025, RADNICI, RAZLOZI, danas=DANAS)
        self.assertEqual(s["na_dan"], date(2025, 12, 31))
        self.assertEqual((s["ukupno"]["ukupno"], s["ukupno"]["zene"], s["ukupno"]["muski"]), (5, 3, 2))  # 1, 2, 4, 5, ISTA
        starost = {r["naziv"]: r for r in s["starost"]}
        self.assertEqual((starost["Od 21–30 godina"]["ukupno"], starost["Od 21–30 godina"]["zene"]), (2, 2))
        self.assertEqual(starost["Od 31–40 godina"]["udeo"], Decimal("40.0"))  # 1 i 2 od 5
        sprema = {r["rb"]: r for r in s["sprema"]}
        self.assertEqual((sprema["8"]["zene"], sprema["7"]["zene"], sprema["2"]["muski"]), (1, 1, 1))
        polozaji = {r["naziv"]: r for r in s["polozaji"]}
        self.assertEqual((polozaji["Lica na položajima"]["zene"], polozaji["Lica na položajima"]["udeo_zena"]), (1, Decimal("33.3")))
        # prijem: samo radnik 4 (ISTA je samo prešla iz van radnog odnosa u radni odnos)
        self.assertEqual((s["prijem"]["ukupno"], s["prijem"]["zene"]), (1, 1))
        # prestanak: samo radnik 3 (penzija); ISTA nastavlja da radi
        self.assertEqual(s["prestanak"]["ukupno"], 1)
        self.assertEqual([(r["naziv"], r["ukupno"]) for r in s["prestanak"]["razlozi"]], [("PENZIJA", 1)])

    def test_tekuca_godina_je_danasnje_stanje(self):
        s = statistika(2026, RADNICI, RAZLOZI, danas=DANAS)
        self.assertEqual((s["na_dan"], s["tekuca"]), (DANAS, True))
        self.assertEqual(s["ukupno"]["ukupno"], 5)


@patch("hr.services.rodna_ravnopravnost.procitaj_izvor", return_value=(RADNICI, RAZLOZI))
class EkranTests(TestCase):
    def setUp(self):
        self.korisnik = get_user_model().objects.create_user("kadrovi-rodna", password="x")
        self.uloga = Role.objects.create(name="Kadrovi rodna", slug="kadrovi-rodna")
        for kod in ("hr:analitika", "hr:rodna_ravnopravnost"):
            self.uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        self.korisnik.roles.add(self.uloga)
        self.client.force_login(self.korisnik)

    def test_ekran_izvoz_i_dugme_na_analitici(self, _izvor):
        adresa = reverse("hr:rodna_ravnopravnost")
        self.assertContains(self.client.get(reverse("hr:analitika")), adresa)
        strana = self.client.get(adresa, {"godina": 2025})
        self.assertContains(strana, "Statistika rodne ravnopravnosti")
        self.assertContains(strana, "Zaposleni i radno angažovani")
        self.assertContains(strana, "3 (60,0%)")  # žene od ukupno 5
        self.assertContains(strana, "Popunjava se ručno")
        xlsx = self.client.get(adresa, {"godina": 2025, "izvoz": "xlsx"})
        self.assertEqual(xlsx["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertIn("rodna_ravnopravnost_2025.xlsx", xlsx["Content-Disposition"])
        pdf = self.client.get(adresa, {"godina": 2025, "izvoz": "pdf"})
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_bez_dozvole(self, _izvor):
        PermissionCode.objects.get(code="hr:rodna_ravnopravnost").roles.clear()
        self.assertEqual(self.client.get(reverse("hr:rodna_ravnopravnost")).status_code, 403)
        self.assertNotContains(self.client.get(reverse("hr:analitika")), reverse("hr:rodna_ravnopravnost"))
