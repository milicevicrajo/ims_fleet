# Nabavka - modeli Zahtevi, EUF, UF i Roba

Ovaj dokument opisuje kako u aplikaciji `nabavka` funkcionisu cetiri osnovne evidencije:

- Zahtevi,
- EUF fakture,
- UF fakture,
- Roba.

Cilj sistema je da se dokumentacioni trag nabavke vidi od internog zahteva, preko stavki zahteva, do stvarnih finansijskih i robnih podataka povucenih sa finansijskog servera.

## Osnovna ideja

Aplikacija ne menja izvorne podatke sa finansijskog servera. Podaci iz EUF, UF i robe se povlace u lokalnu bazu kao snapshot. Snapshot znaci da aplikacija cuva lokalnu kopiju bitnih podataka, da bi korisnik mogao da ih filtrira, dopuni internim podacima i poveze sa zahtevima.

Glavni tok je:

```text
Zahtev nabavke
  -> Stavke zahteva
      -> EUF faktura
      -> UF faktura
      -> Roba
```

EUF i UF predstavljaju fakture. Roba predstavlja robne ili artikalske stavke koje mogu pripadati tim fakturama, ali mogu biti i starije stavke ili podaci koji nisu ucitani kroz UF/EUF na isti nacin.

Zato postoje dve vrste povezivanja:

- tvrdo povezivanje: korisnik izabere tacan zapis i poveze ga sa stavkom zahteva,
- meko poklapanje: sistem samo naglasi da roba verovatno pripada nekoj UF ili EUF fakturi po broju veznog dokumenta.

## 1. Zahtevi

Zahtev je interni dokument nabavke. U kodu je osnovni model `ProcurementCase`, a njegove stavke su model `ProcurementItem`.

Zahtev predstavlja poslovni razlog zbog kog se nesto nabavlja ili evidentira:

- zahtev za nabavku,
- zahtev za uslugu,
- predlog za nabavku opreme.

Za svaki zahtev cuva se:

- broj predmeta,
- tip zahteva,
- status,
- naziv i opis,
- da li je garazni,
- sifra posla / OJ,
- dobavljac ako je poznat,
- vozilo ako je zahtev garazni,
- procenjena vrednost,
- datum zahteva,
- napomena,
- korisnik koji je kreirao zahtev.

Broj zahteva se generise automatski. U broju se koriste tip dokumenta, sifra centra i godina. Za garazu se koriste posebni prefiksi.

### Statusi zahteva

Zahtev prolazi kroz statuse:

- Nacrt,
- Podneto,
- U obradi,
- Ceka fakturu,
- Faktura povezana,
- Zavrseno,
- Otkazano.

Promene statusa se cuvaju u istoriji, zajedno sa korisnikom i komentarom.

### Stavke zahteva

Stavke su kljucne jer povezivanje ne mora da bude samo na nivou celog zahteva. Jedan zahtev moze imati vise stavki, a svaka stavka moze biti povezana sa drugim izvorom.

Stavka cuva:

- naziv artikla ili usluge,
- jedinicu mere,
- kolicinu,
- procenjenu jedinicnu cenu,
- napomenu.

Stavka moze biti povezana sa jednim od izvora:

- EUF,
- UF,
- Roba.

U modelu `ProcurementItem` polje `source_type` odredjuje tip povezivanja, a zatim se koristi odgovarajuce FK polje:

- `euf_invoice` za EUF fakturu,
- `uf_invoice` za UF fakturu,
- `goods_item` za robu.

Pravilo je da jedna stavka u jednom trenutku ima samo jedan aktivan izvor povezivanja. Time se izbegava nejasnoca da li se stavka odnosi na fakturu ili na robnu stavku.

### Povezivanje stavki

Na detalju zahteva korisnik moze da poveze:

- jednu pojedinacnu stavku,
- sve trenutno nepovezane stavke zahteva.

Kada se bira izvor, korisnik prvo bira tip: EUF, UF ili Roba. Zatim bira konkretan zapis iz tog izvora.

Ako je izabrana roba, u prikazu veze se vidi i broj fakture odnosno vezni dokument, npr:

```text
Roba: ART-001 - Filter ulja (Faktura: TEST-UF-001/2026)
```

## 2. EUF fakture

EUF fakture su snapshot faktura povucenih iz finansijskog SQL view-a:

```text
dbo.nbv_preuzete_EUF
```

U kodu se cuvaju u modelu `ProcurementInvoice`, sa `source = "euf"`.

EUF snapshot cuva:

- interni kljuc `euf_key`,
- datum fakture,
- izvorni tekst datuma,
- naziv partnera,
- broj fakture,
- iznos,
- centar,
- magacin,
- registraciju,
- vreme sinhronizacije.

`euf_key` se pravi iz osnovnih podataka fakture. SluzI da se ista faktura ne duplira pri ponovnom povlacenju.

### Lokalni interni podaci na EUF fakturi

EUF faktura se posle povlacenja moze interno dopuniti:

- da li ide u magacin,
- da li je garazna,
- vozilo,
- osnovna sifra posla,
- dodatne sifre posla,
- interna napomena,
- oznaka da je faktura vracena.

Polje `is_returned` ima podrazumevanu vrednost `False`. To znaci da nova povucena EUF faktura nije vracena dok korisnik to ne oznaci.

### Osnovna sifra posla za garaznu fakturu

Osnovna sifra posla na EUF fakturi se ne bira rucno kada je faktura garazna i kada je izabran auto. Tada sistem automatski uzima trenutnu sifru posla automobila i cuva je kao snapshot.

To je bitno poslovno pravilo:

```text
Faktura pamti sifru posla automobila u trenutku povezivanja.
Ako se sifra posla automobila kasnije promeni, faktura se ne menja automatski.
```

U modelu se zato cuva:

- `job_code`,
- `job_code_source = "vehicle_snapshot"`,
- `vehicle_job_code_assigned_date`.

Na ekranu se prikazuje da je to "Sifra posla automobila - snapshot".

### Dodatne sifre posla na EUF fakturi

Ako faktura nema automobil, ili trosak treba podeliti na dodatne sifre posla, koristi se donji deo ekrana "Sifre posla fakture".

Te veze su u modelu `ProcurementInvoiceJobCodeLink`.

Ovo znaci:

- osnovna sifra posla je automatska samo za garazu + auto,
- dodatne sifre posla se dodaju rucno,
- rucno dodavanje ne menja snapshot sifru automobila.

### Povezivanje EUF fakture sa zahtevima

EUF faktura moze da se poveze sa stavkom zahteva. Veza stavke i fakture je u modelu `ProcurementItemInvoiceLink`.

Jedna EUF faktura moze biti povezana sa vise stavki i vise zahteva. Jedna stavka trenutno ima najvise jednu fakturu kroz tu vezu.

Na detalju EUF fakture takodje se vide:

- povezane stavke zahteva,
- povezani kupovni ugovori,
- povezane dodatne sifre posla,
- interna dopuna podataka.

## 3. UF fakture

UF deo predstavlja fakture i stavke povucene sa finansijskog servera iz izvora za ulazne fakture. U aplikaciji postoje dva nivoa:

- `EufItemSnapshot` - pojedinacne UF stavke,
- `UfInvoiceSnapshot` - grupisana UF faktura.

Naziv `EufItemSnapshot` je istorijski naziv modela, ali se poslovno koristi kao UF stavka.

### UF stavke

UF stavka cuva detalje jedne stavke fakture:

- UF ID,
- datum kreiranja,
- datum dokumenta,
- datum dospeca,
- broj fakture,
- partner PIB/MB/naziv,
- ukupan iznos,
- osnovicu,
- iznos placanja,
- jedinicu mere,
- naziv stavke,
- kolicinu,
- cenu,
- vrednost,
- konto.

Ovo je detaljan nivo. Koristan je kada treba videti sta se tacno nalazi u fakturi.

### UF faktura kao grupa stavki

UF faktura `UfInvoiceSnapshot` nastaje grupisanjem UF stavki. Grupisanje se radi po broju fakture i partneru.

UF faktura cuva:

- kljuc izvora,
- UF ID,
- broj fakture,
- partnera,
- datume,
- ukupne iznose,
- zbir vrednosti stavki,
- broj stavki,
- konta koja se pojavljuju na stavkama.

Zato ekran "UF fakture" prikazuje fakturu kao jedan red, a detalj UF fakture prikazuje stavke koje pripadaju toj fakturi.

### Povezivanje UF fakture sa zahtevom

Stavka zahteva se povezuje na `UfInvoiceSnapshot`, odnosno na fakturu kao celinu.

To je prakticno jer korisnik najcesce zna broj fakture, dobavljaca i ukupan iznos. Detaljne UF stavke se i dalje vide na detalju UF fakture.

Tok izgleda ovako:

```text
Stavka zahteva
  -> UF faktura
      -> UF stavke
```

## 4. Roba

Roba je snapshot robnih ili artikalskih podataka sa finansijskog servera. U kodu je model `GoodsSnapshot`.

Roba cuva:

- godinu,
- broj dokumenta,
- vrstu dokumenta,
- organizacionu jedinicu,
- sifru partnera,
- naziv partnera,
- datum dokumenta,
- vezni dokument,
- iznos,
- valutu,
- sifru predmeta,
- broj stavke,
- sifru artikla,
- vrstu artikla,
- naziv artikla,
- kolicinu,
- cenu.

Najvaznije polje za povezivanje sa fakturama je `linked_document`. To je vezni dokument, odnosno broj racuna/fakture kada izvorni podaci to nose.

### Roba kao deo UF ili EUF

Roba moze poslovno pripadati UF ili EUF fakturi. Na primer:

```text
Roba.linked_document = TEST-UF-001/2026
UF.invoice_number = TEST-UF-001/2026
```

ili:

```text
Roba.linked_document = TEST-EUF-001/2026
EUF.invoice_number = TEST-EUF-001/2026
```

Medjutim, aplikacija za sada ne pravi automatsku trajnu vezu robe i fakture. Razlog je sto podaci mogu da se preklapaju:

- ista roba moze biti deo UF fakture,
- ista ili slicna roba moze biti vidljiva i kroz EUF,
- neke robe su iz ranijih perioda i nemaju ucitanu fakturu,
- nekad postoji samo robni trag bez jasne fakture u lokalnom snapshot-u.

Zato se koristi meko poklapanje.

### Meko poklapanje robe sa UF/EUF

Na ekranu "Roba" sistem proverava da li postoje dve tacne potvrde veze:

- `linked_document` mora da odgovara broju povucene UF ili EUF fakture,
- partner na robi mora da odgovara partneru na toj fakturi.

Ako postoji jednoznacno poklapanje:

- red robe se vizuelno naglasi,
- pored veznog dokumenta se prikaze oznaka `UF` ili `EUF`,
- oznaka je link na tu fakturu.

Ako se ista roba po tim pravilima poklopi i sa UF i sa EUF, oznaka se ne prikazuje, jer izvor nije jednoznacno potvrdjen.

Ovo korisniku jasno kaze:

```text
Ova roba verovatno pripada vec povucenoj UF/EUF fakturi.
```

Ali sistem ne tvrdi da su stavke automatski povezane 1:1.

### Tvrdo povezivanje robe sa stavkom zahteva

Korisnik ipak moze rucno da poveze konkretnu robnu stavku sa stavkom zahteva.

Tada se u `ProcurementItem` cuva:

```text
source_type = "goods"
goods_item = izabrana roba
```

U prikazu stavke se vidi:

```text
Roba: sifra artikla - naziv artikla (Faktura: vezni dokument)
```

To je korisno kada je korisnik siguran da bas ta robna stavka odgovara stavci zahteva.

## Kako se cetiri modela zajedno koriste

### Tipican tok za zahtev

1. Kreira se zahtev.
2. Dodaju se stavke zahteva.
3. Povlace se EUF, UF i roba sa finansijskog servera.
4. Korisnik na stavci zahteva bira da li je povezuje sa EUF, UF ili robom.
5. Ako je izabrana roba, vidi se i broj fakture iz veznog dokumenta.
6. Ako roba ima poklapanje sa UF/EUF, sistem je naglasava na ekranu robe.

### Kada koristiti EUF

EUF se koristi kada je bitno povezati stavku zahteva sa fakturom kao finansijskim dokumentom iz EUF pregleda.

Koristi se za:

- broj fakture,
- dobavljaca,
- iznos,
- status vraceno,
- ugovore,
- garaznu fakturu i auto,
- snapshot sifre posla automobila.

### Kada koristiti UF

UF se koristi kada je faktura dosla kao ulazna faktura sa detaljnijim stavkama i kontima.

Koristi se za:

- pregled fakture sa brojem stavki,
- detalj stavki fakture,
- konta,
- povezivanje stavke zahteva sa UF fakturom.

### Kada koristiti robu

Roba se koristi kada je najvazniji artikalski trag:

- sifra artikla,
- naziv artikla,
- kolicina,
- cena,
- robni dokument,
- vezni dokument/faktura.

Roba je posebno vazna za garazu, magacin i situacije gde faktura sama ne daje dovoljno detalja o artiklima.

## Pravila i ogranicenja

1. EUF, UF i roba su snapshot podaci.
2. Snapshot se moze osvezavati ponovnim povlacenjem iz izvora.
3. Interni podaci koje korisnik dopuni na EUF fakturi ne treba da se izgube pri osvezavanju.
4. `Vraceno` na EUF fakturi je podrazumevano `False`.
5. Osnovna sifra posla EUF fakture se automatski postavlja samo kada je faktura garazna i kada je odabran auto.
6. Ta osnovna sifra posla je snapshot i ne menja se sama ako se kasnije promeni sifra posla auta.
7. Dodatne sifre posla na EUF fakturi dodaju se rucno.
8. Roba se automatski samo naglasava kada joj se vezni dokument poklopi sa UF/EUF fakturom.
9. Roba se trajno povezuje sa stavkom zahteva samo kada korisnik rucno izabere robni zapis.
10. Jedna stavka zahteva moze imati jedan aktivan tip izvora: EUF, UF ili Roba.

## Kratak primer

Primer podataka:

```text
EUF faktura:
  TEST-EUF-001/2026

UF faktura:
  TEST-UF-001/2026
  Stavke:
    Filter ulja
    Motorno ulje 5W30
    Rad servisa

Roba:
  ART-001 - Filter ulja
  linked_document = TEST-UF-001/2026
```

Na ekranu robe red `ART-001 - Filter ulja` dobija oznaku `UF`, jer se njegov vezni dokument poklapa sa brojem UF fakture.

Ako korisnik poveze stavku zahteva sa tom robom, na zahtevu se vidi:

```text
Roba: ART-001 - Filter ulja (Faktura: TEST-UF-001/2026)
```

Ako druga roba ima:

```text
linked_document = TEST-EUF-001/2026
```

onda na ekranu robe dobija oznaku `EUF` i link na EUF fakturu.
