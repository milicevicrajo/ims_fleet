from calendar import monthrange
from datetime import date

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell

from core.mixins import role_permission_required, user_has_role_permission
from .access import can_view_all
from .forms import ReportFilters
from .models import SyncRun
from .services.reports import apply_filters, base_querysets, grouped_report, summary


def report_context(request, ledger=False):
    request.session["current_app"] = "finansije"
    company = getattr(settings, "FINANSIJE_COMPANY", 1)
    runs = SyncRun.objects.filter(company=company)
    latest_success = runs.filter(status="success").first()
    last_run = runs.first()
    entries, jobs = base_querysets(request.user)
    if latest_success is None and last_run is not None and last_run.status == "running":
        # The initial import holds write locks on the new tables until validation.
        # Render a useful empty state instead of waiting on those locks.
        entries, jobs = entries.none(), jobs.none()
    form = ReportFilters(request.GET, jobs=jobs, entries=entries, ledger=ledger)
    valid = form.is_valid()
    selected = apply_filters(entries, form.cleaned_data) if valid else entries.none()
    params = form.data.copy()
    params.pop("page", None)
    context = {
        "title": "Finansijska analitika", "form": form, "valid": valid,
        "params": params.urlencode(), "is_ledger": ledger,
        "last_success": latest_success,
        "sync_failed": last_run is not None and last_run.status == "failed",
        "sync_running": last_run is not None and last_run.status == "running",
        "restricted": not can_view_all(request.user),
        "can_export": user_has_role_permission(request.user, "finansije:export"),
        "can_sync_status": can_view_all(request.user) and user_has_role_permission(request.user, "finansije:sync_status"),
    }
    if valid and latest_success:
        start_year, end_year = form.cleaned_data["date_from"].year, form.cleaned_data["date_to"].year
        covered = set()
        for lower, upper in runs.filter(status="success").values_list("year_from", "year_to"):
            covered.update(range(lower, upper + 1))
        context["missing_years"] = sorted(set(range(start_year, end_year + 1)) - covered)
    return context, selected, jobs


def add_links(rows, form):
    group = form.cleaned_data["group"]
    for row in rows:
        params = form.data.copy()
        params.pop("page", None)
        if group == "month":
            year, month = map(int, row["code"].split("-"))
            params["date_from"] = max(form.cleaned_data["date_from"], date(year, month, 1)).isoformat()
            params["date_to"] = min(form.cleaned_data["date_to"], date(year, month, monthrange(year, month)[1])).isoformat()
        else:
            params[{"center": "center", "job": "job", "account": "account"}[group]] = row["code"] or "__none__"
            if group == "account":
                params["account_exact"] = "1"
        row["ledger_url"] = reverse("finansije:ledger") + "?" + params.urlencode()
        params["group"] = "job" if group == "center" else "account"
        row["report_url"] = reverse("finansije:dashboard") + "?" + params.urlencode()


@require_GET
@login_required
@role_permission_required("finansije:dashboard")
def dashboard(request):
    context, entries, jobs = report_context(request)
    totals, rows = (grouped_report(entries, jobs, context["form"].cleaned_data) if context["valid"] else (summary(entries), []))
    if context["valid"]:
        add_links(rows, context["form"])
    context.update(totals=totals, rows=rows, group=context["form"].cleaned_data.get("group", "center"))
    return render(request, "finansije/dashboard.html", context)


@require_GET
@login_required
@role_permission_required("finansije:ledger")
def ledger(request):
    context, entries, _ = report_context(request, ledger=True)
    context["totals"] = summary(entries)
    context["movements"] = entries.aggregate(debit=Sum("debit"), credit=Sum("credit"))
    context["page_obj"] = Paginator(entries.order_by("-booking_date", "year", "journal_type", "journal_number", "line_number"), 100).get_page(request.GET.get("page"))
    return render(request, "finansije/ledger.html", context)


def safe_excel_row(sheet, values):
    cells = []
    for value in values:
        cell = WriteOnlyCell(sheet, value=value)
        if isinstance(value, str):
            cell.data_type = "s"  # External names/references must never become formulas.
        cells.append(cell)
    return cells


@require_GET
@login_required
@role_permission_required("finansije:export")
def export(request):
    is_ledger = request.GET.get("report") == "ledger"
    required = "finansije:ledger" if is_ledger else "finansije:dashboard"
    if not user_has_role_permission(request.user, required):
        raise PermissionDenied
    context, entries, jobs = report_context(request, ledger=is_ledger)
    if not context["valid"]:
        return HttpResponse("Neispravni filteri. Ispravite ih na stranici izveštaja.", status=400, content_type="text/plain; charset=utf-8")
    book = Workbook(write_only=True)
    sheet = book.create_sheet("Knjiženja" if is_ledger else "Izveštaj")
    sheet.freeze_panes = "A4"
    sheet.append(safe_excel_row(sheet, ["Datum knjiženja", str(context["form"].cleaned_data["date_from"]), str(context["form"].cleaned_data["date_to"]), "Iznosi RSD; direktna knjiženja; učešća u filtriranom dostupnom prikazu."]))
    sheet.append(safe_excel_row(sheet, ["Filteri", context["params"]]))
    if is_ledger:
        headers = ["Datum knjiženja", "Godina", "Vrsta", "Broj naloga", "Stavka", "Centar", "Šifra posla", "Naziv posla", "OJ knjiženja", "Konto", "Naziv konta", "Partner", "Naziv partnera", "Veza dokumenta", "Datum dokumenta", "Duguje", "Potražuje", "Valuta", "Devizni iznos", "Opis"]
        fields = ["booking_date", "year", "journal_type", "journal_number", "line_number", "center", "job_code", "job_name", "organizational_unit", "account", "account_name", "partner_code", "partner_name", "document_reference", "document_date", "debit", "credit", "currency", "foreign_amount", "description"]
        records = entries.order_by("booking_date", "pk").values_list(*fields).iterator(chunk_size=2000)
    else:
        _, rows = grouped_report(entries, jobs, context["form"].cleaned_data)
        headers = ["Šifra / period", "Naziv", "Centar", "Prihodi RSD", "Rashodi RSD", "Rezultat RSD", "Učešće u prihodima %", "Učešće u rashodima %", "Broj knjiženja"]
        records = ([row["code"], row["label"], row.get("center", ""), row["revenue"], row["expense"], row["result"], row["revenue_share"], row["expense_share"], row["count"]] for row in rows)
    sheet.append(safe_excel_row(sheet, headers))
    for values in records:
        sheet.append(safe_excel_row(sheet, values))
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="finansije.xlsx"'
    book.save(response)
    return response


@require_GET
@login_required
@role_permission_required("finansije:sync_status")
def sync_status(request):
    if not can_view_all(request.user):
        raise PermissionDenied
    request.session["current_app"] = "finansije"
    runs = SyncRun.objects.filter(company=getattr(settings, "FINANSIJE_COMPANY", 1))
    return render(request, "finansije/sync_status.html", {"title": "Sinhronizacija finansija", "page_obj": Paginator(runs, 30).get_page(request.GET.get("page"))})
