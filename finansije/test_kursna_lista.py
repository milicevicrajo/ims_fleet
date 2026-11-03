"""Srednji kurs NBS (od 02.11.2026.): čitanje stranice „Na željeni dan”, vikend, preuzimanje i ekran."""
from datetime import date
from decimal import Decimal as D
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models import F
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from openpyxl import load_workbook

from core.models import PermissionCode, Role
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


PETAK = stranica(208, "30.10.2026.", (("EUR", "978", "EMU", "1", "117,5367"), ("JPY", "392", "Japan", "100", "66,6648")))
STRANE = {date(2026, 10, 30): PETAK, date(2026, 10, 31): PETAK, date(2026, 11, 1): PETAK, date(2026, 11, 2): stranica()}


def preuzmi(strane, **kwargs):
    """`strane`: {dan: html}; dan bez strane — NBS ne odgovara. Vraća (rezultat, traženi dani)."""
    trazeni = []

    def dan_html(_s, dan):
        trazeni.append(dan)
        if dan not in strane:
            raise ConnectionError("NBS ne radi")
        return kursna_lista.procitaj(strane[dan])
    with patch.object(kursna_lista, "preuzmi_dan", side_effect=dan_html), patch.object(kursna_lista.time, "sleep"):
        return kursna_lista.preuzmi(s=object(), **kwargs), trazeni


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
    def test_vikend_vazi_lista_petka_a_lista_se_upisuje_jednom(self):
        r, _ = preuzmi(STRANE, od=date(2026, 10, 30), do=date(2026, 11, 2))
        self.assertEqual((r["dana"], r["novih_lista"], r["gresaka"]), (4, 2, 0))
        self.assertEqual(KursValute.objects.count(), 4)
        self.assertEqual(KursniDan.objects.get(datum=date(2026, 11, 1)).lista.broj, 208)
        radni = KursniDan.objects.filter(lista__datum_formiranja=F("datum"))
        self.assertEqual(sorted(radni.values_list("datum", flat=True)), [date(2026, 10, 30), date(2026, 11, 2)])

    def test_komanda_dopunjuje_samo_dane_bez_liste_a_greska_ne_zaustavlja_ostale(self):
        preuzmi({date(2026, 11, 2): stranica()}, od=date(2026, 11, 2), do=date(2026, 11, 2))
        r, trazeni = preuzmi({d: s for d, s in STRANE.items() if d != date(2026, 10, 31)},
                             od=date(2026, 10, 30), do=date(2026, 11, 2))
        self.assertEqual(trazeni, [date(2026, 11, 1), date(2026, 10, 31), date(2026, 10, 30)])  # najnoviji prvi
        self.assertEqual((r["dana"], r["gresaka"]), (2, 1))
        self.assertIn("31.10.2026.: ConnectionError", kursna_lista.poruka(r))

    def test_zastita_od_botova_zaustavlja_preuzimanje(self):
        zastita = '<script>window["bobcmn"] = "...TSPD/..."</script>'
        r, trazeni = preuzmi({date(2026, 11, 2): zastita, **{d: s for d, s in STRANE.items() if d != date(2026, 11, 2)}},
                             od=date(2026, 10, 30), do=date(2026, 11, 2))
        self.assertEqual(trazeni, [date(2026, 11, 2)])  # posle blokade nijedan upit vise
        self.assertEqual((r["dana"], r["gresaka"]), (0, 1))
        self.assertIn("zaštitu od botova", kursna_lista.poruka(r))

    @patch("finansije.services.kursna_lista.timezone.localdate", return_value=date(2026, 11, 2))
    def test_automatski_ponovo_cita_poslednjih_5_dana_i_ispravlja_rano_preuzet_dan(self, _):
        preuzmi({date(2026, 11, 2): PETAK}, od=date(2026, 11, 2), do=date(2026, 11, 2))  # pre formiranja liste
        trazeni = []

        def dan_html(_s, dan):
            trazeni.append(dan)
            return kursna_lista.procitaj(STRANE.get(dan, PETAK))
        with patch.object(kursna_lista, "preuzmi_dan", side_effect=dan_html), patch.object(kursna_lista.time, "sleep"):
            kursna_lista.preuzmi_poslednje(s=object())
        self.assertEqual(trazeni, [date(2026, 11, d) for d in (2, 1)] + [date(2026, 10, d) for d in (31, 30, 29)])
        self.assertEqual(KursniDan.objects.get(datum=date(2026, 11, 2)).lista.broj, 209)

    def test_zakazano_svakog_jutra_na_redu_sync(self):
        from django.conf import settings

        from core.management.commands.sync_celery_periodic_tasks import EXPECTED_PERIODIC_TASKS

        zadatak = next(s for s in EXPECTED_PERIODIC_TASKS if s["task"] == "finansije.tasks.kursna_lista_nbs_task")
        self.assertEqual((zadatak["hour"], zadatak["minute"]), ("8", "40"))
        self.assertEqual(settings.CELERY_TASK_ROUTES["finansije.tasks.kursna_lista_nbs_task"], {"queue": "sync"})


class EkranTests(TestCase):
    def setUp(self):
        preuzmi(STRANE, od=date(2026, 10, 30), do=date(2026, 11, 2))
        self.user = get_user_model().objects.create_user("kurs", password="x")
        self.client.force_login(self.user)
        self.url = reverse("finansije:kursna_lista")
        self.period = {"datum_od": "30.10.2026", "datum_do": "02.11.2026"}

    def dozvoli(self):
        uloga = Role.objects.create(name="Kurs", slug="kurs")
        uloga.permissions.add(PermissionCode.objects.get_or_create(code="finansije:kursna_lista")[0])
        self.user.roles.add(uloga)

    def test_trazi_dozvolu(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_proseci_svih_valuta_po_radnim_danima(self):
        self.dozvoli()
        odgovor = self.client.get(self.url, self.period)
        redovi = {r["celije"][0][0]: r for r in odgovor.context["tabela"]["redovi"]}
        self.assertEqual(set(redovi), {"EUR", "JPY"})
        self.assertEqual(kursna_lista.proseci(date(2026, 10, 30), date(2026, 11, 2))[0]["prosek"], D("117.5392"))
        self.assertEqual(redovi["EUR"]["celije"][7][0], "2")  # dve liste — vikend se ne broji
        self.assertContains(odgovor, 'class="form-control js-date"', count=2)
        self.assertContains(odgovor, "Srednji kurs NBS")  # stavka u meniju

    def test_jedna_valuta_po_danima_i_excel(self):
        self.dozvoli()
        odgovor = self.client.get(self.url, dict(self.period, valuta="JPY"))
        self.assertEqual(odgovor.context["sazetak"]["prosek"], D("66.6304"))  # (66,6648 + 66,5959) / 2
        self.assertEqual([r["prigusen"] for r in odgovor.context["tabela"]["redovi"]], [False, True, True, False])
        self.assertEqual(odgovor.context["tabela"]["redovi"][1]["celije"][2][0], "208/2026")
        excel = self.client.get(self.url, dict(self.period, valuta="JPY", izvoz="xlsx"))
        vrednosti = [c for r in load_workbook(BytesIO(excel.content)).active.iter_rows(values_only=True) for c in r
                     if c is not None]
        self.assertIn(66.5959, vrednosti)
        self.assertIn("Srednji kurs JPY po danima", vrednosti)

    def test_podrazumevano_tekuci_mesec(self):
        self.dozvoli()
        with patch("finansije.views.timezone.localdate", return_value=date(2026, 11, 2)):
            odgovor = self.client.get(self.url)
        self.assertEqual(odgovor.context["form"].cleaned_data["datum_od"], date(2026, 11, 1))
        self.assertEqual(len(odgovor.context["tabela"]["redovi"]), 2)
