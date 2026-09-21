# Put od registra do jedinstvene organizacije i dozvola

Datum: **21.09.2026.** · Status: **predlog za odobrenje**

Nastavak na [plan registra šifara posla](plan-registra-sifara-posla.md), čija je Faza 1
**urađena i puštena na produkciju**. Ovaj dokument odgovara na tri pitanja: kojim redom
povezivati module, kako uskladiti povezivanje sa sinhronizacijom, i kada i kako preći na
nove dozvole — a da se ništa ne polomi.

> Status tvrdnji: **[P]** izmereno nad produkcijom 21.09.2026., **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Zatečeno stanje — izmereno, ne pretpostavljeno

### 1.1 Obuhvat korisnika

| | |
|---|---|
| Korisnika | **323**, svi aktivni, 3 superkorisnika |
| Obuhvat preko **tekstualnog** `allowed_center_codes` | **311** |
| Obuhvat preko **M2M** `allowed_centers` | **3** |
| Oba istovremeno | **0** |
| **Bez ikakvog obuhvata** | **9** |

> **[P] Tekstualno polje je stvarni mehanizam, M2M je praktično mrtav.** Svaki plan koji
> polazi od `allowed_centers` promašuje 311 od 323 korisnika.

### 1.2 Vrednosti obuhvata — ista pokvarena šifra kao u šifarniku

| Vrednost | Korisnika | Stanje |
|---|---|---|
| `41` | 93 | odgovara centru u registru |
| `43` | 128 | odgovara |
| `44`, `42`, `82`, `81`, `70`, `60`, `50`, `11`, `20`, `30`, `83` | 105 | odgovaraju |
| **`2`** | **5** | **nema takvog centra — skraćeno od `20`** |
| **`3`** | **3** | **nema takvog centra — skraćeno od `30`** |

> **[P] Ovo je isti defekt koji je registar već rešio.** `FinanceJob.center` piše `2` za
> centar `20` i `3` za `30`; isti skraćeni oblik završio je i u obuhvatu korisnika.
> **Trinaest od petnaest vrednosti mapira se jedan na jedan**, a preostale dve pogađaju
> **osam korisnika**.

Uz to, u podacima ima i `'2,'` sa zarezom na kraju i niz oblika
`'41, 42, 43, 44, 50, 60, 70, 81, 82, 83, 2, 3, 20, 30,'` [P]. Parsiranje to trpi, ali je
podatak neuredan.

### 1.3 Prazan obuhvat znači suprotne stvari

| Modul | Ponašanje bez obuhvata |
|---|---|
| **Flota** (`CenterMixin.allow_if_no_scope = True`) | vidi **sve** |
| **Finansije** (`visible_scope`) | vidi **ništa** (`queryset.none()`) |
| **Potraživanja** (`scoped`) | vidi **ništa** |

Devet korisnika je u tom stanju [P]. Šest su stvarni ljudi sa ulogama
(Uprava+Nabavka, Pravna služba, Garaža, Nabavka, Blagajna), jedan je superkorisnik, a tri
su ostaci testiranja (`tmp-putni`, dva `render-check-phone-filte…`).

### 1.4 Uloge

| | |
|---|---|
| Uloga | **17** |
| Kodova dozvola | **448** |
| Dodela uloga–dozvola | **880** |
| Korisnika bez ijedne uloge | **3** |

| Uloga | Korisnika | Dozvola |
|---|---|---|
| Zaposleni | **300** | 7 |
| Sekretarijat | 10 | 58 |
| Pravna služba | 4 | 63 |
| Uprava | 3 | **448 — sve** |
| Pregled | 3 | 85 |
| Mobilni | 3 | 33 |
| Garaža | 1 | 84 |
| *Render check*, *Render check 2* | 1 + 1 | 1 + 1 |

> **[Z]** Raspodela je zdrava: jedna široka uloga za sve zaposlene i nekoliko uskih.
> Dve „Render check" uloge su ostaci testiranja i brišu se uz proveru.

---

## 2. Glavni zaključak koji određuje redosled

**Registar nije samo pomoćni šifarnik — on je ispravka istog defekta koji kvari i dozvole.**

Obuhvat korisnika i finansijski šifarnik dele istu grešku (`2` umesto `20`, `3` umesto
`30`). Registar je već utvrdio tačne centre iz prefiksa šifre, a knjiženja su ga potvrdila.
Zato prelazak dozvola na registar **nije samo preseljenje** nego i otklanjanje greške.

Ali to znači i obrnuto: **dok se obuhvat ne prevede na registar, ne sme se menjati
značenje praznog obuhvata**, jer bi 9 korisnika odjednom izgubilo ili dobilo pristup.

---

## 3. Redosled — tri odvojene stvari, ne jedna

Ključ je razdvojiti ono što se obično radi zajedno:

| | Šta se radi | Vidljivo korisniku | Rizik |
|---|---|---|---|
| **A** | dodaje se veza na registar | ne | nikakav |
| **B** | modul **čita** iz registra | da, ali isti rezultat | srednji |
| **C** | **dozvole** prelaze na registar | da, menja se ko šta vidi | **visok** |
| **D** | uklanja se legacy | ne | nizak, ali nepovratan |

To je u suštini ono što si i predložio — paralelno uvođenje, pa dozvole, pa uklanjanje
legacyja. Razlika je što se **B i C ne smeju raditi u istom koraku za isti modul**.

---

## 4. Faza A — veze, ništa ne čita

Svakom modelu se dodaje **opciono** `org_node`, pored postojećeg polja. Postojeće polje
ostaje merodavno i i dalje se upisuje.

| Redosled | Modul | Kako se veže | Obim |
|---|---|---|---|
| 1 | **Flota** | `OrganizationalUnit` → `LegacyOrgLink` (veza već postoji) | 204 dodele, 3.651 nalog |
| 2 | **Nabavka** | isto | 242 predmeta, 1.164 veze |
| 3 | **Finansije** | `job_code` → `ExternalOrgMapping` | 147.953 reda |
| 4 | **Potraživanja** | isto | 22.000 redova |

Kod 1 i 2 posao je gotov pre nego što počne: `LegacyOrgLink` već povezuje **144**
zapisa `fleet.OrganizationalUnit` sa čvorovima [P]. Treba samo dodati kolonu i popuniti je
iz te tabele.

**Uslov za kraj faze:** za svaki modul izveštaj koji kaže koliko redova je povezano,
koliko nije i zašto. Nepovezan red **ostaje nepovezan**, ne dobija nasumičan čvor.

---

## 5. Faza B — čitanje, modul po modul

Redosled ovde vodi **veličina štete ako se pogreši**, ne cena povezivanja:

| Redosled | Modul | Zašto tim redom |
|---|---|---|
| **1** | **Nabavka** | Najmanji: 242 predmeta, uloga „Nabavka" ima **2 korisnika**. Ako obrazac ne valja, vidi se na najmanjem uzorku. |
| **2** | **Finansije** | Registar je **napravljen iz njenih podataka**, a usaglašavanje je već dokazano: 145.305 od 147.953 kodiranih redova se razrešava [P]. Obuhvat je već strog (`none()` bez obuhvata), pa se semantika ne menja. |
| **3** | **Potraživanja** | Zavisi od Finansija; isti tip veze, 100% poklapanje šifara [P]. |
| **4** | **Flota** | **Poslednja.** Svih 323 korisnika je dodiruje, i jedina je gde prazan obuhvat znači „vidi sve". Svaka greška ovde pogađa sve. |

> **[Z] Ovo se razlikuje od ranije preporuke.** U planu registra sam predložio Flotu prvu,
> jer je veza najjeftinija. Merenje obuhvata to menja: Flota je **najjeftinija za
> povezivanje, ali najskuplja za grešku**. Povezivanje i čitanje zato idu različitim redom.

**Uslov za prelazak svakog modula:** uporedni izveštaj — isti period, isti korisnik, stari
i novi put, **iznosi identični do dinara**. Razlika koja se ne objasni zaustavlja prelazak.

**Pravilo bez izuzetka:** unutar jednog modula nema režima „stari ILI novi". Delimično
prebačen modul je gori od neprebačenog.

---

## 6. Faza C — dozvole

Najosetljivije, jer dodiruje 311 korisnika. Ide u četiri koraka, i **prvi se može uraditi
odmah, nezavisno od svega**.

### C0. Ispraviti osam skraćenih obuhvata — odmah

`2` → `20`, `3` → `30`, kod **8 korisnika** [P]. Uz to očistiti zareze na kraju.

To je **ispravka podatka, ne migracija**. Trenutno ti korisnici imaju obuhvat koji ne
odgovara nijednom centru, pa u Finansijama i Potraživanjima verovatno ne vide ništa
**[Z] — treba proveriti sa njima pre ispravke**, jer će posle nje videti svoj centar.

### C1. Odlučiti šta znači prazan obuhvat

Devet korisnika. Danas u Floti vide sve, u Finansijama ništa. Odluka je poslovna, ne
tehnička. Dok se ne donese, **ponašanje se ne dira**.

Tri su ostaci testiranja i brišu se odvojeno.

### C2. Prevod obuhvata na registar, u senci

Napraviti `obuhvat korisnika → čvor registra`, pa pustiti **obe provere paralelno**: stara
odlučuje, nova se samo računa i beleži. Izveštaj po korisniku: šta bi novi sistem dodao,
šta oduzeo.

**Uslov za prelazak:** svaka razlika je ili razrešena ili izričito zabeležena kao
namerna. **Nema tihih proširenja pristupa.**

### C3. Prelazak

Po modulu, istim redom kao Faza B, i **tek pošto je taj modul već prešao na čitanje iz
registra**. Prvo čitanje, pa dozvole — nikad obrnuto, jer se inače ne zna da li je razlika
u podacima ili u pravima.

---

## 7. Faza D — uklanjanje legacyja

Tek kad svi moduli čitaju iz registra i koriste nove dozvole:

1. `allowed_center_codes` i `allowed_centers` prestaju da se čitaju — **ostaju u bazi**
   tokom perioda stabilizacije, kao izvor za povratak.
2. `CenterMixin` i `visible_scope` se svode na jednu zajedničku uslugu.
3. Stare kolone se brišu **poslednje**, i to zasebnom odlukom.

`OrganizationalUnit` se **ne briše** — 3.651 putni nalog i 1.164 veze faktura drže FK na
njega [P], a brojevi dokumenata izvedeni iz centra moraju ostati nepromenjeni.

---

## 8. Usklađivanje sa sinhronizacijom

Jedno pravilo rešava većinu: **za svako polje tačno jedan postupak koji ga upisuje.**

| Podatak | Ko ga upisuje posle prelaska |
|---|---|
| Šifra, naziv, roditelj | uvoz iz `FinanceJob` (`uvezi_organizaciju`) |
| **Aktivnost** | **nalaz o obrtu** (`oznaci_neaktivne`) — odluka 21.09.2026. |
| Profitnost | uvoz iz `FinanceJob` |
| Veze dokumenata | povezivanje po modulu, u paketima |
| **Prava pristupa** | **isključivo Admin** — nikad sinhronizacija |

> **[P] Ovo već radi.** Nalaz o obrtu i uvoz su usklađeni: uvoz poštuje nalaz, pa ponovno
> pokretanje daje **0 novih verzija**. Isti obrazac se primenjuje na svako naredno polje.

Prava se **ne osvežavaju iz ERP-a**. Izvor može predložiti nov posao ili promenu
zaposlenja; pristup je zasebna odluka.

---

## 9. Zamke koje su već vidljive

| Zamka | Zašto | Kada puca |
|---|---|---|
| **Promena šifre pravi nov posao** | uvoz prepoznaje posao po šifri; mapa staro → novo ne postoji | čim se šifra promeni u izvoru |
| **Skraćeni centri `2`/`3`** | isti defekt u šifarniku i u obuhvatu | pri prevodu obuhvata |
| **Prazan obuhvat** | suprotno značenje u Floti i Finansijama | pri ujednačavanju |
| **`111111`** | šifra zaključka, 5,41 mlrd, nije posao | ako ikad uđe u stablo |
| **Nauka** | matrica osoba × projekat, ne hijerarhija | ako se pokuša ugurati u stablo |
| **Brojevi dokumenata iz centra** | `PutniNalog`, `ProcurementCase` | ako se centar preimenuje |

Prva je jedina koja **nema rešenje u kodu** i traži potvrđenu mapu staro → novo. Do tada
je zabeležena testom (`test_changing_the_code_in_the_source_creates_a_new_node`) da ne
prođe neprimetno.

---

## 10. Šta se može uraditi odmah, bez ijedne odluke

1. **C0** — ispraviti 8 skraćenih obuhvata (uz prethodnu proveru sa tim korisnicima).
2. **Faza A za Flotu i Nabavku** — veza već postoji kroz `LegacyOrgLink`, treba je samo
   iskoristiti. Ništa ne čita, ništa se ne vidi.
3. Obrisati dve „Render check" uloge i tri testna korisnika.
4. Pokrenuti `sync_permission_codes` da `organizacija:stablo` i `organizacija:cvor`
   postanu dodeljive — inače registar vidi samo superkorisnik.

Sve ostalo čeka odgovore iz odeljka 6.
