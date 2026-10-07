"""Putni nalozi: dodavanje računa pri pravdanju i knjiženje (Isplate), zaključavanje (Nabavka)."""
from decimal import Decimal
from unittest import mock
from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import ActivityLog, OrganizationalUnit, PermissionCode, Role
from isplate.tests import create_employee, create_order
from knjizenje import services as knjizenje
from knjizenje.models import KnjizenjeRacuna
from nabavka.models import FiskalniRacun
from nabavka.services import fiskalni
from nabavka.test_fiskalni import LINK, lazni_suf, napravi_link

PRAVDANJE = ("isplate:putni_nalozi_pravdanje", "isplate:putni_nalog_racuni", "isplate:putni_nalog_racun_dodaj",
             "isplate:putni_nalog_racun_ukloni", "isplate:putni_nalog_opravdaj")
ISPLATE = ("isplate:fiskalni_putni_nalozi", "isplate:fiskalni_izvoz", "isplate:fiskalni_detail",
           "isplate:fiskalni_izmena", "isplate:fiskalni_posalji")
# Modul Knjiženje (od 07.10.2026.): Isplate šalju, Knjiženje knjiži.
KNJIZENJE = ("knjizenje:racuni", "knjizenje:racun", "knjizenje:proknjizi", "knjizenje:vrati", "knjizenje:ponisti",
             "knjizenje:izvoz")
NABAVKA = ("nabavka:fiskalni_detail", "nabavka:fiskalni_update", "nabavka:fiskalni_delete")


def korisnik_sa(ime, *kodovi):
    uloga = Role.objects.create(name=ime, slug=ime)
    for kod in kodovi:
        uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
    korisnik = get_user_model().objects.create_user(ime, password="x")
    korisnik.roles.add(uloga)
    return korisnik


class FiskalniPutnogNalogaTests(TestCase):
    def setUp(self):
        self.nalog = create_order(employee=create_employee(), order_number="43/2026-7", center="43")
        self.nikolina = korisnik_sa("nikolina", *PRAVDANJE)
        self.knjigovodja = korisnik_sa("bilja", *ISPLATE, *NABAVKA, *KNJIZENJE)
        self.client.force_login(self.nikolina)

    def ocitaj(self, link=LINK, nalog=None):
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            return self.client.post(reverse("isplate:putni_nalog_racun_dodaj", args=[(nalog or self.nalog).pk]), {"link": link},
                                    HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_novi_racun_dobija_sifru_posla_naloga(self):
        odgovor = self.ocitaj()
        self.assertEqual(odgovor.status_code, 200, odgovor.content)
        self.assertFalse(odgovor.json()["vezan_postojeci"])
        racun = FiskalniRacun.objects.get()
        self.assertEqual((racun.putni_nalog, racun.job_code, racun.created_by), (self.nalog, self.nalog.job_code, self.nikolina))
        self.assertEqual(odgovor.json()["iznos"], "1.804,50")  # kao poruka posle učitavanja u Nabavci
        racuni = self.client.get(reverse("isplate:putni_nalog_racuni", args=[self.nalog.pk])).json()
        self.assertEqual([r["broj"] for r in racuni["racuni"]], [racun.broj_racuna])
        self.assertEqual(racuni["zbir"], "1.804,50")
        self.assertEqual(self.client.get(reverse("isplate:putni_nalozi_pravdanje")).status_code, 200)
        tabela = self.client.get(reverse("isplate:putni_nalozi_pravdanje"), {"draw": 1}).json()  # DataTables
        self.assertEqual((tabela["recordsFiltered"], tabela["data"][0]["nalog"]), (1, "<strong>43/2026-7</strong>"))
        self.assertIn("1 · 1.804,50", tabela["data"][0]["racuni"])
        self.assertIn("Opravdaj", tabela["data"][0]["akcije"])

    def test_postojeci_racun_se_samo_veze_i_zadrzava_sifru(self):
        druga = OrganizationalUnit.objects.create(code="410001", name="Druga", center="41")
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            fiskalni.upisi(LINK, druga, self.knjigovodja)  # učitan ranije u Nabavci
        odgovor = self.ocitaj()
        self.assertTrue(odgovor.json()["vezan_postojeci"])
        racun = FiskalniRacun.objects.get()
        self.assertEqual((racun.putni_nalog, racun.job_code), (self.nalog, druga))
        self.assertEqual(self.ocitaj().status_code, 400)  # već je na ovom nalogu

    def test_racun_sa_drugog_naloga_i_storniran_nalog_se_odbijaju(self):
        self.ocitaj()
        drugi = create_order(employee=create_employee(code=9002), order_number="43/2026-8", center="43")
        odgovor = self.ocitaj(nalog=drugi)
        self.assertEqual(odgovor.status_code, 400)
        self.assertIn("43/2026-7", odgovor.json()["poruka"])
        drugi.storniran = True
        drugi.save(update_fields=["storniran"])
        odgovor = self.ocitaj(link=napravi_link(brojac=99), nalog=drugi)
        self.assertEqual(odgovor.status_code, 400)
        self.assertIn("storniran", odgovor.json()["poruka"])

    def test_skidanje_sa_naloga_samo_dok_nije_proknjizen(self):
        self.ocitaj()
        racun = FiskalniRacun.objects.get()
        fiskalni.oznaci_proknjizeno(racun, self.knjigovodja)
        self.assertEqual(self.client.post(reverse("isplate:putni_nalog_racun_ukloni", args=[self.nalog.pk, racun.pk])).status_code, 400)
        racun.refresh_from_db()
        self.assertEqual(racun.putni_nalog, self.nalog)  # proknjižen ostaje
        fiskalni.oznaci_proknjizeno(racun, self.knjigovodja, False)
        self.client.post(reverse("isplate:putni_nalog_racun_ukloni", args=[self.nalog.pk, racun.pk]))
        racun.refresh_from_db()
        self.assertIsNone(racun.putni_nalog)
        self.assertTrue(FiskalniRacun.objects.filter(pk=racun.pk).exists())  # ostaje u Nabavci

    def test_opravdan_nalog_je_zakljucan(self):
        self.ocitaj()
        odgovor = self.client.post(reverse("isplate:putni_nalog_opravdaj", args=[self.nalog.pk]), {"next": "https://zlo.example/"})
        self.assertRedirects(odgovor, reverse("isplate:putni_nalozi_pravdanje"), fetch_redirect_response=False)  # samo unutar aplikacije
        self.nalog.refresh_from_db()
        self.assertTrue(self.nalog.opravdan)
        odgovor = self.ocitaj(link=napravi_link(brojac=77))
        self.assertEqual(odgovor.status_code, 400)
        self.assertIn("opravdan", odgovor.json()["poruka"])
        racun = FiskalniRacun.objects.get()
        self.assertEqual(self.client.post(reverse("isplate:putni_nalog_racun_ukloni", args=[self.nalog.pk, racun.pk])).status_code, 400)
        racuni = self.client.get(reverse("isplate:putni_nalog_racuni", args=[self.nalog.pk])).json()
        self.assertTrue(racuni["zakljucan"])
        self.assertEqual(racuni["racuni"][0]["ukloni_url"], "")
        tabela = self.client.get(reverse("isplate:putni_nalozi_pravdanje"), {"draw": 1}).json()
        self.assertEqual(tabela["recordsFiltered"], 0)  # podrazumevano neopravdani
        tabela = self.client.get(reverse("isplate:putni_nalozi_pravdanje"), {"draw": 1, "status": "svi"}).json()
        self.assertNotIn("Opravdaj", tabela["data"][0]["akcije"])

    def test_opravdavanje_iz_tabele(self):
        odgovor = self.client.post(reverse("isplate:putni_nalog_opravdaj", args=[self.nalog.pk]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertTrue(odgovor.json()["ok"])
        self.nalog.refresh_from_db()
        self.assertTrue(self.nalog.opravdan)

    def test_ucitavanje_iz_naloga_za_isplatu(self):
        """U Isplati neoporezovanih svaki nalog ima dugme za fiskalne račune (isti prozor kao na pravdanju)."""
        self.nikolina.roles.first().permissions.add(PermissionCode.objects.get_or_create(code="isplate:neoporezive_isplate")[0])
        strana = self.client.get(reverse("isplate:neoporezive_isplate"))
        self.assertContains(strana, "Dodaj račun")
        self.assertContains(strana, reverse("isplate:putni_nalog_racun_dodaj", args=[self.nalog.pk]))
        self.assertContains(strana, 'id="ispRacuniModal"')
        self.ocitaj()
        self.assertContains(self.client.get(reverse("isplate:neoporezive_isplate")), "1 · 1.804,50")
        self.client.force_login(korisnik_sa("blagajnik", "isplate:neoporezive_isplate"))  # bez prava na račune
        self.assertNotContains(self.client.get(reverse("isplate:neoporezive_isplate")), 'id="ispRacuniModal"')

    def test_isplate_salju_a_knjizi_modul_knjizenje(self):
        self.ocitaj()
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):  # račun iz Nabavke, bez naloga
            fiskalni.upisi(napravi_link(brojac=55), self.nalog.job_code, self.knjigovodja)
        self.client.force_login(self.knjigovodja)
        spisak = self.client.get(reverse("isplate:fiskalni_putni_nalozi"))
        self.assertEqual(spisak.context["zbir"]["broj"], 1)  # samo računi sa putnih naloga
        tabela = self.client.get(reverse("isplate:fiskalni_putni_nalozi"), {"draw": 1}).json()  # DataTables
        self.assertEqual((tabela["recordsTotal"], tabela["recordsFiltered"], tabela["zbir"]["iznos"]), (1, 1, "1.804,50"))
        self.assertIn("43/2026-7", tabela["data"][0]["veza"])
        self.assertIn("isp-posalji", tabela["data"][0]["knjizenje"])  # dugme „Pošalji”
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_putni_nalozi"),
                                         {"draw": 2, "search[value]": "nema-takvog"}).json()["recordsFiltered"], 0)
        racun = FiskalniRacun.objects.get(putni_nalog=self.nalog)
        odgovor = self.client.post(reverse("isplate:fiskalni_posalji", args=[racun.pk]), HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
        self.assertTrue(odgovor["ok"])
        self.assertIn("Poslato", odgovor["kolona"])
        self.assertNotIn("isp-posalji", self.client.get(reverse("isplate:fiskalni_putni_nalozi"), {"draw": 3}).json()["data"][0]["knjizenje"])
        # poslat račun se ne skida sa naloga
        self.client.force_login(self.nikolina)
        self.assertEqual(self.client.post(reverse("isplate:putni_nalog_racun_ukloni", args=[self.nalog.pk, racun.pk])).status_code, 400)
        self.client.force_login(self.knjigovodja)

        self.client.post(reverse("knjizenje:proknjizi"), {"racuni": [racun.pk], "datum": "2026-10-07", "broj_naloga": "TN-12"})
        racun.refresh_from_db()
        self.assertEqual((racun.proknjizeno, racun.proknjizio, racun.knjizenje.broj_naloga), (True, self.knjigovodja, "TN-12"))
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_putni_nalozi")).context["zbir"]["broj"], 0)  # podrazumevano neproknjiženi
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_putni_nalozi"), {"knjizenje": "da"}).context["zbir"]["broj"], 1)
        self.client.post(reverse("knjizenje:ponisti", args=[racun.pk]), {"razlog": "pogrešan nalog"})
        racun.refresh_from_db()
        self.assertEqual((racun.proknjizeno, racun.proknjizio, racun.proknjizeno_at), (False, None, None))
        self.assertEqual(racun.knjizenje.status, KnjizenjeRacuna.Status.POSLATO)
        self.assertTrue(ActivityLog.objects.filter(action=ActivityLog.ACTION_MANUAL, object_pk=str(racun.pk),
                                                   description__contains="Poništena").exists())
        izvoz = self.client.get(reverse("isplate:fiskalni_izvoz"), {"knjizenje": "sve"})
        self.assertEqual(izvoz.status_code, 200)
        self.assertIn("spreadsheetml", izvoz["Content-Type"])

    def test_proknjizen_racun_se_ne_menja_ni_brise_u_nabavci(self):
        self.ocitaj()
        racun = FiskalniRacun.objects.get()
        fiskalni.oznaci_proknjizeno(racun, self.knjigovodja)
        self.client.force_login(self.knjigovodja)
        detalj = self.client.get(reverse("nabavka:fiskalni_detail", args=[racun.pk]))
        self.assertContains(detalj, "Putni nalog")
        self.assertContains(detalj, "43/2026-7")
        self.assertNotContains(detalj, "Obriši račun")
        self.client.post(reverse("nabavka:fiskalni_delete", args=[racun.pk]))
        self.client.post(reverse("nabavka:fiskalni_update", args=[racun.pk]), {"akcija": "obrada", "napomena": "izmena"})
        racun.refresh_from_db()
        self.assertEqual(racun.napomena, "")
        self.assertTrue(FiskalniRacun.objects.filter(pk=racun.pk).exists())

    def test_bez_dozvole(self):
        drugi = get_user_model().objects.create_user("bez", password="x")
        self.client.force_login(drugi)
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_putni_nalozi")).status_code, 403)
        self.assertEqual(self.client.get(reverse("isplate:putni_nalozi_pravdanje")).status_code, 403)
        self.assertEqual(self.ocitaj().status_code, 403)
        self.assertEqual(Decimal("0"), sum((r.iznos for r in FiskalniRacun.objects.all()), Decimal("0")))


class OdvojeniPrikaziTests(TestCase):
    """Ista tabela, odvojeni prikazi: Nabavka, putni nalozi i ostali (gotovinski) fiskalni računi."""

    OSTALI = ("isplate:fiskalni_ostali", "isplate:fiskalni_ostali_ucitaj", "isplate:fiskalni_ostali_izvoz")

    def setUp(self):
        self.nalog = create_order(employee=create_employee(), order_number="43/2026-9", center="43")
        self.blagajna = korisnik_sa("blagajna-test", *self.OSTALI, *PRAVDANJE, *ISPLATE)
        self.nabavka = get_user_model().objects.create_superuser("nabavka-test", password="x")

    def ucitaj(self, korisnik, ruta, podaci, *args):
        self.client.force_login(korisnik)
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            return self.client.post(reverse(ruta, args=args), podaci, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_svaki_prikaz_vidi_samo_svoje_racune(self):
        sifra = self.nalog.job_code
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            fiskalni.upisi(napravi_link(brojac=1), sifra, self.nabavka, "nabavka")
        odgovor = self.ucitaj(self.blagajna, "isplate:fiskalni_ostali_ucitaj",
                              {"job_code": sifra.pk, "link": napravi_link(brojac=2), "napomena": "gotovina"})
        self.assertTrue(odgovor.json()["ok"])  # prozor „Učitaj račun” dobija JSON
        self.ucitaj(self.blagajna, "isplate:putni_nalog_racun_dodaj", {"link": napravi_link(brojac=3)}, self.nalog.pk)
        FiskalniRacun.objects.filter(putni_nalog=self.nalog).update(napomena="nalog")
        self.assertEqual(FiskalniRacun.objects.get(napomena="gotovina").evidencija, FiskalniRacun.Evidencija.GOTOVINA)

        self.client.force_login(self.nabavka)
        nabavka = self.client.get(reverse("nabavka:fiskalni_data"), {"draw": 1}).json()
        self.assertEqual(nabavka["recordsTotal"], 1)
        self.client.force_login(self.blagajna)
        ostali = self.client.get(reverse("isplate:fiskalni_ostali"), {"draw": 1, "knjizenje": "sve"}).json()
        self.assertEqual((ostali["recordsTotal"], ostali["data"][0]["veza"]), (1, "gotovina"))
        putni = self.client.get(reverse("isplate:fiskalni_putni_nalozi"), {"draw": 1, "knjizenje": "sve"}).json()
        self.assertEqual(putni["recordsTotal"], 1)
        self.assertIn("43/2026-9", putni["data"][0]["veza"])
        stranica = self.client.get(reverse("isplate:fiskalni_ostali"))
        self.assertContains(stranica, "Učitaj račun")
        self.assertContains(stranica, "<th>Napomena</th>", html=True)
        self.assertContains(self.client.get(reverse("isplate:fiskalni_putni_nalozi")), "<th>Putni nalog</th>", html=True)

    def test_skinut_sa_naloga_vraca_se_u_svoju_evidenciju(self):
        sifra = self.nalog.job_code
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            iz_nabavke, _ = fiskalni.upisi(napravi_link(brojac=4), sifra, self.nabavka)
        self.ucitaj(self.blagajna, "isplate:putni_nalog_racun_dodaj", {"link": napravi_link(brojac=4)}, self.nalog.pk)
        self.ucitaj(self.blagajna, "isplate:putni_nalog_racun_dodaj", {"link": napravi_link(brojac=5)}, self.nalog.pk)
        sa_naloga = FiskalniRacun.objects.exclude(pk=iz_nabavke.pk).get()
        for racun in (iz_nabavke, sa_naloga):
            racun.refresh_from_db()
            fiskalni.odvezi_od_putnog_naloga(racun)
        self.assertEqual(FiskalniRacun.objects.get(pk=iz_nabavke.pk).evidencija, FiskalniRacun.Evidencija.NABAVKA)
        self.assertEqual(FiskalniRacun.objects.get(pk=sa_naloga.pk).evidencija, FiskalniRacun.Evidencija.GOTOVINA)
        self.client.force_login(self.nabavka)
        detalj = self.client.get(reverse("nabavka:fiskalni_detail", args=[sa_naloga.pk]))
        self.assertContains(detalj, "Isplate → Ostali fiskalni računi")

    def test_knjizenje_izvoz_i_dupli_racun(self):
        sifra = self.nalog.job_code
        self.ucitaj(self.blagajna, "isplate:fiskalni_ostali_ucitaj",
                    {"job_code": sifra.pk, "link": napravi_link(brojac=6), "napomena": "kancelarijski"})
        racun = FiskalniRacun.objects.get()
        knjizenje.posalji(racun, self.blagajna)
        knjizenje.proknjizi([racun], self.blagajna, timezone.localdate())
        self.assertTrue(FiskalniRacun.objects.get(pk=racun.pk).proknjizeno)
        izvoz = self.client.get(reverse("isplate:fiskalni_ostali_izvoz"), {"knjizenje": "sve"})
        self.assertIn("spreadsheetml", izvoz["Content-Type"])
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            with self.assertRaisesMessage(fiskalni.GreskaOcitavanja, "Isplate → Ostali fiskalni računi"):
                fiskalni.upisi(napravi_link(brojac=6), sifra, self.nabavka)


class DetaljIKnjizenjeTests(TestCase):
    """Detalj računa u Isplatama, interni broj, slanje na knjiženje i povratak sa knjiženja na doradu (07.10.2026.)."""

    OSTALI = ("isplate:fiskalni_ostali", "isplate:fiskalni_ostali_ucitaj")

    def setUp(self):
        self.nalog = create_order(employee=create_employee(), order_number="43/2026-21", center="43")
        self.blagajna = korisnik_sa("blagajna-det", *self.OSTALI, *PRAVDANJE, *ISPLATE)
        self.knjigovodja = korisnik_sa("knjigovodja-det", *KNJIZENJE)
        self.client.force_login(self.blagajna)

    def ucitaj_ostali(self, brojac=31, **podaci):
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            return self.client.post(reverse("isplate:fiskalni_ostali_ucitaj"),
                                    {"link": napravi_link(brojac=brojac), **podaci}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_ucitavanje_vraca_detalj_sa_internim_brojem_i_bez_sifre(self):
        odgovor = self.ucitaj_ostali(interni_broj="IR-15/2026").json()
        racun = FiskalniRacun.objects.get()
        self.assertEqual(odgovor["detalj"], reverse("isplate:fiskalni_detail", args=[racun.pk]))
        self.assertEqual((racun.interni_broj, racun.job_code_id), ("IR-15/2026", None))
        detalj = self.client.get(odgovor["detalj"])
        self.assertContains(detalj, "IR-15/2026")
        self.assertContains(detalj, "Pošalji na knjiženje")
        self.assertNotContains(detalj, "Garaža")
        # bez AJAX-a: preusmerenje na detalj
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            odgovor = self.client.post(reverse("isplate:fiskalni_ostali_ucitaj"), {"link": napravi_link(brojac=32)})
        self.assertRedirects(odgovor, reverse("isplate:fiskalni_detail", args=[FiskalniRacun.objects.latest("pk").pk]),
                             fetch_redirect_response=False)

    def vozilo_naloga(self, sifra):
        import datetime
        from decimal import Decimal

        from fleet.models import JobCode, Vehicle

        vozilo = Vehicle.objects.create(
            inventory_number="INV-PN", chassis_number="SAS-PN", brand="Škoda", model="Octavia", year_of_manufacture=2020,
            first_registration_date=datetime.date(2020, 1, 1), color="Siva", number_of_axles=2,
            engine_volume=Decimal("1598.00"), engine_number="MOT-PN", weight=Decimal("1300.00"), engine_power=Decimal("85.00"),
            load_capacity=Decimal("500.00"), category=Vehicle.Category.CARGO, maximum_permissible_weight=Decimal("1900.00"),
            fuel_type="DIZEL", number_of_seats=5, purchase_value=Decimal("10000.00"), value=Decimal("9000.00"))
        JobCode.objects.create(vehicle=vozilo, organizational_unit=sifra, assigned_date=datetime.date(2026, 1, 1))
        self.nalog.vehicle = vozilo
        self.nalog.save(update_fields=["vehicle"])

    def test_racun_naloga_sifra_prema_vozilu_broj_i_detalj(self):
        sifra_vozila = OrganizationalUnit.objects.create(code="430077", name="Vozni park 43", center="43")
        self.vozilo_naloga(sifra_vozila)
        prozor = self.client.get(reverse("isplate:putni_nalog_racuni", args=[self.nalog.pk])).json()
        self.assertEqual((prozor["predlog"]["id"], prozor["predlog"]["izvor"]), (sifra_vozila.pk, "vozilo"))
        self.assertContains(self.client.get(reverse("isplate:putni_nalozi_pravdanje")), 'id="ispRacun_job_code"')
        self.assertNotContains(self.client.get(reverse("isplate:putni_nalozi_pravdanje")), "Nalog još nema računa")

        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):  # bez izbora: šifra prema vozilu
            odgovor = self.client.post(reverse("isplate:putni_nalog_racun_dodaj", args=[self.nalog.pk]),
                                       {"link": napravi_link(brojac=33), "interni_broj": "PN-5"},
                                       HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
        racun = FiskalniRacun.objects.get()
        self.assertEqual(odgovor["detalj"], reverse("isplate:fiskalni_detail", args=[racun.pk]))
        self.assertEqual((racun.job_code, racun.interni_broj, racun.putni_nalog), (sifra_vozila, "PN-5", self.nalog))
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):  # izabrana šifra ima prednost
            self.client.post(reverse("isplate:putni_nalog_racun_dodaj", args=[self.nalog.pk]),
                             {"link": napravi_link(brojac=34), "job_code": self.nalog.job_code.pk},
                             HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(FiskalniRacun.objects.exclude(pk=racun.pk).get().job_code, self.nalog.job_code)

        nazad = reverse("isplate:putni_nalozi_pravdanje") + "?status=svi"
        detalj = self.client.get(odgovor["detalj"], {"nazad": nazad})
        self.assertContains(detalj, "43/2026-21")
        self.assertContains(detalj, 'name="interni_broj"')
        self.assertContains(detalj, 'name="job_code"')
        self.assertContains(detalj, "Tekst računa")  # izgled računa kao u Nabavci
        self.assertContains(detalj, "Skini sa putnog naloga")
        self.assertNotContains(detalj, "Garaža")
        self.assertEqual(detalj.context["nazad"], nazad)
        self.assertEqual(self.client.get(odgovor["detalj"], {"nazad": "https://drugi.sajt/"}).context["nazad"],
                         reverse("isplate:fiskalni_putni_nalozi"))
        izmena = self.client.post(reverse("isplate:fiskalni_izmena", args=[racun.pk]) + "?nazad=" + nazad,
                                  {"job_code": sifra_vozila.pk, "interni_broj": "PN-6", "napomena": "gorivo"})
        self.assertRedirects(izmena, odgovor["detalj"] + "?nazad=" + quote(nazad), fetch_redirect_response=False)
        racun.refresh_from_db()
        self.assertEqual((racun.interni_broj, racun.napomena), ("PN-6", "gorivo"))

    def test_izmena_slanje_zakljucavanje_i_dorada(self):
        self.ucitaj_ostali()
        racun = FiskalniRacun.objects.get()
        sifra = self.nalog.job_code
        self.client.post(reverse("isplate:fiskalni_izmena", args=[racun.pk]),
                         {"job_code": sifra.pk, "interni_broj": "IR-7", "napomena": "papir"})
        racun.refresh_from_db()
        self.assertEqual((racun.job_code, racun.interni_broj, racun.napomena), (sifra, "IR-7", "papir"))

        self.client.post(reverse("isplate:fiskalni_posalji", args=[racun.pk]))
        z = KnjizenjeRacuna.objects.get(racun=racun)
        self.assertEqual((z.status, z.poslao), (KnjizenjeRacuna.Status.POSLATO, self.blagajna))
        self.assertIsNotNone(z.poslato_at)
        self.client.post(reverse("isplate:fiskalni_izmena", args=[racun.pk]), {"interni_broj": "promena"})
        racun.refresh_from_db()
        self.assertEqual(racun.interni_broj, "IR-7")  # poslat račun se ne menja
        detalj = self.client.get(reverse("isplate:fiskalni_detail", args=[racun.pk]))
        self.assertNotContains(detalj, 'action="%s"' % reverse("isplate:fiskalni_posalji", args=[racun.pk]))
        self.assertNotContains(detalj, "Povuci")
        odgovor = self.client.post(reverse("isplate:fiskalni_posalji", args=[racun.pk]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(odgovor.status_code, 400)  # već poslat
        # Isplate ne knjiže: modul Knjiženje im nije dostupan
        for ruta, args in (("knjizenje:racuni", []), ("knjizenje:racun", [racun.pk])):
            self.assertEqual(self.client.get(reverse(ruta, args=args)).status_code, 403)
        self.assertEqual(self.client.post(reverse("knjizenje:proknjizi"), {"racuni": [racun.pk], "datum": "2026-10-07"}).status_code, 403)
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_ostali"), {"knjizenje": "neposlato"}).context["zbir"]["broj"], 0)

        # Knjiženje vraća na doradu — Isplate vide razlog, menjaju i šalju ponovo.
        self.client.force_login(self.knjigovodja)
        self.client.post(reverse("knjizenje:vrati", args=[racun.pk]), {"razlog": "Nedostaje šifra centra"})
        self.client.force_login(self.blagajna)
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_ostali"), {"knjizenje": "vraceno"}).context["zbir"]["broj"], 1)
        self.assertEqual(self.client.get(reverse("isplate:fiskalni_ostali"), {"knjizenje": "neposlato"}).context["zbir"]["broj"], 1)
        detalj = self.client.get(reverse("isplate:fiskalni_detail", args=[racun.pk]))
        self.assertContains(detalj, "Nedostaje šifra centra")
        self.assertContains(detalj, "Pošalji ponovo")
        self.client.post(reverse("isplate:fiskalni_izmena", args=[racun.pk]), {"job_code": sifra.pk, "interni_broj": "IR-8"})
        racun.refresh_from_db()
        self.assertEqual(racun.interni_broj, "IR-8")
        self.client.post(reverse("isplate:fiskalni_posalji", args=[racun.pk]))
        self.assertEqual(KnjizenjeRacuna.objects.get(racun=racun).status, KnjizenjeRacuna.Status.POSLATO)

        self.client.force_login(self.knjigovodja)
        self.client.post(reverse("knjizenje:proknjizi"), {"racuni": [racun.pk], "datum": "2026-10-07"})
        racun.refresh_from_db()
        self.assertTrue(racun.proknjizeno)
        self.client.force_login(self.blagajna)
        self.assertEqual(self.client.post(reverse("isplate:fiskalni_posalji", args=[racun.pk]),
                                          HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 400)

    def test_modul_knjizenje_u_meniju_samo_sa_dozvolom(self):
        meni = f'href="{reverse("switch_app", args=["knjizenje"])}'
        self.assertNotContains(self.client.get(reverse("isplate:fiskalni_ostali")), meni)
        self.client.force_login(korisnik_sa("oba", *self.OSTALI, *KNJIZENJE))
        self.assertContains(self.client.get(reverse("isplate:fiskalni_ostali")), meni)


class OstecenQrKodTests(TestCase):
    """QR kod je oštećen: podaci sa računa + QR očitan sa stranice provere Poreske uprave moraju da se poklope."""

    def setUp(self):
        from django.utils import timezone

        self.nalog = create_order(employee=create_employee(), order_number="43/2026-11", center="43")
        self.korisnik = get_user_model().objects.create_superuser("rucno", password="x")
        self.client.force_login(self.korisnik)
        self.link = napravi_link(brojac=31)
        z = fiskalni.ocitaj_link(self.link)
        vreme = timezone.localtime(z.pfr_vreme)
        self.unos = {"rucno_broj": z.broj_racuna.lower(), "rucno_brojac": f"{z.brojac_vrste}/{z.brojac_ukupno}",
                     "rucno_iznos": f"{z.iznos}".replace(".", ","), "rucno_vreme": f"{vreme.day}.{vreme.month}.{vreme.year}. {vreme:%H:%M}"}

    def posalji(self, ruta, podaci, *args):
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            return self.client.post(reverse(ruta, args=args), podaci, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_provera_podataka(self):
        z = fiskalni.ocitaj_link(self.link)
        self.assertIsNone(fiskalni.ocekivano_iz_zahteva({}))
        fiskalni.proveri_ocekivano(z, fiskalni.ocekivano_iz_zahteva(self.unos))  # poklapa se
        for kljuc, losa in (("rucno_iznos", "9,99"), ("rucno_brojac", "1/2"), ("rucno_broj", "X-Y-1"), ("rucno_vreme", "1.1.2026. 08:00")):
            with self.assertRaises(fiskalni.GreskaOcitavanja):
                fiskalni.proveri_ocekivano(z, fiskalni.ocekivano_iz_zahteva({**self.unos, kljuc: losa}))
        with self.assertRaisesMessage(fiskalni.GreskaOcitavanja, "PFR vreme"):
            fiskalni.ocekivano_iz_zahteva({**self.unos, "rucno_vreme": "juče"})

    def test_sva_tri_mesta_upisuju_samo_kad_se_poklapa(self):
        sifra = self.nalog.job_code
        pogresno = {**self.unos, "rucno_iznos": "1,00"}
        odgovor = self.posalji("isplate:fiskalni_ostali_ucitaj", {"job_code": sifra.pk, "link": self.link, **pogresno})
        self.assertEqual(odgovor.status_code, 400)
        self.assertIn("ukupan iznos", odgovor.json()["poruka"])
        self.assertEqual(self.posalji("nabavka:fiskalni_scan", {"job_code": sifra.pk, "link": self.link, **pogresno}).status_code, 400)
        self.assertEqual(self.posalji("isplate:putni_nalog_racun_dodaj", {"link": self.link, **pogresno}, self.nalog.pk).status_code, 400)
        self.assertFalse(FiskalniRacun.objects.exists())

        odgovor = self.posalji("isplate:fiskalni_ostali_ucitaj", {"job_code": sifra.pk, "link": self.link, "napomena": "gotovina", **self.unos})
        self.assertTrue(odgovor.json()["ok"], odgovor.content)
        racun = FiskalniRacun.objects.get()
        self.assertEqual((racun.evidencija, racun.status, racun.napomena), (FiskalniRacun.Evidencija.GOTOVINA, racun.Status.POTVRDJEN, "gotovina"))
        self.assertTrue(racun.stavke.exists())  # stavke preuzete kao kod skeniranja

    def test_prozori_imaju_dugme_za_osteceni_qr(self):
        for ruta in ("nabavka:fiskalni_list", "isplate:fiskalni_ostali", "isplate:putni_nalozi_pravdanje"):
            stranica = self.client.get(reverse(ruta))
            self.assertContains(stranica, "QR kod je oštećen?", msg_prefix=ruta)
            self.assertContains(stranica, "js-fiskalni-rucno", msg_prefix=ruta)
            self.assertContains(stranica, "https://suf.purs.gov.rs/verify", msg_prefix=ruta)
        ostali = self.client.get(reverse("isplate:fiskalni_ostali"))
        self.assertContains(ostali, 'id="ispOstaliModal"')
        self.assertContains(ostali, 'data-bs-target="#ispOstaliModal"')
