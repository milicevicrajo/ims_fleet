"""Novosti po modulu (od 07.10.2026.): obaveštenje koje korisnik vidi kad uđe u modul, dok ne klikne „Razumem”.

Svaka novost ima stalan ključ; potvrda se čuva po korisniku (`ProcitanaNovost`) i posle nje se ista novost
više ne prikazuje. Nova izdanja dodaju se na početak spiska `NOVOSTI` sa novim ključem.
Moduli su ključevi menija (`core.context_processors.current_app`): fleet, kadrovi, finansije, nabavka,
pravna, potrazivanja, isplate.
"""
from django.urls import Resolver404, resolve

NAZIVI_MODULA = {
    "fleet": "Flota", "kadrovi": "Kadrovi", "finansije": "Finansije", "nabavka": "Nabavka",
    "pravna": "Pravna služba", "potrazivanja": "Potraživanja", "isplate": "Isplate",
}

# Izdanje 07.10.2026. — poslednja četiri commita (b8f8526, 44bebb0, 6182871, aff1a08).
NOVOSTI = [
    {"kljuc": "2026-10-07-fleet", "modul": "fleet", "datum": "07.10.2026.", "stavke": [
        ("Registracija iz polise", "„Registracija važi do” se više ne unosi ručno — računa se iz polise autoodgovornosti "
                                   "(detalj vozila, saobraćajne dozvole, izveštaji)."),
        ("Kontrola faktura goriva", "Novi izveštaj: faktura sa SEF-a ↔ transakcije ↔ knjiženje po šiframa posla, sa "
                                    "upozorenjima kad se iznosi ne slažu; izvoz u Excel i PDF."),
        ("Gorivo po šiframa posla", "Red UKUPNO za knjiženje, izbor fakture, a podrazumevani period je poslednji fakturisani; "
                                    "filter pokazuje izabranu godinu, mesec i polovinu."),
        ("OMV uvoz", "Dve stavke istog računa (npr. dva AdBlue kanistera) se više ne gube; transakcije za vozilo koje "
                     "još nije u Floti se čuvaju i kasnije same povežu."),
        ("Izvoz", "Svi izveštaji imaju Excel i PDF; klik samo preuzima fajl, stranica ostaje."),
    ]},
    {"kljuc": "2026-10-07-kadrovi", "modul": "kadrovi", "datum": "07.10.2026.", "stavke": [
        ("Jedna osoba — jedan red", "Spisak zaposlenih prikazuje osobu jednom (po JMBG-u); na detalju su sve njene šifre "
                                    "(radni odnos i van radnog odnosa), svi ugovori, ukupan radni staž i staž u IMS."),
        ("Više radnih mesta", "Zaposleni može biti raspoređen na do pet radnih mesta — sva se vide, numerisana, "
                              "na detalju, u spisku i u Mom pregledu."),
        ("Radna lista — predaja", "Lista se ne može predati ako red sa satima rada nema šifru posla. Topli obrok je "
                                  "obavezan (i 0 je odgovor); predlog je broj radnih dana sa kucanjem."),
        ("Radna lista — štampa i prilozi", "Datum na listi je prvi radni dan meseca predaje. Nova kartica „Prilozi radne liste” "
                                           "za skenirane propusnice i potpisanu listu."),
        ("Rešenja", "Novo polje „Broj zahteva iz arhive”."),
        ("Rodna ravnopravnost", "Na Analitici dugme „Statistika rodne ravnopravnosti” — podaci za Obrazac 1 za izabranu "
                                "godinu, sa izvozom u Excel i PDF."),
    ]},
    {"kljuc": "2026-10-07-finansije", "modul": "finansije", "datum": "07.10.2026.", "stavke": [
        ("SEF — pridruženi dokumenti", "Uz fakturu se preuzimaju i prilozi (izveštaji, specifikacije, otpremnice…). "
                                       "Vide se na detalju fakture i ulaze u ZIP izvoz."),
    ]},
    {"kljuc": "2026-10-07-nabavka", "modul": "nabavka", "datum": "07.10.2026.", "stavke": [
        ("Fiskalni računi bez šifre posla", "Račun se može učitati i bez šifre posla; šifra se dopunjuje u obradi."),
        ("Oštećen QR kod", "Dugme „QR kod je oštećen?” otvara stranicu Poreske uprave sa strane, pa se QR očita sa nje."),
        ("SEF prilozi", "Na EUF fakturi i u UF SEF vide se i pridruženi dokumenti sa SEF-a."),
        ("EUF detalj", "PDF sa SEF-a prati širinu leve kartice."),
    ]},
    {"kljuc": "2026-10-07-pravna", "modul": "pravna", "datum": "07.10.2026.", "stavke": [
        ("Novčana kazna", "Pri zatvaranju disciplinskog postupka novčanom kaznom unose se procenat osnovne zarade "
                          "(do 20%) i trajanje (1–3 meseca); vide se na detalju i u izveštaju."),
        ("Analitika zaposlenih", "U meniju Pravne službe su Analitika zaposlenih i Statistika rodne ravnopravnosti."),
    ]},
    {"kljuc": "2026-10-07-potrazivanja", "modul": "potrazivanja", "datum": "07.10.2026.", "stavke": [
        ("Brisanje opomene", "Pogrešno uneta opomena se može obrisati (zapisuje se u dnevnik izmena)."),
        ("Broj opomene", "Broj opomene je jedinstven po vrsti i godini; raniji duplikati su dobili nastavak -1, -2."),
    ]},
    {"kljuc": "2026-10-07-isplate", "modul": "isplate", "datum": "07.10.2026.", "stavke": [
        ("Fiskalni računi bez šifre posla", "U Ostalim fiskalnim računima račun se može učitati i bez šifre posla."),
    ]},
]

# Imenski prostor URL-a → modul; rute bez imenskog prostora pripadaju Floti (osim Kadrova i Administracije).
MODUL_PO_PROSTORU = {"hr": "kadrovi", "finansije": "finansije", "nabavka": "nabavka", "pravna": "pravna",
                     "ugovori": "pravna", "potrazivanja": "potrazivanja", "isplate": "isplate"}
BEZ_NOVOSTI = {"pocetna", "switch_app", "login", "logout", "required_password_change", "novosti_procitano"}


def modul_zahteva(request):
    """Modul u kome je korisnik, ili None (početna strana, prijava, administracija…)."""
    match = getattr(request, "resolver_match", None)
    if match is None:
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return None
    if match.url_name in BEZ_NOVOSTI:
        return None
    if match.namespace:
        return MODUL_PO_PROSTORU.get(match.namespace.split(":")[0])
    meni = request.session.get("current_app", "fleet") if hasattr(request, "session") else "fleet"
    if meni == "kadrovi" and (match.url_name or "").startswith(("employee", "my_employee")):
        return "kadrovi"
    return "fleet" if meni in ("fleet", "kadrovi") else None


def neprocitane(request):
    """Novosti modula koje korisnik još nije potvrdio."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or getattr(user, "must_change_password", False):
        return []
    modul = modul_zahteva(request)
    if not modul:
        return []
    kandidati = [n for n in NOVOSTI if n["modul"] == modul]
    if not kandidati:
        return []
    from core.models import ProcitanaNovost

    procitane = set(ProcitanaNovost.objects.filter(user=user, kljuc__in=[n["kljuc"] for n in kandidati])
                    .values_list("kljuc", flat=True))
    return [dict(n, naziv_modula=NAZIVI_MODULA.get(modul, modul)) for n in kandidati if n["kljuc"] not in procitane]
