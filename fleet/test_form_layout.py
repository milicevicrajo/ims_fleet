"""Testovi rasporeda formi Flote (19.09.2026.).

Proveravaju tri stvari koje su ranije nedostajale na svim ekranima osim čarobnjaka:
obaveznost se vidi, polja su grupisana u celine, i nijedno polje ne ispada iz prikaza.
"""
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .forms.fuel import FuelConsumptionForm
from .forms.insurance import DraftInsuranceForm, InsuranceForm
from .forms.lease import LeaseForm
from .forms.policy import PolicyForm
from .forms.services import DraftServiceTransactionForm, RequisitionForm, ServiceTransactionForm
from .forms.vehicles import TrafficCardForm, VehicleForm, VehicleTenderDocumentForm

GROUPED_FORMS = [
    LeaseForm, PolicyForm, FuelConsumptionForm, InsuranceForm, DraftInsuranceForm,
    ServiceTransactionForm, DraftServiceTransactionForm, RequisitionForm,
    VehicleForm, TrafficCardForm, VehicleTenderDocumentForm,
]


class FormLayoutTests(SimpleTestCase):
    def test_no_field_is_lost_when_grouping(self):
        # Polje koje nije navedeno ni u jednoj celini mora završiti u „Ostalo“,
        # da izmena modela ne bi tiho sakrila novo polje sa ekrana.
        for form_class in GROUPED_FORMS:
            with self.subTest(form=form_class.__name__):
                form = form_class()
                shown = [field.name for group in form.grouped_fields for field in group['fields']]
                self.assertEqual(sorted(shown), sorted(form.fields), msg='neko polje je ispalo iz prikaza')
                self.assertEqual(len(shown), len(set(shown)), msg='polje se prikazuje dvaput')

    def test_every_group_has_a_title_and_at_least_one_field(self):
        for form_class in GROUPED_FORMS:
            with self.subTest(form=form_class.__name__):
                for group in form_class().grouped_fields:
                    self.assertTrue(group['title'])
                    self.assertTrue(group['fields'])

    def test_leftover_fields_go_to_a_named_group(self):
        class Partial(LeaseForm):
            fieldsets = (('Samo vozilo', None, ('vehicle',)),)

        groups = Partial().grouped_fields

        self.assertEqual(groups[0]['title'], 'Samo vozilo')
        self.assertEqual(groups[-1]['title'], 'Ostalo')
        self.assertGreater(len(groups[-1]['fields']), 1)

    def test_forms_without_fieldsets_fall_back_to_flat_list(self):
        from .forms.reference import OrganizationalUnitForm

        self.assertEqual(OrganizationalUnitForm().grouped_fields, []) if hasattr(
            OrganizationalUnitForm(), 'grouped_fields') else None

    def test_required_flag_is_reported_for_the_legend(self):
        self.assertTrue(PolicyForm().has_required_fields)

    def test_garage_field_has_one_name_everywhere(self):
        # Polje `nije_garaza` je negacija. Ranije je jedna forma imala naziv sa
        # SUPROTNIM znacenjem, sto je vodilo obrnutom unosu.
        labels = {
            form_class.__name__: str(form_class().fields['nije_garaza'].label)
            for form_class in (ServiceTransactionForm, DraftServiceTransactionForm, RequisitionForm)
        }
        self.assertEqual(len(set(labels.values())), 1, msg=f'različiti nazivi: {labels}')
        self.assertIn('van garaže', list(labels.values())[0])

    def test_ambiguous_amounts_carry_an_explanation(self):
        explained = {
            LeaseForm: ['current_payment_amount'],
            PolicyForm: ['premium_amount', 'first_installment_amount', 'other_installments_amount'],
            FuelConsumptionForm: ['cost_bruto', 'cost_neto'],
            RequisitionForm: ['cena', 'vrednost_nab'],
        }
        for form_class, names in explained.items():
            form = form_class()
            for name in names:
                with self.subTest(form=form_class.__name__, field=name):
                    self.assertTrue(form[name].help_text, msg='iznos bez objašnjenja šta obuhvata')

    def test_lease_amount_warns_that_it_is_not_used_in_the_calculation(self):
        help_text = str(LeaseForm()['current_payment_amount'].help_text)
        self.assertIn('NE koristi', help_text)


class RequiredMarkerRenderTests(TestCase):
    """Zvezdica i legenda moraju stvarno stići do stranice."""

    def setUp(self):
        self.user = get_user_model().objects.create_superuser('admin-forme', password='t')
        self.client.force_login(self.user)

    def test_policy_form_page_marks_required_fields(self):
        response = self.client.get(reverse('policy_create'))

        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('fleet-required', body)
        self.assertIn('su obavezna', body)
        # Celine imaju vidljive naslove.
        self.assertIn('fleet-fieldset', body)
        self.assertIn('Iznosi', body)
