from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.mixins import RolePermissionRequiredMixin

from ..forms import DraftInsuranceForm, InsuranceForm
from ..models import DraftInsurance, Insurance
from ..sync_services import fetch_ddor_insurance_data, migrate_draft_to_insurance_single


class InsuranceListView(LoginRequiredMixin, ListView):
    model = Insurance
    template_name = "fleet/insurance_list.html"
    context_object_name = "insurances"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Osiguranja"
        return ctx


class InsuranceDetailView(LoginRequiredMixin, ListView):
    """
    Prikaz svih stavki jednog naloga (br_naloga, god).
    """

    model = Insurance
    template_name = "fleet/insurance_detail.html"
    context_object_name = "stavke"

    def get_queryset(self):
        return (
            Insurance.objects.filter(
                br_naloga=self.kwargs["br_naloga"],
                god=self.kwargs["god"],
            ).order_by("stavka")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["br_naloga"] = self.kwargs["br_naloga"]
        ctx["god"] = self.kwargs["god"]
        ctx["title"] = f"Osiguranje {ctx['br_naloga']} ({ctx['god']})"
        return ctx


class InsuranceFixingListView(LoginRequiredMixin, ListView):
    """
    Draft zapisi kojima nedostaju kljucni podaci.
    """

    model = DraftInsurance
    template_name = "fleet/draft_insurance_list.html"
    context_object_name = "insurances"

    def get_queryset(self):
        return (
            DraftInsurance.objects.filter(~Q(kola=False)).order_by(
                "god",
                "br_naloga",
                "stavka",
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Potrayivanja od osiguranja koja je potrebno dodeliti automobilu"
        return ctx


class InsuranceCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Insurance
    form_class = InsuranceForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("insurance_list")
    success_message = "Osiguranje uspesno kreirano."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novo osiguranje"
        ctx["submit_button_label"] = "Sacuvaj"
        return ctx


class InsuranceUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Insurance
    form_class = InsuranceForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("insurance_list")
    success_message = "Osiguranje uspesno izmenjeno."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Izmena osiguranja"
        ctx["submit_button_label"] = "Sacuvaj izmene"
        return ctx


class InsuranceDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Insurance
    template_name = "fleet/insurance_confirm_delete.html"
    success_url = reverse_lazy("insurance_list")


def _migrate_one_draft_insurance(draft: DraftInsurance):
    """
    Jedan draft -> final Insurance (transactional).
    """

    if not draft.is_complete():
        return None

    with transaction.atomic():
        ins, created = Insurance.objects.get_or_create(
            god=draft.god,
            sif_vrs=draft.sif_vrs,
            br_naloga=draft.br_naloga,
            stavka=draft.stavka,
            knt=draft.knt,
            defaults={
                "vehicle": draft.vehicle,
                "oj": draft.oj,
                "datum": draft.datum,
                "vez_dok": draft.vez_dok,
                "potrazuje": draft.potrazuje,
                "kola": draft.kola,
            },
        )
        if not created:
            ins.vehicle = draft.vehicle
            ins.oj = draft.oj
            ins.datum = draft.datum
            ins.vez_dok = draft.vez_dok
            ins.potrazuje = draft.potrazuje
            ins.kola = draft.kola
            ins.save()

        draft.delete()
        return ins


def delete_complete_draft_insurances():
    return


class DraftInsuranceUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = DraftInsurance
    form_class = DraftInsuranceForm
    template_name = "fleet/generic_form_draft.html"
    success_message = "Osiguranje uspesno izmenjeno."
    success_url = reverse_lazy("insurance_fixing_list")

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
        current = form.save()

        all_drafts = DraftInsurance.objects.filter(
            br_naloga=current.br_naloga,
            god=current.god,
        ).order_by("stavka")

        migrated = 0
        for draft in list(all_drafts):
            ins = _migrate_one_draft_insurance(draft)
            if ins:
                migrated += 1

        delete_complete_draft_insurances()

        still_exists = DraftInsurance.objects.filter(
            br_naloga=current.br_naloga,
            god=current.god,
        ).exists()

        if still_exists:
            messages.info(
                self.request,
                f"Delimicno premesteno ({migrated}). Dovrsite preostale stavke.",
            )
            return redirect(self.get_success_url())

        messages.success(self.request, f"Premesteno u final ({migrated}).")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Izmena osiguranja {self.object.br_naloga}"
        ctx["submit_button_label"] = "Sacuvaj izmene"
        ctx["manual"] = (
            "Unesite vozilo, ako se potrazivanje ne odnosi na vozilo polje "
            "'Odnosi se na vozilo' postavite NE"
        )
        return ctx


@login_required
def insurance_fetch_ddor_view(request):
    msg = fetch_ddor_insurance_data()
    messages.info(request, msg)
    return redirect("insurance_fixing_list")


@login_required
def insurance_migrate_one_view(request, draft_id, vehicle_id):
    try:
        ins = migrate_draft_to_insurance_single(draft_id, vehicle_id)
        messages.success(request, f"Premesteno u final: {ins}")
        return redirect("insurance_detail", god=ins.god, br_naloga=ins.br_naloga)
    except Exception as exc:
        messages.error(request, f"Greska: {exc}")
        try:
            draft = DraftInsurance.objects.get(id=draft_id)
            return redirect("draft_insurance_update", pk=draft.id)
        except Exception:
            return redirect("insurance_fixing_list")


@login_required
def fetch_ddor_data_view(request):
    if request.method == "POST":
        result = fetch_ddor_insurance_data()
        messages.success(request, result)
        return redirect("insurance_fixing_list")
