# Fakture i prelazak Naplate na lokalni izvor

Stanje pregleda: **18.09.2026.** Organizacija i centralni šifarnik ostaju zaseban, odložen zadatak.

## 1 Završena korekcija faktura u Finansijama

Detalj šifre posla koristi aktivna lokalna knjiženja korisniku dostupne firme i posla. Izvorna godina odgovara izboru korisnika; mesec ili cela godina filtriraju datum dokumenta. Godina 2026. iz dostavljenog SQL primera nije fiksna vrednost u kodu. Stvarni naziv kolone konta u izvoru je `knt`, ne `konto`.

| Tab | Izbor | Iznos |
|---|---|---|
| Fakture | IF i tačna konta 20400, 20500 | Zbir duguje − potražuje |
| Interne fakture | ON i tačna konta 61420, 61421, 61521, 64002 | Zbir potražuje − duguje |

Jedan red predstavlja godinu, nalog, vezu dokumenta i partnera. Iznos je samo deo na izabranoj šifri. Ne dodaju se zajedno prihod, potraživanje i PDV. Negativna knjiženja zadržavaju znak; u izvoru postoje negativni iznosi na izabranim ON kontima. IF prikaz nije saldo duga posle uplata i nije iznos naplaćen po fakturi.

Oba taba koriste AJAX u pozadini, datumsko i numeričko sortiranje, bedževe i zbir celog perioda. P/R, ZT i novčani tokovi nisu menjani. Izvor Finansija ostaje njihova postojeća sinhronizacija iz udaljenog nalog_z u LedgerEntry; nije prebačen na IMS_ERP.dbo.nalog_z.

Provera korekcije faktura: 138 testova finansije/core/naplata prolazi. Na postojećim podacima posla 413111 za celu 2026. zbir grupisanog prikaza jednak je zbiru odgovarajućih lokalnih knjiženja za IF i ON. U toj fazi nisu pokretane procedure, finansijska sinhronizacija niti promene poslovne baze. Naknadna implementacija pokretanja procedure opisana je u odeljku 4.

## 2 Šta radi sp_AzurirajNalogZ

Pročitana je postojeća definicija **IMS_ERP.dbo.sp_AzurirajNalogZ**; procedura nije izvršavana.

- Nema ulaznih parametara. Čita udaljeni PUTGEO-SERVER.BazaIMS.dbo.nalog_z u privremenu tabelu.
- Do uključivo 30. aprila uzima prethodnu i tekuću godinu; posle tog datuma samo tekuću. Na dan pregleda to je 2026, bez ponovnog osvežavanja 2025.
- Nema filter sif_pred=1: obuhvata sve firme u izabranim godinama.
- Proverava NULL i duplikate izvornog ključa firma/godina/vrsta naloga/broj/stavka.
- U transakciji ažurira postojeće i dodaje nedostajuće redove lokalnog dbo.nalog_z.
- Ne uklanja lokalne redove koji su obrisani u izvoru. Zato lokalna tabela nije garantovano identična trenutnom izvoru samo zato što je procedura uspešna.
- BrojAzuriranihRedova broji sve postojeće redove obuhvaćene UPDATE-om, ne samo redove čiji se sadržaj stvarno promenio.
- Vraća OdGodine, DoGodine, BrojAzuriranihRedova i BrojDodatihRedova. Greška se ponovo prijavljuje nakon rollback-a.

U pregledanim metapodacima nema indeksa sa kolonama na lokalnom nalog_z. Pre puštanja rasporeda proveriti duplikate cilja i plan izvršavanja, pa definisati jedinstveni indeks izvornog ključa i potrebne indekse čitanja. Procedura koristi UPDLOCK/HOLDLOCK, ali aplikaciono zaključavanje cele operacije dodatno sprečava paralelni ručni i zakazani poziv. Za sve pozivaoce, uključujući SQL Agent, isto zaključavanje najbolje je ugovoriti u samoj proceduri.

## 3 Gde Naplata sada čita podatke

Veza server_db već pokazuje na **IMS_ERP**. To ne znači da su svi podaci lokalni: postojeći view-ovi unutar IMS_ERP i dalje prelaze na udaljeni server.

| Objekat | Pregledana uloga | Izvor ili zavisnost |
|---|---|---|
| dbo.nalog_z | Lokalna kopija knjiženja | Puni je sp_AzurirajNalogZ |
| dbo.baza | Promet potraživanja za firmu 1, grupu 1 i konta 20400/20500 | Trenutno udaljeni nalog_z i partneri; period zavisi od datuma godine |
| dbo.v_if | IF dokumenti i datumi dospeća | Udaljeni nalog_z od 2025. i UNION ALL tabela_if |
| dbo.v_duplikati | Dokumenti prisutni u više godina, sa izborom dospeća | Udaljeni nalog_z bez istog ograničenja godina i duplikati18 |
| dbo.dodela_baketa | Saldo, broj dana i starosni razred | baza, v_if i v_duplikati |
| dbo.partneri | Šifarnik partnera sa nazivom grupe | Udaljene tabele partner i Gruppartner |
| dbo.tabela_if i dbo.duplikati18 | Dodatni lokalni podaci u IF i duplikatima | Poslovni razlog, istorijski obuhvat i održavanje treba dokumentovati sa vlasnikom baze |
| kontakti, napomene, opomene, poziv_pismo, pozivi_tel, tuzbe | Operativne evidencije Naplate | Već postoje kao lokalne tabele |
| sif_baket i sif_kategorija | Lokalni pomoćni šifarnici | Postoje kao lokalne tabele |
| dbo.ispravke | Dodatni view | Postoji; puna analiza njegove uloge ostaje deo inventara |

Model u naplata/models.py navodi dodela_bucketa, dok pregledani upiti koriste dodela_baketa. Pri pregledu objekata pronađen je drugi naziv. Pre eventualne migracije modela proveriti stvarnu upotrebu prvog; ne preimenovati aktivni view na osnovu samog modela.

U view-u baza granica je računata kao 119 dana od početka godine i poredi se sa GETDATE() koji uključuje vreme. To nije isto što i uključivo 30. april za svaki datum/vreme, posebno u prestupnoj godini. Procedura koristi datum i DATEFROMPARTS. Pre usaglašavanja poslovnog pravila proveriti prelaze 29.04/30.04/01.05, početna stanja POC i obe vrste godine.

Zaključak pregleda: **samo pokretanje procedure ne prebacuje postojeće upite Naplate na lokalnu tabelu**. Potrebno je preusmeriti i proveriti ceo lanac zavisnosti. Lokalna kopija takođe mora imati svu istoriju koju koriste v_if i v_duplikati, ne samo godišnji obuhvat osvežavanja procedure.

## 4 Implementirano pokretanje procedure

Dodati su servis `finansije.services.nalog_z.refresh_nalog_z`, Celery zadatak
`finansije.tasks.refresh_nalog_z_task` na redu `sync` i dugme **Osveži nalog_z** u Finansije →
Sinhronizacija. Ručni POST direktno poziva servis, bez slanja Celery zadatka. Potrebni su CSRF,
prijava i postojeće dozvole `finansije:sync_status` i `finansije:view_all`.

Servis izvršava samo fiksnu proceduru IMS_ERP.dbo.sp_AzurirajNalogZ, bez parametara iz korisničkog
zahteva. SQL session lock u IMS_ERP pokriva i ručne i Celery pozive; preklopljeni poziv se
preskače. SQL Agent/direktni SQL pozivi nisu zaštićeni ovim servisom ako ne koriste isti lock.

Nova tabela istorije `NalogZRefreshRun` čuva početak, završetak, pokretača, status, godine,
ažurirane i dodate redove, grešku i ID zadatka. Istorija se prikazuje zasebno od LedgerEntry,
preko AJAX DataTable sa sortiranjem datuma u bazi i trajanjem uz završetak. Uspeh se beleži tek
posle svih rezultata procedure. Nedostajući brojači nisu uspeh sa nulama. Nema automatskih
ponovnih pokušaja; pri prekidu veze proveriti stvarni ishod u bazi. Zaostali nezavršeni zapis
pri sledećem preuzimanju lock-a dobija oznaku „Ishod nepoznat“.

Raspored je definisan za svaki dan u **10:00 i 11:00, Europe/Belgrade**. Komanda
`manage.py configure_finansije --enable-nalog-z-schedule` aktivira samo ovaj raspored.
Za izvršavanje moraju raditi Celery Beat i worker koji poznaje novi zadatak i sluša red `sync`.
SQL timeout samo za proceduru je 900 s, podesiv kroz `FINANSIJE_NALOG_Z_TIMEOUT`; HTTP/proxy
timeout treba uskladiti za ručno izvršavanje. Greška HTTP odgovora nije potvrda prekida SQL rada.

Nisu menjani sama procedura, pravila brisanja niti view-ovi Naplate. Indeksi, kontrola
duplikata i puna istorijska pokrivenost ostaju deo pripreme migracije Naplate. Pokretanje
procedure samo po sebi ne potvrđuje ispravnost salda, niti završetak sinhronizacije LedgerEntry.

Provera i stanje isporuke 18.09.2026: **154 testa finansije/core/naplata prolazi**.
Migracija istorije primenjena je na razvojnu bazu; raspored procedure upisan je i uključen
za 10:00/11:00, Europe/Belgrade, red sync. Na stvarnom SQL Serveru provereni su EXECUTE pravo
i odbijanje drugog istovremenog session lock-a; HTML stranica i AJAX istorija vraćaju HTTP 200.
Sama poslovna procedura nije pokrenuta tokom provere. Na ovom računaru nisu pronađeni aktivni
Celery worker/Beat procesi, a pokušaj povezivanja na konfigurisani broker nije uspeo
(OperationalError). Zato automatsko izvršavanje još nije operativno potvrđeno: na okruženju
koje će izvršavati raspored potrebno je obezbediti broker, worker sa novim kodom na redu sync
i jedan Beat proces. Ručno dugme ne zavisi od tih procesa.

## 5 Migracija upita Naplate

Nakon kompletnog inventara i pravila održavanja:

1. Sačuvati definicije postojećih view-ova i izmeriti trenutno vreme izvršavanja.
2. Proveriti lokalni nalog_z prema izvoru po ključevima, godinama, firmama i kontrolnim zbirovima; obuhvat mora zadovoljiti sve zavisne upite.
3. Napraviti uporedne lokalne verzije view-ova, bez trenutne zamene postojećih.
4. Uporediti saldo po partneru, dokumentu i šifri posla, dospeća, sve starosne razrede, ino/grupu, POC, korekcije i duplikate kroz godine. Ne objedinjavati migraciju sa neproverenim izmenama poslovnih pravila.
5. Prebaciti aplikaciju tek kada razlike budu objašnjene, uz mogućnost povratka na prethodne view-ove.

Poreklo i namena istorijskih tabela ne mogu se zaključiti samo iz njihovog imena. Njihovo brisanje, spajanje ili ponovni obračun nisu deo prve korekcije faktura.

## 6 Zajedničko osvežavanje šifarnika

Zajednička procedura ima smisla kada se popišu pojedinačne procedure i njihove zavisnosti. Potrebno je utvrditi redosled, obuhvat firmi i godina, status aktivnih/neaktivnih šifara, pravilo nestalih zapisa i brojače po koraku.

Prednost dati preuzimanju u privremene skupove i kontrolisanoj objavi, da neuspeh jednog izvora ne ostavi delimično prepisane šifarnike. Ne podrazumevati jednu dugu distribuiranu transakciju preko svih udaljenih baza. Predvideti zaključavanje, istoriju grešaka, ponovljivost i upozorenje kada su podaci nepotpuni.

U prvom popisu obuhvatiti partner/grupe partnera, posao, konto i ob_jedin; ostale šifarnike dodati prema potvrđenim zavisnostima. Konkretni nazivi novih procedura i njihov raspored nisu izmišljeni niti implementirani ovim dokumentom. Finansije, Flota i budući centralni registar moraju imati jasno određeno mesto održavanja svakog podatka.
