"""Finansije → SEF fakture: preuzimanje sa SEF-a (lazni klijent), UBL, promene statusa, meka veza i ekrani."""
import datetime
import shutil
import tempfile
from decimal import Decimal
from unittest import mock
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import PermissionCode, Role
from finansije.models import LedgerEntry
from finansije.sef_models import SefFaktura, SefPromena, SefSinhronizacija
from finansije.services import sef

DANAS = datetime.date(2026, 9, 30)

UBL = b"""<?xml version="1.0" encoding="utf-8"?>
<env:DocumentEnvelope xmlns:env="urn:eFaktura:MinFinrs:envelop:schema"><env:DocumentBody>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
 <cbc:ID>IF-120/2026</cbc:ID><cbc:IssueDate>2026-09-10</cbc:IssueDate><cbc:DueDate>2026-10-10</cbc:DueDate>
 <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode><cbc:DocumentCurrencyCode>RSD</cbc:DocumentCurrencyCode>
 <cac:AccountingSupplierParty><cac:Party><cac:PartyName><cbc:Name>Institut IMS</cbc:Name></cac:PartyName></cac:Party></cac:AccountingSupplierParty>
 <cac:AccountingCustomerParty><cac:Party>
  <cac:PartyTaxScheme><cbc:CompanyID>RS101234567</cbc:CompanyID></cac:PartyTaxScheme>
  <cac:PartyLegalEntity><cbc:RegistrationName>Kupac DOO</cbc:RegistrationName><cbc:CompanyID>07654321</cbc:CompanyID></cac:PartyLegalEntity>
 </cac:Party></cac:AccountingCustomerParty>
 <cac:Delivery><cbc:ActualDeliveryDate>2026-09-09</cbc:ActualDeliveryDate></cac:Delivery>
 <cac:TaxTotal><cbc:TaxAmount currencyID="RSD">200.00</cbc:TaxAmount></cac:TaxTotal>
 <cac:LegalMonetaryTotal><cbc:TaxExclusiveAmount currencyID="RSD">1000.00</cbc:TaxExclusiveAmount>
  <cbc:PayableAmount currencyID="RSD">1200.00</cbc:PayableAmount></cac:LegalMonetaryTotal>
</Invoice></env:DocumentBody></env:DocumentEnvelope>"""


class LazniKlijent:
    url = "https://efakturatest.mfin.gov.rs"

    def __init__(self):
        self.ulazne = [{
            "InvoiceId": 494482, "GlobUniqId": "dd3a", "DocumentNumber": " MF3814/25 ", "DocumentType": "Invoice",
            "CirInvoiceId": None, "Status": "New", "SupplierName": "Dobavljač DOO", "SupplierRegistrationNumber": "21436587",
            "SupplierVatRegistrationNumber": "123456789", "Amount": 220.0, "SumWithoutVat": 200.0, "VatAmount": 20.0,
            "Currency": "RSD", "DeliveryDate": "2026-09-01T10:59:41.0000000+00:00", "DueDate": None,
            "SentDate": "2026-09-02T11:01:10.5030093+00:00"}]
        self.izlazne = {"Sent": [4831]}
        self.promene_po_danu = {}
        self.ubl_poziva = 0

    def ulazne_pregled(self, od, do):
        return self.ulazne if od <= datetime.date(2026, 9, 2) <= do else []

    def izlazne_ids(self, status, od, do):
        return self.izlazne.get(status, []) if od <= datetime.date(2026, 9, 10) <= do else []

    def ubl(self, smer, sef_id):
        self.ubl_poziva += 1
        return UBL

    def promene(self, smer, dan):
        return self.promene_po_danu.get((smer, dan), [])

    def pdf(self, smer, sef_id):
        return b"%PDF-1.7 test", ""

    def verzija(self):
        return "3.14"


class SinhronizacijaTests(TestCase):
    def sync(self, klijent, **kw):
        kw.setdefault("pdf", False)  # PDF u sinhronizaciji proverava EkraniTests (privremen MEDIA_ROOT)
        return sef.sinhronizuj(datetime.date(2026, 8, 20), DANAS, klijent=klijent, danas=DANAS, **kw)

    def test_ulazne_iz_pregleda_i_izlazne_iz_ubl(self):
        klijent = LazniKlijent()
        run = self.sync(klijent)
        self.assertEqual(run.status, "success")
        ulazna = SefFaktura.objects.get(smer="ulazna")
        self.assertEqual((ulazna.broj, ulazna.broj_kljuc, ulazna.partner_pib, ulazna.iznos, ulazna.status),
                         ("MF3814/25", "MF3814/25", "123456789", Decimal("220.00"), "New"))
        self.assertEqual(ulazna.datum_prometa, datetime.date(2026, 9, 1))
        izlazna = SefFaktura.objects.get(smer="izlazna")
        self.assertEqual((izlazna.sef_id, izlazna.broj, izlazna.partner_naziv, izlazna.partner_pib, izlazna.partner_mb),
                         (4831, "IF-120/2026", "Kupac DOO", "101234567", "07654321"))
        self.assertEqual((izlazna.iznos, izlazna.osnovica, izlazna.pdv, izlazna.status),
                         (Decimal("1200.00"), Decimal("1000.00"), Decimal("200.00"), "Sent"))
        self.assertEqual((izlazna.datum_izdavanja, izlazna.datum_prometa), (datetime.date(2026, 9, 10), datetime.date(2026, 9, 9)))
        self.assertEqual(run.counts["novih"], 2)
        # ponovljeno preuzimanje: bez duplikata i bez ponovnog citanja UBL-a za poznatu fakturu
        self.sync(klijent)
        self.assertEqual(SefFaktura.objects.count(), 2)
        self.assertEqual(klijent.ubl_poziva, 1)
        # izlazna bez broja (bila „u slanju”, bez UBL-a) dobija UBL pri sledecem preuzimanju
        SefFaktura.objects.filter(smer="izlazna").update(broj="", broj_kljuc="")
        self.sync(klijent)
        self.assertEqual((SefFaktura.objects.get(smer="izlazna").broj, klijent.ubl_poziva), ("IF-120/2026", 2))
        # promenjen status izlazne se upisuje bez UBL-a
        klijent.izlazne = {"Approved": [4831]}
        self.assertEqual(self.sync(klijent).counts["azurirano"], 1)
        self.assertEqual(SefFaktura.objects.get(smer="izlazna").status, "Approved")

    def test_promene_statusa_i_istorija(self):
        klijent = LazniKlijent()
        juce = DANAS - datetime.timedelta(days=1)
        klijent.promene_po_danu[("ulazna", juce)] = [
            {"EventId": 5653, "Date": "2026-09-29T07:33:04.2819462", "NewInvoiceStatus": "Approved",
             "PurchaseInvoiceId": 494482, "Comment": "prihvaćeno"},
            {"EventId": 5654, "Date": "2026-09-29T08:00:00", "NewInvoiceStatus": "Seen", "PurchaseInvoiceId": 777}]
        run = self.sync(klijent)
        self.assertEqual((run.counts["promena"], run.counts["promena_bez_fakture"]), (2, 1))
        self.assertEqual(SefFaktura.objects.get(smer="ulazna").status, "Approved")
        self.assertEqual(SefPromena.objects.count(), 2)
        self.sync(klijent)  # isti dogadjaj se ne upisuje dvaput
        self.assertEqual(SefPromena.objects.count(), 2)

    def test_greska_se_belezi(self):
        klijent = LazniKlijent()
        klijent.ulazne_pregled = mock.Mock(side_effect=sef.SefGreska("SEF je vratio grešku 500"))
        with self.assertRaises(sef.SefGreska):
            self.sync(klijent)
        run = SefSinhronizacija.objects.get()
        self.assertEqual((run.status, run.error), ("error", "SEF je vratio grešku 500"))

    @override_settings(SEF_API_KEY="")
    def test_bez_kljuca_nije_podesen(self):
        with self.assertRaises(sef.SefNijePodesen):
            sef.Klijent()
        from finansije.tasks import sync_sef_task

        with mock.patch("core.tasks._run_with_singleton_lock", side_effect=lambda task_name, lock_ttl_seconds, fn: fn()):
            self.assertIn("SEF nije podešen", sync_sef_task())

    @override_settings(SEF_API_KEY="test-kljuc", SEF_API_URL="https://efakturatest.mfin.gov.rs")
    def test_klijent_salje_kljuc_u_zaglavlju_i_datume(self):
        odgovor = mock.Mock(status_code=200, headers={"Content-Type": "application/json"})
        odgovor.json.return_value = [{"InvoiceId": 1}]
        sesija = mock.Mock(request=mock.Mock(return_value=odgovor))
        klijent = sef.Klijent(session=sesija)
        self.assertEqual(klijent.ulazne_pregled(datetime.date(2026, 9, 1), datetime.date(2026, 9, 30)), [{"InvoiceId": 1}])
        metoda, adresa = sesija.request.call_args.args
        self.assertEqual((metoda, adresa), ("GET", "https://efakturatest.mfin.gov.rs/api/publicApi/purchase-invoice/overview"))
        self.assertEqual(sesija.request.call_args.kwargs["headers"]["ApiKey"], "test-kljuc")
        self.assertEqual(sesija.request.call_args.kwargs["params"], {"dateFrom": "2026-09-01", "dateTo": "2026-09-30"})
        # 429 (vise od 3 zahteva u sekundi): pauza pa ponovljen poziv
        preopterecen = mock.Mock(status_code=429, headers={}, text="Rate of max 3 requests per second exceeded")
        sesija.request.side_effect = [preopterecen, odgovor]
        with mock.patch.object(klijent, "_sacekaj") as ceka:
            self.assertEqual(klijent.ulazne_pregled(datetime.date(2026, 9, 1), datetime.date(2026, 9, 30)), [{"InvoiceId": 1}])
        ceka.assert_called_once_with(1.0)
        sesija.request.side_effect = None
        odgovor.status_code = 401
        with self.assertRaisesMessage(sef.SefGreska, "odbio API ključ"):
            klijent.ulazne_pregled(datetime.date(2026, 9, 1), datetime.date(2026, 9, 30))

    def test_periodi_po_mesec_dana(self):
        delovi = list(sef.periodi(datetime.date(2026, 1, 1), datetime.date(2026, 3, 5)))
        self.assertEqual(delovi[0], (datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)))
        self.assertEqual(delovi[-1][1], datetime.date(2026, 3, 5))


def knjizenje(broj, **kw):
    podaci = dict(company=1, year=2026, journal_type="UF", journal_number=1, line_number=1, organizational_unit=1,
                  account="435000", document_date=DANAS, document_reference=broj, debit=0, credit=220,
                  booking_date=DANAS, source_hash=broj, changed_at=timezone.now())
    podaci.update(kw)
    return LedgerEntry.objects.create(**podaci)


MEDIA_TEST = tempfile.mkdtemp(prefix="sef-test-")


@override_settings(MEDIA_ROOT=MEDIA_TEST, SEF_API_KEY="test-kljuc")
class EkraniTests(TestCase):
    KODOVI = ("finansije:sef_list", "finansije:sef_detail", "finansije:sef_dokument", "finansije:sef_sync",
              "finansije:sef_izvoz", "finansije:view_all")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        sef.sinhronizuj(datetime.date(2026, 8, 20), DANAS, klijent=LazniKlijent(), danas=DANAS, pdf=False)
        self.ulazna = SefFaktura.objects.get(smer="ulazna")
        uloga = Role.objects.create(name="Finansije SEF", slug="finansije-sef")
        for kod in self.KODOVI:
            uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        self.korisnik = get_user_model().objects.create_user("fin-sef", password="x")
        self.korisnik.roles.add(uloga)
        self.client.force_login(self.korisnik)

    def test_spisak_i_meka_veza_po_broju(self):
        knjizenje("MF3814/25")
        odgovor = self.client.get(reverse("finansije:sef_list"))
        self.assertContains(odgovor, "MF3814/25")
        self.assertContains(odgovor, "IF-120/2026")
        redovi = {f.broj: f.proknjizena for f in odgovor.context["page_obj"]}
        self.assertEqual(redovi, {"MF3814/25": True, "IF-120/2026": False})
        self.assertEqual(len(self.client.get(reverse("finansije:sef_list"), {"smer": "izlazna"}).context["page_obj"]), 1)
        detalj = self.client.get(reverse("finansije:sef_detail", args=[self.ulazna.pk]))
        self.assertEqual(len(detalj.context["knjizenja"]), 1)

    def test_izlazna_se_vezuje_bez_cetiri_cifre_ispred(self):
        izlazna = SefFaktura.objects.get(smer="izlazna")
        SefFaktura.objects.filter(pk=izlazna.pk).update(broj="2650707001-325", broj_kljuc="2650707001-325")
        izlazna.refresh_from_db()
        knjizenje("707001-325", journal_type="IF", account="20400", debit=1200, credit=0)
        self.assertEqual(sef.knjizenja(izlazna).count(), 1)
        self.assertEqual(sef.proknjizeni_brojevi([izlazna]), {"2650707001-325"})

    def test_broj_duzi_od_polja_knjizenja(self):
        dug = "2026-00012345-ABCDEFGH-9"
        SefFaktura.objects.filter(pk=self.ulazna.pk).update(broj=dug, broj_kljuc=dug)
        self.ulazna.refresh_from_db()
        knjizenje(dug[:20])
        self.assertEqual(sef.knjizenja(self.ulazna).count(), 1)

    def test_pdf_se_preuzima_jednom_i_cuva(self):
        pdf_u_pripremi = LazniKlijent()
        pdf_u_pripremi.pdf = lambda smer, sef_id: (None, "Extended PDF file creation has been initiated")
        with mock.patch.object(sef, "Klijent", return_value=pdf_u_pripremi):
            odgovor = self.client.get(reverse("finansije:sef_dokument", args=[self.ulazna.pk, "pdf"]), follow=True)
        self.assertContains(odgovor, "creation has been initiated")
        with mock.patch.object(sef, "Klijent", return_value=LazniKlijent()):
            odgovor = self.client.get(reverse("finansije:sef_dokument", args=[self.ulazna.pk, "pdf"]))
        self.assertEqual((odgovor.status_code, odgovor["Content-Type"]), (200, "application/pdf"))
        self.assertEqual(b"".join(odgovor.streaming_content), b"%PDF-1.7 test")
        self.assertEqual(odgovor["X-Frame-Options"], "SAMEORIGIN")  # prikaz u okviru detalja
        self.ulazna.refresh_from_db()
        self.assertTrue(self.ulazna.pdf and self.ulazna.pdf_preuzet)
        # drugi put se ne ide na SEF
        odgovor.close()
        with mock.patch.object(sef, "Klijent", side_effect=AssertionError("SEF se ne poziva")):
            drugi = self.client.get(reverse("finansije:sef_dokument", args=[self.ulazna.pk, "pdf"]))
        self.assertEqual(drugi.status_code, 200)
        drugi.close()  # Windows ne brise otvoren fajl
        # zapis postoji, a fajla nema na disku (preuzet sa drugog racunara): preuzima se ponovo
        self.ulazna.pdf.storage.delete(self.ulazna.pdf.name)
        with mock.patch.object(sef, "Klijent", return_value=LazniKlijent()):
            treci = self.client.get(reverse("finansije:sef_dokument", args=[self.ulazna.pk, "pdf"]))
        self.assertEqual(treci.status_code, 200)
        treci.close()
        self.assertTrue(self.ulazna.pdf.storage.exists(SefFaktura.objects.get(pk=self.ulazna.pk).pdf.name))

    def test_detalj_prikazuje_pdf_ili_ga_preuzima(self):
        detalj = self.client.get(reverse("finansije:sef_detail", args=[self.ulazna.pk]))
        self.assertContains(detalj, reverse("finansije:sef_pdf_preuzmi", args=[self.ulazna.pk]))  # automatsko preuzimanje
        adresa = reverse("finansije:sef_pdf_preuzmi", args=[self.ulazna.pk])
        pdf_u_pripremi = LazniKlijent()
        pdf_u_pripremi.pdf = lambda smer, sef_id: (None, "u pripremi")
        with mock.patch.object(sef, "Klijent", return_value=pdf_u_pripremi):
            self.assertEqual(self.client.post(adresa).json()["status"], "priprema")
        with mock.patch.object(sef, "Klijent", return_value=LazniKlijent()):
            podaci = self.client.post(adresa).json()
        self.assertEqual((podaci["status"], podaci["url"]), ("ok", reverse("finansije:sef_dokument", args=[self.ulazna.pk, "pdf"])))
        detalj = self.client.get(reverse("finansije:sef_detail", args=[self.ulazna.pk]))
        self.assertContains(detalj, '<iframe class="sef-pdf" src="%s"' % reverse("finansije:sef_dokument", args=[self.ulazna.pk, "pdf"]))
        pogresan = LazniKlijent()
        pogresan.pdf = lambda smer, sef_id: (b"<html>greska</html>", "")
        druga = SefFaktura.objects.get(smer="izlazna")
        with mock.patch.object(sef, "Klijent", return_value=pogresan):
            odgovor = self.client.post(reverse("finansije:sef_pdf_preuzmi", args=[druga.pk]))
        self.assertEqual((odgovor.status_code, odgovor.json()["status"]), (502, "greska"))

    def test_filteri(self):
        izlazna = SefFaktura.objects.get(smer="izlazna")
        izlazna.broj = "2650707001-325"
        izlazna.save()
        self.assertEqual(izlazna.broj_knjizenja, "707001-325")
        knjizenje("707001-325", journal_type="IF", account="20400", debit=1200, credit=0)
        spisak = reverse("finansije:sef_list")
        broj = lambda **g: self.client.get(spisak, g).context["zbir"]["broj"]
        self.assertEqual((broj(knjizenje="da"), broj(knjizenje="ne")), (1, 1))
        self.assertEqual(broj(knjizenje="da", smer="ulazna"), 0)
        # ulazna nema datum izdavanja: gleda se datum prometa (01.09.2026.)
        self.assertEqual(broj(od="2026-09-01", do="2026-09-01"), 1)
        self.assertEqual(broj(od="2026-09-10", do="2026-09-10"), 1)  # izlazna po datumu izdavanja
        self.assertEqual(broj(status="Sent"), 1)
        odgovor = self.client.get(spisak, {"smer": "ulazna", "knjizenje": "ne"})
        self.assertEqual([(v, n) for v, _, n, _ in [(s[0], s[1], s[2], s[3]) for s in odgovor.context["smerovi"]]],
                         [("", 1), ("ulazna", 1), ("izlazna", 0)])
        self.assertEqual(odgovor.context["aktivnih_filtera"], 1)
        self.assertContains(odgovor, "Poništi (1)")

    def test_precice_i_uklanjanje_filtera_cuvaju_ostale_uslove(self):
        uslovi = {"smer": "izlazna", "status": "Sent", "knjizenje": "ne", "q": "Kupac DOO",
                  "od": "2026-09-01", "do": "2026-09-30", "page": "3"}
        with mock.patch("finansije.sef_views.timezone.localdate", return_value=DANAS):
            odgovor = self.client.get(reverse("finansije:sef_list"), uslovi)
        ctx = odgovor.context
        self.assertEqual(len(ctx["aktivne_oznake"]), 5)
        for (oznaka, url), izbacen in zip(ctx["aktivne_oznake"], ("q", "status", "knjizenje", "od", "do")):
            self.assertEqual(parse_qs(urlsplit(url).query),
                             {k: [v] for k, v in uslovi.items() if k not in (izbacen, "page")})
        svi_periodi = next(url for naziv, url, _ in ctx["periodi"] if naziv == "Svi periodi")
        self.assertEqual(parse_qs(urlsplit(svi_periodi).query),
                         {k: [v] for k, v in uslovi.items() if k not in ("od", "do", "page")})
        self.assertEqual(parse_qs(urlsplit(ctx["ponisti"]).query), {"smer": ["izlazna"]})
        self.assertEqual((ctx["sync_od"], ctx["sync_do"]), ("2026-09-23", "2026-09-30"))

    def test_datatable_pretraga_stranicenje_i_sortiranje_celog_spiska(self):
        from decimal import Decimal
        for i in range(105):
            SefFaktura.objects.create(smer="ulazna", sef_id=800000+i, broj=f"TEST-{i:03d}",
                                     iznos=Decimal(i), datum_izdavanja=DANAS, sinhronizovano=timezone.now())
        url = reverse("finansije:sef_list")
        data = self.client.get(url, {"draw": "3", "smer": "ulazna", "search[value]": "TEST-",
                                     "start": "100", "length": "25", "order[0][column]": "6",
                                     "order[0][dir]": "asc"}).json()
        self.assertEqual((data["draw"], data["recordsTotal"], data["recordsFiltered"], len(data["data"])), (3, 106, 105, 5))
        self.assertIn("TEST-100", data["data"][0][0])
        self.assertIn("TEST-104", data["data"][-1][0])
        self.assertIn("Ulazna", data["data"][0][1])
        by_number = self.client.get(url, {"draw": 1, "length": 1, "order[0][column]": 0, "order[0][dir]": "desc"}).json()
        self.assertIn("TEST-104", by_number["data"][0][0])
        self.assertEqual(len(data["data"][0]), 10)
        with mock.patch("finansije.sef_views.can_view_all", return_value=False):
            self.assertEqual(self.client.get(url, {"draw": 1}).status_code, 403)

    def test_partner_link_samo_jednoznacna_veza_i_dozvola(self):
        from ugovori.models import Partner
        from django.utils.html import escape
        from django.utils.text import Truncator
        self.korisnik.roles.first().permissions.add(PermissionCode.objects.get_or_create(code="ugovori:partner_detail")[0])
        partner = Partner.objects.create(name="Dobavljač", pib="123456789", maticni_broj="00123456")
        name = '<script>alert("x")</script> ' + "Dugačak naziv partnera " * 6
        SefFaktura.objects.filter(pk=self.ulazna.pk).update(partner_pib=partner.pib, partner_mb=partner.maticni_broj, partner_naziv=name)
        url = reverse("finansije:sef_list")
        cell = lambda: self.client.get(url, {"draw": 1, "smer": "ulazna"}).json()["data"][0][3]
        html = cell()
        self.assertIn(reverse("ugovori:partner_detail", args=[partner.pk]), html)
        self.assertIn(str(escape(Truncator(name).chars(80))), html)
        self.assertNotIn("<script>", html)
        # Dupliran PIB može da se razreši matičnim brojem, a duplirani identitet ne sme da se pogađa.
        duplicate = Partner.objects.create(name="Drugi", pib=partner.pib, maticni_broj="99999999")
        self.assertIn('<a ', cell())
        Partner.objects.filter(pk=duplicate.pk).update(maticni_broj=partner.maticni_broj)
        self.assertNotIn('<a ', cell())
        duplicate.delete()
        self.korisnik.roles.first().permissions.remove(PermissionCode.objects.get(code="ugovori:partner_detail"))
        self.assertNotIn('<a ', cell())

    def test_rucno_preuzimanje_odmah_sa_napretkom(self):
        from finansije import sef_views

        pokrenuto = []
        with mock.patch.object(sef_views, "pokreni", side_effect=lambda fn: pokrenuto.append(fn)):
            podaci = self.client.post(reverse("finansije:sef_sync"), {"od": "2026-08-20", "do": "2026-09-30"}).json()
        run = SefSinhronizacija.objects.get(pk=podaci["id"])
        self.assertEqual((podaci["status"], run.status, run.korisnik), ("running", "running", self.korisnik))
        self.assertEqual(podaci["stanje_url"], reverse("finansije:sef_sync_stanje", args=[run.pk]))
        # dok radi, drugo pokretanje prikazuje isto preuzimanje
        with mock.patch.object(sef_views, "pokreni") as drugo:
            ponovo = self.client.post(reverse("finansije:sef_sync"), {"od": "2026-09-01", "do": "2026-09-30"}).json()
        drugo.assert_not_called()
        self.assertEqual((ponovo["id"], ponovo["vec_u_toku"]), (run.pk, True))
        self.assertContains(self.client.get(reverse("finansije:sef_list")), "Preuzimanje sa SEF-a je u toku")
        # nit: fakture, statusi i PDF-ovi, uz procenu i napredak po fazama
        with mock.patch.object(sef, "Klijent", return_value=LazniKlijent()):
            pokrenuto[0]()
        stanje = self.client.get(podaci["stanje_url"]).json()
        self.assertEqual(stanje["status"], "success")
        self.assertIn("PDF preuzeto 2 od 2", stanje["poruka"])
        self.assertEqual(stanje["procena"], {"ulaznih": 1, "izlaznih": 1, "ubl": 0, "dana_promena": 30, "bez_pdf": 2})

    def test_procena_i_napredak_tokom_preuzimanja(self):
        SefFaktura.objects.all().delete()
        snimci = []
        stari = sef.Napredak.sacuvaj

        def sacuvaj(napredak, odmah=False):
            stari(napredak, odmah=True)
            snimci.append(dict(napredak.run.counts.get("napredak", {})))

        with mock.patch.object(sef.Napredak, "sacuvaj", sacuvaj):
            run = sef.sinhronizuj(datetime.date(2026, 8, 20), DANAS, klijent=LazniKlijent(), danas=DANAS)
        self.assertEqual(run.counts["procena"], {"ulaznih": 1, "izlaznih": 1, "ubl": 1, "dana_promena": 30, "bez_pdf": 2})
        self.assertEqual([s["redni"] for s in snimci if s.get("obradjeno") == 0],
                         [1, 2, 3, 4, 5])  # svaka faza pocinje od nule
        self.assertTrue(all(s["preostalo_s"] is not None for s in snimci))
        self.assertEqual(snimci[-1]["faza"], "PDF-ovi")

    def test_zaustavljanje_dnevnik_i_poslednje_stanje(self):
        from finansije import sef_views

        # bez preuzimanja u toku: poslednje zavrseno (iz setUp), sa nazivom statusa za modal
        self.assertEqual(self.client.get(reverse("finansije:sef_sync_poslednje")).json()["status_naziv"], "Uspešno")
        pokrenuto = []
        with mock.patch.object(sef_views, "pokreni", side_effect=lambda fn: pokrenuto.append(fn)):
            podaci = self.client.post(reverse("finansije:sef_sync"), {"od": "2026-08-20", "do": "2026-09-30"}).json()
        poslednje = self.client.get(reverse("finansije:sef_sync_poslednje")).json()
        self.assertEqual((poslednje["id"], poslednje["status"], poslednje["pokrenuo"]), (podaci["id"], "running", "fin-sef"))
        # zaustavljanje pre nego sto nit krene: staje na prvom koraku, sto je preuzeto ostaje
        stanje = self.client.post(podaci["zaustavi_url"]).json()
        self.assertTrue(stanje["zaustavljanje"])
        with mock.patch.object(sef, "Klijent", return_value=LazniKlijent()):
            pokrenuto[0]()
        stanje = self.client.get(podaci["stanje_url"]).json()
        self.assertEqual((stanje["status"], stanje["status_naziv"]), ("stopped", "Zaustavljeno"))
        self.assertIn("Zaustavljeno na zahtev korisnika", stanje["greska"])
        self.assertTrue(stanje["dnevnik"])  # prvi korak je upisan
        # celo preuzimanje: dnevnik prati korake, PDF-ove i kraj
        with mock.patch.object(sef_views, "pokreni", side_effect=lambda fn: fn()), \
                mock.patch.object(sef, "Klijent", return_value=LazniKlijent()):
            podaci = self.client.post(reverse("finansije:sef_sync"), {"od": "2026-08-20", "do": "2026-09-30"}).json()
        stanje = self.client.get(podaci["stanje_url"]).json()
        tekstovi = [r[1] for r in stanje["dnevnik"]]
        self.assertEqual(stanje["status"], "success")
        self.assertIn("Korak 5: PDF-ovi (2)", tekstovi)
        self.assertTrue(any(t.startswith("PDF MF3814/25") for t in tekstovi))
        self.assertEqual(tekstovi[-1], "Završeno.")
        # zavrseno preuzimanje se vise ne moze zaustaviti
        self.assertFalse(self.client.post(stanje["zaustavi_url"]).json()["zaustavljanje"])

    def test_rucno_preuzimanje_greske_i_prekid(self):
        from finansije import sef_views

        self.assertEqual(self.client.post(reverse("finansije:sef_sync"), {"od": "2026-09-30", "do": "2026-09-01"}).json()["greska"],
                         "Datum od je posle datuma do.")
        with override_settings(SEF_API_KEY=""):
            self.assertIn("nije podešen", self.client.post(reverse("finansije:sef_sync"), {}).json()["greska"])
        # greska SEF-a u niti se vidi u stanju
        pokrenuto = []
        with mock.patch.object(sef_views, "pokreni", side_effect=lambda fn: pokrenuto.append(fn)):
            podaci = self.client.post(reverse("finansije:sef_sync"), {"od": "2026-09-01", "do": "2026-09-30"}).json()
        pao = LazniKlijent()
        pao.ulazne_pregled = mock.Mock(side_effect=sef.SefGreska("SEF je vratio grešku 500"))
        with mock.patch.object(sef, "Klijent", return_value=pao), self.assertRaises(sef.SefGreska):
            pokrenuto[0]()
        stanje = self.client.get(podaci["stanje_url"]).json()
        self.assertEqual((stanje["status"], stanje["greska"]), ("error", "SEF je vratio grešku 500"))
        # „u toku” koje se ne javlja 2 minuta (restart servera) zatvara se kao prekinuto
        visi = sef.zapocni(datetime.date(2026, 9, 1), DANAS, danas=DANAS)
        radi = self.client.get(reverse("finansije:sef_sync_stanje", args=[visi.pk])).json()
        self.assertEqual((radi["status"], radi["tisina_s"] < 5), ("running", True))
        visi.counts["napredak"]["azurirano"] = (timezone.now() - datetime.timedelta(minutes=3)).isoformat()
        visi.save(update_fields=["counts"])
        stanje = self.client.get(reverse("finansije:sef_sync_stanje", args=[visi.pk])).json()
        self.assertEqual(stanje["status"], "error")
        self.assertIn("Prekinuto", stanje["greska"])

    @override_settings(SEF_API_KEY="test-kljuc")
    def test_rucno_preuzimanje_sa_strane_sinhronizacije(self):
        self.korisnik.roles.first().permissions.add(PermissionCode.objects.get_or_create(code="finansije:sync_status")[0])
        strana = self.client.get(reverse("finansije:sync_status"))
        self.assertContains(strana, "SEF — ulazne i izlazne fakture")
        self.assertContains(strana, 'id="SefPreuzimanjeModal"')
        self.assertContains(strana, reverse("finansije:sef_sync_poslednje"))
        self.assertContains(strana, reverse("finansije:sef_sync"))

    def test_sinhronizacija_odmah_preuzima_i_pdf(self):
        run = sef.sinhronizuj(datetime.date(2026, 8, 20), DANAS, klijent=LazniKlijent(), danas=DANAS)
        self.assertEqual((run.counts["pdf_bez_pdf"], run.counts["pdf_preuzeto"]), (2, 2))
        self.assertEqual(SefFaktura.objects.filter(pdf="").count(), 0)
        self.assertIn("PDF preuzeto 2 od 2", sef.poruka(run))
        # ponovo: PDF-ovi postoje, SEF se za njih ne pita
        klijent = LazniKlijent()
        klijent.pdf = mock.Mock(side_effect=AssertionError("PDF se ne trazi ponovo"))
        self.assertEqual(sef.sinhronizuj(datetime.date(2026, 8, 20), DANAS, klijent=klijent, danas=DANAS).counts["pdf_bez_pdf"], 0)

    def test_preuzimanje_svih_pdf_u_krugovima(self):
        klijent, pozivi = LazniKlijent(), []

        def pdf(smer, sef_id):  # SEF prvi put samo pokrene izradu
            pozivi.append(sef_id)
            return (b"%PDF-1.7 " + str(sef_id).encode(), "") if pozivi.count(sef_id) > 1 else (None, "u pripremi")

        klijent.pdf = pdf
        spavanja = []
        brojaci = sef.preuzmi_pdfove(list(SefFaktura.objects.all()), klijent=klijent, spavaj=spavanja.append)
        self.assertEqual(brojaci, {"bez_pdf": 2, "preuzeto": 2, "u_pripremi": 0, "gresaka": 0})
        self.assertEqual((len(pozivi), spavanja), (4, [sef.PDF_CEKANJE]))
        # sa napretkom: ista pauza, ali u delovima od 5 s uz javljanje
        SefFaktura.objects.update(pdf="")
        pozivi.clear()
        run = sef.zapocni(datetime.date(2026, 8, 20), DANAS, danas=DANAS)
        napredak = sef.Napredak(run, {}, klijent)
        spavanja = []
        sef.preuzmi_pdfove(list(SefFaktura.objects.all()), klijent=klijent, spavaj=spavanja.append, napredak=napredak)
        self.assertEqual(spavanja, [5, 5, 5])
        run.refresh_from_db()
        self.assertIn("azurirano", run.counts["napredak"])
        self.assertEqual(SefFaktura.objects.filter(pdf="").count(), 0)
        # ponovo: nista ne nedostaje, SEF se ne poziva
        self.assertEqual(sef.preuzmi_pdfove(list(SefFaktura.objects.all()), klijent=klijent)["bez_pdf"], 0)
        self.assertEqual(len(pozivi), 4)

    def test_izvoz_pdf_za_mesec_i_godinu(self):
        import csv
        import io
        import zipfile

        with mock.patch.object(sef, "Klijent", return_value=LazniKlijent()):
            sef.preuzmi_pdf(self.ulazna)
        odgovor = self.client.get(reverse("finansije:sef_izvoz"), {"godina": "2026", "mesec": "9"})
        self.assertEqual((odgovor.status_code, odgovor["Content-Type"]), (200, "application/zip"))
        self.assertIn("SEF_sve_2026-09.zip", odgovor["Content-Disposition"])
        arhiva = zipfile.ZipFile(io.BytesIO(b"".join(odgovor.streaming_content)))
        imena = arhiva.namelist()
        self.assertIn("Ulazne/2026-09/2026-09-01_MF3814_25_Dobavljač_DOO.pdf", imena)
        self.assertEqual(arhiva.read("Ulazne/2026-09/2026-09-01_MF3814_25_Dobavljač_DOO.pdf"), b"%PDF-1.7 test")
        redovi = list(csv.reader(io.StringIO(arhiva.read("spisak.csv").decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(len(redovi), 3)  # zaglavlje + ulazna + izlazna (bez PDF-a)
        self.assertEqual({r[1]: r[-1] for r in redovi[1:]}["IF-120/2026"], "nije preuzet")
        self.assertEqual(odgovor["X-SEF-PDF"], "1")
        # cela godina, samo izlazne
        odgovor = self.client.get(reverse("finansije:sef_izvoz"), {"godina": "2026", "smer": "izlazna"})
        arhiva = zipfile.ZipFile(io.BytesIO(b"".join(odgovor.streaming_content)))
        self.assertEqual(arhiva.namelist(), ["spisak.csv"])
        self.assertIn("SEF_izlazna_2026.zip", odgovor["Content-Disposition"])
        # prazan period i neispravna godina
        self.assertRedirects(self.client.get(reverse("finansije:sef_izvoz"), {"godina": "2025"}),
                             reverse("finansije:sef_list"), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse("finansije:sef_izvoz"), {"godina": "x"}),
                             reverse("finansije:sef_list"), fetch_redirect_response=False)

    def test_bez_obuhvata_cele_firme_nema_pristupa(self):
        with mock.patch("finansije.sef_views.can_view_all", return_value=False):
            self.assertEqual(self.client.get(reverse("finansije:sef_list")).status_code, 403)
