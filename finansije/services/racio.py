"""Racio analiza (od 04.11.2026.): pokazatelji likvidnosti, solventnosti, profitabilnosti i aktivnosti po godinama.

Formule su iz dokumenta „Racio analiza” (finansije, novembar 2026.), izvedene iz AOP pozicija Bilansa stanja i
Bilansa uspeha; iznosi pozicija su iz `bilansi.izracunaj`, isti kao na ekranima bilansa. Odluke od 04.11.2026.:

* zalihe su 0031 (bez 0037, stalne imovine za prodaju); kapital je 0401 − 0455 (stvarni, može biti negativan —
  0401 u obrascu nije negativan, a gubitak iznad kapitala je na 0455); rashodi kamata su samo 1034;
* „prosečno” = (stanje na kraju kolone + stanje na 31.12. prethodne godine) / 2;
* tekuća godina do izabranog dana: iznosi iz Bilansa uspeha se za pokazatelje preračunavaju na celu godinu
  (× dana u godini / dana perioda); marže i pokriće kamata se time ne menjaju. Pomoćne veličine se prikazuju
  stvarne, za period;
* faktor PDV-a u danima naplate i plaćanja je parametar (podrazumevano 1,2 — finansije još nisu odlučile);
* orijentiri samo gde ih dokument daje (likvidnost, zlatno bilansno pravilo); bruto marža na robi samo kad
  ima prodaje robe;
* pokazatelj čiji je imenilac nula ili negativan se ne računa („—”), jer bi broj bio besmislen.
"""
from collections import namedtuple
from datetime import date
from decimal import Decimal

from . import bilansi, izvoz

NULA = Decimal("0")
DANI = Decimal("365")
PDV = Decimal("1.2")

Velicina = namedtuple("Velicina", "kljuc naziv formula racun tok")
Pokazatelj = namedtuple("Pokazatelj", "odeljak naziv formula racun vrsta orijentir uslov", defaults=(None, None))


def _a(*aop):
    """Zbir AOP pozicija; '-0455' oduzima. Pozicije 0xxx su iz Bilansa stanja, 1xxx iz Bilansa uspeha."""
    def racun(bs, bu):
        ukupno = NULA
        for oznaka in aop:
            kod = oznaka.lstrip("-")
            iznos = (bs if kod < "1000" else bu)[kod]
            ukupno += -iznos if oznaka.startswith("-") else iznos
        return ukupno
    return racun


VELICINE = (
    # Bilans stanja — stanje na dan
    Velicina("stalna", "Stalna imovina", "0002", _a("0002"), False),
    Velicina("obrtna", "Obrtna imovina", "0030", _a("0030"), False),
    Velicina("zalihe", "Zalihe", "0031", _a("0031"), False),
    Velicina("kupci", "Potraživanja od kupaca", "0038", _a("0038"), False),
    Velicina("plasmani", "Kratkoročni finansijski plasmani", "0048", _a("0048"), False),
    Velicina("gotovina", "Gotovina", "0057", _a("0057"), False),
    Velicina("aktiva", "Ukupna aktiva", "0059", _a("0059"), False),
    Velicina("kapital", "Kapital", "0401 − 0455", _a("0401", "-0455"), False),
    Velicina("dugorocne", "Dugoročna rezervisanja i obaveze", "0415 + 0429 + 0430", _a("0415", "0429", "0430"), False),
    Velicina("kratkorocne", "Kratkoročne obaveze", "0431", _a("0431"), False),
    Velicina("obaveze", "Ukupne obaveze", "dugoročne + kratkoročne", _a("0415", "0429", "0430", "0431"), False),
    Velicina("dobavljaci", "Dobavljači", "0442", _a("0442"), False),
    Velicina("kamatonosni", "Kamatonosni dug", "0420 + 0433", _a("0420", "0433"), False),
    # Bilans uspeha — tok za period
    Velicina("prodaja", "Prihodi od prodaje", "1002 + 1005", _a("1002", "1005"), True),
    Velicina("roba", "Prihodi od prodaje robe", "1002", _a("1002"), True),
    Velicina("nabavna_roba", "Nabavna vrednost prodate robe", "1014", _a("1014"), True),
    Velicina("materijal", "Troškovi materijala, goriva i energije", "1015", _a("1015"), True),
    Velicina("usluge", "Troškovi proizvodnih usluga", "1022", _a("1022"), True),
    Velicina("poslovni_prihodi", "Poslovni prihodi", "1001", _a("1001"), True),
    Velicina("poslovni_rashodi", "Poslovni rashodi", "1013", _a("1013"), True),
    Velicina("poslovni_rezultat", "Poslovni rezultat", "1025 − 1026", _a("1025", "-1026"), True),
    Velicina("fin_prihodi", "Finansijski prihodi", "1027", _a("1027"), True),
    Velicina("fin_rashodi", "Finansijski rashodi", "1032", _a("1032"), True),
    Velicina("kamate", "Rashodi kamata", "1034", _a("1034"), True),
    Velicina("pre_poreza", "Rezultat pre oporezivanja", "1049 − 1050", _a("1049", "-1050"), True),
    Velicina("neto", "Neto rezultat", "1055 − 1056", _a("1055", "-1056"), True),
    Velicina("amortizacija", "Amortizacija", "1020", _a("1020"), True),
    Velicina("ebit", "EBIT (rezultat pre poreza i kamata)", "1049 − 1050 + 1034", _a("1049", "-1050", "1034"), True),
    Velicina("ebitda", "EBITDA", "EBIT + 1020", _a("1049", "-1050", "1034", "1020"), True),
)
STANJA = [v.kljuc for v in VELICINE if not v.tok]
TOKOVI = {v.kljuc for v in VELICINE if v.tok}


def _deli(brojilac, imenilac):
    if brojilac is None or imenilac is None or imenilac <= 0:
        return None
    return brojilac / imenilac


def _procenat(brojilac, imenilac):
    r = _deli(brojilac, imenilac)
    return None if r is None else r * 100


def _dani_zaliha(v, p, _pdv):
    if p["zalihe"] == 0:
        return NULA  # bez zaliha nema vezivanja
    obrt = _deli(v["nabavna_roba"] + v["materijal"], p["zalihe"])
    return _deli(DANI, obrt)


def _dso(v, p, pdv):
    return _deli(DANI * p["kupci"], v["prodaja"] * pdv)


def _dpo(v, p, pdv):
    return _deli(DANI * p["dobavljaci"], (v["nabavna_roba"] + v["materijal"] + v["usluge"]) * pdv)


def _ciklus(v, p, pdv):
    delovi = (_dani_zaliha(v, p, pdv), _dso(v, p, pdv), _dpo(v, p, pdv))
    return None if None in delovi else delovi[0] + delovi[1] - delovi[2]


LIK, SOL, PRO, AKT = "Likvidnost", "Solventnost i zaduženost", "Profitabilnost", "Aktivnost (obrt)"
POKAZATELJI = (
    Pokazatelj(LIK, "Opšti racio likvidnosti", "Obrtna imovina / Kratkoročne obaveze",
               lambda v, p, _: _deli(v["obrtna"], v["kratkorocne"]), "koef", (Decimal("1.5"), "≥ 1,5–2")),
    Pokazatelj(LIK, "Rigorozni (brzi) racio", "(Obrtna imovina − Zalihe) / Kratkoročne obaveze",
               lambda v, p, _: _deli(v["obrtna"] - v["zalihe"], v["kratkorocne"]), "koef", (Decimal("1"), "≥ 1")),
    Pokazatelj(LIK, "Racio gotovine", "(Gotovina + Kratkoročni fin. plasmani) / Kratkoročne obaveze",
               lambda v, p, _: _deli(v["gotovina"] + v["plasmani"], v["kratkorocne"]), "koef", (Decimal("0.2"), "≥ 0,2")),
    Pokazatelj(LIK, "Neto obrtni kapital", "Obrtna imovina − Kratkoročne obaveze",
               lambda v, p, _: v["obrtna"] - v["kratkorocne"], "iznos", (Decimal("0.01"), "> 0")),
    Pokazatelj(SOL, "Učešće kapitala u izvorima", "Kapital / Ukupna aktiva",
               lambda v, p, _: _procenat(v["kapital"], v["aktiva"]), "procenat"),
    Pokazatelj(SOL, "Stepen zaduženosti", "Ukupne obaveze / Ukupna aktiva",
               lambda v, p, _: _procenat(v["obaveze"], v["aktiva"]), "procenat"),
    Pokazatelj(SOL, "Dug / Kapital (D/E)", "Ukupne obaveze / Kapital",
               lambda v, p, _: _deli(v["obaveze"], v["kapital"]), "koef"),
    Pokazatelj(SOL, "Pokriće stalne imovine kapitalom", "Kapital / Stalna imovina",
               lambda v, p, _: _deli(v["kapital"], v["stalna"]), "koef"),
    Pokazatelj(SOL, "Zlatno bilansno pravilo", "(Kapital + Dugoročna rezervisanja i obaveze) / Stalna imovina",
               lambda v, p, _: _deli(v["kapital"] + v["dugorocne"], v["stalna"]), "koef", (Decimal("1"), "≥ 1")),
    Pokazatelj(SOL, "Pokriće kamata", "EBIT / Rashodi kamata",
               lambda v, p, _: _deli(v["ebit"], v["kamate"]), "koef"),
    Pokazatelj(SOL, "Neto dug / EBITDA", "(Kamatonosni dug − Gotovina) / EBITDA",
               lambda v, p, _: _deli(v["kamatonosni"] - v["gotovina"], v["ebitda"]), "koef"),
    Pokazatelj(PRO, "Bruto marža na robi", "(1002 − 1014) / 1002",
               lambda v, p, _: _procenat(v["roba"] - v["nabavna_roba"], v["roba"]), "procenat",
               uslov=lambda v: v["roba"] > 0),
    Pokazatelj(PRO, "EBITDA marža", "EBITDA / Poslovni prihodi",
               lambda v, p, _: _procenat(v["ebitda"], v["poslovni_prihodi"]), "procenat"),
    Pokazatelj(PRO, "Poslovna (operativna) marža", "Poslovni rezultat / Poslovni prihodi",
               lambda v, p, _: _procenat(v["poslovni_rezultat"], v["poslovni_prihodi"]), "procenat"),
    Pokazatelj(PRO, "Neto profitna marža", "Neto rezultat / Poslovni prihodi",
               lambda v, p, _: _procenat(v["neto"], v["poslovni_prihodi"]), "procenat"),
    Pokazatelj(PRO, "ROA", "Neto rezultat / Prosečna ukupna aktiva",
               lambda v, p, _: _procenat(v["neto"], p["aktiva"]), "procenat"),
    Pokazatelj(PRO, "ROE", "Neto rezultat / Prosečan kapital",
               lambda v, p, _: _procenat(v["neto"], p["kapital"]), "procenat"),
    Pokazatelj(AKT, "Obrt ukupne imovine", "Poslovni prihodi / Prosečna ukupna aktiva",
               lambda v, p, _: _deli(v["poslovni_prihodi"], p["aktiva"]), "koef"),
    Pokazatelj(AKT, "Obrt zaliha", "(1014 + 1015) / Prosečne zalihe",
               lambda v, p, _: _deli(v["nabavna_roba"] + v["materijal"], p["zalihe"]), "koef"),
    Pokazatelj(AKT, "Dani vezivanja zaliha", "365 / Obrt zaliha", _dani_zaliha, "dani"),
    Pokazatelj(AKT, "Dani naplate potraživanja (DSO)", "365 × Prosečni kupci / (Prihodi od prodaje × PDV)",
               _dso, "dani"),
    Pokazatelj(AKT, "Dani plaćanja dobavljačima (DPO)",
               "365 × Prosečni dobavljači / ((1014 + 1015 + 1022) × PDV)", _dpo, "dani"),
    Pokazatelj(AKT, "Ciklus konverzije gotovine", "Dani zaliha + DSO − DPO", _ciklus, "dani"),
)
ODELJCI = (LIK, SOL, PRO, AKT)


def velicine(bs, bu):
    """{ključ: iznos} iz AOP iznosa bilansa stanja i bilansa uspeha (`bilansi.izracunaj(...)["iznosi"]`)."""
    return {v.kljuc: v.racun(bs, bu) for v in VELICINE}


def pokazatelji(vel, vel_pre, faktor_godine=Decimal("1"), pdv=PDV):
    """{naziv pokazatelja: vrednost ili None}.

    `vel` su veličine kolone, `vel_pre` stanje na 31.12. prethodne godine (None — pokazatelji sa prosekom se ne
    računaju). Iznosi Bilansa uspeha se množe sa `faktor_godine` (preračun nepune godine na celu).
    """
    v = {k: iznos * faktor_godine if k in TOKOVI else iznos for k, iznos in vel.items()}
    p = {k: (vel[k] + vel_pre[k]) / 2 if vel_pre else None for k in STANJA}
    rezultat = {}
    for pok in POKAZATELJI:
        if pok.uslov and not pok.uslov(v):
            continue
        try:
            rezultat[pok.naziv] = pok.racun(v, p, pdv)
        except TypeError:  # prosek nije poznat (None u računu)
            rezultat[pok.naziv] = None
    return rezultat


def u_redu(pok, vrednost):
    if pok.orijentir is None or vrednost is None:
        return None
    return vrednost >= pok.orijentir[0]


# --- kolone po godinama -----------------------------------------------------------------------------

def _dana_u_godini(godina):
    return (date(godina, 12, 31) - date(godina, 1, 1)).days + 1


def izradi(na_dan, broj_godina=5, pdv=PDV):
    """Kolone od najstarije godine do godine izabranog dana; poslednja ide do izabranog dana."""
    stanja = {}

    def stanje(dan):
        if dan not in stanja:
            salda = bilansi.salda_stanja(dan)
            stanja[dan] = bilansi.izracunaj("BS", salda) if salda is not None else None
        return stanja[dan]

    kolone = []
    for godina in range(na_dan.year - broj_godina + 1, na_dan.year + 1):
        do = na_dan if godina == na_dan.year else date(godina, 12, 31)
        od = date(godina, 1, 1)
        dana, u_godini = (do - od).days + 1, _dana_u_godini(godina)
        kolona = {"godina": godina, "do": do, "naslov": str(godina) if dana == u_godini else f"{godina} (do {do:%d.%m.})",
                  "preracunato": dana < u_godini, "velicine": None, "pokazatelji": {}, "kontrole": []}
        bs, bs_pre = stanje(do), stanje(date(godina - 1, 12, 31))
        salda_bu = bilansi.salda_uspeha(od, do)
        if bs is None or salda_bu is None:
            kolona["kontrole"].append(("Nema preuzetih knjiženja za ovu godinu.", None))
            kolone.append(kolona)
            continue
        bu = bilansi.izracunaj("BU", salda_bu)
        vel = velicine(bs["iznosi"], bu["iznosi"])
        vel_pre = velicine(bs_pre["iznosi"], bu["iznosi"]) if bs_pre else None
        kolona["velicine"] = vel
        kolona["pokazatelji"] = pokazatelji(vel, vel_pre, Decimal(u_godini) / Decimal(dana), pdv)
        razlika = bs["iznosi"]["0059"] - bs["iznosi"]["0456"]
        if razlika:
            kolona["kontrole"].append((f"Aktiva − pasiva = {izvoz.prikaz(razlika, 'iznos')}; bilans nije u ravnoteži.", False))
        if bs["nerasporedjeno"] or bu["nerasporedjeno"]:
            kolona["kontrole"].append(("Ima konta bez pozicije u obrascu (vidi Bilans stanja / uspeha).", False))
        if not bs_pre:
            kolona["kontrole"].append((f"Nema stanja na 31.12.{godina - 1}.; pokazatelji sa prosekom se ne računaju.", None))
        if kolona["preracunato"]:
            kolona["kontrole"].append((f"Nepuna godina ({dana} dana): Bilans uspeha preračunat na godinu za pokazatelje.", None))
            kolona["kontrole"].append(("Deo troškova i obaveza knjiži se tek na kraju godine (obračuni, razgraničenja, "
                                       "zaključak), pa pokazatelji nepune godine nisu uporedivi sa zaključenim godinama.", False))
        kolone.append(kolona)

    redovi = []
    for odeljak in ODELJCI:
        stavke = []
        for pok in POKAZATELJI:
            if pok.odeljak != odeljak or not any(pok.naziv in k["pokazatelji"] for k in kolone):
                continue
            vrednosti = [k["pokazatelji"].get(pok.naziv) for k in kolone]
            stavke.append({"naziv": pok.naziv, "formula": pok.formula, "vrsta": pok.vrsta,
                           "orijentir": pok.orijentir[1] if pok.orijentir else "",
                           "vrednosti": [(vr, u_redu(pok, vr)) for vr in vrednosti]})
        redovi.append((odeljak, stavke))
    pomocne = [{"naziv": v.naziv, "formula": v.formula, "tok": v.tok,
                "vrednosti": [k["velicine"][v.kljuc] if k["velicine"] else None for k in kolone]} for v in VELICINE]
    return {"kolone": kolone, "odeljci": redovi, "pomocne": pomocne, "pdv": pdv}


# --- izvoz --------------------------------------------------------------------------------------------

JEDINICE = {"koef": "", "procenat": " (%)", "dani": " (dana)", "iznos": " (RSD)"}


def dokument(rezultat, opis):
    naslovi = [k["naslov"] for k in rezultat["kolone"]]
    kolone = [izvoz.Kolona("Pokazatelj"), izvoz.Kolona("Formula"), izvoz.Kolona("Orijentir")] + \
             [izvoz.Kolona(n, "iznos") for n in naslovi]
    redovi = []
    for odeljak, stavke in rezultat["odeljci"]:
        redovi.append([odeljak.upper(), "", "", *[None] * len(naslovi)])
        for s in stavke:
            redovi.append([s["naziv"] + JEDINICE[s["vrsta"]], s["formula"], s["orijentir"],
                           *[vr for vr, _ in s["vrednosti"]]])
    pomocne = [[p["naziv"] + (" (za period)" if p["tok"] else ""), p["formula"], "", *p["vrednosti"]]
               for p in rezultat["pomocne"]]
    kontrole = " · ".join(f"{k['naslov']}: {poruka}" for k in rezultat["kolone"] for poruka, _ in k["kontrole"])
    napomena = (f"Izvor: Bilans stanja i Bilans uspeha iz knjiženja Finansija. Faktor PDV-a u DSO/DPO: "
                f"{izvoz.prikaz(rezultat['pdv'], 'kurs').rstrip('0').rstrip(',')}. Prosek = (kraj perioda + 31.12. "
                "prethodne godine) / 2. „—” — pokazatelj se ne računa (imenilac je nula ili negativan, ili nema proseka).")
    return izvoz.Dokument(naslov="Racio analiza", period=opis, napomena=napomena, filteri=kontrole, tabele=[
        izvoz.Tabela("Pokazatelji", kolone, redovi),
        izvoz.Tabela("Pomoćne veličine (iznosi u RSD)", [izvoz.Kolona("Veličina"), izvoz.Kolona("AOP"),
                                                          izvoz.Kolona("")] + [izvoz.Kolona(n, "iznos") for n in naslovi],
                     pomocne)])
