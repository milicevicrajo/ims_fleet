"""Read-only import of IMS annual-leave allocations and decisions from payroll."""
from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db import connection, connections, transaction
from django.utils import timezone

from hr.models import AnnualLeaveAllowance, AnnualLeaveDecision, AnnualLeaveSync, Employee
from hr.sync import _resolve_hr_db_alias


SOURCE = '[putgeo-server].[BazaLDIMS].[dbo]'
COMPANY_CODE = 1


def fetch_source(year=None, using=None):
    clause = ' WHERE sif_pred=%s'
    params = [COMPANY_CODE]
    if year is not None:
        clause += ' AND god=%s'
        params.append(str(year))
    with connections[_resolve_hr_db_alias(using)].cursor() as cursor:
        cursor.execute(f'SELECT sif_pred,god,rasif,dana1,dana2,dana3,dana4,dana5,dana6,dana,ostalo,ranaz FROM {SOURCE}.[Godmor]'+clause, params)
        allocations = cursor.fetchall()
        cursor.execute(f'SELECT sif_pred,god,rasif,od_datuma,do_datuma,dana,komentar FROM {SOURCE}.[GodmorKor]'+clause, params)
        decisions = cursor.fetchall()
    return allocations, decisions


def integer(value, *, nullable=False):
    if value is None and nullable:
        return None
    result = int(value)
    if float(value) != result:
        raise ValueError
    return result


def identity(company, year, code, selected_year):
    key = (integer(company), integer(year), integer(code))
    if key[0] != COMPANY_CODE or not 1900 <= key[1] <= 2100 or key[2] < 0:
        raise ValueError
    if selected_year is not None and key[1] != selected_year:
        raise ValueError
    return key


def source_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError


def normalize_source(allocations, decisions, selected_year=None):
    normalized_allocations, normalized_decisions = {}, {}
    for row_number, row in enumerate(allocations, 1):
        try:
            company, year, code, *rest = row
            key = identity(company, year, code, selected_year)
            components, days, other, name = rest[:6], rest[6], rest[7], rest[8]
            days = integer(days)
            if days < 0 or len(str(name or '').strip()) > 255 or key in normalized_allocations:
                raise ValueError
            normalized_allocations[key] = {
                'allocated_days': days, 'source_other': integer(other, nullable=True),
                'source_employee_name': str(name or '').strip(),
                **{f'source_day_{index}': integer(value, nullable=True) for index, value in enumerate(components, 1)},
            }
        except (ValueError, TypeError, IndexError, OverflowError):
            raise ValidationError(f'Godmor, red {row_number}: neispravna ili duplirana dodela. Ništa nije sinhronizovano.')
    for row_number, row in enumerate(decisions, 1):
        try:
            company, year, code, start, end, days, comment = row
            base_key = identity(company, year, code, selected_year)
            start_date, end_date = source_date(start), source_date(end)
            start_time = start if isinstance(start, datetime) else datetime.combine(start, datetime.min.time())
            if start_time.tzinfo is not None:
                raise ValueError
            key = (*base_key, start_time.isoformat(timespec='microseconds'))
            days = integer(days)
            comment = str(comment or '').strip()
            if start_date > end_date or days < 0 or len(comment) > 255 or key in normalized_decisions:
                raise ValueError
            normalized_decisions[key] = {
                'start_date': start_date, 'end_date': end_date,
                'approved_days': days, 'source_comment': comment,
            }
        except (ValueError, TypeError, OverflowError):
            raise ValidationError(f'GodmorKor, red {row_number}: neispravno ili duplirano rešenje. Ništa nije sinhronizovano.')
    if not normalized_allocations and not normalized_decisions:
        raise ValidationError('Izvor nema podatke za izabrani obuhvat. Lokalni podaci nisu izmenjeni.')
    return normalized_allocations, normalized_decisions


def apply_snapshot(model, source, key_fields, *, year, employees, batch, now):
    queryset = model.objects.filter(company_code=COMPANY_CODE)
    if year is not None:
        queryset = queryset.filter(year=year)
    existing = {tuple(getattr(item, field) for field in key_fields): item for item in queryset}
    created, updated = [], []
    counts = {'created': 0, 'updated': 0, 'unchanged': 0, 'withdrawn': 0, 'unlinked': 0}
    business_fields = set()
    for key, values in source.items():
        # Legacy source code 0 means no employee identity; preserve it without linking.
        values = dict(values, employee_id=employees.get(key[2]) if key[2] > 0 else None, source_present=True)
        business_fields.update(values)
        if values['employee_id'] is None:
            counts['unlinked'] += 1
        item = existing.pop(key, None)
        if item is None:
            item = model(**dict(zip(key_fields, key)), **values, last_seen_at=now, last_sync=batch)
            created.append(item)
            counts['created'] += 1
        else:
            changed = any(getattr(item, field) != value for field, value in values.items())
            counts['updated' if changed else 'unchanged'] += 1
            for field, value in values.items():
                setattr(item, field, value)
            item.last_seen_at = now
            item.last_sync = batch
            updated.append(item)
    model.objects.bulk_create(created, batch_size=100)
    if updated:
        model.objects.bulk_update(updated, sorted(business_fields)+['last_seen_at','last_sync'], batch_size=25)
    # A changed source PK is a new decision; retain its previous local record as withdrawn.
    withdrawn_ids = [item.pk for item in existing.values() if item.source_present]
    for start in range(0, len(withdrawn_ids), 500):
        counts['withdrawn'] += model.objects.filter(pk__in=withdrawn_ids[start:start+500]).update(source_present=False, last_sync=batch)
    return counts


@transaction.atomic
def sync_annual_leave(*, year=None, using=None, user=None, dry_run=False):
    if year is not None:
        try:
            year = integer(year)
            if not 1900 <= year <= 2100:
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            raise ValidationError('Godina mora biti između 1900. i 2100.')
    # Serialize every entry point (web, command, task) before reading the source.
    if connection.vendor == 'microsoft':
        with connection.cursor() as cursor:
            cursor.execute("""DECLARE @result int;
                EXEC @result = sp_getapplock @Resource='hr:annual_leave_sync',
                    @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=0;
                SELECT @result;""")
            if cursor.fetchone()[0] < 0:
                raise ValidationError('Sinhronizacija godišnjih odmora je već u toku. Pokušajte ponovo kasnije.')
    allocations, decisions = normalize_source(*fetch_source(year=year, using=using), selected_year=year)
    employees = dict(Employee.objects.values_list('employee_code', 'pk'))
    batch = AnnualLeaveSync.objects.create(year=year, created_by=user)
    now = timezone.now()
    base_key = ['company_code','year','employee_code']
    counts = {
        'allocations': apply_snapshot(AnnualLeaveAllowance, allocations, base_key, year=year, employees=employees, batch=batch, now=now),
        'decisions': apply_snapshot(AnnualLeaveDecision, decisions, base_key+['source_start_key'], year=year, employees=employees, batch=batch, now=now),
    }
    batch.counts = counts
    batch.save(update_fields=['counts'])
    if dry_run:
        transaction.set_rollback(True)
    return counts
