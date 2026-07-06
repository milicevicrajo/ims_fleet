from collections import defaultdict
from datetime import date, timedelta
import calendar

from django.db.models import OuterRef, Subquery, Sum

from ..models import (
    FuelConsumption,
    Insurance,
    JobCode,
    Lease,
    LeaseInterest,
    Policy,
    Requisition,
    ServiceTransaction,
    TrafficCard,
    Vehicle,
    VehicleTravelOrder,
)
from .analytics import cost_per_km_status, cost_per_km_thresholds, fixed_cost_per_km_threshold
from .fuel import date_range_for_datetime_field

LONG_TERM_LEASE_TYPES = set(Lease.LONG_TERM_LEASE_TYPE_VALUES)


def _as_date(value):
    return value.date() if hasattr(value, "date") else value


def _valid_number(value):
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _mileage_readings(vehicle):
    readings = []
    invalid_fuel_count = 0

    for row in FuelConsumption.objects.filter(vehicle=vehicle).values("date", "mileage"):
        mileage = _valid_number(row["mileage"])
        if mileage is None:
            invalid_fuel_count += 1
            continue
        readings.append({"date": _as_date(row["date"]), "mileage": mileage, "source": "Točenje"})

    for order in VehicleTravelOrder.objects.filter(vehicle=vehicle).values(
        "created_at",
        "closed_at",
        "start_mileage",
        "end_mileage",
    ):
        start_mileage = _valid_number(order["start_mileage"])
        if start_mileage is not None and order["created_at"]:
            readings.append({"date": _as_date(order["created_at"]), "mileage": start_mileage, "source": "Zaduženje"})

        end_mileage = _valid_number(order["end_mileage"])
        if end_mileage is not None and order["closed_at"]:
            readings.append({"date": _as_date(order["closed_at"]), "mileage": end_mileage, "source": "Zaduženje"})

    readings = [reading for reading in readings if reading["date"]]
    readings.sort(key=lambda reading: (reading["date"], reading["mileage"]))
    return readings, invalid_fuel_count


def _estimate_period_mileage(vehicle, period_start_date, period_end_date):
    readings, invalid_fuel_count = _mileage_readings(vehicle)
    period_days = max((period_end_date - period_start_date).days, 1)

    def no_data(issue):
        if invalid_fuel_count:
            issue += " Točenja sa kilometražom 0 su ignorisana."
        return {
            "km": 0,
            "source": "Nema podatka",
            "issue": issue,
            "requires_driver_warning": True,
            "observed_days": 0,
            "period_days": period_days,
            "start_reading": None,
            "end_reading": None,
        }

    if len(readings) < 2:
        return no_data("Nema dva validna očitavanja kilometraže iz točenja ili zaduženja.")

    best_pair = None
    best_score = None
    for start in readings:
        for end in readings:
            observed_days = (end["date"] - start["date"]).days
            distance = end["mileage"] - start["mileage"]
            if observed_days <= 0 or distance <= 0:
                continue

            score = abs((start["date"] - period_start_date).days) + abs((end["date"] - period_end_date).days)
            if best_score is None or score < best_score:
                best_score = score
                best_pair = (start, end, observed_days, distance)

    if not best_pair:
        return no_data("Nema validan rast kilometraže između dostupnih točenja ili zaduženja.")

    start, end, observed_days, distance = best_pair
    estimated_km = distance / observed_days * period_days
    sources = {start["source"], end["source"]}
    if sources == {"Točenje"}:
        source = "Točenja (okvirno)"
    elif sources == {"Zaduženje"}:
        source = "Zaduženja (okvirno)"
    else:
        source = "Točenja/zaduženja (okvirno)"

    issue_parts = [
        "Okvirno: kilometraža je preračunata iz najbližih validnih očitavanja "
        f"({start['date']:%d.%m.%Y} - {end['date']:%d.%m.%Y}, {observed_days} dana)."
    ]
    if invalid_fuel_count:
        issue_parts.append("Točenja sa kilometražom 0 su ignorisana.")

    return {
        "km": estimated_km,
        "source": source,
        "issue": " ".join(issue_parts),
        "requires_driver_warning": False,
        "observed_days": observed_days,
        "period_days": period_days,
        "start_reading": start,
        "end_reading": end,
    }


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
        category__in=[Vehicle.Category.PASSENGER, Vehicle.Category.CARGO],
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
        financial_lease_interest_period=Subquery(
            LeaseInterest.objects.filter(
                lease__vehicle=OuterRef('pk'),
                lease__lease_type='finansijski',
                lease__end_date__gte=period_start_date,
                year__in=range(period_start_date.year, period_end_date.year + 1),
            )
            .values('lease__vehicle')
            .annotate(total=Sum('interest_amount'))
            .values('total')[:1]
        ),
    )

    period_days = (period_end_date - period_start_date).days or 1

    def monthly_cost_for_overlap(monthly_amount, overlap_start, overlap_end):
        if overlap_end <= overlap_start:
            return 0.0

        total = 0.0
        cursor = overlap_start
        while cursor < overlap_end:
            month_last_day = calendar.monthrange(cursor.year, cursor.month)[1]
            month_end = date(cursor.year, cursor.month, month_last_day) + timedelta(days=1)
            segment_end = min(month_end, overlap_end)
            days_in_segment = (segment_end - cursor).days
            if days_in_segment > 0:
                total += float(monthly_amount or 0) * days_in_segment / month_last_day
            cursor = segment_end
        return total

    # Dugorocni najam: current_payment_amount je mesecna rata.
    # Operativni lizing: zadrzavamo postojecu proporcionalnu raspodelu.
    # Finansijski lizing: i dalje ulazi kroz LeaseInterest.
    vehicle_ids_in_query = list(vehicles.values_list('pk', flat=True))
    lease_contracts = Lease.objects.filter(
        vehicle_id__in=vehicle_ids_in_query,
        start_date__lte=period_end_date,
        end_date__gte=period_start_date,
    ).exclude(lease_type='finansijski').values(
        'vehicle_id', 'lease_type', 'current_payment_amount', 'start_date', 'end_date'
    )

    non_financial_lease_cost_by_vehicle = defaultdict(float)
    for lease in lease_contracts:
        overlap_start = max(lease['start_date'], period_start_date)
        overlap_end = min(lease['end_date'], period_end_date)
        if overlap_end <= overlap_start:
            continue

        if lease['lease_type'] in LONG_TERM_LEASE_TYPES:
            # Pretvaramo u ekskluzivni kraj samo za obracun mesecne rate najma.
            cost = monthly_cost_for_overlap(lease['current_payment_amount'], overlap_start, overlap_end + timedelta(days=1))
            non_financial_lease_cost_by_vehicle[lease['vehicle_id']] += cost
            continue

        total_lease_days = (lease['end_date'] - lease['start_date']).days or 1
        overlap_days = (overlap_end - overlap_start).days
        if overlap_days <= 0:
            continue
        cost = float(lease['current_payment_amount'] or 0) * overlap_days / total_lease_days
        non_financial_lease_cost_by_vehicle[lease['vehicle_id']] += cost

    rows = []
    for vehicle in vehicles:
        mileage_estimate = _estimate_period_mileage(vehicle, period_start_date, period_end_date)
        annual_km = mileage_estimate["km"]
        mileage_source = mileage_estimate["source"]
        mileage_issue = mileage_estimate["issue"]
        requires_driver_warning = mileage_estimate["requires_driver_warning"]

        fuel_cost = number(vehicle.fuel_cost_period)
        service_cost = number(vehicle.service_cost_period)
        requisition_cost = number(vehicle.requisition_cost_period)
        policy_cost = number(vehicle.policy_cost_period)
        # Operativni/dugorocni: current_payment_amount raspodeljeno proporcionalno na preklapajuce dane
        # Finansijski: koristimo kamatu iz LeaseInterest (principal je vec u amortizaciji)
        lease_annual_cost = (
            non_financial_lease_cost_by_vehicle.get(vehicle.pk, 0)
            + number(vehicle.financial_lease_interest_period)
        )
        insurance_recovery = number(vehicle.insurance_recovery_period)

        depreciation_base_date = vehicle.purchase_date or vehicle.first_registration_date
        annual_depreciation = 0
        if vehicle.purchase_value and vehicle.value is not None and depreciation_base_date:
            days_in_use = max((period_end_date - depreciation_base_date).days, 365)
            total_depreciation = max(number(vehicle.purchase_value) - number(vehicle.value), 0)
            annual_depreciation = total_depreciation / days_in_use * period_days

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

        # Napomena za automobile koji se malo voze (ispod 15000 km godišnje)
        low_mileage_threshold = 15000
        below_mileage_threshold = annual_km < low_mileage_threshold if annual_km > 0 else False
        low_mileage_note = (
            f"Vozilo se malo vozi ({annual_km}km < {low_mileage_threshold}km godišnje). "
            "Cena po km može biti iskrivljena jer se fiksni troškovi (osiguranje, doprinosi) "
            "raspoređuju na manju kilometražu." if below_mileage_threshold else None
        )

        rows.append({
            'label': vehicle.registration_number or str(vehicle),
            'vehicle_id': vehicle.id,
            'brand': vehicle.brand,
            'model': vehicle.model,
            'category': vehicle.get_category_display(),
            'center': vehicle.center_code or 'Bez centra',
            'annual_km': annual_km,
            'mileage_source': mileage_source,
            'mileage_issue': mileage_issue,
            'requires_driver_warning': requires_driver_warning,
            'mileage_observed_days': mileage_estimate["observed_days"],
            'mileage_period_days': mileage_estimate["period_days"],
            'mileage_start_reading': mileage_estimate["start_reading"],
            'mileage_end_reading': mileage_estimate["end_reading"],
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
            'below_mileage_threshold': below_mileage_threshold,
            'low_mileage_note': low_mileage_note,
            'maximum_permissible_weight': float(vehicle.maximum_permissible_weight or 0),
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
            vehicle_threshold = fixed_cost_per_km_threshold(row.get('maximum_permissible_weight', 0))
            row['status'] = cost_per_km_status(row['cost_per_km'], vehicle_threshold)
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
