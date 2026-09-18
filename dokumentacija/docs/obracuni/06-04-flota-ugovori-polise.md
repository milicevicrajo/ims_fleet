# 6.4. Flota — polise, lizing i servisi

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](../10-poznati-problemi.md).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [V-17](#v-17--mesečni-troškovi-polisa) | Mesečni troškovi polisa | — |
| [V-18](#v-18--polise-pred-istekom-i-neobnovljene-polise) | Polise pred istekom i neobnovljene polise | — |
| [V-19](#v-19--mesečni-troškovi-lizinga) | Mesečni troškovi lizinga | **P-23, P-24, P-25** |
| [V-20](#v-20--mesečni-troškovi-servisa) | Mesečni troškovi servisa | — |

---

## Zajednička osnova: istorijska šifra posla

Tri od četiri obračuna u ovom poglavlju raspoređuju trošak na **šifru posla koja je
vozilu bila dodeljena na datum dokumenta** — ne na trenutnu. [P]

```
JobCode.objects.filter(
    vehicle = vozilo,
    assigned_date <= datum dokumenta        ← ključni uslov
).order_by("-assigned_date")[:1]
```

| Obračun | Datum po kome se traži dodela | Istorijski |
|---|---|---|
| V-17 Polise | `issue_date` (datum izdavanja polise) | **Da** |
| V-19 Lizing | — | **Ne** — koristi poslednju dodelu |
| V-20 Servisi | `datum` (datum knjiženja servisa) | **Da** |

> **[P]** V-19 odstupa od ostalih — vidi problem **P-24**.

---

## V-17 — Mesečni troškovi polisa

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Mesečni troškovi polisa“ |
| Tehnički naziv | `policies_monthly_costs_qs()` |
| Putanja | [`fleet/support/policy_queries.py:16`](../../../fleet/support/policy_queries.py#L16) |
| Adrese | `/izvestaji/policies-monthly-costs/`, izvoz `/izvestaji/policies-monthly-costs.csv` |

### 2. Poslovna svrha

Pokazuje **koliko je osiguranje vozila koštalo po mesecu, centru, šifri posla i vrsti
osiguranja** — za planiranje i za raspodelu troška na nosioce posla.

### 3. Korisnici rezultata

Služba voznog parka, rukovodioci centara, finansije.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | JM | Obavezno | Ko unosi |
|---|---|---|---|---|---|---|
| Datum izdavanja polise | Datum izdavanja | `fleet_policy.issue_date` | datum | — | Ne | Automatski / ručno |
| Iznos premije | Iznos premije | `fleet_policy.premium_amount` | `decimal(10,2)` | RSD | Ne | Automatski / ručno |
| Tip osiguranja | Tip osiguranja | `fleet_policy.insurance_type` | tekst | — | Ne | Automatski / ručno |
| Vozilo | Vozilo | `fleet_policy.vehicle_id` | veza | — | Ne | Ručno (dopuna) |
| Dodela šifre posla | — | `fleet_jobcode.assigned_date`, `organizational_unit` | veza | — | Da | Sinhronizacija |

**Filteri ekrana** (svi opcioni) [P]: godina, mesec, centar, organizaciona jedinica, vrsta.

### 5. Poreklo podataka

```
 Faktura osiguranja (nabavka, EUF)
        │  sinhronizacija polisa, dnevno u 02:00
        ▼
 fleet_policy (issue_date, premium_amount, insurance_type, vehicle)
        │
        ├── fleet_jobcode: dodela važeća na issue_date ──► šifra posla, naziv, centar
        │
        ▼
 grupisanje: godina × mesec × centar × OJ × vrsta  →  zbir premija
```

> **[P]** Polise se ne unose ručno u redovnom radu — puni ih sinhronizacija iz faktura
> dobavljača osiguranja (`fleet/sync/external.py: fetch_policy_data`), koja prepoznaje
> partnera po nazivu koji sadrži **„osiguranje“** ili **„ddor“**.

### 6. Tačan postupak obračuna

**Korak 1 — izvedene kolone po polisi** [P]:

| Kolona | Kako se dobija |
|---|---|
| `year` | Godina iz `issue_date` |
| `month` | Mesec iz `issue_date` |
| `oj_id`, `oj_name`, `job_code`, `center` | Iz dodele važeće **na datum izdavanja polise** |
| `vrsta` | Normalizovan tip osiguranja (vidi korak 2) |

**Korak 2 — normalizacija vrste osiguranja** [P]:

| Vrednost u bazi (bez obzira na velika/mala slova) | Prikazana vrsta |
|---|---|
| `kasko` | **`kasko`** |
| `autoodgovornost` | **`autoodgovornost`** |
| bilo šta drugo | **prepisuje se doslovno** |

> **[P]** Poređenje je **tačno jednako** (`iexact`), ne „sadrži“. Vrednost
> „Kasko osiguranje“ **neće** biti svedena na `kasko` — prikazaće se doslovno i
> činiti **zasebnu grupu**.

**Korak 3 — grupisanje i zbir:**

> grupa = (godina, mesec, centar, OJ, šifra posla, vrsta)
> **iznos = zbir `premium_amount` svih polisa u grupi**

**Korak 4 — sortiranje:** godina, mesec, centar, OJ, šifra posla, vrsta — sve rastuće. [P]

**Zaokruživanje [P]:** nema — zbrajaju se izvorni decimalni iznosi.

**NULL vrednosti [P]:**

| Situacija | Posledica |
|---|---|
| `issue_date` je prazan | Godina i mesec su **prazni** — red se svrstava u grupu bez perioda |
| `premium_amount` je prazan | Ne uvećava zbir (`SUM` preskače NULL) |
| Vozilo nije povezano | Nema dodele → šifra posla, OJ i centar su **prazni** |
| Nema dodele pre datuma polise | Isto — prazna šifra posla |

> **[P] Obuhvat:** obračun uzima **sve** polise, uključujući **nedovršene**
> (one koje ne prolaze `Policy.is_complete()`). Filter potpunosti ovde se **ne primenjuje**
> — za razliku od V-18.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/policy_queries.py` |
| Funkcije | `policies_monthly_costs_qs()`, `_filtered_qs()` |
| Istorijska dodela | konstanta `_latest_jc` (linija 10) |
| View | `fleet/views/policy.py: PoliciesMonthlyCostsView`, `policies_monthly_costs_csv` |
| Dozvole | `policies_monthly_costs`, `policies_monthly_costs_csv` |

### 8. Primer obračuna

> Ilustrativni primer.

| Polisa | Datum izdavanja | Vozilo | Šifra posla na taj dan | Vrsta | Premija |
|---|---|---|---|---|---|
| 1 | 15.03.2026. | A | 413111 | AUTOODGOVORNOST | 18.000,00 |
| 2 | 20.03.2026. | B | 413111 | autoodgovornost | 22.000,00 |
| 3 | 22.03.2026. | C | 413111 | Kasko osiguranje | 95.000,00 |
| 4 | 05.04.2026. | A | 413222 | KASKO | 88.000,00 |

**Rezultat:**

| Godina | Mesec | Centar | Šifra posla | Vrsta | Iznos |
|---|---|---|---|---|---|
| 2026 | 3 | 43 | 413111 | `autoodgovornost` | **40.000,00** |
| 2026 | 3 | 43 | 413111 | `Kasko osiguranje` | **95.000,00** |
| 2026 | 4 | 43 | 413222 | `kasko` | **88.000,00** |

> Polise 1 i 2 su objedinjene jer se „AUTOODGOVORNOST“ i „autoodgovornost“ svode na istu
> vrstu. Polisa 3 **ostaje zasebno** jer „Kasko osiguranje“ nije tačno jednako „kasko“ —
> zato se u izveštaju vide dve različite kasko grupe.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Zbir premija po mesecu, centru, šifri posla i vrsti |
| Format | Tabela i CSV izvoz; iznosi u RSD |
| Gde se čuva | Nigde — računa se pri otvaranju |
| Kada se ponovo računa | Pri svakom otvaranju |
| Može li korisnik da ga izmeni | Posredno — izmenom polise ili dodele šifre posla |
| Istorija | Ne postoji |

### 10. Upotreba rezultata

| Korisnik | Šta preuzima | Odakle |
|---|---|---|
| Služba voznog parka | Zbir po mesecima | Ekran |
| Rukovodilac centra | Trošak osiguranja svog centra | Ekran, filtriran po centru |
| Finansije | CSV izvoz | `/izvestaji/policies-monthly-costs.csv` |

> **[N] Q3:** nije potvrđeno da li se CSV koristi kao osnov za knjiženje raspodele.

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Zbir svih grupa | Mora biti jednak zbiru `premium_amount` svih polisa u periodu |
| Nedostaje šifra posla | Vozilo nema dodelu pre datuma izdavanja polise — proveriti `/sifre-poslova/` |
| Dve grupe iste vrste | Tip osiguranja je upisan različito — proveriti `/polise/` |
| Polisa nije u izveštaju | Proveriti da li ima `issue_date` |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Nedovršena polisa | **Ulazi** u izveštaj |
| Polisa bez vozila | Ulazi, ali bez šifre posla i centra |
| Tip osiguranja upisan drugačije | **Zasebna grupa** — deli iznos na dve vrste |
| Polisa bez datuma izdavanja | Grupiše se bez godine i meseca |
| Izveštaj prati **datum izdavanja**, ne period važenja | Polisa za celu 2026. prikazuje se **samo u mesecu izdavanja** |

> **[P] Bitna razlika u odnosu na V-07:** ovaj izveštaj raspoređuje premiju po **datumu
> izdavanja**, a trošak po kilometru po **periodu važenja**. Zbog toga se iznosi iz
> dva ekrana ne slažu — to nije greška, nego različita pitanja.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Grupiše se po datumu izdavanja | Potvrđeno | `policy_queries.py:18-19` | — |
| Šifra posla je istorijska, na datum izdavanja | Potvrđeno | `policy_queries.py:10-13` | — |
| Normalizacija samo za tačno `kasko` i `autoodgovornost` | Potvrđeno | `policy_queries.py:26-31` | — |
| Nedovršene polise ulaze | Potvrđeno | Nema filtera potpunosti | Potvrditi da je željeno |
| Upotreba u knjiženju | **Nepotvrđeno** | — | **Q3** |

---

## V-18 — Polise pred istekom i neobnovljene polise

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Polise pred istekom i neobnovljene“ |
| Tehnički naziv | `expiring_policy_qs()`, `expired_unrenewed_policy_qs()` |
| Putanja | [`fleet/support/policy_queries.py:47`](../../../fleet/support/policy_queries.py#L47) |
| Adresa | `/polise/istek/` |

### 2. Poslovna svrha

Sprečava da vozilo ostane **bez važećeg osiguranja**. Dva odvojena spiska:

| Spisak | Značenje |
|---|---|
| **Pred istekom** | Polisa ističe u narednih 30 dana, treba je obnoviti |
| **Neobnovljene** | Polisa je već istekla, a nova nije evidentirana |

### 3. Korisnici rezultata

Služba voznog parka — operativno, svakodnevno.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona |
|---|---|
| Datum početka | `fleet_policy.start_date` |
| Datum završetka | `fleet_policy.end_date` |
| Tip osiguranja | `fleet_policy.insurance_type` |
| Da li se obnavlja | `fleet_policy.is_renewable` |
| Vozilo | `fleet_policy.vehicle_id` |
| Svih 13 polja potpunosti | vidi `Policy.incomplete_q()` |

### 5. Poreklo podataka

Polise iz sinhronizacije faktura osiguranja, dopunjene ručno na ekranu
`/polise/nedovrseno/`.

### 6. Tačan postupak obračuna

**Korak 0 — samo potpune polise** [P]

Oba spiska rade **isključivo nad potpunim polisama** — onima kod kojih je popunjeno
**svih 13 polja**:

> vozilo, PIB partnera, naziv partnera, broj fakture, datum izdavanja, tip osiguranja,
> broj polise, iznos premije, datum početka, datum završetka, iznos prve rate,
> iznos ostalih rata, broj rata

Nedovršena polisa **nikada** ne ulazi u upozorenja. [P]

> **[Z] Posledica:** vozilo sa nedovršenom polisom **neće** dobiti upozorenje o isteku.
> Zato postoji zaseban ekran `/polise/nedovrseno/` i upozorenje na kontrolnoj tabli.

**Korak 1 — „najnovija polisa“ po vozilu i vrsti** [P]

Za svaku polisu se traži **najkasniji datum završetka** među polisama **istog vozila
i iste vrste osiguranja**:

```
najnovija = potpune polise
            .filter(vehicle = isto vozilo, insurance_type = ista vrsta)
            .order_by("-end_date")[:1]
```

> **[P]** Grupisanje je po **tačnoj vrednosti** `insurance_type`. „KASKO“ i „Kasko“ se
> tretiraju kao **različite vrste** i ne obnavljaju jedna drugu.

**Korak 2A — polise pred istekom:**

Polisa ulazi ako **sve** važi:

| Uslov | Objašnjenje |
|---|---|
| `end_date >= danas` | Još nije istekla |
| `end_date <= danas + 30 dana` | Ističe u narednih 30 dana |
| `end_date` = najkasniji datum za to vozilo i vrstu | **Nije zamenjena novijom polisom** |
| najnovija polisa ima `is_renewable = True` | Obnavlja se |

Broj dana je podesiv parametar, podrazumevano **30**. [P]

**Korak 2B — neobnovljene polise:**

Polisa ulazi ako **sve** važi:

| Uslov | Objašnjenje |
|---|---|
| `end_date < danas` | Već je istekla |
| **ne postoji** polisa istog vozila i vrste sa **kasnijim `start_date`** | Nije obnovljena |
| najnovija polisa ima `is_renewable = True` | Trebalo je da se obnovi |

> **[P] Razlika u pravilu:** korak 2A gleda **najkasniji datum završetka**, a korak 2B
> **postojanje polise sa kasnijim datumom početka**. To su dva različita pravila, oba
> namerna: nova polisa obično počinje posle isteka stare.

**NULL vrednosti [P]:** polisa bez `start_date` ili `end_date` je **nedovršena** i
uopšte ne ulazi u obračun.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/policy_queries.py` |
| Funkcije | `complete_policy_qs()`, `expiring_policy_qs()`, `expired_unrenewed_policy_qs()` |
| Uslov potpunosti | `fleet/models.py: Policy.incomplete_q()` |
| View | `fleet/views/policy.py: ExpiringAndNotRenewedPolicyView` |
| Srodno | Kontrolna tabla flote (`fleet_snapshot`) ima **svoju**, drugačiju proveru |

> **[P] Dva različita pravila u sistemu:** kontrolna tabla
> (`fleet/support/fleet_snapshot.py:72-78`) koristi strože pravilo — traži da postoji
> polisa **iste vrste** koja počinje **najkasnije dan posle** isteka i traje duže,
> dakle **bez prekida pokrića**. Ekran `/polise/istek/` to ne proverava.
> Zato se dva spiska mogu razlikovati. Vidi pitanje **Q20**.

### 8. Primer obračuna

> Današnji dan: **20.03.2026.**

| Polisa | Vozilo | Vrsta | Početak | Kraj | Obnavlja se | Potpuna |
|---|---|---|---|---|---|---|
| 1 | A | AUTOODGOVORNOST | 01.04.2025. | **05.04.2026.** | Da | Da |
| 2 | B | AUTOODGOVORNOST | 01.02.2025. | **31.01.2026.** | Da | Da |
| 3 | B | AUTOODGOVORNOST | 01.02.2026. | 31.01.2027. | Da | Da |
| 4 | C | KASKO | 01.03.2025. | **28.02.2026.** | Da | Da |
| 5 | D | AUTOODGOVORNOST | 01.03.2025. | 15.03.2026. | Da | **Ne** (nema broja polise) |

**Rezultat:**

| Spisak | Polise | Obrazloženje |
|---|---|---|
| **Pred istekom** | Polisa 1 | Ističe 05.04.2026., u roku od 30 dana, nema novije |
| **Neobnovljene** | Polisa 4 | Istekla 28.02.2026., nema polise sa kasnijim početkom |
| Ni u jednom | Polisa 2 | Zamenjena polisom 3 (kasniji početak) |
| Ni u jednom | Polisa 3 | Ističe tek 31.01.2027. |
| Ni u jednom | **Polisa 5** | **Nedovršena — ne ulazi ni u jedno upozorenje** |

> Vozilo D je **bez upozorenja**, iako mu polisa ističe za 5 dana. Razlog je nepotpun
> unos. To je namerno ponašanje, ali je rizik — zato kontrolna tabla ima zaseban
> pokazatelj „Polise za dopunu“.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Dva spiska polisa koje traže radnju |
| Format | Tabela na ekranu |
| Gde se čuva | Nigde |
| Kada se ponovo računa | Pri svakom otvaranju, uvek u odnosu na **današnji dan** |
| Ko postupa | Služba voznog parka |

### 10. Upotreba rezultata

Operativni spisak za obnovu osiguranja. **Ne ulazi** ni u jedan drugi obračun.

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Vozilo nije u spisku, a trebalo bi | Proveriti da li je polisa **potpuna** (`/polise/nedovrseno/`) |
| Polisa je obnovljena, a i dalje je u spisku | Proveriti da li je **tip osiguranja** upisan isto u obe polise |
| Spisak se razlikuje od kontrolne table | Različita pravila — vidi 7. i pitanje **Q20** |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Rizik |
|---|---|---|
| **Nedovršena polisa** | Ne ulazi ni u jedno upozorenje | **Vozilo ostane bez upozorenja** |
| Tip osiguranja upisan različito | Nova polisa ne „pokriva“ staru | Lažno upozorenje |
| `is_renewable = False` | Polisa se ne prikazuje ni u jednom spisku | Namerno |
| Polisa obnovljena sa prekidom pokrića | `/polise/istek/` je **ne prikazuje**, kontrolna tabla **prikazuje** | Neusklađenost |
| Vozilo otpisano | **Nema filtera otpisa** — otpisano vozilo može biti u spisku | Nepotrebno upozorenje |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Samo potpune polise ulaze | Potvrđeno | `policy_queries.py:42-44, 50, 69` | — |
| Rok je 30 dana, podesiv | Potvrđeno | `policy_queries.py:47` | — |
| Grupisanje po tačnoj vrednosti tipa | Potvrđeno | `policy_queries.py:52-53` | — |
| Dva različita pravila obnove (ekran i kontrolna tabla) | Potvrđeno | `policy_queries.py` naspram `fleet_snapshot.py:72-78` | **Q20** |
| Otpisana vozila nisu isključena | Potvrđeno | Nema filtera | Potvrditi da li smeta |

---

## V-19 — Mesečni troškovi lizinga

> **Ovaj obračun ima tri utvrđena nedostatka.** Pre oslanjanja na njegove rezultate
> pročitati poglavlje 12 i probleme P-23, P-24 i P-25.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Mesečni troškovi lizinga“ |
| Tehnički naziv | `lease_monthly_costs_rows()` |
| Putanja | [`fleet/support/lease_queries.py:7`](../../../fleet/support/lease_queries.py#L7) |
| Adresa | `/izvestaji/lease-monthly-costs/` |

### 2. Poslovna svrha

Namera je da prikaže **trošak lizinga po mesecu, centru i organizacionoj jedinici**,
uz „prateće troškove“ (servisi i gorivo) vozila te jedinice.

### 3. Korisnici rezultata

Služba voznog parka, finansije.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Napomena |
|---|---|---|
| Datum početka ugovora | `fleet_lease.start_date` | **Određuje mesec u izveštaju** |
| Rata / iznos otplate | `fleet_lease.current_payment_amount` | |
| Vrsta lizinga | `fleet_lease.lease_type` | |
| Šifra posla (tekst) | `fleet_lease.job_code` | Tekstualno polje ugovora |
| Dodela vozila | `fleet_jobcode` | **Poslednja**, ne istorijska |
| Trošak servisa | `fleet_servicetransaction.potrazuje` | „Prateći trošak“ |
| Trošak goriva | `fleet_fuelconsumption.cost_bruto` | „Prateći trošak“ |

### 6. Tačan postupak obračuna

**Korak 1 — grupisanje ugovora** [P]:

> grupa = (godina početka, mesec početka, centar, OJ, šifra posla, vrsta lizinga)
> **iznos lizinga = zbir `current_payment_amount` ugovora u grupi**

Centar i OJ se uzimaju iz **poslednje** dodele vozila (`-assigned_date`, bez datumskog
ograničenja). [P]

> **[P] Problem P-23:** ugovor se pojavljuje **samo u mesecu u kome je počeo**.
> Ugovor koji traje tri godine prikazan je **jednom**, a ne u svakom mesecu trajanja.

**Korak 2 — filteri** (godina, mesec, centar, OJ, vrsta) primenjuju se **u Pythonu**,
nad već učitanim skupom. [P]

**Korak 3 — „prateći troškovi“** [P]:

Za svaku grupu:

1. Pronađu se **sva vozila čija je poslednja dodela ta OJ** — ne samo vozila iz ugovora.
2. Za tu godinu i mesec saberu se:
   - servisi tih vozila (`potrazuje`);
   - gorivo tih vozila (`cost_bruto`).
3. `accompanying_total` = servisi + gorivo
4. `accompanying_per_vehicle` = ukupno / broj vozila

> **[P] Problem P-25:** prateći troškovi se odnose na **sva vozila organizacione
> jedinice**, a ne na vozila pod lizingom. Prikazani su uz red lizinga, pa korisnik
> lako zaključi da pripadaju lizing vozilima.

**Korak 4 — sortiranje:** godina, mesec, centar, OJ. [P]

**NULL vrednosti [P]:** prazan zbir servisa ili goriva se tretira kao 0;
`accompanying_per_vehicle` je **prazan** kada nema vozila u OJ.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/lease_queries.py` |
| Funkcija | `lease_monthly_costs_rows(request)` |
| View | `fleet/views/lease.py: LeaseMonthlyCostsView` |

> **[P] Problem P-24 (izvedba):** za **svaku grupu** izvršavaju se **tri odvojena upita**
> — spisak vozila OJ, zbir servisa i zbir goriva. Kod većeg broja grupa ekran postaje spor.

### 8. Primer obračuna

> Ilustrativni primer.

Ugovori:

| Ugovor | Vozilo | Početak | Kraj | Vrsta | Rata |
|---|---|---|---|---|---|
| L1 | A | 15.01.2024. | 15.01.2027. | operativni | 50.000,00 |
| L2 | B | 01.03.2026. | 01.03.2029. | dugorocni | 65.000,00 |

**Rezultat izveštaja:**

| Godina | Mesec | OJ | Vrsta | Iznos lizinga |
|---|---|---|---|---|
| 2024 | 1 | 413111 | operativni | 50.000,00 |
| 2026 | 3 | 413111 | dugorocni | 65.000,00 |

> Ugovor L1 pojavljuje se **samo u januaru 2024**, iako traje do 2027. Za mart 2026,
> kada obe rate stvarno terete troškove, izveštaj prikazuje **samo L2**.
> To je problem **P-23**.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Zbir rata ugovora **po mesecu početka ugovora** |
| Format | Tabela |
| Gde se čuva | Nigde |
| Može li korisnik da ga izmeni | Ne |

### 10. Upotreba rezultata

Pregled na ekranu. **Ne ulazi** u trošak po kilometru — V-07 računa lizing **potpuno
nezavisno i ispravnije**, sa deljenjem po danima preklapanja.

> **[Z] Preporuka:** za stvarni mesečni trošak lizinga pouzdaniji je obračun iz V-07
> nego ovaj izveštaj.

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Ugovor nedostaje u mesecu | Očekivano — vidi **P-23**; proveriti `/zakupi/` za datum početka |
| Prateći troškovi deluju preveliko | Odnose se na **sva** vozila OJ — vidi **P-25** |
| Zbir lizinga | Uporediti sa `/zakupi/` filtrirano po mesecu početka |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Ugovor traje više meseci** | Prikazan **samo u mesecu početka** | **P-23** |
| **Centar i OJ iz poslednje dodele** | Istorija se zanemaruje | **P-24** / P-05 |
| **Prateći troškovi cele OJ** | Ne odnose se na lizing vozila | **P-25** |
| Vozilo bez dodele | `oj_id` je prazan → nema pratećih troškova, broj vozila 0 | Vidljivo |
| Ugovor bez datuma početka | Godina i mesec prazni | Vidljivo |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Grupisanje po **datumu početka** ugovora | Potvrđeno | `lease_queries.py:13-14` | **P-23** |
| Centar i OJ iz poslednje dodele | Potvrđeno | `lease_queries.py:8-10` | **P-24** |
| Prateći troškovi obuhvataju sva vozila OJ | Potvrđeno | `lease_queries.py:49-72` | **P-25** |
| Filteri se primenjuju u Pythonu | Potvrđeno | `lease_queries.py:30-39` | — |
| Da li je izveštaj u upotrebi | **Nepotvrđeno** | — | **Q21** |

---

## V-20 — Mesečni troškovi servisa

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Mesečni troškovi servisa“ |
| Tehnički naziv | `service_monthly_costs_rows()` |
| Putanja | [`fleet/support/service_queries.py:31`](../../../fleet/support/service_queries.py#L31) |
| Adrese | `/reports/service-monthly-costs/`, izvoz `/reports/services/monthly.csv` |

### 2. Poslovna svrha

Prikazuje **trošak servisa vozila po mesecu, centru i šifri posla**, za praćenje
troškova održavanja po nosiocima.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | JM |
|---|---|---|
| Datum knjiženja servisa | `fleet_servicetransaction.datum` | — |
| Iznos | `fleet_servicetransaction.potrazuje` | RSD |
| Vozilo | `fleet_servicetransaction.vehicle_id` | — |
| Dodela šifre posla | `fleet_jobcode` (na datum servisa) | — |

### 5. Poreklo podataka

```
 dbo.fleet_servisi  ──sinhronizacija dnevno u 03:15──►  fleet_servicetransaction
                                                              │
                     fleet_jobcode: dodela važeća na datum ────┤
                                                              ▼
                              grupisanje: godina × mesec × OJ × centar → zbir
```

### 6. Tačan postupak obračuna

**Korak 1 — izvedene kolone po stavci** [P]:

| Kolona | Kako se dobija |
|---|---|
| `service_year` | Godina iz `datum` |
| `service_month` | Mesec iz `datum` |
| `oj_code_txt` | Šifra OJ iz dodele važeće **na datum servisa** |
| `center_code_txt` | Centar iz iste dodele |

Šifra i centar se pretvaraju u tekst, a prazna vrednost u **prazan string**
(`Coalesce(Cast(...), Value(""))`) — nikada u NULL. [P]

**Korak 2 — grupisanje i zbir:**

> grupa = (godina, mesec, šifra OJ, šifra centra)
> **iznos = zbir `potrazuje`**, a ako nema nijedne stavke → **0,00**

**Korak 3 — sortiranje:** godina opadajuće, mesec opadajuće, centar rastuće,
šifra OJ rastuće. [P] Najnoviji mesec je prvi.

**Tip rezultata [P]:** `decimal(18,2)`.

**NULL vrednosti [P]:**

| Situacija | Posledica |
|---|---|
| Vozilo nema dodelu pre datuma servisa | Šifra i centar su **prazan string**, red je vidljiv |
| Stavka bez vozila | Isto — grupa sa praznom šifrom |
| Prazan `potrazuje` | Ne uvećava zbir |

> **[P] Ispravno rešeno:** za razliku od V-19, ovde se koristi **istorijska** dodela,
> i prazna vrednost se prikazuje kao prazna grupa umesto da se red izgubi.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/service_queries.py` |
| Funkcije | `_service_base_qs()`, `service_monthly_costs_rows()` |
| View | `fleet/views/services.py: ServiceMonthlyCostsView`, `service_monthly_costs_csv` |
| Dozvole | `reports_service_monthly_costs`, `reports_service_monthly_costs_csv` |

### 8. Primer obračuna

| Servis | Datum | Vozilo | Šifra posla na taj dan | Centar | Iznos |
|---|---|---|---|---|---|
| 1 | 10.03.2026. | A | 413111 | 43 | 45.000,00 |
| 2 | 18.03.2026. | B | 413111 | 43 | 12.000,00 |
| 3 | 25.03.2026. | A | 413222 | 12 | 33.000,00 |
| 4 | 05.04.2026. | C | — (nema dodele) | — | 8.000,00 |

**Rezultat:**

| Godina | Mesec | Centar | Šifra OJ | Iznos |
|---|---|---|---|---|
| 2026 | 4 | *(prazno)* | *(prazno)* | **8.000,00** |
| 2026 | 3 | 12 | 413222 | **33.000,00** |
| 2026 | 3 | 43 | 413111 | **57.000,00** |

> Servis 3 ide na **novu** šifru jer je vozilo A promenilo dodelu pre 25.03.
> Servis 4 je vidljiv sa praznom šifrom — ne gubi se.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde |
| Upotreba | Ekran i CSV izvoz |
| Kontrola | Zbir svih grupa = zbir `potrazuje` svih servisnih knjiženja u periodu |
| Prazna grupa | Označava vozila bez dodele — proveriti `/sifre-poslova/` |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Vozilo bez dodele | Prazna šifra i centar, red **ostaje vidljiv** |
| Vozilo promenilo šifru u mesecu | Trošak se deli na dve šifre po datumu |
| Naknadna izmena dodele | **Menja i ranije mesece** — izveštaj nije zamrznut |
| Storno servisa | Zadržava izvorni znak, umanjuje zbir |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Šifra posla je istorijska, na datum servisa | Potvrđeno | `service_queries.py:10-13` |
| Prazna šifra se prikazuje kao prazan string | Potvrđeno | `service_queries.py:25-26` |
| Zbir `potrazuje`, tip `decimal(18,2)` | Potvrđeno | `service_queries.py:36-42` |
| Sortiranje: najnoviji mesec prvi | Potvrđeno | `service_queries.py:52` |

---

## Novi problemi iz ovog poglavlja

Uneti u [Registar problema](../10-poznati-problemi.md):

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-23** | Izveštaj mesečnih troškova lizinga prikazuje ugovor **samo u mesecu početka**, a ne u svakom mesecu trajanja. Mesečni pregled zato ne pokazuje stvarni mesečni trošak lizinga. | **Visoka** |
| **P-24** | Isti izveštaj uzima centar i OJ iz **poslednje** dodele vozila, umesto istorijske — nedosledno sa V-17 i V-20. | Srednja |
| **P-25** | „Prateći troškovi“ u istom izveštaju obuhvataju **sva vozila organizacione jedinice**, ne samo vozila pod lizingom, pa navode na pogrešan zaključak. | Srednja |

## Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q20** | Ekran „Polise pred istekom“ i kontrolna tabla flote koriste **različita pravila** za ocenu da li je polisa obnovljena (kontrolna tabla traži pokriće bez prekida, ekran ne). Koje pravilo je ispravno? |
| **Q21** | Da li se izveštaj „Mesečni troškovi lizinga“ uopšte koristi u radu? Ima tri nedostatka (P-23, P-24, P-25) i preklapa se sa obračunom lizinga u trošku po kilometru. |
| **Q22** | Da li nedovršene polise treba da ulaze u izveštaj mesečnih troškova (V-17)? Sada ulaze, dok su iz upozorenja o isteku (V-18) izuzete. |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.2. Flota — gorivo](06-02-flota-gorivo.md) | Obračuni goriva |
| [6.3. Flota — troškovi](06-03-flota-troskovi.md) | Trošak po kilometru i pragovi |
| [6.5. Flota — izveštaji](06-05-flota-izvestaji.md) | Kilometraža, održavanje, presek flote |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema |
