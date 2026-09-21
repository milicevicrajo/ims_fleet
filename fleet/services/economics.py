"""Shared period analysis and reproducible prospective LCC comparisons (RSD)."""
import calendar
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import OuterRef, Subquery, Q
from django.utils import timezone

from fleet.models import (Vehicle, JobCode, FuelConsumption, ServiceTransaction, Requisition,
    Insurance, Policy, VehicleTravelOrder, Lease, LeaseInterest,
    VehicleAnalysisProfile, VehicleEconomicAssessment)
from fleet.support.fuel import get_vehicle_fuel_transaction_rows
from fleet.support.management_reports import allowed_centers
from fleet.support.vehicle_detail import recorded_analytics, date_only
from fleet.support.vehicle_mileage import mileage_readings, nearest_period
from fleet.support.analysis_defaults import estimated_purpose, holding_at
from fleet.support.lease_costs import lease_daily_amount, lease_amount_between

ZERO = Decimal('0')
VERSION = 'IMS-FLOTA-2.1'
PURPOSE_METRICS = {
    'laboratory': 'RSD/km, RSD/dan po nalogu i trošak posla',
    'supervision': 'RSD/dan po nalogu, trajanje zaduženja i RSD/km',
    'management': 'RSD/kalendarskom danu, raspoloživost i RSD/km',
    'transport': 'RSD/nalogu i RSD/km; nalog nije nužno jedna transportna tura',
    'drilling': 'Trošak vozila i mobilizacije; rad mašine zahteva odvojenu evidenciju',
    'towing': 'Trošak prevoza po nalogu i km; prikolica i SPT se procenjuju zasebno',
    'trailer': 'Trošak perioda i dani po nalogu; kilometri nisu kriterijum opravdanosti',
}
METHODOLOGY = [
    ('Obuhvaćeni troškovi', 'Gorivo + servisi + trebovanja + premije za period + potvrđene naknade + kamata za period.',
     'NIS/OMV ili izabrana ranija evidencija; servisne transakcije; trebovanja; polise; ugovori.',
     'Delimičan zbir evidentiranih iznosa. Nije TCO ni dokaz da su svi troškovi obuhvaćeni. Naknade osiguranja prikazuju se odvojeno.'),
    ('Kilometraža perioda', 'Najbliže krajnje − najbliže početno očitanje, bez pada brojača između njih.',
     'Očitavanja NIS/OMV i naloga vozila; ranija evidencija dopunjava datume bez direktnih očitanja; OMV koristi pozitivnu korigovanu kilometražu kada postoji.',
     'Usvajaju se najbliži stvarni datumi, i van izabranog perioda. Kod iste udaljenosti bira se raniji početak i kasniji kraj. Odstupanje datuma označava približan rezultat, bez ekstrapolacije.'),
    ('RSD/km', 'Troškovi izabranog perioda / razlika km između usvojenih očitanja; približno ako datumi odstupaju.',
     'Zajednički obračun troškova i kilometraže.',
     'Poredi se samo sa unetim pragom istog obuhvata. Prekoračenje traži pregled; ne određuje zamenu.'),
    ('Dani po nalogu', 'Broj jedinstvenih kalendarskih dana pokrivenih nalozima unutar perioda.',
     'Datum otvaranja i zatvaranja naloga; otvoren nalog do kraja izabranog perioda.',
     'Administrativno zaduženje, nije dokaz produktivnog rada. Preklopljeni dani se ne sabiraju dvaput.'),
    ('RSD/dan po nalogu', 'Obuhvaćeni troškovi celog perioda / jedinstveni dani po nalogu.',
     'Troškovi perioda i nalozi.',
     'Uključuje uticaj slobodnog kapaciteta. Nije cena radnog dana mašine niti marginalni trošak novog posla.'),
    ('Raspodela na poslove', 'Trošak na datum dokumenta pripada šifri posla na koju se vozilo tada vodi; premije i naknade prate svaki dan važenja.',
     'Istorija dodela šifre posla vozilu (JobCode).',
     'Putni nalozi ne određuju pripadnost troška. Bez dodele za dati dan trošak ostaje neraspoređen. Zbir poslova i neraspoređenog dela jednak je zbiru troškova.'),
    ('Polise i ugovori', 'Premija × dani preklapanja / dani polise. Mesečna naknada / dani konkretnog meseca; ukupna naknada / dani ugovora.',
     'Polise i ugovori o lizingu / najmu sa mesečnim ili ukupnim iznosom.',
     'Oba kraja datuma uključena. Bez ugovora podrazumeva se vlasništvo IMS. Preklopljeni ugovori i nepoznato značenje iznosa zahtevaju proveru. Proveriti da se uključene usluge ne ponove u drugim izvorima.'),
    ('Ekonomska procena', 'PV = početna vrednost + godišnji trošak × zbir 1/(1+r)^t − preostala vrednost/(1+r)^n. EAC = PV / isti zbir.',
     'Sačuvani scenariji sa istim horizontom, obimom rada i realnom diskontnom stopom.',
     'Porede se samo izvodljive alternative. Godišnji izdaci i prodaja su na kraju godine. Stalne današnje cene, RSD; nema automatskog poreskog preračuna. Najniži EAC je predlog u okviru unetih pretpostavki.'),
]


def visible_vehicles(user, include_retired=False):
    # Access follows CURRENT responsibility, independently of the historical filter.
    today = timezone.localdate()
    assignment = JobCode.objects.filter(vehicle_id=OuterRef('pk'), assigned_date__lte=today).order_by('-assigned_date', '-pk')
    qs = Vehicle.objects.annotate(access_center=Subquery(assignment.values('organizational_unit__center')[:1]))
    centers = allowed_centers(user)
    if centers:
        # Vozilo bez ijedne dodele nema centar i ne sme da nestane: tek uneto vozilo
        # jos nije rasporedjeno. Ranija provera je NULL izricito propustala.
        qs = qs.filter(Q(access_center__in=centers) | Q(access_center__isnull=True))
    if not include_retired:
        qs = qs.filter(otpis=False)
    return qs.order_by('brand', 'model', 'pk')


def _days(start, end):
    return (start + timedelta(days=i) for i in range((end - start).days + 1))


def _group(rows):
    result = defaultdict(list)
    for row in rows:
        result[row.vehicle_id].append(row)
    return result


def _active_orders(rows, day):
    """Nalozi koji pokrivaju dan, bez lazne primopredaje.

    Pri predaji vozila zatvoreni nalog dobija closed_at jednak created_at sledeceg
    naloga. Da se taj dan ne bi brojao dvaput, dan primopredaje pripada nalogu koji
    tog dana POCINJE. Nalog zatvoren bez naslednika zadrzava svoj poslednji dan, a
    jednodnevni nalog svoj jedini dan.
    """
    handover = any(row.created_at == day for row in rows)
    active = []
    for row in rows:
        if row.created_at > day:
            continue
        if row.closed_at is not None and row.closed_at < day:
            continue
        if handover and row.closed_at == day and row.created_at != day:
            continue
        active.append(row)
    return active


def _lease_overview(lease, interest_by_year, today):
    start = max(today, lease.start_date)
    remaining_days = max((lease.end_date - start).days + 1, 0)
    financial = lease.lease_type == 'finansijski'
    daily = lease_daily_amount(lease, start) if remaining_days else None
    return dict(lease=lease, type_label=lease.lease_type_label,
        confirmed=lease.payment_basis in ('monthly', 'total'),
        financial=financial, rate_monthly=lease.monthly_amount,
        total_amount=lease.total_amount,
        rate_daily=None if financial else daily, rate_basis=lease.payment_basis,
        remaining_days=remaining_days,
        remaining_months=round(Decimal(remaining_days) / Decimal('30.44'), 1),
        remaining_amount=lease_amount_between(lease, start, lease.end_date) if remaining_days else ZERO,
        interest_current_year=interest_by_year.get((lease.pk, today.year)),
        expired=lease.end_date < today)


def _readiness(profile, conflicting_days, contract_missing,
               distance, unassigned_days, period_days, purpose_note):
    def item(order, label, state, detail, effect, where=None, where_label=None):
        return dict(order=order, label=label, state=state, detail=detail,
                    effect=effect, where=where, where_label=where_label)
    return [
        item(1, 'Poslovna namena vozila', 'ok' if profile else 'estimated',
             profile.get_purpose_display() if profile else purpose_note,
             'Početna procena se može promeniti; ne sprečava obračun evidentiranih troškova.',
             'vehicle_analysis_settings', 'Namena i kriterijumi'),
        item(2, 'Osnov raspolaganja', 'missing' if conflicting_days else 'ok',
             f'Preklopljeni ugovori: {conflicting_days} dana.' if conflicting_days else
             'Važeći lizing / najam; bez ugovora podrazumeva se vlasništvo IMS.',
             'Raspolaganje se izvodi iz datuma ugovora.', 'lease_list', 'Lizing i najam'),
        item(3, 'Naknada ugovora / kamata', 'missing' if contract_missing else 'ok',
             f'Nedostaje iznos, značenje iznosa ili kamata za {contract_missing} dana.' if contract_missing else
             'Podaci dostupni za ugovorni period ili ugovor nije primenljiv.',
             'Mesečni ili ukupni iznos preuzima se sa ugovora; kamata finansijskog lizinga zasebno.',
             'lease_list', 'Lizing i najam'),
        item(4, 'Najbliža očitavanja kilometraže', 'missing' if distance is None else 'ok',
             'Nema dva upotrebljiva očitanja ili brojač opada.' if distance is None else f'{distance:.0f} km.',
             'Potrebno za RSD/km; ne sprečava raspodelu troškova na šifru posla.',
             None, 'Kartica Potrošnja goriva'),
        item(5, 'Šifra posla vozila', 'missing' if unassigned_days == period_days else 'partial' if unassigned_days else 'ok',
             f'Bez dodele: {unassigned_days} dana.' if unassigned_days else 'Dodela postoji za svaki dan perioda.',
             'Trošak prati istoriju dodela vozila, nezavisno od putnih naloga.',
             'jobcode_create', 'Promeni dodelu'),
        item(6, 'Kontrolni prag', 'ok' if profile and (profile.cost_limit_km is not None or profile.cost_limit_day is not None) else 'optional',
             'Prag se unosi po potrebi za potvrđenu namenu i uporediv obuhvat.',
             'Signal za pregled; nije uslov za obračun troškova.',
             'vehicle_analysis_settings', 'Namena i kriterijumi'),
    ]


def period_analysis(vehicles, start, end):
    """Batch-load sources once; identical output is used by fleet and vehicle screens."""
    vehicles = list(vehicles)
    if end < start or (end - start).days > 1096 or end > timezone.localdate():
        raise ValueError('Neispravan period analize.')
    ids = [v.pk for v in vehicles]
    odometers, _ = mileage_readings(ids)
    direct = defaultdict(list)
    for row in get_vehicle_fuel_transaction_rows(vehicle_ids=ids, start=start, end=end):
        direct[row['vehicle_id']].append(row)
    legacy = _group(FuelConsumption.objects.filter(vehicle_id__in=ids, date__date__range=(start, end)))
    services = _group(ServiceTransaction.objects.filter(vehicle_id__in=ids, datum__range=(start, end)).select_related('popravka_kategorija'))
    requisitions = _group(Requisition.objects.filter(vehicle_id__in=ids, datum_trebovanja__range=(start, end)).select_related('popravka_kategorija'))
    recoveries = _group(Insurance.objects.filter(vehicle_id__in=ids, kola=True, datum__range=(start, end)))
    policies = _group(Policy.objects.filter(vehicle_id__in=ids)
        .filter(Q(start_date__lte=end) | Q(start_date__isnull=True))
        .filter(Q(end_date__gte=start) | Q(end_date__isnull=True)))
    leases = list(Lease.objects.filter(vehicle_id__in=ids, start_date__lte=end, end_date__gte=start))
    lease_map = {r.pk: r for r in leases}
    leases_by_vehicle = defaultdict(list)
    for row in leases:
        leases_by_vehicle[row.vehicle_id].append(row)
    interest = {(r.lease_id, r.year): r.interest_amount for r in LeaseInterest.objects.filter(lease_id__in=lease_map, year__range=(start.year, end.year))}
    profiles = _group(VehicleAnalysisProfile.objects.filter(vehicle_id__in=ids, effective_from__lte=end).order_by('effective_from', 'pk'))
    orders = _group(VehicleTravelOrder.objects.filter(vehicle_id__in=ids, created_at__lte=end).filter(Q(closed_at__isnull=True) | Q(closed_at__gte=start)).select_related('job_code'))
    assignments = _group(JobCode.objects.filter(vehicle_id__in=ids, assigned_date__lte=end).select_related('organizational_unit').order_by('assigned_date', 'pk'))
    assessments = _group(VehicleEconomicAssessment.objects.filter(vehicle_id__in=ids, as_of__lte=end).order_by('as_of', 'pk'))
    labels = {v.pk: (v.brand + ' ' + v.model) for v in vehicles}
    from fleet.models import TrafficCard
    for card in TrafficCard.objects.filter(vehicle_id__in=ids, issue_date__lte=end).order_by('issue_date', 'pk'):
        labels[card.vehicle_id] = card.registration_number
    results = []
    days = list(_days(start, end))
    for vehicle in vehicles:
        pk = vehicle.pk
        warnings = set()
        history = profiles[pk]
        def profile_at(day):
            return next((p for p in reversed(history) if p.effective_from <= day), None)
        profile = profile_at(end)
        period_profiles = {getattr(profile_at(day), 'pk', None) for day in days}
        assignment = assignments[pk][-1] if assignments[pk] else None
        purpose_code, purpose_note = estimated_purpose(vehicle, assignment)
        if profile:
            purpose_code, purpose_note = profile.purpose, 'Potvrđena namena iz profila.'
        if len(period_profiles) > 1:
            warnings.add('Profil se menja unutar perioda; kontrolni prag se ne primenjuje na mešovit period.')
        def source_at(day):
            p = profile_at(day)
            return p.fuel_source if p else 'transactions'
        fuel = [r for r in direct[pk] if source_at(date_only(r['date'])) == 'transactions']
        for r in legacy[pk]:
            if source_at(date_only(r.date)) == 'legacy':
                fuel.append(dict(date=r.date, amount=r.amount, cost_bruto=r.cost_bruto,
                    cost_neto=r.cost_neto, price_per_liter=(r.cost_bruto / r.amount) if r.amount else None,
                    mileage=r.mileage, supplier=r.supplier, product=r.fuel_type,
                    receipt_number='Ranija evidencija'))
        if legacy[pk] and not fuel:
            warnings.add('Postoji ranija evidencija goriva, ali nije izabrana kao izvor. Izvori se ne sabiraju automatski.')
        ledger = recorded_analytics(fuel, services[pk], requisitions[pk], recoveries[pk], start, end)
        timeline = nearest_period(odometers[pk], start, end)
        observed = timeline['total_km']
        points = timeline['days']
        distance = observed
        if distance is None:
            warnings.add('Nema dva upotrebljiva očitanja za razliku kilometraže; RSD/km se ne računa.')
        if timeline['issue_count']:
            warnings.add('Očitavanja kilometraže opadaju; proveriti unose ili zamenu brojača.')

        daily = {day: ZERO for day in days}
        known_days = set()
        for r in fuel:
            if r['cost_bruto'] is not None:
                daily[date_only(r['date'])] += Decimal(r['cost_bruto'])
                known_days.add(date_only(r['date']))
            else:
                warnings.add('Postoje dokumenti bez iznosa; zbir je nepotpun.')
        for records, date_field, value_field in [(services[pk], 'datum', 'potrazuje'), (requisitions[pk], 'datum_trebovanja', 'vrednost_nab')]:
            for r in records:
                if getattr(r, value_field) is not None:
                    daily[getattr(r, date_field)] += getattr(r, value_field)
                    known_days.add(getattr(r, date_field))
                else:
                    warnings.add('Postoje dokumenti bez iznosa; zbir je nepotpun.')
        policy_total = ZERO
        policy_count = 0
        for p in policies[pk]:
            if not p.start_date or not p.end_date or p.premium_amount is None or p.end_date < p.start_date:
                warnings.add('Polisa nema potpun iznos ili ispravan period; nije obračunata.')
                continue
            if p.end_date < start:
                continue
            policy_count += 1
            per_day = p.premium_amount / Decimal((p.end_date - p.start_date).days + 1)
            for day in _days(max(start, p.start_date), min(end, p.end_date)):
                known_days.add(day)
                daily[day] += per_day
                policy_total += per_day
        charge_total = ZERO
        interest_total = ZERO
        charge_days = interest_days = 0
        basis_labels = set()
        basis_codes = set()
        missing_holding_days = 0
        contract_missing = 0
        for day in days:
            basis, label, lease = holding_at(leases_by_vehicle[pk], day)
            basis_codes.add(basis)
            basis_labels.add(label)
            if basis == 'unknown':
                missing_holding_days += 1
                continue
            if lease is None:
                continue
            if lease.lease_type == 'finansijski':
                amount = interest.get((lease.pk, day.year))
                if amount is None:
                    contract_missing += 1
                else:
                    interest_days += 1
                    known_days.add(day)
                    part = amount / Decimal(366 if calendar.isleap(day.year) else 365)
                    interest_total += part
                    daily[day] += part
            else:
                part = lease_daily_amount(lease, day)
                if part is None:
                    contract_missing += 1
                else:
                    charge_days += 1
                    known_days.add(day)
                    charge_total += part
                    daily[day] += part
        if missing_holding_days:
            warnings.add(f'Preklopljeni ugovori tokom {missing_holding_days} dana; ugovorni trošak za te dane nije obračunat.')
        if contract_missing:
            warnings.add(f'Nedostaje potvrđena naknada / kamata ili važeći ugovor za {contract_missing} dana.')
        if charge_total:
            warnings.add('Proveriti obuhvat ugovorne naknade: uključeni servis / osiguranje ne smeju biti dvostruko evidentirani.')
        booked_days = set()
        overlapping_days = 0
        jobs = {}
        # Each recorded day's cost follows the vehicle's assignment on that date.
        total = sum(daily.values(), ZERO)
        if total < 0:
            warnings.add('Negativan zbir / storno: proveriti period i poreklo stavki; kontrolni prag se ne primenjuje.')
        evidence_count = sum(ledger['counts'].values()) + policy_count
        has_cost = bool(known_days)
        unassigned_days = 0
        for day in days:
            active = _active_orders(orders[pk], day)
            if active:
                booked_days.add(day)
            if len(active) > 1:
                overlapping_days += 1
            assignment_on_day = next((a for a in reversed(assignments[pk]) if a.assigned_date <= day), None)
            job = assignment_on_day.organizational_unit if assignment_on_day else None
            if job is not None:
                row = jobs.setdefault(job.pk, dict(code=job.code, name=job.name, days=0, amount=ZERO))
                row['days'] += 1
                row['amount'] += daily[day]
            else:
                unassigned_days += 1
        if overlapping_days:
            warnings.add(f'Preklapanje naloga tokom {overlapping_days} dana; proveriti evidenciju. Dani se broje jednom.')
        if unassigned_days:
            warnings.add(f'Vozilo nema dodeljenu šifru posla za {unassigned_days} dana; troškovi tih dana ostaju neraspoređeni.')
        # Neraspodeljeno je ostatak posle raspodele; racuna se jednom, u punoj
        # Decimal tacnosti, umesto sabiranja zaokruzenih dnevnih delova.
        unallocated = total - sum((j['amount'] for j in jobs.values()), ZERO)
        if not has_cost:
            for job in jobs.values():
                job['amount'] = None
        per_km = total / distance if has_cost and distance is not None and distance > 0 else None
        per_day = total / Decimal(len(booked_days)) if has_cost and booked_days else None
        criteria = []
        if profile and (profile.cost_limit_km is not None or profile.cost_limit_day is not None) and (
            basis_codes != {profile.criterion_basis} or missing_holding_days or contract_missing):
            warnings.add('Kontrolni prag ne važi za nepotpuno ili drugačije raspolaganje / ugovorni obračun u ovom periodu.')
        if profile and len(period_profiles) == 1 and basis_codes == {profile.criterion_basis} and not missing_holding_days and not contract_missing and total >= ZERO and 'Postoje dokumenti bez iznosa; zbir je nepotpun.' not in warnings:
            for label, actual, limit in [('RSD/km', per_km, profile.cost_limit_km), ('RSD/dan po nalogu', per_day, profile.cost_limit_day)]:
                if limit is not None:
                    criteria.append(dict(label=label, value=actual, limit=limit, exceeded=actual is not None and actual > limit))
        status = 'Pregled kriterijuma' if any(c['exceeded'] for c in criteria) else ('U okviru unetih pragova' if criteria and all(c['value'] is not None for c in criteria) else 'Bez ocene prema pragu')
        if warnings:
            quality = 'Potrebna provera podataka'
        else:
            quality = 'Izvori dostupni; potpunost troškova nije potvrđena'
        monthly = {r['month']: dict(r, included=None) for r in ledger['monthly']}
        for day, value in daily.items():
            if day in known_days:
                month = monthly[day.replace(day=1)]
                month['included'] = (month['included'] or ZERO) + value
        assignment = assignments[pk][-1] if assignments[pk] else None
        today = timezone.localdate()
        lease_rows = [_lease_overview(row, interest, today)
                      for row in leases_by_vehicle[pk]]
        readiness = _readiness(profile, missing_holding_days, contract_missing,
            distance, unassigned_days, len(days), purpose_note)
        results.append(dict(vehicle=vehicle, vehicle_id=pk, label=labels[pk], profile=profile,
            purpose=dict(VehicleAnalysisProfile.Purpose.choices)[purpose_code],
            purpose_code=purpose_code, purpose_estimated=profile is None, purpose_note=purpose_note,
            latest_assessment=assessments[pk][-1] if assessments[pk] else None,
            indicators=PURPOSE_METRICS.get(purpose_code, ''),
            basis=', '.join(sorted(basis_labels)) or 'Nije potvrđeno',
            basis_codes=basis_codes,
            center=assignment.organizational_unit.center if assignment and assignment.organizational_unit else 'Bez centra',
            period_start=start, period_end=end, period_days=len(days), ledger=ledger,
            fuel=fuel, services=services[pk], requisitions=requisitions[pk], recoveries=recoveries[pk],
            total=total if has_cost else None, policy=policy_total if policy_count else None,
            contract=charge_total if charge_days else None,
            interest=interest_total if interest_days else None, recovery=ledger['totals']['recovery'] if ledger['counts']['recovery'] else None,
            net_after_recovery=(total - ledger['totals']['recovery']) if has_cost else None,
            mileage=timeline, mileage_approximate=timeline['approximate'],
            distance=distance, observed_distance=observed, mileage_start=points[0]['date'] if points else None,
            mileage_end=points[-1]['date'] if points else None, per_km=per_km, per_day=per_day,
            per_calendar_day=total / Decimal(len(days)) if has_cost else None,
            booked_days=len(booked_days), booked_percent=Decimal(len(booked_days)) * 100 / len(days),
            order_count=len(orders[pk]), downtime_days=None,
            criteria=criteria, status=status, quality=quality, warnings=sorted(warnings),
            jobs=list(jobs.values()), unallocated=unallocated if has_cost else None,
            monthly=list(monthly.values()), evidence_count=evidence_count,
            readiness=readiness, ready_count=sum(1 for i in readiness if i['state'] == 'ok'),
            missing_count=sum(1 for i in readiness if i['state'] == 'missing'),
            leases=lease_rows))
    return results


def fleet_summary(rows):
    # A weighted rate only includes vehicles with both comparable numerator and denominator.
    comparable = [r for r in rows if r['per_km'] is not None]
    km = sum((r['distance'] for r in comparable), ZERO)
    cost = sum((r['total'] for r in comparable), ZERO)
    known = [r for r in rows if r['total'] is not None]
    return dict(count=len(rows), known_count=len(known), total=sum((r['total'] for r in known), ZERO) if known else None,
        distance=km, per_km=cost/km if km else None, comparable_count=len(comparable),
        review_count=sum(bool(r['warnings']) or any(c['exceeded'] for c in r['criteria']) for r in rows))


def compare_scenarios(assessment, scenarios):
    r = assessment.discount_percent / Decimal(100)
    n = assessment.years
    annuity = sum((Decimal(1) / (1+r)**year for year in range(1, n+1)), ZERO)
    discount = (1+r)**n
    results = []
    for scenario in scenarios:
        pv = scenario.initial_cost + scenario.annual_cost * annuity - scenario.residual_value / discount
        eac = pv / annuity
        results.append(dict(name=scenario.name, kind=scenario.kind, feasible=scenario.feasible,
            initial_cost=str(scenario.initial_cost), annual_cost=str(scenario.annual_cost),
            residual_value=str(scenario.residual_value), evidence=scenario.evidence,
            present_cost=str(pv), annual_equivalent=str(eac),
            per_km=str(eac / assessment.annual_km) if assessment.annual_km else None,
            per_day=str(eac / assessment.annual_days) if assessment.annual_days else None))
    feasible = [r for r in results if r['feasible']]
    keep = next((r for r in feasible if r['kind'] == 'keep'), None)
    best = min(feasible, key=lambda r: Decimal(r['present_cost'])) if feasible else None
    recommendation = 'Nema dovoljno uporedivih izvodljivih alternativa.'
    savings = None
    if keep and best and len(feasible) >= 2:
        savings = Decimal(keep['annual_equivalent']) - Decimal(best['annual_equivalent'])
        recommendation = ('Zadržavanje je najpovoljnije ili izjednačeno u okviru unetih pretpostavki.' if savings == 0 else
            f'Razmotriti alternativu „{best["name"]}” — niži ekvivalentni godišnji trošak od zadržavanja.')
    # Metodologija se ne upisuje u snimak: vezana je za version, a prikaz je cita
    # iz koda. Ranije se ista tabela ponavljala u svakoj sacuvanoj proceni.
    return dict(version=VERSION, as_of=assessment.as_of.isoformat(), years=n, discount_percent=str(assessment.discount_percent),
        annual_km=assessment.annual_km, annual_days=assessment.annual_days, scope=assessment.scope,
        assumptions=assessment.assumptions, scenarios=results, recommendation=recommendation,
        annual_saving=str(savings) if savings is not None else None)
