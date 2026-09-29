"""Garaža: provera kilometraže, detalj sa dokumentima, delovi u obliku trebovanja i zahtev u Nabavci."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import PermissionCode, Role
from fleet.forms.garaza import KvarForm
from fleet.models import JobCode, Kvar, KvarPart, OrganizationalUnit, VehicleTravelOrder
from fleet.support.garaza import formiraj_zahtev, poslednja_kilometraza, proveri_kilometrazu
from fleet.test_vehicle_onboarding import card, vehicle
from hr.models import Employee
from nabavka.models import ProcurementCase

DANAS = timezone.localdate()


class KilometrazaTests(TestCase):
    def setUp(self):
        self.vozilo = vehicle("5")
        self.vozac = Employee.objects.create(employee_code=51, first_name="Ime", last_name="Vozac", position="Vozac",
                                             department_code=1, gender="M", date_of_birth=datetime.date(1980, 1, 1),
                                             date_of_joining=datetime.date(2020, 1, 1))
        VehicleTravelOrder.objects.create(employee=self.vozac, vehicle=self.vozilo, start_mileage=120000,
                                          created_at=DANAS - datetime.timedelta(days=10))

    def forma(self, km, **podaci):
        return KvarForm({"vehicle": self.vozilo.pk, "work_type": "popravka", "kilometraza": km, "opis": "Lampica motora",
                         "van_ims": "False", **podaci})

    def test_poslednja_kilometraza_iz_naloga_i_ranije_prijave(self):
        self.assertEqual(poslednja_kilometraza(self.vozilo)["value"], 120000)
        Kvar.objects.create(vehicle=self.vozilo, kilometraza=121500, opis="Ranije")
        poslednja = poslednja_kilometraza(self.vozilo)
        self.assertEqual((poslednja["value"], poslednja["date"]), (121500, DANAS))
        self.assertIn("prijava kvara", poslednja["source"])

    def test_manja_kilometraza_trazi_potvrdu(self):
        forma = self.forma(119000)
        self.assertFalse(forma.is_valid())
        self.assertIn("manja od poslednjeg poznatog očitavanja", forma.errors["kilometraza"][0])
        self.assertIn("120.000 km", forma.errors["kilometraza"][0])
        self.assertTrue(self.forma(119000, potvrda_kilometraze="on").is_valid())

    def test_prevelik_skok_trazi_potvrdu_a_realan_prolazi(self):
        self.assertTrue(self.forma(125000).is_valid())  # 5.000 km za 10 dana
        forma = self.forma(140000)  # 20.000 km za 10 dana
        self.assertFalse(forma.is_valid())
        self.assertIn("veća od poslednjeg poznatog očitavanja", forma.errors["kilometraza"][0])
        self.assertFalse(self.forma(0).is_valid())
        self.assertEqual(proveri_kilometrazu(self.vozilo, 120500), [])

    def test_izmena_bez_promene_kilometraze_se_ne_proverava_ponovo(self):
        kvar = Kvar.objects.create(vehicle=self.vozilo, kilometraza=90000, opis="Stara prijava sa greškom")
        forma = KvarForm({"vehicle": self.vozilo.pk, "work_type": "popravka", "kilometraza": 90000, "opis": "Ispravljen opis",
                          "van_ims": "False"}, instance=kvar)
        self.assertTrue(forma.is_valid(), forma.errors)


class GarazaEkraniTests(TestCase):
    KODOVI = ("kvar_list", "kvar_create", "kvar_update", "kvar_detail", "kvar_print", "kvar_workorder",
              "kvar_trebovanje", "kvar_stampa_sve", "kvar_zahtev", "kvar_kilometraza", "nabavka:case_detail")

    def setUp(self):
        self.vozilo = vehicle("6")
        card(self.vozilo, plate="BG555-GG")
        self.sifra = OrganizationalUnit.objects.create(code="410001", name="Laboratorija", center="41")
        JobCode.objects.create(vehicle=self.vozilo, organizational_unit=self.sifra, assigned_date=datetime.date(2026, 1, 1))
        self.uloga = Role.objects.create(name="Garaza test", slug="garaza-kvar-test")
        for kod in self.KODOVI:
            self.uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        self.korisnik = get_user_model().objects.create_user("garaza-kvar", password="x")
        self.korisnik.roles.add(self.uloga)
        self.client.force_login(self.korisnik)
        self.kvar = Kvar.objects.create(vehicle=self.vozilo, work_type="popravka", kilometraza=80000, opis="Kočnice škripe")

    def test_nova_prijava_vodi_na_detalj(self):
        odgovor = self.client.post(reverse("kvar_create"), {"vehicle": self.vozilo.pk, "work_type": "mali_servis",
                                                            "kilometraza": 80500, "opis": "Redovan servis", "van_ims": "False"})
        novi = Kvar.objects.exclude(pk=self.kvar.pk).get()
        self.assertRedirects(odgovor, reverse("kvar_detail", args=[novi.pk]), fetch_redirect_response=False)
        forma = self.client.get(reverse("kvar_create"))
        self.assertContains(forma, "Poslednja poznata kilometraža")
        podaci = self.client.get(reverse("kvar_kilometraza"), {"vozilo": self.vozilo.pk}).json()
        self.assertEqual((podaci["tablica"], podaci["kilometraza"]["km"]), ("BG555-GG", 80500))
        self.assertIn("410001", podaci["sifra_posla"])

    def test_detalj_prikazuje_tri_dokumenta_i_dokumenti_se_ugradjuju(self):
        odgovor = self.client.get(reverse("kvar_detail", args=[self.kvar.pk]))
        self.assertContains(odgovor, "Prijava kvara")
        self.assertContains(odgovor, "TREBOVANJE MATERIJALA BR.")
        self.assertContains(odgovor, "Radni nalog")
        self.assertContains(odgovor, f'{reverse("kvar_print", args=[self.kvar.pk])}?embed=1')
        self.assertContains(odgovor, "Formiraj zahtev u Nabavci")
        for ruta in ("kvar_print", "kvar_workorder", "kvar_trebovanje"):
            dokument = self.client.get(reverse(ruta, args=[self.kvar.pk]), {"embed": "1"})
            self.assertEqual(dokument.status_code, 200)
            self.assertEqual(dokument.headers["X-Frame-Options"], "SAMEORIGIN")
            self.assertContains(dokument, ".print-toolbar { display: none !important; }")

    def test_delovi_se_cuvaju_iz_tabele_trebovanja(self):
        postojeci = KvarPart.objects.create(kvar=self.kvar, name="Pločice", quantity=Decimal("4"), uom="kom")
        brisanje = KvarPart.objects.create(kvar=self.kvar, name="Pogrešno", quantity=Decimal("1"), uom="kom")
        odgovor = self.client.post(reverse("kvar_detail", args=[self.kvar.pk]), {
            "delovi-TOTAL_FORMS": "3", "delovi-INITIAL_FORMS": "2", "delovi-MIN_NUM_FORMS": "0", "delovi-MAX_NUM_FORMS": "1000",
            "delovi-0-id": postojeci.pk, "delovi-0-name": "Kočione pločice", "delovi-0-quantity": "4", "delovi-0-uom": "kom",
            "delovi-1-id": brisanje.pk, "delovi-1-name": "Pogrešno", "delovi-1-quantity": "1", "delovi-1-uom": "kom", "delovi-1-DELETE": "on",
            "delovi-2-name": "Kočiona tečnost", "delovi-2-quantity": "1.5", "delovi-2-uom": "l",
        })
        self.assertEqual(odgovor.status_code, 302)
        self.assertEqual(sorted(self.kvar.parts.values_list("name", "quantity", "uom")),
                         [("Kočiona tečnost", Decimal("1.50"), "l"), ("Kočione pločice", Decimal("4.00"), "kom")])

    def test_formiranje_zahteva_u_nabavci(self):
        KvarPart.objects.create(kvar=self.kvar, name="Kočione pločice", quantity=Decimal("4"), uom="kom")
        odgovor = self.client.post(reverse("kvar_zahtev", args=[self.kvar.pk]), follow=True)
        predmet = ProcurementCase.objects.get()
        self.assertEqual((predmet.case_type, predmet.status, predmet.is_garage), ("nabavka", "draft", True))
        self.assertEqual((predmet.vehicle, predmet.garage_order, predmet.job_code, predmet.work_type),
                         (self.vozilo, self.kvar, self.sifra, "popravka"))
        self.assertEqual(predmet.case_number, f"ZNG-41/{DANAS.year}-1")
        self.assertIn("BG555-GG", predmet.title)
        self.assertEqual(list(predmet.items.values_list("name", "quantity", "uom")), [("Kočione pločice", Decimal("4.00"), "kom")])
        self.assertEqual(predmet.status_logs.count(), 1)
        self.assertContains(odgovor, f"ZNG-41/{DANAS.year}-1")
        self.assertContains(odgovor, "Otvori u Nabavci")
        self.client.post(reverse("kvar_zahtev", args=[self.kvar.pk]))  # drugi put — isti zahtev
        self.assertEqual(ProcurementCase.objects.count(), 1)

    def test_van_imsa_je_zahtev_za_uslugu_a_bez_sifre_posla_nema_zahteva(self):
        self.kvar.van_ims = True
        self.kvar.save()
        predmet, nov = formiraj_zahtev(self.kvar, self.korisnik)
        self.assertTrue(nov)
        self.assertEqual((predmet.case_type, predmet.case_number[:4]), ("usluga", "ZUG-"))
        JobCode.objects.all().delete()
        drugi = Kvar.objects.create(vehicle=self.vozilo, kilometraza=80100, opis="Bez šifre")
        odgovor = self.client.post(reverse("kvar_zahtev", args=[drugi.pk]), follow=True)
        self.assertContains(odgovor, "nema šifru posla")
        self.assertEqual(ProcurementCase.objects.count(), 1)


class TrebovanjeIStampaTests(GarazaEkraniTests):
    def delovi(self, broj, od=1):
        KvarPart.objects.bulk_create([KvarPart(kvar=self.kvar, name=f"Deo {i}", quantity=1, uom="kom") for i in range(od, od + broj)])

    def test_lista_je_a4_sa_dve_iste_kopije_preko_12_delova_drugi_a4(self):
        self.delovi(12)
        odgovor = self.client.get(reverse("kvar_trebovanje", args=[self.kvar.pk]))
        self.assertContains(odgovor, 'class="a4-page dok-trebovanje"', count=1)
        self.assertContains(odgovor, "TREBOVANJE MATERIJALA BR.", count=2)  # dve iste kopije na A4
        self.delovi(1, od=13)
        odgovor = self.client.get(reverse("kvar_trebovanje", args=[self.kvar.pk]))
        self.assertContains(odgovor, 'class="a4-page dok-trebovanje"', count=2)
        self.assertContains(odgovor, "TREBOVANJE MATERIJALA BR.", count=4)
        self.assertContains(odgovor, "Lista 2 od 2", count=2)
        self.assertContains(odgovor, "Deo 13", count=2)

    def test_stampaj_sve(self):
        self.delovi(13)
        odgovor = self.client.get(reverse("kvar_stampa_sve", args=[self.kvar.pk]))
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, 'class="a4-page', count=4)  # prijava + 2 lista trebovanja + radni nalog
        self.assertContains(odgovor, "PRIJAVA KVARA VOZILA")
        self.assertContains(odgovor, "RADNI NALOG ZA POPRAVKU VOZILA")
        self.assertContains(odgovor, "break-after: page")
        self.assertContains(self.client.get(reverse("kvar_detail", args=[self.kvar.pk])), "Štampaj sve")

    def test_sifra_posla_od_vozila_i_bez_tekuce_dodele(self):
        JobCode.objects.all().delete()
        buduca = OrganizationalUnit.objects.create(code="420002", name="Buduca", center="42")
        JobCode.objects.create(vehicle=self.vozilo, organizational_unit=buduca, assigned_date=DANAS + datetime.timedelta(days=30))
        predmet, _ = formiraj_zahtev(self.kvar, self.korisnik)
        self.assertEqual((predmet.job_code, predmet.case_number), (buduca, f"ZNG-42/{DANAS.year}-1"))

    def test_bez_okvira_i_tacno_a4(self):
        for ruta in ("kvar_print", "kvar_workorder"):
            odgovor = self.client.get(reverse(ruta, args=[self.kvar.pk]))
            self.assertContains(odgovor, "width: 210mm; height: 296mm")
            self.assertNotContains(odgovor, "border:1px solid #000;            /* ukloni")
            self.assertContains(odgovor, 'class="a4-page', count=1)
