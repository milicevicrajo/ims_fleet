"""Srednji kurs NBS (od 02.11.2026.): čitanje stranice „Na željeni dan”, vikend, ponovna provera i raspored."""
from datetime import date
from decimal import Decimal as D
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from .models import KursnaLista, KursniDan, KursValute
from .services import kursna_lista


def stranica(broj=209, formirana="2.11.2026.", kursevi=(("EUR", "978", "EMU", "1", "117,5417"),
                                                       ("JPY", "392", "Japan", "100", "66,5959"))):
    redovi = "".join("<tr>" + "".join(f"<td>\n {c}\n</td>" for c in k) + "</tr>" for k in kursevi)
    return (f"<h5>Kursna lista NBS</h5><center><h6>\n KURSNA LISTA BR. {broj}\n</h6></center>"
            f"<center><h6>ZA ZVANIČNI SREDNJI KURS DINARA</h6></center>"
            f"<center><h6>FORMIRANA NA DAN {formirana} GODINE</h6></center>"
            "<table class='table'><thead><tr><th>OZNAKA VALUTE</th><th>ŠIFRA VALUTE</th><th>NAZIV ZEMLJE</th>"
            f"<th>VAŽI ZA</th><th>SREDNJI KURS</th></tr></thead><tbody>{redovi}</tbody></table>")


class CitanjeTests(SimpleTestCase):
    def test_broj_datum_formiranja_i_kursevi(self):
        broj, formirana, kursevi = kursna_lista.procitaj(stranica())
        self.assertEqual((broj, formirana), (209, date(2026, 11, 2)))
        self.assertEqual(kursevi[1], {"oznaka": "JPY", "sifra": "392", "zemlja": "Japan", "vazi_za": 100,
                                      "srednji_kurs": D("66.5959")})

    def test_stranica_bez_liste_je_greska_sa_porukom_nbs(self):
        with self.assertRaisesMessage(kursna_lista.NemaListe, "datum iz budućnosti"):
            kursna_lista.procitaj("<h5>Kursna lista NBS</h5><div class='alert'>Izabrali ste datum iz budućnosti.</div>")


class PreuzimanjeTests(TestCase):
    def preuzmi(self, strane, **kwargs):
        """`strane`: {dan: html}; dan bez strane — NBS ne odgovara."""
        def dan_html(_s, dan):
            if dan not in strane:
                raise ConnectionError("NBS ne radi")
            return kursna_lista.procitaj(strane[dan])
        with patch.object(kursna_lista, "preuzmi_dan", side_effect=dan_html), patch.object(kursna_lista.time, "sleep"):
            return kursna_lista.preuzmi(s=object(), **kwargs)

    def test_vikend_vazi_lista_petka_a_lista_se_upisuje_jednom(self):
        petak = stranica(208, "30.10.2026.")
        r = self.preuzmi({date(2026, 10, 30): petak, date(2026, 10, 31): petak, date(2026, 11, 1): petak,
                          date(2026, 11, 2): stranica()}, od=date(2026, 10, 30), do=date(2026, 11, 2))
        self.assertEqual((r["dana"], r["novih_lista"], r["gresaka"]), (4, 2, 0))
        self.assertEqual(KursnaLista.objects.count(), 2)
        self.assertEqual(KursValute.objects.count(), 4)
        self.assertEqual(KursniDan.objects.get(datum=date(2026, 11, 1)).lista.broj, 208)
        self.assertEqual(KursValute.objects.get(lista__broj=209, oznaka="EUR").srednji_kurs, D("117.5417"))
        # Radni dani sa sopstvenom listom: 30.10. i 2.11.
        radni = KursniDan.objects.filter(lista__datum_formiranja=kursna_lista.F("datum"))
        self.assertEqual(sorted(radni.values_list("datum", flat=True)), [date(2026, 10, 30), date(2026, 11, 2)])

    def test_dan_preuzet_pre_formiranja_liste_proverava_se_ponovo(self):
        petak = stranica(208, "30.10.2026.")
        self.preuzmi({date(2026, 10, 30): petak, date(2026, 11, 2): petak}, od=date(2026, 10, 30), do=date(2026, 11, 2),
                     najvise=None)
        self.assertEqual(KursniDan.objects.get(datum=date(2026, 11, 2)).lista.broj, 208)  # rano ujutru
        self.assertIn(date(2026, 11, 2), kursna_lista.dani_za_preuzimanje(date(2026, 10, 30), date(2026, 11, 2)))
        self.assertNotIn(date(2026, 10, 30), kursna_lista.dani_za_preuzimanje(date(2026, 10, 30), date(2026, 11, 2)))
        self.preuzmi({date(2026, 11, 2): stranica()}, od=date(2026, 11, 2), do=date(2026, 11, 2))
        self.assertEqual(KursniDan.objects.get(datum=date(2026, 11, 2)).lista.broj, 209)

    def test_greska_jednog_dana_ne_zaustavlja_ostale_i_najvise_ogranicava(self):
        r = self.preuzmi({date(2026, 11, 2): stranica()}, od=date(2026, 10, 30), do=date(2026, 11, 2), najvise=2)
        self.assertEqual((r["dana"], r["gresaka"], r["preostalo"]), (1, 1, 2))  # najnoviji dani prvi
        self.assertIn("01.11.2026.: ConnectionError", r["poslednja_greska"])
        self.assertIn("preostalo za sledeće pokretanje 2", kursna_lista.poruka(r))

    def test_zakazano_svakog_jutra_na_redu_sync(self):
        from django.conf import settings

        from core.management.commands.sync_celery_periodic_tasks import EXPECTED_PERIODIC_TASKS

        zadatak = next(s for s in EXPECTED_PERIODIC_TASKS if s["task"] == "finansije.tasks.kursna_lista_nbs_task")
        self.assertEqual((zadatak["hour"], zadatak["minute"]), ("8", "40"))
        self.assertEqual(settings.CELERY_TASK_ROUTES["finansije.tasks.kursna_lista_nbs_task"], {"queue": "sync"})
