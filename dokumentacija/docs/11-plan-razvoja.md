# 11. Plan razvoja

> **Za koga je ovo poglavlje:** uprava i programeri.
> Sadrži **postojeće planove** i **predloge koji proizlaze iz ovog pregleda**.
> Status tvrdnji: **[P]** potvrđeno, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 11.1. Šta je već isplanirano

U projektu postoje tri razrađena plana, nastala pre ove dokumentacije:

| Plan | Dokument | Stanje |
|---|---|---|
| **Centralna organizacija i dozvole (V2)** | [`plan-organizacije-i-dozvola-v2.md`](../plan-organizacije-i-dozvola-v2.md) | **Aktuelan plan za realizaciju** |
| Centralizacija organizacije i šifara posla | [`plan-centralizacije-organizacije.md`](../plan-centralizacije-organizacije.md) | Prethodna verzija, poslovna pravila i dalje važe |
| Prelazak Naplate na lokalni izvor | `naplata-lokalni-izvor-plan.md` (uklonjen, git `06f60c2`) | Delimično izvedeno |
| Nova Naplata — Potraživanja | `naplata-nova-aplikacija-plan.md` (uklonjen, git `06f60c2`) | **Izvedeno**, u paralelnom radu |

---

## 11.2. Centralna organizacija i dozvole (V2)

**Najveći planirani zahvat.** Puni tekst:
[`plan-organizacije-i-dozvola-v2.md`](../plan-organizacije-i-dozvola-v2.md).

### Zašto [Z]

Danas se organizaciona pripadnost i prava pristupa vode na **nedosledan način**:

| Nedostatak | Posledica | Problem |
|---|---|---|
| Dva mehanizma za centre | Pravo pristupa zavisi od ekrana | [P-19](10-poznati-problemi.md) |
| Nema istorije pripadnosti posla centru | Prošli izveštaji se menjaju | [P-44](10-poznati-problemi.md) |
| Flota mestimično koristi poslednju umesto istorijske dodele | Zbirovi po centrima se ne slažu | [P-05](10-poznati-problemi.md), [P-24](10-poznati-problemi.md) |

### Šta plan uvodi [P]

| Tema | Sadržaj |
|---|---|
| **Tri nivoa organizacije** | Centar → organizaciona jedinica → šifra posla |
| **Uloga zajedno sa obuhvatom** | Dozvola se dodeljuje **uz centar, OJ ili posao**, ne globalno |
| **Stalni identitet i istorija** | Šifra posla zadržava identitet i kroz promene naziva i centra |
| **Snimak na dokumentu** | Dokument pamti pripadnost **u trenutku nastanka** |
| **Sistematizacija** | Ko koga vodi i ko koga ocenjuje |
| **Poslovni Admin panel** | Dodela prava bez Django admina |
| **Efektivni pristup** | Ekran koji pokazuje **šta korisnik stvarno vidi** i zašto |
| **Deset koraka prelaska** | Sa kontrolom postojećih prava i mogućnošću povratka |

### Uticaj na postojeće obračune [Z]

Uvođenje istorije pripadnosti rešava **četiri zabeležena problema odjednom**:
P-05, P-24, P-44 i deo P-19.

### Stanje realizacije registra [P]

Razrada: [`plan-registra-sifara-posla.md`](../plan-registra-sifara-posla.md).

| Faza | Stanje |
|---|---|
| Faza 1 — registar (`organizacija`), uvoz, stablo, kontrolni izveštaj | Izvedeno; otvorena pitanja o šiframa `111111`, `432`, `vranj`, `vranjs` i `960001` |
| Faza 2, Flota — koraci 1–3 (veza `org_node`, popunjavanje, uporedni izveštaj) | Izvedeno 25.09.2026. **Čitanje iz registra (korak 4) nije uključeno** |
| Nova sinhronizacija (01:40) | Radi paralelno sa starom (`fetch_job_codes`, 01:30): osvežava registar, povezuje Flotu i poredi staro i novo. Staru ne menja |
| Faza 2, ostali moduli | Nije počelo |

**Redosled gašenja [Z]:** stara i nova sinhronizacija rade zajedno sve vreme. Moduli prelaze
na čitanje iz registra **jedan po jedan**, svaki tek kad mu uporedni izveštaj prođe. Stara
sinhronizacija i `OrganizationalUnit` gase se **poslednji**, kad nijedan modul više ne čita
staro polje — do tada na njih pokazuju strani ključevi putnih naloga, dodela i nabavke.

**Odluke 25.09.2026.:** centri poslovnog i naučnog bloka su `2` i `3` (knjiženja ih vode kao
jedinice `20` i `30`); naučna šifra je `3` + šifra radnika iz Kadrova + broj projekta i **deo
je bloka 3** (naučni projekat je jedinica, šifra je učešće radnika, radnik je povezan sa Kadrovima); nazivi centara i jedinica su po Pravilniku o
organizaciji od 18.04.2024. (latinicom). Uporedni izveštaj Flote na produkcionim podacima
(proba) se poklapa do dinara u svih 9 centara, bez ijednog nepovezanog zapisa.

---

## 11.3. Gašenje nasleđene Naplate

### Stanje [P]

| | Naplata (nasleđeno) | Potraživanja |
|---|---|---|
| Izvor | Nasleđeni pogledi, pri svakom otvaranju | Lokalne tabele uz sinhronizaciju |
| Brzina | Spora | Brza |
| Istorija stanja | **Nema** | Objavljeni snimci |
| Kontrole | Nema | **Šest kontrolnih zbirova** |
| Revizorski trag | Nema | `CollectionAudit` |
| Status | **Gasi se** | Zamenjuje je |

**Odluka naručioca (18.09.2026.) [P]:** Naplata se **ne dokumentuje**; sav novi rad ide
u Potraživanja.

### Šta ostaje da se uradi [Z]

| # | Korak |
|---|---|
| 1 | Potvrditi da su **sve** funkcije Naplate pokrivene, uključujući **pravnu službu** ([Q12](../00-inventar-i-plan-dokumentacije.md)) |
| 2 | Odrediti **datum gašenja** ([Q34](obracuni/06-08-potrazivanja.md)) |
| 3 | Uporediti saldo dva sistema na isti datum — dok oba rade |
| 4 | Ukloniti meni Naplate iz interfejsa |
| 5 | Ukloniti aplikaciju `naplata` iz `INSTALLED_APPS` i njene rute |
| 6 | Odlučiti šta sa nasleđenim pogledima koje je koristila samo Naplata |

> **[P] Do gašenja ne menjati pravilo starosnih razreda** — promena bi onemogućila
> poređenje dva sistema. Vidi [P-35](10-poznati-problemi.md).

---

## 11.4. Preuzimanje definicija nasleđenih pogleda

**Dogovoreno (18.09.2026.):** DDL stiže **od ponedeljka**. [P]

### Zašto je važno [Z]

**37 objekata baze** čita se bez ijednog podatka o tome kako su napravljeni.
Za **11 izveštaja Flote** formula postoji **isključivo u bazi** — [P-27](10-poznati-problemi.md).

### Redosled preuzimanja [Z]

| Prioritet | Objekti | Zašto |
|---|---|---|
| **1** | `fleet_tro_svi`, `fleet_tro_goriva_m`, `fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`, `tro_zarade`, `fleet_dobavljaci`, `fleet_magacin_rez`, `kasko_rate` | Izveštaji koji idu upravi, formula potpuno u bazi |
| **2** | `fleet_servisi`, `fleet_trebovanja`, `fleet_potrazivanje_ddor`, `fleet_zatvoren_putni`, `vrednost_vozila`, `lizing_kamate`, `sif_pos_trenutno`, `v_organizationalunit`, `fleet_otpis` | Izvori sinhronizacija Flote |
| **3** | `nbv_preuzete_EUF`, `nbv_EUF_stavke`, `nbv_roba`, `nbv_sif_pos_par` | Nabavka |
| **4** | `hr_employee` | Kadrovi |
| **5** | `posao` (na `PUTGEO-SERVER`) | Potraživanja i Finansije |

### Šta uraditi kada stigne [Z]

1. Smestiti DDL u `dokumentacija/sql/` — **pod kontrolu verzija**.
2. Dopuniti poglavlje [6.5.5](obracuni/06-05-flota-izvestaji.md) stvarnim formulama.
3. Dopuniti [4.12](04-baza-podataka.md#412-nasleđeni-objekti-baze-dbo).
4. **Odrediti vlasnika** koji odobrava izmene tih pogleda.

---

## 11.5. Prioriteti iz registra problema

**50 uočenih problema, od toga 20 rešeno (18–19.09.2026.). U Floti je od 21 problema rešeno 16.**

| Dan | Rešeno |
|---|---|
| 18.09. | P-10, P-13, P-14 A-C, P-21, P-22, P-26, P-36, P-46 |
| 19.09. | **P-01** (tajne), **P-02** (prosečna potrošnja), **P-04** (brzina), **P-05** (centar, za V-07), **P-06** (premija polise), **P-07** (kamata lizinga), **P-09** (vozila bez troška) |

Predlog redosleda za ostale — po tome **šta daje pogrešan broj**:

### Prvo — pogrešan poslovni rezultat

| # | Problem | Zašto prvo |
|---|---|---|
| [P-23](10-poznati-problemi.md) | Lizing samo u mesecu početka | Izveštaj ne pokazuje mesečni trošak |
| [P-08](10-poznati-problemi.md) | Operativni lizing razmazan | Rata od 50.000 ulazi kao 1.370. **Traži proveru podataka pre izmene koda** — vidi **Q45** |
| [P-31](10-poznati-problemi.md) | Obustava mobilnih se nigde ne čuva | Nema traga šta je prosleđeno u zarade |
| [P-33](10-poznati-problemi.md) | Virman skraćuje podatke i ne čuva poslatu datoteku | Tiho skraćivanje iznosa i naziva |

> **[Z] Olakšica:** za P-23 **ispravno rešenje već postoji u kodu**, u drugom modulu —
> isti postupak koji je 19.09.2026. primenjen na P-06 i P-07.

> **Rešeno 19.09.2026.:** ~~P-02~~ (prosečna potrošnja), ~~P-06~~ (premija polise),
> ~~P-07~~ (kamata lizinga). Sva tri su davala **pogrešan poslovni broj**.

### Drugo — bezbednost i trag

| # | Problem |
|---|---|
| [P-01](10-poznati-problemi.md) | Lozinke, `SECRET_KEY` i `DEBUG = True` u repozitorijumu |
| [P-48](10-poznati-problemi.md) | **Imena, adrese i brojevi računa 329 osoba u git istoriji** — rešava se istim postupkom kao P-01 |
| [P-34](10-poznati-problemi.md) | **Poslovni izuzetak upisan u kod** — potvrđena greška |
| [P-31](10-poznati-problemi.md) | Obustava mobilnih se nigde ne čuva |
| [P-33](10-poznati-problemi.md) | Virman skraćuje podatke i ne čuva poslatu datoteku |
| [P-45](10-poznati-problemi.md) | Modul Menice nema migracije |

### Treće — doslednost

P-05, P-24, P-44 (istorijska pripadnost — rešava ih **plan V2**),
P-19 (dva mehanizma za centre), P-28 (dva obračuna sati).

### Četvrto — infrastruktura i održavanje

P-15 (jedan radnik), P-16 (zaključavanje popušta), P-27 (DDL 11 izveštaja Flote — prvi
deo preuzet 18.09.2026., videti [`ddl-nasledjenih-pogleda/`](../ddl-nasledjenih-pogleda/README.md)).

### Rešeno 18.09.2026.

| # | Šta je bilo |
|---|---|
| [P-36](10-poznati-problemi.md) | Zbir faktura Nabavke sabirao je fakturu jednom po stavci |
| [P-46](10-poznati-problemi.md) | Zapis goriva bez vaučera ili količine nestajao je sa **svih** ekrana goriva |
| [P-13](10-poznati-problemi.md) | Superuser je dobijao 403 na statistici centra |
| [P-14](10-poznati-problemi.md) | Otpisana vozila, prosečna starost i dijakritici u kategorijama (A, B, C; **D ostaje**) |
| [P-26](10-poznati-problemi.md) | Izveštaj goriva za upravu čitao je OMV bez prečišćavanja |
| [P-10](10-poznati-problemi.md) | Napomena o maloj kilometraži poredila je period sa godišnjim pragom |
| [P-22](10-poznati-problemi.md) | Nekorišćene zavisnosti u `requirements.txt` |
| [P-21](10-poznati-problemi.md) | 95 radnih fajlova u repozitorijumu (arhiva, snimci ekrana, jednokratne skripte, dnevnici) |

**Novo otkriveno pri ispravkama:** [P-47](10-poznati-problemi.md) — ključ za duplikate
OMV transakcija ne obuhvata iznos ni valutu. **Za proveru nad stvarnim podacima.**

---

## 11.6. Predlozi koji proizlaze iz ovog pregleda

Ovo **nisu** obaveze — predlozi za razmatranje. [Z]

### A) Poslovna pravila u bazu, ne u kod

| Sada u kodu | Predlog |
|---|---|
| Poseban broj telefona | Oznaka u evidenciji — **potvrđeno kao greška** ([P-34](10-poznati-problemi.md)) |
| Pragovi troška po kilometru | Šifarnik sa ekranom za održavanje ([P-11](10-poznati-problemi.md)) |
| Konta toka gotovine | Šifarnik ili barem provera pokrivenosti ([P-42](10-poznati-problemi.md)) |
| Podaci platioca u virmanu | Konfiguracija ([P-33](10-poznati-problemi.md)) |
| PIB za pretragu registra menica | Konfiguracija ([P-41](10-poznati-problemi.md)) |
| Vreme 16:00 za službeni izlazak | Podešavanje ([Q27](obracuni/06-06-kadrovi.md)) |

### B) Čuvati ono što je poslato

Tri rezultata idu izvan sistema, a **nijedan se ne čuva** [Z]:

| Rezultat | Predlog |
|---|---|
| **Virman** | Tabela generisanih virmana sa sadržajem ili otiskom, iznosom i spiskom naloga |
| **Obustave mobilnih** | Tabela obračunatih obustava po mesecu, **zaključana** pri izvozu |
| Ocena zaposlenog | **Već rešeno** — nepromenljiv snimak sa revizijama |

> **[Z] Obrazac za preuzimanje:** ocenjivanje i Potraživanja to rade ispravno —
> nepromenljiv snimak, revizije, revizorski trag.

### C) Tiho gubljenje podataka

Nekoliko mesta **tiho izostavlja** podatke [Z]:

| Gde | Šta se gubi | Predlog |
|---|---|---|
| Izveštaj goriva po šifri posla | Transakcije bez vozila | Prikazati broj izostavljenih |
| Trošak po kilometru | Vozila sa troškom ≤ 0 | Prikazati sa oznakom ([P-09](10-poznati-problemi.md)) |
| Obustave mobilnih | Potrošnja bez dodele | Upozorenje ([P-31](10-poznati-problemi.md)) |
| Virman | Skraćeni nazivi | Greška umesto sečenja ([P-33](10-poznati-problemi.md)) |
| UF fakture | Prekinute veze | Prebrojati i prijaviti ([P-37](10-poznati-problemi.md)) |

> **[Z] Dobar uzor:** izveštaj „Gorivo IMS“ za upravu **prebrojava** stavke bez vozila,
> bez šifre posla i bez iznosa. Isti pristup vredi primeniti svuda.

### D) Paralelnost pozadinskih poslova

Drugi Windows servis vezan samo za red `sync`, a postojeći ograničen na `selenium`
([P-15](10-poznati-problemi.md)). [Z]

### E) Upozorenja kojih nema

| Nedostaje | Osnov |
|---|---|
| Dospeo servis po kilometraži | `service_interval` postoji, **ne koristi se** ([Q23](obracuni/06-05-flota-izvestaji.md)) |
| Predmet nabavke zaglavljen bez fakture | ([Q37](obracuni/06-09-nabavka.md)) |
| Razlika zbira stavki i vrednosti predmeta | ([Q36](obracuni/06-09-nabavka.md)) |
| Ugovor pred istekom | Postoji za polise, ne i za ugovore |

---

## 11.7. Otvorena pitanja koja čekaju odgovor

**45 pitanja** iz celog pregleda. Najvažnija:

| # | Pitanje | Bez odgovora ne može |
|---|---|---|
| **Q1** | DDL nasleđenih pogleda | Dokumentovati 11 izveštaja |
| **Q2** | Ko je odgovoran za koji modul | Potvrditi korisnike u dokumentaciji |
| **Q3** | **Kako rezultati ulaze u knjiženje i koja konta** | Opisati upotrebu rezultata |
| Q5 | Koji mehanizam za centre je merodavan | Rešiti P-19 |
| Q13 | Da li je primećena besmislena prosečna potrošnja | Odlučiti o ispravci P-02 |
| Q18 | Poreklo pragova troška po km | Potvrditi ili izmeniti |
| Q28 | Osnovica obustave mobilnih | ✔ **Potvrđeno ispravnim** |
| Q8 | Poseban broj telefona | ✔ **Potvrđeno kao greška** |
| Q34 | Datum gašenja Naplate | Planirati prelazak |
| Q44 | Kako su nastale tabele Menica | Rešiti P-45 |

Potpun spisak: uz svako poglavlje obračuna i u
[inventaru, poglavlje 14](../00-inventar-i-plan-dokumentacije.md).

---

## 11.8. Šta NE treba menjati

> Zabeleženo da se dobra rešenja ne bi slučajno pokvarila. [Z]

| Rešenje | Zašto valja |
|---|---|
| **Prečišćavanje OMV transakcija** | Bez njega su zbirovi višestruko uvećani |
| **Kontrolni zbirovi Finansija i Potraživanja** | Otkrivaju nepotpuno čitanje pre objave |
| **Nepromenljiva ocena sa revizijama** | Uzor za sve što ide u zarade |
| **Objavljeni snimci Potraživanja** | Omogućavaju uvid u ranije stanje |
| **`TrafficCard.for_plate()`** | Namerno odbija da pogađa |
| **Označavanje umesto brisanja** | Nestali zapis se ne gubi |
| **Prazno se razlikuje od nule** | Sprečava pogrešno tumačenje |
| **Izuzimanje zatvaranja u Finansijama** | Namerno i objašnjeno |

---

## 11.9. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Šta je tačno uočeno? | [10. Poznati problemi](10-poznati-problemi.md) |
| Kako sistem sada radi? | [2. Arhitektura](02-arhitektura.md) |
| Kratak pregled za upravu | [Pregled IMS ERP-a](uprava/pregled-ims-erp-a.md) |
| Postojeći plan organizacije | [`plan-organizacije-i-dozvola-v2.md`](../plan-organizacije-i-dozvola-v2.md) |
