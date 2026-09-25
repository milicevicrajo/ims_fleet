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
| Organizacione jedinice | `dbo.v_organizationalunit` | 01:30 | `fleet_organizationalunit` |
| **Tekuća šifra posla vozila** | `dbo.sif_pos_trenutno` | 01:30 | `fleet_jobcode` |
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
> `/organizacija/flota/` (dozvola `organizacija:flota`).
>
> **[P] Čitanje iz registra (od 25.09.2026.):** spiskovi i nazivi šifara posla u Floti dolaze iz
> registra (`fleet/support/registar.py`) — izbor šifre u formama putnog naloga, dodele vozila,
> prijema vozila i naloga za vozilo nudi samo **aktivne** šifre iz registra (već upisana vrednost
> ostaje), a filteri, kontrolna tabla i prava pristupa prikazuju centre sa nazivom po pravilniku.
> Filteri, zbirovi, ograničenje pristupa i broj putnog naloga i dalje rade preko starog polja
> (centar je isti u oba izvora). Prekidač `FLOTA_REGISTAR_ORGANIZACIJE = False` u postavkama vraća
> stare spiskove; dok je registar prazan, stari spiskovi se koriste sami.

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

| Poglavlje | Sadržaj |
|---|---|
| [6.2–6.5](../obracuni/06-02-flota-gorivo.md) | Svi obračuni Flote |
| [4.4](../04-baza-podataka.md#44-vozni-park--fleet) | Tabele Flote |
| [7. Integracije](../07-integracije.md) | NIS, OMV i nasleđeni pogledi |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-02 … P-14, P-23 … P-27 |
