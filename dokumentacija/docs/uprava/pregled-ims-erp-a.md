# IMS ERP — pregled za upravu

**Datum:** 18.09.2026.
**Obuhvat:** stanje sistema utvrđeno pregledom izvornog koda i baze podataka

---

## 1. Šta je IMS ERP

IMS ERP je **interna aplikacija Instituta IMS** koja na jednom mestu objedinjuje
evidencije i analize iz deset poslovnih oblasti. Zaposleni joj pristupaju pregledačem,
sa jednom prijavom, a svako vidi samo ono za šta ima ovlašćenje.

Sistem je nastao postepeno, iz potrebe da se podaci koji su ranije vođeni u
**Excel tabelama i papirnim evidencijama** objedine i povežu sa postojećim
knjigovodstvenim sistemom.

### Šta sistem radi

1. **Vodi evidencije** kojih ranije nije bilo — vozni park, garaža, ugovori, menice,
   mobilni telefoni, ocenjivanje zaposlenih.
2. **Preuzima podatke** iz postojećih sistema i sa portala dobavljača, automatski,
   svake noći.
3. **Računa i prikazuje** rezultate poslovanja, troškove i dugovanja.
4. **Kontroliše** ispravnost podataka i upozorava na ono što traži radnju.

### Šta sistem ne radi

| Ne radi | Ko to radi |
|---|---|
| Ne knjiži | Postojeći knjigovodstveni sistem |
| Ne obračunava zarade | Postojeći sistem za zarade |
| Ne izdaje fakture | Postojeći poslovni sistem |
| Ne vodi magacin | Postojeći poslovni sistem |

**IMS ERP pre svega čita, povezuje, kontroliše i analizira** podatke koji nastaju drugde.

---

## 2. Šta je realizovano

### Deset modula u radu

| Modul | Šta vodi |
|---|---|
| **Vozni park** | Vozila kroz ceo životni ciklus — dokumenta, gorivo, servisi, garaža, putni nalozi |
| **Kadrovi** | Zaposleni, radne liste, godišnji odmori, bolovanja, ocenjivanje |
| **Finansijska analitika** | Rezultat po šifri posla i centru, tok gotovine |
| **Nabavka** | Zahtevi, fakture, plan javnih nabavki, narudžbenice |
| **Potraživanja** | Dugovanja kupaca po starosti, opomene, pravni postupci |
| **Ugovori** | Partneri, zahtevi, ponude, ugovori, aneksi, garancije |
| **Menice** | Ulazne i izlazne menice |
| **Mobilna telefonija** | Službeni brojevi i obustave iz zarada |
| **Isplate** | Nalozi za banku |
| **Administracija** | Korisnici, ovlašćenja, evidencija rada |

### Sistem u brojkama

| Pokazatelj | Vrednost |
|---|---|
| Poslovnih modula u radu | **10** |
| Korisničkih stranica | oko **195** |
| **Obračuna i analiza** | **74** |
| Evidencija u bazi | **118** |
| Podataka koji se preuzimaju iz drugih sistema | **37 izvora** |
| Automatskih noćnih poslova | **18** |
| Provera ispravnosti koje rade same | **550** |

---

## 3. Koje poslove aplikacija podržava

| Poslovni proces | Šta se dobilo |
|---|---|
| **Popravka vozila** | Od prijave kvara, preko zahteva za nabavku, do fakture i troška pripisanog vozilu |
| **Službeno putovanje** | Od izdavanja naloga do **naloga za banku** — bez ručnog kucanja |
| **Zaduženje vozila** | Ko je koristio vozilo, koliko prešao i koliko goriva potrošio |
| **Mesečni obračun mobilnih** | Iznos koji se obustavlja od zarade, spreman za obračun |
| **Radna lista i ocenjivanje** | Sati po šiframa posla i ocena sa tri potpisa |
| **Naplata potraživanja** | Ko duguje, koliko dugo i šta je preduzeto |
| **Zaključenje ugovora** | Od zahteva do ugovora sa sredstvima obezbeđenja |
| **Praćenje rezultata** | Rezultat posla i centra, sa svim evidencijama koje ga čine |

---

## 4. Šta se automatizovalo

Poslovi koji su se ranije radili ručno, a sada se izvršavaju **sami, svake noći**:

| Posao | Bilo | Sada |
|---|---|---|
| **Preuzimanje podataka o gorivu** | Ručno preuzimanje sa portala NIS i OMV, pa unos | Automatski, svake noći |
| **Preuzimanje knjiženja** | Čekanje na obračun u knjigovodstvu | Svakog sata |
| **Evidencija zaposlenih** | Ručno ažuriranje | Svake noći iz kadrovske baze |
| **Šifre poslova i centri** | Ručno | Svake noći |
| **Polise osiguranja** | Ručni unos sa faktura | Automatski iz faktura |
| **Servisi i trebovanja** | Ručno povezivanje sa vozilom | Automatski preuzimanje, ručna samo dopuna |
| **Nalozi za banku** | Ručno kucanje svakog naloga | Datoteka koja se učitava u e-bankarstvo |
| **Provera partnera** | Ručna provera u APR-u | Preuzimanje iz javnog registra |
| **Podaci o menicama** | Ručno prepisivanje iz registra NBS | Automatsko preuzimanje |

---

## 5. Šta aplikacija računa

Sistem izvodi **74 obračuna**. Najvažniji, po poslovnom značaju:

### Za upravu i rukovodioce

| Obračun | Odgovara na pitanje |
|---|---|
| **Rezultat po šifri posla i centru** | Koliko je koji posao zaradio ili izgubio |
| **Zajednički troškovi** | Koliko opštih troškova pada na koji posao |
| **Tok gotovine** | Koliko je novca ušlo i izašlo |
| **Trošak po kilometru** | Koliko stvarno košta svako vozilo |
| **Ocena isplativosti vozila** | Koja vozila više ne isplati zadržavati |
| **Presek stanja flote** | Koliko vozila imamo, gde su, koliko vrede, šta traži radnju |
| **Starosna struktura dugovanja** | Ko duguje i koliko dugo |

### Za obračun zarada

| Obračun | Šta daje |
|---|---|
| **Lični koeficijent** | Množilac za zaradu, iz mesečne ocene sa tri potpisa |
| **Obustave za mobilne telefone** | Iznos koji zaposleni plaća iznad paketa |
| **Radna lista** | Sati po šiframa posla |

### Za operativu

Prosečna potrošnja goriva, gorivo po šifri posla, mesečni troškovi polisa, lizinga i
servisa, kilometraža vozila, evidencija održavanja, i **20 izveštaja Flote**.

---

## 6. Ko koristi sistem

| Organizaciona celina | Šta dobija |
|---|---|
| **Uprava** | Rezultat firme, centara i poslova; izveštaji o floti |
| **Rukovodioci centara** | Rezultat i troškovi svog centra |
| **Služba voznog parka** | Kompletna evidencija vozila i troškova |
| **Garaža** | Prijave kvarova, radni nalozi, trebovanja |
| **Kadrovska služba** | Zaposleni, odsustva, ocenjivanje |
| **Finansije** | Analitika, menice |
| **Služba nabavke** | Predmeti nabavke, fakture, plan javnih nabavki |
| **Služba naplate** | Dugovanja, opomene, postupci |
| **Pravna služba** | Ugovori, garancije, sudski postupci |
| **Sekretarijat** | Putni nalozi |
| **Blagajna** | Nalozi za banku |
| **Svi zaposleni** | Svoja radna lista, svoj profil, zaduženje vozila |

---

## 7. Veza sa drugim sistemima

Sistem razmenjuje podatke sa **devet spoljnih izvora**:

| Izvor | Šta se razmenjuje |
|---|---|
| **Knjigovodstveni sistem** | Knjiženja, šifarnici, partneri — **samo čitanje** |
| **Sistem za obračun zarada** | Podaci o zaradama i godišnjim odmorima — samo čitanje |
| **Sistem kontrole pristupa** | Prolasci zaposlenih kroz čitače kartica |
| **NIS i OMV** | Transakcije sa kartica za gorivo |
| **Narodna banka Srbije** | Registar menica |
| **APR** | Status privrednih subjekata |
| **RFZO** | Bolovanja (mesečno, ručni unos datoteke) |
| **Operater mobilne telefonije** | Paketi i potrošnja (mesečno, ručni unos) |
| **Poslovna banka** | **Nalozi za plaćanje** — jedini izlaz iz sistema |

---

## 8. Kontrole i sledljivost

Sistem je postavljen tako da **greška bude vidljiva, a ne skrivena**.

| Kontrola | Šta znači |
|---|---|
| **Provera pre objave podataka** | Finansije i Potraživanja porede preuzeto sa izvorom. **Ako se ne slaže, ništa se ne objavljuje** i ostaje prethodno stanje |
| **Ništa se ne briše** | Podatak koji nestane iz izvora označava se kao neaktivan, ali ostaje vidljiv |
| **Evidencija rada** | Beleži se ko je, kada i šta otvorio ili promenio, sa koje adrese |
| **Istorija automatskih poslova** | Za svaki noćni posao vidi se da li je prošao, koliko je trajao i šta je bila greška |
| **Nepromenljive ocene** | Ocena zaposlenog se ne može izmeniti — ispravka je nova verzija, a prethodna ostaje |
| **Snimci stanja potraživanja** | Moguće je videti kako je stanje izgledalo ranijeg datuma |
| **Ovlašćenja po ekranu** | Svaki ekran ima svoje ovlašćenje; pristup se dodatno ograničava po centrima |

---

## 9. Šta je Institut dobio

| Korist | Objašnjenje |
|---|---|
| **Rezultat posla dostupan odmah** | Ranije se čekao obračun u knjigovodstvu |
| **Trošak vozila poznat po vozilu** | Ranije se video samo zbirno, kroz knjiženja |
| **Ocena isplativosti vozila** | Osnov za odluku o zameni ili prodaji |
| **Uklonjen ručni rad** | Gorivo, knjiženja, zaposleni, polise — sve se preuzima samo |
| **Nalozi za banku bez kucanja** | Smanjen rizik greške pri isplati |
| **Evidencije kojih nije bilo** | Garaža, ugovori, menice, mobilni telefoni, ocenjivanje |
| **Sledljivost** | Za svaki podatak se zna odakle je i ko ga je menjao |
| **Jedinstvena prava pristupa** | Jedna prijava, jedan sistem ovlašćenja |

---

## 10. Trenutna ograničenja

Navedeno otvoreno, jer utiče na način korišćenja:

| Ograničenje | Šta znači u praksi |
|---|---|
| **Podaci nisu u realnom vremenu** | Većina se osvežava jednom dnevno. Ujutru se vidi stanje od sinoć |
| **Zavisnost od tri udaljena servera** | Ako neki nije dostupan, Finansije i radne liste ne rade |
| **Zavisnost od portala dobavljača goriva** | Promena njihove stranice zaustavlja automatsko preuzimanje. Postoji ručni unos kao zamena |
| **Nema povratne veze ka knjigovodstvu** | Rezultati se prenose ručno, osim naloga za banku |
| **Rezultati se ne pamte** | Skoro svi obračuni se rade u trenutku prikaza. Izveštaj otvoren danas i za mesec dana može dati različit rezultat za isti period |
| **Dva sistema za naplatu rade uporedo** | Stari se gasi, novi ga zamenjuje |
| **Deo pravila je u programskom kodu** | Njihova izmena traži programera, umesto da je izmeni sama služba |

---

## 11. Utvrđeni rizici

Pregledom je utvrđeno **45 stavki** koje treba rešiti. Ovde su navedene samo one sa
poslovnim uticajem.

### Rizici koji daju pogrešan broj

| # | Šta je utvrđeno | Posledica |
|---|---|---|
| 1 | **Cela godišnja premija osiguranja** ulazi u svaki period, bez obzira na dužinu | Trošak vozila po kilometru je **precenjen** — za tromesečni period i do četiri puta |
| 2 | **Cela godišnja kamata lizinga** ulazi isto tako | Isti učinak |
| 3 | **Zbir faktura** na izveštaju Nabavke sabira istu fakturu više puta | Prikazani iznos može biti **višestruko veći** od stvarnog |
| 4 | **Prosečna potrošnja goriva** može biti prikazana desetostruko manja | Pogrešan zaključak o vozilu |
| 5 | **Mesečni izveštaj lizinga** prikazuje ugovor samo u mesecu potpisivanja | Izveštaj ne pokazuje mesečni trošak |

> **Olakšavajuća okolnost:** za četiri od pet navedenih, **ispravno rešenje već postoji
> u samom sistemu**, u drugom delu. Nije potrebno izmišljati nova pravila — dovoljno ih
> je preneti.

### Rizici u vezi sa tragom i bezbednošću

| # | Šta je utvrđeno | Posledica |
|---|---|---|
| 6 | **Lozinke baze podataka nalaze se u projektnoj dokumentaciji koda** | Svako ko ima pristup kodu ima pristup i podacima |
| 7 | **Iznos obustave za mobilne se nigde ne čuva** | Ne postoji odgovor na pitanje koji je iznos prosleđen u zarade |
| 8 | **Sadržaj naloga poslatog banci se ne čuva** | Kod neslaganja sa izvodom nema dokaza šta je poslato |
| 9 | **Jedno poslovno pravilo upisano je u kod** umesto u evidenciju | Potvrđeno kao greška; izmena traži programera |

### Rizici u vezi sa doslednošću

| # | Šta je utvrđeno | Posledica |
|---|---|---|
| 10 | **Promena centra menja i prošle izveštaje** | Izveštaj za prošlu godinu može se promeniti bez ijedne izmene u knjiženjima |
| 11 | **Dva različita obračuna radnih sati** iz iste evidencije prolazaka | Zaposleni i pregled prisustva mogu pokazati različit broj sati |
| 12 | **Formule 11 izveštaja postoje samo u bazi** | Rezultat se može promeniti bez traga u sistemu |

---

## 12. Preporuke

### Odmah

| # | Preporuka | Zašto |
|---|---|---|
| 1 | **Ispraviti pet obračuna koji daju pogrešan broj** | Rešenje već postoji u sistemu; zahvat je mali, a uticaj velik |
| 2 | **Premestiti lozinke iz koda** i isključiti razvojni režim | Bezbednost podataka |
| 3 | **Preuzeti i sačuvati definicije 11 izveštaja iz baze** | Dogovoreno; bez toga se ne može objasniti odakle iznos |

### U narednom periodu

| # | Preporuka | Zašto |
|---|---|---|
| 4 | **Sačuvati ono što se šalje** — nalog banci i obustave | Da postoji dokaz šta je i kada prosleđeno |
| 5 | **Preseliti poslovna pravila iz koda u evidencije** | Da ih menja služba, a ne programer |
| 6 | **Sprovesti planiranu centralizaciju organizacije i ovlašćenja** | Rešava četiri utvrđena problema odjednom |
| 7 | **Odrediti datum gašenja starog sistema naplate** | Dva sistema uporedo su trošak i rizik |

### Trajno

| # | Preporuka | Zašto |
|---|---|---|
| 8 | **Odrediti vlasnika svakog podatka** — ko odobrava izmene u bazi | Izmena pogleda danas menja izveštaje bez traga |
| 9 | **Potvrditi kako rezultati ulaze u knjiženje** | Nije zabeleženo ni u jednom dokumentu |
| 10 | **Odrediti odgovorne osobe po modulima** | Da se zna kome se obratiti |

---

## 13. Zaključak

IMS ERP je **u punom radu i pokriva deset poslovnih oblasti**. Zamenio je veći broj
odvojenih Excel evidencija, automatizovao poslove koji su se radili ručno i dao uvid
u rezultat poslovanja koji ranije nije bio dostupan bez obračuna u knjigovodstvu.

Sistem je izgrađen sa **ozbiljnim kontrolama** — proverava preuzete podatke pre nego što
ih objavi, ne briše ono što nestane iz izvora i beleži trag svake radnje. Na više mesta
**radije ne prikaže podatak nego da prikaže onaj za koji zna da je pogrešan**.

Pregled je utvrdio i **45 stavki koje treba rešiti**. Od njih **pet direktno daje
pogrešan poslovni broj**, a za četiri postoji ispravno rešenje već u samom sistemu.
Nekoliko rizika tiče se **čuvanja traga o onome što je poslato banci i u obračun zarada**.

**Preporuka:** rešiti prvo pet obračuna koji daju pogrešan broj i preseliti lozinke iz
koda. To su kratki zahvati sa velikim uticajem. Zatim sprovesti već pripremljen plan
centralizacije organizacije i ovlašćenja, koji sam rešava četiri utvrđena problema.

---

## Prilozi

| Dokument | Za koga |
|---|---|
| [Pregled sistema](../01-pregled-sistema.md) | Svi |
| [Moduli](../03-moduli.md) | Poslovni korisnici |
| [Poslovni procesi](../05-poslovni-procesi.md) | Poslovni korisnici |
| [Analize i obračuni](../06-analize-i-obracuni.md) | Svi — kako se svaki iznos računa |
| [Registar problema](../10-poznati-problemi.md) | Programeri i uprava |
| [Plan razvoja](../11-plan-razvoja.md) | Uprava |
| [Rečnik pojmova](../12-recnik-poslovnih-pojmova.md) | Svi |
