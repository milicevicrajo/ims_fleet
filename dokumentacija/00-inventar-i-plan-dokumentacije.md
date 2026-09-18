# FAZA 1 — Inventar sistema i plan dokumentovanja

**Dokument:** Inventar IMS ERP aplikacije i predlog strukture dokumentacije
**Verzija:** 0.1 (radna verzija za potvrdu)
**Datum:** 18.09.2026.
**Status:** čeka potvrdu naručioca pre prelaska na FAZU 2

---

## 0. Kako čitati ovaj dokument

Ovo je rezultat FAZE 1: pregled celog repozitorijuma i popis svega što je pronađeno.
Ovaj dokument **ne objašnjava** kako se šta računa — to je predmet FAZE 3. Ovde je
samo popisano **šta postoji**, **gde se nalazi** i **kojim redosledom predlažem da se dokumentuje**.

Svaka tvrdnja u dokumentu je označena statusom pouzdanosti:

| Oznaka | Značenje |
|---|---|
| **[P]** | Potvrđeno — pročitano direktno iz koda, migracija ili konfiguracije u repozitorijumu |
| **[Z]** | Zaključeno — logičan zaključak iz implementacije, ali nije eksplicitno napisano |
| **[N]** | Nepotvrđeno — potrebna potvrda od Vas ili krajnjeg korisnika |

---

## 1. Osnovni podaci o sistemu

| Stavka | Vrednost | Status |
|---|---|---|
| Naziv projekta (tehnički) | `ims_erp` (Django projekat), radni direktorijum `ims_fleet` | [P] |
| Tip sistema | Interna web ERP aplikacija (monolit) | [P] |
| Programski jezik | Python 3.12 | [P] |
| Radni okvir | Django 5.0.9 | [P] |
| Baza podataka | Microsoft SQL Server (`mssql-django` 1.5, ODBC Driver 17) | [P] |
| Pozadinski poslovi | Celery 5.4 + Redis (broker i backend) + `django-celery-beat` 2.7 | [P] |
| Operativni sistem servera | Windows (servis preko NSSM — `nssm.bat`) | [P] |
| Korisnički interfejs | Django templates (server-side), DataTables, Select2, widget-tweaks | [P] |
| Ukupno Python koda | ~59.500 linija u 351 fajlu (bez migracija i biblioteka) | [P] |
| Ukupno šablona | 280 HTML fajlova — 222 stranice + 58 delova stranica | [P] |
| Ukupno Django modela | 134 klase: 118 sopstvenih tabela, 13 nad nasleđenim pogledima, 3 apstraktne | [P] |
| Ukupno migracija baze | 146 migracionih fajlova u 9 aplikacija | [P] |
| Automatski testovi | 550 test metoda u 31 fajlu | [P] |
| Jezik interfejsa | Srpski (latinica); `LANGUAGE_CODE = 'en'`, `TIME_ZONE = 'CET'` | [P] |
| Format datuma | `d/m/Y` (prikaz i unos) | [P] |

### 1.1. Spisak spoljnih biblioteka koje nose poslovnu funkciju

| Biblioteka | Uloga u sistemu | Status |
|---|---|---|
| `selenium` 4.23 + `webdriver-manager` | Automatsko preuzimanje podataka o gorivu sa portala NIS i OMV | [P] |
| `beautifulsoup4` / `requests` | Preuzimanje podataka iz Registra menica NBS i APR OpenAPI | [P] |
| `openpyxl` | Uvoz i izvoz Excel datoteka (plan javnih nabavki, RFZO bolovanja, mobilni, ugovori, menice) | [P] |
| `pandas` / `numpy` | Obrada preuzetih CSV/Excel datoteka o gorivu | [P] |
| `pyodbc` / `mssql-django` | Veza ka SQL Serveru i direktni SQL upiti nad `dbo.*` objektima | [P] |
| `psycopg2-binary` | Prisutan u `requirements.txt`, ali nijedna konfiguracija ne koristi PostgreSQL | [Z] |
| `djangorestframework` | Prisutan u `requirements.txt`, ali nije u `INSTALLED_APPS` niti se koristi | [Z] |

---

## 2. Struktura repozitorijuma

```
ims_fleet/
├── manage.py                     Ulazna tačka za komande
├── ims_erp/                      Konfiguracija projekta (settings, urls, celery, wsgi/asgi)
│   ├── settings/
│   │   ├── base.py               Zajedničke postavke, Celery, rutiranje redova
│   │   ├── development.py        Razvojna baza
│   │   ├── production.py         Produkciona baza
│   │   └── testing.py            Postavke za testove
│   ├── urls.py                   Korenska mapa adresa
│   └── celery.py                 Inicijalizacija Celery aplikacije
│
├── core/                         Zajedničke osnove: korisnici, uloge, dozvole, log rada, istorija taskova
├── fleet/                        Vozni park (najveći modul) + korenske adrese aplikacije
├── hr/                           Kadrovi: zaposleni, radne liste, odsustva, ocenjivanje
├── finansije/                    Finansijska analitika (prihodi, rashodi, tok gotovine, šifre posla)
├── nabavka/                      Nabavka: zahtevi, fakture EUF/UF, roba, javne nabavke, narudžbenice
├── naplata/                      Naplata (postojeća, radi nad SQL view-ovima) + pravna služba
├── potrazivanja/                 Nova Naplata (lokalne Django tabele, u paralelnom radu)
├── ugovori/                      Partneri, zahtevi, ponude, ugovori, aneksi, garancije
├── menice/                       Ulazne i izlazne menice (uz preuzimanje iz registra NBS)
├── mobilni/                      Mobilna telefonija: paketi, dodele, potrošnja, obustave
├── isplate/                      Generisanje virmana i konverzija za neoporeziva primanja
├── izvestaji/                    Prazan direktorijum (nije Django aplikacija)      [P]
│
├── templates/                    Globalni šabloni (osnovni izgled, bočni meniji, prijava)
├── media/                        Otpremljeni fajlovi (slike vozila, dokumenti ugovora, saobraćajne)
├── logs/                         Dnevnici rada
└── dokumentacija/                Postojeća dokumentacija (Markdown, Word, slike ekrana, pomoćne skripte)
```

**Napomena o korenskom direktorijumu [P]:** u korenu repozitorijuma se trenutno nalazi
i veći broj radnih datoteka koje nisu deo aplikacije (Word i Excel analize, izvozi `.csv`,
`db.sqlite3`, dnevnici `*.log` veličine ~18 MB, privremene `tmp*.csv` datoteke,
primeri virmana). Predlog za čišćenje je naveden u poglavlju 13.

---

## 3. Baze podataka i konekcije

### 3.1. Konfigurisane konekcije [P]

| Alias | Motor | Baza | Server | Namena |
|---|---|---|---|---|
| `default` | `mssql` | `IMS_ERP` | `SMS-SERVER` | Sve Django tabele (ORM), migracije |
| `server_db` | `mssql` | `IMS_ERP` | `SMS-SERVER` | Direktni SQL upiti nad nasleđenim `dbo.*` pogledima i procedurama |
| `local` | `sqlite3` | `db.sqlite3` | — | Definisan samo u `production.py`; ne koristi se u kodu |

**Ključni arhitektonski nalaz [P]:** `default` i `server_db` pokazuju na **istu fizičku bazu**
(`IMS_ERP` na `SMS-SERVER`). Razdvojeni su namenski, ne fizički: `default` se koristi za
Django modele, a `server_db` za "sirovi" SQL nad objektima nasleđenog ERP sistema.

**Posledica [Z]:** Django aplikacija i stari ERP dele istu bazu. Django migracije i
nasleđeni `dbo.*` objekti žive jedan pored drugog. To je bitno za svako planiranje
izmena i za razumevanje toga šta se dešava kada neko promeni pogled u bazi.

### 3.2. Izvori podataka izvan Django modela (SQL pogledi, tabele i procedure)

Kompletan spisak `dbo.*` objekata koji se čitaju iz koda [P]:

| Objekat u bazi | Koristi ga | Poslovni sadržaj (preliminarno) | Status |
|---|---|---|---|
| `dbo.baza` | `naplata/views.py` | Stavke dugovanja po partnerima | [P] |
| `dbo.dodela_bucketa` / `dodela_baketa` | `naplata/queries.py`, `naplata/models.py` | Raspoređivanje salda u starosne razrede (baketi) | [P] |
| `dbo.ispravke` | `naplata/models.py` | Ispravke knjiženja | [P] |
| `dbo.partneri` | `naplata`, `ugovori/services.py` | Šifarnik partnera starog sistema | [P] |
| `dbo.kontakti`, `dbo.napomene`, `dbo.opomene`, `dbo.poziv_pismo`, `dbo.pozivi_tel`, `dbo.tuzbe` | `naplata/models.py` | Operativne evidencije naplate (nezavisne tabele, `managed=False`) | [P] |
| `dbo.sif_baket`, `dbo.sif_kategorija` | `naplata/models.py` | Šifarnici baketa i kategorija | [P] |
| `dbo.v_neodobreneIF` | `naplata/queries.py` | Izdate fakture bez odobrenja na SEF-u | [P] |
| `dbo.v_tuzeni` | `naplata/views_pravna.py` | Pregled tuženih lica | [P] |
| `dbo.posao` | `potrazivanja/services/source.py` | Šifre posla | [P] |
| `dbo.sp_AzurirajNalogZ` | `finansije/services/nalog_z.py` | **Uskladištena procedura** — osvežavanje naloga Z | [P] |
| `dbo.element` | `finansije/services/cash_flow.py` | Elementi obračuna zarada (za tok gotovine) | [P] |
| `dbo.hr_employee` | `hr/sync.py`, `hr/services/work_time_catalog.py` | Kadrovska evidencija zaposlenih | [P] |
| `dbo.Radnici`, `dbo.C_Prolasci_Radnika`, `dbo.C_Tasteri`, `dbo.c_parovi_radnika_detalji`, `dbo.radnik` | `hr/services/attendance.py` | Evidencija prolazaka (sistem kontrole pristupa) — **preko povezanog servera `INFORMATIKA23.ID`** | [P] |
| `dbo.nbv_preuzete_EUF` | `nabavka/services/euf.py` | Preuzete elektronske ulazne fakture | [P] |
| `dbo.nbv_EUF_stavke` | `nabavka/services/source_snapshots.py` | Stavke ulaznih faktura (UF) | [P] |
| `dbo.nbv_roba` | `nabavka/services/source_snapshots.py` | Evidencija robe | [P] |
| `dbo.nbv_sif_pos_par` | `nabavka/views/reports.py` | Veza partner ↔ šifra posla | [P] |
| `dbo.fleet_potrazivanje_ddor` | `fleet/sync/external.py` | Knjiženja osiguranja DDOR | [P] |
| `dbo.fleet_otpis` | `fleet/sync/external.py`, `fleet/support/report_queries.py` | Otpisana vozila | [P] |
| `dbo.fleet_servisi` | `fleet/sync/services.py` | Knjiženja servisa vozila | [P] |
| `dbo.fleet_trebovanja` | `fleet/sync/services.py` | Trebovanja materijala | [P] |
| `dbo.fleet_zatvoren_putni` | `fleet/management/commands/sync_putni_nalozi_isplaceno.py` | Isplaćeni iznosi po putnim nalozima | [P] |
| `dbo.vrednost_vozila` | `fleet/sync/external.py`, `fleet/sync/views.py` | Knjigovodstvena vrednost vozila | [P] |
| `dbo.lizing_kamate` | `fleet/sync/views.py` | Kamate po lizing ugovorima | [P] |
| `dbo.sif_pos_trenutno` | `fleet/sync/external.py` | Tekuća šifra posla po registarskoj oznaci | [P] |
| `dbo.v_organizationalunit` | `fleet/sync/external.py` | Šifarnik organizacionih jedinica | [P] |
| `dbo.kasko_rate` | `fleet/models.py` (`KaskoRate`), `report_queries.py` | Kasko rate po ugovorima | [P] |
| `dbo.fleet_magacin_rez` | `fleet/support/report_queries.py` | Rezervacije magacina | [P] |
| `dbo.fleet_tro_goriva_m` | `fleet/support/report_queries.py` | Mesečni trošak goriva | [P] |
| `dbo.fleet_tro_svi` | `fleet/support/report_queries.py` | Zbirni troškovi vozila | [P] |
| `dbo.fleet_tro_pracenje` | `fleet/support/report_queries.py` | Troškovi praćenja vozila (GPS) | [P] |
| `dbo.fleet_tro_taho` | `fleet/support/report_queries.py` | Troškovi tahografa | [P] |
| `dbo.fleet_tro_parking` | `fleet/support/report_queries.py` | Troškovi parkinga | [P] |
| `dbo.tro_zarade` | `fleet/support/report_queries.py` | Troškovi zarada | [P] |
| `dbo.fleet_dobavljaci` | `fleet/support/report_queries.py` | Pregled po dobavljačima | [P] |
| `dbo.servisi`, `dbo.v_servisi` | `fleet/management/commands/migrate_servisi.py` | Migraciona komanda (jednokratna) | [P] |

**Ukupno: 37 nasleđenih objekata baze + 1 uskladištena procedura.**

**Otvoreno pitanje [N]:** definicije ovih pogleda nisu u repozitorijumu (osim
`dokumentacija/sql/naplata_views_ims_erp.sql`). Da bi obračuni bili dokumentovani do kraja,
potrebno je preuzeti DDL svih navedenih pogleda. Dogovoreno: DDL stiže od ponedeljka;
do tada se koristi ono što je opisano u postojećoj dokumentaciji (vidi 3.2.2).

### 3.2.1. Povezani serveri (linked servers) — **ključni nalaz** [P]

Sistem **ne čita sve iz lokalne baze `IMS_ERP`**. Deo najvažnijih podataka dolazi sa
udaljenih servera preko SQL Server "linked server" mehanizma:

| Povezani server | Baza | Objekti koji se čitaju | Ko ih koristi |
|---|---|---|---|
| `PUTGEO-SERVER` | `bazaims` | `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | **Finansijska analitika** (`finansije/services/source.py`), Potraživanja (`services/source.py`) |
| `PUTGEO-SERVER` | `bazaldims` | `Zarada`, `PomLD`, `Radnik`, `element` | Finansije — zaposleni i zarade (`job_people.py`), tok gotovine (`cash_flow.py`) |
| `INFORMATIKA23` | `ID` | `Radnici`, `C_Prolasci_Radnika`, `C_Tasteri`, `c_parovi_radnika_detalji` | Kadrovi — evidencija prolazaka (`hr/services/attendance.py`) |
| `SERFIN` | `bazaldims` | `radnik` | Kadrovi — detalji parova prolazaka |

**Posledica [Z]:** dostupnost i brzina Finansija i Kadrova zavise od **tri udaljena servera**.
Zastoj ili nedostupnost povezanog servera direktno obara sinhronizaciju knjiženja i
prikaz radne liste. Ovo mora biti izričito u poglavlju o održavanju.

**Ispravka [P]:** `nalog_z` postoji na dva mesta — kao **izvor** na
`[PUTGEO-SERVER].[bazaims].dbo.nalog_z` i kao **lokalna kopija** `IMS_ERP.dbo.nalog_z`
koju puni procedura `sp_AzurirajNalogZ`. Finansijska analitika čita **udaljeni** `nalog_z`
u svoju tabelu `LedgerEntry`; Naplata čita poglede koji se oslanjaju na **udaljeni** izvor.
Pokretanje procedure samo osvežava lokalnu kopiju i **ne prebacuje** upite na nju.

### 3.2.2. Šta je poznato o `sp_AzurirajNalogZ` bez DDL-a

Izvor: `dokumentacija/naplata-lokalni-izvor-plan.md`, poglavlje 2 (definicija je ranije
pročitana, procedura nije izvršavana). **Status: [P] prema postojećoj dokumentaciji.**

| Osobina | Opis |
|---|---|
| Ulazni parametri | Nema ih |
| Izvor | `PUTGEO-SERVER.BazaIMS.dbo.nalog_z` → privremena tabela |
| Obuhvat godina | Do uključivo 30. aprila: prethodna i tekuća godina; posle toga samo tekuća |
| Obuhvat firmi | **Sve firme** — nema filtera `sif_pred=1` |
| Kontrole | Provera NULL vrednosti i duplikata ključa firma/godina/vrsta/broj/stavka |
| Upis | U transakciji: `UPDATE` postojećih + `INSERT` nedostajućih redova lokalnog `dbo.nalog_z` |
| **Ograničenje** | **Ne briše** lokalne redove koji su obrisani u izvoru — lokalna kopija nije garantovano identična izvoru |
| **Ograničenje brojača** | `BrojAzuriranihRedova` broji sve redove obuhvaćene `UPDATE`-om, ne samo stvarno promenjene |
| Povratna vrednost | `OdGodine`, `DoGodine`, `BrojAzuriranihRedova`, `BrojDodatihRedova` |
| Zaključavanje | `UPDLOCK/HOLDLOCK` u proceduri + `sp_getapplock` na nivou aplikacije |

**Lanac zavisnosti pogleda Naplate [P]** (iz istog dokumenta):
`dbo.baza` (firma 1, grupa 1, konta 20400/20500) i `dbo.v_if` (IF dokumenti od 2025. +
`UNION ALL tabela_if`) i `dbo.v_duplikati` (dokumenti u više godina + `duplikati18`)
→ **`dbo.dodela_baketa`** (saldo, broj dana, starosni razred).

**Poznata neusaglašenost [P]:** u pogledu `baza` granica je računata kao **119 dana od
početka godine** i poredi se sa `GETDATE()` koji uključuje vreme — to **nije isto**
što i "uključivo 30. april", posebno u prestupnoj godini, gde procedura koristi `DATEFROMPARTS`.

**Poznata neusaglašenost naziva [P]:** model `naplata/models.py` navodi tabelu
`dodela_bucketa`, dok stvarni upiti u `naplata/queries.py` koriste `dodela_baketa`.

### 3.3. Django modeli po aplikacijama (pregled)

| Aplikacija | Broj modela | Glavni modeli |
|---|---|---|
| `core` (tabele pod `app_label="fleet"`) | 7 | `CustomUser`, `Role`, `PermissionCode`, `RolePermission`, `OrganizationalUnit`, `ActivityLog`, `TaskHistory` |
| `fleet` | 23 | `Vehicle`, `TrafficCard`, `JobCode`, `Lease`, `VehicleHolding`, `Policy`, `Insurance`, `DraftInsurance`, `FuelConsumption`, `TransactionNIS`, `TransactionOMV`, `Service`, `ServiceTransaction`, `DraftServiceTransaction`, `Requisition`, `Kvar`, `KvarPart`, `PutniNalog`, `VehicleTravelOrder`, `Incident`, `ProcurementRequest`, `KontaVozila`, `KaskoRate` |
| `hr` (tabele delom pod `app_label="fleet"`) | 16 | `Employee`, `EmployeeCVItem`, `WorkTimeSheet`, `WorkTimeSheetLine`, `WorkTimeCategory`, `WorkTimeElement`, `RecipientType`, `AnnualLeaveAllowance`, `AnnualLeaveDecision`, `SickLeave`, `SickLeaveImport`, `EvaluationGroup`, `EvaluationCriterion`, `EvaluationScale`, `EmployeeEvaluation`, `EvaluationApproval` |
| `finansije` | 4 | `FinanceJob`, `LedgerEntry`, `SyncRun`, `NalogZRefreshRun` |
| `nabavka` | 13 | `ProcurementCase`, `ProcurementItem`, `ProcurementInvoice`, `EufItemSnapshot`, `UfInvoiceSnapshot`, `GoodsSnapshot`, `PurchaseOrder`, `PublicProcurementPlanVersion`, `PublicProcurementPlanItem` + 4 veze |
| `naplata` | 13 | 10 nasleđenih (`managed=False`) + `AvansKlijent`, `Postupak`, `PromenaPostupka` |
| `potrazivanja` | 22 | `FinancePartnerIdentity`, `InvoiceDocument`, `ReceivablePosting`, `BalanceSnapshot`, `ReceivablePosition`, `AgingRule`, `CollectionContact`, `CollectionActivity`, `CollectionNotice`, `CollectionLegalCase` + sinhronizacija i revizija |
| `ugovori` | 8 | `Partner`, `ContractType`, `BusinessRequest`, `Offer`, `Contract`, `ContractDocument`, `ContractParty`, `ContractGuarantee`, `ContractMenicaLink` |
| `menice` | 2 | `Menica`, `UlaznaMenica` |
| `mobilni` | 6 | `MobilePackage`, `MobileUser`, `MobileAssignment`, `MobileUsage`, `MobileParkingExemption`, `MobileImportLog` |
| `isplate` | 0 | Bez modela — samo servisi za generisanje datoteka |

**Nalaz za dokumentovanje [P]:** modeli iz `core/models.py` i `hr/models.py` imaju
`app_label = "fleet"`, pa im tabele fizički pripadaju aplikaciji `fleet`
(npr. `fleet_employee`, `fleet_activity_log`, `fleet_task_history`). To je čest izvor
zabune i mora biti izričito objašnjeno u dokumentaciji baze.

---

## 4. Moduli — pregled

| # | Modul (URL) | Poslovni naziv | Primarni korisnici (preliminarno) | Ekrana | Status razvoja |
|---|---|---|---|---|---|
| 1 | `/` (fleet) | **Vozni park / Flota** | Služba voznog parka, garaža, rukovodioci | 115 | U produkciji |
| 2 | `/hr/` | **Kadrovi** | Kadrovska služba, rukovodioci, svi zaposleni (radna lista) | 25 | U produkciji |
| 3 | `/finansije/` | **Finansijska analitika** | Finansije, uprava, rukovodioci centara | 16 | U produkciji |
| 4 | `/nabavka/` | **Nabavka** | Služba nabavke, garaža, podnosioci zahteva | 24 | U produkciji |
| 5 | `/naplata/` | **Naplata (postojeća)** | Služba naplate, pravna služba | 27 | U produkciji |
| 6 | `/potrazivanja/` | **Potraživanja (nova Naplata)** | Služba naplate | 10 | Paralelni rad / prelazak |
| 7 | `/ugovori/` | **Ugovori i partneri** | Pravna služba, sekretarijat, komercijala | 20 | U produkciji |
| 8 | `/menice/` | **Menice** | Finansije, pravna služba | 6 | U produkciji |
| 9 | `/mobilni/` | **Mobilna telefonija** | Administracija, obračun zarada | 16 | U produkciji |
| 10 | `/isplate/` | **Isplate / virmani** | Blagajna | 2 | U produkciji |
| 11 | `/administracija/` (u fleet) | **Administracija** | Administrator sistema | — | U produkciji |

**Napomena [P]:** aplikacija `fleet` je istovremeno i "korenska" aplikacija — njen `urls.py`
drži i prijavu, kontrolnu tablu, korisnike, log rada i istoriju taskova.
Aplikacija `core` nema svoje ekrane osim prebacivanja između modula (`switch-app`).

### 4.1. Bočni meniji (podela na module u interfejsu) [P]

Prebacivanje između modula ide preko sesije (`current_app`) i mapira se na 12 bočnih menija:
`fleet`, `naplata`, `potrazivanja`, `isplate`, `pravna`, `kadrovi`, `administracija`,
`menice`, `ugovori`, `nabavka`, `mobilni`, `finansije`.
Napomena: **`pravna` i `kadrovi` su posebni meniji, ali nisu posebne Django aplikacije** —
`pravna` se oslanja na `naplata/views_pravna.py` i `ugovori`, a `kadrovi` na `hr`. [Z]

---

## 5. Preliminarna arhitektura

### 5.1. Slojevi

```
   KORISNIK (pregledač)
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│  Django templates (280 ekrana) + DataTables + Select2      │
└────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│  VIEWS  — CBV i FBV po modulima                            │
│  Kontrola pristupa: RolePermissionRequiredMixin            │
│                     RoleRequiredMixin                      │
│                     role_permission_required (dekorator)   │
└────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│  SERVISI I OBRAČUNI                                        │
│  finansije/services/  fleet/support/  fleet/services/      │
│  hr/services/  potrazivanja/services/  nabavka/services/   │
│  mobilni/withholdings.py  isplate/services/                │
│  naplata/queries.py  ugovori/services.py  menice/services  │
└────────────────────────────────────────────────────────────┘
        │
        ├──────────────► Django ORM ──────► SQL Server  IMS_ERP  (alias: default)
        │
        └──────────────► Sirovi SQL ──────► SQL Server  IMS_ERP  (alias: server_db)
                                                  │
                                                  ├── dbo.* pogledi nasleđenog ERP-a
                                                  ├── dbo.sp_AzurirajNalogZ (procedura)
                                                  └── povezani server INFORMATIKA23.ID
                                                      (evidencija prolazaka)
```

### 5.2. Tok podataka iz spoljnih izvora

```
  NIS portal (cards.nis.rs) ──┐
  OMV Fleet (fleet.omv.com) ──┤ Selenium (Chrome) → CSV/Excel → TransactionNIS / TransactionOMV
                              │                                  → FuelConsumption
  NBS registar menica ────────┤ requests + BeautifulSoup → Menica
  APR OpenAPI ────────────────┤ requests (JSON) → Partner (provera statusa)
  RFZO Excel izvoz ───────────┤ openpyxl → SickLeave
  Excel plan javnih nabavki ──┤ openpyxl → PublicProcurementPlanVersion / Item
  Excel mobilni (MTS) ────────┘ openpyxl → MobilePackage / User / Assignment / Usage

  Nasleđeni ERP (dbo.* pogledi) → Celery zadaci → Django tabele (snapshot / draft / final)
```

### 5.3. Obrazac "Draft → Final" [P]

Na više mesta sistem koristi isti obrazac: podatak se prvo povuče u **nedovršenu (draft)**
tabelu, korisnik ga dopuni (najčešće poveže sa vozilom), pa se prebaci u **konačnu** tabelu:

| Draft tabela | Konačna tabela | Ekran za dopunu |
|---|---|---|
| `DraftInsurance` | `Insurance` | `/insurance/drafts/` |
| `DraftServiceTransaction` | `ServiceTransaction` | `/servisi/nedovrseno/` |

Sličan obrazac postoji i kod `Policy` i `Requisition` kroz ekrane "nedovršeno"
(`policy_fixing_list`, `requisition_fixing_list`). [P]

---

## 6. Pozadinski poslovi (Celery)

### 6.1. Raspored [P] — izvor: `core/management/commands/sync_celery_periodic_tasks.py`

| Vreme | Naziv posla | Task | Red |
|---|---|---|---|
| 01:00 | Administracija — sinhronizacija dozvola | `core.tasks.sync_permission_codes_task` | sync |
| 01:10 | Kadrovi — sinhronizacija zaposlenih | `fleet.tasks.sync_hr_employees_task` | sync |
| 01:20 | Flota — provera otpisa vozila | `fleet.tasks.proveri_otpis` | sync |
| 01:30 | Flota — sinhronizacija šifara poslova i OJ | `fleet.tasks.fetch_job_codes` | sync |
| 01:45 | Flota — sinhronizacija trebovanja | `fleet.tasks.fetch_requisition_data_task` | sync |
| 02:00 | Flota — sinhronizacija polisa | `fleet.tasks.fetch_policy_data_task` | sync |
| 02:20 | Nabavka — EUF fakture | `nabavka.tasks.sync_euf_invoices_task` | sync |
| 02:45 | Nabavka — UF stavke | `nabavka.tasks.sync_uf_items_task` | sync |
| 03:15 | Flota — sinhronizacija servisa | `fleet.tasks.fetch_service_data_task` | sync |
| 03:35 | Flota — DDOR osiguranja | `fleet.tasks.fetch_ddor_data_task` | sync |
| 03:50 | Finansije — sve godine od 2025 | `finansije.tasks.sync_all_years` | sync |
| 04:20 | Gorivo — NIS transakcije | `fleet.tasks.run_nis_command` | **selenium** |
| 05:10 | Gorivo — OMV putnička vozila | `fleet.tasks.run_omv_putnicka_command` | **selenium** |
| 06:10 | Gorivo — OMV teretna vozila | `fleet.tasks.run_omv_teretna_command` | **selenium** |
| 07:10 | Nabavka — roba | `nabavka.tasks.sync_goods_task` | sync |
| 10:00 i 11:00 | Finansije — osvežavanje `nalog_z` | `finansije.tasks.refresh_nalog_z_task` | sync |
| 12:30 | Putni nalozi — ažuriranje isplaćenog iznosa | `fleet.tasks.sync_putni_nalozi_isplaceno_task` | sync |
| svaki sat u :20 | Finansije — tekuća godina | `finansije.tasks.sync_current_year` | sync |

**Ukupno 18 zakazanih poslova.** Vremenska zona za `nalog_z` je izričito
`Europe/Belgrade`, za ostale je `CELERY_TIMEZONE = CET`. [P]

### 6.2. Mehanizmi zaštite [P]

| Mehanizam | Opis |
|---|---|
| Jedinstveno izvršavanje | Redis zaključavanje (`ims_erp:task-lock:<task>`); ako posao već radi, novi se preskače |
| Trajanje zaključavanja | 4 sata za Selenium poslove, 90 minuta za sinhronizacije, 60 minuta za lakše poslove |
| "Fail-open" | Ako Redis nije dostupan, posao se ipak izvršava (bez zaključavanja) |
| Razdvojeni redovi | `selenium` (teški poslovi) i `sync` (laki) da se ne blokiraju međusobno |
| Istorija | `TaskHistory` (tabela `fleet_task_history`) — status, trajanje, rezultat, greška |

---

## 7. Autentifikacija, uloge i dozvole

### 7.1. Model pristupa [P]

Sistem **ne koristi** standardne Django dozvole za poslovnu logiku. Umesto toga:

```
CustomUser ──(M2M)──► Role ──(RolePermission)──► PermissionCode
```

- `PermissionCode.code` = **naziv URL rute** (npr. `vehicle_list`, `nabavka:case_detail`).
- Provera: korisnik ima pristup ako ijedna njegova **aktivna** uloga sadrži kod koji odgovara
  imenu rute koja se otvara (`request.resolver_match.view_name`).
- `is_superuser` zaobilazi sve provere.
- Kodovi dozvola se **automatski generišu iz `urls.py`** komandom `sync_permission_codes`
  i noćnim zadatkom u 01:00.

**Posledica [Z]:** dodavanje nove rute automatski stvara novu dozvolu; uloga "Uprava"
automatski dobija **sve** dozvole pri svakoj sinhronizaciji.

### 7.2. Predefinisane uloge [P]

| Slug | Naziv | Obuhvat |
|---|---|---|
| `uprava` | Uprava | Sve dozvole u sistemu (automatski) |
| `nabavka` | Nabavka | Sve funkcije modula Nabavka |
| `menice` | Menice | Samo modul Menice |
| `blagajna` | Blagajna | Sve funkcije modula Isplate |
| `pravna` | Pravna služba | Funkcije pravne službe i modul Ugovori |
| `mobilni` | Mobilni | Sve funkcije modula Mobilni telefoni |
| `finansije` | Finansijska analitika | `dashboard`, `ledger`, `export` |
| `pregled-naplate` | Pregled naplate | Pregledi i Excel izvozi u Naplati, bez izmena |
| `zahtev` | Zahtev | Kreiranje zahteva nabavke sa stavkama i štampa |
| `sekretarijat` | Sekretarijat | Zaposleni i putni nalozi |
| `zaposleni` | Zaposleni | Svoj profil i otvaranje zaduženja vozila |

### 7.3. Dodatna ograničenja vidljivosti [P]

Pored uloga, postoje i ograničenja po **organizacionoj pripadnosti**:

- `CustomUser.allowed_centers` (M2M ka `OrganizationalUnit`)
- `CustomUser.allowed_center_codes` (tekstualna lista šifara centara, odvojena zarezima)
- Posebni kodovi "vidi sve": `finansije:view_all`, `hr:evaluation_view_all`

**Otvoreno pitanje [N]:** postoje dva paralelna mehanizma za centre (`allowed_centers` i
`allowed_center_codes`). Potrebno je potvrditi koji je merodavan u kom modulu. Vidi **Q5**.

### 7.4. Evidencija rada [P]

`ActivityLog` (tabela `fleet_activity_log`) beleži preko `core.middleware.ActivityLogMiddleware`:
prijave, odjave, neuspešne prijave, i pojedinačne akcije (korisnik, IP, putanja, metod,
status, model, ID zapisa, izmene u JSON polju). Ekran: `/administracija/activity-log/`.

---

## 8. Integracije sa spoljnim sistemima

| # | Sistem | Način pristupa | Šta se preuzima | Učestalost | Status |
|---|---|---|---|---|---|
| 1 | **NIS** — `https://cards.nis.rs` | Selenium (Chrome), prijava i preuzimanje datoteke | Transakcije goriva po karticama | Dnevno 04:20 | [P] |
| 2 | **OMV Fleet** — `https://fleet.omv.com/FleetServicesProduction` | Selenium (Chrome) | Transakcije goriva (putnička i teretna, odvojeno) | Dnevno 05:10 i 06:10 | [P] |
| 3 | **NBS registar menica** — `https://webappcenter.nbs.rs/PnWebApp` | `requests` + `BeautifulSoup` | Podaci o menicama i avalistima po dužniku | Na zahtev korisnika | [P] |
| 4 | **APR OpenAPI** — `https://openapi.apr.gov.rs/api/opendata/companies` | `requests` (JSON) | Status privrednog subjekta po matičnom broju | Na zahtev (paketna obrada) | [P] |
| 5 | **Sistem kontrole pristupa** — povezani server `INFORMATIKA23.ID` | SQL preko povezanog servera | Prolasci radnika (ulaz/izlaz/službeni izlaz) | Pri otvaranju radne liste | [P] |
| 5a | **Knjigovodstvo** — povezani server `PUTGEO-SERVER.bazaims` | SQL preko povezanog servera | `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | Svakog sata u :20 i dnevno 03:50 | [P] |
| 5b | **Obračun zarada** — povezani server `PUTGEO-SERVER.bazaldims` | SQL preko povezanog servera | `Zarada`, `PomLD`, `Radnik`, `element` | Pri otvaranju detalja šifre posla | [P] |
| 5c | **Kadrovska** — povezani server `SERFIN.bazaldims` | SQL preko povezanog servera | `radnik` (detalji parova prolazaka) | Pri otvaranju radne liste | [P] |
| 6 | **RFZO** | Ručni uvoz Excel datoteke | Bolovanja | Mesečno, ručno | [P] |
| 7 | **MTS / mobilni operater** | Ručni uvoz Excel datoteke | Paketi, korisnici, dodele, potrošnja | Mesečno, ručno | [Z] |
| 8 | **Interni portal** — `https://control.ims.rs:4081` | Selenium | Prijava na mrežu radi pristupa internetu | Pre svakog Selenium posla | [P] |
| 9 | **Banka (elektronsko bankarstvo)** | Izvoz datoteke fiksne širine (180 znakova, cp1250) | Virmani za neoporeziva primanja | Na zahtev | [P] |

**Napomena o pristupnim podacima [N]:** pristupni podaci za NIS i OMV portale nalaze se
u kodu ili u okruženju — ovo treba proveriti i navesti u dokumentaciji održavanja
(bez navođenja samih lozinki). Vidi **Q7**.

---

## 9. Registar analiza, obračuna i izveštaja

Ovo je **glavni predmet FAZE 3**. Ispod je popis svega što je pronađeno, grupisano po modulu.
Kolona "Već dokumentovano" pokazuje šta je pokriveno postojećim dokumentom
`finansije-metodologija-obracuna.md` (20 poglavlja).

### 9.1. Finansijska analitika (`finansije/`) — 18 obračuna

| # | Analiza / obračun | Implementacija | Već dok. |
|---|---|---|---|
| F-01 | Prihodi po šifri posla | `services/reports.py: summary, grouped_report` | Da |
| F-02 | Rashodi po šifri posla | `services/reports.py` | Da |
| F-03 | Rezultat bez zajedničkih troškova | `services/reports.py: expressions` | Da |
| F-04 | Zajednički troškovi — pravila raspodele | `services/shared_costs.py: allocation_rules` | Da |
| F-05 | Zajednički troškovi — koeficijent posla i raspodela | `services/shared_costs.py: allocate, shared_cost` | Da |
| F-06 | Rezultat posle raspodele ZT | `services/job_overview.py: enrich_jobs` | Da |
| F-07 | Priliv gotovine | `services/cash_flow.py: calculate` | Da |
| F-08 | Odliv gotovine | `services/cash_flow.py: calculate` | Da |
| F-09 | Neto gotovina | `services/cash_flow.py: cash_flow` | Da |
| F-10 | Zamena PDV-a u toku gotovine | `services/cash_flow.py` (period PDV-a) | Da |
| F-11 | Zarade u obračunu toka gotovine | `services/cash_flow.py` (preko `dbo.element`) | Da |
| F-12 | Refundacije | `services/cash_flow.py` | Da |
| F-13 | Grafikoni, učešća i rangiranje | `services/charts.py: overview_data` | Da |
| F-14 | Mesečni rashodi (kartica posla) | `services/job_card.py: monthly_expenses` | Da |
| F-15 | Mesečne fakture IF / interne ON | `services/job_card.py: monthly_invoices` | Da |
| F-16 | Vozila i zaduženja na šifri posla | `services/job_card.py: assigned_vehicles, vehicle_custody` | Da |
| F-17 | Zaposleni i zarade po šifri posla | `services/job_people.py: payroll_employees` | Da |
| F-18 | Osvežavanje naloga Z (procedura) | `services/nalog_z.py: refresh_nalog_z` | Da |

### 9.2. Vozni park (`fleet/`) — 24 obračuna i izveštaja

| # | Analiza / obračun | Implementacija | Već dok. |
|---|---|---|---|
| V-01 | Prosečna potrošnja goriva (period) | `support/fuel.py: calculate_average_fuel_consumption` | Ne |
| V-02 | Prosečna potrošnja goriva (ceo vek vozila) | `support/fuel.py: calculate_average_fuel_consumption_ever` | Ne |
| V-03 | Neto iznos goriva iz bruto i PDV-a | `support/fuel.py: net_amount_from_gross_and_vat` | Ne |
| V-04 | Iznosi OMV (bruto/neto) | `support/fuel.py: omv_charged_gross_net_amounts` | Ne |
| V-05 | Iznosi NIS (bruto/neto) | `support/fuel.py: nis_charged_gross_net_amounts` | Ne |
| V-06 | Uklanjanje duplih OMV transakcija i "odjeka" računa | `support/fuel.py` + `support/fuel_cleanup.py` | Ne |
| V-07 | Trošak po kilometru po vozilu | `support/dashboard.py: vehicle_cost_per_km_rows` | Ne |
| V-08 | Procena pređene kilometraže u periodu | `support/dashboard.py: _estimate_period_mileage` | Ne |
| V-09 | Analiza troška po km za više perioda | `support/dashboard.py: cost_per_km_period_analysis` | Ne |
| V-10 | Neto trošak održavanja | `support/analytics.py: net_maintenance_cost` | Ne |
| V-11 | Pragovi fiksnog troška po km (po masi vozila) | `support/analytics.py: fixed_cost_per_km_ranges, fixed_cost_per_km_threshold` | Ne |
| V-12 | Status "crvena zona" vozila | `support/analytics.py: is_red_zone, cost_per_km_status` | Ne |
| V-13 | Kilometraža vozila — posmatrana vremenska linija | `support/vehicle_mileage.py: observed_timeline, vehicle_mileage` | Ne |
| V-14 | Održavanje vozila i servisni interval | `support/vehicle_maintenance.py: vehicle_maintenance` | Ne |
| V-15 | Analitika na detalju vozila | `support/vehicle_detail.py: recorded_analytics` | Ne |
| V-16 | Presek stanja flote | `support/fleet_snapshot.py: fleet_snapshot` | Ne |
| V-17 | Mesečni troškovi polisa | `support/policy_queries.py: policies_monthly_costs_qs` | Ne |
| V-18 | Polise pred istekom / neobnovljene | `support/policy_queries.py: expiring_policy_qs, expired_unrenewed_policy_qs` | Ne |
| V-19 | Mesečni troškovi lizinga | `support/lease_queries.py: lease_monthly_costs_rows` | Ne |
| V-20 | Mesečni troškovi servisa | `support/service_queries.py: service_monthly_costs_rows` | Ne |
| V-21 | Gorivo po šifri posla (OMV/NIS × putnička/teretna) | `support/fuel_reports.py: fuel_job_code_report` | Ne |
| V-22 | Izveštaji za upravu (kasko, osiguranje IMS, gorivo, delovi) | `support/management_reports.py` | Ne |
| V-23 | Obračun goriva na putnom nalogu vozila | `views/vehicle_travel_orders.py: VehicleTravelOrderFuelReportView` | Ne |
| V-24 | Statistika po centrima | `views/center_statistics.py: center_statistics` | Ne |

**Dodatno: 11 izveštaja nad nasleđenim pogledima** (`support/report_queries.py`):
kasko rate, magacin, otpis, mesečni trošak goriva, svi troškovi, praćenje vozila,
tahograf, zarade, parking, po dobavljačima. [P]

### 9.3. Kadrovi (`hr/`) — 9 obračuna

| # | Analiza / obračun | Implementacija | Već dok. |
|---|---|---|---|
| K-01 | Dnevni sati rada iz evidencije prolazaka | `services/attendance.py: calculate_daily_hours_from_clock_events` | Delimično (Word) |
| K-02 | Mesečni pregled dnevnih sati | `services/attendance.py: get_month_daily_work_hours` | Delimično |
| K-03 | Problemi u parovima prolazaka (kontrola) | `services/attendance.py: ClockPairIssue` | Ne |
| K-04 | Ukupni sati po redu radne liste | `hr/models.py: WorkTimeSheetLine.total_hours` | Ne |
| K-05 | Ukupni sati radne liste | `hr/models.py: WorkTimeSheet.total_hours` | Ne |
| K-06 | Godišnji odmori — dodela i rešenja, normalizacija izvora | `services/annual_leave.py: normalize_source, sync_annual_leave` | Delimično (Word) |
| K-07 | Bolovanja — uvoz RFZO i povezivanje po JMBG | `services/sick_leave.py: import_rfzo_workbook, sick_leaves_by_day` | Delimično (Word) |
| K-08 | **Ocenjivanje zaposlenih — stimulacija i lični koeficijent** | `services/evaluations.py: build_snapshot, save_evaluation` | Delimično (Word) |
| K-09 | Tok saglasnosti na ocenu (3 nivoa) | `services/evaluations.py: approval_state, approve_evaluation` | Delimično |

### 9.4. Mobilna telefonija (`mobilni/`) — 4 obračuna

| # | Analiza / obračun | Implementacija | Već dok. |
|---|---|---|---|
| M-01 | **Obustava po zaposlenom** (osnovica PDV − neto paket + parking + NZRD) | `withholdings.py: calculate_withholding` | Ne |
| M-02 | Izuzeci od parkinga | `withholdings.py: is_parking_exempt` | Ne |
| M-03 | Razvrstavanje: zaposleni / bivši zaposleni / nezaposleni | `withholdings.py: get_withholding_rows` | Ne |
| M-04 | Povezivanje broja telefona sa zaposlenim | `models.py: MobileAssignment.linked_employee` | Ne |

**Napomena [P]:** u obračunu obustava postoji **jedan broj telefona sa posebnim tretmanom**
(`SPECIAL_PHONE_NUMBER = "381637781481"`) za koji se ne odbija iznos paketa.
Ovo je "tvrdo" upisano u kod i mora biti objašnjeno. Vidi **Q8**.

### 9.5. Naplata (`naplata/`) — **izvan obuhvata dokumentacije**

Odlukom naručioca (18.09.2026.) Naplata je nasleđena aplikacija koja se gasi i
**ne dokumentuje se**. Njenih 7 analiza (dugovanja po baketima, izveštaj po šiframa posla,
neodobrene IF, detalj partnera, avans klijenti, pravni postupci, Excel izvozi) zamenjuju
odgovarajuće funkcije modula Potraživanja.

Zadržava se samo zapis u `docs/10-poznati-problemi.md` i `docs/11-plan-razvoja.md`.

### 9.6. Potraživanja (`potrazivanja/`) — 6 analiza

| # | Analiza / obračun | Implementacija | Već dok. |
|---|---|---|---|
| PT-01 | Starosni razredi (aging) po pravilima | `models.py: AgingRule`, `services/sync.py: bucket` | Delimično |
| PT-02 | Saldo stavke (duguje − potražuje, zaokruženo na 2) | `models.py: ReceivablePosition` (kontrola u bazi) | Ne |
| PT-03 | Objavljivanje snimka stanja | `services/sync.py: publish_positions` | Delimično |
| PT-04 | Kontrolni zbirovi i provera izvora | `services/sync.py: validate_postings, compare_maps` | Ne |
| PT-05 | Saldo po šiframa posla | `services/reports.py: job_balances` | Ne |
| PT-06 | Normalizacija kontakata (razdvajanje višestrukih) | `services/contacts.py: parse_contact, normalize_contacts` | Ne |

> **Napomena o oznakama:** analize Potraživanja nose prefiks **PT-**, jer je prefiks
> **P-** rezervisan za registar problema u `docs/10-poznati-problemi.md`.

### 9.7. Nabavka (`nabavka/`) — 6 analiza

| # | Analiza / obračun | Implementacija | Već dok. |
|---|---|---|---|
| B-01 | Procenjena vrednost stavke i predmeta | `models.py: ProcurementItem.estimated_total` | Ne |
| B-02 | Grupisanje UF stavki u UF fakture | `services/source_snapshots.py: rebuild_uf_invoice_snapshots` | Ne |
| B-03 | Ključ EUF fakture (za povezivanje) | `services/euf.py: make_euf_key` | Delimično |
| B-04 | Razlike verzija plana javnih nabavki (dodato/izmenjeno/uklonjeno) | `services/public_procurements.py: import_public_procurement_plan` | Ne |
| B-05 | Provera šifre posla partnera | `views/reports.py: PartnerJobCodeCheckReportView` | Ne |
| B-06 | Alarmi nabavke | `views/alerts.py: AlertsView` | Ne |

### 9.8. Isplate (`isplate/`) — 3 obračuna

| # | Analiza / obračun | Implementacija | Već dok. |
|---|---|---|---|
| I-01 | **Generisanje datoteke virmana** (format 180 znakova, cp1250) | `services/virman.py: build_virman_file` | Ne |
| I-02 | Kontrole ispravnosti naloga pre virmana (račun 18 cifara, RSD, nije storniran) | `services/virman.py: validate_order_for_virman` | Ne |
| I-03 | Konverzija datoteka | `services/converters.py` | Ne |

### 9.9. Ugovori i menice — 4 analize

| # | Analiza / obračun | Implementacija | Već dok. |
|---|---|---|---|
| U-01 | Provera statusa partnera u APR-u | `apr_openapi.py: is_active_apr_status` | Ne |
| U-02 | Sinhronizacija partnera iz finansija | `services.py` (`dbo.partneri`) | Ne |
| U-03 | Preuzimanje menica iz registra NBS | `menice/scraper.py` | Ne |
| U-04 | Povezivanje menica i garancija sa ugovorima | `ugovori/models.py: ContractMenicaLink` | Ne |

### 9.10. Zbir

| Modul | Broj analiza/obračuna | Već dokumentovano | U obuhvatu |
|---|---|---|---|
| Finansije | 18 | 18 | Da |
| Vozni park | 24 (+11 izveštaja nad pogledima) | 0 | Da |
| Kadrovi | 9 | 5 (delimično, u Word dokumentima) | Da |
| Mobilni | 4 | 0 | Da |
| Potraživanja | 6 (+ pravna služba) | 3 (delimično) | Da |
| Nabavka | 6 | 1 (delimično) | Da |
| Isplate | 3 | 0 | Da |
| Ugovori i menice | 4 | 0 | Da |
| ~~Naplata~~ | ~~7~~ | — | **Ne** (nasleđeno) |
| **UKUPNO U OBUHVATU** | **74 (+11)** | **~24** | |

---

## 10. Izveštaji i izvozi (pregled)

| Vrsta | Broj | Primeri |
|---|---|---|
| Ekranski izveštaji (flota) | 20 | `/izvestaji/` — kasko, gorivo, magacin, otpis, parking, tahograf |
| Excel izvozi | 15+ | Lizing, dugovanja po baketima, opomene, ugovori, mobilni (4), nabavka EUF |
| CSV izvozi | 5 | Vozila, mesečni troškovi polisa i servisa, obustave mobilnih |
| Štampani obrasci | 10+ | Putni nalog, prilog za inostranstvo, prijava kvara, radni nalog, trebovanje, radna lista, ocena zaposlenog, zahtev nabavke |
| ZIP izvoz | 1 | Tenderska dokumentacija vozila |
| Bankarska datoteka | 1 | Virman (fiksna širina 180 znakova) |

---

## 11. Uvoz podataka

| Izvor | Format | Komanda / ekran | Status |
|---|---|---|---|
| NIS transakcije | Excel / CSV | `import_nis_excel`, `nis_excel_import` | [P] |
| OMV putnička i teretna | CSV | `import_omv_putnicka_csv`, `import_omv_teretna_csv` | [P] |
| RFZO bolovanja | Excel | `/hr/bolovanja/uvoz/`, `import_rfzo_sick_leave` | [P] |
| Plan javnih nabavki | Excel | `/nabavka/javne-nabavke/uvoz/` | [P] |
| Zahtevi garaže | Excel | `import_garage_requests_excel` | [P] |
| Ugovori | Excel | `import_contracts_excel` | [P] |
| Ulazne i izlazne menice | Excel | `import_ulazne_menice_excel`, `import_izlazne_menice_excel` | [P] |
| Pravna lica (naplata) | Excel | `import_pravna_excel` | [P] |
| Mobilni (paketi, korisnici, dodele, potrošnja) | Excel | `/mobilni/import/` | [P] |
| Šifarnik ocenjivanja | Excel | `import_evaluation_catalog` | [P] |
| Šifarnik elemenata radne liste | Excel | `import_work_time_catalog` | [P] |
| Konta vozila | — | `load_konta_vozila` | [P] |

**Ukupno 50 upravljačkih komandi (`management/commands`)** u svim aplikacijama. [P]

---

## 12. Predlog strukture dokumentacije

### 12.1. Predložena struktura fajlova

```
README.md                                  Kratak uvod, pokretanje, mapa dokumentacije
AGENTS.md                                  Uputstvo za AI agente i nove programere

dokumentacija/docs/
├── 01-pregled-sistema.md                  Šta je IMS ERP, ko ga koristi, šta radi
├── 02-arhitektura.md                      Slojevi, tok podataka, obrasci, konekcije
├── 03-moduli.md                           Sadržaj sa linkovima ka modulima
│   └── moduli/
│       ├── 03-01-flota.md
│       ├── 03-02-kadrovi.md
│       ├── 03-03-finansije.md
│       ├── 03-04-nabavka.md
│       ├── 03-05-potrazivanja.md
│       ├── 03-06-ugovori.md
│       ├── 03-07-menice.md
│       ├── 03-08-mobilni.md
│       ├── 03-09-isplate.md
│       └── 03-10-administracija.md
├── 04-baza-podataka.md                    Django tabele + nasleđeni pogledi + povezani serveri
├── 05-poslovni-procesi.md                 Procesi s kraja na kraj
├── 06-analize-i-obracuni.md               Sadržaj svih 74 obračuna s linkovima
│   └── obracuni/
│       ├── 06-01-finansije.md             (18 obračuna)
│       ├── 06-02-flota-gorivo.md          (6 obračuna)
│       ├── 06-03-flota-troskovi.md        (9 obračuna)
│       ├── 06-04-flota-ugovori-polise.md  (5 obračuna)
│       ├── 06-05-flota-izvestaji.md       (4 + 11 izveštaja)
│       ├── 06-06-kadrovi.md               (9 obračuna)
│       ├── 06-07-mobilni.md               (4 obračuna)
│       ├── 06-08-potrazivanja.md          (6 analiza + pravna služba)
│       ├── 06-09-nabavka.md               (6 analiza)
│       ├── 06-10-isplate.md               (3 obračuna)
│       └── 06-11-ugovori-i-menice.md      (4 analize)
├── 07-integracije.md                      Spoljni sistemi + 3 povezana servera
├── 08-instalacija-i-pokretanje.md         Okruženje, servisi, Celery, Redis
├── 09-odrzavanje.md                       Zakazani poslovi, dnevnici, česti problemi
├── 10-poznati-problemi.md                 Ograničenja i rizici (uklj. nasleđenu Naplatu)
├── 11-plan-razvoja.md                     Postojeći planovi (centralizacija, V2 dozvole)
├── 12-recnik-poslovnih-pojmova.md         Pojmovnik + mapiranje ekran ↔ kod ↔ baza
└── uprava/
    └── pregled-ims-erp-a.md               Kratak netehnički pregled za upravu
```

**Naplata nema svoje poglavlje** — pominje se samo u `10-poznati-problemi.md`
(nasleđeni sistem u gašenju) i `11-plan-razvoja.md` (plan prelaska na Potraživanja).

### 12.2. Odnos prema postojećoj dokumentaciji

Postojeći direktorijum `dokumentacija/` sadrži **vredan materijal** koji **ne treba brisati**:

| Postojeći dokument | Predlog postupanja |
|---|---|
| `finansije-metodologija-obracuna.md` (44 KB, 20 poglavlja) | **Preneti u `docs/obracuni/06-01-finansije.md`** uz usklađivanje strukture; original zadržati |
| `Analiza aplikacije i procedure rada - IMS flota.md` (58 KB) | Izvor za `docs/moduli/03-01-flota.md` |
| `nabavka-modeli-zahtevi-euf-uf-roba.md` | Izvor za `docs/moduli/03-04-nabavka.md` |
| `naplata-nova-aplikacija-plan.md`, `potrazivanja-*.md` | Izvor za `docs/moduli/03-06-potrazivanja.md` i `11-plan-razvoja.md` |
| `plan-centralizacije-organizacije.md`, `plan-organizacije-i-dozvola-v2.md` | Izvor za `docs/11-plan-razvoja.md` |
| `celery-*.md` | Izvor za `docs/09-odrzavanje.md` |
| `detalj-vozila.md`, `kontrolna-tabla.md`, `unos-vozila-carobnjak.md` | Uključiti u `docs/moduli/03-01-flota.md`. Nekorišćeni snimci ekrana uklonjeni 18.09.2026.; ostala su tri koja koristi `unos-vozila-carobnjak.md` |
| Word dokumenti (Kadrovi, Presek stanja, Garaža) | Bili izvor za module Kadrovi i Flota. **Uklonjeni iz repozitorijuma 18.09.2026.** pošto je sadržaj prešao u `docs/`; dostupni kroz git istoriju |
| `procena_*.md`, `opravdanost_*.md` | Ostaju kao arhiva (poslovne procene, nisu tehnička dokumentacija) |

**Predlog [N]:** da li novu dokumentaciju smestiti u novi direktorijum `docs/`
(kako je traženo u zadatku) ili unutar postojećeg `dokumentacija/`? Vidi **Q9**.

---

## 13. Predlog redosleda rada

Predlažem rad po modulima, od onih sa najviše poslovnog uticaja ka onima sa manje:

| Korak | Sadržaj | Procena obima |
|---|---|---|
| **1** | `AGENTS.md`, `README.md`, `01-pregled-sistema.md`, `02-arhitektura.md` | Temelj — bez njega ostalo nema kontekst |
| **2** | `04-baza-podataka.md` — sve tabele i svi nasleđeni pogledi | Zahteva DDL pogleda (**Q1**) |
| **3** | **Flota** — modul + 24 obračuna + 11 izveštaja | Najveći modul, najviše nedokumentovanog |
| **4** | **Finansije** — modul + preuzimanje postojeće metodologije | Najbrže, jer je već dokumentovano |
| **5** | **Nabavka** + **Ugovori** + **Menice** | Povezan lanac: zahtev → ugovor → faktura → menica |
| **6** | **Naplata** + **Potraživanja** | Dva paralelna sistema — bitno za špediciju i računovodstvo |
| **7** | **Kadrovi** + **Mobilni** + **Isplate** | Obračuni koji idu u zarade |
| **8** | `05-poslovni-procesi.md` — procesi s kraja na kraj | Radi se posle modula |
| **9** | `07`–`12` (integracije, instalacija, održavanje, problemi, plan, rečnik) | Zaokruženje |
| **10** | `docs/uprava/pregled-ims-erp-a.md` | Radi se poslednji, kao sažetak svega |
| **11** | Objedinjeni glavni dokument za Word/PDF | Po potvrdi svih delova |

### 13.1. Uočeni rizici i nalazi tokom inventara

Ovo **nisu** predlozi za izmenu koda (kod se ne menja), već nalazi koje treba
uneti u `docs/10-poznati-problemi.md`:

| # | Nalaz | Ozbiljnost | Status |
|---|---|---|---|
| R-1 | Pristupni podaci baze upisani u `development.py` i `production.py` i nalaze se u repozitorijumu | **Visoka** | [P] |
| R-2 | `SECRET_KEY` upisan u `base.py` u repozitorijumu | **Visoka** | [P] |
| R-3 | `DEBUG = True` u `base.py`; `production.py` ga ne isključuje | **Visoka** | [P] |
| R-4 | `db.sqlite3` (6,7 MB) nalazi se u repozitorijumu iako je u `.gitignore` | Srednja | [P] |
| R-5 | Dnevnici rada od ~18 MB u korenu repozitorijuma | Niska | [P] |
| R-6 | Poseban broj telefona "tvrdo" upisan u obračun obustava | Srednja | [P] |
| R-7 | Pristupni podaci banke (račun platioca) upisani u `isplate/services/virman.py` | Niska | [P] |
| R-8 | Dva paralelna mehanizma za ograničavanje po centrima | Srednja | [P] |
| R-9 | Naplata i Potraživanja rade paralelno nad istim poslovnim sadržajem | Srednja | [P] |
| R-10 | `djangorestframework` i `psycopg2` u zavisnostima, a ne koriste se | Niska | [Z] |
| R-11 | Privremene datoteke (`tmp*.csv`, `~$*.docx`) u korenu repozitorijuma | Niska | [P] |

---

## 14. Odluke naručioca i preostala pitanja

### 14.0. Potvrđene odluke (18.09.2026.)

| # | Pitanje | **Odluka** |
|---|---|---|
| Q1 | DDL nasleđenih pogleda i procedure | **DDL stiže od ponedeljka.** Do tada se koristi ono što je već opisano u postojećoj dokumentaciji (`naplata-lokalni-izvor-plan.md`, `finansije/README.md`, `finansije-metodologija-obracuna.md`). Sve što nije potvrđeno kodom ili tim dokumentima ostaje označeno kao **[N]**. |
| Q4 | Naplata ili Potraživanja | **Naplata je nasleđena (legacy) aplikacija — radi sporo i neefikasno i NE dokumentuje se.** Potraživanja je u potpunosti zamenjuju i koriste isključivo Django tabele uz sinhronizaciju. Dokumentuje se samo Potraživanja. |
| Q9 | Lokacija dokumentacije | **`dokumentacija/docs/`** |
| Q11 | Redosled rada | **Kako je predloženo u poglavlju 13.** |

### 14.0.1. Posledice odluke o Naplati na obim posla

| Stavka | Pre odluke | Posle odluke |
|---|---|---|
| Analiza za dokumentovanje | 81 | **74** (−7 iz Naplate) |
| Modula za dokumentovanje | 11 | **10** |
| Stranica u obuhvatu | 222 | **~195** (−27) |

**Napomena [Z]:** modul `naplata` ostaje u radu i u kodu — samo se **ne dokumentuje**
kao poslovni modul. U `docs/10-poznati-problemi.md` i `docs/11-plan-razvoja.md` biće
zabeležen kao nasleđeni sistem u gašenju, sa uputom da se novi rad ne oslanja na njega.

**Otvoreno [N]:** pravna služba (`naplata/views_pravna.py`, tabele `postupak` i
`promena_postupka`) tehnički pripada aplikaciji `naplata`, ali je u Potraživanjima
već modelovana kao `CollectionLegalCase` i `CollectionLegalEvent`. Pretpostavljam da
i ona prelazi u Potraživanja i dokumentujem je tamo. Vidi **Q12**.

---

### 14.1. Preostala pitanja

### Q1 — Definicije SQL pogleda ✔ rešeno za sada
DDL stiže od ponedeljka. **Prioritet kada stigne** (poredano po uticaju na dokumentaciju):

1. `dbo.fleet_tro_svi`, `fleet_tro_goriva_m`, `fleet_tro_pracenje`, `fleet_tro_taho`,
   `fleet_tro_parking`, `tro_zarade`, `fleet_dobavljaci`, `fleet_magacin_rez`, `kasko_rate`
   — 9 izveštaja Flote koji se prikazuju upravi, a formula im je **potpuno u bazi**.
2. `dbo.fleet_servisi`, `fleet_trebovanja`, `fleet_potrazivanje_ddor`, `fleet_zatvoren_putni`,
   `vrednost_vozila`, `lizing_kamate`, `sif_pos_trenutno`, `v_organizationalunit`, `fleet_otpis`
   — izvori sinhronizacija Flote.
3. `dbo.nbv_preuzete_EUF`, `nbv_EUF_stavke`, `nbv_roba`, `nbv_sif_pos_par` — Nabavka.
4. `dbo.hr_employee` — Kadrovi.
5. `dbo.posao` (na `PUTGEO-SERVER.bazaims`) — Potraživanja i Finansije.

Pogledi Naplate (`baza`, `dodela_baketa`, `v_if`, `v_duplikati`, `v_neodobreneIF`, `v_tuzeni`,
`ispravke`) **nisu više prioritet** jer se Naplata ne dokumentuje.

### Q2 — Poslovni vlasnici modula
Za svaki modul treba navesti **ko ga koristi** i **ko je odgovoran**. Iz koda mogu da zaključim
uloge (`sekretarijat`, `blagajna`, `pravna`...), ali ne i stvarne službe i osobe.
**Pitanje:** možete li potvrditi tabelu "modul → služba → odgovorno lice"?

### Q3 — Upotreba rezultata u špediciji i računovodstvu
Zadatak izričito traži da se opiše koju vrednost špedicija/računovodstvo preuzima, sa kog
ekrana, za koji dokument i koja konta se koriste. **U kodu nema evidencije o knjiženju** —
sistem uglavnom **čita** knjiženja, ne stvara ih (izuzeci: virman datoteka i obustave mobilnih).
**Pitanje:** da li postoji pisana procedura kako se ovi rezultati prenose u knjigovodstvo?
Bez toga ću taj deo označiti kao nepotvrđen i neću navoditi konta.

### Q4 — Naplata ili Potraživanja ✔ rešeno
Naplata je nasleđena aplikacija i **ne dokumentuje se**. Dokumentuje se samo Potraživanja.

### Q5 — Ograničenje po centrima
Postoje `allowed_centers` (veza ka OJ) i `allowed_center_codes` (tekstualna lista).
**Pitanje:** koji je merodavan i u kom modulu? Da li je jedan zastareo?

### Q6 — Obračun ocenjivanja zaposlenih
`EmployeeEvaluation` čuva `stimulation` i `personal_coefficient`. Formula se izvodi iz
`EvaluationScale.coefficient` po merilima.
**Pitanje:** postoji li zvanični pravilnik o ocenjivanju na koji da se pozovem, i da li je
`Obrazac za ocenjivanje.xlsx` u korenu merodavan izvor?

### Q7 — Pristupni podaci za portale NIS i OMV
**Pitanje:** da li da u dokumentaciji održavanja navedem **gde se čuvaju** pristupni podaci
(bez samih lozinki), i ko je zadužen za njihovu obnovu kada isteknu?

### Q8 — Poseban broj telefona u obračunu obustava
U `mobilni/withholdings.py` broj `381637781481` ima poseban tretman (ne odbija se iznos paketa).
**Pitanje:** koje je poslovno objašnjenje ovog izuzetka? (Da li je to službeni broj, broj
direktora, zajednički broj?)

### Q9 — Lokacija nove dokumentacije ✔ rešeno
`dokumentacija/docs/`. `README.md` i `AGENTS.md` idu u koren repozitorijuma.

### Q10 — Jezik i pismo pojedinih sadržaja
`EvaluationCriterion.name` i `EvaluationScale.description` u bazi su na **ćirilici** [P],
dok je ostatak sistema na latinici.
**Pitanje:** da li u dokumentaciji nazive merila navodim izvorno (ćirilicom) ili preslovljene?

### Q11 — Prioritet ✔ rešeno
Redosled iz poglavlja 13 se primenjuje bez izmena.

### Q12 — Pravna služba
Pravna služba je tehnički u aplikaciji `naplata` (`views_pravna.py`, tabele `postupak` i
`promena_postupka`), ali je u Potraživanjima već modelovana kao `CollectionLegalCase` i
`CollectionLegalEvent`, uz `LegalCaseLink` za povezivanje sa nasleđenim ID-evima.
**Pitanje:** potvrđujete li da pravna služba prelazi u Potraživanja i da je dokumentujem
tamo, a ne kao deo Naplate? Do potvrde postupam tako.

---

## 15. Stanje izrade

**Ažurirano 18.09.2026.** — faze 1–6 su završene.

| Faza | Sadržaj | Stanje |
|---|---|---|
| **1. Inventar i plan** | Ovaj dokument | ✔ Završeno |
| **2. Mapiranje modula** | `docs/03-moduli.md` + 10 dokumenata modula | ✔ Završeno |
| **3. Analize i obračuni** | `docs/06-analize-i-obracuni.md` + 11 dokumenata | ✔ **Svih 74 obračuna** |
| **4. Poslovni procesi** | `docs/05-poslovni-procesi.md` | ✔ 9 procesa |
| **5. Za programere i AI agente** | `README.md`, `AGENTS.md`, `docs/01`, `02`, `04`, `07`, `08`, `09`, `10`, `11`, `12` | ✔ Završeno |
| **6. Za upravu** | `docs/uprava/pregled-ims-erp-a.md` | ✔ Završeno |
| **Objedinjeni dokument** | Za Word i PDF | Čeka Vašu potvrdu sadržaja |

**Ukupno: 34 dokumenta, oko 17.200 redova.**

### Šta ostaje

| # | Zadatak | Uslov |
|---|---|---|
| 1 | **Dopuna 11 izveštaja Flote stvarnim formulama** | DDL pogleda — očekuje se |
| 2 | **Objedinjeni dokument za Word i PDF** | Vaša potvrda sadržaja |
| 3 | Odgovori na **45 otvorenih pitanja** | Vaša potvrda i potvrda krajnjih korisnika |
| 4 | Potvrda korisnika i odgovornih po modulima | **Q2** |

---

## Prilog A — Tabela pouzdanosti ovog dokumenta

| Tvrdnja | Status | Izvor potvrde |
|---|---|---|
| Tehnologije i verzije | Potvrđeno | `requirements.txt`, `ims_erp/settings/base.py` |
| Spisak modula i ekrana | Potvrđeno | `ims_erp/urls.py` i `*/urls.py` svih aplikacija |
| Spisak modela i tabela | Potvrđeno | `*/models.py`, migracije |
| Spisak nasleđenih `dbo.*` objekata | Potvrđeno | Pretraga izvornog koda |
| **Sadržaj nasleđenih `dbo.*` objekata** | **Nepotvrđeno** | Definicije nisu u repozitorijumu — **Q1** |
| Raspored pozadinskih poslova | Potvrđeno | `core/management/commands/sync_celery_periodic_tasks.py` |
| Uloge i dozvole | Potvrđeno | `core/permissions.py`, `core/mixins.py` |
| Spoljne integracije i adrese | Potvrđeno | `fleet/sync/selenium.py`, `menice/scraper.py`, `ugovori/apr_openapi.py` |
| Spisak analiza i obračuna | Potvrđeno (postojanje) | Pretraga servisnih modula |
| **Formule i poslovna svrha obračuna** | **Predmet FAZE 3** | Biće potvrđeno čitanjem implementacije |
| **Primarni korisnici modula** | **Nepotvrđeno** | Zaključeno iz uloga — **Q2** |
| **Upotreba rezultata u knjiženju** | **Nepotvrđeno** | Nema podatka u kodu — **Q3** |
