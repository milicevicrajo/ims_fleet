"""Faza 2 registra za Flotu: veza `org_node`, ponovljivo popunjavanje i uporedni izvestaj.

Brani tri pravila iz plana (dokumentacija/plan-registra-sifara-posla.md, pogl. 3):
staro polje je merodavno i ne menja se, veza se izvodi bez pogadjanja, a izvestaj
po centru mora da se poklopi starim putem i kroz registar.
"""

import datetime
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import OrganizationalUnit, PermissionCode, Role, RolePermission
from finansije.models import FinanceJob, LedgerEntry
from fleet.models import FuelConsumption, JobCode, Lease, ProcurementRequest, PutniNalog, VehicleTravelOrder
from fleet.test_vehicle_onboarding import vehicle
from hr.models import Employee
from organizacija.models import ExternalOrgMapping, OrgNode, OrgNodeVersion
from organizacija.services import flota
from organizacija.services.importer import run_import
from organizacija.tests import ImportTestCase


def cvor(sifra):
    return ExternalOrgMapping.objects.get(
        source=ExternalOrgMapping.SOURCE_FINANCE_JOB, source_key=sifra, valid_to__isnull=True
    ).node_id


class FlotaTestCase(ImportTestCase):
    def setUp(self):
        super().setUp()
        self.nadzor = OrganizationalUnit.objects.create(code="430111", name="Strucni nadzor", center="43")
        self.materijali = OrganizationalUnit.objects.create(code="410001", name="Amortizacija", center="41")
        self.test_centar = OrganizationalUnit.objects.create(code="960001", name="Test centar", center="96")
        self.car = vehicle()

    def putni_nalog(self, jedinica, broj="01/2026-1"):
        return PutniNalog.objects.create(
            order_number=broj, job_code=jedinica, travel_location="Beograd", task="Test",
            travel_date=datetime.date(2026, 7, 10), number_of_days=1, advance_payment=Decimal("1000.00"),
        )

    def gorivo(self, sifra, dan=datetime.date(2026, 3, 5), iznos="1000", car=None):
        return FuelConsumption.objects.create(
            vehicle=car or self.car, job_code=sifra, supplier="NIS", fuel_type="dizel", mileage=1000,
            date=timezone.make_aware(datetime.datetime.combine(dan, datetime.time(8, 0))),
            amount=Decimal("40"), cost_bruto=Decimal(iznos), cost_neto=Decimal(iznos),
        )

    def lizing(self, sifra):
        return Lease.objects.create(
            vehicle=self.car, partner_code="1", partner_name="Lizing", job_code=sifra, contract_number="L1",
            current_payment_amount=Decimal("500"), start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2028, 1, 1),
        )


class VezaPriCuvanjuTests(FlotaTestCase):
    """Novi i izmenjeni zapisi dobijaju vezu pri cuvanju; staro polje odlucuje."""

    def setUp(self):
        super().setUp()
        run_import(company=1)

    def test_fk_modeli_dobijaju_cvor_jedinice(self):
        dodela = JobCode.objects.create(vehicle=self.car, organizational_unit=self.nadzor,
                                        assigned_date=datetime.date(2026, 1, 1))
        nalog = self.putni_nalog(self.nadzor)
        vozac = Employee.objects.create(employee_code=9101, first_name="Test", last_name="Vozac", position="Vozac",
                                        department_code=1, gender="M", date_of_birth=datetime.date(1980, 1, 1),
                                        date_of_joining=datetime.date(2020, 1, 1))
        nalog_vozila = VehicleTravelOrder.objects.create(vehicle=self.car, employee=vozac, job_code=self.materijali,
                                                         created_at=datetime.date(2026, 2, 1))
        gzn = ProcurementRequest.objects.create(job_code=self.nadzor)
        self.assertEqual(dodela.org_node_id, cvor("430111"))
        self.assertEqual(nalog.org_node_id, cvor("430111"))
        self.assertEqual(nalog_vozila.org_node_id, cvor("410001"))
        self.assertEqual(ProcurementRequest.objects.get(pk=gzn.pk).org_node_id, cvor("430111"))

    def test_tekstualna_sifra_ide_po_tacnoj_sifri_bez_rubnih_razmaka(self):
        self.assertEqual(self.gorivo(" 430111 ").org_node_id, cvor("430111"))
        self.assertEqual(self.lizing("410001").org_node_id, cvor("410001"))

    def test_bez_para_ostaje_prazno_i_nista_se_ne_pogadja_po_prefiksu(self):
        self.assertIsNone(self.putni_nalog(self.test_centar).org_node_id)
        self.assertIsNone(self.gorivo("430999").org_node_id)
        self.assertIsNone(self.gorivo("", dan=datetime.date(2026, 3, 7)).org_node_id)
        self.assertIsNone(self.gorivo(None, dan=datetime.date(2026, 3, 6)).org_node_id)

    def test_izmena_starog_polja_menja_vezu_a_rucni_upis_se_prepisuje(self):
        nalog = self.putni_nalog(self.nadzor)
        nalog.job_code = self.materijali
        nalog.save()
        self.assertEqual(nalog.org_node_id, cvor("410001"))
        nalog.org_node_id = cvor("430111")
        nalog.save()
        self.assertEqual(PutniNalog.objects.get(pk=nalog.pk).org_node_id, cvor("410001"))

    def test_jedinica_napravljena_posle_uvoza_se_razresava_po_sifri(self):
        nova = OrganizationalUnit.objects.create(code="431112", name="Terenske lab.", center="43")
        self.assertEqual(self.putni_nalog(nova).org_node_id, cvor("431112"))

    def test_cuvanje_drugih_polja_ne_dira_vezu(self):
        nalog = self.putni_nalog(self.nadzor)
        PutniNalog.objects.filter(pk=nalog.pk).update(org_node=None)
        nalog.refresh_from_db()
        nalog.isplaceno = Decimal("100")
        nalog.save(update_fields=["isplaceno"])
        self.assertIsNone(PutniNalog.objects.get(pk=nalog.pk).org_node_id)


class PopunjavanjeTests(FlotaTestCase):
    """Zapisi napravljeni pre uvoza registra dobijaju vezu komandom, u paketima."""

    def setUp(self):
        super().setUp()
        # Registar jos ne postoji, pa signal ostavlja vezu praznu — kao zatecni podaci.
        self.dodela = JobCode.objects.create(vehicle=self.car, organizational_unit=self.nadzor,
                                             assigned_date=datetime.date(2026, 1, 1))
        self.nalozi = [self.putni_nalog(self.nadzor, broj=f"01/2026-{n}") for n in range(1, 6)]
        self.bez_para = self.putni_nalog(self.test_centar, broj="01/2026-9")
        self.goriva = [self.gorivo("430111", dan=datetime.date(2026, 3, d)) for d in range(1, 4)]
        self.gorivo("vranj", dan=datetime.date(2026, 3, 9))
        run_import(company=1)

    def zbir(self, zbirovi, kljuc):
        return next(z for z in zbirovi if z["kljuc"] == kljuc)

    def test_proba_ne_upisuje(self):
        zbirovi = flota.povezi(proba=True)
        self.assertEqual(self.zbir(zbirovi, "putni_nalozi")["postavljeno"], 5)
        self.assertFalse(PutniNalog.objects.filter(org_node__isnull=False).exists())

    def test_popunjava_u_paketima_i_ponovljeno_ne_menja_nista(self):
        zbirovi = flota.povezi(batch_size=2)
        nalozi = self.zbir(zbirovi, "putni_nalozi")
        self.assertEqual((nalozi["ukupno"], nalozi["postavljeno"], nalozi["nerazreseno"]), (6, 5, 1))
        self.assertEqual(nalozi["nerazresene_sifre"], [("960001", 1)])
        gorivo = self.zbir(zbirovi, "gorivo")
        self.assertEqual((gorivo["postavljeno"], gorivo["nerazreseno"]), (3, 1))
        self.assertEqual(set(PutniNalog.objects.exclude(pk=self.bez_para.pk).values_list("org_node_id", flat=True)),
                         {cvor("430111")})

        drugi = flota.povezi()
        self.assertEqual(sum(z["postavljeno"] + z["promenjeno"] + z["ocisceno"] for z in drugi), 0)
        self.assertEqual(self.zbir(drugi, "putni_nalozi")["vec_povezano"], 5)

    def test_masovna_izmena_starog_polja_se_ispravlja_popunjavanjem(self):
        flota.povezi()
        PutniNalog.objects.filter(pk=self.nalozi[0].pk).update(job_code=self.materijali)
        PutniNalog.objects.filter(pk=self.nalozi[1].pk).update(job_code=self.test_centar)
        zbir = self.zbir(flota.povezi(), "putni_nalozi")
        self.assertEqual((zbir["promenjeno"], zbir["ocisceno"]), (1, 1))
        self.assertEqual(PutniNalog.objects.get(pk=self.nalozi[0].pk).org_node_id, cvor("410001"))
        self.assertIsNone(PutniNalog.objects.get(pk=self.nalozi[1].pk).org_node_id)

    def test_popunjavanje_ne_dira_stara_polja(self):
        pre = (
            sorted(PutniNalog.objects.values_list("pk", "job_code_id", "order_number", "isplaceno")),
            sorted(JobCode.objects.values_list("pk", "organizational_unit_id", "assigned_date")),
            sorted(FuelConsumption.objects.values_list("pk", "job_code", "cost_bruto")),
            sorted(OrganizationalUnit.objects.values_list("pk", "code", "center")),
        )
        flota.povezi()
        posle = (
            sorted(PutniNalog.objects.values_list("pk", "job_code_id", "order_number", "isplaceno")),
            sorted(JobCode.objects.values_list("pk", "organizational_unit_id", "assigned_date")),
            sorted(FuelConsumption.objects.values_list("pk", "job_code", "cost_bruto")),
            sorted(OrganizationalUnit.objects.values_list("pk", "code", "center")),
        )
        self.assertEqual(pre, posle)

    def test_komanda_proba_i_izvestaj(self):
        izlaz = StringIO()
        call_command("povezi_flotu", "--proba", "--izvestaj", stdout=izlaz)
        tekst = izlaz.getvalue()
        self.assertIn("PROBA", tekst)
        self.assertIn("Uporedni izvestaj", tekst)
        self.assertFalse(PutniNalog.objects.filter(org_node__isnull=False).exists())

        call_command("povezi_flotu", "--model", "putni_nalozi", stdout=StringIO())
        self.assertEqual(PutniNalog.objects.filter(org_node__isnull=False).count(), 5)
        self.assertFalse(FuelConsumption.objects.filter(org_node__isnull=False).exists())


class UporedniIzvestajTests(FlotaTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.nadzor, assigned_date=datetime.date(2026, 1, 1))
        JobCode.objects.create(vehicle=self.car, organizational_unit=self.materijali,
                               assigned_date=datetime.date(2026, 6, 1))
        self.putni_nalog(self.nadzor)
        self.gorivo("430111", dan=datetime.date(2026, 3, 1), iznos="1000")
        self.gorivo("430111", dan=datetime.date(2026, 7, 1), iznos="250.50")

    def deo(self, izvestaj, kljuc):
        return next(d for d in izvestaj["delovi"] if d["kljuc"] == kljuc)

    def test_poklapa_se_kada_je_centar_jedinice_isti_kao_u_registru(self):
        izvestaj = flota.uporedni_izvestaj()
        self.assertTrue(izvestaj["prolazi"], [(d["kljuc"], d["primeri"]) for d in izvestaj["delovi"]])
        po_vozilu = self.deo(izvestaj, "gorivo_po_vozilu")
        iznosi = {r["centar"]: (r["staro_iznos"], r["novo_iznos"]) for r in po_vozilu["redovi"]}
        # Tocenje u martu ide na dodelu 43, u julu na dodelu 41 — isto starim putem i kroz registar.
        self.assertEqual(iznosi, {"43": (Decimal("1000"), Decimal("1000")), "41": (Decimal("250.50"), Decimal("250.50"))})

    def test_pogresan_centar_u_staroj_jedinici_obara_izvestaj(self):
        OrganizationalUnit.objects.filter(pk=self.nadzor.pk).update(center="41")
        izvestaj = flota.uporedni_izvestaj()
        self.assertFalse(izvestaj["prolazi"])
        nalozi = self.deo(izvestaj, "putni_nalozi")
        self.assertEqual(nalozi["razlika_zapisa"], 1)
        self.assertEqual(nalozi["primeri"][0]["sifra"], "430111")
        self.assertEqual((nalozi["primeri"][0]["staro"], nalozi["primeri"][0]["novo"]), ("41", "43"))

    def test_nepovezan_zapis_obara_izvestaj(self):
        PutniNalog.objects.update(org_node=None)
        nalozi = self.deo(flota.uporedni_izvestaj(), "putni_nalozi")
        self.assertFalse(nalozi["prolazi"])
        self.assertEqual({r["centar"] for r in nalozi["redovi"]}, {"43", flota.NEPOVEZANO})

    def test_sifra_goriva_koju_zna_samo_registar_je_dopuna_a_ne_razlika(self):
        self.gorivo("431112", dan=datetime.date(2026, 3, 2))
        gorivo = self.deo(flota.uporedni_izvestaj(), "gorivo")
        self.assertTrue(gorivo["prolazi"])
        self.assertEqual(gorivo["dopuna"], 1)

    def test_godina_ogranicava_izvestaj(self):
        self.gorivo("430111", dan=datetime.date(2025, 3, 1))
        izvestaj = flota.uporedni_izvestaj(godina=2025)
        self.assertEqual(self.deo(izvestaj, "gorivo")["ukupno"], 1)
        self.assertEqual(flota.godine_goriva(), [2026, 2025])


class EkranTests(FlotaTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        self.putni_nalog(self.nadzor)
        User = get_user_model()
        self.admin = User.objects.create_superuser("flota-admin", "a@example.com", "x")
        self.obican = User.objects.create_user("flota-obican", "o@example.com", "x")

    def test_superuser_vidi_izvestaj(self):
        self.client.force_login(self.admin)
        odgovor = self.client.get(reverse("organizacija:flota"))
        self.assertEqual(odgovor.status_code, 200)
        self.assertContains(odgovor, "Uporedni izveštaj prolazi")
        self.assertContains(odgovor, "Putni nalozi")
        self.assertContains(odgovor, reverse("organizacija:flota"))
        self.assertEqual(self.client.get(reverse("organizacija:flota"), {"godina": "abc"}).status_code, 200)

    def test_bez_dozvole_nema_ni_ekrana_ni_linka(self):
        self.client.force_login(self.obican)
        self.assertEqual(self.client.get(reverse("organizacija:flota")).status_code, 403)
        stablo = self.client.get(reverse("organizacija:stablo"))
        self.assertNotContains(stablo, reverse("organizacija:flota"))

    def test_uloga_sa_dozvolom_vidi_ekran(self):
        uloga = Role.objects.create(name="Kontrola registra", slug="kontrola-registra")
        dozvola, _ = PermissionCode.objects.get_or_create(code="organizacija:flota", defaults={"label": "x"})
        RolePermission.objects.create(role=uloga, permission=dozvola)
        self.obican.roles.add(uloga)
        self.client.force_login(self.obican)
        self.assertEqual(self.client.get(reverse("organizacija:flota")).status_code, 200)

    def test_ekran_nista_ne_upisuje(self):
        PutniNalog.objects.update(org_node=None)
        self.client.force_login(self.admin)
        self.client.get(reverse("organizacija:flota"))
        self.assertFalse(PutniNalog.objects.filter(org_node__isnull=False).exists())


class ParalelnaSinhronizacijaTests(FlotaTestCase):
    """Nova sinhronizacija radi pored stare: osvezava registar, povezuje i poredi, staru ne dira."""

    def setUp(self):
        super().setUp()
        from organizacija.services import sync

        self.sync = sync
        run_import(company=1)

    def test_nova_sifra_iz_izvora_dobija_cvor_i_zapisi_se_povezuju(self):
        from finansije.models import FinanceJob

        # Stara sinhronizacija je vec donela novu OJ, a nalog je nastao pre nego sto registar zna za nju.
        FinanceJob.objects.create(company=1, code="431113", center="43", name="Nova laboratorija", active=True, profit_type="P")
        nova = OrganizationalUnit.objects.create(code="431113", name="Nova laboratorija", center="43")
        nalog = self.putni_nalog(nova)
        self.assertIsNone(nalog.org_node_id)

        rezultat = self.sync.sinhronizuj()
        self.assertEqual(rezultat["run"].nodes_created, 1)
        self.assertEqual(PutniNalog.objects.get(pk=nalog.pk).org_node_id, cvor("431113"))
        self.assertEqual(rezultat["kontrola"]["povezano"], 3)

    def test_ponovljena_sinhronizacija_ne_pravi_nista_novo(self):
        self.sync.sinhronizuj()
        drugi = self.sync.sinhronizuj()
        self.assertEqual((drugi["run"].nodes_created, drugi["run"].versions_created), (0, 0))
        self.assertEqual(sum(z["postavljeno"] + z["promenjeno"] + z["ocisceno"] for z in drugi["veze"]), 0)

    def test_stara_organizacija_i_sifarnik_ostaju_netaknuti(self):
        from finansije.models import FinanceJob

        pre = (sorted(OrganizationalUnit.objects.values_list("pk", "code", "name", "center")),
               sorted(FinanceJob.objects.values_list("code", "name", "center", "active")))
        self.sync.sinhronizuj()
        posle = (sorted(OrganizationalUnit.objects.values_list("pk", "code", "name", "center")),
                 sorted(FinanceJob.objects.values_list("code", "name", "center", "active")))
        self.assertEqual(pre, posle)

    def test_poredjenje_jedinica_stare_i_nove(self):
        OrganizationalUnit.objects.create(code="111111", name="Nepoznato", center="3")
        OrganizationalUnit.objects.filter(pk=self.materijali.pk).update(center="4")
        kontrola = self.sync.uporedi_jedinice()
        self.assertEqual(kontrola["jedinica"], 4)
        self.assertEqual(kontrola["povezano"], 2)
        self.assertEqual(kontrola["isti_centar"], 1)
        self.assertEqual(kontrola["razlika_centra"], [{"sifra": "410001", "staro": "4", "novo": "41"}])
        self.assertEqual(kontrola["van_stabla"], [])
        self.assertEqual(kontrola["tehnicke"], ["111111"])  # odluka 25.09.2026.: tehnicka sifra, bez centra
        self.assertEqual(kontrola["van_sifarnika"], ["960001"])
        self.assertIn("431112", kontrola["samo_u_registru"])

    def test_poruka_za_istoriju_zadataka(self):
        from finansije.models import SyncRun

        poruka = self.sync.poruka(self.sync.sinhronizuj())
        self.assertIn("UPOZORENJE", poruka)  # Finansije jos nisu nijednom preuzele sifarnik.
        self.assertIn("Uporedni izvestaj Flote: PROLAZI.", poruka)
        self.assertIn("Nabavke: PROLAZI.", poruka)
        self.assertLessEqual(len(poruka), 500)
        SyncRun.objects.create(company=1, year_from=2026, year_to=2026, status="success", finished_at=timezone.now())
        self.assertNotIn("UPOZORENJE", self.sync.poruka(self.sync.sinhronizuj()))

    def test_zadatak_je_zakazan_posle_stare_sinhronizacije(self):
        from django.conf import settings

        from core.management.commands.sync_celery_periodic_tasks import EXPECTED_PERIODIC_TASKS

        zadaci = {spec["task"]: spec for spec in EXPECTED_PERIODIC_TASKS}
        nova, stara = zadaci["organizacija.tasks.sync_organizacija_task"], zadaci["fleet.tasks.fetch_job_codes"]
        self.assertEqual(nova["hour"], stara["hour"])
        self.assertGreater(int(nova["minute"]), int(stara["minute"]))
        self.assertEqual(settings.CELERY_TASK_ROUTES["organizacija.tasks.sync_organizacija_task"], {"queue": "sync"})

    def test_zadatak_i_komanda(self):
        from unittest import mock

        from organizacija import tasks

        with mock.patch.object(tasks, "_run_with_singleton_lock", side_effect=lambda task_name, lock_ttl_seconds, fn: fn()):
            self.assertIn("Registar:", tasks.sync_organizacija_task.run())
        izlaz = StringIO()
        call_command("sync_organizacija", stdout=izlaz)
        self.assertIn("OJ stara/nova", izlaz.getvalue())
        self.assertIn("nema u sifarniku poslova: 960001", izlaz.getvalue())


class CentriINaukaTests(FlotaTestCase):
    """Odluka 25.09.2026.: blokovi su centri `2` i `3` (knjizenja ih vode kao 20 i 30), a naucna
    sifra je `3` + sifra radnika iz Kadrova + broj projekta — posao u bloku 3."""

    def setUp(self):
        super().setUp()
        self.poslovni = OrganizationalUnit.objects.create(code="209001", name="Organizacija i poslovanje", center="2")
        self.nauka = OrganizationalUnit.objects.create(code="315400", name="Delic Ivana", center="3")
        run_import(company=1)

    def deo(self, kljuc):
        return next(d for d in flota.uporedni_izvestaj()["delovi"] if d["kljuc"] == kljuc)

    def test_oznaka_centra_iz_jedinice_knjizenja(self):
        from organizacija.services import classification as klas

        self.assertEqual([klas.oznaka_centra(j) for j in ("20", "30", " 30 ", "41", "11", "")],
                         ["2", "3", "3", "41", "11", ""])

    def test_registar_vodi_centre_2_i_3(self):
        from organizacija.models import OrgNode, OrgNodeVersion

        centri = set(OrgNodeVersion.objects.filter(node__level=OrgNode.LEVEL_CENTER, valid_to__isnull=True)
                     .values_list("full_code", flat=True))
        self.assertTrue({"2", "3"} <= centri)
        self.assertFalse({"20", "30"} & centri)

    def test_naucna_sifra_je_radnik_i_projekat(self):
        from organizacija.services import classification as klas

        self.assertEqual(klas.sifra_radnika_nauke("315400"), 154)
        self.assertEqual(klas.sifra_radnika_nauke("3154702400"), 154)
        self.assertEqual(klas.sifra_radnika_nauke("333331"), 333)
        self.assertIsNone(klas.sifra_radnika_nauke("300001"))  # posao samog bloka, nije nauka
        self.assertIsNone(klas.sifra_radnika_nauke("430111"))

    def test_poslovni_blok_se_poklapa_bez_prevodjenja(self):
        self.putni_nalog(self.poslovni)
        nalozi = self.deo("putni_nalozi")
        self.assertTrue(nalozi["prolazi"])
        self.assertEqual([r["centar"] for r in nalozi["redovi"]], ["2"])

    def test_nalog_na_naucnoj_sifri_ide_na_svoj_posao_u_bloku_3(self):
        nalog = self.putni_nalog(self.nauka)
        self.assertEqual(nalog.org_node_id, cvor("315400"))
        self.assertEqual(self.gorivo("3154190170").org_node_id, cvor("3154190170"))
        nalozi = self.deo("putni_nalozi")
        self.assertTrue(nalozi["prolazi"])
        self.assertEqual([r["centar"] for r in nalozi["redovi"]], ["3"])

    def test_broj_putnog_naloga_ostaje_na_oznaci_centra(self):
        self.putni_nalog(self.poslovni, broj="2/2026-5")
        nalog = PutniNalog(job_code=self.poslovni, travel_location="BG", task="T", travel_date=datetime.date(2026, 7, 10),
                           number_of_days=1, advance_payment=Decimal("1"))
        nalog.save()
        self.assertEqual(nalog.order_number, "2/2026-6")
        self.assertEqual(OrganizationalUnit.objects.get(pk=self.poslovni.pk).center, "2")

    def test_poredjenje_jedinica_vodi_nauku_u_blok_3(self):
        from organizacija.services import sync

        kontrola = sync.uporedi_jedinice()
        self.assertEqual(kontrola["razlika_centra"], [])
        self.assertNotIn("315400", kontrola["van_stabla"])

    def test_migracija_ispravlja_oznaku_na_mestu(self):
        from importlib import import_module

        from django.apps import apps as global_apps
        from django.db import connection
        from organizacija.models import OrgNode, OrgNodeVersion

        centar = OrgNodeVersion.objects.get(node__level=OrgNode.LEVEL_CENTER, full_code="2", valid_to__isnull=True)
        OrgNodeVersion.objects.filter(pk=centar.pk).update(full_code="20", segment="20")
        migracija = import_module("organizacija.migrations.0005_centri_2_i_3")

        class Editor:
            pass

        editor = Editor()
        editor.connection = connection
        migracija.ispravi(global_apps, editor)
        centar.refresh_from_db()
        self.assertEqual((centar.full_code, centar.segment), ("2", "2"))
        self.assertEqual(OrgNodeVersion.objects.filter(node=centar.node).count(), 1)
        self.assertIn("ispravljena", centar.note)


class PravilnikTests(ImportTestCase):
    """Nazivi po Pravilniku o organizaciji (18.04.2024.), latinicom; nauka u bloku 3."""

    def setUp(self):
        super().setUp()
        FinanceJob.objects.create(company=1, code="431111", center="43", name="Strucni nadzor i ter.ispitiv", active=True, profit_type="P")
        FinanceJob.objects.create(company=1, code="418111", center="41", name="Zastita zivotne sredine", active=True, profit_type="P")
        FinanceJob.objects.create(company=1, code="323331", center="3", name="Projekat 101822", active=False, profit_type="N")
        FinanceJob.objects.create(company=1, code="3166190170", center="3", name="P190170-Vasic R.", active=True, profit_type="N")
        Employee.objects.create(employee_code=154, first_name="Ivana", last_name="Delić Nikolić", position="Istraživač",
                                department_code=30, gender="F", date_of_birth=datetime.date(1980, 1, 1),
                                date_of_joining=datetime.date(2010, 1, 1))
        self.run = run_import(company=1)

    def verzija(self, code):
        from organizacija.models import OrgNodeVersion

        return OrgNodeVersion.objects.get(full_code=code, valid_to__isnull=True)

    def stablo(self, **kwargs):
        from organizacija.services import tree

        return tree.build_tree(1, **kwargs)

    def test_centri_dobijaju_nazive_iz_pravilnika(self):
        self.assertEqual(self.verzija("3").name, "Naučno-istraživački blok")
        self.assertEqual(self.verzija("41").name, "Centar za materijale")
        self.assertEqual(self.verzija("2").name, "Poslovni blok")
        self.assertIn("Pravilnik", self.verzija("41").note)

    def test_jedinica_dobija_naziv_samo_kad_se_poklapaju_broj_i_sadrzaj(self):
        self.assertEqual(self.verzija("431").name, "Odeljenje za geotehniku i nadzor")
        self.assertIn("4.3.1", self.verzija("431").note)
        # 418: po broju akustika, po sadrzaju zastita zivotne sredine — ne upisuje se, samo predlog.
        self.assertEqual(self.verzija("418").name, "")
        centar = next(c for c in self.stablo() if c["code"] == "41")
        jedinica = next(u for u in centar["units"] if u["code"] == "418")
        self.assertEqual(jedinica["predlog"], "Odeljenje za zaštitu životne sredine")
        self.assertIn("4.1.8", jedinica["predlog_razlog"])

    def test_naucni_projekat_je_jedinica_bloka_3(self):
        blok = next(c for c in self.stablo() if c["code"] == "3")
        self.assertEqual(blok["oj_knjizenja"], "30")
        jedinice = {u["code"]: u for u in blok["units"]}
        self.assertEqual(set(jedinice), {"300", "3-00", "3-190170", "3233"})
        # Isti projekat 190170 kod dva radnika je jedna jedinica.
        self.assertEqual([j["code"] for j in jedinice["3-190170"]["jobs"]], ["3154190170", "3166190170"])
        self.assertEqual(jedinice["3-190170"]["predlog"], "P190170")
        self.assertEqual(jedinice["3-00"]["predlog"], "Istraživači bez projekta (šifra samog radnika)")
        self.assertEqual(jedinice["3233"]["predlog"], "Zbirne institutske teme")
        self.assertEqual(jedinice["300"]["predlog"], "Zajednički troškovi centra")

    def test_sifra_je_povezana_sa_radnikom_iz_kadrova(self):
        blok = next(c for c in self.stablo() if c["code"] == "3")
        poslovi = {j["code"]: j for u in blok["units"] for j in u["jobs"]}
        delic = poslovi["3154190170"]["radnik"]
        self.assertEqual((delic["vrsta"], delic["broj"], delic["ime"]), ("zaposlen", 154, "Delić Nikolić Ivana"))
        # Broja 166 nema u Kadrovima: bivsi zaposleni, ime iz naziva sifre.
        self.assertEqual((poslovi["3166190170"]["radnik"]["vrsta"], poslovi["3166190170"]["radnik"]["ime"]),
                         ("bivsi", "Vasic R."))
        self.assertEqual(poslovi["323331"]["radnik"]["vrsta"], "zbirni")
        self.assertIsNone(poslovi["300001"]["radnik"])

    def test_ime_se_poredi_na_nivou_radnika(self):
        FinanceJob.objects.create(company=1, code="3154000", center="3", name="Bilateralni sporazum", active=True, profit_type="N")
        Employee.objects.create(employee_code=998, first_name="Marko", last_name="Stojanović", position="Istraživač",
                                department_code=30, gender="M", date_of_birth=datetime.date(1980, 1, 1),
                                date_of_joining=datetime.date(2010, 1, 1))
        FinanceJob.objects.create(company=1, code="3998360140", center="3", name="Berisavljević Zoran", active=True, profit_type="N")
        run_import(company=1)
        poslovi = {j["code"]: j for c in self.stablo() for u in c["units"] for j in u["jobs"]}
        # Naziv bez imena ne obara vezu kad radnika potvrdjuje druga njegova sifra (315400 „Delic Ivana").
        self.assertEqual(poslovi["3154000"]["radnik"]["vrsta"], "zaposlen")
        # Licni broj 998 u Kadrovima nosi drugi radnik: veza ostaje, ali je oznacena za proveru.
        berisavljevic = poslovi["3998360140"]["radnik"]
        self.assertEqual((berisavljevic["vrsta"], berisavljevic["u_sifri"]), ("ne_poklapa", "Berisavljević Zoran"))

    def test_ponovljen_uvoz_ne_pravi_verzije_za_nazive(self):
        from organizacija.models import OrgNodeVersion

        pre = OrgNodeVersion.objects.count()
        drugi = run_import(company=1)
        self.assertEqual((drugi.nodes_created, drugi.versions_created), (0, 0))
        self.assertEqual(OrgNodeVersion.objects.count(), pre)

    def test_naziv_iz_pravilnika_ispravlja_postojecu_verziju_na_mestu(self):
        from organizacija.models import OrgNodeVersion

        jedinica = self.verzija("431")
        OrgNodeVersion.objects.filter(pk=jedinica.pk).update(name="", valid_from=datetime.date(2026, 1, 1))
        run_import(company=1)
        jedinica.refresh_from_db()
        self.assertEqual(jedinica.name, "Odeljenje za geotehniku i nadzor")
        self.assertIsNone(jedinica.valid_to)
        self.assertEqual(OrgNodeVersion.objects.filter(node=jedinica.node).count(), 1)

    def test_centri_idu_brojevnim_redom_i_po_delovima_pravilnika(self):
        from organizacija.services import tree

        stablo = self.stablo()
        self.assertEqual([c["code"] for c in stablo], ["2", "3", "11", "41", "43"])
        grupe = tree.po_delovima(stablo)
        self.assertEqual([(g["deo"], [c["code"] for c in g["centri"]]) for g in grupe],
                         [(None, ["2"]), (3, ["3"]), (11, ["11"]), (4, ["41", "43"])])
        self.assertEqual(grupe[3]["naziv"], "Poslovno-razvojni blok")

    def test_pretraga_nalazi_radnika_i_projekat(self):
        self.assertEqual([c["code"] for c in self.stablo(query="delić")], ["3"])
        pogodak = self.stablo(query="190170")
        self.assertEqual(sorted(j["code"] for c in pogodak for u in c["units"] for j in u["jobs"]),
                         ["3154190170", "3166190170"])

    def test_povezivanje_samo_po_licnom_broju(self):
        from hr.models import Employee as E
        from organizacija.services import naucnici

        def radnik(broj, prezime, ime, aktivan=True):
            return E(pk=broj, employee_code=broj, last_name=prezime, first_name=ime, is_active=aktivan)

        veze = naucnici.povezi({
            "315400": "Delic Ivana",                 # u Kadrovima, neaktivna
            "3657190170": "P190170-Marceta L.",      # broj postoji, prezime se ne poklapa
            "31014000": "Ugovor o instit.finans. Susic Isidora",  # broja 101 nema — bez pogadjanja po imenu
        }, kadrovi=[radnik(154, "Delić Nikolić", "Ivana", aktivan=False), radnik(657, "Kuresević", "Lidja"),
                    radnik(1014, "Susić", "Isidora")])
        self.assertEqual(veze["315400"]["vrsta"], "bivsi_u_kadrovima")
        self.assertEqual((veze["3657190170"]["vrsta"], veze["3657190170"]["u_sifri"]), ("ne_poklapa", "Marceta L."))
        self.assertEqual((veze["31014000"]["vrsta"], veze["31014000"]["ime"], veze["31014000"]["pk"]),
                         ("bivsi", "Susic Isidora", None))

    def test_ime_iz_naziva_sifre(self):
        from organizacija.services.naucnici import ime_iz_naziva

        self.assertEqual([ime_iz_naziva(n) for n in ("P190170-Vasic R.", "TD 7024 - Mitrovic A.", "M.Drpic P-42012",
                                                    "Ugovor o instit.finans. Susic Isidora", "Pr. DAAD-Odanovic", "P-")],
                         ["Vasic R.", "Mitrovic A.", "M.Drpic", "Susic Isidora", "Odanovic", ""])

    def test_oznaka_projekta_iz_naziva_sifara(self):
        from organizacija.services.tree import oznaka_projekta

        self.assertEqual(oznaka_projekta(["TD 7024-Delic I.", "TD 7024 - Mitrovic A.", "P19020-Savic M."]), "TD 7024")
        self.assertEqual(oznaka_projekta(["B.Budisavljevic P-42012"]), "P 42012")
        self.assertEqual(oznaka_projekta(["Susic"]), "")

    def test_ekran_stabla(self):
        admin = get_user_model().objects.create_superuser("stablo-admin", "s@example.com", "x")
        self.client.force_login(admin)
        odgovor = self.client.get(reverse("organizacija:stablo"))
        self.assertContains(odgovor, "Poslovno-razvojni blok")
        self.assertContains(odgovor, "Delić Nikolić Ivana")
        self.assertContains(odgovor, reverse("employee_detail", args=[Employee.objects.get(employee_code=154).pk]))
        self.assertContains(odgovor, "u knjiženjima OJ 30")
        self.assertContains(odgovor, "Odeljenje za geotehniku i nadzor")
        self.assertContains(odgovor, "proveriti")
        self.assertEqual([g["family"] for g in odgovor.context["unresolved"]], ["C"])


class CitanjeRegistraUFlotiTests(FlotaTestCase):
    """Korak 4: Flota nudi i imenuje sifre iz registra; staro polje i dalje se upisuje."""

    def setUp(self):
        super().setUp()
        self.neaktivna = OrganizationalUnit.objects.create(code="431112", name="Terenske lab.", center="43")
        run_import(company=1)

    def forma(self, **kwargs):
        from fleet.forms.putni_nalozi import PutniNalogForm

        return PutniNalogForm(**kwargs)

    def test_izbor_sifre_su_samo_aktivne_sifre_iz_registra(self):
        polje = self.forma().fields["job_code"]
        self.assertEqual(set(polje.queryset.values_list("code", flat=True)), {"430111", "410001"})
        self.assertEqual(polje.label_from_instance(self.nadzor), "430111 — Strucni nadzor · centar 43")

    def test_upisana_sifra_ostaje_u_izboru_i_kad_nije_aktivna(self):
        nalog = self.putni_nalog(self.neaktivna)
        polje = self.forma(instance=nalog).fields["job_code"]
        self.assertIn(self.neaktivna, polje.queryset)
        self.assertNotIn(self.test_centar, polje.queryset)  # 960001 nije u registru

    def test_iskljucen_prekidac_vraca_stari_izbor(self):
        with self.settings(FLOTA_REGISTAR_ORGANIZACIJE=False):
            polje = self.forma().fields["job_code"]
            self.assertEqual(polje.queryset.count(), OrganizationalUnit.objects.count())
            self.assertEqual(polje.label_from_instance(self.nadzor), str(self.nadzor))

    def test_prazan_registar_ne_prazni_izbor(self):
        from organizacija.models import ExternalOrgMapping, LegacyOrgLink

        LegacyOrgLink.objects.all().delete()
        ExternalOrgMapping.objects.all().delete()
        self.assertEqual(self.forma().fields["job_code"].queryset.count(), OrganizationalUnit.objects.count())

    def test_izbor_dodele_vozila(self):
        from fleet.forms.vehicles import JobCodeForm

        kodovi = set(JobCodeForm().fields["organizational_unit"].queryset.values_list("code", flat=True))
        self.assertEqual(kodovi, {"430111", "410001"})

    def test_filteri_nude_centre_sa_nazivima_iz_registra(self):
        from fleet.filters import PutniNalogFilter, TrafficCardFilterForm

        self.putni_nalog(self.nadzor)
        filter_naloga = PutniNalogFilter(data={}, queryset=PutniNalog.objects.all())
        self.assertIn(("43", "43 — Centar za puteve i geotehniku"), filter_naloga.filters["center"].extra["choices"])
        self.assertIn(("430111", "430111 — Strucni nadzor · centar 43"), filter_naloga.filters["job_code"].extra["choices"])
        kartice = TrafficCardFilterForm()
        self.assertIn(("41", "41 — Centar za materijale"), kartice.fields["center"].choices)
        # Odluka 25.09.2026.: neaktivne sifre se ne nude nigde, ni u filteru; ni sifre van registra.
        self.assertNotIn(self.neaktivna, kartice.fields["organizational_unit"].queryset)
        self.assertNotIn(self.test_centar, kartice.fields["organizational_unit"].queryset)
        self.assertIn(self.nadzor, kartice.fields["organizational_unit"].queryset)

    def test_kontrolna_tabla_imenuje_centar(self):
        from fleet.support.fleet_snapshot import fleet_snapshot

        JobCode.objects.create(vehicle=self.car, organizational_unit=self.nadzor, assigned_date=datetime.date(2026, 1, 1))
        admin = get_user_model().objects.create_superuser("tabla-admin", "t@example.com", "x")
        centri = fleet_snapshot(admin, datetime.date(2026, 9, 25))["centers"]
        self.assertIn("Centar 43 — Centar za puteve i geotehniku", [c["label"] for c in centri])

    def test_forma_prava_pristupa_imenuje_centre_i_sifre(self):
        from core.user_access import UserAccessForm

        admin = get_user_model().objects.create_superuser("prava-admin", "p@example.com", "x")
        admin.allowed_centers.add(self.test_centar)  # vec dodeljeno pravo, sifra van registra
        forma = UserAccessForm(instance=admin, actor=admin)
        self.assertIn(("43", "Centar 43 — Centar za puteve i geotehniku"), forma.fields["center_codes"].choices)
        self.assertEqual(forma.fields["allowed_centers"].label_from_instance(self.nadzor),
                         "430111 — Strucni nadzor · centar 43")
        # Postojeca prava ne nestaju: vec dodeljena ostaje u izboru, a neaktivne se ne nude.
        self.assertIn(self.test_centar, forma.fields["allowed_centers"].queryset)
        self.assertNotIn(self.neaktivna, forma.fields["allowed_centers"].queryset)

    def test_forme_ne_prikazuju_polje_org_node(self):
        from fleet.forms.fuel import FuelConsumptionForm
        from fleet.forms.lease import LeaseForm
        from fleet.forms.vehicles import JobCodeForm

        for forma in (self.forma(), JobCodeForm(), FuelConsumptionForm(), LeaseForm()):
            self.assertNotIn("org_node", forma.fields)


class NabavkaURegistruTests(FlotaTestCase):
    """Faza 2 za Nabavku: veza `org_node` na predmetima, fakturama i vezama faktura; uporedni izvestaj."""

    def setUp(self):
        super().setUp()
        from nabavka.models import ProcurementCase, ProcurementInvoice, ProcurementInvoiceJobCodeLink

        self.korisnik = get_user_model().objects.create_superuser("nabavka-admin", "n@example.com", "x")
        self.predmet = ProcurementCase.objects.create(case_number="ZN-43/2026-1", title="Zahtev",
                                                      job_code=self.nadzor, created_by=self.korisnik)
        self.faktura = ProcurementInvoice.objects.create(source=ProcurementInvoice.SOURCE_EUF, euf_key="euf-1",
                                                         invoice_number="IF-1", supplier_name="Partner DOO",
                                                         job_code=self.nadzor, amount=Decimal("1200.00"),
                                                         invoice_date=datetime.date(2026, 4, 1))
        self.veza = ProcurementInvoiceJobCodeLink.objects.create(invoice=self.faktura, job_code=self.materijali)
        run_import(company=1)

    def test_komanda_popunjava_nabavku_i_ne_dira_flotu(self):
        from nabavka.models import ProcurementCase, ProcurementInvoiceJobCodeLink

        zbirovi = {z["kljuc"]: z for z in flota.povezi(modul="nabavka")}
        self.assertEqual(set(zbirovi), {"predmeti", "fakture", "veze_faktura"})
        self.assertEqual(ProcurementCase.objects.get(pk=self.predmet.pk).org_node_id, cvor("430111"))
        self.assertEqual(ProcurementInvoiceJobCodeLink.objects.get(pk=self.veza.pk).org_node_id, cvor("410001"))
        # Broj predmeta i staro polje ostaju.
        predmet = ProcurementCase.objects.get(pk=self.predmet.pk)
        self.assertEqual((predmet.case_number, predmet.job_code_id), ("ZN-43/2026-1", self.nadzor.pk))

    def test_cuvanje_postavlja_vezu(self):
        from nabavka.models import ProcurementCase

        self.predmet.job_code = self.materijali
        self.predmet.save()
        self.assertEqual(ProcurementCase.objects.get(pk=self.predmet.pk).org_node_id, cvor("410001"))

    def test_uporedni_izvestaj_nabavke(self):
        flota.povezi(modul="nabavka")
        izvestaj = flota.uporedni_izvestaj(modul="nabavka")
        self.assertTrue(izvestaj["prolazi"])
        fakture = next(d for d in izvestaj["delovi"] if d["kljuc"] == "fakture")
        self.assertEqual([(r["centar"], r["staro_iznos"], r["novo_iznos"]) for r in fakture["redovi"]],
                         [("43", Decimal("1200.00"), Decimal("1200.00"))])
        self.assertNotIn("gorivo_po_vozilu", [d["kljuc"] for d in izvestaj["delovi"]])

    def test_ekran_ima_karticu_nabavke(self):
        self.client.force_login(self.korisnik)
        odgovor = self.client.get(reverse("organizacija:flota"), {"modul": "nabavka"})
        self.assertContains(odgovor, "Registar i Nabavka")
        self.assertContains(odgovor, "Predmeti nabavke")
        self.assertEqual(self.client.get(reverse("organizacija:flota"), {"modul": "xyz"}).context["modul"], "flota")

    def test_forme_nabavke_ne_prikazuju_org_node(self):
        from nabavka.models import ProcurementCase

        self.assertFalse(ProcurementCase._meta.get_field("org_node").editable)

    def test_spiskovi_nabavke_iz_registra(self):
        from nabavka.filters import ProcurementCaseFilter
        from nabavka.forms import ProcurementInvoiceJobCodeLinkForm
        from nabavka.models import ProcurementCase

        neaktivna = OrganizationalUnit.objects.create(code="431112", name="Terenske lab.", center="43")
        run_import(company=1)
        veza = ProcurementInvoiceJobCodeLinkForm(invoice=self.faktura).fields["job_code"]
        # Odluka 25.09.2026.: neaktivne sifre se ne nude ni za povezivanje fakture.
        self.assertNotIn(neaktivna, veza.queryset)
        self.assertNotIn(self.test_centar, veza.queryset)
        self.assertEqual(veza.label_from_instance(self.nadzor), "430111 — Strucni nadzor · centar 43")
        filter_predmeta = ProcurementCaseFilter(data={}, queryset=ProcurementCase.objects.all())
        self.assertNotIn(neaktivna, filter_predmeta.form.fields["job_code"].queryset)
        self.assertIn(self.nadzor, filter_predmeta.form.fields["job_code"].queryset)


class FinansijeURegistruTests(ImportTestCase):
    """Faza 2 za Finansije: `org_node` na knjizenju, postavljanje pri objavi i uporedni izvestaj."""

    def setUp(self):
        super().setUp()
        from finansije.models import LedgerEntry

        run_import(company=1)
        # Kao u izvoru: centar na knjizenju je `posao.blok` sifre (2 i 3 za blokove; prazan kod 110002 i 430001).
        for code, centar in (("209001", "2"), ("315400", "3"), ("3154190170", "3"), ("110002", ""), ("430001", "")):
            LedgerEntry.objects.filter(job_code=code).update(center=centar)

    def test_komanda_povezuje_knjizenja(self):
        from finansije.models import LedgerEntry

        zbir = flota.povezi(modul="finansije")[0]
        self.assertEqual(zbir["kljuc"], "knjizenja")
        self.assertEqual(LedgerEntry.objects.get(job_code="430111").org_node_id, cvor("430111"))
        self.assertEqual(zbir["nerazresene_sifre"], [("vranjs", 1)])

    def test_uporedni_izvestaj_posle_odluka(self):
        """110002/430001 su potvrdjeno 11/43; 111111 je tehnicka sifra bez centra (odluke 25.09.2026.)."""
        from finansije.models import LedgerEntry

        self._ledger("111111", "1")
        LedgerEntry.objects.filter(job_code="111111").update(center="3")  # izvor mu upisuje 3
        flota.povezi(modul="finansije")
        deo = flota.uporedni_izvestaj(modul="finansije")["delovi"][0]
        razlike = sorted((p["sifra"], p["staro"], p["novo"]) for p in deo["primeri"])
        self.assertEqual(razlike, [("vranjs", "43", flota.VAN_STABLA)])  # jos nerazreseno
        self.assertEqual((deo["dopuna"], deo["tehnickih"]), (0, 1))
        centri = {r["centar"]: r for r in deo["redovi"]}
        self.assertEqual((centri["11"]["staro_broj"], centri["11"]["novo_broj"]), (1, 1))
        self.assertTrue(centri[flota.TEHNICKA]["poklapa"])
        self.assertNotIn("3", {c for c, r in centri.items() if r["staro_broj"] != r["novo_broj"]})

    def test_objava_sinhronizacije_postavlja_vezu(self):
        from unittest import mock

        from finansije.models import LedgerEntry
        from finansije.services.sync import sync_ledger
        from finansije.tests import job, posting

        red = posting(number=900, job_code="430111", center="43")
        with mock.patch("finansije.services.sync.fetch_source", return_value=([red], [job(code="430111", center="43")])):
            sync_ledger(year_from=2026, year_to=2026)
        self.assertEqual(LedgerEntry.objects.get(journal_number=900).org_node_id, cvor("430111"))
        izmenjen = posting(number=900, job_code="410001", center="41", credit=Decimal("150.00"))
        with mock.patch("finansije.services.sync.fetch_source", return_value=([izmenjen], [job(code="410001", center="41")])):
            sync_ledger(year_from=2026, year_to=2026)
        self.assertEqual(LedgerEntry.objects.get(journal_number=900).org_node_id, cvor("410001"))

    def test_spisak_centara_u_finansijama_nosi_naziv(self):
        from finansije.forms import ReportFilters
        from finansije.models import FinanceJob, LedgerEntry

        forma = ReportFilters({}, jobs=FinanceJob.objects.all(), entries=LedgerEntry.objects.all())
        self.assertIn(("43", "43 — Centar za puteve i geotehniku"), forma.fields["center"].choices)


class PotrazivanjaURegistruTests(ImportTestCase):
    """Faza 2 za Potrazivanja: veza se postavlja pri sinhronizaciji; poredi se poslednji snimak."""

    def setUp(self):
        super().setUp()
        FinanceJob.objects.create(company=1, code="436111", center="43", name="Geotehnicka ispitivanja", active=True,
                                  profit_type="P")
        OrganizationalUnit.objects.create(code="436111", center="43", name="Posao")
        run_import(company=1)

    def sinhronizuj(self):
        from copy import deepcopy
        from unittest import mock

        from potrazivanja.services.sync import sync_collections
        from potrazivanja.test_sync import OBSERVED, fixture

        with mock.patch("potrazivanja.services.sync.extract", return_value=(deepcopy(fixture()), OBSERVED)):
            return sync_collections(trigger="import", include_legacy=True)

    def test_sinhronizacija_postavlja_vezu_na_stavkama_i_pozicijama(self):
        from potrazivanja.models import ReceivablePosition, ReceivablePosting

        self.sinhronizuj()
        self.assertEqual(ReceivablePosting.objects.get().org_node_id, cvor("436111"))
        self.assertEqual(ReceivablePosition.objects.get().org_node_id, cvor("436111"))

    def test_uporedni_izvestaj_poredi_poslednji_snimak(self):
        from potrazivanja.models import ReceivablePosition

        self.sinhronizuj()
        self.sinhronizuj()  # drugi snimak; stari ostaje objavljen, ali se ne broji
        self.assertEqual(ReceivablePosition.objects.count(), 2)
        izvestaj = flota.uporedni_izvestaj(modul="potrazivanja")
        self.assertTrue(izvestaj["prolazi"])
        pozicije = next(d for d in izvestaj["delovi"] if d["kljuc"] == "pozicije")
        self.assertEqual((pozicije["ukupno"], pozicije["redovi"][0]["centar"]), (1, "43"))

    def test_komanda_za_potrazivanja(self):
        from potrazivanja.models import ReceivablePosting

        self.sinhronizuj()
        ReceivablePosting.objects.update(org_node=None)
        zbirovi = {z["kljuc"]: z for z in flota.povezi(modul="potrazivanja")}
        self.assertEqual(zbirovi["stavke"]["postavljeno"], 1)
        self.assertEqual(ReceivablePosting.objects.get().org_node_id, cvor("436111"))


class NeaktivneSifreIGarazaTests(ImportTestCase):
    """Odluke 25.09.2026.: neaktivne sifre se ne nude u Finansijama; Garaza ima celu firmu."""

    def setUp(self):
        super().setUp()
        run_import(company=1)

    def test_finansije_ne_nude_neaktivne_sifre(self):
        from finansije.forms import ReportFilters
        from finansije.models import FinanceJob, LedgerEntry

        forma = ReportFilters({}, jobs=FinanceJob.objects.all(), entries=LedgerEntry.objects.all())
        sifre = {c for c, _ in forma.fields["job"].choices}
        self.assertIn("430111", sifre)
        self.assertNotIn("431112", sifre)  # neaktivna u izvoru
        izabrana = ReportFilters({"job": "431112"}, jobs=FinanceJob.objects.all(), entries=LedgerEntry.objects.all())
        self.assertIn("431112", {c for c, _ in izabrana.fields["job"].choices})  # izabrana ostaje

    def test_izvestaj_po_siframa_prikazuje_samo_aktivne(self):
        from finansije.models import FinanceJob, LedgerEntry
        from finansije.services.reports import grouped_report

        self._ledger("431112", "43")  # neaktivna sifra sa prometom
        totals, rows = grouped_report(LedgerEntry.objects.all(), FinanceJob.objects.all(), {"group": "job"})
        self.assertNotIn("431112", {r["code"] for r in rows})
        self.assertEqual(totals["count"], sum(r["count"] for r in rows))  # zbir se slaze sa redovima
        # Izvestaj po centrima ostaje ceo.
        totals_c, _ = grouped_report(LedgerEntry.objects.all(), FinanceJob.objects.all(), {"group": "center"})
        self.assertEqual(totals_c["count"], LedgerEntry.objects.count())

    def test_sinhronizacija_gasi_sifre_bez_prometa(self):
        from organizacija.services import sync

        sync.sinhronizuj()
        aktivne = set(OrgNodeVersion.objects.filter(valid_to__isnull=True, node__level=OrgNode.LEVEL_JOB,
                                                    is_active=True).values_list("full_code", flat=True))
        knjizene = set(LedgerEntry.objects.values_list("job_code", flat=True))
        self.assertTrue(aktivne)
        self.assertLessEqual(aktivne, knjizene)

    def test_garaza_dobija_celu_firmu(self):
        from organizacija.models import DodelaUloge
        from organizacija.services import prava

        korisnik = get_user_model().objects.create_user("garaza-korisnik", password="x")
        korisnik.roles.add(Role.objects.get_or_create(slug="garaza", defaults={"name": "Garaža"})[0])
        prava.prevedi()
        self.assertTrue(DodelaUloge.objects.get(korisnik=korisnik, status=DodelaUloge.STATUS_NACRT).cela_firma)
