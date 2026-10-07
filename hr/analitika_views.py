"""Kadrovi → Analitika zaposlenih: ekran, PDF (A4, reportlab) i Excel (od 05.10.2026.)."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, user_has_role_permission
from .access import visible_employees
from .services import analitika_izvoz, analitika_pdf
from .services.analitika import analitika
from .services.osobe import jedan_po_osobi


class AnalitikaView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "hr/analitika.html"

    def vidljivi(self):
        # Pravna služba vidi analitiku cele firme (`hr:analitika_view_all`); Kadrovi po svom obuhvatu.
        sve = user_has_role_permission(self.request.user, "hr:analitika_view_all")
        return visible_employees(self.request.user, unrestricted=sve)

    def zaposleni(self):
        qs = self.vidljivi().filter(is_active=True)
        oj = self.request.GET.get("oj", "").strip()
        if oj:
            uslov = Q(org_unit_code=oj)
            if oj.isdigit():
                uslov |= (Q(org_unit_code__isnull=True) | Q(org_unit_code="")) & Q(department_code=int(oj))
            qs = qs.filter(uslov)
        return qs, oj

    def get(self, request, *args, **kwargs):
        qs, oj = self.zaposleni()
        # Jedan čovek = jedan zapis, i kad ima više aktivnih brojeva radnika (radni odnos + van radnog odnosa).
        a = analitika(jedan_po_osobi(qs.select_related("org_node")), timezone.localdate())
        filteri = f"Aktivni zaposleni · OJ {oj}" if oj else "Svi aktivni zaposleni u vašem obuhvatu"
        izvoz = request.GET.get("izvoz")
        if izvoz == "xlsx":
            return analitika_izvoz.excel(a, filteri)
        if izvoz in ("pdf", "stampa"):
            return analitika_pdf.pdf(a, filteri)
        sve_oj = self.vidljivi().filter(is_active=True).values_list("org_unit_code", "department_code")
        upit = request.GET.copy()
        upit.pop("izvoz", None)
        return self.render_to_response(self.get_context_data(
            a=a, filteri=filteri, izabrana_oj=oj, izvoz_upit=upit.urlencode(),
            moze_rodna=user_has_role_permission(request.user, "hr:rodna_ravnopravnost"),
            oj_izbor=sorted({str(k or d) for k, d in sve_oj}, key=lambda x: (len(x), x)),
            title="Analitika zaposlenih", sidebar_template="sidebar_kadrovi.html", current_app="kadrovi"))


class RodnaRavnopravnostView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    """Statistika rodne ravnopravnosti (Obrazac 1) za celu firmu, iz kadrovske baze; Excel i PDF (od 07.10.2026.)."""
    template_name = "hr/rodna_ravnopravnost.html"

    def get(self, request, *args, **kwargs):
        from django.contrib import messages
        from django.db import DatabaseError

        from .services import rodna_ravnopravnost as servis, rodna_ravnopravnost_izvoz as izvoz

        danas = timezone.localdate()
        try:
            godina = int(request.GET.get("godina") or danas.year - 1)
        except ValueError:
            godina = danas.year - 1
        godina = min(max(godina, 2015), danas.year)
        try:
            s = servis.statistika(godina, *servis.procitaj_izvor(), danas=danas)
        except DatabaseError as exc:
            messages.error(request, f"Kadrovska baza nije dostupna: {exc}")
            s = None
        if s and request.GET.get("izvoz") == "xlsx":
            return izvoz.excel(s)
        if s and request.GET.get("izvoz") == "pdf":
            return izvoz.pdf(s)
        return self.render_to_response(self.get_context_data(
            s=s, tabele=izvoz.tabele(s) if s else [], podnaslov=izvoz.podnaslov(s) if s else "", godina=godina,
            godine=range(danas.year, 2019, -1), title="Statistika rodne ravnopravnosti",
            sidebar_template="sidebar_kadrovi.html", current_app="kadrovi"))
