from collections import defaultdict
from datetime import date, timedelta

from django.db.models import Count, ExpressionWrapper, F, IntegerField, Max, Min, OuterRef, Subquery, Sum

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
    VehicleTravelOrder,
)
from .analytics import cost_per_km_status, cost_per_km_thresholds
from .fuel import date_range_for_datetime_field

LONG_TERM_LEASE_TYPES = set(Lease.LONG_TERM_LEASE_TYPE_VALUES)


def vehicle_cost_per_km_rows(period_start_date, period_end_date=None, limit=None, vehicle_ids=None):
    period_end_date = period_end_date or date.today()
    period_start_dt, _ = date_range_for_datetime_field(period_start_date)
    period_end_exclusive_dt, _ = date_range_for_datetime_field(period_end_date + timedelta(days=1))

    def number(value):
        return float(value or 0)

    latest_center = JobCode.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-assigned_date').values('organizational_unit__center')[:1]
    latest_registration = TrafficCard.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-issue_date').values('registration_number')[:1]

    vehicles = Vehicle.objects.filter(
        otpis=False,
        category__in=['PUTNICKO VOZILO', 'TERETNO VOZILO'],
    )
    if vehicle_ids is not None:
        if isinstance(vehicle_ids, (list, tuple, set)):
            vehicles = vehicles.filter(pk__in=list(vehicle_ids))
        else:
            vehicles = vehicles.filter(pk=vehicle_ids)

    vehicles = vehicles.annotate(
        center_code=Subquery(latest_center),
        registration_number=Subquery(latest_registration),
        fuel_cost_period=Subquery(
            FuelConsumption.objects.filter(
                vehicle=OuterRef('pk'),
                date__gte=period_start_dt,
                date__lt=period_end_exclusive_dt,
            )
            .values('vehicle')
            .annotate(total=Sum('cost_bruto'))
            .values('total')[:1]
        ),
        fuel_liters_period=Subquery(
            FuelConsumption.objects.filter(
                vehicle=OuterRef('pk'),
                date__gte=period_start_dt,
                date__lt=period_end_exclusive_dt,
            )
            .values('vehicle')
            .annotate(total=Sum('amount'))
            .values('total')[:1]
        ),
        min_fuel_mileage_period=Subquery(
            FuelConsumption.objects.filter(
                vehicle=OuterRef('pk'),
                date__gte=period_start_dt,
                date__lt=period_end_exclusive_dt,
            )
            .values('vehicle')
            .annotate(total=Min('mileage'))
            .values('total')[:1]
        ),
        max_fuel_mileage_period=Subquery(
            FuelConsumption.objects.filter(
                vehicle=OuterRef('pk'),
                date__gte=period_start_dt,
                date__lt=period_end_exclusive_dt,
            )
            .values('vehicle')
            .annotate(total=Max('mileage'))
            .values('total')[:1]
        ),
        fuel_entry_count_period=Subquery(
            FuelConsumption.objects.filter(
                vehicle=OuterRef('pk'),
                date__gte=period_start_dt,
                date__lt=period_end_exclusive_dt,
            )
            .values('vehicle')
            .annotate(total=Count('id'))
            .values('total')[:1]
        ),
        travel_order_km_period=Subquery(
            VehicleTravelOrder.objects.filter(
                vehicle=OuterRef('pk'),
                created_at__lte=period_end_date,
                closed_at__gte=period_start_date,
                start_mileage__isnull=False,
                end_mileage__isnull=False,
                start_mileage__gt=0,
                end_mileage__gt=F('start_mileage'),
            )
            .annotate(distance=ExpressionWrapper(F('end_mileage') - F('start_mileage'), output_field=IntegerField()))
            .order_by()
            .values('vehicle')
            .annotate(total=Sum('distance'))
            .values('total')[:1]
        ),
        service_cost_period=Subquery(
            ServiceTransaction.objects.filter(
                vehicle=OuterRef('pk'),
                datum__gte=period_start_date,
                datum__lte=period_end_date,
            )
            .values('vehicle')
            .annotate(total=Sum('potrazuje'))
            .values('total')[:1]
        ),
        requisition_cost_period=Subquery(
            Requisition.objects.filter(
                vehicle=OuterRef('pk'),
                datum_trebovanja__gte=period_start_date,
                datum_trebovanja__lte=period_end_date,
            )
            .values('vehicle')
            .annotate(total=Sum('vrednost_nab'))
            .values('total')[:1]
        ),
        insurance_recovery_period=Subquery(
            Insurance.objects.filter(
                vehicle=OuterRef('pk'),
                kola=True,
                datum__gte=period_start_date,
                datum__lte=period_end_date,
            )
            .values('vehicle')
            .annotate(total=Sum('potrazuje'))
            .values('total')[:1]
        ),
        policy_cost_period=Subquery(
            Policy.objects.filter(
                vehicle=OuterRef('pk'),
                start_date__lte=period_end_date,
                end_date__gte=period_start_date,
            )
            .values('vehicle')
            .annotate(total=Sum('premium_amount'))
            .values('total')[:1]
        ),
        lease_payment_period=Subquery(
            Lease.objects.filter(
                vehicle=OuterRef('pk'),
                start_date__lte=period_end_date,
                end_date__gte=period_start_date,
            )
            .values('vehicle')
            .annotate(total=Sum('current_payment_amount'))
            .values('total')[:1]
        ),
    )

    rows = []
    for vehicle in vehicles:
        fuel_entry_count = number(vehicle.fuel_entry_count_period)
        fuel_km = number(vehicle.max_fuel_mileage_period) - number(vehicle.min_fuel_mileage_period)
        travel_order_km = number(vehicle.travel_order_km_period)
        mileage_source = 'Gorivo'
        mileage_issue = ''
        requires_driver_warning = False

        suspicious_fuel_mileage = fuel_entry_count > 0 and fuel_km < 10

        if fuel_entry_count >= 2 and fuel_km >= 10:
            annual_km = fuel_km
        elif travel_order_km > 0:
            annual_km = travel_order_km
            mileage_source = 'Putni nalozi'
            if suspicious_fuel_mileage:
                mileage_issue = 'Kilometraža pri točenju je manja od 10 km; korišćeni su putni nalozi.'
            elif fuel_entry_count < 2:
                mileage_issue = 'Nema dovoljno kilometraže pri točenju; korišćeni su putni nalozi.'
            else:
                mileage_issue = 'Sumnjiva kilometraža pri točenju; korišćeni su putni nalozi.'
        else:
            annual_km = 0
            mileage_source = 'Nema podatka'
            requires_driver_warning = True
            if suspicious_fuel_mileage:
                mileage_issue = 'Kilometraža pri točenju je manja od 10 km. Opomenuti vozače da unose stvarnu kilometražu pri sipanju goriva.'
            else:
                mileage_issue = 'Opomenuti vozače da unose kilometražu pri točenju goriva.'

        fuel_cost = number(vehicle.fuel_cost_period)
        service_cost = number(vehicle.service_cost_period)
        requisition_cost = number(vehicle.requisition_cost_period)
        policy_cost = number(vehicle.policy_cost_period)
        lease_annual_cost = number(vehicle.lease_payment_period) * 12
        insurance_recovery = number(vehicle.insurance_recovery_period)

        depreciation_base_date = vehicle.purchase_date or vehicle.first_registration_date
        annual_depreciation = 0
        if vehicle.purchase_value and vehicle.value is not None and depreciation_base_date:
            days_in_use = max((period_end_date - depreciation_base_date).days, 365)
            total_depreciation = max(number(vehicle.purchase_value) - number(vehicle.value), 0)
            annual_depreciation = total_depreciation / days_in_use * 365

        total_cost = (
            fuel_cost
            + service_cost
            + requisition_cost
            + policy_cost
            + annual_depreciation
            + lease_annual_cost
            - insurance_recovery
        )
        if total_cost <= 0:
            continue

        cost_per_km = total_cost / annual_km if annual_km > 0 else None

        rows.append({
            'label': vehicle.registration_number or str(vehicle),
            'vehicle_id': vehicle.id,
            'brand': vehicle.brand,
            'model': vehicle.model,
            'category': vehicle.category,
            'center': vehicle.center_code or 'Bez centra',
            'annual_km': annual_km,
            'mileage_source': mileage_source,
            'mileage_issue': mileage_issue,
            'requires_driver_warning': requires_driver_warning,
            'fuel_cost': fuel_cost,
            'fuel_liters': number(vehicle.fuel_liters_period),
            'service_cost': service_cost,
            'requisition_cost': requisition_cost,
            'policy_cost': policy_cost,
            'annual_depreciation': annual_depreciation,
            'lease_annual_cost': lease_annual_cost,
            'insurance_recovery': insurance_recovery,
            'total_cost': total_cost,
            'cost_per_km': cost_per_km,
        })

    rows.sort(key=lambda row: row['cost_per_km'] or 0, reverse=True)
    return rows[:limit] if limit else rows


def cost_per_km_period_analysis(periods):
    period_rows = []
    thresholds_by_period = []
    rows_by_vehicle = defaultdict(list)

    for period in periods:
        rows = vehicle_cost_per_km_rows(period['start'], period['end'])
        thresholds = cost_per_km_thresholds(rows)
        for threshold in thresholds.values():
            threshold['period_label'] = period['label']
            thresholds_by_period.append(threshold)

        for row in rows:
            row['period_key'] = period['key']
            row['period_label'] = period['label']
            row['status'] = cost_per_km_status(row['cost_per_km'], thresholds.get(row['category']))
            period_rows.append(row)
            rows_by_vehicle[row['vehicle_id']].append(row)

    persistent_unprofitable = []
    required_periods = {period['key'] for period in periods}
    for rows in rows_by_vehicle.values():
        rows_by_period = {row['period_key']: row for row in rows}
        if not required_periods.issubset(rows_by_period):
            continue
        if not all(rows_by_period[key]['status'] == 'Neisplativo' for key in required_periods):
            continue

        primary = rows_by_period[periods[0]['key']].copy()
        comparison = rows_by_period[periods[1]['key']]
        primary['comparison_period_label'] = comparison['period_label']
        primary['comparison_cost_per_km'] = comparison['cost_per_km']
        primary['change_percent'] = (
            (primary['cost_per_km'] - comparison['cost_per_km']) / comparison['cost_per_km'] * 100
            if comparison['cost_per_km']
            else 0
        )
        persistent_unprofitable.append(primary)

    persistent_unprofitable.sort(key=lambda row: row['cost_per_km'], reverse=True)
    return period_rows, thresholds_by_period, persistent_unprofitable
