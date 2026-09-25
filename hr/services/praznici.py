"""Neradni praznici u Republici Srbiji i datum krsne slave zaposlenog.

Izvor: Zakon o državnim i drugim praznicima u Republici Srbiji. Neradni su za sve:
Nova godina (1. i 2. januar), Sretenje — Dan državnosti (15. i 16. februar), Praznik rada
(1. i 2. maj), Dan primirja u Prvom svetskom ratu (11. novembar), prvi dan Božića (7. januar)
i vaskršnji praznici od Velikog petka do drugog dana Vaskrsa, po pravoslavnom kalendaru.
Kada državni praznik padne u nedelju, ne radi se prvi naredni radni dan.

Verski praznici drugih zajednica (katolički Božić, Bajram, Jom Kipur…) neradni su samo za
vernike te zajednice, pa ih radna lista ne predlaže sama; unose se ručno.
"""
import re
import unicodedata
from datetime import date, timedelta

# Državni praznici (datumi sa pravilom o prenosu sa nedelje na naredni radni dan).
DRZAVNI = [
    ((1, 1), 'Nova godina'), ((1, 2), 'Nova godina'),
    ((2, 15), 'Sretenje — Dan državnosti'), ((2, 16), 'Sretenje — Dan državnosti'),
    ((5, 1), 'Praznik rada'), ((5, 2), 'Praznik rada'),
    ((11, 11), 'Dan primirja u Prvom svetskom ratu'),
]


def pravoslavni_vaskrs(godina):
    """Pravoslavni Vaskrs po gregorijanskom kalendaru (Meeus, julijanski računar + 13 dana, za 1900–2099)."""
    a, b, c = godina % 4, godina % 7, godina % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    mesec, dan = divmod(d + e + 114, 31)
    return date(godina, mesec, dan + 1) + timedelta(days=13)


def neradni_praznici(godina):
    """{datum: naziv} svih neradnih praznika u godini, uključujući dane prenete sa nedelje."""
    praznici = {date(godina, mesec, dan): naziv for (mesec, dan), naziv in DRZAVNI}
    praznici[date(godina, 1, 7)] = 'Božić'
    vaskrs = pravoslavni_vaskrs(godina)
    for pomak, naziv in ((-2, 'Veliki petak'), (-1, 'Velika subota'), (0, 'Vaskrs'), (1, 'Vaskrsni ponedeljak')):
        praznici[vaskrs + timedelta(days=pomak)] = naziv
    for (mesec, dan), naziv in DRZAVNI:
        dan_praznika = date(godina, mesec, dan)
        if dan_praznika.weekday() != 6:
            continue
        naredni = dan_praznika + timedelta(days=1)
        while naredni.weekday() >= 5 or naredni in praznici:
            naredni += timedelta(days=1)
        praznici[naredni] = f'{naziv} (prenet sa nedelje)'
    return dict(sorted(praznici.items()))


# Slave sa stalnim datumom (po gregorijanskom kalendaru). Ključ je naziv bez „sveti“, razmaka,
# tačaka i kvačica, a đ/dj/izgubljeno slovo „?“ se svode na „d“, jer su nazivi u HR-u neujednačeni.
SLAVE = {
    'nikola': (19, 12), 'nikoljdan': (19, 12),
    'nikolaletnji': (22, 5),
    'jovan': (20, 1), 'jovanjdan': (20, 1),
    'ivanjdan': (7, 7), 'rodjenjejovana': (7, 7),
    'zacecejovana': (6, 10), 'zacecejovanakrs': (6, 10), 'zacecejovanakrstitelja': (6, 10),
    'luka': (31, 10), 'lukinden': (31, 10),
    'mitrovdan': (8, 11), 'dimitrije': (8, 11),
    'durdevdan': (6, 5), 'dorde': (6, 5), 'georgije': (6, 5),
    'durdic': (16, 11),
    'arandelovdan': (21, 11), 'arhangelmihailo': (21, 11), 'mihailo': (21, 11),
    'petka': (27, 10), 'paraskeva': (27, 10),
    'andrejprvozvani': (13, 12), 'andrija': (13, 12), 'andrej': (13, 12),
    'blagovesti': (7, 4),
    'aleksandarnevski': (12, 9),
    'alimpije': (9, 12), 'alimpijestolpnik': (9, 12),
    'stefan': (9, 1), 'stevanjdan': (9, 1),
    'toma': (19, 10), 'tomindan': (19, 10),
    'trifun': (14, 2),
    'vasilijeostroski': (12, 5),
    'vasilije': (14, 1), 'vasilijeveliki': (14, 1),
    'kozmaidamjan': (14, 11), 'vraci': (14, 11),
    'mrata': (24, 11),
    'sava': (27, 1), 'savindan': (27, 1),
    'ilija': (2, 8), 'ilindan': (2, 8),
    'pantelejmon': (9, 8), 'pantelija': (9, 8),
    'petrovdan': (12, 7), 'petaripavle': (12, 7),
    'velikagospojina': (28, 8), 'malagospojina': (21, 9),
    'ignjatije': (2, 1),
    'kirikijulita': (28, 7),
    'prokopije': (21, 7),
    'mladenci': (22, 3),
    'spiridon': (25, 12),
}
# Pokretne slave (Spasovdan, Trojice, Lazareva subota) i one čiji naziv ne određuje jedan
# datum (Sv. Grigorije, Sv. Kliment) nisu ovde: za njih se datum upisuje ručno kod zaposlenog.


def kljuc_slave(naziv):
    tekst = str(naziv or '').casefold().replace('đ', 'dj')
    tekst = ''.join(znak for znak in unicodedata.normalize('NFD', tekst) if unicodedata.category(znak) != 'Mn')
    tekst = re.sub(r'\b(sv|sveti|sveta|svetog|svetoga|sv\.)\b', ' ', tekst.replace('.', ' '))
    tekst = tekst.replace('?', 'd').replace('dj', 'd')
    return re.sub(r'[^a-z]', '', tekst)


def predlog_datuma_slave(naziv):
    """(dan, mesec) za poznatu slavu sa stalnim datumom, inače None."""
    return SLAVE.get(kljuc_slave(naziv)) if naziv else None


def datum_slave(employee, godina):
    """(datum, iz_naziva) — upisan datum ima prednost; bez njega se datum predlaže iz naziva slave.

    Od upisanog datuma koriste se samo dan i mesec, jer se slava slavi svake godine istog dana.
    """
    upisan = getattr(employee, 'slava_datum', None)
    dan, mesec, iz_naziva = (upisan.day, upisan.month, False) if upisan else (None, None, False)
    if not (dan and mesec):
        predlog = predlog_datuma_slave(employee.slava)
        if not predlog:
            return None, False
        (dan, mesec), iz_naziva = predlog, True
    try:
        return date(godina, mesec, dan), iz_naziva
    except ValueError:        # 29. februar u neprestupnoj godini
        return None, iz_naziva
