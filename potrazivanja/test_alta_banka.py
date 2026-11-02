"""Kupci sa računima u Alta banci (od 02.11.2026.): čitanje NBS strane, čuvanje snimka i ekran."""
import json
import tempfile
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from core.models import PermissionCode, Role
from .models import KupacAltaBanka
from .services import alta_banka

STRANA_NBS = """<table><tr><th>Naziv</th></tr>
<tr><td>KUPAC DOO</td><td>17511068</td><td>103079096</td><td>ULICA 1</td><td>BEOGRAD</td><td>Beograd</td><td>Gradnja</td>
<td>ALTA BANKA A.D. BEOGRAD</td><td></td><td>190-0000000011200-46</td><td></td><td>Uključen</td><td>Podleže blokadi</td><td>5.7.2013.</td></tr>
<tr><td>KUPAC DOO</td><td>17511068</td><td>103079096</td><td>ULICA 1</td><td>BEOGRAD</td><td>Beograd</td><td>Gradnja</td>
<td>OTP Banka Srbija a.d. Novi Sad</td><td></td><td>325-9500600043776-60</td><td></td><td>Uključen</td><td>Podleže blokadi</td><td>8.11.2011.</td></tr>
</table>"""


def kupac(sif_par=12124, broj_uplata=3, **izmene):
    podaci = {"sif_par": sif_par, "naziv": "KUPAC DOO", "mb": "17511068", "pib": "103079096", "broj_uplata": broj_uplata,
              "iznos_uplata": Decimal("1500.00") if broj_uplata else Decimal("0"), "prva_uplata": date(2024, 7, 17),
              "poslednja_uplata": date(2026, 9, 30), "racuni_uplata": "190-0000000011200-46" if broj_uplata else ""}
    podaci.update(izmene)
    return podaci


class SnimakTests(TestCase):
    def test_strana_nbs_daje_racune(self):
        racuni = alta_banka.citaj_stranu(STRANA_NBS)
        self.assertEqual([r["racun"] for r in racuni], ["190-0000000011200-46", "325-9500600043776-60"])
        self.assertEqual((racuni[0]["banka"], racuni[0]["blokada"], racuni[0]["datum_otvaranja"]),
                         ("ALTA BANKA A.D. BEOGRAD", "Podleže blokadi", "5.7.2013."))

    def test_cuvaju_se_platioci_i_kupci_sa_racunom_u_alta_banci(self):
        racuni = alta_banka.citaj_stranu(STRANA_NBS)
        zapis = alta_banka.sacuvaj(kupac(), racuni, "sve_banke")
        self.assertEqual([(r.racun, r.banka_sifra, r.datum_otvaranja) for r in zapis.racuni.all()],
                         [("190-0000000011200-46", "190", date(2013, 7, 5)), ("325-9500600043776-60", "325", date(2011, 11, 8))])
        self.assertIsNone(alta_banka.sacuvaj(kupac(2, broj_uplata=0), [], "alta"))  # nije platio, nema račun u Alta
        self.assertIsNotNone(alta_banka.sacuvaj(kupac(3, broj_uplata=0), racuni[:1], "alta"))
        self.assertEqual(KupacAltaBanka.objects.count(), 2)

    def test_greska_nbs_ne_brise_raniji_snimak(self):
        alta_banka.sacuvaj(kupac(), alta_banka.citaj_stranu(STRANA_NBS), "sve_banke")
        zapis = alta_banka.sacuvaj(kupac(), [], "sve_banke", greska="NBS ne odgovara.")
        self.assertEqual(zapis.racuni.count(), 2)
        self.assertEqual(zapis.nbs_greska, "NBS ne odgovara.")

    def test_uvoz_iz_snimljenog_fajla(self):
        with tempfile.TemporaryDirectory() as direktorijum:
            fajl = Path(direktorijum) / "nbs.jsonl"
            fajl.write_text(json.dumps({"sif_par": 12124, "obuhvat": "sve_banke",
                                        "racuni": alta_banka.citaj_stranu(STRANA_NBS)}) + "\n", encoding="utf-8")
            with patch.object(alta_banka, "kupci_iz_izvoda", return_value=[kupac(), kupac(7, broj_uplata=2), kupac(8, broj_uplata=0)]):
                self.assertEqual(alta_banka.preuzmi(fajl=fajl, javi=lambda _: None), 2)
        self.assertEqual(KupacAltaBanka.objects.get(partner_code=12124).racuni.count(), 2)
        self.assertEqual(KupacAltaBanka.objects.get(partner_code=7).nbs_greska, "Nije pretražen u NBS.")


class EkranTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("alta-reader", password="x")
        self.role = Role.objects.create(name="Alta test", slug="alta-test")
        self.user.roles.add(self.role)
        self.client.force_login(self.user)
        alta_banka.sacuvaj(kupac(), alta_banka.citaj_stranu(STRANA_NBS), "sve_banke")
        alta_banka.sacuvaj(kupac(3, broj_uplata=0, naziv="SAMO RAČUN DOO"), alta_banka.citaj_stranu(STRANA_NBS)[:1], "alta")

    def grant(self, *codes):
        for code in codes:
            self.role.permissions.add(PermissionCode.objects.get_or_create(code=f"potrazivanja:{code}")[0])

    def test_trazi_dozvolu(self):
        url = reverse("potrazivanja:alta_banka")
        self.grant("dashboard", "view_all")
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_spisak_i_excel(self):
        self.grant("dashboard", "view_all", "alta_banka")
        url = reverse("potrazivanja:alta_banka")
        odgovor = self.client.get(url)
        self.assertContains(odgovor, "KUPAC DOO")
        self.assertContains(odgovor, "325-9500600043776-60")
        self.assertNotContains(odgovor, "SAMO RAČUN DOO")
        self.assertContains(self.client.get(url, {"prikaz": "racun"}), "SAMO RAČUN DOO")
        odgovor = self.client.get(url, {"prikaz": "svi", "izvoz": "xlsx"})
        knjiga = load_workbook(BytesIO(odgovor.content))
        self.assertEqual(knjiga.sheetnames, ["Kupci", "Računi (NBS)"])
        self.assertEqual(knjiga["Računi (NBS)"].max_row, 4)  # zaglavlje + 2 + 1
