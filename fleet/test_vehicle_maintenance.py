from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import OrganizationalUnit
from fleet.models import Kvar, Requisition, ServiceType
from fleet.support.vehicle_maintenance import service_category, vehicle_maintenance
from fleet.test_vehicle_onboarding import vehicle
from nabavka.forms import ProcurementCaseForm, ProcurementInvoiceForm
from nabavka.models import (ProcurementCase, ProcurementInvoice, ProcurementInvoiceLink,
                            ProcurementItem, ProcurementItemInvoiceLink, UfInvoiceSnapshot)


class VehicleMaintenanceTests(TestCase):
    def setUp(self):
        self.car = vehicle()
        self.other = vehicle('2')
        self.oj = OrganizationalUnit.objects.create(code='S1', name='Servis', center='01')
        self.order = Kvar.objects.create(vehicle=self.car, work_type='mali_servis', kilometraza=100000, opis='Test')

    def case(self, **kwargs):
        return ProcurementCase.objects.create(title='Servis', job_code=self.oj, vehicle=self.car, is_garage=True, **kwargs)

    def invoice(self, **kwargs):
        return ProcurementInvoice.objects.create(euf_key='inv1', invoice_number='F-1', **kwargs)

    def requisition(self, **kwargs):
        return Requisition.objects.create(vehicle=self.car, sif_pred=1, god=2026, br_dok='R1',
            sif_vrsart='1', stavka=kwargs.pop('stavka', 1), sif_art='1', naz_art='Filter', kol=1, cena=1, vrednost_nab=1,
            mesec_unosa=2, datum_trebovanja=date(2026,2,1), **kwargs)

    def test_linked_invoice_uses_document_date_and_is_not_duplicated_by_items_or_order(self):
        case = self.case(work_type='mali_servis', garage_order=self.order, needed_by=date(2026,1,1))
        invoice = self.invoice(invoice_date=date(2026,3,15))
        for i in range(2):
            item = ProcurementItem.objects.create(procurement_case=case, name=str(i), uom='kom', quantity=1, euf_invoice=invoice)
            ProcurementItemInvoiceLink.objects.create(procurement_item=item, invoice=invoice)
        ProcurementInvoiceLink.objects.create(procurement_case=case, euf_key='inv1', invoice_number='F-1', invoice_date=invoice.invoice_date)
        data = vehicle_maintenance(self.car)
        self.assertEqual(len(data['documents']), 1)
        self.assertEqual(data['summaries'][0]['latest']['date'], date(2026,3,15))
        self.assertEqual(len(data['documents'][0]['order_links']), 2)
        self.assertEqual({row['latest_date'] for row in data['orders']}, {date(2026,3,15)})

    def test_requests_without_documents_do_not_get_a_service_date(self):
        self.case(work_type='veliki_servis', needed_by=date(2026,1,1))
        data = vehicle_maintenance(self.car)
        self.assertEqual(data['documents'], [])
        self.assertTrue(all(row['latest_date'] is None for row in data['orders']))
        self.assertTrue(all(row['latest'] is None for row in data['summaries']))

    def test_unlinked_invoice_and_requisition_stay_unlinked_and_unclassified(self):
        self.invoice(vehicle=self.car, invoice_date=date(2026,4,1))
        self.requisition()
        data = vehicle_maintenance(self.car)
        self.assertEqual(len(data['documents']), 2)
        self.assertTrue(all(not row['order_links'] and not row['work_type'] for row in data['documents']))
        self.assertTrue(all(row['latest'] is None for row in data['summaries']))

    def test_requisition_lines_are_one_document_and_take_existing_order_type(self):
        self.requisition(kvar=self.order)
        self.requisition(kvar=self.order, stavka=2)
        data = vehicle_maintenance(self.car)
        self.assertEqual(len(data['documents']), 1)
        self.assertEqual(data['documents'][0]['work_type'], 'mali_servis')
        self.assertEqual(data['summaries'][0]['latest']['date'], date(2026,2,1))

    def test_conflicting_types_do_not_claim_latest_service(self):
        category = ServiceType.objects.create(name='Veliki servis van IMS')
        self.requisition(kvar=self.order, popravka_kategorija=category)
        data = vehicle_maintenance(self.car)
        self.assertTrue(data['documents'][0]['conflict'])
        self.assertTrue(all(row['latest'] is None for row in data['summaries']))

    def test_existing_service_categories_keep_location_separate_from_type(self):
        self.assertEqual(service_category('Veliki servis u IMS'), 'veliki_servis')
        self.assertEqual(service_category('Veliki servis van IMS'), 'veliki_servis')
        self.assertEqual(service_category('Popravka u IMS'), 'popravka')
        self.assertEqual(service_category('Filter ulja'), '')

    def test_no_date_is_not_replaced_by_created_date_and_future_is_not_latest(self):
        self.invoice(vehicle=self.car, work_type='mali_servis')
        ProcurementInvoice.objects.create(euf_key='future', invoice_number='future', vehicle=self.car,
                                          work_type='veliki_servis', invoice_date=date(2099,1,1))
        data = vehicle_maintenance(self.car)
        self.assertEqual(len(data['documents']), 2)
        self.assertTrue(all(row['latest'] is None for row in data['summaries']))

    def test_other_vehicle_invoice_not_exposed_even_when_case_link_is_inconsistent(self):
        case = self.case(work_type='mali_servis')
        invoice = self.invoice(vehicle=self.other, invoice_date=date(2026,4,1))
        ProcurementInvoiceLink.objects.create(procurement_case=case, euf_key=invoice.euf_key, invoice_number='F-1', invoice_date=invoice.invoice_date)
        self.assertEqual(vehicle_maintenance(self.car)['documents'], [])

    def test_uf_date_and_standalone_invoice_category_and_cancelled_case(self):
        case = self.case(work_type='veliki_servis')
        uf = UfInvoiceSnapshot.objects.create(source_key='uf', invoice_number='UF1', document_date=date(2026,2,2))
        ProcurementItem.objects.create(procurement_case=case, name='Servis', uom='kom', quantity=1, uf_invoice=uf)
        invoice = self.invoice(vehicle=self.car, invoice_date=date(2026,3,1), work_type='mali_servis')
        data = vehicle_maintenance(self.car)
        self.assertEqual(data['summaries'][0]['latest']['date'], invoice.invoice_date)
        self.assertEqual(data['summaries'][1]['latest']['date'], uf.document_date)
        case.status = ProcurementCase.Status.CANCELLED
        case.save()
        self.assertIsNone(vehicle_maintenance(self.car)['summaries'][1]['latest'])

    def form_data(self, **kwargs):
        return dict(case_type='usluga', status='draft', title='Servis', is_garage=True,
                    vehicle=self.car.pk, job_code=self.oj.pk, currency='RSD', **kwargs)

    def test_case_form_inherits_order_type_and_rejects_other_vehicle_or_type(self):
        form = ProcurementCaseForm(data=self.form_data(garage_order=self.order.pk))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['work_type'], 'mali_servis')
        saved = form.save()
        self.assertEqual(saved.garage_order_id, self.order.pk)
        form = ProcurementCaseForm(data=self.form_data(garage_order=self.order.pk, work_type='veliki_servis'))
        self.assertFalse(form.is_valid())
        self.assertIn('work_type', form.errors)
        data = self.form_data(garage_order=self.order.pk)
        data['vehicle'] = self.other.pk
        form = ProcurementCaseForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('garage_order', form.errors)

    def test_invoice_can_be_classified_without_order(self):
        invoice = self.invoice(vehicle=self.car)
        form = ProcurementInvoiceForm(data={'is_garage':True, 'vehicle':self.car.pk, 'work_type':'veliki_servis'}, instance=invoice)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().work_type, 'veliki_servis')

    def test_vehicle_tab_and_garage_request_prefill_render(self):
        user = get_user_model().objects.create_superuser('service-admin', password='test')
        self.client.force_login(user)
        response = self.client.get(reverse('vehicle_detail', args=[self.car.pk]))
        self.assertContains(response, 'id="maintenance-tab"')
        self.assertContains(response, 'Nema povezanog dokumenta')
        response = self.client.get(reverse('nabavka:case_create'), {'garage_order':self.order.pk, 'case_type':'usluga'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['garage_order'], self.order.pk)
        self.assertEqual(response.context['form'].initial['work_type'], 'mali_servis')
        self.assertContains(response, f'data-vehicle="{self.car.pk}"')
