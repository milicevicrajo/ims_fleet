"""Estimated fuel consumption over actual, shared odometer boundaries."""
from decimal import Decimal

from fleet.models import FuelConsumption, VehicleAnalysisProfile
from fleet.support.fuel import ADBLUE_PRODUCT_KEYWORDS, get_vehicle_fuel_transaction_rows, is_fuel_product_name
from fleet.support.vehicle_detail import date_only


ZERO = Decimal('0')


def consumption_totals(rows, km):
    fuel = [r for r in rows if r['kind'] == 'fuel']
    adblue = [r for r in rows if r['kind'] == 'adblue']
    missing = any(r['amount'] is None or r['amount'] < 0 for r in fuel)
    liters = sum((r['amount'] for r in fuel if r['amount'] is not None), ZERO)
    if km is None:
        reason = 'Nedostaju dva upotrebljiva očitanja ili brojač opada.'
    elif km <= 0:
        reason = 'Nema pozitivne razlike kilometraže.'
    elif not fuel:
        reason = 'Nema evidentiranog goriva za usvojeni raspon.'
    elif missing:
        reason = 'Nedostaje količina goriva ili postoji negativna količina.'
    else:
        reason = ''
    return dict(liters=liters if fuel else None, count=len(fuel),
        adblue=sum((r['amount'] for r in adblue if r['amount'] is not None), ZERO),
        incomplete=missing, rate=liters * 100 / km if not reason else None, reason=reason)


def vehicle_consumption(vehicle, mileage):
    """Use (start, end] days so adjacent intervals never double-count fuel."""
    result = dict(mileage=mileage, rows=[], intervals=[], sources=[], excluded_count=0)
    start, end = mileage.get('coverage_start'), mileage.get('coverage_end')
    rows = []
    if mileage['valid'] and start and end and start < end:
        profiles = list(VehicleAnalysisProfile.objects.filter(vehicle=vehicle, effective_from__lte=end)
                        .order_by('-effective_from', '-pk'))

        def source(day):
            profile = next((p for p in profiles if p.effective_from <= day), None)
            return profile.fuel_source if profile else 'transactions'

        rows = [r for r in get_vehicle_fuel_transaction_rows(vehicle, start=start, end=end)
                if source(date_only(r['date'])) == 'transactions']
        if any(p.fuel_source == 'legacy' for p in profiles):
            for row in FuelConsumption.objects.filter(vehicle=vehicle, date__date__range=(start, end)):
                if source(date_only(row.date)) == 'legacy':
                    rows.append(dict(date=row.date, amount=row.amount, product=row.fuel_type,
                        supplier=row.supplier or 'Ranija evidencija', receipt_number='Ranija evidencija',
                        mileage=row.mileage))
        selected = []
        for row in rows:
            day = date_only(row['date'])
            if not start < day <= end:
                continue
            product = str(row['product'] or '').casefold()
            if any(word in product for word in ADBLUE_PRODUCT_KEYWORDS):
                kind = 'adblue'
            elif is_fuel_product_name(product) and not any(word in product for word in ('cng', 'ngv')):
                kind = 'fuel'
            else:
                result['excluded_count'] += 1
                continue
            selected.append(dict(row, day=day, kind=kind))
        rows = sorted(selected, key=lambda r: (r['day'], r['supplier']), reverse=True)
    result.update(consumption_totals(rows, mileage['total_km']))
    result.update(rows=rows, sources=sorted({r['supplier'] for r in rows}))
    for interval in mileage['intervals']:
        included = [r for r in rows if interval['start'] < r['day'] <= interval['end']]
        result['intervals'].append(dict(interval, **consumption_totals(included, interval['km'])))
    return result
