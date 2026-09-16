from django.db.models import Q

from core.mixins import user_has_role_permission


def can_view_all(user):
    return user_has_role_permission(user, "finansije:view_all")


def visible_scope(queryset, user, job_field="job_code"):
    if can_view_all(user):
        return queryset
    raw = getattr(user, "allowed_center_codes", "") or ""
    centers = {value.strip() for value in raw.replace(";", ",").split(",") if value.strip()}
    units = list(user.allowed_centers.values_list("code", "center"))
    codes = {str(code).strip() for code, _ in units if code and str(code).strip()}
    centers.update(str(center).strip() for _, center in units if center and str(center).strip())
    if not centers and not codes:
        return queryset.none()
    return queryset.filter(Q(center__in=centers) | Q(**{f"{job_field}__in": codes}))
