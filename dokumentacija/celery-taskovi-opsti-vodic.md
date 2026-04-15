# Celery taskovi - opsti vodic

Ovaj dokument je prakticni vodic za rad sa Celery taskovima u projektu na Windows serveru.

## 1) Uloga Celery-ja

Celery sluzi da se dugotrajni poslovi izvrse van HTTP request-a.

Primeri:
- import podataka sa eksternih portala.
- sinhronizacija podataka iz drugih sistema.
- periodicne dnevne obrade.

Prednost:
- UI ostaje brz.
- duzi procesi imaju odvojene worker procese.

## 2) Osnovna arhitektura

1. Django aplikacija:
- salje task u queue (`.delay()` ili `apply_async()`).

2. Broker (Redis):
- cuva poruke taskova dok worker ne preuzme posao.

3. Celery worker:
- preuzima task iz queue-a i izvrsava ga.

4. Celery beat:
- periodicki salje taskove po rasporedu.

5. `django-celery-beat`:
- rasporedi se cuvaju u bazi i mogu da se menjaju kroz admin.

## 3) Tipovi taskova u projektu

## 3.1 Selenium taskovi (teski)

Karakteristike:
- browser automation.
- veci CPU/RAM.
- osetljivi na timeout i web promene.

Primeri:
- `run_nis_command`
- `run_omv_putnicka_command`
- `run_omv_teretna_command`
- `kerio_login_task`

Preporuka:
- posebna queue: `selenium`
- poseban worker: `--pool=solo --concurrency=1`

## 3.2 Sync taskovi (laksi)

Karakteristike:
- DB sync, import i domenska obrada.
- krace trajanje od Selenium taskova.

Primeri:
- `fetch_policy_data_task`
- `fetch_service_data_task`
- `fetch_requisition_data_task`
- `fetch_ddor_data_task`
- `sync_hr_employees_task`

Preporuka:
- queue: `sync`
- worker sa manjom paralelizacijom (`--concurrency=1` ili `2`)

## 4) Ključna pravila stabilnosti

1. Ne dozvoli preklapanje istog taska.
Koristi lock (Redis lock + TTL) po task-u.

2. Ne startuj sve dnevne taskove u isti minut.
Stagger schedule na 20-30 min razmaka.

3. Koristi `prefetch_multiplier=1`.
Worker ne "zagrabi" vise taskova unapred nego sto realno moze da obradi.

4. Drzi result backend pod kontrolom.
Ako rezultat nije potreban, koristi `task_ignore_result=True`.

5. Definisi `expire_seconds` za periodic task.
Ako task kasni i postane nerelevantan, ne treba da se izvrsi satima kasnije.

## 5) Preporuceni deployment na Windows-u

Napomena:
Celery nema punu zvanicnu podrsku za Windows, zato je preporuka konzervativan setup.

Pokrenuti odvojene procese:

1. Worker za sync taskove:
```powershell
celery -A ims_fleet worker -n sync@%COMPUTERNAME% -Q sync,default --pool=threads --concurrency=2 --prefetch-multiplier=1 --without-gossip --without-mingle -l INFO
```

2. Worker za selenium taskove:
```powershell
celery -A ims_fleet worker -n selenium@%COMPUTERNAME% -Q selenium --pool=solo --concurrency=1 --prefetch-multiplier=1 --without-gossip --without-mingle -l INFO
```

3. Beat scheduler:
```powershell
celery -A ims_fleet beat --scheduler django_celery_beat.schedulers:DatabaseScheduler -l INFO
```

Servis menadzer:
- NSSM ili WinSW.
- podesiti auto-restart na failure.
- opcionalno nocni kontrolisani restart selenium workera.

## 6) Scheduling smernice (dnevni taskovi)

Primer dnevnog rasporeda:

1. 01:00 `sync_hr_employees_task`
2. 01:30 `fetch_job_codes`
3. 02:00 `fetch_policy_data_task`
4. 02:30 `fetch_service_data_task`
5. 03:00 `fetch_requisition_data_task`
6. 03:30 `fetch_ddor_data_task`
7. 04:00 `run_nis_command`
8. 05:00 `run_omv_putnicka_command`
9. 06:00 `run_omv_teretna_command`

Bitno:
- ne preklapati Selenium taskove.
- ostaviti buffer vreme.

## 7) Monitoring i dijagnostika

Pratiti:

1. duzinu trajanja taskova.
2. broj poruka u queue-u.
3. broj `SKIP` poruka (znak da lock radi i stiti od duplikata).
4. restart count servisa.
5. CPU/RAM tokom selenium intervala.

Ako se javlja zastoj:

1. proveri da li je eksterni portal spor ili nedostupan.
2. proveri da li je chromedriver kompatibilan.
3. proveri Redis dostupnost.
4. smanji paralelizaciju sync workera.
5. produzi lock TTL za konkretan task ako realno traje duze.

## 8) Standard za nove taskove

Kod dodavanja novog taska:

1. Definisi da li je `selenium` ili `sync`.
2. Dodaj route u `CELERY_TASK_ROUTES`.
3. Umotaj task u singleton lock helper sa realnim TTL-om.
4. Dodaj periodic schedule sa razmakom od drugih taskova.
5. Definisi `expire_seconds` u periodic task zapisu.
6. Testiraj i scenario "drugi trigger dok je prvi jos aktivan".

## 9) Bezbednosne preporuke

1. Credentials ne drzati hardkodovano.
2. Koristiti environment varijable za:
- korisnicka imena/lozinke.
- URL-ove i tokene.
3. Ograniciti pristup Redis instanci.
4. Rotirati tajne periodicno.
