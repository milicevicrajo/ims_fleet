from collections import defaultdict
import csv
import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery, Sum
from django.db.models.functions import TruncMonth, TruncYear
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from core.exporting import csv_attachment_response
from core.mixins import RolePermissionRequiredMixin, role_permission_required

from .analytics_helpers import is_red_zone, net_maintenance_cost
from .filters import VehicleFilter
from .models import (
    FuelConsumption,
    Insurance,
    JobCode,
    Lease,
    LeaseInterest,
    Policy,
    PutniNalog,
    TrafficCard,
    Vehicle,
    VehicleTravelOrder,
)
from .utils import calculate_average_fuel_consumption, calculate_average_fuel_consumption_ever
from .vehicle_forms import VehicleForm

LONG_TERM_LEASE_TYPES = set(Lease.LONG_TERM_LEASE_TYPE_VALUES)


class VehicleListView(LoginRequiredMixin, FilterView):
    model = Vehicle
    template_name = "fleet/vehicle_list.html"
    context_object_name = "vehicles"
    filterset_class = VehicleFilter

    def get_queryset(self):
        qs = Vehicle.objects.all()

        latest_job_code_qs = JobCode.objects.filter(vehicle=OuterRef("pk")).order_by("-assigned_date", "-pk")

        latest_job_code_id_subquery = latest_job_code_qs.values("id")[:1]
        latest_org_unit_id_subquery = latest_job_code_qs.values("organizational_unit_id")[:1]
        latest_org_unit_code_subquery = latest_job_code_qs.values("organizational_unit__code")[:1]
        latest_center_subquery = latest_job_code_qs.values("organizational_unit__center")[:1]

        latest_traffic_card_subquery = TrafficCard.objects.filter(vehicle=OuterRef("pk")).order_by("-issue_date").values("registration_number")[:1]

        last_mileage_subquery = FuelConsumption.objects.filter(vehicle=OuterRef("pk")).order_by("-mileage").values("mileage")[:1]

        qs = Vehicle.objects.annotate(current_ou_id=Subquery(latest_org_unit_id_subquery))

        qs = qs.annotate(
            latest_job_code_id=Subquery(latest_job_code_id_subquery),
            latest_org_unit=Subquery(latest_center_subquery),
            latest_org_unit_code=Subquery(latest_org_unit_code_subquery),
            registration_number=Subquery(latest_traffic_card_subquery),
            total_repairs=Sum("service_transactions__potrazuje"),
            mileage=Subquery(last_mileage_subquery),
        )

        get = self.request.GET
        if "status" not in get and "show_archived" not in get:
            qs = qs.filter(otpis=False)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        vehicles = ctx.get("vehicles") or ctx.get("object_list")
        vehicle_consumption_data = {}
        for vehicle in vehicles:
            vehicle_consumption_data[vehicle.id] = calculate_average_fuel_consumption(vehicle)

        ctx["vehicle_consumption_data"] = vehicle_consumption_data
        ctx["title"] = "Lista vozila"
        ctx.setdefault("current_app", "fleet")
        return ctx


def _vehicle_list_base_queryset(request):
    qs = Vehicle.objects.all()

    latest_job_code_qs = JobCode.objects.filter(vehicle=OuterRef("pk")).order_by("-assigned_date", "-pk")

    latest_job_code_id_subquery = latest_job_code_qs.values("id")[:1]
    latest_org_unit_id_subquery = latest_job_code_qs.values("organizational_unit_id")[:1]
    latest_org_unit_code_subquery = latest_job_code_qs.values("organizational_unit__code")[:1]
    latest_center_subquery = latest_job_code_qs.values("organizational_unit__center")[:1]

    latest_traffic_card_subquery = TrafficCard.objects.filter(vehicle=OuterRef("pk")).order_by("-issue_date").values("registration_number")[:1]

    last_mileage_subquery = FuelConsumption.objects.filter(vehicle=OuterRef("pk")).order_by("-mileage").values("mileage")[:1]

    qs = Vehicle.objects.annotate(current_ou_id=Subquery(latest_org_unit_id_subquery))

    qs = qs.annotate(
        latest_job_code_id=Subquery(latest_job_code_id_subquery),
        latest_org_unit=Subquery(latest_center_subquery),
        latest_org_unit_code=Subquery(latest_org_unit_code_subquery),
        registration_number=Subquery(latest_traffic_card_subquery),
        total_repairs=Sum("service_transactions__potrazuje"),
        mileage=Subquery(last_mileage_subquery),
    )

    get = request.GET
    if "status" not in get and "show_archived" not in get:
        qs = qs.filter(otpis=False)
    return qs


@role_permission_required()
def vehicle_export_csv(request):
    base_qs = _vehicle_list_base_queryset(request)
    vehicle_filter = VehicleFilter(request.GET, queryset=base_qs)
    qs = vehicle_filter.qs

    response = csv_attachment_response("vozila.csv", quoted=True)
    response.write("\ufeff")

    writer = csv.writer(response, delimiter=";")
    writer.writerow(
        [
            "Registracija",
            "Marka",
            "Tip",
            "Godište",
            "Kilometraža",
            "Potrošnja",
            "Kategorija",
            "Centar",
            "Kubikaža",
        ]
    )

    for vehicle in qs:
        avg_consumption = calculate_average_fuel_consumption(vehicle)
        writer.writerow(
            [
                vehicle.registration_number or "",
                vehicle.brand or "",
                vehicle.model or "",
                vehicle.year_of_manufacture or "",
                vehicle.mileage or "",
                f"{avg_consumption:.2f}" if avg_consumption is not None else "0",
                vehicle.category or "",
                vehicle.latest_org_unit_code or "",
                f"{vehicle.engine_volume:.0f}" if vehicle.engine_volume is not None else "",
            ]
        )

    return response


class VehicleDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Vehicle
    template_name = "fleet/vehicle_detail.html"
    context_object_name = "vehicle"

    def get(self, request, *args, **kwargs):
        vehicle = self.get_object()

        latest_org_unit_subquery = JobCode.objects.filter(vehicle_id=OuterRef("pk")).order_by("-assigned_date").values("organizational_unit__center")[:1]

        vehicle_with_latest_org_unit = Vehicle.objects.annotate(
            latest_org_unit=Subquery(latest_org_unit_subquery)
        ).get(pk=vehicle.pk)

        user_allowed_centers_manager = request.user.allowed_centers
        if user_allowed_centers_manager.exists():
            allowed_centers_codes = user_allowed_centers_manager.values_list("center", flat=True)
            if (
                vehicle_with_latest_org_unit.latest_org_unit is not None
                and vehicle_with_latest_org_unit.latest_org_unit not in allowed_centers_codes
            ):
                return HttpResponseForbidden("Nemate dozvolu za pristup ovom vozilu.")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = self.get_object()

        active_policies = Policy.objects.filter(vehicle=vehicle, end_date__gte=datetime.date.today())
        current_job_code = JobCode.objects.filter(vehicle=vehicle).order_by("-assigned_date").first()
        job_codes = JobCode.objects.filter(vehicle=vehicle).order_by("-assigned_date")

        nis_card = vehicle.nis_transactions.filter().first()
        omv_card = vehicle.omv_transactions.filter().first()
        mileage = vehicle.fuel_consumptions.order_by("-mileage").values_list("mileage", flat=True).first()

        consumptions = vehicle.fuel_consumptions.all()
        average_consumption = calculate_average_fuel_consumption(vehicle)
        average_consumption_ever = calculate_average_fuel_consumption_ever(vehicle)

        fuel_data = (
            FuelConsumption.objects.filter(vehicle=vehicle)
            .annotate(month=TruncMonth("date"), year=TruncYear("date"))
            .values("month", "year", "supplier")
            .annotate(total_liters=Sum("amount"), total_cost_bruto=Sum("cost_bruto"))
            .order_by("year", "month", "supplier")
        )

        omv_data = fuel_data.filter(supplier="OMV")
        nis_data = fuel_data.filter(supplier="NIS")

        lease_info = Lease.objects.filter(vehicle=vehicle).order_by("-start_date").first()
        long_term_rental = Lease.objects.filter(vehicle=vehicle, lease_type__in=LONG_TERM_LEASE_TYPES).exists()
        lease_intrests = LeaseInterest.objects.filter(lease=lease_info).order_by("-year")

        repair_costs = vehicle.service_transactions.aggregate(total_repairs=Sum("potrazuje"))["total_repairs"] or 0
        requisition_costs = vehicle.requisitions.aggregate(total_requisitions=Sum("vrednost_nab"))["total_requisitions"] or 0
        insurance_recovery = vehicle.insurances.filter(kola=True).aggregate(total=Sum("potrazuje"))["total"] or 0

        service_list = vehicle.service_transactions.order_by("-datum")
        requisition_list = vehicle.requisitions.order_by("-datum_trebovanja")
        putni_nalozi = PutniNalog.objects.filter(vehicle=vehicle).select_related("employee", "job_code").order_by("-travel_date", "-id")
        vehicle_travel_orders = VehicleTravelOrder.objects.filter(vehicle=vehicle).select_related("employee").order_by("-created_at", "-id")

        trafic_cards = TrafficCard.objects.filter(vehicle=vehicle).order_by("-issue_date")
        trafic_card = trafic_cards.first()
        status_light = "green" if repair_costs < vehicle.purchase_value else "red"

        vehicle_value = vehicle.value or vehicle.purchase_value or 0
        total_fuel_cost = vehicle.fuel_consumptions.aggregate(total=Sum("cost_bruto"))["total"] or 0
        total_fuel_liters = vehicle.fuel_consumptions.aggregate(total=Sum("amount"))["total"] or 0
        gross_maintenance_cost = repair_costs + requisition_costs
        total_maintenance_cost = net_maintenance_cost(repair_costs, requisition_costs, insurance_recovery)
        maintenance_value_ratio = (total_maintenance_cost / vehicle_value * 100) if vehicle_value else 0
        remaining_value_after_maintenance = vehicle_value - total_maintenance_cost
        red_zone = is_red_zone(long_term_rental, vehicle_value, total_maintenance_cost)

        def month_date(value):
            return value.date() if hasattr(value, "date") else value

        monthly_costs = defaultdict(lambda: {"fuel": 0, "service": 0})
        for row in vehicle.fuel_consumptions.annotate(month=TruncMonth("date")).values("month").annotate(total=Sum("cost_bruto")).order_by("month"):
            if row["month"]:
                monthly_costs[month_date(row["month"])]["fuel"] = float(row["total"] or 0)
        for row in vehicle.service_transactions.annotate(month=TruncMonth("datum")).values("month").annotate(total=Sum("potrazuje")).order_by("month"):
            if row["month"]:
                monthly_costs[month_date(row["month"])]["service"] = float(row["total"] or 0)

        monthly_vehicle_costs = [
            {"label": month.strftime("%m.%Y"), "fuel": values["fuel"], "service": values["service"]}
            for month, values in sorted(monthly_costs.items())
        ][-12:]

        service_category_rows = [
            {
                "label": row["popravka_kategorija__name"] or "Nerazvrstano",
                "value": float(row["total"] or 0),
            }
            for row in vehicle.service_transactions.values("popravka_kategorija__name")
            .annotate(total=Sum("potrazuje"))
            .order_by("-total")[:8]
        ]

        vehicle_analysis = {
            "total_fuel_cost": total_fuel_cost,
            "total_fuel_liters": total_fuel_liters,
            "gross_maintenance_cost": gross_maintenance_cost,
            "insurance_recovery": insurance_recovery,
            "total_maintenance_cost": total_maintenance_cost,
            "maintenance_value_ratio": maintenance_value_ratio,
            "remaining_value_after_maintenance": remaining_value_after_maintenance,
            "red_zone": red_zone,
            "vehicle_value": vehicle_value,
            "fuel_cost_per_liter": total_fuel_cost / total_fuel_liters if total_fuel_liters else 0,
            "long_term_rental": long_term_rental,
        }

        context.update(
            {
                "lease_info": lease_info,
                "lease_intrests": lease_intrests,
                "nis_card": nis_card,
                "omv_card": omv_card,
                "mileage": mileage,
                "active_policies": active_policies,
                "average_consumption": average_consumption,
                "average_consumption_ever": average_consumption_ever,
                "omv_data": omv_data,
                "nis_data": nis_data,
                "current_job_code": current_job_code,
                "job_codes": job_codes,
                "status_light": status_light,
                "repair_costs": repair_costs,
                "requisition_costs": requisition_costs,
                "insurance_recovery": insurance_recovery,
                "service_list": service_list,
                "requisition_list": requisition_list,
                "putni_nalozi": putni_nalozi,
                "vehicle_travel_orders": vehicle_travel_orders,
                "consumptions": consumptions,
                "trafic_cards": trafic_cards,
                "trafic_card": trafic_card,
                "vehicle_analysis": vehicle_analysis,
                "monthly_vehicle_costs": monthly_vehicle_costs,
                "service_category_rows": service_category_rows,
                "tender_documents": vehicle.tender_documents.order_by("-created_at"),
                "tender_document_create_url": reverse("vehicle_tender_document_create_for_vehicle", kwargs={"vehicle_id": vehicle.pk}),
                "title": f"Detalji vozila {self.object.brand} {self.object.model}",
            }
        )
        return context


class VehicleCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("vehicle_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect("trafficcard_create", vehicle_id=self.object.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiraj novo vozilo"
        context["submit_button_label"] = "Dodaj vozilo"
        return context


class VehicleUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("vehicle_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni podatke vozila"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class VehicleTogleStatusView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.otpis = not vehicle.otpis
        vehicle.save()
        status = "aktivano" if vehicle.otpis else "otpisano"
        messages.success(request, f"Vozilo je uspešno {status}.")
        return redirect("vehicle_detail", pk=pk)


class VehicleDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Vehicle
    success_url = reverse_lazy("vehicle_list")
    template_name = "fleet/vehicle_confirm_delete.html"
    context_object_name = "vehicle"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obriši vozilo"
        return context
