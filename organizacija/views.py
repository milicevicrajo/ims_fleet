from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.mixins import role_permission_required, user_has_role_permission
from organizacija.forms import DodelaForm
from organizacija.models import DodelaUloge, OrgImportRun
from organizacija.services import detail as detail_service
from organizacija.services import dodele as dodele_service
from organizacija.services import flota as flota_service
from organizacija.services import sema as sema_service
from organizacija.services import sync as sync_service
from organizacija.services import tree as tree_service

COMPANY = 1
# Organizaciju vide svi prijavljeni korisnici. Iznose knjiženja na kartici posla vidi
# samo onaj ko u Finansijama sme da gleda knjiženja.
LEDGER_PERMISSION = "finansije:ledger"


@require_GET
@login_required
def stablo(request):
    """Stablo organizacije, samo za citanje.

    Faza 1 nema nijedno dugme za izmenu: registar se prvo puni i poredi, pa tek kasnije
    postaje mesto odrzavanja. Zato ovde nema ni forme ni POST rute.
    """
    request.session["current_app"] = "organizacija"
    query = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    profit = (request.GET.get("profit") or "").strip()
    if status not in tree_service.STATUS_CHOICES:
        status = ""
    if profit not in tree_service.PROFIT_CHOICES:
        profit = ""

    last_run = OrgImportRun.objects.filter(status=OrgImportRun.STATUS_DONE).first()
    tree = tree_service.build_tree(COMPANY, query, status, profit)
    filtered = bool(query or status or profit)
    context = {
        "tree": tree,
        "totals": tree_service.totals(tree),
        "all_totals": tree_service.totals(tree_service.build_tree(COMPANY)),
        "query": query,
        "status": status,
        "profit": profit,
        "filtered": filtered,
        "filter_links": tree_service.filter_links(query, status, profit),
        "last_run": last_run,
        "grupe": tree_service.po_delovima(tree),
        "unresolved": tree_service.unresolved_groups(last_run),
        "is_empty": not tree and not filtered,
    }
    return render(request, "organizacija/stablo.html", context)


@require_GET
@login_required
def sema(request):
    """Organizaciona šema IMS prema aneksima A, B i C — statičan prikaz, bez podataka iz registra."""
    request.session["current_app"] = "organizacija"
    return render(request, "organizacija/sema.html", sema_service.sema())


@require_GET
@login_required
def cvor(request, pk):
    """Kartica jednog cvora: podaci, putanja, potomci, istorija i povezivanja.

    Samo za citanje, kao i stablo. Istorija je ovde glavna stvar — po njoj se vidi da
    promena naziva ili sifre ostaje isti posao.
    """
    request.session["current_app"] = "organizacija"
    data = detail_service.node_detail(pk)
    if data is None:
        raise Http404("Cvor ne postoji.")
    data["usage"] = (detail_service.ledger_usage(data)
                     if user_has_role_permission(request.user, LEDGER_PERMISSION) else None)
    return render(request, "organizacija/cvor.html", data)


@require_GET
@login_required
@role_permission_required()
def flota(request):
    """Faza 2 po modulima (Flota, Nabavka): stanje veze `org_node` i uporedni izvestaj.

    Samo za citanje — veza se popunjava komandom `povezi_flotu --modul …`. Moduli i dalje sve
    racunaju iz starih polja; ovaj ekran pokazuje da li bi registar dao isto.
    """
    request.session["current_app"] = "organizacija"
    modul = request.GET.get("modul") or "flota"
    if modul not in flota_service.MODULI:
        modul = "flota"
    godine = flota_service.godine_goriva()
    godina = request.GET.get("godina") or ""
    godina = int(godina) if godina.isdigit() and int(godina) in godine else None
    izvestaj = flota_service.uporedni_izvestaj(COMPANY, godina, modul=modul)
    context = {
        "modul": modul,
        "naziv_modula": flota_service.NAZIVI_MODULA[modul],
        "moduli": list(flota_service.NAZIVI_MODULA.items()),
        "stanje": flota_service.povezi(COMPANY, proba=True, modul=modul),
        "kontrola": sync_service.uporedi_jedinice(COMPANY),
        "svezina": sync_service.svezina_izvora(COMPANY),
        "izvestaj": izvestaj,
        "godine": godine,
        "godina": godina,
        "last_run": OrgImportRun.objects.filter(status=OrgImportRun.STATUS_DONE).first(),
    }
    return render(request, "organizacija/flota.html", context)


# --------------------------------------------------------------------------- dodele uloga (korak 3)
# Nijedna dodela jos ne odlucuje o pristupu: moduli citaju stara prava do pilota (korak 5).


@require_GET
@login_required
@role_permission_required()
def dodele(request):
    """Spisak korisnika sa nacrtom i odobrenim dodelama; senka samo na zahtev (traje ~10 s)."""
    request.session["current_app"] = "organizacija"
    q = (request.GET.get("q") or "").strip()
    status = request.GET.get("status") or ""
    if status not in dodele_service.FILTERI_STATUSA:
        status = ""
    sa_senkom = request.GET.get("senka") == "1"
    redovi = dodele_service.spisak(q, status, sa_senkom)
    context = {
        "redovi": redovi, "q": q, "status": status, "sa_senkom": sa_senkom,
        "filteri": dodele_service.FILTERI_STATUSA,
        "ukupno_nacrt": sum(1 for r in redovi if r["nacrt"]),
        "ukupno_odobreno": sum(1 for r in redovi if r["odobren"]),
        "sa_razlikom": sum(1 for r in redovi if r.get("senka") and r["senka"]["razlika"]),
    }
    return render(request, "organizacija/dodele.html", context)


@require_http_methods(["GET", "POST"])
@login_required
@role_permission_required()
def dodele_korisnika(request, pk):
    """Dodele jednog korisnika, istorija, stara prava i senka; POST dodaje rucnu dodelu."""
    from core.models import CustomUser

    request.session["current_app"] = "organizacija"
    korisnik = get_object_or_404(CustomUser, pk=pk)
    form = DodelaForm(request.POST or None, korisnik=korisnik)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        dodele_service.dodaj(korisnik, d["uloga"], d["cvor_id"], d["cela_firma"], d["vazi_od"], d["vazi_do"],
                             request.user, d["napomena"])
        messages.success(request, "Dodela je upisana i odobrena.")
        return redirect("organizacija:dodele_korisnika", pk=korisnik.pk)
    context = {"korisnik": korisnik, "form": form, **dodele_service.pregled_korisnika(korisnik),
               "moze_odobri": user_has_role_permission(request.user, "organizacija:dodele_odobri"),
               "moze_opozovi": user_has_role_permission(request.user, "organizacija:dodela_opozovi")}
    return render(request, "organizacija/dodele_korisnika.html", context)


@require_POST
@login_required
@role_permission_required()
def dodele_odobri(request, pk):
    from core.models import CustomUser

    korisnik = get_object_or_404(CustomUser, pk=pk)
    broj = dodele_service.odobri(korisnik, request.user)
    messages.success(request, f"Odobreno dodela: {broj}." if broj else "Korisnik nema nacrt za odobravanje.")
    return redirect("organizacija:dodele_korisnika", pk=korisnik.pk)


@require_POST
@login_required
@role_permission_required()
def dodela_opozovi(request, pk):
    dodela = get_object_or_404(DodelaUloge, pk=pk)
    ishod = dodele_service.opozovi(dodela, request.user)
    messages.success(request, "Nacrt dodele je obrisan." if ishod == "obrisan" else "Dodela je opozvana od danas.")
    return redirect("organizacija:dodele_korisnika", pk=dodela.korisnik_id)
