"""Fiskalni racuni (Nabavka): spisak, ucitavanje citacem QR koda, detalj, ponovno preuzimanje."""
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from django.views.generic import DetailView, TemplateView

from core.mixins import RolePermissionRequiredMixin
from fleet.models import OrganizationalUnit
from nabavka.access import fiskalni_racuni, sifre_za_izbor

from ..models import FiskalniRacun
from ..services import fiskalni
from .cases import NabavkaContextMixin


class FiskalniRacunForm(forms.Form):
    job_code = forms.ModelChoiceField(queryset=OrganizationalUnit.objects.none(), label="Šifra posla",
                                      empty_label="— izaberite šifru posla —",
                                      widget=forms.Select(attrs={"class": "form-select", "id": "fiskalniSifra"}))
    link = forms.CharField(label="Link sa QR koda računa", widget=forms.Textarea(attrs={
        "class": "form-control font-monospace", "rows": 4, "id": "fiskalniLink", "autocomplete": "off",
        "spellcheck": "false", "placeholder": "Očitajte QR kod računa čitačem…"}))
    napomena = forms.CharField(label="Napomena", required=False, max_length=500,
                               widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, user, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        from fleet.support.registar import ogranici_izbor

        self.fields["job_code"].queryset = sifre_za_izbor(OrganizationalUnit.objects.order_by("code"), user)
        # Samo aktivne sifre posla iz registra (odluka 25.09.2026.), uz vec upisanu na racunu.
        ogranici_izbor(self.fields["job_code"], getattr(instance, "job_code_id", None))


class SifraRacunaForm(forms.ModelForm):
    class Meta:
        model = FiskalniRacun
        fields = ["job_code", "napomena"]
        widgets = {"job_code": forms.Select(attrs={"class": "form-select select2-method"}),
                   "napomena": forms.TextInput(attrs={"class": "form-control"})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        from fleet.support.registar import ogranici_izbor

        self.fields["job_code"].queryset = sifre_za_izbor(OrganizationalUnit.objects.order_by("code"), user)
        ogranici_izbor(self.fields["job_code"], self.instance.job_code_id)


def _vidljivi(user):
    return fiskalni_racuni(FiskalniRacun.objects.select_related("job_code", "created_by"), user)


class FiskalniRacunListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/fiskalni_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title="Fiskalni računi", form=FiskalniRacunForm(user=self.request.user),
                   q=self.request.GET.get("q", ""), na_ims=self.request.GET.get("na_ims", ""),
                   status=self.request.GET.get("status", ""), statusi=FiskalniRacun.Status.choices)
        return ctx


def _filtriraj(request, qs):
    q = (request.GET.get("q") or "").strip()
    pretraga = (request.GET.get("search[value]") or "").strip()
    for termin in (q, pretraga):
        if termin:
            qs = qs.filter(Q(broj_racuna__icontains=termin) | Q(naziv_prodavca__icontains=termin)
                           | Q(prodajno_mesto__icontains=termin) | Q(pib_prodavca__icontains=termin)
                           | Q(job_code__code__icontains=termin) | Q(job_code__name__icontains=termin)
                           | Q(stavke__naziv__icontains=termin)).distinct()
    if request.GET.get("na_ims") in ("1", "0"):
        qs = qs.filter(na_ims=request.GET["na_ims"] == "1")
    if request.GET.get("status"):
        qs = qs.filter(status=request.GET["status"])
    return qs


class FiskalniRacunDataView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    KOLONE = {"0": "pfr_vreme", "1": "naziv_prodavca", "2": "broj_racuna", "3": "iznos", "4": "job_code__code",
              "5": "na_ims", "6": "status"}

    def get(self, request):
        sve = _vidljivi(request.user)
        qs = _filtriraj(request, sve)
        polje = self.KOLONE.get(request.GET.get("order[0][column]", "0"), "pfr_vreme")
        if request.GET.get("order[0][dir]", "desc") == "desc":
            polje = f"-{polje}"
        qs = qs.order_by(polje, "-id")
        try:
            start = max(int(request.GET.get("start", 0)), 0)
            duzina = min(max(int(request.GET.get("length", 50)), 1), 200)
        except (TypeError, ValueError):
            start, duzina = 0, 50
        redovi = []
        for r in qs[start:start + duzina]:
            detalj = reverse("nabavka:fiskalni_detail", kwargs={"pk": r.pk})
            redovi.append({
                "pfr_vreme": timezone.localtime(r.pfr_vreme).strftime("%d.%m.%Y %H:%M"),
                "prodavac": (f'<span title="PIB {escape(r.pib_prodavca)}">{escape(r.naziv_prodavca or r.pib_prodavca or "—")}</span>'
                             f'<div class="fiskalni-small">{escape(r.prodajno_mesto)}</div>'),
                "broj_racuna": escape(r.broj_racuna),
                "iznos": f"{r.iznos:,.2f}".replace(",", " ").replace(".", ",").replace(" ", "."),
                "sifra": escape(f"{r.job_code.code.strip()} · {r.job_code.name}") if r.job_code_id else "—",
                "na_ims": ('<span class="invoice-badge ok"><i class="mdi mdi-domain"></i> IMS</span>' if r.na_ims else
                           '<span class="invoice-badge warn" title="Račun nije izdat na IMS"><i class="mdi mdi-account-alert"></i> '
                           + ("Drugi kupac" if r.id_kupca else "Fizičko lice") + "</span>"),
                "status": ('<span class="invoice-badge ok">Potvrđen</span>' if r.status == FiskalniRacun.Status.POTVRDJEN
                           else '<span class="invoice-badge muted" title="Stavke još nisu preuzete">Čeka proveru</span>'),
                "akcije": f'<a class="btn btn-outline-primary btn-sm" href="{detalj}"><i class="mdi mdi-eye"></i> Detalj</a>',
            })
        try:
            draw = int(request.GET.get("draw", 0))
        except (TypeError, ValueError):
            draw = 0
        return JsonResponse({"draw": draw, "recordsTotal": sve.count(), "recordsFiltered": qs.count(), "data": redovi})


class FiskalniRacunScanView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    """Obrada ocitanog linka: JSON za modal (bez stranice) ili preusmerenje (obican POST)."""

    def post(self, request):
        ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        form = FiskalniRacunForm(request.POST, user=request.user)
        if not form.is_valid():
            greska = " ".join(e for greske in form.errors.values() for e in greske)
            return self._odgovor(request, ajax, ok=False, poruka=greska or "Proverite unos.")
        try:
            racun, upozorenja = fiskalni.upisi(form.cleaned_data["link"], form.cleaned_data["job_code"], request.user,
                                               form.cleaned_data["napomena"])
        except fiskalni.GreskaOcitavanja as exc:
            return self._odgovor(request, ajax, ok=False, poruka=str(exc))
        return self._odgovor(request, ajax, ok=True, racun=racun, upozorenja=upozorenja)

    def _odgovor(self, request, ajax, ok, poruka="", racun=None, upozorenja=()):
        if ajax:
            podaci = {"ok": ok, "poruka": poruka, "upozorenja": list(upozorenja)}
            if racun:
                podaci.update(broj=racun.broj_racuna, prodavac=racun.naziv_prodavca or racun.pib_prodavca,
                              iznos=f"{racun.iznos:,.2f}".replace(",", " ").replace(".", ",").replace(" ", "."),
                              stavki=racun.stavke.count(), na_ims=racun.na_ims,
                              url=reverse("nabavka:fiskalni_detail", kwargs={"pk": racun.pk}))
            return JsonResponse(podaci, status=200 if ok else 400)
        if not ok:
            messages.error(request, poruka)
            return redirect("nabavka:fiskalni_list")
        messages.success(request, f"Račun {racun.broj_racuna} je učitan.")
        for u in upozorenja:
            messages.warning(request, u)
        return redirect("nabavka:fiskalni_detail", pk=racun.pk)


class FiskalniRacunDetailView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = FiskalniRacun
    template_name = "nabavka/fiskalni_detail.html"
    context_object_name = "racun"

    def get_queryset(self):
        return _vidljivi(self.request.user).prefetch_related("stavke")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title=f"Fiskalni račun {self.object.broj_racuna}", upozorenja=fiskalni.upozorenja(self.object),
                   sifra_form=SifraRacunaForm(instance=self.object, user=self.request.user))
        return ctx


class FiskalniRacunRefreshView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        racun = get_object_or_404(_vidljivi(request.user), pk=pk)
        if fiskalni.preuzmi(racun):
            messages.success(request, "Podaci su ponovo preuzeti sa stranice za proveru.")
        else:
            messages.error(request, f"Stranica za proveru nije dostupna: {racun.greska}")
        return redirect("nabavka:fiskalni_detail", pk=pk)


class FiskalniRacunUpdateView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        racun = get_object_or_404(_vidljivi(request.user), pk=pk)
        form = SifraRacunaForm(request.POST, instance=racun, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Šifra posla i napomena su sačuvani.")
        else:
            messages.error(request, " ".join(e for greske in form.errors.values() for e in greske))
        return redirect("nabavka:fiskalni_detail", pk=pk)


class FiskalniRacunDeleteView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        racun = get_object_or_404(_vidljivi(request.user), pk=pk)
        broj = racun.broj_racuna
        racun.delete()
        messages.success(request, f"Račun {broj} je obrisan.")
        return redirect("nabavka:fiskalni_list")
