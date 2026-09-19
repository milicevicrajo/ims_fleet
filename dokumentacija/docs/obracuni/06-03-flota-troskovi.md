# 6.3. Flota — troškovi vozila

> **Promena 19.09.2026:** nova `/analitika/` i analitika na detalju vozila koriste
> [metodologiju IMS-FLOTA-2.0](06-12-flota-ekonomika.md). Opisi V-07–V-12 u ovom
> poglavlju dokumentuju nasleđene funkcije; pragovi po masi više nisu kriterijum
> nove analitike. Detalj vozila zadržava pregled evidentiranih stavki, uz zajednički
> prošireni obračun, profile i sačuvane procene opisane u novom poglavlju.

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
>
> Uočeni problemi u ovom poglavlju vode se u
> [Registru problema za rešavanje](../10-poznati-problemi.md).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [V-08](#v-08--procena-pređene-kilometraže-u-periodu) | Procena pređene kilometraže u periodu | **P-03**, ~~P-04~~ |
| [V-07](#v-07--trošak-po-kilometru-po-vozilu) | Trošak po kilometru po vozilu | ~~P-05~~ ~~P-06~~ ~~P-07~~ **P-08** ~~P-09~~ ~~P-10~~ |
| [V-11](#v-11--pragovi-fiksnog-troška-po-kilometru) | Pragovi fiksnog troška po kilometru | P-11 |
| [V-12](#v-12--status-vozila-prema-trošku-po-kilometru) | Status vozila prema trošku po kilometru | — |
| [V-09](#v-09--analiza-troška-po-km-kroz-više-perioda) | Analiza troška po km kroz više perioda | P-12 |
| [V-10](#v-10--neto-trošak-održavanja) | Neto trošak održavanja | — |
| [V-15](#v-15--analitika-evidentiranih-troškova-na-detalju-vozila) | Analitika evidentiranih troškova na detalju vozila | — |
| [V-24](#v-24--statistika-po-centrima) | Statistika po centrima | P-13, P-14 |

---

## V-08 — Procena pređene kilometraže u periodu

> Ovaj obračun je **imenilac** troška po kilometru. Ako je on pogrešan, pogrešan je
> i ceo trošak po km. Zato se dokumentuje prvi.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kilometraža“ uz oznaku izvora, npr. „Točenja (okvirno)“ |
| Tehnički naziv | `_estimate_period_mileage()` |
| Putanja | [`fleet/support/dashboard.py:68`](../../../fleet/support/dashboard.py#L68) |

### 2. Poslovna svrha

Sistem **nema pouzdan podatak o pređenoj kilometraži po periodu** — brojač se očitava
samo prilikom točenja goriva i pri otvaranju/zatvaranju zaduženja vozila. Ovaj obračun
iz tih raštrkanih očitavanja pravi **procenu** kilometraže za traženi period.

### 3. Korisnici rezultata

Služba voznog parka, rukovodioci centara, uprava — posredno, kroz trošak po kilometru.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | JM | Obavezno | Ko unosi |
|---|---|---|---|---|---|---|
| Datum točenja | — | `fleet_fuelconsumption.date` | datum i vreme | — | Da | Automatski |
| Kilometraža na točenju | Kilometraža | `fleet_fuelconsumption.mileage` | ceo broj | km | Ne | Vozač na pumpi |
| Datum otvaranja zaduženja | Datum otvaranja naloga | `fleet_vehicletravelorder.created_at` | datum | — | Da | Zaposleni |
| Datum zatvaranja zaduženja | Datum zatvaranja naloga | `fleet_vehicletravelorder.closed_at` | datum | — | Ne | Garaža |
| Početna kilometraža | Početna kilometraža | `fleet_vehicletravelorder.start_mileage` | ceo broj | km | Ne | Zaposleni |
| Krajnja kilometraža | Krajnja kilometraža | `fleet_vehicletravelorder.end_mileage` | ceo broj | km | Ne | Zaposleni / garaža |
| Početak perioda | Od | parametar ekrana | datum | — | Da | Korisnik |
| Kraj perioda | Do | parametar ekrana | datum | — | Ne (podrazumevano danas) | Korisnik |

### 5. Poreklo podataka

```
 OMV/NIS portal ──► fleet_fuelconsumption (date, mileage)   ─┐
                                                             │
 Zaposleni ──► fleet_vehicletravelorder                       ├─► spisak očitavanja
              (created_at + start_mileage)                    │
              (closed_at  + end_mileage)                     ─┘
                                                             │
                                              izbor najboljeg para očitavanja
                                                             │
                                                             ▼
                                              procena kilometraže za period
```

### 6. Tačan postupak obračuna

**Korak 1 — prikupljanje očitavanja** (`_mileage_readings`) [P]:

| Izvor | Datum | Vrednost | Uslov |
|---|---|---|---|
| Točenje goriva | `date` | `mileage` | `mileage > 0` |
| Zaduženje — početak | `created_at` | `start_mileage` | `start_mileage > 0` |
| Zaduženje — kraj | `closed_at` | `end_mileage` | `end_mileage > 0` |

Očitavanja sa vrednošću **0 ili manjom se odbacuju** i broje kao neispravna. [P]
Spisak se sortira po datumu, pa po kilometraži, rastuće. [P]

**Korak 2 — provera dovoljnosti:**
Ako ima **manje od 2** očitavanja → rezultat je:

| Polje | Vrednost |
|---|---|
| `km` | **0** |
| `source` | „Nema podatka“ |
| `requires_driver_warning` | **Da** |

**Korak 3 — izbor najboljeg para** [P]:

Prolazi se kroz **sve moguće parove** očitavanja (svako sa svakim). Par je upotrebljiv
samo ako:

> broj dana između očitavanja **> 0**  **i**  razlika kilometraže **> 0**

Za svaki upotrebljiv par računa se **ocena udaljenosti od traženog perioda**:

> ocena = |datum početnog očitavanja − početak perioda| + |datum krajnjeg očitavanja − kraj perioda|

Bira se par sa **najmanjom ocenom** — dakle par čiji su datumi najbliži granicama perioda.

**Korak 4 — preračun na dužinu perioda:**

> **procenjena kilometraža = (razlika kilometraže / broj dana između očitavanja) × broj dana perioda**

gde je `broj dana perioda = max((kraj − početak).days, 1)`. [P]

**Korak 5 — oznaka izvora** [P]:

| Oba očitavanja iz | Oznaka |
|---|---|
| Točenja | „Točenja (okvirno)“ |
| Zaduženja | „Zaduženja (okvirno)“ |
| Mešovito | „Točenja/zaduženja (okvirno)“ |

**Zaokruživanje [P]:** nema — vraća se decimalan rezultat deljenja.

**NULL vrednosti [P]:** očitavanje bez datuma se odbacuje; očitavanje bez kilometraže
ili sa nulom se odbacuje i broji u `invalid_fuel_count`, o čemu se korisnik obaveštava
tekstom *„Točenja sa kilometražom 0 su ignorisana.“*

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/dashboard.py` |
| Funkcije | `_mileage_readings()`, `_estimate_period_mileage()`, `_valid_number()` |
| Poziva je | `vehicle_cost_per_km_rows()` (V-07) |
| Ekrani | Kontrolna tabla, analitika flote, statistika centra |
| Testovi | `fleet/test_vehicle_mileage.py` (11 testova — za srodni prikaz V-13) |

### 8. Primer obračuna

> Ilustrativni primer. Traženi period: **01.03.2026. – 31.03.2026.** (30 dana).

Dostupna očitavanja:

| Datum | Kilometraža | Izvor |
|---|---|---|
| 25.02.2026. | 120.000 | Točenje |
| 10.03.2026. | 121.200 | Točenje |
| 02.04.2026. | 122.700 | Točenje |

Ocene parova (bira se najmanja):

| Par | Razlika km | Dana | Ocena | |
|---|---|---|---|---|
| 25.02. → 02.04. | 2.700 | 36 | \|25.02.−01.03.\| + \|02.04.−31.03.\| = 4 + 2 = **6** | **izabran** |
| 25.02. → 10.03. | 1.200 | 13 | 4 + 21 = 25 | |
| 10.03. → 02.04. | 1.500 | 23 | 9 + 2 = 11 | |

| Korak | Vrednost |
|---|---|
| Razlika kilometraže | 2.700 km |
| Broj dana između očitavanja | 36 |
| Dnevni prosek = 2.700 / 36 | 75 km/dan |
| Dana u periodu | 30 |
| **Procena = 75 × 30** | **2.250 km** |
| Izvor | „Točenja (okvirno)“ |

> Uočite: **nijedno od dva izabrana očitavanja nije unutar traženog perioda.**
> To je dozvoljeno i namerno — vidi problem **P-03**.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | **Procenu**, ne izmerenu kilometražu |
| Format | Decimalan broj, km |
| Gde se čuva | Nigde — računa se pri prikazu |
| Kada se ponovo računa | Pri svakom otvaranju ekrana |
| Može li korisnik da ga izmeni | Posredno — unosom kilometraže na zaduženju |
| Istorija | Ne postoji |

Uz rezultat se uvek vraća i **objašnjenje** (`issue`) sa datumima i brojem dana
korišćenih očitavanja, koje se prikazuje korisniku. [P]

### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Trošak po kilometru (V-07) | **Imenilac** — deli se ukupan trošak |
| Analiza kroz više perioda (V-09) | Posredno, kroz V-07 |
| Kontrolna tabla i analitika flote | Prikaz kolone „Kilometraža“ sa oznakom izvora |

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Da li je procena razumna | Uporediti sa ekranom kilometraže vozila (V-13), gde se vide stvarna očitavanja u intervalima od ~30 dana |
| Iz kojih očitavanja je izvedena | Tekst objašnjenja navodi oba datuma i broj dana |
| Da li su očitavanja unutar perioda | **Proveriti ručno** — sistem to ne garantuje |
| Nema procene | Vozilo ima manje od dva ispravna očitavanja — proveriti da li vozači unose kilometražu |

**Kontrolna formula:**

> procena = (km₂ − km₁) / (dan₂ − dan₁) × dana u periodu

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Ozbiljnost |
|---|---|---|
| Manje od 2 ispravna očitavanja | `km = 0`, upozorenje „Nema podatka“ | Vidljivo |
| **Sva očitavanja izvan perioda** | **Procena se ipak pravi** | **P-03** |
| **Očitavanja veoma udaljena od perioda** | Procena se pravi bez ograničenja udaljenosti | **P-03** |
| Kilometraža opada (zamena brojača) | Takav par se odbacuje (razlika ≤ 0); koristi se drugi par | Ispravno |
| Sva očitavanja istog dana | Nijedan par nema dana > 0 → „Nema podatka“ | Ispravno |
| Očitavanje sa kilometražom 0 | Odbacuje se, korisnik se obaveštava | Ispravno |
| Složenost izbora para | **Linearno-logaritamska** (`_best_reading_pair`) | Rešeno 19.09.2026., **P-04** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Očitavanja iz točenja i zaduženja | Potvrđeno | `dashboard.py:38-65` | — |
| Vrednosti ≤ 0 se odbacuju | Potvrđeno | `dashboard.py:30-36` | — |
| Bira se par najbliži granicama perioda | Potvrđeno | `dashboard.py:89-101` | — |
| Preračun dnevni prosek × dana perioda | Potvrđeno | `dashboard.py:107` | — |
| **Par nije ograničen na period** | **Potvrđeno — problem** | `dashboard.py` — `_best_reading_pair()` | **P-03** |
| Izbor para daje isti rezultat kao ranija petlja | Potvrđeno | `fleet/test_cost_fixes.py` — poređenje sa starom petljom | Rešeno, **P-04** |
| Rezultat je procena, ne merenje | Potvrđeno | Oznaka „okvirno“ u izvoru | — |

---

## V-07 — Trošak po kilometru po vozilu

> **Najsloženiji obračun u modulu Flota.** Objedinjuje šest vrsta troška i deli ih
> procenjenom kilometražom.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Trošak po km“ / „Cena po kilometru“ |
| Tehnički naziv | `vehicle_cost_per_km_rows()` |
| Putanja | [`fleet/support/dashboard.py:135`](../../../fleet/support/dashboard.py#L135) |
| Ekrani | `/analitika/` (Analitika flote), `/` (Kontrolna tabla), `/center_statistics/<centar>/` |

### 2. Poslovna svrha

Pokazuje **koliko stvarno košta jedan pređeni kilometar** svakog vozila, radi:

- poređenja vozila međusobno i sa pragovima po klasi mase;
- prepoznavanja vozila koja više ne isplati zadržavati;
- odluke o zameni, prodaji ili otpisu vozila.

### 3. Korisnici rezultata

Uprava, rukovodioci centara, služba voznog parka.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | JM | Napomena |
|---|---|---|---|
| Trošak goriva | `fleet_fuelconsumption.cost_bruto` | RSD | **Bruto, sa PDV-om** |
| Količina goriva | `fleet_fuelconsumption.amount` | litar | Samo za prikaz |
| Trošak servisa | `fleet_servicetransaction.potrazuje` | RSD | |
| Trošak trebovanja | `fleet_requisition.vrednost_nab` | RSD | |
| Naknada osiguranja | `fleet_insurance.potrazuje` (uz `kola = True`) | RSD | **Odbija se** |
| Premija polise | `fleet_policy.premium_amount` | RSD | |
| Kamata finansijskog lizinga | `fleet_leaseinterest.interest_amount` | RSD | |
| Rata operativnog/dugoročnog | `fleet_lease.current_payment_amount` | RSD | |
| Nabavna vrednost | `fleet_vehicle.purchase_value` | RSD | Za amortizaciju |
| Knjigovodstvena vrednost | `fleet_vehicle.value` | RSD | Za amortizaciju |
| Datum nabavke | `fleet_vehicle.purchase_date` | — | Osnov amortizacije |
| Datum prve registracije | `fleet_vehicle.first_registration_date` | — | Rezerva za osnov |
| Maks. dozvoljena masa | `fleet_vehicle.maximum_permissible_weight` | kg | Za prag (V-11) |
| Procenjena kilometraža | izračunato — **V-08** | km | **Imenilac** |

### 5. Poreklo podataka

```
 fleet_fuelconsumption.cost_bruto        ──┐
 fleet_servicetransaction.potrazuje      ──┤
 fleet_requisition.vrednost_nab          ──┤
 fleet_policy.premium_amount             ──┼──►  UKUPAN TROŠAK
 amortizacija (izračunata)               ──┤
 lizing / najam (izračunat)              ──┤
 fleet_insurance.potrazuje  (oduzima se) ──┘
                                              │
 V-08 procena kilometraže ────────────────────┤
                                              ▼
                                    TROŠAK PO KILOMETRU
                                              │
                              V-11 prag po masi vozila
                                              ▼
                                   V-12 status vozila
```

### 6. Tačan postupak obračuna

#### Korak 1 — koja vozila ulaze [P]

| Uslov | Vrednost |
|---|---|
| `otpis` | `False` — otpisana vozila se ne prikazuju |
| `category` | **`putnicko` ili `teretno`** — priključna vozila su isključena |

#### Korak 2 — troškovi u periodu

| Trošak | Filter perioda | Napomena |
|---|---|---|
| Gorivo | `date >= početak 00:00` i `date < kraj+1 dan 00:00` | Zbir `cost_bruto` |
| Servisi | `datum` između početka i kraja (uključivo) | Zbir `potrazuje` |
| Trebovanja | `datum_trebovanja` između početka i kraja | Zbir `vrednost_nab` |
| Naknada osiguranja | `datum` između početka i kraja, `kola = True` | Zbir `potrazuje` |
| **Polise** | `start_date <= kraj perioda` **i** `end_date >= početak perioda` | **Zbir cele premije** |
| **Kamata fin. lizinga** | `lease_type = finansijski`, `lease.end_date >= početak`, `year` u opsegu godina perioda | **Zbir cele godišnje kamate** |

> **[P] Dva troška se NE dele srazmerno periodu:** premija polise i kamata finansijskog
> lizinga ulaze **u punom iznosu** čim se period bilo kako preklopi sa njihovim važenjem.
> **Ispravljeno 19.09.2026.** — vidi **P-06** i **P-07**. Premija polise i godišnja kamata
> lizinga sada ulaze **srazmerno danima**, a ne u punom iznosu.

#### Korak 3 — lizing i najam (osim finansijskog)

Uzimaju se ugovori koji se **preklapaju** sa periodom
(`start_date <= kraj` i `end_date >= početak`), isključujući `finansijski`. [P]

**Preklapanje:**

> početak preklapanja = max(početak ugovora, početak perioda)
> kraj preklapanja = min(kraj ugovora, kraj perioda)

**A) Dugoročni najam** (`dugorocni`, `dugoročni`, `dugoročnI`) [P]:

`current_payment_amount` se tretira kao **mesečna rata** i deli po danima svakog meseca:

> za svaki mesec u preklapanju:
> deo = mesečna rata × (broj dana u tom mesecu unutar preklapanja) / (broj dana tog meseca)

Zbir svih delova je trošak najma. Kraj preklapanja se pomera za jedan dan da bi bio
isključiv. [P]

**B) Operativni lizing** [P]:

> trošak = `current_payment_amount` × (dana preklapanja) / (ukupno dana trajanja ugovora)

> **[P] Različita pravila:** kod dugoročnog najma iznos je **mesečna rata**, a kod
> operativnog lizinga se **ista kolona** razmazuje preko **celog trajanja ugovora**.
> Vidi problem **P-08**.

**C) Finansijski lizing** [P]: ne ulazi ovde — ulazi kroz kamatu (korak 2),
jer je glavnica već sadržana u amortizaciji.

#### Korak 4 — amortizacija

Računa se **samo** ako su popunjeni `purchase_value`, `value` i osnovni datum. [P]

> osnovni datum = `purchase_date`, a ako je prazan → `first_registration_date`
> dana u upotrebi = **max((kraj perioda − osnovni datum).days, 365)**
> ukupna amortizacija = **max(nabavna vrednost − knjigovodstvena vrednost, 0)**
> **amortizacija za period = ukupna amortizacija / dana u upotrebi × dana perioda**

> **[P]** `max(..., 365)` znači da se za vozilo mlađe od godinu dana amortizacija
> **razmazuje kao da je staro godinu dana** — inače bi bila nerealno velika.

#### Korak 5 — ukupan trošak

> **ukupan trošak = gorivo + servisi + trebovanja + polise + amortizacija + lizing − naknada osiguranja**

#### Korak 6 — isključivanje vozila

> **Ako je ukupan trošak ≤ 0, vozilo se potpuno izostavlja iz rezultata.** [P]

> **Ispravljeno 19.09.2026.** — vozilo bez troška **ostaje** na spisku, sa oznakom
> „Nema evidentiranog troška u periodu“ ili „Naknade osiguranja su veće od evidentiranih
> troškova u periodu“. Cena po km ostaje nepoznata, pa vozilo ne ulazi u proseke, pragove
> ni u crvenu zonu. Vidi **P-09**.

#### Korak 7 — trošak po kilometru

> **trošak po km = ukupan trošak / procenjena kilometraža**  (ako je kilometraža > 0)
> inače: **prazno** (`None`)

#### Korak 8 — napomena o maloj kilometraži

Kilometraža perioda se **svodi na godišnji nivo** (`km × 365 / dana perioda`) i tek se
ta vrednost poredi sa pragom. Ako je **> 0 i < 15.000**, uz red se prikazuje napomena:

> *„Vozilo se malo vozi (… km < 15000 km godišnje). Cena po km može biti iskrivljena
> jer se fiksni troškovi (osiguranje, doprinosi) raspoređuju na manju kilometražu.“*

U poruci stoji **preračunata godišnja** kilometraža, ista ona koja je poređena sa pragom.
Dostupna je i u redu tabele kao `annualized_km`. [P]

> **Ispravljeno 18.09.2026.** — ranije se sa godišnjim pragom poredila kilometraža
> **perioda**, pa je za jednomesečni pregled napomenu dobijalo gotovo svako vozilo.
> Videti [P-10](../10-poznati-problemi.md).

#### Korak 9 — sortiranje

Opadajuće po trošku po kilometru; prazne vrednosti se tretiraju kao 0. [P]

#### Zaokruživanje i NULL [P]

| Pravilo | Vrednost |
|---|---|
| Zaokruživanje | **Nema** — svi iznosi su `float`, zaokružuje šablon |
| Prazan iznos troška | Tretira se kao **0** (`number()` funkcija) |
| Prazna kilometraža | Trošak po km je **prazan**, ne 0 |
| Prazna masa vozila | Nema praga → status „Nema praga“ (V-12) |

> **[P] Napomena o tipovima:** obračun radi sa `float`, ne `Decimal`. Za poređenje
> vozila je to dovoljno, ali zbir nije knjigovodstveno tačan na paru.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/dashboard.py` |
| Glavna funkcija | `vehicle_cost_per_km_rows(period_start_date, period_end_date, limit, vehicle_ids)` |
| Pomoćna | `monthly_cost_for_overlap()` (unutar funkcije) |
| Kilometraža | `_estimate_period_mileage()` — V-08 |
| Pragovi | `fleet/support/analytics.py` — V-11, V-12 |
| Ekrani | `fleet/views/analytics.py: fleet_analytics`, `fleet/views/dashboard.py`, `fleet/views/center_statistics.py` |

**Centar vozila [P]:** uzima se **poslednja** dodela (`-assigned_date`), **bez
ograničenja na period**. Razlikuje se od izveštaja goriva po šifri posla (V-21),
koji koristi **istorijsku** dodelu na datum troška.

> **Ispravljeno 19.09.2026.:** V-07 sada uzima dodelu koja je važila **na kraju izabranog
> perioda**, pa se izveštaji za prošle periode više ne menjaju kad se vozilo kasnije
> prebaci. Vozilo koje je centar promenilo **usred** perioda i dalje nosi ceo trošak u
> centar sa kraja perioda, ali red nosi oznaku `center_changed_in_period`. Vidi **P-05**.

### 8. Primer obračuna

> Ilustrativni primer. Putničko vozilo, period **01.01.2026. – 31.03.2026.** (89 dana).

**Ulazni podaci:**

| Stavka | Vrednost |
|---|---|
| Gorivo (bruto) u periodu | 180.000,00 RSD |
| Servisi u periodu | 45.000,00 RSD |
| Trebovanja u periodu | 12.000,00 RSD |
| Naknada osiguranja u periodu | 30.000,00 RSD |
| Polisa: 01.07.2025.–30.06.2026., premija | 60.000,00 RSD |
| Nabavna vrednost | 2.400.000,00 RSD |
| Knjigovodstvena vrednost | 1.200.000,00 RSD |
| Datum nabavke | 01.01.2021. |
| Lizing | nema |
| Procenjena kilometraža (V-08) | 6.000 km |
| Maks. dozvoljena masa | 2.000 kg |

**Obračun:**

| Korak | Račun | Vrednost |
|---|---|---|
| Gorivo | | 180.000,00 |
| Servisi | | 45.000,00 |
| Trebovanja | | 12.000,00 |
| **Polisa** | preklapa se sa periodom → **cela premija** | 60.000,00 |
| Amortizacija — dana u upotrebi | (31.03.2026. − 01.01.2021.) = 1.915 dana | 1.915 |
| Amortizacija — ukupna | 2.400.000 − 1.200.000 | 1.200.000,00 |
| Amortizacija — za period | 1.200.000 / 1.915 × 89 | 55.770,23 |
| Lizing | | 0,00 |
| Naknada osiguranja | oduzima se | −30.000,00 |
| **Ukupan trošak** | 180.000 + 45.000 + 12.000 + 60.000 + 55.770,23 + 0 − 30.000 | **322.770,23 RSD** |
| **Trošak po km** | 322.770,23 / 6.000 | **53,80 RSD/km** |
| Prag za masu 2.000 kg | Putnička do 3,5 t: dobro ≤ 25, praćenje ≤ 40, rizično ≤ 60 | |
| **Status** | 53,80 je između 40 i 60 | **„Rizično“** |
| Napomena | 6.000 km < 15.000 km | Prikazuje se upozorenje o maloj kilometraži |

> Uočite: cela godišnja premija polise (60.000,00) ušla je u tromesečni period.
> Srazmerno (89 od 365 dana) bilo bi **14.630,14 RSD** — razlika je **+310%**.
> **Ispravljeno 19.09.2026.** — vidi **P-06**.
>
> Da je premija ušla srazmerno, ukupan trošak bio bi 277.400,37 RSD, a trošak po
> kilometru **46,23 RSD/km** umesto 53,80 — i status bi bio **„Rizično“** u oba slučaja,
> ali kod vozila blizu granice ovakva razlika menja ocenu.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Procenu troška po pređenom kilometru u periodu |
| Format | Decimalan broj, RSD/km |
| Gde se čuva | **Nigde** — računa se pri svakom otvaranju |
| Kada se ponovo računa | Pri svakom otvaranju ekrana |
| Može li korisnik da ga izmeni | Ne |
| Ko može da ga potvrdi | Nema postupka potvrde |
| Istorija promene | **Ne postoji** |
| Audit trag | Ne postoji za sam rezultat; otvaranje ekrana se beleži u `ActivityLog` |

### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Analitika flote | Tabela vozila sa statusom i pragom |
| Kontrolna tabla | Najskuplja vozila |
| Statistika centra | Vozila centra |
| Analiza kroz više perioda (V-09) | Trajno neisplativa vozila |
| Odluka uprave | Zamena, prodaja ili otpis vozila |

> **[N] Q3:** rezultat se **ne knjiži** i ne prenosi u druge module. Služi kao
> podloga za odluku. Nije potvrđeno da li se prilaže uz neki dokument.

### 11. Kontrola i ručna provera

**Kontrolna formula:**

> (gorivo + servisi + trebovanja + polise + amortizacija + lizing − naknade) / kilometraža

| Provera | Kako |
|---|---|
| Gorivo | Uporediti sa ekranom „Fakture goriva“ za isto vozilo i period (**pažnja:** ovde je bruto) |
| Servisi | `/service-transactions/` filtrirano po vozilu i periodu |
| Trebovanja | `/requisitions/` filtrirano po vozilu |
| Polise | `/polise/` — proveriti da li polisa pokriva ceo period ili samo deo |
| Amortizacija | Ručno: (nabavna − knjigovodstvena) / dana u upotrebi × dana perioda |
| Kilometraža | Objašnjenje uz red navodi datume korišćenih očitavanja |

**Tipični uzroci razlike:**

| Uzrok | Objašnjenje |
|---|---|
| Trošak manji nego ranije za kratke periode | Polisa i kamata se od 19.09.2026. dele po danima (~~P-06~~, ~~P-07~~) |
| Trošak po km neuobičajeno visok | Procena kilometraže premala (**P-03**) |
| Vozilo bez cene po km | Ukupan trošak ≤ 0; red ostaje, uz objašnjenje (~~P-09~~) |
| Vozilo u pogrešnom centru | Uzima se dodela sa **kraja perioda**; promena usred perioda je označena (~~P-05~~) |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Otpisano vozilo | Izostavljeno | Namerno |
| Priključno vozilo | Izostavljeno | Namerno |
| Ukupan trošak = 0 | Red ostaje; RSD/km je crtica, uz „Nema evidentiranog troška u periodu“ | Ispravljeno, **P-09** |
| Ukupan trošak < 0 | Red ostaje; „Naknade osiguranja su veće od evidentiranih troškova u periodu“ | Ispravljeno, **P-09** |
| Kilometraža = 0 | Trošak po km prazan; vozilo **ostaje** u spisku | Vidljivo |
| Nema nabavne ili knjigovodstvene vrednosti | Amortizacija = 0, bez upozorenja | **P-09** |
| Knjigovodstvena vrednost veća od nabavne | Amortizacija = 0 (`max(..., 0)`) | Ispravno |
| Vozilo mlađe od godinu dana | Amortizacija razmazana na 365 dana | Namerno |
| Polisa važi jedan dan u periodu | Ulazi **jedan dan** premije | Ispravljeno, **P-06** |
| Polisa bez datuma početka ili kraja | **Ne ulazi** u trošak | Ispravljeno, **P-06** |
| Finansijski lizing, period od mesec dana | Ulazi **srazmeran deo** godišnje kamate | Ispravljeno, **P-07** |
| Prestupna godina | Imenilac kamate je **366 dana** | Ispravljeno, **P-07** |
| Vozilo promenilo centar u periodu | Trošak ide na centar sa **kraja perioda**, red je označen | Delimično, **P-05** |
| Period kraći od godinu dana | Kilometraža se **svodi na godišnji nivo** pre poređenja sa pragom od 15.000 km | Ispravljeno, **P-10** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje / problem |
|---|---|---|---|
| Ulaze samo neotpisana putnička i teretna vozila | Potvrđeno | `dashboard.py:150-153` | — |
| Gorivo se uzima kao **bruto** (`cost_bruto`) | Potvrđeno | `dashboard.py:166` | Potvrditi da je bruto željen |
| Formula ukupnog troška | Potvrđeno | `dashboard.py:314-322` | — |
| Amortizacija po danima, najmanje 365 | Potvrđeno | `dashboard.py:307-312` | — |
| Dugoročni najam se deli po mesecima | Potvrđeno | `dashboard.py:274-278` | — |
| Operativni lizing se deli preko celog ugovora | Potvrđeno | `dashboard.py:280-285` | **P-08** |
| Polisa ulazi srazmerno danima preklapanja | Potvrđeno | `dashboard.py` — `policy_cost_by_vehicle` | Rešeno, **P-06** |
| Kamata ulazi srazmerno danima u godini | Potvrđeno | `dashboard.py` — `financial_interest_by_vehicle` | Rešeno, **P-07** |
| Vozila sa troškom ≤ 0 ostaju na spisku | Potvrđeno | `dashboard.py` — `has_cost`, `no_cost_note` | Rešeno, **P-09** |
| Kilometraža se svodi na godišnji nivo pre poređenja sa pragom | Potvrđeno | `dashboard.py:331-333` | Rešeno, **P-10** |
| Centar je onaj sa **kraja perioda** | Potvrđeno | `dashboard.py` — `center_at_period_end` | Rešeno, **P-05** |
| Promena centra unutar perioda je označena | Potvrđeno | `dashboard.py` — `center_changed_in_period` | Rešeno, **P-05** |
| Da li je bruto gorivo ispravan izbor | **Nepotvrđeno** | — | **Q17** |

---

## V-11 — Pragovi fiksnog troška po kilometru

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Prag“, „Klasa vozila“ |
| Tehnički naziv | `fixed_cost_per_km_threshold()`, `fixed_cost_per_km_ranges()` |
| Putanja | [`fleet/support/analytics.py:14`](../../../fleet/support/analytics.py#L14) |

### 2. Poslovna svrha

Trošak po kilometru nije uporediv između putničkog automobila i kamiona. Pragovi
definišu **šta je prihvatljivo za koju klasu vozila**, prema maksimalnoj dozvoljenoj masi.

### 3. Korisnici rezultata

Uprava, rukovodioci centara, služba voznog parka.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | JM |
|---|---|---|---|
| Maksimalna dozvoljena masa | Maksimalna dozvoljena masa (kg) | `fleet_vehicle.maximum_permissible_weight` | kg |

### 5. Poreklo podataka

Ručni unos u obrascu vozila, sa saobraćajne dozvole. **Nema sinhronizacije** — ako
podatak nije unet, prag se ne može odrediti. [P]

### 6. Tačan postupak obračuna

**Pragovi su fiksni i upisani u kod** (`_WEIGHT_CLASS_THRESHOLDS`). Nisu u bazi i ne
mogu se menjati kroz interfejs. [P]

| Klasa vozila | Masa (kg) | Dobro ≤ | Za praćenje ≤ | Rizično ≤ | Iznad = |
|---|---|---|---|---|---|
| Putnička vozila (do 3.5t) | do 3.500 | **25** | **40** | **60** | Neisplativo |
| Laka teretna (3.5t – 7.5t) | 3.501 – 7.500 | **45** | **70** | **100** | Neisplativo |
| Srednja teretna (7.5t – 12t) | 7.501 – 12.000 | **70** | **110** | **140** | Neisplativo |
| Teška teretna (preko 12t) | preko 12.000 | **120** | **150** | **175** | Neisplativo |

*(svi pragovi u RSD po kilometru)*

**Postupak izbora:**

1. Ako je masa **prazna ili ≤ 0** → **nema praga** (`None`). [P]
2. Inače se uzima **prva klasa** čija gornja granica nije manja od mase vozila.

> **[P] Mrtav kod:** funkcija ima i rezervnu vrednost „Nepoznato“ (60/100/150), ali je
> **nedostižna**, jer poslednja klasa ima gornju granicu `beskonačno`.

**Grupna statistika** (`cost_per_km_thresholds`) [P]: za prikaz u tabeli, vozila se
grupišu po klasi mase i računa se **prosek troška po km** te klase i broj vozila.
Vozila bez praga se **izostavljaju** iz grupne statistike.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/analytics.py` |
| Konstanta | `_WEIGHT_CLASS_THRESHOLDS` (linija 14) |
| Funkcije | `fixed_cost_per_km_ranges()`, `fixed_cost_per_km_threshold()`, `cost_per_km_thresholds()` |

### 8. Primer

| Vozilo | Masa | Klasa | Dobro | Praćenje | Rizično |
|---|---|---|---|---|---|
| Putnički automobil | 1.800 kg | Putnička do 3,5 t | ≤ 25 | ≤ 40 | ≤ 60 |
| Kombi | 3.500 kg | **Putnička do 3,5 t** | ≤ 25 | ≤ 40 | ≤ 60 |
| Kombi | 3.501 kg | Laka teretna | ≤ 45 | ≤ 70 | ≤ 100 |
| Kamion | 18.000 kg | Teška teretna | ≤ 120 | ≤ 150 | ≤ 175 |
| Vozilo bez unete mase | — | **Nema praga** | — | — | — |

> Granica 3.500 kg pripada **putničkoj** klasi (uslov je `masa <= 3500`). [P]

### 9–10. Rezultat i upotreba

Prag nije samostalan rezultat — koristi ga isključivo V-12 za određivanje statusa vozila
i tabela grupne statistike po klasama.

### 11. Kontrola i ručna provera

Uporediti masu vozila sa saobraćajnom dozvolom. Ako vozilo ima status „Nema praga“,
proveriti polje „Maksimalna dozvoljena masa“ u obrascu vozila.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Masa nije uneta | **Nema praga** — vozilo bez ocene | **P-11** |
| Masa je 0 | Isto kao da nije uneta | **P-11** |
| **Pragovi zastareli** | Nema mehanizma za izmenu bez izmene koda | **P-11** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Četiri klase i njihove granice | Potvrđeno | `analytics.py:14-19` | — |
| Vrednosti pragova u RSD/km | Potvrđeno | Komentar u kodu | — |
| Bez mase nema praga | Potvrđeno | `analytics.py:41-42` | — |
| **Poreklo i osnov pragova** | **Nepotvrđeno** | Nema izvora u kodu | **Q18** |
| Da li su pragovi još važeći | **Nepotvrđeno** | — | **Q18** |

---

## V-12 — Status vozila prema trošku po kilometru

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Status“ — „Dobro“, „Za praćenje“, „Rizično“, „Neisplativo“, „Opomena“, „Nema praga“ |
| Tehnički naziv | `cost_per_km_status()`, `is_red_zone()` |
| Putanja | [`fleet/support/analytics.py:79`](../../../fleet/support/analytics.py#L79) |

### 2. Poslovna svrha

Pretvara broj (RSD/km) u **jasnu ocenu** koju netehnički korisnik odmah razume.

### 6. Tačan postupak obračuna

#### A) Status prema trošku po kilometru [P]

| Uslov | Status |
|---|---|
| Trošak po km je **prazan** | **„Opomena“** |
| Vozilo **nema prag** (nije uneta masa) | **„Nema praga“** |
| trošak ≤ prag „dobro“ | **„Dobro“** |
| trošak ≤ prag „za praćenje“ | **„Za praćenje“** |
| trošak ≤ prag „rizično“ | **„Rizično“** |
| trošak > prag „rizično“ | **„Neisplativo“** |

> **[Z] Pažnja na naziv:** status **„Opomena“** ne znači da je vozilo problematično —
> znači da **nema podatka o kilometraži**, pa se trošak po km nije mogao izračunati.
> Naziv je obmanjujuć; vidi pitanje **Q19**.

#### B) „Crvena zona“ — zaseban pokazatelj [P]

Koristi se na statistici centra (V-24), **nezavisno** od pragova po masi:

> vozilo je u crvenoj zoni ako:
> **nije** u dugoročnom najmu **i** knjigovodstvena vrednost **> 0**
> **i** neto trošak održavanja **>** knjigovodstvena vrednost

Poslovno značenje [Z]: u vozilo je uloženo više nego što ono vredi.

Dugoročni najam je izuzet jer vozilo nije u vlasništvu, pa poređenje sa
knjigovodstvenom vrednošću nema smisla. [Z]

### 8. Primer

| Vozilo | Masa | Trošak/km | Prag „dobro“ | Prag „praćenje“ | Prag „rizično“ | Status |
|---|---|---|---|---|---|---|
| Automobil A | 1.800 kg | 22,00 | 25 | 40 | 60 | **Dobro** |
| Automobil B | 1.800 kg | 38,50 | 25 | 40 | 60 | **Za praćenje** |
| Automobil C | 1.800 kg | 53,80 | 25 | 40 | 60 | **Rizično** |
| Automobil D | 1.800 kg | 72,00 | 25 | 40 | 60 | **Neisplativo** |
| Kamion E | 18.000 kg | 130,00 | 120 | 150 | 175 | **Za praćenje** |
| Vozilo F | — | 45,00 | — | — | — | **Nema praga** |
| Vozilo G | 1.800 kg | prazno | 25 | 40 | 60 | **Opomena** |

> Kamion sa 130 RSD/km je „Za praćenje“, dok je automobil sa 72 RSD/km „Neisplativo“ —
> upravo zato pragovi zavise od klase vozila.

### 9–11. Rezultat, upotreba i kontrola

Status se prikazuje uz svako vozilo u analitici flote i ulazi u V-09
(trajno neisplativa vozila). Kontrola: uporediti trošak po km sa tabelom pragova (V-11).

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Šest mogućih statusa i njihovi uslovi | Potvrđeno | `analytics.py:79-90` | — |
| Definicija crvene zone | Potvrđeno | `analytics.py:8-9` | — |
| Dugoročni najam izuzet iz crvene zone | Potvrđeno | `analytics.py:9` | — |
| **Naziv „Opomena“ za nedostatak podatka** | Potvrđeno | `analytics.py:80-81` | **Q19** |

---

## V-09 — Analiza troška po km kroz više perioda

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Trajno neisplativa vozila“ |
| Tehnički naziv | `cost_per_km_period_analysis()` |
| Putanja | [`fleet/support/dashboard.py:371`](../../../fleet/support/dashboard.py#L371) |

### 2. Poslovna svrha

Jedan loš period može biti posledica velikog servisa. Ovaj obračun izdvaja vozila koja
su **neisplativa u svim posmatranim periodima** — kod njih nije reč o slučajnosti.

### 6. Tačan postupak obračuna

1. Za **svaki** period se izvrši ceo obračun V-07. [P]
2. Svakom redu se dodeli status po V-12.
3. Redovi se grupišu po vozilu.
4. Vozilo ulazi u rezultat **samo ako** se pojavljuje u **svim** periodima
   **i** ima status **„Neisplativo“ u svima**. [P]
5. Za takvo vozilo uzima se red iz **prvog** perioda i dodaje poređenje sa **drugim**:

> **promena (%) = (trošak/km u prvom periodu − trošak/km u drugom periodu) / trošak/km u drugom periodu × 100**

Ako je trošak u drugom periodu 0 → promena je **0**. [P]

6. Sortiranje: opadajuće po trošku po kilometru prvog perioda. [P]

> **[P] Zahtev:** funkcija koristi `periods[0]` i `periods[1]`, pa **zahteva najmanje
> dva perioda**. Sa jednim periodom prekida se greškom. Vidi problem **P-12**.

### 8. Primer

> Periodi: „Tekuća godina“ (prvi) i „Prethodna godina“ (drugi).

| Vozilo | Tekuća godina | Status | Prethodna godina | Status | U rezultatu |
|---|---|---|---|---|---|
| A | 72,00 | Neisplativo | 68,00 | Neisplativo | **Da** |
| B | 72,00 | Neisplativo | 35,00 | Za praćenje | Ne |
| C | 80,00 | Neisplativo | — (nema podataka) | — | Ne |

Za vozilo A: promena = (72,00 − 68,00) / 68,00 × 100 = **+5,88%**.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Vozilo nema podatke u jednom periodu | **Ne ulazi** u rezultat | Namerno |
| Prosleđen samo jedan period | **Greška u izvršavanju** | **P-12** |
| Više od dva perioda | Poređenje se pravi **samo sa drugim** | Vidljivo |
| Trošak u drugom periodu = 0 | Promena je 0, ne beskonačno | Ispravno |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Vozilo mora biti „Neisplativo“ u svim periodima | Potvrđeno | `dashboard.py:396-398` | — |
| Poređenje ide sa drugim periodom | Potvrđeno | `dashboard.py:401-403` | — |
| **Zahteva najmanje dva perioda** | **Potvrđeno** | `dashboard.py:401` | **P-12** |

---

## V-10 — Neto trošak održavanja

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Neto trošak održavanja“ |
| Tehnički naziv | `net_maintenance_cost()` |
| Putanja | [`fleet/support/analytics.py:4`](../../../fleet/support/analytics.py#L4) |

### 2. Poslovna svrha

Stvarni trošak održavanja vozila **umanjen za ono što je osiguranje nadoknadilo**.
Bez tog umanjenja vozilo posle saobraćajne nezgode izgleda mnogo skuplje nego što jeste.

### 6. Tačan postupak obračuna

> **neto trošak održavanja = trošak servisa + trošak trebovanja − naknada osiguranja**

Prazne vrednosti se tretiraju kao **0**. [P]

| Sastojak | Tabela i kolona | Uslov |
|---|---|---|
| Trošak servisa | `fleet_servicetransaction.potrazuje` | — |
| Trošak trebovanja | `fleet_requisition.vrednost_nab` | — |
| Naknada osiguranja | `fleet_insurance.potrazuje` | **`kola = True`** |

> **[P]** Uslov `kola = True` znači „knjiženje se odnosi na automobil“. Naknade koje
> nisu obeležene tako se **ne odbijaju**.

### 8. Primer

| Stavka | Vrednost |
|---|---|
| Servisi | 145.000,00 RSD |
| Trebovanja | 38.000,00 RSD |
| Naknada osiguranja | −90.000,00 RSD |
| **Neto trošak održavanja** | **93.000,00 RSD** |

### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Statistika centra (V-24) | Zbir po centru i po vozilu |
| Crvena zona (V-12) | Poredi se sa knjigovodstvenom vrednošću |
| Detalj vozila (V-15) | Prikaz uz ukupne iznose |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Naknada veća od troška | **Negativan rezultat** — dozvoljeno, znači da je nadoknađeno više nego što je potrošeno |
| Naknada nije obeležena sa `kola = True` | Ne odbija se |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Formula servisi + trebovanja − naknade | Potvrđeno | `analytics.py:5` |
| Prazne vrednosti kao 0 | Potvrđeno | `analytics.py:5` |
| Uslov `kola = True` za naknade | Potvrđeno | `dashboard.py:205`, `center_statistics.py:97` |

---

## V-15 — Analitika evidentiranih troškova na detalju vozila

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Kartica „Analitika“ na detalju vozila |
| Tehnički naziv | `recorded_analytics()` |
| Putanja | [`fleet/support/vehicle_detail.py:35`](../../../fleet/support/vehicle_detail.py#L35) |

### 2. Poslovna svrha

Za **jedno vozilo i izabrani period** prikazuje **samo evidentirane iznose** — bez
procena, bez amortizacije, bez preračuna. Namerno se razlikuje od V-07.

> **[P] Izričita namera iz koda:** *„Period-based, recorded amounts for the vehicle
> dossier (no TCO estimates)“* — evidentirani iznosi, bez procene ukupnog troška vlasništva.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Datum po kome se filtrira |
|---|---|---|
| Gorivo | `fleet_fuelconsumption.cost_bruto` | `date` |
| Servisi | `fleet_servicetransaction.potrazuje` | `datum` |
| Trebovanja | `fleet_requisition.vrednost_nab` | `datum_trebovanja` |
| Naknade osiguranja | `fleet_insurance.potrazuje` | `datum` |
| Kategorija popravke | `fleet_servicetype.name` preko `popravka_kategorija` | — |

**Ograničenja perioda** (`VehiclePeriodForm`) [P]:

| Pravilo | Poruka |
|---|---|
| Početak mora biti pre kraja | „Početak perioda mora biti pre kraja perioda.“ |
| **Najviše 1.096 dana (3 godine)** | „Izaberite period do tri godine.“ |
| **Kraj ne sme biti u budućnosti** | „Analitika evidentiranih troškova ne obuhvata buduće datume.“ |

### 6. Tačan postupak obračuna

1. Napravi se **mesečni raster** od početka do kraja perioda; svaki mesec počinje
   praznim vrednostima (`None`), **ne nulama**. [P]
2. Za svaku od četiri vrste troška prolazi se kroz stavke; stavka ulazi samo ako
   ima datum **unutar perioda** i iznos koji nije prazan.
3. Za svaku stavku: uvećava se ukupan zbir, broj stavki i iznos odgovarajućeg meseca.
4. Servisi i trebovanja dodatno se zbrajaju **po kategoriji popravke**;
   stavka bez kategorije ide u **„Nerazvrstano“**. [P]
5. Izvedene veličine:

> **održavanje = servisi + trebovanja**
> **neto održavanje = održavanje − naknade osiguranja**

6. **Kilometraža** se računa **samo iz točenja goriva** (ne iz zaduženja):
   - po danu se uzimaju najmanja i najveća vrednost kilometraže;
   - potrebne su **najmanje dve** tačke;
   - ako bilo gde vrednost **opada**, prikazuje se upozorenje
     *„Očitanja kilometraže opadaju; proveriti unose ili zamenu brojača.“* i kilometraža
     se **ne prikazuje**;
   - inače: **kilometraža = najveća vrednost poslednjeg dana − najmanja vrednost prvog dana**.

7. Za grafički prikaz kategorija računa se širina trake:

> širina (%) = |iznos kategorije| / najveći apsolutni iznos × 100

**Znak iznosa [P]:** iznosi zadržavaju **izvorni knjigovodstveni znak** — storna i
ispravke ostaju negativne.

**Prazno naspram nule [P]:** mesec bez ijedne stavke ima `None`, ne `0`. Razlika je
namerna i vidljiva na ekranu.

### 8. Primer

> Vozilo, period 01.01.2026. – 31.03.2026.

| Mesec | Gorivo | Servisi | Trebovanja | Održavanje | Naknade |
|---|---|---|---|---|---|
| Januar | 60.000,00 | — | — | 0,00 | — |
| Februar | 58.000,00 | 45.000,00 | 12.000,00 | 57.000,00 | −30.000,00 |
| Mart | 62.000,00 | — | — | 0,00 | — |
| **Ukupno** | **180.000,00** | **45.000,00** | **12.000,00** | **57.000,00** | **−30.000,00** |

| Izvedeno | Vrednost |
|---|---|
| Održavanje | 45.000 + 12.000 = **57.000,00** |
| Neto održavanje | 57.000 − 30.000 = **27.000,00** |

Kilometraža iz točenja: prvi dan 120.000, poslednji dan 126.000 → **6.000 km**.

### 9–11. Rezultat, upotreba i kontrola

Rezultat se prikazuje samo na detalju vozila; nigde se ne čuva i ne prenosi.
Kontrola: zbir mesečnih iznosa mora biti jednak ukupnom iznosu; ukupan iznos goriva
mora odgovarati ekranu „Fakture goriva“ za isto vozilo i period (bruto).

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Period duži od 3 godine | Obrazac odbija unos |
| Kraj u budućnosti | Obrazac odbija unos |
| Kilometraža opada | Upozorenje, kilometraža se ne prikazuje |
| Manje od 2 dana sa očitavanjem | Kilometraža se ne prikazuje |
| Mesec bez stavki | Prazno, ne nula |
| Servis bez kategorije | „Nerazvrstano“ |

> **[P] Razlika prema V-07:** ova analitika **ne uključuje** amortizaciju, lizing i
> polise, i kilometražu računa **samo iz točenja**. Zbog toga se iznosi na detalju
> vozila i u analitici flote **legitimno razlikuju** — to nije greška.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Samo evidentirani iznosi, bez procena | Potvrđeno | `vehicle_detail.py:1, 35` |
| Prazno se razlikuje od nule | Potvrđeno | `vehicle_detail.py:40` |
| Znak iznosa se čuva | Potvrđeno | `vehicle_detail.py:35` |
| Kilometraža samo iz točenja | Potvrđeno | `vehicle_detail.py:66-70` |
| Ograničenje perioda na 3 godine | Potvrđeno | `vehicle_detail.py:22-23` |

---

## V-24 — Statistika po centrima

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Statistika centra“ |
| Tehnički naziv | `center_statistics()` |
| Putanja | [`fleet/views/center_statistics.py:57`](../../../fleet/views/center_statistics.py#L57) |
| Adresa | `/center_statistics/<sifra_centra>/` |

### 2. Poslovna svrha

Zbirna slika voznog parka jednog centra: broj vozila, vrednost, starost, troškovi,
potrošnja goriva i spisak vozila u **crvenoj zoni**.

### 3. Korisnici rezultata

Rukovodilac centra, uprava.

### 4. Ulazni podaci

Isti izvori kao V-07 i V-10, ali **bez ograničenja perioda**.

### 6. Tačan postupak obračuna

**Korak 1 — kontrola pristupa** [P]:

> Pristup je dozvoljen ako je korisnik **superuser** ili ako ima taj centar
> u `allowed_centers`. [P]

> **Ispravljeno 18.09.2026.** — ranije provera nije izuzimala `is_superuser`, pa je
> administrator bez upisanih centara dobijao **403 Zabranjeno**.
> Videti [P-13](../10-poznati-problemi.md).

**Korak 2 — vozila centra:** sva vozila čija je **poslednja** dodela u tom centru,
**bez otpisanih** (`otpis=False`). [P]

> **Ispravljeno 18.09.2026.** — otpisana vozila su ranije ulazila u broj vozila,
> vrednost i troškove centra. Zbog toga **iznosi centra od sada mogu biti manji nego
> ranije**. Videti [P-14 A](../10-poznati-problemi.md).

**Korak 3 — zbirovi po vozilu, bez filtera perioda** [P]:

| Pokazatelj | Izvor | Period |
|---|---|---|
| Trošak servisa | `potrazuje` | **Sve vreme** |
| Trošak trebovanja | `vrednost_nab` | **Sve vreme** |
| Količina goriva | `amount` | **Sve vreme** |
| Trošak goriva | `cost_bruto` | **Sve vreme** |
| Naknada osiguranja | `potrazuje`, `kola = True` | **Sve vreme** |
| Dugoročni najam | postoji li takav ugovor | — |

**Korak 4 — zbirni pokazatelji centra:**

| Pokazatelj | Formula |
|---|---|
| Broj vozila | broj vozila centra |
| Ukupna vrednost | Σ knjigovodstvena vrednost |
| Prosečna vrednost | ukupna vrednost / broj vozila |
| **Prosečna starost** | tekuća godina − (Σ godina proizvodnje / broj vozila **sa poznatom godinom**) |
| Ukupan neto trošak održavanja | Σ V-10 po vozilu |
| Odnos održavanja i vrednosti | ukupno neto održavanje / ukupna vrednost × 100 |
| Broj vozila u crvenoj zoni | broj vozila po V-12 B |

> **[P]** U prosečnu starost ulaze **samo vozila sa godinom proizvodnje između 1886. i
> tekuće**, isto kao u preseku stanja flote. Ako nijedno vozilo nema unetu godinu,
> prikazuje se `—`, a ne broj. Ekran uz pokazatelj prikazuje i **za koliko vozila je
> godište poznato** (`poznato godište X/Y`), da prosek ne bi obmanuo kada je poznat za
> mali deo voznog parka.
>
> **Ispravljeno 18.09.2026.** — ranije je vozilo bez godine ulazilo kao **0**, pa je
> „prosečna starost“ znala da bude i preko hiljadu godina.
> Videti [P-14 B](../10-poznati-problemi.md).

**Korak 5 — po vozilu:**

| Pokazatelj | Formula |
|---|---|
| Neto trošak održavanja | V-10 |
| Odnos ulaganja i vrednosti | neto održavanje / knjigovodstvena vrednost × 100 |
| Razlika do vrednosti | neto održavanje − knjigovodstvena vrednost |
| Crvena zona | V-12 B |

Vozila u crvenoj zoni sortiraju se opadajuće po razlici do vrednosti. [P]

**Korak 6 — mesečni pregled** [P]: gorivo (količina i iznos), servisi razvrstani po
kategoriji popravke, i premije polisa.

Razvrstavanje ide u dva koraka: nazivi svih kategorija iz `ServiceType` se prvo
**normalizuju** (mala slova, uklonjeni dijakritici, sređeni razmaci), pa se po ključnoj
reči dobije spisak šifara; iznosi se zatim filtriraju **po šifri kategorije**. [P]

| Kolona | Ključna reč u normalizovanom nazivu |
|---|---|
| Gume | `gume` |
| Redovan servis | `redovan servis` |
| Tehnički pregled | `tehnicki pregled` |
| Registracija | `registracija` |

Mesečni pregled prikazuje šest iznosa: količinu i trošak goriva, gume, redovan servis,
tehnički pregled i registraciju, uz premije polisa — svaki sa zbirom i mesečnim
prosekom. [P]

> **Ispravljeno 18.09.2026.** — ranije se poređenje radilo nad **sirovim** nazivom, pa
> kategorija „Tehnički pregled“ (sa „č“) nije bila prepoznata. Uz to se taj iznos, iako
> izračunat, **nigde nije prikazivao** — nije bio ni u zbirovima ni u tabeli. Zato je
> dodata i **kolona „Trošak Tehnički Pregled (Din)“**.
> Videti [P-14 C](../10-poznati-problemi.md).

**Korak 7 — proseci:** ukupan iznos podeljen **brojem meseci koji imaju bilo kakav
zapis** — ne brojem meseci u kalendaru. [P]

### 8. Primer

> Ilustrativni primer, centar sa 3 vozila.

| Vozilo | Knjig. vrednost | Servisi | Trebovanja | Naknade | Neto održavanje | Crvena zona |
|---|---|---|---|---|---|---|
| A | 1.200.000 | 145.000 | 38.000 | 90.000 | 93.000 | Ne |
| B | 300.000 | 420.000 | 55.000 | 0 | 475.000 | **Da** (475.000 > 300.000) |
| C | 0 | 80.000 | 10.000 | 0 | 90.000 | Ne (vrednost nije > 0) |

| Pokazatelj centra | Vrednost |
|---|---|
| Ukupna vrednost | 1.500.000,00 |
| Ukupno neto održavanje | 658.000,00 |
| Odnos održavanja i vrednosti | 658.000 / 1.500.000 × 100 = **43,87%** |
| Vozila u crvenoj zoni | **1** (vozilo B) |

### 9–11. Rezultat, upotreba i kontrola

Rezultat se prikazuje na ekranu i nigde ne čuva. Kontrola: zbir po vozilima mora biti
jednak zbiru centra; spisak vozila u crvenoj zoni mora se slagati sa ručnim poređenjem
neto održavanja i knjigovodstvene vrednosti.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Superuser bez dozvoljenih centara | Pristup dozvoljen | Ispravljeno, **P-13** |
| Otpisana vozila | Isključena iz statistike | Ispravljeno, **P-14 A** |
| Vozilo bez godine proizvodnje | Ne ulazi u prosečnu starost; ekran prikazuje `poznato godište X/Y` | Ispravljeno, **P-14 B** |
| Nijedno vozilo nema godinu | Prosečna starost se prikazuje kao `—` | Ispravljeno, **P-14 B** |
| Kategorija sa dijakriticima | Prepoznaje se — nazivi se normalizuju pre poređenja | Ispravljeno, **P-14 C** |
| Vozilo bez knjigovodstvene vrednosti | Ne može biti u crvenoj zoni | Namerno |
| Vozilo u dugoročnom najmu | Ne može biti u crvenoj zoni | Namerno |
| Svi iznosi su **za ceo vek vozila** | Nema izbora perioda | Namerno, ali nije naznačeno na ekranu |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Iznosi su za ceo vek vozila, bez perioda | Potvrđeno | `center_statistics.py:72-101` | **P-14 D** |
| Centar je poslednja dodela | Potvrđeno | `center_statistics.py:65-67` | **P-05** |
| Superuser ima pristup | Potvrđeno | `center_statistics.py` — provera `is_superuser` | Rešeno, **P-13** |
| Otpisana vozila su isključena | Potvrđeno | `center_statistics.py` — `otpis=False` | Rešeno, **P-14 A** |
| Prosečna starost samo iz poznatih godišta | Potvrđeno | `center_statistics.py` — opseg 1886 … tekuća | Rešeno, **P-14 B** |
| Kategorije se prepoznaju bez obzira na dijakritike | Potvrđeno | `center_statistics.py` — `service_type_ids_by_keyword()` | Rešeno, **P-14 C** |
| Iznosi su za ceo vek vozila i to nije naznačeno na ekranu | Potvrđeno | `center_statistics.py` | **P-14 D — ostaje** |

---

## Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q17** | Trošak po kilometru koristi **bruto** iznos goriva (`cost_bruto`, sa PDV-om), dok izveštaji po šifri posla prikazuju i neto. Da li je bruto željeni osnov za poređenje vozila? |
| **Q18** | Odakle potiču pragovi troška po kilometru (25/40/60 za putnička, 120/150/175 za teška teretna)? Da li su još važeći i da li treba da budu izmenljivi kroz interfejs umesto u kodu? |
| **Q19** | Status **„Opomena“** dodeljuje se vozilu kod koga **nema podatka o kilometraži**, što korisnika navodi da pomisli da je vozilo problematično. Može li se preimenovati u „Nema kilometraže“? |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.2. Flota — gorivo](06-02-flota-gorivo.md) | Prečišćavanje transakcija, potrošnja, gorivo po šifri posla |
| [6.4. Flota — ugovori i polise](06-04-flota-ugovori-polise.md) | Mesečni troškovi polisa, lizinga i servisa |
| [6.5. Flota — izveštaji](06-05-flota-izvestaji.md) | Kilometraža, održavanje, presek flote, izveštaji za upravu |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema P-03 … P-14 |
