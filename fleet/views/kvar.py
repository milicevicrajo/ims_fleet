"""Garaža: prijava kvara, dokumenti (prijava, trebovanje/zahtev za uslugu, radni nalog) i zahtev u Nabavci.

Detalj kvara odmah prikazuje sva tri dokumenta onako kako se štampaju; delovi se unose u tabelu
koja izgleda kao samo trebovanje. Dugme „Formiraj zahtev u Nabavci” pravi nacrt predmeta sa
vozilom, nalogom garaže, šifrom posla i delovima (`fleet/support/garaza.py: formiraj_zahtev`).
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin, user_has_role_permission

from ..filters import KvarFilter
from ..forms.garaza import KvarForm, KvarPartForm
from ..models import Kvar, KvarPart, Vehicle
from ..support.garaza import (NAJMANJI_DOZVOLJEN_SKOK_KM, NAJVISE_KM_DNEVNO, aktivni_zahtevi, ensure_auto_parts,
                              formiraj_zahtev, poslednja_kilometraza, sifra_posla_vozila)
from fleet.support import obuhvat as obuhvat_flote

MAX_REDOVA_TREBOVANJA = 12
MIN_REDOVA_NALOGA = 6
KvarPartFormSet = modelformset_factory(KvarPart, form=KvarPartForm, extra=3, can_delete=True)


def _vidljivi_kvarovi(user):
    return obuhvat_flote.po_vozilu(Kvar.objects.select_related("vehicle"), user)


def _dodela_vozila(vehicle):
    """Šifra posla vozila (ista kao na zahtevu u Nabavci)."""
    return sifra_posla_vozila(vehicle)


def _redovi_po_listama(delovi):
    if not delovi:
        return [[None] * MAX_REDOVA_TREBOVANJA]
    liste = []
    for i in range(0, len(delovi), MAX_REDOVA_TREBOVANJA):
        deo = list(delovi[i:i + MAX_REDOVA_TREBOVANJA])
        liste.append(deo + [None] * (MAX_REDOVA_TREBOVANJA - len(deo)))
    return liste


def kontekst_dokumenta(kvar, request):
    """Zajednički podaci za prijavu kvara, trebovanje/zahtev za uslugu i radni nalog."""
    vehicle = kvar.vehicle
    traffic_card = vehicle.traffic_cards.order_by("-issue_date", "-id").first()
    dodela = _dodela_vozila(vehicle)
    jedinica = getattr(dodela, "organizational_unit", None)
    delovi = ensure_auto_parts(kvar) if not kvar.van_ims else list(kvar.parts.all())
    return {
        "kvar": kvar,
        "vehicle": vehicle,
        "registration_number": getattr(traffic_card, "registration_number", ""),
        "organizational_unit": jedinica,
        "center": (getattr(jedinica, "center", "") or "") if jedinica else "",
        "parts": delovi,
        "auto_parts": [],
        # Lista trebovanja ima 12 redova; svaka lista je jedan A4 sa dve iste kopije.
        "rows_pages": _redovi_po_listama(delovi),
        "prazni_redovi_naloga": range(max(0, MIN_REDOVA_NALOGA - len(delovi))),
        "is_van_ims": kvar.van_ims,
        "vehicle_type": {Vehicle.Category.CARGO: "Teretno vozilo", Vehicle.Category.TRAILER: "Priključno vozilo"}
                        .get(vehicle.category, "Putničko vozilo"),
        # Ugrađen prikaz na detalju kvara: bez trake za štampu i povratka.
        "embed": request.GET.get("embed") == "1",
        "auto_print": request.GET.get("auto") == "1",
        "next_url": request.GET.get("next") or reverse("kvar_detail", kwargs={"pk": kvar.pk}),
    }


@obuhvat_flote.ogranici_po_vozilu()
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
            _vidljivi_kvarovi(self.request.user)
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
            _vidljivi_kvarovi(self.request.user)
            .prefetch_related("vehicle__traffic_cards")
            .filter(van_ims=True)
            .order_by("-created_at")
        )
        return ctx


# Dokumenti se prikazuju i ugrađeni u detalj kvara (iframe iste aplikacije).
@method_decorator(xframe_options_sameorigin, name="dispatch")
class _KvarDokumentView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kvar = get_object_or_404(_vidljivi_kvarovi(self.request.user), pk=kwargs.get("pk"))
        ctx.update(kontekst_dokumenta(kvar, self.request))
        return ctx


class KvarPrintView(_KvarDokumentView):
    template_name = "fleet/kvar_print.html"


class KvarWorkOrderView(_KvarDokumentView):
    template_name = "fleet/kvar_workorder.html"


class KvarTrebovanjeView(_KvarDokumentView):
    template_name = "fleet/kvar_trebovanje.html"


class KvarStampaSveView(_KvarDokumentView):
    """Prijava kvara, trebovanje / zahtev za uslugu i radni nalog u jednoj štampi (svaki list A4)."""
    template_name = "fleet/kvar_stampa_sve.html"


class KvarDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/kvar_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.kvar = get_object_or_404(_vidljivi_kvarovi(request.user), pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Delovi se čuvaju svi odjednom, iz tabele koja izgleda kao trebovanje."""
        formset = KvarPartFormSet(request.POST, queryset=self.kvar.parts.order_by("pk"), prefix="delovi")
        if not formset.is_valid():
            messages.error(request, "Proverite unete stavke — naziv i količina su obavezni.")
            return self.render_to_response(self.get_context_data(formset=formset), status=400)
        for form in formset.forms:
            if not form.has_changed() and not form.instance.pk:
                continue
            if form in formset.deleted_forms:
                if form.instance.pk:
                    form.instance.delete()
                continue
            deo = form.save(commit=False)
            deo.kvar = self.kvar
            deo.save()
        messages.success(request, "Stavke su sačuvane.")
        return redirect(f"{reverse('kvar_detail', kwargs={'pk': self.kvar.pk})}#trebovanje")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(kontekst_dokumenta(self.kvar, self.request))
        zahtevi = list(aktivni_zahtevi(self.kvar))
        ctx.update(
            title=f"Kvar {self.kvar.rbz}",
            formset=kwargs.get("formset") or KvarPartFormSet(queryset=self.kvar.parts.order_by("pk"), prefix="delovi"),
            zahtev=zahtevi[0] if zahtevi else None,
            zahtev_menja_nabavka=bool(zahtevi) and zahtevi[0].status != "draft",
            can_create_request=user_has_role_permission(self.request.user, "kvar_zahtev"),
            can_view_request=user_has_role_permission(self.request.user, "nabavka:case_detail"),
            can_update=user_has_role_permission(self.request.user, "kvar_update"),
            can_print_all=user_has_role_permission(self.request.user, "kvar_stampa_sve"),
        )
        return ctx


class KvarZahtevView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    """Nacrt zahteva u Nabavci iz prijave kvara (POST). Postojeći aktivni zahtev se ne pravi ponovo."""

    def post(self, request, pk):
        kvar = get_object_or_404(_vidljivi_kvarovi(request.user), pk=pk)
        try:
            predmet, nov = formiraj_zahtev(kvar, request.user)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            if nov:
                messages.success(request, f"Zahtev {predmet.case_number} je formiran u Nabavci kao nacrt i čeka potvrdu Nabavke.")
            else:
                messages.info(request, f"Zahtev {predmet.case_number} je već formiran.")
        return redirect("kvar_detail", pk=kvar.pk)


class KvarKilometrazaView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    """JSON za formu prijave: poslednja poznata kilometraža, tablica i šifra posla vozila."""

    def get(self, request):
        vozilo_id = request.GET.get("vozilo", "")
        if not vozilo_id.isdigit():
            return JsonResponse({})
        vozilo = obuhvat_flote.po_vozilu(Vehicle.objects.filter(pk=int(vozilo_id)), request.user, "pk").first()
        if vozilo is None:
            return JsonResponse({})
        kvar_id = request.GET.get("kvar", "")
        iskljuci = Kvar.objects.filter(pk=int(kvar_id)).first() if kvar_id.isdigit() else None
        poslednja = poslednja_kilometraza(vozilo, iskljuci_kvar=iskljuci)
        tablica = vozilo.traffic_cards.order_by("-issue_date", "-id").values_list("registration_number", flat=True).first()
        dodela = _dodela_vozila(vozilo)
        return JsonResponse({
            "tablica": tablica or "",
            "sifra_posla": (f"{dodela.organizational_unit.code} · {dodela.organizational_unit.name}" if dodela else ""),
            "kilometraza": poslednja and {"km": poslednja["value"], "datum": poslednja["date"].strftime("%d.%m.%Y."),
                                          "datum_iso": poslednja["date"].isoformat(), "izvor": poslednja["source"]},
            "pravilo": {"km_dnevno": NAJVISE_KM_DNEVNO, "najmanji_skok": NAJMANJI_DOZVOLJEN_SKOK_KM},
        })


class _KvarFormMixin:
    model = Kvar
    form_class = KvarForm
    template_name = "fleet/kvar_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kilometraza_url"] = reverse("kvar_kilometraza")
        return ctx

    def get_success_url(self):
        return reverse("kvar_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        self.object = form.save()
        if form.upozorenja_kilometraze:
            messages.warning(self.request, "Sačuvano uz potvrđenu kilometražu: " + " ".join(form.upozorenja_kilometraze))
        return redirect("kvar_detail", pk=self.object.pk)


@obuhvat_flote.ogranici_po_vozilu()
class KvarCreateView(_KvarFormMixin, RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    def get_initial(self):
        initial = super().get_initial()
        vozilo = self.request.GET.get("vozilo") or self.request.GET.get("vehicle")
        if vozilo and vozilo.isdigit():
            initial["vehicle"] = vozilo
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["vehicle"].queryset = obuhvat_flote.po_vozilu(Vehicle.objects.all(), self.request.user, "pk")
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title="Prijava kvara", submit_button_label="Sačuvaj prijavu", cancel_url=reverse("kvar_list"))
        return ctx


@obuhvat_flote.ogranici_po_vozilu()
class KvarUpdateView(_KvarFormMixin, RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title=f"Izmena prijave kvara {self.object.rbz}", submit_button_label="Sačuvaj izmene",
                   cancel_url=reverse("kvar_detail", kwargs={"pk": self.object.pk}))
        return ctx


class KvarDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    success_url = reverse_lazy("kvar_list")

    def post(self, request, *args, **kwargs):
        kvar = get_object_or_404(obuhvat_flote.po_vozilu(Kvar.objects.all(), request.user), pk=kwargs.get("pk"))
        kvar.delete()
        messages.success(request, "Kvar je obrisan.")
        return redirect(self.success_url)
