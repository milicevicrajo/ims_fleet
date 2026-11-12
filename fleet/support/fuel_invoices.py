"""Kontrola faktura goriva (od 07.10.2026.): faktura sa SEF-a ↔ transakcije ↔ knjiženje, po šifri posla.

OMV fakturiše po kartici (kupac 107248 = putnička, 107258 = teretna) i svojim periodima (do 13. i do kraja
meseca); svaka transakcija nosi broj fakture, pa se poredi faktura po faktura. NIS fakturiše po polovinama
meseca (1–15, 16–kraj) sa dve fakture, „Putničko“ i „Teretno“, po vrsti kartice; od 27.10.2026. se i one
porede svaka posebno — kartice svake fakture su u specifikaciji uz nju (`nis_kartice.py`). Ako specifikacija
neke fakture nije učitana, poredi se sa transakcijama kojih nema na drugoj fakturi (ako je jedina takva), inače se
prijavljuje da se ne može razdvojiti. Od 09.11.2026. **zbir obe fakture se nikad ne proverava**; kartice kojih nema
ni na jednoj fakturi polovine su poseban red sa razlikom.

Knjiženje (kako su knjižene fakture do sada): putnička vozila — bruto na 51300 po šifri posla, bez PDV-a
(PDV na gorivo za putnička vozila se ne odbija); teretna — neto na 51300 po šifri posla i PDV na 27000.
Knjiženje se pronalazi po broju fakture u referenci ili opisu stavke (`finansije.LedgerEntry`); samo čitanje.
"""
from calendar import monthrange
from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from ..models import TransactionNIS, TransactionOMV
from .fuel import deduplicate_omv_transactions, filter_nis_fuel_queryset, nis_charged_gross_net_amounts, omv_charged_gross_net_amounts
from .fuel_reports import OMV_KUPCI, _historical_job_code_subqueries
from .nis_kartice import PUTNICKA, TERETNA, VrstaKartice, kartica, ucitaj_specifikacije

OMV_PIB = "101987198"
NIS_PIB = "104052135"
KONTO_TROSAK, KONTO_PDV = "51300", "27000"
TOLERANCIJA = Decimal("1.00")
NULA = Decimal("0.00")


def _knjizenje(brojevi):
    """Proknjiženo za fakture: {šifra posla: iznos na 51300}, PDV na 27000, broj stavki."""
    from finansije.models import LedgerEntry

    uslov = Q()
    for broj in brojevi:
        uslov |= Q(document_reference__icontains=broj) | Q(description__icontains=broj)
    stavke = LedgerEntry.objects.filter(active=True).filter(uslov) if brojevi else LedgerEntry.objects.none()
    po_sifri, pdv, broj = defaultdict(Decimal), NULA, 0
    for s in stavke.only("account", "job_code", "debit", "credit"):
        broj += 1
        iznos = (s.debit or NULA) - (s.credit or NULA)
        if s.account == KONTO_TROSAK:
            po_sifri[str(s.job_code or "").strip()] += iznos
        elif s.account == KONTO_PDV:
            pdv += iznos
    return dict(po_sifri), pdv, broj


def _po_sifri(transakcije, *, datum_polje, iznosi, teretna):
    """Očekivano knjiženje na 51300 po šifri posla: putnička bruto, teretna neto (istorijska dodela)."""
    po_sifri, bruto, neto = defaultdict(Decimal), NULA, NULA
    for t in transakcije.annotate(**_historical_job_code_subqueries(datum_polje)):
        b, n = iznosi(t)
        b, n = b or NULA, n or NULA
        bruto += b
        neto += n
        jeste_teretna = teretna(t)
        po_sifri[str(t.sifpos or "").strip()] += n if jeste_teretna else b
    return dict(po_sifri), bruto, neto


def _razlike(knjizeno, ocekivano):
    return [dict(sifra=s or "(bez šifre)", knjizeno=knjizeno.get(s, NULA), ocekivano=ocekivano.get(s, NULA),
                 razlika=knjizeno.get(s, NULA) - ocekivano.get(s, NULA))
            for s in sorted(set(knjizeno) | set(ocekivano))
            if abs(knjizeno.get(s, NULA) - ocekivano.get(s, NULA)) > TOLERANCIJA]


def sr_iznos(v, znak=False):
    """Iznos u srpskom formatu: 1.234,56 (sa znakom + ili − kad je `znak`)."""
    tekst = f"{v:+,.2f}" if znak else f"{v:,.2f}"
    return tekst.replace(",", "X").replace(".", ",").replace("X", ".")


def _status(red):
    poruke = []
    if abs(red["razlika_transakcija"]) > TOLERANCIJA:
        poruke.append(("danger", f"Transakcije se ne poklapaju sa fakturom ({sr_iznos(red['razlika_transakcija'], True)})"))
    if not red["knjizeno_stavki"]:
        poruke.append(("secondary", "Nije proknjiženo"))
    else:
        if not red["knjizeno_trosak"]:
            poruke.append(("danger", "Proknjižen samo dobavljač — trošak (51300) nije"))
        elif abs(red["razlika_knjizenja"]) > TOLERANCIJA:
            poruke.append(("danger", f"Proknjiženi trošak i PDV se razlikuju od fakture ({sr_iznos(red['razlika_knjizenja'], True)})"))
        if red["razlike_sifara"]:
            poruke.append(("warning", f"Raspodela po šiframa posla se razlikuje ({len(red['razlike_sifara'])} šifara)"))
    if not poruke:
        poruke.append(("success", "Sve se poklapa"))
    return poruke


def _red(dobavljac, oznaka, fakture, period, kartica, transakcije, knjizenje, url=None):
    po_sifri_ocek, bruto, neto = transakcije
    po_sifri_knj, pdv, stavki = knjizenje
    sef_bruto = sum((f.iznos or NULA for f in fakture), NULA)
    trosak = sum(po_sifri_knj.values(), NULA)
    red = dict(dobavljac=dobavljac, oznaka=oznaka, fakture=fakture, period=period, kartica=kartica, url=url,
               sef_bruto=sef_bruto, sef_neto=sum((f.osnovica or NULA for f in fakture), NULA),
               transakcije_bruto=bruto, transakcije_neto=neto, razlika_transakcija=bruto - sef_bruto,
               knjizeno_trosak=trosak, knjizeno_pdv=pdv, knjizeno_stavki=stavki,
               razlika_knjizenja=(trosak + pdv - sef_bruto) if stavki else None,
               razlike_sifara=_razlike(po_sifri_knj, po_sifri_ocek) if stavki else [])
    red["status"] = _status(red)
    return red


def _omv(faktura):
    from django.urls import reverse

    transakcije = deduplicate_omv_transactions(TransactionOMV.objects.filter(invoice_no=faktura.broj))
    kupac = transakcije.values_list("customer", flat=True).first() or ""
    teretna = kupac == "107258"
    datumi = transakcije.order_by("transaction_date").values_list("transaction_date", flat=True)
    period = (timezone.localdate(datumi[0]), timezone.localdate(datumi.reverse()[0])) if datumi else (None, None)
    ocek = _po_sifri(transakcije, datum_polje="transaction_date",
                     iznosi=lambda t: omv_charged_gross_net_amounts(t.gross_cc, t.vat), teretna=lambda t: teretna)
    ruta = "fuel_job_code_omv_teretna" if teretna else "fuel_job_code_omv_putnicka"
    return _red("OMV", faktura.broj, [faktura], period, OMV_KUPCI.get(kupac, kupac or "?"), ocek,
                _knjizenje([faktura.broj]), url=f"{reverse(ruta)}?faktura={faktura.broj}")


def _nis_transakcije(godina, mesec, polovina):
    """Polovina meseca (1–15 / 16–kraj) i NIS transakcije goriva u njoj."""
    poslednji = monthrange(godina, mesec)[1]
    od, do = (date(godina, mesec, 1), date(godina, mesec, 15)) if polovina == 1 else \
        (date(godina, mesec, 16), date(godina, mesec, poslednji))
    tz = timezone.get_current_timezone()
    pocetak = timezone.make_aware(timezone.datetime(od.year, od.month, od.day), tz)
    kraj = timezone.make_aware(timezone.datetime(do.year, do.month, do.day, 23, 59, 59), tz)
    return od, do, filter_nis_fuel_queryset(TransactionNIS.objects.select_related("vehicle")
                                            .filter(datum_transakcije__range=(pocetak, kraj)))


NIS_VRSTE = {PUTNICKA: "Putnička vozila", TERETNA: "Teretna vozila"}


def _nis_fakture(od, do):
    """(fakture, knjižna odobrenja i zaduženja) NIS-a sa datumom prometa u polovini."""
    from finansije.sef_models import SefFaktura

    dokumenti = list(SefFaktura.objects.filter(smer="ulazna", partner_pib=NIS_PIB, datum_prometa__range=(od, do))
                     .order_by("datum_prometa", "broj"))
    fakture = [f for f in dokumenti if not f.vrsta or f.vrsta == "Invoice"]
    return fakture, [f for f in dokumenti if f not in fakture]


def _vrste_faktura(fakture):
    """{broj fakture: vrsta kartica} iz specifikacija ("" — vrsta nije utvrđena); fakture bez učitane specifikacije
    nisu u rečniku."""
    from ..models import NisKarticaFakture

    return dict(NisKarticaFakture.objects.filter(faktura__in=[f.broj for f in fakture]).values_list("faktura", "tip")
                .distinct())


def _vrsta(tip):
    return NIS_VRSTE.get(tip, "Vrsta nije utvrđena")


def _razdvoji(fakture, transakcije):
    """Transakcije polovine po NIS fakturama, po karticama iz specifikacije svake fakture (od 09.11.2026. uvek —
    zbir obe fakture se ne proverava).

    Vraća ({broj fakture: [transakcije] ili None}, [transakcije bez fakture], {broj: način}). Faktura bez učitane
    specifikacije dobija transakcije kojih nema na drugoj fakturi ako je jedina takva u polovini (način „ostatak“);
    ako ih je više, ne može se razdvojiti (None)."""
    from finansije.sef_models import SefFaktura

    from ..models import NisKarticaFakture

    if fakture:
        ucitaj_specifikacije(list(SefFaktura.objects.filter(pk__in=[f.pk for f in fakture]).prefetch_related("prilozi")))
    kartica_fakture = {k: f for f, k in NisKarticaFakture.objects.filter(faktura__in=[f.broj for f in fakture])
                       .values_list("faktura", "kartica")}
    sa_specifikacijom = set(kartica_fakture.values())
    po_fakturi = {f.broj: [] for f in fakture if f.broj in sa_specifikacijom}
    ostale = []
    for t in transakcije:
        broj = kartica_fakture.get(kartica(t.broj_kartice))
        (po_fakturi[broj] if broj else ostale).append(t)
    bez = [f.broj for f in fakture if f.broj not in sa_specifikacijom]
    nacin = {broj: "specifikacija" for broj in po_fakturi}
    if len(bez) == 1:
        po_fakturi[bez[0]], ostale, nacin[bez[0]] = ostale, [], "ostatak"
    else:
        for broj in bez:
            po_fakturi[broj], nacin[broj] = None, "nema"
    return po_fakturi, ostale, nacin


def _bruto(transakcije):
    return sum((nis_charged_gross_net_amounts(t.total)[0] or NULA for t in transakcije), NULA)


NAPOMENE = {
    "ostatak": "Specifikacija uz fakturu nije učitana — poređeno sa transakcijama kojih nema na drugoj fakturi.",
    "nema": "Specifikacija uz fakturu nije učitana — faktura se ne može razdvojiti od ostalih.",
}


def nis_potvrda(godina, mesec, polovina):
    """Potvrda u izveštaju NIS po šifri posla: slaže li se **svaka** NIS faktura polovine sa SEF-a sa transakcijama
    kartica sa te fakture. Od 09.11.2026. zbir obe fakture se ne proverava ni kad specifikacija nije učitana;
    transakcije kartica kojih nema ni na jednoj fakturi polovine su posebna razlika."""
    od, do, transakcije = _nis_transakcije(godina, mesec, polovina)
    fakture, odobrenja = _nis_fakture(od, do)
    vrste = VrstaKartice()
    po_vrsti = {PUTNICKA: NULA, TERETNA: NULA}
    for t in transakcije:
        po_vrsti[vrste.tip(t)] += nis_charged_gross_net_amounts(t.total)[0] or NULA
    po_fakturi, ostale, nacin = _razdvoji(fakture, transakcije)
    vrste_faktura = _vrste_faktura(fakture)
    redovi = []
    for f in fakture:
        tip = vrste_faktura.get(f.broj, "")
        svoje = po_fakturi.get(f.broj)
        zbir = _bruto(svoje) if svoje is not None else None
        razlika = zbir - (f.iznos or NULA) if zbir is not None else None
        redovi.append(dict(faktura=f, tip=tip, vrsta=_vrsta(tip), transakcije=zbir, razlika=razlika,
                           poklapa=razlika is not None and abs(razlika) <= TOLERANCIJA,
                           napomena=NAPOMENE.get(nacin[f.broj], "")))
    poklapa = bool(fakture) and all(r["poklapa"] for r in redovi) and not ostale
    return dict(od=od, do=do, fakture=fakture, redovi=redovi, odobrenja=odobrenja,
                sef_bruto=sum((f.iznos or NULA for f in fakture), NULA), putnicka=po_vrsti[PUTNICKA],
                teretna=po_vrsti[TERETNA], transakcije_bruto=po_vrsti[PUTNICKA] + po_vrsti[TERETNA],
                van_faktura=_bruto(ostale), van_faktura_broj=len(ostale), poklapa=poklapa)


def _nis(polovina_fakture, godina, mesec, polovina):
    """Redovi kontrole za NIS polovinu: uvek faktura po faktura, sa transakcijama kartica sa te fakture; kartice
    kojih nema ni na jednoj fakturi — poseban red (od 09.11.2026. bez poređenja zbira obe fakture)."""
    from django.urls import reverse

    od, do, transakcije = _nis_transakcije(godina, mesec, polovina)
    vrste = VrstaKartice()
    po_fakturi, ostale, nacin = _razdvoji(polovina_fakture, transakcije)
    vrste_faktura = _vrste_faktura(polovina_fakture)

    def iznosi(t):
        return nis_charged_gross_net_amounts(t.total)

    redovi = []
    for f in polovina_fakture:
        tip = vrste_faktura.get(f.broj, "")
        svoje = po_fakturi.get(f.broj)
        teretna = (lambda t, tip=tip: tip == TERETNA) if tip else (lambda t: vrste.tip(t) == TERETNA)
        ocek = _po_sifri(transakcije.filter(pk__in=[t.pk for t in svoje or []]), datum_polje="datum_transakcije",
                         iznosi=iznosi, teretna=teretna)
        ruta = "fuel_job_code_nis_teretna" if tip == TERETNA else "fuel_job_code_nis_putnicka"
        red = _red("NIS", f.broj, [f], (od, do), _vrsta(tip), ocek, _knjizenje([f.broj]),
                   url=f"{reverse(ruta)}?godina={godina}&mesec={mesec}&polovina={polovina}")
        if nacin[f.broj] == "nema":
            red.update(transakcije_bruto=None, transakcije_neto=None, razlika_transakcija=None)
            red["status"] = [("danger", NAPOMENE["nema"])] + [p for p in red["status"] if "Transakcije" not in p[1]]
        elif nacin[f.broj] == "ostatak":
            red["status"].insert(0, ("warning", NAPOMENE["ostatak"]))
        redovi.append(red)
    if ostale:
        ocek = _po_sifri(transakcije.filter(pk__in=[t.pk for t in ostale]), datum_polje="datum_transakcije",
                         iznosi=iznosi, teretna=lambda t: vrste.tip(t) == TERETNA)
        red = _red("NIS", "Bez fakture", [], (od, do), "Kartice kojih nema na fakturama polovine", ocek, ({}, NULA, 0))
        red["status"] = [("danger", f"Transakcije kartica kojih nema ni na jednoj fakturi polovine "
                                    f"({len(ostale)}, {sr_iznos(red['transakcije_bruto'])})")]
        redovi.append(red)
    return redovi


def kontrola_faktura(godina, mesec):
    """Redovi kontrole za fakture goriva čiji je datum prometa u datom mesecu."""
    from finansije.sef_models import SefFaktura
    from finansije.services.sef import VRSTE

    fakture = list(SefFaktura.objects.filter(smer="ulazna", partner_pib__in=[OMV_PIB, NIS_PIB],
                                             datum_prometa__year=godina, datum_prometa__month=mesec)
                   .order_by("partner_pib", "datum_prometa", "broj"))
    redovi, nis = [], defaultdict(list)
    for f in fakture:
        if f.vrsta and f.vrsta != "Invoice":
            # Knjižno odobrenje ili zaduženje: nema transakcija, prikazuje se knjiženje.
            red = _red(f.partner_pib == OMV_PIB and "OMV" or "NIS", f.broj, [f], (f.datum_prometa, f.datum_prometa),
                       VRSTE.get(f.vrsta, f.vrsta), ({}, NULA, NULA),
                       _knjizenje([f.broj]))
            red["status"] = [("info", "Knjižno odobrenje / zaduženje — proveriti ručno")]
            redovi.append(red)
        elif f.partner_pib == OMV_PIB:
            redovi.append(_omv(f))
        else:
            nis[1 if f.datum_prometa.day <= 15 else 2].append(f)
    for polovina, grupa in sorted(nis.items()):
        redovi.extend(_nis(grupa, godina, mesec, polovina))
    return redovi
