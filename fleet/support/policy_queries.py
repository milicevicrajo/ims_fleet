from django.db.models import Case, CharField, F, OuterRef, Subquery, Sum, Value, When
from django.db.models.functions import ExtractMonth, ExtractYear

from ..models import JobCode, Policy


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
