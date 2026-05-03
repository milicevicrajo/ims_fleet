from collections import defaultdict
import datetime
from datetime import date, timedelta
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Exists, ExpressionWrapper, F, IntegerField, Max, Min, OuterRef, Q, Subquery, Sum
from django.db.models.functions import TruncMonth, TruncYear
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin, role_permission_required
from core.models import CustomUser, OrganizationalUnit

from ..analytics_helpers import (
    cost_per_km_status,
    cost_per_km_thresholds,
    is_red_zone,
    net_maintenance_cost,
)
from ..filters import (
    ServiceFixingFilter,
    TrafficCardFilterForm,
    VehicleFilter,
    PutniNalogFilter,
)
from ..forms import (
    DraftRequisitionForm,
    DraftServiceTransactionForm,
    JobCodeForm,
    OrganizationalUnitForm,
    PutniNalogForm,
    RequisitionForm,
    ServiceForm,
    ServiceTransactionForm,
    ServiceTypeForm,
    TrafficCardForm,
    VehicleTenderDocumentForm,
    VehicleForm,
)
from ..models import (
    DraftInsurance,
    DraftPolicy,
    DraftRequisition,
    DraftServiceTransaction,
    FuelConsumption,
    Insurance,
    JobCode,
    KontaVozila,
    Lease,
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
from ..mixins import CenterMixin
# Compatibility re-exports for fleet.urls and existing imports.
from .insurance import (
    DraftInsuranceUpdateView,
    InsuranceCreateView,
    InsuranceDeleteView,
    InsuranceDetailView,
    InsuranceFixingListView,
    InsuranceListView,
    InsuranceUpdateView,
    fetch_ddor_data_view,
    insurance_fetch_ddor_view,
    insurance_migrate_one_view,
)
from .vehicles import (
    VehicleCreateView,
    VehicleDeleteView,
    VehicleDetailView,
    VehicleListView,
    VehicleTogleStatusView,
    VehicleUpdateView,
    vehicle_export_csv,
)
from .reference import (
    JobCodeCreateView,
    JobCodeDeleteView,
    JobCodeDetailView,
    JobCodeListView,
    JobCodeUpdateView,
    KontoCreateView,
    KontoDeleteView,
    KontoListView,
    KontoUpdateView,
    OrganizationalUnitCreateView,
    OrganizationalUnitListView,
    OrganizationalUnitUpdateView,
    TrafficCardCreateView,
    TrafficCardDeleteView,
    TrafficCardDetailView,
    TrafficCardListView,
    TrafficCardUpdateView,
    VehicleTenderDocumentCreateView,
    VehicleTenderDocumentDeleteView,
    VehicleTenderDocumentDetailView,
    VehicleTenderDocumentListView,
    VehicleTenderDocumentUpdateView,
)
from .services import (
    DraftRequisitionUpdateView,
    DraftServiceTransactionUpdateView,
    RequisitionCreateView,
    RequisitionDeleteView,
    RequisitionDetailView,
    RequisitionFixingListView,
    RequisitionListView,
    RequisitionUpdateView,
    ServiceCreateView,
    ServiceDeleteView,
    ServiceDetailView,
    ServiceFixingListView,
    ServiceListView,
    ServiceTransactionCreateView,
    ServiceTransactionDeleteView,
    ServiceTransactionFixingListView,
    ServiceTransactionListView,
    ServiceTransactionUpdateView,
    ServiceTypeCreateView,
    ServiceTypeDeleteView,
    ServiceTypeDetailView,
    ServiceTypeListView,
    ServiceTypeUpdateView,
    ServiceUpdateView,
    fetch_requisition_data_view,
    fetch_service_data_view,
)
from .putni_nalozi import (
    PutniNalogCreateView,
    PutniNalogDeleteView,
    PutniNalogDetailView,
    PutniNalogListView,
    PutniNalogPrintView,
    PutniNalogUpdateView,
    putninalog_print_list,
    putninalog_set_opravdan,
    putninalog_storniraj,
)
from .sync import (
    fetch_data_view,
    fetch_lease_interest_data,
    fetch_policy_data_view,
    fetch_vehicle_value_view,
    import_nis_excel_view,
    import_omv_putnicka_csv_view,
    import_omv_teretna_csv_view,
)
from .garaza import (
    GarazaHomeView,
    KvarCreateView,
    KvarDeleteView,
    KvarDetailView,
    KvarIMSListView,
    KvarListView,
    KvarPrintView,
    KvarTrebovanjeView,
    KvarUpdateView,
    KvarVanIMSListView,
    KvarWorkOrderView,
    ProcurementRequestCreateView,
    ProcurementRequestDetailView,
    ProcurementRequestListView,
    ProcurementRequestPrintView,
    VehicleTravelOrderCloseView,
    VehicleTravelOrderCreateView,
    VehicleTravelOrderDeleteView,
    VehicleTravelOrderDetailView,
    VehicleTravelOrderFuelReportView,
    VehicleTravelOrderListView,
    VehicleTravelOrderRequestView,
    VehicleTravelOrderUpdateView,
)
from .fuel import (
    FuelConsumptionCreateView,
    FuelConsumptionDeleteView,
    FuelConsumptionDetailView,
    FuelConsumptionListView,
    FuelConsumptionUpdateView,
    FuelTransactionsListView,
)
from .lease import (
    LeaseCreateView,
    LeaseDeleteView,
    LeaseDetailView,
    LeaseListView,
    LeaseMonthlyCostsView,
    LeaseUpdateView,
    export_leases_to_excel,
)
from .policy import (
    DraftPolicyUpdateView,
    ExpiringAndNotRenewedPolicyView,
    PoliciesMonthlyCostsView,
    PolicyCreateView,
    PolicyDeleteView,
    PolicyDetailView,
    PolicyFixingListView,
    PolicyListView,
    PolicyUpdateView,
    policies_monthly_costs_csv,
)
# Compatibility re-exports for fleet.urls and existing imports/tests.
from ..fuel_helpers import (
    calculate_average_fuel_consumption,
    calculate_average_fuel_consumption_ever,
    date_range_for_datetime_field,
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
    

    
