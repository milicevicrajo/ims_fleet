from calendar import monthrange
from datetime import date
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse, QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.cache import never_cache
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell

from core.mixins import role_permission_required, user_has_role_permission
from .access import can_view_all
from .forms import JobMonthForm, ReportFilters, SyncForm
from .models import SyncRun, NalogZRefreshRun
from .services.charts import overview_data
from .services.datatables import ledger_response, sync_response, nalog_z_response
from .services.nalog_z import refresh_nalog_z, TASK_NAME
from .services.reports import apply_filters, base_querysets, grouped_report, summary
from .services.sync import SyncBusy, sync_ledger
from .services import job_tables
from .services.links import job_detail_url
from .services.job_overview import LABELS, METRICS, enrich_jobs, table_data
from .services.job_additional import EXTRA_KEYS, EXTRA_LABELS, enrich_additional, additional_table_data
from .services.excel import prepare_job_sheet, job_excel_row, finish_job_table


logger = logging.getLogger(__name__)


def report_context(request, ledger=False, data=None):
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
    form = ReportFilters(request.GET if data is None else data, jobs=jobs, entries=entries, ledger=ledger)
    valid = form.is_valid()
    selected = apply_filters(entries, form.cleaned_data) if valid else entries.none()
    params = form.data.copy()
    params.pop("page", None)
    if valid:
        for name in ("date_from", "date_to"):
            params[name] = form.cleaned_data[name].isoformat()
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
    if valid and form.cleaned_data.get("job") not in (None, "", "__none__") and user_has_role_permission(request.user, "finansije:dashboard"):
        context["job_detail_url"] = job_detail_url(form.cleaned_data["job"], form.cleaned_data["date_to"])
    return context, selected, jobs


def job_report_parameters(source):
    """Only period and center can filter the all-jobs overview."""
    data = QueryDict(mutable=True)
    for key in ("date_from", "date_to", "center"):
        if key in source:
            data[key] = source[key]
    data.update(group="job", kind="pnl", include_empty="1")
    if source.get('analysis') == 'additional':
        data['analysis'] = 'additional'
    return data


def job_report_links(rows, form):
    add_links(rows, form)
    start, end = form.cleaned_data["date_from"], form.cleaned_data["date_to"]
    if start == date(start.year, 1, 1) and end == date(start.year, 12, 31):
        for row in rows:
            if row["code"]:
                row["card_url"] = reverse("finansije:job_card") + "?" + urlencode({"job": row["code"], "year": start.year, "month": ""})


def enrich_job_report(rows, form):
    covered = set()
    for lower, upper in SyncRun.objects.filter(company=getattr(settings, "FINANSIJE_COMPANY", 1), status="success").values_list("year_from", "year_to"):
        covered.update(range(lower, upper + 1))
    return enrich_jobs(rows, form.cleaned_data["date_from"], form.cleaned_data["date_to"], covered)


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
        row["report_url"] = reverse("finansije:report") + "?" + params.urlencode()
        if group == "job" and row["code"]:
            selected = form.cleaned_data["date_to"]
            row["card_url"] = job_detail_url(row["code"], selected)
        elif group == "month" and form.cleaned_data.get("job") not in (None, "", "__none__"):
            row["card_url"] = job_detail_url(form.cleaned_data["job"], date(year, month, 1))


@require_GET
@login_required
@role_permission_required("finansije:dashboard")
def dashboard(request):
    # Only the selected period changes the landing page; authorization still scopes entries.
    today = timezone.localdate()
    data = QueryDict(mutable=True)
    data.update(date_from=request.GET.get("date_from", date(today.year, 1, 1).isoformat()),
                date_to=request.GET.get("date_to", today.isoformat()), kind="pnl", group="center")
    context, entries, _ = report_context(request, data=data)
    totals = summary(entries)
    context.update(overview_data(entries, totals))
    context.update(totals=totals, period_from=context["form"].cleaned_data.get("date_from"), period_to=context["form"].cleaned_data.get("date_to"))
    context["period_years"] = [
        {"label": year, "date_from": date(year, 1, 1).isoformat(), "date_to": min(date(year, 12, 31), today).isoformat()}
        for year in range(2025, today.year + 1)
    ]
    for group in context["chart_groups"]:
        for row in group["rows"]:
            params = data.copy()
            params[group["dimension"]] = row["code"] or "__none__"
            params["group"] = "job" if group["dimension"] == "center" else "account"
            row["url"] = reverse("finansije:report") + "?" + params.urlencode()
            if group["dimension"] == "job" and row["code"] and context["valid"]:
                selected = context["period_to"]
                row["url"] = job_detail_url(row["code"], selected)
    return render(request, "finansije/overview.html", context)


@require_GET
@login_required
@role_permission_required("finansije:dashboard")
def report(request):
    if request.GET.get("group") == "job":
        context, entries, jobs = report_context(request, data=job_report_parameters(request.GET))
        totals, rows = grouped_report(entries, jobs, context["form"].cleaned_data) if context["valid"] else (summary(entries), [])
        if context["valid"]:
            job_report_links(rows, context["form"])
        context.update(totals=totals, rows=rows, group="job", metric_labels=LABELS,
                       additional_labels=LABELS + EXTRA_LABELS,
                       additional_active=request.GET.get('analysis') == 'additional',
                       table_source=reverse("finansije:jobs_data") + "?" + context["params"] + '&analysis=standard',
                       additional_source=reverse("finansije:jobs_data") + "?" + context["params"] + '&analysis=additional')
        return render(request, "finansije/jobs_overview.html", context)
    context, entries, jobs = report_context(request)
    totals, rows = (grouped_report(entries, jobs, context["form"].cleaned_data) if context["valid"] else (summary(entries), []))
    if context["valid"]:
        add_links(rows, context["form"])
    context.update(totals=totals, rows=rows, group=context["form"].cleaned_data.get("group", "center"))
    return render(request, "finansije/dashboard.html", context)


@never_cache
@require_GET
@login_required
@role_permission_required("finansije:dashboard")
def jobs_data(request):
    context, entries, jobs = report_context(request, data=job_report_parameters(request.GET))
    if not context["valid"]:
        return JsonResponse({"error": "Neispravan period ili centar."}, status=400)
    _, rows = grouped_report(entries, jobs, context["form"].cleaned_data)
    job_report_links(rows, context["form"])
    enrich_job_report(rows, context["form"])
    if request.GET.get('analysis') == 'additional':
        enrich_additional(rows, context['form'].cleaned_data['date_from'], context['form'].cleaned_data['date_to'],
                          can_people=user_has_role_permission(request.user, 'employee_list'))
        return JsonResponse(additional_table_data(rows))
    return JsonResponse(table_data(rows))


@require_GET
@login_required
@role_permission_required("finansije:dashboard")
def job_card(request):
    request.session["current_app"] = "finansije"
    entries, jobs = base_querysets(request.user)
    directory = {j.code: {"name": j.name, "center": j.center} for j in jobs if j.code}
    for code, name, center in entries.order_by().values_list("job_code", "job_name", "center").distinct():
        if code:
            directory.setdefault(code, {"name": name, "center": center})
    form = JobMonthForm(request.GET, choices=[(code, f"{code} — {info['name']}") for code, info in sorted(directory.items())])
    valid = form.is_valid()
    context = {"title": "Detalj šifre posla", "form": form, "valid": valid,
               "can_ledger": user_has_role_permission(request.user, "finansije:ledger")}
    code = form.cleaned_data.get("job") if valid else None
    if code:
        start, end = form.cleaned_data["date_from"], form.cleaned_data["date_to"]
        selected = entries.filter(job_code=code)
        company = getattr(settings, "FINANSIJE_COMPANY", 1)
        runs = SyncRun.objects.filter(company=company, status="success", year_from__lte=start.year, year_to__gte=start.year)
        context.update(job_code=code, job_info=directory[code], period_from=start, period_to=end,
                       finance_available=runs.exists(), today=timezone.localdate())
        context["totals"] = summary(selected.filter(booking_date__range=(start, end)))
        context["table_urls"] = {table: reverse("finansije:job_table", args=[table]) + "?" + urlencode({
            "job": code, "year": start.year, "month": form.cleaned_data["month"] or "",
        }) for table in ("invoices", "internal_invoices", "expenses", "vehicles", "custody", "employees", "travel", "collections", "shared", "cash")}
        context["ledger_url"] = reverse("finansije:ledger") + "?" + urlencode({
            "job": code, "date_from": start.isoformat(), "date_to": end.isoformat(), "kind": "pnl",
        })
        # Existing modules have their own access rules, in addition to the finance job scope.
        context["can_vehicles"] = user_has_role_permission(request.user, "jobcode_list")
        context["can_custody"] = context["can_vehicles"] and user_has_role_permission(request.user, "vehicle_travel_order_list")
        context["can_employees"] = user_has_role_permission(request.user, "employee_list")
        context["can_travel"] = user_has_role_permission(request.user, "putninalog_list")
        context["can_collections"] = job_collections_access(request.user, code)
    return render(request, "finansije/job_card.html", context)


def job_collections_access(user, code):
    from potrazivanja.access import can_view_job
    return can_view_job(user, code, company=getattr(settings, 'FINANSIJE_COMPANY', 1))


@never_cache
@require_GET
@login_required
@role_permission_required("finansije:dashboard")
def job_table(request, table):
    if table not in ("invoices", "internal_invoices", "expenses", "vehicles", "custody", "employees", "travel", "collections", "shared", "cash"):
        return JsonResponse({"error": "Tabela nije pronađena."}, status=404)
    entries, jobs = base_querysets(request.user)
    code = request.GET.get("job", "").strip()
    if not code or len(code) > 10:
        return JsonResponse({"error": "Izaberite šifru posla."}, status=400)
    selected = entries.filter(job_code=code)
    if not jobs.filter(code=code).exists() and not selected.exists():
        return JsonResponse({"error": "Šifra nije dostupna."}, status=404)
    # Validate only the requested, authorized job; no full directory scan on each AJAX call.
    form = JobMonthForm(request.GET, choices=[(code, code)])
    if not form.is_valid():
        return JsonResponse({"error": "Neispravan period."}, status=400)
    start, end = form.cleaned_data["date_from"], form.cleaned_data["date_to"]
    permissions = {"vehicles": "jobcode_list", "travel": "putninalog_list", "employees": "employee_list",
                   "custody": "vehicle_travel_order_list"}
    if table in permissions and not user_has_role_permission(request.user, permissions[table]):
        raise PermissionDenied
    if table == "custody" and not user_has_role_permission(request.user, "jobcode_list"):
        raise PermissionDenied
    if table == "collections":
        if not job_collections_access(request.user, code):
            raise PermissionDenied
    if table in ("invoices", "internal_invoices", "expenses", "shared", "cash") and not SyncRun.objects.filter(
            company=getattr(settings, "FINANSIJE_COMPANY", 1), status="success",
            year_from__lte=start.year, year_to__gte=start.year).exists():
        return JsonResponse({"error": "Nema potvrđenih podataka za ovu godinu."}, status=409)
    try:
        if table in ("invoices", "internal_invoices"):
            data = job_tables.invoice_data(selected, start, end, internal=table == "internal_invoices")
        elif table == "expenses":
            data = job_tables.expense_data(selected, start, end, code, user_has_role_permission(request.user, "finansije:ledger"))
        elif table == "vehicles":
            data = job_tables.vehicle_data(code, start, end)
        elif table == "custody":
            data = job_tables.custody_data(request, code, start, end)
        elif table == "employees":
            data = job_tables.employee_data(code, start, end)
        elif table == "travel":
            data = job_tables.travel_data(request, code, start, end)
        elif table == "shared":
            data = job_tables.shared_data(selected, code, start, end)
        elif table == "cash":
            data = job_tables.cash_data(code, start, end)
        else:
            data = job_tables.collection_data(request.user, code)
    except DatabaseError:
        logger.exception("Tabela detalja šifre posla nije dostupna: %s", table)
        return JsonResponse({"error": "Podaci trenutno nisu dostupni. Pokušajte ponovo."}, status=503)
    return JsonResponse(data)


@require_GET
@login_required
@role_permission_required("finansije:ledger")
def ledger(request):
    context, entries, _ = report_context(request, ledger=True)
    if "draw" in request.GET:
        return ledger_response(request, entries)
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
    is_jobs = not is_ledger and request.GET.get("group") == "job"
    context, entries, jobs = report_context(request, ledger=is_ledger,
                                          data=job_report_parameters(request.GET) if is_jobs else None)
    if not context["valid"]:
        return HttpResponse("Neispravni filteri. Ispravite ih na stranici izveštaja.", status=400, content_type="text/plain; charset=utf-8")
    book = Workbook(write_only=not is_jobs)
    if is_jobs:
        book.remove(book.active)
    sheet = book.create_sheet("Knjiženja" if is_ledger else "Izveštaj")
    sheet.freeze_panes = "A4"
    sheet.append(safe_excel_row(sheet, ["Datum knjiženja", str(context["form"].cleaned_data["date_from"]), str(context["form"].cleaned_data["date_to"]), "Iznosi RSD; analitika bez zatvaranja ZAT i prenosa 59900/69900; sva knjiženja uključuju i te stavke; učešća u filtriranom dostupnom prikazu."]))
    sheet.append(safe_excel_row(sheet, ["Filteri", context["params"]]))
    if is_ledger:
        headers = ["Datum knjiženja", "Godina", "Vrsta", "Broj naloga", "Stavka", "Centar", "Šifra posla", "Naziv posla", "OJ knjiženja", "Konto", "Naziv konta", "Partner", "Naziv partnera", "Veza dokumenta", "Datum dokumenta", "Duguje", "Potražuje", "Valuta", "Devizni iznos", "Opis"]
        fields = ["booking_date", "year", "journal_type", "journal_number", "line_number", "center", "job_code", "job_name", "organizational_unit", "account", "account_name", "partner_code", "partner_name", "document_reference", "document_date", "debit", "credit", "currency", "foreign_amount", "description"]
        records = entries.order_by("booking_date", "pk").values_list(*fields).iterator(chunk_size=2000)
    elif is_jobs:
        _, rows = grouped_report(entries, jobs, context["form"].cleaned_data)
        job_report_links(rows, context["form"])
        enrich_job_report(rows, context["form"])
        labels, keys = LABELS, METRICS
        if request.GET.get('analysis') == 'additional':
            enrich_additional(rows, context['form'].cleaned_data['date_from'], context['form'].cleaned_data['date_to'],
                              can_people=user_has_role_permission(request.user, 'employee_list'))
            labels, keys = LABELS + EXTRA_LABELS, METRICS + EXTRA_KEYS
            for row in rows:
                row['metrics'].update(row['additional'])
        headers = ["Šifra posla", "Naziv", "Centar", *labels, "Napomena o dostupnosti", "Detalj šifre posla"]
        records = ([row["code"], row["label"], row.get("center", ""),
                    *[row["metrics"][key]["value"] for key in keys],
                    " ".join(dict.fromkeys(metric["note"] for metric in row["metrics"].values()
                                           if metric["value"] is None or not metric["complete"])),
                    request.build_absolute_uri(row["card_url"]) if row.get("card_url") else ""] for row in rows)
    else:
        _, rows = grouped_report(entries, jobs, context["form"].cleaned_data)
        headers = ["Šifra / period", "Naziv", "Centar", "Prihodi RSD", "Rashodi RSD", "Rezultat RSD", "Učešće u prihodima %", "Učešće u rashodima %", "Broj knjiženja"]
        records = ([row["code"], row["label"], row.get("center", ""), row["revenue"], row["expense"], row["result"], row["revenue_share"], row["expense_share"], row["count"]] for row in rows)
    if is_jobs:
        prepare_job_sheet(sheet, headers)
        sheet.title = 'Dodatne analize' if request.GET.get('analysis') == 'additional' else 'Šifre posla'
        sheet.append(job_excel_row(sheet, headers, headers, heading=True))
    else:
        sheet.append(safe_excel_row(sheet, headers))
    row_count = 0
    for values in records:
        sheet.append(job_excel_row(sheet, values, headers) if is_jobs else safe_excel_row(sheet, values))
        row_count += 1
    if is_jobs:
        if not row_count:
            # Excel tables retain one empty input row when no records match.
            sheet.append(job_excel_row(sheet, [None] * len(headers), headers))
            row_count = 1
        finish_job_table(sheet, headers, row_count, additional=request.GET.get('analysis') == 'additional')
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    filename = ('finansije_dodatne_analize.xlsx' if request.GET.get('analysis') == 'additional' else 'finansije_sifre_posla.xlsx') if is_jobs else 'finansije.xlsx'
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
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
    if "draw" in request.GET:
        if request.GET.get("source") == "nalog_z":
            return nalog_z_response(request, NalogZRefreshRun.objects.all())
        return sync_response(request, runs)
    from django_celery_beat.models import PeriodicTask
    schedules = PeriodicTask.objects.filter(task=TASK_NAME, enabled=True).select_related("crontab")
    return render(request, "finansije/sync_status.html", {
        "title": "Sinhronizacija finansija", "sync_form": SyncForm(), "nalog_z_schedules": schedules,
    })


@require_POST
@login_required
@role_permission_required("finansije:sync_status")
def sync_run(request):
    if not can_view_all(request.user):
        raise PermissionDenied
    form = SyncForm(request.POST)
    if not form.is_valid():
        status, code, message = "error", 400, "Izaberite tekuću godinu ili sve godine od 2025."
    else:
        try:
            # Manual execution calls the service directly, without a Celery broker.
            run = sync_ledger(**form.sync_years())
        except SyncBusy:
            status, code, message = "busy", 409, "Sinhronizacija je već u toku. Sačekajte završetak i osvežite istoriju."
        except Exception:
            logger.exception("Ručno pokretanje sinhronizacije finansija nije uspelo.")
            status, code, message = "error", 500, "Sinhronizacija nije uspela. Detalje proverite u istoriji sinhronizacije."
        else:
            status, code = "success", 200
            message = (f"Sinhronizacija za {run.year_from}–{run.year_to} je završena. "
                       f"Preuzeto: {run.source_rows}; novo: {run.created}; izmenjeno: {run.updated}; "
                       f"nepromenjeno: {run.unchanged}; uklonjeno: {run.removed}. Kontrolni zbirovi su usaglašeni.")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": status, "message": message}, status=code)
    level = {"success": messages.SUCCESS, "busy": messages.WARNING, "error": messages.ERROR}[status]
    messages.add_message(request, level, message)
    return redirect("finansije:sync_status")


@require_POST
@login_required
@role_permission_required("finansije:sync_status")
def nalog_z_refresh(request):
    if not can_view_all(request.user):
        raise PermissionDenied
    try:
        run = refresh_nalog_z(requested_by=request.user.get_username())
    except SyncBusy:
        status, code, message = "busy", 409, "Osvežavanje nalog_z je već u toku. Sačekajte završetak."
    except Exception:
        logger.exception("Ručno osvežavanje nalog_z nije uspelo.")
        status, code, message = "error", 500, "Osvežavanje nije potvrđeno. Proverite detalje u istoriji procedure."
    else:
        status, code = "success", 200
        message = (f"Lokalni nalog_z je osvežen za {run.year_from}–{run.year_to}. "
                   f"Ažurirano: {run.updated_rows}; dodato: {run.inserted_rows}.")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": status, "message": message}, status=code)
    messages.add_message(request, {"success": messages.SUCCESS, "busy": messages.WARNING,
                                  "error": messages.ERROR}[status], message)
    return redirect("finansije:sync_status")
