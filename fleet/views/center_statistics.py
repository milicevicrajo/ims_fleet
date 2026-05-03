import datetime

from django.db.models import Exists, OuterRef, Q, Subquery, Sum
from django.db.models.functions import TruncMonth, TruncYear
from django.http import HttpResponseForbidden
from django.shortcuts import render

from ..models import FuelConsumption, Insurance, JobCode, Lease, Policy, Requisition, ServiceTransaction, Vehicle
from ..support.analytics import is_red_zone, net_maintenance_cost
from ..support.dashboard import LONG_TERM_LEASE_TYPES


def center_statistics(request, center_code):
    if not request.user.allowed_centers.filter(center=center_code).exists():
        return HttpResponseForbidden("Nemate pristup ovim podacima.")

    latest_center_code = JobCode.objects.filter(
        vehicle=OuterRef('vehicle')
    ).order_by('-assigned_date').values('organizational_unit__center')[:1]

    latest_vehicle_center_code = JobCode.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-assigned_date').values('organizational_unit__center')[:1]

    center_vehicles = list(
        Vehicle.objects.annotate(
            center_code=Subquery(latest_vehicle_center_code),
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
            insurance_recovery=Subquery(
                Insurance.objects.filter(vehicle=OuterRef('pk'), kola=True)
                .values('vehicle')
                .annotate(total=Sum('potrazuje'))
                .values('total')[:1]
            ),
            long_term_rental=Exists(
                Lease.objects.filter(vehicle=OuterRef('pk'), lease_type__in=LONG_TERM_LEASE_TYPES)
            ),
        ).filter(center_code=center_code)
    )

    center_vehicle_count = len(center_vehicles)
    center_total_value = sum((vehicle.value or 0) for vehicle in center_vehicles)
    center_total_service_cost = sum((vehicle.service_cost or 0) for vehicle in center_vehicles)
    center_total_requisition_cost = sum((vehicle.requisition_cost or 0) for vehicle in center_vehicles)
    center_total_insurance_recovery = sum((vehicle.insurance_recovery or 0) for vehicle in center_vehicles)
    center_total_net_maintenance_cost = sum(
        net_maintenance_cost(vehicle.service_cost, vehicle.requisition_cost, vehicle.insurance_recovery)
        for vehicle in center_vehicles
    )
    center_total_fuel_quantity = sum((vehicle.fuel_amount or 0) for vehicle in center_vehicles)
    center_total_fuel_cost = sum((vehicle.fuel_cost or 0) for vehicle in center_vehicles)
    center_avg_year = (
        sum((vehicle.year_of_manufacture or 0) for vehicle in center_vehicles) / center_vehicle_count
        if center_vehicle_count
        else 0
    )
    center_red_zone_vehicles = []
    for vehicle in center_vehicles:
        vehicle_value = vehicle.value or 0
        service_cost = vehicle.service_cost or 0
        requisition_cost = vehicle.requisition_cost or 0
        insurance_recovery = vehicle.insurance_recovery or 0
        net_cost = net_maintenance_cost(service_cost, requisition_cost, insurance_recovery)
        vehicle.service_cost_total = service_cost
        vehicle.requisition_cost_total = requisition_cost
        vehicle.insurance_recovery_total = insurance_recovery
        vehicle.net_maintenance_cost = net_cost
        vehicle.service_value_ratio = net_cost / vehicle_value * 100 if vehicle_value else 0
        vehicle.value_gap = net_cost - vehicle_value
        if is_red_zone(vehicle.long_term_rental, vehicle_value, net_cost):
            center_red_zone_vehicles.append(vehicle)
    center_red_zone_vehicles.sort(key=lambda vehicle: vehicle.value_gap, reverse=True)

    center_analysis = {
        'vehicle_count': center_vehicle_count,
        'total_value': center_total_value,
        'avg_value': center_total_value / center_vehicle_count if center_vehicle_count else 0,
        'avg_age': datetime.datetime.now().year - center_avg_year if center_avg_year else 0,
        'total_service_cost': center_total_service_cost,
        'total_requisition_cost': center_total_requisition_cost,
        'total_insurance_recovery': center_total_insurance_recovery,
        'total_net_maintenance_cost': center_total_net_maintenance_cost,
        'service_value_ratio': center_total_net_maintenance_cost / center_total_value * 100 if center_total_value else 0,
        'total_fuel_quantity': center_total_fuel_quantity,
        'total_fuel_cost': center_total_fuel_cost,
        'red_zone_count': len(center_red_zone_vehicles),
    }

    fuel_data = FuelConsumption.objects.annotate(
        vehicle_center_code=Subquery(latest_center_code)
    ).filter(
        vehicle_center_code=center_code
    ).annotate(
        year=TruncYear('date'),
        month=TruncMonth('date')
    ).values('year', 'month').annotate(
        total_fuel_quantity=Sum('amount'),
        total_fuel_cost=Sum('cost_bruto')
    ).order_by('year', 'month')

    service_data = ServiceTransaction.objects.annotate(
        vehicle_center_code=Subquery(latest_center_code)
    ).filter(
        vehicle_center_code=center_code
    ).annotate(
        year=TruncYear('datum'),
        month=TruncMonth('datum')
    ).values('year', 'month').annotate(
        total_cost_gume=Sum('potrazuje', filter=Q(popravka_kategorija__name__icontains='gume')),
        total_cost_redovan_servis=Sum('potrazuje', filter=Q(popravka_kategorija__name__icontains='redovan servis')),
        total_cost_tehnicki_pregled=Sum('potrazuje', filter=Q(popravka_kategorija__name__icontains='tehnicki pregled')),
        total_cost_registracija=Sum('potrazuje', filter=Q(popravka_kategorija__name__icontains='registracija'))
    ).order_by('year', 'month')

    insurance_data = Policy.objects.annotate(
        vehicle_center_code=Subquery(latest_center_code)
    ).filter(
        vehicle_center_code=center_code
    ).annotate(
        year=TruncYear('issue_date'),
        month=TruncMonth('issue_date')
    ).values('year', 'month').annotate(
        total_registration_cost=Sum('premium_amount')
    ).order_by('year', 'month')

    consolidated_data = {}

    for fuel in fuel_data:
        year = fuel['year'].year
        month = fuel['month'].month
        consolidated_data[(year, month)] = {
            'total_fuel_quantity': fuel['total_fuel_quantity'],
            'total_fuel_cost': fuel['total_fuel_cost'],
            'total_cost_gume': 0,
            'total_cost_redovan_servis': 0,
            'total_cost_tehnicki_pregled': 0,
            'total_cost_registracija': 0,
            'total_registration_cost': 0
        }

    for service in service_data:
        year = service['year'].year
        month = service['month'].month
        if (year, month) not in consolidated_data:
            consolidated_data[(year, month)] = {
                'total_fuel_quantity': 0,
                'total_fuel_cost': 0,
                'total_cost_gume': service['total_cost_gume'],
                'total_cost_redovan_servis': service['total_cost_redovan_servis'],
                'total_cost_tehnicki_pregled': service['total_cost_tehnicki_pregled'],
                'total_cost_registracija': service['total_cost_registracija'],
                'total_registration_cost': 0
            }
        else:
            consolidated_data[(year, month)].update({
                'total_cost_gume': service['total_cost_gume'],
                'total_cost_redovan_servis': service['total_cost_redovan_servis'],
                'total_cost_tehnicki_pregled': service['total_cost_tehnicki_pregled'],
                'total_cost_registracija': service['total_cost_registracija']
            })

    for insurance in insurance_data:
        year = insurance['year'].year
        month = insurance['month'].month
        if (year, month) not in consolidated_data:
            consolidated_data[(year, month)] = {
                'total_fuel_quantity': 0,
                'total_fuel_cost': 0,
                'total_cost_gume': 0,
                'total_cost_redovan_servis': 0,
                'total_cost_tehnicki_pregled': 0,
                'total_cost_registracija': 0,
                'total_registration_cost': insurance['total_registration_cost']
            }
        else:
            consolidated_data[(year, month)].update({
                'total_registration_cost': insurance['total_registration_cost']
            })

    numeric_fields = [
        'total_fuel_quantity',
        'total_fuel_cost',
        'total_cost_gume',
        'total_cost_redovan_servis',
        'total_cost_registracija',
        'total_registration_cost',
    ]
    center_totals = {
        field: sum((row.get(field) or 0) for row in consolidated_data.values())
        for field in numeric_fields
    }
    month_count = len(consolidated_data)
    center_averages = {
        field: (center_totals[field] / month_count if month_count else 0)
        for field in numeric_fields
    }

    context = {
        'consolidated_data': consolidated_data,
        'center_code': center_code,
        'center_totals': center_totals,
        'center_averages': center_averages,
        'center_analysis': center_analysis,
        'center_red_zone_vehicles': center_red_zone_vehicles,
    }

    return render(request, 'fleet/dashboard_center.html', context)
