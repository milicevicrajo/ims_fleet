from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

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
    Blanko mixin za role. Očekuje da view postavi `required_roles` (lista naziva grupa).
    """

    required_roles = []
    raise_exception = True

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        if not self.required_roles:
            return True
        user_group_names = set(
            self.request.user.groups.values_list("name", flat=True)
        )
        return bool(user_group_names.intersection(set(self.required_roles)))

    def handle_no_permission(self):
        raise PermissionDenied("Nemate potrebnu ulogu za pristup.")


class AnyRoleRequiredMixin(RoleRequiredMixin):
    """
    Alias za RoleRequiredMixin radi jasnijeg imenovanja u view-ovima.
    """

    pass
