"""Flota → Incidenti: saobraćajni prekršaji i kazne po vozilu i vozaču (od 29.09.2026.).

Spisak je DataTable sa servera (`incident_data`), detalj prikazuje incident, prilog (zapisnik,
rešenje, fotografija) i ko je imao vozilo tog dana. Vidljivost prati obuhvat Flote po vozilu.
Incidente unosi Garaža. Forma predlaže vozača iz zaduženja vozila i putnih naloga za dan
prekršaja (`fleet/support/incidenti.py`).
"""
import datetime
import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView

from core.form_fields import LOCAL_DATE_INPUT_FORMATS
from core.mixins import RolePermissionRequiredMixin, user_has_role_permission

from ..forms.incidenti import IncidentForm
from ..models import Incident, Vehicle
from ..support import obuhvat as obuhvat_flote
from ..support.vehicle_links import vozilo_link
from ..support.incidenti import vozaci_na_dan

SLIKE = {".jpg", ".jpeg", ".png"}


def _datum(tekst):
    for oblik in LOCAL_DATE_INPUT_FORMATS:
        try:
            return datetime.datetime.strptime(tekst.strip(), oblik).date()
        except (ValueError, AttributeError):
            continue
    return None


def _vidljivi(user):
    return obuhvat_flote.po_vozilu(Incident.objects.select_related("vehicle", "employee", "uneo"), user)


def _iznos(vrednost):
    return f"{vrednost or 0:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def _tablica(vozilo):
    kartica = next(iter(sorted(vozilo.traffic_cards.all(), key=lambda t: (t.issue_date, t.pk), reverse=True)), None)
    return kartica.registration_number if kartica else ""


def _filtriraj(request, qs):
    g = request.GET
    od, do = _datum(g.get("od", "")), _datum(g.get("do", ""))
    if od:
        qs = qs.filter(date__gte=od)
    if do:
        qs = qs.filter(date__lte=do)
    if (g.get("vozilo") or "").isdigit():
        qs = qs.filter(vehicle_id=int(g["vozilo"]))
    if g.get("prilog") == "da":
        qs = qs.exclude(prilog="")
    elif g.get("prilog") == "ne":
        qs = qs.filter(prilog="")
    pojam = (g.get("search[value]") or g.get("q") or "").strip()
    if pojam:
        qs = qs.filter(Q(violation__icontains=pojam) | Q(location__icontains=pojam) | Q(note__icontains=pojam)
                       | Q(employee__first_name__icontains=pojam) | Q(employee__last_name__icontains=pojam)
                       | Q(vehicle__brand__icontains=pojam) | Q(vehicle__model__icontains=pojam)
                       | Q(vehicle__traffic_cards__registration_number__icontains=pojam.replace(" ", "").upper())).distinct()
    return qs


def _obrisi_stari_prilog(stari, novi):
    if stari and stari.name and stari.name != (novi.name if novi else ""):
        storage, ime = stari.storage, stari.name
        transaction.on_commit(lambda: storage.delete(ime) if storage.exists(ime) else None)


class IncidentListView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = "fleet/incident_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        ctx.update(
            title="Incidenti",
            filteri={"od": g.get("od", ""), "do": g.get("do", ""), "vozilo": g.get("vozilo", ""), "prilog": g.get("prilog", "")},
            vozila=obuhvat_flote.po_vozilu(Vehicle.objects.order_by("brand", "model"), self.request.user, "pk"),
            can_create=user_has_role_permission(self.request.user, "incident_create"),
        )
        return ctx


class IncidentDataView(LoginRequiredMixin, RolePermissionRequiredMixin, View):
    KOLONE = {"0": "date", "1": "vehicle__brand", "2": "employee__last_name", "3": "violation", "4": "location",
              "5": "fine_amount", "6": "prilog"}

    def get(self, request):
        sve = _vidljivi(request.user)
        qs = _filtriraj(request, sve)
        polje = self.KOLONE.get(request.GET.get("order[0][column]", "0"), "date")
        smer = "-" if request.GET.get("order[0][dir]", "desc") == "desc" else ""
        try:
            start = max(int(request.GET.get("start", 0)), 0)
            duzina = min(max(int(request.GET.get("length", 50)), 1), 200)
            draw = int(request.GET.get("draw", 0))
        except (TypeError, ValueError):
            start, duzina, draw = 0, 50, 0
        # Zbir preko jedinstvenih incidenata (pretraga po tablici spaja saobracajne dozvole).
        zbir = Incident.objects.filter(pk__in=qs.values("pk")).aggregate(broj=Count("pk"), iznos=Sum("fine_amount"))
        moze_izmenu = user_has_role_permission(request.user, "incident_update")
        moze_prilog = user_has_role_permission(request.user, "incident_prilog")
        redovi = []
        for i in qs.prefetch_related("vehicle__traffic_cards").order_by(f"{smer}{polje}", "-pk")[start:start + duzina]:
            detalj = reverse("incident_detail", kwargs={"pk": i.pk})
            prilog = '<span class="text-muted">—</span>'
            if i.prilog:
                prilog = (f'<a class="btn btn-outline-secondary btn-sm" href="{reverse("incident_prilog", kwargs={"pk": i.pk})}" '
                          f'target="_blank" rel="noopener" title="{escape(i.prilog_naziv)}"><i class="mdi mdi-paperclip"></i></a>'
                          if moze_prilog else '<i class="mdi mdi-paperclip" title="Prilog postoji"></i>')
            akcije = f'<a class="btn btn-outline-primary btn-sm" href="{detalj}" title="Detalj"><i class="mdi mdi-eye"></i></a>'
            if moze_izmenu:
                akcije += (f' <a class="btn btn-outline-secondary btn-sm" href="{reverse("incident_update", kwargs={"pk": i.pk})}" '
                           f'title="Izmeni"><i class="mdi mdi-pencil"></i></a>')
            redovi.append({
                "datum": f'<span class="text-nowrap">{i.date:%d.%m.%Y.}</span>',
                "vozilo": (f'<strong>{vozilo_link(i.vehicle, _tablica(i.vehicle) or i.vehicle.chassis_number)}</strong>'
                           f'<div class="incident-small">{escape(i.vehicle.brand)} {escape(i.vehicle.model)}</div>'),
                "vozac": f'{escape(str(i.employee))}<div class="incident-small">{i.employee.employee_code}</div>',
                "prekrsaj": f'<a href="{detalj}">{escape(i.violation[:140])}{"…" if len(i.violation) > 140 else ""}</a>',
                "mesto": escape(i.location),
                "kazna": _iznos(i.fine_amount),
                "prilog": prilog,
                "akcije": akcije,
            })
        return JsonResponse({"draw": draw, "recordsTotal": sve.count(), "recordsFiltered": zbir["broj"], "data": redovi,
                             "zbir": {"broj": zbir["broj"], "iznos": _iznos(zbir["iznos"])}})


@obuhvat_flote.ogranici_po_vozilu()
class IncidentDetailView(LoginRequiredMixin, RolePermissionRequiredMixin, DetailView):
    model = Incident
    template_name = "fleet/incident_detail.html"
    context_object_name = "incident"

    def get_queryset(self):
        return super().get_queryset().select_related("vehicle", "employee", "uneo")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        i = self.object
        nastavak = os.path.splitext(i.prilog.name)[1].lower() if i.prilog else ""
        ostali = _vidljivi(self.request.user).exclude(pk=i.pk)
        ctx.update(
            title=f"Incident od {i.date:%d.%m.%Y.}",
            tablica=_tablica(i.vehicle),
            prilog_vrsta="pdf" if nastavak == ".pdf" else ("slika" if nastavak in SLIKE else ("fajl" if i.prilog else "")),
            vozaci=vozaci_na_dan(i.vehicle_id, i.date),
            incidenti_vozila=ostali.filter(vehicle=i.vehicle).order_by("-date")[:10],
            incidenti_vozaca=ostali.filter(employee=i.employee).order_by("-date")[:10],
            can_update=user_has_role_permission(self.request.user, "incident_update"),
            can_delete=user_has_role_permission(self.request.user, "incident_delete"),
            can_prilog=user_has_role_permission(self.request.user, "incident_prilog"),
        )
        return ctx


@method_decorator(xframe_options_sameorigin, name="dispatch")
class IncidentPrilogView(LoginRequiredMixin, RolePermissionRequiredMixin, View):
    """Prilog incidenta — samo za korisnika koji vidi vozilo (prikazuje se i u detalju)."""

    def get(self, request, pk):
        incident = get_object_or_404(_vidljivi(request.user), pk=pk)
        if not incident.prilog:
            raise Http404("Incident nema prilog.")
        try:
            fajl = incident.prilog.open("rb")
        except FileNotFoundError:
            raise Http404("Fajl priloga nije pronađen.")
        naziv = incident.prilog_naziv or os.path.basename(incident.prilog.name)
        return FileResponse(fajl, filename=naziv, as_attachment=request.GET.get("preuzmi") == "1")


class _IncidentFormMixin:
    model = Incident
    form_class = IncidentForm
    template_name = "fleet/incident_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        # Posle cuvanja nazad na spisak (detalj se otvara iz spiska).
        return reverse("incident_list")

    def form_valid(self, form):
        stari = None
        if form.instance.pk:
            stari = Incident.objects.get(pk=form.instance.pk).prilog
        incident = form.save(commit=False)
        if "prilog" in self.request.FILES:
            incident.prilog_naziv = self.request.FILES["prilog"].name[:255]
        elif not incident.prilog:
            incident.prilog_naziv = ""
        if not incident.pk:
            incident.uneo, incident.uneto = self.request.user, timezone.now()
        incident.save()
        _obrisi_stari_prilog(stari, incident.prilog)
        self.object = incident
        messages.success(self.request, self.poruka)
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(cancel_url=reverse("incident_list"), vozaci_url=reverse("incident_vozaci"),
                   form_help="Unesite tablicu i datum sa zapisnika — aplikacija predlaže ko je tada vozio.")
        return ctx


class IncidentCreateView(_IncidentFormMixin, LoginRequiredMixin, RolePermissionRequiredMixin, CreateView):
    poruka = "Incident je upisan."

    def get_initial(self):
        initial = super().get_initial()
        vozilo = self.request.GET.get("vozilo")
        if vozilo and vozilo.isdigit():
            initial["vehicle"] = vozilo
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title="Novi incident", submit_button_label="Sačuvaj incident")
        return ctx


@obuhvat_flote.ogranici_po_vozilu()
class IncidentUpdateView(_IncidentFormMixin, LoginRequiredMixin, RolePermissionRequiredMixin, UpdateView):
    poruka = "Incident je izmenjen."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title=f"Izmena incidenta od {self.object.date:%d.%m.%Y.}", submit_button_label="Sačuvaj izmene")
        return ctx


@obuhvat_flote.ogranici_po_vozilu()
class IncidentDeleteView(LoginRequiredMixin, RolePermissionRequiredMixin, DeleteView):
    model = Incident
    template_name = "fleet/incident_confirm_delete.html"
    context_object_name = "incident"
    success_url = reverse_lazy("incident_list")

    def form_valid(self, form):
        prilog = self.object.prilog
        response = super().form_valid(form)
        _obrisi_stari_prilog(prilog, None)
        messages.success(self.request, "Incident je obrisan.")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Brisanje incidenta"
        return ctx


class IncidentVozaciView(LoginRequiredMixin, RolePermissionRequiredMixin, View):
    """JSON: ko je imao vozilo na dan prekrsaja (zaduzenje vozila, putni nalog)."""

    def get(self, request):
        vozilo, dan = request.GET.get("vozilo", ""), _datum(request.GET.get("datum", ""))
        if not vozilo.isdigit() or dan is None:
            return JsonResponse({"vozaci": []})
        if not obuhvat_flote.po_vozilu(Vehicle.objects.filter(pk=int(vozilo)), request.user, "pk").exists():
            return JsonResponse({"vozaci": []})
        return JsonResponse({"vozaci": vozaci_na_dan(int(vozilo), dan)})
