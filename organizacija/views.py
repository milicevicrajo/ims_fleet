from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.mixins import role_permission_required
from organizacija.models import OrgImportRun
from organizacija.services import detail as detail_service
from organizacija.services import tree as tree_service

COMPANY = 1


@require_GET
@login_required
@role_permission_required()
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

    tree = tree_service.build_tree(COMPANY, query, status, profit)
    last_run = OrgImportRun.objects.filter(status=OrgImportRun.STATUS_DONE).first()
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
        "unresolved": tree_service.unresolved_groups(last_run),
        "is_empty": not tree and not filtered,
    }
    return render(request, "organizacija/stablo.html", context)


@require_GET
@login_required
@role_permission_required()
def cvor(request, pk):
    """Kartica jednog cvora: podaci, putanja, potomci, istorija i povezivanja.

    Samo za citanje, kao i stablo. Istorija je ovde glavna stvar — po njoj se vidi da
    promena naziva ili sifre ostaje isti posao.
    """
    request.session["current_app"] = "organizacija"
    data = detail_service.node_detail(pk)
    if data is None:
        raise Http404("Cvor ne postoji.")
    data["usage"] = detail_service.ledger_usage(data)
    return render(request, "organizacija/cvor.html", data)
