from datetime import date, timedelta
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Q, Subquery
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from hr.models import Employee

from ..filters import KvarFilter, TrafficCardFilterForm, VehicleFilter
from ..models import JobCode, Kvar, Lease, Policy, Requisition, ServiceTransaction, TrafficCard, Vehicle, VehicleTravelOrder
from ..support.fuel import calculate_average_fuel_consumption, get_fuel_invoice_queryset, format_omv_receipt_number
from .lease import LONG_TERM_LEASE_TYPES, LeaseListView
from .vehicles import _vehicle_list_base_queryset
from .vehicle_travel_orders import get_previous_vehicle_travel_order


def _int_param(request, name, default=0):
    try:
        return int(request.GET.get(name, default))
    except (TypeError, ValueError):
        return default


def _datatable_response(
    request,
    base_qs,
    columns,
    row_builder,
    search_filter=None,
    default_order=None,
    append_id_order=True,
):
    records_total = base_qs.count()
    qs = base_qs

    search_value = request.GET.get("search[value]", "").strip()
    if search_value and search_filter is not None:
        qs = qs.filter(search_filter(search_value)).distinct()

    records_filtered = qs.count()

    order_column = request.GET.get("order[0][column]")
    order_dir = request.GET.get("order[0][dir]", "asc")
    order_field = columns.get(order_column)
    if order_field:
        if order_dir == "desc":
            order_field = f"-{order_field}"
        order_fields = [order_field]
        if append_id_order:
            order_fields.append("-id")
        qs = qs.order_by(*order_fields)
    elif default_order:
        qs = qs.order_by(*default_order)

    start = max(_int_param(request, "start", 0), 0)
    length = _int_param(request, "length", 50)
    if length < 0:
        length = 50
    length = min(length, 200)

    return JsonResponse(
        {
            "draw": _int_param(request, "draw", 0),
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": [row_builder(obj) for obj in qs[start:start + length]],
        }
    )


def _date(value, fmt="%d.%m.%Y"):
    return value.strftime(fmt) if value else ""


def _money(value):
    return f"{value:.2f}" if value is not None else ""


@login_required
def vehicle_datatable_data(request):
    base_qs = _vehicle_list_base_queryset(request)
    filtered_qs = VehicleFilter(request.GET, queryset=base_qs).qs

    def search(value):
        return (
            Q(registration_number__icontains=value)
            | Q(brand__icontains=value)
            | Q(model__icontains=value)
            | Q(inventory_number__icontains=value)
            | Q(chassis_number__icontains=value)
            | Q(latest_org_unit_code__icontains=value)
        )

    def row(vehicle):
        consumption = calculate_average_fuel_consumption(vehicle)
        actions = [
            f'<a href="{reverse("vehicle_update", args=[vehicle.pk])}" class="btn btn-outline-primary btn-sm" title="Izmeni">'
            '<i class="mdi mdi-pencil"></i> Izmeni</a>'
        ]
        if vehicle.otpis and request.user.is_superuser:
            actions.append(
                f'<form action="{reverse("vehicle_restore", args=[vehicle.pk])}" method="post" class="d-inline m-0 p-0">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">'
                f'<input type="hidden" name="next" value="{escape(request.get_full_path())}">'
                '<button type="submit" class="btn btn-outline-success btn-sm" '
                'onclick="return confirm(\'Da li zelite da vratite ovo vozilo u upotrebu?\');" title="Vrati u upotrebu">'
                '<i class="mdi mdi-restore"></i> Vrati</button></form>'
            )
        if not vehicle.otpis:
            actions.append(
                f'<form action="{reverse("vehicle_toggle_status", args=[vehicle.pk])}" method="post" class="d-inline m-0 p-0">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">'
                f'<input type="hidden" name="next" value="{escape(request.get_full_path())}">'
                '<button type="submit" class="btn btn-outline-danger btn-sm" '
                'onclick="return confirm(\'Da li ste sigurni da zelite da otpisete ovo vozilo?\');" title="Otpisi">'
                '<i class="mdi mdi-delete"></i></button></form>'
            )
        return {
            "DT_RowClass": "fleet-row-muted" if vehicle.otpis else "",
            "registration_number": (
                f'<a href="{reverse("vehicle_detail", args=[vehicle.pk])}" class="btn btn-sm btn-outline-primary">'
                f'<i class="mdi mdi-eye"></i> {escape(vehicle.registration_number or "")}</a>'
            ),
            "brand": escape(vehicle.brand or ""),
            "model": escape(vehicle.model or ""),
            "year_of_manufacture": vehicle.year_of_manufacture or "",
            "mileage": vehicle.mileage or "",
            "consumption": f"{consumption:.2f}" if consumption else "0",
            "category": escape(vehicle.get_category_display() or ""),
            "center": escape(vehicle.latest_org_unit_code or "-"),
            "engine_volume": f"{vehicle.engine_volume:.0f}" if vehicle.engine_volume is not None else "",
            "actions": f'<span class="fleet-list-actions">{"".join(actions)}</span>',
        }

    return _datatable_response(
        request,
        filtered_qs,
        {
            "0": "registration_number",
            "1": "brand",
            "2": "model",
            "3": "year_of_manufacture",
            "4": "mileage",
            "6": "category",
            "7": "latest_org_unit_code",
            "8": "engine_volume",
        },
        row,
        search,
        default_order=("registration_number", "brand", "model", "id"),
    )


@login_required
def vehicle_travel_order_datatable_data(request):
    qs = VehicleTravelOrder.objects.select_related("vehicle", "employee")
    vehicle_id = request.GET.get("vehicle")
    employee_id = request.GET.get("employee")
    status_filter = request.GET.get("status")
    if vehicle_id:
        qs = qs.filter(vehicle_id=vehicle_id)
    if employee_id:
        qs = qs.filter(employee_id=employee_id)
    if status_filter == "open":
        qs = qs.filter(closed_at__isnull=True)
    elif status_filter == "closed":
        qs = qs.filter(closed_at__isnull=False)

    def search(value):
        return (
            Q(pn_number__icontains=value)
            | Q(rbz__icontains=value)
            | Q(vehicle__brand__icontains=value)
            | Q(vehicle__model__icontains=value)
            | Q(vehicle__chassis_number__icontains=value)
            | Q(employee__first_name__icontains=value)
            | Q(employee__last_name__icontains=value)
        )

    def row(order):
        previous = get_previous_vehicle_travel_order(order)
        actions = []
        if not order.closed_at or request.user.is_superuser:
            actions.append(
                f'<a href="{reverse("vehicle_travel_order_update", args=[order.pk])}" class="btn btn-outline-primary btn-sm">'
                '<i class="mdi mdi-pencil"></i> Izmeni</a>'
            )
        if not order.closed_at:
            actions.append(
                f'<a href="{reverse("vehicle_travel_order_close", args=[order.pk])}" class="btn btn-outline-success btn-sm">'
                '<i class="mdi mdi-lock"></i> Zatvori</a>'
            )
            if previous:
                actions.append(
                    f'<a href="{reverse("vehicle_travel_order_fuel_report", args=[previous.pk])}?next={request.get_full_path()}" '
                    'class="btn btn-outline-secondary btn-sm" target="_blank" title="Obracun prethodnog perioda">'
                    '<i class="mdi mdi-printer"></i> Prethodni obracun</a>'
                )
        else:
            actions.append(
                f'<a href="{reverse("vehicle_travel_order_fuel_report", args=[order.pk])}" class="btn btn-outline-secondary btn-sm" '
                'target="_blank" title="Obracun goriva"><i class="mdi mdi-printer"></i> Obracun</a>'
            )
        actions.append(
            f'<a href="{reverse("vehicle_travel_order_request", args=[order.pk])}?next={request.get_full_path()}" '
            'class="btn btn-outline-info btn-sm" target="_blank"><i class="mdi mdi-printer"></i> Zahtev</a>'
        )
        if not order.closed_at or request.user.is_superuser:
            actions.append(
                f'<a href="{reverse("vehicle_travel_order_delete", args=[order.pk])}?next={request.get_full_path()}" '
                'class="btn btn-outline-danger btn-sm"><i class="mdi mdi-delete"></i> Obrisi</a>'
            )
        return {
            "DT_RowClass": "fleet-row-muted" if order.closed_at else "",
            "pn_number": (
                f'<a href="{reverse("vehicle_travel_order_detail", args=[order.pk])}" class="btn btn-sm btn-outline-primary">'
                f'<i class="mdi mdi-eye"></i> PN {order.pn_number or ""}</a>'
            ),
            "status": (
                '<span class="fleet-status closed"><i class="mdi mdi-lock"></i> Zatvoren</span>'
                if order.closed_at
                else '<span class="fleet-status open"><i class="mdi mdi-folder-open"></i> Otvoren</span>'
            ),
            "rbz": escape(order.rbz or "/"),
            "vehicle": escape(str(order.vehicle)),
            "employee": escape(str(order.employee)),
            "created_at": _date(order.created_at),
            "closed_at": _date(order.closed_at) or "/",
            "actions": f'<span class="fleet-list-actions">{"".join(actions)}</span>',
        }

    return _datatable_response(
        request,
        qs,
        {"0": "pn_number", "2": "rbz", "3": "vehicle__brand", "4": "employee__last_name", "5": "created_at", "6": "closed_at"},
        row,
        search,
        default_order=("-created_at", "-pn_number", "-id"),
    )


@login_required
def fuel_transactions_datatable_data(request):
    vehicle_id = request.GET.get("vehicle") or None
    search_value = request.GET.get("search[value]", "").strip()
    base_qs = get_fuel_invoice_queryset(vehicle_id=vehicle_id)
    qs = get_fuel_invoice_queryset(vehicle_id=vehicle_id, search_value=search_value)

    columns = {
        "0": "registration_number",
        "1": "latest_date",
        "2": "receipt_number",
        "3": "quantity_total",
        "4": "total_net",
        "5": "total_gross",
        "6": "supplier_name",
        "7": "max_mileage",
        "8": "line_count",
    }

    order_column = request.GET.get("order[0][column]")
    order_dir = request.GET.get("order[0][dir]", "asc")
    order_field = columns.get(order_column)
    if order_field:
        qs = qs.order_by(f"-{order_field}" if order_dir == "desc" else order_field)
    else:
        qs = qs.order_by("-latest_date")

    start = max(_int_param(request, "start", 0), 0)
    length = _int_param(request, "length", 50)
    if length < 0:
        length = 50
    length = min(length, 200)

    def row(invoice):
        vehicle_pk = invoice.get("vehicle_id")
        registration_number = invoice.get("registration_number") or "N/A"
        vehicle_link = (
            f'<a href="{reverse("vehicle_detail", args=[vehicle_pk])}" class="btn btn-outline-primary btn-sm">'
            f'<i class="mdi mdi-car"></i> {escape(registration_number)}</a>'
            if vehicle_pk
            else escape(registration_number)
        )
        detail_query = urlencode(
            {
                "supplier": invoice.get("supplier_name") or "",
                "receipt": invoice.get("receipt_number") or "",
                "vehicle": vehicle_pk or "",
            }
        )
        receipt_link = (
            f'<a href="{reverse("fuel_transaction_detail")}?{detail_query}" class="btn btn-outline-primary btn-sm">'
            f'<i class="mdi mdi-receipt"></i> {escape(invoice.get("receipt_number") or "")}</a>'
        )
        return {
            "registration_number": vehicle_link,
            "date": _date(invoice.get("latest_date"), "%d.%m.%Y %H:%M:%S"),
            "receipt_number": receipt_link,
            "quantity": _money(invoice.get("quantity_total") or 0),
            "total_net": _money(invoice.get("total_net") or 0),
            "total_gross": _money(invoice.get("total_gross") or 0),
            "supplier": escape(invoice.get("supplier_name") or ""),
            "mileage": f"{invoice.get('max_mileage') or 0:.0f}",
            "line_count": f"{invoice.get('line_count') or 0}",
        }

    page_rows = list(qs)[start:start + length]

    return JsonResponse(
        {
            "draw": _int_param(request, "draw", 0),
            "recordsTotal": base_qs.count(),
            "recordsFiltered": qs.count(),
            "data": [row(invoice) for invoice in page_rows],
        }
    )


@login_required
def service_transactions_datatable_data(request):
    qs = ServiceTransaction.objects.select_related("vehicle", "popravka_kategorija")

    def search(value):
        return (
            Q(vehicle__brand__icontains=value)
            | Q(vehicle__model__icontains=value)
            | Q(vehicle__chassis_number__icontains=value)
            | Q(popravka_kategorija__name__icontains=value)
            | Q(naz_par_pl__icontains=value)
            | Q(napomena__icontains=value)
        )

    def row(item):
        return {
            "vehicle": escape(str(item.vehicle)),
            "service_type": escape(str(item.popravka_kategorija or "")),
            "date": _date(item.datum, "%d.%m.%Y."),
            "cost": _money(item.potrazuje),
            "supplier": escape(item.naz_par_pl or ""),
            "description": escape(item.napomena or ""),
            "actions": (
                f'<a href="{reverse("service_transaction_update", args=[item.pk])}" class="btn btn-outline-primary btn-sm" title="Izmeni">'
                '<i class="mdi mdi-pencil"></i> Izmeni</a>'
            ),
        }

    return _datatable_response(
        request,
        qs,
        {"0": "vehicle__brand", "1": "popravka_kategorija__name", "2": "datum", "3": "potrazuje", "4": "naz_par_pl", "5": "napomena"},
        row,
        search,
        default_order=("-datum", "-id"),
    )


@login_required
def policies_datatable_data(request):
    qs = Policy.objects.select_related("vehicle")

    def search(value):
        return (
            Q(vehicle__brand__icontains=value)
            | Q(vehicle__model__icontains=value)
            | Q(vehicle__chassis_number__icontains=value)
            | Q(partner_name__icontains=value)
            | Q(invoice_number__icontains=value)
            | Q(insurance_type__icontains=value)
            | Q(policy_number__icontains=value)
        )

    def row(policy):
        partner = escape(policy.partner_name or "")
        if policy.partner_pib:
            partner += f'<small class="text-muted d-block">{policy.partner_pib}</small>'
        invoice = escape(str(policy.invoice_number or ""))
        if policy.invoice_id:
            invoice += f'<small class="text-muted d-block">{policy.invoice_id}</small>'
        return {
            "vehicle": escape(str(policy.vehicle)),
            "partner": partner,
            "invoice": invoice,
            "issue_date": _date(policy.issue_date),
            "insurance_type": escape(policy.insurance_type or ""),
            "policy_number": escape(str(policy.policy_number or "")),
            "premium_amount": _money(policy.premium_amount),
            "start_date": _date(policy.start_date),
            "end_date": _date(policy.end_date),
            "actions": (
                '<span class="fleet-list-actions">'
                f'<a href="{reverse("policy_update", args=[policy.pk])}" class="btn btn-outline-primary btn-sm" title="Izmeni">'
                '<i class="mdi mdi-pencil"></i> Izmeni</a>'
                f'<a href="{reverse("policy_delete", args=[policy.pk])}" class="btn btn-outline-danger btn-sm" title="Obrisi">'
                '<i class="mdi mdi-delete"></i></a></span>'
            ),
        }

    return _datatable_response(
        request,
        qs,
        {"0": "vehicle__brand", "1": "partner_name", "2": "invoice_number", "3": "issue_date", "4": "insurance_type", "5": "policy_number", "6": "premium_amount", "7": "start_date", "8": "end_date"},
        row,
        search,
        default_order=("-end_date", "-id"),
    )


@login_required
def leases_datatable_data(request):
    qs = Lease.objects.select_related("vehicle")
    tip = request.GET.get("tip")
    if tip == "dugorocni":
        qs = qs.filter(lease_type__in=LONG_TERM_LEASE_TYPES)
    elif tip in {"finansijski", "operativni"}:
        qs = qs.filter(lease_type=tip)
    if not LeaseListView._is_truthy(request.GET.get("prikazi_istekle")):
        qs = qs.filter(end_date__gte=timezone.localdate())

    def search(value):
        return (
            Q(vehicle__brand__icontains=value)
            | Q(vehicle__model__icontains=value)
            | Q(vehicle__chassis_number__icontains=value)
            | Q(partner_name__icontains=value)
            | Q(partner_code__icontains=value)
            | Q(contract_number__icontains=value)
            | Q(job_code__icontains=value)
            | Q(note__icontains=value)
        )

    def row(lease):
        if lease.lease_type == "finansijski":
            lease_type = '<span class="fleet-status info"><i class="mdi mdi-file-document"></i> Finansijski</span>'
        elif lease.lease_type == "operativni":
            lease_type = '<span class="fleet-status open"><i class="mdi mdi-car-clock"></i> Operativni</span>'
        elif lease.is_long_term_rental:
            lease_type = '<span class="fleet-status warning"><i class="mdi mdi-calendar-clock"></i> Dugorocni najam</span>'
        else:
            lease_type = escape(lease.lease_type_label or "-")
        return {
            "vehicle": escape(str(lease.vehicle)),
            "partner": f'{escape(lease.partner_name or "")}<small class="text-muted d-block">{escape(lease.partner_code or "")}</small>',
            "contract": f'{escape(lease.contract_number or "")}<small class="text-muted d-block">{escape(lease.job_code or "")}</small>',
            "lease_type": lease_type,
            "current_payment_amount": _money(lease.current_payment_amount),
            "start_date": _date(lease.start_date),
            "end_date": _date(lease.end_date),
            "note": escape(lease.note or "Nema napomena"),
            "actions": (
                '<span class="fleet-list-actions">'
                f'<a href="{reverse("lease_update", args=[lease.pk])}" class="btn btn-outline-primary btn-sm" title="Izmeni">'
                '<i class="mdi mdi-pencil"></i> Izmeni</a>'
                f'<a href="{reverse("lease_delete", args=[lease.pk])}" class="btn btn-outline-danger btn-sm" title="Obrisi" '
                f'onclick="return confirm(\'Da li sigurno zelis da obrises ugovor {escape(lease.contract_number or "")} za {escape(str(lease.vehicle))}?\');">'
                '<i class="mdi mdi-delete"></i></a></span>'
            ),
        }

    return _datatable_response(
        request,
        qs,
        {"0": "vehicle__brand", "1": "partner_name", "2": "contract_number", "3": "lease_type", "4": "current_payment_amount", "5": "start_date", "6": "end_date", "7": "note"},
        row,
        search,
        default_order=("-end_date", "-id"),
    )


@login_required
def kvar_datatable_data(request):
    base_qs = Kvar.objects.select_related("vehicle").prefetch_related("vehicle__traffic_cards")
    qs = KvarFilter(request.GET, queryset=base_qs).qs

    def search(value):
        return (
            Q(vehicle__brand__icontains=value)
            | Q(vehicle__model__icontains=value)
            | Q(vehicle__inventory_number__icontains=value)
            | Q(vehicle__traffic_cards__registration_number__icontains=value)
            | Q(opis__icontains=value)
            | Q(napomena__icontains=value)
        )

    def row(kvar):
        van_ims = (
            '<span class="fleet-status warning">Van IMS-a</span>'
            if kvar.van_ims else '<span class="fleet-status active">IMS garaza</span>'
        )
        return {
            "detail": (
                f'<a href="{reverse("kvar_detail", args=[kvar.pk])}" class="btn btn-outline-primary btn-sm">'
                '<i class="mdi mdi-eye"></i> Otvori</a>'
            ),
            "vehicle": f'<a href="{reverse("vehicle_detail", args=[kvar.vehicle_id])}" class="fleet-table-link">{escape(str(kvar.vehicle))}</a>',
            "work_type": escape(kvar.get_work_type_display()),
            "mileage": kvar.kilometraza,
            "description": escape(kvar.opis or ""),
            "note": escape(kvar.napomena or "/"),
            "van_ims": van_ims,
            "created_at": _date(kvar.created_at, "%d.%m.%Y %H:%M"),
            "actions": (
                '<span class="fleet-list-actions">'
                f'<a href="{reverse("kvar_update", args=[kvar.pk])}" class="btn btn-outline-primary btn-sm" title="Izmeni">'
                '<i class="mdi mdi-pencil"></i> Izmeni</a>'
                f'<a href="{reverse("kvar_print", args=[kvar.pk])}" class="btn btn-outline-secondary btn-sm" target="_blank" title="Prijava kvara (A4)">'
                '<i class="mdi mdi-printer"></i> Prijava</a>'
                f'<a href="{reverse("kvar_workorder", args=[kvar.pk])}" class="btn btn-outline-secondary btn-sm" target="_blank" title="Radni nalog">'
                '<i class="mdi mdi-clipboard-text"></i> Radni nalog</a>'
                f'<a href="{reverse("kvar_trebovanje", args=[kvar.pk])}" class="btn btn-outline-secondary btn-sm" target="_blank">'
                f'<i class="mdi mdi-file-document"></i> {"Zahtev" if kvar.van_ims else "Trebovanje"}</a>'
                f'<form method="post" action="{reverse("kvar_delete", args=[kvar.pk])}" class="d-inline m-0 p-0" '
                'onsubmit="return confirm(\'Da li sigurno zelite da obrisete ovaj kvar?\');">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">'
                '<button type="submit" class="btn btn-outline-danger btn-sm" title="Obrisi"><i class="mdi mdi-delete"></i></button>'
                '</form></span>'
            ),
        }

    return _datatable_response(
        request,
        qs,
        {"1": "vehicle__brand", "2": "work_type", "3": "kilometraza", "4": "opis", "5": "napomena", "6": "van_ims", "7": "created_at"},
        row,
        search,
        default_order=("-created_at", "-id"),
    )


@login_required
def requisitions_datatable_data(request):
    qs = Requisition.objects.select_related("vehicle")

    def search(value):
        return (
            Q(vehicle__brand__icontains=value)
            | Q(vehicle__model__icontains=value)
            | Q(vehicle__chassis_number__icontains=value)
            | Q(br_dok__icontains=value)
            | Q(naz_art__icontains=value)
        )

    def row(requisition):
        return {
            "vehicle": escape(str(requisition.vehicle) if requisition.vehicle_id else ""),
            "year": requisition.god,
            "document": (
                f'<a href="{reverse("requisition_detail", kwargs={"god": requisition.god, "br_dok": requisition.br_dok})}" '
                f'class="btn btn-outline-primary btn-sm"><i class="mdi mdi-eye"></i> {escape(requisition.br_dok)}</a>'
            ),
            "date": _date(requisition.datum_trebovanja),
            "article": escape(requisition.naz_art or ""),
            "quantity": _money(requisition.kol),
            "actions": (
                f'<a href="{reverse("requisition_update", args=[requisition.pk])}" class="btn btn-outline-primary btn-sm">'
                '<i class="mdi mdi-pencil"></i> Izmeni</a>'
            ),
        }

    return _datatable_response(
        request,
        qs,
        {"0": "vehicle__brand", "1": "god", "2": "br_dok", "3": "datum_trebovanja", "4": "naz_art", "5": "kol"},
        row,
        search,
        default_order=("-datum_trebovanja", "-id"),
    )


@login_required
def traffic_cards_datatable_data(request):
    latest_org_unit_subquery = JobCode.objects.filter(
        vehicle_id=OuterRef("vehicle_id")
    ).order_by("-assigned_date").values("organizational_unit__code")[:1]
    latest_center_subquery = JobCode.objects.filter(
        vehicle_id=OuterRef("vehicle_id")
    ).order_by("-assigned_date").values("organizational_unit__center")[:1]
    qs = TrafficCard.objects.select_related("vehicle").annotate(
        latest_org_unit=Subquery(latest_org_unit_subquery),
        latest_center=Subquery(latest_center_subquery),
    )

    filter_form = TrafficCardFilterForm(request.GET or None)
    if filter_form.is_valid():
        org_unit = filter_form.cleaned_data.get("organizational_unit")
        center = filter_form.cleaned_data.get("center")
        if org_unit:
            qs = qs.filter(latest_org_unit=org_unit.code)
        if center:
            qs = qs.filter(latest_center=center)

    def search(value):
        return (
            Q(vehicle__brand__icontains=value)
            | Q(vehicle__model__icontains=value)
            | Q(vehicle__chassis_number__icontains=value)
            | Q(vehicle__inventory_number__icontains=value)
            | Q(registration_number__icontains=value)
            | Q(traffic_card_number__icontains=value)
            | Q(serial_number__icontains=value)
            | Q(owner__icontains=value)
            | Q(homologation_number__icontains=value)
        )

    def row(card):
        pdf_html = (
            f'<a href="{card.traffic_card_pdf.url}" class="btn btn-outline-success btn-sm" target="_blank">'
            '<i class="mdi mdi-file-pdf-box"></i> PDF</a>'
            if card.traffic_card_pdf
            else '<span class="text-muted">Nema PDF</span>'
        )
        return {
            "vehicle": escape(str(card.vehicle)),
            "registration_number": escape(card.registration_number or ""),
            "issue_date": _date(card.issue_date),
            "valid_until": _date(card.valid_until),
            "traffic_card_number": escape(card.traffic_card_number or ""),
            "owner": escape(card.owner or ""),
            "actions": (
                '<span class="fleet-list-actions">'
                f'<a href="{reverse("trafficcard_update", args=[card.pk])}" class="btn btn-outline-primary btn-sm">'
                '<i class="mdi mdi-pencil"></i> Izmeni</a>'
                f"{pdf_html}</span>"
            ),
        }

    return _datatable_response(
        request,
        qs,
        {
            "0": "vehicle__brand",
            "1": "registration_number",
            "2": "issue_date",
            "3": "valid_until",
            "4": "traffic_card_number",
            "5": "owner",
        },
        row,
        search,
        default_order=("-valid_until", "-id"),
    )
