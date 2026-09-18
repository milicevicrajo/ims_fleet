# 6.7. Mobilna telefonija — obračuni

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](../10-poznati-problemi.md).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [M-04](#m-04--povezivanje-broja-telefona-sa-zaposlenim) | Povezivanje broja telefona sa zaposlenim | — |
| [M-02](#m-02--izuzeci-od-parkinga) | Izuzeci od parkinga | — |
| [M-01](#m-01--obustava-po-zaposlenom) | **Obustava po zaposlenom** | **P-30, P-31** |
| [M-03](#m-03--razvrstavanje-zaposleni--bivši--nezaposleni) | Razvrstavanje zaposleni / bivši / nezaposleni | **P-32** |

> **Ovo je jedan od tri obračuna u sistemu čiji rezultat ide u obračun zarada.**
> Ostali su ocenjivanje ([K-08](06-06-kadrovi.md#k-08--ocenjivanje-zaposlenih--stimulacija-i-lični-koeficijent))
> i radna lista ([K-04](06-06-kadrovi.md#k-04-i-k-05--sati-radne-liste)).

---

## Zajednička osnova: četiri evidencije

Modul radi nad četiri odvojene evidencije koje se **mesečno uvoze iz Excel datoteka**
dobijenih od operatera:

| Evidencija | Tabela | Jedinstveno po | Uvoz |
|---|---|---|---|
| **Paketi** | `mobilni_mobilepackage` | partner + naziv + važi od | Bez perioda |
| **Korisnici** | `mobilni_mobileuser` | šifra radnika | Bez perioda |
| **Dodele** | `mobilni_mobileassignment` | **godina + mesec + broj** | **Po mesecu** |
| **Potrošnja** | `mobilni_mobileusage` | **godina + mesec + broj** | **Po mesecu** |

Svaki uvoz se beleži u `mobilni_mobileimportlog` i posle svakog uvoza se automatski
pokreće povezivanje sa zaposlenima (`sync_employee_links`). [P]

```
 Excel operatera ──► Paketi        (naziv, neto iznos, period važenja)
                 ──► Korisnici     (šifra radnika, ime, JMBG)
                 ──► Dodele        (koji broj kome pripada, po mesecu)
                 ──► Potrošnja     (osnovica PDV, parking, NZRD, ukupno, po mesecu)
                                            │
                        povezivanje broja sa zaposlenim (M-04)
                                            │
                                    OBUSTAVA (M-01)
                                            │
                                    CSV ──► obračun zarada
```

---

## M-04 — Povezivanje broja telefona sa zaposlenim

> Ovo je **preduslov** za obustavu. Ako broj nije povezan sa zaposlenim, obustava se
> ne može pripisati nikome.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Zaposleni“ uz dodelu; „Status veze“ kod korisnika |
| Tehnički naziv | `MobileAssignment.linked_employee`, `assignment_linked_employee()` |
| Putanja | [`mobilni/models.py:155`](../../../mobilni/models.py#L155), [`mobilni/withholdings.py:130`](../../../mobilni/withholdings.py#L130) |

### 2. Poslovna svrha

Broj telefona u izvoru operatera nosi **šifru radnika i ime**, ali ne i vezu sa
kadrovskom evidencijom IMS-a. Ovaj korak uspostavlja tu vezu i **jasno označava**
slučajeve u kojima veza nije pouzdana.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona |
|---|---|
| Šifra radnika iz izvora | `mobilni_mobileuser.employee_code` |
| Status veze | `mobilni_mobileuser.link_status` |
| Zaposleni (veza) | `mobilni_mobileuser.employee_id` |
| Šifra iz dodele | `mobilni_mobileassignment.source_employee_code` |
| Ime iz dodele | `mobilni_mobileassignment.source_full_name` |
| Zaposleni na dodeli | `mobilni_mobileassignment.employee_id` |

### 6. Tačan postupak

#### Statusi veze korisnika [P]

| Status | Značenje |
|---|---|
| `auto` | Automatski povezan |
| `manual` | Ručno povezan |
| `unmatched` | **Nije povezan** |
| **`non_employee`** | **Namerno označen kao nezaposleni** — ne povezuje se |
| `ambiguous` | Više mogućih zaposlenih |

#### Razrešavanje zaposlenog [P]

Redosled provere je strog:

```
 1. Dodela ima korisnika mobilnog?
       DA  ──► status je "non_employee"?  ──► NEMA zaposlenog (namerno)
            └─► korisnik ima vezu ka zaposlenom? ──► TAJ zaposleni
                                                └─► NEMA zaposlenog
 2. Dodela ima direktnu vezu ka zaposlenom? ──► TAJ zaposleni
 3. Inače ──► NEMA zaposlenog
```

> **[P] Bitno:** ako dodela ima korisnika mobilnog, **direktna veza `employee` na dodeli
> se ne gleda uopšte**. Korisnik mobilnog je merodavan.

#### Prikaz kada zaposleni nije pronađen [P]

| Podatak | Redosled traženja |
|---|---|
| Šifra | zaposleni → `source_employee_code` → `mobile_user.employee_code` |
| Ime | zaposleni → `mobile_user.full_name` → `source_full_name` |
| JMBG | zaposleni → `mobile_user.personal_number` → prazno |

> **[Z]** Podaci iz izvora se čuvaju i prikazuju čak i kada veza ne postoji, da se
> ne izgubi trag o tome kome je broj bio dodeljen.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Pet statusa veze | Potvrđeno | `mobilni/models.py:50-55` |
| `non_employee` sprečava povezivanje | Potvrđeno | `withholdings.py:134-135` |
| Korisnik mobilnog ima prednost nad direktnom vezom | Potvrđeno | `withholdings.py:132-137` |
| Podaci iz izvora se čuvaju kao rezerva | Potvrđeno | `withholdings.py:101-122` |

---

## M-02 — Izuzeci od parkinga

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Parking izuzeci“, kolona „Parking izuzet“ |
| Tehnički naziv | `parking_exempt_phone_numbers()`, `is_parking_exempt()` |
| Putanja | [`mobilni/withholdings.py:50`](../../../mobilni/withholdings.py#L50) |
| Adresa | `/mobilni/parking-izuzeci/` |

### 2. Poslovna svrha

Nekim zaposlenima parking plaća poslodavac. Za njihove brojeve se **iznos parkinga ne
obustavlja**, iako se pojavljuje na računu operatera.

### 6. Tačan postupak

**Normalizacija broja [P]:** pre poređenja, broj se svodi na same cifre:

| Ulaz | Rezultat |
|---|---|
| `381641234567` | `381641234567` |
| `381641234567.0` | `381641234567` — uklanja se `.0` iz Excel brojčane ćelije |
| `+381 64 123-4567` | `381641234567` |
| tekst bez cifara | ostaje kako jeste |

Ista normalizacija se primenjuje i pri upisu izuzetka (`MobileParkingExemption.save()`). [P]

**Provera [P]:**

> broj je izuzet ako se njegov normalizovan oblik nalazi u spisku izuzetaka

> **[P] Izuzetak nema period važenja.** Spisak je jedinstven po broju telefona i
> **važi za sve mesece**, uključujući i prošle obračune. Funkcija prima godinu i mesec,
> **ali ih ne koristi**. Vidi problem **P-30**.

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Normalizacija na same cifre | Potvrđeno | `withholdings.py:43-47` | — |
| Izuzetak je jedinstven po broju | Potvrđeno | `mobilni/models.py:273` | — |
| **Izuzetak nema period važenja** | **Potvrđeno** | `withholdings.py:50-51` | **P-30** |

---

## M-01 — Obustava po zaposlenom

> **Ovo je najvažniji obračun modula.** Njegov rezultat ulazi u obračun zarada.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Iznos obustave“ |
| Tehnički naziv | `calculate_withholding()` |
| Putanja | [`mobilni/withholdings.py:154`](../../../mobilni/withholdings.py#L154) |
| Adrese | `/mobilni/obustave/`, `/mobilni/obustave/zaposleni/`, izvoz `/mobilni/potrosnja/obracunski-mesec.csv` |

### 2. Poslovna svrha

Zaposleni dobija službeni broj telefona sa paketom koji plaća poslodavac.
**Sve iznad paketa zaposleni plaća sam** — taj iznos se obustavlja od zarade.

### 3. Korisnici rezultata

Administracija (priprema), **obračun zarada** (preuzima iznos), zaposleni (uvid).

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | JM | Obavezno | Ko unosi |
|---|---|---|---|---|---|---|
| Osnovica za PDV | Osnovica za PDV | `mobilni_mobileusage.vat_base` | `decimal(12,2)` | RSD | Da (podrazumevano 0) | Uvoz iz Excel-a |
| Parking | Parking | `mobilni_mobileusage.parking` | `decimal(12,2)` | RSD | Da (podrazumevano 0) | Uvoz iz Excel-a |
| NZRD | NZRD | `mobilni_mobileusage.nzrd` | `decimal(12,2)` | RSD | Da (podrazumevano 0) | Uvoz iz Excel-a |
| **Neto iznos paketa** | Paket neto | `mobilni_mobilepackage.net_amount` | `decimal(12,2)` | RSD | **Ne** | Uvoz iz Excel-a |
| Dodela broja | Paket, Korisnik | `mobilni_mobileassignment` | veza | — | Da | Uvoz iz Excel-a |
| Izuzeće od parkinga | Parking izuzet | `mobilni_mobileparkingexemption` | veza | — | Ne | **Administracija, ručno** |

> **[P] Šta se NE koristi:** kolona `total` („Ukupno za naplatu“) **ne ulazi** u obračun,
> iako je to iznos koji operater naplaćuje. Obustava se računa iz **osnovice za PDV**,
> parkinga i NZRD-a.

### 5. Poreklo podataka

```
 Excel operatera (potrošnja)  ──► mobilni_mobileusage
                                     vat_base, parking, nzrd
                                          │
 Excel operatera (dodele)     ──► mobilni_mobileassignment ──► paket ──► net_amount
                                          │
 Administracija (ručno)       ──► izuzeci od parkinga
                                          ▼
                                  OBUSTAVA (RSD)
                                          │
                                     CSV izvoz
                                          ▼
                                  obračun zarada
```

### 6. Tačan postupak obračuna

#### Korak 1 — koje stavke potrošnje uopšte ulaze [P]

Uzimaju se **samo** stavke potrošnje koje imaju dodelu sa **istim** periodom i brojem:

> potrošnja mora imati dodelu **i**
> `potrošnja.godina = dodela.godina` **i**
> `potrošnja.mesec = dodela.mesec` **i**
> `potrošnja.broj = dodela.broj`

> **[P] Posledica:** potrošnja za mesec u kome **nije uvezena dodela** potpuno
> **ispada iz obračuna**, bez upozorenja. Vidi problem **P-31**.

#### Korak 2 — parking [P]

> ako je broj u spisku izuzetaka → **parking = 0**
> inače → parking = `usage.parking`

#### Korak 3 — odbitak paketa [P]

| Slučaj | Odbitak |
|---|---|
| Broj je **`381637781481`** | **0** — paket se **ne odbija** |
| Paket nema neto iznos (`net_amount` prazan) | **Obustava se ne računa** → rezultat je **prazan** |
| Inače | Neto iznos paketa |

> **[P] Poseban broj upisan u kod:** `SPECIAL_PHONE_NUMBER = "381637781481"`.
> Za taj broj se **ceo iznos obustavlja**, bez odbitka paketa.
>
> **⚠ Potvrđeno kao greška (naručilac, 18.09.2026.):** broj **ne sme biti u kodu** —
> ovakav izuzetak pripada **bazi**, kao oznaka uz dodelu ili broj telefona.
> Vodi se kao problem **[P-34](../10-poznati-problemi.md#p-34--poseban-broj-telefona-upisan-u-kod-umesto-u-bazi)**.

#### Korak 4 — formula [P]

> **obustava = osnovica za PDV − neto iznos paketa + parking + NZRD**

Za poseban broj:

> **obustava = osnovica za PDV + parking + NZRD**

**Zaokruživanje [P]:** obračun **ne zaokružuje** — radi se sa punom decimalnom vrednošću.
Zaokruživanje se primenjuje **tek pri CSV izvozu**, na **ceo dinar**, `ROUND_HALF_UP`.

**Prazne vrednosti [P]:**

| Situacija | Rezultat |
|---|---|
| Nema dodele | Obustava je **prazna** (`None`) |
| Paket nema neto iznos | Obustava je **prazna** (`None`) |
| Nema paketa na dodeli | Obustava je **prazna** (`None`) |
| Osnovica, parking ili NZRD prazni | **Ne može se desiti** — podrazumevana vrednost je 0 |

> **[P] Prazno nije nula.** Razlika je namerna: prazno znači „nije obračunato“,
> a nula znači „nema šta da se obustavi“.

#### Korak 5 — zbir na ekranu [P]

> ukupno = zbir svih obustava koje **nisu prazne**

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `mobilni/withholdings.py` |
| Funkcije | `calculate_withholding()`, `withholding_amount_expression()`, `get_withholding_rows()` |
| SQL varijanta | `withholding_amount_expression()` — ista formula kao `Case`/`When` izraz |
| Ekran | `mobilni/views/mobile.py: MobileWithholdingReportView` |
| CSV izvoz | `export_employee_withholdings_csv()` |
| Testovi | `mobilni/tests.py` — 40 testova |

> **[P] Dve implementacije iste formule:** `calculate_withholding()` radi u Pythonu,
> `withholding_amount_expression()` isto u SQL-u. Obe moraju ostati usklađene.

### 8. Primer obračuna

> Ilustrativni primer, obračunski mesec **avgust 2026**.

| Broj | Osnovica PDV | Parking | NZRD | Paket | Neto paketa | Izuzet parking |
|---|---|---|---|---|---|---|
| 381641111111 | 2.400,00 | 300,00 | 0,00 | Biznis 1 | 1.800,00 | Ne |
| 381642222222 | 1.500,00 | 250,00 | 0,00 | Biznis 1 | 1.800,00 | **Da** |
| **381637781481** | 3.100,00 | 400,00 | 120,00 | Biznis 2 | 2.500,00 | Ne |
| 381643333333 | 2.000,00 | 0,00 | 0,00 | *(bez paketa)* | — | Ne |

**Obračun:**

| Broj | Račun | Obustava |
|---|---|---|
| 381641111111 | 2.400,00 − 1.800,00 + 300,00 + 0,00 | **900,00** |
| 381642222222 | 1.500,00 − 1.800,00 + **0,00** + 0,00 | **−300,00** |
| 381637781481 | 3.100,00 − **0,00** + 400,00 + 120,00 | **3.620,00** |
| 381643333333 | nema neto iznosa paketa | **prazno** |

**U CSV izvoz ulaze [P]:**

| Godina | Mesec | Šifra radnika | Iznos obustave |
|---|---|---|---|
| 2026 | 8 | 1234 | **900** |
| 2026 | 8 | 1235 | **−300** |
| 2026 | 8 | 1240 | **3620** |

> Red sa praznom obustavom **ne ulazi** u izvoz.
> Negativna obustava **ulazi** — vidi problem **P-31**.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Iznos koji se obustavlja od zarade zaposlenog za jedan mesec |
| Format na ekranu | Decimalan broj, RSD, pune decimale |
| **Format u izvozu** | **Ceo dinar**, `ROUND_HALF_UP` |
| Gde se čuva | **Nigde** — računa se pri svakom otvaranju |
| Kada se ponovo računa | Pri svakom otvaranju ekrana ili izvoza |
| Može li korisnik da ga izmeni | Posredno — izmenom dodele, paketa ili izuzetka od parkinga |
| Istorija | **Ne postoji** — izmena paketa menja i ranije obračunate mesece |

> **[Z] Rizik bez istorije:** ako se posle prenosa u zarade promeni neto iznos paketa,
> ekran će za isti mesec pokazati **drugi iznos** nego što je prosleđen. Nema traga
> o tome šta je prosleđeno.

### 10. Upotreba rezultata

| Korisnik | Šta preuzima | Odakle | Format |
|---|---|---|---|
| **Obračun zarada** | Šifra radnika i iznos | `/mobilni/potrosnja/obracunski-mesec.csv` | CSV: `Godina;Mesec;Šifra radnika;Iznos obustave` |
| Administracija | Detaljni pregled | `/mobilni/obustave/` | Ekran |

**Oblik CSV datoteke [P]:**

| Osobina | Vrednost |
|---|---|
| Razdvajač | **tačka-zarez** `;` |
| Kodiranje | **UTF-8 sa BOM** oznakom |
| Prelom reda | `CRLF` |
| Zaglavlje | `Godina;Mesec;Šifra radnika;Iznos obustave` |
| Obuhvat | **samo aktivni zaposleni** (izveštaj „Obustave zaposlenih“) |
| Izostavljeni redovi | Prazna obustava **i obustava jednaka nuli** |
| Iznos | Ceo dinar |

> **[N] Q3:** nije potvrđeno kako se CSV datoteka dalje unosi u obračun zarada —
> uvozom ili ručnim prepisivanjem — niti koja konta se koriste.

### 11. Kontrola i ručna provera

**Kontrolna formula:**

> obustava = osnovica za PDV − neto iznos paketa + parking + NZRD

| Provera | Kako |
|---|---|
| Iznos ne odgovara | Otvoriti detalj broja `/mobilni/brojevi/<broj>/` — vide se sve četiri veličine |
| Obustava je prazna | Proveriti da li dodela ima paket i da li paket ima neto iznos |
| Parking nije odbijen | Proveriti `/mobilni/parking-izuzeci/` |
| Zaposleni nedostaje u izvozu | Proveriti da li je aktivan i da li je broj povezan (M-04) |
| Zbir se ne slaže sa računom operatera | **Očekivano** — obustava nije ukupan račun, nego deo iznad paketa |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Potrošnja bez dodele za isti mesec | **Tiho ispada iz obračuna** | **P-31** |
| Paket bez neto iznosa | Obustava prazna, red se ne izvozi | Vidljivo |
| **Negativna obustava** | **Izvozi se kao negativan iznos** | **P-31** |
| Obustava tačno nula | **Ne izvozi se** | Namerno |
| Poseban broj `381637781481` | Paket se ne odbija | **P-34** |
| Izmena paketa posle prenosa u zarade | Ekran menja iznos za prošli mesec | Nema istorije |
| Zaposleni nije aktivan | Ne ulazi u izvoz za zarade | Namerno — vidi M-03 |
| Broj povezan sa `non_employee` | Ne ulazi u izvoz za zarade | Namerno |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje / problem |
|---|---|---|---|
| **Formula: osnovica PDV − paket + parking + NZRD** | Potvrđeno | `withholdings.py:169` | — |
| Kolona `total` se ne koristi | Potvrđeno | Nema upotrebe u `withholdings.py` | Potvrditi da je željeno |
| Poseban broj bez odbitka paketa | Potvrđeno | `withholdings.py:16, 161-162` | **P-34 — greška** |
| Prazan paket → prazna obustava | Potvrđeno | `withholdings.py:163-164` | — |
| Zaokruživanje tek pri izvozu, na ceo dinar | Potvrđeno | `views/mobile.py:925` | — |
| Nula se ne izvozi | Potvrđeno | `views/mobile.py:923` | — |
| **Potrošnja bez dodele ispada** | **Potvrđeno — problem** | `withholdings.py:55-60` | **P-31** |
| **Rezultat se nigde ne čuva** | Potvrđeno | Nema modela za obračun | **P-31** |
| Način prenosa u zarade | **Nepotvrđeno** | — | **Q3** |

---

## M-03 — Razvrstavanje zaposleni / bivši / nezaposleni

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Četiri izveštaja: „Detaljni“, „Zaposlenih“, „Bivših zaposlenih“, „Nezaposlenih“ |
| Tehnički naziv | `get_withholding_rows()`, `_is_former_employee_for_period()` |
| Putanja | [`mobilni/withholdings.py:252`](../../../mobilni/withholdings.py#L252) |

### 2. Poslovna svrha

Obustava se od zarade može naplatiti **samo aktivnom zaposlenom**. Za bivše zaposlene i
lica koja nisu u radnom odnosu naplata ide drugim putem, pa se izveštaji razdvajaju.

### 6. Tačan postupak

| Izveštaj | Uslov | Adresa |
|---|---|---|
| **Sve** | Bez filtera | `/mobilni/obustave/` |
| **Zaposleni** | Broj povezan sa zaposlenim **i zaposleni je aktivan** | `/mobilni/obustave/zaposleni/` |
| **Bivši zaposleni** | vidi pravilo ispod | `/mobilni/obustave/bivsi-zaposleni/` |
| **Nezaposleni** | Broj **nije** povezan ni sa jednim zaposlenim | `/mobilni/obustave/nezaposleni/` |

**Pravilo „bivši zaposleni“ [P]:**

```
 zaposleni ne postoji ILI je aktivan  ──► NIJE bivši
 inače:
    pronađi korisnika mobilnog (sa dodele, ili poslednjeg po ID-u za tog zaposlenog)
    ima li datum odlaska?
        DA  ──► bivši je ako je datum odlaska PRE prvog dana obračunskog meseca
        NE  ──► SMATRA SE BIVŠIM
```

> **[P]** Neaktivan zaposleni **bez** unetog datuma odlaska uvek se svrstava u bivše.
> Vidi problem **P-32**.

**Obuhvat izvoza za zarade [P]:** CSV se pravi **isključivo** iz izveštaja
„Obustave zaposlenih“ — dakle samo za **aktivne** zaposlene.

### 8. Primer

> Obračunski mesec: **avgust 2026** (prvi dan 01.08.2026.)

| Broj | Zaposleni | Aktivan | Datum odlaska | Izveštaj |
|---|---|---|---|---|
| …111 | Petrović | Da | — | **Zaposleni** |
| …222 | Jovanović | Ne | **15.07.2026.** | **Bivši** (odlazak pre 01.08.) |
| …333 | Nikolić | Ne | **20.08.2026.** | **Nije bivši** — odlazak u toku meseca |
| …444 | Marković | Ne | — | **Bivši** (nema datuma odlaska) |
| …555 | *(nije povezan)* | — | — | **Nezaposleni** |

> Red …333 nije ni u jednom od tri izveštaja osim „Sve“: nije aktivan zaposleni,
> a nije ni bivši po ovom pravilu. Vidi **P-32**.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Neaktivan, odlazak u toku obračunskog meseca** | **Nije ni u jednom pojedinačnom izveštaju** | **P-32** |
| Neaktivan bez datuma odlaska | Svrstan u bivše | **P-32** |
| Korisnik označen kao `non_employee` | Svrstan u nezaposlene | Namerno |
| Zaposleni ima više korisnika mobilnog | Uzima se **poslednji po ID-u** | **P-32** |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Četiri izveštaja i njihovi uslovi | Potvrđeno | `withholdings.py:280-285` | — |
| Bivši: odlazak pre prvog dana meseca | Potvrđeno | `withholdings.py:246-248` | — |
| Bez datuma odlaska → bivši | Potvrđeno | `withholdings.py:249` | **P-32** |
| Izvoz za zarade samo za aktivne | Potvrđeno | `views/mobile.py:910` | — |

---

## Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-30** | Izuzeće od parkinga **nema period važenja** — jednom upisan izuzetak menja i **već obračunate prošle mesece**. Funkcija prima godinu i mesec, ali ih ne koristi. | Srednja |
| **P-31** | Obustava se **nigde ne čuva** i računa se iznova pri svakom otvaranju. Nema traga o tome koji je iznos stvarno prosleđen u zarade. Uz to, potrošnja bez dodele za isti mesec **tiho ispada**, a negativna obustava se izvozi bez upozorenja. | **Visoka** |
| **P-32** | Razvrstavanje na bivše zaposlene ima tri rupe: neaktivan zaposleni sa datumom odlaska **u toku obračunskog meseca** ne ulazi ni u jedan pojedinačni izveštaj; neaktivan **bez** datuma odlaska uvek se smatra bivšim; kod više korisnika mobilnog uzima se poslednji po ID-u. | Srednja |
| **P-34** | **Poseban broj telefona upisan je u kod** umesto u bazu. Naručilac je potvrdio da je to greška: izuzetak od odbitka paketa mora biti **oznaka u evidenciji**, koju administracija održava bez izmene koda. | **Visoka** |

## Nova pitanja iz ovog poglavlja

| # | Pitanje | Status |
|---|---|---|
| **Q8** | Poseban tretman broja **381637781481** upisan je u kod. | ✔ **Rešeno (18.09.2026.):** to je **greška**. Izuzetak mora biti **u bazi**, ne u kodu. Vodi se kao problem **P-34**. |
| **Q28** | Obustava se računa iz **osnovice za PDV**, a ne iz kolone „Ukupno za naplatu“ (`total`). | ✔ **Potvrđeno ispravnim (18.09.2026.).** Formula `osnovica PDV − neto paketa + parking + NZRD` je željena. |
| **Q29** | Da li **negativna obustava** (kada je paket veći od potrošnje) treba da se prosleđuje u zarade kao potraživanje zaposlenog, ili da se tretira kao nula? | Otvoreno |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.6. Kadrovi](06-06-kadrovi.md) | Ocenjivanje i radne liste |
| [6.10. Isplate](06-10-isplate.md) | Virmani |
| [4. Baza podataka](../04-baza-podataka.md#411-mobilna-telefonija--mobilni) | Tabele mobilne telefonije |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema |
