from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.utils.html import escape
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.mixins import RolePermissionRequiredMixin

from .forms import MenicaCreateForm, MenicaUpdateForm, UlaznaMenicaForm
from .models import Menica, UlaznaMenica
from .services import sync_izlazne_menice


TIP_TITLES = {
    Menica.TIP_IZLAZNA: "Izlazne menice",
    Menica.TIP_ULAZNA: "Ulazne menice",
}


def _parse_filter_date(value):
    parsed = parse_date(value or "")
    if parsed:
        return parsed
    try:
        return datetime.strptime(value or "", "%d.%m.%Y").date()
    except ValueError:
        return None


def _hover_text(value, max_length=50):
    text = str(value or "")
    visible = f"{text[:max_length]}..." if len(text) > max_length else text
    return f'<span title="{escape(text)}">{escape(visible)}</span>'


def _datatable_page(request, queryset):
    try:
        start = max(int(request.GET.get("start", 0)), 0)
    except (TypeError, ValueError):
        start = 0
    try:
        length = int(request.GET.get("length", 50))
    except (TypeError, ValueError):
        length = 50
    if length < 0:
        length = 50
    return queryset[start:start + min(length, 200)]


def _draw(request):
    try:
        return int(request.GET.get("draw", 0))
    except (TypeError, ValueError):
        return 0


def _filter_menice(request, queryset):
    q = (request.GET.get("q") or "").strip()
    date_from = _parse_filter_date(request.GET.get("date_from"))
    date_to = _parse_filter_date(request.GET.get("date_to"))
    status = (request.GET.get("status") or "").strip()
    oj = (request.GET.get("oj") or "").strip()
    if q:
        queryset = queryset.filter(
            Q(serijski_broj_menice__icontains=q)
            | Q(osnov_izdavanja__icontains=q)
            | Q(naziv_duznika__icontains=q)
            | Q(naziv_banke__icontains=q)
            | Q(broj_ugovora__icontains=q)
        )
    if date_from:
        queryset = queryset.filter(datum_registracije__gte=date_from)
    if date_to:
        queryset = queryset.filter(datum_registracije__lte=date_to)
    if status:
        queryset = queryset.filter(interni_status=status)
    if oj:
        queryset = queryset.filter(oj__icontains=oj)
    return queryset


def _filter_ulazne_menice(request, queryset):
    q = (request.GET.get("q") or "").strip()
    date_from = _parse_filter_date(request.GET.get("date_from"))
    date_to = _parse_filter_date(request.GET.get("date_to"))
    location = (request.GET.get("location") or "").strip()
    center = (request.GET.get("center") or "").strip()
    if q:
        queryset = queryset.filter(
            Q(serijski_broj_menice__icontains=q)
            | Q(osnov_izdavanja__icontains=q)
            | Q(naziv_pravnog_lica__icontains=q)
            | Q(broj_naseg_ugovora__icontains=q)
        )
    if date_from:
        queryset = queryset.filter(datum_prijema_menice__gte=date_from)
    if date_to:
        queryset = queryset.filter(datum_prijema_menice__lte=date_to)
    if location:
        queryset = queryset.filter(lokacija_menice__icontains=location)
    if center:
        queryset = queryset.filter(sifra_centra__icontains=center)
    return queryset


class MenicaTipMixin(RolePermissionRequiredMixin, LoginRequiredMixin):
    tip = None

    def dispatch(self, request, *args, **kwargs):
        self.tip = kwargs.get("tip")
        if self.tip not in TIP_TITLES:
            raise Http404("Nepoznat tip menice.")
        return super().dispatch(request, *args, **kwargs)

    def get_tip_title(self):
        return TIP_TITLES[self.tip]


class MenicaListView(MenicaTipMixin, ListView):
    model = Menica
    template_name = "menice/menica_list.html"
    context_object_name = "menice"

    def get_queryset(self):
        return Menica.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tip"] = self.tip
        context["title"] = self.get_tip_title()
        context["q"] = (self.request.GET.get("q") or "").strip()
        context["date_from"] = self.request.GET.get("date_from") or ""
        context["date_to"] = self.request.GET.get("date_to") or ""
        context["status"] = self.request.GET.get("status") or ""
        context["oj"] = (self.request.GET.get("oj") or "").strip()
        context["status_choices"] = Menica.INTERNI_STATUS_CHOICES
        return context


class MenicaDataView(MenicaTipMixin, View):
    def get(self, request, *args, **kwargs):
        menice = _filter_menice(request, Menica.objects.filter(tip=self.tip))
        search_value = request.GET.get("search[value]", "").strip()
        if search_value:
            menice = menice.filter(
                Q(serijski_broj_menice__icontains=search_value)
                | Q(osnov_izdavanja__icontains=search_value)
                | Q(naziv_duznika__icontains=search_value)
                | Q(naziv_banke__icontains=search_value)
                | Q(broj_ugovora__icontains=search_value)
                | Q(oj__icontains=search_value)
                | Q(napomena__icontains=search_value)
            )
        records_filtered = menice.count()
        order_map = {
            "0": "serijski_broj_menice",
            "1": "osnov_izdavanja",
            "2": "datum_registracije",
            "3": "naziv_banke",
            "4": "broj_ugovora",
            "5": "datum_ugovora",
            "6": "oj",
            "7": "napomena",
            "8": "interni_status",
        }
        order_field = order_map.get(request.GET.get("order[0][column]", "2"), "datum_registracije")
        if request.GET.get("order[0][dir]", "desc") == "desc":
            order_field = f"-{order_field}"
        menice = menice.order_by(order_field, "-id")

        rows = []
        for menica in _datatable_page(request, menice):
            detail_url = reverse("menice:menica_detail", kwargs={"tip": self.tip, "pk": menica.pk})
            rows.append(
                {
                    "serial": (
                        f'<a href="{detail_url}" class="btn btn-sm btn-outline-primary">'
                        f'<i class="mdi mdi-eye"></i> {_hover_text(menica.serijski_broj_menice, 25)}</a>'
                    ),
                    "basis": _hover_text(menica.osnov_izdavanja, 35),
                    "registration_date": menica.datum_registracije.strftime("%d.%m.%Y") if menica.datum_registracije else "",
                    "bank": _hover_text(menica.naziv_banke, 30),
                    "contract_number": _hover_text(menica.broj_ugovora, 25),
                    "contract_date": menica.datum_ugovora.strftime("%d.%m.%Y") if menica.datum_ugovora else "",
                    "oj": _hover_text(menica.oj, 20),
                    "note": _hover_text(menica.napomena, 45),
                    "status": f'<span class="menica-badge status-{menica.interni_status}">{escape(menica.get_interni_status_display())}</span>',
                    "actions": (
                        f'<a class="btn btn-sm btn-primary" href="{reverse("menice:menica_update", kwargs={"tip": self.tip, "pk": menica.pk})}" title="Izmeni"><i class="mdi mdi-pencil"></i></a> '
                    ),
                }
            )
        return JsonResponse(
            {
                "draw": _draw(request),
                "recordsTotal": Menica.objects.filter(tip=self.tip).count(),
                "recordsFiltered": records_filtered,
                "data": rows,
            }
        )


class MenicaDetailView(MenicaTipMixin, DetailView):
    model = Menica
    template_name = "menice/menica_detail.html"
    context_object_name = "menica"

    def get_queryset(self):
        return Menica.objects.filter(tip=self.tip)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tip"] = self.tip
        context["title"] = f"Detalj - {self.object.serijski_broj_menice or self.object.pk}"
        context["fields"] = [
            ("Naziv duznika", self.object.naziv_duznika, "text"),
            ("Maticni broj duznika", self.object.maticni_broj_duznika, "text"),
            ("Poreski broj duznika", self.object.poreski_broj_duznika, "text"),
            ("Strana rezultata", self.object.strana_rezultata, "text"),
            ("Serijski broj menice", self.object.serijski_broj_menice, "text"),
            ("Datum izdavanja", self.object.datum_izdavanja, "date"),
            ("Iznos menice", self.object.iznos_menice, "text"),
            ("Valuta menice", self.object.valuta_menice, "text"),
            ("Datum dospeca", self.object.datum_dospeca, "date"),
            ("Izdavalac menice", self.object.izdavalac_menice, "text"),
            ("Vrsta menice", self.object.vrsta_menice, "text"),
            ("Redni broj", self.object.redni_broj, "text"),
            ("Osnov izdavanja", self.object.osnov_izdavanja, "text"),
            ("Iznos iz osnova", self.object.iznos_iz_osnova, "text"),
            ("Valuta osnova", self.object.valuta_osnova, "text"),
            ("Datum registracije", self.object.datum_registracije, "date"),
            ("Naziv banke", self.object.naziv_banke, "text"),
            ("Status", self.object.status, "text"),
            ("Avalisti detalji", self.object.avalisti_detalji, "text"),
            ("Avalisti broj zapisa", self.object.avalisti_broj_zapisa, "text"),
            ("Broj ugovora", self.object.broj_ugovora, "text"),
            ("Datum ugovora", self.object.datum_ugovora, "date"),
            ("OJ", self.object.oj, "text"),
            ("Napomena", self.object.napomena, "text"),
            ("Interni status", self.object.get_interni_status_display(), "text"),
            ("Kreirano", self.object.created_at, "datetime"),
            ("Azurirano", self.object.updated_at, "datetime"),
        ]
        return context


class MenicaCreateView(MenicaTipMixin, CreateView):
    model = Menica
    form_class = MenicaCreateForm
    template_name = "menice/menica_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.tip = kwargs.get("tip")
        if self.tip not in TIP_TITLES:
            raise Http404("Nepoznat tip menice.")
        if self.tip == Menica.TIP_IZLAZNA:
            raise Http404("Izlazne menice se povlace iz NBS registra.")
        return super(MenicaTipMixin, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.tip = self.tip
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Nova - {self.get_tip_title()}"
        context["submit_button_label"] = "Sacuvaj"
        context["cancel_url"] = reverse("menice:menica_list", kwargs={"tip": self.tip})
        return context


class MenicaUpdateView(MenicaTipMixin, UpdateView):
    model = Menica
    form_class = MenicaUpdateForm
    template_name = "menice/menica_form.html"

    def get_queryset(self):
        return Menica.objects.filter(tip=self.tip)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.tip == Menica.TIP_IZLAZNA:
            form.fields.pop("fizicka_lokacija", None)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Izmena - {self.get_tip_title()}"
        context["submit_button_label"] = "Sacuvaj"
        context["cancel_url"] = reverse("menice:menica_list", kwargs={"tip": self.tip})
        return context


class MenicaDeleteView(MenicaTipMixin, DeleteView):
    model = Menica
    template_name = "menice/menica_confirm_delete.html"

    def get_queryset(self):
        return Menica.objects.filter(tip=self.tip)

    def get_success_url(self):
        return reverse("menice:menica_list", kwargs={"tip": self.tip})

    def form_valid(self, form):
        if self.tip == Menica.TIP_IZLAZNA:
            self.object.interni_status = Menica.STATUS_OBRISANA
            self.object.save(update_fields=["interni_status", "updated_at"])
            messages.success(self.request, "Menica je oznacena kao obrisana.")
            return redirect(self.get_success_url())
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Brisanje - {self.get_tip_title()}"
        context["soft_delete"] = self.tip == Menica.TIP_IZLAZNA
        return context


class IzlazneMeniceSyncView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request):
        try:
            result = sync_izlazne_menice()
        except Exception as exc:
            messages.error(request, f"Greska pri povlacenju izlaznih menica: {exc}")
        else:
            messages.success(
                request,
                (
                    "Povuceno: {fetched}, novo: {created}, azurirano: {updated}, "
                    "bez izmene: {unchanged}, preskoceno: {skipped}"
                ).format(**result),
            )
        return redirect("menice:menica_list", tip=Menica.TIP_IZLAZNA)


class UlaznaMenicaListView(RolePermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = UlaznaMenica
    template_name = "menice/ulazna_menica_list.html"
    context_object_name = "menice"

    def get_queryset(self):
        return UlaznaMenica.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ulazne menice"
        context["q"] = (self.request.GET.get("q") or "").strip()
        context["date_from"] = self.request.GET.get("date_from") or ""
        context["date_to"] = self.request.GET.get("date_to") or ""
        context["location"] = (self.request.GET.get("location") or "").strip()
        context["center"] = (self.request.GET.get("center") or "").strip()
        return context


class UlaznaMenicaDataView(RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def get(self, request):
        menice = _filter_ulazne_menice(request, UlaznaMenica.objects.all())
        search_value = request.GET.get("search[value]", "").strip()
        if search_value:
            menice = menice.filter(
                Q(serijski_broj_menice__icontains=search_value)
                | Q(osnov_izdavanja__icontains=search_value)
                | Q(naziv_pravnog_lica__icontains=search_value)
                | Q(broj_naseg_ugovora__icontains=search_value)
                | Q(lokacija_menice__icontains=search_value)
                | Q(sifra_centra__icontains=search_value)
            )
        records_filtered = menice.count()
        order_map = {
            "0": "serijski_broj_menice",
            "1": "osnov_izdavanja",
            "2": "datum_prijema_menice",
            "3": "jedinica_vrednosti",
            "4": "procenat_iznos",
            "5": "sifra_poslovnog_partnera",
            "6": "broj_naseg_ugovora",
            "7": "datum_ugovora",
            "8": "ugovor_vazi_do",
            "9": "lokacija_menice",
            "10": "sifra_centra",
        }
        order_field = order_map.get(request.GET.get("order[0][column]", "2"), "datum_prijema_menice")
        if request.GET.get("order[0][dir]", "desc") == "desc":
            order_field = f"-{order_field}"
        menice = menice.order_by(order_field, "-id")

        rows = []
        for menica in _datatable_page(request, menice):
            rows.append(
                {
                    "serial": _hover_text(menica.serijski_broj_menice, 25),
                    "basis": _hover_text(menica.osnov_izdavanja, 35),
                    "received_date": menica.datum_prijema_menice.strftime("%d.%m.%Y") if menica.datum_prijema_menice else "",
                    "unit": menica.get_jedinica_vrednosti_display(),
                    "amount": str(menica.procenat_iznos or ""),
                    "partner_code": str(menica.sifra_poslovnog_partnera or ""),
                    "contract_number": _hover_text(menica.broj_naseg_ugovora, 25),
                    "contract_date": menica.datum_ugovora.strftime("%d.%m.%Y") if menica.datum_ugovora else "",
                    "contract_valid_until": menica.ugovor_vazi_do.strftime("%d.%m.%Y") if menica.ugovor_vazi_do else "",
                    "location": _hover_text(menica.lokacija_menice, 20),
                    "center": _hover_text(menica.sifra_centra, 15),
                    "actions": (
                        f'<a class="btn btn-sm btn-primary" href="{reverse("menice:ulazna_menica_update", kwargs={"pk": menica.pk})}" title="Izmeni"><i class="mdi mdi-pencil"></i></a> '
                        f'<a class="btn btn-sm btn-outline-danger" href="{reverse("menice:ulazna_menica_delete", kwargs={"pk": menica.pk})}" title="Obrisi"><i class="mdi mdi-delete"></i></a>'
                    ),
                }
            )
        return JsonResponse(
            {
                "draw": _draw(request),
                "recordsTotal": UlaznaMenica.objects.count(),
                "recordsFiltered": records_filtered,
                "data": rows,
            }
        )


class UlaznaMenicaCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = UlaznaMenica
    form_class = UlaznaMenicaForm
    template_name = "menice/menica_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Nova - Ulazna menica"
        context["submit_button_label"] = "Sacuvaj"
        context["cancel_url"] = reverse("menice:ulazna_menica_list")
        context["is_ulazna_menica_form"] = True
        return context


class UlaznaMenicaUpdateView(RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = UlaznaMenica
    form_class = UlaznaMenicaForm
    template_name = "menice/menica_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmena - Ulazna menica"
        context["submit_button_label"] = "Sacuvaj"
        context["cancel_url"] = reverse("menice:ulazna_menica_list")
        context["is_ulazna_menica_form"] = True
        return context


class UlaznaMenicaDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = UlaznaMenica
    template_name = "menice/menica_confirm_delete.html"

    def get_success_url(self):
        return reverse("menice:ulazna_menica_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Brisanje - Ulazna menica"
        return context
