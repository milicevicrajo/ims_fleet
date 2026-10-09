"""Kontrola faktura goriva (od 07.10.2026.): faktura sa SEF-a ↔ transakcije ↔ knjiženje, po šifri posla.

OMV fakturiše po kartici (kupac 107248 = putnička, 107258 = teretna) i svojim periodima (do 13. i do kraja
meseca); svaka transakcija nosi broj fakture, pa se poredi faktura po faktura. NIS fakturiše po polovinama
meseca (1–15, 16–kraj) sa dve fakture (Automobili / Kamioni) koje se iz transakcija ne mogu razdvojiti, pa se
porede obe zajedno sa transakcijama polovine; podela putnička/teretna ide po kategoriji vozila u Floti.

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

from ..models import TransactionNIS, TransactionOMV, Vehicle
from .fuel import deduplicate_omv_transactions, filter_nis_fuel_queryset, nis_charged_gross_net_amounts, omv_charged_gross_net_amounts
from .fuel_reports import OMV_KUPCI, _historical_job_code_subqueries

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


def _teretno_nis(t):
    return t.vehicle_id is not None and t.vehicle.category == Vehicle.Category.CARGO


def nis_potvrda(godina, mesec, polovina):
    """Potvrda u izveštaju NIS po šifri posla (od 08.10.2026., kao kod OMV fakture): slažu li se NIS fakture polovine
    sa SEF-a i obračun iz transakcija. Porede se obe fakture (Automobili / Kamioni) zajedno sa svim transakcijama
    polovine — iz transakcija se ne vidi koja je za koju; putnička i teretna su podela po kategoriji vozila u Floti."""
    from finansije.sef_models import SefFaktura

    od, do, transakcije = _nis_transakcije(godina, mesec, polovina)
    dokumenti = list(SefFaktura.objects.filter(smer="ulazna", partner_pib=NIS_PIB, datum_prometa__range=(od, do))
                     .order_by("datum_prometa", "broj"))
    fakture = [f for f in dokumenti if not f.vrsta or f.vrsta == "Invoice"]
    putnicka = teretna = NULA
    for t in transakcije:
        bruto = nis_charged_gross_net_amounts(t.total)[0] or NULA
        if _teretno_nis(t):
            teretna += bruto
        else:
            putnicka += bruto
    sef_bruto = sum((f.iznos or NULA for f in fakture), NULA)
    razlika = putnicka + teretna - sef_bruto
    return dict(od=od, do=do, fakture=fakture, odobrenja=[f for f in dokumenti if f not in fakture],
                sef_bruto=sef_bruto, sef_neto=sum((f.osnovica or NULA for f in fakture), NULA),
                sef_pdv=sum((f.pdv or NULA for f in fakture), NULA), putnicka=putnicka, teretna=teretna,
                transakcije_bruto=putnicka + teretna, razlika=razlika,
                poklapa=bool(fakture) and abs(razlika) <= TOLERANCIJA)


def _nis(polovina_fakture, godina, mesec, polovina):
    od, do, transakcije = _nis_transakcije(godina, mesec, polovina)
    ocek = _po_sifri(transakcije, datum_polje="datum_transakcije", iznosi=lambda t: nis_charged_gross_net_amounts(t.total),
                     teretna=_teretno_nis)
    brojevi = [f.broj for f in polovina_fakture]
    return _red("NIS", f"{od:%d.%m.}–{do:%d.%m.%Y.}", polovina_fakture, (od, do), "Automobili + Kamioni", ocek,
                _knjizenje(brojevi))


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
        redovi.append(_nis(grupa, godina, mesec, polovina))
    return redovi
