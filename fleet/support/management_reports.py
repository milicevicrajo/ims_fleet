"""Read-only reports from existing fleet and procurement records."""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Exists, OuterRef, Q, Subquery
from django.db.models.functions import TruncDate
from django.utils import timezone

from fleet.models import JobCode, Lease, TrafficCard, TransactionNIS, TransactionOMV, Vehicle, VehicleHolding

ZERO = Decimal('0')
FUEL_LABELS = {'diesel': 'Dizel', 'petrol': 'Benzin', 'lpg': 'TNG / LPG', 'cng': 'CNG', 'adblue': 'AdBlue', 'other': 'Ostalo / nerazvrstano'}


def allowed_centers(user):
    if user.is_superuser:
        return set()
    raw = (getattr(user, 'allowed_center_codes', '') or '').replace(';', ',')
    return {x.strip() for x in raw.split(',') if x.strip()} | {str(x).strip() for x in user.allowed_centers.values_list('center', flat=True) if x}


def vehicle_insurance_rows(user, data, *, casco=False):
    day = data['as_of']
    job = JobCode.objects.filter(vehicle_id=OuterRef('pk'), assigned_date__lte=day).order_by('-assigned_date', '-pk')
    card = TrafficCard.objects.filter(vehicle_id=OuterRef('pk'), issue_date__lte=day).order_by('-issue_date', '-pk')
    holding = VehicleHolding.objects.filter(vehicle_id=OuterRef('pk'), start_date__lte=day).filter(Q(end_date__isnull=True) | Q(end_date__gte=day)).order_by('-start_date', '-pk')
    lease = Lease.objects.filter(vehicle_id=OuterRef('pk'), start_date__lte=day, end_date__gte=day)
    qs = Vehicle.objects.filter(otpis=False).annotate(
        report_center=Subquery(job.values('organizational_unit__center')[:1]),
        report_job=Subquery(job.values('organizational_unit__code')[:1]),
        report_unit=Subquery(job.values('organizational_unit__name')[:1]),
        report_plate=Subquery(card.values('registration_number')[:1]),
        report_registration=Subquery(card.values('registration_valid_until')[:1]),
        report_basis=Subquery(holding.values('basis')[:1]),
        report_lease=Exists(lease),
    )
    centers = allowed_centers(user)
    if centers:
        qs = qs.filter(report_center__in=centers)
    if data.get('center'):
        qs = qs.filter(report_center=data['center'])
    if data.get('category'):
        qs = qs.filter(category=data['category'])
    rows, unknown_year, excluded_contract, assumed = [], 0, 0, 0
    for v in qs.order_by('brand', 'model', 'pk'):
        # Do not claim inventory on a date before a known acquisition.
        if v.purchase_date and v.purchase_date > day:
            continue
        owned = v.report_basis == 'owned' or (v.report_basis is None and not v.report_lease)
        if not owned and not casco:
            excluded_contract += 1
            continue
        confirmed = v.report_basis == 'owned'
        if not casco and data.get('ownership') == 'confirmed' and not confirmed:
            continue
        age = day.year - v.year_of_manufacture if v.year_of_manufacture and 1886 <= v.year_of_manufacture <= day.year else None
        if age is None:
            unknown_year += 1
        if casco and (age is None or age <= 7):
            continue
        assumed += owned and not confirmed
        rows.append(dict(id=v.pk, plate=v.report_plate, vin=v.chassis_number, inventory=v.inventory_number,
            brand=v.brand, model=v.model, category=v.get_category_display(), year=v.year_of_manufacture,
            age=age, center=v.report_center, job=v.report_job, unit=v.report_unit, color=v.color,
            fuel=v.fuel_type, engine_volume=v.engine_volume, power=v.engine_power,
            seats=v.number_of_seats, weight=v.maximum_permissible_weight,
            first_registration=v.first_registration_date, registration=v.report_registration,
            purchase_value=v.purchase_value, book_value=v.value,
            ownership=('Evidentirano vlasništvo IMS' if confirmed else 'Vlasništvo IMS — podrazumevano pravilo') if owned else 'Korišćenje po ugovoru'))
    return rows, dict(unknown_year=unknown_year, excluded_contract=excluded_contract, assumed=assumed)


def fuel_kind(name):
    name = (name or '').strip().casefold()
    if 'adblue' in name or 'ad blue' in name:
        return 'adblue'
    if any(x in name for x in ('cng', 'ngv')):
        return 'cng'
    if any(x in name for x in ('lpg', 'tng', 'autogas')):
        return 'lpg'
    if any(x in name for x in ('dizel', 'diesel', 'ed maxx', 'edmaxx')):
        return 'diesel'
    if any(x in name for x in ('benzin', 'petrol', 'bmb')):
        return 'petrol'
    return 'other'


def fuel_report_rows(user, data):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(data['date_from'], time.min), tz)
    end = timezone.make_aware(datetime.combine(data['date_to'] + timedelta(days=1), time.min), tz)
    centers = allowed_centers(user)
    result = []
    for supplier, model, date_field, product_field, amount_field, qty_field, plate_field, currency_field in [
        ('nis', TransactionNIS, 'datum_transakcije', 'naziv_proizvoda', 'total', 'kolicina', 'registarska_oznaka_vozila', 'valuta'),
        ('omv', TransactionOMV, 'transaction_date', 'product_inv', 'gross_cc', 'quantity', 'license_plate_no', 'supplier_currency'),
    ]:
        if data.get('supplier') and data['supplier'] != supplier:
            continue
        history = JobCode.objects.filter(vehicle_id=OuterRef('vehicle_id'), assigned_date__lte=OuterRef('report_day')).order_by('-assigned_date', '-pk')
        qs = model.objects.filter(**{date_field+'__gte': start, date_field+'__lt': end}).annotate(report_day=TruncDate(date_field)).annotate(
            report_center=Subquery(history.values('organizational_unit__center')[:1]),
            report_job=Subquery(history.values('organizational_unit__code')[:1]),
        )
        if centers:
            qs = qs.filter(report_center__in=centers)
        if data.get('center'):
            qs = qs.filter(report_center=data['center'])
        if data.get('job_code'):
            qs = qs.filter(report_job=data['job_code'])
        if data.get('product'):
            qs = qs.filter(**{product_field+'__icontains': data['product']})
        for tr in qs.order_by(date_field, 'pk').values('pk', 'vehicle_id', 'report_day', 'report_center', 'report_job', product_field, amount_field, qty_field, plate_field, currency_field):
            kind = fuel_kind(tr[product_field])
            selected = data.get('fuel_type', 'fuel')
            if selected == 'fuel' and kind not in ('diesel', 'petrol', 'lpg', 'cng'):
                continue
            if selected not in ('all', 'fuel') and selected != kind:
                continue
            currency = (tr[currency_field] or '').strip().upper() or 'Nije uneta'
            currency = 'RSD' if currency in ('DIN', 'DINAR', 'RSD') else currency
            result.append(dict(id=f'{supplier}:{tr["pk"]}', date=tr['report_day'], month=tr['report_day'].strftime('%Y-%m'),
                supplier=supplier.upper(), center=(tr['report_center'] or '').strip() or 'Bez centra',
                job=(tr['report_job'] or '').strip() or 'Bez šifre', product=(tr[product_field] or '').strip() or 'Bez naziva',
                kind=kind, fuel_type=FUEL_LABELS[kind], quantity=tr[qty_field], gross=tr[amount_field], currency=currency,
                plate=tr[plate_field], vehicle_id=tr['vehicle_id']))
    result.sort(key=lambda r:(r['date'],r['id']), reverse=True)
    return result


FUEL_GROUPS = {'month': ['month'], 'center': ['center'], 'job': ['center', 'job'], 'product': ['product'], 'month_center': ['month', 'center'], 'month_job': ['month', 'center', 'job']}


def group_fuel_rows(rows, group_by):
    fields = FUEL_GROUPS[group_by]
    groups = {}
    for row in rows:
        # Products and currencies always stay separate; quantities may use different source units.
        key = tuple(row[f] for f in fields) + (row['fuel_type'], row['product'], row['currency'])
        if key not in groups:
            groups[key] = {**{f: row[f] for f in fields}, 'fuel_type': row['fuel_type'], 'product': row['product'], 'currency': row['currency'], 'count': 0, 'quantity': None, 'gross': None, 'missing_amount': 0}
        g = groups[key]
        g['count'] += 1
        g['missing_amount'] += row['gross'] is None
        for amount in ('quantity', 'gross'):
            if row[amount] is not None:
                g[amount] = (g[amount] or ZERO) + row[amount]
    return sorted(groups.values(), key=lambda r:tuple(str(r[f]) for f in fields)+(r['fuel_type'],r['product'],r['currency']))


def supplier_choices(source):
    from nabavka.models import EufItemSnapshot, GoodsSnapshot
    model, identifier = (GoodsSnapshot, 'partner_code') if source == 'goods' else (EufItemSnapshot, 'partner_pib')
    choices = {}
    for row in model.objects.order_by().values_list(identifier, 'partner_name').distinct():
        key, name = row
        if key is not None and str(key).strip():
            choices[str(key).strip()] = f'{name or "Bez naziva"} · {key}'
    return sorted(choices.items(), key=lambda x:x[1].casefold())


def supplier_parts_rows(data):
    from nabavka.models import EufItemSnapshot, GoodsSnapshot
    if not data.get('supplier'):
        return []
    goods = data['source'] == 'goods'
    model, identifier, name = (GoodsSnapshot, 'partner_code', 'article_name') if goods else (EufItemSnapshot, 'partner_pib', 'item_name')
    qs = model.objects.filter(**{identifier: data['supplier']}, document_date__range=(data['date_from'], data['date_to']))
    if data.get('article'):
        qs = qs.filter(**{name+'__icontains': data['article']})
    rows=[]
    for item in qs.order_by('-document_date','-pk'):
        rows.append(dict(date=item.document_date, supplier=item.partner_name, supplier_id=data['supplier'],
            invoice=item.linked_document if goods else item.invoice_number,
            document_type=item.document_type if goods else 'Ulazna faktura',
            article=item.article_name if goods else item.item_name,
            code=item.article_code if goods else item.account,
            quantity=item.quantity, unit=None if goods else item.uom, price=item.price,
            value=item.debit if goods else item.value,
            currency=(item.currency or 'Nije uneta') if goods else 'Izvor ne navodi valutu',
            synced=item.synced_at.date() if item.synced_at else None))
    return rows
