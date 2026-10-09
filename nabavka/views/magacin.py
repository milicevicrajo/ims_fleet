"""Nabavka → Stanje u magacinu (od 09.10.2026.): pregled pogleda `dbo.nbv_magacin`, samo čitanje."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin

from ..services import magacin
from .cases import NabavkaContextMixin


class MagacinView(NabavkaContextMixin, RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "nabavka/magacin.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        ctx["title"] = "Stanje u magacinu"
        try:
            ctx.update(magacin.pregled(godina=g.get("godina", ""), magacin=g.get("magacin", ""), vrsta=g.get("vrsta", ""),
                                       stanje=g.get("stanje", "sa_stanjem")))
        except DatabaseError:
            ctx["greska"] = "Pogled dbo.nbv_magacin trenutno nije dostupan."
        return ctx
