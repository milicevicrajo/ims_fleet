"""Finansije na registru (plan prelaska na registar, korak 5): obuhvat iz dodela, centar iz registra."""
import datetime

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from finansije.access import can_view_all, polje_centra, visible_scope
from finansije.models import FinanceJob, LedgerEntry
from finansije.services.reports import grouped_report
from organizacija.models import DodelaUloge
from organizacija.services import flota
from organizacija.services.importer import run_import
from organizacija.services.putanja import osvezi_centre
from organizacija.test_prava import centar, uloga_sa_dozvolom
from organizacija.tests import ImportTestCase

NA_REGISTRU = override_settings(PRAVA_PO_REGISTRU={"finansije": True})


@NA_REGISTRU
class FinansijeNaRegistruTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        flota.povezi(modul="finansije")
        osvezi_centre(LedgerEntry.objects.all())
        self.uloga = uloga_sa_dozvolom("finansije-centra", "finansije:dashboard", "finansije:ledger")
        self.korisnik = get_user_model().objects.create_user("fin-41", password="x", allowed_center_codes="43")
        self.korisnik.roles.add(self.uloga)

    def dodeli(self, korisnik=None, **obuhvat):
        return DodelaUloge.objects.create(korisnik=korisnik or self.korisnik, uloga=self.uloga,
                                          vazi_od=datetime.date(2026, 1, 1), status=DodelaUloge.STATUS_AKTIVNA, **obuhvat)

    def vidi(self, korisnik=None):
        korisnik = get_user_model().objects.get(pk=(korisnik or self.korisnik).pk)  # svez obuhvat
        return set(visible_scope(LedgerEntry.objects.all(), korisnik).values_list("job_code", flat=True))

    def test_centar_na_knjizenju_je_iz_registra(self):
        self.assertEqual(polje_centra(), "org_centar")
        centri = dict(LedgerEntry.objects.values_list("job_code", "org_centar"))
        # Izvor vodi 430001 i 110002 bez centra; registar (potvrdjeno) ih vodi u 43 i 11.
        self.assertEqual((centri["430001"], centri["110002"], centri["209001"], centri["315400"]), ("43", "11", "2", "3"))
        self.assertIsNone(centri["vranjs"])  # nije u registru
        self.assertEqual(osvezi_centre(LedgerEntry.objects.all()), 0)  # ponovljeno — bez upisa

    def test_obuhvat_iz_dodele_a_ne_iz_starih_prava(self):
        self.assertEqual(self.vidi(), set())  # stara prava (43) vise ne odlucuju; bez dodele — nista
        self.dodeli(cvor_id=centar("41"))
        self.assertEqual(self.vidi(), {"410001"})
        self.assertFalse(can_view_all(self.korisnik))
        nacrt = get_user_model().objects.create_user("fin-nacrt", password="x")
        nacrt.roles.add(self.uloga)
        DodelaUloge.objects.create(korisnik=nacrt, uloga=self.uloga, cela_firma=True, vazi_od=datetime.date(2026, 1, 1))
        self.assertEqual(self.vidi(nacrt), set())  # nacrt ne odlucuje

    def test_cela_firma_vidi_sve(self):
        self.dodeli(cela_firma=True)
        self.assertEqual(len(self.vidi()), LedgerEntry.objects.count())
        self.assertTrue(can_view_all(get_user_model().objects.get(pk=self.korisnik.pk)))

    def test_izvestaj_po_centrima_iz_registra(self):
        _, redovi = grouped_report(LedgerEntry.objects.all(), FinanceJob.objects.all(), {"group": "center"})
        po_centru = {r["code"]: r["count"] for r in redovi}
        self.assertEqual(po_centru["43"], 2)  # 430111 i 430001
        self.assertEqual(po_centru["11"], 1)
        self.assertEqual(po_centru[""], 1)  # vranjs — neraspoređeno
        _, samo_43 = grouped_report(LedgerEntry.objects.all(), FinanceJob.objects.all(),
                                    {"group": "job", "center": "43", "include_empty": True})
        self.assertIn("430001", {r["code"] for r in samo_43})

    def test_ekran_postuje_obuhvat(self):
        LedgerEntry.objects.update(account="540000")  # rashod, da ga pregled prihoda i rashoda prikaze
        self.dodeli(cvor_id=centar("41"))
        self.client.force_login(self.korisnik)
        odgovor = self.client.get(reverse("finansije:report"), {"group": "center", "date_from": "2026-01-01",
                                                                  "date_to": "2026-12-31", "kind": "pnl"})
        self.assertEqual(odgovor.status_code, 200)
        self.assertTrue(odgovor.context["valid"], odgovor.context["form"].errors)
        self.assertEqual({r["code"] for r in odgovor.context["rows"]}, {"41"})

    def test_svi_ekrani_rade_na_registru(self):
        LedgerEntry.objects.update(account="540000")
        uloga = uloga_sa_dozvolom("fin-sve", "finansije:dashboard", "finansije:report", "finansije:jobs_data",
                                  "finansije:ledger", "finansije:job_card", "finansije:export")
        self.korisnik.roles.add(uloga)
        DodelaUloge.objects.create(korisnik=self.korisnik, uloga=uloga, cvor_id=centar("43"),
                                   vazi_od=datetime.date(2026, 1, 1), status=DodelaUloge.STATUS_AKTIVNA)
        self.client.force_login(self.korisnik)
        period = {"date_from": "2026-01-01", "date_to": "2026-12-31"}
        for ime, parametri in (("finansije:dashboard", period), ("finansije:report", {**period, "group": "job"}),
                               ("finansije:report", {**period, "group": "center", "center": "43"}),
                               ("finansije:report", {**period, "group": "center", "center": "__none__"}),
                               ("finansije:jobs_data", period), ("finansije:ledger", period),
                               ("finansije:job_card", {"job": "430001", "year": "2026"}),
                               ("finansije:export", {**period, "group": "center"})):
            with self.subTest(ime=ime, parametri=parametri):
                self.assertEqual(self.client.get(reverse(ime), parametri).status_code, 200)
        odgovor = self.client.get(reverse("finansije:report"), {**period, "group": "job"})
        self.assertEqual({r["code"] for r in odgovor.context["rows"]} - {""}, {"430111", "430001"})
