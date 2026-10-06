from datetime import timedelta

from django.db.models import Case, CharField, F, OuterRef, Q, Subquery, Sum, Value, When
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone

from ..models import JobCode, Policy


AUTOODGOVORNOST = Q(insurance_type__icontains="autoodgovornost")


def ao_polisa(vehicle, na_dan):
    """Poslednja polisa autoodgovornosti vozila koja je počela do datuma `na_dan` (po kraju važenja)."""
    return (vehicle.policies.filter(AUTOODGOVORNOST, start_date__lte=na_dan, end_date__isnull=False)
            .order_by("-end_date", "-id").first())


def registracija_vazi_do(na_dan, vehicle_ref="pk"):
    """Subquery: registracija važi dok važi polisa autoodgovornosti (od 06.10.2026.; ručni rok sa
    saobraćajne `TrafficCard.registration_valid_until` se više ne koristi). Kraj poslednje AO polise
    koja je počela do datuma `na_dan`."""
    return Subquery(
        Policy.objects.filter(AUTOODGOVORNOST, vehicle_id=OuterRef(vehicle_ref), start_date__lte=na_dan,
                              end_date__isnull=False)
        .order_by("-end_date", "-id").values("end_date")[:1]
    )


_latest_jc = JobCode.objects.filter(
    vehicle=OuterRef("vehicle"),
    assigned_date__lte=OuterRef("issue_date"),
).order_by("-assigned_date")


def policies_monthly_costs_qs(base_qs=None):
    qs = (base_qs or Policy.objects).annotate(
        year=ExtractYear("issue_date"),
        month=ExtractMonth("issue_date"),
        oj_id=Subquery(_latest_jc.values("organizational_unit_id")[:1]),
        oj_name=Subquery(
            _latest_jc.annotate(naziv=F("organizational_unit__name")).values("naziv")[:1]
        ),
        job_code=Subquery(_latest_jc.values("organizational_unit__code")[:1]),
        center=Subquery(_latest_jc.values("organizational_unit__center")[:1]),
        vrsta=Case(
            When(insurance_type__iexact="kasko", then=Value("kasko")),
            When(insurance_type__iexact="autoodgovornost", then=Value("autoodgovornost")),
            default=F("insurance_type"),
            output_field=CharField(),
        ),
    ).values(
        "year", "month", "center", "oj_id", "oj_name", "job_code", "vrsta"
    ).annotate(
        iznos=Sum("premium_amount")
    ).order_by(
        "year", "month", "center", "oj_id", "job_code", "vrsta"
    )
    return qs


def complete_policy_qs(base_qs=None):
    qs = base_qs if base_qs is not None else Policy.objects
    return qs.exclude(Policy.incomplete_q())


def expiring_policy_qs(today=None, days=30, base_qs=None):
    today = today or timezone.localdate()
    end_to = today + timedelta(days=days)
    complete_policies = complete_policy_qs(base_qs)
    newest_policy = complete_policies.filter(
        vehicle=OuterRef("vehicle"),
        insurance_type=OuterRef("insurance_type"),
    ).order_by("-end_date")

    return complete_policies.annotate(
        latest_end_date=Subquery(newest_policy.values("end_date")[:1]),
        latest_is_renewable=Subquery(newest_policy.values("is_renewable")[:1]),
    ).filter(
        end_date__gte=today,
        end_date__lte=end_to,
        end_date=F("latest_end_date"),
        latest_is_renewable=True,
    )


def expired_unrenewed_policy_qs(today=None, base_qs=None):
    today = today or timezone.localdate()
    complete_policies = complete_policy_qs(base_qs)
    newest_policy = complete_policies.filter(
        vehicle=OuterRef("vehicle"),
        insurance_type=OuterRef("insurance_type"),
    ).order_by("-end_date")
    newer_policy_exists = complete_policies.filter(
        vehicle=OuterRef("vehicle"),
        insurance_type=OuterRef("insurance_type"),
        start_date__gt=OuterRef("start_date"),
    )

    return complete_policies.annotate(
        has_newer_policy=Subquery(newer_policy_exists.values("id")[:1]),
        latest_is_renewable=Subquery(newest_policy.values("is_renewable")[:1]),
    ).filter(
        end_date__lt=today,
        has_newer_policy__isnull=True,
        latest_is_renewable=True,
    )


def _filtered_qs(request):
    qs = policies_monthly_costs_qs()

    year = request.GET.get("year")
    month = request.GET.get("month")
    center = request.GET.get("center")
    oj_id = request.GET.get("oj")
    vrsta = request.GET.get("vrsta")

    if year:
        qs = qs.filter(year=year)
    if month:
        qs = qs.filter(month=month)
    if center:
        qs = qs.filter(center=center)
    if oj_id:
        qs = qs.filter(oj_id=oj_id)
    if vrsta:
        qs = qs.filter(vrsta__iexact=vrsta)

    return qs.order_by("year", "month", "center", "oj_id", "job_code", "vrsta")
