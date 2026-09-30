"""Finansije → SEF fakture: ulazne i izlazne fakture sa SEF-a, meko vezane za knjizenja po broju.

Fakture nemaju centar ni sifru posla, pa ih vidi samo obuhvat cele firme (kao sinhronizacija
Finansija). PDF se preuzima sa SEF-a pri prvom otvaranju detalja i cuva u aplikaciji; UBL se
preuzima sa SEF-a u trenutku otvaranja.
"""
import datetime
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, DateField, Q, Sum
from django.db.models.functions import Cast, Coalesce
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_POST

from core.mixins import role_permission_required, user_has_role_permission
from .access import can_view_all
from .sef_models import SefFaktura, SefPromena, SefSinhronizacija
from .services import sef as servis
from .services.sef_table import table_response, table_rows

logger = logging.getLogger(__name__)
FILTERI = ("smer", "status", "od", "do", "knjizenje", "q")
REDOSLED_STATUSA = ("New", "Seen", "ReNotified", "Sending", "Sent", "Approved", "Rejected", "Cancelled", "Storno",
                    "Paid", "Mistake", "OverDue", "Archived", "Unknown")


def _pristup(request):
    if not can_view_all(request.user):
        raise PermissionDenied("SEF fakture vidi samo obuhvat cele firme.")
    request.session["current_app"] = "finansije"


def _datum(tekst):
    try:
        return datetime.date.fromisoformat(tekst) if tekst else None
    except ValueError:
        return None


def _sa_datumom(qs):
    """Datum dokumenta: izdavanje (izlazne), inace promet, inace dan slanja na SEF (ulazne nemaju datum izdavanja)."""
    return qs.annotate(datum_dok=Coalesce("datum_izdavanja", "datum_prometa", Cast("datum_slanja", DateField())))


def _filtriraj(g, qs, bez=()):
    """Primena filtera; `bez` izostavlja filtere (za brojeve na dugmadima smera)."""
    if "smer" not in bez and g.get("smer") in SefFaktura.Smer.values:
        qs = qs.filter(smer=g["smer"])
    if g.get("status"):
        qs = qs.filter(status=g["status"])
    od, do = _datum(g.get("od")), _datum(g.get("do"))
    if od:
        qs = qs.filter(datum_dok__gte=od)
    if do:
        qs = qs.filter(datum_dok__lte=do)
    if g.get("knjizenje") == "da":
        qs = qs.filter(servis.q_proknjizena())
    elif g.get("knjizenje") == "ne":
        qs = qs.exclude(servis.q_proknjizena())
    for rec in (g.get("q") or "").split():
        uslov = Q(broj__icontains=rec) | Q(partner_naziv__icontains=rec) | Q(partner_pib=rec) | Q(partner_mb=rec)
        if rec.isdigit():
            uslov |= Q(sef_id=int(rec))
        qs = qs.filter(uslov)
    return qs


def _statusi():
    postoje = set(SefFaktura.objects.exclude(status="").values_list("status", flat=True).distinct())
    return [s for s in REDOSLED_STATUSA if s in postoje] + sorted(postoje - set(REDOSLED_STATUSA))


@require_GET
@login_required
@role_permission_required("finansije:sef_list")
def sef_list(request):
    _pristup(request)
    g = request.GET
    sve = _sa_datumom(SefFaktura.objects.all())
    qs = _filtriraj(g, sve)
    params = urlencode({k: g[k] for k in FILTERI if g.get(k)})
    if "draw" in g:
        return table_response(request, qs, params)
    strana = Paginator(qs.order_by("-datum_dok", "-datum_slanja", "-sef_id"), 100).get_page(g.get("page"))
    redovi = table_rows(request.user, strana.object_list, params)
    po_smeru = dict(_filtriraj(g, sve, bez=("smer",)).values_list("smer").order_by().annotate(n=Count("pk")))
    filteri = {k: g.get(k, "") for k in FILTERI}
    osnova = {k: v for k, v in filteri.items() if v and k != "smer"}
    danas = timezone.localdate()
    pocetak_meseca = danas.replace(day=1)
    kraj_proslog = pocetak_meseca - datetime.timedelta(days=1)
    oznake = {
        "q": f"Pretraga: {filteri['q']}",
        "status": f"Status: {servis.STATUSI.get(filteri['status'], filteri['status'])}",
        "knjizenje": {"da": "Proknjižene", "ne": "Neproknjižene"}.get(filteri["knjizenje"], filteri["knjizenje"]),
    }
    for kljuc, naziv in (("od", "Od"), ("do", "Do")):
        datum = _datum(filteri[kljuc])
        oznake[kljuc] = f"{naziv}: {datum.strftime('%d.%m.%Y.') if datum else filteri[kljuc]}"
    return render(request, "finansije/sef/list.html", {
        "title": "SEF fakture", "page_obj": strana, "zbir": qs.aggregate(broj=Count("pk"), iznos=Sum("iznos")),
        "table_rows": redovi,
        "params": urlencode({k: v for k, v in filteri.items() if v}), "filteri": filteri,
        "aktivnih_filtera": sum(1 for k, v in filteri.items() if v and k != "smer"),
        "smerovi": [(vrednost, naziv, po_smeru.get(vrednost, 0) if vrednost else sum(po_smeru.values()),
                     "?" + urlencode({**osnova, **({"smer": vrednost} if vrednost else {})}))
                    for vrednost, naziv in (("", "Sve"), ("ulazna", "Ulazne"), ("izlazna", "Izlazne"))],
        "periodi": [("Svi periodi", "?" + urlencode({k: v for k, v in filteri.items() if v and k not in ("od", "do")}),
                     not filteri["od"] and not filteri["do"])] + [
            (naziv, "?" + urlencode({**{k: v for k, v in filteri.items() if v and k not in ("od", "do")},
                                    "od": od.isoformat(), "do": do.isoformat()}),
             filteri["od"] == od.isoformat() and filteri["do"] == do.isoformat())
            for naziv, od, do in (("Ovaj mesec", pocetak_meseca, danas),
                                  ("Prošli mesec", kraj_proslog.replace(day=1), kraj_proslog),
                                  ("Ova godina", danas.replace(month=1, day=1), danas))],
        "ponisti": "?" + urlencode({"smer": filteri["smer"]}) if filteri["smer"] else "?",
        "aktivne_oznake": [(oznake[k], "?" + urlencode({ime: v for ime, v in filteri.items() if v and ime != k}))
                           for k in ("q", "status", "knjizenje", "od", "do") if filteri[k]],
        "sync_od": (danas - datetime.timedelta(days=7)).isoformat(), "sync_do": danas.isoformat(),
        "statusi": _statusi(), "nazivi_statusa": servis.STATUSI, "vrste": servis.VRSTE,
        "poslednja": SefSinhronizacija.objects.select_related("korisnik").first(),
        "podesen": bool(settings.SEF_API_KEY),
        "can_sync": user_has_role_permission(request.user, "finansije:sef_sync"),
    })


@require_GET
@login_required
@role_permission_required("finansije:sef_detail")
def sef_detail(request, pk):
    _pristup(request)
    faktura = get_object_or_404(SefFaktura, pk=pk)
    nazad = request.GET.get("nazad", "")
    if not nazad.startswith("?"):
        nazad = ""
    return render(request, "finansije/sef/detail.html", {
        "title": f"SEF · {faktura.broj or faktura.sef_id}", "f": faktura,
        "knjizenja": servis.knjizenja(faktura)[:200],
        "promene": SefPromena.objects.filter(smer=faktura.smer, sef_id=faktura.sef_id),
        "istog_broja": SefFaktura.objects.filter(broj_kljuc=faktura.broj_kljuc).exclude(pk=faktura.pk)
        if faktura.broj_kljuc else SefFaktura.objects.none(),
        "nazivi_statusa": servis.STATUSI, "vrste": servis.VRSTE,
        "can_file": user_has_role_permission(request.user, "finansije:sef_dokument"),
        "podesen": bool(settings.SEF_API_KEY), "nazad": nazad,
    })


def _ime_fajla(faktura, nastavak):
    ime = "".join(z if z.isalnum() or z in "-_" else "_" for z in (faktura.broj or str(faktura.sef_id)))
    return f"SEF_{ime}.{nastavak}"


@xframe_options_sameorigin
@require_GET
@login_required
@role_permission_required("finansije:sef_dokument")
def sef_dokument(request, pk, vrsta):
    """PDF (sacuvan u aplikaciji; ako nije, preuzima se sada) ili UBL (sa SEF-a u trenutku otvaranja)."""
    _pristup(request)
    faktura = get_object_or_404(SefFaktura, pk=pk)
    if vrsta not in ("pdf", "ubl"):
        raise Http404
    try:
        if vrsta == "pdf":
            spreman, poruka = servis.preuzmi_pdf(faktura)
            if not spreman:
                messages.info(request, poruka)
                return redirect("finansije:sef_detail", pk=faktura.pk)
            try:
                fajl = faktura.pdf.open("rb")
            except FileNotFoundError:
                raise Http404("PDF fakture nije pronađen.")
            odgovor = FileResponse(fajl, content_type="application/pdf")
            odgovor["Content-Disposition"] = f'inline; filename="{_ime_fajla(faktura, "pdf")}"'
            return odgovor
        sadrzaj = servis.Klijent().ubl(faktura.smer, faktura.sef_id)
    except (servis.SefNijePodesen, servis.SefGreska) as exc:
        messages.error(request, str(exc))
        return redirect("finansije:sef_detail", pk=faktura.pk)
    odgovor = HttpResponse(sadrzaj, content_type="application/xml")
    odgovor["Content-Disposition"] = f'attachment; filename="{_ime_fajla(faktura, "xml")}"'
    return odgovor


@require_POST
@login_required
@role_permission_required("finansije:sef_dokument")
def sef_pdf_preuzmi(request, pk):
    """Za detalj: preuzima PDF sa SEF-a u pozadini. `priprema` znaci da ga SEF jos pravi — stranica ponavlja."""
    _pristup(request)
    faktura = get_object_or_404(SefFaktura, pk=pk)
    try:
        spreman, poruka = servis.preuzmi_pdf(faktura)
    except (servis.SefNijePodesen, servis.SefGreska) as exc:
        return JsonResponse({"status": "greska", "poruka": str(exc)}, status=502)
    if not spreman:
        return JsonResponse({"status": "priprema", "poruka": poruka})
    return JsonResponse({"status": "ok", "url": reverse("finansije:sef_dokument", args=[faktura.pk, "pdf"]),
                         "preuzet": timezone.localtime(faktura.pdf_preuzet).strftime("%d.%m.%Y. %H:%M")})


@require_POST
@login_required
@role_permission_required("finansije:sef_sync")
def sef_sync(request):
    _pristup(request)
    nazad = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(nazad, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        nazad = ""
    nazad = nazad or "finansije:sef_list"
    danas = timezone.localdate()
    od = _datum(request.POST.get("od")) or danas - datetime.timedelta(days=7)
    do = _datum(request.POST.get("do")) or danas
    if (do - od).days > 92:
        messages.error(request, "Ručno se preuzima najviše tri meseca odjednom. Za duži period: manage.py sync_sef.")
        return redirect(nazad)
    try:
        run = servis.sinhronizuj(od, do, korisnik=request.user)
    except servis.SefNijePodesen as exc:
        messages.error(request, str(exc))
    except (servis.SefGreska, ValueError) as exc:
        messages.error(request, f"Preuzimanje sa SEF-a nije uspelo: {exc}")
    else:
        messages.success(request, servis.poruka(run))
    return redirect(nazad)
