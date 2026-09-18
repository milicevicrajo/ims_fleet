# Procena prenosa trebovanja u Nabavku

11.09.2026. — pregled koda, lokalnih podataka i definicija SQL izvora. Status: procena i predlog; modeli, poslovni podaci, uvozi i prava nisu menjani.

## 1. Zaključak i preporuka

Prenos modela Requisition iz fleet aplikacije u nabavka aplikaciju je izvodljiv. Preporučujem da trebovanje postane poseban model izdatog materijala u Nabavci, radnog naziva MaterialIssueLine. Postojeći GoodsSnapshot ostaje evidencija druge vrste robnih dokumenata. Ovo nije spajanje dve kopije istih podataka: izvori biraju različite vrste dokumenata.

Najmanji koristan zahvat je promena vlasništva nad modelom, uz početno zadržavanje postojeće fizičke SQL tabele fleet_requisition, svih ID-jeva, kolona i vrednosti. Flota zatim koristi model Nabavke za prikaz i povezivanje sa vozilom/nalogom. Naziv fizičke tabele može se promeniti kasnije; on ne određuje gde korisnik vodi evidenciju. Ne ostavljati dva aktivna Django modela koji nezavisno upisuju istu tabelu.

U Nabavci bi postojali: zahtevi za kupovinu/uslugu, fakture, postojeća roba i trebovanja/izdati materijal. To su različiti događaji. Nabavka 20 filtera i izdavanje jednog filtera određenom vozilu moraju biti razlikovani, ali se svaki događaj evidentira samo jednom. Garaža vodi nalog i potvrdu rada; nabavka materijala nije potvrda da je servis izvršen.

Orijentacioni obim preporučenog prenosa: **24–40 radnih sati, približno 3–5 radnih dana jednog programera**, uz dostupnu bazu i proveru reprezentativnih dokumenata. To je inženjerska procena, ne garantovan rok. Ne obuhvata kompletno odobravanje garaže, novi magacin, servisne intervale ili prenos Service/ServiceTransaction modela.

## 2. Proverena razlika SQL izvora

| Izvor | Šta stvarno bira | Posledica |
| --- | --- | --- |
| dbo.fleet_trebovanja | Transakcije sa sif_dok = 40; godina najmanje 2026; magacin sif_mag1 = 14; dodatni uslovi nad registarskom oznakom | Ovo je izvor sadašnjih trebovanja Flote. Nije kompletna istorija 2024–2025, niti dokaz obuhvata svih IMS magacina. |
| dbo.nbv_roba | Transakcije sa sif_dok = 10 od 2025, povezane sa knjiženjima vrste KA i zadatim kontima | Ovo nije isti skup dokumenata. Postojeći GoodsSnapshot ne zamenjuje izdavanja iz izvora 40. |

Sif_dok (10/40) označava izvorni tip robnog dokumenta. Postojeći GoodsSnapshot.document_type dobija sif_vrs iz knjiženja, npr. KA. Te dve šifre ne predstavljaju isti podatak; eventualni zajednički model mora ih čuvati odvojeno.

Pronađeno je 76 podudaranja nepotpunog poslovnog ključa između lokalnih trebovanja i robe, ali nijedno istovremeno ne odgovara po artiklu, količini, ceni i datumu. Pošto se razlikuje izvorna vrsta dokumenta, ovih 76 podudaranja nisu dokaz duplikata i ne smeju biti automatski spojena.

Broj dokumenta i godina sami nisu dovoljan identitet. Trenutni Requisition koristi jedinstvenost: sif_pred + god + br_dok + sif_vrsart + stavka. Pri objedinjavanju više izvora mora se dodati poreklo i izvorna vrsta dokumenta, uz potvrdu ključa osnovne ERP evidencije.

## 3. Stanje podataka za prenos

Brojevi su rezultat čitanja 11.09.2026; nisu finansijska revizija niti fizički popis. Više upita nije predstavljeno kao jedna atomska kopija baze.

| Pokazatelj | Nalaz |
| --- | --- |
| Lokalne stavke trebovanja | 2.980 |
| Grupe dokumenata po sif_pred, god i br_dok | 698 |
| Godina 2024 | 1.007 stavki; zbir postojeće vrednosti 1.889.995,95 |
| Godina 2025 | 1.202 stavke; zbir postojeće vrednosti 2.715.498,14 |
| Godina 2026 | 771 stavka; zbir postojeće vrednosti 2.285.615,90 |
| Ukupan lokalni zbir vrednost_nab | 6.891.109,99; aplikacija ga prikazuje kao RSD, bez nove potvrde finansijske metodologije |
| Veza sa vozilom | 2.978 stavki ima vozilo; 2 nemaju |
| Veza sa nalogom garaže | Trenutno 0; polje postoji i mora ostati dostupno |
| Dodeljena kategorija | 2.209 stavki |
| Uneta kilometraža | 1.833 stavke |
| Napomena | 13 stavki |
| Vrednost različita od zaokruženog proizvoda lokalne količine i cene | 8 stavki; razlog nije utvrđen, originalnu vrednost sačuvati |
| Lokalna roba Nabavke | 6.660 redova; 23 stavke zahteva već imaju vezu sa robom |

Sadašnji izvor trebovanja vraća 935 jedinstvenih stavki. Za 771 postoji lokalni zapis i nema razlika u proverenim poljima: artikal, količina, cena, vrednost i datum. Preostale 164 izvorne stavke nemaju lokalni ključ. Lokalnih 2.209 stavki iz 2024–2025 nije u sadašnjem izvoru jer je on vremenski ograničen.

Zato se migracija ne sme izvesti brisanjem lokalne tabele i ponovnim uvozom. Time bi nestala ranija istorija i lokalne dopune. Dodatnih 164 stavke treba preuzeti kao jasno odvojenu sinhronizaciju posle kontrolnog preseka; njihov uticaj na zbir mora biti posebno objašnjen. Nisu preuzete tokom ove procene.

## 4. Polja i veze koje treba sačuvati

| Trenutna polja | Šta bi značio direktan prelazak na GoodsSnapshot | Preporučeno postupanje |
| --- | --- | --- |
| id | Roba ima sopstvene ID-jeve i druge dokumente | Zadržati stare ID-jeve u prvom koraku. Ako se kasnije kopira u novu tabelu, obavezna je trajna mapa stari ID → novi ID. |
| sif_pred, god, br_dok, sif_vrsart, stavka | Postoje slična polja, ali različit izvor i domen ključa | Zadržati postojeći ključ za izdavanja; pri zajedničkom modelu dopuniti izvornu vrstu i poreklo. |
| sif_art, naz_art | Slična polja; naziv u robi ograničen na 80, u trebovanju na 255 znakova | Sačuvati postojeće granice i sadržaj. Trenutno nema naziva preko 80, ali to nije razlog za sužavanje budućeg unosa. |
| kol, cena | Postoje količina i cena, ali za drugi događaj | Preneti neizmenjene, uz razliku između kupovine i izdavanja. |
| vrednost_nab | Nema istog eksplicitnog polja; debit je izveden iz knjiženja | Sačuvati originalnu vrednost stavke. Ne zamenjivati je debit poljem niti obavezno preračunavati kol × cena. |
| datum_trebovanja, mesec_unosa | Roba koristi drugi datum; mesec nema neposredan par | Sačuvati oba postojeća podatka. Eventualno uklanjanje izvedenog meseca uraditi odvojeno nakon provere. |
| vehicle_id, kvar_id | GoodsSnapshot nema te direktne veze | U prenetom modelu ostaju isti FK ka vozilu i nalogu. Povezivanje sa nabavnim zahtevom nije obavezno. |
| popravka_kategorija_id | Nema istog polja u robi | Sačuvati šifru i vezu, bez promene značenja starih kategorija. ServiceType ostaje gde trenutno jeste. |
| kilometraza | Nema odgovarajućeg polja u robi | Sačuvati. To je istorijska dopuna dokumenta, ne nova potvrda izvršenog servisa. |
| nije_garaza, napomena | Nema odgovarajućih polja u robi | Sačuvati; napomenu ne izgubiti pri uvozu koji iz izvora vraća prazan tekst. |

Sva polja Requisition modela obuhvaćena su mapom. U prvoj fazi nije potrebno istovremeno menjati sve nazive polja, izdvajati zaglavlje dokumenta, menjati šifarnike ili uvoditi opšti računovodstveni model.

## 5. Varijante i izbor

| Varijanta | Procena | Odluka |
| --- | --- | --- |
| Obrisati Requisition i samo čitati postojeći GoodsSnapshot | Ne pokriva iste izvorne dokumente, istoriju i poslovne dopune | Ne prihvatati kao migracioni plan. |
| Preneti Requisition u Nabavku kao model izdatog materijala; sačuvati fizičku tabelu u početku | Najmanji zahvat; jedna evidencija bez kopiranja redova; postojeća roba nastavlja da radi | Preporuka za sadašnji cilj. |
| Napraviti opšti model robnih kretanja za ulaz, izdavanje i povrat, uz zasebne poslovne raspodele | Dugoročno moguće, ali zahteva širi model, proširene izvore i prevezivanje postojećih veza Nabavke | Poseban projekat ako se pojavi potreba za punim praćenjem magacina; nije potreban da bi se ukinuo paralelan unos. |

Po preporučenoj varijanti, Nabavka dobija poseban pregled „Trebovanja / izdati materijal“ nad jedinom evidencijom izdatog materijala. U Floti ostaje prikaz tog materijala uz vozilo/nalog i postojeći izveštaji. Njihov izgled i smisao ne moraju se preuređivati; menja se izvor podataka. Korisnik ne unosi stavku jednom u Nabavci i drugi put u Floti.

Zahtev za kupovinu nije uslov za postojanje trebovanja: za deo sa zalihe može postojati samo nalog garaže i izdavanje. Sadašnja štampa trebovanja iz zahteva može ostati obrazac traženog materijala; sama ne stvara potvrđeno ERP izdavanje.

## 6. Gde promena utiče na aplikaciju

| Oblast | Potrebna dorada |
| --- | --- |
| Model i Django migracije | Premestiti vlasništvo modela u Nabavku, očuvati podatke, indekse i unique ograničenje; proveriti redosled zavisnosti aplikacija. |
| Uvoz | Preneti servis za preuzimanje iz dbo.fleet_trebovanja u Nabavku; zadržati identitet izvora i zaštitu lokalnih dopuna. |
| Celery i raspoređeni poslovi | Prevezati fleet.tasks.fetch_requisition_data_task, izvoz iz fleet.sync i konfiguraciju periodičnog posla. Ne ostaviti dva nezavisna uvoznika za istu evidenciju. |
| Lista, detalj, dopune, unos i brisanje | Prebaciti postojeće prikaze/forme i DataTables upit na jedini model. Sačuvati prečice ili preusmeravanja; ugasiti odvojen ručni unos u Floti nakon prelaska. |
| Vozilo — Troškovi | Zadržati isti period i zbir vrednost_nab, uz čitanje prenetog modela. |
| Vozilo — Servisi | Zadržati kategoriju, datum dokumenta i veze naloga. Ne pretvarati istorijsko trebovanje u potvrdu rada. |
| Kontrolna tabla, Analitika, statistika centara | Prevezati subquery i agregacije; numerički rezultati istog zamrznutog skupa moraju ostati jednaki. |
| Upozorenja i nedostajuće veze | Zadržati prikaz stavki bez vozila i nije_garaza pravilo. |
| Izveštaji, linkovi i prava | Očuvati dostupnost pregleda, štampe i dozvole postojećih korisnika; pregledati prilagođene kodove ruta i Django ContentType/Permission reference. |
| Testovi i istorijske komande | Prevezati aktivne testove i podržane komande; već primenjene migracije ne prepisivati. |

Direktne zavisnosti su proverene u fleet/models.py, fleet/forms/services.py, fleet/views/services.py, fleet/views/datatables.py, fleet/views/vehicles.py, fleet/views/analytics.py, fleet/views/center_statistics.py, fleet/support/vehicle_detail.py, fleet/support/vehicle_maintenance.py, fleet/support/dashboard.py, fleet/support/fleet_snapshot.py, fleet/sync/services.py, fleet/tasks.py, fleet/urls.py i core/management/commands/sync_celery_periodic_tasks.py, uz povezane šablone i komande uloga.

Postojeći detalj grupiše trebovanje samo po godini i broju, dok jedinstveni ključ sadrži i sif_pred. Pri prevezivanju detalja proveriti kolizije i koristiti pun identitet dokumenta, da različiti dokumenti ne budu objedinjeni samo zbog istog broja.

## 7. Predlog migracije u koracima

1. Sačuvati rezervnu kopiju i kontrolni presek svih postojećih redova, ID-jeva, veza, kategorija, kilometraže, napomena i zbirnih vrednosti. Za konačan prelazak uskladiti kratko zaustavljanje upisa/uvoza; dnevni rad pre toga ne mora da se prekida.
2. U izolovanoj kopiji pripremiti model Nabavke nad postojećom tabelom. Ime MaterialIssueLine je radni predlog. Očuvati tipove polja i postojeće veze; nema ponovnog povezivanja istorije preko današnjih tablica.
3. Migracijama odvojiti Django stanje od fizičkih operacija tamo gde se zadržava ista tabela. Razmotriti SeparateDatabaseAndState i eksplicitne međuzavisnosti; običan DeleteModel iz Flote praćen CreateModel u Nabavci ne sme obrisati i ponovo napraviti tabelu sa podacima. Testirati i nadogradnju stare baze i kreiranje nove prazne baze.
4. Preneti aktivne upite, forme, uvoz i zadatke na jedini model. Očuvati kompatibilnost starih linkova i zadataka tokom kontrolisanog prelaza, bez trajnog održavanja dva izvora upisa.
5. Usaglasiti Django ContentType i ugrađene dozvole sa novim app/model identitetom; posebno proveriti prilagođene dozvole aplikacije. Prenos modela ne sme slučajno dati ili oduzeti prava korisnicima.
6. Uporediti stari i novi prikaz nad istih 2.980 redova: svi ID-jevi i veze, zbir po godini, vozilu i mesecu, kategorije, kilometraža i napomene. Nije dovoljno proveriti samo ukupan broj.
7. Odvojeno pokrenuti kontrolisano preuzimanje novih stavki. Trenutnih 164 su nalaz na datum procene; pre izvršenja broj ponovo izračunati. Zabeležiti šta je dodato, promenjeno ili ostalo nerazrešeno.
8. Prebaciti produkciono korišćenje, ukloniti fleet.Requisition iz aktivnog modela i ugasiti paralelan unos. Istorijske migracije ostaju deo istorije projekta. Fizičko preimenovanje tabele planirati tek kada se provere eventualne spoljne SQL zavisnosti; nije uslov za završetak funkcionalnog prenosa.

Plan povratka: pošto se početno čuva tabela i podaci, vratiti kompatibilnu verziju koda i stanje migracija prema unapred testiranom postupku. Ne vraćati staru kopiju baze preko novijih upisa bez njihovog očuvanja. Mapa starih linkova i identiteta mora ostati dostupna tokom prelaza.

## 8. Procena rada i uslovi

| Posao | Orijentaciono vreme |
| --- | --- |
| Završna provera izvora, kontrolni presek i dogovor migracionog obuhvata | 2–4 sata |
| Prenos modela, stanje migracija, ContentType i dozvole | 4–6 sati |
| Prevezivanje prikaza, obračuna, linkova i povezivanja u Nabavci/Floti | 6–10 sati |
| Prenos uvoza, zakazanih poslova i zaštita lokalnih dopuna | 4–6 sati |
| Proba migracije, kontrola iznosa i veza, test povratka i dokumentacija | 8–14 sati |
| Ukupno | 24–40 sati, približno 3–5 radnih dana jednog programera |

Procena pretpostavlja zadržavanje sadašnjeg poslovnog značenja i početno iste SQL tabele. Ne uključuje čekanje na korisničku proveru, otklanjanje problema dostupnosti baze, novi obračun magacina, opštu raspodelu jedne stavke na više vozila, istorijsku rekonstrukciju nepovezanih dokumenata ili izmene drugih modula. Ako se traži opšti model svih robnih kretanja, potrebno je posebno proceniti taj širi obuhvat.

Glavna neizvesnost nije količina redova nego očuvanje istorije, migracionog redosleda, dozvola i obračuna. Uočenih osam razlika vrednosti treba objasniti pre eventualne promene obračunske formule; prenos može sačuvati postojeće iznose bez čekanja na takvu promenu.

## 9. Uslovi da prenos bude prihvaćen

- Svih 2.980 početnih stavki i njihovih ID-jeva postoji posle prenosa; ne gubi se 2.209 istorijskih stavki koje sadašnji izvor ne vraća.
- Veze ka vozilu/nalogu, kategorije, 1.833 očitavanja kilometraže i 13 napomena ostaju očuvani; prazno ostaje prazno.
- Zbirovi postojećeg skupa su jednaki po godini, vozilu i mesecu. Preuzimanje novih redova proverava se zasebno.
- Ponovljen uvoz ne stvara duplikate; izmena izvorne stavke ne gubi poslovne dopune niti briše istoriju odsutnu iz filtriranog izvora.
- Nabavna roba tipa 10 ne spaja se sa izdavanjem tipa 40 zbog istog broja dokumenta/stavke.
- Postojećih 23 veza stavki zahteva sa GoodsSnapshot ostaje očuvano; ovaj prenos ih ne premešta na trebovanja.
- Detalj vozila, Servisi, Troškovi, Analitika, centri, liste, štampa i upozorenja čitaju jedinu evidenciju i rade pod odgovarajućim ulogama.
- Posle prelaska postoji samo jedan aktivan postupak upisa/sinhronizacije trebovanja. Korisnik ne ponavlja unos u dva modula.
- Nadogradnja postojeće baze, kreiranje nove baze i plan povratka provereni su u izolovanom okruženju pre primene.

## 10. Dokazi i granice provere

Dokazni presek je izvestaji/procena_prenosa_trebovanja_20260911.json. Definicije pregledanih izvora premeštene su 18.09.2026. u [`ddl-nasledjenih-pogleda/`](ddl-nasledjenih-pogleda/README.md) — `fleet_trebovanja.sql` i `nbv_roba.sql`. Skripta `procena_prenosa_trebovanja_audit.py`, koja je samo čitala izvor i upisivala lokalni zbirni izveštaj, uklonjena je iz repozitorijuma; dostupna je kroz git istoriju.

Sadašnja provera razrešava prethodnu neizvesnost iz dokumenta o toku garaže: baza je dostupna i potvrđeno je da postojeća roba Nabavke nije isto što i trebovanja Flote. Nisu izvršeni prenos modela, migracije ili dopuna 164 stavke. Nije potvrđena računovodstvena ispravnost svih istorijskih iznosa. Ocenjena je tehnička izvodljivost prenosa uz očuvanje postojećeg ponašanja.
