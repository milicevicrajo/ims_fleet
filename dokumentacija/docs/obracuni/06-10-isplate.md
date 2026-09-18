# 6.10. Isplate — virmani

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](../10-poznati-problemi.md).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [I-02](#i-02--kontrole-naloga-pre-virmana) | Kontrole naloga pre virmana | — |
| [I-01](#i-01--generisanje-datoteke-virmana) | **Generisanje datoteke virmana** | **P-33** |
| [I-03](#i-03--konverzija-virmana-u-json) | Konverzija virmana u JSON | — |

> **Ovo je jedini obračun u sistemu čiji rezultat ide direktno u banku.**
> Greška ovde znači pogrešnu isplatu.

---

## Zajednička osnova

Modul **nema nijednu sopstvenu tabelu**. [P] Radi isključivo nad putnim nalozima
(`fleet_putninalog`) i proizvodi **datoteku za elektronsko bankarstvo**.

```
 Putni nalozi (akontacija, RSD, nisu stornirani, nije rađen virman)
                          │
                   kontrole ispravnosti (I-02)
                          │
              datoteka fiksne širine 180 znakova (I-01)
                          │
                   preuzimanje i slanje u banku
                          │
              oznaka „virman odrađen“ na nalogu
```

### Podaci platioca upisani u kod [P]

| Podatak | Vrednost |
|---|---|
| Račun platioca | `205000000001445485` |
| Naziv platioca | `Institut IMS a.d.` |
| Mesto platioca | `Beograd` |
| Svrha plaćanja | `NEOPOREZIVA PRIMANJA ZAPOSLENIH` |
| Šifra plaćanja | `241` |
| Model | `000` |
| Oznaka zaglavlja | `Multi E_BANK0` |

> **[P]** Sve navedeno je upisano u `isplate/services/virman.py` i **ne može se menjati
> kroz interfejs**. Promena računa ili naziva firme zahteva izmenu koda.

---

## I-02 — Kontrole naloga pre virmana

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Poruke o greškama pri pokušaju generisanja |
| Tehnički naziv | `validate_order_for_virman()` |
| Putanja | [`isplate/services/virman.py:126`](../../../isplate/services/virman.py#L126) |

### 2. Poslovna svrha

Sprečava da u banku ode nalog sa **pogrešnim ili nepotpunim podacima** — pogrešan broj
računa znači isplatu pogrešnom licu, a duplirani virman dvostruku isplatu.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona |
|---|---|---|
| Broj naloga | Broj naloga | `fleet_putninalog.order_number` |
| Storniran | Storniran | `fleet_putninalog.storniran` |
| Virman odrađen | Virman odrađen | `fleet_putninalog.virman_generated` |
| Valuta akontacije | Valuta akontacije | `fleet_putninalog.advance_payment_currency` |
| Zaposleni | Zaposleni | `fleet_putninalog.employee_id` |
| **Partija (tekući račun)** | Partija | `fleet_employee.account_number` |
| Iznos akontacije | Isplata/Akontacija | `fleet_putninalog.advance_payment` |

### 6. Tačan postupak

Sve provere se izvršavaju, pa se **sve greške prijavljuju zajedno** — korisnik ne mora
da ispravlja jednu po jednu. [P]

| # | Provera | Poruka |
|---|---|---|
| 1 | Nalog **nije storniran** | *„<broj>: nalog je storniran.“* |
| 2 | Virman **nije već odrađen** (osim uz izričito ponovno generisanje) | *„<broj>: virman je vec odradjen.“* |
| 3 | Valuta je **RSD** | *„<broj>: valuta mora biti RSD.“* |
| 4 | Nalog ima **IMS zaposlenog** (ne spoljno lice) | *„<broj>: nalog nema IMS zaposlenog.“* |
| 5 | Zaposleni ima **račun** | *„<broj>: zaposlenom nedostaje racun.“* |
| 6 | Račun ima **tačno 18 cifara** | *„<broj>: racun mora imati 18 cifara.“* |
| 7 | Iznos je **veći od nule** | *„Iznos mora biti veci od nule.“* |
| 8 | Broj naloga ima **redni broj posle crtice** | *„<broj>: nedostaje broj putnog naloga.“* |
| 9 | Redni broj nije duži od **21 znaka** | *„<broj>: redni broj putnog naloga je duzi od 21 karaktera.“* |

> **[P] Provere 5 i 6 se isključuju međusobno** — ako računa nema, ne proverava se dužina.

**Obuhvat spiska na ekranu [P]:** prikazuju se samo nalozi koji **nisu stornirani**,
imaju **akontaciju veću od nule** i valutu **RSD**. Filter „status“ razdvaja naloge
za koje virman **nije** rađen od onih za koje **jeste**.

### 8. Primer

| Nalog | Storniran | Virman | Valuta | Zaposleni | Račun | Iznos | Ishod |
|---|---|---|---|---|---|---|---|
| 43/2026-17 | Ne | Ne | RSD | Petrović | 18 cifara | 12.000,00 | **Prolazi** |
| 43/2026-18 | **Da** | Ne | RSD | Jovanović | 18 cifara | 8.000,00 | Odbijen — storniran |
| 43/2026-19 | Ne | Ne | **EUR** | Nikolić | 18 cifara | 300,00 | Odbijen — valuta |
| 43/2026-20 | Ne | Ne | RSD | *(spoljno lice)* | — | 5.000,00 | Odbijen — nema IMS zaposlenog |
| 43/2026-21 | Ne | Ne | RSD | Marković | **16 cifara** | 9.000,00 | Odbijen — račun nije 18 cifara |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Devet provera, sve greške zajedno | Potvrđeno | `virman.py:126-148` |
| Račun mora imati tačno 18 cifara | Potvrđeno | `virman.py:139-140` |
| Samo RSD | Potvrđeno | `virman.py:133-134` |
| Spoljna lica se ne isplaćuju virmanom | Potvrđeno | `virman.py:135-136` |

---

## I-01 — Generisanje datoteke virmana

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Isplata neoporezivih primanja“ |
| Tehnički naziv | `build_virman_file()` |
| Putanja | [`isplate/services/virman.py:195`](../../../isplate/services/virman.py#L195) |
| Adresa | `/isplate/` |
| Dozvola | Uloga **Blagajna** |

### 2. Poslovna svrha

Pravi datoteku koju blagajna učitava u elektronsko bankarstvo, da se akontacije za
službena putovanja isplate zaposlenima **bez ručnog kucanja naloga**.

### 3. Korisnici rezultata

Blagajna. Posredno: banka i zaposleni.

### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Uloga u datoteci |
|---|---|---|
| Broj računa zaposlenog | `fleet_employee.account_number` | Račun primaoca |
| Ime i prezime | `fleet_employee.original_full_name` ili prikazno ime | Naziv primaoca |
| **Opština boravka** | `fleet_employee.residence_municipality` | Mesto primaoca |
| Iznos akontacije | `fleet_putninalog.advance_payment` | Iznos |
| Broj naloga | `fleet_putninalog.order_number` | Poziv na broj |
| **Datum virmana** | bira korisnik | Datum plaćanja |

### 5. Poreklo podataka

```
 Sekretarijat ──► putni nalog (akontacija, zaposleni, broj naloga)
 Kadrovska    ──► zaposleni (partija, opština boravka)
 Blagajna     ──► izbor naloga + datum virmana
                          ▼
                 datoteka .txt (cp1250)
                          ▼
                  elektronsko bankarstvo
```

### 6. Tačan postupak obračuna

#### Oblik datoteke [P]

| Osobina | Vrednost |
|---|---|
| Dužina svakog reda | **tačno 180 znakova** |
| Kodiranje | **cp1250** (neprevodivi znakovi se zamenjuju) |
| Prelom reda | `CRLF`, i na poslednjem redu |
| Zaglavlje | **dva reda** |
| Detalj | jedan red po nalogu |
| Naziv datoteke | `Virman-putni-nalozi-GGGGMMDD-HHMMSS.txt` |

#### Prvi red zaglavlja [P]

| Pozicija | Širina | Sadržaj |
|---|---|---|
| 1 | 18 | Račun platioca |
| 19 | 35 | Naziv platioca |
| 54 | 10 | Mesto platioca |
| 64 | 6 | **Datum virmana** u obliku `DDMMGG` |
| 168 | 13 | `Multi E_BANK0` |

#### Drugi red zaglavlja [P]

| Pozicija | Širina | Sadržaj |
|---|---|---|
| 1 | 18 | Račun platioca |
| 19 | 35 | Naziv platioca |
| 54 | 10 | Mesto platioca |
| 64 | 15 | **Ukupan iznos u parama**, 15 cifara sa vodećim nulama |
| 79 | 5 | **Broj naloga**, 5 cifara sa vodećim nulama |
| 180 | 1 | `9` |

#### Detaljni red [P]

| Pozicija | Širina | Sadržaj |
|---|---|---|
| 1 | 18 | **Račun primaoca** — samo cifre |
| 19 | 35 | **Naziv primaoca** — velikim slovima, bez dijakritika |
| 54 | 10 | **Mesto primaoca** — opština boravka, velikim slovima |
| 64 | 25 | Model `000` |
| 89 | 35 | `NEOPOREZIVA PRIMANJA ZAPOSLENIH` |
| 125 | 5 | Kontrola `00000` |
| 131 | 3 | Šifra plaćanja `241` |
| 136 | 34 | **Poziv na broj** (vidi ispod) |
| 173 | 8 | **Datum plaćanja** u obliku `DDMMGG01` |

#### Poziv na broj — posebno pravilo [P]

Poziv na broj je spoj dve vrednosti, ukupno 34 znaka:

> **13 znakova:** iznos **u parama**, sa vodećim nulama
> **21 znak:** **redni broj putnog naloga**, poravnat **udesno**

Redni broj se dobija iz broja naloga — **deo posle poslednje crtice**:

| Broj naloga | Redni broj u pozivu |
|---|---|
| `43/2026-17` | `17` |
| `12/2026-235` | `235` |

> **[Z] Zašto je iznos i u pozivu na broj:** banka tako može da uporedi iznos naloga sa
> iznosom u pozivu na broj kao dodatnu kontrolu.

#### Pretvaranje iznosa [P]

> iznos u parama = iznos zaokružen na **2 decimale** (`ROUND_HALF_UP`) × 100, kao **ceo broj**

| Iznos | U parama |
|---|---|
| 12.000,00 | `1200000` |
| 12.345,67 | `1234567` |
| 12.345,675 | `1234568` — zaokruženo naviše |

Pojedinačan iznos mora biti **veći od nule**; ukupan iznos ne sme biti negativan. [P]

#### Čišćenje teksta [P]

Naziv i mesto primaoca prolaze kroz:

1. Sažimanje razmaka u jedan.
2. Zamenu srpskih slova: `č`→`c`, `ć`→`c`, `š`→`s`, `ž`→`z`, `đ`→`dj`
   (i velika slova, `Đ`→`DJ`).
3. Uklanjanje svih preostalih znakova koji nisu ASCII.
4. Prevođenje u **velika slova** (samo naziv primaoca).

> **[P]** Mesto primaoca se takođe prevodi u velika slova, ali **posle** čišćenja.
> Ako zaposleni nema unetu opštinu boravka, koristi se **`Beograd`**.

#### Skraćivanje [P]

Svaka vrednost duža od svoje širine se **skraćuje bez upozorenja**.
Naziv primaoca duži od 35 znakova biće odsečen.

#### Posle generisanja [P]

Na svakom obuhvaćenom nalogu se upisuje:

| Polje | Vrednost |
|---|---|
| `virman_generated` | `True` |
| `virman_generated_at` | Trenutak generisanja |
| `virman_generated_by` | Korisnik |

**Ponovno generisanje** je moguće samo uz izričit izbor („Dozvoli ponovno generisanje“). [P]

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `isplate/services/virman.py` |
| Funkcije | `build_virman_file()`, `build_header_lines()`, `build_detail_line()`, `validate_order_for_virman()` |
| Provera dužine | `_record_to_string()` — prekida ako red nije tačno 180 znakova |
| Ekran | `isplate/views.py: IsplataNeoporezovanihView` |
| Testovi | `isplate/tests.py` — 20 testova |

### 8. Primer obračuna

> Ilustrativni primer. Datum virmana **15.09.2026.**, dva naloga.

| Nalog | Zaposleni | Račun | Opština | Iznos |
|---|---|---|---|---|
| 43/2026-17 | Petrović Miloš | `160000012345678901` | Novi Beograd | 12.000,00 |
| 43/2026-18 | Đurić Željka | `205000098765432109` | Čukarica | 8.500,50 |

**Ukupno:** 20.500,50 RSD = **2050050 para**, **2 naloga**.

**Prvi red zaglavlja** (skraćeno):

```
205000000001445485Institut IMS a.d.                  Beograd   150926 …  Multi E_BANK0
```

**Drugi red zaglavlja** (skraćeno):

```
205000000001445485Institut IMS a.d.                  Beograd   00000000205005000002 …9
                                                               └──15 cifara──┘└─5─┘
```

**Detaljni red za prvi nalog** (delovi):

| Pozicija | Vrednost |
|---|---|
| 1–18 | `160000012345678901` |
| 19–53 | `PETROVIC MILOS` (dopunjeno razmacima) |
| 54–63 | `Novi Beogr` — **skraćeno na 10 znakova** |
| 89–123 | `NEOPOREZIVA PRIMANJA ZAPOSLENIH` |
| 131–133 | `241` |
| 136–169 | `0001200000` + `000` + 19 razmaka + `17` |
| 173–180 | `15092601` |

**Detaljni red za drugi nalog:**

| Pozicija | Vrednost |
|---|---|
| 19–53 | `DJURIC ZELJKA` — `Đ`→`DJ`, `Ž`→`Z` |
| 54–63 | `Cukarica` — `Č`→`C` |
| 136–169 | `0000850050` + … + `18` |

> Uočite: mesto „Novi Beograd“ ima 12 znakova i **skraćuje se na „Novi Beogr“**,
> bez ikakvog upozorenja. Vidi problem **P-33**.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Nalog banci za isplatu akontacija |
| Format | `.txt`, fiksna širina, cp1250 |
| Gde se čuva | **Datoteka se ne čuva** — preuzima je korisnik |
| Trag u sistemu | Na svakom nalogu: da je virman rađen, kada i ko |
| Može li se ponoviti | Da, uz izričit izbor |
| Istorija sadržaja | **Ne postoji** — ne čuva se šta je tačno poslato |

> **[Z] Rizik:** ako se datoteka izgubi ili se posle generisanja promeni iznos na nalogu,
> ne postoji način da se utvrdi šta je poslato banci. Postoji samo oznaka **da jeste**.

### 10. Upotreba rezultata

| Korak | Ko | Šta |
|---|---|---|
| 1 | Blagajna | Bira naloge i datum virmana, preuzima datoteku |
| 2 | Blagajna | Učitava datoteku u elektronsko bankarstvo |
| 3 | Banka | Izvršava plaćanja |
| 4 | Zaposleni | Prima akontaciju na tekući račun |

> **[N] Q3:** nije potvrđeno da li se isplata posle vraća u sistem. Postoji zaseban
> zadatak koji u 12:30 puni polje **„Isplaćeno“** iz `dbo.fleet_zatvoren_putni`, ali
> veza sa ovim virmanom nije uspostavljena u kodu. [P]

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Ukupan iznos | Drugi red zaglavlja, pozicije 64–78, u parama — podeliti sa 100 |
| Broj naloga | Drugi red zaglavlja, pozicije 79–83 |
| Broj redova u datoteci | Mora biti `2 + broj naloga` |
| Dužina reda | **Svaki** red mora imati tačno 180 znakova |
| Iznos pojedinačnog naloga | Pozicije 136–148, u parama |
| Redni broj naloga | Pozicije 149–169, poravnat udesno |
| Račun primaoca | Pozicije 1–18, uporediti sa partijom zaposlenog |

**Kontrolna formula:**

> zbir iznosa iz svih detaljnih redova (pozicije 136–148) = iznos iz zaglavlja (64–78)

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Nijedan nalog nije izabran | *„Izaberi bar jedan putni nalog.“* | Ispravno |
| Datum virmana nije izabran | *„Izaberi datum virmana.“* | Ispravno |
| **Naziv primaoca duži od 35 znakova** | **Skraćuje se bez upozorenja** | **P-33** |
| **Mesto duže od 10 znakova** | **Skraćuje se bez upozorenja** | **P-33** |
| Zaposleni bez opštine boravka | Koristi se `Beograd` | **P-33** |
| Iznos nula ili negativan | Odbija se | Ispravno |
| Red nije tačno 180 znakova | **Prekida se greškom** pre nastanka datoteke | Ispravno |
| Ponovno generisanje | Moguće uz izričit izbor | Ispravno |
| Znak van cp1250 | Zamenjuje se | Ispravno |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje / problem |
|---|---|---|---|
| Red je tačno 180 znakova | Potvrđeno | `virman.py:10, 64-66` | — |
| Kodiranje cp1250 | Potvrđeno | `virman.py:49` | — |
| Dva reda zaglavlja i njihove pozicije | Potvrđeno | `virman.py:151-169` | — |
| Pozicije detaljnog reda | Potvrđeno | `virman.py:182-192` | — |
| Poziv na broj: 13 cifara iznosa + 21 znak rednog broja | Potvrđeno | `virman.py:97-111` | — |
| Iznos u parama, `ROUND_HALF_UP` | Potvrđeno | `virman.py:83-87` | — |
| Preslovljavanje srpskih slova | Potvrđeno | `virman.py:26-39, 70-76` | — |
| Podrazumevano mesto je Beograd | Potvrđeno | `virman.py:120-124` | — |
| **Skraćivanje bez upozorenja** | **Potvrđeno — problem** | `virman.py:56-60` | **P-33** |
| **Sadržaj datoteke se ne čuva** | **Potvrđeno** | Nema modela | **P-33** |
| Podaci platioca upisani u kod | Potvrđeno | `virman.py:12-23` | **Q30** |

---

## I-03 — Konverzija virmana u JSON

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Konverter“ |
| Tehnički naziv | `convert_virman_txt_to_internal_json()` |
| Putanja | [`isplate/services/converters.py:123`](../../../isplate/services/converters.py#L123) |
| Adresa | `/isplate/konverter/` |

### 2. Poslovna svrha

Pretvara **postojeću virman datoteku** (fiksna širina, 180 znakova) u **JSON** oblik,
za sistem koji očekuje takav zapis.

> **[N] Q31:** nije potvrđeno koji sistem koristi ovaj JSON. Nazivi polja
> (`DebtorBankAccount`, `CreditorCodeModel`, `UrgentPayment`) upućuju na drugo
> bankarsko rešenje, ali to nije zabeleženo u kodu.

### 4. Ulazni podaci

Datoteka `.txt` u jednom od kodiranja: **cp1250**, **UTF-8 sa BOM** ili **UTF-16**.
Redosled provere je upravo takav. [P]

### 6. Tačan postupak

**Provere [P]:**

| Provera | Poruka |
|---|---|
| Kodiranje je prepoznatljivo | *„TXT fajl nije u podrzanom encoding-u.“* |
| Ima bar 3 reda (2 zaglavlja + 1 detalj) | *„TXT mora imati dva header reda i bar jedan detaljni red.“* |
| **Svaki** red ima tačno 180 znakova | *„Svi redovi moraju imati 180 karaktera. Neispravni redovi: …“* (nabraja prvih 10) |
| Zaglavlje sadrži račun od 18 cifara | *„Header ne sadrzi ispravan racun duznika.“* |
| Poziv na broj ima bar 15 znakova | *„Poziv na broj je prekratak.“* |

Prazni redovi se izostavljaju pre provere. [P]

**Preslikavanje polja [P]:**

| Polje u JSON-u | Izvor — pozicije u redu |
|---|---|
| `CreditorBankAccount` | 1–18, samo cifre |
| `CreditorName` | 19–53 |
| `CreditorAddress` | 54–63 |
| `DebtorCode` | 67–88 |
| `PaymentBasis` | 89–123 |
| `PaymentCode` | 131–133, kao ceo broj |
| `Amount` | poziv na broj, prvih 13 znakova, **podeljeno sa 100** |
| `CreditorCodeModel` | poziv na broj, znakovi 14–15, kao ceo broj |
| `CreditorCode` | poziv na broj, od 16. znaka |
| `ExpectedPaymentDate` | 173–180, `DDMMGG` → **`GGGG-MM-DD`** |
| `DebtorBankAccount` | **iz prvog reda zaglavlja**, pozicije 1–18 |
| `UrgentPayment` | **uvek `True`** |
| `DebtorCodeModel`, `ExternalId`, `UserGroupName` | uvek prazno |
| `UserTags`, `Comment` | uvek prazan tekst |

**Pretvaranje iznosa [P]:** vrednost u parama deli se sa 100; ako je rezultat ceo broj,
zapisuje se kao **ceo broj**, inače kao **decimalan**.

**Godina [P]:** dvocifrena godina se tumači kao **2000 + GG**.

**Naziv izlazne datoteke [P]:** naziv ulazne, sa nastavkom `.json`.

### 8. Primer

**Ulaz — detaljni red** (delovi):

| Pozicije | Vrednost |
|---|---|
| 1–18 | `160000012345678901` |
| 19–53 | `PETROVIC MILOS` |
| 131–133 | `241` |
| 136–169 | `0001200000` + `97` + `1234567` |
| 173–180 | `15092601` |

**Izlaz:**

```json
{
    "PaymentBasis": "NEOPOREZIVA PRIMANJA ZAPOSLENIH",
    "PaymentCode": 241,
    "Amount": 12000,
    "DebtorBankAccount": "205000000001445485",
    "CreditorName": "PETROVIC MILOS",
    "CreditorBankAccount": "160000012345678901",
    "CreditorCodeModel": 97,
    "CreditorCode": "1234567",
    "UrgentPayment": true,
    "ExpectedPaymentDate": "2026-09-15"
}
```

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Red nije 180 znakova | Prekida se, nabraja prvih 10 neispravnih redova |
| Nepoznato kodiranje | Prekida se |
| **Sve konverzije su „hitne“** | `UrgentPayment` je **uvek `True`** |
| Iznos u pozivu na broj nije broj | *„Neispravan iznos u pozivu na broj: …“* |
| Neispravan datum | *„Neispravan datum placanja: …“* |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Tri podržana kodiranja, tim redom | Potvrđeno | `converters.py:30` | — |
| Preslikavanje pozicija u polja | Potvrđeno | `converters.py:102-120` | — |
| `UrgentPayment` je uvek `True` | Potvrđeno | `converters.py:114` | Potvrditi da je željeno |
| Godina se tumači kao 2000 + GG | Potvrđeno | `converters.py:72` | — |
| **Koji sistem koristi ovaj JSON** | **Nepotvrđeno** | — | **Q31** |

---

## Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-33** | Virman datoteka **skraćuje predugačke vrednosti bez upozorenja** (naziv primaoca preko 35, mesto preko 10 znakova), a **sadržaj poslate datoteke se nigde ne čuva**. Ako se posle generisanja promeni iznos na nalogu, ne postoji način da se utvrdi šta je poslato banci. | **Visoka** |

## Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q30** | Račun platioca, naziv firme i šifra plaćanja **upisani su u kod**. Da li treba da budu podesivi, imajući u vidu da promena računa firme zahteva izmenu i isporuku koda? |
| **Q31** | Koji sistem koristi JSON iz konvertera i da li je `UrgentPayment = true` za **sve** naloge ispravno? |
| **Q32** | Zadatak u 12:30 puni polje „Isplaćeno“ iz `dbo.fleet_zatvoren_putni`, ali nema veze sa generisanim virmanom. Da li se isplata po virmanu negde potvrđuje u sistemu? |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.6. Kadrovi](06-06-kadrovi.md) | Ocenjivanje i radne liste |
| [6.7. Mobilna telefonija](06-07-mobilni.md) | Obustave |
| [4. Baza podataka](../04-baza-podataka.md#446-putni-nalozi) | Putni nalozi |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema |
