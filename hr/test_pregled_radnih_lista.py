"""Kadrovi → Pregled radnih lista (09.10.2026.): prethodni mesec, kontrola, odobravanje, vraćanje, uloga Radne liste."""
import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import OrganizationalUnit, PermissionCode, Role
from hr.models import RecipientType, WorkTimeCategory, WorkTimeElement, WorkTimeSheet, WorkTimeSheetLine
from hr.radne_liste_views import prethodni_mesec
from hr.test_obracun_csv import radnik

# Septembar 2026: 22 radna dana → fond 176 sati.
PUN_SEPTEMBAR = [d for d in range(1, 31) if datetime.date(2026, 9, d).weekday() < 5]


class PregledRadnihListaTests(TestCase):
    def setUp(self):
        primalac = RecipientType.objects.create(code="01", name="Zaposleno lice")
        self.redovan = WorkTimeCategory.objects.create(code="redovan_rad", name="Redovan rad")
        WorkTimeElement.objects.create(recipient_type=primalac, category=self.redovan, payroll_code=1, payroll_name="Redovan")
        self.sifra = OrganizationalUnit.objects.create(code="436222", name="Strucni nadzor", center="43")
        self.ok = radnik(849)
        self.los = radnik(850)
        self.bez = radnik(851)  # nema radnu listu
        self.lista_ok = self.lista(self.ok, PUN_SEPTEMBAR, self.redovan)
        self.lista_los = self.lista(self.los, PUN_SEPTEMBAR[:3], None)  # 24 h, bez vrste
        korisnik = get_user_model().objects.create_user("snezana", password="x")
        from core.permissions import sync_radne_liste_role
        korisnik.roles.add(sync_radne_liste_role())
        self.client.force_login(korisnik)

    def lista(self, zaposleni, dani, vrsta):
        lista = WorkTimeSheet.objects.create(employee=zaposleni, year=2026, month=9, meal_days=0,
                                             status=WorkTimeSheet.Status.SUBMITTED)
        WorkTimeSheetLine.objects.create(sheet=lista, line_number=1, organizational_unit=self.sifra, work_category=vrsta,
                                         **{f"day_{d}": 8 for d in dani})
        return lista

    def test_podrazumevano_prethodni_mesec(self):
        self.assertEqual(prethodni_mesec(datetime.date(2026, 10, 9)), (2026, 9))
        self.assertEqual(prethodni_mesec(datetime.date(2027, 1, 5)), (2026, 12))
        with patch("hr.radne_liste_views.timezone.localdate", return_value=datetime.date(2026, 10, 9)):
            strana = self.client.get(reverse("hr:radne_liste"))
        self.assertEqual((strana.context["godina"], strana.context["mesec"], strana.context["br_obr"]), (2026, 9, 3))
        redovi = {r["zaposleni"].employee_code: r for r in strana.context["redovi"]}
        self.assertEqual(redovi[849]["problemi"], [])
        self.assertEqual((redovi[849]["sati"], redovi[849]["fond"]), (176, 176))
        self.assertTrue(any("fond meseca je 176" in p for p in redovi[850]["problemi"]))
        self.assertTrue(any("izaberite vrstu" in p for p in redovi[850]["problemi"]))
        self.assertEqual(redovi[851]["status"], "nema")
        self.assertContains(strana, reverse("hr:work_time_sheets_csv") + "?year=2026&amp;month=9&amp;br_obr=3")
        self.assertContains(strana, "<h1>", count=1)  # jedan naslov — hero
        # CSV se samo preuzima — bez loadera stranice
        self.assertContains(strana, 'data-no-preloader download href="' + reverse("hr:work_time_sheets_csv"))
        self.assertContains(strana, 'data-no-preloader download href="' + reverse("hr:work_time_sheet_csv", args=[self.lista_ok.pk]))
        pretraga = self.client.get(reverse("hr:radne_liste"), {"year": 2026, "month": 9, "q": "850"})
        self.assertEqual([r["zaposleni"].employee_code for r in pretraga.context["redovi"]], [850])
        self.assertContains(strana, reverse("hr:work_time_sheet_odobri", args=[self.lista_ok.pk]))
        self.assertNotContains(strana, reverse("hr:work_time_sheet_odobri", args=[self.lista_los.pk]))

    def test_odobravanje_vracanje_i_zakljucavanje(self):
        self.client.post(reverse("hr:work_time_sheet_odobri", args=[self.lista_los.pk]))
        self.lista_los.refresh_from_db()
        self.assertEqual(self.lista_los.status, WorkTimeSheet.Status.SUBMITTED)  # ima greške — ne odobrava se
        self.client.post(reverse("hr:work_time_sheet_odobri", args=[self.lista_ok.pk]))
        self.lista_ok.refresh_from_db()
        self.assertEqual(self.lista_ok.status, WorkTimeSheet.Status.APPROVED)
        self.assertIsNotNone(self.lista_ok.odobreno_at)
        # odobrena lista se ne menja ni na sopstvenoj radnoj listi
        zaposleni = get_user_model().objects.create_user("radnik849", password="x", employee=self.ok)
        self.client.force_login(zaposleni)
        odgovor = self.client.post(reverse("hr:work_time_sheet"), {"month": "9", "year": "2026", "action": "save"})
        self.assertRedirects(odgovor, reverse("hr:work_time_sheet") + "?month=9&year=2026", fetch_redirect_response=False)
        self.lista_ok.refresh_from_db()
        self.assertEqual(self.lista_ok.status, WorkTimeSheet.Status.APPROVED)
        self.assertEqual(self.client.post(reverse("hr:work_time_sheet_vrati", args=[self.lista_ok.pk])).status_code, 403)
        # uloga Radne liste vraća u pripremu
        self.client.force_login(get_user_model().objects.get(username="snezana"))
        self.client.post(reverse("hr:work_time_sheet_vrati", args=[self.lista_ok.pk]))
        self.lista_ok.refresh_from_db()
        self.assertEqual((self.lista_ok.status, self.lista_ok.odobrio_id), (WorkTimeSheet.Status.DRAFT, None))

    def test_uloga_ima_ekran_i_csv_u_meniju(self):
        from core.permissions import RADNE_LISTE_CODES

        uloga = Role.objects.get(slug="radne-liste")
        self.assertEqual(set(uloga.permissions.values_list("code", flat=True)), set(RADNE_LISTE_CODES))
        strana = self.client.get(reverse("hr:radne_liste"), {"year": 2026, "month": 9})
        self.assertContains(strana, "Pregled radnih lista")
        csv = self.client.get(reverse("hr:work_time_sheets_csv"), {"year": 2026, "month": 9, "br_obr": 3})
        self.assertIn("1;2026;9;3;849;1;176;436222", csv.content.decode("utf-8-sig"))
        bez = get_user_model().objects.create_user("bez", password="x")
        self.client.force_login(bez)
        self.assertEqual(self.client.get(reverse("hr:radne_liste")).status_code, 403)
        self.assertFalse(PermissionCode.objects.filter(code="hr:radne_liste", roles__users=bez).exists())
