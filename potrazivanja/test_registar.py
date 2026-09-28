"""Potrazivanja na registru (plan prelaska na registar): obuhvat iz dodela, centar iz registra."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from organizacija.models import DodelaUloge
from organizacija.services import prava
from organizacija.services.importer import run_import
from organizacija.services.report import job_code_to_node
from organizacija.test_prava import centar, uloga_sa_dozvolom
from organizacija.tests import ImportTestCase
from potrazivanja.access import can_view_all, can_view_job, scoped
from potrazivanja.models import BalanceSnapshot, CollectionState, CollectionSyncRun, FinancePartnerIdentity, ReceivablePosition

NA_REGISTRU = override_settings(PRAVA_PO_REGISTRU={"potrazivanja": True})


@NA_REGISTRU
class PotrazivanjaNaRegistruTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        run = CollectionSyncRun.objects.create(dataset="full", trigger="import", status="success")
        self.snapshot = BalanceSnapshot.objects.create(run=run, company=1, as_of_date=datetime.date(2026, 9, 28),
                                                       source_observed_at=timezone.now(), published_at=timezone.now(),
                                                       status="published")
        CollectionState.objects.create(company=1, current_snapshot=self.snapshot)
        partner = FinancePartnerIdentity.objects.create(company=1, partner_group=1, partner_code=42, source_name="Kupac")
        cvorovi = job_code_to_node(1)
        for broj, sifra in enumerate(("430111", "410001", "430001"), start=1):
            ReceivablePosition.objects.create(snapshot=self.snapshot, identity=partner, reference=str(broj), job_code=sifra,
                                              center_code="", org_node_id=cvorovi.get(sifra), account_family="204",
                                              debit=Decimal("100"), credit=Decimal("0"), balance=Decimal("100"))
        self.uloga = uloga_sa_dozvolom("potrazivanja-centra", "potrazivanja:dashboard")
        self.korisnik = get_user_model().objects.create_user("pot-43", password="x", allowed_center_codes="41")
        self.korisnik.roles.add(self.uloga)

    def svez(self):
        return get_user_model().objects.get(pk=self.korisnik.pk)

    def dodeli(self, **obuhvat):
        DodelaUloge.objects.create(korisnik=self.korisnik, uloga=self.uloga, vazi_od=datetime.date(2026, 1, 1),
                                   status=DodelaUloge.STATUS_AKTIVNA, **obuhvat)

    def vidi(self):
        return set(scoped(ReceivablePosition.objects.all(), self.svez()).values_list("job_code", flat=True))

    def test_obuhvat_iz_dodele(self):
        self.assertEqual(self.vidi(), set())  # stari centar 41 vise ne odlucuje
        self.dodeli(cvor_id=centar("43"))
        self.assertEqual(self.vidi(), {"430111", "430001"})  # 430001 je po registru u 43
        self.assertTrue(can_view_job(self.svez(), "430001"))
        self.assertFalse(can_view_job(self.svez(), "410001"))
        self.assertFalse(can_view_all(self.svez()))

    def test_pravna_sluzba_i_cela_firma_vide_sve(self):
        self.assertIn("pravna", prava.ULOGE_CELE_FIRME)
        self.dodeli(cela_firma=True)
        self.assertEqual(len(self.vidi()), 3)
        self.assertTrue(can_view_all(self.svez()))

    def test_ekran_postuje_obuhvat(self):
        self.dodeli(cvor_id=centar("41"))
        self.client.force_login(self.korisnik)
        odgovor = self.client.get(reverse("potrazivanja:dashboard"))
        self.assertEqual(odgovor.status_code, 200)
        ukupno = sum(red["amounts"][-1] for red in odgovor.context["legacy_partner_rows"])
        self.assertEqual(ukupno, Decimal("100"))

    def test_centar_sinhronizacije_iz_registra(self):
        from organizacija.services.putanja import centri_sifara

        mapa = centri_sifara()
        self.assertEqual((mapa["430001"], mapa["110002"], mapa["209001"]), ("43", "11", "2"))
        self.assertEqual(mapa.get("111111", ""), "")  # tehnicka sifra nije u registru — bez centra
