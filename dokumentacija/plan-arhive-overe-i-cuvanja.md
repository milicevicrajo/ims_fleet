# Plan implementacije modula „Arhiva" — kancelarijsko i arhivsko poslovanje, elektronska overa i čuvanje

Datum: 01.10.2026. Dopunjeno 05.10.2026. internim pravilnikom o arhivskom poslovanju (odeljak 4.5).
Status: **predlog za dogovor** — faza 1 (šifarnik i delovodnik) je urađena, ostalo nije.
Za koga: Uprava i kadrovska/arhivska služba (odluke u odeljcima 0, 1, 3, 5 i 14), programeri (odeljci 6–13).

Ovaj dokument spaja i zamenjuje dva radna plana iz foldera `aRhiva-docs`:

- „Plan implementacije modula Arhiva" od 23.09.2026, koji pokriva pisarnicu, delovodnik, arhivu i izlučivanje;
- „Elektronska overa i pouzdano elektronsko čuvanje" od 01.10.2026.

| Izvor | Šta iz njega uzimamo |
|---|---|
| `IU 03 Kancelarijsko i arhivsko poslovanje i2.doc` | Postupak pisarnice i evidencione knjige (Prilozi 1–5) |
| **Pravilnik o načinu evidentiranja, klasifikovanja, arhiviranja i čuvanja arhivske građe i dokumentarnog materijala** (br. 20-16153 od 07.12.2021, prečišćen tekst sa izmenom od 24.02.2023) | **Važeći interni akt** — pravila pisarnice, delovodnika, arhive, izlučivanja i predaje (odeljak 4.5). Zamenio je Pravilnik o kancelarijskom i arhivskom poslovanju iz decembra 2005, na koji se IU 03 još poziva. |
| `Lista-kategorija 10.03.2023.doc` (+ overeni PDF) | 454 kategorije sa klasifikacionom oznakom i rokom čuvanja — šifarnik modula |
| `Delovodnik 2024.xlsx` | 15.056 upisa, 27 kolona — **primer** kako se delovodnik stvarno vodi (nije izvoz iz programa; programa za delovodnik nema) |
| Mejl o toku (Olivera) | Ceo tok u 14 koraka i 3 segmenta — okvir plana |
| Propisi (odeljak 3) | Zahtevi za elektronsku overu, formate, metapodatke i čuvanje |
| Kod aplikacije | Dokumenti koji već postoje i koje arhiva **linkuje** (odeljak 8) |

---

## 0. Ukratko

**Cilj:** jedan modul pokriva ceo životni vek akta, od prijema u pisarnici do izlučivanja ili predaje nadležnom
arhivu. Dokumenti se mogu **elektronski overiti, i to masovno**, i čuvati tako da zadrže dokaznu snagu tokom celog
roka čuvanja.

```
SEGMENT A — Tekuće poslovanje      1. Pisarnica → 2. Delovodnik → 3. Moji predmeti → 4. Završetak predmeta
SEGMENT B — Prelazak u arhivu      5. Predaja arhivi → 6. Prijem → 7. Arhivske jedinice → 8. Arhivska knjiga → 9. Lokacija
SEGMENT C — Praćenje i izlučivanje 10. Reversi → 11. Rokovi → 12. Izlučivanje → 13. Predaja nadležnom arhivu → 14. Izveštaji
KROZ SVE — Elektronski dokument    priprema (PDF/A) → overa pečatom → vremenski žig → PAdES-B-LTA → obnova → čuvanje
```

**Ključne odluke koje predlažemo:**

1. **Delovodni broj daje samo arhiva, na postojeći način** (odluka 05.10.2026.): jedan niz osnovnih brojeva za
   ceo Institut po godini, uz oznaku OJ (`43-15238`, podbroj `43-15238/2`). Brojač zahteva u Kadrovima prelazi na arhivu.
2. **Masovnu overu radi server, kvalifikovanim elektronskim pečatom Instituta.** Pečat je kod kvalifikovanog pružaoca
   (udaljeni pečat) ili na kvalifikovanom tokenu u našem serveru, što se odlučuje posle ponuda. Akti koji po zakonu
   traže lični potpis direktora potpisuju se **udaljenim kvalifikovanim potpisom**, jednim odobrenjem za ceo paket.
   Kartice po računarima se ne koriste.
3. **Svaki overen dokument je PDF/A sa PAdES-B-LTA potpisom i kvalifikovanim vremenskim žigom.** Aplikacija sama
   obnavlja žig pre isteka.
4. **Sve se čuva na lokalnom Windows serveru Instituta** (odluka 05.10.2026.): skenovi, overeni dokumenti i dnevnik,
   po Pravilniku o pouzdanom elektronskom čuvanju. **Kvalifikovani pružalac usluge čuvanja se ne koristi.** Zato
   **papirni original uvek ostaje u arhivi** i ne uništava se posle digitalizacije (ZEDEIUP čl. 63 st. 4, interni
   pravilnik čl. 48 st. 3). Pečat i vremenski žig i dalje daje kvalifikovani pružalac — to je usluga overe, ne čuvanja.
   Spoljna (van zgrade) rezervna kopija je otvoreno pitanje (O-25).
5. **Elektronski delovodnik od 01.01.2027.** Program za delovodnik danas ne postoji, pa se ništa ne zamenjuje
   niti uvozi; dotadašnji način vođenja traje do 31.12.2026, a pre toga traje probni rad.
6. **Kancelarijsko i arhivsko poslovanje vodi se elektronski, kroz aplikaciju, uz elektronski potpis i pečat.**
   Papir ostaje samo tamo gde ga traži zakon ili gde akt stiže na papiru. **Gde se interni pravilnik ne slaže sa
   elektronskim radom, menja se pravilnik**, a ne sistem (predlog izmena u odeljku 4.6).

Šta treba pribaviti i odlučiti pre početka i pre svake faze dato je u odeljku 1.

---

## 1. Pre početka: šta pribaviti i šta odlučiti

### 1.1 Kako čitati ovaj odeljak

Implementacija **ne čeka da sve bude rešeno**. Svaka faza traži samo deo odluka i dokumenata. Ono što nije potrebno
za tekuću fazu ne sme da je zaustavi. Zato su stavke grupisane po tome **pre koje faze** moraju biti spremne.

- **Vrsta** kaže šta se traži: *odluka* (neko mora da odluči i to zapiše), *dokument* (treba ga pribaviti ili
  pripremiti), *nabavka* (ugovor sa spoljnim pružaocem) ili *tehničko* (posao IT-a).
- **Ko** je predlog nosioca. Konačno zaduženje određuje Uprava.
- **Rok** je izveden iz datuma prelaska **01.01.2027**. Faze 1 i 2 i probni rad moraju da stanu u oktobar–decembar,
  pa su stavke za fazu 1 najhitnije.
- Oznake O-1 … O-25 su pitanja iz odeljka 14. Tamo je objašnjeno zašto je svako važno.

Kod može da počne odmah, bez ijedne odluke, sa delom koji od odluka ne zavisi: kostur aplikacije, šifarnik
kategorija sa uvozom i izveštajem o spornim stavkama, i brojač sa formatom iz podešavanja.

### 1.2 Odmah — pre faze 1 (pisarnica i delovodnik)

| # | Stavka | Vrsta | Ko | Rok | Zašto baš sada |
|---|---|---|---|---|---|
| 1 | ~~Format delovodnog broja~~ (O-1) — **odlučeno 05.10.2026.: ide postojeći način brojanja.** Jedan niz osnovnih brojeva za ceo Institut po godini, uz oznaku OJ (`43-15238`, podbroj `43-15238/2`); nema posebnog niza po OJ. To je podrazumevani format u aplikaciji. | odluka | — | ✔ | — |
| 2 | ~~Zamena sadašnjeg programa~~ (O-2) — **zatvoreno 05.10.2026.: programa za delovodnik nema**, `Delovodnik 2024.xlsx` je bio samo primer. Ništa se ne zamenjuje i ne uvozi; elektronski delovodnik počinje 01.01.2027. od broja 1. | odluka | — | ✔ | — |
| 3 | **Ko radi u modulu:** pisarnica, arhivista, administrator modula (imena) | odluka | Arhivska služba | 15.10.2026. | Uloge i dozvole se dodeljuju imenovanim ljudima |
| 4 | ~~Pravilnik o kancelarijskom i arhivskom poslovanju Instituta~~ (O-3) — **pribavljen 05.10.2026.** Važi pravilnik iz 2023 (odeljak 4.5); verzija iz 2005 je zamenjena. | dokument | — | ✔ | IU 03 treba uskladiti sa pravilnikom iz 2023 (tačka 12) |
| 4a | **Odluke iz pravilnika koje utiču na fazu 1** (O-20 popis akata, O-21 poverljivi delovodnik, dopuna O-1) | odluka | Uprava, arhivska služba | 15.10.2026. | Određuju vrste knjiga i ko dobija delovodni broj |
| 5 | **Očišćena Lista kategorija** u Excelu (O-7): duplikati, rok za račune (10 ili 5 godina), oznaka 426, događaj od kog teče rok, oznaka „trajno" | dokument | Arhivista | 31.10.2026. | Uvozi se u šifarnik u fazi 1. Aplikacija daje spisak spornih stavki, pa ne mora da se čisti ceo dokument. |
| 6 | **Skladište na lokalnom Windows serveru** za skenove i dokumente (posebna fascikla, van `/media/`), sa rezervnom kopijom na **drugom disku ili uređaju** u Institutu; spoljna kopija kasnije (O-25) | tehničko | IT | 31.10.2026. | Pisarnica skenira od prvog dana probnog rada |
| 7 | ~~Izvozi delovodnika za 2025. i 2026.~~ — **nisu potrebni** (O-2): nema programa iz kog bi se izvozilo, a nova godina 2027. počinje novim nizom. Za probni rad pisarnica upisuje deo pošte i u aplikaciju, uporedo sa sadašnjim načinom vođenja. | — | — | ✔ | — |

### 1.3 Do kraja godine — pre faze 2 (tok predmeta) i pre prelaska

| # | Stavka | Vrsta | Ko | Rok | Zašto |
|---|---|---|---|---|---|
| 8 | **Elektronska potvrda prijema** umesto potpisa u dostavnoj knjizi (O-4) | odluka | Uprava, arhivska služba | 31.10.2026. | Od toga zavisi da li papirna dostavna knjiga prestaje. Dostavna knjiga je i ISO 9001 zapis. |
| 9 | **Faks** (O-5): koristi li se još | odluka | Arhivska služba | 31.10.2026. | Ako ne, knjiga faks poruka se izostavlja |
| 10 | **Pravilo za početak roka čuvanja** (O-6), uz pisanu potvrdu | odluka | Uprava, arhivista | 15.11.2026. | To je formula. Iz nje se računa datum izlučivanja. |
| 11 | **Brisanje zapisa zavedenih u delovodnik** u drugim modulima (O-11): samo zabeleška ili zabrana | odluka | Uprava | 30.11.2026. | Zabrana menja ponašanje drugih modula |
| 12 | **Obuka i izmena IU 03** (novi prilozi su ekrani i štampe iz sistema; poziv na pravilnik iz 2023 umesto 2005) | dokument | Arhivska služba | 20.12.2026. | Uslov za prelazak 01.01.2027. |
| 12a | **Izmena internog pravilnika, korak 1 — elektronski delovodnik i tok predmeta** (odeljak 4.6, tabela A): el. evidencije, el. potvrda prijema, el. pošta bez štampe, el. štambilj, razvod i rokovnik u aplikaciji, ispravke nedoslednosti | dokument | Pravna služba, arhivska služba; donosi generalni direktor | nacrt 15.11.2026, doneto 20.12.2026. | Stupa na snagu pre prelaska 01.01.2027 (8. dan od objave na oglasnoj tabli, kao izmena iz 2023) |

### 1.4 Pokrenuti sada, potrebno pre elektronske overe (faze 3 i 4)

Nabavka i pravila traju, pa ove stavke treba pokrenuti odmah, iako se overa razvija tek posle delovodnika.

| # | Stavka | Vrsta | Ko | Rok | Zašto |
|---|---|---|---|---|---|
| 13 | **Zahtev za ponudu:** kvalifikovani elektronski pečat Instituta (udaljeni ili na tokenu za server) i kvalifikovani vremenski žig, uz **testni nalog** | nabavka | Nabavka, IT | ponude 31.10.2026, ugovor 30.11.2026. | Bez testnog naloga potpisni servis ne može da se razvija. Bez ugovora nema overe. |
| 14 | **Budžet** za pečat i žig, po komadu ili paušalno (O-18) | odluka | Uprava | uz ponude | Odlučuje između udaljenog pečata i tokena |
| 15 | **Odluka o ovlašćenim licima** za overu istovetnosti i za korišćenje pečata | odluka | Direktor | 30.11.2026. | Zakon traži ovlašćeno lice (ZEDEIUP čl. 11) |
| 16 | **Koji akti traže lični potpis direktora**, a gde je dovoljan pečat (O-15) | odluka | Pravna služba | 30.11.2026. | Određuje da li treba i udaljeni lični potpis |
| 17 | **Interna pravila za pouzdano elektronsko čuvanje** (dopuna IU 03) i **procena rizika** | dokument | Arhivska služba, IT, pravna služba | 31.12.2026. | Pravilnik čl. 2 i 8. Mora postojati pre prvog overenog dokumenta. |
| 17a | **Pravilnik o načinu evidentiranja, zaštite i korišćenja elektronskih dokumenata Instituta** (O-23) — interni pravilnik čl. 3 se poziva na njega | dokument | Arhivska služba, pravna služba | 31.10.2026. | Možda već pokriva deo tačke 17. Pre faza 3–5 treba ga pročitati i uskladiti. |
| 17b | **Izmena internog pravilnika, korak 2 — elektronski potpis, pečat, overa i čuvanje** (odeljak 4.6, tabela B), zajedno sa tačkama 15, 17 i 17a | dokument | Pravna služba, arhivska služba, IT; donosi generalni direktor | 31.01.2027. | Pre prvog overenog dokumenta (faza 4) |
| 18 | **Vođenje sistema za čuvanje po pravilima ISO/IEC 27001** (O-12), bez obaveznog sertifikata | odluka | Uprava, IT | 31.12.2026. | **Obavezno**, jer se sve čuva na lokalnom serveru (Pravilnik čl. 8); pružalac kao zamena ne postoji |
| 19 | **Preduslovi u aplikaciji** (odeljak 11): `DEBUG`, zaštita `/media/`, lozinke van repozitorijuma, probno vraćanje iz kopije | tehničko | IT | pre faze 4 | Pre prvog dokumenta sa pravnom snagom |
| 20 | **SEF e-fakture** (O-16): arhiviramo ih sami ili se oslanjamo na SEF | odluka | Finansije | 31.01.2027. | Potrebno za povezivanje SEF faktura |

### 1.5 Tokom 2027.

| # | Stavka | Vrsta | Ko | Rok | Pre faze |
|---|---|---|---|---|---|
| 21 | **Obim skeniranja** (O-8, O-14): svaki ulazni akt ili samo neke vrste; da li i zatečena arhiva | odluka | Uprava, arhivska služba | 31.01.2027. | 5 |
| 22 | **eArhiv** (O-17): da li je IMS obveznik | odluka | Pravna služba | 31.03.2027. | 7 |
| 23 | ~~Uništenje papira posle digitalizacije~~ (O-13) — **zatvoreno 05.10.2026.:** papir se ne uništava, jer se čuva lokalno, bez kvalifikovanog pružaoca | — | — | ✔ | — |
| 24 | ~~Kvalifikovani pružalac čuvanja~~ — **ne koristi se** (sve na lokalnom serveru) | — | — | ✔ | — |
| 24a | **Spoljna rezervna kopija** (O-25): da li i gde se čuva kopija van zgrade (drugi objekat, iznajmljen prostor, oblak) | odluka | Uprava, IT | — | 7 |
| 25 | **Komisija za izlučivanje i nadležni arhiv** (O-10) | odluka | Direktor | 30.06.2027. | 8 |

### 1.6 Nezavisno od arhive: Zakon o informacionoj bezbednosti (O-19)

Zakon o informacionoj bezbednosti iz 2025. u čl. 6 navodi **naučnoistraživačke institucije** kao operatore važnih
IKT sistema. Ako je Institut registrovan kao naučnoistraživačka institucija, i ako ispunjava kriterijume veličine
koje Vlada tek treba da propiše, obaveze važe za ceo IT Instituta, a ne samo za arhivu:

- upis u registar operatora;
- odgovorno lice za informacionu bezbednost;
- mere upravljanja rizikom;
- prijava incidenta u roku od 24 časa.

Prema objavljenom sažetku zakona, rok za procenu rizika je 30.04.2027, što treba proveriti u tekstu zakona.
Procena rizika i mere iz tačaka 17 i 18 mogu da posluže za oba propisa. Nosilac je Uprava sa IT-om.

---

## 2. Principi

1. **Arhiva ne duplira dokumente koji već postoje u aplikaciji.** Rešenje, ugovor, predmet nabavke ili disciplinski
   postupak ostaju u svom modulu. Arhiva čuva upis u delovodnik i **vezu** ka tom zapisu, uz snimak osnovnih podataka.
2. **Delovodni broj daje samo arhiva**, a ostali moduli ga traže preko servisa.
3. **Lista kategorija je šifarnik, a ne tekst.** Svaki predmet dobija kategoriju, iz nje klasifikacionu oznaku i rok
   čuvanja, a iz roka čuvanja datum izlučivanja.
4. **Brojevi se nikad ne brišu i ne koriste ponovo.** Pogrešan upis se stornira uz napomenu.
5. **Overu radi samo potpisni servis**, nikad korisnički računar. Svaka upotreba pečata se beleži.
6. **Ništa se ne overava bez provere.** Sken prolazi kontrolu drugog lica pre nego što uđe u paket overe.
7. **Aplikacija ne briše overene dokumente.** Uklanjaju se samo kroz izlučivanje, uz saglasnost nadležnog arhiva.
8. **Elektronski rad je pravilo, papir izuzetak.** Evidencije, potvrde prijema, razvod, rokovnik, zapisnici i
   arhivska knjiga vode se u aplikaciji; prijava korisnika i dnevnik zamenjuju potpis u knjizi, a kvalifikovani
   el. potpis ili pečat zamenjuje svojeručni potpis i otisak pečata. Interni pravilnik se tome prilagođava (4.6).

Važe i pravila sistema (AGENTS.md): ništa se ne upisuje u nasleđene `dbo.*` objekte, ništa ne ide u modul
`naplata`, a formula za rok čuvanja traži pisanu potvrdu.

---

## 3. Šta propisi traže

| Propis | Odredba | Šta znači za nas |
|---|---|---|
| Zakon o el. dokumentu, el. identifikaciji i uslugama od poverenja (ZEDEIUP) | čl. 10 | Sken papirnog dokumenta je **kopija**, ne original. |
| ZEDEIUP | čl. 11 | Digitalizovani akt ima dokaznu snagu originala kada **istovetnost sa originalom** potvrdi ovlašćeno lice kvalifikovanim el. potpisom ili pečatom. To je „overa“. |
| ZEDEIUP | čl. 51, 53 | Kvalifikovani el. pečat daje pretpostavku celovitosti i porekla. Kvalifikovani vremenski žig daje pretpostavku tačnog vremena. |
| ZEDEIUP | čl. 62 | Pouzdano el. čuvanje: tokom celog čuvanja mora se moći dokazati validnost potpisa. |
| ZEDEIUP | čl. 63 st. 4 | Ako se dokument čuva **u okviru kvalifikovane usluge el. čuvanja**, a period usluge pokriva propisani rok, **izvorni dokument može biti uništen**, osim ako nije drugačije propisano. |
| Pravilnik o uslovima i tehnološkim rešenjima za pouzdano el. čuvanje | čl. 1, 2 | Važi za **svakoga ko vrši pouzdano čuvanje** (rukovalac čuvanja), ne samo za kvalifikovane pružaoce. Čuvanje se vrši po **internim pravilima**. |
| Pravilnik | čl. 4 | Formati: **PAdES (ETSI EN 319 142)**, XAdES, CAdES ili ASiC-S. Nivo **B-LTA**. |
| Pravilnik | čl. 5 | Pri početku čuvanja: vremenski žig, provera potpisa, prikupljanje podataka o validnosti (lanac, opoziv), žig na heš. |
| Pravilnik | čl. 7 | **Obavezna ponovna dopuna** pre isteka sertifikata poslednjeg žiga ili slabljenja algoritama. |
| Pravilnik | čl. 8 | Informacioni sistem za čuvanje vodi se **u skladu sa ISO/IEC 27001**. **Sertifikat se ne traži.** Visok nivo zaštite. Mere su opisane u internim pravilima. |
| Uredba o uslovima za pripremu dokumenata za pouzdano el. čuvanje | čl. 5–7 | Digitalizacija, konverzija ili provera. **Kontrola kvaliteta ne sme zavisiti od jedne osobe ni jedne komponente.** |
| Ista Uredba | čl. 10, 12, 13 | Kvalifikovani potpis ili pečat + žig pri pripremi. **Dnevnik radnji.** Formati: **PDF/A (ISO 19005)**, TIFF, JPEG, PNG, JPEG2000, PDF/E. |
| Uredba o tehničko-tehnološkim zahtevima za čuvanje arhivske građe | čl. 5 | **15 obaveznih metapodataka** (odeljak 7.5). Arhivska knjiga u el. obliku. |
| Zakon o arhivskoj građi i arhivskoj delatnosti | čl. 6 | Arhivska građa se čuva **trajno u obliku u kom je nastala**. Papirni original materijala bez trajnog roka sme se uništiti. |
| Isti zakon | čl. 13 | **El. arhivska građa pre predaje nadležnom arhivu može se privremeno dati na čuvanje samo državnom organu ili kvalifikovanom pružaocu el. čuvanja.** |
| Isti zakon | čl. 9, 14, 16, 17–18 | Arhivska knjiga i prepis do 30. aprila. Lista kategorija uz saglasnost. Izlučivanje samo uz pismenu saglasnost. Predaja posle 30 godina. Kazne do 2.000.000 din. |
| Zakon o informacionoj bezbednosti (2025) | čl. 6 | Naučnoistraživačke institucije su operatori **važnih IKT sistema**. Obaveze važe za ceo IT Instituta (odeljak 1.6). |
| **Interni pravilnik o arhivskom poslovanju (2023)** | čl. 14, 4 | Delovodnik se sme voditi elektronski; arhivska knjiga i u el. obliku. |
| Interni pravilnik | čl. 48 st. 3 | Papir **bez trajnog roka** sme se uništiti pre isteka roka **tek posle digitalizacije i samo uz kvalifikovanu uslugu el. čuvanja**. Sopstveni server za to nije dovoljan (O-13). |
| Interni pravilnik | čl. 51–53 | Izlučivanje i predaja idu **Državnom arhivu Srbije**; predaja posle 30 godina, svake pete godine. |

**Posledice za arhitekturu:**

- **Sopstveni server je dozvoljen**, pa se sve čuva na lokalnom Windows serveru (odluka 05.10.2026.), uz interna
  pravila i vođenje sistema po pravilima ISO/IEC 27001 (odeljak 5.4).
- **Trajna građa:** papirni original je arhivska građa i ostaje u arhivi do predaje Državnom arhivu Srbije; sken na
  serveru je radna kopija. Čl. 13 Zakona o arhivskoj građi ograničava samo **davanje** el. građe drugome na čuvanje
  (samo državnom organu ili kvalifikovanom pružaocu) — mi je ne dajemo nikome, nego čuvamo sami do predaje.
  **Proveriti sa pravnom službom** za akte koji nastaju samo elektronski, a imaju trajan rok.
- **Uništenje papira** posle digitalizacije dozvoljeno je samo uz kvalifikovanu uslugu čuvanja (ZEDEIUP čl. 63 st. 4,
  interni pravilnik čl. 48 st. 3). Pošto je ne koristimo, **papir se ne uništava** (O-13 zatvoreno).

> Tekstovi propisa čitani su sa paragraf.rs. Brojeve članova treba proveriti u važećoj verziji pre nego što uđu u
> interna pravila.

---

## 4. Zatečeno stanje

### 4.1 Evidencione knjige po IU 03

| Knjiga | Rubrike (uputstvo ili obrazac) | U sistemu |
|---|---|---|
| **Delovodnik** (Prilog 1) | osnovni broj / prenos, predmet, podbroj, datum prijema, pošiljalac, broj i datum akta pošiljaoca, OJ, razvod (datum, oznaka) | Osnovna tabela. „Prenos“ je veza ka predmetu iz prethodne godine. |
| **Dostavna knjiga** (Prilog 2) | datum zavođenja, delovodni broj, pošiljalac, primalac, datum razvođenja, potpis primaoca | Elektronska potvrda prijema (korisnik i vreme). Knjige po OJ, uz dve posebne: za direktora, i za finansijskog direktora i direktora opštih poslova. |
| **Prijemna knjiga P-3 PTT** (Prilog 3) | redni broj, prijemni broj, primalac, odredišna pošta, vrednost, masa, otkupnina, poštarina | Evidencija otpreme i štampa lista P-3 |
| **Knjiga ulaznih faktura** (Prilog 4) | od koga, datum i broj fakture, iznos, rok plaćanja, plaćeno … | **Izveštaj** nad podacima Nabavke i Finansija (EUF, SEF). Pisarnica dopisuje samo datum prijema i delovodni broj za papirne fakture. |
| **Knjiga faks poruka** (Prilog 5) | redni broj, OJ, faks, firma, broj strana | Samo ako se faks još koristi (O-5) |

Knjige se vode za kalendarsku godinu. **Zaključenje** je akcija u sistemu: broj akata, korisnik, vreme i službena
zabeleška. Posle nje je knjiga samo za čitanje.

**Neslaganje u IU 03:** slika uz Prilog 2 je obrazac otpreme (datum otpreme, broj preporuke, poštarina), a ne
dostavna knjiga iz tačke 4.1.2. Sistem ima obe evidencije, a uputstvo treba ispraviti.

### 4.2 Delovodnik danas (primer: `Delovodnik 2024.xlsx`)

Delovodnik se danas ne vodi u programu; tabela za 2024. je primer kako izgleda vođenje. Iz nje:

- **15.056 upisa** godišnje, oko 60 po radnom danu, najviše 149 u danu. **Unos mora biti brz.**
- Stvarno se popunjavaju samo: broj, predmet, datum, OJ i jedno od polja „Prijem/Firma“ (ulazni akt) ili
  „Slanje/Firma“ (izlazni akt).
- **Razvod, kategorija, klasifikaciona oznaka, rok čuvanja i predaja arhivi su prazni u svih 15.056 redova.** Bez
  kategorije nema roka, a bez roka nema izlučivanja. Novi modul **traži kategoriju** najkasnije pri završetku predmeta.
- OJ je broj centra (41, 43, 44, 82, 42, 20 …), uz nepravilne vrednosti (`43+44`, `41MD S`, `20/44`, `43HI`) i 17
  praznih. U novom sistemu OJ se bira iz registra organizacije.
- Broj je jedan niz za ceo Institut, a OJ je posebna kolona. **Taj način brojanja ostaje** (O-1, 05.10.2026.).

### 4.3 Brojevi u aplikaciji danas

- **Kadrovi → Zahtevi** imaju sopstveni brojač (`BrojacZahteva`) i broj `{centar}-{redni broj u godini}`, npr.
  `43-17`. **Rešenje** dobija podbroj zahteva (`43-17/1`). Ovo je već oblik delovodnog broja (oznaka OJ + broj iz
  jednog niza), pa arhiva preuzima brojač, a format se ne menja. Od 01.01.2027. zahtevi dobijaju broj iz delovodnika.
- `PutniNalog` dobija broj kao `MAX()+1`. Arhiva to ne preuzima (odeljak 8), ali se ne ugleda na taj obrazac.
- Disciplinski postupak nema broj.

### 4.4 Lista kategorija — pre uvoza

| # | Zapažanje | Posledica |
|---|---|---|
| 1 | Klasifikaciona oznaka stoji samo u zaglavlju grupe. Ista oznaka važi za više grupa (**20**, **82**). | Model ima **Grupu** kao zaseban nivo. |
| 2 | Ponovljene stavke: 75 = 96, 79 = 99, 80 = 100, 13 ≈ 138/139, 16 ≈ 10 | Uvoze se kako jesu, sa oznakom duplikata. Arhivista bira „preporučenu“. |
| 3 | **Protivrečni rokovi:** računi 10 godina (194, 195) i 5 godina (209, 210, 294, 295) | Odluka pre uvoza. Institut je obveznik PDV-a, pa verovatno 10 godina. |
| 4 | Rokovi nisu samo „N godina“: *trajno*, *trajno operativno*, *od isteka zakupa*, *po okončanju*, *nakon prestanka važenja* … | Rok = broj godina (ili trajno) + **događaj od kog teče** |
| 5 | Oznaka **426** ne liči na ostale | Proveriti |
| 6 | Lista važi uz saglasnost Državnog arhiva | Šifarnik ima verziju, datum važenja i broj saglasnosti. Stare stavke se ne brišu. |
| 7 | Za overu svaka kategorija treba oznaku *dozvoljen el. original* (akt sme da nastane i postoji samo elektronski) | Jedno polje u šifarniku, popunjava arhivista uz pravnu proveru. Oznake „trajno → pružalac” i „papir se sme uništiti” otpadaju (sve lokalno, papir se ne uništava). |

---

### 4.5 Interni pravilnik o arhivskom poslovanju (2023) — poređenje sa planom

Pribavljen 05.10.2026. (O-3). Dva PDF-a „Pravilnik o kancelarijskom i arhivskom poslovanju” su isti fajl, akt
Upravnog odbora od 05.12.2005, i **zamenjeni su**. Važi pravilnik br. 20-16153 od 07.12.2021, sa izmenom od
24.02.2023 (doneo generalni direktor, po Zakonu o arhivskoj građi iz 2020).

**Šta pravilnik potvrđuje u planu:** elektronski delovodnik i el. arhivska knjiga (čl. 14, 4); osnovni broj i
podbroj, „prenos” iz prethodne godine (čl. 15, 17); zaključenje delovodnika 31.12 sa službenom zabeleškom (čl. 16);
obrađivač pri završetku upisuje rok čuvanja iz Liste (čl. 25) — u planu **obavezna kategorija**; pomoćne evidencije
(interna dostavna knjiga, dostavna knjiga za poštu, knjiga računa, čl. 14 i 21); Lista uz saglasnost arhiva i popis
za izlučivanje (čl. 47, 51).

**Šta pravilnik traži, a plan do sada nije imao** (dopunjeno u odeljcima 7, 9, 10 i 14):

| # | Obaveza | Član | U planu |
|---|---|---|---|
| 1 | **Popis akata**: za masovne akte iste vrste (uverenja, potvrde, **rešenja o godišnjim odmorima**, radni nalozi, bolovanja) na početku godine se rezervišu prvi osnovni brojevi i vodi „popis akata”; na kraju godine se u delovodnik upisuje ukupan broj. Akt iz popisa sa posebnim postupkom ide u delovodnik pod osnovnim brojem. | 18 | Vrsta knjige `POPIS_AKATA` vezana za rezervisan osnovni broj. **Odluka O-20**: da li zahtevi i rešenja iz Kadrova idu u popis akata umesto da svaki dobije osnovni broj (odeljak 6.4). |
| 2 | **Poverljivi i strogo poverljivi delovodnik**, vodi se kao običan; poverljivu poštu otvara Sekretarijat | 7, 19 | Vrste knjige `POVERLJIVI`, `STROGO_POVERLJIVI`, poseban pristup (O-21) |
| 3 | **Razvod** u rubrici 9: „a/a” + rok čuvanja; „R” (u čl. 15 „P”) + datum; ustupljeno OJ; „izvorno” + organ. **Rokovnik predmeta** — predmeti sa rokom, po datumu roka | 15, 26, 28 | `Predmet.razvod_oznaka` (4 vrste), `rok_datum`, `ustupljeno_oj`, `izvorno_organ`; ekran „Rokovnik” |
| 4 | **Prijemni štambilj**: primljeno, OJ, broj, broj priloga (i listova), vrednost (takse/novac) | 11 | `broj_priloga`, `broj_listova`, `vrednost`; štampa nalepnice |
| 5 | Pošta primljena **elektronski se štampa** i zavodi u papiru | 6 st. 3 | **Menja se pravilnik** (4.6, A2): el. pošta se zavodi elektronski, sa izvornim fajlom. Do stupanja izmene na snagu (probni rad) pisarnica i dalje štampa primerak. |
| 6 | **Omot predmeta**: broj, godina, OJ, kratak sadržaj, popis priloga | 23 | Štampa omota sa detalja predmeta |
| 7 | Službeni dopis nosi broj **„sa klasifikacionim znakom”** | 22 | Dopuna O-1: da li izlazni broj sadrži i klasifikacionu oznaku |
| 8 | Oznake OJ su **trocifreni brojevi 100–831**, po Pravilniku o organizaciji | 12 | OJ iz registra; u rubriku OJ ide trocifrena oznaka. Prefiks centra u broju (`43-15238`) je naš izbor, ne pravilnik (O-1) |
| 9 | Rokovi pisarnice: zavođenje istog dana, najkasnije sledećeg radnog dana **pod datumom prijema**; dostava u rad isti ili sledeći dan; otprema do 13 h isti dan | 13, 20, 29 | `datum_prijema` odvojen od `zavedeno_at`; upozorenja u `proveri_rokove` |
| 10 | **Arhiva pisarnice najviše 2 godine od zavođenja**, zatim zapisnički u arhivski depo. **Revers** najduže do kraja naredne godine, u 3 primerka | 33, 38, 40 | Pravila u `proveri_rokove` i u reversu; štampa reversa u 3 primerka |
| 11 | **Arhivska knjiga**: redni broj se nastavlja iz godine u godinu; rok čuvanja; broj i datum zapisnika (uništenje ili predaja); upis do aprila naredne godine. **Prepis do 30. aprila** sa količinom u **dužnim metrima** | 43, 44 | `UpisArhivskeKnjige.zapisnik_broj/datum`, `rok_cuvanja`; `ArhivskaJedinica.duzni_metri`; podsetnik za 30.04 |
| 12 | **Izlučivanje** u roku od godinu dana od isteka roka; popis sa 6 kolona (i dužni metri); zahtev Državnom arhivu Srbije; obaveštenje o uništenju | 51 | Već u planu; dodati rok i dužne metre |
| 13 | **Predaja posle 30 godina, svake pete godine**; zapisnik u 5 primeraka sa propisanim podacima | 52, 53 | `PredajaNadleznomArhivu`: polja zapisnika i štampa |
| 14 | Obaveštavanje arhiva o statusnim promenama u roku od 30 dana | 54 | Van sistema |

**Nedoslednosti u samom pravilniku** (za izmenu, O-24): oznaka roka je „P” u čl. 15, a „R” u čl. 26; prepis
arhivske knjige ide „nadležnom Istorijskom arhivu” (čl. 44), a izlučivanje i predaja Državnom arhivu Srbije
(čl. 51–53); čl. 37 ima praznu tačku 5.

### 4.6 Predlog izmena internog pravilnika za elektronski rad

Cilj je da se poslovanje vodi kroz aplikaciju i elektronski potpisuje, a da pravilnik to izričito dozvoli. Pravilnik
donosi generalni direktor (čl. 43 Statuta), a izmene se donose na isti način (čl. 55); izmena iz 2023. stupila je na
snagu osmog dana od objave na oglasnoj tabli. Lista kategorija se ne menja (traži saglasnost arhiva, čl. 47).
**Proveriti sa pravnom službom** da li izmena pravilnika traži mišljenje nadležnog arhiva.

Izmene idu u **dva koraka**, da prelazak 01.01.2027. ne čeka nabavku pečata i žiga.

**A — korak 1, do 01.01.2027: elektronski delovodnik i tok predmeta** (tačka 12a)

| # | Član | Sada | Predlog |
|---|---|---|---|
| A1 | 3, 14 | Delovodnik „odnosno elektronski delovodnik” | Sve evidencije (delovodnik, popis akata, poverljivi delovodnik, dostavne i otpremne knjige, knjiga računa, rokovnik, arhivska knjiga) **vode se u aplikaciji IMS ERP**; papirne knjige se ne vode. Štampa iz aplikacije je izvod. |
| A2 | 6 st. 3 | El. primljeni dopis se štampa i zavodi u papiru | El. primljen akt (e-pošta, SEF, portal) zavodi se **elektronski, sa izvornim fajlom**; štampa nije obavezna. |
| A3 | 6, 21 | Potvrda prijema potpisom u dostavnoj knjizi; lična pošta uz potpis primaoca | Prijem se potvrđuje **u aplikaciji** (korisnik i vreme). Papirni potpis samo za papirnu pošiljku predatu lično, ako primalac nema pristup aplikaciji. (O-4) |
| A4 | 10, 11 | Otisak prijemnog štambilja na aktu | Podaci štambilja (datum, OJ, broj, prilozi, listovi, vrednost) upisuju se u aplikaciju; na papirni akt se lepi **nalepnica iz aplikacije**, a na sken se ugrađuje el. otisak. |
| A5 | 15 | Upis „čitkim rukopisom” u rubrike 1–9 | Rubrike su polja u aplikaciji; broj dodeljuje aplikacija. |
| A6 | 15, 26 | „P” i „R” za rok | Jedna oznaka: **„R”** + datum. |
| A7 | 16 | Zabeleška o zaključenju overena pečatom i potpisana | Zaključenje u aplikaciji (korisnik, vreme, broj upisa); zabeleška se **overava el. pečatom** kada pečat postoji (korak 2), do tada štampa i potpis. |
| A8 | 18 | Popis akata u obliku knjige | Popis akata u aplikaciji; vrste za koje se vodi određuje generalni direktor (O-20). |
| A9 | 23, 24, 25 | Papirni omot; predmet se vraća preko interne dostavne knjige; obrađivač na dopisu upisuje „a/a”, rok i potpisuje | **Elektronski predmet** u aplikaciji; papirni omot samo za papirne priloge. Završetak predmeta u aplikaciji: izbor kategorije i rok iz Liste; prijava obrađivača zamenjuje potpis. |
| A10 | 28 | Rokovnik od fascikala | Rokovnik u aplikaciji (spisak po datumu roka, podsetnik). |
| A11 | 29, 32 | Pečat „ekspedovano” na kopiji; knjiga ekspedovane pošte | Otprema se beleži u aplikaciji (datum, način, preporuka, poštarina); knjiga i P-3 su izveštaji. |
| A12 | 33, 38, 40 | Zapisnička predaja u depo; revers u 3 primerka | Zapisnik i revers u aplikaciji sa potvrdom korisnika; papir samo ako ga traži druga strana. |
| A13 | 44 | Prepis arhivske knjige | Prepis je **izvod iz aplikacije**; utvrditi kom arhivu se šalje (O-24). |
| A14 | 37, 44, 51 | Nedoslednosti | Popuniti ili brisati tačku 5 u čl. 37; jedan nadležni arhiv. |

**B — korak 2, pre prve elektronske overe: potpis, pečat, overa i čuvanje** (tačka 17b; spaja se ili usklađuje sa
pravilnikom o el. dokumentima, O-23)

| # | Tema | Predlog odredbe |
|---|---|---|
| B1 | El. potpis i pečat (čl. 3, 22) | Akt Instituta može biti **elektronski dokument** potpisan kvalifikovanim el. potpisom ovlašćenog lica ili overen **kvalifikovanim el. pečatom Instituta**; tada se ne štampa i nema otisak pečata. Koje akte potpisuje direktor lično, a koje pečat (O-15). |
| B2 | Ovlašćena lica | Ko overava istovetnost (ZEDEIUP čl. 11), ko pokreće paket overe, ko koristi pečat; svaka upotreba se beleži (tačka 15). |
| B3 | Digitalizacija | Sken papirnog akta je kopija dok ga **drugo lice ne proveri** i ovlašćeno lice ne overi; tada ima dokaznu snagu originala. Postupak, oprema i formati (PDF/A) po Uredbi. |
| B4 | Formati i potpis | PDF/A, PAdES-B-LTA, kvalifikovani vremenski žig; aplikacija obnavlja žig pre isteka. |
| B5 | Čuvanje | Svi el. dokumenti čuvaju se na **lokalnom serveru Instituta** po **internim pravilima** (procena rizika, pristup, rezervne kopije i probno vraćanje, incidenti, dnevnik; ISO/IEC 27001 bez sertifikata), do isteka roka ili predaje Državnom arhivu Srbije. |
| B6 | Papir posle digitalizacije | **Papirni original se čuva** do isteka roka iz Liste; digitalizacija ne skraćuje čuvanje papira. Postojeći čl. 48 st. 3 ostaje, ali se ne primenjuje dok se ne koristi kvalifikovano čuvanje. |
| B7 | Metapodaci i dnevnik | 15 obaveznih metapodataka; dnevnik radnji se ne menja i ne briše. |

---

## 5. Odluke o tehnologiji overe i čuvanja

### 5.1 Tri slučaja overe

| # | Slučaj | Primer | Kako se overava |
|---|---|---|---|
| A | **Digitalizacija papira** | ulazna pošta, stari ugovori, kadrovski dosijei | Kontrola drugog lica, pa **pečat Instituta** (potvrda istovetnosti, čl. 11) |
| B | **Dokumenti koje pravi aplikacija** | zahtevi i rešenja, radne liste sa evidencijom prolaza, opomene, zapisnici | **Pečat Instituta.** Ako akt traži potpis direktora, **udaljeni lični potpis** za ceo paket. |
| C | **Dokumenti koji stižu potpisani** | SEF e-fakture, ugovori koje je partner potpisao | Ne overavaju se ponovo. **Proverava se** potpis, pa se dodaju žig i podaci do nivoa LTA. |

Za slučaj A nam treba masovna overa: 500 skenova mora da ide **jednim pokretanjem**, bez PIN-a za svaki dokument.

### 5.2 Načini potpisivanja

| Način | Masovno | Za | Protiv | Odluka |
|---|---|---|---|---|
| **Udaljeni kvalifikovani pečat** (ključ u HSM-u pružaoca, server šalje heševe preko API-ja) | Da, paketno | Nema hardvera kod nas. Pružalac odgovara za kvalifikovani uređaj. Skalira se. | Trošak po potpisu ili paketu. Zavisnost od mreže. API se razlikuje od pružaoca do pružaoca. | **Preporuka** |
| **Pečat na kvalifikovanom tokenu ili HSM-u u našem serveru** (PKCS#11) | Da | Bez troška po potpisu. Radi i bez spoljne usluge. | Uređaj na serveru. PIN u konfiguraciji traži jake mere. Jedna tačka otkaza. | Rezerva, ako je udaljeni pečat preskup |
| **Udaljeni kvalifikovani lični potpis** (npr. direktor, jedno odobrenje za paket) | Da, ako pružalac podržava paket | Bez kartice. Potpis sa telefona. | Proveriti paketno odobravanje. | Za akte koji traže lični potpis (O-15) |

### 5.3 Pružaoci u Srbiji (registar Ministarstva informisanja i telekomunikacija)

| Usluga | Registrovani pružaoci |
|---|---|
| Sertifikat za **el. pečat** | Pošta Srbije, E-Smart Systems (ESS QCA) |
| **Udaljeni el. pečat** | PKS CA, Kancelarija za IT i eUpravu, Paperless, Telekom Srbija |
| **Udaljeni el. potpis** | PKS CA, Halcom, Kancelarija za IT i eUpravu, Paperless, Telekom Srbija |
| **Kvalifikovani vremenski žig** | Pošta Srbije, PKS CA, Kancelarija za IT i eUpravu, Inception, Telekom Srbija |
| **Kvalifikovano el. čuvanje** | Inception, Pošta Srbije, Paperless, Iron Mountain — **ne koristi se** (sve na lokalnom serveru, 05.10.2026.) |
| Validacija | PKS CA, Inception, Telekom Srbija |

Izbor pružaoca ide kroz nabavku (odeljak 1.4, tačka 13). Ovo je samo spisak registrovanih.

### 5.4 Gde se šta čuva

**Odluka 05.10.2026.: sve se čuva na lokalnom Windows serveru Instituta.** Overavamo sami (pečat i žig su usluga
pružaoca), a čuvamo kod sebe. Kvalifikovani pružalac čuvanja se ne koristi.

| Vrsta | Gde | Napomena |
|---|---|---|
| Overeni dokumenti (PAdES-B-LTA) | **Lokalni server** | Pouzdano čuvanje po Pravilniku, po internim pravilima. Papirni original ostaje. |
| Radni skenovi bez overe | Lokalni server | Pomoćna kopija, bez pravne snage originala |
| Arhivska građa (trajno) | **Papir u arhivi**; sken, ako postoji, na lokalnom serveru | Original se predaje Državnom arhivu Srbije (Zakon o arhivskoj građi čl. 6) |
| Dnevnik radnji i metapodaci | Baza aplikacije na lokalnom serveru | Dnevnik se samo dopisuje |
| Rezervna kopija | **Drugi disk ili uređaj u Institutu**; spoljna kopija — videćemo (O-25) | Dok ne postoji kopija van zgrade, požar ili krađa servera mogu da unište i original i kopiju el. dokumenta; papir ostaje |

**Šta to znači:** papir se ne uništava posle digitalizacije (O-13 zatvoreno), a čuvanje mora da se vodi po
internim pravilima (O-12 postaje obavezno).

**Šta „po pravilima ISO/IEC 27001" znači u praksi.** Sertifikat se ne traži i niko se ne plaća. Traži se da se
sistem za čuvanje vodi onako kako bi se vodio svaki ozbiljan arhivski sistem, i da to bude **zapisano u internim
pravilima**:

- **procena rizika**: šta može da se desi podacima (kvar diska, brisanje, napad, istek žiga) i šta preduzimamo;
- **pristup**: ko sme šta da vidi i radi, i kako se to proverava;
- **rezervne kopije** i **probno vraćanje** u redovnim razmacima;
- **postupak za incidente**: šta se radi kada se nešto desi, ko odlučuje i ko se obaveštava;
- **dnevnik radnji**: ko je šta radio sa kojim dokumentom.

Tehnički deo ovih mera je već u arhitekturi (odeljak 6.8). Papirni deo su interna pravila i procena rizika
(odeljak 1.4, tačke 17 i 18).

---

## 6. Arhitektura

### 6.1 Celina

```
 ┌──────────────── IMS ERP (Django) — aplikacija `arhiva` ─────────────────────────────┐
 │  Pisarnica · Delovodnik · Moji predmeti · Arhiva · Izlučivanje · Izveštaji           │
 │        │                                                                             │
 │        ▼                                                                             │
 │  Priprema elektronskog dokumenta                                                     │
 │   • digitalizacija: sken → PDF/A + OCR → KONTROLA DRUGOG LICA                        │
 │   • konverzija: štampe iz aplikacije, DOCX/XLSX → PDF/A                              │
 │   • provera: dokument koji je stigao potpisan                                        │
 │   • 15 metapodataka                                                                  │
 │        │                                                                             │
 │        ▼                                                                             │
 │  PAKET OVERE ── „Overi N dokumenata" ──► Celery red `potpis`                         │
 │  Rokovi: obnova žiga, provera integriteta, rok čuvanja, izlučivanje, predaja         │
 │  Nepromenljiv dnevnik radnji                                                         │
 └──────────────┬──────────────────────────────────────────────┬────────────────────────┘
                ▼                                              ▼
 ┌─ Potpisni servis (worker `potpis`) ──────────┐   ┌─ Skladište elektronske arhive ───────┐
 │  pyHanko: PAdES B-B → B-T → B-LT → B-LTA     │   │  lokalni Windows server, ne /media/  │
 │  validacija, OCSP/CRL, document timestamp    │   │  aplikacija ne briše, SHA-256,       │
 │  potpis: API udaljenog pečata ili PKCS#11    │   │  provera heševa, kopija na drugom    │
 └───────┬──────────────────────┬───────────────┘   │  disku, probno vraćanje (O-25)       │
         │ heš → potpis         │ heš → žig         └──────────────────────────────────────┘
         ▼                      ▼
 ┌─ Kvalifikovani pružalac (samo overa) ─────┐
 │  udaljeni pečat / lični potpis (HSM)      │     Čuvanje: SAMO lokalni Windows server Instituta
 │  vremenski žig (RFC 3161)                 │     (odluka 05.10.2026.; spoljna kopija — O-25)
 └───────────────────────────────────────────┘
```

### 6.2 Nova Django aplikacija `arhiva`

Prati obrazac ostalih modula: `views/` prikazuje, a `services/` računa.

```
arhiva/
  models/
    sifarnici.py      VerzijaListe, GrupaKategorija, Kategorija, VrstaAkta, Lokacija
    knjige.py         EvidencionaKnjiga, BrojacKnjige, Predmet, Akt, Prilog, VezaDokumenta
    tok.py            Dostava, Otprema, Zaduzenje
    arhiva.py         PredajaArhivi, ArhivskaJedinica, UpisArhivskeKnjige, Revers
    izlucivanje.py    Izlucivanje, StavkaIzlucivanja, PredajaNadleznomArhivu
    elektronski.py    ElektronskiDokument, KontrolaDigitalizacije, PaketOvere, Overa,
                      ObnovaIntegriteta, PredajaPruzaocu, DnevnikArhive
  services/
    delovodnik.py     zavedi(), dodaj_podbroj(), storniraj(), zakljuci_knjigu(), prenesi_u_novu_godinu()
    rokovi.py         izracunaj_istek_cuvanja(), kandidati_za_izlucivanje()
    veze.py           povezi(), snimak_izvora(), predlog_kategorije()
    priprema.py       u_pdfa(), ocr(), proveri_pdfa(), metapodaci()
    overa.py          napravi_paket(), overi_dokument(), validiraj(), obnovi_zig()
    potpis/           klijent udaljenog pečata, PKCS#11, TSA — iza jednog interfejsa
    cuvanje.py        upisi_u_skladiste(), proveri_hes(), predaj_pruzaocu()
    izlucivanje.py    predlog_liste(), potvrdi_saglasnost(), zavrsi_unistenje()
    predaja.py        zapisnik_predaje(), prijem_u_arhivu()
  registry.py         tipovi dokumenata iz drugih modula koji se mogu arhivirati
  adapters/           po jedan fajl po izvornom modulu: hr.py, pravna.py, ugovori.py, nabavka.py, finansije.py, …
  templatetags/arhiva_tags.py   {% arhiva_panel objekat %}
  views/ templates/arhiva/ forms.py urls.py (app_name = "arhiva") tasks.py
  management/commands/  import_lista_kategorija.py, import_delovodnik_xlsx.py
  tests/
templates/sidebar_arhiva.html
```

Uklapanje: `INSTALLED_APPS`, `path("arhiva/", include("arhiva.urls"))`, kodovi dozvola preko
`sync_permission_codes`, bočni meni (`sidebar_map`, `switch_app`, `header.html`). Sve tabele su nove (`arhiva_*`).

### 6.3 Kako arhiva linkuje postojeće dokumente

```
VezaDokumenta
  akt                  FK → arhiva.Akt
  content_type, object_id (CharField 64), izvor = GenericForeignKey
  -- snimak pri povezivanju, da arhiva ostane čitljiva i ako se izvor promeni ili obriše --
  oznaka, naslov, datum_dokumenta, partner_naziv, zaposleni_naziv, oj_kod, url
  izvor_dostupan (noćna provera), povezao, povezano_at
```

Adapter za svaki izvorni model (`arhiva/adapters/<app>.py`) zna da:

- vrati snimak (`snimak()`);
- predloži kategoriju (`predlog_kategorije()`), koju arhivista potvrđuje;
- vrati postojeće fajlove **bez kopiranja** (`prilozi()`);
- **napravi PDF za overu** iz postojeće štampe ili snimka (`pdf_za_overu()`, slučaj B);
- upiše delovodni broj nazad u izvor (`upisi_broj()`).

Izvorni moduli ostaju skoro netaknuti: jedina izmena je `{% arhiva_panel objekat %}` u šablonu detalja. Panel
prikazuje delovodni broj, status u arhivi i status overe, uz dugmad „Zavedi“, „Poveži“ i „Overi“.

### 6.4 Dodela delovodnog broja

- Za svaku knjigu i godinu postoji jedan red brojača, a `zavedi()` ga zaključava sa `select_for_update()`.
  **Ne koristi se `MAX()+1`.** Druga linija zaštite je unique ograničenje na (knjiga, godina, osnovni broj, podbroj).
- Format dolazi iz postavke i ostaje `{oj}-{osnovni broj}` i `/{podbroj}`, kao danas u Kadrovima (O-1 odlučeno
  05.10.2026.: postojeći način brojanja). Jedan brojač po knjizi i godini, ne po OJ.
- **Prelazak brojača zahteva:** `hr.services.zahtevi.dodeli_broj()` počinje da poziva `arhiva.services.delovodnik.zavedi()`.
  Brojevi i format ostaju isti. `BrojacZahteva` se jednom preslika u brojač delovodnika, pa ostaje samo za čitanje.
  Rešenje i dalje dobija podbroj zahteva.
- **Popis akata (pravilnik čl. 18, O-20):** ako se odluči da masovni akti Kadrova (npr. rešenja o godišnjem odmoru)
  idu u popis akata, oni dobijaju redni broj u popisu pod rezervisanim osnovnim brojem, a ne sopstveni osnovni broj.

### 6.5 Potpisni servis

- **pyHanko** (Python, MIT licenca): PAdES do B-LTA, document timestamp, validacija sa LTV podacima, PKCS#11 i
  potpisivanje kada potpis stiže spolja (heš se šalje pružaocu, potpis se ugrađuje u PDF). Ostaje u postojećem
  Python okruženju.
- **EU DSS** (Java, LGPL) samo ako zatreba ASiC/XAdES ili formalni ETSI izveštaj validacije. Tada radi kao poseban
  REST servis.
- **Poseban Celery red `potpis` i poseban worker** (NSSM servis `IMS_Fleet_Celery_Potpis`). Postojeći worker radi sa
  `-P solo` i opslužuje i Selenium (AGENTS.md §7). Bez posebnog workera overa bi čekala sat vremena ili bi blokirala
  preuzimanje goriva.
- **Nastavljivo:** svaki dokument u paketu ima svoj status. Ponovno pokretanje nastavlja gde je stalo. Dvostruka overa
  se odbija.
- **Tajne** (API ključ pružaoca, PIN tokena) su u `.env`, kao SEF ključ. Upotreba pečata ide samo iz potpisnog
  servisa, sa posebnim servisnim nalogom, i svaka se beleži.

### 6.6 Priprema dokumenta

| Ulaz | Obrada | Alat |
|---|---|---|
| Sken (TIFF, JPG, PDF) | PDF/A-2b sa OCR slojem | OCRmyPDF (Tesseract + Ghostscript) |
| DOCX/XLSX | PDF/A | LibreOffice u pozadinskom režimu |
| Štampa iz aplikacije (rešenje, radna lista, evidencija prolaza) | HTML → PDF/A, iz zaključanog snimka dokumenta | biblioteka za HTML→PDF (izbor u fazi 3) |
| Svaki PDF/A | provera usklađenosti pre overe | veraPDF |

### 6.7 Tok jednog paketa overe

```
1. Pisarnica skenira ─► Prilog (originalni sken, SHA-256)
2. PDF/A-2b + OCR ─► provera PDF/A
3. KONTROLA DRUGOG LICA: poređenje sa papirom, „istovetno, čitljivo, potpuno"
4. Arhivista bira potvrđene dokumente ─► Paket overe (npr. 480 kom)
5. Worker `potpis`, za svaki dokument:
     heš ─► pečat ─► B-B ─► žig ─► B-T ─► OCSP/CRL ─► B-LT ─► document timestamp ─► B-LTA
     validacija ─► upis: sertifikat, vreme žiga, rok obnove
6. Izveštaj paketa: overeno N, grešaka M (ponovi), zapisnik o overi — i on se overava
7. Dokument ─► skladište na lokalnom serveru;
   papir ─► arhivska jedinica (papir se ne uništava)
```

### 6.8 Fajlovi i skladište

- Posebna putanja (`ARHIVA_STORAGE_ROOT`), ne `/media/`. **Preuzimanje samo kroz view** koji proverava dozvolu i
  obuhvat.
- SHA-256 se računa za izvornik i za overenu verziju. Originalni naziv se čuva.
- Dozvoljeni tipovi: PDF, JPG, PNG, TIFF, DOCX, XLSX.
- Aplikacija nema brisanje overenih fajlova. Uklanja ih samo završeno izlučivanje.
- Skladište je na **lokalnom Windows serveru** (`ARHIVA_STORAGE_ROOT`, npr. poseban disk ili fascikla na serveru).
- Rezervna kopija: najmanje jedna kopija na **drugom disku ili uređaju** u Institutu (ne na istom disku). Kopija van
  zgrade (pravilo 3-2-1) je otvoreno pitanje (O-25). Probno vraćanje svakog kvartala.
- Procena: oko 15.000 akata godišnje × oko 1 MB ≈ **15 GB godišnje** samo za novu poštu. Digitalizacija zatečene
  arhive se procenjuje posebno (O-14).

### 6.9 Pristup

- Arhiva radi **na registru organizacije od prvog dana**:
  - predlog je `PRAVA_PO_REGISTRU["arhiva"] = True`;
  - obuhvat daju odobrene dodele uloga (`organizacija.DodelaUloge`);
  - predmet se vidi po glavnoj ili dodatnoj OJ;
  - `allowed_center_codes` i `allowed_centers` se ne čitaju (AGENTS.md §9, zamka 12).
- Pisarnica, arhivista i komisija imaju obuhvat cele firme.
- Zaduženi referent uvek vidi svoj predmet, kao što autor uvek vidi svoj predmet nabavke.
- Kodovi dozvola su imena ruta, kao u ostatku sistema. Uloge: `arhiva-pisarnica`, `arhiva-arhivista`,
  `arhiva-komisija`, `arhiva-administrator`, a posebno pravo je `arhiva:overa_pokreni`. Uprava automatski dobija sve.

---

## 7. Model podataka

### 7.1 Šifarnici

| Model | Ključna polja |
|---|---|
| `VerzijaListe` | naziv, datum donošenja, broj i datum saglasnosti, važi od, aktivna |
| `GrupaKategorija` | verzija, klasifikaciona oznaka, naziv, redosled |
| `Kategorija` | verzija, grupa, redni broj, naziv, `rok_godina` ili `trajno`, `operativno`, `pocetak_roka`, napomena, `duplikat_od`, **`el_original_dozvoljen`**, **`papir_se_unistava`**, **`cuva_pruzalac`**, aktivna |
| `VrstaAkta` | ulazna/izlazna pošta, interna prepiska, ugovor, ulazna faktura, rešenje, odluka, zapisnik … sa podrazumevanom kategorijom i načinom overe (pečat / lični potpis) |
| `Lokacija` | stablo prostorija → regal → polica → pozicija, kapacitet |

`pocetak_roka` (događaj od kog teče rok): `ZAVRSETAK_PREDMETA` (podrazumevano), `ISTEK_UGOVORA`,
`PRESTANAK_VAZENJA`, `OKONCANJE_POSTUPKA`, `PRESTANAK_ZAKUPA`, `PRESTANAK_RADNOG_ODNOSA`, `RUCNO`.

**Predlog pravila za istek (formula, traži pisanu potvrdu, O-6):**
> Rok teče od 1. januara godine posle događaja. Istek je 31. decembra godine `godina_događaja + rok_godina`.
> Primer: završen 14.05.2026, rok 5 godina → istek 31.12.2031 → kandidat za izlučivanje u 2032.
> „Trajno“ nema istek, nego rok za predaju nadležnom arhivu.

### 7.2 Segment A — pisarnica i delovodnik

| Model | Ključna polja |
|---|---|
| `EvidencionaKnjiga` | vrsta (delovodnik / **poverljivi** / **strogo poverljivi** / **popis akata** / dostavna / otpremna / ulazne fakture / faks), godina, OJ, naziv, za popis akata **rezervisan osnovni broj u delovodniku**, status, zaključenje (ko, kada, broj akata, zabeleška; štampa za pečat i potpis) |
| `BrojacKnjige` | knjiga, poslednji osnovni broj |
| `Predmet` | knjiga, osnovni broj, **delovodni broj**, **datum prijema** (pod njim se zavodi, čl. 13) i vreme zavođenja, naslov, smer, primljen elektronski (da/ne), vrsta akta, pošiljalac ili primalac (Partner / zaposleni / tekst, mesto), broj i datum akta pošiljaoca, **prijemni štambilj** (broj priloga, broj listova, vrednost), glavna i dodatne OJ (čvor registra + snimak koda), zaduženi referent, **kategorija** (+ snimak oznake i roka), **razvod** (datum; oznaka: a/a + rok / R + datum roka / ustupljeno OJ / izvorno + organ), `prenos_iz`, status, napomena, razlog storna |
| `Akt` | predmet, podbroj, datum, opis, smer, zaveo |
| `Prilog` | akt, fajl, originalni naziv, SHA-256, veličina, otpremio, vreme |
| `Dostava` | knjiga, akt, primalac, datum razvođenja, **potvrda prijema** (korisnik i vreme) |
| `Otprema` | akt, datum, primalac, mesto, pošta, način, broj preporuke, masa, vrednost, poštarina, list P-3 |
| `Zaduzenje` | istorija dodele referentima |

```
ZAVEDEN ─► RAZVEDEN ─► U_RADU ─► ZAVRSEN (razvod + obavezna kategorija)
        ─► PREDAT_ARHIVI ─► U_ARHIVI ─► IZLUCEN | PREDAT_NADLEZNOM_ARHIVU
Iz prvih stanja: STORNIRAN (broj ostaje, upisuje se razlog)
```

### 7.3 Segment B — arhiva

| Model | Ključna polja |
|---|---|
| `PredajaArhivi` | broj zapisnika (dobija delovodni broj), OJ, datum, predao, primio, stavke, status, nedostaci |
| `ArhivskaJedinica` | oznaka, vrsta (kutija / fascikla / registrator / el. nosač), godine, OJ, kategorija, **datum isteka** (najkasniji predmet), lokacija, status, sadržaj, **dužni metri** (prepis i izlučivanje, čl. 44 i 51), nalepnica: stvaralac (Institut IMS, naziv i oznaka OJ), godine, sadržaj, broj predmeta i redni broj iz arhivske knjige (čl. 37) |
| `UpisArhivskeKnjige` | redni broj (**nastavlja se iz godine u godinu**), datum upisa, period nastanka, klasifikaciona oznaka i vrsta materijala, sadržaj, količina (broj jedinica), **broj i datum zapisnika** (uništenje ili predaja), **rok čuvanja** iz važeće Liste, prostorija i polica, primedba. **Vodi se i u el. obliku** (Uredba čl. 5; pravilnik čl. 4). Upis do aprila naredne godine. |

### 7.4 Segment C — praćenje i izlučivanje

| Model | Ključna polja |
|---|---|
| `Revers` | jedinica ili predmet, zaposleni, svrha, izdato, rok vraćanja (**najkasnije kraj naredne godine**, čl. 33), vraćeno, stanje; štampa u 3 primerka (čl. 40) |
| `Izlucivanje` | godina, komisija, status (predlog → poslato → saglasnost → uništeno / odbijeno), broj saglasnosti, zapisnik o uništenju, način, izvršilac |
| `StavkaIzlucivanja` | jedinica, kategorija, godine, količina, obrazloženje, izuzeta. **Za papir posle digitalizacije: dokaz da je el. original na nivou LTA i čuva se kako traži kategorija.** |
| `PredajaNadleznomArhivu` | jedinice sa rokom „trajno“ starije od 30 godina (svake pete godine), datum, mesto, popis po godinama, vrsti i količini, ceo fond ili deo, mišljenje o korišćenju, članovi komisije, zapisnik u 5 primeraka (čl. 52–53), potvrda |

### 7.5 Elektronski dokument i overa

| Model | Ključna polja |
|---|---|
| `ElektronskiDokument` | akt, poreklo (digitalizovan / konvertovan / izvorno el. / primljen potpisan), format, fajl, SHA-256 izvornika i overene verzije, status, `rok_obnove` |
| `KontrolaDigitalizacije` | dokument, skenirao (ko, kada), **proverilo drugo lice** (ko, kada, nalaz), oprema i podešavanja, oštećenja originala |
| `PaketOvere` | pokrenuo, način (pečat / lični potpis), broj dokumenata, status, vreme, brojači, zapisnik |
| `Overa` | dokument, paket, tip, potpisnik (iz sertifikata), serijski broj i izdavalac, važi do, nivo, vreme žiga, TSA, **izveštaj validacije** (JSON), rezultat |
| `ObnovaIntegriteta` | dokument, prethodni žig i njegov rok, novi žig, vreme, rezultat |
| `DnevnikArhive` | samo dodavanje. Svaki red nosi heš prethodnog, pa se izmena vidi. Beleži skeniranje, kontrolu, konverziju, overu, obnovu, pregled, preuzimanje, predaju i izlučivanje. |

**15 obaveznih metapodataka** (Uredba o arhivskoj građi, čl. 5) i odakle dolaze:

| Metapodatak | Izvor |
|---|---|
| jedinstveni identifikator | `ElektronskiDokument.pk` + UUID |
| broj predmeta | `Predmet.delovodni_broj` |
| vrsta dokumenta, opis | `VrstaAkta`, `Akt.opis` |
| izvorni oblik (papir / el.) | `ElektronskiDokument.poreklo` |
| format | PDF/A-2b … |
| datum nastanka i potpisa/pečata | `Akt.datum`, `Overa` |
| broj kvalifikovanog sertifikata | `Overa.serijski_broj` |
| rok čuvanja | `Kategorija` |
| datum arhiviranja | prijem u arhivu |
| datum žiga, rok obnove integriteta | `Overa`, `ElektronskiDokument.rok_obnove` |
| status predmeta | `Predmet.status` |
| status dokumenta | `ElektronskiDokument.status` |
| napomena | slobodno polje |

---

## 8. Dokumenti koji već postoje u aplikaciji

Kategorije su **predlog** iz Liste i potvrđuje ih arhivista.

| Izvor | Broj i fajl danas | Šta radi arhiva | Overa | Predlog kategorije |
|---|---|---|---|---|
| **`hr.Zahtev` i `hr.Resenje`** | Broj iz `BrojacZahteva` (`43-17`), rešenje podbroj (`43-17/1`), zaključan snimak teksta | **Preuzima brojač** (6.4). Pri izdavanju rešenja: PDF iz snimka → overa. Paketno za grupna rešenja. | Pečat, ili lični potpis direktora (O-15) | 57 rešenja iz radnog odnosa (trajno); 62 prekovremeni (3 g.); 63 godišnji odmor (2 g.); 64 odsustvo (3 g.) |
| `hr.UgovorZaposlenog` | Broj ugovora, skeniran dokument | Link. Sken prolazi digitalizaciju i overu, ako se tako odluči. | Pečat (istovetnost) | ugovori o radu (trajno) |
| `hr.WorkTimeSheet` + evidencija prolaza | Štampa radne liste i priloga | Zbirne jedinice po mesecu i OJ. Opciono overen PDF lista + priloga. | Pečat | 59 (5 g.) |
| `pravna.DisciplinskiPostupak` | Nema broja | **Daje broj.** Akti postupka su podbrojevi. | Pečat | 45 (10 g. po okončanju); 48, 49 (trajno) |
| `pravna.Postupak` | Sudski broj | Link | — | 44 (5 g.) |
| `ugovori.Contract`, `Offer`, `BusinessRequest` | Brojevi, `file`, `ContractDocument` | Link, fajlovi bez kopiranja. Rok teče od isteka ugovora. | Slučaj C ako je potpisan el., inače digitalizacija | 310/309, 444, 35 (trajno) |
| `nabavka.ProcurementCase`, `PurchaseOrder` | `ZN-…`, broj narudžbenice | Link. Delovodni broj se dodaje uz broj predmeta. | — | 82 (10 g.), 280 (3 g.), 253 (5 g.) |
| `nabavka.ProcurementInvoice` (EUF) | Broj fakture, dobavljač | Knjiga ulaznih faktura je **izveštaj** | — | 195 (10 g.) |
| **`finansije.SefFaktura`** (ulazne i izlazne) | PDF sa SEF-a se već čuva | Link. Slučaj C: provera + žig + LTA, ako se arhivira kod nas (O-16). | Slučaj C | 194/195 (10 g.) |
| `potrazivanja.CollectionNotice`, `CollectionLegalCase` | Broj, štampa | Link. Opomena poštom dobija otpremu. | Pečat (opciono) | 259 (5 g.), 44 |
| `menice.Menica`, `UlaznaMenica` | Serijski broj, lokacija | Link. Postojeće polje lokacije ostaje. | — | 260 (5 g.) |
| `fleet.PutniNalog`, `VehicleTravelOrder` | Brojevi | Zbirno po godini i centru | — | 279 (3 g.), 211 (5 g.) |
| `fleet.TrafficCard`, `Policy`, `Lease` | PDF | Link | — | 236 (5 g.), 35 |

**Namerno se ne linkuje:**
- `finansije.LedgerEntry`: stavke nisu akti, glavna knjiga se čuva zbirno (kategorije 191, 192);
- `naplata.*`: modul se gasi.

**Brisanje izvora:** `pre_delete` signal **samo beleži** brisanje i označava vezu „izvor obrisan“. Snimak i overeni
dokument ostaju. Tvrda zabrana brisanja je odluka O-11.

---

## 9. Ekrani i dozvole

| # | Ekran (ruta = kod dozvole) | Ko | Šta radi |
|---|---|---|---|
| 1 | `arhiva:pisarnica` | Pisarnica | Brzi unos ulazne, izlazne i interne pošte, tastaturom, ~30 s po upisu. Sken i razvođenje u istom koraku. |
| 2 | `arhiva:delovodnik`, `predmet_detail`, `predmet_create`, `akt_add`, `knjiga_zakljuci` | Pisarnica, Uprava | Pretraga, podbroj, storno, štampa Priloga 1, Excel, zaključenje knjige |
| 3 | `arhiva:moji_predmeti`, `dostava_potvrdi` | Svaki zaposleni | Potvrda prijema, rad na predmetu, odgovor (novi podbroj), predlog završetka |
| 4 | `arhiva:predmet_zavrsi` | Referent, rukovodilac | Razvod (a/a + rok, R + datum, ustupljeno, izvorno), **obavezna kategorija** |
| 4a | `arhiva:rokovnik` | Pisarnica, referent | **Rokovnik predmeta** (pravilnik čl. 28): predmeti sa oznakom „R” po datumu roka |
| 4b | `arhiva:predmet_omot`, `predmet_stambilj` | Pisarnica | Štampa **omota predmeta** (čl. 23) i nalepnice **prijemnog štambilja** (čl. 11) |
| 5–6 | `arhiva:predaja_create`, `arhiva:prijem` | Sekretarijat OJ, arhivista | Primopredajni zapisnik, prijem |
| 7–9 | `arhiva:jedinice`, `arhivska_knjiga`, `lokacije` | Arhivista | Kutije i fascikle (nalepnica sa QR kodom), arhivska knjiga (štampa i el. oblik), police |
| 10–11 | `arhiva:reversi`, `arhiva:rokovi` | Arhivista, Uprava | Reversi; rokovi čuvanja, **rokovi obnove žiga**, predmeti bez razvoda |
| 12–13 | `arhiva:izlucivanje`, `predaja_nadleznom` | Komisija, arhivista | Lista za izlučivanje, saglasnost, uništenje; trajna građa za predaju |
| 14 | `arhiva:izvestaji` | Uprava, arhivista | Akti po OJ i mesecu, bez kategorije, opterećenost, stanje arhive, **overeno / čeka overu / greške** |
| E1 | `arhiva:digitalizacija`, `kontrola` | Pisarnica, **drugo lice** | Prijem skenova, PDF/A, kontrola istovetnosti |
| E2 | `arhiva:overa_paketi`, `overa_pokreni`, `overa_detail` | Arhivista (samo uz pravo `overa_pokreni`) | Paket overe, napredak, greške i ponavljanje, zapisnik |
| E3 | `arhiva:dokument_proveri` | Svako ko vidi predmet | Validacija overenog dokumenta i prikaz izveštaja |
| — | `arhiva:sifarnik_*`, `prilog_download`, `dokument_download` | Administrator; prema obuhvatu | Šifarnici; zaštićeno preuzimanje |

---

## 10. Zakazani poslovi

Svaki posao se upisuje u `EXPECTED_PERIODIC_TASKS`, ima Redis zaključavanje kao ostali, a worker se restartuje posle
isporuke.

| Zadatak | Kada | Red | Šta radi |
|---|---|---|---|
| `arhiva.tasks.proveri_rokove` | svaki dan 06:30 | default | Reversi (i rok do kraja naredne godine), predmeti bez razvoda, nepotvrđene dostave, nezavedena ili nedostavljena pošta od juče, **rokovnik** (dospeli „R”), **arhiva pisarnice starija od 2 godine** (za predaju depou), istekli rokovi čuvanja i izlučivanje u roku od godinu dana |
| `arhiva.tasks.podsetnik_arhivske_knjige` | 01.03. i 15.04. | default | Upis materijala iz prethodne godine do aprila i **prepis arhivske knjige do 30.04** (pravilnik čl. 43–44) |
| `arhiva.tasks.proveri_veze` | svaki dan 04:30 | default | Veze čiji izvor više ne postoji |
| `arhiva.tasks.obnovi_zigove` | svaki dan | potpis | Dokumenti kojima `rok_obnove` ističe u narednih N meseci dobijaju novi žig (Pravilnik čl. 7) |
| `arhiva.tasks.proveri_integritet` | nedeljno, u delovima | potpis | Ponovo računa SHA-256. Odstupanje je incident. |
| `arhiva.tasks.revalidiraj` | mesečno, uzorak | potpis | Validacija uzorka overenih dokumenata |
| `arhiva.tasks.podsetnik_zakljucenja` | 20.12. i 31.12. | default | Podsetnik. **Knjiga se ne zaključuje automatski.** |
| `arhiva.tasks.otvori_knjige` | 01.01. u 00:05 | default | Knjige i brojači nove godine |

Obaveštenja se prikazuju u aplikaciji, jer aplikacija nema slanje e-pošte.

---

## 11. Preduslovi u postojećoj aplikaciji

Ovo su zatečena stanja iz AGENTS.md §11. Ne rešavaju se usput, ali pre prvog dokumenta sa pravnom snagom
**moraju** biti rešena, svako kao posebna odluka:

| Stanje | Zašto smeta arhivi | Mera |
|---|---|---|
| `DEBUG = True` u produkciji | Stranice grešaka otkrivaju podatke | Isključiti, uz test produkcije |
| `/media/` dostupan bez prijave | Arhiva ide na posebno skladište, ali ostali fajlovi su i dalje otvoreni | Zaštićeno serviranje |
| Lozinke baze i `SECRET_KEY` u repozitorijumu | Pečat i API ključevi ne smeju završiti tamo | Prelazak na `.env`, rotacija |
| Nema dokumentovanog vraćanja iz kopije | Pravilnik čl. 8 traži visok nivo zaštite od gubitka | Plan rezervnih kopija i probno vraćanje |

---

## 12. Faze implementacije

Svaka faza se isporučuje posebno, sa testovima (`--settings=ims_erp.settings.testing`) i poglavljem u
`dokumentacija/docs/`. Šta mora biti spremno pre svake faze dato je u odeljku 1.

| Faza | Sadržaj | Zavisi od | Rezultat |
|---|---|---|---|
| **0 — Dogovor, pravo, nabavka** | Stavke iz odeljka 1.2 i 1.3, i pokretanje stavki iz 1.4 (ponude, ovlašćena lica, interna pravila). Preduslovi iz odeljka 11. | — | Potvrđen format broja i pravilo roka, očišćena Lista, testni nalog za pečat i žig |
| **1 — Osnova i delovodnik** (koraci 1–2) | Aplikacija `arhiva`, šifarnici, uvoz Liste, knjige, brojač, `zavedi()`, podbroj, storno, zaključenje, ekrani pisarnice i delovodnika, štampa, Excel, zaštićeno preuzimanje, dozvole i obuhvat po registru | 1.2 | Probni rad pisarnice uporedo sa sadašnjim načinom vođenja (programa nema) |
| **2 — Tok predmeta** (koraci 3–4) | Dostavne knjige, potvrda prijema, Moji predmeti, završetak sa obaveznom kategorijom i rokom, otprema i P-3, interna prepiska | 1, 1.3 | Predmet prolazi ceo tok |
| **3 — Potpisni servis** | pyHanko, red i worker `potpis`, klijent pružaoca (pečat, TSA), PAdES-B-LTA, validacija, `Overa`, `DnevnikArhive`, priprema PDF/A, veraPDF | testni nalog (1.4, tačka 13) | Overa 1 i 1.000 testnih dokumenata sa izveštajem validacije |
| **4 — Povezivanje i overa dokumenata iz aplikacije** (slučaj B) | `VezaDokumenta`, adapteri, `{% arhiva_panel %}`, **prelazak brojača zahteva na arhivu**, overa rešenja pri izdavanju i paketno. Zatim disciplinski postupci, ugovori, nabavka, SEF (slučaj C), ostalo. | 1, 3, 1.4 (ugovor, pravila, preduslovi) | Rešenja izlaze kao overen PDF sa delovodnim brojem. Najbrža vidljiva korist. |
| **5 — Digitalizacija i masovna overa** (slučaj A) | Prijem skenova, OCR, PDF/A, **kontrola drugog lica**, paket overe, zapisnik o overi, metapodaci, ekrani E1–E3 | 2, 3, O-8 i O-14 | Pisarnica overava ulaznu poštu paketno |
| **6 — Fizička arhiva** (koraci 5–9) | Primopredaja, prijem, jedinice sa QR nalepnicom, arhivska knjiga (štampa + el. oblik), lokacije | 2 | Arhiva u sistemu |
| **7 — Dugoročno čuvanje** | Obnova žigova, provera integriteta, revalidacija, izveštaj „ističe u 90 dana“, provera rezervne kopije i probno vraćanje. Sve na lokalnom serveru; pružalac čuvanja se ne koristi. | 3, 5 | Ispunjen Pravilnik čl. 5–8 za čuvanje na lokalnom serveru |
| **8 — Praćenje i izlučivanje** (koraci 10–14) | Reversi, rokovi, izlučivanje sa saglasnošću (papir se uništava samo **izlučivanjem po isteku roka**, ne posle digitalizacije), predaja nadležnom arhivu, izveštaji | 6, 7, O-10 | Zatvoren ceo tok |
| **9 — Početak elektronskog delovodnika** | Knjige za 2027. otvorene od broja 1, obuka, izmena IU 03. **Nema uvoza** ranijih godina (programa nema, O-2); ranije evidencije ostaju gde su. **Datum početka: 01.01.2027.** | 1, 2 | Jedan delovodnik, u aplikaciji |

**Okvirni redosled:**
- **pre 01.01.2027:** faze 0, 1, 2 i 9; uporedo 3 i prvi deo faze 4 (rešenja);
- **prvi kvartal 2027:** 5 i ostatak faze 4;
- **tokom 2027:** 6, 7 i 8, kada počne predaja završenih predmeta iz 2027.

---

## 13. Testovi

| Oblast | Obavezni testovi |
|---|---|
| Brojevi | Dva istovremena zavođenja ne dobijaju isti broj. Posle zaključenja knjige nema upisa. Storno čuva broj. Brojevi zahteva posle prelaska nastavljaju niz bez rupe i ponavljanja. |
| Pristup | Korisnik vidi samo predmete u svom obuhvatu (na registru, `override_settings`). Preuzimanje bez dozvole daje 403. |
| Tok i rokovi | Ne može se završiti bez kategorije. Istek se računa za svaku vrstu `pocetak_roka`. Predmet ne može u dve jedinice. |
| Overa | Overen dokument se validira kao PAdES-B-LTA. Izmena jednog bajta ruši validaciju i proveru heša. Paket od 1.000 dokumenata se završava i nastavlja posle prekida. Dokument bez kontrole drugog lica ne ulazi u paket. Nema dvostruke overe. Pružalac se u testovima zamenjuje lažnim klijentom; postoji i jedan ručni test sa testnim sertifikatom. |
| Čuvanje | Obnova žiga se pokreće pre isteka. Dnevnik ne može da se izmeni. Overen fajl ne može da se obriše mimo izlučivanja. |
| Izlučivanje | Kandidat je samo jedinica kojoj je istekao rok, koja nije „trajno“ i nije na reversu. Papir ide u uništenje samo kroz izlučivanje po isteku roka. |
| Veze | Snimak ostaje posle brisanja izvora. Postojeći testovi `hr`, `pravna`, `ugovori` i `finansije` i dalje prolaze. |

---

## 14. Otvorena pitanja

Rokovi i nosioci su u odeljku 1.

| # | Pitanje | Zašto je važno | Pre faze |
|---|---|---|---|
| O-1 | ~~Format delovodnog broja~~ — **odlučeno 05.10.2026.: ide postojeći način brojanja.** Jedan niz osnovnih brojeva za ceo Institut po godini (kao pravilnik čl. 12, 15), uz oznaku OJ (`43-15238`, podbroj `/2`), kao danas u Kadrovima; nema niza po OJ. | — | — |
| O-2 | ~~Iz kog programa je izvezen `Delovodnik 2024.xlsx`~~ — **zatvoreno 05.10.2026.:** programa nema, tabela je bila primer. Nema zamene ni uvoza; elektronski delovodnik počinje 01.01.2027. | — | — |
| O-3 | ~~Treba nam Pravilnik o kancelarijskom i arhivskom poslovanju Instituta~~ — **zatvoreno 05.10.2026.** Važi pravilnik iz 2023 (odeljak 4.5); IU 03 se poziva na zamenjeni pravilnik iz 2005. | — | — |
| O-4 | Da li je **elektronska potvrda prijema** prihvatljiva umesto potpisa u dostavnoj knjizi? Pravilnik traži potpis (čl. 6, 21). **Predlog: da**, uz izmenu pravilnika (4.6, A3). | Od toga zavisi da li papirna dostavna knjiga prestaje | 2 |
| O-5 | Da li se **faks** još koristi? | Knjiga faks poruka | 2 |
| O-6 | **Pravilo za početak roka** i događaj za „trajno operativno“ | Formula, pa traži pisanu potvrdu | 2 |
| O-7 | Sporne stavke Liste: računi 10 ili 5 godina, duplikati, oznaka 426 | Pre uvoza šifarnika | 1 |
| O-8 | Skenira li se **svaki** ulazni akt ili samo neke vrste? | Opterećenje pisarnice i skladišta | 5 |
| O-10 | Ko je komisija za izlučivanje? Nadležni arhiv je po pravilniku **Državni arhiv Srbije** (čl. 51–53); za prepis arhivske knjige pravilnik pominje „nadležni Istorijski arhiv” (čl. 44) — potvrditi (O-24). | Put dokumenata za saglasnost | 8 |
| O-11 | Smeju li se u drugim modulima brisati zapisi zavedeni u delovodnik (samo zabeleška ili zabrana)? | Zabrana menja druge module | 4 |
| O-12 | Da li ćemo sistem za čuvanje voditi **po pravilima ISO/IEC 27001** (interna pravila, procena rizika, pristup, kopije i probno vraćanje, incidenti, dnevnik)? **Sertifikat nije obavezan.** | Uslov za čuvanje na lokalnom serveru (Pravilnik čl. 8). **Obavezno**, jer se sve čuva lokalno (05.10.2026.). | 4 |
| O-13 | ~~Za koje kategorije sme da se uništi papir posle digitalizacije?~~ — **zatvoreno 05.10.2026.:** sve se čuva lokalno, bez kvalifikovane usluge čuvanja, pa se papir **ne uništava** (čl. 48 st. 3, ZEDEIUP čl. 63 st. 4). | — | — |
| O-14 | Da li se digitalizuje i **zatečena arhiva** ili samo nova pošta? | Skeneri, ljudi, troškovi žigova | 5 |
| O-15 | Koji akti traže **lični potpis direktora** (rešenja, odluke, ugovori), a gde je dovoljan pečat Instituta? | Obim udaljenog ličnog potpisa | 4 |
| O-16 | **SEF e-fakture**: da li ih arhiviramo sami ili se oslanjamo na čuvanje na SEF-u? | Proveriti obavezu iz Zakona o el. fakturisanju | 4 |
| O-17 | Da li je IMS obveznik **eArhiv-a** (Uredba o tehničko-tehnološkim zahtevima važi pre svega za organe javne vlasti)? | Ako jeste, predaja ide preko eArhiv-a | 7 |
| O-18 | Budžet: pečat i žig po komadu ili paušalno | Izbor između udaljenog pečata i tokena | 3 |
| O-19 | Da li je Institut **operator važnog IKT sistema** po Zakonu o informacionoj bezbednosti (naučnoistraživačka institucija)? | Obaveze za ceo IT Instituta (odeljak 1.6) | nezavisno |
| O-20 | **Popis akata** (pravilnik čl. 18): za koje vrste se vodi (rešenja o godišnjim odmorima, uverenja, radni nalozi, bolovanja …) i da li zahtevi i rešenja Kadrova idu u popis umesto pod sopstveni osnovni broj? | Menja brojač zahteva (6.4) i broj upisa u delovodniku | 1 |
| O-21 | Da li se vode **poverljivi i strogo poverljivi delovodnik** (čl. 19) i ko ima pristup? | Posebne knjige i dozvole | 1 |
| O-22 | Da li se el. primljena pošta i dalje **štampa** pre zavođenja (čl. 6 st. 3), ili se pravilnik menja? **Predlog: menja se** (4.6, A2). | Od toga zavisi da li je el. akt original u predmetu | 2 |
| O-23 | Treba nam **Pravilnik o načinu evidentiranja, zaštite i korišćenja elektronskih dokumenata Instituta** (pravilnik čl. 3) | Uslovi za el. dokumente, overu i čuvanje | 3 |
| O-24 | Ispraviti nedoslednosti pravilnika: „P” ili „R” za rok (čl. 15 i 26), koji arhiv dobija prepis arhivske knjige (čl. 44), prazna tačka 5 u čl. 37 | Sistem prati jednu oznaku i jedan arhiv | 2 |
| O-25 | **Spoljna rezervna kopija** (van zgrade): da li, gde i kako (drugi objekat, iznajmljen prostor, oblak) — „videćemo”, 05.10.2026. | Bez nje požar ili krađa servera uništava i el. dokumente i njihovu kopiju u zgradi | 7 |

(O-9 iz plana od 23.09. — da li je sken samo radna kopija — rešava ovaj plan: sken je radna kopija dok ne prođe
kontrolu i overu, a posle toga je elektronski dokument sa dokaznom snagom.)

---

## 15. Rizici

| Rizik | Mera |
|---|---|
| Unos sporiji od sadašnjeg načina vođenja (~60 upisa dnevno) | Ekran za tastaturu, podrazumevane vrednosti, probni rad |
| Kategorija se opet ne popunjava (kao 2024) | Obavezna pri završetku, predlog iz vrste akta, izveštaj „bez kategorije“ |
| Dupli delovodni brojevi | Zaključavanje brojača, unique ograničenje, test istovremenog zavođenja |
| Odluke iz odeljka 1.2 kasne, pa nema vremena za probni rad do 01.01.2027 | Kod počinje bez odluka (kostur, šifarnik, brojač iz podešavanja). Ako odluke kasne posle 31.10.2026, prelazak se pomera na 01.01.2028. Knjiga se ne deli usred godine. |
| **Overa bez stvarne provere skena** | Kontrola drugog lica kao uslov, ponovna provera uzorka, zapisnik navodi ko je proverio |
| **Istekne žig, dokument izgubi dokaznu snagu** | `rok_obnove`, dnevni posao, izveštaj „ističe u 90 dana“ |
| **Gubitak ili izmena fajlova na lokalnom serveru** | Skladište bez brisanja, SHA-256, nedeljna provera, kopija na drugom disku ili uređaju, probno vraćanje; spoljna kopija (O-25). Papirni original se čuva, pa se el. dokument u krajnjem slučaju može ponovo digitalizovati i overiti. |
| **Kompromitovan pristup pečatu** | Tajne van repozitorijuma, poseban servisni nalog, pečat samo iz potpisnog servisa, dnevnik svake upotrebe |
| Pružalac pečata ili žiga prestane sa radom ili poskupi | Standardni formati (PDF/A + PAdES) čitljivi bilo kojim alatom, kopija kod nas, ugovorni izvoz |
| Selenium ili sinhronizacije blokiraju overu | Poseban red i worker `potpis` |
| Izvorni zapis obrisan ili izmenjen | Snimak u `VezaDokumenta`, noćna provera, `pre_delete` beleženje |
| Promena Liste posle nove saglasnosti | Verzionisan šifarnik. Predmet zadržava rok iz verzije važeće pri završetku. |
| Rast skladišta | Posebna putanja, praćenje veličine, procena pre digitalizacije zatečene arhive |

---

## Izvori

- [Zakon o elektronskom dokumentu, elektronskoj identifikaciji i uslugama od poverenja u elektronskom poslovanju](https://www.paragraf.rs/propisi/zakon-o-elektronskom-dokumentu-elektronskoj-identifikaciji-i-uslugama-od-poverenja-u-elektronskom-poslovanju.html)
- [Pravilnik o uslovima i tehnološkim rešenjima za pouzdano elektronsko čuvanje dokumenata](https://www.paragraf.rs/propisi/pravilnik-uslovi-tehnoloska-resenja-pouzdano-elektronskog-cuvanja-dokumenata.html)
- [Uredba o uslovima za pripremu dokumenata za pouzdano elektronsko čuvanje i formatima dokumenata](https://www.paragraf.rs/propisi/uredba-uslovi-priprema-dokumenata-za-pouzdano-elektronsko-cuvanje-formati-dokumenata.html)
- [Uredba o tehničko-tehnološkim zahtevima i procedurama za čuvanje i zaštitu arhivske građe i dokumentarnog materijala u elektronskom obliku](https://www.paragraf.rs/propisi/uredba-tehnicko-tehnoloskim-zahtevima-procedurama-za-cuvanje-i-zastitu-arhivske-gradje.html)
- [Zakon o arhivskoj građi i arhivskoj delatnosti](https://www.paragraf.rs/propisi/zakon-o-arhivskoj-gradji-i-arhivskoj-delatnosti.html)
- [Zakon o informacionoj bezbednosti (2025) — publikacija PARS sa tekstom zakona](https://www.pars.rs/public/Dokumenti/Publikacije/1955/Zakon-o-informacionoj-bezbednosti-Republike-Srbije.pdf)
- [Paragraf — Šta je elektronsko arhiviranje, pitanja i odgovori](https://www.paragraf.rs/kancelarko/pitanja-odgovori-elektronsko-arhiviranje.html)
- [Registar pružalaca kvalifikovanih usluga od poverenja](https://mit.gov.rs/tekst/sr/583/registar-pruzalaca-kvalifikovanih-usluga-od-poverenja-.php)
- [TIM ERP — elektronsko arhiviranje i arhivska knjiga (primer drugog ERP-a)](https://www.tim-erp.com/ERPX_WEB/L36/helpPage.awp?P1=237)
