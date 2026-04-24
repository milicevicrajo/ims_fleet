import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from urllib.parse import quote
from django_filters.views import FilterView
from django.views import View
from django.views.generic import CreateView, UpdateView, TemplateView, ListView, DeleteView
from django.views.generic.detail import DetailView
from django.utils import timezone

from .filters import KvarFilter
from .forms import (
    KvarForm,
    KvarPartForm,
    VehicleTravelOrderForm,
    VehicleTravelOrderCloseForm,
    ProcurementRequestForm,
    ProcurementItemForm,
)
from .models import (
    Kvar,
    JobCode,
    KvarPart,
    VehicleTravelOrder,
    TransactionOMV,
    TransactionNIS,
    ProcurementRequest,
    ProcurementItem,
)
from .mixins import RolePermissionRequiredMixin


def ensure_auto_parts(kvar: Kvar):
    """Autofill parts for mali/veliki servis ako nisu uneti."""
    if kvar.van_ims or kvar.parts.exists():
        return list(kvar.parts.all())

    parts_map = {
        Kvar.WorkType.MALI_SERVIS: [
            {"name": "Motorno ulje", "quantity": "5.0", "uom": "l"},
            {"name": "Filter ulja", "quantity": "1", "uom": "kom"},
            {"name": "Filter vazduha", "quantity": "1", "uom": "kom"},
            {"name": "Filter klime", "quantity": "1", "uom": "kom"},
            {"name": "Filter goriva", "quantity": "1", "uom": "kom"},
            {"name": "Svećice", "quantity": "4", "uom": "kom"},
            {"name": "WD sprej", "quantity": "1", "uom": "kom"},
        ],
        Kvar.WorkType.VELIKI_SERVIS: [
            {"name": "Motorno ulje", "quantity": "6.0", "uom": "l"},
            {"name": "Filter ulja", "quantity": "1", "uom": "kom"},
            {"name": "Filter vazduha", "quantity": "1", "uom": "kom"},
            {"name": "Filter klime", "quantity": "1", "uom": "kom"},
            {"name": "Vodena pumpa", "quantity": "1", "uom": "kom"},
            {"name": "PK kaiš komplet", "quantity": "1", "uom": "kom"},
            {"name": "PK kaiš i set zupčastog kaiša", "quantity": "1", "uom": "kom"},
            {"name": "G-12", "quantity": "2.0", "uom": "l"},
            {"name": "Diht masa", "quantity": "1", "uom": "kom"},
            {"name": "WD sprej", "quantity": "1", "uom": "kom"},
            {"name": "Svećice", "quantity": "4", "uom": "kom"},
            {"name": "Antifriz", "quantity": "2.0", "uom": "l"},
        ],
    }
    defaults = parts_map.get(kvar.work_type)
    if not defaults:
        return list(kvar.parts.all())

    objs = [
        KvarPart(
            kvar=kvar,
            name=item["name"],
            quantity=Decimal(str(item["quantity"])),
            uom=item["uom"],
        )
        for item in defaults
    ]
    KvarPart.objects.bulk_create(objs)
    return list(kvar.parts.all())


def _get_vehicle_latest_organizational_unit(vehicle):
    latest_jobcode = (
        JobCode.objects.select_related("organizational_unit")
        .filter(vehicle=vehicle)
        .order_by("-assigned_date", "-id")
        .first()
    )
    return getattr(latest_jobcode, "organizational_unit", None)


def _get_vehicle_center_code(vehicle):
    organizational_unit = _get_vehicle_latest_organizational_unit(vehicle)
    if organizational_unit:
        return (getattr(organizational_unit, "center", "") or "").strip()
    return ""


class KvarListView(LoginRequiredMixin, FilterView):
    model = Kvar
    template_name = "fleet/kvar_list.html"
    context_object_name = "kvarovi"
    filterset_class = KvarFilter

    def get_queryset(self):
        return (
            Kvar.objects.select_related("vehicle")
            .prefetch_related("vehicle__traffic_cards")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Kvarovi (garaza)"
        ctx["form"] = ctx["filter"].form
        return ctx


class KvarIMSListView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/kvar_list_simple.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Kvarovi u IMS (bez filtera)"
        ctx["kvarovi"] = (
            Kvar.objects.select_related("vehicle")
            .prefetch_related("vehicle__traffic_cards")
            .filter(van_ims=False)
            .order_by("-created_at")
        )
        return ctx


class KvarVanIMSListView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/kvar_list_simple.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Kvarovi van IMS (bez filtera)"
        ctx["kvarovi"] = (
            Kvar.objects.select_related("vehicle")
            .prefetch_related("vehicle__traffic_cards")
            .filter(van_ims=True)
            .order_by("-created_at")
        )
        return ctx


class GarazaHomeView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/garaza_home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Poslovi garaze IMS"
        return ctx


class KvarPrintView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/kvar_print.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kvar = get_object_or_404(
            Kvar.objects.select_related("vehicle"),
            pk=kwargs.get("pk"),
        )
        vehicle = kvar.vehicle
        traffic_card = vehicle.traffic_cards.order_by("-issue_date", "-id").first()
        latest_jobcode = (
            JobCode.objects.select_related("organizational_unit")
            .filter(vehicle=vehicle)
            .order_by("-assigned_date", "-id")
            .first()
        )

        ctx.update(
            {
                "kvar": kvar,
                "vehicle": vehicle,
                "registration_number": getattr(traffic_card, "registration_number", ""),
                "center": getattr(latest_jobcode.organizational_unit, "center", "")
                if latest_jobcode and latest_jobcode.organizational_unit
                else "",
                "organizational_unit": getattr(latest_jobcode, "organizational_unit", None),
                "next_url": self.request.GET.get("next") or reverse("kvar_list"),
                "auto_print": self.request.GET.get("auto") == "1",
            }
        )
        return ctx


class KvarWorkOrderView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/kvar_workorder.html"

    def dispatch(self, request, *args, **kwargs):
        self.kvar_obj = get_object_or_404(Kvar, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kvar = (
            Kvar.objects.select_related("vehicle")
            .get(pk=self.kvar_obj.pk)
        )
        vehicle = kvar.vehicle
        traffic_card = vehicle.traffic_cards.order_by("-issue_date", "-id").first()
        latest_jobcode = (
            JobCode.objects.select_related("organizational_unit")
            .filter(vehicle=vehicle)
            .order_by("-assigned_date", "-id")
            .first()
        )
        parts_qs = ensure_auto_parts(kvar) if not kvar.van_ims else list(kvar.parts.all())
        auto_parts = [] if kvar.van_ims else []

        ctx.update(
            {
                "kvar": kvar,
                "vehicle": vehicle,
                "registration_number": getattr(traffic_card, "registration_number", ""),
                "center": getattr(latest_jobcode.organizational_unit, "center", "")
                if latest_jobcode and latest_jobcode.organizational_unit
                else "",
                "organizational_unit": getattr(latest_jobcode, "organizational_unit", None),
                "next_url": self.request.GET.get("next") or reverse("kvar_list"),
                "auto_print": self.request.GET.get("auto") == "1",
                "parts": parts_qs,
                "auto_parts": auto_parts,
                "part_form": KvarPartForm(),
                "is_van_ims": kvar.van_ims,
            }
        )
        return ctx


class KvarTrebovanjeView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/kvar_trebovanje.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kvar = get_object_or_404(Kvar.objects.select_related("vehicle"), pk=kwargs.get("pk"))
        vehicle = kvar.vehicle
        traffic_card = vehicle.traffic_cards.order_by("-issue_date", "-id").first()
        latest_jobcode = (
            JobCode.objects.select_related("organizational_unit")
            .filter(vehicle=vehicle)
            .order_by("-assigned_date", "-id")
            .first()
        )
        MAX_ROWS = 12
        parts_qs = ensure_auto_parts(kvar) if not kvar.van_ims else list(kvar.parts.all())
        parts_list = list(parts_qs)

        rows_pages = []
        if not parts_list:
            rows_pages.append([None] * MAX_ROWS)
        else:
            for i in range(0, len(parts_list), MAX_ROWS):
                chunk = parts_list[i : i + MAX_ROWS]
                padded = chunk + [None] * max(0, MAX_ROWS - len(chunk))
                rows_pages.append(padded)

        ctx.update(
            {
                "kvar": kvar,
                "vehicle": vehicle,
                "registration_number": getattr(traffic_card, "registration_number", ""),
                "organizational_unit": getattr(latest_jobcode, "organizational_unit", None),
                "center": getattr(latest_jobcode.organizational_unit, "center", "") if latest_jobcode and latest_jobcode.organizational_unit else "",
                "rows_pages": rows_pages,
                "is_van_ims": kvar.van_ims,
                "auto_print": self.request.GET.get("auto") == "1",
                "next_url": self.request.GET.get("next") or reverse("kvar_list"),
                "vehicle_type": (
                    "Teretno"
                    if (getattr(vehicle, "category", "") or "").lower().find("teret") != -1
                    else "Putnicko"
                ),
            }
        )
        return ctx


class KvarDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/kvar_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.kvar = get_object_or_404(
            Kvar.objects.select_related("vehicle"), pk=kwargs.get("pk")
        )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action") or "add"
        part_id = request.POST.get("part_id")

        if action == "delete" and part_id:
            part = get_object_or_404(KvarPart, pk=part_id, kvar=self.kvar)
            part.delete()
            messages.success(request, "Stavka je obrisana.")
            return redirect("kvar_detail", pk=self.kvar.pk)

        instance = None
        if action == "update" and part_id:
            instance = get_object_or_404(KvarPart, pk=part_id, kvar=self.kvar)

        form = KvarPartForm(request.POST, instance=instance)
        if form.is_valid():
            part = form.save(commit=False)
            part.kvar = self.kvar
            part.save()
            messages.success(request, "Stavka je sacuvana.")
        else:
            messages.error(request, "Proveri unete podatke za stavku.")
        return redirect("kvar_detail", pk=self.kvar.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        vehicle = self.kvar.vehicle
        traffic_card = vehicle.traffic_cards.order_by("-issue_date", "-id").first()
        latest_jobcode = (
            JobCode.objects.select_related("organizational_unit")
            .filter(vehicle=vehicle)
            .order_by("-assigned_date", "-id")
            .first()
        )

        parts = ensure_auto_parts(self.kvar)

        ctx.update(
            {
                "kvar": self.kvar,
                "vehicle": vehicle,
                "registration_number": getattr(traffic_card, "registration_number", ""),
                "organizational_unit": getattr(latest_jobcode, "organizational_unit", None),
                "parts": parts,
                "part_form": KvarPartForm(),
            }
        )
        return ctx


class KvarCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Kvar
    form_class = KvarForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("kvar_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Prijavi kvar"
        ctx["submit_button_label"] = "Sacuvaj"
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect("kvar_detail", pk=self.object.pk)


class KvarUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Kvar
    form_class = KvarForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("kvar_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmeni kvar"
        ctx["submit_button_label"] = "Sacuvaj izmene"
        return ctx


class KvarDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    success_url = reverse_lazy("kvar_list")

    def post(self, request, *args, **kwargs):
        kvar = get_object_or_404(Kvar, pk=kwargs.get("pk"))
        kvar.delete()
        messages.success(request, "Kvar je obrisan.")
        return redirect(self.success_url)


class ProcurementRequestListView(LoginRequiredMixin, ListView):
    model = ProcurementRequest
    template_name = "fleet/gzn_list.html"
    context_object_name = "requests"
    paginate_by = 50


class ProcurementRequestCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ProcurementRequest
    form_class = ProcurementRequestForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("gzn_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi zahtev za nabavku"
        ctx["submit_button_label"] = "Sačuvaj"
        return ctx

    def form_valid(self, form):
        super().form_valid(form)
        return redirect("gzn_detail", pk=self.object.pk)


class ProcurementRequestDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/gzn_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.request_obj = get_object_or_404(
            ProcurementRequest.objects.select_related("job_code"), pk=kwargs.get("pk")
        )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action") or "add"
        item_id = request.POST.get("item_id")

        if action == "delete" and item_id:
            item = get_object_or_404(ProcurementItem, pk=item_id, request=self.request_obj)
            item.delete()
            messages.success(request, "Stavka je obrisana.")
            return redirect("gzn_detail", pk=self.request_obj.pk)

        instance = None
        if action == "update" and item_id:
            instance = get_object_or_404(ProcurementItem, pk=item_id, request=self.request_obj)

        form = ProcurementItemForm(request.POST, instance=instance)
        if form.is_valid():
            item = form.save(commit=False)
            item.request = self.request_obj
            item.save()
            messages.success(request, "Stavka je sačuvana.")
        else:
            messages.error(request, "Proveri unete podatke.")
        return redirect("gzn_detail", pk=self.request_obj.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "gzn": self.request_obj,
                "items": list(self.request_obj.items.all()),
                "item_form": ProcurementItemForm(),
            }
        )
        return ctx


class ProcurementRequestPrintView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/gzn_print.html"

    def dispatch(self, request, *args, **kwargs):
        self.gzn = get_object_or_404(
            ProcurementRequest.objects.select_related("job_code"),
            pk=kwargs.get("pk"),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        MAX_ROWS = 12
        items = list(self.gzn.items.all())
        rows_pages = []
        if not items:
            rows_pages.append([None] * MAX_ROWS)
        else:
            for i in range(0, len(items), MAX_ROWS):
                chunk = items[i : i + MAX_ROWS]
                padded = chunk + [None] * max(0, MAX_ROWS - len(chunk))
                rows_pages.append(padded)

        job_code = self.gzn.job_code

        ctx.update(
            {
                "gzn": self.gzn,
                "rows_pages": rows_pages,
                "job_code": job_code,
                "center": getattr(job_code, "center", ""),
                "next_url": self.request.GET.get("next") or reverse("gzn_detail", kwargs={"pk": self.gzn.pk}),
                "auto_print": self.request.GET.get("auto") == "1",
            }
        )
        return ctx


# <!-- ======================================================================================== -->
#                           PUTNI NALOZI ZA VOZILA
# <!-- ======================================================================================== -->
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
        center_code = _get_vehicle_center_code(order.vehicle)
        period_start = order.created_at
        period_end = order.closed_at or timezone.localdate()
        start_dt = datetime.datetime.combine(period_start, datetime.time.min)
        end_dt = datetime.datetime.combine(period_end, datetime.time.max)

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

        omv_qs = TransactionOMV.objects.filter(omv_filter).order_by("-transaction_date")
        nis_qs = TransactionNIS.objects.filter(nis_filter).order_by("-datum_transakcije")

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
        fuel_rows.sort(key=lambda x: x["date"] or datetime.datetime.min)
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
        VehicleTravelOrder.objects.filter(
            vehicle=self.object.vehicle,
            closed_at__isnull=True,
        ).exclude(pk=self.object.pk).update(closed_at=self.object.created_at)
        return response

    def get_success_url(self):
        # Posle kreiranja otvori detalj novog naloga.
        return reverse("vehicle_travel_order_detail", args=[self.object.pk])


class VehicleTravelOrderUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = VehicleTravelOrder
    form_class = VehicleTravelOrderForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("vehicle_travel_order_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmena putnog naloga (vozilo)"
        ctx["submit_button_label"] = "Sacuvaj izmene"
        return ctx


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
        organizational_unit = _get_vehicle_latest_organizational_unit(vehicle)
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
