"""CSV za učitavanje obračuna zarada iz radne liste (09.10.2026.)."""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import OrganizationalUnit, PermissionCode, Role
from hr.models import Employee, RecipientType, WorkTimeCategory, WorkTimeElement, WorkTimeSheet, WorkTimeSheetLine
from hr.services import obracun_csv


def radnik(sifra, primalac="01"):
    return Employee.objects.create(employee_code=sifra, first_name="Ime", last_name=f"Prezime{sifra}", position="Inženjer",
                                   department_code=43, org_unit_code="436", gender="M", recipient_code=primalac,
                                   date_of_birth=datetime.date(1980, 1, 1), date_of_joining=datetime.date(2020, 1, 1))


class ObracunCsvTests(TestCase):
    def setUp(self):
        primalac = RecipientType.objects.create(code="01", name="Zaposleno lice")
        for oznaka, elsif in (("redovan_rad", 1), ("topli_obrok", 14), ("godisnji_odmor", 181)):
            vrsta = WorkTimeCategory.objects.create(code=oznaka, name=oznaka)
            WorkTimeElement.objects.create(recipient_type=primalac, category=vrsta, payroll_code=elsif, payroll_name=oznaka)
        self.nadzor = OrganizationalUnit.objects.create(code="436222", name="Strucni nadzor", center="43")
        self.drugi = OrganizationalUnit.objects.create(code="437111", name="Drugi posao", center="43")
        self.go = WorkTimeCategory.objects.get(code="godisnji_odmor")

    def lista(self, zaposleni, redovi, topli_obrok=None):
        lista = WorkTimeSheet.objects.create(employee=zaposleni, year=2026, month=8, meal_days=topli_obrok,
                                             meal_organizational_unit=self.nadzor if topli_obrok else None)
        for broj, (sifra, vrsta, dani) in enumerate(redovi, 1):
            WorkTimeSheetLine.objects.create(sheet=lista, line_number=broj, organizational_unit=sifra, work_category=vrsta,
                                             **{f"day_{d}": 8 for d in dani})
        return lista

    def test_primer_iz_avgusta(self):
        # Radnik 849, avgust 2026: 19 dana na 436222, 1 dan na 437111, 1 dan GO, topli obrok 20 dana.
        lista = self.lista(radnik(849), [(self.nadzor, None, range(1, 20)), (self.drugi, None, [20]),
                                         (self.nadzor, self.go, [21])], topli_obrok=20)
        redovi, upozorenja = obracun_csv.stavke(obracun_csv.listovi_meseca(Employee.objects.all(), 2026, 8), 3)
        self.assertEqual(redovi, [[1, 2026, 8, 3, 849, 1, 152, "436222"], [1, 2026, 8, 3, 849, 1, 8, "437111"],
                                  [1, 2026, 8, 3, 849, 14, 160, "436222"], [1, 2026, 8, 3, 849, 181, 8, "436222"]])
        self.assertEqual(upozorenja, [])

        korisnik = get_user_model().objects.create_user("kadrovi-csv", password="x")
        self.client.force_login(korisnik)
        url = reverse("hr:work_time_sheet_csv", args=[lista.pk])
        self.assertEqual(self.client.get(url, {"br_obr": 3}).status_code, 403)
        uloga = Role.objects.create(name="Kadrovi CSV", slug="kadrovi-csv")
        for kod in ("hr:work_time_sheet_csv", "hr:work_time_sheets_csv", "hr:employee_work_time_sheet"):
            uloga.permissions.add(PermissionCode.objects.create(code=kod))
        korisnik.roles.add(uloga)
        self.assertEqual(self.client.get(url).status_code, 400)  # broj obračuna je obavezan
        WorkTimeSheetLine.objects.create(sheet=lista, line_number=9, day_25=4)  # red bez šifre posla
        strana = self.client.get(reverse("hr:employee_work_time_sheet", args=[lista.employee_id]), {"year": 2026, "month": 8})
        self.assertContains(strana, "nema šifru posla")  # upozorenje na ekranu radne liste
        self.assertContains(strana, "CSV svi")
        self.assertIn("red 9 (4 h) nema šifru posla.", obracun_csv.stavke([lista], 3)[1][0])
        WorkTimeSheetLine.objects.filter(sheet=lista, line_number=9).delete()
        odgovor = self.client.get(url, {"br_obr": 3})
        self.assertEqual(odgovor["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("obracun_2026_08_obr3_849.csv", odgovor["Content-Disposition"])
        self.assertEqual(odgovor.content.decode("utf-8-sig").split("\r\n"), [
            "sif_pred;god;mesec;br_obr;rasif;elsif;sati;sif_pos", "1;2026;8;3;849;1;152;436222", "1;2026;8;3;849;1;8;437111",
            "1;2026;8;3;849;14;160;436222", "1;2026;8;3;849;181;8;436222", ""])

    def test_svi_radnici_za_mesec_i_upozorenja(self):
        self.lista(radnik(849), [(self.nadzor, None, [1, 2])])
        self.lista(radnik(850), [(self.drugi, None, [3])], topli_obrok=1)
        self.lista(radnik(900, primalac=""), [(self.nadzor, None, [4])])  # bez vrste primaoca
        korisnik = get_user_model().objects.create_user("kadrovi-svi", password="x")
        uloga = Role.objects.create(name="Kadrovi svi", slug="kadrovi-svi")
        uloga.permissions.add(PermissionCode.objects.create(code="hr:work_time_sheets_csv"))
        korisnik.roles.add(uloga)
        self.client.force_login(korisnik)
        odgovor = self.client.get(reverse("hr:work_time_sheets_csv"), {"year": 2026, "month": 8, "br_obr": 1})
        self.assertEqual(odgovor.content.decode("utf-8-sig").split("\r\n")[1:-1], [
            "1;2026;8;1;849;1;16;436222", "1;2026;8;1;850;1;8;437111", "1;2026;8;1;850;14;8;436222"])
        self.assertEqual(odgovor["X-Upozorenja"], "1")  # radnik 900 nema vrstu primaoca — nije u CSV-u
        self.assertEqual(self.client.get(reverse("hr:work_time_sheets_csv"), {"year": 2026, "month": 9, "br_obr": 1})
                         .content.decode("utf-8-sig").split("\r\n"), ["sif_pred;god;mesec;br_obr;rasif;elsif;sati;sif_pos", ""])
