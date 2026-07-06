from collections import defaultdict
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef, Subquery, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from ..models import (
    FuelConsumption,
    Insurance,
    JobCode,
    Lease,
    Policy,
    Requisition,
    ServiceTransaction,
    TrafficCard,
    Vehicle,
)
from ..support.analytics import fixed_cost_per_km_ranges, is_red_zone, net_maintenance_cost
from ..support.dashboard import LONG_TERM_LEASE_TYPES, cost_per_km_period_analysis, vehicle_cost_per_km_rows
from ..support.fuel import date_range_for_datetime_field


@login_required
def fleet_analytics(request):
    today = date.today()
    first_month = today.replace(day=1)
    month_starts = []
    for offset in range(11, -1, -1):
        year = first_month.year
        month = first_month.month - offset
        while month <= 0:
            month += 12
            year -= 1
        month_starts.append(date(year, month, 1))

    start_dt, _ = date_range_for_datetime_field(month_starts[0])

    def number(value):
        return float(value or 0)

    def month_key(value):
        return value.strftime('%Y-%m')

    month_labels = [month.strftime('%m.%Y') for month in month_starts]
    month_keys = [month_key(month) for month in month_starts]
    start_of_last_12_months = today - timedelta(days=365)
    start_of_last_24_months = today - timedelta(days=730)
    cost_per_km_rows = vehicle_cost_per_km_rows(start_of_last_12_months)
    top_cost_per_km_vehicles = [row for row in cost_per_km_rows if row['cost_per_km'] is not None][:10]
    cost_per_km_periods = [
        {
            'key': '12m',
            'label': 'Poslednjih 12 meseci (okvirno)',
            'start': start_of_last_12_months,
            'end': today,
        },
        {
            'key': '24m',
            'label': 'Poslednja 24 meseca (okvirno)',
            'start': start_of_last_24_months,
            'end': today,
        },
    ]
    period_cost_per_km_rows, _, persistent_unprofitable_vehicles = cost_per_km_period_analysis(cost_per_km_periods)
    mileage_warning_rows = [row for row in period_cost_per_km_rows if row['requires_driver_warning']]
    suspicious_fuel_mileage_rows = [
        row
        for row in mileage_warning_rows
        if 'manja od 10 km' in row['mileage_issue']
    ]
    missing_mileage_rows = [
        row
        for row in mileage_warning_rows
        if 'manja od 10 km' not in row['mileage_issue']
    ]
    status_cost_per_km_by_period = {}
    for period in cost_per_km_periods:
        status_cost_per_km_by_period[period['key']] = [
            row
            for row in period_cost_per_km_rows
            if (
                row['period_key'] == period['key']
                and row['cost_per_km'] is not None
                and row['status'] in ('Rizično', 'Neisplativo')
            )
        ]
    status_cost_per_km_rows = status_cost_per_km_by_period['12m'] + status_cost_per_km_by_period['24m']

    fuel_by_month = {
        month_key(row['month']): number(row['total'])
        for row in FuelConsumption.objects.filter(date__gte=start_dt)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('cost_bruto'))
        .order_by('month')
    }
    service_by_month = {
        month_key(row['month']): number(row['total'])
        for row in ServiceTransaction.objects.filter(datum__gte=month_starts[0])
        .annotate(month=TruncMonth('datum'))
        .values('month')
        .annotate(total=Sum('potrazuje'))
        .order_by('month')
    }
    fuel_liters_by_month = {
        month_key(row['month']): number(row['total'])
        for row in FuelConsumption.objects.filter(date__gte=start_dt)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    }

    monthly_cost_chart = [
        {
            'label': label,
            'fuel': fuel_by_month.get(key, 0),
            'service': service_by_month.get(key, 0),
            'liters': fuel_liters_by_month.get(key, 0),
        }
        for key, label in zip(month_keys, month_labels)
    ]

    latest_center = JobCode.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-assigned_date').values('organizational_unit__center')[:1]
    latest_registration = TrafficCard.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-issue_date').values('registration_number')[:1]

    vehicles = list(
        Vehicle.objects.filter(otpis=False).annotate(
            center_code=Subquery(latest_center),
            registration_number=Subquery(latest_registration),
            service_cost=Subquery(
                ServiceTransaction.objects.filter(vehicle=OuterRef('pk'))
                .values('vehicle')
                .annotate(total=Sum('potrazuje'))
                .values('total')[:1]
            ),
            requisition_cost=Subquery(
                Requisition.objects.filter(vehicle=OuterRef('pk'))
                .values('vehicle')
                .annotate(total=Sum('vrednost_nab'))
                .values('total')[:1]
            ),
            fuel_cost=Subquery(
                FuelConsumption.objects.filter(vehicle=OuterRef('pk'))
                .values('vehicle')
                .annotate(total=Sum('cost_bruto'))
                .values('total')[:1]
            ),
            fuel_liters=Subquery(
                FuelConsumption.objects.filter(vehicle=OuterRef('pk'))
                .values('vehicle')
                .annotate(total=Sum('amount'))
                .values('total')[:1]
            ),
            insurance_recovery=Subquery(
                Insurance.objects.filter(vehicle=OuterRef('pk'), kola=True)
                .values('vehicle')
                .annotate(total=Sum('potrazuje'))
                .values('total')[:1]
            ),
            long_term_rental=Exists(
                Lease.objects.filter(vehicle=OuterRef('pk'), lease_type__in=LONG_TERM_LEASE_TYPES)
            )
        )
    )

    vehicle_rows = []
    for vehicle in vehicles:
        value = number(vehicle.value)
        service_cost = number(vehicle.service_cost)
        requisition_cost = number(vehicle.requisition_cost)
        fuel_cost = number(vehicle.fuel_cost)
        insurance_recovery = number(vehicle.insurance_recovery)
        net_cost = number(net_maintenance_cost(service_cost, requisition_cost, insurance_recovery))
        total_cost = service_cost + requisition_cost + fuel_cost
        ratio = net_cost / value * 100 if value else 0
        vehicle_rows.append({
            'label': vehicle.registration_number or f'{vehicle.brand} {vehicle.model}',
            'vehicle_id': vehicle.id,
            'brand': vehicle.brand,
            'model': vehicle.model,
            'center': vehicle.center_code or 'Bez centra',
            'value': value,
            'service_cost': service_cost,
            'requisition_cost': requisition_cost,
            'insurance_recovery': insurance_recovery,
            'net_maintenance_cost': net_cost,
            'fuel_cost': fuel_cost,
            'fuel_liters': number(vehicle.fuel_liters),
            'total_cost': total_cost,
            'service_value_ratio': ratio,
            'long_term_rental': vehicle.long_term_rental,
            'red_zone': is_red_zone(vehicle.long_term_rental, value, net_cost),
        })

    top_cost_vehicles = sorted(vehicle_rows, key=lambda row: row['total_cost'], reverse=True)[:10]
    top_service_ratio = sorted(
        [row for row in vehicle_rows if row['value'] > 0],
        key=lambda row: row['service_value_ratio'],
        reverse=True
    )[:10]
    red_zone_rows = [row for row in top_service_ratio if row['red_zone']]

    center_map = defaultdict(lambda: {
        'vehicle_count': 0,
        'value': 0,
        'service_cost': 0,
        'requisition_cost': 0,
        'insurance_recovery': 0,
        'net_maintenance_cost': 0,
        'fuel_cost': 0,
        'fuel_liters': 0,
        'red_zone_count': 0,
    })
    for row in vehicle_rows:
        center = center_map[row['center']]
        center['vehicle_count'] += 1
        center['value'] += row['value']
        center['service_cost'] += row['service_cost']
        center['requisition_cost'] += row['requisition_cost']
        center['insurance_recovery'] += row['insurance_recovery']
        center['net_maintenance_cost'] += row['net_maintenance_cost']
        center['fuel_cost'] += row['fuel_cost']
        center['fuel_liters'] += row['fuel_liters']
        center['red_zone_count'] += 1 if row['red_zone'] else 0

    center_rows = []
    for center_code, row in center_map.items():
        center_rows.append({
            'center': center_code,
            'vehicle_count': row['vehicle_count'],
            'value': row['value'],
            'service_cost': row['service_cost'],
            'requisition_cost': row['requisition_cost'],
            'insurance_recovery': row['insurance_recovery'],
            'net_maintenance_cost': row['net_maintenance_cost'],
            'fuel_cost': row['fuel_cost'],
            'fuel_liters': row['fuel_liters'],
            'service_value_ratio': row['net_maintenance_cost'] / row['value'] * 100 if row['value'] else 0,
            'cost_per_vehicle': (row['service_cost'] + row['requisition_cost'] + row['fuel_cost']) / row['vehicle_count'] if row['vehicle_count'] else 0,
            'red_zone_count': row['red_zone_count'],
        })
    center_rows.sort(key=lambda row: row['cost_per_vehicle'], reverse=True)

    fuel_supplier_rows = [
        {'label': row['supplier'] or 'Nepoznato', 'value': number(row['total'])}
        for row in FuelConsumption.objects.filter(date__gte=start_dt)
        .values('supplier')
        .annotate(total=Sum('cost_bruto'))
        .order_by('-total')[:8]
    ]
    service_category_rows = [
        {'label': row['popravka_kategorija__name'] or 'Nerazvrstano', 'value': number(row['total'])}
        for row in ServiceTransaction.objects.filter(datum__gte=month_starts[0])
        .values('popravka_kategorija__name')
        .annotate(total=Sum('potrazuje'))
        .order_by('-total')[:8]
    ]

    last_6_months = monthly_cost_chart[-6:]
    avg_monthly_fuel = sum(row['fuel'] for row in last_6_months) / len(last_6_months) if last_6_months else 0
    avg_monthly_service = sum(row['service'] for row in last_6_months) / len(last_6_months) if last_6_months else 0
    avg_monthly_liters = sum(row['liters'] for row in last_6_months) / len(last_6_months) if last_6_months else 0

    total_fleet_value = sum(row['value'] for row in vehicle_rows)
    total_service_cost = sum(row['service_cost'] for row in vehicle_rows)
    total_requisition_cost = sum(row['requisition_cost'] for row in vehicle_rows)
    total_insurance_recovery = sum(row['insurance_recovery'] for row in vehicle_rows)
    total_net_maintenance_cost = sum(row['net_maintenance_cost'] for row in vehicle_rows)
    total_fuel_cost = sum(row['fuel_cost'] for row in vehicle_rows)
    total_fuel_liters = sum(row['fuel_liters'] for row in vehicle_rows)
    priced_cost_per_km_rows = [row for row in cost_per_km_rows if row['cost_per_km'] is not None]
    total_cost_per_km_cost = sum(row['total_cost'] for row in priced_cost_per_km_rows)
    total_cost_per_km_mileage = sum(row['annual_km'] for row in priced_cost_per_km_rows)
    analytics_summary = {
        'vehicle_count': len(vehicle_rows),
        'cost_per_km_vehicle_count': len(cost_per_km_rows),
        'total_fleet_value': total_fleet_value,
        'total_service_cost': total_service_cost,
        'total_requisition_cost': total_requisition_cost,
        'total_insurance_recovery': total_insurance_recovery,
        'total_net_maintenance_cost': total_net_maintenance_cost,
        'total_fuel_cost': total_fuel_cost,
        'total_fuel_liters': total_fuel_liters,
        'total_cost_per_km_mileage': total_cost_per_km_mileage,
        'avg_cost_per_km': total_cost_per_km_cost / total_cost_per_km_mileage if total_cost_per_km_mileage else 0,
        'red_zone_count': sum(1 for row in vehicle_rows if row['red_zone']),
        'service_value_ratio': total_net_maintenance_cost / total_fleet_value * 100 if total_fleet_value else 0,
        'projected_fuel_cost': avg_monthly_fuel * 12,
        'projected_service_cost': avg_monthly_service * 12,
        'projected_fuel_liters': avg_monthly_liters * 12,
    }

    context = {
        'title': 'Analitika voznog parka',
        'analytics_summary': analytics_summary,
        'monthly_cost_chart': monthly_cost_chart,
        'top_cost_vehicles': top_cost_vehicles,
        'top_cost_per_km_vehicles': top_cost_per_km_vehicles,
        'status_cost_per_km_12m_rows': status_cost_per_km_by_period['12m'],
        'status_cost_per_km_24m_rows': status_cost_per_km_by_period['24m'],
        'status_cost_per_km_rows': status_cost_per_km_rows,
        'cost_per_km_ranges': fixed_cost_per_km_ranges(),
        'persistent_unprofitable_vehicles': persistent_unprofitable_vehicles[:20],
        'suspicious_fuel_mileage_rows': suspicious_fuel_mileage_rows[:50],
        'missing_mileage_rows': missing_mileage_rows[:50],
        'top_service_ratio': top_service_ratio,
        'red_zone_rows': red_zone_rows,
        'center_rows': center_rows,
        'fuel_supplier_rows': fuel_supplier_rows,
        'service_category_rows': service_category_rows,
    }
    return render(request, 'fleet/analytics.html', context)
