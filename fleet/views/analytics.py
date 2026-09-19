from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.mixins import role_permission_required
from fleet.forms.economics import (FleetAnalysisForm, AnalysisProfileForm, ChargePeriodForm,
    DowntimeForm, OrderJobForm, AssessmentForm, ScenarioFormSet)
from fleet.models import (VehicleAnalysisProfile, LeaseChargePeriod, VehicleDowntime,
    VehicleTravelOrder, VehicleEconomicAssessment)
from fleet.services.economics import (VERSION, METHODOLOGY, visible_vehicles, period_analysis,
    fleet_summary, compare_scenarios)


def _lookup_id(value):
    """Kljuc iz adrese; nebrojcana vrednost daje 404 umesto greske 500."""
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise Http404('Neispravan identifikator u adresi.')


def default_period():
    today = timezone.localdate()
    index = today.year * 12 + today.month - 1 - 11
    return today.replace(year=index // 12, month=index % 12 + 1, day=1), today


@login_required
@require_http_methods(['GET'])
def analysis_methodology(request):
    """Jedna stranica metodologije, umesto istog bloka na pet ekrana."""
    return render(request, 'fleet/analysis_methodology.html',
                  dict(methodology=METHODOLOGY, methodology_version=VERSION))


@login_required
@role_permission_required('fleet_analytics')
@require_http_methods(['GET'])
def fleet_analytics(request):
    return render_fleet_analysis(request)


def render_fleet_analysis(request, center_code=None):
    start, end = default_period()
    form = FleetAnalysisForm(request.GET if request.GET else None,
        initial={'start': start, 'end': end, 'center': center_code or ''})
    if center_code is not None:
        form.fields['center'].disabled = True
    valid = not form.is_bound or form.is_valid()
    rows = []
    if valid:
        data = form.cleaned_data if form.is_bound else {}
        start, end = data.get('start', start), data.get('end', end)
        vehicles = visible_vehicles(request.user, include_retired=data.get('include_retired', False))
        selected_center = center_code or data.get('center')
        if selected_center:
            from django.db.models import OuterRef, Subquery
            from fleet.models import JobCode
            assignment = JobCode.objects.filter(vehicle_id=OuterRef('pk'), assigned_date__lte=end).order_by('-assigned_date', '-pk')
            vehicles = vehicles.annotate(period_center=Subquery(assignment.values('organizational_unit__center')[:1])).filter(period_center=selected_center)
        rows = period_analysis(vehicles, start, end)
        purpose = data.get('purpose')
        if purpose:
            rows = [r for r in rows if (r['profile'].purpose if r['profile'] else 'unknown') == purpose]
        if data.get('basis'):
            rows = [r for r in rows if data['basis'] in r['basis_codes']]
    groups = defaultdict(list)
    monthly = {}
    for row in rows:
        groups[(row['purpose'], row['basis'])].append(row)
        for month in row['monthly']:
            key = month['month']
            monthly.setdefault(key, None)
            if month['included'] is not None:
                monthly[key] = (monthly[key] or Decimal(0)) + month['included']
    return render(request, 'fleet/analytics.html', dict(period_form=form, period_valid=valid,
        period_start=start, period_end=end, rows=rows, summary=fleet_summary(rows),
        groups=[dict(purpose=k[0], basis=k[1], summary=fleet_summary(v)) for k, v in groups.items()],
        monthly=[dict(month=k, total=v) for k, v in sorted(monthly.items())],
        methodology=METHODOLOGY, methodology_version=VERSION, center_code=center_code))


@login_required
@role_permission_required('vehicle_analysis_settings')
@require_http_methods(['GET', 'POST'])
def vehicle_analysis_settings(request, pk):
    vehicle = get_object_or_404(visible_vehicles(request.user, include_retired=True), pk=pk)
    action = request.POST.get('action') if request.method == 'POST' else None
    profile = VehicleAnalysisProfile(vehicle=vehicle)
    downtime_id = _lookup_id(request.POST.get('downtime_id') if action == 'downtime' else request.GET.get('downtime'))
    downtime = get_object_or_404(VehicleDowntime, pk=downtime_id, vehicle=vehicle) if downtime_id else VehicleDowntime(vehicle=vehicle)
    charge_id = _lookup_id(request.POST.get('charge_id') if action == 'charge' else request.GET.get('charge'))
    charge = get_object_or_404(LeaseChargePeriod, pk=charge_id, lease__vehicle=vehicle) if charge_id else LeaseChargePeriod()
    order_id = _lookup_id(request.POST.get('order_id') if action == 'job' else request.GET.get('order'))
    order = get_object_or_404(VehicleTravelOrder, pk=order_id, vehicle=vehicle) if order_id else None
    forms = {
        'profile': AnalysisProfileForm(request.POST if action == 'profile' else None, instance=profile, prefix='profile'),
        'charge': ChargePeriodForm(request.POST if action == 'charge' else None, instance=charge, vehicle=vehicle, prefix='charge'),
        'downtime': DowntimeForm(request.POST if action == 'downtime' else None, instance=downtime, vehicle=vehicle, prefix='downtime'),
    }
    if order:
        forms['job'] = OrderJobForm(request.POST if action == 'job' else None, instance=order, user=request.user, prefix='job')
    if action in forms and forms[action].is_valid():
        forms[action].save()
        messages.success(request, 'Evidencija za analitiku je sačuvana.')
        return redirect('vehicle_analysis_settings', pk=pk)
    if action and action not in forms:
        messages.error(request, 'Izaberite postojeći nalog ili ispravnu vrstu evidencije.')
    # Spisak „sta jos nedostaje“ stoji uz polja koja ga popunjavaju, a ne na
    # ekranu za citanje troskova. Racuna se za podrazumevani period, pa se taj
    # period i ispisuje, da spisak ne bi delovao kao da vazi za svaki period.
    readiness_start, readiness_end = default_period()
    readiness = period_analysis([vehicle], readiness_start, readiness_end)[0]

    return render(request, 'fleet/analysis_settings.html', dict(vehicle=vehicle,
        economics=readiness, period_start=readiness_start, period_end=readiness_end,
        can_edit_analysis=True,
        profile_form=forms['profile'], charge_form=forms['charge'], downtime_form=forms['downtime'],
        job_form=forms.get('job'), selected_order=order, selected_downtime=downtime, selected_charge=charge,
        profiles=VehicleAnalysisProfile.objects.filter(vehicle=vehicle),
        charges=LeaseChargePeriod.objects.filter(lease__vehicle=vehicle).select_related('lease'),
        downtimes=VehicleDowntime.objects.filter(vehicle=vehicle),
        orders=VehicleTravelOrder.objects.filter(vehicle=vehicle).select_related('job_code').order_by('-created_at', '-pk'),
        methodology=METHODOLOGY, methodology_version=VERSION))


@login_required
@role_permission_required('vehicle_assessment_create')
@require_http_methods(['GET', 'POST'])
def vehicle_assessment_create(request, pk):
    vehicle = get_object_or_404(visible_vehicles(request.user, include_retired=True), pk=pk)
    assessment = VehicleEconomicAssessment(vehicle=vehicle, created_by=request.user, methodology_version=VERSION)
    form = AssessmentForm(request.POST or None, instance=assessment)
    scenarios = ScenarioFormSet(request.POST or None, instance=assessment, prefix='scenarios')
    if request.method == 'POST':
        valid_form = form.is_valid()
        valid_scenarios = scenarios.is_valid()
        if valid_form and valid_scenarios:
            with transaction.atomic():
                assessment = form.save(commit=False)
                scenario_instances = scenarios.save(commit=False)
                assessment.snapshot = compare_scenarios(assessment, scenario_instances)
                assessment.save()
                for item in scenario_instances:
                    item.assessment = assessment
                    item.full_clean()
                    item.save()
            return redirect('vehicle_assessment_detail', pk=assessment.pk)
    return render(request, 'fleet/assessment_form.html', dict(vehicle=vehicle, form=form, scenarios=scenarios,
        methodology=METHODOLOGY, methodology_version=VERSION))


@login_required
@role_permission_required('vehicle_assessment_detail')
@require_http_methods(['GET'])
def vehicle_assessment_detail(request, pk):
    assessment = get_object_or_404(VehicleEconomicAssessment.objects.select_related('vehicle', 'created_by'),
        pk=pk, vehicle__in=visible_vehicles(request.user, include_retired=True))
    return render(request, 'fleet/assessment_detail.html', dict(assessment=assessment,
        vehicle=assessment.vehicle, snapshot=assessment.snapshot,
        methodology=assessment.snapshot.get('methodology', METHODOLOGY), methodology_version=assessment.methodology_version))
