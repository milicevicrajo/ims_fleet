"""Finansije → Zajednički troškovi po vrsti, OJ službe, centrima i OJ primaoca (od 07.10.2026.)."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finansije.services.zajednicki_troskovi import vrsta, zajednicki_troskovi
from finansije.tests import save_entry

D = Decimal
PRAVILA = [
    {"code": "820001", "month": 2, "criterion": "1", "coefficients": (D("0"), D("0"), D("0")), "profit": "N"},
    {"code": "410001", "month": 2, "criterion": "", "coefficients": (D("100"), D("0"), D("0")), "profit": "P"},
    {"code": "430001", "month": 2, "criterion": "", "coefficients": (D("100"), D("0"), D("0")), "profit": "P"},
]
CENTRI = {"410001": (D("60"), D("0"), D("0")), "430001": (D("40"), D("0"), D("0"))}


@patch("finansije.services.zajednicki_troskovi.allocation_rules", return_value=(PRAVILA, CENTRI))
class ZajednickiTroskoviTests(TestCase):
    def setUp(self):
        sluzba = dict(center="82", job_code="820001", job_name="Opšta služba", organizational_unit=82,
                      organizational_unit_name="Služba za opšte poslove")
        save_entry(number=1, account="52000", debit=D("100"), credit=D("0"), **sluzba)      # zarade službe
        save_entry(number=2, account="51330", debit=D("20"), credit=D("0"), **sluzba)       # struja
        save_entry(number=3, account="61000", credit=D("10"), **sluzba)                     # prihod službe
        save_entry(number=4, credit=D("500"))                                                # 41 / 410001
        save_entry(number=5, center="43", job_code="430001", job_name="Posao C", organizational_unit=43, credit=D("300"))

    def obracun(self):
        return zajednicki_troskovi(date(2026, 2, 1), date(2026, 2, 28), {2026})

    def test_vrste_konta(self, _pravila):
        self.assertEqual([vrsta(k) for k in ("52000", "51330", "51310", "53921", "55080", "54000", "61000", "53100")],
                         ["sluzbe", "energija", "energija", "komunalije", "odrzavanje", "amortizacija", "prihodi", "usluge"])

    def test_osnovica_i_raspodela_po_vrsti(self, _pravila):
        z = self.obracun()
        self.assertEqual((z["osnovica"], z["sluzbe"], z["ostalo"], z["raspodeljeno"]), (D("110.00"), D("100.00"), D("10.00"), D("110.00")))
        self.assertEqual(z["sluzbe_udeo"], D("90.9"))
        centri = {r["code"]: r for r in z["centri"]}
        self.assertEqual((centri["41"]["ukupno"], centri["41"]["udeo"]), (D("66.00"), D("60.0")))
        # svaka vrsta se deli istim koeficijentima: 60% od 100 zarada, 20 struje i −10 prihoda
        self.assertEqual((centri["41"]["vrste"]["sluzbe"], centri["41"]["vrste"]["energija"], centri["41"]["vrste"]["prihodi"]),
                         (D("60.00"), D("12.00"), D("-6.00")))
        self.assertEqual(centri["43"]["ukupno"], D("44.00"))
        izvor = z["izvor_oj"][0]
        self.assertEqual((izvor["code"], izvor["naziv"], izvor["ukupno"], izvor["broj_sifara"]), ("82", "Služba za opšte poslove", D("110.00"), 1))
        self.assertEqual({r["code"] for r in z["oj_primaoca"]}, {"41", "43"})

    def test_ekran_i_pristup(self, _pravila):
        admin = get_user_model().objects.create_superuser("zt-admin", "zt@example.invalid", "x")
        self.client.force_login(admin)
        with patch("finansije.views.pokrivene_godine", return_value={2026}):
            odgovor = self.client.get(reverse("finansije:zajednicki_troskovi"), {"date_from": "2026-02-01", "date_to": "2026-02-28"})
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, "Zajedničke službe (zarade)")
        self.assertContains(odgovor, "Energija i grejanje")
        self.assertEqual(odgovor.context["grafikoni"]["centri"]["vrednosti"]["sluzbe"], [60.0, 40.0])
        with patch("finansije.views.can_view_all", return_value=False):
            self.assertEqual(self.client.get(reverse("finansije:zajednicki_troskovi")).status_code, 403)
