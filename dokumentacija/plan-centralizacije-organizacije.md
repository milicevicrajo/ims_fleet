# Plan centralizacije organizacije i šifara posla

Datum plana: **18.09.2026.**

**Predlog:** uvesti centralni registar sa tačno tri poslovna nivoa, stalnim internim identitetom i istorijom promena. Postojeće module povezivati postepeno, uz očuvanje njihovih ID-eva, dokumentacije, obračuna i sinhronizacije. Ovaj dokument je plan; centralizacija još nije implementirana.

Prvi nivo je centar, drugi je njegova podjedinica, a treći krajnje odeljenje odnosno poslovna šifra koja se koristi na dokumentima. Primeri korisnika su `43 / 6 / 111 → 436111` i `43 / 6 / 22 → 43622`. Završni deo nema obavezno tri cifre. Naziv drugog nivoa u interfejsu usaglasiće se sa sistematizacijom; njegova strukturna uloga je već definisana.

## 1 Poslovna pravila tri nivoa

| Nivo | Lokalna oznaka u primeru | Puna šifra |
|---|---|---|
| Centar | 43 | 43 |
| Podjedinica centra | 6 | 436 |
| Krajnje odeljenje odnosno posao | 111 ili 22 | 436111 ili 43622 |

Veze između nivoa čuvaju se eksplicitno. Puna šifra nastaje spajanjem segmenata od korena do krajnjeg nivoa, bez separatora. U interfejsu prikazujemo i razdvojenu putanju radi čitljivosti. Pripadnost ne određujemo naknadnim sečenjem teksta niti proverom prefiksa.

Šifre i segmenti čuvaju se kao tekst, uz očuvanje vodećih nula. Ne propisujemo obrazac dve cifre + jedna cifra + tri cifre za sve postojeće podatke samo na osnovu primera. Validacija mora da spreči da dve različite putanje daju istu punu šifru u istoj firmi i preklapajućem periodu.

Firma je zaseban obuhvat registra i jedinstvenosti, a ne četvrti poslovni nivo. Novi posao na trećem nivou mora imati potvrđena oba nadređena nivoa. Stare šifre koje ne možemo pouzdano rasporediti ostaju na listi za mapiranje; ne izmišljamo im odeljenje da bismo popunili stablo. Moduli do njihovog razrešenja nastavljaju da koriste postojeće podatke.

Kadrovske OJ, knjigovodstvene OJ i nova tri nivoa nisu unapred isti šifarnik. Mogu da se povežu nakon potvrde poslovnog značenja. Zaposleni može pripadati jednoj jedinici, a raditi na više poslovnih šifara.

## 2 Aktivnost i profitni status

Svaka krajnja poslovna šifra ima dve obavezne i nezavisne oznake: **profitna ili neprofitna**, odnosno **aktivna ili neaktivna**. Profitna ne znači da je rezultat pozitivan; to je klasifikacija posla. Obe oznake imaju istoriju i datum od kojeg važe.

Aktivnost se vodi i za nadređene jedinice. Isključivanje centra ili drugog nivoa blokira izbor njegovih potomaka za nove unose od datuma promene, ali ne briše njihove istorijske statuse. Na višim nivoima profitni status se ne nasleđuje automatski na poslove. Ako se naknadno uvede klasifikacija centra, to je posebno pravilo.

Neaktivna šifra ostaje u istorijskim izveštajima, dokumentima, dodelama vozila i obračunima. Izbor za novi dokument proverava datum dokumenta i važenje šifre. Naknadni unos za stari period i korekcije imaju kontrolisan postupak; trenutna neaktivnost sama po sebi ne sme onemogućiti ispravku starog dokumenta.

Prema proveri izvora i lokalnih Finansija od 18.09.2026, dostupno je 415 poslovnih šifara: 88 aktivnih profitnih, 250 aktivnih neprofitnih, 22 neaktivne profitne i 55 neaktivnih neprofitnih. Izvor koristi `profitni=P/N` i `aktivan=D/N`. Neočekivana ili prazna oznaka ide na proveru, bez automatskog pretvaranja u neprofitnu ili neaktivnu.

Mesečna pravila `posao_mes`, uključujući profitnost, aktivnost i koeficijente raspodele, ostaju zaseban obračunski podatak. Centralna oznaka ne zamenjuje ova pravila i ne menja formule zajedničkih troškova ili novčanih tokova tokom prve migracije.

## 3 Zatečeno stanje aplikacije

| Oblast | Sadašnje stanje | Posledica za prelazak |
|---|---|---|
| Zajednički šifarnik | OrganizationalUnit ima šifru, naziv i tekst centra; 339 zapisa | Sačuvati postojeće ID-eve i dodati vezu ka centralnom poslu |
| Finansije | FinanceJob ima 415 šifara; knjiženja čuvaju šifru i centar kao vrednosti | Povezati registar bez promene identiteta knjiženja i iznosa |
| Flota i putni nalozi | Veze ka zajedničkom šifarniku; gorivo i lizing imaju i tekstualne šifre | Zadržati istoriju dodela i brojeve dokumenata |
| Nabavka | Postoje veze sa poslovima i izvorni tekst centra; faktura može imati više poslova | Sačuvati višestruke veze i poreklo podatka |
| HR | Kadrovska OJ i zanimanje su odvojeni od poslova na radnim listama | Povezivati prema značenju, bez izjednačavanja svih polja job_code |
| Naplata | Spoljni sif_pos, uz lokalno određivanje dozvoljenog obuhvata | Prevoditi spoljne šifre preko potvrđene mape |
| Ugovori | Centar se u pregledu izvodi iz broja ugovora; zahtev ima tekst centra | Dodati eksplicitnu vezu bez prebrojavanja ugovora |
| Menice i Mobilni | Tekstualna polja centra i OJ | Dodati veze uz očuvanje originalnog unosa |

Svih 77 šifara koje postoje samo u finansijskom šifarniku su neaktivne. Jedna lokalna šifra, `960001`, nema par u proveravanom finansijskom šifarniku firme 1. Kod `110002` i `430001` lokalni centar postoji, a u trenutnom poslovnom izvoru i Finansijama je prazan. Postoje i završni razmaci u oznakama centara. Ove razlike treba rešavati kroz pregled usaglašenosti, bez tihog prepisivanja.

OrganizationalUnit se nalazi u core/models.py, ali ima Django app_label fleet. Fizičko premeštanje ili preimenovanje tog modela nije prvi korak. Njegove postojeće veze ostaju tokom prelaska. Naziv modela JobCode u Floti označava dodelu vozila, a ne sam centralni šifarnik poslova.

## 4 Stalni identitet i istorija promena

Svaki centar, podjedinica i krajnji posao dobija stalni interni ID. Dokumenti i nove veze koriste taj ID ili odgovarajuću verziju, dok je šifra promenljiv poslovni podatak.

| Događaj | Postupak | Šta ostaje sačuvano |
|---|---|---|
| Promena naziva | Nova verzija istog entiteta od datuma promene | Prethodni naziv i snimci dokumenata |
| Promena šifre istog posla | Isti ID, nova verzija i veza stare i nove spoljne šifre | Stara šifra, period važenja i kontinuitet posla |
| Prelazak u drugu jedinicu | Nova verzija pripadnosti; po potrebi nova puna šifra | Prethodna putanja i rezultati po tadašnjoj organizaciji |
| Promena aktivnosti ili profitnosti | Nova verzija oznaka | Status koji je važio u ranijem periodu |
| Podela ili spajanje poslova | Novi entiteti i eksplicitne veze sa prethodnicima | Originalni poslovi i pravila eventualnog poređenja |

Promena naziva i promena šifre nisu tehnički ista operacija. Trenutna sinhronizacija posao prepoznaje po šifri: novu šifru može dodati kao novi posao, a staru označiti neaktivnom ili ostaviti u lokalnom šifarniku. Da bi promena šifre ostala isti posao, potrebna je potvrđena veza staro → novo i datum primene. Sličan naziv nije dovoljan dokaz.

Ako se promeni segment centra ili drugog nivoa, mogu se promeniti pune šifre svih potomaka. Pre objave prikazujemo obuhvat, broj zahvaćenih poslova, moguće kolizije i posledice za spoljne izvore. Sve povezane verzije moraju početi istog dogovorenog datuma i objaviti se kao celina.

Objavljene verzije se ne prepisuju običnim uređivanjem. Koriste se intervali od uključivo do isključivo, bez preklapanja za isti entitet. Ispravka pogrešno evidentirane istorije je posebna, zabeležena operacija. Vreme kada smo uočili promenu u izvoru čuva se odvojeno od poslovnog datuma njenog važenja.

## 5 Snapshot na dokumentu

**Snapshot je koristan, ali sam nije dovoljan.** Čuva ono što je važilo na dokumentu, dok istorija registra omogućava da stara i nova šifra ostanu isti posao i da ih buduća sinhronizacija pravilno povezuje.

Na odgovarajućem dokumentu ili njegovoj stavci čuvamo: stalni ID posla, ID organizacione verzije, izvornu šifru, tadašnji naziv, putanju sva tri nivoa, oznake profitnosti i aktivnosti i datum po kojem je verzija određena. Ako jedan dokument ima više poslova, podatak se čuva na svakoj vezi ili stavci, ne samo u zaglavlju.

Primer promene naziva: dokument iz decembra zadržava tadašnji naziv, a dokument iz januara koristi novi. Oba dokumenta pripadaju istom internom poslu. Primer promene šifre: kada je potvrđeno da je to isti posao, stara i nova šifra vode na isti ID kroz različite verzije. Šifre `436111` i `43622` iz korisnikovog primera predstavljaju dva moguća krajnja posla; ne pretpostavljamo da su međusobno preimenovanje.

Za postojeće podatke bez istorije možemo sačuvati stanje na dan prelaska, uz oznaku da je to migracioni snimak. Ne predstavljamo ga kao dokaz organizacije koja je važila 2025. godine. Dokumente sa već sačuvanim istorijskim nazivima i pripadnostima koristimo kao dokaz gde je raspoloživ.

Organizacioni snapshot ne zamrzava pogrešan iznos dokumenta. Ako izvor ispravi knjiženje, postojeća finansijska sinhronizacija i dalje treba da preuzme ispravku. Promena organizacione veze ili istorijskog prikaza tada mora biti posebno evidentirana, umesto da se svaki snapshot osvežava iz trenutnog šifarnika pri svakom uvozu.

## 6 Predlog podataka centralnog registra

Predlaže se aplikacija organizacija sa sledećim logičkim celinama. Nazivi modela su radni i ne predstavljaju već izvršene migracije.

| Celina | Podaci i odgovornost |
|---|---|
| Organizacioni entitet | Stalni ID, firma, nivo 1/2/3; treći nivo je poslovni posao za povezivanje dokumenata |
| Verzija entiteta | Naziv, segment, puna šifra, nadređeni entitet, aktivnost, profitnost posla, važenje od/do |
| Veza sa spoljnim izvorom | Izvorni sistem, firma, vrsta šifarnika, izvorna šifra, važenje i ciljni interni entitet |
| Veza sa starim lokalnim modelom | Postojeći lokalni ID povezan sa centralnim entitetom; više starih šifara može voditi na isti posao |
| Evidencija promene | Autor ili uvoz, vreme, datum primene, razlog, prethodna i nova verzija, status nacrt/objavljeno |
| Promena sistematizacije | Skup povezanih izmena i datum primene; pregled uticaja i zajednička objava |

Validacija proverava dozvoljenog roditelja, pripadnost istoj firmi, tačno tri nivoa za nove poslove, jedinstvenost pune šifre, odsustvo ciklusa i preklapanja intervala. Čitači za istorijski datum koriste verzije svih nivoa koje su tada važile, a ne trenutno ime roditelja.

Za početak se ne dozvoljava dodela iste istorijske pune šifre drugom poslu. Ako izvor već ponovo koristi šifre, potreban je poseban postupak razrešenja uz firmu, vrstu izvora, period važenja i datum dokumenta. Nepouzdano razrešenje ostaje vidljivo kao problem.

Upravljanje bi imalo stablo tri nivoa, detalj sa istorijom, pregled aktivnih i neaktivnih šifara, nacrt buduće sistematizacije i spisak nepovezanih zapisa. Neaktivni poslovi se mogu sakriti u izboru za tekući unos, ali ostaju pretraživi u istoriji.

## 7 Izvori i buduća sinhronizacija

U prvoj fazi poslovni sistem ostaje merodavan za postojeće šifre, nazive i oznake P/N i D/N. Centralni registar vodi potvrđene veze tri nivoa, mapiranja i istoriju. Planirana nova sistematizacija može se pripremiti kao nacrt u Djangu, ali njena objava mora biti usklađena sa promenom u izvornom sistemu. Ovim planom se ne uvodi automatski upis u izvornu bazu.

Ne smeju postojati dva nezavisna mesta koja menjaju istu oznaku bez dogovorenog prioriteta. Ako Django kasnije postane mesto održavanja šifara, posebno se planiraju izlazna integracija, obrada grešaka i trenutak prestanka prepisivanja iz starog izvora.

Predloženi tok uvoza:

1. Preuzeti potpuni dogovoreni skup u privremeni uvozni skup, uključujući neaktivne poslove.
2. Ukloniti rubne razmake, sačuvati sirovu izvornu vrednost i proveriti ključeve i oznake.
3. Uporediti sa postojećim spoljnim mapama; nepoznate šifre i promene pripadnosti prikazati za proveru.
4. Za potvrđenu promenu kreirati novu verziju ili mapu; ponovljeni isti uvoz ne pravi duplikate.
5. Objaviti usaglašene promene atomski, uz zaključavanje i zapis u istoriji uvoza.
6. Osvežiti kompatibilne podatke koje stari moduli još čitaju, prema jednom utvrđenom redosledu pisanja.

Nedostupnost izvora, prazan rezultat ili nestanak iz prikaza samo aktivnih poslova ne znače automatsku deaktivaciju centralnog registra. Deaktivacija mora imati potvrđen status ili pravilo za potpuni izvorni skup. Nepoznat datum promene ostaje označen kao nepoznat; ne izjednačava se prećutno sa datumom sinhronizacije.

Finansijska sinhronizacija zadržava identitet knjiženja firma + godina + vrsta naloga + broj naloga + stavka. Šifra posla nije deo tog ključa, pa dodavanje centralne veze ne zahteva novo numerisanje knjiženja. Čuvaju se provere broja stavki, duguje/potražuje, transakcije i zaključavanje. Centralni uvoz ne pokreće obračunske poslovne procedure.

Dok moduli nisu prebačeni, postojeći uvozi nastavljaju da rade. Kasnije se za svako polje određuje jedan postupak koji ga upisuje; dva Celery zadatka ne smeju se takmičiti oko naziva, centra ili statusa. Neprepoznato mapiranje ne ruši objavu ispravnih izvornih finansijskih iznosa u prelaznoj fazi: veza ostaje prazna, beleži se upozorenje i predmet ne prolazi kao potpuno migriran.

## 8 Izveštaji i prava pristupa

Organizacioni prikaz po istorijskom datumu koristi tada važeću strukturu, gde je istorija potvrđena. Opcioni prikaz po novoj strukturi posebno se označava kao pregrupisavanje. Kod podele ili spajanja stari rezultat se ne umnožava i ne raspodeljuje bez dogovorenih pondera ili druge potvrđene poslovne osnove.

Prelazak ne menja postojeće filtere datuma: knjiženja koriste datum knjiženja, IF datum dokumenta, radne liste period obračuna, a dodele vozila svoje intervale. Za stanje Naplate koje nema istorijski presek ne prikazujemo prividno istorijsko stanje duga samo zato što registar ima istoriju.

Prava se centralizuju odvojeno od izveštajnog grupisanja. Dozvola može obuhvatiti centar, drugi nivo ili pojedinačni posao. Dozvola nadređenog može uključivati njegove potomke prema izričito definisanom pravilu. Članstvo korisnika, prava po modulu i pristup istoriji moraju ostati proverljivi.

Trenutni moduli različito tumače prazan obuhvat i dozvolu na pojedinačnu šifru. Pre zamene pravila napraviti poređenje efektivnog pristupa po korisniku. Promena organizacije ili izbor istorijskog pogleda ne smeju nenamerno proširiti pristup. Razlike se potvrđuju kao zasebna promena prava, a ne kao usputna posledica migracije.

## 9 Faze prelaska i uslovi završetka

### Faza 0 Priprema i početni snimak

Sačuvati proverljivu rezervnu kopiju pre migracija i izvoz postojećih šifarnika, veza i prava. Pripremiti mapu tri nivoa sa izuzecima i utvrditi datum nove sistematizacije. Rezultat je potvrđen spisak mapiranja, početni kontrolni izveštaj i evidentirana ograničenja istorije.

### Faza 1 Centralni registar bez promene postojećih modula

Dodati modele, verzije, uvozni pregled i stablo. Uvesti kompletan šifarnik i oznake. Postojeći ekrani i zadaci ostaju na dosadašnjem načinu rada. Registar prvo radi paralelno, sa poređenjem podataka. To je preporučena prva samostalna isporuka.

### Faza 2 Veze i kontrolisana sinhronizacija

Dodati opcione centralne veze u postojeće modele, bez brisanja starih polja. Povezivanje postojećih redova izvršavati u manjim ponovljivim paketima. Omogućiti verzionisanje i mapu preimenovanja. Nepovezani i dvosmisleni zapisi moraju biti navedeni u izveštaju; nisu automatski nule ili novi poslovi.

### Faza 3 Pilot u Finansijama

Prebaciti čitanje šifarnika, filtera i organizacionih oznaka uz mogućnost uključivanja po modulu. Uporediti isti period i isti korisnički obuhvat sa starim prikazom. Prihodi, rashodi, ZT i tokovi moraju ostati isti za isti poslovni skup; odobrena promena grupisanja prikazuje se odvojeno. Posebno proveriti grupisanje stare i nove šifre istog posla bez dupliranja i uz očuvanje sirovih oznaka na knjiženjima.

### Faza 4 Ostali moduli

Redosled je Flota i putni nalozi, Nabavka, HR, Naplata, zatim Ugovori, Menice i Mobilni. Svaki modul dobija sopstveno povezivanje, proveru istorije i pristupa i mogućnost zasebnog puštanja. Brojevi naloga, ugovora i zahteva ostaju nepromenjeni čak i kada u sebi sadrže staru šifru centra.

### Faza 5 Jedinstveno održavanje

Pošto svi čitači i upisi koriste centralni registar, isključiti duple editore i redundantne zadatke. Stare kolone se ne brišu u istom koraku; zadržavaju se tokom dogovorenog perioda stabilizacije i kao izvorni podaci gde su potrebne. Tek potom razmatrati pojednostavljenje modela i naziva.

## 10 Provere i povratak na prethodni rad

Pre puštanja svake faze proveriti sledeće slučajeve:

- Oba korisnikova primera, različite dužine završnog segmenta, vodeće nule i kolizije pune šifre.
- Isti posao sa novom šifrom; promena samo naziva; prelazak centra i promena segmenta roditelja.
- Dokument dan pre promene i na dan promene, buduća verzija i naknadni unos za stari period.
- Aktivnost i profitnost pre i posle promene, uz nepromenjene mesečne obračunske koeficijente.
- Neaktivna šifra u istorijskom izveštaju; nedostajuća istorija označena bez lažne preciznosti.
- Ponovljen, prekinut i paralelan uvoz; prazan izvor; nepoznata šifra; potvrđena promena šifre bez dupliranja.
- Isti finansijski zbirovi za isti obuhvat, iste dodele vozila i višestruke veze faktura.
- Pristup bez obuhvata, pojedinačnom poslu, celom centru i istoriji nakon premeštanja.

Pri neuspehu se može isključiti centralno čitanje za pogođeni modul, ali to je pouzdano samo dok se stari podaci kompatibilno održavaju i za nove unose. Zato se ta kompatibilnost proverava pre svakog prelaska. Nove verzije i dokumenti se pri povratku ne brišu.

Rezervna kopija služi za oporavak; vraćanje cele baze nakon nastanka novih dokumenata nije rutinski povratak jer bi izgubilo nov rad. Planirati zaseban povratak verzije aplikacije, očuvanje novonastalih podataka i razrešenje uvoza. Potpunu promenu spoljnog sistema ne možemo poništiti samo isključivanjem lokalnog prikaza.

## 11 Složenost i uticaj na rad

| Deo posla | Procena složenosti | Glavni rizik |
|---|---|---|
| Registar tri nivoa i dve oznake | Umerena | Nepotpuna mapa postojećih šifara |
| Verzije i snapshot novih dokumenata | Umerena | Pogrešan datum važenja ili neprimereno prepisivanje |
| Promene šifara i izvori | Viša | Izvor nema stalni ID posla ni pouzdan datum promene |
| Povezivanje svih modula | Viša | Različito značenje OJ, tekstualne veze i prava pristupa |
| Istorijsko pregrupisavanje | Viša | Nedostajući podaci i podele/spajanja bez pravila |

Ukupno je ovo **umereno do visoko složena migracija**, ali ne zahteva prepisivanje cele aplikacije. Samo dodavanje hijerarhije je manji deo posla; najviše pažnje traže istorija, sinhronizacija i pristup podacima.

U prvoj fazi uticaj na postojeće funkcije je mali jer se dodaje paralelan registar. Kasnije se promene ograničavaju na jedan modul i jedan način čitanja odjednom. Migracije, indekse i grupno povezivanje treba probati na kopiji baze i izvoditi van vršnog opterećenja; ne može se unapred garantovati potpuno odsustvo zaključavanja ili prekida.

Sinhronizacija knjiženja može da zadrži svoj osnovni tok. Potrebno je dopuniti razrešenje organizacije i preimenovanja, a zatim objediniti održavanje šifarnika. Najrizičniji pristup bio bi trenutno preimenovanje postojećih modela i šifara uz masovno prepisivanje starih dokumenata; ovaj plan ga izbegava kroz dodatne veze i faze.

Rok treba proceniti nakon odobrene mape tri nivoa i pregleda izuzetaka. Prva isporuka može se jasno odvojiti od celokupne migracije: centralni registar, istorija, pregled uvoza i kontrolni izveštaj, bez promene obračuna u modulima.

## 12 Podaci potrebni za realizaciju

Pre implementacije potvrditi naziv drugog nivoa i mapu segmenta za svaki postojeći posao, dozvoljene dužine i vodeće nule, datum primene nove sistematizacije, spisak promena staro → novo i odgovorno lice za razrešavanje izuzetaka. Za svaku promenu označiti da li je preimenovanje, promena šifre istog posla, premeštanje ili nastanak novog posla.

Potvrditi i mesto održavanja podataka tokom prelaska, način korišćenja starih šifara u spoljnim sistemima i željeni obuhvat pristupa istoriji. Ovo su odluke potrebne za implementaciju; ne sprečavaju da se plan i početni pregled pripreme sada.

Relevantna mesta za budući rad u projektu:

- [Zajednički šifarnik i korisnički obuhvat](../core/models.py)
- [Postojeći uvoz šifara i dodela vozila](../fleet/sync/external.py)
- [Finansijski modeli](../finansije/models.py), [izvor](../finansije/services/source.py) i [sinhronizacija](../finansije/services/sync.py)
- [Mesečna raspodela zajedničkih troškova](../finansije/services/shared_costs.py)
- [Prava Finansija](../finansije/access.py) i [zajedničko filtriranje Flote](../fleet/mixins.py)
- [HR modeli](../hr/models.py) i [modeli Nabavke](../nabavka/models.py)

Odobravanje ovog plana predstavlja osnov za zaseban zadatak implementacije. Dokumentovanje nije pokrenulo migracije, uvoz poslovnih podataka niti promenu sistematizacije.
