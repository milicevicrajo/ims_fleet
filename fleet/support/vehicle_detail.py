"""Period-based, recorded amounts for the vehicle dossier (no TCO estimates)."""
import datetime
from collections import defaultdict
from decimal import Decimal

from django import forms
from django.utils import timezone

ZERO = Decimal('0')


class VehiclePeriodForm(forms.Form):
    start = forms.DateField(label='Od', input_formats=['%Y-%m-%d'], widget=forms.DateInput(attrs={'type': 'date', 'data-native-date': ''}, format='%Y-%m-%d'))
    end = forms.DateField(label='Do', input_formats=['%Y-%m-%d'], widget=forms.DateInput(attrs={'type': 'date', 'data-native-date': ''}, format='%Y-%m-%d'))

    def clean(self):
        data = super().clean()
        start, end = data.get('start'), data.get('end')
        if start and end:
            if start > end:
                raise forms.ValidationError('Početak perioda mora biti pre kraja perioda.')
            elif (end - start).days > 1096:
                raise forms.ValidationError('Izaberite period do tri godine.')
            if end > timezone.localdate():
                raise forms.ValidationError('Analitika evidentiranih troškova ne obuhvata buduće datume.')
        return data


def period_presets(today, selected_start=None, selected_end=None):
    """Brzi izbori perioda, da se ne unose dva datuma za ono sto se najcesce trazi."""
    def months_back(count):
        index = today.year * 12 + today.month - 1 - count
        return datetime.date(index // 12, index % 12 + 1, 1)

    options = [
        ('Ovaj mesec', today.replace(day=1), today),
        ('Poslednja 3 meseca', months_back(2), today),
        ('Poslednjih 12 meseci', months_back(11), today),
        ('Ova godina', datetime.date(today.year, 1, 1), today),
        ('Prošla godina', datetime.date(today.year - 1, 1, 1), datetime.date(today.year - 1, 12, 31)),
    ]
    return [
        {'label': label, 'start': start, 'end': end,
         'active': start == selected_start and end == selected_end}
        for label, start, end in options
    ]


def date_only(value):
    if isinstance(value, datetime.datetime):
        return timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
    return value


def recorded_analytics(fuel, services, requisitions, recoveries, start, end):
    """Keep signed ledger amounts; empty data is distinguishable from zero."""
    month = start.replace(day=1)
    monthly = {}
    while month <= end:
        monthly[month] = dict(month=month, fuel=None, service=None, requisition=None, recovery=None, count=0)
        month = (month.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    totals = dict(fuel=ZERO, service=ZERO, requisition=ZERO, recovery=ZERO)
    counts = dict.fromkeys(totals, 0)
    categories = defaultdict(lambda: ZERO)
    sources = (
        ('fuel', ((date_only(r['date']), r['cost_bruto'], None) for r in fuel)),
        ('service', ((r.datum, r.potrazuje, str(r.popravka_kategorija or 'Nerazvrstano')) for r in services)),
        ('requisition', ((r.datum_trebovanja, r.vrednost_nab, str(r.popravka_kategorija or 'Nerazvrstano')) for r in requisitions)),
        ('recovery', ((r.datum, r.potrazuje, None) for r in recoveries)),
    )
    for source, rows in sources:
        for date, amount, category in rows:
            if not date or not start <= date <= end or amount is None:
                continue
            amount = Decimal(str(amount))
            totals[source] += amount
            counts[source] += 1
            monthly[date.replace(day=1)][source] = (monthly[date.replace(day=1)][source] or ZERO) + amount
            monthly[date.replace(day=1)]['count'] += 1
            if category:
                categories[category] += amount
    maintenance = totals['service'] + totals['requisition']
    for row in monthly.values():
        row['maintenance'] = (row['service'] or ZERO) + (row['requisition'] or ZERO)
    # Fuel receipts supply observations, not distance extrapolated to a whole year.
    readings = defaultdict(set)
    for row in fuel:
        date = date_only(row['date'])
        if date and start <= date <= end and row.get('mileage') and row['mileage'] > 0:
            readings[date].add(Decimal(str(row['mileage'])))
    points = [(date, min(values), max(values)) for date, values in sorted(readings.items())]
    mileage = None
    mileage_issue = ''
    if len(points) >= 2:
        if any(current[1] < previous[2] for previous, current in zip(points, points[1:])):
            mileage_issue = 'Očitanja kilometraže opadaju; proveriti unose ili zamenu brojača.'
        elif points[-1][2] > points[0][1]:
            mileage = {'start': points[0][0], 'end': points[-1][0], 'km': points[-1][2] - points[0][1]}
    scale = max((abs(value) for value in categories.values()), default=ZERO)
    return dict(totals=totals, counts=counts, maintenance=maintenance,
                maintenance_count=counts['service'] + counts['requisition'],
                net_maintenance=maintenance - totals['recovery'],
                monthly=list(monthly.values()), mileage=mileage, mileage_issue=mileage_issue,
                categories=[{'label': name, 'amount': amount, 'width': float(abs(amount) / scale * 100) if scale else 0}
                            for name, amount in sorted(categories.items(), key=lambda item: item[1], reverse=True)])
