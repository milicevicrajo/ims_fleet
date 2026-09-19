"""Pravi dokumentacija/IMS-ERP-dokumentacija.md od poglavlja iz dokumentacija/docs/.

Pokretanje iz korena projekta:

    python dokumentacija/spoji-dokumentaciju.py

OVO NIJE JEDNOKRATNA SKRIPTA. Objedinjeni dokument se ne uredjuje rucno -- uredjuju
se pojedinacna poglavlja u dokumentacija/docs/, pa se on pravi ponovo. Ako dodas novo
poglavlje, upisi ga u REDOSLED nize.

Sta radi:
  1. spusta sve naslove za jedan nivo, da naslov dokumenta bude jedini H1;
  2. veze medju poglavljima pretvara u sidra, a veze ka kodu preracunava iz novog
     polozaja (dokumentacija/ umesto dokumentacija/docs/ ili .../obracuni/);
  3. pravi sadrzaj od naslova poglavlja i njihovih odeljaka.

Naslovi unutar blokova koda se ne diraju. Na kraju ispisuje ponovljena sidra i veze
koje nisu mogle da se razrese -- ako se pojavi UPOZORENJA, nesto treba popraviti u
izvornom poglavlju, ne ovde.
"""
import io
import os
import re
import sys
from collections import Counter

KOREN = "dokumentacija"
IZLAZ = os.path.join(KOREN, "IMS-ERP-dokumentacija.md")

REDOSLED = [
    "dokumentacija/docs/01-pregled-sistema.md",
    "dokumentacija/docs/02-arhitektura.md",
    "dokumentacija/docs/03-moduli.md",
    "dokumentacija/docs/moduli/03-01-flota.md",
    "dokumentacija/docs/moduli/03-02-kadrovi.md",
    "dokumentacija/docs/moduli/03-03-finansije.md",
    "dokumentacija/docs/moduli/03-04-nabavka.md",
    "dokumentacija/docs/moduli/03-05-potrazivanja.md",
    "dokumentacija/docs/moduli/03-06-ugovori.md",
    "dokumentacija/docs/moduli/03-07-menice.md",
    "dokumentacija/docs/moduli/03-08-mobilni.md",
    "dokumentacija/docs/moduli/03-09-isplate.md",
    "dokumentacija/docs/moduli/03-10-administracija.md",
    "dokumentacija/docs/04-baza-podataka.md",
    "dokumentacija/docs/05-poslovni-procesi.md",
    "dokumentacija/docs/06-analize-i-obracuni.md",
    "dokumentacija/docs/obracuni/06-01-finansije.md",
    "dokumentacija/docs/obracuni/06-02-flota-gorivo.md",
    "dokumentacija/docs/obracuni/06-03-flota-troskovi.md",
    "dokumentacija/docs/obracuni/06-04-flota-ugovori-polise.md",
    "dokumentacija/docs/obracuni/06-05-flota-izvestaji.md",
    "dokumentacija/docs/obracuni/06-06-kadrovi.md",
    "dokumentacija/docs/obracuni/06-07-mobilni.md",
    "dokumentacija/docs/obracuni/06-08-potrazivanja.md",
    "dokumentacija/docs/obracuni/06-09-nabavka.md",
    "dokumentacija/docs/obracuni/06-10-isplate.md",
    "dokumentacija/docs/obracuni/06-11-ugovori-i-menice.md",
    "dokumentacija/docs/obracuni/06-12-flota-ekonomika.md",
    "dokumentacija/docs/07-integracije.md",
    "dokumentacija/docs/08-instalacija-i-pokretanje.md",
    "dokumentacija/docs/09-odrzavanje.md",
    "dokumentacija/docs/10-poznati-problemi.md",
    "dokumentacija/docs/11-plan-razvoja.md",
    "dokumentacija/docs/12-recnik-poslovnih-pojmova.md",
    "dokumentacija/docs/uprava/pregled-ims-erp-a.md",
    "dokumentacija/ddl-nasledjenih-pogleda/README.md",
]

# Poglavlja koja u objedinjenom dokumentu dobijaju drugaciji naslov od izvornog.
PRENAZIV = {
    "dokumentacija/docs/uprava/pregled-ims-erp-a.md": "Prilog A — Pregled za upravu",
    "dokumentacija/ddl-nasledjenih-pogleda/README.md": "Prilog B — DDL nasleđenih SQL pogleda",
}


# Na Windowsu normpath daje obrnute kose crte; kljucevi svuda moraju biti isti oblik.
REDOSLED = [os.path.normpath(p) for p in REDOSLED]
PRENAZIV = {os.path.normpath(k): v for k, v in PRENAZIV.items()}


def sidro(tekst):
    """Isti postupak koji GitHub koristi za pravljenje sidra iz naslova."""
    tekst = re.sub(r"`", "", tekst.strip().lower())
    tekst = re.sub(r"[^\w\s-]", "", tekst, flags=re.UNICODE)
    return re.sub(r"\s", "-", tekst)


def redovi_van_koda(sadrzaj):
    """Vraca (redosled, redovi, u_kodu) gde u_kodu kaze da li je red u bloku koda."""
    u_kodu = False
    ograda = None
    for red in sadrzaj.split("\n"):
        m = re.match(r"^\s*(`{3,}|~{3,})", red)
        if m:
            if not u_kodu:
                u_kodu, ograda = True, m.group(1)[0]
            elif m.group(1)[0] == ograda:
                u_kodu, ograda = False, None
            yield red, True
            continue
        yield red, u_kodu


def naslovi(sadrzaj):
    """Stvarni naslovi, bez onih unutar blokova koda."""
    out = []
    for red, u_kodu in redovi_van_koda(sadrzaj):
        if u_kodu:
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", red)
        if m:
            out.append((len(m.group(1)), m.group(2)))
    return out


def main():
    nema = [p for p in REDOSLED if not os.path.exists(p)]
    if nema:
        sys.exit("Nedostaju: " + ", ".join(nema))

    skup = set(REDOSLED)
    sadrzaji = {p: io.open(p, encoding="utf-8").read() for p in REDOSLED}

    # 1. Naslov poglavlja -> sidro, za veze koje pokazuju na ceo fajl.
    poglavlje_sidro, poglavlje_naslov = {}, {}
    for p in REDOSLED:
        h = [t for n, t in naslovi(sadrzaji[p]) if n == 1]
        naslov = PRENAZIV.get(p, h[0] if h else os.path.basename(p))
        poglavlje_naslov[p] = naslov
        poglavlje_sidro[p] = sidro(naslov)

    # 2. Sva sidra u objedinjenom dokumentu, radi provere jedinstvenosti.
    svi_naslovi = []
    for p in REDOSLED:
        for nivo, tekst in naslovi(sadrzaji[p]):
            svi_naslovi.append((p, nivo, PRENAZIV.get(p, tekst) if nivo == 1 else tekst))
    broj = Counter(sidro(t) for _, _, t in svi_naslovi)
    dvojnici = {s for s, n in broj.items() if n > 1}

    delovi, upozorenja = [], []

    def prepisi_vezu(izvorni_fajl, cilj):
        if cilj.startswith(("http://", "https://", "mailto:")):
            return cilj
        if cilj.startswith("#"):
            if cilj[1:] in dvojnici:
                upozorenja.append(f"{izvorni_fajl}: sidro '{cilj}' nije jedinstveno")
            return cilj
        put, _, ankor = cilj.partition("#")
        put = put.strip("<>")
        resen = os.path.normpath(os.path.join(os.path.dirname(izvorni_fajl), put))
        if resen in skup:
            if ankor:
                if ankor in dvojnici:
                    upozorenja.append(f"{izvorni_fajl}: sidro '#{ankor}' nije jedinstveno")
                return "#" + ankor
            return "#" + poglavlje_sidro[resen]
        # Veza van dokumenta (kod, slike): preracunaj iz novog polozaja.
        nova = os.path.relpath(resen, KOREN).replace(os.sep, "/")
        if not os.path.exists(resen):
            upozorenja.append(f"{izvorni_fajl}: ne postoji '{put}'")
        return nova + (("#" + ankor) if ankor else "")

    for p in REDOSLED:
        novi = []
        prvi_h1 = True
        for red, u_kodu in redovi_van_koda(sadrzaji[p]):
            if not u_kodu:
                m = re.match(r"^(#{1,6})(\s+)(.+?)\s*$", red)
                if m:
                    nivo, tekst = len(m.group(1)), m.group(3)
                    if nivo == 1 and prvi_h1:
                        tekst, prvi_h1 = PRENAZIV.get(p, tekst), False
                    red = "#" * (nivo + 1) + m.group(2) + tekst
                else:
                    red = re.sub(
                        r"(\]\()\s*(<[^>]+>|[^)\s]+)\s*(\))",
                        lambda mm: mm.group(1) + prepisi_vezu(p, mm.group(2)) + mm.group(3),
                        red,
                    )
            novi.append(red)
        delovi.append("\n".join(novi).strip() + "\n")

    # 3. Sadrzaj: poglavlja (nekadasnji H1) i njihovi odeljci (nekadasnji H2).
    sadrzaj_redovi = []
    for p in REDOSLED:
        sadrzaj_redovi.append(f"- [{poglavlje_naslov[p]}](#{poglavlje_sidro[p]})")
        for nivo, tekst in naslovi(sadrzaji[p]):
            if nivo == 2:
                sadrzaj_redovi.append(f"    - [{tekst}](#{sidro(tekst)})")

    zaglavlje = f"""# IMS ERP — dokumentacija sistema

> **Objedinjeno izdanje.** Sadrži svih {len(REDOSLED)} poglavlja iz
> `dokumentacija/docs/` u jednom dokumentu, radi štampe i arhiviranja.
> Pojedinačna poglavlja i dalje postoje i **ona se održavaju** — ovaj dokument se
> pravi iz njih i pri svakoj izmeni se pravi ponovo.
>
> Status tvrdnji kroz ceo dokument: **[P]** potvrđeno kodom, bazom ili postojećom
> dokumentacijom, **[Z]** zaključeno, **[N]** nepotvrđeno.

| | |
|---|---|
| **Sistem** | IMS ERP — Django monolit nad Microsoft SQL Server bazom |
| **Obuhvat** | 10 poslovnih modula, 74 obračuna, 48 zabeleženih problema |
| **Sastavljeno** | 18.09.2026. |
| **Izvor** | Izvorni kod, baza, SQL upiti i pogledi, konfiguracija, ekrani i izveštaji |

---

## Sadržaj

{chr(10).join(sadrzaj_redovi)}

---

"""

    io.open(IZLAZ, "w", encoding="utf-8", newline="").write(
        zaglavlje + "\n---\n\n".join(delovi)
    )

    redova = len(io.open(IZLAZ, encoding="utf-8").read().splitlines())
    print(f"Napisano: {IZLAZ}")
    print(f"Poglavlja: {len(REDOSLED)}   Redova: {redova}   Stavki u sadrzaju: {len(sadrzaj_redovi)}")
    if dvojnici:
        print(f"\nPONOVLJENA SIDRA ({len(dvojnici)}) -- veze ka njima su neodredjene:")
        for s in sorted(dvojnici)[:40]:
            print(f"   {s}  ({broj[s]}x)")
    if upozorenja:
        print(f"\nUPOZORENJA ({len(upozorenja)}):")
        for u in sorted(set(upozorenja))[:40]:
            print(f"   {u}")


if __name__ == "__main__":
    main()
