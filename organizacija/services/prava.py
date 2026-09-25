"""Prava sa obuhvatom u stablu (plan prelaska na registar, 3.2; V2, koraci 2 i 4).

Tri dela, nijedan jos ne odlucuje o pristupu:

- `obuhvat` / `q_obuhvata` / `ima_pravo` — jedna provera: cela firma, ili skup cvorova
  (centar pokriva svoje jedinice i poslove, jedinica svoje poslove, posao samo sebe), na datum;
- `prevedi` — stara prava (`allowed_centers`, `allowed_center_codes`) u dodele u statusu `nacrt`;
- `senka` — za svakog korisnika: sta danas vidi u modulu, a sta bi video po nacrtu.

Odluke narucioca 25.09.2026.: dodeljena pojedinacna OJ prevodi se u **ceo njen centar**, kao
sto danas rade Finansije i Potrazivanja (ticalo bi se samo dva korisnika); **prazan obuhvat
znaci da korisnik ne vidi nista** — i u Floti, gde danas vidi sve.
"""

from collections import Counter
from dataclasses import dataclass, field

from django.db import transaction
from django.db.models import Count, F, Q
from django.utils import timezone

from organizacija.models import DodelaUloge, OrgNode, OrgNodeVersion, OrgPutanja
from organizacija.services import classification as klas

ULOGA_CELE_FIRME = "uprava"
# Uloge koje po prirodi posla rade za sve centre (odluka 25.09.2026.: Garaza radi sa svim centrima).
ULOGE_CELE_FIRME = {ULOGA_CELE_FIRME, "garaza"}
# Dozvola bez koje korisnik ne otvara modul — senka poredi samo module koje korisnik vidi.
ULAZ_MODULA = {"finansije": "finansije:dashboard", "potrazivanja": "potrazivanja:dashboard",
               "putni_nalozi": "putninalog_list"}


@dataclass
class Obuhvat:
    cela_firma: bool = False
    centri: set = field(default_factory=set)
    jedinice: set = field(default_factory=set)
    poslovi: set = field(default_factory=set)

    @property
    def prazan(self):
        return not (self.cela_firma or self.centri or self.jedinice or self.poslovi)


def _vazece(qs, dan):
    return qs.filter(vazi_od__lte=dan).filter(Q(vazi_do__isnull=True) | Q(vazi_do__gt=dan))


def obuhvat(korisnik, kod_dozvole=None, status=DodelaUloge.STATUS_AKTIVNA, dan=None):
    """Obuhvat korisnika za dozvolu (ili za bilo koju ulogu, kad je `kod_dozvole` None).

    Prazan obuhvat znaci **nema pristupa** (odluka 2 u planu). Superuser ima celu firmu.
    """
    dan = dan or timezone.localdate()
    if korisnik.is_superuser:
        return Obuhvat(cela_firma=True)
    dodele = _vazece(DodelaUloge.objects.filter(korisnik=korisnik, status=status, uloga__is_active=True), dan)
    if kod_dozvole:
        dodele = dodele.filter(uloga__permissions__code=kod_dozvole)
    rezultat = Obuhvat()
    for cela, cvor, nivo in dodele.values_list("cela_firma", "cvor_id", "cvor__level").distinct():
        if cela:
            rezultat.cela_firma = True
        elif nivo == OrgNode.LEVEL_CENTER:
            rezultat.centri.add(cvor)
        elif nivo == OrgNode.LEVEL_UNIT:
            rezultat.jedinice.add(cvor)
        elif nivo == OrgNode.LEVEL_JOB:
            rezultat.poslovi.add(cvor)
    return rezultat


def poslovi_obuhvata(obuhvat_, dan=None):
    """Svi cvorovi poslova u obuhvatu na dan (None znaci cela firma)."""
    if obuhvat_.cela_firma:
        return None
    dan = dan or timezone.localdate()
    putanje = _vazece(OrgPutanja.objects.all(), dan)
    poslovi = set(obuhvat_.poslovi)
    poslovi.update(putanje.filter(centar_id__in=obuhvat_.centri).values_list("posao_id", flat=True))
    poslovi.update(putanje.filter(jedinica_id__in=obuhvat_.jedinice).values_list("posao_id", flat=True))
    return poslovi


def q_obuhvata(obuhvat_, polje_cvora="org_node", polje_datuma=None):
    """`Q` za zapise u obuhvatu; sa `polje_datuma` pripadnost se gleda na datum dokumenta."""
    if obuhvat_.cela_firma:
        return Q()
    if obuhvat_.prazan:
        return Q(pk__in=[])
    q = Q(**{f"{polje_cvora}__in": obuhvat_.poslovi}) if obuhvat_.poslovi else Q(pk__in=[])
    prefiks = f"{polje_cvora}__putanje__"
    if polje_datuma:
        period = Q(**{f"{prefiks}vazi_od__lte": F(polje_datuma)}) & (
            Q(**{f"{prefiks}vazi_do__isnull": True}) | Q(**{f"{prefiks}vazi_do__gt": F(polje_datuma)}))
    else:
        period = Q(**{f"{prefiks}vazi_do__isnull": True})
    if obuhvat_.centri:
        q |= period & Q(**{f"{prefiks}centar_id__in": obuhvat_.centri})
    if obuhvat_.jedinice:
        q |= period & Q(**{f"{prefiks}jedinica_id__in": obuhvat_.jedinice})
    return q


def ima_pravo(korisnik, kod_dozvole, org_node_id, dan=None):
    """Da li korisnik sme da radi `kod_dozvole` nad zapisom sa tim cvorom posla (na dan)."""
    o = obuhvat(korisnik, kod_dozvole, dan=dan)
    if o.cela_firma:
        return True
    if o.prazan or org_node_id is None:
        return False
    return org_node_id in poslovi_obuhvata(o, dan)


# --------------------------------------------------------------------------- prevod starih prava


def _centri_registra():
    """Oznaka centra → cvor (vazece verzije prvog nivoa)."""
    return dict(OrgNodeVersion.objects.filter(valid_to__isnull=True, node__level=OrgNode.LEVEL_CENTER)
                .values_list("full_code", "node_id"))


def _oznake_iz_teksta(tekst):
    return [d.strip() for d in (tekst or "").replace(";", ",").split(",") if d.strip()]


@transaction.atomic
def prevedi(korisnici=None, dan=None):
    """Stara prava → dodele u statusu `nacrt` (ponovljivo: prethodni nacrt prevoda se zamenjuje).

    Vraca zbir: korisnika, dodela, i sta nije moglo da se prevede.
    """
    from core.models import CustomUser
    from organizacija.services.flota import Razresavac

    dan = dan or timezone.localdate()
    razresavac = Razresavac()
    centri = _centri_registra()
    putanje_danas = dict(_vazece(OrgPutanja.objects.all(), dan).values_list("posao_id", "centar_id"))
    korisnici = korisnici if korisnici is not None else CustomUser.objects.filter(is_active=True, is_superuser=False)
    zbir = {"korisnika": 0, "dodela": 0, "bez_uloge": 0, "nepoznate_oznake": Counter(), "oj_van_registra": Counter(),
            "kadrovske_oj": 0}
    DodelaUloge.objects.filter(korisnik__in=korisnici, status=DodelaUloge.STATUS_NACRT,
                               izvor=DodelaUloge.IZVOR_PREVOD).delete()
    nove = []
    for korisnik in korisnici.prefetch_related("roles", "allowed_centers"):
        uloge = [u for u in korisnik.roles.all() if u.is_active]
        if not uloge:
            zbir["bez_uloge"] += 1
            continue
        zbir["korisnika"] += 1
        obuhvati = []  # (cvor, cela_firma, napomena)
        for oznaka in _oznake_iz_teksta(korisnik.allowed_center_codes):
            centar = centri.get(klas.oznaka_centra(oznaka))
            if centar:
                obuhvati.append((centar, False, f"centar {oznaka} iz allowed_center_codes"))
            else:
                zbir["nepoznate_oznake"][oznaka] += 1
        for jedinica in korisnik.allowed_centers.all():
            posao = razresavac.za_jedinicu(jedinica.pk)
            centar_oj = putanje_danas.get(posao)
            if centar_oj:
                # Odluka 25.09.2026.: dodeljena OJ daje ceo svoj centar, kao sto danas rade moduli.
                obuhvati.append((centar_oj, False, f"OJ {jedinica.code.strip()} iz allowed_centers — ceo njen centar"))
            else:
                zbir["oj_van_registra"][jedinica.code.strip()] += 1
        if korisnik.allowed_hr_unit_codes:
            zbir["kadrovske_oj"] += 1  # ceka kadrovsku mapu (plan, 3.3)
        for uloga in uloge:
            if uloga.slug in ULOGE_CELE_FIRME:
                nove.append(DodelaUloge(korisnik=korisnik, uloga=uloga, cela_firma=True, vazi_od=dan,
                                        status=DodelaUloge.STATUS_NACRT, izvor=DodelaUloge.IZVOR_PREVOD,
                                        napomena=f"uloga {uloga.name} — cela firma"))
                continue
            po_cvoru = {}
            for cvor, _, napomena in obuhvati:  # vise OJ istog centra → jedna dodela centra
                po_cvoru.setdefault(cvor, napomena)
            for cvor, napomena in po_cvoru.items():
                nove.append(DodelaUloge(korisnik=korisnik, uloga=uloga, cvor_id=cvor, vazi_od=dan,
                                        status=DodelaUloge.STATUS_NACRT, izvor=DodelaUloge.IZVOR_PREVOD,
                                        napomena=napomena))
    DodelaUloge.objects.bulk_create(nove, batch_size=500)
    zbir["dodela"] = len(nove)
    return zbir


# --------------------------------------------------------------------------- senka


def _stari_obuhvat(korisnik):
    """Danasnji obuhvat Finansija i Potrazivanja: centri iz teksta + centri dodeljenih OJ + sifre OJ."""
    centri = set(_oznake_iz_teksta(korisnik.allowed_center_codes))
    sifre = set()
    for code, centar in korisnik.allowed_centers.values_list("code", "center"):
        if code and code.strip():
            sifre.add(code.strip())
        if centar and centar.strip():
            centri.add(centar.strip())
    return centri, sifre


def senka(korisnici=None):
    """Za svakog korisnika: broj knjizenja Finansija, stavki Potrazivanja i putnih naloga
    koje vidi danas i koje bi video po nacrtu. Nista ne upisuje."""
    from core.mixins import user_has_role_permission
    from core.models import CustomUser
    from finansije.models import FinanceJob, LedgerEntry
    from fleet.models import PutniNalog
    from potrazivanja.models import ReceivablePosting

    sifra_cvora = dict(OrgNodeVersion.objects.filter(valid_to__isnull=True, node__level=OrgNode.LEVEL_JOB)
                       .values_list("node_id", "full_code"))
    centar_sifre = {c.strip(): (ce or "").strip() for c, ce in FinanceJob.objects.filter(company=1).values_list("code", "center")}
    brojevi = {
        "finansije": Counter(dict(LedgerEntry.objects.filter(company=1, active=True).values("job_code")
                                  .annotate(n=Count("pk")).values_list("job_code", "n"))),
        "potrazivanja": Counter(dict(ReceivablePosting.objects.filter(company=1, active=True).values("job_code")
                                     .annotate(n=Count("pk")).values_list("job_code", "n"))),
        "putni_nalozi": Counter(dict(PutniNalog.objects.filter(storniran=False).values("job_code__code")
                                     .annotate(n=Count("pk")).values_list("job_code__code", "n"))),
    }
    brojevi = {m: Counter({(k or "").strip(): v for k, v in c.items()}) for m, c in brojevi.items()}
    from core.models import OrganizationalUnit
    centar_oj = {(c or "").strip(): (ce or "").strip() for c, ce in OrganizationalUnit.objects.values_list("code", "center")}

    korisnici = korisnici if korisnici is not None else CustomUser.objects.filter(is_active=True, is_superuser=False)
    redovi = []
    for korisnik in korisnici.prefetch_related("roles", "allowed_centers"):
        centri, sifre = _stari_obuhvat(korisnik)
        novo = poslovi_obuhvata(obuhvat(korisnik, status=DodelaUloge.STATUS_NACRT))
        nove_sifre = None if novo is None else {sifra_cvora[c] for c in novo if c in sifra_cvora}
        red = {"korisnik": korisnik, "moduli": {}}
        for modul, broj in brojevi.items():
            if not user_has_role_permission(korisnik, ULAZ_MODULA[modul]):
                continue  # modul mu nije dostupan ni danas ni po nacrtu
            if modul == "putni_nalozi":
                # Danas: Uprava vidi sve, ostali po centru sifre naloga (`_putninalog_base_qs`).
                ceo = korisnik.roles.filter(slug=ULOGA_CELE_FIRME).exists()
                staro = set(broj) if ceo else {s for s in broj if centar_oj.get(s, "") in centri}
            else:
                ceo = user_has_role_permission(korisnik, f"{modul}:view_all")
                staro = set(broj) if ceo else {s for s in broj if s in sifre or centar_sifre.get(s, "") in centri}
            novo_m = set(broj) if (ceo or nove_sifre is None) else (nove_sifre & set(broj))
            vise, manje = novo_m - staro, staro - novo_m
            red["moduli"][modul] = {
                "staro": sum(broj[s] for s in staro), "novo": sum(broj[s] for s in novo_m),
                "vise": sorted(vise), "manje": sorted(manje),
                "vise_zapisa": sum(broj[s] for s in vise), "manje_zapisa": sum(broj[s] for s in manje),
            }
        red["razlika"] = any(m["vise"] or m["manje"] for m in red["moduli"].values())
        redovi.append(red)
    return redovi
