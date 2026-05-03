from collections import defaultdict
import datetime
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Exists, F, OuterRef, Subquery, Sum
from django.shortcuts import render

from ..models import (
    DraftInsurance,
    DraftPolicy,
    DraftRequisition,
    DraftServiceTransaction,
    FuelConsumption,
    Insurance,
    JobCode,
    Lease,
    Policy,
    Requisition,
    ServiceTransaction,
    Vehicle,
)
from ..support.analytics import is_red_zone, net_maintenance_cost
from ..support.dashboard import LONG_TERM_LEASE_TYPES
from ..support.fuel import date_range_for_datetime_field


@login_required
def dashboard(request):
    services_without_vehicle = DraftServiceTransaction.objects.count()
    policies_without_vehicle = DraftPolicy.objects.count()
    requisitions_without_vehicle = DraftRequisition.objects.count()
    draft_insurance_count = DraftInsurance.objects.count()

    today = date.today()
    thirty_days_from_now = today + timedelta(days=30)

    newest_policy = Policy.objects.filter(
        vehicle=OuterRef('vehicle'),
        insurance_type=OuterRef('insurance_type'),
        is_renewable=True,
    ).order_by('-end_date').values('end_date')[:1]

    expiring_policies = Policy.objects.annotate(
        latest_end_date=Subquery(newest_policy)
    ).filter(
        end_date__gte=today,
        end_date__lte=thirty_days_from_now,
        end_date=F('latest_end_date'),
        is_renewable=True,
    )

    expiring_policies_count = expiring_policies.count()

    newer_policy_exists = Policy.objects.filter(
        vehicle=OuterRef('vehicle'),
        insurance_type=OuterRef('insurance_type'),
        start_date__gt=OuterRef('start_date'),
        is_renewable=True,
    )

    expired_unrenewed_policies = Policy.objects.annotate(
        has_newer_policy=Exists(newer_policy_exists)
    ).filter(
        end_date__lt=today,
        has_newer_policy=False,
        is_renewable=True,
    )

    expired_unrenewed_policies_count = expired_unrenewed_policies.count()

    current_year = datetime.datetime.now().year
    first_day_of_current_month = date.today().replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    start_of_year = date.today().replace(month=1, day=1)
    start_of_last_12_months = date.today() - timedelta(days=365)
    start_of_last_12_months_dt, _ = date_range_for_datetime_field(start_of_last_12_months)

    total_vehicles = Vehicle.objects.filter(otpis=False).count()
    passenger_vehicles = Vehicle.objects.filter(category='PUTNICKO VOZILO').filter(otpis=False).count()
    transport_vehicles = Vehicle.objects.filter(category='TERETNO VOZILO').filter(otpis=False).count()

    average_age = Vehicle.objects.aggregate(avg_age=(current_year - Avg('year_of_manufacture')))
    book_value = Vehicle.objects.filter(purchase_date__lte=last_day_of_previous_month).aggregate(total_value=Sum('value'))
    yearly_fuel_costs = FuelConsumption.objects.filter(date__gte=start_of_last_12_months_dt).aggregate(total_fuel_cost=Sum('cost_bruto'))
    yearly_service_costs = ServiceTransaction.objects.filter(datum__gte=start_of_year).aggregate(total_service_cost=Sum('potrazuje'))

    latest_jobcode = JobCode.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-assigned_date')

    vehicles = Vehicle.objects.annotate(
        center_code=Subquery(latest_jobcode.values('organizational_unit__center')[:1]),
        manufacture_year=F('year_of_manufacture'),
        current_value=F('value'),
        fuel_amount=Subquery(
            FuelConsumption.objects.filter(vehicle=OuterRef('pk'))
            .values('vehicle')
            .annotate(total=Sum('amount'))
            .values('total')[:1]
        ),
        fuel_cost=Subquery(
            FuelConsumption.objects.filter(vehicle=OuterRef('pk'))
            .values('vehicle')
            .annotate(total=Sum('cost_bruto'))
            .values('total')[:1]
        ),
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

    grouped = defaultdict(list)
    for vehicle in vehicles:
        grouped[vehicle.center_code].append(vehicle)

    center_data = []
    for center, vehicle_list in grouped.items():
        count = len(vehicle_list)
        total_value = sum([vehicle.current_value or 0 for vehicle in vehicle_list])
        avg_value = total_value / count if count else 0
        total_fuel_quantity = sum([vehicle.fuel_amount or 0 for vehicle in vehicle_list])
        total_fuel_price = sum([vehicle.fuel_cost or 0 for vehicle in vehicle_list])
        total_service_cost = sum([vehicle.service_cost or 0 for vehicle in vehicle_list])
        total_requisition_cost = sum([vehicle.requisition_cost or 0 for vehicle in vehicle_list])
        total_insurance_recovery = sum([vehicle.insurance_recovery or 0 for vehicle in vehicle_list])
        total_net_maintenance_cost = sum([
            net_maintenance_cost(vehicle.service_cost, vehicle.requisition_cost, vehicle.insurance_recovery)
            for vehicle in vehicle_list
        ])
        red_zone_count = sum(
            1
            for vehicle in vehicle_list
            if is_red_zone(
                vehicle.long_term_rental,
                vehicle.current_value,
                net_maintenance_cost(vehicle.service_cost, vehicle.requisition_cost, vehicle.insurance_recovery),
            )
        )
        avg_year = sum([vehicle.year_of_manufacture or 0 for vehicle in vehicle_list]) / count if count else 0
        avg_age = current_year - avg_year if avg_year else None

        center_data.append({
            'center_code': center,
            'center_name': f'Centar {center}' if center else 'Bez centra',
            'vehicle_count': count,
            'avg_age': avg_age,
            'total_value': total_value,
            'avg_value': avg_value,
            'total_fuel_quantity': total_fuel_quantity,
            'total_fuel_price': total_fuel_price,
            'total_service_cost': total_service_cost,
            'total_requisition_cost': total_requisition_cost,
            'total_insurance_recovery': total_insurance_recovery,
            'total_net_maintenance_cost': total_net_maintenance_cost,
            'service_value_ratio': (total_net_maintenance_cost / total_value * 100) if total_value else 0,
            'red_zone_count': red_zone_count,
        })

    dashboard_totals = {
        'vehicle_count': sum(center['vehicle_count'] for center in center_data),
        'total_value': sum(center['total_value'] or 0 for center in center_data),
        'total_fuel_quantity': sum(center['total_fuel_quantity'] or 0 for center in center_data),
        'total_fuel_price': sum(center['total_fuel_price'] or 0 for center in center_data),
        'total_service_cost': sum(center['total_service_cost'] or 0 for center in center_data),
        'total_requisition_cost': sum(center['total_requisition_cost'] or 0 for center in center_data),
        'total_insurance_recovery': sum(center['total_insurance_recovery'] or 0 for center in center_data),
        'total_net_maintenance_cost': sum(center['total_net_maintenance_cost'] or 0 for center in center_data),
        'red_zone_count': sum(center['red_zone_count'] or 0 for center in center_data),
    }
    dashboard_averages = {
        'avg_age': average_age['avg_age'],
        'avg_value': (
            dashboard_totals['total_value'] / dashboard_totals['vehicle_count']
            if dashboard_totals['vehicle_count']
            else 0
        ),
        'avg_fuel_quantity': (
            dashboard_totals['total_fuel_quantity'] / dashboard_totals['vehicle_count']
            if dashboard_totals['vehicle_count']
            else 0
        ),
        'avg_fuel_price': (
            dashboard_totals['total_fuel_price'] / dashboard_totals['vehicle_count']
            if dashboard_totals['vehicle_count']
            else 0
        ),
        'service_value_ratio': (
            dashboard_totals['total_net_maintenance_cost'] / dashboard_totals['total_value'] * 100
            if dashboard_totals['total_value']
            else 0
        ),
    }

    red_zone_vehicles = []
    for vehicle in vehicles:
        vehicle_value = vehicle.current_value or 0
        net_cost = net_maintenance_cost(vehicle.service_cost, vehicle.requisition_cost, vehicle.insurance_recovery)
        if is_red_zone(vehicle.long_term_rental, vehicle_value, net_cost):
            vehicle.service_cost_total = vehicle.service_cost or 0
            vehicle.requisition_cost_total = vehicle.requisition_cost or 0
            vehicle.insurance_recovery_total = vehicle.insurance_recovery or 0
            vehicle.net_maintenance_cost = net_cost
            vehicle.value_gap = net_cost - vehicle_value
            vehicle.service_value_ratio = net_cost / vehicle_value * 100
            red_zone_vehicles.append(vehicle)
    red_zone_vehicles.sort(key=lambda vehicle: vehicle.value_gap, reverse=True)

    fleet_analysis = {
        'total_value': dashboard_totals['total_value'],
        'total_service_cost': dashboard_totals['total_service_cost'],
        'total_requisition_cost': dashboard_totals['total_requisition_cost'],
        'total_insurance_recovery': dashboard_totals['total_insurance_recovery'],
        'total_net_maintenance_cost': dashboard_totals['total_net_maintenance_cost'],
        'service_value_ratio': dashboard_averages['service_value_ratio'],
        'total_fuel_quantity': dashboard_totals['total_fuel_quantity'],
        'total_fuel_price': dashboard_totals['total_fuel_price'],
        'yearly_fuel_costs': yearly_fuel_costs['total_fuel_cost'] or 0,
        'red_zone_count': dashboard_totals['red_zone_count'],
        'center_count': len(center_data),
    }

    context = {
        'services_without_vehicle': services_without_vehicle,
        'policies_without_vehicle': policies_without_vehicle,
        'draft_insurance_count': draft_insurance_count,
        'requisitions_without_vehicle': requisitions_without_vehicle,
        'expiring_policies': expiring_policies,
        'expiring_policies_count': expiring_policies_count,
        'expired_unrenewed_policies': expired_unrenewed_policies,
        'expired_unrenewed_policies_count': expired_unrenewed_policies_count,
        'total_vehicles': total_vehicles,
        'passenger_vehicles': passenger_vehicles,
        'transport_vehicles': transport_vehicles,
        'average_age': average_age['avg_age'],
        'book_value': book_value['total_value'],
        'yearly_fuel_costs': yearly_fuel_costs['total_fuel_cost'],
        'yearly_service_costs': yearly_service_costs['total_service_cost'],
        'red_zone_vehicles': red_zone_vehicles,
        'centers': center_data,
        'dashboard_totals': dashboard_totals,
        'dashboard_averages': dashboard_averages,
        'fleet_analysis': fleet_analysis,
    }

    return render(request, 'fleet/dashboard.html', context)
