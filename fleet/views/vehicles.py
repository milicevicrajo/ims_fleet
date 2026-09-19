import csv
import datetime
from io import BytesIO
import posixpath
import re
import zipfile

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery, Sum, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from core.exporting import csv_attachment_response
from core.mixins import RolePermissionRequiredMixin, role_permission_required

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

        latest_traffic_card_subquery = TrafficCard.objects.issued().filter(vehicle=OuterRef("pk")).order_by("-issue_date", "-id").values("registration_number")[:1]

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

    latest_traffic_card_subquery = TrafficCard.objects.issued().filter(vehicle=OuterRef("pk")).order_by("-issue_date", "-id").values("registration_number")[:1]

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

    def get_queryset(self):
        from fleet.services.economics import visible_vehicles
        return visible_vehicles(self.request.user, include_retired=True)

    def get_context_data(self, **kwargs):
        from fleet.support.vehicle_detail import VehiclePeriodForm
        from fleet.support.vehicle_mileage import vehicle_mileage
        from fleet.support.vehicle_maintenance import vehicle_maintenance
        from django.utils import timezone
        from fleet.services.economics import period_analysis, METHODOLOGY, VERSION
        from fleet.models import VehicleEconomicAssessment
        from core.mixins import user_has_role_permission

        context = super().get_context_data(**kwargs)
        vehicle = self.object
        today = timezone.localdate()
        month_index = today.year * 12 + today.month - 1 - 11
        first_month = datetime.date(month_index // 12, month_index % 12 + 1, 1)
        params = self.request.GET
        period_form = VehiclePeriodForm(params if ('start' in params or 'end' in params) else None,
                                        initial={'start': first_month, 'end': today})
        valid_period = not period_form.is_bound or period_form.is_valid()
        start, end = first_month, today
        if period_form.is_bound and valid_period:
            start, end = period_form.cleaned_data['start'], period_form.cleaned_data['end']
        # Invalid filters show errors and no financial results; never silently substitute a period.
        from fleet.support.vehicle_detail import period_presets
        presets = period_presets(today, start, end)
        economics = period_analysis([vehicle], start, end)[0] if valid_period else None
        fuel = economics['fuel'] if economics else []
        services = economics['services'] if economics else []
        requisitions = economics['requisitions'] if economics else []
        recoveries = economics['recoveries'] if economics else []
        analytics = economics['ledger'] if economics else None
        cards = vehicle.traffic_cards.order_by('-issue_date', '-id')
        card = cards.issued().first()
        holding = vehicle.holdings.filter(start_date__lte=today).filter(Q(end_date__isnull=True) | Q(end_date__gte=today)).select_related('lease').first()
        active_lease = vehicle.leases.filter(start_date__lte=today, end_date__gte=today).order_by('-start_date', '-id').first()
        holding_lease = holding.lease if holding else active_lease
        holding_label = holding.get_basis_display() if holding else ('Ugovorno raspolaganje — proveriti period' if active_lease else 'Osnov nije potvrđen')
        ao_policy = vehicle.policies.filter(insurance_type__icontains='AUTOODGOVORNOST', start_date__lte=today, end_date__isnull=False).order_by('-end_date', '-id').first()
        registration_days = (card.registration_valid_until - today).days if card and card.registration_valid_until else None
        context.update({
            'economics': economics, 'methodology': METHODOLOGY, 'methodology_version': VERSION,
            'can_edit_analysis': user_has_role_permission(self.request.user, 'vehicle_analysis_settings'),
            'assessments': VehicleEconomicAssessment.objects.filter(vehicle=vehicle),
            'mileage': vehicle_mileage(vehicle, params, today),
            'maintenance': vehicle_maintenance(vehicle, today),
            'mileage_other_filters': [(key, value) for key, value in params.items() if key not in ('mileage_from', 'mileage_to')],
            'today': today, 'period_form': period_form, 'period_valid': valid_period,
            'period_start': start, 'period_end': end, 'analytics': analytics,
            'period_presets': presets,
            'consumptions': fuel, 'service_list': services, 'requisition_list': requisitions,
            'recovery_list': recoveries,
            'current_job_code': vehicle.job_codes.filter(assigned_date__lte=today).select_related('organizational_unit').order_by('-assigned_date', '-id').first(),
            'job_codes': vehicle.job_codes.select_related('organizational_unit').order_by('-assigned_date', '-id'),
            'holdings': vehicle.holdings.select_related('lease', 'financing_contract'), 'current_holding': holding,
            'holding_label': holding_label, 'holding_lease': holding_lease, 'ao_policy': ao_policy,
            'leases': vehicle.leases.order_by('-start_date', '-id'),
            'policies': vehicle.policies.order_by('-end_date', '-id'),
            'active_policies': vehicle.policies.filter(start_date__lte=today, end_date__gte=today),
            'trafic_card': card, 'latest_traffic_card': card, 'trafic_cards': cards,
            'previous_traffic_cards': cards.issued().exclude(pk=card.pk) if card else cards.none(),
            'registration_days': registration_days,
            'putni_nalozi': PutniNalog.objects.filter(vehicle=vehicle).select_related('employee', 'job_code').order_by('-travel_date', '-id'),
            'vehicle_travel_orders': VehicleTravelOrder.objects.filter(vehicle=vehicle).select_related('employee').order_by('-created_at', '-id'),
            'tender_documents': vehicle.tender_documents.order_by('-created_at'),
            'latest_sticker_document': vehicle.tender_documents.filter(document_type=VehicleTenderDocument.DocumentType.STICKER, is_active=True).order_by('-created_at').first(),
            'tender_document_create_url': reverse('vehicle_tender_document_create_for_vehicle', kwargs={'vehicle_id': vehicle.pk}),
            'title': f'Detalji vozila {vehicle.brand} {vehicle.model}',
        })
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
