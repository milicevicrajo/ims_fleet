# Tehnicka i finansijska procena: kupovina novog servera ili unapredjenje postojeceg Dell PowerEdge T40

Datum procene: 11.05.2026.

## 1. Kratka preporuka za direktora

Za trenutnu namenu - lokalna Django ERP aplikacija sa SQL Server bazom, bez uloge domain controllera i bez AD servisa - trenutno je racionalnije unaprediti postojeci Dell PowerEdge T40 ugradnjom SSD-a i povecanjem RAM-a na 32 GB, uz obavezno uvodjenje pouzdane backup strategije.

Kupovina novog Dell PowerEdge T360 od oko 820.000 RSD tehnicki jeste bolje i dugorocnije resenje, ali za ovu konkretnu namenu razlika u ceni trenutno nije proporcionalna ocekivanom dobitku u performansama. Glavno usko grlo postojeceg sistema nije procesor, vec mehanicki HDD i relativno skromnih 16 GB RAM-a.

Preporuka je:

1. Sada uraditi racionalan upgrade T40: SSD + 32 GB RAM + backup.
2. Stabilizovati aplikaciju i SQL Server na SSD-u.
3. Planirati kupovinu novog servera u roku od 6-12 meseci, pre isteka Windows Server 2016 extended support-a 12.01.2027.

Zakljucak: investicija od 820.000 RSD trenutno nije hitno opravdana ako je cilj samo ubrzanje postojece Django/SQL aplikacije. SSD + RAM upgrade je racionalno prelazno resenje.

## 2. Polazno stanje

Postojeci server:

- Model: Dell PowerEdge T40
- OS: Windows Server 2016 Datacenter 64-bit
- CPU: Intel Xeon E-2224G @ 3.50 GHz
- RAM: 16 GB DDR4 Dual Channel @ 1330 MHz
- Disk: 1 TB Seagate ST1000DM010 SATA HDD
- Aplikacija: Django ERP aplikacija
- Baza: SQL Server
- Servisi: Python venv, Waitress/NSSM, moguce Redis/Celery
- Korisnici: pristupaju iz lokalne mreze preko browsera
- Server nije domain controller i ne koristi se za AD

Nova opcija:

- Dell PowerEdge T360 DES14400
- Cena: oko 820.000 RSD
- Windows Server 2022
- 32 GB DDR5
- SSD storage / RAID opcija
- Novija serverska platforma

Alternativa:

- SSD 1 TB ili 2 TB
- RAM na 32 GB
- Procena ulaganja: oko 350 EUR, odnosno priblizno 41.000 RSD bez dodatnog rada i pratecih troskova
- Kloniranje sistema sa HDD-a na SSD
- Stari HDD ostaje kao fallback
- Uvodjenje redovnog SQL backup-a

## 3. Tehnicko obrazlozenje

### CPU: Intel Xeon E-2224G

Intel Xeon E-2224G je 4-core procesor visokog osnovnog takta. Za tipicnu internu Django ERP aplikaciju sa SQL Server bazom i korisnicima iz lokalne mreze, ovaj CPU je uglavnom dovoljan.

CPU bi postao ogranicenje ako:

- aplikacija ima veliki broj istovremenih korisnika,
- SQL upiti rade teske agregacije nad velikim tabelama,
- server istovremeno radi vise zahtevnih servisa,
- postoje veliki batch poslovi, izvestaji ili importi koji opterecuju procesor,
- nema optimizacije SQL indeksa.

Za opisani scenario veca je verovatnoca da su uska grla disk i RAM, ne CPU.

### Disk: HDD kao glavno usko grlo

Postojeci 1 TB Seagate SATA HDD je najkriticnija tacka sistema.

SQL Server je posebno osetljiv na disk performanse zbog:

- citanja i pisanja data fajlova,
- transaction log fajlova,
- tempdb operacija,
- index seek/scan operacija,
- backup/restore operacija,
- povremenih vecih izvestaja i importa.

Mehanicki HDD ima visoku latenciju i ogranicen broj I/O operacija po sekundi. Kod baze podataka to se najvise vidi kroz:

- sporo otvaranje stranica koje citaju vise podataka,
- cekanje kod filtera i izvestaja,
- sporije upise,
- usporenje kada vise korisnika radi istovremeno,
- blokiranje tokom backup-a, importa ili jacih SQL upita.

Ugradnja SSD-a je najveca pojedinacna performansna dobit za ovaj server. Realno se moze ocekivati vidno brze otvaranje aplikacije, brzi SQL upiti, brzi importi i stabilniji rad kada vise korisnika radi istovremeno.

### RAM: 16 GB vs 32 GB

16 GB RAM-a je donja granica za Windows Server + SQL Server + Django + dodatne servise. Sistem moze da radi, ali nema mnogo prostora za SQL cache i paralelne servise.

32 GB RAM-a je razuman minimum za ovu namenu:

- Windows Server ima dovoljno memorije za stabilan rad,
- SQL Server moze da drzi vise podataka i indeksa u memoriji,
- Django/Waitress proces ima dovoljno prostora,
- Redis/Celery mogu da rade bez znacajnog pritiska,
- manja je verovatnoca pagefile aktivnosti na disku.

Preporuka je da se SQL Server-u podesi `max server memory`, na primer okvirno 16-20 GB, da ne pojede celu memoriju i ne ugrozi OS i aplikativne procese.

### Windows Server 2016 rizik

Windows Server 2016 je vec star OS. Prema Microsoft lifecycle dokumentaciji, extended support za Windows Server 2016 se zavrsava 12.01.2027. Posle tog datuma sistem ulazi u zonu povecanog bezbednosnog i compliance rizika ako se ne kupe Extended Security Updates ili ne uradi migracija.

To ne znaci da server tehnicki prestaje da radi, ali znaci:

- nema redovnih bezbednosnih ispravki bez dodatnog ESU programa,
- raste rizik kod izlozenih servisa,
- teze je opravdati sistem u internim i spoljnim kontrolama,
- novi softver i driveri mogu imati slabiju podrsku,
- svaka buduca migracija postaje hitnija.

Zbog toga SSD/RAM upgrade treba posmatrati kao prelazno resenje, ne kao trajno resenje za narednih 5 godina.

### Rizik starije Dell T40 platforme

Dell PowerEdge T40 je entry-level server. Za internu aplikaciju je upotrebljiv, ali ima ogranicenja:

- starija platforma,
- ogranicenije storage/RAID opcije,
- potencijalno slabija redundansa u odnosu na novije PowerEdge modele,
- zavisnost od jednog fizickog servera,
- ako nema aktivnu garanciju, kvar moze napraviti duzi zastoj,
- sa jednim SSD-om nema disk redundanse.

Najveci rizik nije brzina, vec dostupnost i oporavak u slucaju kvara.

## 4. Prednosti novog Dell PowerEdge T360

Novi T360 je tehnicki bolje resenje:

- novija serverska platforma,
- Windows Server 2022,
- duzi lifecycle OS-a,
- 32 GB DDR5,
- bolja storage/RAID opcija,
- potencijalno bolja garancija i servisna podrska,
- bolja osnova za rast aplikacije,
- manji rizik od hardverskog kvara,
- pogodniji za ozbiljniji SQL Server rad.

Windows Server 2022 prema Microsoft lifecycle dokumentaciji ima extended support do 14.10.2031, sto je velika prednost u odnosu na Windows Server 2016.

Novi server ima smisla ako firma zeli:

- dugorocno resenje za 5+ godina,
- bolju pouzdanost,
- garanciju i vendor podrsku,
- RAID storage,
- sigurniji osnov za sirenje ERP sistema,
- manje operativnog rizika.

## 5. Poredjenje opcija

| Stavka | T40 trenutno | T40 posle upgrade-a | Novi Dell T360 |
|---|---:|---:|---:|
| CPU | Xeon E-2224G, verovatno dovoljan | Isti, i dalje dovoljan za trenutnu namenu | Novija platforma, bolja rezerva |
| RAM | 16 GB, ograniceno | 32 GB, dovoljno za trenutnu namenu | 32 GB DDR5, bolja osnova |
| Disk | 1 TB SATA HDD, glavno usko grlo | SATA SSD 1-2 TB, veliko ubrzanje | SSD/RAID opcija, najbolje resenje |
| SQL Server performanse | Ogranicene HDD-om | Znatno bolje | Najbolje i najstabilnije |
| Django performanse | Uglavnom OK, ali zavisi od SQL/disk I/O | Brze ucitavanje i stabilniji rad | Brzo i sa vise rezerve |
| Pouzdanost | Zavisi od starosti HDD-a i servera | Bolje ako postoji backup, ali bez RAID-a i dalje ograniceno | Bolje, posebno uz RAID i garanciju |
| OS rizik | Windows Server 2016, support istice 12.01.2027 | Isti OS rizik ostaje | Windows Server 2022, support do 14.10.2031 |
| Cena | Nema ulaganja, ali performansni rizik | Oko 350 EUR + rad | Oko 820.000 RSD |
| Vreme realizacije | Odmah | Brzo, 1 radni dan uz pripremu | Sporije: nabavka, instalacija, migracija |
| Rizik migracije | Nema migracije | Nizak ako se radi klon i HDD ostaje fallback | Srednji: nova instalacija/migracija |
| Racionalnost sada | Slabo | Najbolji odnos cena/dobitak | Tehnicki najbolje, finansijski tesko opravdati odmah |

## 6. Procena troskova

### Opcija 1: Novi Dell PowerEdge T360

Procena:

- Server: oko 820.000 RSD
- Eventualno dodatno:
  - instalacija i migracija,
  - SQL Server/Windows licence ako nisu ukljucene ili nisu dovoljne,
  - backup disk/NAS,
  - UPS ako ne postoji,
  - rad administratora/programera.

Realno ukupno ulaganje moze biti vece od same cene servera.

### Opcija 2: Upgrade Dell PowerEdge T40

Procena:

- RAM: oko 150 EUR
- SSD 1 TB ili 2 TB: oko 150-200 EUR
- Ukupno: oko 350 EUR, priblizno 41.000 RSD

Realnije sa radom, rezervnim diskom i pratecim troskovima:

- osnovni upgrade: 40.000-60.000 RSD
- optimalniji upgrade sa kvalitetnijim SSD-om, backup diskom i radom: 70.000-120.000 RSD

Cak i optimalniji upgrade ostaje visestruko jeftiniji od novog servera.

## 7. Minimum bezbednog upgrade-a

Minimum koji ima smisla:

1. Ugradnja SATA SSD-a od najmanje 1 TB.
2. Povecanje RAM-a na 32 GB.
3. Kloniranje postojeceg sistema sa HDD-a na SSD.
4. Stari HDD sacuvati netaknut kao fallback.
5. Pre migracije napraviti full SQL backup i filesystem backup.
6. Uvesti dnevni SQL backup na odvojenu lokaciju.
7. Testirati restore baze.

Ovo je najracionalniji kratkorocni potez.

## 8. Optimalan upgrade postojeceg T40

Optimalno:

1. 32 GB RAM.
2. 2 TB kvalitetan SATA SSD, po mogucstvu server/NAS/enterprise klasa.
3. Ako platforma dozvoljava, 2 SSD-a u mirror-u ili makar dodatni SSD/HDD za lokalni backup.
4. Stari HDD ostaje neformatiran kao fallback najmanje 2-4 nedelje.
5. SQL Server:
   - podesiti `max server memory`,
   - proveriti autogrowth baze i log fajlova,
   - proveriti indekse,
   - odvojiti redovan backup od production fajlova.
6. Backup:
   - daily full backup,
   - dodatni differential ili transaction log backup ako je baza kriticna,
   - kopija na eksterni disk/NAS,
   - jedna offsite kopija,
   - periodicni test restore-a.
7. UPS provera.
8. Plan migracije OS-a na Windows Server 2022/2025 ili novi server do kraja 2026.

## 9. Idealno resenje ako budzet nije ogranicenje

Ako firma ima veci budzet i zeli dugorocnu stabilnost:

1. Kupiti novi PowerEdge T360 ili slican server.
2. Koristiti Windows Server 2022 ili noviji.
3. Storage konfigurisati kao RAID 1 ili RAID 10 na SSD diskovima.
4. Razdvojiti:
   - OS,
   - SQL data/log/tempdb ako budzet i konfiguracija dozvoljavaju,
   - backup lokaciju.
5. Migrirati SQL Server kontrolisano.
6. Postojeci T40 zadrzati kao:
   - rezervni server,
   - staging/test server,
   - backup restore test masinu.

Ovo je najbolje tehnicko resenje, ali nije nuzno najracionalnije ako je trenutni problem samo brzina i odziv aplikacije.

## 10. Backup strategija

Bez obzira na izbor hardvera, backup je obavezan.

Preporuceni minimum:

- SQL full backup svake noci.
- Backup fajl ne sme ostati samo na istom disku/serveru.
- Kopija backup-a na eksterni disk, NAS ili drugi server.
- Periodicna offsite kopija.
- Retencija npr. 7 dnevnih, 4 nedeljna, 3 mesecna backup-a.
- Jednom mesecno test restore baze na drugu lokaciju.

Ako je baza u Full Recovery modelu:

- full backup dnevno,
- differential backup na nekoliko sati,
- transaction log backup na 15-60 minuta, zavisno od prihvatljivog gubitka podataka.

Ako je baza mala i prihvatljiv je gubitak podataka od jednog dana:

- Simple Recovery + dnevni full backup moze biti dovoljno, ali to treba poslovno potvrditi.

## 11. Plan migracije na SSD korak po korak

1. Popisati trenutno stanje:
   - verzija Windows Server-a,
   - verzija SQL Server-a,
   - lokacija baze i log fajlova,
   - lokacija Django aplikacije,
   - NSSM/Waitress servisi,
   - Redis/Celery ako postoje,
   - scheduled tasks,
   - firewall pravila.

2. Proveriti zdravlje postojeceg HDD-a:
   - SMART status,
   - Windows Event Viewer disk greske,
   - slobodan prostor,
   - SQL consistency check ako je moguce.

3. Napraviti backup pre bilo kakvog rada:
   - full SQL backup,
   - kopija aplikacije,
   - kopija konfiguracionih fajlova,
   - export scheduled tasks,
   - zapis servisnih naloga i lozinki gde je dozvoljeno.

4. Ugraditi SSD.

5. Klonirati HDD na SSD.

6. Prvi boot sa SSD-a:
   - ne formatirati stari HDD,
   - proveriti da li Windows normalno startuje,
   - proveriti SQL Server,
   - proveriti Django/Waitress/NSSM,
   - proveriti pristup aplikaciji sa klijentskog racunara.

7. Testirati aplikaciju:
   - login,
   - glavne liste,
   - unos/izmena,
   - izvestaji,
   - importi,
   - backup job.

8. Testirati SQL backup i restore.

9. Ostaviti stari HDD kao fallback:
   - fizicki prisutan, ali ne koristiti za aktivan rad,
   - cuvati ga netaknut bar 2-4 nedelje.

10. Posle stabilizacije:
   - podesiti backup retenciju,
   - dokumentovati novu konfiguraciju,
   - izmeriti performanse,
   - planirati OS/server migraciju.

## 12. Da li kupiti novi server odmah ili odloziti?

Kupovina novog servera odmah ima smisla ako:

- postojeci T40 ima hardverske probleme,
- HDD pokazuje greske,
- server nema garanciju i firma ne moze da tolerise zastoj,
- broj korisnika brzo raste,
- ERP postaje kritican sistem bez tolerancije na downtime,
- firma zeli odmah resen OS lifecycle rizik,
- postoje compliance zahtevi koji ne dozvoljavaju Windows Server 2016 posle 12.01.2027.

Kupovinu ima smisla odloziti ako:

- trenutni problem je uglavnom sporost,
- nema dokaza da CPU ne moze da izdrzi opterecenje,
- broj korisnika je umeren,
- firma moze da prihvati planiranu migraciju u narednih 6-12 meseci,
- uvede se pouzdan backup,
- SSD/RAM upgrade stabilizuje rad.

Za opisanu situaciju, odlaganje kupovine nekoliko meseci do godinu dana je racionalno, pod uslovom da se odmah uradi SSD/RAM upgrade i backup.

## 13. Zakljucak

Postojeci Dell PowerEdge T40 nije idealan dugorocni server, ali je za trenutnu namenu jos uvek upotrebljiv. Intel Xeon E-2224G je dovoljan za Django ERP + SQL Server u lokalnoj mrezi, dok je 1 TB HDD najverovatnije glavno usko grlo. Povecanje RAM-a na 32 GB i prelazak na SSD treba da daju najveci odnos dobijenih performansi i ulozenog novca.

Novi Dell PowerEdge T360 je tehnicki bolji, sigurniji i dugorocniji izbor, ali investicija od oko 820.000 RSD trenutno nije potpuno opravdana ako se posmatra samo trenutna aplikativna/database namena i ako nema posebnih zahteva za visoku dostupnost, garanciju, compliance ili veci rast sistema.

Preporucena odluka:

- sada: upgrade T40 na SSD + 32 GB RAM + backup,
- kratkorocno: pratiti performanse i stabilnost,
- srednjorocno: planirati migraciju na novi server ili noviji OS pre isteka Windows Server 2016 support-a 12.01.2027.

Ovakav pristup cuva novac, brzo resava glavno performansno usko grlo i ostavlja firmi vreme da planski donese odluku o vecoj investiciji.

## 14. Dodatni strateski kontekst: aplikacija prerasta u interni ERP

Procenu ne treba posmatrati samo kroz danasnje opterecenje. Aplikacija se razvija kao interni ERP sistem firme, sa postojecim i planiranim modulima:

- flota / vozni park,
- naplata potrazivanja,
- kadrovi / evidencija zaposlenih,
- ugovori,
- arhiva / dokumentacioni sistem,
- menice,
- automatizacija uvoza podataka iz postojecih baza,
- automatizacija izvestaja,
- Celery/Redis periodicni zadaci,
- buduce integracije sa drugim internim sistemima.

To menja nacin razmisljanja. Server vise nije samo racunar na kome radi jedna Django aplikacija, vec postaje centralna poslovna infrastruktura. Kako ERP bude rastao, rasce broj korisnika, broj tabela, velicina SQL baze, broj dokumenata, broj background taskova, broj dnevnih izvestaja i poslovna posledica eventualnog zastoja.

Zato T40 moze biti racionalan za trenutnu fazu, ali ga ne treba posmatrati kao konacnu platformu za ERP narednih 3-5 godina.

## 15. Scenario 1 - Minimalno ulaganje sada

Opis:

- postojeci Dell T40 ostaje,
- ugradjuje se SSD,
- RAM se povecava na 32 GB,
- Windows Server 2016 ostaje za sada,
- cilj je stabilan rad u narednih nekoliko meseci do godinu dana.

Procena:

Ovaj scenario je najbrzi i finansijski najlaksi. Resava glavno trenutno usko grlo, odnosno HDD. SQL Server i Django ce najverovatnije raditi znatno bolje posle prelaska na SSD. RAM od 32 GB je dovoljan za trenutnu fazu i za umeren rast.

Prednosti:

- vrlo nizak trosak,
- brzo se realizuje,
- minimalan rizik ako se sistem klonira i stari HDD ostane fallback,
- znacajno ubrzanje SQL Server-a u odnosu na HDD,
- dovoljno za stabilizaciju trenutne aplikacije.

Mane:

- Windows Server 2016 ostaje rizik zbog kraja support-a 12.01.2027,
- T40 ostaje starija entry-level platforma,
- nema ozbiljne redundanse ako se koristi jedan SSD,
- nije idealno za veliki ERP rast,
- kvar fizickog servera i dalje moze zaustaviti poslovni sistem.

Zakljucak za scenario 1:

Ovo je racionalno kratkorocno resenje. Ima smisla ako firma zeli da odmah dobije stabilniji rad uz minimalan trosak i ako prihvata da novi server ostane plan za narednu fazu.

## 16. Scenario 2 - Prelazno racionalno resenje

Opis:

- T40 se unapredjuje SSD-om i RAM-om,
- uvodi se ozbiljnija backup strategija,
- prati se opterecenje CPU/RAM/disk/SQL Server,
- novi server se planira kasnije, kada ERP bude imao vise modula i kada se budzet bolje opravda.

Procena:

Ovo je najuravnotezeniji scenario. Ne odlaze se problem potpuno, jer se odmah resavaju performanse i backup, ali se ne pravi ni velika investicija pre nego sto ERP poslovno opravda novu infrastrukturu.

U ovom scenariju T40 postaje prelazna platforma za razvoj ERP-a. Firma dobija vreme da izmeri stvarno opterecenje, vidi brzinu rasta baze, proveri koliko korisnika stvarno koristi sistem, utvrdi koji moduli su kriticni i pripremi budzet za ozbiljniji server bez pritiska.

Prednosti:

- najbolji odnos cena/dobitak,
- znacajno poboljsanje performansi odmah,
- uvodi se backup kao obavezna operativna disciplina,
- kupovina novog servera se donosi na osnovu podataka, ne pretpostavki,
- smanjuje se rizik pogresne investicije.

Mane:

- i dalje postoji rizik starije platforme,
- i dalje ostaje Windows Server 2016 dok se ne uradi OS/server migracija,
- zahteva pracenje metrika i disciplinu u backup-u,
- ako ERP brzo postane poslovno kritican, novi server ce morati ranije.

Zakljucak za scenario 2:

Ovo je preporuceni scenario. SSD + 32 GB RAM + backup sada, zatim plansko pracenje opterecenja i priprema za novi server kada ERP predje u fazu poslovno kriticnog sistema.

## 17. Scenario 3 - Dugorocna infrastrukturna investicija

Opis:

- kupuje se novi Dell PowerEdge T360,
- instalira se Windows Server 2022,
- SQL Server i Django ERP rade na novijoj platformi,
- sistem se tretira kao centralni poslovni ERP server,
- planira se rast modula: flota, naplata, kadrovi, ugovori, arhiva, automatizacije, izvestaji.

Procena:

Ako se ERP posmatra kao kljucni poslovni sistem za naredne 2-3 godine, novi server je tehnicki opravdaniji nego sto izgleda iz danasnjeg opterecenja. T360 donosi bolju platformu, noviji OS, duzi lifecycle, bolji storage potencijal, garanciju i veci kapacitet za rast.

Ovaj scenario ima smisla ako rukovodstvo vec sada zna da ce ERP postati centralni sistem firme i da zastoj sistema direktno utice na poslovanje.

Prednosti:

- bolja osnova za naredne 2-3 godine,
- manji rizik od hardverskog kvara,
- Windows Server 2022 sa support-om do 14.10.2031,
- bolja storage/RAID opcija,
- bolje opravdanje ako ERP postaje centralni sistem,
- manje improvizacije u buducnosti.

Mane:

- visok trosak sada,
- moguce je da trenutna aplikacija jos ne koristi puni potencijal novog servera,
- migracija zahteva planiranje,
- treba proveriti sve licence i pratece troskove,
- ako se ERP razvoj uspori, investicija moze delovati preuranjeno.

Zakljucak za scenario 3:

Novi T360 je dugorocno tehnicki najbolje resenje, ali nije nuzno finansijski najracionalnije odmah. Opravdan je ako firma vec sada tretira ERP kao centralni poslovni sistem i zeli da infrastruktura prati taj status bez prelaznih resenja.

## 18. Da li je T40 dovoljan za dodatne ERP module?

T40 posle SSD/RAM upgrade-a moze biti dovoljan za razvoj dodatnih modula u pocetnoj i srednjoj fazi, posebno ako:

- broj korisnika nije veliki,
- dokumentacioni sistem ne cuva ogromne fajlove na istom disku bez kontrole,
- SQL upiti su indeksirani,
- izvestaji se optimizuju,
- Celery taskovi se rasporedjuju van radnog pika,
- backup je uredan,
- prati se opterecenje.

T40 nije idealan ako ERP postane:

- glavni sistem za vise sluzbi,
- sistem sa velikim brojem korisnika tokom celog dana,
- sistem sa velikom arhivom dokumenata,
- sistem sa zahtevnim izvestajima,
- sistem gde zastoj od nekoliko sati pravi ozbiljan poslovni problem.

Drugim recima: T40 je dovoljan za razvoj i prelaznu produkciju, ali nije najbolja platforma za zreli centralni ERP.

## 19. Kada T40 postaje rizik?

T40 postaje ozbiljan rizik kada se pojavi jedan ili vise sledecih uslova:

- ERP koristi vise od jedne ili dve kljucne sluzbe svakodnevno,
- baza brzo raste i prelazi desetine GB aktivnih podataka,
- dokumenti/arhiva pocinju da zauzimaju stotine GB,
- SQL izvestaji traju vise minuta i blokiraju rad,
- CPU je cesto preko 70-80% u radnom vremenu,
- RAM je stalno preko 80% i sistem koristi pagefile,
- disk queue i latency su visoki cak i posle SSD upgrade-a,
- Celery taskovi kasne ili se gomilaju,
- backup traje predugo ili ometa korisnike,
- postoji zahtev da sistem mora biti dostupan stalno,
- Windows Server 2016 se priblizi kraju support-a bez plana migracije.

Ako se dva ili vise ovih signala pojave redovno, upgrade T40 vise nije dovoljan i treba krenuti u nabavku novog servera.

## 20. Metrike koje treba pratiti

Da bi odluka o novom serveru bila zasnovana na podacima, treba pratiti:

| Metrika | Sta pratiti | Signal za novi server ili ozbiljniju optimizaciju |
|---|---|---|
| CPU | prosecno i pik opterecenje | cesto preko 70-80% u radnom vremenu |
| RAM | zauzece memorije i pagefile | stalno preko 80%, pagefile aktivan |
| Disk I/O | latency, queue length, throughput | visoka latencija i posle SSD-a |
| SQL Server | najsporiji upiti, wait stats, deadlock/blocking | upiti/izvestaji blokiraju korisnike |
| Velicina baze | MDF/LDF rast po mesecima | brz rast bez plana arhive |
| Backup | trajanje i uspeh backup-a | backup traje predugo ili nije testiran restore |
| Broj korisnika | aktivni korisnici u piku | rast korisnika uz pad odziva |
| Django | response time najcescih stranica | stranice cesto preko 2-3 sekunde |
| Celery | duzina queue-a i trajanje taskova | taskovi kasne, gomilaju se ili pucaju |
| Izvestaji | trajanje generisanja | izvestaji traju vise minuta |
| Storage | slobodan prostor i rast dokumenata | manje od 20-25% slobodnog prostora |

Preporuka je da se posle SSD/RAM upgrade-a uvede mesecno pracenje ovih metrika i kratak izvestaj za rukovodstvo.

## 21. Preporuka u dva nivoa

### Kratkorocna preporuka

Odmah uraditi:

1. Ugraditi SSD od 1-2 TB.
2. Povecati RAM na 32 GB.
3. Klonirati postojeci HDD na SSD.
4. Stari HDD sacuvati kao fallback.
5. Uvesti dnevni SQL backup na odvojenu lokaciju.
6. Testirati restore baze.
7. Podesiti SQL Server `max server memory`.
8. Pratiti CPU/RAM/disk/SQL/Celery metrike naredna 2-3 meseca.

Ovo je minimalan trosak koji odmah resava najveci tehnicki problem: HDD kao usko grlo.

### Dugorocna preporuka

Novi server kupiti kada se ispuni jedan od sledecih uslova:

- ERP postane poslovno kritican sistem za vise sektora,
- broj modula i korisnika znacajno poraste,
- baza i dokumenti pocnu brzo da rastu,
- background taskovi i izvestaji postanu redovan teret,
- T40 i posle SSD/RAM upgrade-a pokazuje ogranicenja,
- firma zeli sigurnu platformu za naredne 2-3 godine,
- priblizi se kraj Windows Server 2016 support-a bez prihvatljivog alternativnog plana.

Ako firma vec sada ima jasno opredeljenje da ERP postane centralni sistem za flotu, naplatu, kadrove, ugovore, arhivu i automatizaciju, novi T360 je strateski opravdan. Ako ERP jos uvek raste fazno i budzet treba racionalno koristiti, bolje je prvo uloziti oko 350 EUR u T40, a kupovinu novog servera planirati kao drugu fazu.

## 22. Finalni odgovor na investiciono pitanje

Pitanje: da li je sada racionalnije odmah kupiti server od oko 820.000 RSD ili prvo uloziti oko 350 EUR u postojeci T40?

Odgovor:

Za trenutni trenutak racionalnije je prvo uloziti oko 350 EUR u postojeci T40, ali uz jasnu napomenu da je to prelazno resenje. SSD + 32 GB RAM ce najverovatnije resiti najveci deo trenutnih performansnih problema i dati firmi nekoliko meseci do godinu dana stabilnijeg rada.

Medjutim, posto aplikacija prerasta u interni ERP sa vise modula, novi server ne treba odbaciti, vec ga treba planirati kao drugu fazu. Kupovina T360 postaje opravdana kada ERP postane poslovno kritican sistem, kada poraste broj korisnika/modula/podataka ili kada se bude radila migracija sa Windows Server 2016 na noviju podrzanu platformu.

Najbolja odluka po odnosu rizik/trosak:

1. Faza 1 odmah: upgrade T40 za oko 350 EUR + backup + monitoring.
2. Faza 2 planski: novi server u narednih 6-12 meseci ako metrike i poslovni znacaj ERP-a pokazu da sistem prerasta T40.

Ovim se izbegava preuranjena investicija od 820.000 RSD, ali se ne ignorise cinjenica da ERP dugorocno zahteva ozbiljniju infrastrukturu.

## Izvori

- Microsoft Lifecycle: Windows Server 2016 - https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2016
- Microsoft Windows Server Blog: Windows Server 2016 extended support ends 12.01.2027 - https://www.microsoft.com/en-us/windows-server/blog/2026/02/25/planning-ahead-for-windows-server-2016-end-of-support/
- Microsoft Lifecycle: Windows Server 2022 - https://learn.microsoft.com/en-us/lifecycle/products/windows-server-2022
