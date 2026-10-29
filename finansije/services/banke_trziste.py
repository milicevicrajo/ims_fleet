"""Pregled tržišta banaka (od 29.10.2026.): sve banke sa spiska NBS i sve bankarske grupe.

Isti sadržaj kao pregledi direktora („Banke_Srbija_NBS_podaci”, „Banke – povezana lica”), uz našu
saradnju: koje šifre partnera imamo i promet u periodu. Povezana lica se traže po PIB-u u lokalnim
kopijama šifarnika — banke u `BankaPartner`, ostala lica (lizing, osiguranje...) u kopiji partnera
grupe 1 koju održavaju Potraživanja — bez upita prema povezanom serveru.
"""
from django.conf import settings
from django.db.models import Count, Max, Q, Sum

from finansije.access import visible_scope
from finansije.models import BankaNbs, LedgerEntry, PovezanoLiceBanke
from . import izvoz
from .banke_nbs import normalizuj_pib


def _prosek(vrednosti):
    vrednosti = list(vrednosti)
    return round(sum(vrednosti) / len(vrednosti), 1) if vrednosti else None


def pregled(banks, user=None, start=None, end=None):
    """`banks` su naše šifre grupe 11 posle `razvrstaj`; promet samo kad je zadat period."""
    from potrazivanja.models import FinancePartnerIdentity

    lica = list(PovezanoLiceBanke.objects.select_related("grupa").order_by("grupa__naziv", "pk"))
    grupa_banke = {normalizuj_pib(l.pib): l.grupa for l in lica if l.je_banka}
    nase_po_nbs, partneri = {}, {}
    for bank in banks:
        if bank.get("nbs"):
            nase_po_nbs.setdefault(bank["nbs"].pk, []).append(bank)
        if bank.get("pib"):
            partneri.setdefault(normalizuj_pib(bank["pib"]), []).append(dict(grupa=11, sifra=bank["code"], naziv=bank["name"]))
    pibovi = [normalizuj_pib(l.pib) for l in lica if not l.je_banka]
    for sifra, naziv, pib in FinancePartnerIdentity.objects.filter(
            company=getattr(settings, "FINANSIJE_COMPANY", 1), partner_group=1, source_tax_id__in=pibovi
    ).values_list("partner_code", "source_name", "source_tax_id"):
        partneri.setdefault(normalizuj_pib(pib), []).append(dict(grupa=1, sifra=sifra, naziv=naziv))

    promet = {}
    kljucevi = {(p["grupa"], p["sifra"]) for lista in partneri.values() for p in lista}
    if start and end and kljucevi:
        uslov = Q(pk__in=[])
        for grupa, sifra in kljucevi:
            uslov |= Q(partner_group=grupa, partner_code=sifra)
        knjizenja = LedgerEntry.objects.filter(active=True, booking_date__gte=start, booking_date__lte=end).exclude(journal_type__in=("POC", "ZAT"))
        if user is not None:
            knjizenja = visible_scope(knjizenja, user)
        for red in knjizenja.filter(uslov).values("partner_group", "partner_code").annotate(
                stavki=Count("id"), duguje=Sum("debit"), potrazuje=Sum("credit"), poslednje=Max("booking_date")).order_by():
            promet[(red["partner_group"], red["partner_code"])] = red

    def saradnja(pib):
        nasi = sorted(partneri.get(normalizuj_pib(pib), []), key=lambda p: (p["grupa"], p["sifra"]))
        redovi = [promet[(p["grupa"], p["sifra"])] for p in nasi if (p["grupa"], p["sifra"]) in promet]
        if not redovi:
            return nasi, None
        zbir = {k: sum(r[k] or 0 for r in redovi) for k in ("stavki", "duguje", "potrazuje")}
        zbir["poslednje"] = max(r["poslednje"] for r in redovi)
        return nasi, zbir

    banke = []
    for banka in BankaNbs.objects.all():
        banke.append(dict(banka=banka, grupa=grupa_banke.get(normalizuj_pib(banka.pib)), promet=saradnja(banka.pib)[1],
                          nase=sorted(nase_po_nbs.get(banka.pk, []), key=lambda b: (b.get("glavna_code") is not None, b["code"]))))
    banke.sort(key=lambda r: (not r["banka"].aktivna, r["grupa"] is None, (r["grupa"].naziv if r["grupa"] else "").lower(),
                              r["banka"].naziv.lower()))
    aktivne = [r["banka"] for r in banke if r["banka"].aktivna]
    zbir = dict(banaka=len(aktivne), sa_nama=sum(1 for r in banke if r["banka"].aktivna and r["nase"]),
                zaposlenih=sum(b.broj_zaposlenih or 0 for b in aktivne), nezavisnih=sum(b.nezavisnih_uo for b in aktivne),
                prosek_uo=_prosek(len(b.upravni_odbor) for b in aktivne), prosek_io=_prosek(len(b.izvrsni_odbor) for b in aktivne))

    grupe = {}
    for lice in lica:
        nasi, zbir_lica = saradnja(lice.pib)
        stavka = grupe.setdefault(lice.grupa.pk, dict(grupa=lice.grupa, lica=[], sa_nama=0))
        stavka["lica"].append(dict(lice=lice, partneri=nasi, promet=zbir_lica))
        stavka["sa_nama"] += bool(nasi)
    # Prvo grupe sa kojima sarađujemo, pa ostale.
    grupe = sorted(grupe.values(), key=lambda g: (g["sa_nama"] == 0, g["grupa"].naziv.lower()))
    return dict(banke=banke, zbir=zbir, grupe=grupe, nepotvrdjenih=sum(1 for l in lica if not l.potvrdjeno))


def dokument(podaci, sa_prometom, period=""):
    """Excel u obliku pregleda direktora: banke iz registra NBS, pa grupe i povezana lica."""
    K = izvoz.Kolona
    kolone_banaka = [
        K("Grupa"), K("Naziv banke"), K("Grad"), K("Adresa"), K("Poštanski broj"), K("Matični broj"), K("PIB"), K("SWIFT"),
        K("Telefon"), K("Telefaks"), K("Veb sajt"), K("E-mail"), K("Rešenje o dozvoli za rad"), K("Datum dozvole za rad", "datum"),
        K("Broj zaposlenih", "broj"), K("Revizor"), K("Najveći akcionar"), K("Učešće najvećeg akcionara"),
        K("Akcionari preko 5% (svi)"), K("Broj akcionara >5%", "broj"), K("Predsednik upravnog odbora"),
        K("Članovi upravnog odbora (sa funkcijom)"), K("Broj članova UO", "broj"), K("Od toga nezavisnih", "broj"),
        K("Predsednik izvršnog odbora"), K("Članovi izvršnog odbora (sa funkcijom)"), K("Broj članova IO", "broj"),
        K("Napomena NBS"), K("Saradnja sa IMS (šifre partnera)"), K("Status"), K("Link na NBS")]

    def clanovi(lista):
        return "\n".join(f"{c['ime']} – {c['funkcija']}" for c in lista)

    redovi_banaka = []
    for r in podaci["banke"]:
        b, najveci = r["banka"], r["banka"].najveci_akcionar
        redovi_banaka.append([
            r["grupa"].naziv if r["grupa"] else "", b.naziv, b.grad, b.adresa, b.postanski_broj, b.maticni_broj, b.pib, b.swift,
            b.telefon, b.telefaks, b.web, b.email, b.resenje, b.datum_resenja, b.broj_zaposlenih, b.revizor,
            najveci["naziv"] if najveci else "", najveci["procenat"] if najveci else "",
            "\n".join(f"{a['naziv']} – {a['procenat']}" for a in b.akcionari), len(b.akcionari),
            b.predsednik_uo, clanovi(b.upravni_odbor), len(b.upravni_odbor), b.nezavisnih_uo,
            b.predsednik_io, clanovi(b.izvrsni_odbor), len(b.izvrsni_odbor), b.napomena,
            ", ".join(f"{n['code']} {n['name']}" for n in r["nase"]) or "ne radimo",
            "na spisku NBS" if b.aktivna else f"istorijska (nije na spisku od {b.nestala:%d.%m.%Y.})", b.nbs_url])
    z = podaci["zbir"]
    zbir_banaka = (["Ukupno / prosek", f"{z['banaka']} banaka · sarađujemo sa {z['sa_nama']}"] + [None] * 12 + [z["zaposlenih"]]
                   + [None] * 7 + [z["prosek_uo"], z["nezavisnih"], None, None, z["prosek_io"]] + [None] * 4)

    kolone_lica = [K("Grupa"), K("Matična grupa (zemlja)"), K("Vrsta lica"), K("Naziv pravnog lica"), K("Matični broj"), K("PIB"),
                   K("Vlasnici / napomena"), K("Izvor MB"), K("Pripadnost grupi potvrđena"), K("Kod nas (grupa / šifra partnera)")]
    if sa_prometom:
        kolone_lica += [K("Stavki u periodu", "broj"), K("Duguje u periodu", "iznos"), K("Potražuje u periodu", "iznos")]
    redovi_lica = []
    for g in podaci["grupe"]:
        for m in g["lica"]:
            lice = m["lice"]
            red = [g["grupa"].naziv, g["grupa"].maticna_grupa, lice.vrsta, lice.naziv, lice.maticni_broj, lice.pib, lice.vlasnistvo,
                   lice.izvor, lice.potvrda, ", ".join(f"{p['grupa']}/{p['sifra']} {p['naziv']}" for p in m["partneri"]) or "nije u šifarniku"]
            if sa_prometom:
                red += [m["promet"]["stavki"], m["promet"]["duguje"], m["promet"]["potrazuje"]] if m["promet"] else [None, None, None]
            redovi_lica.append(red)
    return izvoz.Dokument(
        naslov="Banke u Republici Srbiji", period=period,
        napomena="Izvor: NBS, webappcenter.nbs.rs → Banke (stranica „Detalji” svake banke); grupe i povezana lica po spisku direktora.",
        tabele=[izvoz.Tabela("Banke – registar NBS", kolone_banaka, redovi_banaka, zbir=zbir_banaka),
                izvoz.Tabela("Grupe i povezana lica", kolone_lica, redovi_lica)])
