"""Centri i organizacione jedinice za arhivu: izbor u pisarnici i nazivi za prikaz.

Registar upisuje naziv OJ samo kada je potvrđen (Pravilnik o organizaciji i sl.), pa mnoge OJ
u registru nemaju naziv. Arhiva tada prikazuje isti naziv koji prikazuje **stablo organizacije**
— predlog iz `organizacija.services.tree.predlog_naziva_jedinice` (lista „proveriti” iz
Pravilnika, „Zajednički troškovi centra” za jedinicu sa cifrom 0, naziv posla `…111`) — a ako
ga nema, naziv iz kadrovske evidencije (OJ sa ugovora zaposlenih). Tek ako nema ni toga:
„bez naziva u registru”. Ništa od ovoga se ne upisuje u registar.

Naučni projekti (jedinice bloka 3 sa šifrom `3-…`, AGENTS.md zamka 11) se ne nude: pošta se
zavodi na centar ili OJ, ne na projekat.
"""
from collections import defaultdict

from organizacija.models import OrgNode, OrgNodeVersion

BEZ_NAZIVA = "bez naziva u registru"
PREFIKS_NAUCNOG_PROJEKTA = "3-"


def _nazivi_iz_kadrova(sifre):
    from hr.models import UgovorZaposlenog

    nazivi = {}
    for oj, naziv in (UgovorZaposlenog.objects.filter(oj__in=sifre).exclude(naziv_oj="")
                      .order_by("oj", "-podaci_zabelezeni", "-pk").values_list("oj", "naziv_oj")):
        nazivi.setdefault(oj, naziv.strip())
    return nazivi


def _predlozi_stabla(jedinice):
    """{node_id: predlog naziva} kao u stablu organizacije, za jedinice bez potvrđenog naziva."""
    from organizacija.services.tree import predlog_naziva_jedinice

    if not jedinice:
        return {}
    poslovi = defaultdict(list)
    for posao in OrgNodeVersion.objects.filter(valid_to__isnull=True, parent_id__in=[v.node_id for v in jedinice]):
        poslovi[posao.parent_id].append(posao)
    return {v.node_id: predlog_naziva_jedinice(v, poslovi[v.node_id])[0] for v in jedinice}


def oznake(verzije):
    """{node_id: „šifra · naziv”} za važeće verzije čvorova (`OrgNodeVersion`)."""
    bez = [v for v in verzije if not (v.name or "").strip()]
    stablo = _predlozi_stabla([v for v in bez if v.node.level == OrgNode.LEVEL_UNIT])
    kadrovi = _nazivi_iz_kadrova([v.full_code for v in bez if not stablo.get(v.node_id)]) if bez else {}
    return {v.node_id: f"{v.full_code} · {(v.name or '').strip() or stablo.get(v.node_id) or kadrovi.get(v.full_code) or BEZ_NAZIVA}"
            for v in verzije}


def oznake_cvorova(node_ids):
    return oznake(list(OrgNodeVersion.objects.filter(node_id__in=node_ids, valid_to__isnull=True).select_related("node")))


def izbor():
    """Izbor za pisarnicu, grupisan po centrima: centar (ceo centar) pa njegove OJ."""
    verzije = list(OrgNodeVersion.objects.filter(valid_to__isnull=True, node__level__in=[OrgNode.LEVEL_CENTER, OrgNode.LEVEL_UNIT])
                   .exclude(node__level=OrgNode.LEVEL_UNIT, full_code__startswith=PREFIKS_NAUCNOG_PROJEKTA)
                   .select_related("node").order_by("full_code"))
    natpisi = oznake(verzije)
    jedinice = defaultdict(list)
    for v in verzije:
        if v.node.level == OrgNode.LEVEL_UNIT:
            jedinice[v.parent_id].append((str(v.node_id), natpisi[v.node_id]))
    grupe = []
    for v in verzije:
        if v.node.level == OrgNode.LEVEL_CENTER:
            natpis = natpisi[v.node_id]
            grupe.append((natpis, [(str(v.node_id), f"{natpis} (ceo centar)")] + jedinice.pop(v.node_id, [])))
    ostalo = [opcija for opcije in jedinice.values() for opcija in opcije]
    if ostalo:
        grupe.append(("Ostale OJ", ostalo))
    return grupe
