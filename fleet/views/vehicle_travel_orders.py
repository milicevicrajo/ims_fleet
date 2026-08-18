import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from core.mixins import RolePermissionRequiredMixin
from core.mixins import user_has_role_permission
from hr.models import Employee

from ..forms.garaza import PreviousVehicleTravelOrderForm, VehicleTravelOrderCloseForm, VehicleTravelOrderForm
from ..models import TransactionNIS, TransactionOMV, Vehicle, VehicleTravelOrder
from ..support.fuel import filter_nis_fuel_queryset, filter_omv_fuel_queryset, format_omv_receipt_number
from ..support.garaza import get_vehicle_center_code, get_vehicle_latest_organizational_unit


EMPLOYEE_ROLE_SLUG = "zaposleni"
EMPLOYEE_VEHICLE_TRAVEL_ORDER_PERMISSIONS = {
    "vehicle_travel_order_list",
    "vehicle_travel_order_data",
    "vehicle_travel_order_create",
    "vehicle_travel_order_detail",
    "vehicle_travel_order_request",
    "vehicle_travel_order_fuel_report",
    "vehicle_travel_order_print_open",
}
BROAD_VEHICLE_TRAVEL_ORDER_PERMISSIONS = {
    "vehicle_travel_order_update",
    "vehicle_travel_order_close",
    "vehicle_travel_order_delete",
    "vehicle_travel_order_previous_create",
}


def _user_has_non_employee_role_permission(user, permission_code):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.roles.filter(
        permissions__code=permission_code,
        is_active=True,
    ).exclude(slug=EMPLOYEE_ROLE_SLUG).exists()


def _user_has_employee_role_permission(user, permission_code):
    if not user.is_authenticated:
        return False
    return user.roles.filter(
        permissions__code=permission_code,
        is_active=True,
        slug=EMPLOYEE_ROLE_SLUG,
    ).exists()


def _is_vehicle_travel_order_employee_self_service(user):
    if not user.is_authenticated or user.is_superuser:
        return False
    return bool(
        getattr(user, "employee_id", None)
        and user.roles.filter(slug=EMPLOYEE_ROLE_SLUG, is_active=True).exists()
    )


def _has_vehicle_travel_order_broad_access(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    permission_codes = set(EMPLOYEE_VEHICLE_TRAVEL_ORDER_PERMISSIONS) | BROAD_VEHICLE_TRAVEL_ORDER_PERMISSIONS
    return user.roles.filter(
        permissions__code__in=permission_codes,
        is_active=True,
    ).exclude(slug=EMPLOYEE_ROLE_SLUG).exists()


def _can_employee_access_own_vehicle_travel_order(user, permission_code):
    return (
        permission_code in EMPLOYEE_VEHICLE_TRAVEL_ORDER_PERMISSIONS
        and getattr(user, "employee_id", None)
        and _user_has_employee_role_permission(user, permission_code)
    )


def _vehicle_travel_order_base_qs(request):
    qs = VehicleTravelOrder.objects.select_related("vehicle", "employee")
    user = request.user
    if _is_vehicle_travel_order_employee_self_service(user) and _user_has_employee_role_permission(
        user,
        "vehicle_travel_order_list",
    ):
        return qs
    if _has_vehicle_travel_order_broad_access(user):
        return qs
    if _can_employee_access_own_vehicle_travel_order(user, "vehicle_travel_order_list"):
        return qs.filter(employee_id=user.employee_id)
    return qs.none()


class VehicleTravelOrderEmployeeAccessMixin(RolePermissionRequiredMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        permission_code = self.get_permission_code()
        if _is_vehicle_travel_order_employee_self_service(user) and permission_code == "vehicle_travel_order_update":
            return False
        if _is_vehicle_travel_order_employee_self_service(user) and permission_code in EMPLOYEE_VEHICLE_TRAVEL_ORDER_PERMISSIONS:
            if permission_code == "vehicle_travel_order_create":
                return True
            pk = self.kwargs.get("pk")
            return VehicleTravelOrder.objects.filter(pk=pk).exists()
        if user.is_superuser or _user_has_non_employee_role_permission(user, permission_code):
            return True
        if permission_code == "vehicle_travel_order_create":
            return _can_employee_access_own_vehicle_travel_order(user, permission_code)
        if _can_employee_access_own_vehicle_travel_order(user, permission_code):
            pk = self.kwargs.get("pk")
            return VehicleTravelOrder.objects.filter(pk=pk, employee_id=user.employee_id).exists()
        return False


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


def can_print_previous_vehicle_travel_order_report(user, order, previous_order):
    if not previous_order:
        return False
    if user.is_superuser or _user_has_non_employee_role_permission(user, "vehicle_travel_order_fuel_report"):
        return True
    if (
        _is_vehicle_travel_order_employee_self_service(user)
        and _user_has_employee_role_permission(user, "vehicle_travel_order_fuel_report")
    ):
        return True
    expected_previous_order = get_previous_vehicle_travel_order(order)
    return bool(expected_previous_order and expected_previous_order.pk == previous_order.pk)


def vehicle_travel_order_form_manual():
    return mark_safe(
        """
        <h5 class="mb-3">Uputstvo za zaduzenje vozila</h5>
        <ol class="mb-3">
          <li><strong>PN broj</strong> sistem dodeljuje automatski. Polje se ne popunjava rucno.</li>
          <li><strong>Datum otvaranja</strong> je datum od kada zaposleni preuzima auto.</li>
          <li><strong>Zaposleni</strong> je lice na koje se otvara zaduzenje. Za ulogu Zaposleni sistem automatski postavlja prijavljenog korisnika.</li>
          <li><strong>Vozilo</strong> je auto koji se zaduzuje. Izaberite tacno vozilo iz liste.</li>
          <li><strong>Pocetna kilometraza</strong> je stanje kilometraze na dan preuzimanja vozila.</li>
        </ol>
        <h6 class="mb-2">Pravila pri cuvanju</h6>
        <ul class="mb-3">
          <li>Za istog zaposlenog ne moze postojati vise od jednog otvorenog zaduzenja.</li>
          <li>Za isto vozilo ne moze postojati vise od jednog otvorenog zaduzenja.</li>
          <li>Isti zaposleni ne moze imati dva zaduzenja na isti datum.</li>
          <li>Isto vozilo ne moze imati dva zaduzenja na isti datum.</li>
        </ul>
        <h6 class="mb-2">Sta sistem radi automatski</h6>
        <ul class="mb-0">
          <li>Kada se otvori novo zaduzenje za auto koji ima ranije otvoreno zaduzenje, prethodno zaduzenje za taj auto se zatvara datumom novog naloga.</li>
          <li>Ako unesete pocetnu kilometrazu na novom nalogu, ona se upisuje kao krajnja kilometraza prethodnog zaduzenja za isti auto.</li>
          <li>Posle cuvanja otvara se detalj zaduzenja, gde mogu da se stampaju nalog i obracun.</li>
        </ul>
        """
    )


class VehicleTravelOrderListView(LoginRequiredMixin, ListView):
    model = VehicleTravelOrder
    template_name = "fleet/vehicle_travel_order_list.html"
    context_object_name = "travel_orders"

    def get_queryset(self):
        queryset = (
            _vehicle_travel_order_base_qs(self.request)
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
        user = self.request.user
        has_broad_access = _has_vehicle_travel_order_broad_access(user)
        is_employee_self_service = _is_vehicle_travel_order_employee_self_service(user)
        own_employee_id = getattr(user, "employee_id", None)
        selected_employee = self.request.GET.get("employee", "")

        ctx["title"] = "Zaduzenja vozila"
        ctx["status"] = ""
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["selected_vehicle"] = self.request.GET.get("vehicle", "")
        ctx["selected_employee"] = selected_employee
        ctx["is_employee_self_service"] = is_employee_self_service
        ctx["limit_employee_filter_to_self"] = False
        ctx["own_employee_id"] = own_employee_id
        if has_broad_access or is_employee_self_service:
            ctx["vehicles"] = Vehicle.objects.order_by("brand", "model", "inventory_number")
            employees = Employee.objects.filter(
                vehicle_travel_orders__isnull=False
            )
            if own_employee_id:
                employees = employees | Employee.objects.filter(pk=own_employee_id)
            ctx["employees"] = employees.distinct().order_by("last_name", "first_name")
        else:
            own_orders = _vehicle_travel_order_base_qs(self.request)
            ctx["vehicles"] = Vehicle.objects.filter(
                vehicle_travel_orders__in=own_orders,
            ).distinct().order_by("brand", "model", "inventory_number")
            ctx["employees"] = Employee.objects.filter(
                pk=own_employee_id,
            )
        ctx["can_create_vehicle_travel_order"] = (
            has_broad_access
            or _can_employee_access_own_vehicle_travel_order(user, "vehicle_travel_order_create")
        )
        return ctx


class VehicleTravelOrderDetailView(VehicleTravelOrderEmployeeAccessMixin, LoginRequiredMixin, DetailView):
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

        previous_order = get_previous_vehicle_travel_order(order)
        can_print_previous_order_report = can_print_previous_vehicle_travel_order_report(
            self.request.user,
            order,
            previous_order,
        )

        ctx.update(
            {
                "period_start": period_start,
                "period_end": period_end,
                "previous_order": previous_order,
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
                "can_update_vehicle_travel_order": user_has_role_permission(
                    self.request.user,
                    "vehicle_travel_order_update",
                ) and not _is_vehicle_travel_order_employee_self_service(self.request.user),
                "can_close_vehicle_travel_order": user_has_role_permission(self.request.user, "vehicle_travel_order_close"),
                "can_delete_vehicle_travel_order": user_has_role_permission(self.request.user, "vehicle_travel_order_delete"),
                "can_create_previous_vehicle_travel_order": user_has_role_permission(
                    self.request.user,
                    "vehicle_travel_order_previous_create",
                ),
                "can_print_previous_order_report": can_print_previous_order_report,
            }
        )
        previous_report_pk = self.request.GET.get("open_previous_report")
        if ctx["previous_order"] and previous_report_pk == str(ctx["previous_order"].pk):
            ctx["auto_previous_report_url"] = (
                f"{reverse('vehicle_travel_order_fuel_report', args=[ctx['previous_order'].pk])}"
                f"?for_order={order.pk}&next={reverse('vehicle_travel_order_detail', args=[order.pk])}"
            )
        return ctx


class VehicleTravelOrderFuelReportView(VehicleTravelOrderDetailView):
    template_name = "fleet/vehicle_travel_order_fuel_report.html"

    def test_func(self):
        if super().test_func():
            return True
        user = self.request.user
        if not (
            _is_vehicle_travel_order_employee_self_service(user)
            and _user_has_employee_role_permission(user, "vehicle_travel_order_fuel_report")
        ):
            return False
        current_order_pk = self.request.GET.get("for_order")
        if not current_order_pk:
            return False
        current_order = VehicleTravelOrder.objects.filter(
            pk=current_order_pk,
            employee_id=user.employee_id,
        ).select_related("vehicle", "employee").first()
        previous_order = VehicleTravelOrder.objects.filter(
            pk=self.kwargs.get("pk"),
        ).select_related("vehicle", "employee").first()
        return can_print_previous_vehicle_travel_order_report(user, current_order, previous_order)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["next_url"] = reverse("vehicle_travel_order_list")
        return ctx


class VehicleTravelOrderCreateView(VehicleTravelOrderEmployeeAccessMixin, LoginRequiredMixin, CreateView):
    model = VehicleTravelOrder
    form_class = VehicleTravelOrderForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("vehicle_travel_order_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi putni nalog (vozilo)"
        ctx["submit_button_label"] = "Sacuvaj"
        ctx["manual"] = vehicle_travel_order_form_manual()
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["limit_to_user_employee"] = (
            _is_vehicle_travel_order_employee_self_service(self.request.user)
            or not _has_vehicle_travel_order_broad_access(self.request.user)
        )
        return kwargs

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
        return reverse("vehicle_travel_order_detail", args=[self.object.pk])


class VehicleTravelOrderUpdateView(VehicleTravelOrderEmployeeAccessMixin, LoginRequiredMixin, UpdateView):
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
        ctx["manual"] = vehicle_travel_order_form_manual()
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["limit_to_user_employee"] = _is_vehicle_travel_order_employee_self_service(self.request.user)
        return kwargs

    def get_success_url(self):
        return reverse("vehicle_travel_order_detail", args=[self.object.pk])


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


class PreviousVehicleTravelOrderCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = VehicleTravelOrder
    form_class = PreviousVehicleTravelOrderForm
    template_name = "fleet/generic_form.html"
    required_permission_code = "vehicle_travel_order_previous_create"

    def dispatch(self, request, *args, **kwargs):
        self.next_order = get_object_or_404(
            VehicleTravelOrder.objects.select_related("vehicle", "employee"),
            pk=kwargs.get("pk"),
        )
        if get_previous_vehicle_travel_order(self.next_order):
            messages.info(request, "Prethodno zaduzenje vec postoji za ovaj automobil.")
            return redirect("vehicle_travel_order_detail", pk=self.next_order.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["employee"] = self.next_order.employee_id
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["next_order"] = self.next_order
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Unos prethodnog zaduzenja za obracun goriva"
        ctx["submit_button_label"] = "Sacuvaj prethodno zaduzenje"
        ctx["form_help"] = (
            "Ovaj unos sluzi samo kada ne postoji prethodno zaduzenje za automobil. "
            f"Sistem ce ga automatski zatvoriti datumom {self.next_order.created_at:%d.%m.%Y}. "
            "Posle cuvanja vracate se na zaduzenje sa kog ste krenuli i obracun goriva ce biti dostupan."
        )
        ctx["cancel_url"] = reverse("vehicle_travel_order_detail", args=[self.next_order.pk])
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.vehicle = self.next_order.vehicle
        self.object.closed_at = self.next_order.created_at
        self.object.end_mileage = self.next_order.start_mileage
        self.object.save()
        messages.success(
            self.request,
            "Prethodno zaduzenje je uneto i automatski zatvoreno. Obracun goriva je sada dostupan.",
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        detail_url = reverse("vehicle_travel_order_detail", args=[self.next_order.pk])
        return f"{detail_url}?open_previous_report={self.object.pk}"


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
        return reverse("vehicle_travel_order_list")


class VehicleTravelOrderRequestView(VehicleTravelOrderEmployeeAccessMixin, LoginRequiredMixin, TemplateView):
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


class VehicleTravelOrderPrintOpenView(VehicleTravelOrderEmployeeAccessMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/vehicle_travel_order_print_open.html"

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
                    f"{reverse('vehicle_travel_order_fuel_report', args=[previous_order.pk])}?for_order={order.pk}"
                    if previous_order
                    else ""
                ),
            }
        )
        return ctx
