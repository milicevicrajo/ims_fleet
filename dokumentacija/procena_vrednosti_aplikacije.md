# Procena tehničke i poslovne vrednosti IMS aplikacije

Datum procene: 28.04.2026.

Ovaj dokument je interna procena vrednosti, složenosti i obima IMS aplikacije. Procena nije formalna knjigovodstvena ili sudska procena vrednosti softvera, već inženjersko-poslovna procena zasnovana na stanju koda, poznatim modulima, produkcionoj upotrebi i poslovnim informacijama iz firme.

## 1. Sažetak procene

IMS aplikacija je interna ERP/operativna aplikacija za upravljanje flotom, garažom, putnim nalozima, potrošnjom goriva, naplatom, pravnom službom, menicama i administrativnim pravima. Aplikacija zamenjuje papirne evidencije, Excel fajlove, ručne obračune i rasute "mrtve podatke" koji ranije nisu bili operativno upotrebljivi.

Na osnovu trenutnog obima, realna eksterno naručena vrednost aplikacije je:

| Kategorija | Procena |
|---|---:|
| Tehnička zamenska vrednost postojećeg funkcionalnog obima | 90.000 - 150.000 EUR |
| Realna cena eksterne izrade sa analizom, QA, deployem i stabilizacijom | 120.000 - 220.000 EUR |
| Cena enterprise verzije sa jačim auditom, testovima, SLA, dokumentacijom i formalnom podrškom | 180.000 - 300.000 EUR |
| Interna tehnička vrednost postojeće aplikacije kao operativnog sredstva | 80.000 - 140.000 EUR |
| Godišnja poslovna vrednost u uštedama, kontroli i smanjenju rizika | 90.000 - 220.000 EUR godišnje |
| Procena složenosti | srednje-visoka do visoka |

Najrealnija jedinstvena procena za eksternu kuću, ako bi se danas naručila aplikacija ovog obima sa postojećom funkcionalnošću, jeste oko 150.000 EUR, uz očekivani raspon 120.000 - 220.000 EUR.

## 2. Ulazni podaci za procenu

Poslovni podaci:

| Stavka | Vrednost |
|---|---:|
| Broj vozila u evidenciji | oko 150 |
| Aktivni korisnici | preko 20 |
| Sektori / funkcije | uprava, flota, garaža, naplata, pravna služba, administracija; planirano širenje po sektorima |
| Potrošnja goriva | oko 500.000 EUR u poslednjih 12 meseci |
| Kataloška vrednost flote | oko 650.000 EUR |
| Obučena osoba za rad u aplikaciji | prati i ažurira podatke vezane za flotu, gorivo, vozila, dokumenta i operativne promene |
| NIS/OMV podaci | svakodnevno ažuriranje |
| Putni nalozi | oko 20 unosa dnevno |
| Istorijski podaci | poslednje 3 godine |
| Produkcija | postoji produkcioni server, backup i prava pristupa |
| Izveštaji | koriste se za interne zvanične izveštaje i odluke |
| Stanje pre aplikacije | papir, Excel, odvojene evidencije, deo podataka nije bio aktivno upotrebljiv |

Tehnički podaci iz repozitorijuma, bez vendor statičkih biblioteka i migracija:

| Stavka | Vrednost |
|---|---:|
| Custom fajlovi | oko 204 |
| Custom linije koda i šablona | oko 29.600 |
| Django modeli | 51 |
| URL rute | oko 229 |
| HTML šabloni u custom delu | oko 106 |
| Migracije | oko 70 |
| Glavni moduli | fleet, naplata, menice, administracija, garaža/putni nalozi, integracije i izveštaji |

## 3. Opis aplikacije

IMS aplikacija je Django poslovni sistem koji centralizuje više internih procesa u firmi. Po prirodi je bliža internom ERP sistemu nego jednostavnoj web aplikaciji.

### 3.1. Flota

Modul flote obuhvata evidenciju vozila, kartica, organizacionih jedinica, šifara poslova, lizinga, polisa, osiguranja, servisa, kvarova i drugih podataka koji su potrebni za upravljanje voznim parkom.

Ključna vrednost modula je što vozilo postaje centralna poslovna jedinica na koju se vezuju troškovi, dokumenta, gorivo, putni nalozi, kvarovi i izveštaji.

### 3.2. Garaža i putni nalozi

Modul garaže i putnih naloga podržava svakodnevni operativni rad. Putni nalozi se otvaraju, zatvaraju, štampaju i povezuju sa vozilima, kilometražom i potrošnjom goriva. Po trenutnom obimu upotrebe, oko 20 unosa dnevno znači da je ovo jedan od najoperativnijih delova aplikacije.

Vrednost ovog dela je u standardizaciji procesa koji bi inače bio papirni, sporiji i teži za kontrolu.

### 3.3. Potrošnja goriva i NIS/OMV integracije

Aplikacija uvozi i obrađuje potrošnju goriva iz NIS i OMV izvora. To uključuje Excel/CSV uvoze, mapiranje vozila, transakcije, izveštaje i povezivanje potrošnje sa vozilima i putnim nalozima.

Trošak goriva u poslednjih 12 meseci iznosi oko 500.000 EUR. Čak i mala poboljšanja u kontroli, validaciji i izveštavanju imaju konkretnu finansijsku vrednost. Realan direktan efekat kontrole goriva može biti 2% - 7% godišnje, odnosno 10.000 - 35.000 EUR godišnje, dok je šira vrednost u automatizaciji obračuna, smanjenju ručnog rada i bržem uočavanju odstupanja dodatno značajna.

Kataloška vrednost flote je oko 650.000 EUR. Kada se vrednost osnovnih sredstava posmatra zajedno sa godišnjim troškom goriva, jasno je da aplikacija ne prati sporednu administraciju, već upravlja imovinom i troškovima ukupne vrednosti preko 1.000.000 EUR godišnje posmatrano kroz vrednost flote i godišnji tok troška goriva.

### 3.4. Naplata

Modul naplate sadrži partnere, kontakte, napomene, opomene, pozive, bucket-e, ispravke, avanse, postupke i istoriju promena. Ovaj deo ima visoku poslovnu vrednost jer direktno utiče na kontrolu potraživanja, praćenje aktivnosti i bolju vidljivost statusa klijenata.

U sistemu koji ranije nije imao centralizovan ERP, ovaj modul ne donosi samo uštedu vremena, već uvodi operativnu disciplinu.

### 3.5. Pravna služba

Pravni modul se nastavlja na naplatu i omogućava evidenciju pravnih postupaka i statusa. Njegova vrednost je posebno važna jer pravni i naplatni procesi nose rizik rokova, izgubljene dokumentacije i nejasnog statusa predmeta.

### 3.6. Menice

Modul menica obuhvata izlazne menice, ulazne menice i registar menica. Izlazne menice se ažuriraju iz NBS podataka, ulazne se ručno evidentiraju prema fizičkoj lokaciji i poslovnom partneru, a registar upućuje na NBS registar.

Ovaj modul povećava finansijsku kontrolu i smanjuje rizik da se menice vode van sistema ili u odvojenim evidencijama.

### 3.7. Administracija i prava

Aplikacija ima role i prava pristupa, što je važno jer sistem koristi više od 20 korisnika i više poslovnih funkcija. Prava pristupa su ključna za širenje aplikacije po sektorima.

## 4. Tehnička složenost

Tehnička složenost se procenjuje kao 7.5/10 za trenutno stanje i 8.5/10 ako se aplikacija posmatra kao enterprise sistem koji treba eksterno održavati uz formalni SLA.

Razlozi:

| Oblast | Složenost | Obrazloženje |
|---|---:|---|
| Model podataka | visoka | 51 model, više domena, povezivanje vozila, goriva, pravnih i finansijskih podataka |
| Poslovna pravila | visoka | pravila su specifična za firmu i nisu generička |
| Importi i integracije | srednje-visoka | NIS, OMV, NBS menice, Excel/CSV, scraperi |
| Korisnički interfejs | srednja | mnogo tabela, formi, detalja, štampe i izveštaja |
| Izveštaji | srednje-visoka | koriste se za interne odluke i operativnu kontrolu |
| Prava pristupa | srednja | više uloga i sektora |
| Produkcija i održavanje | srednje-visoka | postoji server, backup, baza i operativna upotreba |
| Testiranje i formalna dokumentacija | trenutno srednji rizik | interni razvoj obično ima manje formalnog QA i dokumentacije nego eksterni enterprise projekat |

Najveća tehnička vrednost nije u pojedinačnim ekranima, već u povezanom modelu podataka i činjenici da aplikacija već radi nad stvarnim podacima, stvarnim procesima i stvarnim korisnicima.

## 5. Tehnička vrednost

Tehnička vrednost može da se posmatra kroz tri perspektive:

### 5.1. Zamenska vrednost

Zamenska vrednost je iznos koji bi firma morala da plati da eksterni tim ponovo napravi aplikaciju istog funkcionalnog obima.

Procena:

| Scenario | Procena |
|---|---:|
| Minimalna rekonstrukcija postojećeg obima, uz čvrstu specifikaciju | 90.000 - 150.000 EUR |
| Realna eksterna izrada od početka, uključujući analizu, QA, deploy i stabilizaciju | 120.000 - 220.000 EUR |
| Enterprise verzija sa punom dokumentacijom, testovima, audit logom, SLA i jačim DevOps procesom | 180.000 - 300.000 EUR |

### 5.2. Interna tehnička vrednost postojećeg sistema

Postojeći sistem već ima:

- funkcionalan kod,
- bazu modela,
- produkcionu upotrebu,
- istorijske podatke,
- poslovna pravila ugrađena kroz razvoj,
- realne korisnike,
- već rešene integracije i import logiku.

Zato je interna tehnička vrednost postojeće aplikacije procenjena na 80.000 - 140.000 EUR.

Ova vrednost nije isto što i cena prodaje na tržištu. To je vrednost zamene za firmu: koliko bi firmu koštalo da izgubi ovaj sistem i mora ponovo da ga dobije.

### 5.3. Rizici koji umanjuju tehničku vrednost

Potencijalni diskont na tehničku vrednost dolazi iz sledećih oblasti:

- aplikaciju su razvijale interne osobe, pa formalna dokumentacija može biti slabija od agencijskog standarda,
- test pokrivenost verovatno nije na nivou enterprise proizvoda,
- poslovno znanje je delom u glavama ljudi koji su razvijali sistem,
- deo funkcionalnosti je u aktivnom razvoju,
- dalji rast će tražiti jači audit, logovanje, dokumentaciju, procedure i eventualno refaktorisanje.

Ovo ne znači da je aplikacija manje korisna, već da bi eksterni održavalac morao da uloži dodatno vreme da preuzme sistem.

## 6. Poslovna složenost

Poslovna složenost je visoka, oko 8/10.

Razlozi:

- firma ranije nije imala ovakav centralizovan sistem,
- deo procesa je bio papirni,
- deo podataka je postojao, ali nije bio operativno živ,
- korisnici dolaze iz više funkcija,
- sistem se koristi za interne odluke,
- podaci se svakodnevno ažuriraju,
- postoji 3 godine istorije,
- naplata i pravna služba imaju poslovne posledice i rokove,
- flota, vozila i gorivo imaju direktan troškovni i imovinski uticaj.

Kod ovakvih sistema poslovna složenost često nadmašuje tehničku. Ekrani i tabele se mogu napraviti relativno brzo, ali tačno definisanje šta znači status, rok, dug, postupak, putni nalog, menica, trošak i vozilo zahteva dubinsko poznavanje firme.

## 7. Poslovna vrednost

Poslovna vrednost aplikacije dolazi iz četiri glavna izvora:

1. ušteda vremena,
2. bolja kontrola troškova,
3. smanjenje operativnog i pravnog rizika,
4. bolja dostupnost podataka za odluke.

### 7.1. Ušteda vremena

Pošto je aplikacija zamenila papir i razdvojene evidencije, realna ušteda nije samo u minutima po unosu. Vrednost je i u tome što sada proces postoji na jednom mestu.

Konzervativna procena uštede:

| Oblast | Procena uštede |
|---|---:|
| Putni nalozi i garaža | 10 - 20 sati nedeljno |
| Gorivo, NIS/OMV i obračuni | 8 - 20 sati nedeljno |
| Naplata i pravna služba | 15 - 35 sati nedeljno |
| Flota, dokumenta, izveštaji i administracija | 10 - 25 sati nedeljno |
| Ukupno | 43 - 100 sati nedeljno |

Na godišnjem nivou, uz 48 radnih nedelja, to je oko 2.000 - 4.800 sati godišnje. Ako se interni rad vrednuje samo 10 - 20 EUR po satu, sama vremenska ušteda daje 20.000 - 96.000 EUR godišnje.

Realnija vrednost je viša jer se ne štedi samo vreme administracije, već se dobijaju brži izveštaji, manje grešaka i bolja kontrola.

### 7.2. Kontrola goriva

Trošak goriva u poslednjih 12 meseci je oko 500.000 EUR. Ako sistem kroz bolju kontrolu, usklađivanje i izveštavanje spreči samo 2% - 7% nepravilnosti, grešaka ili neoptimizovanih troškova, efekat je 10.000 - 35.000 EUR godišnje.

Ovo je direktno merljiv deo. Indirektno, modul goriva je važniji jer obezbeđuje poverenje u podatke po vozilu, putnom nalogu i organizacionoj jedinici. Kod flote kataloške vrednosti oko 650.000 EUR, precizno vezivanje troškova za vozila pomaže i kod odluka o zadržavanju, zameni, otpisu, servisiranju i realnom ukupnom trošku vlasništva.

### 7.3. Naplata i pravna služba

Naplata i pravna služba imaju najveći potencijalni poslovni efekat, jer bolji pregled predmeta i aktivnosti može smanjiti propuštene rokove, nejasne statuse i slabiju naplatu.

Bez tačnog iznosa potraživanja ne može se dati precizna cifra, ali za firmu sa stalnom naplatom i pravnim predmetima realna poslovna vrednost ovog dela može biti 20.000 - 80.000 EUR godišnje, zavisno od obima potraživanja, broja predmeta i kvaliteta discipline pre aplikacije.

### 7.4. Upravljački izveštaji

Pošto se aplikacija koristi za zvanične interne izveštaje i odluke, poslovna vrednost nije samo operativna. Uprava sada ima centralizovan pogled na podatke koji su ranije bili fragmentirani.

Ovo povećava vrednost aplikacije jer sistem utiče na odluke, kontrolu i odgovornost.

### 7.5. Ukupna poslovna vrednost

| Scenario | Godišnja vrednost |
|---|---:|
| Konzervativno | 60.000 - 90.000 EUR |
| Realno za trenutnu upotrebu | 90.000 - 220.000 EUR |
| Visok efekat uz punu upotrebu naplate, pravne službe, flote i uprave | 220.000 - 350.000+ EUR |

Najrealnija procena trenutne godišnje poslovne vrednosti je 120.000 - 180.000 EUR, sa rastom kako se flota, kadrovi, ugovori i menice budu više koristili. Sam modul goriva, zbog obima od oko 500.000 EUR za poslednjih 12 meseci, opravdava ozbiljniji nivo kontrole, automatizacije i infrastrukture.

## 8. Procena vremena razvoja od nule

Ako bi eksterni tim danas kretao od nule, vreme ne bi zavisilo samo od programiranja. Veliki deo vremena otišao bi na otkrivanje procesa, definisanje pravila, čišćenje podataka i usaglašavanje sa korisnicima.

### 8.1. Vreme osmišljavanja od nule

| Aktivnost | Procena sati |
|---|---:|
| Snimanje procesa po sektorima | 120 - 250 |
| Definisanje poslovnih pravila | 150 - 350 |
| Model podataka i arhitektura | 100 - 220 |
| Mapiranje postojećih Excel/papirnih evidencija | 120 - 300 |
| Provera sa korisnicima i upravom | 80 - 180 |
| Ukupno osmišljavanje | 570 - 1.300 sati |

Kalendarski, ovo je 2 - 4 meseca intenzivnog rada, a u firmi bez prethodnog ERP sistema lako može da traje 4 - 6 meseci paralelno sa razvojem.

Uloga koleginice ekonomiste koja je prikupljala podatke i poslovna pravila je veoma važna. Bez te uloge, eksterni tim bi morao da angažuje poslovnog analitičara i da potroši značajno više vremena na radionice sa zaposlenima.

### 8.2. Vreme razvoja

| Oblast | Procena sati |
|---|---:|
| Backend i modeli | 700 - 1.200 |
| Forme, tabele, detalji, liste i UI | 600 - 1.100 |
| Putni nalozi, štampe i obračuni | 250 - 500 |
| NIS/OMV importi i izveštaji goriva | 250 - 500 |
| Naplata i pravna služba | 500 - 900 |
| Menice i NBS povezivanje | 180 - 350 |
| Prava pristupa i administracija | 150 - 300 |
| Migracija i čišćenje istorijskih podataka | 250 - 600 |
| Testiranje i stabilizacija | 400 - 900 |
| Deploy, backup, produkcija i dokumentacija | 150 - 350 |
| Projektni menadžment i koordinacija | 250 - 600 |
| Ukupno razvoj i isporuka | 3.680 - 7.300 sati |

Za eksternu kuću realniji opseg za isporuku trenutnog funkcionalnog obima je 3.000 - 5.000 sati. Gornji deo opsega važi ako se traže formalni testovi, dokumentacija, audit log, SLA i enterprise nivo kvaliteta.

### 8.3. Kalendarsko trajanje

| Tim | Procena trajanja |
|---|---:|
| Jedan iskusan programer + interna poslovna podrška | 12 - 24 meseca, u zavisnosti od raspoloživosti |
| Mali eksterni tim od 3 osobe | 9 - 15 meseci |
| Eksterni tim od 4 - 5 osoba | 6 - 12 meseci |
| Enterprise isporuka sa QA, PM, BA i DevOps disciplinom | 12 - 18 meseci |

To što je aplikaciju radio jedan programer uz koleginicu ekonomistu ne znači da aplikacija ima malu vrednost. Naprotiv, interni razvoj često smanjuje kalendarsko trenje jer su ljudi blizu problema, ali ne eliminiše stvarnu vrednost uloženog znanja.

## 9. Eksterna cena po scenarijima

Tržišne pretpostavke za 2026. godinu:

- Istočna Evropa i regionalni outsourcing često se kreću oko 25 - 55 USD/h za razvojne uloge, zavisno od senioriteta i modela angažovanja.
- Agencijska blended satnica za poslovni sistem obično je viša od čiste developerske satnice, jer uključuje PM, QA, analizu, DevOps i overhead.
- Za Srbiju i region realan blended budžetski raspon za ozbiljnu eksternu isporuku je 35 - 65 EUR/h, a za jači enterprise angažman 60 - 90 EUR/h.

Procena:

| Scenario | Sati | Satnica | Cena |
|---|---:|---:|---:|
| Lean rekonstrukcija uz jasnu specifikaciju | 2.500 - 3.500 | 35 - 50 EUR | 90.000 - 150.000 EUR |
| Realna eksterna izrada od nule | 3.500 - 5.000 | 40 - 60 EUR | 140.000 - 240.000 EUR |
| Enterprise izrada sa punim procesom | 4.500 - 7.000 | 50 - 80 EUR | 225.000 - 560.000 EUR |

Za ovu aplikaciju bih kao realnu pregovaračku procenu naveo 120.000 - 220.000 EUR. Ispod 90.000 EUR bi verovatno značilo da se izbacuje deo analize, testiranja, dokumentacije ili stabilizacije. Preko 220.000 EUR ima smisla ako se zahteva formalni enterprise standard, audit, SLA i širi skup modula.

## 10. Posebna vrednost internog rada

Važno je odvojiti dve stvari:

1. koliko bi koštalo da se aplikacija napiše,
2. koliko vredi znanje koje je ugrađeno u aplikaciju.

U ovom slučaju veliki deo vrednosti je nastao kroz rad jednog programera i koleginice ekonomiste koja je prikupljala podatke i poslovna pravila. To je praktično kombinacija:

- programera,
- poslovnog analitičara,
- implementatora ERP sistema,
- data migration osobe,
- support osobe,
- internog product owner-a.

Eksterna kuća bi te uloge naplatila odvojeno. Zato aplikaciju ne treba vrednovati samo kao "Django kod", već kao operativni sistem koji sadrži poslovno znanje firme.

### 10.1. Vrednost obučene osobe za operativno održavanje flote

Posebna poslovna vrednost nastaje kada postoji obučena osoba koja svakodnevno radi u aplikaciji i prati sve što je potrebno za flotu. Ta osoba nije samo korisnik softvera, već operativni čuvar kvaliteta podataka.

Njena uloga obuhvata:

- ažuriranje podataka o vozilima, karticama, dokumentima, polisama, registracijama i statusima,
- praćenje potrošnje goriva i povezivanje transakcija sa vozilima,
- kontrolu kilometraže, putnih naloga, servisa, kvarova i troškova,
- proveru da li su podaci kompletni, tačni i upotrebljivi za izveštaje,
- komunikaciju sa korisnicima, garažom, administracijom i upravom,
- rano uočavanje nelogičnosti, kašnjenja i grešaka u evidenciji.

Bez takve osobe aplikacija bi i dalje imala tehničku vrednost, ali bi poslovna vrednost bila niža jer bi kvalitet podataka zavisio od povremenih i nepovezanih unosa. Sa obučenom osobom sistem postaje živa operativna baza: podaci se ne samo čuvaju, već se aktivno održavaju, proveravaju i koriste.

Ova uloga je praktično interna kombinacija fleet administratora, data steward-a i prvog nivoa aplikativne podrške. Kod flote od oko 150 vozila, kataloške vrednosti oko 650.000 EUR i godišnjeg troška goriva od oko 500.000 EUR, takva osoba direktno povećava vrednost aplikacije jer obezbeđuje da izveštaji, kontrole i odluke budu zasnovani na ažurnim podacima.

## 11. Opravdanost kupovine servera

Kupovina zasebnog servera za IMS aplikaciju je poslovno opravdana jer aplikacija više nije pomoćni alat, već operativni sistem koji čuva i obrađuje podatke o floti, gorivu, putnim nalozima, naplati, pravnim predmetima, menicama i pravima korisnika.

Najvažnije činjenice za opravdanje:

| Stavka | Poslovni značaj |
|---|---|
| Trošak goriva | oko 500.000 EUR u poslednjih 12 meseci |
| Kataloška vrednost flote | oko 650.000 EUR |
| Broj vozila | oko 150 |
| Broj korisnika | preko 20, uz planirano širenje |
| Procesi | flota, garaža, putni nalozi, gorivo, naplata, pravna služba, menice, prava |
| Podaci | istorijski, operativni i finansijski relevantni podaci |

U takvom kontekstu server nije samo IT trošak. Server je infrastruktura za kontrolu imovine i troškova. Ako aplikacija pomogne da se samo 1% troška goriva bolje kontroliše, to je oko 5.000 EUR godišnje. Ako efekat bude 2% - 7%, vrednost je 10.000 - 35.000 EUR godišnje samo na gorivu, bez uračunavanja uštede vremena, manje grešaka i bolje naplate.

### 11.1. Zašto je potreban namenski server

Namenski server je opravdan iz sledećih razloga:

- aplikacija se koristi svakodnevno i treba da bude dostupna više sektora,
- baza podataka sadrži poslovno kritične podatke,
- Celery worker-i i beat pokreću automatske zadatke, uvoze i sinhronizacije,
- Selenium importi za NIS/OMV i drugi sync procesi mogu biti teži od običnih web zahteva,
- SQL Server, Django aplikacija, Redis, logovi i backup treba da rade stabilno i odvojeno od korisničkih računara,
- server omogućava kontrolisan backup, monitoring, pristupna prava i lakši oporavak u slučaju problema.

Korišćenje običnog desktop računara ili slabog deljenog servera povećava rizik prekida rada, gubitka automatizacije, sporih izveštaja i problema sa backup-om. Kod sistema koji prati flotu od oko 650.000 EUR i godišnji trošak goriva od oko 500.000 EUR, takav rizik nije proporcionalan uštedi na hardveru.

### 11.2. Preporučena serverska konfiguracija

Za trenutni obim aplikacije preporučuje se manji poslovni server, ali sa ECC memorijom, RAID skladištem i prostorom za rast.

Minimalno prihvatljivo:

| Komponenta | Preporuka |
|---|---|
| CPU | 6 - 8 jezgara, server/workstation klasa |
| RAM | 32 GB ECC |
| Disk za sistem i aplikaciju | 2 x NVMe SSD u mirror/RAID 1 režimu, najmanje 1 TB |
| Backup disk / storage | odvojeni disk ili NAS za dnevni backup |
| Mreža | 1 GbE minimalno, poželjno 2.5/10 GbE ako postoji infrastruktura |
| OS | Windows Server ako se zadržava postojeći SQL Server/Windows način rada |
| UPS | obavezan, zbog baze i rizika od korupcije podataka |

Preporučeno za mirniji rad i rast:

| Komponenta | Preporuka |
|---|---|
| CPU | 8 - 12 jezgara |
| RAM | 64 GB ECC |
| Disk | 2 x enterprise NVMe SSD 1 - 2 TB u mirror/RAID 1 režimu |
| Backup | lokalni backup + eksterni/NAS/offsite backup |
| Garancija | 3 - 5 godina poslovne garancije, poželjno next business day |

Primer odgovarajuće klase servera:

- Dell PowerEdge T350/T360 ili sličan tower server,
- HPE ProLiant ML30/ML110 klasa,
- Lenovo ThinkSystem ST50/ST250 klasa,
- ekvivalentan poslovni server sa ECC memorijom, redundantnim diskovima i garancijom.

Za ovu aplikaciju nije neophodan skup enterprise rack server, ali nije preporučljiv ni običan kancelarijski PC. Najrazumniji izbor je tower server srednje klase sa 64 GB ECC RAM-a, RAID 1 NVMe diskovima, UPS-om i uređenim backup-om. Takva investicija je mala u odnosu na vrednost podataka, vrednost flote i godišnji trošak goriva koji aplikacija kontroliše.

### 11.3. Finansijsko opravdanje servera

Ako server sa UPS-om, diskovima, licencama i osnovnim podešavanjem košta okvirno 3.000 - 8.000 EUR, njegova vrednost se opravdava već kroz:

- smanjenje rizika prekida rada i gubitka podataka,
- stabilnije automatske uvoze i sinhronizacije,
- pouzdanije izveštaje za upravu,
- bolju zaštitu podataka i kontrolu pristupa,
- manji rizik ručnog rada kada automatizacija zakaže,
- čak i veoma mali procenat bolje kontrole goriva.

Kod godišnjeg troška goriva od oko 500.000 EUR, server od 5.000 EUR odgovara približno 1% godišnjeg troška goriva. Ako server omogući stabilan rad sistema koji spreči samo deo grešaka, kašnjenja ili nepravilnosti, investicija je racionalna.

## 12. Zaključak

IMS aplikacija ima visoku internu vrednost jer rešava realne operativne probleme firme sa 150 vozila, preko 20 korisnika, svakodnevnim unosima, godišnjom potrošnjom goriva od oko 500.000 EUR, kataloškom vrednošću flote od oko 650.000 EUR i više sektora koji zavise od tačnih podataka. Dodatnu vrednost daje obučena osoba koja kroz aplikaciju prati i ažurira operativno stanje flote, čime sistem ostaje živ, tačan i upotrebljiv za odluke.

Tehnički gledano, aplikacija je srednje-visokog obima i složenosti. Poslovno gledano, složenost je još veća jer je sistem nastao u firmi koja ranije nije imala centralizovan ERP i gde su mnogi procesi bili papirni ili rasuti.

Najkraća procena:

- tehnička složenost: 7.5/10,
- poslovna složenost: 8/10,
- interna tehnička vrednost: 80.000 - 140.000 EUR,
- realna eksterna cena izrade: 120.000 - 220.000 EUR,
- godišnja poslovna vrednost: 90.000 - 220.000 EUR,
- vreme razvoja od nule: 9 - 15 meseci za mali eksterni tim, odnosno 12 - 24 meseca za jednog programera uz internu poslovnu podršku.

Ako se aplikacija nastavi širiti na kadrove, ugovore, menice i sektorsku upotrebu, njena poslovna vrednost će rasti brže od tehničke vrednosti, jer će sve više poslovnih odluka i procesa zavisiti od jedinstvene baze podataka. Iz istog razloga je opravdano ulaganje u stabilan namenski server, backup i automatizaciju, jer infrastruktura direktno štiti sistem koji kontroliše imovinu i troškove velikog obima.

## 13. Izvori za tržišne pretpostavke

Korišćeni su javno dostupni izvori za okvirne cene razvoja softvera u 2026. godini:

- Andersen Lab: https://andersenlab.com/blueprint/custom-software-development-costs-in-2026
- Craft Soft: https://craft-soft.com/insights/custom-software-development-pricing
- Codebridge: https://www.codebridge.tech/articles/software-development-outsourcing-rates-costs-and-trends
- Keyhole Software: https://keyholesoftware.com/cost-custom-software-development/
- GoodFirms: https://www.goodfirms.co/resources/custom-software-development-cost-survey

Za serversku preporuku korišćene su zvanične stranice proizvođača za aktuelne tower server klase:

- Dell PowerEdge T360: https://www.dell.com/en-us/shop/cty/pdp/spd/poweredge-t360/pe_t360_15330_os_vi_vp
- HPE ProLiant ML30 Gen11: https://www.hpe.com/us/en/compute/hpe-proliant-compute/ml30-gen11.html
- Lenovo ThinkSystem ST250 V3: https://www.lenovo.com/us/en/p/servers-storage/servers/towers/thinksystem-st250-v3-tower-server/len21ts0025

Ovi izvori se koriste samo kao tržišni okvir za satnice, budžetske opsege i klasu serverske opreme. Konkretna procena u ovom dokumentu je prilagođena stvarnom obimu IMS aplikacije i poslovnim informacijama firme.
