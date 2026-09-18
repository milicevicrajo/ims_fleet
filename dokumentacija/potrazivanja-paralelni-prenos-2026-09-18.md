# Potraživanja — aktiviranje i kontrola prenosa

**Datum: 18.09.2026. · Baza: IMS_ERP · Poslednje uspešno pokretanje: #5 · Snimak: #4**

Potraživanja su aktivirana na `/potrazivanja/`, pored postojeće Naplate. Primenjene su
migracije novih tabela, registrovane dozvole i izvršena puna sinhronizacija sa kontrolama.
Stara Naplata nastavlja da radi; unos kontakata, napomena, poziva i opomena ostaje u njoj.

## Rezultat poređenja

| Pokazatelj | Rezultat |
|---|---:|
| Knjiženja Naplate — obuhvat 2026. | 10.050 |
| Knjiženja ispravki — obuhvat 2025. | 2.395 |
| Ukupno normalizovanih knjiženja | 12.445 |
| Otvorene stavke | 1.586 |
| Partneri sa otvorenim stavkama | 468 |
| Duguje otvorenih stavki | 657.928.051,21 RSD |
| Potražuje otvorenih stavki | 206.986.096,41 RSD |
| Saldo otvorenih stavki | **450.941.954,80 RSD** |
| Razlika ukupnog salda prema starom prikazu | **0,00 RSD** |

Napomena: navedeni D/P su zbirovi otvorenih stavki. Nisu ukupni prometi svih knjiženja,
jer se zatvorene pozicije sa saldom nula ne prikazuju kao otvorene.

Ugrađene kontrole poslednjeg pokretanja:

| Kontrola | Broj upoređenih grupa / redova | Razlike |
|---|---:|---:|
| Nezavisan zbir D−P iz `baza` prema otvorenim pozicijama | 5.403 | 0 |
| Prenos pozicija po partneru/referenci/poslu/porodici konta | 1.586 | 0 |
| Partner / šifra posla / porodica konta / baket | 994 | 0 |
| Datumi dospeća | 1.586 | 0 |
| Duguje i potražuje pozicija | 1.586 | 0 |
| Ključevi, partneri, konta, poslovi, reference, datumi i D/P knjiženja | 12.445 | 0 |

Pored kontrola samog importa, zasebno je pozvana postojeća funkcija
`naplata.queries.dugovanja_po_bucketima_rows()` i upoređena sa podacima novog ekrana.
Poklopilo se svih **468 grupa partner/domaći–inostrani** i svih devet novčanih pokazatelja
po grupi: sedam baketa, dospelo i ukupno. Broj različitih grupa: **0**.
Ta zasebna provera rađena je nad snimkom #3; naredni snimak #4 zadržao je iste finansijske
iznose i prošao sve ugrađene kontrole.

## Potpunost prenosa

Poslednja sinhronizacija obuhvata **355.433 izvorna reda iz 22 skupa**. Zbir uključuje
view-ove i njihove istorijske pomoćne tabele, pa predstavlja broj sačuvanih izvornih redova,
a ne broj jedinstvenih faktura. Isti istorijski zapis može postojati i u pomoćnoj tabeli i u view-u.

| Izvor | Redovi |
|---|---:|
| partneri — kompletan izvorni view | 13.608 |
| baza | 10.050 |
| ispravke | 2.395 |
| v_tuzeni | 117 |
| v_if | 109.761 |
| v_duplikati | 2.580 |
| dodela_baketa | 1.586 |
| v_neodobreneIF | 160 |
| tabela_if | 98.791 |
| duplikati18 | 111.153 |
| kontakti | 654 |
| napomene | 103 |
| opomene | 895 |
| poziv_pismo | 133 |
| pozivi_tel | 2.478 |
| tuzbe | 32 |
| sif_baket | 7 |
| sif_kategorija | 2 |
| avans_klijent | 7 |
| postupak | 127 |
| promena_postupka | 379 |
| posao — firma 1 | 415 |

U poslovnim Django modelima formirano je 12.906 finansijskih identiteta partnera firme 1 /
grupe 1, 4.180 IF dokumenata iz obuhvata Naplate, 654 kontakta, 2.581 aktivnost
(napomene + pozivi), 1.060 opomena/pisama/starih tužbi i 14 profila sa oznakama kupaca.
Pravni postupci i svih 379 promena ostali su u postojećim tabelama; kreirane su 123
potvrđene veze sa finansijskim partnerom. Svi izvorni postupci i promene dodatno su arhivirani.

Postoje 4.309 kontrolnih mapa prenosa, uključujući mape profila. Promenjene verzije izvora
ostaju sačuvane: ukupna arhiva trenutno ima 23 verzije skupova i 357.910 redova.

## Ponovljivost i vreme

| Pokretanje | Trajanje | Nalaz |
|---|---:|---|
| #2 — prvi uspešan puni prenos | 298,7 s | Kompletan početni upis i kontrole |
| #3 — ponovljeni prenos | 45,8 s | Bez novih/izmenjenih knjiženja i operativnih duplikata |
| #4 — dopuna izvornim šifarnikom poslova | 76,4 s | Dopunjeni centri; preuzet jedan novi telefonski poziv |
| #5 — završna provera pune sinhronizacije | 48,0 s | Svih 22 skupa ponovo upotrebljeno; 0 novih/izmenjenih knjiženja i operativnih redova |

Jedan telefonski poziv unet u staroj Naplati između pokretanja #3 i #4 prenet je u novu
aplikaciju bez dupliranja ostalih poziva. Time je proveren i stvaran nastavak paralelnog rada.
Vremena su merenja ovog okruženja, ne garantovani rokovi budućih sinhronizacija.
Pokretanje #1 prekinuto je greškom kodiranja konzolnog ispisa; upis je vraćen transakcijom.
Kodiranje komandnog izlaza je ispravljeno pre prvog uspešnog prenosa.

## Zatečene stavke za proveru

| Oblast | Broj | Postupanje |
|---|---:|---|
| Kontakti bez potvrđene veze sa partnerom | 32 | Sačuvani original i novi nepovezan kontakt |
| Napomene bez potvrđene veze | 13 | Sačuvani original i nova nepovezana aktivnost |
| Opomene bez potvrđene veze | 16 | Sačuvani original i nova nepovezana opomena |
| Pravni postupci bez potvrđene veze | 4 | Ostali u postojećoj tabeli i kompletnoj arhivi |
| Otvorene stavke bez dospeća | 9 | Izvorni NULL ostao NULL |
| Otvorene stavke bez centra u izvornom šifarniku | 1 | Prikaz „Neraspoređeno”, bez nagađanja centra |

Prvih 65 problema vidi se na strani sinhronizacije. Nijedan od ovih zapisa nije odbačen.
Saldo devet stavki bez dospeća iznosi −310.678,54 RSD. Radi uporedivosti one u tabeli ostaju
u starom baketu 0,1, a zbirna kartica ih zasebno prikazuje. Neraspoređena stavka ima saldo
318.352,18 RSD i uključena je u ukupni iznos.

Centar se preuzima iz `posao.blok` po tačnoj šifri. Opšti registar organizacionih jedinica
nije potpun izvor za sve šifre poslova. Centar se ne zaključuje iz prve dve cifre.

## Ručno pokretanje, Celery i izvori

Na `/potrazivanja/sinhronizacija/` postoji dugme **Pokreni punu sinhronizaciju**.
Poziva običnu funkciju `sync_collections`; ista funkcija ima registrovan Celery zadatak
`potrazivanja.tasks.sync_collections_task`, sa redom `sync`. Novi periodični raspored nije
uključen. Za automatski rad potrebni su broker, worker i odgovarajući Beat raspored.

Postojeći raspored procedure `sp_AzurirajNalogZ` u 10 i 11 nije menjan, niti je procedura
pozivana tokom ovog prenosa. Novi import za sada čita postojeće view-ove Naplate sa svim
njihovim udaljenim zavisnostima; novi UI potom radi isključivo nad lokalnim podacima.

„Full” znači potpuni tekući sadržaj dogovorenih izvora i očuvanje prethodnih verzija,
ne kopiranje cele ERP baze. Obuhvat `baza` ostaje 2026, a `ispravke` 2025, prema potvrđenom
poslovnom pravilu. Istorijske pomoćne tabele zadržane su cele.

## Provere i preostali koraci

- Prošlo je 188 testova aplikacija Potraživanja, Finansije, Core i Naplata.
- Nakon završne izmene evidencije poslednjeg viđenja ponovo su prošla sva 34 testa Potraživanja.
- Migracije Potraživanja su primenjene i nema novih nedostajućih migracija za taj modul.
- Provereni su stvarni ekrani u pregledaču: pregled, detalj partnera, tab knjiženja i sinhronizacija.
  Svi detaljni tabovi započinju AJAX učitavanje bez otvaranja pojedinačnog taba; nisu zabeležene
  JavaScript greške niti neuspešni HTTP odgovori novih stranica.
- Testirani su ograničenja po centrima, direktni AJAX pristup, negativno sortiranje, dospeća,
  ponovljeni prenos, nestanak/ponovno pojavljivanje zapisa, lokalne izmene i povratak transakcije.

Sledeće faze su razrešavanje nepovezanih partnera i odvojeno dogovaranje prelaska poslovnog
unosa u novu aplikaciju. Novi Excel izvoz, potpuno praćenje SEF statusa po EDok.ID, automatsko
uparivanje uplata/faktura, zamena SQL izvora i preusmeravanje Finansija nisu deo ovog aktiviranja.

Tehnički opis i komande: [potrazivanja/README.md](../potrazivanja/README.md).
