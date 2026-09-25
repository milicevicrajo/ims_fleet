"""Razvrstavanje sifara posla u tri porodice.

Pravilo je izvedeno iz merenja nad produkcionom bazom 21.09.2026.
(`dokumentacija/popis-sifara-posla-korak-0.md`) i namerno je ovde, kao ciste funkcije
bez baze, da se moze proveriti testom.

Sta je mereno i zasto pravilo izgleda ovako:

* Centri poslovnog i naucnog bloka su `2` i `3` (odluka narucioca 25.09.2026.), kako stoje u
  `posao.blok`, `FinanceJob.center` i `OrganizationalUnit.center`. Knjizenja ih vode kao
  organizacione jedinice `20` i `30`, pa se oznaka centra u registru izvodi iz jedinice
  knjizenja preko `OZNAKA_CENTRA_IZ_KNJIZENJA`. Kod dve sifre `FinanceJob.center` je prazan,
  zato se pripadnost poslovnog posla cita iz **prve dve cifre same sifre**.
* Prefiks se koristi **samo pri prvom uvozu, kao predlog**. Knjizenja ga potvrdjuju:
  za 92 od 118 upotrebljenih sifara najcesca organizaciona jedinica knjizenja jednaka je
  prve dve cifre sifre. Svih 24 odstupanja su nauka.
* Nauka (porodica B) se knjizi iskljucivo na organizacionu jedinicu `30` (centar `3`).
  Sifra je `3` + **sifra radnika iz Kadrova** (3 cifre) + **broj projekta** (slobodan unos);
  koren `3` + radnik + `00` je sam radnik. Nosioci `133`, `233`, `333` nisu radnici nego
  zbirne institutske teme (Dmt1, projekti, strucni skupovi). Zato se ne sme cepati po prefiksu.
"""

# Organizaciona jedinica nauke. Sve sifre porodice B knjize se na nju.
SCIENCE_UNIT = "30"

# Odluka narucioca 25.09.2026.: poslovni i naucni blok su centri `2` i `3` — tako ih vode
# sifarnik (`posao.blok`), Finansije i Flota, i iz te oznake se prave brojevi putnih naloga
# (`2/2026-…`) i ogranicava pristup. Samo knjizenja ih vode kao jedinice `20` i `30`.
# Zatvorena lista: jedinica knjizenja → oznaka centra u registru. Ostale jedinice su iste.
OZNAKA_CENTRA_IZ_KNJIZENJA = {"20": "2", "30": "3"}


def oznaka_centra(jedinica_knjizenja):
    """Oznaka centra u registru za organizacionu jedinicu iz knjizenja."""
    jedinica = (jedinica_knjizenja or "").strip()
    return OZNAKA_CENTRA_IZ_KNJIZENJA.get(jedinica, jedinica)


def je_nauka(raw_code):
    """Da li je sifra iz naucnog sifarnika (porodica B): `3` + radnik + projekat."""
    return classify(raw_code, set()).family == FAMILY_SCIENCE


def sifra_radnika_nauke(raw_code):
    """Sifra radnika iz Kadrova u naucnoj sifri (`315400` → 154); None ako nije nauka."""
    code = normalize_code(raw_code)
    if not je_nauka(code) or not code[1:4].isdigit():
        return None
    return int(code[1:4])

FAMILY_BUSINESS = "A"
FAMILY_SCIENCE = "B"
FAMILY_EXCEPTION = "C"

REASON_SCIENCE = (
    "Naucna sifra: 3 + sifra radnika iz Kadrova + broj projekta. Deo je bloka 3 "
    "(odluka 25.09.2026.): projekat je jedinica drugog nivoa, sifra je ucesce radnika na njemu."
)

# Nosioci u naucnim siframa koji nisu radnici nego zbirne institutske teme (Dmt1, Naucno vece,
# projekti NPEE i tehnoloskog razvoja, strucni skupovi). Kod njih „broj projekta" (31, 32 …)
# nije zajednicki broj projekta, pa se grupisu po nosiocu, ne po projektu.
ZBIRNI_NOSIOCI_NAUKE = {"133", "233", "333"}
PREFIKS_PROJEKTA = "3-"
REASON_NOT_NUMERIC = "Sifra nije numericka, pa se segmenti ne mogu odrediti."
REASON_UNKNOWN_CENTER = "Prve dve cifre nisu poznata organizaciona jedinica."
REASON_BAD_LENGTH = "Sifra nema 6 cifara, pa ne odgovara obrascu centar + jedinica + posao."
REASON_NO_NAME = "Sifra nema naziv u izvoru."


class Classification:
    """Rezultat razvrstavanja jedne sifre."""

    __slots__ = ("family", "segments", "reason", "needs_review", "_unit_code")

    def __init__(self, family, segments=None, reason="", needs_review=False, unit_code=None):
        self.family = family
        self.segments = segments
        self.reason = reason
        self.needs_review = needs_review
        self._unit_code = unit_code

    @property
    def in_tree(self):
        """Sifra ulazi u stablo: poslovna (A) i naucna (B, deo bloka 3)."""
        return self.family in (FAMILY_BUSINESS, FAMILY_SCIENCE) and bool(self.segments)

    @property
    def unit_code(self):
        """Puna sifra jedinice drugog nivoa: `431` za poslovnu, `3154` (3 + radnik) za naucnu."""
        if self._unit_code:
            return self._unit_code
        return self.segments[0] + self.segments[1] if self.segments else None

    @property
    def center(self):
        return self.segments[0] if self.segments else None

    @property
    def unit(self):
        return self.segments[1] if self.segments else None

    @property
    def job(self):
        return self.segments[2] if self.segments else None

    def __repr__(self):
        return f"Classification({self.family!r}, {self.segments!r})"


def normalize_code(raw):
    """Uklanja rubne razmake. Sirova vrednost se cuva odvojeno, ovde se ne dira."""
    return (raw or "").strip()


def classify(raw_code, known_units, name=""):
    """Razvrstava jednu sifru.

    `known_units` je skup poznatih organizacionih jedinica prvog nivoa (npr. {"41", "43"}),
    procitanih iz knjizenja — ne iz `FinanceJob.center`, koji je nepouzdan.
    """
    code = normalize_code(raw_code)

    if not code.isdigit():
        # Cetiri naucne sifre zavrsavaju slovom (npr. 320519206A); i one su nauka.
        if code.startswith("3") and len(code) >= 6 and code[1:4].isdigit():
            return _science(code)
        return Classification(FAMILY_EXCEPTION, reason=REASON_NOT_NUMERIC, needs_review=True)

    prefix = code[:2]

    # Nauka se prepoznaje pre obrasca, jer bi inace 6-cifrene naucne sifre
    # (npr. 315400 = osoba) bile pogresno procitane kao centar 31.
    if _is_science(code):
        return _science(code)

    if len(code) != 6:
        return Classification(FAMILY_EXCEPTION, reason=REASON_BAD_LENGTH, needs_review=True)

    if prefix not in known_units:
        return Classification(FAMILY_EXCEPTION, reason=REASON_UNKNOWN_CENTER, needs_review=True)

    segments = (prefix, code[2], code[3:])
    if not (name or "").strip():
        # Struktura odgovara, ali sifra bez naziva se ne unosi tiho u stablo.
        return Classification(
            FAMILY_EXCEPTION, segments=segments, reason=REASON_NO_NAME, needs_review=True
        )
    return Classification(FAMILY_BUSINESS, segments=segments)


def _science(code):
    """Naucna sifra u bloku 3: `3` + radnik (3 cifre) + broj projekta (slobodan unos).

    Jedinica drugog nivoa je **projekat** (`3-702400` = TD 7024), a posao je sifra — ucesce
    jednog radnika na tom projektu; segment posla je sifra radnika. Koren `3` + radnik + `00`
    je projekat `00` (radnik bez projekta). Zbirni nosioci (133, 233, 333) grupisu se po nosiocu.
    """
    radnik, projekat = code[1:4], code[4:]
    if radnik in ZBIRNI_NOSIOCI_NAUKE:
        return Classification(FAMILY_SCIENCE, segments=(SCIENCE_UNIT, radnik, projekat),
                              reason=REASON_SCIENCE, unit_code=code[:4])
    return Classification(FAMILY_SCIENCE, segments=(SCIENCE_UNIT, projekat, radnik),
                          reason=REASON_SCIENCE, unit_code=PREFIKS_PROJEKTA + projekat)


def _is_science(code):
    """Sifra pocinje sa 3 i ima bar 6 znakova — osim sifara same jedinice 30.

    Jedina poznata jedinica prvog nivoa koja pocinje sa 3 jeste `30`, pa je izuzetak
    jednoznacan: `30XXXX` je posao jedinice 30 (npr. `300001`), sve ostalo sto pocinje
    sa 3 je nauka, gde su cifre posle `3` nosilac a ne centar.
    """
    if not code.startswith("3"):
        return False
    if code[:2] == SCIENCE_UNIT and len(code) == 6:
        return False
    return len(code) >= 6


def split_science(raw_code):
    """Deli naucnu sifru na nosioca i projekat; None ako oblik ne odgovara.

    Oblik je `3` + nosilac (3 znaka) + projekat (ostatak, moze biti prazan).
    Vraca `(nosilac, projekat)` gde je nosilac cetvoroznakovni prefiks.
    """
    code = normalize_code(raw_code)
    if len(code) < 6 or not code.startswith("3"):
        return None
    holder = code[:4]
    project = code[4:]
    return holder, project
