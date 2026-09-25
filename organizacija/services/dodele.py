"""Ekran dodela uloga (plan prelaska na registar, korak 3; V2, korak 3).

Administrator ovde, bez Django admina, pregleda nacrt koji je napravio prevod starih prava,
odobrava ga, dodaje rucne dodele i opoziva ih. Istorija ostaje u tabeli: opozvana dodela dobija
kraj vazenja i ime onoga ko ju je opozvao, ne brise se. Brise se samo neodobren nacrt.

**Ni odobrena dodela jos ne odlucuje o pristupu** — moduli citaju stara prava dok se ne ukljuci
pilot Finansija i Potrazivanja (korak 5). Zato ovaj ekran nikome nista ne otvara ni ne zatvara.
"""

from collections import defaultdict

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from organizacija.models import DodelaUloge, OrgNode, OrgNodeVersion
from organizacija.services import prava

NIVOI = {OrgNode.LEVEL_CENTER: "centar", OrgNode.LEVEL_UNIT: "jedinica", OrgNode.LEVEL_JOB: "posao"}
FILTERI_STATUSA = {"nacrt": "Ima nacrt", "aktivna": "Odobreni", "bez": "Bez dodela"}


def oznake_cvorova():
    """Cvor → (nivo, "43 · Naziv"), iz vazecih verzija."""
    return {
        node_id: (level, f"{code} · {name}" if name else code)
        for node_id, level, code, name in OrgNodeVersion.objects.filter(valid_to__isnull=True)
        .values_list("node_id", "node__level", "full_code", "name")
    }


def izbor_obuhvata():
    """Izbor obuhvata za novu dodelu: cela firma, centri, jedinice i **aktivni** poslovi
    (odluka 8: neaktivne sifre se ne nude nigde)."""
    grupe = defaultdict(list)
    for node_id, level, code, name, aktivan in (
        OrgNodeVersion.objects.filter(valid_to__isnull=True)
        .values_list("node_id", "node__level", "full_code", "name", "is_active").order_by("full_code")
    ):
        if level == OrgNode.LEVEL_JOB and not aktivan:
            continue
        grupe[level].append((str(node_id), f"{code} · {name}" if name else code))
    return [
        ("firma", "Cela firma"),
        ("Centri", grupe[OrgNode.LEVEL_CENTER]),
        ("Jedinice", grupe[OrgNode.LEVEL_UNIT]),
        ("Šifre posla (aktivne)", grupe[OrgNode.LEVEL_JOB]),
    ]


def _opis(dodela, oznake):
    if dodela.cela_firma:
        return "Cela firma", "firma"
    nivo, oznaka = oznake.get(dodela.cvor_id, (None, f"čvor {dodela.cvor_id}"))
    return oznaka, NIVOI.get(nivo, "")


def spisak(q="", status="", sa_senkom=False):
    """Redovi spiska: korisnik, uloge, broj dodela po statusu i obuhvat koji danas vazi.

    Senka za sve korisnike traje desetak sekundi, pa se racuna samo na zahtev (`sa_senkom`).
    """
    from core.models import CustomUser

    korisnici = CustomUser.objects.filter(is_active=True, is_superuser=False).order_by("username")
    if q:
        korisnici = korisnici.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    dan = timezone.localdate()
    oznake = oznake_cvorova()
    po_korisniku = defaultdict(list)
    for dodela in DodelaUloge.objects.filter(korisnik__in=korisnici).select_related("uloga"):
        po_korisniku[dodela.korisnik_id].append(dodela)

    redovi = []
    for korisnik in korisnici.prefetch_related("roles"):
        dodele = po_korisniku.get(korisnik.pk, [])
        nacrt = [d for d in dodele if d.status == DodelaUloge.STATUS_NACRT]
        aktivne = [d for d in dodele if d.status == DodelaUloge.STATUS_AKTIVNA and _vazi(d, dan)]
        if status == "nacrt" and not nacrt:
            continue
        if status == "aktivna" and not aktivne:
            continue
        if status == "bez" and dodele:
            continue
        prikaz = aktivne or nacrt
        redovi.append({
            "korisnik": korisnik,
            "uloge": [u.name for u in korisnik.roles.all() if u.is_active],
            "nacrt": len(nacrt),
            "aktivnih": len(aktivne),
            "obuhvat": sorted({_opis(d, oznake)[0] for d in prikaz}),
            "odobren": bool(aktivne),
        })
    if sa_senkom and redovi:
        senke = {red["korisnik"].pk: red for red in prava.senka(korisnici.filter(pk__in=[r["korisnik"].pk for r in redovi]))}
        for red in redovi:
            red["senka"] = senke.get(red["korisnik"].pk)
    return redovi


def _vazi(dodela, dan):
    return dodela.vazi_od <= dan and (dodela.vazi_do is None or dodela.vazi_do > dan)


def pregled_korisnika(korisnik):
    """Sve dodele jednog korisnika (i istorija), njegova stara prava i senka samo za njega."""
    from core.models import CustomUser

    dan = timezone.localdate()
    oznake = oznake_cvorova()
    dodele = []
    for dodela in (DodelaUloge.objects.filter(korisnik=korisnik)
                   .select_related("uloga", "odobrio", "opozvao").order_by("status", "uloga__name", "vazi_od", "pk")):
        opis, nivo = _opis(dodela, oznake)
        dodele.append({"dodela": dodela, "opis": opis, "nivo": nivo, "vazi": _vazi(dodela, dan),
                       "istekla": dodela.vazi_do is not None and dodela.vazi_do <= dan})
    senka = prava.senka(CustomUser.objects.filter(pk=korisnik.pk))
    return {
        "dodele": dodele,
        "nacrt": sum(1 for d in dodele if d["dodela"].status == DodelaUloge.STATUS_NACRT),
        "stari_centri": prava._oznake_iz_teksta(korisnik.allowed_center_codes),
        "stare_oj": list(korisnik.allowed_centers.order_by("code").values_list("code", "name")),
        "senka": senka[0] if senka else None,
    }


@transaction.atomic
def odobri(korisnik, ko):
    """Nacrt korisnika postaje odobren (`aktivna`). Vraca broj odobrenih dodela."""
    return DodelaUloge.objects.filter(korisnik=korisnik, status=DodelaUloge.STATUS_NACRT).update(
        status=DodelaUloge.STATUS_AKTIVNA, odobrio=ko, odobreno=timezone.now())


@transaction.atomic
def opozovi(dodela, ko, dan=None):
    """Neodobren nacrt se brise; odobrena dodela prestaje da vazi od danas i ostaje u istoriji.

    Vraca "obrisan" ili "opozvana".
    """
    if dodela.status == DodelaUloge.STATUS_NACRT:
        dodela.delete()
        return "obrisan"
    dan = dan or timezone.localdate()
    kraj = max(dan, dodela.vazi_od)  # dodela sa pocetkom u buducnosti ostaje bez ijednog dana vazenja
    if dodela.vazi_do is None or dodela.vazi_do > kraj:
        dodela.vazi_do = kraj
    dodela.opozvao, dodela.opozvano = ko, timezone.now()
    dodela.save(update_fields=["vazi_do", "opozvao", "opozvano"])
    return "opozvana"


def preklapanje(korisnik, uloga, cvor_id, cela_firma, vazi_od, vazi_do):
    """Postoji li vec dodela iste uloge i istog obuhvata koja vazi u delu tog perioda."""
    qs = DodelaUloge.objects.filter(korisnik=korisnik, uloga=uloga, cela_firma=cela_firma,
                                    status__in=(DodelaUloge.STATUS_NACRT, DodelaUloge.STATUS_AKTIVNA))
    qs = qs.filter(cvor__isnull=True) if cela_firma else qs.filter(cvor_id=cvor_id)
    qs = qs.filter(Q(vazi_do__isnull=True) | Q(vazi_do__gt=vazi_od))
    if vazi_do:
        qs = qs.filter(vazi_od__lt=vazi_do)
    return qs.exists()


@transaction.atomic
def dodaj(korisnik, uloga, cvor_id, cela_firma, vazi_od, vazi_do, ko, napomena=""):
    """Rucna dodela, odmah odobrena — administrator je ta koji odlucuje."""
    return DodelaUloge.objects.create(
        korisnik=korisnik, uloga=uloga, cvor_id=None if cela_firma else cvor_id, cela_firma=cela_firma,
        vazi_od=vazi_od, vazi_do=vazi_do, status=DodelaUloge.STATUS_AKTIVNA, izvor=DodelaUloge.IZVOR_RUCNO,
        napomena=napomena or f"ručno, {ko.get_username()}", odobrio=ko, odobreno=timezone.now())
