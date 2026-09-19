"""Shared period analysis and reproducible prospective LCC comparisons (RSD)."""
import calendar
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import OuterRef, Subquery, Q
from django.utils import timezone

from fleet.models import (Vehicle, JobCode, FuelConsumption, ServiceTransaction, Requisition,
    Insurance, Policy, VehicleTravelOrder, VehicleHolding, Lease, LeaseInterest,
    VehicleAnalysisProfile, VehicleDowntime, LeaseChargePeriod, VehicleEconomicAssessment)
from fleet.support.fuel import get_vehicle_fuel_transaction_rows
from fleet.support.management_reports import allowed_centers
from fleet.support.vehicle_detail import recorded_analytics, date_only
from fleet.support.vehicle_mileage import observed_timeline

ZERO = Decimal('0')
VERSION = 'IMS-FLOTA-2.0'
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
    ('Kilometraža perioda', 'Krajnje − početno očitanje, bez pada brojača između njih.',
     'Očitavanja odabranog izvora goriva i naloga vozila; OMV koristi pozitivnu korigovanu kilometražu kada postoji.',
     'RSD/km postoji samo kada očitanja pokrivaju oba granična datuma. Bez godišnje ekstrapolacije; stvarni termini očitanja ostaju vidljivi.'),
    ('RSD/km', 'Obuhvaćeni troškovi / potvrđena razlika km za iste granice perioda.',
     'Zajednički obračun troškova i kilometraže.',
     'Poredi se samo sa unetim pragom istog obuhvata. Prekoračenje traži pregled; ne određuje zamenu.'),
    ('Dani po nalogu', 'Broj jedinstvenih kalendarskih dana pokrivenih nalozima unutar perioda.',
     'Datum otvaranja i zatvaranja naloga; otvoren nalog do kraja izabranog perioda.',
     'Administrativno zaduženje, nije dokaz produktivnog rada. Preklopljeni dani se ne sabiraju dvaput.'),
    ('RSD/dan po nalogu', 'Obuhvaćeni troškovi celog perioda / jedinstveni dani po nalogu.',
     'Troškovi perioda i nalozi.',
     'Uključuje uticaj slobodnog kapaciteta. Nije cena radnog dana mašine niti marginalni trošak novog posla.'),
    ('Raspodela na poslove', 'Dnevni deo obuhvaćenih troškova pripada jedinom potvrđenom poslu tog dana.',
     'Direktno polje šifre posla na nalogu vozila.',
     'Interna raspodela po vremenu, ne direktno knjiženje. Bez naloga, bez šifre ili uz sukob poslova: neraspoređeno. Zbir poslova i neraspoređenog dela jednak je zbiru troškova.'),
    ('Evidentirani zastoji', 'Jedinstveni dani potvrđene neupotrebljivosti unutar perioda.',
     'Posebna evidencija zastoja, ne datum prijave kvara.',
     'Bez zapisa znači da zastoji nisu evidentirani; ne znači 100% raspoloživosti. Prijave servisa se ne broje kao kvarovi.'),
    ('Polise i ugovori', 'Premija × dani preklapanja / dani polise. Mesečna naknada / dani konkretnog meseca; ukupna naknada / dani njenog perioda.',
     'Polise, istorija raspolaganja i potvrđeni periodi naknada.',
     'Oba kraja datuma uključena. Nepoznat osnov raspolaganja ili značenje rate ostaju upozorenje. Proveriti da se uključene usluge ne ponove u drugim izvorima.'),
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


def _active(rows, day, first='start_date', last='end_date'):
    return [r for r in rows if getattr(r, first) <= day and (getattr(r, last) is None or getattr(r, last) >= day)]


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


def _lease_overview(lease, lease_charges, interest_by_year, today):
    """Sta je rata, a sta preostala ugovorna obaveza — po POTVRDJENOJ naknadi.

    Staro polje `current_payment_amount` se ovde samo prikazuje, bez tumacenja:
    nije potvrdjeno da li je mesecna rata ili ukupan iznos ugovora (P-08).
    """
    current = next((c for c in lease_charges if c.start <= today <= c.end), None)
    if current is None:
        current = next((c for c in lease_charges if c.start > today), None)
    daily = monthly = None
    if current is not None:
        if current.basis == 'monthly':
            monthly = current.amount
            daily = current.amount / Decimal(calendar.monthrange(today.year, today.month)[1])
        else:
            span = Decimal((current.end - current.start).days + 1)
            daily = current.amount / span
            monthly = daily * Decimal(30)
    remaining_to = min(lease.end_date, current.end) if current is not None else lease.end_date
    remaining_days = max((remaining_to - today).days + 1, 0) if remaining_to >= today else 0
    return dict(
        lease=lease,
        type_label=lease.get_lease_type_display(),
        confirmed=current is not None,
        charge=current,
        rate_monthly=monthly,
        rate_daily=daily,
        rate_basis=current.basis if current is not None else None,
        legacy_amount=lease.current_payment_amount,
        remaining_days=remaining_days,
        remaining_months=round(remaining_days / Decimal('30.44'), 1) if remaining_days else Decimal(0),
        remaining_amount=(daily * Decimal(remaining_days)) if daily is not None and remaining_days else None,
        interest_current_year=interest_by_year.get((lease.pk, today.year)),
        expired=lease.end_date < today,
    )


def _readiness(profile, period_profiles, missing_holding_days, contract_missing,
               distance, orders_in_period, jobless_orders, downtime_rows, period_days):
    """Sta je potrebno za obracun troskova, sta nedostaje i gde se popunjava.

    Redosled je redosled popunjavanja: bez namene nema izvora goriva, bez
    raspolaganja nema naknada, bez naknada nema ugovornog troska, i tako redom.
    """
    def item(order, label, state, detail, effect, where=None, where_label=None):
        return dict(order=order, label=label, state=state, detail=detail,
                    effect=effect, where=where, where_label=where_label)

    items = []

    if profile is None:
        items.append(item(1, 'Poslovna namena vozila', 'missing',
            'Namena nije uneta ni za jedan dan perioda.',
            'Određuje merodavne pokazatelje, izvor goriva i da li se kontrolni prag primenjuje.',
            'vehicle_analysis_settings', 'Namena, kriterijumi i evidencija'))
    elif None in period_profiles:
        items.append(item(1, 'Poslovna namena vozila', 'partial',
            'Namena ne pokriva ceo period; za deo dana koristi se podrazumevani izvor NIS/OMV.',
            'Određuje merodavne pokazatelje, izvor goriva i da li se kontrolni prag primenjuje.',
            'vehicle_analysis_settings', 'Namena, kriterijumi i evidencija'))
    elif len(period_profiles) > 1:
        items.append(item(1, 'Poslovna namena vozila', 'partial',
            'Namena se menja unutar perioda; kontrolni prag se na mešovit period ne primenjuje.',
            'Određuje merodavne pokazatelje, izvor goriva i da li se kontrolni prag primenjuje.',
            'vehicle_analysis_settings', 'Namena, kriterijumi i evidencija'))
    else:
        items.append(item(1, 'Poslovna namena vozila', 'ok',
            f'{profile.get_purpose_display()} · izvor goriva: {profile.get_fuel_source_display()}',
            'Određuje merodavne pokazatelje, izvor goriva i da li se kontrolni prag primenjuje.'))

    if missing_holding_days:
        items.append(item(2, 'Osnov raspolaganja', 'missing' if missing_holding_days == period_days else 'partial',
            f'Nije jednoznačno evidentiran za {missing_holding_days} od {period_days} dana.',
            'Bez njega se ne zna da li vozilo nosi naknadu najma, kamatu ili nijedno.',
            'vehicle_holding_create', 'Raspolaganje i polise'))
    else:
        items.append(item(2, 'Osnov raspolaganja', 'ok',
            'Evidentiran za svaki dan perioda.',
            'Određuje da li vozilo nosi naknadu najma, kamatu ili nijedno.'))

    if contract_missing:
        items.append(item(3, 'Potvrđena naknada ugovora / kamata', 'missing',
            f'Nedostaje za {contract_missing} dana. Staro polje „Trenutna rata / iznos otplate“ se ne koristi '
            'jer nije potvrđeno da li je mesečni ili ukupan iznos.',
            'Naknada najma i kamata lizinga ulaze u obuhvaćene troškove.',
            'vehicle_analysis_settings', 'Namena, kriterijumi i evidencija'))
    else:
        items.append(item(3, 'Potvrđena naknada ugovora / kamata', 'ok',
            'Potvrđena za sve dane sa ugovornim raspolaganjem.',
            'Naknada najma i kamata lizinga ulaze u obuhvaćene troškove.'))

    if distance is None:
        items.append(item(4, 'Očitavanja kilometraže na granicama perioda', 'missing',
            'Nema očitanja na oba granična datuma, pa se kilometraža ne izvodi. Ne procenjuje se iz starijih očitanja.',
            'Bez toga nema pokazatelja RSD/km.',
            None, 'Kartica „Kilometraža“ i putni nalozi'))
    else:
        items.append(item(4, 'Očitavanja kilometraže na granicama perioda', 'ok',
            f'{distance:.0f} km između graničnih očitanja.',
            'Daje pokazatelj RSD/km.'))

    # Naziv stavke je uvek isti; menja se samo stanje i opis, da spisak ostane
    # uporediv izmedju dva prikaza.
    orders_effect = 'Daju RSD/dan po nalogu i raspodelu troška na poslove.'
    if not orders_in_period:
        items.append(item(5, 'Putni nalozi i šifra posla', 'missing',
            'Nema nijednog naloga koji dodiruje period.', orders_effect,
            'vehicle_travel_order_create', 'Putni nalozi vozila'))
    elif jobless_orders:
        items.append(item(5, 'Putni nalozi i šifra posla', 'partial',
            f'Od {orders_in_period} naloga, {jobless_orders} nema potvrđenu šifru posla. '
            'Pripadnost se ne izvodi iz centra vozila.', orders_effect,
            'vehicle_analysis_settings', 'Namena, kriterijumi i evidencija'))
    else:
        items.append(item(5, 'Putni nalozi i šifra posla', 'ok',
            f'Svih {orders_in_period} naloga ima potvrđenu šifru posla.', orders_effect))

    if not downtime_rows:
        items.append(item(6, 'Evidencija zastoja', 'missing',
            'Nije vođena. Odsustvo zapisa ne znači da zastoja nije bilo.',
            'Pokazuje koliko je vozilo bilo neupotrebljivo u periodu.',
            'vehicle_analysis_settings', 'Namena, kriterijumi i evidencija'))
    else:
        items.append(item(6, 'Evidencija zastoja', 'ok',
            f'Evidentirano {len(downtime_rows)} zapisa.',
            'Pokazuje koliko je vozilo bilo neupotrebljivo u periodu.'))

    if profile is None or (profile.cost_limit_km is None and profile.cost_limit_day is None):
        items.append(item(7, 'Kontrolni prag', 'optional',
            'Nije unet. Nema univerzalnog praga isplativosti po masi vozila.',
            'Signal za pregled kada trošak pređe unapred obrazložen iznos.',
            'vehicle_analysis_settings', 'Namena, kriterijumi i evidencija'))
    else:
        items.append(item(7, 'Kontrolni prag', 'ok',
            'Unet, sa pisanim osnovom i izabranim načinom raspolaganja.',
            'Signal za pregled kada trošak pređe unapred obrazložen iznos.'))

    return items


def period_analysis(vehicles, start, end):
    """Batch-load sources once; identical output is used by fleet and vehicle screens."""
    vehicles = list(vehicles)
    if end < start or (end - start).days > 1096 or end > timezone.localdate():
        raise ValueError('Neispravan period analize.')
    ids = [v.pk for v in vehicles]
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
    holdings = _group(VehicleHolding.objects.filter(vehicle_id__in=ids, start_date__lte=end).select_related('lease'))
    leases = list(Lease.objects.filter(vehicle_id__in=ids, start_date__lte=end, end_date__gte=start))
    lease_map = {r.pk: r for r in leases}
    charges = defaultdict(list)
    all_charges = defaultdict(list)
    for charge in LeaseChargePeriod.objects.filter(lease_id__in=lease_map).order_by('start', 'pk'):
        all_charges[charge.lease_id].append(charge)
        if charge.start <= end and charge.end >= start:
            charges[charge.lease_id].append(charge)
    leases_by_vehicle = defaultdict(list)
    for row in leases:
        leases_by_vehicle[row.vehicle_id].append(row)
    interest = {(r.lease_id, r.year): r.interest_amount for r in LeaseInterest.objects.filter(lease_id__in=lease_map, year__range=(start.year, end.year))}
    profiles = _group(VehicleAnalysisProfile.objects.filter(vehicle_id__in=ids, effective_from__lte=end).order_by('effective_from', 'pk'))
    orders = _group(VehicleTravelOrder.objects.filter(vehicle_id__in=ids, created_at__lte=end).filter(Q(closed_at__isnull=True) | Q(closed_at__gte=start)).select_related('job_code'))
    downtime = _group(VehicleDowntime.objects.filter(vehicle_id__in=ids, start__lte=end).filter(Q(end__isnull=True) | Q(end__gte=start)))
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
        if None in period_profiles:
            warnings.add('Poslovna namena / izvor podataka nisu potvrđeni za ceo period; podrazumevani izvor goriva je NIS/OMV.')
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
        readings = []
        def reading(day, value, source):
            if day and start <= day <= end and value is not None and value >= 0:
                readings.append(dict(date=day, value=Decimal(value), source=source))
        for r in fuel:
            if r.get('mileage') and r['mileage'] > 0:
                reading(date_only(r['date']), r['mileage'], 'Gorivo')
        for o in orders[pk]:
            reading(o.created_at, o.start_mileage, 'Početak naloga')
            reading(o.closed_at, o.end_mileage, 'Završetak naloga')
        timeline = observed_timeline(readings)
        observed = timeline['total_km']
        points = timeline['days']
        distance = observed if points and points[0]['date'] == start and points[-1]['date'] == end and start < end else None
        if distance is None:
            warnings.add('Nema usklađenih očitanja za oba granična datuma; RSD/km se ne računa.')
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
            active = _active(holdings[pk], day)
            if len(active) != 1:
                missing_holding_days += 1
                basis_codes.add('unknown')
                continue
            h = active[0]
            if h.basis == 'owned':
                basis_codes.add('owned')
                basis_labels.add('Vlasništvo IMS' + (' / kredit' if h.financing == 'credit' else ''))
                if h.financing == 'credit':
                    warnings.add('Kamate kredita nisu u automatskom zbiru; obuhvatiti ih zasebno u planu novca.')
                continue
            lease = h.lease
            if not lease or not lease.start_date <= day <= lease.end_date:
                contract_missing += 1
                basis_codes.add('unknown')
                continue
            basis_labels.add(lease.lease_type_label)
            basis_codes.add('dugorocni' if lease.is_long_term_rental else lease.lease_type)
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
                valid = _active(charges[lease.pk], day, 'start', 'end')
                if len(valid) != 1:
                    contract_missing += 1
                else:
                    charge_days += 1
                    known_days.add(day)
                    c = valid[0]
                    divisor = calendar.monthrange(day.year, day.month)[1] if c.basis == 'monthly' else (c.end - c.start).days + 1
                    part = c.amount / Decimal(divisor)
                    charge_total += part
                    daily[day] += part
        if missing_holding_days:
            warnings.add(f'Osnov raspolaganja nije jednoznačno evidentiran za {missing_holding_days} dana.')
        if contract_missing:
            warnings.add(f'Nedostaje potvrđena naknada / kamata ili važeći ugovor za {contract_missing} dana.')
        if charge_total:
            warnings.add('Proveriti obuhvat ugovorne naknade: uključeni servis / osiguranje ne smeju biti dvostruko evidentirani.')
        booked_days = set()
        overlapping_days = 0
        jobs = {}
        # Allocate a uniform daily share of the period subtotal; not the invoice day.
        total = sum(daily.values(), ZERO)
        if total < 0:
            warnings.add('Negativan zbir / storno: proveriti period i poreklo stavki; kontrolni prag se ne primenjuje.')
        evidence_count = sum(ledger['counts'].values()) + policy_count
        has_cost = bool(known_days)
        day_cost = total / Decimal(len(days))
        for day in days:
            active = _active_orders(orders[pk], day)
            if active:
                booked_days.add(day)
            if len(active) > 1:
                overlapping_days += 1
            job_ids = {o.job_code_id for o in active}
            if len(job_ids) == 1 and None not in job_ids:
                job = active[0].job_code
                row = jobs.setdefault(job.pk, dict(code=job.code, name=job.name, days=0, amount=ZERO))
                row['days'] += 1
                row['amount'] += day_cost
        if overlapping_days:
            warnings.add(f'Preklapanje naloga tokom {overlapping_days} dana; proveriti evidenciju. Dani se broje jednom.')
        if any(not o.job_code_id for o in orders[pk]):
            warnings.add('Postoje nalozi bez potvrđene šifre posla; pripadnost se ne izvodi iz centra vozila.')
        # Neraspodeljeno je ostatak posle raspodele; racuna se jednom, u punoj
        # Decimal tacnosti, umesto sabiranja zaokruzenih dnevnih delova.
        unallocated = total - sum((j['amount'] for j in jobs.values()), ZERO)
        if not has_cost:
            for job in jobs.values():
                job['amount'] = None
        down_days = set()
        for d in downtime[pk]:
            down_days.update(_days(max(start, d.start), min(end, d.end or end)))
        if down_days & booked_days:
            warnings.add('Nalozi obuhvataju i evidentirane dane neupotrebljivosti; proveriti stvarno angažovanje.')
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
        lease_rows = [_lease_overview(row, all_charges[row.pk], interest, today)
                      for row in leases_by_vehicle[pk]]
        readiness = _readiness(profile, period_profiles, missing_holding_days, contract_missing,
            distance, len(orders[pk]), sum(1 for o in orders[pk] if not o.job_code_id),
            downtime[pk], len(days))
        results.append(dict(vehicle=vehicle, vehicle_id=pk, label=labels[pk], profile=profile,
            purpose=profile.get_purpose_display() if profile else 'Namena nije razvrstana',
            latest_assessment=assessments[pk][-1] if assessments[pk] else None,
            indicators=PURPOSE_METRICS.get(profile.purpose, '') if profile else 'Najpre razvrstati poslovnu namenu.',
            basis=', '.join(sorted(basis_labels)) or 'Nije potvrđeno',
            basis_codes=basis_codes,
            center=assignment.organizational_unit.center if assignment and assignment.organizational_unit else 'Bez centra',
            period_start=start, period_end=end, period_days=len(days), ledger=ledger,
            fuel=fuel, services=services[pk], requisitions=requisitions[pk], recoveries=recoveries[pk],
            total=total if has_cost else None, policy=policy_total if policy_count else None,
            contract=charge_total if charge_days else None,
            interest=interest_total if interest_days else None, recovery=ledger['totals']['recovery'] if ledger['counts']['recovery'] else None,
            net_after_recovery=(total - ledger['totals']['recovery']) if has_cost else None,
            distance=distance, observed_distance=observed, mileage_start=points[0]['date'] if points else None,
            mileage_end=points[-1]['date'] if points else None, per_km=per_km, per_day=per_day,
            per_calendar_day=total / Decimal(len(days)) if has_cost else None,
            booked_days=len(booked_days), booked_percent=Decimal(len(booked_days)) * 100 / len(days),
            order_count=len(orders[pk]), downtime_days=len(down_days) if downtime[pk] else None,
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
