"""Putanja sifre posla do centra, po periodima vazenja (plan prelaska na registar, 3.1).

Verzija posla kaze kojoj jedinici posao pripada i od kada do kada; verzija jedinice kaze kom
centru pripada jedinica. Presek ta dva perioda (i perioda verzije centra, zbog oznake) je
jedan red `OrgPutanja`. Tabela se pravi iz verzija pri svakom uvozu i menja se samo kad se
verzije promene — ponovljen uvoz je ne dira.

**Prvi snimak vazi unazad** (odluka 28.09.2026.): registar je prvi put uvezen 21.09.2026., a istorija
pre toga nije poznata. Prva verzija svakog cvora zato vazi od `POCETAK`, pa se starija knjizenja i
dokumenti vode po prvom poznatom stanju — isto kao u staroj organizaciji. Verzije se ne menjaju;
promena posle uvoza (nova verzija od datuma) i dalje razdvaja stare i nove dokumente.
"""

import datetime
from collections import defaultdict

from django.db import transaction
from django.db.models import F, Q

from organizacija.models import OrgNode, OrgNodeVersion, OrgPutanja

KRAJ = datetime.date.max
POCETAK = datetime.date(2000, 1, 1)


def _preklapanje(od1, do1, od2, do2):
    od, do = max(od1, od2), min(do1 or KRAJ, do2 or KRAJ)
    return (od, None if do == KRAJ else do) if od < do else None


def zeljene_putanje(company=1):
    """Redovi putanje izracunati iz verzija: (posao, jedinica, centar, oznaka, od, do)."""
    po_cvoru = defaultdict(list)
    nivo = {}
    for v in OrgNodeVersion.objects.filter(node__company=company).select_related("node").order_by("valid_from", "pk"):
        po_cvoru[v.node_id].append(v)
        nivo[v.node_id] = v.node.level

    def od(verzija):
        return POCETAK if verzija is po_cvoru[verzija.node_id][0] else verzija.valid_from

    redovi = []
    for posao, verzije_posla in po_cvoru.items():
        if nivo[posao] != OrgNode.LEVEL_JOB:
            continue
        for vp in verzije_posla:
            for vj in po_cvoru.get(vp.parent_id, []):
                period = _preklapanje(od(vp), vp.valid_to, od(vj), vj.valid_to)
                if not period:
                    continue
                for vc in po_cvoru.get(vj.parent_id, []):
                    presek = _preklapanje(period[0], period[1], od(vc), vc.valid_to)
                    if presek:
                        redovi.append((posao, vp.parent_id, vj.parent_id, vc.full_code, presek[0], presek[1]))
    return _spoji(sorted(redovi, key=lambda r: (r[0], r[4])))


def _spoji(redovi):
    """Susedni periodi sa istom jedinicom, centrom i oznakom postaju jedan red."""
    spojeni = []
    for red in redovi:
        if spojeni:
            p = spojeni[-1]
            if p[:4] == red[:4] and p[5] == red[4]:
                spojeni[-1] = p[:5] + (red[5],)
                continue
        spojeni.append(red)
    return spojeni


@transaction.atomic
def izgradi(company=1):
    """Uskladjuje tabelu putanja sa verzijama. Vraca (bilo, sada, promenjeno)."""
    zeljene = zeljene_putanje(company)
    postojece = sorted(
        OrgPutanja.objects.filter(posao__company=company)
        .values_list("posao_id", "jedinica_id", "centar_id", "centar_sifra", "vazi_od", "vazi_do"),
        key=lambda r: (r[0], r[4]),
    )
    if list(postojece) == zeljene:
        return len(postojece), len(zeljene), False
    OrgPutanja.objects.filter(posao__company=company).delete()
    OrgPutanja.objects.bulk_create(
        [OrgPutanja(posao_id=p, jedinica_id=j, centar_id=c, centar_sifra=s, vazi_od=od, vazi_do=do)
         for p, j, c, s, od, do in zeljene],
        batch_size=500,
    )
    return len(postojece), len(zeljene), True


def centar_na_dan(posao_id, dan):
    """Oznaka centra sifre posla na dan, ili None."""
    red = (
        OrgPutanja.objects.filter(posao_id=posao_id, vazi_od__lte=dan)
        .filter(Q(vazi_do__isnull=True) | Q(vazi_do__gt=dan))
        .values_list("centar_sifra", flat=True)
        .first()
    )
    return red


def filter_na_dan(polje_cvora, polje_datuma, **uslovi):
    """`Q` za upit „zapis cija je sifra posla na datum dokumenta pripadala ...".

    Primer: `LedgerEntry.objects.filter(filter_na_dan("org_node", "booking_date", centar_sifra="43"))`.
    Svi uslovi idu na isti red putanje, pa se period i centar proveravaju zajedno.
    """
    prefiks = f"{polje_cvora}__putanje__"
    q = Q(**{f"{prefiks}vazi_od__lte": F(polje_datuma)}) & (
        Q(**{f"{prefiks}vazi_do__isnull": True}) | Q(**{f"{prefiks}vazi_do__gt": F(polje_datuma)})
    )
    for kljuc, vrednost in uslovi.items():
        q &= Q(**{f"{prefiks}{kljuc}": vrednost})
    return q


def centar_za(company=1):
    """Funkcija (cvor, dan) → oznaka centra ili None, iz jednog citanja tabele putanja."""
    periodi = defaultdict(list)
    for posao, sifra, od, do in OrgPutanja.objects.filter(posao__company=company).values_list(
            "posao_id", "centar_sifra", "vazi_od", "vazi_do"):
        periodi[posao].append((od, do, sifra))

    def centar(cvor, dan):
        for od, do, sifra in periodi.get(cvor, ()):
            if od <= dan and (do is None or dan < do):
                return sifra
        return None

    return centar


def centri_sifara(company=1, dan=None):
    """Sifra posla (kako je vode Finansije i Potrazivanja) → oznaka centra u registru na dan ("" bez centra)."""
    from organizacija.models import ExternalOrgMapping

    centar, dan = centar_za(company), dan or datetime.date.today()
    return {sifra: centar(cvor, dan) or "" for sifra, cvor in ExternalOrgMapping.objects.filter(
        source=ExternalOrgMapping.SOURCE_FINANCE_JOB, company=company, valid_to__isnull=True)
        .values_list("source_key", "node_id")}


def osvezi_centre(queryset, polje_cvora="org_node", polje_datuma="booking_date", polje_centra="org_centar"):
    """Snimak centra iz registra na dokumentu: `polje_centra` = centar sifre posla na datum dokumenta.

    Menja samo redove koji se razlikuju, pa je ponovljeno pokretanje bez upisa. Zapis bez cvora
    nema centar. Vraca broj izmenjenih redova.
    """
    promenjeno = 0
    for posao, sifra, od, do in OrgPutanja.objects.values_list("posao_id", "centar_sifra", "vazi_od", "vazi_do"):
        uslov = Q(**{polje_cvora: posao, f"{polje_datuma}__gte": od})
        if do:
            uslov &= Q(**{f"{polje_datuma}__lt": do})
        promenjeno += queryset.filter(uslov).exclude(**{polje_centra: sifra}).update(**{polje_centra: sifra})
    promenjeno += (queryset.filter(**{f"{polje_cvora}__isnull": True})
                   .exclude(**{f"{polje_centra}__isnull": True}).update(**{polje_centra: None}))
    return promenjeno
