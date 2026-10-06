"""Finansijski pregled po centrima: ZT centra = zbir ZT šifara, podela po raspodeli ZT, usklađenje sa Institutom."""
from datetime import date
from decimal import Decimal as D
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from .models import FinanceJob, LedgerEntry, SyncRun
from .services.pregled_centara import pregled_centara
from .services.shared_costs import shared_cost_many
from .test_shared_costs import rule
from .tests import job, save_entry

# Kontrolni primer (dokumentacija 6.1.7): osnovica službi B1 = −500, centar 41 dobija 40%, šifra 410001 50% centra.
PRAVILA = [rule("820001", month=2, criterion="1", profit="N"),
           rule("410001", month=2, coefficients=(D("50"), D("0"), D("0"))),
           rule("300001", month=2, coefficients=(D("100"), D("0"), D("0")))]
CENTRI_SIFARA = {"410001": (D("40"), D("0"), D("0")), "300001": (D("0"), D("0"), D("0"))}
RASPODELA = {"41": (D("40"), D("0"), D("0")), "3": (D("0"), D("0"), D("0"))}


def pravila(company, year, first, last, code):
    return PRAVILA, CENTRI_SIFARA


class PregledCentaraTests(TestCase):
    def setUp(self):
        for code, center in (("410001", "41"), ("820001", "82"), ("300001", "3")):
            FinanceJob.objects.create(**job(code, center))
        save_entry(number=1, credit=D("1000"))                                                    # 41: prihod 1000
        save_entry(number=2, account="51200", debit=D("200"), credit=D("0"))                       # 41: rashod 200
        save_entry(number=3, job_code="820001", center="82", account="52000", debit=D("500"), credit=D("0"))  # službe
        save_entry(number=4, job_code="300001", center="3", credit=D("100"))                       # naučni blok
        SyncRun.objects.create(company=1, year_from=2025, year_to=2026, status="success")
        patch("finansije.services.pregled_centara.allocation_rules", side_effect=pravila).start()
        patch("finansije.services.pregled_centara.raspodela_centara", return_value=RASPODELA).start()
        self.addCleanup(patch.stopall)

    def pregled(self):
        return pregled_centara(LedgerEntry.objects.all(), date(2026, 2, 1), date(2026, 2, 28), {2025, 2026})

    def test_grupe_zt_i_uskladjenje(self):
        rezultat = self.pregled()
        grupe = {g["key"]: g for g in rezultat["groups"]}
        self.assertEqual([g["key"] for g in rezultat["groups"]], ["profitni", "sluzbe", "ostali"])
        centar41 = grupe["profitni"]["rows"][0]
        self.assertEqual((centar41["code"], centar41["result"], centar41["zt"], centar41["expense_zt"], centar41["result_zt"]),
                         ("41", D("800"), D("-100"), D("300"), D("700")))
        self.assertEqual([r["code"] for r in grupe["sluzbe"]["rows"]], ["82"])
        self.assertEqual(grupe["sluzbe"]["total"]["result_zt"], D("-500"))
        self.assertEqual(grupe["ostali"]["rows"][0]["zt"], D("0"))  # koeficijent centra 0
        u = rezultat["uskladjenje"]
        self.assertEqual((u["posle_zt_centri"], u["pokrice"], u["institut"], u["sluzbe_posle"]),
                         (D("300"), D("100"), D("400"), D("-400")))
        self.assertEqual(u["posle_zt_centri"] + u["pokrice"], u["institut"])  # raspodela ne menja rezultat Instituta

    def test_zt_centra_jednak_zbiru_zt_sifara(self):
        with patch("finansije.services.shared_costs.allocation_rules", side_effect=pravila):
            sifre = shared_cost_many(1, {"410001"}, date(2026, 2, 1), date(2026, 2, 28))
        centar41 = self.pregled()["groups"][0]["rows"][0]
        self.assertEqual(-centar41["zt"], sifre["410001"]["cost"])

    def test_duplirana_pravila_daju_nedostupno(self):
        with patch("finansije.services.pregled_centara.allocation_rules",
                   return_value=(PRAVILA + [PRAVILA[1]], CENTRI_SIFARA)):
            rezultat = self.pregled()
        self.assertIsNone(rezultat["total"]["zt"])
        self.assertIsNone(rezultat["uskladjenje"])
        self.assertIsNone(rezultat["groups"][0]["rows"][0]["result_zt"])

    def test_ogranicen_korisnik_ne_vidi_uskladjenje(self):
        rezultat = pregled_centara(LedgerEntry.objects.all(), date(2026, 2, 1), date(2026, 2, 28), {2026}, cela_firma=False)
        self.assertIsNone(rezultat["uskladjenje"])

    def test_finansijski_pregled_prikazuje_grupe(self):
        self.client.force_login(get_user_model().objects.create_superuser("fin-pregled", "f@example.invalid", "x"))
        odgovor = self.client.get(reverse("finansije:dashboard"), {"date_from": "2026-02-01", "date_to": "2026-02-28"})
        for tekst in ("Rezultat po centrima", "Profitni centri", "Zajedničke službe (neprofitni centri)", "Ostali centri",
                      "Rezultat Instituta (bez i posle ZT isti)", "Rashodi sa ZT"):
            self.assertContains(odgovor, tekst)
        with patch("finansije.services.pregled_centara.allocation_rules", side_effect=DatabaseError):
            odgovor = self.client.get(reverse("finansije:dashboard"), {"date_from": "2026-02-01", "date_to": "2026-02-28"})
        self.assertContains(odgovor, "trenutno nije dostupna")
