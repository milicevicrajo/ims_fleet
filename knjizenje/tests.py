"""Modul Knjiženje (07.10.2026.): knjiženje fiskalnih računa koje šalju Isplate."""
import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import PermissionCode, Role
from core.permissions import sync_permission_codes
from isplate.test_fiskalni import KNJIZENJE, korisnik_sa
from isplate.tests import create_employee, create_order
from nabavka.models import FiskalniRacun
from nabavka.services import fiskalni
from nabavka.test_fiskalni import lazni_suf, napravi_link

from . import services
from .models import DogadjajKnjizenja, KnjizenjeRacuna

Status = KnjizenjeRacuna.Status


class KnjizenjeTests(TestCase):
    def setUp(self):
        self.nalog = create_order(employee=create_employee(), order_number="43/2026-31", center="43")
        self.blagajna = get_user_model().objects.create_user("blagajna-knj", password="x")
        self.knjigovodja = korisnik_sa("knjigovodja", *KNJIZENJE)
        self.client.force_login(self.knjigovodja)

    def racun(self, brojac, nalog=False, posalji=True):
        with mock.patch.object(fiskalni, "_otvori", side_effect=lazni_suf):
            racun, _ = fiskalni.upisi(napravi_link(brojac=brojac), self.nalog.job_code, self.blagajna, "kancelarija",
                                      evidencija=FiskalniRacun.Evidencija.GOTOVINA)
        if nalog:
            racun.putni_nalog = self.nalog
            racun.save(update_fields=["putni_nalog"])
        if posalji:
            services.posalji(racun, self.blagajna)
        return FiskalniRacun.objects.get(pk=racun.pk)

    def tabela(self, **filteri):
        return self.client.get(reverse("knjizenje:racuni"), {"draw": 1, **filteri}).json()

    def test_spisak_vidi_samo_poslate_a_stampa_proknjizava(self):
        prvi, drugi = self.racun(1), self.racun(2, nalog=True)
        self.racun(3, posalji=False)  # nije poslat — Knjiženje ga ne vidi
        strana = self.client.get(reverse("knjizenje:racuni"))
        self.assertEqual(strana.status_code, 200)
        self.assertEqual(strana.context["plocice"]["ceka"]["broj"], 2)
        podaci = self.tabela()
        self.assertEqual((podaci["recordsTotal"], podaci["recordsFiltered"]), (2, 2))
        self.assertTrue(all("knj-izbor" in red["izbor"] for red in podaci["data"]))
        self.assertEqual(self.tabela(vrsta="nalog")["recordsFiltered"], 1)

        # Spisak: putni nalog i šifra posla (sa nazivom) u svojim kolonama.
        red_naloga = next(r for r in podaci["data"] if "43/2026-31" in r["veza"])
        self.assertIn("Putni nalog", red_naloga["veza"])
        self.assertIn(self.nalog.job_code.code, red_naloga["sifra"])

        # Od 08.10.2026. nema ručnog knjiženja: štampa proknjižava (knjiži se u drugom programu).
        danas = timezone.localdate()
        odgovor = self.client.post(reverse("knjizenje:stampaj"), {"racuni": [prvi.pk, drugi.pk]})
        stampa = reverse("knjizenje:stampa") + f"?racuni={prvi.pk},{drugi.pk}"
        self.assertRedirects(odgovor, stampa, fetch_redirect_response=False)
        for racun in (prvi, drugi):
            racun.refresh_from_db()
            z = racun.knjizenje
            self.assertTrue(racun.proknjizeno)
            self.assertEqual((z.status, z.datum_knjizenja, z.napomena, z.knjizio, z.stampao, z.broj_stampanja),
                             (Status.PROKNJIZENO, danas, services.NAPOMENA_STAMPE, self.knjigovodja, self.knjigovodja, 1))
            self.assertEqual(sorted(z.dogadjaji.values_list("vrsta", flat=True)),
                             sorted([DogadjajKnjizenja.Vrsta.STAMPANO, DogadjajKnjizenja.Vrsta.PROKNJIZENO,
                                     DogadjajKnjizenja.Vrsta.POSLATO]))
        strana = self.client.get(stampa)
        for tekst in ("FISKALNI RAČUN ZA KNJIŽENJE", "Institut za ispitivanje materijala", prvi.broj_racuna,
                      drugi.broj_racuna, self.nalog.job_code.code, "43/2026-31", "Štampao", "knjigovodja", "Učitao",
                      "blagajna-knj", "Poslao na knjiženje"):
            self.assertContains(strana, tekst)
        self.assertEqual(self.tabela()["recordsFiltered"], 0)
        self.assertEqual(self.tabela(status="proknjizeno")["recordsFiltered"], 2)
        self.assertEqual(self.tabela(status="proknjizeno", knjizeno_od=str(danas + datetime.timedelta(days=1)))["recordsFiltered"], 0)
        # ponovna štampa ne menja knjiženje, samo se broji
        self.client.post(reverse("knjizenje:stampaj"), {"racuni": [prvi.pk]})
        prvi.refresh_from_db()
        self.assertEqual((prvi.knjizenje.datum_knjizenja, prvi.knjizenje.broj_stampanja), (danas, 2))
        self.assertEqual(prvi.knjizenje.dogadjaji.filter(vrsta=DogadjajKnjizenja.Vrsta.PROKNJIZENO).count(), 1)
        izvoz = self.client.get(reverse("knjizenje:izvoz"), {"status": "sve"})
        self.assertIn("spreadsheetml", izvoz["Content-Type"])

    def test_vracanje_na_doradu_trazi_razlog(self):
        racun = self.racun(4)
        self.client.post(reverse("knjizenje:vrati", args=[racun.pk]), {"razlog": "  "})
        self.assertEqual(KnjizenjeRacuna.objects.get(racun=racun).status, Status.POSLATO)
        self.client.post(reverse("knjizenje:vrati", args=[racun.pk]), {"razlog": "Pogrešna šifra posla"})
        z = KnjizenjeRacuna.objects.get(racun=racun)
        self.assertEqual((z.status, z.razlog_vracanja, z.vratio), (Status.VRACENO, "Pogrešna šifra posla", self.knjigovodja))
        self.assertEqual(self.tabela(status="vraceno")["recordsFiltered"], 1)
        self.assertIn("Pogrešna šifra posla", self.tabela(status="vraceno")["data"][0]["status"])
        self.assertEqual(self.tabela()["recordsFiltered"], 0)
        # vraćen račun se ne štampa (ni ne knjiži) dok ga Isplate ne pošalju ponovo
        self.client.post(reverse("knjizenje:stampaj"), {"racuni": [racun.pk]})
        self.assertFalse(FiskalniRacun.objects.get(pk=racun.pk).proknjizeno)
        services.posalji(FiskalniRacun.objects.get(pk=racun.pk), self.blagajna)
        self.assertEqual(self.tabela()["recordsFiltered"], 1)

    def test_detalj_istorija_i_ponistavanje(self):
        racun = self.racun(5, nalog=True)
        detalj = self.client.get(reverse("knjizenje:racun", args=[racun.pk]))
        self.assertContains(detalj, "43/2026-31")
        self.assertContains(detalj, "Štampaj i proknjiži")
        self.assertNotContains(detalj, "Broj naloga za knjiženje")  # ručno knjiženje je ugašeno
        self.assertContains(detalj, "Vrati na doradu")
        # Potpuni podaci o računu, kao u Isplatama i Nabavci: kasir i ESIR, tekst računa, upozorenja.
        self.assertContains(detalj, "kasir.test · 644/20.1")
        self.assertContains(detalj, "Tekst računa")
        self.assertContains(detalj, "Касир:")
        self.assertContains(detalj, "Račun NIJE izdat na IMS")
        self.assertContains(detalj, "Šifra posla naloga")
        self.client.post(reverse("knjizenje:stampaj"), {"racuni": [racun.pk]})
        detalj = self.client.get(reverse("knjizenje:racun", args=[racun.pk]))
        self.assertContains(detalj, "Štampaj ponovo")
        self.assertContains(detalj, "Odštampano")  # istorija
        self.assertContains(detalj, "Poništi knjiženje")
        self.client.post(reverse("knjizenje:ponisti", args=[racun.pk]), {"razlog": ""})
        self.assertTrue(FiskalniRacun.objects.get(pk=racun.pk).proknjizeno)  # bez razloga se ne poništava
        self.client.post(reverse("knjizenje:ponisti", args=[racun.pk]), {"razlog": "pogrešan datum"})
        racun.refresh_from_db()
        self.assertFalse(racun.proknjizeno)
        self.assertEqual((racun.knjizenje.status, racun.knjizenje.datum_knjizenja), (Status.POSLATO, None))
        detalj = self.client.get(reverse("knjizenje:racun", args=[racun.pk]))
        self.assertContains(detalj, "Poništeno knjiženje")
        self.assertContains(detalj, "pogrešan datum")

    def test_racun_proknjizen_pre_modula(self):
        racun = self.racun(6, posalji=False)
        fiskalni.oznaci_proknjizeno(racun, self.blagajna)  # oznaka iz Isplata, pre 07.10.2026.
        self.assertEqual(self.tabela(status="proknjizeno")["recordsFiltered"], 1)
        self.assertContains(self.client.get(reverse("knjizenje:racun", args=[racun.pk])), "istorija nije vođena")
        self.client.post(reverse("knjizenje:ponisti", args=[racun.pk]), {"razlog": "ispravka"})
        self.assertEqual(KnjizenjeRacuna.objects.get(racun=racun).status, Status.POSLATO)

    def test_neposlat_racun_nije_dostupan(self):
        racun = self.racun(7, posalji=False)
        self.assertEqual(self.client.get(reverse("knjizenje:racun", args=[racun.pk])).status_code, 404)

    def test_bez_dozvole(self):
        racun = self.racun(8)
        self.client.force_login(korisnik_sa("blagajnik", "isplate:fiskalni_ostali", "isplate:fiskalni_posalji"))
        self.assertEqual(self.client.get(reverse("knjizenje:racuni")).status_code, 403)
        self.assertEqual(self.client.post(reverse("knjizenje:stampaj"), {"racuni": [racun.pk]}).status_code, 403)
        self.assertEqual(self.client.get(reverse("knjizenje:stampa"), {"racuni": racun.pk}).status_code, 403)
        self.assertFalse(FiskalniRacun.objects.get(pk=racun.pk).proknjizeno)


class DozvoleKnjizenjaTests(TestCase):
    def test_uloga_knjizenje_dobija_samo_kodove_modula(self):
        sync_permission_codes()
        uloga = Role.objects.get(slug="knjizenje")
        kodovi = set(uloga.permissions.values_list("code", flat=True))
        from knjizenje.gorivo import KODOVI
        self.assertEqual(kodovi, set(KNJIZENJE) | set(KODOVI))  # i izveštaji o gorivu (od 08.10.2026.)
        blagajna = set(Role.objects.get(slug="blagajna").permissions.values_list("code", flat=True))
        self.assertIn("isplate:fiskalni_posalji", blagajna)
        self.assertFalse(any(k.startswith("knjizenje:") for k in blagajna))
        self.assertTrue(PermissionCode.objects.filter(code="knjizenje:stampaj",
                                                      role_permissions__role__slug="uprava").exists())


class GorivoUMenijuTests(TestCase):
    def test_meni_knjizenja_ima_izvestaje_o_gorivu_po_dozvoli(self):
        from knjizenje.gorivo import meni

        korisnik = korisnik_sa("gorivo-nis", "knjizenje:racuni", "fuel_job_code_nis_putnicka", "fuel_job_code_omv_teretna")
        self.assertEqual([s["naziv"] for s in meni(korisnik)], ["NIS — putnička", "OMV — teretna"])
        self.client.force_login(korisnik)
        self.client.get(reverse("switch_app", args=["knjizenje"]))
        strana = self.client.get(reverse("knjizenje:racuni"))
        self.assertContains(strana, "Gorivo — izveštaji")
        self.assertContains(strana, reverse("fuel_job_code_nis_putnicka"))
        self.assertNotContains(strana, reverse("fuel_job_code_nis_teretna"))
