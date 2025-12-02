from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from urllib.parse import quote
from decimal import Decimal
from django_filters.views import FilterView
from django.views import View
from django.views.generic import CreateView, UpdateView, TemplateView, ListView, DeleteView

from .filters import KvarFilter
from .forms import KvarForm, KvarPartForm, VehicleTravelOrderForm, VehicleTravelOrderCloseForm
from .models import Kvar, JobCode, KvarPart, VehicleTravelOrder


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


class KvarIMSListView(LoginRequiredMixin, TemplateView):
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


class KvarVanIMSListView(LoginRequiredMixin, TemplateView):
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


class GarazaHomeView(LoginRequiredMixin, TemplateView):
    template_name = "fleet/garaza_home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Poslovi garaze IMS"
        return ctx


class KvarPrintView(LoginRequiredMixin, TemplateView):
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


class KvarWorkOrderView(LoginRequiredMixin, TemplateView):
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


class KvarTrebovanjeView(LoginRequiredMixin, TemplateView):
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
        parts_display = list(parts_qs)[:MAX_ROWS]
        rows = parts_display + [None] * max(0, MAX_ROWS - len(parts_display))

        ctx.update(
            {
                "kvar": kvar,
                "vehicle": vehicle,
                "registration_number": getattr(traffic_card, "registration_number", ""),
                "organizational_unit": getattr(latest_jobcode, "organizational_unit", None),
                "center": getattr(latest_jobcode.organizational_unit, "center", "") if latest_jobcode and latest_jobcode.organizational_unit else "",
                "rows": rows,
                "is_van_ims": kvar.van_ims,
                "auto_print": self.request.GET.get("auto") == "1",
                "next_url": self.request.GET.get("next") or reverse("kvar_list"),
            }
        )
        return ctx


class KvarDetailView(LoginRequiredMixin, TemplateView):
    template_name = "fleet/kvar_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.kvar = get_object_or_404(
            Kvar.objects.select_related("vehicle"), pk=kwargs.get("pk")
        )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Dozvoli unos stavki ako je IMS popravka ili servis van IMS-a (zahtev za uslugu)
        if not self.kvar.van_ims and self.kvar.work_type != Kvar.WorkType.POPRAVKA:
            messages.warning(request, "Stavke mozes dodavati samo za IMS popravke ili servis van IMS-a.")
            return redirect("kvar_detail", pk=self.kvar.pk)
        form = KvarPartForm(request.POST)
        if form.is_valid():
            part = form.save(commit=False)
            part.kvar = self.kvar
            part.save()
            messages.success(request, "Deo je dodat.")
        else:
            messages.error(request, "Proveri unete podatke za deo.")
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


class KvarCreateView(LoginRequiredMixin, CreateView):
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


class KvarUpdateView(LoginRequiredMixin, UpdateView):
    model = Kvar
    form_class = KvarForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("kvar_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmeni kvar"
        ctx["submit_button_label"] = "Sacuvaj izmene"
        return ctx


class KvarDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("kvar_list")

    def post(self, request, *args, **kwargs):
        kvar = get_object_or_404(Kvar, pk=kwargs.get("pk"))
        kvar.delete()
        messages.success(request, "Kvar je obrisan.")
        return redirect(self.success_url)

    def get(self, request, *args, **kwargs):
        return redirect(self.success_url)


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


class VehicleTravelOrderCreateView(LoginRequiredMixin, CreateView):
    model = VehicleTravelOrder
    form_class = VehicleTravelOrderForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("vehicle_travel_order_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi putni nalog (vozilo)"
        ctx["submit_button_label"] = "Sacuvaj"
        return ctx


class VehicleTravelOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = VehicleTravelOrder
    form_class = VehicleTravelOrderForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("vehicle_travel_order_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmena putnog naloga (vozilo)"
        ctx["submit_button_label"] = "Sacuvaj izmene"
        return ctx


class VehicleTravelOrderCloseView(LoginRequiredMixin, UpdateView):
    model = VehicleTravelOrder
    form_class = VehicleTravelOrderCloseForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("vehicle_travel_order_open_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Zatvori putni nalog (vozilo)"
        ctx["submit_button_label"] = "Zatvori"
        return ctx


class VehicleTravelOrderDeleteView(LoginRequiredMixin, DeleteView):
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


class VehicleTravelOrderRequestView(LoginRequiredMixin, TemplateView):
    template_name = "fleet/vehicle_travel_order_request.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = get_object_or_404(
            VehicleTravelOrder.objects.select_related("vehicle", "employee"),
            pk=kwargs.get("pk"),
        )
        vehicle = order.vehicle
        traffic_card = vehicle.traffic_cards.order_by("-issue_date", "-id").first()
        ctx.update(
            {
                "order": order,
                "vehicle": vehicle,
                "employee": order.employee,
                "registration_number": getattr(traffic_card, "registration_number", ""),
                "next_url": self.request.GET.get("next") or reverse("vehicle_travel_order_open_list"),
            }
        )
        return ctx
