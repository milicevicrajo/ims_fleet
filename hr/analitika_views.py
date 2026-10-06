"""Kadrovi → Analitika zaposlenih: ekran, PDF (A4, reportlab) i Excel (od 05.10.2026.)."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin
from .access import visible_employees
from .services import analitika_izvoz, analitika_pdf
from .services.analitika import analitika


class AnalitikaView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "hr/analitika.html"

    def zaposleni(self):
        qs = visible_employees(self.request.user).filter(is_active=True)
        oj = self.request.GET.get("oj", "").strip()
        if oj:
            uslov = Q(org_unit_code=oj)
            if oj.isdigit():
                uslov |= (Q(org_unit_code__isnull=True) | Q(org_unit_code="")) & Q(department_code=int(oj))
            qs = qs.filter(uslov)
        return qs, oj

    def get(self, request, *args, **kwargs):
        qs, oj = self.zaposleni()
        a = analitika(qs, timezone.localdate())
        filteri = f"Aktivni zaposleni · OJ {oj}" if oj else "Svi aktivni zaposleni u vašem obuhvatu"
        izvoz = request.GET.get("izvoz")
        if izvoz == "xlsx":
            return analitika_izvoz.excel(a, filteri)
        if izvoz in ("pdf", "stampa"):
            return analitika_pdf.pdf(a, filteri)
        sve_oj = visible_employees(request.user).filter(is_active=True).values_list("org_unit_code", "department_code")
        upit = request.GET.copy()
        upit.pop("izvoz", None)
        return self.render_to_response(self.get_context_data(
            a=a, filteri=filteri, izabrana_oj=oj, izvoz_upit=upit.urlencode(),
            oj_izbor=sorted({str(k or d) for k, d in sve_oj}, key=lambda x: (len(x), x)),
            title="Analitika zaposlenih", sidebar_template="sidebar_kadrovi.html", current_app="kadrovi"))
