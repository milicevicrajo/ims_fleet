"""Isplate → Putni nalozi – Fiskalni računi (od 02.10.2026.).

Knjigovodstvo vidi fiskalne račune koji su učitani na putnim nalozima (`nabavka.FiskalniRacun`
sa `putni_nalog`) i označava ih „proknjiženo”. Oznaka ne upisuje ništa u knjigovodstvo; beleži
ko je i kada označio, a proknjižen račun se u Nabavci i na putnom nalogu više ne menja.
Isplate još rade po starim pravima: ekran pokazuje sve račune sa putnih naloga.
"""
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.exporting import rows_to_xlsx_response
from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission
from nabavka.models import FiskalniRacun
from nabavka.services import fiskalni
from nabavka.views.fiskalni import _iznos

from . import tabela


def racuni_putnih_naloga():
    return (FiskalniRacun.objects.filter(putni_nalog__isnull=False)
            .select_related("putni_nalog", "putni_nalog__employee", "putni_nalog__job_code", "job_code",
                            "created_by", "proknjizio"))


def filtriraj(qs, g):
    knjizenje = g.get("knjizenje", "ne")
    if knjizenje == "ne":
        qs = qs.filter(proknjizeno=False)
    elif knjizenje == "da":
        qs = qs.filter(proknjizeno=True)
    od, do = parse_date(g.get("od") or ""), parse_date(g.get("do") or "")
    if od:
        qs = qs.filter(pfr_vreme__date__gte=od)
    if do:
        qs = qs.filter(pfr_vreme__date__lte=do)
    if g.get("kupac") == "ims":
        qs = qs.filter(na_ims=True)
    elif g.get("kupac") == "drugi":
        qs = qs.filter(na_ims=False)
    for rec in tabela.reci(g):
        qs = qs.filter(Q(broj_racuna__icontains=rec) | Q(naziv_prodavca__icontains=rec) | Q(pib_prodavca=rec)
                       | Q(putni_nalog__order_number__icontains=rec) | Q(putni_nalog__employee__last_name__icontains=rec)
                       | Q(putni_nalog__employee__first_name__icontains=rec) | Q(job_code__code__icontains=rec))
    return qs


def _zbir(qs):
    zbir = qs.aggregate(broj=Count("pk"), iznos=Sum("iznos"), pdv=Sum("pdv_ukupno"))
    return {"broj": zbir["broj"], "iznos": _iznos(zbir["iznos"] or 0), "pdv": _iznos(zbir["pdv"] or 0)}


def _ko(korisnik):
    return (korisnik.get_full_name() or korisnik.get_username()) if korisnik else ""


class FiskalniPutniNaloziView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "isplate/fiskalni_putni_nalozi.html"
    KOLONE = {"0": "pfr_vreme", "1": "naziv_prodavca", "2": "broj_racuna", "3": "iznos", "5": "putni_nalog__order_number",
              "6": "job_code__code", "7": "created_at", "8": "proknjizeno"}

    def get(self, request, *args, **kwargs):
        if tabela.je_zahtev_tabele(request):
            return self.podaci(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        ctx.update(
            title="Putni nalozi – Fiskalni računi", sidebar_template="sidebar_isplate.html",
            zbir=_zbir(filtriraj(racuni_putnih_naloga(), g)),
            filteri={k: g.get(k, "") for k in ("q", "od", "do", "kupac")} | {"knjizenje": g.get("knjizenje", "ne")},
            moze_izvoz=user_has_role_permission(self.request.user, "isplate:fiskalni_izvoz"),
        )
        return ctx

    def podaci(self, request):
        g, user = request.GET, request.user
        sve = racuni_putnih_naloga()
        qs = filtriraj(sve, g)
        start, duzina, draw = tabela.strana(g)
        strana = list(qs.order_by(tabela.redosled(g, self.KOLONE, "pfr_vreme"), "-pk")[start:start + duzina])
        prava = {"knjizi": user_has_role_permission(user, "isplate:fiskalni_proknjizi"),
                 "detalj": user_has_role_permission(user, "nabavka:fiskalni_detail"),
                 "nalog": user_has_role_permission(user, "isplate:putni_nalozi_pravdanje")}
        return tabela.odgovor(draw, sve.count(), qs.count(), [self._red(r, prava) for r in strana], zbir=_zbir(qs))

    @staticmethod
    def _red(r, prava):
        pn = r.putni_nalog
        broj = escape(r.broj_racuna)
        if prava["detalj"]:
            broj = format_html('<a href="{}" target="_blank" rel="noopener">{}</a>',
                               reverse("nabavka:fiskalni_detail", args=[r.pk]), r.broj_racuna)
        if r.status != r.Status.POTVRDJEN:
            broj += ('<div><span class="isp-badge muted" title="Stavke još nisu preuzete sa stranice Poreske uprave">'
                     'Čeka proveru</span></div>')
        nalog = escape(pn.order_number)
        if prava["nalog"]:
            nalog = format_html('<a href="{}?status=svi&amp;q={}">{}</a>', reverse("isplate:putni_nalozi_pravdanje"),
                                quote(pn.order_number), pn.order_number)
        detalji = " · ".join(d for d in (str(pn.employee or pn.other_employee_name or ""), pn.travel_location or "",
                                         f"{pn.travel_date:%d.%m.%Y.}" if pn.travel_date else "") if d)
        nalog += f'<div class="isp-small">{escape(detalji)}</div>'
        if pn.storniran:
            nalog += '<span class="isp-badge warn"><i class="mdi mdi-alert" aria-hidden="true"></i> Nalog storniran</span>'
        if r.na_ims:
            kupac = '<span class="isp-badge ok">IMS</span>'
        else:
            kupac = (f'<span class="isp-badge warn" title="Račun nije izdat na PIB Instituta">'
                     f'{"Drugi kupac" if r.id_kupca else "Fizičko lice"}</span>')
        pdv = f'<div class="isp-small">PDV {_iznos(r.pdv_ukupno)}</div>' if r.pdv_ukupno is not None else ""
        knjizi = format_html(
            '<input type="checkbox" class="form-check-input isp-knjizi" data-url="{}" data-racun="{}" aria-label="Proknjiženo {}"{}{}>'
            '<div class="isp-small isp-ko">{}{}</div>',
            reverse("isplate:fiskalni_proknjizi", args=[r.pk]), r.broj_racuna, r.broj_racuna,
            mark_safe(" checked") if r.proknjizeno else "", mark_safe("") if prava["knjizi"] else mark_safe(" disabled"),
            _ko(r.proknjizio) if r.proknjizeno else "",
            mark_safe(f"<br>{timezone.localtime(r.proknjizeno_at):%d.%m.%Y. %H:%M}") if r.proknjizeno and r.proknjizeno_at else "",
        )
        return {
            "DT_RowClass": "isp-proknjizen" if r.proknjizeno else "",
            "vreme": f"{timezone.localtime(r.pfr_vreme):%d.%m.%Y.}<div class=\"isp-small\">{timezone.localtime(r.pfr_vreme):%H:%M}</div>",
            "prodavac": (f'<span title="{escape(r.naziv_prodavca or "")}">{escape(r.naziv_prodavca or "—")}</span>'
                         f'<div class="isp-small">PIB {escape(r.pib_prodavca or "—")}</div>'),
            "broj": broj,
            "iznos": f"<strong>{_iznos(r.iznos)}</strong>{pdv}",
            "kupac": kupac,
            "nalog": nalog,
            "sifra": escape(r.job_code.code),
            "ucitao": (f'{escape(r.created_by.get_username() if r.created_by_id else "—")}'
                       f'<div class="isp-small">{timezone.localtime(r.created_at):%d.%m.%Y.}</div>'),
            "knjizenje": knjizi,
        }


@login_required
@require_POST
@role_permission_required()
def fiskalni_proknjizi(request, pk):
    """Polje za štikliranje „Proknjiženo” (fetch): vraća novo stanje."""
    racun = get_object_or_404(racuni_putnih_naloga(), pk=pk)
    fiskalni.oznaci_proknjizeno(racun, request.user, request.POST.get("proknjizeno") == "1", request=request)
    return JsonResponse({
        "ok": True, "proknjizeno": racun.proknjizeno,
        "ko": (racun.proknjizio.get_full_name() or racun.proknjizio.get_username()) if racun.proknjizio_id else "",
        "kada": timezone.localtime(racun.proknjizeno_at).strftime("%d.%m.%Y. %H:%M") if racun.proknjizeno_at else "",
    })


@login_required
@role_permission_required()
def fiskalni_izvoz(request):
    qs = filtriraj(racuni_putnih_naloga(), request.GET).order_by("pfr_vreme", "pk")
    zaglavlje = ["Vreme računa", "Prodavac", "PIB prodavca", "Broj računa", "Iznos", "PDV", "Kupac", "Putni nalog",
                 "Zaposleni", "Mesto putovanja", "Datum putovanja", "Šifra posla", "Status", "Proknjiženo", "Proknjižio",
                 "Proknjiženo dana", "Učitao"]
    redovi = []
    for r in qs:
        pn = r.putni_nalog
        redovi.append([
            timezone.localtime(r.pfr_vreme).strftime("%d.%m.%Y %H:%M"), r.naziv_prodavca, r.pib_prodavca, r.broj_racuna,
            float(r.iznos), float(r.pdv_ukupno) if r.pdv_ukupno is not None else None,
            "IMS" if r.na_ims else ("Drugi kupac" if r.id_kupca else "Fizičko lice"),
            pn.order_number, str(pn.employee or pn.other_employee_name or ""), pn.travel_location,
            pn.travel_date.strftime("%d.%m.%Y") if pn.travel_date else "", r.job_code.code,
            r.get_status_display(), "da" if r.proknjizeno else "ne",
            (r.proknjizio.get_full_name() or r.proknjizio.get_username()) if r.proknjizio_id else "",
            timezone.localtime(r.proknjizeno_at).strftime("%d.%m.%Y %H:%M") if r.proknjizeno_at else "",
            r.created_by.get_username() if r.created_by_id else "",
        ])
    return rows_to_xlsx_response(f"Fiskalni-racuni-putnih-naloga-{timezone.localdate():%Y%m%d}.xlsx",
                                 "Fiskalni računi", zaglavlje, redovi, bold_header=True, auto_width=True)
