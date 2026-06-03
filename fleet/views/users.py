from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from core.models import CustomUser
from fleet.models import Employee


class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = "fleet/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        users = (
            CustomUser.objects.select_related("employee")
            .prefetch_related("roles", "allowed_centers")
            .order_by("username")
        )
        for user in users:
            role_names = [role.name for role in user.roles.all()]
            center_codes = [
                part.strip()
                for part in (user.allowed_center_codes or "").split(",")
                if part.strip()
            ]
            unit_centers = sorted(
                {
                    str(center or "").strip()
                    for center in user.allowed_centers.values_list("center", flat=True)
                    if str(center or "").strip()
                }
            )
            all_centers = sorted(set(center_codes + unit_centers), key=lambda value: (len(value), value))
            user.roles_display = ", ".join(role_names) or "-"
            user.centers_display = ", ".join(all_centers) or "-"
            user.login_status_display = "Ulazio" if user.last_login else "Nije ulazio"
            user.password_status_display = (
                "Nije promenio inicijalnu lozinku"
                if user.must_change_password
                else "Promenjena / nije obavezna"
            )
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = list(context["users"])
        active_without_profile = list(
            Employee.objects.filter(is_active=True, user_account__isnull=True)
            .order_by("employee_code")
        )
        context.update(
            {
                "title": "Korisnici",
                "total_users": len(users),
                "linked_users": sum(1 for user in users if user.employee_id),
                "users_logged_in": sum(1 for user in users if user.last_login),
                "users_never_logged_in": sum(1 for user in users if not user.last_login),
                "must_change_password_count": sum(1 for user in users if user.must_change_password),
                "changed_password_count": sum(1 for user in users if not user.must_change_password),
                "active_without_profile": active_without_profile,
                "active_without_profile_count": len(active_without_profile),
            }
        )
        return context
