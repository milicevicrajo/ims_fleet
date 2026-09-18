# 3.4. Nabavka

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Nabavka** |
| Tehnički naziv | Django aplikacija `nabavka` |
| Adresa | `/nabavka/` |
| Bočni meni | `sidebar_nabavka.html` |

---

## 2. Poslovna namena

Vodi **predmet nabavke od podnošenja zahteva do povezane fakture**, i time odgovara na
pitanje: **šta je traženo, šta je nabavljeno, po kojoj fakturi i na čiji teret.**

Uz to vodi **plan javnih nabavki sa verzijama**, da se vidi šta je i kada menjano.

---

## 3. Korisnici modula

| Korisnik | Šta radi | Uloga |
|---|---|---|
| **Služba nabavke** | Obrađuje predmete, povezuje fakture, izdaje narudžbenice | `nabavka` |
| **Podnosioci zahteva** | Podnose zahtev sa stavkama i štampaju ga | `zahtev` |
| **Garaža** | Podnosi garažne zahteve vezane za kvar i vozilo | `zahtev` |
| **Uprava** | Izveštaji i plan javnih nabavki | `uprava` |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Predmeti nabavke** | Zahtev za nabavku, zahtev za uslugu, predlog za opremu; stavke; statusi; štampa |
| **Garažni predmeti** | Zahtevi vezani za kvar i vozilo, sa vrstom intervencije |
| **EUF fakture** | Snimak preuzetih elektronskih ulaznih faktura, sa operativnim oznakama |
| **UF stavke i fakture** | Snimak stavki ulaznih faktura i izvedene fakture |
| **Roba** | Snimak robnog prometa |
| **Povezivanje** | Stavka ↔ izvor; predmet ↔ faktura; faktura ↔ šifra posla; predmet ↔ ugovor |
| **Plan javnih nabavki** | Uvoz Excel plana, verzije i razlike |
| **Narudžbenice** | Broj, datum, dobavljač, ugovor, status, iznos |
| **Izveštaji i alarmi** | Brojači po statusu i tipu, zbirovi, predmeti koji čekaju fakturu |
| **Ponavljanje zahteva** | Kopija predmeta sa stavkama, u statusu nacrta i sa novim brojem |

### Statusi predmeta [P]

```
 Nacrt ──► Podneto ──► U obradi ──► Čeka fakturu ──► Faktura povezana ──► Završeno
                                                                    └──► Otkazano
```

Svaka promena statusa se beleži u `nabavka_status_log` sa komentarom i korisnikom. [P]

> **[P] Redosled nije nametnut.** Obrazac za promenu statusa nudi **sve** statuse i prelaz
> se **ne proverava** — iz bilo kog statusa može se preći u bilo koji. Dijagram iznad
> prikazuje **uobičajen tok**, ne pravilo koje aplikacija sprovodi.

**Jedini automatski prelaz [P]:** kada se stavka **novom** vezom poveže sa EUF fakturom, a
predmet je u statusu **`Čeka fakturu`**, status prelazi u **`Faktura povezana`**.

### Ponavljanje zahteva [P]

Dugme „Ponovi“ pravi **novi predmet u statusu nacrta**, sa novim automatskim brojem. Sve u
jednoj transakciji.

| Šta se kopira | Šta se **ne** kopira |
|---|---|
| Tip, naslov, opis, garažna oznaka, šifra posla, dobavljač, ugovor, vozilo, vrsta intervencije, procenjena vrednost, valuta, napomena | **Veze stavki sa izvorima** (EUF/UF/roba) |
| Stavke: naziv, jedinica mere, količina, procenjena jedinična cena, napomena | `responsible` i `created_by` — postaju **trenutni korisnik** |
| | `needed_by` — postavlja se na **današnji datum** |

U status log novog predmeta upisuje se komentar *„Ponovljen zahtev {broj izvornog
predmeta}.“*, a korisnik dobija poruku *„Kreiran je novi zahtev {broj} sa kopiranim
stavkama.“*

### Format broja predmeta [P]

> `<prefiks>-<centar>/<godina>-<redni broj>`

| Tip | Prefiks | Garažni prefiks |
|---|---|---|
| Zahtev za nabavku | `ZN` | **`ZNG`** |
| Zahtev za uslugu | `ZU` | **`ZUG`** |
| Predlog za opremu | `PLN` | — |

Primer: `ZNG-43/2026-7`. Bez centra u organizacionoj jedinici broj se **ne može dodeliti**.

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| Kontrolna tabla | `/nabavka/` |
| **Zahtevi (predmeti)** | `/nabavka/zahtevi/` |
| Novi zahtev | `/nabavka/zahtevi/novi/` |
| Detalj predmeta | `/nabavka/zahtevi/<id>/` |
| **Štampa zahteva** | `/nabavka/zahtevi/<id>/stampaj/` |
| **Trebovanje materijala** | `/nabavka/zahtevi/<id>/trebovanje-materijala/` |
| Ponovi zahtev | `/nabavka/zahtevi/<id>/ponovi/` |
| Povezivanje sa izvorom | `/nabavka/zahtevi/<id>/stavke/izvor/` |
| **EUF fakture** | `/nabavka/euf-fakture/` |
| Detalj EUF fakture | `/nabavka/euf-fakture/<id>/` |
| Vraćene šifre posla | `/nabavka/euf-fakture/<id>/vraceno-sifre/` |
| **UF stavke** | `/nabavka/uf-stavke/` |
| Detalj UF fakture | `/nabavka/uf-stavke/<id>/` |
| **Roba** | `/nabavka/roba/` |
| Kupovni ugovori | `/nabavka/kupovni-ugovori/` |
| **Plan javnih nabavki** | `/nabavka/javne-nabavke/` |
| Uvoz plana | `/nabavka/javne-nabavke/uvoz/` |
| Narudžbenice | `/nabavka/narudzbenice/` |
| Izveštaji | `/nabavka/izvestaji/` |
| Provera šifre posla partnera | `/nabavka/izvestaji/provera-sifre-posla-partnera/` |
| **Alarmi** | `/nabavka/alarmi/` |

### Kontrolna tabla — šta stvarno prikazuje [P]

| Pokazatelj | Pravilo |
|---|---|
| Ukupno predmeta | Svi |
| **Otvoreni predmeti** | Svi **osim** `Završeno` i `Otkazano` |
| Čekaju fakturu | Status `Čeka fakturu` |
| Garažni predmeti | `is_garage = True` |
| Poslednji kreirani | **Poslednjih 8** po `-created_at` |

> **[P]** Pokazatelja „predmeti kojima je istekao rok“ **nema** — nad poljem `needed_by`
> ne postoji nijedan izračun. Raniji dokument ga je navodio; to nikad nije bilo u kodu ili
> je uklonjeno.

### Detalj EUF fakture — šta se vidi i dopunjuje [P]

| Prikaz | Sadržaj |
|---|---|
| Povezane stavke zahteva | Kroz `nabavka_item_invoice_link` |
| Povezani kupovni ugovori | Ugovori sa šifrom tipa koja počinje sa `KUP` |
| Povezane dodatne šifre posla | Dodate ručno |
| **Interna dopuna** | `is_garage`, `vehicle`, `work_type`, `goes_to_warehouse`, `internal_note` |

Naziv partnera na spiskovima skraćuje se na **50 znakova**, a pun naziv se vidi kao
`title` atribut (na prelazak mišem). [P]

### Kupovni ugovori — nabavni pogled na modul Ugovori [P]

Lista **ne duplira ugovore** — čita ih iz aplikacije `ugovori`.

| Osobina | Pravilo |
|---|---|
| **Šta je kupovni ugovor** | `contract_type__code` počinje sa **`KUP`** — to je jedino pravilo |
| Broj povezanih faktura | `Count("nabavka_invoice_links__invoice", distinct=True)` |
| Ukupna povezana vrednost | `Sum("nabavka_invoice_links__invoice__amount")` |
| Pretraga | Broj ugovora, naslov, predmet, **broj ugovora druge strane** |
| Partner | Naziv, PIB, matični broj i `external_sif_par` (kad je unos broj) |
| Ostali filteri | Vrsta, status, godina (`contract_date__year`) |

Isti `KUP` filter važi i pri povezivanju fakture sa ugovorom, uz isključivanje već
povezanih. [P]

> **[Z] Rizik u zbiru:** „ukupna povezana vrednost faktura“ koristi `Sum` preko veze ka
> više redova, **bez `distinct`** — isti obrazac koji je bio uzrok
> [P-36](../10-poznati-problemi.md#p-36--ukupan-iznos-faktura-na-izveštaju-nabavke-je-višestruko-uvećan).
> Ovde faktura može biti povezana sa jednim ugovorom više puta preko različitih veza;
> **nije provereno da li se to u praksi dešava.**

---

## 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| Naziv, opis, tip predmeta, datum zahteva | Podnosilac |
| Šifra posla (OJ), vozilo, vrsta intervencije | Podnosilac |
| **Stavke: naziv, JM, količina, procenjena cena** | Podnosilac |
| Procenjena vrednost predmeta i valuta | Podnosilac |
| Dobavljač, osnovni ugovor, odgovorno lice | Služba nabavke |
| Promena statusa sa komentarom | Služba nabavke |
| **Povezivanje stavke sa EUF, UF ili robom** | Služba nabavke |
| Oznake na EUF fakturi: šifra posla, vozilo, garaža, ide u magacin, vraćeno, napomena | Služba nabavke |
| Narudžbenica | Služba nabavke |
| Excel plan javnih nabavki | Služba nabavke |

---

## 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada | Tabela |
|---|---|---|---|
| **EUF fakture** | `dbo.nbv_preuzete_EUF` | Dnevno 02:20 | `nabavka_invoice` |
| **UF stavke** | `dbo.nbv_EUF_stavke` | Dnevno 02:45 | `nabavka_euf_item_snapshot` |
| UF fakture | Izvedeno grupisanjem stavki | Uz stavke | `nabavka_uf_invoice_snapshot` |
| **Roba** | `dbo.nbv_roba` | Dnevno 07:10 | `nabavka_goods_snapshot` |
| Šifra posla partnera | `dbo.nbv_sif_pos_par` | Pri otvaranju izveštaja | — |

### Osnovna šifra posla EUF fakture — pun postupak [P]

**Osnovna šifra posla se ne bira ručno** — polje `job_code` uopšte nije u obrascu. Postavlja
se **samo automatski**, po tri grane:

| Uslov | Šta se upisuje |
|---|---|
| Faktura je **garažna**, vozilo **nepromenjeno** i već postoji `job_code` sa `job_code_source = "vehicle_snapshot"` | **Ništa** — snimak se zadržava |
| Faktura je **garažna** i izabrano je vozilo | `JobCode` tog vozila sa `organizational_unit__isnull=False`, sortirano `-assigned_date, -pk`, **prvi**. Upisuju se `job_code`, `job_code_source="vehicle_snapshot"` i `vehicle_job_code_assigned_date` |
| Faktura **nije garažna** ili **nema vozila** | `job_code = None`, `job_code_source = ""`, `vehicle_job_code_assigned_date = None` — **postojeća osnovna šifra se briše** |

Na ekranu polje nosi natpis **„Sifra posla automobila - snapshot“**.

> **[P] Zašto snimak:** faktura pamti šifru posla automobila **u trenutku povezivanja**.
> Ako se šifra posla automobila kasnije promeni, **faktura se ne menja**. Dodatne šifre
> posla dodaju se **ručno** i **ne menjaju** ovaj snimak.

### Šta ponovno preuzimanje sme da promeni [P]

Pri ponovnom povlačenju iz izvora ažuriraju se **samo**: `invoice_number`, `invoice_date`,
`invoice_date_raw`, `supplier_name`, `amount`, `center`, `warehouse`, `registration`,
`synced_at`, `updated_at`.

> **Interni podaci koje je korisnik dopunio se ne diraju:** `job_code`, `job_code_source`,
> `vehicle_job_code_assigned_date`, `is_garage`, `vehicle`, `work_type`,
> `goes_to_warehouse`, `is_returned`, `internal_note`.

**Podrazumevane vrednosti nove EUF fakture [P]:**

| Polje | Podrazumevano |
|---|---|
| `is_returned` | `False` — nova faktura **nije vraćena** dok korisnik to ne označi |
| `goes_to_warehouse` | **`True` ako kolona `magacin` u izvoru nije prazna**; postavlja se samo pri prvom kreiranju i kasnije se ne prepisuje |

---

## 8. Tabele i kolone

### Statusi narudžbenice [P]

`Nacrt` → `Poslato` → `Potvrđeno` → `Zatvoreno`, uz `Otkazano`. Podrazumevano `Nacrt`.

| Polje | Pravilo |
|---|---|
| `order_number` | **Jedinstven** |
| `order_date` | Podrazumevano **danas** |
| `currency` | Podrazumevano **RSD** |
| `supplier`, `contract` | `PROTECT` — ne mogu se obrisati dok postoji narudžbenica |

### Kako se prikazuje povezani izvor stavke [P]

`ProcurementItem.source_reference_label` daje tri oblika:

```text
EUF:  EUF-2026-00123
UF:   UF-001/2026
Roba: ART-001 - Filter ulja (Faktura: TEST-UF-001/2026)
```

Kod robe, ako nema šifre artikla ili veznog dokumenta, na to mesto ide `/`.


Detaljno: [4.7. Nabavka](../04-baza-podataka.md#47-nabavka--nabavka). **13 tabela.**

| Tabela | Uloga |
|---|---|
| `nabavka_procurement_case` | Predmet nabavke |
| `nabavka_procurement_item` | Stavka, sa vezom ka **tačno jednom** izvoru |
| `nabavka_invoice` | EUF faktura + operativne oznake |
| `nabavka_euf_item_snapshot` | UF stavka |
| `nabavka_uf_invoice_snapshot` | UF faktura (izvedena) |
| `nabavka_goods_snapshot` | Roba |
| `nabavka_invoice_link` | Predmet ↔ EUF ključ |
| `nabavka_item_invoice_link` | Stavka ↔ faktura (jedan na jedan) |
| `nabavka_invoice_job_code_link` | Faktura ↔ šifra posla (osnovna / dodatna, vraćeno) |
| `nabavka_contract_link`, `nabavka_invoice_contract_link` | Veze sa ugovorima |
| `nabavka_public_procurement_plan_version`, `…_item` | Plan javnih nabavki |
| `nabavka_purchase_order` | Narudžbenica |
| `nabavka_status_log` | Promene statusa |

---

## 9. SQL pogledi

| Pogled | Namena | Status |
|---|---|---|
| `dbo.nbv_preuzete_EUF` | EUF fakture | Kolone poznate: `datum, naziv_partnera, broj_fakutre, iznos, centar, magacin, registracija` |
| `dbo.nbv_EUF_stavke` | Stavke ulaznih faktura | **[N]** Sadržaj nije potvrđen |
| `dbo.nbv_roba` | Robni promet | **[N]** |
| `dbo.nbv_sif_pos_par` | Partner ↔ šifra posla | Kolone: `sif_par, naz_par, sif_pos` |

> **[P] Napomena:** kolona u izvoru se zove **`broj_fakutre`** — sa greškom u kucanju.
> Ne ispravljati u kodu; tako je u pogledu.

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`nabavka/models.py`](../../../nabavka/models.py) |
| **EUF fakture** | [`services/euf.py`](../../../nabavka/services/euf.py) |
| **UF stavke i roba** | [`services/source_snapshots.py`](../../../nabavka/services/source_snapshots.py) |
| **Plan javnih nabavki** | [`services/public_procurements.py`](../../../nabavka/services/public_procurements.py) |
| Uvoz garažnih zahteva iz Excel-a | [`services/excel_requests.py`](../../../nabavka/services/excel_requests.py) |
| Predmeti i stavke | [`views/cases.py`](../../../nabavka/views/cases.py) |
| Fakture | [`views/invoices.py`](../../../nabavka/views/invoices.py) |
| Pozadinski poslovi | [`nabavka/tasks.py`](../../../nabavka/tasks.py) |

---

## 11. Ulazni i izlazni podaci

| Smer | Šta |
|---|---|
| **Ulaz** | Tri nasleđena pogleda; Excel plan javnih nabavki; Excel garažni zahtevi; ručni unos |
| **Izlaz** | Štampa zahteva i trebovanja materijala; izvoz EUF faktura; podaci Floti |

---

## 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Flota** | Kvar (`garage_order`) i vozilo (`vehicle`) na predmetu; EUF fakture → polise; fakture i trebovanja → dokazi o održavanju |
| **Ugovori** | Dobavljač (`supplier`), osnovni ugovor (`contract`), kupovni ugovori |
| **Administracija** | Organizaciona jedinica i centar — određuju broj predmeta |

> **[P]** Kupovni ugovori su **pogled na modul Ugovori**, bez sopstvene tabele u Nabavci —
> vidi [5. Ekrani](#5-glavni-korisnički-ekrani).

---

## 13. Izveštaji i analize

**6 analiza.** Detaljno: [6.9. Nabavka](../obracuni/06-09-nabavka.md).

| Oznaka | Naziv | Napomena |
|---|---|---|
| B-01 | Procenjena vrednost | [P-38](../10-poznati-problemi.md) |
| B-02 | Grupisanje UF stavki | [P-37](../10-poznati-problemi.md) |
| B-03 | Ključ EUF fakture | [P-39](../10-poznati-problemi.md) |
| B-04 | Razlike verzija plana | — |
| B-05 | Provera šifre posla partnera | — |
| B-06 | Izveštaji i alarmi | [P-36](../10-poznati-problemi.md) — zbir ispravljen 18.09.2026. |

---

## 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `nabavka` | **Sve funkcije modula** — usklađuje se automatski |
| `zahtev` | Kontrolna tabla, spisak i unos zahteva sa stavkama, detalj, **štampa** — bez komercijalne obrade |
| `uprava` | Sve |

> **[P]** Uloga `zahtev` **ne može** povezivati fakture, izdavati narudžbenice ni menjati
> statuse.

---

## 15. Validacije i kontrole

| Kontrola | Poruka / ponašanje |
|---|---|
| **Broj predmeta bez centra** | *„Nedostaje sifra centra za broj zahteva.“* |
| **Stavka: tip bez veze ili veza bez tipa** | *„Izaberite jedan zapis koji odgovara tipu povezivanja.“* / *„Izaberite tip povezivanja za povezani zapis.“* |
| Jedinstvenost predmeta ↔ EUF ključ | Kontrola u bazi |
| Jedinstvenost faktura ↔ šifra posla | Kontrola u bazi |
| **Garažni predmet bez vozila** | *„Izaberite vozilo za zahtev garaže.“* |
| **Predmet nije garažni** | Sistem **prazni** `vehicle`, `work_type` i `garage_order` |
| **Nalog garaže ne pripada vozilu** | *„Nalog mora pripadati izabranom vozilu.“* |
| **Vrsta intervencije ne odgovara nalogu** | *„Vrsta intervencije mora odgovarati izabranom nalogu.“* — inače se preuzima sa naloga |
| Stavka ↔ faktura | **Jedan na jedan prema stavci.** Jedna faktura može imati **više stavki i više predmeta** |
| Masovno povezivanje stavki | Pogađa **samo stavke bez izvora** (`source_type=""`); radi se kroz `update()`, **bez `full_clean()`** |
| Promena osnovne šifre posla | Stara veza se briše **ako nije vraćena**; ako jeste — prelazi u „dodatnu“ |
| Uvoz plana bez prepoznatih stavki | *„Excel ne sadrzi prepoznate stavke plana javnih nabavki.“* |
| Duplirani ključevi u planu | Prijavljuju se korisniku |
| Listovi bez zaglavlja | Preskaču se i prijavljuju |

---

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Predmet vezan za kvar bez sopstvenog vozila | Vrsta intervencije se preuzima sa naloga garaže |
| Otkazan predmet | **Ne prenosi** vrstu intervencije na dokument |
| Faktura dodeljena drugom vozilu | **Uklanja se** iz dokaza o održavanju tog vozila |
| **Ispravka u izvoru EUF** | **Nastaje nova faktura**, stara ostaje sa vezama |
| **UF faktura nestala iz izvora** | **Briše se, veza sa stavkom tiho nestaje** |
| Stavka bez broja fakture | Postaje zasebna UF faktura |
| Stavka plana bez rednog broja | Ključ se pravi iz **otiska naslova** |
| Stavka uklonjena pa vraćena | Status **„Dodato“**, bez veze sa izvornom |
| Pomerena stavka u Excel-u | **„Bez izmene“** — broj reda nije u otisku |
| Roba se poklapa i sa UF i sa EUF | Prikazuje se **`UF`** — vidi [B-07](../obracuni/06-09-nabavka.md#b-07--poklapanje-robe-sa-uf-ili-euf-fakturom) |
| Više od 2.000 EUF faktura u izvoru | **Višak se ne preuzima**, bez upozorenja |
| Naziv firme je prefiks druge firme | Meko poklapanje robe ih može **spojiti** |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Sadržaj pogleda `nbv_EUF_stavke`, `nbv_roba`, `nbv_sif_pos_par` | DDL |
| 2 | Postoji li u izvoru **stabilan identifikator** EUF fakture | **Q35** |
| 3 | Treba li upozorenje kada se zbir stavki razlikuje od unete vrednosti | **Q36** |
| 4 | Da li su potrebni dodatni alarmi | **Q37** |
| 5 | Kako se predmet nabavke povezuje sa knjiženjem troška | **Q3** |
| 6 | **Vrednosni pragovi nabavke** — vidi niže | **Q44** |

### Vrednosni pragovi — poslovno pravilo kojeg u kodu nema [N]

Raniji dokument `nabavka-funkcionalnosti-i-povezivanja.md` navodio je, pod „pravila za
dalju doradu“, tri praga:

| Prag | Postupak |
|---|---|
| Do **100.000,00 RSD** | Mala nabavka |
| **100.000,00 – 1.000.000,00 RSD** | Tri ponude i obrazloženje izbora |
| Preko **1.000.000,00 RSD** | Javna nabavka |

> **[P] U kodu ne postoji nijedna provera pragova** — nema nijedne konstante `100000` ni
> `1000000` u aplikaciji `nabavka`. **Q44:** da li ovo pravilo i dalje važi i treba li ga
> sistem sprovoditi, ili se primenjuje van aplikacije?

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.9. Nabavka](../obracuni/06-09-nabavka.md) | Svih 6 analiza |
| [4.7](../04-baza-podataka.md#47-nabavka--nabavka) | Tabele |
| [5. Poslovni procesi](../05-poslovni-procesi.md) | Proces od kvara do fakture |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-36 … P-39 |
