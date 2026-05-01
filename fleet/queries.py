from decimal import Decimal

from django.db import connections
from django.db.models import Case, CharField, DecimalField, F, OuterRef, Subquery, Sum, Value, When
from django.db.models.functions import Cast, Coalesce, ExtractMonth, ExtractYear, TruncMonth, TruncYear

from .models import FuelConsumption, JobCode, Lease, Policy, ServiceTransaction, Vehicle


def get_data_from_secondary_db(query, db_alias, params=None):
    """
    Izvršava SQL upit na drugoj bazi i vraća rezultat kao listu rečnika.
    """
    with connections[db_alias].cursor() as cursor:
        cursor.execute(query, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _append_report_filters(query, filters):
    if filters:
        return query + " " + " ".join(filters)
    return query


def report_period_filtered_query(query, form, cast_params=False):
    filters = []
    params = []

    if form.is_valid():
        for field_name, condition in (
            ("godina", "AND godina = %s"),
            ("mesec", "AND mesec = %s"),
            ("polovina", "AND polovina = %s"),
        ):
            value = form.cleaned_data.get(field_name)
            if value:
                filters.append(condition)
                params.append(int(value) if cast_params else value)

    return _append_report_filters(query, filters), params


def date_period_filtered_query(query, form, cast_params=False):
    filters = []
    params = []

    if form.is_valid():
        godina = form.cleaned_data.get('godina')
        mesec = form.cleaned_data.get('mesec')
        polovina = form.cleaned_data.get('polovina')

        if godina:
            filters.append("AND YEAR(datum) = %s")
            params.append(int(godina) if cast_params else godina)

        if mesec:
            filters.append("AND MONTH(datum) = %s")
            params.append(int(mesec) if cast_params else mesec)

        if polovina:
            polovina_value = int(polovina)
            if polovina_value == 1:
                filters.append("AND DAY(datum) <= 15")
            elif polovina_value == 2:
                filters.append("AND DAY(datum) > 15")

    return _append_report_filters(query, filters), params


# "Važeći" JobCode na dan izdavanja polise
_latest_jc = JobCode.objects.filter(
    vehicle=OuterRef('vehicle'),
    assigned_date__lte=OuterRef('issue_date'),
).order_by('-assigned_date')

def policies_monthly_costs_qs(base_qs=None):
    qs = (base_qs or Policy.objects).annotate(
        year=ExtractYear('issue_date'),
        month=ExtractMonth('issue_date'),

        # OJ vaÅ¾eÄ‡a na dan izdavanja
        oj_id=Subquery(_latest_jc.values('organizational_unit_id')[:1]),
        oj_name=Subquery(
            _latest_jc.annotate(naziv=F('organizational_unit__name')).values('naziv')[:1]
        ),

        # >>> OVDE JE KLJUÄŒNA IZMJENA <<<
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

def _filtered_qs(request):
    qs = policies_monthly_costs_qs()

    # SVI filteri su opcioni â€” ako ih nema, dobiÄ‡eÅ¡ SVE GODINE
    year = request.GET.get('year')
    month = request.GET.get('month')
    center = request.GET.get('center')
    oj_id = request.GET.get('oj')
    vrsta = request.GET.get('vrsta')

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

    # po Å¾elji: stabilan redosled
    return qs.order_by('year', 'month', 'center', 'oj_id', 'job_code', 'vrsta')



def lease_monthly_costs_rows(request):
    """
    Grupa lizinga po godini/mesecu/centar/oj/job_code/vrsti i raÄuna prateÄ‡e troÅ¡kove
    (servisi + gorivo) za vozila koja su u toj organizacionoj jedinici u tom trenutku.
    """
    # Subqueryi za poslednju OU za vozilo
    latest_center_subq = JobCode.objects.filter(vehicle=OuterRef('vehicle')).order_by('-assigned_date').values('organizational_unit__center')[:1]
    latest_oj_id_subq = JobCode.objects.filter(vehicle=OuterRef('vehicle')).order_by('-assigned_date').values('organizational_unit__id')[:1]
    latest_oj_name_subq = JobCode.objects.filter(vehicle=OuterRef('vehicle')).order_by('-assigned_date').values('organizational_unit__name')[:1]

    # Agregacija lizinga po datumu poÄetka (year/month) i OU
    leases_agg = Lease.objects.annotate(
        year=TruncYear('start_date'),
        month=TruncMonth('start_date'),
        center=Subquery(latest_center_subq),
        oj_id=Subquery(latest_oj_id_subq),
        oj_name=Subquery(latest_oj_name_subq),
    ).values(
        'year','month','center','oj_id','oj_name','job_code','lease_type'
    ).annotate(
        total_lease_amount=Sum('current_payment_amount')
    )

    # primeni GET filtere (opcionalno)
    year = request.GET.get('year')
    month = request.GET.get('month')
    center = request.GET.get('center')
    oj_id_filter = request.GET.get('oj')
    lease_type = request.GET.get('vrsta')  # oÄekuje 'finansijski'|'operativni'|'dugorocni'

    if year:
        leases_agg = [r for r in leases_agg if r['year'] and r['year'].year == int(year)]
    if month:
        leases_agg = [r for r in leases_agg if r['month'] and r['month'].month == int(month)]
    if center:
        leases_agg = [r for r in leases_agg if (r.get('center') or '') == center]
    if oj_id_filter:
        leases_agg = [r for r in leases_agg if str(r.get('oj_id') or '') == str(oj_id_filter)]
    if lease_type:
        leases_agg = [r for r in leases_agg if (r.get('lease_type') or '').lower() == lease_type.lower()]

    rows = []
    # subquery za poslednju OU kod Vehicle (koristi se za pronalazak vozila u OU)
    latest_ou_for_vehicle = JobCode.objects.filter(vehicle=OuterRef('pk')).order_by('-assigned_date').values('organizational_unit__id')[:1]

    for r in leases_agg:
        # izvuci year/month kao int
        y = r['year'].year if r['year'] else None
        m = r['month'].month if r['month'] else None
        oj_id = r.get('oj_id')

        # nađ vozila koja trenutno pripadaju toj OU (ako postoji oj_id)
        if oj_id:
            vehicle_ids = list(Vehicle.objects.annotate(
                latest_ou_id=Subquery(latest_ou_for_vehicle)
            ).filter(latest_ou_id=oj_id).values_list('pk', flat=True))
        else:
            vehicle_ids = []

        num_vehicles = len(vehicle_ids)

        # prateci troskovi = servisi + gorivo za te vehicle_ids i za dati year/month
        service_sum = 0
        fuel_sum = 0
        if num_vehicles and y and m:
            service_sum = ServiceTransaction.objects.filter(
                vehicle_id__in=vehicle_ids,
                datum__year=y,
                datum__month=m
            ).aggregate(total=Sum('potrazuje'))['total'] or 0

            fuel_sum = FuelConsumption.objects.filter(
                vehicle_id__in=vehicle_ids,
                date__year=y,
                date__month=m
            ).aggregate(total=Sum('cost_bruto'))['total'] or 0

        accompanying_total = (service_sum or 0) + (fuel_sum or 0)
        accompanying_per_vehicle = (accompanying_total / num_vehicles) if num_vehicles else None

        rows.append({
            'year': y,
            'month': m,
            'center': r.get('center'),
            'oj_id': oj_id,
            'oj_name': r.get('oj_name'),
            'job_code': r.get('job_code'),
            'lease_type': r.get('lease_type'),
            'lease_amount': r.get('total_lease_amount') or 0,
            'accompanying_total': accompanying_total,
            'accompanying_per_vehicle': accompanying_per_vehicle,
            'vehicle_count': num_vehicles,
        })

    # opcionalno sortiranje
    rows = sorted(rows, key=lambda x: (x['year'] or 0, x['month'] or 0, x.get('center') or '', x.get('oj_id') or ''))
    return rows

def _service_base_qs():
    """
    Osnovni QS za servise, anotira: year, month, oj_code, center_code (+ txt).
    OJ i centar se određuju po stanju na datum servisa (<= datum).
    """
    latest_jc = JobCode.objects.filter(
        vehicle_id=OuterRef('vehicle_id'),
        assigned_date__lte=OuterRef('datum'),
    ).order_by('-assigned_date', '-pk')

    oj_code_sq     = latest_jc.values('organizational_unit__code')[:1]
    center_code_sq = latest_jc.values('organizational_unit__center')[:1]

    return (
        ServiceTransaction.objects
        .annotate(
            service_year=ExtractYear('datum'),
            service_month=ExtractMonth('datum'),
            raw_oj_code=Subquery(oj_code_sq),
            raw_center_code=Subquery(center_code_sq),
        )
        .annotate(
            oj_code_txt_calc=Coalesce(Cast('raw_oj_code', CharField()), Value('')),
            center_code_txt_calc=Coalesce(Cast('raw_center_code', CharField()), Value('')),
        )
    )

def service_monthly_costs_rows(request):
    """
    Vraća agregirane redove: year, month, oj_code_txt, center_code_txt, iznos
    (iznos = sum(potrazuje) kao Decimal).
    """
    qs = _service_base_qs()

    dec_out = DecimalField(max_digits=18, decimal_places=2)

    aggregated = (
        qs.values('service_year', 'service_month', 'oj_code_txt_calc', 'center_code_txt_calc')
          .annotate(
              iznos=Coalesce(
                  Sum('potrazuje', output_field=dec_out),
                  Value(Decimal('0.00')),
                  output_field=dec_out,
              )
          )
    )

    return (
        aggregated.values(
            year=F('service_year'),
            month=F('service_month'),
            oj_code_txt=F('oj_code_txt_calc'),
            center_code_txt=F('center_code_txt_calc'),
            iznos=F('iznos'),
        )
        .order_by('-year', '-month', 'center_code_txt', 'oj_code_txt')
    )






