"""Obuhvat kadrovskih podataka: centri i pojedinačne HR organizacione jedinice."""
from core.mixins import user_has_role_permission
from core.models import OrganizationalUnit
from fleet.services.employee_user_profiles import infer_center
from hr.models import Employee


def scope_values(user):
    centers = {x.strip() for x in (user.allowed_center_codes or '').replace(';', ',').split(',') if x.strip()}
    legacy = list(user.allowed_centers.values_list('code', 'center'))
    centers.update(str(center).strip() for _,center in legacy if center and str(center).strip())
    units = set()
    units.update(str(code).strip() for code,_ in legacy if code and str(code).strip())
    return centers, units


def has_restricted_scope(user):
    if user.is_superuser:
        return False
    centers, units = scope_values(user)
    return bool(centers or units or user_has_role_permission(user, 'hr:kadrovi_manage'))


def allowed_unit_codes(user, *, extra_centers=None):
    centers, units = scope_values(user)
    if extra_centers is not None:
        centers, units = set(extra_centers), set()
    registry = {str(code).strip():str(center).strip() for code,center in OrganizationalUnit.objects.values_list('code','center')}
    all_centers = set(registry.values()) - {''}
    result = set(units)
    for code,department in Employee.objects.values_list('org_unit_code','department_code').distinct():
        code = str(code or department or '').strip()
        center = registry.get(code) or infer_center(code, centers=all_centers)[0]
        if center in centers:
            result.add(code)
    return result


def visible_employees(user, *, unrestricted=False, extra_centers=None):
    qs = Employee.objects.all()
    if not user.is_authenticated:
        return qs.none()
    if extra_centers is None and (unrestricted or not has_restricted_scope(user)):
        return qs
    codes = allowed_unit_codes(user, extra_centers=extra_centers)
    ids = [pk for pk,code,department in qs.values_list('pk','org_unit_code','department_code')
           if str(code or department or '').strip() in codes]
    return qs.filter(pk__in=ids)


def scope_employee_records(qs, user, field='employee'):
    if not has_restricted_scope(user):
        return qs
    return qs.filter(**{f'{field}__in':visible_employees(user)})
