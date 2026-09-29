"""Kadrovi → Ugovori: sinhronizacija iz v_hr_RadStaz, zabelezena OJ i radno mesto, unos i dokument."""
import datetime
import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import PermissionCode, Role
from hr.models import Employee, UgovoriSinhronizacija, UgovorZaposlenog
from hr.services import ugovori
from hr.test_registar import NA_REGISTRU, radnik
from organizacija.models import DodelaUloge
from organizacija.services.importer import run_import
from organizacija.test_prava import centar, uloga_sa_dozvolom
from organizacija.tests import ImportTestCase

DANAS = datetime.date(2026, 9, 29)


def period(sifra=701, rb=1, od=datetime.datetime(2024, 3, 1), do=datetime.datetime(3000, 1, 1),
           kategorija="Radni odnos", opis="                    "):
    return (kategorija, Decimal(sifra), rb, od, do, opis, 2, 6, 28)


def radnik_izvora(sifra=701, oj=413, sif_sis=Decimal("40"), aktivan="D", preduzece=1):
    return (Decimal(sifra), preduzece, "OSOBA   TEST        ", aktivan, oj, sif_sis)


def izvor(periodi=None, radnici=None, oj=None, sistematizacija=None):
    return (periodi if periodi is not None else [period()],
            radnici if radnici is not None else [radnik_izvora()],
            oj if oj is not None else [(1, "2025", 413, "Stari naziv       "), (1, "2026", 413, "Laboratorija za beton  "),
                                       (1, "3000", 413, "Probni naziv"), (1, "2026", 414, "Druga laboratorija")],
            sistematizacija if sistematizacija is not None else [(1, "40", "KV RADNIK II"), (2, "40", "Drugo preduzece"),
                                                                 (1, "41", "VKV RADNIK")])


class SinhronizacijaTests(TestCase):
    def setUp(self):
        self.zaposleni = Employee.objects.create(employee_code=701, first_name="Test", last_name="Osoba", department_code=1,
                                                 date_of_birth=datetime.date(1990, 1, 1), date_of_joining=datetime.date(2020, 1, 1))

    def sync(self, **kwargs):
        return ugovori.sinhronizuj(izvor=izvor(**kwargs), danas=DANAS)

    def test_novi_period_belezi_trenutnu_oj_i_radno_mesto(self):
        rezultat = self.sync()
        self.assertEqual((rezultat["ukupno"], rezultat["novih"], rezultat["bez_zaposlenog"]), (1, 1, 0))
        red = UgovorZaposlenog.objects.get()
        self.assertEqual(red.employee, self.zaposleni)
        self.assertEqual((red.oj, red.naziv_oj), ("413", "Laboratorija za beton"))  # tekuca godina, ne 3000
        self.assertEqual((red.sifra_sistematizacije, red.naziv_radnog_mesta), ("40", "KV RADNIK II"))  # po preduzecu
        self.assertEqual((red.podaci_poreklo, red.podaci_zabelezeni), (UgovorZaposlenog.Poreklo.SINHRONIZACIJA, DANAS))
        self.assertTrue(red.na_neodredjeno)
        self.assertIsNone(red.datum_do)
        self.assertEqual((red.staz, red.ime_prezime, red.opis), ("2 g 6 m 28 d", "OSOBA TEST", ""))
        self.assertTrue(red.radnik_aktivan)
        self.assertEqual(UgovoriSinhronizacija.objects.get().counts["novih"], 1)

    def test_istorija_ostaje_kada_radnik_promeni_oj(self):
        self.sync()
        rezultat = self.sync(periodi=[period(), period(rb=2, od=datetime.datetime(2026, 9, 1))],
                             radnici=[radnik_izvora(oj=414, sif_sis=Decimal("41"))])
        self.assertEqual((rezultat["novih"], rezultat["azurirano"]), (1, 0))
        stari, novi = UgovorZaposlenog.objects.order_by("redni_broj")
        self.assertEqual((stari.oj, stari.sifra_sistematizacije), ("413", "40"))  # zabelezeno ranije — ne menja se
        self.assertEqual((novi.oj, novi.naziv_oj, novi.naziv_radnog_mesta), ("414", "Druga laboratorija", "VKV RADNIK"))

    def test_uneti_podaci_ostaju_a_promena_perioda_se_oznacava(self):
        self.sync()
        red = UgovorZaposlenog.objects.get()
        red.broj_ugovora, red.napomena = "01-123/2024", "potpisan"
        red.save()
        self.sync(periodi=[period(od=datetime.datetime(2024, 3, 4), do=datetime.datetime(2025, 3, 3))])
        red.refresh_from_db()
        self.assertEqual((red.broj_ugovora, red.napomena), ("01-123/2024", "potpisan"))
        self.assertEqual((red.datum_od, red.datum_do, red.na_neodredjeno), (datetime.date(2024, 3, 4), datetime.date(2025, 3, 3), False))
        self.assertEqual(red.prethodni_datum_od, datetime.date(2024, 3, 1))

    def test_nestali_period_se_ne_brise(self):
        self.sync(periodi=[period(), period(rb=2)])
        rezultat = self.sync(periodi=[period()])
        self.assertEqual(rezultat["nema_u_izvoru"], 1)
        self.assertEqual(UgovorZaposlenog.objects.count(), 2)
        self.assertFalse(UgovorZaposlenog.objects.get(redni_broj=2).u_izvoru)
        self.assertEqual(self.sync(periodi=[period()])["azurirano"], 0)  # bez promena — bez upisa

    def test_prazan_izvor_ne_menja_nista(self):
        self.sync()
        with self.assertRaises(ugovori.PrazanIzvor):
            self.sync(periodi=[])
        self.assertTrue(UgovorZaposlenog.objects.get().u_izvoru)

    def test_van_radnog_odnosa_i_radnik_bez_kartice(self):
        rezultat = self.sync(periodi=[period(sifra=900, kategorija="Van radnog odnosa")],
                             radnici=[radnik_izvora(sifra=900, preduzece=2, aktivan="N")])
        red = UgovorZaposlenog.objects.get()
        self.assertEqual((red.kategorija, red.employee, rezultat["bez_zaposlenog"]),
                         (UgovorZaposlenog.Kategorija.VAN_RADNOG_ODNOSA, None, 1))
        self.assertEqual(red.naziv_radnog_mesta, "Drugo preduzece")
        self.assertFalse(red.radnik_aktivan)

    def test_nocni_posao_je_u_rasporedu(self):
        from core.management.commands.sync_celery_periodic_tasks import EXPECTED_PERIODIC_TASKS

        zadatak = next(s for s in EXPECTED_PERIODIC_TASKS if s["task"] == "hr.tasks.sync_ugovori_zaposlenih_task")
        self.assertEqual((zadatak["hour"], zadatak["minute"]), ("1", "15"))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="hr-ugovori-"))
class EkraniTests(TestCase):
    KODOVI = ("hr:ugovor_list", "hr:ugovor_data", "hr:ugovor_detail", "hr:ugovor_update", "hr:ugovor_dokument", "hr:ugovor_sync")

    @classmethod
    def tearDownClass(cls):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        Employee.objects.create(employee_code=701, first_name="Test", last_name="Osoba", department_code=1,
                                date_of_birth=datetime.date(1990, 1, 1), date_of_joining=datetime.date(2020, 1, 1))
        ugovori.sinhronizuj(izvor=izvor(periodi=[period(), period(rb=2, od=datetime.datetime(2025, 3, 1))]), danas=DANAS)
        self.glavni, self.aneks = UgovorZaposlenog.objects.order_by("redni_broj")
        self.uloga = Role.objects.create(name="Kadrovi test", slug="kadrovi-test")
        for kod in self.KODOVI:
            self.uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        self.korisnik = get_user_model().objects.create_user("kadrovi-ugovori", password="x")
        self.korisnik.roles.add(self.uloga)
        self.client.force_login(self.korisnik)

    def izmena(self, red, **podaci):
        return self.client.post(reverse("hr:ugovor_update", args=[red.pk]), {"akcija": "sacuvaj", **{
            "broj_ugovora": "", "broj_aneksa": "", "glavni_ugovor": "", "napomena": "",
            "oj": red.oj, "naziv_oj": red.naziv_oj, "sifra_sistematizacije": red.sifra_sistematizacije,
            "naziv_radnog_mesta": red.naziv_radnog_mesta, **podaci}})

    def test_spisak_i_podaci(self):
        odgovor = self.client.get(reverse("hr:ugovor_list"))
        self.assertContains(odgovor, "Ugovori zaposlenih")
        self.assertContains(odgovor, "Osveži iz kadrovske baze")
        podaci = self.client.get(reverse("hr:ugovor_data"), {"draw": 1, "start": 0, "length": 10}).json()
        self.assertEqual((podaci["recordsTotal"], podaci["recordsFiltered"]), (2, 2))
        self.assertIn("Laboratorija za beton", podaci["data"][0]["oj"])
        self.assertIn("Nije uneto", podaci["data"][0]["broj_ugovora"])
        nije = self.client.get(reverse("hr:ugovor_data"), {"draw": 1, "unos": "uneto"}).json()
        self.assertEqual(nije["recordsFiltered"], 0)
        self.assertEqual(self.client.get(reverse("hr:ugovor_data"), {"radnici": "bivsi"}).json()["recordsFiltered"], 0)

    def test_unos_ugovora_aneksa_i_dokumenta(self):
        self.assertEqual(self.izmena(self.glavni, broj_ugovora="01-10/2024").status_code, 302)
        dokument = SimpleUploadedFile("aneks.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        odgovor = self.izmena(self.aneks, broj_ugovora="01-10/2024", broj_aneksa="1", glavni_ugovor=self.glavni.pk,
                              dokument=dokument)
        self.assertEqual(odgovor.status_code, 302)
        self.aneks.refresh_from_db()
        self.assertEqual((self.aneks.broj_aneksa, self.aneks.glavni_ugovor, self.aneks.dokument_naziv), ("1", self.glavni, "aneks.pdf"))
        self.assertEqual(self.aneks.izmenio, self.korisnik)
        preuzimanje = self.client.get(reverse("hr:ugovor_dokument", args=[self.aneks.pk]))
        self.assertEqual(preuzimanje.status_code, 200)
        self.assertEqual(b"".join(preuzimanje.streaming_content), b"%PDF-1.4 test")
        detalj = self.client.get(reverse("hr:ugovor_detail", args=[self.glavni.pk]))
        self.assertContains(detalj, "Aneksi ovog ugovora")
        # bez broja aneksa nema ni veze sa glavnim ugovorom
        self.izmena(self.aneks, broj_ugovora="01-10/2024", glavni_ugovor=self.glavni.pk)
        self.aneks.refresh_from_db()
        self.assertIsNone(self.aneks.glavni_ugovor)
        self.assertTrue(self.aneks.dokument)  # dokument ostaje dok se ne ukloni

    def test_glavni_ugovor_se_bira_samo_od_ranijih_perioda(self):
        from hr.ugovori_views import UgovorForm

        self.assertEqual(list(UgovorForm(instance=self.aneks).fields["glavni_ugovor"].queryset), [self.glavni])
        self.assertEqual(list(UgovorForm(instance=self.glavni).fields["glavni_ugovor"].queryset), [])

    def test_rucna_izmena_oj_se_belezi_a_los_fajl_odbija(self):
        self.izmena(self.glavni, broj_ugovora="5", oj="999", naziv_oj="Ispravljeno")
        self.glavni.refresh_from_db()
        self.assertEqual((self.glavni.oj, self.glavni.podaci_poreklo), ("999", UgovorZaposlenog.Poreklo.RUCNO))
        los = SimpleUploadedFile("ugovor.exe", b"MZ", content_type="application/octet-stream")
        odgovor = self.izmena(self.glavni, broj_ugovora="5", dokument=los)
        self.assertEqual(odgovor.status_code, 400)
        self.assertContains(odgovor, "Dozvoljeni su PDF", status_code=400)
        self.assertContains(self.izmena(self.glavni), "Unesite broj ugovora.", status_code=400)  # broj ugovora

    def test_potvrda_promenjenog_perioda(self):
        UgovorZaposlenog.objects.filter(pk=self.glavni.pk).update(prethodni_datum_od=datetime.date(2024, 2, 1))
        self.assertContains(self.client.get(reverse("hr:ugovor_detail", args=[self.glavni.pk])), "promenio se u kadrovskoj bazi")
        self.client.post(reverse("hr:ugovor_update", args=[self.glavni.pk]), {"akcija": "potvrdi_period"})
        self.glavni.refresh_from_db()
        self.assertIsNone(self.glavni.prethodni_datum_od)

    def test_bez_dozvole_za_izmenu_samo_pregled(self):
        self.uloga.permissions.remove(PermissionCode.objects.get(code="hr:ugovor_update"))
        odgovor = self.client.get(reverse("hr:ugovor_detail", args=[self.glavni.pk]))
        self.assertEqual(odgovor.status_code, 200)
        self.assertNotContains(odgovor, 'name="broj_ugovora"')
        self.assertEqual(self.izmena(self.glavni, broj_ugovora="X").status_code, 403)

    def test_rucna_sinhronizacija_i_nedostupan_izvor(self):
        from unittest import mock

        from django.db import DatabaseError

        with mock.patch.object(ugovori, "procitaj_izvor", return_value=izvor()):
            odgovor = self.client.post(reverse("hr:ugovor_sync"), follow=True)
        self.assertContains(odgovor, "Sinhronizacija završena")
        self.assertEqual(UgovoriSinhronizacija.objects.first().created_by, self.korisnik)
        with mock.patch.object(ugovori, "procitaj_izvor", side_effect=DatabaseError("nema veze")):
            odgovor = self.client.post(reverse("hr:ugovor_sync"), follow=True)
        self.assertContains(odgovor, "nije dostupna")


@NA_REGISTRU
class ObuhvatTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        radnik(1, "431")
        radnik(3, "41")
        ugovori.sinhronizuj(danas=DANAS, izvor=izvor(periodi=[period(sifra=1), period(sifra=3), period(sifra=900)],
                                                     radnici=[radnik_izvora(sifra=1), radnik_izvora(sifra=3), radnik_izvora(sifra=900)]))
        self.uloga = uloga_sa_dozvolom("kadrovi-ugovori", "hr:ugovor_list", "hr:ugovor_data")
        self.korisnik = get_user_model().objects.create_user("kadrovi-centra", password="x")
        self.korisnik.roles.add(self.uloga)
        self.client.force_login(self.korisnik)

    def vidi(self):
        podaci = self.client.get(reverse("hr:ugovor_data"), {"draw": 1}).json()
        return podaci["recordsTotal"]

    def test_obuhvat_centra_i_cela_firma(self):
        self.assertEqual(self.vidi(), 0)  # bez dodele — nista
        dodela = DodelaUloge.objects.create(korisnik=self.korisnik, uloga=self.uloga, vazi_od=datetime.date(2026, 1, 1),
                                            status=DodelaUloge.STATUS_AKTIVNA, cvor_id=centar("43"))
        self.assertEqual(self.vidi(), 1)  # samo radnik iz centra 43; bez kartice zaposlenog — ne
        dodela.cvor_id, dodela.cela_firma = None, True
        dodela.save()
        self.assertEqual(self.vidi(), 3)  # cela firma vidi i periode bez kartice zaposlenog
