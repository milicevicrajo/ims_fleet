"""Moj profil → Pregled (od 02.10.2026.): podaci zaposlenog o sebi na jednom mestu.

Samo čita evidencije koje zaposleni već vidi na svojim karticama profila. Godišnji odmor:
dodeljeni dani i dani po rešenjima iz kadrovske baze. Razlika je „preostalo prema rešenjima” —
dani po rešenju nisu potvrđeno korišćenje (vidi napomenu na kartici Godišnji odmori), pa to nije
obračun salda, nego pregled.
"""
import datetime

from django.db.models import Q, Sum

from hr.models import AnnualLeaveAllowance, AnnualLeaveDecision

MESECI = ["januar", "februar", "mart", "april", "maj", "jun", "jul", "avgust", "septembar", "oktobar",
          "novembar", "decembar"]


def godisnji_odmor(employee, danas):
    """Godine prava (tekuća i prethodna) sa dodeljenim danima, danima po rešenjima i razlikom."""
    dodele = {a.year: a.allocated_days for a in AnnualLeaveAllowance.objects.filter(
        employee=employee, source_present=True, year__in=(danas.year - 1, danas.year))}
    po_resenjima = dict(AnnualLeaveDecision.objects.filter(employee=employee, source_present=True, year__in=dodele)
                        .values("year").annotate(dana=Sum("approved_days")).order_by().values_list("year", "dana"))
    godine = []
    for godina in sorted(dodele, reverse=True):
        iskorisceno = po_resenjima.get(godina) or 0
        preostalo = max(dodele[godina] - iskorisceno, 0)
        if godina < danas.year and not preostalo:
            continue  # prethodna godina samo ako je ostalo dana
        godine.append({"godina": godina, "dodeljeno": dodele[godina], "po_resenjima": iskorisceno, "preostalo": preostalo,
                       "procenat": min(round(100 * iskorisceno / dodele[godina]), 100) if dodele[godina] else 0})
    sledeci = (AnnualLeaveDecision.objects.filter(employee=employee, source_present=True, end_date__gte=danas)
               .order_by("start_date").first())
    return {"godine": godine, "sledeci": sledeci, "u_toku": bool(sledeci and sledeci.start_date <= danas)}


def tekuci_ugovor(ugovori, danas):
    """Ugovor koji danas važi (poslednji počeo), iz kadrovske baze."""
    return (ugovori.filter(u_izvoru=True, datum_od__lte=danas)
            .filter(Q(na_neodredjeno=True) | Q(datum_do__isnull=True) | Q(datum_do__gte=danas))
            .order_by("-datum_od", "-redni_broj").first())


def staz(od, danas):
    if not od or od > danas:
        return None
    meseci = (danas.year - od.year) * 12 + danas.month - od.month - (danas.day < od.day)
    return {"godina": meseci // 12, "meseci": meseci % 12}


def organizaciona_jedinica(employee):
    """(šifra, naziv) čvora registra na kartici zaposlenog, i centar iznad njega."""
    from organizacija.models import OrgNode

    cvor = employee.org_node
    if not cvor:
        return None
    verzija = cvor.current_version
    if not verzija:
        return None
    centar = None
    if cvor.level != OrgNode.LEVEL_CENTER and verzija.parent_id:
        centar = verzija.parent.current_version
    return {"sifra": verzija.full_code, "naziv": verzija.name,
            "centar": (centar.full_code, centar.name) if centar else None}


def pregled(employee, ctx, danas=None):
    """Dodaje u kontekst profila deo „Pregled”; koristi već pripremljene upite profila."""
    danas = danas or datetime.date.today()
    radna_lista = next((s for s in ctx["work_time_sheets"] if (s.year, s.month) == (danas.year, danas.month)), None)
    ugovor = tekuci_ugovor(ctx["ugovori_zaposlenog"], danas)
    return {
        "danas": danas,
        "mesec": f"{MESECI[danas.month - 1]} {danas.year}.",
        "radna_lista": radna_lista,
        "godisnji": godisnji_odmor(employee, danas),
        "ugovor": ugovor,
        "ugovor_istice": (ugovor.datum_do - danas).days if ugovor and ugovor.datum_do and not ugovor.na_neodredjeno else None,
        "staz": staz(employee.date_of_joining, danas),
        "oj": organizaciona_jedinica(employee),
        "zahtevi": list(ctx["zahtevi"][:4]),
        "resenja": list(ctx["resenja"][:4]),
        "putni_neopravdani": ctx["travel_orders"].filter(opravdan=False, storniran=False).count(),
        "zaduzenje_vozila": ctx["vehicle_travel_orders"].filter(closed_at__isnull=True).first(),
    }
