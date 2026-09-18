"""Read-only monthly job analysis. Never executes source business procedures."""
from datetime import timedelta
from urllib.parse import urlencode

from django.db.models import Count, F, Max, Min, Q, Sum
from django.db.models.functions import Substr
from django.urls import reverse

from fleet.models import JobCode, TrafficCard
from .reports import CLOSING_POSTINGS, summary


INVOICE_ACCOUNTS = ("20400", "20500")
INTERNAL_INVOICE_ACCOUNTS = ("61420", "61421", "61521", "64002")


def monthly_expenses(entries, start, end, job_code):
    """Input must already be restricted to the authorized company and job."""
    period = entries.filter(booking_date__range=(start, end))
    totals = summary(period)
    expenses = list(period.exclude(CLOSING_POSTINGS).filter(account__startswith="5")
                    .order_by().annotate(knt3=Substr("account", 1, 3)).values("knt3")
                    .annotate(amount=Sum(F("debit") - F("credit")), count=Count("pk"))
                    .order_by("knt3"))
    for row in expenses:
        row["share"] = row["amount"] * 100 / totals["expense"] if totals["expense"] else None
        row["url"] = reverse("finansije:ledger") + "?" + urlencode({
            "job": job_code, "date_from": start.isoformat(), "date_to": end.isoformat(),
            "account": row["knt3"], "kind": "expense",
        })
    return expenses


def monthly_invoices(entries, start, end, *, internal=False):
    # Issued documents are selected by document date, not booking date.
    # Sum only the agreed accounts, preserving corrections and the authorized job scope.
    journal_type = "ON" if internal else "IF"
    accounts = INTERNAL_INVOICE_ACCOUNTS if internal else INVOICE_ACCOUNTS
    amount = F("credit") - F("debit") if internal else F("debit") - F("credit")
    invoices = list(entries.filter(journal_type=journal_type, account__in=accounts,
                                  year=start.year, document_date__range=(start, end))
                    .order_by().values("year", "journal_number", "document_reference",
                                      "partner_group", "partner_code")
                    .annotate(partner_name=Max("partner_name"), date=Min("document_date"),
                              last_date=Max("document_date"), amount=Sum(amount))
                    .order_by("date", "year", "journal_number", "document_reference"))
    return invoices


def assigned_vehicles(job_code, start, end):
    """A dated assignment lasts until the next assignment, including to another job."""
    candidate_ids = JobCode.objects.filter(organizational_unit__code=job_code,
                                           assigned_date__lte=end, vehicle__isnull=False).values("vehicle_id")
    history = JobCode.objects.filter(vehicle_id__in=candidate_ids).select_related(
        "vehicle", "organizational_unit").order_by("vehicle_id", "assigned_date", "pk")
    by_vehicle = {}
    for assignment in history:
        by_vehicle.setdefault(assignment.vehicle_id, []).append(assignment)
    plates = {}
    for card in TrafficCard.objects.filter(vehicle_id__in=candidate_ids, issue_date__lte=end).order_by("issue_date", "pk"):
        plates[card.vehicle_id] = card.registration_number
    result = []
    for vehicle_id, assignments in by_vehicle.items():
        for index, assignment in enumerate(assignments):
            until = assignments[index + 1].assigned_date - timedelta(days=1) if index + 1 < len(assignments) else None
            if (assignment.organizational_unit is None or assignment.organizational_unit.code != job_code
                    or assignment.assigned_date > end or (until is not None and until < start)):
                continue
            vehicle = assignment.vehicle
            result.append({"vehicle_id": vehicle_id, "plate": plates.get(vehicle_id, vehicle.chassis_number),
                           "name": f"{vehicle.brand} {vehicle.model}", "assigned": assignment.assigned_date,
                           "from": max(start, assignment.assigned_date), "to": min(end, until) if until else end})
    return result


def vehicle_custody(request, job_code, start, end):
    """Intersect custody dates with historical job assignments, never today's job."""
    from fleet.views.vehicle_travel_orders import _vehicle_travel_order_base_qs

    assignments = assigned_vehicles(job_code, start, end)
    by_vehicle = {}
    for assignment in assignments:
        by_vehicle.setdefault(assignment["vehicle_id"], []).append(assignment)
    orders = _vehicle_travel_order_base_qs(request).filter(
        vehicle_id__in=by_vehicle, created_at__lte=end,
    ).filter(Q(closed_at__isnull=True) | Q(closed_at__gte=start)).order_by("created_at", "pk")
    rows = []
    for order in orders:
        for assignment in by_vehicle[order.vehicle_id]:
            overlap_from = max(assignment["from"], order.created_at)
            overlap_to = min(assignment["to"], order.closed_at or end)
            if overlap_from <= overlap_to:
                rows.append({**assignment, "order": order, "from": overlap_from, "to": overlap_to})
    return rows
