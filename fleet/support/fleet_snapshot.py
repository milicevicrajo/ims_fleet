"""Current fleet inventory. All center totals use the same scoped vehicle set."""
from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import OuterRef, Q, Subquery
from django.urls import reverse
from django.utils import timezone

from ..models import DraftInsurance, DraftServiceTransaction, JobCode, Policy, Requisition, TrafficCard, Vehicle, VehicleTravelOrder


def fleet_snapshot(user, today=None):
    today = today or timezone.localdate()
    limit = today + timedelta(days=30)
    job = JobCode.objects.filter(vehicle=OuterRef('pk'), assigned_date__lte=today).order_by('-assigned_date', '-pk')
    card = TrafficCard.objects.filter(vehicle=OuterRef('pk'), issue_date__lte=today).order_by('-issue_date', '-pk')
    scoped = Vehicle.objects.annotate(
        current_center=Subquery(job.values('organizational_unit__center')[:1]),
        current_unit=Subquery(job.values('organizational_unit__name')[:1]),
        current_job_code=Subquery(job.values('organizational_unit__code')[:1]),
        plate=Subquery(card.values('registration_number')[:1]),
        registration_until=Subquery(card.values('registration_valid_until')[:1]),
    )
    allowed = list(user.allowed_centers.values_list('center', flat=True).distinct())
    if allowed:
        scoped = scoped.filter(current_center__in=allowed)
    archived_count = scoped.filter(otpis=True).count()
    vehicles = list(scoped.filter(otpis=False).order_by('brand', 'model', 'pk'))
    by_id = {v.pk: v for v in vehicles}
    ids = list(by_id)
    policies = list(Policy.objects.filter(vehicle_id__in=ids).order_by('-end_date', '-pk'))
    active_policies = [p for p in policies if p.start_date and p.end_date and p.start_date <= today <= p.end_date]
    ao_vehicles = {p.vehicle_id for p in active_policies if 'AUTOODGOVORNOST' in (p.insurance_type or '').upper()}
    orders = list(VehicleTravelOrder.objects.filter(vehicle_id__in=ids, created_at__lte=today).filter(Q(closed_at__isnull=True) | Q(closed_at__gt=today)).values('vehicle_id'))
    assigned = Counter(row['vehicle_id'] for row in orders)
    grouped = defaultdict(list)
    for v in vehicles:
        v.current_center = (v.current_center or '').strip() or None
        v.has_active_ao = v.pk in ao_vehicles
        v.has_assignment = v.pk in assigned
        grouped[v.current_center].append(v)

    def statistics(rows):
        years = [v.year_of_manufacture for v in rows if v.year_of_manufacture and 1886 <= v.year_of_manufacture <= today.year]
        values = [v.value for v in rows if v.value is not None]
        counts = Counter(v.category for v in rows)
        return dict(count=len(rows), passenger=counts[Vehicle.Category.PASSENGER], cargo=counts[Vehicle.Category.CARGO],
                    trailer=counts[Vehicle.Category.TRAILER], other=sum(n for key,n in counts.items() if key not in Vehicle.Category.values),
                    age=(today.year - sum(years)/len(years)) if years else None, age_known=len(years),
                    book_value=sum(values, Decimal('0')) if values else None, value_known=len(values),
                    assigned=sum(v.has_assignment for v in rows), ao=sum(v.has_active_ao for v in rows))

    centers = []
    for code, rows in sorted(grouped.items(), key=lambda item: (item[0] is None, item[0] or '')):
        centers.append(dict(code=code, label=f'Centar {code}' if code else 'Bez centra', vehicles=rows,
                            share=100*len(rows)/len(vehicles) if vehicles else 0, **statistics(rows)))
    totals = statistics(vehicles)
    groups = []

    def add_group(title, entries, description, tone='warning'):
        if entries:
            groups.append(dict(title=title, count=len(entries), entries=entries, description=description, tone=tone))

    def vehicle_entry(v, detail):
        return dict(label=f'{v.plate or v.chassis_number} · {v.brand} {v.model}', detail=detail, url=reverse('vehicle_detail', args=[v.pk]))

    add_group('Registracija je istekla', [vehicle_entry(v, v.registration_until.strftime('%d.%m.%Y')) for v in vehicles if v.registration_until and v.registration_until < today], 'Prema unetom roku registracije.', 'danger')
    add_group('Registracija ističe u narednih 30 dana', [vehicle_entry(v, v.registration_until.strftime('%d.%m.%Y')) for v in vehicles if v.registration_until and today <= v.registration_until <= limit], 'Prema unetom roku registracije.')
    add_group('Nedostaje rok registracije', [vehicle_entry(v, 'Rok sa registracione nalepnice nije unet.') for v in vehicles if not v.registration_until], 'Datum AO polise se ne prepisuje automatski kao rok registracije.', 'info')
    add_group('Nema evidentirane važeće AO polise', [vehicle_entry(v, 'Proveriti polisu autoodgovornosti.') for v in vehicles if not v.has_active_ao], 'Provera koristi početak, kraj i vrstu polise; kasko nije AO.')
    upcoming = []
    for p in active_policies:
        kind = (p.insurance_type or '').strip().upper()
        extended = any(other.vehicle_id == p.vehicle_id and (other.insurance_type or '').strip().upper() == kind and other.start_date and other.end_date and other.start_date <= p.end_date + timedelta(days=1) and other.end_date > p.end_date for other in policies)
        if p.end_date <= limit and p.is_renewable and not extended:
            upcoming.append(dict(label=f'{by_id[p.vehicle_id].plate or by_id[p.vehicle_id].chassis_number} · {p.policy_number or "Bez broja"}', detail=f'{p.insurance_type or "Vrsta nije uneta"} · {p.end_date:%d.%m.%Y}', url=reverse('policy_detail', args=[p.pk])))
    add_group('Polise pred istekom bez nastavka pokrića', upcoming, 'Rok do 30 dana. Evidentirano produženje bez prekida pokrića uklanja polisu iz ovog upozorenja.')
    add_group('Vozila bez trenutnog centra', [vehicle_entry(v, 'Dodeliti OJ / šifru posla.') for v in vehicles if not v.current_center], 'Buduće dodele nisu trenutni raspored.', 'info')
    add_group('Više istovremenih zaduženja', [vehicle_entry(by_id[pk], f'{count} otvorenih zaduženja') for pk,count in assigned.items() if count > 1], 'Brojač zaduženih vozila svako vozilo računa samo jednom.')
    corrections = []
    incomplete = Policy.objects.filter(Policy.incomplete_q())
    if allowed:
        incomplete = incomplete.filter(vehicle_id__in=ids)
    else:
        incomplete = incomplete.filter(Q(vehicle_id__in=ids) | Q(vehicle__isnull=True))
    sources = [('Polise za dopunu', incomplete.count(), 'policy_fixing_list')]
    if not allowed:
        sources += [('Spoljne usluge za povezivanje', DraftServiceTransaction.objects.count(), 'service_fixing_list'),
                    ('Trebovanja bez vozila', Requisition.objects.filter(nije_garaza=False, vehicle__isnull=True).count(), 'requisition_fixing_list'),
                    ('Naknade osiguranja za povezivanje', DraftInsurance.objects.count(), 'insurance_fixing_list')]
    for title,count,url in sources:
        if count:
            corrections.append(dict(label=title, detail=f'{count} stavki', url=reverse(url)))
    add_group('Evidencije za dopunu', corrections, 'Brojevi predstavljaju stavke evidencije. Ista polisa može biti i među upozorenjima o roku.', 'info')
    return dict(today=today, title='Kontrolna tabla flote', totals=totals, centers=centers,
                vehicles=vehicles, archived_count=archived_count, warning_groups=groups,
                warning_group_count=len(groups), restricted=bool(allowed),
                center_count=sum(bool(c['code']) for c in centers), open_order_count=len(orders),
                no_center_count=len(grouped.get(None, [])))
