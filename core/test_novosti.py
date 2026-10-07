"""Novosti po modulu: obaveštenje pri ulasku u modul dok korisnik ne potvrdi „Razumem” (od 07.10.2026.)."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from core.models import ProcitanaNovost
from core.novosti import NOVOSTI, modul_zahteva

NASLOV = "Šta je novo u modulu"


class NovostiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("novosti", "novosti@example.invalid", "x")
        self.client.force_login(self.user)

    def test_svaki_modul_ima_jedinstven_kljuc(self):
        kljucevi = [n["kljuc"] for n in NOVOSTI]
        self.assertEqual(len(kljucevi), len(set(kljucevi)))
        self.assertEqual({n["modul"] for n in NOVOSTI},
                         {"fleet", "kadrovi", "finansije", "nabavka", "pravna", "potrazivanja", "isplate"})

    def test_modul_po_adresi(self):
        rf = RequestFactory()
        for adresa, sesija, modul in (("/hr/analitika/", "fleet", "kadrovi"), ("/finansije/", "fleet", "finansije"),
                                      ("/nabavka/fiskalni-racuni/", "fleet", "nabavka"), ("/", "fleet", None),
                                      ("/pravna/disciplinski/", "pravna", "pravna")):
            zahtev = rf.get(adresa)
            zahtev.session = {"current_app": sesija}
            self.assertEqual(modul_zahteva(zahtev), modul, adresa)

    def test_obavestenje_do_potvrde(self):
        with patch("hr.analitika_views.analitika", side_effect=lambda *a, **k: {"ukupno": 0}):
            strana = self.client.get(reverse("hr:analitika"))
        self.assertContains(strana, f"{NASLOV} Kadrovi")
        self.assertContains(strana, 'value="2026-10-07-kadrovi"')
        self.assertContains(strana, "Razumem")
        # Razumem (AJAX) → zapis, i obaveštenje se više ne prikazuje
        odgovor = self.client.post(reverse("novosti_procitano"), {"kljuc": ["2026-10-07-kadrovi", "nepostojeci"]},
                                   HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(odgovor.json(), {"ok": True})
        self.assertEqual(list(ProcitanaNovost.objects.values_list("kljuc", flat=True)), ["2026-10-07-kadrovi"])
        with patch("hr.analitika_views.analitika", side_effect=lambda *a, **k: {"ukupno": 0}):
            self.assertNotContains(self.client.get(reverse("hr:analitika")), NASLOV)
        # drugi modul ima svoje obaveštenje
        self.assertContains(self.client.get(reverse("finansije:dashboard")), f"{NASLOV} Finansije")

    def test_bez_javascript_a_vraca_na_stranu_i_pocetna_nema_obavestenje(self):
        odgovor = self.client.post(reverse("novosti_procitano"), {"kljuc": "2026-10-07-finansije", "next": "/finansije/"})
        self.assertRedirects(odgovor, "/finansije/", fetch_redirect_response=False)
        odgovor = self.client.post(reverse("novosti_procitano"), {"kljuc": "2026-10-07-finansije", "next": "https://zlo.example/"})
        self.assertRedirects(odgovor, "/", fetch_redirect_response=False)
        self.assertNotContains(self.client.get(reverse("pocetna")), NASLOV)
