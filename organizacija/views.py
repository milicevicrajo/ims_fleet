from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.mixins import role_permission_required
from organizacija.models import OrgImportRun
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
    tree = tree_service.build_tree(COMPANY, query)
    last_run = OrgImportRun.objects.filter(status=OrgImportRun.STATUS_DONE).first()
    context = {
        "tree": tree,
        "totals": tree_service.totals(tree),
        "query": query,
        "last_run": last_run,
        "unresolved": tree_service.unresolved_groups(last_run),
        "is_empty": not tree and not query,
    }
    return render(request, "organizacija/stablo.html", context)
