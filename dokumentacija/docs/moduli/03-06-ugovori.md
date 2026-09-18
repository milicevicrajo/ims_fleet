# 3.6. Ugovori i partneri

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Ugovori** |
| Tehnički naziv | Django aplikacija `ugovori` |
| Adresa | `/ugovori/` |
| Bočni meni | `sidebar_ugovori.html` |

---

## 2. Poslovna namena

Vodi **poslovni odnos sa partnerom od prvog zahteva do isteka ugovora**:

> zahtev → ponuda → ugovor → aneksi → dokumenta → sredstva obezbeđenja

Uz to je **centralni šifarnik partnera** za ceo sistem — Nabavka, Potraživanja i Menice
koriste iste partnere.

---

## 3. Korisnici modula

| Korisnik | Šta radi | Uloga |
|---|---|---|
| **Pravna služba** | Vodi ugovore, anekse, garancije, veze sa menicama | `pravna` |
| **Sekretarijat** | Evidentira zahteve i ponude | `pravna` (dodeljeno) |
| **Služba nabavke** | Bira dobavljača i ugovor uz predmet nabavke | `nabavka` |
| **Komercijala** | Prati ponude i zahteve | **[N]** |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Partneri** | Pravna lica, fizička lica, banke; domaći i strani; **provera u APR-u** |
| **Zahtevi** | Ispitivanje, usluga, izlazak na teren, konsultacija, ostalo |
| **Ponude** | Naša ponuda i ponuda data nama; vrednost, valuta, rok važenja |
| **Ugovori** | Glavni ugovor i aneksi; tip, vrednost, period, status |
| **Dokumenta** | Prilozi uz ugovor, sa originalnim nazivom datoteke |
| **Stranke** | Ko je kupac, prodavac, zakupac, izvođač, garant… |
| **Garancije** | Bankarske garancije sa periodom i statusom |
| **Veze sa menicama** | Ugovor ↔ menica (izlazna ili ulazna) |

### Tipovi vrednosti ugovora [P]

`fixed` (fiksna), `hourly` (po radnom satu), `monthly` (mesečno),
`man_month` (čovek mesec), `unit` (po jedinici), `undefined` (bez definisane vrednosti).

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Partneri** | `/ugovori/partneri/` |
| Detalj partnera | `/ugovori/partneri/<id>/` |
| **Provera partnera u APR-u** | `/ugovori/partneri/<id>/apr-update/` |
| Paketna APR provera | `/ugovori/partneri/sync-apr/start/` |
| **Sinhronizacija iz Finansija** | `/ugovori/partneri/sync-finansije/` |
| Tipovi ugovora | `/ugovori/tipovi/` |
| Zahtevi | `/ugovori/zahtevi/` |
| Ponude | `/ugovori/ponude/` |
| **Ugovori** | `/ugovori/` |
| Detalj ugovora | `/ugovori/<id>/` |
| **Novi aneks** | `/ugovori/<id>/aneks/novi/` |
| Dokumenta uz ugovor | `/ugovori/<id>/dokumenti/dodaj/` |
| Menice uz ugovor | `/ugovori/<id>/menice/dodaj/` |
| Garancije uz ugovor | `/ugovori/<id>/garancije/dodaj/` |
| Štampa spiska | `/ugovori/stampaj/` |
| Izvoz u Excel | `/ugovori/export-excel/` |

---

## 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| Partner: naziv, tip, rezidentnost, PIB, matični broj, JMBG, adresa, kontakt | Pravna služba |
| Zahtev: broj, datum, tip, predmet, centar, status, fajl | Sekretarijat |
| Ponuda: broj, datum, smer, tip, vrednost, valuta, rok važenja, status | Sekretarijat |
| **Ugovor: broj, naslov, predmet, datumi, vrednost, tip vrednosti, valuta, status** | Pravna služba |
| Aneks uz glavni ugovor | Pravna služba |
| Dokumenta uz ugovor | Pravna služba |
| Stranke i njihove uloge | Pravna služba |
| Garancije | Pravna služba |
| Veze sa menicama | Pravna služba |

---

## 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| **Partneri** | `dbo.partneri` (nasleđeni šifarnik) | **Ručno**, paketno |
| **Status u APR-u i poslovno ime** | `openapi.apr.gov.rs` | **Ručno** |

---

## 8. Tabele i kolone

Detaljno: [4.9. Ugovori](../04-baza-podataka.md#49-ugovori--ugovori). **8 tabela.**

| Tabela | Uloga |
|---|---|
| `ugovori_partner` | Partner; veza sa starim sistemom je `external_sif_par` |
| `ugovori_contract_type` | Šifarnik tipova ugovora |
| `ugovori_business_request` | Zahtev |
| `ugovori_offer` | Ponuda |
| **`ugovori_contract`** | Ugovor i aneks (`kind`, `parent_contract`) |
| `ugovori_contract_document` | Dokument uz ugovor |
| `ugovori_contract_party` | Stranka ugovora |
| `ugovori_contract_guarantee` | Garancija |
| `ugovori_contract_menica_link` | Veza sa menicom |

---

## 9. Spoljni izvori

| Izvor | Namena | Status |
|---|---|---|
| `dbo.partneri` | Šifarnik partnera | Kolone poznate |
| **`https://openapi.apr.gov.rs/api/opendata/companies`** | Status privrednog subjekta | Javni skup, bez prijave |

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`ugovori/models.py`](../../../ugovori/models.py) |
| **Sinhronizacija partnera** | [`ugovori/services.py`](../../../ugovori/services.py) |
| **APR provera** | [`ugovori/apr_openapi.py`](../../../ugovori/apr_openapi.py) |
| Ekrani | [`ugovori/views.py`](../../../ugovori/views.py) |
| Uvoz ugovora iz Excel-a | `management/commands/import_contracts_excel.py` |

---

## 11–12. Ulaz, izlaz i veze sa modulima

| Modul | Veza |
|---|---|
| **Nabavka** | Partner kao dobavljač; osnovni i kupovni ugovor uz predmet |
| **Flota** | Ugovor o lizingu (`Lease.contract`), ugovor o finansiranju (`VehicleHolding.financing_contract`) |
| **Mobilni** | Ugovor uz paket (`MobilePackage.contract`) |
| **Menice** | Veza ugovora i menice |
| **Potraživanja** | `FinancePartnerIdentity.partner` → partner |

Izlaz: štampa spiska ugovora, izvoz u Excel.

---

## 13. Izveštaji i analize

| Oznaka | Naziv | Poglavlje |
|---|---|---|
| U-01 | Provera statusa partnera u APR-u | [6.11](../obracuni/06-11-ugovori-i-menice.md) |
| U-02 | Sinhronizacija partnera iz finansija | [6.11](../obracuni/06-11-ugovori-i-menice.md) |
| U-04 | Povezivanje menica i garancija | [6.11](../obracuni/06-11-ugovori-i-menice.md) |

---

## 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `pravna` | **Sve funkcije modula** |
| `nabavka` | Čita partnere i ugovore kroz svoj modul |
| `uprava` | Sve |

> **[P]** Uloga `pravna` se pri sinhronizaciji dozvola **samo dopunjava**, ne usklađuje —
> ručno dodate dozvole joj ostaju.

---

## 15. Validacije i kontrole

| Kontrola | Poruka |
|---|---|
| Domaće pravno lice bez PIB-a i matičnog broja | *„Domaće pravno lice treba da ima PIB i/ili matični broj.“* |
| Domaće fizičko lice bez JMBG-a | *„Domaće fizičko lice treba da ima JMBG.“* |
| **Aneks bez glavnog ugovora** | *„Aneks mora imati glavni ugovor.“* |
| **Glavni ugovor sa nadređenim** | *„Glavni ugovor ne sme imati nadređeni ugovor.“* |
| Nadređeni koji nije glavni | *„Nadređeni ugovor mora biti tipa 'Glavni ugovor'.“* |
| Ugovor sam sebi nadređen | Odbija se |
| „Važi do“ pre „Važi od“ | Odbija se |
| Ponuda: „Vazi do“ pre datuma ponude | Odbija se |
| **Veza sa menicom: ni jedna ni obe** | *„Izaberite tacno jednu menicu.“* |
| Garancija: „Vazi do“ pre „Vazi od“ | Odbija se |
| Brisanje povezane menice | **Zabranjeno** (`PROTECT`) |
| Jedinstvenost stranke | `(ugovor, partner, uloga)` |

**Datoteke [P]:** stara datoteka se briše tek **posle potvrde transakcije**;
najveća veličina je **50 MB** (`MAX_CONTRACT_UPLOAD_SIZE`).

---

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Partner u više grupa u izvoru | Bira se red po **prvenstvu grupa** (1 → 10 → 11/13/14 → ostalo) |
| Partner obrisan iz izvora | **Ostaje** u evidenciji |
| Partner bez matičnog broja | APR provera ga **preskače** |
| Partner nije u APR-u | **Ništa se ne menja** — odsustvo nije dokaz gašenja |
| **Status različit od `активан`** | **Partner postaje neaktivan** ([P-40](../10-poznati-problemi.md)) |
| Zahtev ili ponuda bez partnera | Koristi se slobodan tekst `external_partner_name` |
| Ista menica na više ugovora | **Dozvoljeno** |
| Oznake „ima menice / garancije“ | **Ručne** — ne usklađuju se automatski |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Koje sve vrednosti statusa vraća APR | **Q38** |
| 2 | Treba li APR provera da bude zakazana | **Q39** |
| 3 | Treba li oznake na ugovoru automatski usklađivati | **Q40** |
| 4 | Ko sve koristi modul (komercijala?) | **Q2** |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.11](../obracuni/06-11-ugovori-i-menice.md) | Analize Ugovora i Menica |
| [3.7. Menice](03-07-menice.md) | Povezani modul |
| [4.9](../04-baza-podataka.md#49-ugovori--ugovori) | Tabele |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-40 |
