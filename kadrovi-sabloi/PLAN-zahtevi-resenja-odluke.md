# Plan proširenja kadrovskih akata: Zahtev → Rešenje / Odluka

Datum: 24.09.2026.
Status: **faza 1 implementirana 24.09.2026.** (zahtev → rešenje), uz sledeće odluke:

| Pitanje | Odluka |
|---|---|
| Jedan zahtev — jedan ili više zaposlenih | **Jedan zaposleni.** Za više zaposlenih pravi se više istih zahteva odjednom, svaki sa svojim brojem |
| Broj zahteva | **Automatski**, `{centar}-{redni broj u godini}`; početak niza podesiv u šifarniku |
| Broj rešenja (P-5) | **Podbroj zahteva**: `43-17/1`, `43-17/2` |
| Ko podnosi i ko odobrava (P-1) | Upisuje se **u samom zahtevu** (zaposleni + funkcija); bez toka odobravanja za sada |
| Zamena odsutnog zaposlenog (P-3) | **Rešenje** |
| Godišnji odmori (P-4) | Otvoreno — ostaju kako jesu |
| Zahtev u šemi | Bez stavki: `ZahtevStavka` iz odeljka 3.1 nije potrebna, jer je zaposleni na samom zahtevu |

Obrasci zahteva napravljeni su za svih 7 postojećih vrsta rešenja i za zamenu, po uzoru na
„Zahtev za prekovremeni — Jasmina Ljubičić“ i „Imenovanje lica za zamenu“. Odluke (naknada
štete, umanjenje zarade) i službeni put još nisu u šifarniku; mehanizam dodatnih polja koji
im treba (iznos, mesec obustave, odredište) već postoji.
Veza: [Plan modula Arhiva](../../../aRhiva-docs/PLAN-implementacije-modula-Arhiva.md) (delovodni broj i arhiviranje).

Izvori:

| Izvor | Šta iz njega uzimamo |
|---|---|
| `kadrovi-sabloi/` (6 × `.doc`, 1 × `.docx`) | Tekstovi 7 postojećih vrsta rešenja. Svako obrazloženje se poziva na zahtev. |
| Kod: `hr/resenja_models.py`, `hr/services/resenja.py`, `hr/resenja_views.py`, `hr/resenja_forms.py`, migracija `0014` | Šta aplikacija danas radi sa rešenjima. |
| `Delovodnik 2024.xlsx` (15.056 upisa) | Koje zahteve, rešenja i odluke kadrovska stvarno izdaje i koliko ih ima godišnje. |

---

## 1. Polazno stanje

### 1.1 Šta aplikacija već ima (i to ostaje)

- **Šifarnik vrsta rešenja** (`VrstaResenja`). Tekstovi su ćirilicom, sa čuvarima mesta (`{zaposleni}`, `{period}`, `{rod:дужан|дужна}`, `[[uslov|tekst]]`). Latinica nastaje preslovljavanjem.
- **Potpisnik po periodu važenja** (`Potpisnik.za_datum`).
- **Rešenje sa tokom nacrt → izdato → stornirano.** Pri izdavanju se tekst zaključava u JSON snimak (`Resenje.dokument`).
- Pojedinačni i grupni unos, štampa (i grupna), kartica „Rešenja" na profilu zaposlenog, ograničenje po centru i OJ (`hr/access.py`, `visible_resenja`).
- U šifarniku je 7 vrsta: noćni rad, prekovremeni, prekovremeni i vikend, praznik, vikend, prekovremeni + vikend + smene, plaćeno odsustvo zbog davanja krvi.

### 1.2 Šta nedostaje

1. **Zahtev ne postoji kao zapis.** `Resenje.zahtev_broj` i `zahtev_datum` su slobodan tekst koji kadrovik prepisuje sa papira. Iz aplikacije se zato ne vidi:
   - koji zahtevi još čekaju rešenje,
   - koja rešenja pripadaju istom zahtevu,
   - ko je zahtev podneo i odobrio,
   - da li je rešenje izdato bez ikakvog zahteva.
2. **Odluke ne postoje.** U 2024. ih je zavedeno oko 187. Najčešće su: zamena zaposlenog (56), isplata jubilarne nagrade (19), umanjenje zarade, bonus i imenovanje.
3. **Šifarnik ne pokriva vrste koje se najviše izdaju** (odeljak 1.4).
4. **Primer u polju za broj rešenja je pogrešan.** Help text za `Resenje.broj` kaže „npr. 43-15238". U obrascu je `43-15238` broj **zahteva** („на основу захтева бр. 43-15238"), a broj samog rešenja u obrascima je prazan („Бр. _______"). I zahtev i rešenje dobijaju svoj broj iz delovodnika.

### 1.3 Šta obrasci govore o zahtevu

| Obrazac | Obrazloženje | Ko podnosi |
|---|---|---|
| Noćni rad | „Dana 06.03.2020 podnet je zahtev br. 42-2883 … kojim se traži angažovanje zaposlenog" | Centar (42) |
| Prekovremeni | „Zbog potrebe posla, a na osnovu zahteva br. 41-6279 od 29.05.2023" | Centar (41) |
| Prekovremeni i vikend | „Na osnovu zahteva br. 20-2907 dostavljenog dana 20.03.2026" | OJ 20 |
| Praznik | „Na osnovu zahteva br. 43-15238 dostavljenog dana 27.12.2024" | Centar (43) |
| Vikend | „… a na osnovu zahteva br. 82-6992 od 18.06.2026" | Služba (82) |
| Smene | „Dana 23.06.2016 podnet je zahtev br. 82-9187 … angažovanje … na sređivanju i praćenju zapaljivosti uglja" | Služba (82); **razlog je deo teksta** |
| Plaćeno odsustvo (krv) | „Zaposleni je dana 20.08.2026 podneo potvrdu Instituta za transfuziju krvi" | **Sam zaposleni**, sa prilogom |

Zaključci:

- **Zahtev ima broj iz delovodnika** u obliku `{OJ}-{redni broj}`.
- Zahtev podnosi **organizaciona jedinica** (rukovodilac) za svoje zaposlene. Kod odsustva ga podnosi **sam zaposleni**, uz dokaz.
- **Razlog zahteva** („potreba posla", opis angažovanja) ulazi u obrazloženje rešenja.

### 1.4 Šta kadrovska stvarno izdaje (delovodnik 2024, zbirno)

| Akt | Broj u 2024 | U aplikaciji danas |
|---|---|---|
| Rešenje za godišnji odmor | ~510 | Samo preslikano iz obračuna zarada (`AnnualLeaveDecision`), bez teksta |
| Rešenje za prekovremeni rad i rad vikendom (mesečno, po centru) | ~430 | ✔ |
| Rešenje za službeni put u inostranstvo | 140 | ✘ |
| Rešenje o plaćenom odsustvu | ~66 | Samo za davanje krvi |
| Rešenje o zameni odsutnog zaposlenog | ~59 | ✘ |
| **Odluka o zameni zaposlenog** | 56 | ✘ (isti slučaj ide nekad kao rešenje, a nekad kao odluka) |
| Rešenje o isplati solidarne pomoći | 24 | ✘ |
| **Odluka o isplati jubilarne nagrade** | 19 | ✘ |
| Rešenje za rad na državni praznik, rad vikendom | ~40 | ✔ |
| Rešenje o imenovanju / odluka o imenovanju | ~20 | ✘ |
| Odluke o umanjenju zarade, bonusu, komisijama i ekipama | ~15 | ✘ |
| **Zahtevi**: produženje radnog odnosa 154, zamena odsutnog 32, plaćeno odsustvo 23 (+ 8 molbi), prekovremeni ili vikend oko 70 (+ mnogo upisa samo „Zahtev"), jubilarna 4, promena radnog mesta 4 | — | ✘ |
| Ostali kadrovski akti: ugovor o radu 304, obaveštenje o isteku radnog odnosa ~275, otkaz ugovora o radu 132, potvrda o zaposlenju ili zaradi ~55, aneksi i sporazumi o prestanku | — | ✘ (van ovog plana, odeljak 8) |

Iz brojeva sledi i ovo: upisi kao „Rešenje za prekovremeno i rad vikendom februar 2024" (95 u jednom mesecu) pokazuju da **jedan mesečni zahtev centra daje desetine rešenja**. Zahtev zato mora da pokrije više zaposlenih.

---

## 2. Ciljni tok

```
               ┌──────────── (kasnije: elektronski podnosi rukovodilac ili zaposleni) ────────────┐
               ▼                                                                                   │
ZAHTEV  nacrt → podnet → odobren ─┬─► stavka 1 (zaposleni A) ──► REŠENJE / ODLUKA  nacrt → izdato
 broj 43-15238 (delovodnik)       ├─► stavka 2 (zaposleni B) ──► REŠENJE / ODLUKA  nacrt → izdato
 vrsta, razlog, period, prilozi   └─► stavka 3 (odbijena)
                  │
                  └─ odbijen / povučen
Zahtev je REŠEN kada svaka stavka ima izdat akt ili je odbijena.
Storno akta vraća stavku u „otvorena".
```

Tri principa:

1. **Zahtev je poseban zapis**, a rešenje ili odluka se **pravi iz njega**. Podaci o zaposlenom, periodu, danima i razlogu prelaze u nacrt automatski, pa se ne kucaju dvaput.
2. **Rešenje i odluka koriste isti mehanizam.** Šifarnik obrazaca, čuvari mesta, snimak, storno, štampa i potpisnik su isti. Razlikuje ih samo **tip akta** u vrsti. Odluka ne dobija novi model ni kopiju koda.
3. **Stara rešenja ostaju važeća.** Veza sa zahtevom je opciona u bazi. Obaveza postoji samo za vrste gde se tako podesi, i važi od dana uključenja.

---

## 3. Model podataka

### 3.1 Novo: zahtevi (`hr/zahtevi_models.py`, uvoz u `hr/models.py` kao kod rešenja)

**`VrstaZahteva`** (šifarnik; kadrovik ga uređuje bez izmene koda)

| Polje | Svrha |
|---|---|
| `kod`, `naziv`, `redosled`, `je_aktivna` | kao u `VrstaResenja` |
| `podnosilac` | `oj` (rukovodilac za svoje zaposlene) / `zaposleni` (za sebe) / `kadrovska` |
| `vise_zaposlenih` | Da li jedan zahtev pokriva više zaposlenih (prekovremeni: da; plaćeno odsustvo: ne) |
| `trazi_period`, `trazi_dane`, `trazi_radne_dane` | Isto značenje kao u `VrstaResenja`, da forma sakrije polja koja se ne traže |
| `trazi_razlog`, `trazi_prilog` | Npr. „smene" traži opis angažovanja; „davanje krvi" traži potvrdu |
| `vrste_akata` (M2M → `VrstaResenja`) i `podrazumevana_vrsta_akta` | Koji akti mogu da nastanu iz zahteva. Npr. „zamena odsutnog" može dati rešenje ili odluku. |
| `trazi_odobrenje` | Da li zahtev mora biti odobren pre obrade (faza 3) |

**`Zahtev`**

| Polje | Svrha |
|---|---|
| `vrsta` | FK `VrstaZahteva` |
| `broj`, `datum_zahteva` | Broj iz delovodnika (`43-15238`). Unosi se ručno dok ne postoji Arhiva, a posle ga daje Arhiva. Unique (`broj`, `datum_zahteva`), kao kod rešenja. |
| `podnosilac` | FK `fleet.Employee` (rukovodilac ili sam zaposleni) |
| `oj_kod`, `centar` | Snimak, kao u `Resenje`. Po ovim poljima radi ograničenje vidljivosti. |
| `razlog` | Tekst koji ulazi u obrazloženje (`{razlog_zahteva}`) |
| `datum_od`, `datum_do`, `do_zavrsetka_posla` | Podrazumevani period za sve stavke |
| `status` | `nacrt` / `podnet` / `odobren` / `u_obradi` / `resen` / `odbijen` / `povucen` |
| `odobrio`, `odobreno_at`, `razlog_odbijanja` | faza 3 |
| `napomena`, `created_by`, `created_at`, `updated_at` | |

**`ZahtevStavka`** (jedan zaposleni u zahtevu)

| Polje | Svrha |
|---|---|
| `zahtev`, `zaposleni` | Unique (`zahtev`, `zaposleni`) |
| `datum_od`, `datum_do`, `broj_radnih_dana`, `napomena` | Prazno znači da važi period iz zahteva |
| `status` | `otvorena` / `odbijena` / `resena` (izvodi se iz akta) |

**`ZahtevDan`**: isto kao `ResenjeDan` (`datum`, `vrsta_dana`), vezan za stavku. Iz njega se pune dani rešenja.

**`ZahtevPrilog`**

| Polje | Svrha |
|---|---|
| `fajl` | `upload_to='hr/zahtevi/%Y/%m/'`. Preuzima se **samo kroz view sa proverom** vidljivosti zahteva, nikad direktnim `/media/` linkom. |
| `naziv`, `originalni_naziv`, `uploaded_by`, `uploaded_at` | Npr. potvrda Instituta za transfuziju |

### 3.2 Izmene postojećih modela (male i unazad kompatibilne)

**`VrstaResenja`** dobija:

| Polje | Vrednosti | Podrazumevano |
|---|---|---|
| `tip_akta` | `resenje` / `odluka` | `resenje` (svih 7 postojećih vrsta ostaje isto) |
| `zahtev_obavezan` | bool: izdavanje traži vezu sa zahtevom | `False`. Uključuje se po vrsti kada se pređe na novi tok. |

**`Resenje`** dobija:

| Polje | Svrha |
|---|---|
| `zahtev` | FK `Zahtev`, `null=True`, `on_delete=PROTECT` |
| `zahtev_stavka` | OneToOne `ZahtevStavka`, `null=True`, `PROTECT`. Jedna stavka daje jedan akt; posle storna se veza oslobađa za novi akt. |

`zahtev_broj` i `zahtev_datum` **ostaju**. Kada postoji veza, popunjavaju se iz zahteva i u formi su samo za čitanje. Bez veze (stara rešenja) rade kao danas.

**Zašto se model `Resenje` ne preimenuje u „KadrovskiAkt":** `hr_resenje`, JSON snimci, testovi i dozvole `hr:resenje_*` već postoje. Preimenovanje tabele i ruta daje veliku izmenu bez koristi za korisnika. U korisničkom interfejsu se piše „Rešenja i odluke", a u kodu ostaje `Resenje` sa poljem `vrsta.tip_akta`. Ako se kasnije odluči drugačije, to je zaseban i čisto tehnički korak.

### 3.3 Novi čuvari mesta u obrascima

| Čuvar | Vrednost |
|---|---|
| `{razlog_zahteva}` | `Zahtev.razlog` |
| `{podnosilac}` | ime podnosioca (ćirilica ili latinica prema pismu akta) |
| `{zahtev_vrsta}` | naziv vrste zahteva |
| `{zahtev_broj}`, `{zahtev_datum}` | postoje već, a sada se pune iz zahteva |

`build_document` ostaje `schema: 1` jer se samo dodaju ključevi. Već izdata rešenja se prikazuju iz svog snimka i na njih izmena ne utiče.

---

## 4. Servisi (`hr/services/zahtevi.py`) i izmene u `hr/services/resenja.py`

| Funkcija | Šta radi |
|---|---|
| `pripremi_zahtev(zahtev)` | Snimak OJ i centra podnosioca, isto kao `pripremi_resenje` |
| `podnesi_zahtev`, `odobri_zahtev`, `odbij_zahtev`, `povuci_zahtev` | Prelazi statusa sa proverom da je prelaz dozvoljen |
| `napravi_akte(zahtev, *, vrsta_akta, datum, brojevi, pismo, user, stavke=None)` | Za svaku otvorenu stavku pravi **nacrt** `Resenje`. Popunjava zaposlenog, period i dane iz stavke ili zahteva, `zahtev_broj`, `zahtev_datum` i napomenu, pa poziva postojeći `pripremi_resenje()`. Vraća listu nacrta. Zamenjuje ručni deo grupnog unosa. |
| `uskladi_status(zahtev)` | `u_obradi` čim postoji nacrt; `resen` kada su sve stavke rešene ili odbijene. Poziva se iz `izdaj_resenje` i `storniraj_resenje`. |
| `otvoreni_zahtevi(user)` | Red za obradu kadrovske, sa istim ograničenjem po centru kao `visible_resenja` |
| `visible_zahtevi(user)` | Isti obrazac kao `visible_resenja`: centar ili OJ iz `hr/access.py` |

Izmene u postojećem servisu:

- `izdaj_resenje`: ako je `vrsta.zahtev_obavezan`, a nema ni `zahtev` ni `zahtev_broj`, javlja se greška. Posle izdavanja poziva se `uskladi_status`.
- `storniraj_resenje`: stavka se vraća u `otvorena`, a status zahteva se preračunava.
- `build_document`: novi čuvari mesta iz odeljka 3.3.

---

## 5. Ekrani i dozvole

| Ruta (= kod dozvole) | Ekran |
|---|---|
| `hr:zahtev_list` | Lista zahteva: filteri po vrsti, statusu, centru i godini; kartica „čeka obradu" |
| `hr:zahtev_create`, `hr:zahtev_edit` | Unos: vrsta, broj i datum, podnosilac, razlog, period, izbor više zaposlenih (kao u grupnom rešenju), dani, prilozi |
| `hr:zahtev_detail` | Zahtev, stavke sa statusom i linkom na rešenje, prilozi, istorija; dugme **„Napravi rešenja / odluke"** |
| `hr:zahtev_napravi_akte` | Izbor vrste akta (samo dozvoljene za vrstu zahteva), datum, pismo i broj za svaku stavku, zatim grupni nacrti |
| `hr:zahtev_podnesi`, `hr:zahtev_odobri`, `hr:zahtev_odbij`, `hr:zahtev_povuci` | Promene statusa (POST) |
| `hr:zahtev_prilog` | Zaštićeno preuzimanje priloga |
| `hr:zahtev_catalog…` | Vrste zahteva, u postojećem šifarniku rešenja kao nova kartica |

Izmene na postojećim ekranima:

- **Bočni meni** (`templates/sidebar_kadrovi.html`): „Zahtevi" i „Rešenja i odluke" umesto samo „Rešenja zaposlenih".
- **Lista rešenja**: filter po tipu akta (rešenje / odluka) i po tome da li je akt vezan za zahtev.
- **Forma rešenja**: polje „Zahtev" (samo otvorene stavke izabranog zaposlenog) popunjava period i dane.
- **Detalj rešenja**: link ka zahtevu.
- **Grupno izdavanje**: ostaje za prelazni period. Glavni put postaje „iz zahteva".
- **Profil zaposlenog** (`employee_detail.html`): nova kartica „Zahtevi", a kartica „Rešenja" prikazuje i odluke.

**Dozvole:**

- Nove rute se automatski skupljaju kroz `collect_kadrovi_permission_codes()`.
- Namenska sinhronizacija rešenja filtrira samo `hr:resenje_*` (`collect_resenja_permission_codes`, `RESENJA_ADMIN_CODES`), pa je treba **proširiti na `hr:zahtev_*`**, uz to da šifarnik vrsta zahteva ostane „samo Uprava".
- Uloga **Kadrovik — rešenja** dobija operativne dozvole za zahteve.
- U fazi 3 dolazi nova uloga **Rukovodilac — zahtevi**: podnošenje i odobravanje samo za sopstveni centar.

---

## 6. Faze

### Faza 0 — Priprema (bez koda)
- **Prvo commit-ovati tekući rad na obuhvatu pristupa.** Trenutno nisu commit-ovani `hr/access.py`, `core/user_access.py`, migracija `0081_customuser_allowed_hr_unit_codes` i izmene u `hr/resenja_views.py` i `hr/services/resenja.py`. Novi plan se oslanja na te funkcije.
- Od kadrovske preuzeti **Word obrasce** za vrste koje nedostaju (odeljak 1.4) i **papirni obrazac zahteva** ako postoji.
- Odgovoriti na pitanja iz odeljka 9, najmanje P-1 do P-5.

### Faza 1 — Zahtev kao zapis i akti iz zahteva *(najveća korist)*
- Modeli iz 3.1, polja iz 3.2, migracija (sa početnim šifarnikom vrsta zahteva za 7 postojećih vrsta rešenja), servisi iz odeljka 4, ekrani iz odeljka 5 (bez odobravanja).
- Kadrovska unosi papirni zahtev kada stigne iz pisarnice i iz njega pravi nacrte.
- Ispraviti help text `Resenje.broj`: broj rešenja iz delovodnika, bez primera koji je zapravo broj zahteva.
- **Testovi:**
  - zahtev sa 3 stavke daje 3 nacrta sa ispravnim periodom i danima;
  - stavka ne može dobiti drugi akt dok prvi nije storniran;
  - storno vraća stavku u „otvorena";
  - status zahteva prati akte;
  - ograničenje po centru važi za zahteve kao i za rešenja;
  - prilog bez dozvole daje 403 ili 404;
  - **svi postojeći testovi u `hr/test_resenja.py` prolaze bez izmene.**

### Faza 2 — Odluke i nove vrste akata
- `tip_akta` u šifarniku, oznaka u listama i na štampi.
- Nove vrste, **redom po broju u 2024**:
  1. službeni put u inostranstvo;
  2. plaćeno odsustvo po svim osnovima (proširenje današnjeg obrasca za davanje krvi; vidi P-8);
  3. zamena odsutnog zaposlenog (rešenje ili odluka, prema P-3);
  4. solidarna pomoć;
  5. jubilarna nagrada (odluka);
  6. imenovanje;
  7. umanjenje zarade i bonus (odluke).
- Za svaku novu vrstu i odgovarajuća vrsta zahteva.
- Tekstovi idu **podacima u šifarnik** (kao migracija `0014`), ne kodom. Ako obrazac traži nov podatak (npr. zemlja i svrha službenog puta, iznos solidarne pomoći, zaposleni koga zamenjuje), dodaje se kao **opšte polje sa čuvarom mesta**, a ne kao posebno polje za jednu vrstu. Predlog: `Resenje.dodatni_podaci` (JSON) i `VrstaResenja.dodatna_polja` (spisak naziva, oznaka i tipova polja koja forma prikazuje).
- **Iznosi** (solidarna pomoć, jubilarna nagrada, umanjenje zarade) se **ne računaju u aplikaciji**. Unose se kako ih odobri nadležni, jer bi obračun bio nova formula (AGENTS.md, pravilo 5).

### Faza 3 — Elektronsko podnošenje i odobravanje
- **Rukovodilac OJ** podnosi zahtev za svoje zaposlene u aplikaciji (samo svoj centar) i prati status.
- **Zaposleni** podnosi zahtev za sebe (plaćeno odsustvo) i prilaže dokaz. Za to su potrebni korisnički nalog povezan sa zaposlenim (`CustomUser.employee`) i ekran „Moji zahtevi".
- Odobravanje (`trazi_odobrenje`), pa red „Zahtevi za obradu" u kadrovskoj.
- Obaveštenja su u samoj aplikaciji, jer sistem nema slanje e-pošte.

### Faza 4 — Kontrola: radna lista ↔ rešenja
- Izveštaj „rad bez rešenja": dani i sati prekovremenog rada, rada vikendom, praznikom i noću u radnoj listi (`WorkTimeSheetLine` + `WorkTimeCategory`) za koje ne postoji izdato rešenje. Obrnuto: „rešenje bez rada".
- Rešenje kaže „što se dokazuje potpisanom radnom listom", pa je ovo prirodna provera pre obračuna.
- **Samo izveštaj.** Ne menja obračun zarade i ništa ne blokira, osim ako se tako izričito odluči (P-9).
- Potrebno je mapiranje `WorkTimeCategory` → `ResenjeDan.VrstaDana`, koje uređuje kadrovik.

### Faza 5 — Veza sa modulom Arhiva
- Kada Arhiva bude spremna (njena faza 3), dugme „Zavedi u delovodnik" na zahtevu i na rešenju upisuje broj u `Zahtev.broj` i `Resenje.broj`. Tada prestaje ručno prepisivanje.
- Da li je rešenje **podbroj** zahteva (`43-15238/2`) ili ima svoj broj, zavisi od odluke P-5 i od pitanja P-1 u planu Arhive.
- Predlog kategorija iz Liste: 57 rešenja iz radnog odnosa (trajno), 62 prekovremeni i raspored radnog vremena (3 g.), 63 godišnji odmor (2 g.), 64 plaćeno ili neplaćeno odsustvo (3 g.), 24 pasoš za službeni put (3 g.), 29/33 novčane nagrade (trajno).

### Faza 6 — Kasnije, van ovog plana (odeljak 8)

---

## 7. Šta se ne dira

- **Godišnji odmori** ostaju preslikani iz obračuna zarada (`AnnualLeaveDecision`), osim ako P-4 odluči drugačije. U aplikaciji se ne pravi drugi izvor istine za broj dana odmora.
- Disciplinski postupci ostaju u `pravna`. Mehanizam obrazaca bi kasnije mogao da štampa i disciplinske odluke, ali to je posebna odluka.
- Obračun zarada, elementi radne liste i nasleđeni `dbo.*` pogledi ostaju kakvi jesu.

---

## 8. Mogući nastavak (drugi kadrovski akti iz delovodnika 2024)

| Akt | Godišnje | Napomena |
|---|---|---|
| Potvrda o zaposlenju ili zaradi | ~55 | Najlakše: svi podaci postoje u kadrovskoj evidenciji. Isti mehanizam obrazaca, `tip_akta = potvrda`. |
| Obaveštenje o isteku radnog odnosa | ~275 | Traži podatak o datumu isteka ugovora, koji aplikacija danas nema (vidi ugovor o radu). |
| Otkaz ugovora o radu, sporazum o prestanku | ~140 | Pravno osetljivo; zajedno sa pravnom službom |
| Ugovor o radu i aneksi | ~320 | Poseban projekat: evidencija ugovora o radu (vrsta, trajanje, radno mesto, zarada) |
| Zahtev za produženje radnog odnosa (154) | — | Vrsta zahteva čiji je ishod aneks ili ugovor, a ne rešenje; dolazi uz projekat ugovora o radu |
| Opšte odluke (neradni dan, komisije, ekipe za vanredne situacije) | ~20 | Nemaju jednog zaposlenog; traže listu lica sa ulogama (P-6) |

---

## 9. Pitanja za kadrovsku službu i Upravu

| # | Pitanje | Na šta utiče |
|---|---|---|
| P-1 | Ko podnosi zahtev za prekovremeni i vikend rad (rukovodilac, direktor centra) i da li ga neko odobrava pre kadrovske? | Faza 3, uloge |
| P-2 | Da li jedan zahtev centra pokriva **više zaposlenih za ceo mesec**? Delovodnik 2024 to nagoveštava. | `vise_zaposlenih` |
| P-3 | Zamena odsutnog zaposlenog: **rešenje ili odluka**? U 2024. ima i jednih (59) i drugih (56). | Šifarnik |
| P-4 | Da li rešenja za godišnji odmor (~510 godišnje) ostaju u programu za obračun zarada ili se izdaju ovde? | Obuhvat faze 2 |
| P-5 | Da li rešenje dobija svoj delovodni broj ili podbroj zahteva? | Faza 5, Arhiva |
| P-6 | Da li opšte odluke (neradni dan, komisije) pripadaju kadrovskoj ili Upravi? | Odeljak 8 |
| P-7 | Word obrasci za: službeni put, zamenu, solidarnu pomoć, jubilarnu nagradu, imenovanje, umanjenje zarade, ostale osnove plaćenog odsustva, i obrazac zahteva ako postoji | Faza 2 |
| P-8 | Spisak osnova za plaćeno odsustvo i broj dana za svaki (Pravilnik o radu, čl. 19) | Da li se broj dana predlaže automatski (pravilo → pisana potvrda) |
| P-9 | Da li radna lista sa prekovremenim radom može da se potvrdi bez rešenja? | Faza 4: samo izveštaj ili blokada |
| P-10 | Kada je zahtev odbijen, da li se piše akt (obaveštenje podnosiocu)? | Status `odbijen` i štampa |
