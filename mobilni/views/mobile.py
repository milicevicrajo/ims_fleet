import csv
from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from core.exporting import csv_attachment_response, rows_to_xlsx_response
from core.mixins import RolePermissionRequiredMixin, role_permission_required

from ..forms.mobile import (
    MobileAssignmentForm,
    MobilePackageForm,
    MobileParkingExemptionForm,
    MobilePeriodImportForm,
    MobileSimpleImportForm,
    MobileUsageForm,
    MobileUserForm,
)
from ..models import MobileAssignment, MobileImportLog, MobilePackage, MobileParkingExemption, MobileUsage, MobileUser
from ..support.mobile import import_assignments, import_packages, import_usages, import_users, sync_employee_links
from ..withholdings import (
    REPORT_ALL,
    REPORT_EMPLOYEES,
    REPORT_FORMER_EMPLOYEES,
    REPORT_TYPES,
    SPECIAL_PHONE_NUMBER,
    assignment_employee_active,
    assignment_employee_code,
    assignment_employee_name,
    assignment_package_amount,
    assignment_package_name,
    calculate_withholding,
    get_withholding_rows,
    is_parking_exempt,
    normalize_phone_number,
    parking_exempt_phone_numbers,
)


def _periods():
    values = set(
        MobileAssignment.objects.values_list("year", "month")
    ) | set(MobileUsage.objects.values_list("year", "month"))
    return sorted(values, reverse=True)


def _selected_period(request):
    periods = _periods()
    try:
        year = int(request.GET.get("year") or 0)
        month = int(request.GET.get("month") or 0)
    except (TypeError, ValueError):
        year, month = 0, 0
    if year and month:
        return year, month
    return periods[0] if periods else (None, None)


def _period_suffix(year, month):
    return f"{year}_{month:02d}" if year and month else "sve"


def _date(value):
    return value.strftime("%d.%m.%Y") if value else ""


def _decimal(value):
    return float(value or 0)


def _filter_assignments(request):
    qs = MobileAssignment.objects.select_related("package", "employee")
    year, month = _selected_period(request)
    if year and month:
        qs = qs.filter(year=year, month=month)
    phone_number = (request.GET.get("phone_number") or "").strip()
    if phone_number:
        qs = qs.filter(phone_number__icontains=phone_number)
    search = (request.GET.get("q") or "").strip()
    if search:
        query = (
            Q(employee__first_name__icontains=search)
            | Q(employee__last_name__icontains=search)
            | Q(employee__original_full_name__icontains=search)
            | Q(package__name__icontains=search)
            | Q(package__partner_name__icontains=search)
        )
        if search.isdigit():
            query |= Q(employee__employee_code=int(search))
            query |= Q(employee_id=int(search))
        qs = qs.filter(query)
    return qs, year, month


def _usage_report_filters(request):
    year, month = _selected_period(request)
    package_id = request.GET.get("package") or None
    try:
        package_id = int(package_id) if package_id else None
    except (TypeError, ValueError):
        package_id = None
    return {
        "year": year,
        "month": month,
        "phone_number": (request.GET.get("phone_number") or "").strip(),
        "employee": (request.GET.get("employee") or "").strip(),
        "package_id": package_id,
    }


def _filter_packages(request):
    qs = MobilePackage.objects.select_related("contract")
    search = (request.GET.get("q") or "").strip()
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(partner_name__icontains=search)
            | Q(contract__contract_number__icontains=search)
        )
    return qs


def _filter_users(request):
    qs = MobileUser.objects.select_related("employee")
    status = request.GET.get("status") or "active"
    if status not in {"active", "inactive", "all"}:
        status = "active"

    if status == "active":
        qs = qs.filter(is_active=True).filter(Q(employee__isnull=True) | Q(employee__is_active=True))
    elif status == "inactive":
        qs = qs.filter(Q(is_active=False) | Q(employee__is_active=False))

    oj = (request.GET.get("oj") or "").strip()
    if oj:
        qs = qs.filter(organizational_unit=oj)

    hr_link = request.GET.get("hr_link") or "all"
    if hr_link == "linked":
        qs = qs.filter(employee__isnull=False)
    elif hr_link == "unlinked":
        qs = qs.filter(employee__isnull=True)

    search = (request.GET.get("q") or "").strip()
    if search:
        query = (
            Q(full_name__icontains=search)
            | Q(organizational_unit__icontains=search)
        )
        if search.isdigit():
            query |= Q(employee_code=int(search))
            query |= Q(employee_id=int(search))
        qs = qs.filter(query)
    return qs


def _filter_parking_exemptions(request):
    qs = MobileParkingExemption.objects.all()
    search = (request.GET.get("q") or "").strip()
    if search:
        qs = qs.filter(phone_number__icontains=search)
    return qs, search


def _mobile_user_filter_context(request):
    status = request.GET.get("status") or "active"
    if status not in {"active", "inactive", "all"}:
        status = "active"

    hr_link = request.GET.get("hr_link") or "all"
    if hr_link not in {"all", "linked", "unlinked"}:
        hr_link = "all"

    return {
        "status": status,
        "hr_link": hr_link,
        "oj": (request.GET.get("oj") or "").strip(),
        "oj_options": (
            MobileUser.objects.exclude(organizational_unit="")
            .values_list("organizational_unit", flat=True)
            .distinct()
            .order_by("organizational_unit")
        ),
    }


class MobileDashboardView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    template_name = "mobilni/mobile/dashboard.html"
    context_object_name = "usages"

    def get_queryset(self):
        year, month = _selected_period(self.request)
        qs = MobileUsage.objects.select_related("assignment__employee", "assignment__package", "employee")
        if year and month:
            qs = qs.filter(year=year, month=month)
        phone_number = (self.request.GET.get("phone_number") or "").strip()
        if phone_number:
            qs = qs.filter(phone_number__icontains=phone_number)
        search = (self.request.GET.get("q") or "").strip()
        if search:
            query = (
                Q(assignment__employee__first_name__icontains=search)
                | Q(assignment__employee__last_name__icontains=search)
                | Q(assignment__employee__original_full_name__icontains=search)
                | Q(assignment__package__name__icontains=search)
                | Q(employee__first_name__icontains=search)
                | Q(employee__last_name__icontains=search)
            )
            if search.isdigit():
                query |= Q(employee_id=int(search))
                query |= Q(assignment__employee__employee_code=int(search))
            qs = qs.filter(query)
        return qs.order_by("-total", "phone_number")[:15]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        year, month = _selected_period(self.request)
        phone_number = (self.request.GET.get("phone_number") or "").strip()
        parking_exempt_numbers = parking_exempt_phone_numbers(year, month)
        for usage in ctx.get("usages", []):
            usage.parking_exempt = normalize_phone_number(usage.phone_number) in parking_exempt_numbers
        usage_period_qs = MobileUsage.objects.filter(year=year, month=month) if year and month else MobileUsage.objects.none()
        assignment_period_qs = (
            MobileAssignment.objects.filter(year=year, month=month)
            if year and month
            else MobileAssignment.objects.none()
        )
        if phone_number:
            usage_period_qs = usage_period_qs.filter(phone_number__icontains=phone_number)
            assignment_period_qs = assignment_period_qs.filter(phone_number__icontains=phone_number)
        withholding_rows = get_withholding_rows(REPORT_ALL, year=year, month=month, phone_number=phone_number)
        usage_total = sum((row.usage.total for row in withholding_rows), start=Decimal("0"))
        withholding_total = sum(
            (row.withholding for row in withholding_rows if row.withholding is not None),
            start=Decimal("0"),
        )
        institute_total = usage_total - withholding_total
        package_metrics = defaultdict(
            lambda: {
                "package_name": "Bez paketa",
                "phone_numbers": set(),
                "usage_total": Decimal("0"),
                "withholding_total": Decimal("0"),
            }
        )
        for row in withholding_rows:
            package_key = row.usage.assignment.package_id or "bez-paketa"
            metric = package_metrics[package_key]
            metric["package_name"] = row.package_name or "Bez paketa"
            metric["phone_numbers"].add(row.phone_number)
            metric["usage_total"] += row.usage.total
            if row.withholding is not None:
                metric["withholding_total"] += row.withholding
        package_summary = []
        for metric in package_metrics.values():
            metric["number_count"] = len(metric.pop("phone_numbers"))
            metric["institute_total"] = metric["usage_total"] - metric["withholding_total"]
            package_summary.append(metric)
        package_summary.sort(key=lambda item: item["institute_total"], reverse=True)
        contracted_number_count = assignment_period_qs.count()
        active_number_count = assignment_period_qs.filter(number_active=True).count()
        active_number_percent = (
            (active_number_count / contracted_number_count) * 100
            if contracted_number_count
            else 0
        )
        ctx.update(
            {
                "title": "Mobilni telefoni",
                "periods": _periods(),
                "selected_year": year,
                "selected_month": month,
                "assignment_count": contracted_number_count,
                "contracted_number_count": contracted_number_count,
                "active_number_count": active_number_count,
                "active_number_percent": active_number_percent,
                "usage_count": usage_period_qs.count(),
                "usage_total": usage_total,
                "withholding_total": withholding_total,
                "institute_total": institute_total,
                "package_summary": package_summary,
                "latest_imports": MobileImportLog.objects.all()[:8],
                "q": self.request.GET.get("q", ""),
                "phone_number": phone_number,
                "parking_exempt_numbers": parking_exempt_numbers,
            }
        )
        return ctx


class MobileAssignmentListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = MobileAssignment
    template_name = "mobilni/mobile/assignment_list.html"
    context_object_name = "assignments"

    def get_queryset(self):
        qs, _, _ = _filter_assignments(self.request)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        year, month = _selected_period(self.request)
        parking_exempt_numbers = parking_exempt_phone_numbers(year, month)
        for assignment in ctx.get("assignments", []):
            assignment.parking_exempt = normalize_phone_number(assignment.phone_number) in parking_exempt_numbers
        ctx.update(
            {
                "title": "Dodele mobilnih brojeva",
                "periods": _periods(),
                "selected_year": year,
                "selected_month": month,
                "q": self.request.GET.get("q", ""),
                "phone_number": self.request.GET.get("phone_number", ""),
                "parking_exempt_numbers": parking_exempt_numbers,
            }
        )
        return ctx


class MobilePhoneDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "mobilni/mobile/phone_detail.html"
    required_permission_code = "mobilni:mobile_assignment_list"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        raw_phone_number = self.kwargs["phone_number"]
        phone_number = normalize_phone_number(raw_phone_number)
        phone_values = {value for value in {raw_phone_number, phone_number} if value}

        assignments = list(
            MobileAssignment.objects.filter(phone_number__in=phone_values)
            .select_related("package", "employee")
            .order_by("-year", "-month", "-id")
        )
        usages = list(
            MobileUsage.objects.filter(phone_number__in=phone_values)
            .select_related("assignment__package", "assignment__employee", "employee")
            .order_by("-year", "-month", "-id")
        )
        if not assignments and not usages:
            raise Http404("Broj nije pronadjen.")

        exempt_phone_numbers = parking_exempt_phone_numbers()
        for usage in usages:
            usage.parking_exempt = is_parking_exempt(usage, exempt_phone_numbers)
            usage.withholding = calculate_withholding(usage, exempt_phone_numbers)

        current_assignment = assignments[0] if assignments else None
        ctx.update(
            {
                "title": f"Detalj broja {phone_number or raw_phone_number}",
                "phone_number": phone_number or raw_phone_number,
                "assignments": assignments,
                "usages": usages,
                "current_assignment": current_assignment,
                "parking_exempt": normalize_phone_number(raw_phone_number) in exempt_phone_numbers,
            }
        )
        return ctx


class MobileUsageListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = MobileUsage
    template_name = "mobilni/mobile/usage_list.html"
    context_object_name = "usages"

    def get_queryset(self):
        filters = _usage_report_filters(self.request)
        return get_withholding_rows(REPORT_ALL, **filters)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        filters = _usage_report_filters(self.request)
        ctx.update(
            {
                "title": "Potrošnja mobilnih",
                "periods": _periods(),
                "selected_year": filters["year"],
                "selected_month": filters["month"],
                "phone_number": filters["phone_number"],
                "employee_filter": filters["employee"],
                "selected_package": filters["package_id"],
                "package_options": MobilePackage.objects.order_by("name", "valid_from"),
                "withholding_total": sum(
                    (row.withholding for row in ctx["usages"] if row.withholding is not None),
                    start=Decimal("0"),
                ),
            }
        )
        return ctx


class MobilePackageListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = MobilePackage
    template_name = "mobilni/mobile/package_list.html"
    context_object_name = "packages"

    def get_queryset(self):
        return _filter_packages(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Mobilni paketi"
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class MobileUserListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = MobileUser
    template_name = "mobilni/mobile/user_list.html"
    context_object_name = "mobile_users"

    def get_queryset(self):
        return _filter_users(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Korisnici mobilnih"
        ctx["q"] = self.request.GET.get("q", "")
        ctx.update(_mobile_user_filter_context(self.request))
        return ctx


class MobileParkingExemptionListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = MobileParkingExemption
    template_name = "mobilni/mobile/parking_exemption_list.html"
    context_object_name = "parking_exemptions"

    def get_queryset(self):
        qs, _ = _filter_parking_exemptions(self.request)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        _, search = _filter_parking_exemptions(self.request)
        ctx.update(
            {
                "title": "Izuzeci parkinga",
                "q": search,
            }
        )
        return ctx


class MobilePackageCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = MobilePackage
    form_class = MobilePackageForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("mobilni:mobile_package_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi mobilni paket"
        ctx["submit_button_label"] = "Sačuvaj paket"
        return ctx


class MobilePackageUpdateView(MobilePackageCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmeni mobilni paket"
        return ctx


class MobileUserCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = MobileUser
    form_class = MobileUserForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("mobilni:mobile_user_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi korisnik mobilnog"
        ctx["submit_button_label"] = "Sačuvaj korisnika"
        return ctx


class MobileUserUpdateView(MobileUserCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmeni korisnika mobilnog"
        return ctx


class MobileAssignmentCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = MobileAssignment
    form_class = MobileAssignmentForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("mobilni:mobile_assignment_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nova dodela mobilnog broja"
        ctx["submit_button_label"] = "Sačuvaj dodelu"
        return ctx


class MobileAssignmentUpdateView(MobileAssignmentCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmeni dodelu mobilnog broja"
        return ctx


class MobileUsageCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = MobileUsage
    form_class = MobileUsageForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("mobilni:mobile_usage_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nova potrošnja mobilnog"
        ctx["submit_button_label"] = "Sačuvaj potrošnju"
        return ctx


class MobileUsageUpdateView(MobileUsageCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmeni potrošnju mobilnog"
        return ctx


class MobileParkingExemptionCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = MobileParkingExemption
    form_class = MobileParkingExemptionForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("mobilni:mobile_parking_exemption_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi izuzetak parkinga"
        ctx["submit_button_label"] = "Sacuvaj izuzetak"
        ctx["cancel_url"] = reverse_lazy("mobilni:mobile_parking_exemption_list")
        return ctx


class MobileParkingExemptionUpdateView(MobileParkingExemptionCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmeni izuzetak parkinga"
        return ctx


class MobileAssignmentDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = MobileAssignment
    template_name = "mobilni/mobile/confirm_delete.html"
    success_url = reverse_lazy("mobilni:mobile_assignment_list")
    context_object_name = "object"


class MobileUsageDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = MobileUsage
    template_name = "mobilni/mobile/confirm_delete.html"
    success_url = reverse_lazy("mobilni:mobile_usage_list")
    context_object_name = "object"


class MobilePackageDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = MobilePackage
    template_name = "mobilni/mobile/confirm_delete.html"
    success_url = reverse_lazy("mobilni:mobile_package_list")
    context_object_name = "object"


class MobileUserDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = MobileUser
    template_name = "mobilni/mobile/confirm_delete.html"
    success_url = reverse_lazy("mobilni:mobile_user_list")
    context_object_name = "object"


class MobileParkingExemptionDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = MobileParkingExemption
    template_name = "mobilni/mobile/confirm_delete.html"
    success_url = reverse_lazy("mobilni:mobile_parking_exemption_list")
    context_object_name = "object"


class MobileWithholdingReportView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "mobilni/mobile/withholding_report.html"
    report_type = REPORT_ALL

    def get_report_type(self):
        if self.report_type not in REPORT_TYPES:
            raise Http404("Izveštaj ne postoji.")
        return self.report_type

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report_type = self.get_report_type()
        year, month = _selected_period(self.request)
        search = (self.request.GET.get("q") or "").strip()
        phone_number = (self.request.GET.get("phone_number") or "").strip()
        rows = get_withholding_rows(
            report_type,
            year=year,
            month=month,
            search=search,
            phone_number=phone_number,
        )
        paginator = Paginator(rows, 100)
        page_obj = paginator.get_page(self.request.GET.get("page"))
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        total = sum((row.withholding for row in rows if row.withholding is not None), start=0)
        titles = {
            REPORT_ALL: "Detaljni izveštaj obustava",
            REPORT_EMPLOYEES: "Obustave zaposlenih",
            REPORT_FORMER_EMPLOYEES: "Obustave bivših zaposlenih",
        }
        context.update(
            {
                "title": titles[report_type],
                "report_type": report_type,
                "report_all": REPORT_ALL,
                "report_employees": REPORT_EMPLOYEES,
                "report_former_employees": REPORT_FORMER_EMPLOYEES,
                "special_phone_number": SPECIAL_PHONE_NUMBER,
                "rows": page_obj.object_list,
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
                "query_without_page": query_params.urlencode(),
                "periods": _periods(),
                "selected_year": year,
                "selected_month": month,
                "q": search,
                "phone_number": phone_number,
                "row_count": len(rows),
                "withholding_total": total,
            }
        )
        return context


@role_permission_required()
def export_employee_withholdings_csv(request):
    filters = _usage_report_filters(request)
    year = filters["year"]
    month = filters["month"]
    search = (request.GET.get("q") or "").strip()
    rows = get_withholding_rows(
        REPORT_EMPLOYEES,
        **filters,
        search=search,
    )
    suffix = _period_suffix(year, month)
    response = csv_attachment_response(
        f"obustave_zaposleni_{suffix}.csv",
        charset="utf-8",
    )
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";", lineterminator="\r\n")
    writer.writerow(["Godina", "Mesec", "Šifra radnika", "Iznos obustave"])
    for row in rows:
        amount = "" if row.withholding is None else f"{row.withholding:.2f}"
        writer.writerow([row.year, row.month, row.employee_code or "", amount])
    return response


@role_permission_required()
def export_assignments_xlsx(request):
    qs, year, month = _filter_assignments(request)
    parking_exempt_numbers = parking_exempt_phone_numbers(year, month)
    headers = [
        "Godina",
        "Mesec",
        "Broj",
        "Parking izuzet",
        "Aktivan broj",
        "Paket",
        "Paket od",
        "Paket do",
        "Paket neto",
        "ID zaposlenog",
        "Šifra radnika",
        "Radnik",
        "Aktivan radnik",
        "JMBG",
    ]
    rows = [
        [
            item.year,
            item.month,
            item.phone_number,
            "Da" if normalize_phone_number(item.phone_number) in parking_exempt_numbers else "Ne",
            "Da" if item.number_active else "Ne",
            assignment_package_name(item),
            _date(item.package.valid_from if item.package_id else None),
            _date(item.package.valid_to if item.package_id else None),
            _decimal(assignment_package_amount(item)),
            item.employee_id or "",
            assignment_employee_code(item) or "",
            assignment_employee_name(item),
            "Da" if assignment_employee_active(item) else "Ne",
            item.employee.personal_number if item.employee_id else "",
        ]
        for item in qs.order_by("year", "month", "phone_number")
    ]
    return rows_to_xlsx_response(
        f"mobilni_dodele_{_period_suffix(year, month)}.xlsx",
        "Dodele",
        headers,
        rows,
        quoted=True,
        bold_header=True,
        auto_width=True,
    )


@role_permission_required()
def export_usages_xlsx(request):
    filters = _usage_report_filters(request)
    year = filters["year"]
    month = filters["month"]
    report_rows = get_withholding_rows(REPORT_ALL, **filters)
    headers = [
        "Šifra radnika",
        "Korisnik",
        "Paket",
        "Iznos neto",
        "Godina",
        "Mesec",
        "Broj",
        "Parking izuzet",
        "Onnet",
        "U MTS mreži",
        "Van MTS mreže",
        "Ka KIM",
        "Ka specijalnim",
        "Internacionalni",
        "Roaming",
        "GPRS",
        "SMS",
        "SMS internac.",
        "SMS u roamingu",
        "MMS",
        "VAS SMS",
        "Saobraćaj za popust",
        "Fiksni popust",
        "Varijabilni popust",
        "Usluge",
        "Otpremnice",
        "Parking",
        "NZRD",
        "Osnovica za PDV",
        "PDV",
        "Plaćanje na rate",
        "Ukupno za naplatu",
        "Obustava",
    ]
    rows = [
        [
            row.employee_code or "",
            row.employee_name,
            row.package_name,
            _decimal(row.package_net_amount),
            row.year,
            row.month,
            row.phone_number,
            "Da" if row.parking_exempt else "Ne",
            _decimal(row.usage.onnet),
            _decimal(row.usage.mts_network),
            _decimal(row.usage.outside_mts),
            _decimal(row.usage.kim),
            _decimal(row.usage.special),
            _decimal(row.usage.international),
            _decimal(row.usage.roaming),
            _decimal(row.usage.gprs),
            _decimal(row.usage.sms),
            _decimal(row.usage.sms_international),
            _decimal(row.usage.sms_roaming),
            _decimal(row.usage.mms),
            _decimal(row.usage.vas_sms),
            _decimal(row.usage.discount_traffic),
            _decimal(row.usage.fixed_discount),
            _decimal(row.usage.variable_discount),
            _decimal(row.usage.services),
            _decimal(row.usage.dispatch_notes),
            _decimal(row.usage.parking),
            _decimal(row.usage.nzrd),
            _decimal(row.usage.vat_base),
            _decimal(row.usage.vat),
            _decimal(row.usage.installments),
            _decimal(row.usage.total),
            _decimal(row.withholding),
        ]
        for row in report_rows
    ]
    return rows_to_xlsx_response(
        f"mobilni_potrosnja_{_period_suffix(year, month)}.xlsx",
        "Potrošnja",
        headers,
        rows,
        quoted=True,
        bold_header=True,
        auto_width=True,
    )


@role_permission_required()
def export_packages_xlsx(request):
    qs = _filter_packages(request)
    headers = [
        "Šifra partnera",
        "Partner",
        "Paket",
        "Važi od",
        "Važi do",
        "Neto",
        "Bruto",
        "Opis",
        "Godina ugovora",
        "Broj ugovora",
    ]
    rows = [
        [
            item.partner_code,
            item.partner_name,
            item.name,
            _date(item.valid_from),
            _date(item.valid_to),
            _decimal(item.net_amount),
            _decimal(item.gross_amount),
            item.description,
            item.contract.contract_date.year if item.contract_id else "",
            item.contract.contract_number if item.contract_id else "",
        ]
        for item in qs.order_by("name", "valid_from", "id")
    ]
    return rows_to_xlsx_response(
        "mobilni_paketi.xlsx",
        "Paketi",
        headers,
        rows,
        quoted=True,
        bold_header=True,
        auto_width=True,
    )


@role_permission_required()
def export_users_xlsx(request):
    qs = _filter_users(request)
    headers = ["ID zaposlenog", "OJ", "Šifra radnika", "Ime i prezime", "JMBG", "Aktivan", "Datum odlaska"]
    rows = [
        [
            item.employee_id or "",
            item.organizational_unit,
            item.employee_code,
            item.full_name,
            item.personal_number,
            "Da" if item.is_active else "Ne",
            _date(item.departure_date),
        ]
        for item in qs.order_by("full_name", "employee_code")
    ]
    return rows_to_xlsx_response(
        "mobilni_korisnici.xlsx",
        "Korisnici",
        headers,
        rows,
        quoted=True,
        bold_header=True,
        auto_width=True,
    )


@role_permission_required()
def mobile_import_view(request):
    forms = {
        "packages": MobileSimpleImportForm(prefix="packages"),
        "users": MobileSimpleImportForm(prefix="users"),
        "assignments": MobilePeriodImportForm(prefix="assignments"),
        "usages": MobilePeriodImportForm(prefix="usages"),
    }

    if request.method == "POST":
        import_type = request.POST.get("import_type")
        form = forms.get(import_type)
        if form:
            form = form.__class__(request.POST, request.FILES, prefix=import_type)
            forms[import_type] = form
            if form.is_valid():
                return _handle_mobile_import(request, import_type, form)

    return render(
        request,
        "mobilni/mobile/import.html",
        {
            "title": "Import mobilnih podataka",
            "forms": forms,
            "latest_imports": MobileImportLog.objects.all()[:20],
        },
    )


def _handle_mobile_import(request, import_type, form):
    uploaded_file = form.cleaned_data["file"]
    year = int(form.cleaned_data["year"]) if "year" in form.cleaned_data else None
    month = int(form.cleaned_data["month"]) if "month" in form.cleaned_data else None
    importer = {
        "packages": lambda: import_packages(uploaded_file),
        "users": lambda: import_users(uploaded_file),
        "assignments": lambda: import_assignments(uploaded_file, year, month),
        "usages": lambda: import_usages(uploaded_file, year, month),
    }[import_type]

    try:
        result = importer()
        sync_result = sync_employee_links()
        MobileImportLog.objects.create(
            import_type=import_type,
            year=year,
            month=month,
            source_file=uploaded_file.name,
            imported_count=result.imported,
            updated_count=result.updated,
            skipped_count=result.skipped,
            error_message="\n".join(result.errors),
            created_by=request.user,
        )
        messages.success(
            request,
            (
                f"Import završen: novo {result.imported}, ažurirano {result.updated}, "
                f"preskočeno {result.skipped}. Sinhronizacija zaposlenih: "
                f"korisnici {sync_result['mobile_users_linked']}, "
                f"potrošnja {sync_result['usages_employee_linked']}."
            ),
        )
    except Exception as exc:
        MobileImportLog.objects.create(
            import_type=import_type,
            year=year,
            month=month,
            source_file=uploaded_file.name,
            error_message=str(exc),
            created_by=request.user,
        )
        messages.error(request, f"Import nije uspeo: {exc}")

    return redirect("mobilni:mobile_import")
