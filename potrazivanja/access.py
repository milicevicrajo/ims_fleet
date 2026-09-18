from django.core.exceptions import PermissionDenied
from django.db.models import Q
from core.mixins import user_has_role_permission as has
from core.models import OrganizationalUnit


def _allowed_centers_from_user(user):
    raw = (user.allowed_center_codes or '').replace(';', ',').split(',')
    return sorted({str(x).strip() for x in list(raw) + list(user.allowed_centers.values_list('center', flat=True)) if str(x).strip()})


def _allowed_sif_pos_from_user(user):
    explicit = set(user.allowed_centers.values_list('code', flat=True))
    explicit.update(OrganizationalUnit.objects.filter(center__in=_allowed_centers_from_user(user)).values_list('code', flat=True))
    return sorted(explicit)


def can_view(user):
    return has(user, 'potrazivanja:dashboard')


def can_view_all(user):
    return has(user, "potrazivanja:view_all")


def can_edit(user, kind, action='update'):
    return can_view(user) and can_view_all(user) and has(user, f'potrazivanja:{kind}_{action}')


def can_sync(user):
    return has(user, "potrazivanja:sync_status") and can_view_all(user)


def check_access(user):
    if not can_view(user):
        raise PermissionDenied("Nemate pristup Potraživanjima.")


def scoped(queryset, user):
    check_access(user)
    return queryset if can_view_all(user) else queryset.filter(
        Q(job_code__in=_allowed_sif_pos_from_user(user)) | Q(center_code__in=_allowed_centers_from_user(user)))


def can_view_job(user, code, company=1):
    """Check the local collections scope, including source-catalog jobs absent in OJ."""
    if not can_view(user):
        return False
    if can_view_all(user) or code in _allowed_sif_pos_from_user(user):
        return True
    centers = set(_allowed_centers_from_user(user))
    if not centers:
        return False
    from .models import CollectionState, SourceRow
    state = CollectionState.objects.select_related('current_snapshot').filter(company=company).first()
    if not state or not state.current_snapshot or state.current_snapshot.status != 'published':
        return False
    snapshot = state.current_snapshot
    if snapshot.positions.filter(job_code=code, center_code__in=centers).exists():
        return True
    step = snapshot.run.steps.filter(code='posao').only('details').first()
    if not step:
        return False
    raw = SourceRow.objects.filter(dataset_id=step.details['dataset_id'], job_code=code).values_list('raw_data', flat=True).first()
    return bool(raw and str(raw.get('blok', '')).strip() in centers)
