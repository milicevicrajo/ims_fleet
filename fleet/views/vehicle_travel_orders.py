import datetime
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from core.mixins import RolePermissionRequiredMixin

from ..forms.garaza import VehicleTravelOrderCloseForm, VehicleTravelOrderForm
from ..models import TransactionNIS, TransactionOMV, VehicleTravelOrder
from ..support.fuel import filter_nis_fuel_queryset, filter_omv_fuel_queryset
from ..support.garaza import get_vehicle_center_code, get_vehicle_latest_organizational_unit


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
        status = self.kwargs.get("status")
        if status == "open":
            queryset = queryset.filter(closed_at__isnull=True)
        elif status == "closed":
            queryset = queryset.filter(closed_at__isnull=False)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        status = self.kwargs.get("status")
        ctx["title"] = "Otvoreni putni nalozi za vozila" if status == "open" else "Zatvoreni putni nalozi za vozila"
        ctx["status"] = status
        return ctx


class VehicleTravelOrderDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = VehicleTravelOrder
    template_name = "fleet/vehicle_travel_order_detail.html"
    context_object_name = "order"

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

        omv_filter = Q(transaction_date__range=(start_dt, end_dt))
        nis_filter = Q(datum_transakcije__range=(start_dt, end_dt))

        if order.vehicle_id:
            omv_filter &= Q(vehicle=order.vehicle) | Q(license_plate_no=registration_number)
            nis_filter &= Q(vehicle=order.vehicle) | Q(registarska_oznaka_vozila=registration_number)
        elif registration_number:
            omv_filter &= Q(license_plate_no=registration_number)
            nis_filter &= Q(registarska_oznaka_vozila=registration_number)

        omv_qs = filter_omv_fuel_queryset(
            TransactionOMV.objects.filter(omv_filter)
        ).order_by("-transaction_date")
        nis_qs = filter_nis_fuel_queryset(
            TransactionNIS.objects.filter(nis_filter)
        ).order_by("-datum_transakcije")

        omv_liters = omv_qs.aggregate(total=Sum("quantity"))["total"] or Decimal("0")
        nis_liters = nis_qs.aggregate(total=Sum("kolicina"))["total"] or Decimal("0")
        total_liters = omv_liters + nis_liters
        omv_amount = omv_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        nis_amount = nis_qs.aggregate(total=Sum("total"))["total"] or Decimal("0")
        total_amount = omv_amount + nis_amount

        distance = None
        consumption = None
        if order.start_mileage is not None and order.end_mileage is not None:
            distance = order.end_mileage - order.start_mileage
            if distance > 0:
                consumption = ((total_liters or Decimal("0")) / Decimal(distance)) * Decimal("100")

        fuel_rows = []
        for trx in omv_qs:
            qty = trx.quantity or Decimal("0")
            amt = trx.amount or Decimal("0")
            unit_price = trx.unit_price or (amt / qty if qty else None)
            fuel_rows.append(
                {
                    "date": trx.transaction_date,
                    "invoice": trx.voucher,
                    "card": trx.card,
                    "supplier": "OMV",
                    "quantity": qty,
                    "unit_price": unit_price,
                    "amount": amt,
                    "mileage": trx.mileage,
                }
            )
        for trx in nis_qs:
            qty = trx.kolicina or Decimal("0")
            amt = trx.total or Decimal("0")
            unit_price = trx.cena or (amt / qty if qty else None)
            fuel_rows.append(
                {
                    "date": trx.datum_transakcije,
                    "invoice": trx.broj_racuna,
                    "card": trx.broj_kartice,
                    "supplier": "NIS",
                    "quantity": qty,
                    "unit_price": unit_price,
                    "amount": amt,
                    "mileage": trx.kilometraza,
                }
            )
        fuel_rows.sort(key=lambda row: row["date"] or datetime.datetime.min)
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
                "omv_transactions": omv_qs,
                "nis_transactions": nis_qs,
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
        ctx["next_url"] = self.request.GET.get("next") or reverse("vehicle_travel_order_detail", args=[self.object.pk])
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
        previous_orders = VehicleTravelOrder.objects.filter(
            vehicle=self.object.vehicle,
            closed_at__isnull=True,
            created_at__lt=self.object.created_at,
        ).exclude(pk=self.object.pk)
        update_fields = {"closed_at": self.object.created_at}
        if self.object.start_mileage is not None:
            update_fields["end_mileage"] = self.object.start_mileage
        previous_orders.update(**update_fields)
        return response

    def get_success_url(self):
        return reverse("vehicle_travel_order_detail", args=[self.object.pk])


class VehicleTravelOrderUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = VehicleTravelOrder
    form_class = VehicleTravelOrderForm
    template_name = "fleet/generic_form.html"

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
    success_url = reverse_lazy("vehicle_travel_order_open_list")
    context_object_name = "travel_order"

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
                "next_url": self.request.GET.get("next") or reverse("vehicle_travel_order_open_list"),
            }
        )
        return ctx
