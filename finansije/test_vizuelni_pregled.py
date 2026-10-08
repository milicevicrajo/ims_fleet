"""Finansije → Vizuelni pregled poslovanja po centrima i šiframa posla (od 07.10.2026.)."""
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finansije.models import FinanceJob
from finansije.tests import job, save_entry


@patch("finansije.services.kontni_plan.nazivi_konta", return_value={"51": "Troškovi materijala", "52": "Troškovi zarada"})
class VizuelniPregledTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("viz-admin", "viz@example.invalid", "test")
        FinanceJob.objects.create(**job())
        FinanceJob.objects.create(**job("420001", "42", name="Posao B"))
        save_entry()                                                                       # 41: prihod 100
        save_entry(number=2, account="51000", debit=Decimal("40"), credit=Decimal("0"))    # 41: materijal 40
        save_entry(number=3, account="52000", debit=Decimal("20"), credit=Decimal("0"))    # 41: zarade 20
        save_entry(number=4, center="42", job_code="420001", job_name="Posao B", credit=Decimal("300"))  # 42: prihod 300
        save_entry(number=5, center="42", job_code="420001", job_name="Posao B", account="52000",
                   debit=Decimal("340"), credit=Decimal("0"))                              # 42: zarade 340 → gubitak
        self.client.force_login(self.user)
        self.params = {"date_from": "2026-02-01", "date_to": "2026-02-28"}

    def test_centri_ucesca_struktura_i_tok(self, _plan):
        with patch("finansije.views.centri_sa_zt", return_value=None):
            odgovor = self.client.get(reverse("finansije:vizuelni_pregled"), self.params)
        self.assertEqual(odgovor.status_code, 200)
        v = odgovor.context["v"]
        self.assertEqual((v["ukupno"]["revenue"], v["ukupno"]["expense"], v["ukupno"]["result"]),
                         (Decimal("400"), Decimal("400"), Decimal("0")))
        centri = {r["code"]: r for r in v["jedinice"]}
        self.assertEqual(centri["42"]["revenue_share"], Decimal("75.0"))
        self.assertEqual(centri["41"]["expense_share"], Decimal("15.0"))
        self.assertEqual(centri["41"]["result_share"], Decimal("100.0"))  # jedini sa dobiti
        self.assertIsNone(centri["42"]["result_share"])                   # gubitak nije u zaradi
        self.assertEqual(centri["41"]["margin"], Decimal("40.0"))
        self.assertEqual([(s["code"], s["expense"]) for s in v["struktura"]], [("zarade", Decimal("360")), ("materijal", Decimal("40"))])
        self.assertEqual(centri["41"]["struktura"]["materijal"], Decimal("40"))
        self.assertEqual([s["key"] for s in v["grafikoni"]["struktura_po_jedinici"]["datasets"]], ["zarade", "materijal"])
        self.assertEqual(v["grafikoni"]["tok"]["labels"], ["feb"])
        self.assertIn("center=41", centri["41"]["url"])
        podaci = json.loads(odgovor.content.decode().split('id="vp-podaci" type="application/json">')[1].split("</script>")[0])
        self.assertEqual(podaci["jedinice"]["revenue"], [300.0, 100.0])
        self.assertContains(odgovor, "chart.umd.min.js")

    def test_centar_prikazuje_sifre_posla(self, _plan):
        odgovor = self.client.get(reverse("finansije:vizuelni_pregled"), dict(self.params, center="42"))
        self.assertEqual(odgovor.status_code, 200)
        v = odgovor.context["v"]
        self.assertTrue(v["po_siframa"])
        self.assertEqual([(r["code"], r["name"]) for r in v["jedinice"]], [("420001", "Posao B")])
        self.assertContains(odgovor, "Svi centri")

    def test_neaktivne_sifre_se_ne_prikazuju(self, _plan):
        from fleet.support.registar import Registar

        save_entry(number=6, center="42", job_code="420002", job_name="Ugašen posao", credit=Decimal("70"))
        with patch.object(Registar, "aktivna_sifra", lambda self, sifra: (sifra or "").strip() != "420002"), \
                patch("finansije.views.centri_sa_zt", return_value=None):
            centar = self.client.get(reverse("finansije:vizuelni_pregled"), dict(self.params, center="42")).context["v"]
            pregled = self.client.get(reverse("finansije:dashboard"), self.params).context
        self.assertEqual([r["code"] for r in centar["jedinice"]], ["420001"])
        self.assertEqual(centar["ukupno"]["revenue"], Decimal("300"))  # zbir se slaže sa prikazanim šiframa
        sifre = next(g for g in pregled["chart_groups"] if g["dimension"] == "job")
        self.assertNotIn("420002", [r["code"] for r in sifre["rows"]])
        self.assertEqual(pregled["totals"]["revenue"], Decimal("470"))  # ukupno za period ostaje celo

    def test_dugme_na_finansijskom_pregledu_i_dozvola(self, _plan):
        with patch("finansije.views.centri_sa_zt", return_value=None):
            pregled = self.client.get(reverse("finansije:dashboard"), self.params)
        self.assertContains(pregled, reverse("finansije:vizuelni_pregled") + "?date_from=2026-02-01&amp;date_to=2026-02-28")
        bez = get_user_model().objects.create_user("bez-finansija", password="x")
        self.client.force_login(bez)
        self.assertEqual(self.client.get(reverse("finansije:vizuelni_pregled"), self.params).status_code, 403)

    def test_struktura_sa_zajednickim_troskovima(self, _plan):
        from finansije.models import LedgerEntry
        from finansije.services.vizuelni_pregled import vizuelni_pregled

        v = vizuelni_pregled(LedgerEntry.objects.all(), zt_po_jedinici={"41": (Decimal("30"), Decimal("10")),
                                                                         "99": (Decimal("5"), Decimal("5"))})
        centri = {r["code"]: r for r in v["jedinice"]}
        self.assertEqual((centri["41"]["struktura"]["zt_sluzbe"], centri["41"]["struktura"]["zt_ostalo"]), (Decimal("30"), Decimal("10")))
        self.assertEqual(centri["41"]["ukupno_sa_zt"], Decimal("100"))  # 40 materijal + 20 zarade + 40 ZT
        self.assertEqual(v["ukupno_sa_zt"], Decimal("440"))             # centar 99 nije u prikazu
        self.assertEqual([s["code"] for s in v["struktura"]][-2:], ["zt_sluzbe", "zt_ostalo"])

    def test_marza_bez_poslovnog_bloka(self, _plan):
        save_entry(number=9, center="2", job_code="209001", job_name="Organizacija", credit=Decimal("50"))
        with patch("finansije.views.centri_sa_zt", return_value=None):
            v = self.client.get(reverse("finansije:vizuelni_pregled"), self.params).context["v"]
        self.assertIn("2", {r["code"] for r in v["jedinice"]})
        self.assertNotIn("2", [l.split(" ")[0] for l in v["grafikoni"]["marza"]["labels"]])
        self.assertEqual(len(v["grafikoni"]["marza"]["labels"]), 2)


    def test_marza_bez_neprofitnih_centara(self, _plan):
        from finansije.models import LedgerEntry
        from finansije.services.vizuelni_pregled import vizuelni_pregled

        save_entry(number=10, center="81", job_code="812004", job_name="Knjigovodstvo", credit=Decimal("10"))
        red = lambda c: {"code": c, "result_zt": None}
        podela = {"groups": [{"key": "profitni", "rows": [red("41"), red("42")]},
                             {"key": "sluzbe", "rows": [red("81")]}], "available": True}
        v = vizuelni_pregled(LedgerEntry.objects.all(), centri_zt=podela)
        marza = [l.split(" ")[0] for l in v["grafikoni"]["marza"]["labels"]]
        self.assertNotIn("81", marza)
        self.assertEqual(sorted(marza), ["41", "42"])
        self.assertNotIn("81", [l.split(" ")[0] for l in v["grafikoni"]["rezultat"]["labels"]])  # ni neto rezultat
        self.assertIn("81", {r["code"] for r in v["jedinice"]})  # ostaje u ostalim grafikonima i tabeli
