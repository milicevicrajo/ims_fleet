"""Detalj EUF fakture: meka veza sa ulaznom SEF fakturom (isti broj i PIB), PDF sa SEF-a."""
import datetime
import shutil
import tempfile
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import PermissionCode, Role
from finansije.sef_models import SefFaktura
from finansije.services import sef as sef_servis
from nabavka.models import ProcurementInvoice
from finansije.test_sef import UBL_PRILOZI
from nabavka.services.sef_veza import sef_faktura


class SefVezaTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media = override_settings(MEDIA_ROOT=tempfile.mkdtemp())
        cls._media.enable()

    @classmethod
    def tearDownClass(cls):
        from django.conf import settings

        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        cls._media.disable()
        super().tearDownClass()

    def setUp(self):
        self.faktura = ProcurementInvoice.objects.create(source=ProcurementInvoice.SOURCE_EUF, euf_key="e1",
                                                         invoice_number="K019/2026-577187", partner_pib="100618836",
                                                         supplier_name="Dobavljač doo", amount=Decimal("1200.00"),
                                                         invoice_date=datetime.date(2026, 9, 25))
        self.sef = SefFaktura.objects.create(smer="ulazna", sef_id=501, broj="K019/2026-577187 ", partner_pib="100618836",
                                             partner_naziv="DOBAVLJAČ DOO", iznos=Decimal("1200.00"), status="Approved",
                                             vrsta="Invoice", datum_prometa=datetime.date(2026, 9, 24),
                                             sinhronizovano=timezone.now())
        uloga = Role.objects.create(name="nabavka-sef", slug="nabavka-sef")
        for kod in ("nabavka:euf_invoice_detail", "nabavka:euf_invoice_sef_pdf"):
            uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        korisnik = get_user_model().objects.create_user("nabavka-sef", password="x")
        korisnik.roles.add(uloga)
        self.client.force_login(korisnik)
        # detalj cita priloge sa SEF-a kad ih jos nema — u testovima lazni UBL
        ubl = mock.patch.object(sef_servis.Klijent, "ubl", return_value=UBL_PRILOZI)
        ubl.start()
        self.addCleanup(ubl.stop)

    def detalj(self):
        return self.client.get(reverse("nabavka:euf_invoice_detail", args=[self.faktura.pk]))

    def test_veza_po_broju_i_pibu(self):
        self.assertEqual(sef_faktura(self.faktura), (self.sef, 1))
        odgovor = self.detalj()
        self.assertContains(odgovor, "Povezana po broju i PIB-u")
        self.assertContains(odgovor, "Prihvaćena")  # status sa SEF-a
        self.assertContains(odgovor, reverse("nabavka:euf_invoice_sef_pdf", args=[self.faktura.pk]))
        self.assertNotContains(odgovor, "se razlikuje od iznosa")

    def test_drugi_pib_nije_veza(self):
        SefFaktura.objects.filter(pk=self.sef.pk).update(partner_pib="999999999")
        self.assertEqual(sef_faktura(self.faktura), (None, 0))
        self.assertContains(self.detalj(), "Na SEF-u nema ulazne fakture")
        self.assertEqual(self.client.get(reverse("nabavka:euf_invoice_sef_pdf", args=[self.faktura.pk])).status_code, 404)

    def test_izlazna_sa_istim_brojem_nije_veza(self):
        SefFaktura.objects.filter(pk=self.sef.pk).update(smer="izlazna")
        self.assertEqual(sef_faktura(self.faktura), (None, 0))

    def test_razlika_iznosa(self):
        SefFaktura.objects.filter(pk=self.sef.pk).update(iznos=Decimal("1250.00"))
        self.assertContains(self.detalj(), "se razlikuje od iznosa u EUF za 50.00")

    def test_prilozi_sef_fakture(self):
        odgovor = self.detalj()
        self.assertContains(odgovor, "Pridruženi dokumenti (2)")
        adresa = reverse("nabavka:euf_invoice_sef_prilog", args=[self.faktura.pk, 1])
        self.assertContains(odgovor, adresa)
        prilog = self.client.get(adresa)
        self.assertEqual((prilog.status_code, b"".join(prilog.streaming_content)), (200, b"%PDF-1.7 prilog"))
        self.assertEqual(self.client.get(reverse("nabavka:euf_invoice_sef_prilog", args=[self.faktura.pk, 9])).status_code, 404)
        # bez dozvole za PDF sa SEF-a nema ni priloga
        PermissionCode.objects.get(code="nabavka:euf_invoice_sef_pdf").roles.clear()
        self.assertEqual(self.client.get(adresa).status_code, 403)

    def test_pdf_u_okviru_strane(self):
        with mock.patch.object(sef_servis.Klijent, "pdf", return_value=(b"%PDF-1.4 SEF", "")):
            odgovor = self.client.get(reverse("nabavka:euf_invoice_sef_pdf", args=[self.faktura.pk]))
        self.assertEqual(odgovor.status_code, 200)
        self.assertEqual(b"".join(odgovor.streaming_content), b"%PDF-1.4 SEF")
        self.assertEqual(odgovor["X-Frame-Options"], "SAMEORIGIN")
        with mock.patch.object(sef_servis.Klijent, "pdf", return_value=(None, "SEF priprema PDF.")):
            SefFaktura.objects.filter(pk=self.sef.pk).update(pdf="")
            odgovor = self.client.get(reverse("nabavka:euf_invoice_sef_pdf", args=[self.faktura.pk]))
        self.assertEqual(odgovor.status_code, 202)
        self.assertContains(odgovor, "SEF priprema PDF.", status_code=202)
