# Celery - sta je uradjeno

Datum: 2026-04-06
Projekat: `ims_erp`

## Cilj

Stabilizacija Celery taskova na Windows serveru, sa fokusom na:

1. Sprecavanje preklapanja istog taska kada prethodni zapne.
2. Razdvajanje teskih i lakih taskova po queue-ovima.
3. Smanjenje opterecenja Redis-a i workera.
4. Cistija Celery inicijalizacija bez nepotrebnog output-a pri import-u.

## Uradjene izmene u kodu

## 1) `ims_erp/celery.py`

Uklonjeni su debug `print` pozivi pri inicijalizaciji Celery aplikacije.

Pre:
- stampanje broker URL-a i liste registrovanih taskova na import.

Posle:
- `app = Celery('ims_erp')`
- `app.config_from_object(...)`
- `app.autodiscover_tasks()`
- bez automatskog printovanja pri svakom startu procesa.

Efekat:
- cistiji logovi.
- manje suma pri restartu servisa.

## 2) `ims_erp/settings/base.py`

Dodata su produkciona Celery podesavanja za stabilniji rad na Windows-u.

Ključne stavke:

1. Broker/backend preko env var:
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

2. Windows-friendly throttling:
- `CELERY_WORKER_CONCURRENCY` (default `2`)
- `CELERY_WORKER_PREFETCH_MULTIPLIER` (default `1`)
- `CELERY_BROKER_POOL_LIMIT` (default `5`)
- `CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True`

3. Rasterecenje result backend-a:
- `CELERY_TASK_IGNORE_RESULT = True` (po default-u)
- `CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED = True`
- `CELERY_RESULT_EXPIRES = 3600`

4. Routing taskova po queue-ovima:
- `selenium` queue za teske web-automation taskove.
- `sync` queue za regularne sync taskove.
- `default` kao podrazumevani fallback.

Efekat:
- tezak Selenium vise ne gusi lake sync taskove.
- manje gomilanje poruka i manje drzanih rezultata u Redis-u.

## 3) `fleet/tasks.py`

Implementiran je singleton lock mehanizam za sve bitne taskove.

Nova pomocna funkcija:
- `_run_with_singleton_lock(task_name, lock_ttl_seconds, fn)`

Kako radi:
1. Pokusava da uzme Redis lock (`blocking=False`) za konkretan task.
2. Ako lock vec postoji, task se preskace i vraca poruku:
   `SKIP: task '<ime>' je vec aktivan.`
3. Ako lock servis nije dostupan, radi se `fail-open` (task ipak ide).
4. Lock ima TTL, pa se automatski oslobadja i u slucaju pada procesa.

Taskovi koji su obuhvaceni lock-om:

1. Selenium grupa:
- `run_nis_command` (TTL 4h)
- `run_omv_putnicka_command` (TTL 4h)
- `run_omv_teretna_command` (TTL 4h)
- `kerio_login_task` (TTL 30m)

2. Sync grupa:
- `fetch_policy_data_task` (TTL 90m)
- `fetch_service_data_task` (TTL 90m)
- `fetch_requisition_data_task` (TTL 90m)
- `fetch_ddor_data_task` (TTL 90m)
- `fetch_job_codes` (TTL 60m)
- `proveri_otpis` (TTL 60m)
- `sync_hr_employees_task` (TTL 90m)
- `sync_permission_codes_task` (TTL 30m)

Efekat:
- ako dnevni task zakoci, sledeci termin ne pravi paralelni duplikat.
- drasticno manji rizik od "lančanog haosa" i zapusenja queue-a.

## Operativne preporuke (dogovoreni nacin rada)

Iako su taskovi dnevni, treba izbeci istovremeni start svih taskova.

Preporuka:

1. Dnevne taskove rasporediti sa razmakom 20-30 minuta.
2. `selenium` worker drzati odvojeno od `sync` workera.
3. `selenium` worker pokretati sa `--pool=solo --concurrency=1`.
4. Za periodic taskove postaviti `expire_seconds` da stari job ne krece kasno.
5. Uvesti auto-restart servisa jednom dnevno van radnog vremena.

## Brza provera nakon deploy-a

1. Da li su worker-i podignuti na odvojenim queue-ovima:
- `sync/default`
- `selenium`

2. Da li u logu postoje `SKIP: task ... je vec aktivan` poruke kada task kasni.

3. Da li Redis nema nekontrolisan rast kljuceva rezultata.

4. Da li se taskovi zavrsavaju bez paralelnih duplikata.

## Napomena

U kodu postoje hardkodovani kredencijali u nekim integracijama (npr. Selenium login podaci). Sledeci bezbednosni korak je prebacivanje svih tajni u environment varijable.
