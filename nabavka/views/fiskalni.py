"""Fiskalni racuni (Nabavka): spisak, ucitavanje citacem QR koda, detalj, obrada, vraceno."""
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
from django_select2.forms import Select2Widget

from core.mixins import RolePermissionRequiredMixin
from fleet.models import JobCode, OrganizationalUnit, Vehicle
from nabavka.access import fiskalni_racuni, sifre_za_izbor

from ..models import FiskalniRacun, FiskalniRacunSifra
from ..services import fiskalni
from .cases import NabavkaContextMixin


def _izbor_sifara(field, user, zadrzi=None):
    """Samo aktivne sifre posla iz registra, u obuhvatu korisnika, uz vec upisanu."""
    from fleet.support.registar import ogranici_izbor

    field.queryset = sifre_za_izbor(OrganizationalUnit.objects.order_by("code"), user)
    ogranici_izbor(field, zadrzi)


class FiskalniRacunForm(forms.Form):
    job_code = forms.ModelChoiceField(queryset=OrganizationalUnit.objects.none(), label="Šifra posla",
                                      empty_label="— izaberite šifru posla —",
                                      widget=forms.Select(attrs={"class": "form-select", "id": "fiskalniSifra"}))
    link = forms.CharField(label="Link sa QR koda računa", widget=forms.Textarea(attrs={
        "class": "form-control font-monospace", "rows": 4, "id": "fiskalniLink", "autocomplete": "off",
        "spellcheck": "false", "placeholder": "Očitajte QR kod računa čitačem…"}))
    napomena = forms.CharField(label="Napomena", required=False, max_length=500,
                               widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        _izbor_sifara(self.fields["job_code"], user)


class ObradaRacunaForm(forms.ModelForm):
    """Obrada kao kod EUF faktura: glavna sifra posla, garaza (vozilo, vrsta intervencije), magacin."""

    class Meta:
        model = FiskalniRacun
        fields = ["job_code", "is_garage", "vehicle", "work_type", "goes_to_warehouse", "napomena"]
        labels = {"job_code": "Glavna šifra posla"}
        widgets = {"job_code": Select2Widget(attrs={"class": "select2-method"}),
                   "vehicle": Select2Widget(attrs={"class": "select2-method"}),
                   "work_type": forms.Select(attrs={"class": "form-select"}),
                   "is_garage": forms.CheckboxInput(attrs={"class": "form-check-input"}),
                   "goes_to_warehouse": forms.CheckboxInput(attrs={"class": "form-check-input"}),
                   "napomena": forms.TextInput(attrs={"class": "form-control"})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        _izbor_sifara(self.fields["job_code"], user, self.instance.job_code_id)
        self.fields["vehicle"].required = False
        self.fields["vehicle"].queryset = Vehicle.objects.order_by("brand", "model")
        self.fields["work_type"].required = False

    def clean(self):
        data = super().clean()
        if not data.get("is_garage"):
            data["vehicle"], data["work_type"] = None, ""
        elif data.get("vehicle"):
            # Kao kod EUF faktura: garazni racun ide na sifru posla na kojoj je vozilo danas.
            dodela = (JobCode.objects.select_related("organizational_unit")
                      .filter(vehicle=data["vehicle"], organizational_unit__isnull=False,
                              assigned_date__lte=timezone.localdate()).order_by("-assigned_date", "-pk").first())
            if dodela:
                data["job_code"] = dodela.organizational_unit
        return data


class DodatnaSifraForm(forms.Form):
    job_code = forms.ModelChoiceField(queryset=OrganizationalUnit.objects.none(), label="Dodatna šifra posla",
                                      widget=Select2Widget(attrs={"class": "select2-method"}))
    note = forms.CharField(label="Napomena", required=False, max_length=255,
                           widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, user, racun, **kwargs):
        super().__init__(*args, **kwargs)
        self.racun = racun
        _izbor_sifara(self.fields["job_code"], user)

    def clean_job_code(self):
        sifra = self.cleaned_data["job_code"]
        if self.racun.sifre.filter(job_code=sifra).exists():
            raise forms.ValidationError("Ta šifra posla je već na računu.")
        return sifra


def _vidljivi(user):
    return fiskalni_racuni(FiskalniRacun.objects.select_related("job_code", "created_by", "vehicle"), user)


def _iznos(vrednost):
    return f"{vrednost:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def _vracene_sifre(racun):
    return [s.job_code.code.strip() for s in racun.sifre.all() if s.is_returned]


def _dugme_vraceno(racun):
    url = reverse("nabavka:fiskalni_returned", kwargs={"pk": racun.pk})
    vracene = _vracene_sifre(racun)
    klasa = "btn-outline-warning" if vracene else "btn-outline-secondary"
    stanje = f'<div class="fiskalni-small">{escape(", ".join(vracene))}</div>' if vracene else ""
    return (f'<button type="button" class="btn {klasa} btn-sm js-fiskalni-vraceno" data-url="{url}" '
            f'data-racun="{escape(racun.broj_racuna)}"><i class="mdi mdi-clipboard-check-outline"></i> Vraćeno</button>{stanje}')


class FiskalniRacunListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/fiskalni_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(title="Fiskalni računi", form=FiskalniRacunForm(user=self.request.user),
                   q=self.request.GET.get("q", ""), na_ims=self.request.GET.get("na_ims", ""),
                   status=self.request.GET.get("status", ""), statusi=FiskalniRacun.Status.choices,
                   magacin=self.request.GET.get("magacin", ""), garaza=self.request.GET.get("garaza", ""))
        return ctx


def _filtriraj(request, qs):
    q = (request.GET.get("q") or "").strip()
    pretraga = (request.GET.get("search[value]") or "").strip()
    for termin in (q, pretraga):
        if termin:
            qs = qs.filter(Q(broj_racuna__icontains=termin) | Q(naziv_prodavca__icontains=termin)
                           | Q(prodajno_mesto__icontains=termin) | Q(pib_prodavca__icontains=termin)
                           | Q(sifre__job_code__code__icontains=termin) | Q(sifre__job_code__name__icontains=termin)
                           | Q(stavke__naziv__icontains=termin)).distinct()
    for parametar, polje in (("na_ims", "na_ims"), ("magacin", "goes_to_warehouse"), ("garaza", "is_garage")):
        if request.GET.get(parametar) in ("1", "0"):
            qs = qs.filter(**{polje: request.GET[parametar] == "1"})
    if request.GET.get("status"):
        qs = qs.filter(status=request.GET["status"])
    return qs


class FiskalniRacunDataView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    KOLONE = {"0": "pfr_vreme", "1": "naziv_prodavca", "2": "broj_racuna", "3": "iznos", "4": "job_code__code",
              "5": "goes_to_warehouse", "6": "is_garage", "7": "is_returned", "8": "na_ims", "9": "status"}

    def get(self, request):
        sve = _vidljivi(request.user)
        qs = _filtriraj(request, sve).prefetch_related("sifre__job_code", "vehicle__traffic_cards")
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
            sifre = [s.job_code.code.strip() for s in sorted(r.sifre.all(), key=lambda s: (s.vrsta != "osnovna", s.job_code.code))]
            tablica = next((t.registration_number for t in r.vehicle.traffic_cards.all()), "") if r.vehicle_id else ""
            redovi.append({
                "pfr_vreme": timezone.localtime(r.pfr_vreme).strftime("%d.%m.%Y %H:%M"),
                "prodavac": (f'<span title="PIB {escape(r.pib_prodavca)}">{escape(r.naziv_prodavca or r.pib_prodavca or "—")}</span>'
                             f'<div class="fiskalni-small">{escape(r.prodajno_mesto)}</div>'),
                "broj_racuna": escape(r.broj_racuna),
                "iznos": _iznos(r.iznos),
                "sifra": escape(", ".join(sifre) or (r.job_code.code if r.job_code_id else "—")),
                "magacin": ('<span class="invoice-badge ok"><i class="mdi mdi-warehouse"></i> Da</span>' if r.goes_to_warehouse
                            else '<span class="invoice-badge muted">Ne</span>'),
                "garaza": (('<span class="invoice-badge warn"><i class="mdi mdi-car-wrench"></i> Da</span>'
                            + (f'<div class="fiskalni-small">{escape(tablica)}</div>' if tablica else "")) if r.is_garage
                           else '<span class="invoice-badge muted">Ne</span>'),
                "vraceno": _dugme_vraceno(r),
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
                              iznos=_iznos(racun.iznos), stavki=racun.stavke.count(), na_ims=racun.na_ims,
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
        return _vidljivi(self.request.user).prefetch_related("stavke", "sifre__job_code", "sifre__returned_by")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.object.uskladi_glavnu_sifru(self.request.user)
        ctx.update(title=f"Fiskalni račun {self.object.broj_racuna}", upozorenja=fiskalni.upozorenja(self.object),
                   obrada_form=kwargs.get("obrada_form") or ObradaRacunaForm(instance=self.object, user=self.request.user),
                   sifra_form=kwargs.get("sifra_form") or DodatnaSifraForm(user=self.request.user, racun=self.object),
                   sifre=sorted(self.object.sifre.all(), key=lambda s: (s.vrsta != FiskalniRacunSifra.OSNOVNA, s.job_code.code)))
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
    """Obrada racuna (glavna sifra, garaza, magacin, napomena) i dodatne sifre posla."""

    def post(self, request, pk):
        racun = get_object_or_404(_vidljivi(request.user), pk=pk)
        akcija = request.POST.get("akcija", "obrada")
        if akcija == "dodaj_sifru":
            form = DodatnaSifraForm(request.POST, user=request.user, racun=racun)
            if form.is_valid():
                FiskalniRacunSifra.objects.create(racun=racun, job_code=form.cleaned_data["job_code"],
                                                  note=form.cleaned_data["note"], created_by=request.user)
                messages.success(request, "Šifra posla je dodata.")
            else:
                messages.error(request, " ".join(e for greske in form.errors.values() for e in greske))
        elif akcija == "obrisi_sifru":
            veza = get_object_or_404(racun.sifre, pk=request.POST.get("sifra"))
            if veza.vrsta == FiskalniRacunSifra.OSNOVNA:
                messages.error(request, "Glavna šifra posla se menja u obradi računa, ne briše se.")
            else:
                veza.delete()
                messages.success(request, "Šifra posla je uklonjena sa računa.")
        else:
            form = ObradaRacunaForm(request.POST, instance=racun, user=request.user)
            if form.is_valid():
                form.save()
                racun.uskladi_glavnu_sifru(request.user)
                messages.success(request, "Obrada računa je sačuvana.")
            else:
                messages.error(request, " ".join(e for greske in form.errors.values() for e in greske))
        return redirect("nabavka:fiskalni_detail", pk=pk)


class FiskalniRacunReturnedView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    """„Vraceno” po sifri posla (prozor na spisku), kao kod Preuzetih EUF."""

    @staticmethod
    def _redovi(racun):
        return [{"id": s.pk, "code": s.job_code.code.strip(), "name": s.job_code.name,
                 "kind_label": s.get_vrsta_display(), "is_returned": s.is_returned}
                for s in sorted(racun.sifre.select_related("job_code"),
                                key=lambda s: (s.vrsta != FiskalniRacunSifra.OSNOVNA, s.job_code.code))]

    def get(self, request, pk):
        racun = get_object_or_404(_vidljivi(request.user), pk=pk)
        racun.uskladi_glavnu_sifru(request.user)
        return JsonResponse({"ok": True, "racun": racun.broj_racuna, "job_codes": self._redovi(racun)})

    def post(self, request, pk):
        racun = get_object_or_404(_vidljivi(request.user), pk=pk)
        vracene = {int(v) for v in request.POST.getlist("returned_links") if str(v).isdigit()}
        sada = timezone.now()
        for veza in racun.sifre.all():
            treba = veza.pk in vracene
            if veza.is_returned != treba:
                veza.is_returned = treba
                veza.returned_at, veza.returned_by = (sada, request.user) if treba else (None, None)
                veza.save(update_fields=["is_returned", "returned_at", "returned_by"])
        racun.is_returned = racun.sifre.filter(is_returned=True).exists()
        racun.save(update_fields=["is_returned"])
        return JsonResponse({"ok": True, "racun": racun.broj_racuna, "job_codes": self._redovi(racun),
                             "button_html": _dugme_vraceno(racun)})


class FiskalniRacunDeleteView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        racun = get_object_or_404(_vidljivi(request.user), pk=pk)
        broj = racun.broj_racuna
        racun.delete()
        messages.success(request, f"Račun {broj} je obrisan.")
        return redirect("nabavka:fiskalni_list")
