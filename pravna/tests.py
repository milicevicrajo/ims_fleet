from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from core.models import OrganizationalUnit
from hr.models import Employee

from .models import DisciplinskiPostupak, Postupak, PromenaPostupka, TokPostupka


def zaposleni(code, prezime, org_unit_code=""):
    return Employee.objects.create(
        employee_code=code,
        first_name="Ime",
        last_name=prezime,
        position="Referent",
        department_code=1,
        org_unit_code=org_unit_code,
        gender="M",
        date_of_birth=date(1990, 1, 1),
        date_of_joining=date(2020, 1, 1),
    )


class PravnaSelidbaTests(TestCase):
    """Pravna sluzba je presla iz naplate; tabele i podaci ostaju isti."""

    def test_postupak_and_promena_keep_their_legacy_tables(self):
        self.assertEqual(Postupak._meta.db_table, "postupak")
        self.assertEqual(PromenaPostupka._meta.db_table, "promena_postupka")
        self.assertEqual(Postupak._meta.app_label, "pravna")

    def test_old_naplata_routes_are_gone_and_new_ones_answer(self):
        with self.assertRaises(NoReverseMatch):
            reverse("naplata:pravna_cases_list", kwargs={"case_type": "tuzeni"})
        self.assertEqual(reverse("pravna:cases_list", kwargs={"case_type": "tuzeni"}), "/pravna/tuzeni/")
        self.assertEqual(reverse("pravna:disciplinski_lista"), "/pravna/disciplinski/")

    def test_case_list_still_renders_for_every_type(self):
        admin = get_user_model().objects.create_superuser("pravnik", "p@example.com", "test-pass")
        Postupak.objects.create(tip="tuzeni", broj_predmeta="P 1/2026", naziv_partnera="Kupac")
        self.client.force_login(admin)
        for case_type in ("tuzeni", "tuzili", "stecaj", "uppr"):
            response = self.client.get(reverse("pravna:cases_list", kwargs={"case_type": case_type}))
            self.assertEqual(response.status_code, 200, case_type)
        self.assertContains(response, "Pravna služba")

    def test_adding_a_promena_writes_to_the_default_database(self):
        admin = get_user_model().objects.create_superuser("pravnik2", "p2@example.com", "test-pass")
        postupak = Postupak.objects.create(tip="tuzeni", broj_predmeta="P 2/2026")
        self.client.force_login(admin)
        response = self.client.post(
            reverse("pravna:dodaj_promenu", kwargs={"pk": postupak.pk}),
            {"datum": "01.02.2026", "promena": "Rociste odrzano"},
        )
        self.assertRedirects(response, reverse("pravna:detalj", kwargs={"pk": postupak.pk}))
        promena = PromenaPostupka.objects.get(postupak=postupak)
        self.assertEqual(promena.datum, date(2026, 2, 1))
        self.assertEqual(promena.created_by, admin)


class DisciplinskiPostupakTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("kadrovik", "k@example.com", "test-pass")
        OrganizationalUnit.objects.create(name="Laboratorija", code="436111", center="43")
        self.radnik = zaposleni(1001, "Petrovic", org_unit_code="436111")
        self.sef = zaposleni(1002, "Nikolic", org_unit_code="436111")
        self.client.force_login(self.admin)

    def _create(self, **overrides):
        data = {
            "zaposleni": self.radnik.pk,
            "centar": "",
            "datum_podnosenja": "05.03.2026",
            "podnosilac": self.sef.pk,
        }
        data.update(overrides)
        return self.client.post(reverse("pravna:disciplinski_dodaj"), data)

    def test_center_is_taken_from_the_employee_org_unit_and_kept(self):
        response = self._create()
        postupak = DisciplinskiPostupak.objects.get()
        self.assertRedirects(response, reverse("pravna:disciplinski_detalj", kwargs={"pk": postupak.pk}))
        self.assertEqual(postupak.centar, "43")
        self.assertEqual(postupak.datum_podnosenja, date(2026, 3, 5))
        self.assertEqual(postupak.created_by, self.admin)

        # Zaposleni prelazi u drugi centar - postupak zadrzava centar iz vremena zahteva.
        OrganizationalUnit.objects.create(name="Teren", code="426111", center="42")
        self.radnik.org_unit_code = "426111"
        self.radnik.save(update_fields=["org_unit_code"])
        postupak.refresh_from_db()
        self.assertEqual(postupak.centar, "43")

    def test_explicit_center_is_not_overwritten(self):
        OrganizationalUnit.objects.create(name='Drugi centar', code='426111', center='42')
        self._create(centar="42")
        self.assertEqual(DisciplinskiPostupak.objects.get().centar, "42")

    def test_tok_postupka_accepts_several_entries_in_date_order(self):
        self._create()
        postupak = DisciplinskiPostupak.objects.get()
        url = reverse("pravna:disciplinski_dodaj_tok", kwargs={"pk": postupak.pk})
        self.client.post(url, {"datum": "20.03.2026", "opis": "Izjasnjenje zaposlenog"})
        self.client.post(url, {"datum": "10.03.2026", "opis": "Zahtev prosledjen komisiji"})
        self.assertEqual(
            [z.opis for z in postupak.tok.all()],
            ["Zahtev prosledjen komisiji", "Izjasnjenje zaposlenog"],
        )

        zapis = postupak.tok.first()
        self.client.post(reverse("pravna:disciplinski_obrisi_tok", kwargs={"pk": zapis.pk}))
        self.assertEqual(postupak.tok.count(), 1)

    def test_measure_and_date_close_the_case_and_can_be_undone(self):
        self._create()
        postupak = DisciplinskiPostupak.objects.get()
        self.assertFalse(postupak.zatvoren)
        self.assertEqual(postupak.datum_statusa, date(2026, 3, 5))

        url = reverse("pravna:disciplinski_mera", kwargs={"pk": postupak.pk})
        response = self.client.post(url, {"mera_datum": "01.04.2026", "mera_vrsta": "1"})
        self.assertRedirects(response, reverse("pravna:disciplinski_detalj", kwargs={"pk": postupak.pk}))
        postupak.refresh_from_db()
        self.assertTrue(postupak.zatvoren)
        self.assertEqual(postupak.mera_datum, date(2026, 4, 1))
        self.assertEqual(postupak.datum_statusa, date(2026, 4, 1))
        self.assertEqual(postupak.mera_opis, "")
        self.assertEqual(postupak.mera_vrsta, '1')

        self.client.post(url, {"ponisti": "1"})
        postupak.refresh_from_db()
        self.assertFalse(postupak.zatvoren)
        self.assertEqual(postupak.mera_vrsta, '')
        self.assertEqual(postupak.datum_statusa, date(2026, 3, 5))
        self.assertEqual(postupak.mera_opis, "")

    def test_closing_without_valid_date_is_refused_and_case_stays_open(self):
        self._create()
        postupak = DisciplinskiPostupak.objects.get()
        for datum in ("", "31.02.2026"):
            with self.subTest(datum=datum):
                response = self.client.post(
                    reverse("pravna:disciplinski_mera", kwargs={"pk": postupak.pk}),
                    {"mera_datum": datum},
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("mera_datum", response.context["forma_mera"].errors)
                postupak.refresh_from_db()
                self.assertFalse(postupak.zatvoren)

    def test_closing_requires_one_of_the_four_measures(self):
        self._create()
        postupak = DisciplinskiPostupak.objects.get()
        url = reverse('pravna:disciplinski_mera', args=[postupak.pk])
        for mera in ['', '5', 'free text']:
            response = self.client.post(url, {'mera_datum': '01.04.2026', 'mera_vrsta': mera})
            self.assertIn('mera_vrsta', response.context['forma_mera'].errors)
            postupak.refresh_from_db()
            self.assertFalse(postupak.zatvoren)
        for mera in ['1', '2', '3', '4']:
            self.assertEqual(self.client.post(url, {'mera_datum': '01.04.2026', 'mera_vrsta': mera}).status_code, 302)
            postupak.refresh_from_db()
            self.assertEqual(postupak.mera_vrsta, mera)

    def test_closed_legacy_case_can_get_measure_without_losing_date(self):
        self._create()
        postupak = DisciplinskiPostupak.objects.get()
        DisciplinskiPostupak.objects.filter(pk=postupak.pk).update(mera_datum=date(2026,4,1))
        self.assertContains(self.client.get(reverse('pravna:disciplinski_detalj', args=[postupak.pk])), 'Sačuvaj meru')
        self.client.post(reverse('pravna:disciplinski_mera', args=[postupak.pk]), {'mera_vrsta':'3', 'mera_datum':'01.04.2026'})
        postupak.refresh_from_db()
        self.assertEqual(postupak.mera_datum, date(2026,4,1))
        self.assertEqual(postupak.mera_vrsta, '3')

    def test_short_hr_unit_maps_to_center_and_archived_is_not_editable_in_form(self):
        self.radnik.org_unit_code = '431'
        self.radnik.save()
        self._create(arhivirano='on')
        postupak = DisciplinskiPostupak.objects.get()
        self.assertEqual(postupak.centar, '43')
        self.assertFalse(postupak.arhivirano)
        response = self.client.get(reverse('pravna:disciplinski_izmeni', args=[postupak.pk]))
        self.assertNotContains(response, 'name="arhivirano"')
        self.assertEqual(response.context['form'].employee_centers[str(self.radnik.pk)], '43')

    def test_closing_and_reopening_preserves_existing_description_and_history(self):
        self._create()
        postupak = DisciplinskiPostupak.objects.get()
        postupak.mera_opis = "Ranije evidentirana mera"
        postupak.save()
        zapis = TokPostupka.objects.create(
            postupak=postupak, datum=date(2026, 3, 10), opis="Opomena pred otkaz",
        )
        url = reverse("pravna:disciplinski_mera", kwargs={"pk": postupak.pk})
        for payload in ({"mera_datum": "01.04.2026", "mera_vrsta": "2"}, {"ponisti": "1"}):
            self.client.post(url, payload)
            postupak.refresh_from_db()
            self.assertEqual(postupak.mera_opis, "Ranije evidentirana mera")
            self.assertTrue(postupak.tok.filter(pk=zapis.pk).exists())

    def test_list_and_detail_show_current_status_date(self):
        self._create()
        postupak = DisciplinskiPostupak.objects.get()
        list_url = reverse("pravna:disciplinski_lista")
        detail_url = reverse("pravna:disciplinski_detalj", kwargs={"pk": postupak.pk})
        response = self.client.get(list_url)
        self.assertContains(response, 'data-order="2026-03-05">05.03.2026.</td>')
        self.client.post(
            reverse("pravna:disciplinski_mera", kwargs={"pk": postupak.pk}),
            {"mera_datum": "01.04.2026", "mera_vrsta": "1"},
        )
        response = self.client.get(list_url)
        self.assertContains(response, 'data-order="2026-04-01">01.04.2026.</td>')
        self.assertNotContains(response, "Datum disciplinske mere")
        response = self.client.get(detail_url)
        self.assertContains(response, "Datum zatvaranja: 01.04.2026.")
        self.assertContains(response, "Promena toka postupka")
        self.assertNotContains(response, 'name="mera_opis"')

    def test_list_filters_by_center_status_and_archive(self):
        self._create()
        drugi = zaposleni(1003, "Jovanovic", org_unit_code="")
        DisciplinskiPostupak.objects.create(
            zaposleni=drugi, podnosilac=self.sef, centar="42",
            datum_podnosenja=date(2026, 2, 1), mera_datum=date(2026, 2, 20), mera_opis="Otkaz",
        )
        DisciplinskiPostupak.objects.create(
            zaposleni=drugi, podnosilac=self.sef, centar="42",
            datum_podnosenja=date(2026, 1, 1), arhivirano=True,
        )
        url = reverse("pravna:disciplinski_lista")

        self.assertEqual(len(self.client.get(url).context["postupci"]), 2)
        self.assertEqual(len(self.client.get(url, {"arhivirano": "1"}).context["postupci"]), 3)
        self.assertEqual(len(self.client.get(url, {"centar": "43"}).context["postupci"]), 1)
        self.assertEqual(len(self.client.get(url, {"status": "zatvoreni"}).context["postupci"]), 1)
        self.assertEqual(len(self.client.get(url, {"status": "aktivni"}).context["postupci"]), 1)

    def test_archive_toggle_and_delete(self):
        self._create()
        postupak = DisciplinskiPostupak.objects.get()
        self.client.post(reverse("pravna:disciplinski_arhiviraj", kwargs={"pk": postupak.pk}))
        postupak.refresh_from_db()
        self.assertTrue(postupak.arhivirano)

        self.client.post(reverse("pravna:disciplinski_dodaj_tok", kwargs={"pk": postupak.pk}),
                         {"datum": "20.03.2026", "opis": "Zapisnik"})
        self.client.post(reverse("pravna:disciplinski_obrisi", kwargs={"pk": postupak.pk}))
        self.assertFalse(DisciplinskiPostupak.objects.exists())
        self.assertFalse(TokPostupka.objects.exists())

    def test_print_report_groups_by_center(self):
        self._create()
        response = self.client.get(reverse("pravna:disciplinski_izvestaj"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([g["centar"] for g in response.context["groups"]], ["43"])
        self.assertEqual(response.context["total_postupci"], 1)

    def test_user_without_permission_cannot_open_the_list(self):
        user = get_user_model().objects.create_user("bez-dozvole", password="test-pass")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("pravna:disciplinski_lista")).status_code, 403)
