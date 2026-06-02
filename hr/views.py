from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from core.mixins import RolePermissionRequiredMixin

from .forms import EmployeeCVItemForm, EmployeeForm, EmployeeNameCorrectionForm
from .models import Employee, EmployeeCVItem
from .querysets import employee_list_queryset


def _collect_user_activities(user):
    if not user:
        return []

    from nabavka.models import (
        ProcurementCase,
        ProcurementContractLink,
        ProcurementInvoiceContractLink,
        ProcurementInvoiceLink,
        ProcurementItemInvoiceLink,
        ProcurementStatusLog,
        PurchaseOrder,
    )
    from naplata.models import AvansKlijent, Postupak, PromenaPostupka
    from ugovori.models import BusinessRequest, Offer, Partner

    activities = []

    def append_items(queryset, category, description=None):
        for item in queryset:
            activities.append(
                {
                    "created_at": item.created_at,
                    "category": category,
                    "reference": str(item),
                    "description": description(item) if description else "",
                }
            )

    append_items(
        ProcurementCase.objects.filter(created_by=user),
        "Zahtev za nabavku i uslugu",
        lambda item: item.get_status_display(),
    )
    append_items(
        PurchaseOrder.objects.filter(created_by=user),
        "Narudzbenica",
        lambda item: item.get_status_display(),
    )
    append_items(
        ProcurementStatusLog.objects.filter(created_by=user).select_related("procurement_case"),
        "Promena statusa zahteva",
        lambda item: f"{item.get_old_status_display() or '-'} -> {item.get_new_status_display()}",
    )
    append_items(
        ProcurementInvoiceLink.objects.filter(created_by=user).select_related("procurement_case"),
        "Povezivanje fakture",
    )
    append_items(
        ProcurementItemInvoiceLink.objects.filter(created_by=user).select_related("invoice", "procurement_item"),
        "Povezivanje stavke fakture",
    )
    append_items(
        ProcurementContractLink.objects.filter(created_by=user).select_related("contract", "procurement_case"),
        "Povezivanje ugovora",
    )
    append_items(
        ProcurementInvoiceContractLink.objects.filter(created_by=user).select_related("invoice", "contract"),
        "Povezivanje fakture i ugovora",
    )
    append_items(Partner.objects.filter(created_by=user), "Partner")
    append_items(
        BusinessRequest.objects.filter(created_by=user),
        "Poslovni zahtev",
        lambda item: item.get_status_display(),
    )
    append_items(
        Offer.objects.filter(created_by=user),
        "Ponuda",
        lambda item: item.get_status_display(),
    )
    append_items(AvansKlijent.objects.filter(created_by=user), "Avans klijent")
    append_items(
        Postupak.objects.filter(created_by=user),
        "Pravni postupak",
        lambda item: item.get_tip_display(),
    )
    append_items(
        PromenaPostupka.objects.filter(created_by=user).select_related("postupak"),
        "Promena pravnog postupka",
    )

    return sorted(activities, key=lambda item: item["created_at"], reverse=True)


def _employee_detail_context(employee, *, is_self_profile=False):
    from fleet.models import Incident, PutniNalog, VehicleTravelOrder
    from ugovori.models import Contract

    travel_orders = (
        PutniNalog.objects.filter(employee=employee)
        .select_related("vehicle", "job_code")
        .order_by("-order_date", "-id")
    )
    vehicle_travel_orders = (
        VehicleTravelOrder.objects.filter(employee=employee)
        .select_related("vehicle")
        .order_by("-created_at", "-id")
    )
    incidents = (
        Incident.objects.filter(employee=employee)
        .select_related("vehicle")
        .order_by("-date", "-id")
    )
    cv_items = employee.cv_items.all()
    linked_user = getattr(employee, "user_account", None)

    contracts = (
        Contract.objects.filter(parties__partner__external_sif_par=employee.employee_code)
        .select_related("contract_type")
        .prefetch_related("parties__partner")
        .distinct()
        .order_by("-contract_date", "-id")
    )

    activities = _collect_user_activities(linked_user)
    return {
        "employee": employee,
        "title": str(employee),
        "is_self_profile": is_self_profile,
        "linked_user": linked_user,
        "cv_items": cv_items,
        "cv_items_count": cv_items.count(),
        "travel_orders": travel_orders,
        "travel_orders_count": travel_orders.count(),
        "vehicle_travel_orders": vehicle_travel_orders,
        "vehicle_travel_orders_count": vehicle_travel_orders.count(),
        "incidents": incidents,
        "incidents_count": incidents.count(),
        "contracts": contracts,
        "contracts_count": contracts.count(),
        "activities": activities,
        "activities_count": len(activities),
    }


class EmployeeListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = Employee
    template_name = "hr/employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        show_inactive = self.request.GET.get("inactive") == "1"
        return employee_list_queryset(show_inactive=show_inactive)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista zaposlenih"
        context["show_inactive"] = self.request.GET.get("inactive") == "1"
        return context


class EmployeeCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("employee_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiraj novog zaposlenog"
        context["submit_button_label"] = "Dodaj zaposlenog"
        return context


class EmployeeUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("employee_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni podatke zaposlenog"
        context["submit_button_label"] = "Sacuvaj izmene"
        return context


class EmployeeDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Employee
    template_name = "hr/employee_detail.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_employee_detail_context(self.object))
        return context


class MyEmployeeProfileView(LoginRequiredMixin, TemplateView):
    template_name = "hr/employee_detail.html"

    def get_template_names(self):
        if not self.request.user.employee_id:
            return ["hr/my_profile_unlinked.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.employee_id:
            context.update(
                _employee_detail_context(
                    self.request.user.employee,
                    is_self_profile=True,
                )
            )
        return context


class MyEmployeeNameCorrectionView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeNameCorrectionForm
    template_name = "hr/name_correction_form.html"

    def get_object(self, queryset=None):
        if not self.request.user.employee_id:
            raise PermissionDenied("Korisnicki nalog nije povezan sa zaposlenim.")
        return self.request.user.employee

    def get_success_url(self):
        return reverse("my_employee_profile")


class OwnEmployeeCVMixin(LoginRequiredMixin):
    def get_employee(self):
        if not self.request.user.employee_id:
            raise PermissionDenied("Korisnicki nalog nije povezan sa zaposlenim.")
        return self.request.user.employee

    def get_queryset(self):
        return EmployeeCVItem.objects.filter(employee=self.get_employee())

    def get_success_url(self):
        return f"{reverse('my_employee_profile')}#cv"


class EmployeeCVItemCreateView(OwnEmployeeCVMixin, CreateView):
    model = EmployeeCVItem
    form_class = EmployeeCVItemForm
    template_name = "hr/cv_item_form.html"

    def form_valid(self, form):
        form.instance.employee = self.get_employee()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dodaj CV stavku"
        return context


class EmployeeCVItemUpdateView(OwnEmployeeCVMixin, UpdateView):
    model = EmployeeCVItem
    form_class = EmployeeCVItemForm
    template_name = "hr/cv_item_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni CV stavku"
        return context


class EmployeeCVItemDeleteView(OwnEmployeeCVMixin, DeleteView):
    model = EmployeeCVItem
    template_name = "hr/cv_item_confirm_delete.html"


class EmployeeDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy("employee_list")
    template_name = "hr/employee_confirm_delete.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obrisi zaposlenog"
        return context
