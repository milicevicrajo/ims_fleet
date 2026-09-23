# 6.6. Kadrovi — obračuni

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](../10-poznati-problemi.md).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [K-01](#k-01--dnevni-sati-rada-iz-evidencije-prolazaka) | Dnevni sati rada iz evidencije prolazaka | **P-28** |
| [K-02](#k-02--dnevni-sati-iz-obračunatih-parova-drugi-postupak) | Dnevni sati iz obračunatih parova (drugi postupak) | **P-28** |
| [K-03](#k-03--problemi-u-parovima-prolazaka) | Problemi u parovima prolazaka | — |
| [K-04](#k-04-i-k-05--sati-radne-liste) | Ukupni sati po redu radne liste | — |
| [K-05](#k-04-i-k-05--sati-radne-liste) | Ukupni sati radne liste | — |
| [K-06](#k-06--godišnji-odmori--dodele-i-rešenja) | Godišnji odmori — dodele i rešenja | — |
| [K-07](#k-07--bolovanja--uvoz-rfzo-i-povezivanje) | Bolovanja — uvoz RFZO i povezivanje | **P-29** |
| [K-08](#k-08--ocenjivanje-zaposlenih--stimulacija-i-lični-koeficijent) | **Ocenjivanje — stimulacija i lični koeficijent** | — |
| [K-09](#k-09--tok-saglasnosti-na-ocenu) | Tok saglasnosti na ocenu | — |
| [K-10](#k-10--rešenja-zaposlenih--izrada-teksta-dokumenta) | **Rešenja zaposlenih — izrada teksta dokumenta** | — |

---

## Zajednička osnova: odakle dolaze kadrovski podaci

```
┌─ INFORMATIKA23.ID ──────────────┐   sistem kontrole pristupa (čitači kartica)
│  Radnici                        │
│  C_Prolasci_Radnika             │ ← pojedinačni prolasci (K-01)
│  C_Tasteri                      │ ← šifarnik tastera
│  c_parovi_radnika_detalji       │ ← već uparena trajanja (K-02)
└─────────────────────────────────┘
┌─ SERFIN.bazaldims ──────────────┐
│  radnik                         │ ← OJ i ime uz parove (K-02)
└─────────────────────────────────┘
┌─ PUTGEO-SERVER.BazaLDIMS ───────┐   obračun zarada
│  Godmor                         │ ← dodele godišnjeg odmora (K-06)
│  GodmorKor                      │ ← rešenja o korišćenju (K-06)
└─────────────────────────────────┘
┌─ IMS_ERP ───────────────────────┐
│  dbo.hr_employee                │ ← zaposleni (dnevna sinhronizacija u 01:10)
└─────────────────────────────────┘
        RFZO Excel izvoz  ─────────► bolovanja (ručni uvoz, K-07)
```

> **[P]** Kadrovski moduli zavise od **tri udaljena servera**. Ako bilo koji nije
> dostupan, radna lista se otvara, ali **bez podataka o prolascima**, uz poruku
> *„Izvor prolazaka trenutno nije dostupan. Bolovanja i putni nalozi prikazani su
> iz aplikacije.“*

---

## K-01 — Dnevni sati rada iz evidencije prolazaka

> **Ovo je obračun koji zaposleni vidi na svojoj radnoj listi.**

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Sati“ i „Decimalno“ u koloni evidencije prolazaka |
| Tehnički naziv | `calculate_daily_hours_from_clock_events()` |
| Putanja | [`hr/services/attendance.py:313`](../../../hr/services/attendance.py#L313) |
| Ekran | `/hr/radna-lista/` |

### 2. Poslovna svrha

Iz pojedinačnih prolazaka kroz čitač kartica računa **koliko je sati zaposleni proveo
na poslu svakog dana**, kao **predlog i kontrolu** pri popunjavanju radne liste.

> **[P] Važno:** ovo **nije** automatsko popunjavanje radne liste. Sati iz prolazaka
> se prikazuju **uporedo** sa radnom listom, ali se **ne prepisuju** u nju — zaposleni
> sam unosi sate po šiframa posla.

### 3. Korisnici rezultata

Zaposleni (svoja radna lista), kadrovska služba, superuser (tuđe radne liste).

### 4. Ulazni podaci

| Poslovni naziv | Izvor | Kolona | Obavezno |
|---|---|---|---|
| Vreme prolaska | `INFORMATIKA23.ID.dbo.C_Prolasci_Radnika` | `Vreme` | Da |
| Taster | ista tabela | — | Da |
| Šifra radnika | `INFORMATIKA23.ID.dbo.Radnici` | `Sifra` | Da |
| Ime i prezime | ista tabela | — | Ne |

### 5. Poreklo podataka

Zaposleni prislanja karticu na čitač i bira taster. Zapis nastaje u sistemu kontrole
pristupa, a IMS ERP ga **samo čita** preko povezanog servera. [P]

### 6. Tačan postupak obračuna

#### Šifarnik tastera [P]

| Taster | Značenje | Uloga u obračunu |
|---|---|---|
| **1** | Ulazak 1 | **Ulaz** |
| **3** | Ulazak 2 | **Ulaz** |
| **5** | Ulazak 3 | **Ulaz** |
| **7** | Ulazak u posebnu smenu | **Ulaz** |
| **2** | Izlazak radnika | **Izlaz** |
| **4** | Službeni izlazak | **Izlaz, po posebnom pravilu** |
| **11** | Poništavanje prolaska radnika | **Za pregled** — ne ulazi u obračun |
| **12** | Pauza | **Za pregled** — ne ulazi u obračun |
| ostalo | — | **Nepoznat taster** — prijavljuje se kao problem |

Opisi tastera se mogu dopuniti iz tabele `C_Tasteri`; podrazumevani spisak je u kodu. [P]

#### Uparivanje [P]

Prolasci se grupišu **po danu** i sortiraju po vremenu. Zatim se redom obrađuju:

```
 taster = ULAZ   ──► ako već postoji otvoren ulaz → PROBLEM „Dupli ulaz bez izlaza“
                     inače → zapamti ulaz

 taster = IZLAZ  ──► ako nema otvorenog ulaza → PROBLEM „… bez prethodnog ulaza“
                     ako je izlaz pre ili u trenutku ulaza → PROBLEM „… nije posle ulaza“
                     inače → saberi trajanje, zatvori par

 taster = 11/12  ──► PROBLEM „… nije automatski uključen u obračun“

 ostalo          ──► PROBLEM „Nepoznat taster“

 na kraju dana, ostao otvoren ulaz ──► PROBLEM „… bez izlaza“
```

#### Službeni izlazak — posebno pravilo [P]

> Kod tastera **4 (Službeni izlazak)** vreme izlaska se **ne uzima stvarno**, nego se
> **postavlja na 16:00** istog dana.

Uz taj par se upisuje napomena *„Sluzbeni izlazak - racunato do 16:00.“*, koja se
**ne broji kao problem** (`is_problem = False`). [P]

> **[Z] Poslovno objašnjenje:** zaposleni koji izađe službeno ne vraća se da odjavi
> izlazak, pa se radni dan računa do kraja radnog vremena.
>
> **[P] Vreme 16:00 je upisano u kod** (`DEFAULT_OFFICIAL_EXIT_END_TIME`) i nije podesivo
> kroz interfejs.

#### Zbir [P]

> **trajanje para = ceo broj minuta između ulaza i izlaza** (sekunde se odbacuju)
> **ukupno dnevno = zbir trajanja svih parova**

| Prikaz | Način |
|---|---|
| Sati i minuti | `ukupno // 60` : `ukupno % 60`, dvocifreno |
| Decimalno | `ukupno / 60`, zaokruženo na **2 decimale** |

#### Status dana na ekranu [P]

| Uslov (redom) | Status |
|---|---|
| Dan ima bar jedan **problem** | **„Problem“** |
| Dan ima bar jedan zatvoren par | **„OK“** |
| Zaposleni je tog dana na **bolovanju** i nema problema ni parova | **„Bolovanje“** |
| Izvor prolazaka nije dostupan | **„Nije učitano“** |
| Inače | **„Nema prolaza“** |

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `hr/services/attendance.py` |
| Funkcije | `get_clock_events()`, `calculate_daily_hours_from_clock_events()` |
| Ekran | `hr/views.py: MyWorkTimeSheetView.build_clock_attendance_context()` |
| Šablon | `hr/templates/hr/work_time_sheet.html` |
| Zaštita od pada izvora | `except DatabaseError` — ekran se otvara i bez prolazaka |

**Dodatno na istom ekranu [P]:** uz svaki dan se prikazuju i **putni nalozi**
(`_travel_orders_by_day`) i **bolovanja** (`sick_leaves_by_day`), koji dolaze iz
same aplikacije i **ne zavise** od udaljenog servera.

Putni nalog se prikazuje na **svakom danu svog trajanja**:
od `travel_date` do `travel_date + broj dana − 1`; stornirani nalozi se izuzimaju. [P]

### 8. Primer obračuna

> Ilustrativni primer, jedan dan.

| Vreme | Taster | Značenje | Obrada |
|---|---|---|---|
| 07:32 | 1 | Ulazak 1 | Otvoren ulaz |
| 11:05 | 12 | Pauza | **Problem** — ne ulazi u obračun |
| 11:40 | 2 | Izlazak radnika | Par 07:32–11:40 = **248 min** |
| 12:15 | 3 | Ulazak 2 | Otvoren ulaz |
| 14:50 | 4 | **Službeni izlazak** | Par 12:15–**16:00** = **225 min** |

| Rezultat | Vrednost |
|---|---|
| Ukupno minuta | 248 + 225 = **473** |
| Sati i minuti | **7:53** |
| Decimalno | 473 / 60 = **7,88** |
| Broj parova | 2 |
| Broj problema | **1** (pauza) |
| Status dana | **„Problem“** |

> Uočite: službeni izlazak u 14:50 računa se **do 16:00**, što daje 70 minuta više nego
> stvarno provedeno vreme. To je pravilo, ne greška.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Predlog i kontrolu sati po danu |
| Format | `H:MM` i decimalno sa 2 decimale |
| Gde se čuva | **Nigde** — čita se iz izvora pri svakom otvaranju |
| Može li korisnik da ga izmeni | **Ne** — ispravka se radi u sistemu kontrole pristupa |
| Istorija | Ne postoji |

### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Radna lista | Prikaz uz svaki dan, kao kontrola |
| Kadrovska služba | Provera prisustva |

> **[P]** Rezultat **ne ulazi** u radnu listu automatski i **ne prenosi se** u obračun
> zarada. Zaposleni sate unosi ručno, po šiframa posla.

### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Sati ne odgovaraju | Otvoriti spisak napomena uz dan — vidi se svaki prolazak i razlog |
| „Nema prolaza“ a bio je na poslu | Zaposleni nije prislonio karticu ili je izabrao pogrešan taster |
| Dan ima problem | Napomena navodi tačno vreme i opis |
| Ceo mesec prikazuje „—“ | Izvor prolazaka nije dostupan — nije greška podataka |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Posledica |
|---|---|---|
| Zaboravljen izlazak | Problem „bez izlaza“, **par se ne računa** | Sati manji od stvarnih |
| Zaboravljen ulazak | Problem „bez prethodnog ulaza“, par se ne računa | Sati manji od stvarnih |
| Dva ulaza zaredom | Prvi se zadržava, drugi je problem | Moguće veće trajanje |
| **Prolazak preko ponoći** | Grupisanje je **po danu prolaska** — ulaz u 22:00 i izlaz u 06:00 **ne čine par** | **P-28** |
| Službeni izlazak posle 16:00 | Izlaz se postavlja na 16:00 → **izlaz pre ulaza** → problem | Par se gubi |
| Pauza (taster 12) | Uvek problem, čak i kada je pravilno korišćena | Svaki dan sa pauzom ima status „Problem“ |
| Nepoznat taster | Problem | Vidljivo |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Ulazni tasteri su 1, 3, 5, 7 | Potvrđeno | `attendance.py:89` | — |
| Izlazni taster je 2, službeni 4 | Potvrđeno | `attendance.py:90-91` | — |
| Službeni izlazak se računa do 16:00 | Potvrđeno | `attendance.py:93, 391` | Potvrditi poslovno pravilo |
| Tasteri 11 i 12 se prijavljuju kao problem | Potvrđeno | `attendance.py:423-434` | **Q25** |
| Trajanje u celim minutima | Potvrđeno | `attendance.py:407` | — |
| Sati se ne prepisuju u radnu listu | Potvrđeno | Nema takvog upisa | — |
| **Prolasci preko ponoći** | **Potvrđeno — problem** | `attendance.py:337, 342` | **P-28** |

---

## K-02 — Dnevni sati iz obračunatih parova (drugi postupak)

> **U sistemu postoje DVA različita obračuna sati.** Ovaj se **ne prikazuje zaposlenom**
> — koristi ga samo upravljačka komanda. Daje **drugačiji rezultat** od K-01.

### 1. Naziv

| | |
|---|---|
| Tehnički naziv | `get_daily_work_hours()`, `get_month_daily_work_hours()` |
| Putanja | [`hr/services/attendance.py:474`](../../../hr/services/attendance.py#L474) |
| Gde se koristi | Upravljačka komanda `manage.py hr_attendance_summary` |

### 2. Poslovna svrha

Čita **već uparena trajanja** iz sistema kontrole pristupa
(`c_parovi_radnika_detalji`), umesto da sam upa­ruje prolaske.

### 6. Tačan postupak obračuna

Sve se izvršava **jednim SQL upitom** nad povezanim serverima. [P]

**Izvor:**

> `INFORMATIKA23.ID.dbo.c_parovi_radnika_detalji`
> spojeno sa `SERFIN.bazaldims.dbo.radnik` preko `Radnik = rasif`

**Isključenje neispravnih zapisa [P]:**

> uzimaju se samo redovi gde je `Trajanje_1` prazno **ili manje od 20**

> **[Z]** Prag od 20 sati služi da se izuzmu zapisi sa besmisleno dugim trajanjem
> (npr. zaboravljena odjava). Prag je upisan u upit i nije podesiv.

**Formula dnevnog zbira [P]:**

> **ukupno sati = `Trajanje_1` + `Trajanje_2` + `Trajanje_3`
> + `Trajanje_Posebna` + `Trajanje_Sluzbeno`
> + min(`trajanje_pauza`, 0,5)**

Prazne vrednosti se računaju kao **0** (`COALESCE`).

> **[P] Pauza se priznaje najviše 30 minuta.** Ako je pauza trajala duže, u radno vreme
> ulazi samo 0,5 sata. Ako je kraća, ulazi u punom trajanju.

**Grupisanje:** po danu, šifri radnika, organizacionoj jedinici i imenu. [P]

**Prikaz [P]:**

| Kolona | Formula |
|---|---|
| Sati | `FLOOR(ukupno)` |
| Minuti | `ROUND((ukupno − FLOOR(ukupno)) × 60, 0)` |
| Ukupno | `CAST(ukupno AS decimal(10,2))` |

**Čišćenje imena [P]:** znakovi **Ć** (`NCHAR(262)`) i **Č** (`NCHAR(268)`) zamenjuju se
sa **C** već u upitu.

### 8. Primer

| Kolona izvora | Vrednost |
|---|---|
| `Trajanje_1` | 3,50 |
| `Trajanje_2` | 4,00 |
| `Trajanje_Sluzbeno` | 0,00 |
| `trajanje_pauza` | **0,75** |

> ukupno = 3,50 + 4,00 + 0,00 + **0,50** (pauza ograničena) = **8,00 sati**
> Prikaz: sati **8**, minuti **0**, ukupno **8,00**

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| `Trajanje_1 >= 20` | **Ceo red se izuzima** |
| Pauza duža od 30 minuta | Priznaje se samo 0,5 sata |
| Radnik nije u `SERFIN.bazaldims.dbo.radnik` | **Red se gubi** — spajanje je `INNER JOIN` |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Formula zbira pet trajanja plus ograničena pauza | Potvrđeno | `attendance.py:497-506` | — |
| Prag isključenja `Trajanje_1 < 20` | Potvrđeno | `attendance.py:512` | Potvrditi značenje praga |
| Pauza ograničena na 0,5 sata | Potvrđeno | `attendance.py:502-505` | — |
| Radnik bez zapisa u `radnik` se gubi | Potvrđeno | `INNER JOIN`, linija 508 | — |
| **Dva različita obračuna sati u sistemu** | **Potvrđeno — problem** | K-01 naspram K-02 | **P-28** |

---

## K-03 — Problemi u parovima prolazaka

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Napomene uz dan, status „Problem“ |
| Tehnički naziv | `ClockPairIssue` |
| Putanja | [`hr/services/attendance.py:68`](../../../hr/services/attendance.py#L68) |

### 2. Poslovna svrha

Umesto da tiho preskoči neupariv prolazak, sistem **imenuje tačan problem** i prikazuje
ga uz dan, da bi zaposleni znao šta da ispravi.

### 6. Spisak prepoznatih problema [P]

| Poruka | Kada nastaje | Broji se kao problem |
|---|---|---|
| „Dupli ulaz bez izlaza izmedju (*taster*).“ | Dva ulaza bez izlaza između | Da |
| „*Taster* bez prethodnog ulaza.“ | Izlaz bez otvorenog ulaza | Da |
| „*Taster* nije posle ulaza.“ | Izlaz pre ili u trenutku ulaza | Da |
| „*Taster* bez izlaza.“ | Ulaz ostao otvoren do kraja dana | Da |
| „*Taster* nije automatski ukljucen u obracun.“ | Tasteri 11 i 12 | Da |
| „Nepoznat taster: *N*.“ | Taster izvan šifarnika | Da |
| **„Sluzbeni izlazak - racunato do 16:00.“** | Taster 4 uspešno uparen | **Ne** — obaveštenje |

Svaki zapis nosi datum, šifru zaposlenog, **tačno vreme** i taster. [P]

### 9–11. Rezultat i upotreba

Prikazuje se uz dan u obliku `HH:MM - poruka`. U zaglavlju meseca prikazuje se
**ukupan broj problema** (bez obaveštenja o službenom izlasku). [P]

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Sedam vrsta poruka | Potvrđeno | `attendance.py:357-458` |
| Službeni izlazak nije problem | Potvrđeno | `attendance.py:418` |
| Brojač problema izuzima obaveštenja | Potvrđeno | `hr/views.py:561` |

---

## K-04 i K-05 — Sati radne liste

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Ukupno“ po redu i „Ukupno“ radne liste |
| Tehnički naziv | `WorkTimeSheetLine.total_hours`, `WorkTimeSheet.total_hours` |
| Putanja | [`hr/models.py:255`](../../../hr/models.py#L255), [`hr/models.py:189`](../../../hr/models.py#L189) |

### 2. Poslovna svrha

Radna lista je mesečna evidencija u kojoj zaposleni raspoređuje svoje sate **po šiframa
posla**. Zbir po redu pokazuje koliko je sati utrošeno na jednu šifru, a zbir liste
ukupan mesečni fond.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Ograničenje | Ko unosi |
|---|---|---|---|---|
| Šifra posla | Šifra posla | `hr_worktimesheetline.organizational_unit_id` | — | **Zaposleni** |
| Sati po danu | Kolone 1–31 | `day_1` … `day_31` | **ceo broj 0–24** | **Zaposleni** |
| Vrsta rada / odsustva | Napomena | `work_category_id` | Samo aktivne i „zaposleni bira“ | Zaposleni |
| Topli obrok — dana | Topli obrok | `hr_worktimesheet.meal_days` | 0–31 | Zaposleni |
| Topli obrok — šifra posla | Topli obrok, šifra | `meal_organizational_unit_id` | — | Zaposleni |
| Terenski dodatak — dana | Terenski dodatak | `field_allowance_days` | 0–31 | Zaposleni |

> **[P] Sati su celobrojni.** Polje je `PositiveSmallIntegerField` sa najvećom vrednošću
> **24** — polovine sata se **ne mogu uneti**.

### 6. Tačan postupak obračuna

> **ukupno po redu = `day_1` + `day_2` + … + `day_31`**, gde se prazno računa kao **0**
> **ukupno radne liste = zbir „ukupno“ svih redova**

**Čišćenje dana izvan meseca [P]:** pri čuvanju se svim danima **iznad broja dana u
mesecu** postavlja prazno. Februar tako ne može zadržati sate u poljima 30. i 31.

**Broj redova [P]:** radna lista se pri otvaranju automatski dopunjava do
`WORK_TIME_SHEET_LINE_COUNT` redova — prazni redovi postoje unapred.

### 6.1. Status radne liste [P]

| Status | Značenje | Kako se postiže |
|---|---|---|
| `draft` — „Popunjava se“ | Radna verzija | Podrazumevano |
| `submitted` — „Predato“ | Zaposleni je predao | Dugme „Predaj i štampaj“ |
| `approved` — „Odobreno“ | Odobreno | **[N] Nije pronađena radnja koja postavlja ovaj status** |

> **[N] Q26:** status „Odobreno“ postoji u modelu, ali u kodu **nije pronađena** radnja
> koja ga postavlja. Da li je odobravanje predviđeno, a nije izvedeno?

### 6.2. Ko čiju listu vidi [P]

| Korisnik | Pristup |
|---|---|
| Zaposleni | **Samo svoju** radnu listu |
| Superuser | Radnu listu bilo kog zaposlenog (`/hr/zaposleni/<id>/radna-lista/`) |
| Korisnik bez povezanog zaposlenog | **Zabranjen pristup** — *„Korisnicki nalog nije povezan sa zaposlenim.“* |

> **[P]** Tuđu radnu listu može otvoriti **isključivo superuser** — ne postoji uloga
> koja to dozvoljava kadrovskoj službi.

### 8. Primer

| Red | Šifra posla | 1. | 2. | 3. | … | Ukupno |
|---|---|---|---|---|---|---|
| 1 | 413111 | 8 | 8 | — | … | **160** |
| 2 | 413222 | — | — | 8 | … | **16** |
| 3 | *(prazan)* | — | — | — | … | **0** |
| | | | | | **Ukupno liste** | **176** |

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | **Sati se čuvaju** u `hr_worktimesheetline`; zbirovi se računaju pri prikazu |
| Ko menja | Zaposleni, dok je status `draft` |
| Trag | `created_by`, `updated_by`, `created_at`, `updated_at` |
| Kontrola | Uporediti zbir liste sa satima iz prolazaka (K-01) prikazanim na istom ekranu |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Sati uneti u dan koji ne postoji u mesecu | Brišu se pri čuvanju |
| Prazno polje | Računa se kao 0 |
| Više od 24 sata u danu | Obrazac odbija unos |
| Polovina sata | **Nije moguće uneti** |
| Predata lista | Status se menja, ali **izmena i dalje ostaje moguća** [Z] |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Sati su celi brojevi 0–24 | Potvrđeno | `hr/models.py:213-243` | — |
| Zbir po redu i po listi | Potvrđeno | `hr/models.py:189-191, 255-260` | — |
| Dani izvan meseca se brišu | Potvrđeno | `hr/views.py:653-654` | — |
| Tuđu listu otvara samo superuser | Potvrđeno | `hr/views.py:433-434` | — |
| **Status „Odobreno“ se nigde ne postavlja** | **Nepotvrđeno** | Nema takve radnje | **Q26** |

---

## K-06 — Godišnji odmori — dodele i rešenja

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Godišnji odmori“ |
| Tehnički naziv | `sync_annual_leave()` |
| Putanja | [`hr/services/annual_leave.py:135`](../../../hr/services/annual_leave.py#L135) |
| Adrese | `/hr/godisnji-odmori/`, sinhronizacija `/hr/godisnji-odmori/sinhronizacija/` |

### 2. Poslovna svrha

Preuzima iz obračuna zarada **koliko je dana odmora zaposlenom dodeljeno** i
**koja rešenja o korišćenju su izdata**, da bi kadrovska služba imala pregled na
jednom mestu.

> **[P] Izričita namera iz koda:** *„Read-only import… without payroll calculations“* —
> sistem **ne računa** pravo na odmor, samo preuzima ono što je obračun zarada utvrdio.

### 4. Ulazni podaci

| Izvor | Tabela | Kolone |
|---|---|---|
| **Dodele** | `[putgeo-server].[BazaLDIMS].[dbo].[Godmor]` | `sif_pred, god, rasif, dana1…dana6, dana, ostalo, ranaz` |
| **Rešenja** | `[putgeo-server].[BazaLDIMS].[dbo].[GodmorKor]` | `sif_pred, god, rasif, od_datuma, do_datuma, dana, komentar` |

Obuhvat: **firma 1**, opciono jedna godina. [P]

### 6. Tačan postupak obračuna

**Korak 1 — zaključavanje** [P]: pre čitanja izvora uzima se SQL zaključavanje
`sp_getapplock` na resursu `hr:annual_leave_sync`, vezano za **transakciju**.
Ako je već zauzeto: *„Sinhronizacija godišnjih odmora je već u toku.“*

> Zaključavanje pokriva **sve ulazne tačke** — ekran, komandu i zadatak.

**Korak 2 — provera ispravnosti (sve pre bilo kakvog upisa)** [P]:

| Provera | Poruka pri neuspehu |
|---|---|
| Firma mora biti 1 | „Godmor, red *N*: neispravna ili duplirana dodela.“ |
| Godina između 1900. i 2100. | isto |
| Šifra zaposlenog ≥ 0 | isto |
| Broj dana ≥ 0 | isto |
| Ime do 255 znakova | isto |
| Ključ se ne sme ponavljati | isto |
| Rešenje: početak ≤ kraj | „GodmorKor, red *N*: neispravno ili duplirano rešenje.“ |
| Komentar do 255 znakova | isto |

> **[P] Sve ili ništa:** jedan neispravan red **zaustavlja ceo prenos** uz poruku
> *„Ništa nije sinhronizovano.“*

**Korak 3 — ključ zapisa** [P]:

| Zapis | Ključ |
|---|---|
| Dodela | (firma, godina, šifra zaposlenog) |
| Rešenje | (firma, godina, šifra zaposlenog, **`source_start_key`**) |

`source_start_key` je početni datum i vreme iz izvora, zapisan kao tekst sa
**mikrosekundama** (`isoformat(timespec='microseconds')`).

> **[P] Zašto tako:** izvorni ključ nosi vremensku komponentu. Da se rešenja ne bi
> duplirala ili gubila zbog prikaza i vremenskih zona, čuva se **tačan tekst**.
> Zapis sa vremenskom zonom se **odbija**.

**Korak 4 — povezivanje sa zaposlenim** [P]:

> šifra zaposlenog **0** znači „nema identiteta“ u nasleđenom izvoru — takav zapis se
> **čuva, ali ne povezuje** sa zaposlenim

Nepovezani zapisi se broje u `unlinked`.

**Korak 5 — upis i povlačenje** [P]:

| Situacija | Postupak | Brojač |
|---|---|---|
| Ključ ne postoji lokalno | Novi zapis | `created` |
| Ključ postoji, sadržaj promenjen | Ažuriranje | `updated` |
| Ključ postoji, sadržaj isti | Ništa | `unchanged` |
| **Ključ više nije u izvoru** | **`source_present = False`** — zapis se **ne briše** | `withdrawn` |

> **[P] Izričito objašnjenje iz koda:** *„A changed source PK is a new decision;
> retain its previous local record as withdrawn.“* — izmenjeno rešenje u izvoru dobija
> novi ključ, a staro ostaje kao povučeno.

**Korak 6 — istorija:** svaki prenos upisuje `AnnualLeaveSync` sa brojačima. [P]

**Probni prolaz [P]:** `dry_run=True` izvrši ceo postupak pa **poništi transakciju** —
brojači se prikazuju, podaci se ne menjaju.

### 8. Primer

> Sinhronizacija za 2026.

| Izvor | Ključ | Ishod |
|---|---|---|
| Godmor | (1, 2026, 1234) — 20 dana | **Novo** |
| Godmor | (1, 2026, 1235) — 25 dana, bilo 24 | **Ažurirano** |
| Godmor | (1, 2026, **0**) — 18 dana | Novo, **nepovezano** |
| GodmorKor | (1, 2026, 1234, `2026-07-01T00:00:00.000000`) | **Novo** |
| *lokalno postoji* | (1, 2026, 1236) — nema ga više u izvoru | **Povučeno** (`source_present = False`) |

**Brojači:** dodele — novo 2, ažurirano 1, nepovezano 1, povučeno 1.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `hr_annualleaveallowance`, `hr_annualleavedecision` |
| Kada se osvežava | **Ručno** — nije u rasporedu zakazanih poslova |
| Istorija | `hr_annualleavesync` sa brojačima po prolazu |
| Kontrola | Uporediti brojače sa očekivanim brojem zaposlenih; „nepovezano“ ukazuje na zapise sa šifrom 0 |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Jedan neispravan red | **Ceo prenos se prekida** |
| Izvor prazan za obuhvat | Greška: *„Lokalni podaci nisu izmenjeni.“* |
| Šifra zaposlenog 0 | Zapis se čuva nepovezan |
| Zaposleni ne postoji lokalno | Zapis se čuva nepovezan |
| Rešenje uklonjeno iz izvora | Označeno kao povučeno, **ne briše se** |
| Dva istovremena pokretanja | Drugo se odbija |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Izvor su `Godmor` i `GodmorKor` na `PUTGEO-SERVER.BazaLDIMS` | Potvrđeno | `annual_leave.py:12, 23-26` |
| Obuhvat je firma 1 | Potvrđeno | `annual_leave.py:13, 41` |
| Sve ili ništa pri grešci | Potvrđeno | `annual_leave.py:71-72, 90-91` |
| Ključ rešenja nosi mikrosekunde | Potvrđeno | `annual_leave.py:81` |
| Šifra 0 se ne povezuje | Potvrđeno | `annual_leave.py:107` |
| Nestali zapis se označava, ne briše | Potvrđeno | `annual_leave.py:128-130` |
| Zaključavanje pokriva sve ulazne tačke | Potvrđeno | `annual_leave.py:144-151` |
| Sinhronizacija nije zakazana | Potvrđeno | Nije u `EXPECTED_PERIODIC_TASKS` |

---

## K-07 — Bolovanja — uvoz RFZO i povezivanje

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Bolovanja“ i „Uvoz bolovanja“ |
| Tehnički naziv | `parse_rfzo_workbook()`, `import_rfzo_workbook()` |
| Putanja | [`hr/services/sick_leave.py:77`](../../../hr/services/sick_leave.py#L77) |
| Adrese | `/hr/bolovanja/`, `/hr/bolovanja/uvoz/` |

### 2. Poslovna svrha

Preuzima spisak bolovanja iz **RFZO Excel izvoza** i povezuje ga sa zaposlenima,
da bi kadrovska služba imala pregled odsustava i da bi se bolovanja videla na radnoj listi.

> **[P] Izričita namera iz koda:** *„…without payroll calculations“* — sistem **ne računa**
> naknadu za bolovanje.

### 4. Ulazni podaci

Kolone se prepoznaju po nazivu, **na ćirilici ili latinici** [P]:

| Podatak | Prihvaćeni nazivi kolone | Obavezno |
|---|---|---|
| RFZO ID | `Ид`, `Id`, `RFZO ID` | Da |
| JMBG | `ЈМБГ`, `JMBG` | Da |
| Status | `Статус`, `Status` | Da |
| Početak bolovanja | `Датум почетка боловања`, `Datum početka bolovanja`, `Datum pocetka bolovanja` | Da |
| Zaključenje | `Датум закључења боловања`, `Datum zaključenja bolovanja`, `Datum zakljucenja bolovanja` | Ne |
| Ukupno dana | `Укупно дана`, `Ukupno dana` | Ne |

Zaglavlje se traži u **prvih 20 redova**; ako se ne pronađe — greška. [P]

### 6. Tačan postupak obračuna

#### Ograničenja datoteke [P]

| Ograničenje | Vrednost |
|---|---|
| Veličina datoteke | najviše **10 MB** |
| Raspakovan sadržaj | najviše **50 MB** |
| Broj redova | najviše **50.000** |
| Format | `.xlsx` |

> **[Z]** Provera raspakovane veličine štiti od namerno pripremljene datoteke koja je
> mala, a raspakuje se u ogroman sadržaj.

#### Normalizacija JMBG-a [P]

| Ulaz | Rezultat |
|---|---|
| Tekst od 13 cifara | Prihvata se |
| **12 cifara** | **Dodaje se vodeća nula** — Excel je „pojeo“ nulu u brojčanoj ćeliji |
| Broj sa decimalama | Odbija se |
| Tekst sa vodećim apostrofom | Apostrof se uklanja |
| Bilo šta drugo | Odbija se |

#### Status [P]

| Vrednost u datoteci (ćirilica ili latinica, bez obzira na veličinu slova) | Status |
|---|---|
| `aktivno`, `активно` | **Aktivno** |
| `zaključeno`, `zakljuceno`, `закључено` | **Zaključeno** |
| `stornirano`, `сторнирано` | **Stornirano** |
| `poništeno`, `ponisteno`, `поништено` | **Poništeno** |
| bilo šta drugo | **Greška** |

#### Provere po redu [P]

| Provera | Uslov |
|---|---|
| RFZO ID | Nije prazan, najviše 64 znaka |
| Početak | Postoji, godina između 1900. i 2100. |
| Kraj | Ako postoji: nije pre početka, godina do 2100. |
| **Status „Zaključeno“** | **Mora imati datum zaključenja** |
| Ukupno dana | Ceo broj, najviše 100.000 |
| Isti RFZO ID u datoteci | Dozvoljen **samo ako su podaci identični** |

**Podržani formati datuma:** Excel broj, `GGGG-MM-DD`, `DD.MM.GGGG`, `DD.MM.GGGG.`, `DD/MM/GGGG`. [P]

> **[P] Sve ili ništa:** svaka greška prekida uvoz uz poruku
> *„Nijedan red nije uvezen.“*

#### Provere pri upisu [P]

| Provera | Poruka |
|---|---|
| Isti RFZO ID već postoji uz **drugi JMBG** | *„RFZO ID već postoji uz drugi JMBG. Uvoz nije izvršen.“* |
| **Datum izvoza stariji** od već evidentiranog | *„Datoteka je starija od već evidentiranih podataka.“* |

> **[P]** Druga provera sprečava da stariji izvoz pregazi novije podatke.

#### Povezivanje sa zaposlenim [P]

Traži se zaposleni sa **istim normalizovanim JMBG-om**:

| Broj pronađenih | Povezivanje | Napomena |
|---|---|---|
| **Tačno jedan** | Poveže se | prazno |
| Više | **Ne povezuje se** | „Više zaposlenih sa istim JMBG-om“ |
| Nijedan | **Ne povezuje se** | „Zaposleni nije pronađen po JMBG-u“ |

Nepovezani se broje u `unlinked_count`.

#### Brojači uvoza [P]

`row_count`, `created_count`, `updated_count`, `unchanged_count`, `unlinked_count` —
čuvaju se u `hr_sickleaveimport` zajedno sa **SHA-256 otiskom datoteke**.

**Probni prolaz [P]:** `dry_run=True` vraća brojače bez ijednog upisa.

#### Prikaz bolovanja po danima (radna lista) [P]

Funkcija `sick_leaves_by_day()`:

> uzimaju se bolovanja zaposlenog koja počinju **pre kraja meseca**
> i koja se **završavaju u mesecu ili kasnije**, odnosno **otvorena** bolovanja
> čiji je datum izvoza u mesecu ili kasnije
>
> **isključuju se statusi „Stornirano“ i „Poništeno“**

Za **otvoreno** bolovanje (bez datuma zaključenja) kao kraj se uzima **datum RFZO izvoza**.

### 8. Primer

> Uvoz datoteke sa datumom izvoza **10.09.2026.**

| RFZO ID | JMBG u datoteci | Status | Početak | Kraj | Ishod |
|---|---|---|---|---|---|
| 100001 | `0101990710012` (13) | Zaključeno | 01.08. | 15.08. | **Novo, povezano** |
| 100002 | `101990710013` (**12**) | Aktivno | 20.08. | — | Novo, povezano (dodata nula) |
| 100003 | `0101990710099` | Aktivno | 25.08. | — | Novo, **nepovezano** — nema zaposlenog |
| 100004 | `0101990710012` | **Zaključeno** | 01.09. | **—** | **GREŠKA — ceo uvoz se prekida** |

Bez reda 100004: `row_count=3, created=3, unlinked=1`.

Na radnoj listi za avgust: bolovanje 100002 prikazuje se od 20.08. do **10.09.**
(datum izvoza), odnosno do kraja avgusta u avgustovskoj listi.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `hr_sickleave`, istorija u `hr_sickleaveimport` |
| Kada se osvežava | **Ručno** — kadrovska služba uvozi RFZO datoteku |
| JMBG na ekranu | **Maskiran** — prikazuju se samo poslednje 4 cifre |
| Kontrola | Brojač „nepovezano“ ukazuje na zaposlene čiji JMBG ne odgovara izvoru |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Jedan neispravan red | Ceo uvoz se prekida | Namerno |
| Ista datoteka uvezena dvaput | Svi redovi „nepromenjeni“, otisak se pamti | Ispravno |
| Stariji izvoz posle novijeg | Odbija se | Ispravno |
| Više zaposlenih sa istim JMBG-om | Ne povezuje se, uz napomenu | Vidljivo |
| **Otvoreno bolovanje** | Kraj se pretpostavlja kao **datum izvoza** | **P-29** |
| Storno i poništenje | Ne prikazuju se na radnoj listi, ali **ostaju u bazi** | Ispravno |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Kolone se prepoznaju i ćirilicom i latinicom | Potvrđeno | `sick_leave.py:20-27` | — |
| JMBG od 12 cifara dobija vodeću nulu | Potvrđeno | `sick_leave.py:39-40` | — |
| Sve ili ništa pri grešci | Potvrđeno | `sick_leave.py:127, 129` | — |
| Stariji izvoz se odbija | Potvrđeno | `sick_leave.py:160-161` | — |
| Povezivanje samo pri jednom poklapanju | Potvrđeno | `sick_leave.py:162-164` | — |
| Storno i poništenje se izuzimaju iz kalendara | Potvrđeno | `sick_leave.py:191` | — |
| **Otvoreno bolovanje se prikazuje do datuma izvoza** | **Potvrđeno** | `sick_leave.py:194` | **P-29** |

---

## K-08 — Ocenjivanje zaposlenih — stimulacija i lični koeficijent

> **Ovo je obračun čiji rezultat ide u obračun zarada.**

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Ocenjivanje“, „Koeficijent stimulacije“, „Lični koeficijent“ |
| Tehnički naziv | `build_snapshot()`, `save_evaluation()` |
| Putanja | [`hr/services/evaluations.py:136`](../../../hr/services/evaluations.py#L136) |
| Adrese | `/hr/ocenjivanje/`, `/hr/ocenjivanje/novo/`, štampa `/hr/ocenjivanje/<id>/stampa/` |

### 2. Poslovna svrha

Mesečna ocena zaposlenog po **šest merila**, koja daje **lični koeficijent (K4)** —
množilac koji ulazi u obračun zarade.

### 3. Korisnici rezultata

Neposredni rukovodilac, direktor centra, generalni direktor, **obračun zarada**.

### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Ko unosi |
|---|---|---|---|
| Zaposleni | Zaposleni | `hr_employeeevaluation.employee_id` | Rukovodilac |
| Godina i mesec | Period | `year`, `month` | Rukovodilac |
| Grupa za ocenjivanje | Grupa | `hr_evaluationemployeesetup.group_id` | Šifarnik |
| **Bodovi po merilu** | 0–4 po svakom merilu | u `snapshot` | **Rukovodilac** |
| Komentar po merilu | Napomena | u `snapshot` | Rukovodilac |
| Ocenjivači | Tri nivoa | `hr_evaluationunitsetup` | Šifarnik po OJ |

**Šifarnik [P]:** 2 grupe × 6 merila × 5 nivoa bodova (0–4) = **60 kombinacija**.
Uvozi se iz Excel datoteke (`import_evaluation_catalog`), koja **mora** imati tačno
60 kombinacija.

### 5. Poreklo podataka

```
 Excel šifarnik ocenjivanja ──► EvaluationGroup, EvaluationCriterion, EvaluationScale
                                                     │
 Zaposleni (org_unit_code) ──► EvaluationUnitSetup ──┤ (tri ocenjivača za OJ)
                                                     ▼
                                        potpisani snimak obrasca
                                                     │
                            rukovodilac bira bodove po merilima
                                                     ▼
                              stimulacija = zbir koeficijenata
                              lični koeficijent = 1 + stimulacija
```

### 6. Tačan postupak obračuna

#### Korak 1 — priprema obrasca (snimak) [P]

Za izabranu grupu se učitavaju **aktivna merila** i njihove **aktivne skale**.

**Obavezna provera:** svako merilo mora imati bar jednu opciju sa koeficijentom **0**
(neutralna vrednost). Inače: *„Merilo *N* nema aktivnu skalu sa neutralnom vrednošću 0.“*

Podrazumevani izbor je neutralna opcija — po pravilu ona sa **1 bod i koeficijentom 0**.

**Granice obrasca** se računaju odmah i **upisuju u snimak** [P]:

> **minimum = 1 + zbir najmanjih koeficijenata svih merila**
> **maksimum = 1 + zbir najvećih koeficijenata svih merila**

#### Korak 2 — potpisivanje obrasca [P]

Snimak se **kriptografski potpisuje** (`django.core.signing`) zajedno sa:

| Podatak | Svrha |
|---|---|
| `user` | Obrazac važi samo za korisnika koji ga je otvorio |
| `nonce` (UUID) | **Sprečava dvostruki upis** iste ocene |
| `source_id` | Veza na prethodnu reviziju |

**Rok važenja: 24 sata.** Posle toga: *„Obrazac je istekao ili nije važeći.“*

#### Korak 3 — obračun pri čuvanju [P]

Za svako merilo se uzimaju izabrani bodovi i pronalazi odgovarajuća opcija
**u sačuvanom snimku** — ne u tekućem šifarniku:

> **stimulacija = Σ koeficijent izabrane opcije, po svim merilima**
> **lični koeficijent (K4) = 1 + stimulacija**

Pravilo je izričito upisano u snimak: `'rule': 'K4 = 1 + sum(stimulation)'`. [P]

> **[P] Ključna zaštita:** ako izabrani bodovi ne postoje u sačuvanoj skali:
> *„Izabrani bodovi ne pripadaju sačuvanoj skali.“* Izmena šifarnika posle otvaranja
> obrasca **ne može** promeniti rezultat.

**Tip i preciznost [P]:** koeficijenti su `decimal(10,5)` — **pet decimala**.

#### Korak 4 — revizija [P]

> **revizija = najveća postojeća revizija za (zaposleni, godina, mesec) + 1**

Ocena je **nepromenljiva**. Ispravka se pravi kao **nova revizija** koja pokazuje na izvornu.

#### Korak 5 — ko koga sme da ocenjuje [P]

| Korisnik | Koga može da oceni |
|---|---|
| Sa dozvolom `hr:evaluation_view_all` | **Sve zaposlene** |
| Neposredni rukovodilac | Samo zaposlene **svojih organizacionih jedinica** (`EvaluationUnitSetup.supervisor`) |
| Bez dozvole `hr:evaluation_create` | **Nikoga** |

Pri čuvanju se zaposleni **zaključava** (`select_for_update`). [P]

#### Pismo [P]

Nazivi merila, opisi i imena čuvaju se **preslovljeni na latinicu** funkcijom `latin()`,
koja pokriva celu ćiriličnu azbuku uključujući `Љ`, `Њ`, `Џ`.

> **[P] Napomena:** funkcija `cyrillic()` je **identična** funkciji `latin()` — obe
> preslovljavaju **na latinicu**. Naziv `cyrillic` je obmanjujuć.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `hr/services/evaluations.py` |
| Funkcije | `build_snapshot()`, `sign_snapshot()`, `read_snapshot()`, `save_evaluation()` |
| Tabela | `hr_employeeevaluation` — `snapshot` (JSON), `stimulation`, `personal_coefficient` |
| Uvoz šifarnika | `manage.py import_evaluation_catalog` |
| Testovi | `hr/test_evaluations.py` — 15 testova |
| Ekran za štampu | `/hr/ocenjivanje/<id>/stampa/` |

### 8. Primer obračuna

> Ilustrativni primer, grupa „Ostali zaposleni“, šest merila.

| Merilo | Izabrani bodovi | Koeficijent |
|---|---|---|
| 1. Kvalitet rada | 3 | **0,04000** |
| 2. Obim posla | 4 | **0,06000** |
| 3. Samostalnost | 2 | **0,02000** |
| 4. Odnos prema radu | 1 | **0,00000** |
| 5. Saradnja | 3 | **0,04000** |
| 6. Poštovanje rokova | 0 | **−0,03000** |

| Korak | Račun | Rezultat |
|---|---|---|
| **Stimulacija** | 0,04 + 0,06 + 0,02 + 0,00 + 0,04 − 0,03 | **0,13000** |
| **Lični koeficijent K4** | 1 + 0,13000 | **1,13000** |
| Minimum obrasca | 1 + zbir najmanjih | npr. 0,82000 |
| Maksimum obrasca | 1 + zbir najvećih | npr. 1,36000 |

> Koeficijent 1,13000 je unutar granica, pa ga viši nivo može potvrditi ili korigovati
> samo u rasponu 0,82000–1,36000.

### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Množilac za obračun zarade za jedan mesec |
| Format | `decimal(10,5)` — pet decimala |
| Gde se čuva | `hr_employeeevaluation.stimulation` i `.personal_coefficient`, uz **pun JSON snimak** |
| Kada se ponovo računa | **Nikada** — vrednost je zamrznuta |
| Može li korisnik da ga izmeni | **Ne** — samo nova revizija ili korekcija pri saglasnosti (K-09) |
| Istorija | **Potpuna** — svaka revizija ostaje, sa vezom na izvornu |
| Audit trag | `created_by`, `created_at`, `request_key`, plus saglasnosti |

### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Obrazac za štampu | Potpisuju ga tri nivoa |
| **Obračun zarada** | **[N] način prenosa nije potvrđen — Q3** |

> **[N] Q3:** nije potvrđeno kako lični koeficijent stiže u obračun zarada — ručnim
> prepisivanjem sa odštampanog obrasca ili nekim prenosom. U kodu nema izvoza ni veze
> ka sistemu zarada.

### 11. Kontrola i ručna provera

**Kontrolna formula:**

> lični koeficijent = 1 + zbir koeficijenata izabranih bodova po svih šest merila

| Provera | Kako |
|---|---|
| Koeficijent uz svako merilo | Vidljiv na obrascu i u štampi, uz opis osnove bodovanja |
| Granice | Minimum i maksimum su upisani u snimak i prikazani |
| Da li je šifarnik u međuvremenu menjan | Snimak čuva vrednosti **iz trenutka ocenjivanja** |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Obrazac otvoren pre više od 24 sata | Odbija se, traži ponovno otvaranje |
| Dvostruko slanje istog obrasca | **Vraća se postojeća ocena** — `request_key` sprečava duplikat |
| Merilo bez neutralne opcije (koeficijent 0) | Obrazac se **ne može otvoriti** |
| Šifarnik izmenjen posle otvaranja obrasca | Rezultat se računa iz **snimka** |
| Ocena za isti mesec već postoji | Stvara se **nova revizija** |
| Zaposleni izvan nadležnosti rukovodioca | Pristup zabranjen |
| Uvoz šifarnika sa manje od 60 kombinacija | Odbija se |
| Ponovni uvoz šifarnika | Postojeći zapisi se **čuvaju** (`preserved`), ne prepisuju |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| **K4 = 1 + zbir koeficijenata** | Potvrđeno | `evaluations.py:153, 203-204` | — |
| Pet decimala | Potvrđeno | `evaluations.py:60`, model | — |
| Snimak zamrzava skalu i nazive | Potvrđeno | `evaluations.py:183, 197-199` | — |
| Obrazac važi 24 sata | Potvrđeno | `evaluations.py:173` | — |
| `request_key` sprečava dvostruki upis | Potvrđeno | `evaluations.py:188-190` | — |
| Ocena je nepromenljiva, ispravka je nova revizija | Potvrđeno | `evaluations.py:205-210` | — |
| Šifarnik ima tačno 60 kombinacija | Potvrđeno | `evaluations.py:89-90` | — |
| **Kako rezultat stiže u obračun zarada** | **Nepotvrđeno** | — | **Q3** |
| Poreklo koeficijenata u šifarniku | **Nepotvrđeno** | Excel datoteka | **Q6** |

---

## K-09 — Tok saglasnosti na ocenu

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Saglasnost“ |
| Tehnički naziv | `approve_evaluation()`, `approval_state()` |
| Putanja | [`hr/services/evaluations.py:220`](../../../hr/services/evaluations.py#L220) |
| Adrese | `/hr/ocenjivanje/<id>/saglasnost/`, grupno `/hr/ocenjivanje/saglasnost/` |

### 2. Poslovna svrha

Ocena postaje važeća tek kada je potvrde **tri nivoa rukovođenja**. Svaki viši nivo može
**korigovati** koeficijent, uz obavezno obrazloženje.

### 6. Tačan postupak obračuna

#### Redosled nivoa [P]

```
 1. supervisor        Neposredni rukovodilac
 2. director          Direktor centra
 3. general_director  Generalni direktor
```

Nivo se **ne može preskočiti**: *„Prethodni nivo ocenjivanja još nije potvrdio obrazac.“*

#### Ko sme da potvrdi [P]

| Provera | Poruka pri neuspehu |
|---|---|
| Dozvola `hr:evaluation_approve` | Zabranjen pristup |
| **Korisnik mora biti baš taj ocenjivač** sa svog naloga | *„Saglasnost daje samo imenovani ocenjivač sa svog naloga.“* |
| Saglasnost tog nivoa ne sme već postojati | *„Ova saglasnost je već sačuvana.“* |
| Ne sme postojati **novija revizija** | *„Postoji novija verzija obrasca. Potvrdite novu verziju.“* |

#### Koeficijent pri saglasnosti [P]

**Polazna vrednost** je koeficijent **poslednjeg potvrđenog nivoa**, a ako ga nema —
lični koeficijent iz ocene.

| Pravilo | Objašnjenje |
|---|---|
| **Neposredni rukovodilac ne sme menjati koeficijent** | *„Za korekciju merila sačuvajte novu verziju obrasca.“* |
| Viši nivoi smeju menjati | Uz obavezne uslove ispod |
| Nova vrednost mora biti **između minimuma i maksimuma iz snimka** | *„Koeficijent je izvan granica sačuvanog šifrarnika.“* |
| Svaka izmena traži **obrazloženje** | *„Za korekciju koeficijenta unesite obrazloženje.“* |

**Merodavan koeficijent [P]:** vrednost **poslednjeg** potvrđenog nivoa. Ako nema
nijedne saglasnosti — lični koeficijent iz ocene.

#### Zaključavanje [P]

Pri potvrdi se zaključavaju i zaposleni i sama ocena (`select_for_update`).

#### Šta se beleži [P]

| Polje | Sadržaj |
|---|---|
| `stage` | Nivo |
| `actor` | Korisnik koji je potvrdio |
| **`actor_name`** | **Ime u trenutku potvrde** — ne menja se kasnije |
| `document_date` | Datum dokumenta |
| `coefficient` | Potvrđen ili korigovan koeficijent |
| `comment` | Obrazloženje |
| `created_at` | Vreme |

Jedinstveno: **jedna saglasnost po nivou za istu ocenu** (kontrola u bazi). [P]

### 8. Primer

| Nivo | Radnja | Koeficijent | Obrazloženje |
|---|---|---|---|
| Neposredni rukovodilac | Potvrdio | **1,13000** | — |
| Direktor centra | **Korigovao** | **1,10000** | „Smanjeno zbog kašnjenja na projektu X“ |
| Generalni direktor | Potvrdio | **1,10000** | — |

**Merodavan koeficijent: 1,10000** — vrednost poslednjeg nivoa.

> Da je direktor pokušao 1,40000, bilo bi odbijeno jer prelazi maksimum obrasca (1,36000).
> Da je promenio vrednost bez obrazloženja, takođe bi bilo odbijeno.

### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `hr_evaluationapproval` |
| Istorija | Potpuna — svaka saglasnost ostaje |
| Kontrola | Na detalju ocene vide se sva tri nivoa, sa datumom, imenom i obrazloženjem |

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Pokušaj preskakanja nivoa | Odbija se |
| Pokušaj potvrde tuđe ocene | Odbija se |
| Dvostruka potvrda istog nivoa | Odbija se |
| Nova revizija posle potvrde | Starija ocena se **ne može** dalje potvrđivati |
| Korekcija izvan granica | Odbija se |
| Korekcija bez obrazloženja | Odbija se |
| Rukovodilac menja koeficijent | Odbija se — mora nova revizija |

### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Tri nivoa u tačnom redosledu | Potvrđeno | `evaluations.py:18, 232-233` |
| Potvrđuje samo imenovani ocenjivač | Potvrđeno | `evaluations.py:223-224` |
| Novija revizija blokira staru | Potvrđeno | `evaluations.py:227-228` |
| Rukovodilac ne sme menjati koeficijent | Potvrđeno | `evaluations.py:235-236` |
| Korekcija mora biti u granicama snimka | Potvrđeno | `evaluations.py:237-238` |
| Korekcija zahteva obrazloženje | Potvrđeno | `evaluations.py:239-240` |
| Merodavan je koeficijent poslednjeg nivoa | Potvrđeno | `evaluations.py:213-216` |

---

## K-10 — Rešenja zaposlenih — izrada teksta dokumenta

> **Ovo nije brojčani obračun.** Rezultat je tekst rešenja koje potpisuje generalni
> direktor, pa se pravila vode ovde, uz ostale kadrovske postupke.

### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Rešenja“, „Novo rešenje“, „Grupno izdavanje“ |
| Tehnički naziv | `build_document()`, `izdaj_resenje()` |
| Putanja | [`hr/services/resenja.py`](../../../hr/services/resenja.py) |
| Adrese | `/hr/resenja/`, `/hr/resenja/novo/`, `/hr/resenja/grupno/`, štampa `/hr/resenja/<id>/stampa/` |

### 2. Poslovna svrha

Zamenjuje Word obrasce kadrovske službe za sedam vrsta rešenja: noćni rad, prekovremeni
rad, prekovremeni rad i rad vikendom, rad na državni i verski praznik, rad vikendom,
prekovremeni rad sa radom vikendom i u smenama, i plaćeno odsustvo za davanje krvi.

### 3. Korisnici rezultata

Kadrovska služba, zaposleni, referent obračuna zarada, dosije zaposlenog.

### 4. Ulazni podaci

| Poslovni naziv | Odakle | Ko unosi |
|---|---|---|
| Vrsta rešenja, tekstovi obrasca | `hr_vrstaresenja` | Uprava (šifarnik) |
| Broj rešenja | Delovodnik | **Kadrovik, ručno** |
| Datum rešenja, period ili dani | Ekran rešenja | Kadrovik |
| Broj i datum zahteva | Zahtev iz centra | Kadrovik |
| Ime, organizaciona jedinica, radno mesto | `fleet_employee`, `fleet_organizationalunit` | **Predlaže sistem, kadrovik ispravlja** |
| Pol | `fleet_employee.gender` | HR sinhronizacija |
| Potpisnik i funkcija | `hr_potpisnik`, po datumu rešenja | Uprava (šifarnik) |

### 5. Poreklo podataka

Svi podaci su lokalni. Nijedan povezani server ne učestvuje, pa izrada rešenja radi
i kada `PUTGEO-SERVER` ili `INFORMATIKA23` nisu dostupni.

### 6. Tačan postupak obračuna

#### Pismo — jedan smer preslovljavanja [P]

Tekstovi u šifarniku se čuvaju **ćirilicom**. Rešenje koje se štampa latinicom nastaje
funkcijom `latin()` iz `hr/services/evaluations.py`.

> **Zašto baš tako:** ćirilica → latinica je jednoznačna, a latinica → ćirilica nije,
> jer se `lj`, `nj` i `dž` ne razlikuju od `l+j`, `n+j` i `d+ž` (na primer „injekcija“).
> Zato obrnuti smer (`to_cyrillic()`) služi **samo kao predlog u formi**, nikada kao
> konačan tekst dokumenta.

Ime zaposlenog ćirilicom uzima se ovim redom [P]:

1. `fleet_employee.full_name_cyrillic` — ručno uneto polje, ima prednost;
2. automatsko preslovljavanje latiničnog imena, kada polje nije popunjeno.

#### Rod — oblici po polu [P]

Word obrasci pišu „запослен-а“ i „дужан-на“ jer papir ne zna pol. Šifarnik umesto toga
koristi čuvar mesta `{rod:дужан|дужна}`, koji se razrešava iz `Employee.gender`:

| Pol | Rezultat |
|---|---|
| `M` | prvi oblik |
| `F` | drugi oblik |
| prazno | oba oblika, odvojena kosom crtom |

#### Uslovni delovi teksta [P]

Segment `[[ime|tekst]]` opstaje samo kada vrednost `ime` nije prazna. Tako jedan obrazac
pokriva i rešenje samo za državni praznik i ono za državni i verski:

```
ради[[dani_drzavni| {dani_drzavni} на дан државног празника]][[dani_verski| и {dani_verski} на дан верског празника]]
```

Red koji se posle razrešavanja isprazni **ne ostavlja praznu tačku** u dispozitivu.

#### Opis perioda [P]

| Uneto | Tekst u rešenju |
|---|---|
| `datum_od` i `datum_do` | „у периоду од 01.02.2026. до 28.02.2026. године“ |
| `datum_od` i „do završetka posla“ | „почев од 23.06.2016. до завршетка посла“ |
| pojedinačni dani | „20.06.2026. и 21.06.2026. године“ |

#### Potpisnik po datumu rešenja [P]

`Potpisnik.za_datum()` bira onog čiji period važenja pokriva datum rešenja
(`vazi_od` uključivo, `vazi_do` isključivo). Zato rešenje iz 2016. godine i danas
nosi tadašnjeg potpisnika, a ne sadašnjeg.

#### Snimak dokumenta [P]

Dok je rešenje **nacrt**, tekst se računa iz trenutnih podataka pri svakom otvaranju.
Pri **izdavanju** se ceo razrešen dokument upisuje u `hr_resenje.dokument` (JSON) i
status prelazi u `izdato`. Od tog trenutka:

- izmena šifarnika, naziva OJ ili potpisnika **ne menja** izdato rešenje;
- rešenje se više ne otvara za izmenu — ispravka ide preko **storniranja** i novog rešenja.

Isti obrazac koristi ocenjivanje (K-08), iz istog razloga.

### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajlovi | `hr/resenja_models.py`, `hr/services/resenja.py`, `hr/resenja_views.py`, `hr/resenja_forms.py` |
| Funkcije | `build_document()`, `razresi()`, `opis_perioda()`, `pripremi_resenje()`, `izdaj_resenje()` |
| Tabele | `hr_vrstaresenja`, `hr_potpisnik`, `hr_resenje`, `hr_resenjedan` |
| Početni šifarnik | Migracija `hr/migrations/0014_resenja_sifrarnik_i_dozvole.py` |
| Testovi | `hr/test_resenja.py` — **41 test** |
| Štampa | HTML strana A4 sa dugmetom „Štampaj / Sačuvaj PDF“, bez dodatnih biblioteka |

### 8. Primer

> Rešenje za rad na državni i verski praznik, muškarac, ćirilica.

Ulaz: zaposleni Лазар Живановић (OJ 430, centar 43), dani 01.01.2025. i 02.01.2025.
kao državni praznik, 07.01.2025. kao verski, zahtev br. 43-15238 od 27.12.2024.

Tačka 1 dispozitiva:

```
ЛАЗАР ЖИВАНОВИЋ запослен у Институту за испитивање материјала а.д. Београд,
распоређен у ЦЕНТАР ЗА ПУТЕВЕ И ГЕОТЕХНИКУ, дужан је да ради 01.01.2025. и
02.01.2025. на дан државног празника и 07.01.2025. на дан верског празника.
```

Isto rešenje za ženu daje „запослена … распоређена … дужна“, bez ijedne ručne izmene.

### 9. Rezultat

| Izlaz | Gde |
|---|---|
| Nacrt rešenja | `/hr/resenja/<id>/` |
| Izdato rešenje sa snimkom | `hr_resenje.dokument` |
| Štampa jednog ili više rešenja | `/hr/resenja/<id>/stampa/`, `/hr/resenja/stampa/` |

### 10. Upotreba rezultata

Odštampano rešenje potpisuje generalni direktor; primerci idu zaposlenom, referentu
obračuna, centru i u dosije. Dani upisani u `hr_resenjedan` ostaju kao osnov za
proveru prekovremenih i prazničnih sati u radnoj listi.

### 11. Kontrola i ručna provera

- Broj rešenja je **jedinstven po datumu** — duplikat iz delovodnika se odbija pri unosu.
- Pre izdavanja se ceo tekst vidi na ekranu detalja, u konačnom obliku.
- Vrsta koja traži dane ne prolazi bez ijednog unetog dana.

### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Zaposleni bez unetog pola | Tekst dobija oba oblika („дужан/дужна“) — vidljivo pri pregledu |
| Automatsko preslovljavanje pogreši digraf | Ispravlja se poljem „Ime i prezime (ćirilica)“ na zaposlenom |
| Potreban drugi padež (plaćeno odsustvo traži dativ) | Polje „Zaposleni u tekstu rešenja“ se menja ručno |
| Nema potpisnika za datum rešenja | Izdavanje se odbija uz poruku |
| Zaposleni nema OJ u `fleet_organizationalunit` | Naziv jedinice i centar ostaju prazni; unose se ručno |

### 13. Status pouzdanosti

| Tvrdnja | Status | Dokaz |
|---|---|---|
| Šifarnik se čuva ćirilicom, latinica nastaje preslovljavanjem | Potvrđeno | `resenja.py: u_pismu()` |
| Ručno uneto ćirilično ime ima prednost | Potvrđeno | `resenja.py: ime_zaposlenog()` |
| Rod se razrešava iz `Employee.gender` | Potvrđeno | `resenja.py: razresi()` |
| Prazan uslovni segment ne ostavlja praznu tačku | Potvrđeno | `resenja.py: _neprazni()` |
| Izdato rešenje se ne menja izmenom šifarnika | Potvrđeno | `test_resenja.py: test_izmena_sifrarnika_ne_menja_vec_izdato_resenje` |
| Potpisnik se bira po datumu rešenja | Potvrđeno | `resenja_models.py: Potpisnik.za_datum()` |

---

## Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-28** | U sistemu postoje **dva različita obračuna dnevnih sati** iz iste evidencije prolazaka, sa različitim pravilima (K-01 uparuje prolaske i računa službeni izlazak do 16:00; K-02 čita gotova trajanja i ograničava pauzu na 30 minuta). Daju različite rezultate za isti dan. Dodatno, K-01 **ne ume da upari smenu preko ponoći**. | **Visoka** |
| **P-29** | Otvoreno bolovanje (bez datuma zaključenja) prikazuje se na radnoj listi **do datuma RFZO izvoza**. Ako izvoz nije skoro rađen, bolovanje koje još traje prestaje da se prikazuje. | Srednja |

## Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q25** | Taster **12 (Pauza)** uvek se prijavljuje kao **problem**, pa svaki dan u kome je zaposleni koristio pauzu dobija status „Problem“. Da li pauzu treba obračunati (kao u K-02, ograničeno na 30 minuta) ili je dovoljno da ne bude označena kao problem? |
| **Q26** | Radna lista ima status **„Odobreno“**, ali u kodu nije pronađena radnja koja ga postavlja. Da li je odobravanje radne liste predviđeno? |
| **Q27** | Službeni izlazak se računa **do 16:00**, što je upisano u kod. Da li je to i zvanično radno vreme i treba li da bude podesivo? |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.7. Mobilna telefonija](06-07-mobilni.md) | Obustave iz zarada |
| [6.10. Isplate](06-10-isplate.md) | Virmani |
| [4. Baza podataka](../04-baza-podataka.md#45-kadrovi--hr) | Kadrovske tabele |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema |
