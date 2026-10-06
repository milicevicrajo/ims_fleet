from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.exporting import rows_to_xlsx_response
from core.mixins import RolePermissionRequiredMixin, user_has_role_permission

from ..forms.lease import LeaseForm, LeaseInterestForm
from ..models import Lease
from ..support.lease_queries import lease_monthly_costs_rows
from fleet.support import obuhvat as obuhvat_flote

LONG_TERM_LEASE_TYPES = set(Lease.LONG_TERM_LEASE_TYPE_VALUES)


@obuhvat_flote.ogranici_po_vozilu()
class LeaseListView(LoginRequiredMixin, ListView):
    model = Lease
    template_name = "fleet/lease_list.html"
    context_object_name = "leases"

    @staticmethod
    def _is_truthy(value):
        return str(value).lower() in {"1", "true", "yes", "on", "da"}

    def _show_expired(self):
        return self._is_truthy(self.request.GET.get("prikazi_istekle"))

    def _build_url(self, url_name, tip=None, show_expired=None):
        params = {}
        if tip:
            params["tip"] = tip
        if show_expired is None:
            show_expired = self._show_expired()
        if show_expired:
            params["prikazi_istekle"] = "1"

        url = reverse(url_name)
        if params:
            return f"{url}?{urlencode(params)}"
        return url

    def get_queryset(self):
        qs = super().get_queryset().select_related("vehicle")
        tip = self.request.GET.get("tip")
        if tip == "dugorocni":
            qs = qs.filter(lease_type__in=LONG_TERM_LEASE_TYPES)
        elif tip in {"finansijski", "operativni"}:
            qs = qs.filter(lease_type=tip)

        if not self._show_expired():
            qs = qs.filter(end_date__gte=timezone.localdate())
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Lizing i najam ugovori"
        active_tip = self.request.GET.get("tip")
        show_expired = self._show_expired()
        ctx["active_tip"] = active_tip
        ctx["show_expired"] = show_expired
        ctx["export_url"] = self._build_url("export_leases")
        ctx["lease_filter_links"] = {
            "all": self._build_url("lease_list"),
            "finansijski": self._build_url("lease_list", "finansijski"),
            "operativni": self._build_url("lease_list", "operativni"),
            "dugorocni": self._build_url("lease_list", "dugorocni"),
        }
        ctx["only_active_url"] = self._build_url("lease_list", tip=active_tip, show_expired=False)
        ctx["show_expired_url"] = self._build_url("lease_list", tip=active_tip, show_expired=True)
        return ctx


@obuhvat_flote.ogranici_po_vozilu()
class LeaseCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Lease
    form_class = LeaseForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("lease_list")

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('vehicle'):
            initial['vehicle'] = self.request.GET['vehicle']
        return initial

    def get_success_url(self):
        return reverse('vehicle_detail', kwargs={'pk': self.object.vehicle_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Kreiraj novi zakup"
        context["submit_button_label"] = "Dodaj zakup"
        return context


def export_leases_to_excel(request):
    tip = request.GET.get("tip")
    show_expired = LeaseListView._is_truthy(request.GET.get("prikazi_istekle"))
    leases = Lease.objects.select_related("vehicle").all()
    if tip == "dugorocni":
        leases = leases.filter(lease_type__in=LONG_TERM_LEASE_TYPES)
    elif tip in {"finansijski", "operativni"}:
        leases = leases.filter(lease_type=tip)

    if not show_expired:
        leases = leases.filter(end_date__gte=timezone.localdate())

    headers = [
        "Vozilo (sasija)",
        "Šifra partnera",
        "Naziv partnera",
        "Šifra posla",
        "Broj ugovora",
        "Mesečni iznos RSD",
        "Ukupno za ugovor RSD",
        "Značenje unetog iznosa",
        "Uneti iznos RSD",
        "Vrsta lizinga",
        "Datum početka",
        "Datum završetka",
        "Napomena",
    ]
    rows = [
        [
            lease.vehicle.chassis_number if lease.vehicle else "",
            lease.partner_code,
            lease.partner_name,
            lease.job_code,
            lease.contract_number,
            float(lease.monthly_amount) if lease.monthly_amount is not None else "",
            float(lease.total_amount) if lease.total_amount is not None else "",
            lease.get_payment_basis_display(),
            float(lease.current_payment_amount or 0),
            lease.lease_type_label,
            lease.start_date.strftime("%d.%m.%Y") if lease.start_date else "",
            lease.end_date.strftime("%d.%m.%Y") if lease.end_date else "",
            lease.note or "",
        ]
        for lease in leases
    ]

    fname = f"lizing_ugovori_{tip or 'svi'}.xlsx"
    return rows_to_xlsx_response(fname, "Lizing ugovori", headers, rows, quoted=True)


@obuhvat_flote.ogranici_po_vozilu()
class LeaseUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Lease
    form_class = LeaseForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("lease_list")

    def zavrsava(self):
        """„Završi ugovor” sa kartice vozila: ista izmena, uz uputstvo i povratak na vozilo."""
        return self.request.GET.get("zavrsi") == "1"

    def get_success_url(self):
        if self.zavrsava():
            return reverse('vehicle_detail', kwargs={'pk': self.object.vehicle_id}) + '#holding-pane'
        return super().get_success_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni zakup"
        context["submit_button_label"] = "Sacuvaj izmene"
        if self.zavrsava():
            context.update(
                title=f"Završi ugovor {self.object.contract_number}", submit_button_label="Završi ugovor",
                cancel_url=reverse('vehicle_detail', kwargs={'pk': self.object.vehicle_id}),
                form_help=("U „Datum završetka” unesite poslednji dan ugovora — dan otkupa ili vraćanja vozila. "
                           "Od narednog dana vozilo ne nosi naknadu ugovora i vodi se kao vlasništvo IMS. "
                           "Kod otkupa na kartici vozila dopunite nabavnu vrednost i finansiranje (Izmeni podatke); "
                           "vraćeno vozilo otpišite (Izveštaji → Otpis), da se ne vodi kao vlasništvo."))
        return context


@obuhvat_flote.ogranici_po_vozilu()
class LeaseInterestUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """Kamate finansijskog lizinga po godinama ugovora (dozvola izvedena iz `lease_update`)."""
    model = Lease
    form_class = LeaseInterestForm
    template_name = "fleet/generic_form.html"

    def get_queryset(self):
        return super().get_queryset().filter(lease_type='finansijski')

    def get_success_url(self):
        return reverse('lease_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            title=f"Kamate · {self.object.contract_number}", submit_button_label="Sačuvaj kamate",
            cancel_url=reverse('lease_detail', kwargs={'pk': self.object.pk}),
            form_help=("Za svaku godinu upišite stvarnu kamatu iz otplatnog plana u dinarima — samo kamatu, bez glavnice, "
                       "PDV-a i troškova obrade. Za prvu i poslednju (delimičnu) godinu upisuje se kamata za taj deo godine; "
                       "obračun je raspoređuje na dane kada ugovor važi. Prazno polje briše upis."))
        return context


@obuhvat_flote.ogranici_po_vozilu()
class LeaseDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Lease
    template_name = "fleet/lease_detail.html"
    context_object_name = "lease"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Detalji zakupa {self.object.partner_name}"
        if self.object.lease_type == 'finansijski':
            from ..support.lease_costs import lease_days_in_year

            upisane = {r.year: r.interest_amount for r in self.object.lease_interests.all()}
            context["kamate"] = [
                {"godina": godina, "iznos": upisane.get(godina), "dana": lease_days_in_year(self.object, godina)}
                for godina in range(self.object.start_date.year, self.object.end_date.year + 1)]
            context["can_edit_interest"] = user_has_role_permission(self.request.user, 'lease_interest_update')
        return context


@obuhvat_flote.ogranici_po_vozilu()
class LeaseDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Lease
    success_url = reverse_lazy("lease_list")
    template_name = "fleet/lease_confirm_delete.html"
    context_object_name = "lease"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obrisi zakup"
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)


class LeaseMonthlyCostsView(LoginRequiredMixin, ListView):
    template_name = "fleet/reports/lease_monthly_costs.html"
    context_object_name = "rows"
    paginate_by = 200

    def get_queryset(self):
        return lease_monthly_costs_rows(self.request)
