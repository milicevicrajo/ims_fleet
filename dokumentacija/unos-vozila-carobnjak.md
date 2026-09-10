# Unos vozila kroz čarobnjak

Implementirano 10. 09. 2026. na postojećoj putanji `vozila/novo/` (`vehicle_create`).

## Postupak unosa

1. Identifikacija: kategorija, šasija, marka, model, godina i inventarski broj kada postoji. Šasija se normalizuje i proverava pre nastavka.
2. Osnov korišćenja: vlasništvo IMS uz finansiranje nabavke ili korišćenje po ugovoru. Za kredit može da se poveže postojeći `ugovori.Contract`; kredit nije vrsta lizinga. Za lizing/najam kreira se `Lease`, opciono vezan za postojeći ugovor iz modula Ugovori. Postojeći `Lease` drugog vozila se ne prenosi na novo vozilo.
3. Tehnički podaci: boja, homologacija, datum prve registracije, mase, motor, sedišta i ostale karakteristike. Priključno vozilo nema polja motora; električno nema zapreminu motora. Nepoznate vrednosti se ne zamenjuju nulom.
4. Saobraćajna i prilozi: može se preskočiti. Rok dokumenta i istek registracije su odvojeni. Privremeni PDF/slike ostaju dostupni tokom koraka.
5. Šifra posla/OJ sa datumom dodele; opciono prvo zaduženje zaposlenog i kilometraža, uključujući nulu. Za korisnika ograničenog na centre, raspoređivanje u dozvoljeni centar je obavezno.
6. Provera: pregled podataka i nedostajućih informacija, povratak na ranije korake, završna potvrda.

Pre završne potvrde nema zapisa u poslovnim tabelama. Svi povezani zapisi nastaju u jednoj transakciji. Ako naknadni korak ne uspe, vraćaju se upisi i uklanjaju trajno kopirani prilozi. Ponovljena završna potvrda iste sesije otvara već kreirano vozilo.

Privremeni unos traje dva sata od poslednjeg sačuvanog koraka, najviše pet paralelnih unosa u sesiji. Nije trajni nacrt koji deli više zaposlenih. Izbor „Nazad“ otvara prethodno sačuvan korak; izmene tekućeg koraka potvrđuju se dugmetom „Dalje“.

## Modeli i podaci

- `Vehicle`: zadržan identitet i tehnički podaci. Dodat homologacioni broj. Inventarski broj, motor i pojedinačne tehničke/nabavne vrednosti mogu biti nepoznati. Neprazni inventarski brojevi i brojevi motora ostaju jedinstveni; SQL Server koristi jedinstvene indekse koji izostavljaju NULL vrednosti.
- `TrafficCard`: saobraćajna i registraciona oznaka ostaju zajedno. Više dokumenata istog vozila može imati iste tablice. Prikaz poslednje izdate dozvole koristi datum izdavanja, pa ID za isti datum. To nije potvrda da registracija važi. Novi dokument ne briše prethodni.
- `VehicleHolding`: jedina nova poslovna tabela. Istorija osnova raspolaganja, početak/kraj, veza sa `Lease`, finansiranje nabavke, opciona veza sa kreditnim ugovorom i dokaz/napomena. Periodi istog vozila ne smeju da se preklapaju. Krajnji datum je uključiv; novi period počinje narednog dana. Istek lizinga ne kreira vlasništvo.
- `Lease`: ostaje evidencija lizinga/najma; dodata opciona veza sa registrom ugovora. Postojeća metodologija naknada ostaje: dugoročni najam ima mesečnu naknadu, operativni ukupnu naknadu za ugovoreni period, finansijski kamate vodi odvojeno. Čarobnjak označava iznose kao RSD i ne prihvata vezivanje ugovora u drugoj valuti za ovaj obračun. Valutna konverzija, promenljive rate i kompletan obračun kredita nisu uvedeni.
- `JobCode` i `VehicleTravelOrder`: koriste se postojeće evidencije, bez novih tabela ili dupliranja šifre posla i zaposlenog na vozilu.

Nabavne vrednosti i podaci dobavljača nisu uklonjeni sa `Vehicle`, jer ih postojeći obračuni koriste. Homologacioni broj na prethodnim saobraćajnim takođe je zadržan kao izvorni podatak. Novi unos i izmena homologacije idu preko vozila.

## Saobraćajne i integracije

Podrazumevani pregled prikazuje poslednju izdatu dozvolu po vozilu. Opcija „Prikaži i prethodne dokumente“ otvara istoriju. Kartica vozila prikazuje dokumente, datume i veze za izmenu.

`TrafficCard.objects.for_plate(...)` pronalazi vozilo kroz istoriju dokumenata. Ako postoji više dokumenata istog vozila, bira poslednji dokument; ako oznaka pripada različitim vozilima, odbija dvosmisleno povezivanje. Stare tablice ostaju upotrebljive za prepoznavanje istorijskih transakcija. Uvozi NIS/OMV, šifara poslova, servisa, trebovanja i Excel zahteva nabavke prilagođeni su ovoj logici.

Namerno nije uvedeno automatsko tumačenje ponovne dodele iste oznake drugom vozilu. Takav slučaj traži proveru istorije i dodatno pravilo po datumu. Validacija u aplikaciji sprečava običan unos iste oznake na drugom vozilu, a uvozi odbijaju dvosmislene stare ili direktno upisane podatke.

## Dozvole i održavanje

Ulaz u čarobnjak koristi postojeću dozvolu `vehicle_create`. Završni upis dodatno proverava dozvole za izabrane evidencije: `lease_create`, `trafficcard_create`, `jobcode_create`, `vehicle_travel_order_create`.

Dodavanje/izmena osnova raspolaganja koristi postojeću dozvolu `vehicle_update` i proverava centar vozila. Za promenu osnova najpre treba završiti prethodni period, pa dodati novi. Sa kartice su dostupni osnovi raspolaganja i ugovori. Izmena pojedinačnih podataka ne pokreće ponovo čarobnjak.

Privremeni prilozi se čuvaju van javnog MEDIA direktorijuma, u sistemskom privremenom direktorijumu `ims_fleet_vehicle_wizard`. Uspeh, odustajanje i obrada isteka sesije uklanjaju priloge. Za napuštene sesije koje korisnik više ne otvara postoji komanda:

```powershell
.venv/Scripts/python.exe -X utf8 manage.py cleanup_vehicle_onboarding_uploads
```

Komanda uklanja samo datoteke iz imenovanih privremenih direktorijuma neaktivnih duže od dva sata i 15 minuta. Može se uključiti u postojeći raspored održavanja. Sesije i privremeni prilozi pretpostavljaju isti serverski disk; više aplikacionih hostova zahtevalo bi zajedničko privremeno skladište.

## Migracije i provera podataka

`0073_vehicle_onboarding` dodaje strukturu i menja obaveznost/jedinstvenost odgovarajućih polja. `0074_vehicle_onboarding_data` kopira homologaciju samo kada nema različitih vrednosti među dokumentima i prenosi nepreklapajuće ugovore u istoriju raspolaganja. Ne pretpostavlja vlasništvo, kredit niti značenje starog datuma `valid_until`.

Komanda za pregled pre/posle migracije:

```powershell
.venv/Scripts/python.exe -X utf8 manage.py audit_vehicle_onboarding
```

Migracije su primenjene na konfigurisanu SQL Server bazu. Pre primene sačuvan je snimak tri izvorne tabele u `izvestaji/backup_vehicle_onboarding_20260910_094927.json`. To je kopija zapisa obuhvaćenih izmenom, a ne kompletan backup baze.

Provera nakon migracija:

- svih 172 vozila, 172 saobraćajne i 23 ugovora imaju očuvane vrednosti svih prethodnih kolona;
- 172 homologaciona broja preneta su na vozila;
- 23 osnova raspolaganja preneta su iz postojećih ugovora, sa napomenom da treba proveriti datum preuzimanja;
- nijedan datum isteka registracije nije automatski pretpostavljen;
- za 149 vozila bez ugovora vlasništvo nije automatski popunjeno;
- prikaz postojeće kartice vozila na SQL Server bazi vraća HTTP 200.

Vraćanje starih NOT NULL i UNIQUE ograničenja nije bezuslovno moguće nakon novih unosa sa praznim poljima i istorijom dokumenata. Povratak na staru verziju zahteva prethodnu proveru novih podataka; ne pokretati automatski migraciju unazad posle početka korišćenja.

## Validacija

Izolovana konfiguracija `ims_erp.settings.testing` koristi SQLite bez SQL Server veze, slanja pošte ili spoljnog keša. Nova funkcionalnost ima testove za unos, istoriju, preklapanja, kredit, ugovore, zaduženje, priloge, odustajanje, ponovljenu potvrdu i vraćanje transakcije.

```powershell
.venv/Scripts/python.exe -X utf8 manage.py test fleet.test_vehicle_onboarding --settings=ims_erp.settings.testing --noinput
.venv/Scripts/python.exe -X utf8 manage.py test fleet nabavka --settings=ims_erp.settings.testing --noinput
```

U široj proveri pronađena su dva prethodno postojeća pada, potvrđena i na čistom sadržaju Git HEAD:

- `fleet.tests.VehicleTravelOrderConsumptionTests.test_datatable_search_finds_order_by_registration_number` — test koristi korisnika bez pristupa zaduženjima, očekuje jedan rezultat, dobija nula;
- `nabavka.tests.ProcurementInvoiceJobCodeLinkTests.test_primary_invoice_job_code_cannot_be_added_as_additional` — osnovna šifra fakture ostaje i među dodatnim vezama.

Završni rezultat: 25/25 novih testova prolazi; širi skup ima 117 uspešnih od 119 testova, uz navedena dva prethodno postojeća pada. `check` i provera usklađenosti modela i migracija prolaze. Ova izmena ne menja ta dva ranija ponašanja. Proveren je i ceo unos u stvarnom Chrome pregledaču na privremenoj bazi, uključujući mobilni prikaz bez horizontalnog prelivanja. Primeri prikaza: `unos_vozila_tehnicki.png`, `unos_vozila_potvrda.png`, `unos_vozila_mobilni.png`.
