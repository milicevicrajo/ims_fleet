# 6.5. Flota — kilometraža, održavanje, presek stanja i izveštaji

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](../10-poznati-problemi.md).

**Sadržaj:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [V-13](#v-13--kilometraža-vozila--posmatrana-vremenska-linija) | Kilometraža vozila — posmatrana vremenska linija | — |
| [V-14](#v-14--održavanje-vozila-i-servisni-interval) | Održavanje vozila i servisni interval | — |
| [V-16](#v-16--presek-stanja-flote-kontrolna-tabla) | Presek stanja flote (kontrolna tabla) | — |
| [V-22](#v-22--izveštaji-za-upravu) | Izveštaji za upravu (4 izveštaja) | **P-26** |
| [Poglavlje 6.5.5](#655-izveštaji-nad-nasleđenim-pogledima) | 11 izveštaja nad nasleđenim pogledima | **P-27** |

---

## V-13 — Kilometraža vozila — posmatrana vremenska linija

> Ovo je **najpažljivije napisan obračun u modulu Flota**. Za razliku od procene
> kilometraže (V-08), ovaj prikazuje **samo ono što je stvarno očitano** i izričito
> odbija da prikaže kilometražu kada podaci nisu pouzdani.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kilometraža“ na detalju vozila |
| Tehnički naziv | `vehicle_mileage()`, `observed_timeline()` |
| Putanja | [`fleet/support/vehicle_mileage.py:55`](../../../fleet/support/vehicle_mileage.py#L55) |
| Namera iz koda | *„Observed odometer readings and non-overlapping intervals near 30 days“* |

### 2. Poslovna svrha

Prikazuje **sva očitavanja brojača** jednog vozila kroz vreme, razvrstana u intervale
od približno 30 dana, i **jasno označava mesta gde kilometraža opada** — što ukazuje na
grešku unosa ili zamenu brojača.

### 3. Korisnici rezultata

Služba voznog parka, garaža — za kontrolu kvaliteta unosa i za proveru stvarne
pređene kilometraže.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Oznaka izvora na ekranu | Dozvoljena nula |
|---|---|---|---|
| Kilometraža NIS točenja | `fleet_transactionnis.kilometraza` (`datum_transakcije`) | „NIS — točenje“ | Ne |
| Kilometraža OMV točenja | `fleet_transactionomv.mileage` (`transaction_date`) | „OMV — točenje“ | Ne |
| **Ispravljena kilometraža OMV** | `fleet_transactionomv.corrected_mileage` | „OMV — korigovano u izvoru“ | Ne |
| Ranija evidencija goriva | `fleet_fuelconsumption.mileage` (`date`) | „Ranija evidencija goriva“ | Ne |
| Početna kilometraža zaduženja | `fleet_vehicletravelorder.start_mileage` (`created_at`) | „Nalog vozila — početak“ | **Da** |
| Krajnja kilometraža zaduženja | `fleet_vehicletravelorder.end_mileage` (`closed_at`) | „Nalog vozila — završetak“ | **Da** |

**Filteri ekrana** (`MileagePeriodForm`) [P]: „Očitavanja od“ i „Očitavanja do“.
Početak ne sme biti posle završetka.

### 5. Poreklo podataka

```
 NIS transakcije   ──┐
 OMV transakcije   ──┤  (ispravljena kilometraža ima prednost)
                     ├──► spisak očitavanja  ──► dnevni maksimum i minimum
 Evidencija goriva ──┤     (samo za dane koje                    │
 Zaduženja vozila  ──┘      NIS/OMV ne pokrivaju)                 ▼
                                                    intervali od ~30 dana
                                                                 │
                                                    provera pada kilometraže
                                                                 ▼
                                               prikaz sa oznakom pouzdanosti
```

### 6. Tačan postupak obračuna

#### Korak 1 — prikupljanje očitavanja [P]

Očitavanje se **odbacuje** ako:

| Uslov | Objašnjenje |
|---|---|
| Nema datuma | — |
| **Datum je u budućnosti** | `day > danas` |
| Vrednost nije broj ili nije konačna | |
| Vrednost je negativna | |
| Vrednost je **0**, a izvor ne dozvoljava nulu | Dozvoljena je samo kod zaduženja vozila |

Svako odbačeno očitavanje se broji i prikazuje korisniku kao broj izuzetih. [P]

**OMV — ispravljena kilometraža [P]:** ako je `corrected_mileage` popunjena i veća od 0,
koristi se **ona**, uz oznaku „OMV — korigovano u izvoru“. Izvorna vrednost se pamti
i prikazuje ako se razlikuje.

**Evidencija goriva — samo dopunski [P]:** `fleet_fuelconsumption` se koristi **samo za
dane koje nijedna NIS ili OMV transakcija ne pokriva**, da se isto točenje ne bi pojavilo
dvaput iz dva izvora.

#### Korak 2 — dnevni sažetak [P]

Za svaki dan sa očitavanjima:

| Veličina | Značenje |
|---|---|
| `value` | **Najveća** kilometraža tog dana — merodavna vrednost |
| `minimum` | **Najmanja** kilometraža tog dana — služi za proveru pada |
| `source` | Izvori koji su dali najveću vrednost |
| `count` | Broj očitavanja tog dana |

#### Korak 3 — intervali od približno 30 dana [P]

Postupak je lančani, bez preklapanja:

1. Početak (`anchor`) je **prvi** dan sa očitavanjem.
2. Cilj je `datum početka + 30 dana`.
3. Za kraj intervala bira se dan koji je **najbliži cilju**
   (pri jednakoj udaljenosti — raniji datum).
4. Interval se upisuje, a **kraj postaje početak sledećeg intervala**.
5. Ponavlja se do kraja spiska.

**Pređena kilometraža intervala:**

> **km = najveća vrednost poslednjeg dana − najveća vrednost prvog dana**

**ali samo ako u intervalu nema pada.** [P]

#### Korak 4 — prepoznavanje pada kilometraže [P]

Unutar intervala se za svaki dan proverava:

> **`minimum` tog dana < `value` prethodnog dana**  →  **pad**

Ako je pad pronađen bilo gde u intervalu:

> **km intervala = prazno** (`None`), a datumi padova se prikazuju kao problem

#### Korak 5 — ukupna kilometraža [P]

> **ukupno = zbir km svih intervala — ali samo ako nijedan interval nema pad**
> U suprotnom: **prazno**

> **[P] Ovo je namerno strogo pravilo.** Sistem radije **ne prikaže ništa** nego da
> prikaže zbir koji zna da je pogrešan.

#### Korak 6 — trenutno stanje [P]

Poslednji dan sa očitavanjem prikazuje se zasebno, sa oznakom `needs_check` ako je
njegov minimum manji od vrednosti prethodnog dana.

**Trenutno stanje se računa iz *svih* očitavanja**, nezavisno od izabranog perioda. [P]

#### Sortiranje i prikaz [P]

Intervali se prikazuju **obrnutim redosledom** — najnoviji prvi.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/vehicle_mileage.py` |
| Funkcije | `vehicle_mileage()`, `observed_timeline()` |
| Obrazac | `MileagePeriodForm` |
| Ekran | Od 21.09.2026. podloga kartice „Potrošnja goriva“ i obračuna RSD/km; zasebna kartica „Kilometraža“ zamenjena je potrošnjom |
| Testovi | `fleet/test_vehicle_mileage.py` — 11 testova |

### 8. Primer obračuna

> Ilustrativni primer.

**Očitavanja:**

| Datum | Vrednost | Izvor |
|---|---|---|
| 05.01.2026. | 120.000 | OMV — točenje |
| 05.01.2026. | 120.050 | Nalog vozila — početak |
| 03.02.2026. | 121.400 | NIS — točenje |
| 06.03.2026. | 122.900 | OMV — točenje |
| 06.03.2026. | 118.000 | Nalog vozila — završetak |

**Dnevni sažetak:**

| Datum | Minimum | Vrednost (maksimum) |
|---|---|---|
| 05.01. | 120.000 | **120.050** |
| 03.02. | 121.400 | **121.400** |
| 06.03. | **118.000** | 122.900 |

**Intervali:**

| Interval | Dana | Od | Do | Pad? | km |
|---|---|---|---|---|---|
| 05.01. → 03.02. | 29 | 120.050 | 121.400 | Ne | **1.350** |
| 03.02. → 06.03. | 31 | 121.400 | 122.900 | **Da** — 06.03. minimum 118.000 < 121.400 | **prazno** |

| Rezultat | Vrednost |
|---|---|
| Ukupna kilometraža | **prazno** — jer jedan interval ima pad |
| Broj problema | 1 |
| Trenutno stanje | 122.900, uz oznaku „potrebna provera“ |

> Sistem **ne prikazuje** zbir od 2.850 km, iako bi ga mogao izračunati — jer bi taj
> broj bio neproverljiv. Korisniku se prikazuje tačan datum problema (06.03.) i on
> proverava unos zaduženja.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Spisak očitavanja, intervali od ~30 dana i ukupna kilometraža |
| Format | Tabela na ekranu |
| Gde se čuva | Nigde |
| Kada se ponovo računa | Pri svakom otvaranju |
| Može li korisnik da ga izmeni | Posredno — ispravkom kilometraže na zaduženju |

### 10. Upotreba rezultata

Kontrola kvaliteta unosa i provera procene iz V-08. **Ne ulazi** ni u jedan drugi
obračun — V-07 koristi svoju, jednostavniju procenu.

> **[Z] Nedoslednost koja nije greška:** V-13 odbija da prikaže kilometražu kada
> primeti pad, a V-08 u istoj situaciji **tiho** bira drugi par očitavanja i ipak daje
> procenu. Dva ekrana zato mogu pokazati različitu sliku istog vozila.

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Ukupno je prazno | Postoji pad — pronaći datum u koloni problema i proveriti unos |
| Nedostaje očitavanje | Proveriti broj izuzetih očitavanja ispod tabele |
| Vrednost izgleda pogrešno | Proveriti izvor u koloni „Izvor“ — zaduženje unosi zaposleni, točenje dolazi iz izvora |
| OMV korigovana vrednost | Oznaka „korigovano u izvoru“ znači da je dobavljač sam ispravio kilometražu |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Datum u budućnosti | Očitavanje se odbacuje i broji kao izuzeto |
| Kilometraža 0 na točenju | Odbacuje se |
| Kilometraža 0 na zaduženju | **Prihvata se** — novo vozilo može imati 0 km |
| Dva očitavanja istog dana sa različitim vrednostima | Uzima se najveća; najmanja služi za proveru pada |
| Zamena brojača | Prepoznaje se kao pad, kilometraža se ne prikazuje |
| Manje od dva dana sa očitavanjem | Nema intervala, nema ukupne kilometraže |
| Isto točenje u dva izvora | Sprečeno — evidencija goriva se koristi samo za nepokrivene dane |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Budući datumi i nule se odbacuju | Potvrđeno | `vehicle_mileage.py:68-70` |
| Ispravljena OMV kilometraža ima prednost | Potvrđeno | `vehicle_mileage.py:76-80` |
| Evidencija goriva samo za nepokrivene dane | Potvrđeno | `vehicle_mileage.py:81-85` |
| Dnevni maksimum je merodavan, minimum za proveru | Potvrđeno | `vehicle_mileage.py:32-35` |
| Intervali ciljaju 30 dana, bez preklapanja | Potvrđeno | `vehicle_mileage.py:37-45` |
| Pad kilometraže poništava km intervala | Potvrđeno | `vehicle_mileage.py:42, 45` |
| Ukupno je prazno ako ijedan interval ima pad | Potvrđeno | `vehicle_mileage.py:52` |

---

## V-14 — Održavanje vozila i servisni interval

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Održavanje“ na detalju vozila |
| Tehnički naziv | `vehicle_maintenance()` |
| Putanja | [`fleet/support/vehicle_maintenance.py:25`](../../../fleet/support/vehicle_maintenance.py#L25) |
| Namera iz koda | *„Vehicle maintenance evidence using explicit links and document dates only“* |

### 2. Poslovna svrha

Objedinjuje **sve dokaze o održavanju jednog vozila** — naloge garaže, zahteve nabavke,
fakture i trebovanja — i odgovara na pitanje: **kada je poslednji put rađen mali,
a kada veliki servis?**

### 3. Korisnici rezultata

Garaža, služba voznog parka.

### 4. Ulazni podaci

| Poslovni naziv | Tabela | Uloga |
|---|---|---|
| Nalog garaže (prijava kvara) | `fleet_kvar` | **Nalog** |
| Predmet nabavke | `nabavka_procurement_case` | **Nalog** |
| Veza fakture i predmeta | `nabavka_invoice_link` | Dokument |
| EUF faktura | `nabavka_invoice` | Dokument |
| UF faktura | `nabavka_uf_invoice_snapshot` | Dokument |
| UF stavka | `nabavka_euf_item_snapshot` | Dokument |
| Trebovanje | `fleet_requisition` | Dokument |
| Kategorija popravke | `fleet_servicetype.name` | Razvrstavanje |

### 6. Tačan postupak obračuna

#### Korak 1 — nalozi [P]

| Izvor | Oznaka | Vrsta intervencije |
|---|---|---|
| `fleet_kvar` | `rbz` ili `PK <id>` | `work_type` kvara |
| `nabavka_procurement_case` | `case_number` | `work_type` predmeta, a ako je prazan — `work_type` povezanog naloga garaže **istog vozila** |

Predmeti nabavke se uzimaju i kada su vezani **za vozilo**, i kada su vezani **za nalog
garaže tog vozila** bez sopstvene veze ka vozilu. [P]

#### Korak 2 — dokumenti [P]

Iz svakog predmeta se skupljaju fakture i UF stavke. Ključno pravilo:

> **Dokument izričito dodeljen drugom vozilu nije dokaz za ovo vozilo** —
> faktura sa `vehicle_id` različitim od posmatranog vozila se **preskače**.

Isto pravilo se primenjuje i naknadno: ako se faktura kasnije dodeli drugom vozilu,
ona se **uklanja** iz spiska. [P]

#### Korak 3 — razvrstavanje kategorije popravke [P]

Funkcija `service_category()` normalizuje naziv kategorije:

1. Sve u mala slova, donje crte u razmake, višestruki razmaci u jedan.
2. Uklanjaju se nastavci **„ van ims“** i **„ u ims“**.
3. Mapiranje:

| Normalizovan naziv | Vrsta |
|---|---|
| `mali servis` | `mali_servis` |
| `veliki servis` | `veliki_servis` |
| **`мали сервис`** (ćirilica) | `mali_servis` |
| **`велики сервис`** (ćirilica) | `veliki_servis` |
| `popravka` | `popravka` |
| bilo šta drugo | prazno („Nije razvrstano“) |

> **[P] Ispravno rešeno:** ovo je jedino mesto u sistemu koje prepoznaje i **ćirilične**
> nazive kategorija. Statistika centra (V-24) od 18.09.2026. takođe normalizuje nazive,
> ali samo latinične — videti [P-14 C](../10-poznati-problemi.md).

#### Korak 4 — sukob podataka [P]

Dokument dobija oznaku **„Proveriti kategoriju / datum“** ako:

| Uslov | Objašnjenje |
|---|---|
| Ima **više od jedne** vrste intervencije | Isti dokument je vezan za nalog malog i velikog servisa |
| Ima **različite datume** iz različitih izvora | Faktura ima jedan datum u vezi, drugi u zaglavlju |

Otkazani predmeti (`cancelled`) **ne prenose** svoju vrstu intervencije na dokument. [P]

#### Korak 5 — prenos veza sa predmeta na nalog garaže [P]

Ako je predmet nabavke vezan za nalog garaže, **svi njegovi dokumenti se pripisuju i
tom nalogu** — da bi nalog garaže prikazao kompletan trag. Otkazani predmeti se izuzimaju.

#### Korak 6 — sažetak po vrsti servisa [P]

Za `mali_servis` i `veliki_servis` posebno:

> uzimaju se dokumenti koji imaju **tačno tu vrstu**, **nemaju sukob**,
> imaju datum i taj datum **nije u budućnosti**

| Podatak | Značenje |
|---|---|
| **Poslednji** | Najnoviji takav dokument |
| **Broj** | Ukupan broj takvih dokumenata |

Dokumenti su sortirani opadajuće po datumu, pa je prvi ujedno i najnoviji. [P]

> **[P] Važno:** dokument sa sukobom kategorije **ne ulazi** u sažetak. Zato broj
> u sažetku može biti manji od broja dokumenata u spisku.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/vehicle_maintenance.py` |
| Funkcije | `vehicle_maintenance()`, `service_category()` |
| Ekran | Detalj vozila, kartica „Održavanje“ |
| Testovi | `fleet/test_vehicle_maintenance.py` — 12 testova |

> **[P] Šta se NE koristi:** servisni interval iz `fleet_vehicle.service_interval`
> (podrazumevano 15.000 km) **ne ulazi** u ovaj obračun. Sistem prikazuje **kada je
> servis rađen**, ali **ne računa kada sledeći dospeva**. Vidi pitanje **Q23**.

### 8. Primer

| Dokument | Datum | Vrsta iz naloga | Sukob | U sažetku „mali servis“ |
|---|---|---|---|---|
| Faktura F-100 | 10.01.2026. | mali servis | Ne | **Da** |
| Faktura F-220 | 15.03.2026. | mali servis | Ne | **Da — poslednji** |
| Trebovanje 45/2026 | 20.03.2026. | mali servis + veliki servis | **Da** | Ne |
| Faktura F-300 | 05.05.2026. *(budući datum)* | mali servis | Ne | Ne |

**Sažetak „Mali servis“:** poslednji **15.03.2026.**, broj **2**.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde |
| Upotreba | Prikaz na detalju vozila |
| Kontrola | Otvoriti povezani nalog ili fakturu — svaki red ima vezu ka izvornom dokumentu |
| Sukob kategorije | Otvoriti dokument i proveriti kojim je nalozima vezan |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Dokument vezan za dva naloga različite vrste | Oznaka sukoba, izuzet iz sažetka |
| Dokument sa različitim datumima iz dva izvora | Oznaka sukoba |
| Otkazan predmet nabavke | Ne prenosi vrstu, ne prenosi veze |
| Faktura dodeljena drugom vozilu | Uklanja se iz spiska |
| Dokument sa budućim datumom | Vidljiv u spisku, **izuzet iz sažetka** |
| Kategorija nepoznatog naziva | „Nije razvrstano“ |
| **Servisni interval u km** | **Ne koristi se** — nema upozorenja o dospeću servisa |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Dokument drugog vozila se isključuje | Potvrđeno | `vehicle_maintenance.py:75-77, 95-97` | — |
| Ćirilični nazivi kategorija se prepoznaju | Potvrđeno | `vehicle_maintenance.py:21` | — |
| Sukob vrste ili datuma isključuje iz sažetka | Potvrđeno | `vehicle_maintenance.py:130, 140-141` | — |
| Budući datumi se izuzimaju iz sažetka | Potvrđeno | `vehicle_maintenance.py:141` | — |
| **Servisni interval se ne koristi** | Potvrđeno | Nema upotrebe `service_interval` | **Q23** |

---

## V-16 — Presek stanja flote (kontrolna tabla)

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kontrolna tabla flote“ |
| Tehnički naziv | `fleet_snapshot()` |
| Putanja | [`fleet/support/fleet_snapshot.py:13`](../../../fleet/support/fleet_snapshot.py#L13) |
| Adresa | `/` (početna strana) |
| Namera iz koda | *„Current fleet inventory. All center totals use the same scoped vehicle set.“* |

### 2. Poslovna svrha

Jedinstvena početna slika: **koliko vozila imamo, gde su, koliko vrede i šta traži hitnu
radnju.**

### 3. Korisnici rezultata

Služba voznog parka (svakodnevno), rukovodioci centara, uprava.

### 4. Ulazni podaci

| Podatak | Tabela i kolona | Datum |
|---|---|---|
| Vozila | `fleet_vehicle` | — |
| Trenutni centar, OJ, šifra posla | `fleet_jobcode` | Dodela `<= danas` |
| Registarska oznaka i rok registracije | `fleet_trafficcard` | Izdata `<= danas` |
| Polise | `fleet_policy` | Sve |
| Otvorena zaduženja | `fleet_vehicletravelorder` | Otvoreno `<= danas`, zatvoreno prazno ili `> danas` |
| Nedovršene evidencije | `fleet_policy`, `fleet_draftservicetransaction`, `fleet_requisition`, `fleet_draftinsurance` | — |

### 6. Tačan postupak obračuna

#### Korak 1 — obuhvat po centrima [P]

> Ako korisnik ima upisane `allowed_centers`, prikazuju se **samo vozila čiji je
> trenutni centar u toj listi**. Prazna lista znači **pun obuhvat**.

#### Korak 2 — razdvajanje otpisanih [P]

| Skup | Uslov |
|---|---|
| Prikazana vozila | `otpis = False` |
| Brojač arhiviranih | `otpis = True` — prikazuje se samo kao broj |

#### Korak 3 — statistika (ista funkcija za centar i za ukupno) [P]

| Pokazatelj | Postupak |
|---|---|
| Broj vozila | Broj redova |
| Putnička / teretna / priključna / ostalo | Po `category` |
| **Prosečna starost** | `tekuća godina − (zbir godina / broj)` — **samo za vozila sa godinom između 1886. i tekuće** |
| Poznata godišta | Broj vozila sa ispravnom godinom |
| Knjigovodstvena vrednost | Zbir `value`, **samo za vozila sa unetom vrednošću** |
| Poznate vrednosti | Broj vozila sa unetom vrednošću |
| Zadužena vozila | Broj vozila sa bar jednim otvorenim zaduženjem |
| Vozila sa važećom AO | Broj vozila sa aktivnom polisom autoodgovornosti |

> **[P] Ispravno rešeno:** prosečna starost računa **samo vozila sa ispravnom godinom**,
> i uz nju se prikazuje **koliko je godišta poznato**. Statistika centra (V-24) je
> 18.09.2026. preuzela isti način računanja — videti
> [P-14 B](../10-poznati-problemi.md).

#### Korak 4 — važeća polisa autoodgovornosti [P]

> polisa je aktivna ako: ima početak i kraj **i** `početak <= danas <= kraj`
> polisa je AO ako naziv tipa **sadrži** `AUTOODGOVORNOST` (velikim slovima)

> **[P]** Ovde je uslov **„sadrži“**, za razliku od mesečnih troškova polisa (V-17)
> gde je uslov **„tačno jednako“**. Zato „Autoodgovornost — obavezno“ ovde **jeste**
> prepoznata, a tamo **nije**.

#### Korak 5 — upozorenja [P]

Osam grupa, po redosledu prikaza:

| # | Grupa | Uslov | Ton |
|---|---|---|---|
| 1 | **Registracija je istekla** | `registration_valid_until < danas` | Opasnost |
| 2 | **Registracija ističe u 30 dana** | `danas <= rok <= danas + 30` | Upozorenje |
| 3 | **Nedostaje rok registracije** | Rok nije unet | Obaveštenje |
| 4 | **Nema važeće AO polise** | Vozilo nema aktivnu AO polisu | Upozorenje |
| 5 | **Polise pred istekom bez nastavka pokrića** | vidi ispod | Upozorenje |
| 6 | **Vozila bez trenutnog centra** | Nema dodele | Obaveštenje |
| 7 | **Više istovremenih zaduženja** | Vozilo ima 2+ otvorenih zaduženja | Upozorenje |
| 8 | **Evidencije za dopunu** | Brojači nedovršenih zapisa | Obaveštenje |

**Grupa 5 — pravilo nastavka pokrića [P]:**

Aktivna polisa ulazi u upozorenje ako:

| Uslov | |
|---|---|
| `end_date <= danas + 30` | Ističe uskoro |
| `is_renewable = True` | Obnavlja se |
| **ne postoji „produžetak“** | vidi ispod |

Produžetak postoji ako postoji **druga polisa istog vozila i iste vrste** (poređenje po
tipu u velikim slovima, bez suvišnih razmaka) koja:

> počinje **najkasnije dan posle** isteka posmatrane polise **i** traje **duže** od nje

> **[P]** Ovo je **strože i tačnije** pravilo od onog na ekranu `/polise/istek/` (V-18),
> koje ne proverava neprekidnost pokrića. Vidi pitanje **Q20**.

**Grupa 8 — evidencije za dopunu [P]:**

| Stavka | Uslov | Vidi je |
|---|---|---|
| Polise za dopunu | `Policy.incomplete_q()` | Svi |
| Spoljne usluge za povezivanje | `DraftServiceTransaction` — sve | **Samo korisnici bez ograničenja centara** |
| Trebovanja bez vozila | `Requisition` sa `nije_garaza = False` i bez vozila | Samo bez ograničenja |
| Naknade osiguranja za povezivanje | `DraftInsurance` — sve | Samo bez ograničenja |

Za korisnika sa ograničenim centrima broje se **samo polise njegovih vozila**; za korisnika
bez ograničenja broje se i **polise bez vozila**. [P]

#### Korak 6 — pregled po centrima [P]

Vozila se grupišu po trenutnom centru; centar bez šifre prikazuje se kao **„Bez centra“**
i sortira **poslednji**.

> **učešće centra (%) = broj vozila centra / ukupan broj vozila × 100**

### 8. Primer

> Ilustrativni primer, korisnik bez ograničenja centara, 12 vozila.

| Pokazatelj | Vrednost |
|---|---|
| Vozila u upotrebi | 12 |
| Arhivirano (otpisano) | 3 |
| Putnička / teretna / priključna | 8 / 3 / 1 |
| Poznata godišta | 11 od 12 |
| Prosečna starost | 2026 − (2015,4) = **10,6 godina** |
| Knjigovodstvena vrednost | 14.500.000,00 RSD (poznato za 10 vozila) |
| Zadužena vozila | 4 |
| Vozila sa važećom AO | 11 |

**Upozorenja:**

| Grupa | Broj |
|---|---|
| Registracija je istekla | 1 |
| Nema važeće AO polise | 1 |
| Više istovremenih zaduženja | 1 |
| Evidencije za dopunu | 3 vrste |

> Vozilo sa nepoznatim godištem **ne obara** prosečnu starost — prikazano je da je
> poznato 11 od 12 godišta.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde |
| Kada se računa | Pri svakom otvaranju početne strane, uvek u odnosu na **današnji dan** |
| Upotreba | Svakodnevni operativni pregled |
| Kontrola | Svako upozorenje ima vezu ka konkretnom vozilu ili polisi |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Vozilo bez dodele | Grupa „Bez centra“, zasebno upozorenje |
| Korisnik sa ograničenim centrima | Vidi manje vozila i **manje vrsta** nedovršenih evidencija |
| Vozilo bez godine proizvodnje | **Ne ulazi** u prosečnu starost; prikazuje se broj poznatih godišta |
| Vozilo bez knjigovodstvene vrednosti | Ne ulazi u zbir; prikazuje se broj poznatih vrednosti |
| Polisa bez vozila | Broji se u „Polise za dopunu“ samo za korisnike bez ograničenja |
| Rok registracije nije unet | Zasebna grupa — **datum AO polise se ne prepisuje automatski kao rok registracije** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Obuhvat po `allowed_centers`; prazna lista = pun obuhvat | Potvrđeno | `fleet_snapshot.py:25-27` |
| Otpisana vozila su odvojena i samo prebrojana | Potvrđeno | `fleet_snapshot.py:28-29` |
| Prosečna starost samo za ispravna godišta | Potvrđeno | `fleet_snapshot.py:45, 51` |
| AO se prepoznaje po **sadržaju** naziva tipa | Potvrđeno | `fleet_snapshot.py:34` |
| Pravilo nastavka pokrića polise | Potvrđeno | `fleet_snapshot.py:73-78` |
| Brojač zaduženih vozila broji vozilo jednom | Potvrđeno | `fleet_snapshot.py:36, 52` |

---

## V-22 — Izveštaji za upravu

Četiri izveštaja sa zajedničkim okvirom: filteri, tabela, pokazatelji, napomene o
obuhvatu i **izvoz u Excel sa zasebnim listom „Obuhvat“**. [P]

| Izveštaj | Adresa | Dozvola |
|---|---|---|
| Kasko — vozila starija od 7 godina | `/izvestaji/osiguranje/kasko/` | `vehicle_list` |
| Auto osiguranje — vlasništvo IMS | `/izvestaji/osiguranje/ims/` | `vehicle_list` |
| Gorivo IMS — NIS i OMV | `/izvestaji/gorivo-ims/` | `fuel_transactions_list` |
| Kupljeni delovi — dobavljač | `/izvestaji/delovi-dobavljaca/` | `nabavka:euf_invoice_list` |

**Zajedničko pravilo bezbednosti [P]:** pri izvozu u Excel, tekst iz spoljnih izvora koji
počinje sa `=`, `+`, `-` ili `@` dobija apostrof ispred, da ga Excel **ne protumači kao
formulu**.

**Obuhvat po centrima** (`allowed_centers`) [P]:

> superuser → **prazan skup = bez ograničenja**
> ostali → unija `allowed_center_codes` (razdvojeno zarezom ili tačkom-zarezom)
> i `allowed_centers.center`

> **[P]** Ovo je **jedino** mesto u sistemu koje koristi **oba** mehanizma za centre.
> Vidi problem **P-19**.

---

### V-22.1 — Kasko i auto osiguranje

#### Postupak [P]

**Korak 1 — presek na datum.** Svi podaci se biraju **na izabrani datum preseka**
(`as_of`): dodela šifre posla, saobraćajna dozvola, osnov raspolaganja i važeći lizing.

**Korak 2 — obuhvat:** samo **trenutno neotpisana** vozila.

> **[P] Izričita napomena u izveštaju:** *„ovaj pregled ne rekonstruiše raniji status
> otpisa“* — otpis se gleda **danas**, ostalo na datum preseka.

**Korak 3 — vozilo nabavljeno posle datuma preseka se preskače**
(`purchase_date > as_of`).

**Korak 4 — određivanje vlasništva:**

> **vlasništvo IMS** ako je osnov `owned`
> **ili** ako **nema** evidentiranog osnova **i nema** važećeg lizinga/najma na taj dan

| Slučaj | Oznaka na izveštaju |
|---|---|
| Osnov je `owned` | „Evidentirano vlasništvo IMS“ |
| Nema osnova ni lizinga | **„Vlasništvo IMS — podrazumevano pravilo“** |
| Ostalo | „Korišćenje po ugovoru“ |

**Korak 5 — razlike između dva izveštaja:**

| | Auto osiguranje (IMS) | Kasko |
|---|---|---|
| Vozila po ugovoru | **Isključena** (broje se zasebno) | **Uključena** |
| Filter „vlasništvo“ | Postoji (`confirmed` / `all`) | **Ne postoji** |
| Uslov starosti | Nema | **`godina preseka − godište > 7`** |
| Nepoznato godište | Ulazi | **Isključeno** |

> **[P] Tačan uslov kaska:** *„Vozilo staro tačno 7 godina nije uključeno“* —
> uslov je `age > 7`, ne `>= 7`. Izričito napisano i u napomeni izveštaja.
> **Nema uslova visoke vrednosti** — svi osnovi raspolaganja ulaze.

**Pokazatelji [P]:** broj vozila u pregledu, broj sa podrazumevanim osnovom
(`assumed`), broj sa nepoznatim godištem.

#### Primer

> Datum preseka: 31.12.2026.

| Vozilo | Godište | Starost | Osnov | Kasko | Auto osiguranje IMS |
|---|---|---|---|---|---|
| A | 2015 | 11 | `owned` | **Da** | **Da** (evidentirano) |
| B | 2019 | **7** | `owned` | **Ne** (nije > 7) | **Da** |
| C | 2010 | 16 | `contract` (lizing) | **Da** | **Ne** (isključeno) |
| D | — | — | nema osnova, nema lizinga | **Ne** (nepoznato godište) | **Da** (podrazumevano) |

#### Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Vozilo bez evidentiranog osnova | **Pretpostavlja se vlasništvo IMS** — izričito označeno |
| Vozilo bez godišta | Broji se zasebno, izuzeto iz kaska |
| Vozilo nabavljeno posle preseka | Izostavljeno |
| Vozilo otpisano danas, a bilo aktivno na datum preseka | **Izostavljeno** — izričita napomena |

---

### V-22.2 — Gorivo IMS (NIS i OMV)

#### Postupak [P]

**Korak 1 — period:** `date_from` 00:00 do `date_to + 1 dan` 00:00 (isključivo).

**Korak 2 — istorijska šifra posla i centar:** prema dodeli važećoj **na dan transakcije**
(`TruncDate` datuma transakcije).

**Korak 3 — razvrstavanje proizvoda** (`fuel_kind`) [P]:

| Ako naziv sadrži | Vrsta |
|---|---|
| `adblue`, `ad blue` | **AdBlue** |
| `cng`, `ngv` | CNG |
| `lpg`, `tng`, `autogas` | TNG / LPG |
| `dizel`, `diesel`, `ed maxx`, `edmaxx` | Dizel |
| `benzin`, `petrol`, `bmb` | Benzin |
| bilo šta drugo | **Ostalo / nerazvrstano** |

> **[P] Redosled provere je bitan:** AdBlue se proverava **prvi**, pa proizvod
> „AdBlue dizel“ ne bi bio svrstan u dizel.

**Korak 4 — izbor vrste** (`fuel_type`) [P]:

| Izbor | Šta ulazi |
|---|---|
| **`fuel`** (podrazumevano) | Samo dizel, benzin, LPG i CNG — **bez AdBlue i bez „Ostalo“** |
| `all` | Sve |
| pojedinačna vrsta | Samo ta vrsta |

**Korak 5 — normalizacija valute** [P]: `DIN`, `DINAR` i `RSD` se svode na **`RSD`**;
prazna valuta postaje **„Nije uneta“**.

**Korak 6 — grupisanje** [P]. Šest načina: mesec, centar, šifra posla, proizvod,
mesec+centar, mesec+centar+šifra. Uz izabrane kolone, **proizvod i valuta ostaju uvek
odvojeni**:

> ključ grupe = izabrane kolone + vrsta goriva + **proizvod** + **valuta**

> **[P] Izričito objašnjenje iz koda:** *„Products and currencies always stay separate;
> quantities may use different source units.“* — količine različitih proizvoda se
> **ne sabiraju** u jedan pokazatelj.

**Korak 7 — zbirovi:** broj transakcija, zbir količine, zbir bruto iznosa i
**broj stavki bez iznosa** (`missing_amount`). Prazan iznos **nije nula** i broji se
posebno. [P]

**Iznos [P]:** NIS `total`, OMV `gross_cc` — **bruto terećenje posle popusta**.
Neto se u ovom izveštaju **ne računa**.

#### Prečišćavanje OMV transakcija [P]

OMV transakcije prolaze kroz **uklanjanje duplikata** iz V-06 — zastareli datumi fakture,
ponovljeni redovi iste transakcije i „odjeci“ računa. NIS transakcije se ne prečišćavaju,
jer za njih takav postupak ne postoji.

Primenjuje se `deduplicate_omv_transactions()`, a **ne** ceo `filter_omv_fuel_queryset()`.
Razlika je bitna: `filter_omv_fuel_queryset()` uz uklanjanje duplikata i **ograničava skup
samo na goriva**, pa bi opcije „AdBlue“, „ostalo“ i „sve“ u polju `fuel_type` prestale da
prikazuju bilo šta. Ovaj izveštaj sam razvrstava proizvode, pa mu treba samo prvi deo. [P]

> **Ispravljeno 18.09.2026.** — izveštaj je ranije čitao `TransactionOMV` **direktno**.
> U praksi obično nije smetalo, jer se `cleanup_omv_fuel_data(apply=True)` pokreće pri
> svakom uvozu (`fleet/sync/selenium.py:212`) i duplikate **fizički briše iz baze**.
> Smetalo bi kada uvoz prekine greška pre čišćenja ili kada se podaci unesu zaobilazeći
> redovan uvoz. Videti [P-26](../10-poznati-problemi.md).

#### Pokazatelji [P]

| Pokazatelj | Značenje |
|---|---|
| Transakcije | Broj stavki |
| Bruto · *valuta* | Zbir po svakoj valuti posebno |
| **Bez povezanog vozila** | Broj stavki kod kojih vozilo nije prepoznato |
| **Bez šifre posla** | Broj stavki bez istorijske dodele |
| **Bez iznosa** | Broj stavki sa praznim iznosom |

> **[P] Dobro rešeno:** za razliku od izveštaja goriva po šifri posla (V-21), koji
> transakcije bez vozila **tiho izostavlja**, ovaj izveštaj ih **uključuje i prebrojava**.

---

### V-22.3 — Kupljeni delovi po dobavljaču

#### Postupak [P]

**Izbor izvora** — dva odvojena, nikad zajedno:

| Izvor | Tabela | Identifikator dobavljača | Vrednost |
|---|---|---|---|
| `uf` (ulazne fakture) | `nabavka_euf_item_snapshot` | `partner_pib` | `value` |
| `goods` (roba) | `nabavka_goods_snapshot` | `partner_code` | `debit` |

> **[P] Izričito objašnjenje:** *„Izvori se biraju odvojeno da se faktura i robni promet
> ne saberu dvaput.“*

**Filteri:** dobavljač (obavezan — bez njega je spisak **prazan**), period po
`document_date`, deo naziva artikla.

**Automatski izbor dobavljača [P]:** ako korisnik nije izabrao dobavljača, sistem
pokušava da pronađe „AutoDeki“ — ali **samo ako postoji tačno jedno poklapanje**.
Ako ih je više ili nijedno, prikazuje se napomena:

> *„AutoDeki nije nedvosmisleno identifikovan u izvoru… prazan pregled ne znači da
> nije bilo kupovine.“*

**Napomene o obuhvatu [P]:**

> *„Kupovina dela ne potvrđuje ugradnju u vozilo.“*
> *„Storna i negativne stavke nisu uklonjeni.“*

---

## 6.5.5. Izveštaji nad nasleđenim pogledima

Jedanaest izveštaja koji se **ne računaju u aplikaciji** — cela formula je u pogledu
u bazi. Aplikacija samo izvršava `SELECT` i prikazuje rezultat. [P]

| Izveštaj | Adresa | Pogled | Kolone koje se čitaju |
|---|---|---|---|
| Kasko rate | `/izvestaji/kasko_rate/` | `dbo.kasko_rate` | `SELECT *` |
| Magacin | `/izvestaji/magacin/` | `dbo.fleet_magacin_rez` | `sif_pred, god, oj, sif_mag, sif_art, kolul, koliz, popkol, vrulnab, vriznab, vrulvp, vrizvp, revalzal, razliz, mag_cena, kolpon, cenapon, naz_art, sif_vrsart, naz_vrsart` |
| Otpis | `/izvestaji/otpis/` | `dbo.fleet_otpis` | 40 kolona osnovnih sredstava |
| Trošak goriva po mesecima | `/izvestaji/tro_gorivo_mesec/` | `dbo.fleet_tro_goriva_m` | `god, mesec, kategorija, iznos` |
| Svi troškovi | `/izvestaji/troskovi_svi/` | `dbo.fleet_tro_svi` | `god, sif_vrs, datum, br_naloga, stavka, oj, knt, naz_knt, duguje, sif_pos` |
| Troškovi praćenja vozila | `/izvestaji/tro_pracenja_vozila/` | `dbo.fleet_tro_pracenje` | `PartnerPIB, PartnerIme, ID, BrojFakture, issuedate, ZaPlacanje, Konto_tro` |
| Troškovi tahografa | `/izvestaji/troskovi_tahograf/` | `dbo.fleet_tro_taho` | `SELECT *` |
| Troškovi zarada | `/izvestaji/tro_zarade/` | `dbo.tro_zarade` | `oj, god, mesec, rasif, ranaz, neto, bruto, bruto2` |
| Troškovi parkinga | `/izvestaji/tro_parking/` | `dbo.fleet_tro_parking` | `PartnerPIB, PartnerIme, ID, BrojFakture, issuedate, note, naziv, ZaPlacanje` |
| Po dobavljačima | `/izvestaji/po_dobavljacima/` | `dbo.fleet_dobavljaci` | 24 kolone knjiženja |

*(Deseti i jedanaesti izveštaj — `kasko_rate` se pojavljuje i kao Django model
`KaskoRate` sa `managed = False`.)*

### Zajednički postupak [P]

| Element | Vrednost |
|---|---|
| Fajl sa upitima | [`fleet/support/report_queries.py`](../../../fleet/support/report_queries.py) |
| Izvršavanje | `fleet/support/report_helpers.py: get_data_from_secondary_db()` |
| Konekcija | **`server_db`** |
| Filteri | Dodaju se kao `WHERE` uslovi preko `report_period_filtered_query()` i `date_period_filtered_query()` |
| Ekrani | `fleet/views/reports.py` |

### Problem P-27 — formula je izvan projekta

> **[P]** Za ovih 11 izveštaja **u repozitorijumu ne postoji nijedan podatak o tome
> kako se iznosi računaju**. Poznata su samo imena kolona koje aplikacija čita.

**Posledice [Z]:**

1. Ne može se odgovoriti na pitanje **„odakle ovaj iznos“** bez pristupa bazi.
2. Promena pogleda u bazi menja rezultat na ekranu **bez ijedne izmene u aplikaciji**
   i bez traga u istoriji verzija.
3. Dokumentacija ovih izveštaja **ne može biti završena** dok se ne dobiju definicije.

**Status [P]:** definicije (DDL) su zatražene i očekuju se.
Do tada su ovi izveštaji dokumentovani **samo do nivoa naziva kolona**.

### Šta se ipak može reći o sadržaju [Z]

Na osnovu naziva kolona, uz napomenu da je **zaključeno, ne potvrđeno**:

| Pogled | Verovatan sadržaj |
|---|---|
| `fleet_tro_svi` | Knjiženja troškova vozila po nalogu, kontu i šifri posla (`duguje`) |
| `fleet_tro_goriva_m` | Zbir troška goriva po godini, mesecu i kategoriji |
| `fleet_tro_pracenje` | Fakture za GPS praćenje vozila (`ZaPlacanje`) |
| `fleet_tro_taho` | Fakture za tahografe |
| `fleet_tro_parking` | Fakture za parking, sa nazivom i napomenom |
| `tro_zarade` | Zarade po OJ i mesecu: neto, bruto, bruto 2 |
| `fleet_dobavljaci` | Knjiženja po dobavljačima — ista struktura kao `nalog_z` |
| `fleet_magacin_rez` | Stanje i promet magacina: ulaz, izlaz, nabavne i veleprodajne vrednosti |
| `fleet_otpis` | Osnovna sredstva: nabavna vrednost, osnovica, otpis, amortizacione stope |

> **Ne oslanjati se na ovu tabelu za poslovne odluke** dok se ne dobiju definicije pogleda.

---

## Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-26** | ~~Izveštaj „Gorivo IMS“ za upravu čita OMV transakcije **bez prečišćavanja duplikata pri čitanju**.~~ **Rešeno 18.09.2026.** | Srednja |
| **P-46** | Ključ za prepoznavanje duplikata OMV transakcija **ne podnosi prazna polja**, pa zapis bez vaučera ili količine tiho nestaje sa **svih** ekrana goriva. Otkriveno pri rešavanju P-26. **Rešeno 18.09.2026.** | **Visoka** |
| **P-47** | Isti ključ **ne obuhvata iznos ni valutu**, pa se dva zapisa koja se razlikuju samo po iznosu spajaju u jedan. Nije potvrđeno da takvi parovi postoje u stvarnim podacima. | Srednja |
| **P-27** | Za 11 izveštaja nad nasleđenim pogledima **formula nije poznata** — nalazi se isključivo u bazi. Rezultat se može promeniti bez ijedne izmene u aplikaciji. | Srednja |

## Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q23** | Vozilo ima polje „Servisni interval (km)“ sa podrazumevanih 15.000, ali se **nigde ne koristi**. Da li je predviđeno upozorenje o dospelom servisu (kilometraža od poslednjeg servisa ≥ interval)? |
| **Q24** | Izveštaj za upravu prepoznaje AO polisu po **sadržaju** naziva tipa, a mesečni troškovi polisa po **tačnoj vrednosti**. Da li tipove osiguranja treba svesti na šifarnik umesto slobodnog teksta? |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.2. Flota — gorivo](06-02-flota-gorivo.md) | Obračuni goriva |
| [6.3. Flota — troškovi](06-03-flota-troskovi.md) | Trošak po kilometru |
| [6.4. Flota — polise i lizing](06-04-flota-ugovori-polise.md) | Mesečni troškovi |
| [4. Baza podataka](../04-baza-podataka.md#412-nasleđeni-objekti-baze-dbo) | Nasleđeni pogledi |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema |
