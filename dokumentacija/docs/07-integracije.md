# 7. Integracije

> **Za koga je ovo poglavlje:** programeri i održavanje.
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 7.1. Pregled

IMS ERP razmenjuje podatke sa **devet spoljnih sistema**, na **pet različitih načina**:

| Način | Sistemi | Rizik |
|---|---|---|
| **Povezani server (SQL)** | `PUTGEO-SERVER` (dve baze; od 28.09.2026. i kadrovska, ranije `SERFIN`), `INFORMATIKA23` | Nedostupnost servera zaustavlja modul |
| **Automatsko preuzimanje sa portala (Selenium)** | NIS, OMV | **Promena izgleda stranice zaustavlja preuzimanje** |
| **Čitanje web stranice (HTTP + HTML)** | Registar menica NBS | Isti rizik |
| **Programski interfejs (HTTP + JSON)** | APR OpenAPI | Najstabilnije |
| **Ručni uvoz datoteka** | RFZO, operater mobilne telefonije, Excel planovi | Zavisi od oblika datoteke |
| **Izvoz datoteke** | Banka | — |

```
 ┌── ULAZ ─────────────────────────────────────────────────────┐
 │                                                             │
 │  cards.nis.rs ──────────Selenium───────┐                    │
 │  fleet.omv.com ─────────Selenium───────┤                    │
 │  webappcenter.nbs.rs ───HTTP+HTML──────┤                    │
 │  openapi.apr.gov.rs ────HTTP+JSON──────┼──► IMS ERP         │
 │  RFZO Excel ────────────ručni uvoz─────┤                    │
 │  Operater Excel ────────ručni uvoz─────┤                    │
 │  Excel planovi ─────────ručni uvoz─────┘                    │
 │                                                             │
 │  PUTGEO-SERVER.bazaims ────┐                                │
 │  PUTGEO-SERVER.bazaldims ──┼── SQL (povezani server)        │
 │  INFORMATIKA23.ID ─────────┤                                │
 │  (SERFIN — premešten na PUTGEO-SERVER.bazaldims 28.09.2026.)│
 └─────────────────────────────────────────────────────────────┘
                              │
 ┌── IZLAZ ─────────────────────────────────────────────────────┐
 │  Banka ◄──── datoteka virmana (180 znakova, cp1250)          │
 │  Obračun zarada ◄──── CSV obustava mobilnih                  │
 └──────────────────────────────────────────────────────────────┘
```

---

## 7.2. Povezani serveri (SQL)

> **Najvažnija zavisnost sistema.** Finansije i Kadrovi **ne rade** bez njih.

### 7.2.1. `PUTGEO-SERVER` — knjigovodstvo i zarade

| Baza | Objekti | Ko čita | Kada |
|---|---|---|---|
| **`bazaims`** | `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | `finansije/services/source.py` | Svaki sat u :20, dnevno 03:50 |
| `bazaims` | `posao_mes`, `blokraspodela`, `tipnal`, `vrsta_naloga`, `pdv_arhiva` | `finansije/services/shared_costs.py`, `cash_flow.py` | **Pri otvaranju ekrana** |
| `bazaims` | `posao` | `potrazivanja/services/source.py` | Uz sinhronizaciju |
| **`bazaldims`** | `element` | `finansije/services/cash_flow.py` | Pri otvaranju |
| `bazaldims` | `Zarada`, `PomLD`, `Radnik` | `finansije/services/job_people.py` | Pri otvaranju |
| **`BazaLDIMS`** | `Godmor`, `GodmorKor` | `hr/services/annual_leave.py` | **Ručno** |

> **[P] Samo `SELECT` upiti.** Nijedan modul ne piše u ove baze.

### 7.2.2. `INFORMATIKA23.ID` — sistem kontrole pristupa

| Objekat | Sadržaj | Ko čita |
|---|---|---|
| `Radnici` | Radnici u sistemu kontrole pristupa | `hr/services/attendance.py` |
| **`C_Prolasci_Radnika`** | **Pojedinačni prolasci** | Radna lista |
| `C_Tasteri` | Šifarnik tastera | Radna lista |
| `c_parovi_radnika_detalji` | Već uparena trajanja | Komanda `hr_attendance_summary` |

Čita se **pri svakom otvaranju radne liste**. [P]

### 7.2.3. Kadrovska — `PUTGEO-SERVER.bazaldims` (ranije `SERFIN`)

| Objekat | Sadržaj |
|---|---|
| `radnik` | OJ i ime, uz uparena trajanja |

**SERFIN je ugašen — potvrđeno od korisnika 28.09.2026.** Ciljni izvor kadrovske
evidencije je `PUTGEO-SERVER.bazaldims`. **[P]** Kod u repozitorijumu
(`hr/services/attendance.py`) već koristi taj izvor. Za pet nasleđenih `dbo` objekata
pripremljen je [SQL skript za administratora baze](../sql/2026-09-28-serfin-na-putgeo-server.sql).
Postojanje skripta nije dokaz da je primenjen u produkciji; status primene ostaje
**[N] — za proveru**.

Prethodna evidencija beleži pad sinhronizacije zaposlenih u 01:10 od 24.09. zbog
reference `dbo.hr_employee` na SERFIN. Skript u spoju sa `Sistemat` dodaje i `sif_pred`
da različita preduzeća ne umnože zaposlene. Brojevi 1.682 naspram 841 reda / 840 radnika
zapisani su u komentaru skripta kao kontrolni uzorak od 28.09, a ne kao trajno očekivanje.

#### 7.2.3.1. Provere nakon gašenja SERFIN-a

**Otvorena kontrolna lista za administratora baze i održavanje.** Provere ispod nisu
izvršene ovom dopunom dokumentacije. Ne čekati ponovno uključivanje SERFIN-a kao rešenje.
Za svaku stavku zabeležiti datum, izvršioca, rezultat i dokaz (definicija objekta,
kontrolni zbir ili zapis u istoriji zadataka).

| Provera | Šta proveriti / uslov za zatvaranje stavke |
|---|---|
| Veza i prava na novom izvoru | Sa SQL Servera koji drži `IMS_ERP` proveriti čitanje `PUTGEO-SERVER.bazaldims` preko istog naloga i mapiranja koje koristi aplikacija. Uspešan pristup ličnim administratorskim nalogom nije dovoljan. Proveriti i zavisnost od `INFORMATIKA23.ID` za sate. |
| Preostale reference na SERFIN | U aktivnim bazama pregledati definicije pogleda, funkcija i procedura, SQL zavisnosti, sinonime i korake SQL Agent poslova. Obuhvatiti dinamički SQL, `OPENQUERY`, povezane servere i spoljne skripte; sam spisak statičkih zavisnosti nije dovoljan. Za svako pojavljivanje označiti da li je aktivno ili samo istorijski komentar. |
| Pet poznatih objekata | U `IMS_ERP` proveriti stvarne definicije `dbo.hr_employee`, `dbo.hr_ugovori`, `dbo.hr_radni_sati_dan`, `dbo.fn_hr_radni_sati_dan` i `dbo.sp_bonusi_PR`. Potvrditi da aktivni upiti više ne upućuju na SERFIN. `default` i `server_db` su aliasi iste fizičke baze, ne dva mesta za primenu izmene. |
| Zaposleni i preduzeće | U `hr_employee` proveriti spoj `radnik`–`Sistemat` po `sif_sis` **i** `sif_pred`, broj redova, broj različitih `rasif`, duplikate, nazive radnih mesta, OJ i aktivnost. Razjasniti i zabeleženu razliku 841 red / 840 radnika. Brojeve uporediti sa aktuelnim izvorom i poslednjim pouzdanim preuzimanjem. |
| Ugovori zaposlenih | Za `hr_ugovori` proveriti `radstaz`, uslov `u_firmi = 'DA'`, broj ugovora, vezu preko `rasif` i datume `datum1` / `datum2`. Uzorak treba da uključi zaposlenog sa više ugovora i prestankom rada. |
| Dnevni i mesečni sati | Proveriti pogled, funkciju i aplikacijski upit na istom zaposlenom i periodu. U skriptu `hr_radni_sati_dan` ima fiksnu godinu **2025**; ne tumačiti prazne podatke za 2026. automatski kao kvar veze. Proveriti zaposlene koji ispadaju iz `INNER JOIN` jer im `rasif` nije nađen, kao i eventualno umnožavanje istog `rasif` između preduzeća. Razlike perioda, uslova za `NULL` i zaokruživanja evidentirati posebno; ovom proverom ne menjati obračun. |
| Bonusi i zarade | Pregledati definiciju `sp_bonusi_PR`, njene zavisnosti i pripadnost podataka preduzeću (`sif_pred`). Skript beleži da na novom izvoru postoje dva preduzeća. Vlasnik obračuna treba da potvrdi obuhvat i kontrolne zbirove; proceduru **ne izvršavati radi provere veze**, jer menja podatke. Promene obračunske logike traže pisanu potvrdu. |
| Isporuka aplikacije | Potvrditi da produkcioni kod, web proces i Celery worker koriste novu verziju `hr/services/attendance.py`. Posle isporuke osvežiti procese koji učitavaju promenjeni kod; nije dovoljno da je izmena samo u razvojnom repozitorijumu. |
| Sinhronizacija i ekrani | Posle potvrde baze i isporuke proveriti sledeće izvršavanje `fleet.tasks.sync_hr_employees_task` u **01:10**, ishod i broj preuzetih zapisa na `/administracija/task-history/`. U Kadrovima proveriti spisak zaposlenih, ugovore i radnu listu; pregled sati iz komande `hr_attendance_summary` uporediti sa kontrolnim uzorkom. Potvrditi da se podaci zaista osvežavaju, a ne samo da se stari podaci prikazuju. |

**Prelazak je potvrđen tek kada** nema aktivne zavisnosti navedenih tokova od
ugašenog servera, podaci i kontrolni uzorci su usaglašeni, a sinhronizacija prođe pod
produkcijskim nalogom. Do tada zabeležiti neuspešne stavke i poslednje uspešno osvežavanje.
Promene nasleđenih `dbo` objekata radi administrator baze, uz čuvanje prethodnih definicija;
aplikacija ih ne menja.

#### 7.2.3.2. Zatečeno stanje 28.09.2026. (provera čitanjem)

**Skript još nije primenjen: 30 objekata na SMS-SERVER i dalje čita SERFIN, a
sinhronizacija zaposlenih pada od 24.09.2026.** Provera je rađena samo čitanjem
(`sys.sql_modules` u svim bazama, `msdb` koraci SQL Agenta, istorija zadataka). Ovo je
presek stanja, a ne zatvaranje stavki iz kontrolne liste iznad.

Povezani server `SERFIN` (dobavljač `MSDASQL`) još je definisan, ali upit na njega javlja
*„Cannot initialize the data source object of OLE DB provider MSDASQL for linked server
serfin“*. Nijedan korak SQL Agent posla ne pominje SERFIN.

| Baza | Objekata koji čitaju SERFIN | Pripremljen skript |
|---|---|---|
| `IMS_ERP` | 5 — `hr_employee`, `hr_ugovori`, `hr_radni_sati_dan`, `fn_hr_radni_sati_dan`, `sp_bonusi_PR` | Da |
| `Kadro` | 14 pogleda — `br_naucnika`, `br_zaposlenih`, `fluktuacija_zap`, `grele`, `k1_ispod_minimalca`, `ob_jedin`, `obustave_trenutno`, `osnovna_tabela`, `spisak_zap_v1`, `v_radni_sati_dan`, `v_radstaz`, `v_zarada`, `vrsta_prihoda`, `zap_na_odredjeno` | Ne |
| `Reports` | 7 — procedure `sp_db_bonusi`, `sp_db_bonusi_k4`; pogledi `br_naucnika`, `fluktuacija_zap`, `NO_br_zap`, `NO_br_zap_oj`, `v_sif_pos_radnika` | Ne |
| `Mobilni` | 2 pogleda — `kontrola`, `obustave_nezap` | Ne |
| `Vozila` | 2 pogleda — `tro_zarade`, `zaposleni` | Ne |

**Uticaj na aplikaciju.** Aplikacija direktno čita samo `dbo.hr_employee`:

| Tok | Stanje 28.09.2026. |
|---|---|
| `fleet.tasks.sync_hr_employees_task` (01:10) | Pada 24–27.09; poslednje uspešno 23.09. (841 zapis) |
| Šifarnik radnog vremena (`hr/services/work_time_catalog.py`) | Pada pri osvežavanju — čita isti pogled |
| Spisak zaposlenih, dodele uloga, ostali moduli | Rade, sa podacima od 23.09; promene posle toga ne stižu |

Ostala četiri objekta u `IMS_ERP` i svih 25 objekata u drugim bazama aplikacija ne poziva,
a nijedan objekat u `IMS_ERP` ne zavisi od njih. Verovatno ih koriste stari izveštaji,
Excel tabele ili stari programi — vlasnici nisu utvrđeni. `sp_bonusi_PR` pored SERFIN-a
čita i `Reports.dbo.db_bonusi`, `Reports.dbo.db_bonusi_k4` i `Kadro.dbo.elsif_pozicija`.

**Novi izvor je ažuran:**

| Provera na `PUTGEO-SERVER.bazaldims` | Rezultat |
|---|---|
| `radnik` | 840 radnika, 331 aktivan |
| Poslednji primljen radnik | 14.09.2026. (šifra 1057 — već je u aplikaciji) |
| Poslednji obračun u `zarada` | avgust 2026. (preduzeće 1: 3.930 redova, preduzeće 2: 1 red) |

**Otvorena pitanja:**

1. Da li `sp_bonusi_PR` treba ograničiti na `sif_pred = 1`? `zarada` ima i preduzeće 2
   (34 reda ukupno). Ko koristi proceduru?
2. Ko su vlasnici 25 objekata u bazama `Kadro`, `Reports`, `Mobilni` i `Vozila`, koji
   se još koriste i ko odobrava izmenu? Prelazak je ista zamena imena servera, uz proveru
   spoja po `sif_pred` gde se čita `Sistemat` ili `zarada`.
3. U `zarada` postoje obračuni za godine 3022, 3000 i 2100, a radnik 1041 ima datum dolaska
   01.01.3000. Probni ili pogrešni unosi?
4. Posle prelaska svih objekata: ukloniti povezani server `SERFIN`, da svaki zaostali poziv
   odmah prijavi grešku?

### 7.2.4. Šta se dešava kada server nije dostupan [P]

| Modul | Ponašanje |
|---|---|
| **Kadrovi — radna lista** | Ekran radi; sati prikazani kao „—“, uz poruku *„Izvor prolazaka trenutno nije dostupan.“* |
| **Kadrovi — godišnji odmori** | Sinhronizacija ne uspeva; postojeći podaci ostaju |
| **Finansije — prihodi i rashodi** | **Rade** — čitaju lokalnu kopiju |
| **Finansije — ZT, tok gotovine, zaposleni** | **Ne rade** — greška na tom delu ekrana |
| **Finansije — sinhronizacija** | Ne uspeva; postojeći podaci ostaju |

> **[P] Dobro rešeno:** greška jednog izvora na kartici posla **ne uklanja** pokazatelje
> iz drugih izvora — svaki tab se učitava zasebno i nudi ponovni pokušaj.

---

## 7.3. Nasleđeni pogledi u bazi `IMS_ERP`

**37 objekata**, čitaju se preko aliasa `server_db`.
Potpun spisak: [4.12. Nasleđeni objekti baze](04-baza-podataka.md#412-nasleđeni-objekti-baze-dbo).

> **[P]** Deo tih pogleda **interno prelazi na `PUTGEO-SERVER`**, pa „lokalno“ ne znači
> ni brzo ni nezavisno.

### Procedura `IMS_ERP.dbo.sp_AzurirajNalogZ` [P]

Jedina procedura koju sistem pokreće. Detaljno:
[4.12.4](04-baza-podataka.md#4124-procedura-ims_erpdbosp_azurirajnalogz).

| Osobina | Vrednost |
|---|---|
| Pokreće je | `finansije/services/nalog_z.py` |
| Kada | 10:00 i 11:00 (`Europe/Belgrade`), ili ručno |
| Zaštita | `sp_getapplock` u **istoj sesiji** koja pokreće proceduru |
| Rok | 900 s (`FINANSIJE_NALOG_Z_TIMEOUT`) |
| Istorija | `finansije_nalogzrefreshrun` |

**Procedure koje se NE pokreću [P]:** `SPFINizv52`, `53`, `55`, `52nt`, `SPLdKnjizenje`.
Njihova pravila su **prepisana u Python**.

---

## 7.4. NIS i OMV — gorivo (Selenium)

### 7.4.1. Kako radi [P]

```
 1. Prijava na internu mrežu    https://control.ims.rs:4081
 2. Pokretanje pregledača       Chrome (chrome-for-testing)
 3. Prijava na portal           cards.nis.rs  /  fleet.omv.com
 4. Preuzimanje datoteke        CSV / Excel u lokalni direktorijum
 5. Obrada datoteke             pandas / openpyxl
 6. Upis                        TransactionNIS / TransactionOMV + FuelConsumption
 7. Čišćenje duplikata          cleanup_omv_fuel_data(apply=True)   ← samo OMV
```

| Portal | Adresa | Zadatak | Vreme | Red |
|---|---|---|---|---|
| **NIS** | `https://cards.nis.rs` | `fleet.tasks.run_nis_command` | 04:20 | `selenium` |
| **OMV putnička** | `https://fleet.omv.com/FleetServicesProduction` | `fleet.tasks.run_omv_putnicka_command` | 05:10 | `selenium` |
| **OMV teretna** | isti | `fleet.tasks.run_omv_teretna_command` | 06:10 | `selenium` |

**Zaključavanje:** Redis, **4 sata**. [P]

### 7.4.2. Ručni uvoz kao zamena [P]

Ako automatsko preuzimanje ne uspe, datoteka se može uvesti ručno:

| Ekran | Šta prima |
|---|---|
| `/import-nis-excel/` | NIS Excel |
| `/import-omv-putnicka-csv/` | OMV CSV, putnička |
| `/import-omv-teretna-csv/` | OMV CSV, teretna |

### 7.4.3. Rizici [P]

| Rizik | Opis |
|---|---|
| **Promena izgleda stranice** | Selenium traži elemente po izgledu — promena zaustavlja preuzimanje |
| **Isticanje lozinke** | Prijava ne uspeva; posao pada uz grešku u `TaskHistory` |
| **Mrežni portal** | Bez prijave na `control.ims.rs` nema pristupa internetu |
| **Chrome verzija** | Mora odgovarati upravljaču (`chrome-for-testing` u projektu) |
| **Duplikati OMV** | Rešeno čišćenjem pri uvozu i filterom pri čitanju — vidi [V-06](obracuni/06-02-flota-gorivo.md) |

> **[N] Q7:** gde se čuvaju pristupni podaci za portale i ko ih obnavlja nije zabeleženo.

---

## 7.5. Registar menica NBS

| | |
|---|---|
| Adresa | `https://webappcenter.nbs.rs/PnWebApp` |
| Način | `requests` + `BeautifulSoup` — **čitanje HTML stranice** |
| Pokretanje | **Ručno**, sa ekrana `/menice/izlazna/azuriraj/` |
| Pretraga po | PIB dužnika (podrazumevano **PIB IMS-a, upisan u kod**) |
| Preuzima | 20 polja o menici + **avalisti** sa zasebne adrese |
| Rok | 30 s |

**Rizik [P]:** promena izgleda stranice zaustavlja preuzimanje — [P-41](10-poznati-problemi.md).

---

## 7.6. APR OpenAPI

| | |
|---|---|
| Adresa | `https://openapi.apr.gov.rs/api/opendata/companies` |
| Način | `GET`, odgovor u JSON obliku, kodiranje `utf-8-sig` |
| Prijava | **Nije potrebna** — javni skup podataka |
| Pokretanje | **Ručno**, pojedinačno ili paketno |
| Osnov povezivanja | **Matični broj**, dopunjen vodećim nulama do 8 cifara |
| Preuzima | `PoslovnoIme`, `NazivStatus` |
| Rok | 60 s |

**Rizici [P]:**

| Rizik | Opis |
|---|---|
| **Zaobilaženje SSL provere** | Pri SSL grešci zahtev se ponavlja sa `verify=False` — [P-40](10-poznati-problemi.md) |
| **Uzak uslov statusa** | Aktivan samo za **tačno** `активан` — svaki drugi zapis daje „neaktivan“ |

---

## 7.6a. SEF — Sistem elektronskih faktura (od 30.09.2026.)

| | |
|---|---|
| Adresa | `https://efaktura.mfin.gov.rs/api/publicApi/…` (test: `https://efakturatest.mfin.gov.rs`) |
| Način | REST, `requests`; odgovor JSON, fakture u UBL (XML) |
| Prijava | **API ključ** u zaglavlju `ApiKey` — `SEF_API_KEY` iz `.env`, nikad u kodu |
| Pokretanje | Noću u 06:50 i ručno (Finansije → SEF fakture, `manage.py sync_sef`) |
| Preuzima | ulazne fakture (pregled), izlazne (ID + UBL), promene statusa, na zahtev PDF i UBL |
| Šalje | **Ništa** — nema slanja, prihvatanja, odbijanja ni storniranja |
| Rok | 60 s po pozivu (`SEF_TIMEOUT`) |

**Rizici [P]:** SEF ima noćnu pauzu (zato jutarnji termin); promene statusa čuva mesec dana,
pa duži prekid noćnog posla ostavlja stare statuse do sledećeg preuzimanja pregleda. Ključ
daje pristup SEF-u u ime Instituta — ako ga koristi i drugi sistem, radnje prihvatanja i
odbijanja ostaju samo u tom sistemu. Specifikacija: „API dokumentacija SEF“, 31.07.2026.

---

## 7.7. Ručni uvoz datoteka

| Izvor | Oblik | Ekran / komanda | Učestalost |
|---|---|---|---|
| **RFZO — bolovanja** | `.xlsx` | `/hr/bolovanja/uvoz/` | Mesečno |
| **Operater — paketi** | Excel | `/mobilni/import/` | Po potrebi |
| **Operater — korisnici** | Excel | isto | Po potrebi |
| **Operater — dodele** | Excel, **uz godinu i mesec** | isto | Mesečno |
| **Operater — potrošnja** | Excel, **uz godinu i mesec** | isto | Mesečno |
| **Plan javnih nabavki** | `.xlsx` | `/nabavka/javne-nabavke/uvoz/` | Pri izmeni plana |
| Garažni zahtevi | Excel | `import_garage_requests_excel` | Jednokratno |
| Ugovori | Excel | `import_contracts_excel` | Jednokratno |
| Menice (ulazne i izlazne) | Excel | `import_*_menice_excel` | Jednokratno |
| Šifarnik ocenjivanja | Excel | `import_evaluation_catalog` | Po izmeni |
| Šifarnik elemenata radne liste | Excel | `import_work_time_catalog` | Po izmeni |
| Opomene (Potraživanja) | Excel | `/potrazivanja/uvoz-opomena/` | Po potrebi |
| Gorivo NIS / OMV | Excel / CSV | Ekrani uvoza | Kada Selenium ne uspe |

### Zajedničke zaštite pri uvozu [P]

| Zaštita | Gde |
|---|---|
| **Najveća veličina datoteke** | RFZO: 10 MB; raspakovano najviše 50 MB |
| **Najveći broj redova** | RFZO: 50.000 |
| **Otisak datoteke** | RFZO i Potraživanja — sprečava dvostruki uvoz |
| **Sve ili ništa** | RFZO, godišnji odmori, plan javnih nabavki |
| Dnevnik uvoza | Mobilni (`MobileImportLog`), RFZO (`SickLeaveImport`) |

---

## 7.8. Izlaz iz sistema

### 7.8.1. Banka — virman

| | |
|---|---|
| Oblik | Tekstualna datoteka, **180 znakova po redu**, `cp1250`, `CRLF` |
| Sadržaj | Dva reda zaglavlja + jedan red po nalogu |
| Naziv | `Virman-putni-nalozi-GGGGMMDD-HHMMSS.txt` |
| Prenos | **Ručno** — blagajna preuzima i učitava u elektronsko bankarstvo |

Detaljno: [6.10. Isplate](obracuni/06-10-isplate.md).

### 7.8.2. Obračun zarada — obustave mobilnih

| | |
|---|---|
| Oblik | CSV, razdvajač `;`, UTF-8 **sa BOM**, `CRLF` |
| Kolone | `Godina;Mesec;Šifra radnika;Iznos obustave` |
| Obuhvat | Samo **aktivni zaposleni**; iznos u **celom dinaru** |
| Prenos | **[N] Nije potvrđeno** — uvozom ili ručno |

### 7.8.3. Ostali izvozi

Excel i CSV izvozi u Floti, Nabavci, Ugovorima, Mobilnom, Potraživanjima i Finansijama —
namenjeni **čoveku**, ne drugom sistemu. [Z]

---

## 7.9. Šta sistem NE radi

| Ne radi | Napomena |
|---|---|
| **Nema REST API** | `djangorestframework` je u zavisnostima, ali se ne koristi |
| **Ne šalje na SEF** | Fakture i statuse sa SEF-a samo čita — kroz Potraživanja i, od 30.09.2026., Finansije → SEF fakture (API) |
| **Ne knjiži** | Sve knjiženje ostaje u nasleđenom ERP-u |
| **Ne šalje e-poštu** | Nema podešenog slanja pošte |
| **Ne prima podatke spolja programski** | Svaki ulaz je sinhronizacija ili ručni uvoz |

---

## 7.10. Pregled rizika integracija

| Integracija | Rizik | Ozbiljnost | Šta se dešava |
|---|---|---|---|
| NIS / OMV (Selenium) | Promena stranice, lozinka | **Visoka** | Nema novih podataka o gorivu |
| NBS registar menica | Promena stranice | Srednja | Nema novih menica |
| APR OpenAPI | Promena odgovora, SSL | Srednja | Status partnera se ne osvežava |
| `PUTGEO-SERVER` | Nedostupnost | **Visoka** | Finansije i odmori ne rade |
| `INFORMATIKA23` | Nedostupnost | Srednja | Radna lista bez prolazaka |
| Nasleđeni pogledi | **Izmena definicije** | **Visoka** | **Rezultat se menja bez traga** — [P-27](10-poznati-problemi.md) |
| Ručni uvoz | Promena oblika datoteke | Srednja | Uvoz ne prolazi, uz poruku |

---

## 7.11. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kada se šta pokreće? | [9. Održavanje](09-odrzavanje.md) |
| Koje tabele se pune? | [4. Baza podataka](04-baza-podataka.md) |
| Kako se obrađuju preuzeti podaci? | [6. Analize i obračuni](06-analize-i-obracuni.md) |
| Šta je uočeno kao problem? | [10. Poznati problemi](10-poznati-problemi.md) |
