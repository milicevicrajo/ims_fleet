# Plan izrade centralnog registra šifara posla

Datum: **21.09.2026.** · Status: **predlog za odobrenje, bez implementacije**

Ovaj plan razrađuje **korak 1 i 2** iz [plana organizacije i dozvola V2](plan-organizacije-i-dozvola-v2.md)
i **fazu 1 i 2** iz [plana centralizacije](plan-centralizacije-organizacije.md).
Za razliku od njih, oslanja se na **izmerene podatke** iz
[popisa nad produkcionom bazom](popis-sifara-posla-korak-0.md), a ne na primer iz razgovora.

> Status tvrdnji: **[P]** izmereno, **[Z]** zaključeno, **[N]** nepotvrđeno.

**Odgovor na postavljeno pitanje:** da — registar se pravi **odvojeno i paralelno**, a
moduli se prevode **jedan po jedan**, svaki sa svojim prekidačem i svojim povratkom.
To je i ono što oba postojeća plana traže. Novo je što se sada zna **kojim redosledom se
isplati** i **šta se sme izostaviti na početku**.

---

## 1. Osnovno pravilo celog posla

**Registar se prvo samo puni i poredi. Ništa ga ne čita u obračunu dok se modul izričito
ne prebaci.** U svakom trenutku postoji tačno jedan modul koji je „u prelasku”; ostali rade
nepromenjeno.

Tri zabrane koje važe kroz sve faze:

| Zabrana | Razlog |
|---|---|
| Ne brisati i ne preimenovati `OrganizationalUnit`, `FinanceJob` ni njihova polja | 3.651 putni nalog, 1.164 veze faktura i 204 dodele vozila drže FK na `OrganizationalUnit` [P] |
| Ne dirati `fleet.Employee.job_code` | To je **šifra radnog mesta** — jednu vrednost deli do **49 zaposlenih** [P] |
| Ne menjati brojeve dokumenata koji u sebi sadrže šifru centra | `PutniNalog` i `ProcurementCase` izvode broj iz centra [P] |

---

## 2. Faza 1 — registar koji ništa ne menja

Samostalna isporuka. Posle nje aplikacija radi **identično** kao pre.

### 2.1 Nova aplikacija `organizacija`

| Model | Šta nosi |
|---|---|
| `OrgNode` | Stalni ID, firma, nivo 1/2/3. **Nikad se ne menja ni ne briše.** |
| `OrgNodeVersion` | Naziv, segment, puna šifra, roditelj, aktivnost, profitnost, `vazi_od` / `vazi_do` |
| `ExternalOrgMapping` | Izvorni sistem, sirova šifra (sa razmacima, neobrađena), period, ciljni `OrgNode` |
| `LegacyOrgLink` | `OrganizationalUnit.id` i `FinanceJob.id` → `OrgNode`. Više starih zapisa sme voditi na isti čvor. |
| `OrgImportRun` | Kada, ko/šta, koliko uneto, koliko na listi za razrešenje, izveštaj razlika |

Provere u bazi: bez ciklusa, bez preklapanja intervala za isti čvor, puna šifra
jedinstvena u firmi i periodu, dete i roditelj u istoj firmi.

> Intervali su **od uključivo do isključivo**. Objavljena verzija se ne prepravlja —
> pravi se nova.

### 2.2 Uvoz — samo porodica A

Prvi uvoz unosi **209 šifara porodice A** i iz njih gradi stablo:

```
nivo 1: 10 centara        41 42 43 44 50 60 70 81 82 83
nivo 2: treći znak šifre  0–9 unutar centra
nivo 3: 209 poslova       puna šifra = segment1 + segment2 + segment3
```

Veza roditelj–dete se upisuje **eksplicitno**. Prefiks se koristi **samo jednom, pri prvom
uvozu, kao predlog** koji ulazi u izveštaj za potvrdu — posle toga pripadnost se nikad ne
izvodi sečenjem teksta.

Uz njih ulazi i **centar `3` (Nauka) kao čvor prvog nivoa bez potomaka**.

**Šta se ne unosi u stablo:**

| Skup | Šifara | Postupak |
|---|---|---|
| **Porodica B — nauka** | 193 | **Trajno van stabla.** Odluka naručioca (21.09.2026.): nauka je **zaseban šifarnik**. Merenje je potvrđuje — to je matrica **osoba × projekat**, a ne hijerarhija: isti projekat se javlja kod do **19 osoba** [P]. Šifre se vezuju za čvor centra `3`. |
| Porodica C — izuzeci | 13 | Nerazvrstani, sa označenim razlogom za svaki, do odluke |

Ovo pokriva **preko 97% stvarnih dokumenata** [P].

> **Zašto nauka ne može u stablo** [P]: ako bi osoba bila drugi nivo, projekat `702400` bi
> se rascepio na 19 čvorova i nikad se ne bi mogao sabrati kao projekat; ako bi projekat bio
> drugi nivo, ista osoba bi imala više roditelja, što stablo zabranjuje. Nijedan raspored
> nije tačan, pa se ne pravi nijedan.

### 2.3 Naučni šifarnik — zaseban, kasnija faza

Nije predmet ove isporuke, ali se beleži šta je izmereno, da se kasnije ne pogađa [P]:

| | |
|---|---|
| Šifara | 193, od toga **stvarno upotrebljenih 25** |
| Osoba (prefiks 4 znaka) | 66 u šifarniku, **23 u knjiženjima** |
| Projekata (sufiks) | 55 u šifarniku, **5 u knjiženjima** |
| Knjiženja | 2.666, od toga **2.372 (89%) na osobu**, 294 na osobu × projekat |
| Centar na tim knjiženjima | **uvek `3`**; nijedna druga šifra ne koristi centar `3` |

> **[Z] Kada dođe red na naučni šifarnik**, on traži dve tabele — **osoba** i **projekat** —
> i vezu među njima, a ne stablo. Pošto 89% knjiženja ide na osobu, **osoba je nosilac**, a
> projekat druga dimenzija. Osobe se **[Z]** verovatno mogu povezati sa kadrovskom
> evidencijom: poređenje po imenu je već dalo parove (`315400 Delić Ivana` → zaposlena Ivana
> Delić Nikolić). To povezivanje mora biti **potvrđeno pojedinačno**, ne po sličnosti imena.

### 2.4 Ekran u Adminu — samo za čitanje

Stablo levo, kartica čvora desno, pretraga po šifri i nazivu, spisak nerazvrstanih.
Bez ijednog dugmeta za izmenu u ovoj fazi.

### 2.5 Kontrolni izveštaj — uslov za nastavak

Uvoz se smatra uspešnim tek kad izveštaj pokaže:

- svih 209 poslova porodice A ima potvrđena oba nadređena nivoa;
- nijedna puna šifra se ne ponavlja;
- **za svaku od 118 stvarno upotrebljenih šifara postoji čvor ili obrazložen izuzetak** [P];
- ponovljeni uvoz ne pravi duplikate ni nove verzije bez stvarne promene;
- zbir `LedgerEntry` po centru izračunat preko registra **jednak** zbiru preko postojećeg
  tekstualnog polja, za isti period.

Poslednja stavka je najvažnija: to je dokaz da registar opisuje iste podatke.

### 2.6 Nalaz o obrtu — lokalno gašenje neupotrebljenih šifara

Urađeno 21.09.2026. na zahtev naručioca: **šifra bez obrta novca u poslednjih 12 meseci
proglašava se neaktivnom.**

**Zašto to nije prosto `is_active = False`** [P]: aktivnost dolazi iz poslovnog sistema
kroz `FinanceJob.active`. Da je zastavica prepisana, sledeći `uvezi_organizaciju` bi je
vratio i napravio novu verziju bez stvarne promene — oznaka bi **oscilovala između dva
uvoza**, a istorija bi se punila lažnim redovima. To je tačno ono na šta plan upozorava:
*„Ne smeju postojati dva nezavisna mesta koja menjaju istu oznaku bez dogovorenog
prioriteta.”*

Zato postoji model `JobActivityReview`: čuva **šta je izmereno i kada**, a uvoz ga
poštuje — posao je aktivan samo ako ga i izvor drži aktivnim **i** ako ima obrt.

| Pravilo | |
|---|---|
| Mera | knjiženje sa iznosom različitim od nule, po **datumu knjiženja** |
| Obuhvat | sve šifre koje je čvor ikada nosio, da promena šifre ne izgleda kao prestanak rada |
| Smer | **jednosmerno** — nalaz može samo da ugasi, nikad da upali |
| Izvor podataka | `finansije.LedgerEntry`; upisuje se **isključivo** u tabele registra |

**Rezultat nad produkcijom, prozor 21.09.2025 – 21.09.2026** [P]:

| | |
|---|---|
| Poslova u stablu | 220 |
| Sa obrtom | 88 |
| Bez obrta | 132 |
| — aktivni po izvoru, **ugašeni nalazom** | **61** |
| — već neaktivni, nalaz ih potvrđuje | 71 |
| Aktivnih posle nalaza | **83** (bilo 144) |

> **Provera pouzdanosti [P]:** od 61 ugašenog, **56 nema nijedno knjiženje** otkad
> Finansije uopšte imaju podatke (01.01.2025). Samo jedna šifra (`606001`) je blizu
> granice — poslednje knjiženje 04.09.2025, sedamnaest dana pre početka prozora.
> `430111 Administracija`, `430999 Režija` i `429999 Poslovi režije` imaju **nula
> knjiženja ikada**.

> **Sukob koji traži objašnjenje [P]:** pet šifara je **neaktivno po izvoru, a ima obrt**
> u prozoru — `412113`, `413114`, `442902`, `444111`, `707003`. One se **ne pale**, jer
> je izvor merodavan za gašenje. Ali novac koji se kreće na ugašenoj šifri je nalaz sam
> po sebi i treba ga razrešiti.

Pokreće se sa `python manage.py oznaci_neaktivne --meseci 12`, uz `--proba` za prikaz bez
upisa. Ponovno pokretanje ne menja ništa ako se podaci nisu promenili.

**Šta ovo ne radi** [P]: ne dira `FinanceJob`, ne dira knjiženja i ne menja poslovni
sistem. Gašenje važi **samo u registru**, koji Faza 1 ionako ne koristi ni u jednom
obračunu.

---

## 3. Faza 2 — moduli, jedan po jedan

Svaki modul dobija **opcionu** vezu `org_node` pored postojećeg polja. Staro polje ostaje
i dalje se upisuje. Modul se prebacuje na čitanje iz registra tek kad njegov izveštaj
prođe.

### Redosled — i zašto se razlikuje od V2

V2 predviđa pilot **Finansije + Potraživanja**, jer tamo najviše boli pitanje **prava
pristupa**. Ovaj plan se bavi **registrom**, ne pravima, pa je redosled drugačiji — vodi
ga cena povezivanja, koja je izmerena:

| # | Modul | Kako je sada vezan | Obim | Zašto tim redom |
|---|---|---|---|---|
| **1** | **Flota** | **FK** na `OrganizationalUnit` | 204 dodele, 3.651 nalog, 16.118 goriva | Veza je FK→FK, najjeftinija. Najveći broj testova. Odmah rešava [P-52](docs/10-poznati-problemi.md#p-52--ulazni-podaci-ekonomike-su-prazni-na-produkciji) |
| **2** | **Nabavka** | **FK** na `OrganizationalUnit` | 242 predmeta, 1.164 veze | Ista vrsta veze; već podržava više poslova po fakturi |
| **3** | **Finansije** | tekst `job_code` | **147.851 red** | 118 različitih šifara, **sve postoje u šifarniku** [P]. Najveći obim, ali nula nepoznatih |
| **4** | **Potraživanja** | tekst `job_code` | 12.445 + 9.516 | 100% poklapanje [P]; zavisi od Finansija |
| **5** | **Ugovori, Menice, Mobilni** | tekst centra | mali | Male količine, nose malo rizika |
| **—** | **HR** | **šifra radnog mesta** | 369 zaposlenih | **Ne prebacuje se.** Razrešeno merenjem: nije šifra posla |

> **[Z] Zašto Flota prva:** ona jedina spaja tri stvari — vezu koja je već strukturirana,
> mali obim i postojeću pokrivenost testovima. Ako se pokaže da model tri nivoa negde ne
> radi, bolje je da se to vidi na 204 dodele nego na 147.851 knjiženju.

### Šta se radi u svakom modulu

1. Dodati `org_node` kao **null, opciono**. Staro polje ostaje merodavno.
2. Popuniti vezu u **ponovljivim paketima**; nepovezani redovi idu u izveštaj, ne u nulu.
3. Napraviti **uporedni izveštaj**: isti period, isti korisnik, stari i novi put — iznosi
   moraju biti identični.
4. Tek tada uključiti čitanje iz registra, **za sve rute modula odjednom**.
5. Staro polje se i dalje upisuje tokom perioda stabilizacije.

Pravilo iz V2 koje ovde važi doslovno: **nema režima „stari ILI novi pristup”** unutar
jednog modula. Delimično prebačen modul je gori od neprebačenog.

### Flota — koraci 1–3 izvedeni 25.09.2026.

| Korak | Kako je urađeno |
|---|---|
| 1. `org_node` | Opciona kolona na `JobCode`, `PutniNalog`, `VehicleTravelOrder`, `ProcurementRequest`, `FuelConsumption`, `Lease` (`fleet/migrations/0084`). Pri svakom čuvanju se **izvodi** iz starog polja (`organizacija/signals.py`); ručni upis se prepisuje |
| 2. Popunjavanje | `manage.py povezi_flotu [--proba] [--model …] [--paket N]` — paketi po 500, menja samo ono što odstupa, pa je ponovljivo. Hvata i masovne izmene (`update`) koje signal ne vidi |
| 3. Uporedni izveštaj | `/organizacija/flota/` i `povezi_flotu --izvestaj`: broj i iznos po centru, starim putem (`OrganizationalUnit.center`) i kroz upisani `org_node`; gorivo i po dodeli vozila važećoj na dan točenja — putem kojim ga Flota raspoređuje |
| 4. Čitanje iz registra | **Uključeno 25.09.2026. za spiskove i nazive** (`fleet/support/registar.py`, prekidač `FLOTA_REGISTAR_ORGANIZACIJE`): izbor šifre u svim formama Flote nudi samo aktivne šifre iz registra (uz već upisanu vrednost), oznake su iz registra, a centri u filterima, na kontrolnoj tabli i u pravima pristupa nose naziv po pravilniku. Staro polje se i dalje upisuje i ostaje ključ za filtere, zbirove, pristup i brojeve putnih naloga — centar je u registru isti za sve zapise, pa se zbirovi ne menjaju |

**Paralelna sinhronizacija [P]:** stara `fleet.tasks.fetch_job_codes` (01:30) i dalje puni
`OrganizationalUnit` i ostaje merodavna. Nova `organizacija.tasks.sync_organizacija_task`
(01:40, ručno `manage.py sync_organizacija`) iz istog izvora (`posao` → `FinanceJob`) osvežava
registar, povezuje jedinice i zapise Flote i poredi staru i novu organizaciju. Rezultat piše u
istoriju zadataka; staru organizaciju ne dira.

Razrešavanje je bez pogađanja: jedinica Flote preko `LegacyOrgLink` (po primarnom ključu),
a ako veze još nema — tačnom šifrom iz šifarnika poslova; tekstualna šifra goriva i lizinga
samo tačnom šifrom. Prefiks se ne koristi, osim potvrđenog pravila nauke (ispod).

**Odluke naručioca 25.09.2026. [P]:**

| Pitanje | Odluka | Kako je sprovedeno |
|---|---|---|
| Centar poslovnog i naučnog bloka | **`2` i `3`**, kako stoje u šifarniku (`posao.blok`) i u Floti. Knjiženja ih vode kao jedinice `20` i `30` | Uvoz jedinicu knjiženja `20`/`30` upisuje kao centar `2`/`3` (`OZNAKA_CENTRA_IZ_KNJIZENJA`); postojeće verzije ispravljene na mestu (`organizacija/migrations/0005`). Stari podatak, brojevi putnih naloga (`2/2026-…`) i pristup po centru ostaju nepromenjeni |
| Naučne šifre | **`3` + šifra radnika iz Kadrova (3 cifre) + broj projekta (slobodan unos)**; koren `3` + radnik + `00` je sam radnik. **Deo su bloka 3, nije zaseban šifarnik** (ispravlja odluku od 21.09.) | U stablu: centar `3` (u knjiženjima OJ `30`) → **naučni projekat** `3-<broj projekta>` (npr. `3-702400` TD 7024, 19 radnika) → šifra kao učešće radnika na projektu. Koren `3` + radnik + `00` je projekat `3-00` „bez projekta”. Radnik se **povezuje sa Kadrovima** po ličnom broju (prikaz, sa poređenjem prezimena). Nosioci `133`, `233`, `333` nisu radnici — zbirne institutske teme, grupisane po nosiocu |
| Nazivi centara i jedinica | Po **Pravilniku o organizaciji (18.04.2024.)**, latinicom | `organizacija/services/pravilnik.py`. Numeracija šifara prati pravilnik (deo 3 → `3`, 4.1–4.4 → `41`–`44`, 8.1–8.3 → `81`–`83`, 4.1.1 → `411`…). U registar se upisuje samo naziv gde se poklapaju broj i sadržaj poslova (21 jedinica); ostalih 11 su predlog „proveriti”. Naziv iz pravilnika ispravlja postojeću verziju na mestu |

Provereno na Kadrovima: kod svih aktivnih radnika tri cifre posle `3` su njihova šifra
(`315400` → 154 Delić Nikolić Ivana, `357900` → 579 Bojović Dragan…). Neupareni brojevi su
bivši radnici i zbirni nosioci.

**Proba nad produkcionim podacima (samo čitanje, pre migracije) [P]:**

| Model | Zapisa | Povezano | Bez šifre | Razlika centra |
|---|---:|---:|---:|---:|
| Dodele vozila | 205 | 205 | 0 | 0 |
| Putni nalozi | 3.770 | 3.770 | 0 | 0 |
| Nalozi za vozila | 250 | 10 | 240 | 0 |
| GZN | 2 | 2 | 0 | 0 |
| Gorivo | 16.212 | 16.212 | 0 | 0 |
| Lizing | 23 | 23 | 0 | 0 |

Gorivo po dodeli vozila poklapa se **do dinara u svih 9 centara** (2, 41, 42, 43, 44, 70, 81,
82, 83). Organizacione jedinice: **335 od 339** imaju čvor, sve sa istim centrom (od toga 191
naučnih u bloku 3). Van registra su samo `111111`, `vranj`, `vranjs` (otvoreno pitanje 2)
i `960001` (pitanje 3) — na njima nema zapisa Flote.

**Uvoz 25.09.2026. [P]:** 13 centara, 115 jedinica (od toga 60 u bloku 3: 55 projekata i
grupe), 411 poslova (220 poslovnih + 191 naučna), 0 zatvorenih verzija. Na listi za razrešenje
ostaju 4 izuzetka porodice C; u knjiženjima su nerazrešene samo stavke bez šifre i `111111`.
Naučne šifre: 89 povezano sa Kadrovima, 80 na brojevima kojih nema u Kadrovima (bivši radnici),
22 zbirne. **Za proveru:** lični brojevi 657, 998 i 999 u Kadrovima pripadaju drugim osobama
nego u nazivima šifara; projekti P36014 i P36017 upisani su pod dva broja (`36014`/`360140`,
`36017`/`360170`) — broj je slobodan unos, pa se ne spajaju bez potvrde.

**Uslov za korak 4 — ispunjen 25.09.2026. [P]:** veza `org_node` popunjena na bazi (20.222
zapisa: 205 dodela, 3.770 putnih naloga, 10 naloga za vozila, 2 GZN, 16.212 goriva, 23 lizinga;
240 naloga za vozila je bez šifre), uporedni izveštaj **prolazi** u svih 7 delova, 0 razlika.
Pre toga su sve šifre koje Flota koristi (25 tekućih dodela, 29 šifara na putnim nalozima od 2025.,
4 na nalozima za vozila) potvrđene kao aktivne u registru.

---

## 4. Šta se ne radi u ovom poslu

| Ne radi se | Kada |
|---|---|
| Dodele uloga sa obuhvatom i novi sistem prava | Zaseban posao, korak 2–3 u V2 |
| Objava nove sistematizacije | Korak 8 u V2; traži datum i mapu staro → novo |
| Uređivanje stabla kroz aplikaciju | Faza posle registra; prvo samo čitanje |
| Brisanje starih kolona i modela | Tek po završenoj stabilizaciji svih modula |
| Upis nazad u izvorni poslovni sistem | Nije predmet nijednog plana |

---

## 5. Odluke potrebne pre početka

**Razrešeno 21.09.2026. — nema više blokade:**

| Pitanje | Odgovor |
|---|---|
| Gde pripada nauka | ~~Zaseban šifarnik, van stabla~~ — **izmenjeno 25.09.2026.:** deo bloka 3; radnik je jedinica drugog nivoa, šifra je posao |
| Šta je `Employee.job_code` | **Šifra radnog mesta** — ne povezuje se |

**Otvoreno, ali ne blokira faze 1 i 2:**

1. Naziv i značenje drugog nivoa u porodici A; da li je `0` zaista „zajedničko/režija”.
   Potrebno pre nego što se stablo prikaže korisnicima sa nazivima nivoa.
2. Šta su `432`, `vranj`, `vranjs`, `111111`.
3. Sme li se `960001` „Test centar” ukloniti iz produkcije.
4. ~~Da li su `200001` i `209001`–`209007` centar `20`~~ — **razrešeno 25.09.2026.:** centri
   blokova su `2` i `3`; `20` i `30` su samo jedinice knjiženja (poglavlje 3, Flota).
5. Šta znači slovo `A` na kraju četiri naučne šifre.

> **Faza 1 može početi odmah.** Nijedno preostalo pitanje ne utiče na model podataka ni na
> uvoz porodice A.

---

## 6. Provere pre puštanja svake faze

| Provera | Očekivano |
|---|---|
| Ponovljen uvoz bez promene u izvoru | Nema novih verzija ni duplikata |
| Prekinut uvoz | Nema polupopunjenog stabla; objava je atomska |
| Šifra sa rubnim razmacima | Isti čvor kao bez njih; sirova vrednost sačuvana |
| Vodeće nule (`430001`) | Sačuvane, nije pretvoreno u broj |
| Nepoznata šifra u uvozu | Zapis sačuvan, upozorenje evidentirano, **bez dodele centra po prefiksu** |
| Zbir po centru — stari put naspram registra | **Identičan** za isti period |
| Broj putnog naloga i predmeta nabavke | **Nepromenjen** |
| Isključivanje modula iz registra | Modul radi kao pre, bez gubitka novih unosa |

---

## 7. Složenost

| Deo | Procena | Glavni rizik |
|---|---|---|
| Registar i uvoz porodice A | **Niska** | Značenje drugog nivoa nije potvrđeno |
| Admin stablo za čitanje | **Niska** | — |
| Povezivanje Flote i Nabavke | **Niska** | Brojevi dokumenata izvedeni iz centra |
| Povezivanje Finansija i Potraživanja | **Srednja** | Obim; uporedni izveštaj mora biti tačan do dinara |
| Naučni šifarnik (zasebna, kasnija isporuka) | **Srednja** | Osoba × projekat; povezivanje osoba sa kadrovskom mora biti potvrđeno pojedinačno |
| HR | — | **Ne radi se** — nije isti šifarnik |

Prva isporuka — registar, uvoz porodice A, stablo za čitanje i kontrolni izveštaj — je
**niska složenost** i ne dodiruje nijedan postojeći obračun. To je i razlog da se počne
od nje.
