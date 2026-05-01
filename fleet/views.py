from collections import defaultdict
import csv
import datetime
from datetime import date, timedelta
import logging
import os
import tempfile
import textwrap

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.management import call_command
from django.core.exceptions import PermissionDenied
from django.db import connections
from django.db.models import Avg, Count, Exists, F, Max, Min, OuterRef, Q, Subquery, Sum, IntegerField, ExpressionWrapper, Value
from django.db.models.functions import Cast, StrIndex, Substr, TruncMonth, TruncYear
from django.http import FileResponse, HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_filters.views import FilterView

from core.exporting import csv_attachment_response, dataframe_xlsx_response, rows_to_xlsx_response

from .analytics_helpers import (
    cost_per_km_status,
    cost_per_km_thresholds,
    is_red_zone,
    net_maintenance_cost,
)
from .filters import (
    FuelFilterForm,
    FuelTransactionFilterForm,
    PoliciesMonthlyCostsFilter,
    ServiceFixingFilter,
    ServiceMonthlyCostsFilter,
    TrafficCardFilterForm,
    VehicleFilter,
    PutniNalogFilter,
)
from .forms import (
    DraftRequisitionForm,
    DraftServiceTransactionForm,
    EmployeeForm,
    FuelConsumptionForm,
    IncidentForm,
    JobCodeForm,
    LeaseForm,
    OMVPutnickaFilterForm,
    OrganizationalUnitForm,
    PolicyForm,
    PutniNalogForm,
    PutnickaFilterForm,
    RequisitionForm,
    ServiceForm,
    ServiceTransactionForm,
    ServiceTypeForm,
    TrafficCardForm,
    VehicleTenderDocumentForm,
    VehicleForm,
)
from .models import (
    CustomUser,
    DraftPolicy,
    DraftRequisition,
    DraftServiceTransaction,
    Employee,
    FuelConsumption,
    Incident,
    Insurance,
    JobCode,
    KontaVozila,
    Lease,
    LeaseInterest,
    OrganizationalUnit,
    Policy,
    PutniNalog,
    Requisition,
    Service,
    ServiceTransaction,
    ServiceType,
    TrafficCard,
    VehicleTenderDocument,
    VehicleTravelOrder,
    Vehicle,
)
from .mixins import CenterMixin, RolePermissionRequiredMixin, role_permission_required
from .queries import (
    _filtered_qs,
    date_period_filtered_query,
    get_data_from_secondary_db,
    lease_monthly_costs_rows,
    policies_monthly_costs_qs,
    report_period_filtered_query,
    service_monthly_costs_rows,
)
from .report_exports import (
    NIS_PUTNICKA_EXPORT,
    NIS_TERETNA_EXPORT,
    OMV_PUTNICKA_EXPORT,
    OMV_TERETNA_EXPORT,
    report_xlsx_response,
)
from .report_queries import (
    NIS_PUTNICKA_SQL,
    NIS_TERETNA_SQL,
    OMV_PUTNICKA_SQL,
    OMV_TERETNA_SQL,
)
from .utils import (
    calculate_average_fuel_consumption,
    calculate_average_fuel_consumption_ever,
    delete_complete_drafts,
    date_range_for_datetime_field,
    fetch_policy_data,
    fetch_requisition_data,
    fetch_service_data,
    get_fuel_consumption_queryset,
    migrate_draft_to_service_transaction,
    populate_putni_nalog_template,
    sanitize_filename,
)

logger = logging.getLogger(__name__)
LONG_TERM_LEASE_TYPES = set(Lease.LONG_TERM_LEASE_TYPE_VALUES)

# <!-- ======================================================================= -->
#                           <!-- DASHBOARD I ANALITIKA -->
# <!-- ======================================================================= -->
def vehicle_cost_per_km_rows(period_start_date, period_end_date=None, limit=None):
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
    ).annotate(
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


def dashboard(request):    
    # Count the number of objects where vehicle is None
    services_without_vehicle = DraftServiceTransaction.objects.count()
    policies_without_vehicle = DraftPolicy.objects.count()
    requisitions_without_vehicle = DraftRequisition.objects.count()
    draft_insurance_count = DraftInsurance.objects.count()
    
    today = date.today()
    thirty_days_from_now = today + timedelta(days=30)

    # Subquery za pronalaženje najnovijeg datuma završetka za isti automobil i tip osiguranja
    newest_policy = Policy.objects.filter(
        vehicle=OuterRef('vehicle'),
        insurance_type=OuterRef('insurance_type'),
        is_renewable=True  # Dodato da se uzimaju u obzir samo polise koje se obnavljaju
    ).order_by('-end_date').values('end_date')[:1]

    # Filtriranje polisa koje uskoro ističu i koje se obnavljaju
    expiring_policies = Policy.objects.annotate(
        latest_end_date=Subquery(newest_policy)
    ).filter(
        end_date__gte=today,
        end_date__lte=thirty_days_from_now,
        end_date=F('latest_end_date'),
        is_renewable=True  # Dodato da filtrira samo polise koje se obnavljaju
    )

    expiring_policies_count = expiring_policies.count()

    # Subquery da proveri da li postoji nova polisa za isto vozilo i tip osiguranja
    newer_policy_exists = Policy.objects.filter(
        vehicle=OuterRef('vehicle'),
        insurance_type=OuterRef('insurance_type'),
        start_date__gt=OuterRef('start_date'),
        is_renewable=True  # Dodato da proveri samo polise koje se obnavljaju
    )

    # Filtriranje polisa koje su istekle i nisu obnovljene
    expired_unrenewed_policies = Policy.objects.annotate(
        has_newer_policy=Exists(newer_policy_exists)
    ).filter(
        end_date__lt=today,           # Polise koje su već istekle
        has_newer_policy=False,       # Proveri da li nema novije polise
        is_renewable=True             # Dodato da proveri samo polise koje se obnavljaju
    )

    expired_unrenewed_policies_count = expired_unrenewed_policies.count()

    # Current year and last day of the previous month
    current_year = datetime.datetime.now().year
    first_day_of_current_month = date.today().replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    start_of_year = date.today().replace(month=1, day=1)
    start_of_last_12_months = date.today() - timedelta(days=365)
    start_of_last_12_months_dt, _ = date_range_for_datetime_field(start_of_last_12_months)

    # Number of vehicles
    total_vehicles = Vehicle.objects.filter(otpis=False).count()
    passenger_vehicles = Vehicle.objects.filter(category='PUTNICKO VOZILO').filter(otpis=False).count()
    transport_vehicles = Vehicle.objects.filter(category='TERETNO VOZILO').filter(otpis=False).count()



    # Average vehicle age
    average_age = Vehicle.objects.aggregate(avg_age=(current_year - Avg('year_of_manufacture')))

    # Book value as of the last day of the previous month
    book_value = Vehicle.objects.filter(purchase_date__lte=last_day_of_previous_month).aggregate(total_value=Sum('value'))

    # Costs for the last 12 months
    yearly_fuel_costs = FuelConsumption.objects.filter(date__gte=start_of_last_12_months_dt).aggregate(total_fuel_cost=Sum('cost_bruto'))
    yearly_service_costs = ServiceTransaction.objects.filter(datum__gte=start_of_year).aggregate(total_service_cost=Sum('potrazuje'))

    # Podupit za poslednju dodelu jedinice po vozilu
    latest_jobcode = JobCode.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-assigned_date')

    # Dohvati sva vozila sa podacima, bez grupisanja
    vehicles = Vehicle.objects.annotate(
        center_code=Subquery(latest_jobcode.values('organizational_unit__center')[:1]),
        manufacture_year=F('year_of_manufacture'),
        current_value=F('value'),  # promenjeno ime!
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
    # Grupisanje u Pythonu
    grouped = defaultdict(list)

    for v in vehicles:
        grouped[v.center_code].append(v)

    # Napravi center_data ručno
    center_data = []
    for center, vehicle_list in grouped.items():
        count = len(vehicle_list)
        total_value = sum([v.current_value or 0 for v in vehicle_list])
        avg_value = total_value / count if count else 0
        total_fuel_quantity = sum([v.fuel_amount or 0 for v in vehicle_list])
        total_fuel_price = sum([v.fuel_cost or 0 for v in vehicle_list])
        total_service_cost = sum([v.service_cost or 0 for v in vehicle_list])
        total_requisition_cost = sum([v.requisition_cost or 0 for v in vehicle_list])
        total_insurance_recovery = sum([v.insurance_recovery or 0 for v in vehicle_list])
        total_net_maintenance_cost = sum([
            net_maintenance_cost(v.service_cost, v.requisition_cost, v.insurance_recovery)
            for v in vehicle_list
        ])
        red_zone_count = sum(
            1
            for v in vehicle_list
            if is_red_zone(
                v.long_term_rental,
                v.current_value,
                net_maintenance_cost(v.service_cost, v.requisition_cost, v.insurance_recovery),
            )
        )
        avg_year = sum([v.year_of_manufacture or 0 for v in vehicle_list]) / count if count else 0
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
        # 'vehicles_by_center': vehicles_by_center,
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
            'label': 'Poslednjih 12 meseci',
            'start': start_of_last_12_months,
            'end': today,
        },
        {
            'key': '24m',
            'label': 'Poslednja 24 meseca',
            'start': start_of_last_24_months,
            'end': today,
        },
    ]
    period_cost_per_km_rows, cost_per_km_thresholds_by_period, persistent_unprofitable_vehicles = cost_per_km_period_analysis(cost_per_km_periods)
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
        'cost_per_km_thresholds_by_period': cost_per_km_thresholds_by_period,
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

def center_statistics(request, center_code):
    # Check if the user has access to this center
    if not request.user.allowed_centers.filter(center=center_code).exists():
        return HttpResponseForbidden("Nemate pristup ovim podacima.")
    
    # Podupit za poslednju OU (tj. centar) za vozilo
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

    # Filtriranje FuelConsumption po centru
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

    # Service costs statistics (grouped by service type, month, and year, filtered by center)
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

    # Ispravljen upit za registracije
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

    # Combine all data based on year and month
    consolidated_data = {}
    
    # Consolidating fuel data
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

    # Consolidating service data
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

    # Consolidating insurance data
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

# <!-- ======================================================================= -->
#                           <!-- ORGANIZATIONAL UNITS -->
# <!-- ======================================================================= -->

class OrganizationalUnitListView(LoginRequiredMixin, ListView):
    model = OrganizationalUnit
    template_name = 'fleet/organizational_units_list.html'
    context_object_name = 'units'


class OrganizationalUnitCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = OrganizationalUnit
    form_class = OrganizationalUnitForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('organizational_unit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novu organizacionu jedinicu'
        context['submit_button_label'] = 'Sačuvaj'
        return context


class OrganizationalUnitUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = OrganizationalUnit
    form_class = OrganizationalUnitForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('organizational_unit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni organizacionu jedinicu'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context
    
# class OrganizationalUnitDeleteView(DeleteView):
#     model = OrganizationalUnit
#     success_url = reverse_lazy('organizational_unit_list')

# <!-- ======================================================================= -->
#                           <!-- VEHICLE -->
# <!-- ======================================================================= -->
class VehicleListView(LoginRequiredMixin, FilterView):
    model = Vehicle
    template_name = 'fleet/vehicle_list.html'
    context_object_name = 'vehicles'
    filterset_class = VehicleFilter


    def get_queryset(self):
        qs = Vehicle.objects.all()

        # Subqueries / annotate — kao u tvojoj postojećoj logici
        latest_job_code_qs = JobCode.objects.filter(
            vehicle=OuterRef('pk')
        ).order_by('-assigned_date', '-pk')

        latest_job_code_id_subquery = latest_job_code_qs.values('id')[:1]
        latest_org_unit_id_subquery = latest_job_code_qs.values('organizational_unit_id')[:1]
        latest_org_unit_code_subquery = latest_job_code_qs.values('organizational_unit__code')[:1]
        latest_center_subquery = latest_job_code_qs.values('organizational_unit__center')[:1]

        latest_traffic_card_subquery = TrafficCard.objects.filter(
            vehicle=OuterRef('pk')
        ).order_by('-issue_date').values('registration_number')[:1]

        last_mileage_subquery = FuelConsumption.objects.filter(
            vehicle=OuterRef('pk')
        ).order_by('-mileage').values('mileage')[:1]

        qs = Vehicle.objects.annotate(
            current_ou_id=Subquery(latest_org_unit_id_subquery)
        )

        qs = qs.annotate(
            latest_job_code_id=Subquery(latest_job_code_id_subquery),
            latest_org_unit=Subquery(latest_center_subquery),
            latest_org_unit_code=Subquery(latest_org_unit_code_subquery),
            registration_number=Subquery(latest_traffic_card_subquery),
            total_repairs=Sum('service_transactions__potrazuje'),
            mileage=Subquery(last_mileage_subquery),
        )

        # DEFAULT: ako korisnik NIJE eksplicitno izabrao status / show_archived,
        # prikaži samo aktivna (otpis=False)
        get = self.request.GET
        if "status" not in get and "show_archived" not in get:
            qs = qs.filter(otpis=False)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Prosečna potrošnja (isti princip kao kod tebe)
        vehicles = ctx.get('vehicles') or ctx.get('object_list')  # safety
        vehicle_consumption_data = {}
        for v in vehicles:
            vehicle_consumption_data[v.id] = calculate_average_fuel_consumption(v)

        ctx['vehicle_consumption_data'] = vehicle_consumption_data
        ctx['title'] = 'Lista vozila'
        # Ako želiš globalni indikator aktivne aplikacije:
        ctx.setdefault('current_app', 'fleet')
        return ctx


def _vehicle_list_base_queryset(request):
    qs = Vehicle.objects.all()

    latest_job_code_qs = JobCode.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-assigned_date', '-pk')

    latest_job_code_id_subquery = latest_job_code_qs.values('id')[:1]
    latest_org_unit_id_subquery = latest_job_code_qs.values('organizational_unit_id')[:1]
    latest_org_unit_code_subquery = latest_job_code_qs.values('organizational_unit__code')[:1]
    latest_center_subquery = latest_job_code_qs.values('organizational_unit__center')[:1]

    latest_traffic_card_subquery = TrafficCard.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-issue_date').values('registration_number')[:1]

    last_mileage_subquery = FuelConsumption.objects.filter(
        vehicle=OuterRef('pk')
    ).order_by('-mileage').values('mileage')[:1]

    qs = Vehicle.objects.annotate(
        current_ou_id=Subquery(latest_org_unit_id_subquery)
    )

    qs = qs.annotate(
        latest_job_code_id=Subquery(latest_job_code_id_subquery),
        latest_org_unit=Subquery(latest_center_subquery),
        latest_org_unit_code=Subquery(latest_org_unit_code_subquery),
        registration_number=Subquery(latest_traffic_card_subquery),
        total_repairs=Sum('service_transactions__potrazuje'),
        mileage=Subquery(last_mileage_subquery),
    )

    get = request.GET
    if "status" not in get and "show_archived" not in get:
        qs = qs.filter(otpis=False)
    return qs


@role_permission_required()
def vehicle_export_csv(request):
    base_qs = _vehicle_list_base_queryset(request)
    vehicle_filter = VehicleFilter(request.GET, queryset=base_qs)
    qs = vehicle_filter.qs

    response = csv_attachment_response("vozila.csv", quoted=True)
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Registracija',
        'Marka',
        'Tip',
        'Godište',
        'Kilometraža',
        'Potrošnja',
        'Kategorija',
        'Centar',
        'Kubikaža',
    ])

    for vehicle in qs:
        avg_consumption = calculate_average_fuel_consumption(vehicle)
        writer.writerow([
            vehicle.registration_number or '',
            vehicle.brand or '',
            vehicle.model or '',
            vehicle.year_of_manufacture or '',
            vehicle.mileage or '',
            f"{avg_consumption:.2f}" if avg_consumption is not None else '0',
            vehicle.category or '',
            vehicle.latest_org_unit_code or '',
            f"{vehicle.engine_volume:.0f}" if vehicle.engine_volume is not None else '',
        ])

    return response
    
# DETALJI VOZILA
class VehicleDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'fleet/vehicle_detail.html'
    context_object_name = 'vehicle'

    def get(self, request, *args, **kwargs):
        logger.info("VehicleDetailView get() method called")
        vehicle = self.get_object()
        logger.info(vehicle)

        # Subquery to get the latest org_unit for each Vehicle
        # Ovo vam vraća kod centra iz JobCode-a, bazirano na 'organizational_unit__center'
        latest_org_unit_subquery = JobCode.objects.filter(
            vehicle_id=OuterRef('pk')
        ).order_by('-assigned_date').values('organizational_unit__center')[:1]

        # Annotate the vehicle queryset with the latest org_unit code
        vehicle_with_latest_org_unit = Vehicle.objects.annotate(
            latest_org_unit=Subquery(latest_org_unit_subquery)
        ).get(pk=vehicle.pk)

        # --- Modifikovana logika za proveru dozvola ---
        user_allowed_centers_manager = request.user.allowed_centers # Dobijamo ManyRelatedManager

        # Proveravamo da li korisnik uopšte ima definisane dozvoljene centre
        # Prazan manager (kada korisnik nema dodeljene centre) se u if uslovu ponaša kao False
        if user_allowed_centers_manager.exists(): # Proverava da li manager sadrži ijedan srodni objekat
             # Iz managers dobijamo listu kodova dozvoljenih centara.
             # *** VAŽNO: Zamenite 'center' u values_list('center', flat=True)
             # *** sa STVARNIM IMENOM POLJA na modelu na koji ukazuje
             # *** request.user.allowed_centers, a koje sadrži kod centra.
             # *** Na osnovu vašeg subquery-a 'organizational_unit__center',
             # *** verovatno se to polje zove 'center' ili 'code'.
             allowed_centers_codes = user_allowed_centers_manager.values_list('center', flat=True) # Vraća QuerySet sa listom vrednosti, flat=True daje Python listu


             # Sada proveravamo da li kod poslednjeg organizacione jedinice vozila
             # NIJE u listi dozvoljenih kodova za korisnika.
             # Dodata provera da li latest_org_unit nije None (ako vozilo nema JobCode)
             if vehicle_with_latest_org_unit.latest_org_unit is not None and \
                vehicle_with_latest_org_unit.latest_org_unit not in allowed_centers_codes:
                 return HttpResponseForbidden("Nemate dozvolu za pristup ovom vozilu.")
        # else: Ako user_allowed_centers_manager.exists() vrati False, to znači da korisnik
        # nema eksplicitno definisane centre kojima može da pristupi. Ako je željeno ponašanje
        # da takav korisnik ima pristup svim vozilima, onda ova if struktura to omogućava
        # jer se provera dozvole preskače.
        # --- Kraj modifikovane logike ---


        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vehicle = self.get_object()

        # 1. Aktivne polise osiguranja
        active_policies = Policy.objects.filter(vehicle=vehicle, end_date__gte=datetime.date.today())

        # 2. Job Code
        current_job_code = JobCode.objects.filter(vehicle=vehicle).order_by('-assigned_date').first()
        job_codes = JobCode.objects.filter(vehicle=vehicle).order_by('-assigned_date')

        
        # 3. Gorivo, kilometraza i kartice
        nis_card = vehicle.nis_transactions.filter().first()
        omv_card = vehicle.omv_transactions.filter().first()

        mileage = vehicle.fuel_consumptions.order_by('-mileage').values_list('mileage', flat=True).first()

        consumptions = vehicle.fuel_consumptions.all() # Za tabelu potrosnje
        average_consumption = calculate_average_fuel_consumption(vehicle) # poslednjih 10
        average_consumption_ever = calculate_average_fuel_consumption_ever(vehicle) # Sva tocenja
        
        # Grupisanje po mesecima i godinama uz dobavljača, agregiranje količine i bruto cene
        fuel_data = FuelConsumption.objects.filter(vehicle=vehicle).annotate(
            month=TruncMonth('date'),
            year=TruncYear('date')
        ).values('month', 'year', 'supplier').annotate(
            total_liters=Sum('amount'),
            total_cost_bruto=Sum('cost_bruto')
        ).order_by('year', 'month', 'supplier')

        # Razdvajanje podataka za OMV i NIS
        omv_data = fuel_data.filter(supplier='OMV')
        nis_data = fuel_data.filter(supplier='NIS')

        # 4. Leasing data
        lease_info = Lease.objects.filter(vehicle=vehicle).order_by('-start_date').first()
        long_term_rental = Lease.objects.filter(vehicle=vehicle, lease_type__in=LONG_TERM_LEASE_TYPES).exists()
        lease_intrests = LeaseInterest.objects.filter(lease=lease_info).order_by('-year')

        # 5. General status (red/green light based on repair costs)
        repair_costs = vehicle.service_transactions.aggregate(total_repairs=Sum('potrazuje'))['total_repairs'] or 0
        requisition_costs = vehicle.requisitions.aggregate(total_requisitions=Sum('vrednost_nab'))['total_requisitions'] or 0
        insurance_recovery = vehicle.insurances.filter(kola=True).aggregate(total=Sum('potrazuje'))['total'] or 0

        service_list = vehicle.service_transactions.order_by('-datum')
        requisition_list = vehicle.requisitions.order_by('-datum_trebovanja')
        putni_nalozi = PutniNalog.objects.filter(vehicle=vehicle).select_related('employee', 'job_code').order_by('-travel_date', '-id')
        vehicle_travel_orders = VehicleTravelOrder.objects.filter(vehicle=vehicle).select_related('employee').order_by('-created_at', '-id')
        
        # 6. Saobracajna dozvol i istorija
        trafic_cards = TrafficCard.objects.filter(vehicle=vehicle).order_by('-issue_date')
        trafic_card = trafic_cards.first()
        status_light = 'green' if repair_costs < vehicle.purchase_value else 'red'

        vehicle_value = vehicle.value or vehicle.purchase_value or 0
        total_fuel_cost = vehicle.fuel_consumptions.aggregate(total=Sum('cost_bruto'))['total'] or 0
        total_fuel_liters = vehicle.fuel_consumptions.aggregate(total=Sum('amount'))['total'] or 0
        gross_maintenance_cost = repair_costs + requisition_costs
        total_maintenance_cost = net_maintenance_cost(repair_costs, requisition_costs, insurance_recovery)
        maintenance_value_ratio = (total_maintenance_cost / vehicle_value * 100) if vehicle_value else 0
        remaining_value_after_maintenance = vehicle_value - total_maintenance_cost
        red_zone = is_red_zone(long_term_rental, vehicle_value, total_maintenance_cost)

        def month_date(value):
            return value.date() if hasattr(value, 'date') else value

        monthly_costs = defaultdict(lambda: {'fuel': 0, 'service': 0})
        for row in vehicle.fuel_consumptions.annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('cost_bruto')).order_by('month'):
            if row['month']:
                monthly_costs[month_date(row['month'])]['fuel'] = float(row['total'] or 0)
        for row in vehicle.service_transactions.annotate(month=TruncMonth('datum')).values('month').annotate(total=Sum('potrazuje')).order_by('month'):
            if row['month']:
                monthly_costs[month_date(row['month'])]['service'] = float(row['total'] or 0)
        monthly_vehicle_costs = [
            {'label': month.strftime('%m.%Y'), 'fuel': values['fuel'], 'service': values['service']}
            for month, values in sorted(monthly_costs.items())
        ][-12:]

        service_category_rows = [
            {
                'label': row['popravka_kategorija__name'] or 'Nerazvrstano',
                'value': float(row['total'] or 0),
            }
            for row in vehicle.service_transactions.values('popravka_kategorija__name')
            .annotate(total=Sum('potrazuje'))
            .order_by('-total')[:8]
        ]

        vehicle_analysis = {
            'total_fuel_cost': total_fuel_cost,
            'total_fuel_liters': total_fuel_liters,
            'gross_maintenance_cost': gross_maintenance_cost,
            'insurance_recovery': insurance_recovery,
            'total_maintenance_cost': total_maintenance_cost,
            'maintenance_value_ratio': maintenance_value_ratio,
            'remaining_value_after_maintenance': remaining_value_after_maintenance,
            'red_zone': red_zone,
            'vehicle_value': vehicle_value,
            'fuel_cost_per_liter': total_fuel_cost / total_fuel_liters if total_fuel_liters else 0,
            'long_term_rental': long_term_rental,
        }

        
        context.update({
            'lease_info': lease_info,
            'lease_intrests':lease_intrests,
            'nis_card': nis_card,
            'omv_card': omv_card,
            'mileage': mileage,
            'active_policies': active_policies,
            'average_consumption': average_consumption,
            'average_consumption_ever': average_consumption_ever,
            'omv_data':omv_data,
            'nis_data':nis_data,
            'current_job_code': current_job_code,
            'job_codes': job_codes,
            'status_light': status_light,
            'repair_costs': repair_costs,
            'requisition_costs':requisition_costs,
            'insurance_recovery': insurance_recovery,
            'service_list':service_list,
            'requisition_list':requisition_list,
            'putni_nalozi': putni_nalozi,
            'vehicle_travel_orders': vehicle_travel_orders,
            'consumptions': consumptions,
            'trafic_cards':trafic_cards,
            'trafic_card':trafic_card,
            'vehicle_analysis': vehicle_analysis,
            'monthly_vehicle_costs': monthly_vehicle_costs,
            'service_category_rows': service_category_rows,
            'tender_documents': vehicle.tender_documents.order_by('-created_at'),
            'tender_document_create_url': reverse('vehicle_tender_document_create_for_vehicle', kwargs={'vehicle_id': vehicle.pk}),
            'title':f"Detalji vozila {self.object.brand} {self.object.model}"
        })
        return context



class VehicleCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('vehicle_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect('trafficcard_create', vehicle_id=self.object.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novo vozilo'
        context['submit_button_label'] = 'Dodaj vozilo'
        return context

class VehicleUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('vehicle_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni podatke vozila'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class VehicleTogleStatusView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.otpis = not vehicle.otpis
        vehicle.save()
        status = "aktivano" if vehicle.otpis else "otpisano"
        messages.success(request, f"Vozilo je uspešno {status}.")
        return redirect('vehicle_detail', pk=pk)


class VehicleDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Vehicle
    success_url = reverse_lazy('vehicle_list')
    template_name = 'fleet/vehicle_confirm_delete.html'
    context_object_name = 'vehicle'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši vozilo'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)


# <!-- ======================================================================= -->
#                   <!-- VEHICLE TENDER DOCUMENTS -->
# <!-- ======================================================================= -->
class VehicleTenderDocumentListView(LoginRequiredMixin, ListView):
    model = VehicleTenderDocument
    template_name = 'fleet/vehicle_tender_document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('vehicle')
        vehicle_id = self.request.GET.get('vehicle')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        only_active = self.request.GET.get('only_active')
        if only_active == '1':
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Tender dokumenti vozila'
        context['vehicles'] = Vehicle.objects.all().order_by('brand', 'model')
        context['selected_vehicle_id'] = self.request.GET.get('vehicle')
        context['only_active'] = self.request.GET.get('only_active') == '1'
        context['document_type_choices'] = VehicleTenderDocument.DocumentType.choices
        return context


class VehicleTenderDocumentCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = VehicleTenderDocument
    form_class = VehicleTenderDocumentForm
    template_name = 'fleet/generic_form.html'

    def get_initial(self):
        initial = super().get_initial()
        vehicle_id = self.kwargs.get('vehicle_id') or self.request.GET.get('vehicle')
        if vehicle_id:
            initial['vehicle'] = Vehicle.objects.filter(pk=vehicle_id).first()
        return initial

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Dokument je uspešno dodat.')
        return redirect('vehicle_detail', pk=self.object.vehicle_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj tender dokument'
        context['submit_button_label'] = 'Sačuvaj dokument'
        return context


class VehicleTenderDocumentUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = VehicleTenderDocument
    form_class = VehicleTenderDocumentForm
    template_name = 'fleet/generic_form.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Dokument je uspešno izmenjen.')
        return redirect('vehicle_detail', pk=self.object.vehicle_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Izmeni tender dokument {self.object.title}'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context


class VehicleTenderDocumentDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = VehicleTenderDocument
    template_name = 'fleet/vehicle_tender_document_detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Tender dokument {self.object.title}'
        return context


class VehicleTenderDocumentDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = VehicleTenderDocument
    template_name = 'fleet/vehicle_tender_document_confirm_delete.html'
    context_object_name = 'document'
    success_url = reverse_lazy('vehicle_tender_document_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        vehicle_id = self.object.vehicle_id
        messages.success(request, 'Dokument je uspešno obrisan.')
        self.success_url = reverse('vehicle_detail', kwargs={'pk': vehicle_id})
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Obriši tender dokument {self.object.title}'
        return context


# <!-- ======================================================================= -->
#                           <!-- TRAFIC CARD -->
# <!-- ======================================================================= -->
# <!-- ======================================================================= -->
#                           <!-- TRAFIC CARD -->
# <!-- ======================================================================= -->
class TrafficCardListView(LoginRequiredMixin, ListView):
    model = TrafficCard
    template_name = 'fleet/trafficcard_list.html'
    context_object_name = 'traffic_cards'
    form_class = TrafficCardFilterForm

    def get_queryset(self):
        queryset = super().get_queryset().select_related('vehicle')
        self.filter_form = self.form_class(self.request.GET or None)

        # Subquery: poslednji JobCode po datumu
        latest_org_unit_subquery = JobCode.objects.filter(
            vehicle_id=OuterRef('vehicle_id')
        ).order_by('-assigned_date').values('organizational_unit__code')[:1]

        latest_center_subquery = JobCode.objects.filter(
            vehicle_id=OuterRef('vehicle_id')
        ).order_by('-assigned_date').values('organizational_unit__center')[:1]

        queryset = queryset.annotate(
            latest_org_unit=Subquery(latest_org_unit_subquery),
            latest_center=Subquery(latest_center_subquery),
        )

        if self.filter_form.is_valid():
            org_unit = self.filter_form.cleaned_data.get('organizational_unit')
            center = self.filter_form.cleaned_data.get('center')

            if org_unit:
                queryset = queryset.filter(latest_org_unit=org_unit.code)

            if center:
                queryset = queryset.filter(latest_center=center)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['title'] = 'Lista saobraćajnih dozvola'
        return context
class TrafficCardCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = TrafficCard
    form_class = TrafficCardForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('trafficcard_list')
   
    def get_initial(self):
        vehicle_id = self.kwargs.get('vehicle_id')
        return {'vehicle': vehicle_id}

    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect('jobcode_create', vehicle_id = self.object.vehicle.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novu saobraćajnu dozvolu'
        context['submit_button_label'] = 'Dodaj saobraćajnu dozvolu'
        return context

class TrafficCardUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = TrafficCard
    form_class = TrafficCardForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('trafficcard_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni podatke saobraćajne dozvole'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class TrafficCardDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = TrafficCard
    template_name = 'fleet/trafficcard_detail.html'
    context_object_name = 'traffic_card'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji saobraćajne dozvole {self.object.registration_number}"
        return context

class TrafficCardDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = TrafficCard
    success_url = reverse_lazy('trafficcard_list')
    template_name = 'fleet/trafficcard_confirm_delete.html'
    context_object_name = 'traffic_card'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši saobraćajnu dozvolu'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)



# <!-- ======================================================================= -->
#                           <!-- JOB CODE -->
# <!-- ======================================================================= -->
class JobCodeListView(LoginRequiredMixin, ListView):
    model = JobCode
    template_name = 'fleet/jobcode_list.html'
    context_object_name = 'job_codes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista šifara poslova'
        return context

class JobCodeCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = JobCode
    form_class = JobCodeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('jobcode_list')

    def get_initial(self):
        return {
            'vehicle': self.kwargs.get('vehicle_id')
        }
    
    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect('vehicle_detail', pk = self.object.vehicle.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novu šifru posla'
        context['submit_button_label'] = 'Dodaj šifru posla'
        return context
    
class JobCodeUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = JobCode
    form_class = JobCodeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('jobcode_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni šifru posla'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class JobCodeDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = JobCode
    template_name = 'fleet/jobcode_detail.html'
    context_object_name = 'job_code'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji šifre posla {self.object.job_code}"
        return context

class JobCodeDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = JobCode
    success_url = reverse_lazy('jobcode_list')
    template_name = 'fleet/jobcode_confirm_delete.html'
    context_object_name = 'job_code'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši šifru posla'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)



# <!-- ======================================================================= -->
#                           <!-- LEASE -->
# <!-- ======================================================================= -->
class LeaseListView(LoginRequiredMixin, ListView):
    model = Lease
    template_name = 'fleet/lease_list.html'
    context_object_name = 'leases'

    def get_queryset(self):
        qs = super().get_queryset().select_related('vehicle')
        tip = self.request.GET.get('tip')
        if tip == 'dugorocni':
            qs = qs.filter(lease_type__in=LONG_TERM_LEASE_TYPES)
        elif tip in {'finansijski', 'operativni'}:
            qs = qs.filter(lease_type=tip)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Lizing i najam ugovori'
        return ctx


class LeaseCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Lease
    form_class = LeaseForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('lease_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novi zakup'
        context['submit_button_label'] = 'Dodaj zakup'
        return context

def export_leases_to_excel(request):
    # Filter po tipu lizinga (opciono)
    tip = request.GET.get("tip")
    leases = Lease.objects.select_related("vehicle").all()
    if tip == "dugorocni":
        leases = leases.filter(lease_type__in=LONG_TERM_LEASE_TYPES)
    elif tip in {"finansijski", "operativni"}:
        leases = leases.filter(lease_type=tip)

    # Naslovi kolona
    headers = [
        "Vozilo (šasija)",
        "Šifra partnera",
        "Naziv partnera",
        "Šifra posla",
        "Broj ugovora",
        "Trenutna vrednost otplate",
        "Vrsta lizinga",
        "Datum početka",
        "Datum završetka",
        "Napomena",
    ]

    # Podaci iz baze
    rows = (
        [
            lease.vehicle.chassis_number if lease.vehicle else "",
            lease.partner_code,
            lease.partner_name,
            lease.job_code,
            lease.contract_number,
            float(lease.current_payment_amount or 0),
            lease.lease_type_label,
            lease.start_date.strftime("%d.%m.%Y") if lease.start_date else "",
            lease.end_date.strftime("%d.%m.%Y") if lease.end_date else "",
            lease.note or "",
        ]
        for lease in leases
    )

    fname = f"lizing_ugovori_{tip or 'svi'}.xlsx"
    return rows_to_xlsx_response(fname, "Lizing ugovori", headers, rows, quoted=True)

class LeaseUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Lease
    form_class = LeaseForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('lease_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni zakup'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class LeaseDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Lease
    template_name = 'fleet/lease_detail.html'
    context_object_name = 'lease'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji zakupa {self.object.partner_name}"
        return context

class LeaseDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Lease
    success_url = reverse_lazy('lease_list')
    template_name = 'fleet/lease_confirm_delete.html'
    context_object_name = 'lease'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši zakup'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)
    


# <!-- ======================================================================= -->
#                           <!-- POLICY -->
# <!-- ======================================================================= -->
class PolicyListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = 'fleet/policy_list.html'
    context_object_name = 'policies'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista polisa osiguranja'
        return context

class PolicyFixingListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = 'fleet/draft_policy_list.html'
    context_object_name = 'policies'

    def get_queryset(self):
        # Filter policies where the vehicle is None
        return DraftPolicy.objects.all

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista polisa osiguranja koje morate dopuniti'
        return context

class ExpiringAndNotRenewedPolicyView(LoginRequiredMixin, ListView):
    template_name = 'fleet/policy_expiring.html'
    model = Policy

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        thirty_days_from_now = today + timedelta(days=30)
        
        # Pronađi najnoviju polisu po vozilu i tipu osiguranja
        newest_policy = Policy.objects.filter(
            vehicle=OuterRef('vehicle'),
            insurance_type=OuterRef('insurance_type')
        ).order_by('-end_date').values('end_date', 'is_renewable')[:1]

        # Dodaj anotaciju sa datumom i informacijom da li je polisa obnovljiva
        expiring_policies = Policy.objects.annotate(
            latest_end_date=Subquery(newest_policy.values('end_date')[:1]),
            latest_is_renewable=Subquery(newest_policy.values('is_renewable')[:1])
        ).filter(
            end_date__gte=today,
            end_date__lte=thirty_days_from_now,
            end_date=F('latest_end_date'),
            latest_is_renewable=True  # Prikazuj samo ako je obnovljiva
        )

        # Proveri da li postoji novija polisa
        newer_policy_exists = Policy.objects.filter(
            vehicle=OuterRef('vehicle'),
            insurance_type=OuterRef('insurance_type'),
            start_date__gt=OuterRef('start_date')
        )

        # Pronađi istekle polise koje nisu obnovljene
        expired_unrenewed_policies = Policy.objects.annotate(
            has_newer_policy=Subquery(newer_policy_exists.values('id')[:1]),
            latest_is_renewable=Subquery(newest_policy.values('is_renewable')[:1])
        ).filter(
            end_date__lt=today,
            has_newer_policy__isnull=True,   # Nema novije polise
            latest_is_renewable=True         # Prikazuj samo ako je obnovljiva
        )


        context['expiring_policies'] = expiring_policies
        context['expired_unrenewed_policies'] = expired_unrenewed_policies
        context['title'] = 'Liste polisa koje ističu i koje su istekle i nisu obnovljene'
        return context

class PolicyCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('policy_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novu polisu osiguranja'
        context['submit_button_label'] = 'Dodaj polisu'
        return context

class PolicyUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('policy_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni polisu osiguranja'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context
    
    def form_valid(self, form):
        # Prvo sačuvaj izmene
        response = super().form_valid(form)
        next_url = self.request.GET.get('next')

        # Zatim preusmeri korisnika nazad ako postoji 'next' parametar
        next_url = self.request.GET.get('next')
        if next_url:
            return HttpResponseRedirect(next_url)
        
        return response


class PolicyDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Policy
    template_name = 'fleet/policy_detail.html'
    context_object_name = 'policy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji polise {self.object.policy_number}"
        return context

class PolicyDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Policy
    success_url = reverse_lazy('policy_list')
    template_name = 'fleet/policy_confirm_delete.html'
    context_object_name = 'policy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši polisu osiguranja'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)

class DraftPolicyUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = DraftPolicy
    form_class = PolicyForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('policy_fixing_list')

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return str(self.success_url)

    def form_valid(self, form):
        # Sačuvaj izmene u draft tabeli
        draft = form.save(commit=False)
        logger.info("Izmene sačuvane u draft tabeli.")

        # Provera da li su svi potrebni podaci sada prisutni osim opcionalnih polja
        required_fields = [
            'partner_pib',
            'partner_name',
            'invoice_id',
            'invoice_number',
            'issue_date',
            'insurance_type',
            'policy_number',
            'premium_amount',
            'start_date',
            'end_date',
            'first_installment_amount',
            'other_installments_amount',
            'number_of_installments'
        ]
        is_complete = all(
            getattr(draft, field) is not None and getattr(draft, field) != ''
            for field in required_fields
        )

        if is_complete:
            # Ako su podaci kompletni, prebacujemo ih u glavni model
            policy = Policy(
                vehicle=draft.vehicle,
                partner_pib=draft.partner_pib,
                partner_name=draft.partner_name,
                invoice_id=draft.invoice_id,
                invoice_number=draft.invoice_number,
                issue_date=draft.issue_date,
                insurance_type=draft.insurance_type,
                policy_number=draft.policy_number,
                premium_amount=draft.premium_amount,
                start_date=draft.start_date,
                end_date=draft.end_date,
                first_installment_amount=draft.first_installment_amount,
                other_installments_amount=draft.other_installments_amount,
                number_of_installments=draft.number_of_installments
            )
            policy.save()
            logger.info("Podaci migrirani u glavnu tabelu Policy.")
            draft.delete()  # Obrisan unos iz draft tabele
            return redirect(self.get_success_url())

        # Ako podaci nisu kompletni, sačuvaj ih samo u draft tabeli
        else:
            draft.save()  # Sačuvaj izmene u draft tabeli
            logger.info("Podaci nisu kompletni, ostaju u draft tabeli.")
            return redirect(self.get_success_url())


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dopuni polisu'
        context['submit_button_label'] = 'Sačuvaj'
        return context

# <!-- ======================================================================================== -->
#                           <!-- FUEL CONSUMPTION -->
# <!-- ======================================================================================== -->

class FuelConsumptionListView(LoginRequiredMixin, FilterView):
    model = FuelConsumption
    filterset_class = FuelFilterForm
    template_name = 'fleet/fuelconsumption_list.html'
    context_object_name = 'fuel_consumptions'

    def get_queryset(self):
        # Subquery to get the latest TrafficCard for each Vehicle
        latest_traffic_card_subquery = TrafficCard.objects.filter(
            vehicle=OuterRef('vehicle')
        ).order_by('-issue_date').values('registration_number')[:1]

        # Base queryset with annotation
        queryset = super().get_queryset().annotate(
            registration_number=Subquery(latest_traffic_card_subquery)
        )

        # Default filtering logic
        if not self.request.GET:  # If there are no GET parameters
            today = timezone.now().date()
            forty_days_ago = today - timedelta(days=40)
            start_dt, end_dt = date_range_for_datetime_field(forty_days_ago, today)
            return queryset.filter(date__gte=start_dt, date__lte=end_dt)

        # Apply filter if GET parameters are present
        form = self.filterset_class(self.request.GET, queryset=queryset)
        if form.is_valid():
            return form.qs
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.filterset_class(self.request.GET, queryset=self.get_queryset())
        context.update({
            'filter': form,
            'title': 'Lista potrošnje goriva',
        })
        return context

class FuelTransactionsListView(LoginRequiredMixin, ListView):
    template_name = 'fleet/fuel_transactions_list.html'
    context_object_name = 'fuel_transactions'

    def get_queryset(self):
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # Postavi podrazumevane vrednosti ako GET parametri nisu prisutni
        if not start_date:
            start_date = date.today() - timedelta(days=40)
        if not end_date:
            end_date = date.today()

        return get_fuel_consumption_queryset(start_date=start_date, end_date=end_date)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Inicijalizacija forme sa trenutnim GET vrednostima ili podrazumevanim datumima
        context['filter_form'] = FuelTransactionFilterForm(self.request.GET or {
            'start_date': (date.today() - timedelta(days=40)).strftime('%Y-%m-%d'),
            'end_date': date.today().strftime('%Y-%m-%d'),

        })
        context['title'] = 'Izveštaj o potrošnji goriva'
        return context



class FuelConsumptionCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = FuelConsumption
    form_class = FuelConsumptionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('fuelconsumption_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj potrošnju goriva'
        context['submit_button_label'] = 'Dodaj'
        return context

class FuelConsumptionUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = FuelConsumption
    form_class = FuelConsumptionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('fuelconsumption_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni potrošnju goriva'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class FuelConsumptionDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = FuelConsumption
    template_name = 'fleet/fuelconsumption_detail.html'
    context_object_name = 'fuel_consumption'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji potrošnje goriva {self.object.date}"
        return context

class FuelConsumptionDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = FuelConsumption
    success_url = reverse_lazy('fuelconsumption_list')
    template_name = 'fleet/fuelconsumption_confirm_delete.html'
    context_object_name = 'fuel_consumption'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši potrošnju goriva'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)





# <!-- ======================================================================================== -->
#                           <!-- EMPLOYEES -->
# <!-- ======================================================================================== -->
class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'fleet/employee_list.html'
    context_object_name = 'employees'

    def get_queryset(self):
        qs = super().get_queryset()
        show_inactive = self.request.GET.get("inactive") == "1"
        return qs.filter(is_active=not show_inactive)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista zaposlenih'
        context['show_inactive'] = self.request.GET.get("inactive") == "1"
        return context

class EmployeeCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novog zaposlenog'
        context['submit_button_label'] = 'Dodaj zaposlenog'
        return context

class EmployeeUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni podatke zaposlenog'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class EmployeeDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'fleet/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji zaposlenog {self.object.last_name} {self.object.first_name}"
        return context

class EmployeeDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy('employee_list')
    template_name = 'fleet/employee_confirm_delete.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši zaposlenog'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)




# <!-- ======================================================================================== -->
#                           <!-- FUEL CONSUMPTION -->
# <!-- ======================================================================================== -->
class IncidentListView(LoginRequiredMixin, ListView):
    model = Incident
    template_name = 'fleet/incident_list.html'
    context_object_name = 'incidents'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista incidenata'
        return context

class IncidentCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('incident_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj incident'
        context['submit_button_label'] = 'Dodaj'
        return context

class IncidentUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('incident_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni incident'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class IncidentDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Incident
    template_name = 'fleet/incident_detail.html'
    context_object_name = 'incident'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji incidenta {self.object.date}"
        return context

class IncidentDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Incident
    success_url = reverse_lazy('incident_list')
    template_name = 'fleet/incident_confirm_delete.html'
    context_object_name = 'incident'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši incident'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)




# <!-- ======================================================================================== -->
#                           <!-- PUTNI NALOG -->
# <!-- ======================================================================================== -->
def _is_uprava(user):
    return user.roles.filter(slug="uprava").exists()


def _get_allowed_centers(user):
    codes = []
    raw = (user.allowed_center_codes or "").strip()
    if raw:
        parts = [p.strip() for p in raw.replace(";", ",").split(",")]
        codes.extend([p for p in parts if p])
    unit_centers = list(
        user.allowed_centers.values_list("center", flat=True)
    )
    codes.extend([c for c in unit_centers if c])
    return sorted({c.strip() for c in codes if str(c).strip()})


def _split_putni_nalog_note_lines(note, max_lines=2, width=70):
    if not note:
        return [""] * max_lines

    wrapped_lines = []
    for raw_line in str(note).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        wrapped = textwrap.wrap(
            line,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        wrapped_lines.extend(wrapped or [""])

    if not wrapped_lines:
        wrapped_lines = [""]

    result = wrapped_lines[:max_lines]
    while len(result) < max_lines:
        result.append("")
    return result


def _putninalog_base_qs(request, include_stornirani=False):
    qs = PutniNalog.objects.select_related("job_code", "employee", "vehicle")
    if not include_stornirani:
        qs = qs.filter(storniran=False)
    user = request.user

    if not user.is_superuser and not _is_uprava(user):
        allowed_centers = _get_allowed_centers(user)
        if allowed_centers:
            qs = qs.filter(job_code__center__in=allowed_centers)
        else:
            return qs.none()

    qs = qs.annotate(
        _pn_dash_pos=StrIndex("order_number", Value("-")),
        _pn_slash_pos=StrIndex("order_number", Value("/")),
    ).annotate(
        _pn_year=Cast(
            Substr(
                "order_number",
                F("_pn_slash_pos") + 1,
                F("_pn_dash_pos") - F("_pn_slash_pos") - 1,
            ),
            IntegerField(),
        ),
        _pn_seq=Cast(
            Substr("order_number", F("_pn_dash_pos") + 1),
            IntegerField(),
        ),
        pn_sort_key=ExpressionWrapper(
            F("_pn_year") * Value(1000000) + F("_pn_seq"),
            output_field=IntegerField(),
        ),
    )

    return qs.order_by("-_pn_year", "-_pn_seq", "-id")


class PutniNalogListView(LoginRequiredMixin, FilterView):
    model = PutniNalog
    template_name = 'fleet/putninalog_list.html'
    context_object_name = 'putni_nalozi'
    filterset_class = PutniNalogFilter

    def get_queryset(self):
        return _putninalog_base_qs(self.request)

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista putnih naloga'
        return context


@role_permission_required()
def putninalog_print_list(request):
    base_qs = _putninalog_base_qs(request)
    filterset = PutniNalogFilter(request.GET, queryset=base_qs, request=request)
    putni_nalozi = filterset.qs
    return render(request, 'fleet/putninalog_list_print.html', {
        'title': 'Štampa liste putnih naloga',
        'putni_nalozi': putni_nalozi,
    })


@role_permission_required()
def putninalog_set_opravdan(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("Neispravan zahtev.")

    base_qs = _putninalog_base_qs(request)
    putni_nalog = get_object_or_404(base_qs, pk=pk)
    if not putni_nalog.opravdan:
        putni_nalog.opravdan = True
        putni_nalog.save(update_fields=["opravdan"])

    return redirect(request.META.get("HTTP_REFERER", reverse("putninalog_list")))


@role_permission_required()
def putninalog_storniraj(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("Neispravan zahtev.")

    base_qs = _putninalog_base_qs(request, include_stornirani=True)
    putni_nalog = get_object_or_404(base_qs, pk=pk)
    if not putni_nalog.storniran:
        putni_nalog.storniran = True
        putni_nalog.save(update_fields=["storniran"])

    return redirect(request.META.get("HTTP_REFERER", reverse("putninalog_list")))





class PutniNalogCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = PutniNalog
    form_class = PutniNalogForm
    template_name = 'fleet/putni_nalog_form.html'
    success_url = reverse_lazy('putninalog_list')

    def get_initial(self):
        initial = super().get_initial()
        copy_pk = self.request.GET.get("copy")
        if copy_pk:
            base_qs = _putninalog_base_qs(self.request)
            source = base_qs.filter(pk=copy_pk).first()
            if source:
                initial.update({
                    "employee": source.employee,
                    "other_employee_name": source.other_employee_name,
                    "job_code": source.job_code,
                    "travel_location": source.travel_location,
                    "task": source.task,
                    "napomena": source.napomena,
                    "contract_offer": source.contract_offer,
                    "vehicle": source.vehicle,
                    "other_vehicle": source.other_vehicle,
                    "number_of_days": source.number_of_days,
                    "advance_payment": source.advance_payment,
                    "advance_payment_currency": source.advance_payment_currency,
                    "daily_allowance": source.daily_allowance,
                    "is_weekly": source.is_weekly,
                })
                if source.vehicle:
                    initial["transport_type"] = "ims"
                elif source.other_vehicle:
                    initial["transport_type"] = "other"
                if source.employee:
                    initial["employee_type"] = "ims"
                elif source.other_employee_name:
                    initial["employee_type"] = "other"
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj putni nalog'
        context['submit_button_label'] = 'Dodaj'
        return context
    
    def form_valid(self, form):
        try:
            # Sačuvaj objekat
            self.object = form.save()
        except ValueError as exc:
            form.add_error('start_sequence', str(exc))
            return self.form_invalid(form)

        # Vrati URL za preuzimanje i preusmeravanje
        return JsonResponse({
            'redirect_url': reverse('putninalog_list'),
            'print_url': f"{reverse('putninalog_print', args=[self.object.pk])}?auto=1",
        })


class PutniNalogUpdateView(CenterMixin, RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = PutniNalog
    form_class = PutniNalogForm
    template_name = 'fleet/putni_nalog_form.html'
    success_url = reverse_lazy('putninalog_list')
    org_unit_field = "job_code"
    allow_if_no_scope = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni putni nalog'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context
    
    def form_valid(self, form):
        # Save the object
        self.object = form.save()
        return JsonResponse({
            'redirect_url': reverse('putninalog_list'),
            'print_url': f"{reverse('putninalog_print', args=[self.object.pk])}?auto=1",
        })

    def get_queryset(self):
        return PutniNalog.objects.all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.storniran:
            raise PermissionDenied("Nalog je storniran i zakljucan za izmene.")
        user = self.request.user
        if user.is_superuser:
            if obj.opravdan:
                raise PermissionDenied("Nalog je opravdan i zakljucan za izmene.")
            return obj

        center_code = getattr(obj.job_code, "center", None)
        if not center_code:
            raise PermissionDenied("Ne možete menjati naloge iz ovog centra.")

        center_code = str(center_code).strip()
        allowed_center_codes = set(self.get_user_allowed_center_codes())
        if allowed_center_codes and center_code in allowed_center_codes:
            if obj.opravdan:
                raise PermissionDenied("Nalog je opravdan i zakljucan za izmene.")
            return obj

        allowed_units = self.get_user_allowed_units()
        if allowed_units.filter(center=center_code).exists():
            if obj.opravdan:
                raise PermissionDenied("Nalog je opravdan i zakljucan za izmene.")
            return obj

        raise PermissionDenied("Ne možete menjati naloge iz ovog centra.")

class PutniNalogDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = PutniNalog
    template_name = 'fleet/putninalog_detail.html'
    context_object_name = 'putni_nalog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji putnog naloga {self.object.travel_date}"
        return context


class PutniNalogPrintView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = PutniNalog
    template_name = 'fleet/putni_nalog_print.html'
    context_object_name = 'putni_nalog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Štampa putnog naloga {self.object.order_number}"
        context['auto_print'] = self.request.GET.get('auto') == '1'
        context["napomena_lines"] = _split_putni_nalog_note_lines(self.object.napomena)
        return context

class PutniNalogDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = PutniNalog
    success_url = reverse_lazy('putninalog_list')
    template_name = 'fleet/putninalog_confirm_delete.html'
    context_object_name = 'putni_nalog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši putni nalog'
        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.storniran:
            raise PermissionDenied("Nalog je storniran i zakljucan za izmene.")
        if obj.opravdan:
            raise PermissionDenied("Nalog je opravdan i zakljucan za izmene.")
        return obj



# <!-- ======================================================================================== -->
#                           <!-- SERVICE TYPES -->
# <!-- ======================================================================================== -->
class ServiceTypeListView(LoginRequiredMixin, ListView):
    model = ServiceType
    template_name = 'fleet/servicetype_list.html'
    context_object_name = 'service_types'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista tipova servisa'
        return context

class ServiceTypeCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('servicetype_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj tip servisa'
        context['submit_button_label'] = 'Dodaj'
        return context

class ServiceTypeUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('servicetype_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni tip servisa'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class ServiceTypeDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = ServiceType
    template_name = 'fleet/servicetype_detail.html'
    context_object_name = 'service_type'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji tipa servisa {self.object.name}"
        return context

class ServiceTypeDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = ServiceType
    success_url = reverse_lazy('servicetype_list')
    template_name = 'fleet/servicetype_confirm_delete.html'
    context_object_name = 'service_type'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši tip servisa'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)



# <!-- ======================================================================================== -->
#                           <!-- SERVICES -->
# <!-- ======================================================================================== -->



class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'fleet/service_list.html'
    context_object_name = 'services'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista servisa'
        return context

class ServiceFixingListView(LoginRequiredMixin, FilterView):
    model = DraftServiceTransaction
    template_name = 'fleet/draft_service_transactions_list.html'
    context_object_name = 'service_transactions'
    filterset_class = ServiceFixingFilter


    def get_queryset(self):
        return (DraftServiceTransaction.objects
                .select_related('vehicle', 'popravka_kategorija')
                .order_by('-datum', '-id'))
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # >>> ključno: da bi {{ form.* }} radio kao ranije
        ctx['form'] = ctx['filter'].form
        return ctx


class ServiceCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('service_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj servis'
        context['submit_button_label'] = 'Dodaj'
        return context

class ServiceUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('service_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni servis'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class ServiceDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Service
    template_name = 'fleet/service_detail.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji servisa {self.object.service_date}"
        return context

class ServiceDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Service
    success_url = reverse_lazy('service_list')
    template_name = 'fleet/service_confirm_delete.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši servis'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)
    


# <!-- ======================================================================================== -->
#                           <!-- SERVICE TRANSACTIONS -->
# <!-- ======================================================================================== -->
class ServiceTransactionListView(LoginRequiredMixin, ListView):
    model = ServiceTransaction
    template_name = 'fleet/service_transactions_list.html'
    context_object_name = 'service_transactions'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista servisa - popravke van IMS-a'
        return context

@method_decorator(never_cache, name="dispatch")
class ServiceTransactionFixingListView(LoginRequiredMixin, FilterView):
    model = DraftServiceTransaction
    template_name = 'fleet/draft_service_transactions_list.html'
    context_object_name = 'service_transactions'
    filterset_class = ServiceFixingFilter


    def get_queryset(self):
        return (DraftServiceTransaction.objects
                .select_related('vehicle', 'popravka_kategorija')
                .order_by('-datum', '-id'))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Lista servisa koje morate dopuniti'
        # Ako želiš da u templatu i dalje koristiš {{ form.* }}
        ctx['form'] = ctx['filter'].form
        return ctx

class ServiceTransactionCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ServiceTransaction
    form_class = ServiceTransactionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('service_transaction_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiranje servisa'
        context['submit_button_label'] = 'Sačuvaj insformacije o servisu'
        return context
    
class ServiceTransactionUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = ServiceTransaction
    form_class = ServiceTransactionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('service_transaction_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmena servisa'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class ServiceTransactionDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = ServiceTransaction
    template_name = 'service_transaction_confirm_delete.html'
    success_url = reverse_lazy('service_transaction_list')

class DraftServiceTransactionUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = DraftServiceTransaction
    form_class = DraftServiceTransactionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('service_fixing_list')

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return str(self.success_url)

    def form_valid(self, form):
        # Sačuvaj izmene u draft tabeli
        draft = form.save(commit=False)
        logger.info("Izmene sačuvane u draft tabeli.")

        # Proveri da li su svi potrebni podaci sada prisutni osim `kom` i `napomena`
        is_complete = all([
            draft.vehicle_id is not None,
            draft.god is not None,
            draft.sif_par_pl not in [None, ''],
            draft.naz_par_pl not in [None, ''],
            draft.datum is not None,
            draft.sif_vrs not in [None, ''],
            draft.br_naloga not in [None, ''],
            draft.vez_dok not in [None, ''],
            draft.knt_pl not in [None, ''],
            draft.potrazuje is not None,
            draft.sif_par_npl not in [None, ''],
            draft.knt_npl not in [None, ''],
            draft.duguje is not None,
            draft.konto_vozila not in [None, ''],
            draft.popravka_kategorija not in [None, '']
        ])


        # Ako su svi potrebni podaci prisutni, pokreni migraciju u glavnu tabelu
        if is_complete:
            draft.save()
            migrate_draft_to_service_transaction(draft.id)
            logger.info("Podaci migrirani u glavnu tabelu.")
            messages.success(self.request, "✅ Podaci su uspešno migrirani u glavnu tabelu.")
            return redirect(self.get_success_url())
        
        # Ako podaci nisu kompletni, sačuvaj samo u draft tabeli
        else:
            logger.info("Podaci nisu kompletni, ostaju u draft tabeli.")
            messages.warning(self.request, "⚠️ Podaci nisu kompletni, ostaju u draft tabeli.")
            draft.save()  # Sačuvaj bez migracije
            return redirect(self.get_success_url())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dopunite informacije o servisu'
        context['submit_button_label'] = 'Sačuvaj insformacije o servisu'
        return context

# <!-- ======================================================================================== -->
#                           <!-- REQUISTION - TREBOVANJA -->
# <!-- ======================================================================================== -->

class RequisitionListView(LoginRequiredMixin, ListView):
    model = Requisition
    template_name = 'fleet/requisition_list.html'
    context_object_name = 'requisitions'
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Trebovanja'
        return context

class RequisitionDetailView(LoginRequiredMixin, ListView):
    model = Requisition
    template_name = 'fleet/requisition_detail.html'
    context_object_name = 'stavke'

    def get_queryset(self):
        return Requisition.objects.filter(
            br_dok=self.kwargs['br_dok'],
            god=self.kwargs['god']
        ).order_by('stavka')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['br_dok'] = self.kwargs['br_dok']
        context['god'] = self.kwargs['god']
        return context

# Draft    
class RequisitionFixingListView(LoginRequiredMixin, ListView): 
    model = DraftRequisition
    template_name = 'fleet/draft_requisition_list.html'
    context_object_name = 'requisitions'
    
    def get_queryset(self):
        return DraftRequisition.objects.filter(nije_garaza=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Trebovanja koja je potrebno dopuniti'
        return context
    
class RequisitionCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Requisition
    form_class = RequisitionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('requisition_list')
    success_message = "Requisition successfully created."

class RequisitionUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Requisition
    form_class = RequisitionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('requisition_list')
    success_message = "Trebovanje uspešno izmenjeno!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmena trebovanja'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context


class DraftRequisitionUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = DraftRequisition
    form_class = DraftRequisitionForm
    template_name = 'fleet/generic_form_draft.html'
    success_message = "Trebovanje uspešno izmenjeno!"
    success_url = reverse_lazy('requisition_fixing_list')

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return str(self.success_url)

    def form_valid(self, form):
        current_instance = form.save()

        # Ažuriraj ostale redove
        DraftRequisition.objects.filter(
            br_dok=current_instance.br_dok,
            god=current_instance.god
        ).exclude(id=current_instance.id).update(
            vehicle=current_instance.vehicle,
            datum_trebovanja=current_instance.datum_trebovanja,
            mesec_unosa=current_instance.mesec_unosa,
            popravka_kategorija=current_instance.popravka_kategorija,
            kilometraza=current_instance.kilometraza,
            nije_garaza=current_instance.nije_garaza,
            napomena=current_instance.napomena
        )

        # Obradi zapise i premesti one koji su kompletni
        draft_requisitions = DraftRequisition.objects.filter(
            br_dok=current_instance.br_dok,
            god=current_instance.god
        )

       

        for draft in draft_requisitions:
            logger.info(f"Obrada: {draft}, kompletan: {draft.is_complete()}")
            if draft.is_complete():
                logger.info("→ Premeštam u Requisition")
                Requisition.objects.create(
                    vehicle=draft.vehicle,
                    sif_pred=draft.sif_pred,
                    god=draft.god,
                    br_dok=draft.br_dok,
                    sif_vrsart=draft.sif_vrsart,
                    stavka=draft.stavka,
                    sif_art=draft.sif_art,
                    naz_art=draft.naz_art,
                    kol=draft.kol,
                    cena=draft.cena,
                    vrednost_nab=draft.vrednost_nab,
                    popravka_kategorija=draft.popravka_kategorija,
                    mesec_unosa=draft.mesec_unosa,
                    kilometraza=draft.kilometraza,
                    nije_garaza=draft.nije_garaza,
                    datum_trebovanja=draft.datum_trebovanja,
                    napomena=draft.napomena
                )
                draft.delete()

        # Proveri da li još uvek ima nedovršenih zapisa
        ostali_draftovi = DraftRequisition.objects.filter(
            br_dok=current_instance.br_dok,
            god=current_instance.god
        ).exists()

        # Pozovi funkciju za brisanje kompletnih zapisa
        delete_complete_drafts()
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Izmena trebovanja {self.object.br_dok}'
        context['submit_button_label'] = 'Sačuvaj izmene'
        context['manual'] = 'Kilometražu je poželjno uneti uvek, ali nije obavezno. ' \
        'Kada se radi o redovnim servisima, kilometraža je obavezna.'
        return context

class RequisitionDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Requisition
    template_name = 'requisition/requisition_confirm_delete.html'
    success_url = reverse_lazy('requisition_list')
    success_message = "Requisition successfully deleted."


# <!-- ======================================================================================== -->
#                                     <!-- USERS -->
# <!-- ======================================================================================== -->

class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'fleet/user_list.html'  # Specify your template
    context_object_name = 'users'     # The name of the variable to use in the template

    # Optionally, you can override get_queryset to filter users if needed
    def get_queryset(self):
        # You can apply any filters if needed, otherwise return all users
        return CustomUser.objects.all()
    

    
# <!-- ======================================================================================== -->
#                           <!-- FETCHING FUNCTIONS -->
# <!-- ======================================================================================== -->



@staff_member_required
def fetch_data_view(request):
    """
    View za prikaz HTML stranice koja sadrži sve fetching forme.
    """
    if request.method == 'POST':
        command = request.POST.get('command')
        try:
            # Provera i pokretanje komande
            if command == 'nis_command':
                call_command('nis_command')
            elif command == 'omv_command_putnicka':
                call_command('omv_command_putnicka')
            elif command == 'omv_command_teretna':
                call_command('omv_command_teretna')
            else:
                return JsonResponse({'status': 'error', 'message': 'Nepoznata komanda.'}, status=400)
            
            return JsonResponse({'status': 'success', 'message': f'Komanda {command} uspešno izvršena.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # Prikaz stranice sa svim fetching formama
    return render(request, 'fleet/fetch_data.html')


@staff_member_required
def import_nis_excel_view(request):
    """
    Ručni import NIS transakcija i potrošnje goriva iz odabranog Excel fajla.
    """
    if request.method != "POST":
        return redirect("fetch_data")

    excel_file = request.FILES.get("excel_file")
    if not excel_file:
        messages.error(request, "Nije izabran Excel fajl.")
        return redirect("fetch_data")

    extension = os.path.splitext(excel_file.name or "")[1] or ".xlsx"
    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            for chunk in excel_file.chunks():
                tmp_file.write(chunk)
            temp_file_path = tmp_file.name

        from .selenium_integrations import import_nis_fuel_consumption, import_nis_transactions

        import_nis_fuel_consumption(temp_file_path)
        import_nis_transactions(temp_file_path)
        messages.success(request, "NIS Excel import je uspešno završen.")
    except Exception as exc:
        logger.exception("Greška prilikom ručnog NIS Excel importa.")
        messages.error(request, f"Greška prilikom importa: {exc}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                logger.warning("Nije moguće obrisati privremeni fajl: %s", temp_file_path)

    return redirect("fetch_data")


def _handle_omv_csv_import(request, category_label):
    csv_file = request.FILES.get("omv_csv_file")
    if not csv_file:
        messages.error(request, "Nije izabran OMV CSV fajl.")
        return redirect("fetch_data")

    extension = (os.path.splitext(csv_file.name or "")[1] or ".csv").lower()
    if extension != ".csv":
        messages.error(request, "OMV ručni import podržava samo CSV fajl.")
        return redirect("fetch_data")

    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            for chunk in csv_file.chunks():
                tmp_file.write(chunk)
            temp_file_path = tmp_file.name

        from .selenium_integrations import import_omv_fuel_consumption_from_csv, import_omv_transactions_from_csv

        import_omv_fuel_consumption_from_csv(temp_file_path)
        import_omv_transactions_from_csv(temp_file_path)
        messages.success(request, f"OMV {category_label} CSV import je uspešno završen.")
    except Exception as exc:
        logger.exception("Greška prilikom ručnog OMV %s CSV importa.", category_label)
        messages.error(request, f"Greška prilikom OMV {category_label} importa: {exc}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                logger.warning("Nije moguće obrisati privremeni fajl: %s", temp_file_path)

    return redirect("fetch_data")


@staff_member_required
def import_omv_putnicka_csv_view(request):
    if request.method != "POST":
        return redirect("fetch_data")
    return _handle_omv_csv_import(request, "putnicka")


@staff_member_required
def import_omv_teretna_csv_view(request):
    if request.method != "POST":
        return redirect("fetch_data")
    return _handle_omv_csv_import(request, "teretna")



# POVLACENJE PODATAKA IZ DRUGE BAZE
def fetch_vehicle_value_view(request):
    if request.method == 'POST':
        # Povlačenje podataka iz druge baze
        with connections['test_db'].cursor() as cursor:
            cursor.execute("""
                SELECT sif_osn, vrednost FROM dbo.vrednost_vozila
            """)
            rows = cursor.fetchall()

        # Broj ažuriranih vozila
        updated_vehicles_count = 0

        for row in rows:
            sif_osn = row[0].strip()  # Polje 'sif_osn' iz druge baze (odgovara 'inventory_number' u modelu Vehicle)
            vrednost = row[1]  # Polje 'vrednost' iz druge baze (odgovara polju 'value' u modelu Vehicle)

            try:
                # Pronađi vozilo po inventory_number (sif_osn)
                logger.info(sif_osn)
                vehicle = Vehicle.objects.get(inventory_number=sif_osn)
                # Ažuriraj polje 'value' sa novom vrednošću
                vehicle.value = vrednost
                vehicle.save()
                updated_vehicles_count += 1

            except Vehicle.DoesNotExist:
                # Ako vozilo sa datim 'sif_osn' ne postoji, preskoči i zapiši grešku
                logger.warning(f"Vozilo sa inventory_number (sif_osn) {sif_osn} nije pronađeno.")
                continue

            except Exception as e:
                # U slučaju bilo koje druge greške
                logger.error(f"Greška prilikom ažuriranja vozila sa inventory_number {sif_osn}: {e}")
                messages.error(request, "Došlo je do greške prilikom ažuriranja podataka o vozilu.")
                return redirect('fetch_policies')

        # Poruka o uspešnom ažuriranju
        messages.success(request, f"Uspešno ažurirano {updated_vehicles_count} vozila.")

        # Preusmeravanje nakon uspešnog povlačenja podataka
        return redirect('fetch_policies')  # Postavi URL na koji želiš da preusmeriš korisnika

    return render(request, 'fleet/fetch_data.html')


# LEASE KAMATE FETCH
def fetch_lease_interest_data(request):
    if request.method == 'POST':
        # Povlačenje podataka iz view-a u bazi
        with connections['test_db'].cursor() as cursor:
            cursor.execute("""
                SELECT god, ugovor, iznos FROM dbo.lizing_kamate
            """)
            rows = cursor.fetchall()

        for row in rows:
            year = row[0]
            contract_number = row[1].strip()
            interest_amount = row[2]

            try:
                # Pronađi ugovor lizinga po broju ugovora
                lease = Lease.objects.get(contract_number=contract_number)

                # Proveri da li već postoji zapis za tu godinu i lizing ugovor
                lease_interest, created = LeaseInterest.objects.get_or_create(
                    lease=lease,
                    year=year,
                    defaults={'interest_amount': interest_amount}
                )

                if not created:
                    # Ako zapis već postoji, možeš ga ažurirati ako je potrebno
                    lease_interest.interest_amount = interest_amount
                    lease_interest.save()

            except Lease.DoesNotExist:
                logger.warning(f"Lizing ugovor sa brojem {contract_number} nije pronađen.")
                continue

        # Nakon uspešne obrade, preusmeravanje ili prikaz poruke
        return redirect('fetch_policies')  # Preusmeri na odgovarajući URL za prikaz lizing kamata

    return render(request, 'fleet/fetch_data.html')

def fetch_policy_data_view(request):
    if request.method == 'POST':
        days = request.POST.get('days')
        result = None
        
        try:
            if days:
                days = int(days)
                if days < 0:
                    raise ValueError
                result = fetch_policy_data(last_24_hours=False, days=days)
            else:
                result = fetch_policy_data()
            
            if result.startswith('Critical error'):
                messages.error(request, result)
            else:
                messages.success(request, result)
                
        except ValueError:
            messages.error(request, "Invalid number of days")
        
        return redirect('policy_list')

    return render(request, 'fleet/fetch_policy_data.html')


# POVLACENJE PODATAKA IZ DRUGE BAZE
def fetch_service_data_view(request):
    if request.method == 'POST':
        days_str = request.POST.get('days', '').strip() # Preuzmi string i ukloni whitespace

        days = None # Podrazumevano postavi na None
        if days_str: # Proveri da li string nije prazan
            try:
                days = int(days_str)
                if days <= 0: # Dodatna validacija: broj dana mora biti pozitivan
                    messages.error(request, "Broj dana mora biti pozitivan broj.")
                    return redirect('fetch_service_data')
            except ValueError:
                messages.error(request, "Uneta vrednost za broj dana nije validna.")
                return redirect('fetch_service_data')

        # Pozovi funkciju za povlačenje podataka.
        # Ako je 'days' None, 'last_24_hours' će kontrolisati.
        # Ako je 'days' int, 'last_24_hours' će biti pregaženo 'days' parametrom.
        result = fetch_service_data(last_24_hours=(days is None), days=days)
        messages.success(request, result)
        return redirect('service_transaction_list')

    # Prikaz forme za unos broja dana
    return render(request, 'fleet/fetch_service_data.html')


def fetch_requisition_data_view(request):
    if request.method == 'POST':
        days = request.POST.get('days', None)
        if days:
            try:
                days = int(days)
            except ValueError:
                messages.error(request, "Uneta vrednost za broj dana nije validna.")
                return redirect('fetch_policies')

        result = fetch_requisition_data(last_24_hours=False, days=days)
        messages.success(request, result)
        return redirect('requisition_list')

    return render(request, 'fleet/fetch_data.html')

def fetch_ddor_data_view(request):
    if request.method == 'POST':
        days = request.POST.get('days', None)
        if days:
            try:
                days = int(days)
            except ValueError:
                messages.error(request, "Uneta vrednost za broj dana nije validna.")
                return redirect('fetch_policies')  # ili gde god želiš da vratiš usera

        # poziv util funkcije
        result = fetch_ddor_insurance_data()
        messages.success(request, result)
        return redirect('insurance_fixing_list')  # ili 'insurance_list' ako hoćeš pregled finalnih

class KontoListView(LoginRequiredMixin, ListView):
    model = KontaVozila
    template_name = "fleet/konta_list.html"
    context_object_name = "konta"
    paginate_by = 50
    ordering = ("knt",)

class KontoCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = KontaVozila
    fields = ["knt", "naz_knt"]
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("konta_list")
    success_message = "Konto %(knt)s je dodat."

class KontoUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):

    model = KontaVozila
    fields = ["naz_knt"]
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("konta_list")
    success_message = "Konto %(knt)s je izmenjen."

class KontoDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = KontaVozila
    template_name = "fleet/konta_confirm_delete.html"
    success_url = reverse_lazy("konta_list")
    success_message = "Konto je obrisan."


# <!-- ======================================================================================== -->
#                           <!-- IZVESTAJI -->
# <!-- ======================================================================================== -->

def reports_index(request):
    """Početna stranica za izveštaje sa linkovima."""
    sections = {
        "Finansije": [
            {"name": "Spisak vozila po šiframa posla", "url": "vehicle_list"},
            {"name": "Pregled potrošnje goriva po šiframa posla - OMV putnicka", "url": "omv_putnicka"},
            {"name": "Pregled potrošnje goriva po šiframa posla - OMV teretna", "url": "omv_teretna"},
            {"name": "Pregled potrošnje goriva po šiframa posla - NIS putnicka", "url": "nis_putnicka"},
            {"name": "Pregled potrošnje goriva po šiframa posla - NIS teretna", "url": "nis_teretna"},
        ],
        "Centri": [
            # {"name": "Pregled putnih naloga po godinama", "url": "kasko_rate"},
            {"name": "Zatvoreni putni nalozi", "url": "zatvoreni_putni"},
        ],
        "Garaža": [
            {"name": "Trenutno stanje u magacinu", "url": "magacin"},
            {"name": "Spisak otpisanih vozila", "url": "otpis"},
            # {"name": "Trenutno stanje u magacinu", "url": "tro_gorivo_mesec"},
        ],
        "Uprava": [
            {"name": "Promet goriva po mesecima", "url": "tro_gorivo_mesec"},
            {"name": "Pregled ukupnih troskova, pa po kontima, pa po centrima, po mesecima ", "url": "troskovi_svi"},
            {"name": "Troškovi praćenja vozila", "url": "tro_pracenja_vozila"},
            {"name": "Troškovi tahografa ", "url": "troskovi_tahograf"},
            {"name": "Troškovi parkinga", "url": "tro_parking"},
            {"name": "Pregled Potraživanja od osiguranja", "url": "potrazivanje_ddor"},
            {"name": "Pregled Najvećih Dobavljača Usluga", "url": "po_dobavljacima"},
            
        ],
    }

    return render(request, 'fleet/reports_index.html', {"sections": sections})


def omv_putnicka_view(request):
    form = OMVPutnickaFilterForm(request.GET or None)

    query = OMV_PUTNICKA_SQL

    query, params = report_period_filtered_query(query, form)

    data = get_data_from_secondary_db(query, 'test_db', params=params)

    # Excel export
    if 'export' in request.GET:

        return dataframe_xlsx_response(data, "omv_putnicka.xlsx", "OMV Putnicka")

    return render(request, 'fleet/reports/omv_putnicka.html', {
        'data': data,
        'form': form,
        'title': 'OMV Putnička vozila'
    })


def export_omv_putnicka_excel(request):
    form = PutnickaFilterForm(request.GET or None)

    query = OMV_PUTNICKA_SQL

    query, params = report_period_filtered_query(query, form, cast_params=True)

    data = get_data_from_secondary_db(query, 'test_db', params=params)

    return report_xlsx_response(OMV_PUTNICKA_EXPORT, data)

def nis_putnicka_view(request):
    form = PutnickaFilterForm(request.GET or None)

    query = NIS_PUTNICKA_SQL

    query, params = report_period_filtered_query(query, form)

    data = get_data_from_secondary_db(query, 'test_db', params=params)

    # Excel export
    if 'export' in request.GET:
        return dataframe_xlsx_response(data, "nis_putnicka.xlsx", "NIS Putnicka")

    return render(request, 'fleet/reports/nis_putnicka.html', {
        'data': data,
        'form': form,
        'title': 'NIS Putnička vozila'
    })

def export_nis_putnicka_excel(request):
    form = PutnickaFilterForm(request.GET or None)

    query = NIS_PUTNICKA_SQL

    query, params = report_period_filtered_query(query, form, cast_params=True)

    data = get_data_from_secondary_db(query, 'test_db', params=params)

    return report_xlsx_response(NIS_PUTNICKA_EXPORT, data)

def nis_teretna_view(request):
    form = PutnickaFilterForm(request.GET or None)

    query = NIS_TERETNA_SQL

    query, params = date_period_filtered_query(query, form)

    data = get_data_from_secondary_db(query, 'test_db', params=params)

    # Excel export
    if 'export' in request.GET:
        return dataframe_xlsx_response(data, "nis_teretna.xlsx", "NIS Teretna")

    return render(request, 'fleet/reports/nis_teretna.html', {
        'data': data,
        'form': form,
        'title': 'NIS Teretna vozila'
    })



def export_nis_teretna_excel(request):
    form = PutnickaFilterForm(request.GET or None)

    query = NIS_TERETNA_SQL

    query, params = date_period_filtered_query(query, form, cast_params=True)

    data = get_data_from_secondary_db(query, 'test_db', params=params)

    return report_xlsx_response(NIS_TERETNA_EXPORT, data)


def omv_teretna_view(request):
    form = PutnickaFilterForm(request.GET or None)

    query = OMV_TERETNA_SQL

    query, params = report_period_filtered_query(query, form)

    data = get_data_from_secondary_db(query, 'test_db', params=params)

    # Excel export
    if 'export' in request.GET:
        return dataframe_xlsx_response(data, "omv_teretna.xlsx", "OMV Teretna")

    return render(request, 'fleet/reports/omv_teretna.html', {
        'data': data,
        'form': form,
        'title': 'OMV Teretna vozila'
    })

def export_omv_teretna_excel(request):
    form = PutnickaFilterForm(request.GET or None)

    query = OMV_TERETNA_SQL

    query, params = report_period_filtered_query(query, form, cast_params=True)

    data = get_data_from_secondary_db(query, 'test_db', params=params)

    return report_xlsx_response(OMV_TERETNA_EXPORT, data)

def kasko_rate_view(request):
    """
    View za prikaz podataka iz dbo.kasko_rate.
    """
    query = "SELECT * FROM dbo.kasko_rate"
    data = get_data_from_secondary_db(query, 'test_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/kasko_rate.html', {'data': data})

	
def zatvoren_putni_view(request):
    """
    View za prikaz podataka iz dbo.fleet_zatvoren_putni.
    """
    query = "SELECT * FROM dbo.fleet_zatvoren_putni"
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/zatvoreni_putni.html', {'data': data})


def magacin_view(request):
    """
    View za prikaz podataka iz dbo.fleet_magacin_rez.
    """
    query = """
        SELECT sif_pred, god, oj, sif_mag, sif_art, kolul, koliz, popkol, vrulnab, vriznab,
               vrulvp, vrizvp, revalzal, razliz, mag_cena, kolpon, cenapon, naz_art,
               sif_vrsart, naz_vrsart
        FROM dbo.fleet_magacin_rez
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/magacin.html', {'data': data})


def otpis_view(request):
    """
    View za prikaz podataka iz fleet_otpis
    """
    query = """
        SELECT sif_pred, god, sif_osn, rb, naz_osn, inv_br, kol, jed_mere, sif_par, knt, oj, sif_lok,
               sif_amort, sif_reval, stopa_dogam, dat_stavlj, dat_prest, iznos_val, skr_naz, poreklo,
               nab_vred, osnovica, otpis, status, br_fakture, zemljiste_ar, zemljiste_m, u_gramima,
               sif_amortP, sif_revalP, otpisP, otudjena_vrednost, ind_trosak, opis, osnovicaP,
               ind_manjak, ind_amort, knt_ispravka, sif_kor, stopa_amort
        FROM dbo.fleet_otpis
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/otpis.html', {'data': data})

def tro_gorivo_mesec_view(request):
    """
    View za prikaz podataka iz dbo.fleet_tro_goriva_m.
    """
    query = """
        SELECT god, mesec, kategorija, iznos
        FROM dbo.fleet_tro_goriva_m
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/tro_gorivo_mesec.html', {'data': data})

def troskovi_svi_view(request):
    """
    View za prikaz podataka iz dbo.Troskovi_svi.
    """
    query = """
        SELECT god, sif_vrs, datum, br_naloga, stavka, oj, knt, naz_knt, duguje, sif_pos
        FROM dbo.fleet_tro_svi
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/troskovi_svi.html', {'data': data})

def tro_pracenja_vozila_view(request):
    """
    View za prikaz podataka iz dbo.TroPracenjaVozila.
    """
    query = """
        SELECT PartnerPIB, PartnerIme, ID, BrojFakture, issuedate, ZaPlacanje, Konto_tro
        FROM dbo.fleet_tro_pracenje
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/tro_pracenja_vozila.html', {'data': data})

def tahograf_partneri_view(request):
    """
    View za prikaz podataka iz dbo.TroTahografa.
    """
    query = """
        SELECT *
        FROM dbo.fleet_tro_taho
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/tro_tahografa.html', {'data': data})

def tro_zarade_view(request):
    """
    View za prikaz podataka iz dbo.tro_zarade.
    """
    query = """
        SELECT oj, god, mesec, rasif, ranaz, neto, bruto, bruto2
        FROM dbo.tro_zarade
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/tro_zarade.html', {'data': data})

def tro_parking_view(request):
    """
    View za prikaz podataka iz dbo.tro_parking.
    """
    query = """
        SELECT PartnerPIB, PartnerIme, ID, BrojFakture, issuedate, note, naziv, ZaPlacanje
        FROM dbo.fleet_tro_parking
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/tro_parking.html', {'data': data})

def po_dobavljacima_view(request):
    """
    View za prikaz podataka iz dbo.po_dobavljacima.
    """
    query = """
        SELECT naz_par, sif_pred, god, sif_vrs, br_naloga, stavka, oj, knt, grupa, sif_par, datum, vez_dok,
               duguje, potrazuje, skr_naz, deviza, kom, stavka_k, dpo, promena, sif_pos, dat_naloga, d_p, placeno
        FROM dbo.fleet_dobavljaci
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/po_dobavljacima.html', {'data': data})

def potrazivanje_ddor_view(request):
    """
    View za prikaz podataka iz dbo.potrazivanje_ddor.
    """
    query = """
        SELECT god, sif_vrs, br_naloga, stavka, oj, knt, datum, vez_dok, potrazuje
        FROM dbo.fleet_potrazivanje_ddor
    """
    data = get_data_from_secondary_db(query, 'server_db')  # test_db je alias za sekundarnu bazu
    return render(request, 'fleet/reports/potrazivanje_ddor.html', {'data': data})



class PoliciesMonthlyCostsView(LoginRequiredMixin, FilterView, ListView):
    """
    FilterView + ListView:
    - koristi django-filter formu za filtere
    - prikazuje listu (agregiranih) redova
    """
    template_name = "fleet/reports/policies_monthly_costs.html"
    context_object_name = "rows"
    filterset_class = PoliciesMonthlyCostsFilter


    def get_queryset(self):
        # Annotirani i agregirani QS nad Policy
        return policies_monthly_costs_qs(Policy.objects.all()).order_by(
            'year', 'month', 'center', 'oj_id', 'job_code', 'vrsta'
        )
    
def policies_monthly_costs_csv(request):
    qs = _filtered_qs(request)
    response = csv_attachment_response("polise_mesecni_troskovi_sve_godine.csv", quoted=True)
    writer = csv.writer(response)
    writer.writerow(['god', 'mesec', 'centar', 'oj_id', 'oj_naziv', 'sifra_posla', 'vrsta', 'iznos'])
    for r in qs:
        writer.writerow([
            r['year'], r['month'], r['center'] or '', r['oj_id'] or '',
            r['oj_name'] or '', r.get('job_code') or '', r['vrsta'] or '',
            f"{(r['iznos'] or 0):.2f}",
        ])
    return response


class LeaseMonthlyCostsView(LoginRequiredMixin, ListView):
    """
    Prikaz mjesečnih troškova po vrstama lizinga.
    Vraća rows sa poljima: year, month, center, oj_id, oj_name, job_code, lease_type,
    lease_amount, accompanying_total, accompanying_per_vehicle, vehicle_count
    """
    template_name = "fleet/reports/lease_monthly_costs.html"
    context_object_name = "rows"
    paginate_by = 200

    def get_queryset(self):
        return lease_monthly_costs_rows(self.request)
    

class ServiceMonthlyCostsView(LoginRequiredMixin, FilterView):
    template_name = "fleet/reports/service_monthly_costs.html"
    context_object_name = "rows"
    filterset_class = ServiceMonthlyCostsFilter  # <-- bez navodnika!

    def get_queryset(self):
        return service_monthly_costs_rows(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Mesečni troškovi servisa po centru"
        return ctx
    
@login_required
def service_monthly_costs_csv(request):
    rows = service_monthly_costs_rows(request)

    resp = csv_attachment_response("service_monthly_costs.csv", charset=None, quoted=True)

    w = csv.writer(resp)
    # zaglavlje koje odgovara poljima iz service_monthly_costs_rows
    w.writerow(['Godina', 'Mesec', 'OJ', 'Centar', 'Ukupan trosak'])

    for r in rows:
        w.writerow([
            r['year'],
            r['month'],
            r.get('oj_code_txt') or '',
            r.get('center_code_txt') or '',
            f"{r['iznos']:.2f}",
        ])

    return resp


from django.db import transaction
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect
from django.contrib import messages

from .models import Insurance, DraftInsurance
from .forms import InsuranceForm, DraftInsuranceForm


# ----------------------------
# FINAL: LIST & DETAIL (po dokumentu)
# ----------------------------

class InsuranceListView(LoginRequiredMixin, ListView):
    model = Insurance
    template_name = "fleet/insurance_list.html"
    context_object_name = "insurances"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Osiguranja"
        return ctx


class InsuranceDetailView(LoginRequiredMixin, ListView):
    """
    Prikaz svih stavki jednog naloga (br_naloga, god) — analogno RequisitionDetailView.
    """
    model = Insurance
    template_name = "fleet/insurance_detail.html"
    context_object_name = "stavke"

    def get_queryset(self):
        return (
            Insurance.objects
            .filter(br_naloga=self.kwargs["br_naloga"], god=self.kwargs["god"])
            .order_by("stavka")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["br_naloga"] = self.kwargs["br_naloga"]
        ctx["god"] = self.kwargs["god"]
        ctx["title"] = f"Osiguranje {ctx['br_naloga']} ({ctx['god']})"
        return ctx


# ----------------------------
# DRAFT: LIST ZA DOPUNU
# ----------------------------

class InsuranceFixingListView(LoginRequiredMixin, ListView):
    """
    Draft zapisi kojima nedostaju ključni podaci (npr. vehicle ili datum) i koje treba dopuniti.
    """
    model = DraftInsurance
    template_name = "fleet/draft_insurance_list.html"
    context_object_name = "insurances"

    def get_queryset(self):
        return (
            DraftInsurance.objects
            .filter(~Q(kola=False))  # sve osim False (dakle True ili NULL)
            .order_by("god", "br_naloga", "stavka")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Potrayivanja od osiguranja koja je potrebno dodeliti automobilu"
        return ctx


# ----------------------------
# FINAL: CREATE / UPDATE / DELETE
# ----------------------------

class InsuranceCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Insurance
    form_class = InsuranceForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("insurance_list")
    success_message = "Osiguranje uspešno kreirano."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novo osiguranje"
        ctx["submit_button_label"] = "Sačuvaj"
        return ctx


class InsuranceUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Insurance
    form_class = InsuranceForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("insurance_list")
    success_message = "Osiguranje uspešno izmenjeno."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmena osiguranja"
        ctx["submit_button_label"] = "Sačuvaj izmene"
        return ctx


class InsuranceDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Insurance
    template_name = "fleet/insurance_confirm_delete.html"
    success_url = reverse_lazy("insurance_list")


# ----------------------------
# DRAFT: UPDATE sa PROPAGACIJOM + MIGRACIJA
# ----------------------------

def _migrate_one_draft_insurance(draft: DraftInsurance):
    """
    Jedan draft → final Insurance (transactional).
    Kriterijum kompletiranja je definisan u draft.is_complete().
    Ako već postoji final sa istim ključem, ažurira ga.
    """
    if not draft.is_complete():
        return None

    with transaction.atomic():
        ins, created = Insurance.objects.get_or_create(
            god=draft.god,
            sif_vrs=draft.sif_vrs,
            br_naloga=draft.br_naloga,
            stavka=draft.stavka,
            knt=draft.knt,
            defaults=dict(
                vehicle=draft.vehicle,
                oj=draft.oj,
                datum=draft.datum,
                vez_dok=draft.vez_dok,
                potrazuje=draft.potrazuje,
                kola=draft.kola,
            ),
        )
        if not created:
            # Ažuriraj podatke (meko prepisivanje)
            ins.vehicle = draft.vehicle
            ins.oj = draft.oj
            ins.datum = draft.datum
            ins.vez_dok = draft.vez_dok
            ins.potrazuje = draft.potrazuje
            ins.kola = draft.kola
            ins.save()

        draft.delete()
        return ins


def delete_complete_draft_insurances():
    """
    Opciono: očisti draft zapise koji su postali “prazni” scenario (ako se nešto eksterno promeni).
    Ovde jednostavno ne radimo ništa – ostavljeno za simetriju sa Trebovanjem.
    """
    return


class DraftInsuranceUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """
    Analogno DraftRequisitionUpdateView:
    - Sačuva izmenjeni draft red (jedna stavka),
    - Propagira izmenjene ključne vrednosti na sve stavke istog dokumenta (br_naloga, god),
    - Pokuša migraciju svakog reda u final ako je kompletan,
    - Ako ostane nedovršenih → vrati na fixing listu; inače → na detail tog dokumenta.
    """
    model = DraftInsurance
    form_class = DraftInsuranceForm
    template_name = "fleet/generic_form_draft.html"
    success_message = "Osiguranje uspešno izmenjeno."
    success_url = reverse_lazy("insurance_fixing_list")

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return str(self.success_url)

    def form_valid(self, form):
        current = form.save()

        # Ponovo skup svih draftova za ovaj dokument (uklj. trenutni)
        all_drafts = DraftInsurance.objects.filter(
            br_naloga=current.br_naloga, god=current.god
        ).order_by("stavka")

        # Pokušaj migracije svih koji su kompletni
        migrated = 0
        for d in list(all_drafts):
            ins = _migrate_one_draft_insurance(d)
            if ins:
                migrated += 1

        # Opciono: očisti kompletne draftove (nema potrebe, već ih brišemo pri migraciji)
        delete_complete_draft_insurances()

        # Ako su ostali neki draftovi → vrati na fixing listu, inače na detail
        still_exists = DraftInsurance.objects.filter(
            br_naloga=current.br_naloga, god=current.god
        ).exists()

        if still_exists:
            messages.info(self.request, f"Delimično premešteno ({migrated}). Dovršite preostale stavke.")
            return redirect(self.get_success_url())
        else:
            messages.success(self.request, f"Premešteno u final ({migrated}).")
            return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Izmena osiguranja {self.object.br_naloga}"
        ctx["submit_button_label"] = "Sačuvaj izmene"
        # Po želji: kratko uputstvo
        ctx["manual"] = (
            "Unesite vozilo, ako se potraživanje ne odnosi na vozilo polje 'Odnosi se na vozilo' postavite NE"
        )
        return ctx

from .utils import fetch_ddor_insurance_data, migrate_draft_to_insurance_single
from .models import DraftInsurance
def insurance_fetch_ddor_view(request):
    """
    POST /insurance/fetch-ddor/
    Povuče podatke iz view-a u DraftInsurance.
    """
    msg = fetch_ddor_insurance_data()
    messages.info(request, msg)
    # Preusmeri na listu draftova za dopunu (ili gde želiš)
    return redirect("insurance_fixing_list")



def insurance_migrate_one_view(request, draft_id, vehicle_id):
    """
    POST /insurance/migrate-one/<draft_id>/<vehicle_id>/
    Migrira jedan draft zapis u final Insurance.
    """
    try:
        ins = migrate_draft_to_insurance_single(draft_id, vehicle_id)
        messages.success(request, f"Premešteno u final: {ins}")
        # ako želiš nazad na detail dokumenta:
        return redirect("insurance_detail", god=ins.god, br_naloga=ins.br_naloga)
    except Exception as e:
        messages.error(request, f"Greška: {e}")
        # vrati na edit tog draft-a ili na fixing list
        try:
            d = DraftInsurance.objects.get(id=draft_id)
            return redirect("draft_insurance_update", pk=d.id)
        except Exception:
            return redirect("insurance_fixing_list")

