"""Prikaz SEF faktura; straničenje i veze samo nad lokalnim podacima."""
from collections import defaultdict
from urllib.parse import urlencode

from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils.formats import number_format
from django.utils.html import format_html
from django.utils.text import Truncator

from core.mixins import user_has_role_permission
from ugovori.models import Partner
from . import sef
from .datatables import display_date, integer


def confirmation_icon(confirmed, label, *, pdf=False):
    document = format_html('<i class="{}" aria-hidden="true"></i>', "mdi mdi-file-pdf-box sef-pdf-icon") if pdf else ""
    return format_html('<span class="sef-confirmation" role="img" aria-label="{}" title="{}">'
                       '<i class="mdi {} {}" aria-hidden="true"></i>{}</span>',
                       label, label, "mdi-check-circle" if confirmed else "mdi-minus-circle-outline",
                       "sef-confirmed" if confirmed else "sef-missing", document)


def table_rows(user, invoices, params):
    invoices = list(invoices)
    booked = sef.proknjizeni_brojevi(invoices)
    by_pib, by_mb = defaultdict(dict), defaultdict(dict)
    if invoices and user_has_role_permission(user, "ugovori:partner_detail"):
        pibs = {f.partner_pib.strip() for f in invoices if f.partner_pib.strip()}
        mbs = {f.partner_mb.strip() for f in invoices if f.partner_mb.strip()}
        for p in Partner.objects.filter(Q(pib__in=pibs) | Q(maticni_broj__in=mbs)).only("pk", "pib", "maticni_broj"):
            if p.pib:
                by_pib[p.pib.strip()][p.pk] = p
            if p.maticni_broj:
                by_mb[p.maticni_broj.strip()][p.pk] = p
    rows = []
    for f in invoices:
        # Oba identifikatora moraju biti saglasna kada postoje u šifrarniku.
        candidates = by_pib.get(f.partner_pib.strip(), {})
        mb_matches = by_mb.get(f.partner_mb.strip(), {})
        if candidates and mb_matches:
            candidates = {pk: p for pk, p in candidates.items() if pk in mb_matches}
        elif not candidates:
            candidates = mb_matches
        candidates = {pk: p for pk, p in candidates.items()
                      if not (f.partner_pib and p.pib and f.partner_pib.strip() != p.pib.strip())
                      and not (f.partner_mb and p.maticni_broj and f.partner_mb.strip() != p.maticni_broj.strip())}
        name = f.partner_naziv or "—"
        short = Truncator(name).chars(80)
        if len(candidates) == 1:
            partner = format_html('<a class="sef-partner" href="{}" title="{}">{}</a>',
                                  reverse("ugovori:partner_detail", args=[next(iter(candidates))]), name, short)
        else:
            partner = format_html('<span class="sef-partner" title="{}">{}</span>', name, short)
        if f.partner_pib:
            partner = format_html('{}<small class="sef-meta">PIB {}</small>', partner, f.partner_pib)
        url = reverse("finansije:sef_detail", args=[f.pk])
        if params:
            url += "?" + urlencode({"nazad": "?" + params})
        f.proknjizena = f.broj_kljuc in booked
        rows.append([
            format_html('<a class="btn btn-sm btn-outline-primary sef-document" href="{}"><i class="mdi mdi-eye" aria-hidden="true"></i> {}</a>', url, f.broj or f.sef_id),
            format_html('<span class="sef-direction sef-direction-{}">{}</span>',
                        f.smer, f.get_smer_display()),
            format_html('<span class="sef-kind">{}</span>', sef.VRSTE.get(f.vrsta, f.vrsta or "—")),
            partner,
            display_date(f.datum_dok), display_date(f.datum_slanja),
            format_html('<span class="sef-amount">{} <small>{}</small></span>',
                        number_format(f.iznos, decimal_pos=2, use_l10n=True) if f.iznos is not None else "—", f.valuta),
            format_html('<span class="sef-status">{}</span>', sef.STATUSI.get(f.status, f.status or "—")),
            confirmation_icon(f.proknjizena, "Postoji knjiženje sa ovim brojem dokumenta" if f.proknjizena else "Nema knjiženja sa ovim brojem dokumenta"),
            confirmation_icon(bool(f.pdf), "PDF je preuzet" if f.pdf else "PDF nije preuzet", pdf=True),
        ])
    return rows


def table_response(request, queryset, params):
    total = queryset.count()
    term = request.GET.get("search[value]", "").strip()[:200]
    if term:
        query = Q(broj__icontains=term) | Q(partner_naziv__icontains=term) | Q(partner_pib__icontains=term) | Q(partner_mb__icontains=term)
        for field, choices in (("status", sef.STATUSI.items()), ("vrsta", sef.VRSTE.items()),
                               ("smer", (("ulazna", "Ulazna"), ("izlazna", "Izlazna")))):
            query |= Q(**{field + "__in": [code for code, label in choices if term.casefold() in label.casefold()]})
        queryset = queryset.filter(query)
    filtered = queryset.count() if term else total
    columns = ("broj", "smer", "vrsta", "partner_naziv", "datum_dok", "datum_slanja", "iznos", "status", None, None)
    ordering = []
    for index in range(len(columns)):
        col = integer(request.GET, f"order[{index}][column]", -1)
        if 0 <= col < len(columns) and columns[col]:
            ordering.append(("-" if request.GET.get(f"order[{index}][dir]") == "desc" else "") + columns[col])
    start = max(0, integer(request.GET, "start", 0))
    length = max(1, min(200, integer(request.GET, "length", 50)))
    invoices = queryset.order_by(*(ordering or ["-datum_dok"]), "-pk")[start:start + length]
    return JsonResponse({"draw": max(0, integer(request.GET, "draw", 0)), "recordsTotal": total,
                         "recordsFiltered": filtered, "data": table_rows(request.user, invoices, params)})
