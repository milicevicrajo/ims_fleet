"""Spiskovi Nabavke: podrazumevano od najnovijeg ka najstarijem."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from fleet.models import OrganizationalUnit
from nabavka.models import ProcurementCase


class RedosledPredmetaTests(TestCase):
    def test_predmeti_od_najnovijeg_bez_obzira_na_prefiks_broja(self):
        korisnik = get_user_model().objects.create_superuser("nabavka-sort", password="x")
        self.client.force_login(korisnik)
        sifra = OrganizationalUnit.objects.create(code="410001", name="A", center="41")
        stariji = ProcurementCase.objects.create(title="Stariji", job_code=sifra, case_type="usluga", is_garage=True)  # ZUG-…
        noviji = ProcurementCase.objects.create(title="Noviji", job_code=sifra, case_type="nabavka")  # ZN-…
        for parametri in ({}, {"order[0][column]": "0", "order[0][dir]": "desc"}):
            redovi = self.client.get(reverse("nabavka:case_data"), {"draw": 1, "start": 0, "length": 10, **parametri}).json()["data"]
            self.assertIn(noviji.case_number, redovi[0]["case_number"])
            self.assertIn(stariji.case_number, redovi[1]["case_number"])
