# 6.2. Flota — obračuni goriva

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
>
> Zajednička implementacija svih obračuna u ovom poglavlju:
> [`fleet/support/fuel.py`](../../../fleet/support/fuel.py).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [V-03](#v-03--neto-iznos-goriva-iz-bruto-iznosa) | Neto iznos goriva iz bruto iznosa | — |
| [V-04](#v-04--iznosi-omv-transakcije) | Iznosi OMV transakcije | — |
| [V-05](#v-05--iznosi-nis-transakcije) | Iznosi NIS transakcije | — |
| [V-06](#v-06--prečišćavanje-omv-transakcija) | Prečišćavanje OMV transakcija (duplikati i odjeci računa) | — |
| [V-01](#v-01--prosečna-potrošnja-goriva-poslednjih-10-točenja) | Prosečna potrošnja goriva (poslednjih 10 točenja) | **P-02** |
| [V-02](#v-02--prosečna-potrošnja-goriva-za-ceo-vek-vozila) | Prosečna potrošnja goriva za ceo vek vozila | — |
| [V-21](#v-21--gorivo-po-šifri-posla) | Gorivo po šifri posla | — |
| [V-23](#v-23--obračun-goriva-na-putnom-nalogu-vozila) | Obračun goriva na putnom nalogu vozila | — |

Registar problema: [10. Poznati problemi](../10-poznati-problemi.md).

---

## Zajednička osnova: šta se uopšte smatra gorivom

Pre svakog obračuna sistem odbacuje stavke koje nisu gorivo. Prepoznavanje ide
**po nazivu proizvoda**, ne po šifri. [P]

Ključne reči (`FUEL_PRODUCT_KEYWORDS`), traže se **bilo gde u nazivu, bez obzira na velika
i mala slova** [P]:

```
dizel, diesel, benzin, petrol, maxxmotion, maxxm, bmb,
lpg, autogas, cng, tng, ngv, adblue, ad blue
```

| Polje koje se proverava | Izvor |
|---|---|
| `product_inv` | OMV (`fleet_transactionomv`) |
| `naziv_proizvoda` | NIS (`fleet_transactionnis`) |

**AdBlue je poseban slučaj [P]:** računa se kao „proizvod goriva“ u opštim pregledima,
ali se **izuzima** iz obračuna na putnom nalogu vozila (V-23), jer nije gorivo koje
učestvuje u potrošnji po 100 km.

| Funkcija | Uključuje AdBlue |
|---|---|
| `filter_omv_fuel_queryset` / `filter_nis_fuel_queryset` | Da |
| `filter_omv_travel_order_fuel_queryset` / `filter_nis_travel_order_fuel_queryset` | **Ne** |

> **Rizik [Z]:** proizvod čiji naziv ne sadrži nijednu ključnu reč **neće biti prepoznat
> kao gorivo** i tiho će ispasti iz svih obračuna. Novi naziv proizvoda kod dobavljača
> zahteva dopunu liste u kodu.

---

## V-03 — Neto iznos goriva iz bruto iznosa

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Iznos neto“ / „Neto“ |
| Tehnički naziv | `net_amount_from_gross_and_vat()` |
| Putanja | [`fleet/support/fuel.py:65`](../../../fleet/support/fuel.py#L65) |

### 2. Poslovna svrha

Fakture dobavljača goriva iskazuju **bruto** iznos (sa PDV-om). Za poređenje troškova
među vozilima, centrima i šiframa posla potreban je **neto** iznos, jer je PDV za
Institut odbitna stavka i ne predstavlja stvarni trošak.

### 3. Korisnici rezultata

Služba voznog parka (izveštaji o gorivu), rukovodioci centara, uprava.
Neto iznos ulazi u obračun **troška po kilometru** (V-07) i u **izveštaj goriva po
šifri posla** (V-21).

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | JM | Obavezno | Ko unosi | Izvor |
|---|---|---|---|---|---|---|---|
| Bruto iznos (OMV) | Bruto | `fleet_transactionomv.gross_cc` | `decimal(10,2)` | RSD | Ne | Niko — automatski | OMV portal |
| PDV (OMV) | PDV | `fleet_transactionomv.vat` | `decimal(10,2)` | RSD | Ne | Niko — automatski | OMV portal |
| Bruto iznos (NIS) | Bruto | `fleet_transactionnis.total` | `decimal(12,2)` | RSD | Da | Niko — automatski | NIS portal |

### 5. Poreklo podataka

```
OMV portal (fleet.omv.com)  ──Selenium──► CSV ──► fleet_transactionomv.gross_cc, .vat
NIS portal (cards.nis.rs)   ──Selenium──► CSV ──► fleet_transactionnis.total
                                                          │
                                                          ▼
                                          net_amount_from_gross_and_vat()
                                                          │
                                                          ▼
                             ekran „Fakture goriva“, izveštaji, trošak po km
```

### 6. Tačan postupak obračuna

Postoje **dva puta**, u zavisnosti od toga da li je PDV poznat. [P]

**Slučaj A — PDV je poznat (nije NULL):**

> neto = bruto − PDV

**Slučaj B — PDV nije poznat (NULL):**

> neto = bruto × 5 / 6

Konstante u kodu: `VAT_NET_NUMERATOR = 5`, `VAT_NET_DENOMINATOR = 6`. [P]

**Zašto 5/6 [Z]:** pri stopi PDV-a od 20%, bruto = neto × 1,20, pa je
neto = bruto / 1,20 = bruto × 5/6 ≈ bruto × 0,8333.

> **Ograničenje [Z]:** koeficijent 5/6 je **tvrdo upisan u kod**. Stavka sa drugom
> poreskom stopom (npr. 10%) bila bi pogrešno preračunata. Promena opšte stope PDV-a
> zahteva izmenu koda.

**Zaokruživanje [P]:** rezultat se kvantizuje na **2 decimale, `ROUND_HALF_UP`**
(pola naviše). Isto važi i za bruto iznos.

**NULL i nedostajuće vrednosti [P]:**

| Situacija | Rezultat |
|---|---|
| Bruto je NULL | **`None`** — ne 0 |
| Bruto je `NaN` | **`None`** |
| Bruto nije pretvoriv u broj | **`None`** |
| PDV je NULL | Primenjuje se slučaj B (× 5/6) |

Razlika između „nema podatka“ (`None`) i „iznos je nula“ je namerno očuvana. [P]

**U SQL upitima** se ista logika izražava kroz `Case`/`When`
(`_amount_minus_vat_or_without_vat_expression`), gde se NULL prvo zamenjuje nulom
(`Coalesce`) — pa se u agregacijama ponaša kao 0. [P]

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/fuel.py` |
| Funkcije | `net_amount_from_gross_and_vat()`, `_amount_for_decimal()`, `_quantize_money()` |
| SQL varijanta | `_amount_minus_expression()`, `_amount_without_vat_expression()`, `_amount_minus_vat_or_without_vat_expression()` |
| Tip rezultata | `DecimalField(max_digits=14, decimal_places=2)` |
| Ekrani | `/fuel-transactions/`, `/izvestaji/gorivo-sifra-posla/*`, detalj vozila |

### 8. Primer obračuna

> Ilustrativni primer sa zaokruženim brojevima.

**Slučaj A — PDV poznat (OMV):**

| Korak | Vrednost |
|---|---|
| Bruto (`gross_cc`) | 12.000,00 RSD |
| PDV (`vat`) | 2.000,00 RSD |
| Neto = 12.000,00 − 2.000,00 | **10.000,00 RSD** |

**Slučaj B — PDV nepoznat (NIS):**

| Korak | Vrednost |
|---|---|
| Bruto (`total`) | 12.000,00 RSD |
| PDV | nije u izvoru |
| Neto = 12.000,00 × 5 / 6 = 10.000,000000 | **10.000,00 RSD** |

**Slučaj B sa zaokruživanjem:**

| Korak | Vrednost |
|---|---|
| Bruto | 7.499,99 RSD |
| 7.499,99 × 5 / 6 = 6.249,991666… | |
| `ROUND_HALF_UP` na 2 decimale | **6.249,99 RSD** |

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Iznos bez PDV-a za jednu transakciju goriva |
| Format | Decimalan broj, 2 decimale, RSD |
| Gde se čuva | **Nigde** — računa se u trenutku prikaza |
| Kada se ponovo računa | Pri svakom otvaranju ekrana ili izveštaja |
| Može li korisnik da ga izmeni | Ne |
| Istorija promene | Ne postoji — menja se samo ako se promeni izvorni iznos |

> **Napomena [P]:** postoji i tabela `fleet_fuelconsumption` sa kolonama `cost_bruto`
> i `cost_neto` koje **jesu** sačuvane. Njih puni sinhronizacija, a **trošak po kilometru
> (V-07) koristi `cost_bruto` iz te tabele**, ne ovaj izračunati neto iznos.
> Vidi upozorenje u V-07.

### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Ekran „Fakture goriva“ | Kolona „Neto“, zbir po računu |
| Izveštaj gorivo po šifri posla (V-21) | Kolona „neto“, zbir po šifri i polumesecu |
| Detalj vozila | Lista transakcija |
| Excel izvoz | Ista vrednost |

> **[N] Q3:** nije potvrđeno da li računovodstvo preuzima ovaj iznos i za koji dokument.
> Sistem ga ne knjiži i ne prenosi automatski.

### 11. Kontrola i ručna provera

**Kontrolna formula:**

- Kada je PDV poznat: `neto + PDV = bruto` — mora važiti tačno.
- Kada PDV nije poznat: `neto × 1,2 = bruto` sa odstupanjem do 0,01 RSD zbog zaokruživanja.

**Dozvoljeno odstupanje:** ±0,01 RSD po stavci (zaokruživanje).
Pri zbiru od N stavki odstupanje može narasti do ±0,01 × N.

**Tipični uzroci razlike:**

| Uzrok | Kako se prepoznaje |
|---|---|
| Stavka sa stopom PDV-a različitom od 20% | `neto × 1,2 ≠ bruto` za pojedinačnu stavku |
| Prazan bruto iznos | Neto je prazan, ne nula |
| Zbir uključuje stavke koje nisu gorivo | Uporediti sa filterom naziva proizvoda |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje sistema |
|---|---|
| Bruto je NULL | Vraća `None`; u agregacijama se ponaša kao 0 |
| Bruto je `NaN` | Vraća `None` |
| PDV veći od bruto iznosa | **Daje negativan neto** — sistem to ne sprečava |
| Stopa PDV-a nije 20% | **Pogrešan rezultat** u slučaju B |
| Bruto je 0 | Neto je 0,00 (nije `None`) |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Neto = bruto − PDV kada je PDV poznat | Potvrđeno | `fuel.py:65-72` | — |
| Neto = bruto × 5/6 kada PDV nije poznat | Potvrđeno | `fuel.py:72` | — |
| Zaokruživanje `ROUND_HALF_UP` na 2 decimale | Potvrđeno | `fuel.py:59-62` | — |
| Koeficijent 5/6 odgovara stopi PDV-a od 20% | **Zaključeno** | Matematika, nije komentarisano u kodu | Potvrditi da su sve stavke goriva po stopi 20% |
| Rezultat se nigde ne čuva | Potvrđeno | Nema upisa u modele | — |
| Računovodstvo preuzima ovaj iznos | **Nepotvrđeno** | — | **Q3** |

---

## V-04 — Iznosi OMV transakcije

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Bruto“ i „Neto“ u listama OMV transakcija |
| Tehnički naziv | `omv_charged_gross_net_amounts()` |
| Putanja | [`fleet/support/fuel.py:75`](../../../fleet/support/fuel.py#L75) |

### 2. Poslovna svrha

Vraća par (bruto, neto) za jednu OMV transakciju, iz onoga što je OMV stvarno naplatio.

### 3. Korisnici rezultata

Isti kao V-03.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | JM |
|---|---|---|
| Naplaćeni bruto iznos | `fleet_transactionomv.gross_cc` | RSD |
| PDV | `fleet_transactionomv.vat` | RSD |

> **[P] Važno:** koristi se `gross_cc` („Gross CC“ iz izvora), **ne** kolona `amount`.
> Tabela sadrži i `amount`, `discount`, `surcharge`, `cost_1`, `cost_2`, `amount_other` —
> nijedna od njih **ne ulazi** u ovaj obračun.

### 5. Poreklo podataka

OMV Fleet portal → Selenium preuzimanje → CSV → `fleet_transactionomv`.
Dnevno u 05:10 (putnička) i 06:10 (teretna vozila). [P]

### 6. Tačan postupak obračuna

1. Ako je `gross_cc` prazan ili nije broj → vraća `(None, None)`.
2. Bruto = `gross_cc`, zaokruženo na 2 decimale `ROUND_HALF_UP`.
3. Neto = rezultat obračuna **V-03** nad `gross_cc` i `vat`.

### 7. Tehnička implementacija

`fleet/support/fuel.py: omv_charged_gross_net_amounts()`.
Poziva se iz `get_fuel_invoice_lines()`, `get_vehicle_fuel_transaction_rows()`,
`_detail_from_omv()` i detalja putnog naloga vozila. [P]

### 8. Primer obračuna

| Korak | Vrednost |
|---|---|
| `gross_cc` | 9.600,00 RSD |
| `vat` | 1.600,00 RSD |
| Bruto | **9.600,00 RSD** |
| Neto = 9.600,00 − 1.600,00 | **8.000,00 RSD** |

### 9–13.

Isto kao V-03. Dodatna razlika:

| Slučaj | Ponašanje |
|---|---|
| `gross_cc` prazan, ali `amount` popunjen | Vraća `(None, None)` — **`amount` se ne koristi kao zamena** u ovom obračunu |

> **[P] Izuzetak:** u detalju **putnog naloga vozila** (V-23) koristi se drugačije
> pravilo — tamo je iznos `gross_cc or amount`. To je jedina tačka u sistemu gde
> `amount` služi kao rezerva.

---

## V-05 — Iznosi NIS transakcije

### 1. Naziv

| | |
|---|---|
| Tehnički naziv | `nis_charged_gross_net_amounts()` |
| Putanja | [`fleet/support/fuel.py:82`](../../../fleet/support/fuel.py#L82) |

### 2–5.

Isto kao V-04, ali za NIS. Izvor: NIS portal `cards.nis.rs`, dnevno u 04:20. [P]

| Poslovni naziv | Tabela i kolona |
|---|---|
| Ukupan iznos | `fleet_transactionnis.total` |

> **[P]** NIS izvor **nema kolonu PDV**. Tabela ima `total` i `total_sa_kase`;
> koristi se **`total`**.

### 6. Tačan postupak obračuna

1. Ako je `total` prazan ili nije broj → `(None, None)`.
2. Bruto = `total`, zaokruženo na 2 decimale.
3. Neto = **uvek** po slučaju B: `total × 5 / 6`, jer PDV nije dostupan.

### 8. Primer obračuna

| Korak | Vrednost |
|---|---|
| `total` | 6.000,00 RSD |
| Bruto | **6.000,00 RSD** |
| Neto = 6.000,00 × 5 / 6 | **5.000,00 RSD** |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| NIS stavka po stopi različitoj od 20% | **Pogrešan neto** — nema načina da se prepozna |
| Razlika `total` i `total_sa_kase` | Zanemaruje se; koristi se `total` |
| Popust (`popust`) | Nije posebno obrađen — pretpostavka je da je već u `total` [Z] |

### 13. Status pouzdanosti

| Tvrdnja | Status | Pitanje |
|---|---|---|
| NIS neto se uvek računa kao × 5/6 | Potvrđeno | — |
| Koristi se `total`, ne `total_sa_kase` | Potvrđeno | — |
| Popust je već sadržan u `total` | **Zaključeno** | Potvrditi sa NIS-om ili poređenjem sa fakturom |

---

## V-06 — Prečišćavanje OMV transakcija

> **Ovo je najvažniji obračun u poglavlju.** Bez njega su svi zbirovi goriva pogrešni.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Nema — radi nevidljivo, u pozadini svih OMV pregleda |
| Tehnički naziv | `filter_omv_fuel_queryset()` |
| Putanja | [`fleet/support/fuel.py:239`](../../../fleet/support/fuel.py#L239) |

### 2. Poslovna svrha

OMV izvor **sadrži istu transakciju više puta**, u različitim stanjima obrade
(pre i posle fakturisanja, sa ispravljenim datumom fakture). Sirovo sabiranje daje
**dvostruko ili višestruko uvećan trošak goriva**.

Ovaj korak bira **tačno jedan merodavan red** po stvarnom točenju.

### 3. Korisnici rezultata

Svi korisnici izveštaja o gorivu. Greška ovde direktno kvari trošak po kilometru,
izveštaje za upravu i obračun na putnom nalogu.

### 4. Ulazni podaci

Ceo skup `fleet_transactionomv`, filtriran na proizvode goriva.

| Kolona | Uloga u prečišćavanju |
|---|---|
| `license_plate_no`, `transaction_date`, `product_inv`, `voucher`, `quantity` | **Identitet točenja** |
| `invoice_date`, `transaction_date` | Provera ispravnosti datuma fakture |
| `invoiced` | Da li je red fakturisan |
| `invoice_no` | Broj fakture |
| `gross_cc`, `amount`, `mileage` | Poređenje identičnosti kod „odjeka“ |

### 5. Poreklo podataka

OMV Fleet portal → Selenium → CSV → `fleet_transactionomv`.
Jedinstveni ključ u bazi je
`(license_plate_no, transaction_date, product_inv, voucher, quantity)` — ali izvor
i dalje isporučuje **više redova sa različitim stanjem fakturisanja**, koji se razlikuju
po ostalim kolonama, pa ključ ne sprečava višestruke zapise istog točenja. [Z]

### 6. Tačan postupak obračuna

Tri koraka, tim redom [P]:

```
  svi OMV redovi sa proizvodom goriva
              │
              ▼
  KORAK 1  Izbaci redove sa neispravnim datumom fakture
              │      (invoice_date < datum transakcije)
              ▼
  KORAK 2  Za svako točenje zadrži samo JEDAN red
              │      (najbolji po prioritetu)
              ▼
  KORAK 3  Izbaci „odjeke“ računa
              │      (nefakturisani blizanci fakturisanog reda)
              ▼
      merodavan skup za sve obračune
```

#### Korak 1 — neispravan datum fakture

Izbacuje se svaki red gde je **datum fakture pre datuma transakcije**:

> `invoice_date < DATE(transaction_date)` → red se odbacuje

Funkcija: `_exclude_omv_stale_invoice_dates()` / `is_omv_invoice_date_stale()`. [P]

**Obrazloženje [Z]:** faktura ne može biti izdata pre nego što je gorivo natočeno;
takav red je zaostatak ranije obrade.

#### Korak 2 — jedan red po točenju

Redovi se grupišu po identitetu točenja:

> `(license_plate_no, transaction_date, product_inv, voucher, quantity)`

**Prazna polja se izjednačavaju** [P]: `product_inv` i `voucher` bez vrednosti računaju se
kao prazan tekst, a `quantity` bez vrednosti kao dogovorena zamena. Bez toga poređenje
`NULL = NULL` u SQL-u nije tačno, pa red bez vaučera ne bi našao ni samog sebe i **tiho bi
ispao iz svih pregleda goriva**.

> **Ispravljeno 18.09.2026.** — pre toga je svaka OMV transakcija bez vaučera ili bez
> količine nestajala sa svih ekrana goriva, bez ikakvog upozorenja. Zbog ispravke
> **iznosi goriva mogu biti veći nego ranije**; koliko — zavisi od toga koliko takvih
> zapisa ima u bazi. Videti [P-46](../10-poznati-problemi.md).

Unutar grupe bira se **prvi** red po redosledu [P]:

| Prioritet | Kriterijum | Smisao |
|---|---|---|
| 1 | `invoiced` opadajuće | Fakturisan red ima prednost nad nefakturisanim |
| 2 | `invoice_date` opadajuće | Novija faktura ima prednost |
| 3 | `id` opadajuće | Poslednji upisan red |

Funkcija: `_dedupe_omv_transaction_lines()`. [P]

> **[P] Bitno:** i ovaj izbor se pravi **nad skupom već očišćenim u koraku 1** —
> red sa neispravnim datumom fakture ne može biti izabran kao merodavan.

> **[P] Šta ključ NE obuhvata:** **iznos** (`gross_cc`, `amount`) ni **valutu**
> (`supplier_currency`). Dva reda koja se razlikuju **samo** po iznosu smatraju se istim
> točenjem, a koji preživljava odlučuje stanje fakturisanja — nikad iznos. Nije potvrđeno
> da takvi parovi postoje u stvarnim podacima; videti
> [P-47](../10-poznati-problemi.md), koji traži proveru nad bazom.

#### Korak 3 — „odjeci“ računa

Izbacuje se red koji ispunjava **sva tri** uslova [P]:

1. Postoji **drugi** red sa istim vrednostima
   `license_plate_no`, `product_inv`, `voucher`, `quantity`, `gross_cc`, `amount`,
   `mileage`, `invoice_date`, koji je `invoiced = True`, ima popunjen `invoice_no`
   različit od `voucher`, i nije isti red.
2. Posmatrani red **nije fakturisan** (`invoiced = False` ili NULL).
3. Kod posmatranog reda je **`invoice_no` jednak `voucher`**.

Funkcija: `_exclude_omv_receipt_echoes()`. [P]

**Poslovno objašnjenje [Z]:** dok račun nije fakturisan, OMV kao „broj fakture“ prikazuje
broj bona (`voucher`). Kada stigne prava faktura, pojavi se novi red sa stvarnim brojem
fakture. Stari red ostaje u izvoru kao **odjek** i mora se izbaciti.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/fuel.py` |
| Ulazna tačka | `filter_omv_fuel_queryset()` — filter goriva **+** tri koraka čišćenja |
| Samo čišćenje, bez filtera goriva | `deduplicate_omv_transactions()` — koristi ga izveštaj za upravu, koji sam razvrstava proizvode |
| Koraci | `_exclude_omv_stale_invoice_dates()`, `_dedupe_omv_transaction_lines()`, `_exclude_omv_receipt_echoes()` |
| Varijanta za putni nalog | `filter_omv_travel_order_fuel_queryset()` — dodatno izbacuje AdBlue |
| Srodno čišćenje u bazi | [`fleet/support/fuel_cleanup.py: cleanup_omv_fuel_data()`](../../../fleet/support/fuel_cleanup.py) |

> **[P] Dva različita mehanizma:** `filter_omv_fuel_queryset()` samo **filtrira pri
> čitanju** (ne menja podatke). `cleanup_omv_fuel_data()` je zasebna komanda koja
> **stvarno briše** duplikate iz baze i pokreće se ručno
> (`manage.py cleanup_omv_fuel_duplicates`).

**NIS nema ovaj problem [P]:** `filter_nis_fuel_queryset()` radi samo filter naziva proizvoda.

### 8. Primer obračuna

> Ilustrativni primer.

Izvor sadrži četiri reda za isto točenje (tablica `BG123-AA`, 40 l dizela, 12.000 RSD):

| # | `transaction_date` | `voucher` | `invoice_no` | `invoiced` | `invoice_date` | Ishod |
|---|---|---|---|---|---|---|
| 1 | 05.03.2026. | `V-777` | `V-777` | Ne | 01.03.2026. | **Izbačen u koraku 1** — faktura pre transakcije |
| 2 | 05.03.2026. | `V-777` | `V-777` | Ne | 31.03.2026. | Izbačen u koraku 3 — odjek reda 3 |
| 3 | 05.03.2026. | `V-777` | `F-12345` | Da | 31.03.2026. | **Zadržan** |
| 4 | 05.03.2026. | `V-777` | `F-12345` | Da | 20.03.2026. | Izbačen u koraku 2 — stariji `invoice_date` |

**Rezultat:** jedan red, 12.000 RSD bruto.
**Bez prečišćavanja:** 4 × 12.000 = 48.000 RSD — **četvorostruko uvećan trošak**.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Skup merodavnih OMV transakcija |
| Gde se čuva | Nigde — filter se primenjuje pri svakom čitanju |
| Kada se ponovo računa | Pri svakom otvaranju ekrana ili izveštaja |
| Može li korisnik da ga izmeni | Ne |

### 10. Upotreba rezultata

**Svaki** OMV obračun u sistemu polazi od ovog filtera: V-01, V-02, V-07, V-21, V-23,
izveštaji za upravu, detalj vozila, ekran „Fakture goriva“. [P]

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Broj redova pre i posle filtera | Uporediti `TransactionOMV.objects.count()` sa brojem posle `filter_omv_fuel_queryset()` |
| Sumnja na duplikat | Na ekranu „Fakture goriva“ proveriti da li se isti bon (`voucher`) pojavljuje dvaput |
| Poređenje sa fakturom dobavljača | Zbir bruto iznosa po broju fakture mora odgovarati iznosu na papirnoj fakturi OMV-a |

**Najpouzdanija kontrola [Z]:** zbir po broju fakture (`invoice_no`) uporediti sa
stvarnom fakturom OMV-a za taj mesec.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Rizik |
|---|---|---|
| Isto točenje sa **različitom količinom** u dva reda | Tretiraju se kao **dva različita točenja** | **Dupliranje ostaje** |
| Isto točenje sa različitim `voucher` | Tretiraju se kao dva točenja | Dupliranje ostaje |
| Nefakturisan red bez fakturisanog parnjaka | Zadržava se | Ispravno |
| Fakturisan red kod koga je `invoice_no = voucher` | **Ne** izbacuje se (uslov 3 koraka 3 traži nefakturisan red) | Ispravno |
| Svi redovi imaju neispravan datum fakture | **Točenje potpuno nestaje** iz obračuna | **Tiho gubljenje podatka** |
| Proizvod nije prepoznat kao gorivo | Ne ulazi ni u jedan obračun | Tiho gubljenje podatka |

> **Najveći rizik [Z]:** ako izvor promeni količinu ili broj bona između dva preuzimanja,
> mehanizam **neće** prepoznati duplikat. Zato postoji i zasebna komanda za čišćenje baze.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Tri koraka i njihov redosled | Potvrđeno | `fuel.py:226-240` | — |
| Identitet točenja je petorka kolona | Potvrđeno | `fuel.py:164-175` | — |
| Prioritet izbora: `invoiced`, `invoice_date`, `id` | Potvrđeno | `fuel.py:190` | — |
| Uslovi za „odjek“ računa | Potvrđeno | `fuel.py:194-219` | — |
| Prazna polja se izjednačavaju pri poređenju | Potvrđeno | `fuel.py:159-175` | Rešeno, **P-46** |
| **Iznos i valuta nisu deo ključa** | **Potvrđeno** | `fuel.py:164-175` | **P-47** |
| `voucher` je broj bona pre fakturisanja | **Zaključeno** | Iz logike filtera, nije dokumentovano | Potvrditi sa OMV-om |
| Filter ne menja podatke u bazi | Potvrđeno | Samo `filter`/`exclude` | — |

---

## V-01 — Prosečna potrošnja goriva (poslednjih 10 točenja)

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Prosečna potrošnja“ (l/100 km) |
| Tehnički naziv | `calculate_average_fuel_consumption()` |
| Putanja | [`fleet/support/fuel.py:320`](../../../fleet/support/fuel.py#L320) |

### 2. Poslovna svrha

Pokazuje **skorašnju** potrošnju vozila, radi uočavanja kvara, nepravilne vožnje ili
nepravilnog evidentiranja goriva.

### 3. Korisnici rezultata

Služba voznog parka, garaža, rukovodioci centara.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | JM | Obavezno |
|---|---|---|---|
| Datum točenja | `fleet_fuelconsumption.date` | — | Da |
| Količina | `fleet_fuelconsumption.amount` | litar | Da |
| Kilometraža | `fleet_fuelconsumption.mileage` | km | Da (ali može biti 0) |

> **[P]** Obračun čita **`fleet_fuelconsumption`**, a ne sirove OMV/NIS tabele.

### 5. Poreklo podataka

```
OMV / NIS portal ──► fleet_transactionomv / fleet_transactionnis
                              │  (sinhronizacija)
                              ▼
                     fleet_fuelconsumption  (date, amount, mileage)
                              │
                              ▼
                  calculate_average_fuel_consumption()
```

### 6. Tačan postupak obračuna

1. Uzmi **poslednjih 10 točenja** vozila, sortirano po datumu **opadajuće**
   (indeks 0 = najnovije, indeks 9 = najstarije).
2. **Ako ih ima manje od 10 → rezultat je `None`** (ne prikazuje se ništa). [P]
3. Pronađi **`k`** — najmanji indeks od 0 do 8 na kome je `mileage > 0`,
   tj. **najnovije točenje sa unetom kilometražom**. [P]
4. Ako `k` nije pronađen ili je **`k > 4`** → rezultat je `None`. [P]
5. Inače se posmatra **simetričan prozor `[k, 9−k]`**:
   - ukupna količina = zbir `amount` za točenja sa indeksima od `k` do `9−k` (uključivo);
   - pređeni put = `mileage[k] − mileage[9−k]`;
   - ako je pređeni put > 0:

> **potrošnja (l/100 km) = ukupna količina / pređeni put × 100**

6. Inače → `None`.

**Kako nastaje uslov `k > 4` [P]:** kod traži `k` dvaput istom petljom, jednom
dodeljujući granicu `[9−k]`, drugi put `[k]`, pa proverava `9−k ≥ k`. To je ispunjeno
samo za `k ≤ 4`.

**Praktično značenje [Z]:** ako **pet ili više najnovijih** točenja nema unetu
kilometražu, prosečna potrošnja se **uopšte ne prikazuje**.

**Zaokruživanje [P]:** funkcija **ne zaokružuje** — vraća pun rezultat deljenja.
Zaokruživanje radi šablon pri prikazu.

**NULL i nula [P]:** točenja sa `mileage = 0` se ne mogu koristiti kao **novija**
granica, ali njihova količina **ulazi u zbir** ako se nalaze u prozoru.

> **[P] Utvrđeni nedostatak — starija granica se ne proverava.**
> Kod proverava `mileage > 0` samo pri traženju **novije** granice (indeks `k`).
> **Starija granica `[9−k]` se uzima bez ikakve provere.** Ako to točenje ima
> kilometražu 0, pređeni put postaje `mileage[k] − 0`, tj. **cela kilometraža vozila**,
> pa je izračunata potrošnja **drastično premala**, bez ijednog upozorenja.
>
> Primer: `k = 2`, `mileage[2] = 128.000`, `mileage[7] = 0` → pređeni put = 128.000 km
> umesto stvarnih ~1.500 km. Umesto ~6 l/100 km dobija se ~0,07 l/100 km.
>
> Vodi se kao problem **[P-02](../10-poznati-problemi.md#p-02--prosečna-potrošnja-ne-proverava-stariju-granicu)**,
> pitanje **Q13**. Kod nije menjan.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl i funkcija | `fleet/support/fuel.py: calculate_average_fuel_consumption()` |
| Ulazni podatak | `vehicle.fuel_consumptions` (povratna veza ka `FuelConsumption`) |
| Ekran | Detalj vozila |
| Testovi | `fleet/tests.py` |

### 8. Primer obračuna

> Ilustrativni primer, svih 10 točenja ima ispravnu kilometražu.

| Točenje (od najnovijeg) | Datum | Količina (l) | Kilometraža |
|---|---|---|---|
| 1 | 20.03. | 45 | 128.000 |
| 2–9 | … | ukupno 360 | … |
| 10 | 05.01. | 40 | 118.000 |

| Korak | Vrednost |
|---|---|
| Ukupna količina (10 točenja) | 445 l |
| Pređeni put = 128.000 − 118.000 | 10.000 km |
| Potrošnja = 445 / 10.000 × 100 | **4,45 l/100 km** |

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Prosečna potrošnja u litrima na 100 km, za period poslednjih 10 točenja |
| Format | Decimalan broj, l/100 km |
| Gde se čuva | Nigde — računa se pri prikazu |
| Može li korisnik da ga izmeni | Ne |
| Istorija | Ne postoji |

### 10. Upotreba rezultata

Prikaz na detalju vozila. **Ne ulazi** ni u jedan drugi obračun i **ne prenosi se**
u druge module. [P]

### 11. Kontrola i ručna provera

**Kontrolna formula:** zbir litara između dva očitavanja podeljen sa razlikom
kilometraže, puta 100.

| Provera | Kako |
|---|---|
| Vrednost izgleda previsoka | Proveriti da li je neko točenje pogrešno pripisano vozilu |
| Vrednost izgleda preniska | Proveriti da li nedostaju točenja u periodu |
| Nema vrednosti | Vozilo ima manje od 10 evidentiranih točenja |

**Dozvoljeno odstupanje [Z]:** rezultat je procena — očitavanja kilometraže na pumpi
unosi vozač i podložna su grešci. Odstupanje od deklarisane potrošnje do 20% nije
samo po sebi znak greške.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Manje od 10 točenja | `None` — ništa se ne prikazuje |
| Sva točenja sa `mileage = 0` | `None` |
| Pet ili više najnovijih točenja bez kilometraže (`k > 4`) | `None` |
| **Starije granično točenje ima `mileage = 0`** | **Potrošnja drastično premala, bez upozorenja** |
| Kilometraža opada (zamena brojača) | Pređeni put ≤ 0 → `None` |
| Točenje pripisano pogrešnom vozilu | **Pogrešan rezultat, bez upozorenja** |
| AdBlue među točenjima | **Ulazi u količinu** — uvećava potrošnju |

> **Rizik [Z]:** `fleet_fuelconsumption` **ne razdvaja AdBlue od goriva**. Za vozila
> koja koriste AdBlue prosečna potrošnja je zato precenjena.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Koristi tačno poslednjih 10 točenja | Potvrđeno | `fuel.py:321` | — |
| Manje od 10 točenja → nema rezultata | Potvrđeno | `fuel.py:323-324` | — |
| Formula količina / put × 100 | Potvrđeno | `fuel.py:346` | — |
| Prozor je simetričan `[k, 9−k]`, uslov `k ≤ 4` | Potvrđeno | `fuel.py:326-342` | — |
| **Starija granica se ne proverava na `mileage > 0`** | **Potvrđeno — nedostatak** | `fuel.py:330, 345` | **Q13** |
| Da li je takav rezultat ikada viđen u radu | **Nepotvrđeno** | — | **Q13** |
| AdBlue ulazi u količinu | **Zaključeno** | `FuelConsumption` nema vrstu proizvoda | Potvrditi da li je to željeno |

---

## V-02 — Prosečna potrošnja goriva za ceo vek vozila

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Prosečna potrošnja (ukupno)“ |
| Tehnički naziv | `calculate_average_fuel_consumption_ever()` |
| Putanja | [`fleet/support/fuel.py:350`](../../../fleet/support/fuel.py#L350) |

### 2. Poslovna svrha

Dugoročni prosek potrošnje vozila, za poređenje vozila istog tipa i za procenu
isplativosti zadržavanja vozila u floti.

### 3–5.

Isti izvori i korisnici kao V-01.

### 6. Tačan postupak obračuna

1. Prebroj sva točenja vozila. **Ako ih je manje od 2 → `None`.** [P]
2. Uzmi sva točenja sortirana po datumu **opadajuće**.
3. `first_entry` = **prvo** točenje (od najnovijeg) sa `mileage > 0`.
4. `last_entry` = **poslednje** točenje (od najstarijeg) sa `mileage > 0`.
5. Ako su obe pronađene i međusobno različite:
   - ukupna količina = zbir `amount` svih točenja u rasponu datuma
     `last_entry.date ≤ date ≤ first_entry.date`;
   - pređeni put = `first_entry.mileage − last_entry.mileage`;
   - ako je pređeni put > 0:

> **potrošnja (l/100 km) = ukupna količina / pređeni put × 100**

6. Inače → `None`.

**Razlike u odnosu na V-01 [P]:**

| | V-01 (poslednjih 10) | V-02 (ceo vek) |
|---|---|---|
| Obuhvat | Poslednjih 10 točenja | Sva točenja |
| Najmanji broj točenja | 10 | 2 |
| **Provera `mileage > 0` na novijoj granici** | Da | Da |
| **Provera `mileage > 0` na starijoj granici** | **Ne — nedostatak** | **Da — ispravno** |

> **[P]** V-02 je u ovom pogledu **ispravno** izveden: obe granice se biraju samo među
> točenjima sa kilometražom većom od nule. Nedostatak opisan u V-01 ovde **ne postoji**.

### 8. Primer obračuna

| Korak | Vrednost |
|---|---|
| Najnovije točenje sa kilometražom > 0 | 20.03.2026., 128.000 km |
| Najstarije točenje sa kilometražom > 0 | 10.02.2023., 18.000 km |
| Zbir količine u tom rasponu | 7.150 l |
| Pređeni put = 128.000 − 18.000 | 110.000 km |
| Potrošnja = 7.150 / 110.000 × 100 | **6,50 l/100 km** |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Manje od 2 točenja | `None` |
| Zamena brojača tokom veka vozila | **Pređeni put je pogrešan** — rezultat je besmislen |
| Vozilo preuzeto od drugog vlasnika | Početna kilometraža nije 0 — to je uzeto u obzir, koristi se razlika |
| AdBlue | Ulazi u količinu (isto kao V-01) |

> **Najveći rizik [Z]:** zamena brojača kilometraže. V-02 ne proverava da li kilometraža
> monotono raste, za razliku od obračuna kilometraže (V-13) koji to **proverava i
> prijavljuje**.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Najmanje 2 točenja | Potvrđeno | `fuel.py:353-354` |
| Granice su najnovije i najstarije točenje sa kilometražom > 0 | Potvrđeno | `fuel.py:360-368` |
| Zbir količine se ograničava rasponom datuma granica | Potvrđeno | `fuel.py:371` |
| Ne proverava se pad kilometraže | Potvrđeno | Nema takve provere |

---

## V-21 — Gorivo po šifri posla

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Gorivo po šifri posla“ — četiri ekrana: OMV/NIS × putnička/teretna |
| Tehnički naziv | `fuel_job_code_report()` |
| Putanja | [`fleet/support/fuel_reports.py:202`](../../../fleet/support/fuel_reports.py#L202) |
| Adrese | `/izvestaji/gorivo-sifra-posla/omv-putnicka/`, `…/omv-teretna/`, `…/nis-putnicka/`, `…/nis-teretna/` |

### 2. Poslovna svrha

Raspoređuje trošak goriva na **šifru posla koja je vozilu bila dodeljena na dan točenja**,
radi kontrole i prenosa troška na nosioce posla.

### 3. Korisnici rezultata

Služba voznog parka, računovodstvo, rukovodioci centara.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona |
|---|---|---|
| Godina | Godina | filter (`godina`) |
| Mesec | Mesec | filter (`mesec`) |
| Polovina meseca | Polovina | filter (`polovina`: 1 ili 2) |
| Transakcije OMV | — | `fleet_transactionomv` |
| Transakcije NIS | — | `fleet_transactionnis` |
| Istorijska dodela | — | `fleet_jobcode.assigned_date`, `organizational_unit` |
| Kategorija vozila | — | `fleet_vehicle.category` |

### 5. Poreklo podataka

```
 OMV/NIS transakcija  ──► prečišćavanje (V-06)  ──► samo vozila sa vezom
                                                          │
       fleet_jobcode (dodela ≤ datum transakcije)  ────────┤
                                                          ▼
                              grupisanje: šifra × godina × mesec × polovina
                                                          │
                                                          ▼
                                       zbirni pregled + detalj po šifri
```

### 6. Tačan postupak obračuna

1. **Izbor izvora:** OMV ili NIS, prema pozvanoj adresi.
2. **Filter goriva:** `filter_omv_fuel_queryset()` (uključuje prečišćavanje V-06) ili
   `filter_nis_fuel_queryset()`. [P]
3. **Samo povezana vozila:** `vehicle__isnull=False` — transakcije bez prepoznatog
   vozila **ispadaju iz izveštaja**. [P]
4. **Filter kategorije vozila:**
   - „putnička“ → `category = putnicko`;
   - „teretna“ → `category = teretno`.
   **Priključna vozila nikada nisu obuhvaćena.** [P]
5. **Filter perioda** (svi su opcioni):
   - godina → `godina(datum) = godina`;
   - mesec → `mesec(datum) = mesec`;
   - polovina `1` → dan ≤ 15; polovina `2` → dan > 15.
6. **Istorijska šifra posla** — za svaku transakciju se traži poslednja dodela
   sa `assigned_date <= datum transakcije`, sortirano `-assigned_date, -id`. [P]
   Uzimaju se šifra, naziv i **datum dodele**.
7. **Iznosi po stavci:** bruto i neto po V-04 (OMV) odnosno V-05 (NIS).
8. **Grupisanje** po petorki: `(šifra posla, naziv šifre, godina, mesec, polovina)`.
   Za svaku grupu: broj transakcija, zbir količine, zbir bruto, zbir neto.
9. **Prazna šifra** se prikazuje kao **`"Bez sifre"`**. [P]
10. **Sortiranje:** godina, mesec, polovina, šifra posla — sve rastuće. [P]

**Zaokruživanje [P]:** zbirovi se sabiraju iz već zaokruženih iznosa po stavci
(2 decimale), pa dodatnog zaokruživanja nema.

**NULL vrednosti [P]:** prazna količina, bruto ili neto se u zbiru računaju kao `0,00`.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/fuel_reports.py` |
| Ulazna tačka | `fuel_job_code_report(form, supplier, vehicle_type, sifpos)` |
| Istorijska šifra | `_historical_job_code_subqueries()` |
| Polumesec | `_half_month_case()` |
| Detalj | `_detail_from_omv()`, `_detail_from_nis()` |
| View-ovi | `fleet/views/reports.py: fuel_job_code_*_view` |

> **[Z] Napomena o izvedbi:** `fuel_job_code_report()` uvek prvo napravi **pun detaljni
> spisak** svih transakcija, pa tek onda grupiše i filtrira po šifri. Za velike periode
> to znači učitavanje celog skupa u memoriju.

### 8. Primer obračuna

> Ilustrativni primer, OMV, putnička vozila, mart 2026.

Tri transakcije istog vozila:

| Datum | Šifra posla vozila na taj dan | Količina | Bruto | Neto |
|---|---|---|---|---|
| 05.03.2026. | 413111 | 40 l | 9.600,00 | 8.000,00 |
| 12.03.2026. | 413111 | 38 l | 9.120,00 | 7.600,00 |
| 22.03.2026. | 413222 *(dodela od 15.03.)* | 42 l | 10.080,00 | 8.400,00 |

**Rezultat — tri grupe:**

| Šifra | Godina | Mesec | Polovina | Broj | Količina | Bruto | Neto |
|---|---|---|---|---|---|---|---|
| 413111 | 2026 | 3 | 1 | 2 | 78 l | 18.720,00 | 15.600,00 |
| 413222 | 2026 | 3 | 2 | 1 | 42 l | 10.080,00 | 8.400,00 |

> Ključno: treće točenje ide na **novu** šifru, jer je dodela promenjena 15.03.,
> a ne na trenutnu šifru vozila.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Trošak i količina goriva po šifri posla i polumesecu |
| Format | Tabela; količina u litrima, iznosi u RSD |
| Gde se čuva | Nigde — računa se pri otvaranju |
| Kada se ponovo računa | Pri svakom otvaranju, sa tekućim stanjem transakcija |
| Može li korisnik da ga izmeni | Ne — ali može promeniti dodelu šifre posla, što menja rezultat |
| Istorija | Ne postoji |

### 10. Upotreba rezultata

| Korisnik | Šta preuzima | Sa kog ekrana | Za šta |
|---|---|---|---|
| Služba voznog parka | Zbir po šifri | `/izvestaji/gorivo-sifra-posla/*` | Kontrola raspodele |
| Računovodstvo | **[N]** | **[N]** | **[N] Q3** |

> **[N] Q3:** nije potvrđeno da li se ovaj izveštaj koristi kao osnov za knjiženje
> raspodele goriva po nosiocima. Konta nisu navedena jer nisu u kodu.

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Ukupan zbir | Zbir svih šifara = zbir bruto iznosa svih OMV/NIS transakcija u periodu za tu kategoriju vozila |
| Pojedinačna šifra | Otvoriti detalj šifre — spisak pojedinačnih transakcija mora se sabrati u zbirni red |
| „Bez sifre“ | Označava vozila bez ijedne dodele pre datuma točenja — proveriti u `/sifre-poslova/` |
| Neslaganje sa fakturom dobavljača | Izveštaj obuhvata samo **povezana** vozila i **jednu** kategoriju — zbir je uvek ≤ faktura |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Posledica |
|---|---|---|
| Transakcija bez prepoznatog vozila | **Ispada iz izveštaja** | Trošak nedostaje, bez upozorenja |
| Priključno vozilo | Nikad nije u izveštaju | Namerno |
| Vozilo bez ijedne dodele pre datuma | Grupa „Bez sifre“ | Vidljivo |
| Dodela unesena naknadno, sa ranijim datumom | **Menja ranije izveštaje** | Izveštaj nije zamrznut |
| Vozilo promenilo šifru usred meseca | Trošak se deli na dve šifre po datumu | Namerno i ispravno |
| AdBlue | **Ulazi** u izveštaj | Uvećava količinu i iznos |

> **Najveći rizik [Z]:** izveštaj se **uvek računa iz tekućeg stanja**. Naknadna izmena
> dodele šifre posla menja i već odštampane izveštaje za prošle mesece.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Koristi se istorijska dodela na datum točenja | Potvrđeno | `fuel_reports.py:55-64` | — |
| Priključna vozila su isključena | Potvrđeno | `fuel_reports.py:29-32` | — |
| Transakcije bez vozila ispadaju | Potvrđeno | `fuel_reports.py:101, 108` | — |
| Polovina meseca je granica 15. dana | Potvrđeno | `fuel_reports.py:48-50, 75-80` | — |
| OMV prolazi kroz prečišćavanje V-06 | Potvrđeno | `fuel_reports.py:100` | — |
| Izveštaj se koristi za knjiženje | **Nepotvrđeno** | — | **Q3** |
| Da li AdBlue treba da bude u izveštaju | **Nepotvrđeno** | — | **Q14** |

---

## V-23 — Obračun goriva na putnom nalogu vozila

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Obračun“ na putnom nalogu vozila |
| Tehnički naziv | `VehicleTravelOrderDetailView.get_context_data()` |
| Putanja | [`fleet/views/vehicle_travel_orders.py:289`](../../../fleet/views/vehicle_travel_orders.py#L289) |
| Adresa | `/garaza/putni-nalozi-vozila/<pk>/obracun/` |

### 2. Poslovna svrha

Za jedno zaduženje vozila prikazuje **koliko je goriva natočeno, koliko je pređeno
kilometara i kolika je potrošnja** — osnov za pravdanje zaduženja i za kontrolu vozača.

### 3. Korisnici rezultata

Garaža, služba voznog parka, sam zaposleni koji je zadužio vozilo.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Ko unosi |
|---|---|---|---|
| Datum otvaranja | Datum otvaranja naloga | `fleet_vehicletravelorder.created_at` | Zaposleni / garaža |
| Datum zatvaranja | Datum zatvaranja naloga | `fleet_vehicletravelorder.closed_at` | Garaža |
| Početna kilometraža | Početna kilometraža | `fleet_vehicletravelorder.start_mileage` | Zaposleni |
| Krajnja kilometraža | Krajnja kilometraža | `fleet_vehicletravelorder.end_mileage` | Zaposleni / garaža |
| Transakcije goriva | — | `fleet_transactionomv`, `fleet_transactionnis` | Automatski |

### 5. Poreklo podataka

```
 Zaduženje vozila (period: created_at → closed_at ili danas)
            │
            ├─► OMV transakcije u periodu  (bez AdBlue, prečišćene V-06)
            └─► NIS transakcije u periodu  (bez AdBlue)
                          │
                          ▼
              ukupno litara, ukupan iznos
                          │
         start_mileage, end_mileage ──► pređeni put
                          │
                          ▼
                   potrošnja l/100 km
```

### 6. Tačan postupak obračuna

**Korak 1 — period:**

> od = `created_at` (00:00:00) · do = `closed_at` ili **današnji dan** (23:59:59.999999)

Otvoren nalog se obračunava **do danas**. [P]

**Korak 2 — pronalaženje transakcija.** Vozilo se traži na **dva načina istovremeno** [P]:

> `vehicle = vozilo naloga` **ILI** `registarska oznaka = poslednja tablica vozila`

Poslednja tablica je iz `traffic_cards` sortirano `-issue_date, -id`. [P]

> **[P] Važno:** ovo je **jedini** obračun u sistemu koji hvata i transakcije koje
> **nisu povezane sa vozilom**, preko registarske oznake. Razlog je što nalog mora
> obuhvatiti i tek preuzete transakcije koje sinhronizacija još nije povezala. [Z]

**Korak 3 — filter goriva bez AdBlue:**
`filter_omv_travel_order_fuel_queryset()` i `filter_nis_travel_order_fuel_queryset()`. [P]

**Korak 4 — iznos po stavci** (razlikuje se od V-04!) [P]:

| Izvor | Količina | Iznos | Jedinična cena |
|---|---|---|---|
| OMV | `quantity` | **`gross_cc` ili, ako je prazan, `amount`** | `unit_price`, ili iznos / količina |
| NIS | `kolicina` | `total` | `cena`, ili iznos / količina |

> **[P] Odstupanje:** ovde se koristi **bruto** iznos, **bez** preračuna u neto,
> i `amount` služi kao rezerva za `gross_cc`. To je jedino mesto u sistemu sa tim pravilom.

**Korak 5 — zbirovi:**

> ukupno litara = Σ količina · ukupan iznos = Σ iznos

**Korak 6 — pređeni put:** samo ako su **obe** kilometraže unete:

> pređeni put = krajnja kilometraža − početna kilometraža

**Korak 7 — potrošnja:** samo ako je pređeni put > 0:

> **potrošnja (l/100 km) = ukupno litara / pređeni put × 100**

**NULL vrednosti [P]:**

| Situacija | Rezultat |
|---|---|
| Nedostaje početna ili krajnja kilometraža | Pređeni put i potrošnja su **prazni** |
| Pređeni put ≤ 0 | Potrošnja je **prazna** |
| Nema transakcija u periodu | Ukupno litara = 0, iznos = 0, potrošnja = 0 (ako je put > 0) |

**Zaokruživanje [P]:** funkcija **ne zaokružuje**; prikaz zaokružuje šablon.

**Priprema za štampu [P]:** redovi se dele na stranice od po 30; prva stranica se
dopunjava praznim redovima do 30, druga obuhvata redove 31–60.
**Transakcije preko 60 se ne štampaju.**

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/views/vehicle_travel_orders.py` |
| Klasa | `VehicleTravelOrderDetailView` (obračun), `VehicleTravelOrderFuelReportView` (štampa) |
| Redovi | `_row_from_omv()`, `_row_from_nis()` |
| Šablon | `fleet/vehicle_travel_order_fuel_report.html` |
| Dozvole | `vehicle_travel_order_detail`, `vehicle_travel_order_fuel_report` |

**Zatvaranje prethodnog naloga [P]:** pri otvaranju novog naloga za isto vozilo,
svi raniji otvoreni nalozi se **automatski zatvaraju** na datum novog naloga, a njihova
krajnja kilometraža se postavlja na **početnu kilometražu novog naloga**
(`VehicleTravelOrderCreateView.form_valid`).

### 8. Primer obračuna

> Ilustrativni primer.

| Podatak | Vrednost |
|---|---|
| Nalog otvoren | 01.03.2026. |
| Nalog zatvoren | 31.03.2026. |
| Početna kilometraža | 120.000 km |
| Krajnja kilometraža | 122.500 km |

Transakcije u periodu (bez AdBlue):

| Datum | Izvor | Količina | Iznos (bruto) |
|---|---|---|---|
| 05.03. | OMV | 40 l | 9.600,00 |
| 18.03. | NIS | 45 l | 10.800,00 |
| 27.03. | OMV | 38 l | 9.120,00 |

| Korak | Vrednost |
|---|---|
| Ukupno litara | 40 + 45 + 38 = **123 l** |
| Ukupan iznos | 9.600 + 10.800 + 9.120 = **29.520,00 RSD** |
| Pređeni put = 122.500 − 120.000 | **2.500 km** |
| Potrošnja = 123 / 2.500 × 100 | **4,92 l/100 km** |

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Gorivo, put i potrošnja za jedno zaduženje vozila |
| Format | Ekran i obrazac za štampu |
| Gde se čuva | **Nigde** — samo `start_mileage` i `end_mileage` su sačuvani |
| Kada se ponovo računa | Pri svakom otvaranju |
| Može li korisnik da ga izmeni | Posredno — izmenom kilometraže na nalogu |
| Ko može da potvrdi | Garaža, zatvaranjem naloga |
| Istorija | Ne postoji; izmena zatvorenog naloga dozvoljena je **samo superuseru** [P] |

### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Štampani obračun uz putni nalog | Prilog za pravdanje zaduženja |
| Kontrola vozača | Poređenje sa očekivanom potrošnjom vozila (V-01) |

> **[N] Q3:** nije potvrđeno da li se ovaj obračun prilaže uz neki knjigovodstveni dokument.

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Broj transakcija | Uporediti sa spiskom na ekranu „Fakture goriva“ za isto vozilo i period |
| Pređeni put | Uporediti sa očitanjima na ekranu kilometraže vozila (V-13) |
| Potrošnja | Uporediti sa V-01 za isto vozilo; velika razlika ukazuje na grešku unosa |
| Nedostaju transakcije | Proveriti da li je vozilu promenjena registarska oznaka u periodu |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Posledica |
|---|---|---|
| Nalog nije zatvoren | Period ide **do danas** | Rezultat se menja svakog dana |
| Vozilo je promenilo tablice u periodu | Hvata se **samo poslednja** tablica | **Transakcije sa stare tablice mogu nedostajati** |
| Ista tablica kod drugog vozila u istoriji | Moguće **preuzimanje tuđih transakcija** | Rizik |
| Više od 60 transakcija | Štampa se **samo prvih 60** | Tihi gubitak na papiru |
| AdBlue | Izuzet | Namerno |
| `gross_cc` prazan, `amount` popunjen | Koristi se `amount` | Odstupanje od V-04 |
| Preklapajuća zaduženja istog vozila | Ista transakcija ulazi u **oba** naloga | Dvostruko računanje |

> **Najveći rizik [Z]:** hvatanje po registarskoj oznaci. Ako je tablica nekada pripadala
> drugom vozilu, mogu se povući tuđe transakcije. Kontrolna tabla flote zato ima
> upozorenje „Više istovremenih zaduženja“.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Period je `created_at` → `closed_at` ili danas | Potvrđeno | `vehicle_travel_orders.py:293-294` | — |
| Transakcije se hvataju i po vozilu i po tablici | Potvrđeno | `…:311-316` | — |
| AdBlue je izuzet | Potvrđeno | `…:318-323`, `fuel.py:247-252` | — |
| Iznos je bruto, sa `amount` kao rezervom | Potvrđeno | `…:261` | — |
| Potrošnja = litri / put × 100 | Potvrđeno | `…:336` | — |
| Štampa najviše 60 transakcija | Potvrđeno | `…:341-348` | — |
| Zašto se hvata i po tablici | **Zaključeno** | Nije komentarisano | Potvrditi namenu |
| Da li je dvostruko računanje kod preklapanja prihvatljivo | **Nepotvrđeno** | — | **Q15** |

---

## Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q13** | U obračunu V-01 starija granica prozora se ne proverava na `mileage > 0`. Ako to točenje ima kilometražu 0, prikazana prosečna potrošnja je drastično premala, bez upozorenja. Da li je neko primetio takve vrednosti na detalju vozila? (Kod nije menjan — potrebna je odluka da li se ispravlja.) |
| **Q14** | Da li AdBlue treba da ulazi u izveštaj „Gorivo po šifri posla“ (V-21) i u prosečnu potrošnju (V-01, V-02)? Trenutno ulazi u sve osim u obračun putnog naloga. |
| **Q15** | Kod preklapajućih zaduženja istog vozila ista transakcija goriva ulazi u obračun oba naloga. Da li je to prihvatljivo? |
| **Q16** | Da li su sve stavke goriva po stopi PDV-a od 20%? Preračun neto iznosa iz bruto (kada PDV nije poznat) pretpostavlja upravo tu stopu. |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.3. Flota — troškovi](06-03-flota-troskovi.md) | Trošak po kilometru, pragovi, crvena zona |
| [6.5. Flota — izveštaji](06-05-flota-izvestaji.md) | Kilometraža, održavanje, presek flote |
| [4. Baza podataka](../04-baza-podataka.md#444-gorivo) | Tabele goriva |
| [7. Integracije](../07-integracije.md) | Kako se preuzimaju NIS i OMV podaci |
