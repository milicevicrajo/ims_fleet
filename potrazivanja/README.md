# Potraživanja — samostalna evidencija i lokalni finansijski prikaz

Aplikacija je dostupna na `/potrazivanja/`, pored postojeće Naplate. Ekrani čitaju lokalne
Django tabele u IMS_ERP. Potraživanja samostalno vode kontakte, pozive, napomene, opomene,
pisma, oznake kupaca i pravne postupke. Naplata ostaje dostupna i nije menjana.
Novi operativni unosi se ne prenose između aplikacija: posle završnog prenosa korisnik
vodi evidenciju u odabranoj aplikaciji. Finansije čitaju potraživanja iz lokalnog objavljenog
snimka preko `services.reports.job_balances`, bez pozivanja starih upita Naplate.
SQL izvori sinhronizacije ostaju isti.

U gornjem meniju je Potraživanja; stara Naplata dostupna je kroz link „Stara Naplata
(legacy)” u bočnom meniju, prema starim dozvolama. `configure_permissions` dodaje
odgovarajuća prava Potraživanja svim ulogama sa pravima Naplate, čuva stara prava i
ograničeni obuhvat uloge `pregled-naplate`. Poziva se i iz standardnog usklađivanja prava.

## Pokretanje

```powershell
.venv\Scripts\python.exe manage.py migrate potrazivanja --settings=ims_erp.settings.development
.venv\Scripts\python.exe manage.py configure_potrazivanja --settings=ims_erp.settings.development
.venv\Scripts\python.exe manage.py initialize_potrazivanja --settings=ims_erp.settings.development
.venv\Scripts\python.exe manage.py sync_potrazivanja --settings=ims_erp.settings.development
.venv\Scripts\python.exe manage.py test potrazivanja finansije core naplata --settings=ims_erp.settings.testing --noinput
```

Dugme na `/potrazivanja/sinhronizacija/` direktno poziva `sync_collections`.
Ista funkcija registrovana je kroz `potrazivanja.tasks.sync_collections_task`, red `sync`.
Novi periodični raspored nije automatski uključen. Rad zadatka zahteva dostupan broker,
worker za red `sync` i Beat ako se kasnije uvede raspored. Postojeći raspored procedure
`sp_AzurirajNalogZ` u 10 i 11 nije menjan.

## Šta znači puna sinhronizacija

Svako pokretanje čita **sve redove ugovorenih izvora**, bez datuma poslednje izmene i bez
filtriranja samo otvorenih stavki. To nije kopija cele ERP baze niti svih godišta glavne
knjige: godišnji obuhvat finansijskih view-ova ostaje isti kao u Naplati.

Izvori: `partneri`, `baza`, `ispravke`, `v_tuzeni`, `v_if`, `v_duplikati`, `dodela_baketa`,
`v_neodobreneIF`, `tabela_if`, `duplikati18`, `sif_baket`, `sif_kategorija` i izvorni `posao`
za firmu 1. To je 13 izvora redovne finansijske sinhronizacije.

Samo jednokratna inicijalizacija dodatno čita `kontakti`, `napomene`, `opomene`,
`poziv_pismo`, `pozivi_tel`, `tuzbe`, `avans_klijent`, `postupak`, `promena_postupka`.
Nakon uspešnog prenosa postavlja se `CollectionState.operations_independent_at`.
Ponovna inicijalizacija je bez izmene podataka, a pokušaj `include_legacy=True` u redovnoj
funkciji se odbija. UI dozvoljava operativne upise tek nakon ovog završnog prenosa.

`SourceDataset` i `SourceRow` čuvaju kompletne izvorne kolone, NULL vrednosti, duplikate,
stare godine i izvorne identifikatore. Decimal i datumi se u JSON čuvaju kao tekst bez
gubitka preciznosti. SHA-256 skupa proverava sadržaj i broj ponavljanja, nezavisno od
redosleda redova. Jedino prolazni `danasnji_datum` ne utiče na identitet sadržaja; trenutak
preuzimanja čuva sam snimak. Isti sadržaj ponovo koristi postojeći nepromenljiv skup.
Promenjeni skup ostaje nova verzija, a prethodni se ne briše.

Prvobitnih 19 modela dopunjeno je sa dve arhivske tabele u migraciji `0003`, kontakt
kanalima, lokalnim postupcima/promenama i revizijskim zapisima u `0004`, odvajanjem stare
pravne veze u `0005`, te dnevnikom Excel uvoza u `0006` (26 modela ukupno).

## Objavljivanje i kontrole

- SQL aplikaciono zaključavanje sprečava preklapanje ručnog, komandnog i Celery pokretanja.
- `baza`, `ispravke` i `dodela_baketa` se ponovo pročitaju pre upisa; promena sadržaja ili
  datuma tokom preuzimanja prekida pokretanje. To nije distribuirana transakcija sa ERP-om:
  prikazuje se jasno označen snimak uspešno preuzetog stanja.
- Arhiva, partneri, knjiženja, dokumenti, operativni prenos i pokazivač aktivnog snimka upisuju
  se u jednoj lokalnoj transakciji. Greška vraća sve te izmene, a ostavlja zapis neuspeha.
- Sadržaj svakog novog arhivskog skupa se pročita iz baze i proveri hash i broj redova.
- Iz `baza` se nezavisno sabira D−P po partneru/referenci/poslu/porodici konta i poredi sa
  otvorenim pozicijama `dodela_baketa`. Nulte pozicije se ne prikazuju kao otvorene.
- Upisana knjiženja proveravaju se po ključevima, partneru, kontu, poslu, referenci,
  datumima i duguje/potražuje. Upisane pozicije proveravaju duguje, potražuje i saldo po ključu i po
  partneru/poslu/porodici konta/baketu i svi datumi dospeća.
- Duplirani ključevi ili razlike blokiraju objavu. Prethodni objavljeni snimak ostaje aktivan.
- Stari snimci pozicija se ne menjaju naknadno. Novi saldo nije upis preko stare istorije.

Ovo potvrđuje vernost prenosa postojećih obračuna. Nije nezavisna revizija ispravnosti
poslovnih pravila samih SQL view-ova.

## Poslovna pravila koja se čuvaju

Finansijski obuhvat je firma 1 / grupa partnera 1, kao u `baza` i `ispravke`.
Partner ima izvor/firma/grupa/šifra ključ. Finansijska referenca sa nestalim partnerom iz
šifarnika dobija označen neaktivan identitet, uz problem za proveru. Operativni red bez
potvrđenog partnera ostaje nepovezan; naziv nije dovoljan za automatsko povezivanje.
Registar `ugovori.Partner` i njegova APR polja se ne prepisuju.

`ReceivablePosting` koristi godinu/vrstu/nalog/stavku uz firmu i izvor. Promenjeni red se
osvežava; red van celog tekućeg view-a postaje neaktivan. To **nije dokaz da je obrisan u
ERP-u**: može izaći zbog promene godišnjeg obuhvata. Prethodna puna arhiva ostaje sačuvana.

Fakture `IF` se grupišu po godini/nalogu/partneru/referenci iz `baza`, na kontima potraživanja.
Iznos je zbir D−P na tim kontima. `v_if.saldo`, koji obuhvata drugačije stavke, ne koristi se
kao ukupan iznos fakture. Automatsko povezivanje uplate sa fakturom samo po `vez_dok` nije
uvedeno. Saldo nije isto što i iznos naplaćen po konkretnoj fakturi.

Dospeća za otvorene stavke preuzimaju se iz postojeće `dodela_baketa`, sa pravilima
`v_if` / `v_duplikati` i istorijskim tabelama. Te tabele su potpuno arhivirane. Prvobitni
`DueDateEvidence` model se u ovoj fazi ne puni nezavisnim preračunavanjem istorije; poreklo
pozicije pokazuje na view i snimak svih njegovih izvora.

Baketi: ≤0 dana → 0,1; 1–30 → 30; 31–45 → 45; 46–60 → 60; 61–90 → 90; 91–180 → 180;
preko 180 → 181. **Nepoznato dospeće ostaje u baketu 0,1 radi identičnosti stare tabele**,
a u zbirnim karticama je posebno izdvojeno. Baketi su zamrznuti na datum snimka, ne stare
samostalno dok se podaci ne sinhronizuju.

Ispravke nakon prelaznog roka ostaju iz prethodne godine, prema potvrđenom poslovnom
pravilu. Postojeća SQL granica `DATEADD(DAY,119,...)` zadržana je bez promene; njen rubni
slučaj prestupne godine i tačan čas 30.04. nisu prećutno menjani.

`v_neodobreneIF` se potpuno snima. Nestanak iz filtriranog view-a ne tumači se kao status
Approved. UI prikazuje samo ono što izvor sadrži na datum snimka. `ElectronicInvoiceStatus`
se još ne puni direktno iz EDok: praćenje kompletnog životnog ciklusa svih SEF ID-jeva ostaje
odvojeni naredni korak, a istorija zatečenih neodobrenih redova je sačuvana u arhivi.

## Kontakti, napomene, opomene i pravna evidencija

Svaki stari kontakt, napomena, telefonski poziv, opomena, pozivno pismo i red `tuzbe` ima
stabilnu `LegacyImportMap` vezu sa novim zapisom. Ponovljeni prenos ne duplira zapise.
Izvorni tekst faktura u opomeni se čuva celovit; ne izmišljaju se stavke razdvajanjem teksta.
Stare tužbe imaju tip `legacy_claim`; iz njih se ne kreiraju novi pravni postupci.

Tokom početnog prenosa, ako je novi zapis lokalno promenjen posle prethodnog prenosa, import ga ne prepisuje:
beleži konflikt i čuva novu izvornu verziju u arhivi. Nestali stari zapisi se arhiviraju,
ne brišu. Ponovno pojavljivanje može ih ponovo aktivirati ako nema lokalnog konflikta.

`veliki=da` je svojstvo važnog kupca. `avans_klijent` je spisak za proveru, ne obračun avansa.
Profili čuvaju ove oznake i originalnu napomenu za proveru. Potraživanja imaju sopstvene
`CollectionLegalCase` i `CollectionLegalEvent` sa svim poljima, izvornim ID-jem i originalom.
`LegalCaseLink.legacy_case_id` je istorijska oznaka; nema FK veze ka Naplati.
Stari postupci i promene ostaju netaknuti u svojim tabelama.

Kontakti imaju ime, prezime, funkciju/odeljenje i napomenu. `ContactPoint` je jedan telefon,
mobilni broj ili mejl. Automatsko razdvajanje čuva original i pravi osobe samo za pouzdane
parove imena i broja. Mejlovima se ne nagađa vlasnik. Nejasni zapisi dobijaju oznaku za
sređivanje, odvojenu od kupčevog statusa „Za proveru”.

Unosi i izmene imaju autora i vreme, optimističku proveru verzije i `CollectionAudit`
sa prethodnom/novom vrednošću. Brisanje u korisničkom interfejsu je arhiviranje sa mogućnošću
vraćanja. Izmena stavki kontakta/opomene čuva prethodne vrednosti kroz audit.
Opomena/pismo ima primaoca, tekst, rok i strukturirane reference sa iznosima; zbir se
proverava pre čuvanja. Štampa ne šalje dokument. Excel uvoz opomena ima pregled pre upisa,
odbija ceo neispravan skup i ne duplira ponovno učitavanje identičnog fajla.

## Pristup i prikaz

Dozvole su u `potrazivanja:*`; konfiguracija kopira odgovarajuća postojeća prava Naplate
bez menjanja tih prava. Provera pristupa pri radu ne zavisi od Naplate. Uprava/superuser mogu pokrenuti
sinhronizaciju; korisnici ograničenog pregleda dobijaju samo dodeljene centre/šifre posla.
Obuhvat se proverava na serveru i za direktne AJAX zahteve i za detalj partnera. Operativna
partnerova evidencija i view-ovi bez raspodele po poslu dostupni su samo potpunom pristupu.

Centri se uzimaju iz izvornog `posao.blok` po tačnoj šifri posla. Ne parsira se prefiks
šifre. Nedostajuća veza ostaje „Neraspoređeno”; sve sirove šifre ostaju sačuvane.

Tabele koriste AJAX, podrazumevano 100 redova, sortiranje po brojčanoj/ISO vrednosti i
pet nijansi crvene za potraživanja: nedospelo/bez datuma, 1–45, 46–90, 91–180 i preko
180 dana. Nule su neutralne; znak iznosa ostaje očuvan. Dospeli zbir koristi četvrtu,
ukupan saldo i ostali iznosi treću nijansu (zbir nije pojedinačni starosni razred).
Finansije koriste istu paletu u tabu Potraživanja. Detalj partnera ima tabove u kartici; svi počinju učitavanje pri
otvaranju stranice. Izvori se ne čitaju preko povezanog servera pri otvaranju ekrana.

## Granice ove faze

Nema menjanja starih SQL view-ova, automatskog zaključivanja naplate pojedinačne fakture,
automatskog razrešavanja nepovezanih partnera.
Procedura `sp_AzurirajNalogZ` nije preduslov ovog importa: sinhronizacija čita postojeće
view-ove koji sada imaju udaljene izvore. Prebacivanje samog izvora svih view-ova na lokalni
`nalog_z` zahteva zasebnu proveru prethodne godine, brisanja i potpunosti istorije.

Plan: [Nova Naplata](../dokumentacija/naplata-nova-aplikacija-plan.md).
Rezultat stvarnog prenosa: [Kontrola paralelnog rada](../dokumentacija/potrazivanja-paralelni-prenos-2026-09-18.md).
Samostalan rad: [Završni prenos i provere](../dokumentacija/potrazivanja-samostalan-rad.md).
