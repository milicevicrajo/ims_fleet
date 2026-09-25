# 9. Održavanje

> **Za koga je ovo poglavlje:** osoba koja održava sistem i dežurni administrator.
> Status tvrdnji: **[P]** potvrđeno kodom/konfiguracijom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 9.1. Šta se svakodnevno dešava samo od sebe

```
 01:00  Dozvole i uloge
 01:10  Zaposleni iz kadrovske baze
 01:20  Provera otpisanih vozila
 01:30  Šifre poslova i organizacione jedinice
 01:45  Trebovanja
 02:00  Polise osiguranja
 02:20  EUF fakture (Nabavka)
 02:45  UF stavke (Nabavka)
 03:15  Servisi vozila
 03:35  Knjiženja osiguranja DDOR
 03:50  Finansije — sve godine od 2025.
 04:20  Gorivo NIS                    ← Selenium, do 4 h
 05:10  Gorivo OMV putnička            ← Selenium, do 4 h
 06:10  Gorivo OMV teretna             ← Selenium, do 4 h
 07:10  Roba (Nabavka)
 ────────────────── radni dan ──────────────────
 10:00  Osvežavanje lokalnog nalog_z
 11:00  Osvežavanje lokalnog nalog_z
 12:30  Isplaćeni iznosi po putnim nalozima
 :20    Svakog sata — Finansije, tekuća godina
```

**Ukupno 18 zakazanih poslova.** [P]

---

## 9.2. Tabela zakazanih poslova

| Vreme | Naziv | Task | Red | Zaključavanje |
|---|---|---|---|---|
| 01:00 | Administracija — sinhronizacija dozvola | `core.tasks.sync_permission_codes_task` | `sync` | — |
| 01:10 | Kadrovi — sinhronizacija zaposlenih | `fleet.tasks.sync_hr_employees_task` | `sync` | 90 min |
| 01:20 | Flota — provera otpisa vozila | `fleet.tasks.proveri_otpis` | `sync` | 60 min |
| 01:30 | Flota — šifre poslova i OJ | `fleet.tasks.fetch_job_codes` | `sync` | 60 min |
| 01:45 | Flota — trebovanja | `fleet.tasks.fetch_requisition_data_task` | `sync` | 90 min |
| 02:00 | Flota — polise | `fleet.tasks.fetch_policy_data_task` | `sync` | 90 min |
| 02:20 | Nabavka — EUF fakture | `nabavka.tasks.sync_euf_invoices_task` | `sync` | — |
| 02:45 | Nabavka — UF stavke | `nabavka.tasks.sync_uf_items_task` | `sync` | — |
| 03:15 | Flota — servisi | `fleet.tasks.fetch_service_data_task` | `sync` | 90 min |
| 03:35 | Flota — DDOR osiguranja | `fleet.tasks.fetch_ddor_data_task` | `sync` | 90 min |
| 03:50 | Finansije — sve godine | `finansije.tasks.sync_all_years` | `sync` | SQL lock |
| **04:20** | **Gorivo — NIS** | `fleet.tasks.run_nis_command` | **`selenium`** | **4 h** |
| **05:10** | **Gorivo — OMV putnička** | `fleet.tasks.run_omv_putnicka_command` | **`selenium`** | **4 h** |
| **06:10** | **Gorivo — OMV teretna** | `fleet.tasks.run_omv_teretna_command` | **`selenium`** | **4 h** |
| 07:10 | Nabavka — roba | `nabavka.tasks.sync_goods_task` | `sync` | — |
| **10:00 i 11:00** | **Finansije — osvežavanje `nalog_z`** | `finansije.tasks.refresh_nalog_z_task` | `sync` | SQL lock |
| 12:30 | Putni nalozi — isplaćeno | `fleet.tasks.sync_putni_nalozi_isplaceno_task` | `sync` | 90 min |
| svaki sat u :20 | Finansije — tekuća godina | `finansije.tasks.sync_current_year` | `sync` | SQL lock |

> **[P] Vremenska zona:** `nalog_z` izričito koristi `Europe/Belgrade`; ostali koriste
> `CELERY_TIMEZONE = CET`.

### Poslovi koji NISU zakazani, a postoje [P]

| Posao | Pokreće se |
|---|---|
| Sinhronizacija godišnjih odmora | Ručno, sa ekrana |
| Sinhronizacija Potraživanja | Ručno (zadatak postoji, ali nije u rasporedu) |
| Preuzimanje menica iz NBS-a | Ručno |
| APR provera partnera | Ručno |
| Sinhronizacija partnera iz Finansija | Ručno |
| Knjigovodstvena vrednost vozila | Ručno |
| Kamate lizinga | Ručno |
| Čišćenje duplikata goriva | Automatski **uz svaki uvoz OMV podataka** |

---

## 9.3. Kako proveriti da je sve prošlo

### Prvi korak — istorija zadataka [P]

> **`/administracija/task-history/`**

| Status | Značenje | Šta uraditi |
|---|---|---|
| **Uspešan** | Prošlo | Ništa |
| **Preskočen** | Prethodno izvršavanje još traje | **Nije greška.** Proveriti da se ne ponavlja svaki dan |
| **Neuspešan** | Greška | Pogledati poruku i dnevnik |
| **Pokrenut** *(a prošlo je puno vremena)* | Posao je prekinut bez zapisa | Proveriti da li proces radi |

Uz svaki posao se vide **trajanje**, **rezultat** i **tekst greške**. [P]

### Drugi korak — po modulima

| Modul | Gde se proverava |
|---|---|
| **Finansije** | `/finansije/sinhronizacija/` — brojači i **kontrolni zbirovi** |
| **Potraživanja** | `/potrazivanja/sinhronizacija/` — koraci, kontrole, problemi prenosa |
| **Mobilni** | `/mobilni/import/` — dnevnik uvoza |
| **Kadrovi — bolovanja** | `/hr/bolovanja/uvoz/` — brojači |
| **Flota — nedovršeno** | Kontrolna tabla, grupa „Evidencije za dopunu“ |

### Treći korak — dnevnici

```
C:\DjangoApps\logs\celery-worker.stdout.log
C:\DjangoApps\logs\celery-worker.stderr.log
C:\DjangoApps\logs\celery-beat.stdout.log
C:\DjangoApps\logs\redis.stdout.log
```

Dnevnici se **rotiraju na 10 MB** (NSSM). [P]

Korisne oznake u dnevniku [P]: `TASK_START`, `TASK_DONE`, `TASK_FAIL`,
`CELERY_TASK_START`, `CELERY_TASK_FINISH`, `CELERY_TASK_FAILURE`, `SKIP:`.

---

## 9.4. Windows servisi

| Servis | Šta radi |
|---|---|
| `IMS_Fleet_Redis` | Redis — broker i zaključavanje |
| `IMS_Fleet_Celery_Worker` | Izvršava poslove |
| `IMS_Fleet_Celery_Beat` | Pokreće poslove po rasporedu |

```powershell
Get-Service IMS_Fleet_*
Restart-Service IMS_Fleet_Celery_Worker
```

Instalacija: `nssm.bat`. Podešavanja se menjaju kroz `nssm edit <servis>`.

### Ozbiljno ograničenje [P]

Radnik se pokreće sa **`-P solo`** — **jedan zadatak u jednom trenutku**.
Postavka `CELERY_WORKER_CONCURRENCY = 2` u tom režimu **nema dejstva**.

**Posledica:** Selenium posao koji traje sat vremena **blokira i lake sinhronizacije**.
Vidi [P-15](10-poznati-problemi.md).

---

## 9.5. Posle isporuke novog koda

> **Redosled je bitan.** [Z]

```powershell
# 1. Migracije
.\.venv\Scripts\python.exe manage.py migrate

# 2. Dozvole — ako su dodate nove rute
.\.venv\Scripts\python.exe manage.py sync_permission_codes

# 3. Raspored — ako su dodati novi zadaci (prvo provera)
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks --dry-run
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks

# 4. Restart radnika — OBAVEZNO ako je dodat novi zadatak
Restart-Service IMS_Fleet_Celery_Worker
Restart-Service IMS_Fleet_Celery_Beat
```

> **[P] Zašto restart:** stari radnik **odbacuje nepoznat zadatak**. Ako se raspored
> aktivira pre restarta, zadaci se gube.

Za ciljanu dopunu novih ekrana Pravne službe i rešenja zaposlenih:

```powershell
.\.venv\Scripts\python.exe manage.py sync_pravna_resenja_permissions --dry-run
.\.venv\Scripts\python.exe manage.py sync_pravna_resenja_permissions
```

Komanda dodaje sve rute `pravna:*` ulozi **Pravna služba**, operativne dozvole
`hr:resenje_*` ulozi **Sekretarijat**, a ove kodove **Upravi**. Uloga **Kadrovi**
zamenjuje **Kadrovik — rešenja** i dobija funkcije celog kadrovskog modula, uključujući
šifarnike, uz ograničenje podataka po dodeljenom obuhvatu. Posebne dozvole za sve centre
ne dodaju se ulozi Kadrovi.
Postojeće dozvole i članstva korisnika ostaju sačuvani. Ista dopuna je uključena
u redovni `sync_permission_codes`.

Za ekran upravljanja korisničkim pristupom od 24.09.2026. primeniti migraciju
`fleet.0081_customuser_allowed_hr_unit_codes`, pa ciljanu komandu:

```powershell
.\.venv\Scripts\python.exe manage.py migrate fleet 0081
.\.venv\Scripts\python.exe manage.py sync_user_access_permissions --dry-run
.\.venv\Scripts\python.exe manage.py sync_user_access_permissions
```

Ona usklađuje samo ulogu Kadrovi i kodove administracije korisnika, bez redovnog
prepisivanja dozvola drugih standardnih uloga. Posle isporuke koda restartovati web
proces i radnike koji učitavaju `core.permissions`, da stari kod ne bi vratio staru ulogu.

Disciplinski postupci od 24.09.2026. koriste migraciju
`pravna.0002_disciplinskipostupak_mera_vrsta`: zatvaranje traži datum i jednu od četiri
mere iz člana 77 dostavljenog pravilnika (pisana opomena, udaljenje bez naknade
1–15 radnih dana, novčana kazna do 20% osnovne zarade do tri meseca, prestanak radnog
odnosa). Stari zatvoreni postupci ostaju zatvoreni; nedostajuća mera dopunjava se na
detalju, bez nagađanja na osnovu datuma ili zaposlenog. Raniji slobodan opis se čuva.
Centar u formi je izbor iz spiska, predložen iz OJ zaposlenog postojećim pravilom
najdužeg prefiksa centra; izabrani drugi centar se čuva. „Arhivirano“ je uklonjeno iz
forme unosa/izmene, dok zasebna akcija arhiviranja i postojeća arhiva ostaju dostupne.

---

## 9.6. Česti problemi i šta uraditi

| Simptom | Verovatan uzrok | Šta uraditi |
|---|---|---|
| **Nema novih podataka o gorivu** | Selenium ne uspeva | Pogledati `TaskHistory`; proveriti prijavu na portal i verziju Chrome-a; **uvesti datoteku ručno** |
| **Finansije prazne za godinu** | Sinhronizacija nije prošla | `/finansije/sinhronizacija/` — pokrenuti ručno; proveriti `PUTGEO-SERVER` |
| **Radna lista bez sati** | `INFORMATIKA23` nedostupan | Poruka to kaže; podaci se vraćaju kada server proradi |
| **Zadatak stalno „Preskočen“** | Prethodni je ostao zaključan | Proveriti da li proces radi; zaključavanje ističe posle 4 h / 90 min |
| **Novi ekran niko ne vidi** | Dozvola nije generisana | `sync_permission_codes`, pa dodeliti ulozi |
| **Novi zadatak se ne izvršava** | Radnik ga ne poznaje | Restart radnika |
| **`nalog_z` — „Ishod nepoznat“** | Proces je pao tokom procedure | **Proveriti stanje u bazi** pre ponovnog pokretanja |
| **Sinhronizacija Potraživanja ne prolazi** | Kontrolni zbirovi se ne slažu | Poruka navodi koja kontrola; **prethodni snimak ostaje objavljen** |
| **Vozilo nema šifru posla** | Nema dodele pre datuma | `/sifre-poslova/` |
| **Polisa nije u upozorenjima** | Polisa je **nedovršena** | `/polise/nedovrseno/` |
| **Redis ne radi** | Servis stao | Poslovi se **ipak izvršavaju**, bez zaštite — [P-16](10-poznati-problemi.md) |

---

## 9.7. Redovne provere

### Svakodnevno

| Provera | Gde |
|---|---|
| Da li su noćni poslovi prošli | `/administracija/task-history/` |
| Upozorenja o vozilima | Kontrolna tabla `/` |

### Nedeljno

| Provera | Gde |
|---|---|
| Nedovršene evidencije | Kontrolna tabla, „Evidencije za dopunu“ |
| Problemi prenosa Potraživanja | `/potrazivanja/sinhronizacija/` |
| Veličina dnevnika | `C:\DjangoApps\logs` |

### Mesečno

| Provera | Gde |
|---|---|
| Uvoz bolovanja (RFZO) | `/hr/bolovanja/uvoz/` |
| Uvoz podataka operatera | `/mobilni/import/` |
| **Obustave pre slanja u zarade** | `/mobilni/obustave/zaposleni/` |
| Kontrolni zbirovi Finansija | `/finansije/sinhronizacija/` |

### Godišnje

| Provera | Napomena |
|---|---|
| Početni brojevi putnih naloga po centrima | Bez njih se nalog **ne može otvoriti** za novu godinu |
| Plan javnih nabavki | Nova verzija |
| Pragovi troška po kilometru | Upisani u kod — [P-11](10-poznati-problemi.md) |

---

## 9.8. Ručno pokretanje poslova

```powershell
# Finansije
.\.venv\Scripts\python.exe manage.py sync_finansije
.\.venv\Scripts\python.exe manage.py sync_finansije --year-from 2026 --year-to 2026

# Potraživanja
.\.venv\Scripts\python.exe manage.py sync_potrazivanja

# Kadrovi
.\.venv\Scripts\python.exe manage.py sync_hr_employees
.\.venv\Scripts\python.exe manage.py sync_annual_leave
.\.venv\Scripts\python.exe manage.py import_rfzo_sick_leave <putanja>

# Flota
.\.venv\Scripts\python.exe manage.py fetch_job_codes
.\.venv\Scripts\python.exe manage.py otpis
.\.venv\Scripts\python.exe manage.py nis_command
.\.venv\Scripts\python.exe manage.py omv_command_putnicka
.\.venv\Scripts\python.exe manage.py omv_command_teretna
.\.venv\Scripts\python.exe manage.py cleanup_omv_fuel_duplicates          # pregled
.\.venv\Scripts\python.exe manage.py cleanup_omv_fuel_duplicates --apply  # brisanje

# Dozvole i raspored
.\.venv\Scripts\python.exe manage.py sync_permission_codes
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks --dry-run
```

**Ukupno 50 upravljačkih komandi.** Spisak: `manage.py help`. [P]

> **[P] Zaštita:** ručno pokretanje koristi **isto zaključavanje** kao zakazani posao —
> ne mogu se preklopiti.

---

## 9.9. Šta ne raditi

| Ne raditi | Zašto |
|---|---|
| **Ne pokretati poslovne procedure ručno** (`SPFINizv52/53/55`, `SPLdKnjizenje`) | Menjaju poslovne podatke u produkciji |
| **Ne pisati u nasleđene `dbo.*` poglede** | Vlasnik im je stari ERP |
| **Ne menjati nasleđene poglede bez dogovora** | Menja rezultat na ekranu bez traga — [P-27](10-poznati-problemi.md) |
| **Ne brisati zapise iz `TaskHistory` i `ActivityLog`** | To je jedini trag rada sistema |
| **Ne pokretati `makemigrations` za `menice`** bez provere | Nema migracija — [P-45](10-poznati-problemi.md) |
| **Ne uključivati `DEBUG = False`** bez rešavanja medija | Slike i dokumenti prestaju da se prikazuju — [P-01](10-poznati-problemi.md) |
| **Ne menjati vreme Selenium poslova** da se preklope | Jedan radnik, `-P solo` |

---

## 9.10. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako se sistem instalira? | [8. Instalacija i pokretanje](08-instalacija-i-pokretanje.md) |
| Odakle dolaze podaci? | [7. Integracije](07-integracije.md) |
| Šta je poznato kao problem? | [10. Poznati problemi](10-poznati-problemi.md) |
| Kako rade dozvole? | [2.6](02-arhitektura.md#26-kontrola-pristupa) |
