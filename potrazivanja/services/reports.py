"""Local, permission-scoped reporting contract for other applications."""
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import PermissionDenied

from potrazivanja.access import can_view_job, scoped
from potrazivanja.models import CollectionState
from .sync import bucket

# Seven aging buckets followed by overdue and total; five red intensity levels.
AGING_TONES = (1, 2, 2, 3, 3, 4, 5, 4, 3)
BUCKET_TONES = dict(zip(('0.1', '30', '45', '60', '90', '180', '181'), AGING_TONES))


def job_balances(user, code, company=1):
    if not can_view_job(user, code, company):
        raise PermissionDenied('Šifra posla nije dostupna u Potraživanjima.')
    state = CollectionState.objects.select_related('current_snapshot').filter(company=company).first()
    snapshot = state.current_snapshot if state else None
    if not snapshot or snapshot.status != 'published':
        return {'snapshot': None, 'rows': []}
    groups = {}
    positions = scoped(snapshot.positions.filter(job_code=code), user).values(
        'identity_id', 'identity__partner_code', 'identity__source_name', 'account_family', 'due_date', 'balance')
    for row in positions:
        group = groups.setdefault((row['identity_id'], row['account_family']), {
            'identity_id': row['identity_id'], 'partner_code': row['identity__partner_code'],
            'partner_name': row['identity__source_name'], 'account_family': row['account_family'],
            'buckets': defaultdict(Decimal),
        })
        group['buckets'][bucket(row['due_date'], snapshot.as_of_date)] += row['balance']
    rows = []
    for group in groups.values():
        amounts = group.pop('buckets')
        values = [amounts[key] for key in ('0.1', '30', '45', '60', '90', '180', '181')]
        group['amounts'] = values + [sum(values[1:], Decimal(0)), sum(values, Decimal(0))]
        rows.append(group)
    rows.sort(key=lambda r: (r['partner_code'], r['account_family']))
    return {'snapshot': snapshot, 'rows': rows}
