"""Kadrovi → Pregled: početna strana modula (link „Kadrovi” u zaglavlju vodi ovde).

Stranu otvara svaki prijavljeni korisnik, kao što su i „Moj profil” i radna lista svima dostupni;
delovi strane se prikazuju samo uz dozvolu odgovarajućeg spiska i u obuhvatu korisnika
(`hr/services/pregled.py`). Zato ruta nema sopstvenu proveru dozvole.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from hr.services.pregled import pregled


class KadroviPregledView(LoginRequiredMixin, TemplateView):
    template_name = "hr/pregled.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(pregled(self.request.user, timezone.localdate()))
        ctx.update(title="Kadrovi — pregled", sidebar_template="sidebar_kadrovi.html", current_app="kadrovi",
                   ima_profil=bool(getattr(self.request.user, "employee_id", None)))
        return ctx
