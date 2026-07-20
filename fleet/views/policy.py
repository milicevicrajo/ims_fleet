import csv
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_filters.views import FilterView

from core.exporting import csv_attachment_response
from core.mixins import RolePermissionRequiredMixin

from ..filters import PoliciesMonthlyCostsFilter
from ..models import Policy, Vehicle
from ..forms.policy import PolicyForm
from ..support.policy_queries import _filtered_qs, policies_monthly_costs_qs


class PolicyListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = "fleet/policy_list.html"
    context_object_name = "policies"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista polisa osiguranja"
        context["vehicles"] = (
            Vehicle.objects.filter(policies__isnull=False)
            .distinct()
            .order_by("brand", "model", "inventory_number", "id")
        )
        context["insurance_types"] = (
            Policy.objects.exclude(insurance_type__isnull=True)
            .exclude(insurance_type="")
            .order_by("insurance_type")
            .values_list("insurance_type", flat=True)
            .distinct()
        )
        context["selected_vehicle"] = self.request.GET.get("vehicle", "")
        context["selected_partner"] = self.request.GET.get("partner", "")
        context["selected_insurance_type"] = self.request.GET.get("insurance_type", "")
        context["selected_completeness"] = self.request.GET.get("completeness", "")
        context["selected_renewable"] = self.request.GET.get("renewable", "")
        context["selected_end_from"] = self.request.GET.get("end_from", "")
        context["selected_end_to"] = self.request.GET.get("end_to", "")
        return context


class PolicyFixingListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = "fleet/policy_fixing_list.html"
    context_object_name = "policies"

    def get_queryset(self):
        return Policy.objects.select_related("vehicle").filter(Policy.incomplete_q()).order_by("-issue_date", "-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista polisa osiguranja koje morate dopuniti"
        return context


class ExpiringAndNotRenewedPolicyView(LoginRequiredMixin, ListView):
    template_name = "fleet/policy_expiring.html"
    model = Policy

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        thirty_days_from_now = today + timedelta(days=30)
        complete_policies = Policy.objects.exclude(Policy.incomplete_q())

        newest_policy = complete_policies.filter(
            vehicle=OuterRef("vehicle"),
            insurance_type=OuterRef("insurance_type"),
        ).order_by("-end_date").values("end_date", "is_renewable")[:1]

        expiring_policies = complete_policies.annotate(
            latest_end_date=Subquery(newest_policy.values("end_date")[:1]),
            latest_is_renewable=Subquery(newest_policy.values("is_renewable")[:1]),
        ).filter(
            end_date__gte=today,
            end_date__lte=thirty_days_from_now,
            end_date=F("latest_end_date"),
            latest_is_renewable=True,
        )

        newer_policy_exists = complete_policies.filter(
            vehicle=OuterRef("vehicle"),
            insurance_type=OuterRef("insurance_type"),
            start_date__gt=OuterRef("start_date"),
        )

        expired_unrenewed_policies = complete_policies.annotate(
            has_newer_policy=Subquery(newer_policy_exists.values("id")[:1]),
            latest_is_renewable=Subquery(newest_policy.values("is_renewable")[:1]),
        ).filter(
            end_date__lt=today,
            has_newer_policy__isnull=True,
            latest_is_renewable=True,
        )

        context["expiring_policies"] = expiring_policies
        context["expired_unrenewed_policies"] = expired_unrenewed_policies
        context["title"] = "Liste polisa koje isticu i koje su istekle i nisu obnovljene"
        return context


class PolicyCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Policy
    form_class = PolicyForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("policy_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiraj novu polisu osiguranja"
        context["submit_button_label"] = "Dodaj polisu"
        return context


class PolicyUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Policy
    form_class = PolicyForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("policy_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni polisu osiguranja"
        context["submit_button_label"] = "Sacuvaj izmene"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        next_url = self.request.GET.get("next")
        if next_url:
            return HttpResponseRedirect(next_url)
        return response


class PolicyDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Policy
    template_name = "fleet/policy_detail.html"
    context_object_name = "policy"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        policy = self.object
        context["title"] = f"Detalj polise {policy.policy_number or policy.invoice_number or policy.invoice_id}"
        missing_fields = []
        field_labels = {
            "vehicle": "Automobil",
            "partner_pib": "PIB partnera",
            "partner_name": "Naziv partnera",
            "invoice_number": "Broj fakture",
            "issue_date": "Datum izdavanja",
            "insurance_type": "Tip osiguranja",
            "policy_number": "Broj polise",
            "premium_amount": "Iznos premije",
            "start_date": "Datum pocetka",
            "end_date": "Datum zavrsetka",
            "first_installment_amount": "Iznos prve rate",
            "other_installments_amount": "Iznos ostalih rata",
            "number_of_installments": "Broj rata",
        }
        for field_name, label in field_labels.items():
            value = policy.vehicle_id if field_name == "vehicle" else getattr(policy, field_name)
            if value is None or value == "":
                missing_fields.append(label)
        context["missing_fields"] = missing_fields
        return context
        return context


class PolicyDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Policy
    success_url = reverse_lazy("policy_list")
    template_name = "fleet/policy_confirm_delete.html"
    context_object_name = "policy"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obrisi polisu osiguranja"
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)


class PoliciesMonthlyCostsView(LoginRequiredMixin, FilterView, ListView):
    template_name = "fleet/reports/policies_monthly_costs.html"
    context_object_name = "rows"
    filterset_class = PoliciesMonthlyCostsFilter

    def get_queryset(self):
        return policies_monthly_costs_qs(Policy.objects.all()).order_by(
            "year", "month", "center", "oj_id", "job_code", "vrsta"
        )


def policies_monthly_costs_csv(request):
    qs = _filtered_qs(request)
    response = csv_attachment_response("polise_mesecni_troskovi_sve_godine.csv", quoted=True)
    writer = csv.writer(response)
    writer.writerow(["god", "mesec", "centar", "oj_id", "oj_naziv", "sifra_posla", "vrsta", "iznos"])
    for row in qs:
        writer.writerow(
            [
                row["year"],
                row["month"],
                row["center"] or "",
                row["oj_id"] or "",
                row["oj_name"] or "",
                row.get("job_code") or "",
                row["vrsta"] or "",
                f"{(row['iznos'] or 0):.2f}",
            ]
        )
    return response
