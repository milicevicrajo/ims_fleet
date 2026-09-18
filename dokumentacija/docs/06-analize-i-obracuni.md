# 6. Analize i obračuni — sadržaj

> **Za koga je ovo poglavlje:** za sve. Poslovni korisnici ovde nalaze **kako se računa**
> svaki iznos koji vide na ekranu; programeri nalaze **gde je implementiran**.
>
> Ovo je samo sadržaj. Svaki obračun je opisan u svom poglavlju, po jedinstvenoj
> strukturi od 13 tačaka.

---

## 6.0.1. Kako je opisan svaki obračun

Svaki obračun ima istih 13 tačaka:

| # | Tačka | Šta sadrži |
|---|---|---|
| 1 | Naziv | Naziv na ekranu i tehnički naziv, sa putanjom do koda |
| 2 | Poslovna svrha | Koji problem rešava i zašto postoji |
| 3 | Korisnici rezultata | Koja služba koristi rezultat |
| 4 | Ulazni podaci | Tabela: poslovni naziv, polje na ekranu, tabela i kolona, tip, jedinica mere, obaveznost, ko unosi |
| 5 | Poreklo podataka | Put podatka od izvora do ekrana |
| 6 | Tačan postupak obračuna | Formula, uslovi, filteri, zaokruživanje, postupanje sa praznim vrednostima |
| 7 | Tehnička implementacija | Fajl, funkcija, upit, ekran, testovi |
| 8 | Primer obračuna | Potpun primer sa konkretnim brojevima |
| 9 | Rezultat | Šta predstavlja, gde se čuva, kada se ponovo računa, ko ga menja |
| 10 | Upotreba rezultata | Gde se dalje koristi |
| 11 | Kontrola i ručna provera | Kako korisnik može sam da proveri iznos |
| 12 | Izuzeci i rizični slučajevi | Šta se dešava kada podatak nedostaje ili nije ispravan |
| 13 | Status pouzdanosti | Tabela: tvrdnja, status, izvor potvrde, otvoreno pitanje |

**Oznake statusa:**

| Oznaka | Značenje |
|---|---|
| **[P]** | Potvrđeno — pročitano iz koda, migracija ili konfiguracije |
| **[Z]** | Zaključeno — logičan zaključak iz implementacije, nije izričito napisano |
| **[N]** | Nepotvrđeno — traži potvrdu korisnika |

---

## 6.0.2. Zbirni pregled

| Modul | Obračuna | Poglavlje | Stanje |
|---|---|---|---|
| **Finansijska analitika** | 18 | [6.1](obracuni/06-01-finansije.md) | ✔ **Završeno** (preuzeto iz postojeće metodologije) |
| **Flota — gorivo** | 8 | [6.2](obracuni/06-02-flota-gorivo.md) | ✔ **Završeno** |
| **Flota — troškovi** | 8 | [6.3](obracuni/06-03-flota-troskovi.md) | ✔ **Završeno** |
| **Flota — polise i lizing** | 4 | [6.4](obracuni/06-04-flota-ugovori-polise.md) | ✔ **Završeno** |
| **Flota — izveštaji** | 4 + 11 | [6.5](obracuni/06-05-flota-izvestaji.md) | ✔ **Završeno** (11 izveštaja čeka DDL) |
| **Kadrovi** | 9 | [6.6](obracuni/06-06-kadrovi.md) | ✔ **Završeno** |
| **Mobilna telefonija** | 4 | [6.7](obracuni/06-07-mobilni.md) | ✔ **Završeno** |
| **Potraživanja** | 6 | [6.8](obracuni/06-08-potrazivanja.md) | ✔ **Završeno** |
| **Nabavka** | 6 | [6.9](obracuni/06-09-nabavka.md) | ✔ **Završeno** |
| **Isplate** | 3 | [6.10](obracuni/06-10-isplate.md) | ✔ **Završeno** |
| **Ugovori i menice** | 4 | [6.11](obracuni/06-11-ugovori-i-menice.md) | ✔ **Završeno** |
| | **74 (+11)** | | ✔ **Svih 74 završeno** (11 izveštaja nad pogledima čeka DDL) |

> Modul **Naplata** nije obuhvaćen — nasleđen je i zamenjuju ga Potraživanja.
> Vidi [10. Poznati problemi, P-18](10-poznati-problemi.md#p-18--naplata-i-potraživanja-rade-paralelno).

---

## 6.1. Finansijska analitika (18 obračuna)

Poglavlje: [`obracuni/06-01-finansije.md`](obracuni/06-01-finansije.md)
Postojeća metodologija: `finansije-metodologija-obracuna.md` — Uklonjen iz repozitorijuma 18.09.2026.; sadržaj je dostupan u git istoriji, u izmeni `06f60c2`

| Oznaka | Naziv | Implementacija |
|---|---|---|
| F-01 | Prihodi po šifri posla | `finansije/services/reports.py` |
| F-02 | Rashodi po šifri posla | `finansije/services/reports.py` |
| F-03 | Rezultat bez zajedničkih troškova | `finansije/services/reports.py` |
| F-04 | Zajednički troškovi — pravila raspodele | `finansije/services/shared_costs.py` |
| F-05 | Zajednički troškovi — koeficijent posla | `finansije/services/shared_costs.py` |
| F-06 | Rezultat posle raspodele ZT | `finansije/services/job_overview.py` |
| F-07 | Priliv gotovine | `finansije/services/cash_flow.py` |
| F-08 | Odliv gotovine | `finansije/services/cash_flow.py` |
| F-09 | Neto gotovina | `finansije/services/cash_flow.py` |
| F-10 | Zamena PDV-a u toku gotovine | `finansije/services/cash_flow.py` |
| F-11 | Zarade u obračunu toka gotovine | `finansije/services/cash_flow.py` |
| F-12 | Refundacije | `finansije/services/cash_flow.py` |
| F-13 | Grafikoni, učešća i rangiranje | `finansije/services/charts.py` |
| F-14 | Mesečni rashodi (kartica posla) | `finansije/services/job_card.py` |
| F-15 | Mesečne fakture IF i interne ON | `finansije/services/job_card.py` |
| F-16 | Vozila i zaduženja na šifri posla | `finansije/services/job_card.py` |
| F-17 | Zaposleni i zarade po šifri posla | `finansije/services/job_people.py` |
| F-18 | Osvežavanje naloga Z | `finansije/services/nalog_z.py` |

---

## 6.2. Flota — gorivo (8 obračuna) ✔

Poglavlje: [`obracuni/06-02-flota-gorivo.md`](obracuni/06-02-flota-gorivo.md)

> U koloni **Problemi** precrtana oznaka (~~P-10~~) znači da je problem
> **rešen 18.09.2026.** — opis šta je promenjeno stoji u
> [registru problema](10-poznati-problemi.md).

| Oznaka | Naziv | Ključna formula | Problemi |
|---|---|---|---|
| [V-03](obracuni/06-02-flota-gorivo.md#v-03--neto-iznos-goriva-iz-bruto-iznosa) | Neto iznos goriva iz bruto | `bruto − PDV`, ili `bruto × 5/6` | — |
| [V-04](obracuni/06-02-flota-gorivo.md#v-04--iznosi-omv-transakcije) | Iznosi OMV transakcije | Iz `gross_cc` i `vat` | — |
| [V-05](obracuni/06-02-flota-gorivo.md#v-05--iznosi-nis-transakcije) | Iznosi NIS transakcije | Iz `total`, uvek × 5/6 | — |
| [V-06](obracuni/06-02-flota-gorivo.md#v-06--prečišćavanje-omv-transakcija) | **Prečišćavanje OMV transakcija** | Tri koraka uklanjanja duplikata | — |
| [V-01](obracuni/06-02-flota-gorivo.md#v-01--prosečna-potrošnja-goriva-poslednjih-10-točenja) | Prosečna potrošnja (10 točenja) | `litri / km × 100` | **P-02** |
| [V-02](obracuni/06-02-flota-gorivo.md#v-02--prosečna-potrošnja-goriva-za-ceo-vek-vozila) | Prosečna potrošnja (ceo vek) | `litri / km × 100` | — |
| [V-21](obracuni/06-02-flota-gorivo.md#v-21--gorivo-po-šifri-posla) | Gorivo po šifri posla | Zbir po istorijskoj dodeli i polumesecu | — |
| [V-23](obracuni/06-02-flota-gorivo.md#v-23--obračun-goriva-na-putnom-nalogu-vozila) | Obračun goriva na putnom nalogu | `litri / pređeni put × 100` | — |

---

## 6.3. Flota — troškovi (8 obračuna) ✔

Poglavlje: [`obracuni/06-03-flota-troskovi.md`](obracuni/06-03-flota-troskovi.md)

| Oznaka | Naziv | Ključna formula | Problemi |
|---|---|---|---|
| [V-08](obracuni/06-03-flota-troskovi.md#v-08--procena-pređene-kilometraže-u-periodu) | Procena kilometraže u periodu | `(Δkm / Δdana) × dana perioda` | **P-03, P-04** |
| [V-07](obracuni/06-03-flota-troskovi.md#v-07--trošak-po-kilometru-po-vozilu) | **Trošak po kilometru** | `(gorivo+servisi+trebovanja+polise+amortizacija+lizing−naknade) / km` | **P-05…P-09**, ~~P-10~~ |
| [V-11](obracuni/06-03-flota-troskovi.md#v-11--pragovi-fiksnog-troška-po-kilometru) | Pragovi po masi vozila | 4 klase × 3 praga | **P-11** |
| [V-12](obracuni/06-03-flota-troskovi.md#v-12--status-vozila-prema-trošku-po-kilometru) | Status vozila i „crvena zona“ | Poređenje sa pragom | — |
| [V-09](obracuni/06-03-flota-troskovi.md#v-09--analiza-troška-po-km-kroz-više-perioda) | Trajno neisplativa vozila | „Neisplativo“ u svim periodima | **P-12** |
| [V-10](obracuni/06-03-flota-troskovi.md#v-10--neto-trošak-održavanja) | Neto trošak održavanja | `servisi + trebovanja − naknade` | — |
| [V-15](obracuni/06-03-flota-troskovi.md#v-15--analitika-evidentiranih-troškova-na-detalju-vozila) | Analitika na detalju vozila | Samo evidentirani iznosi | — |
| [V-24](obracuni/06-03-flota-troskovi.md#v-24--statistika-po-centrima) | Statistika po centrima | Zbirovi za ceo vek vozila | ~~P-13~~, **P-14 D** |

---

## 6.4. Flota — polise, lizing i servisi (4 obračuna) ✔

Poglavlje: [`obracuni/06-04-flota-ugovori-polise.md`](obracuni/06-04-flota-ugovori-polise.md)

| Oznaka | Naziv | Grupisanje | Problemi |
|---|---|---|---|
| [V-17](obracuni/06-04-flota-ugovori-polise.md#v-17--mesečni-troškovi-polisa) | Mesečni troškovi polisa | Po **datumu izdavanja**, istorijska šifra posla | — |
| [V-18](obracuni/06-04-flota-ugovori-polise.md#v-18--polise-pred-istekom-i-neobnovljene-polise) | Polise pred istekom i neobnovljene | Rok 30 dana, samo potpune polise | — |
| [V-19](obracuni/06-04-flota-ugovori-polise.md#v-19--mesečni-troškovi-lizinga) | Mesečni troškovi lizinga | Po **datumu početka ugovora** | **P-23, P-24, P-25** |
| [V-20](obracuni/06-04-flota-ugovori-polise.md#v-20--mesečni-troškovi-servisa) | Mesečni troškovi servisa | Po datumu servisa, istorijska šifra posla | — |

---

## 6.5. Flota — kilometraža, održavanje i izveštaji (4 + 11) ✔

Poglavlje: [`obracuni/06-05-flota-izvestaji.md`](obracuni/06-05-flota-izvestaji.md)

| Oznaka | Naziv | Napomena | Problemi |
|---|---|---|---|
| [V-13](obracuni/06-05-flota-izvestaji.md#v-13--kilometraža-vozila--posmatrana-vremenska-linija) | Kilometraža — vremenska linija | Odbija prikaz kada primeti pad | — |
| [V-14](obracuni/06-05-flota-izvestaji.md#v-14--održavanje-vozila-i-servisni-interval) | Održavanje vozila | Prepoznaje i ćirilične kategorije | — |
| [V-16](obracuni/06-05-flota-izvestaji.md#v-16--presek-stanja-flote-kontrolna-tabla) | Presek stanja flote | 8 grupa upozorenja | — |
| [V-22](obracuni/06-05-flota-izvestaji.md#v-22--izveštaji-za-upravu) | Izveštaji za upravu (4) | Kasko, osiguranje IMS, gorivo, delovi | ~~P-26~~, **P-47** |
| [6.5.5](obracuni/06-05-flota-izvestaji.md#655-izveštaji-nad-nasleđenim-pogledima) | 11 izveštaja nad pogledima | **Formula je u bazi, ne u kodu** | **P-27** |

---

## 6.6. Kadrovi (9 obračuna) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| K-01 | Dnevni sati rada iz evidencije prolazaka | `hr/services/attendance.py` |
| K-02 | Mesečni pregled dnevnih sati | `hr/services/attendance.py` |
| K-03 | Problemi u parovima prolazaka | `hr/services/attendance.py` |
| K-04 | Ukupni sati po redu radne liste | `hr/models.py` |
| K-05 | Ukupni sati radne liste | `hr/models.py` |
| K-06 | Godišnji odmori — dodele i rešenja | `hr/services/annual_leave.py` |
| K-07 | Bolovanja — uvoz RFZO i povezivanje | `hr/services/sick_leave.py` |
| K-08 | **Ocenjivanje — stimulacija i lični koeficijent** | `hr/services/evaluations.py` |
| K-09 | Tok saglasnosti na ocenu | `hr/services/evaluations.py` |

## 6.7. Mobilna telefonija (4 obračuna) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| M-01 | **Obustava po zaposlenom** | `mobilni/withholdings.py` |
| M-02 | Izuzeci od parkinga | `mobilni/withholdings.py` |
| M-03 | Razvrstavanje zaposleni / bivši / nezaposleni | `mobilni/withholdings.py` |
| M-04 | Povezivanje broja telefona sa zaposlenim | `mobilni/models.py` |

## 6.8. Potraživanja (6 analiza) — u pripremi

> Oznake su **PT-**, a ne **P-**, da se ne mešaju sa oznakama problema iz
> [10. Poznati problemi](10-poznati-problemi.md).

| Oznaka | Naziv | Implementacija |
|---|---|---|
| PT-01 | Starosni razredi (aging) | `potrazivanja/services/sync.py` |
| PT-02 | Saldo stavke | `potrazivanja/models.py` |
| PT-03 | Objavljivanje snimka stanja | `potrazivanja/services/sync.py` |
| PT-04 | Kontrolni zbirovi i provera izvora | `potrazivanja/services/sync.py` |
| PT-05 | Saldo po šiframa posla | `potrazivanja/services/reports.py` |
| PT-06 | Normalizacija kontakata | `potrazivanja/services/contacts.py` |

## 6.9. Nabavka (6 analiza) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| B-01 | Procenjena vrednost stavke i predmeta | `nabavka/models.py` |
| B-02 | Grupisanje UF stavki u UF fakture | `nabavka/services/source_snapshots.py` |
| B-03 | Ključ EUF fakture | `nabavka/services/euf.py` |
| B-04 | Razlike verzija plana javnih nabavki | `nabavka/services/public_procurements.py` |
| B-05 | Provera šifre posla partnera | `nabavka/views/reports.py` |
| B-06 | Alarmi nabavke | `nabavka/views/alerts.py` |

## 6.10. Isplate (3 obračuna) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| I-01 | **Generisanje datoteke virmana** | `isplate/services/virman.py` |
| I-02 | Kontrole naloga pre virmana | `isplate/services/virman.py` |
| I-03 | Konverzija datoteka | `isplate/services/converters.py` |

## 6.11. Ugovori i menice (4 analize) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| U-01 | Provera statusa partnera u APR-u | `ugovori/apr_openapi.py` |
| U-02 | Sinhronizacija partnera iz finansija | `ugovori/services.py` |
| U-03 | Preuzimanje menica iz registra NBS | `menice/scraper.py` |
| U-04 | Povezivanje menica i garancija sa ugovorima | `ugovori/models.py` |

---

## 6.0.3. Obračuni po korisniku

Za brzo snalaženje — koji obračuni su važni kojoj službi:

| Služba | Obračuni |
|---|---|
| **Uprava** | F-01…F-13, V-07, V-09, V-12, V-16, V-22 |
| **Finansije** | Svi F-01…F-18, V-17, V-19, V-20 |
| **Služba voznog parka** | Svi V-01…V-24 |
| **Garaža** | V-13, V-14, V-23 |
| **Kadrovska služba** | K-01…K-09 |
| **Obračun zarada** | K-08, **M-01**, I-01 |
| **Služba naplate** | PT-01…PT-06 |
| **Služba nabavke** | B-01…B-06 |
| **Pravna služba** | U-01…U-04 |
| **Blagajna** | **I-01**, I-02 |

---

## 6.0.4. Obračuni čiji rezultat ide izvan sistema

Većina obračuna služi samo za prikaz. Ovi **stvaraju podatak koji ide dalje**:

| Obračun | Šta nastaje | Gde ide | Način prenosa |
|---|---|---|---|
| **I-01** Virman | Datoteka fiksne širine (180 znakova, cp1250) | **Banka** | Preuzimanje datoteke, ručno slanje |
| **M-01** Obustava mobilnih | Iznos po zaposlenom | **Obračun zarada** | CSV izvoz, **[N] način prenosa nije potvrđen** |
| **K-08** Ocenjivanje | Stimulacija i lični koeficijent | **Obračun zarada** | **[N] nije potvrđeno** |
| **K-04/K-05** Radna lista | Sati po šiframa posla | **Obračun zarada** | **[N] nije potvrđeno** |
| **F-18** Nalog Z | Osvežena lokalna kopija knjiženja | `IMS_ERP.dbo.nalog_z` | Uskladištena procedura |

> **[N] Otvoreno pitanje Q3:** ni za jedan od ovih rezultata nije potvrđeno **koja konta
> i koja vrsta knjiženja** se koriste, niti postoji li pisana procedura prenosa.
> Dok se to ne potvrdi, dokumentacija **ne navodi konta**.

---

## 6.0.5. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Koje tabele i kolone koriste ovi obračuni? | [4. Baza podataka](04-baza-podataka.md) |
| Kako podaci dolaze u sistem? | [7. Integracije](07-integracije.md) |
| Šta je uočeno kao problem? | [10. Poznati problemi](10-poznati-problemi.md) |
| Šta znači neki pojam? | [12. Rečnik pojmova](12-recnik-poslovnih-pojmova.md) |
