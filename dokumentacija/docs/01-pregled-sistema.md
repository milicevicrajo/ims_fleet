# 1. Pregled sistema

> **Za koga je ovo poglavlje:** za sve — poslovne korisnike, programere i rukovodstvo.
> Objašnjava šta IMS ERP radi, ko ga koristi i kako se uklapa u postojeće poslovanje.
> Tehnički detalji su u [2. Arhitektura](02-arhitektura.md).

---

## 1.1. Šta je IMS ERP

IMS ERP je **interna web aplikacija Instituta IMS a.d.** koja objedinjuje evidencije i
analize iz deset poslovnih oblasti u jedan sistem sa jedinstvenom prijavom, jedinstvenim
šifarnikom organizacionih jedinica i jedinstvenim pravilima pristupa.

Sistemu se pristupa pregledačem, sa adrese na internoj mreži. Nema mobilne aplikacije,
nema javnog pristupa sa interneta i nema programskog interfejsa (API) za spoljne sisteme.

### Šta sistem nije

Da bi očekivanja bila realna, važno je reći i šta IMS ERP **ne radi**:

| Ne radi | Ko to radi |
|---|---|
| Ne knjiži | Knjigovodstveni sistem na `PUTGEO-SERVER` |
| Ne obračunava zarade | Sistem za obračun zarada (`bazaldims`) |
| Ne izdaje fakture | Postojeći poslovni sistem |
| Ne vodi magacinsko poslovanje | Postojeći poslovni sistem |
| Ne šalje podatke na SEF | Postojeći poslovni sistem |

**IMS ERP je pre svega sistem koji čita, povezuje, kontroliše i analizira** podatke koji
nastaju drugde, i dodaje sopstvene evidencije tamo gde ih raniji sistemi nisu imali
(vozni park, garaža, ugovori, menice, mobilni telefoni, ocenjivanje zaposlenih).

Izuzeci — mesta gde IMS ERP **stvara** podatak koji ide dalje:

1. **Virman za banku** — datoteka za elektronsko bankarstvo (modul Isplate).
2. **Obustave za mobilne telefone** — iznos koji ulazi u obračun zarada (modul Mobilni).
3. **Ocena zaposlenog** — stimulacija i lični koeficijent (modul Kadrovi).
4. **Radna lista** — evidencija sati po šiframa posla (modul Kadrovi).

---

## 1.2. Koji poslovni problem rešava

| Problem pre sistema | Kako ga IMS ERP rešava |
|---|---|
| Evidencija vozila vođena u Excel tabelama, bez istorije | Jedinstvena evidencija vozila sa istorijom saobraćajnih, šifara posla, osnova raspolaganja i kilometraže |
| Trošak vozila poznat tek kroz knjiženja, bez veze sa vozilom | Trošak po vozilu i po kilometru, sa pragovima i oznakom „crvene zone“ |
| Podaci o gorivu ručno preuzimani sa portala dobavljača | Automatsko noćno preuzimanje sa NIS i OMV portala |
| Rezultat po šifri posla poznat tek posle obračuna u knjigovodstvu | Dnevno osvežena finansijska analitika po šifri posla i centru |
| Zajednički troškovi i tok gotovine računati ručno po proceduri | Isti obračun dostupan na ekranu, bez pokretanja poslovnih procedura |
| Dugovanja kupaca u odvojenoj bazi, bez istorije kontakata | Potraživanja sa starosnom strukturom, kontaktima, opomenama i pravnim postupcima |
| Ugovori i menice u registratorima | Evidencija ugovora, aneksa, garancija i menica, sa vezama i rokovima |
| Zahtevi za nabavku na papiru | Elektronski predmet nabavke sa stavkama, fakturama i statusima |
| Trošak mobilne telefonije bez veze sa zaposlenim | Obustava po zaposlenom, spremna za obračun zarada |
| Radne liste i odmori u papiru i Excel-u | Radna lista sa predlogom sati iz evidencije prolazaka |

---

## 1.3. Ko koristi sistem

> **Status: [Z] zaključeno iz uloga u kodu.** Konačnu potvrdu službi i odgovornih lica
> treba dati naručilac (pitanje **Q2** u inventaru).

| Organizaciona celina | Moduli koje koristi | Šta dobija |
|---|---|---|
| **Služba voznog parka** | Flota | Evidencija vozila, dokumenata, troškova; izveštaji o gorivu i održavanju |
| **Garaža** | Flota (garaža), Nabavka | Prijave kvarova, radni nalozi, trebovanja, zahtevi za nabavku |
| **Kadrovska služba** | Kadrovi | Zaposleni, radne liste, odmori, bolovanja, ocenjivanje |
| **Finansije** | Finansijska analitika, Menice | Rezultat po šifri posla, tok gotovine, evidencija menica |
| **Služba nabavke** | Nabavka, Ugovori | Predmeti nabavke, fakture, plan javnih nabavki, narudžbenice |
| **Služba naplate** | Potraživanja | Dugovanja po starosti, opomene, kontakti, pravni postupci |
| **Pravna služba** | Ugovori, Potraživanja (pravni postupci) | Ugovori, aneksi, garancije, sudski postupci |
| **Sekretarijat** | Flota (putni nalozi), Kadrovi | Izdavanje i štampa putnih naloga |
| **Blagajna** | Isplate | Virmani za neoporeziva primanja |
| **Administracija** | Mobilni, Administracija | Mobilni telefoni i obustave; korisnici i dozvole |
| **Rukovodioci centara** | Finansijska analitika, izveštaji Flote | Rezultat svog centra, troškovi vozila |
| **Uprava** | Svi moduli | Zbirni pregledi i izveštaji |
| **Svi zaposleni** | Kadrovi (svoj profil), Flota (zaduženje vozila) | Sopstvena radna lista, CV, otvaranje putnog naloga vozila |

---

## 1.4. Moduli — šta koji radi

### Flota (vozni park)

Najveći modul. Vodi kompletan životni ciklus vozila:

- **Vozilo i dokumenti** — tehnički podaci, saobraćajne dozvole (sa istorijom registarskih
  oznaka), slike, tenderska dokumentacija.
- **Raspolaganje** — vlasništvo IMS ili korišćenje po ugovoru (lizing, dugoročni najam),
  sa istorijom perioda koji se ne smeju preklapati.
- **Osiguranje** — polise i knjiženja osiguranja, praćenje isteka i neobnovljenih polisa.
- **Gorivo** — transakcije sa kartica NIS i OMV, prosečna potrošnja, trošak po šifri posla.
- **Održavanje** — servisi, trebovanja delova, servisni intervali.
- **Garaža** — prijave kvarova, radni nalozi, trebovanja materijala, zahtevi za nabavku.
- **Putni nalozi** — službena putovanja zaposlenih i zaduženja vozila.
- **Analitika** — trošak po kilometru, pragovi po masi vozila, presek stanja flote.

### Kadrovi

- **Zaposleni** — evidencija sinhronizovana iz kadrovske baze, sa CV stavkama.
- **Radna lista** — mesečna evidencija sati po šiframa posla, sa predlogom sati iz
  evidencije prolazaka kroz sistem kontrole pristupa.
- **Godišnji odmori** — dodele i rešenja preuzeti iz izvora.
- **Bolovanja** — uvoz iz RFZO izvoza, povezivanje po matičnom broju.
- **Ocenjivanje** — merila, bodovi, koeficijent stimulacije, saglasnost u tri nivoa
  (neposredni rukovodilac → direktor centra → generalni direktor).

### Finansijska analitika

Dnevno osvežena slika poslovanja po šifri posla i centru:
prihodi, rashodi, rezultat, zajednički troškovi, rezultat posle raspodele,
priliv, odliv i neto gotovina, uz detalj sa fakturama, kontima, vozilima, zaposlenima,
putnim nalozima i potraživanjima.

### Nabavka

Predmeti nabavke (zahtev za nabavku, zahtev za uslugu, predlog za opremu), stavke,
povezivanje sa ulaznim fakturama i robom, ugovori, narudžbenice, plan javnih nabavki
sa verzijama i razlikama između verzija, alarmi.

### Potraživanja

Dugovanja kupaca sa starosnom strukturom, objavljeni snimci stanja, kontakti,
telefonski pozivi, opomene, pozivna pisma i pravni postupci.
**Zamenjuje nasleđeni modul Naplata.**

### Ugovori

Partneri (sa proverom statusa u APR-u), zahtevi, ponude, ugovori i aneksi,
dokumenti uz ugovor, stranke, garancije i veze sa menicama.

### Menice

Ulazne i izlazne menice, sa mogućnošću preuzimanja podataka iz Registra menica
Narodne banke Srbije.

### Mobilna telefonija

Paketi, korisnici, dodele brojeva po mesecima, potrošnja i **obračun obustave po
zaposlenom** koja ide u obračun zarada.

### Isplate

Generisanje datoteke virmana za elektronsko bankarstvo, za neoporeziva primanja
zaposlenih po putnim nalozima.

### Administracija

Korisnici, uloge i dozvole, evidencija rada korisnika (ko je šta otvorio i promenio),
istorija zakazanih poslova.

---

## 1.5. Sistem u brojkama

| Pokazatelj | Vrednost |
|---|---|
| Poslovnih modula | 10 (+1 nasleđeni u gašenju) |
| HTML šablona | 280 — od toga 222 stranice i 58 delova stranica |
| Stranica u obuhvatu dokumentacije | ~195 (bez nasleđene Naplate) |
| Dokumentovanih obračuna i analiza | 74 (+11 izveštaja nad pogledima baze) |
| Django tabela (sopstvenih) | 118 |
| Django modela nad nasleđenim pogledima (bez sopstvene tabele) | 13 |
| Nasleđenih pogleda i tabela koje sistem čita | 37 |
| Povezanih servera | 3 |
| Spoljnih sistema sa kojima se razmenjuju podaci | 9 |
| Zakazanih pozadinskih poslova | 18 |
| Predefinisanih uloga | 11 |
| Automatskih testova | 550 |

---

## 1.6. Radni dan sistema

```
01:00  Sinhronizacija dozvola
01:10  Zaposleni iz kadrovske baze
01:20  Provera otpisanih vozila
01:30  Šifre poslova i organizacione jedinice
01:45  Trebovanja
02:00  Polise osiguranja
02:20  EUF fakture (nabavka)
02:45  UF stavke (nabavka)
03:15  Servisi vozila
03:35  Knjiženja osiguranja DDOR
03:50  Finansije — sve godine od 2025.
04:20  Gorivo — NIS
05:10  Gorivo — OMV putnička vozila
06:10  Gorivo — OMV teretna vozila
07:10  Roba (nabavka)
       ── radni dan ──
10:00  Osvežavanje lokalne kopije nalog_z
11:00  Osvežavanje lokalne kopije nalog_z
12:30  Isplaćeni iznosi po putnim nalozima
:20    Svakog sata — finansije, tekuća godina
```

Korisnik ujutru zatiče podatke preuzete tokom noći. Sve što je zavisno od spoljnih
portala (gorivo) stiže do 07:10.

---

## 1.7. Šta ograničava sistem

> Detaljno u [10. Poznati problemi](10-poznati-problemi.md).

1. **Zavisnost od tri udaljena servera.** Finansije i Kadrovi ne rade ako povezani
   server nije dostupan. To nije greška aplikacije, ali korisnik to tako doživljava.
2. **Zavisnost od portala dobavljača goriva.** Promena izgleda stranice NIS-a ili OMV-a
   zaustavlja automatsko preuzimanje.
3. **Podaci nisu u realnom vremenu.** Većina se osvežava jednom dnevno.
4. **Nema povratne veze ka knjigovodstvu.** Rezultati se prenose ručno, osim virmana.
5. **Definicije nasleđenih pogleda nisu deo projekta.** Promena pogleda u bazi menja
   rezultat na ekranu bez ijedne izmene u aplikaciji.
6. **Nasleđeni modul Naplata i novi modul Potraživanja rade paralelno** do završetka prelaska.

---

## 1.8. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako je sistem tehnički sastavljen? | [2. Arhitektura](02-arhitektura.md) |
| Šta tačno radi pojedini modul? | [3. Moduli](03-moduli.md) |
| Koje tabele i pogledi postoje? | [4. Baza podataka](04-baza-podataka.md) |
| Kako teče posao od početka do kraja? | [5. Poslovni procesi](05-poslovni-procesi.md) |
| Kako se računa određeni iznos? | [6. Analize i obračuni](06-analize-i-obracuni.md) |
| Odakle dolaze podaci spolja? | [7. Integracije](07-integracije.md) |
| Šta znači neki pojam? | [12. Rečnik pojmova](12-recnik-poslovnih-pojmova.md) |
