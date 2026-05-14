from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.db.models import Q

from core.mixins import RolePermissionRequiredMixin

from .forms import EmployeeForm
from .models import Employee
from .querysets import employee_list_queryset


class EmployeeListView(LoginRequiredMixin, ListView):
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
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class EmployeeDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Employee
    template_name = "hr/employee_detail.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Detalji zaposlenog {self.object.last_name} {self.object.first_name}"
        
        # Dodaj putne naloge
        from fleet.models import PutniNalog
        travel_orders = PutniNalog.objects.filter(employee=self.object).order_by('-order_date')
        context["travel_orders"] = travel_orders
        context["travel_orders_count"] = travel_orders.count()
        
        # Dodaj ugovore preko šifre stranke iz job_code-a putnih naloga
        from ugovori.models import Contract
        
        # Pronađi sve šifre Job Code-ova iz putnih naloga
        job_codes = travel_orders.values_list('job_code__code', flat=True).distinct()
        
        # Pronađi sve ugovore čiji partneri imaju external_sif_par koji se pojavljuje u job_codes
        contracts = Contract.objects.filter(
            parties__partner__external_sif_par__in=job_codes
        ).distinct().order_by('-contract_date')
        
        context["contracts"] = contracts
        context["contracts_count"] = contracts.count()
        
        return context


class EmployeeDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy("employee_list")
    template_name = "hr/employee_confirm_delete.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obriši zaposlenog"
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)
