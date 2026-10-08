"""Knjiženje → Fiskalni računi (od 07.10.2026.): računi koje su Isplate poslale na knjiženje.

Spisak (DataTables, strana sa servera — isti URL uz `draw`), knjiženje označenih računa pod istim datumom i
nalogom za knjiženje, detalj računa sa istorijom, vraćanje na doradu i poništavanje knjiženja.
Dozvole su samo za ulogu Knjiženje (i Upravu); Isplate ih nemaju.
"""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import escape, format_html
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.exporting import rows_to_xlsx_response
from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from isplate import tabela
from nabavka.services import fiskalni
from nabavka.views.fiskalni import _iznos

from . import services
from .models import KnjizenjeRacuna

Status = KnjizenjeRacuna.Status
SIDEBAR = "sidebar_knjizenje.html"


class ProknjiziForm(forms.Form):
    datum = forms.DateField(label="Datum knjiženja", widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    broj_naloga = forms.CharField(label="Broj naloga za knjiženje", required=False, max_length=50,
                                  widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    napomena = forms.CharField(label="Napomena", required=False, max_length=500,
                               widget=forms.TextInput(attrs={"class": "form-control"}))


def _ko(korisnik):
    return (korisnik.get_full_name() or korisnik.get_username()) if korisnik else ""


def _racuni():
    return services.racuni_knjizenja().select_related(
        "knjizenje", "knjizenje__poslao", "knjizenje__knjizio", "knjizenje__vratio", "putni_nalog",
        "putni_nalog__employee", "putni_nalog__vehicle", "putni_nalog__job_code", "job_code", "proknjizio", "created_by")


def filtriraj(qs, g):
    status = g.get("status", "ceka")
    if status == "ceka":
        qs = qs.filter(knjizenje__status=Status.POSLATO, proknjizeno=False)
    elif status == "vraceno":
        qs = qs.filter(knjizenje__status=Status.VRACENO, proknjizeno=False)
    elif status == "proknjizeno":
        qs = qs.filter(proknjizeno=True)
    if g.get("vrsta") == "nalog":
        qs = qs.filter(putni_nalog__isnull=False)
    elif g.get("vrsta") == "ostali":
        qs = qs.filter(putni_nalog__isnull=True)
    od, do = parse_date(g.get("od") or ""), parse_date(g.get("do") or "")
    if od:
        qs = qs.filter(pfr_vreme__date__gte=od)
    if do:
        qs = qs.filter(pfr_vreme__date__lte=do)
    kod, kdo = parse_date(g.get("knjizeno_od") or ""), parse_date(g.get("knjizeno_do") or "")
    if kod:
        qs = qs.filter(knjizenje__datum_knjizenja__gte=kod)
    if kdo:
        qs = qs.filter(knjizenje__datum_knjizenja__lte=kdo)
    for rec in tabela.reci(g):
        qs = qs.filter(Q(broj_racuna__icontains=rec) | Q(naziv_prodavca__icontains=rec) | Q(pib_prodavca=rec)
                       | Q(napomena__icontains=rec) | Q(interni_broj__icontains=rec) | Q(job_code__code__icontains=rec)
                       | Q(putni_nalog__order_number__icontains=rec) | Q(putni_nalog__employee__last_name__icontains=rec)
                       | Q(knjizenje__broj_naloga__icontains=rec))
    return qs


def _zbir(qs):
    zbir = qs.aggregate(broj=Count("pk"), iznos=Sum("iznos"), pdv=Sum("pdv_ukupno"))
    return {"broj": zbir["broj"], "iznos": _iznos(zbir["iznos"] or 0), "pdv": _iznos(zbir["pdv"] or 0)}


def _filteri(g):
    return {k: g.get(k, "") for k in ("q", "vrsta", "od", "do", "knjizeno_od", "knjizeno_do")} | {"status": g.get("status", "ceka")}


def _status_html(r):
    z = services.zapis(r)
    st = services.stanje(r)
    if st == Status.PROKNJIZENO:
        detalji = " · ".join(d for d in (
            f"{z.datum_knjizenja:%d.%m.%Y.}" if z and z.datum_knjizenja else "",
            f"nalog {z.broj_naloga}" if z and z.broj_naloga else "",
            _ko(z.knjizio if z else r.proknjizio)) if d)
        return format_html('<span class="isp-badge ok"><i class="mdi mdi-check-decagram" aria-hidden="true"></i> Proknjiženo</span>'
                           '<div class="isp-small">{}</div>', detalji)
    if st == Status.VRACENO:
        return format_html('<span class="isp-badge warn" title="{}"><i class="mdi mdi-undo" aria-hidden="true"></i> Vraćeno na doradu</span>'
                           '<div class="isp-small">{}</div>', z.razlog_vracanja, z.razlog_vracanja)
    return format_html('<span class="isp-badge info"><i class="mdi mdi-timer-sand" aria-hidden="true"></i> Čeka knjiženje</span>')


def _veza(r):
    if r.putni_nalog_id:
        pn = r.putni_nalog
        detalji = " · ".join(d for d in (str(pn.employee or pn.other_employee_name or ""), pn.travel_location or "") if d)
        return format_html('<span class="isp-badge muted">Putni nalog</span> <strong>{}</strong><div class="isp-small">{}</div>',
                           pn.order_number, detalji)
    return format_html('<span class="isp-badge muted">Ostali račun</span><div class="isp-small">{}</div>', r.napomena or "")


class RacuniView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "knjizenje/racuni.html"
    KOLONE = {"1": "pfr_vreme", "2": "naziv_prodavca", "3": "broj_racuna", "4": "iznos", "6": "job_code__code",
              "7": "knjizenje__poslato_at", "8": "knjizenje__datum_knjizenja"}

    def get(self, request, *args, **kwargs):
        if tabela.je_zahtev_tabele(request):
            return self.podaci(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g, user = self.request.GET, self.request.user
        sve = services.racuni_knjizenja()
        danas = timezone.localdate()
        ctx.update(
            title="Knjiženje fiskalnih računa", sidebar_template=SIDEBAR, filteri=_filteri(g),
            zbir=_zbir(filtriraj(sve, g)),
            plocice={
                "ceka": _zbir(sve.filter(knjizenje__status=Status.POSLATO, proknjizeno=False)),
                "vraceno": _zbir(sve.filter(knjizenje__status=Status.VRACENO, proknjizeno=False)),
                "mesec": _zbir(sve.filter(proknjizeno=True, knjizenje__datum_knjizenja__year=danas.year,
                                          knjizenje__datum_knjizenja__month=danas.month)),
            },
            moze_knjiziti=user_has_role_permission(user, "knjizenje:proknjizi"),
            moze_izvoz=user_has_role_permission(user, "knjizenje:izvoz"),
            forma=ProknjiziForm(initial={"datum": danas}),
        )
        return ctx

    def podaci(self, request):
        g = request.GET
        sve = services.racuni_knjizenja()
        qs = filtriraj(_racuni(), g)
        start, duzina, draw = tabela.strana(g)
        strana = list(qs.order_by(tabela.redosled(g, self.KOLONE, "pfr_vreme"), "-pk")[start:start + duzina])
        knjizi = user_has_role_permission(request.user, "knjizenje:proknjizi")
        return tabela.odgovor(draw, sve.count(), qs.count(), [self._red(r, knjizi) for r in strana], zbir=_zbir(qs))

    @staticmethod
    def _red(r, knjizi):
        z = services.zapis(r)
        ceka = services.stanje(r) == Status.POSLATO
        izbor = (format_html('<input type="checkbox" class="form-check-input knj-izbor" value="{}" aria-label="Izaberi račun {}">',
                             r.pk, r.broj_racuna) if knjizi and ceka else "")
        broj = format_html('<a href="{}">{}</a>', reverse("knjizenje:racun", args=[r.pk]), r.broj_racuna)
        if r.interni_broj:
            broj += format_html('<div class="isp-small">interni br. {}</div>', r.interni_broj)
        pdv = f'<div class="isp-small">PDV {_iznos(r.pdv_ukupno)}</div>' if r.pdv_ukupno is not None else ""
        return {
            "DT_RowClass": "isp-proknjizen" if r.proknjizeno else "",
            "izbor": izbor,
            "vreme": f"{timezone.localtime(r.pfr_vreme):%d.%m.%Y.}<div class=\"isp-small\">{timezone.localtime(r.pfr_vreme):%H:%M}</div>",
            "prodavac": (f'<span title="{escape(r.naziv_prodavca or "")}">{escape(r.naziv_prodavca or "—")}</span>'
                         f'<div class="isp-small">PIB {escape(r.pib_prodavca or "—")}</div>'),
            "broj": broj,
            "iznos": f"<strong>{_iznos(r.iznos)}</strong>{pdv}",
            "veza": _veza(r),
            "sifra": escape(r.job_code.code if r.job_code_id else "—"),
            "poslao": (format_html('{}<div class="isp-small">{}</div>', _ko(z.poslao),
                                   f"{timezone.localtime(z.poslato_at):%d.%m.%Y. %H:%M}" if z.poslato_at else "")
                       if z and z.poslato_at else "—"),
            "status": _status_html(r),
        }


@login_required
@require_POST
@role_permission_required()
def proknjizi(request):
    """Knjiži označene račune (spisak) ili jedan račun (detalj) pod istim datumom i nalogom za knjiženje."""
    forma = ProknjiziForm(request.POST)
    ids = [i for i in request.POST.getlist("racuni") if i.isdigit()]
    nazad = request.POST.get("nazad") or reverse("knjizenje:racuni")
    if not nazad.startswith("/"):
        nazad = reverse("knjizenje:racuni")
    if not forma.is_valid():
        messages.error(request, "Upišite ispravan datum knjiženja.")
        return redirect(nazad)
    racuni = list(_racuni().filter(pk__in=ids))
    try:
        broj = services.proknjizi(racuni, request.user, forma.cleaned_data["datum"], forma.cleaned_data["broj_naloga"],
                                  forma.cleaned_data["napomena"])
    except services.GreskaKnjizenja as exc:
        messages.error(request, str(exc))
        return redirect(nazad)
    messages.success(request, f"Proknjiženo računa: {broj}." if broj > 1 else f"Račun {racuni[0].broj_racuna} je proknjižen.")
    return redirect(nazad)


def _racun_ili_404(pk):
    return get_object_or_404(_racuni().prefetch_related("stavke"), pk=pk)


@login_required
@role_permission_required()
def racun(request, pk):
    r = _racun_ili_404(pk)
    user = request.user
    st = services.stanje(r)
    z = services.zapis(r)
    return render(request, "knjizenje/racun.html", {
        "title": f"Knjiženje · {r.broj_racuna}", "sidebar_template": SIDEBAR, "racun": r, "z": z, "stanje": st,
        # Isti podaci o računu kao u Isplatama i Nabavci (podaci, stavke, tekst računa, upozorenja).
        "upozorenja": fiskalni.upozorenja(r),
        "dogadjaji": list(z.dogadjaji.select_related("korisnik")) if z else [],
        "moze_knjiziti": st == Status.POSLATO and user_has_role_permission(user, "knjizenje:proknjizi"),
        "moze_vratiti": st == Status.POSLATO and user_has_role_permission(user, "knjizenje:vrati"),
        "moze_ponistiti": st == Status.PROKNJIZENO and user_has_role_permission(user, "knjizenje:ponisti"),
        "forma": ProknjiziForm(initial={"datum": timezone.localdate()}),
    })


@login_required
@require_POST
@role_permission_required()
def vrati(request, pk):
    r = _racun_ili_404(pk)
    try:
        services.vrati_na_doradu(r, request.user, request.POST.get("razlog"), request=request)
    except services.GreskaKnjizenja as exc:
        messages.error(request, str(exc))
        return redirect("knjizenje:racun", pk=r.pk)
    messages.success(request, f"Račun {r.broj_racuna} je vraćen Isplatama na doradu.")
    return redirect("knjizenje:racuni")


@login_required
@require_POST
@role_permission_required()
def ponisti(request, pk):
    r = _racun_ili_404(pk)
    try:
        services.ponisti(r, request.user, request.POST.get("razlog"), request=request)
    except services.GreskaKnjizenja as exc:
        messages.error(request, str(exc))
        return redirect("knjizenje:racun", pk=r.pk)
    messages.success(request, f"Knjiženje računa {r.broj_racuna} je poništeno; račun ponovo čeka knjiženje.")
    return redirect("knjizenje:racun", pk=r.pk)


@login_required
@role_permission_required()
def izvoz(request):
    qs = filtriraj(_racuni(), request.GET).order_by("pfr_vreme", "pk")
    zaglavlje = ["Vreme računa", "Prodavac", "PIB prodavca", "Broj računa", "Interni broj", "Iznos", "PDV", "Vrsta",
                 "Putni nalog", "Zaposleni", "Napomena", "Šifra posla", "Status", "Poslao", "Poslato", "Datum knjiženja",
                 "Broj naloga za knjiženje", "Napomena knjiženja", "Proknjižio", "Razlog vraćanja"]
    redovi = []
    for r in qs:
        z = services.zapis(r)
        pn = r.putni_nalog
        st = services.stanje(r)
        redovi.append([
            timezone.localtime(r.pfr_vreme).strftime("%d.%m.%Y %H:%M"), r.naziv_prodavca, r.pib_prodavca, r.broj_racuna,
            r.interni_broj, float(r.iznos), float(r.pdv_ukupno) if r.pdv_ukupno is not None else None,
            "Putni nalog" if pn else "Ostali", pn.order_number if pn else "",
            str(pn.employee or pn.other_employee_name or "") if pn else "", r.napomena,
            r.job_code.code if r.job_code_id else "", str(Status(st).label) if st else "",
            _ko(z.poslao) if z else "", timezone.localtime(z.poslato_at).strftime("%d.%m.%Y %H:%M") if z and z.poslato_at else "",
            z.datum_knjizenja.strftime("%d.%m.%Y") if z and z.datum_knjizenja else "", z.broj_naloga if z else "",
            z.napomena if z else "", _ko(z.knjizio if z and z.knjizio_id else r.proknjizio),
            z.razlog_vracanja if z and st == Status.VRACENO else "",
        ])
    return rows_to_xlsx_response(f"Knjizenje-fiskalnih-racuna-{timezone.localdate():%Y%m%d}.xlsx",
                                 "Knjiženje", zaglavlje, redovi, bold_header=True, auto_width=True)
