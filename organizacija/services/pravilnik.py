"""Nazivi organizacionih delova prema Pravilniku o organizaciji Instituta IMS.

Izvor: *Pravilnik o organizaciji Instituta za ispitivanje materijala akcionarskog drustva*,
precisceni tekst sa izmenama od 18.04.2024. (`organizacija/2. Pravilnik o organizaciji
18.04.2024 (1).pdf`). Tekst je na cirilici; nazivi su ovde preneti **latinicom**.

Numeracija sifara prati numeraciju pravilnika: deo 3 je naucno-istrazivacki blok (`3`),
4.1–4.4 su centri `41`–`44`, 5 je `50`, 6 je `60`, 7 je `70`, 8.1–8.3 su `81`–`83`, 11 je `11`.
Treca cifra sifre je broj jedinice u pravilniku (4.1.1 → `411`, 8.3.2 → `832`).

U registar se upisuju **samo** nazivi gde se poklapaju i broj i sadrzaj poslova jedinice.
Gde se broj i sadrzaj razilaze, naziv je samo predlog za proveru (`PROVERITI`).
"""

IZVOR = "Pravilnik o organizaciji, 18.04.2024."

# Clan 3: dvanaest osnovnih delova Instituta.
DELOVI = {
    1: "Upravni blok",
    2: "Izvršni blok",
    3: "Naučno-istraživački blok",
    4: "Poslovno-razvojni blok",
    5: "Kontrolno telo",
    6: "Služba za integrisane sisteme menadžmenta",
    7: "Sertifikaciono telo",
    8: "Zajedničke službe",
    9: "Provajder za ispitivanje osposobljenosti",
    10: "Sertifikaciono telo za osobe",
    11: "Telo za tehničko ocenjivanje",
    12: "Telo za verifikaciju",
}

# Centar (oznaka u registru) → (deo pravilnika, naziv, clan). Centar `2` sifarnik zove
# „Poslovni blok"; po sadrzaju poslova (zastupanje, Upravni odbor, organizacija i poslovanje)
# odgovara upravnom i izvrsnom bloku — naziv se zato ne menja dok se ne potvrdi.
CENTRI = {
    "2": (None, "Poslovni blok", "šifarnik"),
    "3": (3, "Naučno-istraživački blok", "čl. 14"),
    "11": (11, "Telo za tehničko ocenjivanje", "čl. 41"),
    "41": (4, "Centar za materijale", "čl. 21"),
    "42": (4, "Centar za metale i energetiku", "čl. 22"),
    "43": (4, "Centar za puteve i geotehniku", "čl. 23"),
    "44": (4, "Centar za konstrukcije i prednaprezanje", "čl. 24"),
    "50": (5, "Kontrolno telo", "čl. 25"),
    "60": (6, "Služba za integrisane sisteme menadžmenta", "čl. 27"),
    "70": (7, "Sertifikaciono telo", "čl. 29"),
    "81": (8, "Finansijska služba", "čl. 34"),
    "82": (8, "Služba za opšte i tehničke poslove — opšti poslovi", "čl. 35"),
    "83": (8, "Služba za opšte i tehničke poslove — tehnički poslovi", "čl. 35"),
}

# Jedinica → (oznaka u pravilniku, naziv). Samo gde se poklapaju broj i sadrzaj poslova.
JEDINICE = {
    "411": ("4.1.1", "Laboratorija za kamen i agregat"),
    "412": ("4.1.2", "Laboratorija za građevinsku keramiku"),
    "413": ("4.1.3", "Laboratorija za beton"),
    "414": ("4.1.4", "Laboratorija za veziva, hemiju i maltere"),
    "416": ("4.1.6", "Laboratorija za drvo i sintetičke materijale"),
    "417": ("4.1.7", "Laboratorija za hidroizolaciju i antikorozivnu zaštitu"),
    "421": ("4.2.1", "Odeljenje za kontrolu opreme i mehaničko-tehnološka ispitivanja metala"),
    "431": ("4.3.1", "Odeljenje za geotehniku i nadzor"),
    "433": ("4.3.3", "Laboratorija za puteve i geotehniku"),
    "441": ("4.4.1", "Odeljenje za prednaprezanje"),
    "442": ("4.4.2", "Odeljenje za projektovanje, nadzor i sanacije"),
    "443": ("4.4.3", "Laboratorija za ispitivanje konstrukcija"),
    "812": ("8.1.2", "Knjigovodstvo"),
    "821": ("8.2.1", "Pravni i kadrovski poslovi"),
    "822": ("8.2.2", "Ekonomski poslovi"),
    "823": ("8.2.3", "Informatika"),
    "824": ("8.2.4", "Marketing"),
    "825": ("8.2.5", "Opšti poslovi"),
    "831": ("8.3.1", "Radionica"),
    "832": ("8.3.2", "Garaža"),
    "833": ("8.3.3", "Tehničko održavanje i kotlarnica"),
}

# Jedinice gde se broj i sadrzaj razilaze ili pravilnik jedinicu ne navodi: predlog + razlog.
PROVERITI = {
    "415": ("Laboratorija za toplotnu tehniku i zaštitu od požara",
            "Broj odgovara 4.1.5, ali jedinica drži i akustiku i vibracije (4.1.8)."),
    "418": ("Odeljenje za zaštitu životne sredine",
            "Sadržaj je zaštita životne sredine; broj 4.1.8 je u pravilniku akustika i vibracije."),
    "422": ("Metrološka laboratorija za mehaničke veličine",
            "Sadržaj je etaloniranje (4.2.3); broj 4.2.2 je Laboratorija za ispitivanje metala."),
    "425": ("Kontrolisanje", "Pravilnik nema 4.2.5; poslovi su kontrolisanje i superkontrola."),
    "426": ("Sertifikacija osoblja za zavarivanje", "Pravilnik nema 4.2.6; sadržaj liči na Sertifikaciono telo za osobe (deo 10)."),
    "432": ("Odeljenje za projektovanje saobraćajnica",
            "Broj odgovara 4.3.2, ali su poslovi terenske laboratorije i sanacija klizišta (svi neaktivni)."),
    "434": ("Projektovanje i baza podataka o saobraćaju", "Pravilnik nema 4.3.4; sadržaj liči na 4.3.2."),
    "437": ("Laboratorije za geomehaniku, asfalt i saobraćajnu signalizaciju",
            "Pravilnik nema 4.3.7; poslovi odgovaraju laboratorijama 4.3.3.1–4.3.3.3."),
    "439": ("Projektovanje saobraćajnica", "Pravilnik nema 4.3.9; sadržaj odgovara 4.3.2."),
    "811": ("Komercijala i magacin", "Sadržaj je nabavka, magacin i devizni poslovi (8.1.3 i 8.1.5); broj 8.1.1 je računovodstvo."),
    "813": ("Računovodstvo i blagajna", "Sadržaj je obračun, platni promet i blagajna (8.1.1 i 8.1.4); broj 8.1.3 je komercijala."),
}


def naziv_centra(oznaka):
    podatak = CENTRI.get(oznaka)
    return podatak[1] if podatak else ""


def deo_centra(oznaka):
    podatak = CENTRI.get(oznaka)
    return podatak[0] if podatak else None


def naziv_jedinice(oznaka):
    podatak = JEDINICE.get(oznaka)
    return podatak[1] if podatak else ""
