from django.db.models import OuterRef, Subquery, Sum
from django.db.models.functions import TruncMonth, TruncYear

from ..models import FuelConsumption, JobCode, Lease, ServiceTransaction, Vehicle


def lease_monthly_costs_rows(request):
    latest_center_subq = JobCode.objects.filter(vehicle=OuterRef("vehicle")).order_by("-assigned_date").values("organizational_unit__center")[:1]
    latest_oj_id_subq = JobCode.objects.filter(vehicle=OuterRef("vehicle")).order_by("-assigned_date").values("organizational_unit__id")[:1]
    latest_oj_name_subq = JobCode.objects.filter(vehicle=OuterRef("vehicle")).order_by("-assigned_date").values("organizational_unit__name")[:1]

    leases_agg = Lease.objects.annotate(
        year=TruncYear("start_date"),
        month=TruncMonth("start_date"),
        center=Subquery(latest_center_subq),
        oj_id=Subquery(latest_oj_id_subq),
        oj_name=Subquery(latest_oj_name_subq),
    ).values(
        "year", "month", "center", "oj_id", "oj_name", "job_code", "lease_type"
    ).annotate(
        total_lease_amount=Sum("current_payment_amount")
    )

    year = request.GET.get("year")
    month = request.GET.get("month")
    center = request.GET.get("center")
    oj_id_filter = request.GET.get("oj")
    lease_type = request.GET.get("vrsta")

    if year:
        leases_agg = [r for r in leases_agg if r["year"] and r["year"].year == int(year)]
    if month:
        leases_agg = [r for r in leases_agg if r["month"] and r["month"].month == int(month)]
    if center:
        leases_agg = [r for r in leases_agg if (r.get("center") or "") == center]
    if oj_id_filter:
        leases_agg = [r for r in leases_agg if str(r.get("oj_id") or "") == str(oj_id_filter)]
    if lease_type:
        leases_agg = [r for r in leases_agg if (r.get("lease_type") or "").lower() == lease_type.lower()]

    rows = []
    latest_ou_for_vehicle = JobCode.objects.filter(vehicle=OuterRef("pk")).order_by("-assigned_date").values("organizational_unit__id")[:1]

    for r in leases_agg:
        y = r["year"].year if r["year"] else None
        m = r["month"].month if r["month"] else None
        oj_id = r.get("oj_id")

        if oj_id:
            vehicle_ids = list(
                Vehicle.objects.annotate(
                    latest_ou_id=Subquery(latest_ou_for_vehicle)
                ).filter(latest_ou_id=oj_id).values_list("pk", flat=True)
            )
        else:
            vehicle_ids = []

        num_vehicles = len(vehicle_ids)
        service_sum = 0
        fuel_sum = 0
        if num_vehicles and y and m:
            service_sum = ServiceTransaction.objects.filter(
                vehicle_id__in=vehicle_ids,
                datum__year=y,
                datum__month=m,
            ).aggregate(total=Sum("potrazuje"))["total"] or 0

            fuel_sum = FuelConsumption.objects.filter(
                vehicle_id__in=vehicle_ids,
                date__year=y,
                date__month=m,
            ).aggregate(total=Sum("cost_bruto"))["total"] or 0

        accompanying_total = (service_sum or 0) + (fuel_sum or 0)
        accompanying_per_vehicle = (accompanying_total / num_vehicles) if num_vehicles else None

        rows.append(
            {
                "year": y,
                "month": m,
                "center": r.get("center"),
                "oj_id": oj_id,
                "oj_name": r.get("oj_name"),
                "job_code": r.get("job_code"),
                "lease_type": r.get("lease_type"),
                "lease_amount": r.get("total_lease_amount") or 0,
                "accompanying_total": accompanying_total,
                "accompanying_per_vehicle": accompanying_per_vehicle,
                "vehicle_count": num_vehicles,
            }
        )

    return sorted(rows, key=lambda x: (x["year"] or 0, x["month"] or 0, x.get("center") or "", x.get("oj_id") or ""))
