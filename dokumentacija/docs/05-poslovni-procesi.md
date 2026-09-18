# 5. Poslovni procesi

> **Za koga je ovo poglavlje:** poslovni korisnici i programeri.
> Ovde je opisano **kako posao teče kroz sistem od početka do kraja**, kroz više modula.
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 5.0. Spisak procesa

| # | Proces | Moduli | Pokreće ga |
|---|---|---|---|
| [1](#51-popravka-vozila--od-kvara-do-troška) | **Popravka vozila** — od kvara do troška | Flota → Nabavka → Flota | Vozač / garaža |
| [2](#52-službeno-putovanje--od-naloga-do-isplate) | **Službeno putovanje** — od naloga do isplate | Flota → Isplate → Banka | Zaposleni |
| [3](#53-zaduženje-vozila--od-preuzimanja-do-obračuna) | **Zaduženje vozila** — od preuzimanja do obračuna | Flota | Zaposleni |
| [4](#54-mesečni-obračun-mobilnih-telefona) | **Mesečni obračun mobilnih telefona** | Mobilni → Zarade | Administracija |
| [5](#55-mesečna-radna-lista-i-ocenjivanje) | **Mesečna radna lista i ocenjivanje** | Kadrovi → Zarade | Zaposleni |
| [6](#56-noćno-preuzimanje-podataka) | **Noćno preuzimanje podataka** | Svi | Sistem |
| [7](#57-naplata-potraživanja) | **Naplata potraživanja** | Potraživanja | Služba naplate |
| [8](#58-zaključenje-ugovora) | **Zaključenje ugovora** | Ugovori → Menice | Pravna služba |
| [9](#59-mesečno-praćenje-rezultata) | **Mesečno praćenje rezultata** | Finansije | Rukovodioci |

---

## 5.1. Popravka vozila — od kvara do troška

> **Najsloženiji proces u sistemu** — prolazi kroz tri modula i dva izvora podataka.

### Pokretački događaj

Vozač prijavljuje kvar na vozilu, ili dolazi red na servisni interval.

### Odgovorni korisnici

Garaža (prijava i radni nalog), služba nabavke (predmet i faktura),
služba voznog parka (kontrola troška).

### Potrebni ulazni podaci

| Podatak | Obavezno |
|---|---|
| Vozilo | Da |
| Kilometraža | Da |
| Opis kvara | Da |
| Vrsta intervencije (mali/veliki servis, popravka) | Da |
| Popravka van IMS-a | Da/Ne |

### Redosled aktivnosti [P]

```
 1. GARAŽA: prijava kvara              →  fleet_kvar,  broj PK-<id>/<godina>
 2. GARAŽA: stavke delova              →  fleet_kvarpart
 3. GARAŽA: štampa prijave i radnog naloga
 4. GARAŽA: trebovanje materijala      →  štampa
        │
        ├─── popravka u IMS garaži ────► materijal iz magacina
        │                                 dbo.fleet_trebovanja → fleet_requisition (01:45)
        │
        └─── popravka van IMS-a ───────► 5. zahtev za nabavku
 5. NABAVKA: predmet nabavke           →  nabavka_procurement_case
        broj ZNG-<centar>/<godina>-<broj>, vezan za kvar i vozilo
 6. NABAVKA: stavke predmeta           →  nabavka_procurement_item
 7. NABAVKA: statusi                   →  Nacrt → Podneto → U obradi → Čeka fakturu
 8. NABAVKA: narudžbenica (po potrebi) →  nabavka_purchase_order
 9. DOBAVLJAČ izdaje fakturu
10. SISTEM: preuzima EUF fakturu       →  nabavka_invoice (02:20)
11. NABAVKA: povezuje fakturu sa stavkom → nabavka_item_invoice_link
        status → Faktura povezana → Završeno
12. NABAVKA: označava šifru posla i vozilo na fakturi
13. SISTEM: knjiženje servisa          →  dbo.fleet_servisi → fleet_servicetransaction (03:15)
14. FLOTA: dopunjava kategoriju popravke i vezu sa vozilom
15. FLOTA: trošak ulazi u analitiku    →  trošak po kilometru
```

### Promene statusa [P]

| Objekat | Statusi |
|---|---|
| Predmet nabavke | `Nacrt → Podneto → U obradi → Čeka fakturu → Faktura povezana → Završeno` (ili `Otkazano`) |
| Knjiženje servisa | Nedovršeno (draft) → konačno |

### Tabele kroz koje podaci prolaze

`fleet_kvar` → `fleet_kvarpart` → `nabavka_procurement_case` →
`nabavka_procurement_item` → `nabavka_invoice` → `nabavka_item_invoice_link` →
`fleet_servicetransaction` / `fleet_requisition`

### Obračuni koji se izvršavaju

| Obračun | Kada |
|---|---|
| [B-01](obracuni/06-09-nabavka.md) Procenjena vrednost | Pri unosu stavki |
| [B-03](obracuni/06-09-nabavka.md) Ključ EUF fakture | Pri preuzimanju |
| [V-14](obracuni/06-05-flota-izvestaji.md) Održavanje vozila | Pri otvaranju detalja vozila |
| [V-10](obracuni/06-03-flota-troskovi.md) Neto trošak održavanja | U analitici |
| [V-07](obracuni/06-03-flota-troskovi.md) Trošak po kilometru | U analitici |

### Dokumenti koji nastaju

| Dokument | Gde |
|---|---|
| Prijava kvara | `/garaza/kvarovi/<id>/prijava/` |
| **Radni nalog** | `/garaza/kvarovi/<id>/radni-nalog/` |
| **Trebovanje materijala** | `/garaza/kvarovi/<id>/trebovanje/` |
| Zahtev za nabavku | `/nabavka/zahtevi/<id>/stampaj/` |
| Trebovanje materijala (nabavka) | `/nabavka/zahtevi/<id>/trebovanje-materijala/` |

### Kontrole [P]

| Kontrola | Gde |
|---|---|
| Broj predmeta traži **centar** organizacione jedinice | Pri čuvanju |
| Stavka mora imati **tačno jedan** izvor | `ProcurementItem.clean()` |
| Faktura dodeljena drugom vozilu **ne ulazi** u dokaze o održavanju | `vehicle_maintenance()` |
| Sukob kategorije ili datuma | Oznaka **„Proveriti kategoriju / datum“** |

### Moguće greške

| Greška | Posledica |
|---|---|
| Vozilo nema šifru posla | Predmet se **ne može numerisati** |
| Faktura ispravljena u izvoru | **Nastaje dvojnik** — [P-39](10-poznati-problemi.md) |
| UF faktura nestala iz izvora | **Veza tiho nestaje** — [P-37](10-poznati-problemi.md) |
| Knjiženje servisa bez vozila | Ostaje u „nedovršeno“, trošak nije na vozilu |

### Završni rezultat

Trošak popravke je **pripisan vozilu i šifri posla**, vidi se na detalju vozila i
ulazi u trošak po kilometru.

### Podaci za knjiženje

> **[N] Q3:** knjiženje nastaje u nasleđenom ERP-u; sistem ga **samo preuzima**.
> Nije potvrđeno da li se neki podatak iz sistema prenosi u knjiženje.

---

## 5.2. Službeno putovanje — od naloga do isplate

### Pokretački događaj

Potreba za službenim putovanjem.

### Odgovorni korisnici

Sekretarijat (nalog), blagajna (virman), zaposleni (pravdanje).

### Redosled aktivnosti [P]

```
 1. SEKRETARIJAT: putni nalog          →  fleet_putninalog
        broj <centar>/<godina>-<redni broj>
        zaposleni, mesto, zadatak, dani, vozilo, AKONTACIJA, valuta, dnevnica
 2. SEKRETARIJAT: štampa naloga        →  obrazac za zaposlenog
        (+ prilog za inostranstvo ako treba)
 3. BLAGAJNA: bira naloge za isplatu   →  /isplate/
 4. BLAGAJNA: zadaje datum virmana
 5. SISTEM: kontrole (9 provera)       →  I-02
 6. SISTEM: datoteka virmana           →  180 znakova po redu, cp1250
        upisuje: virman_generated, _at, _by
 7. BLAGAJNA: učitava datoteku u elektronsko bankarstvo
 8. BANKA: izvršava plaćanja           →  zaposleni prima akontaciju
 9. ZAPOSLENI: putuje i pravda nalog
10. SEKRETARIJAT: označava „Opravdan“
11. SISTEM: puni „Isplaćeno“           →  dbo.fleet_zatvoren_putni (12:30)
```

### Promene statusa [P]

| Oznaka | Značenje |
|---|---|
| `virman_generated` | Virman je napravljen |
| `opravdan` | Nalog je pravdan |
| `storniran` | Nalog je storniran — **ne ulazi u virman** |

### Obračuni

| Obračun | Napomena |
|---|---|
| [I-02](obracuni/06-10-isplate.md) Kontrole naloga | Devet provera, sve greške zajedno |
| [I-01](obracuni/06-10-isplate.md) Generisanje virmana | Iznos u parama, poziv na broj |

### Dokumenti koji nastaju

| Dokument | Gde |
|---|---|
| Putni nalog | `/putni-nalozi/<id>/print/` |
| Prilog za inostranstvo | `/putni-nalozi/<id>/prilog-inostranstvo/` |
| **Datoteka virmana** | Preuzimanje sa `/isplate/` |

### Kontrole [P]

| Kontrola | Poruka |
|---|---|
| Nalog nije storniran | *„nalog je storniran“* |
| Virman nije već rađen | *„virman je vec odradjen“* |
| **Valuta je RSD** | *„valuta mora biti RSD“* |
| **Zaposleni je iz IMS-a** | *„nalog nema IMS zaposlenog“* |
| **Račun ima 18 cifara** | *„racun mora imati 18 cifara“* |
| Iznos veći od nule | *„Iznos mora biti veci od nule“* |

### Moguće greške

| Greška | Posledica |
|---|---|
| Nema početnog broja za centar i godinu | Nalog se **ne može otvoriti** |
| Zaposleni nema partiju | Nalog **ne ulazi** u virman |
| **Ime duže od 35 znakova** | **Skraćuje se bez upozorenja** — [P-33](10-poznati-problemi.md) |
| **Mesto duže od 10 znakova** | Skraćuje se — „Novi Beograd“ → „Novi Beogr“ |
| Nema opštine boravka | Upisuje se **„Beograd“** |

### Podaci za knjiženje

| Ko preuzima | Šta | Odakle |
|---|---|---|
| **Banka** | Datoteka virmana | `/isplate/` |
| Knjigovodstvo | **[N] Nije potvrđeno** | — |

### Završni rezultat

Zaposleni je primio akontaciju, nalog je označen kao isplaćen i pravdan.

---

## 5.3. Zaduženje vozila — od preuzimanja do obračuna

### Pokretački događaj

Zaposleni preuzima vozilo.

### Redosled aktivnosti [P]

```
 1. ZAPOSLENI: otvara zaduženje        →  fleet_vehicletravelorder
        broj PN-<redni broj>, POČETNA KILOMETRAŽA
 2. SISTEM: automatski ZATVARA ranija otvorena zaduženja tog vozila
        njihova krajnja kilometraža = početna kilometraža novog naloga
 3. ZAPOSLENI: koristi vozilo, toči gorivo
 4. SISTEM: preuzima transakcije goriva (04:20 / 05:10 / 06:10)
 5. GARAŽA ili ZAPOSLENI: zatvara zaduženje  →  KRAJNJA KILOMETRAŽA
 6. SISTEM: obračun goriva             →  V-23
 7. ZAPOSLENI: štampa obračun
```

### Obračuni

| Obračun | Formula |
|---|---|
| [V-23](obracuni/06-02-flota-gorivo.md) Obračun goriva | `litri / pređeni put × 100` |
| [V-13](obracuni/06-05-flota-izvestaji.md) Kilometraža | Očitavanja iz zaduženja ulaze u vremensku liniju |

### Kontrole i moguće greške

| Slučaj | Ponašanje |
|---|---|
| Nalog nije zatvoren | Obračun ide **do današnjeg dana**, menja se svakog dana |
| Vozilo promenilo tablice | **Transakcije sa stare tablice mogu nedostajati** |
| Više otvorenih zaduženja | Ista transakcija ulazi u **oba** obračuna |
| Preko 60 transakcija | **Štampa se samo prvih 60** |
| Zatvoreno zaduženje | Menja ga **samo superuser** |

### Završni rezultat

Poznato je ko je koristio vozilo, koliko je prešao i koliko goriva potrošio.

---

## 5.4. Mesečni obračun mobilnih telefona

### Pokretački događaj

Stigao je mesečni račun operatera.

### Odgovorni korisnik

Administracija.

### Redosled aktivnosti [P]

```
 1. OPERATER: dostavlja 4 Excel datoteke
 2. ADMINISTRACIJA: uvozi paketе i korisnike    →  /mobilni/import/
 3. ADMINISTRACIJA: uvozi DODELE za mesec       →  uz godinu i mesec
 4. ADMINISTRACIJA: uvozi POTROŠNJU za mesec    →  uz godinu i mesec
 5. SISTEM: automatski povezuje brojeve sa zaposlenima
 6. ADMINISTRACIJA: proverava nepovezane i rešava ih ručno
 7. ADMINISTRACIJA: održava izuzetke od parkinga
 8. SISTEM: računa obustavu                     →  M-01
 9. ADMINISTRACIJA: pregleda izveštaj obustava
10. ADMINISTRACIJA: preuzima CSV                →  obracunski-mesec.csv
11. OBRAČUN ZARADA: preuzima iznose             →  [N] način nije potvrđen
```

### Obračun [P]

> **obustava = osnovica za PDV − neto iznos paketa + parking + NZRD**

Potvrđeno kao ispravno (naručilac, 18.09.2026.).

### Kontrole

| Kontrola | Gde |
|---|---|
| Jedna dodela i jedna potrošnja po broju i mesecu | Kontrola u bazi |
| Dnevnik uvoza sa brojačima | `mobilni_mobileimportlog` |
| **Pregled pre slanja u zarade** | Izveštaj „Obustave zaposlenih“ |

### Moguće greške

| Greška | Posledica |
|---|---|
| **Dodele za mesec nisu uvezene** | **Cela potrošnja tiho ispada iz obračuna** — [P-31](10-poznati-problemi.md) |
| Paket bez neto iznosa | Obustava prazna, red se ne izvozi |
| Negativna obustava | **Izvozi se** — [Q29](obracuni/06-07-mobilni.md) |
| Broj nije povezan sa zaposlenim | Ide u izveštaj „Nezaposleni“, **ne u zarade** |
| Zaposleni otišao usred meseca | **Nije ni u jednom pojedinačnom izveštaju** — [P-32](10-poznati-problemi.md) |

### Podaci za knjiženje

| Ko preuzima | Šta | Odakle | Oblik |
|---|---|---|---|
| **Obračun zarada** | Šifra radnika i iznos | `/mobilni/potrosnja/obracunski-mesec.csv` | `Godina;Mesec;Šifra;Iznos` |

> **[N] Q3:** nije potvrđeno da li se CSV uvozi ili iznosi prepisuju ručno,
> ni koja konta se koriste.

### Završni rezultat

Iznosi obustava su spremni za obračun zarada.

> **[Z] Rizik:** obustava se **nigde ne čuva**. Ako se posle prenosa promeni paket ili
> dodela, ekran će za isti mesec pokazati **drugi iznos**. Vidi [P-31](10-poznati-problemi.md).

---

## 5.5. Mesečna radna lista i ocenjivanje

### Pokretački događaj

Kraj meseca.

### Redosled aktivnosti [P]

```
 A) RADNA LISTA
 1. ZAPOSLENI: otvara svoju radnu listu        →  /hr/radna-lista/
 2. SISTEM: prikazuje sate iz prolazaka        →  K-01 (kao KONTROLA, ne prepisuje se)
        + putne naloge i bolovanja po danima
 3. ZAPOSLENI: unosi sate PO ŠIFRAMA POSLA
 4. ZAPOSLENI: unosi topli obrok i terenski dodatak
 5. ZAPOSLENI: „Predaj i štampaj“              →  status Predato

 B) OCENJIVANJE
 6. RUKOVODILAC: otvara obrazac                →  potpisan snimak, važi 24 h
 7. RUKOVODILAC: bira bodove 0–4 po šest merila
 8. SISTEM: stimulacija = zbir koeficijenata
        LIČNI KOEFICIJENT = 1 + stimulacija    →  K-08
 9. RUKOVODILAC: potvrđuje                     →  saglasnost 1/3
10. DIREKTOR CENTRA: potvrđuje ili koriguje    →  saglasnost 2/3
11. GENERALNI DIREKTOR: potvrđuje              →  saglasnost 3/3
12. Štampa obrasca sa tri potpisa
13. OBRAČUN ZARADA: preuzima koeficijent       →  [N] način nije potvrđen
```

### Obračuni

| Obračun | Formula |
|---|---|
| [K-01](obracuni/06-06-kadrovi.md) Dnevni sati | Uparivanje prolazaka; službeni izlazak **do 16:00** |
| [K-04/K-05](obracuni/06-06-kadrovi.md) Sati radne liste | Zbir 31 kolone |
| [K-08](obracuni/06-06-kadrovi.md) **Lični koeficijent** | **`K4 = 1 + zbir koeficijenata`** |
| [K-09](obracuni/06-06-kadrovi.md) Saglasnost | Tri nivoa, korekcija uz obrazloženje |

### Kontrole [P]

| Kontrola | Ponašanje |
|---|---|
| Obrazac stariji od 24 h | Odbija se |
| Dvostruko slanje | Vraća se postojeća ocena |
| Bodovi van sačuvane skale | Odbija se |
| **Preskakanje nivoa** | Odbija se |
| Korekcija izvan granica obrasca | Odbija se |
| **Korekcija bez obrazloženja** | Odbija se |
| Novija revizija | Blokira potvrdu starije |

### Moguće greške

| Greška | Posledica |
|---|---|
| Zaboravljen ulaz ili izlaz | Sati manji od stvarnih, uz prijavljen problem |
| **Smena preko ponoći** | **Ne uparuje se uopšte** — [P-28](10-poznati-problemi.md) |
| Izvor prolazaka nedostupan | Radna lista radi, sati prikazani kao „—“ |
| Pogrešna ocena | Ispravka je **nova revizija** |

### Završni rezultat

Radna lista je predata, ocena potvrđena u tri nivoa, koeficijent spreman za zaradu.

---

## 5.6. Noćno preuzimanje podataka

### Pokretački događaj

Raspored — Celery Beat.

### Redosled aktivnosti [P]

```
 01:00  Dozvole            →  nove rute postaju vidljive
 01:10  Zaposleni          →  fleet_employee
 01:20  Otpis vozila       →  fleet_vehicle.otpis
 01:30  Šifre poslova      →  fleet_organizationalunit, fleet_jobcode
 01:45  Trebovanja         →  fleet_requisition
 02:00  Polise             →  fleet_policy
 02:20  EUF fakture        →  nabavka_invoice
 02:45  UF stavke          →  nabavka_euf_item_snapshot + UF fakture
 03:15  Servisi            →  fleet_servicetransaction
 03:35  DDOR osiguranja    →  fleet_draftinsurance
 03:50  Finansije          →  finansije_ledgerentry  (uz KONTROLNE ZBIROVE)
 04:20  Gorivo NIS         →  Selenium → TransactionNIS + FuelConsumption
 05:10  Gorivo OMV putn.   →  Selenium → TransactionOMV + čišćenje duplikata
 06:10  Gorivo OMV teretna →  isto
 07:10  Roba               →  nabavka_goods_snapshot
```

### Kontrole [P]

| Kontrola | Gde |
|---|---|
| **Zaključavanje** | Redis (4 h / 90 min / 60 min) ili SQL `sp_getapplock` |
| **Kontrolni zbirovi** | Finansije — broj redova i iznosi po godini i kontu |
| **Prazan izvor ne briše podatke** | Finansije, Potraživanja |
| Nestali zapis | Označava se neaktivnim, **ne briše se** |
| Istorija | `TaskHistory` za svaki posao |

### Moguće greške

| Greška | Posledica | Šta uraditi |
|---|---|---|
| Selenium ne uspeva | Nema novih podataka o gorivu | **Uvesti datoteku ručno** |
| Povezani server nedostupan | Finansije ne rade | Sačekati, pa pokrenuti ručno |
| Kontrolni zbirovi se ne slažu | **Ništa se ne objavljuje** | Ponoviti; proveriti izvor |
| Redis nedostupan | Poslovi rade **bez zaštite** | [P-16](10-poznati-problemi.md) |
| Selenium blokira ostale poslove | Kasne sve sinhronizacije | [P-15](10-poznati-problemi.md) |

### Završni rezultat

Ujutru korisnik zatiče osvežene podatke. Provera: `/administracija/task-history/`.

---

## 5.7. Naplata potraživanja

### Pokretački događaj

Potreba za pregledom dugovanja ili istekao rok plaćanja.

### Redosled aktivnosti [P]

```
 1. SLUŽBA NAPLATE: pokreće sinhronizaciju     →  /potrazivanja/sinhronizacija/
 2. SISTEM: preuzima ceo izvor                 →  nepromenljiv snimak izvora
 3. SISTEM: partneri, knjiženja, fakture
 4. SISTEM: pozicije i starosni razredi        →  PT-01
 5. SISTEM: ŠEST KONTROLA                      →  PT-04
        razlika → NIŠTA SE NE OBJAVLJUJE
 6. SISTEM: objavljuje snimak stanja           →  PT-03
 7. SLUŽBA NAPLATE: pregleda dugovanja po starosti
 8. SLUŽBA NAPLATE: telefonski poziv           →  CollectionActivity
 9. SLUŽBA NAPLATE: opomena / pozivno pismo    →  CollectionNotice + stavke
10. SLUŽBA NAPLATE: štampa dokument
11. PRAVNA SLUŽBA: pravni postupak             →  CollectionLegalCase
12. PRAVNA SLUŽBA: promene u postupku          →  CollectionLegalEvent
```

### Obračuni

| Obračun | Napomena |
|---|---|
| [PT-01](obracuni/06-08-potrazivanja.md) Starosni razredi | Sedam baketa |
| [PT-02](obracuni/06-08-potrazivanja.md) Saldo | Kontrola i u bazi |
| [PT-04](obracuni/06-08-potrazivanja.md) **Šest kontrola** | Svaka razlika prekida objavu |
| [PT-05](obracuni/06-08-potrazivanja.md) Saldo po šiframa posla | Ide u Finansije |

### Moguće greške

| Greška | Posledica |
|---|---|
| Kontrolni zbirovi se ne slažu | **Snimak se ne objavljuje**, prethodni ostaje |
| Prazan izvor | Prenos se prekida, podaci ostaju |
| Partner bez šifarnika | Upisuje se neaktivan, uz zabeležen problem |
| **Dug bez datuma dospeća** | Prikazuje se kao **„Nedospelo“** — [P-35](10-poznati-problemi.md) |

### Završni rezultat

Objavljen snimak stanja na određeni datum; opomene i postupci evidentirani.
Finansije vide isti saldo na kartici posla.

---

## 5.8. Zaključenje ugovora

### Redosled aktivnosti [P]

```
 1. Partner podnosi zahtev            →  ugovori_business_request
 2. Priprema se ponuda                →  ugovori_offer (naša ili data nama)
 3. Ponuda prihvaćena                 →  status Prihvacena
 4. PRAVNA: zaključuje ugovor         →  ugovori_contract (kind = MAIN)
 5. PRAVNA: dodaje stranke            →  ugovori_contract_party
 6. PRAVNA: prilaže dokumenta         →  ugovori_contract_document
 7. Sredstva obezbeđenja:
        menica    →  ugovori_contract_menica_link
        garancija →  ugovori_contract_guarantee
 8. Tokom trajanja: aneksi            →  ugovori_contract (kind = ANNEX)
 9. Ugovor se koristi u:
        Nabavci   (osnovni i kupovni ugovor)
        Floti     (lizing, finansiranje)
        Mobilnom  (paket)
10. Istek ugovora → status Istekao; garancije i menice se vraćaju
```

### Kontrole [P]

| Kontrola | Poruka |
|---|---|
| Aneks bez glavnog ugovora | *„Aneks mora imati glavni ugovor.“* |
| Glavni ugovor sa nadređenim | *„Glavni ugovor ne sme imati nadređeni ugovor.“* |
| „Važi do“ pre „Važi od“ | Odbija se |
| Veza sa menicom: ni jedna ni obe | *„Izaberite tacno jednu menicu.“* |
| Brisanje povezane menice | **Zabranjeno** |

### Moguće greške

| Greška | Posledica |
|---|---|
| Partner neaktivan u APR-u | Upozorenje u evidenciji partnera |
| Oznake „ima menice/garancije“ netačne | **Nema provere** — [Q40](obracuni/06-11-ugovori-i-menice.md) |
| Menica sa jedinicom „PROCENAT“ | Iznos **nije novčani** |

### Završni rezultat

Ugovor sa strankama, dokumentima i sredstvima obezbeđenja, spreman za upotrebu u
drugim modulima.

---

## 5.9. Mesečno praćenje rezultata

### Pokretački događaj

Kraj meseca ili potreba za uvidom.

### Redosled aktivnosti [P]

```
 1. SISTEM: sinhronizuje knjiženja (svaki sat u :20, dnevno 03:50)
 2. RUKOVODILAC: otvara Finansijski pregled  →  /finansije/
        prihodi, rashodi, rezultat po centrima i poslovima
 3. RUKOVODILAC: zbirna tabela šifara posla  →  11 kolona
        P, R, P−R, ZT, P−R−ZT, priliv, odliv, neto gotovina
 4. RUKOVODILAC: klik na šifru → kartica posla
 5. Osam tabova: fakture, interne fakture, rashodi, vozila,
        zaduženja, zaposleni, putni nalozi, POTRAŽIVANJA
 6. Izvoz u Excel po potrebi
```

### Obračuni

Svih [18 obračuna Finansija](obracuni/06-01-finansije.md).

### Kontrole [P]

| Kontrola | Kako |
|---|---|
| Rezultat reda | `prihod + prikazani rashod + prikazani ZT` |
| Neto gotovina | `prikazani priliv + prikazani odliv` |
| Potpunost sinhronizacije | Ekran sinhronizacije — kontrolni zbirovi |
| **Nepotpun obračun** | Zvezdica i objašnjenje — **„nepotpuno“ nije „nula“** |

### Moguće greške u tumačenju [P]

| Zabluda | Ispravno |
|---|---|
| „Rashod je negativan, pa ga treba oduzeti“ | **Već je prikazan negativno** — samo sabrati |
| „Godišnji ZT = zbir mesečnih“ | **Nije** — koeficijent je prosek |
| „Tok gotovine = promet računa“ | **Nije** — obračun po pravilima procedure |
| „Zbir klasa 5 i 6 mora biti nula“ | Zatvaranja su **namerno izuzeta** |
| „Zbirna tabela = detalj“ | Detalj otvara **poslednji mesec perioda** |

### Završni rezultat

Rukovodilac zna rezultat svog posla ili centra, i vidi sve evidencije koje ga čine.

---

## 5.10. Šta nijedan proces ne obuhvata

| Nedostaje | Napomena |
|---|---|
| **Odobravanje** predmeta nabavke pre slanja | Postoje statusi, ali ne i tok odobravanja |
| **Odobravanje** radne liste | Status „Odobreno“ postoji, ali se **nigde ne postavlja** — [Q26](obracuni/06-06-kadrovi.md) |
| **Potvrda isplate** po virmanu | [Q32](obracuni/06-10-isplate.md) |
| **Povratna veza ka knjiženju** | Sistem čita knjiženja; ne knjiži |
| **Obaveštenja** (e-pošta, poruke) | Nema podešenog slanja |
| **Upozorenje o dospelom servisu** | `service_interval` se **ne koristi** — [Q23](obracuni/06-05-flota-izvestaji.md) |

---

## 5.11. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Šta radi pojedini modul? | [3. Moduli](03-moduli.md) |
| Kako se računa iznos u procesu? | [6. Analize i obračuni](06-analize-i-obracuni.md) |
| Odakle dolaze podaci? | [7. Integracije](07-integracije.md) |
| Šta može poći naopako? | [10. Poznati problemi](10-poznati-problemi.md) |
