"""Lista kategorija arhivske građe i dokumentarnog materijala sa rokovima čuvanja: čitanje, provera, uvoz.

Ulaz je Word (.docx, tabela sa kolonama Redni broj | Klasifikaciona oznaka | Kategorija | Rok
čuvanja) ili Excel sa istim kolonama (očišćena lista od arhiviste). Red bez rednog broja je
**grupa**: nosi klasifikacionu oznaku i naziv, a kategorije ispod nje pripadaju toj oznaci.

`sporne_stavke()` vraća samo ono o čemu arhivista treba da odluči, poređano po važnosti, da se
ne čisti ceo dokument od 454 reda. Isti naziv u različitim grupama nije duplikat (npr. „Zapisi
sistema menadžmenta" posebno za sertifikaciono telo i za laboratorije); sporno je tek kada
takve stavke imaju različit rok.
"""
import difflib
import re
import zipfile
from dataclasses import dataclass, field
from xml.etree import ElementTree

from django.db import transaction

from arhiva.models import GrupaKategorija, Kategorija, VerzijaListe

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
POCETAK = Kategorija.PocetakRoka

# Oznake koje Lista koristi za službe i centre (provereno na Listi od 10.03.2023.). Oznaka van
# ovog skupa se prijavljuje kao sporna (npr. 426), a zajednička oznaka kao „41/42/43/44" nije sporna.
OCEKIVANE_OZNAKE = {"20", "30", "41", "42", "43", "44", "50", "60", "70", "81", "82", "120"}

# Isti dokument pod različitim nazivima, sa rokovima koji moraju biti jednaki (plan, 4.4 #3).
ISTI_DOKUMENT = {
    "Izlazni računi": re.compile(r"izlazn\w*\s+račun", re.I),
    "Ulazni računi": re.compile(r"ulazn\w*\s+račun", re.I),
}

PRIORITETI = [
    ("isti_naziv_razlicit_rok", "Isti naziv, različit rok",
     "Odlučiti da li je razlika u roku namerna (različita služba) ili greška."),
    ("protivrecan_rok", "Isti dokument, različit rok",
     "Odlučiti koji rok važi za IMS i ostaviti jednu stavku kao preporučenu."),
    ("duplikat", "Duplikat u istoj grupi",
     "Ista stavka dva puta u istoj grupi. Jedna se označava kao duplikat i ne nudi se pri izboru."),
    ("neobicna_oznaka", "Neobična klasifikaciona oznaka",
     "Oznaka ne odgovara nijednoj službi ni centru. Proveriti da li je greška u kucanju."),
    ("nejasan_rok", "Rok sa izuzetkom ili nejasan",
     "Rok ne može da se izračuna automatski. Odrediti pravilo ili predmete ove vrste voditi pojedinačno."),
    ("uslovni_rok", "Rok teče od događaja",
     "Potvrditi od kog događaja rok teče (npr. prestanak važenja, istek zakupa)."),
    ("trajno_operativno", "Trajno operativno",
     "Odrediti šta „trajno operativno” znači za izlučivanje i predaju arhivu (plan, O-6)."),
    ("isti_naziv_isti_rok", "Isti naziv u više grupa (isti rok)",
     "Verovatno u redu (različite službe). Proveriti samo da li treba jedna zajednička stavka."),
    ("pravopis_roka", "Pravopis roka",
     "Samo tekst (npr. „5 godine”). Rok se računa ispravno; ispraviti pri sledećoj izmeni Liste."),
]


@dataclass
class Stavka:
    redni_broj: int
    oznaka: str
    grupa: str
    grupa_redosled: int
    naziv: str
    rok_tekst: str
    rok_godina: int | None = None
    trajno: bool = False
    operativno: bool = False
    pocetak_roka: str = POCETAK.ZAVRSETAK_PREDMETA
    napomena_roka: str = ""
    nejasan_rok: bool = False
    pravopis: bool = False


@dataclass
class Sporno:
    vrsta: str
    redni_brojevi: list
    opis: str
    rokovi: str = ""
    detalji: list = field(default_factory=list)


def _cist(tekst):
    return " ".join(str(tekst or "").split())


def _kljuc(naziv):
    return " ".join(re.sub(r"[^\wčćšđž ]", " ", naziv.lower()).split())


# ---------------------------------------------------------------- čitanje

def redovi_docx(putanja):
    """Redovi prve tabele u .docx (4 kolone), bez zaglavlja."""
    with zipfile.ZipFile(putanja) as z:
        koren = ElementTree.fromstring(z.read("word/document.xml"))
    tabela = koren.find(f".//{W}tbl")
    if tabela is None:
        raise ValueError("U dokumentu nema tabele sa kategorijama.")
    redovi = []
    for tr in tabela.findall(f"{W}tr"):
        celije = []
        for tc in tr.findall(f"{W}tc"):
            pasusi = ["".join(t.text or "" for t in p.iter(f"{W}t")) for p in tc.findall(f"{W}p")]
            celije.append(_cist(" ".join(pasusi)))
        redovi.append(celije)
    return redovi[1:]


def redovi_xlsx(putanja):
    from openpyxl import load_workbook

    list_ = load_workbook(putanja, read_only=True, data_only=True).worksheets[0]
    redovi = [[_cist(v) for v in red[:4]] for red in list_.iter_rows(values_only=True)]
    return [r for r in redovi[1:] if any(r)]


def procitaj(putanja):
    """Stavke Liste iz .docx ili .xlsx."""
    ime = str(putanja).lower()
    if ime.endswith(".docx"):
        redovi = redovi_docx(putanja)
    elif ime.endswith(".xlsx"):
        redovi = redovi_xlsx(putanja)
    else:
        raise ValueError("Lista se uvozi iz .docx ili .xlsx. Stari .doc prvo sačuvajte kao .docx (Word → Save As).")
    stavke, oznaka, grupa, redosled = [], "", "", 0
    for red in redovi:
        rb, oz, naziv, rok = (red + ["", "", "", ""])[:4]
        if not rb:
            if naziv:
                redosled += 1
                oznaka, grupa = oz, naziv
            continue
        broj = re.match(r"^(\d+)\.?$", rb)
        if not broj:
            raise ValueError(f"Redni broj „{rb}” nije broj (kategorija „{naziv[:40]}”).")
        stavka = Stavka(redni_broj=int(broj.group(1)), oznaka=oz or oznaka, grupa=grupa, grupa_redosled=redosled,
                        naziv=naziv, rok_tekst=rok)
        _rok(stavka)
        stavke.append(stavka)
    return stavke


def _rok(stavka):
    tekst = _cist(stavka.rok_tekst)
    if re.fullmatch(r"trajno", tekst, re.I):
        stavka.trajno = True
        return
    if re.fullmatch(r"trajno\s+operativno", tekst, re.I):
        stavka.trajno = stavka.operativno = True
        return
    m = re.match(r"^(\d+)\s+(godin[aeu]?)\b\s*(.*)$", tekst, re.I)
    if not m:
        stavka.nejasan_rok = True
        stavka.pocetak_roka = POCETAK.RUCNO
        stavka.napomena_roka = tekst
        return
    broj, rec, ostatak = int(m.group(1)), m.group(2).lower(), m.group(3).strip(" ,")
    stavka.rok_godina = broj
    # 2, 3, 4 (i 22–24, 32–34 …) godine; ostalo godina (1, 5–20, 21, 25 …)
    ispravno = "godine" if broj % 10 in (2, 3, 4) and not 12 <= broj % 100 <= 14 else "godina"
    stavka.pravopis = rec != ispravno
    if not ostatak:
        return
    stavka.napomena_roka = ostatak
    malo = ostatak.lower()
    if "osim" in malo:
        stavka.nejasan_rok = True
        stavka.pocetak_roka = POCETAK.RUCNO
    elif "zakup" in malo:
        stavka.pocetak_roka = POCETAK.PRESTANAK_ZAKUPA
    elif "važenja" in malo or "vazenja" in malo:
        stavka.pocetak_roka = POCETAK.PRESTANAK_VAZENJA
    elif "okončanj" in malo or "okoncanj" in malo:
        stavka.pocetak_roka = POCETAK.OKONCANJE_POSTUPKA
    elif "ugovor" in malo:
        stavka.pocetak_roka = POCETAK.ISTEK_UGOVORA
    elif "radnog odnosa" in malo:
        stavka.pocetak_roka = POCETAK.PRESTANAK_RADNOG_ODNOSA
    else:
        stavka.pocetak_roka = POCETAK.RUCNO


# ---------------------------------------------------------------- provera

def _isti_rok(clanovi):
    return len({_cist(s.rok_tekst).lower() for s in clanovi}) == 1


def grupe_duplikata(stavke):
    """Iste stavke u istoj grupi (naziv se poklapa bar 97 %, npr. „sistemskog” / „sistematskog”),
    kao spiskovi poređani po rednom broju; tri ista naziva su jedna grupa, ne dva para."""
    po_grupi, rezultat = {}, []
    for s in stavke:
        po_grupi.setdefault(s.grupa_redosled, []).append(s)
    for clanovi in po_grupi.values():
        roditelj = {s.redni_broj: s.redni_broj for s in clanovi}

        def koren(rb):
            while roditelj[rb] != rb:
                rb = roditelj[rb]
            return rb

        for i, a in enumerate(clanovi):
            for b in clanovi[i + 1:]:
                if difflib.SequenceMatcher(None, _kljuc(a.naziv), _kljuc(b.naziv)).ratio() >= 0.97:
                    roditelj[koren(b.redni_broj)] = koren(a.redni_broj)
        skupovi = {}
        for s in clanovi:
            skupovi.setdefault(koren(s.redni_broj), []).append(s)
        rezultat.extend(sorted(v, key=lambda x: x.redni_broj) for v in skupovi.values() if len(v) > 1)
    return sorted(rezultat, key=lambda v: v[0].redni_broj)


def duplikati(stavke):
    """{redni broj duplikata: redni broj prve stavke}, samo kada sve iste stavke imaju isti rok.
    Ako se rok razlikuje, odluku donosi arhivista (sporno „isti naziv, različit rok”)."""
    return {s.redni_broj: grupa[0].redni_broj
            for grupa in grupe_duplikata(stavke) if _isti_rok(grupa) for s in grupa[1:]}


def sporne_stavke(stavke):
    """Sporne stavke poređane po važnosti (PRIORITETI)."""
    sporno = []
    opis = lambda s: f"{s.redni_broj}. {s.naziv}"
    rok = lambda s: s.rok_tekst or "—"

    # isti naziv u različitim grupama
    po_nazivu = {}
    for s in stavke:
        po_nazivu.setdefault(_kljuc(s.naziv), []).append(s)
    for grupa in po_nazivu.values():
        grupe = {s.grupa_redosled for s in grupa}
        if len(grupe) < 2:
            continue
        vrsta = "isti_naziv_razlicit_rok" if len({_cist(s.rok_tekst).lower() for s in grupa}) > 1 else "isti_naziv_isti_rok"
        sporno.append(Sporno(vrsta, [s.redni_broj for s in grupa], grupa[0].naziv,
                             "; ".join(f"{s.redni_broj}: {rok(s)} ({s.oznaka} · {s.grupa})" for s in grupa)))

    for naziv, obrazac in ISTI_DOKUMENT.items():
        nadjene = [s for s in stavke if obrazac.search(s.naziv)]
        if len({_cist(s.rok_tekst).lower() for s in nadjene}) > 1:
            sporno.append(Sporno("protivrecan_rok", [s.redni_broj for s in nadjene], naziv,
                                 "; ".join(f"{s.redni_broj}: {rok(s)}" for s in nadjene),
                                 [opis(s) for s in nadjene]))

    for grupa in grupe_duplikata(stavke):
        vrsta = "duplikat" if _isti_rok(grupa) else "isti_naziv_razlicit_rok"
        sporno.append(Sporno(vrsta, [s.redni_broj for s in grupa], grupa[0].naziv,
                             "; ".join(f"{s.redni_broj}: {rok(s)}" for s in grupa)
                             + ("" if vrsta == "duplikat" else f" (ista grupa: {grupa[0].oznaka} · {grupa[0].grupa})")))

    for oznaka in sorted({s.oznaka for s in stavke}):
        if not set(re.split(r"[/,+ ]+", oznaka)) <= OCEKIVANE_OZNAKE:
            clanovi = [s for s in stavke if s.oznaka == oznaka]
            sporno.append(Sporno("neobicna_oznaka", [s.redni_broj for s in clanovi],
                                 f"Oznaka {oznaka} · {clanovi[0].grupa}", "", [opis(s) for s in clanovi]))

    for s in stavke:
        if s.nejasan_rok:
            sporno.append(Sporno("nejasan_rok", [s.redni_broj], s.naziv, rok(s)))
        elif s.pocetak_roka != POCETAK.ZAVRSETAK_PREDMETA:
            sporno.append(Sporno("uslovni_rok", [s.redni_broj], s.naziv,
                                 f"{rok(s)} → {POCETAK(s.pocetak_roka).label.lower()}"))

    operativno = [s for s in stavke if s.operativno]
    if operativno:
        sporno.append(Sporno("trajno_operativno", [s.redni_broj for s in operativno],
                             f"{len(operativno)} stavki sa rokom „Trajno operativno”", "Trajno operativno",
                             [opis(s) for s in operativno]))

    pravopis = [s for s in stavke if s.pravopis]
    if pravopis:
        sporno.append(Sporno("pravopis_roka", [s.redni_broj for s in pravopis], "Oblik reči „godina” u roku",
                             "; ".join(f"{s.redni_broj}: {s.rok_tekst}" for s in pravopis)))

    redosled = {kljuc: i for i, (kljuc, _, _) in enumerate(PRIORITETI)}
    return sorted(sporno, key=lambda x: (redosled[x.vrsta], x.redni_brojevi))


# ---------------------------------------------------------------- uvoz i izveštaj

@transaction.atomic
def uvezi(stavke, *, naziv, datum_donosenja=None, izvor="", aktivna=False, korisnik=None):
    """Nova verzija Liste. Stara verzija se ne menja; aktivna može biti samo jedna."""
    if aktivna:
        VerzijaListe.objects.filter(aktivna=True).update(aktivna=False)
    verzija = VerzijaListe.objects.create(naziv=naziv, datum_donosenja=datum_donosenja, izvor=izvor,
                                          aktivna=aktivna, uvezao=korisnik)
    grupe = {}
    for s in stavke:
        if s.grupa_redosled not in grupe:
            grupe[s.grupa_redosled] = GrupaKategorija.objects.create(
                verzija=verzija, redosled=s.grupa_redosled, klasifikaciona_oznaka=s.oznaka, naziv=s.grupa)
    kategorije = {}
    for s in stavke:
        kategorije[s.redni_broj] = Kategorija.objects.create(
            verzija=verzija, grupa=grupe[s.grupa_redosled], redni_broj=s.redni_broj, naziv=s.naziv,
            rok_tekst=s.rok_tekst, rok_godina=s.rok_godina, trajno=s.trajno, operativno=s.operativno,
            pocetak_roka=s.pocetak_roka, napomena_roka=s.napomena_roka)
    for duplikat, prvi in duplikati(stavke).items():
        Kategorija.objects.filter(pk=kategorije[duplikat].pk).update(duplikat_od=kategorije[prvi], aktivna=False)
    return verzija


def izvestaj_xlsx(stavke, sporne, putanja, *, naslov="Lista kategorija — sporne stavke"):
    """Excel za arhivistu: list „Sporne stavke” (za odluku) i list „Sve kategorije” (kako je pročitano)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    nazivi = {kljuc: (naziv, sta) for kljuc, naziv, sta in PRIORITETI}
    zaglavlje_stil = dict(font=Font(bold=True, color="FFFFFF"), fill=PatternFill("solid", fgColor="14395B"),
                          alignment=Alignment(vertical="center", wrap_text=True))
    kn = Workbook()
    ws = kn.active
    ws.title = "Sporne stavke"
    ws.append([naslov])
    ws["A1"].font = Font(bold=True, size=13, color="14395B")
    ws.append(["Vrsta", "Redni brojevi", "Stavka", "Rok u Listi", "Šta treba odlučiti", "Detalji", "Odluka arhiviste"])
    for celija in ws[2]:
        for k, v in zaglavlje_stil.items():
            setattr(celija, k, v)
    for s in sporne:
        naziv, sta = nazivi[s.vrsta]
        ws.append([naziv, ", ".join(map(str, s.redni_brojevi)), s.opis, s.rokovi, sta, "\n".join(s.detalji), ""])
    for red in ws.iter_rows(min_row=3):
        for celija in red:
            celija.alignment = Alignment(vertical="top", wrap_text=True)
    for kolona, sirina in zip("ABCDEFG", (24, 16, 48, 38, 44, 50, 30)):
        ws.column_dimensions[kolona].width = sirina
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:G{ws.max_row}"

    sve = kn.create_sheet("Sve kategorije")
    sve.append(["Redni broj", "Klasifikaciona oznaka", "Grupa", "Kategorija", "Rok (kako piše)", "Rok (godina)",
                "Trajno", "Trajno operativno", "Rok teče", "Napomena uz rok", "Duplikat od"])
    for celija in sve[1]:
        for k, v in zaglavlje_stil.items():
            setattr(celija, k, v)
    dup = duplikati(stavke)
    for s in stavke:
        sve.append([s.redni_broj, s.oznaka, s.grupa, s.naziv, s.rok_tekst, s.rok_godina, "da" if s.trajno else "",
                    "da" if s.operativno else "", POCETAK(s.pocetak_roka).label, s.napomena_roka,
                    dup.get(s.redni_broj, "")])
    for kolona, sirina in enumerate((10, 12, 40, 60, 24, 10, 8, 10, 24, 30, 10), start=1):
        sve.column_dimensions[get_column_letter(kolona)].width = sirina
    sve.freeze_panes = "A2"
    sve.auto_filter.ref = f"A1:K{sve.max_row}"
    kn.save(putanja)
