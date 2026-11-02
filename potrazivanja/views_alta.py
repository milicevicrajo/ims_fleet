"""Kupci sa računima u Alta banci — poseban slučaj naplate (od 02.11.2026., services/alta_banka.py)."""
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from core.exporting import create_xlsx_workbook, style_header_row, workbook_response
from core.mixins import user_has_role_permission as has
from .access import can_view_all, check_access
from .models import FinancePartnerIdentity, KupacAltaBanka
from .services.alta_banka import ALTA

PRIKAZI = {"platioci": "Plaćali preko Alta banke", "racun": "Imaju račun u Alta banci", "svi": "Svi"}


def redovi(prikaz, snapshot):
    kupci = KupacAltaBanka.objects.filter(company=1).prefetch_related("racuni")
    if prikaz == "platioci":
        kupci = kupci.filter(broj_uplata__gt=0)
    elif prikaz == "racun":
        kupci = kupci.filter(racuni__banka_sifra=ALTA).distinct()
    kupci = list(kupci.order_by("-iznos_uplata", "naziv"))
    identiteti = dict(FinancePartnerIdentity.objects.filter(company=1, partner_group=1, partner_code__in=[
        k.partner_code for k in kupci]).values_list("partner_code", "pk"))
    dug = {}
    if snapshot:
        dug = dict(snapshot.positions.filter(identity_id__in=identiteti.values()).values("identity_id")
                   .annotate(s=Sum("balance")).values_list("identity_id", "s"))
    for kupac in kupci:
        kupac.racuni_alta = [r for r in kupac.racuni.all() if r.alta]
        kupac.identitet = identiteti.get(kupac.partner_code)
        kupac.dug = dug.get(kupac.identitet)
    return kupci


def excel(kupci):
    knjiga, list_ = create_xlsx_workbook("Kupci")
    list_.append(["Šifra partnera", "Naziv", "Matični broj", "PIB", "Uplata preko Alta (broj)", "Uplata preko Alta (iznos)",
                  "Prva uplata", "Poslednja uplata", "Računi Alta iz izvoda", "Računi u Alta banci (NBS)",
                  "Dug (Potraživanja)", "NBS preuzeto", "Napomena"])
    for k in kupci:
        list_.append([k.partner_code, k.naziv, k.maticni_broj, k.pib, k.broj_uplata, float(k.iznos_uplata), k.prva_uplata,
                      k.poslednja_uplata, k.racuni_uplata, ", ".join(r.racun for r in k.racuni_alta),
                      float(k.dug) if k.dug is not None else None,
                      k.nbs_preuzeto.replace(tzinfo=None) if k.nbs_preuzeto else None, k.nbs_greska])
    style_header_row(list_)
    # Računi u drugim bankama ostaju u bazi (snimak NBS za platioce), ali se ne prikazuju (02.11.2026.).
    racuni = knjiga.create_sheet("Računi u Alta banci")
    racuni.append(["Šifra partnera", "Naziv", "Račun", "Tip", "Status", "Blokada", "Datum otvaranja",
                   "Naziv u NBS", "Mesto", "Preuzeto"])
    for k in kupci:
        for r in k.racuni_alta:
            racuni.append([k.partner_code, k.naziv, r.racun, r.tip, r.status, r.blokada, r.datum_otvaranja,
                           r.naziv_nbs, r.mesto, r.preuzeto.replace(tzinfo=None)])
    style_header_row(racuni)
    for ws, sirine in ((list_, (10, 45, 12, 12, 10, 16, 12, 12, 30, 45, 16, 18, 40)),
                      (racuni, (10, 45, 24, 10, 12, 18, 14, 45, 25, 18))):
        for i, sirina in enumerate(sirine):
            ws.column_dimensions[chr(65 + i)].width = sirina
    return knjiga


@never_cache
@require_GET
def alta_banka(request):
    from .views import context, current_snapshot

    check_access(request.user)
    if not (can_view_all(request.user) and has(request.user, "potrazivanja:alta_banka")):
        raise PermissionDenied("Spisak kupaca sa računima u Alta banci zahteva pristup svim potraživanjima.")
    prikaz = request.GET.get("prikaz") if request.GET.get("prikaz") in PRIKAZI else "platioci"
    snapshot = current_snapshot(request)
    kupci = redovi(prikaz, snapshot)
    if request.GET.get("izvoz") == "xlsx":
        return workbook_response(excel(kupci), f"alta_banka_kupci_{prikaz}.xlsx")
    ctx = context(request, snapshot)
    poslednje = KupacAltaBanka.objects.filter(company=1, nbs_preuzeto__isnull=False).order_by("-nbs_preuzeto").first()
    ctx.update(section="alta", title="Alta banka — kupci", kupci=kupci, prikaz=prikaz, prikazi=PRIKAZI,
               poslednje=poslednje.nbs_preuzeto if poslednje else None,
               ukupno=sum((k.iznos_uplata for k in kupci), 0),
               bez_snimka=sum(1 for k in kupci if not k.nbs_preuzeto))
    return render(request, "potrazivanja/alta_banka.html", ctx)
