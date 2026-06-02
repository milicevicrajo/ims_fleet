# Nabavka - funkcionalnosti i povezivanje podataka

Ovaj dokument opisuje sta trenutno postoji u aplikaciji `nabavka`, kako se podaci povezuju i sta je predvidjeno za sledece faze razvoja.

## Poslovni okvir

Proces nabavke u aplikaciji pokriva evidenciju pre knjizenja fakture. Cilj je da se kroz IMS prati dokumentacioni trag od zahteva, preko stavki i dobavljaca, do fakture, ugovora ili narudzbenice.

Proces moze da krene iz tri osnovna dokumenta:

- Zahtev za nabavku.
- Zahtev za uslugu.
- Predlog za nabavku opreme.

Za garazu se vodi jedinstveni tok za nabavku i usluge. Za ostale organizacione jedinice tokovi se mogu razdvojiti na nabavke i usluge.

## Sta je implementirano

### Kontrolna tabla nabavke

Pocetna strana aplikacije prikazuje osnovne pokazatelje:

- ukupan broj predmeta nabavke,
- otvorene predmete,
- predmete koji cekaju fakturu,
- garazne predmete,
- predmete kojima je istekao rok,
- poslednje kreirane predmete.

### Zahtevi i procesi nabavke

Postoji centralni ekran `Zahtevi i procesi nabavke`.

Podrzani tipovi predmeta su:

- `Zahtev za nabavku`,
- `Zahtev za uslugu`,
- `Predlog za nabavku opreme`.

Za svaki predmet se evidentira:

- automatski broj predmeta,
- tip predmeta,
- status,
- naziv i opis,
- da li je predmet garazni,
- OJ / sifra posla,
- dobavljac,
- vozilo za garazne predmete,
- procenjena vrednost i valuta,
- rok `Potrebno do`,
- napomena,
- korisnik koji je kreirao predmet.

Kod novog predmeta rok je podrazumevano 7 dana od dana kreiranja, ali moze rucno da se promeni. To omogucava i retroaktivni unos kada je potrebno uneti dokument koji je nastao ranije.

Broj predmeta se generise automatski. U broju se koriste tip dokumenta, sifra centra/OJ i godina. Za garazne zahteve koriste se posebni prefiksi za garazu.

### Stavke zahteva

Svaki predmet moze da ima vise stavki.

Za stavku se evidentira:

- naziv artikla ili usluge,
- jedinica mere,
- kolicina,
- procenjena jedinicna cena,
- napomena.

Stavke su vazne jer se faktura ne mora vezati samo za ceo zahtev. Sistem podrzava vezivanje fakture na nivou pojedinacne stavke.

### Ponavljanje zahteva

Postoji opcija `Ponovi`.

Kada se zahtev ponovi, kreira se novi predmet u statusu nacrta, sa kopiranim osnovnim podacima i stavkama. Novi zahtev dobija novi automatski broj. Ovo je korisno za periodicne nabavke i usluge, slicno logici ponavljanja putnih naloga.

### Statusi i istorija promena

Predmeti imaju status:

- Nacrt,
- Podneto,
- U obradi,
- Ceka fakturu,
- Faktura povezana,
- Zavrseno,
- Otkazano.

Promene statusa se upisuju u istoriju sa komentarom i korisnikom koji je promenio status.

### Stampa zahteva

Za predmet postoji stampa zahteva. Stampa koristi stavke predmeta i priprema dokument za papirnu arhivu.

Postoji i stampa trebovanja materijala za predmet. 

### EUF fakture

Postoji ekran `EUF fakture`.

Fakture se preuzimaju iz SQL view-a:

`dbo.nbv_preuzete_EUF`

Preuzima se:

- datum fakture,
- naziv partnera,
- broj fakture,
- iznos,
- centar,
- magacin,
- registracija.

U lokalnoj bazi se cuva snapshot EUF fakture da bi mogla da se povezuje sa zahtevima, stavkama i ugovorima.

Na EUF fakturi mogu da se dopune interni podaci:

- povezana OJ / sifra posla,
- da li faktura ide u magacin,
- da li je faktura garazna,
- vozilo kada je faktura garazna,
- interna napomena.

Partner u listi je skracen radi preglednosti, a pun naziv se vidi na hover.

### Povezivanje faktura i zahteva

Postoje dva nacina povezivanja:

- sa detalja zahteva, faktura se moze povezati sa jednom stavkom,
- sa detalja zahteva, faktura se moze povezati sa svim jos nepovezanim stavkama tog zahteva.

Na detalju EUF fakture moze se izabrati stavka zahteva koja jos nema povezanu fakturu.

Veza je na nivou:

`stavka zahteva -> EUF faktura`

To znaci:

- jedan zahtev moze imati vise stavki,
- stavke istog zahteva mogu biti vezane za razlicite fakture,
- jedna faktura moze biti vezana za vise stavki i vise zahteva,
- svaka pojedinacna stavka trenutno ima najvise jednu fakturu.

Ova struktura daje trazenu dubinu pracenja: vidi se koji deo kog zahteva je povezan sa kojom fakturom i dobavljacem.

### Povezivanje faktura i kupovnih ugovora

Na detalju EUF fakture postoji deo za povezivanje sa kupovnim ugovorom iz aplikacije `ugovori`.

Veza je na nivou:

`EUF faktura -> kupovni ugovor`

Na listi kupovnih ugovora u nabavci prikazuju se kupovni ugovori iz aplikacije `ugovori`, sa obracunom:

- broj povezanih faktura,
- ukupna povezana vrednost faktura.

Ovo je osnova za pracenje realizacije kupovnih ugovora po ukupnoj vrednosti.

### Kupovni ugovori

Ekran `Kupovni ugovori` prikazuje ugovore iz aplikacije `ugovori` koji su oznaceni kao kupovni ugovori.

Postoje filteri:

- pretraga po broju, nazivu, predmetu i broju ugovora druge strane,
- partner,
- vrsta,
- status,
- godina.

Ova lista sluzi kao nabavni pogled na ugovore, bez dupliranja ugovora u aplikaciji `nabavka`.

### Narudzbenice

Postoji modul `Narudzbenice`.

Narudzbenica se veze za predmet nabavke i moze imati:

- broj narudzbenice,
- datum narudzbenice,
- dobavljaca,
- ugovor,
- status,
- iznos,
- valutu,
- napomenu.

Statusi narudzbenice su:

- Nacrt,
- Poslato,
- Potvrdjeno,
- Zatvoreno,
- Otkazano.

Ovo je osnova za nabavke po narudzbenici, posebno za situacije gde nema klasicnog ugovora.

### Izvestaji

Postoji ekran `Izvestaji nabavke`.

Trenutno prikazuje:

- broj predmeta po statusu,
- broj predmeta po tipu,
- zbir povezanih EUF faktura,
- zbir narudzbenica.

Ovo je pocetna verzija izvestavanja. Planirani izvestaji su navedeni u delu za sledece faze.

### Alarmi

Postoji ulaz u modul `Alarmi`.

Planirana poslovna logika alarma je:

- ugovori koji isticu za 15 dana,
- ugovori kod kojih se realizacija priblizava 95% ugovorene sume.

## Kako su podaci povezani

Osnovni tok izgleda ovako:

```text
Predmet nabavke
  -> Stavke predmeta
      -> EUF faktura
          -> Kupovni ugovor
```

Dodatni tok za narudzbenice:

```text
Predmet nabavke
  -> Narudzbenica
      -> Dobavljac / ugovor / iznos
```

Garazni tok:

```text
Predmet nabavke ili EUF faktura
  -> oznaka Garaza
      -> Vozilo
          -> OJ / centar preko vozila ili rucno povezane OJ
```

Veze sa drugim aplikacijama:

- `ugovori` daje partnere i kupovne ugovore,
- `fleet` daje vozila i organizacione jedinice/sifre poslova,
- EUF SQL view daje preuzete fakture.

## Poslovna pravila koja aplikacija trenutno podrzava

Podrzano je:

- automatsko numerisanje predmeta,
- retroaktivno korigovanje roka,
- odvajanje garaznih i negaraznih predmeta,
- obavezan izbor vozila kada je predmet garazni,
- kopiranje zahteva kroz opciju `Ponovi`,
- evidencija stavki,
- povezivanje stavki sa EUF fakturama,
- povezivanje EUF faktura sa kupovnim ugovorima,
- pracenje statusa i istorije statusa,
- stampa zahteva i trebovanja.

## Poslovna pravila za dalju doradu

Iz zahteva korisnika treba dalje razraditi:

- odvojene redne knjige/spiskove za nabavke, usluge i garazu,
- redni broj na nivou IMS-a, centra i sifre centra,
- eksplicitno pravilo vrednosti nabavke:
  - do 100.000,00 RSD kao mala nabavka,
  - od 100.000,00 do 1.000.000,00 RSD sa tri ponude i obrazlozenjem izbora,
  - preko 1.000.000,00 RSD kao javna nabavka,
- padajuci meni za vrstu robe/usluge koji odgovara poziciji iz plana JN na koje se zakon ne primenjuje,
- vise dobavljaca/partnera po jednom zahtevu,
- jedan partner kroz vise zahteva,
- detaljnije povezivanje delova zahteva, partnera i faktura,
- pracenje realizacije ugovora po proizvodu i kolicini,
- poredjenje realizacije po proizvodu i kolicini sa planom,
- izvestaj `Preuzete fakture` sa filterima po datumu,
- izvestaj faktura koje nisu vezane za ugovor,
- nabavke po narudzbenici kroz poseban view,
- ocenjivanje isporucioca,
- lista odabranih dobavljaca,
- pregled ispostavljenih faktura po dobavljacu,
- ocena dobavljaca,
- alarmi za istek ugovora i 95% realizacije.

## Dokumenti i papirna arhiva

Svaki dokument koji nastaje u procesu treba da ima elektronsku evidenciju i mogucnost stampe, jer se dokumenti cuvaju u papiru u skladu sa internim pravilnikom.

Trenutno su pokriveni:

- stampa zahteva,
- stampa trebovanja materijala,
- detalji predmeta i faktura kroz aplikaciju.

Za sledece faze treba predvideti obrasce:

- IZ 050 - Zahtev za nabavku,
- IZ 052 - Zahtev za usluge,
- IZ 02.1 - Predlog za nabavku opreme,
- IZ 059 - Pracenje nabavke,
- IZ 059a - Pracenje usluge,
- IZ 059b - Pracenje nabavke i usluge garaze.

## Predlog sledecih faza

### Faza 1 - stabilizacija postojece evidencije

- Doraditi filtere za EUF fakture po datumu.
- Dodati jasan izvestaj `Preuzete fakture`.
- Dodati izvestaj nepovezanih faktura.
- Razdvojiti preglede za nabavku, uslugu i garazu ako poslovni korisnici to potvrde.

### Faza 2 - obrasci i spiskovi

- Uskladiti stampu sa obrascima IZ 050, IZ 052 i IZ 02.1.
- Uvesti pracenja IZ 059, IZ 059a i IZ 059b.
- Dodati knjige rednih brojeva po pravilima IMS/centar/garaza.

### Faza 3 - ugovori, narudzbenice i view-i

- Prosiriti pracenje kupovnih ugovora po proizvodu i kolicini.
- Dodati view-e za poredjenje sa planom.
- Dodati nabavke po narudzbenici.
- Uvesti pravila za fakture bez ugovora.

### Faza 4 - dobavljaci i alarmi

- Uvesti ocenjivanje isporucioca.
- Prikazati fakture i realizaciju po dobavljacu.
- Aktivirati alarme za ugovore koji isticu i ugovore blizu 95% realizacije.

## Kratak pregled korisnickog toka

1. Sekretarica kreira zahtev, uslugu ili predlog za opremu.
2. Sistem automatski dodeljuje broj predmeta.
3. Unose se OJ/sifra posla, rok, dobavljac ako je poznat i stavke.
4. Ako je garaza, bira se vozilo.
5. Zahtev se moze stampati i cuvati u papirnoj arhivi.
6. Fakture se preuzimaju iz EUF view-a.
7. Na fakturi se dopunjava OJ, magacin, garaza, vozilo i interna napomena.
8. Faktura se povezuje sa stavkama zahteva.
9. Faktura se po potrebi povezuje sa kupovnim ugovorom.
10. Kroz izvestaje se prati realizacija, nepovezane fakture i dalji tok nabavke.
