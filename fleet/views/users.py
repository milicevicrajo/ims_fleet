from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from core.mixins import RolePermissionRequiredMixin
from core.models import ActivityLog, CustomUser
from fleet.models import Employee
from fleet.services.employee_user_profiles import (
    create_user_profile_for_employee,
    create_user_profiles_for_missing_employees,
)


def _require_superuser(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise PermissionDenied("Samo superuser moze da upravlja korisnickim profilima.")


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
        unlinked_users = [user for user in users if not user.employee_id]
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
                "can_manage_user_profiles": self.request.user.is_superuser,
                "link_employee_options": active_without_profile,
                "unlinked_users_count": len(unlinked_users),
            }
        )
        return context


@login_required
@require_POST
def link_user_employee_view(request):
    _require_superuser(request)
    user_id = request.POST.get("user_id")
    employee_id = request.POST.get("employee_id")
    account = get_object_or_404(CustomUser, pk=user_id)
    employee = get_object_or_404(Employee, pk=employee_id, is_active=True)

    if account.employee_id:
        messages.error(request, f"Korisnik {account.username} je vec povezan sa zaposlenim.")
        return redirect("user_list")
    if CustomUser.objects.filter(employee=employee).exclude(pk=account.pk).exists():
        messages.error(request, f"Zaposleni {employee} vec ima korisnicki profil.")
        return redirect("user_list")

    account.employee = employee
    if not account.first_name:
        account.first_name = employee.first_name or ""
    if not account.last_name:
        account.last_name = employee.last_name or ""
    account.save(update_fields=["employee", "first_name", "last_name"])
    messages.success(request, f"Korisnik {account.username} je povezan sa zaposlenim {employee}.")
    return redirect("user_list")


@login_required
@require_POST
def create_employee_user_profile_view(request, pk):
    _require_superuser(request)
    employee = get_object_or_404(Employee, pk=pk, is_active=True, user_account__isnull=True)
    try:
        user, _center, _reason = create_user_profile_for_employee(employee)
    except Exception as exc:
        messages.error(request, f"Profil za {employee} nije kreiran: {exc}")
    else:
        messages.success(
            request,
            f"Kreiran je korisnicki profil {user.username} za {employee}. Inicijalna lozinka je JMBG ili ims{employee.employee_code}.",
        )
    return redirect("user_list")


@login_required
@require_POST
def create_missing_employee_user_profiles_view(request):
    _require_superuser(request)
    created, skipped = create_user_profiles_for_missing_employees()
    if created:
        messages.success(request, f"Kreirano korisnickih profila: {len(created)}.")
    if skipped:
        messages.warning(request, f"Preskoceno zaposlenih: {len(skipped)}.")
    if not created and not skipped:
        messages.info(request, "Nema aktivnih zaposlenih bez korisnickog profila.")
    return redirect("user_list")


class ActivityLogListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = ActivityLog
    template_name = "fleet/activity_log_list.html"
    context_object_name = "logs"
    paginate_by = 100
    required_permission_code = "activity_log_list"

    def get_queryset(self):
        queryset = ActivityLog.objects.select_related("user").order_by("-created_at", "-id")
        params = self.request.GET

        q = (params.get("q") or "").strip()
        if q:
            queryset = queryset.filter(
                Q(actor_username__icontains=q)
                | Q(actor_display_name__icontains=q)
                | Q(description__icontains=q)
                | Q(path__icontains=q)
                | Q(view_name__icontains=q)
                | Q(object_model__icontains=q)
                | Q(object_pk__icontains=q)
                | Q(object_repr__icontains=q)
                | Q(ip_address__icontains=q)
            )

        user_id = params.get("user") or ""
        if user_id.isdigit():
            queryset = queryset.filter(user_id=user_id)

        action = params.get("action") or ""
        if action:
            queryset = queryset.filter(action=action)

        app_label = (params.get("app") or "").strip()
        if app_label:
            queryset = queryset.filter(app_label=app_label)

        status = (params.get("status") or "").strip()
        if status.isdigit():
            queryset = queryset.filter(status_code=int(status))

        date_from = parse_date(params.get("from") or "")
        if date_from:
            start = timezone.make_aware(datetime.combine(date_from, time.min))
            queryset = queryset.filter(created_at__gte=start)

        date_to = parse_date(params.get("to") or "")
        if date_to:
            end = timezone.make_aware(datetime.combine(date_to, time.max))
            queryset = queryset.filter(created_at__lte=end)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        params = self.request.GET.copy()
        params.pop("page", None)
        context.update(
            {
                "title": "Activity log",
                "filters": self.request.GET,
                "querystring": params.urlencode(),
                "user_options": CustomUser.objects.order_by("username").only("id", "username", "first_name", "last_name"),
                "action_options": ActivityLog.ACTION_CHOICES,
                "app_options": (
                    ActivityLog.objects.exclude(app_label="")
                    .values_list("app_label", flat=True)
                    .distinct()
                    .order_by("app_label")
                ),
                "total_logs": ActivityLog.objects.count(),
                "today_logs": ActivityLog.objects.filter(created_at__date=today).count(),
                "failed_logs": ActivityLog.objects.filter(action=ActivityLog.ACTION_LOGIN_FAILED).count(),
            }
        )
        return context
