"""Dokumenti za izvoz ekrana Finansija (Excel i PDF), iz vrednosti koje ekrani već računaju."""
import logging

from django.conf import settings
from django.db.models import Sum

from .izvoz import Dokument, Kolona, Tabela, period_tekst

logger = logging.getLogger(__name__)

NAPOMENA = ("Prihodi: potražuje − duguje na kontima klase 6; rashodi: duguje − potražuje na kontima klase 5. "
            "Izuzeti su završno zatvaranje ZAT i konta prenosa 59900/69900. Iznosi u RSD, pre poreza na dobit.")
MAKS_KNJIZENJA_PDF = 2000


def opis_filtera(form):
    delovi = []
    for ime in ("center", "job", "unit", "account", "nivo", "kind"):
        vrednost = form.cleaned_data.get(ime)
        if vrednost in (None, ""):
            continue
        polje = form.fields[ime]
        izbori = dict(getattr(polje, "choices", []) or [])
        tekst = izbori.get(vrednost, vrednost)
        if ime == "account" and form.cleaned_data.get("account_exact"):
            tekst = f"{vrednost} (tačno konto)"
        delovi.append(f"{polje.label}: {tekst}")
    return " · ".join(delovi)


def _period(form):
    return period_tekst(form.cleaned_data["date_from"], form.cleaned_data["date_to"])


# --- Finansijski pregled --------------------------------------------------------------------------

KOLONE_ZT = [Kolona("Centar"), Kolona("Prihodi", "iznos"), Kolona("Rashodi", "iznos"), Kolona("Rezultat bez ZT", "iznos"),
             Kolona("Troškovi zajedničkih službi", "iznos"), Kolona("Rashodi sa ZT", "iznos"),
             Kolona("Rezultat posle ZT", "iznos")]


def _zt_red(naziv, r):
    return [naziv, r["revenue"], r["expense"], r["result"], r["zt"], r["expense_zt"], r["result_zt"]]


def dokument_pregleda(form, totals, centri_zt, chart_groups):
    dokument = Dokument("Finansijski pregled", _period(form), napomena=NAPOMENA, sazetak=[
        ("Prihodi", totals["revenue"], "iznos"), ("Direktni rashodi", totals["expense"], "iznos"),
        ("Direktni rezultat", totals["result"], "iznos"), ("Broj knjiženja", totals["count"], "broj")])
    if centri_zt is None:
        dokument.napomena += " Raspodela zajedničkih troškova trenutno nije dostupna; prikazan je direktni rezultat."
        centri = chart_groups[0]["rows"]
        dokument.tabele.append(Tabela(
            "Centri — direktni rezultat", [Kolona("Centar"), Kolona("Prihodi", "iznos"), Kolona("Rashodi", "iznos"),
                                           Kolona("Rezultat", "iznos"), Kolona("Broj knjiženja", "broj")],
            [[r["label"], r["revenue"], r["expense"], r["result"], r["count"]] for r in centri],
            zbir=["Ukupno", totals["revenue"], totals["expense"], totals["result"], totals["count"]]))
    else:
        for grupa in centri_zt["groups"]:
            nepotpuni = [f'{r["label"]}: {r["note"]}' for r in grupa["rows"] if not r["complete"] and r["note"]]
            opis = grupa["description"] + (" Nepotpuna raspodela — " + "; ".join(nepotpuni) if nepotpuni else "")
            dokument.tabele.append(Tabela(
                grupa["title"], KOLONE_ZT, [_zt_red(r["label"], r) for r in grupa["rows"]],
                zbir=_zt_red("Ukupno · " + grupa["title"].lower(), grupa["total"]), opis=opis))
        u = centri_zt["uskladjenje"]
        if u:
            dokument.tabele.append(Tabela(
                "Usklađenje sa rezultatom Instituta", [Kolona("Stavka"), Kolona("Iznos · RSD", "iznos")], [
                    ["Rezultat svih centara posle ZT", u["posle_zt_centri"]],
                    ["+ Pokriće troškova zajedničkih službi raspodelom", u["pokrice"]],
                    ["Zajedničke službe: rezultat pre pokrića", u["sluzbe_rezultat"]],
                    ["Zajedničke službe: rezultat posle pokrića", u["sluzbe_posle"]],
                ], zbir=["= Rezultat Instituta (bez i posle ZT isti)", u["institut"]],
                opis="Raspodela ne menja rezultat Instituta: ZT profitnih centara pokriva troškove zajedničkih službi."))
    sifre = chart_groups[1]["rows"]
    dokument.tabele.append(Tabela(
        "Šifre posla — direktni rezultat", [Kolona("Šifra"), Kolona("Naziv"), Kolona("Prihodi", "iznos"),
                                            Kolona("Rashodi", "iznos"), Kolona("Rezultat", "iznos")],
        [[r["code"] or "Bez šifre posla", r["name"], r["revenue"], r["expense"], r["result"]] for r in sifre],
        zbir=["Ukupno", "", totals["revenue"], totals["expense"], totals["result"]],
        opis="Poređano po rezultatu, od najboljeg. Bez dodatne raspodele zajedničkih troškova."))
    return dokument


# --- Izveštaj po centrima, kontima i mesecima -----------------------------------------------------

NASLOVI = {"center": "Izveštaj po centrima", "account": "Struktura po kontima", "month": "Mesečni pregled"}


def dokument_izvestaja(form, rows, totals, konto=None):
    group = form.cleaned_data.get("group") or "center"
    naslov = NASLOVI.get(group, "Izveštaj")
    if group == "account" and form.cleaned_data.get("kind") == "expense":
        naslov = "Struktura rashoda po kontima"
    filteri = opis_filtera(form)
    if konto:
        nivo = dict(konto["konto_nivoi"]).get(konto["konto_nivo"], "")
        putanja = " › ".join(f'{k["code"]} {k["label"]}'.strip() for k in konto["konto_putanja"][1:])
        filteri = " · ".join(filter(None, [filteri, f"Nivo konta: {nivo.lower()}", putanja and f"Otvoreno: {putanja}"]))
    prvi = {"center": "Centar", "account": "Konto", "month": "Mesec"}.get(group, "Šifra")
    kolone = [Kolona(prvi), Kolona("Naziv"), Kolona("Prihodi", "iznos"), Kolona("Rashodi", "iznos"),
              Kolona("Rezultat", "iznos"), Kolona("Učešće prihoda", "procenat"), Kolona("Učešće rashoda", "procenat"),
              Kolona("Broj knjiženja", "broj")]
    redovi = [[r["code"] or "Neraspoređeno", r["label"], r["revenue"], r["expense"], r["result"],
               r["revenue_share"], r["expense_share"], r["count"]] for r in rows]
    return Dokument(naslov, _period(form), filteri, NAPOMENA, tabele=[Tabela(
        naslov, kolone, redovi, zbir=["Ukupno", "", totals["revenue"], totals["expense"], totals["result"], None, None,
                                      totals["count"]])])


# --- Šifre posla ----------------------------------------------------------------------------------

def dokument_sifara(form, rows, labels, keys, *, dodatne=False):
    def vrsta(naziv):
        return "procenat" if naziv.endswith("%") else "iznos"

    if dodatne:
        # Dodatne analize imaju previše kolona za A4; osnovni pokazatelji su na ekranu „Šifre posla”.
        from .job_overview import LABELS
        labels, keys = labels[len(LABELS):], keys[len(LABELS):]
    kolone = [Kolona("Šifra"), Kolona("Naziv"), Kolona("Centar"), *[Kolona(l, vrsta(l)) for l in labels]]
    redovi = [[r["code"] or "Bez šifre", r["label"], r.get("center", ""), *[r["metrics"][k]["value"] for k in keys]]
              for r in rows]
    zbir = ["Ukupno", "", ""]
    for i, kolona in enumerate(kolone[3:], 3):
        vrednosti = [red[i] for red in redovi]
        sabira = kolona.vrsta == "iznos" and not kolona.naziv.endswith("čoveku") and kolona.naziv != "Prosečan broj ljudi"
        zbir.append(sum(vrednosti) if sabira and vrednosti and None not in vrednosti else None)
    nepotpuno = sum(1 for r in rows if any(m["value"] is None or not m["complete"] for m in r["metrics"].values()))
    opis = f"Za {nepotpuno} šifara deo pokazatelja je nepotpun ili nedostupan (crta); detalj je u Excelu." if nepotpuno else ""
    naslov = "Šifre posla — dodatne analize" if dodatne else "Šifre posla"
    return Dokument(naslov, _period(form), opis_filtera(form), NAPOMENA + " ZT = troškovi zajedničkih službi.",
                    tabele=[Tabela(naslov, kolone, redovi, zbir=zbir, opis=opis)])


# --- Knjiženja ------------------------------------------------------------------------------------

def dokument_knjizenja(form, entries, polje):
    ukupno = entries.count()
    zapisi = entries.order_by("booking_date", "pk").values(
        "booking_date", "year", "journal_type", "journal_number", "line_number", polje, "job_code", "account",
        "account_name", "partner_name", "document_reference", "debit", "credit")[:MAKS_KNJIZENJA_PDF]
    redovi = [[z["booking_date"], f'{z["year"]}/{z["journal_type"]}/{z["journal_number"]}·{z["line_number"]}', z[polje],
               z["job_code"], z["account"], z["account_name"], z["partner_name"], z["document_reference"],
               z["debit"], z["credit"]] for z in zapisi]
    promet = entries.aggregate(debit=Sum("debit"), credit=Sum("credit"))
    opis = (f"Prikazano prvih {MAKS_KNJIZENJA_PDF} od {ukupno} knjiženja, po datumu. Ceo spisak je u Excelu; "
            "zbir je za sva knjiženja." if ukupno > MAKS_KNJIZENJA_PDF else f"Ukupno {ukupno} knjiženja.")
    kolone = [Kolona("Datum", "datum"), Kolona("Nalog · stavka"), Kolona("Centar"), Kolona("Šifra posla"), Kolona("Konto"),
              Kolona("Naziv konta"), Kolona("Partner"), Kolona("Dokument"), Kolona("Duguje", "iznos"),
              Kolona("Potražuje", "iznos")]
    return Dokument("Finansijska knjiženja", _period(form), opis_filtera(form), tabele=[Tabela(
        "Knjiženja", kolone, redovi, opis=opis,
        zbir=["Ukupno", "", "", "", "", "", "", "", promet["debit"], promet["credit"]])])


# --- Detalj šifre posla ---------------------------------------------------------------------------

def _bezbedno(racunaj, *args):
    try:
        rezultat = racunaj(*args)
    except Exception:  # izvor raspodele ili tokova gotovine nedostupan: iznos je nepoznat, ne nula
        logger.exception("Pokazatelj detalja šifre nije dostupan za izvoz.")
        return None
    return rezultat if rezultat.get("available") else None


def dokument_sifre(code, naziv, centar, start, end, selected, finance_available):
    from .cash_flow import cash_flow
    from .job_card import monthly_expenses, monthly_invoices
    from .kontni_plan import nazivi_konta
    from .reports import summary
    from .shared_costs import shared_cost

    dokument = Dokument(f"Detalj šifre posla {code}", period_tekst(start, end),
                        f"{code} — {naziv} · Centar {centar or 'Neraspoređeno'}", NAPOMENA)
    if not finance_available:
        dokument.napomena = "Nema potvrđenih sinhronizovanih finansijskih podataka za izabranu godinu."
        return dokument
    company = getattr(settings, "FINANSIJE_COMPANY", 1)
    totals = summary(selected.filter(booking_date__range=(start, end)))
    zt, tok = _bezbedno(shared_cost, company, code, start, end), _bezbedno(cash_flow, company, code, start, end)
    dokument.sazetak = [
        ("Prihodi", totals["revenue"], "iznos"), ("Rashodi", -totals["expense"], "iznos"),
        ("Rezultat bez ZT · P − R", totals["result"], "iznos"),
        ("Zajednički troškovi", -zt["cost"] if zt else None, "iznos"),
        ("Rezultat P − R − ZT", totals["result"] - zt["cost"] if zt else None, "iznos"),
        ("Priliv", tok["inflow"] if tok else None, "iznos"), ("Odliv", -tok["outflow"] if tok else None, "iznos"),
        ("Neto gotovina · P − O", tok["net"] if tok else None, "iznos"),
    ]
    beleske = [b["note"] for b in (zt, tok) if b and b.get("note")]
    if beleske:
        dokument.napomena += " " + " ".join(beleske)
    plan = nazivi_konta()
    rashodi = monthly_expenses(selected, start, end, code)
    dokument.tabele.append(Tabela(
        "Struktura rashoda · sintetička konta",
        [Kolona("Konto"), Kolona("Naziv konta"), Kolona("Rashodi · RSD", "iznos"), Kolona("Učešće", "procenat"),
         Kolona("Broj knjiženja", "broj")],
        [[r["knt3"], plan.get(r["knt3"]) or "", -r["amount"], r["share"], r["count"]] for r in rashodi],
        zbir=["Ukupno", "", -totals["expense"], None, sum(r["count"] for r in rashodi)],
        opis="Rashod je prikazan sa znakom minus (uticaj na rezultat); storna zadržavaju suprotan znak."))
    for interne, naslov, opis in (
            (False, "Izdate fakture · IF", "Konta 20400 i 20500, po datumu dokumenta; deo fakture knjižen na ovoj šifri."),
            (True, "Interne fakture · ON", "Konta 61420, 61421, 61521 i 64002, po datumu dokumenta.")):
        fakture = monthly_invoices(selected, start, end, internal=interne)
        vrsta = "ON" if interne else "IF"
        dokument.tabele.append(Tabela(
            naslov, [Kolona("Datum dokumenta", "datum"), Kolona("Veza dokumenta"), Kolona("Nalog"), Kolona("Partner"),
                     Kolona("Iznos · RSD", "iznos")],
            [[f["date"], f["document_reference"] or "Bez veze dokumenta", f'{f["year"]}/{vrsta}/{f["journal_number"]}',
              f'{f["partner_code"] or "—"} · {f["partner_name"] or ""}', f["amount"]] for f in fakture],
            zbir=["Ukupno", "", "", "", sum((f["amount"] or 0 for f in fakture), 0)], opis=opis))
    return dokument
