from decimal import Decimal

from django.db.models import CharField, DecimalField, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Cast, Coalesce, ExtractMonth, ExtractYear

from .models import JobCode, ServiceTransaction


def _service_base_qs():
    latest_jc = JobCode.objects.filter(
        vehicle_id=OuterRef("vehicle_id"),
        assigned_date__lte=OuterRef("datum"),
    ).order_by("-assigned_date", "-pk")

    oj_code_sq = latest_jc.values("organizational_unit__code")[:1]
    center_code_sq = latest_jc.values("organizational_unit__center")[:1]

    return (
        ServiceTransaction.objects.annotate(
            service_year=ExtractYear("datum"),
            service_month=ExtractMonth("datum"),
            raw_oj_code=Subquery(oj_code_sq),
            raw_center_code=Subquery(center_code_sq),
        ).annotate(
            oj_code_txt_calc=Coalesce(Cast("raw_oj_code", CharField()), Value("")),
            center_code_txt_calc=Coalesce(Cast("raw_center_code", CharField()), Value("")),
        )
    )


def service_monthly_costs_rows(request):
    qs = _service_base_qs()
    dec_out = DecimalField(max_digits=18, decimal_places=2)

    aggregated = qs.values(
        "service_year", "service_month", "oj_code_txt_calc", "center_code_txt_calc"
    ).annotate(
        iznos=Coalesce(
            Sum("potrazuje", output_field=dec_out),
            Value(Decimal("0.00")),
            output_field=dec_out,
        )
    )

    return (
        aggregated.values(
            year=F("service_year"),
            month=F("service_month"),
            oj_code_txt=F("oj_code_txt_calc"),
            center_code_txt=F("center_code_txt_calc"),
            iznos=F("iznos"),
        ).order_by("-year", "-month", "center_code_txt", "oj_code_txt")
    )
