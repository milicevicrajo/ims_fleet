"""Bounded, permission-scoped DataTables responses; database-native ordering."""
from datetime import datetime

from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import format_html

from finansije.templatetags.finance import amount_badge
from core.mixins import user_has_role_permission
from .links import job_detail_url


def integer(params, name, default):
    try:
        return int(params.get(name, default))
    except (TypeError, ValueError):
        return default


def response(request, queryset, columns, row_builder, search_filter):
    total = queryset.count()
    term = request.GET.get("search[value]", "").strip()[:200]
    if term:
        queryset = queryset.filter(search_filter(term))
    filtered = queryset.count() if term else total
    ordering = []
    # Accept only our column map, never field names supplied by the browser.
    for index in range(len(columns)):
        column = integer(request.GET, f"order[{index}][column]", -1)
        if 0 <= column < len(columns):
            prefix = "-" if request.GET.get(f"order[{index}][dir]") == "desc" else ""
            ordering.extend(prefix + field for field in columns[column])
    queryset = queryset.order_by(*(ordering or ["-" + columns[0][0]]), "pk")
    start = max(integer(request.GET, "start", 0), 0)
    length = max(1, min(integer(request.GET, "length", 50), 200))
    return JsonResponse({
        "draw": max(integer(request.GET, "draw", 0), 0),
        "recordsTotal": total, "recordsFiltered": filtered,
        "data": [row_builder(row) for row in queryset[start:start + length]],
    })


def two_lines(main, detail):
    return format_html('{}<br><small class="text-muted">{}</small>', main or "—", detail or "")


def display_date(value, with_time=False):
    if not value:
        return "—"
    if with_time and timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%d.%m.%Y. %H:%M:%S" if with_time else "%d.%m.%Y.")


def ledger_response(request, entries):
    can_detail = user_has_role_permission(request.user, "finansije:dashboard")
    columns = [
        ("booking_date",), ("year", "journal_type", "journal_number", "line_number"),
        ("center",), ("job_code",), ("organizational_unit",), ("account",),
        ("partner_name", "partner_code"), ("document_reference",), ("document_date",),
        ("debit",), ("credit",),
    ]

    def search(term):
        query = Q()
        for field in ("journal_type", "center", "job_code", "job_name", "organizational_unit_name", "account", "account_name", "partner_name", "document_reference", "description"):
            query |= Q(**{f"{field}__icontains": term})
        if term.isdecimal() and len(term) <= 9:
            query |= Q(journal_number=int(term)) | Q(organizational_unit=int(term)) | Q(partner_code=int(term))
        for pattern in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                selected_date = datetime.strptime(term.rstrip("."), pattern).date()
            except ValueError:
                continue
            query |= Q(booking_date=selected_date) | Q(document_date=selected_date)
        return query

    def row(item):
        job_label = item.job_code
        if job_label and can_detail:
            job_label = format_html('<a href="{}" title="Detalj šifre posla">{}</a>',
                                    job_detail_url(item.job_code, item.booking_date), item.job_code)
        return [
            display_date(item.booking_date),
            two_lines(f"{item.year}/{item.journal_type}/{item.journal_number}", f"Stavka {item.line_number}"),
            format_html('<span class="finance-code-badge">{}</span>', item.center or "—"),
            two_lines(job_label, item.job_name),
            format_html('<span title="{}">{}</span>', item.organizational_unit_name, item.organizational_unit),
            two_lines(item.account, item.account_name), two_lines(item.partner_name, item.partner_code),
            two_lines(item.document_reference, item.description), display_date(item.document_date),
            amount_badge(item.debit), amount_badge(item.credit),
        ]

    return response(request, entries, columns, row, search)


def sync_response(request, runs):
    columns = [("started_at",), ("finished_at",), ("year_from", "year_to"), ("status",),
               ("source_rows",), ("created",), ("updated",), ("unchanged",), ("removed",)]

    def search(term):
        query = Q(status__icontains=term) | Q(error__icontains=term)
        for code, label in runs.model.STATUS:
            if term.casefold() in label.casefold():
                query |= Q(status=code)
        if term.isdecimal() and len(term) == 4:
            query |= Q(year_from=int(term)) | Q(year_to=int(term))
        for pattern in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                day = datetime.strptime(term.rstrip("."), pattern).date()
            except ValueError:
                continue
            query |= Q(started_at__date=day) | Q(finished_at__date=day)
        return query

    def row(item):
        color = {"success": "success", "failed": "danger", "running": "info"}.get(item.status, "secondary")
        status = format_html('<span class="badge bg-{}">{}</span>', color, item.get_status_display())
        if item.error:
            status = format_html('{}<details class="finance-sync-error"><summary>Detalji greške</summary><div>{}</div></details>', status, item.error)
        return [display_date(item.started_at, True), display_date(item.finished_at, True),
                f"{item.year_from}–{item.year_to}", status,
                item.source_rows, item.created, item.updated, item.unchanged, item.removed]

    return response(request, runs, columns, row, search)


def nalog_z_response(request, runs):
    columns = [("started_at",), ("finished_at",), ("trigger", "requested_by"),
               ("year_from", "year_to"), ("status",), ("updated_rows",), ("inserted_rows",)]

    def search(term):
        query = Q(requested_by__icontains=term) | Q(error__icontains=term) | Q(status__icontains=term)
        for code, label in runs.model.STATUS:
            if term.casefold() in label.casefold():
                query |= Q(status=code)
        return query

    def row(item):
        color = {"success": "success", "failed": "danger", "running": "info",
                 "skipped": "warning", "unknown": "warning"}[item.status]
        status = format_html('<span class="badge bg-{}">{}</span>', color, item.get_status_display())
        if item.error:
            status = format_html('{}<details><summary>Detalji</summary><div>{}</div></details>', status, item.error)
        duration = f"{(item.finished_at - item.started_at).total_seconds():.1f} s" if item.finished_at else ""
        return [display_date(item.started_at, True), two_lines(display_date(item.finished_at, True), duration),
                two_lines(item.get_trigger_display(), item.requested_by),
                f"{item.year_from}–{item.year_to}" if item.year_from else "—", status,
                item.updated_rows if item.updated_rows is not None else "—",
                item.inserted_rows if item.inserted_rows is not None else "—"]

    return response(request, runs, columns, row, search)
