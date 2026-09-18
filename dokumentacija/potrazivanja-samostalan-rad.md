# Potraživanja — samostalan rad, 18.09.2026.

Potraživanja su aktivna pored Naplate. Stara aplikacija, njene tabele, unosi i procedure
nisu menjani. Potraživanja imaju sopstvene operativne podatke: novi unos u jednoj aplikaciji
ne pojavljuje se automatski u drugoj.

## Navigacija, prava i Finansije

Potraživanja su u glavnom meniju. Stara Naplata je dostupna preko linka „Stara Naplata
(legacy)” u bočnom meniju Potraživanja, uz proveru njenih postojećih prava.
Proverene su uloge `uprava`, `pravna` i `pregled-naplate`: sve imaju pristup novoj
aplikaciji, a stara prava su ostala očuvana. Ograničena uloga nema pravo `view_all`.
Prenos prava je ponovljiv i deo redovnog usklađivanja dozvola.

Tab Potraživanja u detalju šifre posla u Finansijama koristi samo lokalne tabele
`CollectionState`, `BalanceSnapshot`, `ReceivablePosition` i identitet partnera.
Poštuje prava obe aplikacije i obuhvat centara/poslova. Starosni razredi računaju se
na datum snimka, a ne na datum otvaranja stranice. Uz tabelu su datum stanja i vreme
preuzimanja. Izbor meseca ne menja ovaj presek; partner vodi na isti snimak u
Potraživanjima. Bez objavljenog snimka prikazuje se obaveštenje da podaci nisu dostupni.

Kontrola povezivanja od 18.09.2026: poređenje svih 26 šifara sa stavkama, odnosno 642
grupisana reda partnera/porodice konta, daje iste razrede i ukupan saldo
450.941.954,80 RSD u adapteru Finansija i izveštaju Potraživanja. Tokom kontrole nije
izvršen nijedan upit preko `server_db`. Prošlo je 213 testova modula Potraživanja,
Finansije, core i Naplata. U pregledaču su provereni uklanjanje stare stavke iz
zaglavlja, legacy link, datum snimka i prelazak iz Finansija na partnera u Potraživanjima.

## Završni prenos

Primenjene su migracije `0004`–`0006`. Završni prenos je sinhronizacija #6:

| Evidencija | Preneto / formirano |
|---|---:|
| Originalni kontakti | 654 |
| Izdvojene osobe | 400 |
| Telefoni i adrese u zasebnim redovima | 2.512 |
| Originalni kontakti označeni za proveru | 490 |
| Napomene | 103 |
| Telefonski pozivi | 2.479 |
| Opomene | 895 |
| Pozivna pisma | 133 |
| Stara evidencija tužbi | 32 |
| Pravni postupci | 127 |
| Promene pravnih postupaka | 379 |

Originalni kontakt tekst ostaje dostupan u obrascu pod „Originalni podaci prenosa”.
Provera kontakta znači da treba potvrditi razdvajanje osobe/broja ili vezu sa partnerom;
ne znači da je izvorni podatak izgubljen. Neizvesne veze se ne povezuju nagađanjem.
Početno razdvajanje označilo je 480 zapisa; naknadna kontrola neprepoznatog teksta u
polju mejla označila je još 10. Izvorni sadržaj je sačuvan u svih 654 originalnih zapisa.

Finansijske kontrole: 12.445 knjiženja, 1.586 otvorenih pozicija, 468 partnera sa saldom.
Saldo je **450.941.954,80 RSD**. Razlike knjiženja/pozicija, partnera/poslova/baketa,
duguje/potražuje i datuma dospeća: **0**. Stanje i godišnji obuhvat pišu u hero zaglavlju.

## Rad korisnika

Levi meni prati postojeću Naplatu: Lista dugovanja, Spisak za proveru, Utuženi klijenti,
Opomene, Izveštaj po šiframa posla, Neodobrene IF i NBS linkovi. Administratori imaju
Sinhronizaciju i kontrole. Kontakti, napomene/pozivi i pisma dostupni su kroz detalj partnera.

Klik na partnera otvara zasebne tabove za kontakte, telefonske pozive, napomene, opomene,
pisma, evidenciju tužbi i pravne postupke, uz finansijske tabove. Svaki ima svoje dugme
za unos i prikazuje samo pripadajuće zapise. Izgled kartica prati detalj šifre posla;
sve tabele se učitavaju odmah u pozadini. „Svi partneri” omogućava unos i kupcu
bez trenutnog duga. „Za proveru” je prekidač u listi; oznaka važnog kupca uređuje se sa detalja.
Broj redova je podrazumevano 100. Sortiranje novca koristi broj, a datuma ISO vrednost.

Jedan kontakt predstavlja osobu ili opšte odeljenje, uz više zasebnih telefona i adresa.
Poziv ima datum/vreme, kontakt, belešku, ishod i datum sledećeg kontakta.
Opomena i pismo imaju tekst, primaoca, rok i stavke dokumenta; dostupna je štampa / PDF iz
pregledača. Slanje mejla nije automatsko. Pravni postupci imaju sopstvene promene i arhivu.
Unosi mogu da se izmene, arhiviraju i vrate; istorija izmena ostaje u `CollectionAudit`.

Excel izvoz poštuje isti obuhvat i filtere kao lista; tekst iz izvora nije Excel formula.
Excel uvoz opomena koristi obavezne kolone `sif_par`, `datum`, `iznos`, uz opcione
`naz_par`, `god`, `br_opomene`, `fakture`, `napomene`. Valuta uvoza je RSD. Pre upisa se
prikazuje pregled; greška u bilo kom redu sprečava ceo upis. Isti fajl se ne uvozi dvaput.

## Sinhronizacija i brzina

Redovna funkcija `sync_collections()` i njen Celery zadatak preuzimaju 13 finansijskih
izvora. Više ne čitaju 9 starih operativnih izvora niti prepisuju lokalne operativne unose.
Komanda `initialize_potrazivanja` završava početni prenos samo jednom. Uključivanje
`include_legacy=True` posle prelaska na samostalan rad se odbija.

Provereno je i pokretanje #7 nakon inicijalizacije: 43,73 sekunde, isti finansijski saldo,
svih 13 finansijskih izvora i nepromenjen hash kompletnog sadržaja svih sedam operativnih
tabela (kontakti, kontakt kanali, aktivnosti, opomene, profili, postupci i promene).

Ekrani čitaju samo lokalne tabele Potraživanja. Izvorni view-i se čitaju tokom
sinhronizacije. Nije promenjena logika njihove prethodne godine ili poreklo podataka.

Uklonjeno je nepotrebno čitanje celog šifarnika od 12.906 partnera u svakom tabu detalja.
Na istom uzorku izmerena je priprema podataka oko 13–31 ms po tabu, umesto oko 800 ms.
Ovo je vreme serverske obrade bez mreže i prikaza u pregledaču; nije garantovano vreme za
svakog partnera. Regresioni testovi proveravaju da nema čitanja izvornog servera, učitavanja
nepovezanih partnera ili po jednog dodatnog upita za svaki red.

Postojeći raspored procedure `sp_AzurirajNalogZ` u 10 i 11 ostaje neizmenjen. Novo
periodično pokretanje sinhronizacije Potraživanja nije automatski uključeno.

Istorijska migracija `0001` još ima zavisnost od migracije Naplate zbog tadašnje pravne
veze; `0005` uklanja samu vezu iz aktivne šeme. To ne utiče na samostalan rad, ali potpuno
uklanjanje stare aplikacije iz Django projekta kasnije zahteva sređivanje istorije migracija.
