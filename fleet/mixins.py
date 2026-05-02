from core.mixins import (
    AnyRoleRequiredMixin,
    RolePermissionRequiredMixin,
    RoleRequiredMixin,
    role_permission_required,
    user_has_role_permission,
)

from core.models import OrganizationalUnit


class CenterMixin:
    """
    Mixin koji konzistentno filtrira queryset po dozvoljenim centrima
    ili pojedinacnim organizacionim jedinicama.

    Konfigurise se preko:
    - center_field: polje na modelu koje sadrzi kod centra (npr. "organizational_unit__center")
    - org_unit_field: polje na modelu koje je FK ka OrganizationalUnit (npr. "organizational_unit")
    """

    center_field = None
    org_unit_field = None
    allow_if_no_scope = True

    def get_user_allowed_center_codes(self):
        raw = (self.request.user.allowed_center_codes or "").strip()
        if not raw:
            return []
        parts = [part.strip() for part in raw.replace(";", ",").split(",")]
        return [part for part in parts if part]

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
            allowed_unit_ids = allowed_units.values_list("pk", flat=True)
            if allowed_center_codes:
                units_from_centers = OrganizationalUnit.objects.filter(
                    center__in=allowed_center_codes
                ).values_list("pk", flat=True)
                allowed_unit_ids = units_from_centers.union(allowed_unit_ids)
            return qs.filter(**{f"{self.org_unit_field}__in": allowed_unit_ids}).distinct()

        if self.center_field:
            return qs.filter(**{f"{self.center_field}__in": allowed_center_codes}).distinct()

        return qs

    def get_queryset(self):
        qs = super().get_queryset()
        return self.apply_center_scope(qs)


CenterScopedMixin = CenterMixin
