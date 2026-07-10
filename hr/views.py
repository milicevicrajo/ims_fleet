import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission

from .forms import (
    EmployeeCVItemForm,
    EmployeeForm,
    EmployeeNameCorrectionForm,
    WORK_TIME_SHEET_DAY_FIELDS,
    WORK_TIME_SHEET_LINE_COUNT,
    WorkTimeSheetForm,
    WorkTimeSheetLineFormSet,
)
from .models import Employee, EmployeeCVItem, WorkTimeSheet, WorkTimeSheetLine
from .querysets import employee_list_queryset
from .services.attendance import calculate_daily_hours_from_clock_events, get_clock_events, month_period
from .sync import sync_employees_from_hr_view


def _collect_user_activities(user):
    if not user:
        return []

    from nabavka.models import (
        ProcurementCase,
        ProcurementContractLink,
        ProcurementInvoiceContractLink,
        ProcurementInvoiceLink,
        ProcurementItemInvoiceLink,
        ProcurementStatusLog,
        PurchaseOrder,
    )
    from naplata.models import AvansKlijent, Postupak, PromenaPostupka
    from ugovori.models import BusinessRequest, Offer, Partner

    activities = []

    def append_items(queryset, category, description=None):
        for item in queryset:
            activities.append(
                {
                    "created_at": item.created_at,
                    "category": category,
                    "reference": str(item),
                    "description": description(item) if description else "",
                }
            )

    append_items(
        ProcurementCase.objects.filter(created_by=user),
        "Zahtev za nabavku i uslugu",
        lambda item: item.get_status_display(),
    )
    append_items(
        PurchaseOrder.objects.filter(created_by=user),
        "Narudzbenica",
        lambda item: item.get_status_display(),
    )
    append_items(
        ProcurementStatusLog.objects.filter(created_by=user).select_related("procurement_case"),
        "Promena statusa zahteva",
        lambda item: f"{item.get_old_status_display() or '-'} -> {item.get_new_status_display()}",
    )
    append_items(
        ProcurementInvoiceLink.objects.filter(created_by=user).select_related("procurement_case"),
        "Povezivanje fakture",
    )
    append_items(
        ProcurementItemInvoiceLink.objects.filter(created_by=user).select_related("invoice", "procurement_item"),
        "Povezivanje stavke fakture",
    )
    append_items(
        ProcurementContractLink.objects.filter(created_by=user).select_related("contract", "procurement_case"),
        "Povezivanje ugovora",
    )
    append_items(
        ProcurementInvoiceContractLink.objects.filter(created_by=user).select_related("invoice", "contract"),
        "Povezivanje fakture i ugovora",
    )
    append_items(Partner.objects.filter(created_by=user), "Partner")
    append_items(
        BusinessRequest.objects.filter(created_by=user),
        "Poslovni zahtev",
        lambda item: item.get_status_display(),
    )
    append_items(
        Offer.objects.filter(created_by=user),
        "Ponuda",
        lambda item: item.get_status_display(),
    )
    append_items(AvansKlijent.objects.filter(created_by=user), "Avans klijent")
    append_items(
        Postupak.objects.filter(created_by=user),
        "Pravni postupak",
        lambda item: item.get_tip_display(),
    )
    append_items(
        PromenaPostupka.objects.filter(created_by=user).select_related("postupak"),
        "Promena pravnog postupka",
    )

    return sorted(activities, key=lambda item: item["created_at"], reverse=True)


def _employee_detail_context(employee, *, is_self_profile=False):
    from fleet.models import Incident, PutniNalog, VehicleTravelOrder
    from ugovori.models import Contract

    travel_orders = (
        PutniNalog.objects.filter(employee=employee)
        .select_related("vehicle", "job_code")
        .order_by("-order_date", "-id")
    )
    vehicle_travel_orders = (
        VehicleTravelOrder.objects.filter(employee=employee)
        .select_related("vehicle")
        .order_by("-created_at", "-id")
    )
    incidents = (
        Incident.objects.filter(employee=employee)
        .select_related("vehicle")
        .order_by("-date", "-id")
    )
    work_time_sheets = list(
        employee.work_time_sheets.select_related("meal_organizational_unit")
        .prefetch_related("lines")
        .order_by("-year", "-month")
    )
    month_labels = MyWorkTimeSheetView.MONTH_LABELS if "MyWorkTimeSheetView" in globals() else []
    for sheet in work_time_sheets:
        sheet.month_label = month_labels[sheet.month - 1] if month_labels and 1 <= sheet.month <= 12 else sheet.month
    cv_items = employee.cv_items.all()
    linked_user = getattr(employee, "user_account", None)

    contracts = (
        Contract.objects.filter(parties__partner__external_sif_par=employee.employee_code)
        .select_related("contract_type")
        .prefetch_related("parties__partner")
        .distinct()
        .order_by("-contract_date", "-id")
    )

    activities = _collect_user_activities(linked_user)
    return {
        "employee": employee,
        "title": str(employee),
        "is_self_profile": is_self_profile,
        "linked_user": linked_user,
        "cv_items": cv_items,
        "cv_items_count": cv_items.count(),
        "travel_orders": travel_orders,
        "travel_orders_count": travel_orders.count(),
        "vehicle_travel_orders": vehicle_travel_orders,
        "vehicle_travel_orders_count": vehicle_travel_orders.count(),
        "work_time_sheets": work_time_sheets,
        "work_time_sheets_count": len(work_time_sheets),
        "incidents": incidents,
        "incidents_count": incidents.count(),
        "contracts": contracts,
        "contracts_count": contracts.count(),
        "activities": activities,
        "activities_count": len(activities),
    }


class EmployeeListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = Employee
    template_name = "hr/employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        show_inactive = self.request.GET.get("inactive") == "1"
        return employee_list_queryset(show_inactive=show_inactive)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista zaposlenih"
        context["show_inactive"] = self.request.GET.get("inactive") == "1"
        context["can_sync_employees"] = user_has_role_permission(
            self.request.user,
            "employee_sync",
        )
        return context


@login_required
@require_POST
@role_permission_required("employee_sync")
def employee_sync_view(request):
    try:
        result = sync_employees_from_hr_view()
    except Exception as exc:
        messages.error(request, f"Sinhronizacija zaposlenih nije uspela: {exc}")
    else:
        messages.success(
            request,
            "Sinhronizacija zaposlenih zavrsena. "
            f"Ukupno: {result['total']}, "
            f"Kreirano: {result['created']}, "
            f"Azurirano: {result['updated']}, "
            f"Azurirano neaktivnih: {result['updated_inactive']}, "
            f"Preskoceno neaktivnih: {result['skipped_inactive']}.",
        )
    return redirect("employee_list")


class EmployeeCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("employee_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiraj novog zaposlenog"
        context["submit_button_label"] = "Dodaj zaposlenog"
        return context


class EmployeeUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("employee_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni podatke zaposlenog"
        context["submit_button_label"] = "Sacuvaj izmene"
        return context


class EmployeeDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Employee
    template_name = "hr/employee_detail.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_employee_detail_context(self.object))
        return context


class MyEmployeeProfileView(LoginRequiredMixin, TemplateView):
    template_name = "hr/employee_detail.html"

    def get_template_names(self):
        if not self.request.user.employee_id:
            return ["hr/my_profile_unlinked.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.employee_id:
            context.update(
                _employee_detail_context(
                    self.request.user.employee,
                    is_self_profile=True,
                )
            )
        return context


class MyEmployeeNameCorrectionView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeNameCorrectionForm
    template_name = "hr/name_correction_form.html"

    def get_object(self, queryset=None):
        if not self.request.user.employee_id:
            raise PermissionDenied("Korisnicki nalog nije povezan sa zaposlenim.")
        return self.request.user.employee

    def get_success_url(self):
        return reverse("my_employee_profile")


class OwnEmployeeCVMixin(LoginRequiredMixin):
    def get_employee(self):
        if not self.request.user.employee_id:
            raise PermissionDenied("Korisnicki nalog nije povezan sa zaposlenim.")
        return self.request.user.employee

    def get_queryset(self):
        return EmployeeCVItem.objects.filter(employee=self.get_employee())

    def get_success_url(self):
        return f"{reverse('my_employee_profile')}#cv"


class EmployeeCVItemCreateView(OwnEmployeeCVMixin, CreateView):
    model = EmployeeCVItem
    form_class = EmployeeCVItemForm
    template_name = "hr/cv_item_form.html"

    def form_valid(self, form):
        form.instance.employee = self.get_employee()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dodaj CV stavku"
        return context


class EmployeeCVItemUpdateView(OwnEmployeeCVMixin, UpdateView):
    model = EmployeeCVItem
    form_class = EmployeeCVItemForm
    template_name = "hr/cv_item_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni CV stavku"
        return context


class EmployeeCVItemDeleteView(OwnEmployeeCVMixin, DeleteView):
    model = EmployeeCVItem
    template_name = "hr/cv_item_confirm_delete.html"


class MyWorkTimeSheetView(LoginRequiredMixin, TemplateView):
    template_name = "hr/work_time_sheet.html"
    MONTH_LABELS = [
        "Januar",
        "Februar",
        "Mart",
        "April",
        "Maj",
        "Jun",
        "Jul",
        "Avgust",
        "Septembar",
        "Oktobar",
        "Novembar",
        "Decembar",
    ]

    def get_employee(self):
        if not self.request.user.employee_id:
            raise PermissionDenied("Korisnicki nalog nije povezan sa zaposlenim.")
        return self.request.user.employee

    def get_period(self):
        today = timezone.localdate()
        source = self.request.POST if self.request.method == "POST" else self.request.GET
        try:
            month = int(source.get("month") or today.month)
            year = int(source.get("year") or today.year)
        except (TypeError, ValueError):
            month = today.month
            year = today.year

        if month < 1 or month > 12:
            month = today.month
        if year < 2000 or year > 2100:
            year = today.year
        return year, month

    def get_sheet(self, employee, year, month):
        sheet, created = WorkTimeSheet.objects.get_or_create(
            employee=employee,
            year=year,
            month=month,
            defaults={"created_by": self.request.user, "updated_by": self.request.user},
        )
        existing_line_numbers = set(sheet.lines.values_list("line_number", flat=True))
        missing_lines = [
            WorkTimeSheetLine(sheet=sheet, line_number=line_number)
            for line_number in range(1, WORK_TIME_SHEET_LINE_COUNT + 1)
            if line_number not in existing_line_numbers
        ]
        if missing_lines:
            WorkTimeSheetLine.objects.bulk_create(missing_lines)
        return sheet

    def build_clock_attendance_context(self, employee, year, month, days_in_month):
        try:
            date_from, date_to, _last_day = month_period(year, month)
            clock_events = get_clock_events(
                date_from=date_from,
                date_to=date_to,
                employee_code=employee.employee_code,
            )
            daily_hours, issues = calculate_daily_hours_from_clock_events(clock_events)
        except DatabaseError as exc:
            return {
                "clock_attendance_error": str(exc),
                "clock_attendance_rows": [],
                "clock_attendance_summary": {
                    "event_count": 0,
                    "day_count": 0,
                    "total_label": "0:00",
                    "issue_count": 0,
                },
            }

        daily_by_date = {item.date: item for item in daily_hours}
        notes_by_date = {}
        for issue in issues:
            notes_by_date.setdefault(issue.date, []).append(issue)

        rows = []
        total_minutes = 0
        for day in range(1, days_in_month + 1):
            work_date = date(year, month, day)
            item = daily_by_date.get(work_date)
            day_notes = notes_by_date.get(work_date, [])
            day_problems = [note for note in day_notes if note.is_problem]
            total_minutes += item.total_minutes if item else 0

            if day_problems:
                status = "Problem"
                status_class = "problem"
            elif item and item.pair_count:
                status = "OK"
                status_class = "ok"
            else:
                status = "Nema prolaza"
                status_class = "empty"

            issue_messages = []
            for issue in day_notes:
                issue_time = issue.event_time.strftime("%H:%M") if hasattr(issue.event_time, "strftime") else issue.event_time
                issue_messages.append(f"{issue_time} - {issue.message}")

            rows.append(
                {
                    "day": day,
                    "date": work_date,
                    "weekday": work_date.strftime("%a"),
                    "is_weekend": calendar.weekday(year, month, day) >= 5,
                    "hours_label": f"{item.hours}:{item.minutes:02d}" if item else "0:00",
                    "decimal_label": f"{item.total_hours:.2f}" if item else "0.00",
                    "pair_count": item.pair_count if item else 0,
                    "issue_count": len(day_problems),
                    "status": status,
                    "status_class": status_class,
                    "issue_messages": issue_messages,
                }
            )

        return {
            "clock_attendance_error": None,
            "clock_attendance_rows": rows,
            "clock_attendance_summary": {
                "event_count": len(clock_events),
                "day_count": len([item for item in daily_hours if item.pair_count or item.issue_count]),
                "total_label": f"{total_minutes // 60}:{total_minutes % 60:02d}",
                "issue_count": len([issue for issue in issues if issue.is_problem]),
            },
        }

    def build_context(self, *, header_form=None, line_formset=None):
        employee = self.get_employee()
        year, month = self.get_period()
        sheet = self.get_sheet(employee, year, month)
        days_in_month = calendar.monthrange(year, month)[1]
        if header_form is None:
            header_form = WorkTimeSheetForm(instance=sheet)
        if line_formset is None:
            line_formset = WorkTimeSheetLineFormSet(
                instance=sheet,
                queryset=sheet.lines.order_by("line_number"),
            )
        attendance_context = self.build_clock_attendance_context(employee, year, month, days_in_month)

        context = {
            "title": "Radna lista",
            "sidebar_template": "sidebar_kadrovi.html",
            "employee": employee,
            "sheet": sheet,
            "header_form": header_form,
            "line_formset": line_formset,
            "day_fields": [
                {
                    "day": day,
                    "field": field_name,
                    "active": day <= days_in_month,
                    "is_weekend": day <= days_in_month and calendar.weekday(year, month, day) >= 5,
                }
                for day, field_name in enumerate(WORK_TIME_SHEET_DAY_FIELDS, start=1)
            ],
            "month": month,
            "year": year,
            "month_name": self.MONTH_LABELS[month - 1],
            "days_in_month": days_in_month,
            "available_years": range(timezone.localdate().year - 2, timezone.localdate().year + 2),
            "available_months": [
                {"value": index, "label": label}
                for index, label in enumerate(self.MONTH_LABELS, start=1)
            ],
        }
        context.update(attendance_context)
        return context

    def get_context_data(self, **kwargs):
        header_form = kwargs.pop("header_form", None)
        line_formset = kwargs.pop("line_formset", None)
        context = super().get_context_data(**kwargs)
        context.update(self.build_context(header_form=header_form, line_formset=line_formset))
        return context

    def post(self, request, *args, **kwargs):
        employee = self.get_employee()
        year, month = self.get_period()
        sheet = self.get_sheet(employee, year, month)
        action = request.POST.get("action") or "save"
        header_form = WorkTimeSheetForm(request.POST, instance=sheet)
        line_formset = WorkTimeSheetLineFormSet(
            request.POST,
            instance=sheet,
            queryset=sheet.lines.order_by("line_number"),
        )

        if header_form.is_valid() and line_formset.is_valid():
            days_in_month = calendar.monthrange(year, month)[1]
            saved_sheet = header_form.save(commit=False)
            saved_sheet.employee = employee
            saved_sheet.year = year
            saved_sheet.month = month
            if action == "submit_print":
                saved_sheet.status = WorkTimeSheet.Status.SUBMITTED
            saved_sheet.updated_by = request.user
            if saved_sheet.created_by_id is None:
                saved_sheet.created_by = request.user
            saved_sheet.save()

            lines = line_formset.save(commit=False)
            for index, line in enumerate(lines, start=1):
                line.sheet = saved_sheet
                if not line.line_number:
                    line.line_number = index
                for day in range(days_in_month + 1, 32):
                    setattr(line, f"day_{day}", None)
                line.save()
            if action == "submit_print":
                return redirect("hr:work_time_sheet_print", pk=saved_sheet.pk)
            messages.success(request, "Radna lista je sacuvana.")
            return redirect(f"{reverse('hr:work_time_sheet')}?month={month}&year={year}")

        context = self.get_context_data(header_form=header_form, line_formset=line_formset)
        return self.render_to_response(context)


class WorkTimeSheetPrintView(LoginRequiredMixin, TemplateView):
    template_name = "hr/work_time_sheet_print.html"
    MONTH_LABELS = MyWorkTimeSheetView.MONTH_LABELS

    def get_sheet(self):
        sheet = get_object_or_404(
            WorkTimeSheet.objects.select_related("employee", "meal_organizational_unit")
            .prefetch_related("lines__organizational_unit"),
            pk=self.kwargs["pk"],
        )
        can_print_other = self.request.user.is_superuser or user_has_role_permission(self.request.user, "employee_list")
        if sheet.employee_id != self.request.user.employee_id and not can_print_other:
            raise PermissionDenied("Mozes stampati samo svoju radnu listu.")
        return sheet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sheet = self.get_sheet()
        days_in_month = calendar.monthrange(sheet.year, sheet.month)[1]
        lines = list(sheet.lines.all())
        working_days = sum(
            1
            for day in range(1, days_in_month + 1)
            if calendar.weekday(sheet.year, sheet.month, day) < 5
        )
        day_fields = [
            {
                "day": day,
                "field": f"day_{day}",
                "active": day <= days_in_month,
                "is_weekend": day <= days_in_month and calendar.weekday(sheet.year, sheet.month, day) >= 5,
                "total": sum((getattr(line, f"day_{day}") or 0) for line in lines),
            }
            for day in range(1, 32)
        ]
        context.update(
            {
                "sheet": sheet,
                "employee": sheet.employee,
                "lines": lines,
                "day_fields": day_fields,
                "month_name": self.MONTH_LABELS[sheet.month - 1],
                "days_in_month": days_in_month,
                "working_days": working_days,
            }
        )
        return context


class EmployeeDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy("employee_list")
    template_name = "hr/employee_confirm_delete.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obrisi zaposlenog"
        return context
