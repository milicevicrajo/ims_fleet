"""CSV za učitavanje obračuna zarada iz radnih lista (od 09.10.2026.): jedan radnik ili svi radnici za mesec."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.exporting import csv_attachment_response
from core.mixins import role_permission_required

from .access import visible_employees
from .services import obracun_csv


def _br_obr(request):
    try:
        broj = int(request.GET.get("br_obr", ""))
    except ValueError:
        return None
    return broj if 1 <= broj <= 99 else None


def _odgovor(naziv, redovi, upozorenja):
    response = csv_attachment_response(naziv)
    response["X-Upozorenja"] = str(len(upozorenja))
    return obracun_csv.upisi(response, redovi)


@login_required
@role_permission_required()
def work_time_sheet_csv(request, pk):
    """Jedna radna lista (radnik iz obuhvata korisnika)."""
    br_obr = _br_obr(request)
    if br_obr is None:
        return HttpResponseBadRequest("Upišite broj obračuna (1–99).")
    lista = get_object_or_404(obracun_csv.listovi(visible_employees(request.user)), pk=pk)
    redovi, upozorenja = obracun_csv.stavke([lista], br_obr)
    return _odgovor(f"obracun_{lista.year}_{lista.month:02d}_obr{br_obr}_{lista.employee.employee_code}.csv", redovi, upozorenja)


@login_required
@role_permission_required()
def work_time_sheets_csv(request):
    """Sve radne liste meseca za radnike iz obuhvata korisnika."""
    br_obr = _br_obr(request)
    danas = timezone.localdate()
    try:
        godina, mesec = int(request.GET.get("year", danas.year)), int(request.GET.get("month", danas.month))
    except ValueError:
        return HttpResponseBadRequest("Neispravan period.")
    if br_obr is None or not (2000 <= godina <= 2100 and 1 <= mesec <= 12):
        return HttpResponseBadRequest("Upišite broj obračuna (1–99) i ispravan period.")
    redovi, upozorenja = obracun_csv.stavke(obracun_csv.listovi_meseca(visible_employees(request.user), godina, mesec), br_obr)
    return _odgovor(f"obracun_{godina}_{mesec:02d}_obr{br_obr}_svi.csv", redovi, upozorenja)
