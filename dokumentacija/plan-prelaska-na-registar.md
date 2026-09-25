# Plan prelaska na registar organizacije — čitanje, prava i gašenje stare organizacije

Datum: **25.09.2026.** · Status: **u realizaciji** — koraci 1, 2 i 3 izvedeni, korak 4 izveden (senka: 4 razlike, sve potvrđene); ništa od toga još ne odlučuje o pristupu

Ovaj plan je nastavak [plana registra šifara posla](plan-registra-sifara-posla.md) i razrađuje
preostale korake **2–9** iz [plana organizacije i dozvola V2](plan-organizacije-i-dozvola-v2.md),
sada kada su svi moduli sa šifrom posla povezani sa registrom.

> Status tvrdnji: **[P]** izmereno ili provereno u kodu, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Gde smo stali

Registar postoji, sinhronizuje se svake noći paralelno sa starom organizacijom, i **svi
zapisi sa šifrom posla imaju vezu `org_node`** [P]:

| Modul | Veza u bazi | Uporedni izveštaj | Šta već čita iz registra |
|---|---:|---|---|
| Flota | 20.222 | prolazi (7 delova) | spiskovi i nazivi šifara i centara |
| Nabavka | 1.784 | prolazi (3 dela) | spiskovi i nazivi šifara |
| Finansije | 149.195 | prolazi (584 tehnička) | nazivi centara |
| Potraživanja | 21.961 | prolazi (2 dela) | — |

**Šta i dalje radi preko stare organizacije** [P]:

- **filteri, zbirovi i grupisanja po centru** — u svakom modulu, preko starog polja
  (`OrganizationalUnit.center`, `LedgerEntry.center`, `center_code`);
- **prava pristupa po centru** — `CustomUser.allowed_centers` (M2M na `OrganizationalUnit`),
  `allowed_center_codes` (tekst); `allowed_hr_unit_codes` (kadrovske OJ) uklonjen je 25.09.2026.;
- **brojevi dokumenata** — putni nalog `43/2026-…`, predmet nabavke `ZN-43/2026-…`;
- **stara sinhronizacija** (`fetch_job_codes`, 01:30) i tabela `OrganizationalUnit`.

Oba izvora danas daju **isti centar za svaki zapis** (uporedni izveštaji). Zato prelazak na
registar ne menja brojke sam po sebi — menja **ko šta vidi** kad se uvedu prava po obuhvatu,
i omogućava istoriju pripadnosti, koju stara organizacija nema.

---

## 2. Pravila koja važe kroz ceo prelazak

| Pravilo | Razlog |
|---|---|
| **Jedan modul u prelasku u jednom trenutku** | Greška se vidi na jednom mestu i vraća se jednim prekidačem |
| **Unutar modula nema „staro ILI novo”** — filteri, zbirovi i prava prelaze **zajedno**, za sve rute modula | Delimično prebačen modul je gori od neprebačenog (pravilo iz V2) |
| **Staro polje se i dalje upisuje** do kraja stabilizacije svih modula | Povratak je samo prekidač, bez vraćanja podataka |
| **Brojevi dokumenata se ne menjaju** | Putni nalog i predmet nabavke nose oznaku centra (`2/2026-…`) |
| **Formule obračuna se ne menjaju** | Pravilo 5 iz AGENTS.md; menja se samo odakle se čita centar |
| **Nijedno pravo se ne proširuje tiho** | Svaka razlika u pristupu je razrešena ili pisano potvrđena (V2, pogl. 6) |
| **Ništa se ne briše** — kolone i `OrganizationalUnit` ostaju za istoriju | Strani ključevi 3.770 putnih naloga, 1.227 veza faktura, 205 dodela |

---

## 3. Četiri toka posla

### 3.1. Putanja čvora i istorija pripadnosti — osnova za sve ostalo

Danas se centar zapisa dobija iz važeće verzije čvora, u memoriji (`node_center_map`). Za
filtere i zbirove u bazi potreban je **jedan spoj** od zapisa do centra, i to **na datum**.

**Predlog [Z]:** tabela putanje `OrgPutanja(posao, jedinica, centar, vazi_od, vazi_do)` —
jedan red po šifri posla i periodu u kome je važila ta pripadnost. Puni je uvoz registra
(ponovljivo, isto kao verzije). Upit tada glasi:

```text
zapis.org_node → OrgPutanja (vazi_od ≤ datum dokumenta < vazi_do) → centar
```

| Pitanje | Odgovor |
|---|---|
| Koji datum određuje pripadnost | Datum dokumenta (putni nalog, faktura, knjiženje); za Flotu i dalje dodela vozila važeća na dan — to pravilo već postoji |
| Šta kad šifra promeni centar | Novi red putanje od datuma promene; stari dokumenti ostaju u starom centru (V2, pogl. 4 — „snimak na dokumentu”) |
| Složenost | **Niska** — izvodi se iz postojećih verzija, bez novih izvora |

### 3.2. Prava sa obuhvatom — najveći deo posla

Ovo su koraci **2–4 iz V2**. Danas prava i obuhvat žive odvojeno i na tri načina [P]:

| Mehanizam | Gde se čita [P] |
|---|---|
| `allowed_centers` (M2M na `OrganizationalUnit`) | 15 fajlova u Floti, po 2 u Potraživanjima, HR i core, 1 u Finansijama |
| `allowed_center_codes` (tekst, zarezi) | 7 u Floti, 2 u HR i core, po 1 u Finansijama i Potraživanjima |
| ~~`allowed_hr_unit_codes`~~ (kadrovske OJ) | **uklonjeno 25.09.2026.** — niko ga nije koristio |
| Pomoćne funkcije obuhvata | `finansije.access.visible_scope`, `potrazivanja.access.scoped`, `fleet.mixins.CenterMixin`, `fleet.support.management_reports.allowed_centers`, `putni_nalozi._get_allowed_centers`, `hr.access.allowed_unit_codes` — **šest različitih tumačenja** |

Ista dva polja se u Floti negde sabiraju, a negde se čita samo M2M (popis mesta u kodu od
25.09.2026.: kontrolna tabla, saobraćajne dozvole i prijem vozila čitaju samo M2M) [P].

**Predlog [Z]:**

1. **Dodela uloge sa obuhvatom** — `DodelaUloge(korisnik, uloga, cvor, vazi_od, vazi_do)`,
   gde je čvor centar, jedinica ili šifra posla. Obuhvat centra pokriva njegove jedinice i
   poslove; obuhvat posla **ne** daje ceo centar.
2. **Jedna provera** umesto šest: `ima_pravo(korisnik, kod_dozvole, zapis)` i
   `obuhvat(korisnik, kod_dozvole) → skup čvorova`, sa jasnim značenjem praznog obuhvata.
3. **Prevod starih prava u nacrt** (bez uticaja na rad):

   | Staro | Prevodi se u |
   |---|---|
   | `allowed_centers` (OJ) | **ceo centar te OJ**, kao danas (odluka 25.09.2026.) |
   | `allowed_center_codes` | čvor centra; oznake `20`, `30` → centri `2`, `3`; `96` (Test centar) → ništa [P] |
   | ~~`allowed_hr_unit_codes`~~ | uklonjeno 25.09.2026. — nema posebne kadrovske organizacije |
   | Uloga „Uprava” | obuhvat cele firme |

4. **Senka** (V2, korak 4): nova provera se računa uporedo sa starom, ali ne odlučuje. Svaka
   razlika (korisnik × modul × skup zapisa) ide u izveštaj; prelazi se tek kad je spisak prazan
   ili svaka stavka potvrđena.

**Izmereno [P]:** 320 aktivnih korisnika, 312 sa ograničenjem po centrima. Četiri korisnika
imaju oznake bez ijedne šifre (`20`, `30`, `96`) — ne gube ništa prevodom.

**Izvedeno 25.09.2026. [P]** — putanja, model prava, prevod i senka (ništa od toga ne odlučuje o
pristupu):

| Deo | Stanje |
|---|---|
| Putanja čvora (3.1) | `OrgPutanja`, 411 redova; gradi je svaki uvoz registra; centar na danas jednak dosadašnjem za svih 411 poslova |
| Model prava | `DodelaUloge` (korisnik, uloga, čvor ili cela firma, period, status `nacrt`/`aktivna`); provera `organizacija/services/prava.py` — `obuhvat`, `q_obuhvata`, `ima_pravo`; prazan obuhvat = nema pristupa |
| Prevod | `manage.py prava_u_senci`: 319 korisnika sa ulogom → 437 dodela u nacrtu; oznaka `96` (2 korisnika) bez čvora |
| Senka | **0 korisnika sa razlikom** u Finansijama, Potraživanjima i putnim nalozima |

Zašto nema razlika: od 320 korisnika **310 ima obuhvat samo tekstom centra**, a **samo 2 imaju
pojedinačne OJ** (`bilja` 140, `suzana.injac` 23); 8 nema obuhvat. Finansije otvaraju 3
korisnika, Potraživanja 7 — svi sa punim pristupom (`view_all`); putne naloge 9 (3 Uprava, 6 po
tekstu centra). Odluka 3 je doneta tako da ta dva korisnika zadrže današnji pristup.

**Korisnici bez obuhvata [P]** (8): `helena.stevancevic` (Uprava — cela firma), `ivana.sibinovic`
(u Potraživanjima `view_all`), `ana.andjelkovic` i `milena.stojanovski` — **odluka 25.09.2026.:
uloge Nabavka i Blagajna vide sve** (cela firma, kao Uprava i Garaža; nacrt obema odobren);
`zoran` (Garaža) — cela firma. Probni nalozi `tmp-putni`, `render-check-phone-filter`,
`render-check-phone-filter-2` i uloge `render-check`, `render-check-2` **obrisani su 25.09.2026.**
**Senka za Flotu (25.09.2026.) [P]** — poredi i spisak vozila i kontrolnu tablu Flote. Današnja
pravila koja senka poštuje: **spisak vozila nema ograničenje po centru** (svako sa `vehicle_list`
vidi sva vozila); kontrolna tabla gleda samo centre dodeljenih OJ. Kadrovi nisu u senci (3.3).
Rezultat na živoj bazi: 320 korisnika, **4 sa razlikom — sve potvrđene**:

| Korisnik | Razlika | Uzrok |
|---|---|---|
| `zoran` (Garaža) | putni nalozi 0 → 3.740 | Garaža — cela firma, samo čitanje; potvrđeno |
| `mirjana.zivanovic`, `olivera.mazibrada`, `vladimir.markovic` (Pregled, centar 43) | vozila i kontrolna tabla 164 → 98 | Danas vide sva vozila jer spisak nema ograničenje; **odlučeno 25.09.2026.: samo svoj centar** — važi za svakog korisnika vozila osim Uprave i Garaže |

### 3.3. Kadrovi i sistematizacija — bez posebne kadrovske organizacije

**Odluka naručioca 25.09.2026.: kadrovske OJ se ne vode posebno — to je dupliranje organizacije.**
Postoji **jedna organizacija**, registar. Zato [P]:

- nema kadrovske mape (`KadrovskaOJ`) ni pravila „OJ istog broja ili prefiks centra” — prvobitni
  predlog je povučen, a odluke 5 i 6 (4331/4332/423/4110, oznaka `20`) time su bespredmetne;
- izbor kadrovskih OJ u pravima korisnika (`allowed_hr_unit_codes`) je uklonjen (niko ga nije koristio);
- Kadrovi nisu u senci; kada dođu na red (korak 7), **zaposleni dobija vezu na čvor registra**
  (jedinicu ili centar) na svojoj kartici, isto kao vozila i nalozi, a obuhvat se proverava kroz
  istu dodelu uloge. Do tada Kadrovi rade po starim pravima (`hr.access`, po centrima).
- **Uprava vidi sve zaposlene** (odluka 25.09.2026.) — danas je u Kadrovima ograničena svojim
  centrima (`helena.stevancevic` 0, `milivoje.peric` 31, `bilja` 361 od 371); to se menja prelaskom
  Kadrova na dodele.

Sistematizacija (V2, korak 8 — ko koga vodi, objava od datuma) gradi se na vezi zaposlenog sa
čvorom registra. Potvrda 11 naziva jedinica označenih „proveriti” ostaje otvorena — jedinice 415,
418, 422 i 432 imaju zaposlene, znači da postoje.

### 3.4. Gašenje stare organizacije

Poslednji korak (V2, korak 9). Uslovi za gašenje [Z]:

1. nijedan modul ne čita `OrganizationalUnit.center`, `allowed_centers` ni `allowed_center_codes`
   za filter, zbir ili pravo (danas: 36 fajlova u 8 aplikacija referiše `OrganizationalUnit` [P]);
2. najmanje jedan pun mesec rada svih modula na registru bez razlika u noćnom izveštaju;
3. **održavanje `OrganizationalUnit` preuzima nova sinhronizacija** — iz registra upisuje nove
   šifre i izmene naziva, jer postojeći strani ključevi (putni nalozi, dodele, nabavka) i dalje
   pokazuju na tu tabelu. Bez toga bi nova šifra iz `posao` bila u registru, ali ne bi mogla da se
   izabere u formama. Tabela tada ima jednog vlasnika upisa (V2, korak 8).

Tada se isključuje `fetch_job_codes` (01:30). **Tabela `OrganizationalUnit` i stari strani
ključevi ostaju** — za istoriju i brojeve postojećih dokumenata; prestaje samo održavanje.
Nasleđena Naplata ostaje na starom režimu dok se ne ugasi (AGENTS pravilo 7).

---

## 4. Redosled i uslovi završetka

| # | Korak | Uslov završetka | Složenost |
|---|---|---|---|
| **0** | **Stabilizacija isporuke** — novi kod na serveru, `migrate`, restart workera, `sync_celery_periodic_tasks`; nedelju dana noćnih izveštaja. **Migracija `fleet.0086_bez_kadrovskih_oj` briše kolonu `allowed_hr_unit_codes`** — pokreće se tek zajedno sa novim kodom (stari kod tu kolonu čita pri svakom učitavanju korisnika); na živoj bazi namerno još nije primenjena | 7 uzastopnih noći: svi uporedni izveštaji prolaze, nijedan zapis Finansija i Potraživanja bez veze | Niska |
| **1** ✅ | **Putanja čvora** (3.1) — izvedeno 25.09.2026. | Centar na datum iz baze jednak `node_center_map` za sve zapise; test promene centra šifre | Niska |
| **2** ✅ | **Model prava sa obuhvatom i jedna provera** (3.2, tačke 1–2) — izgrađeno, nije uključeno | Testovi: obuhvat posla ne daje centar, istek dodele gasi pravo, prazan obuhvat ima jedno značenje | Srednja |
| **3** ✅ | **Admin korisnika i uloga** (V2, korak 3) — izvedeno 25.09.2026.: **Organizacija → Dodele uloga** (spisak, kartica korisnika, odobravanje nacrta, ručna dodela, opoziv sa istorijom, senka) | Administrator održava pilot korisnike bez Django admina | Srednja |
| **4** ✅ | **Prevod i senka** (3.2, tačke 3–4) — Finansije, Potraživanja, putni nalozi, vozila i kontrolna tabla: 4 razlike, sve potvrđene (Garaža, Pregled); Kadrovi van senke (3.3) | Izveštaj razlika po korisniku i modulu je prazan ili potvrđen | Srednja |
| **5** | **Pilot: Potraživanja + Finansije** — filteri, zbirovi i prava zajedno | Isti iznosi za isti skup; tuđi podaci nedostupni; istorija i opoziv provereni | Srednja |
| **6** | **Flota** — ~30 mesta filtera i zbirova [P], sa pravilom dodele na datum | Nema promene brojeva dokumenata ni istorije zaduženja | Srednja |
| **7** | **Nabavka**, pa **HR** — zaposleni dobija vezu na čvor registra, bez posebne kadrovske organizacije (3.3) | Kontrolni izveštaj modula prolazi | Srednja |
| **8** | **Sistematizacija** (V2, korak 8) | Promena naziva, šifre ili roditelja bez gubitka istorije i bez neočekivanog pristupa | Visoka |
| **9** | **Gašenje stare organizacije** (3.4) | Uslovi iz 3.4 | Niska |

**Zašto pilot Potraživanja + Finansije, a ne Flota [Z]:** tamo prava najviše „bole” — oba modula
danas pojedinačnu OJ korisnika šire na ceo centar (V2, pogl. 1), pa je dobitak od prava po
obuhvatu najveći, a modeli su najjednostavniji (tekstualna šifra, bez dodele vozila na datum).

---

## 5. Odluke potrebne pre početka

| # | Pitanje | Predlog |
|---|---|---|
| 1 | Da li se uvodi tabela putanje (3.1) | Da — bez nje filteri na datum zahtevaju složene podupite u svakom modulu |
| 2 | Značenje praznog obuhvata | ✅ **Odlučeno 25.09.2026.: ne vidi ništa** — i u Floti, gde danas vidi sve. Uloga **Garaža** dobija obuhvat cele firme (odluka 25.09.2026.): radi sa celom Flotom svih centara, a putne naloge **samo gleda** — ne kreira, ne menja i ne briše (to već važi kroz dozvole uloge: ima samo `putninalog_list`, `_detail`, `_print`). Senka zato pokazuje `zoran` 0 → 3.740 putnih naloga — potvrđeno |
| 3 | Da li pojedinačna OJ korisnika ostaje ograničena na tu OJ | ✅ **Odlučeno 25.09.2026.: ne — ostaje kao danas**, OJ daje ceo svoj centar (tiče se `bilja`, koja ionako ima Upravu, i `suzana.injac` → centar 43) |
| 4 | Uloga „Uprava” | ✅ **Odlučeno 25.09.2026.:** obuhvat cele firme kroz dodelu, ne kao izuzetak u kodu (tako i radi: prevod joj pravi dodelu „cela firma”, provera nema izuzetak osim za superuser) |
| 5 | Kadrovske OJ 4331, 4332, 423, 4110 | ✅ **Bespredmetno** — posebne kadrovske organizacije nema (3.3, odluka 25.09.2026.) |
| 6 | Kadrovska oznaka `20` | ✅ **Bespredmetno** — posebne kadrovske organizacije nema (3.3) |
| 7 | Pilot | Potraživanja + Finansije |
| 8 | Neaktivne šifre | ✅ **Odlučeno 25.09.2026.: ne nude se nigde** — forme, filteri, povezivanje faktura, spisak šifara u Finansijama i šifre bez prometa. Već upisana vrednost i već dodeljeno pravo ostaju. **Šifra bez prometa u poslednjih 12 meseci je neaktivna** (primenjeno 25.09.2026.: 168 naučnih projekata koji nikad nisu knjiženi; noćna sinhronizacija 01:40 to od sada radi sama). Izveštaj Finansija **po šiframa posla** prikazuje samo aktivne šifre, a zbir ispod tabele računa se nad istim knjiženjima; izveštaj po centrima, kontima i mesecima ostaje ceo (za 2025. van pregleda po šiframa ostaje 47 knjiženja, rashod 1.071.763,60) |

**Otvoreno iz registra, ne blokira korak 0–4:** 11 naziva jedinica „proveriti” i naziv centra 2;
lični brojevi 657, 998, 999; projekti P36014/P36017 pod dva broja; šifre `vranj`, `vranjs`,
`960001`.

---

## 6. Provere pre puštanja svakog koraka

| Provera | Očekivano |
|---|---|
| Isti korisnik, isti period — stari i novi put | Isti iznosi do dinara |
| Korisnik sa pojedinačnom OJ | Vidi samo tu OJ, ne ceo centar (posle potvrđene senke) |
| Korisnik bez obuhvata | Ne vidi ništa (osim eksplicitne uloge cele firme) |
| Šifra promeni centar od datuma | Stari dokumenti ostaju u starom centru, novi idu u novi |
| Isključen prekidač modula | Modul radi kao pre, bez gubitka novih unosa |
| Broj putnog naloga i predmeta | Nepromenjen |

---

## 7. Šta se ne radi u ovom poslu

| Ne radi se | Zašto |
|---|---|
| Brisanje `OrganizationalUnit` i starih kolona | Istorija i brojevi postojećih dokumenata |
| Upis u izvorni poslovni sistem (`posao`, `nalog_z`) | AGENTS pravila 2 i 3 |
| Promena formula obračuna | AGENTS pravilo 5 |
| Prebacivanje nasleđene Naplate | Gasi se zasebnom odlukom (AGENTS pravilo 7) |
