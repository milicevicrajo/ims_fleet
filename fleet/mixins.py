from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from functools import wraps

from .models import OrganizationalUnit


class CenterMixin:
    """
    Mixin koji konzistentno filtrira queryset po dozvoljenim centrima
    ili pojedinačnim organizacionim jedinicama.

    Konfiguriše se preko:
    - center_field: polje na modelu koje sadrži kod centra (npr. "organizational_unit__center")
    - org_unit_field: polje na modelu koje je FK ka OrganizationalUnit (npr. "organizational_unit")
    """

    center_field = None
    org_unit_field = None
    allow_if_no_scope = True

    def get_user_allowed_center_codes(self):
        raw = (self.request.user.allowed_center_codes or "").strip()
        if not raw:
            return []
        parts = [p.strip() for p in raw.replace(";", ",").split(",")]
        return [p for p in parts if p]

    def get_user_allowed_units(self):
        return self.request.user.allowed_centers.all()

    def apply_center_scope(self, qs):
        user = self.request.user
        if user.is_superuser:
            return qs

        allowed_units = self.get_user_allowed_units()
        allowed_center_codes = self.get_user_allowed_center_codes()

        if not allowed_units.exists() and not allowed_center_codes:
            return qs if self.allow_if_no_scope else qs.none()

        if self.org_unit_field:
            if allowed_center_codes:
                units_from_centers = OrganizationalUnit.objects.filter(
                    center__in=allowed_center_codes
                )
                allowed_units = units_from_centers.union(allowed_units)
            return qs.filter(**{f"{self.org_unit_field}__in": allowed_units}).distinct()

        if self.center_field:
            return qs.filter(**{f"{self.center_field}__in": allowed_center_codes}).distinct()

        return qs

    def get_queryset(self):
        qs = super().get_queryset()
        return self.apply_center_scope(qs)


# Backwards-compatible alias
CenterScopedMixin = CenterMixin


class RoleRequiredMixin(UserPassesTestMixin):
    """
    Blanko mixin za role. Očekuje da view postavi `required_roles` (lista slug-ova uloga).
    """

    required_roles = []
    raise_exception = True
    default_roles = ["uprava"]
    use_default_roles_if_empty = True

    def get_required_roles(self):
        if self.required_roles:
            return self.required_roles
        if self.use_default_roles_if_empty:
            return self.default_roles
        return []

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        required_roles = self.get_required_roles()
        if not required_roles:
            return False
        user_role_slugs = set(
            self.request.user.roles.values_list("slug", flat=True)
        )
        return bool(user_role_slugs.intersection(set(required_roles)))

    def handle_no_permission(self):
        raise PermissionDenied("Nemate potrebnu ulogu za pristup.")


class AnyRoleRequiredMixin(RoleRequiredMixin):
    """
    Alias za RoleRequiredMixin radi jasnijeg imenovanja u view-ovima.
    """

    pass


class RolePermissionRequiredMixin(UserPassesTestMixin):
    """
    Provera dozvole preko custom uloga i RolePermission (role.permissions).
    View može da postavi `required_permission_code`.
    Ako nije postavljeno, koristi `request.resolver_match.view_name`.
    """

    required_permission_code = None
    raise_exception = True

    def get_permission_code(self):
        if self.required_permission_code:
            return self.required_permission_code
        match = getattr(self.request, "resolver_match", None)
        if match and match.view_name:
            return match.view_name
        return None

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        permission_code = self.get_permission_code()
        if not permission_code:
            return False
        return self.request.user.roles.filter(
            permissions__code=permission_code,
            is_active=True,
        ).exists()

    def handle_no_permission(self):
        raise PermissionDenied("Nemate potrebnu dozvolu za pristup.")


def user_has_role_permission(user, permission_code):
    if user.is_superuser:
        return True
    if not permission_code:
        return False
    return user.roles.filter(
        permissions__code=permission_code,
        is_active=True,
    ).exists()


def role_permission_required(permission_code=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            code = permission_code
            if not code:
                match = getattr(request, "resolver_match", None)
                code = match.view_name if match else None
            if not user_has_role_permission(request.user, code):
                raise PermissionDenied("Nemate potrebnu dozvolu za pristup.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
