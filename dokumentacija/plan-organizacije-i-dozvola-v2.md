# Centralna organizacija i dozvole — plan realizacije po koracima

Datum: **18.09.2026.** · Status: **predlog, bez implementacije**

Ovaj plan dopunjuje [plan centralizacije organizacije](plan-centralizacije-organizacije.md)
i proširuje ga na jedinstven sistem dozvola i administraciju kroz samu IMS aplikaciju.
Za redosled narednih radova koristiti ovaj dokument. Pravila istorije, stalnog identiteta,
profitnosti, aktivnosti i očuvanja izvornih podataka iz prethodnog plana ostaju osnova.
Pregledani su kod i postojeća dokumentacija; raniji brojevi šifara nisu ponovo popisivani u bazi.

**Cilj:** jedno stablo **centar → organizaciona jedinica → šifra posla**, na koje se vezuju
podaci i obuhvat korisnikovih uloga. Sve redovne dodele održavaju se kroz odeljak
**Admin** u aplikaciji, sa pretragom, karticama, stablom i pregledom efektivnih prava.
Poslovnom administratoru nije potreban Django admin niti status superuser.

## 1. Šta postoji i šta treba promeniti

| Zatečeno u kodu | Značenje za plan |
|---|---|
| `OrganizationalUnit` čuva šifru, naziv i tekst centra; nema tri nivoa ni verzije | Dodati centralni registar i mapu starih ID-eva, bez trenutnog premeštanja modela |
| `Role`, `PermissionCode`, `RolePermission` i `CustomUser.roles` već postoje | Zadržati identitete uloga i dozvola; nadograditi dodelu uloge obuhvatom |
| Korisnik ima M2M `allowed_centers` ka OJ i tekst `allowed_center_codes` | Ovi nazivi nisu pouzdan opis obuhvata; zamenjivati ih potvrđenim vezama ka stablu |
| Finansije dodaju centar iz dodeljene OJ; Potraživanja takođe izvode centar iz OJ | Pojedinačna dodela sada može proširiti pristup na druge poslove istog centra |
| `CenterMixin` Flote podrazumevano dozvoljava rad bez obuhvata; Finansije tada vraćaju prazan skup | Nema jedinstvenog značenja praznog obuhvata; ne menjati ponašanje svih modula odjednom |
| Uloge i organizacioni obuhvat korisnika vode se odvojeno | Nedostaje veza „ova uloga važi baš za ovaj centar/posao” |
| Admin aplikacije ima listu korisnika i povezivanje sa zaposlenim; uređivanje uloga i obuhvata je u Django adminu | Proširiti postojeći Admin kompletnim poslovnim interfejsom |
| `UserListView` u pregledanom kodu traži prijavu, a izmene profila proveravaju superuser | Uvesti posebna prava za pregled korisnika, uređivanje i dodelu pristupa na svim rutama |
| `sync_permission_codes` ne registruje samo kodove: dodeljuje/uklanja neka prava i povezuje grupe sa ulogama | Pre novog editora razdvojiti katalog dozvola od promena koje administrator održava |
| Kreiranje profila zaposlenog može izvesti centar iz prefiksa HR oznake | U budućnosti predlagati potvrđenu mapu; zaposlenje nije automatska dozvola za poslovne podatke |
| Finansije sada čitaju potraživanja iz lokalne aplikacije Potraživanja | Pilot obuhvata oba modula i njihove međusobne linkove; stara Naplata ostaje zaseban legacy modul |
| Potraživanja za operativne izmene trenutno traže i `view_all`, a više vrsta evidencije deli ista prava | Regionalno uređivanje zahteva prilagođavanje tih provera; novi editor ne sme samo dodeliti `view_all` da bi unos proradio |

Ovo su nalazi za planiranje. U okviru ovog zadatka nisu menjane provere pristupa,
dodele korisnika, administracija, modeli niti sinhronizacije.

## 2. Organizaciona struktura

```text
Firma — granica podataka, nije četvrti poslovni nivo
└── Centar 43
    └── Organizaciona jedinica 6       puna oznaka: 436
        ├── Šifra posla 111           puna šifra: 436111
        └── Šifra posla 22            puna šifra: 43622
```

Svaki čvor ima stalni interni ID. Šifra, naziv, nadređeni čvor i statusi imaju verzije
sa datumom važenja. Veze roditelj–dete su eksplicitne: pripadnost se ne utvrđuje
sečenjem šifre ili proverom prefiksa. Segmenti su tekst, čuvaju vodeće nule i mogu
imati različite dužine; puna šifra mora biti jednoznačna u firmi i periodu važenja.

Krajnja šifra ima nezavisne oznake **profitna/neprofitna** i **aktivna/neaktivna**.
Neaktivnost blokira tekući novi unos prema poslovnom datumu, ali ne briše istoriju
niti ukida mogućnost kontrolisane korekcije starog dokumenta. Mesečni koeficijenti
obračuna ostaju posebni podaci; registar ne menja formule ZT i novčanih tokova.

Naziv drugog nivoa u planu je „organizaciona jedinica”. Postojeća kadrovska OJ nije
automatski taj nivo: mapiranje mora biti potvrđeno. Ako se utvrdi da jedno odeljenje
ima više nezavisnih šifara poslova, proveriti poslovni model pre migracije; ne spajati
različite poslove niti uvoditi skriveni četvrti nivo samo da bi podaci stali u stablo.

## 3. Osnovno pravilo dozvola: uloga zajedno sa obuhvatom

**Uloga određuje šta korisnik sme da radi. Obuhvat te dodele određuje nad kojim podacima.**
Korisnik dobija jednu ili više dodela oblika:

`korisnik + uloga + firma + organizacioni obuhvat + vreme važenja`

| Primer dodele | Efekat |
|---|---|
| Pregled Finansija · centar 43 sa potomcima | Čitanje finansijskih podataka dostupnih centru 43 |
| Referent Potraživanja · OJ 436 sa potomcima | Dozvoljene radnje nad poslovima te OJ, uz posebna pravila zajedničkih partnera |
| Pregled Potraživanja · posao 436111 | Samo taj posao, bez ostalih poslova OJ ili centra |
| Urednik Flote · centar 41; Pregled Flote · centar 43 | U centru 41 može uređivanje, u centru 43 samo pregled |
| Pregled Finansija · cela firma | Svi organizacioni podaci te firme u okviru te uloge; ne daje upravljanje korisnicima |
| Administrator pristupa | Upravljanje korisnicima/ulogama u dozvoljenim granicama; ne daje automatski čitanje svih zarada i finansija |

Poslednja dva primera razlikuju „sve poslovne podatke” od „administrira sistem”.
Organizacioni obuhvat sam ne daje pravo na novi modul.

### Kako se donosi odluka

Pristup je dozvoljen ako postoji **najmanje jedna trenutno važeća dodela** čija aktivna
uloga sadrži traženu radnju i čiji obuhvat pokriva konkretan zapis u istoj firmi.
Za neaktivnog korisnika nema pristupa. I dalje važe pravila dokumenta, npr. zaključen
obračun ne postaje izmenjiv samo zato što korisnik ima opšte pravo izmene.

Ne sme se uzeti zbir svih korisnikovih radnji i nezavisno zbir svih njegovih centara:
to bi iz prethodnog primera pogrešno dalo pravo uređivanja i u centru 43.
Prava više dodela sabiraju se samo kroz cele parove **uloga–obuhvat**.

Predložena pravila za prvu verziju:

- Bez odgovarajuće dodele nema pristupa organizacionim podacima. Prazno ne znači „sve”.
- Centar i OJ podrazumevano uključuju potomke; interfejs to jasno ispisuje i pokazuje spisak poslova.
- Šifra posla nikada ne daje pravo na roditelja, braću ili ceo centar.
- „Cela firma” je poseban, vidljiv izbor sa posebnim pravom dodeljivanja.
- Pravo „sopstveni podaci” za profil zaposlenog je zasebna politika vlasništva; nije pristup svim podacima njegovog centra.
- Nema pojedinačnih skrivenih dozvola mimo uloga. Izuzetak se rešava posebnom, jasno imenovanom ulogom i dodelom.
- U prvoj verziji nema mešanja dozvola i eksplicitnih zabrana. „Centar osim jednog posla” rešava se izborom tačnih grana/poslova, uz prikazan način nasleđivanja.
- Rok dodele pristupa i period podataka nisu isto. Dodela može trajati do kraja meseca,
  a dozvoljavati istorijske dokumente. Ako je potrebna granica datuma podataka, vodi se zasebno i jasno prikazuje.

## 4. Sistematizacija, promena šifre i pristup istoriji

Promena naziva ili šifre istog posla ne menja njegov ID. Dodela direktno poslu zato
ostaje vezana za taj posao; ne nestaje i ne prelazi na drugog samo zato što je oznaka promenjena.
Podela ili spajanje poslova pravi nove identitete i pregled novih dodela, bez automatskog
umnožavanja pristupa. Stara i nova spoljna šifra povezuju se potvrđenom mapom i datumom.

**Predlog za istorijske dokumente:** obuhvat centra/OJ proverava se prema potvrđenoj
organizacionoj pripadnosti zapisa na njegov poslovni datum. Datum određuje adapter modula
(npr. knjiženje, dokument, period rada), a ne korisnikov izbor pogleda ili datuma na ekranu.

Primer: posao pređe iz centra 43 u 44 od 01.01.2027. Ranija knjiženja ostaju u istorijskom
obuhvatu centra 43; nova ulaze u 44. Direktna dodela stalnom poslu može pokriti oba perioda,
što mora jasno pisati u pregledu pristupa. Ako novi rukovodilac treba i celu prethodnu
istoriju prenetog posla, dobija eksplicitnu dodelu tom poslu, po potrebi samo za čitanje.
Prikaz rezultata po novoj organizaciji ne proširuje dozvoljeni skup podataka.

Za tekuće resurse, poput vozila i aktuelnog zaduženja, adapter koristi odgovarajuću
važeću dodelu resursa. Za Potraživanja poslovni datum/organizacija moraju biti dosledni
izabranom objavljenom snimku i poreklu stavke; istorija registra ne stvara istorijski
finansijski snimak koji ne postoji. Ova pravila se potvrđuju i testiraju po modulu.

Ako istorijska pripadnost nije dokaziva, zapis dobija oznaku „istorija nepotvrđena” i
mapu na dan prelaska. Korisnik sa ograničenim obuhvatom ne dobija takav zapis preko
pretpostavljenog prefiksa ili pravila „nepoznato je dostupno svima”. Za pilot se izuzetak
razrešava ili odgovarajući deo ostaje na postojećem pristupu dok se mapiranje ne potvrdi.

Objava sistematizacije prikazuje i promenu pristupa: koje dodele nasleđuju nove poslove,
koji zapisi menjaju tekući obuhvat, ko dobija/gubi pristup i šta ostaje u istorijskom centru.
Nov posao ispod dodeljene grane nasleđuje obuhvat prema ovom pravilu; administrator to
vidi pre objave. Promena organizacije i osvežavanje keša pristupa izvršavaju se usklađeno.

## 5. Predlog podataka i jedinstvene provere

Radni nazivi modela služe planiranju, nisu zahtev da se postojeće tabele preimenuju.

| Celina | Odgovornost |
|---|---|
| `OrgNode` | Stalni identitet, firma, nivo 1/2/3 |
| `OrgNodeVersion` | Naziv, segment, puna šifra, roditelj, aktivnost, profitnost i važenje od/do |
| `ExternalOrgMapping` | Izvor, firma, izvorna šifra/ključ, period i centralni identitet; čuva se sirova oznaka |
| Veze starih modela | Postojeći `OrganizationalUnit`, `FinanceJob` i ostali podaci povezuju se bez gubitka starih ID-eva |
| `OrgChangeSet` | Nacrt promene sistematizacije, datum primene, validacija, pregled uticaja i objava |
| Postojeći `Role` i `PermissionCode` | Uloge i katalog poslovnih radnji; oznake modula, grupe i čitljivi nazivi |
| `UserRoleAssignment` | Korisnik, uloga, firma, važenje, status, autor i razlog dodele |
| `AssignmentScope` | Dodela + centar/OJ/posao, način uključivanja potomaka ili eksplicitna cela firma |
| Evidencija promena pristupa | Ko je promenio šta, pre/posle, razlog, vreme i verzija konfiguracije |

Za firme, dozvole, vremenske intervale i veze definisati ograničenja baze i validaciju
na serveru. Nema ciklusa, preklopljenih organizacionih verzija ili aktivne dodele drugoj
firmi. Na dokumentima/stavkama ostaju izvorna šifra i istorijski snimak pored nove veze.

Jedna zajednička usluga treba da podrži: proveru radnje, filtriranje dostupnog skupa,
proveru pojedinačnog objekta, objašnjenje pristupa i pregled posledica promene.
Postojeći dekoratori, mixin-i i modulski adapteri postepeno pozivaju tu uslugu.
Nije dovoljno promeniti sidebar: ista pravila važe za direktan URL, AJAX, izbor u formi,
izvoz/štampu, datoteke, zbirne iznose, izmenu i grupne radnje.

Filter obuhvata primenjuje se u bazi pre paginacije i sabiranja. Keš zavisi od verzije
korisnikovih dodela, uloge i organizacije; opoziv mora važiti za naredni zahtev bez
ponovne prijave. Dugotrajni izvozi ponovo proveravaju pravo pre isporuke fajla.
Sistemski Celery uvoz ima sopstveni servisni pristup i ne zavisi od centra korisnika
koji je kliknuo dugme; dozvola za pokretanje uvoza je zasebna, globalna radnja modula.

## 6. Posebni slučajevi koji ne smeju proširiti pristup

| Slučaj | Predloženo pravilo |
|---|---|
| Partner ima dugovanja u više centara | Prikazati dostupne stavke i njihove zbirove, bez otkrivanja drugih centara |
| Kontakti, napomene i pravni postupak pripadaju celom partneru | Nisu automatski vlasništvo jednog centra. U prvom pilotu zadržati centralna prava uređivanja; za regionalni unos prvo definisati vidljivost/vlasništvo zapisa |
| Faktura ili zahtev ima više šifara posla | Ograničen izveštaj može prikazati dozvoljene stavke uz oznaku delimičnog prikaza. Izmena celog dokumenta i preuzimanje originala traže obuhvat svih stavki ili posebno pravo |
| Zbir/ZT koristi osnovicu cele firme | Služba obračuna sme računati punu osnovicu, ali prikaz vraća samo dozvoljeni rezultat; ne izlagati tuđe stavke kroz detalje |
| Veza Finansije → Potraživanja | Proveravaju se prava ciljnog modula. Pravo Finansija nije zamena za pravo Potraživanja |
| Nova ili nepovezana šifra u uvozu | Sačuvati izvorni podatak i upozorenje; ne dodeljivati centar po prefiksu niti svima otvoriti zapis |
| Skrivanje zarada i drugih osetljivih polja | Posebna radnja/dozvola, nezavisna od običnog pregleda centra |
| Promena HR radnog mesta korisnika | Predlog za pregled dodela, bez tihog prepisivanja poslovnih prava |

## 7. Admin panel u aplikaciji

Admin zadržava zajednički header i stil aplikacije. Predložene sekcije bočnog menija:
**Organizacija**, **Korisnici**, **Uloge i dozvole**, **Provera pristupa**,
**Sistematizacija**, **Mapiranja i uvozi**, **Istorija promena**.

### Organizacija

Levo pretraživo stablo sa tri nivoa, desno kartica izabranog čvora. Pretraga radi po
staroj/novoj šifri i nazivu. Kartica ima tabove **Podaci**, **Podređene jedinice**,
**Korisnici i pristup**, **Istorija**, **Povezivanja**. Aktivne/neaktivne i profitne/neprofitne
oznake su tekstualni bedževi; značenje ne zavisi samo od boje. Izmena organizacije sa
datumom primene vodi u nacrt i pregled uticaja, ne u prepisivanje stare vrednosti.

### Korisnici

Tabela: korisnik, zaposleni, status, uloge, sažetak obuhvata i datum poslednje izmene.
Detalj ima tabove **Profil**, **Dodele uloga**, **Efektivni pristup**, **Istorija**.
Svaka dodela je zaseban red/kartica: uloga, firma, izbor centra/OJ/posla, nasledni
obuhvat i važenje. Obuhvati više uloga ne prikazuju se kao jedna zajednička lista centara.

Tok „Dodaj dodelu”: izaberi ulogu → izaberi stablo/obuhvat → proveri konkretne radnje
i poslove → sačuvaj uz razlog. U stablu razlikovati direktno označeno, nasleđeno i
delimično izabranu granu. Selekcija jednog posla ne označava roditelja kao potpuno dodeljenog.
„Kopiraj dodele korisnika” prikazuje razlike pre čuvanja i ne kopira superuser privilegije.

### Uloge i dozvole

Lista uloga sa opisom, statusom i brojem korisnika. Detalj prikazuje module kao kartice,
a unutar njih grupisane radnje: pregled, unos, izmena, arhiviranje, izvoz, odobravanje,
sinhronizacija i druge radnje koje modul zaista podržava. Tehnički nazivi ruta nisu glavni
tekst interfejsa. Prekidači imaju čitljive oznake; „sve u modulu” prikazuje šta uključuje.
Novo pravo dodato u kod ne uključuje se automatski svim postojećim ulogama.

Katalog poslovnih radnji ima eksplicitnu mapu ka postojećim rutama i servisima; nije
samo automatski spisak URL-ova. U Potraživanjima prikazati odvojene celine Kontakti,
Pozivi, Napomene, Opomene, Pisma i Pravni postupci. Ako treba nezavisno dodeljivanje
njihovih radnji, podeliti sadašnja zajednička prava uz mapu prenosa. Editor ne sme
prikazivati odvojene prekidače koje server zapravo tretira kao jedno pravo.

Uloga je skup radnji, a konkretan centar bira se pri dodeli korisniku. Zbog toga ne treba
praviti posebnu kopiju iste uloge za svaki centar. Izmena zajedničke uloge prikazuje
sve pogođene korisnike i promenu njihovih radnji pre čuvanja.

### Provera pristupa

Izbor korisnika, modula, radnje i konkretnog posla/dokumenta daje odgovor
**dozvoljeno / nije dozvoljeno**, uz objašnjenje: koja dodela, koji predak i koje pravilo.
Prikazati i razlog odbijanja, npr. nema radnje, istekao rok ili zapis van obuhvata.
Ovo je objašnjenje prava, ne prijavljivanje kao drugi korisnik. Dostupno samo ovlašćenom administratoru.

### Ko sme da administrira

Razdvojiti pregled organizacije, uređivanje stabla, objavu sistematizacije, pregled
korisnika, dodelu uloga, uređivanje sadržaja uloga i pregled evidencije promena.
U prvoj isporuci prava dodeljuje centralni administrator. Delegiranje rukovodiocima
centara je naredna faza sa ograničenjem koje uloge i čije obuhvate smeju dodeliti.
Administrator ne može sebi ili drugome dodeliti više nego što njegova administrativna
politika dozvoljava, niti običnim editorom menjati superuser. Sprečiti uklanjanje poslednjeg
aktivnog administratora. Svaka promena se proverava na serveru i beleži atomski.

Django admin ostaje tehnički alat za održavanje, a ne redovan put za dodelu ovih prava.
Nakon prelaska njegove editore istih polja učiniti samo za čitanje ili ukloniti, kako
ne bi postojao drugi put koji zaobilazi validaciju, evidenciju i osvežavanje keša.

## 8. Redosled implementacije i uslovi završetka

| Korak | Rad i rezultat | Uslov za nastavak |
|---|---|---|
| **0. Popis i pravila** | Ponoviti popis šifarnika, korisnika, uloga, svih ulaza i zadataka koji menjaju prava. Napraviti tabelu sadašnjeg pristupa po modulu i korisniku, mapu tri nivoa i spisak izuzetaka. Potvrditi pravilo istorije iz ovog plana. | Postoji početni kontrolni izveštaj i jasno označene nerešene odluke |
| **1. Centralni registar** | Dodati aplikaciju organizacije, stalne ID-eve, verzije, mape izvora i Admin stablo sa pregledom istorije. Uvesti prvo centar 43 sa potvrđenim OJ/poslovima, pa preostali šifarnik. | Validni nivoi, bez kolizija i ciklusa; stari ekrani i uvozi rade kao ranije |
| **2. Model dodela i katalog radnji** | Dodati dodelu uloga sa obuhvatom i jedinstvenu uslugu provere. Zadržati postojeće uloge i kodove. Odvojiti registraciju kataloga od uređivanja prava, ukinuti automatsko vraćanje povučenih prava kroz stare sync skripte za prenete uloge. | Testirano sabiranje parova uloga–obuhvat, tačan posao ne daje ceo centar; UI izmene opstaju posle sinhronizacije kataloga |
| **3. Admin korisnika i uloga** | Izraditi sve kartice, stablo izbora, matricu radnji, pregled efektivnog pristupa, istoriju i pregled promena pre čuvanja. Zaštititi i listu korisnika i sve pomoćne rute. | Administrator može potpuno održavati pilot korisnike kroz aplikaciju, bez Django admina |
| **4. Probni prenos i paralelna provera** | Prevesti stare dodele u nacrt novih. Nova provera računa očekivani pristup uz postojeću, bez upravljanja produkcionim odgovorom. Izvesti sve proširene/sužene skupove i promene radnji. | Svaka razlika je razrešena ili eksplicitno evidentirana kao namerna; nema tihih proširenja |
| **5. Pilot: Potraživanja i Finansije** | Dodati centralne veze lokalnim podacima i adaptere za liste, detalje, AJAX, filtere, izvoz i međumodulske linkove. Aktivirati za izabrane korisnike i potvrđenu granu, zatim proširiti. | Isti iznosi za isti skup, potvrđena zabrana tuđih podataka, proverena istorija i opoziv; nema povratka na udaljene view-ove pri otvaranju |
| **6. Flota i putni nalozi** | Povezati vozila, dodele, troškove i naloge; zameniti lokalna tumačenja centara uz poštovanje datuma dodele i prava nad sopstvenim podacima. | Nema promene brojeva dokumenata ni istorije zaduženja; testirani korisnici bez obuhvata |
| **7. Ostali moduli** | Nabavka, HR, Ugovori, Menice, Mobilni, Isplate i preostale pravne funkcije — svaki sa svojim mapiranjem, pravilima zapisa i kontrolom. Legacy Naplata ostaje na starom režimu do zasebne odluke o njenom gašenju/prebacivanju. | Za svaki modul završen njegov kontrolni izveštaj i zatvoren pregled svih ulaznih tačaka |
| **8. Sistematizacija i usklađeni uvozi** | Pustiti tok nacrt → pregled uticaja na podatke i pristup → objava od datuma. Utvrditi jednog vlasnika upisa po polju i povezati potvrđene promene staro → novo. | Promena naziva/šifre/roditelja prolazi bez gubitka istorije i neočekivanog pristupa; paralelni zadaci ne prepisuju jedni druge |
| **9. Stabilizacija i uklanjanje duplog održavanja** | Po modulima isključiti stare editore i zadatke, ukloniti zavisnost od tekstualnih korisničkih centara i starih provera; zadržati izvorne kolone i evidenciju koliko je potrebno za istoriju. | Svi aktivni moduli koriste isti sistem; stare veze više ne upravljaju pravima; postoji proverljiv povratak i dokumentacija |

Koraci 0–4 pripremaju rad; korak 5 je prvo prebacivanje poslovnih ekrana na nova prava.
Model buduće sistematizacije nastaje u koraku 1, a puna operativna objava kroz izvore
pušta se u koraku 8. Ako sistematizacija mora ranije, korak 8 se deli i deo za pilot
završava pre njegovog aktiviranja. Ne čekati kraj migracije da bi se zaštitila istorija.

**Prva konkretna isporuka:** popis i potvrđena pravila, centralno stablo, pregled u Adminu
i početno mapiranje. Sledeća isporuka su dodele sa obuhvatom i Admin interfejs. Tek zatim
aktivirati nova prava u poslovnim modulima. To omogućava da se izgled i logika ocene
na stvarnom primeru centra 43 pre prenosa cele aplikacije.

## 9. Prenos bez prekida sinhronizacije i gubitka prava

Stare M2M veze uloga nemaju dovoljno podataka da opišu različit obuhvat po ulozi.
Probni prenos zato polazi od stvarnog ponašanja svakog modula, a ne samo od naziva
polja. Stari `view_all` prevodi se u eksplicitnu dodelu cele firme za odgovarajuće
radnje, ne u univerzalni pristup svim modulima. Stare Django grupe i imenovane uloge
koje zaobilaze katalog ulaze u isti popis; ne uvoditi još jedan paralelan izvor prava.

Finansijsko knjiženje zadržava svoj postojeći poslovni ključ i iznose. Potraživanja
zadržavaju objavljivanje snimaka i svoje kontrole. Dodaju se veze i potvrđene mape;
ne menja se izvorni dokument zbog novog naziva centra. Uvoz nepoznate šifre ne sme
izazvati gubitak finansijskih iznosa: zapis se čuva, problem mapiranja evidentira, a
ograničeni pristup rešava pre uključivanja novog režima za taj skup.

Prava se ne osvežavaju iz ERP-a zajedno sa poslovnim šifarnikom. Izvor može predložiti
novi posao ili promenu zaposlenja; pravo pristupa je zasebna odluka održavana u Adminu.
Katalog novih radnji može se dopunjavati iz koda, ali ne sme menjati sačuvane uloge
ili ponovo dodavati povučene dodele. Početni predlošci uloga primenjuju se eksplicitno,
uz pregled razlika, umesto pri svakom periodičnom pokretanju.

Pre svake faze napraviti rezervnu kopiju i probu na kopiji baze. Nove veze prvo su
opcione, a povezivanje se radi u ponovljivim paketima. Uključivanje novog režima mora
biti dosledno za sve rute jednog modula/korisnika: nema pravila „stari ILI novi pristup”.

Povratak na staru proveru dozvoljen je samo ako može prikazati poslednje potvrđene
dodele bez proširenja prava. Stara globalna lista centara ne može uvek predstaviti
„uređivanje 41, pregled 43”; tada se pogođeni novi pristup privremeno zatvara i ispravlja,
umesto da se korisniku ponovo otvori širi legacy obuhvat. Poslovni zapisi se ne brišu.

## 10. Provere pre puštanja

| Kontrola | Očekivani rezultat |
|---|---|
| Korisnik ima samo 436111 | Ne vidi 43622 ni ostale poslove centra 43 |
| Korisnik ima OJ 436 | Vidi njene dozvoljene potomke, bez drugih OJ centra |
| Korisnik ima centar 43 | Vidi odgovarajuću istoriju i potomke centra po definisanim pravilima |
| Urednik 41 + čitalac 43 | Ne može izmeniti zapis centra 43 ni preko direktnog POST/AJAX zahteva |
| Prazan obuhvat, istekla dodela, neaktivna uloga/korisnik | Nema pristupa organizacionim podacima |
| Opozvana dodela ili izmenjena uloga | Naredni zahtev koristi novu odluku; stari keš/izvoz ne otkriva podatke |
| Promena naziva/šifre istog posla | Direktna dodela ostaje na istom identitetu; stari dokument zadržava snimak |
| Premeštanje posla i podela/spajanje | Rezultat odgovara potvrđenom pravilu istorije; nema automatskog umnožavanja prava |
| Datum filtra ili istorijskog pogleda se menja | Ne može proširiti autorizovani skup |
| Mešoviti partner/faktura i preuzimanje originala | Nema prikaza tuđih stavki kroz zbir, kontakt, prilog ili izvoz |
| Druga firma, nepovezana šifra, nepotvrđena istorija | Nema podrazumevanog pristupa |
| Sinhronizacija šifarnika i kataloga dozvola | Ne briše istoriju, ne vraća povučena prava i ne menja finansijske kontrolne zbirove |
| Korisnik pogodi skriveni URL ili ID dokumenta | Dobija istu zabranu kao kroz interfejs |
| Dva administratora menjaju istu dodelu | Sukob je prikazan; nema tihog prepisivanja, promena i evidencija su celina |
| Prelazak i povratak modula | Ne izgube se novi unosi; ne vrati se prethodno opozvan pristup |

Pored funkcionalnih provera meriti vreme lista, agregata i izvoza pre/posle. Obuhvat se
ne rešava jednim upitom po redu. Indeksi, keš po verziji i skupno razrešenje pripadnosti
moraju biti provereni na stvarnom obimu; hijerarhija ne sme vratiti sporo učitavanje.

## 11. Odluke za početak realizacije

Predlog je da se prihvati model tri nivoa iz ovog plana, dodela **uloga + obuhvat**,
centralna administracija u prvoj fazi i istorijski pristup prema pripadnosti dokumenta.
Pre punog uvoza potrebni su potvrđena mapa drugog nivoa, datum sistematizacije i spisak
starih/novih šifara sa oznakom da li je promena identiteta ili samo šifre/naziva.

Pre pilota treba potvrditi ko je administrator pristupa, koje uloge sme održavati i
da li postoje posebni zahtevi za pristup staroj istoriji prenetih poslova. Pravilo za
operativne podatke zajedničkog partnera posebno potvrditi pre omogućavanja regionalnog
uređivanja kontakata, napomena i pravnih predmeta. Ove odluke ne sprečavaju izradu
registra i prototipa Admin interfejsa.

Složenost je **srednja za registar i UI, visoka za usklađivanje prava i istorije kroz sve
module**. Ne zahteva prepisivanje cele aplikacije, ali nije samo dodavanje tri tabele.
Rok proceniti po završenom koraku 0 i potvrđenom pilotu, umesto obećanja za celu
migraciju dok izuzeci nisu popisani.

## 12. Mesta proverena za ovaj plan

- [Prethodni plan organizacije](plan-centralizacije-organizacije.md).
- [Zajednički modeli i korisnički obuhvat](../core/models.py).
- [Provere uloga](../core/mixins.py) i [sinhronizacija dozvola](../core/permissions.py).
- [Korisnici u aplikaciji](../fleet/views/users.py), [postojeći Django admin](../fleet/admin.py)
  i [kreiranje profila zaposlenih](../fleet/services/employee_user_profiles.py).
- [Obuhvat Flote](../fleet/mixins.py), [Finansija](../finansije/access.py)
  i [Potraživanja](../potrazivanja/access.py).
- [Lokalni ugovor podataka Potraživanja](../potrazivanja/services/reports.py)
  i [povezivanje sa Finansijama](../finansije/services/job_tables.py).

Ovim zadatkom je napravljen plan. Implementacija, migracije i promena stvarnih prava
korisnika predstavljaju naredne, odvojene korake.
