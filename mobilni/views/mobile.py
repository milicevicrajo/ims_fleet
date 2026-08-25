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
    MobilePeriodImportForm,
    MobileSimpleImportForm,
    MobileUsageForm,
    MobileUserForm,
)
from ..models import MobileAssignment, MobileImportLog, MobilePackage, MobileUsage, MobileUser
from ..support.mobile import import_assignments, import_packages, import_usages, import_users, sync_employee_links
from ..withholdings import (
    REPORT_ALL,
    REPORT_EMPLOYEES,
    REPORT_FORMER_EMPLOYEES,
    REPORT_TYPES,
    get_withholding_rows,
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
    qs = MobileAssignment.objects.select_related("package", "mobile_user", "employee")
    year, month = _selected_period(request)
    if year and month:
        qs = qs.filter(year=year, month=month)
    phone_number = (request.GET.get("phone_number") or "").strip()
    if phone_number:
        qs = qs.filter(phone_number__icontains=phone_number)
    search = (request.GET.get("q") or "").strip()
    if search:
        query = (
            Q(employee_name__icontains=search)
            | Q(package_name__icontains=search)
        )
        if search.isdigit():
            query |= Q(employee_code=int(search))
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
        qs = MobileUsage.objects.select_related("assignment", "employee")
        if year and month:
            qs = qs.filter(year=year, month=month)
        phone_number = (self.request.GET.get("phone_number") or "").strip()
        if phone_number:
            qs = qs.filter(phone_number__icontains=phone_number)
        search = (self.request.GET.get("q") or "").strip()
        if search:
            query = (
                Q(assignment__employee_name__icontains=search)
                | Q(assignment__package_name__icontains=search)
                | Q(employee__first_name__icontains=search)
                | Q(employee__last_name__icontains=search)
            )
            if search.isdigit():
                query |= Q(employee_id=int(search))
            qs = qs.filter(query)
        return qs.order_by("-total", "phone_number")[:15]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        year, month = _selected_period(self.request)
        phone_number = (self.request.GET.get("phone_number") or "").strip()
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
            package_key = row.usage.assignment.package_id or row.package_name or "bez-paketa"
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
        ctx.update(
            {
                "title": "Dodele mobilnih brojeva",
                "periods": _periods(),
                "selected_year": year,
                "selected_month": month,
                "q": self.request.GET.get("q", ""),
                "phone_number": self.request.GET.get("phone_number", ""),
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
    headers = [
        "Godina",
        "Mesec",
        "Broj",
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
        "Napomena",
    ]
    rows = [
        [
            item.year,
            item.month,
            item.phone_number,
            "Da" if item.number_active else "Ne",
            item.package_name or str(item.package or ""),
            _date(item.valid_from),
            _date(item.valid_to),
            _decimal(item.package_net_amount),
            item.employee_id or "",
            item.employee_code or "",
            item.employee_name,
            "Da" if item.employee_active else "Ne",
            item.personal_number,
            item.note,
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
                f"dodele {sync_result['assignments_employee_linked']}, "
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
