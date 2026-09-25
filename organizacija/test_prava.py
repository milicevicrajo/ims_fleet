"""Plan prelaska na registar, 3.1 i 3.2: putanja na datum, obuhvat, prevod starih prava i senka."""
import datetime

from django.contrib.auth import get_user_model

from core.models import OrganizationalUnit, PermissionCode, Role, RolePermission
from finansije.models import FinanceJob, LedgerEntry
from organizacija.models import DodelaUloge, ExternalOrgMapping, OrgNode, OrgNodeVersion
from organizacija.services import flota, prava, putanja
from organizacija.services.importer import run_import
from organizacija.tests import ImportTestCase


def cvor(sifra):
    return ExternalOrgMapping.objects.get(source=ExternalOrgMapping.SOURCE_FINANCE_JOB, source_key=sifra,
                                          valid_to__isnull=True).node_id


def centar(oznaka):
    return OrgNodeVersion.objects.get(node__level=OrgNode.LEVEL_CENTER, full_code=oznaka, valid_to__isnull=True).node_id


def jedinica(oznaka):
    return OrgNodeVersion.objects.get(node__level=OrgNode.LEVEL_UNIT, full_code=oznaka, valid_to__isnull=True).node_id


def uloga_sa_dozvolom(slug, *kodovi):
    uloga = Role.objects.create(name=slug, slug=slug)
    for kod in kodovi:
        dozvola, _ = PermissionCode.objects.get_or_create(code=kod)
        RolePermission.objects.create(role=uloga, permission=dozvola)
    return uloga


class PutanjaTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1, valid_from=datetime.date(2026, 1, 1))

    def test_svaki_posao_ima_putanju_do_centra(self):
        self.assertEqual(putanja.centar_na_dan(cvor("430111"), datetime.date(2026, 3, 1)), "43")
        self.assertEqual(putanja.centar_na_dan(cvor("3154190170"), datetime.date(2026, 3, 1)), "3")
        self.assertIsNone(putanja.centar_na_dan(cvor("430111"), datetime.date(2025, 12, 31)))  # pre snimka

    def test_ponovljena_izgradnja_ne_menja_nista(self):
        self.assertFalse(putanja.izgradi(1)[2])

    def test_promena_centra_od_datuma_cuva_stare_dokumente(self):
        # Jedinica 431 od 1.6.2026. prelazi pod centar 41: stari dokumenti ostaju u 43.
        v = OrgNodeVersion.objects.get(node_id=jedinica("431"), valid_to__isnull=True)
        OrgNodeVersion.objects.filter(pk=v.pk).update(valid_to=datetime.date(2026, 6, 1))
        OrgNodeVersion.objects.create(node_id=v.node_id, parent_id=centar("41"), segment=v.segment,
                                      full_code=v.full_code, name=v.name, is_active=True,
                                      valid_from=datetime.date(2026, 6, 1))
        self.assertTrue(putanja.izgradi(1)[2])
        posao = cvor("431112")
        self.assertEqual(putanja.centar_na_dan(posao, datetime.date(2026, 5, 31)), "43")
        self.assertEqual(putanja.centar_na_dan(posao, datetime.date(2026, 6, 1)), "41")
        self._ledger("431112", "43")
        LedgerEntry.objects.filter(job_code="431112").update(org_node=posao, booking_date=datetime.date(2026, 7, 1))
        u_41 = LedgerEntry.objects.filter(putanja.filter_na_dan("org_node", "booking_date", centar_sifra="41"))
        self.assertEqual(list(u_41.values_list("job_code", flat=True)), ["431112"])


class ObuhvatTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1, valid_from=datetime.date(2026, 1, 1))
        self.korisnik = get_user_model().objects.create_user("obuhvat", password="x")
        self.uloga = uloga_sa_dozvolom("finansije-uloga", "finansije:dashboard")
        self.korisnik.roles.add(self.uloga)

    def dodeli(self, **kwargs):
        return DodelaUloge.objects.create(korisnik=self.korisnik, uloga=self.uloga, vazi_od=datetime.date(2026, 1, 1),
                                          status=DodelaUloge.STATUS_AKTIVNA, **kwargs)

    def test_prazan_obuhvat_znaci_nema_pristupa(self):
        self.assertTrue(prava.obuhvat(self.korisnik, "finansije:dashboard").prazan)
        self.assertFalse(prava.ima_pravo(self.korisnik, "finansije:dashboard", cvor("430111")))

    def test_centar_pokriva_svoje_poslove_a_posao_samo_sebe(self):
        self.dodeli(cvor_id=cvor("410001"))
        self.assertTrue(prava.ima_pravo(self.korisnik, "finansije:dashboard", cvor("410001")))
        self.assertFalse(prava.ima_pravo(self.korisnik, "finansije:dashboard", cvor("430111")))
        self.dodeli(cvor_id=centar("43"))
        poslovi = prava.poslovi_obuhvata(prava.obuhvat(self.korisnik, "finansije:dashboard"))
        self.assertEqual(poslovi, {cvor("410001"), cvor("430111"), cvor("430001"), cvor("431112")})

    def test_obuhvat_vazi_samo_za_dozvole_uloge_i_u_periodu(self):
        self.dodeli(cvor_id=centar("43"), vazi_do=datetime.date(2026, 2, 1))
        self.assertTrue(prava.obuhvat(self.korisnik, "finansije:dashboard", dan=datetime.date(2026, 1, 15)).centri)
        self.assertTrue(prava.obuhvat(self.korisnik, "finansije:dashboard", dan=datetime.date(2026, 3, 1)).prazan)
        self.assertTrue(prava.obuhvat(self.korisnik, "potrazivanja:dashboard", dan=datetime.date(2026, 1, 15)).prazan)

    def test_q_obuhvata_na_knjizenjima(self):
        flota.povezi(modul="finansije")
        self.dodeli(cvor_id=centar("41"))
        q = prava.q_obuhvata(prava.obuhvat(self.korisnik, "finansije:dashboard"), "org_node", "booking_date")
        self.assertEqual(set(LedgerEntry.objects.filter(q).values_list("job_code", flat=True)), {"410001"})

    def test_superuser_ima_celu_firmu(self):
        admin = get_user_model().objects.create_superuser("obuhvat-admin", "a@example.com", "x")
        self.assertTrue(prava.obuhvat(admin, "finansije:dashboard").cela_firma)


class PrevodISenkaTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        FinanceJob.objects.create(company=1, code="410002", center="41", name="Provajder", active=True, profit_type="N")
        self._ledger("410002", "41")
        run_import(company=1)
        flota.povezi(modul="finansije")
        User = get_user_model()
        self.uloga = uloga_sa_dozvolom("finansije-uloga", "finansije:dashboard")
        materijali = OrganizationalUnit.objects.create(code="410001", name="Amortizacija", center="41")
        self.sa_oj = User.objects.create_user("samo-oj", password="x")
        self.sa_oj.roles.add(self.uloga)
        self.sa_oj.allowed_centers.add(materijali)
        self.sa_centrom = User.objects.create_user("sa-centrom", password="x", allowed_center_codes="43, 20, 96")
        self.sa_centrom.roles.add(self.uloga)
        self.uprava = User.objects.create_user("uprava-korisnik", password="x")
        self.uprava.roles.add(Role.objects.get_or_create(slug="uprava", defaults={"name": "Uprava"})[0])

    def test_prevod_starih_prava_u_nacrt(self):
        zbir = prava.prevedi()
        self.assertEqual(dict(zbir["nepoznate_oznake"]), {"96": 1})
        nacrt = DodelaUloge.objects.filter(status=DodelaUloge.STATUS_NACRT)
        self.assertEqual(set(nacrt.filter(korisnik=self.sa_centrom).values_list("cvor_id", flat=True)),
                         {centar("43"), centar("2")})  # oznaka 20 je centar 2
        # Odluka 25.09.2026.: dodeljena OJ daje ceo svoj centar, kao danas.
        self.assertEqual(list(nacrt.filter(korisnik=self.sa_oj).values_list("cvor_id", flat=True)), [centar("41")])
        self.assertTrue(nacrt.get(korisnik=self.uprava).cela_firma)
        broj = nacrt.count()
        prava.prevedi()  # ponovljen prevod zamenjuje nacrt, ne dodaje duplikate
        self.assertEqual(DodelaUloge.objects.filter(status=DodelaUloge.STATUS_NACRT).count(), broj)

    def test_nacrt_ne_odlucuje_o_pristupu(self):
        prava.prevedi()
        self.assertTrue(prava.obuhvat(self.sa_centrom, "finansije:dashboard").prazan)  # vazi samo aktivna dodela

    def test_senka_pokazuje_razlike(self):
        prava.prevedi()
        redovi = {r["korisnik"].username: r for r in prava.senka()}
        fin = redovi["samo-oj"]["moduli"]["finansije"]
        # OJ 410001 i danas i po nacrtu daje ceo centar 41 (i 410002) — bez razlike.
        self.assertEqual((fin["manje"], fin["vise"]), ([], []))
        self.assertEqual(fin["staro"], fin["novo"])
        centar_fin = redovi["sa-centrom"]["moduli"]["finansije"]
        # Oznaka 20 je po odluci centar 2 (danas ne pokriva 209001, jer sifarnik pise „2"), a 430001
        # je potvrdjeno centar 43 (danas bez centra) — senka to prikazuje kao „vise". `vranjs` danas
        # pripada centru 43 po sifarniku, a nije u registru — „manje", dok se ne resi otvoreno pitanje.
        self.assertEqual((centar_fin["vise"], centar_fin["manje"]), (["209001", "430001"], ["vranjs"]))
        self.assertNotIn("potrazivanja", redovi["samo-oj"]["moduli"])  # modul mu nije dostupan


class SenkaFloteTests(ImportTestCase):
    """Korak 4: senka i za spisak vozila i kontrolnu tablu Flote. Kadrovi nemaju posebnu organizaciju."""

    def setUp(self):
        super().setUp()
        run_import(company=1)
        from fleet.models import JobCode
        from fleet.test_vehicle_onboarding import vehicle

        nadzor = OrganizationalUnit.objects.create(code="430111", name="Strucni nadzor", center="43")
        materijali = OrganizationalUnit.objects.create(code="410001", name="Amortizacija", center="41")
        for broj, jedinica_ in (("1", nadzor), ("2", materijali)):
            JobCode.objects.create(vehicle=vehicle(broj), organizational_unit=jedinica_,
                                   assigned_date=datetime.date(2026, 1, 1))
        self.korisnik = get_user_model().objects.create_user("pregled-41", password="x", allowed_center_codes="41")
        self.korisnik.roles.add(uloga_sa_dozvolom("pregled-flote", "vehicle_list", "dashboard"))

    def test_spisak_vozila_danas_nema_ogranicenje_a_po_dodeli_ima(self):
        prava.prevedi()
        red = prava.senka(get_user_model().objects.filter(pk=self.korisnik.pk))[0]
        vozila = red["moduli"]["vozila"]
        self.assertEqual((vozila["staro"], vozila["novo"], vozila["manje"]), (2, 1, ["430111"]))
        tabla = red["moduli"]["kontrolna_tabla"]
        self.assertEqual((tabla["staro"], tabla["manje"]), (2, ["430111"]))  # bez OJ tabla danas vidi sve
        self.assertEqual(vozila["naziv"], "Vozila")
        self.assertNotIn("zaposleni", red["moduli"])
