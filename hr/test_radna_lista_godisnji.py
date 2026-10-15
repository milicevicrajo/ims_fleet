"""Godišnji odmor na radnoj listi (15.10.2026.): ukupno, iskorišćeno, preostalo i upozorenje kad se upiše više."""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import OrganizationalUnit
from hr.models import (AnnualLeaveAllowance, AnnualLeaveDecision, RecipientType, WorkTimeCategory, WorkTimeElement,
                       WorkTimeSheet, WorkTimeSheetLine)
from hr.services import radna_lista as pravila
from hr.test_obracun_csv import radnik


def dodela(zaposleni, godina, dana):
    return AnnualLeaveAllowance.objects.create(year=godina, employee_code=zaposleni.employee_code, employee=zaposleni,
                                               last_seen_at=timezone.now(), allocated_days=dana)


def resenje(zaposleni, godina, od, do, dana):
    return AnnualLeaveDecision.objects.create(year=godina, employee_code=zaposleni.employee_code, employee=zaposleni,
                                              last_seen_at=timezone.now(), source_start_key=od.isoformat(),
                                              start_date=od, end_date=do, approved_days=dana)


class GodisnjiOdmorNaRadnojListiTests(TestCase):
    def setUp(self):
        primalac = RecipientType.objects.create(code="01", name="Zaposleno lice")
        self.redovan = WorkTimeCategory.objects.create(code="redovan_rad", name="Redovan rad")
        self.go = WorkTimeCategory.objects.create(code="godisnji_odmor", name="Godišnji odmor")
        for elsif, vrsta in ((1, self.redovan), (181, self.go)):
            WorkTimeElement.objects.create(recipient_type=primalac, category=vrsta, payroll_code=elsif, payroll_name=vrsta.code)
        self.sifra = OrganizationalUnit.objects.create(code="436222", name="Strucni nadzor", center="43")
        self.zaposleni = radnik(849)

    def lista(self, zaposleni, mesec=9, dana_go=5):
        """Septembar 2026: 22 radna dana — prvih `dana_go` je godišnji odmor, ostalo redovan rad (fond 176 h je pun)."""
        radni = [d for d in range(1, 31) if datetime.date(2026, mesec, d).weekday() < 5]
        lista = WorkTimeSheet.objects.create(employee=zaposleni, year=2026, month=mesec, meal_days=0,
                                             status=WorkTimeSheet.Status.SUBMITTED)
        WorkTimeSheetLine.objects.create(sheet=lista, line_number=1, organizational_unit=self.sifra, work_category=self.go,
                                         **{f"day_{d}": 8 for d in radni[:dana_go]})
        WorkTimeSheetLine.objects.create(sheet=lista, line_number=2, organizational_unit=self.sifra, work_category=self.redovan,
                                         **{f"day_{d}": 8 for d in radni[dana_go:]})
        return lista

    def test_stanje_bez_resenja_za_mesec_liste_i_prenos_do_juna(self):
        dodela(self.zaposleni, 2025, 25)
        dodela(self.zaposleni, 2026, 20)
        resenje(self.zaposleni, 2025, datetime.date(2025, 7, 1), datetime.date(2025, 7, 28), 20)  # iz 2025 ostaje 5
        resenje(self.zaposleni, 2026, datetime.date(2026, 3, 2), datetime.date(2026, 3, 13), 10)
        resenje(self.zaposleni, 2026, datetime.date(2026, 9, 1), datetime.date(2026, 9, 7), 5)  # u mesecu liste — iz liste
        septembar = pravila.stanja_godisnjeg([self.zaposleni.pk], 2026, 9)[self.zaposleni.pk]
        self.assertEqual((septembar["ukupno"], septembar["prenos"], septembar["po_resenjima"], septembar["dostupno"]),
                         (20, 0, 10, 10))  # posle juna nema prenosa iz 2025
        jun = pravila.stanja_godisnjeg([self.zaposleni.pk], 2026, 6)[self.zaposleni.pk]
        self.assertEqual((jun["ukupno"], jun["prenos"], jun["po_resenjima"], jun["dostupno"]), (25, 5, 15, 10))

        stanje = pravila.godisnji_odmor_liste(self.lista(self.zaposleni))
        self.assertEqual((stanje["u_listi"], stanje["iskorisceno"], stanje["preostalo"], stanje["upozorenje"]),
                         (5, 15, 5, None))

    def test_upozorenje_kad_je_upisano_vise_nego_sto_je_preostalo(self):
        dodela(self.zaposleni, 2026, 20)
        resenje(self.zaposleni, 2026, datetime.date(2026, 3, 2), datetime.date(2026, 3, 30), 17)
        stanje = pravila.godisnji_odmor_liste(self.lista(self.zaposleni))
        self.assertEqual((stanje["preostalo"], stanje["upozorenje"]),
                         (-2, "upisano 5 dana godišnjeg odmora, a preostalo je 3"))
        bez_dodele = radnik(850)
        stanje = pravila.godisnji_odmor_liste(self.lista(bez_dodele))
        self.assertFalse(stanje["ima_dodelu"])
        self.assertIn("nema dodele odmora za 2026", stanje["upozorenje"])
        self.assertIsNone(pravila.godisnji_odmor_liste(self.lista(radnik(851), dana_go=0))["upozorenje"])

    def test_pregled_i_radna_lista_prikazuju_upozorenje_ali_odobravanje_ostaje(self):
        dodela(self.zaposleni, 2026, 20)
        resenje(self.zaposleni, 2026, datetime.date(2026, 3, 2), datetime.date(2026, 3, 30), 17)
        lista = self.lista(self.zaposleni)
        korisnik = get_user_model().objects.create_superuser("kadrovi-go", password="x")
        self.client.force_login(korisnik)

        strana = self.client.get(reverse("hr:radne_liste"), {"year": 2026, "month": 9, "status": "sve"})
        red = {r["zaposleni"].employee_code: r for r in strana.context["redovi"]}[849]
        self.assertEqual(red["problemi"], [])
        self.assertContains(strana, "rl-red-upozorenje")
        self.assertContains(strana, "upisano 5 dana godišnjeg odmora, a preostalo je 3")
        self.assertContains(strana, reverse("hr:work_time_sheet_odobri", args=[lista.pk]))  # upozorenje ne blokira

        strana = self.client.get(reverse("hr:employee_work_time_sheet", args=[self.zaposleni.pk]), {"year": 2026, "month": 9})
        self.assertEqual(strana.context["godisnji"]["preostalo"], -2)
        self.assertContains(strana, 'id="go-panel"')
        self.assertContains(strana, "go-panel is-over")
        self.assertContains(strana, "Upisano je više dana godišnjeg odmora nego što je preostalo.")
        self.assertContains(strana, 'data-dostupno="3"')

        self.client.post(reverse("hr:work_time_sheet_odobri", args=[lista.pk]))
        lista.refresh_from_db()
        self.assertEqual(lista.status, WorkTimeSheet.Status.APPROVED)
