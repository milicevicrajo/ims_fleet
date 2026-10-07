"""Finansije → SEF fakture: ulazne i izlazne fakture sa SEF-a, meko vezane za knjizenja po broju.

Fakture nemaju centar ni sifru posla, pa ih vidi samo obuhvat cele firme (kao sinhronizacija
Finansija). PDF se preuzima sa SEF-a pri prvom otvaranju detalja i cuva u aplikaciji; UBL se
preuzima sa SEF-a u trenutku otvaranja.
"""
import calendar
import datetime
import logging
import tempfile
import threading
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_POST

from core.mixins import role_permission_required, user_has_role_permission
from .access import can_view_all
from .sef_models import SefFaktura, SefPrilog, SefPromena, SefSinhronizacija
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


_sa_datumom = servis.sa_datumom


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
        "aktivno_preuzimanje": _aktivno(),
        "statusi": _statusi(), "nazivi_statusa": servis.STATUSI, "vrste": servis.VRSTE,
        "poslednja": SefSinhronizacija.objects.select_related("korisnik").first(),
        "podesen": bool(settings.SEF_API_KEY),
        "can_sync": user_has_role_permission(request.user, "finansije:sef_sync"),
        "can_izvoz": user_has_role_permission(request.user, "finansije:sef_izvoz"),
        "godine": sorted({d.year for d in _sa_datumom(SefFaktura.objects.all()).values_list("datum_dok", flat=True)
                          .distinct() if d} or {danas.year}, reverse=True),
        "meseci": list(enumerate(MESECI, start=1)), "danas": danas,
        "pdf_stanje": qs.aggregate(ukupno=Count("pk"), sa_pdf=Count("pk", filter=~Q(pdf=""))),
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
    can_file = user_has_role_permission(request.user, "finansije:sef_dokument")
    prilozi, prilozi_greska = servis.prilozi_fakture(faktura) if can_file else ([], "")
    return render(request, "finansije/sef/detail.html", {
        "title": f"SEF · {faktura.broj or faktura.sef_id}", "f": faktura,
        "knjizenja": servis.knjizenja(faktura)[:200],
        "promene": SefPromena.objects.filter(smer=faktura.smer, sef_id=faktura.sef_id),
        "istog_broja": SefFaktura.objects.filter(broj_kljuc=faktura.broj_kljuc).exclude(pk=faktura.pk)
        if faktura.broj_kljuc else SefFaktura.objects.none(),
        "nazivi_statusa": servis.STATUSI, "vrste": servis.VRSTE,
        "can_file": can_file,
        "podesen": bool(settings.SEF_API_KEY), "nazad": nazad,
        "prilozi": prilozi, "prilozi_greska": prilozi_greska,
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


@xframe_options_sameorigin
@require_GET
@login_required
@role_permission_required("finansije:sef_dokument")
def sef_prilog(request, pk, redni):
    """Pridruzeni dokument fakture (sacuvan u aplikaciji pri preuzimanju ili prvom otvaranju detalja)."""
    _pristup(request)
    return servis.prilog_odgovor(get_object_or_404(SefPrilog, faktura_id=pk, redni=redni))


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


MESECI = ("januar", "februar", "mart", "april", "maj", "jun", "jul", "avgust", "septembar", "oktobar", "novembar",
          "decembar")


def _period_izvoza(g):
    """(od, do, oznaka) za godinu i, ako je izabran, mesec; None ako godina nije ispravna."""
    try:
        godina = int(g.get("godina", ""))
        mesec = int(g["mesec"]) if g.get("mesec") else None
    except (TypeError, ValueError):
        return None
    if not 2020 <= godina <= 2100 or (mesec is not None and not 1 <= mesec <= 12):
        return None
    if mesec:
        return (datetime.date(godina, mesec, 1), datetime.date(godina, mesec, calendar.monthrange(godina, mesec)[1]),
                f"{godina}-{mesec:02d}")
    return datetime.date(godina, 1, 1), datetime.date(godina, 12, 31), str(godina)


def _fakture_perioda(g):
    period = _period_izvoza(g)
    if period is None:
        return None, None
    od, do, oznaka = period
    qs = _sa_datumom(SefFaktura.objects.all()).filter(datum_dok__gte=od, datum_dok__lte=do)
    if g.get("smer") in SefFaktura.Smer.values:
        qs = qs.filter(smer=g["smer"])
    return qs, (od, do, oznaka)


@require_GET
@login_required
@role_permission_required("finansije:sef_izvoz")
def sef_izvoz(request):
    """ZIP PDF-ova i priloga za mesec ili godinu (uz spisak svih faktura perioda i oznaku koje nemaju PDF)."""
    _pristup(request)
    qs, period = _fakture_perioda(request.GET)
    if qs is None:
        messages.error(request, "Izaberite godinu (i po želji mesec) za izvoz.")
        return redirect("finansije:sef_list")
    od, do, oznaka = period
    fajl = tempfile.TemporaryFile()
    broj, sa_pdf = servis.izvoz_zip(qs.order_by("smer", "datum_dok", "broj", "sef_id").prefetch_related("prilozi"), fajl)
    if not broj:
        fajl.close()
        messages.info(request, f"Za period {oznaka} nema faktura.")
        return redirect("finansije:sef_list")
    fajl.seek(0)
    smer = request.GET.get("smer") if request.GET.get("smer") in SefFaktura.Smer.values else "sve"
    odgovor = FileResponse(fajl, as_attachment=True, filename=f"SEF_{smer}_{oznaka}.zip", content_type="application/zip")
    odgovor["X-SEF-Faktura"], odgovor["X-SEF-PDF"] = str(broj), str(sa_pdf)
    return odgovor


PREKID_BEZ_JAVLJANJA = datetime.timedelta(minutes=2)


def pokreni(fn):
    """Pozadinska nit web procesa (bez Celery-ja); u testovima se zamenjuje neposrednim pozivom."""
    def _nit():
        from django.db import connection

        try:
            fn()
        except Exception:  # greska je vec upisana u zapis sinhronizacije
            logger.exception("SEF rucno preuzimanje nije uspelo")
        finally:
            connection.close()

    threading.Thread(target=_nit, name="sef-preuzimanje", daemon=True).start()


def _aktivno():
    """Preuzimanje u toku koje se javilo u poslednja 2 min; tiho „u toku” (restart servera) se zatvara."""
    for run in SefSinhronizacija.objects.filter(status="running"):
        javljeno = run.counts.get("napredak", {}).get("azurirano")
        poslednje = datetime.datetime.fromisoformat(javljeno) if javljeno else run.started_at
        if timezone.now() - poslednje > PREKID_BEZ_JAVLJANJA:
            run.status, run.finished_at = "error", timezone.now()
            run.error = ("Prekinuto: preuzimanje je prestalo da radi (restart servera ili prekid veze). "
                         "Pokrenite ga ponovo — nastavlja gde je stalo, bez duplikata.")
            run.save(update_fields=["status", "error", "finished_at"])
            continue
        return run
    return None


def _tisina(napredak, run):
    """Sekundi od poslednjeg javljanja preuzimanja."""
    javljeno = napredak.get("azurirano")
    poslednje = datetime.datetime.fromisoformat(javljeno) if javljeno else run.started_at
    return round((timezone.now() - poslednje).total_seconds())


def _stanje(run):
    napredak = run.counts.get("napredak", {})
    return {
        "id": run.pk, "status": run.status, "od": f"{run.od:%d.%m.%Y.}", "do": f"{run.do:%d.%m.%Y.}",
        "faza": napredak.get("faza", ""), "redni": napredak.get("redni", 0), "faza_ukupno": napredak.get("faza_ukupno", 5),
        "obradjeno": napredak.get("obradjeno", 0), "ukupno": napredak.get("ukupno", 0),
        "preostalo_s": napredak.get("preostalo_s"), "proteklo_s": napredak.get("proteklo_s"),
        "tisina_s": _tisina(napredak, run) if run.status == "running" else None,
        "procena": run.counts.get("procena"),
        "poruka": servis.poruka(run) if run.status in ("success", "stopped") else "",
        "greska": run.error if run.status in ("error", "stopped") else "",
        "status_naziv": run.get_status_display(), "zaustavljanje": run.zaustavi and run.status == "running",
        "pokrenuto": timezone.localtime(run.started_at).strftime("%d.%m.%Y. %H:%M"),
        "pokrenuo": run.korisnik.get_username() if run.korisnik_id else "noćni posao",
        "dnevnik": napredak.get("dnevnik", []),
        "stanje_url": reverse("finansije:sef_sync_stanje", args=[run.pk]),
        "zaustavi_url": reverse("finansije:sef_sync_zaustavi", args=[run.pk]),
    }


@require_POST
@login_required
@role_permission_required("finansije:sef_sync")
def sef_sync(request):
    """Pokrece preuzimanje sa SEF-a odmah (pozadinska nit web procesa) i vraca stanje za modal."""
    _pristup(request)
    danas = timezone.localdate()
    od = _datum(request.POST.get("od")) or danas - datetime.timedelta(days=7)
    do = _datum(request.POST.get("do")) or danas
    greska = ""
    if od > do:
        greska = "Datum od je posle datuma do."
    elif do > danas:
        greska = "Datum do ne može biti u budućnosti."
    elif not settings.SEF_API_KEY:
        greska = "SEF nije podešen: u .env nedostaje SEF_API_KEY."
    if greska:
        return JsonResponse({"greska": greska}, status=400)
    aktivno = _aktivno()
    if aktivno is not None:  # jedno preuzimanje u isto vreme — prikazuje se ono koje vec radi
        return JsonResponse({**_stanje(aktivno), "vec_u_toku": True})
    run = servis.zapocni(od, do, korisnik=request.user, danas=danas)
    pokreni(lambda: servis.sinhronizuj(korisnik=request.user, danas=danas, run=run))
    return JsonResponse(_stanje(run))


@require_GET
@login_required
@role_permission_required("finansije:sef_sync")
def sef_sync_poslednje(request):
    """Status za dugme „Status preuzimanja”: preuzimanje u toku, inace poslednje (ili nista)."""
    _pristup(request)
    run = _aktivno() or SefSinhronizacija.objects.select_related("korisnik").first()
    return JsonResponse(_stanje(run) if run else {"status": "nema"})


@require_POST
@login_required
@role_permission_required("finansije:sef_sync")
def sef_sync_zaustavi(request, pk):
    """Zahtev za zaustavljanje: preuzimanje staje posle koraka koji upravo radi (najviše nekoliko sekundi)."""
    _pristup(request)
    SefSinhronizacija.objects.filter(pk=pk, status="running").update(zaustavi=True)
    return JsonResponse(_stanje(get_object_or_404(SefSinhronizacija, pk=pk)))


@require_GET
@login_required
@role_permission_required("finansije:sef_sync")
def sef_sync_stanje(request, pk):
    _pristup(request)
    _aktivno()  # zatvara zaboravljeno „u toku”
    return JsonResponse(_stanje(get_object_or_404(SefSinhronizacija, pk=pk)))
