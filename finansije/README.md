# Finansijska analitika — prva faza

Izvor se isključivo čita preko postojećeg `server_db` aliasa:
`[PUTGEO-SERVER].[bazaims].dbo.nalog_z`, uz `posao`, `konto`, `ob_jedin` i `partner`.
Ne izvršavaju se poslovne procedure SPFINizv i ne menja se postojeća lokalna tabela `nalog_z`.

## Podaci i obračun

- Podržan obuhvat: preduzeće `FINANSIJE_COMPANY` (podrazumevano 1), godine od 2025.
- Identitet stavke: preduzeće, godina, vrsta naloga, broj naloga i stavka.
- Izveštaji koriste datum knjiženja `dat_naloga`; datumi izvora se čuvaju kao datumi, bez vremenske komponente.
- Prihodi = potražuje − duguje na klasi 6; rashodi = duguje − potražuje na klasi 5.
- Iznosi duguje/potražuje su u obračunskoj valuti RSD; valuta/devizni iznos čuvaju se zasebno.
- Storna ostaju sa izvornim znakom. Prva faza ne isključuje vrste naloga (usklađeno sa SPFINizv51).
- Centar/OJ u zbirnom izveštaju dolazi iz **aktuelnog** `posao.blok`, dok je `nalog_z.oj` zaseban filter „OJ knjiženja“.
  Promena centra u šifarniku pregrupiše istoriju u osveženom obuhvatu. Istorijska raspodela i mesečni koeficijenti su sledeća faza.
- Učešća imaju imenilac ukupnog filtriranog, korisniku dostupnog prikaza; nulti imenilac daje crtu.
- Knjiženja bez šifarnika se ne odbacuju. Prazan centar prikazan je kao neraspoređen (dostupan samo uz globalna prava ili izričito dozvoljen posao).
- Fakturisano, naplaćeno, plaćanja dobavljačima i raspodela zajedničkih troškova **nisu** obračunati u ovoj fazi.

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
- `finansije.tasks.sync_current_year`: svakog sata u :20.
- `finansije.tasks.sync_all_years`: svakog dana u 03:50 (vremenska zona projekta).

Rasporedi su dodati postojećoj komandi `sync_celery_periodic_tasks`. Posle isporuke koda
treba ponovo pokrenuti relevantne Celery workere da registruju nove zadatke, pa aktivirati raspored.
Samo finansije mogu se aktivirati komandom `manage.py configure_finansije --enable-schedule`.
Ne pokretati stare radnike sa novim rasporedom: mogu odbaciti nepoznat zadatak.

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

Pre operativne upotrebe potvrditi računovodstveni obuhvat naloga (posebno završna knjiženja),
vezu centara i nekoliko poslova prema postojećem izveštaju 51. Nije potrebno pokretati procedure
52/53/55, koje menjaju poslovne podatke, radi prikaza ove aplikacije.

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
