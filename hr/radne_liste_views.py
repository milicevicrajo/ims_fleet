"""Kadrovi → Pregled radnih lista (od 09.10.2026.): radne liste meseca za radnike iz obuhvata, kontrola, odobravanje
i CSV za obračun zarada. Podrazumevano prethodni mesec (tekući se još popunjava) i obračun broj 3."""
import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission

from .access import visible_employees
from .models import WorkTimeSheet
from .services import obracun_csv
from .services import radna_lista as pravila

PODRAZUMEVANI_BR_OBR = 3
MESECI = ["Januar", "Februar", "Mart", "April", "Maj", "Jun", "Jul", "Avgust", "Septembar", "Oktobar", "Novembar", "Decembar"]
STATUSI = {"nema": "Nema liste", WorkTimeSheet.Status.DRAFT: "Popunjava se", WorkTimeSheet.Status.SUBMITTED: "Predato",
           WorkTimeSheet.Status.APPROVED: "Odobreno"}


def prethodni_mesec(danas=None):
    danas = danas or timezone.localdate()
    return (danas.year - 1, 12) if danas.month == 1 else (danas.year, danas.month - 1)


def _period(g):
    godina, mesec = prethodni_mesec()
    try:
        godina, mesec = int(g.get("year") or godina), int(g.get("month") or mesec)
    except ValueError:
        pass
    if not (2000 <= godina <= 2100 and 1 <= mesec <= 12):
        godina, mesec = prethodni_mesec()
    return godina, mesec


def _sati(lista):
    fond = ostalo = 0
    for red in lista.lines.all():
        vrsta = red.work_category.code if red.work_category_id else None
        if vrsta is None or vrsta in pravila.FOND_VRSTE:
            fond += red.total_hours
        else:
            ostalo += red.total_hours
    return fond, ostalo


def _csv_upozorenja(lista, katalog):
    """Upozorenja CSV-a kojih nema u kontroli liste (element zarade), bez imena radnika — red je već njegov."""
    prefiks = f"{lista.employee.employee_code} {lista.employee}: "
    return [u.removeprefix(prefiks) for u in obracun_csv.stavke([lista], 0, katalog=katalog)[1] if "nema elementa" in u]


class RadneListePregledView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "hr/radne_liste.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g, user = self.request.GET, self.request.user
        godina, mesec = _period(g)
        status = g.get("status", "")
        vidljivi = visible_employees(user)
        liste = {s.employee_id: s for s in obracun_csv.listovi_meseca(vidljivi, godina, mesec)}
        zaposleni = (vidljivi.filter(Q(is_active=True) | Q(pk__in=list(liste)))
                     .exclude(date_of_joining__gt=date(godina, mesec, calendar.monthrange(godina, mesec)[1]))
                     .order_by("last_name", "first_name"))
        q = (g.get("q") or "").strip()
        for rec in q.split():
            uslov = (Q(first_name__icontains=rec) | Q(last_name__icontains=rec) | Q(display_first_name_override__icontains=rec)
                     | Q(display_last_name_override__icontains=rec))
            if rec.isdigit():
                uslov |= Q(employee_code=int(rec))
            zaposleni = zaposleni.filter(uslov)
        katalog = obracun_csv.elementi()
        redovi, brojevi = [], {k: 0 for k in STATUSI}
        for z in zaposleni:
            lista = liste.get(z.pk)
            st = lista.status if lista else "nema"
            brojevi[st] += 1
            if status and st != status:
                continue
            fond = pravila.fond_sati(godina, mesec, z.date_of_joining)
            red = {"zaposleni": z, "lista": lista, "status": st, "status_naziv": STATUSI[st], "fond": fond}
            if lista:
                red["sati"], red["dodatno"] = _sati(lista)
                red["problemi"] = pravila.kontrola_liste(lista) + _csv_upozorenja(lista, katalog)
            redovi.append(red)
        try:
            br_obr = int(g.get("br_obr") or PODRAZUMEVANI_BR_OBR)
        except ValueError:
            br_obr = PODRAZUMEVANI_BR_OBR
        danas = timezone.localdate()
        ctx.update(
            title="Pregled radnih lista", sidebar_template="sidebar_kadrovi.html", current_app="kadrovi",
            godina=godina, mesec=mesec, mesec_naziv=MESECI[mesec - 1], status=status, q=q, br_obr=br_obr, redovi=redovi,
            brojevi=[(k, v, brojevi[k]) for k, v in STATUSI.items()], ukupno=sum(brojevi.values()),
            meseci=list(enumerate(MESECI, start=1)), godine=range(danas.year - 2, danas.year + 1),
            fond=pravila.fond_sati(godina, mesec),
            can_csv=user_has_role_permission(user, "hr:work_time_sheet_csv"),
            can_csv_svi=user_has_role_permission(user, "hr:work_time_sheets_csv"),
            can_odobri=user_has_role_permission(user, "hr:work_time_sheet_odobri"),
            can_vrati=user_has_role_permission(user, "hr:work_time_sheet_vrati"),
            can_otvori=user_has_role_permission(user, "hr:employee_work_time_sheet"),
        )
        return ctx


def _nazad(request, lista):
    nazad = request.POST.get("nazad") or ""
    if nazad.startswith("/"):
        return redirect(nazad)
    return redirect(f"{reverse('hr:radne_liste')}?year={lista.year}&month={lista.month}")


@login_required
@require_POST
@role_permission_required()
def work_time_sheet_odobri(request, pk):
    """Predata lista bez grešaka postaje odobrena; posle toga se ne menja (osim vraćanja u pripremu)."""
    lista = get_object_or_404(obracun_csv.listovi(visible_employees(request.user)), pk=pk)
    if lista.status != WorkTimeSheet.Status.SUBMITTED:
        messages.error(request, f"{lista.employee}: odobrava se samo predata radna lista.")
        return _nazad(request, lista)
    problemi = pravila.kontrola_liste(lista)
    if problemi:
        messages.error(request, f"{lista.employee}: lista ne može da se odobri — " + "; ".join(problemi) + ".")
        return _nazad(request, lista)
    lista.status, lista.odobrio, lista.odobreno_at, lista.updated_by = (WorkTimeSheet.Status.APPROVED, request.user,
                                                                        timezone.now(), request.user)
    lista.save(update_fields=["status", "odobrio", "odobreno_at", "updated_by", "updated_at"])
    messages.success(request, f"Radna lista {lista.employee} za {lista.month:02d}/{lista.year} je odobrena.")
    return _nazad(request, lista)


@login_required
@require_POST
@role_permission_required()
def work_time_sheet_vrati(request, pk):
    """Predata ili odobrena lista se vraća zaposlenom u pripremu (da je ispravi i preda ponovo)."""
    lista = get_object_or_404(obracun_csv.listovi(visible_employees(request.user)), pk=pk)
    if lista.status == WorkTimeSheet.Status.DRAFT:
        messages.error(request, f"{lista.employee}: lista je već u pripremi.")
        return _nazad(request, lista)
    lista.status, lista.odobrio, lista.odobreno_at, lista.updated_by = WorkTimeSheet.Status.DRAFT, None, None, request.user
    lista.save(update_fields=["status", "odobrio", "odobreno_at", "updated_by", "updated_at"])
    messages.success(request, f"Radna lista {lista.employee} za {lista.month:02d}/{lista.year} je vraćena u pripremu.")
    return _nazad(request, lista)
