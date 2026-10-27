"""OMV: raspodela fakture po šifri posla za knjiženje, sa redom „Ukupno” (od 07.10.2026.)."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from finansije.sef_models import SefFaktura
from fleet.forms.reports import PutnickaFilterForm
from fleet.models import TransactionOMV
from fleet.support.fuel_reports import SUPPLIER_OMV, VEHICLE_TYPE_PASSENGER, fuel_job_code_report, ukupno


def stavka(faktura, proizvod, kolicina, bruto, dan, tablica="BG100-AA", voucher=None):
    return TransactionOMV.objects.create(
        issuer="OMV", customer="107248", card="1", license_plate_no=tablica,
        transaction_date=timezone.make_aware(datetime.datetime(2026, *dan, 8, 0)), product_inv=proizvod,
        quantity=Decimal(kolicina), gross_cc=Decimal(bruto), vat=(Decimal(bruto) / 6).quantize(Decimal("0.01")),
        amount=Decimal(bruto), voucher=voucher or f"V{proizvod[:3]}{dan}", invoice_no=faktura,
        invoice_date=datetime.date(2026, 9, 30), invoiced=True)


class OMVFakturaTests(TestCase):
    def setUp(self):
        stavka("8916409357", "OMV EVRO DIZEL", "40.00", "9360.00", (9, 14))
        stavka("8916409357", "AdBlue Kanister", "1.00", "1499.00", (9, 20))
        stavka("8916409357", "Izrada kartica", "1.00", "150.00", (9, 25), tablica="")
        stavka("8916409357", "PUTARINA", "4700.00", "4700.00", (8, 31))  # van kalendarskog perioda, ali na fakturi
        stavka("8916406404", "OMV EVRO DIZEL", "10.00", "2340.00", (9, 2))  # druga faktura

    def test_faktura_obuhvata_sve_stavke_i_ima_ukupno(self):
        form = PutnickaFilterForm({"faktura": "8916409357"})
        self.assertTrue(form.is_valid(), form.errors)
        summary, _ = fuel_job_code_report(form, supplier=SUPPLIER_OMV, vehicle_type=VEHICLE_TYPE_PASSENGER)
        zbir = ukupno(summary)
        self.assertEqual(zbir["broj_transakcija"], 4)
        self.assertEqual(zbir["bruto"], Decimal("15709.00"))
        # Cela faktura u jednom redu po šifri, sa mesecom i polovinom fakturisanog perioda (faktura od 30.09.).
        self.assertEqual({(r["godina"], r["mesec"], r["polovina"]) for r in summary}, {(2026, 9, 2)})

    def test_ekran_poredi_sa_sef_om_i_prikazuje_ukupno(self):
        SefFaktura.objects.create(smer="ulazna", sef_id=479593522, broj="8916409357", partner_naziv="OMV SRBIJA DOO",
                                  iznos=Decimal("15709.00"), osnovica=Decimal("13090.83"), pdv=Decimal("2618.17"),
                                  sinhronizovano=timezone.now())
        self.client.force_login(get_user_model().objects.create_superuser("omv", password="x"))
        odgovor = self.client.get(reverse("fuel_job_code_omv_putnicka"), {"faktura": "8916409357"})
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, "Poklapa se")
        self.assertContains(odgovor, "UKUPNO")
        self.assertContains(odgovor, "8916406404")  # izbor fakture
        excel = self.client.get(reverse("fuel_job_code_omv_putnicka"), {"faktura": "8916409357", "export": "1"})
        self.assertEqual(excel.status_code, 200)


class OMVUvozStavkiIstogRacunaTests(TestCase):
    """Dve stavke istog računa sa istim ključem ne smeju da se prepišu (faktura 8916409357, 07.10.2026.)."""

    ZAGLAVLJE = ["Issuer", "Customer", "Card", "License plate No", "Transactiondate", "Product INV", "Quantity",
                 "Gross CC", "VAT", "Voucher", "Mileage", "Corrected mileage", "Additional info", "Supply country",
                 "Site Town", "Product DEL", "Unitprice", "Amount", "Discount", "Surcharge", "VAT2010",
                 "Suppliercurrency", "Invoice No", "Invoice date", "Invoiced?", "State", "Supplier", "Cost 1",
                 "Cost 2", "Reference No", "Recordtype", "Amount other", "is listprice ?", "Approval code",
                 "Date to", "Final Trx.", "LPI"]

    def setUp(self):
        from fleet.models import TrafficCard, Vehicle
        for tablica, inv in (("BG3244-OT", "1"), ("BG2024-OU", "2")):
            v = Vehicle.objects.create(inventory_number=inv, chassis_number=f"VIN{inv}", brand="Fiat", model="Doblo",
                                       year_of_manufacture=2020, color="Bela", number_of_axles=2,
                                       engine_volume=Decimal("1400"), engine_number=f"E{inv}", weight=Decimal("1000"),
                                       engine_power=Decimal("70"), load_capacity=Decimal("500"),
                                       category=Vehicle.Category.PASSENGER, maximum_permissible_weight=Decimal("1800"),
                                       fuel_type="DIZEL", number_of_seats=5, purchase_value=Decimal("1"), value=Decimal("1"))
            TrafficCard.objects.create(vehicle=v, registration_number=tablica, issue_date=datetime.date(2020, 1, 1),
                                       traffic_card_number=f"T{inv}", serial_number=f"S{inv}", owner="IMS")

    def red(self, **izmene):
        osnova = {k: "" for k in self.ZAGLAVLJE}
        osnova.update({"Issuer": "710111", "Customer": "107248", "Card": "1037", "License plate No": "BG3244-OT",
                       "Transactiondate": "2026-09-14 07:55:00", "Product INV": "AdBlue Kanister", "Quantity": "1.00",
                       "Gross CC": "2,199.00", "VAT": "366.50", "Voucher": "00316171", "Amount": "2,199.00",
                       "Invoice No": "8916409357", "Invoice date": "2026-09-30", "Invoiced?": "YES",
                       "is listprice ?": "No", "Final Trx.": "1", "Recordtype": "D"})
        osnova.update(izmene)
        return osnova

    def uvezi(self, redovi):
        import csv, os, tempfile
        from fleet.sync.selenium import import_omv_transactions_from_csv
        with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8-sig", suffix=".csv", delete=False) as h:
            pisac = csv.DictWriter(h, fieldnames=self.ZAGLAVLJE, delimiter=";")
            pisac.writeheader()
            pisac.writerows(redovi)
            putanja = h.name
        try:
            return import_omv_transactions_from_csv(putanja)
        finally:
            os.unlink(putanja)

    def test_dva_kanistera_i_dve_kartice_ostaju_cetiri_stavke_i_ponovni_uvoz_ne_duplira(self):
        kartice = dict(**{"License plate No": "BG 2024 - OU", "Transactiondate": "2026-09-26 00:00:00",
                          "Product INV": "Izrada kartica", "Voucher": "00000001", "Gross CC": "150.00", "Amount": "150.00"})
        redovi = [self.red(), self.red(**{"Gross CC": "1,499.00", "Amount": "1,499.00"}),
                  self.red(Card="1102", **kartice), self.red(Card="1094", **kartice),
                  self.red()]  # isti red dvaput u fajlu: ponovljen izvoz
        prvi = self.uvezi(redovi)
        self.assertEqual((prvi["created"], prvi["skipped_identical_rows"]), (4, 1))
        self.assertEqual(TransactionOMV.objects.filter(invoice_no="8916409357").count(), 4)
        self.assertEqual(sum(t.gross_cc for t in TransactionOMV.objects.all()), Decimal("3998.00"))
        from fleet.support.fuel import deduplicate_omv_transactions
        self.assertEqual(deduplicate_omv_transactions(TransactionOMV.objects.all()).count(), 4)  # izveštaji vide sve 4
        drugi = self.uvezi(redovi)
        self.assertEqual((drugi["created"], drugi["updated"]), (0, 4))
        self.assertEqual(TransactionOMV.objects.count(), 4)


class KontrolaFakturaGorivaTests(TestCase):
    def test_poredi_sef_transakcije_i_knjizenje_po_sifri(self):
        from core.models import PermissionCode, Role
        from finansije.models import LedgerEntry
        from fleet.support.fuel_invoices import kontrola_faktura

        stavka("8916409360", "OMV EVRO DIZEL", "40.00", "1200.00", (9, 20))
        TransactionOMV.objects.filter(invoice_no="8916409360").update(customer="107258")  # teretna
        SefFaktura.objects.create(smer="ulazna", sef_id=1, broj="8916409360", partner_naziv="OMV SRBIJA DOO",
                                  partner_pib="101987198", vrsta="Invoice", iznos=Decimal("1200.00"),
                                  osnovica=Decimal("1000.00"), pdv=Decimal("200.00"),
                                  datum_prometa=datetime.date(2026, 9, 30), sinhronizovano=timezone.now())
        polja = dict(company=1, year=2026, journal_type="EUF", journal_number=1, document_reference="8916409360",
                     description="OMV", credit=Decimal("0"), organizational_unit=1,
                     document_date=datetime.date(2026, 10, 2), booking_date=datetime.date(2026, 10, 2),
                     changed_at=timezone.now())
        # Ceo neto na jednu šifru (kao 8916403500) — kontrola mora da pokaže razliku po šiframa.
        LedgerEntry.objects.create(line_number=1, account="51300", job_code="832111", debit=Decimal("1000.00"),
                                   source_hash="a", **polja)
        LedgerEntry.objects.create(line_number=2, account="27000", job_code="", debit=Decimal("200.00"),
                                   source_hash="b", **polja)

        red = next(r for r in kontrola_faktura(2026, 9) if r["oznaka"] == "8916409360")
        self.assertEqual(red["kartica"], "Teretna vozila")
        self.assertEqual(red["razlika_transakcija"], Decimal("0.00"))
        self.assertEqual(red["razlika_knjizenja"], Decimal("0.00"))
        self.assertEqual({s["sifra"] for s in red["razlike_sifara"]}, {"832111", "(bez šifre)"})

        korisnik = get_user_model().objects.create_user("kontrola", password="x")
        self.client.force_login(korisnik)
        url = reverse("fuel_invoice_control")
        self.assertEqual(self.client.get(url, {"godina": "2026", "mesec": "9"}).status_code, 403)
        uloga = Role.objects.create(name="Kontrola", slug="kontrola")
        uloga.permissions.add(PermissionCode.objects.get_or_create(code="fuel_invoice_control")[0])
        korisnik.roles.add(uloga)
        odgovor = self.client.get(url, {"godina": "2026", "mesec": "9"})
        self.assertContains(odgovor, "Raspodela po šiframa posla se razlikuje")


class PodrazumevaniPeriodTests(TestCase):
    def test_bez_filtera_poslednja_faktura_kartice_i_poslednja_nis_polovina(self):
        from fleet.support.fuel_reports import SUPPLIER_NIS, VEHICLE_TYPE_TRUCK, poslednji_fakturisani_period

        stavka("8916406404", "OMV EVRO DIZEL", "10.00", "2340.00", (9, 2))
        TransactionOMV.objects.filter(invoice_no="8916406404").update(invoice_date=datetime.date(2026, 9, 13))
        stavka("8916409357", "OMV EVRO DIZEL", "10.00", "2340.00", (9, 20))
        self.assertEqual(poslednji_fakturisani_period(SUPPLIER_OMV, VEHICLE_TYPE_PASSENGER),
                         {"faktura": "8916409357", "godina": "2026", "mesec": "9", "polovina": "2"})
        SefFaktura.objects.create(smer="ulazna", sef_id=2, broj="9006720949", partner_pib="104052135", vrsta="Invoice",
                                  datum_prometa=datetime.date(2026, 9, 15), sinhronizovano=timezone.now())
        self.assertEqual(poslednji_fakturisani_period(SUPPLIER_NIS, VEHICLE_TYPE_TRUCK),
                         {"godina": "2026", "mesec": "9", "polovina": "1"})
        self.client.force_login(get_user_model().objects.create_superuser("period", password="x"))
        odgovor = self.client.get(reverse("fuel_job_code_omv_putnicka"))
        self.assertContains(odgovor, "Prikazan je poslednji fakturisani period")
        self.assertEqual(odgovor.context["faktura"], "8916409357")
        self.assertEqual((odgovor.context["form"]["godina"].value(), odgovor.context["form"]["mesec"].value()), ("2026", "9"))
        self.assertContains(odgovor, "2026 · 9. mesec · druga polovina")
        izabrana = self.client.get(reverse("fuel_job_code_omv_putnicka"), {"faktura": "8916406404"})
        self.assertEqual(izabrana.context["form"]["polovina"].value(), "1")  # faktura od 13.09. = prva polovina


class NISPotvrdaTests(TestCase):
    """08.10.2026.: izveštaji NIS putnička i teretna potvrđuju da se fakture polovine i obračun slažu (kao OMV)."""

    def tocenje(self, broj, total, dan):
        from fleet.models import TransactionNIS

        return TransactionNIS.objects.create(
            kupac="IMS", sifra_kupca="1", broj_kartice="123", kompanijski_kod_kupca="217", zemlja_sipanja="SR",
            benzinska_stanica="LAPOVO", id_transakcije=broj, app_kod="APP",
            datum_transakcije=timezone.make_aware(datetime.datetime(2026, 9, dan, 9, 0)), tociono_mesto="1",
            registarska_oznaka_vozila="BG123-AA", broj_racuna=broj, kilometraza=1000, sipanje_van_rezervoara=False,
            naziv_proizvoda="EVRO DIZEL", kolicina=Decimal("10.00"), popust=Decimal("0"), primenjen_popust="",
            cena_sa_kase=Decimal("200"), cena=Decimal("200"), total_sa_kase=Decimal(total), total=Decimal(total),
            valuta="RSD", aktivirano_prekoracenje=False, kolicinsko_prekoracenje=False, finansijsko_prekoracenje=False,
            nacin_ocitavanja_kartice="manual")

    def test_fakture_polovine_i_obracun(self):
        self.tocenje("1", "6000.00", 3)
        druga = self.tocenje("2", "4000.00", 12)
        self.tocenje("3", "9999.00", 20)  # druga polovina — ne ulazi
        for sef_id, broj, iznos in ((1, "9006720949", "7000.00"), (2, "9006720950", "3000.00")):
            SefFaktura.objects.create(smer="ulazna", sef_id=sef_id, broj=broj, partner_pib="104052135", vrsta="Invoice",
                                      iznos=Decimal(iznos), osnovica=Decimal(iznos) / Decimal("1.2"),
                                      pdv=Decimal(iznos) - Decimal(iznos) / Decimal("1.2"),
                                      datum_prometa=datetime.date(2026, 9, 15), sinhronizovano=timezone.now())
        self.client.force_login(get_user_model().objects.create_superuser("nis-potvrda", password="x"))
        filter_ = {"godina": "2026", "mesec": "9", "polovina": "1"}
        for ruta in ("fuel_job_code_nis_putnicka", "fuel_job_code_nis_teretna"):
            odgovor = self.client.get(reverse(ruta), filter_)
            k = odgovor.context["nis_kontrola"]
            self.assertEqual((k["sef_bruto"], k["transakcije_bruto"], k["poklapa"]), (Decimal("10000.00"), Decimal("10000.00"), True))
            self.assertContains(odgovor, "Poklapa se")
            self.assertContains(odgovor, "9006720949")
        druga.delete()
        odgovor = self.client.get(reverse("fuel_job_code_nis_putnicka"), filter_)
        self.assertFalse(odgovor.context["nis_kontrola"]["poklapa"])
        self.assertContains(odgovor, "Ne poklapa se")
        self.assertIsNone(self.client.get(reverse("fuel_job_code_omv_putnicka"), filter_).context["nis_kontrola"])


class UvozBezVozilaTests(TestCase):
    def test_transakcija_bez_vozila_se_upisuje_i_kasnije_povezuje(self):
        from fleet.sync.selenium import povezi_transakcije_sa_vozilima
        from fleet.models import TrafficCard, Vehicle

        t = stavka("8916409357", "OMV EVRO DIZEL", "10.00", "2340.00", (9, 20), tablica="BG3435-GH")
        self.assertIsNone(t.vehicle_id)
        self.assertEqual(povezi_transakcije_sa_vozilima(), 0)
        v = Vehicle.objects.create(inventory_number="9", chassis_number="VIN9", brand="Fiat", model="Panda",
                                   year_of_manufacture=2026, color="Bela", number_of_axles=2, engine_volume=Decimal("1200"),
                                   engine_number="E9", weight=Decimal("900"), engine_power=Decimal("50"),
                                   load_capacity=Decimal("400"), category=Vehicle.Category.PASSENGER,
                                   maximum_permissible_weight=Decimal("1400"), fuel_type="BMB", number_of_seats=5,
                                   purchase_value=Decimal("1"), value=Decimal("1"))
        TrafficCard.objects.create(vehicle=v, registration_number="BG3435-GH", issue_date=datetime.date(2026, 8, 27),
                                   traffic_card_number="T9", serial_number="S9", owner="IMS")
        self.assertEqual(povezi_transakcije_sa_vozilima(), 1)
        t.refresh_from_db()
        self.assertEqual(t.vehicle_id, v.pk)


class IzvozIzvestajaTests(TestCase):
    def test_pdf_i_excel_izvestaja_goriva(self):
        stavka("8916409357", "OMV EVRO DIZEL", "40.00", "9360.00", (9, 14))
        self.client.force_login(get_user_model().objects.create_superuser("izvoz", password="x"))
        for ruta, parametri in (("fuel_job_code_omv_putnicka", {}), ("fuel_invoice_control", {"godina": "2026", "mesec": "9"})):
            pdf = self.client.get(reverse(ruta), {**parametri, "export": "pdf"})
            self.assertEqual(pdf["Content-Type"], "application/pdf", ruta)
            self.assertTrue(pdf.content.startswith(b"%PDF"), ruta)
            excel = self.client.get(reverse(ruta), {**parametri, "export": "xlsx" if ruta == "fuel_invoice_control" else "1"})
            self.assertIn("spreadsheetml", excel["Content-Type"], ruta)
        self.assertContains(self.client.get(reverse("fuel_invoice_control")), "export=pdf")

    def test_pdf_upravljackog_izvestaja(self):
        self.client.force_login(get_user_model().objects.create_superuser("izvoz2", password="x"))
        strana = self.client.get(reverse("casco_report"))
        self.assertContains(strana, "Preuzmi PDF")
        pdf = self.client.get(reverse("casco_report") + "?" + strana.context["export_pdf_query"])
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))


class NISFakturaPoKarticiTests(TestCase):
    """27.10.2026.: NIS deli fakture polovine („Putničko“ / „Teretno“) po kartici, ne po kategoriji vozila u Floti;
    svaka faktura mora da se složi u dinar sa transakcijama svojih kartica."""

    SPECIFIKACIJA = (
        "NIS a.d. Novi Sad\nIzvestaj o obavljenoj kupovini putem kompanijske Kreditne kartice\n"
        "Komitent : Faktura : Tip vozila :2205247 - INSTITUT IMS AD BEOGRAD\n \n{broj} {tip}\n"
        "11028 EVRO PREMIJUM BMB-95 205.010.09.2026 14:16 DRX BS Surcin - selo 48.54 9,950.70 3030076BG 826 VJ\n"
        "Ukupno za karticu : 7824723061569717 48.54 9,950.70\n"
        "11003 EVRO DIZEL 234.011.09.2026 06:39 SKT BS Dzona Kenedija 5.04 1,179.36 5673401BG 1461 EB\n"
        "Ukupno za karticu : 7824723063178053 5.04 1,179.36\n")

    def setUp(self):
        from fleet.models import Vehicle

        self.putnicko = Vehicle.objects.create(
            inventory_number="P1", chassis_number="VINP1", brand="Dacia", model="Sandero", year_of_manufacture=2020,
            color="Bela", number_of_axles=2, engine_volume=Decimal("999"), engine_number="EP1", weight=Decimal("1000"),
            engine_power=Decimal("50"), load_capacity=Decimal("400"), category=Vehicle.Category.PASSENGER,
            maximum_permissible_weight=Decimal("1500"), fuel_type="BMB", number_of_seats=5, purchase_value=Decimal("1"),
            value=Decimal("1"))

    def tocenje(self, broj, kartica, total, dan, vozilo=None):
        from fleet.models import TransactionNIS

        return TransactionNIS.objects.create(
            vehicle=vozilo, kupac="IMS", sifra_kupca="1", broj_kartice=kartica, kompanijski_kod_kupca="217",
            zemlja_sipanja="SR", benzinska_stanica="LAPOVO", id_transakcije=broj, app_kod="APP",
            datum_transakcije=timezone.make_aware(datetime.datetime(2026, 9, dan, 9, 0)), tociono_mesto="1",
            registarska_oznaka_vozila=f"BG{broj}-AA", broj_racuna=broj, kilometraza=1000, sipanje_van_rezervoara=False,
            naziv_proizvoda="EVRO DIZEL", kolicina=Decimal("10.00"), popust=Decimal("0"), primenjen_popust="",
            cena_sa_kase=Decimal("200"), cena=Decimal("200"), total_sa_kase=Decimal(total), total=Decimal(total),
            valuta="RSD", aktivirano_prekoracenje=False, kolicinsko_prekoracenje=False, finansijsko_prekoracenje=False,
            nacin_ocitavanja_kartice="manual")

    def faktura(self, sef_id, broj, iznos):
        return SefFaktura.objects.create(smer="ulazna", sef_id=sef_id, broj=broj, partner_pib="104052135", vrsta="Invoice",
                                         iznos=Decimal(iznos), osnovica=Decimal(iznos) / Decimal("1.2"),
                                         pdv=Decimal(iznos) - Decimal(iznos) / Decimal("1.2"),
                                         datum_prometa=datetime.date(2026, 9, 15), sinhronizovano=timezone.now())

    def kartice(self, faktura, tip, *kartice):
        from fleet.models import NisKarticaFakture

        for k in kartice:
            NisKarticaFakture.objects.create(faktura=faktura, datum_prometa=datetime.date(2026, 9, 15), tip=tip, kartica=k,
                                             iznos=Decimal("0"))

    def test_specifikacija_se_cita_iz_teksta(self):
        from fleet.support.nis_kartice import TERETNA, iz_teksta, kartica

        broj, tip, kartice = iz_teksta(self.SPECIFIKACIJA.format(broj="9006720950", tip="Teretno"))
        self.assertEqual((broj, tip), ("9006720950", TERETNA))
        self.assertEqual(kartice, {"7824723061569717": Decimal("9950.70"), "7824723063178053": Decimal("1179.36")})
        self.assertEqual(kartica("7824723061569717.0"), "7824723061569717")

    def test_specifikacija_se_ucitava_iz_priloga_fakture(self):
        import io
        import tempfile

        from django.core.files.base import ContentFile
        from django.test import override_settings
        from reportlab.pdfgen import canvas

        from finansije.sef_models import SefPrilog
        from fleet.models import NisKarticaFakture
        from fleet.support.nis_kartice import ucitaj_specifikacije

        pdf = io.BytesIO()
        platno = canvas.Canvas(pdf)
        for i, red in enumerate(self.SPECIFIKACIJA.format(broj="9006720950", tip="Teretno").splitlines()):
            platno.drawString(20, 800 - 14 * i, red)
        platno.save()
        with override_settings(MEDIA_ROOT=tempfile.mkdtemp()):
            f = self.faktura(2, "9006720950", "11130.06")
            SefPrilog.objects.create(faktura=f, redni=1, naziv="/mft_sef/0002205247-9006720950-specifikacija_uz_fakturu.pdf",
                                     fajl=ContentFile(pdf.getvalue(), name="spec.pdf"))
            self.assertEqual(ucitaj_specifikacije([f]), 1)
            self.assertEqual(ucitaj_specifikacije([f]), 0)  # već učitana
        self.assertEqual(set(NisKarticaFakture.objects.values_list("kartica", "tip")),
                         {("7824723061569717", "teretna"), ("7824723063178053", "teretna")})

    def test_bez_fajla_priloga_specifikacija_se_cita_sa_sef_a(self):
        from unittest.mock import patch

        from finansije.sef_models import SefPrilog
        from fleet.models import NisKarticaFakture
        from fleet.support.nis_kartice import ucitaj_specifikacije

        f = self.faktura(2, "9006720950", "11130.06")
        # Prilog je upisan, ali fajl je samo na serveru.
        SefPrilog.objects.create(faktura=f, redni=1, naziv="/mft_sef/0002205247-9006720950-specifikacija_uz_fakturu.pdf",
                                 fajl="finansije/sef/prilozi/nema.pdf")
        tekst = self.SPECIFIKACIJA.format(broj="9006720950", tip="Teretno")
        with patch("finansije.services.sef.Klijent") as klijent, \
                patch("finansije.services.sef.prilozi_iz_ubl",
                      return_value=[{"naziv": "0002205247-9006720950-specifikacija_uz_fakturu.pdf", "sadrzaj": b"%PDF"}]), \
                patch("fleet.support.nis_kartice.tekst_pdf", return_value=tekst):
            self.assertEqual(ucitaj_specifikacije([f]), 1)
        klijent.return_value.ubl.assert_called_once_with("ulazna", 2)
        self.assertEqual(NisKarticaFakture.objects.filter(faktura="9006720950", tip="teretna").count(), 2)

    def test_svaka_faktura_se_poredi_sa_svojim_karticama(self):
        from fleet.support.fuel_invoices import kontrola_faktura, nis_potvrda
        from fleet.support.fuel_reports import SUPPLIER_NIS, VEHICLE_TYPE_TRUCK

        # Vozilo je u Floti putničko, ali je njegova kartica na teretnoj fakturi — ide na teretnu.
        self.tocenje("1", "7824723061569717.0", "9950.70", 3, vozilo=self.putnicko)
        self.tocenje("2", "1111.0", "6000.00", 5, vozilo=self.putnicko)
        self.tocenje("3", "2222.0", "1000.00", 7)  # vozilo još nije u Floti — ipak je na fakturi
        self.faktura(1, "9006720949", "6000.00")
        self.faktura(2, "9006720950", "10950.70")
        self.kartice("9006720949", "putnicka", "1111")
        self.kartice("9006720950", "teretna", "7824723061569717", "2222")

        k = nis_potvrda(2026, 9, 1)
        self.assertTrue(k["poklapa"])
        self.assertEqual([(r["faktura"].broj, r["transakcije"], r["poklapa"]) for r in k["redovi"]],
                         [("9006720949", Decimal("6000.00"), True), ("9006720950", Decimal("10950.70"), True)])

        nis = [r for r in kontrola_faktura(2026, 9) if r["dobavljac"] == "NIS"]
        self.assertEqual([(r["oznaka"], r["kartica"], r["razlika_transakcija"]) for r in nis],
                         [("9006720949", "Putnička vozila", Decimal("0.00")), ("9006720950", "Teretna vozila", Decimal("0.00"))])

        form = PutnickaFilterForm({"godina": "2026", "mesec": "9", "polovina": "1"})
        self.assertTrue(form.is_valid(), form.errors)
        summary, _ = fuel_job_code_report(form, supplier=SUPPLIER_NIS, vehicle_type=VEHICLE_TYPE_TRUCK)
        self.assertEqual(ukupno(summary)["bruto"], Decimal("10950.70"))

    def test_faktura_koja_se_ne_slaze_se_vidi_pojedinacno(self):
        from fleet.support.fuel_invoices import nis_potvrda

        self.tocenje("1", "1111.0", "6000.00", 5, vozilo=self.putnicko)
        self.tocenje("2", "2222.0", "1000.00", 7, vozilo=self.putnicko)
        # Zbir obe fakture se slaže (7000), ali je 1000 na pogrešnoj fakturi.
        self.faktura(1, "9006720949", "5000.00")
        self.faktura(2, "9006720950", "2000.00")
        self.kartice("9006720949", "putnicka", "1111")
        self.kartice("9006720950", "teretna", "2222")

        k = nis_potvrda(2026, 9, 1)
        self.assertEqual(k["razlika"], Decimal("0.00"))
        self.assertFalse(k["poklapa"])
        self.assertEqual([r["razlika"] for r in k["redovi"]], [Decimal("1000.00"), Decimal("-1000.00")])
        self.client.force_login(get_user_model().objects.create_superuser("nis-kartice", password="x"))
        odgovor = self.client.get(reverse("fuel_job_code_nis_putnicka"), {"godina": "2026", "mesec": "9", "polovina": "1"})
        self.assertContains(odgovor, "ne poklapa se")
