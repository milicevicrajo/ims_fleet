from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.mixins import RolePermissionRequiredMixin
from core.models import OrganizationalUnit

from .filters import TrafficCardFilterForm
from .forms import JobCodeForm, OrganizationalUnitForm, TrafficCardForm, VehicleTenderDocumentForm
from .models import JobCode, KontaVozila, TrafficCard, Vehicle, VehicleTenderDocument


class OrganizationalUnitListView(LoginRequiredMixin, ListView):
    model = OrganizationalUnit
    template_name = "fleet/organizational_units_list.html"
    context_object_name = "units"


class OrganizationalUnitCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = OrganizationalUnit
    form_class = OrganizationalUnitForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("organizational_unit_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiraj novu organizacionu jedinicu"
        context["submit_button_label"] = "Sačuvaj"
        return context


class OrganizationalUnitUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = OrganizationalUnit
    form_class = OrganizationalUnitForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("organizational_unit_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni organizacionu jedinicu"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class VehicleTenderDocumentListView(LoginRequiredMixin, ListView):
    model = VehicleTenderDocument
    template_name = "fleet/vehicle_tender_document_list.html"
    context_object_name = "documents"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("vehicle")
        vehicle_id = self.request.GET.get("vehicle")
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if self.request.GET.get("only_active") == "1":
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Tender dokumenti vozila"
        context["vehicles"] = Vehicle.objects.all().order_by("brand", "model")
        context["selected_vehicle_id"] = self.request.GET.get("vehicle")
        context["only_active"] = self.request.GET.get("only_active") == "1"
        context["document_type_choices"] = VehicleTenderDocument.DocumentType.choices
        return context


class VehicleTenderDocumentCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = VehicleTenderDocument
    form_class = VehicleTenderDocumentForm
    template_name = "fleet/generic_form.html"

    def get_initial(self):
        initial = super().get_initial()
        vehicle_id = self.kwargs.get("vehicle_id") or self.request.GET.get("vehicle")
        if vehicle_id:
            initial["vehicle"] = Vehicle.objects.filter(pk=vehicle_id).first()
        return initial

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, "Dokument je uspešno dodat.")
        return redirect("vehicle_detail", pk=self.object.vehicle_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dodaj tender dokument"
        context["submit_button_label"] = "Sačuvaj dokument"
        return context


class VehicleTenderDocumentUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = VehicleTenderDocument
    form_class = VehicleTenderDocumentForm
    template_name = "fleet/generic_form.html"

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, "Dokument je uspešno izmenjen.")
        return redirect("vehicle_detail", pk=self.object.vehicle_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Izmeni tender dokument {self.object.title}"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class VehicleTenderDocumentDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = VehicleTenderDocument
    template_name = "fleet/vehicle_tender_document_detail.html"
    context_object_name = "document"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Tender dokument {self.object.title}"
        return context


class VehicleTenderDocumentDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = VehicleTenderDocument
    template_name = "fleet/vehicle_tender_document_confirm_delete.html"
    context_object_name = "document"
    success_url = reverse_lazy("vehicle_tender_document_list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        vehicle_id = self.object.vehicle_id
        messages.success(request, "Dokument je uspešno obrisan.")
        self.success_url = reverse("vehicle_detail", kwargs={"pk": vehicle_id})
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Obriši tender dokument {self.object.title}"
        return context


class TrafficCardListView(LoginRequiredMixin, ListView):
    model = TrafficCard
    template_name = "fleet/trafficcard_list.html"
    context_object_name = "traffic_cards"
    form_class = TrafficCardFilterForm

    def get_queryset(self):
        queryset = super().get_queryset().select_related("vehicle")
        self.filter_form = self.form_class(self.request.GET or None)

        latest_org_unit_subquery = JobCode.objects.filter(
            vehicle_id=OuterRef("vehicle_id")
        ).order_by("-assigned_date").values("organizational_unit__code")[:1]

        latest_center_subquery = JobCode.objects.filter(
            vehicle_id=OuterRef("vehicle_id")
        ).order_by("-assigned_date").values("organizational_unit__center")[:1]

        queryset = queryset.annotate(
            latest_org_unit=Subquery(latest_org_unit_subquery),
            latest_center=Subquery(latest_center_subquery),
        )

        if self.filter_form.is_valid():
            org_unit = self.filter_form.cleaned_data.get("organizational_unit")
            center = self.filter_form.cleaned_data.get("center")

            if org_unit:
                queryset = queryset.filter(latest_org_unit=org_unit.code)
            if center:
                queryset = queryset.filter(latest_center=center)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["title"] = "Lista saobraćajnih dozvola"
        return context


class TrafficCardCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = TrafficCard
    form_class = TrafficCardForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("trafficcard_list")

    def get_initial(self):
        return {"vehicle": self.kwargs.get("vehicle_id")}

    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect("jobcode_create", vehicle_id=self.object.vehicle.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiraj novu saobraćajnu dozvolu"
        context["submit_button_label"] = "Dodaj saobraćajnu dozvolu"
        return context


class TrafficCardUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = TrafficCard
    form_class = TrafficCardForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("trafficcard_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni podatke saobraćajne dozvole"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class TrafficCardDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = TrafficCard
    template_name = "fleet/trafficcard_detail.html"
    context_object_name = "traffic_card"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Detalji saobraćajne dozvole {self.object.registration_number}"
        return context


class TrafficCardDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = TrafficCard
    success_url = reverse_lazy("trafficcard_list")
    template_name = "fleet/trafficcard_confirm_delete.html"
    context_object_name = "traffic_card"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obriši saobraćajnu dozvolu"
        return context


class JobCodeListView(LoginRequiredMixin, ListView):
    model = JobCode
    template_name = "fleet/jobcode_list.html"
    context_object_name = "job_codes"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista šifara poslova"
        return context


class JobCodeCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = JobCode
    form_class = JobCodeForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("jobcode_list")

    def get_initial(self):
        return {"vehicle": self.kwargs.get("vehicle_id")}

    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect("vehicle_detail", pk=self.object.vehicle.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiraj novu šifru posla"
        context["submit_button_label"] = "Dodaj šifru posla"
        return context


class JobCodeUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = JobCode
    form_class = JobCodeForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("jobcode_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni šifru posla"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class JobCodeDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = JobCode
    template_name = "fleet/jobcode_detail.html"
    context_object_name = "job_code"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Detalji šifre posla {self.object.job_code}"
        return context


class JobCodeDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = JobCode
    success_url = reverse_lazy("jobcode_list")
    template_name = "fleet/jobcode_confirm_delete.html"
    context_object_name = "job_code"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obriši šifru posla"
        return context


class KontoListView(LoginRequiredMixin, ListView):
    model = KontaVozila
    template_name = "fleet/konta_list.html"
    context_object_name = "konta"
    paginate_by = 50
    ordering = ("knt",)


class KontoCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = KontaVozila
    fields = ["knt", "naz_knt"]
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("konta_list")
    success_message = "Konto %(knt)s je dodat."


class KontoUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = KontaVozila
    fields = ["naz_knt"]
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("konta_list")
    success_message = "Konto %(knt)s je izmenjen."


class KontoDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = KontaVozila
    template_name = "fleet/konta_confirm_delete.html"
    success_url = reverse_lazy("konta_list")
    success_message = "Konto je obrisan."
