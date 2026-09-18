# 7. Integracije

> **Za koga je ovo poglavlje:** programeri i održavanje.
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 7.1. Pregled

IMS ERP razmenjuje podatke sa **devet spoljnih sistema**, na **pet različitih načina**:

| Način | Sistemi | Rizik |
|---|---|---|
| **Povezani server (SQL)** | `PUTGEO-SERVER` (dve baze), `INFORMATIKA23`, `SERFIN` | Nedostupnost servera zaustavlja modul |
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
 │  SERFIN.bazaldims ─────────┘                                │
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

### 7.2.3. `SERFIN.bazaldims` — kadrovska

| Objekat | Sadržaj |
|---|---|
| `radnik` | OJ i ime, uz uparena trajanja |

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
| **Ne šalje na SEF** | Statuse sa SEF-a samo čita, kroz Potraživanja |
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
