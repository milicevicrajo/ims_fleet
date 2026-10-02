# 3.1. Vozni park (Flota)

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Flota** / „Vozni park“ |
| Tehnički naziv | Django aplikacija `fleet` |
| Adresa | `/` — **korenska aplikacija sistema** |
| Bočni meni | `sidebar_fleet.html` |

> **[P]** `fleet` je i korenska aplikacija: njen `urls.py` drži prijavu, odjavu,
> kontrolnu tablu, korisnike, evidenciju rada i istoriju pozadinskih poslova.

---

## 2. Poslovna namena

Vodi **ceo životni ciklus vozila** — od nabavke do otpisa:

1. **Ko je vlasnik ili po kom ugovoru se vozilo koristi** i u kom periodu.
2. **Kojoj organizacionoj jedinici vozilo pripada** u kom periodu.
3. **Koliko vozilo košta** — evidentirani troškovi perioda; kapital i budući troškovi u zasebnoj ekonomskoj proceni.
4. **Troškovi i opravdanost vozila** — poslovna namena × istorija raspolaganja, obrazloženi kontrolni kriterijumi i poređenje budućih alternativa; [metodologija IMS-FLOTA-2.0](../obracuni/06-12-flota-ekonomika.md).
5. **Šta traži hitnu radnju** — istekla registracija, polisa bez pokrića, kvar.
6. **Ko je vozilo zadužio i koliko je prešao** — putni nalozi vozila.
7. **Službena putovanja zaposlenih** — putni nalozi sa akontacijom.

---

## 3. Korisnici modula

| Korisnik | Šta radi | Uloga |
|---|---|---|
| **Služba voznog parka** | Vodi evidenciju, prati troškove, priprema izveštaje | `uprava` ili posebne dozvole |
| **Garaža** | Prijavljuje kvarove, vodi radne naloge i trebovanja | `uprava`, `zahtev` |
| **Sekretarijat** | Izdaje i štampa putne naloge za službena putovanja | `sekretarijat` |
| **Zaposleni** | Otvara zaduženje vozila i štampa obračun | `zaposleni` |
| **Rukovodioci centara** | Prate vozila i troškove svog centra | uz dozvoljene centre |
| **Uprava** | Izveštaji za pripremu osiguranja i analizu isplativosti | `uprava` |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Vozila** | Tehnički podaci, slike, čarobnjak za unos novog vozila, otpis i vraćanje u upotrebu |
| **Dokumenta** | Saobraćajne dozvole sa istorijom tablica, tenderska dokumentacija, izvoz u ZIP |
| **Raspolaganje** | Osnov raspolaganja (vlasništvo ili ugovor), lizing i najam, kamate |
| **Šifre posla** | Istorijske dodele vozila organizacionoj jedinici |
| **Osiguranje** | Polise, knjiženja osiguranja, dopuna nedovršenih zapisa, pregled isteka |
| **Gorivo** | Transakcije NIS i OMV, fakture goriva, prosečna potrošnja, izveštaji po šifri posla |
| **Održavanje** | Servisi, knjiženja servisa, trebovanja, tipovi servisa, konta vozila |
| **Garaža** | Prijava kvara, radni nalog, trebovanje materijala, zahtev za nabavku (GZN) |
| **Putni nalozi vozila** | Zaduženje vozila sa kilometražom i obračunom goriva |
| **Putni nalozi zaposlenih** | Službena putovanja sa akontacijom, dnevnicom i štampom |
| **Analitika** | Zajednički obračun za flotu, centar i vozilo; namena × raspolaganje, dokumentovani kriterijumi, raspodela na poslove i sačuvane ekonomske procene |
| **Izveštaji** | 20 izveštaja, uključujući 4 za upravu i 11 nad nasleđenim pogledima |
| **Administracija** | Korisnici, uloge, evidencija rada, istorija pozadinskih poslova |

---

## 5. Glavni korisnički ekrani

### Vozila i dokumenta

> **Link na vozilo (od 29.09.2026.) [P].** Svuda na ekranima Flote (spiskovi, detalji, izveštaji,
> kontrolna tabla, tabele sa servera) i na kartici zaposlenog vozilo je link na detalj vozila —
> `fleet/support/vehicle_links.py` (`vozilo_link`, `vozilo_link_id`) i u šablonima `{% load vozila %}`
> (`{{ x.vehicle|vozilo_link }}`, `{% vozilo_a id tekst %}`). Štampani dokumenti, forme i izvozi
> namerno nemaju linkove. Novi ekran sa vozilom treba da koristi isti pomoćnik.

| Ekran | Adresa | Napomena |
|---|---|---|
| Spisak vozila | `/vozila/` | DataTables preko AJAX-a |
| **Unos novog vozila** | `/vozila/novo/` | **Čarobnjak u koracima** |
| Detalj vozila | `/vozila/<id>/` | Kartice: pregled, dokumenti, raspolaganje, korišćenje, kilometraža, analitika |
| Osnov raspolaganja | `/vozila/<id>/osnov/novo/` | Vlasništvo ili ugovor |
| Tenderska dokumentacija | `/vozila/<id>/tenderska-dokumentacija/` | Preuzimanje ZIP datoteke |
| Saobraćajne dozvole | `/saobracajne-dozvole/` | Istorija tablica |
| Šifre poslova (dodele) | `/sifre-poslova/` | Istorijske dodele |

Detalj vozila prikazuje četiri sažete kartice trenutnog stanja. Na užim ekranima
raspoređuju se u dve ili jednu kolonu; kartice podataka, raspolaganja i dokumenata
takođe prelaze u jednu kolonu. Izbor odeljaka ostaje u jednom horizontalno
pomerljivom redu. Oznake statusa imaju odvojene stilove od grupa kartica.

### Ugovori i osiguranje

| Ekran | Adresa |
|---|---|
| Lizing i najam | `/zakupi/` |
| Polise | `/polise/` |
| **Polise za dopunu** | `/polise/nedovrseno/` |
| **Polise pred istekom** | `/polise/istek/` |
| Knjiženja osiguranja | `/insurance/` |
| Knjiženja osiguranja za dopunu | `/insurance/drafts/` |

### Gorivo

| Ekran | Adresa |
|---|---|
| Transakcije goriva | `/fuel-transactions/` |
| Fakture goriva (detalj računa) | `/fuel-transactions/detail/` |
| Potrošnja goriva | `/potrosnja-goriva/` |

> **[P] Šifra posla na gorivu (ispravljeno 25.09.2026.):** uvoz NIS i OMV upisuje u
> `FuelConsumption.job_code` šifru **dodele vozila važeće na dan točenja** (`fleet/support/assignments.py`),
> isto pravilo kao izveštaji o gorivu. Ranije je upisivana najstarija dodela vozila. Stari zapisi
> ispravljeni komandom `ispravi_sifre_goriva` (1.076 od 16.212); ona menja samo pogrešne, a
> zapise bez dodele na taj dan ne dira.

> **[P] Lizing — mesečni troškovi (ispravljeno 25.09.2026.):** jedan lizing je jedno vozilo, pa je
> red izveštaja jedan lizing u jednom mesecu u kome traje. Iznos je iz obračuna lizinga
> (`fleet/support/lease_costs.py`, isto kao ekonomika vozila), centar i OJ po dodeli važećoj u
> tom mesecu, a prateći troškovi su servis i gorivo **samo tog vozila**. Ranije je iznos bio samo
> u mesecu početka, centar po poslednjoj dodeli, a prateći troškovi zbir svih vozila u OJ.
> Lizing bez upisanog „Značenja iznosa” (mesečni ili ukupan) ima prazan iznos (7 od 23 [P]).

### Održavanje i garaža

| Ekran | Adresa |
|---|---|
| Knjiženja servisa | `/service-transactions/` |
| Knjiženja servisa za dopunu | `/servisi/nedovrseno/` |
| Trebovanja | `/requisitions/` |
| Trebovanja za dopunu | `/requisitions/nedovrseno/` |
| **Prijave kvarova** | `/garaza/kvarovi/` |
| Kvarovi u IMS garaži / van IMS-a | `/garaza/kvarovi/ims/`, `/garaza/kvarovi/van-ims/` |
| Štampa prijave kvara | `/garaza/kvarovi/<id>/prijava/` |
| **Radni nalog** | `/garaza/kvarovi/<id>/radni-nalog/` |
| **Trebovanje uz kvar** | `/garaza/kvarovi/<id>/trebovanje/` |
| Formiranje zahteva u Nabavci (POST) | `/garaza/kvarovi/<id>/zahtev/` |
| Poslednja kilometraža vozila (JSON za formu) | `/garaza/kvarovi/kilometraza/` |

#### Prijava kvara i zahtev iz Garaže (od 29.09.2026.) [P]

- **Forma prijave** (`fleet/kvar_form.html`): vozilo sa tablicom, šifrom posla i poslednjom poznatom
  kilometražom; vrsta intervencije i mesto popravke (IMS garaža / van IMS-a) kao kartice; opis.
- **Provera kilometraže** (`fleet/support/garaza.py: proveri_kilometrazu`): poredi se sa poslednjim
  poznatim očitavanjem (točenja NIS/OMV, ranija evidencija goriva, nalozi vozila, ranije prijave
  kvara). Manja vrednost ili skok veći od `max(2.000 km, 1.000 km × dana od očitavanja)` čuva se
  samo uz oznaku „Potvrđujem unetu kilometražu“. Kilometraža mora biti 1–3.000.000. Izmena prijave
  bez promene kilometraže se ne proverava ponovo.
- **Poslednja očitana kilometraža svuda (od 29.09.2026.)**: ispod svakog polja kilometraže u Floti
  (točenje goriva, otvaranje, zatvaranje i prethodno zaduženje vozila, servisna stavka i nedovršena
  stavka, trebovanje) piše poslednja očitana kilometraža vozila do datuma unosa, sa datumom i izvorom;
  kada je uneta manja ili skok veći od istog pravila kao kod prijave kvara, ispod stoji upozorenje.
  Ovde upozorenje **ne sprečava čuvanje** (strogo — uz potvrdu — samo na prijavi kvara). Oznake dodaje
  `fleet/forms/kilometraza.py: oznaci_kilometrazu`, podatke daje `vozilo_kilometraza`
  (`/vozila/kilometraza/`, samo vozila u obuhvatu), prikaz `fleet/static/fleet/js/kilometraza.js`.
  Preuzimanje novog vozila nema napomenu (vozilo još nema očitavanja).
- **Detalj** odmah prikazuje sva tri dokumenta onako kako se štampaju (prijava kvara, trebovanje
  materijala / zahtev za uslugu, radni nalog — ugrađene stranice `?embed=1`, `X-Frame-Options:
  SAMEORIGIN` samo za te tri). Delovi (usluge) se upisuju direktno u tabelu koja izgleda kao
  trebovanje; čuvaju se svi odjednom (dodavanje, izmena, uklanjanje reda).
- **Štampa** (`fleet/templates/fleet/kvar_dokumenti/`): svaki list je tačno A4 (210 × 297 mm) sa
  prelomom posle svakog lista. Lista trebovanja (zahteva za uslugu) ima 12 redova i na A4 se štampa
  **dva puta ista** (jedna kopija se čuva); preko 12 delova sledeća lista ide na **sledeći A4**, opet
  u dve kopije („Lista 1 od 2“, „Lista 2 od 2“). Prijava kvara i radni nalog su po jedan A4, bez okvira
  oko stranice. **„Štampaj sve“** (`/garaza/kvarovi/<id>/stampa/`) štampa redom prijavu, sve liste
  trebovanja i radni nalog (npr. 15 delova → 4 A4 lista; provereno štampom u PDF 29.09.2026.).
  Na trebovanju je O.J. centar, a šifra posla šifra vozila.
- **„Formiraj zahtev u Nabavci“** (`formiraj_zahtev`) pravi **nacrt** predmeta Nabavke: popravka u
  IMS garaži → **Zahtev za nabavku** (`ZNG-<centar>/<godina>-<n>`), van IMS-a → **Zahtev za uslugu**
  (`ZUG-…`). Broj se dodeljuje sam; popunjeni su garaža, vozilo, nalog garaže, vrsta intervencije,
  šifra posla vozila (današnja, a ako je nema — poslednja dodeljena; Nabavka je po potrebi menja), naziv (intervencija + tablica), opis, napomena i stavke iz tabele
  delova. Nabavka nacrt potvrđuje i dopunjuje. Dok postoji neotkazan zahtev za taj kvar, novi se ne
  pravi; detalj kvara prikazuje njegov broj i status. Vozilo bez šifre posla ne može dobiti zahtev.
  Izmene delova posle potvrde Nabavke ne menjaju stavke zahteva.
- Ručni unos predmeta iz Nabavke i dalje radi kao ranije (`nabavka:case_create?garage_order=…`);
  sa kartice vozila (Održavanje) predlaže se Zahtev za uslugu.

### Opomene za gorivo (od 29.09.2026.) [P]

Ekran `/gorivo/opomene/` (Flota → **Ostalo** → Opomene za gorivo) i noćni posao u **07:45**
(`fleet.tasks.opomene_goriva_task`, posle preuzimanja NIS i OMV). Logika: `fleet/support/opomene.py`.

| Tema | Pravilo |
|---|---|
| Šta se proverava | Točenja goriva NIS i OMV iz poslednjih 14 dana (bez AdBlue-a; OMV bez duplikata i odjeka; točenje van rezervoara se preskače). Nepravilnosti: **kilometraža nije uneta** (0 ili prazno), **manja od prethodnog točenja**, **nerealan skok** (više od `max(2.000 km, 1.000 km × dana)`), **ista kao prethodno točenje** drugog dana. Poredi se sa prethodnim *ispravnim* točenjem istog vozila (NIS i OMV zajedno), pa jedno pogrešno točenje ne kvari poređenje sledećeg. |
| Kome ide opomena | Samo vozaču: sa **putnog naloga** vozila za taj dan (nije storniran), a ako naloga nema — onom ko je **zadužio vozilo**. Bez oba: status „Vozač nije poznat“. |
| Tekst | Npr. „IMS Flota — točenje 22.09.2026. u 09:13, BUBANJ POTOK, vozilo BG1017-OU, 38,72 l: kilometraža nije uneta. Molimo da pri svakom točenju unesete tačno stanje brojila.“ Za sada samo opomena, bez ispravke. |
| Slanje | `settings.OPOMENE_GORIVA["kanal"]`: `""` (podrazumevano) — **slanje isključeno**, opomene se samo pripremaju i vide na ekranu; `"email"` — jedna zbirna poruka po vozaču na e-mail korisnika vezanog za zaposlenog (treba podesiti `EMAIL_*`; vozač bez e-maila dobija status „Vozač nema kontakt“). Viber zahteva posrednika (Viber poslovne poruke) — još nije uveden. |
| Jedinstvenost | Jedno točenje = najviše jedna opomena (`izvor` + ID točenja). Izvorne transakcije NIS/OMV se ne menjaju. |
| Prava | Ekran i „Proveri sada“: uloga Garaža (i Uprava). Vidljivost po obuhvatu Flote (vozilo). |

Prvo pokretanje 29.09.2026.: 259 točenja u 14 dana, 78 opomena (73 bez kilometraže, 4 manja, 1 skok); vozač poznat za 60 (23 sa putnog naloga, 37 iz zaduženja).

### Incidenti (od 29.09.2026.) [P]

| Ekran | Adresa |
|---|---|
| **Incidenti** — saobraćajni prekršaji i kazne (DataTable, podaci `/incidenti/podaci/`) | `/incidenti/` |
| **Detalj incidenta** (prilog, ko je imao vozilo, raniji incidenti) | `/incidenti/<id>/` |
| Prilog (otvaranje i preuzimanje, `?preuzmi=1`) | `/incidenti/<id>/prilog/` |
| Novi incident / izmena / brisanje | `/incidenti/novo/`, `/incidenti/<id>/izmena/`, `/incidenti/<id>/brisanje/` |
| Predlog vozača (JSON za formu) | `/incidenti/vozaci/` |

Incident beleži vozilo, datum i mesto prekršaja, vozača, opis prekršaja, iznos kazne (RSD) i
napomenu, i **prilog** (zapisnik, rešenje o kazni, fotografija — PDF ili slika do 20 MB, otvara se
samo kroz aplikaciju uz proveru obuhvata; PDF i slika se na detalju prikazuju odmah). Beleži se ko je
i kada uneo incident. Posle izbora vozila i datuma forma prikazuje ko je tog dana imao vozilo — iz zaduženja
vozila (otvoreno do tog dana, nezatvoreno pre njega) i putnih naloga (dan u periodu putovanja,
bez storniranih) — i vozača bira jednim klikom; kada je predlog jedan, bira ga sama
(`fleet/support/incidenti.py`). Spisak se filtrira po periodu, vozilu i pretrazi (tablica, vozač,
prekršaj, mesto), po prilogu, i prikazuje zbir kazni za filtrirane incidente. Vidljivost prati
obuhvat Flote po vozilu. Incidenti zaposlenog vide se i na njegovoj kartici u Kadrovima.
**Incidente unosi Garaža** — uloga Garaža ima sve dozvole `incident_*` (i Uprava).

### Putni nalozi

| Ekran | Adresa |
|---|---|
| **Zaduženja vozila** | `/garaza/putni-nalozi-vozila/` |
| Obračun goriva na zaduženju | `/garaza/putni-nalozi-vozila/<id>/obracun/` |
| Zatvaranje zaduženja | `/garaza/putni-nalozi-vozila/<id>/zatvori/` |
| **Putni nalozi zaposlenih** | `/putni-nalozi/` |
| Štampa putnog naloga | `/putni-nalozi/<id>/print/` |
| Prilog za inostranstvo | `/putni-nalozi/<id>/prilog-inostranstvo/` |

### Pregledi i izveštaji

| Ekran | Adresa |
|---|---|
| **Kontrolna tabla flote** | `/` |
| **Analitika flote** | `/analitika/` |
| Statistika centra | `/center_statistics/<centar>/` |
| Spisak izveštaja | `/izvestaji/` |
| Izveštaji za upravu | `/izvestaji/osiguranje/kasko/`, `/izvestaji/osiguranje/ims/`, `/izvestaji/gorivo-ims/`, `/izvestaji/delovi-dobavljaca/` |

---

## 6. Podaci koje korisnik unosi

### Kako izgledaju forme [P]

Od 19.09.2026. sve forme Flote koje idu kroz zajednički šablon poštuju tri pravila:

| Pravilo | Kako |
|---|---|
| **Obavezno polje se vidi** | Crvena zvezdica uz naziv, uz legendu na vrhu. Ranije je to imao **samo čarobnjak za unos vozila** — na ostalih 26 ekrana obaveznost se saznavala tek posle slanja |
| **Polja su grupisana u celine** | Forma navede `fieldsets`; polje koje nije razvrstano ide u celinu **„Ostalo“**, da izmena modela ne bi tiho sakrila novo polje |
| **Objašnjenje stoji uz polje** | `help_text`, naročito kod iznosa (mesečni ili ukupni), datuma (da li je uključiv) i knjigovodstvenih skraćenica |

Grupisanje se dodaje nasleđivanjem `FieldsetMixin` iz
[`fleet/forms/layout.py`](../../../fleet/forms/layout.py):

```python
class LeaseForm(FieldsetMixin, forms.ModelForm):
    fieldsets = (
        ('Vozilo i ugovor', 'Na koje vozilo se ugovor odnosi.', ('vehicle', 'contract_number')),
        ('Trajanje', 'Oba datuma su uključena.', ('start_date', 'end_date')),
    )
```

Sređeno je **jedanaest formi** sa ukupno 147 polja: vozilo (26), servisna stavka i njena
nedovršena verzija (2×19), trebovanje (18), polisa (15), ugovor lizinga, saobraćajna
dozvola, naknada osiguranja i njena nedovršena verzija (4×11), gorivo (9), raspolaganje (8)
i tenderski dokument (7).

> **Ispravljena opasna nedoslednost [P]:** polje `nije_garaza` je **negacija** — tačno
> znači da servis **nije** rađen u garaži IMS-a. Nedovršena servisna stavka je za isto polje
> imala naziv *„Da li ovaj servis pripada garaži?“*, dakle **suprotnog značenja**. Sve tri
> forme sada nose isti naziv: **„Servis van garaže IMS-a“**.

> **Vraćeno izgubljeno objašnjenje [P]:** `KvarForm` je redeklaracijom polja brisao
> `help_text` koji postoji na modelu.

---



| Podatak | Ekran | Ko unosi |
|---|---|---|
| Tehnički podaci vozila | Unos vozila | Služba voznog parka |
| **Maksimalna dozvoljena masa** | Unos vozila | Tehnička karakteristika; u novoj analitici ne određuje kriterijum opravdanosti |
| Saobraćajna dozvola i tablice | Saobraćajne dozvole | Služba voznog parka |
| Osnov raspolaganja i period | Detalj vozila | Služba voznog parka |
| Lizing i najam | Lizing | Služba voznog parka |
| Prijava kvara, kilometraža, opis | Garaža | Garaža |
| Stavke delova uz kvar | Radni nalog | Garaža |
| Zahtev za nabavku (GZN) | Garaža | Garaža |
| **Zaduženje vozila i kilometraža** | Putni nalozi vozila | **Zaposleni** |
| Putni nalog: mesto, zadatak, dani, akontacija | Putni nalozi | Sekretarijat |
| Kategorija popravke i napomena na knjiženjima | Ekrani „za dopunu“ | Služba voznog parka |
| Veza knjiženja sa vozilom | Ekrani „za dopunu“ | Služba voznog parka |
| Tipovi servisa, konta vozila | Šifarnici | Služba voznog parka |

---

## 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada | Tabela |
|---|---|---|---|
| Organizacione jedinice | **Registar organizacije** (od 28.09.2026.; ranije `dbo.v_organizationalunit`) | 01:40 | `fleet_organizationalunit` |
| **Tekuća šifra posla vozila** | `dbo.sif_pos_trenutno` | Ručno, `update_job_codes` (nije u rasporedu) | `fleet_jobcode` |
| Otpisana vozila | `dbo.fleet_otpis` | 01:20 | `fleet_vehicle.otpis` |
| **Knjigovodstvena vrednost** | `dbo.vrednost_vozila` | Ručno | `fleet_vehicle.value` |
| Trebovanja | `dbo.fleet_trebovanja` | 01:45 | `fleet_requisition` |
| Polise osiguranja | EUF fakture Nabavke | 02:00 | `fleet_policy` |
| Knjiženja servisa | `dbo.fleet_servisi` | 03:15 | `fleet_servicetransaction` |
| Knjiženja osiguranja DDOR | `dbo.fleet_potrazivanje_ddor` | 03:35 | `fleet_draftinsurance` |
| **Gorivo NIS** | Portal `cards.nis.rs` (Selenium) | 04:20 | `fleet_transactionnis`, `fleet_fuelconsumption` |
| **Gorivo OMV putnička** | Portal `fleet.omv.com` (Selenium) | 05:10 | `fleet_transactionomv`, `fleet_fuelconsumption` |
| **Gorivo OMV teretna** | Isti portal | 06:10 | isto |
| **Isplaćeno po putnom nalogu** | `dbo.fleet_zatvoren_putni` | 12:30 | `fleet_putninalog.isplaceno` |
| Kamate lizinga | `dbo.lizing_kamate` | Ručno | `fleet_leaseinterest` |
| Zaposleni | `dbo.hr_employee` | 01:10 | `fleet_employee` |

---

## 8. Tabele i kolone

Detaljno: [4.4. Vozni park](../04-baza-podataka.md#44-vozni-park--fleet).

**23 tabele.** Najvažnije:

| Tabela | Uloga | Ključ |
|---|---|---|
| `fleet_vehicle` | Vozilo | `chassis_number` (broj šasije) |
| `fleet_trafficcard` | Saobraćajna dozvola, istorija tablica | — |
| `fleet_jobcode` | **Istorijska dodela vozila OJ** | `(vehicle, assigned_date)` |
| `fleet_vehicleholding` | Osnov raspolaganja, periodi bez preklapanja | — |
| `fleet_lease`, `fleet_leaseinterest` | Lizing i kamata | `(year, lease)` |
| `fleet_policy` | Polisa osiguranja | `invoice_id` |
| `fleet_insurance`, `fleet_draftinsurance` | Knjiženja osiguranja | `(god, sif_vrs, br_naloga, stavka, knt)` |
| `fleet_transactionomv`, `fleet_transactionnis` | Sirove transakcije goriva | petorke kolona |
| `fleet_fuelconsumption` | Objedinjena potrošnja | `(vehicle, supplier, date, amount, fuel_type)` |
| `fleet_servicetransaction`, `fleet_draftservicetransaction` | Knjiženja servisa | `(datum, duguje, vez_dok, br_naloga)` |
| `fleet_requisition` | Trebovanje | `(sif_pred, god, br_dok, sif_vrsart, stavka)` |
| `fleet_kvar`, `fleet_kvarpart` | Prijava kvara i delovi | `rbz` |
| `fleet_vehicletravelorder` | Zaduženje vozila | `pn_number`, `rbz` |
| `fleet_putninalog` | Službeno putovanje | `order_number` |

> **[P] Veza sa registrom organizacije (faza 2, od 25.09.2026.):** šest tabela —
> `fleet_jobcode`, `fleet_putninalog`, `fleet_vehicletravelorder`, `fleet_procurementrequest`,
> `fleet_fuelconsumption`, `fleet_lease` — imaju opcionu kolonu `org_node_id` (čvor registra).
> Ona se **izvodi** iz postojećeg polja (`organizational_unit` / `job_code`) pri svakom čuvanju
> (`organizacija/signals.py`) i komandom `povezi_flotu`. Uporedni izveštaj:
> `/organizacija/flota/` (dozvola `organizacija:flota`). Od 02.10.2026. nije u meniju Organizacije —
> kontrola prelaska na registar, otvara se samo direktnom adresom.
>
> **[P] Čitanje iz registra (od 25.09.2026.):** spiskovi i nazivi šifara posla u Floti dolaze iz
> registra (`fleet/support/registar.py`) — izbor šifre u formama putnog naloga, dodele vozila,
> prijema vozila i naloga za vozilo nudi samo **aktivne** šifre iz registra (već upisana vrednost
> ostaje), a filteri, kontrolna tabla i prava pristupa prikazuju centre sa nazivom po pravilniku.
> Od 25.09.2026. neaktivne šifre se ne nude **ni u filterima** (vozila, putni nalozi, saobraćajne,
> polise), ni u Nabavci (predmet, povezivanje fakture, filter), ni u Finansijama (spisak šifara,
> kartica posla, izveštaj po šiframa); u pravima pristupa ostaju samo već dodeljene. Šifra bez
> prometa u poslednjih 12 meseci je neaktivna — to noćna sinhronizacija organizacije (01:40)
> proverava sama. Uloga **Garaža** radi sa celom Flotom svih centara, a putne naloge samo gleda.
> Broj putnog naloga i dalje se pravi iz starog polja (centar je isti u oba izvora). Prekidač
> `FLOTA_REGISTAR_ORGANIZACIJE = False` u postavkama vraća stare spiskove; dok je registar prazan,
> stari spiskovi se koriste sami.

> **[P] Pristup od 28.09.2026. — Flota na registru** (plan prelaska, korak 6; prekidač
> `PRAVA_PO_REGISTRU["flota"]`, pravila u `fleet/support/obuhvat.py`). Obuhvat daju **odobrene
> dodele uloga** koje imaju bilo koju dozvolu Flote (bez dozvola za zaposlene, naloge za vozilo i
> korisnički nalog). `allowed_center_codes`, `allowed_centers` i izuzetak za Upravu više ne odlučuju.
>
> | Šta | Ko vidi |
> |---|---|
> | **Vozilo** i sve vezano za njega — saobraćajne, polise, lizing, gorivo i računi goriva, servisi, kvarovi, trebovanja, osiguranje, dokumenti za tender, dodele, kontrolna tabla | Ako je **današnja dodela vozila** u obuhvatu; vozilo bez ijedne dodele vidi svako ko ima obuhvat (da tek uneto vozilo ne nestane); zapis bez vozila (npr. nacrti za povezivanje) samo cela firma |
> | **Putni nalog** | Ako mu je šifra posla u obuhvatu; nalog se ne može prebaciti na šifru van obuhvata |
> | Izveštaji po istorijskoj dodeli (osiguranje, gorivo po šifri) | Po šiframa posla u obuhvatu |
> | Analiza centra | Samo za centre koji su celi u obuhvatu |
> | Izbor šifre posla (garaža, ekonomika, prijem vozila) | Samo šifre iz obuhvata, uz već upisanu |
>
> **Nalozi za vozilo** ne zavise od organizacije (zaposleni vidi svoje) i ne menjaju se. Uprava,
> Garaža, Nabavka, Blagajna i (od 30.09.2026.) Pregled imaju obuhvat cele firme. Merenje 28.09.2026. (19 korisnika Flote):
> putne naloge svi vide isto kao ranije, osim Garaže (0 → 3.746, samo čitanje, potvrđeno); vozila —
> Pregled (3) i Sekretarijat (10) sada samo vozila svog centra (npr. 98 od 164 za centar 43), po
> odluci 25.09.2026. „samo svoj centar”. Odluka 30.09.2026.: **Pregled vidi celu firmu** (sva vozila,
> kao pre registra, a time i sve putne naloge: 3.819 umesto 2.285 za centar 43).

---

## 9. SQL pogledi i upiti

| Objekat | Namena | Status |
|---|---|---|
| `dbo.v_organizationalunit` | Šifarnik OJ | Poznate kolone |
| `dbo.sif_pos_trenutno` | Tekuća šifra posla po tablici | Poznate kolone |
| `dbo.fleet_otpis` | Otpisana osnovna sredstva | Poznate kolone |
| `dbo.vrednost_vozila` | Knjigovodstvena vrednost | Poznate kolone |
| `dbo.fleet_trebovanja` | Trebovanja | **[N]** Sadržaj nije potvrđen |
| `dbo.fleet_servisi` | Knjiženja servisa | **[N]** |
| `dbo.fleet_potrazivanje_ddor` | Knjiženja osiguranja | Poznate kolone |
| `dbo.fleet_zatvoren_putni` | Isplaćeni putni nalozi | **[N]** |
| `dbo.lizing_kamate` | Kamate lizinga | **[N]** |
| **9 izveštajnih pogleda** | `fleet_tro_svi`, `fleet_tro_goriva_m`, `fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`, `tro_zarade`, `fleet_dobavljaci`, `fleet_magacin_rez`, `kasko_rate` | **[N] Formula je u bazi** — [P-27](../10-poznati-problemi.md) |

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`fleet/models.py`](../../../fleet/models.py) |
| Rute i dozvole | [`fleet/urls.py`](../../../fleet/urls.py) |
| **Obračuni goriva** | [`fleet/support/fuel.py`](../../../fleet/support/fuel.py) |
| **Nova analitika i ekonomske procene** | [`fleet/services/economics.py`](../../../fleet/services/economics.py), [`fleet/economics_models.py`](../../../fleet/economics_models.py) |
| Nasleđeni trošak/km i pragovi — radi kompatibilnosti | [`fleet/support/dashboard.py`](../../../fleet/support/dashboard.py), [`fleet/support/analytics.py`](../../../fleet/support/analytics.py) |
| Kilometraža | [`fleet/support/vehicle_mileage.py`](../../../fleet/support/vehicle_mileage.py) |
| Održavanje | [`fleet/support/vehicle_maintenance.py`](../../../fleet/support/vehicle_maintenance.py) |
| Presek stanja | [`fleet/support/fleet_snapshot.py`](../../../fleet/support/fleet_snapshot.py) |
| Izveštaji za upravu | [`fleet/support/management_reports.py`](../../../fleet/support/management_reports.py) |
| Upiti nad pogledima | [`fleet/support/report_queries.py`](../../../fleet/support/report_queries.py) |
| Preuzimanje iz ERP-a | [`fleet/sync/external.py`](../../../fleet/sync/external.py), [`services.py`](../../../fleet/sync/services.py) |
| **Selenium preuzimanje goriva** | [`fleet/sync/selenium.py`](../../../fleet/sync/selenium.py) |
| Čišćenje duplikata goriva | [`fleet/support/fuel_cleanup.py`](../../../fleet/support/fuel_cleanup.py) |
| Pozadinski poslovi | [`fleet/tasks.py`](../../../fleet/tasks.py) |
| **Normalizacija tablica** | [`fleet/support/vehicle.py: format_license_plate()`](../../../fleet/support/vehicle.py) |

**41 upravljačka komanda** u `fleet/management/commands/` — sinhronizacije, uvozi,
ispravke i provere. [P]

---

## 11. Ulazni i izlazni podaci

### Ulaz

| Vrsta | Izvor |
|---|---|
| Sinhronizacija | 9 nasleđenih pogleda |
| Selenium | NIS i OMV portali |
| Uvoz datoteka | NIS Excel, OMV CSV (putnička i teretna) |
| Ručni unos | Vozila, dokumenta, kvarovi, putni nalozi |

### Izlaz

| Vrsta | Šta |
|---|---|
| Excel | Lizing, izveštaji za upravu |
| CSV | Vozila, mesečni troškovi polisa i servisa |
| ZIP | Tenderska dokumentacija vozila |
| Štampa | Putni nalog, prilog za inostranstvo, prijava kvara, radni nalog, trebovanje |
| Podaci drugim modulima | Vozila i zaduženja Finansijama, kvarovi Nabavci, putni nalozi Isplatama |

---

## 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Kadrovi** | Zaposleni na putnom nalogu i zaduženju vozila |
| **Nabavka** | Kvar → predmet nabavke; EUF fakture → polise i dokazi o održavanju |
| **Ugovori** | Ugovor o lizingu (`Lease.contract`) i o finansiranju (`VehicleHolding.financing_contract`) |
| **Finansije** | Vozila i zaduženja na šifri posla; trošak zarada |
| **Isplate** | Putni nalozi sa akontacijom → virman |
| **Administracija** | Organizacione jedinice i centri |
| **Organizacija (registar)** | Kolona `org_node` na šest tabela, samo upis i poređenje — čitanje iz registra još nije uključeno |

---

## 13. Izveštaji i analize

**24 obračuna + 11 izveštaja nad pogledima.** Detaljno:

| Poglavlje | Sadržaj |
|---|---|
| [6.2. Gorivo](../obracuni/06-02-flota-gorivo.md) | Prečišćavanje OMV, potrošnja, gorivo po šifri posla |
| [6.3. Troškovi](../obracuni/06-03-flota-troskovi.md) | Dokumentacija nasleđenih obračuna |
| [6.12. Ekonomika flote](../obracuni/06-12-flota-ekonomika.md) | Aktuelna metodologija zajedničke analitike i poređenja budućih opcija |
| [6.4. Polise i lizing](../obracuni/06-04-flota-ugovori-polise.md) | Mesečni troškovi, istek polisa |
| [6.5. Izveštaji](../obracuni/06-05-flota-izvestaji.md) | Kilometraža, održavanje, presek stanja, izveštaji za upravu |

---

## 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `uprava` | Sve |
| `sekretarijat` | Zaposleni, putni nalozi: unos, izmena, štampa, storno |
| `zaposleni` | **Samo zaduženja vozila** — spisak, otvaranje, detalj, obračun, štampa. **Ne može** menjati zaduženje |
| Uz dozvoljene centre | Kontrolna tabla i izveštaji ograničeni na svoje centre |

**Posebna pravila [P]:**

- Zatvoreno zaduženje vozila može menjati **samo superuser**.
- Statistiku centra vidi superuser ili korisnik sa tim centrom u `allowed_centers`
  (usklađeno 18.09.2026., [P-13](../10-poznati-problemi.md)).
- Izveštaji za upravu koriste **oba** mehanizma za centre — vidi [P-19](../10-poznati-problemi.md).

---

## 15. Validacije i kontrole

| Kontrola | Gde | Poruka / ponašanje |
|---|---|---|
| **Format tablica** | `TrafficCard` | `AA999-AA` ili `AA9999-AA` |
| **Tablica kod drugog vozila** | `TrafficCard.clean()` | *„Ove tablice su već povezane sa drugim vozilom.“* |
| Datum izdavanja u budućnosti | `TrafficCard.clean()` | Odbija se |
| **Preklapanje osnova raspolaganja** | `VehicleHolding.clean()` | *„Period se preklapa… Najpre završite prethodni period.“* |
| Period raspolaganja izvan ugovora | `VehicleHolding.clean()` | Odbija se |
| Ugovor ne pripada vozilu | `VehicleHolding.clean()` | Odbija se |
| Finansiranje samo za vlasništvo IMS | `VehicleHolding.clean()` | Odbija se |
| **Jedna dodela po vozilu i danu** | `JobCode` | Kontrola u bazi |
| Broj putnog naloga | `PutniNalog.generate_order_number()` | *„Nedostaje početni broj za izabrani centar/godinu.“* |
| Tablica kod više vozila | `TrafficCard.for_plate()` | **Namerno odbija da pogađa** |
| Broj zaduženja vozila | `VehicleTravelOrder.save()` | Uz `select_for_update()` |
| Brisanje slike posle potvrde | `VehicleTenderDocument` | `transaction.on_commit` |

---

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Vozilo bez saobraćajne | Prikazuje se broj šasije umesto tablica |
| Tablica pripada većem broju vozila | Sinhronizacija **preskače** taj red |
| Vozilo bez dodele | Grupa „Bez centra“, zasebno upozorenje |
| Otpisano vozilo | Ne ulazi u analitiku; broji se zasebno na kontrolnoj tabli |
| OMV duplikati | Brišu se pri uvozu i filtriraju pri čitanju |
| Novo vozilo (mlađe od godinu dana) | Amortizacija razmazana na 365 dana |
| Nedovršena polisa | **Ne ulazi** u upozorenja o isteku |
| Otvoreno zaduženje | Obračun goriva ide **do današnjeg dana** |
| Više otvorenih zaduženja istog vozila | Upozorenje na kontrolnoj tabli |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Potrebno |
|---|---|---|
| 1 | **Formula 11 izveštaja** nad nasleđenim pogledima | DDL pogleda — [P-27](../10-poznati-problemi.md) |
| 2 | Sadržaj pogleda `fleet_servisi`, `fleet_trebovanja`, `fleet_zatvoren_putni`, `lizing_kamate` | DDL |
| 3 | **Poreklo pragova troška po kilometru** | Potvrda naručioca — **Q18** |
| 4 | Da li se izveštaji koriste kao osnov za knjiženje | Potvrda — **Q3** |
| 5 | Zašto se službeni izlazak računa do 16:00 *(deli se sa Kadrovima)* | Potvrda — **Q27** |
| 6 | Da li se izveštaj mesečnih troškova lizinga uopšte koristi | Potvrda — **Q21** |
| 7 | Poreklo pristupnih podataka za NIS i OMV portale | Potvrda — **Q7** |

---

## Gde dalje

### Vizuelni pregled Flote

[Otvoriti UML galeriju Flote](../../dijagrami/flota.html) lokalno u pregledaču.
Šest dijagrama obuhvata organizaciju koda, vozila i dodele, putne naloge,
održavanje, zakup, osiguranje, uvoz goriva i ekonomske analize.
Svaki ima SVG za uvećavanje i PlantUML izvor za izmene u VS Code-u (Alt+D).
Novi [interaktivni atlas Flote](../../dijagrami/index.html#module/fleet) omogućava
prelazak od oblasti do modela, njegovih polja, veza i poslovnih tokova.
Prikaz je zasnovan na repozitorijumu od **28.09.2026.**, bez pristupa živoj bazi.

Početi od **07 — Organizacija Flote**, zatim otvoriti modele **08–09** ili tokove
**10–12**. `VehicleTravelOrder` i `PutniNalog` prikazani su zasebno; pomoćne
evidencije nisu automatski ulazi u obračune. Detalji izvora i regenerisanja
nalaze se u [poglavlju 2.14](../02-arhitektura.md#214-uml-dijagrami-aplikacije).

| Poglavlje | Sadržaj |
|---|---|
| [6.2–6.5](../obracuni/06-02-flota-gorivo.md) | Svi obračuni Flote |
| [4.4](../04-baza-podataka.md#44-vozni-park--fleet) | Tabele Flote |
| [7. Integracije](../07-integracije.md) | NIS, OMV i nasleđeni pogledi |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-02 … P-14, P-23 … P-27 |
