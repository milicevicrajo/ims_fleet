"""JSON: poslednja očitana kilometraža vozila do datuma unosa (za napomenu ispod polja kilometraže).

Namerno bez provere dozvole po ruti: koriste ga sve forme sa kilometražom (gorivo, zaduženja,
servisi, trebovanja, kvarovi), a vraća samo broj kilometara za vozilo u obuhvatu korisnika.
"""
import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from ..models import Vehicle
from ..support import obuhvat as obuhvat_flote
from ..support.garaza import NAJMANJI_DOZVOLJEN_SKOK_KM, NAJVISE_KM_DNEVNO, poslednja_kilometraza


def _dan(tekst):
    tekst = (tekst or "").strip()[:10]
    for oblik in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(tekst, oblik).date()
        except ValueError:
            continue
    return timezone.localdate()


@login_required
def vozilo_kilometraza(request):
    vozilo_id = request.GET.get("vozilo", "")
    if not vozilo_id.isdigit():
        return JsonResponse({})
    vozilo = obuhvat_flote.po_vozilu(Vehicle.objects.filter(pk=int(vozilo_id)), request.user, "pk").first()
    if vozilo is None:
        return JsonResponse({})
    dan = min(_dan(request.GET.get("datum")), timezone.localdate())
    poslednja = poslednja_kilometraza(vozilo, dan=dan)
    return JsonResponse({
        "dan": dan.isoformat(),
        "kilometraza": poslednja and {"km": poslednja["value"], "datum": poslednja["date"].strftime("%d.%m.%Y."),
                                      "datum_iso": poslednja["date"].isoformat(), "izvor": poslednja["source"]},
        "pravilo": {"km_dnevno": NAJVISE_KM_DNEVNO, "najmanji_skok": NAJMANJI_DOZVOLJEN_SKOK_KM},
    })
