# 3.8. Mobilna telefonija

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Mobilni** / „Mobilni telefoni“ |
| Tehnički naziv | Django aplikacija `mobilni` |
| Adresa | `/mobilni/` |
| Bočni meni | `sidebar_mobilni.html` |

---

## 2. Poslovna namena

Zaposleni dobija službeni broj telefona sa paketom koji plaća poslodavac.
**Sve iznad paketa zaposleni plaća sam.** Modul odgovara na pitanje:
**koliko se kome obustavlja od zarade za mobilni telefon.**

> **Rezultat ovog modula ide u obračun zarada** — jedan od tri takva u sistemu.

---

## 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Administracija** | Uvozi mesečne datoteke operatera, održava izuzetke od parkinga, povezuje brojeve sa zaposlenima |
| **Obračun zarada** | Preuzima CSV sa iznosima obustava |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Paketi** | Naziv, period važenja, **neto i bruto iznos**, veza sa ugovorom |
| **Korisnici mobilnih** | Šifra radnika, ime, JMBG, datum odlaska, **status veze** sa zaposlenim |
| **Dodele brojeva** | Koji broj kome pripada, **po mesecu** |
| **Potrošnja** | 25 kolona iz računa operatera, **po mesecu** |
| **Izuzeci od parkinga** | Brojevi kojima se parking ne obustavlja |
| **Obustave** | Četiri izveštaja + CSV za obračun zarada |
| **Uvoz** | Četiri odvojena uvoza, sa dnevnikom |

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| Kontrolna tabla | `/mobilni/` |
| **Uvoz podataka** | `/mobilni/import/` |
| Paketi | `/mobilni/paketi/` |
| Korisnici | `/mobilni/korisnici/` |
| **Dodele brojeva** | `/mobilni/dodele/` |
| **Potrošnja** | `/mobilni/potrosnja/` |
| Detalj broja telefona | `/mobilni/brojevi/<broj>/` |
| Izuzeci od parkinga | `/mobilni/parking-izuzeci/` |
| **Obustave — sve** | `/mobilni/obustave/` |
| **Obustave — zaposleni** | `/mobilni/obustave/zaposleni/` |
| Obustave — bivši zaposleni | `/mobilni/obustave/bivsi-zaposleni/` |
| Obustave — nezaposleni | `/mobilni/obustave/nezaposleni/` |
| **CSV za obračun zarada** | `/mobilni/potrosnja/obracunski-mesec.csv` |

Izvoz u Excel postoji za pakete, korisnike, dodele i potrošnju. [P]

---

## 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| **Excel datoteke operatera** (4 vrste) | Administracija |
| Godina i mesec uz dodele i potrošnju | Administracija |
| **Izuzeci od parkinga** | Administracija |
| Ručna ispravka paketa, korisnika, dodele ili potrošnje | Administracija |
| **Status veze korisnika** (npr. „Nezaposleni“) | Administracija |

---

## 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| Paketi, korisnici, dodele, potrošnja | **Excel operatera** | **Ručno, mesečno** |
| Povezivanje sa zaposlenima | `fleet_employee` | **Automatski posle svakog uvoza** |

> **[P]** Modul **nema nijedan zakazani posao** — sve se pokreće ručno.
> Postoji komanda `sync_mobilni_sqlserver`, ali nije u rasporedu. [N]

---

## 8. Tabele i kolone

Detaljno: [4.11. Mobilna telefonija](../04-baza-podataka.md#411-mobilna-telefonija--mobilni).
**6 tabela.**

| Tabela | Jedinstveno po |
|---|---|
| `mobilni_mobilepackage` | `(partner_code, name, valid_from)` |
| `mobilni_mobileuser` | `employee_code` |
| **`mobilni_mobileassignment`** | **`(year, month, phone_number)`** |
| **`mobilni_mobileusage`** | **`(year, month, phone_number)`** |
| `mobilni_mobileparkingexemption` | `phone_number` |
| `mobilni_mobileimportlog` | — |

---

## 9. Spoljni izvori

| Izvor | Način | Napomena |
|---|---|---|
| Operater (MTS) | **Excel, ručni uvoz** | Četiri odvojene datoteke |

> **[N]** Naziv operatera nije zabeležen u kodu; kolone potrošnje (`U MTS mreži`,
> `Van MTS mreže`) upućuju na MTS.

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`mobilni/models.py`](../../../mobilni/models.py) |
| **Obračun obustava** | [`mobilni/withholdings.py`](../../../mobilni/withholdings.py) |
| Uvoz i povezivanje | [`mobilni/support/mobile.py`](../../../mobilni/support/mobile.py) |
| Ekrani i izvozi | [`mobilni/views/mobile.py`](../../../mobilni/views/mobile.py) |

Testovi: **40 testova**. [P]

---

## 11–12. Ulaz, izlaz i veze

| Smer | Šta |
|---|---|
| **Ulaz** | Četiri Excel datoteke operatera |
| **Izlaz** | **CSV za obračun zarada**; Excel izvozi za sve četiri evidencije |

| Modul | Veza |
|---|---|
| **Kadrovi** | Zaposleni uz broj telefona (`fleet_employee`) |
| **Ugovori** | Ugovor uz paket (`MobilePackage.contract`) |

**Oblik CSV datoteke za zarade [P]:**

| Osobina | Vrednost |
|---|---|
| Kolone | `Godina;Mesec;Šifra radnika;Iznos obustave` |
| Razdvajač | tačka-zarez |
| Kodiranje | UTF-8 **sa BOM** |
| Prelom reda | `CRLF` |
| Obuhvat | **samo aktivni zaposleni** |
| Iznos | **ceo dinar**, `ROUND_HALF_UP` |
| Izostavljeno | prazna obustava i **obustava jednaka nuli** |

---

## 13. Izveštaji i analize

**4 obračuna.** Detaljno: [6.7. Mobilna telefonija](../obracuni/06-07-mobilni.md).

**Formula obustave [P]:**

> **obustava = osnovica za PDV − neto iznos paketa + parking + NZRD**

Potvrđeno kao ispravno (naručilac, 18.09.2026.).

---

## 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `mobilni` | **Sve funkcije modula** — usklađuje se automatski |
| `uprava` | Sve |

> **[P]** Uloga `sekretarijat` je izričito **lišena** dozvola ovog modula pri svakoj
> sinhronizaciji dozvola.

---

## 15. Validacije i kontrole

| Kontrola | Ponašanje |
|---|---|
| Jedna dodela po broju i mesecu | Kontrola u bazi |
| Jedna potrošnja po broju i mesecu | Kontrola u bazi |
| Normalizacija broja telefona | Uklanja `.0` iz Excel ćelije i sve osim cifara |
| Godina | 2020–2100 |
| Mesec | 1–12 |
| Izuzetak od parkinga | Jedinstven po broju |
| Uvoz | Beleži se u `mobilni_mobileimportlog` sa brojačima i greškom |

---

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Potrošnja bez dodele za isti mesec** | **Tiho ispada iz obračuna** | [P-31](../10-poznati-problemi.md) |
| Paket bez neto iznosa | Obustava **prazna**, red se ne izvozi | — |
| **Negativna obustava** | **Izvozi se** | [P-31](../10-poznati-problemi.md) |
| Obustava jednaka nuli | **Ne izvozi se** | — |
| **Poseban broj `381637781481`** | Paket se **ne odbija** | **[P-34](../10-poznati-problemi.md) — potvrđena greška** |
| Korisnik označen „Nezaposleni“ | Ne povezuje se sa zaposlenim | Namerno |
| Zaposleni otišao usred meseca | **Nije ni u jednom pojedinačnom izveštaju** | [P-32](../10-poznati-problemi.md) |
| Izuzetak od parkinga upisan naknadno | **Menja i prošle obračune** | [P-30](../10-poznati-problemi.md) |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | **Poslovno objašnjenje posebnog broja** | **Q8** — potvrđeno kao greška, ide u bazu |
| 2 | Da li negativna obustava ide u zarade kao potraživanje zaposlenog | **Q29** |
| 3 | **Kako se CSV unosi u obračun zarada** i koja konta se koriste | **Q3** |
| 4 | Ko je operater i da li se oblik datoteka menja | **[N]** |
| 5 | Čemu služi komanda `sync_mobilni_sqlserver` | **[N]** |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.7](../obracuni/06-07-mobilni.md) | Sva 4 obračuna |
| [4.11](../04-baza-podataka.md#411-mobilna-telefonija--mobilni) | Tabele |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-30, P-31, P-32, **P-34** |
