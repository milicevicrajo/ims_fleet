# Korak 0 — popis šifara posla nad produkcionom bazom

Datum: **21.09.2026.** · Status: **kontrolni izveštaj, bez izmena u bazi i kodu**

Oba postojeća plana — [centralizacija organizacije](plan-centralizacije-organizacije.md)
i [organizacija i dozvole V2](plan-organizacije-i-dozvola-v2.md) — traže popis kao uslov
za nastavak. V2 izričito kaže: *„raniji brojevi šifara nisu ponovo popisivani u bazi”*.
Ovo je taj popis, izvršen **nad produkcijom**, samo čitanjem.

> Status tvrdnji: **[P]** izmereno u produkcionoj bazi, **[Z]** zaključeno, **[N]** nepotvrđeno.
>
> Nijedan upit nije menjao podatke. Nije pokrenuta nijedna migracija ni uvoz.

---

## 1. Šta je izmereno

| Šifarnik | Zapisa | Napomena |
|---|---|---|
| `finansije.FinanceJob` | **415** | Sve firma 1 |
| `fleet.OrganizationalUnit` | **339** | Bez firme; `code` je jedinstven |

Podela `FinanceJob` po oznakama [P]: **88** aktivnih profitnih, **250** aktivnih
neprofitnih, **22** neaktivne profitne, **55** neaktivnih neprofitnih. Ovo se **poklapa
sa brojevima iz plana od 18.09.2026.** — šifarnik se u međuvremenu nije menjao.

---

## 2. Glavni nalaz — šifre nisu jedan sistem, nego tri

Plan uzima primer `43 / 6 / 111 → 436111` i **izričito upozorava da se obrazac ne sme
propisati svim podacima na osnovu primera**. Merenje pokazuje da je to upozorenje bilo
opravdano: postoje **tri različite porodice šifara**.

| Porodica | Šifara | Struktura | Staje li u model tri nivoa |
|---|---|---|---|
| **A — poslovni centri** | **209** | centar 2 cifre + jedinica 1 cifra + posao 3 cifre | **Da, tačno** |
| **B — nauka i projekti** | **193** | centar `3` + nosilac 3 cifre + projekat promenljive dužine | **Ne** |
| **C — izuzeci** | **13** | razno | **Ne bez odluke** |

### Porodica A — model plana se drži doslovno [P]

Centri: `41` (37), `42` (19), `43` (38), `44` (55), `50` (1), `60` (10), `70` (4),
`81` (9), `82` (29), `83` (8). Sve šifre su **tačno 6 cifara** i počinju šifrom centra.

```
43 0 111  Administracija
43 0 999  Režija
43 1 111  Stručni nadzor i ter.ispitivanja
43 1 112  Terenske lab. kod izv.
44 1 111  Prednaprezanje
41 0 001  Troškovi amortizacije
```

Treći znak (kandidat za drugi nivo) uzima vrednosti `0`–`9`. Šifra `0` se svuda javlja uz
opšte poslove (amortizacija, administracija, režija), a `1`–`9` uz stručne. **[Z]** To
liči na „zajednički / operativni”, ali **značenje drugog nivoa nije potvrđeno** i ostaje
pitanje za naručioca.

### Porodica B — nauka je zaseban šifarnik, i to matrica čovek × projekat [P]

193 šifre imaju centar `3`. Struktura je **`3` + osoba (3 cifre) + projekat (promenljivo)**:

```
315400      Delić Ivana                    <- koren: sama osoba
3154190170  P190170-Delić I.               <- ta osoba na projektu 190170
3154190200  P19020-Delić I.
3154450080  P 450080-Delić I.
3154702400  TD 7024-Delić I.
```

**Da su koreni stvarne osobe — provereno poređenjem sa kadrovskom evidencijom** [P].
Imena iz šifarnika nalaze se među zaposlenima:

| Šifra | Naziv u šifarniku | Zaposleni |
|---|---|---|
| `315400` | Delic Ivana | Ivana Delić Nikolić |
| `317700` | Jankovic Ksenija | Ksenija Janković |
| `351900` | Radojevic Zagorka | Dr. Zagorka Radojević |
| `360900` | Flajs Zeljko | Željko Flajs |
| `366500` / `367900` | Vasic Milica / Vasic Milos | Milica Vasić / Miloš Vasić |

**Isti projekat se javlja kod više osoba** — to je presudno [P]:

| Sufiks projekta | Kod koliko osoba |
|---|---|
| `702400` (TD 7024) | **19** |
| `190170` | 9 |
| `190200` | 9 |
| `450080` | 7 |
| `160140`, `360170` | po 6 |

Od 55 različitih projekata, **27 deli više osoba**.

> **[P] Ovo nije hijerarhija nego matrica.** Jedna šifra porodice B znači **jedna osoba na
> jednom projektu**. Ne postoji način da stane u stablo tri nivoa:
>
> - ako je osoba drugi nivo, projekat `702400` se cepa na **19 čvorova** i nikad se ne može
>   sabrati kao projekat;
> - ako je projekat drugi nivo, ista osoba se javlja pod više roditelja, što stablo zabranjuje.
>
> **Zaključak: nauka je zaseban šifarnik i ne ulazi u organizaciono stablo.**

**Kako se ponaša na knjiženjima** [P]:

| | |
|---|---|
| Knjiženja sa šifrom porodice B | 2.666 |
| — na koren, dakle na **osobu** | **2.372 (89%)** |
| — na osobu × projekat | 294 (11%) |
| Centar na tim knjiženjima | **uvek `3`, bez izuzetka** |
| Knjiženja sa centrom `3` a šifrom van porodice B | **0** |
| Stvarno upotrebljenih šifara porodice B | **25 od 193** — 23 osobe, 5 projekata |

> **[P] Centar `3` je čist.** Koristi ga isključivo nauka, i nijedna druga šifra. Zato
> `3` može ući u stablo kao **čvor prvog nivoa bez potomaka**, a cela naučna evidencija
> ostaje u svom šifarniku, vezana za taj centar.
>
> **[Z]** Pošto 89% knjiženja ide na osobu a ne na projekat, **nosilac evidencije je osoba**.
> Projekat je druga, ređe korišćena dimenzija.

Četiri šifre završavaju slovom `A` (`320719206A`, `371419206A`) — **[N]** značenje nije
potvrđeno.

### Porodica C — 13 izuzetaka, deset ih je mehaničkih [P]

| Šifra | Centar u bazi | Naziv | Šta je |
|---|---|---|---|
| `110002` | **prazan** | Telo za tehničku ocenu | Centar očigledno `11` — samo nije upisan |
| `430001` | **prazan** | Troškovi amortizacije | Centar očigledno `43` — samo nije upisan |
| `200001`, `209001`–`209007` | `2` | Amortizacija, UO, sindikat, popis… | Centar je **`20`**, upisana je samo prva cifra |
| `432` | `1` | Uvođenje grejanja-gasifikacija | Neaktivna, 3 znaka — **stvarno nepoznato** |
| `vranj` | `11` | Telo za tehničku ocenu | Tekstualna šifra — **stvarno nepoznato** |
| `vranjs` | `43` | Troškovi amortizacije | Tekstualna šifra — **stvarno nepoznato** |
| `111111` | `3` | *(bez naziva)* | **Šifra zaključka, ne posao** — vidi niže |

> **Šta je `111111` — razrešeno pri uvozu 21.09.2026. [P]:** nema naziv, ali nosi
> **5,41 milijardi RSD na 584 reda**. Knjiženja pokazuju šta je: konta **699 „Prenos
> prihoda iz redovnog”**, **599 „Prenos rashoda iz redovnog”**, **710 „Račun rashoda i
> prihoda”** i zbirni prihodi (614, 615, 640) — sve na organizacionoj jedinici **1 (IMS)**.
> To su **zaključna knjiženja na nivou cele ustanove**, ne posao.
>
> Pravilo uvoza odbija šifru bez naziva i time ju je zadržalo van stabla. Da je prošla,
> 5,41 milijardi zaključka bilo bi pripisano centru `11`. **Ne sme ući u stablo poslova.**

Uz to, u `OrganizationalUnit` postoji **`960001` „Test centar”** kojeg nema u
`FinanceJob` — **testni zapis u produkciji** [P].

Rubni razmaci [P]: **174 od 339** šifara u `OrganizationalUnit` ima razmake na kraju, i
**3** centra. To se čisti pri uvozu, uz čuvanje sirove vrednosti.

---

## 3. Odlučujući nalaz — dokumenti koriste skoro isključivo porodicu A

Iako je porodica B **skoro pola šifarnika**, na dokumentima je gotovo nema [P]:

| Izvor | Redova | Porodica A | Porodica B | Izuzeci |
|---|---|---|---|---|
| `finansije.LedgerEntry` | 147.851 | **143.066 (97%)** | 2.666 (2%) | 2.119 (1%) |
| `potrazivanja.ReceivablePosting` | 12.445 | **12.441 (100%)** | 0 | 4 |
| `fleet.FuelConsumption` | 16.118 | **15.927 (99%)** | 0 | 191 (1%) |
| `fleet.Lease` | 23 | 21 | 0 | 2 |
| `fleet.JobCode` (dodele vozila) | 204 | 199 | 0 | 5 |

> **[Z] Zaključak koji određuje redosled rada:** registar se može izgraditi **samo za
> porodicu A** i time pokriti **preko 97% svih stvarnih podataka**. Porodica B ostaje na
> listi za mapiranje — što oba plana izričito dozvoljavaju („*Stare šifre koje ne možemo
> pouzdano rasporediti ostaju na listi za mapiranje; ne izmišljamo im odeljenje da bismo
> popunili stablo*”). **Nauka ne blokira početak.**

---

## 4. Rizik povezivanja je mali — šifre se poklapaju

Provereno je da li šifra sa dokumenta uopšte postoji u šifarniku [P]:

| Izvor | Različitih šifara | Nema u `FinanceJob` |
|---|---|---|
| `finansije.LedgerEntry` | 118 | **0** |
| `potrazivanja.ReceivablePosting` | 42 | **0** |
| `potrazivanja.ReceivablePosition` | 26 | **0** |
| `fleet.FuelConsumption` | 26 | **0** |
| `fleet.Lease` | 8 | **0** |
| `fleet.Employee` | 122 | **122 — sve** |

> **[P] `fleet.Employee.job_code` je šifra radnog mesta, ne šifre posla.** Razrešeno
> merenjem: 123 vrednosti, nijedna se ne poklapa sa `FinanceJob`, `OrganizationalUnit`
> **ni sa šiframa osoba iz nauke** (0 od 66 prefiksa). Presudno je koliko ljudi deli istu
> vrednost — `7152` ima **49 zaposlenih**, `4052` ima **48**, `7117` ima 12. Šifra koju deli
> 49 ljudi ne može biti ni posao ni osoba; to je **klasifikacija radnog mesta** [Z].
>
> Plan je na ovo upozorio („*bez izjednačavanja svih polja `job_code`*”). **Ovo polje se ne
> sme povezati na registar** i pitanje 6 iz odeljka 7 je time zatvoreno.

Ostalo se poklapa **stopostotno**. Migracija veza je zato tehnički niskorizična; rizik je
u istoriji i pravima, ne u podacima.

---

## 5. Koliko je šifarnika zapravo živo

| | |
|---|---|
| Šifara u `FinanceJob` | 415 |
| **Stvarno upotrebljenih na dokumentima** | **118** |
| Nikad upotrebljenih | 297 |
| — od toga već neaktivnih | 71 |
| — **aktivnih a nikad upotrebljenih** | **226** |

> **[Z]** Više od polovine šifarnika je aktivno ali se ne koristi. To nije greška po sebi
> (šifra može čekati posao), ali znači da **pregled aktivnosti nije odraz stvarne upotrebe**.
> Prvi uvoz treba da unese sve, a ekran izbora da nudi upotrebljene prvo.

---

## 6. Razlike između dva postojeća šifarnika

| Provera | Rezultat |
|---|---|
| U `OrganizationalUnit` a nema u `FinanceJob` | **1** — `960001` „Test centar” |
| U `FinanceJob` a nema u `OrganizationalUnit` | **77** — sve neaktivne (potvrđeno u planu) |

Ovo se **poklapa sa planom od 18.09.** i ne otvara novo pitanje.

---

## 7. Pitanja koja moraju dobiti odgovor pre uvoza

**Zatvoreno 21.09.2026.**

| Pitanje | Odgovor |
|---|---|
| **Gde pripada nauka** | **Zaseban šifarnik** — potvrda naručioca, i merenje je potkrepljuje: matrica osoba × projekat ne staje u stablo. Centar `3` ulazi u stablo kao čvor prvog nivoa bez potomaka; 193 šifre ostaju u svom šifarniku [P] |
| **Šta je `fleet.Employee.job_code`** | **Šifra radnog mesta** — jednu vrednost deli do 49 zaposlenih [P]. Ne povezuje se na registar |

**Još otvoreno** [N] — ne može odgovoriti ni kod ni baza:

1. **Kako se zove i šta znači drugi nivo** u porodici A (treći znak šifre)? Da li je `0`
   zaista „zajedničko/režija”?
2. **Šta su `432`, `vranj`, `vranjs`, `111111`?** Zadržati, preimenovati ili ugasiti.
3. **Sme li se `960001` „Test centar” ukloniti iz produkcije?**
4. **Da li su `200001` i `209001`–`209007` centar `20`?** Ako jesu, to je ispravka podatka,
   ne mapiranje, i svodi izuzetke sa 13 na 3.
5. **Šta znači slovo `A`** na kraju četiri naučne šifre.

**Nijedno od ovih pitanja ne blokira izradu registra ni uvoz porodice A.**

---

## 8. Šta ovaj popis menja u postojećim planovima

| Tvrdnja u planu | Stanje posle merenja |
|---|---|
| „415 poslovnih šifara, 88/250/22/55” | **Potvrđeno** [P] |
| „339 zapisa `OrganizationalUnit`” | **Potvrđeno** [P] |
| „`960001` nema par u finansijskom šifarniku” | **Potvrđeno** — i to je *Test centar* [P] |
| „svih 77 šifara samo u finansijskom šifarniku su neaktivne” | **Potvrđeno** [P] |
| „`110002` i `430001` imaju prazan centar” | **Potvrđeno**, uz još 8 sličnih (`2` umesto `20`) [P] |
| „ne propisivati obrazac 2+1+3 svim podacima” | **Opravdano** — drži se za 209 od 415 [P] |
| „HR `job_code` nije isto” | **Potvrđeno merenjem** — 0 poklapanja od 122 [P] |
| *(nije bilo u planu)* | **Nova porodica B, 193 šifre nauke sa drugačijom logikom** [P] |
| *(nije bilo u planu)* | **Porodica A pokriva 97%+ dokumenata** — nauka ne blokira početak [P] |
| *(nije bilo u planu)* | **Nauka je matrica osoba × projekat**, ne hijerarhija; isti projekat kod do 19 osoba [P] |
| *(nije bilo u planu)* | **`Employee.job_code` je radno mesto** — jednu vrednost deli 49 ljudi [P] |

---

## 9. Gde su mereni podaci

Merenje je izvršeno nad `ims_erp.settings.development` sa `default` usmerenim na
produkciju, isključivo `SELECT` upitima kroz Django ORM nad:
`finansije.FinanceJob`, `finansije.LedgerEntry`, `fleet.OrganizationalUnit`,
`fleet.JobCode`, `fleet.FuelConsumption`, `fleet.Employee`, `fleet.Lease`,
`potrazivanja.ReceivablePosting`, `potrazivanja.ReceivablePosition`.
