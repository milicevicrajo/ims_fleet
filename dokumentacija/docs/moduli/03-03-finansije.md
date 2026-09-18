# 3.3. Finansijska analitika

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Finansije** / „Finansijska analitika“ |
| Tehnički naziv | Django aplikacija `finansije` |
| Adresa | `/finansije/` |
| Bočni meni | `sidebar_finansije.html` |

---

## 2. Poslovna namena

Odgovara na pitanje: **koliko je koji posao i koji centar zaradio ili izgubio, i koliko
je novca stvarno ušlo i izašlo.**

Do ovog modula taj odgovor se dobijao tek posle obračuna u knjigovodstvu, pokretanjem
poslovnih procedura. Sada je dostupan na ekranu, **bez pokretanja ijedne procedure**. [P]

> **[P] Modul ne knjiži i ne menja poslovne podatke** — koristi isključivo `SELECT` upite
> nad izvorom. Jedini izuzetak je dugme „Osveži nalog_z“, koje pokreta jednu unapred
> određenu proceduru.

---

## 3. Korisnici modula

| Korisnik | Šta dobija |
|---|---|
| **Uprava** | Rezultat cele firme, po centrima i poslovima, rang-liste |
| **Rukovodioci centara** | Rezultat svog centra i svojih šifara posla |
| **Finansije** | Detalj posla: fakture, konta, zaposleni, vozila, potraživanja |
| **Rukovodioci poslova** | Kartica posla sa svim evidencijama |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Finansijski pregled** | Prihodi, rashodi i rezultat po centrima i poslovima, sa grafikonima i rang-listama |
| **Detaljni izveštaji** | Po šiframa posla, kontima, mesecima i centrima |
| **Zbirna tabela šifara posla** | 11 kolona: prihod, rashod, P−R, ZT, P−R−ZT, priliv, odliv, neto gotovina |
| **Kartica (detalj) posla** | Osam tabova sa dokumentima i evidencijama |
| **Knjiženja** | Pojedinačne stavke sa filterima i izvozom |
| **Sinhronizacija** | Ručno pokretanje, istorija, kontrolni zbirovi, osvežavanje `nalog_z` |

### Osam tabova na kartici posla [P]

| Tab | Sadržaj | Odakle |
|---|---|---|
| Fakture | Izdate fakture IF, konta `20400/20500` | Lokalna knjiženja |
| Interne fakture | Nalozi `ON`, konta `61420/61421/61521/64002` | Lokalna knjiženja |
| Rashodi | Mesečni rashodi po kontima | Lokalna knjiženja |
| **Vozila** | Vozila na šifri posla, po istorijskim dodelama | **Flota** |
| **Zaduženja vozila** | Ko je zadužio vozilo na tom poslu | **Flota** |
| **Zaposleni i zarade** | Lica iz zaključenih obračuna zarada | `bazaldims` |
| **Putni nalozi** | Službena putovanja na teret posla | **Flota** |
| **Potraživanja** | Saldo kupaca po starosnim razredima | **Potraživanja** |

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Finansijski pregled** | `/finansije/` |
| Detaljni izveštaji | `/finansije/izvestaji/` |
| Zbirna tabela šifara posla | `/finansije/izvestaji/?group=job` |
| **Kartica posla** | `/finansije/posao/?job=413111&year=2026&month=8` |
| Knjiženja | `/finansije/knjizenja/` |
| Izvoz u Excel | `/finansije/izvoz/` |
| **Sinhronizacija** | `/finansije/sinhronizacija/` |

---

## 6. Podaci koje korisnik unosi

**Nijedan poslovni podatak.** [P] Korisnik bira samo:

| Izbor | Gde |
|---|---|
| Period (od–do) | Svi ekrani |
| Centar, šifra posla, konto, vrsta naloga, OJ knjiženja | Detaljni izveštaji i knjiženja |
| Način grupisanja | Izveštaji |
| Pokretanje sinhronizacije | Ekran sinhronizacije |
| Osvežavanje `nalog_z` | Ekran sinhronizacije |

---

## 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada | Način |
|---|---|---|---|
| **Knjiženja** | `[PUTGEO-SERVER].[bazaims].dbo.nalog_z` | Svaki sat u :20 (tekuća godina), 03:50 (sve godine) | Sinhronizovano u `LedgerEntry` |
| Šifarnici poslova, konta, OJ, partnera | `bazaims.dbo.posao`, `konto`, `ob_jedin`, `partner` | Uz sinhronizaciju | Sinhronizovano i direktno |
| **Pravila zajedničkih troškova** | `bazaims.dbo.posao_mes`, `blokraspodela` | **Pri otvaranju ekrana** | Direktan `SELECT` |
| **Tok gotovine** | `nalog_z`, `konto`, `vrsta_naloga`, `tipnal`, `pdv_arhiva`, `posao_mes` | **Pri otvaranju ekrana** | Direktan `SELECT` |
| Konta zarada | `[PUTGEO-SERVER].[bazaldims].dbo.element` | Pri otvaranju | Direktan `SELECT` |
| Zaposleni na poslu | `bazaldims.dbo.Zarada`, `PomLD`, `Radnik` | Pri otvaranju | Direktan `SELECT` |
| Lokalna kopija `nalog_z` | `IMS_ERP.dbo.sp_AzurirajNalogZ` | 10:00 i 11:00 | Procedura |

> **[P] Važno:** samo prihodi i rashodi rade iz lokalne kopije. **Zajednički troškovi,
> tok gotovine i zaposleni zahtevaju da udaljeni server radi u trenutku otvaranja ekrana.**

---

## 8. Tabele i kolone

Detaljno: [4.6. Finansijska analitika](../04-baza-podataka.md#46-finansijska-analitika--finansije).
**Samo 4 tabele** — modul je pretežno „čitač“.

| Tabela | Uloga | Ključ |
|---|---|---|
| **`finansije_ledgerentry`** | Lokalna kopija knjiženja | firma + godina + vrsta + broj + stavka |
| `finansije_financejob` | Šifarnik poslova | `(company, code)` |
| `finansije_syncrun` | Istorija sinhronizacije, kontrolni zbirovi | — |
| `finansije_nalogzrefreshrun` | Istorija osvežavanja `nalog_z` | — |

---

## 9. SQL objekti

| Objekat | Server | Namena |
|---|---|---|
| `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | `PUTGEO-SERVER.bazaims` | Knjiženja i šifarnici |
| `posao_mes`, `blokraspodela` | `PUTGEO-SERVER.bazaims` | Pravila zajedničkih troškova |
| `tipnal`, `vrsta_naloga`, `pdv_arhiva` | `PUTGEO-SERVER.bazaims` | Tok gotovine |
| `element`, `Zarada`, `PomLD`, `Radnik` | `PUTGEO-SERVER.bazaldims` | Zarade |
| **`sp_AzurirajNalogZ`** | `IMS_ERP` | **Jedina procedura koju modul pokreće** |

> **[P] Procedure koje se NE pokreću:** `SPFINizv52`, `53`, `55`, `52nt`, `SPLdKnjizenje`.
> Njihova **pravila su prepisana u Python**, ali se same procedure ne izvršavaju.

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`finansije/models.py`](../../../finansije/models.py) |
| **Čitanje izvora** | [`services/source.py`](../../../finansije/services/source.py) |
| **Sinhronizacija** | [`services/sync.py`](../../../finansije/services/sync.py) |
| Prihodi i rashodi | [`services/reports.py`](../../../finansije/services/reports.py) |
| **Zajednički troškovi** | [`services/shared_costs.py`](../../../finansije/services/shared_costs.py) |
| **Tok gotovine** | [`services/cash_flow.py`](../../../finansije/services/cash_flow.py) |
| Kartica posla | [`services/job_card.py`](../../../finansije/services/job_card.py), [`job_tables.py`](../../../finansije/services/job_tables.py) |
| Zaposleni i zarade | [`services/job_people.py`](../../../finansije/services/job_people.py) |
| **Procedura nalog_z** | [`services/nalog_z.py`](../../../finansije/services/nalog_z.py) |
| Grafikoni | [`services/charts.py`](../../../finansije/services/charts.py) |

Testovi: **121 test** u 7 fajlova. [P]

---

## 11. Ulazni i izlazni podaci

| Smer | Šta |
|---|---|
| **Ulaz** | Knjiženja i šifarnici sa dva udaljena servera; podaci Flote i Potraživanja |
| **Izlaz** | Ekrani i **izvoz u Excel** sa istim obuhvatom i napomenama |

> **[N] Q3:** rezultati se **ne knjiže** i ne prenose automatski. Nije potvrđeno
> da li ih neko preuzima i za koji dokument.

---

## 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Flota** | Vozila, zaduženja i putni nalozi na šifri posla — **uz dozvole Flote** |
| **Potraživanja** | Saldo kupaca po šifri posla — **uz dozvole Potraživanja** |
| **Administracija** | Dozvoljeni centri korisnika |

> **[P] Dvostruka provera prava:** za tab „Vozila“ traže se i `jobcode_list` i
> `vehicle_travel_order_list`; za „Zaposlene“ i `employee_list`. Finansijski pristup
> poslu **nije dovoljan** za tuđe module.

---

## 13. Izveštaji i analize

**18 obračuna.** Detaljno:
[6.1. Finansijska analitika](../obracuni/06-01-finansije.md) i
postojeća metodologija (`finansije-metodologija-obracuna.md`, uklonjena 18.09.2026., u git istoriji `06f60c2`).

---

## 14. Uloge i prava pristupa

| Dozvola | Šta omogućava |
|---|---|
| `finansije:dashboard` | Pregled, izveštaji, kartica posla |
| `finansije:ledger` | Knjiženja |
| `finansije:export` | Izvoz u Excel |
| `finansije:sync_status` | Ekran sinhronizacije |
| **`finansije:view_all`** | **Ceo obuhvat firme** |

| Uloga | Obuhvat |
|---|---|
| `uprava` | Sve dozvole |
| `finansije` („Finansijska analitika“) | Pregled, knjiženja, izvoz — **ograničeno dozvoljenim centrima** |

**Posebna pravila [P]:**

- **Prazan spisak dozvoljenih centara nije globalan pristup.**
- Ukupni iznosi i procenti računaju se **iz korisniku dostupnog skupa** — dva korisnika
  mogu videti različite ukupne iznose.
- Za zajedničke troškove se **osnovice cele firme** moraju izračunati, ali se korisniku
  vraća samo rezultat za dostupne poslove.
- Ručno pokretanje sinhronizacije i procedure traži **i `sync_status` i `view_all`**.

---

## 15. Validacije i kontrole

| Kontrola | Ponašanje |
|---|---|
| **Kontrolni zbirovi pre objave** | Broj redova i oba iznosa po godini i kontu, iz nezavisnog upita. Neslaganje **zaustavlja** sinhronizaciju |
| Duplikat u šifarniku izvora | *„Dupliran ključ izvornog šifarnika; sinhronizacija je zaustavljena.“* |
| Zaključavanje sinhronizacije | SQL `sp_getapplock` — pokriva i komandnu liniju |
| Zaključavanje procedure | `sp_getapplock` u **istoj sesiji** koja pokreće proceduru |
| Prazan izvor | **Ne može** obrisati postojeće podatke |
| Neispravni brojači procedure | *„Procedura je vratila neispravne brojače.“* |
| Prekinut prethodni prolaz | Status **„Ishod nepoznat“** pri sledećem preuzimanju zaključavanja |
| Neispravan period | Finansijski rezultati se **ne prikazuju** |
| Nepotpuna pokrivenost koeficijentima | Iznos sa **zvezdicom** i objašnjenjem — „nepotpuno“ nije „nula“ |

---

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| **Zatvaranja godine** | Vrsta `ZAT` i konta `59900`/`69900` **namerno izuzeti** iz prihoda i rashoda |
| Godina bez uspešne sinhronizacije | Iznosi se **ne prikazuju kao nula** |
| Godišnji ZT | **Nije zbir** dvanaest mesečnih obračuna |
| Cela godina naspram zbira meseci (tok gotovine) | **Ne moraju biti jednaki** — periodna pravila procedure |
| Učešće preko 100% | Moguće kada drugi centri imaju gubitak — nije greška |
| Nulti imenilac | Procenat je **crtica**, ne nula |
| **Promena centra u šifarniku** | **Pregrupiše celu istoriju** ([P-44](../10-poznati-problemi.md)) |
| Knjiženje bez šifarnika | **Ne odbacuje se** — prikazuje se kao neraspoređeno |
| Prazna šifra posla u toku gotovine | Pripisuje se **`111111`**, po pravilu procedure |
| Prazna šifra u prihodima i rashodima | **Ne preimenuje se** |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Da li se raspodela zajedničkih troškova **knjiži** na klasu 5 | **Q41** / [P-43](../10-poznati-problemi.md) |
| 2 | Da li je potrebna istorija pripadnosti posla centru | **Q42** / [P-44](../10-poznati-problemi.md) |
| 3 | Ko obaveštava o izmeni kontnog plana ili procedura | **Q43** / [P-42](../10-poznati-problemi.md) |
| 4 | **Ukupan trošak zarada centra** | Čeka potvrdu izvora i pravila |
| 5 | Istorijski kadrovski spisak centra | Čeka potvrdu |
| 6 | Kako se rezultati koriste u knjiženju | **Q3** |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| **Postojeća metodologija** (uklonjena) | Potpun opis svih obračuna. Uklonjen iz repozitorijuma 18.09.2026.; sadržaj je dostupan u git istoriji, u izmeni `06f60c2` |
| [6.1](../obracuni/06-01-finansije.md) | Registar obračuna i nalazi pregleda |
| [4.6](../04-baza-podataka.md#46-finansijska-analitika--finansije) | Tabele |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-42, P-43, P-44 |
