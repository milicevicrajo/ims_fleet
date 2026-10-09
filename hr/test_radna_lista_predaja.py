"""Radna lista (od 07.10.2026.): šifra posla za sate rada, obavezan topli obrok, datum predaje i prilozi.
Od 09.10.2026.: svaki red sa satima traži vrstu i šifru posla (i odsustvo), a zbir sati fonda = radni dani × 8."""
import datetime
import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import OrganizationalUnit

from .models import Employee, RadnaListaPrilog, RecipientType, WorkTimeCategory, WorkTimeElement, WorkTimeSheet
from .services.attendance import ClockEvent
from .services.radna_lista import fond_sati, prvi_radni_dan_predaje

# Maj 2026: 21 radni dan (1.5. petak, praznik se računa u fond) → 168 sati.
PUN_MAJ = {d: 8 for d in range(1, 32) if datetime.date(2026, 5, d).weekday() < 5}

MEDIA = tempfile.mkdtemp(prefix="radna-lista-")


@override_settings(MEDIA_ROOT=MEDIA)
class PredajaRadneListeTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.employee = Employee.objects.create(
            employee_code=501, first_name="Petar", last_name="Petrovic", position="Inzenjer", department_code=1,
            gender="M", date_of_birth=datetime.date(1990, 1, 1), date_of_joining=datetime.date(2020, 1, 1))
        self.user = get_user_model().objects.create_user("radnik", password="x", employee=self.employee)
        self.unit = OrganizationalUnit.objects.create(code="200", name="Centar 200", center="20")
        self.bolovanje = WorkTimeCategory.objects.create(code="bolovanje", name="Bolovanje")
        self.redovan = WorkTimeCategory.objects.create(code="redovan_rad", name="Redovan rad")
        self.prekovremeni = WorkTimeCategory.objects.create(code="prekovremeni_rad", name="Prekovremeni rad")
        primalac = RecipientType.objects.create(code="01", name="Zaposleni")
        WorkTimeElement.objects.create(recipient_type=primalac, category=self.bolovanje, payroll_code=40,
                                       payroll_name="Bolovanje do 30 dana")
        WorkTimeElement.objects.create(recipient_type=primalac, category=self.redovan, payroll_code=1, payroll_name="Redovan")
        WorkTimeElement.objects.create(recipient_type=primalac, category=self.prekovremeni, payroll_code=6, payroll_name="Prek.")
        Employee.objects.filter(pk=self.employee.pk).update(recipient_code="01")
        self.client.force_login(self.user)
        self.client.get(reverse("hr:work_time_sheet"), {"month": 5, "year": 2026})
        self.sheet = WorkTimeSheet.objects.get(employee=self.employee, month=5, year=2026)

    def podaci(self, action="submit_print", meal_days="0", meal_unit="", red=None, drugi=None):
        """Prvi red: {'sifra': unit|None, 'vrsta': kategorija|None, 'sati': {dan: sati}}; `drugi` — drugi red."""
        red = red or {}
        redovi = {0: red, 1: drugi or {}}
        data = {"month": "5", "year": "2026", "action": action, "status": WorkTimeSheet.Status.DRAFT,
                "meal_days": meal_days, "meal_organizational_unit": str(meal_unit.pk) if meal_unit else "",
                "field_allowance_days": "", "lines-TOTAL_FORMS": "12", "lines-INITIAL_FORMS": "12",
                "lines-MIN_NUM_FORMS": "12", "lines-MAX_NUM_FORMS": "12"}
        for index, line in enumerate(self.sheet.lines.order_by("line_number")):
            prefix = f"lines-{index}"
            r = redovi.get(index, {})
            data[f"{prefix}-id"] = str(line.pk)
            data[f"{prefix}-line_number"] = str(line.line_number)
            data[f"{prefix}-organizational_unit"] = str(r["sifra"].pk) if r.get("sifra") else ""
            data[f"{prefix}-work_category"] = str(r["vrsta"].pk) if r.get("vrsta") else ""
            for day in range(1, 32):
                data[f"{prefix}-day_{day}"] = str(r.get("sati", {}).get(day, ""))
            data[f"{prefix}-work_conditions"] = ""
        return data

    def posalji(self, **kw):
        return self.client.post(reverse("hr:work_time_sheet"), self.podaci(**kw))

    def test_sati_rada_bez_sifre_posla_ne_mogu_da_se_predaju(self):
        odgovor = self.posalji(red={"vrsta": self.redovan, "sati": PUN_MAJ})
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, "Lista nije predata: svaki red sa satima mora da ima vrstu i šifru posla.")
        self.assertContains(odgovor, "Unesite šifru posla.")
        self.sheet.refresh_from_db()
        self.assertEqual(self.sheet.status, WorkTimeSheet.Status.DRAFT)
        # čuvanje bez predaje je dozvoljeno
        self.assertEqual(self.posalji(action="save", red={"sati": {4: 8}}).status_code, 302)
        # sa šifrom posla predaja prolazi
        odgovor = self.posalji(red={"sifra": self.unit, "vrsta": self.redovan, "sati": PUN_MAJ})
        self.assertRedirects(odgovor, reverse("hr:work_time_sheet_print", args=[self.sheet.pk]), fetch_redirect_response=False)
        self.sheet.refresh_from_db()
        self.assertEqual(self.sheet.status, WorkTimeSheet.Status.SUBMITTED)

    def test_odsustvo_trazi_sifru_posla_i_red_trazi_vrstu(self):
        # Od 09.10.2026. i odsustvo traži šifru posla — CSV za obračun zarada je traži za svaki element.
        odgovor = self.posalji(red={"vrsta": self.bolovanje, "sati": PUN_MAJ})
        self.assertContains(odgovor, "Unesite šifru posla.")
        odgovor = self.posalji(red={"sifra": self.unit, "sati": PUN_MAJ})
        self.assertContains(odgovor, "Izaberite vrstu rada ili odsustva.")
        self.assertEqual(self.posalji(red={"sifra": self.unit, "vrsta": self.bolovanje, "sati": PUN_MAJ}).status_code, 302)

    def test_zbir_sati_mora_biti_fond_meseca(self):
        self.assertEqual(fond_sati(2026, 5), 168)
        self.assertEqual(fond_sati(2026, 5, datetime.date(2026, 5, 18)), 80)  # zaposlen od 18.5.: 10 radnih dana
        odgovor = self.posalji(red={"sifra": self.unit, "vrsta": self.redovan, "sati": {4: 8}})
        self.assertContains(odgovor, "zbir sati rada i odsustva je 8, a fond meseca je 168 (21 radnih dana × 8)")
        # prekovremeni rad je van fonda: 168 redovnih + 8 prekovremenih prolazi
        odgovor = self.posalji(red={"sifra": self.unit, "vrsta": self.redovan, "sati": PUN_MAJ},
                               drugi={"sifra": self.unit, "vrsta": self.prekovremeni, "sati": {9: 8}})
        self.assertEqual(odgovor.status_code, 302)

    def test_topli_obrok_je_obavezan_pri_predaji(self):
        odgovor = self.posalji(meal_days="")
        self.assertContains(odgovor, "Unesite broj dana za topli obrok (0 ako ga nema).")
        odgovor = self.posalji(meal_days="22")
        self.assertContains(odgovor, "Izaberi sifru posla za topli obrok.")
        self.assertEqual(self.posalji(meal_days="22", meal_unit=self.unit,
                                      red={"sifra": self.unit, "vrsta": self.redovan, "sati": PUN_MAJ}).status_code, 302)

    @patch("hr.views.get_clock_events")
    def test_topli_obrok_predlog_su_radni_dani_sa_kucanjem(self, prolazi):
        WorkTimeSheet.objects.filter(pk=self.sheet.pk).update(meal_days=None)
        Employee.objects.filter(pk=self.employee.pk).update(org_unit_code="200")
        prolazi.return_value = [
            ClockEvent(1, 501, "Petrovic", "Petar", "", 1, datetime.datetime(2026, 5, 4, 8, 0), 1),
            ClockEvent(1, 501, "Petrovic", "Petar", "", 2, datetime.datetime(2026, 5, 4, 16, 0), 2),
            ClockEvent(1, 501, "Petrovic", "Petar", "", 3, datetime.datetime(2026, 5, 5, 8, 0), 1),
            ClockEvent(1, 501, "Petrovic", "Petar", "", 4, datetime.datetime(2026, 5, 9, 8, 0), 1),  # subota
            ClockEvent(1, 501, "Petrovic", "Petar", "", 5, datetime.datetime(2026, 5, 1, 8, 0), 1),  # praznik
        ]
        odgovor = self.client.get(reverse("hr:work_time_sheet"), {"month": 5, "year": 2026})
        forma = odgovor.context["header_form"]
        self.assertEqual(odgovor.context["topli_obrok_predlog"], 2)
        self.assertEqual(forma["meal_days"].value(), 2)
        self.assertEqual(forma["meal_organizational_unit"].value(), self.unit.pk)
        self.assertContains(odgovor, "Dana sa kucanjem: 2")
        # upisana vrednost se ne menja predlogom
        WorkTimeSheet.objects.filter(pk=self.sheet.pk).update(meal_days=0)
        self.assertEqual(self.client.get(reverse("hr:work_time_sheet"), {"month": 5, "year": 2026})
                         .context["header_form"]["meal_days"].value(), 0)

    def test_datum_na_stampi_je_prvi_radni_dan_meseca_predaje(self):
        self.assertEqual(prvi_radni_dan_predaje(2026, 5), datetime.date(2026, 6, 1))
        self.assertEqual(prvi_radni_dan_predaje(2026, 12), datetime.date(2027, 1, 4))  # 1–2.1. praznik, 3.1. nedelja
        self.assertEqual(prvi_radni_dan_predaje(2026, 2), datetime.date(2026, 3, 2))  # 1.3. nedelja
        self.assertEqual(prvi_radni_dan_predaje(2026, 10), datetime.date(2026, 11, 2))  # 1.11. nedelja
        odgovor = self.client.get(reverse("hr:work_time_sheet_print", args=[self.sheet.pk]))
        self.assertContains(odgovor, '<div class="signature-value">01.06.2026.</div>')

    def test_prilozi_dodavanje_otvaranje_i_brisanje(self):
        adresa = reverse("hr:work_time_sheet")
        odgovor = self.client.post(adresa, {"month": "5", "year": "2026", "action": "prilog_dodaj", "vrsta": "propusnice",
                                            "napomena": "maj", "fajl": [SimpleUploadedFile("propusnice.pdf", b"%PDF-1.4 a"),
                                                                        SimpleUploadedFile("lista.jpg", b"jpg")]})
        self.assertRedirects(odgovor, f"{adresa}?month=5&year=2026#prilozi-radne-liste", fetch_redirect_response=False)
        self.assertEqual(self.sheet.prilozi.count(), 2)
        prilog = self.sheet.prilozi.get(naziv="propusnice.pdf")
        self.assertEqual((prilog.vrsta, prilog.napomena, prilog.velicina), ("propusnice", "maj", 10))
        strana = self.client.get(adresa, {"month": 5, "year": 2026})
        self.assertContains(strana, "Prilozi radne liste")
        url = reverse("hr:work_time_sheet_prilog", args=[self.sheet.pk, prilog.pk])
        self.assertContains(strana, url)
        self.assertEqual(b"".join(self.client.get(url).streaming_content), b"%PDF-1.4 a")
        # nedozvoljen tip fajla
        self.client.post(adresa, {"month": "5", "year": "2026", "action": "prilog_dodaj", "vrsta": "ostalo",
                                  "fajl": SimpleUploadedFile("virus.exe", b"MZ")})
        self.assertEqual(self.sheet.prilozi.count(), 2)
        # drugi zaposleni ne vidi prilog
        drugi = Employee.objects.create(employee_code=502, first_name="Ana", last_name="Anic", position="x",
                                        department_code=1, gender="Z", date_of_birth=datetime.date(1990, 1, 1),
                                        date_of_joining=datetime.date(2020, 1, 1))
        self.client.force_login(get_user_model().objects.create_user("drugi", password="x", employee=drugi))
        self.assertEqual(self.client.get(url).status_code, 403)
        # odobrena lista: prilog se ne briše
        self.client.force_login(self.user)
        WorkTimeSheet.objects.filter(pk=self.sheet.pk).update(status=WorkTimeSheet.Status.APPROVED)
        self.client.post(adresa, {"month": "5", "year": "2026", "action": "prilog_obrisi", "prilog": prilog.pk})
        self.assertTrue(RadnaListaPrilog.objects.filter(pk=prilog.pk).exists())
        WorkTimeSheet.objects.filter(pk=self.sheet.pk).update(status=WorkTimeSheet.Status.SUBMITTED)
        self.client.post(adresa, {"month": "5", "year": "2026", "action": "prilog_obrisi", "prilog": prilog.pk})
        self.assertFalse(RadnaListaPrilog.objects.filter(pk=prilog.pk).exists())
