# Finansijska analitika

**Kompletna metodologija svih prikazanih podataka:**
[Izvori, formule, periodi, izuzeci i kontrolni postupak](../dokumentacija/finansije-metodologija-obracuna.md).
Dokument je usklađen sa implementacijom na dan 18.09.2026. i predstavlja glavno mesto za opis obračuna.
Ovaj README sadrži tehničko uputstvo i beleške prethodnih faza; ranije zabeleženi brojevi testova i
kontrolni iznosi predstavljaju provere tih faza, ne trenutno stanje izvora.

Izvor se isključivo čita preko postojećeg `server_db` aliasa:
`[PUTGEO-SERVER].[bazaims].dbo.nalog_z`, uz `posao`, `konto`, `ob_jedin` i `partner`.
Otvaranje izveštaja ne izvršava poslovne procedure SPFINizv. Posebna funkcija osvežavanja izvora,
opisana ispod, poziva `IMS_ERP.dbo.sp_AzurirajNalogZ` i ažurira lokalni `nalog_z`.

## Detalj šifre posla

`/finansije/posao/?job=413111&year=2026&month=8` otvara mesečni detalj posla.
Prazan `month=` (izbor „Cela godina”) daje period 01.01–31.12. izabrane godine u pokazateljima i svim tabelama.
Klik na šifru u izveštaju, grafikonima, rang-listama i knjiženjima vodi na isti detalj.
Iz knjiženja se prenosi mesec knjiženja; iz zbirnih prikaza poslednji mesec perioda.
Izveštaji po kontima i mesecima za izabranu šifru imaju i dugme za detalj.
Naplata po šiframa posla nudi vezu kada korisnik ima pristup finansijskoj analitici.

- Prihodi/rashodi i knt3 koriste datum knjiženja i ista isključenja zatvaranja kao ostali izveštaji.
- IF dokumenti koriste datum dokumenta i izabranu izvornu godinu. Tačna konta su `20400/20500`,
  a iznos je zbir `duguje - potrazuje` na izabranoj šifri, grupisan po godini, nalogu, vezi i partneru.
  Ovo je iznos sa konta potraživanja, ne prihod klase 6 niti dokaz naplate.
- Interne fakture su zaseban tab: `ON` na tačnim kontima `61420/61421/61521/64002`,
  sa iznosom `potrazuje - duguje`, istim pravilima perioda i grupisanja i očuvanim znakom korekcija.
- Vozila se prikazuju prema intervalima istorijskih dodela, zaključno sa danom pre sledeće dodele.
- Službena putovanja koriste datum putovanja, izuzimaju storna i zadržavaju postojeći obuhvat pristupa.
- Potraživanja koriste lokalni objavljeni snimak nove aplikacije i njena prava pristupa.
  Prikazani su datum stanja i vreme preuzimanja; nema istorijskog mesečnog preseka.
  Link partnera vodi u Potraživanja na isti snimak. Otvaranje taba ne čita stare view-ove Naplate.
- Lična zaduženja povezana su preko istorijskih dodela vozila; zaposleni se prikazuju iz zaključenih
  obračuna zarada na šifri posla. Istorijski spisak zaposlenih centra i ukupan trošak
  zarada centra čekaju potvrdu izvora i pravila. Godina bez uspešne sinhronizacije u detalju ne prikazuje finansijske iznose kao nulu.
- Detalj zahteva `finansije:dashboard` i dostupan centar/šifru; vozila, putni nalozi i Potraživanja
  dodatno poštuju prava njihovih modula. Otvaranje stranice ne pokreće sinhronizaciju/procedure.
- Početni HTML učitava samo izbor posla i zbirne pokazatelje. Osam tabela dobija podatke preko
  `/finansije/posao/tabela/<invoices|internal_invoices|expenses|vehicles|custody|employees|travel|collections>/` sa istim parametrima.
  Svaki zahtev ponovo proverava dostupnost šifre, period i prava izvornog modula.
  Tabele detalja su u osam tabova unutar zajedničke kartice. Sve se učitavaju u pozadini odmah po otvaranju stranice.
  Povratak na otvoren tab zadržava podatke, pretragu i stranicu, uz prilagođavanje širina kolona.
  Koriste `deferRender` i nude ponovni
  pokušaj kod greške. Skup za izabrani period se preuzima jednom po tabeli; pretraga, sortiranje i stranice
  obrađuju se u DataTables-u. Datumi imaju ISO vrednosti za sortiranje i lokalizovan prikaz/pretragu.
  Iznosi zadržavaju sirove numeričke vrednosti za sortiranje, nezavisno od prikazanih bedževa.

### Zajednički troškovi

`shared` AJAX endpoint preuzima aktivne mesečne kriterijume/koeficijente iz `posao_mes`
i raspodelu centra iz `blokraspodela`, prema aktuelnom centru u `posao`.
Osnovice su rezultat P−R poslova sa kriterijumom 1/2/3 za celu kompaniju,
računat iz lokalnih sinhronizovanih knjiženja za izabrani period. Sačuvana polja
`posao_mes.iznos/prihod/trosak` ne koriste se kao osnovica jer ih 52/52nt međusobno prepisuju.
Primenjuje se formula iz 52/53: osnovica × koeficijent centra / 100 × prosečan koeficijent posla / 100.
Koeficijent posla je zbir aktivnih mesečnih koeficijenata profitnih poslova podeljen brojem meseci perioda,
kao u 53; godišnji obračun nije zbir nezavisnih mesečnih raspodela. ZT je suprotan znak zbira alokacija,
pa je konačni rezultat P−R−ZT. Ostaju isključena zatvaranja i prenosi rezultata, kao u analitici.
Nepotpuna pokrivenost koeficijentima prikazuje upozorenje; nedostajuća raspodela nema izmišljenu nulu.
Otvaranje detalja ne izvršava UPDATE naredbe originalnih procedura. Koriste se njihova pravila i izvorni koeficijenti.
Provera: šifra 413111, avgust 2026: ZT 1.797.391,32 RSD, podudaranje sa sačuvanom avgustovskom raspodelom.

### Priliv, odliv i neto gotovina

`cash` AJAX endpoint čita izvorne podatke za autorizovanu šifru i isti mesečni/godišnji period.
`services/cash_flow.py` reprodukuje pripremu novčanih tokova iz `SPFINizv52nt`:
tip naloga NT i oznaka konta, posebna ON konta, zamena PDV-a arhivom (uključujući decembar prethodne
godine za januarsku uplatu), zamene obaveza troškovima ugovorenih poslova i zarada, refundacije,
isključenje 241 i provera aktivne mesečne evidencije. Konta zarada čitaju se iz `bazaldims.dbo.element`.
Prazna šifra se tretira kao 111111, kao u proceduri. Priliv je zbir `pot`, odliv zbir `dug`, neto P−O.
Odliv se u UI prikazuje sa suprotnim znakom (redovan odliv negativno/crveno); korekcije zadržavaju svoj smisao.
Ovo je obračun prema postojećoj poslovnoj metodologiji, ne prost zbir prometa bankovnog računa.
Poslovne tabele se ne menjaju i ne koriste se prepisiva polja `posao_mes.prihod/trosak/iznos`.
Nedostupna aktivna mesečna evidencija nije nula; nepotpuna pokrivenost daje upozorenje.
Godišnji obračun prati periodna pravila procedure (uključujući PDV na datum kraja perioda),
zato ne mora biti jednak zbiru odvojeno pokrenutih mesečnih obračuna.
ZT i tokovi imaju nezavisne AJAX zahteve, prikaz greške i ponovni pokušaj.

Provera sa izvornim računskim delom 52nt (isključivo njegove privremene tabele, bez trajnih UPDATE):
šifra 413111, avgust 2026: priliv 53.087.225,36; odliv 4.501.917,06; neto 48.585.308,30 RSD.
Potvrđena je jednakost priliva/odliva i za januar 2026, celu 2025. i celu 2026.

## Podaci i obračun

- Podržan obuhvat: preduzeće `FINANSIJE_COMPANY` (podrazumevano 1), godine od 2025.
- Identitet stavke: preduzeće, godina, vrsta naloga, broj naloga i stavka.
- Izveštaji koriste datum knjiženja `dat_naloga`; datumi izvora se čuvaju kao datumi, bez vremenske komponente.
- Prihodi = potražuje − duguje na klasi 6; rashodi = duguje − potražuje na klasi 5.
- Iznosi duguje/potražuje su u obračunskoj valuti RSD; valuta/devizni iznos čuvaju se zasebno.
- Storna ostaju sa izvornim znakom. Analitika izuzima završno zatvaranje vrste `ZAT` i konta
  prenosa rezultata `59900`/`69900`, potvrđena po izvornom šifarniku i nalozima za 2025.
  Redovni `ON` nalozi i korekcije na `59120`/`69120` ostaju uključeni. Ovo je namerna razlika
  u odnosu na zbir svih stavki klasa 5/6, koji nakon zatvaranja godine iznosi nula.
  Sinhronizacija čuva sve stavke; opcija „Sva knjiženja” i njen Excel izvoz uključuju i zatvaranja.
  Pokazatelji prihoda/rashoda i tada ostaju analitički, dok promet duguje/potražuje uključuje sve.
- Centar/OJ u zbirnom izveštaju dolazi iz **aktuelnog** `posao.blok`, dok je `nalog_z.oj` zaseban filter „OJ knjiženja“.
  Promena centra u šifarniku pregrupiše istoriju u osveženom obuhvatu. Mesečni koeficijenti raspodele ZT koriste se;
  zasebna istorija pripadnosti posla centru po datumima nije uvedena.
- Učešća imaju imenilac ukupnog filtriranog, korisniku dostupnog prikaza; nulti imenilac daje crtu.
- Knjiženja bez šifarnika se ne odbacuju. Prazan centar prikazan je kao neraspoređen (dostupan samo uz globalna prava ili izričito dozvoljen posao).
- Implementirani su IF iznosi na kontima potraživanja, interne ON fakture, ZT i novčani tokovi po pravilima 52nt.
  Iznos cele fakture preko svih poslova, povezivanje fakture sa pojedinačnom uplatom i spisak plaćenih
  računa dobavljača nisu izvedeni iz tih pokazatelja. Naplata je trenutno stanje dugovanja.

## Sinhronizacija

```powershell
.\.venv\Scripts\python.exe manage.py migrate finansije
.\.venv\Scripts\python.exe manage.py configure_finansije
.\.venv\Scripts\python.exe manage.py sync_finansije
.\.venv\Scripts\python.exe manage.py sync_finansije --year-from 2026 --year-to 2026
```

Svaki prolaz čita ceo izabrani opseg (nema pouzdanog vremena poslednje izmene na izvoru).
Upoređuje sadržaj po stabilnom ključu, unosi nove i ažurira izmenjene redove. Nestale redove
označava neaktivnim; ponovo pojavljen red vraća pod istim lokalnim ID-em. Šifarnici se osvežavaju
u istom koraku. Različite godine mogu poslednji put biti osvežene u različito vreme — istorija prikazuje obuhvat svakog prolaza.

SQL Server session application lock sprečava istovremene prolaze, uključujući komandnu liniju.
Izvorni upiti ne koriste NOLOCK. Pre objave se porede broj redova i oba iznosa po godini/kontu
sa dodatnim izvornim upitom. Ovo otkriva nepotpuno čitanje i mnoge konkurentne izmene, ali
nije transakcijski snimak udaljene baze; istovremene promene koje zadržavaju kontrolne zbirove
biće obuhvaćene sledećim prolazom. Sve lokalne izmene i uspešan zapis u istoriji čine jednu transakciju.
Greška zadržava prethodno stanje; prazan izvor ne može automatski ukloniti postojeće podatke.
Paketni upis na SQL Server eksplicitno kastuje novčane vrednosti (uključujući NULL) na
`numeric(18,2)`, zbog zaključivanja tipova u kombinaciji Django 5 / ODBC Driver 17.

Celery zadaci na redu `sync`:
- `finansije.tasks.sync_ledger_task(year_from=2025, year_to=None)`: opšti zadatak za zadati opseg godina.
- `finansije.tasks.sync_current_year`: svakog sata u :20.
- `finansije.tasks.sync_all_years`: svakog dana u 03:50 (vremenska zona projekta).
- `finansije.tasks.refresh_nalog_z_task`: svakog dana u 10:00 i 11:00 (`Europe/Belgrade`).

Rasporedi su dodati postojećoj komandi `sync_celery_periodic_tasks`. Posle isporuke koda
treba ponovo pokrenuti relevantne Celery workere da registruju nove zadatke, pa aktivirati raspored.
Samo finansije mogu se aktivirati komandom `manage.py configure_finansije --enable-schedule`.
Samo raspored procedure, bez aktiviranja drugih zadataka:
`manage.py configure_finansije --enable-nalog-z-schedule`.
Ne pokretati stare radnike sa novim rasporedom: mogu odbaciti nepoznat zadatak.

### Osvežavanje lokalnog nalog_z (18.09.2026.)

Na stranici sinhronizacije dugme **Osveži nalog_z** direktno poziva
`services.nalog_z.refresh_nalog_z`, a isti servis koristi Celery zadatak.
POST ruta `sinhronizacija/nalog-z/` zahteva prijavu, CSRF i obe postojeće dozvole
`finansije:sync_status` i `finansije:view_all`. Ne prihvata naziv procedure niti SQL iz zahteva.
Procedura nema parametre i obuhvata sve firme; godine bira sama (do uključivo 30. aprila
prethodna i tekuća godina, zatim tekuća). Otvaranje stranice ne pokreće proceduru.

Istorija `NalogZRefreshRun` beleži ko/odakle je pokrenuo, vreme, trajanje, status, godine,
ažurirane i dodate redove, grešku i Celery ID. Prikazuje se u posebnoj AJAX DataTable tabeli.
Brojač ažuriranih redova uključuje sve pogođene UPDATE-om, ne samo stvarno promenjene redove.
SQL `sp_getapplock` u IMS_ERP, vezan za istu sesiju kao procedura, sprečava preklapanje
ručnih i Celery poziva ovog servisa; zauzet poziv se beleži kao preskočen. Pozivi direktno
iz SQL alata/Agenta moraju koristiti isti lock da bi učestvovali u ovoj zaštiti.

Uspeh se upisuje tek nakon čitanja svih SQL rezultata i brojača. Greške se ne ponavljaju
automatski. Posle pada procesa raniji nezavršeni zapis dobija status „Ishod nepoznat“ pri
sledećem uspešnom preuzimanju lock-a; potrebno je proveriti stanje u bazi.
Prekid veze ili greška prijema rezultata ne garantuju da procedura nije već commit-ovala.
SQL timeout je samo tokom ove operacije `FINANSIJE_NALOG_Z_TIMEOUT` (podrazumevano 900 s),
pa se vraća prethodna vrednost; web/proxy timeout treba uskladiti jer ručni poziv traje
do završetka. Prekinut HTTP odgovor traži proveru istorije pre ponovnog pokretanja.

Migracija `0002_nalogzrefreshrun` dodaje isključivo tabelu istorije. Procedura i poslovni
view-ovi nisu prepravljani. Ova operacija ne preuzima LedgerEntry i ne preusmerava Naplatu
sa udaljenih view-ova na lokalni izvor. Procedura ne briše nestale izvorne redove.
Detaljan plan migracije ostaje u `dokumentacija/naplata-lokalni-izvor-plan.md`.

Na stranici `/finansije/sinhronizacija/` postoji dugme **Pokreni sinhronizaciju**, sa izborom
tekuće godine ili svih godina od 2025. POST ruta `/finansije/sinhronizacija/pokreni/` direktno
poziva `services.sync.sync_ledger`; ne šalje Celery zadatak i radi bez brokera/workera.
Celery zadaci i komandna linija pozivaju istu funkciju. Ručno pokretanje zahteva postojeće
dozvole `finansije:sync_status` i `finansije:view_all`, prijavu i CSRF token.

Tokom zahteva dugme je onemogućeno i prikazuje se stanje izvršavanja. Uspeh se prikazuje tek
posle provere kontrolnih zbirova; istorija se automatski osvežava. Bez JavaScripta forma radi
kao običan POST sa povratkom na istoriju. Zajednički SQL Server lock sprečava preklapanje ručnog,
komandnog i Celery izvršavanja. Ručni zahtev traje koliko i sama sinhronizacija; pri isporuci
treba uskladiti timeout web servera/proxy-ja sa trajanjem uvoza. Prekid HTTP odgovora nije dokaz
da je uvoz zaustavljen — ishod se proverava u istoriji.

Provera dugmeta i Celery ulaznih tačaka: 87 testova (`finansije core naplata`) prolazi, uključujući
direktan uvoz bez slanja zadatka, opseg godina, zabranu paralelnog izvršavanja, greške, dozvole i
CSRF. Stranica je renderovana na postojećoj bazi i potvrđena lokalna registracija zadatka na
redu `sync`. Ovom izmenom nije pokrenut stvarni uvoz niti aktiviran automatski raspored.

## Pristup

`/finansije/` i meni „Finansije“. Postojeća sinhronizacija dozvola registruje rute i dodatnu
dozvolu `finansije:view_all`. Uloga Uprava dobija sve dozvole; nova uloga Finansijska analitika
dobija pregled, knjiženja i izvoz, ograničeno postojećim dozvoljenim centrima/poslovima.
Prazna lista dozvoljenih centara nije globalan pristup. Korisnicima se uloge ne dodeljuju automatski.
Istorija sa kontrolnim podacima zahteva i `sync_status` i `view_all`. Izvoz proverava i dozvolu
odgovarajućeg izveštaja i isti opseg podataka kao ekran. Excel tretira izvorne tekstove kao tekst, nikada kao formule.

## Provera

```powershell
.\.venv\Scripts\python.exe manage.py test finansije core --settings=ims_erp.settings.testing
```

Kontrolni postupak za knjiženja, centre, ZT i tokove opisan je u kompletnoj metodologiji.
Nije potrebno pokretati izvorne poslovne procedure 52/53/55 radi prikaza ove aplikacije.

Pri proširenoj proveri zabeležen je postojeći pad testa
`nabavka.tests.ProcurementInvoiceJobCodeLinkTests.test_primary_invoice_job_code_cannot_be_added_as_additional`.
Isti pad potvrđen je sa originalnim integracionim modulima iz Git HEAD-a, bez aplikacije finansija
u test podešavanjima. Ovaj zadatak ne menja taj deo Nabavke.

### Provera prve instalacije — 16.09.2026.

- Migracija `finansije.0001_initial` primenjena na IMS_ERP.
- Prvi uvoz: 160.421 knjiženje; sledeći prolaz: 160.421 nepromenjeno, bez novih/uklonjenih redova.
- Kontrolni zbirovi po godini i kontu usaglašeni. Nezavisno provereni prihodi i rashodi za 2025. i 2026. prema izvoru.
- Sva četiri grupisanja, knjiženja, istorija sinhronizacije i Excel izvoz renderovani na SQL Server podacima (HTTP 200).
- 63 testa za `finansije core naplata` prolaze. Posebno provereni mešoviti NULL/decimal paketni unos i izmena na SQL Serveru, u poništenoj dijagnostičkoj transakciji.
- Lokalna ruta je dostupna na `http://127.0.0.1:8001/finansije/` i zahteva prijavu.
- Vizuelna provera u browseru nije bila dostupna u sesiji; renderovanje šablona i HTTP odgovori su provereni.
- Celery konekcija nije bila dostupna. Periodični zadaci su pripremljeni u kodu, ali ovom instalacijom nisu aktivirani.

### UI i grafikoni učešća

Stranice koriste zajedničko hero zaglavlje. Početni pregled `/finansije/` ima samo izbor perioda,
bez ostalih filtera i zbirne tabele. Podrazumevano prikazuje tekuću godinu do danas, uz izbor
datuma od 01.01.2025. i prečice za pojedinačne godine. Period važi za oba grafikona, rangiranje
i linkove ka detaljima. Neispravan period ne prikazuje finansijske rezultate. Prava pristupa
uvek ograničavaju dostupne podatke. Zasebna ruta `/finansije/izvestaji/` služi za
detaljne izveštaje po šiframa, kontima, mesecima i centrima, sa odgovarajućim naslovima.
Koristi istu dozvolu `finansije:dashboard`; nije potrebna nova dodela pristupa.
Detaljni izveštaji i knjiženja imaju kompaktne filtere u dva reda na desktopu, Select2 pretragu
i klizne prekidače. Excel izvoz ostaje u zaglavlju detaljnih izveštaja.

Pregled ima dve kartice, prvo centre pa šifre posla. Svaki red prikazuje prihode, rashode i
neto rezultat (prihodi minus direktni rashodi). Cela traka predstavlja 100%, a popunjenost
odgovara apsolutnom procentu učešća u zbiru odgovarajuće kolone: prihoda, rashoda ili neto rezultata.
Kada je zbir nula, procenat nije definisan i traka se ne popunjava. Učešća preko 100% zadržavaju
tačan procenat, dok je traka puna sa oznakom »; neto učešće može preći 100% zbog gubitaka drugih
centara/poslova. Svi stubići polaze od leve ivice, a negativni iznosi imaju
minus i crveni stubić. Kolona oznake centra je uža od kolona grafikona. Svi centri su odmah prikazani, a za šifre je vidljivo
prvih osam po neto rezultatu; jedno proširivanje otvara sve preostale šifre i sva tri pokazatelja,
bez unutrašnjeg skrola. Klik na oznaku otvara detaljni izveštaj sa istim periodom i obuhvatom.

Četiri kartice izdvajaju najbolje tri i najgore tri šifre, te najbolji i najgori centar, prema
neto rezultatu. Rangiraju se samo dodeljene šifre/centri sa nenultim prihodom ili rashodom.
Neraspoređene stavke ostaju u grafikonima i ukupnim iznosima. Kod manje od tri šifre prikazuje
se raspoloživi broj; rangiranja se mogu preklopiti. Grafikoni ne koriste spoljašnje biblioteke.

Provera: 76 testova (`finansije core naplata`) prolazi. Pregled i sva tri detaljna izveštaja
renderovani sa SQL Server podacima (HTTP 200); sva tri zbira u obe kartice usaglašena sa izveštajem.
Vizuelna provera u browseru nije bila dostupna u sesiji.

### Korekcija zatvaranja godine

Pre ispravke, zatvaranja 2025. na šifri `111111` (blok/centar `3`) poništavala su prihode i rashode
na nivou preduzeća, ali ostavljala poslovne iznose na drugim centrima. Za 2025–16.09.2026. to je
davalo pogrešno učešće centra 43 od 107,86%. Nakon izuzimanja zatvaranja i prenosa ono je 47,66%.
Nezavisan read-only upit izvornog `nalog_z`, povezanog sa `posao`, potvrđuje iznose i broj stavki
za svih 26 kombinacija godine i centra. Za 2025. prihodi su 1.758.842.530,46 RSD, rashodi
1.724.342.512,54 RSD; za 2026. do 16.09. prihodi 1.392.297.861,69 RSD, rashodi 1.009.974.470,86 RSD.
Neto prikazan na ekranu je razlika ovih prihoda i rashoda, pre poreza na dobit.

### Tabele

Uklonjen je zajednički red sa poslednjom uspešnom sinhronizacijom i linkom ka istoriji.
Zadržana su obaveštenja o početnom uvozu, neuspehu, uvozu u toku i nepotpunom obuhvatu.
Sve tabele finansija koriste lokalni DataTables: zbirni izveštaji obrađuju ceo skup redova
u pregledaču, a knjiženja i istorija sinhronizacije koriste serversku pretragu, sortiranje i
straničenje preko postojećih ruta (parametar `draw`). Broj redova po serverskom zahtevu ograničen
je na 200; autorizacija i filteri proveravaju se za svaki zahtev pre brojanja i pretrage.

Datum knjiženja i datum dokumenta su odvojene kolone. Na serveru se sortiraju izvorna polja
DateField/DateTimeField i DecimalField, uz stabilan poredak po primarnom ključu. Zbirne tabele
koriste nelokalizovane `data-order` vrednosti za iznose, procente i hronološke oznake meseca.
Oznake plus/minus ne menjaju sortiranje. Spoljni tekstovi u JSON ćelijama se HTML-escape-uju.
Ukupni iznosi iznad tabela i u podnožju odnose se na izabrane filtere, pre tekstualne pretrage tabele.

Provereni su prelazak meseca/godine pri sortiranju oba datuma, numeričko sortiranje iznosa pre
straničenja, pretraga celog skupa, ograničenja pristupa i bezbedan prikaz teksta. Serverski
DataTables odgovori provereni su i na stvarnim SQL Server podacima, bez izmena baze.

### Datumi i oznaka primenjenog perioda

Datumska polja koriste zajednički Flatpickr kalendar (`js-date`) i prikaz `DD.MM.GGGG`.
Forma prihvata taj format, završnu tačku i ISO datume iz linkova; widget normalizuje i ISO
parametre pre inicijalizacije kalendara. Time je otklonjeno neslaganje između zajedničkog
kalendara koji šalje `d.m.Y` i stare validacije koja je dozvoljavala samo `Y-m-d`.
Greške se prikazuju na srpskom. Primenjeni period je istaknut u zaglavlju, iznad pokazatelja,
uz grafikone i rangiranje. Pri neispravnim datumima pokazatelji i tabele se ne prikazuju.
Svih 47 testova finansija prolazi, uključujući lokalni i ISO format, prikaz vrednosti u poljima,
nepostojeće datume i obrnute opsege. Oba formata proverena su i na stvarnim podacima za 2025/2026.

### Dopuna detalja posla: zaduženja vozila i zaposleni (17.09.2026.)

Detalj posla sada ima zasebne tabove `Zaduženja vozila` i `Zaposleni i zarade`.
Obe DataTables tabele učitavaju se preko AJAX-a u pozadini odmah po otvaranju detalja,
za izabrani mesec ili celu godinu. Datumi/meseci imaju ISO vrednosti za sortiranje.

Zaduženja koriste postojeći `VehicleTravelOrder` i njegov queryset sa pravilima pristupa.
Veza sa poslom dobija se presekom perioda zaduženja, istorijske `JobCode` dodele i
izabranog perioda. Datumi su uključivi; povratak vozila na posao daje poseban interval.
Prikazuju se zaposleno lice, vozilo, broj zaduženja, izvorni datumi i interval na poslu.
Status otvoreno/zatvoreno je trenutno evidentirani status. Ne raspoređuju se kilometraža
ni troškovi srazmerno danima. Potrebne su obe dozvole `jobcode_list` i
`vehicle_travel_order_list`, uz finansijski pristup toj šifri.

Spisak zaposlenih čita `[PUTGEO-SERVER].[bazaldims].dbo.Zarada`, `PomLD` i `Radnik`,
isključivo SELECT upitima. Filteri su firma, godina, meseci, tačna `sif_pos`,
`PomLD.status_obr='Z'` i nenulti `dinara` ili `rekol`. Broj obračuna je DISTINCT `br_obr`
po zaposlenom i mesecu, pa više elemenata ne umnožava broj zaposlenih. Godišnji ukupan
broj broji različite `rasif` jednom. Otvoreni obračuni su izuzeti, a dostupnost zaključenih
obračuna označena po mesecima. Kada nema zaključenog obračuna, ukupan broj je crtica,
a ne tvrdnja da nema zaposlenih. Pristup zahteva `employee_list` i finansijski pristup poslu.

Ovo je spisak lica evidentiranih u obračunima na poslu, ne istorijski kadrovski spisak centra,
dokaz prisustva ili broj izvršilaca preračunat iz sati. Izvorne tabele zarada imaju podatke
za 2025. i januar–avgust 2026, ali otvoreni avgustovski obračun nije prikazan kao zaključen.
Lokalne radne liste nisu uzete za potpuni spisak jer postoje samo dve predate liste.

Preostalo: istorijska pripadnost zaposlenih
centru; pravilo ukupnog troška zarada i raspodele automatskih elemenata/doprinosa.
`SPLdKnjizenje` potvrđuje da prost zbir `Zarada.dinara` nije dovoljna zamena za puni trošak.
Procedura nije izvršavana; nijedan izvorni poslovni podatak nije menjan.

### Zbirna tabela šifara posla

`izvestaji/?group=job` prikazuje 100 redova po strani. Forma i serverska obrada
prihvataju samo period i centar; raniji parametri konto, posao, vrsta i OJ ne utiču na
ovaj pregled. Uključene su i šifre bez prometa u dostupnom opsegu korisnika.
Zbirni iznosi iz hero zaglavlja su uklonjeni; primenjeni period ostaje iznad tabele.

AJAX `izvestaji/sifre-podaci/` za svaki zahtev ponovo proverava prava, centar i period.
Tabela daje osam iznosa po poslu: prihod, negativan rashod, P−R, negativan ZT,
P−R−ZT, priliv, negativan odliv i neto gotovinu. ZT i tokovi učitavaju izvore grupno,
uz postojeće formule detalja (52/53 i 52nt), bez izvršavanja izvornih procedura.
Poslovni podaci se ne menjaju. Greška jednog izvora ne uklanja dostupne pokazatelje
drugog izvora ili lokalne prihode/rashode. Nedostajući iznos je crtica, delimičan
obračun ima zvezdicu i objašnjenje; provera pokrivenosti sinhronizacijom obuhvata sve godine.
Višegodišnji period se obračunava zasebno po kalendarskim godinama, a zatim sabira.

Tabela se završava neto gotovinom (ukupno 11 kolona). Šifra posla je jasno dugme
koje otvara detalj sa dokumentima i evidencijama. Detalj zadržava izbor poslednjeg
meseca perioda, osim izbora cele kalendarske godine koji
otvara celu godinu. Ta razlika je navedena ispod tabele. Trošak zarada
ostaje nedostupan dok se ne potvrde izvor i pravila. Izvoz u Excel koristi iste
brojčane pokazatelje, znakove i napomene o obuhvatu, uz link na detalj.

Finansijske numeričke kolone koriste namensko sortiranje `finance-signed` nad sirovim
`sort`/`data-order` vrednostima. Negativni iznosi se porede po brojčanoj vrednosti,
bez čitanja lokalizovanog teksta ili HTML oznaka; prazne vrednosti ostaju na kraju
i rastućeg i opadajućeg redosleda. Datumske kolone zadržavaju ISO sortiranje.
