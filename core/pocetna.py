"""Početna strana aplikacije (od 02.10.2026.): opis, moduli i podaci o prijavljenom korisniku.

Modul je „otvoren” ako korisnik ima dozvolu za njegovu početnu rutu (kod = naziv rute, kao i
inače); bez ulazne dozvole nude se pojedinačni dozvoljeni ekrani. Kartice vode preko `switch_app`, isto kao
linkovi u zaglavlju. Strana samo čita.
"""
import datetime

from django.urls import reverse

from core.models import PermissionCode
from core.pocetna_ekrani import EKRANI


# (slug za switch_app, naziv, ikona, ruta početne strane modula, kod dozvole ili None = svi prijavljeni, opis)
MODULI = [
    ("fleet", "Flota", "mdi-car", "dashboard", None,
     "Vozni park: vozila, putni nalozi, gorivo (NIS, OMV), servisi, kilometraža i troškovi po vozilu."),
    ("kadrovi", "Kadrovi", "mdi-account-group", "hr:pregled", None,
     "Zaposleni, radne liste, godišnji odmori, bolovanja, zahtevi i rešenja, ugovori i ocenjivanje."),
    ("finansije", "Finansije", "mdi-chart-bar", "finansije:dashboard", "finansije:dashboard",
     "Finansijska analitika po šiframa posla: prihodi, rashodi, zarade i tok gotovine; SEF fakture."),
    ("nabavka", "Nabavka", "mdi-clipboard-check", "nabavka:dashboard", "nabavka:dashboard",
     "Zahtevi za nabavku i uslugu, EUF i UF SEF fakture, fiskalni računi, ugovori i porudžbine."),
    ("potrazivanja", "Potraživanja", "mdi-cash-check", "potrazivanja:dashboard", "potrazivanja:dashboard",
     "Dugovanja kupaca po starosti, avansi, opomene i izveštaji po šiframa posla."),
    ("isplate", "Isplate", "mdi-bank-transfer", "isplate:neoporezive_isplate", "isplate:neoporezive_isplate",
     "Isplata akontacija za putne naloge (TXT virman), pravdanje i fiskalni računi putnih naloga."),
    ("pravna", "Pravna služba", "mdi-gavel", "pravna:cases_list", "pravna:cases_list",
     "Sudski postupci (tuženi i tužioci) i disciplinski postupci."),
    ("ugovori", "Ugovori", "mdi-file-document-multiple", "ugovori:contract_list", "ugovori:contract_list",
     "Poslovni ugovori sa partnerima, rokovi i provera partnera u APR-u."),
    ("menice", "Menice", "mdi-file-document", "menice:menica_list", "menice:menica_list",
     "Izdate i primljene menice i provera u registru NBS."),
    ("mobilni", "Mobilni telefoni", "mdi-cellphone", "mobilni:mobile_dashboard", "mobilni:mobile_dashboard",
     "Brojevi, potrošnja i obustave zaposlenima za mobilnu telefoniju."),
    ("arhiva", "Arhiva", "mdi-archive", "arhiva:delovodnik", "arhiva:delovodnik",
     "Pisarnica i delovodnik: zavođenje predmeta i akata, lista kategorija."),
    ("organizacija", "Organizacija", "mdi-file-tree", "organizacija:stablo", None,
     "Stablo i šema organizacije (centri, jedinice, šifre posla) i dodele uloga po obuhvatu."),
    ("administracija", "Administracija", "mdi-shield-account", "dashboard", "__superuser__",
     "Korisnici, uloge i dozvole, istorija zakazanih poslova i log rada."),
]

# Argumenti rute za module čija početna strana ih traži.
ARGUMENTI = {"pravna:cases_list": {"case_type": "tuzeni"}, "menice:menica_list": {"tip": "izlazna"}}

NAZIVI_PREFIKSA = {slug: naziv for slug, naziv, *_ in MODULI}
NAZIVI_PREFIKSA.update({"hr": "Kadrovi", "fleet": "Flota", "": "Flota i zajedničko"})


def kodovi_korisnika(user):
    if not user.is_authenticated:
        return set()
    return set(PermissionCode.objects.filter(role_permissions__role__in=user.roles.filter(is_active=True))
               .values_list("code", flat=True))


def moduli(user, kodovi):
    redovi = []
    for slug, naziv, ikona, ruta, kod, opis in MODULI:
        if kod == "__superuser__":
            dostupan = user.is_superuser
        elif kod == "potrazivanja:dashboard":
            from potrazivanja.access import can_view

            dostupan = can_view(user)
        else:
            dostupan = user.is_superuser or kod is None or kod in kodovi
        cilj = reverse(ruta, kwargs=ARGUMENTI.get(ruta))
        ekrani = []
        if not dostupan:
            for ekran, naslov, argumenti, dozvola in EKRANI.get(slug, []):
                if dozvola in kodovi:
                    if ekran in {"finansije:sef_list", "finansije:sync_status"}:
                        from finansije.access import can_view_all

                        if not can_view_all(user):
                            continue
                    ekrani.append({
                        "naziv": naslov,
                        "url": f"{reverse('switch_app', args=[slug])}?next={reverse(ekran, kwargs=argumenti)}",
                    })
        redovi.append({"slug": slug, "naziv": naziv, "ikona": ikona, "opis": opis, "dostupan": dostupan,
                       "ekrani": ekrani, "ima_pristup": dostupan or bool(ekrani),
                       "url": f"{reverse('switch_app', args=[slug])}?next={cilj}"})
    return redovi


def dozvole_po_modulu(kodovi):
    """[(naziv modula, [kodovi])] — prefiks pre „:” je modul; kodovi bez prefiksa su Flota i zajednički."""
    grupe = {}
    for kod in sorted(kodovi):
        prefiks = kod.split(":", 1)[0] if ":" in kod else ""
        grupe.setdefault(NAZIVI_PREFIKSA.get(prefiks, prefiks.capitalize()), []).append(kod)
    return sorted(grupe.items(), key=lambda g: (-len(g[1]), g[0]))


def dodele(user, dan=None):
    """Odobrene dodele uloga koje danas važe (obuhvat po registru)."""
    from django.db.models import Q

    from organizacija.models import DodelaUloge

    dan = dan or datetime.date.today()
    return list(DodelaUloge.objects.filter(korisnik=user, status=DodelaUloge.STATUS_AKTIVNA, vazi_od__lte=dan)
                .filter(Q(vazi_do__isnull=True) | Q(vazi_do__gt=dan)).select_related("uloga", "cvor")
                .order_by("uloga__name", "pk"))


def pocetna(user):
    kodovi = kodovi_korisnika(user)
    lista = moduli(user, kodovi)
    dodele_korisnika = dodele(user)
    for d in dodele_korisnika:
        verzija = d.cvor.current_version if d.cvor_id else None
        d.obuhvat_naziv = "Cela firma" if d.cela_firma else (
            f"{verzija.full_code} {verzija.name}".strip() if verzija else "—")
    return {
        "moduli": lista,
        "broj_dostupnih": sum(m["ima_pristup"] for m in lista),
        "uloge": list(user.roles.filter(is_active=True).order_by("name")),
        "dozvole": dozvole_po_modulu(kodovi),
        "broj_dozvola": len(kodovi),
        "dodele": dodele_korisnika,
        "employee": getattr(user, "employee", None) if getattr(user, "employee_id", None) else None,
    }
