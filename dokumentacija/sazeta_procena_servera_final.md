# Sazeta procena servera za interni ERP sistem

Datum procene: 11.05.2026.

## 1. Kontekst

Firma ima preko 300 zaposlenih i flotu od oko 150 vozila. Interna aplikacija se vise ne posmatra kao jednostavna Django aplikacija, vec kao ERP sistem koji obuhvata ili ce obuhvatati:

- flotu / vozni park,
- naplatu potrazivanja,
- kadrove,
- ugovore,
- arhivu i dokumentaciju,
- menice,
- automatizaciju uvoza podataka,
- automatizaciju izvestaja,
- Celery/Redis periodične zadatke,
- buduce integracije sa internim sistemima.

Zbog toga server treba posmatrati kao centralnu poslovnu infrastrukturu, a ne kao obican racunar za jednu aplikaciju.

## 2. Trenutno stanje

Postojeci server:

- Dell PowerEdge T40
- Intel Xeon E-2224G
- 16 GB RAM
- 1 TB SATA HDD
- Windows Server 2016
- Django ERP + SQL Server

Glavni problemi trenutne konfiguracije:

- HDD je ozbiljno usko grlo za SQL Server,
- 16 GB RAM-a je donja granica,
- Windows Server 2016 izlazi iz extended support-a 12.01.2027,
- T40 je entry-level server i nije idealna platforma za centralni ERP firme,
- ako ERP postane poslovno kritican, kvar ili spor rad servera direktno uticu na poslovanje.

## 3. Opcije

### Opcija A - Upgrade postojeceg T40

Ulaganje:

- SSD 1-2 TB,
- RAM na 32 GB,
- procena oko 350 EUR.

Dobitak:

- znacajno ubrzanje SQL Server-a,
- stabilniji rad Django aplikacije,
- bolji odziv kod izvestaja i import procesa,
- brzo i jeftino poboljsanje.

Ogranicenje:

- server ostaje stara platforma,
- Windows Server 2016 rizik ostaje,
- nema dugorocnu rezervu za ERP rast,
- nije optimalno za firmu ovog obima.

Zakljucak:

Upgrade T40 je dobar kao privremeno ili fallback resenje, ali nije dugorocno resenje za centralni ERP sistem firme.

### Opcija B - Novi Dell PowerEdge T360

Ulaganje:

- oko 8.000 EUR, odnosno oko 820.000 RSD,
- Windows Server 2022,
- 32 GB DDR5,
- SSD / RAID opcija,
- novija serverska platforma.

Dobitak:

- stabilnija i novija platforma,
- duzi OS lifecycle,
- bolja storage i RAID osnova,
- bolja garancija i servisna podrska,
- bolja osnova za ERP razvoj naredne 3-5 godina,
- manji rizik od zastoja poslovnog sistema.

Zakljucak:

Za firmu sa 300+ zaposlenih i 150 vozila, server od oko 8.000 EUR nije nerazumna investicija ako ERP postaje centralni poslovni sistem.

## 4. Poredjenje

| Stavka | T40 sada | T40 posle upgrade-a | Novi T360 |
|---|---|---|---|
| Namena | Privremeni app/db server | Prelazna ERP platforma | Centralni ERP server |
| Performanse | Ogranicene HDD-om | Znatno bolje | Najbolja osnova |
| RAM | 16 GB | 32 GB | 32 GB DDR5 |
| Disk | HDD | SSD | SSD/RAID |
| OS | Windows Server 2016 | Windows Server 2016 | Windows Server 2022 |
| Rizik OS support-a | Visok od 2027 | Visok od 2027 | Nizak dugorocno |
| Pouzdanost | Ogranicena | Bolja, ali bez ozbiljne redundanse | Bolja serverska platforma |
| Trosak | 0 | oko 350 EUR | oko 8.000 EUR |
| Dugorocna ERP spremnost | Slaba | Srednja / prelazna | Dobra |

## 5. Cena i rizik poskupljenja

Prognoze rasta cena DRAM-a i SSD-a ne znace da ce ceo server poskupeti 130%. Realnije je da kompletne serverske konfiguracije mogu poskupeti okvirno 10-25%, zavisno od RAM-a, SSD-a, RAID-a, garancije, dobavljaca i kursa.

Za server od 820.000 RSD:

| Rast cene | Nova okvirna cena |
|---:|---:|
| +10% | 902.000 RSD |
| +15% | 943.000 RSD |
| +20% | 984.000 RSD |
| +25% | 1.025.000 RSD |

Zakljucak:

- SSD i RAM za T40 treba kupiti odmah ako se radi upgrade, jer su to direktno komponente koje mogu poskupeti.
- Novi T360 ne treba kupiti samo zbog straha od poskupljenja.
- Ali ako firma svakako planira ERP kao centralni sistem, kupovina sada ima smisla jer se izbegava kasnije poskupljenje i dobija stabilna platforma odmah.

## 6. Poslovni ugao

Za firmu sa preko 300 zaposlenih i flotom od oko 150 vozila, ERP sistem ima realnu poslovnu vrednost. Ako sistem pokriva flotu, kadrove, naplatu, ugovore, arhivu i automatizacije, zastoj aplikacije nije samo IT problem, vec operativni problem firme.

Server od oko 8.000 EUR treba posmatrati kroz:

- smanjenje rizika zastoja,
- bolju dostupnost poslovnog sistema,
- brzi rad zaposlenih,
- sigurniji razvoj ERP modula,
- kvalitetniji backup i restore,
- duzi lifecycle platforme,
- manju zavisnost od starog hardvera.

U odnosu na velicinu firme, broj zaposlenih i vrednost flote, investicija od 8.000 EUR je opravdana ako ERP postaje centralni alat rada.

## 7. Preporuka

### Kratkorocno

Ako novi server ne moze odmah da se nabavi ili migrira, uraditi minimalni upgrade T40:

1. SSD 1-2 TB.
2. RAM 32 GB.
3. Kloniranje sistema.
4. Stari HDD zadrzati kao fallback.
5. Uvesti dnevni SQL backup.
6. Testirati restore.

Ovo obezbedjuje stabilniji rad dok se novi server ne pripremi.

### Strateski

Kupiti novi Dell PowerEdge T360 sada ili u najkracem planskom roku.

Razlog:

- ERP prerasta u centralni poslovni sistem,
- firma ima dovoljno veliki obim poslovanja da opravda server od oko 8.000 EUR,
- T40 je koristan kao prelazno/test/fallback resenje, ali nije idealna dugorocna ERP platforma,
- Windows Server 2016 lifecycle rizik se mora resiti pre 2027,
- kupovina sada smanjuje rizik kasnijeg poskupljenja i migracije pod pritiskom.

## 8. Predlozeni plan

1. Odmah obezbediti backup postojeceg sistema i SQL baze.
2. Ako novi server ne stize brzo, uraditi SSD/RAM upgrade T40 kao prelaznu meru.
3. Nabaviti T360 kao novu ERP platformu.
4. Instalirati Windows Server 2022.
5. Podesiti SSD/RAID storage.
6. Migrirati SQL Server i Django ERP kontrolisano.
7. Testirati aplikaciju, izvestaje, Celery taskove i backup.
8. T40 ostaviti kao test/staging/fallback server.
9. Uvesti monitoring CPU/RAM/disk/SQL/Celery opterecenja.
10. Dokumentovati backup i restore proceduru.

## 9. Zakljucak

Ako bi se posmatrala samo trenutna tehnicka potreba, upgrade T40 za oko 350 EUR bio bi najracionalniji potez.

Medjutim, uzimajuci u obzir da firma ima preko 300 zaposlenih, flotu od oko 150 vozila i ERP koji se razvija kao centralni poslovni sistem, kupovina novog servera od oko 8.000 EUR je opravdana strateška investicija.

Preporuka:

```text
Kupiti novi Dell PowerEdge T360 kao centralni ERP server.
```

Ako isporuka ili budzet nisu odmah spremni:

```text
Uraditi SSD + RAM upgrade T40 kao privremenu meru, ali novi server planirati kao obaveznu drugu fazu, ne kao opcionu kupovinu.
```

T40 upgrade resava kratkorocnu brzinu. Novi T360 resava dugorocnu pouzdanost, rast ERP-a i poslovni rizik.
