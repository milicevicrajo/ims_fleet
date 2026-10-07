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
| **Radna lista** | Mesečna evidencija sati po šiframa posla, topli obrok, terenski dodatak; predlog popunjavanja iz prolazaka, putnih naloga, bolovanja, praznika i slave (K-11) |
| **Analitika zaposlenih** | Od 05.10.2026.: pol, starosna piramida i histogram, rasponi po deset godina, prosečna starost (ukupno, žene, muškarci), stručna sprema (izvedena iz zanimanja), starost po spremi, staž u Institutu, radni odnos i OJ; PDF fajl (A4, zaglavlje i broj strane na svakoj strani) i Excel ([K-10](../obracuni/06-06-kadrovi.md)) |
| **Evidencija prolazaka** | Od 05.10.2026. za dan sa problemom ili bez prolaza na radni dan upisuje se **komentar** (vidi se i u prilogu). Prikaz dnevnih sati iz sistema kontrole pristupa, uz spisak problema; od 01.10.2026. štampa se i kao **prilog radne liste** (A4 uspravno: svaki prolaz sa vremenom, sati po danu, praznici, bolovanja, putni nalozi, potpisi zaposlenog i rukovodioca). Ako izvor prolazaka nije dostupan, prilog to piše i ne prilaže se. |
| **Godišnji odmori** | Dodele i rešenja preuzeti iz obračuna zarada |
| **Bolovanja** | Uvoz RFZO Excel izvoza, povezivanje po JMBG |
| **Ocenjivanje** | Šest merila, bodovi 0–4, lični koeficijent, saglasnost u tri nivoa |
| **Zahtevi** | Zahtev za izdavanje rešenja, sa automatskim brojem; ko podnosi i ko odobrava upisuje se u zahtev; isti zahtev za više zaposlenih odjednom |
| **Rešenja** | Rešenja o prekovremenom i noćnom radu, radu vikendom i praznikom, plaćenom odsustvu i zameni odsutnog zaposlenog — iz zahteva ili bez njega, pojedinačno i grupno, sa štampom |
| **Šifarnici** | Vrste rada/odsustva, elementi radne liste, vrste primalaca, merila ocenjivanja |

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa | Ko pristupa |
|---|---|---|
| **Pregled** (početna strana, od 02.10.2026.) | `/hr/` | Svaki prijavljeni korisnik; delovi samo uz dozvolu spiska |
| Spisak zaposlenih | `/zaposleni/` | Kadrovska služba |
| **Analitika zaposlenih** (od 05.10.2026.), PDF i Excel | `/hr/analitika/`, `?izvoz=pdf`, `?izvoz=xlsx` | Dozvola `hr:analitika`, u obuhvatu korisnika; sa `hr:analitika_view_all` cela firma. Osoba sa više aktivnih brojeva radnika broji se jednom (od 06.10.2026.) |
| Štampa spiska (A4, „Sačuvaj kao PDF”) i Excel (od 05.10.2026.) | `/zaposleni/?izvoz=stampa`, `?izvoz=xlsx` | Isto kao spisak — ista dozvola `employee_list`, obuhvat i filteri |
| Detalj zaposlenog | `/zaposleni/<id>/` | Kadrovska služba |
| **Moj profil** | `/moj-profil/` | Svaki zaposleni |
| Ispravka imena za prikaz | `/moj-profil/ispravi-ime/` | Svaki zaposleni |
| CV stavke | `/moj-profil/cv/novo/` | Svaki zaposleni |
| **Moja radna lista** | `/hr/radna-lista/` | Svaki zaposleni |
| Radna lista drugog zaposlenog | `/hr/zaposleni/<id>/radna-lista/` | **Samo superuser** |
| Štampa radne liste | `/hr/radna-lista/<id>/stampa/` | Zaposleni |
| Štampa evidencije prolaza (prilog radne liste) | `/hr/radna-lista/<id>/prolazi/stampa/` | Zaposleni (ista prava kao štampa radne liste) |
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
| **Zahtevi zaposlenih** | `/hr/zahtevi/` | Kadrovska služba |
| Novi zahtev | `/hr/zahtevi/novi/` | Kadrovska služba |
| Isti zahtev za više zaposlenih | `/hr/zahtevi/grupno/` | Kadrovska služba |
| Detalj zahteva i „Dodaj rešenje iz zahteva“ | `/hr/zahtevi/<id>/` | Kadrovska služba |
| Štampa zahteva | `/hr/zahtevi/<id>/stampa/`, `/hr/zahtevi/stampa/` | Kadrovska služba |
| **Rešenja zaposlenih** | `/hr/resenja/` | Kadrovska služba |
| Novo rešenje | `/hr/resenja/novo/` | Kadrovska služba |
| Grupno izdavanje | `/hr/resenja/grupno/` | Kadrovska služba |
| Štampa rešenja | `/hr/resenja/<id>/stampa/`, `/hr/resenja/stampa/` | Kadrovska služba |
| Šifarnik rešenja | `/hr/resenja/sifrarnik/` | **Samo Uprava** |
| Elementi radne liste | `/hr/sifrarnici/elementi-rl/` | Kadrovska služba |
| **Ugovori zaposlenih** | `/hr/ugovori/` | Kadrovska služba, Uprava |
| Unos ugovora za period | `/hr/ugovori/<id>/` (čuvanje: `/hr/ugovori/<id>/izmena/`) | Kadrovska služba |
| Skeniran ugovor | `/hr/ugovori/<id>/dokument/` | Kadrovska služba, Uprava (samo zaposleni u obuhvatu) |
| Sinhronizacija ugovora | `/hr/ugovori/sinhronizacija/` | Kadrovska služba |

### Ugovori zaposlenih (od 29.09.2026.) [P]

**Jedan red je jedan period rada iz kadrovske baze**, a Kadrovi uz njega unose broj i datum ugovora
(datum od 30.09.2026., nije obavezan), broj aneksa (nije obavezan — prvi ugovor nema aneks), skeniran
dokument i napomenu. Ugovori
sa zaposlenima vode se ovde, a ne u modulu Ugovori: tamo su poslovni ugovori sa partnerima
(vrsta „Ugovori o radu“ tamo sadrži ugovore o delu sa spoljnim licima).

| Tema | Pravilo |
|---|---|
| Izvor | `dbo.v_hr_RadStaz` (IMS_ERP) → `RadStaz` na `PUTGEO-SERVER.bazaldims`, samo `u_firmi = 'DA'`. Ključ je šifra radnika + redni broj (`rasif`, `rb`). Kategorija „Radni odnos“ je preduzeće 1, „Van radnog odnosa“ preduzeće 2. Datum 01.01.3000. znači na neodređeno. |
| Sinhronizacija | Noću u **01:15** (`hr.tasks.sync_ugovori_zaposlenih_task`, posle zaposlenih) i dugmetom „Osveži iz kadrovske baze“. Menja samo polja iz izvora (period, opis, staž, aktivnost radnika); unete podatke ne dira. Svako pokretanje se beleži (`hr_ugovori_sinhronizacija`). Prazan izvor zaustavlja sinhronizaciju. |
| OJ i radno mesto | Šifre i nazivi OJ (`radnik.oj` + `ob_jedin`, naziv za tekuću godinu) i radnog mesta po sistematizaciji (`radnik.sif_sis` + `Sistemat`, po preduzeću) **upisuju se kada se period prvi put pojavi i posle se sami ne menjaju** — ostaju kao istorija. Kadrovska baza nema istoriju OJ i radnog mesta, pa su periodi zatečeni pri prvoj sinhronizaciji (29.09.2026.) dobili današnje stanje. Ručna izmena se beleži kao „Uneto ručno“; dugme „Preuzmi trenutnu OJ i radno mesto“ ponovo upisuje stanje iz kadrovske baze. |
| Više radnih mesta | Od 01.10.2026. Ako radnik radi na više radnih mesta, Kadrovi na unosu perioda dodaju drugo i dalja (OJ i radno mesto po sistematizaciji, tabela `hr_ugovor_dodatno_radno_mesto`). **Izveštaji uvek uzimaju prvo radno mesto** — polja na samom periodu; ostala služe bezbednosti i zdravlju na radu. Dodatna radna mesta unose se samo ručno: sinhronizacija i dugme „Preuzmi trenutnu OJ i radno mesto“ ih ne diraju. Vide se na spisku ugovora (pretraga ih nalazi po nazivu) i na kartici zaposlenog. |
| Aneks | Kada je unet broj aneksa, može se izabrati glavni ugovor — raniji period istog radnika koji nije i sam aneks. Veza nije obavezna. |
| Dokument | PDF ili slika (JPG, PNG, TIFF), najviše 20 MB, u `media/hr/ugovori/`. Otvara se samo kroz aplikaciju (`hr:ugovor_dokument`), uz proveru obuhvata. |
| Nestao ili izmenjen period | Period koji nestane iz kadrovske baze se ne briše, nego dobija oznaku „Nema u kadrovskoj bazi“. Ako se posle unosa promeni datum početka, raniji datum se čuva i red je označen „Proveriti“ dok ga Kadrovi ne potvrde. |
| Veza sa zaposlenim | Period je vezan za karticu zaposlenog (FK `employee`, po šifri radnika, pri svakoj sinhronizaciji). Na kartici zaposlenog, kartica **Ugovori** prikazuje njegove periode sa brojem i datumom ugovora, aneksom, OJ, radnim mestom i dokumentom (od 30.09.2026.); ispod su poslovni ugovori sa partnerom iste šifre. Na sopstvenom profilu zaposleni vidi svoje ugovore, bez ulaska u unos i bez otvaranja dokumenta. Periodi bivših radnika koji nemaju karticu u aplikaciji (1.291 od 4.142, 30.09.2026.) ostaju bez veze. |
| Obuhvat | Kao spisak zaposlenih: vide se periodi zaposlenih u obuhvatu korisnika. Periodi bivših radnika koji nemaju karticu u aplikaciji i radnika bez čvora registra (OJ `1`) vidi samo obuhvat cele firme. |

---

### Moj profil → Pregled (od 02.10.2026.)

Moj profil se otvara na kartici **Pregled** (`hr/_moj_pregled.html`, `hr/services/moj_profil.py`); ostale
kartice (osnovni podaci, CV, radne liste, godišnji odmori, zahtevi, rešenja, putni nalozi…) su iza nje.
Tuđi profil (detalj zaposlenog) nema ovu karticu.

| Deo | Sadržaj |
|---|---|
| Brze akcije | Radna lista tekućeg meseca (sa statusom), **Podnesi zahtev** (uz `hr:zahtev_create`; zaposleni je unapred izabran preko `?zaposleni=`), evidencija prolaza za tekući mesec, godišnji odmor, dodavanje CV stavke |
| Godišnji odmor | Za tekuću godinu (i prethodnu, ako je ostalo dana): dodeljeno, po rešenjima i **preostalo prema rešenjima** — dani po rešenju iz kadrovske baze nisu potvrđeno korišćenje, pa ovo nije obračun salda; sledeći ili tekući godišnji odmor |
| Gde radim | Centar i jedinica iz registra (`Employee.org_node`), radno mesto i dodatna radna mesta, ugovor koji danas važi (kategorija, broj, period, upozorenje ako ističe u 45 dana), staž u IMS-u od datuma zaposlenja |
| Ovaj mesec | Status radne liste, putni nalozi bez pravdanja, zaduženo vozilo, telefoni |
| Moji zahtevi / Moja rešenja | Poslednja četiri, sa statusom i vezom na detalj |

### Pregled — početna strana Kadrova (od 02.10.2026.)

Link **Kadrovi** u zaglavlju otvara `hr:pregled` (`hr/pregled_views.py`, `hr/services/pregled.py`).
Strana samo broji i izdvaja ono što korisnik već vidi na spiskovima, u istom obuhvatu; ništa ne upisuje.
U bočnom meniju je prva stavka **Pregled**, a **Moj profil** je na dnu.

| Deo | Dozvola | Sadržaj |
|---|---|---|
| Aktivni zaposleni, zaposleni po centrima, novi zaposleni | `employee_list` | Broj aktivnih (žene: pol `F` ili `Z` — kadrovska baza upisuje `Z`; muškarci `M`), raspodela po centru registra (`Employee.org_node`), zaposleni u poslednjih 30 dana |
| Odsutni danas | `hr:annual_leave_list` / `hr:sick_leave_list` | Godišnji odmor po rešenju (`AnnualLeaveDecision`, prisutno u izvoru) i bolovanje (RFZO, bez kraja ili sa krajem od danas) |
| Ugovori koji ističu | `hr:ugovor_list` | Ugovori na određeno aktivnih radnika sa krajem u narednih 45 dana, bez kasnijeg ugovora istog radnika |
| Zahtevi koji čekaju rešenje | `hr:zahtev_list` (+ `hr:resenje_list`) | Podneti zahtevi bez nestorniranog rešenja; nacrti zahteva i rešenja; rešenja izdata ovog meseca |
| Moje | — | Moj profil, moja radna lista, zahtevi i rešenja (ako ih korisnik vidi) |

Ruta nema sopstvenu proveru dozvole, kao ni Moj profil i radna lista; zato nema nove dozvole za dodelu.

## 6. Podaci koje korisnik unosi

| Podatak | Ekran | Ko unosi |
|---|---|---|
| **Sati po danima i šiframa posla** | Radna lista | **Zaposleni** — od 07.10.2026. lista se **ne može predati** dok red sa satima rada (redovan, prekovremeni, noćni, rad na praznik ili red bez vrste) nema šifru posla; odsustva (bolovanje, godišnji, plaćeno odsustvo, državni i verski praznik) je ne traže. Čuvanje je dozvoljeno; proveru radi i pregledač pre otvaranja štampe (`hr/services/radna_lista.py`). Na štampi je datum prvi radni dan meseca predaje (mesec posle meseca liste, bez vikenda i praznika) |
| Vrsta rada / odsustva po redu | Radna lista | Zaposleni |
| Topli obrok — broj dana i šifra posla | Radna lista | Zaposleni — **obavezan pri predaji** (i 0 je odgovor); predlog je broj radnih dana sa kucanjem (pon–pet, bez praznika), uz podrazumevanu šifru zaposlenog (od 07.10.2026.) |
| Terenski dodatak — broj dana | Radna lista | Zaposleni (predlaže se iz putnih naloga) |
| Prilozi radne liste (skenirane propusnice, finalna radna lista) | Radna lista, kartica „Prilozi radne liste” | Zaposleni ili kadrovik; PDF/JPG/PNG/TIFF do 20 MB, i posle predaje; odobrena lista ne dozvoljava brisanje |
| **Datum slave** | Izmena zaposlenog, sekcija „Obrazovanje i slava“ | Kadrovska služba; predlaže se iz naziva slave, koriste se dan i mesec |
| Ispravka imena za prikaz | Moj profil | Zaposleni |
| CV stavke | Moj profil | Zaposleni |
| **Bodovi po merilima i komentari** | Ocenjivanje | Neposredni rukovodilac |
| Saglasnost, korekcija koeficijenta, obrazloženje | Saglasnost | Direktor centra, generalni direktor |
| RFZO Excel datoteka i datum izvoza | Uvoz bolovanja | Kadrovska služba |
| **Vrsta zahteva, zaposleni, datum, period ili dani, razlog** | Zahtevi | Kadrovska služba |
| **Ko podnosi i ko odobrava zahtev**, sa funkcijama | Zahtevi | Kadrovska služba |
| Poslovi koje zaposleni preuzima (zamena odsutnog) | Zahtevi, Rešenja | Kadrovska služba |
| Datum rešenja i potpisnik; broj samo za rešenje **bez** zahteva | Rešenja | Kadrovska služba |
| Broj i datum zahteva kao tekst — samo za rešenje bez zahteva | Rešenja | Kadrovska služba |
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
| Obračunati parovi prolazaka | `INFORMATIKA23.ID.dbo.c_parovi_radnika_detalji` + `PUTGEO-SERVER.bazaldims.dbo.radnik` | Komanda `hr_attendance_summary`; kod prebačen 28.09.2026. |
| **Godišnji odmori** | `[putgeo-server].[BazaLDIMS].[dbo].[Godmor]`, `[GodmorKor]` | **Ručno** |
| Vrste primalaca | `dbo.hr_employee` | Uz šifarnik |

> **[P] Zaštita identiteta:** polje `skip_hr_identity_update` sprečava da noćna
> sinhronizacija prepiše titulu, ime, prezime, originalno ime i pol. Pri čuvanju promene
> imena, prezimena ili titule na formi zaposlenog zaštita se uključuje automatski.
> Superuser je može isključiti naknadnim čuvanjem bez promene tih polja. Ispravka
> kvačica na sopstvenom profilu koristi posebna polja za prikaz i ne uključuje ovaj prekidač.

### Osoba i zaposlenja (od 06.10.2026.) [P]

Osobu određuje **JMBG** (`fleet_osoba`), a zaposlenje je **broj radnika u preduzeću** (`fleet_employee`,
jedinstven par `preduzece` + `employee_code`; preduzeće 1 = radni odnos, 2 = van radnog odnosa). Ista osoba
posle ponovnog prijema ili uz rad van radnog odnosa ima više brojeva — sve veze (radne liste, rešenja,
putni nalozi, …) i dalje idu na zaposlenje, a osoba ih objedinjuje.

| Tema | Pravilo |
|---|---|
| Vezivanje | Sinhronizacija veže zaposlenje za osobu po JMBG-u (`hr/services/osobe.py: povezi_osobu`). Bez JMBG-a svako zaposlenje je posebna osoba. |
| Lični podaci osobe | Ime, prezime, titula, pol i datum rođenja iz **glavnog zaposlenja**: aktivno, radni odnos, poslednji prijem (`glavno_zaposlenje`). |
| Ime za prikaz i ćirilica | Pripadaju **osobi**. Izmena na bilo kom zaposlenju upisuje se na osobu i prepisuje na sva njena zaposlenja; novo zaposlenje ih preuzima od osobe. |
| Preduzeće | Pogled `dbo.hr_employee` nema preduzeće — čita se iz `radnik.sif_pred` (`hr/sync.py: preduzeca_radnika`). |
| Neaktivni brojevi | Uvoze se **samo za osobe koje već postoje** (da se vide sve njihove šifre); davno otišli bez aktivnog broja se ne uvoze. |
| Sukobi | Isti broj radnika u oba preduzeća ili različiti redovi istog broja u pogledu — broj se **preskače**, ništa se ne prepisuje; broj se vidi u poruci sinhronizacije. |
| Duplirani redovi pogleda | `dbo.hr_employee` od oktobra 2026. vraća svaki red dvaput (ispravlja vlasnik pogleda); identični redovi se računaju jednom. |
| Nestanak iz izvora | Broj koji nestane iz kadrovske baze dobija `u_izvoru = False`; ne briše se i aktivnost mu se ne menja. |
| Pregled pre izmena | `manage.py kadrovi_osobe_pregled` — samo čita: osobe sa više brojeva, sukobi brojeva, zapisi bez JMBG-a. |
| Detalj zaposlenog | Sve kartice (ugovori, rešenja, zahtevi, radne liste, odmori, putni nalozi, vozila, incidenti, CV) obuhvataju **sva zaposlenja osobe**; kartica „Šifre“ prikazuje sve brojeve; kartica „Bolovanja“ samo uz pravo `hr:sick_leave_list`. Detalj ugovora prikazuje periode pod svim šiframa osobe. Spisak zaposlenih ima jedan red po osobi. |
| Korisnički nalog | **Jedna osoba, jedan nalog** (od 07.10.2026.): `manage.py uskladi_naloge_zaposlenih [--execute] [--i-van-radnog-odnosa]` pravi nalog aktivnoj osobi bez naloga na glavnom zaposlenju (lozinka JMBG, obavezna promena, obuhvat svog centra), prebacuje nalog sa neaktivnog na aktivan broj, deaktivira duple naloge i naloge osoba bez aktivnog zaposlenja (ne briše; superuser se ne dira). Brojevi van kadrovske baze i osobe samo van radnog odnosa ne dobijaju nalog bez posebne opcije. Isto pravilo koriste dugme „napravi profile“ i `create_employee_users`. |
| Ukupan staž | Na osobi (`staz_*`, `staz_ims_*`), računa ga HR sinhronizacija iz `RadStaz` (u IMS `DA` i kod drugih poslodavaca `NE`/`ME`) za sve šifre osobe (`hr/services/osobe.py: obracunaj_staz`). Sabiraju se izvorne vrednosti perioda (30 dana = mesec, 12 meseci = godina, kao kadrovska baza); period bez staža otpada; isti period pod dve šifre računa se jednom (vrednost novije šifre); period ceo unutar dužeg perioda druge šifre se ne računa, osim kad duži nema upisan kraj (3000). |

---

## 8. Tabele i kolone

Detaljno: [4.5. Kadrovi](../04-baza-podataka.md#45-kadrovi--hr). **20 tabela.**

| Tabela | Uloga |
|---|---|
| **`fleet_osoba`** | Osoba — jedinstvena po JMBG-u (od 06.10.2026.) |
| **`fleet_employee`** | Zaposlenje — ključ je `preduzece` + `employee_code`; `osoba` ga veže za osobu |
| `fleet_employee.radna_mesta` | **Sva radna mesta** radnika (od 07.10.2026.): do pet **ravnopravnih**, po rednim brojevima 1–5, iz `radnik.sif_sis` i `sif_sis1`–`sif_sis4`, OJ iz `oj`/`oj1`–`oj4` (prazna `oj1`–`oj4` = `oj`), nazivi iz `Sistemat` i `ob_jedin`. Uz njih se dodaje i **rukovodeće mesto** (`radnik.sif_ruk` → `RukMesto`, npr. „Rukovodilac u laboratoriji”) kao poslednje, sa oznakom „rukovodeće mesto”, osim kad isti naziv već postoji (od 07.10.2026., 24 aktivna zaposlena). Puni ih noćna sinhronizacija Kadrova (`hr/services/radna_mesta.py`); prikaz u detalju zaposlenog (Radni podaci), spisku zaposlenih i Mom pregledu. Stanje 07.10.2026.: od aktivnih 39 ima dva, 13 tri, 6 četiri i 3 pet radnih mesta. Dodatna radna mesta na ugovoru (ručni unos za BZR) ostaju odvojena |
| `fleet_employeecvitem` | CV stavke |
| `hr_worktimesheet`, `hr_worktimesheetline` | Radna lista i redovi (31 kolona sati) |
| `hr_radnalistaprilog` | Prilozi radne liste — skenirane propusnice, finalna potpisana lista, ostalo (`media/hr/radne_liste/`, od 07.10.2026.) |
| `fleet_employee.slava_datum` | Datum krsne slave (koriste se dan i mesec); HR sinhronizacija ga ne menja, naziv slave dolazi iz HR-a |
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
| `hr_vrstazahteva` | Šifarnik obrazaca zahteva — tekstovi ćirilicom, rešenje koje se po zahtevu izdaje |
| `hr_brojaczahteva` | Poslednji dodeljeni redni broj zahteva po godini |
| **`hr_zahtev`** | **Zahtev sa automatskim brojem, podnosiocem, odobravaocem i JSON snimkom** |
| `hr_zahtevdan` | Pojedinačni dani zahteva |

---

## 9. SQL pogledi i povezani serveri

| Objekat | Server | Namena | Status |
|---|---|---|---|
| `dbo.hr_employee` | `IMS_ERP` | Zaposleni | **[N]** Sadržaj nije potvrđen |
| `Radnici`, `C_Prolasci_Radnika`, `C_Tasteri`, `c_parovi_radnika_detalji` | **`INFORMATIKA23.ID`** | Kontrola pristupa | Kolone poznate iz upita |
| `radnik` | **`PUTGEO-SERVER.bazaldims`** | OJ i ime uz parove | SERFIN je ugašen; [provera produkcionog prelaska](../07-integracije.md#7231-provere-nakon-gašenja-serfin-a) |
| `Godmor`, `GodmorKor` | **`PUTGEO-SERVER.BazaLDIMS`** | Godišnji odmori | Kolone poznate |
| `dbo.v_hr_RadStaz` | `IMS_ERP` (čita `RadStaz` sa `PUTGEO-SERVER.bazaldims`) | Periodi rada za ugovore | Od 29.09.2026. [P] |
| `radnik`, `ob_jedin`, `Sistemat` | **`PUTGEO-SERVER.bazaldims`** | Trenutna OJ i radno mesto sa nazivima (ugovori) | Od 29.09.2026. [P] |

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
| **Zahtevi** | [`hr/services/zahtevi.py`](../../../hr/services/zahtevi.py), [`hr/zahtevi_models.py`](../../../hr/zahtevi_models.py) |
| Godišnji odmori | [`hr/services/annual_leave.py`](../../../hr/services/annual_leave.py) |
| Bolovanja | [`hr/services/sick_leave.py`](../../../hr/services/sick_leave.py) |
| Šifarnik radne liste | [`hr/services/work_time_catalog.py`](../../../hr/services/work_time_catalog.py) |
| Sinhronizacija zaposlenih | [`hr/sync.py`](../../../hr/sync.py) |
| Radna lista | [`hr/views.py: MyWorkTimeSheetView`](../../../hr/views.py) |
| **Predlog radne liste** | [`hr/services/work_time_prefill.py`](../../../hr/services/work_time_prefill.py), praznici i slave: [`hr/services/praznici.py`](../../../hr/services/praznici.py) |

Testovi: `hr/tests.py`, `test_annual_leave.py`, `test_evaluations.py`,
`test_sick_leave.py`, `test_work_time_catalog.py`, `test_resenja.py`, `test_zahtevi.py`. [P]

---

## 11. Ulazni i izlazni podaci

| Smer | Šta |
|---|---|
| **Ulaz** | Kadrovska baza, prolasci, godišnji odmori iz zarada, RFZO Excel, Excel šifarnici |
| **Izlaz** | Štampa radne liste i evidencije prolaza kao priloga, **štampa ocene sa tri potpisa** |

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
| **K-10** | **Analitika zaposlenih** (pol, starost, stručna sprema, staž) |

---

## 14. Uloge i prava pristupa

| Dozvola | Šta omogućava |
|---|---|
| `hr:work_time_sheet` | Svoja radna lista (i komentar na prolaze) |
| `hr:analitika` | Analitika zaposlenih, PDF i Excel (od 05.10.2026.). Dobijaju je uloge **Kadrovi** (po obuhvatu) i **Pravna služba** (od 06.10.2026., link u meniju Pravne službe) |
| `hr:rodna_ravnopravnost` | **Statistika rodne ravnopravnosti** (od 07.10.2026.): dugme na Analitici → `/hr/analitika/rodna-ravnopravnost/`, tačke 1–4 i 6 „Obrasca 1” (evidencija o ostvarivanju rodne ravnopravnosti) za izabranu godinu, Excel i PDF. Cela firma (oba preduzeća, osoba jednom po JMBG-u), iz kadrovske baze `radnik` (pol, rođenje, dolazak/odlazak — 01.01.1900. i 3000. znače prazno, `sif_spr` stručna sprema, `sif_ruk` rukovodeće mesto = položaj, `sif_odl` razlog odlaska). Stanje na 31.12. (tekuća godina — danas); sprema i položaj su današnji podaci. Ostale tačke se popunjavaju ručno. Provera za 2024: 312 lica prema 311 u predatom obrascu, 29 prestanaka kao u obrascu. Dobijaju je Kadrovi i Pravna služba (`hr/services/rodna_ravnopravnost.py`) |
| **`hr:analitika_view_all`** | Analitika za **celu firmu**, bez obzira na obuhvat — Pravna služba (`core/permissions.py: PRAVNA_KADROVI_CODES`) i Uprava |
| `hr:sick_leave_list`, `hr:sick_leave_import` | Bolovanja |
| `hr:annual_leave_list` | Godišnji odmori |
| `hr:work_time_catalog` | Šifarnici |
| `hr:evaluation_list`, `hr:evaluation_create`, `hr:evaluation_approve` | Ocenjivanje |
| **`hr:evaluation_view_all`** | Vidi i ocenjuje **sve** zaposlene |
| `hr:resenje_list`, `hr:resenje_create`, `hr:resenje_izdaj` | Rešenja — pregled, unos, izdavanje |
| `hr:resenje_bulk_create`, `hr:resenje_print` | Grupno izdavanje i štampa |
| `hr:resenje_catalog` | Šifarnik vrsta rešenja i potpisnika |
| **`hr:resenje_view_all`** | Vidi rešenja i zahteve **svih** centara |
| `hr:zahtev_list`, `hr:zahtev_create`, `hr:zahtev_bulk_create` | Zahtevi — pregled, unos, isti zahtev za više zaposlenih |
| `hr:zahtev_resenje_create`, `hr:zahtev_bulk_resenja` | Rešenje iz jednog ili više zahteva |
| `hr:zahtev_podnesi`, `hr:zahtev_storniraj`, `hr:zahtev_print` | Zaključavanje, storniranje i štampa zahteva |

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
- Dozvole za zahteve (`hr:zahtev_*`) dobijaju Uprava, Kadrovi i Sekretarijat, isto kao
  operativne dozvole za rešenja. Zahtev je vidljiv po istom pravilu kao rešenje: po
  centru i OJ snimljenim na zahtevu.
- Od 04.10.2026. uloga **Zaposleni** podnosi zahtev **za sebe** (Moj profil → „Podnesi
  zahtev“): pregled, unos, izmena nacrta, štampa i podnošenje (`hr.access.DOZVOLE_ZAHTEVA_ZA_SEBE`),
  bez grupnog unosa, storniranja i rešenja. U formi bira samo sebe, a podnosilac je unapred on sam.
  Ove dozvole **ne daju obuhvat Kadrova** — uloga Zaposleni ima dodelu na ceo svoj centar
  (zbog Flote), a bez izuzetka bi videla sve kolege. Svako vidi zahteve koje je uneo i
  zahteve koji se odnose na njega.

Od 24.09.2026. `hr/access.py` ograničava spisak, detalje i izmenu zaposlenih, radne liste,
odmore, bolovanja i pristup Kadrova ocenjivanju. Kod rešenja proveravaju se i pojedinačni
unos, grupni unos, predlog teksta i snimljene šifre OJ/centra.

> **[P] Od 28.09.2026. Kadrovi su na registru organizacije** (prekidač `PRAVA_PO_REGISTRU["kadrovi"]`).
> Nema posebne kadrovske organizacije: zaposleni pripada **čvoru registra** (`Employee.org_node`),
> koji se izvodi iz OJ kadrovske baze — OJ istog broja kao jedinica → ta jedinica; kao centar →
> centar (`20` → `2`); inače centar po prefiksu (4331 i 4332 → 43, 4110 → 41, 423 → 42); `1` i `10`
> (Institut kao celina) nemaju čvor. Veza se postavlja pri čuvanju i noću u 01:40 (361 od 371
> zaposlenog vezano 28.09.2026.). Obuhvat daju odobrene dodele uloga sa dozvolama `hr:…` ili
> `employee_…`: dodeljen centar daje sve svoje jedinice, šifra posla ne daje ljude. „Sva rešenja”
> i „sva ocenjivanja” su obuhvat cele firme. Merenje 28.09.2026.: 18 korisnika sa spiskom
> zaposlenih vidi isto kao ranije, osim Uprave, koja sada vidi sve zaposlene (odluka 28.09.2026.).

Ograničenja podataka ne menjaju obračune
ni pravilo da saglasnost na ocenu daje imenovani ocenjivač.

### Forme Kadrova u sekcijama

Sve forme za unos u Kadrovima imaju isti raspored (`hr/templates/hr/forms/base.html`,
stilovi `hr/static/hr/forme.css`, ponašanje `hr/static/hr/forme.js`):

- polja su podeljena u **sekcije**; svaka sekcija ima kratak opis i dugme **Uputstvo** koje klizno
  otvara objašnjenje, a sva uputstva su zajedno u prozoru „Uputstvo“ u zaglavlju;
- **kartica „Sekcije forme“ desno** ostaje na ekranu pri pomeranju, pokazuje sekciju koja se gleda
  i broj grešaka po sekciji; sekcija koja se sakrije (npr. „Pojedinačni dani“ kada ih izabrana vrsta
  rešenja ne traži) nestaje i iz kartice; forma sa jednom sekcijom nema karticu;
- da/ne polja su **prekidači**; polja koja HR sinhronizacija prepisuje nose oznaku **„iz HR-a“**;
- traka **Odustani / Sačuvaj** stoji na dnu ekrana.

Od 04.10.2026. korisnik koji nije superuser na **izmeni zaposlenog** uređuje samo ime,
prezime, titulu, ime i prezime za prikaz, ime ćirilicom i datum slave. Ostali podaci
(uključujući šifru zaposlenog) prikazani su informativno ispod forme i ne prihvataju
izmene ni iz ručno izmenjenog POST zahteva. Promena imena, prezimena ili titule
automatski uključuje zaštitu identiteta od HR sinhronizacije. Stara korekcija za prikaz
promenjenog imena uklanja se ako korisnik nije istovremeno izmenio i tu korekciju.
Promene samo lokalnih podataka ne uključuju zaštitu. Superuser zadržava punu formu;
unos novog zaposlenog i dozvole/obuhvat zaposlenih ostaju po postojećim pravilima.
Polja za unos su na vrhu ekrana, uz kratko obaveštenje o zaštiti imena. Pregled ispod
forme razdvaja lične podatke, zaposlenje i organizaciju, podatke za obračun, kontakt i
adresu, obrazovanje i slavu. Svaka celina ima opis i parove naziv–vrednost; crtica
označava podatak koji nije unet. Osnovno ime i opciono ime za prikaz imaju odvojena objašnjenja.

Forma navodi sekcije u `SECTIONS` (`hr/form_layout.py: SekcijeMixin`): oznaka, naslov, opis, polja,
uputstvo i ikonica. Polje koje nije razvrstano ide u „Ostalo“, pa novo polje modela ne nestaje iz
forme; forma bez `SECTIONS` prikazuje se kao jedna sekcija. Posebni delovi (tabela dana, spisak
zaposlenih, merila ocenjivanja) prave se oznakom `{% sekcija %}` iz `hr_forme`.

Na ovaj način su uređene: zaposleni (unos i izmena), ispravka imena, stavka CV-a, uvoz bolovanja,
šifarnici elemenata radne liste i ocenjivanja, obrazac ocenjivanja, rešenje, zahtev, isti zahtev za
više zaposlenih i šifarnik rešenja (vrste rešenja i zahteva, potpisnici, brojač). Radna lista je
tabela za unos sati i ima svoj raspored.

### Zahtev → rešenje

Od 24.09.2026. rešenje se pravi **iz zahteva**:

1. Kadrovik unosi zahtev (**Zahtevi → Novi zahtev**) ili isti zahtev za više zaposlenih
   odjednom. Svaki zaposleni dobija **svoj zahtev i svoj broj**.
2. Broj se dodeljuje **automatski**, u obliku `{centar}-{redni broj}` (npr. `43-17`).
   Redni broj je jedan niz za ceo Institut i počinje od 1 svake godine, kao u delovodniku.
   Početak niza se podešava u **Šifarnik → Brojač zahteva** (npr. da se nastavi na
   postojeći delovodnik); brojač ne može da ide unazad.
3. U zahtev se upisuje **ko podnosi** (zaposleni i funkcija, npr. „Финансијски директор“)
   i **ko odobrava**. Ako „ko odobrava“ ostane prazno, uzima se potpisnik rešenja koji
   važi na datum zahteva. Zahtev se štampa kao dopis sa oba potpisa.
4. Na detalju zahteva **Dodaj rešenje iz zahteva** pravi nacrt rešenja sa istim
   zaposlenim, periodom, danima, vremenom i dodatnim podacima. Iz liste zahteva može se
   napraviti rešenje za više označenih zahteva odjednom; zahtev koji već ima rešenje se
   preskače.
5. Rešenje dobija broj kao **podbroj zahteva**: `43-17/1`. Važi **jedan zahtev — jedno
   rešenje**, uključujući stornirano rešenje. Broj, zaposleni i podaci o zahtevu se ne menjaju ručno.
6. Rešenje i zahtev su povezani u oba smera: detalj rešenja vodi na zahtev, a detalj
   zahteva prikazuje povezano rešenje. Dok ga nema, prikazuje dugme **Dodaj rešenje**.
   Profil zaposlenog ima karticu „Zahtevi“.

Pravila [P]:

- Zahtev se ne briše, nego **stornira**; broj storniranog zahteva se ne koristi ponovo.
  Ni obrisan nacrt rešenja ne vraća svoj podbroj.
- Zahtev koji ima rešenje koje nije stornirano ne može da se stornira.
- **Podnošenje** zaključava tekst zahteva (JSON snimak). Zahtev se zaključava i sam, kada se
  izda prvo rešenje po njemu.
- Od 04.10.2026. zahtev se **ne menja čim po njemu postoji rešenje**, i dok je rešenje još
  nacrt (`Zahtev.je_zakljucan`). Ispravka ide preko rešenja; tek kad se nacrt rešenja obriše,
  zahtev se ponovo može menjati.
- Rešenje mora biti povezano sa postojećim zahtevom. Baza odbija praznu ili duplu vezu.
  Stari linkovi za samostalni i grupni unos vode na listu zahteva bez rešenja.
- Zamena odsutnog zaposlenog je **rešenje** („Imenovanje lica za zamenu“ → „Rešenje o zameni
  odsutnog zaposlenog“). Poslovi koje zaposleni preuzima unose se kao dodatno polje.
- Vrste rešenja i zahteva mogu imati **dodatna polja** (`oznaka|Naziv`), koja se u tekstu
  koriste kao `{oznaka}`. Polje koje izabrana vrsta traži je obavezno.

### Unos i štampa rešenja zaposlenih

- Pol za tekst se preuzima iz evidencije (ženske oznake `F`, `Z`, `Ž` i `Ж` se
  prepoznaju jednako), uz mogućnost izbora oblika za konkretno rešenje. Izbor se čuva
  u nacrtu, a izdati dokument ostaje sačuvan u svom snimku.
- OJ se automatski bira prema zaposlenom. Izbor druge OJ ograničen je korisnikovim
  obuhvatom. Ako nema naziva u šifrarniku, predlaže se „OJ <šifra>“, koji se može
  tekstualno dopuniti. Centar se izvodi postojećim mapiranjem OJ na centar.
- Period od–do dostupan je za sve vrste; kod praznika ostaju obavezni pojedinačni
  dani sa vrstom praznika. Za rad se može uneti vreme smene od–do; završetak pre
  početka označava naredni dan. Rešenje automatski preuzima broj i datum povezanog zahteva.
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
