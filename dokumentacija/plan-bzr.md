# Plan implementacije modula „BZR" — bezbednost i zdravlje na radu, zaštita od požara i vanredne situacije

Datum: 05.10.2026. Usklađeno sa **Zakonom o bezbednosti i zdravlju na radu** („Sl. glasnik RS", br. 35/2023) i
**Zakonom o zaštiti od požara** („Sl. glasnik RS", br. 111/2009, 20/2015, 87/2018) istog dana.
Za koga: Uprava i savetnik/saradnik za BZR (lice za BZR i ZOP) — odluke u odeljcima 0, 1, 3 i 13; programeri —
odeljci 5–12.

Plan je izrađen na osnovu dokumenata iz fascikle `BZR`, teksta zakona i pregleda postojeće aplikacije (odeljak
„Izvori"). Dokumenti su pročitani u celini, uključujući skenirane. Akt o proceni rizika u zaštiti lica, imovine i
poslovanja i Plan tehničke zaštite označeni su kao **poslovna tajna**; ovde su opisani samo uopšteno.

U tekstu „Zakon" znači Zakon o BZR 35/2023, a „čl." bez druge oznake — član tog zakona. „ZZOP" je Zakon o
zaštiti od požara, a „ZZOP čl." član tog zakona.

---

## 0. Ukratko

**Cilj:** jedno mesto na kome savetnik za BZR vidi **ko, šta i do kada** mora da uradi — za svakog zaposlenog,
svaki aparat i mašinu, svaki objekat i svaki akt — i gde se čuva dokaz da je urađeno. Danas su te obaveze
razbacane po 11 akata, papirnim evidencijama i ugovorima sa ovlašćenim firmama, a rokovi se ne prate. Akti
Instituta su doneti po starom zakonu i nisu usklađeni sa novim, iako je rok za to istekao u maju 2025 (čl. 111).

```
ZAPOSLENI     radno mesto → obuka za bezbedan rad (1 / 3 god.) → obuka ZOP → prva pomoć → lekarski → LZO
OPREMA        oprema za rad (191 kom) → PP aparati, hidranti, panik, dojava → instalacije, gromobran → stručni nalazi
OBJEKTI       4 objekta i prostorije → radna sredina → prva pomoć → planovi evakuacije, vežbe → zakupci (sporazum)
DOGAĐAJI      povreda (prijava 24 h / 5 radnih dana) → opasna pojava → profesionalna bolest → požar → zabrane
ZAHTEVI       zaposleni prijavljuje nedostatak (rok 8 dana) → dozvola za rad na visini, u dubini, sa hemikalijama
AKTI I MERE   pravilnici, planovi, procene (izmene i rokovi) → imenovanja i licence → mere i rešenja inspekcije
KROZ SVE      rokovi i podsetnici → karton zaposlenog → evidencije iz čl. 62 → izveštaji (Excel, PDF)
```

**Ključne odluke koje predlažemo:**

1. **Jedan modul `bzr` za BZR, zaštitu od požara (ZOP) i vanredne situacije.** Isti ljudi, isti objekti i ista
   oprema pojavljuju se u sva tri domena. Tehnička zaštita i zaštita lica i imovine ulaze samo kao registar
   akata sa rokom revizije i merama, uz posebnu dozvolu (poslovna tajna).
2. **Rokovi se računaju, ne prepisuju.** Za svaku vrstu obaveze šifarnik kaže period i okidač; sledeći rok =
   poslednje izvršenje + period. Ekran „Rokovi" pokazuje istekle, one koji ističu i one bez podatka.
3. **Svaki period ima izvor i oznaku „potvrđeno".** Gde rok daje zakon (obuka 1/3 godine, prijava povrede
   24 h / 5 radnih dana, stručni nalaz 30 dana, zahtev zaposlenog 8 dana; kontrola PP aparata, hidranata i
   dojave na 6 meseci, osnovna obuka ZOP za 30 dana, provera znanja ZOP na 3 godine), izvor je član zakona. Gde ga daju
   podzakonski akti ili stari interni akti, savetnik za BZR ga potvrđuje pre nego što počne da šalje upozorenja.
4. **Kadrovi su izvor zaposlenih i radnih mesta.** Prijem, premeštaj i promena radnog mesta automatski otvaraju
   obaveze iz čl. 33 (obuka), čl. 56 (lekarski) i čl. 28 (LZO).
5. **Evidencije iz čl. 62 vode se u aplikaciji — osim evidencije o obučenim zaposlenima.** Zakon izričito kaže da
   se ta evidencija ne može voditi elektronski (čl. 62 st. 3). Aplikacija zato vodi podatke i štampa obrazac za
   svojeručni potpis, a skenirani potpisani primerak je dokaz; papirni original (ili kopija) drži se tamo gde
   zaposleni radi (čl. 62 st. 2). Ostale evidencije (radna mesta sa povećanim rizikom i lekarski, povrede, oprema,
   radna sredina, LZO…) vode se elektronski.
6. **Zdravstveni podaci se ne čuvaju.** Podaci o lekarskim pregledima su poverljivi i pod nadzorom medicine rada
   (čl. 55). Iz izveštaja se beleži samo ocena sposobnosti, datum i sledeći rok; u evidencijama samo ime, prezime i
   naziv radnog mesta (čl. 63 st. 1).
7. **Zaposleni koristi modul**: vidi svoje rokove, prijavljuje nepravilnost ili opasnost (rok poslodavcu 8 dana,
   čl. 42), potvrđuje upoznavanje sa uputstvima, a savetnik vidi rok i odgovor.
8. **Svi dokazi se čuvaju na lokalnom Windows serveru** (kao odluka za arhivu, 05.10.2026.), sa preuzimanjem samo
   kroz proveru dozvole, ne preko `/media/`.

Šta treba pribaviti i odlučiti pre početka dato je u odeljku 1. Najvažnije: **važeći Akt o proceni rizika na
radnim mestima** nije u fascikli, a od njega zavise radna mesta sa povećanim rizikom, lekarski pregledi, LZO i
sadržaj obuke (čl. 16, 17, 33).

---

## 1. Pre početka: šta pribaviti i šta odlučiti

Implementacija ne čeka sve odluke. Svaka faza (odeljak 11) traži samo deo. Oznake B-1 … B-30 su pitanja iz
odeljka 13.

### 1.1 Odmah — pre faze 1

| # | Stavka | Vrsta | Ko | Zašto |
|---|---|---|---|---|
| 1 | **Važeći Akt o proceni rizika na radnim mestima** (br. 82-14150 iz 2009, poslednja izmena 82-9274 od 07.08.2020. — po Aktu LIP, str. 58) i da li je menjan po čl. 16 st. 4 Zakona | dokument | Savetnik za BZR | Bez njega nema radnih mesta sa povećanim rizikom (B-1) |
| 2 | **Normativ LZO** po radnom mestu (vrsta, količina, rok trajanja) | dokument | Savetnik za BZR | LZO se obezbeđuje „u skladu sa aktom o proceni rizika" (čl. 15 t. 5) (B-2) |
| 3 | **Ko danas obavlja poslove**: savetnik ili saradnik za BZR (ime, akt o imenovanju, broj i rok licence), predstavnik zaposlenih, Odbor, lice za ZOP, poverenik CZ, krizni tim, lica za prvu pomoć, komisije (B-3) | odluka | Uprava | Imenovanja i licence ulaze u šifarnik uloga |
| 4 | **Delatnost po čl. 48 ili 49** i broj savetnika/saradnika (B-21) | odluka (pravna) | Uprava, pravna služba | Od toga zavisi da li je potreban savetnik (240 ESPB) ili saradnik (180 ESPB) i koliko njih |
| 5 | **Koji podzakonski akti su doneti po novom Zakonu** (rok im je bio 18 meseci, čl. 108): evidencije i rokovi čuvanja, pregledi opreme i radne sredine, lekarski pregledi, prva pomoć, izveštaj o povredi, procena rizika (B-28) | odluka (pisana potvrda) | Savetnik za BZR, pravna služba | Iz njih dolaze periodi koje Zakon ne daje; stari se primenjuju dok se ne zamene |
| 6 | **Gde ko radi**: objekat (i smena, gde postoji) za svakog zaposlenog ili po OJ; ko radi noću (B-5, B-24) | odluka | Savetnik za BZR, Kadrovi | Prva pomoć mora biti dostupna u svim smenama i lokacijama (čl. 18); noćni rad traži lekarski (čl. 56 st. 2) |
| 6a | **Stanje Plana zaštite od požara**: da li je posle 2018. menjan, ima li saglasnost MUP-a na plan i izmene, ko organizuje **stalno dežurstvo** i da li agencija ima ovlašćenje MUP-a (B-29, B-14) | dokument | Lice za ZOP | Za II kategoriju Plan je obavezan i menja se sa svakom promenom (ZZOP čl. 24, 25, 27) |

### 1.2 Pre faze 2 (zaposleni)

| # | Stavka | Vrsta | Ko | Zašto |
|---|---|---|---|---|
| 7 | **Postojeće evidencije**: obučeni zaposleni (Obrazac 6), zapisnici obuke ZOP (poslednja 26. i 29.11.2021, 340 lica), lekarski pregledi, lica za prvu pomoć | dokument | Savetnik za BZR | Početno stanje. Bez njega svi zaposleni izgledaju neobučeno. |
| 8 | **Usklađen Program obuke** (opšti i posebni deo, čl. 34), uključujući program obuke rukovodilaca i predstavnika zaposlenih (čl. 35, 50 t. 2) | dokument | Savetnik za BZR | Sadržaj obuke i provere |
| 9 | **Ko vrši proveru** i prag (Pravilnik čl. 25 i Program čl. 26 se razlikuju; Zakon traži proveru na radnom mestu, čl. 34 st. 5) (B-6) | odluka | Uprava, savetnik za BZR | Ko potpisuje proveru |
| 10 | **Medicina rada**: ugovor, način dostave izveštaja o pregledu bez narušavanja poverljivosti (čl. 55 st. 3) (B-12) | dokument | Savetnik za BZR, nabavka | Šta se uopšte unosi u modul |

### 1.3 Pre faze 3 (oprema i objekti)

| # | Stavka | Vrsta | Ko | Zašto |
|---|---|---|---|---|
| 11 | **Popis opreme za rad posle 2019.** — početna verzija: [`bzr/oprema-za-rad-2019.xlsx`](bzr/oprema-za-rad-2019.xlsx) (191 stavka iz priloga Pravilnika o pregledima, sa kolonama za proveru) (B-8) | dokument | Savetnik za BZR, centri | Uvoz registra opreme |
| 12 | **Popis PP opreme po prostorijama** (tip, serijski broj, godina, datum ispitivanja) i da li je uvedena dojava požara (B-9) | dokument | Lice za ZOP, serviser | Tabele u Pravilima ZOP su prazne, planovi daju različite brojeve |
| 13 | **Ugovori i licence ovlašćenih firmi** (pregledi opreme i instalacija, radna sredina, servis PP opreme, medicina rada, tehnička zaštita) (B-10) | dokument | Nabavka, savetnik za BZR | Licence važe 5 godina (čl. 75); nalaz firme bez važeće licence ne važi |
| 14 | **Poslednji stručni nalazi** (oprema i instalacije — jul 2019; radna sredina; hidranti i aparati — 21.06.2021; gromobran) | dokument | Savetnik za BZR | Početni rokovi |
| 15 | **Sporazumi sa zakupcima** o podeli radnog prostora i licu za koordinaciju (čl. 24) (B-23) | dokument | Pravna služba | Zakupci u Upravnoj zgradi (fakultet, institut, firma) |

### 1.4 Pre faza 4–6

| # | Stavka | Vrsta | Ko | Zašto |
|---|---|---|---|---|
| 16 | **Ovlašćeno službeno lice za Registar povreda na radu** prijavljeno Upravi (čl. 69 st. 4) (B-26) | odluka | Uprava | Povrede se unose u državni Registar; modul priprema podatke |
| 17 | **Postupak za izdavanje dozvole za rad** (čl. 27 st. 2) (B-22) | dokument | Savetnik za BZR | Rad na visini, u dubini, sa opasnim hemikalijama, na energetskim objektima |
| 18 | **Polisa osiguranja zaposlenih** od povreda na radu i profesionalnih bolesti (čl. 67) | dokument | Finansije | Rok važenja polise |
| 19 | **Pristup zdravstvenim podacima i alko-proverama** (B-12) | odluka | Uprava, pravna služba | Posebne dozvole |
| 20 | **Vežbe evakuacije** i **dežurstvo** za II kategoriju ugroženosti od požara (B-13, B-14) | odluka | Uprava, lice za ZOP | Akti ih ne uređuju |
| 21 | **Imejl za podsetnike** (B-15) | tehničko | IT | U aplikaciji imejl nije podešen |

---

## 2. Principi

1. **Kadrovi su izvor istine za zaposlene i radna mesta.** BZR ne vodi sopstveni spisak ljudi; dodaje samo ono što
   Kadrovi nemaju (objekat rada, smena, uloge, noćni rad).
2. **Rok se računa iz poslednjeg izvršenja i perioda iz šifarnika.** Nema ručnog upisivanja „sledećeg roka" osim
   kada ga nalaz ili rešenje izričito propiše.
3. **Svaki period ima izvor** (član Zakona, podzakonski akt, akt Instituta) i oznaku „potvrđeno". Nepotvrđen
   period se vidi, ali ne šalje podsetnik. Promena perioda ne menja istoriju.
4. **Jedan događaj, jedan zapis.** Vežba evakuacije zadovoljava i Pravila ZOP i Plan zaštite i spasavanja; obuka
   prve pomoći je ista za BZR i CZ.
5. **Dokaz je fajl, a ne čekirano polje.** Nalaz, zapisnik, potpisan obrazac i izveštaj se prilažu.
6. **Minimum ličnih podataka** (čl. 63): u evidencijama ime, prezime i radno mesto; JMBG i ostalo za izveštaj o
   povredi uzima se iz Kadrova u trenutku izrade izveštaja; bez dijagnoza.
7. **Obuhvat po registru organizacije** (kao Kadrovi, AGENTS.md §9 zamka 12): rukovodilac vidi svoje zaposlene;
   savetnik za BZR i Uprava vide sve; predstavnik zaposlenih i Odbor imaju uvid u akte i evidencije o povredama
   (čl. 58 st. 2, čl. 59).
8. **Ništa se ne briše.** Ispravka je nova verzija ili storno sa razlogom; dnevnik ko je šta menjao.

---

## 3. Zatečeno stanje

### 3.1 Dokumenti u fascikli

| Dokument | Datum | Osnov | Napomena |
|---|---|---|---|
| **Pravilnik o BZR** | mart 2023 (zamenjuje 82-17626 od 14.11.2019) | **stari** Zakon o BZR 101/05… | Donet pre novog Zakona; **mora se uskladiti** (rok maj 2025, čl. 111) |
| **Program osposobljavanja za bezbedan i zdrav rad** | 14.11.2019 (datum usvajanja prazan) | stari zakon; Pravilnik iz 2019 | Nema periodične obuke za sva radna mesta, programa za rukovodioce ni predstavnike zaposlenih |
| **Pravilnik o periodičnim pregledima opreme za rad, radne sredine, gromobranskih i el. instalacija** („opr ras gei") | nov. 2019 | stari zakon; Pravilnik 94/06…; propisi iz 1989 i 1996 | **191 stavka opreme za rad**, rok 3 godine; sadržaj stručnog nalaza. **Nema LZO.** |
| **Plan zaštite od požara** | jan. 2018 (INZA, TK 2801-1/18) | ZZOP 111/09, 20/15 | **Glavni akt za II kategoriju** (ZZOP čl. 27). 4 objekta, aparati i hidranti, opasne materije i boce, mere 2018–2023 (**istekle**). Saglasnost MUP-a se u tekstu ne vidi. |
| **Pravila zaštite od požara** (+ identična kopija) i **Aneks 1** | 08.06.2012 i 17.11.2016 | ZZOP 111/09, 20/15 | Donete po ZZOP čl. 28, koji važi za subjekte **bez** obaveze Plana. Od rešenja iz 2016 (II kategorija) zakonski akt je Plan; Pravila mogu ostati kao interni akt sa ulogama, zabranama i odobrenjima. **Navode III kategoriju.** |
| **Program obuke iz ZOP** (skeniran) | 27.04.2018, saglasnost MUP 22.05.2018 | ZOP čl. 53 | Obuka u 30 dana od prijema, 4 časa, provera na 3 godine, prag 70% |
| **Plan zaštite i spasavanja**, **Procena rizika od katastrofa** | 2021, 2020 (saglasnost 22.01.2021) | Zakon o smanjenju rizika od katastrofa 87/2018 | Krizni tim, poverenici, timovi, obrasci PD-1 … PD-5 |
| **Akt o proceni rizika u zaštiti lica, imovine i poslovanja**, **Plan tehničke zaštite** (poslovna tajna) | nov. 2021, mart 2022 | Zakon o privatnom obezbeđenju | Revizija Akta na 3 godine — **rok nov. 2024** |

### 3.2 Šta nedostaje

- **Akt o proceni rizika na radnim mestima** (BZR) — obavezan za sva radna mesta (čl. 16).
- Normativ **LZO**; program obuke **rukovodilaca** i **predstavnika zaposlenih** (čl. 35, 50).
- Postupak za **dozvolu za rad** (čl. 27) i **sporazumi o podeli radnog prostora** sa zakupcima (čl. 24).
- Druga sveska Plana ZOP (simulacija evakuacije), grafički prilozi sa rasporedom aparata, Sanacioni plan.
- Rešenja o imenovanju (savetnik za BZR, poverenici CZ, Odbor, predstavnik zaposlenih) — u planovima su slike.

### 3.3 Šta je po dokumentima verovatno isteklo (proveriti)

| Šta | Poslednje po dokumentima | Rok | Isteklo |
|---|---|---|---|
| **Usklađivanje poslovanja sa novim Zakonom** (akti, organizacija poslova BZR) | — | 2 godine od stupanja Zakona na snagu (čl. 111 st. 7) | maj 2025 |
| Pregled opreme za rad, el. i gromobranskih instalacija, radne sredine | jul 2019 | 3 godine | jul 2022 |
| **Periodična obuka za bezbedan i zdrav rad — sva radna mesta** | nepoznato (Program nije propisivao) | 1 god. (povećan rizik) / 3 god. (ostala) (čl. 34 st. 6) | proveriti za svakog zaposlenog |
| Provera znanja iz ZOP (svi zaposleni) | 26. i 29.11.2021 | 3 godine | nov. 2024 |
| Revizija Akta o proceni rizika LIP | nov. 2021 | 3 godine | nov. 2024 |
| Mere i finansijski plan Plana ZOP | 2018 | 2018–2023 | 2023 |
| Izmene Plana ZOP sa saglasnošću MUP-a (promene zakupaca, broja zaposlenih, opreme, kotlarnice…) | 2018 | pri svakoj promeni (ZZOP čl. 27 st. 4–5) | proveriti |
| Kontrola PP aparata, hidranata i dojave od ovlašćenog lica | 21.06.2021 | **6 meseci** (ZZOP čl. 44) | dec. 2021, ako posle nije rađena |
| Automatska dojava požara u Upravnoj zgradi (Plan ZOP: potrebna; procena rizika po ZZOP čl. 42 st. 4) | — | mera iz Plana, rok 2018–2023 | proveriti da li je ugrađena |
| Usklađivanje Pravila ZOP sa II kategorijom i izmenama Zakona o ZOP | 2012 | — | — |

Ovo je prvi sadržaj ekrana „Rokovi" posle uvoza (faza 1), da Uprava odmah vidi zatečeno stanje. Za
neusklađenost sa Zakonom o BZR zaprećena je kazna za Institut i do 2.000.000 dinara, a za direktora do 150.000
dinara; po ZZOP (čl. 82) za Institut do 1.000.000 dinara, a za odgovorno lice do 50.000 dinara — između ostalog
za nedonete izmene Plana ZOP, neistaknut plan evakuacije, nekontrolisane instalacije i uređaje, neorganizovanu
protivpožarnu stražu i obuku van roka.

### 3.4 Šta novi Zakon menja u odnosu na akte Instituta

| Tema | Akti Instituta (2019–2023) | Zakon 35/2023 | Posledica za modul |
|---|---|---|---|
| Lice za BZR | „lice za BZR" sa stručnim ispitom | **savetnik** (240 ESPB, čl. 48) ili **saradnik** (180 ESPB, čl. 49), stručni ispit i **licenca na 5 godina**, imenovan pisanim aktom (čl. 4, 15, 46); kontinuirano usavršavanje uslov za obnovu (čl. 53) | Imenovanje sa licencom i rokom; podsetnik 60 dana pre isteka (čl. 75) |
| Periodična obuka | samo za povećan rizik, „po aktu o proceni rizika" | **najkasnije 1 godina** za povećan rizik, **3 godine** za ostala radna mesta (čl. 34 st. 6) | Svi zaposleni dobijaju periodični rok |
| Okidači obuke | prijem, premeštaj, nova sredstva, promena procesa | isto + **promena opreme za rad**; obuka na svakom od dva ili više radnih mesta; zaposleni drugog poslodavca pod našim nadzorom (čl. 33) | Okidači iz Kadrova i iz registra opreme |
| Provera | test 90% / 100%, komisija | teorijska i **praktična provera na radnom mestu** (čl. 34 st. 5); obuka na jeziku koji zaposleni razume | Zapis gde je provera obavljena |
| Dodatna obuka | vanredna, po odluci | posle teške, smrtne ili kolektivne povrede **odmah, najkasnije 8 dana**, za zaposlene na tom radnom mestu u toj OJ, uz obaveštenje svih (čl. 36 st. 2) | Povreda automatski otvara rok od 8 dana |
| Posebne grupe | posebna zaštita žena, omladine, invalida | **pisano obaveštenje** o rezultatima procene rizika za trudnice, porodilje, dojilje, mlađe od 18, osobe sa invaliditetom i sa profesionalnom bolešću (čl. 36 st. 3) | Obaveza bez ličnih podataka o stanju — evidentira se samo da je obaveštenje uručeno |
| Obuka predstavnika zaposlenih i rukovodilaca | nema | predstavnik: **odmah po izboru**, periodično **3 godine** (čl. 35); rukovodioci: program obuke (čl. 50 t. 10) | Nove vrste obuke |
| Lekarski pregledi | povećan rizik; sistematski 12 meseci | povećan rizik + **noćni rad** (čl. 56 st. 2); **na zahtev zaposlenog najkasnije na 5 godina** (st. 5); nesposoban → premeštaj (st. 4); rokovi po zajedničkom pravilniku ministara | Okidač „noćni rad"; zahtev zaposlenog |
| Radno mesto sa povećanim rizikom | „po aktu o proceni rizika" | po zakonu **uvek**: rad na visini (≥ 2 m), u dubini (> 1 m), **upravljanje vozilima** i unutrašnjim transportom (dizalice, viljuškari…) + ostala po aktu (čl. 4 t. 21) | Vozači službenih vozila (Flota) i rukovaoci dizalicama su povećan rizik po zakonu |
| Evidencije | „u skladu sa Zakonom", nisu nabrojane; Obrazac 6 elektronski dozvoljen | **9 evidencija** (čl. 62 st. 1); elektronski **osim evidencije o obučenim zaposlenima**; čuva se tamo gde zaposleni radi (st. 2) | Odeljak 6.6 |
| Stručni nalaz | sadržaj nalaza | izdaje se **najkasnije 30 dana** od pregleda; neispravna oprema dobija **nalepnicu**, rad se **odmah zabranjuje** do novog nalaza (čl. 15 st. 3–4) | Kontrola roka nalaza; automatska zabrana |
| Povrede | izveštava „nadležne organe" | smrtna, kolektivna, teška povreda i opasna pojava: inspekcija rada i MUP **odmah, najkasnije 24 h**; laka povreda sa nesposobnošću > 3 dana: inspekcija **najkasnije 5 radnih dana**; profesionalna bolest: **5 dana** od mišljenja (čl. 64); izveštaj zaposlenom, RFZO i Upravi (čl. 65); **Registar povreda na radu** — unosi poslodavac (čl. 68–69) | Rokovi prijave kao obaveze sa satom; priprema podataka za Registar |
| Prava zaposlenih | pravo da odbije rad | pisani zahtev poslodavcu; **8 dana** pa inspekcija (čl. 39); obaveštenje o nedostatku, **8 dana** za otklanjanje (čl. 42); ako poslodavac smatra odbijanje neopravdanim — odmah inspekcija (čl. 39 st. 4) | Prijava nepravilnosti u aplikaciji sa rokom |
| Zabrana rada | lice za BZR, direktor centra, rukovodilac | savetnik zabranjuje i **pisano obaveštava poslodavca i predstavnika zaposlenih**; ako poslodavac naloži nastavak — savetnik **odmah inspekciji** (čl. 50 st. 3–4) | Polja za obaveštenja |
| Dozvola za rad | nema | **obavezna** pre rada na visini, u dubini, u skučenom prostoru, u Ex atmosferi, na energetskom objektu, sa opasnim hemikalijama, u zonama opasnosti; poslodavac utvrđuje postupak (čl. 27) | Novi zapis „dozvola za rad" |
| Odbor za BZR | direktor imenuje (Pravilnik čl. 19) | **zaposleni biraju** predstavnike; Odbor najmanje 3 predstavnika zaposlenih + bar 1 predstavnik poslodavca, zaposlenih više za bar 1 (čl. 57); predstavniku **najmanje 5 časova mesečno** plaćenog odsustva (st. 5) | Imenovanje sa izvorom „izbor"; konsultacije (čl. 58) |
| Podela radnog prostora | ugovor sa zakupcem o odgovornosti (Pravila ZOP) | **pisani sporazum pre početka** i lice za koordinaciju (čl. 24) | Registar sporazuma sa rokom |
| Gradilište i radilište | „Prilog o BZR" sa odgovornim inženjerima | prijava inspekciji **najmanje 8 dana pre** početka, elaborat o uređenju gradilišta (radovi > 3 dana) ili radilišta; hitni radovi — odmah (čl. 22–23) | Opciono: evidencija radilišta po šifri posla (faza 8) |
| Hemijske materije, oprema | — | bezbednosni list dostupan i preveden (čl. 30); oprema sa ispravom o usaglašenosti i uputstvom na jeziku koji zaposleni razume (čl. 29) | Polja na opasnoj materiji i opremi |
| Osiguranje | — | zaposleni se osiguravaju od povreda na radu i profesionalnih bolesti (čl. 67) | Rok polise |
| Akt o proceni rizika | izmena „po potrebi" | izmena pri **svakoj** novoj opasnosti, promeni nivoa rizika, **novom radnom mestu**, novoj tehnologiji, promeni radne sredine (čl. 16 st. 4); program postupnog otklanjanja nedostataka (čl. 32) | Okidač: novo radno mesto u sistematizaciji bez procene |

### 3.5 Šta Zakon o zaštiti od požara traži od Instituta (II kategorija)

| Tema | ZZOP | Akti Instituta | Posledica za modul |
|---|---|---|---|
| Organizacija | Preventivne mere, **stalno dežurstvo** sa potrebnim brojem stručno osposobljenih lica, adekvatna oprema (čl. 24 st. 2); poslovi se mogu ugovoriti sa pravnim licem koje ima **ovlašćenje MUP-a** (čl. 25) | Plan ZOP 2018: agencija sa 6 vatrogasaca-čuvara, dežurstvo 24/7; Pravila ga ne uređuju | Imenovanja i ugovor sa agencijom (ovlašćenje, rok); raspored dežurstva kao dokaz (B-14) |
| Plan zaštite od požara | Obavezan; sadrži i proračun broja ljudi za bezbednu evakuaciju; postupa se po proračunima; **izmene pri svakoj urbanističkoj, tehničko-tehnološkoj i drugoj promeni**; saglasnost MUP-a na plan i izmene (čl. 27) | Plan iz 2018, mere do 2023 | Akt sa okidačima za izmenu (promena objekata, zakupaca, broja lica, opreme); rok saglasnosti |
| Plan evakuacije i uputstva | Moraju biti **istaknuti na vidljivom mestu** (čl. 27a) | Istaknuti po spratovima (Plan zaštite i spasavanja) | Provera istaknutosti pri obilasku objekata |
| Kontrola instalacija i uređaja | Dojava, gašenje, detekcija gasova, Ex zone, odvođenje dima, **hidrantska mreža i mobilni uređaji (aparati)**: kontrola **na svakih 6 meseci od ovlašćenog pravnog lica** (čl. 44); održavanje po propisima, standardima i uputstvu proizvođača (čl. 43); sve ugrađene instalacije periodično po tehničkim propisima (čl. 40 st. 4) | Pravila čl. 11: aparati 6 meseci, hidranti 2× godišnje, dojava 2 meseca / godišnje / 3 godine | Rok 6 meseci je zakonski; izvršilac mora imati ovlašćenje MUP-a; isprava o kontrolisanju je dokaz |
| Dojava i gašenje | Za objekte van spiska iz čl. 42 st. 1 obavezna je **procena rizika** o potrebi za dojavom i gašenjem (čl. 42 st. 4) | Plan ZOP 2018 zaključuje da je dojava potrebna u Upravnoj zgradi | Mera sa rokom dok se ne ugradi |
| Osnovna obuka zaposlenih | **Odmah po stupanju na rad, najkasnije 30 dana**; provera znanja **jednom u 3 godine**; program sa saglasnošću MUP-a, opšti i posebni deo; obuku izvodi ovlašćeno pravno lice ili lice na poslovima ZOP u Institutu (čl. 53); prisustvo obavezno (čl. 54) | Program 2018 sa saglasnošću; Pravila kažu 1 godina | Rokovi su zakonski; svaka izmena Programa traži novu saglasnost |
| Lica na poslovima ZOP | Rukovodilac službe ZOP i lice za preventivne mere u II kategoriji: **najmanje prvi stepen visokog obrazovanja** (čl. 52); **posebna obuka i stručni ispit u roku od 1 godine** od raspoređivanja (čl. 55) | Rukovodilac sa stručnim ispitom | Imenovanje sa stručnim ispitom (broj, datum); rok 1 godina za novo lice |
| Protivpožarna straža | Obavezna pri pretakanju > 5 m³, **zavarivanju, rezanju, lemljenju i otvorenom plamenu van za to prilagođene prostorije**, javnim skupovima; prisustvo stručno osposobljenih lica sa opremom (čl. 51) | Pravila čl. 43–47: odobrenje lica za ZOP, evidencija zavarivanja | Dozvola za vruće radove sa stražom (deo „dozvole za rad") |
| Zapaljivi materijal | Ne bliže od **6 m** od objekta (čl. 48); tehnološki procesi sa zapaljivim tečnostima i gasovima u požarno odvojenim prostorima (čl. 37) | Pravila čl. 59; Plan ZOP: trihloretilen u evakuacionom hodniku | Nalaz obilaska → mera |
| Prilazi i evakuacioni putevi | Zabrana zapreka na prilazima vatrogasnim vozilima i evakuacionim putevima (čl. 41) | Pravila: dnevna kontrola (održavanje, obezbeđenje) | Čeklista obilaska |
| Inspekcija | Za I i II kategoriju **periodični pregled** inspekcije (čl. 73); rešenja o merama i zabranama (čl. 77–79) | — | Rešenje inspekcije → mere sa rokom |

---

## 4. Obaveze koje modul prati

### 4.1 Uloge

| Uloga | Odakle | U modulu |
|---|---|---|
| Generalni direktor (poslodavac) | čl. 9, 15; Pravila ZOP čl. 58 | Imenuje savetnika, prima obaveštenja o zabranama, odluke |
| **Savetnik / saradnik za BZR** (licenca 5 god.) | čl. 46–50, 53 | Glavni korisnik: evidencije, obuke, pregledi, lekarski, zabrane, prijave, usklađivanje akata (čl. 50) |
| Lice za ZOP / rukovodilac službe ZOP | ZZOP čl. 52, 55; Pravila ZOP čl. 56 | Najmanje prvi stepen visokog obrazovanja, posebna obuka i stručni ispit (u roku od 1 godine); obuke i PP oprema |
| Agencija za fizičko-tehničko obezbeđenje (dežurstvo, vatrogasci-čuvari) | ZZOP čl. 24–25 | Ugovor i ovlašćenje MUP-a; dežurstvo za II kategoriju |
| Direktori centara, neposredni rukovodioci | Pravilnik čl. 7, 10; čl. 46 st. 2 (svakodnevno praćenje) | Praktična obuka, nadzor neobučenog, zabrana rada, LZO zaduženja, dozvole za rad |
| Kadrovska služba | Pravilnik čl. 6 | Obaveštava o prijemu i premeštaju — **automatski iz Kadrova** |
| Predstavnik zaposlenih, Odbor za BZR | čl. 57–61 | Uvid u akte i evidencije o povredama i merama inspekcije; konsultacije; obuka |
| Poverenik CZ i zamenici, krizni tim, timovi, kuriri | Plan zaštite i spasavanja | Šifarnik uloga po objektu |
| Lica za prvu pomoć | čl. 18; Pravilnik čl. 60 | Dostupna u svim smenama i na svim lokacijama |
| Komisije (provera obuke, alko-provera, Komisija ZOP) | Pravilnik čl. 25, 47; Pravila ZOP čl. 73–77 | Potpisuju zapisnike |
| Ovlašćeno službeno lice za Registar povreda | čl. 69 st. 3–4 | Unosi povrede u državni Registar |
| Lice za koordinaciju sa zakupcima | čl. 24 st. 4 | Iz sporazuma |
| Ovlašćene firme (pregledi, radna sredina, PP servis, medicina rada, TZ) | čl. 15 t. 7, 54, 75 | Šifarnik izvršilaca sa licencom i rokom |

Sve uloge su jedan model **Imenovanje**: zaposleni, uloga, objekat (opciono), akt (broj, datum, fajl), način
(imenovan / izabran), važi od–do, licenca (broj, važi do) gde je propisana.

### 4.2 Periodi i rokovi (početni šifarnik)

Kolona „Status": **Zakon** — rok iz Zakona 35/2023; **potvrditi** — iz podzakonskog ili internog akta, čeka
potvrdu (tačka 1.1/5).

| Obaveza | Okidač | Rok / period | Izvor | Status |
|---|---|---|---|---|
| Obuka za bezbedan i zdrav rad (teorija + praksa + provera na radnom mestu) | prijem ili drugo angažovanje; premeštaj; nova tehnologija, sredstva ili **promena opreme**; promena radnog procesa | pre početka rada | čl. 33, 38 st. 1 | Zakon |
| Obuka na svakom radnom mestu | zaposleni radi na 2+ radna mesta | pre rada na svakom | čl. 33 st. 5 | Zakon |
| **Periodična obuka — povećan rizik** | — | **najkasnije 1 godina** | čl. 34 st. 6 | Zakon |
| **Periodična obuka — ostala radna mesta** | — | **najkasnije 3 godine** | čl. 34 st. 6 | Zakon |
| Dodatna obuka posle teške, smrtne ili kolektivne povrede | povreda | **odmah, najkasnije 8 dana** | čl. 36 st. 2 | Zakon |
| Ponovna provera posle neuspeha | neuspeh | 15 dana | Pravilnik čl. 28 | potvrditi |
| Obuka za korišćenje LZO | izdavanje LZO | pri izdavanju | čl. 28 st. 2 | Zakon |
| Obuka predstavnika zaposlenih | izbor ili imenovanje | odmah; periodično **3 godine** | čl. 35 | Zakon |
| Pisano obaveštenje posebnih grupa o proceni rizika | trudnoća, porodilja, dojilja, < 18 god., invaliditet, profesionalna bolest | pri saznanju | čl. 36 st. 3 | Zakon |
| Upoznavanje lica u radnoj sredini sa opasnostima | posetioci, izvođači | pri dolasku | čl. 37 | Zakon |
| Osnovna obuka ZOP (4 časa, teorija i praktična provera) | stupanje na rad | **odmah, najkasnije 30 dana** | ZZOP čl. 53 st. 1; Program obuke ZOP čl. 5 | Zakon |
| Provera znanja ZOP | — | **jednom u 3 godine** | ZZOP čl. 53 st. 6 | Zakon |
| Posebna obuka i stručni ispit lica na poslovima ZOP | zasnivanje radnog odnosa ili raspoređivanje na poslove ZOP | **najkasnije 1 godina** | ZZOP čl. 55 | Zakon |
| Izmena Programa obuke ZOP | izmena programa | pre primene, uz saglasnost MUP-a | ZZOP čl. 53 st. 3 | Zakon |
| Prethodni lekarski pregled | prijem/raspored na povećan rizik; **noćni rad** | pre početka rada | čl. 56 st. 1–2 | Zakon |
| Periodični lekarski pregled | povećan rizik; noćni rad | po pravilniku ministara | čl. 56 st. 3 | potvrditi |
| Lekarski pregled na zahtev zaposlenog | zahtev | **najkasnije 5 godina** od prethodnog | čl. 56 st. 5 | Zakon |
| Premeštaj nesposobnog | ocena „ne ispunjava uslove" | bez odlaganja | čl. 56 st. 4 | Zakon |
| Stručni nalaz posle pregleda | pregled | **najkasnije 30 dana** od pregleda | čl. 15 st. 3 | Zakon |
| Zabrana rada na neispravnoj opremi | nalaz ili nalepnica o neispravnosti | **odmah**, do novog nalaza | čl. 15 st. 4 | Zakon |
| Preventivni i periodični pregled opreme za rad, el. i gromobranskih instalacija | pre upotrebe; periodično | 3 godine (privremena instalacija 1 god.) | čl. 15 st. 2; Pravilnik o pregledima | potvrditi |
| Preventivno i periodično ispitivanje radne sredine | početak procesa, rekonstrukcija; periodično | 6 meseci; 3 godine | čl. 15 st. 2; Pravilnik o pregledima | potvrditi |
| **Prijava smrtne, kolektivne, teške povrede i opasne pojave** (inspekcija rada i MUP) | događaj | **odmah, najkasnije 24 časa** | čl. 64 st. 1 | Zakon |
| **Prijava lake povrede** sa nesposobnošću > 3 dana (inspekcija rada) | događaj | **najkasnije 5 radnih dana** | čl. 64 st. 2 | Zakon |
| Prijava profesionalne bolesti | mišljenje zdravstvene ustanove | **5 dana** | čl. 64 st. 3 | Zakon |
| Izveštaj o povredi / profesionalnoj bolesti (zaposlenom, RFZO, Upravi; Registar) | događaj | po pravilniku o obrascu | čl. 65, 69 | potvrditi |
| Odgovor na zahtev zaposlenog (odbijanje rada) | pisani zahtev | **8 dana** | čl. 39 st. 3 | Zakon |
| Otklanjanje prijavljene nepravilnosti | obaveštenje zaposlenog | **8 dana** | čl. 42 st. 2 | Zakon |
| Obaveštenje inspekcije kada se odbijanje rada smatra neopravdanim | odbijanje | odmah | čl. 39 st. 4 | Zakon |
| Obaveštenje inspekcije kada se nastavi rad uprkos zabrani savetnika | nalog poslodavca | odmah | čl. 50 st. 4 | Zakon |
| Izveštaj inspekciji o radu odvojene jedinice ili promeni tehnološkog postupka | promena | **najmanje 8 dana pre** | čl. 20 | Zakon |
| Prijava gradilišta/radilišta sa elaboratom | početak radova | **najmanje 8 dana pre** | čl. 22 | Zakon |
| Prijava hitnih radova | hitni radovi | odmah | čl. 23 | Zakon |
| Sporazum o podeli radnog prostora | zajednički prostor | pre početka | čl. 24 | Zakon |
| Licenca savetnika i ovlašćenih firmi | — | 5 godina; zahtev za obnovu **60 dana pre isteka** | čl. 75 | Zakon |
| Kontinuirano usavršavanje savetnika | — | po pravilniku | čl. 53 | potvrditi |
| Izmena akta o proceni rizika | nova opasnost, novo radno mesto, nova tehnologija, promena radne sredine | bez odlaganja | čl. 16 st. 4 | Zakon |
| Odsustvo predstavnika zaposlenih | — | najmanje 5 časova mesečno | čl. 57 st. 5 | Zakon |
| Osiguranje zaposlenih od povreda | — | važenje polise | čl. 67 | Zakon |
| **Kontrola ispravnosti** PP aparata (mobilni uređaji), hidrantske mreže, dojave, gašenja, detekcije gasova, odvođenja dima — **ovlašćeno pravno lice** | — | **6 meseci** | ZZOP čl. 44 | Zakon |
| Održavanje istih instalacija i uređaja | — | po tehničkim propisima, standardima i uputstvu proizvođača | ZZOP čl. 43 | potvrditi |
| Ispitivanje aparata hladnim vodenim pritiskom (S 2 god., CO₂ 5 god.); panik-rasveta 3 meseca; interne kontrole dojave; dimnjaci i kotlarnica | — | kao u Pravilima ZOP čl. 11 | Pravila ZOP; tehnički propisi | potvrditi (SRPS Z.C2.035 za aparate) |
| Periodična kontrola ostalih ugrađenih instalacija (el. instalacije, gromobran…) | — | po tehničkim propisima | ZZOP čl. 40 st. 4; Pravilnik o pregledima | potvrditi |
| **Izmena Plana ZOP** sa saglasnošću MUP-a | urbanistička, tehničko-tehnološka ili druga promena (objekti, zakupci, broj lica, oprema, procesi) | bez odlaganja | ZZOP čl. 27 st. 4–5 | Zakon |
| Protivpožarna straža | vrući radovi van prilagođene prostorije; pretakanje > 5 m³; javni skup | za vreme rada | ZZOP čl. 51 | Zakon |
| Posebna obuka i stručni ispit lica u straži i dežurstvu | — | — | ZZOP čl. 24, 51 | potvrditi |
| Ormarić prve pomoći | — | kompletnost 3 meseca, rokovi godišnje; normativ po pravilniku ministara (čl. 18 st. 4) | Pravilnik čl. 55–56; Pravila ZOP | potvrditi |
| Revizija Akta LIP; Procene rizika od katastrofa | — | 3 godine (LIP); po zakonu | Akt LIP; Zakon o smanjenju rizika od katastrofa | potvrditi |
| Postupanje po rešenju inspekcije | rešenje | rok iz rešenja | Pravilnik čl. 7, 9 | — |

### 4.3 Protivrečnosti koje modul ne sme sam da reši

| # | Šta | Gde | Predlog |
|---|---|---|---|
| 1 | Ko bira Odbor | Pravilnik čl. 19 (direktor imenuje) / Zakon čl. 57 (zaposleni biraju) | Po Zakonu; menja Pravilnik |
| 2 | Periodična obuka | Program (samo povećan rizik) / Zakon čl. 34 (1 i 3 godine) | Po Zakonu |
| 3 | Rok obuke ZOP: 1 godina ili 30 dana | Pravila čl. 68 / Program čl. 5 | **Rešeno ZZOP čl. 53: najkasnije 30 dana** |
| 4 | Prag ZOP: 100% ili 70% | Pravila čl. 68 / Program čl. 15 | 70% |
| 5 | Komisija za proveru BZR | Pravilnik čl. 25 / Program čl. 26 | Usaglasiti oba sa čl. 34 st. 5 (provera na radnom mestu) |
| 6 | Kategorija ugroženosti III ili II | Pravila čl. 5 / rešenje 2016 | II — zakonski akt je Plan ZOP (ZZOP čl. 27), ne Pravila (čl. 28) |
| 8 | Kontrola dojave i hidranata | Pravila čl. 11 (2 meseca / 2× godišnje) / ZZOP čl. 44 (6 meseci, ovlašćeno lice) | Zakonski minimum 6 meseci od ovlašćenog lica; češće interne provere ostaju |
| 7 | Broj aparata, hidranata, dojava | Plan ZOP / Plan zaštite i spasavanja / Pravila | Fizički popis |

---

## 5. Arhitektura

### 5.1 Nova aplikacija `bzr`

```
bzr/
  models/          sifarnici.py, zaposleni.py, oprema.py, dogadjaji.py, zahtevi.py, akti.py, vanredne.py
  services/        rokovi.py (računa sve rokove), kadrovi.py (okidači), normativi.py, evidencije.py (čl. 62),
                   registar_povreda.py (podaci za unos), izvestaji.py, pdf.py (reportlab), uvoz.py
  views/           po celinama; preuzimanje fajlova samo kroz view sa proverom dozvole
  tasks.py         proveri_rokove, prati_kadrove, podsetnici
  access.py        obuhvat po registru (kao hr.access.visible_employees)
  templates/bzr/   ekrani, štampe (obrazac obučenih za potpis), _karton.html
```

Registracija aplikacije prati postojeći obrazac (8 mesta): `INSTALLED_APPS`, `ims_erp/urls.py`, `switch_app`,
`sidebar_map`, `templates/sidebar_bzr.html`, **pločica u `templates/header.html` koja već postoji kao „BZR — U
pripremi"**, početna strana (`core/pocetna.py`), sakupljanje dozvola u `core/permissions.py` i
`PRAVA_PO_REGISTRU["bzr"] = True`.

### 5.2 Kako se računaju rokovi

`bzr.services.rokovi` za svaku **vrstu obaveze** iz šifarnika vraća redove:
`predmet` (zaposleni / oprema / objekat / radno mesto / akt / događaj / zahtev), `poslednje izvršenje`,
`sledeći rok` (datum, a za prijave povreda **datum i vreme**), `status` (istekao, ističe u N dana, u redu, nema
podatka, nepotvrđen period), `izvor`, `veza` na zapis i dokaz.

- **Periodične obaveze:** sledeći rok = poslednje izvršenje + period; nalaz može propisati kraći rok.
- **Okidačke obaveze:** okidač + rok iz šifarnika; zatvara ih zapis o izvršenju.
- **Radni dani** (prijava lake povrede) računaju se bez vikenda i neradnih praznika — postoji
  `hr.services.praznici.neradni_praznici`.
- Ništa se ne upisuje unapred: promena perioda u šifarniku odmah menja sve rokove, a istorija ostaje.
- Isti servis puni ekran „Rokovi", kartone, početnu stranu i podsetnike (obrazac `fleet/support/fleet_snapshot.py`).

### 5.3 Okidači iz Kadrova i drugih modula

- `bzr.tasks.prati_kadrove` (noću, posle sinhronizacije zaposlenih) poredi `Employee` sa poslednjim snimkom
  (`RadnoMestoZaposlenog`: šifra i naziv radnog mesta iz sistematizacije, OJ, aktivan).
- **Novi zaposleni** → obuka pre rada (čl. 33), obuka ZOP (30 dana), prethodni lekarski ako je povećan rizik ili
  noćni rad (čl. 56), zaduženje LZO i obuka za LZO (čl. 28).
- **Promena radnog mesta** → obuka za novo mesto, lekarski ako novo mesto traži, razduženje i zaduženje LZO.
- **Novo radno mesto u sistematizaciji** bez procene rizika → obaveza „dopuniti akt o proceni rizika" (čl. 16 st. 4).
- **Nova oprema za rad** u registru → preventivni pregled pre upotrebe i obuka korisnika (čl. 33 t. 3).
- **Prestanak rada** → zatvaraju se otvorene obaveze, traži se razduženje LZO.
- **Flota** → zaposleni koji upravljaju službenim vozilima (zaduženja vozila, putni nalozi kao vozač) su na radnom
  mestu sa povećanim rizikom po čl. 4 t. 21 → lekarski i periodična obuka na 1 godinu (B-27).
- Angažovanja van radnog odnosa i zaposleni drugih poslodavaca pod našim nadzorom (čl. 33 st. 6) unose se ručno.

### 5.4 Fajlovi

- Posebna putanja na lokalnom serveru (`BZR_STORAGE_ROOT`), ne `/media/` (koji nije zaštićen).
- Preuzimanje samo kroz view sa proverom dozvole i obuhvata (obrazac `hr:ugovor_dokument`).
- SHA-256 i originalni naziv; ništa se ne briše.
- Kasnije (faza 4 plana arhive): nalazi, zapisnici i izveštaji dobijaju delovodni broj preko `{% arhiva_panel %}`.

### 5.5 Podsetnici

- **Na ekranu** od prvog dana: „Rokovi", početna strana modula, blok u Kadrovi → Pregled za rukovodioca,
  Moj profil za zaposlenog.
- **Prijave povreda** (24 h) prikazuju se kao hitne odmah po upisu događaja, sa brojačem preostalog vremena.
- **Imejl** kada se podesi (tačka 1.4/21): odmah za prijave povreda i zabrane rada; nedeljno savetniku za BZR;
  mesečno rukovodiocima. Status slanja kao `OpomenaGoriva` u Floti (za slanje / poslato / bez kontakta / greška).

---

## 6. Model podataka

### 6.1 Šifarnici

| Model | Ključna polja |
|---|---|
| `Objekat` | naziv (Upravna zgrada, Mala zgrada, Hala konstrukcije, Hala beton), adresa, etaže, površina, kategorija ugroženosti od požara, broj lica po planu, aktivan |
| `Prostorija` | objekat, sprat, broj i naziv (npr. arhiva 71, kotlarnica, trafostanica, PP komora, laboratorije), posebne opasnosti |
| `RadnoMesto` | šifra i naziv iz sistematizacije (`Sistemat`), **povećan rizik** (da/ne i osnov: visina, dubina, vozila i unutrašnji transport — čl. 4 t. 21 — ili akt o proceni rizika), opasnosti i štetnosti, posebni zdravstveni uslovi (čl. 17), period lekarskog, noćni rad, izvor (akt o proceni rizika, broj, datum) |
| `Opasnost` | naziv, grupa (mehaničke, električne, hemijske, fizičke, biološke, napori…) |
| `VrstaObaveze` | kod, naziv, domen (BZR / ZOP / CZ / LIP), predmet, okidač, period ili rok (meseci, dani, radni dani, časovi), **izvor (propis, član)**, **potvrđeno (ko, kada)**, aktivna |
| `Izvrsilac` | firma, vrsta ovlašćenja (pregledi opreme i instalacija; radna sredina; biološke štetnosti; medicina rada; **kontrola PP instalacija i uređaja — ovlašćenje MUP, ZZOP čl. 44**; **poslovi ZOP i dežurstvo — ZZOP čl. 25**; posebna obuka ZOP — čl. 56; TZ), broj licence ili ovlašćenja, važi do, odgovorno lice i njegova licenca, ugovor |
| `Uloga` | savetnik za BZR, saradnik za BZR, lice za ZOP, predstavnik zaposlenih, član Odbora (zaposlenih / poslodavca), poverenik CZ, zamenik, član kriznog tima, član tima, kurir, lice za prvu pomoć, lice sa ispitom ZOP, član komisije, ovlašćeno lice za Registar povreda, lice za koordinaciju |
| `VrstaLZO`, `NormativLZO` | vrsta (deo tela), standard; normativ: radno mesto, vrsta, količina, rok trajanja (faza 5) |

### 6.2 Zaposleni

| Model | Ključna polja |
|---|---|
| `RadnoMestoZaposlenog` | zaposleni, radno mesto, OJ, objekat rada, smena, noćni rad, od–do (snimak za okidače i istoriju) |
| `Imenovanje` | zaposleni, uloga, objekat, akt (broj, datum, fajl), način (imenovan / izabran), od–do, licenca (broj, važi do), stručni ispit (vrsta, broj uverenja, datum — za ZOP rok 1 godina od raspoređivanja) |
| `Obuka` | zaposleni ili treće lice, vrsta (bezbedan i zdrav rad / periodična / dodatna posle povrede / LZO / ZOP / prva pomoć / CZ / predstavnik zaposlenih / rukovodioci / treća lica), radno mesto, okidač, teorija (datum, ko), praksa (datum, nadzornik), **provera na radnom mestu** (datum, mesto, rezultat, ko je proverio), jezik, **potpisan obrazac** (skeniran, obavezan za zatvaranje), potvrda rukovodioca |
| `ObukaGrupna` | datum, vrsta, predavač (za ZOP broj uverenja MUP), spisak prisutnih, zapisnik — iz nje nastaju pojedinačne obuke |
| `LekarskiPregled` | zaposleni, vrsta (prethodni / periodični / kontrolni / ciljani / na zahtev / noćni rad), uput (datum, ko), ustanova, datum, **ocena** (ispunjava / ispunjava sa ograničenjem / ne ispunjava), ograničenje rečima ako ga daje medicina rada, sledeći rok, dokaz (posebna dozvola) |
| `ObavestenjePosebneGrupe` | zaposleni, osnov (bez detalja o zdravlju), datum uručenja pisanog obaveštenja (čl. 36 st. 3) |
| `ZaduzenjeLZO` | zaposleni, vrsta, količina, datum zaduženja, rok zamene, razduženje, potpisan revers (faza 5) |

### 6.3 Oprema i objekti

| Model | Ključna polja |
|---|---|
| `Oprema` | vrsta (oprema za rad / PP aparat / hidrant / panik-rasveta / dojava / gromobran / el. instalacija / sud pod pritiskom / trafostanica / ormarić prve pomoći / ventilacioni orman), naziv, tip, fabrički i inventarski broj, proizvođač, godina, objekat, prostorija, centar, **vozilo** (FK na Flotu), status, **isprava o usaglašenosti** i **uputstvo** (fajlovi, čl. 29), dodatna polja po vrsti |
| `Pregled` | predmet (oprema / instalacija / objekat), vrsta (preventivni / periodični / kontrolni / **kontrola ispravnosti po ZZOP čl. 44 — isprava o kontrolisanju** / servis / HVP), **datum pregleda**, **datum nalaza** (upozorenje ako > 30 dana, čl. 15 st. 3), izvršilac i odgovorno lice (licenca važeća na dan pregleda), broj nalaza, **zaključak** (primenjene / nisu primenjene mere), nalepnica o neispravnosti, nedostaci → mere, kraći sledeći rok, dokaz |
| `IspitivanjeRadneSredine` | objekat, prostorija ili radno mesto, merno mesto, štetnosti (mikroklima leto/zima, hemijske, fizičke, osvetljenost, biološke), u granicama (da/ne), izvršilac, datum ispitivanja, datum nalaza, nalaz |
| `OpasnaMaterija` | naziv, UN broj, klasa, karcinogena ili mutagena (da/ne), pakovanje, količina, prostorija, **bezbednosni list** (fajl, jezik), revizija |
| `Izlozenost` | zaposleni, štetnost (biološka grupa 3/4, karcinogeni, mutageni, hemijske materije, azbest), od–do — evidencije iz čl. 62 t. 4–5 (B-25) |

### 6.4 Događaji, zahtevi, mere, akti

| Model | Ključna polja |
|---|---|
| `Dogadjaj` | vrsta (povreda na radu / opasna pojava / profesionalna bolest / bolest u vezi sa radom / požar / havarija / vanredna situacija), datum i vreme, objekat ili teren, zaposleni, **težina** (laka / laka sa nesposobnošću > 3 dana / teška / smrtna / kolektivna), neposredni rukovodilac, očevidac, opis, prva pomoć, uzrok, analiza, mere; **prijave** (inspekcija rada, MUP — vreme, način, broj), **izveštaj o povredi** (zaposlenom, RFZO, Upravi — datum), **unos u Registar** (datum, ko); za vanredne situacije polja evidencionog kartona iz Procene rizika od katastrofa |
| `ZahtevZaposlenog` | zaposleni, vrsta (prijava nepravilnosti ili opasnosti — čl. 42; odbijanje rada — čl. 39), opis, prijem, **rok 8 dana**, odgovor i mere, obaveštenje savetnika i predstavnika zaposlenih, ishod (otklonjeno / neopravdano → inspekcija odmah) |
| `DozvolaZaRad` | vrsta rada (visina, dubina, skučeni prostor, Ex atmosfera, energetski objekat, opasne hemikalije, zona opasnosti, **vrući radovi — zavarivanje, rezanje, lemljenje, otvoreni plamen**), lokacija ili šifra posla, izvođači (zaposleni sa važećom obukom i lekarskim), mere, **protivpožarna straža** (lica i oprema — ZZOP čl. 51), od–do, izdao, zatvorena |
| `ZabranaRada` | zaposleni ili oprema ili prostorija, ko je izrekao, razlog (neposredna opasnost, neispravna oprema, bez LZO, alkohol…), od–do, **pisano obaveštenje poslodavcu i predstavniku zaposlenih** (čl. 50 st. 3), nalog za nastavak i obaveštenje inspekciji (st. 4) |
| `AlkoProvera` | nalog (rukovodilac), komisija, metoda, rezultat, osporavanje, zapisnik — **posebna dozvola** |
| `Mera` | izvor (rešenje inspekcije / stručni nalaz / analiza povrede / zahtev zaposlenog / akt o proceni rizika i program postupnog otklanjanja nedostataka — čl. 32 / Plan ZOP / Akt LIP / Komisija ZOP), opis, odgovorni, rok, status, dokaz, obaveštenje inspekciji |
| `Konsultacija` | tema (mera, organizovanje poslova BZR, akt, plan obuke — čl. 58), datum, ko je konsultovan (zaposleni, predstavnik, Odbor), mišljenje, dokaz |
| `Akt` | vrsta (Pravilnik o BZR, Program obuke, akt o proceni rizika, akt o proceni rizika za rad od kuće, Pravilnik o pregledima, Plan ZOP, Pravila ZOP, Program obuke ZOP, Plan zaštite i spasavanja, Procena rizika od katastrofa, Akt LIP, Plan TZ, postupak dozvole za rad, **sporazum o podeli prostora** sa licem za koordinaciju, **polisa osiguranja zaposlenih**, rešenje o kategoriji ugroženosti od požara, ugovor sa agencijom za dežurstvo…), okidači za izmenu (za Plan ZOP: promena objekata, zakupaca, broja lica, opreme, procesa), broj, datum, saglasnost (broj, datum), izrađivač i licenca, verzija, zamenjuje, rok revizije ili važenja, fajl, **poverljivo** |
| `Vezba` | vrsta (evakuacija / zemljotres / požar / prva pomoć), objekat, datum, broj učesnika, vreme evakuacije, nalaz, mere, zapisnik |
| `PotvrdaUpoznavanja` | zaposleni, akt ili uputstvo (plan evakuacije, uputstvo za bezbedan rad, Pravila ZOP), vreme — „upoznat sam" u aplikaciji (dopuna, ne zamena obaveznog potpisa iz 6.6) |

### 6.5 Veze sa postojećim modulima

| Modul | Veza |
|---|---|
| **Kadrovi** | `Employee` (radno mesto, OJ, prijem, aktivan); okidači 5.3; karton BZR u detalju zaposlenog i u Moj profil; podaci za izveštaj o povredi (čl. 63 st. 3) u trenutku izrade; `DodatnoRadnoMesto` iz ugovora (obuka za svako radno mesto, čl. 33 st. 5); 5 časova mesečno predstavniku zaposlenih (radna lista) |
| **Registar organizacije** | obuhvat (rukovodilac vidi svoje), centar opreme, OJ za dodatnu obuku posle povrede |
| **Flota** | vozači = povećan rizik po zakonu; oprema na vozilima; službeno vozilo za hitan prevoz povređenog; aparat u svakom vozilu |
| **Nabavka** | LZO, PP aparati, ugovori sa ovlašćenim firmama; predlog nabavke iz isteklih rokova i normativa |
| **Pravna (disciplinski postupci)** | kršenje mera, odbijanje alko-provere, neodazivanje na lekarski — veza iz `Dogadjaj` / `ZabranaRada` |
| **Ugovori** | ugovori sa ovlašćenim firmama i zakupcima (sporazum o podeli prostora) |
| **Finansije / šifre posla** | radilišta i dozvole za rad po šifri posla (teren, gradilišta) |
| **Arhiva** | kategorija „Akta lica za BZR"; delovodni broj za nalaze, zapisnike i izveštaje o povredi |
| **Mobilna telefonija** | službeni brojevi za liste uzbunjivanja |

### 6.6 Evidencije iz čl. 62 i gde su u modulu

| # | Evidencija (čl. 62 st. 1) | Model | Oblik |
|---|---|---|---|
| 1 | Radna mesta sa povećanim rizikom, zaposleni na njima i njihovi lekarski pregledi | `RadnoMesto`, `RadnoMestoZaposlenog`, `LekarskiPregled` | elektronski |
| 2 | Povrede na radu i profesionalne bolesti | `Dogadjaj` | elektronski |
| 3 | **Zaposleni obučeni za bezbedan i zdrav rad i pravilno korišćenje LZO** | `Obuka` + štampa obrasca za potpis + skenirani potpisan primerak | **ne samo elektronski** (st. 3): potpisan papir ili kopija tamo gde zaposleni radi (st. 2) |
| 4 | Zaposleni izloženi biološkim štetnostima grupe 3 i/ili 4 | `Izlozenost` | elektronski |
| 5 | Zaposleni izloženi karcinogenima, mutagenima, hemijskim materijama i azbestu | `Izlozenost`, `OpasnaMaterija` | elektronski |
| 6 | Izveštaj o primeni mera (samo delatnosti iz čl. 48) | `izvestaji.py` | po B-21 |
| 7 | Pregledi i provere opreme za rad, el. i gromobranskih instalacija | `Oprema`, `Pregled` | elektronski |
| 8 | Ispitivanja uslova radne sredine | `IspitivanjeRadneSredine` | elektronski |
| 9 | Izdata LZO | `ZaduzenjeLZO` | elektronski |

Način vođenja i **rokove čuvanja** propisuje ministar (čl. 62 st. 4) — tačka 1.1/5. Svaka evidencija ima izvoz
u Excel i štampu u obliku propisanog obrasca.

---

## 7. Ekrani

| Celina | Ekran | Ko |
|---|---|---|
| Početna | **Rokovi** (hitno: prijave povreda; istekli / 30 dana / bez podatka / nepotvrđeni periodi), brojke po domenu, zatečeno stanje (3.3) | Savetnik za BZR, Uprava |
| Zaposleni | **Karton BZR zaposlenog**: radno mesto i rizik, obuke i periodični rokovi, ZOP, prva pomoć, lekarski rokovi, LZO, uloge, događaji, zahtevi | Savetnik; rukovodilac za svoje; zaposleni svoj (Moj profil) |
| Zaposleni | Novi i premešteni bez obuke; spisak za periodičnu obuku (1 i 3 godine); spisak za lekarski (uput, Excel za medicinu rada) | Savetnik za BZR |
| Zaposleni | **Grupna obuka**: izbor zaposlenih, zapisnik, provera na radnom mestu, štampa obrasca za potpis, prilaganje potpisanog skena | Savetnik za BZR |
| Zaposleni | **Moj BZR** (Moj profil): moji rokovi, potvrda upoznavanja, **prijava nepravilnosti ili opasnosti** (rok 8 dana, status), zahtev za lekarski pregled (čl. 56 st. 5) | Svaki zaposleni |
| Radna mesta | Šifarnik radnih mesta: povećan rizik i osnov, opasnosti, posebni zdravstveni uslovi, noćni rad, normativ LZO | Savetnik za BZR |
| Oprema | Registar opreme po objektu i prostoriji; karton opreme; unos stručnog nalaza (rok 30 dana, nalepnica, automatska zabrana) | Savetnik; centri čitaju svoju |
| Oprema | PP oprema: aparati sa kontrolnim kartonom, hidranti, panik-rasveta; zapisnik servisa za više aparata odjednom | Lice za ZOP |
| Objekti | Objekti i prostorije; radna sredina; opasne materije i bezbednosni listovi; ormarići i lica za prvu pomoć po smeni i lokaciji | Savetnik za BZR |
| Događaji | Povrede, opasne pojave, profesionalne bolesti, požari — **rokovi prijava sa satom**, izveštaj o povredi, podaci za Registar, analiza i mere, dodatna obuka 8 dana | Savetnik; Odbor i predstavnik čitaju |
| Zahtevi i dozvole | Zahtevi zaposlenih (8 dana); dozvole za rad; zabrane rada sa obaveštenjima; alko-provere (posebna dozvola) | Savetnik, rukovodioci |
| Mere | Mere i rešenja inspekcije, program postupnog otklanjanja nedostataka (čl. 32), konsultacije (čl. 58) | Savetnik, Uprava |
| Akti | Registar akata sa rokom revizije, saglasnostima, sporazumima i polisama; poverljivi samo uz dozvolu | Savetnik, Uprava; predstavnik i Odbor uvid (čl. 58 st. 2) |
| Vanredne situacije | Imenovanja i timovi po objektu; vežbe; PD-3 (broj lica po objektu iz Kadrova, ranjive grupe samo kao broj); PD-4 oprema | Savetnik, poverenik |
| Evidencije | Svih 9 evidencija iz čl. 62 kao spiskovi sa Excelom i štampom obrasca | Savetnik |
| Izveštaji | Godišnji izveštaj ZOP; analiza povreda za Odbor; stanje obučenosti po centru; Excel i PDF (A4, zaglavlje) | Savetnik, Uprava |
| Šifarnici | Vrste obaveza sa periodom, izvorom i potvrdom; izvršioci i licence; uloge; LZO | Savetnik za BZR |

### 7.1 Dozvole

Kodovi su imena ruta (`bzr:...`). Predlog uloga:

| Uloga | Šta sme |
|---|---|
| `bzr-savetnik` | sve, osim poverljivih akata ako nije posebno dodeljeno |
| `bzr-rukovodilac` | karton i rokove svojih zaposlenih, dozvola za rad, zabrana rada, nalog za alko-proveru, zaduženje LZO, odgovor na zahtev zaposlenog |
| `bzr-odbor` | akti, evidencije o povredama i profesionalnim bolestima, mere inspekcije — samo čitanje (čl. 58–59) |
| `bzr-uprava` | čitanje svega i izveštaji |
| posebno | `bzr:alko`, `bzr:lekarski_dokaz` (fajlovi izveštaja medicine rada), `bzr:poverljivo` (Akt LIP, Plan TZ) |

Zaposleni vidi svoj karton i podnosi zahtev bez posebne dozvole (kao Moj profil). **Predlog: `bzr:alko` i
`bzr:lekarski_dokaz` Uprava ne dobija automatski** (B-12; čl. 55).

---

## 8. Zakazani poslovi

| Zadatak | Kada | Red | Šta radi |
|---|---|---|---|
| `bzr.tasks.prati_kadrove` | svaki dan 01:55 (posle sinhronizacije zaposlenih i organizacije) | default | Snimak radnog mesta; novi, premešteni, otišli; vozači iz Flote → okidačke obaveze |
| `bzr.tasks.proveri_rokove` | svaki dan 06:35 | default | Statusi rokova; istekle licence (i 60 dana pre isteka); nalazi kasne > 30 dana |
| `bzr.tasks.podsetnici` | ponedeljkom 07:15 (kada se podesi imejl); prijave povreda odmah | default | Pregled savetniku; rukovodiocima mesečno |

Svaki zadatak se upisuje u `EXPECTED_PERIODIC_TASKS`, posle isporuke se restartuje worker (AGENTS.md §7, §10).

---

## 9. Uvoz početnih podataka

| Šta | Odakle | Kako |
|---|---|---|
| 4 objekta i ključne prostorije | Plan ZOP, Plan zaštite i spasavanja | Ručno ili fixture; savetnik potvrđuje |
| Radna mesta | Sistematizacija (`Sistemat`, isto kao Kadrovi → Ugovori) | Komanda; povećan rizik po čl. 4 t. 21 predlaže sistem (vozači, dizalice), ostalo iz akta o proceni rizika |
| **Oprema za rad (191 stavka)** | [`bzr/oprema-za-rad-2019.xlsx`](bzr/oprema-za-rad-2019.xlsx) (centar, laboratorija, vrsta, fab./inv. broj, godina, lokacija, namena, vrsta pregleda, rok; kolone za proveru) | Centri označe šta postoji → uvoz; stavke na vozilima vezati za Flotu |
| PP oprema | Fizički popis (1.3/12); do tada zbirno po objektu iz Plana ZOP | Excel → uvoz |
| Opasne materije i boce | Plan ZOP (29 stavki, boce gasova); trihloretilen označiti kao karcinogen | Excel za proveru → uvoz |
| Akti | Ova fascikla | Ručno, sa fajlom; poverljivi označeni |
| Obučenost, ZOP obuka, lekarski, prva pomoć | Postojeće evidencije (1.2/7) | Excel → uvoz, sa datumom i izvorom „uvezeno"; potpisani obrasci se skeniraju |
| Imenovanja | Rešenja (1.1/3) | Ručno |

---

## 10. Testovi

| Oblast | Šta proveriti |
|---|---|
| Rokovi | Periodični rok = poslednje + period; kraći rok iz nalaza ima prednost; promena perioda menja rok, ne istoriju; nepotvrđen period ne šalje podsetnik |
| Zakonski rokovi | Teška povreda u 23:00 → rok prijave sledećeg dana u 23:00; laka povreda u petak → 5 radnih dana bez vikenda i praznika; periodična obuka 1 god. za povećan rizik i 3 god. za ostala; teška povreda otvara dodatnu obuku od 8 dana za radno mesto u toj OJ; stručni nalaz > 30 dana posle pregleda je upozorenje |
| Okidači | Novi zaposleni otvara obaveze; promena radnog mesta otvara obuku za novo mesto; vozač iz Flote dobija povećan rizik; novo radno mesto bez procene otvara meru; ponovno pokretanje ne pravi duplikate |
| Obuka | Obuka se ne zatvara bez potpisanog obrasca (čl. 62 st. 3); potvrda u aplikaciji ga ne zamenjuje |
| Oprema | Nalaz „nisu primenjene mere" automatski zabranjuje rad na opremi do novog pozitivnog nalaza; nalaz firme sa isteklom licencom se ne prihvata; kontrola aparata i hidranata od firme bez ovlašćenja MUP-a ne zatvara rok od 6 meseci |
| ZOP | Novi zaposleni bez osnovne obuke ZOP posle 30 dana je istekao; vrući radovi van prilagođene prostorije ne mogu se odobriti bez protivpožarne straže |
| Zahtevi | Prijava nepravilnosti ima rok 8 dana; odbijanje rada ocenjeno kao neopravdano otvara obavezu „odmah obavestiti inspekciju" |
| Lekarski | Ne postoji polje za dijagnozu; dokaz samo uz `bzr:lekarski_dokaz`; „ne ispunjava" → upozorenje i obaveza premeštaja |
| Normativi | Prva pomoć dostupna u svakoj smeni i na svakoj lokaciji; ormarići po pravilniku |
| Pristup | Rukovodilac vidi samo svoje; Odbor samo čita propisane evidencije; poverljivi akti i alko-provere samo uz posebnu dozvolu; preuzimanje bez dozvole → 403 |
| Postojeći moduli | Testovi `hr`, `fleet`, `pravna` i dalje prolaze (`--settings=ims_erp.settings.testing`) |

---

## 11. Faze implementacije

| Faza | Sadržaj | Zavisi od | Rezultat |
|---|---|---|---|
| **0 — Dogovor i dokumenti** | Stavke iz 1.1; potvrda perioda (4.2), protivrečnosti (4.3) i podzakonskih akata; usklađivanje Pravilnika o BZR i Programa sa Zakonom (posao savetnika, čl. 50 t. 17) | — | Važeći akt o proceni rizika, potvrđeni periodi, imenovan savetnik sa licencom |
| **1 — Osnova i rokovi** | Aplikacija `bzr`, registracija (5.1), objekti i prostorije, radna mesta iz sistematizacije, vrste obaveza, izvršioci i licence, imenovanja, **registar akata sa rokovima** (uključujući sporazume i polisu), servis rokova, ekran „Rokovi" sa zatečenim stanjem, dozvole i obuhvat | 1.1 | Uprava vidi šta je isteklo i šta Zakon traži |
| **2 — Zaposleni** | Okidači iz Kadrova i Flote, obuke (početna, periodična 1/3 god., dodatna, LZO, ZOP, prva pomoć, predstavnik, rukovodioci) sa obrascem za potpis, lekarski pregledi, posebne grupe, karton zaposlenog, Moj BZR, evidencije 1 i 3 | 1, 1.2 | Svaki zaposleni ima rok obuke i lekarskog |
| **3 — Oprema i objekti** | Uvoz 191 stavke opreme za rad, PP oprema, instalacije, stručni nalazi (30 dana, nalepnica, zabrana), radna sredina, opasne materije i izloženost, prva pomoć po smeni i lokaciji; evidencije 4, 5, 7, 8 | 1, 1.3 | Svaki aparat i mašina ima rok i nalaz |
| **4 — Događaji, zahtevi, mere** | Povrede i opasne pojave sa rokovima prijava (24 h / 5 radnih dana), izveštaj o povredi i podaci za Registar, profesionalne bolesti; zahtevi zaposlenih (8 dana); dozvole za rad; zabrane rada; alko-provera; mere, rešenja inspekcije, konsultacije; evidencija 2; veza sa disciplinskim postupcima | 2, 1.4/16–19 | Povreda ima ceo tok u zakonskim rokovima |
| **5 — LZO** | Normativ po radnom mestu, zaduženje i razduženje sa potpisanim reversom, obuka za LZO, rokovi zamene, predlog nabavke; evidencija 9 | 2, 1.1/2 | Svaki zaposleni ima zaduženu LZO po normativu |
| **6 — Vanredne situacije i ZOP organizacija** | Timovi i poverenici po objektu, vežbe evakuacije, PD-3/PD-4 iz podataka, dežurstvo, godišnji izveštaj ZOP, Komisija ZOP | 1, 3, 1.4/20 | Planovi se ažuriraju iz podataka |
| **7 — Podsetnici i izveštaji** | Imejl podsetnici, PDF izveštaji (A4), analiza povreda za Odbor, stanje obučenosti po centru, izveštaj o primeni mera (ako je delatnost iz čl. 48) | 1–4, 1.4/21 | Rokovi stižu sami |
| **8 — Opciono** | Radilišta i gradilišta sa prijavom 8 dana pre početka (po šifri posla); elektronska provera znanja (test u aplikaciji — teorijski deo; praktični ostaje na radnom mestu); rad od kuće i na daljinu (čl. 44–45); registar rizika LIP; knjiga ključeva i posetilaca | po odluci | — |

**Okvirni redosled:** faze 0 i 1 odmah (vidi se zatečeno stanje i neusklađenost sa Zakonom); 2 i 3 uporedo;
4 čim se odredi lice za Registar i postupak dozvole za rad; 5–8 po potrebi.

---

## 12. Rizici

| Rizik | Mera |
|---|---|
| Nema važećeg akta o proceni rizika na radnim mestima | Faze 1 i 3 ne zavise od njega; povećan rizik po čl. 4 t. 21 (visina, dubina, vozila, dizalice) zna se iz Zakona |
| Podzakonski akti po novom Zakonu nisu potvrđeni | Period sa izvorom i potvrdom; stari se primenjuju dok se ne zamene (čl. 108 st. 2) |
| Početno stanje nepotpuno, pa sve izgleda isteklo | „Nema podatka" odvojeno od „isteklo"; uvoz postojećih evidencija pre puštanja upozorenja |
| Evidencija obučenih mora imati papirni potpis | Štampa obrasca iz aplikacije, skeniranje potpisanog; obuka se ne zatvara bez njega |
| Prijava povrede se propusti van radnog vremena | Hitan prikaz i imejl odmah; zamenik savetnika u imenovanjima |
| Zdravstveni podaci i alko-provere | Bez dijagnoze; posebne dozvole; dnevnik pregleda (čl. 55) |
| Savetnik je jedna osoba za sve domene | Zamenik; rokovi vidljivi i Upravi |
| Kadrovski podaci o radnom mestu kasne ili su netačni | Okidač je predlog: savetnik potvrđuje ili ispravlja; istorija snimaka |
| Poverljivi dokumenti (Akt LIP, Plan TZ) | Posebna dozvola, bez sadržaja u pretrazi i izveštajima |
| Imejl nije podešen | Rokovi su od prvog dana na ekranu; imejl je dodatak |

---

## 13. Otvorena pitanja

| # | Pitanje | Zašto je važno | Pre faze |
|---|---|---|---|
| B-1 | Gde je važeći **akt o proceni rizika na radnim mestima** i da li je menjan po čl. 16 st. 4 (nova radna mesta, nova oprema, promena uslova)? | Radna mesta sa povećanim rizikom, lekarski, LZO, obuka | 1 |
| B-2 | Postoji li normativ **LZO** po radnom mestu? | Faza 5 | 5 |
| B-3 | Ko je danas **savetnik ili saradnik za BZR** (akt o imenovanju, licenca i rok)? Predstavnik zaposlenih, Odbor (izabran ili imenovan), lice za ZOP, poverenik CZ, krizni tim, lica za prvu pomoć? | Imenovanja, dozvole, rok licence | 1 |
| B-4 | Periodi koje ZZOP ne daje (ispitivanje aparata hladnim vodenim pritiskom, panik-rasveta, interne kontrole dojave) po važećim pravilnicima i SRPS Z.C2.035; kontrola na 6 meseci je zakonska (ZZOP čl. 44) | Rokovi PP opreme | 3 |
| B-5 | U kom objektu (i smeni) radi koji zaposleni? Kako se vodi teren? | Prva pomoć u svim smenama i lokacijama (čl. 18 st. 2), evakuacija | 2 |
| B-6 | Ko vrši proveru obučenosti na radnom mestu i koji je prag? | Usklađivanje Pravilnika i Programa | 2 |
| B-7 | ~~Da li je elektronska potvrda dovoljna za evidenciju obučenih?~~ **Zatvoreno Zakonom (čl. 62 st. 3): nije** — obrazac se štampa i potpisuje, sken je dokaz. Ostaje: da li je elektronska potvrda dovoljna za revers LZO? | Revers LZO | 5 |
| B-8 | Aktuelni popis opreme za rad i ko ga održava | Uvoz i održavanje registra | 3 |
| B-9 | Broj aparata, hidranata, panik-svetala; postoji li automatska dojava požara? | Registar i periodi | 3 |
| B-10 | Ugovori i licence ovlašćenih firmi | Važenje nalaza | 3 |
| B-11 | Ko unosi povrede, ko potpisuje izveštaj o povredi i kako se obezbeđuje prijava za 24 h van radnog vremena? | Faza 4 | 4 |
| B-12 | Ko sme da vidi izveštaje medicine rada i alko-provere; da li ih Uprava dobija automatski? | Čl. 55, zaštita podataka | 2, 4 |
| B-13 | Da li se i koliko često izvode vežbe evakuacije? | Nijedan akt ne propisuje | 6 |
| B-14 | Kako je rešeno **stalno dežurstvo** za II kategoriju (ZZOP čl. 24 st. 2)? Da li ga i dalje obavlja agencija (vatrogasci-čuvari) i da li ona ima **ovlašćenje MUP-a** (čl. 25)? | Zakonska obaveza; kazna do 1.000.000 dinara | 1 |
| B-15 | Imejl server i adresa za podsetnike | Faza 7 | 7 |
| B-16 | Da li se već rade revizija Akta LIP, Plana ZOP i usklađivanje Pravilnika o BZR i Programa sa novim Zakonom? | Zatečeno stanje | 1 |
| B-17 | Da li zakupci ulaze u obuke, evakuaciju i brojanje lica? | Normativi, PD-3 | 6 |
| B-18 | Rokovi čuvanja evidencija (čl. 62 st. 4 — propisuje ministar) | Čuvanje dokaza, Lista kategorija arhive | 2 |
| B-19 | Da li i dalje postoje kotlarnica na čvrsto gorivo, lakirnica, stolarska radionica, ambulanta, stambeni prostor u Maloj zgradi? | Opasnosti i prostorije | 3 |
| B-20 | Da li modul vodi i tehničku zaštitu i zaštitu lica i imovine ili samo akte sa rokom? | Obim faze 8 | 8 |
| B-21 | Da li je delatnost Instituta (laboratorijska ispitivanja, nadzor i terenski rad na gradilištima, geotehnička bušenja) u **čl. 48** (građevinarstvo i slično → savetnik, za 251–500 zaposlenih **najmanje dva** sa punim radnim vremenom) ili **čl. 49** (saradnik)? | Broj i kvalifikacija lica za BZR; izveštaj o primeni mera (evidencija 6) | 1 |
| B-22 | Postupak izdavanja **dozvole za rad** (čl. 27): ko izdaje, za koje radove (visina, dubina, hemikalije, energetski objekti, teren)? | Faza 4 | 4 |
| B-23 | Postoje li pisani **sporazumi o podeli radnog prostora** sa zakupcima i ko je lice za koordinaciju (čl. 24)? | Obaveza pre početka zajedničkog rada | 1 |
| B-24 | Ko radi **noću** (obezbeđenje je eksterno; terenski rad, dežurstva)? | Prethodni i periodični lekarski (čl. 56 st. 2) | 2 |
| B-25 | Da li su zaposleni **izloženi karcinogenima** (npr. trihloretilen u laboratoriji za asfalt), biološkim štetnostima grupe 3/4 ili azbestu? | Evidencije iz čl. 62 t. 4–5 | 3 |
| B-26 | Ko je **ovlašćeno službeno lice za Registar povreda** i da li je prijavljeno Upravi (čl. 69 st. 4)? | Unos povreda | 4 |
| B-27 | Da li se svi vozači službenih vozila vode kao radno mesto sa povećanim rizikom (čl. 4 t. 21) i kako ih prepoznati iz Flote (zaduženja, putni nalozi)? | Lekarski i obuka na 1 godinu | 2 |
| B-28 | Koji su **podzakonski akti** doneti po Zakonu 35/2023 (evidencije i rokovi čuvanja, pregledi opreme i radne sredine, lekarski pregledi, prva pomoć, obrazac izveštaja o povredi, procena rizika) i šta menjaju? | Periodi koji nisu u Zakonu | 1 |
| B-29 | Da li je **Plan ZOP** posle 2018. menjan i ima li **saglasnost MUP-a** (na plan i izmene, ZZOP čl. 27 st. 5)? Da li je ugrađena dojava u Upravnoj zgradi i ko vrši kontrolu na 6 meseci (ovlašćenje MUP-a)? | Glavni akt ZOP; rokovi kontrola | 1 |
| B-30 | Ko su lica na poslovima ZOP i da li imaju posebnu obuku i stručni ispit (ZZOP čl. 52, 55); da li osnovnu obuku izvodi Institut ili ovlašćena firma (čl. 53 st. 2)? | Imenovanja i ko potpisuje obuku | 2 |

---

## Izvori

**Zakon:** Zakon o bezbednosti i zdravlju na radu („Sl. glasnik RS", br. 35/2023), tekst sa
<https://www.paragraf.rs/propisi/zakon_o_bezbednosti_i_zdravlju_na_radu.html>, pročitan 05.10.2026. Korišćeni
članovi: 4, 15–18, 20–30, 32–42, 44–50, 53–59, 62–69, 75, 108, 111, kaznene odredbe.

Zakon o zaštiti od požara („Sl. glasnik RS", br. 111/2009, 20/2015, 87/2018 i 87/2018 — dr. zakoni), tekst sa
<https://www.paragraf.rs/propisi/zakon_o_zastiti_od_pozara.html>, pročitan 05.10.2026. Korišćeni članovi: 23–25,
27–28, 37, 40–44, 48, 51–55, 73, 77–79, 82, 86. Čl. 58–72 prestali su da važe 21.11.2018. (prešli u Zakon o
smanjenju rizika od katastrofa i Zakon o dobrovoljnom vatrogastvu).

**Fascikla `BZR` (C:\Users\rajom\Desktop\BZR):**

- `PRAVILNIK O BZR-2023, MART.pdf` — skeniran; pročitan rekonstrukcijom teksta
- `Program osposobljavanja za bezbedan i zdrav rad 14.11.2019.doc`
- `Pravilnik  opr ras gei novembar 2019.doc` (prilog sa 191 stavkom opreme izvučen u
  `dokumentacija/bzr/oprema-za-rad-2019.xlsx`)
- `Plan zastite od pozara iz 2018.pdf` (222 strane; skenirani prilozi bez teksta)
- `Pravila zastite od pozara 08.06.2012.docx` (kopija „(1)" je identična) i `Aneks 1 17.11.2016.docx`
- `Program obuke ZOP 27.04.2018.pdf` — skeniran; pročitan sa slika
- `Plan zastite i spasavanja.pdf`, `Procena rizika od katastrofa iz 2020.pdf`
- `Akt o proceni ruizika u zastiti lica, imovine i poslovanja, novembar 2021.pdf`, `Plan sistema tehnicke zastite mart 2022.docx` — poslovna tajna, opisani uopšteno

**Aplikacija:** `hr/models.py` (Employee), `hr/sync.py`, `hr/services/ugovori.py` (sistematizacija),
`hr/ugovori_models.py` (`DodatnoRadnoMesto`), `hr/services/praznici.py`, `fleet/support/fleet_snapshot.py`
(rokovi), `fleet/opomene_models.py` (imejl sa statusom), `pravna/models.py` (disciplinski postupci),
`templates/header.html` (pločica „BZR — U pripremi"), `dokumentacija/plan-arhive-overe-i-cuvanja.md`.

**Propisi koje treba proveriti u važećoj verziji:** podzakonski akti po Zakonu o BZR 35/2023 (B-28); pravilnici
po ZZOP (minimum sadržaja programa osnovne obuke, kontrola instalacija i uređaja i isprava o kontrolisanju,
broj stručno osposobljenih lica za dežurstvo, aparati, hidrantska mreža, dojava); Zakon o
smanjenju rizika od katastrofa i upravljanju vanrednim situacijama (87/2018); Zakon o privatnom obezbeđenju i
Pravilnik o tehničkoj zaštiti (91/2019).
