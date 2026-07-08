from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin
from fleet.models import PutniNalog

from .services.virman import build_virman_file


def parse_payment_date(value):
    value = (value or "").strip()
    if not value:
        return None
    parsed = parse_date(value)
    if parsed:
        return parsed
    try:
        return timezone.datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        return None


class IsplataNeoporezovanihView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "isplate/neoporezive_isplate.html"

    def get_queryset(self):
        return (
            PutniNalog.objects.select_related(
                "employee",
                "job_code",
                "vehicle",
                "virman_generated_by",
            )
            .filter(storniran=False, advance_payment__gt=0)
            .filter(advance_payment_currency="RSD")
            .order_by("-order_date", "-id")
        )

    def apply_filters(self, qs, include_status=True):
        if include_status:
            status = self.request.GET.get("status", "pending")
            if status == "pending":
                qs = qs.filter(virman_generated=False)
            elif status == "generated":
                qs = qs.filter(virman_generated=True)

        center = self.request.GET.get("center", "").strip()
        if center:
            qs = qs.filter(job_code__center=center)

        year = self.request.GET.get("year", "").strip()
        if year.isdigit():
            qs = qs.filter(order_date__year=int(year))

        month = self.request.GET.get("month", "").strip()
        if month.isdigit():
            qs = qs.filter(order_date__month=int(month))

        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(
                Q(order_number__icontains=search)
                | Q(employee__first_name__icontains=search)
                | Q(employee__last_name__icontains=search)
                | Q(employee__original_full_name__icontains=search)
                | Q(employee__account_number__icontains=search)
                | Q(other_employee_name__icontains=search)
                | Q(travel_location__icontains=search)
                | Q(job_code__code__icontains=search)
            )

        return qs

    def post(self, request, *args, **kwargs):
        action = request.POST.get("virman_action", "selected")
        allow_regenerate = request.POST.get("allow_regenerate") == "1"
        payment_date = parse_payment_date(request.POST.get("payment_date"))
        if not payment_date:
            messages.error(request, "Izaberi datum virmana.")
            return redirect(request.get_full_path())

        qs = self.get_queryset().select_related("employee", "job_code")
        if action == "selected":
            selected_ids = request.POST.getlist("order_ids")
            try:
                selected_ids = [int(selected_id) for selected_id in selected_ids]
            except (TypeError, ValueError):
                messages.error(request, "Izabrani nalozi nisu ispravni.")
                return redirect(request.get_full_path())

            orders = list(
                qs.filter(pk__in=selected_ids)
                .order_by("employee__last_name", "employee__first_name", "id")
            )

            if len(orders) != len(set(selected_ids)):
                messages.error(request, "Neki izabrani nalozi nisu dostupni ili nisu dozvoljeni za isplatu.")
                return redirect(request.get_full_path())
        elif action == "pending_for_date":
            orders = list(
                self.apply_filters(qs, include_status=False)
                .filter(virman_generated=False)
                .order_by("employee__last_name", "employee__first_name", "id")
            )
            allow_regenerate = False
        else:
            messages.error(request, "Nepoznata akcija generisanja virmana.")
            return redirect(request.get_full_path())


        generated_at = timezone.now()
        try:
            virman_file = build_virman_file(
                orders,
                payment_date=payment_date,
                generated_at=generated_at,
                allow_regenerate=allow_regenerate,
            )
        except ValidationError as exc:
            for message in exc.messages:
                messages.error(request, message)
            return redirect(request.get_full_path())

        with transaction.atomic():
            PutniNalog.objects.filter(pk__in=[order.pk for order in orders]).update(
                virman_generated=True,
                virman_generated_at=generated_at,
                virman_generated_by=request.user,
            )

        response = HttpResponse(virman_file.bytes, content_type="text/plain; charset=windows-1250")
        response["Content-Disposition"] = f'attachment; filename="{virman_file.filename}"'
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = self.get_queryset()
        filtered_qs = self.apply_filters(base_qs)

        centers = (
            base_qs.exclude(job_code__center__isnull=True)
            .values_list("job_code__center", flat=True)
            .distinct()
            .order_by("job_code__center")
        )
        years = (
            base_qs.exclude(order_date__isnull=True)
            .values_list("order_date__year", flat=True)
            .distinct()
            .order_by("-order_date__year")
        )

        total_amount = filtered_qs.aggregate(total=Sum("advance_payment"))["total"] or 0
        missing_account_count = filtered_qs.filter(
            Q(employee__isnull=True)
            | Q(employee__account_number__isnull=True)
            | Q(employee__account_number="")
        ).count()

        context.update(
            {
                "title": "Isplata neoporezovanih",
                "orders": filtered_qs[:500],
                "status": self.request.GET.get("status", "pending"),
                "allow_regenerate": self.request.GET.get("status") == "generated",
                "selected_center": self.request.GET.get("center", "").strip(),
                "selected_year": self.request.GET.get("year", "").strip(),
                "selected_month": self.request.GET.get("month", "").strip(),
                "search_query": self.request.GET.get("q", "").strip(),
                "centers": centers,
                "years": years,
                "months": range(1, 13),
                "payment_date": timezone.localdate().strftime("%d.%m.%Y"),
                "orders_count": filtered_qs.count(),
                "total_amount": total_amount,
                "missing_account_count": missing_account_count,
            }
        )
        return context
