import csv
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_filters.views import FilterView

from core.exporting import csv_attachment_response
from core.mixins import RolePermissionRequiredMixin

from .filters import PoliciesMonthlyCostsFilter
from .models import DraftPolicy, Policy
from .policy_forms import PolicyForm
from .queries import _filtered_qs, policies_monthly_costs_qs


class PolicyListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = "fleet/policy_list.html"
    context_object_name = "policies"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista polisa osiguranja"
        return context


class PolicyFixingListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = "fleet/draft_policy_list.html"
    context_object_name = "policies"

    def get_queryset(self):
        return DraftPolicy.objects.all()

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

        newest_policy = Policy.objects.filter(
            vehicle=OuterRef("vehicle"),
            insurance_type=OuterRef("insurance_type"),
        ).order_by("-end_date").values("end_date", "is_renewable")[:1]

        expiring_policies = Policy.objects.annotate(
            latest_end_date=Subquery(newest_policy.values("end_date")[:1]),
            latest_is_renewable=Subquery(newest_policy.values("is_renewable")[:1]),
        ).filter(
            end_date__gte=today,
            end_date__lte=thirty_days_from_now,
            end_date=F("latest_end_date"),
            latest_is_renewable=True,
        )

        newer_policy_exists = Policy.objects.filter(
            vehicle=OuterRef("vehicle"),
            insurance_type=OuterRef("insurance_type"),
            start_date__gt=OuterRef("start_date"),
        )

        expired_unrenewed_policies = Policy.objects.annotate(
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
        context["title"] = f"Detalji polise {self.object.policy_number}"
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


class DraftPolicyUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = DraftPolicy
    form_class = PolicyForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("policy_fixing_list")

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return str(self.success_url)

    def form_valid(self, form):
        draft = form.save(commit=False)
        required_fields = [
            "partner_pib",
            "partner_name",
            "invoice_id",
            "invoice_number",
            "issue_date",
            "insurance_type",
            "policy_number",
            "premium_amount",
            "start_date",
            "end_date",
            "first_installment_amount",
            "other_installments_amount",
            "number_of_installments",
        ]
        is_complete = all(
            getattr(draft, field) is not None and getattr(draft, field) != ""
            for field in required_fields
        )

        if is_complete:
            policy = Policy(
                vehicle=draft.vehicle,
                partner_pib=draft.partner_pib,
                partner_name=draft.partner_name,
                invoice_id=draft.invoice_id,
                invoice_number=draft.invoice_number,
                issue_date=draft.issue_date,
                insurance_type=draft.insurance_type,
                policy_number=draft.policy_number,
                premium_amount=draft.premium_amount,
                start_date=draft.start_date,
                end_date=draft.end_date,
                first_installment_amount=draft.first_installment_amount,
                other_installments_amount=draft.other_installments_amount,
                number_of_installments=draft.number_of_installments,
            )
            policy.save()
            draft.delete()
            return redirect(self.get_success_url())

        draft.save()
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dopuni polisu"
        context["submit_button_label"] = "Sacuvaj"
        return context


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
