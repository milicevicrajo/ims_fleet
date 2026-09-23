# AGENTS.md — uputstvo za rad na IMS ERP sistemu

Namenjeno AI agentima i programerima koji prvi put rade na ovom sistemu.
Cilj: da za 10 minuta znaš gde je šta, šta smeš, a šta ne smeš da diraš.

Puna dokumentacija: [`dokumentacija/docs/`](dokumentacija/docs/).
Inventar celog sistema: [`dokumentacija/00-inventar-i-plan-dokumentacije.md`](dokumentacija/00-inventar-i-plan-dokumentacije.md).

---

## 1. Šta je ovo

Interni ERP sistem Instituta IMS. Django 5.0 monolit, Python 3.12, Microsoft SQL Server,
Celery + Redis, Windows server. Bez REST API-ja — sve je server-side Django templates.

**11 poslovnih modula:** Flota (vozni park), Kadrovi, Finansijska analitika, Nabavka,
Potraživanja, Pravna služba, Ugovori, Menice, Mobilna telefonija, Isplate, Administracija.

Obim: ~59.500 linija Pythona, 351 fajl, 280 šablona, 146 migracija, 550 testova.

---

## 2. Pravila koja se ne krše

| # | Pravilo | Zašto |
|---|---|---|
| 1 | **Nikad ne pokrećeš poslovne procedure na SQL Serveru** (`SPFINizv52`, `53`, `55`, `SPLdKnjizenje`, `sp_AzurirajNalogZ`) osim kroz postojeći servis `finansije.services.nalog_z` | One menjaju poslovne podatke u produkciji |
| 2 | **Nikad ne pišeš u nasleđene `dbo.*` poglede i tabele** | Vlasnik im je stari ERP; aplikacija ih samo čita |
| 3 | **Nikad ne menjaš `nalog_z`, `posao`, `konto`, `partner`, `Zarada`** na povezanim serverima | To je izvor istine knjigovodstva i zarada |
| 4 | **Ne preimenuješ nasleđene poglede na osnovu Django modela** | Model `naplata` navodi `dodela_bucketa`, a stvarni pogled je `dodela_baketa` — model je pogrešan, ne pogled |
| 5 | **Ne menjaš formule obračuna bez pisane potvrde** | Rezultati idu u knjiženje, zarade i izveštaje upravi |
| 6 | **Ne dodaješ `NOLOCK`** u upite nad izvorom | Kontrolni zbirovi se oslanjaju na doslednost čitanja |
| 7 | **Ne uvodiš novi modul `naplata`** | Nasleđen je i gasi se — sav novi rad ide u `potrazivanja` |

---

## 3. Gde je koja logika

Obrazac je dosledan: **`views/` samo prikazuje, `services/` i `support/` računaju.**
Ako tražiš formulu, gledaj u `services/` ili `support/` — ne u `views/`.

| Šta tražiš | Gde je |
|---|---|
| Finansijski obračuni (prihodi, rashodi, ZT, tok gotovine) | `finansije/services/` |
| Obračuni flote (gorivo, trošak/km, kilometraža, održavanje) | `fleet/support/` |
| Preuzimanje podataka iz starog ERP-a | `fleet/sync/external.py`, `fleet/sync/services.py` |
| Selenium preuzimanje goriva (NIS, OMV) | `fleet/sync/selenium.py` |
| Kadrovski obračuni (prolasci, odmori, bolovanja, ocenjivanje) | `hr/services/` |
| Obustave za mobilne telefone | `mobilni/withholdings.py` |
| Generisanje virmana za banku | `isplate/services/virman.py` |
| Sinhronizacija potraživanja | `potrazivanja/services/sync.py` |
| Snimci izvora nabavke (EUF, UF, roba) | `nabavka/services/` |
| Pravni i disciplinski postupci | `pravna/views.py`, `pravna/views_disciplinski.py` |
| Preuzimanje menica iz registra NBS | `menice/scraper.py` |
| Provera partnera u APR-u | `ugovori/apr_openapi.py` |
| Dozvole i uloge | `core/permissions.py`, `core/mixins.py` |
| Zakazani poslovi | `core/management/commands/sync_celery_periodic_tasks.py` |

---

## 4. Podaci — odakle dolaze

Ovo je najvažnija stvar za razumevanje sistema. **Podaci nisu svi lokalni.**

```
┌─ IMS_ERP na SMS-SERVER ────────────────────────────────────────┐
│                                                                │
│  Django tabele (alias: default)                                │
│     fleet_*, hr_*, nabavka_*, finansije_*, potrazivanja_*, ... │
│                                                                │
│  Nasleđeni dbo.* pogledi (alias: server_db — ISTA baza!)       │
│     fleet_tro_svi, dodela_baketa, nbv_roba, hr_employee, ...   │
│         │                                                      │
└─────────┼──────────────────────────────────────────────────────┘
          │ mnogi od ovih pogleda interno čitaju:
          ▼
┌─ POVEZANI SERVERI (linked servers) ────────────────────────────┐
│  PUTGEO-SERVER.bazaims     nalog_z, posao, konto, partner      │  ← knjigovodstvo
│  PUTGEO-SERVER.bazaldims   Zarada, PomLD, Radnik, element      │  ← zarade
│  INFORMATIKA23.ID          Radnici, C_Prolasci_Radnika         │  ← kontrola pristupa
│  SERFIN.bazaldims          radnik                              │  ← kadrovska
└────────────────────────────────────────────────────────────────┘
```

**Posledice na koje moraš da računaš:**

- `default` i `server_db` su **ista fizička baza** `IMS_ERP`. Razdvojeni su namenski:
  `default` za ORM, `server_db` za sirovi SQL nad nasleđenim objektima.
- Finansije i Kadrovi **zavise od tri udaljena servera**. Ako povezani server ne radi,
  sinhronizacija knjiženja i radna lista padaju — to nije greška aplikacije.
- `nalog_z` postoji **dva puta**: kao izvor na `PUTGEO-SERVER.bazaims` i kao lokalna kopija
  `IMS_ERP.dbo.nalog_z`. Finansije čitaju **udaljeni**. Procedura `sp_AzurirajNalogZ`
  osvežava samo lokalnu kopiju i **ne prebacuje** nijedan upit na nju.
- Procedura `sp_AzurirajNalogZ` **ne briše** redove obrisane u izvoru — lokalna kopija
  nije garantovano jednaka izvoru ni posle uspešnog izvršavanja.

---

## 5. Dozvole — kako stvarno rade

Sistem **ne koristi Django `Permission`** za poslovnu logiku.

```
CustomUser ──M2M──► Role ──RolePermission──► PermissionCode
                                                  │
                                     code = NAZIV URL RUTE
                                     npr. "vehicle_list", "nabavka:case_detail"
```

Provera je: *ima li korisnik ijednu aktivnu ulogu koja sadrži kod jednak imenu rute
koja se otvara* (`request.resolver_match.view_name`). `is_superuser` prolazi svuda.

**Ako dodaš novu rutu u `urls.py`, automatski si stvorio novu dozvolu.**
Nova dozvola postaje stvarna tek posle `manage.py sync_permission_codes`
(ili noćnog zadatka u 01:00). Uloga **Uprava** tada automatski dobija **sve** dozvole.

Postoji i drugi sloj — ograničenje po centrima:
`CustomUser.allowed_centers` (M2M) i `CustomUser.allowed_center_codes` (tekst, zarezi).
**Oba postoje paralelno** — pre oslanjanja na jedno, proveri koje modul stvarno koristi.

Zaštita u view-ovima:
```python
from core.mixins import RolePermissionRequiredMixin, role_permission_required

class MojView(LoginRequiredMixin, RolePermissionRequiredMixin, ListView): ...

@role_permission_required()          # kod se izvodi iz imena rute
def moj_view(request): ...
```

---

## 6. Komande

```powershell
# Testovi — UVEK sa testing postavkama (u memoriji, bez SQL Servera)
.\.venv\Scripts\python.exe manage.py test --settings=ims_erp.settings.testing

# Testovi jednog modula
.\.venv\Scripts\python.exe manage.py test finansije core --settings=ims_erp.settings.testing

# Razvojni server (podrazumevano: ims_erp.settings.development → pravi SQL Server!)
.\.venv\Scripts\python.exe manage.py runserver

# Migracije
.\.venv\Scripts\python.exe manage.py migrate

# Dozvole i uloge
.\.venv\Scripts\python.exe manage.py sync_permission_codes

# Zakazani poslovi
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks --dry-run
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks

# Finansije
.\.venv\Scripts\python.exe manage.py sync_finansije --year-from 2026 --year-to 2026
.\.venv\Scripts\python.exe manage.py configure_finansije
```

**Upozorenje:** `manage.py` podrazumevano koristi `ims_erp.settings.development`,
a to je **prava SQL Server baza**, ne lokalna. Za bilo šta eksperimentalno
uvek dodaj `--settings=ims_erp.settings.testing`.

---

## 7. Produkciono okruženje

| Stavka | Vrednost |
|---|---|
| Direktorijum aplikacije | `C:\DjangoApps\ims_erp` |
| Virtuelno okruženje | `C:\DjangoApps\venv` |
| Dnevnici | `C:\DjangoApps\logs` |
| Redis | `C:\Redis\redis-server.exe` |
| Postavke | `ims_erp.settings.production` |

Tri Windows servisa (instalirana preko NSSM, `nssm.bat`):

| Servis | Komanda |
|---|---|
| `IMS_Fleet_Redis` | `redis-server.exe redis.windows.conf` |
| `IMS_Fleet_Celery_Worker` | `celery -A ims_erp worker -l info -P solo -Q default,sync,selenium` |
| `IMS_Fleet_Celery_Beat` | `celery -A ims_erp beat --scheduler django_celery_beat.schedulers:DatabaseScheduler` |

**Bitno:** worker radi sa `-P solo`, dakle **jedan zadatak u jednom trenutku**,
bez obzira na `CELERY_WORKER_CONCURRENCY = 2` u postavkama. Selenium posao koji traje
sat vremena blokira sve ostale zadatke tog radnika.

Posle isporuke novog koda sa novim Celery zadatkom **mora se restartovati worker** —
stari radnik odbacuje nepoznat zadatak.

---

## 8. Zakazani poslovi (18 komada)

Noć: 01:00–07:10 sve sinhronizacije. Dan: 10:00 i 11:00 `nalog_z`, 12:30 putni nalozi,
svaki sat u :20 tekuća godina Finansija.

Zaštita od preklapanja: Redis zaključavanje `ims_erp:task-lock:<task>`
(4 h za Selenium, 90 min za sinhronizacije). Ako Redis padne — **posao se ipak izvršava**
(fail-open). Istorija je u `TaskHistory` (tabela `fleet_task_history`), ekran
`/administracija/task-history/`.

Puna tabela rasporeda: [`dokumentacija/docs/09-odrzavanje.md`](dokumentacija/docs/09-odrzavanje.md).

---

## 9. Zamke koje će te iznenaditi

| # | Zamka |
|---|---|
| 1 | Modeli iz `core/models.py` i `hr/models.py` imaju `app_label = "fleet"` — tabele su `fleet_employee`, `fleet_activity_log`, `fleet_task_history`, ne `core_*` ni `hr_*` |
| 2 | `hr/models.py` definiše `Employee`, ali ga `fleet` uvozi kao `from hr.models import Employee`, dok `CustomUser.employee` pokazuje na `"fleet.Employee"` — isti model, dva imena |
| 3 | Aplikacija `fleet` drži i korenske rute: prijavu, kontrolnu tablu, korisnike, log rada |
| 4 | `izvestaji/` je **prazan direktorijum**, nije Django aplikacija |
| 5 | Bočni meni `kadrovi` nije Django aplikacija — koristi `hr`. Meni `pravna` jeste aplikacija `pravna`, ali uz nju prikazuje i `ugovori` |
| 6 | U obračunu obustava mobilnih jedan broj (`381637781481`) ima poseban tretman upisan u kod |
| 7 | Registarske oznake se normalizuju kroz `fleet/support/vehicle.py: format_license_plate` — nikad ne poredi tablice sirovo |
| 8 | `TrafficCard.for_plate()` namerno **odbija** da pogađa kada tablica pripada većem broju vozila — ne "popravljaj" to |
| 9 | OMV transakcije imaju duplikate i „odjeke“ računa koji se filtriraju u `fleet/support/fuel.py`; sirov `SUM` daje pogrešan rezultat. Dve ulazne tačke: `filter_omv_fuel_queryset()` (čišćenje **+** samo goriva) i `deduplicate_omv_transactions()` (samo čišćenje, za izveštaje sa sopstvenom podelom proizvoda). Ključ za duplikate poredi prazna polja preko `Coalesce` — ne uklanjaj to, jer bez njega `NULL = NULL` izbacuje zapise bez vaučera |
| 10 | Finansije namerno izuzimaju zatvaranja (`ZAT`, konta `59900`/`69900`) — zbir svih stavki klase 5/6 posle zatvaranja godine je nula, što nije greška |

---

## 10. Pre nego što nešto promeniš

1. **Pročitaj postojeće testove** za taj deo — 550 testova opisuje očekivano ponašanje.
2. **Proveri da li podatak dolazi spolja.** Ako da, promena u Django kodu neće pomoći.
3. **Ako menjaš obračun**, proveri da li je opisan u `dokumentacija/docs/obracuni/`
   i ažuriraj i dokumentaciju i kontrolni primer.
4. **Ako dodaješ rutu**, dodaj i dozvolu (`sync_permission_codes`) i uključi je u
   odgovarajuću ulogu; inače je vidi samo `superuser` i uloga Uprava.
5. **Ako dodaješ Celery zadatak**, upiši ga u `EXPECTED_PERIODIC_TASKS` i restartuj worker.
6. **Pokreni testove sa `--settings=ims_erp.settings.testing`.**

7. **Ako menjaš dokumentaciju**, menjaj poglavlja u `dokumentacija/docs/`, pa pokreni
   `python dokumentacija/spoji-dokumentaciju.py`. Objedinjeni
   `dokumentacija/IMS-ERP-dokumentacija.md` se **ne uređuje ručno** — pravi se iz njih.

> **Polazno stanje testova (18.09.2026.):** 550 testova, **4 koja padaju i pre bilo kakve
> izmene** — `fleet.tests.VehicleTravelOrderConsumptionTests.test_datatable_search_finds_order_by_registration_number`,
> dva `mobilni.tests.MobileWithholdingTests` (CSV zaokružuje na ceo dinar, test očekuje dve
> decimale) i `nabavka.tests.ProcurementInvoiceJobCodeLinkTests.test_primary_invoice_job_code_cannot_be_added_as_additional`.
> Ako ti padne baš tih 4 — nisi ti. Ako padne bilo šta peto — jesi.

---

## 11. Poznati rizici u repozitorijumu

Ovo su zatečena stanja, zabeležena radi transparentnosti
(detaljno: [`dokumentacija/docs/10-poznati-problemi.md`](dokumentacija/docs/10-poznati-problemi.md)):

- Pristupni podaci baze i `SECRET_KEY` nalaze se u `ims_erp/settings/` u repozitorijumu.
- `DEBUG = True` je u `base.py` i `production.py` ga ne isključuje.
- `db.sqlite3` i veliki dnevnici (`*.log`) su u radnom direktorijumu iako su u `.gitignore`.
- `djangorestframework` i `psycopg2` su u `requirements.txt`, a ne koriste se.

**Ne ispravljaj ih usput** uz nepovezanu izmenu — to su zasebne odluke sa svojim rizikom
(rotacija lozinki, restart servisa).
