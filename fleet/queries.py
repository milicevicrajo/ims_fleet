# reports/queries.py
from django.db.models import F, Value, CharField, Case, When, Sum, OuterRef, Subquery
from django.db.models.functions import ExtractYear, ExtractMonth
from .models import Policy, JobCode  # prilagodi import ako treba

# "Važeći" JobCode na dan izdavanja polise
_latest_jc = JobCode.objects.filter(
    vehicle=OuterRef('vehicle'),
    assigned_date__lte=OuterRef('issue_date'),
).order_by('-assigned_date')

def policies_monthly_costs_qs(base_qs=None):
    qs = (base_qs or Policy.objects).annotate(
        year=ExtractYear('issue_date'),
        month=ExtractMonth('issue_date'),

        # OJ važeća na dan izdavanja
        oj_id=Subquery(_latest_jc.values('organizational_unit_id')[:1]),
        oj_name=Subquery(
            _latest_jc.annotate(naziv=F('organizational_unit__name')).values('naziv')[:1]
        ),

        # >>> OVDE JE KLJUČNA IZMJENA <<<
        job_code=Subquery(_latest_jc.values('organizational_unit__code')[:1]),
        center=Subquery(_latest_jc.values('organizational_unit__center')[:1]),

        vrsta=Case(
            When(insurance_type__iexact='kasko', then=Value('kasko')),
            When(insurance_type__iexact='autoodgovornost', then=Value('autoodgovornost')),
            default=F('insurance_type'),
            output_field=CharField(),
        ),
    ).values(
        'year', 'month', 'center', 'oj_id', 'oj_name', 'job_code', 'vrsta'
    ).annotate(
        iznos=Sum('premium_amount')
    ).order_by(
        'year', 'month', 'center', 'oj_id', 'job_code', 'vrsta'
    )
    return qs
