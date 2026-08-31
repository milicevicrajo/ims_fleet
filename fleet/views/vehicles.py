from collections import defaultdict
import csv
import datetime
from io import BytesIO
import posixpath
import re
import zipfile

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from core.exporting import csv_attachment_response
from core.mixins import RolePermissionRequiredMixin, role_permission_required

from ..support.analytics import cost_per_km_status, fixed_cost_per_km_threshold, is_red_zone, net_maintenance_cost
from ..support.dashboard import vehicle_cost_per_km_rows
from ..filters import VehicleFilter
from ..models import (
    FuelConsumption,
    Insurance,
    JobCode,
    Lease,
    LeaseInterest,
    Policy,
    PutniNalog,
    TrafficCard,
    Vehicle,
    VehicleTenderDocument,
    VehicleTravelOrder,
)
from ..support.fuel import (
    calculate_average_fuel_consumption,
    calculate_average_fuel_consumption_ever,
    get_vehicle_fuel_transaction_rows,
)
from ..forms.vehicles import VehicleForm

LONG_TERM_LEASE_TYPES = set(Lease.LONG_TERM_LEASE_TYPE_VALUES)


def _safe_next_url(request, next_url):
    if not next_url:
        return None
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return None
    if next_url == request.path:
        return None
    return next_url


def _safe_zip_name(value, fallback="dokument"):
    value = (value or fallback).strip()
    value = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE)
    value = value.strip("._-")
    return value or fallback


def _file_extension(file_field):
    filename = posixpath.basename(file_field.name or "")
    extension = posixpath.splitext(filename)[1]
    return extension or ".bin"


def _write_storage_file(zip_file, file_field, archive_name):
    if not file_field or not file_field.name:
        return False

    storage = file_field.storage
    if not storage.exists(file_field.name):
        return False

    with storage.open(file_field.name, "rb") as source:
        zip_file.writestr(archive_name, source.read())
    return True


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
                vehicle.get_category_display() or "",
                vehicle.latest_org_unit_code or "",
                f"{vehicle.engine_volume:.0f}" if vehicle.engine_volume is not None else "",
            ]
        )

    return response


@role_permission_required("vehicle_detail")
def vehicle_tender_documentation_zip(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

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

    traffic_cards = TrafficCard.objects.filter(vehicle=vehicle).order_by("-issue_date", "-id")
    latest_traffic_card = traffic_cards.first()
    registration = latest_traffic_card.registration_number if latest_traffic_card else None
    zip_base_name = _safe_zip_name(registration, fallback=f"vozilo_{vehicle.pk}")

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for index, card in enumerate(traffic_cards, start=1):
            card_folder = _safe_zip_name(card.registration_number, fallback=f"saobracajna_{index}")
            base_folder = f"saobracajna_dozvola/{index:02d}_{card_folder}"

            _write_storage_file(
                zip_file,
                card.traffic_card_pdf,
                f"{base_folder}/ocitana_saobracajna_dozvola{_file_extension(card.traffic_card_pdf)}",
            )
            _write_storage_file(
                zip_file,
                card.traffic_card_front_image,
                f"{base_folder}/prednja_strana{_file_extension(card.traffic_card_front_image)}",
            )
            _write_storage_file(
                zip_file,
                card.traffic_card_back_image,
                f"{base_folder}/zadnja_strana{_file_extension(card.traffic_card_back_image)}",
            )

        tender_documents = vehicle.tender_documents.order_by("-created_at", "-id")
        for index, document in enumerate(tender_documents, start=1):
            document_type = _safe_zip_name(document.get_document_type_display(), fallback="dokument")
            title = _safe_zip_name(document.title, fallback=f"dokument_{index}")
            archive_name = (
                f"tenderska_dokumentacija/{index:02d}_{document_type}_{title}"
                f"{_file_extension(document.image)}"
            )
            _write_storage_file(zip_file, document.image, archive_name)

    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{zip_base_name}_tenderska_dokumentacija.zip"'
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
        consumptions = get_vehicle_fuel_transaction_rows(vehicle)
        mileage_values = [row["mileage"] for row in consumptions if row["mileage"]]
        mileage = (
            max(mileage_values)
            if mileage_values
            else vehicle.fuel_consumptions.order_by("-mileage").values_list("mileage", flat=True).first()
        )
        average_consumption = calculate_average_fuel_consumption(vehicle)
        average_consumption_ever = calculate_average_fuel_consumption_ever(vehicle)

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
        latest_sticker_document = (
            vehicle.tender_documents.filter(
                document_type=VehicleTenderDocument.DocumentType.STICKER,
                is_active=True,
            )
            .order_by("-created_at")
            .first()
        )
        status_light = "green" if repair_costs < vehicle.purchase_value else "red"

        vehicle_value = vehicle.value or vehicle.purchase_value or 0
        total_fuel_cost = sum((row["cost_bruto"] or 0) for row in consumptions)
        total_fuel_liters = sum((row["amount"] or 0) for row in consumptions)
        gross_maintenance_cost = repair_costs + requisition_costs
        total_maintenance_cost = net_maintenance_cost(repair_costs, requisition_costs, insurance_recovery)
        maintenance_value_ratio = (total_maintenance_cost / vehicle_value * 100) if vehicle_value else 0
        remaining_value_after_maintenance = vehicle_value - total_maintenance_cost
        red_zone = is_red_zone(long_term_rental, vehicle_value, total_maintenance_cost)

        def month_date(value):
            value = value.date() if hasattr(value, "date") else value
            return value.replace(day=1) if value else value

        monthly_costs = defaultdict(lambda: {"fuel": 0, "service": 0})
        for row in consumptions:
            if row["date"]:
                monthly_costs[month_date(row["date"])]["fuel"] += float(row["cost_bruto"] or 0)
        for row in vehicle.service_transactions.annotate(month=TruncMonth("datum")).values("month").annotate(total=Sum("potrazuje")).order_by("month"):
            if row["month"]:
                monthly_costs[month_date(row["month"])]["service"] = float(row["total"] or 0)

        monthly_vehicle_costs = [
            {"label": month.strftime("%m.%Y"), "fuel": values["fuel"], "service": values["service"]}
            for month, values in sorted(monthly_costs.items())
        ][-12:]

        cost_per_km_periods = [
            {
                "label": "Poslednjih 12 meseci (okvirno)",
                "start": datetime.date.today() - datetime.timedelta(days=365),
                "end": datetime.date.today(),
            },
            {
                "label": "Poslednja 24 meseca (okvirno)",
                "start": datetime.date.today() - datetime.timedelta(days=730),
                "end": datetime.date.today(),
            },
        ]
        vehicle_cost_per_km_details = []
        vehicle_cost_per_km_12m = None
        for period in cost_per_km_periods:
            row = next(
                iter(
                    vehicle_cost_per_km_rows(
                        period_start_date=period["start"],
                        period_end_date=period["end"],
                        vehicle_ids=[vehicle.id],
                    )
                ),
                None,
            )
            threshold = fixed_cost_per_km_threshold((row or {}).get("maximum_permissible_weight", vehicle.maximum_permissible_weight))
            status = cost_per_km_status((row or {}).get("cost_per_km"), threshold)
            vehicle_cost_per_km_details.append(
                {
                    "period_label": period["label"],
                    "row": row,
                    "threshold": threshold,
                    "status": status,
                }
            )
            if vehicle_cost_per_km_12m is None:
                vehicle_cost_per_km_12m = vehicle_cost_per_km_details[-1]

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
                "latest_traffic_card": trafic_card,
                "vehicle_analysis": vehicle_analysis,
                "monthly_vehicle_costs": monthly_vehicle_costs,
                "service_category_rows": service_category_rows,
                "vehicle_cost_per_km_details": vehicle_cost_per_km_details,
                "vehicle_cost_per_km_12m": vehicle_cost_per_km_12m,
                "tender_documents": vehicle.tender_documents.order_by("-created_at"),
                "latest_sticker_document": latest_sticker_document,
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
        if vehicle.otpis and not request.user.is_superuser:
            return HttpResponseForbidden("Samo superuser moze da vrati vozilo u upotrebu.")

        vehicle.otpis = not vehicle.otpis
        vehicle.save()

        status = "otpisano" if vehicle.otpis else "aktivirano"
        messages.success(request, f"Vozilo je uspešno {status}.")

        next_url = _safe_next_url(
            request,
            request.POST.get("next") or request.GET.get("next") or request.META.get("HTTP_REFERER"),
        )
        if next_url:
            return redirect(next_url)

        return redirect("vehicle_detail", pk=pk)


class VehicleRestoreView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_superuser:
            return HttpResponseForbidden("Samo superuser moze da vrati vozilo u upotrebu.")

        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.otpis = False
        vehicle.save(update_fields=["otpis"])
        messages.success(request, "Vozilo je vraceno u upotrebu.")

        next_url = _safe_next_url(
            request,
            request.POST.get("next") or request.GET.get("next") or request.META.get("HTTP_REFERER"),
        )
        if next_url:
            return redirect(next_url)

        return redirect("vehicle_list")


class VehicleDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Vehicle
    success_url = reverse_lazy("vehicle_list")
    template_name = "fleet/vehicle_confirm_delete.html"
    context_object_name = "vehicle"

    def _next_url(self):
        return _safe_next_url(
            self.request,
            self.request.POST.get("next") or self.request.GET.get("next") or self.request.META.get("HTTP_REFERER"),
        )

    def get_success_url(self):
        return self._next_url() or str(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obriši vozilo"
        context["next_url"] = self._next_url() or reverse("vehicle_list")
        return context
