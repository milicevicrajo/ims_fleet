from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import MenicaCreateForm, MenicaUpdateForm, UlaznaMenicaForm
from .models import Menica, UlaznaMenica
from .services import sync_izlazne_menice


TIP_TITLES = {
    Menica.TIP_IZLAZNA: "Izlazne menice",
    Menica.TIP_ULAZNA: "Ulazne menice",
}


class MenicaTipMixin(LoginRequiredMixin):
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
        return Menica.objects.filter(tip=self.tip)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tip"] = self.tip
        context["title"] = self.get_tip_title()
        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Brisanje - {self.get_tip_title()}"
        return context


class IzlazneMeniceSyncView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            result = sync_izlazne_menice()
        except Exception as exc:
            messages.error(request, f"Greska pri povlacenju izlaznih menica: {exc}")
        else:
            messages.success(
                request,
                "Povuceno: {fetched}, novo: {created}, preskoceno: {skipped}".format(**result),
            )
        return redirect("menice:menica_list", tip=Menica.TIP_IZLAZNA)


class UlaznaMenicaListView(LoginRequiredMixin, ListView):
    model = UlaznaMenica
    template_name = "menice/ulazna_menica_list.html"
    context_object_name = "menice"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Ulazne menice"
        return context


class UlaznaMenicaCreateView(LoginRequiredMixin, CreateView):
    model = UlaznaMenica
    form_class = UlaznaMenicaForm
    template_name = "menice/menica_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Nova - Ulazna menica"
        context["submit_button_label"] = "Sacuvaj"
        context["cancel_url"] = reverse("menice:ulazna_menica_list")
        return context


class UlaznaMenicaUpdateView(LoginRequiredMixin, UpdateView):
    model = UlaznaMenica
    form_class = UlaznaMenicaForm
    template_name = "menice/menica_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmena - Ulazna menica"
        context["submit_button_label"] = "Sacuvaj"
        context["cancel_url"] = reverse("menice:ulazna_menica_list")
        return context


class UlaznaMenicaDeleteView(LoginRequiredMixin, DeleteView):
    model = UlaznaMenica
    template_name = "menice/menica_confirm_delete.html"

    def get_success_url(self):
        return reverse("menice:ulazna_menica_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Brisanje - Ulazna menica"
        return context
