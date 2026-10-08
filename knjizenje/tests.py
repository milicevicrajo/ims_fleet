"""Modul Knjiženje (07.10.2026.): knjiženje fiskalnih računa koje šalju Isplate."""
import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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

    def test_spisak_vidi_samo_poslate_i_knjizi_vise_racuna_odjednom(self):
        prvi, drugi = self.racun(1), self.racun(2, nalog=True)
        self.racun(3, posalji=False)  # nije poslat — Knjiženje ga ne vidi
        strana = self.client.get(reverse("knjizenje:racuni"))
        self.assertEqual(strana.status_code, 200)
        self.assertEqual(strana.context["plocice"]["ceka"]["broj"], 2)
        podaci = self.tabela()
        self.assertEqual((podaci["recordsTotal"], podaci["recordsFiltered"]), (2, 2))
        self.assertTrue(all("knj-izbor" in red["izbor"] for red in podaci["data"]))
        self.assertEqual(self.tabela(vrsta="nalog")["recordsFiltered"], 1)

        odgovor = self.client.post(reverse("knjizenje:proknjizi"), {
            "racuni": [prvi.pk, drugi.pk], "datum": "2026-10-06", "broj_naloga": "TN-44", "napomena": "blagajna oktobar",
            "nazad": reverse("knjizenje:racuni") + "?status=ceka"})
        self.assertRedirects(odgovor, reverse("knjizenje:racuni") + "?status=ceka", fetch_redirect_response=False)
        for racun in (prvi, drugi):
            racun.refresh_from_db()
            z = racun.knjizenje
            self.assertTrue(racun.proknjizeno)
            self.assertEqual((z.status, z.datum_knjizenja, z.broj_naloga, z.napomena, z.knjizio),
                             (Status.PROKNJIZENO, datetime.date(2026, 10, 6), "TN-44", "blagajna oktobar", self.knjigovodja))
            self.assertEqual(list(z.dogadjaji.values_list("vrsta", flat=True)),
                             [DogadjajKnjizenja.Vrsta.PROKNJIZENO, DogadjajKnjizenja.Vrsta.POSLATO])
        self.assertEqual(self.tabela()["recordsFiltered"], 0)
        proknjizeni = self.tabela(status="proknjizeno")
        self.assertEqual(proknjizeni["recordsFiltered"], 2)
        self.assertIn("TN-44", proknjizeni["data"][0]["status"])
        self.assertEqual(self.tabela(status="proknjizeno", **{"search[value]": "TN-44"})["recordsFiltered"], 2)
        self.assertEqual(self.tabela(status="proknjizeno", knjizeno_od="2026-10-07")["recordsFiltered"], 0)
        # ponovo se ne knjiži
        self.client.post(reverse("knjizenje:proknjizi"), {"racuni": [prvi.pk], "datum": "2026-10-07"})
        prvi.refresh_from_db()
        self.assertEqual(prvi.knjizenje.datum_knjizenja, datetime.date(2026, 10, 6))
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
        # vraćen račun se ne knjiži dok ga Isplate ne pošalju ponovo
        self.client.post(reverse("knjizenje:proknjizi"), {"racuni": [racun.pk], "datum": "2026-10-07"})
        self.assertFalse(FiskalniRacun.objects.get(pk=racun.pk).proknjizeno)
        services.posalji(FiskalniRacun.objects.get(pk=racun.pk), self.blagajna)
        self.assertEqual(self.tabela()["recordsFiltered"], 1)

    def test_detalj_istorija_i_ponistavanje(self):
        racun = self.racun(5, nalog=True)
        detalj = self.client.get(reverse("knjizenje:racun", args=[racun.pk]))
        self.assertContains(detalj, "43/2026-31")
        self.assertContains(detalj, "Proknjiži")
        self.assertContains(detalj, "Vrati na doradu")
        # Potpuni podaci o računu, kao u Isplatama i Nabavci: kasir i ESIR, tekst računa, upozorenja.
        self.assertContains(detalj, "kasir.test · 644/20.1")
        self.assertContains(detalj, "Tekst računa")
        self.assertContains(detalj, "Касир:")
        self.assertContains(detalj, "Račun NIJE izdat na IMS")
        self.assertContains(detalj, "Šifra posla naloga")
        self.client.post(reverse("knjizenje:proknjizi"), {"racuni": [racun.pk], "datum": "2026-10-07", "broj_naloga": "TN-1",
                                                          "nazad": reverse("knjizenje:racun", args=[racun.pk])})
        detalj = self.client.get(reverse("knjizenje:racun", args=[racun.pk]))
        self.assertContains(detalj, "TN-1")
        self.assertContains(detalj, "Poništi knjiženje")
        self.client.post(reverse("knjizenje:ponisti", args=[racun.pk]), {"razlog": ""})
        self.assertTrue(FiskalniRacun.objects.get(pk=racun.pk).proknjizeno)  # bez razloga se ne poništava
        self.client.post(reverse("knjizenje:ponisti", args=[racun.pk]), {"razlog": "pogrešan datum"})
        racun.refresh_from_db()
        self.assertFalse(racun.proknjizeno)
        self.assertEqual((racun.knjizenje.status, racun.knjizenje.broj_naloga), (Status.POSLATO, ""))
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
        self.assertEqual(self.client.post(reverse("knjizenje:proknjizi"), {"racuni": [racun.pk], "datum": "2026-10-07"}).status_code, 403)
        self.assertFalse(FiskalniRacun.objects.get(pk=racun.pk).proknjizeno)


class DozvoleKnjizenjaTests(TestCase):
    def test_uloga_knjizenje_dobija_samo_kodove_modula(self):
        sync_permission_codes()
        uloga = Role.objects.get(slug="knjizenje")
        kodovi = set(uloga.permissions.values_list("code", flat=True))
        self.assertEqual(kodovi, set(KNJIZENJE))
        blagajna = set(Role.objects.get(slug="blagajna").permissions.values_list("code", flat=True))
        self.assertIn("isplate:fiskalni_posalji", blagajna)
        self.assertFalse(any(k.startswith("knjizenje:") for k in blagajna))
        self.assertTrue(PermissionCode.objects.filter(code="knjizenje:proknjizi",
                                                      role_permissions__role__slug="uprava").exists())
