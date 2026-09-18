from django.contrib.auth import get_user_model
from django.db import transaction, models
from django.utils import timezone
from potrazivanja.models import CollectionState, CollectionLegalCase, CollectionLegalEvent, SourceRow, FinancePartnerIdentity
from .source import day, timestamp, money, text, integer
from .sync import sync_collections, sync_lock
from .contacts import normalize_contacts


def import_cases(run):
    def records(name):
        step = run.steps.get(code=name)
        return SourceRow.objects.filter(dataset_id=step.details['dataset_id']).values_list('raw_data', flat=True)
    identities = {x.partner_code: x for x in FinancePartnerIdentity.objects.filter(company=1, partner_group=1)}
    users = set(get_user_model().objects.values_list('pk', flat=True))
    copied = 0
    for raw in records('postupak'):
        if CollectionLegalCase.objects.filter(legacy_id=raw['id']).exists():
            continue
        values = {}
        for field in CollectionLegalCase._meta.fields:
            if field.name not in raw or field.name in ('id', 'created_at', 'updated_at') or field.is_relation:
                continue
            value = raw[field.name]
            if isinstance(field, models.DecimalField): value = money(value) if value is not None else None
            elif isinstance(field, models.DateField): value = day(value)
            elif isinstance(field, models.CharField) or isinstance(field, models.TextField): value = text(value)
            values[field.name] = value
        identity = identities.get(integer(raw.get('sifra_partnera')))
        obj = CollectionLegalCase.objects.create(legacy_id=raw['id'], original_data=raw, identity=identity,
            created_by_id=raw.get('created_by_id') if raw.get('created_by_id') in users else None, **values)
        dates = {key: timestamp(raw[key]) for key in ('created_at', 'updated_at') if raw.get(key)}
        if dates: CollectionLegalCase.objects.filter(pk=obj.pk).update(**dates)
        copied += 1
    cases = dict(CollectionLegalCase.objects.exclude(legacy_id=None).values_list('legacy_id', 'pk'))
    events = 0
    for raw in records('promena_postupka'):
        if CollectionLegalEvent.objects.filter(legacy_id=raw['id']).exists(): continue
        if raw['postupak_id'] not in cases: raise ValueError('Promena nema pripadajući postupak.')
        event = CollectionLegalEvent.objects.create(legacy_id=raw['id'], case_id=cases[raw['postupak_id']],
            date=day(raw['datum']), text=text(raw['promena']), original_data=raw,
            created_by_id=raw.get('created_by_id') if raw.get('created_by_id') in users else None)
        if raw.get('created_at'): CollectionLegalEvent.objects.filter(pk=event.pk).update(created_at=timestamp(raw['created_at']))
        events += 1
    return {'cases': copied, 'events': events}


def initialize_independent_operations(progress=print):
    if CollectionState.objects.filter(company=1, operations_independent_at__isnull=False).exists():
        return {'already_initialized': True}
    run = sync_collections(trigger='import', include_legacy=True, progress=progress)
    with sync_lock(), transaction.atomic():
        state = CollectionState.objects.select_for_update().get(company=1)
        if state.operations_independent_at:
            return {'already_initialized': True}
        result = {'run_id': run.pk, 'contacts': normalize_contacts(), 'legal': import_cases(run)}
        state.operations_independent_at = timezone.now()
        state.save(update_fields=['operations_independent_at', 'updated_at'])
        run.scope['independent_operations'] = result
        run.save(update_fields=['scope'])
        return result
