"""AJAX data for the bounded monthly tables, with raw ordering values."""
from datetime import date
from decimal import Decimal

from django.utils.html import format_html
from django.utils.formats import number_format
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from potrazivanja.services.reports import job_balances, AGING_TONES

from finansije.templatetags.finance import amount_badge, expense_badge
from .job_card import assigned_vehicles, monthly_expenses, monthly_invoices, vehicle_custody
from .job_people import payroll_employees
from .reports import summary
from .shared_costs import shared_cost
from .cash_flow import cash_flow


def cell(value, display=None):
    raw = "" if value is None else str(value)
    return {"display": str(format_html("{}", raw) if display is None else display), "sort": raw, "filter": raw}


def money(value):
    return cell(value, amount_badge(value))


def day(value):
    result = cell(value.isoformat() if value else "", value.strftime("%d.%m.%Y.") if value else "—")
    result["filter"] = f'{result["sort"]} {result["display"]}'
    return result


def invoice_data(entries, start, end, *, internal=False):
    invoices = monthly_invoices(entries, start, end, internal=internal)
    journal_type = "ON" if internal else "IF"
    rows = []
    for item in invoices:
        document_date = day(item["date"])
        if item["date"] != item["last_date"]:
            document_date["display"] = str(format_html('{}<br><small>Više datuma: do {}</small>',
                document_date["display"], item["last_date"].strftime("%d.%m.%Y.")))
        rows.append([document_date, cell(item["document_reference"] or "Bez veze dokumenta"),
                     cell(f'{item["year"]}/{journal_type}/{item["journal_number"]}'),
                     cell(f'{item["partner_code"] or "—"} · {item["partner_name"]}'), money(item["amount"])])
    total = sum((item["amount"] or Decimal("0") for item in invoices), Decimal("0"))
    footer_key = "internal_invoice_amount" if internal else "invoice_amount"
    return {"data": rows, "footer": {footer_key: str(amount_badge(total))}}


def expense_data(entries, start, end, code, can_ledger):
    rows = []
    for item in monthly_expenses(entries, start, end, code):
        share = cell(item["share"], number_format(item["share"], decimal_pos=2) + "%" if item["share"] is not None else "—")
        link = format_html('<a href="{}">Knjiženja</a>', item["url"]) if can_ledger else "—"
        rows.append([cell(item["knt3"]), money(-item["amount"]), share, cell(item["count"]), cell("", link)])
    return {"data": rows}


def vehicle_data(code, start, end):
    return {"data": [[cell(r["plate"]), cell(r["name"]), day(r["assigned"]), day(r["from"]), day(r["to"])]
                     for r in assigned_vehicles(code, start, end)]}


def custody_data(request, code, start, end):
    rows = []
    for item in vehicle_custody(request, code, start, end):
        order = item["order"]
        status = "Zatvoreno" if order.closed_at else "Otvoreno"
        badge = format_html('<span class="badge {}">{}</span>',
                            "bg-secondary" if order.closed_at else "bg-success", status)
        rows.append([day(order.created_at), cell(order.rbz or order.pn_number),
                     cell(item["plate"]), cell(item["name"]),
                     cell(f"{order.employee.employee_code} · {order.employee}"),
                     day(order.closed_at), day(item["from"]), day(item["to"]), cell(status, badge)])
    return {"data": rows}


def employee_data(code, start, end):
    result = payroll_employees(getattr(settings, "FINANSIJE_COMPANY", 1), code, start, end)
    records, rows = result["rows"], []
    for month, employee_code, name, runs in records:
        period = cell(date(start.year, month, 1).isoformat(), f"{month:02d}.{start.year}.")
        period["filter"] = f'{period["sort"]} {period["display"]}'
        rows.append([period, cell(employee_code), cell(name or "Ime nije dostupno"), cell(runs)])
    missing = sorted(set(range(start.month, end.month + 1)) - set(result["closed_months"]))
    if not result["closed_months"]:
        coverage = "Za izabrani period nema zaključenih obračuna zarada. Broj zaposlenih nije potvrđen."
    elif missing:
        coverage = "Nepotpun obuhvat: nema zaključenih obračuna za mesece " + ", ".join(f"{m:02d}.{start.year}." for m in missing)
    else:
        coverage = "Zaključeni obračuni postoje za sve mesece izabranog perioda."
    if result["open_months"]:
        coverage += " Otvoreni obračuni nisu uključeni (" + ", ".join(f"{m:02d}.{start.year}." for m in result["open_months"]) + ")."
    return {"data": rows, "footer": {
        "employee_count": str(len({r[1] for r in records})) if result["closed_months"] else "—",
        "payroll_coverage": str(format_html("{}", coverage)),
    }}


def travel_data(request, code, start, end):
    from fleet.views.putni_nalozi import _putninalog_base_qs
    rows = []
    orders = _putninalog_base_qs(request).filter(job_code__code=code, travel_date__range=(start, end)).order_by("travel_date", "pk")
    for item in orders:
        employee = str(item.employee) if item.employee else item.other_employee_name or "—"
        vehicle = f"{item.vehicle.brand} {item.vehicle.model} · {item.vehicle.chassis_number}" if item.vehicle else item.other_vehicle or "—"
        rows.append([day(item.travel_date), cell(item.order_number), cell(employee), cell(item.travel_location),
                     cell(vehicle), cell(item.number_of_days)])
    return {"data": rows}


def collection_data(user, code):
    report = job_balances(user, code, company=getattr(settings, 'FINANSIJE_COMPANY', 1))
    snapshot = report['snapshot']
    if not snapshot:
        return {'data': [], 'available': False, 'footer': {
            'collections_as_of': 'Potraživanja još nemaju uspešan snimak podataka. Iznosi nisu dostupni.'}}
    rows = []
    for record in report['rows']:
        label = f"{record['partner_code']} · {record['partner_name']}"
        url = reverse('potrazivanja:partner_detail', args=[record['identity_id']]) + f'?snapshot={snapshot.pk}'
        rows.append([cell(label, format_html('<a href="{}">{}</a>', url, label)),
                     *[cell(value, format_html('<span class="receivable-amount {}">{}</span>',
                        f'receivable-tone-{tone}' if value else 'receivable-zero',
                        number_format(value, decimal_pos=2, use_l10n=True, force_grouping=True)))
                       for value, tone in zip(record['amounts'], AGING_TONES)]])
    observed = timezone.localtime(snapshot.source_observed_at)
    return {'data': rows, 'available': True, 'snapshot_id': snapshot.pk, 'as_of_date': snapshot.as_of_date.isoformat(),
            'footer': {'collections_as_of': str(format_html(
                'Stanje na dan {} · Preuzeto {} · Izvor: Potraživanja',
                snapshot.as_of_date.strftime('%d.%m.%Y.'), observed.strftime('%d.%m.%Y. %H:%M')))}}


def shared_data(entries, code, start, end):
    result = shared_cost(getattr(settings, "FINANSIJE_COMPANY", 1), code, start, end)
    metrics = {"shared_cost": "Nema podataka", "result_after_shared": "Nema podataka"}
    if result["available"]:
        direct = summary(entries.filter(booking_date__range=(start, end)))["result"]
        metrics = {"shared_cost": str(expense_badge(result["cost"])),
                   "result_after_shared": str(amount_badge(direct - result["cost"]))}
    return {"metrics": metrics, "note": result["note"], "complete": result.get("complete")}


def cash_data(code, start, end):
    result = cash_flow(getattr(settings, "FINANSIJE_COMPANY", 1), code, start, end)
    metrics = {key: "Nema podataka" for key in ("inflow", "outflow", "net_cash")}
    if result["available"]:
        metrics = {"inflow": str(amount_badge(result["inflow"])),
                   "outflow": str(expense_badge(result["outflow"])),
                   "net_cash": str(amount_badge(result["net"]))}
    return {"metrics": metrics, "note": result["note"], "complete": result.get("complete")}
