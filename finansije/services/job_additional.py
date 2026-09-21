"""Relative indicators derived from the existing, unchanged job results."""
from calendar import monthrange
from datetime import date
from decimal import Decimal
import logging

from django.conf import settings
from django.db import DatabaseError
from django.utils.formats import number_format
from django.utils.html import format_html

from .job_overview import METRICS, LABELS, metric_cell, table_data
from .job_people import payroll_headcounts
from .job_tables import cell


logger = logging.getLogger(__name__)
RATIOS = (
    ('margin', 'Rezultat bez ZT / prihodi %', 'result', 1),
    ('margin_after', 'Rezultat posle ZT / prihodi %', 'after_shared', 1),
    ('expense_share', 'Rashodi / prihodi %', 'expense', -1),
    ('shared_share', 'ZT / prihodi %', 'shared_cost', -1),
)
EXTRA_KEYS = tuple(r[0] for r in RATIOS) + ('people',) + tuple(f'{key}_person' for key in METRICS)
EXTRA_LABELS = tuple(r[1] for r in RATIOS) + ('Prosečan broj ljudi',) + tuple(f'{label} / čoveku' for label in LABELS)


def metric(value, complete=True, note=''):
    return dict(value=value, complete=complete, note=note)


def divide(numerator, denominator, multiplier=1):
    note = ' '.join(dict.fromkeys(p['note'] for p in (numerator, denominator) if p['note']))
    if numerator['value'] is None or denominator['value'] is None:
        return metric(None, False, note or 'Nedostaju podaci za obračun.')
    if denominator['value'] <= 0:
        return metric(None, False, 'Osnovica mora biti veća od nule. ' + note)
    return metric(numerator['value'] * multiplier / denominator['value'],
                  numerator['complete'] and denominator['complete'], note)


def enrich_additional(rows, start, end, *, can_people=True):
    codes = {row['code'] for row in rows if row['code']}
    months = {(year, month) for year in range(start.year, end.year + 1)
              for month in range(1, 13) if start.replace(day=1) <= date(year, month, 1) <= end}
    counts, closed, opened = {}, set(), set()
    source_failed = False
    if can_people and codes:
        for year in range(start.year, end.year + 1):
            lower, upper = max(start, date(year, 1, 1)), min(end, date(year, 12, 31))
            try:
                data = payroll_headcounts(getattr(settings, 'FINANSIJE_COMPANY', 1), codes, lower, upper)
            except DatabaseError:
                logger.exception('Broj ljudi po poslovima nije dostupan za %s', year)
                source_failed = True
                continue
            closed.update((year, m) for m in data['closed_months'])
            opened.update((year, m) for m in data['open_months'])
            for code, values in data['counts'].items():
                counts.setdefault(code, {}).update({(year, m): value for m, value in values.items()})
    closed &= months
    opened &= months
    partial_month = start.day != 1 or end.day != monthrange(end.year, end.month)[1]
    complete = closed == months and not opened and not source_failed and not partial_month
    note = f'Zaključeni obračuni: {len(closed)} od {len(months)} meseci. '
    note += 'Prosek mesečnog broja različitih ljudi na šifri, preko dostupnih zaključenih meseci.'
    if opened:
        note += ' Postoje i otvoreni obračuni koji nisu uključeni.'
    if source_failed:
        note += ' Izvor zarada za deo perioda trenutno nije dostupan.'
    if partial_month:
        note += ' Za nepotpun mesec broj ljudi obuhvata ceo mesec; iznosi prate izabrane datume.'
    for row in rows:
        metrics = row['metrics']
        extra = {key: divide(metrics[source], metrics['revenue'], sign * 100)
                 for key, _, source, sign in RATIOS}
        if not can_people:
            people = metric(None, False, 'Za pokazatelje po čoveku potrebna je dozvola za zaposlene.')
        elif not row['code'] or not closed:
            people = metric(None, False, note if row['code'] else 'Nema šifre posla.')
        else:
            average = sum((Decimal(counts.get(row['code'], {}).get(m, 0)) for m in closed), Decimal(0)) / len(closed)
            people = metric(average, complete, note)
        extra['people'] = people
        extra.update({f'{key}_person': divide(metrics[key], people) for key in METRICS})
        row['additional'] = extra
    return rows


def additional_table_data(rows):
    data = table_data(rows)
    for row, cells in zip(rows, data['data']):
        for key in EXTRA_KEYS:
            item = row['additional'][key]
            if item['value'] is None or key.endswith('_person'):
                cells.append(metric_cell(item))
            else:
                suffix = '%' if key != 'people' else ''
                display = format_html('<span title="{}">{}{}{}</span>', item['note'],
                    number_format(item['value'], decimal_pos=2, force_grouping=True), suffix,
                    ' *' if not item['complete'] else '')
                cells.append(cell(item['value'], display))
    return data
