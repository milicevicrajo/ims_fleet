"""Flota → Incidenti: spisak, unos, izmena, brisanje i predlog vozaca za dan prekrsaja."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import PermissionCode, Role
from fleet.models import Incident, OrganizationalUnit, PutniNalog, VehicleTravelOrder
from fleet.support.incidenti import vozaci_na_dan
from fleet.test_vehicle_onboarding import card, vehicle
from hr.models import Employee


def zaposleni(sifra, prezime):
    return Employee.objects.create(employee_code=sifra, first_name="Ime", last_name=prezime, position="Vozac",
                                   department_code=1, gender="M", date_of_birth=datetime.date(1980, 1, 1),
                                   date_of_joining=datetime.date(2020, 1, 1))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="fleet-incidenti-"))
class IncidentiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    KODOVI = ("incident_list", "incident_data", "incident_detail", "incident_prilog", "incident_create", "incident_update",
              "incident_delete", "incident_vozaci")

    def setUp(self):
        self.vozilo = vehicle("7")
        card(self.vozilo, plate="BG123-AA")
        self.petrovic, self.jovic = zaposleni(11, "Petrovic"), zaposleni(12, "Jovic")
        self.uloga = Role.objects.create(name="Garaza test", slug="garaza-test")
        for kod in self.KODOVI:
            self.uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        self.korisnik = get_user_model().objects.create_user("garaza-incidenti", password="x")
        self.korisnik.roles.add(self.uloga)
        self.client.force_login(self.korisnik)

    def podaci(self, **izmene):
        return {"vehicle": self.vozilo.pk, "date": "15.09.2026", "location": "Beograd", "employee": self.petrovic.pk,
                "violation": "Prekoračenje brzine", "fine_amount": "6000", "note": "", **izmene}

    def podaci_tabele(self, **parametri):
        return self.client.get(reverse("incident_data"), {"draw": 1, "start": 0, "length": 50, **parametri}).json()

    def test_unos_spisak_izmena_i_brisanje(self):
        odgovor = self.client.post(reverse("incident_create"), self.podaci())
        incident = Incident.objects.get()
        self.assertRedirects(odgovor, reverse("incident_list"), fetch_redirect_response=False)
        self.assertEqual((incident.date, incident.fine_amount, incident.uneo), (datetime.date(2026, 9, 15), Decimal("6000"), self.korisnik))
        self.assertContains(self.client.get(reverse("incident_list")), 'id="IncidentTable"')
        podaci = self.podaci_tabele()
        self.assertEqual((podaci["recordsTotal"], podaci["zbir"]["broj"], podaci["zbir"]["iznos"]), (1, 1, "6.000,00"))
        self.assertIn("Prekoračenje brzine", podaci["data"][0]["prekrsaj"])
        self.assertIn("BG123-AA", podaci["data"][0]["vozilo"])
        self.assertEqual(self.podaci_tabele(**{"search[value]": "bg 123"})["recordsFiltered"], 1)
        self.assertEqual(self.podaci_tabele(od="16.09.2026")["recordsFiltered"], 0)
        detalj = self.client.get(reverse("incident_detail", args=[incident.pk]))
        self.assertContains(detalj, "Prilog nije dodat")
        Incident.objects.filter(pk=incident.pk).update(uneo=None, uneto=None)  # uneto pre 29.09.2026.
        self.assertContains(self.client.get(reverse("incident_detail", args=[incident.pk])), "<dt>Uneo</dt><dd>—")
        self.client.post(reverse("incident_update", args=[incident.pk]), self.podaci(employee=self.jovic.pk, fine_amount="3000"))
        incident.refresh_from_db()
        self.assertEqual((incident.employee, incident.fine_amount), (self.jovic, Decimal("3000")))
        self.client.post(reverse("incident_delete", args=[incident.pk]))
        self.assertFalse(Incident.objects.exists())

    def test_prilog_se_cuva_prikazuje_i_proverava(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        pdf = SimpleUploadedFile("zapisnik.pdf", b"%PDF-1.4 kazna", content_type="application/pdf")
        self.client.post(reverse("incident_create"), {**self.podaci(), "prilog": pdf})
        incident = Incident.objects.get()
        self.assertEqual(incident.prilog_naziv, "zapisnik.pdf")
        detalj = self.client.get(reverse("incident_detail", args=[incident.pk]))
        self.assertContains(detalj, f'<iframe class="inc-prilog-okvir" src="{reverse("incident_prilog", args=[incident.pk])}"')
        fajl = self.client.get(reverse("incident_prilog", args=[incident.pk]))
        self.assertEqual((fajl.status_code, b"".join(fajl.streaming_content)), (200, b"%PDF-1.4 kazna"))
        self.assertEqual(fajl.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertEqual(self.podaci_tabele(prilog="da")["recordsFiltered"], 1)
        los = SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")
        odgovor = self.client.post(reverse("incident_update", args=[incident.pk]), {**self.podaci(), "prilog": los})
        self.assertContains(odgovor, "Prilog može biti PDF ili slika")

    def test_negativna_kazna_se_odbija(self):
        odgovor = self.client.post(reverse("incident_create"), self.podaci(fine_amount="-5"))
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, "ne može biti negativan")
        self.assertFalse(Incident.objects.exists())

    def test_predlog_vozaca_iz_zaduzenja_i_putnog_naloga(self):
        VehicleTravelOrder.objects.create(employee=self.petrovic, vehicle=self.vozilo, created_at=datetime.date(2026, 9, 1),
                                          closed_at=datetime.date(2026, 9, 20))
        VehicleTravelOrder.objects.create(employee=self.jovic, vehicle=self.vozilo, created_at=datetime.date(2026, 8, 1),
                                          closed_at=datetime.date(2026, 8, 31))  # zatvoreno pre prekrsaja
        sifra = OrganizationalUnit.objects.create(code="410001", name="A", center="41")
        osnova = {"job_code": sifra, "order_date": datetime.date(2026, 9, 10), "travel_location": "Niš", "task": "Teren",
                  "advance_payment": Decimal("0"), "vehicle": self.vozilo}
        PutniNalog.objects.create(order_number="PN/2026-1", employee=self.jovic, travel_date=datetime.date(2026, 9, 14),
                                  number_of_days=2, **osnova)
        PutniNalog.objects.create(order_number="PN/2026-2", employee=self.jovic, travel_date=datetime.date(2026, 9, 10),
                                  number_of_days=1, storniran=True, **osnova)
        predlog = vozaci_na_dan(self.vozilo.pk, datetime.date(2026, 9, 15))
        self.assertEqual([v["id"] for v in predlog], [self.petrovic.pk, self.jovic.pk])
        self.assertIn("zaduženje", predlog[0]["izvor"])
        self.assertEqual(vozaci_na_dan(self.vozilo.pk, datetime.date(2026, 9, 16))[-1]["id"], self.petrovic.pk)  # nalog istekao
        odgovor = self.client.get(reverse("incident_vozaci"), {"vozilo": self.vozilo.pk, "datum": "15.09.2026"}).json()
        self.assertEqual(len(odgovor["vozaci"]), 2)
        self.assertEqual(self.client.get(reverse("incident_vozaci"), {"vozilo": "x"}).json(), {"vozaci": []})

    def test_bez_dozvole_nema_pristupa(self):
        self.uloga.permissions.clear()
        self.assertEqual(self.client.get(reverse("incident_list")).status_code, 403)
        self.assertEqual(self.client.post(reverse("incident_create"), self.podaci()).status_code, 403)
