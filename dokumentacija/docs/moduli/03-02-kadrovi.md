# 3.2. Kadrovi

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Kadrovi** |
| Tehnički naziv | Django aplikacija `hr` |
| Adresa | `/hr/` |
| Bočni meni | `sidebar_kadrovi.html` |

> **[P] Zamka:** modeli `Employee` i `EmployeeCVItem` imaju `app_label = "fleet"`,
> pa su im tabele **`fleet_employee`** i **`fleet_employeecvitem`**, a ne `hr_*`.

---

## 2. Poslovna namena

Vodi **zaposlene i njihovo radno vreme**:

1. **Ko su zaposleni** — evidencija sinhronizovana iz kadrovske baze.
2. **Koliko je ko radio** — radna lista po šiframa posla, uz kontrolu iz evidencije prolazaka.
3. **Ko je odsustvovao** — godišnji odmori i bolovanja.
4. **Kako je ocenjen** — mesečna ocena koja daje lični koeficijent za zaradu.

> **[P] Modul ne obračunava zarade.** Izričito je navedeno u kodu:
> *„without payroll calculations“*. Rezultati se prosleđuju sistemu za obračun zarada.

---

## 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Svaki zaposleni** | Popunjava **svoju** radnu listu, dopunjava svoj CV, ispravlja prikaz imena |
| **Kadrovska služba** | Vodi zaposlene, uvozi bolovanja, sinhronizuje odmore, održava šifarnike |
| **Neposredni rukovodilac** | Ocenjuje zaposlene svoje organizacione jedinice |
| **Direktor centra i generalni direktor** | Daju saglasnost na ocene |
| **Kadrovi i superuser** | Radne liste drugih zaposlenih u dozvoljenom obuhvatu |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Zaposleni** | Evidencija, CV stavke, ispravka prikaza imena |
| **Radna lista** | Mesečna evidencija sati po šiframa posla, topli obrok, terenski dodatak |
| **Evidencija prolazaka** | Prikaz dnevnih sati iz sistema kontrole pristupa, uz spisak problema |
| **Godišnji odmori** | Dodele i rešenja preuzeti iz obračuna zarada |
| **Bolovanja** | Uvoz RFZO Excel izvoza, povezivanje po JMBG |
| **Ocenjivanje** | Šest merila, bodovi 0–4, lični koeficijent, saglasnost u tri nivoa |
| **Rešenja** | Rešenja o prekovremenom i noćnom radu, radu vikendom i praznikom, plaćenom odsustvu — pojedinačno i grupno, sa štampom |
| **Šifarnici** | Vrste rada/odsustva, elementi radne liste, vrste primalaca, merila ocenjivanja |

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa | Ko pristupa |
|---|---|---|
| Spisak zaposlenih | `/zaposleni/` | Kadrovska služba |
| Detalj zaposlenog | `/zaposleni/<id>/` | Kadrovska služba |
| **Moj profil** | `/moj-profil/` | Svaki zaposleni |
| Ispravka imena za prikaz | `/moj-profil/ispravi-ime/` | Svaki zaposleni |
| CV stavke | `/moj-profil/cv/novo/` | Svaki zaposleni |
| **Moja radna lista** | `/hr/radna-lista/` | Svaki zaposleni |
| Radna lista drugog zaposlenog | `/hr/zaposleni/<id>/radna-lista/` | **Samo superuser** |
| Štampa radne liste | `/hr/radna-lista/<id>/stampa/` | Zaposleni |
| **Godišnji odmori** | `/hr/godisnji-odmori/` | Kadrovska služba |
| Sinhronizacija odmora | `/hr/godisnji-odmori/sinhronizacija/` | Kadrovska služba |
| **Bolovanja** | `/hr/bolovanja/` | Kadrovska služba |
| Uvoz bolovanja | `/hr/bolovanja/uvoz/` | Kadrovska služba |
| **Ocenjivanje** | `/hr/ocenjivanje/` | Rukovodioci |
| Nova ocena | `/hr/ocenjivanje/novo/` | Neposredni rukovodilac |
| Štampa ocene | `/hr/ocenjivanje/<id>/stampa/` | Rukovodioci |
| Saglasnost | `/hr/ocenjivanje/<id>/saglasnost/` | Imenovani ocenjivač |
| Grupna saglasnost | `/hr/ocenjivanje/saglasnost/` | Imenovani ocenjivač |
| Šifarnik ocenjivanja | `/hr/ocenjivanje/sifrarnik/` | Kadrovska služba |
| **Rešenja zaposlenih** | `/hr/resenja/` | Kadrovska služba |
| Novo rešenje | `/hr/resenja/novo/` | Kadrovska služba |
| Grupno izdavanje | `/hr/resenja/grupno/` | Kadrovska služba |
| Štampa rešenja | `/hr/resenja/<id>/stampa/`, `/hr/resenja/stampa/` | Kadrovska služba |
| Šifarnik rešenja | `/hr/resenja/sifrarnik/` | **Samo Uprava** |
| Elementi radne liste | `/hr/sifrarnici/elementi-rl/` | Kadrovska služba |

---

## 6. Podaci koje korisnik unosi

| Podatak | Ekran | Ko unosi |
|---|---|---|
| **Sati po danima i šiframa posla** | Radna lista | **Zaposleni** |
| Vrsta rada / odsustva po redu | Radna lista | Zaposleni |
| Topli obrok — broj dana i šifra posla | Radna lista | Zaposleni |
| Terenski dodatak — broj dana | Radna lista | Zaposleni |
| Ispravka imena za prikaz | Moj profil | Zaposleni |
| CV stavke | Moj profil | Zaposleni |
| **Bodovi po merilima i komentari** | Ocenjivanje | Neposredni rukovodilac |
| Saglasnost, korekcija koeficijenta, obrazloženje | Saglasnost | Direktor centra, generalni direktor |
| RFZO Excel datoteka i datum izvoza | Uvoz bolovanja | Kadrovska služba |
| **Broj rešenja iz delovodnika, datum, period ili dani** | Rešenja | Kadrovska služba |
| Broj i datum zahteva na osnovu koga se rešenje donosi | Rešenja | Kadrovska služba |
| Ime u drugom padežu, naziv OJ i radnog mesta u tekstu rešenja | Rešenja | Kadrovska služba |
| Ime i prezime ćirilicom (kada preslovljavanje pogreši) | Detalj zaposlenog | Kadrovska služba |
| Šifarnici | Šifarnici | Kadrovska služba |

---

## 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| **Zaposleni** | `IMS_ERP.dbo.hr_employee` | Dnevno 01:10 |
| **Prolasci radnika** | `INFORMATIKA23.ID.dbo.C_Prolasci_Radnika` | **Pri otvaranju radne liste** |
| Šifarnik tastera | `INFORMATIKA23.ID.dbo.C_Tasteri` | Pri otvaranju |
| Obračunati parovi prolazaka | `INFORMATIKA23.ID.dbo.c_parovi_radnika_detalji` + `SERFIN.bazaldims.dbo.radnik` | Komanda `hr_attendance_summary` |
| **Godišnji odmori** | `[putgeo-server].[BazaLDIMS].[dbo].[Godmor]`, `[GodmorKor]` | **Ručno** |
| Vrste primalaca | `dbo.hr_employee` | Uz šifarnik |

> **[P] Zaštita identiteta:** polje `skip_hr_identity_update` sprečava da noćna
> sinhronizacija prepiše titulu, ime, prezime i pol — jer zaposleni sam ispravlja
> prikaz svog imena.

---

## 8. Tabele i kolone

Detaljno: [4.5. Kadrovi](../04-baza-podataka.md#45-kadrovi--hr). **20 tabela.**

| Tabela | Uloga |
|---|---|
| **`fleet_employee`** | Zaposleni — ključ je `employee_code` |
| `fleet_employeecvitem` | CV stavke |
| `hr_worktimesheet`, `hr_worktimesheetline` | Radna lista i redovi (31 kolona sati) |
| `hr_worktimecategory`, `hr_worktimeelement`, `hr_recipienttype` | Šifarnici radne liste |
| `hr_annualleaveallowance`, `hr_annualleavedecision`, `hr_annualleavesync` | Godišnji odmori |
| `hr_sickleave`, `hr_sickleaveimport` | Bolovanja |
| `hr_evaluationgroup`, `hr_evaluationcriterion`, `hr_evaluationscale` | Šifarnik ocenjivanja |
| `hr_evaluationunitsetup`, `hr_evaluationemployeesetup` | Ko koga ocenjuje |
| **`hr_employeeevaluation`** | **Nepromenljiva ocena sa JSON snimkom** |
| `hr_evaluationapproval` | Saglasnosti po nivoima |
| `hr_vrstaresenja` | Šifarnik obrazaca rešenja — tekstovi ćirilicom |
| `hr_potpisnik` | Ko potpisuje rešenja i u kom periodu |
| **`hr_resenje`** | **Izdato rešenje sa JSON snimkom dokumenta** |
| `hr_resenjedan` | Pojedinačni dani rešenja (vikend, praznik, prekovremeni) |

---

## 9. SQL pogledi i povezani serveri

| Objekat | Server | Namena | Status |
|---|---|---|---|
| `dbo.hr_employee` | `IMS_ERP` | Zaposleni | **[N]** Sadržaj nije potvrđen |
| `Radnici`, `C_Prolasci_Radnika`, `C_Tasteri`, `c_parovi_radnika_detalji` | **`INFORMATIKA23.ID`** | Kontrola pristupa | Kolone poznate iz upita |
| `radnik` | **`SERFIN.bazaldims`** | OJ i ime uz parove | Kolone poznate |
| `Godmor`, `GodmorKor` | **`PUTGEO-SERVER.BazaLDIMS`** | Godišnji odmori | Kolone poznate |

> **[P] Modul zavisi od tri udaljena servera.** Ako nisu dostupni, radna lista se
> otvara, ali bez prolazaka, uz poruku *„Izvor prolazaka trenutno nije dostupan.“*

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`hr/models.py`](../../../hr/models.py), [`hr/evaluation_models.py`](../../../hr/evaluation_models.py), [`hr/resenja_models.py`](../../../hr/resenja_models.py) |
| **Evidencija prolazaka** | [`hr/services/attendance.py`](../../../hr/services/attendance.py) |
| **Ocenjivanje** | [`hr/services/evaluations.py`](../../../hr/services/evaluations.py) |
| **Rešenja** | [`hr/services/resenja.py`](../../../hr/services/resenja.py) |
| Godišnji odmori | [`hr/services/annual_leave.py`](../../../hr/services/annual_leave.py) |
| Bolovanja | [`hr/services/sick_leave.py`](../../../hr/services/sick_leave.py) |
| Šifarnik radne liste | [`hr/services/work_time_catalog.py`](../../../hr/services/work_time_catalog.py) |
| Sinhronizacija zaposlenih | [`hr/sync.py`](../../../hr/sync.py) |
| Radna lista | [`hr/views.py: MyWorkTimeSheetView`](../../../hr/views.py) |

Testovi: `hr/tests.py`, `test_annual_leave.py`, `test_evaluations.py`,
`test_sick_leave.py`, `test_work_time_catalog.py`, `test_resenja.py` — **138 testova**. [P]

---

## 11. Ulazni i izlazni podaci

| Smer | Šta |
|---|---|
| **Ulaz** | Kadrovska baza, prolasci, godišnji odmori iz zarada, RFZO Excel, Excel šifarnici |
| **Izlaz** | Štampa radne liste, **štampa ocene sa tri potpisa** |

> **[N] Q3:** nije potvrđeno kako lični koeficijent i sati sa radne liste stižu u
> obračun zarada — prepisivanjem sa odštampanog obrasca ili nekim prenosom.
> U kodu **nema izvoza** ni veze ka sistemu zarada.

---

## 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Flota** | Zaposleni na putnom nalogu i zaduženju vozila; radna lista prikazuje putne naloge |
| **Mobilni** | Zaposleni uz broj telefona |
| **Isplate** | Partija i opština boravka zaposlenog ulaze u virman |
| **Ugovori** | Ocenjivači po organizacionoj jedinici |
| **Administracija** | Korisnički nalog povezan sa zaposlenim (`CustomUser.employee`) |

---

## 13. Izveštaji i analize

**9 obračuna.** Detaljno: [6.6. Kadrovi](../obracuni/06-06-kadrovi.md).

| Oznaka | Naziv |
|---|---|
| K-01, K-02 | Dnevni sati rada — **dva različita postupka** ([P-28](../10-poznati-problemi.md)) |
| K-03 | Problemi u parovima prolazaka |
| K-04, K-05 | Sati radne liste |
| K-06 | Godišnji odmori |
| K-07 | Bolovanja |
| **K-08** | **Stimulacija i lični koeficijent** |
| K-09 | Tok saglasnosti |

---

## 14. Uloge i prava pristupa

| Dozvola | Šta omogućava |
|---|---|
| `hr:work_time_sheet` | Svoja radna lista |
| `hr:sick_leave_list`, `hr:sick_leave_import` | Bolovanja |
| `hr:annual_leave_list` | Godišnji odmori |
| `hr:work_time_catalog` | Šifarnici |
| `hr:evaluation_list`, `hr:evaluation_create`, `hr:evaluation_approve` | Ocenjivanje |
| **`hr:evaluation_view_all`** | Vidi i ocenjuje **sve** zaposlene |
| `hr:resenje_list`, `hr:resenje_create`, `hr:resenje_izdaj` | Rešenja — pregled, unos, izdavanje |
| `hr:resenje_bulk_create`, `hr:resenje_print` | Grupno izdavanje i štampa |
| `hr:resenje_catalog` | Šifarnik vrsta rešenja i potpisnika |
| **`hr:resenje_view_all`** | Vidi rešenja **svih** centara |

**Posebna pravila [P]:**

- **Sekretarijat** dobija operativne dozvole za rešenja:
  listu, detalj, unos i izmenu nacrta, brisanje, predlog teksta, izdavanje, storniranje,
  pojedinačnu i grupnu štampu i grupni unos. Sinhronizacija dopunjava ove uloge bez
  menjanja njihovih korisnika. Uloga **Pregled** time ne dobija pravo unosa rešenja.
- **Kadrovi** (`kadrovi`) zamenjuju ulogu **Kadrovik — rešenja**, zadržavaju njene korisnike
  i dobijaju sve funkcije kadrovskog modula, uključujući šifarnike. Podaci se ograničavaju
  centrima i kadrovskim OJ iz korisničkog profila; kod `hr:kadrovi_manage` omogućava
  pregled i ocenjivanje zaposlenih u tom obuhvatu. Bez obuhvata nema tuđih podataka.
- `hr:resenje_view_all` i `hr:evaluation_view_all` ostaju posebne dozvole za sve centre;
  kompletna uloga Kadrovi ih ne dobija automatski.
- Bez dozvole `hr:evaluation_view_all`, rukovodilac ocenjuje **samo zaposlene svojih OJ**.
- Ocenu vidi onaj ko ju je napravio **ili** je na njoj imenovan kao ocenjivač.
- Saglasnost daje **isključivo imenovani ocenjivač sa svog naloga**.
- Tuđu radnu listu otvara superuser ili korisnik sa `hr:employee_work_time_sheet`,
  samo za zaposlene u svom obuhvatu. Direktan URL i štampa imaju istu proveru obuhvata.
- Korisnik bez povezanog zaposlenog **ne može** otvoriti radnu listu.
- Bez dozvole `hr:resenje_view_all`, korisnik vidi rešenja dodeljenih centara i OJ
  prema snimljenim šiframa na rešenju. Uloga Kadrovi bez obuhvata ne vidi tuđe podatke.
  Za ranije operativne uloge bez obuhvata ostaje pravilo: samo sopstvena rešenja.
- **Izdato rešenje se više ne menja** — ispravka ide preko storniranja i novog rešenja.

Od 24.09.2026. `hr/access.py` ograničava spisak, detalje i izmenu zaposlenih, radne liste,
odmore, bolovanja i pristup Kadrova ocenjivanju. Kod rešenja proveravaju se i pojedinačni
unos, grupni unos, predlog teksta i snimljene šifre OJ/centra. Kadrovske OJ biraju se
u Administracija → Korisnici → Uloge i dozvole. Ograničenja podataka ne menjaju obračune
ni pravilo da saglasnost na ocenu daje imenovani ocenjivač.

### Unos i štampa rešenja zaposlenih

- Pol za tekst se preuzima iz evidencije (ženske oznake `F`, `Z`, `Ž` i `Ж` se
  prepoznaju jednako), uz mogućnost izbora oblika za konkretno rešenje. Izbor se čuva
  u nacrtu, a izdati dokument ostaje sačuvan u svom snimku.
- OJ se automatski bira prema zaposlenom. Izbor druge OJ ograničen je korisnikovim
  obuhvatom. Ako nema naziva u šifrarniku, predlaže se „OJ <šifra>“, koji se može
  tekstualno dopuniti. Centar se izvodi postojećim mapiranjem OJ na centar.
- Period od–do dostupan je za sve vrste; kod praznika ostaju obavezni pojedinačni
  dani sa vrstom praznika. Za rad se može uneti vreme smene od–do; završetak pre
  početka označava naredni dan. Zahtev se trenutno unosi kao tekst (broj ili opis),
  uz opcion datum, bez veze sa budućom evidencijom zahteva.
- Polje **Ko potpisuje rešenje** prikazuje potpisnika prema datumu ili ručni izbor.
  Korisnik sa dozvolom `hr:resenje_catalog_create` može dodati osobu i funkciju
  direktno uz nacrt. Bez potpisnika nacrt se čuva, a izdavanje traži važeći potpis.

- Datumi u formama koriste format **dd.mm.gggg** i kalendar, kao ostali ekrani Kadrova.
  Pojedinačni dani se dodaju dugmetom **Dodaj dan**, a označavanjem **Ukloni** izostavljaju
  pri čuvanju nacrta. Grupni unos zadržava izabrane zaposlene i njihove brojeve rešenja
  ako validacija prijavi grešku.
- Detalj prikazuje dokument u širini **A4 (210 × 297 mm)**. Dugme **Štampaj** otvara
  prikaz za štampu ili čuvanje PDF-a: uspravan A4, margine **18 mm**, osnovni tekst Times New Roman 12 pt.
  Zaglavlje sadrži IMS logo, broj i datum, zatim naslov vrste i podatke zaposlenog.
  U dijalogu pregledača isključiti njegova zaglavlja i podnožja.
- Svako rešenje u grupnoj štampi počinje na novoj stranici. Duži tekst prelazi na narednu
  A4 stranicu, a blok potpisa i dostavljanja ostaje zajedno pri dnu poslednje strane.

---

## 15. Validacije i kontrole

| Kontrola | Poruka / ponašanje |
|---|---|
| Sati po danu | Ceo broj **0–24** |
| Dani izvan meseca | Brišu se pri čuvanju |
| **Uvoz bolovanja — sve ili ništa** | *„Nijedan red nije uvezen.“* |
| RFZO ID uz drugi JMBG | *„RFZO ID već postoji uz drugi JMBG.“* |
| **Stariji RFZO izvoz** | *„Datoteka je starija od već evidentiranih podataka.“* |
| Status „Zaključeno“ bez datuma | Odbija se |
| **Sinhronizacija odmora — sve ili ništa** | *„Ništa nije sinhronizovano.“* |
| Istovremena sinhronizacija odmora | *„Sinhronizacija je već u toku.“* |
| Obrazac ocene stariji od 24 sata | *„Obrazac je istekao ili nije važeći.“* |
| Dvostruko slanje ocene | Vraća se postojeća ocena (`request_key`) |
| Bodovi van sačuvane skale | *„Izabrani bodovi ne pripadaju sačuvanoj skali.“* |
| Preskakanje nivoa saglasnosti | *„Prethodni nivo još nije potvrdio obrazac.“* |
| Korekcija izvan granica obrasca | *„Koeficijent je izvan granica sačuvanog šifrarnika.“* |
| Korekcija bez obrazloženja | Odbija se |
| Rukovodilac menja koeficijent | *„Za korekciju merila sačuvajte novu verziju obrasca.“* |

---

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| **Smena preko ponoći** | **Ne uparuje se** — dva problema, sati se ne računaju ([P-28](../10-poznati-problemi.md)) |
| Pauza (taster 12) | Uvek prijavljena kao problem |
| Službeni izlazak | Računa se **do 16:00** |
| Zaboravljen ulazak ili izlazak | Par se ne računa, problem se prijavljuje |
| Izvor prolazaka nedostupan | Radna lista radi, sati prikazani kao „—“ |
| **Otvoreno bolovanje** | Prikazuje se do **datuma RFZO izvoza** ([P-29](../10-poznati-problemi.md)) |
| Više zaposlenih sa istim JMBG | Bolovanje se **ne povezuje**, uz napomenu |
| Šifra zaposlenog 0 u odmorima | Zapis se čuva **nepovezan** |
| Rešenje uklonjeno iz izvora | Označava se povučenim, **ne briše se** |
| Ocena je pogrešna | Ispravka je **nova revizija**, izvorna ostaje |
| Nazivi merila na ćirilici | Preslovljavaju se na latinicu pri prikazu |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | **Koji od dva obračuna sati je merodavan** | **P-28** |
| 2 | Zašto se službeni izlazak računa do 16:00 i da li je to zvanično radno vreme | **Q27** |
| 3 | Da li pauzu treba obračunati ili samo ne označavati kao problem | **Q25** |
| 4 | Da li je odobravanje radne liste („Odobreno“) predviđeno | **Q26** |
| 5 | **Kako lični koeficijent stiže u obračun zarada** | **Q3** |
| 6 | Poreklo koeficijenata u šifarniku ocenjivanja i zvanični pravilnik | **Q6** |
| 7 | Sadržaj pogleda `dbo.hr_employee` | DDL |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.6. Kadrovi](../obracuni/06-06-kadrovi.md) | Svih 9 obračuna |
| [4.5](../04-baza-podataka.md#45-kadrovi--hr) | Tabele Kadrova |
| [7. Integracije](../07-integracije.md) | Povezani serveri i RFZO |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-28, P-29 |
