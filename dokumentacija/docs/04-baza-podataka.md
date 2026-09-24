# 4. Baza podataka

> **Za koga je ovo poglavlje:** programeri, administratori baze, AI agenti.
> Status tvrdnji: **[P]** potvrđeno kodom/migracijama, **[Z]** zaključeno, **[N]** nepotvrđeno.
>
> Ovo poglavlje opisuje **šta koja tabela znači poslovno** i **koji ključ je čini jedinstvenom**.
> Iscrpan spisak svake kolone je u izvornom kodu modela — putanja je navedena uz svaku grupu.

---

## 4.1. Osnovno

| Stavka | Vrednost | Status |
|---|---|---|
| Motor | Microsoft SQL Server | [P] |
| Baza | `IMS_ERP` na serveru `SMS-SERVER` | [P] |
| Django adapter | `mssql-django` 1.5, ODBC Driver 17 | [P] |
| Sopstvenih Django tabela | 118 | [P] |
| Modela nad nasleđenim pogledima (`managed = False`) | 13 | [P] |
| Apstraktnih modela (bez tabele) | 3 | [P] |
| Nasleđenih `dbo.*` objekata koji se čitaju sirovim SQL-om | 37 | [P] |
| Migracija | 146 | [P] |

### 4.1.1. Dva aliasa, jedna baza [P]

| Alias | Namena |
|---|---|
| `default` | Django ORM i migracije |
| `server_db` | Sirovi SQL nad nasleđenim `dbo.*` objektima |

Oba pokazuju na **istu fizičku bazu** `IMS_ERP`. Django tabele i nasleđeni objekti starog
ERP-a žive jedni pored drugih. Django migracije **ne diraju** nasleđene objekte.

### 4.1.2. Povezani serveri [P]

Deo `dbo.*` pogleda u `IMS_ERP` interno čita udaljene servere, a neki moduli ih čitaju direktno:

| Povezani server | Baza | Objekti | Ko čita direktno |
|---|---|---|---|
| `PUTGEO-SERVER` | `bazaims` | `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | `finansije/services/source.py`, `potrazivanja/services/source.py` |
| `PUTGEO-SERVER` | `bazaldims` | `Zarada`, `PomLD`, `Radnik`, `element` | `finansije/services/job_people.py`, `cash_flow.py` |
| `INFORMATIKA23` | `ID` | `Radnici`, `C_Prolasci_Radnika`, `C_Tasteri`, `c_parovi_radnika_detalji` | `hr/services/attendance.py` |
| `SERFIN` | `bazaldims` | `radnik` | `hr/services/attendance.py` |

---

## 4.2. Pravilo imenovanja tabela — obavezno pročitati [P]

Django podrazumevano imenuje tabelu `<app_label>_<model>`. U ovom projektu **`app_label`
nije uvek jednak direktorijumu aplikacije**:

| Model je definisan u | `app_label` | Tabela |
|---|---|---|
| `core/models.py` (svi modeli) | `fleet` | `fleet_customuser`, `fleet_role`, `fleet_permissioncode`, `fleet_rolepermission`, `fleet_organizationalunit` |
| `core/models.py: ActivityLog` | `fleet` | **`fleet_activity_log`** (izričit `db_table`) |
| `core/models.py: TaskHistory` | `fleet` | **`fleet_task_history`** (izričit `db_table`) |
| `hr/models.py: Employee`, `EmployeeCVItem` | `fleet` | `fleet_employee`, `fleet_employeecvitem` |
| `hr/models.py: ostali` | `hr` | `hr_worktimesheet`, `hr_sickleave`, … |
| `nabavka/models.py` | `nabavka` | izričiti `db_table`: `nabavka_procurement_case`, `nabavka_invoice`, … |
| `ugovori/models.py` | `ugovori` | izričiti `db_table`: `ugovori_partner`, `ugovori_contract`, … |
| `menice/models.py` | `menice` | izričiti `db_table`: **`menica`**, **`ulazna_menica`** (bez prefiksa) |
| `naplata/models.py` | `naplata` | izričiti `db_table`: **`postupak`**, **`promena_postupka`**, **`avans_klijent`** |

**Posledica [Z]:** pretraga po imenu tabele može da promaši. `fleet_employee` je kadrovska
tabela; `menica` i `postupak` nemaju prefiks aplikacije.

---

## 4.3. Zajedničke osnove — `core` (tabele u `fleet_*`)

Izvorni kod: [`core/models.py`](../../core/models.py)

### `fleet_organizationalunit` — organizaciona jedinica / šifra posla

Centralni šifarnik na koji se vezuju vozila, putni nalozi, radne liste, nabavka i finansije.

| Kolona | Tip | Poslovno značenje |
|---|---|---|
| `code` | `char(10)`, **jedinstveno** | Šifra organizacione jedinice (šifra posla) |
| `name` | `char(100)` | Naziv |
| `center` | `char(10)` | **Šifra centra** — koristi se za ograničenje pristupa i brojanje dokumenata |

Puni ga sinhronizacija iz `dbo.v_organizationalunit` (`sif_pos`, `naz_pos`, `blok`),
dnevno u 01:30. [P] Redovi sa praznim poljima se **preskaču**, ne upisuju. [P]

> **Pažnja [P]:** u Finansijama centar **ne dolazi** iz ove tabele nego iz aktuelnog
> `posao.blok` na izvoru. Promena centra u šifarniku pregrupiše celu istoriju.

### `fleet_customuser` — korisnik sistema

Zamenjuje Django `User` (`AUTH_USER_MODEL = 'fleet.CustomUser'`). [P]

| Kolona | Poslovno značenje |
|---|---|
| `employee_id` | Veza 1:1 ka `fleet_employee` — povezuje nalog sa zaposlenim |
| `allowed_center_codes` | Šifre centara, odvojene zarezima |
| `allowed_hr_unit_codes` | JSON lista kadrovskih OJ; pojedinačna ograničenja za modul Kadrovi |
| `must_change_password` | Prisiljava promenu lozinke pri prijavi |
| M2M `fleet_customuser_allowed_centers` | Dozvoljene organizacione jedinice |
| M2M `fleet_customuser_roles` | Dodeljene uloge |

> **[N]** Postoje **dva** mehanizma za centre (`allowed_centers` i `allowed_center_codes`).
> Koji je merodavan u kom modulu nije potvrđeno — pitanje **Q5**.

### `fleet_role`, `fleet_permissioncode`, `fleet_rolepermission` — dozvole

| Tabela | Sadržaj |
|---|---|
| `fleet_role` | Uloga: `name`, `slug` (jedinstven), `is_active` |
| `fleet_permissioncode` | `code` (jedinstven) = **ime URL rute**, `label` |
| `fleet_rolepermission` | Veza uloga ↔ dozvola, jedinstveno po paru |

Kodovi se generišu automatski iz `urlpatterns`. Vidi [2.6](02-arhitektura.md#26-kontrola-pristupa).

### `fleet_activity_log` — evidencija rada korisnika

Popunjava je `ActivityLogMiddleware` posle svakog odgovora. [P]

| Kolona | Značenje |
|---|---|
| `action` | `request`, `login`, `logout`, `login_failed`, `manual` |
| `actor_username`, `actor_display_name` | Sačuvani i kad se korisnik kasnije obriše |
| `app_label`, `view_name`, `method`, `path`, `status_code` | Šta je otvoreno |
| `object_model`, `object_pk`, `object_repr` | Nad kojim zapisom |
| `changes` | JSON sa izmenama |
| `ip_address`, `user_agent` | Odakle |

Indeksi: po korisniku, po akciji i po aplikaciji — svi uz `-created_at`. [P]

### `fleet_task_history` — istorija pozadinskih poslova

| Kolona | Značenje |
|---|---|
| `task_id` | Jedinstven Celery ID |
| `task_name`, `display_name` | Tehnički i prikazni naziv (iz rasporeda) |
| `status` | `started`, `success`, `skipped`, `failure` |
| `short_message`, `result`, `error` | Ishod |
| `started_at`, `finished_at`, `elapsed_seconds` | Trajanje |

Status `skipped` znači da je posao preskočen jer je prethodni još radio. [P]

---

## 4.4. Vozni park — `fleet`

Izvorni kod: [`fleet/models.py`](../../fleet/models.py)

### 4.4.1. Vozilo i dokumenti

#### `fleet_vehicle` — vozilo

| Kolona | Poslovno značenje |
|---|---|
| `chassis_number` | **Broj šasije — jedinstven, obavezan.** Pravi identitet vozila |
| `inventory_number` | Inventarski broj (jedinstven, može biti prazan) — veza sa knjigovodstvom |
| `engine_number` | Broj motora (jedinstven, može biti prazan) |
| `category` | `putnicko`, `teretno`, `prikljucno` |
| `brand`, `model`, `year_of_manufacture`, `first_registration_date` | Osnovni podaci |
| `engine_volume`, `engine_power`, `weight`, `maximum_permissible_weight`, `load_capacity`, `number_of_axles`, `number_of_seats`, `fuel_type`, `color`, `homologation_number` | Tehnički podaci |
| `purchase_value` | Nabavna vrednost |
| `value` | **Knjigovodstvena vrednost** — puni je sinhronizacija iz `dbo.vrednost_vozila` |
| `service_interval` | Servisni interval u km, podrazumevano **15.000** |
| `purchase_date`, `partner_code`, `partner_name`, `invoice_number` | Podaci o nabavci |
| `otpis` | **Otpisano** — `editable=False`, postavlja ga samo sinhronizacija iz `dbo.fleet_otpis` |

> **[P]** `Vehicle.__str__` prikazuje registarsku oznaku iz **izdate** saobraćajne
> (`issue_date <= danas`), a ako je nema — broj šasije.
>
> **[P]** `maximum_permissible_weight` nije samo tehnički podatak: od njega zavisi
> **prag fiksnog troška po kilometru** (vidi obračun V-11).

#### `fleet_trafficcard` — saobraćajna dozvola

Istorijska tabela: jedno vozilo ima više saobraćajnih kroz vreme, sa različitim tablicama.

| Kolona | Poslovno značenje |
|---|---|
| `registration_number` | Registarska oznaka, format `AA999-AA` ili `AA9999-AA` (validator) |
| `issue_date` | Datum izdavanja — **ne sme biti u budućnosti** |
| `valid_until` | Rok dokumenta — ne sme biti pre datuma izdavanja |
| `registration_valid_until` | Registracija važi do |
| `traffic_card_number`, `serial_number`, `owner` | Podaci sa dokumenta |
| `traffic_card_pdf`, `traffic_card_front_image`, `traffic_card_back_image` | Prilozi |

Kontrole u `clean()` [P]:

1. Tablica se normalizuje kroz `format_license_plate()`.
2. **Ista tablica ne sme pripadati drugom vozilu** — inače: *„Ove tablice su već povezane
   sa drugim vozilom. Potrebna je provera istorije.“*
3. Rok ne sme biti pre izdavanja; izdavanje ne sme biti u budućnosti.

Poseban upit `for_plate()` [P] razrešava tablicu u vozilo kroz istoriju dokumenata i
**namerno odbija da pogađa** kada tablica pripada većem broju vozila
(`MultipleObjectsReturned`). To je zaštita, ne greška.

Indeks: `(vehicle, -issue_date, -id)`. [P]

#### `fleet_vehicletenderdocument` — tenderska dokumentacija

Slike tablica, nalepnica i ostalo, za potrebe tendera. Stara slika se briše tek posle
potvrde transakcije (`transaction.on_commit`). [P]

### 4.4.2. Pripadnost i raspolaganje

#### `fleet_jobcode` — dodela vozila organizacionoj jedinici (istorijska)

| Kolona | Značenje |
|---|---|
| `vehicle_id`, `organizational_unit_id` | Vozilo i OJ |
| `assigned_date` | **Datum dodele** |

Jedinstveno: `(vehicle, assigned_date)`. [P]
Važenje dodele traje **do dana pre sledeće dodele**. [P]

> Ovo je osnova za sve izveštaje „po šifri posla“ — trošak vozila pripada onoj OJ koja je
> bila dodeljena **na datum troška**, a ne trenutnoj.

Dnevno se osvežava iz `dbo.sif_pos_trenutno` (`regbr`, `sifpos`); nova dodela se upisuje
**samo ako se razlikuje od poslednje**. [P]

#### `fleet_vehicleholding` — osnov raspolaganja vozilom

| Kolona | Značenje |
|---|---|
| `basis` | `owned` (vlasništvo IMS) ili `contract` (korišćenje po ugovoru) |
| `start_date`, `end_date` | Period (uključivo); `end_date` prazan = još traje |
| `lease_id` | Obavezan za `contract` |
| `financing` | `own_funds` ili `credit` — samo za vlasništvo IMS |
| `financing_contract_id` | Samo uz `credit` |
| `evidence`, `note` | Osnov promene |

Kontrole [P]:

1. Kraj ne sme biti pre početka (i kao `CheckConstraint` u bazi).
2. Za `contract`: ugovor mora pripadati **tom** vozilu, a period raspolaganja mora biti
   **unutar** perioda ugovora.
3. Za `owned`: ne sme se birati ugovor o korišćenju.
4. Ugovor o finansiranju samo uz `credit`.
5. **Periodi se ne smeju preklapati** — provera uz `select_for_update()` nad vozilom.

#### `fleet_lease` — lizing / najam

| Kolona | Značenje |
|---|---|
| `lease_type` | `finansijski`, `operativni`, `dugorocni` (dugoročni najam) |
| `partner_code`, `partner_name` | Davalac |
| `job_code` | Šifra posla (tekst, ne veza) |
| `contract_number` | Broj ugovora (tekst) |
| `contract_id` | Veza ka `ugovori_contract` (opciona) |
| `current_payment_amount` | **Trenutna rata** |
| `start_date`, `end_date` | Period |

`is_long_term_rental` je `True` za `dugorocni`, `dugoročni`, `dugoročnI` — tri zapisa
zbog istorijskih podataka sa dijakriticima. [P]

#### `fleet_leaseinterest` — kamata po godini

Jedinstveno `(year, lease)`. Puni se iz `dbo.lizing_kamate`. [P]

### 4.4.3. Osiguranje

| Tabela | Uloga |
|---|---|
| `fleet_policy` | **Polisa** — premija, rate, period, obnavljanje; ključ je `invoice_id` (jedinstven) |
| `fleet_draftinsurance` | Nedovršeno knjiženje osiguranja iz `dbo.fleet_potrazivanje_ddor` |
| `fleet_insurance` | Konačno knjiženje osiguranja |

`fleet_insurance` jedinstveno po `(god, sif_vrs, br_naloga, stavka, knt)` — to je
**izvorni ključ knjiženja**. [P] Ista petorka se koristi i za proveru da li draft već postoji.

`Policy.incomplete_q()` i `is_complete()` definišu šta je „nedovršena polisa“ —
13 obaveznih polja. [P] Ekran `/polise/nedovrseno/` koristi upravo taj uslov.

### 4.4.4. Gorivo

| Tabela | Uloga | Izvorni ključ |
|---|---|---|
| `fleet_transactionomv` | Sirove transakcije sa OMV kartica | `(license_plate_no, transaction_date, product_inv, voucher, quantity)` |
| `fleet_transactionnis` | Sirove transakcije sa NIS kartica | `(datum_transakcije, registarska_oznaka_vozila, naziv_proizvoda)` |
| `fleet_fuelconsumption` | Objedinjena potrošnja po vozilu | `(vehicle, supplier, date, amount, fuel_type)` |

`fleet_fuelconsumption` kolone: `date`, `amount` (količina), `fuel_type`,
`cost_bruto`, `cost_neto`, `supplier`, `job_code`, `mileage`.

> **[P] Važno:** OMV transakcije sadrže duplikate i „odjeke“ računa. Sirov `SUM` nad
> `fleet_transactionomv` daje **pogrešan** iznos. Filteri su u
> [`fleet/support/fuel.py`](../../fleet/support/fuel.py) — vidi obračune V-03 do V-06.

### 4.4.5. Održavanje i garaža

| Tabela | Uloga |
|---|---|
| `fleet_servicetype` | Šifarnik tipova servisa (jedinstven naziv) |
| `fleet_service` | Servis: datum, trošak, dobavljač |
| `fleet_servicetransaction` | **Knjiženje servisa** iz `dbo.fleet_servisi` |
| `fleet_draftservicetransaction` | Nedovršeno knjiženje servisa |
| `fleet_requisition` | **Trebovanje** materijala iz `dbo.fleet_trebovanja` |
| `fleet_kvar` | Prijava kvara (garaža) |
| `fleet_kvarpart` | Stavke delova uz prijavu kvara |
| `fleet_procurementrequest` | Zahtev za nabavku iz garaže (GZN) |
| `fleet_procurementitem` | Stavke zahteva |
| `fleet_kontavozila` | Šifarnik konta vozila (PK je `knt`) |

Ključevi [P]:

- `fleet_servicetransaction` i `fleet_draftservicetransaction`:
  `(datum, duguje, vez_dok, br_naloga)`.
- `fleet_requisition`: `(sif_pred, god, br_dok, sif_vrsart, stavka)` — izvorni red.

Brojevi dokumenata [P]:

| Model | Format | Kada se dodeljuje |
|---|---|---|
| `Kvar.rbz` | `PK-<pk>/<godina>` | Posle prvog upisa |
| `ProcurementRequest.number` | `GZN-<pk>/<godina>` | Posle prvog upisa |
| `VehicleTravelOrder.pn_number` | redni broj + `rbz` = `PN-<broj>` | Uz `select_for_update()` |

`Kvar.work_type`: `mali_servis`, `veliki_servis`, `popravka`. `van_ims` označava popravku
izvan IMS garaže. [P]

### 4.4.6. Putni nalozi

#### `fleet_putninalog` — službeno putovanje zaposlenog

| Kolona | Poslovno značenje |
|---|---|
| `order_number` | **Broj naloga, jedinstven**, format `<centar>/<godina>-<redni broj>` |
| `employee_id` / `other_employee_name` | Zaposleni IMS ili spoljno lice |
| `job_code_id` | **„Troškovi idu na teret“** — organizaciona jedinica |
| `travel_location`, `task`, `contract_offer`, `napomena` | Podaci o putovanju |
| `vehicle_id` / `other_vehicle` | Vozilo IMS ili drugo prevozno sredstvo |
| `travel_date`, `number_of_days` | Period |
| `advance_payment`, `advance_payment_currency` | **Akontacija** (RSD/EUR/USD) |
| `isplaceno` | **Isplaćeno** — `editable=False`, puni sinhronizacija iz `dbo.fleet_zatvoren_putni` |
| `daily_allowance` | Dnevnica, podrazumevano **2.600** |
| `is_weekly` | Nedeljni nalog |
| `opravdan` | Pravdanje naloga |
| `storniran` | Storniran |
| `virman_generated`, `virman_generated_at`, `virman_generated_by` | Trag generisanja virmana |

Dodela broja (`generate_order_number`) [P]:

1. Uzima `center` iz izabrane OJ; bez centra — greška.
2. Prefiks je `<centar>/<godina putovanja>-`.
3. Traži najveći postojeći broj sa tim prefiksom i dodaje 1.
4. Ako za tu godinu nema nijednog, a za centar postoje raniji nalozi — kreće od 1.
5. Ako nema nijednog naloga za centar i nije zadat početni broj — **greška**:
   *„Nedostaje početni broj za izabrani centar/godinu.“*

Pomoćna tabela `fleet_putninalogsequence` drži `(center_code, year, next_number)`. [P]

> **[Z]** Numeracija se izvodi iz postojećih brojeva, a ne iz brojača, pa brisanje
> poslednjeg naloga oslobađa njegov broj za sledeći nalog.

#### `fleet_vehicletravelorder` — zaduženje vozila

Ko je i kada zadužio vozilo, sa početnom i krajnjom kilometražom.

| Kolona | Značenje |
|---|---|
| `pn_number` | Redni broj zaduženja (jedinstven) |
| `rbz` | `PN-<broj>` (jedinstven) |
| `created_at`, `closed_at` | Otvaranje i zatvaranje |
| `start_mileage`, `end_mileage` | Kilometraža |
| `employee_id`, `vehicle_id` | Ko i šta |

### 4.4.7. Ostalo

| Tabela | Uloga |
|---|---|
| `fleet_incident` | Prekršaj: zaposleni, vozilo, opis, datum, lokacija, iznos kazne |
| `[dbo].[kasko_rate]` | `managed = False` — kasko rate po ugovoru i godini |

---

## 4.5. Kadrovi — `hr`

Izvorni kod: [`hr/models.py`](../../hr/models.py), [`hr/evaluation_models.py`](../../hr/evaluation_models.py)

### `fleet_employee` — zaposleni

> Tabela je u `fleet_*` iako je model u `hr` (vidi 4.2).

| Kolona | Poslovno značenje |
|---|---|
| `employee_code` | **Šifra zaposlenog — jedinstvena.** Ključ prema kadrovskoj bazi |
| `original_full_name` | Ime i prezime kako stoji u izvoru |
| `first_name`, `last_name` | Razdvojeno ime i prezime |
| `display_first_name_override`, `display_last_name_override` | **Ispravka za prikaz** koju unosi zaposleni |
| `skip_hr_identity_update` | Ako je uključeno, sinhronizacija **ne menja** titulu, ime, prezime i pol |
| `position`, `department_code`, `org_unit_code`, `system_code`, `system_name` | Organizaciona pripadnost |
| `job_code`, `job_title` | Zanimanje |
| `status_code`, `status_name` | Status u kadrovskoj evidenciji |
| `recipient_code`, `recipient_name` | **Vrsta primaoca** — određuje elemente radne liste |
| `personal_number` | JMBG |
| `account_number` | **Partija (tekući račun)** — koristi se za virman, mora imati 18 cifara |
| `residence_municipality` | Opština boravka — ide u virman |
| `date_of_birth`, `date_of_joining`, `gender`, `address`, `education`, `slava` | Lični podaci |
| `phone_number`, `mobile_phone` | Kontakt |
| `is_active` | Aktivan |

`display_first_name` / `display_last_name` [P]: vraćaju ispravku ako postoji, inače izvorno ime.
`__str__` je `"<prezime> <ime>"`.

> **[P]** `skip_hr_identity_update` postoji jer zaposleni može ispraviti svoje ime u
> aplikaciji, a noćna sinhronizacija bi ga inače vratila na izvornu vrednost.

### `fleet_employeecvitem` — stavka CV-a

Naziv posla/projekta, organizacija, uloga, period, opis, znanja i veštine.
Unosi je **sam zaposleni** na svom profilu. [P]

### Radne liste

| Tabela | Uloga |
|---|---|
| `hr_worktimesheet` | Mesečna radna lista: zaposleni, godina, mesec, status |
| `hr_worktimesheetline` | Red radne liste: šifra posla + 31 kolona sati |
| `hr_worktimecategory` | Šifarnik „Vrsta rada / odsustva“ |
| `hr_worktimeelement` | Element za obračun zarada: vrsta primaoca + `payroll_code` + `payroll_name` |
| `hr_recipienttype` | Šifarnik vrsta primalaca |

`hr_worktimesheet` [P]:

- Jedinstveno `(employee, year, month)`.
- `status`: `draft` (popunjava se), `submitted` (predato), `approved` (odobreno).
- `meal_days` + `meal_organizational_unit` — **topli obrok**: broj dana i šifra posla.
- `field_allowance_days` — **terenski dodatak**: broj dana.
- `created_by`, `updated_by` — trag korisnika.

`hr_worktimesheetline` [P]:

- Jedinstveno `(sheet, line_number)`.
- Kolone `day_1` … `day_31`, svaka `0–24` (validator `MaxValueValidator(24)`).
- **Celobrojne su** — nema polovina sata.
- `work_category_id` → prikazana „napomena“ reda.
- `total_hours` = zbir svih 31 dana (prazna vrednost se računa kao 0).

`hr_worktimeelement` jedinstveno po `(recipient_type, payroll_code)`. [P]

### Godišnji odmori

| Tabela | Uloga | Izvorni ključ |
|---|---|---|
| `hr_annualleaveallowance` | **Dodela** dana odmora po godini | `(company_code, year, employee_code)` |
| `hr_annualleavedecision` | **Rešenje** o korišćenju | `(company_code, year, employee_code, source_start_key)` |
| `hr_annualleavesync` | Istorija sinhronizacije | |

`source_start_key` je `char(26)` i čuva **tačan vremenski deo izvornog ključa**, nezavisno
od prikaza i vremenskih zona. [P] To sprečava dupliranje rešenja zbog pomeranja sata.

`hr_annualleavedecision` ima `CheckConstraint`: `end_date >= start_date`. [P]

Oba modela nasleđuju `AnnualLeaveSourceRecord` sa poljima `source_present` (da li je red
još u izvoru) i `last_seen_at`. **Nestali red se ne briše**, označi se kao odsutan. [P]

### Bolovanja

| Tabela | Uloga |
|---|---|
| `hr_sickleaveimport` | Jedan uvoz RFZO datoteke: naziv, hash, datum izvoza, brojači |
| `hr_sickleave` | Pojedinačno bolovanje |

`hr_sickleave` [P]:

| Kolona | Značenje |
|---|---|
| `rfzo_id` | **Jedinstven ID iz RFZO izvoza** |
| `employee_id` | Veza ka zaposlenom (može biti prazna — nepovezano) |
| `personal_number` | JMBG iz izvora (osnov povezivanja) |
| `start_date`, `end_date` | Period; kraj može biti prazan (bolovanje traje) |
| `source_status`, `source_total_days`, `source_date` | Podaci iz izvora |
| `matching_note` | Kako je povezano |

`CheckConstraint`: `end_date >= start_date` ili prazno. [P]
`masked_personal_number` prikazuje samo poslednje 4 cifre JMBG-a. [P]

`file_hash` u uvozu omogućava prepoznavanje ponovljene datoteke. [P]

### Ocenjivanje

| Tabela | Uloga |
|---|---|
| `hr_evaluationgroup` | Grupa za ocenjivanje |
| `hr_evaluationcriterion` | **Merilo** — šifra, naziv (ćirilica), redosled |
| `hr_evaluationscale` | **Skala**: grupa × merilo × bodovi (0–4) → koeficijent |
| `hr_evaluationunitsetup` | Po OJ: neposredni rukovodilac, direktor centra, generalni direktor |
| `hr_evaluationemployeesetup` | Kojoj grupi zaposleni pripada |
| `hr_employeeevaluation` | **Ocena** — nepromenljiv snimak |
| `hr_evaluationapproval` | Saglasnost po nivou |

`hr_evaluationscale` [P]: jedinstveno `(group, criterion, points)`;
`points` 0–4; `coefficient` je `decimal(8,5)`.

`hr_employeeevaluation` [P]:

| Kolona | Značenje |
|---|---|
| `employee_id`, `year`, `month`, `revision` | **Jedinstveno zajedno** |
| `unit_code` | OJ u trenutku ocenjivanja |
| `supervisor_id`, `director_id`, `general_director_id` | Potpisnici, zamrznuti u trenutku ocene |
| `snapshot` | **JSON snimak** cele ocene — merila, bodovi, opisi |
| `stimulation` | Stimulacija, `decimal(10,5)` |
| `personal_coefficient` | Lični koeficijent, `decimal(10,5)` |
| `request_key` | UUID, jedinstven — sprečava dvostruki upis istog obrasca |
| `source_evaluation_id` | Veza na prethodnu reviziju |

> **[P]** Ocena je **nepromenljiva**. Ispravka se pravi kao **nova revizija** koja
> pokazuje na izvornu. Nazivi merila se čuvaju u `snapshot`, pa kasnija izmena
> šifarnika **ne menja** ranije ocene.

`hr_evaluationapproval` [P]: jedinstveno `(evaluation, stage)`;
`stage` je `supervisor`, `director` ili `general_director`.

> **[N] Q10:** nazivi merila i opisi bodovanja u bazi su na **ćirilici**, dok je ostatak
> sistema na latinici. `hr/services/evaluations.py` ima funkcije `latin()` i `cyrillic()`
> za preslovljavanje.

---

## 4.6. Finansijska analitika — `finansije`

Izvorni kod: [`finansije/models.py`](../../finansije/models.py)

### `finansije_ledgerentry` — knjiženje (lokalna kopija izvora)

Najvažnija tabela finansijske analitike. Jedan red = **jedna izvorna stavka naloga**.

| Kolona | Izvorno polje | Poslovno značenje |
|---|---|---|
| `company` | `sif_pred` | Firma |
| `year` | `god` | Godina |
| `journal_type` | `sif_vrs` | Vrsta naloga (npr. `IF`, `ON`, `NT`, `ZAT`) |
| `journal_number` | `br_naloga` | Broj naloga |
| `line_number` | `stavka` | Stavka |
| `organizational_unit` | `oj` | **OJ knjiženja** (nije isto što i centar) |
| `account` | `knt` | Konto |
| `partner_group`, `partner_code` | `grupa`, `sif_par` | Partner |
| `document_date` | `datum` | **Datum dokumenta** |
| `booking_date` | `dat_naloga` | **Datum knjiženja** — po njemu idu prihodi/rashodi |
| `document_reference` | `vez_dok` | Veza dokumenta |
| `debit`, `credit` | `duguje`, `potrazuje` | Iznosi u RSD |
| `currency`, `foreign_amount` | `deviza`, `promena` | Valuta i devizni iznos |
| `description` | `skr_naz` | Opis |
| `linked_line` | `stavka_k` | Vezana stavka |
| `due_date` | `dpo` | Dospeće |
| `debit_credit_flag` | `d_p` | Oznaka duguje/potražuje |
| `source_paid_amount` | `placeno` | Plaćeno po izvoru |
| `job_code` | `sif_pos` | **Šifra posla** |
| `job_name`, `center` | iz `posao` | Naziv posla i **centar** (aktuelni, iz šifarnika) |
| `account_name` | iz `konto` | Naziv konta |
| `organizational_unit_name` | iz `ob_jedin` | Naziv OJ |
| `partner_name` | iz `partner` | Naziv partnera |
| `source_hash` | — | Otisak sadržaja, za prepoznavanje izmene |
| `active` | — | **Nestala stavka postaje neaktivna, ne briše se** |
| `changed_at`, `removed_at` | — | Kada je promenjena/uklonjena |

**Izvorni ključ (jedinstven):** `(company, year, journal_type, journal_number, line_number)`. [P]
Identitet **nikad ne zavisi** od iznosa ni opisa. [P]

Indeksi [P]: po periodu, centru, šifri posla, kontu i dokumentu — svi uz `company`.

> **[P] Dva datuma, dva značenja.** `booking_date` (datum knjiženja) određuje period za
> prihode i rashode; `document_date` (datum dokumenta) određuje period za fakture IF i ON.
> Mešanje ta dva datuma je najčešći uzrok neslaganja u proveri.
>
> **[P] Dva pojma „organizaciona jedinica“.** `organizational_unit` je OJ **knjiženja**,
> a `center` je centar **šifre posla** iz šifarnika. To nisu isti podaci.

### `finansije_financejob` — šifarnik poslova

`(company, code)` jedinstveno; `name`, `center`, `active`, `profit_type`. [P]
`active` se izvodi iz izvora kao `aktivan == "D"`. [P]

### `finansije_syncrun` — istorija sinhronizacije knjiženja

Obuhvat (`year_from`–`year_to`), brojači (`source_rows`, `created`, `updated`, `unchanged`,
`removed`), `source_totals` (kontrolni zbirovi, JSON), `latest_booking_date`, greška. [P]

### `finansije_nalogzrefreshrun` — istorija osvežavanja `nalog_z`

| Kolona | Značenje |
|---|---|
| `trigger` | `manual` ili `celery` |
| `requested_by`, `task_id` | Ko i koji zadatak |
| `year_from`, `year_to` | Godine koje je procedura sama izabrala |
| `updated_rows`, `inserted_rows` | Brojači iz procedure |
| `status` | `running`, `success`, `failed`, `skipped`, **`unknown`** |

> **[P]** Status `unknown` („Ishod nepoznat“) dobija zapis koji je ostao nezavršen posle
> pada procesa. Tada se **mora proveriti stanje u bazi** — procedura je možda ipak prošla.
>
> **[P]** `updated_rows` broji **sve redove obuhvaćene `UPDATE`-om**, ne samo stvarno
> promenjene. Veliki broj ne znači veliku promenu.

---

## 4.7. Nabavka — `nabavka`

Izvorni kod: [`nabavka/models.py`](../../nabavka/models.py). Sve tabele imaju izričit `db_table`.

### `nabavka_procurement_case` — predmet nabavke

| Kolona | Značenje |
|---|---|
| `case_number` | **Broj predmeta, jedinstven** |
| `case_type` | `nabavka` (ZN), `usluga` (ZU), `oprema` (PLN) |
| `is_garage` | Garažni predmet → prefiks `ZNG` / `ZUG` |
| `status` | `draft`, `submitted`, `in_progress`, `waiting_invoice`, `invoice_linked`, `completed`, `cancelled` |
| `work_type` | `mali_servis`, `veliki_servis`, `popravka` |
| `garage_order_id` | Veza ka `fleet_kvar` |
| `job_code_id` | OJ / šifra posla |
| `supplier_id`, `contract_id`, `vehicle_id`, `responsible_id` | Veze |
| `estimated_value`, `currency` | Procenjena vrednost (RSD/EUR/USD/CHF) |
| `needed_by` | Datum zahteva |

Format broja [P]: `<prefiks>-<centar>/<godina>-<redni broj>`,
npr. `ZN-43/2026-17`, `ZNG-43/2026-3`. Godina se uzima iz `created_at`.
Bez centra u OJ — greška *„Nedostaje sifra centra za broj zahteva.“*

### `nabavka_procurement_item` — stavka predmeta

`name`, `uom`, `quantity`, `estimated_unit_price`, `note`.
`estimated_total` = cena × količina (prazno ako bilo šta nedostaje). [P]

**Povezivanje sa izvorom** [P]: `source_type` je `euf`, `uf` ili `goods`, a odgovarajuća
veza mora biti **tačno jedna**:

| `source_type` | Veza |
|---|---|
| `euf` | `euf_invoice_id` → `nabavka_invoice` |
| `uf` | `uf_invoice_id` → `nabavka_uf_invoice_snapshot` (ili `uf_item_id`) |
| `goods` | `goods_item_id` → `nabavka_goods_snapshot` |

`clean()` odbija i stavku sa tipom bez veze i stavku sa vezom bez tipa. [P]

### Snimci izvora

| Tabela | Izvor | Ključ |
|---|---|---|
| `nabavka_invoice` | `dbo.nbv_preuzete_EUF` | `(source, euf_key)` |
| `nabavka_euf_item_snapshot` | `dbo.nbv_EUF_stavke` | `source_key` |
| `nabavka_uf_invoice_snapshot` | izvedeno grupisanjem stavki | `source_key` |
| `nabavka_goods_snapshot` | `dbo.nbv_roba` | `source_key` |

`nabavka_invoice` (EUF faktura) dodatno nosi operativne oznake koje unosi korisnik [P]:
`job_code_id`, `job_code_source`, `vehicle_job_code_assigned_date`, `is_garage`,
`work_type`, `vehicle_id`, `goes_to_warehouse`, `is_returned`, `internal_note`.

> **[P]** `job_code_source = "vehicle_snapshot"` znači da šifra posla **nije** uneta ručno
> nego preuzeta iz istorijske dodele vozila na datum `vehicle_job_code_assigned_date`.

### Veze

| Tabela | Šta povezuje | Jedinstveno |
|---|---|---|
| `nabavka_invoice_link` | Predmet ↔ EUF ključ | `(procurement_case, source, euf_key)` |
| `nabavka_item_invoice_link` | Stavka ↔ faktura | stavka je `OneToOne` |
| `nabavka_invoice_job_code_link` | Faktura ↔ šifra posla (`primary`/`additional`) | `(invoice, job_code)` |
| `nabavka_contract_link` | Predmet ↔ ugovor | `(procurement_case, contract)` |
| `nabavka_invoice_contract_link` | Faktura ↔ kupovni ugovor | `(invoice, contract)` |

`sync_primary_job_code_link()` [P]: kad se promeni `job_code` fakture, stara osnovna veza
se **briše ako nije vraćena**, a ako **jeste vraćena** — prelazi u „dodatnu“, da se trag
vraćanja ne izgubi.

### Plan javnih nabavki

| Tabela | Uloga |
|---|---|
| `nabavka_public_procurement_plan_version` | Verzija plana za godinu: `(year, version_number)` jedinstveno, + brojači razlika |
| `nabavka_public_procurement_plan_item` | Stavka plana |

Stavka [P]: `plan_type` (`public` / `exempt`), `diff_status`
(`added`, `changed`, `unchanged`, `removed`), `stable_key`, `content_hash`,
`previous_item_id` (veza na istu stavku u prethodnoj verziji), `raw_data` (JSON izvorni red).
Jedinstveno `(version, stable_key)`.

> **[P]** Uklonjena stavka se **prepisuje u novu verziju** sa statusom `removed`,
> da bi plan ostao potpun.

### Ostalo

| Tabela | Uloga |
|---|---|
| `nabavka_purchase_order` | Narudžbenica: broj (jedinstven), datum, dobavljač, ugovor, status, iznos |
| `nabavka_status_log` | Promena statusa predmeta: stari, novi, komentar, ko i kada |

---

## 4.8. Potraživanja — `potrazivanja`

Izvorni kod: [`potrazivanja/models.py`](../../potrazivanja/models.py)

Modul je projektovan oko tri načela [P]:

1. **Identitet po izvoru** — svaki preuzeti zapis ima stabilan izvorni ključ.
2. **Nepromenljivi snimci** — stanje se objavljuje, ne prepisuje.
3. **Potpuna sledljivost** — svaki prenos ima svoj `run`, korak, kontrolne zbirove i greške.

### Sinhronizacija

| Tabela | Uloga |
|---|---|
| `potrazivanja_collectionsyncrun` | Jedan prenos: status, obuhvat, brojači, kontrolni zbirovi, greška |
| `potrazivanja_collectionsyncstep` | Korak prenosa: `(run, code)` jedinstveno, brojači po koraku |
| `potrazivanja_sourcedataset` | **Nepromenljiv snimak celog izvora**: `(name, fingerprint)` |
| `potrazivanja_sourcerow` | Red snimka: `(dataset, ordinal)` |
| `potrazivanja_legacyimportmap` | Mapa nasleđeni zapis → novi zapis |
| `potrazivanja_importissue` | Problem pri prenosu: šifra, ozbiljnost, poruka, rešenje |

> **[P]** `SourceDataset` se **ponovo koristi samo za identičan sadržaj** (isti `fingerprint`).
> Ponovljena sinhronizacija istih podataka ne stvara novi snimak.

### Partneri i dokumenti

| Tabela | Uloga | Ključ |
|---|---|---|
| `potrazivanja_financepartneridentity` | **Identitet partnera** u finansijama | `(source_system, company, partner_group, partner_code)` |
| `potrazivanja_collectionprofile` | Oznake partnera: važan kupac, potrebna provera, vlasnik | `identity` 1:1 |
| `potrazivanja_invoicedocument` | Faktura | `(source_system, company, source_key)` |
| `potrazivanja_receivableposting` | **Knjiženje potraživanja** | `(source_system, company, year, journal_type, journal_number, line_number)` |
| `potrazivanja_duedateevidence` | Dokaz dospeća iz uvozne serije | `(import_run, source_table, source_key, occurrence)` |

Kontrole doslednosti u `clean()` [P]:

- Dokument i partner moraju biti ista firma.
- Knjiženje i partner moraju imati isti izvorni ključ.
- Dokument i knjiženje moraju imati istu firmu **i** istog partnera.
- Dokaz dospeća mora odgovarati firmi, grupi i šifri partnera.

### Snimci stanja

| Tabela | Uloga |
|---|---|
| `potrazivanja_balancesnapshot` | Snimak: `(run, company, as_of_date)`, status `draft`/`validated`/`published` |
| `potrazivanja_receivableposition` | **Pozicija** u snimku |
| `potrazivanja_collectionstate` | Aktivno stanje po firmi — pokazuje na **objavljeni** snimak |
| `potrazivanja_agingrule` | Starosni razred: `min_days`, `max_days`, redosled, predložena radnja |

`ReceivablePosition` [P]:

| Kolona | Značenje |
|---|---|
| `identity_id`, `document_id`, `reference` | Partner i dokument |
| `job_code`, `center_code` | Šifra posla i centar |
| `account_family` | Grupa konta (3 znaka) |
| `debit`, `credit`, `balance` | **`balance` mora biti tačno `ROUND(debit − credit, 2)`** — provereno `CheckConstraint`-om u bazi |
| `due_date`, `due_date_method`, `due_date_evidence_id` | Dospeće, **način kako je utvrđeno** i dokaz |
| `resolution_details` | JSON sa objašnjenjem razrešenja |

Jedinstveno: `(snapshot, identity, reference, job_code, account_family)`. [P]

`BalanceSnapshot` ima `CheckConstraint` [P]: `published_at` je popunjen **ako i samo ako**
je status `published`.

`CollectionState.clean()` [P]: aktivno stanje mora biti **objavljen** snimak **iste firme**.

> **[P]** `due_date_method` i `due_date_evidence` postoje jer dospeće nije uvek u izvoru —
> sistem beleži **kako** je do njega došao, da bi rezultat bio proveriv.

### Operativne evidencije

| Tabela | Uloga |
|---|---|
| `potrazivanja_collectioncontact` | Kontakt kod partnera, sa razdvojenim imenom/prezimenom/funkcijom |
| `potrazivanja_contactpoint` | Pojedinačan telefon / mobilni / e-pošta: `(contact, kind, value)` jedinstveno |
| `potrazivanja_collectionactivity` | Napomena ili telefonski poziv, sa ishodom i sledećom radnjom |
| `potrazivanja_collectionnotice` | Opomena, pozivno pismo ili nasleđena evidencija tužbe |
| `potrazivanja_collectionnoticeitem` | Stavka opomene: `(notice, line_number)` |
| `potrazivanja_electronicinvoicestatus` | Status fakture na SEF-u |
| `potrazivanja_collectionlegalcase` | **Pravni postupak** |
| `potrazivanja_collectionlegalevent` | Promena u postupku |
| `potrazivanja_legalcaselink` | Veza ka nasleđenom ID-u postupka |
| `potrazivanja_collectionaudit` | Revizorski trag: entitet, ID, akcija, pre/posle (JSON) |
| `potrazivanja_collectionfileimport` | Uvoz Excel datoteke: `fingerprint` jedinstven |

`CollectionContact` [P]: `original_data` (JSON) čuva izvorni zapis, `needs_review` označava
kontakt koji treba proveriti, `import_parent` povezuje kontakte nastale **razdvajanjem**
jednog nasleđenog zapisa sa više adresa.

`CollectionLegalCase` [P]: `tip` je `tuzeni`, `tuzili`, `stecaj` ili `uppr`; polja se
koriste u zavisnosti od tipa (osnovni dug, kamata, troškovi, ukupan dug, vrednost spora,
datum otvaranja stečaja, prijava potraživanja…). `original_data` čuva nasleđeni zapis.

`CollectionFileImport.fingerprint` je jedinstven — **ponovljeni uvoz iste datoteke
ne stvara duple opomene**. [P]

---

## 4.9. Ugovori — `ugovori`

Izvorni kod: [`ugovori/models.py`](../../ugovori/models.py)

### `ugovori_partner`

| Kolona | Značenje |
|---|---|
| `partner_type` | `legal_entity`, `person`, `bank` |
| `residency` | `domestic`, `foreign` |
| `external_sif_par` | **Šifra iz starog sistema** — veza sa knjigovodstvom |
| `pib`, `maticni_broj`, `jmbg`, `passport_number`, `foreign_tax_id` | Identifikatori |
| `data_source`, `data_validated`, `data_validated_at` | Poreklo i validacija podataka |
| `apr_status`, `apr_checked_at` | **Status iz APR-a** i kada je proveren |

Kontrole [P]: domaće pravno lice mora imati PIB i/ili matični broj;
domaće fizičko lice mora imati JMBG.

### `ugovori_contract`

| Kolona | Značenje |
|---|---|
| `kind` | `MAIN` (glavni ugovor) ili `ANNEX` (aneks) |
| `parent_contract_id` | Obavezan za aneks, zabranjen za glavni |
| `contract_number` | **Jedinstven** |
| `contract_type_id` | Tip iz šifarnika |
| `contract_date`, `valid_from`, `valid_to` | Datumi |
| `value`, `value_type`, `unit_price`, `unit_label`, `currency` | Vrednost |
| `status` | `draft`, `active`, `expired`, `terminated`, `archived` |
| `has_incoming_menice`, `has_outgoing_menice`, `has_guarantees` | Oznake instrumenata |

`value_type` [P]: `fixed`, `hourly`, `monthly`, `man_month`, `unit`, `undefined`.

Kontrole [P]: aneks mora imati glavni ugovor; glavni ne sme imati nadređeni;
nadređeni mora biti tipa `MAIN`; ugovor ne može biti sam sebi nadređen;
`valid_to` ne sme biti pre `valid_from`.

### Ostalo

| Tabela | Uloga |
|---|---|
| `ugovori_contract_type` | Šifarnik tipova (šifra jedinstvena) |
| `ugovori_business_request` | Zahtev: broj (jedinstven), tip, predmet, status, fajl |
| `ugovori_offer` | Ponuda: broj (jedinstven), smer (naša / data nama), vrednost, status |
| `ugovori_contract_document` | Dokument uz ugovor (tip, opis, fajl, originalni naziv) |
| `ugovori_contract_party` | Stranka ugovora: `(contract, partner, role)` jedinstveno |
| `ugovori_contract_guarantee` | Garancija: broj, izdavalac, korisnik, iznos, period, status |
| `ugovori_contract_menica_link` | Veza ugovora i menice — **tačno jedna** od (`menica`, `ulazna_menica`) |

---

## 4.10. Menice — `menice`

Izvorni kod: [`menice/models.py`](../../menice/models.py). Tabele: **`menica`** i **`ulazna_menica`** (bez prefiksa).

### `menica`

Zapis iz Registra menica NBS ili ručni unos.

| Kolona | Značenje |
|---|---|
| `tip` | `izlazna` ili `ulazna` |
| `serijski_broj_menice` | Serijski broj (indeksiran) |
| `sifra_partnera`, `naziv_duznika`, `maticni_broj_duznika`, `poreski_broj_duznika` | Dužnik |
| `datum_izdavanja`, `datum_dospeca`, `datum_registracije` | Datumi |
| `iznos_menice`, `valuta_menice` | Iznos |
| `osnov_izdavanja`, `iznos_iz_osnova`, `valuta_osnova` | Osnov |
| `avalisti_detalji`, `avalisti_broj_zapisa` | Avalisti iz registra |
| `broj_ugovora`, `datum_ugovora`, `oj` | Veza sa poslom |
| `fizicka_lokacija` | **`centar` ili `blagajna`** — gde se menica fizički nalazi |
| `interni_status` | `0` aktivna, `1` obrisana, `2` nepoznat |

### `ulazna_menica`

Menica primljena od partnera, sa vlastitim skupom polja.

| Kolona | Značenje |
|---|---|
| `serijski_broj_menice` | Serijski broj |
| `jedinica_vrednosti` | **`RSD`, `EUR` ili `PROCENAT`** |
| `procenat_iznos` | Iznos ili procenat, zavisno od jedinice |
| `sifra_poslovnog_partnera`, `naziv_pravnog_lica` | Partner |
| `broj_naseg_ugovora`, `datum_ugovora`, `ugovor_vazi_do` | Naš ugovor |
| `lokacija_menice`, `sifra_centra` | Gde se nalazi |

> **[P]** `jedinica_vrednosti = PROCENAT` znači da `procenat_iznos` **nije novčani iznos**
> nego procenat vrednosti ugovora. Sabiranje te kolone bez provere jedinice daje besmislen zbir.

---

## 4.11. Mobilna telefonija — `mobilni`

Izvorni kod: [`mobilni/models.py`](../../mobilni/models.py)

| Tabela | Uloga | Jedinstveno |
|---|---|---|
| `mobilni_mobilepackage` | Paket: naziv, period, neto i bruto iznos, ugovor | `(partner_code, name, valid_from)` |
| `mobilni_mobileuser` | Korisnik iz izvora operatera | `employee_code` |
| `mobilni_mobileassignment` | **Dodela broja za mesec** | `(year, month, phone_number)` |
| `mobilni_mobileusage` | **Potrošnja za mesec** | `(year, month, phone_number)` |
| `mobilni_mobileparkingexemption` | Broj izuzet od parkinga | `phone_number` |
| `mobilni_mobileimportlog` | Log uvoza | |

### `mobilni_mobileuser.link_status` [P]

| Vrednost | Značenje |
|---|---|
| `auto` | Automatski povezan sa zaposlenim |
| `manual` | Ručno povezan |
| `unmatched` | Nije povezan |
| `non_employee` | **Nije zaposleni** — namerno se ne povezuje |
| `ambiguous` | Više mogućih zaposlenih |

### `mobilni_mobileusage` — kolone koje ulaze u obračun [P]

`vat_base` (osnovica za PDV), `parking`, `nzrd`, `total` (ukupno za naplatu),
`vat` (PDV), `installments` (plaćanje na rate), plus 20 kolona vrsta saobraćaja
(`onnet`, `mts_network`, `outside_mts`, `kim`, `special`, `international`, `roaming`,
`gprs`, `sms`, `sms_international`, `sms_roaming`, `mms`, `vas_sms`, `discount_traffic`,
`fixed_discount`, `variable_discount`, `services`, `dispatch_notes`).

> **[P]** Obustava se računa iz **`vat_base`, `parking` i `nzrd`** — ne iz `total`.
> Vidi obračun M-01.

### Razrešavanje zaposlenog [P]

`MobileAssignment.linked_employee` ide ovim redom:

1. Ako postoji `mobile_user` sa `link_status = non_employee` → **nema zaposlenog**.
2. Ako `mobile_user` ima zaposlenog → taj zaposleni.
3. Inače, ako dodela ima direktnu vezu `employee` → taj zaposleni.
4. Inače → nema zaposlenog.

Prikaz šifre i imena pada nazad na `source_employee_code` i `source_full_name` iz izvora.

---

## 4.12. Nasleđeni objekti baze (`dbo.*`)

> **[N] Sadržaj ovih objekata nije potvrđen** — definicije nisu u repozitorijumu.
> DDL se očekuje; do tada važi samo ono što je potvrđeno kodom koji ih čita ili
> postojećom dokumentacijom.

### 4.12.1. Izvori za Flotu

| Objekat | Kolone koje aplikacija čita | Šta radi sa njima |
|---|---|---|
| `dbo.fleet_otpis` | `inv_br` | Postavlja `Vehicle.otpis = True` po inventarskom broju |
| `dbo.vrednost_vozila` | `sif_osn`, `sad_vrednost` | Upisuje `Vehicle.value` |
| `dbo.sif_pos_trenutno` | `regbr`, `sifpos` | Nova `JobCode` dodela ako se razlikuje od poslednje |
| `dbo.v_organizationalunit` | `sif_pos`, `naz_pos`, `blok` | Puni `OrganizationalUnit` |
| `dbo.fleet_potrazivanje_ddor` | `god`, `sif_vrs`, `br_naloga`, `stavka`, `oj`, `knt`, `datum`, `vez_dok`, `potrazuje`, `kola` | Stvara `DraftInsurance` |
| `dbo.fleet_servisi` | — | Puni `ServiceTransaction` / `DraftServiceTransaction` |
| `dbo.fleet_trebovanja` | — | Puni `Requisition` |
| `dbo.fleet_zatvoren_putni` | — | Puni `PutniNalog.isplaceno` |
| `dbo.lizing_kamate` | — | Puni `LeaseInterest` |
| `dbo.kasko_rate` | `contract_number`, `year`, `rate` | Model `KaskoRate` (`managed = False`) |

### 4.12.2. Izveštajni pogledi Flote

Ovih devet pogleda se čita **bez ijedne transformacije u Pythonu** — cela formula je u bazi.
Zato je njihov DDL **prioritet 1** za dokumentaciju obračuna. [P]

| Pogled | Ekran |
|---|---|
| `dbo.fleet_tro_svi` | `/izvestaji/troskovi_svi/` |
| `dbo.fleet_tro_goriva_m` | `/izvestaji/tro_gorivo_mesec/` |
| `dbo.fleet_tro_pracenje` | `/izvestaji/tro_pracenja_vozila/` |
| `dbo.fleet_tro_taho` | `/izvestaji/troskovi_tahograf/` |
| `dbo.fleet_tro_parking` | `/izvestaji/tro_parking/` |
| `dbo.tro_zarade` | `/izvestaji/tro_zarade/` |
| `dbo.fleet_dobavljaci` | `/izvestaji/po_dobavljacima/` |
| `dbo.fleet_magacin_rez` | `/izvestaji/magacin/` |
| `dbo.kasko_rate` | `/izvestaji/kasko_rate/` |

### 4.12.3. Izvori za ostale module

| Objekat | Koristi ga |
|---|---|
| `dbo.nbv_preuzete_EUF` | Nabavka — EUF fakture |
| `dbo.nbv_EUF_stavke` | Nabavka — UF stavke |
| `dbo.nbv_roba` | Nabavka — roba |
| `dbo.nbv_sif_pos_par` | Nabavka — provera šifre posla partnera |
| `dbo.hr_employee` | Kadrovi — zaposleni, vrste primalaca |
| `dbo.partneri` | Ugovori — sinhronizacija partnera |
| `dbo.posao` (na `PUTGEO-SERVER.bazaims`) | Potraživanja, Finansije |

### 4.12.4. Procedura `IMS_ERP.dbo.sp_AzurirajNalogZ`

Ponašanje potvrđeno ranijim čitanjem definicije
(izvor: `naplata-lokalni-izvor-plan.md`, poglavlje 2; dokument uklonjen 18.09.2026., u git istoriji `06f60c2`). [P]

| Osobina | Vrednost |
|---|---|
| Parametri | Nema ih |
| Izvor | `PUTGEO-SERVER.BazaIMS.dbo.nalog_z` → privremena tabela |
| Obuhvat godina | Do uključivo 30. aprila: prethodna i tekuća; posle toga samo tekuća |
| Obuhvat firmi | **Sve firme** (nema `sif_pred=1`) |
| Kontrole | NULL vrednosti i duplikati ključa firma/godina/vrsta/broj/stavka |
| Upis | U transakciji: `UPDATE` postojećih + `INSERT` novih u `IMS_ERP.dbo.nalog_z` |
| Vraća | `OdGodine`, `DoGodine`, `BrojAzuriranihRedova`, `BrojDodatihRedova` |

**Dva ograničenja koja korisnik mora znati [P]:**

1. **Ne briše** redove obrisane u izvoru — uspešno izvršavanje **ne znači** da je lokalna
   kopija jednaka izvoru.
2. `BrojAzuriranihRedova` broji sve redove obuhvaćene `UPDATE`-om, ne samo promenjene.

**Nema indeksa** sa kolonama na lokalnom `nalog_z` prema pregledanim metapodacima. [P]

Pokreće se samo kroz `finansije/services/nalog_z.py`, uz `sp_getapplock` u istoj sesiji. [P]

---

## 4.13. Nasleđeni modul Naplata — van obuhvata

Modul `naplata` ima 12 modela sa `managed = False` nad pogledima
(`baza`, `dodela_bucketa`, `ispravke`, `partneri`, `kontakti`, `napomene`, `opomene`,
`poziv_pismo`, `pozivi_tel`, `sif_baket`, `sif_kategorija`, `tuzbe`) i 3 sopstvene tabele
(`avans_klijent`, `postupak`, `promena_postupka`).

Odlukom naručioca **nije predmet ove dokumentacije.** Zamenjuje ga modul Potraživanja.
Vidi [10. Poznati problemi](10-poznati-problemi.md) i [11. Plan razvoja](11-plan-razvoja.md).

> **[P] Poznata neusaglašenost:** model navodi `dodela_bucketa`, a stvarni upiti u
> `naplata/queries.py` koriste **`dodela_baketa`**. Ne preimenovati aktivni pogled
> na osnovu modela — model je taj koji je pogrešan.

---

## 4.14. Kontrolna pravila koja baza sama proverava

Ova pravila su `CheckConstraint` ili `UniqueConstraint` u bazi — ne mogu se zaobići
ni ručnim upisom kroz aplikaciju. [P]

| Tabela | Pravilo |
|---|---|
| `fleet_vehicleholding` | `end_date >= start_date` ili prazno |
| `fleet_jobcode` | Jedno vozilo ne može imati dve dodele istog datuma |
| `hr_annualleavedecision` | `end_date >= start_date` |
| `hr_sickleave` | `end_date >= start_date` ili prazno |
| `hr_employeeevaluation` | `month` između 1 i 12; jedna revizija po zaposlenom/mesecu |
| `hr_evaluationapproval` | Jedna saglasnost po nivou za istu ocenu |
| `potrazivanja_receivableposition` | **`balance = ROUND(debit − credit, 2)`** |
| `potrazivanja_balancesnapshot` | `published_at` popunjen ↔ status je `published` |
| `potrazivanja_collectionsyncrun` | `finished_at >= started_at` |
| `potrazivanja_collectionnoticeitem` | `line_number >= 1` |
| `potrazivanja_duedateevidence` | `occurrence >= 1` |
| `potrazivanja_agingrule` | `max_days >= min_days` |
| `finansije_ledgerentry` | Jedinstven izvorni ključ stavke naloga |

---

## 4.15. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako se podaci preuzimaju iz ovih izvora? | [7. Integracije](07-integracije.md) |
| Kako se iz ovih tabela računaju iznosi? | [6. Analize i obračuni](06-analize-i-obracuni.md) |
| Šta koji modul radi sa ovim tabelama? | [3. Moduli](03-moduli.md) |
