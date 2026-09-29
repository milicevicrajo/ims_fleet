"""Opomene za gorivo: pravila, vozač (putni nalog pa zaduženje), priprema i slanje."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import PermissionCode, Role
from fleet.models import OpomenaGoriva, OrganizationalUnit, PutniNalog, TransactionNIS, VehicleTravelOrder
from fleet.support import opomene
from fleet.test_vehicle_onboarding import card, vehicle
from hr.models import Employee

DANAS = timezone.localdate()
BROJ = iter(range(1, 10_000))


def zaposleni(sifra, prezime):
    return Employee.objects.create(employee_code=sifra, first_name="Ime", last_name=prezime, position="Vozac",
                                   department_code=1, gender="M", date_of_birth=datetime.date(1980, 1, 1),
                                   date_of_joining=datetime.date(2020, 1, 1))


def tocenje(vozilo, dana_pre, km, **izmene):
    dan = DANAS - datetime.timedelta(days=dana_pre)
    vreme = timezone.make_aware(datetime.datetime(dan.year, dan.month, dan.day, 9, 0))
    broj = next(BROJ)
    podaci = dict(kupac="IMS", sifra_kupca="1", broj_kartice="123", kompanijski_kod_kupca="217", zemlja_sipanja="SR",
                  benzinska_stanica="LAPOVO JUG", id_transakcije=str(broj), app_kod="APP", datum_transakcije=vreme,
                  tociono_mesto="1", registarska_oznaka_vozila="BG123-AA", broj_racuna=str(broj), kilometraza=km,
                  sipanje_van_rezervoara=False, naziv_proizvoda="EVRO DIZEL", kolicina=Decimal("40.00"),
                  popust=Decimal("0"), primenjen_popust="", cena_sa_kase=Decimal("200"), cena=Decimal("200"),
                  total_sa_kase=Decimal("8000"), total=Decimal("8000"), valuta="RSD", aktivirano_prekoracenje=False,
                  kolicinsko_prekoracenje=False, finansijsko_prekoracenje=False, nacin_ocitavanja_kartice="manual",
                  vehicle=vozilo)
    podaci.update(izmene)
    return TransactionNIS.objects.create(**podaci)


class OpomeneTests(TestCase):
    def setUp(self):
        self.vozilo = vehicle("8")
        card(self.vozilo, plate="BG123-AA")
        self.putnik, self.zaduzio = zaposleni(71, "Putnik"), zaposleni(72, "Zaduzio")
        VehicleTravelOrder.objects.create(employee=self.zaduzio, vehicle=self.vozilo, start_mileage=100000,
                                          created_at=DANAS - datetime.timedelta(days=60))

    def test_pravila_i_vozac_iz_zaduzenja(self):
        tocenje(self.vozilo, 20, 100500)                     # van prozora, sluzi kao prethodno
        tocenje(self.vozilo, 10, 0)                          # kilometraza nije uneta
        tocenje(self.vozilo, 9, 101000)                      # ispravno
        tocenje(self.vozilo, 8, 100900)                      # manja od prethodnog
        tocenje(self.vozilo, 7, 101400)                      # ispravno (poredi se sa 101000, ne sa pogresnim)
        tocenje(self.vozilo, 6, 190000)                      # nerealan skok
        tocenje(self.vozilo, 5, 101400)                      # ista kao prethodno ispravno, drugog dana
        tocenje(self.vozilo, 4, 0, sipanje_van_rezervoara=True)  # kanister — preskace se
        rezultat = opomene.otkrij()
        self.assertEqual((rezultat["nove"], rezultat["bez_km"], rezultat["manja"], rezultat["skok"], rezultat["ista"]), (4, 1, 1, 1, 1))
        manja = OpomenaGoriva.objects.get(vrsta="manja")
        self.assertEqual((manja.uneta_km, manja.prethodna_km, manja.employee, manja.status), (100900, 101000, self.zaduzio, "za_slanje"))
        self.assertIn("zaduženje vozila", manja.vozac_izvor)
        self.assertIn("BG123-AA", manja.poruka)
        self.assertIn("manja od prethodnog točenja (101.000 km", manja.poruka)
        self.assertEqual(opomene.otkrij()["nove"], 0)  # ista tocenja se ne opominju dvaput

    def test_putni_nalog_ima_prednost_a_bez_vozaca_status(self):
        sifra = OrganizationalUnit.objects.create(code="410001", name="A", center="41")
        PutniNalog.objects.create(order_number="PN/2026-9", employee=self.putnik, vehicle=self.vozilo, job_code=sifra,
                                  order_date=DANAS - datetime.timedelta(days=4), travel_date=DANAS - datetime.timedelta(days=3),
                                  number_of_days=2, travel_location="Niš", task="Teren", advance_payment=Decimal("0"))
        tocenje(self.vozilo, 3, 0)
        opomene.otkrij()
        o = OpomenaGoriva.objects.get()
        self.assertEqual(o.employee, self.putnik)
        self.assertIn("putni nalog PN/2026-9", o.vozac_izvor)
        drugo = vehicle("9")
        tocenje(drugo, 2, 0)
        opomene.otkrij()
        self.assertEqual(OpomenaGoriva.objects.get(vehicle=drugo).status, "bez_vozaca")

    @override_settings(OPOMENE_GORIVA={"kanal": ""})
    def test_bez_kanala_nista_se_ne_salje(self):
        tocenje(self.vozilo, 2, 0)
        opomene.otkrij()
        self.assertEqual(opomene.posalji(), (0, 0))
        self.assertEqual(OpomenaGoriva.objects.get().status, "za_slanje")
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(OPOMENE_GORIVA={"kanal": "email"})
    def test_email_jedna_zbirna_poruka_po_vozacu(self):
        get_user_model().objects.create_user("vozac-z", password="x", email="vozac@example.rs", employee=self.zaduzio)
        tocenje(self.vozilo, 3, 0)
        tocenje(self.vozilo, 2, 0)
        opomene.otkrij()
        self.assertEqual(opomene.posalji(), (2, 0))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["vozac@example.rs"])
        self.assertEqual(mail.outbox[0].body.count("kilometraža nije uneta"), 2)
        self.assertEqual(set(OpomenaGoriva.objects.values_list("status", "kanal")), {("poslata", "email")})

    def test_ekran_i_proveri_sada(self):
        uloga = Role.objects.create(name="Garaza test", slug="garaza-opomene")
        for kod in ("opomena_list", "opomena_proveri"):
            uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        korisnik = get_user_model().objects.create_user("garaza-o", password="x")
        korisnik.roles.add(uloga)
        self.client.force_login(korisnik)
        tocenje(self.vozilo, 2, 0)
        odgovor = self.client.post(reverse("opomena_proveri"), follow=True)
        self.assertContains(odgovor, "Opomene za gorivo: novih 1")
        self.assertContains(odgovor, "Slanje opomena još nije uključeno")
        self.assertContains(odgovor, "kilometraža nije uneta")
        self.assertContains(self.client.get(reverse("opomena_list"), {"vrsta": "manja"}), "Nema opomena za izabrane filtere")

    def test_opomene_su_u_ostalo_a_ne_u_meniju(self):
        self.client.force_login(get_user_model().objects.create_superuser("ostalo-o", password="x"))
        ostalo = self.client.get(reverse("fleet_other"))
        self.assertContains(ostalo, reverse("opomena_list"))
        self.assertNotContains(self.client.get(reverse("vehicle_list")), 'class="hide-menu">Opomene za gorivo')
