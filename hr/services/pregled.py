"""Kadrovi → Pregled (početna strana modula, od 02.10.2026.).

Samo broji i izdvaja ono što korisnik već vidi na spiskovima Kadrova: svaki deo traži dozvolu
odgovarajućeg spiska i ide kroz isti obuhvat (`hr.access`, `visible_zahtevi`, `visible_resenja`).
Ništa ne upisuje i ne čita izvan aplikacije.
"""
import datetime
from collections import Counter

from django.db.models import Exists, OuterRef, Q

from core.mixins import user_has_role_permission
from hr.access import scope_employee_records, visible_employees
from hr.models import AnnualLeaveDecision, SickLeave
from hr.resenja_models import Resenje
from hr.ugovori_models import UgovorZaposlenog
from hr.zahtevi_models import Zahtev

ISTEK_UGOVORA_DANA = 45
NOVI_ZAPOSLENI_DANA = 30
NAJVISE_REDOVA = 12


def _ime(employee):
    return str(employee) if employee else ""


def odsutni_danas(user, danas, godisnji=True, bolovanje=True):
    """Ko je danas na godišnjem odmoru (po rešenju) ili na bolovanju (RFZO)."""
    redovi = []
    if godisnji:
        qs = scope_employee_records(AnnualLeaveDecision.objects.select_related("employee"), user).filter(
            source_present=True, employee__isnull=False, employee__is_active=True,
            start_date__lte=danas, end_date__gte=danas)
        redovi += [{"employee": r.employee, "vrsta": "godisnji", "do": r.end_date} for r in qs]
    if bolovanje:
        qs = scope_employee_records(SickLeave.objects.select_related("employee"), user).filter(
            employee__isnull=False, employee__is_active=True, start_date__lte=danas).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=danas))
        redovi += [{"employee": r.employee, "vrsta": "bolovanje", "do": r.end_date} for r in qs]
    jedinstveni = {}
    for red in redovi:  # isti zaposleni dva puta (npr. preklopljeni zapisi) — jednom
        jedinstveni.setdefault((red["employee"].pk, red["vrsta"]), red)
    return sorted(jedinstveni.values(), key=lambda r: (r["employee"].last_name, r["employee"].first_name))


def ugovori_isticu(user, danas, dana=ISTEK_UGOVORA_DANA):
    """Tekući ugovori na određeno koji ističu u narednih `dana`, bez kasnijeg ugovora istog radnika."""
    from hr.ugovori_views import vidljivi

    kasniji = UgovorZaposlenog.objects.filter(employee_code=OuterRef("employee_code"), u_izvoru=True,
                                              datum_od__gt=OuterRef("datum_do"))
    return (vidljivi(user).filter(u_izvoru=True, radnik_aktivan=True, na_neodredjeno=False,
                                  datum_do__gte=danas, datum_do__lte=danas + datetime.timedelta(days=dana))
            .exclude(Exists(kasniji)).order_by("datum_do", "employee_code"))


def struktura_po_centrima(zaposleni):
    """[(centar, naziv, broj)] za aktivne zaposlene, po čvoru registra na kartici zaposlenog."""
    from organizacija.models import OrgNode, OrgNodeVersion

    po_cvoru = Counter(zaposleni.values_list("org_node_id", flat=True))
    verzije = {v["node_id"]: v for v in OrgNodeVersion.objects.filter(valid_to__isnull=True).values(
        "node_id", "node__level", "parent_id", "full_code", "name")}
    centri = Counter()
    for cvor, broj in po_cvoru.items():
        v = verzije.get(cvor)
        while v and v["node__level"] != OrgNode.LEVEL_CENTER and v["parent_id"]:
            v = verzije.get(v["parent_id"])
        kljuc = (v["full_code"], v["name"]) if v and v["node__level"] == OrgNode.LEVEL_CENTER else ("", "Bez centra u registru")
        centri[kljuc] += broj
    return sorted(((sifra, naziv, broj) for (sifra, naziv), broj in centri.items()),
                  key=lambda r: (r[0] == "", -r[2], r[0]))


def pregled(user, danas=None):
    danas = danas or datetime.date.today()
    prava = {kod: user_has_role_permission(user, kod) for kod in (
        "employee_list", "employee_detail", "hr:annual_leave_list", "hr:sick_leave_list", "hr:ugovor_list",
        "hr:ugovor_detail", "hr:zahtev_list", "hr:zahtev_create", "hr:resenje_list", "hr:resenje_create")}
    ctx = {"danas": danas, "moze": {k.replace("hr:", "").replace(":", "_"): v for k, v in prava.items()}}

    if prava["employee_list"]:
        aktivni = visible_employees(user).filter(is_active=True)
        struktura = struktura_po_centrima(aktivni)
        najvise = max((r[2] for r in struktura), default=0)
        ctx["zaposleni"] = {
            "aktivni": aktivni.count(),
            # Kadrovska baza upisuje ženski pol kao „Z”, a model kao „F” — broje se oba.
            "zene": aktivni.filter(gender__in=("F", "Z")).count(),
            "muskarci": aktivni.filter(gender="M").count(),
            "novi": list(aktivni.filter(date_of_joining__gt=danas - datetime.timedelta(days=NOVI_ZAPOSLENI_DANA))
                         .order_by("-date_of_joining", "last_name")[:NAJVISE_REDOVA]),
            "struktura": [{"sifra": s, "naziv": n, "broj": b, "procenat": round(100 * b / najvise) if najvise else 0}
                          for s, n, b in struktura],
        }

    if prava["hr:annual_leave_list"] or prava["hr:sick_leave_list"]:
        odsutni = odsutni_danas(user, danas, prava["hr:annual_leave_list"], prava["hr:sick_leave_list"])
        ctx["odsutni"] = {"redovi": odsutni[:NAJVISE_REDOVA], "ukupno": len(odsutni),
                          "godisnji": sum(r["vrsta"] == "godisnji" for r in odsutni),
                          "bolovanje": sum(r["vrsta"] == "bolovanje" for r in odsutni)}

    if prava["hr:ugovor_list"]:
        isticu = ugovori_isticu(user, danas)
        redovi = list(isticu.select_related("employee")[:NAJVISE_REDOVA])
        for red in redovi:
            red.preostalo = (red.datum_do - danas).days
        ctx["ugovori"] = {"redovi": redovi, "ukupno": isticu.count(), "dana": ISTEK_UGOVORA_DANA}

    if prava["hr:zahtev_list"]:
        from hr.services.zahtevi import visible_zahtevi

        zahtevi = visible_zahtevi(user)
        aktivno_resenje = Resenje.objects.filter(zahtev=OuterRef("pk")).exclude(status=Resenje.Status.STORNIRANO)
        cekaju = (zahtevi.filter(status=Zahtev.Status.PODNET).exclude(Exists(aktivno_resenje))
                  .order_by("-podneto_at", "-pk"))
        ctx["zahtevi"] = {"cekaju": list(cekaju[:8]), "cekaju_ukupno": cekaju.count(),
                          "nacrti": zahtevi.filter(status=Zahtev.Status.NACRT).count()}

    if prava["hr:resenje_list"]:
        from hr.services.resenja import visible_resenja

        resenja = visible_resenja(user)
        ctx["resenja"] = {"nacrti": resenja.filter(status=Resenje.Status.NACRT).count(),
                          "izdata_mesec": resenja.filter(status=Resenje.Status.IZDATO, datum_resenja__year=danas.year,
                                                         datum_resenja__month=danas.month).count()}
    return ctx
