"""Isplate → Putni nalozi – pravdanje (od 02.10.2026.).

Pri pravdanju putnog naloga dodaju se fiskalni računi (čitač QR koda). Račun se čuva gde i
ostali fiskalni računi (`nabavka.FiskalniRacun`), samo je vezan za putni nalog i dobija njegovu
šifru posla; račun koji je već učitan u Nabavci se samo veže. Opravdan nalog je zaključan, pa
mu se računi više ne dodaju. Knjiženje radi `fiskalni_views` (Putni nalozi – Fiskalni računi).
Isplate rade po starim pravima: vide se svi putni nalozi, kao na ekranu isplate akontacija.
Isti prozor („Dodaj račun”) otvara se i iz naloga za isplatu (Isplata neoporezovanih), da se račun
učita u toku rada. Spisak je DataTables tabela koja stranu dobija sa servera (`tabela`).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import escape, format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from fleet.models import PutniNalog
from nabavka.models import FiskalniRacun
from nabavka.services import fiskalni
from nabavka.views.fiskalni import _iznos

from . import tabela


def putni_nalozi():
    return PutniNalog.objects.select_related("employee", "job_code")


def _filtriraj(qs, g):
    status = g.get("status", "neopravdani")
    if status == "neopravdani":
        qs = qs.filter(opravdan=False, storniran=False)
    elif status == "opravdani":
        qs = qs.filter(opravdan=True)
    od, do = parse_date(g.get("od") or ""), parse_date(g.get("do") or "")
    if od:
        qs = qs.filter(travel_date__gte=od)
    if do:
        qs = qs.filter(travel_date__lte=do)
    for rec in tabela.reci(g):
        qs = qs.filter(Q(order_number__icontains=rec) | Q(employee__last_name__icontains=rec)
                       | Q(employee__first_name__icontains=rec) | Q(other_employee_name__icontains=rec)
                       | Q(travel_location__icontains=rec) | Q(job_code__code__icontains=rec))
    return qs


def racuni_po_nalogu(ids):
    """{id naloga: {"broj", "zbir"}} za naloge na strani — jedan upit, bez GROUP BY nad nalozima."""
    return {r["putni_nalog_id"]: r for r in FiskalniRacun.objects.filter(putni_nalog_id__in=ids)
            .values("putni_nalog_id").annotate(broj=Count("pk"), zbir=Sum("iznos")).order_by()}


def dugme_racuni(putni_nalog, racuni=None):
    """Dugme koje otvara prozor sa računima naloga (isto na pravdanju i u nalozima za isplatu)."""
    broj = racuni["broj"] if racuni else 0
    if not broj and (putni_nalog.opravdan or putni_nalog.storniran):
        return mark_safe('<span class="text-muted">—</span>')
    return format_html(
        '<button type="button" class="btn btn-sm {} js-racuni-naloga text-nowrap" data-racuni="{}" data-dodaj="{}" '
        'title="Fiskalni računi putnog naloga {}"><i class="mdi mdi-qrcode-scan" aria-hidden="true"></i> '
        '<span class="js-racuni-oznaka">{}</span></button>',
        "btn-outline-success" if broj else "btn-outline-primary",
        reverse("isplate:putni_nalog_racuni", args=[putni_nalog.pk]),
        reverse("isplate:putni_nalog_racun_dodaj", args=[putni_nalog.pk]), putni_nalog.order_number,
        f"{broj} · {_iznos(racuni['zbir'] or 0)}" if broj else "Dodaj račun",
    )


def _status(n):
    if n.storniran:
        return '<span class="isp-badge warn">Storniran</span>'
    if n.opravdan:
        return '<span class="isp-badge ok"><i class="mdi mdi-lock" aria-hidden="true"></i> Opravdan</span>'
    return '<span class="isp-badge muted">Nije opravdan</span>'


class PutniNaloziPravdanjeView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "isplate/putni_nalozi_pravdanje.html"
    KOLONE = {"0": "order_number", "1": "employee__last_name", "2": "travel_date", "3": "job_code__code",
              "4": "advance_payment", "6": "opravdan"}

    def get(self, request, *args, **kwargs):
        if tabela.je_zahtev_tabele(request):
            return self.podaci(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        ctx.update(
            title="Putni nalozi – pravdanje", sidebar_template="sidebar_isplate.html",
            filteri={"q": g.get("q", ""), "od": g.get("od", ""), "do": g.get("do", ""),
                     "status": g.get("status", "neopravdani")},
        )
        return ctx

    def podaci(self, request):
        g, user = request.GET, request.user
        sve = putni_nalozi()
        qs = _filtriraj(sve, g)
        start, duzina, draw = tabela.strana(g)
        strana = list(qs.order_by(tabela.redosled(g, self.KOLONE, "travel_date"), "-pk")[start:start + duzina])
        racuni = racuni_po_nalogu([n.pk for n in strana])
        prava = {"racuni": user_has_role_permission(user, "isplate:putni_nalog_racuni"),
                 "opravdaj": user_has_role_permission(user, "isplate:putni_nalog_opravdaj")}
        return tabela.odgovor(draw, sve.count(), qs.count(), [self._red(n, racuni.get(n.pk), prava) for n in strana])

    @staticmethod
    def _red(n, racuni, prava):
        putovanje = escape(n.travel_location or "—")
        detalji = [f"{n.travel_date:%d.%m.%Y.}" if n.travel_date else "", f"{n.number_of_days} d." if n.number_of_days else ""]
        if any(detalji):
            putovanje += f'<div class="isp-small">{" · ".join(d for d in detalji if d)}</div>'
        opravdaj = ""
        if prava["opravdaj"] and not n.opravdan and not n.storniran:
            opravdaj = format_html(
                '<button type="button" class="btn btn-sm btn-outline-success js-opravdaj text-nowrap" data-url="{}" '
                'data-broj="{}"><i class="mdi mdi-check" aria-hidden="true"></i> Opravdaj</button>',
                reverse("isplate:putni_nalog_opravdaj", args=[n.pk]), n.order_number)
        return {
            "nalog": f"<strong>{escape(n.order_number)}</strong>",
            "zaposleni": escape(str(n.employee or n.other_employee_name or "—")),
            "putovanje": putovanje,
            "sifra": (f'{escape(n.job_code.code)}<div class="isp-small isp-skrati" title="{escape(n.job_code.name or "")}">'
                      f'{escape(n.job_code.name or "")}</div>'),
            "akontacija": (f'{_iznos(n.advance_payment)} <small class="text-muted">{escape(n.advance_payment_currency or "")}</small>'
                           if n.advance_payment else '<span class="text-muted">—</span>'),
            "racuni": dugme_racuni(n, racuni) if prava["racuni"] else str((racuni or {}).get("broj", 0)),
            "status": _status(n),
            "akcije": opravdaj,
        }


def _racun_json(racun, putni_nalog, moze_ukloniti):
    return {
        "id": racun.pk, "broj": racun.broj_racuna, "prodavac": racun.naziv_prodavca or racun.pib_prodavca or "—",
        "vreme": timezone.localtime(racun.pfr_vreme).strftime("%d.%m.%Y. %H:%M"), "iznos": _iznos(racun.iznos),
        "na_ims": racun.na_ims, "ceka": racun.status != racun.Status.POTVRDJEN, "proknjizeno": racun.proknjizeno,
        "sifra": racun.job_code.code, "druga_sifra": racun.job_code_id != putni_nalog.job_code_id,
        "ukloni_url": (reverse("isplate:putni_nalog_racun_ukloni", args=[putni_nalog.pk, racun.pk])
                       if moze_ukloniti and not racun.proknjizeno and not putni_nalog.opravdan else ""),
    }


@login_required
@role_permission_required()
def putni_nalog_racuni(request, pk):
    """Računi naloga za prozor „Dodaj račun” (JSON)."""
    putni_nalog = get_object_or_404(putni_nalozi(), pk=pk)
    moze_ukloniti = user_has_role_permission(request.user, "isplate:putni_nalog_racun_ukloni")
    racuni = putni_nalog.fiskalni_racuni.select_related("job_code").order_by("pfr_vreme", "pk")
    zbir = racuni.aggregate(iznos=Sum("iznos"))["iznos"]
    return JsonResponse({
        "nalog": putni_nalog.order_number, "sifra": putni_nalog.job_code.code, "sifra_naziv": putni_nalog.job_code.name,
        "zaposleni": str(putni_nalog.employee or putni_nalog.other_employee_name or ""),
        "putovanje": f"{putni_nalog.travel_location} · {putni_nalog.travel_date:%d.%m.%Y.}",
        "zakljucan": putni_nalog.opravdan or putni_nalog.storniran,
        "moze_dodati": user_has_role_permission(request.user, "isplate:putni_nalog_racun_dodaj"),
        "racuni": [_racun_json(r, putni_nalog, moze_ukloniti) for r in racuni],
        "zbir": _iznos(zbir) if zbir is not None else "0,00",
    })


@login_required
@require_POST
@role_permission_required()
def putni_nalog_racun_dodaj(request, pk):
    """Očitan link sa QR koda → račun vezan za putni nalog (JSON za prozor)."""
    putni_nalog = get_object_or_404(putni_nalozi(), pk=pk)
    if putni_nalog.opravdan:
        return JsonResponse({"ok": False, "poruka": f"Putni nalog {putni_nalog.order_number} je opravdan i zaključan."},
                            status=400)
    link = (request.POST.get("link") or "").strip()
    if not link:
        return JsonResponse({"ok": False, "poruka": "Očitajte QR kod računa."}, status=400)
    try:
        racun, upozorenja, vezan = fiskalni.ucitaj_za_putni_nalog(link, putni_nalog, request.user,
                                                                   (request.POST.get("napomena") or "").strip()[:500],
                                                                   ocekivano=fiskalni.ocekivano_iz_zahteva(request.POST))
    except fiskalni.GreskaOcitavanja as exc:
        return JsonResponse({"ok": False, "poruka": str(exc)}, status=400)
    return JsonResponse({
        "ok": True, "vezan_postojeci": vezan, "upozorenja": list(upozorenja), "broj": racun.broj_racuna,
        "prodavac": racun.naziv_prodavca or racun.pib_prodavca, "iznos": _iznos(racun.iznos),
        "poruka": (f"Račun {racun.broj_racuna} je već bio učitan; vezan je za ovaj putni nalog i zadržava svoju šifru posla."
                   if vezan else f"Račun {racun.broj_racuna} je dodat na šifru posla {putni_nalog.job_code.code}."),
    })


@login_required
@require_POST
@role_permission_required()
def putni_nalog_racun_ukloni(request, pk, racun_pk):
    """Skida pogrešno skeniran račun sa naloga (dok nalog nije opravdan i račun nije proknjižen)."""
    putni_nalog = get_object_or_404(putni_nalozi(), pk=pk)
    racun = get_object_or_404(putni_nalog.fiskalni_racuni, pk=racun_pk)
    if putni_nalog.opravdan:
        return JsonResponse({"ok": False, "poruka": "Putni nalog je opravdan i zaključan."}, status=400)
    try:
        fiskalni.odvezi_od_putnog_naloga(racun)
    except fiskalni.GreskaOcitavanja as exc:
        return JsonResponse({"ok": False, "poruka": str(exc)}, status=400)
    return JsonResponse({"ok": True, "poruka": f"Račun {racun.broj_racuna} je skinut sa putnog naloga."})


@login_required
@require_POST
@role_permission_required()
def putni_nalog_opravdaj(request, pk):
    """Kao „Opravdaj” u Floti: nalog postaje opravdan i zaključan za izmene."""
    putni_nalog = get_object_or_404(putni_nalozi().filter(storniran=False), pk=pk)
    ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if not putni_nalog.opravdan:
        putni_nalog.opravdan = True
        putni_nalog.save(update_fields=["opravdan"])
        if not ajax:
            messages.success(request, f"Putni nalog {putni_nalog.order_number} je opravdan.")
    if ajax:
        return JsonResponse({"ok": True, "poruka": f"Putni nalog {putni_nalog.order_number} je opravdan."})
    nazad = request.POST.get("next") or ""
    if not url_has_allowed_host_and_scheme(nazad, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        nazad = reverse("isplate:putni_nalozi_pravdanje")
    return redirect(nazad)
