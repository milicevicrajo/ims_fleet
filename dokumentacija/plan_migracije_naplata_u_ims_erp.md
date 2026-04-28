# Plan migracije aplikacije Naplata u IMS_ERP

## Cilj

Prebaciti aplikaciju `naplata` iz zasebne SQL Server baze `Naplata` u glavnu ERP bazu `IMS_ERP`, tako da naplata, pravna sluzba, menice i ostali moduli koriste isti izvor podataka.

Glavni cilj nije samo promena konekcije, nego smanjenje tehnickog duga:

- jedna produkciona baza za IMS aplikaciju,
- manje posebnih `.using(...)` i `connections[...]` poziva za naplatu,
- lakse migracije i backup,
- jednostavniji odnosi sa korisnicima, pravima i ostalim ERP tabelama,
- lakse odrzavanje SQL view-eva.

## Trenutno stanje

Produkcioni `default` i `server_db` pokazuju na bazu `IMS_ERP`; poseban alias za staru bazu `Naplata` je uklonjen iz koda.

Aplikacija `naplata` trenutno radi dve stvari:

1. Cita finansijske podatke i izvestaje iz SQL view-eva/tabela u bazi `Naplata`.
2. Upisuje operativne podatke naplate i pravne sluzbe u bazu `Naplata`.

Bitne grupe objekata:

- read/reporting objekti: `baza`, `dodela_baketa`, `ispravke`, `partneri`, `v_neodobreneIF`, `v_tuzeni`
- operativne tabele naplate: `kontakti`, `napomene`, `opomene`, `poziv_pismo`, `pozivi_tel`, `tuzbe`
- Django-managed tabele: `avans_klijent`, `postupak`, `promena_postupka`

## Preporuka

Da, tabele koje su vlasnistvo Django aplikacije treba praviti kroz Django migracije.

To posebno vazi za:

- `avans_klijent`
- `postupak`
- `promena_postupka`

Za stare postojece tabele koje vec postoje u `Naplata` bazi postoje dve mogucnosti:

1. Privremeno ih napraviti rucno u `IMS_ERP` SQL skriptom, prebaciti podatke, pa ih ostaviti kao `managed = False`.
2. Dugorocno ih pretvoriti u Django-managed modele, ako aplikacija treba da bude potpuni vlasnik tih tabela.

Pragmaticno: prvo izabrati opciju 1, jer je manje rizicna. Kada sve proradi u `IMS_ERP`, onda odluciti koje tabele vredi prebaciti pod Django migracije.

SQL view-eve ne treba praviti kroz standardne Django modele. Njih treba praviti SQL skriptama u `IMS_ERP`, a Django modeli za njih treba da ostanu `managed = False`.

## Faza 1: Inventar baze Naplata

Napraviti spisak svih objekata iz baze `Naplata` koje aplikacija koristi.

Minimalni spisak:

- `kontakti`
- `napomene`
- `opomene`
- `poziv_pismo`
- `pozivi_tel`
- `tuzbe`
- `sif_baket`
- `sif_kategorija`
- `baza`
- `dodela_baketa`
- `ispravke`
- `partneri`
- `v_neodobreneIF`
- `v_tuzeni`
- `avans_klijent`
- `postupak`
- `promena_postupka`

Proveriti tacne nazive u SQL Serveru. U kodu postoji neslaganje izmedju `dodela_bucketa` u modelu i `dodela_baketa` u SQL upitima. To treba standardizovati pre selidbe.

## Faza 2: Napraviti strukturu u IMS_ERP

### Django migracije

Django treba da napravi svoje tabele migracijama nad `IMS_ERP`.

Komanda u produkcionom okruzenju:

```powershell
python manage.py migrate naplata --database default
```

Ovo ima smisla samo za modele koji su `managed = True`.

Trenutno su to:

- `AvansKlijent`
- `Postupak`
- `PromenaPostupka`

### SQL skripte

Rucno SQL skriptom napraviti ili prebaciti stare tabele koje su trenutno `managed = False`.

To su:

- `kontakti`
- `napomene`
- `opomene`
- `poziv_pismo`
- `pozivi_tel`
- `tuzbe`
- `sif_baket`
- `sif_kategorija`

SQL view-eve napraviti u `IMS_ERP` kao view-eve:

- `baza`
- `dodela_baketa`
- `ispravke`
- `partneri`
- `v_neodobreneIF`
- `v_tuzeni`

Ako neki view sada cita tabele iz baze `Naplata`, treba promeniti definiciju da cita iz tabela u `IMS_ERP` ili iz originalnih ERP tabela.

## Faza 3: Prebacivanje podataka

Pre prebacivanja:

- napraviti backup baze `Naplata`
- napraviti backup baze `IMS_ERP`
- zakljucati ili privremeno zaustaviti unos u naplati dok traje migracija
- zabeleziti broj redova po svakoj tabeli

Podatke prebaciti SQL skriptom, ne kroz Django admin.

Primer principa:

```sql
INSERT INTO IMS_ERP.dbo.kontakti (...)
SELECT ...
FROM Naplata.dbo.kontakti;
```

Za tabele sa identity kolonom proveriti da li treba `SET IDENTITY_INSERT ON`.

Posle prebacivanja proveriti:

- broj redova pre i posle,
- maksimalni `id`,
- par nasumicnih partnera sa svim detaljima,
- pravne postupke i njihove faze,
- opomene i napomene.

## Faza 4: Kratkotrajan prelaz bez velikog refaktora

Ova faza je preskocena u korist direktnog ciscenja koda: aplikacija naplate sada koristi eksplicitnu `server_db` konekciju, koja pokazuje na `IMS_ERP`.

Za produkciju je bitno da `server_db` baza ostane:

```python
'server_db': {
    'ENGINE': 'mssql',
    'NAME': 'IMS_ERP',
    ...
}
```

Prednost:

- manje promena u Python kodu,
- brzo se vidi da li aplikacija radi nad novom bazom,
- lak rollback ako nesto nije dobro.

Time se izbegava tehnicki dug u kome kod izgleda kao da naplata koristi posebnu bazu.

## Faza 5: Ciscenje koda

Kada se potvrdi da aplikacija radi u `IMS_ERP`, postepeno uklanjati preostale eksplicitne reference na posebne baze.

Zameniti:

- `connections[...]` za posebnu naplata konekciju
- `.using(...)` za posebnu naplata konekciju
- `save(using=...)`
- `delete(using=...)`

sa default konekcijom gde god je moguce.

Ovo ne treba raditi pre validacije podataka, jer onda istovremeno menjamo i bazu i kod.

## Faza 6: Testiranje

Obavezno proveriti ove ekrane:

- lista dugovanja
- dugovanja po bucketima
- detalj partnera
- dodavanje/izmena/brisanje kontakta
- dodavanje/izmena/brisanje napomene
- uvoz i lista opomena
- pozivi telefonom
- pozivna pisma
- tuzbe
- pravna sluzba: lista, detalj, dodavanje, izmena, arhiviranje
- dodavanje faze pravnog postupka
- exporti u Excel
- menice izbor partnera

## Preporuceni redosled rada

1. Izvuci SQL definicije tabela i view-eva iz baze `Naplata`.
2. Napraviti test kopiju `IMS_ERP` ili raditi u posebnoj test bazi.
3. Napraviti tabele i view-eve u test bazi.
4. Prebaciti podatke.
5. Podesiti `server_db` konekciju na test `IMS_ERP`.
6. Testirati aplikaciju.
7. Ispraviti razlike u nazivima view-eva i kolona.
8. Ponoviti proces u produkciji uz backup i kratak period bez unosa.
9. Nakon stabilizacije ukloniti posebne naplata konekcije iz koda.

## Kratak odgovor na pitanje

Da: nove Django tabele treba da napravi Django migracijama.

Ne: SQL view-eve i postojece ERP/reporting objekte ne treba forsirati kroz Django. Njih napravi SQL skriptama u `IMS_ERP`, a u Django modelima ih ostavi kao `managed = False`.

Za postojece operativne tabele iz stare naplate najbezbednije je prvo ih fizicki prebaciti SQL-om u `IMS_ERP`, pa tek kasnije odluciti da li ih Django treba preuzeti kao `managed = True`.
