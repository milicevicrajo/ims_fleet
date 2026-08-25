import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Sum
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
    search = (request.GET.get("q") or "").strip()
    if search:
        query = (
            Q(phone_number__icontains=search)
            | Q(employee_name__icontains=search)
            | Q(package_name__icontains=search)
        )
        if search.isdigit():
            query |= Q(employee_code=int(search))
            query |= Q(employee_id=int(search))
        qs = qs.filter(query)
    return qs, year, month


def _filter_usages(request):
    qs = MobileUsage.objects.select_related("assignment", "employee")
    year, month = _selected_period(request)
    if year and month:
        qs = qs.filter(year=year, month=month)
    search = (request.GET.get("q") or "").strip()
    if search:
        query = (
            Q(phone_number__icontains=search)
            | Q(assignment__employee_name__icontains=search)
            | Q(employee__first_name__icontains=search)
            | Q(employee__last_name__icontains=search)
        )
        if search.isdigit():
            query |= Q(employee_id=int(search))
        qs = qs.filter(query)
    return qs, year, month


def _filter_packages(request):
    qs = MobilePackage.objects.all()
    search = (request.GET.get("q") or "").strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(partner_name__icontains=search))
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
        search = (self.request.GET.get("q") or "").strip()
        if search:
            query = (
                Q(phone_number__icontains=search)
                | Q(assignment__employee_name__icontains=search)
                | Q(assignment__package_name__icontains=search)
                | Q(employee__first_name__icontains=search)
                | Q(employee__last_name__icontains=search)
            )
            if search.isdigit():
                query |= Q(employee_id=int(search))
            qs = qs.filter(query)
        return qs.order_by("-total", "phone_number")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        year, month = _selected_period(self.request)
        usage_period_qs = MobileUsage.objects.filter(year=year, month=month) if year and month else MobileUsage.objects.none()
        assignment_period_qs = (
            MobileAssignment.objects.filter(year=year, month=month)
            if year and month
            else MobileAssignment.objects.none()
        )
        ctx.update(
            {
                "title": "Mobilni telefoni",
                "periods": _periods(),
                "selected_year": year,
                "selected_month": month,
                "assignment_count": assignment_period_qs.count(),
                "active_number_count": assignment_period_qs.filter(number_active=True).count(),
                "usage_count": usage_period_qs.count(),
                "usage_total": usage_period_qs.aggregate(total=Sum("total"))["total"] or 0,
                "latest_imports": MobileImportLog.objects.all()[:8],
                "q": self.request.GET.get("q", ""),
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
            }
        )
        return ctx


class MobileUsageListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = MobileUsage
    template_name = "mobilni/mobile/usage_list.html"
    context_object_name = "usages"

    def get_queryset(self):
        qs, _, _ = _filter_usages(self.request)
        return qs.order_by("-total", "phone_number")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        year, month = _selected_period(self.request)
        ctx.update(
            {
                "title": "Potrosnja mobilnih",
                "periods": _periods(),
                "selected_year": year,
                "selected_month": month,
                "q": self.request.GET.get("q", ""),
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
        ctx["submit_button_label"] = "Sacuvaj paket"
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
        ctx["submit_button_label"] = "Sacuvaj korisnika"
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
        ctx["submit_button_label"] = "Sacuvaj dodelu"
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
        ctx["title"] = "Nova potrosnja mobilnog"
        ctx["submit_button_label"] = "Sacuvaj potrosnju"
        return ctx


class MobileUsageUpdateView(MobileUsageCreateView, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmeni potrosnju mobilnog"
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
            raise Http404("Izvestaj ne postoji.")
        return self.report_type

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report_type = self.get_report_type()
        year, month = _selected_period(self.request)
        search = (self.request.GET.get("q") or "").strip()
        rows = get_withholding_rows(
            report_type,
            year=year,
            month=month,
            search=search,
        )
        paginator = Paginator(rows, 100)
        page_obj = paginator.get_page(self.request.GET.get("page"))
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        total = sum((row.withholding for row in rows if row.withholding is not None), start=0)
        titles = {
            REPORT_ALL: "Detaljni izvestaj obustava",
            REPORT_EMPLOYEES: "Obustave zaposlenih",
            REPORT_FORMER_EMPLOYEES: "Obustave bivsih zaposlenih",
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
                "row_count": len(rows),
                "withholding_total": total,
            }
        )
        return context


@role_permission_required()
def export_employee_withholdings_csv(request):
    year, month = _selected_period(request)
    search = (request.GET.get("q") or "").strip()
    rows = get_withholding_rows(
        REPORT_EMPLOYEES,
        year=year,
        month=month,
        search=search,
    )
    suffix = _period_suffix(year, month)
    response = csv_attachment_response(
        f"obustave_zaposleni_{suffix}.csv",
        charset="utf-8",
    )
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";", lineterminator="\r\n")
    writer.writerow(["Godina", "Mesec", "Sifra radnika", "Iznos obustave"])
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
        "Sifra radnika",
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
    qs, year, month = _filter_usages(request)
    headers = [
        "Godina",
        "Mesec",
        "Broj",
        "ID zaposlenog",
        "Korisnik",
        "Onnet",
        "U MTS mrezi",
        "Van MTS mreze",
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
        "Saobracaj za popust",
        "Fiksni popust",
        "Varijabilni popust",
        "Usluge",
        "Otpremnice",
        "Parking",
        "NZRD",
        "Osnovica za PDV",
        "PDV",
        "Placanje na rate",
        "Ukupno za naplatu",
    ]
    rows = [
        [
            item.year,
            item.month,
            item.phone_number,
            item.employee_id or "",
            (
                item.assignment.employee_name
                if item.assignment
                else str(item.employee or "")
            ),
            _decimal(item.onnet),
            _decimal(item.mts_network),
            _decimal(item.outside_mts),
            _decimal(item.kim),
            _decimal(item.special),
            _decimal(item.international),
            _decimal(item.roaming),
            _decimal(item.gprs),
            _decimal(item.sms),
            _decimal(item.sms_international),
            _decimal(item.sms_roaming),
            _decimal(item.mms),
            _decimal(item.vas_sms),
            _decimal(item.discount_traffic),
            _decimal(item.fixed_discount),
            _decimal(item.variable_discount),
            _decimal(item.services),
            _decimal(item.dispatch_notes),
            _decimal(item.parking),
            _decimal(item.nzrd),
            _decimal(item.vat_base),
            _decimal(item.vat),
            _decimal(item.installments),
            _decimal(item.total),
        ]
        for item in qs.order_by("year", "month", "phone_number")
    ]
    return rows_to_xlsx_response(
        f"mobilni_potrosnja_{_period_suffix(year, month)}.xlsx",
        "Potrosnja",
        headers,
        rows,
        quoted=True,
        bold_header=True,
        auto_width=True,
    )


@role_permission_required()
def export_packages_xlsx(request):
    qs = _filter_packages(request)
    headers = ["Sifra partnera", "Partner", "Paket", "Vazi od", "Vazi do", "Neto", "Bruto", "Opis"]
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
    headers = ["ID zaposlenog", "OJ", "Sifra radnika", "Ime i prezime", "JMBG", "Aktivan", "Datum odlaska"]
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
                f"Import zavrsen: novo {result.imported}, azurirano {result.updated}, "
                f"preskoceno {result.skipped}. Sync zaposlenih: "
                f"korisnici {sync_result['mobile_users_linked']}, "
                f"dodele {sync_result['assignments_employee_linked']}, "
                f"potrosnja {sync_result['usages_employee_linked']}."
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
