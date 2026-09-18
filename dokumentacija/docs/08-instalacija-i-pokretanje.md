# 8. Instalacija i pokretanje

> **Za koga je ovo poglavlje:** programeri i osoba koja održava server.
> Status tvrdnji: **[P]** potvrđeno kodom/konfiguracijom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 8.1. Šta je potrebno

| Stavka | Verzija | Napomena |
|---|---|---|
| Python | **3.12** | |
| **ODBC Driver 17 for SQL Server** | — | **Bez njega ništa ne radi** |
| Microsoft SQL Server | — | Baza `IMS_ERP` |
| Redis | — | Broker i zaključavanje poslova |
| Google Chrome | Uz odgovarajući upravljač | Samo za preuzimanje goriva |
| NSSM | — | Samo na produkciji, za Windows servise |

Sve biblioteke su u [`requirements.txt`](../../requirements.txt) — **68 paketa**. [P]

---

## 8.2. Razvojno okruženje

```powershell
# 1. Virtuelno okruženje
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Provera ODBC upravljača
Get-OdbcDriver -Name "ODBC Driver 17 for SQL Server"

# 3. Migracije
.\.venv\Scripts\python.exe manage.py migrate

# 4. Server
.\.venv\Scripts\python.exe manage.py runserver
```

> **⚠ Upozorenje [P]:** `manage.py` podrazumevano koristi `ims_erp.settings.development`,
> a to je **prava SQL Server baza** `IMS_ERP` na `SMS-SERVER` — **ne** lokalna kopija.
> Migracije i komande pokrenute bez razmišljanja menjaju produkcione podatke.

### Bezbedan način rada

```powershell
.\.venv\Scripts\python.exe manage.py <komanda> --settings=ims_erp.settings.testing
```

`testing` koristi **SQLite u memoriji**, bez SQL Servera, Redisa i e-pošte. [P]

---

## 8.3. Postavke po okruženjima

| Fajl | Baza | `ALLOWED_HOSTS` | Namena |
|---|---|---|---|
| `base.py` | — | — | Zajedničko; `DEBUG = True`, `SECRET_KEY` |
| `development.py` | **Pravi SQL Server** | `127.0.0.1` | Razvoj |
| `production.py` | Isti SQL Server + nekorišćeni `local` | `ims-flota`, `ims.portal`, `192.168.6.7`, `127.0.0.1`, `localhost` | Produkcija |
| `testing.py` | **SQLite u memoriji** | `testserver`, `localhost`, `127.0.0.1` | Testovi |

**Podrazumevano [P]:** `manage.py` → `development`; `ims_erp/celery.py` → `production`.

### Promenljive okruženja [P]

| Promenljiva | Podrazumevano | Namena |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `ims_erp.settings.development` | Izbor postavki |
| `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` | Redis |
| `CELERY_WORKER_CONCURRENCY` | 2 | **Nema dejstva uz `-P solo`** |
| `MSSQL_DRIVER` | `ODBC Driver 17 for SQL Server` | |
| `MSSQL_QUERY_TIMEOUT` | 90 s | |
| `MSSQL_CONN_MAX_AGE` | 300 s | |
| `FINANSIJE_NALOG_Z_TIMEOUT` | 900 s | Rok za proceduru |
| `MAX_CONTRACT_UPLOAD_SIZE` | 50 MB | Najveći dokument |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | 60 MB | |

> **[P] Bezbednosni nalaz:** lozinke baze i `SECRET_KEY` su **upisani u kod**, ne u
> promenljive okruženja. `python-dotenv` je u zavisnostima, ali se ne koristi.
> Vidi [P-01](10-poznati-problemi.md).

---

## 8.4. Testovi

```powershell
# Svi testovi
.\.venv\Scripts\python.exe manage.py test --settings=ims_erp.settings.testing

# Jedan modul
.\.venv\Scripts\python.exe manage.py test finansije core --settings=ims_erp.settings.testing
```

**550 testova** u 31 fajlu. Izvršavaju se na SQLite bazi u memoriji. [P]

| Modul | Testova |
|---|---|
| `fleet` | 153 |
| `finansije` | 121 |
| `hr` | 97 |
| `potrazivanja` | 59 |
| `mobilni` | 40 |
| `core` | 28 |
| `isplate` | 20 |
| `nabavka` | 19 |
| `ugovori`, `naplata`, `menice` | 13 |

> **[P] Poznat pad testa:** `nabavka.tests.ProcurementInvoiceJobCodeLinkTests.`
> `test_primary_invoice_job_code_cannot_be_added_as_additional` — zabeležen u
> `finansije/README.md` kao postojeći pre uvođenja Finansija.

---

## 8.5. Produkciono okruženje

| Stavka | Putanja |
|---|---|
| Aplikacija | `C:\DjangoApps\ims_erp` |
| Virtuelno okruženje | `C:\DjangoApps\venv` |
| Dnevnici | `C:\DjangoApps\logs` |
| Redis | `C:\Redis\redis-server.exe` |
| NSSM | `C:\nssm\nssm.exe` |
| Postavke | `ims_erp.settings.production` |

### Tri Windows servisa [P]

| Servis | Komanda |
|---|---|
| `IMS_Fleet_Redis` | `redis-server.exe redis.windows.conf` |
| `IMS_Fleet_Celery_Worker` | `celery -A ims_erp worker -l info -P solo -Q default,sync,selenium` |
| `IMS_Fleet_Celery_Beat` | `celery -A ims_erp beat --scheduler django_celery_beat.schedulers:DatabaseScheduler -l info` |

Instalacija: `nssm.bat`. Podešeno: samopokretanje, ponovno pokretanje posle 5 s,
rotacija dnevnika na 10 MB. [P]

> **[N] Web server nije zabeležen.** `wsgi.py` postoji, ali u projektu nema
> konfiguracije IIS-a ni drugog servera. Treba dopuniti.

---

## 8.6. Prvo puštanje u rad

```powershell
# 1. Baza i struktura
.\.venv\Scripts\python.exe manage.py migrate

# 2. Šifarnik organizacionih jedinica
.\.venv\Scripts\python.exe manage.py fetch_job_codes

# 3. Zaposleni
.\.venv\Scripts\python.exe manage.py sync_hr_employees

# 4. Dozvole i uloge
.\.venv\Scripts\python.exe manage.py sync_permission_codes

# 5. Korisnički nalozi za zaposlene
.\.venv\Scripts\python.exe manage.py create_employee_users

# 6. Raspored poslova
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks

# 7. Finansije
.\.venv\Scripts\python.exe manage.py configure_finansije
.\.venv\Scripts\python.exe manage.py sync_finansije

# 8. Potraživanja
.\.venv\Scripts\python.exe manage.py initialize_potrazivanja
.\.venv\Scripts\python.exe manage.py configure_potrazivanja

# 9. Šifarnici
.\.venv\Scripts\python.exe manage.py import_work_time_catalog <putanja>
.\.venv\Scripts\python.exe manage.py import_evaluation_catalog <putanja>
.\.venv\Scripts\python.exe manage.py load_konta_vozila

# 10. Servisi
.\nssm.bat
```

> **⚠ Korak koji će zakazati [P]:** aplikacija **`menice` nema migracije**, pa korak 1
> **neće stvoriti** tabele `menica` i `ulazna_menica`. Vidi [P-45](10-poznati-problemi.md).

---

## 8.7. Struktura projekta

```
ims_erp/          Konfiguracija (settings, urls, celery, wsgi)
core/             Korisnici, uloge, dozvole, evidencija rada
fleet/            Vozni park + korenske rute
hr/               Kadrovi
finansije/        Finansijska analitika
nabavka/          Nabavka
potrazivanja/     Potraživanja
ugovori/          Partneri i ugovori
menice/           Menice  ← bez migracija
mobilni/          Mobilna telefonija
isplate/          Virmani (bez tabela)
naplata/          NASLEĐENO — u gašenju
templates/        Globalni šabloni i bočni meniji
media/            Otpremljeni fajlovi
logs/             Dnevnici
dokumentacija/    Dokumentacija
chrome-for-testing/  Chrome za Selenium
```

---

## 8.8. Provera da sve radi

| # | Provera | Očekivano |
|---|---|---|
| 1 | Otvoriti `/login/` | Ekran za prijavu |
| 2 | Prijaviti se | Kontrolna tabla flote |
| 3 | Otvoriti `/administracija/task-history/` | Spisak poslova |
| 4 | Otvoriti `/finansije/sinhronizacija/` | Istorija i kontrolni zbirovi |
| 5 | `Get-Service IMS_Fleet_*` | Tri servisa rade |
| 6 | Pokrenuti lak posao ručno | Status **Uspešan** u istoriji |
| 7 | Otvoriti `/potrazivanja/` | Datum poslednjeg objavljenog snimka |

---

## 8.9. Šta treba dopuniti u ovoj dokumentaciji

| # | Nedostaje | Potrebno od |
|---|---|---|
| 1 | **Konfiguracija web servera** (IIS ili drugi) | Održavanje |
| 2 | **Postupak izrade rezervne kopije** baze i direktorijuma `media/` | Održavanje |
| 3 | Gde se čuvaju pristupni podaci za NIS i OMV portale | **Q7** |
| 4 | Ko i kako obnavlja lozinke portala | **Q7** |
| 5 | Postupak vraćanja na prethodnu verziju koda | Održavanje |

---

## 8.10. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako se sistem održava iz dana u dan? | [9. Održavanje](09-odrzavanje.md) |
| Kako je sastavljen? | [2. Arhitektura](02-arhitektura.md) |
| Šta je poznato kao problem? | [10. Poznati problemi](10-poznati-problemi.md) |
| Pravila za programere | [AGENTS.md](../../AGENTS.md) |
