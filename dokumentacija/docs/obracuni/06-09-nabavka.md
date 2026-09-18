# 6.9. Nabavka — obračuni i analize

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](../10-poznati-problemi.md).

**Analize u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [B-01](#b-01--procenjena-vrednost-stavke-i-predmeta) | Procenjena vrednost stavke i predmeta | **P-38** |
| [B-03](#b-03--ključ-euf-fakture) | Ključ EUF fakture | **P-39** |
| [B-02](#b-02--grupisanje-uf-stavki-u-uf-fakture) | Grupisanje UF stavki u UF fakture | **P-37** |
| [B-04](#b-04--razlike-verzija-plana-javnih-nabavki) | Razlike verzija plana javnih nabavki | — |
| [B-05](#b-05--provera-šifre-posla-partnera) | Provera šifre posla partnera | — |
| [B-06](#b-06--izveštaji-i-alarmi-nabavke) | Izveštaji i alarmi nabavke | ~~P-36~~ |
| [B-07](#b-07--poklapanje-robe-sa-uf-ili-euf-fakturom) | Poklapanje robe sa UF ili EUF fakturom | — |

---

## Zajednička osnova: tri izvora i tri snimka

Nabavka radi nad **sopstvenim evidencijama** (predmeti, stavke, narudžbenice) i nad
**tri snimka nasleđenih izvora**:

| Snimak | Django tabela | Izvor | Zadatak |
|---|---|---|---|
| Snimak | Django tabela | Izvor | Zadatak | **Najviše redova po prolazu** |
|---|---|---|---|---|
| **EUF fakture** | `nabavka_invoice` | `dbo.nbv_preuzete_EUF` | Dnevno u 02:20 | **2.000** |
| **UF stavke** | `nabavka_euf_item_snapshot` | `dbo.nbv_EUF_stavke` | Dnevno u 02:45 | **20.000** |
| **Roba** | `nabavka_goods_snapshot` | `dbo.nbv_roba` | Dnevno u 07:10 | **20.000** |
| *UF fakture* | `nabavka_uf_invoice_snapshot` | **izvedeno iz UF stavki** | Uz sinhronizaciju stavki | — |

```
 dbo.nbv_preuzete_EUF ──► EUF fakture (nabavka_invoice)
                              │
 dbo.nbv_EUF_stavke   ──► UF stavke ──grupisanje──► UF fakture
                              │
 dbo.nbv_roba         ──► Roba
                              │
              povezivanje sa stavkom predmeta nabavke
                              ▼
                  predmet ── faktura ── šifra posla
```

> **[P] Načelo:** stavka predmeta nabavke povezuje se sa **tačno jednim** izvorom
> (`euf`, `uf` ili `goods`). Provera je u `ProcurementItem.clean()`.

### Granice preuzimanja [P]

EUF fakture se čitaju sa `SELECT TOP (limit)` uz `ORDER BY TRY_CONVERT(date, datum) DESC`,
a zadatak poziva sa `limit=2000`. **Preuzima se samo najnovijih 2.000 faktura po prolazu.**
Tvrdi maksimum je takođe 2.000.

Za UF stavke i Robu podrazumevano je 10.000, a tvrdi maksimum **20.000**.

> **[Z] Šta to znači:** ako izvor u jednom danu ima više od toga, **višak se ne preuzima** i
> nema upozorenja. Kod EUF faktura granica je najuža, a `get_euf_invoice()` traži ključ
> **linearno** kroz listu od 2.000 redova.

Svaki od tri zadatka ima **singleton zaključavanje**: TTL 2 sata za EUF fakture, 3 sata za
UF stavke i Robu. [P]

### Dva odvojena mehanizma povezivanja [P]

Ovo se lako pomeša, a razlika menja iznose u izveštajima:

| Odakle se povezuje | Šta se upisuje | Ulazi u „Ukupan iznos faktura“ ([B-06](#b-06--izveštaji-i-alarmi-nabavke)) |
|---|---|---|
| **Sa detalja predmeta** | `ProcurementItem.source_type` + jedan FK (`euf_invoice` / `uf_invoice` / `goods_item`) | **Ne** |
| **Sa detalja EUF fakture** | Red u `nabavka_item_invoice_link` (`ProcurementItemInvoiceLink`) | **Da** |

> **[P]** Samo drugi način stvara vezu koja se broji u zbiru faktura i u koloni „povezane
> stavke“ na fakturi. Veza je **jedan na jedan prema stavci** (`OneToOneField`) — jedna
> stavka ima najviše jednu fakturu, ali **jedna faktura može imati više stavki i više
> predmeta**.

Pri povezivanju sa fakture nude se **samo** stavke bez već postojeće veze
(`invoice_link__isnull=True`) i predmeti čiji status **nije** `Završeno`, sortirano po
`-procurement_case__created_at`. [P]

> **[P] Automatska promena statusa:** kada se **novom** vezom stavka poveže sa EUF fakturom
> i predmet je u statusu **`Čeka fakturu`**, status predmeta se automatski menja u
> **`Faktura povezana`**.

---

## B-01 — Procenjena vrednost stavke i predmeta

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Procenjena vrednost“ |
| Tehnički naziv | `ProcurementItem.estimated_total`, `ProcurementCase.estimated_value` |
| Putanja | [`nabavka/models.py:306`](../../../nabavka/models.py#L306) |

### 2. Poslovna svrha

Pokazuje **koliko se očekuje da će nabavka koštati**, pre nego što stigne faktura —
osnov za odobravanje i za praćenje plana javnih nabavki.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | JM | Ko unosi |
|---|---|---|---|---|
| Količina | Količina | `nabavka_procurement_item.quantity` | prema JM | Podnosilac zahteva |
| Procenjena cena | Procenjena cena | `nabavka_procurement_item.estimated_unit_price` | RSD | Podnosilac zahteva |
| **Procenjena vrednost predmeta** | Procenjena vrednost | `nabavka_procurement_case.estimated_value` | prema valuti | **Podnosilac zahteva, ručno** |
| Valuta | Valuta | `nabavka_procurement_case.currency` | RSD/EUR/USD/CHF | Podnosilac zahteva |

### 6. Tačan postupak obračuna

**Po stavci [P]:**

> **procenjena vrednost stavke = procenjena cena × količina**
> ako **bilo koja** od dve vrednosti nedostaje → **prazno** (`None`)

**Po predmetu [P]:**

> **procenjena vrednost predmeta se NE računa iz stavki** — unosi se **ručno**,
> kao zaseban podatak na predmetu

> **[P] Problem P-38:** predmet ima sopstveno polje „Procenjena vrednost“, nezavisno od
> zbira stavki. Sistem **nigde ne poredi** to dvoje, pa se mogu razlikovati bez upozorenja.

**Zaokruživanje [P]:** nema — množe se decimalni brojevi kakvi jesu.

**Valuta [P]:** valuta postoji **samo na predmetu**, ne na stavci. Procenjena cena stavke
se **podrazumeva u valuti predmeta**. [Z]

### 8. Primer

| Stavka | Količina | JM | Procenjena cena | Procenjena vrednost |
|---|---|---|---|---|
| Ulje motorno 5W30 | 40,00 | l | 1.250,00 | **50.000,00** |
| Filter ulja | 10,00 | kom | 1.800,00 | **18.000,00** |
| Rad servisera | 6,00 | h | *(nije uneta)* | **prazno** |
| | | | **Zbir stavki** | **68.000,00** |
| | | | **Uneto na predmetu** | **75.000,00** |

> Razlika od 7.000,00 RSD ostaje **neprimećena** — sistem je ne prijavljuje.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Stavka: računa se pri prikazu. Predmet: **čuva se** kao uneta vrednost |
| Upotreba | Odobravanje predmeta, poređenje sa planom javnih nabavki |
| Kontrola | **Ručno** sabrati stavke i uporediti sa vrednošću predmeta |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Nema procenjene cene | Vrednost stavke prazna | Vidljivo |
| **Zbir stavki ≠ vrednost predmeta** | **Nema upozorenja** | **P-38** |
| Različite valute | Nemoguće — valuta je samo na predmetu | — |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Vrednost stavke = cena × količina | Potvrđeno | `models.py:306-310` | — |
| Prazno kad nedostaje podatak | Potvrđeno | `models.py:308-309` | — |
| **Vrednost predmeta se unosi ručno** | **Potvrđeno** | `models.py:110-116` | **P-38** |
| Valuta samo na predmetu | Potvrđeno | `models.py:117-122` | — |

---

## B-03 — Ključ EUF fakture

> Ovo nije obračun iznosa, nego **obračun identiteta** — određuje šta je „ista faktura“.
> Od njega zavisi da li će se veza sa predmetom nabavke sačuvati ili izgubiti.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Ne prikazuje se |
| Tehnički naziv | `make_euf_key()` |
| Putanja | [`nabavka/services/euf.py:49`](../../../nabavka/services/euf.py#L49) |

### 2. Poslovna svrha

Nasleđeni pogled `dbo.nbv_preuzete_EUF` **nema stabilan identifikator** fakture.
Sistem ga pravi sam, iz sadržaja reda, da bi pri svakom preuzimanju prepoznao
**istu fakturu**.

### 6. Tačan postupak obračuna

> **ključ = SHA-256 od:** `datum` **|** `naziv partnera` **|** `broj fakture` **|** `iznos`

| Sastojak | Kako se priprema |
|---|---|
| `datum` | **Izvorni tekst**, samo očišćen od razmaka — **ne** pretvoren u datum |
| `naziv partnera` | Očišćen od razmaka |
| `broj fakture` | Očišćen od razmaka |
| `iznos` | Zaokružen na **2 decimale**; prazan iznos → **prazan tekst** |

Razdvajač je uspravna crta `|`. [P]

> **[P] Zašto se koristi izvorni tekst datuma:** isti datum može stići u različitim
> oblicima (`2026-03-15`, `15.03.2026`). Ključ koristi **izvorni zapis**, pa bi promena
> oblika u izvoru promenila ključ. Poseban obrađen datum (`datum`) se čuva **odvojeno**.

**Prepoznati oblici datuma** (za polje `datum`, ne za ključ) [P]:
`GGGG-MM-DD`, `DD.MM.GGGG`, `DD/MM/GGGG`, `MMM DD GGGG`.

**Jedinstvenost [P]:** `nabavka_invoice` je jedinstvena po (`source`, `euf_key`).

### 8. Primer

| Polje | Vrednost |
|---|---|
| datum | `15.03.2026` |
| naziv partnera | `AUTODEKI DOO` |
| broj fakture | `2026-1234` |
| iznos | `45000.00` |

> Tekst za heširanje: `15.03.2026|AUTODEKI DOO|2026-1234|45000.00`
> Ključ: `a3f2…` (64 heksadecimalna znaka)

**Šta se dešava kada se izvor promeni:**

| Promena u izvoru | Novi ključ? | Posledica |
|---|---|---|
| Ispravljen iznos sa 45.000,00 na 45.600,00 | **Da** | **Nova faktura**; stara ostaje sa vezama |
| Ispravljen naziv partnera | **Da** | Isto |
| Promenjen oblik datuma | **Da** | Isto |
| Promenjen centar ili magacin | Ne | Ista faktura, ažuriraju se polja |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Ispravka iznosa, partnera ili datuma u izvoru** | **Nastaje nova faktura**, stara ostaje | **P-39** |
| Dve različite fakture sa istim datumom, partnerom, brojem i iznosom | **Isti ključ** — spajaju se u jednu | **P-39** |
| Prazan iznos | Ulazi u ključ kao prazan tekst | Vidljivo |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Ključ je SHA-256 četiri polja | Potvrđeno | `euf.py:49-57` | — |
| Datum ulazi kao **izvorni tekst** | Potvrđeno | `euf.py:52, 61` | — |
| Iznos se zaokružuje na 2 decimale | Potvrđeno | `euf.py:50` | — |
| **Ispravka u izvoru pravi novu fakturu** | **Potvrđeno** | `euf.py:49-57` | **P-39** |

---

## B-02 — Grupisanje UF stavki u UF fakture

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „UF fakture“ |
| Tehnički naziv | `rebuild_uf_invoice_snapshots()` |
| Putanja | [`nabavka/services/source_snapshots.py:192`](../../../nabavka/services/source_snapshots.py#L192) |
| Adresa | `/nabavka/uf-stavke/`, detalj `/nabavka/uf-stavke/<id>/` |

### 2. Poslovna svrha

Izvor isporučuje **pojedinačne stavke** ulaznih faktura, bez zaglavlja fakture.
Ovaj postupak stavke **grupiše u fakture**, da bi korisnik video dokument, a ne samo redove.

### 6. Tačan postupak obračuna

**Ključ grupisanja [P]:**

> **SHA-256 od:** (broj fakture **ili** rezerva) **|** (PIB **ili** matični broj **ili** naziv partnera)

| Deo | Redosled traženja |
|---|---|
| Identifikator fakture | `invoice_number` → ako je prazan: `purchase_invoice_id` → `source_key` |
| Identifikator partnera | `partner_pib` → `partner_mb` → `partner_name` |

**Vrednosti fakture — tri različita pravila [P]:**

| Polje | Pravilo |
|---|---|
| `purchase_invoice_id`, `invoice_number`, `partner_pib`, `partner_mb`, `partner_name`, `accounts` | **Prva neprazna** vrednost među stavkama |
| `document_date`, `creation_date`, `due_date` | **Najkasniji** datum među stavkama |
| `total`, `base_amount`, `payment_amount` | **Prva vrednost koja nije prazna** |
| **`item_value_total`** | **Zbir `value` svih stavki** |
| `item_count` | Broj stavki |
| `accounts` | **Sva različita konta**, sortirana, razdvojena zarezom |

> **[P] Dva iznosa, dva značenja:**
> **`total`** je iznos **iz zaglavlja** izvora (ponovljen na svakoj stavci),
> a **`item_value_total`** je **zbir stavki**. Ako se razlikuju, izvor je nedosledan —
> to je korisna kontrola.

**Povezivanje [P]:** posle grupisanja se svakoj stavci upisuje veza ka fakturi, a
stavkama predmeta nabavke koje imaju vezu ka **stavci**, a nemaju ka **fakturi**,
dopunjava se veza ka fakturi.

**Brisanje viška [P]:**

> `UfInvoiceSnapshot.objects.exclude(pk__in=invoice_ids).delete()`

Sve UF fakture koje se nisu pojavile u ovom prolazu se **brišu**.

> **[P] Problem P-37:** veza `ProcurementItem.uf_invoice` je `SET_NULL`, pa brisanje
> fakture **tiho uklanja vezu** sa stavke predmeta nabavke — bez upozorenja i bez traga.

Ceo postupak je u **jednoj transakciji**. [P]

### 8. Primer

**UF stavke iz izvora:**

| Stavka | Broj fakture | PIB | Datum dokumenta | Vrednost | Konto |
|---|---|---|---|---|---|
| 1 | `2026-1234` | `100123456` | 15.03.2026. | 30.000,00 | `51300` |
| 2 | `2026-1234` | `100123456` | **20.03.2026.** | 18.000,00 | `51300` |
| 3 | `2026-1234` | `100123456` | 15.03.2026. | 12.000,00 | `52400` |

**Nastala UF faktura:**

| Polje | Vrednost | Pravilo |
|---|---|---|
| Broj fakture | `2026-1234` | prva neprazna |
| PIB | `100123456` | prva neprazna |
| **Datum dokumenta** | **20.03.2026.** | **najkasniji** |
| `item_value_total` | **60.000,00** | zbir stavki |
| `item_count` | 3 | |
| `accounts` | `51300, 52400` | sva različita, sortirana |

> Uočite: datum dokumenta je **najkasniji**, ne najraniji. Ako izvor ima grešku u datumu
> jedne stavke, cela faktura dobija taj datum.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Stavka bez broja fakture | Koristi se `purchase_invoice_id` ili `source_key` — **svaka takva stavka postaje zasebna faktura** | Vidljivo |
| Isti broj fakture kod dva partnera | **Različite fakture** — partner je u ključu | Ispravno |
| **Faktura nestala iz izvora** | **Briše se, veza sa predmetom tiho nestaje** | **P-37** |
| Neslaganje `total` i `item_value_total` | Oba se prikazuju, bez upozorenja | Korisna kontrola |
| Različiti datumi na stavkama | Uzima se najkasniji | Vidljivo |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Ključ je broj fakture + identifikator partnera | Potvrđeno | `source_snapshots.py:164-168` | — |
| Datumi: najkasniji | Potvrđeno | `source_snapshots.py:171-173` | — |
| Iznosi zaglavlja: prva neprazna vrednost | Potvrđeno | `source_snapshots.py:184-188` | — |
| `item_value_total` je zbir stavki | Potvrđeno | `source_snapshots.py:215` | — |
| **Višak faktura se briše** | **Potvrđeno** | `source_snapshots.py:229-232` | **P-37** |
| Ceo postupak je jedna transakcija | Potvrđeno | `source_snapshots.py:191` | — |

---

## B-04 — Razlike verzija plana javnih nabavki

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Plan javnih nabavki“, kolona „Status razlike“ |
| Tehnički naziv | `import_public_procurement_plan()` |
| Putanja | [`nabavka/services/public_procurements.py:392`](../../../nabavka/services/public_procurements.py#L392) |
| Adrese | `/nabavka/javne-nabavke/`, uvoz `/nabavka/javne-nabavke/uvoz/` |

### 2. Poslovna svrha

Plan javnih nabavki se tokom godine **više puta menja**. Ovaj postupak pri svakom uvozu
pravi **novu verziju** i jasno pokazuje **šta je dodato, izmenjeno i uklonjeno** u odnosu
na prethodnu.

### 3. Korisnici rezultata

Služba nabavke, uprava, pravna služba.

### 4. Ulazni podaci

Excel datoteka plana. Zaglavlje se **prepoznaje samo po nazivima kolona**. [P]

**Dve vrste plana** se razlikuju po prisutnim kolonama [P]:

| Ako list ima kolonu | Vrsta plana |
|---|---|
| „Osnov izuzeća“ ili „Način procene vrednosti“ | **Nabavka bez primene ZJN** (`exempt`) |
| inače | **Javna nabavka** (`public`) |

### 6. Tačan postupak obračuna

#### Korak 1 — stabilni ključ stavke [P]

Ključ mora ostati isti između verzija, da bi se stavka prepoznala.

**Ako stavka ima redni broj** (vodeće nule se uklanjaju):

| Dostupno | Ključ |
|---|---|
| Odeljak **i** kategorija | `vrsta:list:odeljak:kategorija:broj` |
| Samo odeljak | `vrsta:list:odeljak:broj` |
| Ništa od toga | `vrsta:list:broj` |

**Ako stavka nema redni broj:**

> `vrsta:list:title:` + prvih **24 znaka** SHA-256 otiska **preslovljenog naslova**

Naziv lista se skraćuje na 30, odeljak i kategorija na 40 znakova. [P]

#### Korak 2 — otisak sadržaja [P]

> otisak = SHA-256 svih polja stavke, **osim broja reda u Excel-u**

> **[P] Zašto se broj reda izuzima:** pomeranje stavke gore-dole u Excel-u **ne sme**
> da je označi kao izmenjenu.

#### Korak 3 — poređenje sa prethodnom verzijom [P]

Uzima se **poslednja verzija za tu godinu**, **bez** stavki označenih kao uklonjene.

| Uslov | Status |
|---|---|
| Ključ ne postoji u prethodnoj verziji | **Dodato** |
| Ključ postoji, **isti otisak** | **Bez izmene** |
| Ključ postoji, **drugi otisak** | **Izmenjeno** |
| Ključ postojao, a nema ga u novoj | **Uklonjeno** |

#### Korak 4 — prenošenje uklonjenih [P]

Uklonjena stavka se **prepisuje u novu verziju** sa statusom „Uklonjeno“, sa svim
podacima iz prethodne verzije.

> **[Z] Posledica:** svaka verzija je **potpuna slika** — sadrži i ono što je uklonjeno.

> **[P] Ograničenje:** stavka uklonjena u v2 pa ponovo uvedena u v3 dobija status
> **„Dodato“**, jer se pri poređenju uklonjene stavke izostavljaju. Veza sa izvornom
> stavkom se gubi.

#### Korak 5 — brojači verzije [P]

Upisuju se `total_rows`, `added_count`, `changed_count`, `unchanged_count`, `removed_count`.

#### Ostala pravila [P]

| Pravilo | Opis |
|---|---|
| Broj verzije | `najveći za tu godinu + 1` |
| Zbirni redovi | Naslovi koji počinju sa **„ukupno“** ili **„svega“** se **preskaču** |
| Listovi bez prepoznatog zaglavlja | Preskaču se i **prijavljuju** korisniku |
| Duplirani ključevi | Prijavljuju se korisniku |
| Prazan rezultat | *„Excel ne sadrzi prepoznate stavke plana javnih nabavki.“* |
| Izvorni red | Ceo se čuva u `raw_data` |
| Upis | **Red po red**, ne paketno — zbog mešanih JSON i decimalnih vrednosti na SQL Serveru |
| Transakcija | Ceo uvoz je jedna transakcija |

### 8. Primer

> Plan za 2026, verzija 2.

| Stavka u v1 | Stavka u v2 | Otisak | Status u v2 |
|---|---|---|---|
| 1. Kancelarijski materijal, 500.000 | 1. Kancelarijski materijal, 500.000 | isti | **Bez izmene** |
| 2. Gorivo, 8.000.000 | 2. Gorivo, **9.500.000** | drugi | **Izmenjeno** |
| 3. Računari, 1.200.000 | *(nema)* | — | **Uklonjeno** *(prepisano iz v1)* |
| *(nema)* | 4. Softverske licence, 700.000 | — | **Dodato** |

**Brojači verzije 2:** ukupno 4 — dodato 1, izmenjeno 1, bez izmene 1, uklonjeno 1.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `nabavka_public_procurement_plan_version` i `…_item` |
| **Istorija** | **Potpuna** — sve verzije ostaju |
| Upotreba | Praćenje izmena plana, poređenje sa stvarnim nabavkama |
| Kontrola | Brojači verzije; svaka stavka nosi vezu na prethodnu (`previous_item`) |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Izmenjen naslov stavke bez rednog broja | **Nov ključ** → „Dodato“ + „Uklonjeno“ umesto „Izmenjeno“ |
| Preimenovan list u Excel-u | **Nov ključ** za sve stavke tog lista |
| Stavka uklonjena pa vraćena | „Dodato“, bez veze sa izvornom |
| Pomerena stavka u Excel-u | **Bez izmene** — broj reda nije u otisku |
| Zbirni red („Ukupno“) | Preskače se |
| List bez prepoznatog zaglavlja | Preskače se, prijavljuje se |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Stabilni ključ i njegovi oblici | Potvrđeno | `public_procurements.py:211-231` |
| Broj reda se izuzima iz otiska | Potvrđeno | `public_procurements.py:235` |
| Četiri statusa razlike | Potvrđeno | `public_procurements.py:357-363` |
| Uklonjene stavke se prepisuju | Potvrđeno | `public_procurements.py:329-354, 437-439` |
| Uklonjene se izuzimaju pri poređenju | Potvrđeno | `public_procurements.py:416-418` |
| Vrsta plana se prepoznaje po kolonama | Potvrđeno | `public_procurements.py:205-208` |
| Zbirni redovi se preskaču | Potvrđeno | `public_procurements.py:240-242` |

---

## B-05 — Provera šifre posla partnera

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Provera sifre posla za partnera“ |
| Tehnički naziv | `fetch_partner_job_code_rows()` |
| Putanja | [`nabavka/views/reports.py:18`](../../../nabavka/views/reports.py#L18) |
| Adresa | `/nabavka/izvestaji/provera-sifre-posla-partnera/` |

### 2. Poslovna svrha

Pokazuje **koje šifre posla su vezane za kog partnera** u nasleđenom izvoru, radi
provere pre povezivanja fakture sa šifrom posla.

### 6. Tačan postupak

**Nema obračuna** — čita se nasleđeni pogled i prikazuje kako jeste. [P]

| Element | Vrednost |
|---|---|
| Izvor | `dbo.nbv_sif_pos_par` |
| Kolone | `sif_par`, `naz_par`, `sif_pos` |
| Filter | Deo naziva partnera (opciono) |
| **Ograničenje** | **Najviše 2.000 redova** (`TOP`) |
| Sortiranje | Po nazivu partnera, pa po šifri posla |

> **[P] Bez filtera se prikazuje samo prvih 2.000 redova**, bez oznake da je spisak
> odsečen. Korisnik ne zna da li vidi sve.

**Dozvola [P]:** `nabavka:reports` — ista kao za opšte izveštaje.

### 12–13. Izuzeci i pouzdanost

| Tvrdnja | Status | Izvor |
|---|---|---|
| Čisto čitanje, bez obrade | Potvrđeno | `reports.py:26-44` |
| Ograničenje 2.000 redova | Potvrđeno | `reports.py:27` |
| **Sadržaj pogleda nije poznat** | **Nepotvrđeno** | Čeka DDL — **P-27** |

---

## B-06 — Izveštaji i alarmi nabavke

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Izveštaji nabavke“, „Alarmi nabavke“ |
| Tehnički naziv | `ReportsView`, `AlertsView` |
| Putanja | [`nabavka/views/reports.py:47`](../../../nabavka/views/reports.py#L47), [`nabavka/views/alerts.py:10`](../../../nabavka/views/alerts.py#L10) |
| Adrese | `/nabavka/izvestaji/`, `/nabavka/alarmi/` |

### 2. Poslovna svrha

Brz pregled stanja nabavke: koliko predmeta je u kom statusu i koje vrste, ukupan iznos
povezanih faktura i narudžbenica, i spisak predmeta koji **čekaju fakturu**.

### 6. Tačan postupak

#### Izveštaji nabavke — četiri pokazatelja [P]

| Pokazatelj | Postupak |
|---|---|
| **Po statusu** | Broj predmeta po svakom od sedam statusa |
| **Po tipu** | Broj predmeta po tipu (nabavka / usluga / oprema) |
| **Ukupan iznos faktura** | Zbir `amount` faktura **koje imaju bar jednu povezanu stavku** |
| **Ukupan iznos narudžbenica** | Zbir `amount` **svih** narudžbenica |

Ukupan iznos faktura sabira se nad skupom **bez ponavljanja** [P]:

```python
ProcurementInvoice.objects.filter(
    pk__in=ProcurementItemInvoiceLink.objects.values("invoice_id")
).aggregate(total=Sum("amount"))["total"]
```

> **Ispravljeno 18.09.2026.** — raniji upit je filtrirao po `item_links`, što pravi
> **spoj sa tabelom veza**, pa se faktura pojavljivala **onoliko puta koliko ima
> povezanih stavki**; `distinct()` na to nije uticao jer se primenjuje na spoljni
> `SELECT`, a ne na sabiranje. Faktura od 100.000 RSD sa tri stavke ulazila je kao
> **300.000 RSD**.
>
> **Prikazani iznos će zato biti manji nego ranije. Raniji je bio pogrešan.**
> Videti [P-36](../10-poznati-problemi.md).

#### Alarmi nabavke [P]

> prikazuju se **samo** predmeti sa statusom **„Čeka fakturu“** (`waiting_invoice`)

Nema nijednog drugog alarma — **nema upozorenja** na osnovu datuma zahteva (`needed_by`),
prekoračenja procenjene vrednosti ni starosti predmeta. [P]

### 8. Primer

> Tri fakture povezane sa predmetima.

| Faktura | Iznos | Broj povezanih stavki |
|---|---|---|
| F-100 | 100.000,00 | **3** |
| F-200 | 50.000,00 | **1** |
| F-300 | 20.000,00 | **2** |

| Pokazatelj | Tačno | **Prikazano** |
|---|---|---|
| Ukupan iznos faktura | 170.000,00 | **390.000,00** *(3×100.000 + 1×50.000 + 2×20.000)* |

> Prikazan iznos je **2,3 puta veći** od stvarnog.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde |
| Upotreba | Pregled stanja nabavke |
| **Kontrola** | **Ukupan iznos faktura uporediti sa spiskom** `/nabavka/euf-fakture/` — zbir tamo je tačan |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Faktura sa više povezanih stavki | Iznos ulazi u zbir **jednom** | Ispravljeno, **P-36** |
| Faktura bez povezanih stavki | Ne ulazi u zbir | Namerno |
| Narudžbenica bez iznosa | Ne uvećava zbir | Vidljivo |
| Predmet zaglavljen mesecima | **Nema alarma** | Ograničenje |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Brojači po statusu i tipu | Potvrđeno | `reports.py:55-56` | — |
| Zbir faktura broji svaku fakturu jednom | Potvrđeno | `reports.py` — podupit `pk__in` | Rešeno, **P-36** |
| Zbir narudžbenica obuhvata sve | Potvrđeno | `reports.py:61` | — |
| Alarm je samo „Čeka fakturu“ | Potvrđeno | `alerts.py:18-20` | — |

---

## B-07 — Poklapanje robe sa UF ili EUF fakturom

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Oznaka `UF` / `EUF` uz vezni dokument na spisku robe |
| Tehnički naziv | `_goods_invoice_match_badges()` |
| Putanja | [`nabavka/views/source_snapshots.py`](../../../nabavka/views/source_snapshots.py) |

### 2. Poslovna svrha

Roba u izvoru **nema trajnu vezu sa fakturom**. Zato postoje **dva nivoa povezivanja** [P]:

| Nivo | Šta radi |
|---|---|
| **Tvrdo povezivanje** | Korisnik **sam izabere** tačan zapis i poveže ga sa stavkom zahteva |
| **Meko poklapanje** | Sistem **samo naglasi** da roba verovatno pripada nekoj UF ili EUF fakturi |

**Zašto nema automatske trajne veze [P]:**

1. Ista roba može biti deo UF fakture.
2. Ista ili slična roba može biti vidljiva i kroz EUF.
3. Neke robe su iz ranijih perioda i **nemaju učitanu fakturu**.
4. Ponekad postoji **samo robni trag**, bez jasne fakture u lokalnom snimku.

> Meko poklapanje je **pomoć pri radu, a ne evidencija**. Ne upisuje se u bazu i ne menja
> nijedan iznos. [P]

### 6. Tačan postupak

**Korak 1 — koja roba se uopšte proverava** [P]: samo redovi koji imaju **i** `linked_document`
**i** naziv partnera. Roba bez jednog od toga se preskače.

**Korak 2 — poklapanje broja dokumenta** [P]:

| Vrsta | Poklapa se sa |
|---|---|
| **UF** | `UfInvoiceSnapshot.invoice_number` **ili** `purchase_invoice_id` |
| **EUF** | `ProcurementInvoice.invoice_number` |

Broj se pre poređenja **normalizuje**: `" ".join(str(value).split()).casefold()` — dakle
sređeni razmaci i mala slova.

**Korak 3 — poklapanje firme** [P]. Naziv partnera se svodi na tokene:

1. uklone se dijakritici;
2. sve što nije `a-z0-9` postaje razmak;
3. izbacuju se pravni oblici **`doo`, `ad`, `szr`, `pr`** — i razbijeni oblici `d o o`, `a d`.

Poklapanje je **tačno ili prefiksno po tokenima**: kraći niz tokena mora biti **početak**
dužeg. Tako se „AUTO DEKI DOO“ i „Auto Deki d.o.o. Beograd“ prepoznaju kao ista firma.

**Korak 4 — prikaz oznake** [P]: oznaka se prikazuje **samo kada postoji tačno jedno**
poklapanje te vrste. Oznaka je **link na tu fakturu**, a tooltip glasi
*„Potvrdjeno brojem fakture i firmom“*.

### 8. Primer

| Roba | `linked_document` | Partner | Rezultat |
|---|---|---|---|
| Filter ulja | `TEST-UF-001/2026` | `AUTO DEKI DOO` | Jedna UF sa tim brojem i firmom → oznaka **`UF`** |
| Guma | `12345` | `Auto Deki d.o.o.` | Dve UF fakture sa istim brojem → **nema oznake** |
| Akumulator | *(prazno)* | `AUTO DEKI DOO` | Nema veznog dokumenta → **ne proverava se** |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Više od jednog poklapanja iste vrste | **Nema oznake** — izvor nije jednoznačan |
| **Poklapa se i sa UF i sa EUF** | Prikazuje se **`UF`**, sa tooltipom *„Potvrdjeno brojem fakture i firmom. Postoji i EUF, ali roba se prikazuje kao UF jer UF ima stavke.“* [P] |
| Roba bez `linked_document` ili bez partnera | Preskače se bez traga |
| Firma se razlikuje samo po pravnom obliku | **Poklapa se** — pravni oblici se izbacuju |
| Firma je prefiks druge firme | **Poklapa se** — prefiksno pravilo može spojiti „Auto Deki“ i „Auto Deki Plus“ [Z] |

> **[Z] Granica prefiksnog pravila:** dve stvarno različite firme čiji je naziv jedne
> početak druge biće prepoznate kao ista. Uz obavezno poklapanje broja fakture to je malo
> verovatno, ali **nije nemoguće**.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Dva nivoa povezivanja, meko se ne upisuje | Potvrđeno | `source_snapshots.py` |
| Normalizacija broja i naziva firme | Potvrđeno | `_company_matches()` |
| Oznaka samo kod tačno jednog poklapanja | Potvrđeno | `_goods_invoice_match_badges()` |
| Kod dvostrukog poklapanja prikazuje se **UF** | Potvrđeno | `nabavka/tests.py` — `assertIn(">UF</a>")`, `assertNotIn(">EUF</a>")` |

> **Ispravka ranije dokumentacije [P]:** stariji dokument
> `nabavka-modeli-zahtevi-euf-uf-roba.md` tvrdio je da se kod poklapanja i sa UF i sa EUF
> **oznaka ne prikazuje**. **To više ne važi** — prikazuje se UF, jer UF ima stavke.

---

## Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-36** | ~~**Ukupan iznos faktura na izveštaju Nabavke je višestruko uvećan.**~~ **Rešeno 18.09.2026.** | **Visoka** |
| **P-37** | Pri obnavljanju UF faktura se **brišu** one koje se nisu pojavile u prolazu. Veza sa stavkom predmeta nabavke je `SET_NULL`, pa **tiho nestaje**, bez upozorenja i bez traga. | **Srednja** |
| **P-38** | Predmet nabavke ima **ručno unetu** procenjenu vrednost, nezavisnu od zbira stavki. Sistem ih **nigde ne poredi**, pa razlika ostaje neprimećena. | Srednja |
| **P-39** | Ključ EUF fakture se pravi iz **datuma, partnera, broja i iznosa**. Svaka ispravka bilo kog od ta četiri podatka u izvoru stvara **novu fakturu**, dok stara ostaje sa svim vezama. Dve stvarno različite fakture sa istim vrednostima dobijaju **isti ključ**. | **Srednja** |

## Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q35** | Da li se ispravke iznosa ili naziva partnera u izvoru EUF faktura dešavaju u praksi? Ako da, koliko često se pojavljuju „dvojnici“ faktura (**P-39**)? |
| **Q36** | Treba li sistem da upozori kada se **zbir stavki** predmeta nabavke razlikuje od **ručno unete** procenjene vrednosti (**P-38**)? |
| **Q37** | Da li su potrebni dodatni alarmi u Nabavci — npr. predmet stariji od N dana bez fakture, ili prekoračenje procenjene vrednosti? |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.8. Potraživanja](06-08-potrazivanja.md) | Dugovanja kupaca |
| [6.11. Ugovori i menice](06-11-ugovori-i-menice.md) | Partneri, ugovori, menice |
| [4. Baza podataka](../04-baza-podataka.md#47-nabavka--nabavka) | Tabele Nabavke |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema |
