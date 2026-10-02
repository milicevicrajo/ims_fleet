"""DataTables sa obradom na serveru (Isplate): isti URL vraća stranu, a uz `draw` — JSON za tabelu.

Ruta je ista, pa je i dozvola ista (kod = naziv rute); nije potrebna posebna ruta „…_data”.
"""
from django.http import JsonResponse


def je_zahtev_tabele(request):
    return "draw" in request.GET


def strana(g):
    try:
        start = max(int(g.get("start", 0)), 0)
        duzina = min(max(int(g.get("length", 50)), 1), 200)
        draw = int(g.get("draw", 0))
    except (TypeError, ValueError):
        return 0, 50, 0
    return start, duzina, draw


def redosled(g, kolone, podrazumevano):
    """Polje za `order_by`; bez izbora kolone — podrazumevano polje, opadajuće."""
    kolona = g.get("order[0][column]")
    if kolona not in kolone:
        return f"-{podrazumevano}"
    return ("" if g.get("order[0][dir]") == "asc" else "-") + kolone[kolona]


def reci(g):
    """Reči pretrage: polje `q` (link sa drugog ekrana) i polje pretrage tabele."""
    return (g.get("q") or "").split() + (g.get("search[value]") or "").split()


def odgovor(draw, ukupno, filtrirano, redovi, **dodatno):
    return JsonResponse({"draw": draw, "recordsTotal": ukupno, "recordsFiltered": filtrirano, "data": redovi, **dodatno})
