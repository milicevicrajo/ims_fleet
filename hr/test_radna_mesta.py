"""Više radnih mesta zaposlenog iz kadrovske baze (od 07.10.2026.)."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import PermissionCode, Role

from .models import Employee
from .services.radna_mesta import osvezi_radna_mesta, radna_mesta

SISTEMAT = [(1, Decimal("22"), "GLAVNI DIPLOMIRANI INZENJER   "), (1, Decimal("471"), "TEHN.EKSPERT ZA PREDMET ISPITIVANJA"),
            (1, Decimal("4301"), "Ovlasceno lice za vrednovanje"), (1, Decimal("434"), "Laborant")]
OJ = [(1, 2026, 414, "Laboratorija za beton"), (1, 2025, 432, "Stari naziv"), (1, 2026, 432, "Sertifikacija")]


class RadnaMestaTests(TestCase):
    def test_do_pet_radnih_mesta_redom_iz_izvora(self):
        redovi = [
            # sif_pred, rasif, oj, sif_sis, oj1, sif_sis1, oj2, sif_sis2, oj3, sif_sis3, oj4, sif_sis4
            (1, Decimal("205"), 414, Decimal("22"), 432, Decimal("471.00"), 0, Decimal("4301"), 0, Decimal("434"), 0, Decimal("0")),
            (1, Decimal("206"), 414, Decimal("22"), 0, Decimal("0.00"), 0, None, 0, Decimal("0"), 0, Decimal("0")),
            (1, Decimal("207"), 414, Decimal("22"), 0, Decimal("22.00"), 0, None, 0, None, 0, None),  # ponovljeno
        ]
        mesta = radna_mesta(redovi, OJ, SISTEMAT, danas=datetime.date(2026, 10, 7))
        self.assertEqual(mesta[(1, 205)], [
            {"sifra": "22", "naziv": "GLAVNI DIPLOMIRANI INZENJER", "oj": "414", "naziv_oj": "Laboratorija za beton"},
            {"sifra": "471", "naziv": "TEHN.EKSPERT ZA PREDMET ISPITIVANJA", "oj": "432", "naziv_oj": "Sertifikacija"},
            {"sifra": "4301", "naziv": "Ovlasceno lice za vrednovanje", "oj": "414", "naziv_oj": "Laboratorija za beton"},
            {"sifra": "434", "naziv": "Laborant", "oj": "414", "naziv_oj": "Laboratorija za beton"},
        ])  # radno mesto bez svoje OJ dobija OJ iz `oj`
        self.assertEqual(len(mesta[(1, 206)]), 1)
        self.assertEqual(len(mesta[(1, 207)]), 1)

    def test_rukovodece_mesto_je_poslednje_radno_mesto(self):
        redovi = [  # Verica Laninović: jedno radno mesto i rukovodeće mesto 201
            (1, Decimal("222"), 417, Decimal("22"), 0, Decimal("0.00"), 0, Decimal("0"), 0, Decimal("0"), 0, Decimal("0"), 201),
            (1, Decimal("223"), 414, Decimal("20"), 0, Decimal("0"), 0, None, 0, None, 0, None, 20),  # isti naziv — ne ponavlja se
            (1, Decimal("224"), 414, Decimal("22"), 0, Decimal("0"), 0, None, 0, None, 0, None, 0),
        ]
        sistemat = SISTEMAT + [(1, Decimal("20"), "RUKOVODILAC LABORATORIJE")]
        rukovodeca = [(1, 201, "Rukovodilac u laboratoriji   "), (1, 20, "Rukovodilac laboratorije")]
        mesta = radna_mesta(redovi, OJ, sistemat, danas=datetime.date(2026, 10, 7), rukovodeca=rukovodeca)
        self.assertEqual([(m["sifra"], m["naziv"], m.get("rukovodece", False)) for m in mesta[(1, 222)]],
                         [("22", "GLAVNI DIPLOMIRANI INZENJER", False), ("201", "Rukovodilac u laboratoriji", True)])
        self.assertEqual(mesta[(1, 222)][1]["oj"], "417")
        self.assertEqual(len(mesta[(1, 223)]), 1)
        self.assertEqual(len(mesta[(1, 224)]), 1)

    def test_upis_i_prikaz(self):
        employee = Employee.objects.create(
            employee_code=205, first_name="Ljiljana", last_name="Milicic", position="GLAVNI DIPLOMIRANI INZENJER",
            department_code=1, gender="F", date_of_birth=datetime.date(1980, 1, 1), date_of_joining=datetime.date(2010, 1, 1))
        redovi = [(1, Decimal("205"), 414, Decimal("22"), 432, Decimal("471"), 0, Decimal("4301"), 0, Decimal("0"), 0, Decimal("0"))]
        po_radniku = radna_mesta(redovi, OJ, SISTEMAT, danas=datetime.date(2026, 10, 7))
        self.assertEqual(osvezi_radna_mesta(po_radniku), 1)
        self.assertEqual(osvezi_radna_mesta(po_radniku), 0)  # bez promene se ne upisuje
        employee.refresh_from_db()
        self.assertEqual([m["sifra"] for m in employee.radna_mesta], ["22", "471", "4301"])

        korisnik = get_user_model().objects.create_user("kadrovi-rm", password="x")
        uloga = Role.objects.create(name="Kadrovi RM", slug="kadrovi-rm")
        for kod in ("employee_detail", "employee_list"):
            uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        korisnik.roles.add(uloga)
        self.client.force_login(korisnik)
        detalj = self.client.get(reverse("employee_detail", args=[employee.pk]))
        self.assertContains(detalj, "Radna mesta (3):")
        self.assertContains(detalj, "TEHN.EKSPERT ZA PREDMET ISPITIVANJA")
        self.assertContains(detalj, "OJ 432 Sertifikacija")
        self.assertNotContains(detalj, "glavno")
        self.assertContains(detalj, "1. GLAVNI DIPLOMIRANI INZENJER; 2. TEHN.EKSPERT ZA PREDMET ISPITIVANJA; 3. Ovlasceno lice za vrednovanje")
        spisak = self.client.get(reverse("employee_list"))
        self.assertContains(spisak, "1. GLAVNI DIPLOMIRANI INZENJER")
        self.assertContains(spisak, "3. Ovlasceno lice za vrednovanje")
