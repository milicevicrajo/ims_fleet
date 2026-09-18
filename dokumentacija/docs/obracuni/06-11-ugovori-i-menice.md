# 6.11. Ugovori i menice — analize

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](../10-poznati-problemi.md).

**Analize u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [U-02](#u-02--sinhronizacija-partnera-iz-finansija) | Sinhronizacija partnera iz finansija | — |
| [U-01](#u-01--provera-statusa-partnera-u-apr-u) | Provera statusa partnera u APR-u | **P-40** |
| [U-03](#u-03--preuzimanje-menica-iz-registra-nbs) | Preuzimanje menica iz registra NBS | **P-41** |
| [U-04](#u-04--povezivanje-menica-i-garancija-sa-ugovorima) | Povezivanje menica i garancija sa ugovorima | — |

---

## U-02 — Sinhronizacija partnera iz finansija

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Sinhronizacija partnera iz Finansija“ |
| Tehnički naziv | `fetch_finance_partners()`, `partner_defaults_from_finance()` |
| Putanja | [`ugovori/services.py:123`](../../../ugovori/services.py#L123) |
| Adrese | `/ugovori/partneri/sync-finansije/` i paketna obrada |

### 2. Poslovna svrha

Partneri postoje u **nasleđenom finansijskom šifarniku** (`dbo.partneri`). Ovaj postupak
ih prenosi u evidenciju Ugovora, da bi se ugovori i nabavke vezivali za **isti** partner.

### 3. Korisnici rezultata

Pravna služba, služba nabavke, komercijala.

### 4. Ulazni podaci

| Poslovni naziv | Izvorna kolona | Polje u evidenciji |
|---|---|---|
| Šifra partnera | `sif_par` | `external_sif_par` |
| Naziv | `naz_par` | `name` |
| **Grupa** | `grupa` | određuje **tip partnera** |
| Naziv grupe | `naz_grup` | — |
| Ulica | `ulica_par` | `address` |
| Mesto | `mesto_par` | `city` |
| Matični broj | `mb` | `maticni_broj` |
| PIB | `pib` | `pib` |
| Zemlja | `zemlja` | `country`, određuje **rezidentnost** |
| Telefon, e-pošta, kontakt osoba | `telefon`, `email`, `lice` | odgovarajuća polja |

### 6. Tačan postupak

#### Korak 1 — jedan red po šifri partnera [P]

Isti partner se u izvoru može pojaviti u **više grupa**. Upit bira **jedan** red po šifri,
po redosledu prvenstva grupa:

| Prvenstvo | Grupa | Značenje |
|---|---|---|
| **1** | `1` | Kupci i dobavljači |
| **2** | `10` | Fizička lica |
| **3** | `11`, `13`, `14` | Banke |
| 4 | ostale | Ostalo |

Unutar istog prvenstva bira se **manji broj grupe**. [P]

#### Korak 2 — tip partnera iz grupe [P]

| Grupa | Tip partnera |
|---|---|
| `10` | **Fizičko lice** |
| `11`, `13`, `14` | **Banka** |
| ostale | **Pravno lice** |

#### Korak 3 — rezidentnost [P]

Izvodi se iz polja `zemlja` (`residency_from_country`).

#### Korak 4 — upis

Partner se prepoznaje po **`external_sif_par`** — šifri iz starog sistema. [P]

**Paketna obrada [P]:** prenos ide u delovima (`OFFSET … FETCH NEXT`), sa brojačem
ukupnog broja partnera (`count_finance_partners`), da veliki šifarnik ne blokira ekran.

### 8. Primer

**Izvor — isti partner u dve grupe:**

| `sif_par` | `grupa` | `naz_par` |
|---|---|---|
| 1234 | **5** | `AUTODEKI DOO` |
| 1234 | **1** | `AUTODEKI DOO BEOGRAD` |

> Bira se red sa grupom **1** (prvenstvo 1) → naziv `AUTODEKI DOO BEOGRAD`,
> tip **Pravno lice**.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `ugovori_partner` |
| Veza sa izvorom | `external_sif_par` |
| Upotreba | Ugovori, ponude, zahtevi, predmeti nabavke, narudžbenice |
| Kontrola | Uporediti broj partnera sa `count_finance_partners()` |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Partner u više grupa | Uzima se red po prvenstvu |
| Partner bez naziva | Naziv postaje `Partner <šifra>` |
| Partner bez šifre | **Ne ulazi** — upit traži `sif_par IS NOT NULL` |
| Partner obrisan iz izvora | **Ostaje** u evidenciji Ugovora |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Jedan red po šifri, po prvenstvu grupa | Potvrđeno | `services.py:155-165` |
| Tip partnera iz grupe | Potvrđeno | `services.py:103-109` |
| Veza je `external_sif_par` | Potvrđeno | `models.py:40-45` |
| Partneri se ne brišu | Potvrđeno | Nema brisanja |

---

## U-01 — Provera statusa partnera u APR-u

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „APR status“, „APR provera“ |
| Tehnički naziv | `update_partners_from_apr()`, `is_active_apr_status()` |
| Putanja | [`ugovori/apr_openapi.py:34`](../../../ugovori/apr_openapi.py#L34) |
| Adrese | `/ugovori/partneri/<id>/apr-update/`, paketna obrada `/ugovori/partneri/sync-apr/` |

### 2. Poslovna svrha

Proverava u **javnom registru APR-a** da li je partner i dalje **aktivan** privredni
subjekt, i preuzima zvanično poslovno ime — pre zaključenja ugovora i pre plaćanja.

### 3. Korisnici rezultata

Pravna služba, služba nabavke, finansije.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Uloga |
|---|---|---|
| **Matični broj** | `ugovori_partner.maticni_broj` | **Jedini osnov povezivanja** |

**Izvor:** `https://openapi.apr.gov.rs/api/opendata/companies` — javni skup podataka,
bez prijave. [P]

### 6. Tačan postupak

#### Korak 1 — preuzimanje [P]

| Osobina | Vrednost |
|---|---|
| Način | `GET`, odgovor u JSON obliku |
| Kodiranje | `utf-8-sig` |
| Rok | 60 sekundi |
| Koren odgovora | ključ **`Podaci`** |

> **[P] Problem P-40 — zaobilaženje provere potvrde:** ako veza ne uspe zbog SSL greške,
> kod **ponavlja zahtev sa isključenom proverom potvrde** (`verify=False`), uz gašenje
> upozorenja.

#### Korak 2 — normalizacija matičnog broja [P]

> uklone se svi znakovi osim cifara; ako ostane **manje od 8 cifara**, dopuni se
> **vodećim nulama do 8**

| Ulaz | Rezultat |
|---|---|
| `12345678` | `12345678` |
| `1234567` | `01234567` |
| `MB 12345678` | `12345678` |
| prazno | prazno — partner se **preskače** |

#### Korak 3 — određivanje aktivnosti [P]

> partner je aktivan ako je `NazivStatus` **tačno** jednak reči **`активан`**
> (ćirilicom), bez obzira na velika i mala slova

> **[P] Poređenje je tačno, ne „sadrži“.** Status „Активан — у ликвидацији“ ili
> latinično „Aktivan“ **ne bi** bio prepoznat kao aktivan.

#### Korak 4 — šta se upisuje [P]

| Polje | Vrednost |
|---|---|
| `name` | `PoslovnoIme` iz APR-a; ako je prazno — **zadržava se postojeći naziv** |
| `is_active` | Rezultat provere statusa |
| `apr_status` | Izvorni tekst statusa |
| `apr_checked_at` | Trenutak provere |
| `data_source` | `apr_openapi` |
| `data_validated` | **`True`** |
| `data_validated_at` | Trenutak provere |

Upisuju se **samo stvarno promenjena polja**. [P]

#### Korak 5 — brojači [P]

| Brojač | Značenje |
|---|---|
| `checked` | Ukupno provereno |
| `updated` | Nešto je promenjeno |
| `unchanged` | Sve isto |
| `missing_maticni_broj` | **Partner nema matični broj** — preskočen |
| `not_found` | **Nije pronađen u APR-u** |

### 8. Primer

| Partner | Matični broj | APR `NazivStatus` | `is_active` | Brojač |
|---|---|---|---|---|
| AUTODEKI DOO | `20123456` | `Активан` | **Da** | `updated` / `unchanged` |
| STARI DOBAVLJAČ | `07654321` | `Брисан` | **Ne** | `updated` |
| FIZIČKO LICE | *(prazno)* | — | nepromenjeno | `missing_maticni_broj` |
| NOVI PARTNER | `21999999` | *(nema ga)* | nepromenjeno | `not_found` |

> Za partnere u kategorijama `missing_maticni_broj` i `not_found` **ništa se ne menja** —
> `is_active` ostaje kakav je bio. To je namerno: odsustvo u APR-u nije dokaz gašenja.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `ugovori_partner`: `is_active`, `apr_status`, `apr_checked_at`, `data_validated` |
| Kada se osvežava | **Ručno** — nije u rasporedu zakazanih poslova |
| Kontrola | `apr_checked_at` pokazuje kada je partner poslednji put proveren |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **SSL greška** | **Ponavlja se bez provere potvrde** | **P-40** |
| Partner bez matičnog broja | Preskače se, broji se zasebno | Ispravno |
| Partner nije u APR-u | Ništa se ne menja | Ispravno |
| Status napisan drugačije | **Tretira se kao neaktivan** | **P-40** |
| APR nedostupan | Ceo prenos ne uspeva | Vidljivo |
| Fizičko lice | Nema matični broj — nikad se ne proverava | Očekivano |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Osnov povezivanja je matični broj | Potvrđeno | `apr_openapi.py:84` | — |
| Dopuna vodećim nulama do 8 cifara | Potvrđeno | `apr_openapi.py:31` | — |
| Aktivan samo za tačno `активан` | Potvrđeno | `apr_openapi.py:35` | **P-40** |
| Prazan naziv ne briše postojeći | Potvrđeno | `apr_openapi.py:58` | — |
| **Zaobilaženje provere potvrde pri SSL grešci** | **Potvrđeno** | `apr_openapi.py:40-43` | **P-40** |
| Provera nije zakazana | Potvrđeno | Nije u `EXPECTED_PERIODIC_TASKS` | — |

---

## U-03 — Preuzimanje menica iz registra NBS

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Ažuriraj izlazne menice“ |
| Tehnički naziv | `sync_izlazne_menice()`, `scrape()` |
| Putanja | [`menice/services.py:164`](../../../menice/services.py#L164), [`menice/scraper.py`](../../../menice/scraper.py) |
| Adresa | `/menice/izlazna/azuriraj/` |

### 2. Poslovna svrha

Preuzima podatke o **menicama koje je IMS izdao** iz **Registra menica i ovlašćenja
Narodne banke Srbije**, da bi finansije imale pregled obaveza po menicama bez ručnog
prepisivanja.

### 3. Korisnici rezultata

Finansije, pravna služba.

### 4. Ulazni podaci

| Podatak | Podrazumevana vrednost | Napomena |
|---|---|---|
| **Poreski broj (PIB)** | **`100223617`** | PIB Instituta IMS |
| Matični broj | prazno | opciono |
| Serijski broj menice | prazno | opciono |
| Datum registracije | prazno | opciono |
| Veličina strane | 100 | |
| Preuzimanje avalista | **uključeno** | |
| Najviše strana | bez ograničenja | |
| Rok | 30 sekundi | |

**Izvor:** `https://webappcenter.nbs.rs/PnWebApp` — javna pretraga registra menica,
čita se **razlaganjem HTML stranice** (`BeautifulSoup`). [P]

### 6. Tačan postupak

#### Korak 1 — preuzimanje [P]

Pretraga registra po PIB-u dužnika, strana po strana. Za svaku menicu se opciono
preuzimaju i **avalisti**, sa zasebne adrese.

#### Korak 2 — normalizacija zapisa [P]

Dvadeset polja iz registra se preslikava u evidenciju. Pretvaranje vrednosti:

| Vrsta | Polja | Pravilo |
|---|---|---|
| **Datumi** | datum izdavanja, dospeća, registracije | Oblici `DD.MM.GGGG`, `DD/MM/GGGG`, `GGGG-MM-DD`; prateća tačka se uklanja |
| **Iznosi** | iznos menice, iznos iz osnova | Prepoznaje **oba zapisa decimale** (vidi ispod) |
| **Celi brojevi** | strana rezultata, redni broj, broj avalista | Preko `float`, pa u ceo broj |
| Ostalo | tekst | Očišćen od razmaka; prazno → prazno |

**Prepoznavanje decimalnog zapisa [P]:**

| Ulaz | Tumačenje | Rezultat |
|---|---|---|
| `1.234.567,89` | zarez je poslednji → **evropski** | `1234567.89` |
| `1,234,567.89` | tačka je poslednja → **engleski** | `1234567.89` |
| `1234,89` | samo zarez | `1234.89` |
| `1234.89` | samo tačka | `1234.89` |

#### Korak 3 — prepoznavanje postojeće menice [P]

> **serijski broj** + **datum registracije** *(+ redni broj, ako postoji)*

| Situacija | Postupak |
|---|---|
| Nema serijskog broja **ili** datuma registracije | **Preskače se** (`skipped`) |
| Menica pronađena | Ažuriraju se **samo polja iz registra** |
| Menica nije pronađena | Upisuje se nova |

> **[P] Ključna zaštita:** ažuriraju se **samo polja iz NBS registra** (`NBS_FIELDS`).
> Ručno uneti podaci — **broj ugovora, datum ugovora, OJ, fizička lokacija, napomena,
> interni status** — **ostaju netaknuti**.

#### Korak 4 — brojači [P]

`fetched`, `created`, `updated`, `unchanged`, `skipped`.

### 8. Primer

| Serijski broj | Datum registracije | Redni broj | Ishod |
|---|---|---|---|
| `AA1234567` | 15.03.2026. | 1 | **Nova** |
| `AA1234567` | 15.03.2026. | 1 | **Bez izmene** *(drugi prolaz)* |
| `AA1234567` | 15.03.2026. | 1, iznos promenjen | **Ažurirano** — ručna polja ostaju |
| *(bez serijskog broja)* | 20.03.2026. | — | **Preskočeno** |

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `menica` (tabela bez prefiksa aplikacije) |
| Kada se osvežava | **Ručno** — nije u rasporedu zakazanih poslova |
| Upotreba | Pregled menica, povezivanje sa ugovorima (U-04) |
| Kontrola | Brojači prolaza; `skipped` ukazuje na nepotpune zapise u registru |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Promena izgleda stranice NBS-a** | **Preuzimanje prestaje da radi** | **P-41** |
| Zapis bez serijskog broja ili datuma registracije | Preskače se | Ispravno |
| Dve menice sa istim ključem | Uzima se **prva po ID-u** | Vidljivo |
| Ručno uneti podaci | **Ne prepisuju se** | Ispravno |
| Menica uklonjena iz registra | **Ostaje** u evidenciji | Namerno — `interni_status` |
| PIB nije zadat | Koristi se **podrazumevani PIB IMS-a iz koda** | **P-41** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Ključ je serijski broj + datum registracije (+ redni broj) | Potvrđeno | `services.py:152-161` | — |
| Ažuriraju se samo polja iz registra | Potvrđeno | `services.py:203`, `NBS_FIELDS` | — |
| Prepoznaju se oba decimalna zapisa | Potvrđeno | `services.py:94-100` | — |
| Nepotpuni zapisi se preskaču | Potvrđeno | `services.py:197-199` | — |
| **PIB IMS-a upisan kao podrazumevana vrednost** | **Potvrđeno** | `services.py:166` | **P-41** |
| **Preuzimanje zavisi od izgleda stranice NBS-a** | **Potvrđeno** | `menice/scraper.py` | **P-41** |

---

## U-04 — Povezivanje menica i garancija sa ugovorima

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Menice uz ugovor“, „Garancije uz ugovor“ |
| Tehnički naziv | `ContractMenicaLink`, `ContractGuarantee` |
| Putanja | [`ugovori/models.py:738`](../../../ugovori/models.py#L738), [`ugovori/models.py:816`](../../../ugovori/models.py#L816) |

### 2. Poslovna svrha

Ugovor često ima **sredstva obezbeđenja** — menice ili bankarske garancije.
Ova veza pokazuje **koja menica pokriva koji ugovor**, da bi se pri isteku ugovora
znalo šta treba vratiti.

### 6. Tačan postupak

#### Veza sa menicom [P]

Jedna veza pokazuje na **tačno jednu** menicu, i to na **jednu od dve vrste**:

| Polje | Vrsta menice |
|---|---|
| `menica` | Menica iz registra NBS (izlazna ili ulazna) |
| `ulazna_menica` | Ulazna menica iz sopstvene evidencije |

> **[P] Kontrola:** *„Izaberite tacno jednu menicu.“* — ne sme biti ni nijedna ni obe.

**Prikaz veze [P]** se prilagođava vrsti:

| Podatak | Ako je `menica` | Ako je `ulazna_menica` |
|---|---|---|
| Oznaka | Serijski broj ili `Menica <id>` | Serijski broj |
| Vrsta | Izlazna / ulazna menica | „Ulazna menica“ |
| Partner | Naziv dužnika ili izdavalac | Naziv pravnog lica |
| **Iznos** | `iznos_menice` + valuta | `procenat_iznos` + **jedinica vrednosti** |

> **[P] Pažnja na iznos ulazne menice:** jedinica vrednosti može biti **`RSD`, `EUR`
> ili `PROCENAT`**. Kada je `PROCENAT`, vrednost **nije novčani iznos** nego procenat
> vrednosti ugovora. Sabiranje te kolone bez provere jedinice daje besmislen zbir.

Brisanje menice je **zabranjeno** dok postoji veza (`PROTECT`). [P]

#### Garancija uz ugovor [P]

| Polje | Sadržaj |
|---|---|
| `guarantee_number` | Broj garancije |
| `issuer` | Izdavalac / banka |
| `beneficiary` | Korisnik garancije |
| `amount`, `currency` | Iznos i valuta |
| `valid_from`, `valid_to` | Period važenja |
| `status` | **Aktivna / Vraćena / Istekla / Stornirana** |

**Kontrola [P]:** *„Datum 'Vazi do' ne sme biti pre datuma 'Vazi od'.“*

#### Oznake na ugovoru [P]

Ugovor ima tri zasebne oznake: `has_incoming_menice`, `has_outgoing_menice`,
`has_guarantees`.

> **[Z]** To su **ručne oznake**, nezavisne od stvarno povezanih zapisa. Sistem ih
> **ne usklađuje automatski** — ugovor može imati povezanu menicu, a oznaku isključenu.

### 8. Primer

| Ugovor | Veza | Vrsta | Partner | Iznos |
|---|---|---|---|---|
| U-2026/15 | Menica `AA1234567` | Izlazna menica | AUTODEKI DOO | 500.000,00 RSD |
| U-2026/15 | Ulazna menica `BB7654321` | Ulazna menica | GRADNJA DOO | **10,00 Procenat** |
| U-2026/15 | Garancija `G-2026-7` | — | Banka Poštanska | 1.000.000,00 RSD, do 31.12.2026. |

> Druga stavka je **10% vrednosti ugovora**, ne 10 dinara.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `ugovori_contract_menica_link`, `ugovori_contract_guarantee` |
| Trag | Ko je i kada uspostavio vezu |
| Upotreba | Detalj ugovora; pregled pri isteku ugovora |
| Kontrola | Uporediti oznake na ugovoru sa stvarnim vezama |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Izabrane obe vrste menice ili nijedna | Odbija se |
| Brisanje povezane menice | **Zabranjeno** |
| Ista menica na više ugovora | **Dozvoljeno** — nema zabrane |
| Iznos u procentima | Prikazuje se sa jedinicom, **ne sme se sabirati sa dinarima** |
| Oznake na ugovoru netačne | **Nema provere** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Tačno jedna menica po vezi | Potvrđeno | `models.py:780-782` |
| Brisanje povezane menice je zabranjeno | Potvrđeno | `models.py:745-760` (`PROTECT`) |
| Jedinica vrednosti može biti procenat | Potvrđeno | `menice/models.py:96-102`, `models.py:808-812` |
| Kontrola perioda garancije | Potvrđeno | `models.py:888-890` |
| **Oznake na ugovoru su ručne** | **Zaključeno** | Nema usklađivanja u kodu |

---

## Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-40** | Provera partnera u APR-u **zaobilazi proveru SSL potvrde** kada prvi pokušaj ne uspe (`verify=False`), i prepoznaje kao aktivan **samo tačan tekst `активан`** — svaki drugi zapis statusa vodi u `is_active = False`. | **Srednja** |
| **P-41** | Preuzimanje menica zavisi od **izgleda HTML stranice NBS-a** i koristi **PIB Instituta upisan u kod** kao podrazumevanu vrednost. Promena stranice zaustavlja preuzimanje bez jasne poruke. | **Srednja** |

## Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q38** | Koje sve vrednosti `NazivStatus` vraća APR? Ako postoje oblici poput „Активан — у ликвидацији“, sadašnja provera bi ih označila kao **neaktivne**. |
| **Q39** | Treba li preuzimanje menica iz NBS-a i provera partnera u APR-u da budu **zakazani poslovi**, umesto ručnog pokretanja? |
| **Q40** | Da li oznake „Ima ulazne menice / izlazne menice / garancije“ na ugovoru treba da se **usklađuju automatski** sa stvarno povezanim zapisima? |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.9. Nabavka](06-09-nabavka.md) | Predmeti nabavke i fakture |
| [4. Baza podataka](../04-baza-podataka.md#49-ugovori--ugovori) | Tabele Ugovora i Menica |
| [7. Integracije](../07-integracije.md) | APR i NBS |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema |
