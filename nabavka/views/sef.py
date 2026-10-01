"""UF SEF (Nabavka): pregled samo ulaznih faktura sa SEF-a.

Fakture preuzimaju Finansije (`finansije/services/sef.py`, nocu i dugmetom u Finansijama);
Nabavka ih samo prikazuje — ne preuzima ih sama i nista ne salje na SEF (ne prihvata, ne odbija).
Ulazna faktura nema sifru posla, pa je vidi samo obuhvat cele firme (`nabavka.access.ulazne_sef`).
"""
import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import number_format
from django.utils.html import escape
from django.views import View
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, user_has_role_permission
from finansije.sef_models import SefFaktura, SefSinhronizacija
from finansije.services import sef as servis
from nabavka.access import ulazne_sef

from .cases import NabavkaContextMixin

FILTERI = ("q", "status", "vrsta", "od", "do", "knjizenje")


def _vidljive(user):
    return ulazne_sef(servis.sa_datumom(SefFaktura.objects.filter(smer=SefFaktura.Smer.ULAZNA)), user)


def _datum(tekst):
    try:
        return datetime.date.fromisoformat(tekst) if tekst else None
    except ValueError:
        return None


def _filtriraj(g, qs):
    if g.get("status"):
        qs = qs.filter(status=g["status"])
    if g.get("vrsta"):
        qs = qs.filter(vrsta=g["vrsta"])
    od, do = _datum(g.get("od")), _datum(g.get("do"))
    if od:
        qs = qs.filter(datum_dok__gte=od)
    if do:
        qs = qs.filter(datum_dok__lte=do)
    if g.get("knjizenje") == "da":
        qs = qs.filter(servis.q_proknjizena())
    elif g.get("knjizenje") == "ne":
        qs = qs.exclude(servis.q_proknjizena())
    for termin in (g.get("q") or "").split() + (g.get("search[value]") or "").split():
        uslov = (Q(broj__icontains=termin) | Q(partner_naziv__icontains=termin) | Q(partner_pib=termin)
                 | Q(partner_mb=termin))
        if termin.isdigit():
            uslov |= Q(sef_id=int(termin))
        qs = qs.filter(uslov)
    return qs


def _iznos(vrednost, valuta=""):
    if vrednost is None:
        return "—"
    return f'{number_format(vrednost, decimal_pos=2, use_l10n=True)} <small class="text-muted">{escape(valuta)}</small>'


class UfSefListView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/uf_sef_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        sve = _vidljive(self.request.user)
        statusi = set(sve.exclude(status="").values_list("status", flat=True).distinct())
        poslednja = SefSinhronizacija.objects.filter(status__in=("success", "stopped")).first()
        ctx.update(
            title="UF SEF", filteri={k: g.get(k, "") for k in FILTERI},
            zbir=_filtriraj(g, sve).aggregate(broj=Count("pk"), iznos=Sum("iznos")),
            statusi=[(s, servis.STATUSI.get(s, s)) for s in sorted(statusi, key=lambda s: servis.STATUSI.get(s, s))],
            vrste=list(servis.VRSTE.items()),
            poslednja=poslednja,
        )
        return ctx


class UfSefDataView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    KOLONE = {"0": "broj", "1": "partner_naziv", "2": "datum_dok", "3": "datum_slanja", "4": "datum_dospeca",
              "5": "iznos", "6": "status"}

    def get(self, request):
        sve = _vidljive(request.user)
        qs = _filtriraj(request.GET, sve)
        polje = self.KOLONE.get(request.GET.get("order[0][column]", "2"), "datum_dok")
        smer = "-" if request.GET.get("order[0][dir]", "desc") == "desc" else ""
        qs = qs.order_by(f"{smer}{polje}", "-sef_id")
        try:
            start = max(int(request.GET.get("start", 0)), 0)
            duzina = min(max(int(request.GET.get("length", 50)), 1), 200)
            draw = int(request.GET.get("draw", 0))
        except (TypeError, ValueError):
            start, duzina, draw = 0, 50, 0
        strana = list(qs[start:start + duzina])
        proknjizene = servis.proknjizeni_brojevi(strana)
        moze_pdf = user_has_role_permission(request.user, "nabavka:uf_sef_pdf")
        redovi = [self._red(f, f.broj_kljuc in proknjizene, moze_pdf) for f in strana]
        return JsonResponse({"draw": draw, "recordsTotal": sve.count(), "recordsFiltered": qs.count(), "data": redovi})

    @staticmethod
    def _red(f, proknjizena, moze_pdf):
        pdf = '<span class="text-muted">—</span>'
        if moze_pdf:
            pdf = (f'<a class="btn btn-outline-secondary btn-sm" href="{reverse("nabavka:uf_sef_pdf", args=[f.pk])}" '
                   f'target="_blank" rel="noopener" title="{"PDF je preuzet" if f.pdf else "PDF se preuzima sa SEF-a"}">'
                   f'<i class="mdi mdi-file-pdf-box"></i></a>')
        return {
            "broj": (f'<strong>{escape(f.broj or f.sef_id)}</strong>'
                     f'<div class="sef-small">{escape(servis.VRSTE.get(f.vrsta, f.vrsta or ""))}</div>'),
            "dobavljac": (f'<span title="{escape(f.partner_naziv)}">{escape(f.partner_naziv or "—")}</span>'
                      + (f'<div class="sef-small">PIB {escape(f.partner_pib)}</div>' if f.partner_pib else "")),
            "datum": f.datum_dok.strftime("%d.%m.%Y.") if f.datum_dok else "—",
            "primljena": timezone.localtime(f.datum_slanja).strftime("%d.%m.%Y. %H:%M") if f.datum_slanja else "—",
            "dospece": f.datum_dospeca.strftime("%d.%m.%Y.") if f.datum_dospeca else "—",
            "iznos": _iznos(f.iznos, f.valuta),
            "status": f'<span class="invoice-badge muted">{escape(servis.STATUSI.get(f.status, f.status or "—"))}</span>',
            "knjizenje": ('<span class="invoice-badge ok" title="Postoji knjiženje sa ovim brojem"><i class="mdi mdi-check"></i> Da</span>'
                          if proknjizena else '<span class="invoice-badge warn" title="Nema knjiženja sa ovim brojem">Ne</span>'),
            "pdf": pdf,
        }


class UfSefPdfView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, View):
    """PDF ulazne fakture: sacuvan u aplikaciji, a ako nije — preuzima se sa SEF-a sada (kao u Finansijama)."""

    def get(self, request, pk):
        faktura = get_object_or_404(_vidljive(request.user), pk=pk)
        try:
            spreman, poruka = servis.preuzmi_pdf(faktura)
        except (servis.SefNijePodesen, servis.SefGreska) as exc:
            messages.error(request, str(exc))
            return redirect("nabavka:uf_sef_list")
        if not spreman:
            messages.info(request, poruka or "SEF još priprema PDF. Pokušajte ponovo za nekoliko sekundi.")
            return redirect("nabavka:uf_sef_list")
        try:
            fajl = faktura.pdf.open("rb")
        except FileNotFoundError:
            raise Http404("PDF fakture nije pronađen.")
        ime = "".join(z if z.isalnum() or z in "-_" else "_" for z in (faktura.broj or str(faktura.sef_id)))
        odgovor = FileResponse(fajl, content_type="application/pdf")
        odgovor["Content-Disposition"] = f'inline; filename="SEF_{ime}.pdf"'
        return odgovor
