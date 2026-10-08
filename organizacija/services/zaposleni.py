"""Zaposleni u registru organizacije (plan prelaska na registar, korak 7; odluka 28.09.2026.).

Nema posebne kadrovske organizacije: zaposleni pripada **cvoru registra** (jedinici ili centru),
zapisanom na kartici zaposlenog (`Employee.org_node`). Cvor se izvodi iz OJ koju salje kadrovska
baza, jednom i istim pravilom za sve:

1. OJ istog broja kao jedinica registra → ta jedinica (411, 431, …);
2. OJ istog broja kao centar → taj centar (41, 43, …); oznaka `20` je centar `2`, `30` centar `3`;
3. pododeljenje jedinice — najduzi jednoznacan prefiks jedinice → ta jedinica (4331 i 4332 → 433, 4110 → 411;
   od 08.10.2026., da rukovodilac jedinice vidi svoje ljude);
4. inace najduzi jednoznacan prefiks centra → centar (423 → 42), kao i dosad u Kadrovima;
5. ostalo (`1`, `10` — Institut kao celina, prazno) nema cvor i vidi ga samo obuhvat cele firme.

Veza se postavlja pri cuvanju zaposlenog i nocu (01:40, posle preuzimanja iz kadrovske baze u 01:10).
"""
from organizacija.models import OrgNode, OrgNodeVersion
from organizacija.services import classification as klas


def mape_registra(company=1):
    """(centri po oznaci, jedinice po oznaci → (cvor, cvor centra)) iz vazecih verzija."""
    verzije = list(OrgNodeVersion.objects.filter(valid_to__isnull=True, node__company=company, node__level__in=(
        OrgNode.LEVEL_CENTER, OrgNode.LEVEL_UNIT)).values_list("node_id", "node__level", "full_code", "parent_id"))
    centri = {code: node for node, level, code, _ in verzije if level == OrgNode.LEVEL_CENTER}
    jedinice = {code: (node, parent) for node, level, code, parent in verzije if level == OrgNode.LEVEL_UNIT}
    return centri, jedinice


def cvor_oj(sifra, mape):
    """Cvor registra za OJ iz kadrovske baze, ili None."""
    centri, jedinice = mape
    sifra = (sifra or "").strip()
    if not sifra:
        return None
    if sifra in jedinice:
        return jedinice[sifra][0]
    oznaka = klas.oznaka_centra(sifra)
    if oznaka in centri:
        return centri[oznaka]
    jedinica = _najduzi_prefiks(sifra, jedinice)
    if jedinica:
        return jedinice[jedinica][0]
    centar = _najduzi_prefiks(sifra, centri)
    return centri[centar] if centar else None


def _najduzi_prefiks(sifra, oznake):
    """Najduza oznaka koja je prefiks sifre, ako je jednoznacna; inace None."""
    kandidati = [o for o in oznake if sifra.startswith(o)]
    if not kandidati:
        return None
    najduzi = max(len(o) for o in kandidati)
    najbolji = [o for o in kandidati if len(o) == najduzi]
    return najbolji[0] if len(najbolji) == 1 else None


def oj_zaposlenog(employee):
    return str(employee.org_unit_code or employee.department_code or "").strip()


def povezi_zaposlene(company=1):
    """Uskladjuje `Employee.org_node` sa OJ iz kadrovske baze. Vraca broj izmenjenih zaposlenih."""
    from hr.models import Employee

    mape = mape_registra(company)
    promenjeno = 0
    for pk, oj, department, cvor in Employee.objects.values_list("pk", "org_unit_code", "department_code", "org_node_id"):
        novi = cvor_oj(str(oj or department or "").strip(), mape)
        if novi != cvor:
            promenjeno += Employee.objects.filter(pk=pk).update(org_node_id=novi)
    return promenjeno


def cvorovi_obuhvata(obuhvat_):
    """Cvorovi zaposlenih u obuhvatu: dodeljeni centri i jedinice, i jedinice dodeljenih centara.

    Obuhvat sifre posla ne daje ljude. None znaci cela firma.
    """
    if obuhvat_.cela_firma:
        return None
    cvorovi = set(obuhvat_.centri) | set(obuhvat_.jedinice)
    if obuhvat_.centri:
        cvorovi.update(OrgNodeVersion.objects.filter(valid_to__isnull=True, node__level=OrgNode.LEVEL_UNIT,
                                                     parent_id__in=obuhvat_.centri).values_list("node_id", flat=True))
    return cvorovi
