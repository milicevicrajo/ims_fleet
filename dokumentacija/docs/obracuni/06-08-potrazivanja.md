# 6.8. Potraživanja — obračuni

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](../10-poznati-problemi.md).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [PT-01](#pt-01--starosni-razredi-baketi) | Starosni razredi (baketi) | **P-35** |
| [PT-02](#pt-02--saldo-stavke) | Saldo stavke | — |
| [PT-03](#pt-03--objavljivanje-snimka-stanja) | Objavljivanje snimka stanja | — |
| [PT-04](#pt-04--kontrolni-zbirovi-i-provera-izvora) | **Kontrolni zbirovi i provera izvora** | — |
| [PT-05](#pt-05--saldo-po-šiframa-posla) | Saldo po šiframa posla | — |
| [PT-06](#pt-06--normalizacija-nasleđenih-kontakata) | Normalizacija nasleđenih kontakata | — |

> **Oznake su `PT-`, a ne `P-`**, jer je prefiks `P-` rezervisan za registar problema.

---

## Zajednička osnova: zašto Potraživanja postoje

Nasleđena Naplata čita **direktno nasleđene poglede** pri svakom otvaranju ekrana —
sporo i bez ikakve istorije. Potraživanja umesto toga:

1. **Preuzimaju ceo izvor** u lokalne Django tabele.
2. **Proveravaju** da li se preneto poklapa sa izvorom — kroz šest kontrola.
3. **Objavljuju snimak stanja** na određeni datum.
4. Svi ekrani zatim čitaju **objavljeni snimak**, ne izvor.

```
 dbo pogledi (partneri, baza, ispravke, dodela_baketa, posao)
            │  puno preuzimanje, jedan zaključan prolaz
            ▼
  nepromenljiv snimak izvora (SourceDataset + SourceRow)
            │
            ├──► FinancePartnerIdentity   (partneri)
            ├──► ReceivablePosting        (knjiženja)
            ├──► InvoiceDocument          (fakture IF)
            │
            ▼
   ŠEST KONTROLA  ──── razlika ──► NIŠTA SE NE OBJAVLJUJE
            │
            ▼
  BalanceSnapshot (objavljen) + ReceivablePosition
            │
            ▼
  CollectionState.current_snapshot  ──► svi ekrani i Finansije
```

> **[P] Načelo iz koda:** *„Full, serialized and atomic publication of the legacy
> collections contract.“* — ceo prenos je **jedna transakcija**; ili prođe sve, ili ništa.

### Zaključavanje [P]

| Baza | Mehanizam |
|---|---|
| SQL Server | `sp_getapplock` na resursu `potrazivanja.full.sync`, vezan za **sesiju** |
| SQLite (testovi) | Zaključavanje u procesu |
| Bilo šta drugo | **Odbija se** — *„Sinhronizacija zahteva SQL Server.“* |

Prethodno pokretanje koje je ostalo u statusu „U toku“, a zaključavanje je slobodno,
automatski se označava kao **neuspešno**. [P]

---

## PT-01 — Starosni razredi (baketi)

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Baket“, „Starosna struktura“, „Nedospelo“, „Dospelo 30/45/60/90/180/181+“ |
| Tehnički naziv | `bucket()` |
| Putanja | [`potrazivanja/services/sync.py:76`](../../../potrazivanja/services/sync.py#L76) |

### 2. Poslovna svrha

Razvrstava svako potraživanje po **starosti duga** — koliko je dana prošlo od dospeća —
da bi služba naplate znala **čime prvo da se bavi** i koji su dugovi najrizičniji.

### 3. Korisnici rezultata

Služba naplate, pravna služba, finansije, uprava.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | Obavezno |
|---|---|---|---|---|
| Datum dospeća | Dospeće | `potrazivanja_receivableposition.due_date` | datum | **Ne** |
| Datum snimka | Stanje na dan | `potrazivanja_balancesnapshot.as_of_date` | datum | Da |

#### Odakle dolazi datum dospeća [P]

Dospeće se **ne računa u aplikaciji** — preuzima se iz pogleda `dodela_baketa`, koji ga
sastavlja iz dva skupa:

| Skup | Sadržaj |
|---|---|
| `dupli` | Sve iz `v_duplikati` |
| `bez_duplih` | Iz `v_if`, **samo ono čega nema u `v_duplikati`**, sa **`MIN(dpo)`** |

Skupovi se spajaju `UNION ALL` i tek onda **`LEFT OUTER JOIN`**-uju na `baza`.

> **[P] Posledica `LEFT OUTER JOIN`-a:** stavka koja **ne nađe par** dobija `dpo = NULL` →
> razred **`0.1`**. Nepoznato dospeće tako nastaje i kada dokument postoji, ali mu se par
> ne pronađe.

Raniji opis pravila kaže da se za partnera/vezu koja postoji **u više godina** bira
**`MAX`** dospeća, a za ostale **`MIN`** iz `v_if`. **`MAX` se u preuzetom DDL-u ne vidi**
— vidi napomenu o sumnjivoj definiciji `v_duplikati` u
[3.5 §17](../moduli/03-05-potrazivanja.md). [N]

> **[P] Dospeća se ne sužavaju na ista dva konta kao saldo.** `baza` filtrira `20400%` i
> `20500%`, ali `v_if` **nema filter po kontu** (`sif_vrs='IF'`, `sif_par > 0`,
> `god >= 2025`). To je namerno — dokazi dospeća dolaze iz svih IF stavki.

### 6. Tačan postupak obračuna

```
 dospeće nije poznato   ILI   dospeće >= datum snimka   ──►  razred "0.1"
 inače:
     dana = datum snimka − dospeće
     dana <= 30   ──►  razred "30"
     dana <= 45   ──►  razred "45"
     dana <= 60   ──►  razred "60"
     dana <= 90   ──►  razred "90"
     dana <= 180  ──►  razred "180"
     inače        ──►  razred "181"
```

**Sedam razreda [P]:**

| Razred | Značenje | Dana od dospeća |
|---|---|---|
| **`0.1`** | **Nedospelo** *(i nepoznato dospeće)* | dospeće u budućnosti ili nepoznato |
| `30` | Dospelo — baket 1 | 1–30 |
| `45` | Dospelo — baket 2 | 31–45 |
| `60` | Dospelo — baket 3 | 46–60 |
| `90` | Dospelo — baket 4 | 61–90 |
| `180` | Dospelo — baket 5 | 91–180 |
| `181` | Dospelo — baket 6 | **preko 180** |

> **[P] Razred `0.1` objedinjuje dva različita slučaja:** potraživanje koje **još nije
> dospelo** i potraživanje **kome se ne zna datum dospeća**. U kodu je to izričito
> zabeleženo kao namerno preuzimanje nasleđenog pravila:
> *„Deliberately preserves legacy unknown-date bucket.“*
>
> Sistem ipak **broji** stavke bez dospeća (`unknown_due_count`) i uz svaku poziciju
> beleži oznaku `unknown_due`. Vidi problem **P-35**.

**Granice su „uključivo“ [P]:** dug star tačno 30 dana pripada razredu `30`,
a star 31 dan razredu `45`.

**Provera prema izvoru [P]:** pri objavljivanju snimka sistem **za svaku stavku** poredi
sopstveni izračunat razred sa razredom iz izvora (`dodela_baketa.baket`). Razlika
prekida ceo prenos: *„Baket izvora ne odgovara datumu snimka.“*

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `potrazivanja/services/sync.py` |
| Funkcija | `bucket(due, as_of)` |
| Koristi je | `publish_positions()`, `job_balances()` (PT-05) |
| Bojenje na ekranu | `potrazivanja/services/reports.py:12-13` — pet nivoa crvene |

### 8. Primer obračuna

> Datum snimka: **18.09.2026.**

| Faktura | Dospeće | Dana | Razred | Prikaz |
|---|---|---|---|---|
| IF-100 | 30.09.2026. | — | **`0.1`** | Nedospelo |
| IF-101 | 18.09.2026. | 0 | **`0.1`** | Nedospelo *(dospeva danas)* |
| IF-102 | 25.08.2026. | 24 | **`30`** | Dospelo — baket 1 |
| IF-103 | 19.08.2026. | 30 | **`30`** | Dospelo — baket 1 |
| IF-104 | 18.08.2026. | 31 | **`45`** | Dospelo — baket 2 |
| IF-105 | 20.03.2026. | 182 | **`181`** | Dospelo — baket 6 |
| IF-106 | **nepoznato** | — | **`0.1`** | **Nedospelo** — iako možda jeste dospelo |

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Starosni razred jednog potraživanja na datum snimka |
| Gde se čuva | U `resolution_details` pozicije, kao `bucket` |
| Kada se ponovo računa | **Pri svakom novom snimku** — razred se menja kako dug stari |
| Može li korisnik da ga izmeni | Ne |

### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Kontrolna tabla Potraživanja | Starosna struktura po partnerima |
| Saldo po šiframa posla (PT-05) | Sedam kolona po razredima |
| Finansijska analitika | Tab „Potraživanja“ na detalju šifre posla |
| Opomene i pravni postupci | Osnov za odluku o daljem postupku |

### 11. Kontrola i ručna provera

**Kontrolna formula:**

> dana = datum snimka − datum dospeća, pa se uporedi sa granicama 30/45/60/90/180

| Provera | Kako |
|---|---|
| Razred deluje pogrešno | Proveriti **datum snimka** — nije današnji dan, nego dan preuzimanja |
| Dug u „Nedospelo“, a star je | Verovatno **nema datuma dospeća** — proveriti `unknown_due` |
| Razlika prema Naplati | Snimci su iz različitih trenutaka |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Nepoznato dospeće** | Svrstava se u **„Nedospelo“** | **P-35** |
| **Isti red je i „dospeo“ i „nedospeo“** | Vidi niže | **P-35** |
| Dospeće u budućnosti | Nedospelo | Ispravno |
| Razred izvora ne odgovara | **Ceo prenos se prekida** | Ispravno |
| Snimak star nekoliko dana | Razredi su **na dan snimka**, ne na danas | Vidljivo — datum je prikazan |

#### Nesaglasnost `baket` i `kategorija` kod praznog dospeća [P]

Pogled `dodela_baketa` računa **dve** oznake, i one se **ne slažu** kada dospeće nedostaje:

```sql
CASE WHEN DATEDIFF(DAY, dpo, GETDATE()) <= 0 THEN 0 ELSE 1 END AS kategorija
```

Sa `dpo = NULL` poređenje je `UNKNOWN`, pa red pada u `ELSE` → **`kategorija = 1`
(dospelo)**. Istovremeno `baket` ide u **`0.1` (nedospelo)**.

> **Ista stavka je „dospela“ po jednoj koloni i „nedospela“ po drugoj.** [P]

Aplikacija **čuva obe vrednosti** i beleži da je dospeće nepoznato:

```python
resolution_details = {"bucket": ..., "category": integer(row.get("kategorija")),
                      "unknown_due": due is None}
```

> To je konkretan dokaz uz [P-35](../10-poznati-problemi.md#p-35--nepoznato-dospeće-prikazuje-se-kao-nedospelo):
> nesaglasnost postoji **na izvoru**, ne u Django kodu.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Sedam razreda i njihove granice | Potvrđeno | `sync.py:76-83` | — |
| Granice su uključive | Potvrđeno | `sync.py:81` | — |
| **Nepoznato dospeće ide u „Nedospelo“** | **Potvrđeno — namerno preuzeto iz nasleđenog** | `sync.py:78` | **P-35** |
| Razred se proverava prema izvoru | Potvrđeno | `sync.py:276-277` | — |
| Broj stavki bez dospeća se beleži | Potvrđeno | `sync.py:315` | — |

---

## PT-02 — Saldo stavke

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Saldo“ |
| Tehnički naziv | `ReceivablePosition.balance` |
| Putanja | [`potrazivanja/models.py:260`](../../../potrazivanja/models.py#L260) |

### 2. Poslovna svrha

Koliko partner **stvarno duguje** po jednom dokumentu, posle svih uplata i ispravki.

### 6. Tačan postupak obračuna

> **saldo = duguje − potražuje**

**Tri nezavisne provere iste formule [P]:**

| # | Gde | Šta proverava |
|---|---|---|
| 1 | Pri čitanju izvora | `saldo` iz `dodela_baketa` mora biti jednak `duguje − potražuje` |
| 2 | Posle upisa pozicija | Par (`duguje`, `potražuje`) mora ostati nepromenjen |
| 3 | **U samoj bazi** | `CheckConstraint`: `balance = ROUND(debit − credit, 2)` |

> **[P] Treća provera je u bazi**, pa je **nemoguće** upisati poziciju sa netačnim saldom
> — ni kroz aplikaciju, ni ručnim upisom.

**Zaokruživanje [P]:** na **2 decimale**, kako nalaže `CheckConstraint`.

**Grupisanje pozicije [P]:** jedna pozicija je jedinstvena po:

> (snimak, partner, veza dokumenta, šifra posla, grupa konta)

**Grupa konta** (`account_family`) je **tri znaka** [P]:

| Izvor | Kako se dobija |
|---|---|
| `dodela_baketa` | `204` ako je `ino = 0`, inače `205` |
| `baza` (kontrola) | prva **tri znaka** konta (`knt[:3]`) |

> **[Z]** `204` su domaći kupci, `205` inostrani — kontrola upravo poredi da li se te
> dve podele poklapaju.

### 8. Primer

| Dokument | Duguje | Potražuje | Saldo |
|---|---|---|---|
| IF-100 | 120.000,00 | 0,00 | **120.000,00** |
| IF-101 | 80.000,00 | 80.000,00 | **0,00** |
| IF-102 | 50.000,00 | 65.000,00 | **−15.000,00** — pretplata |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Saldo izvora ≠ duguje − potražuje | **Ceo prenos se prekida** |
| Negativan saldo | **Zadržava se** — ne pretvara se u nulu i ne uklanja kao greška |
| **Saldo tačno nula** | Pogled ima `HAVING SUM(dug) - SUM(pot) <> 0` — **zatvorena pozicija se uopšte ne pojavljuje** kao otvorena stavka. Njeni dokumenti i aktivnosti ostaju |
| Dva reda za isti ključ pozicije | **Prekida se** — *„potrebno razrešiti izvor, bez tihog spajanja“* |
| Devizni iznosi | **Ne sabiraju se** preko valuta — iznos i valuta se čuvaju odvojeno |

> **[P] „Domaći / inostrani“ je podela po kontu, ne po valuti.** Pogled računa
> `CASE WHEN LEFT(knt,3) = N'204' THEN 0 ELSE 1 END AS ino`. Stavka na kontu `205` vodi se
> kao inostrana **bez obzira na valutu knjiženja**, i obrnuto.

> **[P] „Potražuje“ nije dokazano „naplaćeno“.** U izvornom prikazu `potražuje` može
> sadržati i **preknjiženja i druga zatvaranja**, ne samo bankarske uplate. Bez potvrđenih
> vrsta knjiženja i povezivanja **taj zbir se ne sme zvati „naplaćeno“**.

> **[P] Isti broj dokumenta može se ponoviti u različitim godinama.** `POC`/uplata sa
> `vez_dok` **nije automatski dokument godine knjiženja**. Nejasne veze ostaju
> nerazrešene — bez izmišljene raspodele.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Saldo = duguje − potražuje | Potvrđeno | `models.py:268`, `sync.py:279-280` |
| Kontrola u bazi, ne samo u kodu | Potvrđeno | `models.py:268` |
| Tri nezavisne provere | Potvrđeno | `sync.py:279, 300, models.py:268` |
| Duplikat ključa prekida prenos | Potvrđeno | `sync.py:272-273` |

---

## PT-03 — Objavljivanje snimka stanja

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Stanje na dan“, „Sinhronizacija“ |
| Tehnički naziv | `publish_positions()`, `sync_collections()` |
| Putanja | [`potrazivanja/services/sync.py:260`](../../../potrazivanja/services/sync.py#L260) |
| Adresa | `/potrazivanja/sinhronizacija/` |

### 2. Poslovna svrha

Umesto da svaki ekran čita izvor u svom trenutku, sistem pravi **jedan snimak stanja**
na tačno određeni datum, proveri ga i **objavi**. Svi ekrani zatim vide **istu sliku**.

### 6. Tačan postupak

**Korak 1 — preuzimanje** [P]: čitav izvor se čita odjednom, uz zabeležen **trenutak
posmatranja** (`observed`). Datum snimka je datum tog trenutka.

**Korak 2 — provera osnovnog obuhvata** [P]:

> ako su `partneri` **ili** `baza` prazni →
> *„Prazan osnovni izvor; postojeći podaci ostaju objavljeni.“*

Prazan izvor **ne može** obrisati postojeće stanje.

**Korak 3 — šifarnik centara** [P]: iz `posao` se pravi mapa šifra → centar.
Duplirana ili prazna šifra prekida prenos.

**Korak 4 — arhiviranje izvora** [P]: svaki skup se čuva kao **nepromenljiv snimak**
(`SourceDataset`), sa otiskom sadržaja:

| Situacija | Postupak |
|---|---|
| Isti otisak već postoji | Snimak se **ponovo koristi**, ne dupliraju se redovi |
| Novi otisak | Upisuju se svi redovi, pa se **pročitaju nazad** i otisak ponovo izračuna |

> **[P] Provera upisa:** posle upisa se čita nazad i poredi otisak.
> *„Kontrola kompletnog sadržaja izvora … nije prošla.“* prekida prenos.

**Korak 5 — partneri** [P]: obuhvat je **firma 1, grupa 1**.

| Situacija | Postupak |
|---|---|
| Nov partner | Upisuje se |
| Promenjen (drugi otisak) | Ažurira se |
| Nestao iz šifarnika | **`active = False`** — ne briše se |
| **Partner postoji u finansijskim podacima, a nema ga u šifarniku** | Upisuje se kao **neaktivan**, uz zabeležen problem `missing_partner` |

> **[P] Načelo iz koda:** *„Preserve the confirmed company/group from baza; do not guess
> the identity of orphan operational data.“*

**Korak 6 — knjiženja i fakture** [P]:

Izvorni ključ knjiženja: **(godina, vrsta naloga, broj naloga, stavka)**.
Duplikat ili nepotpun ključ prekida prenos. Knjiženje bez datuma knjiženja takođe.

**Faktura (IF dokument)** se pravi grupisanjem knjiženja po:

> (godina, broj naloga, partner, veza dokumenta) — **samo za vrstu `IF` iz `baza`**

| Polje fakture | Kako se dobija |
|---|---|
| Datum dokumenta | **Najraniji** među stavkama |
| Datum dospeća | **Najraniji** među stavkama |
| **Iznos** | **Zbir (duguje − potražuje)** svih stavki |

> **[P] Izričito upozorenje iz koda:** *„v_if.saldo is deliberately NOT used as invoice
> amount.“* — iznos fakture se **ne preuzima** iz nasleđenog pogleda, nego se računa iz
> stavki knjiženja.

**Korak 7 — pozicije** [P]: prave se iz `dodela_baketa`, uz proveru razreda i salda
(vidi PT-01 i PT-02).

**Korak 8 — kontrole** [P]: šest kontrola (vidi PT-04). Svaka razlika prekida prenos.

**Korak 9 — objava** [P]:

```
 snimak: status = "published", published_at = sada
 CollectionState.current_snapshot = ovaj snimak
```

> **[P] Kontrola u bazi:** `CollectionState` ne dozvoljava da aktivno stanje bude
> snimak koji **nije objavljen** ili pripada **drugoj firmi**.

**Sve u jednoj transakciji [P]:** koraci 4–9 su u `transaction.atomic()`.
Greška bilo gde znači da **ništa** nije upisano, a prethodni snimak ostaje objavljen.

### 8. Primer

| Korak | Ishod |
|---|---|
| Preuzeto | partneri 1.240, baza 18.500, ispravke 320, dodela_baketa 4.100, posao 860 |
| Arhivirano | 5 snimaka izvora; 2 ponovo iskorišćena (isti sadržaj) |
| Partneri | 12 novih, 35 ažuriranih, 4 neaktivna, **2 problema `missing_partner`** |
| Knjiženja | 480 novih, 210 ažuriranih, 15 neaktivnih |
| Fakture | 96 novih dokumenata |
| Pozicije | 4.100 |
| Kontrole | 6 kontrola, **0 razlika** |
| **Objavljeno** | Snimak na dan **18.09.2026.** |

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Proveren snimak stanja potraživanja na određeni datum |
| Gde se čuva | `potrazivanja_balancesnapshot` + `potrazivanja_receivableposition` |
| Kada se ponovo računa | Pri svakoj sinhronizaciji — **novi snimak, stari ostaje** |
| Može li korisnik da ga izmeni | Ne |
| **Istorija** | **Potpuna** — svi raniji snimci ostaju |
| Audit trag | `CollectionSyncRun`, `CollectionSyncStep`, `ImportIssue` |

> **[P] Prednost nad nasleđenom Naplatom:** moguće je pogledati stanje **kako je izgledalo
> na raniji datum**, što Naplata ne omogućava.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Prazan osnovni izvor | Prenos se prekida, staro stanje ostaje objavljeno |
| Bilo koja kontrola ne prođe | **Ništa se ne upisuje**, staro stanje ostaje |
| Dva istovremena pokretanja | Drugo se preskače |
| Prekinut prethodni prolaz | Automatski se označava kao neuspešan |
| Partner nestao iz šifarnika | Označava se neaktivnim, ne briše |
| Knjiženje nestalo iz izvora | `active = False`, uz napomenu *„Van tekućeg obuhvata view-a; nije dokaz brisanja iz ERP-a.“* |
| Ponovni uvoz nasleđenih operativnih podataka posle osamostaljenja | **Odbija se** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Ceo prenos je jedna transakcija | Potvrđeno | `sync.py:350-362` |
| Prazan izvor ne briše podatke | Potvrđeno | `sync.py:338-339` |
| Iznos fakture se računa iz stavki, ne iz `v_if.saldo` | Potvrđeno | `sync.py:203-215` |
| Nestali zapisi se označavaju, ne brišu | Potvrđeno | `sync.py:143-146, 196-198` |
| Objavljen snimak postaje aktivno stanje | Potvrđeno | `sync.py:317-320` |
| Kontrola aktivnog stanja u bazi | Potvrđeno | `models.py:244-247` |

---

## PT-04 — Kontrolni zbirovi i provera izvora

> **Ovo je najvažnija zaštita modula.** Bez nje bi tiha greška u prenosu ostala neprimećena.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kontrolni zbirovi“ u istoriji sinhronizacije |
| Tehnički naziv | `compare_maps()`, `validate_postings()` |
| Putanja | [`potrazivanja/services/sync.py:232`](../../../potrazivanja/services/sync.py#L232) |

### 2. Poslovna svrha

Dokazuje da je **sve što je preneto jednako onome što je u izvoru** — pre nego što se
podaci objave i pre nego što ih iko vidi.

### 6. Šest kontrola [P]

| # | Naziv | Šta poredi | Poruka pri razlici |
|---|---|---|---|
| 1 | **knjiženja → otvorene pozicije** | Zbir `duguje − potražuje` iz `baza` po ključu pozicije naspram salda iz `dodela_baketa` | *„Kontrola knjiženja → otvorene pozicije: N razlika. Snimak nije objavljen.“* |
| 2 | **pozicije** | Očekivani saldo naspram **stvarno upisanog** u bazi | *„Kontrola pozicije: N razlika.“* |
| 3 | **partner/posao/baket** | Zbirovi grupisani po partneru, šifri posla, grupi konta i razredu | *„Kontrola partner/posao/baket: N razlika.“* |
| 4 | **dospeća** | Datum dospeća posle upisa naspram izvora | *„Razlika u datumima dospeća posle prenosa.“* |
| 5 | **duguje/potražuje** | Par iznosa posle upisa naspram izvora | *„Razlika duguje/potražuje nakon prenosa pozicija.“* |
| 6 | **knjiženja** | **Osam polja svakog knjiženja** naspram izvora | *„Kontrola prenetih knjiženja: N razlika.“* |

**Kontrola 6 poredi po knjiženju [P]:** partner, konto, šifra posla, veza dokumenta,
datum knjiženja, datum dospeća, duguje i potražuje — za **svako** aktivno knjiženje.

### Još dve kontrole: da se izvor nije promenio tokom čitanja [P]

| # | Naziv | Šta radi | Poruka |
|---|---|---|---|
| 7 | **Ponovno čitanje** | Posle čitanja svih izvora, `baza`, `ispravke` i `dodela_baketa` se **čitaju ponovo** i porede po otisku (`fingerprint`) | *„Izvor {naziv} se promenio tokom čitanja. Ponovite sinhronizaciju.“* |
| 8 | **Datum izvora** | Ponovo se uzima `GETDATE()` i poredi sa prvim | *„Datum izvora promenjen tokom čitanja; ponovite sinhronizaciju.“* |

> **[P]** Otisak **namerno izostavlja kolonu `danasnji_datum`** — ona je metapodatak
> snimanja, a ne sadržaj. Bez toga bi se svako čitanje razlikovalo.

Ove dve kontrole rešavaju ono što kontrolni zbirovi sami ne mogu: izvor se čita **bez
`NOLOCK`**, ali u više upita, pa promena između njih ne bi bila vidljiva.

### Ključ poređenja i nasleđeno upoređivanje teksta [P]

Ključ pozicije je:

> (šifra partnera, **fold**(veza dokumenta), **fold**(šifra posla), grupa konta)

Funkcija `fold()` oponaša nasleđeno SQL upoređivanje `Latin1_General_CI_AI`:

| Postupak | Primer |
|---|---|
| Uklanja **prateće razmake** | `"IF-100  "` → `"if-100"` |
| Svodi na **mala slova** | `"IF-100"` → `"if-100"` |
| Uklanja **dijakritike** | `"Čačak"` → `"cacak"` |

> **[P] Zašto je to neophodno:** nasleđena baza koristi upoređivanje neosetljivo na
> velika slova, dijakritike i prateće razmake. Bez `fold()` bi `"IF-100"` i `"if-100 "`
> bili različiti ključevi, pa bi kontrola prijavila lažne razlike.

### Zbirni pokazatelji snimka [P]

Uz kontrole se u snimak upisuju i:

| Pokazatelj | Značenje |
|---|---|
| `positions` | Broj pozicija |
| `partners` | Broj različitih partnera |
| `balance` | **Ukupan saldo** |
| `debit`, `credit` | Ukupno duguje i potražuje |
| **`unknown_due_count`** | **Broj pozicija bez datuma dospeća** |

### 8. Primer

> Sinhronizacija koja **ne prolazi**.

| Kontrola | Grupa | Očekivano | Stvarno |
|---|---|---|---|
| knjiženja → pozicije | partner 1234, IF-100, posao 413111, 204 | 120.000,00 | **118.000,00** |

Ishod: `ValueError: Kontrola knjiženja → otvorene pozicije: 1 razlika. Snimak nije objavljen.`

| Posledica | |
|---|---|
| Transakcija | **Poništena** — ništa nije upisano |
| Prethodni snimak | **Ostaje objavljen** |
| Prolaz | Status **„Neuspešno“**, sa punim tekstom greške |
| Korisnik | Vidi grešku na ekranu sinhronizacije |

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `BalanceSnapshot.totals` i `CollectionSyncRun.control_totals` (JSON) |
| Upotreba | Dokaz ispravnosti snimka; osnov za poređenje sa Naplatom pri prelasku |
| Kontrola | Broj razlika mora biti **0** u svih šest kontrola |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Bilo koja razlika | **Snimak se ne objavljuje** |
| Razlika u zapisu teksta (velika slova, razmaci) | **Ne stvara lažnu razliku** — `fold()` |
| Partner u finansijskim podacima bez šifarnika | Zabeležen kao problem, **ne prekida** prenos |
| Stavke bez dospeća | Prebrojane, **ne prekidaju** prenos |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Šest kontrola pre objave | Potvrđeno | `sync.py:289, 304-310` |
| Svaka razlika prekida objavu | Potvrđeno | `sync.py:255-256, 243-244` |
| `fold()` oponaša `Latin1_General_CI_AI` | Potvrđeno | `sync.py:70-73` |
| Kontrola knjiženja poredi osam polja | Potvrđeno | `sync.py:236-241` |
| Kontrolni zbirovi se čuvaju uz snimak | Potvrđeno | `sync.py:311-316` |

---

## PT-05 — Saldo po šiframa posla

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Tab „Potraživanja“ na detalju šifre posla |
| Tehnički naziv | `job_balances()` |
| Putanja | [`potrazivanja/services/reports.py:16`](../../../potrazivanja/services/reports.py#L16) |

### 2. Poslovna svrha

Pokazuje **koliko kupci duguju po jednoj šifri posla**, razvrstano po starosnim razredima —
da rukovodilac posla vidi **koliko duga stoji i koliko je star**.

> **[P] Ovo nije „koliko je naplaćeno“.** Saldo je `duguje − potražuje`, a `potražuje` u
> izvoru može sadržati i preknjiženja i druga zatvaranja, ne samo uplate — vidi
> [PT-02 §12](#12-izuzeci-i-rizični-slučajevi). Iznos naplaćen po pojedinačnoj fakturi
> **sistem ne zna**.

### 3. Korisnici rezultata

Rukovodioci poslova i centara, finansije, uprava — kroz Finansijsku analitiku.

### 6. Tačan postupak

**Korak 1 — provera prava** [P]: *„Šifra posla nije dostupna u Potraživanjima.“*
ako korisnik nema pristup toj šifri.

**Korak 2 — aktivno stanje** [P]: uzima se `CollectionState.current_snapshot`.
Ako ga nema ili nije objavljen → **prazan rezultat**, ne greška.

**Korak 3 — pozicije** [P]: pozicije snimka za tu šifru posla, dodatno ograničene
pravima korisnika (`scoped`).

**Korak 4 — grupisanje:**

> grupa = (partner, grupa konta)

**Korak 5 — devet iznosa po grupi [P]:**

| # | Kolona | Sadržaj |
|---|---|---|
| 1 | Nedospelo | razred `0.1` |
| 2 | Dospelo — baket 1 | razred `30` |
| 3 | Dospelo — baket 2 | razred `45` |
| 4 | Dospelo — baket 3 | razred `60` |
| 5 | Dospelo — baket 4 | razred `90` |
| 6 | Dospelo — baket 5 | razred `180` |
| 7 | Dospelo — baket 6 | razred `181` |
| 8 | **Dospelo ukupno** | **zbir kolona 2–7** |
| 9 | **Ukupno** | **zbir kolona 1–7** |

**Sortiranje:** po šifri partnera, pa po grupi konta. [P]

**Bojenje [P]:** pet nivoa crvene, po razredu:

| Razred | `0.1` | `30` | `45` | `60` | `90` | `180` | `181` | Dospelo | Ukupno |
|---|---|---|---|---|---|---|---|---|---|
| Nivo | 1 | 2 | 2 | 3 | 3 | 4 | **5** | 4 | 3 |

### 8. Primer

> Šifra posla **413111**, snimak na **18.09.2026.**

| Partner | Grupa | Nedospelo | 30 | 45 | 60 | 90 | 180 | 181+ | **Dospelo** | **Ukupno** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1234 Kupac A | 204 | 200.000 | 50.000 | 0 | 0 | 0 | 0 | 0 | **50.000** | **250.000** |
| 5678 Kupac B | 204 | 0 | 0 | 0 | 0 | 0 | 0 | 480.000 | **480.000** | **480.000** |
| 9012 Kupac C | 205 | 120.000 | 0 | 0 | 30.000 | 0 | 0 | 0 | **30.000** | **150.000** |

> Kupac B ima ceo dug stariji od 180 dana — najviši nivo bojenja.
> Kupac C je inostrani (grupa 205).

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde — računa se iz objavljenog snimka |
| Datum stanja | **Uvek se prikazuje** uz tabelu |
| Upotreba | Detalj šifre posla u Finansijama; veza partnera vodi u Potraživanja |
| Kontrola | Zbir svih partnera po šifri mora odgovarati zbiru pozicija te šifre u snimku |

> **[P]** Finansijska analitika **ne čita** nasleđene poglede Naplate — koristi
> isključivo objavljeni snimak Potraživanja i njegova prava pristupa.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Nema objavljenog snimka | Prazan rezultat, bez greške |
| Korisnik nema pravo na šifru | Zabranjen pristup |
| Partner bez naziva | Prikazuje se šifra |
| **Nema istorijskog mesečnog preseka** | Prikazuje se **samo tekuće stanje** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Devet iznosa: sedam razreda + dospelo + ukupno | Potvrđeno | `reports.py:36-37` |
| Grupisanje po partneru i grupi konta | Potvrđeno | `reports.py:27-31` |
| Bez objavljenog snimka — prazan rezultat | Potvrđeno | `reports.py:21-22` |
| Prava pristupa se primenjuju dvaput | Potvrđeno | `reports.py:17-18, 24` |

---

## PT-06 — Normalizacija nasleđenih kontakata

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kontakti“, oznaka „Potrebna provera“ |
| Tehnički naziv | `normalize_contacts()`, `parse_contact()` |
| Putanja | [`potrazivanja/services/contacts.py:70`](../../../potrazivanja/services/contacts.py#L70) |

### 2. Poslovna svrha

U nasleđenoj Naplati je kontakt bio **jedno tekstualno polje** u koje se upisivalo sve —
više imena, više telefona, više adresa e-pošte. Ovaj postupak taj tekst **razdvaja na
pojedinačne osobe i kanale**, a da **ništa ne izgubi**.

> **[P] Načelo iz koda:** *„Conservative, lossless conversion of legacy contact text into
> people and channels.“* — kada nije siguran, sistem **ne pogađa**, nego označava
> za proveru.

### 6. Tačan postupak

**Korak 1 — adrese e-pošte** [P]: traže se u oba polja (`email` i `name`), proveravaju
Django validatorom, svode na mala slova i **uklanjaju duplikati**.

**Korak 2 — razdvajanje na delove** [P]: polje imena se deli po **zarezu, tački-zarezu
i prelomu reda**.

**Korak 3 — telefoni** [P]: u svakom delu se traže brojevi, pa se čiste:

| Provera | Pravilo |
|---|---|
| Dozvoljeni znakovi | cifre, `+`, razmak, `()`, `/`, `.`, `-` |
| **Broj cifara** | **od 7 do 15** |
| Poseban slučaj | `+ 381 (0)` → `+381` |
| **Datum se ne prihvata** | Oblik `0D.MM.GGGG` se odbacuje |
| Domaći broj | Ako počinje nulom, mora imati **9 ili 10 cifara** |

**Korak 4 — prepoznavanje osobe** [P]. Deo je **osoba** samo ako **sve** važi:

| Uslov |
|---|
| Ima **tačno jedan** telefon |
| Preostali tekst ima **1 do 3 reči** |
| Svaka reč je **slovo po slovo** i počinje **velikim slovom** |
| Nijedna reč nije **oznaka funkcije** |

**Oznake funkcije** (`ROLE_WORDS`) [P]: `direktor`, `dir`, `knjigovodstvo`,
`racunovodstvo`, `računovodstvo`, `finansije`, `office`, `fax`, `faks`, `telefon`,
`tel`, `mobilni`, `knjig`, `agencija`.

**Korak 5 — šta postaje šta** [P]:

| Prepoznato | Ishod |
|---|---|
| Osoba | **Novi kontakt** sa imenom, prezimenom i telefonom, vezan za izvorni (`import_parent`) |
| Ostali telefoni | Kanali na **opštem kontaktu** |
| Adrese e-pošte | Kanali na opštem kontaktu |
| **Nerazrešeno** | Upisuje se u `original_data.unresolved` |

Izvorni zapis postaje **„Opšti kontakt“**, a **ceo izvorni tekst se čuva** u
`original_data`. [P]

**Korak 6 — oznaka za proveru** [P]. Kontakt se označava sa `needs_review` ako:

> ima nerazrešenih delova **ili** je iz njega izdvojena bar jedna osoba
> **ili** nije povezan sa partnerom

> **[Z]** Oznaka se stavlja i kada je razdvajanje uspelo — da čovek potvrdi rezultat.

**Idempotentnost [P]:** obrađuju se samo kontakti koji **još nisu normalizovani**
(`normalized_at` prazan) i koji **nisu nastali razdvajanjem** (`import_parent` prazan).
Ponovno pokretanje ne menja već obrađene.

**Kanali [P]:** `ContactPoint` je jedinstven po (kontakt, vrsta, vrednost) — isti broj
se ne upisuje dvaput.

### 8. Primer

**Izvorni zapis iz Naplate:**

| Polje | Vrednost |
|---|---|
| `name` | `Marko Marković 0641234567, računovodstvo 011/2345-678; Ana Anić 0651112223` |
| `email` | `office@primer.rs, ana@primer.rs` |

**Rezultat:**

| Nastalo | Vrsta | Sadržaj |
|---|---|---|
| **Opšti kontakt** (izvorni zapis) | — | Funkcija: „Opšti kontakt“ |
| — kanal | telefon | `0112345678` *(iz dela „računovodstvo“ — oznaka funkcije, nije osoba)* |
| — kanal | e-pošta | `office@primer.rs` |
| — kanal | e-pošta | `ana@primer.rs` |
| **Novi kontakt** | osoba | Marko Marković, `0641234567` |
| **Novi kontakt** | osoba | Ana Anić, `0651112223` |
| Oznaka | — | **„Potrebna provera“** — izdvojene su osobe |

Ceo izvorni tekst ostaje u `original_data`.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `potrazivanja_collectioncontact`, `potrazivanja_contactpoint` |
| Kada se pokreće | Jednom, pri osamostaljivanju operativnih podataka |
| Trag izvornog | `original_data` — **ceo izvorni zapis** |
| Kontrola | Pregledati kontakte sa oznakom „Potrebna provera“ |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Ime i telefon u jednom delu | Postaje osoba |
| Dva telefona u istom delu | **Nije osoba** — telefoni idu na opšti kontakt |
| „Direktor 0641234567“ | **Nije osoba** — `direktor` je oznaka funkcije |
| Datum umesto telefona | Prepoznaje se i odbacuje |
| Neispravna adresa e-pošte | Preskače se, deo ide u nerazrešeno |
| Ista osoba dvaput | Spaja se u **jedan** kontakt, oba telefona kao kanali |
| Ponovno pokretanje | Već obrađeni se **preskaču** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Ceo izvorni tekst se čuva | Potvrđeno | `contacts.py:73, 76` |
| Osoba samo uz tačno jedan telefon i 1–3 reči | Potvrđeno | `contacts.py:58-60` |
| Oznake funkcije sprečavaju prepoznavanje osobe | Potvrđeno | `contacts.py:10, 60` |
| Telefon mora imati 7–15 cifara | Potvrđeno | `contacts.py:19-20` |
| Datumi se ne pretvaraju u telefone | Potvrđeno | `contacts.py:51-52` |
| Ponovno pokretanje je bezbedno | Potvrđeno | `contacts.py:72` |

---

## Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-35** | Starosni razred **`0.1` („Nedospelo“) objedinjuje dva različita slučaja**: potraživanje koje još nije dospelo i potraživanje **kome se ne zna datum dospeća**. Dug star godinu dana bez unetog dospeća prikazuje se kao **nedospeo**. Pravilo je namerno preuzeto iz nasleđene Naplate. | Srednja |

## Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q33** | Da li potraživanja **bez datuma dospeća** treba i dalje prikazivati kao „Nedospelo“ (nasleđeno pravilo), ili ih izdvojiti u zaseban razred „Nepoznato dospeće“? Sistem ih već broji zasebno (`unknown_due_count`). |
| **Q34** | Postoji li planirani datum kada Potraživanja preuzimaju **sve** funkcije Naplate, uključujući pravnu službu, i kada se meni Naplate uklanja? |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.1. Finansijska analitika](06-01-finansije.md) | Prihodi, rashodi, tok gotovine |
| [6.9. Nabavka](06-09-nabavka.md) | Predmeti nabavke i fakture |
| [4. Baza podataka](../04-baza-podataka.md#48-potraživanja--potrazivanja) | Tabele Potraživanja |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema |
