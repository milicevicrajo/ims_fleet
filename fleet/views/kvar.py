from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin

from ..filters import KvarFilter
from ..forms.garaza import KvarForm, KvarPartForm
from ..models import JobCode, Kvar, KvarPart, Vehicle
from ..support.garaza import ensure_auto_parts


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
        ctx["title"] = "Kvarovi (garaža)"
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
        kvar = Kvar.objects.select_related("vehicle").get(pk=self.kvar_obj.pk)
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
        max_rows = 12
        parts_qs = ensure_auto_parts(kvar) if not kvar.van_ims else list(kvar.parts.all())
        parts_list = list(parts_qs)

        rows_pages = []
        if not parts_list:
            rows_pages.append([None] * max_rows)
        else:
            for index in range(0, len(parts_list), max_rows):
                chunk = parts_list[index : index + max_rows]
                padded = chunk + [None] * max(0, max_rows - len(chunk))
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
                "vehicle_type": {
                    Vehicle.Category.CARGO: "Teretno vozilo",
                    Vehicle.Category.TRAILER: "Priključno vozilo",
                }.get(vehicle.category, "Putničko vozilo"),
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
        super().form_valid(form)
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
