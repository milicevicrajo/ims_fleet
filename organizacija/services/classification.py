"""Razvrstavanje sifara posla u tri porodice.

Pravilo je izvedeno iz merenja nad produkcionom bazom 21.09.2026.
(`dokumentacija/popis-sifara-posla-korak-0.md`) i namerno je ovde, kao ciste funkcije
bez baze, da se moze proveriti testom.

Sta je mereno i zasto pravilo izgleda ovako:

* `FinanceJob.center` **nije pouzdan** — za centar `20` upisuje `2`, za `30` upisuje `3`,
  a kod dve sifre je prazan. Zato se centar cita iz **prve dve cifre same sifre**.
* Prefiks se koristi **samo pri prvom uvozu, kao predlog**. Knjizenja ga potvrdjuju:
  za 92 od 118 upotrebljenih sifara najcesca organizaciona jedinica knjizenja jednaka je
  prve dve cifre sifre. Svih 24 odstupanja su nauka.
* Nauka (porodica B) se knjizi iskljucivo na organizacionu jedinicu `30`, a cifre posle
  `3` u sifri su **nosilac (osoba)**, ne centar. Zato se ne sme cepati po prefiksu.
"""

# Organizaciona jedinica nauke. Sve sifre porodice B knjize se na nju.
SCIENCE_UNIT = "30"

FAMILY_BUSINESS = "A"
FAMILY_SCIENCE = "B"
FAMILY_EXCEPTION = "C"

REASON_SCIENCE = (
    "Nauka je zaseban sifarnik (odluka 21.09.2026.). Sifra vezuje osobu za projekat, "
    "pa ne staje u stablo: isti projekat javlja se kod vise osoba."
)
REASON_NOT_NUMERIC = "Sifra nije numericka, pa se segmenti ne mogu odrediti."
REASON_UNKNOWN_CENTER = "Prve dve cifre nisu poznata organizaciona jedinica."
REASON_BAD_LENGTH = "Sifra nema 6 cifara, pa ne odgovara obrascu centar + jedinica + posao."
REASON_NO_NAME = "Sifra nema naziv u izvoru."


class Classification:
    """Rezultat razvrstavanja jedne sifre."""

    __slots__ = ("family", "segments", "reason", "needs_review")

    def __init__(self, family, segments=None, reason="", needs_review=False):
        self.family = family
        self.segments = segments
        self.reason = reason
        self.needs_review = needs_review

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
        if code.startswith("3") and len(code) >= 6:
            return Classification(FAMILY_SCIENCE, reason=REASON_SCIENCE)
        return Classification(FAMILY_EXCEPTION, reason=REASON_NOT_NUMERIC, needs_review=True)

    prefix = code[:2]

    # Nauka se prepoznaje pre obrasca, jer bi inace 6-cifrene naucne sifre
    # (npr. 315400 = osoba) bile pogresno procitane kao centar 31.
    if _is_science(code):
        return Classification(FAMILY_SCIENCE, reason=REASON_SCIENCE)

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
