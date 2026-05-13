# Procena nabavke servera za interni ERP sistem

Datum: 12.05.2026.

## 1. Kontekst

Firma ima preko 300 zaposlenih i flotu od oko 150 vozila. Interna aplikacija se razvija kao ERP sistem koji obuhvata flotu, naplatu, kadrove, ugovore, arhivu, menice, automatizaciju uvoza podataka, izvestaje i pozadinske Celery/Redis zadatke.

Zbog toga server ne treba posmatrati samo kao racunar za jednu Django aplikaciju, vec kao centralnu poslovnu infrastrukturu firme.

## 2. Trenutno stanje

Postojeci server je Dell PowerEdge T40:

- Intel Xeon E-2224G
- 16 GB RAM
- 1 TB SATA HDD
- Windows Server 2016
- Django ERP aplikacija + SQL Server

Trenutni CPU je dovoljan za sadasnju fazu rada. Glavno usko grlo je mehanicki HDD, jer SQL Server znacajno zavisi od brzine diska. RAM od 16 GB je donja granica za Windows Server, SQL Server, Django, Redis/Celery i ostale servise.

Windows Server 2016 ima dodatni rizik jer extended support istice 12.01.2027.

## 3. Opcije

| Opcija | Procena troska | Prednosti | Ogranicenja |
|---|---:|---|---|
| Bez ulaganja | 0 | Nema troska | HDD ostaje usko grlo, 16 GB RAM, star OS |
| Upgrade T40 | oko 350 EUR | SSD + 32 GB RAM daju veliko ubrzanje za mali trosak | Stara platforma i Windows Server 2016 ostaju |
| Novi Dell T360 | oko 8.000 EUR / 820.000 RSD | Nova platforma, Windows Server 2022, SSD/RAID, garancija, bolja osnova za ERP | Veci trenutni trosak |

## 4. Tehnicka procena

Upgrade postojeceg T40 sa SSD-om i 32 GB RAM-a bi najverovatnije doneo veliko ubrzanje, jer uklanja najvecu trenutnu slabost: HDD. SQL Server, izvestaji, importi i rad aplikacije bi trebalo da budu osetno brzi.

Ipak, T40 ostaje entry-level server i nije idealna dugorocna platforma za ERP sistem koji treba da podrzi vise poslovnih modula i vise korisnika. Takodje ostaje problem Windows Server 2016 lifecycle-a.

Novi Dell T360 je tehnicki bolje resenje za naredne 3-5 godina. Donosi noviju serversku platformu, Windows Server 2022, bolju storage/RAID osnovu, vecu pouzdanost i bolju podlogu za dalji rast ERP sistema.

## 5. Finansijska procena

Ako se gleda samo danasnje opterecenje, upgrade T40 za oko 350 EUR je najpovoljnije resenje.

Medjutim, za firmu sa preko 300 zaposlenih i flotom od 150 vozila, ERP sistem ima dovoljno veliki poslovni znacaj da server od oko 8.000 EUR ne predstavlja nerazumnu investiciju. To nije trosak za jednu aplikaciju, vec ulaganje u infrastrukturu centralnog poslovnog sistema.

Moguci rast cena DRAM/SSD komponenti ne treba racunati kao +130% na ceo server. Realnije je da kompletni serveri mogu poskupeti okvirno 10-25%.

Za server od 820.000 RSD:

| Rast | Nova cena |
|---:|---:|
| +10% | 902.000 RSD |
| +15% | 943.000 RSD |
| +20% | 984.000 RSD |
| +25% | 1.025.000 RSD |

Zbog toga SSD i RAM za T40 treba kupiti odmah ako se radi upgrade, ali T360 ne treba kupovati samo iz straha od poskupljenja, vec zbog strateškog znacaja ERP-a.

## 6. Preporuka

### Kratkorocno

Ako novi server ne moze odmah da se nabavi ili migrira, uraditi minimalni upgrade T40:

1. SSD 1-2 TB.
2. RAM 32 GB.
3. Kloniranje sistema sa HDD-a na SSD.
4. Stari HDD sacuvati kao fallback.
5. Uvesti dnevni SQL backup na odvojenu lokaciju.
6. Testirati restore baze.

Ovo brzo i jeftino poboljsava stabilnost i performanse.

### Dugorocno

Kupiti novi Dell PowerEdge T360 kao centralni ERP server sada ili u najkracem planskom roku.

Razlozi:

- ERP prerasta u centralni poslovni sistem firme.
- Firma ima dovoljno veliki obim rada da opravda server od oko 8.000 EUR.
- T40 je dobar kao prelazno, test ili fallback resenje, ali nije idealan kao dugorocni ERP server.
- Windows Server 2016 mora se zameniti pre 2027.
- Novi server smanjuje rizik zastoja i daje bolju osnovu za rast modula.

## 7. Zakljucak

Za kratkorocnu stabilizaciju, SSD + RAM upgrade postojeceg T40 je racionalan i jeftin potez.

Za dugorocni razvoj ERP sistema, posebno u firmi sa 300+ zaposlenih i 150 vozila, novi Dell PowerEdge T360 od oko 8.000 EUR je opravdana strateška investicija.

Preporuka:

```text
Kupiti novi T360 kao centralni ERP server.
T40 po potrebi unaprediti minimalno i zadrzati kao fallback/test server.
```

Ako budzet ili isporuka novog servera nisu odmah spremni, T40 upgrade treba uraditi odmah, ali novi server treba planirati kao obaveznu drugu fazu.
