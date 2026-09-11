"""Vehicle maintenance evidence using explicit links and document dates only."""
from datetime import date

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from fleet.models import Kvar, Requisition
from nabavka.models import ProcurementCase, ProcurementInvoice


WORK_TYPES = dict(Kvar.WorkType.choices)


def service_category(name):
    normalized = ' '.join((name or '').lower().replace('_', ' ').split())
    for suffix in (' van ims', ' u ims'):
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
    return {'mali servis': 'mali_servis', 'veliki servis': 'veliki_servis',
            'мали сервис': 'mali_servis', 'велики сервис': 'veliki_servis',
            'popravka': 'popravka'}.get(normalized, '')


def vehicle_maintenance(vehicle, today=None):
    today = today or timezone.localdate()
    documents, orders = {}, {}

    def order_row(key, reference, title, work_type, url, status=''):
        row = dict(key=key, reference=reference, title=title,
                   work_type=work_type, type_label=WORK_TYPES.get(work_type, 'Nije razvrstano'),
                   url=url, status=status, document_keys=set())
        orders[key] = row
        return row

    def document(key, kind, number, day, url, work_type='', order=None, supplier=''):
        row = documents.setdefault(key, dict(key=key, kind=kind, reference=number or '—',
            date=day, url=url, types=set(), orders={}, supplier=supplier, date_conflict=False))
        if row['date'] and day and row['date'] != day:
            row['date_conflict'] = True
        elif not row['date']:
            row['date'] = day
        if work_type:
            row['types'].add(work_type)
        if order:
            row['orders'][order['key']] = order
            order['document_keys'].add(key)
            if order['status'] != ProcurementCase.Status.CANCELLED and order['work_type']:
                row['types'].add(order['work_type'])
        return row

    for kvar in Kvar.objects.filter(vehicle=vehicle):
        order_row(('garage', kvar.pk), kvar.rbz or f'PK {kvar.pk}',
                  'Nalog garaže', kvar.work_type, reverse('kvar_detail', args=[kvar.pk]))

    cases = list(ProcurementCase.objects.filter(
        Q(vehicle=vehicle) | Q(vehicle__isnull=True, garage_order__vehicle=vehicle)
    ).select_related('garage_order').prefetch_related(
        'invoice_links', 'items__euf_invoice', 'items__uf_invoice',
        'items__uf_item__uf_invoice', 'items__invoice_link__invoice',
    ))
    for case in cases:
        work_type = case.work_type or (case.garage_order.work_type if case.garage_order_id and case.garage_order.vehicle_id == vehicle.pk else '')
        order = order_row(('case', case.pk), case.case_number, case.get_case_type_display(),
                          work_type, reverse('nabavka:case_detail', args=[case.pk]), case.status)
        order['status_label'] = case.get_status_display()
        for link in case.invoice_links.all():
            document(('euf', link.euf_key), 'Faktura', link.invoice_number, link.invoice_date,
                     order['url'], order=order, supplier=link.supplier_name)
        for item in case.items.all():
            invoices = [item.euf_invoice] if item.euf_invoice_id else []
            if hasattr(item, 'invoice_link'):
                invoices.append(item.invoice_link.invoice)
            for invoice in invoices:
                # A document explicitly assigned to a different vehicle is not this vehicle's evidence.
                if invoice.vehicle_id and invoice.vehicle_id != vehicle.pk:
                    continue
                document(('euf', invoice.euf_key), 'Faktura', invoice.invoice_number, invoice.invoice_date,
                         reverse('nabavka:euf_invoice_detail', args=[invoice.pk]),
                         invoice.work_type, order, invoice.supplier_name)
            uf = item.uf_invoice or (item.uf_item.uf_invoice if item.uf_item_id else None)
            if uf:
                document(('uf', uf.pk), 'UF faktura', uf.invoice_number, uf.document_date,
                         reverse('nabavka:uf_invoice_detail', args=[uf.pk]), order=order, supplier=uf.partner_name)
            elif item.uf_item_id:
                uf_item = item.uf_item
                document(('uf_item', uf_item.purchase_invoice_id or uf_item.source_key), 'UF faktura',
                         uf_item.invoice_number, uf_item.document_date, order['url'],
                         order=order, supplier=uf_item.partner_name)

    # Invoice header links and legacy item links share the same EUF identity.
    keys = [key[1] for key in documents if key[0] == 'euf']
    for invoice in ProcurementInvoice.objects.filter(Q(vehicle=vehicle) | Q(euf_key__in=keys)):
        key = ('euf', invoice.euf_key)
        if invoice.vehicle_id and invoice.vehicle_id != vehicle.pk:
            documents.pop(key, None)
            continue
        row = document(key, 'Faktura', invoice.invoice_number, invoice.invoice_date,
                       reverse('nabavka:euf_invoice_detail', args=[invoice.pk]),
                       invoice.work_type, supplier=invoice.supplier_name)
        row['url'] = reverse('nabavka:euf_invoice_detail', args=[invoice.pk])

    requisitions = Requisition.objects.filter(
        Q(vehicle=vehicle) | Q(vehicle__isnull=True, kvar__vehicle=vehicle)
    ).select_related('popravka_kategorija')
    for item in requisitions:
        order = orders.get(('garage', item.kvar_id))
        key = ('requisition', item.sif_pred, item.god, item.br_dok)
        document(key, 'Trebovanje', f'{item.br_dok}/{item.god}', item.datum_trebovanja,
                 reverse('requisition_detail', kwargs={'god': item.god, 'br_dok': item.br_dok}),
                 service_category(item.popravka_kategorija.name if item.popravka_kategorija else ''), order)

    # A request may be linked to a garage order; carry its existing document links to that order.
    for case in cases:
        garage = orders.get(('garage', case.garage_order_id))
        if garage is None or case.status == ProcurementCase.Status.CANCELLED:
            continue
        request = orders[('case', case.pk)]
        for key in request['document_keys']:
            if key not in documents:
                continue
            row = documents[key]
            row['orders'][garage['key']] = garage
            garage['document_keys'].add(key)
            if garage['work_type']:
                row['types'].add(garage['work_type'])

    for row in documents.values():
        row['work_type'] = next(iter(row['types'])) if len(row['types']) == 1 else ''
        row['conflict'] = len(row['types']) > 1 or row['date_conflict']
        row['type_label'] = 'Proveriti kategoriju / datum' if row['conflict'] else WORK_TYPES.get(row['work_type'], 'Nije razvrstano')
        row['order_links'] = list(row['orders'].values())

    document_list = sorted(documents.values(), key=lambda r: (r['date'] or date.min, r['reference']), reverse=True)
    for order in orders.values():
        order['documents'] = [r for r in document_list if r['key'] in order['document_keys']]
        order['latest_date'] = max((r['date'] for r in order['documents'] if r['date']), default=None)
    summaries = []
    for work_type in ('mali_servis', 'veliki_servis'):
        eligible = [r for r in document_list if r['work_type'] == work_type and not r['conflict']
                    and r['date'] and r['date'] <= today]
        summaries.append(dict(label=WORK_TYPES[work_type], latest=eligible[0] if eligible else None, count=len(eligible)))
    return dict(summaries=summaries, documents=document_list,
                orders=sorted(orders.values(), key=lambda r: (r['latest_date'] or date.min, r['reference'] or ''), reverse=True))
