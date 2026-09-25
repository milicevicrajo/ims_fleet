"""Ispravke oko sifara posla u Floti (25.09.2026.).

- gorivo dobija sifru dodele vazece na dan tocenja (ranije: najstariju dodelu);
- ispravka starih zapisa menja samo pogresne, ispravne i one bez dodele ne dira;
- kolona „Centar" u spisku vozila prikazuje centar, a ne sifru OJ;
- izmena putnog naloga: obuhvat po centrima u upitu i zabrana prebacivanja na tudji centar;
- ekrani dodela sifre posla i izvestaj o lizingu se otvaraju.
"""
import csv
import datetime
import io
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import OrganizationalUnit
from fleet.models import FuelConsumption, JobCode, PutniNalog, TrafficCard
from fleet.sync.selenium import get_vehicle_job_code
from fleet.test_vehicle_onboarding import vehicle
from fleet.views.putni_nalozi import PutniNalogUpdateView


def u_osam(dan):
    return timezone.make_aware(datetime.datetime.combine(dan, datetime.time(8, 0)))


class SifraGorivaNaDanTests(TestCase):
    def setUp(self):
        self.car = vehicle()
        self.stara = OrganizationalUnit.objects.create(code="430111", name="Nadzor", center="43")
        self.nova = OrganizationalUnit.objects.create(code="410001", name="Materijali", center="41")
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.stara, assigned_date=datetime.date(2025, 1, 1))
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.nova, assigned_date=datetime.date(2026, 3, 1))

    def gorivo(self, dan, sifra):
        return FuelConsumption.objects.create(
            vehicle=self.car, date=u_osam(dan), amount=Decimal("40"), fuel_type="dizel", supplier="NIS",
            cost_bruto=Decimal("100"), cost_neto=Decimal("80"), job_code=sifra, mileage=1000)

    def test_sifra_dodele_vazece_na_dan_tocenja(self):
        self.assertEqual(get_vehicle_job_code(self.car, u_osam(datetime.date(2026, 2, 28))), "430111")
        self.assertEqual(get_vehicle_job_code(self.car, u_osam(datetime.date(2026, 3, 1))), "410001")
        self.assertEqual(get_vehicle_job_code(self.car, datetime.date(2027, 1, 1)), "410001")
        # Pre prve dodele sifra se ne izmislja.
        self.assertIsNone(get_vehicle_job_code(self.car, datetime.date(2024, 12, 31)))

    def test_ispravka_menja_samo_pogresne_zapise(self):
        pogresan = self.gorivo(datetime.date(2026, 5, 10), "430111")   # tada je vazila 410001
        ispravan = self.gorivo(datetime.date(2025, 6, 1), "430111")
        bez_dodele = self.gorivo(datetime.date(2024, 6, 1), "999999")  # pre prve dodele — ne dira se

        izlaz = StringIO()
        call_command("ispravi_sifre_goriva", "--proba", stdout=izlaz)
        self.assertIn("za ispravku 1", izlaz.getvalue())
        pogresan.refresh_from_db()
        self.assertEqual(pogresan.job_code, "430111")

        call_command("ispravi_sifre_goriva", stdout=StringIO())
        for zapis in (pogresan, ispravan, bez_dodele):
            zapis.refresh_from_db()
        self.assertEqual((pogresan.job_code, ispravan.job_code, bez_dodele.job_code), ("410001", "430111", "999999"))


class KolonaCentarUSpiskuVozilaTests(TestCase):
    def setUp(self):
        self.car = vehicle()
        TrafficCard.objects.create(vehicle=self.car, registration_number="BG123-AA", issue_date=datetime.date(2020, 1, 1),
                                   traffic_card_number="1", serial_number="1", owner="IMS")
        jedinica = OrganizationalUnit.objects.create(code="430111", name="Nadzor", center="43")
        JobCode.objects.create(vehicle=self.car, organizational_unit=jedinica, assigned_date=datetime.date(2025, 1, 1))
        self.admin = get_user_model().objects.create_superuser("vozila-admin", "v@example.com", "x")
        self.client.force_login(self.admin)

    def test_datatable_prikazuje_centar_i_oj(self):
        odgovor = self.client.get(reverse("vehicle_data"), {"draw": "1", "start": "0", "length": "10"})
        self.assertEqual(odgovor.status_code, 200)
        self.assertEqual([red["center"] for red in odgovor.json()["data"]], ["43 · 430111"])

    def test_csv_ima_centar_i_oj_odvojeno(self):
        from fleet.views.vehicles import vehicle_export_csv

        zahtev = RequestFactory().get("/")
        zahtev.user = self.admin
        redovi = list(csv.reader(io.StringIO(vehicle_export_csv(zahtev).content.decode("utf-8-sig")), delimiter=";"))
        zaglavlje = redovi[0]
        red = dict(zip(zaglavlje, redovi[1]))
        self.assertEqual((red["Centar"], red["OJ"]), ("43", "430111"))


class IzmenaPutnogNalogaTests(TestCase):
    def setUp(self):
        self.nas = OrganizationalUnit.objects.create(code="430111", name="Nadzor", center="43")
        self.tudji = OrganizationalUnit.objects.create(code="410001", name="Materijali", center="41")
        self.korisnik = get_user_model().objects.create_user("pn-korisnik", password="x", allowed_center_codes="43")
        self.nalog_nas = self.nalog(self.nas, "43/2026-1")
        self.nalog_tudji = self.nalog(self.tudji, "41/2026-1")

    def nalog(self, jedinica, broj):
        return PutniNalog.objects.create(order_number=broj, job_code=jedinica, travel_location="BG", task="T",
                                         travel_date=datetime.date(2026, 7, 10), number_of_days=1,
                                         advance_payment=Decimal("1"))

    def pogled(self, korisnik):
        view = PutniNalogUpdateView()
        view.request = RequestFactory().post("/")
        view.request.user = korisnik
        view.kwargs = {}
        return view

    def test_upit_sadrzi_samo_naloge_centara_korisnika(self):
        self.assertEqual(list(self.pogled(self.korisnik).get_queryset()), [self.nalog_nas])
        admin = get_user_model().objects.create_superuser("pn-admin", "a@example.com", "x")
        self.assertEqual(self.pogled(admin).get_queryset().count(), 2)

    def test_nalog_se_ne_sme_prebaciti_na_tudji_centar(self):
        view = self.pogled(self.korisnik)
        view.object = self.nalog_nas
        forma = mock.Mock(cleaned_data={"job_code": self.tudji})
        with mock.patch.object(PutniNalogUpdateView, "form_invalid", return_value="neispravno") as invalid:
            self.assertEqual(view.form_valid(forma), "neispravno")
        invalid.assert_called_once()
        forma.add_error.assert_called_once()
        forma.save.assert_not_called()

    def test_nalog_ostaje_u_svom_centru(self):
        view = self.pogled(self.korisnik)
        forma = mock.Mock(cleaned_data={"job_code": self.nas})
        forma.save.return_value = self.nalog_nas
        odgovor = view.form_valid(forma)
        self.assertEqual(odgovor.status_code, 200)
        forma.save.assert_called_once()


class EkraniDodelaILizingaTests(TestCase):
    def setUp(self):
        self.car = vehicle()
        jedinica = OrganizationalUnit.objects.create(code="430111", name="Nadzor", center="43")
        self.dodela = JobCode.objects.create(vehicle=self.car, organizational_unit=jedinica,
                                             assigned_date=datetime.date(2025, 1, 1))
        self.client.force_login(get_user_model().objects.create_superuser("ekrani-admin", "e@example.com", "x"))

    def test_spisak_detalj_i_brisanje_dodele_se_otvaraju(self):
        spisak = self.client.get(reverse("jobcode_list"))
        self.assertContains(spisak, "430111 - Nadzor")
        detalj = self.client.get(reverse("jobcode_detail", args=[self.dodela.pk]))
        self.assertContains(detalj, "Dodela šifre posla 430111 - Nadzor")
        self.assertEqual(self.client.get(reverse("jobcode_delete", args=[self.dodela.pk])).status_code, 200)

    def test_izvestaj_o_lizingu_se_otvara(self):
        self.assertContains(self.client.get(reverse("lease_monthly_costs")), "Lizing — mesečni troškovi")


class LizingMesecniTroskoviTests(TestCase):
    """Jedan lizing je jedno vozilo: red po mesecu lizinga, centar po dodeli u tom mesecu,
    prateci troskovi samo tog vozila."""

    def setUp(self):
        from fleet.models import Lease, ServiceTransaction

        self.car = vehicle("1")
        self.drugo = vehicle("2")
        self.nadzor = OrganizationalUnit.objects.create(code="430111", name="Nadzor", center="43")
        self.materijali = OrganizationalUnit.objects.create(code="410001", name="Materijali", center="41")
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.nadzor, assigned_date=datetime.date(2025, 1, 1))
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.materijali, assigned_date=datetime.date(2026, 2, 10))
        JobCode.objects.create(vehicle=self.drugo, organizational_unit=self.nadzor, assigned_date=datetime.date(2025, 1, 1))
        self.lease = Lease.objects.create(
            vehicle=self.car, partner_code="1", partner_name="Lizing", job_code="430111", contract_number="L-1",
            current_payment_amount=Decimal("1000"), payment_basis="monthly", lease_type="operativni",
            start_date=datetime.date(2026, 1, 16), end_date=datetime.date(2026, 3, 31))
        for car, iznos in ((self.car, "200"), (self.drugo, "5000")):
            FuelConsumption.objects.create(vehicle=car, date=u_osam(datetime.date(2026, 1, 20)), amount=Decimal("40"),
                                           fuel_type="dizel", supplier="NIS", cost_bruto=Decimal(iznos),
                                           cost_neto=Decimal(iznos), mileage=1000)
        ServiceTransaction.objects.create(vehicle=self.car, datum=datetime.date(2026, 1, 25), potrazuje=Decimal("50"),
                                          god=2026, sif_par_pl="1", naz_par_pl="Servis", sif_vrs="1", br_naloga="1",
                                          vez_dok="1", knt_pl="1", sif_par_npl="1", knt_npl="1", duguje=Decimal("0"),
                                          konto_vozila="1")
        self.client.force_login(get_user_model().objects.create_superuser("lizing-admin", "l@example.com", "x"))

    def redovi(self, **params):
        from fleet.support.lease_queries import lease_monthly_costs_rows

        return lease_monthly_costs_rows(RequestFactory().get("/", params))

    def test_red_za_svaki_mesec_lizinga_sa_iznosom_iz_obracuna(self):
        redovi = self.redovi()
        self.assertEqual([(r["year"], r["month"]) for r in redovi], [(2026, 1), (2026, 2), (2026, 3)])
        # Januar od 16. do 31. = 16/31 mesecnog iznosa; februar i mart pun iznos.
        self.assertEqual(round(redovi[0]["lease_amount"], 2), Decimal("516.13"))
        self.assertEqual([r["lease_amount"] for r in redovi[1:]], [Decimal("1000"), Decimal("1000")])

    def test_centar_po_dodeli_u_tom_mesecu(self):
        self.assertEqual([r["center"] for r in self.redovi()], ["43", "41", "41"])
        self.assertEqual([r["month"] for r in self.redovi(center="43")], [1])

    def test_prateci_troskovi_samo_tog_vozila(self):
        januar = self.redovi(year="2026", month="1")[0]
        # Gorivo drugog vozila iz iste OJ (5.000) ne ulazi.
        self.assertEqual((januar["fuel_total"], januar["service_total"], januar["accompanying_total"]),
                         (Decimal("200"), Decimal("50"), Decimal("250")))

    def test_ekran(self):
        odgovor = self.client.get(reverse("lease_monthly_costs"), {"year": "2026"})
        self.assertContains(odgovor, "L-1")
        self.assertContains(odgovor, "430111 — Nadzor")
