"""Arhiva — ekrani faze 1: delovodnik, pisarnica (brzi unos), detalj predmeta, šifarnik kategorija.

`views` samo prikazuje; broj i pravila su u `services.delovodnik`.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from arhiva.access import predmeti
from arhiva.forms import AktForm, FilterDelovodnikaForm, PisarnicaForm, StornoForm
from arhiva.models import EvidencionaKnjiga, GrupaKategorija, Kategorija, Predmet, VerzijaListe
from arhiva.services import delovodnik
from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission


class ArhivaContextMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_app"] = "arhiva"
        ctx["sidebar_template"] = "sidebar_arhiva.html"
        return ctx


def _vidljivi(user):
    return predmeti(Predmet.objects.select_related("knjiga", "kategorija", "glavna_oj", "zaveo"), user)


def _sa_oznakom_oj(predmeti_):
    """Svakom predmetu dodaje `oj_oznaka` („43 · Naziv”), jednim upitom za celu stranu."""
    from organizacija.models import OrgNodeVersion

    predmeti_ = list(predmeti_)
    oznake = {pk: f"{sifra} · {naziv}" if naziv else sifra for pk, sifra, naziv in
              OrgNodeVersion.objects.filter(node_id__in={p.glavna_oj_id for p in predmeti_}, valid_to__isnull=True)
              .values_list("node_id", "full_code", "name")}
    for p in predmeti_:
        p.oj_oznaka = oznake.get(p.glavna_oj_id, "")
    return predmeti_


class DelovodnikView(ArhivaContextMixin, LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = "arhiva/delovodnik.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        forma = FilterDelovodnikaForm(self.request.GET or None)
        godina = timezone.localdate().year
        qs = _vidljivi(self.request.user)
        if forma.is_valid():
            f = forma.cleaned_data
            godina = f.get("godina") or godina
            if f.get("smer"):
                qs = qs.filter(smer=f["smer"])
            if f.get("status"):
                qs = qs.filter(status=f["status"])
            for rec in (f.get("q") or "").split():
                qs = qs.filter(Q(delovodni_broj__icontains=rec) | Q(naslov__icontains=rec)
                               | Q(korespondent__icontains=rec) | Q(broj_akta_posiljaoca__icontains=rec))
        qs = qs.filter(knjiga__godina=godina, knjiga__vrsta=EvidencionaKnjiga.Vrsta.DELOVODNIK)
        strana = Paginator(qs.annotate(broj_akata=Count("akti")).order_by("-osnovni_broj"), 50).get_page(self.request.GET.get("page"))
        knjiga = EvidencionaKnjiga.objects.filter(vrsta=EvidencionaKnjiga.Vrsta.DELOVODNIK, godina=godina, oznaka="").first()
        parametri = self.request.GET.copy()
        parametri.pop("page", None)
        ctx.update(title="Delovodnik", forma=forma, godina=godina, knjiga=knjiga, strana=strana,
                   redovi=_sa_oznakom_oj(strana.object_list), parametri=parametri.urlencode(),
                   godine=sorted({godina, *EvidencionaKnjiga.objects.filter(vrsta=EvidencionaKnjiga.Vrsta.DELOVODNIK)
                                  .values_list("godina", flat=True)}, reverse=True),
                   moze_upis=user_has_role_permission(self.request.user, "arhiva:pisarnica"))
        return ctx


class PisarnicaView(ArhivaContextMixin, LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    """Brzi unos pošte. Posle upisa forma ostaje otvorena sa istim smerom i OJ, za sledeći akt."""

    template_name = "arhiva/pisarnica.html"
    SESIJA = "arhiva_pisarnica_poslednje"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        forma = kwargs.get("forma") or PisarnicaForm(initial=self.request.session.get(self.SESIJA, {}))
        danas = timezone.localdate()
        poslednji = _sa_oznakom_oj(_vidljivi(self.request.user).filter(datum_zavodjenja=danas).order_by("-zavedeno_at")[:15])
        ctx.update(title="Pisarnica", forma=forma, poslednji=poslednji, ima_oj=len(forma.fields["glavna_oj"].choices) > 1,
                   ima_listu=VerzijaListe.objects.filter(aktivna=True).exists())
        return ctx

    def post(self, request, *args, **kwargs):
        forma = PisarnicaForm(request.POST)
        if forma.is_valid():
            f = forma.cleaned_data
            try:
                predmet = delovodnik.zavedi(
                    datum=f["datum_zavodjenja"], naslov=f["naslov"], smer=f["smer"], glavna_oj=f["glavna_oj"],
                    zaveo=request.user, korespondent=f["korespondent"], mesto=f["mesto"],
                    broj_akta_posiljaoca=f["broj_akta_posiljaoca"], datum_akta_posiljaoca=f["datum_akta_posiljaoca"],
                    kategorija=f["kategorija"], napomena=f["napomena"])
            except ValidationError as exc:
                forma.add_error(None, "; ".join(exc.messages))
            else:
                request.session[self.SESIJA] = {"smer": f["smer"], "glavna_oj": str(f["glavna_oj"].pk)}
                messages.success(request, f"Zavedeno pod brojem {predmet.delovodni_broj}: {predmet.naslov}")
                return redirect("arhiva:pisarnica")
        return self.render_to_response(self.get_context_data(forma=forma), status=400)


class PredmetDetailView(ArhivaContextMixin, LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = "arhiva/predmet_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        predmet = get_object_or_404(_vidljivi(self.request.user), pk=self.kwargs["pk"])
        user = self.request.user
        ctx.update(title=f"Predmet {predmet.delovodni_broj}", predmet=predmet,
                   akti=predmet.akti.select_related("zaveo").order_by("podbroj"),
                   oj=_sa_oznakom_oj([predmet])[0].oj_oznaka,
                   akt_forma=kwargs.get("akt_forma") or AktForm(), storno_forma=kwargs.get("storno_forma") or StornoForm(),
                   moze_akt=user_has_role_permission(user, "arhiva:akt_add") and not predmet.storniran,
                   moze_storno=user_has_role_permission(user, "arhiva:predmet_storniraj") and not predmet.storniran)
        return ctx


def _predmet(request, pk):
    return get_object_or_404(_vidljivi(request.user), pk=pk)


@login_required
@require_POST
@role_permission_required()
def akt_add(request, pk):
    predmet = _predmet(request, pk)
    forma = AktForm(request.POST)
    if forma.is_valid():
        try:
            akt = delovodnik.dodaj_podbroj(predmet, zaveo=request.user, **forma.cleaned_data)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, f"Upisan akt {akt.delovodni_broj}.")
    else:
        messages.error(request, "Proverite datum i opis akta.")
    return redirect("arhiva:predmet_detail", pk=predmet.pk)


@login_required
@require_POST
@role_permission_required()
def predmet_storniraj(request, pk):
    predmet = _predmet(request, pk)
    forma = StornoForm(request.POST)
    if forma.is_valid():
        try:
            delovodnik.storniraj(predmet, razlog=forma.cleaned_data["razlog"], ko=request.user)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, f"Predmet {predmet.delovodni_broj} je storniran. Broj se ne koristi ponovo.")
    else:
        messages.error(request, "Unesite razlog storna.")
    return redirect("arhiva:predmet_detail", pk=predmet.pk)


class KategorijeView(ArhivaContextMixin, LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    """Šifarnik: Lista kategorija sa rokovima čuvanja (aktivna verzija ili izabrana)."""

    template_name = "arhiva/kategorije.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        verzije = VerzijaListe.objects.all()
        verzija = verzije.filter(pk=g.get("verzija")).first() if (g.get("verzija") or "").isdigit() else None
        verzija = verzija or verzije.filter(aktivna=True).first() or verzije.first()
        qs = Kategorija.objects.filter(verzija=verzija).select_related("grupa", "duplikat_od") if verzija else Kategorija.objects.none()
        for rec in (g.get("q") or "").split():
            qs = qs.filter(naziv__icontains=rec)
        rok = g.get("rok", "")
        if rok == "trajno":
            qs = qs.filter(trajno=True, operativno=False)
        elif rok == "operativno":
            qs = qs.filter(operativno=True)
        elif rok == "godine":
            qs = qs.filter(trajno=False, rok_godina__isnull=False)
        elif rok == "uslov":
            qs = qs.exclude(pocetak_roka=Kategorija.PocetakRoka.ZAVRSETAK_PREDMETA)
        if (g.get("grupa") or "").isdigit():
            qs = qs.filter(grupa_id=g["grupa"])
        ctx.update(title="Lista kategorija", verzija=verzija, verzije=verzije, kategorije=qs.order_by("redni_broj"),
                   grupe=GrupaKategorija.objects.filter(verzija=verzija) if verzija else [],
                   filteri={"q": g.get("q", ""), "rok": rok, "grupa": g.get("grupa", "")})
        return ctx
