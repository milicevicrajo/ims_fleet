# 10. Poznati problemi i ograničenja

> **Za koga je ovo poglavlje:** programeri, održavanje, uprava (poglavlje 10.1 i 10.5).
>
> Ovde se vodi **registar svega što je uočeno tokom dokumentovanja sistema**, sa
> opisom posledice i predlogom rešenja.
>
> **Dana 18.09.2026. ispravljena je prva grupa problema** — oni kod kojih je uzrok bio
> nedvosmislen i ispravka kratka. Označeni su statusom **Rešeno** i za svaki piše šta je
> tačno promenjeno. Svi ostali problemi i dalje **nisu dirani**.
>
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 10.1. Kako čitati registar

| Ozbiljnost | Značenje |
|---|---|
| **Visoka** | Daje pogrešan poslovni rezultat ili ugrožava bezbednost podataka. Rešiti prvo. |
| **Srednja** | Daje rezultat koji zbunjuje ili nije uporediv; radi se, ali pogrešno se tumači. |
| **Niska** | Smeta u radu ili održavanju, ne kvari rezultat. |

| Status | Značenje |
|---|---|
| **Za rešavanje** | Potvrđeno, čeka odluku i ispravku |
| **Za proveru** | Potrebna potvrda korisnika pre bilo kakve izmene |
| **Prihvaćeno** | Poznato ograničenje, svesno se ne menja |
| **Rešeno** | Ispravljeno; u opisu stoji šta je promenjeno i kada |

---

## 10.2. Zbirni pregled

| # | Oblast | Kratak opis | Ozbiljnost | Status |
|---|---|---|---|---|
| [P-01](#p-01--tajne-i-debug-u-repozitorijumu) | Konfiguracija | Lozinke baze, `SECRET_KEY` i `DEBUG=True` u repozitorijumu | **Visoka** | **Rešeno** 19.09. — *istorija* |
| [P-02](#p-02--prosečna-potrošnja-ne-proverava-stariju-granicu) | Flota / gorivo | Prosečna potrošnja može biti desetostruko premala | **Visoka** | **Rešeno** 19.09. |
| [P-03](#p-03--procena-kilometraže-koristi-očitavanja-izvan-perioda) | Flota / troškovi | Kilometraža se procenjuje iz očitavanja izvan perioda | **Visoka** | Za proveru |
| [P-04](#p-04--kvadratna-složenost-izbora-para-očitavanja) | Flota / troškovi | Spor obračun kod vozila sa mnogo očitavanja | Niska | **Rešeno** 19.09. |
| [P-05](#p-05--centar-se-uzima-iz-poslednje-dodele-a-ne-istorijske) | Flota / troškovi | Trošak ide na trenutni, a ne na tadašnji centar | **Srednja** | **Rešeno** 19.09. — *V-07* |
| [P-06](#p-06--cela-premija-polise-ulazi-u-svaki-period) | Flota / troškovi | Cela godišnja premija ulazi i u jednomesečni period | **Visoka** | **Rešeno** 19.09. |
| [P-07](#p-07--cela-godišnja-kamata-lizinga-ulazi-u-svaki-period) | Flota / troškovi | Cela godišnja kamata ulazi i u jednomesečni period | **Visoka** | **Rešeno** 19.09. |
| [P-08](#p-08--operativni-lizing-se-deli-drugačije-od-dugoročnog-najma) | Flota / troškovi | Ista kolona se tumači na dva načina | **Srednja** | Za proveru |
| [P-09](#p-09--vozila-sa-troškom-nula-ili-manjim-nestaju-iz-spiska) | Flota / troškovi | Vozilo bez troška se ne prikazuje, bez objašnjenja | **Srednja** | **Rešeno** 19.09. |
| [P-10](#p-10--napomena-o-maloj-kilometraži-poredi-period-sa-godinom) | Flota / troškovi | Upozorenje se pojavljuje i kada ne treba | Niska | **Rešeno** 18.09. |
| [P-11](#p-11--pragovi-troška-po-km-su-upisani-u-kod) | Flota / troškovi | Pragovi se ne mogu menjati bez izmene koda | **Srednja** | Za proveru |
| [P-12](#p-12--analiza-kroz-više-perioda-zahteva-najmanje-dva-perioda) | Flota / troškovi | Greška ako se prosledi jedan period | Niska | Za rešavanje |
| [P-13](#p-13--superuser-ne-može-da-otvori-statistiku-centra) | Flota / pristup | Superuser dobija 403 | **Srednja** | **Rešeno** 18.09. |
| [P-14](#p-14--statistika-centra--četiri-odvojena-nedostatka) | Flota / centri | Otpisana vozila, prosečna starost, dijakritici | **Srednja** | **Rešeno** A, B, C 18.09. |
| [P-15](#p-15--jedan-celery-radnik-poništava-razdvajanje-redova) | Infrastruktura | `-P solo` blokira lake poslove | **Srednja** | Za proveru |
| [P-16](#p-16--zaključavanje-poslova-popušta-kada-redis-nije-dostupan) | Infrastruktura | Dva ista posla mogu raditi istovremeno | **Srednja** | Za proveru |
| [P-17](#p-17--procedura-sp_azurirajnalogz-ne-briše-obrisane-redove) | Finansije | Lokalna kopija nije jednaka izvoru | **Srednja** | Prihvaćeno |
| [P-18](#p-18--naplata-i-potraživanja-rade-paralelno) | Naplata | Dva sistema nad istim poslom | **Srednja** | Za rešavanje |
| [P-19](#p-19--dva-mehanizma-za-ograničenje-po-centrima) | Pristup | Nije jasno koji je merodavan | **Srednja** | Za proveru |
| [P-20](#p-20--model-naplate-navodi-nepostojeći-pogled) | Naplata | `dodela_bucketa` naspram `dodela_baketa` | Niska | Prihvaćeno |
| [P-21](#p-21--radni-fajlovi-u-repozitorijumu) | Repozitorijum | Baza, dnevnici i privremeni fajlovi u projektu | Niska | **Rešeno** 18.09. |
| [P-22](#p-22--nekorišćene-zavisnosti) | Repozitorijum | `djangorestframework`, `psycopg2` | Niska | **Rešeno** 18.09. |
| [P-23](#p-23--lizing-se-prikazuje-samo-u-mesecu-početka-ugovora) | Flota / lizing | Mesečni izveštaj prikazuje ugovor samo jednom | **Visoka** | Za rešavanje |
| [P-24](#p-24--izveštaj-lizinga-koristi-poslednju-dodelu-vozila) | Flota / lizing | Nedosledno sa ostalim mesečnim izveštajima | **Srednja** | Za rešavanje |
| [P-25](#p-25--prateći-troškovi-lizinga-obuhvataju-sva-vozila-jedinice) | Flota / lizing | Troškovi koji ne pripadaju lizing vozilima | **Srednja** | Za rešavanje |
| [P-26](#p-26--izveštaj-goriva-za-upravu-nema-zaštitu-pri-čitanju) | Flota / izveštaji | Nema prečišćavanja OMV pri čitanju | **Srednja** | **Rešeno** 18.09. |
| [P-27](#p-27--formule-11-izveštaja-nisu-u-projektu) | Flota / izveštaji | Formule 11 izveštaja postoje samo u bazi | **Srednja** | Za rešavanje |
| [P-28](#p-28--dva-različita-obračuna-dnevnih-sati) | Kadrovi | Dva obračuna sati iz iste evidencije | **Visoka** | Za proveru |
| [P-29](#p-29--otvoreno-bolovanje-nestaje-sa-radne-liste) | Kadrovi | Otvoreno bolovanje se prikazuje do datuma izvoza | **Srednja** | Za rešavanje |
| [P-30](#p-30--izuzeće-od-parkinga-nema-period-važenja) | Mobilni | Izuzetak menja i prošle obračune | **Srednja** | Za rešavanje |
| [P-31](#p-31--obustava-se-nigde-ne-čuva) | Mobilni | Nema traga šta je prosleđeno u zarade | **Visoka** | Za rešavanje |
| [P-32](#p-32--rupe-u-razvrstavanju-bivših-zaposlenih) | Mobilni | Neki zaposleni nisu ni u jednom izveštaju | **Srednja** | Za rešavanje |
| [P-33](#p-33--virman-skraćuje-podatke-i-ne-čuva-poslatu-datoteku) | Isplate | Tiho skraćivanje i bez traga o poslatom | **Visoka** | Za rešavanje |
| [P-34](#p-34--poseban-broj-telefona-upisan-u-kod-umesto-u-bazi) | Mobilni | Poslovni izuzetak upisan u kod | **Visoka** | **Potvrđena greška** |
| [P-35](#p-35--nepoznato-dospeće-prikazuje-se-kao-nedospelo) | Potraživanja | Dug bez dospeća izgleda kao nedospeo | **Srednja** | Za proveru |
| [P-36](#p-36--ukupan-iznos-faktura-na-izveštaju-nabavke-je-višestruko-uvećan) | Nabavka | Zbir sabira fakturu više puta | **Visoka** | **Rešeno** 18.09. |
| [P-37](#p-37--brisanje-uf-faktura-tiho-kida-veze) | Nabavka | Veza sa predmetom nestaje bez traga | **Srednja** | Za rešavanje |
| [P-38](#p-38--procenjena-vrednost-predmeta-se-ne-poredi-sa-stavkama) | Nabavka | Dve nezavisne vrednosti, bez provere | Srednja | Za proveru |
| [P-39](#p-39--ispravka-u-izvoru-stvara-dvojnika-euf-fakture) | Nabavka | Ispravka u izvoru pravi novu fakturu | **Srednja** | Za proveru |
| [P-40](#p-40--apr-provera-zaobilazi-ssl-i-prepoznaje-samo-jedan-status) | Ugovori | Zaobilaženje SSL i uzak uslov statusa | **Srednja** | Za rešavanje |
| [P-41](#p-41--preuzimanje-menica-zavisi-od-izgleda-stranice-nbs-a) | Menice | Krhka integracija i PIB u kodu | **Srednja** | Za rešavanje |
| [P-42](#p-42--konta-i-pravila-toka-gotovine-upisani-su-u-kod) | Finansije | Kontni plan i pravila u kodu | **Srednja** | Za proveru |
| [P-43](#p-43--mogući-dvostruki-obuhvat-zajedničkih-troškova) | Finansije | Rizik dvostrukog obuhvata ZT | **Srednja** | Za proveru |
| [P-44](#p-44--promena-centra-pregrupiše-celu-istoriju-finansija) | Finansije | Prošli izveštaji se menjaju | **Srednja** | Za proveru |
| [P-45](#p-45--modul-menice-nema-migracije) | Menice | Tabele se ne mogu stvoriti migracijom | **Visoka** | Za rešavanje |
| [P-46](#p-46--ključ-za-duplikate-ne-podnosi-prazna-polja) | Flota / gorivo | Zapis bez vaučera ili količine nestaje sa ekrana | **Visoka** | **Rešeno** 18.09. |
| [P-47](#p-47--ključ-za-duplikate-ne-obuhvata-iznos-ni-valutu) | Flota / gorivo | Dva iznosa iste transakcije se spajaju u jedan | **Srednja** | **Za proveru** |
| [P-48](#p-48--lični-podaci-i-brojevi-računa-329-osoba-u-repozitorijumu) | Bezbednost | Imena, adrese i brojevi računa u git istoriji | **Visoka** | Delimično rešeno — **istorija ostaje** |
| [P-49](#p-49--procedura-osvežava-tekuću-godinu-a-ispravke-čitaju-prethodnu) | Potraživanja | Posle aprila ispravke čitaju godinu koja se ne osvežava | **Srednja** | **Za proveru** |

---

## 10.3. Bezbednost i konfiguracija

### P-01 — Tajne i DEBUG u repozitorijumu

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (19.09.2026.) — **tajne ostaju u istoriji** |
| **Gde** | `ims_erp/settings/base.py`, `development.py`, `production.py` |

**Šta je zatečeno [P]:**

| Stavka | Gde | Vrednost |
|---|---|---|
| `SECRET_KEY` | `base.py:70` | Upisan u kod |
| `DEBUG = True` | `base.py:73` | **Produkcija ga ne isključuje** |
| Korisnik i lozinka baze | `development.py:11-13`, `production.py:14-17` | Upisani u kod |
| Ime servera i baze | oba fajla | Upisani u kod |

**Posledice [Z]:**

1. Svako ko ima pristup repozitorijumu ima i pristupne podatke za bazu `IMS_ERP`.
2. Sa `DEBUG = True` Django pri grešci prikazuje **pun ispis stanja**, uključujući
   delove konfiguracije i vrednosti promenljivih.
3. Poznat `SECRET_KEY` omogućava falsifikovanje sesija i CSRF tokena.
4. Mediji se opslužuju preko Djanga, jer `MEDIA_URL` radi samo uz `DEBUG=True`
   — isključivanje `DEBUG`-a zahteva i podešavanje opsluživanja medija.

**Predlog rešenja [Z]:**

1. Preseliti sve tajne u promenljive okruženja (`python-dotenv` je već u zavisnostima).
2. Postaviti `DEBUG = False` u `production.py` i podesiti opsluživanje `media/`
   preko web servera.
3. Promeniti `SECRET_KEY` i lozinku baze **posle** preseljenja.
4. Ukloniti istoriju tajni iz repozitorijuma ili prihvatiti da su kompromitovane
   i rotirati ih.

> **Redosled je bitan [Z]:** isključivanje `DEBUG`-a bez rešavanja medija prekida
> prikaz slika vozila i dokumenata.


**Šta je urađeno (19.09.2026.) [P]:**

| Korak | Stanje |
|---|---|
| 1. Tajne u promenljive okruženja | **Urađeno.** `SECRET_KEY`, korisnik, lozinka, server i ime baze čitaju se iz `.env`, koji je u `.gitignore`. Uzor je `.env.example`. |
| 2. `DEBUG` iz okruženja | **Urađeno.** `DJANGO_DEBUG`; podrazumevano **`False`**, a `.env` za razvoj postavlja `True`. |
| 3. Nov `SECRET_KEY` | **Urađeno.** Generisan je nov ključ; stari više nigde ne stoji. |
| 4. Nova lozinka baze | **Nije urađeno** — menja se na serveru, pa se upiše u `.env`. |
| 5. Prepisivanje istorije | **Nije urađeno** |

Uvedene su i dve pomoćne funkcije u `ims_erp/settings/base.py` [P]:

| Funkcija | Šta radi |
|---|---|
| `env_required(name)` | Diže `ImproperlyConfigured` sa jasnom porukom ako promenljiva nedostaje — umesto tihog pada na podrazumevanu vrednost |
| `database_credentials()` | Jedno mesto za pristupne podatke, koje koriste i `development.py` i `production.py` |

> ⚠ **Dve stvari koje i dalje stoje:**
>
> 1. **Stari `SECRET_KEY` i lozinka `Rajo123` ostaju u git istoriji.** Dok se istorija ne
>    prepiše, treba ih smatrati kompromitovanim — **lozinku baze promeniti na serveru**.
> 2. **Promena `SECRET_KEY`-a poništava sve prijave.** Pri prvom restartu svi korisnici
>    se odjavljuju i moraju ponovo da se prijave. To je jednokratno.

> **[P] `DEBUG = False` i dalje prekida prikaz slika.** `ims_erp/urls.py` opslužuje `media/`
> samo kada je `DEBUG=True`. Pre prebacivanja produkcije na `False` treba podesiti
> opsluživanje `media/` preko web servera.

---

### P-48 — Lični podaci i brojevi računa 329 osoba u repozitorijumu

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Delimično rešeno 18.09.2026. — **podaci ostaju u istoriji** |
| **Gde** | `internal.txt.json`, `Virman-165-B5-2.TXT`, `Virman-165-B4-4 primer.TXT.20260520104653` |
| **Otkriveno** | 18.09.2026., pri čišćenju repozitorijuma |

**Šta je zatečeno [P]:** tri datoteke u korenu projekta sadrže **stvarne podatke o
isplatama fizičkim licima**, i sve tri su **u git istoriji**.

| Datoteka | Sadržaj | U istoriji od |
|---|---|---|
| `internal.txt.json` (437 KB) | **329 zapisa, 329 različitih imena i 329 različitih brojeva računa**, adrese, iznosi, ukupno 3.290.000,00, datum 29.04.2022. | `cfee1f6` |
| `Virman-165-B5-2.TXT` | 21 red — imena, brojevi računa, „Upl.zarade“ | `458498a` |
| `Virman-165-B4-4 primer.TXT.20260520104653` | 4 reda istog oblika | `458498a` |

Polja u `internal.txt.json` [P]: `CreditorName`, `CreditorAddress`, `CreditorBankAccount`,
`Amount`, `PaymentBasis` („Prihodi van radnog odnosa“), `DebtorBankAccount`.

**Posledica [Z]:** svako ko ima pristup repozitorijumu — ili bilo kojoj njegovoj kopiji —
ima **imena, adrese, brojeve tekućih računa i iznose isplata 329 osoba**. Ovo je ista
vrsta problema kao [P-01](#p-01--tajne-i-debug-u-repozitorijumu), ali se tiče **podataka o
ljudima**, a ne pristupa sistemu.

**Zašto se ne rešava prostim brisanjem [P]:** datoteke su **komitovane**. Brisanje iz
radnog direktorijuma ih uklanja iz zatečenog stanja, ali **ostaju u istoriji svakog klona**.
Stvarno uklanjanje traži prepisivanje istorije (`git filter-repo`) i usaglašavanje sa svima
koji imaju kopiju.

**Dodatna zapetljanost [P]:** `Virman-165-B5-2.TXT` **koristе dva testa** —
`isplate/tests.py:161` i `:410`. Ne može se samo obrisati; treba ga **zameniti izmišljenim
podacima** istog oblika (180 znakova, cp1250), pa tek onda ukloniti original.

**Predlog koraka [Z]:**

1. Potvrditi sa odgovornim licem za zaštitu podataka da su to stvarni podaci.
2. Napraviti sintetički uzorak za `isplate/tests.py` i prevezati testove na njega.
3. Ukloniti sve tri datoteke iz zatečenog stanja i dodati pravilo u `.gitignore`.
4. Odlučiti o prepisivanju istorije — zajedno sa [P-01](#p-01--tajne-i-debug-u-repozitorijumu),
   jer se i tajne uklanjaju istim postupkom.

**Šta je urađeno (18.09.2026.) [P]:**

| Korak | Stanje |
|---|---|
| 1. Potvrda da su podaci stvarni | **Nije urađeno** — traži potvrdu odgovornog lica |
| 2. Sintetički uzorak za testove | **Urađeno.** `isplate/test_data/virman-uzorak.TXT` — 19 stavki sa izmišljenim imenima i brojevima računa, isti oblik (180 znakova, cp1250). Oba testa prevezana i prolaze. |
| 3. Uklanjanje datoteka iz zatečenog stanja | **Urađeno.** Sve tri su obrisane. |
| 4. Prepisivanje istorije | **Nije urađeno** |

> ⚠ **Problem nije rešen.** Datoteke više nisu u radnom direktorijumu, ali su **i dalje u
> svakoj kopiji repozitorijuma**, u izmenama `cfee1f6` i `458498a`. Dok se istorija ne
> prepiše (`git filter-repo`), imena, adrese i brojevi računa 329 osoba ostaju dostupni
> svakome ko ima klon. To se radi **zajedno sa** [P-01](#p-01--tajne-i-debug-u-repozitorijumu),
> jer se tajne uklanjaju istim postupkom, i traži usaglašavanje sa svima koji imaju kopiju.

**Šta je time dobijeno [P]:** projektu **više nisu potrebni stvarni podaci** — testovi rade
nad izmišljenim uzorkom. Prepisivanje istorije zato više ništa ne lomi.

---

## 10.4. Obračuni — Flota

### P-02 — Prosečna potrošnja ne proverava stariju granicu

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/fuel.py:320-347`, funkcija `calculate_average_fuel_consumption()` |
| **Obračun** | [V-01](obracuni/06-02-flota-gorivo.md#v-01--prosečna-potrošnja-goriva-poslednjih-10-točenja) |
| **Pitanje** | Q13 |

**Šta je zatečeno [P]:** obračun bira prozor točenja `[k, 9−k]`, gde je `k` najnovije
točenje sa `mileage > 0`. **Novija granica se proverava, starija (`9−k`) ne.**

**Posledica [P]:** ako starije granično točenje ima kilometražu 0, pređeni put postaje
cela kilometraža vozila:

| | Stvarno | Prikazano |
|---|---|---|
| Pređeni put | ~1.500 km | 128.000 km |
| Potrošnja | ~6 l/100 km | **~0,07 l/100 km** |

Bez ijednog upozorenja na ekranu.

**Predlog rešenja [Z]:** primeniti isto pravilo kao u
`calculate_average_fuel_consumption_ever()`, koji **jeste** ispravan — obe granice tražiti
među točenjima sa `mileage > 0`.

**Pre ispravke proveriti [Z]:** koliko vozila trenutno prikazuje besmisleno nisku
potrošnju — to je i provera da li se problem stvarno javlja u radu.


**Šta je urađeno (19.09.2026.) [P]:** obe granice prozora se sada traže među točenjima sa
`mileage > 0`, po istom postupku kao u `calculate_average_fuel_consumption_ever()`:

```python
newest_index = next((i for i, entry in enumerate(last_10_consumptions) if entry.mileage > 0), None)
oldest_index = next((i for i in range(len(last_10_consumptions) - 1, -1, -1)
                     if last_10_consumptions[i].mileage > 0), None)
if newest_index is None or oldest_index is None or newest_index >= oldest_index:
    return None
```

Dodata su i **dva uslova zdravog razuma** [P]:

1. Novija granica mora biti **stvarno novija** od starije (`newest_index < oldest_index`).
2. **Kilometraža novije granice mora biti veća** od starije (`total_mileage > 0`).

Kada nijedan od uslova nije ispunjen, vraća se `None` — na ekranu **nema broja**, umesto
izmišljenog. To je bolje nego prikazati 0,07 l/100 km.

**Testovi [P]:** `fleet/test_cost_fixes.py: AverageFuelConsumptionTests` — tri slučaja:
nula na starijoj granici, kilometraža koja ne raste, i samo jedno točenje sa kilometražom.

---

### P-03 — Procena kilometraže koristi očitavanja izvan perioda

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za proveru |
| **Gde** | `fleet/support/dashboard.py:89-101`, `_estimate_period_mileage()` |
| **Obračun** | [V-08](obracuni/06-03-flota-troskovi.md#v-08--procena-pređene-kilometraže-u-periodu) |

**Šta je zatečeno [P]:** pri izboru para očitavanja prolaze se **sva** očitavanja vozila,
bez ograničenja na traženi period. Bira se par sa najmanjim zbirom udaljenosti od granica
perioda, ali **udaljenost nije ograničena**.

**Posledica [Z]:** za vozilo koje u periodu nema nijedno očitavanje, kilometraža se ipak
procenjuje — iz očitavanja starih mesecima ili godinama. Ta procena zatim postaje
imenilac troška po kilometru (V-07).

**Primer [Z]:** vozilo sa očitavanjima samo iz 2024. dobiće procenu i za mart 2026,
kao da se vozilo i dalje kreće istim tempom.

**Predlog rešenja [Z]:** uvesti gornju granicu udaljenosti očitavanja od perioda
(npr. 90 dana), a izvan nje vratiti „Nema podatka“ umesto procene.

> **Pre izmene potrebna potvrda [N]:** moguće je da je ovakvo ponašanje namerno, da bi
> se izbeglo da vozila bez skorašnjih očitavanja nestanu iz analitike. Vidi **P-09**.


**Zašto je ovo problem — dopuna (19.09.2026.) [Z]:**

Izbor para očitavanja gleda **sva** očitavanja vozila i bira ono koje je **najbliže**
granicama perioda. Reč „najbliže“ tu nema gornju granicu — ako je najbliže očitavanje
staro dve godine, ono se svejedno uzima.

| Šta korisnik vidi | Šta se zapravo dogodilo |
|---|---|
| Kolona „Kilometraža“ pokazuje npr. **2.480 km** za mart 2026. | Vozilo u martu 2026. **nema nijedno očitavanje**. Uzet je dnevni prosek iz 2024. i pomnožen brojem dana u martu. |
| Kolona „RSD/km“ pokazuje npr. **41,20** | Imenilac je taj izmišljeni broj, pa je i cena po km izmišljena. |
| Kolona „Izvor“ pokazuje „Točenja (okvirno)“ | To je jedini nagoveštaj, i lako se previdi. |

**Suština [Z]:** broj ne izgleda kao procena. Stoji u istoj koloni, istim formatom, pored
vozila koja **imaju** stvarna očitavanja. Rukovodilac ih poredi kao da su ista vrsta
podatka — a jedan je izmeren, drugi izveden iz podataka od pre dve godine.

> **Zašto možda i nije greška [N]:** bez te procene vozila bez skorašnjih očitavanja
> dobila bi „Nema podatka“. Ranije su takva vozila, ako uz to nisu imala ni trošak,
> **potpuno nestajala** sa spiska — vidi [P-09](#p-09--vozila-sa-troškom-nula-ili-manjim-nestaju-iz-spiska),
> koji je rešen 19.09.2026.. Sada vozilo ostaje na spisku i kada nema podataka, pa „Nema podatka“
> više ne znači da vozilo nestaje.

**Šta treba odlučiti [N]:** dokle unazad očitavanje sme da posluži kao osnova procene.
Predlog je **90 dana** od granice perioda; izvan toga prikazati „Nema podatka“. Tačan broj
dana je poslovna odluka.

---

### P-04 — Kvadratna složenost izbora para očitavanja

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:91-101` |

**Šta je zatečeno [P]:** dvostruka petlja „svako sa svakim“ preko svih očitavanja vozila.
Vozilo sa 1.000 očitavanja daje milion poređenja, i to **za svako vozilo** pri svakom
otvaranju analitike flote.

**Posledica [Z]:** sporo otvaranje ekrana analitike, rastuće sa starošću sistema.

**Predlog rešenja [Z]:** pošto su očitavanja sortirana po datumu, dovoljno je posmatrati
samo očitavanja najbliža granicama perioda — složenost pada na linearnu.


**Šta je urađeno (19.09.2026.) [P]:** dvostruka petlja zamenjena je funkcijom
`_best_reading_pair()`, koja očitavanja obilazi **jednom**, po datumu.

| | Ranije | Sada |
|---|---|---|
| Složenost | `O(n²)` | **`O(n log n)`** |
| Vozilo sa 1.000 očitavanja | ~1.000.000 poređenja | ~10.000 koraka |

Najbolji kandidat za početak para pamti se u **Fenwick stablu** po rangu kilometraže, pa
upit „najbolji početak sa manjom kilometražom“ traje logaritamski.

> **[P] Rezultat je isti, uključujući i izbor pri izjednačenju.** Kada više parova ima isti
> zbir udaljenosti, bira se isti par koji bi našla i ranija petlja — najmanji indeks
> početka, pa najmanji indeks kraja.

**Test [P]:** `fleet/test_cost_fixes.py: BestReadingPairTests` poredi novi postupak sa
**doslovnom starom dvostrukom petljom** na 40 nasumičnih skupova očitavanja, uključujući i
padove kilometraže. Rezultati se poklapaju u svim slučajevima.

---

### P-05 — Centar se uzima iz poslednje dodele, a ne istorijske

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** za V-07 (19.09.2026.); **V-24 nema period** |
| **Gde** | `fleet/support/dashboard.py:143-145`, `fleet/views/center_statistics.py:65-67` |
| **Obračun** | [V-07](obracuni/06-03-flota-troskovi.md#v-07--trošak-po-kilometru-po-vozilu), [V-24](obracuni/06-03-flota-troskovi.md#v-24--statistika-po-centrima) |

**Šta je zatečeno [P]:** trošak po kilometru i statistika centra koriste **poslednju**
dodelu vozila (`-assigned_date`, bez datumskog ograničenja).

**Nedoslednost [P]:** izveštaj goriva po šifri posla (V-21) i mesečni troškovi servisa
koriste **istorijsku** dodelu — onu koja je važila **na dan troška**.

**Posledica [Z]:** vozilo prebačeno iz centra 43 u centar 12 nosi **ceo istorijski trošak**
u centar 12, iako je trošak nastao u centru 43. Zbirovi po centrima iz dva različita
ekrana se ne slažu.

**Predlog rešenja [Z]:** uskladiti sa V-21 — koristiti dodelu koja je važila na datum
troška. To zahteva razlaganje troška po intervalima dodele unutar perioda.

> **Potrebna odluka [N]:** moguće je da je za analitiku flote namerno izabrana
> trenutna pripadnost, jer rukovodilac gleda „svoja“ vozila. Tada ostaje da se ta
> razlika **jasno napiše na ekranu**.


**Šta je urađeno (19.09.2026.) [P]:** trošak po kilometru (V-07) više ne koristi **trenutnu**
dodelu, nego onu koja je **važila na kraju izabranog perioda**:

```python
center_at_period_end = JobCode.objects.filter(
    vehicle=OuterRef('pk'),
    assigned_date__lte=period_end_date,
).order_by('-assigned_date', '-pk').values('organizational_unit__center')[:1]
```

**Šta to rešava [P]:** izveštaj za prošli period **više se ne menja** kada se vozilo kasnije
prebaci u drugi centar. Ranije je svaka promena centra retroaktivno menjala i već
pogledane izveštaje.

Dodata je i oznaka `center_changed_in_period` [P] — tačna kada je vozilo **unutar perioda**
dobilo novu dodelu. Time se vidi kod kojih redova pripadnost nije bila ista celog perioda.

> **[P] Šta i dalje nije rešeno:** vozilo koje je centar promenilo **usred** perioda i dalje
> nosi **ceo** trošak perioda u centar u kojem je bilo na kraju. Potpuna ispravka traži
> razlaganje svakog troška po intervalima dodele, što menja i strukturu reda (jedan red po
> vozilu i centru). Oznaka `center_changed_in_period` bar pokazuje gde se to dešava.

> **[P] Statistika centra (V-24) nije menjana** — ona nema izabrani period, prikazuje iznose
> **za ceo vek vozila**. Tamo je „poslednja dodela“ jedini mogući izbor. Vidi
> [P-14 D](#p-14--statistika-centra--četiri-odvojena-nedostatka).

---

### P-06 — Cela premija polise ulazi u svaki period

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:214-223` |
| **Obračun** | [V-07](obracuni/06-03-flota-troskovi.md#v-07--trošak-po-kilometru-po-vozilu) |

**Šta je zatečeno [P]:** polisa ulazi u trošak ako se **bilo kako** preklapa sa periodom:

```
start_date <= kraj perioda  I  end_date >= početak perioda
```

Uzima se **ceo iznos premije**, bez deljenja po danima.

**Posledica [P]:** godišnja premija od 60.000 RSD ulazi u punom iznosu i u
jednomesečni period, gde bi srazmerno bilo oko 5.000 RSD. Trošak po kilometru je
**višestruko uvećan** za kratke periode.

Za godišnju premiju od 60.000 RSD (polisa važi 365 dana):

| Period | Dana | Srazmerno | Sistem računa | Odstupanje |
|---|---|---|---|---|
| Godina dana | 365 | 60.000,00 | 60.000,00 | 0 |
| Tri meseca (01.01.–31.03.) | 89 | 14.630,14 | **60.000,00** | **+310%** |
| Mesec dana (mart) | 30 | 4.931,51 | **60.000,00** | **+1.117%** |

**Predlog rešenja [Z]:** primeniti isti postupak kao kod dugoročnog najma —
deliti premiju po danima preklapanja sa važenjem polise:

> deo premije = premija × (dana preklapanja) / (dana važenja polise)


**Šta je urađeno (19.09.2026.) [P]:** premija se deli srazmerno danima preklapanja:

```python
policy_days = (policy['end_date'] - policy['start_date']).days + 1
days = days_of_overlap(policy['start_date'], policy['end_date'],
                       period_start_date, period_end_date)
policy_cost_by_vehicle[policy['vehicle_id']] += (
    float(policy['premium_amount'] or 0) * days / policy_days
)
```

Obračun je premešten iz SQL podupita u Python, jer deljenje po danima traži datume svake
polise posebno. Polise bez datuma početka ili kraja se **ne uzimaju** — ranije su ulazile u
punom iznosu. [P]

**Provera na primeru iz opisa [P]** — godišnja premija 60.000 RSD:

| Period | Dana | Ranije | Sada |
|---|---|---|---|
| Godina dana | 365 | 60.000,00 | **60.000,00** |
| Mart (31 dan) | 31 | 60.000,00 | **5.095,89** |

> **Posledica za korisnika [Z]:** trošak po kilometru za kratke periode **biće znatno
> manji nego ranije**. Raniji je bio uvećan i do jedanaest puta.

**Testovi [P]:** `fleet/test_cost_fixes.py` — jedan za jednomesečni period, jedan za celu
godinu (gde ceo iznos i dalje ulazi).

---

### P-07 — Cela godišnja kamata lizinga ulazi u svaki period

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:224-234` |
| **Obračun** | [V-07](obracuni/06-03-flota-troskovi.md#v-07--trošak-po-kilometru-po-vozilu) |

**Šta je zatečeno [P]:** kamata finansijskog lizinga se uzima za **sve godine koje period
dodiruje** (`year in range(početna godina, krajnja godina + 1)`), u **punom godišnjem
iznosu**.

**Posledica [Z]:** period od 01.12.2025. do 31.01.2026. povlači **dve pune godišnje
kamate** (2025. i 2026.) za dva meseca troška.

**Predlog rešenja [Z]:** deliti godišnju kamatu po danima preklapanja perioda sa tom
kalendarskom godinom.


**Šta je urađeno (19.09.2026.) [P]:** godišnja kamata se deli srazmerno danima preklapanja
perioda sa **tom kalendarskom godinom**:

```python
days = days_of_overlap(date(year, 1, 1), date(year, 12, 31),
                       period_start_date, period_end_date)
days_in_year = 366 if calendar.isleap(year) else 365
financial_interest_by_vehicle[interest['lease__vehicle_id']] += (
    float(interest['interest_amount'] or 0) * days / days_in_year
)
```

**Prestupna godina se poštuje** — imenilac je 366 dana kada treba. [P]

**Provera na primeru iz opisa [P]** — kamata 36.500 RSD za 2025. i isto toliko za 2026.,
period 01.12.2025.–31.01.2026.:

| | Ranije | Sada |
|---|---|---|
| Ulazi u trošak | 73.000,00 (dve pune godine) | **6.200,00** (31 + 31 dan) |

**Test [P]:** `fleet/test_cost_fixes.py: test_financial_lease_interest_is_split_per_calendar_year`.

---

### P-08 — Operativni lizing se deli drugačije od dugoročnog najma

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `fleet/support/dashboard.py:274-285` |

**Šta je zatečeno [P]:** ista kolona `current_payment_amount` („Trenutna rata / iznos
otplate“) tumači se na dva načina:

| Vrsta | Tumačenje | Formula |
|---|---|---|
| Dugoročni najam | **Mesečna rata** | Deli se po danima svakog meseca |
| Operativni lizing | **Ukupan iznos** | rata × dana preklapanja / ukupno dana ugovora |

**Posledica [Z]:** za operativni lizing sa mesečnom ratom od 50.000 RSD i ugovorom od
tri godine, u mesec dana ulazi samo ~1.370 RSD umesto ~50.000 RSD. Trošak operativnog
lizinga je **drastično potcenjen**.

**Predlog rešenja [Z]:** potvrditi šta kolona stvarno sadrži za operativni lizing,
pa primeniti isto pravilo kao kod dugoročnog najma ako je reč o mesečnoj rati.

> **Potrebna potvrda [N]:** verovatno je reč o grešci, ali je moguće da se kod
> operativnog lizinga u ovu kolonu unosi ukupan iznos ugovora. To se mora proveriti
> u podacima pre bilo kakve izmene.


**Kako ovo rešiti — predlog (19.09.2026.) [Z]:**

Problem nije u kodu nego u **značenju kolone**. Ista kolona `current_payment_amount` ne može
istovremeno biti mesečna rata i ukupan iznos ugovora. Zato ispravka **ne sme** početi od
koda.

**Korak 1 — utvrditi šta kolona sadrži.** Upit koji to pokazuje bez ikakve izmene podataka:

```sql
SELECT lease_type,
       COUNT(*)                                   AS ugovora,
       AVG(current_payment_amount)                AS prosecan_iznos,
       AVG(DATEDIFF(month, start_date, end_date)) AS prosecno_meseci,
       AVG(current_payment_amount /
           NULLIF(DATEDIFF(month, start_date, end_date), 0)) AS iznos_po_mesecu
FROM fleet_lease
WHERE lease_type <> 'finansijski'
GROUP BY lease_type;
```

**Kako pročitati rezultat [Z]:**

| Nalaz | Zaključak |
|---|---|
| `prosecan_iznos` operativnog lizinga je **istog reda veličine** kao kod dugoročnog najma | Kolona je **mesečna rata** → greška u kodu, primeniti isto pravilo kao za najam |
| `prosecan_iznos` je **desetinama puta veći** (npr. 1.800.000 naspram 50.000) | Kolona je **ukupan iznos ugovora** → kod je ispravan, ali naziv kolone obmanjuje |
| Nalazi se **mešaju** unutar iste vrste | Podaci su neujednačeni — treba ih **razdvojiti pre** bilo kakve izmene koda |

**Korak 2 — po nalazu:**

- Ako je mesečna rata: izbaciti poseban slučaj i pustiti operativni lizing kroz
  `monthly_cost_for_overlap()`, isto kao dugoročni najam. Izmena je **tri reda**.
- Ako je ukupan iznos: kod ostaje, ali se **preimenuje polje na ekranu** u
  „Ukupan iznos ugovora“ za operativni lizing, i doda napomena u ovo poglavlje.
- Ako je mešano: prvo razdvojiti u dve kolone ili uvesti oznaku šta iznos znači.

> **Zašto ne odmah ispraviti [Z]:** ako je kolona ukupan iznos, „ispravka“ bi trošak
> operativnog lizinga uvećala **36 puta** za trogodišnji ugovor. Pogrešna pretpostavka
> ovde je skuplja od čekanja na proveru.

**Q45:** kakav je stvarni sadržaj kolone „Trenutna rata / iznos otplate“ za operativni
lizing — mesečna rata ili ukupan iznos ugovora?

---

### P-09 — Vozila sa troškom nula ili manjim nestaju iz spiska

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:323-324` |

**Šta je zatečeno [P]:**

```python
if total_cost <= 0:
    continue
```

**Posledica [Z]:** vozilo bez ijednog evidentiranog troška u periodu, ili vozilo kod
koga je naknada osiguranja veća od troškova, **potpuno nestaje** iz analitike flote.
Korisnik ne dobija nikakvo objašnjenje i može zaključiti da vozilo ne postoji.

**Predlog rešenja [Z]:** prikazati vozilo sa oznakom „Nema evidentiranog troška u
periodu“ umesto izostavljanja, ili barem prikazati broj izostavljenih vozila.


**Šta je urađeno (19.09.2026.) [P]:** vozilo ostaje na spisku, sa jasnom oznakom zašto nema
cenu po kilometru:

```python
has_cost = total_cost > 0
cost_per_km = total_cost / annual_km if has_cost and annual_km > 0 else None
no_cost_note = None
if not has_cost:
    no_cost_note = ("Nema evidentiranog troška u periodu" if total_cost == 0
                    else "Naknade osiguranja su veće od evidentiranih troškova u periodu")
```

Razlikuju se **dva različita slučaja** koja su ranije oba završavala tako što vozilo
nestane [P]:

| Slučaj | Poruka |
|---|---|
| `total_cost == 0` | „Nema evidentiranog troška u periodu“ |
| `total_cost < 0` | „Naknade osiguranja su veće od evidentiranih troškova u periodu“ |

Na ekranu se u koloni RSD/km prikazuje **crtica** sa objašnjenjem u opisu, umesto praznog
polja. [P]

> **[P] Takvo vozilo ne kvari ostale pokazatelje:** `cost_per_km` je `None`, pa vozilo
> **ne ulazi** u proseke i pragove po klasi mase, niti može biti proglašeno „Neisplativim“
> u analizi kroz više perioda.

**Testovi [P]:** `fleet/test_cost_fixes.py` — vozilo bez ijednog troška i vozilo kod koga
je naknada osiguranja veća od troškova.

---

### P-10 — Napomena o maloj kilometraži poredi period sa godinom

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:328-339` |

**Šta je zatečeno [P]:** prag od 15.000 km poredi se sa **procenjenom kilometražom
perioda**, a poruka govori o **godišnjoj** kilometraži:

> *„Vozilo se malo vozi (… km < 15000 km godišnje).“*

**Posledica [Z]:** za jednomesečni period gotovo **svako** vozilo dobija to upozorenje,
pa ono gubi smisao.

**Predlog rešenja [Z]:** preračunati kilometražu na godišnji nivo pre poređenja
(`km × 365 / dana perioda`), ili prag skalirati dužinom perioda.


**Šta je urađeno (18.09.2026.) [P]:** u `fleet/support/dashboard.py` kilometraža se pre
poređenja svodi na godišnji nivo, a poruka prikazuje **tu preračunatu vrednost**:

```python
annualized_km = annual_km / period_days * 365 if annual_km > 0 else 0
below_mileage_threshold = 0 < annualized_km < low_mileage_threshold
```

Preračunata vrednost je dodata i u red tabele kao `annualized_km`, da bi bila dostupna
ekranima. Prag od 15.000 km nije menjan — i dalje je upisan u kod, videti
[P-11](#p-11--pragovi-troška-po-km-su-upisani-u-kod).

---

### P-11 — Pragovi troška po km su upisani u kod

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `fleet/support/analytics.py:14-19` |
| **Pitanje** | Q18 |

**Šta je zatečeno [P]:** četiri klase mase i po tri praga upisani su u konstantu
`_WEIGHT_CLASS_THRESHOLDS`. Nema ih u bazi i ne mogu se menjati kroz interfejs.

**Posledice [Z]:**

1. Promena pragova zahteva izmenu koda i isporuku nove verzije.
2. Nigde nije zabeleženo **odakle pragovi potiču** ni kada su poslednji put provereni.
3. Vozilo **bez unete maksimalne dozvoljene mase nema prag** i ostaje bez ocene,
   bez upozorenja da nedostaje podatak.

**Predlog rešenja [Z]:** preseliti pragove u šifarnik u bazi sa ekranom za održavanje,
i dodati upozorenje za vozila bez unete mase.

---

### P-12 — Analiza kroz više perioda zahteva najmanje dva perioda

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | Za rešavanje |
| **Gde** | `fleet/support/dashboard.py:401-403` |

**Šta je zatečeno [P]:** funkcija bez provere koristi `periods[1]`. Poziv sa jednim
periodom prekida se greškom.

**Predlog rešenja [Z]:** proveriti broj perioda i vratiti prazan spisak trajno
neisplativih vozila ako ih je manje od dva.

---

### P-13 — Superuser ne može da otvori statistiku centra

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `fleet/views/center_statistics.py:58-59` |

**Šta je zatečeno [P]:**

```python
if not request.user.allowed_centers.filter(center=center_code).exists():
    return HttpResponseForbidden("Nemate pristup ovim podacima.")
```

Provera **ne izuzima `is_superuser`**, za razliku od svih ostalih provera u sistemu
(`core/mixins.py`).

**Posledica [P]:** administrator sistema koji nema izričito upisane dozvoljene centre
dobija **403 Zabranjeno** na ekranu statistike centra.

**Predlog rešenja [Z]:** dodati izuzeće za `is_superuser`, kao u
`RolePermissionRequiredMixin`.


**Šta je urađeno (18.09.2026.) [P]:** provera je usklađena sa
`RolePermissionRequiredMixin`:

```python
if not request.user.is_superuser and not request.user.allowed_centers.filter(center=center_code).exists():
    return HttpResponseForbidden("Nemate pristup ovim podacima.")
```

---

### P-14 — Statistika centra — četiri odvojena nedostatka

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** A, B i C (18.09.2026.); **D ostaje za odluku** |
| **Gde** | `fleet/views/center_statistics.py` |

**A) Otpisana vozila ulaze u statistiku [P]** (linija 61)

Za razliku od analitike flote i preseka stanja, ovde **nema filtera `otpis=False`**.
Otpisano vozilo i dalje uvećava broj vozila, vrednost i troškove centra.

**B) Prosečna starost računa i vozila bez godine proizvodnje [P]** (linije 75-79)

```python
sum((vehicle.year_of_manufacture or 0) for vehicle in center_vehicles) / center_vehicle_count
```

Vozilo bez unete godine ulazi kao **0**, pa prosečna godina pada, a „prosečna starost“
(tekuća godina − prosek) postaje **besmisleno velika**.

> Primer: dva vozila, jedno iz 2020, jedno bez godine → prosek = 1010 →
> prikazana prosečna starost **1.016 godina**.

Presek stanja flote (`fleet_snapshot`) isti problem **rešava ispravno** — tamo se
računaju samo vozila sa godinom između 1886. i tekuće. [P]

**C) Kategorije popravki se traže bez dijakritika [P]** (linije 132-135)

Mesečni pregled traži nazive `gume`, `redovan servis`, `tehnicki pregled`, `registracija`.
Kategorija nazvana **„Tehnički pregled“** (sa „č“) **neće biti prepoznata** i njen iznos
neće se pojaviti ni u jednoj koloni.

**D) Iznosi su za ceo vek vozila, bez izbora perioda [P]**

Svi zbirovi (servisi, trebovanja, gorivo, naknade) idu **bez filtera datuma**.
Na ekranu to nije naznačeno, pa korisnik lako pomisli da gleda tekuću godinu.

**Predlog rešenja [Z]:**

1. Dodati `otpis=False`.
2. Preuzeti način računanja starosti iz `fleet_snapshot`.
3. Kategorije prepoznavati preko `ServiceType` šifre umesto po nazivu, ili normalizovati
   dijakritike kao u `fleet/support/vehicle_maintenance.py: service_category()`,
   koji to **već radi ispravno**.
4. Dodati izbor perioda ili jasno napisati „za ceo vek vozila“.


**Šta je urađeno (18.09.2026.) [P]:**

| | Ispravka |
|---|---|
| **A** | Dodat `otpis=False` u izbor vozila centra. |
| **B** | Prosečna starost se računa **samo iz vozila sa godinom između 1886. i tekuće**, kao u `fleet_snapshot`. Kad nijedno vozilo nema godinu, prikazuje se `—` umesto broja. Ekran uz to prikazuje i **koliko vozila ima poznato godište** (`poznato godište X/Y`), da prosek ne bi obmanuo kad je poznat za mali deo voznog parka. |
| **C** | Kategorije se više ne traže po nazivu. Nazivi iz `ServiceType` se **normalizuju** (mala slova, uklonjeni dijakritici) i po tome se dobija spisak šifara, pa se filtrira po šifri. „Tehnički pregled“ i „Tehnicki pregled“ od sada ulaze u isti zbir. |
| **C — dopuna** | Pri ispravci je utvrđeno da se iznos za **tehnički pregled uopšte nije prikazivao**: računao se, upisivao u podatke ekrana, ali nije bio ni u zbirovima (`numeric_fields`) ni u tabeli u šablonu. Bez toga bi ispravka prepoznavanja ostala nevidljiva, pa je **dodata kolona „Trošak Tehnički Pregled (Din)“** u mesečni pregled, sa zbirom i mesečnim prosekom. |

> **Očekivana promena na ekranu [Z]:** u mesečnom pregledu se pojavljuje **nova kolona**
> za tehnički pregled, a ukupni iznosi centra mogu **pasti** jer su otpisana vozila izašla
> iz obračuna. Oba pomaka su ispravka, ne greška.

**D nije menjano.** Iznosi su i dalje za ceo vek vozila i to na ekranu nije naznačeno —
za to je potrebna odluka da li dodati izbor perioda ili samo napisati napomenu.

---

### P-23 — Lizing se prikazuje samo u mesecu početka ugovora

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za rešavanje |
| **Gde** | `fleet/support/lease_queries.py:13-14` |
| **Obračun** | [V-19](obracuni/06-04-flota-ugovori-polise.md#v-19--mesečni-troškovi-lizinga) |

**Šta je zatečeno [P]:** izveštaj grupiše ugovore po `TruncYear`/`TruncMonth` nad
poljem **`start_date`** — datumom početka ugovora.

**Posledica [P]:** ugovor koji traje tri godine pojavljuje se u izveštaju **jednom**,
u mesecu u kome je potpisan. Za bilo koji kasniji mesec izveštaj **ne prikazuje** njegovu
ratu, iako ona i dalje tereti troškove.

> Izveštaj se zove „Mesečni troškovi lizinga“, ali **ne prikazuje mesečni trošak** —
> prikazuje **kada su ugovori počeli**.

**Predlog rešenja [Z]:** razložiti svaki ugovor na mesece njegovog trajanja, kao što
to već radi trošak po kilometru (`monthly_cost_for_overlap()` u
`fleet/support/dashboard.py:239`), pa grupisati po tim mesecima.

> **Napomena [Z]:** ispravan postupak **već postoji u kodu**, u drugom modulu —
> može se preuzeti bez izmišljanja novog pravila.

---

### P-24 — Izveštaj lizinga koristi poslednju dodelu vozila

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `fleet/support/lease_queries.py:8-10` |

**Šta je zatečeno [P]:** centar i organizaciona jedinica uzimaju se iz **poslednje**
dodele vozila, bez datumskog ograničenja.

**Nedoslednost [P]:** ostala dva mesečna izveštaja u istom modulu koriste **istorijsku**
dodelu:

| Izveštaj | Dodela |
|---|---|
| V-17 Mesečni troškovi polisa | Istorijska, na datum izdavanja polise |
| V-20 Mesečni troškovi servisa | Istorijska, na datum servisa |
| **V-19 Mesečni troškovi lizinga** | **Poslednja** |

**Posledica [Z]:** zbirovi po centrima iz tri izveštaja istog modula ne mogu se
međusobno sabrati niti uporediti.

**Predlog rešenja [Z]:** uskladiti sa V-17 i V-20 — koristiti dodelu važeću na datum
koji izveštaj prikazuje.

---

### P-25 — Prateći troškovi lizinga obuhvataju sva vozila jedinice

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `fleet/support/lease_queries.py:49-75` |

**Šta je zatečeno [P]:** kolone „prateći troškovi“ i „prateći troškovi po vozilu“
računaju se iz servisa i goriva **svih vozila čija je poslednja dodela ta organizaciona
jedinica** — a ne vozila obuhvaćenih lizing ugovorima iz tog reda.

**Posledica [Z]:** u redu koji prikazuje jedan lizing ugovor stoje troškovi desetak
vozila koja sa tim ugovorom nemaju veze. Korisnik prirodno zaključuje da su to troškovi
lizing vozila.

**Predlog rešenja [Z]:** ili ograničiti prateće troškove na vozila iz ugovora u tom redu,
ili preimenovati kolone tako da jasno kažu da se odnose na celu organizacionu jedinicu.

**Dodatno [P]:** za svaku grupu izvršavaju se tri odvojena upita u petlji — spisak vozila,
zbir servisa i zbir goriva. Kod većeg broja grupa ekran postaje spor.

---

### P-26 — Izveštaj goriva za upravu nema zaštitu pri čitanju

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `fleet/support/management_reports.py:102-106` |
| **Obračun** | [V-22.2](obracuni/06-05-flota-izvestaji.md#v-222--gorivo-ims-nis-i-omv) |

**Šta je zatečeno [P]:** izveštaj „Gorivo IMS — NIS i OMV“ čita `TransactionOMV`
**direktno**, bez `filter_omv_fuel_queryset()`:

```python
qs = model.objects.filter(**{date_field+'__gte': start, date_field+'__lt': end})
```

Svi ostali ekrani goriva (V-01, V-02, V-21, V-23, „Fakture goriva“, detalj vozila)
prolaze kroz prečišćavanje iz [V-06](obracuni/06-02-flota-gorivo.md#v-06--prečišćavanje-omv-transakcija).

**Zašto u praksi obično ne smeta [P]:** `cleanup_omv_fuel_data(apply=True)` pokreće se
**automatski pri svakom uvozu OMV podataka** (`fleet/sync/selenium.py:212`), pa se
duplikati i „odjeci“ računa **fizički brišu iz baze**.

**Kada smeta [Z]:**

1. Ako uvoz prekine grešku pre koraka čišćenja.
2. Ako se podaci unesu zaobilazeći redovni uvoz.
3. Ako se `import_omv_csv_data` pozove sa `cleanup=False`.

U tim slučajevima **izveštaj za upravu prikazuje uvećane iznose**, dok ostali ekrani
goriva ostaju tačni — što je najgori mogući oblik greške, jer se ne primeti poređenjem
sa drugim ekranima.

**Predlog rešenja [Z]:** primeniti `filter_omv_fuel_queryset()` i u ovom izveštaju.

**Šta je urađeno (18.09.2026.) [P]:** prečišćavanje je primenjeno, ali **ne celo**.
`filter_omv_fuel_queryset()` radi **dve odvojene stvari**:

1. izbacuje duplikate (zastareli datumi fakture, ponovljeni redovi, odjeci računa);
2. **ograničava skup samo na goriva** (`FUEL_PRODUCT_KEYWORDS`).

Izveštaj za upravu ima **sopstvenu podelu proizvoda** (`fuel_type`: gorivo, AdBlue,
ostalo, sve). Da je primenjen ceo filter, opcije „AdBlue“, „ostalo“ i „sve“ **prestale bi
da prikazuju bilo šta**. Zato je prvi deo izdvojen u novu funkciju:

```python
def deduplicate_omv_transactions(queryset):
    return _exclude_omv_receipt_echoes(
        _dedupe_omv_transaction_lines(_exclude_omv_stale_invoice_dates(queryset))
    )


def filter_omv_fuel_queryset(queryset):
    return deduplicate_omv_transactions(queryset.filter(_fuel_product_filter("product_inv")))
```

Izveštaj za upravu poziva `deduplicate_omv_transactions()` samo za OMV
(`fleet/support/management_reports.py`). Ponašanje `filter_omv_fuel_queryset()`
i svih ekrana koji ga koriste **ostalo je nepromenjeno** — redosled koraka je isti.

> **Ispravka ranije tvrdnje:** gore je pisalo da „dvostruka zaštita ne smeta, jer filter
> nad već očišćenim podacima ništa ne uklanja“. **To nije tačno** i utvrđeno je tek pri
> ispravci — videti [P-46](#p-46--ključ-za-duplikate-ne-podnosi-prazna-polja) i
> [P-47](#p-47--ključ-za-duplikate-ne-obuhvata-iznos-ni-valutu).

---

### P-46 — Ključ za duplikate ne podnosi prazna polja

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `fleet/support/fuel.py` — `_dedupe_omv_transaction_lines()` |
| **Obračun** | [V-06](obracuni/06-02-flota-gorivo.md#v-06--prečišćavanje-omv-transakcija) |

**Kako je otkriveno [P]:** pri ispravci [P-26](#p-26--izveštaj-goriva-za-upravu-nema-zaštitu-pri-čitanju)
tri postojeća testa izveštaja za upravu prestala su da vraćaju bilo koji red.

**Šta je zatečeno [P]:** prečišćavanje bira „pravi“ red transakcije tako što traži
podudaranje po pet polja:

```python
license_plate_no=OuterRef("license_plate_no"),
transaction_date=OuterRef("transaction_date"),
product_inv=OuterRef("product_inv"),
voucher=OuterRef("voucher"),
quantity=OuterRef("quantity"),
```

Tri od tih pet polja **smeju da budu prazna** u bazi (`product_inv`, `voucher`,
`quantity`). U SQL-u poređenje `NULL = NULL` **nije tačno**, pa red sa praznim vaučerom
**ne pronalazi ni samog sebe**. Posledica: `filter(id=Subquery(...))` ga izostavlja.

**Posledica [P]:** svaka OMV transakcija **bez broja vaučera ili bez količine tiho
nestaje** sa svih ekrana goriva koji koriste `filter_omv_fuel_queryset()` — pregled
goriva, fakture goriva, detalj vozila, trošak po kilometru. Ne prikazuje se nikakvo
upozorenje; iznos jednostavno nije u zbiru.

> Ovo **nije** bilo unedeno ispravkom P-26 — postojalo je i ranije, a ispravka ga je
> samo učinila vidljivim.

**Šta je urađeno (18.09.2026.) [P]:** podudaranje je učinjeno otpornim na prazna polja.
Prazna tekstualna polja izjednačavaju se sa `""`, prazna količina sa dogovorenom
zamenom, i to **samo unutar podupita** — spoljni upit se ne dira, da se ne pokvari
nijedno postojeće grupisanje:

```python
.filter(
    license_plate_no=OuterRef("license_plate_no"),
    transaction_date=OuterRef("transaction_date"),
    _key_product=Coalesce(OuterRef("product_inv"), DEDUPE_NO_TEXT),
    _key_voucher=Coalesce(OuterRef("voucher"), DEDUPE_NO_TEXT),
    _key_quantity=Coalesce(OuterRef("quantity"), DEDUPE_NO_QUANTITY, ...),
)
```

> **Posledica za korisnika [Z]:** na ekranima goriva mogu se pojaviti transakcije kojih
> ranije nije bilo, pa **iznosi mogu porasti**. Koliko — zavisi od toga koliko zapisa u
> bazi nema vaučer ili količinu, što treba **prebrojati na stvarnim podacima**.

---

### P-47 — Ključ za duplikate ne obuhvata iznos ni valutu

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Za proveru** |
| **Gde** | `fleet/support/fuel.py` — `_dedupe_omv_transaction_lines()` |
| **Obračun** | [V-06](obracuni/06-02-flota-gorivo.md#v-06--prečišćavanje-omv-transakcija) |

**Šta je zatečeno [P]:** dva reda se smatraju **istom transakcijom** ako im se poklope
tablica, vreme, proizvod, vaučer i količina. **Iznos (`gross_cc`, `amount`) i valuta
(`supplier_currency`) ne ulaze u to poređenje.** Koji red preživljava bira se po
`-invoiced`, `-invoice_date`, `-id` — dakle **po stanju fakturisanja, nikada po iznosu**.

**Posledica [Z]:** ako se dva zapisa razlikuju **samo** po iznosu ili valuti, jedan će
biti odbačen, a koji — zavisi od redosleda upisa. Prikazani iznos tada nije zbir već
izbor.

**Zašto je status „za proveru“ [Z]:** nije potvrđeno da takvi parovi **postoje u stvarnim
podacima**. Moguće je i da je ovo namerno, jer se isti račun preuzima u dve faze
(predračun bez iznosa, pa konačan račun). Bez uvida u podatke se ne može zaključiti.

**Šta proveriti pre bilo kakve izmene [Z]:** prebrojati u `TransactionOMV` grupe sa
istom tablicom, vremenom, proizvodom, vaučerom i količinom, a **različitim** `gross_cc`
ili `supplier_currency`. Ako takvih grupa nema — ponašanje je bezopasno i ovo se zatvara
kao „prihvaćeno“. Ako ih ima, treba odlučiti da li su to duplikati ili zasebne stavke.

---

### P-27 — Formule 11 izveštaja nisu u projektu

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `fleet/support/report_queries.py` |
| **Obračun** | [6.5.5](obracuni/06-05-flota-izvestaji.md#655-izveštaji-nad-nasleđenim-pogledima) |

**Šta je zatečeno [P]:** jedanaest izveštaja Flote se **ne računaju u aplikaciji** —
cela formula je u pogledu u bazi (`dbo.fleet_tro_svi`, `fleet_tro_goriva_m`,
`fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`, `tro_zarade`,
`fleet_dobavljaci`, `fleet_magacin_rez`, `fleet_otpis`, `kasko_rate`).
Aplikacija izvršava `SELECT` i prikazuje rezultat.

**Posledice [Z]:**

1. Na pitanje **„odakle ovaj iznos“** ne može se odgovoriti iz koda.
2. Promena pogleda u bazi menja rezultat na ekranu **bez ijedne izmene u aplikaciji**
   i **bez traga u istoriji verzija**.
3. Izveštaji za upravu zavise od objekata koje niko ne održava zajedno sa aplikacijom.

**Predlog rešenja [Z]:**

1. Preuzeti definicije (DDL) svih 11 pogleda — **već zatraženo**.
2. Smestiti ih u `dokumentacija/sql/` da budu pod kontrolom verzija.
3. Dokumentovati formulu svakog izveštaja u poglavlju 6.5.5.
4. Odrediti vlasnika koji odobrava izmene tih pogleda.


**Delimično razrešeno (18.09.2026.) [P]:** pri čišćenju repozitorijuma nađene su tri
datoteke sa **stvarnim definicijama pogleda** i premeštene u
[`dokumentacija/ddl-nasledjenih-pogleda/`](../ddl-nasledjenih-pogleda/README.md):

| Datoteka | Sadrži |
|---|---|
| `naplata-pogledi.sql` | Sedam pogleda Naplate: `baza`, `v_if`, `v_duplikati`, `ispravke`, `tuzeni`, `dodela bucketa`, šifarnik partnera |
| `fleet_trebovanja.sql` | `CREATE view [dbo].[fleet_trebovanja]`, uključujući zakomentarisanu prethodnu verziju |
| `nbv_roba.sql` | `CREATE view [dbo].[nbv_roba]` |

Dve od njih (`fleet_trebovanja.sql`, `nbv_roba.sql`) **nisu bile u kontroli verzija**.

**Šta je time odgovoreno [P]:** formula za `vrednost_nab` (`kol * cena`), granica
„304“ u pogledima Naplate, razredi starosti duga i razlika između stare i nove verzije
pogleda `fleet_trebovanja` (godina 2024 → 2026, vrste artikala `REZ`/`GOR` → sve).

**Šta i dalje nedostaje [P]:** DDL za **11 izveštaja Flote** — `fleet_tro_svi`,
`fleet_tro_goriva_m`, `fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`,
`tro_zarade`, `fleet_dobavljaci`, `fleet_magacin_rez`, `fleet_otpis`, `kasko_rate`.
Za njih se na pitanje „odakle ovaj iznos“ i dalje **ne može odgovoriti iz projekta**.

---

## 10.4.1. Obračuni — Kadrovi

### P-28 — Dva različita obračuna dnevnih sati

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za proveru |
| **Gde** | `hr/services/attendance.py:313` i `:474` |
| **Obračuni** | [K-01](obracuni/06-06-kadrovi.md#k-01--dnevni-sati-rada-iz-evidencije-prolazaka), [K-02](obracuni/06-06-kadrovi.md#k-02--dnevni-sati-iz-obračunatih-parova-drugi-postupak) |

**Šta je zatečeno [P]:** iz **iste** evidencije prolazaka sistem računa sate na
**dva različita načina**, sa različitim pravilima:

| | K-01 `calculate_daily_hours_from_clock_events` | K-02 `get_daily_work_hours` |
|---|---|---|
| Izvor | `C_Prolasci_Radnika` — pojedinačni prolasci | `c_parovi_radnika_detalji` — gotovi parovi |
| Uparivanje | Sam upa­ruje po tasterima | Preuzima uparena trajanja |
| Službeni izlazak | **Računa do 16:00** | Uzima `Trajanje_Sluzbeno` iz izvora |
| Pauza | **Prijavljuje kao problem, ne računa** | **Računa, najviše 30 minuta** |
| Neispravno dug zapis | Nema provere | **Izuzima `Trajanje_1 >= 20`** |
| **Gde se prikazuje** | **Radna lista zaposlenog** | Samo `manage.py hr_attendance_summary` |

**Posledica [Z]:** za isti dan i istog zaposlenog dva postupka daju **različit broj sati**.
Zaposleni na radnoj listi vidi jedan broj, a komanda za pregled prisustva drugi. Nije
zabeleženo koji je merodavan.

**Dodatni nedostatak K-01 [P]:** prolasci se grupišu **po datumu prolaska**
(`attendance.py:337`), pa **smena preko ponoći ne može biti uparena** — ulaz u 22:00
ostaje „bez izlaza“, a izlaz u 06:00 „bez prethodnog ulaza“. Dan dobija dva problema,
a **sati se ne računaju uopšte**.

**Predlog rešenja [Z]:**

1. Odrediti koji je postupak merodavan i drugi ukloniti ili jasno označiti kao pomoćni.
2. Ako ostaje K-01, dodati uparivanje preko ponoći (otvoren ulaz prenosi se u sledeći dan).
3. Uskladiti postupanje sa pauzom — vidi pitanje **Q25**.

> **Pre izmene potrebna potvrda [N]:** moguće je da je K-02 ostatak ranije faze, a K-01
> trenutno rešenje. Treba proveriti da li se komanda `hr_attendance_summary` uopšte koristi.

---

### P-29 — Otvoreno bolovanje nestaje sa radne liste

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `hr/services/sick_leave.py:194` |
| **Obračun** | [K-07](obracuni/06-06-kadrovi.md#k-07--bolovanja--uvoz-rfzo-i-povezivanje) |

**Šta je zatečeno [P]:** za bolovanje bez datuma zaključenja (status „Aktivno“) kao
kraj se uzima **datum RFZO izvoza**:

```python
end = min(last, leave.end_date or leave.source_date)
```

**Posledica [Z]:** bolovanje koje i dalje traje prikazuje se na radnoj listi **samo do
dana poslednjeg uvoza**. Ako se RFZO datoteka ne uveze mesec dana, poslednjih mesec dana
bolovanja **nestaje sa radne liste**, iako zaposleni i dalje odsustvuje.

**Predlog rešenja [Z]:** za otvoreno bolovanje prikazivati odsustvo **do kraja meseca
koji se gleda** (ili do današnjeg dana), uz jasnu oznaku *„otvoreno — poslednji izvoz
od <datum>“*, umesto tihog prekidanja.

---

## 10.4.2. Obračuni — Mobilna telefonija

### P-30 — Izuzeće od parkinga nema period važenja

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `mobilni/withholdings.py:50-51`, `mobilni/models.py:272-287` |
| **Obračun** | [M-02](obracuni/06-07-mobilni.md#m-02--izuzeci-od-parkinga) |

**Šta je zatečeno [P]:** tabela izuzetaka ima **samo broj telefona**, bez perioda:

```python
def parking_exempt_phone_numbers(year=None, month=None):
    return {normalize_phone_number(item.phone_number) for item in MobileParkingExemption.objects.all()}
```

Funkcija **prima godinu i mesec, ali ih ne koristi**.

**Posledica [Z]:** izuzetak upisan danas menja i **već obračunate prošle mesece**.
Ako je obustava za avgust već prosleđena u zarade, a u septembru se doda izuzetak,
avgustovski ekran će prikazati **drugi iznos** nego što je prosleđen — bez traga o
tome šta je bilo.

**Predlog rešenja [Z]:** dodati polja „važi od“ i „važi do“ na izuzetak i filtrirati
po obračunskom mesecu. Postojeći izuzeci bi dobili „važi od“ sa datumom upisa.

---

### P-31 — Obustava se nigde ne čuva

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za rešavanje |
| **Gde** | `mobilni/withholdings.py`, `mobilni/views/mobile.py:903` |
| **Obračun** | [M-01](obracuni/06-07-mobilni.md#m-01--obustava-po-zaposlenom) |

**Šta je zatečeno [P]:** obustava se **računa pri svakom otvaranju ekrana ili izvoza**
i **nigde se ne čuva**. Ne postoji model koji beleži obračunatu obustavu.

**Posledica [Z]:** ne postoji odgovor na pitanje **„koji je iznos stvarno prosleđen u
zarade za avgust“**. Svaka naknadna izmena paketa, dodele ili izuzetka menja i prikaz
za prošle mesece. Rezultat koji ulazi u zaradu zaposlenog nema ni istoriju ni revizorski trag.

**Tri prateća nedostatka [P]:**

1. **Potrošnja bez dodele tiho ispada.** U obračun ulaze samo stavke potrošnje koje imaju
   dodelu sa **istim** periodom i brojem. Ako dodele za taj mesec nisu uvezene, cela
   potrošnja **nestaje iz obračuna**, bez upozorenja i bez brojača.
2. **Negativna obustava se izvozi.** Kada je neto iznos paketa veći od potrošnje,
   obustava je negativna i takva ulazi u CSV za zarade — vidi pitanje **Q29**.
3. **Obustava jednaka nuli se ne izvozi**, dok se negativna izvozi. Pravilo nije dosledno.

**Predlog rešenja [Z]:**

1. Uvesti tabelu obračunatih obustava po mesecu, sa trenutkom obračuna i korisnikom,
   koja se **zaključava** pri izvozu u zarade.
2. Prikazati broj stavki potrošnje **bez odgovarajuće dodele** kao upozorenje na ekranu.
3. Odlučiti šta sa negativnom obustavom (**Q29**).

---

### P-32 — Rupe u razvrstavanju bivših zaposlenih

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `mobilni/withholdings.py:238-249` |
| **Obračun** | [M-03](obracuni/06-07-mobilni.md#m-03--razvrstavanje-zaposleni--bivši--nezaposleni) |

**Tri odvojena nedostatka [P]:**

**A) Zaposleni koji je otišao u toku obračunskog meseca nije nigde.**
Uslov za „bivšeg“ je `datum odlaska < prvi dan meseca`. Neaktivan zaposleni sa datumom
odlaska 20.08. **nije** u izveštaju „Zaposleni“ (nije aktivan) ni u „Bivši“
(odlazak nije pre 01.08.). Pojavljuje se samo u zbirnom izveštaju „Sve“ — i **ne ulazi
u izvoz za zarade**, iako je deo meseca radio.

**B) Neaktivan bez datuma odlaska uvek je „bivši“.**
Ako datum odlaska nije unet, sistem pretpostavlja da je zaposleni otišao. Zaposleni koji
je privremeno označen kao neaktivan zbog greške u podacima završava među bivšima.

**C) Kod više korisnika mobilnog uzima se poslednji po ID-u.**
Ako zaposleni ima više zapisa u evidenciji korisnika, uzima se onaj sa najvećim ID-em
(`order_by("-id").first()`), a ne onaj sa odgovarajućim datumom.

**Predlog rešenja [Z]:** uvesti pravilo „zaposlen bar jedan dan u obračunskom mesecu“
umesto poređenja sa prvim danom, i tražiti izričitu potvrdu kada datum odlaska nedostaje.

---

### P-34 — Poseban broj telefona upisan u kod umesto u bazi

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Potvrđena greška** — naručilac, 18.09.2026. |
| **Gde** | `mobilni/withholdings.py:16, 94, 161-162` |
| **Obračun** | [M-01](obracuni/06-07-mobilni.md#m-01--obustava-po-zaposlenom) |

**Šta je zatečeno [P]:**

```python
SPECIAL_PHONE_NUMBER = "381637781481"
```

Za taj broj se u obračunu obustave **ne odbija neto iznos paketa**, pa se zaposlenom
obustavlja **ceo iznos**:

> obično: `osnovica PDV − neto paketa + parking + NZRD`
> za taj broj: `osnovica PDV + parking + NZRD`

Pravilo postoji na **dva mesta** — u Python funkciji `calculate_withholding()` i u SQL
izrazu `withholding_amount_expression()`. Oba moraju ostati usklađena.

**Odluka naručioca [P]:** ovo je **greška**. Poslovni izuzetak ne sme biti u kodu —
**mora se čuvati u bazi**.

**Posledice postojećeg stanja [Z]:**

1. Dodavanje ili uklanjanje takvog broja zahteva **izmenu koda i isporuku nove verzije**.
2. Administracija ne može sama da održava spisak.
3. Nema **istorije** — ne zna se od kada pravilo važi za taj broj.
4. Nema **obrazloženja** — ni u kodu ni u bazi ne piše zašto je taj broj izuzet.
5. Ako se broj prenese drugom zaposlenom, pravilo **ostaje uz broj**, ne uz lice.

**Predlog rešenja [Z]:**

| Korak | Opis |
|---|---|
| 1 | Dodati oznaku u evidenciju — na **dodelu broja** (`MobileAssignment`) ili na zaseban šifarnik izuzetaka, po ugledu na postojeći `MobileParkingExemption` |
| 2 | Predvideti **period važenja** i **obrazloženje**, da se izbegne isti nedostatak kao kod izuzetka za parking (**P-30**) |
| 3 | Preneti postojeći broj u bazu i **ukloniti konstantu iz koda**, na **oba** mesta (Python i SQL izraz) |
| 4 | Dopuniti testove — postojeći testovi se oslanjaju na konstantu |

> **Napomena [Z]:** rešenje je slično već postojećem obrascu `MobileParkingExemption`,
> pa se može preuzeti njegova struktura — ali sa periodom važenja, koji tamo nedostaje.

---

## 10.4.3. Obračuni — Isplate

### P-33 — Virman skraćuje podatke i ne čuva poslatu datoteku

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za rešavanje |
| **Gde** | `isplate/services/virman.py:56-60, 195-213` |
| **Obračun** | [I-01](obracuni/06-10-isplate.md#i-01--generisanje-datoteke-virmana) |

**A) Tiho skraćivanje [P]**

Funkcija upisa u red seče svaku vrednost na širinu polja, **bez ijedne provere**:

```python
def _write(record, start, width, value, align="left"):
    text = text[:width]
```

| Polje | Širina | Šta se dešava |
|---|---|---|
| Naziv primaoca | 35 | Duže ime se odseca |
| **Mesto primaoca** | **10** | „Novi Beograd“ (12) postaje **„Novi Beogr“** |
| Naziv platioca | 35 | Odseca se |

Posledica [Z]: banka dobija **nepotpun naziv mesta**, a korisnik ne zna da se to desilo.
Za naziv primaoca to može značiti i **neprepoznavanje primaoca**.

**B) Bez opštine boravka koristi se „Beograd“ [P]**

Ako zaposleni nema unetu opštinu boravka, upisuje se `Beograd` — **bez upozorenja**,
i za zaposlene koji tamo ne žive.

**C) Sadržaj poslate datoteke se ne čuva [P]**

Na nalogu se beleži **samo da je virman rađen**, kada i ko. Sama datoteka se **ne čuva**.

Posledica [Z]: ako se posle generisanja promeni iznos akontacije ili račun zaposlenog,
**ne postoji način** da se utvrdi šta je poslato banci. Kod neslaganja sa izvodom nema
dokaza o poslatom nalogu.

**Predlog rešenja [Z]:**

1. Pri skraćivanju prijaviti grešku ili upozorenje umesto tihog sečenja — naročito za
   naziv primaoca i mesto.
2. Tražiti izričitu potvrdu kada opština boravka nedostaje, umesto podrazumevanog Beograda.
3. Uvesti tabelu generisanih virmana koja čuva **sadržaj datoteke ili njen otisak**,
   spisak obuhvaćenih naloga, ukupan iznos, datum i korisnika.

---

## 10.4.4. Obračuni — Potraživanja

### P-35 — Nepoznato dospeće prikazuje se kao „Nedospelo“

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `potrazivanja/services/sync.py:76-78` |
| **Obračun** | [PT-01](obracuni/06-08-potrazivanja.md#pt-01--starosni-razredi-baketi) |
| **Pitanje** | Q33 |

**Šta je zatečeno [P]:**

```python
def bucket(due, as_of):
    if due is None or due >= as_of:
        return "0.1"  # Deliberately preserves legacy unknown-date bucket.
```

Razred `0.1` („Nedospelo“) objedinjuje **dva različita poslovna slučaja**:

| Slučaj | Poslovno značenje |
|---|---|
| `due >= as_of` | Potraživanje **još nije dospelo** — uredno je |
| `due is None` | **Ne zna se** kada dospeva — može biti i nekoliko godina staro |

**Posledica [Z]:** dug star godinu dana kome nije unet datum dospeća prikazuje se u koloni
**„Nedospelo“**, zajedno sa urednim potraživanjima. Služba naplate ga ne vidi kao problem.

**Dokaz sa izvora [P]:** pogled `dodela_baketa` računa **dve** oznake koje se kod praznog
dospeća **ne slažu**:

```sql
CASE WHEN DATEDIFF(DAY, dpo, GETDATE()) <= 0 THEN 0 ELSE 1 END AS kategorija
```

Sa `dpo = NULL` poređenje je `UNKNOWN`, pa red pada u `ELSE` → **`kategorija = 1`
(dospelo)**, dok `baket` istovremeno ide u **`0.1` (nedospelo)**.

> **Ista stavka je „dospela“ po jednoj koloni i „nedospela“ po drugoj — već u izvoru.**

Django kod obe vrednosti **čuva i označava**:

```python
resolution_details = {"bucket": ..., "category": integer(row.get("kategorija")),
                      "unknown_due": due is None}
```

**Koliko ih ima [P]:** pri prenosu je zatečeno **9 otvorenih stavki bez dospeća**, ukupnog
salda **−310.678,54 RSD**. Zbirna kartica ih **prikazuje zasebno**, a u tabeli ostaju u
razredu `0.1` radi uporedivosti sa Naplatom.

**Olakšavajuće okolnosti [P]:**

1. Pravilo je **namerno preuzeto** iz nasleđene Naplate, da se snimci mogu porediti
   tokom prelaska — izričito zabeleženo u komentaru koda.
2. Sistem **broji** stavke bez dospeća (`unknown_due_count` u zbirnim pokazateljima snimka).
3. Svaka pozicija nosi oznaku `unknown_due` u `resolution_details`.
4. Beleži se i **način utvrđivanja dospeća** (`due_date_method`).

**Predlog rešenja [Z]:** posle završenog prelaska sa Naplate uvesti **osmi razred**
„Nepoznato dospeće“ i prikazati ga zasebnom kolonom. Podaci za to **već postoje**.

> **Pre izmene potrebna potvrda [N]:** dok Naplata i Potraživanja rade paralelno,
> promena pravila bi **onemogućila poređenje** dva sistema. Vidi **P-18**.


**Potvrda sa izvora (18.09.2026.) [P]:** DDL nasleđenog pogleda `dodela bucketa`
nađen je u projektu i premešten u
[`ddl-nasledjenih-pogleda/naplata-pogledi.sql`](../ddl-nasledjenih-pogleda/README.md#razredi-starosti-duga--dodela-bucketa).
On **potvrđuje da pravilo dolazi iz baze**, a ne iz Django koda:

```sql
CASE WHEN DATEDIFF(DAY, dpo, GETDATE()) BETWEEN 1 AND 30 THEN 30
     ...
     ELSE 0.1 END AS baket
```

`DATEDIFF` sa praznim `dpo` vraća `NULL`, nijedan `WHEN` nije tačan i stavka pada u
`ELSE 0.1`. Django kod je to **verno preslikao**.

**Šta to menja [Z]:** ispravka u Djangu razdvojila bi razrede **samo u Potraživanjima**,
dok bi nasleđeni pogled i dalje vraćao staro. Dok Naplata radi paralelno
([P-18](#p-18--naplata-i-potraživanja-rade-paralelno)), dva ekrana bi pokazivala različite
brojeve za isti dug. **Odluku donositi zajedno sa gašenjem Naplate.**

---

## 10.4.5. Obračuni — Nabavka

### P-36 — Ukupan iznos faktura na izveštaju Nabavke je višestruko uvećan

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `nabavka/views/reports.py:57-60` |
| **Obračun** | [B-06](obracuni/06-09-nabavka.md#b-06--izveštaji-i-alarmi-nabavke) |

**Šta je zatečeno [P]:**

```python
"invoice_total": ProcurementInvoice.objects
    .filter(item_links__isnull=False)
    .distinct()
    .aggregate(total=Sum("amount"))["total"]
```

Filter po `item_links` pravi **spoj sa tabelom veza stavki i faktura**. Faktura se u
rezultatu pojavljuje **onoliko puta koliko ima povezanih stavki**.

`distinct()` **ne pomaže**: Django ga primenjuje na spoljni `SELECT`
(`SELECT DISTINCT SUM(...)`), a ne na skup redova koji se sabiraju. Pošto agregat vraća
jedan red, `DISTINCT` nema nikakvo dejstvo.

**Posledica [P]:** faktura od 100.000 RSD povezana sa tri stavke ulazi u zbir kao
**300.000 RSD**.

| Faktura | Iznos | Veza stavki | Ulazi u zbir kao |
|---|---|---|---|
| F-100 | 100.000,00 | 3 | 300.000,00 |
| F-200 | 50.000,00 | 1 | 50.000,00 |
| F-300 | 20.000,00 | 2 | 40.000,00 |
| **Tačno** | **170.000,00** | | **Prikazano: 390.000,00** |

**Predlog rešenja [Z]:** sabirati nad skupom bez ponavljanja, na primer:

```python
ProcurementInvoice.objects.filter(
    pk__in=ProcurementItemInvoiceLink.objects.values("invoice_id")
).aggregate(total=Sum("amount"))["total"]
```

> **Napomena [Z]:** isti obrazac (`filter` po vezi ka više redova + `Sum`) treba proveriti
> i na drugim mestima. U pregledanim modulima drugih pojava nije nađeno.


**Šta je urađeno (18.09.2026.) [P]:** primenjeno je predloženo rešenje — zbir ide nad
skupom faktura bez ponavljanja (`nabavka/views/reports.py`):

```python
# Svaka faktura se broji jednom; spoj preko item_links ponovio bi iznos za svaku stavku.
"invoice_total": ProcurementInvoice.objects.filter(
    pk__in=ProcurementItemInvoiceLink.objects.values("invoice_id")
).aggregate(total=Sum("amount"))["total"],
```

> **Posledica za korisnika [Z]:** prikazani „ukupan iznos faktura“ na izveštaju Nabavke
> **biće manji nego ranije**. Raniji iznos je bio pogrešan.

---

### P-37 — Brisanje UF faktura tiho kida veze

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `nabavka/services/source_snapshots.py:229-232`, `nabavka/models.py:229-236` |
| **Obračun** | [B-02](obracuni/06-09-nabavka.md#b-02--grupisanje-uf-stavki-u-uf-fakture) |

**Šta je zatečeno [P]:** posle obnavljanja UF faktura se **briše sve što se nije pojavilo**
u tom prolazu:

```python
UfInvoiceSnapshot.objects.exclude(pk__in=invoice_ids).delete()
```

Veza `ProcurementItem.uf_invoice` je `on_delete=SET_NULL`, pa se pri brisanju
**tiho prazni** — stavka predmeta nabavke ostaje bez fakture.

**Posledica [Z]:** ako se u izvoru promeni broj fakture ili identifikator partnera, menja
se ključ grupisanja, stara faktura se briše i **veza koju je korisnik ručno uspostavio
nestaje** — bez poruke, bez zapisa u istoriji i bez mogućnosti da se sazna šta je bilo
povezano.

**Predlog rešenja [Z]:**

1. Umesto brisanja, označiti fakturu kao neaktivnu (kao što rade Finansije i Potraživanja).
2. Ako brisanje ostaje, **prebrojati i prijaviti** koliko je veza prekinuto.
3. Zabraniti brisanje fakture koja ima povezane stavke predmeta (`PROTECT`).

---

### P-38 — Procenjena vrednost predmeta se ne poredi sa stavkama

| | |
|---|---|
| **Ozbiljnost** | Srednja |
| **Status** | Za proveru |
| **Gde** | `nabavka/models.py:110-116, 306-310` |
| **Obračun** | [B-01](obracuni/06-09-nabavka.md#b-01--procenjena-vrednost-stavke-i-predmeta) |
| **Pitanje** | Q36 |

**Šta je zatečeno [P]:** predmet nabavke ima **ručno uneto** polje „Procenjena vrednost“,
a stavke imaju svoju procenjenu vrednost (cena × količina). Sistem ih **nigde ne poredi**.

**Posledica [Z]:** vrednost po kojoj se predmet odobrava može se razlikovati od zbira
onoga što je stvarno traženo, a da niko ne primeti.

**Predlog rešenja [Z]:** prikazati zbir stavki uz unetu vrednost i istaći razliku.
Ne menjati automatski uneti podatak — vrednost predmeta može legitimno biti veća
(rezerva, troškovi dostave).

---

### P-39 — Ispravka u izvoru stvara dvojnika EUF fakture

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `nabavka/services/euf.py:49-57` |
| **Obračun** | [B-03](obracuni/06-09-nabavka.md#b-03--ključ-euf-fakture) |
| **Pitanje** | Q35 |

**Šta je zatečeno [P]:** identitet EUF fakture je otisak četiri polja:

> `datum` (izvorni tekst) **|** `naziv partnera` **|** `broj fakture` **|** `iznos`

Nasleđeni pogled nema stabilan identifikator, pa je ovo jedino rešenje bez izmene izvora. [Z]

**Dve posledice [Z]:**

**A) Ispravka u izvoru pravi novu fakturu.** Ako se ispravi iznos, naziv partnera ili
oblik datuma, nastaje **nov ključ**, pa sistem upisuje **novu fakturu**. Stara ostaje,
sa svim vezama ka predmetima nabavke i šiframa posla. Na spisku se pojavljuju **dve**
fakture za isti dokument.

**B) Dve stvarno različite fakture mogu dobiti isti ključ**, ako imaju isti datum,
partnera, broj i iznos. Tada se **spajaju u jednu**.

**Predlog rešenja [Z]:** proveriti da li izvor ima neki stabilan identifikator koji bi
mogao ući u ključ (npr. interni ID dokumenta). Ako nema — prikazati upozorenje kada se
pojave dve fakture istog partnera i broja sa različitim ključem.

---

### P-49 — Procedura osvežava tekuću godinu, a ispravke čitaju prethodnu

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Za proveru** |
| **Gde** | `sp_AzurirajNalogZ` (baza) + pogledi `ispravke`, `v_duplikati`, `tuzeni` |
| **Obračun** | [PT-03](obracuni/06-08-potrazivanja.md#pt-03--objavljivanje-snimka-stanja) |

**Šta je zatečeno [P]:** posle **30. aprila** pogledi se razilaze po godini koju čitaju:

| Pogled | Posle 30.04. čita |
|---|---|
| `baza` | **Tekuću** godinu |
| `ispravke`, `v_duplikati`, `tuzeni` | **Prethodnu** godinu |

To je **potvrđeno poslovno pravilo**, ne greška — vidi
[Prilog B](../ddl-nasledjenih-pogleda/README.md).

Istovremeno, procedura `sp_AzurirajNalogZ`, koja puni lokalni `nalog_z`, posle 30. aprila
osvežava **samo tekuću godinu**.

**Posledica [Z]:** posle aprila `ispravke` čitaju godinu koju procedura **više ne
osvežava**. Lokalna kopija prethodne godine tada je **stara koliko i poslednje aprilsko
osvežavanje** — a to se nigde ne vidi. Postojanje podataka **nije dokaz svežine**.

**Šta proveriti [Z]:**

1. Da li se prethodna godina osvežava nekim drugim putem.
2. Ako ne — da li se ispravke uopšte menjaju posle zaključenja godine. Ako se ne menjaju,
   problem ne postoji u praksi i zatvara se kao „prihvaćeno“.

**Predlog rešenja ako se menjaju [Z]:** proširiti proceduru da posle aprila osvežava i
prethodnu godinu, ili uvesti zaseban prolaz za nju — uz dogovor sa vlasnikom baze.

---

## 10.4.6. Obračuni — Ugovori i menice

### P-40 — APR provera zaobilazi SSL i prepoznaje samo jedan status

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `ugovori/apr_openapi.py:34-45` |
| **Obračun** | [U-01](obracuni/06-11-ugovori-i-menice.md#u-01--provera-statusa-partnera-u-apr-u) |
| **Pitanje** | Q38 |

**A) Zaobilaženje provere SSL potvrde [P]**

```python
try:
    response = requests.get(url, timeout=timeout)
except SSLError:
    urllib3.disable_warnings(InsecureRequestWarning)
    response = requests.get(url, timeout=timeout, verify=False)
```

Pri SSL grešci zahtev se **ponavlja bez provere potvrde**, uz gašenje upozorenja.

**Posledica [Z]:** podatak o statusu partnera — koji se koristi pri odlukama o ugovaranju
i plaćanju — može doći od **neprovereno g izvora**. Greška u potvrdi je upravo signal koji
ne bi trebalo zaobići.

**Predlog rešenja [Z]:** prekinuti sa jasnom porukom umesto zaobilaženja. Ako je problem
u zastarelim korenskim potvrdama na serveru, rešiti to na serveru (`certifi` je već u
zavisnostima).

**B) Prepoznaje se samo tačan tekst `активан` [P]**

```python
str(status or "").strip().casefold() == "активан".casefold()
```

Poređenje je **tačno**, ne „sadrži“, i traži **ćirilični** zapis.

**Posledica [Z]:** svaki drugi zapis statusa — `Активан у ликвидацији`, latinično
`Aktivan`, status sa dodatnim razmakom unutar reči — daje **`is_active = False`**,
pa partner izgleda kao ugašen iako nije.

**Predlog rešenja [Z]:** popisati sve vrednosti koje APR vraća (**Q38**) i uskladiti
uslov; do tada, kod nepoznatog statusa **ne menjati** `is_active`, nego samo upisati
`apr_status` i označiti za proveru.

---

### P-41 — Preuzimanje menica zavisi od izgleda stranice NBS-a

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `menice/scraper.py`, `menice/services.py:164-174` |
| **Obračun** | [U-03](obracuni/06-11-ugovori-i-menice.md#u-03--preuzimanje-menica-iz-registra-nbs) |

**A) Krhka integracija [P]:** podaci se preuzimaju **razlaganjem HTML stranice**
registra NBS (`BeautifulSoup`), a ne kroz programski interfejs. Promena izgleda stranice
zaustavlja preuzimanje.

**B) PIB Instituta upisan u kod [P]:**

```python
def sync_izlazne_menice(*, tax_code="100223617", ...):
```

Podrazumevani PIB je upisan kao podrazumevana vrednost parametra.

> **Napomena [Z]:** ovo je blaži slučaj od **P-34** — vrednost se **može** proslediti
> spolja, pa nije neophodna izmena koda. Ipak, podatak o firmi pripada konfiguraciji.

**Predlog rešenja [Z]:**

1. Preseliti PIB u konfiguraciju (isto rešenje kao za podatke platioca u virmanu, **P-33**).
2. Dodati proveru da je preuzimanje vratilo očekivanu strukturu i **jasnu poruku** kada nije.
3. Beležiti svaki prolaz u istoriju, kao što to rade Finansije i Potraživanja.

> **Slična krhka integracija [Z]:** Selenium preuzimanje goriva sa portala NIS i OMV
> (vidi [7. Integracije](07-integracije.md)) ima isti rizik.

---

## 10.4.7. Obračuni — Finansijska analitika

### P-42 — Konta i pravila toka gotovine upisani su u kod

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `finansije/services/cash_flow.py`, `reports.py` |
| **Obračun** | [F-07 … F-12](obracuni/06-01-finansije.md#611-registar-obračuna) |
| **Pitanje** | Q43 |

**Šta je zatečeno [P]:** obračun toka gotovine sadrži **više od 40 broja konta** upisanih
u kod — spiskove za dodatne `ON` naloge, zamene obaveza troškovima, zarade, refundacije,
PDV i završna isključenja. Isto važi i za isključenja u prihodima i rashodima
(`59900`, `69900`) i za konta faktura (`20400`, `20500`, `61420`, `61421`, `61521`, `64002`).

**Posledica [Z]:**

1. Izmena kontnog plana zahteva **izmenu koda i isporuku nove verzije**.
2. Nigde u bazi ne postoji zapis o tome koja pravila važe niti od kada.
3. **Pravilo je udvostručeno** — isto postoji i u izvornim procedurama `SPFINizv52/52nt`.
   Promena procedure **ne bi se odrazila** na aplikaciju, i obrnuto.

> **Olakšavajuća okolnost [P]:** kod je **verna kopija** postojeće poslovne metodologije.
> Svi spiskovi konta **navedeni su poimence** u
> [6.1.4](obracuni/06-01-finansije.md#konta-upisana-u-obračun-toka-gotovine), pa nisu
> skriveni.

**Predlog rešenja [Z]:** dogovoriti ko obaveštava o izmeni kontnog plana ili procedura,
i uvesti proveru koja upozorava kada se u izvoru pojavi konto koji pravila ne pokrivaju.

---

### P-43 — Mogući dvostruki obuhvat zajedničkih troškova

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `finansije/services/reports.py`, `shared_costs.py` |
| **Obračun** | [F-02, F-05, F-06](obracuni/06-01-finansije.md#611-registar-obračuna) |
| **Pitanje** | Q41 |

**Šta je zatečeno [P]:** postojeća metodologija to sama navodi:

> *„Osnovni `R` već sadrži sve odgovarajuće proknjižene stavke klase 5, uključujući
> eventualna knjiženja zajedničkih troškova u izvoru. Aplikacija nema zasebno pravilo
> koje iz klase 5 uklanja ranije proknjiženu raspodelu.“*

**Posledica [Z]:** ako se u knjigovodstvu uvede knjiženje raspodele zajedničkih troškova
na pojedinačne poslove, ista stavka bi ušla **i u rashode `R` i u raspodeljeni `ZT`**,
pa bi konačni rezultat `P − R − ZT` bio **dvostruko umanjen**.

**Trenutno stanje [Z]:** nije problem, jer se raspodela ne knjiži na taj način.
Ali to je pretpostavka koju aplikacija **ne proverava**.

**Predlog rešenja [Z]:** potvrditi sa knjigovodstvom da se raspodela ne knjiži na klasu 5,
i uvesti proveru koja upozorava ako se takva knjiženja pojave.

---

### P-44 — Promena centra pregrupiše celu istoriju Finansija

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `finansije/services/source.py:95-97` |
| **Obračun** | [F-01, F-02, F-13](obracuni/06-01-finansije.md#611-registar-obračuna) |
| **Pitanje** | Q42 |

**Šta je zatečeno [P]:** centar posla se uzima iz **aktuelnog** šifarnika (`posao.blok`)
pri svakoj sinhronizaciji. Ne postoji istorija pripadnosti posla centru po datumima.

**Posledica [P]:** ako se poslu promeni centar, **sva njegova ranija knjiženja** se pri
sledećoj sinhronizaciji pripišu novom centru. Izveštaj po centrima za **prošlu godinu**
može se promeniti, iako se nijedno knjiženje nije promenilo.

**Isti obrazac u Floti [P]:** vidi **P-05**. Flota za deo izveštaja **već ima** istorijsku
dodelu (`JobCode.assigned_date`), pa se isto rešenje može primeniti i ovde.

**Predlog rešenja [Z]:** uvesti istoriju pripadnosti posla centru sa datumima važenja,
i pri sinhronizaciji upisivati centar **koji je važio na datum knjiženja**.

> **Napomena [P]:** postojeća dokumentacija ovo **navodi kao svesno ograničenje**, ne kao
> grešku. Ovde se vodi zato što menja već objavljene izveštaje.

---

## 10.4.8. Struktura baze

### P-45 — Modul Menice nema migracije

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za rešavanje |
| **Gde** | Aplikacija `menice` |
| **Modul** | [3.7. Menice](moduli/03-07-menice.md) |
| **Pitanje** | Q44 |

**Šta je zatečeno [P]:** aplikacija `menice` **uopšte nema direktorijum `migrations/`**.
Ostale aplikacije ih imaju:

| Aplikacija | Migracija |
|---|---|
| `fleet` | 77 |
| `nabavka` | 20 |
| `hr`, `ugovori` | po 12 |
| `mobilni` | 8 |
| `potrazivanja` | 7 |
| `naplata` | 6 |
| `finansije` | 3 |
| `core` | 1 |
| **`menice`** | **0 — nema ni direktorijuma** |

Modeli `Menica` i `UlaznaMenica` **nisu** označeni sa `managed = False`, pa Django
očekuje da njima upravlja.

**Posledice [Z]:**

1. **`manage.py migrate` ne stvara tabele `menica` i `ulazna_menica`.** Na novom
   okruženju modul ne bi radio.
2. Pokretanje `makemigrations menice` napravilo bi **početnu migraciju sa `CREATE TABLE`**,
   koja bi na postojećoj bazi **pukla** — tabele već postoje.
3. **Nijedna izmena modela ne može se preneti** uobičajenim putem; svaka bi tražila ručnu
   izmenu u bazi.
4. Istorija strukture ovih tabela **ne postoji** u projektu.

> **Zašto testovi ipak prolaze [Z]:** Django za aplikacije bez migracija stvara tabele
> direktno iz modela pri pripremi test baze. Zato 2 testa modula prolaze, iako bi
> `migrate` na pravoj bazi zakazao.

**Predlog rešenja [Z]:**

1. Napraviti početnu migraciju: `manage.py makemigrations menice`.
2. Uporediti je sa **stvarnom strukturom** tabela u bazi i uskladiti razlike.
3. Označiti je kao već primenjenu: `manage.py migrate menice --fake-initial`.
4. Proveriti da posle toga `migrate` prolazi bez izmena.

> **Pre izmene [N]:** utvrditi kako su tabele prvobitno nastale (**Q44**) — ako su
> pravljene ručnim SQL-om, njihova struktura može odstupati od modela.

---

## 10.5. Infrastruktura

### P-15 — Jedan Celery radnik poništava razdvajanje redova

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `nssm.bat:31`, `ims_erp/settings/base.py:212` |

**Šta je zatečeno [P]:** produkcioni radnik se pokreće sa

```
celery -A ims_erp worker -l info -P solo -Q default,sync,selenium
```

`-P solo` znači **jedan zadatak u jednom trenutku**. Postavka
`CELERY_WORKER_CONCURRENCY = 2` u tom režimu **nema dejstva**.

**Posledica [Z]:** razdvajanje redova `sync` i `selenium`, uvedeno upravo zato da teški
Selenium poslovi ne blokiraju lake sinhronizacije, **ne daje nikakav efekat** dok radi
samo jedan radnik. Preuzimanje goriva koje traje sat vremena zaustavlja sve ostalo.

**Predlog rešenja [Z]:** pokrenuti **drugi Windows servis** — radnika vezanog samo za
red `sync`, a postojećeg ograničiti na `selenium`.

> **Potrebna potvrda [N]:** `-P solo` je verovatno izabran zbog poznatih teškoća
> Celery-ja na Windows-u. Pre izmene proveriti da li je to bio razlog.

---

### P-16 — Zaključavanje poslova popušta kada Redis nije dostupan

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `fleet/tasks.py:72-85` |

**Šta je zatečeno [P]:** ako Redis nije dostupan, zaključavanje se preskače i
**posao se ipak izvršava** (`fail-open`).

**Posledica [Z]:** pri ispadu Redisa dva ista posla mogu raditi istovremeno — na primer
dva Selenium preuzimanja goriva ili dve sinhronizacije servisa. Rezultat mogu biti
duplirani zapisi ili međusobno gaženje.

**Predlog rešenja [Z]:** za poslove koji upisuju podatke prekinuti izvršavanje kada
zaključavanje nije moguće (`fail-closed`), i zabeležiti to u istoriji kao „Preskočen“.

> **Napomena [P]:** Finansije ovo **već rešavaju bolje** — koriste SQL Server
> `sp_getapplock` u istoj sesiji, pa zaštita ne zavisi od Redisa.

---

### P-17 — Procedura `sp_AzurirajNalogZ` ne briše obrisane redove

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Prihvaćeno |
| **Gde** | `IMS_ERP.dbo.sp_AzurirajNalogZ` |

**Šta je zatečeno [P]:** procedura ažurira postojeće i dodaje nove redove, ali
**ne uklanja** redove koji su u međuvremenu obrisani u izvoru.

**Posledica [P]:** uspešno izvršavanje procedure **ne znači** da je lokalna kopija
`IMS_ERP.dbo.nalog_z` jednaka izvoru.

Dodatno, `BrojAzuriranihRedova` broji **sve** redove obuhvaćene naredbom `UPDATE`,
ne samo one čiji se sadržaj stvarno promenio — veliki broj ne znači veliku promenu. [P]

**Zašto je prihvaćeno [Z]:** procedura je poslovni objekat van aplikacije. Aplikacija je
**ne menja**, samo je pokreće. Finansijska analitika ovaj problem **zaobilazi** tako što
čita **udaljeni izvor**, a ne lokalnu kopiju.

**Za dalji rad [Z]:** pre eventualnog prelaska Naplate na lokalnu kopiju, ovo mora
biti rešeno — opisano u `naplata-lokalni-izvor-plan.md`, poglavlje 5 (dokument uklonjen 18.09.2026., u git istoriji `06f60c2`).

---

## 10.6. Podaci i moduli

### P-18 — Naplata i Potraživanja rade paralelno

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |

**Šta je zatečeno [P]:** dva modula pokrivaju isti posao:

| | Naplata (`naplata`) | Potraživanja (`potrazivanja`) |
|---|---|---|
| Izvor | Nasleđeni `dbo.*` pogledi | Sopstvene Django tabele uz sinhronizaciju |
| Brzina | Spora | Brza |
| Istorija stanja | Nema | Objavljeni snimci |
| Revizorski trag | Nema | `CollectionAudit` |
| Status | **Nasleđeno, gasi se** | Zamenjuje Naplatu |

**Posledica [Z]:** dok oba rade, isti podatak se može videti na dva mesta sa različitim
vrednostima, jer se čitaju različiti izvori u različito vreme.

**Odluka naručioca (18.09.2026.) [P]:** Naplata se **ne dokumentuje**; sav novi rad
ide u Potraživanja.

**Za dalji rad [Z]:** odrediti datum gašenja Naplate i ukloniti njen meni iz interfejsa
kada Potraživanja preuzmu sve funkcije, uključujući pravnu službu.

---

### P-19 — Dva mehanizma za ograničenje po centrima

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `core/models.py:78-90` |
| **Pitanje** | Q5 |

**Šta je zatečeno [P]:**

| Polje | Tip |
|---|---|
| `CustomUser.allowed_centers` | Veza više-prema-više ka `OrganizationalUnit` |
| `CustomUser.allowed_center_codes` | Tekst, šifre odvojene zarezima |

Oba postoje istovremeno. Različiti moduli koriste različito:

| Modul | Koristi |
|---|---|
| `fleet/support/management_reports.py: allowed_centers()` | **Oba, sabrano** |
| `fleet/support/fleet_snapshot.py` | Samo `allowed_centers` |
| `fleet/views/center_statistics.py` | Samo `allowed_centers` |

**Posledica [Z]:** korisnik kome je upisana šifra centra samo u tekstualno polje
vidiće izveštaje za upravu, ali **neće** videti presek stanja flote za taj centar.
Pravo pristupa zavisi od ekrana, što je teško objasniti korisniku.

**Predlog rešenja [Z]:** odrediti jedan merodavan mehanizam, preseliti podatke i ukloniti
drugi. Veza ka `OrganizationalUnit` je pouzdanija jer se oslanja na šifarnik.

---

### P-20 — Model Naplate navodi nepostojeći pogled

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | Prihvaćeno |
| **Gde** | `naplata/models.py:163` naspram `naplata/queries.py:32` |

Model navodi tabelu `dodela_bucketa`, dok stvarni upiti koriste **`dodela_baketa`**.

**Za dalji rad [Z]:** **ne preimenovati aktivni pogled** na osnovu modela — model je taj
koji je pogrešan. Pošto se Naplata gasi, ispravka nema svrhu.

---

## 10.7. Repozitorijum

### P-21 — Radni fajlovi u repozitorijumu

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | **Rešeno** (18.09.2026.) |

| Šta | Veličina | Napomena |
|---|---|---|
| `db.sqlite3` | 6,7 MB | Naveden u `.gitignore`, ali je u projektu |
| `ims-flota-worker-err.log` | 9,8 MB | Dnevnik rada |
| `ims-flota-worker-out.log` | 7,8 MB | Dnevnik rada |
| `tmp*.csv` | ~1,6 MB | Privremeni izvozi |
| `~$*.docx` | — | Privremeni Word fajlovi |
| Word i Excel analize u korenu | ~4 MB | Radni materijal, ne deo aplikacije |

**Predlog rešenja [Z]:** premestiti radni materijal u `dokumentacija/`, obrisati
privremene fajlove i dnevnike iz projekta, proveriti da li su zaista izvan kontrole
verzija.

**Šta je urađeno (18.09.2026.) [P]:** uklonjeno je samo ono kod čega nema dileme.

| Uklonjeno iz repozitorijuma | Šta je bilo |
|---|---|
| `tmp1192810480842213795.csv`, `tmp729760060394745781.csv` | Preuzimanja OMV transakcija koja ostavlja Selenium; ušla su u repozitorijum sa izmenom `361b81d`. |
| `~$*.docx` (4 fajla) | Word fajlovi zaključavanja otvorenog dokumenta, po 162 bajta. |

U `.gitignore` su dodata pravila `tmp*.csv` i `~$*`, da se isto ne ponovi.

**Drugi krug, po odluci korisnika (18.09.2026.) [P]:** uklonjeno je još **95 fajlova**.

| Grupa | Broj | Veličina | Napomena |
|---|---|---|---|
| `dokumentacija/arhiva/` | 42 | 20,7 MB | Međuverzije Word dokumenata koje su generatori pravili pre svake izmene. Direktorijum više ne postoji. |
| Snimci ekrana | 22 | 1,7 MB | 16 se nije pominjalo nigde, 6 samo u skriptama koje su takođe uklonjene. **Zadržana su tri** koja koristi `unos-vozila-carobnjak.md`. |
| Jednokratne `.py` skripte | 14 | 0,1 MB | Generatori Word dokumenata (`generisi_*`, `dopuni_*`) i provere (`provera_*`, `proveri_*`). |
| Word analize u korenu | 10 | 1,7 MB | Presek stanja (3), Kadrovi (4), Analiza aplikacije, Garaža IMS, Procena prenosa. Sadržaj je prešao u `docs/`. |
| Excel izvozi i planovi | 7 | 1,6 MB | Jednokratni izvozi i evidencije nabavke. |
| Dnevnici Celery-ja | 3 | 16,9 MB | **Bili izvan kontrole verzija — brisanje je trajno.** |
| `celerybeat-schedule.{bak,dat,dir}` | 3 | 1,7 KB | Stanje Celery beat-a od 02.12.2024.; beat ga sam pravi. |

Svi osim dnevnika bili su u gitu, pa ih **istorija i dalje čuva**.

**Šta je spaseno pre brisanja [P]:** tri datoteke koje su izgledale kao radni otpad
sadržale su **definicije nasleđenih SQL pogleda**. Premeštene su u
[`dokumentacija/ddl-nasledjenih-pogleda/`](../ddl-nasledjenih-pogleda/README.md), uz opis
šta koji pogled radi. Dve od njih **nisu bile u gitu** — brisanje bi bilo nepovratno.
Videti [P-27](#p-27--formule-11-izveštaja-nisu-u-projektu).

**Šta namerno nije dirano [P]:**

| | Zašto |
|---|---|
| `db.sqlite3` (6,7 MB) | Izvan kontrole verzija, a **trenutno je razvojna baza** — brisanje bi uništilo lokalne podatke. |
| `IZ 055 Radna lista.xlsx`, `IZ 073 Zahtev za put.doc`, `Obrazac za ocenjivanje.xlsx` | Originalni obrasci koje reprodukuju štampani šabloni u kodu (`work_time_sheet_print.html`, `putni_nalog_print_foreign.html`). |
| `izvestaji/backup_*.json` | Rezervne kopije podataka o dodelama vozila, unosu vozila i fotografijama. |

**Posledica na kod [P]:** komanda `import_garage_requests_excel` imala je podrazumevanu
putanju `"Pracenje nabavke za garazu.xlsx"`, koja sada ne postoji. Putanja je **postala
obavezan argument**, da komanda odmah javi grešku umesto da traži nepostojeći fajl.

---

### P-22 — Nekorišćene zavisnosti

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | **Rešeno** (18.09.2026.) |

| Biblioteka | Stanje |
|---|---|
| `djangorestframework` 3.15.2 | Nije u `INSTALLED_APPS`, ne koristi se nigde u kodu |
| `psycopg2-binary` 2.9.9 | Nijedna konfiguracija ne koristi PostgreSQL |

**Posledica [Z]:** nepotrebno održavanje i bezbednosno praćenje biblioteka koje sistem
ne koristi.


**Šta je urađeno (18.09.2026.) [P]:** oba reda su uklonjena iz `requirements.txt`.
Pre uklanjanja provereno je pretragom celog projekta da se `rest_framework` i `psycopg2`
**nigde ne uvoze** i da nisu u `INSTALLED_APPS`. Kodiranje datoteke (UTF-16LE sa BOM)
zadržano je nepromenjeno.

---

## 10.8. Ograničenja koja nisu greške

Ovo su svesna ograničenja sistema, navedena da bi se izbeglo pogrešno tumačenje.

| Ograničenje | Objašnjenje |
|---|---|
| **Podaci nisu u realnom vremenu** | Većina se osvežava jednom dnevno, noću. Korisnik ujutru vidi stanje od sinoć. |
| **Zavisnost od tri udaljena servera** | Finansije i Kadrovi ne rade ako `PUTGEO-SERVER`, `INFORMATIKA23` ili `SERFIN` nisu dostupni. |
| **Zavisnost od portala dobavljača goriva** | Promena izgleda stranice NIS-a ili OMV-a zaustavlja automatsko preuzimanje. |
| **Definicije nasleđenih pogleda nisu u projektu** | Promena pogleda u bazi menja rezultat na ekranu bez ijedne izmene u aplikaciji. |
| **Nema povratne veze ka knjigovodstvu** | Sistem čita knjiženja; ne knjiži. Jedini izlaz je datoteka virmana. |
| **Rezultati obračuna se ne čuvaju** | Skoro svi obračuni se rade u trenutku prikaza. Izveštaj otvoren danas i za mesec dana može dati različit rezultat za isti period, ako su se ulazni podaci promenili. |
| **Prosečna potrošnja ne razdvaja AdBlue** | `fleet_fuelconsumption` ne čuva vrstu proizvoda. Vozila koja koriste AdBlue imaju precenjenu potrošnju. |
| **Finansije izuzimaju zatvaranja** | Vrsta `ZAT` i konta `59900`/`69900` se namerno izostavljaju. Zbir svih stavki klase 5/6 posle zatvaranja godine je nula — to nije greška. |

---

## 10.9. Šta je proveravano i **nije** problem

Da bi se izbeglo ponovno ispitivanje istog:

| Provereno | Nalaz |
|---|---|
| `calculate_average_fuel_consumption_ever()` | **Ispravno** — obe granice se proveravaju na `mileage > 0` |
| `fleet_snapshot()` prosečna starost | **Ispravno** — računa samo vozila sa godinom između 1886. i tekuće |
| `service_category()` u `vehicle_maintenance.py` | **Ispravno** — normalizuje dijakritike i ćirilicu |
| `TrafficCard.for_plate()` | **Ispravno** — namerno odbija da pogađa kada tablica pripada većem broju vozila |
| Prečišćavanje OMV transakcija (V-06) | **Ispravno** i neophodno — bez njega su zbirovi višestruko uvećani |
| Kontrolni zbirovi pri sinhronizaciji Finansija | **Ispravno** — neslaganje zaustavlja objavu |
| `ReceivablePosition.balance` | **Ispravno** — proverava ga sama baza (`CheckConstraint`) |
| Zaštita od preklapanja u Finansijama | **Ispravno** — `sp_getapplock` u istoj sesiji |

---

## 10.10. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Detaljan opis pogođenih obračuna | [6. Analize i obračuni](06-analize-i-obracuni.md) |
| Plan daljeg razvoja | [11. Plan razvoja](11-plan-razvoja.md) |
| Održavanje i zakazani poslovi | [9. Održavanje](09-odrzavanje.md) |
| Sva otvorena pitanja za korisnika | [Inventar, poglavlje 14](../00-inventar-i-plan-dokumentacije.md) |
