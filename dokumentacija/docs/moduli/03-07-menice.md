# 3.7. Menice

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Menice** |
| Tehnički naziv | Django aplikacija `menice` |
| Adresa | `/menice/` |
| Bočni meni | `sidebar_menice.html` |

> **[P] Zamka:** tabele se zovu **`menica`** i **`ulazna_menica`** — **bez prefiksa
> aplikacije**.

---

## 2. Poslovna namena

Vodi evidenciju **sredstava obezbeđenja u obliku menica**:

| Vrsta | Značenje |
|---|---|
| **Izlazne menice** | Menice koje je **IMS izdao** — obaveza IMS-a |
| **Ulazne menice** | Menice koje je IMS **primio od partnera** — obezbeđenje za IMS |

Za izlazne menice podaci se mogu **preuzeti iz Registra menica NBS**, umesto ručnog
prepisivanja.

---

## 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Finansije** | Prate obaveze po izdatim menicama, vode fizičku lokaciju |
| **Pravna služba** | Povezuju menice sa ugovorima |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Izlazne menice** | Podaci iz registra NBS + ručne dopune (broj ugovora, OJ, lokacija, napomena) |
| **Ulazne menice** | Sopstvena evidencija sa jedinicom vrednosti |
| **Preuzimanje iz NBS** | Pretraga registra po PIB-u dužnika, sa avalistima |
| **Uvoz iz Excel-a** | Za ulazne i izlazne menice |
| **Fizička lokacija** | Centar ili blagajna |
| **Interni status** | Aktivna, obrisana, nepoznat |

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| Spisak menica po vrsti | `/menice/<vrsta>/` (`izlazna` ili `ulazna`) |
| Detalj menice | `/menice/<vrsta>/<id>/` |
| Nova menica | `/menice/<vrsta>/nova/` |
| **Ažuriranje iz registra NBS** | `/menice/izlazna/azuriraj/` |
| **Ulazne menice** | `/menice/ulazne/` |
| Nova ulazna menica | `/menice/ulazne/nova/` |

---

## 6. Podaci koje korisnik unosi

### Izlazne menice — ručne dopune [P]

| Podatak | Napomena |
|---|---|
| Broj i datum ugovora | Veza sa poslovnim osnovom |
| Organizaciona jedinica | |
| **Fizička lokacija** | **Centar** ili **blagajna** |
| Napomena | |
| **Interni status** | Aktivna / obrisana / nepoznat |

> **[P] Ove dopune preuzimanje iz NBS-a NE prepisuje** — ažuriraju se samo polja
> koja dolaze iz registra.

### Ulazne menice — sve unosi korisnik [P]

Serijski broj, osnov izdavanja, datum prijema, **jedinica vrednosti**, iznos,
partner, broj i datum našeg ugovora, ugovor važi do, lokacija, šifra centra.

---

## 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| **Izlazne menice** | `https://webappcenter.nbs.rs/PnWebApp` | **Ručno** |

Preuzima se 20 polja: dužnik, serijski broj, datumi, iznos i valuta, izdavalac, vrsta,
osnov izdavanja, banka, status i **avalisti**.

---

## 8. Tabele i kolone

Detaljno: [4.10. Menice](../04-baza-podataka.md#410-menice--menice). **2 tabele.**

| Tabela | Uloga | Ključ prepoznavanja |
|---|---|---|
| **`menica`** | Izlazne i ulazne menice iz registra | serijski broj + datum registracije (+ redni broj) |
| **`ulazna_menica`** | Ulazne menice, sopstvena evidencija | serijski broj |

---

## 9. Spoljni izvori

| Izvor | Način | Rizik |
|---|---|---|
| **Registar menica NBS** | Razlaganje HTML stranice (`requests` + `BeautifulSoup`) | **Promena stranice zaustavlja preuzimanje** ([P-41](../10-poznati-problemi.md)) |

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`menice/models.py`](../../../menice/models.py) |
| **Preuzimanje iz NBS** | [`menice/scraper.py`](../../../menice/scraper.py) |
| Obrada i uvoz | [`menice/services.py`](../../../menice/services.py) |
| Ekrani | [`menice/views.py`](../../../menice/views.py) |
| Uvoz iz Excel-a | `management/commands/import_ulazne_menice_excel.py`, `import_izlazne_menice_excel.py` |

> **[P] Modul uopšte nema direktorijum `migrations/`.** Modeli **nisu** označeni sa
> `managed = False`, pa Django očekuje da njima upravlja — ali bez migracija ih **ne može
> stvoriti**. Tabele `menica` i `ulazna_menica` su nastale izvan uobičajenog postupka.
> Vodi se kao problem **[P-45](../10-poznati-problemi.md#p-45--modul-menice-nema-migracije)**.

---

## 11–12. Ulaz, izlaz i veze

| Smer | Šta |
|---|---|
| **Ulaz** | Registar NBS; Excel uvoz; ručni unos |
| **Izlaz** | Spiskovi na ekranu |

| Modul | Veza |
|---|---|
| **Ugovori** | `ContractMenicaLink` — veza ugovora i menice; brisanje povezane menice je **zabranjeno** |

---

## 13. Izveštaji i analize

| Oznaka | Naziv | Poglavlje |
|---|---|---|
| U-03 | Preuzimanje menica iz registra NBS | [6.11](../obracuni/06-11-ugovori-i-menice.md) |
| U-04 | Povezivanje menica sa ugovorima | [6.11](../obracuni/06-11-ugovori-i-menice.md) |

---

## 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `menice` | **Samo ovaj modul** — usklađuje se automatski |
| `pravna` | Povezivanje sa ugovorima (kroz modul Ugovori) |
| `uprava` | Sve |

---

## 15. Validacije i kontrole

| Kontrola | Ponašanje |
|---|---|
| Zapis bez serijskog broja ili datuma registracije | **Preskače se** pri preuzimanju |
| Prepoznavanje postojeće menice | Serijski broj + datum registracije (+ redni broj) |
| **Ručni podaci** | **Ne prepisuju se** pri preuzimanju |
| Decimalni zapis iznosa | Prepoznaju se **oba** oblika (`1.234,56` i `1,234.56`) |
| Datumi | Oblici `DD.MM.GGGG`, `DD/MM/GGGG`, `GGGG-MM-DD` |
| Brisanje povezane menice | **Zabranjeno** |

---

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| **Jedinica vrednosti = `PROCENAT`** | **Iznos nije novčani** — sabiranje kolone bez provere jedinice daje besmislen zbir |
| Menica uklonjena iz registra | **Ostaje** u evidenciji; koristi se interni status |
| Dve menice sa istim ključem | Uzima se **prva po ID-u** |
| Promena izgleda stranice NBS-a | Preuzimanje prestaje da radi |
| PIB nije zadat | Koristi se **podrazumevani PIB IMS-a iz koda** |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Treba li preuzimanje iz NBS-a da bude zakazano | **Q39** |
| 2 | **Kako su nastale tabele `menica` i `ulazna_menica` bez migracija** | **Q44** / [P-45](../10-poznati-problemi.md) |
| 3 | Ko i kada menja fizičku lokaciju menice | **[N]** |
| 4 | Šta znači „ulazna menica“ u tabeli `menica` naspram tabele `ulazna_menica` | **Q45** |

> **[N] Q45:** model `Menica` ima vrstu `ulazna`, a postoji i **zasebna tabela**
> `ulazna_menica` sa drugačijim skupom polja. Nije zabeleženo kada se koja koristi.

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.11](../obracuni/06-11-ugovori-i-menice.md) | U-03 i U-04 |
| [3.6. Ugovori](03-06-ugovori.md) | Povezani modul |
| [4.10](../04-baza-podataka.md#410-menice--menice) | Tabele |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-41 |
