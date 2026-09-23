# 2. Arhitektura

> **Za koga je ovo poglavlje:** za programere i AI agente. Poslovni korisnici mogu
> preskočiti na [3. Moduli](03-moduli.md).
> Sve tvrdnje su označene: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 2.1. Tip sistema

**Django monolit.** [P] Jedan proces opslužuje sve module; nema mikroservisa,
nema REST API-ja, nema odvojenog frontend okvira.

| Sloj | Tehnologija | Napomena |
|---|---|---|
| Prikaz | Django templates + DataTables + Select2 + widget-tweaks | 280 HTML šablona |
| Aplikacija | Django 5.0.9, Python 3.12 | 11 Django aplikacija |
| Obračuni | Obični Python moduli (`services/`, `support/`) | Bez okvira, bez klasa gde nisu potrebne |
| Pristup podacima | Django ORM (`default`) + sirovi SQL (`server_db`) | Dva aliasa, ista baza |
| Baza | Microsoft SQL Server, `mssql-django` 1.5, ODBC Driver 17 | Baza `IMS_ERP` |
| Pozadinski poslovi | Celery 5.4 + Redis + `django-celery-beat` | 18 zakazanih poslova |
| Okruženje | Windows server, NSSM servisi | Tri servisa |

`djangorestframework` i `psycopg2-binary` postoje u `requirements.txt`, ali **nisu**
u `INSTALLED_APPS` niti se koriste u kodu. [Z]

---

## 2.2. Slojevi i putanja zahteva

```
 Pregledač
     │  HTTP
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ MIDDLEWARE                                                      │
│   SecurityMiddleware → Session → Common → CSRF → Authentication  │
│   → core.middleware.ActivityLogMiddleware  ← beleži svaki zahtev │
│   → Messages → XFrameOptions                                     │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ URL RAZREŠAVANJE          ims_erp/urls.py → <app>/urls.py        │
│   Ime rute (view_name) ISTOVREMENO je i kod dozvole.             │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ VIEW      LoginRequiredMixin + RolePermissionRequiredMixin       │
│           Zadatak: pročitati parametre, pozvati servis, vratiti  │
│           kontekst šablonu. BEZ poslovne logike.                 │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ SERVIS / SUPPORT      Sva poslovna logika i svi obračuni.        │
│                       Bez pristupa `request`-u gde god je moguće.│
└─────────────────────────────────────────────────────────────────┘
     │
     ├──► Django ORM ─────────► alias `default`   ─┐
     └──► connections['server_db'].cursor() ──────┤──► SQL Server IMS_ERP
                                                   │
                                                   └──► povezani serveri
```

**Pravilo koje kod dosledno poštuje [P]:** `views/` prikazuje, `services/` i `support/`
računaju. Ako tražiš formulu, ona **nije** u view-u.

---

## 2.3. Aplikacije i njihove uloge

| Aplikacija | Uloga | Ima ekrane |
|---|---|---|
| `core` | Korisnici, uloge, dozvole, evidencija rada, istorija zadataka, prebacivanje modula | Samo `switch-app` |
| `fleet` | Vozni park **+ korenske rute sistema** (prijava, kontrolna tabla, korisnici, log) | Da (115) |
| `hr` | Kadrovi | Da (25) |
| `finansije` | Finansijska analitika | Da (16) |
| `nabavka` | Nabavka | Da (24) |
| `potrazivanja` | Potraživanja | Da (10) |
| `ugovori` | Partneri i ugovori | Da (20) |
| `menice` | Menice | Da (6) |
| `mobilni` | Mobilna telefonija | Da (16) |
| `isplate` | Virmani | Da (2) |
| `naplata` | **Nasleđeno, u gašenju** | Da (27) |

### Zamke u organizaciji aplikacija [P]

1. **`core` i `hr` upisuju tabele u `fleet`.** Modeli u `core/models.py` i deo modela u
   `hr/models.py` imaju `class Meta: app_label = "fleet"`. Fizičke tabele su zato
   `fleet_employee`, `fleet_activity_log`, `fleet_task_history`, `fleet_organizationalunit`,
   a **ne** `core_*` ni `hr_*`.

2. **`Employee` ima dva imena.** Definisan je u `hr/models.py`, uvozi se kao
   `from hr.models import Employee`, ali se u vezama navodi kao `"fleet.Employee"`
   (npr. `CustomUser.employee`, `MobileUser.employee`). To je isti model.

3. **`izvestaji/` je prazan direktorijum** — nije Django aplikacija i nije u `INSTALLED_APPS`.

4. **Bočni meniji ≠ aplikacije.** Meni `kadrovi` koristi `hr`. Meni `pravna` jeste
   aplikacija `pravna`, ali pored nje prikazuje i `ugovori`. Prebacivanje se čuva u sesiji
   (`request.session["current_app"]`) preko `core/context_processors.py`.

5. **Pravna služba je preseljena iz `naplata` u `pravna`** (rute `pravna:*` umesto
   `naplata:pravna_*`). Tabele `postupak` i `promena_postupka` nisu menjane — selidba je
   izvedena kroz `SeparateDatabaseAndState`, a stare dozvole su preslikane migracijom
   `fleet/0079_pravna_permission_codes.py`.

---

## 2.4. Podaci — gde šta živi

### 2.4.1. Konekcije [P]

| Alias | Motor | Baza | Server | Namena |
|---|---|---|---|---|
| `default` | `mssql` | `IMS_ERP` | `SMS-SERVER` | Django ORM, migracije |
| `server_db` | `mssql` | `IMS_ERP` | `SMS-SERVER` | Sirovi SQL nad nasleđenim `dbo.*` objektima |
| `local` | `sqlite3` | `db.sqlite3` | — | Definisan u `production.py`, **ne koristi se** |

**`default` i `server_db` su ista fizička baza.** [P] Razdvojeni su namenski, ne fizički.
Django aplikacija i nasleđeni ERP dele bazu `IMS_ERP`.

Podrazumevane postavke veze prema SQL Serveru primenjuje
`ims_erp/settings/base.py: apply_mssql_connection_defaults()` [P]:

| Postavka | Vrednost | Svrha |
|---|---|---|
| `CONN_MAX_AGE` | 300 s | Manje ponovnih povezivanja u dugotrajnim Celery procesima |
| `CONN_HEALTH_CHECKS` | uključeno | Provera veze pre upotrebe |
| `connection_timeout` | 10 s | |
| `query_timeout` | 90 s | Za `sp_AzurirajNalogZ` se privremeno diže na 900 s |
| `connection_retries` | 3, sa pauzom 5 s | |
| `TrustServerCertificate` | `yes` | |

### 2.4.2. Povezani serveri — **najvažniji arhitektonski nalaz** [P]

Sistem **ne čita sve iz lokalne baze**. Ključni podaci dolaze sa udaljenih servera:

| Povezani server | Baza | Objekti | Ko čita |
|---|---|---|---|
| `PUTGEO-SERVER` | `bazaims` | `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | `finansije/services/source.py`, `potrazivanja/services/source.py` |
| `PUTGEO-SERVER` | `bazaldims` | `Zarada`, `PomLD`, `Radnik`, `element` | `finansije/services/job_people.py`, `cash_flow.py` |
| `INFORMATIKA23` | `ID` | `Radnici`, `C_Prolasci_Radnika`, `C_Tasteri`, `c_parovi_radnika_detalji` | `hr/services/attendance.py` |
| `SERFIN` | `bazaldims` | `radnik` | `hr/services/attendance.py` |

**Posledice [Z]:**

- Dostupnost Finansija i Kadrova zavisi od tri udaljena servera.
- Deo nasleđenih `dbo.*` pogleda u `IMS_ERP` **interno** takođe prelazi na udaljeni server,
  pa „lokalno“ ne znači i „brzo“ ni „nezavisno“.
- `nalog_z` postoji dvaput: **izvor** na `PUTGEO-SERVER.bazaims` i **lokalna kopija**
  `IMS_ERP.dbo.nalog_z` koju puni `sp_AzurirajNalogZ`. Finansijska analitika čita
  **udaljeni** izvor u svoju tabelu `LedgerEntry`. Pokretanje procedure osvežava samo
  lokalnu kopiju i **ne prebacuje** nijedan upit na nju. [P]

### 2.4.3. Tri vrste podataka u sistemu [Z]

| Vrsta | Vlasnik podatka | Primeri | Sme li se menjati iz aplikacije |
|---|---|---|---|
| **Sopstveni** | IMS ERP | Vozila, kvarovi, ugovori, menice, predmeti nabavke, ocene | Da |
| **Preuzeti (snimak)** | Spoljni sistem | `LedgerEntry`, `EufItemSnapshot`, `GoodsSnapshot`, `SickLeave`, `AnnualLeaveAllowance`, `MobileUsage` | Ne — prepisuje ih sledeća sinhronizacija |
| **Čitani u letu** | Spoljni sistem | `dbo.fleet_tro_svi`, `dbo.dodela_baketa`, prolasci radnika | Ne — aplikacija ih samo čita |

---

## 2.5. Ponavljajući obrasci

Sistem koristi nekoliko obrazaca dosledno. Kada ih prepoznaš, ostatak koda je predvidiv.

### Obrazac 1 — „Draft → Final“ [P]

Podatak iz spoljnog izvora ne može odmah da se poveže sa vozilom, pa se prvo upisuje u
nedovršenu tabelu, korisnik ga dopuni, a zatim se prebacuje u konačnu.

```
 Spoljni izvor ──► Draft tabela ──► ekran „nedovršeno“ ──► Final tabela
                   (bez vozila)      (korisnik bira)        (sa vozilom)
```

| Draft | Final | Ekran | Funkcija prebacivanja |
|---|---|---|---|
| `DraftInsurance` | `Insurance` | `/insurance/drafts/` | `fleet/sync/external.py: migrate_draft_to_insurance_single` |
| `DraftServiceTransaction` | `ServiceTransaction` | `/servisi/nedovrseno/` | `fleet/views/services.py` |

Srodni ekrani „nedovršeno“ bez zasebne draft tabele: `policy_fixing_list`,
`requisition_fixing_list` — tamo se dopunjuje isti zapis.

### Obrazac 2 — „Snimak izvora“ (snapshot) [P]

Spoljni skup se čita u celini i upisuje u lokalnu tabelu po **stabilnom ključu izvora**,
nikada po iznosu ili opisu.

| Model | Stabilni ključ | Izvor |
|---|---|---|
| `LedgerEntry` | firma, godina, vrsta naloga, broj naloga, stavka | `PUTGEO-SERVER.bazaims.nalog_z` |
| `EufItemSnapshot` | `source_key` | `dbo.nbv_EUF_stavke` |
| `GoodsSnapshot` | `source_key` | `dbo.nbv_roba` |
| `ReceivablePosting` | izvor, firma, godina, vrsta, broj, stavka | `dbo` pogledi naplate |
| `AnnualLeaveAllowance` | firma, godina, šifra zaposlenog | kadrovska baza |

Pravila koja svi snimci poštuju:

- Nestao red se označava **neaktivnim** (`active=False`), ne briše se. [P]
- Ponovo pojavljen red vraća se pod **istim lokalnim ID-em**. [P]
- Prazan izvor ne može automatski obrisati postojeće podatke. [P]
- Pre objave se porede **kontrolni zbirovi** sa nezavisnim upitom nad izvorom;
  neslaganje zaustavlja sinhronizaciju. [P] (`finansije/services/source.py: totals_for`)

### Obrazac 3 — „Objavljeni snimak stanja“ [P]

U Potraživanjima postoji dodatni korak: sirova knjiženja se prvo obrade u **pozicije**,
pa se snimak objavi. Aktivno stanje je uvek jedan **objavljeni** snimak.

```
ReceivablePosting ──► BalanceSnapshot (draft) ──► validated ──► published
                            │                                       │
                            └──► ReceivablePosition                 ▼
                                                            CollectionState.current_snapshot
```

`CollectionState` ne dozvoljava da aktivno stanje bude snimak koji nije objavljen. [P]

### Obrazac 4 — Zaključavanje pozadinskih poslova [P]

```python
_run_with_singleton_lock(task_name, lock_ttl_seconds, fn)
```

Redis ključ `ims_erp:task-lock:<task>`. Ako posao već radi, novi se **preskače**
(vraća `SKIP:`), a `TaskHistory` to beleži kao status „Preskočen“.

Trajanje zaključavanja: 4 h za Selenium, 90 min za sinhronizacije, 60 min za lakše poslove.

**Fail-open:** ako Redis nije dostupan, posao se **ipak izvršava**, bez zaštite. [P]

Finansije koriste jači mehanizam — **SQL Server `sp_getapplock`** vezan za istu sesiju
koja pokreće proceduru, pa zaštita važi i za ručno i za Celery pokretanje. [P]

### Obrazac 5 — Istorija izvršavanja [P]

Svaki Celery zadatak automatski upisuje `TaskHistory` preko signala u `ims_erp/celery.py`
(`task_prerun`, `task_postrun`, `task_failure`). Finansije dodatno imaju `SyncRun` i
`NalogZRefreshRun`, a Potraživanja `CollectionSyncRun` i `CollectionSyncStep`.

### Obrazac 6 — DataTables preko AJAX-a [P]

Veće liste se ne renderuju u šablonu. Stranica učita okvir, pa zasebna ruta `.../data/`
vrati JSON. Zajednička pomoć: `finansije/services/datatables.py`, `fleet/views/datatables.py`.
Autorizacija i filteri se **ponovo proveravaju pri svakom AJAX zahtevu**. [P]

### Obrazac 7 — Brisanje fajlova posle potvrde transakcije [P]

Modeli sa fajlovima (`Contract`, `Offer`, `BusinessRequest`, `VehicleTenderDocument`,
`ContractDocument`) brišu staru datoteku tek u `transaction.on_commit`, da neuspela
transakcija ne obriše fajl.

---

## 2.6. Kontrola pristupa

### 2.6.1. Model [P]

```
CustomUser ──M2M──► Role ──RolePermission──► PermissionCode
                     │                            │
                 is_active                 code = IME URL RUTE
```

Provera (`core/mixins.py`):

```python
user.roles.filter(permissions__code=permission_code, is_active=True).exists()
```

gde je `permission_code` podrazumevano `request.resolver_match.view_name`.
`is_superuser` prolazi uvek.

Tri načina primene:

| Način | Upotreba |
|---|---|
| `RolePermissionRequiredMixin` | Klasni view-ovi |
| `role_permission_required()` | Funkcijski view-ovi |
| `RoleRequiredMixin` | Kada se traži **uloga**, a ne dozvola (podrazumevano `uprava`) |

### 2.6.2. Automatsko generisanje dozvola [P]

`core/permissions.py: sync_permission_codes()` obilazi `urlpatterns` svih aplikacija,
skuplja imena ruta i stvara `PermissionCode` za svako.

**Posledice:**

- Nova ruta = nova dozvola, ali tek posle `manage.py sync_permission_codes`
  ili noćnog zadatka u 01:00.
- Uloga **Uprava** pri svakoj sinhronizaciji dobija **sve** dozvole.
- Uloge `nabavka`, `menice`, `blagajna`, `mobilni`, `pregled-naplate`, `zahtev` se
  **usklađuju** — višak dozvola se briše. Uloge `pravna`, `sekretarijat`, `zaposleni`
  se samo dopunjuju.
- Postoje i ručno dodate dozvole van ruta: `finansije:view_all`, `hr:evaluation_view_all`.

### 2.6.3. Drugi sloj — ograničenje po centrima [P]

| Polje | Tip | Napomena |
|---|---|---|
| `CustomUser.allowed_centers` | M2M ka `OrganizationalUnit` | |
| `CustomUser.allowed_center_codes` | tekst, šifre odvojene zarezima | |

**Oba mehanizma postoje paralelno.** [P] Koji je merodavan u kom modulu nije potvrđeno —
otvoreno pitanje **Q5** u inventaru. [N]

U Finansijama prazna lista dozvoljenih centara **nije** globalan pristup. [P]

### 2.6.4. Predefinisane uloge [P]

| Slug | Naziv | Obuhvat |
|---|---|---|
| `uprava` | Uprava | Sve dozvole (automatski) |
| `nabavka` | Nabavka | Ceo modul Nabavka |
| `menice` | Menice | Ceo modul Menice |
| `blagajna` | Blagajna | Ceo modul Isplate |
| `pravna` | Pravna služba | Pravna služba + modul Ugovori |
| `mobilni` | Mobilni | Ceo modul Mobilni |
| `finansije` | Finansijska analitika | `dashboard`, `ledger`, `export` |
| `pregled-naplate` | Pregled naplate | Pregledi i izvozi Naplate, bez izmena |
| `zahtev` | Zahtev | Kreiranje zahteva nabavke i štampa |
| `sekretarijat` | Sekretarijat | Zaposleni i putni nalozi |
| `zaposleni` | Zaposleni | Svoj profil i zaduženje vozila |

### 2.6.5. Evidencija rada [P]

`core/middleware.py: ActivityLogMiddleware` posle svakog odgovora poziva
`core/activity.py: log_request_activity` i upisuje `ActivityLog`
(tabela `fleet_activity_log`): korisnik, akcija, aplikacija, ruta, metod, putanja,
status, model, ID zapisa, izmene (JSON), IP adresa, korisnički agent.

Beleže se i prijava, odjava i **neuspešna prijava**. Ekran: `/administracija/activity-log/`.

---

## 2.7. Pozadinski poslovi

### 2.7.1. Redovi [P]

| Red | Šta ide u njega | Zašto odvojeno |
|---|---|---|
| `selenium` | NIS, OMV putnička, OMV teretna | Traju dugo i zavise od pregledača |
| `sync` | Sve ostale sinhronizacije | Kratke, ne smeju čekati Selenium |
| `default` | Podrazumevani | |

### 2.7.2. Ozbiljno ograničenje [P]

Produkcioni worker se pokreće sa `-P solo` (`nssm.bat`):

```
celery -A ims_erp worker -l info -P solo -Q default,sync,selenium
```

`-P solo` znači **jedan zadatak u jednom trenutku**, bez obzira na
`CELERY_WORKER_CONCURRENCY = 2` u postavkama. Razdvajanje redova zato **ne daje
paralelnost** dok radi jedan worker — Selenium posao koji traje sat vremena blokira
i `sync` zadatke.

> **Napomena za održavanje [Z]:** paralelnost bi zahtevala drugi worker proces
> vezan samo za red `sync`. To je odluka za održavanje, ne izmena koda.

### 2.7.3. Postavke koje smanjuju opterećenje [P]

| Postavka | Vrednost | Svrha |
|---|---|---|
| `CELERY_TASK_IGNORE_RESULT` | `1` | Rezultati se ne čuvaju u Redisu |
| `CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED` | `True` | Greške se ipak čuvaju |
| `CELERY_WORKER_MAX_TASKS_PER_CHILD` | 100 | Obnavljanje procesa, protiv curenja memorije |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | 1 | Bez gomilanja zadataka |
| `CELERY_ENABLE_UTC` | `False`, `CELERY_TIMEZONE = CET` | Lokalno vreme u rasporedu |

---

## 2.8. Datoteke i mediji

| Sadržaj | Putanja |
|---|---|
| Slike vozila | `media/vehicles/photos/%Y/%m/` |
| Saobraćajne dozvole (PDF i slike) | `media/traffic_cards/`, `media/traffic_cards/images/%Y/%m/` |
| Tenderska dokumentacija vozila | `media/vehicle_tender_documents/%Y/%m/` |
| Ugovori i prilozi | `media/ugovori/files/`, `dokumenti/`, `ponude/`, `zahtevi/` |

Ograničenja otpremanja [P]: `MAX_CONTRACT_UPLOAD_SIZE` 50 MB,
`DATA_UPLOAD_MAX_MEMORY_SIZE` 60 MB.

`MEDIA_URL` se opslužuje preko Djanga **samo kad je `DEBUG=True`**. [P]
Pošto je `DEBUG=True` i u produkciji, mediji se trenutno opslužuju preko Djanga. [Z]

---

## 2.9. Postavke po okruženjima

| Fajl | Baza | `ALLOWED_HOSTS` |
|---|---|---|
| `base.py` | — (zajedničko; `DEBUG = True`, `SECRET_KEY` upisan) | — |
| `development.py` | **Pravi SQL Server** `IMS_ERP` | `127.0.0.1` |
| `production.py` | Isti SQL Server + nekorišćeni `local` sqlite | `ims-flota`, `ims.portal`, `192.168.6.7`, `127.0.0.1`, `localhost` |
| `testing.py` | SQLite **u memoriji** | `testserver`, `localhost`, `127.0.0.1` |

`testing.py` isključuje SQL Server, Redis i e-poštu; `CELERY_TASK_ALWAYS_EAGER = True`
i brz MD5 heš lozinki. [P]

**`manage.py` podrazumevano koristi `development`** [P] — dakle pravu bazu.
`ims_erp/celery.py` podrazumevano koristi `production`. [P]

> Bezbednosni nalazi u vezi sa ovim postavkama: [10. Poznati problemi](10-poznati-problemi.md).

---

## 2.10. Testovi

550 testova u 31 fajlu. [P] Pokreću se na SQLite bazi u memoriji:

```powershell
.\.venv\Scripts\python.exe manage.py test --settings=ims_erp.settings.testing
```

Raspored po modulima:

| Modul | Testova | Najviše pokriveno |
|---|---|---|
| `fleet` | 153 | Presek flote, kilometraža, održavanje, unos vozila, izveštaji |
| `finansije` | 121 | Tok gotovine, kartica posla, zajednički troškovi, nalog Z |
| `hr` | 97 | Odmori, bolovanja, ocenjivanje, šifarnik radne liste |
| `potrazivanja` | 59 | Sinhronizacija, operacije, integracija, brzina čitanja |
| `mobilni` | 40 | Obustave, uvoz |
| `core` | 28 | Dozvole, evidencija rada |
| `nabavka` | 19 | Povezivanje faktura i šifara posla |
| `isplate` | 20 | Virman |
| ostali | 13 | |

---

## 2.11. Sistemi izvan aplikacije

```
┌──────────────┐  Selenium   ┌───────────────────────┐
│ cards.nis.rs │◄────────────┤                       │
└──────────────┘             │                       │
┌──────────────┐  Selenium   │                       │
│ fleet.omv.com│◄────────────┤                       │
└──────────────┘             │      IMS ERP          │
┌──────────────┐  HTTP/HTML  │                       │
│ NBS PnWebApp │◄────────────┤   (Django + Celery)   │
└──────────────┘             │                       │
┌──────────────┐  HTTP/JSON  │                       │
│ APR OpenAPI  │◄────────────┤                       │
└──────────────┘             │                       │
┌──────────────┐  Excel      │                       │
│ RFZO, MTS    │────────────►│                       │
└──────────────┘             │                       │
                             │                       │  datoteka
                             │                       ├──────────► Banka (virman)
                             └───────────┬───────────┘
                                         │ SQL
                             ┌───────────▼───────────┐
                             │  PUTGEO-SERVER        │ knjigovodstvo, zarade
                             │  INFORMATIKA23        │ kontrola pristupa
                             │  SERFIN               │ kadrovska
                             └───────────────────────┘
```

Detaljno: [7. Integracije](07-integracije.md).

---

## 2.12. Šta arhitektura dobro rešava, a šta ne

### Dobro [Z]

- **Razdvajanje prikaza i obračuna** — formule su na jednom mestu i mogu se testirati.
- **Stabilni ključevi izvora** — ponovljena sinhronizacija ne stvara duplikate.
- **Kontrolni zbirovi pre objave** — nepotpuno čitanje izvora se otkriva, a ne objavljuje.
- **Istorija svega** — `TaskHistory`, `SyncRun`, `ActivityLog`, `ProcurementStatusLog`,
  `CollectionAudit` daju sledljivost.
- **Dozvole vezane za rute** — nemoguće je zaboraviti dozvolu za novi ekran; najgore što
  se desi je da je vidi samo Uprava.

### Slabije [Z]

- **Jedan worker sa `-P solo`** poništava korist od razdvojenih redova.
- **Zavisnost od tri udaljena servera** bez rezervnog ponašanja.
- **Selenium kao integracija** je krhak — promena stranice dobavljača zaustavlja preuzimanje.
- **Nasleđeni pogledi van kontrole verzija** — promena pogleda menja rezultat bez izmene koda.
- **Dva paralelna mehanizma za centre** otežavaju rasuđivanje o pristupu.
- **`DEBUG=True` u produkciji** i tajne u repozitorijumu.

---

## 2.13. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Šta radi pojedini modul? | [3. Moduli](03-moduli.md) |
| Koje tabele i kolone postoje? | [4. Baza podataka](04-baza-podataka.md) |
| Kako se računa određeni iznos? | [6. Analize i obračuni](06-analize-i-obracuni.md) |
| Kako se sistem pokreće i održava? | [8. Instalacija](08-instalacija-i-pokretanje.md), [9. Održavanje](09-odrzavanje.md) |
