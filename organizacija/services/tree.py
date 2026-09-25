"""Stablo za prikaz: deo pravilnika → centar → jedinica → posao.

Cita **samo vazece verzije** (`valid_to IS NULL`) i slaze ih u ugnjezdenu strukturu.
Pripadnost se uzima iz `parent` veze u verziji, nikad iz secenja sifre — zato ovde i
nema nijednog rada sa prefiksima. Grupisanje centara po delovima Pravilnika o organizaciji
(npr. 41–44 su Poslovno-razvojni blok) je samo prikaz, ne nivo u registru.
"""

import re
from collections import defaultdict

from organizacija.models import OrgNode, OrgNodeVersion, UnresolvedOrgCode
from organizacija.services import classification as klas
from organizacija.services import pravilnik

# Predlog naziva jedinice koja nema potvrdjen naziv. Nista od ovoga se ne upisuje u registar.
# - posao `…111` u jedinici nosi ime laboratorije ili odeljenja (411111 „Kamen i agregat");
# - jedinica sa cifrom `0` drzi zajednicke troskove centra (amortizacija, rezija);
# - naucni projekat: oznaka projekta iz naziva njegovih sifara („TD 7024", „P19020").
POSAO_SA_NAZIVOM_JEDINICE = "111"
PREDLOG_ZAJEDNICKO = "Zajednički troškovi centra"
PREDLOG_ZBIRNI = "Zbirne institutske teme"
PREDLOG_BEZ_PROJEKTA = "Istraživači bez projekta (šifra samog radnika)"
# Jedinica knjizenja za centre ciji se oznaka razlikuje (centar 3 se knjizi na OJ 30).
JEDINICA_KNJIZENJA = {oznaka: jedinica for jedinica, oznaka in klas.OZNAKA_CENTRA_IZ_KNJIZENJA.items()}


def _redosled_sifre(code):
    """Brojevni redosled (2, 3, 11, 41 …); nebrojevne sifre idu na kraj."""
    return (0, int(code), code) if code.isdigit() else (1, 0, code)


def current_versions(company=1):
    return (
        OrgNodeVersion.objects.filter(valid_to__isnull=True, node__company=company)
        .select_related("node")
        .order_by("full_code")
    )


# Dozvoljene vrednosti filtera. Nepoznata vrednost se ignorise, ne ruši prikaz.
STATUS_CHOICES = ("aktivni", "neaktivni")
PROFIT_CHOICES = ("profitni", "neprofitni", "nepoznato")


def job_passes(job, status="", profit=""):
    """Da li posao prolazi filtere oznaka."""
    if status == "aktivni" and not job["is_active"]:
        return False
    if status == "neaktivni" and job["is_active"]:
        return False
    if profit == "profitni" and job["is_profit"] is not True:
        return False
    if profit == "neprofitni" and job["is_profit"] is not False:
        return False
    if profit == "nepoznato" and job["is_profit"] is not None:
        return False
    return True


def build_tree(company=1, query="", status="", profit=""):
    """Vraca listu centara sa jedinicama i poslovima.

    `query` filtrira po sifri ili nazivu na bilo kom nivou; grana se zadrzava ako
    sama odgovara ili ako joj neki potomak odgovara, da se pogodak vidi u kontekstu.

    `status` i `profit` filtriraju po oznakama posla. Kad je bilo koji filter ukljucen,
    prazne grane se **izbacuju** — inace bi ekran bio pun centara bez ijednog reda.
    """
    versions = list(current_versions(company))
    by_node = {version.node_id: version for version in versions}

    children = defaultdict(list)
    roots = []
    for version in versions:
        if version.node.level == OrgNode.LEVEL_CENTER:
            roots.append(version)
        elif version.parent_id in by_node:
            children[version.parent_id].append(version)

    radnici = _radnici_nauke(versions)
    needle = (query or "").strip().lower()
    status = status if status in STATUS_CHOICES else ""
    profit = profit if profit in PROFIT_CHOICES else ""
    flagged = bool(status or profit)
    filtering = bool(needle or flagged)

    tree = []
    for center in sorted(roots, key=lambda item: _redosled_sifre(item.full_code)):
        # Pogodak na centru zadrzava ceo njegov sadrzaj — inace bi pretraga po nazivu
        # centra vratila prazan centar umesto onoga sto se u njemu nalazi.
        center_hit = bool(needle) and _matches(center, needle)
        units = []
        for unit in sorted(children[center.node_id], key=lambda item: _redosled_sifre(item.full_code)):
            jobs = [_job(job, needle, radnici) for job in sorted(children[unit.node_id], key=lambda i: i.full_code)]
            if flagged:
                jobs = [job for job in jobs if job_passes(job, status, profit)]
            predlog = ("", "") if unit.name else predlog_naziva_jedinice(unit, children[unit.node_id])
            if needle and not center_hit:
                unit_hit = _matches(unit, needle) or needle in predlog[0].lower()
                jobs = jobs if unit_hit else [job for job in jobs if job["match"]]
                if not unit_hit and not jobs:
                    continue
            if flagged and not jobs:
                continue
            units.append(_unit(unit, jobs, predlog))
        if filtering and not units:
            continue
        tree.append(_center(center, units, radnici))
    return tree


def po_delovima(tree):
    """Centri grupisani po delovima Pravilnika o organizaciji, redom delova (clan 3)."""
    grupe = []
    for center in tree:
        deo = pravilnik.deo_centra(center["code"])
        if grupe and grupe[-1]["deo"] == deo and deo is not None:
            grupe[-1]["centri"].append(center)
            continue
        grupe.append({"deo": deo, "naziv": pravilnik.DELOVI.get(deo, ""), "centri": [center]})
    for grupa in grupe:
        grupa["vise"] = len(grupa["centri"]) > 1
    return grupe


def _matches(version, needle):
    return needle in version.full_code.lower() or needle in (version.name or "").lower()


def _job(version, needle="", radnici=None):
    radnik = (radnici or {}).get(version.full_code)
    return {
        "code": version.full_code,
        "segment": version.segment,
        "name": version.name,
        "is_active": version.is_active,
        "is_profit": version.is_profit,
        "node_id": version.node_id,
        "radnik": radnik,
        "match": bool(needle) and (_matches(version, needle) or bool(radnik and needle in (radnik["ime"] or "").lower())),
    }


def _radnici_nauke(versions):
    """Naucna sifra → radnik iz Kadrova (`naucnici.povezi`: po licnom broju, pa po imenu)."""
    from organizacija.services import naucnici

    return naucnici.povezi({
        v.full_code: v.name for v in versions if v.node.level == OrgNode.LEVEL_JOB and klas.je_nauka(v.full_code)
    })


def _unit(version, jobs, predlog=("", "")):
    return {
        "code": version.full_code,
        "segment": version.segment,
        "name": version.name,
        "predlog": predlog[0],
        "predlog_razlog": predlog[1],
        "node_id": version.node_id,
        "jobs": jobs,
        "job_count": len(jobs),
        "active_jobs": sum(1 for job in jobs if job["is_active"]),
    }


def predlog_naziva_jedinice(unit, poslovi):
    """(predlog, razlog) za jedinicu bez potvrdjenog naziva; prazno ako pravilo ne daje odgovor."""
    code = unit.full_code
    if code in pravilnik.PROVERITI:
        return pravilnik.PROVERITI[code]
    if code.startswith(klas.PREFIKS_PROJEKTA):
        broj = code[len(klas.PREFIKS_PROJEKTA):]
        if broj == "00":
            return PREDLOG_BEZ_PROJEKTA, "Koren šifre: 3 + radnik + 00."
        oznaka = oznaka_projekta(posao.name for posao in poslovi)
        razlog = f"Naučni projekat {broj}; broj je slobodan unos, oznaka je iz naziva šifara."
        return (oznaka or f"Projekat {broj}"), razlog
    if len(code) == 4 and code.startswith("3") and code[1:] in klas.ZBIRNI_NOSIOCI_NAUKE:
        return PREDLOG_ZBIRNI, "Nosilac nije radnik nego zbirna institutska tema."
    if unit.segment == "0":
        return PREDLOG_ZAJEDNICKO, "Jedinica sa cifrom 0 drži amortizaciju i režiju centra."
    for posao in poslovi:
        if posao.segment == POSAO_SA_NAZIVOM_JEDINICE and (posao.name or "").strip():
            return posao.name.strip(), "Iz naziva posla …111 jedinice; pravilnik je ne navodi pod ovim brojem."
    return "", ""


def _center(version, units, radnici=None):
    jobs = sum(unit["job_count"] for unit in units)
    ljudi = _zbir_ljudi(units) if radnici else None
    return {
        "code": version.full_code,
        "name": version.name,
        "oj_knjizenja": JEDINICA_KNJIZENJA.get(version.full_code, ""),
        "node_id": version.node_id,
        "units": units,
        "unit_count": len(units),
        "job_count": jobs,
        "active_jobs": sum(unit["active_jobs"] for unit in units),
        "ljudi": ljudi,
    }


def _zbir_ljudi(units):
    """Koliko razlicitih nosilaca u centru je zaposleno, bivse ili za proveru (samo naucni blok)."""
    nosioci = {}
    for unit in units:
        for job in unit["jobs"]:
            if job.get("radnik"):
                nosioci[job["radnik"]["broj"]] = job["radnik"]["vrsta"]
    if not nosioci:
        return None
    vrste = list(nosioci.values())
    return {
        "zaposlenih": sum(1 for v in vrste if v == "zaposlen"),
        "bivsih": sum(1 for v in vrste if v in ("bivsi", "bivsi_u_kadrovima")),
        "provera": sum(1 for v in vrste if v == "ne_poklapa"),
    }


def totals(tree):
    return {
        "centers": len(tree),
        "units": sum(center["unit_count"] for center in tree),
        "jobs": sum(center["job_count"] for center in tree),
        "active_jobs": sum(center["active_jobs"] for center in tree),
    }


# Oznake projekta u nazivu naucne sifre: `P190170`, `P-42012`, `P 450080`, `TD 7024`,
# `TR 6351B`, `ON 142041`, `Pr. DAAD`, `Projekat PROMIS`.
OZNAKA_PROJEKTA = re.compile(
    r"(?i)\b(?:projekat\s+[^\s-]+|pr\.\s*[^\s-]+|(?:p|td|tr|on)\s*-?\s*\d+[a-z]?)\b"
)


def oznaka_projekta(nazivi):
    """Najcesca oznaka projekta u nazivima sifara: „TD 7024-Delic I." → „TD 7024"."""
    from collections import Counter

    oznake = Counter()
    for naziv in nazivi:
        for oznaka in OZNAKA_PROJEKTA.findall(naziv or ""):
            oznake[" ".join(oznaka.replace("-", " ").split())] += 1
    return oznake.most_common(1)[0][0] if oznake else ""


def unresolved_groups(run=None):
    """Nerazresene sifre iz poslednjeg uvoza, grupisane po porodici."""
    queryset = UnresolvedOrgCode.objects.all()
    if run is not None:
        queryset = queryset.filter(run=run)
    groups = defaultdict(list)
    for row in queryset.order_by("family", "code"):
        groups[row.family].append(row)
    labels = dict(UnresolvedOrgCode.FAMILY_CHOICES)
    return [
        {"family": family, "label": labels.get(family, family), "rows": rows, "count": len(rows)}
        for family, rows in sorted(groups.items())
    ]


# Redosled i nazivi filtera u prikazu. Svaki je veza, ne JavaScript — pa radi i sa
# otvaranjem u novoj kartici, i ostaje u istoriji pregledaca.
FILTER_BUTTONS = (
    ("status", "", "Svi"),
    ("status", "aktivni", "Samo aktivni"),
    ("status", "neaktivni", "Prikaži neaktivne"),
    ("profit", "profitni", "Profitni"),
    ("profit", "neprofitni", "Neprofitni"),
    ("profit", "nepoznato", "Oznaka nepoznata"),
)


def filter_links(query="", status="", profit=""):
    """Gradi spisak filtera sa upitnim delom adrese i oznakom da li je ukljucen.

    Klik na vec ukljucen filter ga **iskljucuje**, pa je svako dugme prekidac.
    """
    from urllib.parse import urlencode

    current = {"status": status, "profit": profit}
    links = []
    for field, value, label in FILTER_BUTTONS:
        active = current.get(field, "") == value
        params = dict(current)
        params[field] = "" if active and value else value
        if field == "status" and value == "":
            params = {"status": "", "profit": ""}
        if query:
            params["q"] = query
        query_string = urlencode({k: v for k, v in params.items() if v})
        links.append(
            {
                "label": label,
                "field": field,
                "value": value,
                "active": active if value else not (status or profit),
                "url": ("?" + query_string) if query_string else "?",
            }
        )
    return links
