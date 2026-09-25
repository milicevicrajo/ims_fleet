"""Forme Kadrova u sekcijama (hr/forms/base.html): nijedno polje ne ispada, a sve forme se otvaraju."""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from core.models import OrganizationalUnit
from hr.absence_views import SickLeaveImportForm
from hr.form_layout import sekcije_forme
from hr.forms import EmployeeCVItemForm, EmployeeForm, EmployeeNameCorrectionForm
from hr.models import Employee, EmployeeCVItem, Potpisnik, VrstaResenja, VrstaZahteva, WorkTimeCategory, Zahtev
from hr.resenja_forms import VrstaResenjaForm
from hr.services.zahtevi import dodeli_broj, napravi_resenje, pripremi_zahtev
from hr.zahtevi_forms import VrstaZahtevaForm

FORME_SA_SEKCIJAMA = (EmployeeForm, EmployeeCVItemForm, EmployeeNameCorrectionForm, SickLeaveImportForm,
                      VrstaResenjaForm, VrstaZahtevaForm)


class SekcijeTests(SimpleTestCase):
    def test_nijedno_polje_ne_ispada_iz_sekcija(self):
        for form_class in FORME_SA_SEKCIJAMA:
            with self.subTest(forma=form_class.__name__):
                form = form_class()
                prikazana = [polje.name for sekcija in form.sections for polje in sekcija['fields']]
                self.assertEqual(sorted(prikazana), sorted(form.fields))
                self.assertEqual(len(prikazana), len(set(prikazana)))
                for sekcija in form.sections:
                    self.assertTrue(sekcija['title'] and sekcija['icon'] and sekcija['fields'])

    def test_forma_bez_sekcija_je_jedna_sekcija(self):
        from django import forms

        class Obicna(forms.Form):
            naziv = forms.CharField()
            skriveno = forms.CharField(widget=forms.HiddenInput)

        sekcije = sekcije_forme(Obicna(), naslov='Vrsta rada')
        self.assertEqual(len(sekcije), 1)
        self.assertEqual(sekcije[0]['title'], 'Vrsta rada')
        self.assertEqual([polje.name for polje in sekcije[0]['fields']], ['naziv'])


class EkraniFormiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        OrganizationalUnit.objects.create(code='430', name='Centar za puteve', center='43')
        cls.employee = Employee.objects.create(employee_code=700, first_name='Petar', last_name='Petrovic',
            position='Inženjer', department_code=430, org_unit_code='430', gender='M',
            date_of_birth=date(1990, 1, 1), date_of_joining=date(2020, 1, 1))
        direktor = Employee.objects.create(employee_code=701, first_name='Dragan', last_name='Bojovic',
            position='Direktor', department_code=430, org_unit_code='430', gender='M',
            date_of_birth=date(1970, 1, 1), date_of_joining=date(2000, 1, 1))
        Potpisnik.objects.create(zaposleni=direktor, funkcija='Генерални директор', vazi_od=date(2024, 1, 1))
        cls.admin = get_user_model().objects.create_superuser('forme-admin', 'f@example.com', 'x', employee=cls.employee)
        cls.cv = EmployeeCVItem.objects.create(employee=cls.employee, title='Nadzor', organization='IMS',
                                               start_date=date(2021, 1, 1))
        cls.kategorija = WorkTimeCategory.objects.create(code='redovan_rad', name='Redovan rad')
        zahtev = Zahtev(vrsta=VrstaZahteva.objects.get(kod='prekovremeni-i-vikend'), zaposleni=cls.employee,
                        datum_zahteva=date(2026, 7, 28), datum_od=date(2026, 8, 1), datum_do=date(2026, 8, 31),
                        podnosilac=direktor, created_by=cls.admin)
        pripremi_zahtev(zahtev)
        dodeli_broj(zahtev)
        zahtev.save()
        cls.zahtev = zahtev
        cls.resenje = napravi_resenje(zahtev, cls.admin, datum_resenja=date(2026, 7, 30))

    def setUp(self):
        self.client.force_login(self.admin)

    def test_sve_forme_se_otvaraju_u_sekcijama(self):
        adrese = {
            reverse('employee_update', args=[self.employee.pk]): 'identitet',
            reverse('employee_create'): 'identitet',
            reverse('my_employee_name_correction'): 'ime',
            reverse('employee_cv_item_update', args=[self.cv.pk]): 'posao',
            reverse('hr:sick_leave_import'): 'datoteka',
            reverse('hr:work_time_catalog_edit', args=['categories', self.kategorija.pk]): 'podaci',
            reverse('hr:evaluation_catalog_create', args=['groups']): 'podaci',
            reverse('hr:evaluation_create'): 'zaposleni',
            reverse('hr:resenje_edit', args=[self.resenje.pk]): 'dani',
            reverse('hr:zahtev_edit', args=[self.zahtev.pk]): 'potpisi',
            reverse('hr:zahtev_bulk_create'): 'zaposleni',
            reverse('hr:resenje_catalog_edit', args=['vrste', VrstaResenja.objects.first().pk]): 'tekst',
            reverse('hr:resenje_catalog_edit', args=['vrste-zahteva', VrstaZahteva.objects.first().pk]): 'tekst',
            reverse('hr:resenje_catalog_create', args=['potpisnici']): 'podaci',
        }
        for adresa, sekcija in adrese.items():
            with self.subTest(adresa=adresa):
                odgovor = self.client.get(adresa)
                self.assertEqual(odgovor.status_code, 200)
                self.assertContains(odgovor, f'data-ef-section="{sekcija}"')
                self.assertContains(odgovor, 'hr/forme.js')
                self.assertContains(odgovor, 'id="ef-nav-links"')
