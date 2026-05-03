from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin

from ..filters import FuelFilterForm, FuelTransactionFilterForm
from ..forms.fuel import FuelConsumptionForm
from ..models import FuelConsumption, TrafficCard
from ..utils import date_range_for_datetime_field, get_fuel_consumption_queryset


class FuelConsumptionListView(LoginRequiredMixin, FilterView):
    model = FuelConsumption
    filterset_class = FuelFilterForm
    template_name = "fleet/fuelconsumption_list.html"
    context_object_name = "fuel_consumptions"

    def get_queryset(self):
        latest_traffic_card_subquery = TrafficCard.objects.filter(
            vehicle=OuterRef("vehicle")
        ).order_by("-issue_date").values("registration_number")[:1]

        queryset = super().get_queryset().annotate(
            registration_number=Subquery(latest_traffic_card_subquery)
        )

        if not self.request.GET:
            today = timezone.now().date()
            forty_days_ago = today - timedelta(days=40)
            start_dt, end_dt = date_range_for_datetime_field(forty_days_ago, today)
            return queryset.filter(date__gte=start_dt, date__lte=end_dt)

        form = self.filterset_class(self.request.GET, queryset=queryset)
        if form.is_valid():
            return form.qs
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.filterset_class(self.request.GET, queryset=self.get_queryset())
        context.update(
            {
                "filter": form,
                "title": "Lista potrošnje goriva",
            }
        )
        return context


class FuelTransactionsListView(LoginRequiredMixin, ListView):
    template_name = "fleet/fuel_transactions_list.html"
    context_object_name = "fuel_transactions"

    def get_queryset(self):
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if not start_date:
            start_date = date.today() - timedelta(days=40)
        if not end_date:
            end_date = date.today()

        return get_fuel_consumption_queryset(start_date=start_date, end_date=end_date)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = FuelTransactionFilterForm(
            self.request.GET
            or {
                "start_date": (date.today() - timedelta(days=40)).strftime("%Y-%m-%d"),
                "end_date": date.today().strftime("%Y-%m-%d"),
            }
        )
        context["title"] = "Izveštaj o potrošnji goriva"
        return context


class FuelConsumptionCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = FuelConsumption
    form_class = FuelConsumptionForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("fuelconsumption_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dodaj potrošnju goriva"
        context["submit_button_label"] = "Dodaj"
        return context


class FuelConsumptionUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = FuelConsumption
    form_class = FuelConsumptionForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("fuelconsumption_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni potrošnju goriva"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context


class FuelConsumptionDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = FuelConsumption
    template_name = "fleet/fuelconsumption_detail.html"
    context_object_name = "fuel_consumption"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Detalji potrošnje goriva {self.object.date}"
        return context


class FuelConsumptionDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = FuelConsumption
    success_url = reverse_lazy("fuelconsumption_list")
    template_name = "fleet/fuelconsumption_confirm_delete.html"
    context_object_name = "fuel_consumption"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obriši potrošnju goriva"
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)
