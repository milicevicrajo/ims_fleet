# IMS FLOTA
## Analiza aplikacije, procedure rada i plan razvoja

**Presek:** 10.09.2026.  
**Verzija:** 1.0 — dokument za razmatranje uprave, garaže, Nabavke i finansija.  
**Obuhvat:** vozila, raspored, zaduženja, putovanja, intervencije, nabavka, kilometraža, troškovi i izveštavanje.

Dokument razlikuje tri nivoa: **POSTOJI** — provereno u kodu ili bazi; **DOGOVORENO** — potvrđeno u razgovoru; **PREDLOG** — postupak ili razvoj koji tek treba usvojiti i sprovesti. Predložene procedure ne znače da aplikacija već tehnički sprovodi sva navedena pravila.

# 1. Glavna ocena i šta prvo uraditi

Aplikacija ima dobru osnovu za upravljanje flotom: stabilan identitet vozila, povezane dokumente i ugovore, istoriju organizacionog rasporeda, zaduženja, putne naloge, podatke o gorivu i integraciju sa Nabavkom. Nije potrebno ponovo praviti ove evidencije. Najveći nedostatak je što **povezan dokument još nije potvrđena intervencija**, a mogućnost promene statusa još nije poslovno odobrenje uprave.

Prioritet je da se svaki novi posao može pratiti kroz sled: **prijavljeno → pripremljen nalog → odobrila uprava → izvršeno → potvrdila garaža → povezana dokumentacija i troškovi**. Tek tada planiranje servisa i kontrola ponavljanja imaju pouzdanu osnovu.

| Prioritet | Šta treba dobiti | Zašto je važno |
| --- | --- | --- |
| 1 | Odobravanje intervencije i potvrda izvršenja | Zna se ko je tražio, ko odobrio i šta je stvarno urađeno. |
| 2 | Plan malog i velikog servisa po vozilu | Sledeći servis zavisi od potvrđenog prethodnog rada i važećeg intervala. |
| 3 | Povezivanje dokumentacije i sređivanje kategorija troška | Faktura, trebovanje i knjiženje ne smeju predstavljati tri troška istog događaja. |
| 4 | Usklađivanje uloga i pristupa između modula | Garaža može da formira zahtev, a Nabavka da vidi povezano vozilo, bez nepotrebnih prava izmene. |
| 5 | Trošak interne garaže i uporedivi pokazatelji | Materijal, rad i zajednički troškovi imaju odvojene izvore i pravila raspodele. |

## 1.1. Šta je korisnik potvrdio

- Sekretarice vode putne naloge. Zaduženje vozila traje određeni period, a za svako putovanje postoji nalog. Vozač na pojedinom putovanju može biti druga osoba od periodično zaduženog zaposlenog.
- Garaža, odnosno Veljović, prima prijave kvarova, priprema naloge i vodi servisne intervencije. Uprava odobrava radove. Garaža treba da potvrdi izvršenje.
- Dokumentacija se za sada može povezivati i naknadno, bez prethodnog zahteva. Takav zapis ne treba automatski proglasiti odobrenim ili izvršenim.
- Prioriteti su kontrola troškova, izbegavanje nepotrebnog ponavljanja servisa i planiranje održavanja.
- Za moguće nepotrebno ponavljanje traži se **upozorenje**. To nije automatska zabrana servisa; odobrenje uprave ostaje zasebna obaveza.
- Postoji unos servisnog intervala; želi se i interval velikog servisa i odgovarajući obračun.
- Aplikacija je namenjena radu na računarima. Mobilni interfejs nije prioritet ovog plana.

## 1.2. Dobra praksa na koju se predlog oslanja

Upravljanje sredstvom treba povezati sa njegovom poslovnom svrhom, troškom, pouzdanošću i rizikom, a ne samo sa spiskom dokumenata. To je okvir javnog pregleda standarda [ISO 55001:2024](https://www.iso.org/standard/83054.html); ovaj dokument nije ocena sertifikacione usaglašenosti IMS-a.

Razdvajanje odobrenja rada, rada u toku, fizičkog završetka i konačnog zatvaranja dokumentacije postoji i u [IBM opisu statusa radnih naloga](https://www.ibm.com/docs/en/control-desk/7.6.1?topic=orders-work-order-statuses). Konkretan postupak u nastavku prilagođen je potvrđenim odgovornostima u IMS-u.

Namena vozila, upotreba, kilometraža, zastoji i istorija održavanja korisni su zajedno pri oceni flote. [FEMP smernice](https://www.energy.gov/cmei/femp/femp-best-practices-sustainable-fleet-core-principles) daju takav okvir. Američki propisi navedeni u izvoru nisu predstavljeni kao obaveze IMS-a.

# 2. Provereno stanje aplikacije i baze

Brojevi su zatečeni tokom čitanja baze 10.09.2026. Obuhvataju postojeću istoriju, osim gde piše „aktivna vozila“. Broj stavki, dokumenata i intervencija nije ista mera. Nijedan zapis nije menjan radi ove analize.

| Nalaz u bazi | Poslovno značenje |
| --- | --- |
| 172 vozila, od toga 164 aktivna | Postoji razvijena matična evidencija; aktivno u evidenciji ne znači automatski tehnički raspoloživo. |
| 204 zapisa rasporeda na OJ/šifre posla | Raspored ima istoriju. Sva aktivna vozila imaju bar jedan zapis rasporeda. |
| 164 aktivna vozila bez roka registracije na aktuelnoj saobraćajnoj | Nedostaje taj konkretan podatak. To ne dokazuje da su vozila neregistrovana; polise su zasebna evidencija. |
| 162 aktivna vozila imaju interval 15.000 km; 2 imaju 0 | Ista podrazumevana vrednost nije dokaz da je interval proveren za svaki automobil. Nulu treba tretirati kao neodređen/nepotvrđen plan. |
| 217 zaduženja; 98 bez datuma zatvaranja | Periodična zaduženja se koriste. U ovom preseku nema više otvorenih zapisa za isto vozilo. |
| 5 zatvorenih zaduženja bez završne kilometraže; 3 sa završnom manjom od početne | Potrebna je provera konkretnih zapisa; istoriju ne popravljati proizvoljnim vrednostima. |
| 3.522 putna naloga, od toga 3.461 sa vezom ka IMS vozilu | Postoji značajna evidencija putovanja. Ostali mogu imati drugo prevozno sredstvo i nisu automatski greške. |
| 1 nalog garaže; 2.980 stavki trebovanja, bez veze sa nalogom garaže | Postoje podaci o materijalu, ali oni nisu istorija 2.980 potvrđenih servisa. Veza materijala i intervencije tek treba da zaživi. |
| 1.342 knjižene stavke u ServiceTransaction | Evidencija sadrži i registraciju, gume, putarinu, lizing i gorivo; nije homogena evidencija popravki. |
| 224 zahteva u Nabavci; 222 označena kao garažna; 173 sa vozilom | Postoje zahtevi bez konkretnog vozila, uključujući potrebe magacina. To samo po sebi nije greška. |
| 223 zahteva u nacrtu; 1 sa statusom povezana faktura | Statusi se ne mogu koristiti kao dokaz koliko je radova stvarno završeno. |
| 0 zahteva povezanih sa nalogom garaže; 0 popunjenih novih tipova intervencije na zahtevima/fakturama | Nedavno dodata polja postoje, ali evidencija još nije dopunjena. |
| 3.061 faktura Nabavke; 242 povezane sa vozilom | Ukupan broj uključuje i druge nabavke IMS-a. Ne treba svih preostalih 2.819 smatrati nepovezanim automobilskim fakturama. |
| 9.092 NIS i 7.058 OMV transakcija; bez nepovezanih vozila u ovim tabelama | Veza goriva sa vozilom postoji. Tačnost kilometraže i tumačenje proizvoda zahtevaju zasebnu kontrolu. |

## 2.1. Tehnički i logički nalazi koji menjaju prioritete

**Odobrenje nije implementirano kao poseban događaj.** Kvar nema status odobrenja, odobravaoca ni potvrdu završetka. Nabavka ima statuse i istoriju njihovih promena, ali nema poseban status odobreno sa kontrolisanim pravom uprave. Postojeći endpoint promene statusa prihvata izabrani status bez matrice dozvoljenih prelaza.

**Pregled može da napravi predložene delove.** Funkcija ensure_auto_parts upisuje generičke KvarPart stavke za mali/veliki servis prilikom otvaranja nekih prikaza naloga. Spiskovi sadrže unapred zadate količine ulja, svećice i druge delove nezavisno od konkretnog vozila. Ideja šablona je korisna, ali upis mora postati svesna radnja „Dodaj predlog“, a specifikacija se proverava za automobil. Predlog nije dokaz izdavanja ili ugradnje.

**Zaduženje nije pojedinačno putovanje.** Novi zapis zaduženja automatski zatvara prethodni zapis za isto vozilo datumom novog preuzimanja i može preneti početnu kilometražu kao završnu prethodnog. To održava sled zaduženja, ali ne potvrđuje fizičku primopredaju. Forma ne dozvoljava dva početka za isto vozilo istog datuma, pa ne podržava precizno više primopredaja u jednom danu.

**Putni nalog nije evidencija brojila.** PutniNalog sadrži putnika/zaposlenog, destinaciju, zadatak, vozilo, datum, trajanje i finansijske podatke, ali nema posebnog stvarnog vozača, vezu sa periodičnim zaduženjem ni početnu/završnu kilometražu. Oznaka „opravdan“ odnosi se na pravdanje naloga, ne na potvrdu servisa ili stanja auta.

**Servisi i troškovi su trenutno dva različita pogleda.** Tab Servisi prikazuje dokumente i datume; Troškovi sabira druge izvore. Nova faktura vezana za auto može biti vidljiva u Servisima, a njen iznos još ne mora biti uključen u obračun Troškova. Obrnuto, stara knjižena popravka može ući u trošak bez datuma potvrđenog rada.

**Stara Analitika nije usaglašena sa novim detaljem.** Koristi stariju evidenciju FuelConsumption, neke zbirne vrednosti iz cele istorije, procenu kilometraže i fiksne granice RSD/km po masi vozila. I dalje postoji ocena „Neisplativo“ i logika crvene zone. Vraćanje linka u meni nije potvrda ispravnosti tih poslovnih zaključaka.

**Pristup se ne proverava jednako svuda.** Postoje uloge i dozvole po akcijama, ali deo starih pregleda proverava samo prijavu, dok neke stare funkcije izveštaja nemaju lokalnu proveru prijave/uloge. Ograničenja centara nisu centralizovana. To treba urediti kao deo procedure pristupa; analiza ne tvrdi da je proverena celokupna produkciona infrastruktura.

# 3. Šta pratimo kod svakog automobila

Vozilo je centralni predmet evidencije. Stabilna veza je njegov interni ID, uz VIN i inventarski broj. Tablice služe za prepoznavanje i povezivanje sa izvorima; istorija saobraćajnih dozvola ostaje odvojena od identiteta automobila.

| Oblast | Podaci i događaji koje pratimo | Stanje i odgovornost |
| --- | --- | --- |
| Identitet i tehnika | VIN, inventar, marka/model, godište, boja, gorivo, motor, snaga, mase, sedišta, slika | POSTOJI. Predlog: imenovani referent za matične podatke, uz potvrdu uprave za pripadnost. |
| Namena | Prevoz ljudi/robe, terenska podrška, radna jedinica; oprema koja menja način korišćenja | PREDLOG. Tehnička kategorija nije dovoljna da objasni kamion sa garniturom ili kombi sa alatom. |
| Dokumenti | Aktuelna i prethodne saobraćajne, rok registracije, nalepnica i drugi prilozi | POSTOJI. Nedostaju konkretni rokovi; odgovorno lice za dopunu treba imenovati. |
| Raspolaganje | Vlasništvo, korišćenje po ugovoru, finansiranje, početak/kraj, dokaz | POSTOJI. Podrazumevani prikaz vlasništva IMS ostaje označen kao zaključak po dogovorenom pravilu kada nema tekućeg ugovora. |
| Organizacija | Centar, OJ/šifra posla i datum svake promene | POSTOJI. Uprava potvrđuje pripadnost; promena se dodaje istorijski, ne prepisuje ceo raniji period. |
| Zaduženje | Odgovorni zaposleni, period, preuzimanje i vraćanje, početno/završno stanje | DELIMIČNO. Zapis postoji; predlog dopune primopredaje i jasnog nosioca unosa. |
| Putovanja | Stvarni vozač, putnici, ruta, svrha, polazak/povratak, kilometraža, nalog | DELIMIČNO. Sekretarice vode naloge; zasebnu vezu vozača i stvarne vožnje treba dopuniti. |
| Kilometraža | Vrednost, datum/vreme, izvor, korekcija i razlog korekcije | DELIMIČNO. Novi tab čita gorivo i zaduženja; nema punog postupka potvrđivanja korekcija. |
| Održavanje | Prijava, dijagnoza, odobrenje, plan rada, izvršenje, delovi, datum/km završetka | DELIMIČNO. Nalog i dokumenti postoje; odobrenje i potvrđena realizacija su prioritet razvoja. |
| Plan servisa | Mali/veliki servis, primenljivost, interval km/vreme, poslednja potvrđena realizacija | DELIMIČNO. Jedno polje intervala postoji; odvojeni planovi i pouzdan obračun tek slede. |
| Nabavka | Zahtevi, dobavljači, stavke, narudžbenice, fakture/UF, trebovanja, povrati | POSTOJI više vrsta veza. Nabavka uređuje dokumente; garaža potvrđuje njihovu vezu sa radom. |
| Troškovi | Gorivo, održavanje, gume, registracija/polise, ugovori, druge usluge, interni rad | DELIMIČNO. Postoje brojni izvori, ali nema jedinstvenog potvrđenog ukupnog troška po autu. |
| Raspoloživost | U upotrebi, čeka deo, u garaži/spoljnom servisu, vraćeno u rad; trajanje zastoja | PREDLOG. Ne izjednačavati „aktivan u evidenciji“ i „raspoloživ za put“. |
| Trag odgovornosti | Ko je uneo, odobrio, izvršio, povezao, ispravio i kada | DELIMIČNO. Opšti dnevnik aktivnosti i istorija Nabavke postoje; poslovne potvrde treba dodatno evidentirati. |

## 3.1. Veze koje treba sačuvati

Jedno vozilo ima više dokumenata, promena OJ, zaduženja, putovanja, polisa, intervencija i troškovnih događaja. Jedna intervencija može imati više zahteva, faktura i trebovanja. Jedna faktura može obuhvatiti više intervencija ili vozila — tada je potrebna raspodela stavki/iznosa, a ne kopiranje punog iznosa na svaki automobil.

**Primer:** vozilo je u centru A, zaduženo kod zaposlenog X, a na službeni put ga vozi Y. Putovanje ne menja automatski ni centar ni periodično zaduženje. Trošak puta može teretiti određenu šifru posla različitu od matične pripadnosti auta. Sve tri informacije treba sačuvati, sa jasnim nazivima.

## 3.2. Predlog pregleda detalja vozila

Zadržati sedam tabova: Podaci, Raspolaganje i polise, Troškovi, Korišćenje, Kilometraža, Servisi i Dokumenti. U zaglavlju prikazati identitet, tekući raspored i poslednje evidentirano stanje brojila sa datumom. U Servisima odvojiti potvrđene radove od pratećih naloga i dokumenata. U Troškovima obavezno navesti period, valutu, osnovicu i obuhvat izvora.

Najkorisnije buduće kartice su: sledeći mali servis, sledeći veliki servis ili neprimenljivo, otvorene intervencije koje čekaju odobrenje, potvrđeni radovi bez kompletne dokumentacije i trošak u izabranom periodu. Nepoznat podatak prikazivati kao nepoznat, bez izmišljene nule ili datuma.

# 4. Uloge, dozvole i odgovornosti

U bazi postoje prilagođene uloge i dozvole. Brojevi ispod znače aktivne naloge povezane sa ulogom, ne broj ljudi koji aplikaciju svakodnevno koriste. Jedan nalog može imati više uloga; prava se sabiraju. Posebna superuser prava nadjačavaju uloge.

| Uloga iz baze | Aktivni nalozi / dozvole | Šta je bitno za ovu proceduru |
| --- | --- | --- |
| Garaza | 1 / 84 | Ima kreiranje i izmenu kvarova, kao i brisanje. Sama uloga nema kreiranje zahteva Nabavke; novi tok traži dopunu pristupa. |
| Uprava | 3 / 390 | Ima široka prava, uključujući status Nabavke. Potrebno je posebno pravo odobravanja intervencije, umesto izjednačavanja svake izmene sa odobrenjem. |
| Nabavka | 2 / 45 | Ima zahteve, povezivanje faktura i promenu statusa. Sama uloga nema vehicle_detail; direktni link ka autu zahteva odgovarajuće pravo pregleda. |
| Sekretarijat | 10 / 58 | Ima kreiranje/izmenu putnih naloga i zaduženja. Sama uloga nema vehicle_travel_order_close; treba uskladiti zatvaranje sa dogovorenim poslom sekretarica. |
| Zatvaranje putnih naloga | 2 / 2 | Ima pregled i pravdanje putnih naloga. To je finansijsko/administrativno pravdanje, različito od vraćanja vozila. |
| Blagajna | 2 / 2 | Postoji ograničena uloga za blagajnički posao. Ne treba je automatski izjednačiti sa kompletnom finansijskom kontrolom flote. |
| Pregled | 3 / 85 | Postoji osnova za pravo pregleda. Proveriti obuhvat centara i dokumentacije po funkciji. |
| Zaposleni | 300 / 7 | Postoje prava vezana za zaduženja. Dogovor da sekretarice vode evidenciju treba usaglasiti sa već postojećim mogućnostima zaposlenih. |
| Zahtev | 0 / 9 | Uloga za podnosioca zahteva postoji. Može pomoći raspodeli prava, ali nije dokaz da je garaža već ima. |

Postoje i druge uloge za pravnu službu, menice, mobilnu telefoniju i naplatu, kao i dve pomoćne „Render check“ uloge. Ukupno je 323 aktivna naloga, od toga 2 superuser naloga; 1 aktivan nesuperuser nema ulogu. U dostupnom katalogu nema posebne uloge pod nazivom Finansije. Ovo su nalazi za sređivanje pristupa, bez promene naloga u ovoj analizi.

## 4.1. Predlog matrice odgovornosti

| Aktivnost | Ko operativno radi | Ko potvrđuje / odlučuje |
| --- | --- | --- |
| Matični podaci i dokumenti vozila | Imenovani referent / sekretarijat — potvrditi osobu | Uprava potvrđuje pripadnost; finansije osnov raspolaganja i finansiranje. |
| Zaduženje, promena zaduženog i povrat | Sekretarijat, uz podatke učesnika primopredaje | Predaja/preuzimanje moraju imati evidentiranu potvrdu; odgovorno lice imenovati. |
| Putni nalog i podaci posle puta | Sekretarijat | Vozač dostavlja stvarne podatke; pravdanje obavlja ovlašćena finansijska funkcija. |
| Prijava i dijagnoza kvara | Garaža / Veljović | Garaža potvrđuje nalaz i predlog rada. |
| Odobrenje intervencije | Uprava | Ovlašćeni član uprave; sačuvati identitet, vreme i odobreni obuhvat. |
| Zahtev za delove/uslugu | Garaža, iz naloga | Nabavka proverava dobavljača i dokumentaciju; odobrenje rada ostaje na nalogu. |
| Izvršeni radovi i stanje pri završetku | Garaža / Veljović | Potvrđuje šta je stvarno urađeno, datum i kilometražu. |
| Izdavanje/povrat delova | Magacinska funkcija | Potvrđuje količinu i dokument; garaža potvrđuje utrošak na intervenciji. |
| Faktura i raspodela na vozila | Nabavka | Finansije potvrđuju iznos, period, osnovicu i usaglašavanje sa knjiženjima. |
| Intervali i servisni planovi | Garaža na osnovu dokumentacije vozila | Imenovano odgovorno lice potvrđuje plan i njegove izmene. |
| Mesečni pregled i odluke | Finansije pripremaju potvrđene podatke; uprava pregleda | Uprava odlučuje o trošku, planu, opravdanosti ponavljanja i prioritetima. |

Upravi treba ekran za odobravanje, a garaži ekran za izvršenje. Naknadno povezivanje fakture ostaje dozvoljeno, ali ne sme samo po sebi da popuni polje „odobrio“ ili „izvršeno“. Promena opisa ili procene ne sme izbrisati prethodno odobrenu verziju naloga.

# 5. Procedure: formiranje, raspored, zaduženja i putovanja

## P-01. Uvođenje vozila i održavanje matične evidencije

1. Referent proverava VIN i inventarski broj i otvara postojeće vozilo ako već postoji. Ne kreira duplikat zbog novih tablica ili nove saobraćajne.
2. Unosi/proverava tehničke podatke, fotografiju i dokumente kroz postojeći čarobnjak. Poreklo spornih podataka ostavlja vidljivim.
3. Uprava potvrđuje centar/OJ i datum početka rasporeda. Za kasniju promenu dodaje se novi istorijski zapis.
4. Finansije potvrđuju osnov vlasništva/korišćenja i povezani ugovor. Podrazumevani prikaz vlasništva nije zamena za dokaz u zvaničnoj dokumentaciji.
5. Garaža potvrđuje početno stanje kilometraže i početnu servisnu istoriju. Ako poslednji servis nije poznat, plan dobija oznaku „nedostaje početna osnova“.
6. Odgovorno lice dopunjava rok registracije i polise. Datum dokumenta, registracije i pokrića osiguranja ostaju odvojeni.

**Rezultat:** jedinstven dosije automobila, poznata pripadnost i lista podataka koji čekaju dopunu. Procedura koristi postojeće funkcionalnosti, uz predloženu kontrolu potpunosti.

## P-02. Periodično zaduženje i primopredaja

1. Sekretarica bira automobil i zaposlenog na čije ime ide periodično zaduženje. Proverava postojeće otvoreno zaduženje i trenutnu raspoloživost.
2. Evidentira početak, stvarnu kilometražu pri preuzimanju i osnov zaduženja. Predlog dopune: stanje goriva, oštećenja, predata dokumenta/ključevi i potvrda učesnika.
3. Kod promene korisnika, prethodna primopredaja se zatvara, a nova otvara kao povezan događaj. Automatsko zatvaranje postojećeg softvera treba prikazati korisniku kao deo ove radnje i potvrditi podatke.
4. Pri vraćanju se unose stvarni datum/vreme, završna kilometraža i primećene promene stanja. Novi kvar se povezuje sa prijavom garaži.
5. Zatvoren zapis se ispravlja kroz ovlašćenu korekciju sa razlogom. Pravo ispravke i istorija zamene podataka moraju biti vidljivi.

**Važno:** trenutno polja rade na nivou datuma. Za više primopredaja istog dana treba dopuniti vreme i pravilo granice perioda. Predlog je interval od uključivog početka do isključivog kraja, da se trenutak prenosa ne broji dvaput. Potrebne su provere preklapanja i atomsko čuvanje prenosa.

## P-03. Nalog za pojedinačno putovanje

1. Pre puta sekretarica evidentira zaposlenog/putnike, stvarnog vozača, automobil, svrhu, odredište, planirane datume i šifru posla koja snosi trošak.
2. Sistem prikazuje periodično zaduženog zaposlenog, ali ne zahteva da bude isti kao vozač. Tuđi vozač ne prepisuje zaduženje automatski.
3. Proverava se da li je automobil već na drugoj vožnji ili označen kao neraspoloživ zbog intervencije. Nedovoljno podataka prikazuje se kao upozorenje za proveru.
4. Po povratku vozač dostavlja stvarni polazak/povratak, kilometražu i napomene, a sekretarica evidentira podatke. Očitavanje postaje izvor za kilometražu tek sa stvarnim datumom.
5. Dokumentacija putovanja ide na zasebno pravdanje. Trošak dnevnica i akontacija vodi se uz putovanje/zaposlenog; ne ulazi automatski u trošak održavanja automobila.

**Potreban razvoj:** jedna stvarna vožnja treba da postoji samo jednom, čak i ako više zaposlenih ima svoje putne naloge. Predlog je zapis VehicleTrip sa stvarnim vozačem, vremenom i brojilom, na koji se povezuju postojeći PutniNalog zapisi. Time se čuva postojeća administracija dnevnica, a kilometraža se ne množi brojem putnika.

# 6. Procedure: garaža, odobrenje i izvršenje

## P-04. Prijava i priprema intervencije

1. Vozač ili korisnik prijavljuje problem Veljoviću. Garaža otvara prijavu/nalog za konkretan automobil.
2. Beleži simptom, datum prijave, trenutno očitavanje, podnosioca, da li vozilo može u upotrebu i eventualne priloge. Razlikuje prijavljeni simptom od utvrđene dijagnoze.
3. Bira glavni tip: mali servis, veliki servis ili popravka. Tip ne predstavlja potvrdu izvršenja.
4. Pregleda poslednje potvrđene radove, otvorene naloge i plan servisa. Upozorenje za ponavljanje pokazuje prethodni nalog, datum, kilometražu i tadašnji obuhvat.
5. Priprema predlog rada, lokaciju izvršenja, delove/usluge i procenu. Predloženi delovi se proveravaju za automobil; nisu automatski „ugrađeni“.
6. Podnosi nalog upravi. Nacrt je moguće korigovati; podnetu verziju treba sačuvati za poređenje sa odobrenjem.

## P-05. Odobrenje uprave

Uprava vidi vozilo, razlog rada, prethodne slične intervencije, upozorenja, predlog specifikacije, interni/spoljni način rada i procenu. Odluka je odobri, vrati na dopunu ili odbij. Evidentiraju se osoba, vreme, komentar, odobreni obuhvat i iznos/valuta ako postoji procena.

Promena koja proširuje odobreni obuhvat ili prelazi odobreni iznos treba da traži novu odluku. To je predlog kontrole koji se primenjuje na verziju naloga, a ne samo na njegov trenutni tekst. Upozorenje za ponovljen servis ne sprečava upravu da odobri opravdan rad, reklamaciju ili otklanjanje novog kvara.

Hitne intervencije na terenu treba obraditi kroz unapred dogovoreno ovlašćenje i naknadno dokumentovanje; konkretna pravila i ovlašćeni zamenski odobravalac ostaju za odluku uprave. Ne predlaže se skriveno zaobilaženje odobrenja.

## P-06. Rad unutar IMS-a

1. Odobreni nalog postaje osnova rada garaže. Ako delovi postoje, koristi se magacinsko trebovanje povezano sa tim nalogom i vozilom.
2. Ako delova nema, garaža otvara zahtev za nabavku iz naloga. Veza sa vozilom i intervencijom prenosi se automatski; Nabavka obrađuje dobavljača i nabavku.
3. Prijem robe u magacin ne označava servis kao izvršen. Izdavanje i eventualni povrat delova ostaju zasebni dokumenti.
4. Garaža evidentira stvarno urađene operacije i stvarno utrošene delove. Razlika u odnosu na plan ostaje vidljiva.
5. Ako se uvede evidencija rada, unose se izvršilac i utrošeni sati. Nema sati ili cene rada znači „trošak rada nije obračunat“, a ne nula.
6. Veljović potvrđuje završetak: datum, kilometražu, urađeno, eventualni preostali problem i vraćanje u upotrebu. Potvrđuje se koje servisne obaveze su zaista izvršene.
7. Dokumenti koji stignu kasnije dopunjuju trošak istog naloga. Ne otvara se novi „servis“ samo zato što je stigla dodatna faktura.

## P-07. Popravka ili servis van IMS-a

1. Garaža priprema nalog i predlog spoljne usluge. Uprava odobrava rad.
2. Iz naloga se otvara zahtev za uslugu. Nabavka povezuje dobavljača, ponudu/ugovor ili narudžbenicu kada postoje.
3. Evidentiraju se predaja vozila, očekivani radovi i zastoj. Dopunski rad koji proširuje odobrenje vraća se na odluku uprave.
4. Po preuzimanju vozila garaža proverava specifikaciju izvedenih radova i potvrđuje stvarno stanje. Datum izvršenja može biti raniji od datuma fakture.
5. Nabavka povezuje fakturu sa zahtevom i nalogom; finansije proveravaju iznos i način knjiženja. Avansna i konačna dokumentacija ne sabiraju se kao dva puna troška iste usluge.
6. Reklamacija ili ponovljeni problem vezuju se za prethodnu intervenciju. Trošak reklamacije može biti nula, ali rad i zastoj i dalje postoje kao događaji.

## 6.1. Predlog stanja naloga

| Stanje | Ko sprovodi promenu | Uslov / rezultat |
| --- | --- | --- |
| Nacrt | Garaža | Prijava i predlog se pripremaju. |
| Čeka odobrenje | Garaža podnosi | Sačuvana verzija predloga i upozorenja. |
| Vraćeno na dopunu / odbijeno | Uprava | Vidljiv razlog; nema pretpostavljenog odobrenja. |
| Odobreno | Uprava | Evidentirana osoba, vreme i obuhvat. |
| Čeka deo / termin | Garaža i Nabavka | Rad nije završen; vidi se razlog čekanja. |
| U radu | Garaža | Evidentiran početak i izvršilac/lokacija. |
| Rad potvrđen | Garaža / Veljović | Stvarni datum, kilometraža i izvršene operacije. Ovo je osnova servisne istorije. |
| Dokumentacija kompletirana | Nabavka i finansije | Dokumenti povezani i trošak proveren. |
| Otkazano | Ovlašćeno lice uz razlog | Ne briše već izvršen rad ili nastali trošak; delimičan rad ostaje evidentiran. |

Status nabavke i status intervencije ostaju različiti. Zahtev može čekati fakturu dok je vozilo već vraćeno u upotrebu. Za jednostavan ekran mogu se grupisati u nekoliko kolona, ali poslovni događaji i odgovornosti moraju ostati odvojeni.

# 7. Povezivanje Nabavke i servisne istorije

## P-08. Dokument sa postojećim nalogom

Nabavka pronalazi zahtev/nalog i povezuje izvorni dokument ili stavku. Sistem proverava vozilo, dobavljača, identitet dokumenta i postojeće veze. Veza se prikazuje na automobilu, nalogu i zahtevu. Više stavki istog dokumenta ne povećava broj faktura u pregledu.

Garaža potvrđuje da dokument odgovara intervenciji, dok finansije potvrđuju novčani obuhvat. Datum fakture/trebovanja ostaje vidljiv uz datum stvarnog izvršenja. Ako je jedan dokument vezan za više automobila, unosi se raspodela stavki ili iznosa i neraspoređeni ostatak.

## P-09. Dokument koji stiže bez prethodnog naloga

1. Nabavka može da poveže fakturu direktno sa automobilom, kako je korisnik odobrio. Ne kreira se izmišljeno prethodno odobrenje.
2. Ako vrsta rada nije poznata, ostaje „Nije razvrstano“. Naziv dela ili samo isti datum nisu dovoljan dokaz da je urađen mali/veliki servis.
3. Ako garaža kasnije utvrdi stvarnu intervenciju, dodaje se veza i potvrda rada sa dokazom. Datum unosa ostaje različit od datuma događaja.
4. Ako nema dokaza, dokument ostaje finansijska ili nabavna evidencija automobila, bez pomeranja servisnog plana.

Istorijske intervencije mogu se naknadno potvrditi na osnovu servisne knjižice, specifikacije izvršioca ili drugog proverenog dokaza. Potvrda mora označiti izvor i da je uneta naknadno. Stare dokumente ne povezivati masovno samo po približnom datumu ili iznosu.

## 7.1. Datumi koji se ne smeju poistovetiti

| Datum | Značenje | Za šta se koristi |
| --- | --- | --- |
| Prijava / zahtev | Kada je potreba evidentirana | Praćenje čekanja i ažurnosti. |
| Odobrenje | Kada je uprava donela odluku | Kontrola ovlašćenja i odobrenog obuhvata. |
| Početak i završetak rada | Kada je posao stvarno rađen | Servisna istorija, zastoj i plan narednog servisa. |
| Faktura / trebovanje | Datum pratećeg dokumenta | Dokumentacioni pregled i analiza prema datumu dokumenta. |
| Knjiženje | Finansijski period evidentiranja | Usaglašavanje sa finansijama. |
| Uvoz / unos | Kada je aplikacija dobila podatak | Kontrola ažurnosti i porekla; nije zamena za datum događaja. |

**Trenutno rešenje:** tab Servisi pravilno prikazuje datum fakture ili trebovanja i ne tvrdi da je to potvrđeni datum izvršenja. **Predlog:** zadržati taj prikaz, a iznad dodati stvarnu servisnu istoriju nakon uvođenja potvrde garaže.

# 8. Mali i veliki servis: planiranje i upozorenja

## 8.1. Podaci za svaki plan

Za vozilo i tip servisa treba sačuvati: da li je plan primenljiv, interval kilometara, eventualni interval meseci/radnih sati, izvor pravila, datum važenja, ko ga je potvrdio i poslednju potvrđenu realizaciju. „Neprimenljivo“ i „nije poznato“ moraju biti različite vrednosti.

Interval se potvrđuje prema dokumentaciji konkretnog vozila i uslovima upotrebe. [Fordov opis servisne istorije](https://www.ford.co.uk/support/how-tos/ford-services/parts-and-service/how-do-i-find-the-service-history-for-my-vehicle) navodi održavanje prema vremenu ili kilometraži, prema prvom dostignutom uslovu. To je ilustracija principa, a ne preporuka istog Fordovog intervala za sva IMS vozila.

## 8.2. Obračun

- **Sledeći servis u km = potvrđena kilometraža poslednjeg izvršenja + potvrđeni interval.**
- **Preostalo km = sledeći servis u km − poslednje prihvaćeno očitavanje.**
- Ako postoji vremenski interval: **sledeći datum = datum poslednjeg izvršenja + broj meseci**; dospeće nastupa kada se ispuni bilo koji primenljivi uslov.
- Bez početne servisne istorije ili bez potvrđenog intervala prikazuje se „potrebna dopuna“, bez izmišljenog roka.
- Ako je kilometraža nepouzdana ili opada, kilometarski obračun traži proveru. Vremenski plan može ostati vidljiv ako ima pouzdan datum, uz oznaku nedostatka kilometraže.

**Ilustracija, ne podatak o stvarnom servisu:** mali servis potvrđen na 186.900,00 km, odobreni interval 15.000,00 km, poslednje očitavanje 188.682,00 km. Sledeći prag je 201.900,00 km, a preostalo je 13.218,00 km. Sama činjenica da postoje očitavanja 186.900 i 188.682 ne dokazuje da je na prvom datumu izvršen servis.

Veliki servis ne resetuje automatski mali. Ako su u jednoj intervenciji stvarno izvršene obe obaveze, Veljović ih posebno potvrđuje. Isto važi za delimične radove, zamenu pojedinačnog dela i reklamaciju.

## 8.3. Upozorenja koja imaju smisla

| Upozorenje | Šta korisnik vidi | Reakcija |
| --- | --- | --- |
| Servis se približava / dospeo je | Poslednji potvrđeni servis, interval, preostalo km/dana | Garaža planira nalog; prag približavanja je podesiv. |
| Novi nalog za isti tip već postoji | Link na otvoreni nalog i njegov status | Proveriti da li je novi nalog potreban ili se dopunjava postojeći. |
| Sličan servis je skoro izvršen | Prethodna potvrda rada, protekli km/dani i obuhvat | Upozorenje upravi i garaži; moguća reklamacija ili opravdan novi rad. |
| Nema potvrđene servisne osnove | Šta nedostaje i koji dokumenti postoje | Dopuniti dokaz, ne izračunavati proizvoljan rok. |
| Očitavanje opada ili je zastarelo | Vrednosti, datumi i izvori | Provera unosa ili zamene brojila. |
| Rad završen, dokumenti nepotpuni | Izvršeni rad i nedostajuća faktura/trebovanje | Nabavka dopunjava vezu; servis se ne označava ponovo kao neizvršen. |

„Skoro“ treba definisati kroz podesivi period i/ili pređenu kilometražu prema vrsti rada; broj nije unapred dogovoren. Upozorenje je razlog za proveru, ne dokaz nepotrebnog rada ili odgovornosti vozača. Predlog je da svako upozorenje ima vlasnika, link na podatke i zabeležen ishod pregleda, kako ista poruka ne bi stalno ostajala bez postupanja.

## 8.4. Kilometraža i radne jedinice

Novi tab kilometraže zadržati: stvarna očitavanja, približno mesečni intervali sa tačnim datumima, decimalni zarez i izvori. OMV „korigovano u izvoru“ je preuzeto polje, a ne račun aplikacije; izvorna vrednost se vidi kada se razlikuje. Za buduće interne korekcije uvesti razlog, autora i originalnu vrednost.

Za kamion sa garniturom ili drugo radno vozilo kilometri ne predstavljaju ceo rad. Predlog je zasebna poslovna namena i, gde postoje pouzdani izvori, radni sati vozila ili priključene opreme. Potrošnja goriva iz kartice nije automatski potrošnja motora po kilometru. Bez početnog/završnog stanja rezervoara i obuhvata upotrebe ne treba prikazivati prividno precizan l/100 km.

# 9. Trošak po vozilu i trošak garaže

Ovo je predlog upravljačke metodologije. Finansije treba da potvrde izvore, PDV osnovu, valute i period pre nego što se rezultat nazove konačnim ukupnim troškom. [GSA vodič](https://www.gsa.gov/policy-regulations/policy/motor-vehicle-management-policy/motor-vehicle-policy-customer-guide) razlikuje direktne i indirektne troškove flote; konkretna raspodela u nastavku je predlog za IMS, ne primena američkih računovodstvenih pravila.

## 9.1. Tri iznosa koja treba odvojiti

**Predloženo/odobreno** pokazuje planirani obuhvat i odobrenje uprave. **Dokumentovano** pokazuje pristigle fakture i trebovanja. **Finansijski potvrđeno** pokazuje usaglašene stavke u izabranom periodu. Njihove razlike su korisne: završena usluga može čekati fakturu, a primljen račun može čekati proveru.

## 9.2. Predlog kategorija troška vozila

| Kategorija | Osnov za uključivanje | Posebna kontrola |
| --- | --- | --- |
| Gorivo | Transakcije ili potvrđena knjiženja, prema izabranom izveštaju | Kartice i knjiženja istog goriva ne sabirati. AdBlue i druge proizvode odvojiti. |
| Spoljni rad i usluge | Proverena faktura/stavka raspoređena na vozilo/intervenciju | Istu stavku ne dodavati ponovo iz ServiceTransaction. |
| Delovi iz magacina | Izdata vrednost za vozilo, umanjena za vraćeno | Nabavka zalihe i kasnije izdavanje nisu dva troška vozila. |
| Direktno kupljen i ugrađen deo | Potvrđena direktna nabavka koja nije troškovana kroz magacinsko izdavanje | Sačuvati oznaku puta dokumenta. |
| Rad interne garaže | Potvrđeni sati × odobrena cena sata | Interni obračun prikazati posebno od spoljne fakture. |
| Gume, registracija, polise, pranje, putarine, parking i praćenje | Odgovarajući izvor i kategorija | Ne prikazivati svaku ovu stavku kao popravku. |
| Lizing/najam i finansiranje | Potvrđena metodologija ugovora i finansija | Ne sabirati glavni dug, nabavnu cenu i amortizaciju bez definisanog modela. |
| Zajednički troškovi | Odobrena raspodela finansija | Neraspoređeni deo ostaje vidljiv. |
| Naknade osiguranja / reklamacije | Zaseban priliv ili umanjenje sa vezom | Pokazati bruto trošak i naknadu odvojeno, pa izvedeni neto efekat. |

Sadašnji obračun održavanja sabira ServiceTransaction.potrazuje i Requisition.vrednost_nab. U ServiceTransaction postoje 49 stavki kategorije lizing/najam i 8 stavki goriva, između ostalog. Zato prvi posao nije nova formula već potvrđena klasifikacija i provera identiteta istog troška između izvora.

**Predlog formule za period:** trošak korišćenja = gorivo + potvrđene spoljne usluge + stvarno izdat/direktno utrošen materijal + interni rad + ostale usvojene kategorije. Svaka kategorija ima jedan merodavan put do izvora. Naknade se prikazuju zasebno. Nabavna vrednost automobila ostaje podatak o nabavci, a ne automatski tekući trošak perioda.

**Primer kontrole dupliranja, iznosi samo za ilustraciju:** kupljeni delovi od 10.000 RSD primljeni su u magacin; za vozilo A izdato je 4.000, a za B 6.000 RSD. Na automobilima se prikazuju njihova izdavanja. Dodavanje još 10.000 sa ulazne fakture povećalo bi zbir na 20.000 i dvaput prikazalo isti materijal. Veza sa fakturom ostaje za praćenje porekla.

## 9.3. Jedna faktura za više vozila

Raspodela mora imati izvorni dokument/stavku, vozilo, intervenciju ako je poznata, iznos ili procenat, valutu, osnovicu i autora potvrde. Zbir raspodela ne sme preći raspoloživi iznos; ostatak ostaje „neraspoređeno“. Zaglavlje fakture ne sme se kopirati u punom iznosu na svako vozilo. Ako nema specifikacije, raspodela se ne izmišlja prema tablicama u napomeni.

## 9.4. Trošak interne garaže

Odvojiti dva pitanja: **koliko košta održavanje automobila** i **koliko košta funkcionisanje garaže**. Spoljni servis automobila nije trošak rada interne garaže, iako može biti u istom ukupnom budžetu održavanja.

Za garažu po mesecu pratiti: trošak zaposlenih prema potvrđenom obuhvatu finansija, materijal za rad, zajedničke troškove prostora/opreme i druge jasno određene stavke. Postoji SQL izvor tro_zarade i ranija ruta pregleda zarada, ali time nisu potvrđeni zaposleni/OJ koji pripadaju garaži, ostali troškovi niti cena produktivnog sata.

Prva faza može prikazivati samo potvrđene mesečne troškove garaže, broj i vrstu potvrđenih intervencija i koliko dokumentacije nedostaje. Za trošak rada po automobilu potrebna je evidencija utrošenih sati. Predlog kasnije raspodele je potvrđeni sati po nalogu × periodično odobrena stopa rada. Razlika između raspoređenog i ukupnog troška garaže ostaje vidljiva kao neraspoređeni iznos; ne sakriva se deljenjem na vozila bez podataka.

Kada se interna cena rada rasporedi na vozila, pri zbiru za ceo IMS treba ukloniti internu dvostruku raspodelu: ne sabirati pune zarade garaže i njihov isti obračun kroz sate kao dva spolja nastala troška. Finansije potvrđuju granice ovog obračuna.

## 9.5. Pokazatelji koji imaju smisla

- Trošak po vozilu i kategoriji, uz isti period, valutu i osnovicu; uvek link do izvornih stavki.
- Trošak po kilometru samo kada kilometri i troškovi pokrivaju uporediv stvarni period. Bez dovoljno očitavanja prikazati obuhvat i nedostatak, bez automatske godišnje procene.
- Trošak intervencije i odstupanje od odobrenja; nepotpuna dokumentacija mora biti označena.
- Broj ponovljenih potvrđenih radova i reklamacija, uz poslovni razlog, a ne samo isti naziv stavke.
- Dani zastoja i čekanja, kada budu uvedeni stvarni datumi i status raspoloživosti.
- Za radne jedinice, trošak po radnom satu ili zadatku tek kada postoji pouzdana evidencija rada.

Nizak broj kilometara ili visok RSD/km nije samostalna odluka o otpisu. Namena, raspoloživost, zastoji, stanje i alternativa moraju ući u procenu. Predlog je zadržati Analitiku dostupnom, ali preimenovati/ne koristiti automatske ocene isplativosti dok se izvori i metodologija ne usaglase.

# 10. Katalog postojećih izveštaja i pregleda

Ekran Izveštaji trenutno sadrži 21 stavku u šest grupa. Neke su operativni spiskovi, a neke obračunski izveštaji. Pojavljivanje u meniju nije potvrda potpunosti podataka niti finansijske metodologije.

| Grupa / postojeći pregled | Šta daje | Ograničenje / sledeći korak |
| --- | --- | --- |
| Vozni park — Potrošnja | Transakcije NIS/OMV i proizvodi po vozilu | Kupovina/točenje nije isto što i fizička potrošnja motora. |
| Vozni park — Polise | Evidencija polisa i pokrića | Razlikovati AO/kasko i rok polise od registracije. |
| Vozni park — Popravke van IMS | Knjižene ServiceTransaction stavke | Kategorije obuhvataju i druge troškove; naziv spiska nije dokaz izvršenog rada. |
| Vozni park — Popravke u IMS | Requisition stavke trebovanja | Stavka materijala nije poseban servis. Dopuniti vezu sa nalogom. |
| Vozni park — Lizing i najam | Ugovori i periodi korišćenja | Ugovoreno nije isto što i plaćeno/knjiženo. |
| Finansije — Gorivo IMS: meseci, centri i šifre | Novi periodični pregled sa vrstom proizvoda, dobavljačem, grupisanjem i Excel izvozom | Direktne transakcije; nema magacina i goriva zaposlenih bez tih izvora. |
| Finansije — OMV putnička po šifri posla | Specijalizovan pregled goriva | Usaglasiti obuhvat i izvor sa novim pregledom. |
| Finansije — OMV teretna po šifri posla | Specijalizovan pregled goriva | Ista metodološka provera; ne mešati vrste vozila i datume. |
| Finansije — NIS putnička po šifri posla | Specijalizovan pregled goriva | Proveriti uslove starog izvora i istorijski raspored. |
| Finansije — NIS teretna po šifri posla | Specijalizovan pregled goriva | Uporediti stvarni izbor vozila sa nazivom izveštaja. |
| Osiguranje — Kasko, starija od 7 godina | Izbor prema potvrđenom korisničkom kriterijumu, bez uslova visoke vrednosti; Excel | Godina preseka minus godište, strogo preko 7. Ovo nije opšte pravilo podobnosti za osiguranje. |
| Osiguranje — Vlasništvo IMS | Podaci automobila i dokumentacije za osiguranje; Excel | Podrazumevano vlasništvo jasno označiti i proveriti za zvaničnu predaju. |
| Garaža — Trenutno stanje u magacinu | Robno stanje iz SQL izvora | Ne dokazuje da je deo izdat ili ugrađen u vozilo. |
| Garaža — Otpisana vozila | Evidencija otpisanih sredstava | Ne koristiti kao automatsku listu tehnički neispravnih vozila. |
| Uprava — Knjiženi troškovi goriva po mesecima | Računovodstveni pregled, uključujući širi obuhvat izvora | Datum knjiženja i obuhvat razlikuju se od kartičnih transakcija. |
| Uprava — Ukupni troškovi po kontima, centrima, mesecima | Pregled iz fleet_tro_svi; decimalni prikaz i numerički izvoz su ispravljeni | Nije automatski raspodela svake stavke na automobil. |
| Uprava — Troškovi praćenja vozila | Fakture/usluge praćenja | Za analizu po autu potrebna je specifikacija i raspodela. |
| Uprava — Troškovi tahografa | Poseban SQL pregled | Proveriti pripadnost dokumenta i kategoriju troška. |
| Uprava — Troškovi parkinga | Poseban SQL pregled | Povezivanje sa vozilom/putovanjem i pravilom obračuna ostaje potrebno. |
| Uprava — Najveći dobavljači usluga | Promet/dokumentacija dobavljača | Pre rangiranja odrediti da li se poredi fakturisano, plaćeno ili obaveza. |
| Nabavka i delovi — AutoDeki / dobavljač | Stavke faktura ili robna evidencija, period, artikal, Excel | Tačan identitet AutoDekija još nije potvrđen; nabavljeni deo nije dokaz ugradnje. |

**Van ovog kataloga:** Pregled prikazuje trenutno stanje flote i centara; Analitika ima starije obračune i pokazatelje; detalj vozila ima periodične troškove, kilometražu i servisne dokumente. Nabavka ima sopstveni pregled statusa/tipova zahteva, faktura/narudžbenica i proveru šifre posla partnera. Njen zbir faktura trenutno koristi konkretan put veze item_links, pa ne treba pretpostaviti da obuhvata sve druge vrste povezivanja.

Postoje i ranije rute kasko rata i zarada koje nisu među 21 stavkom ovog ekrana. Njihovu dostupnost, naziv, korisnike i namenu treba usaglasiti. Posebni DDOR pregled i izdvojeni pregled zatvorenih putnih naloga ranije su uklonjeni iz planiranog toka, ali se u bazi još vide neke stare šifre dozvola. Podatke i nepotrebne stavke menija ne tretirati isto.

## 10.1. Izveštaji koje treba razviti sledeće

| Novi pregled | Ključne kolone | Korisnik i radnja |
| --- | --- | --- |
| Nalozi na odobrenju | Vozilo, predlog, poslednji sličan rad, upozorenje, procena, čekanje | Uprava odobrava ili vraća na dopunu. |
| Plan malih/velikih servisa | Potvrđena poslednja realizacija, interval, trenutni km, sledeći prag, kvalitet podataka | Garaža planira rad i dopunjava nedostatke. |
| Otvoreni radovi i zastoji | Razlog, status, početak, čeka deo/termin, zaduženo lice | Garaža i Nabavka otklanjaju razlog čekanja. |
| Ponovljeni radovi/reklamacije | Tip/operacija, razmak km/dana, prethodni nalog, razlog ponavljanja | Uprava prati upozorenja i odluke. |
| Dokumenti koji čekaju povezivanje | Dokument, poznato vozilo, nedostajući nalog/raspodela, iznos | Nabavka i finansije dopunjavaju veze. |
| Potvrđeni troškovi po vozilu | Period, kategorija, izvor, iznos, raspodela, status potvrde | Finansije usaglašavaju; uprava poredi. |
| Trošak i rad garaže | Mesečni trošak, intervencije, potvrđeni sati, raspoređeno/neraspoređeno | Finansije i uprava procenjuju opterećenje i trošak. |

# 11. Predlog tehničke arhitekture i migracija

Ovo je plan razvoja, ne već izvršena migracija. Zadržati Vehicle, TrafficCard, JobCode, VehicleHolding, VehicleTravelOrder, PutniNalog, Kvar, ProcurementCase i izvorne dokumente. Nedavno dodata veza zahteva sa nalogom i tip intervencije na zahtevu/fakturi već postoje kroz migraciju nabavka.0019.

| Promena | Predlog modela/podataka | Kada |
| --- | --- | --- |
| Životni ciklus intervencije | Dopuniti Kvar statusom, podnosiocem, odgovornim, odobrenim obuhvatom i verzijom, datumima početka/završetka i raspoloživosti | Prva faza. Kvar postaje jasan glavni nalog; ne uvoditi drugi nepovezani glavni nalog. |
| Istorija odluka | Nova tabela događaja naloga: prelaz, autor, vreme, komentar, verzija odobrenja | Prva faza. Opšti HTTP dnevnik nije zamena za poslovno odobrenje. |
| Servisni plan po tipu | ServicePlan: vozilo, tip, primenljivost, km/meseci/sati, izvor, potvrda, važenje | Prva faza. Za početak mali/veliki; kasnije druga oprema i obaveze. |
| Potvrđena realizacija plana | ServiceCompletion: nalog, tip izvršene obaveze, stvarni datum/km/sati, potvrđivač i dokaz | Prva faza. Jedan nalog može izvršiti i mali i veliki servis, uz posebnu potvrdu oba. |
| Stvarna vožnja | VehicleTrip i veza postojećih putnih naloga sa njom; zaseban stvarni vozač | Naredna faza posle uređenja osnovnog toka. Ne duplirati kilometre po putniku. |
| Raspodela novčanog dokumenta | Veza dokumenta/stavke sa vozilom/nalogom i raspoređenim iznosom | Posle usvajanja finansijske metodologije. Odrediti jedinstven identitet izvora i kontrolu zbira. |
| Sati rada i stopa | GarageWorkLog i, kada treba, periodično važeća stopa internog rada | Kada se potvrdi ko može da obezbedi podatke. |
| Namena i radna oprema | Poslovna namena na vozilu; odvojena oprema ako ima svoj inventar i održavanje | Fazno, prema stvarnom obuhvatu IMS-a. |

**Zašto servisna istorija ne pripada samo tabeli Vehicle?** Na automobilu mogu stajati trenutni opis i tehnički parametri, ali više planova, izvedenih radova, odobrenja i izmena kroz vreme čine zasebne događaje. Samo polja „poslednji mali“ i „poslednji veliki“ izgubila bi istoriju i poreklo. Mogu biti izvedeni prikaz, ne jedini zapis.

**Zašto nije dovoljan samo novi interval velikog servisa?** Broj intervala ne govori kada i na koliko kilometara je prethodni servis zaista izvršen. Potrebni su primenljivost, potvrđena realizacija i pouzdano poslednje očitavanje. Predložena tabela planova izbegava širenje Vehicle sa velikim brojem sličnih polja i omogućava istoriju izmena.

## 11.1. Pravila realizacije i migracije

1. Dodati nova polja/tabele bez izmišljanja istorijskih odobrenja i završetaka. Stari zapis dobija oznaku nepotvrđene istorije gde nema dokaza.
2. Postojeći service_interval preneti kao kandidat za mali servis, uz status da treba potvrda; vrednost 0 ne pretvarati u važeći interval. Veliki servis ostaje nepoznat dok se ne unese pravilo.
3. Stare kategorije prevesti preko eksplicitne mape. „Veliki servis u/van IMS“ može se mapirati po tipu; „Redovan servis“ čeka poslovnu potvrdu da predstavlja mali servis.
4. Izvršenje kreira isključivo ovlašćena potvrda, ne otvaranje detalja, štampa, račun ili uvoz dokumenta. Generičke predložene delove odvojiti od stvarnog izdavanja/utroška.
5. Odobrenja i prelaze statusa proveravati na serveru, u jedinstvenoj funkciji. Isto pravilo mora važiti za formu izmene, poseban endpoint, uvoz i naknadnu korekciju.
6. Čuvanje odobrenja, događaja i verzije naloga obaviti atomski. Istovremene izmene rešavati kontrolom verzije; prijaviti korisniku konflikt umesto tihog prepisivanja.
7. Zaduženja i primopredaje imaju jedinstveno pravilo preklapanja, prenosa kilometraže i granica perioda. Ispravka istorije mora ostaviti trag.
8. Ujednačiti prava ruta, AJAX tabela, izvoza, dokumenata i centara. Aktivna rola i samo prisustvo linka nisu dovoljni za proveru pristupa konkretnom objektu.
9. Izvore troškova čitati preko jedinstvenog sloja klasifikacije/raspodele. Ne praviti novu zbirnu tabelu koja će ponovo kopirati iste troškove iz više sistema bez identiteta izvora.
10. Pre primene napraviti rezervnu kopiju baze i priloga, probno prebacivanje i plan povratka. Porediti broj zapisa, veze i kontrolne sume; istorijske dokumente čuvati.

# 12. Uvođenje procedure u svakodnevni rad

## 12.1. Predložene faze

| Faza | Obuhvat | Uslov da je završena |
| --- | --- | --- |
| A — dogovor i priprema | Odgovorna lica, prava, kategorije, uzorak početne istorije i intervala | Svaka radnja ima izvršioca i potvrđivača; poznato je šta nedostaje. |
| B — osnovni rad garaže | Prijava, nalog, uprava odobrava, garaža potvrđuje, zahtevi i dokumenti | Novi rad može da prođe ceo sled bez nejasnog statusa ili nepotrebnog duplog unosa. |
| C — plan i upozorenja | Potvrđeni mali/veliki servisi, planovi, upozorenja, red za proveru | Isti ulazni podaci daju proverljiv rok i link do osnove; upozorenje ne blokira opravdan rad. |
| D — potvrđeni troškovi | Klasifikacija, raspodela, usaglašavanje izvora i izveštaj po vozilu | Finansije potvrđuju reprezentativan mesec i dokumente bez dvostrukog računanja. |
| E — širi potencijal | Rad garaže, sati, zastoji, stvarne vožnje i namena radnih jedinica | Pokazatelji koriste evidenciju koju ljudi stvarno održavaju. |

Predlog je pilot sa reprezentativnim vozilima i nekoliko stvarnih internih i spoljnih intervencija, uz garažu, jednu sekretaricu, Nabavku, finansije i upravu. Broj vozila i termini se usvajaju operativno; ne procenjuje se rok razvoja pre razlaganja i potvrde obuhvata.

## 12.2. Dnevne, nedeljne i mesečne obaveze

- **Sekretarijat:** pre puta vodi nalog; po dobijanju podataka dopunjava povratak i očitavanja; prati nezatvorena putovanja i primopredaje. Predlog roka za unos po povratku je isti ili naredni radni dan, uz potvrdu IMS-a.
- **Garaža:** pregleda prijave, upozorenja i dospeća, podnosi naloge i potvrđuje stvarne završetke. Ne odlaže potvrdu izvršenja samo zbog fakture koja kasni.
- **Uprava:** redovno obrađuje naloge na odobrenju i upozorenja uz novi zahtev. Nedeljno pregleda čekanja, ponavljanja i zastoje.
- **Nabavka:** obrađuje zahteve, povezuje dokumente i vodi spisak nedostajućih veza/specifikacija. Naknadni unos ostaje jasno označen.
- **Finansije:** mesečno potvrđuju period, klasifikaciju, raspodele i usaglašavanje sa knjiženjima; prikazuju neraspoređene/nepotvrđene iznose.
- **Administrator aplikacije:** održava pristupe i prati uspeh uvoza i oporavak podataka; ne preuzima poslovnu ulogu odobravaoca ili potvrđivača servisa.

## 12.3. Scenariji za prijem dorada

1. Sekretarica kreira putovanje sa vozačem različitim od periodično zaduženog; zaduženje ostaje sačuvano.
2. Dva putna naloga za isto zajedničko putovanje ne udvostručavaju kilometražu vozila.
3. Garaža podnosi nalog, ali ne može sama da upiše odobrenje uprave drugim ekranom ili izmenom statusa.
4. Uprava odobrava tačnu verziju i obuhvat. Kasnija dopuna je vidljiva i ne menja istorijsko odobrenje.
5. Otvaranje/štampanje naloga ne stvara stvarno utrošene delove niti potvrdu rada.
6. Garaža potvrđuje rad pre pristizanja fakture; servisni plan se zasniva na toj potvrdi.
7. Faktura bez naloga može da se poveže sa vozilom; ne stvara automatsku potvrdu servisa.
8. Jedna faktura sa više stavki/vozila ima kontrolisan zbir raspodela i vidljiv ostatak.
9. Ulaz u magacin, izdavanje i povrat ne udvostručavaju trošak materijala.
10. Upozorenje za ponovljen servis prikazuje dokaze, ali uprava može da odobri opravdan nastavak.
11. Nepoznat interval, veliki servis koji nije primenljiv i nepouzdana kilometraža daju različite, razumljive statuse.
12. Zaposleni iz druge organizacione oblasti ne dobija neodobren pristup kroz direktni URL, tabelu ili izvoz.
13. Mesečni izveštaj vozila i garaže može se usaglasiti sa potvrđenim izvorima i objasniti svaka razlika.

# 13. Potencijal aplikacije

Najveća vrednost je povezivanje već postojećih podataka u jasan tok odlučivanja. Uprava može dobiti pregled zašto se trošak predlaže, da li je sličan rad već urađen i šta čeka odobrenje. Garaža dobija servisnu istoriju i plan, a Nabavka dokumentacioni sled bez traženja po više nepovezanih spiskova.

Sledeći nivo je realno poređenje rada interne garaže i spoljnih servisa: sličan obuhvat posla, delovi, sati, cena, zastoj i reklamacije. Finansijsko poređenje bez podataka o internom radu prikazivalo bi samo deo troška i moglo bi dati pogrešan zaključak.

Kasnije aplikacija može podržati plan zamene vozila, raspodelu po centrima, namenu radnih jedinica i pouzdaniju ocenu dobavljača. Za te odluke nisu dovoljni ukupna kilometraža, knjigovodstvena vrednost i jedna granica RSD/km. Potrebna je istorija upotrebe, održavanja i raspoloživosti koju predložene procedure prvo stvaraju.

Ne predlaže se razvoj „prediktivnog“ održavanja ili automatskih ocena odgovornosti pre nego što osnovna evidencija bude pouzdana. Praktična korist prve faze je merljiva: koliko naloga ima odobrenje, koliko radova potvrdu, koliko dokumenata je povezano i koliko upozorenja je stvarno pregledano.

# 14. Otvorene odluke koje ne sprečavaju početak

| Pitanje | Ko treba da odgovori | Do odgovora |
| --- | --- | --- |
| Da li „Redovan servis u IMS / van IMS“ uvek znači mali servis? | Garaža i korisnik | Ne mapirati automatski u potvrđen mali servis. |
| Koji intervali velikog servisa i vremenski uslovi važe za svako vozilo? | Garaža, uz dokumentaciju vozila | Nepoznato ostaje nepoznato; ne kopirati isti broj celoj floti. |
| Ko su konkretni finansijski potvrđivači i odgovorno lice za matične podatke/registraciju? | Uprava | U proceduri ostaju navedene funkcije, a imena se dodaju pri uvođenju. |
| Koje kategorije, PDV osnovu, valute i datum perioda finansije potvrđuju? | Finansije | Prikazivati postojeće izvore odvojeno i označiti nepotpun obuhvat. |
| Postoje li podaci o satima rada i tačnom troškovnom obuhvatu garaže? | Garaža i finansije | Ne obračunavati izmišljenu cenu internog rada po automobilu. |
| Kako se rešavaju hitna intervencija i odsustvo odobravaoca? | Uprava | Predvideti dokumentovan izuzetak, bez automatskog preskakanja odobrenja. |
| Koji pragovi ponavljanja/dospeća odgovaraju IMS-u? | Garaža i uprava | Pripremiti podesiva upozorenja, bez proizvoljnih poslovnih granica. |
| Koji je tačan naziv/PIB/šifra AutoDekija? | Nabavka | Koristiti pregled po odabranom dobavljaču bez tvrdnje da je identitet potvrđen. |

# 15. Osnova provere i granice zaključaka

Analiza je zasnovana na aktuelnim modelima, formama, prikazima, poslovnim pomoćnim funkcijama, katalogu izveštaja, ulozi/dozvolama iz baze i razgovoru sa korisnikom. Raniji Word dokumenti korišćeni su kao istorija odluka; kod i živa struktura imaju prednost kada se stari opis razlikuje od sadašnjeg stanja. Na primer, stariji opis Nabavke pominje rok „potrebno do“, dok sadašnje polje nosi naziv datum zahteva.

Čitanje baze dokazuje šta je evidentirano, ne šta je fizički urađeno na automobilu. Podaci sa datumom preseka nisu revizorski potvrđen popis ni finansijsko usaglašavanje svih perioda. U ovom zadatku nisu menjani aplikacioni tokovi, prava korisnika ili poslovni zapisi; izrađeni su analiza, dokazni presek i dokumentacija. Ranije izvedene dorade ostaju odvojene od predloga iz ovog dokumenta.

## 15.1. Lokalni izvori za proveru nalaza

| Izvor | Šta je provereno |
| --- | --- |
| core/models.py; core/mixins.py | Uloge, dozvole, aktivne uloge i način provere akcije. |
| fleet/models.py; fleet/forms/garaza.py | Identitet vozila, interval, zaduženja, nalog garaže i ograničenja formi. |
| fleet/views/vehicle_travel_orders.py | Automatsko zatvaranje prethodnog zaduženja, prava i unos kilometraže. |
| fleet/forms/putni_nalozi.py; fleet/views/putni_nalozi.py | Kreiranje i pravdanje ličnog putnog naloga. |
| fleet/support/garaza.py; fleet/views/kvar.py | Automatsko formiranje generičkih predloženih delova i prikazi naloga. |
| nabavka/models.py; nabavka/views/cases.py | Veza vozilo–zahtev–nalog, trenutni statusi i endpoint promene statusa. |
| fleet/support/vehicle_maintenance.py; fleet/support/vehicle_mileage.py | Dokumentacioni servisni pregled, klasifikacija, očitavanja i stvarni intervali. |
| fleet/support/vehicle_detail.py; fleet/support/fuel.py | Stvarni izvori sadašnjeg periodičnog obračuna detalja. |
| fleet/views/analytics.py; fleet/support/analytics.py; fleet/support/dashboard.py | Stariji zbirni obračuni, procena kilometraže i fiksne ocene RSD/km. |
| fleet/views/reports.py; fleet/support/report_queries.py; nabavka/views/reports.py | Katalog izveštaja, SQL izvori i ograničenje obuhvata pojedinih veza. |
| core/activity.py; core/middleware.py | Opšti trag aktivnosti i njegova razlika u odnosu na poslovne potvrde. |
| izvestaji/analiza_aplikacije_stanje_20260910.json | Brojevi evidencija, kvalitet podataka, postojeće uloge i kodovi dozvola. Bez ličnih imena korisnika. |
| izvestaji/provera_izvestaja_gorivo_20260910.json | Ranija kontrola novog izveštaja goriva i razlika u starim SQL izvorima, istog dana. |

## 15.2. Spoljni izvori dobre prakse

- [ISO 55001:2024 — javni pregled standarda](https://www.iso.org/standard/83054.html): ciljevi upravljanja sredstvima i odnos troška, rizika i učinka.
- [IBM — Work order statuses](https://www.ibm.com/docs/en/control-desk/7.6.1?topic=orders-work-order-statuses): razdvajanje odobrenja, rada, fizičkog završetka i zatvaranja. Korišćen dostupan indeksirani tekst zvanične dokumentacije; direktan pristup stranici bio je ograničen.
- [U.S. DOE / FEMP — Sustainable Fleet Core Principles](https://www.energy.gov/cmei/femp/femp-best-practices-sustainable-fleet-core-principles): povezivanje namene, upotrebe, održavanja i stanja flote.
- [Ford — Service history](https://www.ford.co.uk/support/how-tos/ford-services/parts-and-service/how-do-i-find-the-service-history-for-my-vehicle): vremenski i kilometarski uslov prema servisnom planu proizvođača. Korišćen indeksirani tekst; stranica zahteva JavaScript.
- [GSA — Motor Vehicle Policy Customer Guide, avgust 2026](https://www.gsa.gov/policy-regulations/policy/motor-vehicle-management-policy/motor-vehicle-policy-customer-guide): direktni/indirektni troškovi i vođenje evidencije tokom životnog ciklusa.

Izvori su konsultovani 10.09.2026. Koriste se za opšte principe i poređenje prakse. Konkretne procedure IMS-a, odobravanja, finansijska pravila i tehnički intervali usvajaju se interno na osnovu potvrđenih podataka.
