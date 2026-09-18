# 12. Rečnik pojmova i mapiranje naziva

> **Za koga je ovo poglavlje:** za sve.
> Sadrži **objašnjenja pojmova** i **tabelu preslikavanja** naziva sa ekrana u nazive
> u kodu i bazi — jer se često razlikuju.

---

## 12.1. Poslovni pojmovi

### Organizacija

| Pojam | Značenje |
|---|---|
| **Centar** | Najviši nivo organizacije. U bazi: `OrganizationalUnit.center`, u izvoru `posao.blok`. Određuje **šta korisnik sme da vidi**. |
| **Organizaciona jedinica (OJ)** | Sinonim za **šifru posla** u ovom sistemu. Tabela `fleet_organizationalunit`. |
| **Šifra posla** | Oznaka nosioca troška i prihoda. Isti podatak kao OJ. U izvoru `sif_pos`. |
| **OJ knjiženja** | **Različit pojam!** Organizaciona jedinica upisana na knjiženju (`nalog_z.oj`). **Nije** isto što i centar. |
| **Blok** | Naziv za centar u nasleđenom šifarniku (`posao.blok`). |
| **Profitni posao** | Posao sa oznakom `profitni = 'P'` — učestvuje u raspodeli zajedničkih troškova. |

### Vozni park

| Pojam | Značenje |
|---|---|
| **Osnov raspolaganja** | Po čemu IMS koristi vozilo: **vlasništvo IMS** ili **korišćenje po ugovoru**. Tabela `fleet_vehicleholding`. |
| **Dodela šifre posla** | Istorijski zapis kojoj OJ vozilo pripada od kog datuma. Tabela `fleet_jobcode`. |
| **Otpis** | Vozilo izuzeto iz upotrebe. Polje `otpis`, puni ga sinhronizacija — **ne unosi se ručno**. |
| **Kvar (PK)** | Prijava kvara u garaži. Broj `PK-<id>/<godina>`. |
| **GZN** | Zahtev za nabavku iz garaže. Broj `GZN-<id>/<godina>`. |
| **Trebovanje** | Zahtev za materijal iz magacina. |
| **Putni nalog (PN)** | **Dva različita pojma:** *putni nalog vozila* = zaduženje vozila; *putni nalog* = službeno putovanje zaposlenog sa akontacijom. |
| **Zaduženje vozila** | Period u kome zaposleni koristi vozilo, sa početnom i krajnjom kilometražom. |
| **Crvena zona** | Vozilo u koje je uloženo više nego što vredi. |
| **Prag troška po km** | Granica prihvatljivog troška, po klasi mase vozila. |

### Gorivo

| Pojam | Značenje |
|---|---|
| **Bon (voucher)** | Broj potvrde sa pumpe. Kod OMV-a služi kao „broj fakture“ dok faktura ne stigne. |
| **Odjek računa** | Zaostali nefakturisani red u OMV izvoru, koji ponavlja isto točenje. **Mora se ukloniti.** |
| **AdBlue** | Dodatak za dizel motore. Računa se kao proizvod goriva, ali **ne ulazi** u obračun putnog naloga. |
| **Polumesec** | Prva (dani 1–15) ili druga (16–31) polovina meseca. |

### Finansije

| Pojam | Značenje |
|---|---|
| **P − R** | Prihod minus rashod, **pre** raspodele zajedničkih troškova. |
| **ZT** | Zajednički trošak raspoređen na posao. |
| **P − R − ZT** | Konačni rezultat posla, **pre poreza na dobit**. |
| **Priliv / odliv** | Obračun novčanog toka po pravilima procedure — **nije promet bankovnog računa**. |
| **Neto gotovina** | Priliv minus odliv. |
| **IF** | Izdata faktura. Konta potraživanja `20400` / `20500`. |
| **ON** | Interna faktura ili nalog. |
| **ZAT** | Vrsta naloga za **zatvaranje godine** — namerno izuzeta iz analitike. |
| **`nalog_z`** | Tabela knjiženja u nasleđenom sistemu. **Postoji dvaput** — udaljeni izvor i lokalna kopija. |
| **Kriterijum (1/2/3)** | Osnovica po kojoj se raspoređuje zajednički trošak. |
| **Koeficijent posla / centra** | Procenat učešća u raspodeli. |

### Potraživanja

| Pojam | Značenje |
|---|---|
| **Baket** | Starosni razred duga. Sedam razreda: nedospelo, 30, 45, 60, 90, 180, 181+. |
| **Nedospelo (`0.1`)** | Dug koji još nije dospeo — **ali i dug bez unetog datuma dospeća**. |
| **Snimak stanja** | Provereno i objavljeno stanje potraživanja na određeni datum. |
| **Pozicija** | Jedna otvorena stavka duga: partner + dokument + šifra posla + grupa konta. |
| **Grupa konta** | Prva tri znaka konta: `204` domaći kupci, `205` inostrani. |
| **Ino** | Oznaka inostranog partnera. |
| **Opomena / pozivno pismo** | Dokumenti kojima se traži plaćanje. |
| **UPPR** | Unapred pripremljen plan reorganizacije. |

### Nabavka

| Pojam | Značenje |
|---|---|
| **Predmet nabavke** | Zahtev sa stavkama, od podnošenja do fakture. |
| **ZN / ZU / PLN** | Zahtev za nabavku / za uslugu / predlog za opremu. Sa **G** na kraju = garažni. |
| **EUF** | Elektronska ulazna faktura. |
| **UF** | Ulazna faktura — u sistemu su **stavke** i izvedene **fakture**. |
| **Roba** | Robni promet iz nasleđenog sistema. |
| **Snimak izvora** | Lokalna kopija nasleđenog skupa, sa stabilnim ključem. |
| **Vraćeno** | Oznaka da je faktura vraćena sa šifre posla. |
| **Verzija plana** | Svaki uvoz plana javnih nabavki pravi novu verziju sa razlikama. |

### Kadrovi

| Pojam | Značenje |
|---|---|
| **Radna lista** | Mesečna evidencija sati po šiframa posla. Sati su **celi brojevi**. |
| **Element radne liste** | Šifra za obračun zarada (`elsif`, `elnaz`), vezana za vrstu primaoca. |
| **Vrsta primaoca** | Kategorija zaposlenog; određuje koje elemente može birati. |
| **Prolazak** | Zapis o prislanjanju kartice na čitač. |
| **Službeni izlazak** | Taster 4 — radno vreme se računa **do 16:00**. |
| **Merilo** | Jedno od šest merila ocenjivanja. |
| **Stimulacija** | Zbir koeficijenata izabranih bodova. |
| **Lični koeficijent (K4)** | **`1 + stimulacija`** — množilac za zaradu. |
| **Revizija ocene** | Ispravka se pravi kao **nova revizija**; izvorna ostaje. |

### Mobilna telefonija

| Pojam | Značenje |
|---|---|
| **Paket** | Iznos koji plaća poslodavac. |
| **Obustava** | Iznos koji se obustavlja od zarade: `osnovica PDV − neto paketa + parking + NZRD`. |
| **NZRD** | Stavka sa računa operatera koja **ulazi u obustavu**. **[N]** Puno značenje nije potvrđeno. |
| **Osnovica za PDV** | Polje sa računa; **osnov obračuna obustave** — potvrđeno ispravnim. |
| **Dodela** | Koji broj kome pripada u kom mesecu. |

### Ugovori i menice

| Pojam | Značenje |
|---|---|
| **Aneks** | Izmena ugovora; mora imati glavni ugovor. |
| **Tip vrednosti** | Fiksna, po satu, mesečno, čovek mesec, po jedinici, bez definisane vrednosti. |
| **Izlazna menica** | Menica koju je **IMS izdao** — obaveza IMS-a. |
| **Ulazna menica** | Menica **primljena od partnera** — obezbeđenje za IMS. |
| **Avalista** | Lice koje jemči za menicu. |
| **Jedinica vrednosti** | Kod ulazne menice: `RSD`, `EUR` ili **`PROCENAT`** — u trećem slučaju iznos **nije novčani**. |
| **APR status** | Status privrednog subjekta; aktivan **samo** za tačno `активан`. |

### Tehnički pojmovi

| Pojam | Značenje |
|---|---|
| **Povezani server** | Udaljeni SQL Server dostupan kroz upit — `PUTGEO-SERVER`, `INFORMATIKA23`, `SERFIN`. |
| **Nasleđeni pogled** | `dbo.*` objekat starog ERP-a koji sistem samo čita. |
| **Draft (nedovršeno)** | Podatak preuzet spolja koji čeka dopunu korisnika. |
| **Snimak (snapshot)** | Lokalna kopija spoljnog skupa po stabilnom ključu. |
| **Stabilni ključ** | Identitet zapisa koji **ne zavisi** od iznosa i opisa. |
| **Kontrolni zbirovi** | Poređenje prenetog sa izvorom **pre** objave. |
| **Zaključavanje poslova** | Sprečava da dva ista posla rade istovremeno. |
| **Preskočen** | Posao nije pokrenut jer prethodni još radi — **nije greška**. |

---

## 12.2. Naziv na ekranu ↔ u kodu ↔ u bazi

> Najčešći uzrok nesporazuma. [P]

### Vozni park

| Na ekranu | U kodu | U bazi |
|---|---|---|
| Vozilo | `Vehicle` | `fleet_vehicle` |
| Broj šasije | `chassis_number` | isto |
| Inventarski broj | `inventory_number` | isto |
| Knjigovodstvena vrednost | `value` | isto |
| Nabavna vrednost | `purchase_value` | isto |
| Otpis | `otpis` | isto |
| Saobraćajna dozvola | `TrafficCard` | `fleet_trafficcard` |
| Registracioni broj | `registration_number` | isto |
| Šifra posla (dodela) | `JobCode` | `fleet_jobcode` |
| Osnov raspolaganja | `VehicleHolding` | `fleet_vehicleholding` |
| Lizing / najam | `Lease` | `fleet_lease` |
| Polisa | `Policy` | `fleet_policy` |
| Osiguranje (knjiženje) | `Insurance` | `fleet_insurance` |
| Potrošnja goriva | `FuelConsumption` | `fleet_fuelconsumption` |
| Kvar | `Kvar` | `fleet_kvar` |
| Trebovanje | `Requisition` | `fleet_requisition` |
| Putni nalog (zaposleni) | `PutniNalog` | `fleet_putninalog` |
| Putni nalog vozila | `VehicleTravelOrder` | `fleet_vehicletravelorder` |
| Troškovi idu na teret | `job_code` | `job_code_id` |
| Isplaćeno | `isplaceno` | isto |

### Kadrovi — **pažnja na prefiks**

| Na ekranu | U kodu | U bazi |
|---|---|---|
| **Zaposleni** | `hr.models.Employee` | **`fleet_employee`** |
| **CV stavka** | `EmployeeCVItem` | **`fleet_employeecvitem`** |
| Radna lista | `WorkTimeSheet` | `hr_worktimesheet` |
| Red radne liste | `WorkTimeSheetLine` | `hr_worktimesheetline` |
| Partija | `account_number` | isto |
| Opština boravka | `residence_municipality` | isto |
| Šifra zaposlenog | `employee_code` | isto |
| Vrsta primaoca | `RecipientType` | `hr_recipienttype` |
| Bolovanje | `SickLeave` | `hr_sickleave` |
| Ocena | `EmployeeEvaluation` | `hr_employeeevaluation` |
| Stimulacija | `stimulation` | isto |
| Lični koeficijent | `personal_coefficient` | isto |

### Administracija — **pažnja na prefiks**

| Na ekranu | U kodu | U bazi |
|---|---|---|
| **Korisnik** | `core.models.CustomUser` | **`fleet_customuser`** |
| **Uloga** | `Role` | **`fleet_role`** |
| **Dozvola** | `PermissionCode` | **`fleet_permissioncode`** |
| **Organizaciona jedinica** | `OrganizationalUnit` | **`fleet_organizationalunit`** |
| **Evidencija rada** | `ActivityLog` | **`fleet_activity_log`** |
| **Istorija zadataka** | `TaskHistory` | **`fleet_task_history`** |

### Finansije

| Na ekranu | U kodu | U izvoru |
|---|---|---|
| Knjiženje | `LedgerEntry` | `nalog_z` |
| Datum knjiženja | `booking_date` | `dat_naloga` |
| Datum dokumenta | `document_date` | `datum` |
| Vrsta naloga | `journal_type` | `sif_vrs` |
| Broj naloga | `journal_number` | `br_naloga` |
| Stavka | `line_number` | `stavka` |
| Konto | `account` | `knt` |
| Duguje / potražuje | `debit` / `credit` | `duguje` / `potrazuje` |
| Šifra posla | `job_code` | `sif_pos` |
| Centar | `center` | `posao.blok` |
| OJ knjiženja | `organizational_unit` | `oj` |
| Veza dokumenta | `document_reference` | `vez_dok` |
| Dospeće | `due_date` | `dpo` |

### Potraživanja

| Na ekranu | U kodu | U bazi |
|---|---|---|
| Partner | `FinancePartnerIdentity` | `potrazivanja_financepartneridentity` |
| Faktura | `InvoiceDocument` | `potrazivanja_invoicedocument` |
| Knjiženje | `ReceivablePosting` | `potrazivanja_receivableposting` |
| Snimak stanja | `BalanceSnapshot` | `potrazivanja_balancesnapshot` |
| Pozicija | `ReceivablePosition` | `potrazivanja_receivableposition` |
| Baket | `bucket()` | `resolution_details.bucket` |
| Opomena | `CollectionNotice` | `potrazivanja_collectionnotice` |
| Pravni postupak | `CollectionLegalCase` | `potrazivanja_collectionlegalcase` |

### Nabavka i Ugovori

| Na ekranu | U kodu | U bazi |
|---|---|---|
| Predmet nabavke | `ProcurementCase` | `nabavka_procurement_case` |
| Stavka | `ProcurementItem` | `nabavka_procurement_item` |
| EUF faktura | `ProcurementInvoice` | `nabavka_invoice` |
| UF stavka | `EufItemSnapshot` | `nabavka_euf_item_snapshot` |
| UF faktura | `UfInvoiceSnapshot` | `nabavka_uf_invoice_snapshot` |
| Roba | `GoodsSnapshot` | `nabavka_goods_snapshot` |
| Narudžbenica | `PurchaseOrder` | `nabavka_purchase_order` |
| Partner | `Partner` | `ugovori_partner` |
| Ugovor | `Contract` | `ugovori_contract` |
| Garancija | `ContractGuarantee` | `ugovori_contract_guarantee` |
| **Menica** | `Menica` | **`menica`** *(bez prefiksa)* |
| **Ulazna menica** | `UlaznaMenica` | **`ulazna_menica`** *(bez prefiksa)* |

---

## 12.3. Skraćenice

| Skraćenica | Značenje |
|---|---|
| **OJ** | Organizaciona jedinica |
| **ZT** | Zajednički trošak |
| **P / R** | Prihod / rashod |
| **IF / ON / ZAT / NT** | Vrste naloga |
| **EUF / UF** | Elektronska ulazna faktura / ulazna faktura |
| **ZN / ZU / PLN / ZNG / ZUG** | Vrste predmeta nabavke |
| **GZN** | Garažni zahtev za nabavku |
| **PK** | Prijava kvara |
| **PN** | Putni nalog |
| **AO** | Autoodgovornost |
| **JMBG / MB / PIB** | Matični broj građana / matični broj / poreski identifikacioni broj |
| **RFZO** | Republički fond za zdravstveno osiguranje |
| **APR** | Agencija za privredne registre |
| **NBS** | Narodna banka Srbije |
| **SEF** | Sistem elektronskih faktura |
| **UPPR** | Unapred pripremljen plan reorganizacije |
| **ZJN** | Zakon o javnim nabavkama |
| **CPV / NSTJ** | Šifarnici u planu javnih nabavki |
| **NZRD** | Stavka računa operatera — **[N]** značenje nije potvrđeno |

---

## 12.4. Pojmovi koje treba razlikovati

> Najčešći uzrok pogrešnog tumačenja. [Z]

| Slično zvuči | Ali nije isto |
|---|---|
| **Centar** naspram **OJ knjiženja** | Centar je iz šifarnika posla; OJ knjiženja je polje na knjiženju |
| **Datum knjiženja** naspram **datuma dokumenta** | Prihodi po prvom, fakture po drugom |
| **Putni nalog** naspram **putnog naloga vozila** | Službeno putovanje naspram zaduženja vozila |
| **P − R** naspram **P − R − ZT** | Pre i posle raspodele zajedničkih troškova |
| **Priliv** naspram **naplate** | Priliv je obračun po pravilima, ne evidencija uplata |
| **Neto gotovina** naspram **stanja na računu** | Obračunska veličina, ne stanje |
| **Bruto** naspram **neto** iznosa goriva | Sa PDV-om i bez njega |
| **`nalog_z` udaljeni** naspram **lokalnog** | Finansije čitaju udaljeni; procedura puni lokalni |
| **„Nedospelo“** naspram **„nepoznato dospeće“** | U istom baketu, iako su različite stvari |
| **„Opomena“** (status vozila) | Znači **nema podatka o kilometraži**, ne da je vozilo problematično |
| **„Preskočen“** (posao) | Prethodni još radi — **nije greška** |
| **Prazno** naspram **nule** | „Nema podatka“ naspram „iznos je nula“ |

---

## 12.5. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Šta radi pojedini modul? | [3. Moduli](03-moduli.md) |
| Koje tabele postoje? | [4. Baza podataka](04-baza-podataka.md) |
| Kako se računa iznos? | [6. Analize i obračuni](06-analize-i-obracuni.md) |
