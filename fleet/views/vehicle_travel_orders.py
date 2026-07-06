import datetime
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from core.mixins import RolePermissionRequiredMixin
from hr.models import Employee

from ..forms.garaza import VehicleTravelOrderCloseForm, VehicleTravelOrderForm
from ..models import TransactionNIS, TransactionOMV, Vehicle, VehicleTravelOrder
from ..support.fuel import filter_nis_fuel_queryset, filter_omv_fuel_queryset, format_omv_receipt_number
from ..support.garaza import get_vehicle_center_code, get_vehicle_latest_organizational_unit


def get_previous_vehicle_travel_order(order):
    if not order or not order.vehicle_id or not order.created_at:
        return None
    return (
        VehicleTravelOrder.objects.filter(
            vehicle=order.vehicle,
            created_at__lt=order.created_at,
            closed_at__isnull=False,
        )
        .order_by("-created_at", "-id")
        .first()
    )


class VehicleTravelOrderListView(LoginRequiredMixin, ListView):
    model = VehicleTravelOrder
    template_name = "fleet/vehicle_travel_order_list.html"
    context_object_name = "travel_orders"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("vehicle", "employee")
            .order_by("-created_at", "-pn_number")
        )
        vehicle_id = self.request.GET.get("vehicle")
        employee_id = self.request.GET.get("employee")
        status_filter = self.request.GET.get("status")

        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if status_filter == "open":
            queryset = queryset.filter(closed_at__isnull=True)
        elif status_filter == "closed":
            queryset = queryset.filter(closed_at__isnull=False)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Zaduzenja vozila"
        ctx["status"] = ""
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["selected_vehicle"] = self.request.GET.get("vehicle", "")
        ctx["selected_employee"] = self.request.GET.get("employee", "")
        ctx["vehicles"] = Vehicle.objects.order_by("brand", "model", "inventory_number")
        ctx["employees"] = Employee.objects.filter(
            vehicle_travel_orders__isnull=False
        ).distinct().order_by("last_name", "first_name")
        return ctx


class VehicleTravelOrderDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = VehicleTravelOrder
    template_name = "fleet/vehicle_travel_order_detail.html"
    context_object_name = "order"

    def _row_from_omv(self, trx):
        qty = trx.quantity or Decimal("0")
        amt = trx.amount or Decimal("0")
        return {
            "date": trx.transaction_date,
            "invoice": format_omv_receipt_number(trx.invoice_no, trx.voucher),
            "card": trx.card,
            "supplier": "OMV",
            "quantity": qty,
            "unit_price": trx.unit_price or (amt / qty if qty else None),
            "amount": amt,
            "mileage": trx.mileage,
            "object": trx,
        }

    def _row_from_nis(self, trx):
        qty = trx.kolicina or Decimal("0")
        amt = trx.total or Decimal("0")
        return {
            "date": trx.datum_transakcije,
            "invoice": trx.broj_racuna,
            "card": trx.broj_kartice,
            "supplier": "NIS",
            "quantity": qty,
            "unit_price": trx.cena or (amt / qty if qty else None),
            "amount": amt,
            "mileage": trx.kilometraza,
            "object": trx,
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = self.object
        center_code = get_vehicle_center_code(order.vehicle)
        period_start = order.created_at
        period_end = order.closed_at or timezone.localdate()
        start_dt = datetime.datetime.combine(period_start, datetime.time.min)
        end_dt = datetime.datetime.combine(period_end, datetime.time.max)
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt)

        registration_number = (
            order.vehicle.traffic_cards.order_by("-issue_date")
            .values_list("registration_number", flat=True)
            .first()
        )

        omv_vehicle_filter = Q()
        nis_vehicle_filter = Q()

        if order.vehicle_id:
            omv_vehicle_filter &= Q(vehicle=order.vehicle) | Q(license_plate_no=registration_number)
            nis_vehicle_filter &= Q(vehicle=order.vehicle) | Q(registarska_oznaka_vozila=registration_number)
        elif registration_number:
            omv_vehicle_filter &= Q(license_plate_no=registration_number)
            nis_vehicle_filter &= Q(registarska_oznaka_vozila=registration_number)

        omv_period = list(filter_omv_fuel_queryset(
            TransactionOMV.objects.filter(omv_vehicle_filter, transaction_date__range=(start_dt, end_dt))
        ).order_by("transaction_date", "id"))
        nis_period = list(filter_nis_fuel_queryset(
            TransactionNIS.objects.filter(nis_vehicle_filter, datum_transakcije__range=(start_dt, end_dt))
        ).order_by("datum_transakcije", "id"))

        fuel_rows = [self._row_from_omv(trx) for trx in omv_period]
        fuel_rows += [self._row_from_nis(trx) for trx in nis_period]
        fuel_rows.sort(key=lambda row: row["date"] or datetime.datetime.min.replace(tzinfo=timezone.get_current_timezone()))
        total_liters = sum((row["quantity"] or Decimal("0")) for row in fuel_rows)
        total_amount = sum((row["amount"] or Decimal("0")) for row in fuel_rows)

        distance = None
        consumption = None
        if order.start_mileage is not None and order.end_mileage is not None:
            distance = order.end_mileage - order.start_mileage
            if distance > 0:
                consumption = ((total_liters or Decimal("0")) / Decimal(distance)) * Decimal("100")

        fuel_rows.sort(key=lambda row: row["date"])
        first_fuel_page = []
        second_fuel_page = []
        if fuel_rows:
            first_fuel_page = fuel_rows[:30]
            while len(first_fuel_page) < 30:
                first_fuel_page.append(None)
            if len(fuel_rows) > 30:
                second_fuel_page = fuel_rows[30:60]
                while len(second_fuel_page) < 30:
                    second_fuel_page.append(None)

        ctx.update(
            {
                "period_start": period_start,
                "period_end": period_end,
                "registration_number": registration_number,
                "center_code": center_code,
                "omv_transactions": [row["object"] for row in fuel_rows if row["supplier"] == "OMV"],
                "nis_transactions": [row["object"] for row in fuel_rows if row["supplier"] == "NIS"],
                "total_liters": total_liters,
                "total_amount": total_amount,
                "distance": distance,
                "consumption": consumption,
                "fuel_rows": fuel_rows,
                "first_fuel_page": first_fuel_page,
                "second_fuel_page": second_fuel_page,
            }
        )
        return ctx


class VehicleTravelOrderFuelReportView(VehicleTravelOrderDetailView):
    template_name = "fleet/vehicle_travel_order_fuel_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["next_url"] = reverse("vehicle_travel_order_list")
        return ctx


class VehicleTravelOrderCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = VehicleTravelOrder
    form_class = VehicleTravelOrderForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("vehicle_travel_order_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi putni nalog (vozilo)"
        ctx["submit_button_label"] = "Sacuvaj"
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        previous_orders = list(VehicleTravelOrder.objects.filter(
            vehicle=self.object.vehicle,
            closed_at__isnull=True,
            created_at__lt=self.object.created_at,
        ).exclude(pk=self.object.pk).order_by("-created_at", "-id"))
        update_fields = {"closed_at": self.object.created_at}
        if self.object.start_mileage is not None:
            update_fields["end_mileage"] = self.object.start_mileage
        if previous_orders:
            VehicleTravelOrder.objects.filter(pk__in=[order.pk for order in previous_orders]).update(**update_fields)
            self.closed_previous_order_id = previous_orders[0].pk
        return response

    def get_success_url(self):
        return reverse("vehicle_travel_order_print_open", args=[self.object.pk])


class VehicleTravelOrderUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = VehicleTravelOrder
    form_class = VehicleTravelOrderForm
    template_name = "fleet/generic_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.object = self.get_object()
        if self.object.closed_at and not request.user.is_superuser:
            raise PermissionDenied("Zatvoren putni nalog moze da menja samo superuser.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmena putnog naloga (vozilo)"
        ctx["submit_button_label"] = "Sacuvaj izmene"
        return ctx

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        return next_url or reverse("vehicle_travel_order_detail", args=[self.object.pk])


class VehicleTravelOrderCloseView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = VehicleTravelOrder
    form_class = VehicleTravelOrderCloseForm
    template_name = "fleet/generic_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Zatvori putni nalog (vozilo)"
        ctx["submit_button_label"] = "Zatvori"
        return ctx

    def get_success_url(self):
        return reverse("vehicle_travel_order_detail", args=[self.object.pk])


class VehicleTravelOrderDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = VehicleTravelOrder
    template_name = "fleet/vehicle_travel_order_confirm_delete.html"
    success_url = reverse_lazy("vehicle_travel_order_list")
    context_object_name = "travel_order"

    def dispatch(self, request, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.object = self.get_object()
        if self.object.closed_at and not request.user.is_superuser:
            raise PermissionDenied("Zatvoren putni nalog moze da brise samo superuser.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Obrisi putni nalog"
        ctx["next"] = self.request.GET.get("next") or self.request.META.get("HTTP_REFERER")
        return ctx

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        return next_url or super().get_success_url()


class VehicleTravelOrderRequestView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/vehicle_travel_order_request.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = get_object_or_404(
            VehicleTravelOrder.objects.select_related("vehicle", "employee"),
            pk=kwargs.get("pk"),
        )
        vehicle = order.vehicle
        organizational_unit = get_vehicle_latest_organizational_unit(vehicle)
        traffic_card = vehicle.traffic_cards.order_by("-issue_date", "-id").first()
        ctx.update(
            {
                "order": order,
                "vehicle": vehicle,
                "employee": order.employee,
                "organizational_unit_code": getattr(organizational_unit, "code", ""),
                "organizational_unit_name": getattr(organizational_unit, "name", ""),
                "registration_number": getattr(traffic_card, "registration_number", ""),
                "next_url": reverse("vehicle_travel_order_list"),
                "previous_report_url": self.request.GET.get("previous_report"),
            }
        )
        return ctx


class VehicleTravelOrderPrintOpenView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/vehicle_travel_order_print_open.html"
    required_permission_code = "vehicle_travel_order_create"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = get_object_or_404(
            VehicleTravelOrder.objects.select_related("vehicle", "employee"),
            pk=kwargs.get("pk"),
        )
        previous_order = get_previous_vehicle_travel_order(order)
        ctx.update(
            {
                "title": "Otvaranje stampe zaduzenja",
                "order": order,
                "list_url": reverse("vehicle_travel_order_list"),
                "request_url": reverse("vehicle_travel_order_request", args=[order.pk]),
                "previous_report_url": (
                    reverse("vehicle_travel_order_fuel_report", args=[previous_order.pk])
                    if previous_order
                    else ""
                ),
            }
        )
        return ctx
