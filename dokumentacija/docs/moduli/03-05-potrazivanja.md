# 3.5. Potraživanja

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Potraživanja** |
| Tehnički naziv | Django aplikacija `potrazivanja` |
| Adresa | `/potrazivanja/` |
| Bočni meni | `sidebar_potrazivanja.html` |
| Status | **Zamenjuje nasleđenu Naplatu** |

---

## 2. Poslovna namena

Odgovara na pitanje: **ko nam duguje, koliko, koliko dugo i šta je preduzeto.**

Nasleđena Naplata je isto radila, ali **čitanjem nasleđenih pogleda pri svakom otvaranju
ekrana** — sporo i bez istorije. Potraživanja umesto toga:

1. **Preuzimaju ceo izvor** u lokalne tabele.
2. **Proveravaju** preneto sa izvorom kroz **šest kontrola**.
3. **Objavljuju snimak stanja** na tačno određeni datum.
4. Svi ekrani čitaju **objavljeni snimak**, ne izvor.

> **[P] Ključna prednost:** moguće je videti stanje **kako je izgledalo ranije**.
> Naplata to ne omogućava.

---

## 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Služba naplate** | Prati dugovanja, vodi kontakte, poziva, izdaje opomene i pozivna pisma |
| **Pravna služba** | Vodi sudske postupke, stečajeve i UPPR |
| **Finansije** | Vidi saldo kupaca po šifri posla, kroz Finansijsku analitiku |
| **Rukovodioci poslova** | Vide naplativost svog posla |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Kontrolna tabla** | Dugovanja po partnerima i starosnim razredima |
| **Detalj partnera** | Stavke, dospeća, kontakti, aktivnosti, opomene, postupci |
| **Kontakti** | Osobe i kanali (telefon, mobilni, e-pošta), sa oznakom za proveru |
| **Aktivnosti** | Napomene i telefonski pozivi, sa ishodom i sledećom radnjom |
| **Opomene i pozivna pisma** | Dokument sa stavkama, rokom za odgovor i tekstom za štampu |
| **Pravni postupci** | Tuženi, tužili, stečaj, UPPR — sa istorijom promena |
| **Sinhronizacija** | Ručno pokretanje, istorija, koraci, kontrolni zbirovi, problemi prenosa |
| **Uvoz i izvoz** | Uvoz opomena iz Excel-a, izvoz tabela |

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Kontrolna tabla** | `/potrazivanja/` |
| Detalj partnera | `/potrazivanja/partner/<id>/` |
| Oznake partnera (važan kupac, provera) | `/potrazivanja/partner/<id>/oznaki/` |
| Unos i izmena zapisa | `/potrazivanja/unos/<vrsta>/`, `/izmena/<vrsta>/<id>/` |
| Arhiviranje zapisa | `/potrazivanja/arhiva/<vrsta>/<id>/` |
| **Pravni postupak** | `/potrazivanja/postupak/<id>/` |
| Promena u postupku | `/potrazivanja/postupak/<id>/promena/` |
| **Štampa opomene** | `/potrazivanja/dokument/<id>/stampa/` |
| **Sinhronizacija** | `/potrazivanja/sinhronizacija/` |
| Izvoz | `/potrazivanja/izvoz/` |
| Uvoz opomena | `/potrazivanja/uvoz-opomena/` |

---

## 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| Oznaka „važan kupac“ i „potrebna provera“ | Služba naplate |
| Kontakti: ime, prezime, funkcija, telefon, e-pošta | Služba naplate |
| Telefonski pozivi: datum, tekst, ishod, sledeća radnja | Služba naplate |
| **Opomene i pozivna pisma**: broj, datum, primalac, iznos, tekst, rok | Služba naplate |
| Stavke opomene (fakture) | Služba naplate |
| **Pravni postupci**: sud, broj predmeta, vrednost spora, kamata, troškovi | Pravna služba |
| Promene u postupku | Pravna služba |

---

## 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Tabela |
|---|---|---|
| **Partneri** | `dbo.partneri` (firma 1, grupa 1) | `potrazivanja_financepartneridentity` |
| **Knjiženja potraživanja** | `dbo.baza`, `dbo.ispravke` | `potrazivanja_receivableposting` |
| **Fakture IF** | Izvedeno grupisanjem knjiženja | `potrazivanja_invoicedocument` |
| **Otvorene pozicije i baketi** | `dbo.dodela_baketa` | `potrazivanja_receivableposition` |
| Šifre posla i centri | `[PUTGEO-SERVER].[bazaims].dbo.posao` | u pozicije |
| Nasleđene operativne evidencije | `kontakti`, `napomene`, `opomene`, `poziv_pismo`, `pozivi_tel`, `tuzbe` | Jednokratni prenos |

> **[P] Sinhronizacija se pokreće ručno** — nije u rasporedu zakazanih poslova. Postoji
> Celery zadatak `potrazivanja.tasks.sync_collections_task`, u redu **`sync`**, ali za
> automatski rad trebalo bi uključiti **broker, radnika i Beat raspored**.

### Centar posla — tačna šifra, nikad prefiks [P]

Centar se preuzima iz **`posao.blok` po tačnoj šifri**, sa `sif_pred=1`.

> **Centar se ne zaključuje iz prve dve cifre šifre**, i **ne uzima se** iz opšteg registra
> organizacionih jedinica — taj registar nije potpun izvor za sve šifre poslova.

Ako u izvornom šifarniku postoji duplirana ili prazna šifra posla, prenos se **prekida**
porukom *„Duplirana/prazna šifra posla u izvornom šifarniku.“* [P]

### Obim izvornih evidencija [P]

Snimak iz vremena prenosa — **nisu trajne konstante**:

| Skup | Redova | | Skup | Redova |
|---|---|---|---|---|
| `partneri` | 13.608 | | `tabela_if` | 98.791 |
| `baza` | 10.050 | | `duplikati18` | 111.153 |
| `ispravke` | 2.395 | | kontakti | 654 |
| `v_if` | 109.761 | | napomene | 103 |
| `v_duplikati` | 2.580 | | opomene | 895 |
| `dodela_baketa` | 1.586 | | pozivna pisma | 133 |
| `v_tuzeni` | 117 | | telefonski pozivi | 2.479 |
| `v_neodobreneIF` | 160 | | stara evidencija tužbi | 32 |
| `posao` (firma 1) | 415 | | pravni postupci / promene | 127 / 379 |

> **[Z]** Zbir uključuje i poglede i njihove istorijske pomoćne tabele, pa je to broj
> **sačuvanih izvornih redova, a ne broj jedinstvenih faktura**. Isti istorijski zapis može
> postojati i u pomoćnoj tabeli i u pogledu (`v_if` = `tabela_if` + IF od 2025.).

---

## 8. Tabele i kolone

Detaljno: [4.8. Potraživanja](../04-baza-podataka.md#48-potraživanja--potrazivanja).
**22 tabele** — najviše od svih modula.

| Grupa | Tabele |
|---|---|
| **Sinhronizacija** | `collectionsyncrun`, `collectionsyncstep`, `sourcedataset`, `sourcerow`, `legacyimportmap`, `importissue` |
| **Finansijski podaci** | `financepartneridentity`, `invoicedocument`, `receivableposting`, `duedateevidence` |
| **Snimci stanja** | `balancesnapshot`, `receivableposition`, `collectionstate`, `agingrule` |
| **Operativne evidencije** | `collectionprofile`, `collectioncontact`, `contactpoint`, `collectionactivity`, `collectionnotice`, `collectionnoticeitem` |
| **Pravni postupci** | `collectionlegalcase`, `collectionlegalevent`, `legalcaselink` |
| **Ostalo** | `electronicinvoicestatus`, `collectionaudit`, `collectionfileimport` |

### ⚠ Dve tabele postoje, ali se nikada ne pune [P]

| Tabela | Stanje |
|---|---|
| `duedateevidence` | Model postoji i `sync.py` ga uvozi, ali ga **nigde ne kreira** — jedini `objects.create` je u testovima. Pozicije dobijaju `due_date_method="legacy_views"` i dospeće **direktno iz `dodela_baketa`**. Nezavisan obračun dospeća **nije uveden**. |
| `electronicinvoicestatus` | Model postoji, ali ga **nijedna servisna funkcija ne kreira**. Ekran „Neodobrene IF“ čita **arhivirane redove `SourceRow`** skupa `v_neodobreneIF`, ne ovaj model. |

> **[Z] Zašto je to važno:** ko gleda samo spisak tabela pomisliće da sistem vodi zasebne
> dokaze o dospeću i istoriju SEF statusa. **Ne vodi ih.**

`duedateevidence` je pripremljen za istorijske tabele **bez primarnog ključa** — ima polje
`occurrence` i ograničenje `UniqueConstraint(import_run, source_table, source_key,
occurrence)`, da bi se ponovljeni identični redovi mogli sačuvati i prebrojati. [P]

### Skupovi koji postoje samo kao arhivirani izvor [P]

`v_tuzeni`, `tabela_if`, `duplikati18`, `sif_baket` i `sif_kategorija` čitaju se i čuvaju u
`SourceDataset` / `SourceRow`, ali **nemaju sopstvene poslovne modele**. Ekran „Utuženi
klijenti“ čita `SourceRow` skupa `v_tuzeni`.

---

## 9. SQL pogledi

Redovna sinhronizacija čita **13 finansijskih izvora**, ne pet. [P]

| Pogled | Uloga i zavisnosti | DDL |
|---|---|---|
| `partneri` | Udaljeni `BazaIMS.partner` + `Gruppartner`; **sve grupe**, ne samo grupa 1 | [✔](../../ddl-nasledjenih-pogleda/README.md) |
| `baza` | Udaljeni `nalog_z` + `partneri`; firma 1, grupa 1, konta `20400%`/`20500%`; godišnji izbor i `POC` | [✔](../../ddl-nasledjenih-pogleda/README.md) |
| `v_if` | IF **od 2025.** iz udaljenog `nalog_z` + `UNION ALL tabela_if`; **izvor dospeća** | [✔](../../ddl-nasledjenih-pogleda/README.md) |
| `v_duplikati` | IF iz **svih** godina + `duplikati18`; partner/veza u više godina i **MAX dospeća** | ⚠ sumnjiv |
| `dodela_baketa` | `baza` + prethodna dva; saldo, dospeće, starost i domaće/ino | [✔](../../ddl-nasledjenih-pogleda/README.md) |
| `ispravke` | Udaljeni `nalog_z` + `konto` + `partneri`; konta `2049%`, `2059%`, `2048%`, `2058%` | [✔](../../ddl-nasledjenih-pogleda/README.md) |
| `v_tuzeni` | Udaljeni `nalog_z` + `konto` + `partneri`; `2048%`/`2058%`, `promena='O'` | [✔](../../ddl-nasledjenih-pogleda/README.md) |
| `v_neodobreneIF` | `EFaktura.EDok` + `EStatusIZ` + `BazaIMS.partner` | **nema** |
| `tabela_if`, `duplikati18` | Istorijske pomoćne tabele (2006–2024, 2006–2020) | — |
| `sif_baket`, `sif_kategorija` | Šifarnici razreda i kategorija | — |
| `posao` | Šifre posla i centri (`blok`), `sif_pred=1` | — |

Definicije sedam pogleda nalaze se u
[Prilogu B — DDL nasleđenih pogleda](../../ddl-nasledjenih-pogleda/README.md), zajedno sa
dve granice tog ispisa. [P]

### `v_neodobreneIF` — jedini opis koji postoji [N]

Tog pogleda **nema u preuzetom DDL-u**. Pravila su poznata samo posredno, iz ranijeg plana
Naplate:

> Datum dokumenta **od 2025.**, `sif_dok=50`, `StatusIz=20` i status **različit od
> `Approved`**. To je **podskup poslatih faktura**, ne kompletna istorija SEF statusa.

| Napomena | |
|---|---|
| Pravi ključ izvora | **`EDok.ID`** |
| Izvedeni prikaz broja fakture | `SUBSTRING(EID,5,20)` — **nije pouzdan identifikator** |
| Faktura nestala iz pogleda | Može biti odobrena, obrisana **ili van filtera** — odsustvo **nije dokaz** statusa `Approved` |

Kolone koje aplikacija koristi: `oj`, `god`, `datum`, šifra i naziv partnera, `faktura`,
`Status na sefu`, `vreme statusa`, `komentar`. [P]

### Godišnji obuhvat se razlikuje po pogledu [P]

Posle **30. aprila** `baza` čita **tekuću** godinu, a `ispravke`, `v_duplikati` i `tuzeni`
**prethodnu** — to je **potvrđeno poslovno pravilo**, ne greška. Modul to beleži odvojeno,
u `run.scope["baza_years"]` i `run.scope["ispravke_years"]`.

> **[Z] Rizik svežine:** procedura `sp_AzurirajNalogZ` posle aprila osvežava **tekuću**
> godinu, a `ispravke` tada traže **prethodnu**. Ako se prethodna godina ne osvežava
> zasebno, **stara lokalna kopija nije dokaz svežine**.

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`potrazivanja/models.py`](../../../potrazivanja/models.py) |
| **Sinhronizacija i kontrole** | [`services/sync.py`](../../../potrazivanja/services/sync.py) |
| Čitanje izvora | [`services/source.py`](../../../potrazivanja/services/source.py) |
| Saldo po šiframa posla | [`services/reports.py`](../../../potrazivanja/services/reports.py) |
| **Normalizacija kontakata** | [`services/contacts.py`](../../../potrazivanja/services/contacts.py) |
| Prenos operativnih evidencija | [`services/operations.py`](../../../potrazivanja/services/operations.py) |
| Osamostaljivanje | [`services/independence.py`](../../../potrazivanja/services/independence.py) |
| Prava pristupa | [`potrazivanja/access.py`](../../../potrazivanja/access.py), [`permissions.py`](../../../potrazivanja/permissions.py) |

Testovi: **59 testova** u 5 fajlova, uključujući **proveru brzine čitanja**. [P]

---

## 11. Ulazni i izlazni podaci

| Smer | Šta |
|---|---|
| **Ulaz** | Nasleđeni pogledi; Excel uvoz opomena |
| **Izlaz** | Štampa opomena i pozivnih pisama; izvoz tabela; **saldo po šiframa posla Finansijama** |

---

## 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Finansije** | Tab „Potraživanja“ na kartici posla — `job_balances()` |
| **Ugovori** | `FinancePartnerIdentity.partner` → `ugovori_partner` |
| **Naplata** *(nasleđeno)* | Jednokratni prenos operativnih evidencija i pravnih postupaka |

---

## 13. Izveštaji i analize

**6 analiza.** Detaljno: [6.8. Potraživanja](../obracuni/06-08-potrazivanja.md).

| Oznaka | Naziv |
|---|---|
| PT-01 | Starosni razredi (7 baketa) — [P-35](../10-poznati-problemi.md) |
| PT-02 | Saldo stavke |
| PT-03 | Objavljivanje snimka stanja |
| **PT-04** | **Šest kontrolnih zbirova** |
| PT-05 | Saldo po šiframa posla |
| PT-06 | Normalizacija nasleđenih kontakata |

---

## 14. Uloge i prava pristupa

Modul ima **sopstveni sistem dozvola** (`potrazivanja/permissions.py`), uz uobičajeni. [P]

Ukupno **21 dozvola** [P]:

| Grupa | Dozvole |
|---|---|
| Pregled | `dashboard`, `partner_detail`, `table_data`, `sync_status` |
| **Obuhvat** | **`view_all`** — ceo obuhvat firme |
| Izlaz | `export`, `print` |
| Unos | `review_update`, `notice_import` |
| Operativni rad | `contact_*`, `activity_*`, `notice_*`, `legal_*` — svaki sa `create`, `update`, `archive` |

Korisnik bez `view_all` vidi samo **dozvoljene centre i šifre posla** (`scoped()`).
Pristup šifri posla se proverava **dvaput** — pri ulasku i pri filtriranju pozicija. [P]

> **[P] Dva ekrana su ograničenom korisniku potpuno nedostupna:** „Neodobrene IF“ (SEF) i
> „Utuženi klijenti“. Bez `view_all` dižu poruku *„Izveštaj nema raspodelu po šiframa
> posla.“* — jer se ti izvori ne mogu podeliti po šifri posla.

> **[P] Obuhvat se određuje serverski**, u svakoj listi, detalju, AJAX zahtevu i izvozu —
> **nezavisno od ulaznog URL-a**. Stari obrazac iz Naplate, gde je `?report=1` menjao
> vidljive šifre, **namerno nije prenet**.

### Kako su prenete stare dozvole Naplate [P]

| Stara dozvola | Nova |
|---|---|
| `naplata:lista_dugovanja_po_bucketima` | `view_all` — **osim za ulogu `pregled-naplate`** |
| `naplata:toggle_avans_klijent` | `review_update` |
| `notice_create` | Automatski dodaje i `notice_import` |

Provereno za uloge `uprava`, `pravna` i `pregled-naplate`: sve imaju pristup novoj
aplikaciji, a stara prava su ostala očuvana. Prenos je **ponovljiv** i deo redovnog
usklađivanja dozvola. [P]

---

## 15. Validacije i kontrole

> **Ovaj modul ima najviše kontrola u celom sistemu.** [Z]

| Kontrola | Gde |
|---|---|
| **Saldo = duguje − potražuje** | **Kontrola u bazi** (`CheckConstraint`) |
| Objavljen snimak mora imati vreme objave | Kontrola u bazi |
| Aktivno stanje mora biti **objavljen** snimak iste firme | `CollectionState.clean()` |
| Partner i dokument iste firme | `InvoiceDocument.clean()` |
| Knjiženje odgovara izvornom ključu partnera | `ReceivablePosting.clean()` |
| Faktura opomene pripada partneru opomene | `CollectionNoticeItem.clean()` |
| SEF dokument odgovara firmi i partneru | `ElectronicInvoiceStatus.clean()` |
| **Šest kontrolnih zbirova pre objave** | `publish_positions()` |
| **Baket izvora odgovara datumu snimka** | `publish_positions()` |
| Duplirani ključ pozicije | *„bez tihog spajanja“* |
| Prazan osnovni izvor | *„postojeći podaci ostaju objavljeni“* |
| Zaključavanje sinhronizacije | `sp_getapplock`, vezano za sesiju |
| **Lokalne izmene se ne prepisuju** | Ponovni uvoz beleži `local_profile_conflict` / `local_edit_conflict` — *„Lokalna izmena je zadržana. Nova izvorna verzija je u arhivi.“* |
| Ponovni uvoz posle osamostaljenja | **Odbija se:** *„Potraživanja već samostalno vode operativne podatke. Ponovni uvoz iz Naplate je isključen.“* |
| Ponovljeni uvoz iste Excel datoteke | Sprečen otiskom (`fingerprint`) |

> **[P] Ko šta menja:** izvorna finansijska polja menja **sinhronizacija**; kontakte,
> aktivnosti, oznake i opomene menja **korisnik**. Ponovni uvoz **ne sme izbrisati
> korisnički rad** — zato se sukobi beleže, a lokalna verzija zadržava.

### Osamostaljenje [P]

Početni prenos završava komanda **`initialize_potrazivanja`**, i to **samo jednom**.
Trenutak se upisuje u **`CollectionState.operations_independent_at`**. Posle toga
`include_legacy=True` se **odbija**.

### Uvoz opomena iz Excel-a [P]

| Osobina | Pravilo |
|---|---|
| **Obavezne kolone** | `sif_par`, `datum`, `iznos` |
| Opcione kolone | `naz_par`, `god`, `br_opomene`, `fakture`, `napomene` |
| Prihvaćeni sinonimi zaglavlja | `sifra`, `šifra`, `sifra partnera`, `naziv`, `godina`, `broj`, `broj opomene`, `napomena` |
| Valuta | Uvek **RSD** |
| Pre upisa | Prikazuje se **pregled** |
| Greška u bilo kom redu | **Sprečava ceo upis** |
| Isti fajl dvaput | Sprečeno otiskom, zapis u `CollectionFileImport` |

Izvoz poštuje **isti obuhvat i filtere kao lista**, sa zbirom **celog filtriranog skupa**,
ne samo prikazanih 100 redova. Tekst iz izvora **se ne izvozi kao Excel formula**. [P]

---

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| **Nepoznato dospeće** | Svrstava se u **„Nedospelo“** ([P-35](../10-poznati-problemi.md)) |
| Partner u finansijskim podacima bez šifarnika | Upisuje se **neaktivan**, uz zabeležen problem |
| Nestalo knjiženje | `active = False`, uz napomenu da to **nije dokaz brisanja iz ERP-a** |
| Bilo koja kontrola ne prođe | **Ništa se ne upisuje**, prethodni snimak ostaje |
| Prekinut prethodni prolaz | Automatski se označava kao neuspešan |
| Nasleđeni kontakt sa više osoba | Razdvaja se, uz oznaku **„Potrebna provera“** |
| Nema objavljenog snimka | Prazan rezultat, **ne greška** |
| **Stavka bez centra u izvornom šifarniku** | Prikaz **„Neraspoređeno“** — centar se ne nagađa |
| Zatvorena pozicija (saldo nula) | **Ne prikazuje se** kao otvorena stavka; dokumenti i aktivnosti ostaju |
| Negativan saldo | **Zadržava se** — ne pretvara se u nulu i ne uklanja kao greška |

### Zatečene stavke za proveru pri prenosu [P]

Nijedan od ovih zapisa **nije odbačen**:

| Oblast | Broj | Postupanje |
|---|---|---|
| Kontakti bez potvrđene veze sa partnerom | **32** | Sačuvan original i novi nepovezan kontakt |
| Napomene bez potvrđene veze | **13** | Sačuvan original i nova nepovezana aktivnost |
| Opomene bez potvrđene veze | **16** | Sačuvan original i nova nepovezana opomena |
| Pravni postupci bez potvrđene veze | **4** | Ostali u postojećoj tabeli i arhivi |
| Otvorene stavke **bez dospeća** | **9** | Izvorni `NULL` ostao `NULL`; saldo **−310.678,54 RSD** |
| Otvorena stavka **bez centra** | **1** | „Neraspoređeno“; saldo **318.352,18 RSD**, uključena u ukupno |

Prvih 65 problema vidi se na ekranu sinhronizacije. Stavke bez dospeća radi uporedivosti
ostaju u razredu `0.1`, a zbirna kartica ih **prikazuje zasebno**. [P]

### Nalazi o kvalitetu izvornih podataka [P]

| # | Nalaz |
|---|---|
| 1 | `partneri` ima **13.607 redova i 13.588 različitih `sif_par`** — **sama šifra nije globalni ključ**. Nove veze moraju čuvati **pun finansijski identitet** (firma + grupa + šifra) |
| 2 | `ugovori.Partner` ima **13.406** partnera; `external_sif_par` **nije jedinstveno ograničeno** i ne sadrži firmu/grupu — **ne povezivati slepo samo po broju** |
| 3 | **32 kontakta, 13 napomena i 16 opomena** nemaju odgovarajućeg partnera; kod 32/13/3 od njih šifra je `NULL` ili necelobrojna. Čuvaju se za **ručno** povezivanje — **ne po sličnom nazivu** |
| 4 | `tabela_if` ima **7.424**, a `duplikati18` **6.105** redova **bez dospeća**. To je kvalitet **pomoćne istorije**, ne broj današnjih faktura bez dospeća |
| 5 | U `nalog_z` **nema dupliranih ključeva** firma/godina/vrsta/broj/stavka. Pregled metapodataka **nije pokazao indekse** na `nalog_z` i dvema istorijskim tabelama |
| 6 | Stare operativne tabele koriste **`float` za šifre i iznose**, a fakture u opomenama su **tekst**. Novi iznosi koriste `Decimal`, veze su FK. Original se **čuva** (`original_invoice_text`) |
| 7 | `tabela_if.saldo` je `numeric(38,2)`. Izmereni najveći iznos staje u `decimal(18,2)`, ali uvoz **proverava opseg** umesto prećutnog sužavanja — `DueDateEvidence.legacy_balance` je `decimal(38,2)` |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Sadržaj pogleda `baza`, `ispravke`, `dodela_baketa` | DDL |
| 2 | Da li „Nedospelo“ treba razdvojiti od „Nepoznato dospeće“ | **Q33** |
| 3 | **Datum gašenja nasleđene Naplate** | **Q34** |
| 4 | Da li sinhronizacija treba da bude zakazana | **[N]** |
| 5 | Da li pravna služba u celini prelazi u Potraživanja | **Q12** |
| 6 | **Definicija `v_duplikati` u preuzetom DDL-u je sumnjiva** — vidi niže | **[N]** |
| 7 | Tačno ponašanje granice „119 dana“ oko 29/30.04. i u prestupnoj godini | **[N]** |

### Zašto je definicija `v_duplikati` sumnjiva [Z]

U preuzetom DDL-u `ispravke` i `v_duplikati` imaju **doslovno isti tekst**. To ne može biti
tačno: pri prenosu `ispravke` je dalo **2.395**, a `v_duplikati` **2.580** redova.

Raniji plan Naplate opisuje `v_duplikati` sasvim drugačije — **IF iz svih godina spojen sa
`duplikati18`, uz `MAX` dospeća**. **Definiciju treba ponovo preuzeti iz baze.**

### Šta blokira gašenje nasleđene Naplate (Q34) [P]

| Prepreka | Opis |
|---|---|
| **Menice** | Izbor partnera čita SQL pogled `partneri` |
| **Ugovori** | Uvoz postojećeg registra čita **isti pogled** |
| **Migracije** | Istorijska migracija `0001` još ima zavisnost od migracije Naplate. `0005` je uklonila samu vezu iz aktivne šeme, ali potpuno uklanjanje aplikacije iz projekta traži **sređivanje istorije migracija** |

> **SQL poglede ne brisati dok ih koriste Menice i Ugovori.** [P]

### Tri evidencije tužbi nisu ista stvar [P]

| Izvor | Gde završava |
|---|---|
| Stare `tuzbe` | `CollectionNotice(kind="legacy_claim")` |
| Knjigovodstveni `v_tuzeni` | **Samo arhivirani izvor** (`SourceRow`) |
| Pravni `postupak` | `CollectionLegalCase` / `LegalCaseLink` |

> **Ne smeju se automatski spojiti po partneru.** [P]

> **[P] Finansijski identitet nije novi registar partnera** — čuva izvorni ključ i mapira ga
> na postojeći `ugovori.Partner`. **Ne prepisuje** APR-proverene ni ručno održavane podatke
> tog registra. Podudaranje po PIB/MB je **kandidat za proveru, ne automatski dokaz**.

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.8. Potraživanja](../obracuni/06-08-potrazivanja.md) | Svih 6 analiza |
| [4.8](../04-baza-podataka.md#48-potraživanja--potrazivanja) | 22 tabele |
| [11. Plan razvoja](../11-plan-razvoja.md) | Prelazak sa Naplate |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-18, P-35 |
