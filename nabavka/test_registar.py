"""Nabavka na registru (plan prelaska na registar, korak 5): predmeti i fakture po obuhvatu dodela."""
import datetime

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from core.models import OrganizationalUnit
from nabavka.access import fakture, predmeti
from nabavka.models import ProcurementCase, ProcurementInvoice
from organizacija.models import DodelaUloge
from organizacija.services.importer import run_import
from organizacija.test_prava import centar, uloga_sa_dozvolom
from organizacija.tests import ImportTestCase

NA_REGISTRU = override_settings(PRAVA_PO_REGISTRU={"nabavka": True})


@NA_REGISTRU
class NabavkaNaRegistruTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        nadzor = OrganizationalUnit.objects.create(code="430111", name="Strucni nadzor", center="43")
        materijali = OrganizationalUnit.objects.create(code="410001", name="Amortizacija", center="41")
        self.predmet_43 = ProcurementCase.objects.create(case_number="ZN-43/2026-1", title="43", job_code=nadzor)
        self.predmet_41 = ProcurementCase.objects.create(case_number="ZN-41/2026-1", title="41", job_code=materijali)
        self.bez_sifre = ProcurementCase.objects.create(case_number="ZN-00/2026-1", title="bez")
        self.faktura_43 = ProcurementInvoice.objects.create(source=ProcurementInvoice.SOURCE_EUF, euf_key="e43",
                                                           invoice_number="F43", amount="10.00", job_code=nadzor)
        self.uloga = uloga_sa_dozvolom("nabavka-centra", "nabavka:case_detail")  # samo detalj, bez spiska
        self.korisnik = get_user_model().objects.create_user("nab-41", password="x")
        self.korisnik.roles.add(self.uloga)

    def dodeli(self, **obuhvat):
        DodelaUloge.objects.create(korisnik=self.korisnik, uloga=self.uloga, vazi_od=datetime.date(2026, 1, 1),
                                   status=DodelaUloge.STATUS_AKTIVNA, **obuhvat)

    def svez(self):
        return get_user_model().objects.get(pk=self.korisnik.pk)

    def test_predmeti_i_fakture_po_obuhvatu(self):
        self.assertFalse(predmeti(ProcurementCase.objects.all(), self.svez()).exists())  # bez dodele — nista
        self.dodeli(cvor_id=centar("41"))
        self.assertEqual(set(predmeti(ProcurementCase.objects.all(), self.svez())), {self.predmet_41})
        self.assertFalse(fakture(ProcurementInvoice.objects.all(), self.svez()).exists())

    def test_sopstveni_zahtev_se_uvek_vidi(self):
        sopstveni = ProcurementCase.objects.create(case_number="ZN-43/2026-2", title="moj", created_by=self.korisnik)
        self.assertEqual(set(predmeti(ProcurementCase.objects.all(), self.svez())), {sopstveni})

    def test_cela_firma_vidi_i_zapise_bez_sifre(self):
        self.dodeli(cela_firma=True)
        self.assertEqual(predmeti(ProcurementCase.objects.all(), self.svez()).count(), 3)

    def test_detalj_tudjeg_predmeta_nije_dostupan(self):
        self.dodeli(cvor_id=centar("41"))
        self.client.force_login(self.korisnik)
        self.assertEqual(self.client.get(reverse("nabavka:case_detail", args=[self.predmet_41.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("nabavka:case_detail", args=[self.predmet_43.pk])).status_code, 404)

    def test_broj_predmeta_se_ne_menja(self):
        self.dodeli(cvor_id=centar("41"))
        self.predmet_43.refresh_from_db()
        self.assertEqual(self.predmet_43.case_number, "ZN-43/2026-1")

    def test_svi_ekrani_rade_na_registru(self):
        uloga = uloga_sa_dozvolom("nab-sve", "nabavka:dashboard", "nabavka:case_list", "nabavka:case_data",
                                  "nabavka:euf_invoice_list", "nabavka:euf_invoice_data", "nabavka:euf_invoice_detail",
                                  "nabavka:alerts", "nabavka:reports", "nabavka:case_print", "nabavka:case_update")
        self.korisnik.roles.add(uloga)
        self.dodeli(cvor_id=centar("43"))
        self.client.force_login(self.korisnik)
        for ime, args in (("nabavka:dashboard", []), ("nabavka:case_list", []), ("nabavka:case_data", []),
                          ("nabavka:euf_invoice_list", []), ("nabavka:euf_invoice_data", []), ("nabavka:alerts", []),
                          ("nabavka:reports", []), ("nabavka:euf_invoice_detail", [self.faktura_43.pk]),
                          ("nabavka:case_print", [self.predmet_43.pk]), ("nabavka:case_update", [self.predmet_43.pk])):
            with self.subTest(ime=ime):
                self.assertEqual(self.client.get(reverse(ime, args=args)).status_code, 200)
        self.assertEqual(self.client.get(reverse("nabavka:case_print", args=[self.predmet_41.pk])).status_code, 404)
        podaci = self.client.get(reverse("nabavka:case_data"), {"draw": 1, "start": 0, "length": 10}).json()
        self.assertEqual((podaci["recordsTotal"], podaci["recordsFiltered"]), (1, 1))

    def test_fiskalni_racuni_po_obuhvatu_i_izbor_sifara(self):
        from datetime import datetime, timezone as dt_timezone

        from nabavka.access import fiskalni_racuni, sifre_za_izbor
        from nabavka.models import FiskalniRacun

        vreme = datetime(2026, 9, 18, tzinfo=dt_timezone.utc)
        r41 = FiskalniRacun.objects.create(link="x", broj_racuna="A-A-1", iznos="10", pfr_vreme=vreme,
                                           job_code=self.predmet_41.job_code)
        FiskalniRacun.objects.create(link="x", broj_racuna="A-A-2", iznos="10", pfr_vreme=vreme, job_code=self.predmet_43.job_code)
        self.assertIsNotNone(r41.org_node_id)  # veza sa registrom pri cuvanju
        self.dodeli(cvor_id=centar("41"))
        self.assertEqual(list(fiskalni_racuni(FiskalniRacun.objects.all(), self.svez())), [r41])
        self.assertEqual(set(sifre_za_izbor(OrganizationalUnit.objects.all(), self.svez())), {self.predmet_41.job_code})
