"""Osoba (JMBG) i zaposlenja (preduzeće + broj radnika), od 06.10.2026."""
import importlib
from datetime import date
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from hr.forms import EmployeeNameCorrectionForm
from hr.models import Employee, Osoba
from hr.services.osobe import glavno_zaposlenje, povezi_osobu
from hr.sync import sync_employees_from_hr_view

JMBG_A = "1508980710011"
JMBG_B = "0101990710022"


def red(rasif, ime, aktivan="D", jmbg=JMBG_A, prijem=date(2020, 1, 1), oj="413"):
    # Kolone kao u SELECT-u sinhronizacije (dbo.hr_employee), bez opcionih kolona izvora.
    return (rasif, ime, None, "Inženjer", oj, "M", date(1980, 8, 15), prijem, None, aktivan, jmbg,
            None, None, None, None, None, None, None, None, None, None, None)


def zaposleni(code, jmbg=JMBG_A, aktivan=True, prijem=date(2020, 1, 1), **polja):
    vrednosti = dict(first_name="Dragan", last_name="Kerkez", position="x", department_code=1, gender="M",
                     date_of_birth=date(1980, 8, 15), date_of_joining=prijem, is_active=aktivan, personal_number=jmbg)
    return Employee.objects.create(employee_code=code, **{**vrednosti, **polja})


class SinhronizacijaOsobaTests(TestCase):
    def pokreni(self, redovi, preduzeca):
        with patch("hr.sync._hr_employee_columns", return_value={}), \
                patch("hr.sync.preduzeca_radnika", return_value=preduzeca), \
                patch("hr.sync.staz_periodi", return_value=[]), \
                patch("hr.sync.radna_mesta_izvora", return_value={}), \
                patch("hr.sync.connections") as conn:
            conn.__getitem__.return_value.cursor.return_value.__enter__.return_value.fetchall.return_value = redovi
            return sync_employees_from_hr_view()

    def test_ista_osoba_sa_dva_broja_u_dva_preduzeca_je_jedna_osoba(self):
        rezultat = self.pokreni(
            [red(965, "KERKEZ DRAGAN", prijem=date(2023, 9, 19)), red(8, "Dragan Kerkez", prijem=date(1900, 1, 1))] * 2,
            {965: {(1, JMBG_A)}, 8: {(2, JMBG_A)}})
        self.assertEqual(rezultat["duplicate_rows"], 2)  # pogled vraća svaki red dvaput
        self.assertEqual(Osoba.objects.count(), 1)
        osoba = Osoba.objects.get()
        self.assertEqual(sorted(osoba.zaposlenja.values_list("preduzece", "employee_code")), [(1, 965), (2, 8)])
        self.assertEqual(glavno_zaposlenje(osoba).employee_code, 965)  # radni odnos, poslednji prijem
        self.assertEqual((osoba.ime, osoba.prezime, osoba.jmbg), ("Dragan", "Kerkez", JMBG_A))

    def test_neaktivan_broj_se_uvozi_samo_za_postojecu_osobu(self):
        rezultat = self.pokreni(
            [red(102, "KERKEZ DRAGAN", aktivan="N"), red(965, "KERKEZ DRAGAN"),
             red(359, "BOKIC MILE", aktivan="N", jmbg=JMBG_B)],
            {102: {(1, JMBG_A)}, 965: {(1, JMBG_A)}, 359: {(1, JMBG_B)}})
        self.assertEqual((rezultat["created"], rezultat["created_inactive"], rezultat["skipped_inactive"]), (1, 1, 1))
        osoba = Osoba.objects.get(jmbg=JMBG_A)
        self.assertEqual(sorted(osoba.zaposlenja.values_list("employee_code", "is_active")), [(102, False), (965, True)])
        self.assertFalse(Employee.objects.filter(employee_code=359).exists())

    def test_sukobi_se_preskacu_i_nista_se_ne_prepisuje(self):
        postojeci = zaposleni(7, first_name="Aleksa")
        rezultat = self.pokreni(
            [red(7, "DRUGI COVEK", jmbg=JMBG_B), red(5, "PRVI RED"), red(5, "DRUGI RED")],
            {7: {(1, JMBG_A), (2, JMBG_B)}, 5: {(1, JMBG_A)}})
        self.assertEqual((rezultat["company_conflicts"], rezultat["conflicting_rows"]), (1, 1))
        postojeci.refresh_from_db()
        self.assertEqual((postojeci.first_name, postojeci.personal_number), ("Aleksa", JMBG_A))
        self.assertFalse(Employee.objects.filter(employee_code=5).exists())

    def test_broj_koji_nestane_iz_izvora_dobija_oznaku_a_aktivnost_ostaje(self):
        rucni = zaposleni(9601, jmbg="")
        self.pokreni([red(965, "KERKEZ DRAGAN")], {965: {(1, JMBG_A)}})
        rucni.refresh_from_db()
        self.assertEqual((rucni.u_izvoru, rucni.is_active), (False, True))
        self.assertTrue(Employee.objects.get(employee_code=965).u_izvoru)

    def test_novo_zaposlenje_preuzima_ime_za_prikaz_i_cirilicu_osobe(self):
        stari = zaposleni(185, aktivan=False, display_last_name_override="Kerkéz",
                          full_name_cyrillic="Драган Керкез")
        povezi_osobu(stari)
        self.pokreni([red(185, "KERKEZ DRAGAN", aktivan="N"), red(1026, "KERKEZ DRAGAN", prijem=date(2025, 9, 1))],
                     {185: {(1, JMBG_A)}, 1026: {(1, JMBG_A)}})
        novi = Employee.objects.get(employee_code=1026)
        self.assertEqual(novi.osoba_id, stari.osoba_id)
        self.assertEqual((novi.display_last_name_override, novi.full_name_cyrillic), ("Kerkéz", "Драган Керкез"))


class OsobaTests(TestCase):
    def test_ispravka_imena_vazi_za_sva_zaposlenja_osobe(self):
        prvo, drugo = zaposleni(965, last_name="Stevancevic"), zaposleni(5, last_name="Stevancevic")
        for e in (prvo, drugo):
            povezi_osobu(e)
        forma = EmployeeNameCorrectionForm({"display_first_name_override": "", "display_last_name_override": "Stevančević"},
                                           instance=prvo)
        self.assertTrue(forma.is_valid(), forma.errors)
        forma.save()
        drugo.refresh_from_db()
        self.assertEqual(drugo.display_last_name_override, "Stevančević")
        self.assertEqual(prvo.osoba.prezime_za_prikaz, "Stevančević")

    def test_bez_jmbg_svako_zaposlenje_je_posebna_osoba(self):
        a, b = zaposleni(9601, jmbg=""), zaposleni(9602, jmbg=None)
        self.assertNotEqual(povezi_osobu(a).pk, povezi_osobu(b).pk)
        self.assertEqual(Osoba.objects.filter(jmbg="").count(), 2)

    def test_migracija_spaja_postojece_zaposlene_po_jmbg(self):
        staro = zaposleni(185, aktivan=False, full_name_cyrillic="Бранко Павловић", prijem=date(2003, 6, 16))
        novo = zaposleni(1026, prijem=date(2025, 9, 1), first_name="Branko", last_name="Pavlović")
        zaposleni(9601, jmbg="")
        migracija = importlib.import_module("fleet.migrations.0091_osoba_i_zaposlenja")
        migracija.popuni_osobe(apps, None)
        staro.refresh_from_db()
        novo.refresh_from_db()
        self.assertEqual(staro.osoba_id, novo.osoba_id)
        self.assertEqual((novo.osoba.ime, novo.osoba.prezime), ("Branko", "Pavlović"))  # aktivno, poslednji prijem
        self.assertEqual(novo.full_name_cyrillic, "Бранко Павловић")  # ćirilica prešla na osobu i sva zaposlenja
        self.assertEqual(Osoba.objects.count(), 2)


class SpisakPoOsobiTests(TestCase):
    def test_osoba_sa_dva_broja_je_jedan_red_sa_ostalim_siframa(self):
        glavno = zaposleni(1048, last_name="Stevančević", first_name="Helena", prijem=date(2026, 7, 1))
        pp = zaposleni(5, last_name="Stevančević", first_name="Helena", prijem=date(1900, 1, 1), preduzece=2)
        staro = zaposleni(185, jmbg=JMBG_B, aktivan=False, last_name="Pavlović")
        novo = zaposleni(1026, jmbg=JMBG_B, last_name="Pavlović")
        for e in (glavno, pp, staro, novo):
            povezi_osobu(e)
        self.client.force_login(get_user_model().objects.create_superuser("spisak", password="x"))
        redovi = self.client.get(reverse("employee_list")).context["employees"]
        self.assertEqual(sorted(e.employee_code for e in redovi), [1026, 1048])
        helena = next(e for e in redovi if e.employee_code == 1048)
        self.assertEqual([d.employee_code for d in helena.druge_sifre], [5])
        neaktivni = self.client.get(reverse("employee_list"), {"status": "inactive"}).context["employees"]
        self.assertEqual(list(neaktivni), [])  # Pavlović ima aktivan broj, nije među neaktivnima


class DetaljOsobeTests(TestCase):
    def test_detalj_prikazuje_ugovore_i_sifre_svih_zaposlenja(self):
        from hr.models import UgovorZaposlenog

        glavno = zaposleni(1048, first_name="Helena", last_name="Stevančević", prijem=date(2026, 7, 1))
        pp = zaposleni(5, first_name="Helena", last_name="Stevančević", prijem=date(1900, 1, 1), preduzece=2)
        for e in (glavno, pp):
            povezi_osobu(e)
        UgovorZaposlenog.objects.create(employee_code=1048, redni_broj=1, employee=glavno, datum_od=date(2026, 7, 1))
        UgovorZaposlenog.objects.create(employee_code=5, redni_broj=1, employee=pp, datum_od=date(2025, 3, 1),
                                        kategorija=UgovorZaposlenog.Kategorija.VAN_RADNOG_ODNOSA)
        self.client.force_login(get_user_model().objects.create_superuser("detalj", password="x"))
        odgovor = self.client.get(reverse("employee_detail", args=[glavno.pk]))
        self.assertEqual(odgovor.status_code, 200)
        self.assertEqual(odgovor.context["ugovori_zaposlenog_count"], 2)
        self.assertEqual([z.employee_code for z in odgovor.context["zaposlenja"]], [1048, 5])
        self.assertContains(odgovor, "Šifre zaposlenog:")
        self.assertContains(odgovor, 'id="bolovanja"')  # superuser vidi bolovanja


class UgovoriOsobeTests(TestCase):
    def test_detalj_ugovora_prikazuje_periode_pod_svim_siframa_osobe(self):
        from hr.models import UgovorZaposlenog

        staro = zaposleni(417, aktivan=False, last_name="Didanović", first_name="Veselinka", prijem=date(1980, 6, 24))
        novo = zaposleni(1033, last_name="Didanović", first_name="Veselinka", prijem=date(2026, 1, 8))
        for e in (staro, novo):
            povezi_osobu(e)
        stari = UgovorZaposlenog.objects.create(employee_code=417, redni_broj=1, employee=staro, datum_od=date(1980, 6, 24))
        novi = UgovorZaposlenog.objects.create(employee_code=1033, redni_broj=1, employee=novo, datum_od=date(2026, 1, 8))
        self.client.force_login(get_user_model().objects.create_superuser("ugovori", password="x"))
        odgovor = self.client.get(reverse("hr:ugovor_detail", args=[novi.pk]))
        self.assertEqual(odgovor.status_code, 200)
        self.assertEqual(sorted(p.pk for p in odgovor.context["periodi"]), sorted([stari.pk, novi.pk]))
        self.assertContains(odgovor, "šifra 417")


class StazTests(TestCase):
    def p(self, broj, od, do, staz, u_ims=True):
        return dict(preduzece=1, broj=broj, od=od, do=do, u_ims=u_ims, staz=staz)

    def test_zbir_po_izvoru_30_dana_12_meseci(self):
        from hr.services.osobe import obracunaj_staz
        # Pavlović 185: kadrovska baza daje 44 g 3 m 28 d.
        periodi = [self.p(185, date(1979, 11, 14), date(1980, 2, 29), (0, 3, 18), False),
                   self.p(185, date(1980, 3, 24), date(1980, 4, 25), (0, 1, 3), False),
                   self.p(185, date(1981, 7, 20), date(2002, 7, 19), (21, 0, 5)),
                   self.p(185, date(2002, 9, 9), date(2003, 6, 15), (0, 9, 10), False),
                   self.p(185, date(2003, 6, 16), date(2025, 8, 1), (22, 1, 22))]
        self.assertEqual(obracunaj_staz(periodi, {185: 0}), ((44, 3, 28), (43, 1, 27)))

    def test_ponovljeni_i_obuhvaceni_periodi_se_ne_racunaju_dvaput(self):
        from hr.services.osobe import obracunaj_staz
        periodi = [self.p(571, date(1999, 3, 1), date(2002, 12, 15), (3, 9, 0)),  # prepisan pod 789
                   self.p(789, date(1999, 3, 1), date(2002, 12, 15), (3, 9, 20)),
                   self.p(581, date(2002, 8, 1), date(2008, 11, 24), (6, 3, 27)),
                   self.p(562, date(2002, 8, 1), date(2002, 11, 1), (0, 3, 3)),  # unutar 581
                   self.p(5, date(1900, 1, 1), date(3000, 1, 1), (0, 0, 0)),  # PP bez staža
                   self.p(164, date(1983, 4, 25), date(3000, 1, 1), (41, 1, 2)),  # kraj nije upisan
                   self.p(995, date(2024, 5, 27), date(2024, 12, 31), (0, 6, 23))]
        ukupno, _ = obracunaj_staz(periodi, {789: 0, 571: 1, 581: 0, 562: 1, 995: 0, 164: 1})
        # 789 (3-9-20) + 581 (6-3-27) + 164 (41-1-2) + 995 (0-6-23) = 50 g 19 m 72 d = 51 g 9 m 12 d
        self.assertEqual(ukupno, (51, 9, 12))


class NaloziOsobaTests(TestCase):
    def test_jedna_osoba_jedan_nalog_i_deaktivacija_bivsih(self):
        from fleet.services.employee_user_profiles import uskladi_naloge_zaposlenih

        User = get_user_model()
        # Olgica: nalog na staroj šifri, aktivna nova → nalog se prebacuje, ne pravi se drugi.
        staro = zaposleni(226, jmbg=JMBG_B, aktivan=False, last_name="Mladenović", first_name="Olgica")
        novo = zaposleni(1058, jmbg=JMBG_B, last_name="Mladenović", first_name="Olgica", prijem=date(2026, 10, 1))
        # Kerkez: radni odnos + van radnog odnosa, bez naloga → jedan nalog na radnom odnosu.
        kerkez = zaposleni(965, prijem=date(2023, 9, 19))
        pp = zaposleni(8, prijem=date(1900, 1, 1), preduzece=2)
        # Bivši: osoba bez aktivnog broja → nalog se deaktivira; ručni zapis van izvora dobija nalog tek kad uđe u izvor.
        bivsi = zaposleni(893, jmbg="2202980710033", aktivan=False, last_name="Stanković", first_name="Nikola")
        rucni = zaposleni(9601, jmbg="", u_izvoru=False)
        samo_pp = zaposleni(3, jmbg="2410980710044", preduzece=2, last_name="Abduramani", first_name="Adnan")
        for e in (staro, novo, kerkez, pp, bivsi, rucni, samo_pp):
            povezi_osobu(e)
        olgica = User.objects.create_user("olgica.mladenovic", password="x", employee=staro)
        nikola = User.objects.create_user("nikola.stankovic", password="x", employee=bivsi)

        plan = uskladi_naloge_zaposlenih(execute=True)

        self.assertEqual([e.employee_code for e in plan["kreirati"]], [965])
        olgica.refresh_from_db(); nikola.refresh_from_db()
        self.assertEqual(olgica.employee_id, novo.pk)
        self.assertFalse(nikola.is_active)
        self.assertTrue(User.objects.filter(employee=kerkez, must_change_password=True).exists())
        self.assertFalse(User.objects.filter(employee__in=[pp, rucni, samo_pp]).exists())
        self.assertEqual(uskladi_naloge_zaposlenih(execute=True)["kreirati"], [])  # drugi put nema šta
        self.assertEqual([e.employee_code for e in uskladi_naloge_zaposlenih(van_radnog_odnosa=True)["kreirati"]], [3])
