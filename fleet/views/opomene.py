"""Flota → Opomene za gorivo: nepravilno uneta kilometraža pri točenju i opomene vozačima.

Spisak pripremljenih i poslatih opomena (`fleet/support/opomene.py`) sa filterima i dugmetom
„Proveri sada”. Vidljivost prati obuhvat Flote po vozilu.
"""
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission

from ..models import OpomenaGoriva
from ..support import obuhvat as obuhvat_flote
from ..support import opomene as servis

NAJVISE_REDOVA = 500


def _datum(tekst):
    for oblik in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime((tekst or "").strip(), oblik).date()
        except ValueError:
            continue
    return None


class OpomenaListView(LoginRequiredMixin, RolePermissionRequiredMixin, TemplateView):
    template_name = "fleet/opomena_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        sve = obuhvat_flote.po_vozilu(OpomenaGoriva.objects.select_related("vehicle", "employee"), self.request.user)
        qs = sve
        if g.get("status") in OpomenaGoriva.Status.values:
            qs = qs.filter(status=g["status"])
        if g.get("vrsta") in OpomenaGoriva.Vrsta.values:
            qs = qs.filter(vrsta=g["vrsta"])
        od, do = _datum(g.get("od")), _datum(g.get("do"))
        if od:
            qs = qs.filter(vreme_tocenja__date__gte=od)
        if do:
            qs = qs.filter(vreme_tocenja__date__lte=do)
        brojevi = dict(sve.order_by().values_list("status").annotate(n=Count("pk")))
        po_statusu = [(naziv, brojevi.get(vrednost, 0)) for vrednost, naziv in OpomenaGoriva.Status.choices]
        ctx.update(
            title="Opomene za gorivo",
            opomene=qs.prefetch_related("vehicle__traffic_cards")[:NAJVISE_REDOVA], ukupno=qs.count(),
            najvise=NAJVISE_REDOVA, po_statusu=po_statusu,
            statusi=OpomenaGoriva.Status.choices, vrste=OpomenaGoriva.Vrsta.choices,
            filteri={k: g.get(k, "") for k in ("status", "vrsta", "od", "do")},
            kanal=servis.podesavanja()["kanal"],
            can_check=user_has_role_permission(self.request.user, "opomena_proveri"),
        )
        return ctx


@login_required
@require_POST
@role_permission_required("opomena_proveri")
def opomena_proveri(request):
    rezultat = servis.otkrij()
    try:
        poslato, bez_kontakta = servis.posalji()
    except ValueError as exc:
        messages.error(request, str(exc))
        poslato = bez_kontakta = 0
    messages.success(request, servis.poruka_zadatka(rezultat, poslato, bez_kontakta))
    return redirect("opomena_list")
