# IMS ERP — dokumentacija sistema

> **Objedinjeno izdanje.** Sadrži svih 36 poglavlja iz
> `dokumentacija/docs/` u jednom dokumentu, radi štampe i arhiviranja.
> Pojedinačna poglavlja i dalje postoje i **ona se održavaju** — ovaj dokument se
> pravi iz njih i pri svakoj izmeni se pravi ponovo.
>
> Status tvrdnji kroz ceo dokument: **[P]** potvrđeno kodom, bazom ili postojećom
> dokumentacijom, **[Z]** zaključeno, **[N]** nepotvrđeno.

| | |
|---|---|
| **Sistem** | IMS ERP — Django monolit nad Microsoft SQL Server bazom |
| **Obuhvat** | 10 poslovnih modula, 74 obračuna, 48 zabeleženih problema |
| **Sastavljeno** | 18.09.2026. |
| **Izvor** | Izvorni kod, baza, SQL upiti i pogledi, konfiguracija, ekrani i izveštaji |

---

## Sadržaj

- [1. Pregled sistema](#1-pregled-sistema)
    - [1.1. Šta je IMS ERP](#11-šta-je-ims-erp)
    - [1.2. Koji poslovni problem rešava](#12-koji-poslovni-problem-rešava)
    - [1.3. Ko koristi sistem](#13-ko-koristi-sistem)
    - [1.4. Moduli — šta koji radi](#14-moduli--šta-koji-radi)
    - [1.5. Sistem u brojkama](#15-sistem-u-brojkama)
    - [1.6. Radni dan sistema](#16-radni-dan-sistema)
    - [1.7. Šta ograničava sistem](#17-šta-ograničava-sistem)
    - [1.8. Gde dalje](#18-gde-dalje)
- [2. Arhitektura](#2-arhitektura)
    - [2.1. Tip sistema](#21-tip-sistema)
    - [2.2. Slojevi i putanja zahteva](#22-slojevi-i-putanja-zahteva)
    - [2.3. Aplikacije i njihove uloge](#23-aplikacije-i-njihove-uloge)
    - [2.4. Podaci — gde šta živi](#24-podaci--gde-šta-živi)
    - [2.5. Ponavljajući obrasci](#25-ponavljajući-obrasci)
    - [2.6. Kontrola pristupa](#26-kontrola-pristupa)
    - [2.7. Pozadinski poslovi](#27-pozadinski-poslovi)
    - [2.8. Datoteke i mediji](#28-datoteke-i-mediji)
    - [2.9. Postavke po okruženjima](#29-postavke-po-okruženjima)
    - [2.10. Testovi](#210-testovi)
    - [2.11. Sistemi izvan aplikacije](#211-sistemi-izvan-aplikacije)
    - [2.12. Šta arhitektura dobro rešava, a šta ne](#212-šta-arhitektura-dobro-rešava-a-šta-ne)
    - [2.13. Gde dalje](#213-gde-dalje)
- [3. Moduli — sadržaj i veze](#3-moduli--sadržaj-i-veze)
    - [3.0.1. Sadržaj](#301-sadržaj)
    - [3.0.2. Šta koji modul radi — u jednoj rečenici](#302-šta-koji-modul-radi--u-jednoj-rečenici)
    - [3.0.3. Mapa veza između modula](#303-mapa-veza-između-modula)
    - [3.0.4. Ko koristi koji modul](#304-ko-koristi-koji-modul)
    - [3.0.5. Broj ekrana i tabela po modulu [P]](#305-broj-ekrana-i-tabela-po-modulu-p)
    - [3.0.6. Gde nastaje, a gde se samo čita](#306-gde-nastaje-a-gde-se-samo-čita)
    - [3.0.7. Zajednička pravila svih modula](#307-zajednička-pravila-svih-modula)
    - [3.0.8. Gde dalje](#308-gde-dalje)
- [3.1. Vozni park (Flota)](#31-vozni-park-flota)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima automatski](#7-podaci-koje-sistem-preuzima-automatski)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. SQL pogledi i upiti](#9-sql-pogledi-i-upiti)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11. Ulazni i izlazni podaci](#11-ulazni-i-izlazni-podaci)
    - [12. Veze sa drugim modulima](#12-veze-sa-drugim-modulima)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [Gde dalje](#gde-dalje)
- [3.2. Kadrovi](#32-kadrovi)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima automatski](#7-podaci-koje-sistem-preuzima-automatski)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. SQL pogledi i povezani serveri](#9-sql-pogledi-i-povezani-serveri)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11. Ulazni i izlazni podaci](#11-ulazni-i-izlazni-podaci)
    - [12. Veze sa drugim modulima](#12-veze-sa-drugim-modulima)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [Gde dalje](#gde-dalje)
- [3.3. Finansijska analitika](#33-finansijska-analitika)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima automatski](#7-podaci-koje-sistem-preuzima-automatski)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. SQL objekti](#9-sql-objekti)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11. Ulazni i izlazni podaci](#11-ulazni-i-izlazni-podaci)
    - [12. Veze sa drugim modulima](#12-veze-sa-drugim-modulima)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [18. Banke](#18-banke)
    - [Gde dalje](#gde-dalje)
- [3.4. Nabavka](#34-nabavka)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima automatski](#7-podaci-koje-sistem-preuzima-automatski)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. SQL pogledi](#9-sql-pogledi)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11. Ulazni i izlazni podaci](#11-ulazni-i-izlazni-podaci)
    - [12. Veze sa drugim modulima](#12-veze-sa-drugim-modulima)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [Gde dalje](#gde-dalje)
- [3.5. Potraživanja](#35-potraživanja)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima automatski](#7-podaci-koje-sistem-preuzima-automatski)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. SQL pogledi](#9-sql-pogledi)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11. Ulazni i izlazni podaci](#11-ulazni-i-izlazni-podaci)
    - [12. Veze sa drugim modulima](#12-veze-sa-drugim-modulima)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [Gde dalje](#gde-dalje)
- [3.6. Ugovori i partneri](#36-ugovori-i-partneri)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima automatski](#7-podaci-koje-sistem-preuzima-automatski)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. Spoljni izvori](#9-spoljni-izvori)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11–12. Ulaz, izlaz i veze sa modulima](#1112-ulaz-izlaz-i-veze-sa-modulima)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [Gde dalje](#gde-dalje)
- [3.7. Menice](#37-menice)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima automatski](#7-podaci-koje-sistem-preuzima-automatski)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. Spoljni izvori](#9-spoljni-izvori)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11–12. Ulaz, izlaz i veze](#1112-ulaz-izlaz-i-veze)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [Gde dalje](#gde-dalje)
- [3.8. Mobilna telefonija](#38-mobilna-telefonija)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima automatski](#7-podaci-koje-sistem-preuzima-automatski)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. Spoljni izvori](#9-spoljni-izvori)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11–12. Ulaz, izlaz i veze](#1112-ulaz-izlaz-i-veze)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [Gde dalje](#gde-dalje)
- [3.9. Isplate](#39-isplate)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima](#7-podaci-koje-sistem-preuzima)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. Spoljni izvori](#9-spoljni-izvori)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11–12. Ulaz, izlaz i veze](#1112-ulaz-izlaz-i-veze)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [Gde dalje](#gde-dalje)
- [3.10. Administracija](#310-administracija)
    - [1. Naziv modula](#1-naziv-modula)
    - [2. Poslovna namena](#2-poslovna-namena)
    - [3. Korisnici modula](#3-korisnici-modula)
    - [4. Glavne funkcionalnosti](#4-glavne-funkcionalnosti)
    - [5. Glavni korisnički ekrani](#5-glavni-korisnički-ekrani)
    - [6. Podaci koje korisnik unosi](#6-podaci-koje-korisnik-unosi)
    - [7. Podaci koje sistem preuzima automatski](#7-podaci-koje-sistem-preuzima-automatski)
    - [8. Tabele i kolone](#8-tabele-i-kolone)
    - [9. Kako rade dozvole](#9-kako-rade-dozvole)
    - [10. Glavne klase, funkcije i fajlovi](#10-glavne-klase-funkcije-i-fajlovi)
    - [11–12. Ulaz, izlaz i veze](#1112-ulaz-izlaz-i-veze)
    - [13. Izveštaji i analize](#13-izveštaji-i-analize)
    - [14. Uloge i prava pristupa](#14-uloge-i-prava-pristupa)
    - [15. Validacije i kontrole](#15-validacije-i-kontrole)
    - [16. Poznati izuzeci i granični slučajevi](#16-poznati-izuzeci-i-granični-slučajevi)
    - [17. Šta nije moguće objasniti bez dodatnih podataka](#17-šta-nije-moguće-objasniti-bez-dodatnih-podataka)
    - [Gde dalje](#gde-dalje)
- [4. Baza podataka](#4-baza-podataka)
    - [4.1. Osnovno](#41-osnovno)
    - [4.2. Pravilo imenovanja tabela — obavezno pročitati [P]](#42-pravilo-imenovanja-tabela--obavezno-pročitati-p)
    - [4.3. Zajedničke osnove — `core` (tabele u `fleet_*`)](#43-zajedničke-osnove--core-tabele-u-fleet_)
    - [4.4. Vozni park — `fleet`](#44-vozni-park--fleet)
    - [4.5. Kadrovi — `hr`](#45-kadrovi--hr)
    - [4.6. Finansijska analitika — `finansije`](#46-finansijska-analitika--finansije)
    - [4.7. Nabavka — `nabavka`](#47-nabavka--nabavka)
    - [4.8. Potraživanja — `potrazivanja`](#48-potraživanja--potrazivanja)
    - [4.9. Ugovori — `ugovori`](#49-ugovori--ugovori)
    - [4.10. Menice — `menice`](#410-menice--menice)
    - [4.11. Mobilna telefonija — `mobilni`](#411-mobilna-telefonija--mobilni)
    - [4.12. Nasleđeni objekti baze (`dbo.*`)](#412-nasleđeni-objekti-baze-dbo)
    - [4.13. Nasleđeni modul Naplata — van obuhvata](#413-nasleđeni-modul-naplata--van-obuhvata)
    - [4.14. Kontrolna pravila koja baza sama proverava](#414-kontrolna-pravila-koja-baza-sama-proverava)
    - [4.15. Gde dalje](#415-gde-dalje)
- [5. Poslovni procesi](#5-poslovni-procesi)
    - [5.0. Spisak procesa](#50-spisak-procesa)
    - [5.1. Popravka vozila — od kvara do troška](#51-popravka-vozila--od-kvara-do-troška)
    - [5.2. Službeno putovanje — od naloga do isplate](#52-službeno-putovanje--od-naloga-do-isplate)
    - [5.3. Zaduženje vozila — od preuzimanja do obračuna](#53-zaduženje-vozila--od-preuzimanja-do-obračuna)
    - [5.4. Mesečni obračun mobilnih telefona](#54-mesečni-obračun-mobilnih-telefona)
    - [5.5. Mesečna radna lista i ocenjivanje](#55-mesečna-radna-lista-i-ocenjivanje)
    - [5.6. Noćno preuzimanje podataka](#56-noćno-preuzimanje-podataka)
    - [5.7. Naplata potraživanja](#57-naplata-potraživanja)
    - [5.8. Zaključenje ugovora](#58-zaključenje-ugovora)
    - [5.9. Mesečno praćenje rezultata](#59-mesečno-praćenje-rezultata)
    - [5.10. Šta nijedan proces ne obuhvata](#510-šta-nijedan-proces-ne-obuhvata)
    - [5.11. Gde dalje](#511-gde-dalje)
- [6. Analize i obračuni — sadržaj](#6-analize-i-obračuni--sadržaj)
    - [6.0.1. Kako je opisan svaki obračun](#601-kako-je-opisan-svaki-obračun)
    - [6.0.2. Zbirni pregled](#602-zbirni-pregled)
    - [6.1. Finansijska analitika (18 obračuna)](#61-finansijska-analitika-18-obračuna)
    - [6.2. Flota — gorivo (8 obračuna) ✔](#62-flota--gorivo-8-obračuna-)
    - [6.3. Flota — troškovi (8 obračuna) ✔](#63-flota--troškovi-8-obračuna-)
    - [6.4. Flota — polise, lizing i servisi (4 obračuna) ✔](#64-flota--polise-lizing-i-servisi-4-obračuna-)
    - [6.5. Flota — kilometraža, održavanje i izveštaji (4 + 11) ✔](#65-flota--kilometraža-održavanje-i-izveštaji-4--11-)
    - [6.6. Kadrovi (9 obračuna) — u pripremi](#66-kadrovi-9-obračuna--u-pripremi)
    - [6.7. Mobilna telefonija (4 obračuna) — u pripremi](#67-mobilna-telefonija-4-obračuna--u-pripremi)
    - [6.8. Potraživanja (6 analiza) — u pripremi](#68-potraživanja-6-analiza--u-pripremi)
    - [6.9. Nabavka (6 analiza) — u pripremi](#69-nabavka-6-analiza--u-pripremi)
    - [6.10. Isplate (3 obračuna) — u pripremi](#610-isplate-3-obračuna--u-pripremi)
    - [6.11. Ugovori i menice (4 analize) — u pripremi](#611-ugovori-i-menice-4-analize--u-pripremi)
    - [6.0.3. Obračuni po korisniku](#603-obračuni-po-korisniku)
    - [6.0.4. Obračuni čiji rezultat ide izvan sistema](#604-obračuni-čiji-rezultat-ide-izvan-sistema)
    - [6.0.5. Gde dalje](#605-gde-dalje)
- [6.1. Finansijska analitika — obračuni](#61-finansijska-analitika--obračuni)
    - [6.1.0. Šta ovo poglavlje pokriva](#610-šta-ovo-poglavlje-pokriva)
    - [6.1.1. Registar obračuna](#611-registar-obračuna)
    - [6.1.2. Sedam pravila koja objašnjavaju većinu nedoumica](#612-sedam-pravila-koja-objašnjavaju-većinu-nedoumica)
    - [6.1.3. Period, centar i obuhvat pristupa](#613-period-centar-i-obuhvat-pristupa)
    - [6.1.4. Odakle Finansije čitaju](#614-odakle-finansije-čitaju)
    - [6.1.5. Prihodi, rashodi i rezultat bez ZT](#615-prihodi-rashodi-i-rezultat-bez-zt)
    - [6.1.6. Zajednički troškovi i rezultat posle raspodele](#616-zajednički-troškovi-i-rezultat-posle-raspodele)
    - [6.1.7. Priliv, odliv i neto gotovina](#617-priliv-odliv-i-neto-gotovina)
    - [6.1.8. Grafikoni, učešća i rangiranje](#618-grafikoni-učešća-i-rangiranje)
    - [6.1.9. Fakture IF i interne ON](#619-fakture-if-i-interne-on)
    - [6.1.10. Struktura rashoda po kontima](#6110-struktura-rashoda-po-kontima)
    - [6.1.11. Zaposleni i zarade](#6111-zaposleni-i-zarade)
    - [6.1.12. Vozila, zaduženja i putni nalozi](#6112-vozila-zaduženja-i-putni-nalozi)
    - [6.1.13. Potraživanja na detalju posla](#6113-potraživanja-na-detalju-posla)
    - [6.1.14. Knjiženja, grupisanja i broj redova](#6114-knjiženja-grupisanja-i-broj-redova)
    - [6.1.15. Nule, nedostajući podaci, znakovi i sortiranje](#6115-nule-nedostajući-podaci-znakovi-i-sortiranje)
    - [6.1.16. Sinhronizacija, istorija i procedure](#6116-sinhronizacija-istorija-i-procedure)
    - [6.1.17. Kontrolni postupak](#6117-kontrolni-postupak)
    - [6.1.18. Šta Finansije ne rade](#6118-šta-finansije-ne-rade)
    - [6.1.19. Problemi iz ovog poglavlja](#6119-problemi-iz-ovog-poglavlja)
    - [6.1.20. Otvorena pitanja](#6120-otvorena-pitanja)
    - [Mapa izvornog koda](#mapa-izvornog-koda)
    - [Gde dalje](#gde-dalje)
    - [Dodatne analize po šifri posla — dopuna 21.09.2026.](#dodatne-analize-po-šifri-posla--dopuna-21092026)
    - [6.1.21. Banke po računima](#6121-banke-po-računima)
- [6.2. Flota — obračuni goriva](#62-flota--obračuni-goriva)
    - [Zajednička osnova: šta se uopšte smatra gorivom](#zajednička-osnova-šta-se-uopšte-smatra-gorivom)
    - [V-03 — Neto iznos goriva iz bruto iznosa](#v-03--neto-iznos-goriva-iz-bruto-iznosa)
    - [V-04 — Iznosi OMV transakcije](#v-04--iznosi-omv-transakcije)
    - [V-05 — Iznosi NIS transakcije](#v-05--iznosi-nis-transakcije)
    - [V-06 — Prečišćavanje OMV transakcija](#v-06--prečišćavanje-omv-transakcija)
    - [V-01 — Prosečna potrošnja goriva (poslednjih 10 točenja)](#v-01--prosečna-potrošnja-goriva-poslednjih-10-točenja)
    - [V-02 — Prosečna potrošnja goriva za ceo vek vozila](#v-02--prosečna-potrošnja-goriva-za-ceo-vek-vozila)
    - [V-21 — Gorivo po šifri posla](#v-21--gorivo-po-šifri-posla)
    - [V-23 — Obračun goriva na putnom nalogu vozila](#v-23--obračun-goriva-na-putnom-nalogu-vozila)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
    - [V-24 — Potrošnja goriva u detalju vozila](#v-24--potrošnja-goriva-u-detalju-vozila)
- [6.3. Flota — troškovi vozila](#63-flota--troškovi-vozila)
    - [V-08 — Procena pređene kilometraže u periodu](#v-08--procena-pređene-kilometraže-u-periodu)
    - [V-07 — Trošak po kilometru po vozilu](#v-07--trošak-po-kilometru-po-vozilu)
    - [V-11 — Pragovi fiksnog troška po kilometru](#v-11--pragovi-fiksnog-troška-po-kilometru)
    - [V-12 — Status vozila prema trošku po kilometru](#v-12--status-vozila-prema-trošku-po-kilometru)
    - [V-09 — Analiza troška po km kroz više perioda](#v-09--analiza-troška-po-km-kroz-više-perioda)
    - [V-10 — Neto trošak održavanja](#v-10--neto-trošak-održavanja)
    - [V-15 — Analitika evidentiranih troškova na detalju vozila](#v-15--analitika-evidentiranih-troškova-na-detalju-vozila)
    - [V-24 — Statistika po centrima](#v-24--statistika-po-centrima)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
- [6.4. Flota — polise, lizing i servisi](#64-flota--polise-lizing-i-servisi)
    - [Zajednička osnova: istorijska šifra posla](#zajednička-osnova-istorijska-šifra-posla)
    - [V-17 — Mesečni troškovi polisa](#v-17--mesečni-troškovi-polisa)
    - [V-18 — Polise pred istekom i neobnovljene polise](#v-18--polise-pred-istekom-i-neobnovljene-polise)
    - [V-19 — Mesečni troškovi lizinga](#v-19--mesečni-troškovi-lizinga)
    - [V-20 — Mesečni troškovi servisa](#v-20--mesečni-troškovi-servisa)
    - [Novi problemi iz ovog poglavlja](#novi-problemi-iz-ovog-poglavlja)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
- [6.5. Flota — kilometraža, održavanje, presek stanja i izveštaji](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji)
    - [V-13 — Kilometraža vozila — posmatrana vremenska linija](#v-13--kilometraža-vozila--posmatrana-vremenska-linija)
    - [V-14 — Održavanje vozila i servisni interval](#v-14--održavanje-vozila-i-servisni-interval)
    - [V-16 — Presek stanja flote (kontrolna tabla)](#v-16--presek-stanja-flote-kontrolna-tabla)
    - [V-22 — Izveštaji za upravu](#v-22--izveštaji-za-upravu)
    - [6.5.5. Izveštaji nad nasleđenim pogledima](#655-izveštaji-nad-nasleđenim-pogledima)
    - [Novi problemi iz ovog poglavlja](#novi-problemi-iz-ovog-poglavlja)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
- [6.6. Kadrovi — obračuni](#66-kadrovi--obračuni)
    - [Zajednička osnova: odakle dolaze kadrovski podaci](#zajednička-osnova-odakle-dolaze-kadrovski-podaci)
    - [K-01 — Dnevni sati rada iz evidencije prolazaka](#k-01--dnevni-sati-rada-iz-evidencije-prolazaka)
    - [K-02 — Dnevni sati iz obračunatih parova (drugi postupak)](#k-02--dnevni-sati-iz-obračunatih-parova-drugi-postupak)
    - [K-03 — Problemi u parovima prolazaka](#k-03--problemi-u-parovima-prolazaka)
    - [K-04 i K-05 — Sati radne liste](#k-04-i-k-05--sati-radne-liste)
    - [K-06 — Godišnji odmori — dodele i rešenja](#k-06--godišnji-odmori--dodele-i-rešenja)
    - [K-07 — Bolovanja — uvoz RFZO i povezivanje](#k-07--bolovanja--uvoz-rfzo-i-povezivanje)
    - [K-08 — Ocenjivanje zaposlenih — stimulacija i lični koeficijent](#k-08--ocenjivanje-zaposlenih--stimulacija-i-lični-koeficijent)
    - [K-09 — Tok saglasnosti na ocenu](#k-09--tok-saglasnosti-na-ocenu)
    - [K-10 — Rešenja zaposlenih — izrada teksta dokumenta](#k-10--rešenja-zaposlenih--izrada-teksta-dokumenta)
    - [K-11 — Predlog popunjavanja radne liste](#k-11--predlog-popunjavanja-radne-liste)
    - [Novi problemi iz ovog poglavlja](#novi-problemi-iz-ovog-poglavlja)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
- [6.7. Mobilna telefonija — obračuni](#67-mobilna-telefonija--obračuni)
    - [Zajednička osnova: četiri evidencije](#zajednička-osnova-četiri-evidencije)
    - [M-04 — Povezivanje broja telefona sa zaposlenim](#m-04--povezivanje-broja-telefona-sa-zaposlenim)
    - [M-02 — Izuzeci od parkinga](#m-02--izuzeci-od-parkinga)
    - [M-01 — Obustava po zaposlenom](#m-01--obustava-po-zaposlenom)
    - [M-03 — Razvrstavanje zaposleni / bivši / nezaposleni](#m-03--razvrstavanje-zaposleni--bivši--nezaposleni)
    - [Novi problemi iz ovog poglavlja](#novi-problemi-iz-ovog-poglavlja)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
- [6.8. Potraživanja — obračuni](#68-potraživanja--obračuni)
    - [Zajednička osnova: zašto Potraživanja postoje](#zajednička-osnova-zašto-potraživanja-postoje)
    - [PT-01 — Starosni razredi (baketi)](#pt-01--starosni-razredi-baketi)
    - [PT-02 — Saldo stavke](#pt-02--saldo-stavke)
    - [PT-03 — Objavljivanje snimka stanja](#pt-03--objavljivanje-snimka-stanja)
    - [PT-04 — Kontrolni zbirovi i provera izvora](#pt-04--kontrolni-zbirovi-i-provera-izvora)
    - [PT-05 — Saldo po šiframa posla](#pt-05--saldo-po-šiframa-posla)
    - [PT-06 — Normalizacija nasleđenih kontakata](#pt-06--normalizacija-nasleđenih-kontakata)
    - [Novi problemi iz ovog poglavlja](#novi-problemi-iz-ovog-poglavlja)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
- [6.9. Nabavka — obračuni i analize](#69-nabavka--obračuni-i-analize)
    - [Zajednička osnova: tri izvora i tri snimka](#zajednička-osnova-tri-izvora-i-tri-snimka)
    - [B-01 — Procenjena vrednost stavke i predmeta](#b-01--procenjena-vrednost-stavke-i-predmeta)
    - [B-03 — Ključ EUF fakture](#b-03--ključ-euf-fakture)
    - [B-02 — Grupisanje UF stavki u UF fakture](#b-02--grupisanje-uf-stavki-u-uf-fakture)
    - [B-04 — Razlike verzija plana javnih nabavki](#b-04--razlike-verzija-plana-javnih-nabavki)
    - [B-05 — Provera šifre posla partnera](#b-05--provera-šifre-posla-partnera)
    - [B-06 — Izveštaji i alarmi nabavke](#b-06--izveštaji-i-alarmi-nabavke)
    - [B-07 — Poklapanje robe sa UF ili EUF fakturom](#b-07--poklapanje-robe-sa-uf-ili-euf-fakturom)
    - [Novi problemi iz ovog poglavlja](#novi-problemi-iz-ovog-poglavlja)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
- [6.10. Isplate — virmani](#610-isplate--virmani)
    - [Zajednička osnova](#zajednička-osnova)
    - [I-02 — Kontrole naloga pre virmana](#i-02--kontrole-naloga-pre-virmana)
    - [I-01 — Generisanje datoteke virmana](#i-01--generisanje-datoteke-virmana)
    - [I-03 — Konverzija virmana u JSON](#i-03--konverzija-virmana-u-json)
    - [Novi problemi iz ovog poglavlja](#novi-problemi-iz-ovog-poglavlja)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
- [6.11. Ugovori i menice — analize](#611-ugovori-i-menice--analize)
    - [U-02 — Sinhronizacija partnera iz finansija](#u-02--sinhronizacija-partnera-iz-finansija)
    - [U-01 — Provera statusa partnera u APR-u](#u-01--provera-statusa-partnera-u-apr-u)
    - [U-03 — Preuzimanje menica iz registra NBS](#u-03--preuzimanje-menica-iz-registra-nbs)
    - [U-04 — Povezivanje menica i garancija sa ugovorima](#u-04--povezivanje-menica-i-garancija-sa-ugovorima)
    - [Novi problemi iz ovog poglavlja](#novi-problemi-iz-ovog-poglavlja)
    - [Nova pitanja iz ovog poglavlja](#nova-pitanja-iz-ovog-poglavlja)
    - [Gde dalje](#gde-dalje)
- [6.12. Flota — analitika namene, raspolaganja i ekonomskih alternativa](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa)
    - [E-01 — Zajednička analitika flote i vozila](#e-01--zajednička-analitika-flote-i-vozila)
    - [E-02 — Sačuvano poređenje budućih alternativa](#e-02--sačuvano-poređenje-budućih-alternativa)
    - [Uvođenje i prelaz sa ranije analitike](#uvođenje-i-prelaz-sa-ranije-analitike)
- [7. Integracije](#7-integracije)
    - [7.1. Pregled](#71-pregled)
    - [7.2. Povezani serveri (SQL)](#72-povezani-serveri-sql)
    - [7.3. Nasleđeni pogledi u bazi `IMS_ERP`](#73-nasleđeni-pogledi-u-bazi-ims_erp)
    - [7.4. NIS i OMV — gorivo (Selenium)](#74-nis-i-omv--gorivo-selenium)
    - [7.5. Registar menica NBS](#75-registar-menica-nbs)
    - [7.6. APR OpenAPI](#76-apr-openapi)
    - [7.7. Ručni uvoz datoteka](#77-ručni-uvoz-datoteka)
    - [7.8. Izlaz iz sistema](#78-izlaz-iz-sistema)
    - [7.9. Šta sistem NE radi](#79-šta-sistem-ne-radi)
    - [7.10. Pregled rizika integracija](#710-pregled-rizika-integracija)
    - [7.11. Gde dalje](#711-gde-dalje)
- [8. Instalacija i pokretanje](#8-instalacija-i-pokretanje)
    - [8.1. Šta je potrebno](#81-šta-je-potrebno)
    - [8.2. Razvojno okruženje](#82-razvojno-okruženje)
    - [8.3. Postavke po okruženjima](#83-postavke-po-okruženjima)
    - [8.4. Testovi](#84-testovi)
    - [8.5. Produkciono okruženje](#85-produkciono-okruženje)
    - [8.6. Prvo puštanje u rad](#86-prvo-puštanje-u-rad)
    - [8.7. Struktura projekta](#87-struktura-projekta)
    - [8.8. Provera da sve radi](#88-provera-da-sve-radi)
    - [8.9. Šta treba dopuniti u ovoj dokumentaciji](#89-šta-treba-dopuniti-u-ovoj-dokumentaciji)
    - [8.10. Gde dalje](#810-gde-dalje)
- [9. Održavanje](#9-održavanje)
    - [9.1. Šta se svakodnevno dešava samo od sebe](#91-šta-se-svakodnevno-dešava-samo-od-sebe)
    - [9.2. Tabela zakazanih poslova](#92-tabela-zakazanih-poslova)
    - [9.3. Kako proveriti da je sve prošlo](#93-kako-proveriti-da-je-sve-prošlo)
    - [9.4. Windows servisi](#94-windows-servisi)
    - [9.5. Posle isporuke novog koda](#95-posle-isporuke-novog-koda)
    - [9.6. Česti problemi i šta uraditi](#96-česti-problemi-i-šta-uraditi)
    - [9.7. Redovne provere](#97-redovne-provere)
    - [9.8. Ručno pokretanje poslova](#98-ručno-pokretanje-poslova)
    - [9.9. Šta ne raditi](#99-šta-ne-raditi)
    - [9.10. Gde dalje](#910-gde-dalje)
- [10. Poznati problemi i ograničenja](#10-poznati-problemi-i-ograničenja)
    - [10.1. Kako čitati registar](#101-kako-čitati-registar)
    - [10.2. Zbirni pregled](#102-zbirni-pregled)
    - [10.3. Bezbednost i konfiguracija](#103-bezbednost-i-konfiguracija)
    - [10.4. Obračuni — Flota](#104-obračuni--flota)
    - [10.4.1. Obračuni — Kadrovi](#1041-obračuni--kadrovi)
    - [10.4.2. Obračuni — Mobilna telefonija](#1042-obračuni--mobilna-telefonija)
    - [10.4.3. Obračuni — Isplate](#1043-obračuni--isplate)
    - [10.4.4. Obračuni — Potraživanja](#1044-obračuni--potraživanja)
    - [10.4.5. Obračuni — Nabavka](#1045-obračuni--nabavka)
    - [10.4.6. Obračuni — Ugovori i menice](#1046-obračuni--ugovori-i-menice)
    - [10.4.7. Obračuni — Finansijska analitika](#1047-obračuni--finansijska-analitika)
    - [10.4.8. Struktura baze](#1048-struktura-baze)
    - [10.5. Infrastruktura](#105-infrastruktura)
    - [10.6. Podaci i moduli](#106-podaci-i-moduli)
    - [10.7. Repozitorijum](#107-repozitorijum)
    - [10.8. Ograničenja koja nisu greške](#108-ograničenja-koja-nisu-greške)
    - [10.9. Šta je proveravano i **nije** problem](#109-šta-je-proveravano-i-nije-problem)
    - [10.10. Gde dalje](#1010-gde-dalje)
- [11. Plan razvoja](#11-plan-razvoja)
    - [11.1. Šta je već isplanirano](#111-šta-je-već-isplanirano)
    - [11.2. Centralna organizacija i dozvole (V2)](#112-centralna-organizacija-i-dozvole-v2)
    - [11.3. Gašenje nasleđene Naplate](#113-gašenje-nasleđene-naplate)
    - [11.4. Preuzimanje definicija nasleđenih pogleda](#114-preuzimanje-definicija-nasleđenih-pogleda)
    - [11.5. Prioriteti iz registra problema](#115-prioriteti-iz-registra-problema)
    - [11.6. Predlozi koji proizlaze iz ovog pregleda](#116-predlozi-koji-proizlaze-iz-ovog-pregleda)
    - [11.7. Otvorena pitanja koja čekaju odgovor](#117-otvorena-pitanja-koja-čekaju-odgovor)
    - [11.8. Šta NE treba menjati](#118-šta-ne-treba-menjati)
    - [11.9. Gde dalje](#119-gde-dalje)
- [12. Rečnik pojmova i mapiranje naziva](#12-rečnik-pojmova-i-mapiranje-naziva)
    - [12.1. Poslovni pojmovi](#121-poslovni-pojmovi)
    - [12.2. Naziv na ekranu ↔ u kodu ↔ u bazi](#122-naziv-na-ekranu--u-kodu--u-bazi)
    - [12.3. Skraćenice](#123-skraćenice)
    - [12.4. Pojmovi koje treba razlikovati](#124-pojmovi-koje-treba-razlikovati)
    - [12.5. Gde dalje](#125-gde-dalje)
- [Prilog A — Pregled za upravu](#prilog-a--pregled-za-upravu)
    - [1. Šta je IMS ERP](#1-šta-je-ims-erp)
    - [2. Šta je realizovano](#2-šta-je-realizovano)
    - [3. Koje poslove aplikacija podržava](#3-koje-poslove-aplikacija-podržava)
    - [4. Šta se automatizovalo](#4-šta-se-automatizovalo)
    - [5. Šta aplikacija računa](#5-šta-aplikacija-računa)
    - [6. Ko koristi sistem](#6-ko-koristi-sistem)
    - [7. Veza sa drugim sistemima](#7-veza-sa-drugim-sistemima)
    - [8. Kontrole i sledljivost](#8-kontrole-i-sledljivost)
    - [9. Šta je Institut dobio](#9-šta-je-institut-dobio)
    - [10. Trenutna ograničenja](#10-trenutna-ograničenja)
    - [11. Utvrđeni rizici](#11-utvrđeni-rizici)
    - [12. Preporuke](#12-preporuke)
    - [13. Zaključak](#13-zaključak)
    - [Prilozi](#prilozi)
- [Prilog B — DDL nasleđenih SQL pogleda](#prilog-b--ddl-nasleđenih-sql-pogleda)
    - [Šta je gde](#šta-je-gde)
    - [Šta je provera u bazi pokazala (21.09.2026.)](#šta-je-provera-u-bazi-pokazala-21092026)
    - [Pogledi Naplate — šta koji radi](#pogledi-naplate--šta-koji-radi)
    - [`fleet_trebovanja` — trebovanja Flote](#fleet_trebovanja--trebovanja-flote)
    - [`nbv_roba` — roba za Nabavku](#nbv_roba--roba-za-nabavku)
    - [Šta još nedostaje](#šta-još-nedostaje)

---

## 1. Pregled sistema

> **Za koga je ovo poglavlje:** za sve — poslovne korisnike, programere i rukovodstvo.
> Objašnjava šta IMS ERP radi, ko ga koristi i kako se uklapa u postojeće poslovanje.
> Tehnički detalji su u [2. Arhitektura](#2-arhitektura).

---

### 1.1. Šta je IMS ERP

IMS ERP je **interna web aplikacija Instituta IMS a.d.** koja objedinjuje evidencije i
analize iz deset poslovnih oblasti u jedan sistem sa jedinstvenom prijavom, jedinstvenim
šifarnikom organizacionih jedinica i jedinstvenim pravilima pristupa.

Sistemu se pristupa pregledačem, sa adrese na internoj mreži. Nema mobilne aplikacije,
nema javnog pristupa sa interneta i nema programskog interfejsa (API) za spoljne sisteme.

#### Šta sistem nije

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

### 1.2. Koji poslovni problem rešava

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

### 1.3. Ko koristi sistem

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

### 1.4. Moduli — šta koji radi

#### Flota (vozni park)

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

#### Kadrovi

- **Zaposleni** — evidencija sinhronizovana iz kadrovske baze, sa CV stavkama.
- **Radna lista** — mesečna evidencija sati po šiframa posla, sa predlogom sati iz
  evidencije prolazaka kroz sistem kontrole pristupa.
- **Godišnji odmori** — dodele i rešenja preuzeti iz izvora.
- **Bolovanja** — uvoz iz RFZO izvoza, povezivanje po matičnom broju.
- **Ocenjivanje** — merila, bodovi, koeficijent stimulacije, saglasnost u tri nivoa
  (neposredni rukovodilac → direktor centra → generalni direktor).

#### Finansijska analitika

Dnevno osvežena slika poslovanja po šifri posla i centru:
prihodi, rashodi, rezultat, zajednički troškovi, rezultat posle raspodele,
priliv, odliv i neto gotovina, uz detalj sa fakturama, kontima, vozilima, zaposlenima,
putnim nalozima i potraživanjima.

#### Nabavka

Predmeti nabavke (zahtev za nabavku, zahtev za uslugu, predlog za opremu), stavke,
povezivanje sa ulaznim fakturama i robom, ugovori, narudžbenice, plan javnih nabavki
sa verzijama i razlikama između verzija, alarmi.

#### Potraživanja

Dugovanja kupaca sa starosnom strukturom, objavljeni snimci stanja, kontakti,
telefonski pozivi, opomene, pozivna pisma i pravni postupci.
**Zamenjuje nasleđeni modul Naplata.**

#### Ugovori

Partneri (sa proverom statusa u APR-u), zahtevi, ponude, ugovori i aneksi,
dokumenti uz ugovor, stranke, garancije i veze sa menicama.

#### Menice

Ulazne i izlazne menice, sa mogućnošću preuzimanja podataka iz Registra menica
Narodne banke Srbije.

#### Mobilna telefonija

Paketi, korisnici, dodele brojeva po mesecima, potrošnja i **obračun obustave po
zaposlenom** koja ide u obračun zarada.

#### Isplate

Generisanje datoteke virmana za elektronsko bankarstvo, za neoporeziva primanja
zaposlenih po putnim nalozima.

#### Administracija

Korisnici, uloge i dozvole, evidencija rada korisnika (ko je šta otvorio i promenio),
istorija zakazanih poslova.

---

### 1.5. Sistem u brojkama

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

### 1.6. Radni dan sistema

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

### 1.7. Šta ograničava sistem

> Detaljno u [10. Poznati problemi](#10-poznati-problemi-i-ograničenja).

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

### 1.8. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako je sistem tehnički sastavljen? | [2. Arhitektura](#2-arhitektura) |
| Šta tačno radi pojedini modul? | [3. Moduli](#3-moduli--sadržaj-i-veze) |
| Koje tabele i pogledi postoje? | [4. Baza podataka](#4-baza-podataka) |
| Kako teče posao od početka do kraja? | [5. Poslovni procesi](#5-poslovni-procesi) |
| Kako se računa određeni iznos? | [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj) |
| Odakle dolaze podaci spolja? | [7. Integracije](#7-integracije) |
| Šta znači neki pojam? | [12. Rečnik pojmova](#12-rečnik-pojmova-i-mapiranje-naziva) |

---

## 2. Arhitektura

> **Za koga je ovo poglavlje:** za programere i AI agente. Poslovni korisnici mogu
> preskočiti na [3. Moduli](#3-moduli--sadržaj-i-veze).
> Sve tvrdnje su označene: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 2.1. Tip sistema

**Django monolit.** [P] Jedan proces opslužuje sve module; nema mikroservisa,
nema REST API-ja, nema odvojenog frontend okvira.

| Sloj | Tehnologija | Napomena |
|---|---|---|
| Prikaz | Django templates + DataTables + Select2 + widget-tweaks | 280 HTML šablona |
| Aplikacija | Django 5.0.9, Python 3.12 | 11 Django aplikacija |
| Obračuni | Obični Python moduli (`services/`, `support/`) | Bez okvira, bez klasa gde nisu potrebne |
| Pristup podacima | Django ORM (`default`) + sirovi SQL (`server_db`) | Dva aliasa, ista baza |
| Baza | Microsoft SQL Server, `mssql-django` 1.5, ODBC Driver 17 | Baza `IMS_ERP` |
| Pozadinski poslovi | Celery 5.4 + Redis + `django-celery-beat` | 19 zakazanih poslova |
| Okruženje | Windows server, NSSM servisi | Tri servisa |

`djangorestframework` i `psycopg2-binary` postoje u `requirements.txt`, ali **nisu**
u `INSTALLED_APPS` niti se koriste u kodu. [Z]

---

### 2.2. Slojevi i putanja zahteva

```
 Pregledač
     │  HTTP
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ MIDDLEWARE                                                      │
│   SecurityMiddleware → Session → Common → CSRF → Authentication  │
│   → core.middleware.ActivityLogMiddleware  ← beleži svaki zahtev │
│   → Messages → XFrameOptions                                     │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ URL RAZREŠAVANJE          ims_erp/urls.py → <app>/urls.py        │
│   Ime rute (view_name) ISTOVREMENO je i kod dozvole.             │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ VIEW      LoginRequiredMixin + RolePermissionRequiredMixin       │
│           Zadatak: pročitati parametre, pozvati servis, vratiti  │
│           kontekst šablonu. BEZ poslovne logike.                 │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ SERVIS / SUPPORT      Sva poslovna logika i svi obračuni.        │
│                       Bez pristupa `request`-u gde god je moguće.│
└─────────────────────────────────────────────────────────────────┘
     │
     ├──► Django ORM ─────────► alias `default`   ─┐
     └──► connections['server_db'].cursor() ──────┤──► SQL Server IMS_ERP
                                                   │
                                                   └──► povezani serveri
```

**Pravilo koje kod dosledno poštuje [P]:** `views/` prikazuje, `services/` i `support/`
računaju. Ako tražiš formulu, ona **nije** u view-u.

---

### 2.3. Aplikacije i njihove uloge

| Aplikacija | Uloga | Ima ekrane |
|---|---|---|
| `core` | Korisnici, uloge, dozvole, evidencija rada, istorija zadataka, prebacivanje modula | Samo `switch-app` |
| `fleet` | Vozni park **+ korenske rute sistema** (prijava, kontrolna tabla, korisnici, log) | Da (115) |
| `hr` | Kadrovi | Da (25) |
| `finansije` | Finansijska analitika | Da (16) |
| `nabavka` | Nabavka | Da (24) |
| `potrazivanja` | Potraživanja | Da (10) |
| `ugovori` | Partneri i ugovori | Da (20) |
| `menice` | Menice | Da (6) |
| `mobilni` | Mobilna telefonija | Da (16) |
| `isplate` | Virmani | Da (2) |
| `naplata` | **Nasleđeno, u gašenju** | Da (27) |

#### Zamke u organizaciji aplikacija [P]

1. **`core` i `hr` upisuju tabele u `fleet`.** Modeli u `core/models.py` i deo modela u
   `hr/models.py` imaju `class Meta: app_label = "fleet"`. Fizičke tabele su zato
   `fleet_employee`, `fleet_activity_log`, `fleet_task_history`, `fleet_organizationalunit`,
   a **ne** `core_*` ni `hr_*`.

2. **`Employee` ima dva imena.** Definisan je u `hr/models.py`, uvozi se kao
   `from hr.models import Employee`, ali se u vezama navodi kao `"fleet.Employee"`
   (npr. `CustomUser.employee`, `MobileUser.employee`). To je isti model.

3. **`izvestaji/` je prazan direktorijum** — nije Django aplikacija i nije u `INSTALLED_APPS`.

4. **Bočni meniji ≠ aplikacije.** Meni `kadrovi` koristi `hr`. Meni `pravna` jeste
   aplikacija `pravna`, ali pored nje prikazuje i `ugovori`. Prebacivanje se čuva u sesiji
   (`request.session["current_app"]`) preko `core/context_processors.py`.

5. **Pravna služba je preseljena iz `naplata` u `pravna`** (rute `pravna:*` umesto
   `naplata:pravna_*`). Tabele `postupak` i `promena_postupka` nisu menjane — selidba je
   izvedena kroz `SeparateDatabaseAndState`, a stare dozvole su preslikane migracijom
   `fleet/0079_pravna_permission_codes.py`.

---

### 2.4. Podaci — gde šta živi

#### 2.4.1. Konekcije [P]

| Alias | Motor | Baza | Server | Namena |
|---|---|---|---|---|
| `default` | `mssql` | `IMS_ERP` | `SMS-SERVER` | Django ORM, migracije |
| `server_db` | `mssql` | `IMS_ERP` | `SMS-SERVER` | Sirovi SQL nad nasleđenim `dbo.*` objektima |
| `local` | `sqlite3` | `db.sqlite3` | — | Definisan u `production.py`, **ne koristi se** |

**`default` i `server_db` su ista fizička baza.** [P] Razdvojeni su namenski, ne fizički.
Django aplikacija i nasleđeni ERP dele bazu `IMS_ERP`.

Podrazumevane postavke veze prema SQL Serveru primenjuje
`ims_erp/settings/base.py: apply_mssql_connection_defaults()` [P]:

| Postavka | Vrednost | Svrha |
|---|---|---|
| `CONN_MAX_AGE` | 300 s | Manje ponovnih povezivanja u dugotrajnim Celery procesima |
| `CONN_HEALTH_CHECKS` | uključeno | Provera veze pre upotrebe |
| `connection_timeout` | 10 s | |
| `query_timeout` | 90 s | Za `sp_AzurirajNalogZ` se privremeno diže na 900 s |
| `connection_retries` | 3, sa pauzom 5 s | |
| `TrustServerCertificate` | `yes` | |

#### 2.4.2. Povezani serveri — **najvažniji arhitektonski nalaz** [P]

Sistem **ne čita sve iz lokalne baze**. Ključni podaci dolaze sa udaljenih servera:

| Povezani server | Baza | Objekti | Ko čita |
|---|---|---|---|
| `PUTGEO-SERVER` | `bazaims` | `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | `finansije/services/source.py`, `potrazivanja/services/source.py` |
| `PUTGEO-SERVER` | `bazaldims` | `Zarada`, `PomLD`, `Radnik`, `element` | `finansije/services/job_people.py`, `cash_flow.py` |
| `INFORMATIKA23` | `ID` | `Radnici`, `C_Prolasci_Radnika`, `C_Tasteri`, `c_parovi_radnika_detalji` | `hr/services/attendance.py` |
| `SERFIN` | `bazaldims` | `radnik` | `hr/services/attendance.py` |

**Posledice [Z]:**

- Dostupnost Finansija i Kadrova zavisi od tri udaljena servera.
- Deo nasleđenih `dbo.*` pogleda u `IMS_ERP` **interno** takođe prelazi na udaljeni server,
  pa „lokalno“ ne znači i „brzo“ ni „nezavisno“.
- `nalog_z` postoji dvaput: **izvor** na `PUTGEO-SERVER.bazaims` i **lokalna kopija**
  `IMS_ERP.dbo.nalog_z` koju puni `sp_AzurirajNalogZ`. Finansijska analitika čita
  **udaljeni** izvor u svoju tabelu `LedgerEntry`. Pokretanje procedure osvežava samo
  lokalnu kopiju i **ne prebacuje** nijedan upit na nju. [P]

#### 2.4.3. Tri vrste podataka u sistemu [Z]

| Vrsta | Vlasnik podatka | Primeri | Sme li se menjati iz aplikacije |
|---|---|---|---|
| **Sopstveni** | IMS ERP | Vozila, kvarovi, ugovori, menice, predmeti nabavke, ocene | Da |
| **Preuzeti (snimak)** | Spoljni sistem | `LedgerEntry`, `EufItemSnapshot`, `GoodsSnapshot`, `SickLeave`, `AnnualLeaveAllowance`, `MobileUsage` | Ne — prepisuje ih sledeća sinhronizacija |
| **Čitani u letu** | Spoljni sistem | `dbo.fleet_tro_svi`, `dbo.dodela_baketa`, prolasci radnika | Ne — aplikacija ih samo čita |

---

### 2.5. Ponavljajući obrasci

Sistem koristi nekoliko obrazaca dosledno. Kada ih prepoznaš, ostatak koda je predvidiv.

#### Obrazac 1 — „Draft → Final“ [P]

Podatak iz spoljnog izvora ne može odmah da se poveže sa vozilom, pa se prvo upisuje u
nedovršenu tabelu, korisnik ga dopuni, a zatim se prebacuje u konačnu.

```
 Spoljni izvor ──► Draft tabela ──► ekran „nedovršeno“ ──► Final tabela
                   (bez vozila)      (korisnik bira)        (sa vozilom)
```

| Draft | Final | Ekran | Funkcija prebacivanja |
|---|---|---|---|
| `DraftInsurance` | `Insurance` | `/insurance/drafts/` | `fleet/sync/external.py: migrate_draft_to_insurance_single` |
| `DraftServiceTransaction` | `ServiceTransaction` | `/servisi/nedovrseno/` | `fleet/views/services.py` |

Srodni ekrani „nedovršeno“ bez zasebne draft tabele: `policy_fixing_list`,
`requisition_fixing_list` — tamo se dopunjuje isti zapis.

#### Obrazac 2 — „Snimak izvora“ (snapshot) [P]

Spoljni skup se čita u celini i upisuje u lokalnu tabelu po **stabilnom ključu izvora**,
nikada po iznosu ili opisu.

| Model | Stabilni ključ | Izvor |
|---|---|---|
| `LedgerEntry` | firma, godina, vrsta naloga, broj naloga, stavka | `PUTGEO-SERVER.bazaims.nalog_z` |
| `EufItemSnapshot` | `source_key` | `dbo.nbv_EUF_stavke` |
| `GoodsSnapshot` | `source_key` | `dbo.nbv_roba` |
| `ReceivablePosting` | izvor, firma, godina, vrsta, broj, stavka | `dbo` pogledi naplate |
| `AnnualLeaveAllowance` | firma, godina, šifra zaposlenog | kadrovska baza |

Pravila koja svi snimci poštuju:

- Nestao red se označava **neaktivnim** (`active=False`), ne briše se. [P]
- Ponovo pojavljen red vraća se pod **istim lokalnim ID-em**. [P]
- Prazan izvor ne može automatski obrisati postojeće podatke. [P]
- Pre objave se porede **kontrolni zbirovi** sa nezavisnim upitom nad izvorom;
  neslaganje zaustavlja sinhronizaciju. [P] (`finansije/services/source.py: totals_for`)

#### Obrazac 3 — „Objavljeni snimak stanja“ [P]

U Potraživanjima postoji dodatni korak: sirova knjiženja se prvo obrade u **pozicije**,
pa se snimak objavi. Aktivno stanje je uvek jedan **objavljeni** snimak.

```
ReceivablePosting ──► BalanceSnapshot (draft) ──► validated ──► published
                            │                                       │
                            └──► ReceivablePosition                 ▼
                                                            CollectionState.current_snapshot
```

`CollectionState` ne dozvoljava da aktivno stanje bude snimak koji nije objavljen. [P]

#### Obrazac 4 — Zaključavanje pozadinskih poslova [P]

```python
_run_with_singleton_lock(task_name, lock_ttl_seconds, fn)
```

Redis ključ `ims_erp:task-lock:<task>`. Ako posao već radi, novi se **preskače**
(vraća `SKIP:`), a `TaskHistory` to beleži kao status „Preskočen“.

Trajanje zaključavanja: 4 h za Selenium, 90 min za sinhronizacije, 60 min za lakše poslove.

**Fail-open:** ako Redis nije dostupan, posao se **ipak izvršava**, bez zaštite. [P]

Finansije koriste jači mehanizam — **SQL Server `sp_getapplock`** vezan za istu sesiju
koja pokreće proceduru, pa zaštita važi i za ručno i za Celery pokretanje. [P]

#### Obrazac 5 — Istorija izvršavanja [P]

Svaki Celery zadatak automatski upisuje `TaskHistory` preko signala u `ims_erp/celery.py`
(`task_prerun`, `task_postrun`, `task_failure`). Finansije dodatno imaju `SyncRun` i
`NalogZRefreshRun`, a Potraživanja `CollectionSyncRun` i `CollectionSyncStep`.

#### Obrazac 6 — DataTables preko AJAX-a [P]

Veće liste se ne renderuju u šablonu. Stranica učita okvir, pa zasebna ruta `.../data/`
vrati JSON. Zajednička pomoć: `finansije/services/datatables.py`, `fleet/views/datatables.py`.
Autorizacija i filteri se **ponovo proveravaju pri svakom AJAX zahtevu**. [P]

#### Obrazac 7 — Brisanje fajlova posle potvrde transakcije [P]

Modeli sa fajlovima (`Contract`, `Offer`, `BusinessRequest`, `VehicleTenderDocument`,
`ContractDocument`) brišu staru datoteku tek u `transaction.on_commit`, da neuspela
transakcija ne obriše fajl.

---

### 2.6. Kontrola pristupa

#### 2.6.1. Model [P]

```
CustomUser ──M2M──► Role ──RolePermission──► PermissionCode
                     │                            │
                 is_active                 code = IME URL RUTE
```

Provera (`core/mixins.py`):

```python
user.roles.filter(permissions__code=permission_code, is_active=True).exists()
```

gde je `permission_code` podrazumevano `request.resolver_match.view_name`.
`is_superuser` prolazi uvek.

Tri načina primene:

| Način | Upotreba |
|---|---|
| `RolePermissionRequiredMixin` | Klasni view-ovi |
| `role_permission_required()` | Funkcijski view-ovi |
| `RoleRequiredMixin` | Kada se traži **uloga**, a ne dozvola (podrazumevano `uprava`) |

#### 2.6.2. Automatsko generisanje dozvola [P]

`core/permissions.py: sync_permission_codes()` obilazi `urlpatterns` svih aplikacija,
skuplja imena ruta i stvara `PermissionCode` za svako.

**Posledice:**

- Nova ruta = nova dozvola, ali tek posle `manage.py sync_permission_codes`
  ili noćnog zadatka u 01:00.
- Uloga **Uprava** pri svakoj sinhronizaciji dobija **sve** dozvole.
- Uloge `nabavka`, `menice`, `blagajna`, `mobilni`, `pregled-naplate`, `zahtev` se
  **usklađuju** — višak dozvola se briše. Uloge `pravna`, `sekretarijat`, `zaposleni`
  se samo dopunjuju.
- Postoje i ručno dodate dozvole van ruta: `finansije:view_all`, `hr:evaluation_view_all`.

#### 2.6.3. Drugi sloj — ograničenje po centrima [P]

| Polje | Tip | Napomena |
|---|---|---|
| `CustomUser.allowed_centers` | M2M ka `OrganizationalUnit` | |
| `CustomUser.allowed_center_codes` | tekst, šifre odvojene zarezima | |

**Oba mehanizma postoje paralelno.** [P] Koji je merodavan u kom modulu nije potvrđeno —
otvoreno pitanje **Q5** u inventaru. [N]

U Finansijama prazna lista dozvoljenih centara **nije** globalan pristup. [P]

#### 2.6.4. Predefinisane uloge [P]

| Slug | Naziv | Obuhvat |
|---|---|---|
| `uprava` | Uprava | Sve dozvole (automatski) |
| `nabavka` | Nabavka | Ceo modul Nabavka |
| `menice` | Menice | Ceo modul Menice |
| `blagajna` | Blagajna | Ceo modul Isplate |
| `pravna` | Pravna služba | Pravna služba + modul Ugovori |
| `mobilni` | Mobilni | Ceo modul Mobilni |
| `finansije` | Finansijska analitika | `dashboard`, `ledger`, `export` |
| `pregled-naplate` | Pregled naplate | Pregledi i izvozi Naplate, bez izmena |
| `zahtev` | Zahtev | Kreiranje zahteva nabavke i štampa |
| `sekretarijat` | Sekretarijat | Zaposleni i putni nalozi |
| `zaposleni` | Zaposleni | Svoj profil i zaduženje vozila |

#### 2.6.5. Evidencija rada [P]

`core/middleware.py: ActivityLogMiddleware` posle svakog odgovora poziva
`core/activity.py: log_request_activity` i upisuje `ActivityLog`
(tabela `fleet_activity_log`): korisnik, akcija, aplikacija, ruta, metod, putanja,
status, model, ID zapisa, izmene (JSON), IP adresa, korisnički agent.

Beleže se i prijava, odjava i **neuspešna prijava**. Ekran: `/administracija/activity-log/`.

---

### 2.7. Pozadinski poslovi

#### 2.7.1. Redovi [P]

| Red | Šta ide u njega | Zašto odvojeno |
|---|---|---|
| `selenium` | NIS, OMV putnička, OMV teretna | Traju dugo i zavise od pregledača |
| `sync` | Sve ostale sinhronizacije | Kratke, ne smeju čekati Selenium |
| `default` | Podrazumevani | |

#### 2.7.2. Ozbiljno ograničenje [P]

Produkcioni worker se pokreće sa `-P solo` (`nssm.bat`):

```
celery -A ims_erp worker -l info -P solo -Q default,sync,selenium
```

`-P solo` znači **jedan zadatak u jednom trenutku**, bez obzira na
`CELERY_WORKER_CONCURRENCY = 2` u postavkama. Razdvajanje redova zato **ne daje
paralelnost** dok radi jedan worker — Selenium posao koji traje sat vremena blokira
i `sync` zadatke.

> **Napomena za održavanje [Z]:** paralelnost bi zahtevala drugi worker proces
> vezan samo za red `sync`. To je odluka za održavanje, ne izmena koda.

#### 2.7.3. Postavke koje smanjuju opterećenje [P]

| Postavka | Vrednost | Svrha |
|---|---|---|
| `CELERY_TASK_IGNORE_RESULT` | `1` | Rezultati se ne čuvaju u Redisu |
| `CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED` | `True` | Greške se ipak čuvaju |
| `CELERY_WORKER_MAX_TASKS_PER_CHILD` | 100 | Obnavljanje procesa, protiv curenja memorije |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | 1 | Bez gomilanja zadataka |
| `CELERY_ENABLE_UTC` | `False`, `CELERY_TIMEZONE = CET` | Lokalno vreme u rasporedu |

---

### 2.8. Datoteke i mediji

| Sadržaj | Putanja |
|---|---|
| Slike vozila | `media/vehicles/photos/%Y/%m/` |
| Saobraćajne dozvole (PDF i slike) | `media/traffic_cards/`, `media/traffic_cards/images/%Y/%m/` |
| Tenderska dokumentacija vozila | `media/vehicle_tender_documents/%Y/%m/` |
| Ugovori i prilozi | `media/ugovori/files/`, `dokumenti/`, `ponude/`, `zahtevi/` |

Ograničenja otpremanja [P]: `MAX_CONTRACT_UPLOAD_SIZE` 50 MB,
`DATA_UPLOAD_MAX_MEMORY_SIZE` 60 MB.

`MEDIA_URL` se opslužuje preko Djanga **samo kad je `DEBUG=True`**. [P]
Pošto je `DEBUG=True` i u produkciji, mediji se trenutno opslužuju preko Djanga. [Z]

---

### 2.9. Postavke po okruženjima

| Fajl | Baza | `ALLOWED_HOSTS` |
|---|---|---|
| `base.py` | — (zajedničko; `DEBUG = True`, `SECRET_KEY` upisan) | — |
| `development.py` | **Pravi SQL Server** `IMS_ERP` | `127.0.0.1` |
| `production.py` | Isti SQL Server + nekorišćeni `local` sqlite | `ims-flota`, `ims.portal`, `192.168.6.7`, `127.0.0.1`, `localhost` |
| `testing.py` | SQLite **u memoriji** | `testserver`, `localhost`, `127.0.0.1` |

`testing.py` isključuje SQL Server, Redis i e-poštu; `CELERY_TASK_ALWAYS_EAGER = True`
i brz MD5 heš lozinki. [P]

**`manage.py` podrazumevano koristi `development`** [P] — dakle pravu bazu.
`ims_erp/celery.py` podrazumevano koristi `production`. [P]

> Bezbednosni nalazi u vezi sa ovim postavkama: [10. Poznati problemi](#10-poznati-problemi-i-ograničenja).

---

### 2.10. Testovi

550 testova u 31 fajlu. [P] Pokreću se na SQLite bazi u memoriji:

```powershell
.\.venv\Scripts\python.exe manage.py test --settings=ims_erp.settings.testing
```

Raspored po modulima:

| Modul | Testova | Najviše pokriveno |
|---|---|---|
| `fleet` | 153 | Presek flote, kilometraža, održavanje, unos vozila, izveštaji |
| `finansije` | 121 | Tok gotovine, kartica posla, zajednički troškovi, nalog Z |
| `hr` | 97 | Odmori, bolovanja, ocenjivanje, šifarnik radne liste |
| `potrazivanja` | 59 | Sinhronizacija, operacije, integracija, brzina čitanja |
| `mobilni` | 40 | Obustave, uvoz |
| `core` | 28 | Dozvole, evidencija rada |
| `nabavka` | 19 | Povezivanje faktura i šifara posla |
| `isplate` | 20 | Virman |
| ostali | 13 | |

---

### 2.11. Sistemi izvan aplikacije

```
┌──────────────┐  Selenium   ┌───────────────────────┐
│ cards.nis.rs │◄────────────┤                       │
└──────────────┘             │                       │
┌──────────────┐  Selenium   │                       │
│ fleet.omv.com│◄────────────┤                       │
└──────────────┘             │      IMS ERP          │
┌──────────────┐  HTTP/HTML  │                       │
│ NBS PnWebApp │◄────────────┤   (Django + Celery)   │
└──────────────┘             │                       │
┌──────────────┐  HTTP/JSON  │                       │
│ APR OpenAPI  │◄────────────┤                       │
└──────────────┘             │                       │
┌──────────────┐  Excel      │                       │
│ RFZO, MTS    │────────────►│                       │
└──────────────┘             │                       │
                             │                       │  datoteka
                             │                       ├──────────► Banka (virman)
                             └───────────┬───────────┘
                                         │ SQL
                             ┌───────────▼───────────┐
                             │  PUTGEO-SERVER        │ knjigovodstvo, zarade
                             │  INFORMATIKA23        │ kontrola pristupa
                             │  SERFIN               │ kadrovska
                             └───────────────────────┘
```

Detaljno: [7. Integracije](#7-integracije).

---

### 2.12. Šta arhitektura dobro rešava, a šta ne

#### Dobro [Z]

- **Razdvajanje prikaza i obračuna** — formule su na jednom mestu i mogu se testirati.
- **Stabilni ključevi izvora** — ponovljena sinhronizacija ne stvara duplikate.
- **Kontrolni zbirovi pre objave** — nepotpuno čitanje izvora se otkriva, a ne objavljuje.
- **Istorija svega** — `TaskHistory`, `SyncRun`, `ActivityLog`, `ProcurementStatusLog`,
  `CollectionAudit` daju sledljivost.
- **Dozvole vezane za rute** — nemoguće je zaboraviti dozvolu za novi ekran; najgore što
  se desi je da je vidi samo Uprava.

#### Slabije [Z]

- **Jedan worker sa `-P solo`** poništava korist od razdvojenih redova.
- **Zavisnost od tri udaljena servera** bez rezervnog ponašanja.
- **Selenium kao integracija** je krhak — promena stranice dobavljača zaustavlja preuzimanje.
- **Nasleđeni pogledi van kontrole verzija** — promena pogleda menja rezultat bez izmene koda.
- **Dva paralelna mehanizma za centre** otežavaju rasuđivanje o pristupu.
- **`DEBUG=True` u produkciji** i tajne u repozitorijumu.

---

### 2.13. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Šta radi pojedini modul? | [3. Moduli](#3-moduli--sadržaj-i-veze) |
| Koje tabele i kolone postoje? | [4. Baza podataka](#4-baza-podataka) |
| Kako se računa određeni iznos? | [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj) |
| Kako se sistem pokreće i održava? | [8. Instalacija](#8-instalacija-i-pokretanje), [9. Održavanje](#9-održavanje) |

---

## 3. Moduli — sadržaj i veze

> **Za koga je ovo poglavlje:** poslovni korisnici i programeri.
> Ovde je pregled svih modula i **kako su povezani**. Detaljan opis svakog modula je u
> zasebnom dokumentu.
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 3.0.1. Sadržaj

| # | Modul | Adresa | Dokument |
|---|---|---|---|
| 1 | **Vozni park (Flota)** | `/` | [03-01-flota.md](#31-vozni-park-flota) |
| 2 | **Kadrovi** | `/hr/` | [03-02-kadrovi.md](#32-kadrovi) |
| 3 | **Finansijska analitika** | `/finansije/` | [03-03-finansije.md](#33-finansijska-analitika) |
| 4 | **Nabavka** | `/nabavka/` | [03-04-nabavka.md](#34-nabavka) |
| 5 | **Potraživanja** | `/potrazivanja/` | [03-05-potrazivanja.md](#35-potraživanja) |
| 6 | **Ugovori i partneri** | `/ugovori/` | [03-06-ugovori.md](#36-ugovori-i-partneri) |
| 7 | **Menice** | `/menice/` | [03-07-menice.md](#37-menice) |
| 8 | **Mobilna telefonija** | `/mobilni/` | [03-08-mobilni.md](#38-mobilna-telefonija) |
| 9 | **Isplate** | `/isplate/` | [03-09-isplate.md](#39-isplate) |
| 10 | **Administracija** | `/administracija/` | [03-10-administracija.md](#310-administracija) |

> Modul **Naplata** (`/naplata/`) je nasleđen i **nije obuhvaćen dokumentacijom**.
> Zamenjuju ga Potraživanja. Vidi [10. Poznati problemi, P-18](#10-poznati-problemi-i-ograničenja).

---

### 3.0.2. Šta koji modul radi — u jednoj rečenici

| Modul | Poslovna namena |
|---|---|
| **Flota** | Vodi vozila kroz ceo životni ciklus: dokumenta, raspolaganje, gorivo, održavanje, garaža i putni nalozi |
| **Kadrovi** | Vodi zaposlene, njihove radne liste, odsustva i mesečnu ocenu rada |
| **Finansijska analitika** | Pokazuje rezultat poslovanja po šifri posla i centru, i tok gotovine |
| **Nabavka** | Vodi zahtev za nabavku od podnošenja do fakture, uz plan javnih nabavki |
| **Potraživanja** | Prati koliko kupci duguju, po starosti duga, i vodi postupak naplate |
| **Ugovori** | Vodi partnere, zahteve, ponude, ugovore, anekse i garancije |
| **Menice** | Vodi ulazne i izlazne menice, uz preuzimanje iz registra NBS |
| **Mobilna telefonija** | Vodi službene brojeve i računa obustavu koja ide u zaradu |
| **Isplate** | Pravi datoteku virmana za isplatu akontacija preko banke |
| **Administracija** | Vodi korisnike, uloge, dozvole, evidenciju rada i istoriju pozadinskih poslova |

---

### 3.0.3. Mapa veza između modula

Ovo je **najvažniji deo poglavlja** — pokazuje šta se dešava kada se nešto promeni.

```
                        ┌──────────────────────┐
                        │   ADMINISTRACIJA     │
                        │  korisnici, uloge,   │
                        │  dozvole, OJ/šifre   │
                        └──────────┬───────────┘
                                   │ šifra posla (OJ) i centar
        ┌──────────────┬───────────┼───────────┬──────────────┐
        ▼              ▼           ▼           ▼              ▼
   ┌─────────┐   ┌──────────┐ ┌─────────┐ ┌─────────┐  ┌────────────┐
   │  FLOTA  │   │ KADROVI  │ │NABAVKA  │ │FINANSIJE│  │POTRAŽIVANJA│
   └────┬────┘   └────┬─────┘ └────┬────┘ └────┬────┘  └─────┬──────┘
        │             │            │           │             │
        │  zaposleni  │            │           │             │
        │◄────────────┤            │           │             │
        │             │            │           │             │
        │  vozilo, kvar, trebovanje│           │             │
        ├────────────────────────►│            │             │
        │             │            │           │             │
        │  polise iz faktura       │           │             │
        │◄────────────────────────┤            │             │
        │             │            │           │             │
        │  vozila, zaduženja, putni nalozi     │             │
        ├─────────────────────────────────────►│             │
        │             │            │           │             │
        │             │            │   saldo kupaca          │
        │             │            │           │◄────────────┤
        │             │            │           │             │
   ┌────┴────┐        │       ┌────┴────┐      │        ┌────┴─────┐
   │ ISPLATE │        │       │ UGOVORI │◄─────┘        │  PRAVNI  │
   │ virmani │        │       │ partneri│  partneri     │ POSTUPCI │
   └─────────┘        │       └────┬────┘               └──────────┘
                      │            │ menice, garancije
                 ┌────┴─────┐  ┌───┴────┐
                 │ MOBILNI  │  │ MENICE │
                 │ obustave │  └────────┘
                 └────┬─────┘
                      │
                      ▼
              OBRAČUN ZARADA (van sistema)
```

#### Veze — tabelarno [P]

| Iz modula | U modul | Šta se prenosi | Kako |
|---|---|---|---|
| **Administracija** | Svi | Organizaciona jedinica i centar (`OrganizationalUnit`) | Veza u bazi |
| **Kadrovi** | Flota | Zaposleni — vozač, podnosilac putnog naloga | Veza `fleet_employee` |
| **Kadrovi** | Mobilni | Zaposleni uz broj telefona | Veza |
| **Kadrovi** | Isplate | Partija i opština boravka za virman | Veza preko putnog naloga |
| **Kadrovi** | Ugovori | Ocenjivači po organizacionoj jedinici | Veza |
| **Flota** | Nabavka | Kvar, vozilo, trebovanje → predmet nabavke | Veza `garage_order`, `vehicle` |
| **Flota** | Finansije | Vozila i zaduženja na šifri posla | Upit po istorijskim dodelama |
| **Flota** | Isplate | Putni nalozi sa akontacijom | Veza |
| **Nabavka** | Flota | EUF fakture osiguranja → polise | Sinhronizacija polisa |
| **Nabavka** | Flota | Fakture i UF stavke → dokazi o održavanju vozila | Upit |
| **Nabavka** | Ugovori | Osnovni i kupovni ugovor uz predmet | Veza `contract` |
| **Ugovori** | Nabavka | Partner kao dobavljač | Veza `supplier` |
| **Ugovori** | Menice | Veza ugovora i menice | Veza `ContractMenicaLink` |
| **Ugovori** | Flota | Ugovor o lizingu i o finansiranju | Veza `Lease.contract`, `VehicleHolding.financing_contract` |
| **Ugovori** | Mobilni | Ugovor uz paket | Veza `MobilePackage.contract` |
| **Ugovori** | Potraživanja | Partner uz finansijski identitet | Veza `FinancePartnerIdentity.partner` |
| **Potraživanja** | Finansije | Saldo kupaca po šifri posla | `job_balances()` |
| **Mobilni** | *(izvan sistema)* | Obustava po zaposlenom | CSV izvoz |
| **Kadrovi** | *(izvan sistema)* | Ocena i radna lista | Štampa |
| **Isplate** | *(izvan sistema)* | Virman | Datoteka za banku |

---

### 3.0.4. Ko koristi koji modul

> **[Z] Zaključeno iz uloga u kodu.** Konačnu potvrdu daje naručilac — pitanje **Q2**.

| Uloga (slug) | Flota | Kadrovi | Finansije | Nabavka | Potraž. | Ugovori | Menice | Mobilni | Isplate | Admin |
|---|---|---|---|---|---|---|---|---|---|---|
| `uprava` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `nabavka` | | | | ✔ | | | | | | |
| `menice` | | | | | | | ✔ | | | |
| `blagajna` | | | | | | | | | ✔ | |
| `pravna` | | | | | ✔ | ✔ | | | | |
| `mobilni` | | | | | | | | ✔ | | |
| `finansije` | | | ✔ | | | | | | | |
| `zahtev` | | | | ✔ (samo zahtevi) | | | | | | |
| `sekretarijat` | ✔ (putni nalozi) | ✔ (zaposleni) | | | | | | | | |
| `zaposleni` | ✔ (zaduženje vozila) | ✔ (svoj profil) | | | | | | | | |
| `pregled-naplate` | | | | | ✔ (pregled) | | | | | |

---

### 3.0.5. Broj ekrana i tabela po modulu [P]

| Modul | HTML šablona | Django tabela | Obračuna |
|---|---|---|---|
| Flota | 115 | 23 | 24 (+11 izveštaja) |
| Naplata *(nasleđeno)* | 27 | 3 (+12 pogleda) | — |
| Kadrovi | 25 | 16 | 9 |
| Nabavka | 24 | 13 | 6 |
| Ugovori | 20 | 8 | 2 |
| Finansije | 16 | 4 | 18 |
| Mobilni | 16 | 6 | 4 |
| Potraživanja | 10 | 22 | 6 |
| Menice | 6 | 2 | 2 |
| Isplate | 2 | **0** | 3 |
| Zajednički šabloni | 19 | 7 (`core`) | — |

---

### 3.0.6. Gde nastaje, a gde se samo čita

Ključ za razumevanje sistema: **koji modul je vlasnik kog podatka**. [Z]

| Podatak | Vlasnik | Ko ga samo čita |
|---|---|---|
| Vozilo, saobraćajna, kvar, putni nalog | **Flota** | Nabavka, Finansije, Isplate |
| Zaposleni | **Kadrovska baza** *(spolja)* | Flota, Mobilni, Ugovori, Isplate |
| Organizaciona jedinica i centar | **Nasleđeni ERP** *(spolja)* | Svi |
| Knjiženja | **Knjigovodstvo** *(spolja)* | Finansije, Potraživanja, Flota |
| Partner | **Ugovori** *(uz preuzimanje iz ERP-a)* | Nabavka, Potraživanja, Menice |
| Predmet nabavke, narudžbenica | **Nabavka** | Flota |
| Ugovor, aneks, garancija | **Ugovori** | Nabavka, Flota, Mobilni |
| Menica | **NBS registar + Menice** | Ugovori |
| Paket, dodela broja, potrošnja | **Operater** *(spolja)* | Mobilni |
| Ocena zaposlenog, radna lista | **Kadrovi** | — |
| Saldo kupaca | **Potraživanja** | Finansije |

> **[P] Pravilo:** podatak koji stiže spolja (sinhronizacijom ili uvozom) **ne treba
> menjati u aplikaciji** — sledeća sinhronizacija ga prepisuje.
> Izuzetak su izričita polja za dopunu, kao što su „Kategorija popravke“ i „Napomena“
> na knjiženjima servisa.

---

### 3.0.7. Zajednička pravila svih modula

#### Pristup [P]

Svaki ekran ima dozvolu koja se zove **isto kao ruta**. Vidi
[2.6. Kontrola pristupa](#26-kontrola-pristupa).

#### Evidencija rada [P]

Svaki zahtev se beleži u `fleet_activity_log` — ko, kada, koji ekran, koji zapis.
Ekran: `/administracija/activity-log/`.

#### Prebacivanje između modula [P]

Bočni meni se bira preko `switch-app`, a izbor se pamti u sesiji.
Postoji 12 menija, među njima i **`pravna`** i **`kadrovi`**, koji nisu zasebne
Django aplikacije.

#### Izvoz [P]

| Vrsta | Moduli |
|---|---|
| Excel (`.xlsx`) | Flota, Nabavka, Ugovori, Mobilni, Potraživanja, Finansije |
| CSV | Flota, Mobilni |
| Štampa (HTML) | Flota, Kadrovi, Nabavka, Ugovori, Potraživanja |
| Datoteka za banku | Isplate |

Pri izvozu u Excel tekst iz spoljnih izvora koji počinje sa `=`, `+`, `-` ili `@`
dobija apostrof ispred, da ga Excel **ne protumači kao formulu**. [P]

---

### 3.0.8. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako teče posao od početka do kraja? | [5. Poslovni procesi](#5-poslovni-procesi) |
| Kako se računa neki iznos? | [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj) |
| Koje tabele koristi modul? | [4. Baza podataka](#4-baza-podataka) |
| Odakle dolaze podaci spolja? | [7. Integracije](#7-integracije) |

---

## 3.1. Vozni park (Flota)

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Flota** / „Vozni park“ |
| Tehnički naziv | Django aplikacija `fleet` |
| Adresa | `/` — **korenska aplikacija sistema** |
| Bočni meni | `sidebar_fleet.html` |

> **[P]** `fleet` je i korenska aplikacija: njen `urls.py` drži prijavu, odjavu,
> kontrolnu tablu, korisnike, evidenciju rada i istoriju pozadinskih poslova.

---

### 2. Poslovna namena

Vodi **ceo životni ciklus vozila** — od nabavke do otpisa:

1. **Ko je vlasnik ili po kom ugovoru se vozilo koristi** i u kom periodu.
2. **Kojoj organizacionoj jedinici vozilo pripada** u kom periodu.
3. **Koliko vozilo košta** — evidentirani troškovi perioda; kapital i budući troškovi u zasebnoj ekonomskoj proceni.
4. **Troškovi i opravdanost vozila** — poslovna namena × istorija raspolaganja, obrazloženi kontrolni kriterijumi i poređenje budućih alternativa; [metodologija IMS-FLOTA-2.0](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa).
5. **Šta traži hitnu radnju** — istekla registracija, polisa bez pokrića, kvar.
6. **Ko je vozilo zadužio i koliko je prešao** — putni nalozi vozila.
7. **Službena putovanja zaposlenih** — putni nalozi sa akontacijom.

---

### 3. Korisnici modula

| Korisnik | Šta radi | Uloga |
|---|---|---|
| **Služba voznog parka** | Vodi evidenciju, prati troškove, priprema izveštaje | `uprava` ili posebne dozvole |
| **Garaža** | Prijavljuje kvarove, vodi radne naloge i trebovanja | `uprava`, `zahtev` |
| **Sekretarijat** | Izdaje i štampa putne naloge za službena putovanja | `sekretarijat` |
| **Zaposleni** | Otvara zaduženje vozila i štampa obračun | `zaposleni` |
| **Rukovodioci centara** | Prate vozila i troškove svog centra | uz dozvoljene centre |
| **Uprava** | Izveštaji za pripremu osiguranja i analizu isplativosti | `uprava` |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Vozila** | Tehnički podaci, slike, čarobnjak za unos novog vozila, otpis i vraćanje u upotrebu |
| **Dokumenta** | Saobraćajne dozvole sa istorijom tablica, tenderska dokumentacija, izvoz u ZIP |
| **Raspolaganje** | Osnov raspolaganja (vlasništvo ili ugovor), lizing i najam, kamate |
| **Šifre posla** | Istorijske dodele vozila organizacionoj jedinici |
| **Osiguranje** | Polise, knjiženja osiguranja, dopuna nedovršenih zapisa, pregled isteka |
| **Gorivo** | Transakcije NIS i OMV, fakture goriva, prosečna potrošnja, izveštaji po šifri posla |
| **Održavanje** | Servisi, knjiženja servisa, trebovanja, tipovi servisa, konta vozila |
| **Garaža** | Prijava kvara, radni nalog, trebovanje materijala, zahtev za nabavku (GZN) |
| **Putni nalozi vozila** | Zaduženje vozila sa kilometražom i obračunom goriva |
| **Putni nalozi zaposlenih** | Službena putovanja sa akontacijom, dnevnicom i štampom |
| **Analitika** | Zajednički obračun za flotu, centar i vozilo; namena × raspolaganje, dokumentovani kriterijumi, raspodela na poslove i sačuvane ekonomske procene |
| **Izveštaji** | 20 izveštaja, uključujući 4 za upravu i 11 nad nasleđenim pogledima |
| **Administracija** | Korisnici, uloge, evidencija rada, istorija pozadinskih poslova |

---

### 5. Glavni korisnički ekrani

#### Vozila i dokumenta

| Ekran | Adresa | Napomena |
|---|---|---|
| Spisak vozila | `/vozila/` | DataTables preko AJAX-a |
| **Unos novog vozila** | `/vozila/novo/` | **Čarobnjak u koracima** |
| Detalj vozila | `/vozila/<id>/` | Kartice: pregled, dokumenti, raspolaganje, korišćenje, kilometraža, analitika |
| Osnov raspolaganja | `/vozila/<id>/osnov/novo/` | Vlasništvo ili ugovor |
| Tenderska dokumentacija | `/vozila/<id>/tenderska-dokumentacija/` | Preuzimanje ZIP datoteke |
| Saobraćajne dozvole | `/saobracajne-dozvole/` | Istorija tablica |
| Šifre poslova (dodele) | `/sifre-poslova/` | Istorijske dodele |

Detalj vozila prikazuje četiri sažete kartice trenutnog stanja. Na užim ekranima
raspoređuju se u dve ili jednu kolonu; kartice podataka, raspolaganja i dokumenata
takođe prelaze u jednu kolonu. Izbor odeljaka ostaje u jednom horizontalno
pomerljivom redu. Oznake statusa imaju odvojene stilove od grupa kartica.

#### Ugovori i osiguranje

| Ekran | Adresa |
|---|---|
| Lizing i najam | `/zakupi/` |
| Polise | `/polise/` |
| **Polise za dopunu** | `/polise/nedovrseno/` |
| **Polise pred istekom** | `/polise/istek/` |
| Knjiženja osiguranja | `/insurance/` |
| Knjiženja osiguranja za dopunu | `/insurance/drafts/` |

#### Gorivo

| Ekran | Adresa |
|---|---|
| Transakcije goriva | `/fuel-transactions/` |
| Fakture goriva (detalj računa) | `/fuel-transactions/detail/` |
| Potrošnja goriva | `/potrosnja-goriva/` |

#### Održavanje i garaža

| Ekran | Adresa |
|---|---|
| Knjiženja servisa | `/service-transactions/` |
| Knjiženja servisa za dopunu | `/servisi/nedovrseno/` |
| Trebovanja | `/requisitions/` |
| Trebovanja za dopunu | `/requisitions/nedovrseno/` |
| **Prijave kvarova** | `/garaza/kvarovi/` |
| Kvarovi u IMS garaži / van IMS-a | `/garaza/kvarovi/ims/`, `/garaza/kvarovi/van-ims/` |
| Štampa prijave kvara | `/garaza/kvarovi/<id>/prijava/` |
| **Radni nalog** | `/garaza/kvarovi/<id>/radni-nalog/` |
| **Trebovanje uz kvar** | `/garaza/kvarovi/<id>/trebovanje/` |

#### Putni nalozi

| Ekran | Adresa |
|---|---|
| **Zaduženja vozila** | `/garaza/putni-nalozi-vozila/` |
| Obračun goriva na zaduženju | `/garaza/putni-nalozi-vozila/<id>/obracun/` |
| Zatvaranje zaduženja | `/garaza/putni-nalozi-vozila/<id>/zatvori/` |
| **Putni nalozi zaposlenih** | `/putni-nalozi/` |
| Štampa putnog naloga | `/putni-nalozi/<id>/print/` |
| Prilog za inostranstvo | `/putni-nalozi/<id>/prilog-inostranstvo/` |

#### Pregledi i izveštaji

| Ekran | Adresa |
|---|---|
| **Kontrolna tabla flote** | `/` |
| **Analitika flote** | `/analitika/` |
| Statistika centra | `/center_statistics/<centar>/` |
| Spisak izveštaja | `/izvestaji/` |
| Izveštaji za upravu | `/izvestaji/osiguranje/kasko/`, `/izvestaji/osiguranje/ims/`, `/izvestaji/gorivo-ims/`, `/izvestaji/delovi-dobavljaca/` |

---

### 6. Podaci koje korisnik unosi

#### Kako izgledaju forme [P]

Od 19.09.2026. sve forme Flote koje idu kroz zajednički šablon poštuju tri pravila:

| Pravilo | Kako |
|---|---|
| **Obavezno polje se vidi** | Crvena zvezdica uz naziv, uz legendu na vrhu. Ranije je to imao **samo čarobnjak za unos vozila** — na ostalih 26 ekrana obaveznost se saznavala tek posle slanja |
| **Polja su grupisana u celine** | Forma navede `fieldsets`; polje koje nije razvrstano ide u celinu **„Ostalo“**, da izmena modela ne bi tiho sakrila novo polje |
| **Objašnjenje stoji uz polje** | `help_text`, naročito kod iznosa (mesečni ili ukupni), datuma (da li je uključiv) i knjigovodstvenih skraćenica |

Grupisanje se dodaje nasleđivanjem `FieldsetMixin` iz
[`fleet/forms/layout.py`](../fleet/forms/layout.py):

```python
class LeaseForm(FieldsetMixin, forms.ModelForm):
    fieldsets = (
        ('Vozilo i ugovor', 'Na koje vozilo se ugovor odnosi.', ('vehicle', 'contract_number')),
        ('Trajanje', 'Oba datuma su uključena.', ('start_date', 'end_date')),
    )
```

Sređeno je **jedanaest formi** sa ukupno 147 polja: vozilo (26), servisna stavka i njena
nedovršena verzija (2×19), trebovanje (18), polisa (15), ugovor lizinga, saobraćajna
dozvola, naknada osiguranja i njena nedovršena verzija (4×11), gorivo (9), raspolaganje (8)
i tenderski dokument (7).

> **Ispravljena opasna nedoslednost [P]:** polje `nije_garaza` je **negacija** — tačno
> znači da servis **nije** rađen u garaži IMS-a. Nedovršena servisna stavka je za isto polje
> imala naziv *„Da li ovaj servis pripada garaži?“*, dakle **suprotnog značenja**. Sve tri
> forme sada nose isti naziv: **„Servis van garaže IMS-a“**.

> **Vraćeno izgubljeno objašnjenje [P]:** `KvarForm` je redeklaracijom polja brisao
> `help_text` koji postoji na modelu.

---



| Podatak | Ekran | Ko unosi |
|---|---|---|
| Tehnički podaci vozila | Unos vozila | Služba voznog parka |
| **Maksimalna dozvoljena masa** | Unos vozila | Tehnička karakteristika; u novoj analitici ne određuje kriterijum opravdanosti |
| Saobraćajna dozvola i tablice | Saobraćajne dozvole | Služba voznog parka |
| Osnov raspolaganja i period | Detalj vozila | Služba voznog parka |
| Lizing i najam | Lizing | Služba voznog parka |
| Prijava kvara, kilometraža, opis | Garaža | Garaža |
| Stavke delova uz kvar | Radni nalog | Garaža |
| Zahtev za nabavku (GZN) | Garaža | Garaža |
| **Zaduženje vozila i kilometraža** | Putni nalozi vozila | **Zaposleni** |
| Putni nalog: mesto, zadatak, dani, akontacija | Putni nalozi | Sekretarijat |
| Kategorija popravke i napomena na knjiženjima | Ekrani „za dopunu“ | Služba voznog parka |
| Veza knjiženja sa vozilom | Ekrani „za dopunu“ | Služba voznog parka |
| Tipovi servisa, konta vozila | Šifarnici | Služba voznog parka |

---

### 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada | Tabela |
|---|---|---|---|
| Organizacione jedinice | `dbo.v_organizationalunit` | 01:30 | `fleet_organizationalunit` |
| **Tekuća šifra posla vozila** | `dbo.sif_pos_trenutno` | 01:30 | `fleet_jobcode` |
| Otpisana vozila | `dbo.fleet_otpis` | 01:20 | `fleet_vehicle.otpis` |
| **Knjigovodstvena vrednost** | `dbo.vrednost_vozila` | Ručno | `fleet_vehicle.value` |
| Trebovanja | `dbo.fleet_trebovanja` | 01:45 | `fleet_requisition` |
| Polise osiguranja | EUF fakture Nabavke | 02:00 | `fleet_policy` |
| Knjiženja servisa | `dbo.fleet_servisi` | 03:15 | `fleet_servicetransaction` |
| Knjiženja osiguranja DDOR | `dbo.fleet_potrazivanje_ddor` | 03:35 | `fleet_draftinsurance` |
| **Gorivo NIS** | Portal `cards.nis.rs` (Selenium) | 04:20 | `fleet_transactionnis`, `fleet_fuelconsumption` |
| **Gorivo OMV putnička** | Portal `fleet.omv.com` (Selenium) | 05:10 | `fleet_transactionomv`, `fleet_fuelconsumption` |
| **Gorivo OMV teretna** | Isti portal | 06:10 | isto |
| **Isplaćeno po putnom nalogu** | `dbo.fleet_zatvoren_putni` | 12:30 | `fleet_putninalog.isplaceno` |
| Kamate lizinga | `dbo.lizing_kamate` | Ručno | `fleet_leaseinterest` |
| Zaposleni | `dbo.hr_employee` | 01:10 | `fleet_employee` |

---

### 8. Tabele i kolone

Detaljno: [4.4. Vozni park](#44-vozni-park--fleet).

**23 tabele.** Najvažnije:

| Tabela | Uloga | Ključ |
|---|---|---|
| `fleet_vehicle` | Vozilo | `chassis_number` (broj šasije) |
| `fleet_trafficcard` | Saobraćajna dozvola, istorija tablica | — |
| `fleet_jobcode` | **Istorijska dodela vozila OJ** | `(vehicle, assigned_date)` |
| `fleet_vehicleholding` | Osnov raspolaganja, periodi bez preklapanja | — |
| `fleet_lease`, `fleet_leaseinterest` | Lizing i kamata | `(year, lease)` |
| `fleet_policy` | Polisa osiguranja | `invoice_id` |
| `fleet_insurance`, `fleet_draftinsurance` | Knjiženja osiguranja | `(god, sif_vrs, br_naloga, stavka, knt)` |
| `fleet_transactionomv`, `fleet_transactionnis` | Sirove transakcije goriva | petorke kolona |
| `fleet_fuelconsumption` | Objedinjena potrošnja | `(vehicle, supplier, date, amount, fuel_type)` |
| `fleet_servicetransaction`, `fleet_draftservicetransaction` | Knjiženja servisa | `(datum, duguje, vez_dok, br_naloga)` |
| `fleet_requisition` | Trebovanje | `(sif_pred, god, br_dok, sif_vrsart, stavka)` |
| `fleet_kvar`, `fleet_kvarpart` | Prijava kvara i delovi | `rbz` |
| `fleet_vehicletravelorder` | Zaduženje vozila | `pn_number`, `rbz` |
| `fleet_putninalog` | Službeno putovanje | `order_number` |

> **[P] Veza sa registrom organizacije (faza 2, od 25.09.2026.):** šest tabela —
> `fleet_jobcode`, `fleet_putninalog`, `fleet_vehicletravelorder`, `fleet_procurementrequest`,
> `fleet_fuelconsumption`, `fleet_lease` — imaju opcionu kolonu `org_node_id` (čvor registra).
> Ona se **izvodi** iz postojećeg polja (`organizational_unit` / `job_code`) pri svakom čuvanju
> (`organizacija/signals.py`) i komandom `povezi_flotu`. **Flota je ne čita:** sve rute i obračuni
> i dalje rade preko starih polja, koja ostaju merodavna. Uporedni izveštaj:
> `/organizacija/flota/` (dozvola `organizacija:flota`).

---

### 9. SQL pogledi i upiti

| Objekat | Namena | Status |
|---|---|---|
| `dbo.v_organizationalunit` | Šifarnik OJ | Poznate kolone |
| `dbo.sif_pos_trenutno` | Tekuća šifra posla po tablici | Poznate kolone |
| `dbo.fleet_otpis` | Otpisana osnovna sredstva | Poznate kolone |
| `dbo.vrednost_vozila` | Knjigovodstvena vrednost | Poznate kolone |
| `dbo.fleet_trebovanja` | Trebovanja | **[N]** Sadržaj nije potvrđen |
| `dbo.fleet_servisi` | Knjiženja servisa | **[N]** |
| `dbo.fleet_potrazivanje_ddor` | Knjiženja osiguranja | Poznate kolone |
| `dbo.fleet_zatvoren_putni` | Isplaćeni putni nalozi | **[N]** |
| `dbo.lizing_kamate` | Kamate lizinga | **[N]** |
| **9 izveštajnih pogleda** | `fleet_tro_svi`, `fleet_tro_goriva_m`, `fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`, `tro_zarade`, `fleet_dobavljaci`, `fleet_magacin_rez`, `kasko_rate` | **[N] Formula je u bazi** — [P-27](#10-poznati-problemi-i-ograničenja) |

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`fleet/models.py`](../fleet/models.py) |
| Rute i dozvole | [`fleet/urls.py`](../fleet/urls.py) |
| **Obračuni goriva** | [`fleet/support/fuel.py`](../fleet/support/fuel.py) |
| **Nova analitika i ekonomske procene** | [`fleet/services/economics.py`](../fleet/services/economics.py), [`fleet/economics_models.py`](../fleet/economics_models.py) |
| Nasleđeni trošak/km i pragovi — radi kompatibilnosti | [`fleet/support/dashboard.py`](../fleet/support/dashboard.py), [`fleet/support/analytics.py`](../fleet/support/analytics.py) |
| Kilometraža | [`fleet/support/vehicle_mileage.py`](../fleet/support/vehicle_mileage.py) |
| Održavanje | [`fleet/support/vehicle_maintenance.py`](../fleet/support/vehicle_maintenance.py) |
| Presek stanja | [`fleet/support/fleet_snapshot.py`](../fleet/support/fleet_snapshot.py) |
| Izveštaji za upravu | [`fleet/support/management_reports.py`](../fleet/support/management_reports.py) |
| Upiti nad pogledima | [`fleet/support/report_queries.py`](../fleet/support/report_queries.py) |
| Preuzimanje iz ERP-a | [`fleet/sync/external.py`](../fleet/sync/external.py), [`services.py`](../fleet/sync/services.py) |
| **Selenium preuzimanje goriva** | [`fleet/sync/selenium.py`](../fleet/sync/selenium.py) |
| Čišćenje duplikata goriva | [`fleet/support/fuel_cleanup.py`](../fleet/support/fuel_cleanup.py) |
| Pozadinski poslovi | [`fleet/tasks.py`](../fleet/tasks.py) |
| **Normalizacija tablica** | [`fleet/support/vehicle.py: format_license_plate()`](../fleet/support/vehicle.py) |

**41 upravljačka komanda** u `fleet/management/commands/` — sinhronizacije, uvozi,
ispravke i provere. [P]

---

### 11. Ulazni i izlazni podaci

#### Ulaz

| Vrsta | Izvor |
|---|---|
| Sinhronizacija | 9 nasleđenih pogleda |
| Selenium | NIS i OMV portali |
| Uvoz datoteka | NIS Excel, OMV CSV (putnička i teretna) |
| Ručni unos | Vozila, dokumenta, kvarovi, putni nalozi |

#### Izlaz

| Vrsta | Šta |
|---|---|
| Excel | Lizing, izveštaji za upravu |
| CSV | Vozila, mesečni troškovi polisa i servisa |
| ZIP | Tenderska dokumentacija vozila |
| Štampa | Putni nalog, prilog za inostranstvo, prijava kvara, radni nalog, trebovanje |
| Podaci drugim modulima | Vozila i zaduženja Finansijama, kvarovi Nabavci, putni nalozi Isplatama |

---

### 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Kadrovi** | Zaposleni na putnom nalogu i zaduženju vozila |
| **Nabavka** | Kvar → predmet nabavke; EUF fakture → polise i dokazi o održavanju |
| **Ugovori** | Ugovor o lizingu (`Lease.contract`) i o finansiranju (`VehicleHolding.financing_contract`) |
| **Finansije** | Vozila i zaduženja na šifri posla; trošak zarada |
| **Isplate** | Putni nalozi sa akontacijom → virman |
| **Administracija** | Organizacione jedinice i centri |
| **Organizacija (registar)** | Kolona `org_node` na šest tabela, samo upis i poređenje — čitanje iz registra još nije uključeno |

---

### 13. Izveštaji i analize

**24 obračuna + 11 izveštaja nad pogledima.** Detaljno:

| Poglavlje | Sadržaj |
|---|---|
| [6.2. Gorivo](#62-flota--obračuni-goriva) | Prečišćavanje OMV, potrošnja, gorivo po šifri posla |
| [6.3. Troškovi](#63-flota--troškovi-vozila) | Dokumentacija nasleđenih obračuna |
| [6.12. Ekonomika flote](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa) | Aktuelna metodologija zajedničke analitike i poređenja budućih opcija |
| [6.4. Polise i lizing](#64-flota--polise-lizing-i-servisi) | Mesečni troškovi, istek polisa |
| [6.5. Izveštaji](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji) | Kilometraža, održavanje, presek stanja, izveštaji za upravu |

---

### 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `uprava` | Sve |
| `sekretarijat` | Zaposleni, putni nalozi: unos, izmena, štampa, storno |
| `zaposleni` | **Samo zaduženja vozila** — spisak, otvaranje, detalj, obračun, štampa. **Ne može** menjati zaduženje |
| Uz dozvoljene centre | Kontrolna tabla i izveštaji ograničeni na svoje centre |

**Posebna pravila [P]:**

- Zatvoreno zaduženje vozila može menjati **samo superuser**.
- Statistiku centra vidi superuser ili korisnik sa tim centrom u `allowed_centers`
  (usklađeno 18.09.2026., [P-13](#10-poznati-problemi-i-ograničenja)).
- Izveštaji za upravu koriste **oba** mehanizma za centre — vidi [P-19](#10-poznati-problemi-i-ograničenja).

---

### 15. Validacije i kontrole

| Kontrola | Gde | Poruka / ponašanje |
|---|---|---|
| **Format tablica** | `TrafficCard` | `AA999-AA` ili `AA9999-AA` |
| **Tablica kod drugog vozila** | `TrafficCard.clean()` | *„Ove tablice su već povezane sa drugim vozilom.“* |
| Datum izdavanja u budućnosti | `TrafficCard.clean()` | Odbija se |
| **Preklapanje osnova raspolaganja** | `VehicleHolding.clean()` | *„Period se preklapa… Najpre završite prethodni period.“* |
| Period raspolaganja izvan ugovora | `VehicleHolding.clean()` | Odbija se |
| Ugovor ne pripada vozilu | `VehicleHolding.clean()` | Odbija se |
| Finansiranje samo za vlasništvo IMS | `VehicleHolding.clean()` | Odbija se |
| **Jedna dodela po vozilu i danu** | `JobCode` | Kontrola u bazi |
| Broj putnog naloga | `PutniNalog.generate_order_number()` | *„Nedostaje početni broj za izabrani centar/godinu.“* |
| Tablica kod više vozila | `TrafficCard.for_plate()` | **Namerno odbija da pogađa** |
| Broj zaduženja vozila | `VehicleTravelOrder.save()` | Uz `select_for_update()` |
| Brisanje slike posle potvrde | `VehicleTenderDocument` | `transaction.on_commit` |

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Vozilo bez saobraćajne | Prikazuje se broj šasije umesto tablica |
| Tablica pripada većem broju vozila | Sinhronizacija **preskače** taj red |
| Vozilo bez dodele | Grupa „Bez centra“, zasebno upozorenje |
| Otpisano vozilo | Ne ulazi u analitiku; broji se zasebno na kontrolnoj tabli |
| OMV duplikati | Brišu se pri uvozu i filtriraju pri čitanju |
| Novo vozilo (mlađe od godinu dana) | Amortizacija razmazana na 365 dana |
| Nedovršena polisa | **Ne ulazi** u upozorenja o isteku |
| Otvoreno zaduženje | Obračun goriva ide **do današnjeg dana** |
| Više otvorenih zaduženja istog vozila | Upozorenje na kontrolnoj tabli |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Potrebno |
|---|---|---|
| 1 | **Formula 11 izveštaja** nad nasleđenim pogledima | DDL pogleda — [P-27](#10-poznati-problemi-i-ograničenja) |
| 2 | Sadržaj pogleda `fleet_servisi`, `fleet_trebovanja`, `fleet_zatvoren_putni`, `lizing_kamate` | DDL |
| 3 | **Poreklo pragova troška po kilometru** | Potvrda naručioca — **Q18** |
| 4 | Da li se izveštaji koriste kao osnov za knjiženje | Potvrda — **Q3** |
| 5 | Zašto se službeni izlazak računa do 16:00 *(deli se sa Kadrovima)* | Potvrda — **Q27** |
| 6 | Da li se izveštaj mesečnih troškova lizinga uopšte koristi | Potvrda — **Q21** |
| 7 | Poreklo pristupnih podataka za NIS i OMV portale | Potvrda — **Q7** |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.2–6.5](#62-flota--obračuni-goriva) | Svi obračuni Flote |
| [4.4](#44-vozni-park--fleet) | Tabele Flote |
| [7. Integracije](#7-integracije) | NIS, OMV i nasleđeni pogledi |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-02 … P-14, P-23 … P-27 |

---

## 3.2. Kadrovi

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Kadrovi** |
| Tehnički naziv | Django aplikacija `hr` |
| Adresa | `/hr/` |
| Bočni meni | `sidebar_kadrovi.html` |

> **[P] Zamka:** modeli `Employee` i `EmployeeCVItem` imaju `app_label = "fleet"`,
> pa su im tabele **`fleet_employee`** i **`fleet_employeecvitem`**, a ne `hr_*`.

---

### 2. Poslovna namena

Vodi **zaposlene i njihovo radno vreme**:

1. **Ko su zaposleni** — evidencija sinhronizovana iz kadrovske baze.
2. **Koliko je ko radio** — radna lista po šiframa posla, uz kontrolu iz evidencije prolazaka.
3. **Ko je odsustvovao** — godišnji odmori i bolovanja.
4. **Kako je ocenjen** — mesečna ocena koja daje lični koeficijent za zaradu.

> **[P] Modul ne obračunava zarade.** Izričito je navedeno u kodu:
> *„without payroll calculations“*. Rezultati se prosleđuju sistemu za obračun zarada.

---

### 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Svaki zaposleni** | Popunjava **svoju** radnu listu, dopunjava svoj CV, ispravlja prikaz imena |
| **Kadrovska služba** | Vodi zaposlene, uvozi bolovanja, sinhronizuje odmore, održava šifarnike |
| **Neposredni rukovodilac** | Ocenjuje zaposlene svoje organizacione jedinice |
| **Direktor centra i generalni direktor** | Daju saglasnost na ocene |
| **Kadrovi i superuser** | Radne liste drugih zaposlenih u dozvoljenom obuhvatu |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Zaposleni** | Evidencija, CV stavke, ispravka prikaza imena |
| **Radna lista** | Mesečna evidencija sati po šiframa posla, topli obrok, terenski dodatak; predlog popunjavanja iz prolazaka, putnih naloga, bolovanja, praznika i slave (K-11) |
| **Evidencija prolazaka** | Prikaz dnevnih sati iz sistema kontrole pristupa, uz spisak problema |
| **Godišnji odmori** | Dodele i rešenja preuzeti iz obračuna zarada |
| **Bolovanja** | Uvoz RFZO Excel izvoza, povezivanje po JMBG |
| **Ocenjivanje** | Šest merila, bodovi 0–4, lični koeficijent, saglasnost u tri nivoa |
| **Zahtevi** | Zahtev za izdavanje rešenja, sa automatskim brojem; ko podnosi i ko odobrava upisuje se u zahtev; isti zahtev za više zaposlenih odjednom |
| **Rešenja** | Rešenja o prekovremenom i noćnom radu, radu vikendom i praznikom, plaćenom odsustvu i zameni odsutnog zaposlenog — iz zahteva ili bez njega, pojedinačno i grupno, sa štampom |
| **Šifarnici** | Vrste rada/odsustva, elementi radne liste, vrste primalaca, merila ocenjivanja |

---

### 5. Glavni korisnički ekrani

| Ekran | Adresa | Ko pristupa |
|---|---|---|
| Spisak zaposlenih | `/zaposleni/` | Kadrovska služba |
| Detalj zaposlenog | `/zaposleni/<id>/` | Kadrovska služba |
| **Moj profil** | `/moj-profil/` | Svaki zaposleni |
| Ispravka imena za prikaz | `/moj-profil/ispravi-ime/` | Svaki zaposleni |
| CV stavke | `/moj-profil/cv/novo/` | Svaki zaposleni |
| **Moja radna lista** | `/hr/radna-lista/` | Svaki zaposleni |
| Radna lista drugog zaposlenog | `/hr/zaposleni/<id>/radna-lista/` | **Samo superuser** |
| Štampa radne liste | `/hr/radna-lista/<id>/stampa/` | Zaposleni |
| **Godišnji odmori** | `/hr/godisnji-odmori/` | Kadrovska služba |
| Sinhronizacija odmora | `/hr/godisnji-odmori/sinhronizacija/` | Kadrovska služba |
| **Bolovanja** | `/hr/bolovanja/` | Kadrovska služba |
| Uvoz bolovanja | `/hr/bolovanja/uvoz/` | Kadrovska služba |
| **Ocenjivanje** | `/hr/ocenjivanje/` | Rukovodioci |
| Nova ocena | `/hr/ocenjivanje/novo/` | Neposredni rukovodilac |
| Štampa ocene | `/hr/ocenjivanje/<id>/stampa/` | Rukovodioci |
| Saglasnost | `/hr/ocenjivanje/<id>/saglasnost/` | Imenovani ocenjivač |
| Grupna saglasnost | `/hr/ocenjivanje/saglasnost/` | Imenovani ocenjivač |
| Šifarnik ocenjivanja | `/hr/ocenjivanje/sifrarnik/` | Kadrovska služba |
| **Zahtevi zaposlenih** | `/hr/zahtevi/` | Kadrovska služba |
| Novi zahtev | `/hr/zahtevi/novi/` | Kadrovska služba |
| Isti zahtev za više zaposlenih | `/hr/zahtevi/grupno/` | Kadrovska služba |
| Detalj zahteva i „Dodaj rešenje iz zahteva“ | `/hr/zahtevi/<id>/` | Kadrovska služba |
| Štampa zahteva | `/hr/zahtevi/<id>/stampa/`, `/hr/zahtevi/stampa/` | Kadrovska služba |
| **Rešenja zaposlenih** | `/hr/resenja/` | Kadrovska služba |
| Novo rešenje | `/hr/resenja/novo/` | Kadrovska služba |
| Grupno izdavanje | `/hr/resenja/grupno/` | Kadrovska služba |
| Štampa rešenja | `/hr/resenja/<id>/stampa/`, `/hr/resenja/stampa/` | Kadrovska služba |
| Šifarnik rešenja | `/hr/resenja/sifrarnik/` | **Samo Uprava** |
| Elementi radne liste | `/hr/sifrarnici/elementi-rl/` | Kadrovska služba |

---

### 6. Podaci koje korisnik unosi

| Podatak | Ekran | Ko unosi |
|---|---|---|
| **Sati po danima i šiframa posla** | Radna lista | **Zaposleni** |
| Vrsta rada / odsustva po redu | Radna lista | Zaposleni |
| Topli obrok — broj dana i šifra posla | Radna lista | Zaposleni |
| Terenski dodatak — broj dana | Radna lista | Zaposleni (predlaže se iz putnih naloga) |
| **Datum slave** | Izmena zaposlenog, sekcija „Obrazovanje i slava“ | Kadrovska služba; predlaže se iz naziva slave, koriste se dan i mesec |
| Ispravka imena za prikaz | Moj profil | Zaposleni |
| CV stavke | Moj profil | Zaposleni |
| **Bodovi po merilima i komentari** | Ocenjivanje | Neposredni rukovodilac |
| Saglasnost, korekcija koeficijenta, obrazloženje | Saglasnost | Direktor centra, generalni direktor |
| RFZO Excel datoteka i datum izvoza | Uvoz bolovanja | Kadrovska služba |
| **Vrsta zahteva, zaposleni, datum, period ili dani, razlog** | Zahtevi | Kadrovska služba |
| **Ko podnosi i ko odobrava zahtev**, sa funkcijama | Zahtevi | Kadrovska služba |
| Poslovi koje zaposleni preuzima (zamena odsutnog) | Zahtevi, Rešenja | Kadrovska služba |
| Datum rešenja i potpisnik; broj samo za rešenje **bez** zahteva | Rešenja | Kadrovska služba |
| Broj i datum zahteva kao tekst — samo za rešenje bez zahteva | Rešenja | Kadrovska služba |
| Ime u drugom padežu, naziv OJ i radnog mesta u tekstu rešenja | Rešenja | Kadrovska služba |
| Ime i prezime ćirilicom (kada preslovljavanje pogreši) | Detalj zaposlenog | Kadrovska služba |
| Šifarnici | Šifarnici | Kadrovska služba |

---

### 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| **Zaposleni** | `IMS_ERP.dbo.hr_employee` | Dnevno 01:10 |
| **Prolasci radnika** | `INFORMATIKA23.ID.dbo.C_Prolasci_Radnika` | **Pri otvaranju radne liste** |
| Šifarnik tastera | `INFORMATIKA23.ID.dbo.C_Tasteri` | Pri otvaranju |
| Obračunati parovi prolazaka | `INFORMATIKA23.ID.dbo.c_parovi_radnika_detalji` + `SERFIN.bazaldims.dbo.radnik` | Komanda `hr_attendance_summary` |
| **Godišnji odmori** | `[putgeo-server].[BazaLDIMS].[dbo].[Godmor]`, `[GodmorKor]` | **Ručno** |
| Vrste primalaca | `dbo.hr_employee` | Uz šifarnik |

> **[P] Zaštita identiteta:** polje `skip_hr_identity_update` sprečava da noćna
> sinhronizacija prepiše titulu, ime, prezime i pol — jer zaposleni sam ispravlja
> prikaz svog imena.

---

### 8. Tabele i kolone

Detaljno: [4.5. Kadrovi](#45-kadrovi--hr). **20 tabela.**

| Tabela | Uloga |
|---|---|
| **`fleet_employee`** | Zaposleni — ključ je `employee_code` |
| `fleet_employeecvitem` | CV stavke |
| `hr_worktimesheet`, `hr_worktimesheetline` | Radna lista i redovi (31 kolona sati) |
| `fleet_employee.slava_datum` | Datum krsne slave (koriste se dan i mesec); HR sinhronizacija ga ne menja, naziv slave dolazi iz HR-a |
| `hr_worktimecategory`, `hr_worktimeelement`, `hr_recipienttype` | Šifarnici radne liste |
| `hr_annualleaveallowance`, `hr_annualleavedecision`, `hr_annualleavesync` | Godišnji odmori |
| `hr_sickleave`, `hr_sickleaveimport` | Bolovanja |
| `hr_evaluationgroup`, `hr_evaluationcriterion`, `hr_evaluationscale` | Šifarnik ocenjivanja |
| `hr_evaluationunitsetup`, `hr_evaluationemployeesetup` | Ko koga ocenjuje |
| **`hr_employeeevaluation`** | **Nepromenljiva ocena sa JSON snimkom** |
| `hr_evaluationapproval` | Saglasnosti po nivoima |
| `hr_vrstaresenja` | Šifarnik obrazaca rešenja — tekstovi ćirilicom |
| `hr_potpisnik` | Ko potpisuje rešenja i u kom periodu |
| **`hr_resenje`** | **Izdato rešenje sa JSON snimkom dokumenta** |
| `hr_resenjedan` | Pojedinačni dani rešenja (vikend, praznik, prekovremeni) |
| `hr_vrstazahteva` | Šifarnik obrazaca zahteva — tekstovi ćirilicom, rešenje koje se po zahtevu izdaje |
| `hr_brojaczahteva` | Poslednji dodeljeni redni broj zahteva po godini |
| **`hr_zahtev`** | **Zahtev sa automatskim brojem, podnosiocem, odobravaocem i JSON snimkom** |
| `hr_zahtevdan` | Pojedinačni dani zahteva |

---

### 9. SQL pogledi i povezani serveri

| Objekat | Server | Namena | Status |
|---|---|---|---|
| `dbo.hr_employee` | `IMS_ERP` | Zaposleni | **[N]** Sadržaj nije potvrđen |
| `Radnici`, `C_Prolasci_Radnika`, `C_Tasteri`, `c_parovi_radnika_detalji` | **`INFORMATIKA23.ID`** | Kontrola pristupa | Kolone poznate iz upita |
| `radnik` | **`SERFIN.bazaldims`** | OJ i ime uz parove | Kolone poznate |
| `Godmor`, `GodmorKor` | **`PUTGEO-SERVER.BazaLDIMS`** | Godišnji odmori | Kolone poznate |

> **[P] Modul zavisi od tri udaljena servera.** Ako nisu dostupni, radna lista se
> otvara, ali bez prolazaka, uz poruku *„Izvor prolazaka trenutno nije dostupan.“*

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`hr/models.py`](../hr/models.py), [`hr/evaluation_models.py`](../hr/evaluation_models.py), [`hr/resenja_models.py`](../hr/resenja_models.py) |
| **Evidencija prolazaka** | [`hr/services/attendance.py`](../hr/services/attendance.py) |
| **Ocenjivanje** | [`hr/services/evaluations.py`](../hr/services/evaluations.py) |
| **Rešenja** | [`hr/services/resenja.py`](../hr/services/resenja.py) |
| **Zahtevi** | [`hr/services/zahtevi.py`](../hr/services/zahtevi.py), [`hr/zahtevi_models.py`](../hr/zahtevi_models.py) |
| Godišnji odmori | [`hr/services/annual_leave.py`](../hr/services/annual_leave.py) |
| Bolovanja | [`hr/services/sick_leave.py`](../hr/services/sick_leave.py) |
| Šifarnik radne liste | [`hr/services/work_time_catalog.py`](../hr/services/work_time_catalog.py) |
| Sinhronizacija zaposlenih | [`hr/sync.py`](../hr/sync.py) |
| Radna lista | [`hr/views.py: MyWorkTimeSheetView`](../hr/views.py) |
| **Predlog radne liste** | [`hr/services/work_time_prefill.py`](../hr/services/work_time_prefill.py), praznici i slave: [`hr/services/praznici.py`](../hr/services/praznici.py) |

Testovi: `hr/tests.py`, `test_annual_leave.py`, `test_evaluations.py`,
`test_sick_leave.py`, `test_work_time_catalog.py`, `test_resenja.py`, `test_zahtevi.py`. [P]

---

### 11. Ulazni i izlazni podaci

| Smer | Šta |
|---|---|
| **Ulaz** | Kadrovska baza, prolasci, godišnji odmori iz zarada, RFZO Excel, Excel šifarnici |
| **Izlaz** | Štampa radne liste, **štampa ocene sa tri potpisa** |

> **[N] Q3:** nije potvrđeno kako lični koeficijent i sati sa radne liste stižu u
> obračun zarada — prepisivanjem sa odštampanog obrasca ili nekim prenosom.
> U kodu **nema izvoza** ni veze ka sistemu zarada.

---

### 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Flota** | Zaposleni na putnom nalogu i zaduženju vozila; radna lista prikazuje putne naloge |
| **Mobilni** | Zaposleni uz broj telefona |
| **Isplate** | Partija i opština boravka zaposlenog ulaze u virman |
| **Ugovori** | Ocenjivači po organizacionoj jedinici |
| **Administracija** | Korisnički nalog povezan sa zaposlenim (`CustomUser.employee`) |

---

### 13. Izveštaji i analize

**9 obračuna.** Detaljno: [6.6. Kadrovi](#66-kadrovi--obračuni).

| Oznaka | Naziv |
|---|---|
| K-01, K-02 | Dnevni sati rada — **dva različita postupka** ([P-28](#10-poznati-problemi-i-ograničenja)) |
| K-03 | Problemi u parovima prolazaka |
| K-04, K-05 | Sati radne liste |
| K-06 | Godišnji odmori |
| K-07 | Bolovanja |
| **K-08** | **Stimulacija i lični koeficijent** |
| K-09 | Tok saglasnosti |

---

### 14. Uloge i prava pristupa

| Dozvola | Šta omogućava |
|---|---|
| `hr:work_time_sheet` | Svoja radna lista |
| `hr:sick_leave_list`, `hr:sick_leave_import` | Bolovanja |
| `hr:annual_leave_list` | Godišnji odmori |
| `hr:work_time_catalog` | Šifarnici |
| `hr:evaluation_list`, `hr:evaluation_create`, `hr:evaluation_approve` | Ocenjivanje |
| **`hr:evaluation_view_all`** | Vidi i ocenjuje **sve** zaposlene |
| `hr:resenje_list`, `hr:resenje_create`, `hr:resenje_izdaj` | Rešenja — pregled, unos, izdavanje |
| `hr:resenje_bulk_create`, `hr:resenje_print` | Grupno izdavanje i štampa |
| `hr:resenje_catalog` | Šifarnik vrsta rešenja i potpisnika |
| **`hr:resenje_view_all`** | Vidi rešenja i zahteve **svih** centara |
| `hr:zahtev_list`, `hr:zahtev_create`, `hr:zahtev_bulk_create` | Zahtevi — pregled, unos, isti zahtev za više zaposlenih |
| `hr:zahtev_resenje_create`, `hr:zahtev_bulk_resenja` | Rešenje iz jednog ili više zahteva |
| `hr:zahtev_podnesi`, `hr:zahtev_storniraj`, `hr:zahtev_print` | Zaključavanje, storniranje i štampa zahteva |

**Posebna pravila [P]:**

- **Sekretarijat** dobija operativne dozvole za rešenja:
  listu, detalj, unos i izmenu nacrta, brisanje, predlog teksta, izdavanje, storniranje,
  pojedinačnu i grupnu štampu i grupni unos. Sinhronizacija dopunjava ove uloge bez
  menjanja njihovih korisnika. Uloga **Pregled** time ne dobija pravo unosa rešenja.
- **Kadrovi** (`kadrovi`) zamenjuju ulogu **Kadrovik — rešenja**, zadržavaju njene korisnike
  i dobijaju sve funkcije kadrovskog modula, uključujući šifarnike. Podaci se ograničavaju
  centrima i kadrovskim OJ iz korisničkog profila; kod `hr:kadrovi_manage` omogućava
  pregled i ocenjivanje zaposlenih u tom obuhvatu. Bez obuhvata nema tuđih podataka.
- `hr:resenje_view_all` i `hr:evaluation_view_all` ostaju posebne dozvole za sve centre;
  kompletna uloga Kadrovi ih ne dobija automatski.
- Bez dozvole `hr:evaluation_view_all`, rukovodilac ocenjuje **samo zaposlene svojih OJ**.
- Ocenu vidi onaj ko ju je napravio **ili** je na njoj imenovan kao ocenjivač.
- Saglasnost daje **isključivo imenovani ocenjivač sa svog naloga**.
- Tuđu radnu listu otvara superuser ili korisnik sa `hr:employee_work_time_sheet`,
  samo za zaposlene u svom obuhvatu. Direktan URL i štampa imaju istu proveru obuhvata.
- Korisnik bez povezanog zaposlenog **ne može** otvoriti radnu listu.
- Bez dozvole `hr:resenje_view_all`, korisnik vidi rešenja dodeljenih centara i OJ
  prema snimljenim šiframa na rešenju. Uloga Kadrovi bez obuhvata ne vidi tuđe podatke.
  Za ranije operativne uloge bez obuhvata ostaje pravilo: samo sopstvena rešenja.
- **Izdato rešenje se više ne menja** — ispravka ide preko storniranja i novog rešenja.
- Dozvole za zahteve (`hr:zahtev_*`) dobijaju Uprava, Kadrovi i Sekretarijat, isto kao
  operativne dozvole za rešenja. Zahtev je vidljiv po istom pravilu kao rešenje: po
  centru i OJ snimljenim na zahtevu.

Od 24.09.2026. `hr/access.py` ograničava spisak, detalje i izmenu zaposlenih, radne liste,
odmore, bolovanja i pristup Kadrova ocenjivanju. Kod rešenja proveravaju se i pojedinačni
unos, grupni unos, predlog teksta i snimljene šifre OJ/centra. Kadrovske OJ biraju se
u Administracija → Korisnici → Uloge i dozvole. Ograničenja podataka ne menjaju obračune
ni pravilo da saglasnost na ocenu daje imenovani ocenjivač.

#### Forme Kadrova u sekcijama

Sve forme za unos u Kadrovima imaju isti raspored (`hr/templates/hr/forms/base.html`,
stilovi `hr/static/hr/forme.css`, ponašanje `hr/static/hr/forme.js`):

- polja su podeljena u **sekcije**; svaka sekcija ima kratak opis i dugme **Uputstvo** koje klizno
  otvara objašnjenje, a sva uputstva su zajedno u prozoru „Uputstvo“ u zaglavlju;
- **kartica „Sekcije forme“ desno** ostaje na ekranu pri pomeranju, pokazuje sekciju koja se gleda
  i broj grešaka po sekciji; sekcija koja se sakrije (npr. „Pojedinačni dani“ kada ih izabrana vrsta
  rešenja ne traži) nestaje i iz kartice; forma sa jednom sekcijom nema karticu;
- da/ne polja su **prekidači**; polja koja HR sinhronizacija prepisuje nose oznaku **„iz HR-a“**;
- traka **Odustani / Sačuvaj** stoji na dnu ekrana.

Forma navodi sekcije u `SECTIONS` (`hr/form_layout.py: SekcijeMixin`): oznaka, naslov, opis, polja,
uputstvo i ikonica. Polje koje nije razvrstano ide u „Ostalo“, pa novo polje modela ne nestaje iz
forme; forma bez `SECTIONS` prikazuje se kao jedna sekcija. Posebni delovi (tabela dana, spisak
zaposlenih, merila ocenjivanja) prave se oznakom `{% sekcija %}` iz `hr_forme`.

Na ovaj način su uređene: zaposleni (unos i izmena), ispravka imena, stavka CV-a, uvoz bolovanja,
šifarnici elemenata radne liste i ocenjivanja, obrazac ocenjivanja, rešenje, zahtev, isti zahtev za
više zaposlenih i šifarnik rešenja (vrste rešenja i zahteva, potpisnici, brojač). Radna lista je
tabela za unos sati i ima svoj raspored.

#### Zahtev → rešenje

Od 24.09.2026. rešenje se pravi **iz zahteva**:

1. Kadrovik unosi zahtev (**Zahtevi → Novi zahtev**) ili isti zahtev za više zaposlenih
   odjednom. Svaki zaposleni dobija **svoj zahtev i svoj broj**.
2. Broj se dodeljuje **automatski**, u obliku `{centar}-{redni broj}` (npr. `43-17`).
   Redni broj je jedan niz za ceo Institut i počinje od 1 svake godine, kao u delovodniku.
   Početak niza se podešava u **Šifarnik → Brojač zahteva** (npr. da se nastavi na
   postojeći delovodnik); brojač ne može da ide unazad.
3. U zahtev se upisuje **ko podnosi** (zaposleni i funkcija, npr. „Финансијски директор“)
   i **ko odobrava**. Ako „ko odobrava“ ostane prazno, uzima se potpisnik rešenja koji
   važi na datum zahteva. Zahtev se štampa kao dopis sa oba potpisa.
4. Na detalju zahteva **Dodaj rešenje iz zahteva** pravi nacrt rešenja sa istim
   zaposlenim, periodom, danima, vremenom i dodatnim podacima. Iz liste zahteva može se
   napraviti rešenje za više označenih zahteva odjednom; zahtev koji već ima rešenje se
   preskače.
5. Rešenje dobija broj kao **podbroj zahteva**: `43-17/1`. Važi **jedan zahtev — jedno
   rešenje**, uključujući stornirano rešenje. Broj, zaposleni i podaci o zahtevu se ne menjaju ručno.
6. Rešenje i zahtev su povezani u oba smera: detalj rešenja vodi na zahtev, a detalj
   zahteva prikazuje povezano rešenje. Dok ga nema, prikazuje dugme **Dodaj rešenje**.
   Profil zaposlenog ima karticu „Zahtevi“.

Pravila [P]:

- Zahtev se ne briše, nego **stornira**; broj storniranog zahteva se ne koristi ponovo.
  Ni obrisan nacrt rešenja ne vraća svoj podbroj.
- Zahtev koji ima rešenje koje nije stornirano ne može da se stornira.
- **Podnošenje** zaključava tekst zahteva (JSON snimak). Zahtev se zaključava i sam, kada se
  izda prvo rešenje po njemu.
- Rešenje mora biti povezano sa postojećim zahtevom. Baza odbija praznu ili duplu vezu.
  Stari linkovi za samostalni i grupni unos vode na listu zahteva bez rešenja.
- Zamena odsutnog zaposlenog je **rešenje** („Imenovanje lica za zamenu“ → „Rešenje o zameni
  odsutnog zaposlenog“). Poslovi koje zaposleni preuzima unose se kao dodatno polje.
- Vrste rešenja i zahteva mogu imati **dodatna polja** (`oznaka|Naziv`), koja se u tekstu
  koriste kao `{oznaka}`. Polje koje izabrana vrsta traži je obavezno.

#### Unos i štampa rešenja zaposlenih

- Pol za tekst se preuzima iz evidencije (ženske oznake `F`, `Z`, `Ž` i `Ж` se
  prepoznaju jednako), uz mogućnost izbora oblika za konkretno rešenje. Izbor se čuva
  u nacrtu, a izdati dokument ostaje sačuvan u svom snimku.
- OJ se automatski bira prema zaposlenom. Izbor druge OJ ograničen je korisnikovim
  obuhvatom. Ako nema naziva u šifrarniku, predlaže se „OJ <šifra>“, koji se može
  tekstualno dopuniti. Centar se izvodi postojećim mapiranjem OJ na centar.
- Period od–do dostupan je za sve vrste; kod praznika ostaju obavezni pojedinačni
  dani sa vrstom praznika. Za rad se može uneti vreme smene od–do; završetak pre
  početka označava naredni dan. Rešenje automatski preuzima broj i datum povezanog zahteva.
- Polje **Ko potpisuje rešenje** prikazuje potpisnika prema datumu ili ručni izbor.
  Korisnik sa dozvolom `hr:resenje_catalog_create` može dodati osobu i funkciju
  direktno uz nacrt. Bez potpisnika nacrt se čuva, a izdavanje traži važeći potpis.

- Datumi u formama koriste format **dd.mm.gggg** i kalendar, kao ostali ekrani Kadrova.
  Pojedinačni dani se dodaju dugmetom **Dodaj dan**, a označavanjem **Ukloni** izostavljaju
  pri čuvanju nacrta. Grupni unos zadržava izabrane zaposlene i njihove brojeve rešenja
  ako validacija prijavi grešku.
- Detalj prikazuje dokument u širini **A4 (210 × 297 mm)**. Dugme **Štampaj** otvara
  prikaz za štampu ili čuvanje PDF-a: uspravan A4, margine **18 mm**, osnovni tekst Times New Roman 12 pt.
  Zaglavlje sadrži IMS logo, broj i datum, zatim naslov vrste i podatke zaposlenog.
  U dijalogu pregledača isključiti njegova zaglavlja i podnožja.
- Svako rešenje u grupnoj štampi počinje na novoj stranici. Duži tekst prelazi na narednu
  A4 stranicu, a blok potpisa i dostavljanja ostaje zajedno pri dnu poslednje strane.

---

### 15. Validacije i kontrole

| Kontrola | Poruka / ponašanje |
|---|---|
| Sati po danu | Ceo broj **0–24** |
| Dani izvan meseca | Brišu se pri čuvanju |
| **Uvoz bolovanja — sve ili ništa** | *„Nijedan red nije uvezen.“* |
| RFZO ID uz drugi JMBG | *„RFZO ID već postoji uz drugi JMBG.“* |
| **Stariji RFZO izvoz** | *„Datoteka je starija od već evidentiranih podataka.“* |
| Status „Zaključeno“ bez datuma | Odbija se |
| **Sinhronizacija odmora — sve ili ništa** | *„Ništa nije sinhronizovano.“* |
| Istovremena sinhronizacija odmora | *„Sinhronizacija je već u toku.“* |
| Obrazac ocene stariji od 24 sata | *„Obrazac je istekao ili nije važeći.“* |
| Dvostruko slanje ocene | Vraća se postojeća ocena (`request_key`) |
| Bodovi van sačuvane skale | *„Izabrani bodovi ne pripadaju sačuvanoj skali.“* |
| Preskakanje nivoa saglasnosti | *„Prethodni nivo još nije potvrdio obrazac.“* |
| Korekcija izvan granica obrasca | *„Koeficijent je izvan granica sačuvanog šifrarnika.“* |
| Korekcija bez obrazloženja | Odbija se |
| Rukovodilac menja koeficijent | *„Za korekciju merila sačuvajte novu verziju obrasca.“* |

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| **Smena preko ponoći** | **Ne uparuje se** — dva problema, sati se ne računaju ([P-28](#10-poznati-problemi-i-ograničenja)) |
| Pauza (taster 12) | Uvek prijavljena kao problem |
| Službeni izlazak | Računa se **do 16:00** |
| Zaboravljen ulazak ili izlazak | Par se ne računa, problem se prijavljuje |
| Izvor prolazaka nedostupan | Radna lista radi, sati prikazani kao „—“ |
| **Otvoreno bolovanje** | Prikazuje se do **datuma RFZO izvoza** ([P-29](#10-poznati-problemi-i-ograničenja)) |
| Više zaposlenih sa istim JMBG | Bolovanje se **ne povezuje**, uz napomenu |
| Šifra zaposlenog 0 u odmorima | Zapis se čuva **nepovezan** |
| Rešenje uklonjeno iz izvora | Označava se povučenim, **ne briše se** |
| Ocena je pogrešna | Ispravka je **nova revizija**, izvorna ostaje |
| Nazivi merila na ćirilici | Preslovljavaju se na latinicu pri prikazu |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | **Koji od dva obračuna sati je merodavan** | **P-28** |
| 2 | Zašto se službeni izlazak računa do 16:00 i da li je to zvanično radno vreme | **Q27** |
| 3 | Da li pauzu treba obračunati ili samo ne označavati kao problem | **Q25** |
| 4 | Da li je odobravanje radne liste („Odobreno“) predviđeno | **Q26** |
| 5 | **Kako lični koeficijent stiže u obračun zarada** | **Q3** |
| 6 | Poreklo koeficijenata u šifarniku ocenjivanja i zvanični pravilnik | **Q6** |
| 7 | Sadržaj pogleda `dbo.hr_employee` | DDL |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.6. Kadrovi](#66-kadrovi--obračuni) | Svih 9 obračuna |
| [4.5](#45-kadrovi--hr) | Tabele Kadrova |
| [7. Integracije](#7-integracije) | Povezani serveri i RFZO |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-28, P-29 |

---

## 3.3. Finansijska analitika

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Finansije** / „Finansijska analitika“ |
| Tehnički naziv | Django aplikacija `finansije` |
| Adresa | `/finansije/` |
| Bočni meni | `sidebar_finansije.html` |

---

### 2. Poslovna namena

Odgovara na pitanje: **koliko je koji posao i koji centar zaradio ili izgubio, i koliko
je novca stvarno ušlo i izašlo.**

Do ovog modula taj odgovor se dobijao tek posle obračuna u knjigovodstvu, pokretanjem
poslovnih procedura. Sada je dostupan na ekranu, **bez pokretanja ijedne procedure**. [P]

> **[P] Modul ne knjiži i ne menja poslovne podatke** — koristi isključivo `SELECT` upite
> nad izvorom. Jedini izuzetak je dugme „Osveži nalog_z“, koje pokreta jednu unapred
> određenu proceduru.

---

### 3. Korisnici modula

| Korisnik | Šta dobija |
|---|---|
| **Uprava** | Rezultat cele firme, po centrima i poslovima, rang-liste |
| **Rukovodioci centara** | Rezultat svog centra i svojih šifara posla |
| **Finansije** | Detalj posla: fakture, konta, zaposleni, vozila, potraživanja |
| **Rukovodioci poslova** | Kartica posla sa svim evidencijama |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Finansijski pregled** | Prihodi, rashodi i rezultat po centrima i poslovima, sa grafikonima i rang-listama |
| **Detaljni izveštaji** | Po šiframa posla, kontima, mesecima i centrima |
| **Zbirna tabela šifara posla** | 11 kolona: prihod, rashod, P−R, ZT, P−R−ZT, priliv, odliv, neto gotovina |
| **Dodatne analize** | Posebna kartica uz zbirnu tabelu: isti iznosi, četiri odnosa prema prihodima, prosečan broj ljudi i osam iznosa po čoveku; poseban Excel izvoz aktivne kartice |
| **Kartica (detalj) posla** | Osam tabova sa dokumentima i evidencijama |
| **Knjiženja** | Pojedinačne stavke sa filterima i izvozom |
| **Sinhronizacija** | Ručno pokretanje, istorija, kontrolni zbirovi, osvežavanje `nalog_z` |

Bočni meni ima posebnu stavku **Dodatne analize** koja direktno otvara tu
karticu. Obe kartice šifara posla imaju dugme **Izvezi u Excel**. Izvoz pravi
nativnu Excel tabelu sa filterima i sortiranjem u zaglavlju, naizmenično
obojenim redovima, formatiranim brojevima i zamrznutim zaglavljem i prve
tri kolone. Preuzimaju se sve šifre koje odgovaraju periodu, centru i
dozvolama, a ne samo trenutno prikazana stranica tabele.


#### Osam tabova na kartici posla [P]

| Tab | Sadržaj | Odakle |
|---|---|---|
| Fakture | Izdate fakture IF, konta `20400/20500` | Lokalna knjiženja |
| Interne fakture | Nalozi `ON`, konta `61420/61421/61521/64002` | Lokalna knjiženja |
| Rashodi | Mesečni rashodi po kontima | Lokalna knjiženja |
| **Vozila** | Vozila na šifri posla, po istorijskim dodelama | **Flota** |
| **Zaduženja vozila** | Ko je zadužio vozilo na tom poslu | **Flota** |
| **Zaposleni i zarade** | Lica iz zaključenih obračuna zarada | `bazaldims` |
| **Putni nalozi** | Službena putovanja na teret posla | **Flota** |
| **Potraživanja** | Saldo kupaca po starosnim razredima | **Potraživanja** |

---

### 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Finansijski pregled** | `/finansije/` |
| Detaljni izveštaji | `/finansije/izvestaji/` |
| Zbirna tabela šifara posla | `/finansije/izvestaji/?group=job` |
| **Kartica posla** | `/finansije/posao/?job=413111&year=2026&month=8` |
| Knjiženja | `/finansije/knjizenja/` |
| Izvoz u Excel | `/finansije/izvoz/` |
| **Sinhronizacija** | `/finansije/sinhronizacija/` |

---

### 6. Podaci koje korisnik unosi

**Nijedan poslovni podatak.** [P] Korisnik bira samo:

| Izbor | Gde |
|---|---|
| Period (od–do) | Svi ekrani |
| Centar, šifra posla, konto, vrsta naloga, OJ knjiženja | Detaljni izveštaji i knjiženja |
| Način grupisanja | Izveštaji |
| Pokretanje sinhronizacije | Ekran sinhronizacije |
| Osvežavanje `nalog_z` | Ekran sinhronizacije |

---

### 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada | Način |
|---|---|---|---|
| **Knjiženja** | `[PUTGEO-SERVER].[bazaims].dbo.nalog_z` | Svaki sat u :20 (tekuća godina), 03:50 (sve godine) | Sinhronizovano u `LedgerEntry` |
| Šifarnici poslova, konta, OJ, partnera | `bazaims.dbo.posao`, `konto`, `ob_jedin`, `partner` | Uz sinhronizaciju | Sinhronizovano i direktno |
| **Pravila zajedničkih troškova** | `bazaims.dbo.posao_mes`, `blokraspodela` | **Pri otvaranju ekrana** | Direktan `SELECT` |
| **Tok gotovine** | `nalog_z`, `konto`, `vrsta_naloga`, `tipnal`, `pdv_arhiva`, `posao_mes` | **Pri otvaranju ekrana** | Direktan `SELECT` |
| Konta zarada | `[PUTGEO-SERVER].[bazaldims].dbo.element` | Pri otvaranju | Direktan `SELECT` |
| Zaposleni na poslu | `bazaldims.dbo.Zarada`, `PomLD`, `Radnik` | Pri otvaranju | Direktan `SELECT` |
| Lokalna kopija `nalog_z` | `IMS_ERP.dbo.sp_AzurirajNalogZ` | 10:00 i 11:00 | Procedura |

> **[P] Važno:** samo prihodi i rashodi rade iz lokalne kopije. **Zajednički troškovi,
> tok gotovine i zaposleni zahtevaju da udaljeni server radi u trenutku otvaranja ekrana.**

---

### 8. Tabele i kolone

Detaljno: [4.6. Finansijska analitika](#46-finansijska-analitika--finansije).
**Samo 4 tabele** — modul je pretežno „čitač“.

| Tabela | Uloga | Ključ |
|---|---|---|
| **`finansije_ledgerentry`** | Lokalna kopija knjiženja | firma + godina + vrsta + broj + stavka |
| `finansije_financejob` | Šifarnik poslova | `(company, code)` |
| `finansije_syncrun` | Istorija sinhronizacije, kontrolni zbirovi | — |
| `finansije_nalogzrefreshrun` | Istorija osvežavanja `nalog_z` | — |

---

### 9. SQL objekti

| Objekat | Server | Namena |
|---|---|---|
| `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | `PUTGEO-SERVER.bazaims` | Knjiženja i šifarnici |
| `posao_mes`, `blokraspodela` | `PUTGEO-SERVER.bazaims` | Pravila zajedničkih troškova |
| `tipnal`, `vrsta_naloga`, `pdv_arhiva` | `PUTGEO-SERVER.bazaims` | Tok gotovine |
| `element`, `Zarada`, `PomLD`, `Radnik` | `PUTGEO-SERVER.bazaldims` | Zarade |
| **`sp_AzurirajNalogZ`** | `IMS_ERP` | **Jedina procedura koju modul pokreće** |

> **[P] Procedure koje se NE pokreću:** `SPFINizv52`, `53`, `55`, `52nt`, `SPLdKnjizenje`.
> Njihova **pravila su prepisana u Python**, ali se same procedure ne izvršavaju.

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`finansije/models.py`](../finansije/models.py) |
| **Čitanje izvora** | [`services/source.py`](../finansije/services/source.py) |
| **Sinhronizacija** | [`services/sync.py`](../finansije/services/sync.py) |
| Prihodi i rashodi | [`services/reports.py`](../finansije/services/reports.py) |
| **Zajednički troškovi** | [`services/shared_costs.py`](../finansije/services/shared_costs.py) |
| **Tok gotovine** | [`services/cash_flow.py`](../finansije/services/cash_flow.py) |
| Kartica posla | [`services/job_card.py`](../finansije/services/job_card.py), [`job_tables.py`](../finansije/services/job_tables.py) |
| Zaposleni i zarade | [`services/job_people.py`](../finansije/services/job_people.py) |
| **Procedura nalog_z** | [`services/nalog_z.py`](../finansije/services/nalog_z.py) |
| Grafikoni | [`services/charts.py`](../finansije/services/charts.py) |

Testovi: **121 test** u 7 fajlova. [P]

---

### 11. Ulazni i izlazni podaci

| Smer | Šta |
|---|---|
| **Ulaz** | Knjiženja i šifarnici sa dva udaljena servera; podaci Flote i Potraživanja |
| **Izlaz** | Ekrani i **izvoz u Excel** sa istim obuhvatom i napomenama |

> **[N] Q3:** rezultati se **ne knjiže** i ne prenose automatski. Nije potvrđeno
> da li ih neko preuzima i za koji dokument.

---

### 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Flota** | Vozila, zaduženja i putni nalozi na šifri posla — **uz dozvole Flote** |
| **Potraživanja** | Saldo kupaca po šifri posla — **uz dozvole Potraživanja** |
| **Administracija** | Dozvoljeni centri korisnika |

> **[P] Dvostruka provera prava:** za tab „Vozila“ traže se i `jobcode_list` i
> `vehicle_travel_order_list`; za „Zaposlene“ i `employee_list`. Finansijski pristup
> poslu **nije dovoljan** za tuđe module.

---

### 13. Izveštaji i analize

**18 obračuna.** Detaljno:
[6.1. Finansijska analitika](#61-finansijska-analitika--obračuni) i
postojeća metodologija (`finansije-metodologija-obracuna.md`, uklonjena 18.09.2026., u git istoriji `06f60c2`).

---

### 14. Uloge i prava pristupa

| Dozvola | Šta omogućava |
|---|---|
| `finansije:dashboard` | Pregled, izveštaji, kartica posla |
| `finansije:ledger` | Knjiženja |
| `finansije:export` | Izvoz u Excel |
| `finansije:sync_status` | Ekran sinhronizacije |
| **`finansije:view_all`** | **Ceo obuhvat firme** |

| Uloga | Obuhvat |
|---|---|
| `uprava` | Sve dozvole |
| `finansije` („Finansijska analitika“) | Pregled, knjiženja, izvoz — **ograničeno dozvoljenim centrima** |

**Posebna pravila [P]:**

- **Prazan spisak dozvoljenih centara nije globalan pristup.**
- Ukupni iznosi i procenti računaju se **iz korisniku dostupnog skupa** — dva korisnika
  mogu videti različite ukupne iznose.
- Za zajedničke troškove se **osnovice cele firme** moraju izračunati, ali se korisniku
  vraća samo rezultat za dostupne poslove.
- Ručno pokretanje sinhronizacije i procedure traži **i `sync_status` i `view_all`**.

---

### 15. Validacije i kontrole

| Kontrola | Ponašanje |
|---|---|
| **Kontrolni zbirovi pre objave** | Broj redova i oba iznosa po godini i kontu, iz nezavisnog upita. Neslaganje **zaustavlja** sinhronizaciju |
| Duplikat u šifarniku izvora | *„Dupliran ključ izvornog šifarnika; sinhronizacija je zaustavljena.“* |
| Zaključavanje sinhronizacije | SQL `sp_getapplock` — pokriva i komandnu liniju |
| Zaključavanje procedure | `sp_getapplock` u **istoj sesiji** koja pokreće proceduru |
| Prazan izvor | **Ne može** obrisati postojeće podatke |
| Neispravni brojači procedure | *„Procedura je vratila neispravne brojače.“* |
| Prekinut prethodni prolaz | Status **„Ishod nepoznat“** pri sledećem preuzimanju zaključavanja |
| Neispravan period | Finansijski rezultati se **ne prikazuju** |
| Nepotpuna pokrivenost koeficijentima | Iznos sa **zvezdicom** i objašnjenjem — „nepotpuno“ nije „nula“ |

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| **Zatvaranja godine** | Vrsta `ZAT` i konta `59900`/`69900` **namerno izuzeti** iz prihoda i rashoda |
| Godina bez uspešne sinhronizacije | Iznosi se **ne prikazuju kao nula** |
| Godišnji ZT | **Nije zbir** dvanaest mesečnih obračuna |
| Cela godina naspram zbira meseci (tok gotovine) | **Ne moraju biti jednaki** — periodna pravila procedure |
| Učešće preko 100% | Moguće kada drugi centri imaju gubitak — nije greška |
| Nulti imenilac | Procenat je **crtica**, ne nula |
| **Promena centra u šifarniku** | **Pregrupiše celu istoriju** ([P-44](#10-poznati-problemi-i-ograničenja)) |
| Knjiženje bez šifarnika | **Ne odbacuje se** — prikazuje se kao neraspoređeno |
| Prazna šifra posla u toku gotovine | Pripisuje se **`111111`**, po pravilu procedure |
| Prazna šifra u prihodima i rashodima | **Ne preimenuje se** |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Da li se raspodela zajedničkih troškova **knjiži** na klasu 5 | **Q41** / [P-43](#10-poznati-problemi-i-ograničenja) |
| 2 | Da li je potrebna istorija pripadnosti posla centru | **Q42** / [P-44](#10-poznati-problemi-i-ograničenja) |
| 3 | Ko obaveštava o izmeni kontnog plana ili procedura | **Q43** / [P-42](#10-poznati-problemi-i-ograničenja) |
| 4 | **Ukupan trošak zarada centra** | Čeka potvrdu izvora i pravila |
| 5 | Istorijski kadrovski spisak centra | Čeka potvrdu |
| 6 | Kako se rezultati koriste u knjiženju | **Q3** |

---

### 18. Banke

Ekran `/finansije/banke/` prikazuje partnere iz `PUTGEO-SERVER.bazaims.dbo.partner`
za podešenu firmu i `grupa=11`. Osnovni podaci čitaju se neposredno iz izvora,
sa istim poljima kao u Naplati. Novi podaci ne upisuju se u nasleđeni šifarnik.

Kartice banke idu redom: **Osnovni podaci, Kontakti, Promet po računima, Menice,
Garancije, Oročena sredstva**. Početni period je 1. januar tekuće godine do danas.
Može se izabrati drugi period unutar jedne godine od 2025. nadalje. Za svaki račun
odvojeno se prikazuju promet izabranog perioda i povećanja/smanjenja od početka
izabrane godine do danas, odnosno do 31. decembra za završene godine.

#### Knjiženja i povezivanje

- Čitaju se aktivni `LedgerEntry` redovi konta **23/24**, iz postojeće finansijske
  sinhronizacije. Nema dodatnog preuzimanja `nalog_z` ni izvršavanja procedura.
- Partner grupe 11 određuje banku. Za knjiženje bez partnera primenjuje se potvrđena
  `BankAccountRule` veza konta i banke. Ne pripisuje se istoimeni broj partnera druge grupe.
- Na ekranu **Veze konta i banaka** održavaju se banka, vrsta posla i napomena.
  Predlog prema nazivu nije primenjen dok se ne sačuva. Dvosmislene šifre, npr.
  AIK 15/16, ne spajaju se automatski. Zbirno konto 24100 i prelazni računi ne smeju
  imati jednu banku. Izvorni partner uvek ima prednost nad lokalnim pravilom.
- Nepovezana konta ostaju u posebnoj kontroli sa iznosima. Blagajne i prelazna konta
  prikazuju se odvojeno; ne ulaze u zbir banke. Lista iznosi u RSD, a detalj dodatno
  razdvaja izvorne valute. Račun iz partnera nije potvrđeni broj IMS računa.
- Garancije trenutno prikazuju **depozite za garancije** u zadatom obuhvatu 23/24,
  ne nominalne vrednosti garancija. Konta 88610/89610 i dugoročni depoziti 03/04 nisu
  deo ovog obuhvata i ne pripisuju se banci bez potvrđene veze.

#### Kontakti i menice

`BankContact` podržava više osoba po istom segmentu, funkciju, telefon, email osobe,
više zajedničkih emailova i napomenu. Red može imati samo zajedničke adrese segmenta.

`BankBillPlacement` povezuje postojeću `Menica` ili `UlaznaMenica` sa bankom kojoj
je predata, datumom predaje, vraćanja i napomenom. Jedna menica ne može imati dve
otvorene predaje. Banka registracije nije automatski mesto čuvanja/predaje; ta
informacija prikazuje se zasebno samo kada se poklapa naziv iz izvora.

#### Dozvole i isporuka

`bank_list` i `bank_detail` dodeljuju se ulozi Finansijska analitika, uz postojeće
ograničenje knjiženja po centrima. Ograničen prikaz jasno kaže da nije stanje cele
banke. Unos/izmena kontakata, veza i predaja traže svoju rutu i `finansije:view_all`.
Menice dodatno traže prava postojećih evidencija; predaja traži oba prava čitanja.
Uloga Uprava dobija nove kodove kroz postojeću sinhronizaciju dozvola.

Nova migracija Finansija 0003 dodaje samo lokalne tabele i ograničenja. Posle primene
registrovati nove dozvole. Obračun i kontrolni primer su u odeljku 6.1.21;
regresije su u `finansije/test_banks.py`.

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| **Postojeća metodologija** (uklonjena) | Potpun opis svih obračuna. Uklonjen iz repozitorijuma 18.09.2026.; sadržaj je dostupan u git istoriji, u izmeni `06f60c2` |
| [6.1](#61-finansijska-analitika--obračuni) | Registar obračuna i nalazi pregleda |
| [4.6](#46-finansijska-analitika--finansije) | Tabele |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-42, P-43, P-44 |

---

## 3.4. Nabavka

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Nabavka** |
| Tehnički naziv | Django aplikacija `nabavka` |
| Adresa | `/nabavka/` |
| Bočni meni | `sidebar_nabavka.html` |

---

### 2. Poslovna namena

Vodi **predmet nabavke od podnošenja zahteva do povezane fakture**, i time odgovara na
pitanje: **šta je traženo, šta je nabavljeno, po kojoj fakturi i na čiji teret.**

Uz to vodi **plan javnih nabavki sa verzijama**, da se vidi šta je i kada menjano.

---

### 3. Korisnici modula

| Korisnik | Šta radi | Uloga |
|---|---|---|
| **Služba nabavke** | Obrađuje predmete, povezuje fakture, izdaje narudžbenice | `nabavka` |
| **Podnosioci zahteva** | Podnose zahtev sa stavkama i štampaju ga | `zahtev` |
| **Garaža** | Podnosi garažne zahteve vezane za kvar i vozilo | `zahtev` |
| **Uprava** | Izveštaji i plan javnih nabavki | `uprava` |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Predmeti nabavke** | Zahtev za nabavku, zahtev za uslugu, predlog za opremu; stavke; statusi; štampa |
| **Garažni predmeti** | Zahtevi vezani za kvar i vozilo, sa vrstom intervencije |
| **EUF fakture** | Snimak preuzetih elektronskih ulaznih faktura, sa operativnim oznakama |
| **UF stavke i fakture** | Snimak stavki ulaznih faktura i izvedene fakture |
| **Roba** | Snimak robnog prometa |
| **Povezivanje** | Stavka ↔ izvor; predmet ↔ faktura; faktura ↔ šifra posla; predmet ↔ ugovor |
| **Plan javnih nabavki** | Uvoz Excel plana, verzije i razlike |
| **Narudžbenice** | Broj, datum, dobavljač, ugovor, status, iznos |
| **Izveštaji i alarmi** | Brojači po statusu i tipu, zbirovi, predmeti koji čekaju fakturu |
| **Ponavljanje zahteva** | Kopija predmeta sa stavkama, u statusu nacrta i sa novim brojem |

#### Statusi predmeta [P]

```
 Nacrt ──► Podneto ──► U obradi ──► Čeka fakturu ──► Faktura povezana ──► Završeno
                                                                    └──► Otkazano
```

Svaka promena statusa se beleži u `nabavka_status_log` sa komentarom i korisnikom. [P]

> **[P] Redosled nije nametnut.** Obrazac za promenu statusa nudi **sve** statuse i prelaz
> se **ne proverava** — iz bilo kog statusa može se preći u bilo koji. Dijagram iznad
> prikazuje **uobičajen tok**, ne pravilo koje aplikacija sprovodi.

**Jedini automatski prelaz [P]:** kada se stavka **novom** vezom poveže sa EUF fakturom, a
predmet je u statusu **`Čeka fakturu`**, status prelazi u **`Faktura povezana`**.

#### Ponavljanje zahteva [P]

Dugme „Ponovi“ pravi **novi predmet u statusu nacrta**, sa novim automatskim brojem. Sve u
jednoj transakciji.

| Šta se kopira | Šta se **ne** kopira |
|---|---|
| Tip, naslov, opis, garažna oznaka, šifra posla, dobavljač, ugovor, vozilo, vrsta intervencije, procenjena vrednost, valuta, napomena | **Veze stavki sa izvorima** (EUF/UF/roba) |
| Stavke: naziv, jedinica mere, količina, procenjena jedinična cena, napomena | `responsible` i `created_by` — postaju **trenutni korisnik** |
| | `needed_by` — postavlja se na **današnji datum** |

U status log novog predmeta upisuje se komentar *„Ponovljen zahtev {broj izvornog
predmeta}.“*, a korisnik dobija poruku *„Kreiran je novi zahtev {broj} sa kopiranim
stavkama.“*

#### Format broja predmeta [P]

> `<prefiks>-<centar>/<godina>-<redni broj>`

| Tip | Prefiks | Garažni prefiks |
|---|---|---|
| Zahtev za nabavku | `ZN` | **`ZNG`** |
| Zahtev za uslugu | `ZU` | **`ZUG`** |
| Predlog za opremu | `PLN` | — |

Primer: `ZNG-43/2026-7`. Bez centra u organizacionoj jedinici broj se **ne može dodeliti**.

---

### 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| Kontrolna tabla | `/nabavka/` |
| **Zahtevi (predmeti)** | `/nabavka/zahtevi/` |
| Novi zahtev | `/nabavka/zahtevi/novi/` |
| Detalj predmeta | `/nabavka/zahtevi/<id>/` |
| **Štampa zahteva** | `/nabavka/zahtevi/<id>/stampaj/` |
| **Trebovanje materijala** | `/nabavka/zahtevi/<id>/trebovanje-materijala/` |
| Ponovi zahtev | `/nabavka/zahtevi/<id>/ponovi/` |
| Povezivanje sa izvorom | `/nabavka/zahtevi/<id>/stavke/izvor/` |
| **EUF fakture** | `/nabavka/euf-fakture/` |
| Detalj EUF fakture | `/nabavka/euf-fakture/<id>/` |
| Vraćene šifre posla | `/nabavka/euf-fakture/<id>/vraceno-sifre/` |
| **UF stavke** | `/nabavka/uf-stavke/` |
| Detalj UF fakture | `/nabavka/uf-stavke/<id>/` |
| **Roba** | `/nabavka/roba/` |
| Kupovni ugovori | `/nabavka/kupovni-ugovori/` |
| **Plan javnih nabavki** | `/nabavka/javne-nabavke/` |
| Uvoz plana | `/nabavka/javne-nabavke/uvoz/` |
| Narudžbenice | `/nabavka/narudzbenice/` |
| Izveštaji | `/nabavka/izvestaji/` |
| Provera šifre posla partnera | `/nabavka/izvestaji/provera-sifre-posla-partnera/` |
| **Alarmi** | `/nabavka/alarmi/` |

#### Kontrolna tabla — šta stvarno prikazuje [P]

| Pokazatelj | Pravilo |
|---|---|
| Ukupno predmeta | Svi |
| **Otvoreni predmeti** | Svi **osim** `Završeno` i `Otkazano` |
| Čekaju fakturu | Status `Čeka fakturu` |
| Garažni predmeti | `is_garage = True` |
| Poslednji kreirani | **Poslednjih 8** po `-created_at` |

> **[P]** Pokazatelja „predmeti kojima je istekao rok“ **nema** — nad poljem `needed_by`
> ne postoji nijedan izračun. Raniji dokument ga je navodio; to nikad nije bilo u kodu ili
> je uklonjeno.

#### Detalj EUF fakture — šta se vidi i dopunjuje [P]

| Prikaz | Sadržaj |
|---|---|
| Povezane stavke zahteva | Kroz `nabavka_item_invoice_link` |
| Povezani kupovni ugovori | Ugovori sa šifrom tipa koja počinje sa `KUP` |
| Povezane dodatne šifre posla | Dodate ručno |
| **Interna dopuna** | `is_garage`, `vehicle`, `work_type`, `goes_to_warehouse`, `internal_note` |

Naziv partnera na spiskovima skraćuje se na **50 znakova**, a pun naziv se vidi kao
`title` atribut (na prelazak mišem). [P]

#### Kupovni ugovori — nabavni pogled na modul Ugovori [P]

Lista **ne duplira ugovore** — čita ih iz aplikacije `ugovori`.

| Osobina | Pravilo |
|---|---|
| **Šta je kupovni ugovor** | `contract_type__code` počinje sa **`KUP`** — to je jedino pravilo |
| Broj povezanih faktura | `Count("nabavka_invoice_links__invoice", distinct=True)` |
| Ukupna povezana vrednost | `Sum("nabavka_invoice_links__invoice__amount")` |
| Pretraga | Broj ugovora, naslov, predmet, **broj ugovora druge strane** |
| Partner | Naziv, PIB, matični broj i `external_sif_par` (kad je unos broj) |
| Ostali filteri | Vrsta, status, godina (`contract_date__year`) |

Isti `KUP` filter važi i pri povezivanju fakture sa ugovorom, uz isključivanje već
povezanih. [P]

> **[Z] Rizik u zbiru:** „ukupna povezana vrednost faktura“ koristi `Sum` preko veze ka
> više redova, **bez `distinct`** — isti obrazac koji je bio uzrok
> [P-36](#p-36--ukupan-iznos-faktura-na-izveštaju-nabavke-je-višestruko-uvećan).
> Ovde faktura može biti povezana sa jednim ugovorom više puta preko različitih veza;
> **nije provereno da li se to u praksi dešava.**

---

### 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| Naziv, opis, tip predmeta, datum zahteva | Podnosilac |
| Šifra posla (OJ), vozilo, vrsta intervencije | Podnosilac |
| **Stavke: naziv, JM, količina, procenjena cena** | Podnosilac |
| Procenjena vrednost predmeta i valuta | Podnosilac |
| Dobavljač, osnovni ugovor, odgovorno lice | Služba nabavke |
| Promena statusa sa komentarom | Služba nabavke |
| **Povezivanje stavke sa EUF, UF ili robom** | Služba nabavke |
| Oznake na EUF fakturi: šifra posla, vozilo, garaža, ide u magacin, vraćeno, napomena | Služba nabavke |
| Narudžbenica | Služba nabavke |
| Excel plan javnih nabavki | Služba nabavke |

---

### 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada | Tabela |
|---|---|---|---|
| **EUF fakture** | `dbo.nbv_preuzete_EUF` | Dnevno 02:20 | `nabavka_invoice` |
| **UF stavke** | `dbo.nbv_EUF_stavke` | Dnevno 02:45 | `nabavka_euf_item_snapshot` |
| UF fakture | Izvedeno grupisanjem stavki | Uz stavke | `nabavka_uf_invoice_snapshot` |
| **Roba** | `dbo.nbv_roba` | Dnevno 07:10 | `nabavka_goods_snapshot` |
| Šifra posla partnera | `dbo.nbv_sif_pos_par` | Pri otvaranju izveštaja | — |

#### Osnovna šifra posla EUF fakture — pun postupak [P]

**Osnovna šifra posla se ne bira ručno** — polje `job_code` uopšte nije u obrascu. Postavlja
se **samo automatski**, po tri grane:

| Uslov | Šta se upisuje |
|---|---|
| Faktura je **garažna**, vozilo **nepromenjeno** i već postoji `job_code` sa `job_code_source = "vehicle_snapshot"` | **Ništa** — snimak se zadržava |
| Faktura je **garažna** i izabrano je vozilo | `JobCode` tog vozila sa `organizational_unit__isnull=False`, sortirano `-assigned_date, -pk`, **prvi**. Upisuju se `job_code`, `job_code_source="vehicle_snapshot"` i `vehicle_job_code_assigned_date` |
| Faktura **nije garažna** ili **nema vozila** | `job_code = None`, `job_code_source = ""`, `vehicle_job_code_assigned_date = None` — **postojeća osnovna šifra se briše** |

Na ekranu polje nosi natpis **„Sifra posla automobila - snapshot“**.

> **[P] Zašto snimak:** faktura pamti šifru posla automobila **u trenutku povezivanja**.
> Ako se šifra posla automobila kasnije promeni, **faktura se ne menja**. Dodatne šifre
> posla dodaju se **ručno** i **ne menjaju** ovaj snimak.

#### Šta ponovno preuzimanje sme da promeni [P]

Pri ponovnom povlačenju iz izvora ažuriraju se **samo**: `invoice_number`, `invoice_date`,
`invoice_date_raw`, `supplier_name`, `amount`, `center`, `warehouse`, `registration`,
`synced_at`, `updated_at`.

> **Interni podaci koje je korisnik dopunio se ne diraju:** `job_code`, `job_code_source`,
> `vehicle_job_code_assigned_date`, `is_garage`, `vehicle`, `work_type`,
> `goes_to_warehouse`, `is_returned`, `internal_note`.

**Podrazumevane vrednosti nove EUF fakture [P]:**

| Polje | Podrazumevano |
|---|---|
| `is_returned` | `False` — nova faktura **nije vraćena** dok korisnik to ne označi |
| `goes_to_warehouse` | **`True` ako kolona `magacin` u izvoru nije prazna**; postavlja se samo pri prvom kreiranju i kasnije se ne prepisuje |

---

### 8. Tabele i kolone

#### Statusi narudžbenice [P]

`Nacrt` → `Poslato` → `Potvrđeno` → `Zatvoreno`, uz `Otkazano`. Podrazumevano `Nacrt`.

| Polje | Pravilo |
|---|---|
| `order_number` | **Jedinstven** |
| `order_date` | Podrazumevano **danas** |
| `currency` | Podrazumevano **RSD** |
| `supplier`, `contract` | `PROTECT` — ne mogu se obrisati dok postoji narudžbenica |

#### Kako se prikazuje povezani izvor stavke [P]

`ProcurementItem.source_reference_label` daje tri oblika:

```text
EUF:  EUF-2026-00123
UF:   UF-001/2026
Roba: ART-001 - Filter ulja (Faktura: TEST-UF-001/2026)
```

Kod robe, ako nema šifre artikla ili veznog dokumenta, na to mesto ide `/`.


Detaljno: [4.7. Nabavka](#47-nabavka--nabavka). **13 tabela.**

| Tabela | Uloga |
|---|---|
| `nabavka_procurement_case` | Predmet nabavke |
| `nabavka_procurement_item` | Stavka, sa vezom ka **tačno jednom** izvoru |
| `nabavka_invoice` | EUF faktura + operativne oznake |
| `nabavka_euf_item_snapshot` | UF stavka |
| `nabavka_uf_invoice_snapshot` | UF faktura (izvedena) |
| `nabavka_goods_snapshot` | Roba |
| `nabavka_invoice_link` | Predmet ↔ EUF ključ |
| `nabavka_item_invoice_link` | Stavka ↔ faktura (jedan na jedan) |
| `nabavka_invoice_job_code_link` | Faktura ↔ šifra posla (osnovna / dodatna, vraćeno) |
| `nabavka_contract_link`, `nabavka_invoice_contract_link` | Veze sa ugovorima |
| `nabavka_public_procurement_plan_version`, `…_item` | Plan javnih nabavki |
| `nabavka_purchase_order` | Narudžbenica |
| `nabavka_status_log` | Promene statusa |

---

### 9. SQL pogledi

| Pogled | Namena | Status |
|---|---|---|
| `dbo.nbv_preuzete_EUF` | EUF fakture | Kolone poznate: `datum, naziv_partnera, broj_fakutre, iznos, centar, magacin, registracija` |
| `dbo.nbv_EUF_stavke` | Stavke ulaznih faktura | **[N]** Sadržaj nije potvrđen |
| `dbo.nbv_roba` | Robni promet | **[N]** |
| `dbo.nbv_sif_pos_par` | Partner ↔ šifra posla | Kolone: `sif_par, naz_par, sif_pos` |

> **[P] Napomena:** kolona u izvoru se zove **`broj_fakutre`** — sa greškom u kucanju.
> Ne ispravljati u kodu; tako je u pogledu.

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`nabavka/models.py`](../nabavka/models.py) |
| **EUF fakture** | [`services/euf.py`](../nabavka/services/euf.py) |
| **UF stavke i roba** | [`services/source_snapshots.py`](../nabavka/services/source_snapshots.py) |
| **Plan javnih nabavki** | [`services/public_procurements.py`](../nabavka/services/public_procurements.py) |
| Uvoz garažnih zahteva iz Excel-a | [`services/excel_requests.py`](../nabavka/services/excel_requests.py) |
| Predmeti i stavke | [`views/cases.py`](../nabavka/views/cases.py) |
| Fakture | [`views/invoices.py`](../nabavka/views/invoices.py) |
| Pozadinski poslovi | [`nabavka/tasks.py`](../nabavka/tasks.py) |

---

### 11. Ulazni i izlazni podaci

| Smer | Šta |
|---|---|
| **Ulaz** | Tri nasleđena pogleda; Excel plan javnih nabavki; Excel garažni zahtevi; ručni unos |
| **Izlaz** | Štampa zahteva i trebovanja materijala; izvoz EUF faktura; podaci Floti |

---

### 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Flota** | Kvar (`garage_order`) i vozilo (`vehicle`) na predmetu; EUF fakture → polise; fakture i trebovanja → dokazi o održavanju |
| **Ugovori** | Dobavljač (`supplier`), osnovni ugovor (`contract`), kupovni ugovori |
| **Administracija** | Organizaciona jedinica i centar — određuju broj predmeta |

> **[P]** Kupovni ugovori su **pogled na modul Ugovori**, bez sopstvene tabele u Nabavci —
> vidi [5. Ekrani](#5-glavni-korisnički-ekrani).

---

### 13. Izveštaji i analize

**6 analiza.** Detaljno: [6.9. Nabavka](#69-nabavka--obračuni-i-analize).

| Oznaka | Naziv | Napomena |
|---|---|---|
| B-01 | Procenjena vrednost | [P-38](#10-poznati-problemi-i-ograničenja) |
| B-02 | Grupisanje UF stavki | [P-37](#10-poznati-problemi-i-ograničenja) |
| B-03 | Ključ EUF fakture | [P-39](#10-poznati-problemi-i-ograničenja) |
| B-04 | Razlike verzija plana | — |
| B-05 | Provera šifre posla partnera | — |
| B-06 | Izveštaji i alarmi | [P-36](#10-poznati-problemi-i-ograničenja) — zbir ispravljen 18.09.2026. |

---

### 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `nabavka` | **Sve funkcije modula** — usklađuje se automatski |
| `zahtev` | Kontrolna tabla, spisak i unos zahteva sa stavkama, detalj, **štampa** — bez komercijalne obrade |
| `uprava` | Sve |

> **[P]** Uloga `zahtev` **ne može** povezivati fakture, izdavati narudžbenice ni menjati
> statuse.

---

### 15. Validacije i kontrole

| Kontrola | Poruka / ponašanje |
|---|---|
| **Broj predmeta bez centra** | *„Nedostaje sifra centra za broj zahteva.“* |
| **Stavka: tip bez veze ili veza bez tipa** | *„Izaberite jedan zapis koji odgovara tipu povezivanja.“* / *„Izaberite tip povezivanja za povezani zapis.“* |
| Jedinstvenost predmeta ↔ EUF ključ | Kontrola u bazi |
| Jedinstvenost faktura ↔ šifra posla | Kontrola u bazi |
| **Garažni predmet bez vozila** | *„Izaberite vozilo za zahtev garaže.“* |
| **Predmet nije garažni** | Sistem **prazni** `vehicle`, `work_type` i `garage_order` |
| **Nalog garaže ne pripada vozilu** | *„Nalog mora pripadati izabranom vozilu.“* |
| **Vrsta intervencije ne odgovara nalogu** | *„Vrsta intervencije mora odgovarati izabranom nalogu.“* — inače se preuzima sa naloga |
| Stavka ↔ faktura | **Jedan na jedan prema stavci.** Jedna faktura može imati **više stavki i više predmeta** |
| Masovno povezivanje stavki | Pogađa **samo stavke bez izvora** (`source_type=""`); radi se kroz `update()`, **bez `full_clean()`** |
| Promena osnovne šifre posla | Stara veza se briše **ako nije vraćena**; ako jeste — prelazi u „dodatnu“ |
| Uvoz plana bez prepoznatih stavki | *„Excel ne sadrzi prepoznate stavke plana javnih nabavki.“* |
| Duplirani ključevi u planu | Prijavljuju se korisniku |
| Listovi bez zaglavlja | Preskaču se i prijavljuju |

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Predmet vezan za kvar bez sopstvenog vozila | Vrsta intervencije se preuzima sa naloga garaže |
| Otkazan predmet | **Ne prenosi** vrstu intervencije na dokument |
| Faktura dodeljena drugom vozilu | **Uklanja se** iz dokaza o održavanju tog vozila |
| **Ispravka u izvoru EUF** | **Nastaje nova faktura**, stara ostaje sa vezama |
| **UF faktura nestala iz izvora** | **Briše se, veza sa stavkom tiho nestaje** |
| Stavka bez broja fakture | Postaje zasebna UF faktura |
| Stavka plana bez rednog broja | Ključ se pravi iz **otiska naslova** |
| Stavka uklonjena pa vraćena | Status **„Dodato“**, bez veze sa izvornom |
| Pomerena stavka u Excel-u | **„Bez izmene“** — broj reda nije u otisku |
| Roba se poklapa i sa UF i sa EUF | Prikazuje se **`UF`** — vidi [B-07](#b-07--poklapanje-robe-sa-uf-ili-euf-fakturom) |
| Više od 2.000 EUF faktura u izvoru | **Višak se ne preuzima**, bez upozorenja |
| Naziv firme je prefiks druge firme | Meko poklapanje robe ih može **spojiti** |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Sadržaj pogleda `nbv_EUF_stavke`, `nbv_roba`, `nbv_sif_pos_par` | DDL |
| 2 | Postoji li u izvoru **stabilan identifikator** EUF fakture | **Q35** |
| 3 | Treba li upozorenje kada se zbir stavki razlikuje od unete vrednosti | **Q36** |
| 4 | Da li su potrebni dodatni alarmi | **Q37** |
| 5 | Kako se predmet nabavke povezuje sa knjiženjem troška | **Q3** |
| 6 | **Vrednosni pragovi nabavke** — vidi niže | **Q44** |

#### Vrednosni pragovi — poslovno pravilo kojeg u kodu nema [N]

Raniji dokument `nabavka-funkcionalnosti-i-povezivanja.md` navodio je, pod „pravila za
dalju doradu“, tri praga:

| Prag | Postupak |
|---|---|
| Do **100.000,00 RSD** | Mala nabavka |
| **100.000,00 – 1.000.000,00 RSD** | Tri ponude i obrazloženje izbora |
| Preko **1.000.000,00 RSD** | Javna nabavka |

> **[P] U kodu ne postoji nijedna provera pragova** — nema nijedne konstante `100000` ni
> `1000000` u aplikaciji `nabavka`. **Q44:** da li ovo pravilo i dalje važi i treba li ga
> sistem sprovoditi, ili se primenjuje van aplikacije?

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.9. Nabavka](#69-nabavka--obračuni-i-analize) | Svih 6 analiza |
| [4.7](#47-nabavka--nabavka) | Tabele |
| [5. Poslovni procesi](#5-poslovni-procesi) | Proces od kvara do fakture |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-36 … P-39 |

---

## 3.5. Potraživanja

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Potraživanja** |
| Tehnički naziv | Django aplikacija `potrazivanja` |
| Adresa | `/potrazivanja/` |
| Bočni meni | `sidebar_potrazivanja.html` |
| Status | **Zamenjuje nasleđenu Naplatu** |

---

### 2. Poslovna namena

Odgovara na pitanje: **ko nam duguje, koliko, koliko dugo i šta je preduzeto.**

Nasleđena Naplata je isto radila, ali **čitanjem nasleđenih pogleda pri svakom otvaranju
ekrana** — sporo i bez istorije. Potraživanja umesto toga:

1. **Preuzimaju ceo izvor** u lokalne tabele.
2. **Proveravaju** preneto sa izvorom kroz **šest kontrola**.
3. **Objavljuju snimak stanja** na tačno određeni datum.
4. Svi ekrani čitaju **objavljeni snimak**, ne izvor.

> **[P] Ključna prednost:** moguće je videti stanje **kako je izgledalo ranije**.
> Naplata to ne omogućava.

---

### 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Služba naplate** | Prati dugovanja, vodi kontakte, poziva, izdaje opomene i pozivna pisma |
| **Pravna služba** | Vodi sudske postupke, stečajeve i UPPR |
| **Finansije** | Vidi saldo kupaca po šifri posla, kroz Finansijsku analitiku |
| **Rukovodioci poslova** | Vide naplativost svog posla |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Kontrolna tabla** | Dugovanja po partnerima i starosnim razredima |
| **Detalj partnera** | Stavke, dospeća, kontakti, aktivnosti, opomene, postupci |
| **Kontakti** | Osobe i kanali (telefon, mobilni, e-pošta), sa oznakom za proveru |
| **Aktivnosti** | Napomene i telefonski pozivi, sa ishodom i sledećom radnjom |
| **Opomene i pozivna pisma** | Dokument sa stavkama, rokom za odgovor i tekstom za štampu |
| **Pravni postupci** | Tuženi, tužili, stečaj, UPPR — sa istorijom promena |
| **Sinhronizacija** | Ručno pokretanje, istorija, koraci, kontrolni zbirovi, problemi prenosa |
| **Uvoz i izvoz** | Uvoz opomena iz Excel-a, izvoz tabela |

---

### 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Kontrolna tabla** | `/potrazivanja/` |
| Detalj partnera | `/potrazivanja/partner/<id>/` |
| Oznake partnera (važan kupac, provera) | `/potrazivanja/partner/<id>/oznaki/` |
| Unos i izmena zapisa | `/potrazivanja/unos/<vrsta>/`, `/izmena/<vrsta>/<id>/` |
| Arhiviranje zapisa | `/potrazivanja/arhiva/<vrsta>/<id>/` |
| **Pravni postupak** | `/potrazivanja/postupak/<id>/` |
| Promena u postupku | `/potrazivanja/postupak/<id>/promena/` |
| **Štampa opomene** | `/potrazivanja/dokument/<id>/stampa/` |
| **Sinhronizacija** | `/potrazivanja/sinhronizacija/` |
| Izvoz | `/potrazivanja/izvoz/` |
| Uvoz opomena | `/potrazivanja/uvoz-opomena/` |

---

### 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| Oznaka „važan kupac“ i „potrebna provera“ | Služba naplate |
| Kontakti: ime, prezime, funkcija, telefon, e-pošta | Služba naplate |
| Telefonski pozivi: datum, tekst, ishod, sledeća radnja | Služba naplate |
| **Opomene i pozivna pisma**: broj, datum, primalac, iznos, tekst, rok | Služba naplate |
| Stavke opomene (fakture) | Služba naplate |
| **Pravni postupci**: sud, broj predmeta, vrednost spora, kamata, troškovi | Pravna služba |
| Promene u postupku | Pravna služba |

---

### 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Tabela |
|---|---|---|
| **Partneri** | `dbo.partneri` (firma 1, grupa 1) | `potrazivanja_financepartneridentity` |
| **Knjiženja potraživanja** | `dbo.baza`, `dbo.ispravke` | `potrazivanja_receivableposting` |
| **Fakture IF** | Izvedeno grupisanjem knjiženja | `potrazivanja_invoicedocument` |
| **Otvorene pozicije i baketi** | `dbo.dodela_baketa` | `potrazivanja_receivableposition` |
| Šifre posla i centri | `[PUTGEO-SERVER].[bazaims].dbo.posao` | u pozicije |
| Nasleđene operativne evidencije | `kontakti`, `napomene`, `opomene`, `poziv_pismo`, `pozivi_tel`, `tuzbe` | Jednokratni prenos |

> **[P] Sinhronizacija se pokreće ručno** — nije u rasporedu zakazanih poslova. Postoji
> Celery zadatak `potrazivanja.tasks.sync_collections_task`, u redu **`sync`**, ali za
> automatski rad trebalo bi uključiti **broker, radnika i Beat raspored**.

#### Centar posla — tačna šifra, nikad prefiks [P]

Centar se preuzima iz **`posao.blok` po tačnoj šifri**, sa `sif_pred=1`.

> **Centar se ne zaključuje iz prve dve cifre šifre**, i **ne uzima se** iz opšteg registra
> organizacionih jedinica — taj registar nije potpun izvor za sve šifre poslova.

Ako u izvornom šifarniku postoji duplirana ili prazna šifra posla, prenos se **prekida**
porukom *„Duplirana/prazna šifra posla u izvornom šifarniku.“* [P]

#### Obim izvornih evidencija [P]

Snimak iz vremena prenosa — **nisu trajne konstante**:

| Skup | Redova | | Skup | Redova |
|---|---|---|---|---|
| `partneri` | 13.608 | | `tabela_if` | 98.791 |
| `baza` | 10.050 | | `duplikati18` | 111.153 |
| `ispravke` | 2.395 | | kontakti | 654 |
| `v_if` | 109.761 | | napomene | 103 |
| `v_duplikati` | 2.580 | | opomene | 895 |
| `dodela_baketa` | 1.586 | | pozivna pisma | 133 |
| `v_tuzeni` | 117 | | telefonski pozivi | 2.479 |
| `v_neodobreneIF` | 160 | | stara evidencija tužbi | 32 |
| `posao` (firma 1) | 415 | | pravni postupci / promene | 127 / 379 |

> **[Z]** Zbir uključuje i poglede i njihove istorijske pomoćne tabele, pa je to broj
> **sačuvanih izvornih redova, a ne broj jedinstvenih faktura**. Isti istorijski zapis može
> postojati i u pomoćnoj tabeli i u pogledu (`v_if` = `tabela_if` + IF od 2025.).

---

### 8. Tabele i kolone

Detaljno: [4.8. Potraživanja](#48-potraživanja--potrazivanja).
**22 tabele** — najviše od svih modula.

| Grupa | Tabele |
|---|---|
| **Sinhronizacija** | `collectionsyncrun`, `collectionsyncstep`, `sourcedataset`, `sourcerow`, `legacyimportmap`, `importissue` |
| **Finansijski podaci** | `financepartneridentity`, `invoicedocument`, `receivableposting`, `duedateevidence` |
| **Snimci stanja** | `balancesnapshot`, `receivableposition`, `collectionstate`, `agingrule` |
| **Operativne evidencije** | `collectionprofile`, `collectioncontact`, `contactpoint`, `collectionactivity`, `collectionnotice`, `collectionnoticeitem` |
| **Pravni postupci** | `collectionlegalcase`, `collectionlegalevent`, `legalcaselink` |
| **Ostalo** | `electronicinvoicestatus`, `collectionaudit`, `collectionfileimport` |

#### ⚠ Dve tabele postoje, ali se nikada ne pune [P]

| Tabela | Stanje |
|---|---|
| `duedateevidence` | Model postoji i `sync.py` ga uvozi, ali ga **nigde ne kreira** — jedini `objects.create` je u testovima. Pozicije dobijaju `due_date_method="legacy_views"` i dospeće **direktno iz `dodela_baketa`**. Nezavisan obračun dospeća **nije uveden**. |
| `electronicinvoicestatus` | Model postoji, ali ga **nijedna servisna funkcija ne kreira**. Ekran „Neodobrene IF“ čita **arhivirane redove `SourceRow`** skupa `v_neodobreneIF`, ne ovaj model. |

> **[Z] Zašto je to važno:** ko gleda samo spisak tabela pomisliće da sistem vodi zasebne
> dokaze o dospeću i istoriju SEF statusa. **Ne vodi ih.**

`duedateevidence` je pripremljen za istorijske tabele **bez primarnog ključa** — ima polje
`occurrence` i ograničenje `UniqueConstraint(import_run, source_table, source_key,
occurrence)`, da bi se ponovljeni identični redovi mogli sačuvati i prebrojati. [P]

#### Skupovi koji postoje samo kao arhivirani izvor [P]

`v_tuzeni`, `tabela_if`, `duplikati18`, `sif_baket` i `sif_kategorija` čitaju se i čuvaju u
`SourceDataset` / `SourceRow`, ali **nemaju sopstvene poslovne modele**. Ekran „Utuženi
klijenti“ čita `SourceRow` skupa `v_tuzeni`.

---

### 9. SQL pogledi

Redovna sinhronizacija čita **13 finansijskih izvora**, ne pet. [P]

| Pogled | Uloga i zavisnosti | DDL |
|---|---|---|
| `partneri` | Udaljeni `BazaIMS.partner` + `Gruppartner`; **sve grupe**, ne samo grupa 1 | [✔](#prilog-b--ddl-nasleđenih-sql-pogleda) |
| `baza` | Udaljeni `nalog_z` + `partneri`; firma 1, grupa 1, konta `20400%`/`20500%`; godišnji izbor i `POC` | [✔](#prilog-b--ddl-nasleđenih-sql-pogleda) |
| `v_if` | IF **od 2025.** iz udaljenog `nalog_z` + `UNION ALL tabela_if`; **izvor dospeća** | [✔](#prilog-b--ddl-nasleđenih-sql-pogleda) |
| `v_duplikati` | IF iz **svih** godina + `duplikati18`; partner/veza u više godina i **MAX dospeća** | ⚠ sumnjiv |
| `dodela_baketa` | `baza` + prethodna dva; saldo, dospeće, starost i domaće/ino | [✔](#prilog-b--ddl-nasleđenih-sql-pogleda) |
| `ispravke` | Udaljeni `nalog_z` + `konto` + `partneri`; konta `2049%`, `2059%`, `2048%`, `2058%` | [✔](#prilog-b--ddl-nasleđenih-sql-pogleda) |
| `v_tuzeni` | Udaljeni `nalog_z` + `konto` + `partneri`; `2048%`/`2058%`, `promena='O'` | [✔](#prilog-b--ddl-nasleđenih-sql-pogleda) |
| `v_neodobreneIF` | `EFaktura.EDok` + `EStatusIZ` + `BazaIMS.partner` | **nema** |
| `tabela_if`, `duplikati18` | Istorijske pomoćne tabele (2006–2024, 2006–2020) | — |
| `sif_baket`, `sif_kategorija` | Šifarnici razreda i kategorija | — |
| `posao` | Šifre posla i centri (`blok`), `sif_pred=1` | — |

Definicije sedam pogleda nalaze se u
[Prilogu B — DDL nasleđenih pogleda](#prilog-b--ddl-nasleđenih-sql-pogleda), zajedno sa
dve granice tog ispisa. [P]

#### `v_neodobreneIF` — jedini opis koji postoji [N]

Tog pogleda **nema u preuzetom DDL-u**. Pravila su poznata samo posredno, iz ranijeg plana
Naplate:

> Datum dokumenta **od 2025.**, `sif_dok=50`, `StatusIz=20` i status **različit od
> `Approved`**. To je **podskup poslatih faktura**, ne kompletna istorija SEF statusa.

| Napomena | |
|---|---|
| Pravi ključ izvora | **`EDok.ID`** |
| Izvedeni prikaz broja fakture | `SUBSTRING(EID,5,20)` — **nije pouzdan identifikator** |
| Faktura nestala iz pogleda | Može biti odobrena, obrisana **ili van filtera** — odsustvo **nije dokaz** statusa `Approved` |

Kolone koje aplikacija koristi: `oj`, `god`, `datum`, šifra i naziv partnera, `faktura`,
`Status na sefu`, `vreme statusa`, `komentar`. [P]

#### Godišnji obuhvat se razlikuje po pogledu [P]

Posle **30. aprila** `baza` čita **tekuću** godinu, a `ispravke`, `v_duplikati` i `tuzeni`
**prethodnu** — to je **potvrđeno poslovno pravilo**, ne greška. Modul to beleži odvojeno,
u `run.scope["baza_years"]` i `run.scope["ispravke_years"]`.

> **[Z] Rizik svežine:** procedura `sp_AzurirajNalogZ` posle aprila osvežava **tekuću**
> godinu, a `ispravke` tada traže **prethodnu**. Ako se prethodna godina ne osvežava
> zasebno, **stara lokalna kopija nije dokaz svežine**.

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`potrazivanja/models.py`](../potrazivanja/models.py) |
| **Sinhronizacija i kontrole** | [`services/sync.py`](../potrazivanja/services/sync.py) |
| Čitanje izvora | [`services/source.py`](../potrazivanja/services/source.py) |
| Saldo po šiframa posla | [`services/reports.py`](../potrazivanja/services/reports.py) |
| **Normalizacija kontakata** | [`services/contacts.py`](../potrazivanja/services/contacts.py) |
| Prenos operativnih evidencija | [`services/operations.py`](../potrazivanja/services/operations.py) |
| Osamostaljivanje | [`services/independence.py`](../potrazivanja/services/independence.py) |
| Prava pristupa | [`potrazivanja/access.py`](../potrazivanja/access.py), [`permissions.py`](../potrazivanja/permissions.py) |

Testovi: **59 testova** u 5 fajlova, uključujući **proveru brzine čitanja**. [P]

---

### 11. Ulazni i izlazni podaci

| Smer | Šta |
|---|---|
| **Ulaz** | Nasleđeni pogledi; Excel uvoz opomena |
| **Izlaz** | Štampa opomena i pozivnih pisama; izvoz tabela; **saldo po šiframa posla Finansijama** |

---

### 12. Veze sa drugim modulima

| Modul | Veza |
|---|---|
| **Finansije** | Tab „Potraživanja“ na kartici posla — `job_balances()` |
| **Ugovori** | `FinancePartnerIdentity.partner` → `ugovori_partner` |
| **Naplata** *(nasleđeno)* | Jednokratni prenos operativnih evidencija i pravnih postupaka |

---

### 13. Izveštaji i analize

**6 analiza.** Detaljno: [6.8. Potraživanja](#68-potraživanja--obračuni).

| Oznaka | Naziv |
|---|---|
| PT-01 | Starosni razredi (7 baketa) — [P-35](#10-poznati-problemi-i-ograničenja) |
| PT-02 | Saldo stavke |
| PT-03 | Objavljivanje snimka stanja |
| **PT-04** | **Šest kontrolnih zbirova** |
| PT-05 | Saldo po šiframa posla |
| PT-06 | Normalizacija nasleđenih kontakata |

---

### 14. Uloge i prava pristupa

Modul ima **sopstveni sistem dozvola** (`potrazivanja/permissions.py`), uz uobičajeni. [P]

Ukupno **21 dozvola** [P]:

| Grupa | Dozvole |
|---|---|
| Pregled | `dashboard`, `partner_detail`, `table_data`, `sync_status` |
| **Obuhvat** | **`view_all`** — ceo obuhvat firme |
| Izlaz | `export`, `print` |
| Unos | `review_update`, `notice_import` |
| Operativni rad | `contact_*`, `activity_*`, `notice_*`, `legal_*` — svaki sa `create`, `update`, `archive` |

Korisnik bez `view_all` vidi samo **dozvoljene centre i šifre posla** (`scoped()`).
Pristup šifri posla se proverava **dvaput** — pri ulasku i pri filtriranju pozicija. [P]

> **[P] Dva ekrana su ograničenom korisniku potpuno nedostupna:** „Neodobrene IF“ (SEF) i
> „Utuženi klijenti“. Bez `view_all` dižu poruku *„Izveštaj nema raspodelu po šiframa
> posla.“* — jer se ti izvori ne mogu podeliti po šifri posla.

> **[P] Obuhvat se određuje serverski**, u svakoj listi, detalju, AJAX zahtevu i izvozu —
> **nezavisno od ulaznog URL-a**. Stari obrazac iz Naplate, gde je `?report=1` menjao
> vidljive šifre, **namerno nije prenet**.

#### Kako su prenete stare dozvole Naplate [P]

| Stara dozvola | Nova |
|---|---|
| `naplata:lista_dugovanja_po_bucketima` | `view_all` — **osim za ulogu `pregled-naplate`** |
| `naplata:toggle_avans_klijent` | `review_update` |
| `notice_create` | Automatski dodaje i `notice_import` |

Provereno za uloge `uprava`, `pravna` i `pregled-naplate`: sve imaju pristup novoj
aplikaciji, a stara prava su ostala očuvana. Prenos je **ponovljiv** i deo redovnog
usklađivanja dozvola. [P]

---

### 15. Validacije i kontrole

> **Ovaj modul ima najviše kontrola u celom sistemu.** [Z]

| Kontrola | Gde |
|---|---|
| **Saldo = duguje − potražuje** | **Kontrola u bazi** (`CheckConstraint`) |
| Objavljen snimak mora imati vreme objave | Kontrola u bazi |
| Aktivno stanje mora biti **objavljen** snimak iste firme | `CollectionState.clean()` |
| Partner i dokument iste firme | `InvoiceDocument.clean()` |
| Knjiženje odgovara izvornom ključu partnera | `ReceivablePosting.clean()` |
| Faktura opomene pripada partneru opomene | `CollectionNoticeItem.clean()` |
| SEF dokument odgovara firmi i partneru | `ElectronicInvoiceStatus.clean()` |
| **Šest kontrolnih zbirova pre objave** | `publish_positions()` |
| **Baket izvora odgovara datumu snimka** | `publish_positions()` |
| Duplirani ključ pozicije | *„bez tihog spajanja“* |
| Prazan osnovni izvor | *„postojeći podaci ostaju objavljeni“* |
| Zaključavanje sinhronizacije | `sp_getapplock`, vezano za sesiju |
| **Lokalne izmene se ne prepisuju** | Ponovni uvoz beleži `local_profile_conflict` / `local_edit_conflict` — *„Lokalna izmena je zadržana. Nova izvorna verzija je u arhivi.“* |
| Ponovni uvoz posle osamostaljenja | **Odbija se:** *„Potraživanja već samostalno vode operativne podatke. Ponovni uvoz iz Naplate je isključen.“* |
| Ponovljeni uvoz iste Excel datoteke | Sprečen otiskom (`fingerprint`) |

> **[P] Ko šta menja:** izvorna finansijska polja menja **sinhronizacija**; kontakte,
> aktivnosti, oznake i opomene menja **korisnik**. Ponovni uvoz **ne sme izbrisati
> korisnički rad** — zato se sukobi beleže, a lokalna verzija zadržava.

#### Osamostaljenje [P]

Početni prenos završava komanda **`initialize_potrazivanja`**, i to **samo jednom**.
Trenutak se upisuje u **`CollectionState.operations_independent_at`**. Posle toga
`include_legacy=True` se **odbija**.

#### Uvoz opomena iz Excel-a [P]

| Osobina | Pravilo |
|---|---|
| **Obavezne kolone** | `sif_par`, `datum`, `iznos` |
| Opcione kolone | `naz_par`, `god`, `br_opomene`, `fakture`, `napomene` |
| Prihvaćeni sinonimi zaglavlja | `sifra`, `šifra`, `sifra partnera`, `naziv`, `godina`, `broj`, `broj opomene`, `napomena` |
| Valuta | Uvek **RSD** |
| Pre upisa | Prikazuje se **pregled** |
| Greška u bilo kom redu | **Sprečava ceo upis** |
| Isti fajl dvaput | Sprečeno otiskom, zapis u `CollectionFileImport` |

Izvoz poštuje **isti obuhvat i filtere kao lista**, sa zbirom **celog filtriranog skupa**,
ne samo prikazanih 100 redova. Tekst iz izvora **se ne izvozi kao Excel formula**. [P]

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| **Nepoznato dospeće** | Svrstava se u **„Nedospelo“** ([P-35](#10-poznati-problemi-i-ograničenja)) |
| Partner u finansijskim podacima bez šifarnika | Upisuje se **neaktivan**, uz zabeležen problem |
| Nestalo knjiženje | `active = False`, uz napomenu da to **nije dokaz brisanja iz ERP-a** |
| Bilo koja kontrola ne prođe | **Ništa se ne upisuje**, prethodni snimak ostaje |
| Prekinut prethodni prolaz | Automatski se označava kao neuspešan |
| Nasleđeni kontakt sa više osoba | Razdvaja se, uz oznaku **„Potrebna provera“** |
| Nema objavljenog snimka | Prazan rezultat, **ne greška** |
| **Stavka bez centra u izvornom šifarniku** | Prikaz **„Neraspoređeno“** — centar se ne nagađa |
| Zatvorena pozicija (saldo nula) | **Ne prikazuje se** kao otvorena stavka; dokumenti i aktivnosti ostaju |
| Negativan saldo | **Zadržava se** — ne pretvara se u nulu i ne uklanja kao greška |

#### Zatečene stavke za proveru pri prenosu [P]

Nijedan od ovih zapisa **nije odbačen**:

| Oblast | Broj | Postupanje |
|---|---|---|
| Kontakti bez potvrđene veze sa partnerom | **32** | Sačuvan original i novi nepovezan kontakt |
| Napomene bez potvrđene veze | **13** | Sačuvan original i nova nepovezana aktivnost |
| Opomene bez potvrđene veze | **16** | Sačuvan original i nova nepovezana opomena |
| Pravni postupci bez potvrđene veze | **4** | Ostali u postojećoj tabeli i arhivi |
| Otvorene stavke **bez dospeća** | **9** | Izvorni `NULL` ostao `NULL`; saldo **−310.678,54 RSD** |
| Otvorena stavka **bez centra** | **1** | „Neraspoređeno“; saldo **318.352,18 RSD**, uključena u ukupno |

Prvih 65 problema vidi se na ekranu sinhronizacije. Stavke bez dospeća radi uporedivosti
ostaju u razredu `0.1`, a zbirna kartica ih **prikazuje zasebno**. [P]

#### Nalazi o kvalitetu izvornih podataka [P]

| # | Nalaz |
|---|---|
| 1 | `partneri` ima **13.607 redova i 13.588 različitih `sif_par`** — **sama šifra nije globalni ključ**. Nove veze moraju čuvati **pun finansijski identitet** (firma + grupa + šifra) |
| 2 | `ugovori.Partner` ima **13.406** partnera; `external_sif_par` **nije jedinstveno ograničeno** i ne sadrži firmu/grupu — **ne povezivati slepo samo po broju** |
| 3 | **32 kontakta, 13 napomena i 16 opomena** nemaju odgovarajućeg partnera; kod 32/13/3 od njih šifra je `NULL` ili necelobrojna. Čuvaju se za **ručno** povezivanje — **ne po sličnom nazivu** |
| 4 | `tabela_if` ima **7.424**, a `duplikati18` **6.105** redova **bez dospeća**. To je kvalitet **pomoćne istorije**, ne broj današnjih faktura bez dospeća |
| 5 | U `nalog_z` **nema dupliranih ključeva** firma/godina/vrsta/broj/stavka. Pregled metapodataka **nije pokazao indekse** na `nalog_z` i dvema istorijskim tabelama |
| 6 | Stare operativne tabele koriste **`float` za šifre i iznose**, a fakture u opomenama su **tekst**. Novi iznosi koriste `Decimal`, veze su FK. Original se **čuva** (`original_invoice_text`) |
| 7 | `tabela_if.saldo` je `numeric(38,2)`. Izmereni najveći iznos staje u `decimal(18,2)`, ali uvoz **proverava opseg** umesto prećutnog sužavanja — `DueDateEvidence.legacy_balance` je `decimal(38,2)` |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Sadržaj pogleda `baza`, `ispravke`, `dodela_baketa` | DDL |
| 2 | Da li „Nedospelo“ treba razdvojiti od „Nepoznato dospeće“ | **Q33** |
| 3 | **Datum gašenja nasleđene Naplate** | **Q34** |
| 4 | Da li sinhronizacija treba da bude zakazana | **[N]** |
| 5 | Da li pravna služba u celini prelazi u Potraživanja | **Q12** |
| 6 | **Definicija `v_duplikati` u preuzetom DDL-u je sumnjiva** — vidi niže | **[N]** |
| 7 | Tačno ponašanje granice „119 dana“ oko 29/30.04. i u prestupnoj godini | **[N]** |

#### Zašto je definicija `v_duplikati` sumnjiva [Z]

U preuzetom DDL-u `ispravke` i `v_duplikati` imaju **doslovno isti tekst**. To ne može biti
tačno: pri prenosu `ispravke` je dalo **2.395**, a `v_duplikati` **2.580** redova.

Raniji plan Naplate opisuje `v_duplikati` sasvim drugačije — **IF iz svih godina spojen sa
`duplikati18`, uz `MAX` dospeća**. **Definiciju treba ponovo preuzeti iz baze.**

#### Šta blokira gašenje nasleđene Naplate (Q34) [P]

| Prepreka | Opis |
|---|---|
| **Menice** | Izbor partnera čita SQL pogled `partneri` |
| **Ugovori** | Uvoz postojećeg registra čita **isti pogled** |
| **Migracije** | Istorijska migracija `0001` još ima zavisnost od migracije Naplate. `0005` je uklonila samu vezu iz aktivne šeme, ali potpuno uklanjanje aplikacije iz projekta traži **sređivanje istorije migracija** |

> **SQL poglede ne brisati dok ih koriste Menice i Ugovori.** [P]

#### Tri evidencije tužbi nisu ista stvar [P]

| Izvor | Gde završava |
|---|---|
| Stare `tuzbe` | `CollectionNotice(kind="legacy_claim")` |
| Knjigovodstveni `v_tuzeni` | **Samo arhivirani izvor** (`SourceRow`) |
| Pravni `postupak` | `CollectionLegalCase` / `LegalCaseLink` |

> **Ne smeju se automatski spojiti po partneru.** [P]

> **[P] Finansijski identitet nije novi registar partnera** — čuva izvorni ključ i mapira ga
> na postojeći `ugovori.Partner`. **Ne prepisuje** APR-proverene ni ručno održavane podatke
> tog registra. Podudaranje po PIB/MB je **kandidat za proveru, ne automatski dokaz**.

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.8. Potraživanja](#68-potraživanja--obračuni) | Svih 6 analiza |
| [4.8](#48-potraživanja--potrazivanja) | 22 tabele |
| [11. Plan razvoja](#11-plan-razvoja) | Prelazak sa Naplate |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-18, P-35 |

---

## 3.6. Ugovori i partneri

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Ugovori** |
| Tehnički naziv | Django aplikacija `ugovori` |
| Adresa | `/ugovori/` |
| Bočni meni | `sidebar_ugovori.html` |

---

### 2. Poslovna namena

Vodi **poslovni odnos sa partnerom od prvog zahteva do isteka ugovora**:

> zahtev → ponuda → ugovor → aneksi → dokumenta → sredstva obezbeđenja

Uz to je **centralni šifarnik partnera** za ceo sistem — Nabavka, Potraživanja i Menice
koriste iste partnere.

---

### 3. Korisnici modula

| Korisnik | Šta radi | Uloga |
|---|---|---|
| **Pravna služba** | Vodi ugovore, anekse, garancije, veze sa menicama | `pravna` |
| **Sekretarijat** | Evidentira zahteve i ponude | `pravna` (dodeljeno) |
| **Služba nabavke** | Bira dobavljača i ugovor uz predmet nabavke | `nabavka` |
| **Komercijala** | Prati ponude i zahteve | **[N]** |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Partneri** | Pravna lica, fizička lica, banke; domaći i strani; **provera u APR-u** |
| **Zahtevi** | Ispitivanje, usluga, izlazak na teren, konsultacija, ostalo |
| **Ponude** | Naša ponuda i ponuda data nama; vrednost, valuta, rok važenja |
| **Ugovori** | Glavni ugovor i aneksi; tip, vrednost, period, status |
| **Dokumenta** | Prilozi uz ugovor, sa originalnim nazivom datoteke |
| **Stranke** | Ko je kupac, prodavac, zakupac, izvođač, garant… |
| **Garancije** | Bankarske garancije sa periodom i statusom |
| **Veze sa menicama** | Ugovor ↔ menica (izlazna ili ulazna) |

#### Tipovi vrednosti ugovora [P]

`fixed` (fiksna), `hourly` (po radnom satu), `monthly` (mesečno),
`man_month` (čovek mesec), `unit` (po jedinici), `undefined` (bez definisane vrednosti).

---

### 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Partneri** | `/ugovori/partneri/` |
| Detalj partnera | `/ugovori/partneri/<id>/` |
| **Provera partnera u APR-u** | `/ugovori/partneri/<id>/apr-update/` |
| Paketna APR provera | `/ugovori/partneri/sync-apr/start/` |
| **Sinhronizacija iz Finansija** | `/ugovori/partneri/sync-finansije/` |
| Tipovi ugovora | `/ugovori/tipovi/` |
| Zahtevi | `/ugovori/zahtevi/` |
| Ponude | `/ugovori/ponude/` |
| **Ugovori** | `/ugovori/` |
| Detalj ugovora | `/ugovori/<id>/` |
| **Novi aneks** | `/ugovori/<id>/aneks/novi/` |
| Dokumenta uz ugovor | `/ugovori/<id>/dokumenti/dodaj/` |
| Menice uz ugovor | `/ugovori/<id>/menice/dodaj/` |
| Garancije uz ugovor | `/ugovori/<id>/garancije/dodaj/` |
| Štampa spiska | `/ugovori/stampaj/` |
| Izvoz u Excel | `/ugovori/export-excel/` |

---

### 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| Partner: naziv, tip, rezidentnost, PIB, matični broj, JMBG, adresa, kontakt | Pravna služba |
| Zahtev: broj, datum, tip, predmet, centar, status, fajl | Sekretarijat |
| Ponuda: broj, datum, smer, tip, vrednost, valuta, rok važenja, status | Sekretarijat |
| **Ugovor: broj, naslov, predmet, datumi, vrednost, tip vrednosti, valuta, status** | Pravna služba |
| Aneks uz glavni ugovor | Pravna služba |
| Dokumenta uz ugovor | Pravna služba |
| Stranke i njihove uloge | Pravna služba |
| Garancije | Pravna služba |
| Veze sa menicama | Pravna služba |

---

### 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| **Partneri** | `dbo.partneri` (nasleđeni šifarnik) | **Ručno**, paketno |
| **Status u APR-u i poslovno ime** | `openapi.apr.gov.rs` | **Ručno** |

---

### 8. Tabele i kolone

Detaljno: [4.9. Ugovori](#49-ugovori--ugovori). **8 tabela.**

| Tabela | Uloga |
|---|---|
| `ugovori_partner` | Partner; veza sa starim sistemom je `external_sif_par` |
| `ugovori_contract_type` | Šifarnik tipova ugovora |
| `ugovori_business_request` | Zahtev |
| `ugovori_offer` | Ponuda |
| **`ugovori_contract`** | Ugovor i aneks (`kind`, `parent_contract`) |
| `ugovori_contract_document` | Dokument uz ugovor |
| `ugovori_contract_party` | Stranka ugovora |
| `ugovori_contract_guarantee` | Garancija |
| `ugovori_contract_menica_link` | Veza sa menicom |

---

### 9. Spoljni izvori

| Izvor | Namena | Status |
|---|---|---|
| `dbo.partneri` | Šifarnik partnera | Kolone poznate |
| **`https://openapi.apr.gov.rs/api/opendata/companies`** | Status privrednog subjekta | Javni skup, bez prijave |

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`ugovori/models.py`](../ugovori/models.py) |
| **Sinhronizacija partnera** | [`ugovori/services.py`](../ugovori/services.py) |
| **APR provera** | [`ugovori/apr_openapi.py`](../ugovori/apr_openapi.py) |
| Ekrani | [`ugovori/views.py`](../ugovori/views.py) |
| Uvoz ugovora iz Excel-a | `management/commands/import_contracts_excel.py` |

---

### 11–12. Ulaz, izlaz i veze sa modulima

| Modul | Veza |
|---|---|
| **Nabavka** | Partner kao dobavljač; osnovni i kupovni ugovor uz predmet |
| **Flota** | Ugovor o lizingu (`Lease.contract`), ugovor o finansiranju (`VehicleHolding.financing_contract`) |
| **Mobilni** | Ugovor uz paket (`MobilePackage.contract`) |
| **Menice** | Veza ugovora i menice |
| **Potraživanja** | `FinancePartnerIdentity.partner` → partner |

Izlaz: štampa spiska ugovora, izvoz u Excel.

---

### 13. Izveštaji i analize

| Oznaka | Naziv | Poglavlje |
|---|---|---|
| U-01 | Provera statusa partnera u APR-u | [6.11](#611-ugovori-i-menice--analize) |
| U-02 | Sinhronizacija partnera iz finansija | [6.11](#611-ugovori-i-menice--analize) |
| U-04 | Povezivanje menica i garancija | [6.11](#611-ugovori-i-menice--analize) |

---

### 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `pravna` | **Sve funkcije modula** |
| `nabavka` | Čita partnere i ugovore kroz svoj modul |
| `uprava` | Sve |

> **[P]** Uloga `pravna` se pri sinhronizaciji dozvola **samo dopunjava**, ne usklađuje —
> ručno dodate dozvole joj ostaju.

---

### 15. Validacije i kontrole

| Kontrola | Poruka |
|---|---|
| Domaće pravno lice bez PIB-a i matičnog broja | *„Domaće pravno lice treba da ima PIB i/ili matični broj.“* |
| Domaće fizičko lice bez JMBG-a | *„Domaće fizičko lice treba da ima JMBG.“* |
| **Aneks bez glavnog ugovora** | *„Aneks mora imati glavni ugovor.“* |
| **Glavni ugovor sa nadređenim** | *„Glavni ugovor ne sme imati nadređeni ugovor.“* |
| Nadređeni koji nije glavni | *„Nadređeni ugovor mora biti tipa 'Glavni ugovor'.“* |
| Ugovor sam sebi nadređen | Odbija se |
| „Važi do“ pre „Važi od“ | Odbija se |
| Ponuda: „Vazi do“ pre datuma ponude | Odbija se |
| **Veza sa menicom: ni jedna ni obe** | *„Izaberite tacno jednu menicu.“* |
| Garancija: „Vazi do“ pre „Vazi od“ | Odbija se |
| Brisanje povezane menice | **Zabranjeno** (`PROTECT`) |
| Jedinstvenost stranke | `(ugovor, partner, uloga)` |

**Datoteke [P]:** stara datoteka se briše tek **posle potvrde transakcije**;
najveća veličina je **50 MB** (`MAX_CONTRACT_UPLOAD_SIZE`).

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Partner u više grupa u izvoru | Bira se red po **prvenstvu grupa** (1 → 10 → 11/13/14 → ostalo) |
| Partner obrisan iz izvora | **Ostaje** u evidenciji |
| Partner bez matičnog broja | APR provera ga **preskače** |
| Partner nije u APR-u | **Ništa se ne menja** — odsustvo nije dokaz gašenja |
| **Status različit od `активан`** | **Partner postaje neaktivan** ([P-40](#10-poznati-problemi-i-ograničenja)) |
| Zahtev ili ponuda bez partnera | Koristi se slobodan tekst `external_partner_name` |
| Ista menica na više ugovora | **Dozvoljeno** |
| Oznake „ima menice / garancije“ | **Ručne** — ne usklađuju se automatski |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Koje sve vrednosti statusa vraća APR | **Q38** |
| 2 | Treba li APR provera da bude zakazana | **Q39** |
| 3 | Treba li oznake na ugovoru automatski usklađivati | **Q40** |
| 4 | Ko sve koristi modul (komercijala?) | **Q2** |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.11](#611-ugovori-i-menice--analize) | Analize Ugovora i Menica |
| [3.7. Menice](#37-menice) | Povezani modul |
| [4.9](#49-ugovori--ugovori) | Tabele |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-40 |

---

## 3.7. Menice

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Menice** |
| Tehnički naziv | Django aplikacija `menice` |
| Adresa | `/menice/` |
| Bočni meni | `sidebar_menice.html` |

> **[P] Zamka:** tabele se zovu **`menica`** i **`ulazna_menica`** — **bez prefiksa
> aplikacije**.

---

### 2. Poslovna namena

Vodi evidenciju **sredstava obezbeđenja u obliku menica**:

| Vrsta | Značenje |
|---|---|
| **Izlazne menice** | Menice koje je **IMS izdao** — obaveza IMS-a |
| **Ulazne menice** | Menice koje je IMS **primio od partnera** — obezbeđenje za IMS |

Za izlazne menice podaci se mogu **preuzeti iz Registra menica NBS**, umesto ručnog
prepisivanja.

---

### 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Finansije** | Prate obaveze po izdatim menicama, vode fizičku lokaciju |
| **Pravna služba** | Povezuju menice sa ugovorima |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Izlazne menice** | Podaci iz registra NBS + ručne dopune (broj ugovora, OJ, lokacija, napomena) |
| **Ulazne menice** | Sopstvena evidencija sa jedinicom vrednosti |
| **Preuzimanje iz NBS** | Pretraga registra po PIB-u dužnika, sa avalistima |
| **Uvoz iz Excel-a** | Za ulazne i izlazne menice |
| **Fizička lokacija** | Centar ili blagajna |
| **Interni status** | Aktivna, obrisana, nepoznat |

---

### 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| Spisak menica po vrsti | `/menice/<vrsta>/` (`izlazna` ili `ulazna`) |
| Detalj menice | `/menice/<vrsta>/<id>/` |
| Nova menica | `/menice/<vrsta>/nova/` |
| **Ažuriranje iz registra NBS** | `/menice/izlazna/azuriraj/` |
| **Ulazne menice** | `/menice/ulazne/` |
| Nova ulazna menica | `/menice/ulazne/nova/` |

---

### 6. Podaci koje korisnik unosi

#### Izlazne menice — ručne dopune [P]

| Podatak | Napomena |
|---|---|
| Broj i datum ugovora | Veza sa poslovnim osnovom |
| Organizaciona jedinica | |
| **Fizička lokacija** | **Centar** ili **blagajna** |
| Napomena | |
| **Interni status** | Aktivna / obrisana / nepoznat |

> **[P] Ove dopune preuzimanje iz NBS-a NE prepisuje** — ažuriraju se samo polja
> koja dolaze iz registra.

#### Ulazne menice — sve unosi korisnik [P]

Serijski broj, osnov izdavanja, datum prijema, **jedinica vrednosti**, iznos,
partner, broj i datum našeg ugovora, ugovor važi do, lokacija, šifra centra.

---

### 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| **Izlazne menice** | `https://webappcenter.nbs.rs/PnWebApp` | **Ručno** |

Preuzima se 20 polja: dužnik, serijski broj, datumi, iznos i valuta, izdavalac, vrsta,
osnov izdavanja, banka, status i **avalisti**.

---

### 8. Tabele i kolone

Detaljno: [4.10. Menice](#410-menice--menice). **2 tabele.**

| Tabela | Uloga | Ključ prepoznavanja |
|---|---|---|
| **`menica`** | Izlazne i ulazne menice iz registra | serijski broj + datum registracije (+ redni broj) |
| **`ulazna_menica`** | Ulazne menice, sopstvena evidencija | serijski broj |

---

### 9. Spoljni izvori

| Izvor | Način | Rizik |
|---|---|---|
| **Registar menica NBS** | Razlaganje HTML stranice (`requests` + `BeautifulSoup`) | **Promena stranice zaustavlja preuzimanje** ([P-41](#10-poznati-problemi-i-ograničenja)) |

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`menice/models.py`](../menice/models.py) |
| **Preuzimanje iz NBS** | [`menice/scraper.py`](../menice/scraper.py) |
| Obrada i uvoz | [`menice/services.py`](../menice/services.py) |
| Ekrani | [`menice/views.py`](../menice/views.py) |
| Uvoz iz Excel-a | `management/commands/import_ulazne_menice_excel.py`, `import_izlazne_menice_excel.py` |

> **[P] Modul uopšte nema direktorijum `migrations/`.** Modeli **nisu** označeni sa
> `managed = False`, pa Django očekuje da njima upravlja — ali bez migracija ih **ne može
> stvoriti**. Tabele `menica` i `ulazna_menica` su nastale izvan uobičajenog postupka.
> Vodi se kao problem **[P-45](#p-45--modul-menice-nema-migracije)**.

---

### 11–12. Ulaz, izlaz i veze

| Smer | Šta |
|---|---|
| **Ulaz** | Registar NBS; Excel uvoz; ručni unos |
| **Izlaz** | Spiskovi na ekranu |

| Modul | Veza |
|---|---|
| **Ugovori** | `ContractMenicaLink` — veza ugovora i menice; brisanje povezane menice je **zabranjeno** |

---

### 13. Izveštaji i analize

| Oznaka | Naziv | Poglavlje |
|---|---|---|
| U-03 | Preuzimanje menica iz registra NBS | [6.11](#611-ugovori-i-menice--analize) |
| U-04 | Povezivanje menica sa ugovorima | [6.11](#611-ugovori-i-menice--analize) |

---

### 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `menice` | **Samo ovaj modul** — usklađuje se automatski |
| `pravna` | Povezivanje sa ugovorima (kroz modul Ugovori) |
| `uprava` | Sve |

---

### 15. Validacije i kontrole

| Kontrola | Ponašanje |
|---|---|
| Zapis bez serijskog broja ili datuma registracije | **Preskače se** pri preuzimanju |
| Prepoznavanje postojeće menice | Serijski broj + datum registracije (+ redni broj) |
| **Ručni podaci** | **Ne prepisuju se** pri preuzimanju |
| Decimalni zapis iznosa | Prepoznaju se **oba** oblika (`1.234,56` i `1,234.56`) |
| Datumi | Oblici `DD.MM.GGGG`, `DD/MM/GGGG`, `GGGG-MM-DD` |
| Brisanje povezane menice | **Zabranjeno** |

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| **Jedinica vrednosti = `PROCENAT`** | **Iznos nije novčani** — sabiranje kolone bez provere jedinice daje besmislen zbir |
| Menica uklonjena iz registra | **Ostaje** u evidenciji; koristi se interni status |
| Dve menice sa istim ključem | Uzima se **prva po ID-u** |
| Promena izgleda stranice NBS-a | Preuzimanje prestaje da radi |
| PIB nije zadat | Koristi se **podrazumevani PIB IMS-a iz koda** |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Treba li preuzimanje iz NBS-a da bude zakazano | **Q39** |
| 2 | **Kako su nastale tabele `menica` i `ulazna_menica` bez migracija** | **Q44** / [P-45](#10-poznati-problemi-i-ograničenja) |
| 3 | Ko i kada menja fizičku lokaciju menice | **[N]** |
| 4 | Šta znači „ulazna menica“ u tabeli `menica` naspram tabele `ulazna_menica` | **Q45** |

> **[N] Q45:** model `Menica` ima vrstu `ulazna`, a postoji i **zasebna tabela**
> `ulazna_menica` sa drugačijim skupom polja. Nije zabeleženo kada se koja koristi.

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.11](#611-ugovori-i-menice--analize) | U-03 i U-04 |
| [3.6. Ugovori](#36-ugovori-i-partneri) | Povezani modul |
| [4.10](#410-menice--menice) | Tabele |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-41 |

---

## 3.8. Mobilna telefonija

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Mobilni** / „Mobilni telefoni“ |
| Tehnički naziv | Django aplikacija `mobilni` |
| Adresa | `/mobilni/` |
| Bočni meni | `sidebar_mobilni.html` |

---

### 2. Poslovna namena

Zaposleni dobija službeni broj telefona sa paketom koji plaća poslodavac.
**Sve iznad paketa zaposleni plaća sam.** Modul odgovara na pitanje:
**koliko se kome obustavlja od zarade za mobilni telefon.**

> **Rezultat ovog modula ide u obračun zarada** — jedan od tri takva u sistemu.

---

### 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Administracija** | Uvozi mesečne datoteke operatera, održava izuzetke od parkinga, povezuje brojeve sa zaposlenima |
| **Obračun zarada** | Preuzima CSV sa iznosima obustava |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Paketi** | Naziv, period važenja, **neto i bruto iznos**, veza sa ugovorom |
| **Korisnici mobilnih** | Šifra radnika, ime, JMBG, datum odlaska, **status veze** sa zaposlenim |
| **Dodele brojeva** | Koji broj kome pripada, **po mesecu** |
| **Potrošnja** | 25 kolona iz računa operatera, **po mesecu** |
| **Izuzeci od parkinga** | Brojevi kojima se parking ne obustavlja |
| **Obustave** | Četiri izveštaja + CSV za obračun zarada |
| **Uvoz** | Četiri odvojena uvoza, sa dnevnikom |

---

### 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| Kontrolna tabla | `/mobilni/` |
| **Uvoz podataka** | `/mobilni/import/` |
| Paketi | `/mobilni/paketi/` |
| Korisnici | `/mobilni/korisnici/` |
| **Dodele brojeva** | `/mobilni/dodele/` |
| **Potrošnja** | `/mobilni/potrosnja/` |
| Detalj broja telefona | `/mobilni/brojevi/<broj>/` |
| Izuzeci od parkinga | `/mobilni/parking-izuzeci/` |
| **Obustave — sve** | `/mobilni/obustave/` |
| **Obustave — zaposleni** | `/mobilni/obustave/zaposleni/` |
| Obustave — bivši zaposleni | `/mobilni/obustave/bivsi-zaposleni/` |
| Obustave — nezaposleni | `/mobilni/obustave/nezaposleni/` |
| **CSV za obračun zarada** | `/mobilni/potrosnja/obracunski-mesec.csv` |

Izvoz u Excel postoji za pakete, korisnike, dodele i potrošnju. [P]

---

### 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| **Excel datoteke operatera** (4 vrste) | Administracija |
| Godina i mesec uz dodele i potrošnju | Administracija |
| **Izuzeci od parkinga** | Administracija |
| Ručna ispravka paketa, korisnika, dodele ili potrošnje | Administracija |
| **Status veze korisnika** (npr. „Nezaposleni“) | Administracija |

---

### 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| Paketi, korisnici, dodele, potrošnja | **Excel operatera** | **Ručno, mesečno** |
| Povezivanje sa zaposlenima | `fleet_employee` | **Automatski posle svakog uvoza** |

> **[P]** Modul **nema nijedan zakazani posao** — sve se pokreće ručno.
> Postoji komanda `sync_mobilni_sqlserver`, ali nije u rasporedu. [N]

---

### 8. Tabele i kolone

Detaljno: [4.11. Mobilna telefonija](#411-mobilna-telefonija--mobilni).
**6 tabela.**

| Tabela | Jedinstveno po |
|---|---|
| `mobilni_mobilepackage` | `(partner_code, name, valid_from)` |
| `mobilni_mobileuser` | `employee_code` |
| **`mobilni_mobileassignment`** | **`(year, month, phone_number)`** |
| **`mobilni_mobileusage`** | **`(year, month, phone_number)`** |
| `mobilni_mobileparkingexemption` | `phone_number` |
| `mobilni_mobileimportlog` | — |

---

### 9. Spoljni izvori

| Izvor | Način | Napomena |
|---|---|---|
| Operater (MTS) | **Excel, ručni uvoz** | Četiri odvojene datoteke |

> **[N]** Naziv operatera nije zabeležen u kodu; kolone potrošnje (`U MTS mreži`,
> `Van MTS mreže`) upućuju na MTS.

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`mobilni/models.py`](../mobilni/models.py) |
| **Obračun obustava** | [`mobilni/withholdings.py`](../mobilni/withholdings.py) |
| Uvoz i povezivanje | [`mobilni/support/mobile.py`](../mobilni/support/mobile.py) |
| Ekrani i izvozi | [`mobilni/views/mobile.py`](../mobilni/views/mobile.py) |

Testovi: **40 testova**. [P]

---

### 11–12. Ulaz, izlaz i veze

| Smer | Šta |
|---|---|
| **Ulaz** | Četiri Excel datoteke operatera |
| **Izlaz** | **CSV za obračun zarada**; Excel izvozi za sve četiri evidencije |

| Modul | Veza |
|---|---|
| **Kadrovi** | Zaposleni uz broj telefona (`fleet_employee`) |
| **Ugovori** | Ugovor uz paket (`MobilePackage.contract`) |

**Oblik CSV datoteke za zarade [P]:**

| Osobina | Vrednost |
|---|---|
| Kolone | `Godina;Mesec;Šifra radnika;Iznos obustave` |
| Razdvajač | tačka-zarez |
| Kodiranje | UTF-8 **sa BOM** |
| Prelom reda | `CRLF` |
| Obuhvat | **samo aktivni zaposleni** |
| Iznos | **ceo dinar**, `ROUND_HALF_UP` |
| Izostavljeno | prazna obustava i **obustava jednaka nuli** |

---

### 13. Izveštaji i analize

**4 obračuna.** Detaljno: [6.7. Mobilna telefonija](#67-mobilna-telefonija--obračuni).

**Formula obustave [P]:**

> **obustava = osnovica za PDV − neto iznos paketa + parking + NZRD**

Potvrđeno kao ispravno (naručilac, 18.09.2026.).

---

### 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `mobilni` | **Sve funkcije modula** — usklađuje se automatski |
| `uprava` | Sve |

> **[P]** Uloga `sekretarijat` je izričito **lišena** dozvola ovog modula pri svakoj
> sinhronizaciji dozvola.

---

### 15. Validacije i kontrole

| Kontrola | Ponašanje |
|---|---|
| Jedna dodela po broju i mesecu | Kontrola u bazi |
| Jedna potrošnja po broju i mesecu | Kontrola u bazi |
| Normalizacija broja telefona | Uklanja `.0` iz Excel ćelije i sve osim cifara |
| Godina | 2020–2100 |
| Mesec | 1–12 |
| Izuzetak od parkinga | Jedinstven po broju |
| Uvoz | Beleži se u `mobilni_mobileimportlog` sa brojačima i greškom |

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Potrošnja bez dodele za isti mesec** | **Tiho ispada iz obračuna** | [P-31](#10-poznati-problemi-i-ograničenja) |
| Paket bez neto iznosa | Obustava **prazna**, red se ne izvozi | — |
| **Negativna obustava** | **Izvozi se** | [P-31](#10-poznati-problemi-i-ograničenja) |
| Obustava jednaka nuli | **Ne izvozi se** | — |
| **Poseban broj `381637781481`** | Paket se **ne odbija** | **[P-34](#10-poznati-problemi-i-ograničenja) — potvrđena greška** |
| Korisnik označen „Nezaposleni“ | Ne povezuje se sa zaposlenim | Namerno |
| Zaposleni otišao usred meseca | **Nije ni u jednom pojedinačnom izveštaju** | [P-32](#10-poznati-problemi-i-ograničenja) |
| Izuzetak od parkinga upisan naknadno | **Menja i prošle obračune** | [P-30](#10-poznati-problemi-i-ograničenja) |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | **Poslovno objašnjenje posebnog broja** | **Q8** — potvrđeno kao greška, ide u bazu |
| 2 | Da li negativna obustava ide u zarade kao potraživanje zaposlenog | **Q29** |
| 3 | **Kako se CSV unosi u obračun zarada** i koja konta se koriste | **Q3** |
| 4 | Ko je operater i da li se oblik datoteka menja | **[N]** |
| 5 | Čemu služi komanda `sync_mobilni_sqlserver` | **[N]** |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.7](#67-mobilna-telefonija--obračuni) | Sva 4 obračuna |
| [4.11](#411-mobilna-telefonija--mobilni) | Tabele |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-30, P-31, P-32, **P-34** |

---

## 3.9. Isplate

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Isplate** / „Isplata neoporezivih primanja“ |
| Tehnički naziv | Django aplikacija `isplate` |
| Adresa | `/isplate/` |
| Bočni meni | `sidebar_isplate.html` |

> **[P] Modul nema nijednu sopstvenu tabelu.** Radi isključivo nad putnim nalozima
> Flote i proizvodi datoteku.

---

### 2. Poslovna namena

Pretvara **akontacije sa putnih naloga** u **datoteku za elektronsko bankarstvo**, da
blagajna ne bi ručno kucala naloge za plaćanje.

> **Ovo je jedini modul čiji rezultat ide direktno u banku.**
> Greška ovde znači pogrešnu isplatu.

---

### 3. Korisnici modula

| Korisnik | Šta radi | Uloga |
|---|---|---|
| **Blagajna** | Bira naloge, zadaje datum virmana, preuzima datoteku, učitava je u banku | `blagajna` |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Spisak putnih naloga za isplatu** | Filteri: status virmana, centar, godina, mesec, pretraga |
| **Generisanje virmana** | Izabrani nalozi ili svi filtrirani; datum virmana |
| **Ponovno generisanje** | Uz izričit izbor |
| **Konverter** | Postojeća virman datoteka → JSON |

---

### 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Isplata neoporezivih primanja** | `/isplate/` |
| **Konverter** | `/isplate/konverter/` |

---

### 6. Podaci koje korisnik unosi

| Podatak | Napomena |
|---|---|
| **Datum virmana** | Obavezan — *„Izaberi datum virmana.“* |
| Izbor naloga | Pojedinačno ili svi filtrirani |
| Dozvoli ponovno generisanje | Izričit izbor |
| Datoteka za konverziju | `.txt` u konverteru |

> **[P] Modul ne unosi nijedan poslovni podatak** — svi dolaze sa putnog naloga i
> iz kadrovske evidencije.

---

### 7. Podaci koje sistem preuzima

| Podatak | Odakle |
|---|---|
| Broj naloga, iznos akontacije, valuta, status storna | `fleet_putninalog` |
| **Partija (tekući račun)** | `fleet_employee.account_number` |
| Ime i prezime | `fleet_employee.original_full_name` |
| **Opština boravka** | `fleet_employee.residence_municipality` |

**Podaci platioca su upisani u kod** [P]:

| Podatak | Vrednost |
|---|---|
| Račun platioca | `205000000001445485` |
| Naziv | `Institut IMS a.d.` |
| Mesto | `Beograd` |
| Svrha | `NEOPOREZIVA PRIMANJA ZAPOSLENIH` |
| Šifra plaćanja | `241` |

---

### 8. Tabele i kolone

**Modul nema sopstvenih tabela.** [P]

Upisuje u `fleet_putninalog`:

| Kolona | Kada |
|---|---|
| `virman_generated` | Postaje `True` posle generisanja |
| `virman_generated_at` | Trenutak generisanja |
| `virman_generated_by` | Korisnik |

---

### 9. Spoljni izvori

| Izvor | Smer | Oblik |
|---|---|---|
| **Banka (elektronsko bankarstvo)** | **Izlaz** | Datoteka fiksne širine, **180 znakova**, `cp1250`, `CRLF` |

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| **Generisanje virmana** | [`isplate/services/virman.py`](../isplate/services/virman.py) |
| **Konverter u JSON** | [`isplate/services/converters.py`](../isplate/services/converters.py) |
| Ekrani | [`isplate/views.py`](../isplate/views.py) |

Testovi: **20 testova**. [P]

---

### 11–12. Ulaz, izlaz i veze

| Modul | Veza |
|---|---|
| **Flota** | Putni nalozi sa akontacijom — jedini izvor |
| **Kadrovi** | Partija i opština boravka zaposlenog |

**Tok [Z]:**

```
 Sekretarijat izdaje putni nalog sa akontacijom
            │
 Blagajna bira naloge i datum virmana
            │
 Sistem pravi datoteku (180 znakova po redu)
            │
 Blagajna učitava datoteku u elektronsko bankarstvo
            │
 Banka izvršava plaćanja → zaposleni prima akontaciju
            │
 Zadatak u 12:30 puni polje „Isplaćeno“ iz dbo.fleet_zatvoren_putni
```

> **[N] Q32:** poslednji korak **nije povezan** sa generisanim virmanom u kodu.
> Nije potvrđeno da li se isplata po virmanu igde potvrđuje u sistemu.

---

### 13. Izveštaji i analize

**3 obračuna.** Detaljno: [6.10. Isplate](#610-isplate--virmani).

| Oznaka | Naziv |
|---|---|
| I-01 | **Generisanje datoteke virmana** — [P-33](#10-poznati-problemi-i-ograničenja) |
| I-02 | Kontrole naloga pre virmana |
| I-03 | Konverzija virmana u JSON |

---

### 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `blagajna` | **Sve funkcije modula** — usklađuje se automatski |
| `uprava` | Sve |

---

### 15. Validacije i kontrole

**Devet provera pre generisanja, sve greške se prijavljuju zajedno** [P]:

| # | Provera |
|---|---|
| 1 | Nalog nije storniran |
| 2 | Virman nije već odrađen (osim uz izričito ponovno generisanje) |
| 3 | **Valuta je RSD** |
| 4 | **Nalog ima IMS zaposlenog** — ne spoljno lice |
| 5 | Zaposleni ima račun |
| 6 | **Račun ima tačno 18 cifara** |
| 7 | Iznos je veći od nule |
| 8 | Broj naloga ima redni broj posle crtice |
| 9 | Redni broj nije duži od 21 znaka |

**Dodatna kontrola [P]:** svaki red se proverava na **tačno 180 znakova**;
neispravan red **prekida** nastanak datoteke.

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Naziv primaoca duži od 35 znakova** | **Skraćuje se bez upozorenja** | [P-33](#10-poznati-problemi-i-ograničenja) |
| **Mesto duže od 10 znakova** | **Skraćuje se** — „Novi Beograd“ → „Novi Beogr“ | [P-33](#10-poznati-problemi-i-ograničenja) |
| Zaposleni bez opštine boravka | Upisuje se **`Beograd`** | [P-33](#10-poznati-problemi-i-ograničenja) |
| **Sadržaj poslate datoteke** | **Ne čuva se** | [P-33](#10-poznati-problemi-i-ograničenja) |
| Srpska slova | Preslovljavaju se: `đ`→`dj`, `č`/`ć`→`c`, `š`→`s`, `ž`→`z` |  |
| Znak van `cp1250` | Zamenjuje se | — |
| Konverter: svi nalozi | `UrgentPayment` je **uvek `true`** | — |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Treba li da podaci platioca budu podesivi umesto u kodu | **Q30** |
| 2 | Koji sistem koristi JSON iz konvertera | **Q31** |
| 3 | Da li se isplata po virmanu potvrđuje u sistemu | **Q32** |
| 4 | Koja se banka koristi i da li je oblik datoteke njen standard | **[N]** |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.10](#610-isplate--virmani) | Sva 3 obračuna, sa opisom svakog polja datoteke |
| [3.1. Flota](#31-vozni-park-flota) | Putni nalozi |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-33 |

---

## 3.10. Administracija

> Deo poglavlja [3. Moduli](#3-moduli--sadržaj-i-veze).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Administracija** |
| Tehnički naziv | Django aplikacija `core` **+ deo aplikacije `fleet`** |
| Adresa | `/administracija/`, `/users/`, `/organizacione-jedinice` |
| Bočni meni | `sidebar_administracija.html` |

> **[P] Zamka:** modeli su u `core/models.py`, ali imaju `app_label = "fleet"`, pa su
> tabele `fleet_customuser`, `fleet_role`, `fleet_activity_log`… Ekrani su u `fleet/views/`.
> Aplikacija `core` sama ima **samo jednu rutu** — prebacivanje između modula.

---

### 2. Poslovna namena

Vodi **ko sme šta da radi u sistemu i šta je ko uradio**:

1. **Korisnici** i njihova veza sa zaposlenima.
2. **Uloge i dozvole** — ko vidi koji ekran.
3. **Organizacione jedinice i centri** — osnova svih evidencija i ograničenja pristupa.
4. **Evidencija rada** — trag svake radnje u sistemu.
5. **Istorija pozadinskih poslova** — da li su noćne sinhronizacije prošle.

---

### 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Administrator sistema** | Vodi korisnike, dodeljuje uloge i centre, prati rad sistema |
| **Uprava** | Uvid u evidenciju rada |

---

### 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Korisnici** | Spisak, uređivanje pristupa, povezivanje sa zaposlenim, stvaranje naloga iz kadrovske evidencije |
| **Uloge i dozvole** | Izbor uloga za korisnika i pregled pripadajućih dozvola; dozvole se generišu iz ruta |
| **Organizacione jedinice** | Šifra, naziv, **centar** |
| **Evidencija rada** | Ko, kada, koji ekran, koji zapis, sa koje IP adrese |
| **Istorija zadataka** | Status, trajanje, rezultat i greška svakog pozadinskog posla |
| **Prebacivanje modula** | Izbor bočnog menija, pamti se u sesiji |
| **Obavezna promena lozinke** | Za naloge sa oznakom `must_change_password` |

---

### 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Korisnici** | `/users/` |
| **Uloge i dozvole korisnika** | `/users/<id>/access/` |
| Povezivanje korisnika sa zaposlenim | `/users/link-employee/` |
| **Stvaranje naloga za zaposlene** | `/users/create-missing-profiles/`, `/users/create-profile/<id>/` |
| **Evidencija rada** | `/administracija/activity-log/` |
| **Istorija zadataka** | `/administracija/task-history/` |
| Organizacione jedinice | `/organizacione-jedinice` |
| Prijava / odjava | `/login/`, `/logout/` |
| Obavezna promena lozinke | `/moj-profil/promena-lozinke/` |
| Django admin | `/admin/` |

Pregled **Korisnici** ima tabove **Korisnički nalozi** i **Zaposleni bez naloga**.
Nalozi se pretražuju po imenu, korisničkom imenu, centru i OJ, uz filtere po ulozi
i statusu. Brzi filteri izdvajaju naloge bez prijave, sa obaveznom promenom lozinke
i bez veze sa zaposlenim. Tabela prikazuje uloge, obuhvat i poslednju prijavu;
na telefonu se redovi prikazuju kao kartice. Administrator dugmetom **Uredi pristup**
otvara dozvole, a **Poveži zaposlenog** otvara prozor za izbor zaposlenog.

---

### 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| Korisnički nalog: korisničko ime, lozinka | Administrator |
| **Veza korisnika sa zaposlenim** | Administrator |
| **Uloge** korisnika | Administrator |
| **Dozvoljeni centri** (veza i/ili tekstualna lista) | Administrator |
| Oznaka „mora promeniti lozinku“ | Administrator |
| Organizaciona jedinica (ručno) | Administrator |

---

### 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| **Organizacione jedinice i centri** | `dbo.v_organizationalunit` | Dnevno 01:30 |
| **Kodovi dozvola** | Automatski iz `urlpatterns` svih aplikacija | Dnevno 01:00 |
| Evidencija rada | Sam sistem, kroz `ActivityLogMiddleware` | Pri svakom zahtevu |
| Istorija zadataka | Celery signali | Pri svakom zadatku |

---

### 8. Tabele i kolone

Detaljno: [4.3. Zajedničke osnove](#43-zajedničke-osnove--core-tabele-u-fleet_).
**7 tabela**, sve sa prefiksom `fleet_`.

| Tabela | Uloga |
|---|---|
| **`fleet_customuser`** | Korisnik; zamenjuje Django `User` |
| `fleet_role` | Uloga (`name`, `slug`, `is_active`) |
| `fleet_permissioncode` | **Kod dozvole = ime URL rute** |
| `fleet_rolepermission` | Veza uloga ↔ dozvola |
| **`fleet_organizationalunit`** | Šifra posla / OJ i **centar** |
| **`fleet_activity_log`** | Evidencija rada |
| **`fleet_task_history`** | Istorija pozadinskih poslova |

Plus M2M tabele: `fleet_customuser_roles`, `fleet_customuser_allowed_centers`.

---

### 9. Kako rade dozvole

```
 CustomUser ──M2M──► Role ──RolePermission──► PermissionCode
                      │                            │
                  is_active                 code = IME URL RUTE
```

**Provera [P]:** korisnik ima pristup ako ijedna njegova **aktivna** uloga sadrži kod
jednak imenu rute koja se otvara. `is_superuser` prolazi svuda.
I stariji `RoleRequiredMixin`, koji proverava slug uloge, od 24.09.2026. isključuje
neaktivne uloge. Spisak korisnika sada traži dozvolu `user_list`.

**Generisanje [P]:** `sync_permission_codes` obilazi `urlpatterns` svih aplikacija.
Nova ruta = nova dozvola, ali tek posle pokretanja komande ili noćnog zadatka u 01:00.

**Uloge koje se usklađuju** (višak dozvola se briše) [P]:
`nabavka`, `menice`, `blagajna`, `mobilni`, `pregled-naplate`, `zahtev`.

**Uloge koje se samo dopunjavaju** [P]: `pravna`, `sekretarijat`, `zaposleni`, `uprava`.

> **[P]** Uloga **`uprava`** pri svakoj sinhronizaciji dobija **sve** dozvole u sistemu.

#### Glavne predefinisane uloge [P]

| Slug | Naziv |
|---|---|
| `uprava` | Uprava |
| `nabavka` | Nabavka |
| `menice` | Menice |
| `blagajna` | Blagajna |
| `pravna` | Pravna služba |
| `mobilni` | Mobilni |
| `finansije` | Finansijska analitika |
| `pregled-naplate` | Pregled naplate |
| `zahtev` | Zahtev |
| `sekretarijat` | Sekretarijat |
| `kadrovi` | Kadrovi — kompletan modul, podaci prema obuhvatu |
| `zaposleni` | Zaposleni |

#### Upravljanje pristupom kroz aplikaciju

U **Administracija → Korisnici → Uloge i dozvole**, superuser bira uloge,
centre i kadrovske OJ iz pretraživih spiskova. Tu se menjaju ime, prezime,
e-pošta i aktivnost naloga. Pregled dozvola prati izabrane uloge, a primena je
tek nakon **Sačuvaj pristup**. Pristup listi traži `user_list`; izmene naloga su
i dalje samo za superuser, uključujući direktan POST. Nije moguće ugasiti sopstveni
nalog niti kroz ovu formu dodeliti `is_superuser` ili `is_staff`.

Centri se čuvaju u `allowed_center_codes`. Kadrovske OJ (npr. 411 i 431) čuvaju
se zasebno u `allowed_hr_unit_codes`; izbor jedne OJ ne uključuje njene susedne OJ.
Postojeći M2M `allowed_centers` je u zasebnom odeljku jer sadrži i šifre poslova,
a pojedini moduli iz njega izvode pristup celom centru. Dodele se sabiraju.

Uloga **Kadrovi** zamenjuje `kadrovik-resenja`, uz očuvanje članstva i dodatnih
dozvola. Ima funkcije celog modula i šifarnike, ali joj se automatski ne dodeljuju
`hr:resenje_view_all` i `hr:evaluation_view_all`. Bez obuhvata nema tuđih kadrovskih
podataka. Superuser i odgovarajuće posebne dozvole za sve centre imaju prednost.
Za druge module prazan obuhvat zadržava njihova postojeća pravila; nije univerzalna
zabrana pristupa. Obrasci to izričito prikazuju.

Promena se evidentira u Activity logu sa prethodnim i novim ulogama, obuhvatom i
aktivnošću. Pri uklanjanju uloge uklanja se i odgovarajuća stara Django grupa za
Sekretarijat, Zaposlene ili Pregled naplate, kako je noćni sync ne bi ponovo dodelio.

Provera od 24.09.2026. našla je i dodeljene probne uloge `render-check` i
`render-check-2`. Nisu obrisane niti su njihovi korisnici menjani. Noćni sync za
neke standardne uloge i dalje prepisuje skup dozvola; ovaj ekran menja članstvo
korisnika, a ne definiciju zajedničke uloge.

---

### 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`core/models.py`](../core/models.py) |
| **Generisanje dozvola** | [`core/permissions.py`](../core/permissions.py) |
| **Provera dozvola** | [`core/mixins.py`](../core/mixins.py) |
| Evidencija rada | [`core/middleware.py`](../core/middleware.py), [`core/activity.py`](../core/activity.py) |
| Prebacivanje modula | [`core/context_processors.py`](../core/context_processors.py), [`core/views.py`](../core/views.py) |
| Ekrani korisnika i logova | [`fleet/views/users.py`](../fleet/views/users.py) |
| **Raspored pozadinskih poslova** | [`core/management/commands/sync_celery_periodic_tasks.py`](../core/management/commands/sync_celery_periodic_tasks.py) |
| Istorija zadataka | [`ims_erp/celery.py`](../ims_erp/celery.py) — signali |

---

### 11–12. Ulaz, izlaz i veze

| Modul | Veza |
|---|---|
| **Svi moduli** | Organizaciona jedinica i centar; dozvole |
| **Kadrovi** | `CustomUser.employee` → `fleet_employee` |

---

### 13. Izveštaji i analize

Modul nema obračune. Ima dva pregleda:

| Pregled | Sadržaj |
|---|---|
| **Evidencija rada** | Prijave, odjave, **neuspešne prijave**, pojedinačne radnje |
| **Istorija zadataka** | Status (`Pokrenut`, `Uspešan`, **`Preskočen`**, `Neuspešan`), trajanje, poruka |

---

### 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `uprava` | Sve |
| Superuser | Sve, uključujući Django admin i upravljanje pristupom korisnika kroz aplikaciju |

> **Ranija zamka, ispravljena 18.09.2026.:** statistiku centra u Floti ni superuser nije
> mogao da otvori bez upisanih dozvoljenih centara — [P-13](#10-poznati-problemi-i-ograničenja).
> Provera je usklađena sa `RolePermissionRequiredMixin`.

---

### 15. Validacije i kontrole

| Kontrola | Ponašanje |
|---|---|
| Jedinstven `slug` uloge | Kontrola u bazi |
| Jedinstven kod dozvole | Kontrola u bazi |
| Jedinstven par uloga ↔ dozvola | Kontrola u bazi |
| Jedinstvena šifra organizacione jedinice | Kontrola u bazi |
| **OJ sa praznim poljima** | **Preskače se** pri sinhronizaciji, uz upozorenje |
| Obavezna promena lozinke | Preusmerava na ekran za promenu |
| Neuspešna prijava | **Beleži se** u evidenciju rada |

---

### 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Nova ruta bez pokretanja sinhronizacije dozvola | Vide je **samo superuser i Uprava** |
| **Dva mehanizma za centre** | `allowed_centers` i `allowed_center_codes` rade paralelno — [P-19](#10-poznati-problemi-i-ograničenja) |
| Korisnik bez povezanog zaposlenog | Ne može otvoriti radnu listu ni svoj profil |
| Zadatak preskočen | Status **„Preskočen“** — prethodni je još radio, **nije greška** |
| Redis nedostupan | Zadatak se **ipak izvršava**, bez zaštite — [P-16](#10-poznati-problemi-i-ograničenja) |
| Brisanje korisnika | Evidencija rada **zadržava** korisničko ime i ime |

---

### 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | **Koji mehanizam za centre je merodavan** | **Q5** / [P-19](#10-poznati-problemi-i-ograničenja) |
| 2 | Ko je odgovoran za dodelu uloga i po kom pravilu | **Q2** |
| 3 | Koliko dugo se čuva evidencija rada i da li se briše | **[N]** |
| 4 | Sadržaj pogleda `dbo.v_organizationalunit` | DDL |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [2.6. Kontrola pristupa](#26-kontrola-pristupa) | Kako rade dozvole |
| [9. Održavanje](#9-održavanje) | Zakazani poslovi i praćenje |
| [4.3](#43-zajedničke-osnove--core-tabele-u-fleet_) | Tabele |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | P-13, P-16, P-19 |

---

## 4. Baza podataka

> **Za koga je ovo poglavlje:** programeri, administratori baze, AI agenti.
> Status tvrdnji: **[P]** potvrđeno kodom/migracijama, **[Z]** zaključeno, **[N]** nepotvrđeno.
>
> Ovo poglavlje opisuje **šta koja tabela znači poslovno** i **koji ključ je čini jedinstvenom**.
> Iscrpan spisak svake kolone je u izvornom kodu modela — putanja je navedena uz svaku grupu.

---

### 4.1. Osnovno

| Stavka | Vrednost | Status |
|---|---|---|
| Motor | Microsoft SQL Server | [P] |
| Baza | `IMS_ERP` na serveru `SMS-SERVER` | [P] |
| Django adapter | `mssql-django` 1.5, ODBC Driver 17 | [P] |
| Sopstvenih Django tabela | 118 | [P] |
| Modela nad nasleđenim pogledima (`managed = False`) | 13 | [P] |
| Apstraktnih modela (bez tabele) | 3 | [P] |
| Nasleđenih `dbo.*` objekata koji se čitaju sirovim SQL-om | 37 | [P] |
| Migracija | 146 | [P] |

#### 4.1.1. Dva aliasa, jedna baza [P]

| Alias | Namena |
|---|---|
| `default` | Django ORM i migracije |
| `server_db` | Sirovi SQL nad nasleđenim `dbo.*` objektima |

Oba pokazuju na **istu fizičku bazu** `IMS_ERP`. Django tabele i nasleđeni objekti starog
ERP-a žive jedni pored drugih. Django migracije **ne diraju** nasleđene objekte.

#### 4.1.2. Povezani serveri [P]

Deo `dbo.*` pogleda u `IMS_ERP` interno čita udaljene servere, a neki moduli ih čitaju direktno:

| Povezani server | Baza | Objekti | Ko čita direktno |
|---|---|---|---|
| `PUTGEO-SERVER` | `bazaims` | `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | `finansije/services/source.py`, `potrazivanja/services/source.py` |
| `PUTGEO-SERVER` | `bazaldims` | `Zarada`, `PomLD`, `Radnik`, `element` | `finansije/services/job_people.py`, `cash_flow.py` |
| `INFORMATIKA23` | `ID` | `Radnici`, `C_Prolasci_Radnika`, `C_Tasteri`, `c_parovi_radnika_detalji` | `hr/services/attendance.py` |
| `SERFIN` | `bazaldims` | `radnik` | `hr/services/attendance.py` |

---

### 4.2. Pravilo imenovanja tabela — obavezno pročitati [P]

Django podrazumevano imenuje tabelu `<app_label>_<model>`. U ovom projektu **`app_label`
nije uvek jednak direktorijumu aplikacije**:

| Model je definisan u | `app_label` | Tabela |
|---|---|---|
| `core/models.py` (svi modeli) | `fleet` | `fleet_customuser`, `fleet_role`, `fleet_permissioncode`, `fleet_rolepermission`, `fleet_organizationalunit` |
| `core/models.py: ActivityLog` | `fleet` | **`fleet_activity_log`** (izričit `db_table`) |
| `core/models.py: TaskHistory` | `fleet` | **`fleet_task_history`** (izričit `db_table`) |
| `hr/models.py: Employee`, `EmployeeCVItem` | `fleet` | `fleet_employee`, `fleet_employeecvitem` |
| `hr/models.py: ostali` | `hr` | `hr_worktimesheet`, `hr_sickleave`, … |
| `nabavka/models.py` | `nabavka` | izričiti `db_table`: `nabavka_procurement_case`, `nabavka_invoice`, … |
| `ugovori/models.py` | `ugovori` | izričiti `db_table`: `ugovori_partner`, `ugovori_contract`, … |
| `menice/models.py` | `menice` | izričiti `db_table`: **`menica`**, **`ulazna_menica`** (bez prefiksa) |
| `naplata/models.py` | `naplata` | izričiti `db_table`: **`postupak`**, **`promena_postupka`**, **`avans_klijent`** |

**Posledica [Z]:** pretraga po imenu tabele može da promaši. `fleet_employee` je kadrovska
tabela; `menica` i `postupak` nemaju prefiks aplikacije.

---

### 4.3. Zajedničke osnove — `core` (tabele u `fleet_*`)

Izvorni kod: [`core/models.py`](../core/models.py)

#### `fleet_organizationalunit` — organizaciona jedinica / šifra posla

Centralni šifarnik na koji se vezuju vozila, putni nalozi, radne liste, nabavka i finansije.

| Kolona | Tip | Poslovno značenje |
|---|---|---|
| `code` | `char(10)`, **jedinstveno** | Šifra organizacione jedinice (šifra posla) |
| `name` | `char(100)` | Naziv |
| `center` | `char(10)` | **Šifra centra** — koristi se za ograničenje pristupa i brojanje dokumenata |

Puni ga sinhronizacija iz `dbo.v_organizationalunit` (`sif_pos`, `naz_pos`, `blok`),
dnevno u 01:30. [P] Redovi sa praznim poljima se **preskaču**, ne upisuju. [P]

> **Pažnja [P]:** u Finansijama centar **ne dolazi** iz ove tabele nego iz aktuelnog
> `posao.blok` na izvoru. Promena centra u šifarniku pregrupiše celu istoriju.

#### `fleet_customuser` — korisnik sistema

Zamenjuje Django `User` (`AUTH_USER_MODEL = 'fleet.CustomUser'`). [P]

| Kolona | Poslovno značenje |
|---|---|
| `employee_id` | Veza 1:1 ka `fleet_employee` — povezuje nalog sa zaposlenim |
| `allowed_center_codes` | Šifre centara, odvojene zarezima |
| `allowed_hr_unit_codes` | JSON lista kadrovskih OJ; pojedinačna ograničenja za modul Kadrovi |
| `must_change_password` | Prisiljava promenu lozinke pri prijavi |
| M2M `fleet_customuser_allowed_centers` | Dozvoljene organizacione jedinice |
| M2M `fleet_customuser_roles` | Dodeljene uloge |

> **[N]** Postoje **dva** mehanizma za centre (`allowed_centers` i `allowed_center_codes`).
> Koji je merodavan u kom modulu nije potvrđeno — pitanje **Q5**.

#### `fleet_role`, `fleet_permissioncode`, `fleet_rolepermission` — dozvole

| Tabela | Sadržaj |
|---|---|
| `fleet_role` | Uloga: `name`, `slug` (jedinstven), `is_active` |
| `fleet_permissioncode` | `code` (jedinstven) = **ime URL rute**, `label` |
| `fleet_rolepermission` | Veza uloga ↔ dozvola, jedinstveno po paru |

Kodovi se generišu automatski iz `urlpatterns`. Vidi [2.6](#26-kontrola-pristupa).

#### `fleet_activity_log` — evidencija rada korisnika

Popunjava je `ActivityLogMiddleware` posle svakog odgovora. [P]

| Kolona | Značenje |
|---|---|
| `action` | `request`, `login`, `logout`, `login_failed`, `manual` |
| `actor_username`, `actor_display_name` | Sačuvani i kad se korisnik kasnije obriše |
| `app_label`, `view_name`, `method`, `path`, `status_code` | Šta je otvoreno |
| `object_model`, `object_pk`, `object_repr` | Nad kojim zapisom |
| `changes` | JSON sa izmenama |
| `ip_address`, `user_agent` | Odakle |

Indeksi: po korisniku, po akciji i po aplikaciji — svi uz `-created_at`. [P]

#### `fleet_task_history` — istorija pozadinskih poslova

| Kolona | Značenje |
|---|---|
| `task_id` | Jedinstven Celery ID |
| `task_name`, `display_name` | Tehnički i prikazni naziv (iz rasporeda) |
| `status` | `started`, `success`, `skipped`, `failure` |
| `short_message`, `result`, `error` | Ishod |
| `started_at`, `finished_at`, `elapsed_seconds` | Trajanje |

Status `skipped` znači da je posao preskočen jer je prethodni još radio. [P]

---

### 4.4. Vozni park — `fleet`

Izvorni kod: [`fleet/models.py`](../fleet/models.py)

#### 4.4.1. Vozilo i dokumenti

##### `fleet_vehicle` — vozilo

| Kolona | Poslovno značenje |
|---|---|
| `chassis_number` | **Broj šasije — jedinstven, obavezan.** Pravi identitet vozila |
| `inventory_number` | Inventarski broj (jedinstven, može biti prazan) — veza sa knjigovodstvom |
| `engine_number` | Broj motora (jedinstven, može biti prazan) |
| `category` | `putnicko`, `teretno`, `prikljucno` |
| `brand`, `model`, `year_of_manufacture`, `first_registration_date` | Osnovni podaci |
| `engine_volume`, `engine_power`, `weight`, `maximum_permissible_weight`, `load_capacity`, `number_of_axles`, `number_of_seats`, `fuel_type`, `color`, `homologation_number` | Tehnički podaci |
| `purchase_value` | Nabavna vrednost |
| `value` | **Knjigovodstvena vrednost** — puni je sinhronizacija iz `dbo.vrednost_vozila` |
| `service_interval` | Servisni interval u km, podrazumevano **15.000** |
| `purchase_date`, `partner_code`, `partner_name`, `invoice_number` | Podaci o nabavci |
| `otpis` | **Otpisano** — `editable=False`, postavlja ga samo sinhronizacija iz `dbo.fleet_otpis` |

> **[P]** `Vehicle.__str__` prikazuje registarsku oznaku iz **izdate** saobraćajne
> (`issue_date <= danas`), a ako je nema — broj šasije.
>
> **[P]** `maximum_permissible_weight` nije samo tehnički podatak: od njega zavisi
> **prag fiksnog troška po kilometru** (vidi obračun V-11).

##### `fleet_trafficcard` — saobraćajna dozvola

Istorijska tabela: jedno vozilo ima više saobraćajnih kroz vreme, sa različitim tablicama.

| Kolona | Poslovno značenje |
|---|---|
| `registration_number` | Registarska oznaka, format `AA999-AA` ili `AA9999-AA` (validator) |
| `issue_date` | Datum izdavanja — **ne sme biti u budućnosti** |
| `valid_until` | Rok dokumenta — ne sme biti pre datuma izdavanja |
| `registration_valid_until` | Registracija važi do |
| `traffic_card_number`, `serial_number`, `owner` | Podaci sa dokumenta |
| `traffic_card_pdf`, `traffic_card_front_image`, `traffic_card_back_image` | Prilozi |

Kontrole u `clean()` [P]:

1. Tablica se normalizuje kroz `format_license_plate()`.
2. **Ista tablica ne sme pripadati drugom vozilu** — inače: *„Ove tablice su već povezane
   sa drugim vozilom. Potrebna je provera istorije.“*
3. Rok ne sme biti pre izdavanja; izdavanje ne sme biti u budućnosti.

Poseban upit `for_plate()` [P] razrešava tablicu u vozilo kroz istoriju dokumenata i
**namerno odbija da pogađa** kada tablica pripada većem broju vozila
(`MultipleObjectsReturned`). To je zaštita, ne greška.

Indeks: `(vehicle, -issue_date, -id)`. [P]

##### `fleet_vehicletenderdocument` — tenderska dokumentacija

Slike tablica, nalepnica i ostalo, za potrebe tendera. Stara slika se briše tek posle
potvrde transakcije (`transaction.on_commit`). [P]

#### 4.4.2. Pripadnost i raspolaganje

##### `fleet_jobcode` — dodela vozila organizacionoj jedinici (istorijska)

| Kolona | Značenje |
|---|---|
| `vehicle_id`, `organizational_unit_id` | Vozilo i OJ |
| `assigned_date` | **Datum dodele** |

Jedinstveno: `(vehicle, assigned_date)`. [P]
Važenje dodele traje **do dana pre sledeće dodele**. [P]

> Ovo je osnova za sve izveštaje „po šifri posla“ — trošak vozila pripada onoj OJ koja je
> bila dodeljena **na datum troška**, a ne trenutnoj.

Dnevno se osvežava iz `dbo.sif_pos_trenutno` (`regbr`, `sifpos`); nova dodela se upisuje
**samo ako se razlikuje od poslednje**. [P]

##### `fleet_vehicleholding` — osnov raspolaganja vozilom

| Kolona | Značenje |
|---|---|
| `basis` | `owned` (vlasništvo IMS) ili `contract` (korišćenje po ugovoru) |
| `start_date`, `end_date` | Period (uključivo); `end_date` prazan = još traje |
| `lease_id` | Obavezan za `contract` |
| `financing` | `own_funds` ili `credit` — samo za vlasništvo IMS |
| `financing_contract_id` | Samo uz `credit` |
| `evidence`, `note` | Osnov promene |

Kontrole [P]:

1. Kraj ne sme biti pre početka (i kao `CheckConstraint` u bazi).
2. Za `contract`: ugovor mora pripadati **tom** vozilu, a period raspolaganja mora biti
   **unutar** perioda ugovora.
3. Za `owned`: ne sme se birati ugovor o korišćenju.
4. Ugovor o finansiranju samo uz `credit`.
5. **Periodi se ne smeju preklapati** — provera uz `select_for_update()` nad vozilom.

##### `fleet_lease` — lizing / najam

| Kolona | Značenje |
|---|---|
| `lease_type` | `finansijski`, `operativni`, `dugorocni` (dugoročni najam) |
| `partner_code`, `partner_name` | Davalac |
| `job_code` | Šifra posla (tekst, ne veza) |
| `contract_number` | Broj ugovora (tekst) |
| `contract_id` | Veza ka `ugovori_contract` (opciona) |
| `current_payment_amount` | **Trenutna rata** |
| `start_date`, `end_date` | Period |

`is_long_term_rental` je `True` za `dugorocni`, `dugoročni`, `dugoročnI` — tri zapisa
zbog istorijskih podataka sa dijakriticima. [P]

##### `fleet_leaseinterest` — kamata po godini

Jedinstveno `(year, lease)`. Puni se iz `dbo.lizing_kamate`. [P]

#### 4.4.3. Osiguranje

| Tabela | Uloga |
|---|---|
| `fleet_policy` | **Polisa** — premija, rate, period, obnavljanje; ključ je `invoice_id` (jedinstven) |
| `fleet_draftinsurance` | Nedovršeno knjiženje osiguranja iz `dbo.fleet_potrazivanje_ddor` |
| `fleet_insurance` | Konačno knjiženje osiguranja |

`fleet_insurance` jedinstveno po `(god, sif_vrs, br_naloga, stavka, knt)` — to je
**izvorni ključ knjiženja**. [P] Ista petorka se koristi i za proveru da li draft već postoji.

`Policy.incomplete_q()` i `is_complete()` definišu šta je „nedovršena polisa“ —
13 obaveznih polja. [P] Ekran `/polise/nedovrseno/` koristi upravo taj uslov.

#### 4.4.4. Gorivo

| Tabela | Uloga | Izvorni ključ |
|---|---|---|
| `fleet_transactionomv` | Sirove transakcije sa OMV kartica | `(license_plate_no, transaction_date, product_inv, voucher, quantity)` |
| `fleet_transactionnis` | Sirove transakcije sa NIS kartica | `(datum_transakcije, registarska_oznaka_vozila, naziv_proizvoda)` |
| `fleet_fuelconsumption` | Objedinjena potrošnja po vozilu | `(vehicle, supplier, date, amount, fuel_type)` |

`fleet_fuelconsumption` kolone: `date`, `amount` (količina), `fuel_type`,
`cost_bruto`, `cost_neto`, `supplier`, `job_code`, `mileage`.

> **[P] Važno:** OMV transakcije sadrže duplikate i „odjeke“ računa. Sirov `SUM` nad
> `fleet_transactionomv` daje **pogrešan** iznos. Filteri su u
> [`fleet/support/fuel.py`](../fleet/support/fuel.py) — vidi obračune V-03 do V-06.

#### 4.4.5. Održavanje i garaža

| Tabela | Uloga |
|---|---|
| `fleet_servicetype` | Šifarnik tipova servisa (jedinstven naziv) |
| `fleet_service` | Servis: datum, trošak, dobavljač |
| `fleet_servicetransaction` | **Knjiženje servisa** iz `dbo.fleet_servisi` |
| `fleet_draftservicetransaction` | Nedovršeno knjiženje servisa |
| `fleet_requisition` | **Trebovanje** materijala iz `dbo.fleet_trebovanja` |
| `fleet_kvar` | Prijava kvara (garaža) |
| `fleet_kvarpart` | Stavke delova uz prijavu kvara |
| `fleet_procurementrequest` | Zahtev za nabavku iz garaže (GZN) |
| `fleet_procurementitem` | Stavke zahteva |
| `fleet_kontavozila` | Šifarnik konta vozila (PK je `knt`) |

Ključevi [P]:

- `fleet_servicetransaction` i `fleet_draftservicetransaction`:
  `(datum, duguje, vez_dok, br_naloga)`.
- `fleet_requisition`: `(sif_pred, god, br_dok, sif_vrsart, stavka)` — izvorni red.

Brojevi dokumenata [P]:

| Model | Format | Kada se dodeljuje |
|---|---|---|
| `Kvar.rbz` | `PK-<pk>/<godina>` | Posle prvog upisa |
| `ProcurementRequest.number` | `GZN-<pk>/<godina>` | Posle prvog upisa |
| `VehicleTravelOrder.pn_number` | redni broj + `rbz` = `PN-<broj>` | Uz `select_for_update()` |

`Kvar.work_type`: `mali_servis`, `veliki_servis`, `popravka`. `van_ims` označava popravku
izvan IMS garaže. [P]

#### 4.4.6. Putni nalozi

##### `fleet_putninalog` — službeno putovanje zaposlenog

| Kolona | Poslovno značenje |
|---|---|
| `order_number` | **Broj naloga, jedinstven**, format `<centar>/<godina>-<redni broj>` |
| `employee_id` / `other_employee_name` | Zaposleni IMS ili spoljno lice |
| `job_code_id` | **„Troškovi idu na teret“** — organizaciona jedinica |
| `travel_location`, `task`, `contract_offer`, `napomena` | Podaci o putovanju |
| `vehicle_id` / `other_vehicle` | Vozilo IMS ili drugo prevozno sredstvo |
| `travel_date`, `number_of_days` | Period |
| `advance_payment`, `advance_payment_currency` | **Akontacija** (RSD/EUR/USD) |
| `isplaceno` | **Isplaćeno** — `editable=False`, puni sinhronizacija iz `dbo.fleet_zatvoren_putni` |
| `daily_allowance` | Dnevnica, podrazumevano **2.600** |
| `is_weekly` | Nedeljni nalog |
| `opravdan` | Pravdanje naloga |
| `storniran` | Storniran |
| `virman_generated`, `virman_generated_at`, `virman_generated_by` | Trag generisanja virmana |

Dodela broja (`generate_order_number`) [P]:

1. Uzima `center` iz izabrane OJ; bez centra — greška.
2. Prefiks je `<centar>/<godina putovanja>-`.
3. Traži najveći postojeći broj sa tim prefiksom i dodaje 1.
4. Ako za tu godinu nema nijednog, a za centar postoje raniji nalozi — kreće od 1.
5. Ako nema nijednog naloga za centar i nije zadat početni broj — **greška**:
   *„Nedostaje početni broj za izabrani centar/godinu.“*

Pomoćna tabela `fleet_putninalogsequence` drži `(center_code, year, next_number)`. [P]

> **[Z]** Numeracija se izvodi iz postojećih brojeva, a ne iz brojača, pa brisanje
> poslednjeg naloga oslobađa njegov broj za sledeći nalog.

##### `fleet_vehicletravelorder` — zaduženje vozila

Ko je i kada zadužio vozilo, sa početnom i krajnjom kilometražom.

| Kolona | Značenje |
|---|---|
| `pn_number` | Redni broj zaduženja (jedinstven) |
| `rbz` | `PN-<broj>` (jedinstven) |
| `created_at`, `closed_at` | Otvaranje i zatvaranje |
| `start_mileage`, `end_mileage` | Kilometraža |
| `employee_id`, `vehicle_id` | Ko i šta |

#### 4.4.7. Ostalo

| Tabela | Uloga |
|---|---|
| `fleet_incident` | Prekršaj: zaposleni, vozilo, opis, datum, lokacija, iznos kazne |
| `[dbo].[kasko_rate]` | `managed = False` — kasko rate po ugovoru i godini |

---

### 4.5. Kadrovi — `hr`

Izvorni kod: [`hr/models.py`](../hr/models.py), [`hr/evaluation_models.py`](../hr/evaluation_models.py)

#### `fleet_employee` — zaposleni

> Tabela je u `fleet_*` iako je model u `hr` (vidi 4.2).

| Kolona | Poslovno značenje |
|---|---|
| `employee_code` | **Šifra zaposlenog — jedinstvena.** Ključ prema kadrovskoj bazi |
| `original_full_name` | Ime i prezime kako stoji u izvoru |
| `first_name`, `last_name` | Razdvojeno ime i prezime |
| `display_first_name_override`, `display_last_name_override` | **Ispravka za prikaz** koju unosi zaposleni |
| `skip_hr_identity_update` | Ako je uključeno, sinhronizacija **ne menja** titulu, ime, prezime i pol |
| `position`, `department_code`, `org_unit_code`, `system_code`, `system_name` | Organizaciona pripadnost |
| `job_code`, `job_title` | Zanimanje |
| `status_code`, `status_name` | Status u kadrovskoj evidenciji |
| `recipient_code`, `recipient_name` | **Vrsta primaoca** — određuje elemente radne liste |
| `personal_number` | JMBG |
| `account_number` | **Partija (tekući račun)** — koristi se za virman, mora imati 18 cifara |
| `residence_municipality` | Opština boravka — ide u virman |
| `date_of_birth`, `date_of_joining`, `gender`, `address`, `education`, `slava` | Lični podaci |
| `phone_number`, `mobile_phone` | Kontakt |
| `is_active` | Aktivan |

`display_first_name` / `display_last_name` [P]: vraćaju ispravku ako postoji, inače izvorno ime.
`__str__` je `"<prezime> <ime>"`.

> **[P]** `skip_hr_identity_update` postoji jer zaposleni može ispraviti svoje ime u
> aplikaciji, a noćna sinhronizacija bi ga inače vratila na izvornu vrednost.

#### `fleet_employeecvitem` — stavka CV-a

Naziv posla/projekta, organizacija, uloga, period, opis, znanja i veštine.
Unosi je **sam zaposleni** na svom profilu. [P]

#### Radne liste

| Tabela | Uloga |
|---|---|
| `hr_worktimesheet` | Mesečna radna lista: zaposleni, godina, mesec, status |
| `hr_worktimesheetline` | Red radne liste: šifra posla + 31 kolona sati |
| `hr_worktimecategory` | Šifarnik „Vrsta rada / odsustva“ |
| `hr_worktimeelement` | Element za obračun zarada: vrsta primaoca + `payroll_code` + `payroll_name` |
| `hr_recipienttype` | Šifarnik vrsta primalaca |

`hr_worktimesheet` [P]:

- Jedinstveno `(employee, year, month)`.
- `status`: `draft` (popunjava se), `submitted` (predato), `approved` (odobreno).
- `meal_days` + `meal_organizational_unit` — **topli obrok**: broj dana i šifra posla.
- `field_allowance_days` — **terenski dodatak**: broj dana.
- `created_by`, `updated_by` — trag korisnika.

`hr_worktimesheetline` [P]:

- Jedinstveno `(sheet, line_number)`.
- Kolone `day_1` … `day_31`, svaka `0–24` (validator `MaxValueValidator(24)`).
- **Celobrojne su** — nema polovina sata.
- `work_category_id` → prikazana „napomena“ reda.
- `total_hours` = zbir svih 31 dana (prazna vrednost se računa kao 0).

`hr_worktimeelement` jedinstveno po `(recipient_type, payroll_code)`. [P]

#### Godišnji odmori

| Tabela | Uloga | Izvorni ključ |
|---|---|---|
| `hr_annualleaveallowance` | **Dodela** dana odmora po godini | `(company_code, year, employee_code)` |
| `hr_annualleavedecision` | **Rešenje** o korišćenju | `(company_code, year, employee_code, source_start_key)` |
| `hr_annualleavesync` | Istorija sinhronizacije | |

`source_start_key` je `char(26)` i čuva **tačan vremenski deo izvornog ključa**, nezavisno
od prikaza i vremenskih zona. [P] To sprečava dupliranje rešenja zbog pomeranja sata.

`hr_annualleavedecision` ima `CheckConstraint`: `end_date >= start_date`. [P]

Oba modela nasleđuju `AnnualLeaveSourceRecord` sa poljima `source_present` (da li je red
još u izvoru) i `last_seen_at`. **Nestali red se ne briše**, označi se kao odsutan. [P]

#### Bolovanja

| Tabela | Uloga |
|---|---|
| `hr_sickleaveimport` | Jedan uvoz RFZO datoteke: naziv, hash, datum izvoza, brojači |
| `hr_sickleave` | Pojedinačno bolovanje |

`hr_sickleave` [P]:

| Kolona | Značenje |
|---|---|
| `rfzo_id` | **Jedinstven ID iz RFZO izvoza** |
| `employee_id` | Veza ka zaposlenom (može biti prazna — nepovezano) |
| `personal_number` | JMBG iz izvora (osnov povezivanja) |
| `start_date`, `end_date` | Period; kraj može biti prazan (bolovanje traje) |
| `source_status`, `source_total_days`, `source_date` | Podaci iz izvora |
| `matching_note` | Kako je povezano |

`CheckConstraint`: `end_date >= start_date` ili prazno. [P]
`masked_personal_number` prikazuje samo poslednje 4 cifre JMBG-a. [P]

`file_hash` u uvozu omogućava prepoznavanje ponovljene datoteke. [P]

#### Ocenjivanje

| Tabela | Uloga |
|---|---|
| `hr_evaluationgroup` | Grupa za ocenjivanje |
| `hr_evaluationcriterion` | **Merilo** — šifra, naziv (ćirilica), redosled |
| `hr_evaluationscale` | **Skala**: grupa × merilo × bodovi (0–4) → koeficijent |
| `hr_evaluationunitsetup` | Po OJ: neposredni rukovodilac, direktor centra, generalni direktor |
| `hr_evaluationemployeesetup` | Kojoj grupi zaposleni pripada |
| `hr_employeeevaluation` | **Ocena** — nepromenljiv snimak |
| `hr_evaluationapproval` | Saglasnost po nivou |

`hr_evaluationscale` [P]: jedinstveno `(group, criterion, points)`;
`points` 0–4; `coefficient` je `decimal(8,5)`.

`hr_employeeevaluation` [P]:

| Kolona | Značenje |
|---|---|
| `employee_id`, `year`, `month`, `revision` | **Jedinstveno zajedno** |
| `unit_code` | OJ u trenutku ocenjivanja |
| `supervisor_id`, `director_id`, `general_director_id` | Potpisnici, zamrznuti u trenutku ocene |
| `snapshot` | **JSON snimak** cele ocene — merila, bodovi, opisi |
| `stimulation` | Stimulacija, `decimal(10,5)` |
| `personal_coefficient` | Lični koeficijent, `decimal(10,5)` |
| `request_key` | UUID, jedinstven — sprečava dvostruki upis istog obrasca |
| `source_evaluation_id` | Veza na prethodnu reviziju |

> **[P]** Ocena je **nepromenljiva**. Ispravka se pravi kao **nova revizija** koja
> pokazuje na izvornu. Nazivi merila se čuvaju u `snapshot`, pa kasnija izmena
> šifarnika **ne menja** ranije ocene.

`hr_evaluationapproval` [P]: jedinstveno `(evaluation, stage)`;
`stage` je `supervisor`, `director` ili `general_director`.

> **[N] Q10:** nazivi merila i opisi bodovanja u bazi su na **ćirilici**, dok je ostatak
> sistema na latinici. `hr/services/evaluations.py` ima funkcije `latin()` i `cyrillic()`
> za preslovljavanje.

---

### 4.6. Finansijska analitika — `finansije`

Izvorni kod: [`finansije/models.py`](../finansije/models.py)

#### `finansije_ledgerentry` — knjiženje (lokalna kopija izvora)

Najvažnija tabela finansijske analitike. Jedan red = **jedna izvorna stavka naloga**.

| Kolona | Izvorno polje | Poslovno značenje |
|---|---|---|
| `company` | `sif_pred` | Firma |
| `year` | `god` | Godina |
| `journal_type` | `sif_vrs` | Vrsta naloga (npr. `IF`, `ON`, `NT`, `ZAT`) |
| `journal_number` | `br_naloga` | Broj naloga |
| `line_number` | `stavka` | Stavka |
| `organizational_unit` | `oj` | **OJ knjiženja** (nije isto što i centar) |
| `account` | `knt` | Konto |
| `partner_group`, `partner_code` | `grupa`, `sif_par` | Partner |
| `document_date` | `datum` | **Datum dokumenta** |
| `booking_date` | `dat_naloga` | **Datum knjiženja** — po njemu idu prihodi/rashodi |
| `document_reference` | `vez_dok` | Veza dokumenta |
| `debit`, `credit` | `duguje`, `potrazuje` | Iznosi u RSD |
| `currency`, `foreign_amount` | `deviza`, `promena` | Valuta i devizni iznos |
| `description` | `skr_naz` | Opis |
| `linked_line` | `stavka_k` | Vezana stavka |
| `due_date` | `dpo` | Dospeće |
| `debit_credit_flag` | `d_p` | Oznaka duguje/potražuje |
| `source_paid_amount` | `placeno` | Plaćeno po izvoru |
| `job_code` | `sif_pos` | **Šifra posla** |
| `job_name`, `center` | iz `posao` | Naziv posla i **centar** (aktuelni, iz šifarnika) |
| `account_name` | iz `konto` | Naziv konta |
| `organizational_unit_name` | iz `ob_jedin` | Naziv OJ |
| `partner_name` | iz `partner` | Naziv partnera |
| `source_hash` | — | Otisak sadržaja, za prepoznavanje izmene |
| `active` | — | **Nestala stavka postaje neaktivna, ne briše se** |
| `changed_at`, `removed_at` | — | Kada je promenjena/uklonjena |

**Izvorni ključ (jedinstven):** `(company, year, journal_type, journal_number, line_number)`. [P]
Identitet **nikad ne zavisi** od iznosa ni opisa. [P]

Indeksi [P]: po periodu, centru, šifri posla, kontu i dokumentu — svi uz `company`.

> **[P] Dva datuma, dva značenja.** `booking_date` (datum knjiženja) određuje period za
> prihode i rashode; `document_date` (datum dokumenta) određuje period za fakture IF i ON.
> Mešanje ta dva datuma je najčešći uzrok neslaganja u proveri.
>
> **[P] Dva pojma „organizaciona jedinica“.** `organizational_unit` je OJ **knjiženja**,
> a `center` je centar **šifre posla** iz šifarnika. To nisu isti podaci.

#### `finansije_financejob` — šifarnik poslova

`(company, code)` jedinstveno; `name`, `center`, `active`, `profit_type`. [P]
`active` se izvodi iz izvora kao `aktivan == "D"`. [P]

#### `finansije_syncrun` — istorija sinhronizacije knjiženja

Obuhvat (`year_from`–`year_to`), brojači (`source_rows`, `created`, `updated`, `unchanged`,
`removed`), `source_totals` (kontrolni zbirovi, JSON), `latest_booking_date`, greška. [P]

#### `finansije_nalogzrefreshrun` — istorija osvežavanja `nalog_z`

| Kolona | Značenje |
|---|---|
| `trigger` | `manual` ili `celery` |
| `requested_by`, `task_id` | Ko i koji zadatak |
| `year_from`, `year_to` | Godine koje je procedura sama izabrala |
| `updated_rows`, `inserted_rows` | Brojači iz procedure |
| `status` | `running`, `success`, `failed`, `skipped`, **`unknown`** |

> **[P]** Status `unknown` („Ishod nepoznat“) dobija zapis koji je ostao nezavršen posle
> pada procesa. Tada se **mora proveriti stanje u bazi** — procedura je možda ipak prošla.
>
> **[P]** `updated_rows` broji **sve redove obuhvaćene `UPDATE`-om**, ne samo stvarno
> promenjene. Veliki broj ne znači veliku promenu.

---

### 4.7. Nabavka — `nabavka`

Izvorni kod: [`nabavka/models.py`](../nabavka/models.py). Sve tabele imaju izričit `db_table`.

#### `nabavka_procurement_case` — predmet nabavke

| Kolona | Značenje |
|---|---|
| `case_number` | **Broj predmeta, jedinstven** |
| `case_type` | `nabavka` (ZN), `usluga` (ZU), `oprema` (PLN) |
| `is_garage` | Garažni predmet → prefiks `ZNG` / `ZUG` |
| `status` | `draft`, `submitted`, `in_progress`, `waiting_invoice`, `invoice_linked`, `completed`, `cancelled` |
| `work_type` | `mali_servis`, `veliki_servis`, `popravka` |
| `garage_order_id` | Veza ka `fleet_kvar` |
| `job_code_id` | OJ / šifra posla |
| `supplier_id`, `contract_id`, `vehicle_id`, `responsible_id` | Veze |
| `estimated_value`, `currency` | Procenjena vrednost (RSD/EUR/USD/CHF) |
| `needed_by` | Datum zahteva |

Format broja [P]: `<prefiks>-<centar>/<godina>-<redni broj>`,
npr. `ZN-43/2026-17`, `ZNG-43/2026-3`. Godina se uzima iz `created_at`.
Bez centra u OJ — greška *„Nedostaje sifra centra za broj zahteva.“*

#### `nabavka_procurement_item` — stavka predmeta

`name`, `uom`, `quantity`, `estimated_unit_price`, `note`.
`estimated_total` = cena × količina (prazno ako bilo šta nedostaje). [P]

**Povezivanje sa izvorom** [P]: `source_type` je `euf`, `uf` ili `goods`, a odgovarajuća
veza mora biti **tačno jedna**:

| `source_type` | Veza |
|---|---|
| `euf` | `euf_invoice_id` → `nabavka_invoice` |
| `uf` | `uf_invoice_id` → `nabavka_uf_invoice_snapshot` (ili `uf_item_id`) |
| `goods` | `goods_item_id` → `nabavka_goods_snapshot` |

`clean()` odbija i stavku sa tipom bez veze i stavku sa vezom bez tipa. [P]

#### Snimci izvora

| Tabela | Izvor | Ključ |
|---|---|---|
| `nabavka_invoice` | `dbo.nbv_preuzete_EUF` | `(source, euf_key)` |
| `nabavka_euf_item_snapshot` | `dbo.nbv_EUF_stavke` | `source_key` |
| `nabavka_uf_invoice_snapshot` | izvedeno grupisanjem stavki | `source_key` |
| `nabavka_goods_snapshot` | `dbo.nbv_roba` | `source_key` |

`nabavka_invoice` (EUF faktura) dodatno nosi operativne oznake koje unosi korisnik [P]:
`job_code_id`, `job_code_source`, `vehicle_job_code_assigned_date`, `is_garage`,
`work_type`, `vehicle_id`, `goes_to_warehouse`, `is_returned`, `internal_note`.

> **[P]** `job_code_source = "vehicle_snapshot"` znači da šifra posla **nije** uneta ručno
> nego preuzeta iz istorijske dodele vozila na datum `vehicle_job_code_assigned_date`.

#### Veze

| Tabela | Šta povezuje | Jedinstveno |
|---|---|---|
| `nabavka_invoice_link` | Predmet ↔ EUF ključ | `(procurement_case, source, euf_key)` |
| `nabavka_item_invoice_link` | Stavka ↔ faktura | stavka je `OneToOne` |
| `nabavka_invoice_job_code_link` | Faktura ↔ šifra posla (`primary`/`additional`) | `(invoice, job_code)` |
| `nabavka_contract_link` | Predmet ↔ ugovor | `(procurement_case, contract)` |
| `nabavka_invoice_contract_link` | Faktura ↔ kupovni ugovor | `(invoice, contract)` |

`sync_primary_job_code_link()` [P]: kad se promeni `job_code` fakture, stara osnovna veza
se **briše ako nije vraćena**, a ako **jeste vraćena** — prelazi u „dodatnu“, da se trag
vraćanja ne izgubi.

#### Plan javnih nabavki

| Tabela | Uloga |
|---|---|
| `nabavka_public_procurement_plan_version` | Verzija plana za godinu: `(year, version_number)` jedinstveno, + brojači razlika |
| `nabavka_public_procurement_plan_item` | Stavka plana |

Stavka [P]: `plan_type` (`public` / `exempt`), `diff_status`
(`added`, `changed`, `unchanged`, `removed`), `stable_key`, `content_hash`,
`previous_item_id` (veza na istu stavku u prethodnoj verziji), `raw_data` (JSON izvorni red).
Jedinstveno `(version, stable_key)`.

> **[P]** Uklonjena stavka se **prepisuje u novu verziju** sa statusom `removed`,
> da bi plan ostao potpun.

#### Ostalo

| Tabela | Uloga |
|---|---|
| `nabavka_purchase_order` | Narudžbenica: broj (jedinstven), datum, dobavljač, ugovor, status, iznos |
| `nabavka_status_log` | Promena statusa predmeta: stari, novi, komentar, ko i kada |

---

### 4.8. Potraživanja — `potrazivanja`

Izvorni kod: [`potrazivanja/models.py`](../potrazivanja/models.py)

Modul je projektovan oko tri načela [P]:

1. **Identitet po izvoru** — svaki preuzeti zapis ima stabilan izvorni ključ.
2. **Nepromenljivi snimci** — stanje se objavljuje, ne prepisuje.
3. **Potpuna sledljivost** — svaki prenos ima svoj `run`, korak, kontrolne zbirove i greške.

#### Sinhronizacija

| Tabela | Uloga |
|---|---|
| `potrazivanja_collectionsyncrun` | Jedan prenos: status, obuhvat, brojači, kontrolni zbirovi, greška |
| `potrazivanja_collectionsyncstep` | Korak prenosa: `(run, code)` jedinstveno, brojači po koraku |
| `potrazivanja_sourcedataset` | **Nepromenljiv snimak celog izvora**: `(name, fingerprint)` |
| `potrazivanja_sourcerow` | Red snimka: `(dataset, ordinal)` |
| `potrazivanja_legacyimportmap` | Mapa nasleđeni zapis → novi zapis |
| `potrazivanja_importissue` | Problem pri prenosu: šifra, ozbiljnost, poruka, rešenje |

> **[P]** `SourceDataset` se **ponovo koristi samo za identičan sadržaj** (isti `fingerprint`).
> Ponovljena sinhronizacija istih podataka ne stvara novi snimak.

#### Partneri i dokumenti

| Tabela | Uloga | Ključ |
|---|---|---|
| `potrazivanja_financepartneridentity` | **Identitet partnera** u finansijama | `(source_system, company, partner_group, partner_code)` |
| `potrazivanja_collectionprofile` | Oznake partnera: važan kupac, potrebna provera, vlasnik | `identity` 1:1 |
| `potrazivanja_invoicedocument` | Faktura | `(source_system, company, source_key)` |
| `potrazivanja_receivableposting` | **Knjiženje potraživanja** | `(source_system, company, year, journal_type, journal_number, line_number)` |
| `potrazivanja_duedateevidence` | Dokaz dospeća iz uvozne serije | `(import_run, source_table, source_key, occurrence)` |

Kontrole doslednosti u `clean()` [P]:

- Dokument i partner moraju biti ista firma.
- Knjiženje i partner moraju imati isti izvorni ključ.
- Dokument i knjiženje moraju imati istu firmu **i** istog partnera.
- Dokaz dospeća mora odgovarati firmi, grupi i šifri partnera.

#### Snimci stanja

| Tabela | Uloga |
|---|---|
| `potrazivanja_balancesnapshot` | Snimak: `(run, company, as_of_date)`, status `draft`/`validated`/`published` |
| `potrazivanja_receivableposition` | **Pozicija** u snimku |
| `potrazivanja_collectionstate` | Aktivno stanje po firmi — pokazuje na **objavljeni** snimak |
| `potrazivanja_agingrule` | Starosni razred: `min_days`, `max_days`, redosled, predložena radnja |

`ReceivablePosition` [P]:

| Kolona | Značenje |
|---|---|
| `identity_id`, `document_id`, `reference` | Partner i dokument |
| `job_code`, `center_code` | Šifra posla i centar |
| `account_family` | Grupa konta (3 znaka) |
| `debit`, `credit`, `balance` | **`balance` mora biti tačno `ROUND(debit − credit, 2)`** — provereno `CheckConstraint`-om u bazi |
| `due_date`, `due_date_method`, `due_date_evidence_id` | Dospeće, **način kako je utvrđeno** i dokaz |
| `resolution_details` | JSON sa objašnjenjem razrešenja |

Jedinstveno: `(snapshot, identity, reference, job_code, account_family)`. [P]

`BalanceSnapshot` ima `CheckConstraint` [P]: `published_at` je popunjen **ako i samo ako**
je status `published`.

`CollectionState.clean()` [P]: aktivno stanje mora biti **objavljen** snimak **iste firme**.

> **[P]** `due_date_method` i `due_date_evidence` postoje jer dospeće nije uvek u izvoru —
> sistem beleži **kako** je do njega došao, da bi rezultat bio proveriv.

#### Operativne evidencije

| Tabela | Uloga |
|---|---|
| `potrazivanja_collectioncontact` | Kontakt kod partnera, sa razdvojenim imenom/prezimenom/funkcijom |
| `potrazivanja_contactpoint` | Pojedinačan telefon / mobilni / e-pošta: `(contact, kind, value)` jedinstveno |
| `potrazivanja_collectionactivity` | Napomena ili telefonski poziv, sa ishodom i sledećom radnjom |
| `potrazivanja_collectionnotice` | Opomena, pozivno pismo ili nasleđena evidencija tužbe |
| `potrazivanja_collectionnoticeitem` | Stavka opomene: `(notice, line_number)` |
| `potrazivanja_electronicinvoicestatus` | Status fakture na SEF-u |
| `potrazivanja_collectionlegalcase` | **Pravni postupak** |
| `potrazivanja_collectionlegalevent` | Promena u postupku |
| `potrazivanja_legalcaselink` | Veza ka nasleđenom ID-u postupka |
| `potrazivanja_collectionaudit` | Revizorski trag: entitet, ID, akcija, pre/posle (JSON) |
| `potrazivanja_collectionfileimport` | Uvoz Excel datoteke: `fingerprint` jedinstven |

`CollectionContact` [P]: `original_data` (JSON) čuva izvorni zapis, `needs_review` označava
kontakt koji treba proveriti, `import_parent` povezuje kontakte nastale **razdvajanjem**
jednog nasleđenog zapisa sa više adresa.

`CollectionLegalCase` [P]: `tip` je `tuzeni`, `tuzili`, `stecaj` ili `uppr`; polja se
koriste u zavisnosti od tipa (osnovni dug, kamata, troškovi, ukupan dug, vrednost spora,
datum otvaranja stečaja, prijava potraživanja…). `original_data` čuva nasleđeni zapis.

`CollectionFileImport.fingerprint` je jedinstven — **ponovljeni uvoz iste datoteke
ne stvara duple opomene**. [P]

---

### 4.9. Ugovori — `ugovori`

Izvorni kod: [`ugovori/models.py`](../ugovori/models.py)

#### `ugovori_partner`

| Kolona | Značenje |
|---|---|
| `partner_type` | `legal_entity`, `person`, `bank` |
| `residency` | `domestic`, `foreign` |
| `external_sif_par` | **Šifra iz starog sistema** — veza sa knjigovodstvom |
| `pib`, `maticni_broj`, `jmbg`, `passport_number`, `foreign_tax_id` | Identifikatori |
| `data_source`, `data_validated`, `data_validated_at` | Poreklo i validacija podataka |
| `apr_status`, `apr_checked_at` | **Status iz APR-a** i kada je proveren |

Kontrole [P]: domaće pravno lice mora imati PIB i/ili matični broj;
domaće fizičko lice mora imati JMBG.

#### `ugovori_contract`

| Kolona | Značenje |
|---|---|
| `kind` | `MAIN` (glavni ugovor) ili `ANNEX` (aneks) |
| `parent_contract_id` | Obavezan za aneks, zabranjen za glavni |
| `contract_number` | **Jedinstven** |
| `contract_type_id` | Tip iz šifarnika |
| `contract_date`, `valid_from`, `valid_to` | Datumi |
| `value`, `value_type`, `unit_price`, `unit_label`, `currency` | Vrednost |
| `status` | `draft`, `active`, `expired`, `terminated`, `archived` |
| `has_incoming_menice`, `has_outgoing_menice`, `has_guarantees` | Oznake instrumenata |

`value_type` [P]: `fixed`, `hourly`, `monthly`, `man_month`, `unit`, `undefined`.

Kontrole [P]: aneks mora imati glavni ugovor; glavni ne sme imati nadređeni;
nadređeni mora biti tipa `MAIN`; ugovor ne može biti sam sebi nadređen;
`valid_to` ne sme biti pre `valid_from`.

#### Ostalo

| Tabela | Uloga |
|---|---|
| `ugovori_contract_type` | Šifarnik tipova (šifra jedinstvena) |
| `ugovori_business_request` | Zahtev: broj (jedinstven), tip, predmet, status, fajl |
| `ugovori_offer` | Ponuda: broj (jedinstven), smer (naša / data nama), vrednost, status |
| `ugovori_contract_document` | Dokument uz ugovor (tip, opis, fajl, originalni naziv) |
| `ugovori_contract_party` | Stranka ugovora: `(contract, partner, role)` jedinstveno |
| `ugovori_contract_guarantee` | Garancija: broj, izdavalac, korisnik, iznos, period, status |
| `ugovori_contract_menica_link` | Veza ugovora i menice — **tačno jedna** od (`menica`, `ulazna_menica`) |

---

### 4.10. Menice — `menice`

Izvorni kod: [`menice/models.py`](../menice/models.py). Tabele: **`menica`** i **`ulazna_menica`** (bez prefiksa).

#### `menica`

Zapis iz Registra menica NBS ili ručni unos.

| Kolona | Značenje |
|---|---|
| `tip` | `izlazna` ili `ulazna` |
| `serijski_broj_menice` | Serijski broj (indeksiran) |
| `sifra_partnera`, `naziv_duznika`, `maticni_broj_duznika`, `poreski_broj_duznika` | Dužnik |
| `datum_izdavanja`, `datum_dospeca`, `datum_registracije` | Datumi |
| `iznos_menice`, `valuta_menice` | Iznos |
| `osnov_izdavanja`, `iznos_iz_osnova`, `valuta_osnova` | Osnov |
| `avalisti_detalji`, `avalisti_broj_zapisa` | Avalisti iz registra |
| `broj_ugovora`, `datum_ugovora`, `oj` | Veza sa poslom |
| `fizicka_lokacija` | **`centar` ili `blagajna`** — gde se menica fizički nalazi |
| `interni_status` | `0` aktivna, `1` obrisana, `2` nepoznat |

#### `ulazna_menica`

Menica primljena od partnera, sa vlastitim skupom polja.

| Kolona | Značenje |
|---|---|
| `serijski_broj_menice` | Serijski broj |
| `jedinica_vrednosti` | **`RSD`, `EUR` ili `PROCENAT`** |
| `procenat_iznos` | Iznos ili procenat, zavisno od jedinice |
| `sifra_poslovnog_partnera`, `naziv_pravnog_lica` | Partner |
| `broj_naseg_ugovora`, `datum_ugovora`, `ugovor_vazi_do` | Naš ugovor |
| `lokacija_menice`, `sifra_centra` | Gde se nalazi |

> **[P]** `jedinica_vrednosti = PROCENAT` znači da `procenat_iznos` **nije novčani iznos**
> nego procenat vrednosti ugovora. Sabiranje te kolone bez provere jedinice daje besmislen zbir.

---

### 4.11. Mobilna telefonija — `mobilni`

Izvorni kod: [`mobilni/models.py`](../mobilni/models.py)

| Tabela | Uloga | Jedinstveno |
|---|---|---|
| `mobilni_mobilepackage` | Paket: naziv, period, neto i bruto iznos, ugovor | `(partner_code, name, valid_from)` |
| `mobilni_mobileuser` | Korisnik iz izvora operatera | `employee_code` |
| `mobilni_mobileassignment` | **Dodela broja za mesec** | `(year, month, phone_number)` |
| `mobilni_mobileusage` | **Potrošnja za mesec** | `(year, month, phone_number)` |
| `mobilni_mobileparkingexemption` | Broj izuzet od parkinga | `phone_number` |
| `mobilni_mobileimportlog` | Log uvoza | |

#### `mobilni_mobileuser.link_status` [P]

| Vrednost | Značenje |
|---|---|
| `auto` | Automatski povezan sa zaposlenim |
| `manual` | Ručno povezan |
| `unmatched` | Nije povezan |
| `non_employee` | **Nije zaposleni** — namerno se ne povezuje |
| `ambiguous` | Više mogućih zaposlenih |

#### `mobilni_mobileusage` — kolone koje ulaze u obračun [P]

`vat_base` (osnovica za PDV), `parking`, `nzrd`, `total` (ukupno za naplatu),
`vat` (PDV), `installments` (plaćanje na rate), plus 20 kolona vrsta saobraćaja
(`onnet`, `mts_network`, `outside_mts`, `kim`, `special`, `international`, `roaming`,
`gprs`, `sms`, `sms_international`, `sms_roaming`, `mms`, `vas_sms`, `discount_traffic`,
`fixed_discount`, `variable_discount`, `services`, `dispatch_notes`).

> **[P]** Obustava se računa iz **`vat_base`, `parking` i `nzrd`** — ne iz `total`.
> Vidi obračun M-01.

#### Razrešavanje zaposlenog [P]

`MobileAssignment.linked_employee` ide ovim redom:

1. Ako postoji `mobile_user` sa `link_status = non_employee` → **nema zaposlenog**.
2. Ako `mobile_user` ima zaposlenog → taj zaposleni.
3. Inače, ako dodela ima direktnu vezu `employee` → taj zaposleni.
4. Inače → nema zaposlenog.

Prikaz šifre i imena pada nazad na `source_employee_code` i `source_full_name` iz izvora.

---

### 4.12. Nasleđeni objekti baze (`dbo.*`)

> **[N] Sadržaj ovih objekata nije potvrđen** — definicije nisu u repozitorijumu.
> DDL se očekuje; do tada važi samo ono što je potvrđeno kodom koji ih čita ili
> postojećom dokumentacijom.

#### 4.12.1. Izvori za Flotu

| Objekat | Kolone koje aplikacija čita | Šta radi sa njima |
|---|---|---|
| `dbo.fleet_otpis` | `inv_br` | Postavlja `Vehicle.otpis = True` po inventarskom broju |
| `dbo.vrednost_vozila` | `sif_osn`, `sad_vrednost` | Upisuje `Vehicle.value` |
| `dbo.sif_pos_trenutno` | `regbr`, `sifpos` | Nova `JobCode` dodela ako se razlikuje od poslednje |
| `dbo.v_organizationalunit` | `sif_pos`, `naz_pos`, `blok` | Puni `OrganizationalUnit` |
| `dbo.fleet_potrazivanje_ddor` | `god`, `sif_vrs`, `br_naloga`, `stavka`, `oj`, `knt`, `datum`, `vez_dok`, `potrazuje`, `kola` | Stvara `DraftInsurance` |
| `dbo.fleet_servisi` | — | Puni `ServiceTransaction` / `DraftServiceTransaction` |
| `dbo.fleet_trebovanja` | — | Puni `Requisition` |
| `dbo.fleet_zatvoren_putni` | — | Puni `PutniNalog.isplaceno` |
| `dbo.lizing_kamate` | — | Puni `LeaseInterest` |
| `dbo.kasko_rate` | `contract_number`, `year`, `rate` | Model `KaskoRate` (`managed = False`) |

#### 4.12.2. Izveštajni pogledi Flote

Ovih devet pogleda se čita **bez ijedne transformacije u Pythonu** — cela formula je u bazi.
Zato je njihov DDL **prioritet 1** za dokumentaciju obračuna. [P]

| Pogled | Ekran |
|---|---|
| `dbo.fleet_tro_svi` | `/izvestaji/troskovi_svi/` |
| `dbo.fleet_tro_goriva_m` | `/izvestaji/tro_gorivo_mesec/` |
| `dbo.fleet_tro_pracenje` | `/izvestaji/tro_pracenja_vozila/` |
| `dbo.fleet_tro_taho` | `/izvestaji/troskovi_tahograf/` |
| `dbo.fleet_tro_parking` | `/izvestaji/tro_parking/` |
| `dbo.tro_zarade` | `/izvestaji/tro_zarade/` |
| `dbo.fleet_dobavljaci` | `/izvestaji/po_dobavljacima/` |
| `dbo.fleet_magacin_rez` | `/izvestaji/magacin/` |
| `dbo.kasko_rate` | `/izvestaji/kasko_rate/` |

#### 4.12.3. Izvori za ostale module

| Objekat | Koristi ga |
|---|---|
| `dbo.nbv_preuzete_EUF` | Nabavka — EUF fakture |
| `dbo.nbv_EUF_stavke` | Nabavka — UF stavke |
| `dbo.nbv_roba` | Nabavka — roba |
| `dbo.nbv_sif_pos_par` | Nabavka — provera šifre posla partnera |
| `dbo.hr_employee` | Kadrovi — zaposleni, vrste primalaca |
| `dbo.partneri` | Ugovori — sinhronizacija partnera |
| `dbo.posao` (na `PUTGEO-SERVER.bazaims`) | Potraživanja, Finansije |

#### 4.12.4. Procedura `IMS_ERP.dbo.sp_AzurirajNalogZ`

Ponašanje potvrđeno ranijim čitanjem definicije
(izvor: `naplata-lokalni-izvor-plan.md`, poglavlje 2; dokument uklonjen 18.09.2026., u git istoriji `06f60c2`). [P]

| Osobina | Vrednost |
|---|---|
| Parametri | Nema ih |
| Izvor | `PUTGEO-SERVER.BazaIMS.dbo.nalog_z` → privremena tabela |
| Obuhvat godina | Do uključivo 30. aprila: prethodna i tekuća; posle toga samo tekuća |
| Obuhvat firmi | **Sve firme** (nema `sif_pred=1`) |
| Kontrole | NULL vrednosti i duplikati ključa firma/godina/vrsta/broj/stavka |
| Upis | U transakciji: `UPDATE` postojećih + `INSERT` novih u `IMS_ERP.dbo.nalog_z` |
| Vraća | `OdGodine`, `DoGodine`, `BrojAzuriranihRedova`, `BrojDodatihRedova` |

**Dva ograničenja koja korisnik mora znati [P]:**

1. **Ne briše** redove obrisane u izvoru — uspešno izvršavanje **ne znači** da je lokalna
   kopija jednaka izvoru.
2. `BrojAzuriranihRedova` broji sve redove obuhvaćene `UPDATE`-om, ne samo promenjene.

**Nema indeksa** sa kolonama na lokalnom `nalog_z` prema pregledanim metapodacima. [P]

Pokreće se samo kroz `finansije/services/nalog_z.py`, uz `sp_getapplock` u istoj sesiji. [P]

---

### 4.13. Nasleđeni modul Naplata — van obuhvata

Modul `naplata` ima 12 modela sa `managed = False` nad pogledima
(`baza`, `dodela_bucketa`, `ispravke`, `partneri`, `kontakti`, `napomene`, `opomene`,
`poziv_pismo`, `pozivi_tel`, `sif_baket`, `sif_kategorija`, `tuzbe`) i 3 sopstvene tabele
(`avans_klijent`, `postupak`, `promena_postupka`).

Odlukom naručioca **nije predmet ove dokumentacije.** Zamenjuje ga modul Potraživanja.
Vidi [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) i [11. Plan razvoja](#11-plan-razvoja).

> **[P] Poznata neusaglašenost:** model navodi `dodela_bucketa`, a stvarni upiti u
> `naplata/queries.py` koriste **`dodela_baketa`**. Ne preimenovati aktivni pogled
> na osnovu modela — model je taj koji je pogrešan.

---

### 4.14. Kontrolna pravila koja baza sama proverava

Ova pravila su `CheckConstraint` ili `UniqueConstraint` u bazi — ne mogu se zaobići
ni ručnim upisom kroz aplikaciju. [P]

| Tabela | Pravilo |
|---|---|
| `fleet_vehicleholding` | `end_date >= start_date` ili prazno |
| `fleet_jobcode` | Jedno vozilo ne može imati dve dodele istog datuma |
| `hr_annualleavedecision` | `end_date >= start_date` |
| `hr_sickleave` | `end_date >= start_date` ili prazno |
| `hr_employeeevaluation` | `month` između 1 i 12; jedna revizija po zaposlenom/mesecu |
| `hr_evaluationapproval` | Jedna saglasnost po nivou za istu ocenu |
| `potrazivanja_receivableposition` | **`balance = ROUND(debit − credit, 2)`** |
| `potrazivanja_balancesnapshot` | `published_at` popunjen ↔ status je `published` |
| `potrazivanja_collectionsyncrun` | `finished_at >= started_at` |
| `potrazivanja_collectionnoticeitem` | `line_number >= 1` |
| `potrazivanja_duedateevidence` | `occurrence >= 1` |
| `potrazivanja_agingrule` | `max_days >= min_days` |
| `finansije_ledgerentry` | Jedinstven izvorni ključ stavke naloga |

---

### 4.15. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako se podaci preuzimaju iz ovih izvora? | [7. Integracije](#7-integracije) |
| Kako se iz ovih tabela računaju iznosi? | [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj) |
| Šta koji modul radi sa ovim tabelama? | [3. Moduli](#3-moduli--sadržaj-i-veze) |

---

## 5. Poslovni procesi

> **Za koga je ovo poglavlje:** poslovni korisnici i programeri.
> Ovde je opisano **kako posao teče kroz sistem od početka do kraja**, kroz više modula.
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 5.0. Spisak procesa

| # | Proces | Moduli | Pokreće ga |
|---|---|---|---|
| [1](#51-popravka-vozila--od-kvara-do-troška) | **Popravka vozila** — od kvara do troška | Flota → Nabavka → Flota | Vozač / garaža |
| [2](#52-službeno-putovanje--od-naloga-do-isplate) | **Službeno putovanje** — od naloga do isplate | Flota → Isplate → Banka | Zaposleni |
| [3](#53-zaduženje-vozila--od-preuzimanja-do-obračuna) | **Zaduženje vozila** — od preuzimanja do obračuna | Flota | Zaposleni |
| [4](#54-mesečni-obračun-mobilnih-telefona) | **Mesečni obračun mobilnih telefona** | Mobilni → Zarade | Administracija |
| [5](#55-mesečna-radna-lista-i-ocenjivanje) | **Mesečna radna lista i ocenjivanje** | Kadrovi → Zarade | Zaposleni |
| [6](#56-noćno-preuzimanje-podataka) | **Noćno preuzimanje podataka** | Svi | Sistem |
| [7](#57-naplata-potraživanja) | **Naplata potraživanja** | Potraživanja | Služba naplate |
| [8](#58-zaključenje-ugovora) | **Zaključenje ugovora** | Ugovori → Menice | Pravna služba |
| [9](#59-mesečno-praćenje-rezultata) | **Mesečno praćenje rezultata** | Finansije | Rukovodioci |

---

### 5.1. Popravka vozila — od kvara do troška

> **Najsloženiji proces u sistemu** — prolazi kroz tri modula i dva izvora podataka.

#### Pokretački događaj

Vozač prijavljuje kvar na vozilu, ili dolazi red na servisni interval.

#### Odgovorni korisnici

Garaža (prijava i radni nalog), služba nabavke (predmet i faktura),
služba voznog parka (kontrola troška).

#### Potrebni ulazni podaci

| Podatak | Obavezno |
|---|---|
| Vozilo | Da |
| Kilometraža | Da |
| Opis kvara | Da |
| Vrsta intervencije (mali/veliki servis, popravka) | Da |
| Popravka van IMS-a | Da/Ne |

#### Redosled aktivnosti [P]

```
 1. GARAŽA: prijava kvara              →  fleet_kvar,  broj PK-<id>/<godina>
 2. GARAŽA: stavke delova              →  fleet_kvarpart
 3. GARAŽA: štampa prijave i radnog naloga
 4. GARAŽA: trebovanje materijala      →  štampa
        │
        ├─── popravka u IMS garaži ────► materijal iz magacina
        │                                 dbo.fleet_trebovanja → fleet_requisition (01:45)
        │
        └─── popravka van IMS-a ───────► 5. zahtev za nabavku
 5. NABAVKA: predmet nabavke           →  nabavka_procurement_case
        broj ZNG-<centar>/<godina>-<broj>, vezan za kvar i vozilo
 6. NABAVKA: stavke predmeta           →  nabavka_procurement_item
 7. NABAVKA: statusi                   →  Nacrt → Podneto → U obradi → Čeka fakturu
 8. NABAVKA: narudžbenica (po potrebi) →  nabavka_purchase_order
 9. DOBAVLJAČ izdaje fakturu
10. SISTEM: preuzima EUF fakturu       →  nabavka_invoice (02:20)
11. NABAVKA: povezuje fakturu sa stavkom → nabavka_item_invoice_link
        status → Faktura povezana → Završeno
12. NABAVKA: označava šifru posla i vozilo na fakturi
13. SISTEM: knjiženje servisa          →  dbo.fleet_servisi → fleet_servicetransaction (03:15)
14. FLOTA: dopunjava kategoriju popravke i vezu sa vozilom
15. FLOTA: trošak ulazi u analitiku    →  trošak po kilometru
```

#### Promene statusa [P]

| Objekat | Statusi |
|---|---|
| Predmet nabavke | `Nacrt → Podneto → U obradi → Čeka fakturu → Faktura povezana → Završeno` (ili `Otkazano`) |
| Knjiženje servisa | Nedovršeno (draft) → konačno |

#### Tabele kroz koje podaci prolaze

`fleet_kvar` → `fleet_kvarpart` → `nabavka_procurement_case` →
`nabavka_procurement_item` → `nabavka_invoice` → `nabavka_item_invoice_link` →
`fleet_servicetransaction` / `fleet_requisition`

#### Obračuni koji se izvršavaju

| Obračun | Kada |
|---|---|
| [B-01](#69-nabavka--obračuni-i-analize) Procenjena vrednost | Pri unosu stavki |
| [B-03](#69-nabavka--obračuni-i-analize) Ključ EUF fakture | Pri preuzimanju |
| [V-14](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji) Održavanje vozila | Pri otvaranju detalja vozila |
| [V-10](#63-flota--troškovi-vozila) Neto trošak održavanja | U analitici |
| [V-07](#63-flota--troškovi-vozila) Trošak po kilometru | U analitici |

#### Dokumenti koji nastaju

| Dokument | Gde |
|---|---|
| Prijava kvara | `/garaza/kvarovi/<id>/prijava/` |
| **Radni nalog** | `/garaza/kvarovi/<id>/radni-nalog/` |
| **Trebovanje materijala** | `/garaza/kvarovi/<id>/trebovanje/` |
| Zahtev za nabavku | `/nabavka/zahtevi/<id>/stampaj/` |
| Trebovanje materijala (nabavka) | `/nabavka/zahtevi/<id>/trebovanje-materijala/` |

#### Kontrole [P]

| Kontrola | Gde |
|---|---|
| Broj predmeta traži **centar** organizacione jedinice | Pri čuvanju |
| Stavka mora imati **tačno jedan** izvor | `ProcurementItem.clean()` |
| Faktura dodeljena drugom vozilu **ne ulazi** u dokaze o održavanju | `vehicle_maintenance()` |
| Sukob kategorije ili datuma | Oznaka **„Proveriti kategoriju / datum“** |

#### Moguće greške

| Greška | Posledica |
|---|---|
| Vozilo nema šifru posla | Predmet se **ne može numerisati** |
| Faktura ispravljena u izvoru | **Nastaje dvojnik** — [P-39](#10-poznati-problemi-i-ograničenja) |
| UF faktura nestala iz izvora | **Veza tiho nestaje** — [P-37](#10-poznati-problemi-i-ograničenja) |
| Knjiženje servisa bez vozila | Ostaje u „nedovršeno“, trošak nije na vozilu |

#### Završni rezultat

Trošak popravke je **pripisan vozilu i šifri posla**, vidi se na detalju vozila i
ulazi u trošak po kilometru.

#### Podaci za knjiženje

> **[N] Q3:** knjiženje nastaje u nasleđenom ERP-u; sistem ga **samo preuzima**.
> Nije potvrđeno da li se neki podatak iz sistema prenosi u knjiženje.

---

### 5.2. Službeno putovanje — od naloga do isplate

#### Pokretački događaj

Potreba za službenim putovanjem.

#### Odgovorni korisnici

Sekretarijat (nalog), blagajna (virman), zaposleni (pravdanje).

#### Redosled aktivnosti [P]

```
 1. SEKRETARIJAT: putni nalog          →  fleet_putninalog
        broj <centar>/<godina>-<redni broj>
        zaposleni, mesto, zadatak, dani, vozilo, AKONTACIJA, valuta, dnevnica
 2. SEKRETARIJAT: štampa naloga        →  obrazac za zaposlenog
        (+ prilog za inostranstvo ako treba)
 3. BLAGAJNA: bira naloge za isplatu   →  /isplate/
 4. BLAGAJNA: zadaje datum virmana
 5. SISTEM: kontrole (9 provera)       →  I-02
 6. SISTEM: datoteka virmana           →  180 znakova po redu, cp1250
        upisuje: virman_generated, _at, _by
 7. BLAGAJNA: učitava datoteku u elektronsko bankarstvo
 8. BANKA: izvršava plaćanja           →  zaposleni prima akontaciju
 9. ZAPOSLENI: putuje i pravda nalog
10. SEKRETARIJAT: označava „Opravdan“
11. SISTEM: puni „Isplaćeno“           →  dbo.fleet_zatvoren_putni (12:30)
```

#### Promene statusa [P]

| Oznaka | Značenje |
|---|---|
| `virman_generated` | Virman je napravljen |
| `opravdan` | Nalog je pravdan |
| `storniran` | Nalog je storniran — **ne ulazi u virman** |

#### Obračuni

| Obračun | Napomena |
|---|---|
| [I-02](#610-isplate--virmani) Kontrole naloga | Devet provera, sve greške zajedno |
| [I-01](#610-isplate--virmani) Generisanje virmana | Iznos u parama, poziv na broj |

#### Dokumenti koji nastaju

| Dokument | Gde |
|---|---|
| Putni nalog | `/putni-nalozi/<id>/print/` |
| Prilog za inostranstvo | `/putni-nalozi/<id>/prilog-inostranstvo/` |
| **Datoteka virmana** | Preuzimanje sa `/isplate/` |

#### Kontrole [P]

| Kontrola | Poruka |
|---|---|
| Nalog nije storniran | *„nalog je storniran“* |
| Virman nije već rađen | *„virman je vec odradjen“* |
| **Valuta je RSD** | *„valuta mora biti RSD“* |
| **Zaposleni je iz IMS-a** | *„nalog nema IMS zaposlenog“* |
| **Račun ima 18 cifara** | *„racun mora imati 18 cifara“* |
| Iznos veći od nule | *„Iznos mora biti veci od nule“* |

#### Moguće greške

| Greška | Posledica |
|---|---|
| Nema početnog broja za centar i godinu | Nalog se **ne može otvoriti** |
| Zaposleni nema partiju | Nalog **ne ulazi** u virman |
| **Ime duže od 35 znakova** | **Skraćuje se bez upozorenja** — [P-33](#10-poznati-problemi-i-ograničenja) |
| **Mesto duže od 10 znakova** | Skraćuje se — „Novi Beograd“ → „Novi Beogr“ |
| Nema opštine boravka | Upisuje se **„Beograd“** |

#### Podaci za knjiženje

| Ko preuzima | Šta | Odakle |
|---|---|---|
| **Banka** | Datoteka virmana | `/isplate/` |
| Knjigovodstvo | **[N] Nije potvrđeno** | — |

#### Završni rezultat

Zaposleni je primio akontaciju, nalog je označen kao isplaćen i pravdan.

---

### 5.3. Zaduženje vozila — od preuzimanja do obračuna

#### Pokretački događaj

Zaposleni preuzima vozilo.

#### Redosled aktivnosti [P]

```
 1. ZAPOSLENI: otvara zaduženje        →  fleet_vehicletravelorder
        broj PN-<redni broj>, POČETNA KILOMETRAŽA
 2. SISTEM: automatski ZATVARA ranija otvorena zaduženja tog vozila
        njihova krajnja kilometraža = početna kilometraža novog naloga
 3. ZAPOSLENI: koristi vozilo, toči gorivo
 4. SISTEM: preuzima transakcije goriva (04:20 / 05:10 / 06:10)
 5. GARAŽA ili ZAPOSLENI: zatvara zaduženje  →  KRAJNJA KILOMETRAŽA
 6. SISTEM: obračun goriva             →  V-23
 7. ZAPOSLENI: štampa obračun
```

#### Obračuni

| Obračun | Formula |
|---|---|
| [V-23](#62-flota--obračuni-goriva) Obračun goriva | `litri / pređeni put × 100` |
| [V-13](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji) Kilometraža | Očitavanja iz zaduženja ulaze u vremensku liniju |

#### Kontrole i moguće greške

| Slučaj | Ponašanje |
|---|---|
| Nalog nije zatvoren | Obračun ide **do današnjeg dana**, menja se svakog dana |
| Vozilo promenilo tablice | **Transakcije sa stare tablice mogu nedostajati** |
| Više otvorenih zaduženja | Ista transakcija ulazi u **oba** obračuna |
| Preko 60 transakcija | **Štampa se samo prvih 60** |
| Zatvoreno zaduženje | Menja ga **samo superuser** |

#### Završni rezultat

Poznato je ko je koristio vozilo, koliko je prešao i koliko goriva potrošio.

---

### 5.4. Mesečni obračun mobilnih telefona

#### Pokretački događaj

Stigao je mesečni račun operatera.

#### Odgovorni korisnik

Administracija.

#### Redosled aktivnosti [P]

```
 1. OPERATER: dostavlja 4 Excel datoteke
 2. ADMINISTRACIJA: uvozi paketе i korisnike    →  /mobilni/import/
 3. ADMINISTRACIJA: uvozi DODELE za mesec       →  uz godinu i mesec
 4. ADMINISTRACIJA: uvozi POTROŠNJU za mesec    →  uz godinu i mesec
 5. SISTEM: automatski povezuje brojeve sa zaposlenima
 6. ADMINISTRACIJA: proverava nepovezane i rešava ih ručno
 7. ADMINISTRACIJA: održava izuzetke od parkinga
 8. SISTEM: računa obustavu                     →  M-01
 9. ADMINISTRACIJA: pregleda izveštaj obustava
10. ADMINISTRACIJA: preuzima CSV                →  obracunski-mesec.csv
11. OBRAČUN ZARADA: preuzima iznose             →  [N] način nije potvrđen
```

#### Obračun [P]

> **obustava = osnovica za PDV − neto iznos paketa + parking + NZRD**

Potvrđeno kao ispravno (naručilac, 18.09.2026.).

#### Kontrole

| Kontrola | Gde |
|---|---|
| Jedna dodela i jedna potrošnja po broju i mesecu | Kontrola u bazi |
| Dnevnik uvoza sa brojačima | `mobilni_mobileimportlog` |
| **Pregled pre slanja u zarade** | Izveštaj „Obustave zaposlenih“ |

#### Moguće greške

| Greška | Posledica |
|---|---|
| **Dodele za mesec nisu uvezene** | **Cela potrošnja tiho ispada iz obračuna** — [P-31](#10-poznati-problemi-i-ograničenja) |
| Paket bez neto iznosa | Obustava prazna, red se ne izvozi |
| Negativna obustava | **Izvozi se** — [Q29](#67-mobilna-telefonija--obračuni) |
| Broj nije povezan sa zaposlenim | Ide u izveštaj „Nezaposleni“, **ne u zarade** |
| Zaposleni otišao usred meseca | **Nije ni u jednom pojedinačnom izveštaju** — [P-32](#10-poznati-problemi-i-ograničenja) |

#### Podaci za knjiženje

| Ko preuzima | Šta | Odakle | Oblik |
|---|---|---|---|
| **Obračun zarada** | Šifra radnika i iznos | `/mobilni/potrosnja/obracunski-mesec.csv` | `Godina;Mesec;Šifra;Iznos` |

> **[N] Q3:** nije potvrđeno da li se CSV uvozi ili iznosi prepisuju ručno,
> ni koja konta se koriste.

#### Završni rezultat

Iznosi obustava su spremni za obračun zarada.

> **[Z] Rizik:** obustava se **nigde ne čuva**. Ako se posle prenosa promeni paket ili
> dodela, ekran će za isti mesec pokazati **drugi iznos**. Vidi [P-31](#10-poznati-problemi-i-ograničenja).

---

### 5.5. Mesečna radna lista i ocenjivanje

#### Pokretački događaj

Kraj meseca.

#### Redosled aktivnosti [P]

```
 A) RADNA LISTA
 1. ZAPOSLENI: otvara svoju radnu listu        →  /hr/radna-lista/
 2. SISTEM: prikazuje sate iz prolazaka        →  K-01 (kao KONTROLA, ne prepisuje se)
        + putne naloge i bolovanja po danima
 3. ZAPOSLENI: unosi sate PO ŠIFRAMA POSLA
 4. ZAPOSLENI: unosi topli obrok i terenski dodatak
 5. ZAPOSLENI: „Predaj i štampaj“              →  status Predato

 B) OCENJIVANJE
 6. RUKOVODILAC: otvara obrazac                →  potpisan snimak, važi 24 h
 7. RUKOVODILAC: bira bodove 0–4 po šest merila
 8. SISTEM: stimulacija = zbir koeficijenata
        LIČNI KOEFICIJENT = 1 + stimulacija    →  K-08
 9. RUKOVODILAC: potvrđuje                     →  saglasnost 1/3
10. DIREKTOR CENTRA: potvrđuje ili koriguje    →  saglasnost 2/3
11. GENERALNI DIREKTOR: potvrđuje              →  saglasnost 3/3
12. Štampa obrasca sa tri potpisa
13. OBRAČUN ZARADA: preuzima koeficijent       →  [N] način nije potvrđen
```

#### Obračuni

| Obračun | Formula |
|---|---|
| [K-01](#66-kadrovi--obračuni) Dnevni sati | Uparivanje prolazaka; službeni izlazak **do 16:00** |
| [K-04/K-05](#66-kadrovi--obračuni) Sati radne liste | Zbir 31 kolone |
| [K-08](#66-kadrovi--obračuni) **Lični koeficijent** | **`K4 = 1 + zbir koeficijenata`** |
| [K-09](#66-kadrovi--obračuni) Saglasnost | Tri nivoa, korekcija uz obrazloženje |

#### Kontrole [P]

| Kontrola | Ponašanje |
|---|---|
| Obrazac stariji od 24 h | Odbija se |
| Dvostruko slanje | Vraća se postojeća ocena |
| Bodovi van sačuvane skale | Odbija se |
| **Preskakanje nivoa** | Odbija se |
| Korekcija izvan granica obrasca | Odbija se |
| **Korekcija bez obrazloženja** | Odbija se |
| Novija revizija | Blokira potvrdu starije |

#### Moguće greške

| Greška | Posledica |
|---|---|
| Zaboravljen ulaz ili izlaz | Sati manji od stvarnih, uz prijavljen problem |
| **Smena preko ponoći** | **Ne uparuje se uopšte** — [P-28](#10-poznati-problemi-i-ograničenja) |
| Izvor prolazaka nedostupan | Radna lista radi, sati prikazani kao „—“ |
| Pogrešna ocena | Ispravka je **nova revizija** |

#### Završni rezultat

Radna lista je predata, ocena potvrđena u tri nivoa, koeficijent spreman za zaradu.

---

### 5.6. Noćno preuzimanje podataka

#### Pokretački događaj

Raspored — Celery Beat.

#### Redosled aktivnosti [P]

```
 01:00  Dozvole            →  nove rute postaju vidljive
 01:10  Zaposleni          →  fleet_employee
 01:20  Otpis vozila       →  fleet_vehicle.otpis
 01:30  Šifre poslova      →  fleet_organizationalunit, fleet_jobcode
 01:45  Trebovanja         →  fleet_requisition
 02:00  Polise             →  fleet_policy
 02:20  EUF fakture        →  nabavka_invoice
 02:45  UF stavke          →  nabavka_euf_item_snapshot + UF fakture
 03:15  Servisi            →  fleet_servicetransaction
 03:35  DDOR osiguranja    →  fleet_draftinsurance
 03:50  Finansije          →  finansije_ledgerentry  (uz KONTROLNE ZBIROVE)
 04:20  Gorivo NIS         →  Selenium → TransactionNIS + FuelConsumption
 05:10  Gorivo OMV putn.   →  Selenium → TransactionOMV + čišćenje duplikata
 06:10  Gorivo OMV teretna →  isto
 07:10  Roba               →  nabavka_goods_snapshot
```

#### Kontrole [P]

| Kontrola | Gde |
|---|---|
| **Zaključavanje** | Redis (4 h / 90 min / 60 min) ili SQL `sp_getapplock` |
| **Kontrolni zbirovi** | Finansije — broj redova i iznosi po godini i kontu |
| **Prazan izvor ne briše podatke** | Finansije, Potraživanja |
| Nestali zapis | Označava se neaktivnim, **ne briše se** |
| Istorija | `TaskHistory` za svaki posao |

#### Moguće greške

| Greška | Posledica | Šta uraditi |
|---|---|---|
| Selenium ne uspeva | Nema novih podataka o gorivu | **Uvesti datoteku ručno** |
| Povezani server nedostupan | Finansije ne rade | Sačekati, pa pokrenuti ručno |
| Kontrolni zbirovi se ne slažu | **Ništa se ne objavljuje** | Ponoviti; proveriti izvor |
| Redis nedostupan | Poslovi rade **bez zaštite** | [P-16](#10-poznati-problemi-i-ograničenja) |
| Selenium blokira ostale poslove | Kasne sve sinhronizacije | [P-15](#10-poznati-problemi-i-ograničenja) |

#### Završni rezultat

Ujutru korisnik zatiče osvežene podatke. Provera: `/administracija/task-history/`.

---

### 5.7. Naplata potraživanja

#### Pokretački događaj

Potreba za pregledom dugovanja ili istekao rok plaćanja.

#### Redosled aktivnosti [P]

```
 1. SLUŽBA NAPLATE: pokreće sinhronizaciju     →  /potrazivanja/sinhronizacija/
 2. SISTEM: preuzima ceo izvor                 →  nepromenljiv snimak izvora
 3. SISTEM: partneri, knjiženja, fakture
 4. SISTEM: pozicije i starosni razredi        →  PT-01
 5. SISTEM: ŠEST KONTROLA                      →  PT-04
        razlika → NIŠTA SE NE OBJAVLJUJE
 6. SISTEM: objavljuje snimak stanja           →  PT-03
 7. SLUŽBA NAPLATE: pregleda dugovanja po starosti
 8. SLUŽBA NAPLATE: telefonski poziv           →  CollectionActivity
 9. SLUŽBA NAPLATE: opomena / pozivno pismo    →  CollectionNotice + stavke
10. SLUŽBA NAPLATE: štampa dokument
11. PRAVNA SLUŽBA: pravni postupak             →  CollectionLegalCase
12. PRAVNA SLUŽBA: promene u postupku          →  CollectionLegalEvent
```

#### Obračuni

| Obračun | Napomena |
|---|---|
| [PT-01](#68-potraživanja--obračuni) Starosni razredi | Sedam baketa |
| [PT-02](#68-potraživanja--obračuni) Saldo | Kontrola i u bazi |
| [PT-04](#68-potraživanja--obračuni) **Šest kontrola** | Svaka razlika prekida objavu |
| [PT-05](#68-potraživanja--obračuni) Saldo po šiframa posla | Ide u Finansije |

#### Moguće greške

| Greška | Posledica |
|---|---|
| Kontrolni zbirovi se ne slažu | **Snimak se ne objavljuje**, prethodni ostaje |
| Prazan izvor | Prenos se prekida, podaci ostaju |
| Partner bez šifarnika | Upisuje se neaktivan, uz zabeležen problem |
| **Dug bez datuma dospeća** | Prikazuje se kao **„Nedospelo“** — [P-35](#10-poznati-problemi-i-ograničenja) |

#### Završni rezultat

Objavljen snimak stanja na određeni datum; opomene i postupci evidentirani.
Finansije vide isti saldo na kartici posla.

---

### 5.8. Zaključenje ugovora

#### Redosled aktivnosti [P]

```
 1. Partner podnosi zahtev            →  ugovori_business_request
 2. Priprema se ponuda                →  ugovori_offer (naša ili data nama)
 3. Ponuda prihvaćena                 →  status Prihvacena
 4. PRAVNA: zaključuje ugovor         →  ugovori_contract (kind = MAIN)
 5. PRAVNA: dodaje stranke            →  ugovori_contract_party
 6. PRAVNA: prilaže dokumenta         →  ugovori_contract_document
 7. Sredstva obezbeđenja:
        menica    →  ugovori_contract_menica_link
        garancija →  ugovori_contract_guarantee
 8. Tokom trajanja: aneksi            →  ugovori_contract (kind = ANNEX)
 9. Ugovor se koristi u:
        Nabavci   (osnovni i kupovni ugovor)
        Floti     (lizing, finansiranje)
        Mobilnom  (paket)
10. Istek ugovora → status Istekao; garancije i menice se vraćaju
```

#### Kontrole [P]

| Kontrola | Poruka |
|---|---|
| Aneks bez glavnog ugovora | *„Aneks mora imati glavni ugovor.“* |
| Glavni ugovor sa nadređenim | *„Glavni ugovor ne sme imati nadređeni ugovor.“* |
| „Važi do“ pre „Važi od“ | Odbija se |
| Veza sa menicom: ni jedna ni obe | *„Izaberite tacno jednu menicu.“* |
| Brisanje povezane menice | **Zabranjeno** |

#### Moguće greške

| Greška | Posledica |
|---|---|
| Partner neaktivan u APR-u | Upozorenje u evidenciji partnera |
| Oznake „ima menice/garancije“ netačne | **Nema provere** — [Q40](#611-ugovori-i-menice--analize) |
| Menica sa jedinicom „PROCENAT“ | Iznos **nije novčani** |

#### Završni rezultat

Ugovor sa strankama, dokumentima i sredstvima obezbeđenja, spreman za upotrebu u
drugim modulima.

---

### 5.9. Mesečno praćenje rezultata

#### Pokretački događaj

Kraj meseca ili potreba za uvidom.

#### Redosled aktivnosti [P]

```
 1. SISTEM: sinhronizuje knjiženja (svaki sat u :20, dnevno 03:50)
 2. RUKOVODILAC: otvara Finansijski pregled  →  /finansije/
        prihodi, rashodi, rezultat po centrima i poslovima
 3. RUKOVODILAC: zbirna tabela šifara posla  →  11 kolona
        P, R, P−R, ZT, P−R−ZT, priliv, odliv, neto gotovina
 4. RUKOVODILAC: klik na šifru → kartica posla
 5. Osam tabova: fakture, interne fakture, rashodi, vozila,
        zaduženja, zaposleni, putni nalozi, POTRAŽIVANJA
 6. Izvoz u Excel po potrebi
```

#### Obračuni

Svih [18 obračuna Finansija](#61-finansijska-analitika--obračuni).

#### Kontrole [P]

| Kontrola | Kako |
|---|---|
| Rezultat reda | `prihod + prikazani rashod + prikazani ZT` |
| Neto gotovina | `prikazani priliv + prikazani odliv` |
| Potpunost sinhronizacije | Ekran sinhronizacije — kontrolni zbirovi |
| **Nepotpun obračun** | Zvezdica i objašnjenje — **„nepotpuno“ nije „nula“** |

#### Moguće greške u tumačenju [P]

| Zabluda | Ispravno |
|---|---|
| „Rashod je negativan, pa ga treba oduzeti“ | **Već je prikazan negativno** — samo sabrati |
| „Godišnji ZT = zbir mesečnih“ | **Nije** — koeficijent je prosek |
| „Tok gotovine = promet računa“ | **Nije** — obračun po pravilima procedure |
| „Zbir klasa 5 i 6 mora biti nula“ | Zatvaranja su **namerno izuzeta** |
| „Zbirna tabela = detalj“ | Detalj otvara **poslednji mesec perioda** |

#### Završni rezultat

Rukovodilac zna rezultat svog posla ili centra, i vidi sve evidencije koje ga čine.

---

### 5.10. Šta nijedan proces ne obuhvata

| Nedostaje | Napomena |
|---|---|
| **Odobravanje** predmeta nabavke pre slanja | Postoje statusi, ali ne i tok odobravanja |
| **Odobravanje** radne liste | Status „Odobreno“ postoji, ali se **nigde ne postavlja** — [Q26](#66-kadrovi--obračuni) |
| **Potvrda isplate** po virmanu | [Q32](#610-isplate--virmani) |
| **Povratna veza ka knjiženju** | Sistem čita knjiženja; ne knjiži |
| **Obaveštenja** (e-pošta, poruke) | Nema podešenog slanja |
| **Upozorenje o dospelom servisu** | `service_interval` se **ne koristi** — [Q23](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji) |

---

### 5.11. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Šta radi pojedini modul? | [3. Moduli](#3-moduli--sadržaj-i-veze) |
| Kako se računa iznos u procesu? | [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj) |
| Odakle dolaze podaci? | [7. Integracije](#7-integracije) |
| Šta može poći naopako? | [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) |

---

## 6. Analize i obračuni — sadržaj

> **Za koga je ovo poglavlje:** za sve. Poslovni korisnici ovde nalaze **kako se računa**
> svaki iznos koji vide na ekranu; programeri nalaze **gde je implementiran**.
>
> Ovo je samo sadržaj. Svaki obračun je opisan u svom poglavlju, po jedinstvenoj
> strukturi od 13 tačaka.

---

### 6.0.1. Kako je opisan svaki obračun

Svaki obračun ima istih 13 tačaka:

| # | Tačka | Šta sadrži |
|---|---|---|
| 1 | Naziv | Naziv na ekranu i tehnički naziv, sa putanjom do koda |
| 2 | Poslovna svrha | Koji problem rešava i zašto postoji |
| 3 | Korisnici rezultata | Koja služba koristi rezultat |
| 4 | Ulazni podaci | Tabela: poslovni naziv, polje na ekranu, tabela i kolona, tip, jedinica mere, obaveznost, ko unosi |
| 5 | Poreklo podataka | Put podatka od izvora do ekrana |
| 6 | Tačan postupak obračuna | Formula, uslovi, filteri, zaokruživanje, postupanje sa praznim vrednostima |
| 7 | Tehnička implementacija | Fajl, funkcija, upit, ekran, testovi |
| 8 | Primer obračuna | Potpun primer sa konkretnim brojevima |
| 9 | Rezultat | Šta predstavlja, gde se čuva, kada se ponovo računa, ko ga menja |
| 10 | Upotreba rezultata | Gde se dalje koristi |
| 11 | Kontrola i ručna provera | Kako korisnik može sam da proveri iznos |
| 12 | Izuzeci i rizični slučajevi | Šta se dešava kada podatak nedostaje ili nije ispravan |
| 13 | Status pouzdanosti | Tabela: tvrdnja, status, izvor potvrde, otvoreno pitanje |

**Oznake statusa:**

| Oznaka | Značenje |
|---|---|
| **[P]** | Potvrđeno — pročitano iz koda, migracija ili konfiguracije |
| **[Z]** | Zaključeno — logičan zaključak iz implementacije, nije izričito napisano |
| **[N]** | Nepotvrđeno — traži potvrdu korisnika |

---

### 6.0.2. Zbirni pregled

Nova analitika flote i vozila od 19.09.2026. opisana je u
[6.12. Flota — ekonomika](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa): E-01 zajednički periodni
obračun i E-02 sačuvano poređenje budućih alternativa. Donji inventar 74 obračuna
opisuje ranije stanje; nasleđene funkcije nisu uklonjene.

| Modul | Obračuna | Poglavlje | Stanje |
|---|---|---|---|
| **Finansijska analitika** | 18 | [6.1](#61-finansijska-analitika--obračuni) | ✔ **Završeno** (preuzeto iz postojeće metodologije) |
| **Flota — gorivo** | 8 | [6.2](#62-flota--obračuni-goriva) | ✔ **Završeno** |
| **Flota — troškovi** | 8 | [6.3](#63-flota--troškovi-vozila) | ✔ **Završeno** |
| **Flota — polise i lizing** | 4 | [6.4](#64-flota--polise-lizing-i-servisi) | ✔ **Završeno** |
| **Flota — izveštaji** | 4 + 11 | [6.5](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji) | ✔ **Završeno** (11 izveštaja čeka DDL) |
| **Kadrovi** | 9 | [6.6](#66-kadrovi--obračuni) | ✔ **Završeno** |
| **Mobilna telefonija** | 4 | [6.7](#67-mobilna-telefonija--obračuni) | ✔ **Završeno** |
| **Potraživanja** | 6 | [6.8](#68-potraživanja--obračuni) | ✔ **Završeno** |
| **Nabavka** | 6 | [6.9](#69-nabavka--obračuni-i-analize) | ✔ **Završeno** |
| **Isplate** | 3 | [6.10](#610-isplate--virmani) | ✔ **Završeno** |
| **Ugovori i menice** | 4 | [6.11](#611-ugovori-i-menice--analize) | ✔ **Završeno** |
| | **74 (+11)** | | ✔ **Svih 74 završeno** (11 izveštaja nad pogledima čeka DDL) |

> Modul **Naplata** nije obuhvaćen — nasleđen je i zamenjuju ga Potraživanja.
> Vidi [10. Poznati problemi, P-18](#p-18--naplata-i-potraživanja-rade-paralelno).

---

### 6.1. Finansijska analitika (18 obračuna)

Poglavlje: [`obracuni/06-01-finansije.md`](#61-finansijska-analitika--obračuni)
Postojeća metodologija: `finansije-metodologija-obracuna.md` — Uklonjen iz repozitorijuma 18.09.2026.; sadržaj je dostupan u git istoriji, u izmeni `06f60c2`

| Oznaka | Naziv | Implementacija |
|---|---|---|
| F-01 | Prihodi po šifri posla | `finansije/services/reports.py` |
| F-02 | Rashodi po šifri posla | `finansije/services/reports.py` |
| F-03 | Rezultat bez zajedničkih troškova | `finansije/services/reports.py` |
| F-04 | Zajednički troškovi — pravila raspodele | `finansije/services/shared_costs.py` |
| F-05 | Zajednički troškovi — koeficijent posla | `finansije/services/shared_costs.py` |
| F-06 | Rezultat posle raspodele ZT | `finansije/services/job_overview.py` |
| F-07 | Priliv gotovine | `finansije/services/cash_flow.py` |
| F-08 | Odliv gotovine | `finansije/services/cash_flow.py` |
| F-09 | Neto gotovina | `finansije/services/cash_flow.py` |
| F-10 | Zamena PDV-a u toku gotovine | `finansije/services/cash_flow.py` |
| F-11 | Zarade u obračunu toka gotovine | `finansije/services/cash_flow.py` |
| F-12 | Refundacije | `finansije/services/cash_flow.py` |
| F-13 | Grafikoni, učešća i rangiranje | `finansije/services/charts.py` |
| F-14 | Mesečni rashodi (kartica posla) | `finansije/services/job_card.py` |
| F-15 | Mesečne fakture IF i interne ON | `finansije/services/job_card.py` |
| F-16 | Vozila i zaduženja na šifri posla | `finansije/services/job_card.py` |
| F-17 | Zaposleni i zarade po šifri posla | `finansije/services/job_people.py` |
| F-18 | Osvežavanje naloga Z | `finansije/services/nalog_z.py` |

---

### 6.2. Flota — gorivo (8 obračuna) ✔

Poglavlje: [`obracuni/06-02-flota-gorivo.md`](#62-flota--obračuni-goriva)

> U koloni **Problemi** precrtana oznaka (~~P-10~~) znači da je problem
> **rešen 18.09.2026.** — opis šta je promenjeno stoji u
> [registru problema](#10-poznati-problemi-i-ograničenja).

| Oznaka | Naziv | Ključna formula | Problemi |
|---|---|---|---|
| [V-03](#v-03--neto-iznos-goriva-iz-bruto-iznosa) | Neto iznos goriva iz bruto | `bruto − PDV`, ili `bruto × 5/6` | — |
| [V-04](#v-04--iznosi-omv-transakcije) | Iznosi OMV transakcije | Iz `gross_cc` i `vat` | — |
| [V-05](#v-05--iznosi-nis-transakcije) | Iznosi NIS transakcije | Iz `total`, uvek × 5/6 | — |
| [V-06](#v-06--prečišćavanje-omv-transakcija) | **Prečišćavanje OMV transakcija** | Tri koraka uklanjanja duplikata | — |
| [V-01](#v-01--prosečna-potrošnja-goriva-poslednjih-10-točenja) | Prosečna potrošnja (10 točenja) | `litri / km × 100` | **P-02** |
| [V-02](#v-02--prosečna-potrošnja-goriva-za-ceo-vek-vozila) | Prosečna potrošnja (ceo vek) | `litri / km × 100` | — |
| [V-21](#v-21--gorivo-po-šifri-posla) | Gorivo po šifri posla | Zbir po istorijskoj dodeli i polumesecu | — |
| [V-23](#v-23--obračun-goriva-na-putnom-nalogu-vozila) | Obračun goriva na putnom nalogu | `litri / pređeni put × 100` | — |

---

### 6.3. Flota — troškovi (8 obračuna) ✔

Poglavlje: [`obracuni/06-03-flota-troskovi.md`](#63-flota--troškovi-vozila)

| Oznaka | Naziv | Ključna formula | Problemi |
|---|---|---|---|
| [V-08](#v-08--procena-pređene-kilometraže-u-periodu) | Procena kilometraže u periodu | `(Δkm / Δdana) × dana perioda` | **P-03, P-04** |
| [V-07](#v-07--trošak-po-kilometru-po-vozilu) | **Trošak po kilometru** | `(gorivo+servisi+trebovanja+polise+amortizacija+lizing−naknade) / km` | **P-05…P-09**, ~~P-10~~ |
| [V-11](#v-11--pragovi-fiksnog-troška-po-kilometru) | Pragovi po masi vozila | 4 klase × 3 praga | **P-11** |
| [V-12](#v-12--status-vozila-prema-trošku-po-kilometru) | Status vozila i „crvena zona“ | Poređenje sa pragom | — |
| [V-09](#v-09--analiza-troška-po-km-kroz-više-perioda) | Trajno neisplativa vozila | „Neisplativo“ u svim periodima | **P-12** |
| [V-10](#v-10--neto-trošak-održavanja) | Neto trošak održavanja | `servisi + trebovanja − naknade` | — |
| [V-15](#v-15--analitika-evidentiranih-troškova-na-detalju-vozila) | Analitika na detalju vozila | Samo evidentirani iznosi | — |
| [V-24](#v-24--statistika-po-centrima) | Statistika po centrima | Zbirovi za ceo vek vozila | ~~P-13~~, **P-14 D** |

---

### 6.4. Flota — polise, lizing i servisi (4 obračuna) ✔

Poglavlje: [`obracuni/06-04-flota-ugovori-polise.md`](#64-flota--polise-lizing-i-servisi)

| Oznaka | Naziv | Grupisanje | Problemi |
|---|---|---|---|
| [V-17](#v-17--mesečni-troškovi-polisa) | Mesečni troškovi polisa | Po **datumu izdavanja**, istorijska šifra posla | — |
| [V-18](#v-18--polise-pred-istekom-i-neobnovljene-polise) | Polise pred istekom i neobnovljene | Rok 30 dana, samo potpune polise | — |
| [V-19](#v-19--mesečni-troškovi-lizinga) | Mesečni troškovi lizinga | Po **datumu početka ugovora** | **P-23, P-24, P-25** |
| [V-20](#v-20--mesečni-troškovi-servisa) | Mesečni troškovi servisa | Po datumu servisa, istorijska šifra posla | — |

---

### 6.5. Flota — kilometraža, održavanje i izveštaji (4 + 11) ✔

Poglavlje: [`obracuni/06-05-flota-izvestaji.md`](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji)

| Oznaka | Naziv | Napomena | Problemi |
|---|---|---|---|
| [V-13](#v-13--kilometraža-vozila--posmatrana-vremenska-linija) | Kilometraža — vremenska linija | Odbija prikaz kada primeti pad | — |
| [V-14](#v-14--održavanje-vozila-i-servisni-interval) | Održavanje vozila | Prepoznaje i ćirilične kategorije | — |
| [V-16](#v-16--presek-stanja-flote-kontrolna-tabla) | Presek stanja flote | 8 grupa upozorenja | — |
| [V-22](#v-22--izveštaji-za-upravu) | Izveštaji za upravu (4) | Kasko, osiguranje IMS, gorivo, delovi | ~~P-26~~, **P-47** |
| [6.5.5](#655-izveštaji-nad-nasleđenim-pogledima) | 11 izveštaja nad pogledima | **Formula je u bazi, ne u kodu** | **P-27** |

---

### 6.6. Kadrovi (9 obračuna) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| K-01 | Dnevni sati rada iz evidencije prolazaka | `hr/services/attendance.py` |
| K-02 | Mesečni pregled dnevnih sati | `hr/services/attendance.py` |
| K-03 | Problemi u parovima prolazaka | `hr/services/attendance.py` |
| K-04 | Ukupni sati po redu radne liste | `hr/models.py` |
| K-05 | Ukupni sati radne liste | `hr/models.py` |
| K-06 | Godišnji odmori — dodele i rešenja | `hr/services/annual_leave.py` |
| K-07 | Bolovanja — uvoz RFZO i povezivanje | `hr/services/sick_leave.py` |
| K-08 | **Ocenjivanje — stimulacija i lični koeficijent** | `hr/services/evaluations.py` |
| K-09 | Tok saglasnosti na ocenu | `hr/services/evaluations.py` |

### 6.7. Mobilna telefonija (4 obračuna) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| M-01 | **Obustava po zaposlenom** | `mobilni/withholdings.py` |
| M-02 | Izuzeci od parkinga | `mobilni/withholdings.py` |
| M-03 | Razvrstavanje zaposleni / bivši / nezaposleni | `mobilni/withholdings.py` |
| M-04 | Povezivanje broja telefona sa zaposlenim | `mobilni/models.py` |

### 6.8. Potraživanja (6 analiza) — u pripremi

> Oznake su **PT-**, a ne **P-**, da se ne mešaju sa oznakama problema iz
> [10. Poznati problemi](#10-poznati-problemi-i-ograničenja).

| Oznaka | Naziv | Implementacija |
|---|---|---|
| PT-01 | Starosni razredi (aging) | `potrazivanja/services/sync.py` |
| PT-02 | Saldo stavke | `potrazivanja/models.py` |
| PT-03 | Objavljivanje snimka stanja | `potrazivanja/services/sync.py` |
| PT-04 | Kontrolni zbirovi i provera izvora | `potrazivanja/services/sync.py` |
| PT-05 | Saldo po šiframa posla | `potrazivanja/services/reports.py` |
| PT-06 | Normalizacija kontakata | `potrazivanja/services/contacts.py` |

### 6.9. Nabavka (6 analiza) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| B-01 | Procenjena vrednost stavke i predmeta | `nabavka/models.py` |
| B-02 | Grupisanje UF stavki u UF fakture | `nabavka/services/source_snapshots.py` |
| B-03 | Ključ EUF fakture | `nabavka/services/euf.py` |
| B-04 | Razlike verzija plana javnih nabavki | `nabavka/services/public_procurements.py` |
| B-05 | Provera šifre posla partnera | `nabavka/views/reports.py` |
| B-06 | Alarmi nabavke | `nabavka/views/alerts.py` |

### 6.10. Isplate (3 obračuna) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| I-01 | **Generisanje datoteke virmana** | `isplate/services/virman.py` |
| I-02 | Kontrole naloga pre virmana | `isplate/services/virman.py` |
| I-03 | Konverzija datoteka | `isplate/services/converters.py` |

### 6.11. Ugovori i menice (4 analize) — u pripremi

| Oznaka | Naziv | Implementacija |
|---|---|---|
| U-01 | Provera statusa partnera u APR-u | `ugovori/apr_openapi.py` |
| U-02 | Sinhronizacija partnera iz finansija | `ugovori/services.py` |
| U-03 | Preuzimanje menica iz registra NBS | `menice/scraper.py` |
| U-04 | Povezivanje menica i garancija sa ugovorima | `ugovori/models.py` |

---

### 6.0.3. Obračuni po korisniku

Za brzo snalaženje — koji obračuni su važni kojoj službi:

| Služba | Obračuni |
|---|---|
| **Uprava** | F-01…F-13, V-07, V-09, V-12, V-16, V-22 |
| **Finansije** | Svi F-01…F-18, V-17, V-19, V-20 |
| **Služba voznog parka** | Svi V-01…V-24 |
| **Garaža** | V-13, V-14, V-23 |
| **Kadrovska služba** | K-01…K-09 |
| **Obračun zarada** | K-08, **M-01**, I-01 |
| **Služba naplate** | PT-01…PT-06 |
| **Služba nabavke** | B-01…B-06 |
| **Pravna služba** | U-01…U-04 |
| **Blagajna** | **I-01**, I-02 |

---

### 6.0.4. Obračuni čiji rezultat ide izvan sistema

Većina obračuna služi samo za prikaz. Ovi **stvaraju podatak koji ide dalje**:

| Obračun | Šta nastaje | Gde ide | Način prenosa |
|---|---|---|---|
| **I-01** Virman | Datoteka fiksne širine (180 znakova, cp1250) | **Banka** | Preuzimanje datoteke, ručno slanje |
| **M-01** Obustava mobilnih | Iznos po zaposlenom | **Obračun zarada** | CSV izvoz, **[N] način prenosa nije potvrđen** |
| **K-08** Ocenjivanje | Stimulacija i lični koeficijent | **Obračun zarada** | **[N] nije potvrđeno** |
| **K-04/K-05** Radna lista | Sati po šiframa posla | **Obračun zarada** | **[N] nije potvrđeno** |
| **F-18** Nalog Z | Osvežena lokalna kopija knjiženja | `IMS_ERP.dbo.nalog_z` | Uskladištena procedura |

> **[N] Otvoreno pitanje Q3:** ni za jedan od ovih rezultata nije potvrđeno **koja konta
> i koja vrsta knjiženja** se koriste, niti postoji li pisana procedura prenosa.
> Dok se to ne potvrdi, dokumentacija **ne navodi konta**.

---

### 6.0.5. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Koje tabele i kolone koriste ovi obračuni? | [4. Baza podataka](#4-baza-podataka) |
| Kako podaci dolaze u sistem? | [7. Integracije](#7-integracije) |
| Šta je uočeno kao problem? | [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) |
| Šta znači neki pojam? | [12. Rečnik pojmova](#12-rečnik-pojmova-i-mapiranje-naziva) |

---

## 6.1. Finansijska analitika — obračuni

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](#10-poznati-problemi-i-ograničenja).

---

### 6.1.0. Šta ovo poglavlje pokriva

Finansijska analitika je **jedini modul koji je bio detaljno dokumentovan pre ovog posla**.
Ta metodologija (`finansije-metodologija-obracuna.md`, 584 reda u 20 poglavlja) uklonjena je
iz repozitorijuma 18.09.2026., a **njen sadržaj je prenet ovde**. Ovo poglavlje je od tada
**samostalno** — za pitanje „kako je tačno izračunat ovaj iznos“ ne treba nijedan drugi
dokument.

> Izvorna metodologija ostaje u git istoriji:
> `git show 06f60c2:dokumentacija/finansije-metodologija-obracuna.md`

Uz nju postoji i tehničko uputstvo: [`finansije/README.md`](../finansije/README.md).

**Šta se ovde opisuje:** ono što aplikacija računa i prikazuje, prema izvornom kodu.
Razdvojeni su knjigovodstveni rezultat, raspodela zajedničkih troškova, obračun novčanih
tokova i povezane evidencije.

> **Svi brojčani primeri u ovom poglavlju su ilustracije formula, ne poslovni podaci
> preduzeća** — osim iznosa izričito označenih kao kontrolni u
> [6.1.17](#6117-kontrolni-postupak). [P]

---

### 6.1.1. Registar obračuna

| # | Obračun | Ključna formula | Implementacija | Detaljno |
|---|---|---|---|---|
| **F-01** | Prihodi | `P = Σ(potražuje − duguje)` na klasi **6** | `services/reports.py` | [6.1.5](#615-prihodi-rashodi-i-rezultat-bez-zt) |
| **F-02** | Rashodi | `R = Σ(duguje − potražuje)` na klasi **5** | `services/reports.py` | [6.1.5](#615-prihodi-rashodi-i-rezultat-bez-zt) |
| **F-03** | Rezultat bez ZT | `P − R` | `services/reports.py: expressions()` | [6.1.5](#615-prihodi-rashodi-i-rezultat-bez-zt) |
| **F-04** | ZT — pravila raspodele | Čitanje `posao_mes`, `blokraspodela` | `services/shared_costs.py: allocation_rules()` | [6.1.6](#616-zajednički-troškovi-i-rezultat-posle-raspodele) |
| **F-05** | ZT — koeficijent i raspodela | `Aj = Bj × Cj/100 × Kj/100` | `services/shared_costs.py: allocate()` | [6.1.6](#616-zajednički-troškovi-i-rezultat-posle-raspodele) |
| **F-06** | Rezultat posle ZT | `P − R − ZT` | `services/job_overview.py: enrich_jobs()` | [6.1.6](#616-zajednički-troškovi-i-rezultat-posle-raspodele) |
| **F-07** | Priliv | `I = Σ` završnog potražuje | `services/cash_flow.py: calculate()` | [6.1.7](#617-priliv-odliv-i-neto-gotovina) |
| **F-08** | Odliv | `O = Σ` završnog duguje | `services/cash_flow.py: calculate()` | [6.1.7](#617-priliv-odliv-i-neto-gotovina) |
| **F-09** | Neto gotovina | `I − O` | `services/cash_flow.py: cash_flow()` | [6.1.7](#617-priliv-odliv-i-neto-gotovina) |
| **F-10** | Zamena PDV-a | `PDV = Σ(pdv+pdv8) tip I − Σ ostali` | `services/cash_flow.py` | [6.1.7](#zamena-pdv-a-p) |
| **F-11** | Zarade u toku gotovine | Zamena konta 450xx kontima iz `element.knt_troska` | `services/cash_flow.py` | [6.1.7](#zarade-u-obračunu-toka-p) |
| **F-12** | Refundacije | `potražuje = izvorno potražuje − izvorno duguje` | `services/cash_flow.py` | [6.1.7](#refundacije-p) |
| **F-13** | Grafikoni i učešća | `učešće = red / ukupno × 100` | `services/charts.py: overview_data()` | [6.1.8](#618-grafikoni-učešća-i-rangiranje) |
| **F-14** | Mesečni rashodi (kartica posla) | Zbir po mesecu knjiženja | `services/job_card.py: monthly_expenses()` | [6.1.10](#6110-struktura-rashoda-po-kontima) |
| **F-15** | Fakture IF i interne ON | IF: `Σ(duguje − potražuje)`; ON: `Σ(potražuje − duguje)` | `services/job_card.py: monthly_invoices()` | [6.1.9](#619-fakture-if-i-interne-on) |
| **F-16** | Vozila i zaduženja na poslu | Presek perioda i istorijskih dodela | `services/job_card.py: assigned_vehicles()`, `vehicle_custody()` | [6.1.12](#6112-vozila-zaduženja-i-putni-nalozi) |
| **F-17** | Zaposleni i zarade na poslu | `DISTINCT br_obr` po zaposlenom i mesecu | `services/job_people.py: payroll_employees()` | [6.1.11](#6111-zaposleni-i-zarade) |
| **F-18** | Osvežavanje naloga Z | Pokretanje `sp_AzurirajNalogZ` | `services/nalog_z.py: refresh_nalog_z()` | [6.1.16](#6116-sinhronizacija-istorija-i-procedure) |

#### Oznake u formulama [P]

| Oznaka | Značenje |
|---|---|
| `P` | Prihod |
| `R` | Rashod kao **obračunska** veličina; redovan rashod je pozitivan pre promene znaka za prikaz |
| `ZT` | Raspoređeni zajednički trošak; redovan trošak je pozitivan pre promene znaka |
| `I` | Priliv prema obračunu novčanih tokova |
| `O` | Odliv kao obračunska veličina; redovan odliv je pozitivan pre promene znaka |
| `D` / `C` | Izvorno duguje / potražuje |

| Pokazatelj | Obračunska formula | Prikaz u tabeli Šifre posla i detalju |
|---|---|---|
| Prihodi | `P = Σ(C − D)` na klasi 6, uz isključenja | `P` |
| Rashodi | `R = Σ(D − C)` na klasi 5, uz ista isključenja | `−R` |
| Rezultat bez ZT | `P − R` | `P − R` |
| Zajednički troškovi | Raspodela iz [6.1.6](#616-zajednički-troškovi-i-rezultat-posle-raspodele) | `−ZT` |
| Rezultat `P − R − ZT` | `P − R − ZT` | Isti iznos |
| Priliv | Zbir potražuje posle transformacija iz [6.1.7](#617-priliv-odliv-i-neto-gotovina) | `I` |
| Odliv | Zbir duguje posle istih transformacija | `−O` |
| Neto gotovina | `I − O` | Isti iznos |

> **[P] „Neto rezultat“ na Finansijskom pregledu i rang-listama znači `P−R`** — pre dodatne
> raspodele ZT i **pre poreza na dobit**. Konačni rezultat posle raspodele posebno je
> označen kao `P−R−ZT` na šifri posla. **Nijedan od ta dva rezultata ne znači stanje novca
> na računu.**

---

### 6.1.2. Sedam pravila koja objašnjavaju većinu nedoumica

#### 1. Prikazani znak nije obračunski znak [P]

| Pokazatelj | Obračunski | Na ekranu |
|---|---|---|
| Prihodi | `P` | `P` |
| **Rashodi** | `R` (pozitivan) | **`−R`** |
| **Zajednički troškovi** | `ZT` (pozitivan) | **`−ZT`** |
| **Odliv** | `O` (pozitivan) | **`−O`** |

> Rezultat se proverava **sabiranjem prikazanih vrednosti**: `prihod + prikazani rashod
> + prikazani ZT`, odnosno `prikazani priliv + prikazani odliv`. Ne treba ponovo oduzimati
> već negativan broj.

**Primer [P]:** `P=1.000`, `R=600`, `ZT=80`, `I=700`, `O=650`. Ekran prikazuje `+1.000`,
`−600`, rezultat bez ZT `+400`, ZT `−80`, rezultat posle ZT `+320`, priliv `+700`,
odliv `−650`, neto gotovinu `+50`.

#### 2. Dva različita datuma [P]

| Podatak | Datum |
|---|---|
| Prihodi, rashodi, ZT, konta, grafikoni, knjiženja | **Datum knjiženja** (`dat_naloga`) |
| Fakture IF i interne ON | **Datum dokumenta** (`datum`), uz izabranu izvornu godinu `god` |
| Tokovi 52nt | Datum naloga uz godinu izvora; PDV ima posebno pomeranje |
| Zaposleni iz obračuna | `Zarada.god`, `Zarada.mesec` |
| Vozila i zaduženja | Presek perioda sa istorijom dodela |
| Putni nalozi | Datum putovanja (`travel_date`) |
| Potraživanja | **Poslednji objavljeni snimak** — izabrani mesec ga ne menja |

#### 3. Centar nije OJ knjiženja [P]

`posao.blok` (centar posla) i `nalog_z.oj` (OJ knjiženja) su **odvojene dimenzije**.

#### 4. Zatvaranja su namerno isključena [P]

Iz prihoda i rashoda izuzimaju se: vrsta naloga **`ZAT`**, konto **`59900`**, konto **`69900`**.

> Zbog toga zbir svih stavki klasa 5 i 6 posle zatvaranja godine **nije nula** u ovom
> prikazu — to nije greška, nego namera.

#### 5. Godišnji ZT nije zbir mesečnih [P]

> `Kj = zbir koeficijenata posla za kriterijum j / broj meseci perioda`

Koeficijent je **prosek**, pa godišnji obračun po pravilu procedure 53 daje drugačiji
iznos od zbira dvanaest zasebnih mesečnih obračuna. Isto važi i za tokove.

#### 6. Tok gotovine nije promet računa [P]

Priliv i odliv nastaju po pravilima procedure `SPFINizv52nt` — uz zamenu PDV-a, zamenu
obaveza troškovima, zamenu zarada i refundacije. **Nije zbir prometa bankovnog računa** i
**ne povezuje fakturu sa uplatom**. Originalna poslovna procedura se pri prikazu **ne
izvršava**.

#### 7. Ekran nije jedan vremenski snimak [P]

Prihodi i rashodi dolaze iz **poslednje uspešne sinhronizacije**, tokovi i koeficijenti se
čitaju **u trenutku otvaranja**, a Potraživanja iz **svog objavljenog snimka**.
Različite godine mogu biti osvežene u različito vreme. **Izabrani period određuje obuhvat,
a ne trenutak osvežavanja izvora.**

---

### 6.1.3. Period, centar i obuhvat pristupa

#### Granice perioda [P]

| Pravilo | Ponašanje |
|---|---|
| Granice datuma | **Uključive** |
| Mesečni detalj | Prvi i poslednji dan meseca |
| „Cela godina“ (`month=`) | **01.01–31.12**, uključujući i deo tekuće godine koji još nije protekao |
| **Nedostajući** parametar meseca | Bira **tekući mesec** — nije isto što i prazan parametar |
| Početni Finansijski pregled i zbirni pregled šifara | 01.01. tekuće godine **do današnjeg datuma** |
| Format unosa | `DD.MM.GGGG`; prihvataju se i završna tačka i ISO `YYYY-MM-DD` |

#### Filteri tabele Šifre posla [P]

Tabela **Šifre posla** ima **samo** filtere od/do i centar. Raniji URL parametri konto,
šifra, vrsta knjiženja, tačno konto i OJ knjiženja **ne filtriraju** ovu tabelu.

Ona uvek prikazuje **i prihode i rashode** i uključuje dostupne šifre **bez prometa**.
Prikaz šifarnika nije ograničen samo na trenutno aktivne poslove.

Ostali izveštaji i Knjiženja zadržavaju svoje filtere. **Učešća i zbirovi uvek zavise od
primenjenih filtera.**

#### Centar nije OJ knjiženja [P]

Centar posla dolazi iz `posao.blok`, OJ knjiženja iz `nalog_z.oj`.

Pri sinhronizaciji se koristi **aktuelni šifarnik poslova**. Promena centra u šifarniku
može posle osvežavanja **pregrupisati ranija knjiženja** — vidi
[P-44](#p-44--promena-centra-pregrupiše-celu-istoriju-finansija).
ZT za posao takođe koristi aktuelni `posao.blok`, uz koeficijente za izabranu godinu.
Lokalni P/R mogu odražavati **starije** stanje centra ako sinhronizacija još nije preuzela
promenu.

#### Prava pristupa menjaju i ukupne iznose [P]

Uz `finansije:view_all` korisnik vidi ceo obuhvat firme. Ostali vide **uniju** dozvoljenih
centara i izričito dozvoljenih šifara posla. **Prazan spisak dozvola nije globalan pristup.**

> **[P] Bitno:** ukupni iznosi i procenti računaju se **iz korisniku dostupnog skupa**.
> Zato **dva korisnika sa različitim obuhvatom vide različite ukupne iznose i procente**
> na istom ekranu, za isti period. To nije greška.

Za ZT su osnovice **cele firme** potrebne za pravilnu raspodelu, ali se korisniku vraća
samo rezultat za dostupne poslove. Vozila, zaduženja, zaposleni, putni nalozi i
Potraživanja dodatno poštuju dozvole **svojih** modula.

#### Period pri prelasku na detalj [P]

Iz zbirnih prikaza klik otvara detalj za **poslednji mesec izabranog perioda**. Iz tabele
Šifre posla izbor tačno cele kalendarske godine otvara celu godinu. Klik iz pojedinačnog
knjiženja prenosi mesec tog knjiženja.

> **Proizvoljan opseg od više meseci se ne prenosi u detalj.** Zbirna tabela za
> januar–septembar **ne poredi se direktno** sa detaljem otvorenim samo za septembar —
> najpre treba uskladiti periode.

---

### 6.1.4. Odakle Finansije čitaju

Podrazumevano preduzeće je `FINANSIJE_COMPANY=1`. Finansijska analitika **počinje od 2025.
godine**. [P]

| Skup | Izvor | Način |
|---|---|---|
| Knjiženja, prihodi, rashodi, IF, konta, grafikoni | `[PUTGEO-SERVER].[bazaims].dbo.nalog_z` i prateći šifarnici | Sinhronizovano u `LedgerEntry` |
| Šifre posla, naziv, centar, aktivnost, tip | `bazaims.dbo.posao` | Lokalni `FinanceJob`; deo obračuna čita i izvorni šifarnik |
| Kriterijumi i koeficijenti ZT | `bazaims.dbo.posao_mes`, `blokraspodela`, `posao` | **Direktan `SELECT` pri obračunu** |
| Osnovice raspodele ZT | Lokalni `LedgerEntry` | Sinhronizovana knjiženja **cele firme** |
| Priliv i odliv | `nalog_z`, `konto`, `vrsta_naloga`, `tipnal`, `pdv_arhiva`, `posao_mes`; `bazaldims.dbo.element` | **Direktan `SELECT`** |
| Zaposleni na poslu | `bazaldims.dbo.Zarada`, `PomLD`, `Radnik` | **Direktan `SELECT`** |
| Vozila i istorija dodela | Lokalni `Vehicle`, `JobCode`, `TrafficCard`, `OrganizationalUnit` | ORM |
| Lična zaduženja | Lokalni `VehicleTravelOrder` | ORM |
| Službena putovanja | Lokalni `PutniNalog` | ORM |
| Dugovanja i starosni razredi | Objavljeni `BalanceSnapshot` i `ReceivablePosition` | `potrazivanja.services.reports.job_balances` |

> **[P] Posledica:** samo prihodi i rashodi rade iz lokalne kopije. **Zajednički troškovi,
> tok gotovine i zaposleni zahtevaju da udaljeni server radi u trenutku otvaranja ekrana.**

#### Mapiranje polja knjiženja [P]

| Lokalno polje | Izvorno polje |
|---|---|
| `company`, `year` | `sif_pred`, `god` |
| `journal_type`, `journal_number`, `line_number` | `sif_vrs`, `br_naloga`, `stavka` |
| `booking_date` | `dat_naloga` |
| `document_date`, `document_reference` | `datum`, `vez_dok` |
| `debit`, `credit` | `duguje`, `potrazuje` |
| `account`, `job_code`, `organizational_unit` | `knt`, `sif_pos`, `oj` |
| `partner_group`, `partner_code` | `grupa`, `sif_par` |
| `currency`, `foreign_amount` | `skr_naz`, `deviza` |
| `description`, `due_date`, `source_paid_amount` | `kom`, `dpo`, `placeno` |

Nazivi se dopunjavaju iz `posao`, `konto`, `ob_jedin` po godini/OJ i `partner` po
grupi/šifri partnera.

> **Identitet knjiženja je: firma + godina + vrsta naloga + broj naloga + stavka.** [P]

Iznosi koriste duguje/potražuje **u RSD**. Aplikacija **ne preračunava** `deviza` po kursu.
Polje `placeno` se preuzima, ali se **ne koristi** za naplaćeno niti za priliv. [P]

---

### 6.1.5. Prihodi, rashodi i rezultat bez ZT

Osnov su **aktivna** lokalna knjiženja (`LedgerEntry.active=True`) odgovarajuće firme,
perioda i vidljivog posla/centra. [P]

```text
P = zbir (potražuje − duguje), kada konto počinje sa 6
R = zbir (duguje − potražuje), kada konto počinje sa 5
Rezultat bez dodatne raspodele ZT = P − R
```

**Iz sva tri obračuna isključuju se** [P]:

- sva knjiženja vrste `ZAT`;
- konto `59900`;
- konto `69900`.

Ta knjiženja zatvaraju/prenose rezultat i ne treba da ponište redovno poslovanje u
analitičkom prikazu. **Isključenje je logičko ILI** — dovoljno je da stavka ispuni bilo
koji od tri uslova.

| Slučaj | Ponašanje |
|---|---|
| Redovni `ON` nalozi | **Ostaju uključeni** |
| Korekcije na `59120` / `69120` | **Nisu** posebno izbačene |
| Storna i korekcije | Zadržavaju **izvorni znak**; ne koristi se apsolutna vrednost |
| `R` negativan zbog korekcija | Prikaz `−R` biće **pozitivan** — označava smanjenje rashoda. Isto važi za ZT i odliv |

> **[P] Šta znači „bez ZT“:** *bez dodatne raspodele ZT koju ova aplikacija računa.*
> Osnovni `R` **već sadrži** sve odgovarajuće proknjižene stavke klase 5, uključujući
> eventualna knjiženja zajedničkih troškova u izvoru. Aplikacija **nema** pravilo koje iz
> klase 5 uklanja ranije proknjiženu raspodelu — vidi
> [P-43](#p-43--mogući-dvostruki-obuhvat-zajedničkih-troškova).

---

### 6.1.6. Zajednički troškovi i rezultat posle raspodele

#### Šta se čita [P]

Iz `posao_mes` uzimaju se firma, godina, šifra posla, mesec, `kriterijum`, `koef`, `koef2`,
`koef3`, `profitni` — **samo redovi sa `aktivan='D'`** za mesece koji ulaze u izabrani
period. Posao mora postojati u izvornom šifarniku.

Koeficijenti centra `koef1/koef2/koef3` čitaju se iz `blokraspodela` za godinu i centar
aktuelnog posla.

> **[P] Šta NIJE osnovica:** polja `posao_mes.prihod`, `trosak` i `iznos`. Procedure 52 i
> 52nt mogu u njih upisati **različite vrste rezultata**, pa se ne koriste.

#### Osnovice cele firme [P]

Za svaki posao i mesec u izabranom intervalu računa se lokalni `P−R`, sa isključenjima iz
[6.1.5](#615-prihodi-rashodi-i-rezultat-bez-zt). Prema **mesečnom kriterijumu posla**
rezultat ulazi u jednu od tri osnovice:

```text
B1 = zbir (P − R) za posao/mesec sa kriterijumom 1
B2 = zbir (P − R) za posao/mesec sa kriterijumom 2
B3 = zbir (P − R) za posao/mesec sa kriterijumom 3
```

To su osnovice **cele firme**, ne samo prikazanog centra. Posao/mesec bez odgovarajućeg
aktivnog pravila **ne doprinosi** osnovici. Za osnovice se proverava **kriterijum**, a
**ne** zahteva se `profitni='P'`.

#### Koeficijent posla i konačna formula [P]

Za ciljni posao koriste se **samo njegovi aktivni mesečni redovi sa `profitni='P'`**.
Neka je `M` broj kalendarskih meseci koje zahvata izabrani period unutar godine:

```text
M  = završni_mesec − početni_mesec + 1
Kj = zbir koeficijenata ciljnog posla za kriterijum j / M
Cj = koeficijent centra za kriterijum j
Aj = Bj × Cj / 100 × Kj / 100
ZT = −(A1 + A2 + A3)
Rezultat posle raspodele = P − R − ZT
```

Nedostajući pojedinačni koeficijent tretira se kao **nula**. Izračunati ZT zaokružuje se na
dve decimale metodom **`ROUND_HALF_UP`**.

**Primer [P]:** osnovica `B1 = −1.000`, centar dobija 40%, posao dobija 25% centra.
Alokacija rezultata je `−100`, pa je `ZT = 100`. Na ekranu je ZT `−100`, a rezultat posla
umanjuje se za 100.

> Ako osnovica ima **pozitivan** rezultat, raspoređeni ZT može biti **negativan**. Tada je
> njegov prikaz pozitivan i **povećava** rezultat posla. [P]

#### Zašto godišnji ZT nije zbir mesečnih [P]

Godišnji ZT je **osnovica godišnjeg perioda × prosečni koeficijent posla**, a ne zbir 12
zasebno izračunatih mesečnih ZT.

**Primer, centar 50%:** osnovice januar `−1.000`, februar `−2.000`; koeficijenti posla 20%
i 40%.

| Način obračuna | Rezultat |
|---|---|
| Za oba meseca odjednom | `3.000 × 50% × 30% = 450` |
| Zbir samostalnih meseci | `100 + 400 = 500` |

Razlika proizlazi iz **periodnog pravila procedure 53**.

Za proizvoljne datume osnovica uzima samo knjiženja unutar tih datuma, ali **broj meseci i
koeficijenti računaju se po zahvaćenim kalendarskim mesecima**. Nema proporcionalnog
umanjenja koeficijenta po broju dana.

#### Nepotpuni meseci i nedostupnost [P]

| Slučaj | Ponašanje |
|---|---|
| Pravilo postoji za 10 od 12 meseci | **Imenilac ostaje 12.** Iznos se prikazuje kao **nepotpun**, sa zvezdicom/upozorenjem |
| „Nepotpun“ | **Nije isto što i „nula“** |
| Nema tačno jedne raspodele centra/godine | ZT **nije dostupan** |
| Duplirana pravila posao/mesec | ZT **nije dostupan** |
| Ciljni posao nema aktivno profitno pravilo | ZT **nije dostupan** |

Kada ZT nije dostupan, ni rezultat posle ZT nije potvrđen — ali direktni `P−R` može i dalje
biti dostupan.

U zbirnoj tabeli **period kroz više godina razdvaja se po kalendarskim godinama**. Svaka
godina ima svoje koeficijente i zaokružen ZT; iznosi se sabiraju. Ako je neka godišnja
komponenta nedostupna, **ukupan ZT nije prikazan kao poznat iznos**.

---

### 6.1.7. Priliv, odliv i neto gotovina

Ovo je obračun po pravilima pripreme **`SPFINizv52nt`**.

> **[P] Nije prost zbir prometa bankovnog računa, niti evidencija koja povezuje svaku
> fakturu sa uplatom.** Originalna poslovna procedura se pri prikazu **ne izvršava** —
> primenjena su njena pravila.

#### Ulazni skup i početni izbor [P]

Čita se izvorni `nalog_z` za firmu, izvornu godinu `god`, datum naloga u intervalu i posao.
Stavke se sabiraju po **kontu, datumu i vrsti naloga**.

> **Prazna ili NULL šifra posla pripisuje se `111111`**, prema metodologiji procedure.
> Kod P/R se prazna šifra **ne** preimenuje na ovaj način. [P]

U početni skup ulaze:

1. Nalozi čiji povezani tip `tipnal.sif_tipnal` ima oznaku **`NT`**, na kontima gde
   `konto.nt` **nije NULL i nije `NT`**.
2. Dodatno, nalozi **`ON`** na kontima:
   `61420, 61300, 61520, 52901, 52991, 52610, 52620, 57910, 53011, 61211, 61421, 61521`.

Za oba izbora potrebne su odgovarajuće šifre konta i vrste naloga. **Ne primenjuje se
automatski filter zatvaranja iz P/R** — 52nt ima sopstvena pravila odabira i zamene.

#### Zamena PDV-a [P]

Iz radnog skupa **uklanjaju se redovi na `47900`**. Zamenjuje ih obračun iz `pdv_arhiva` za
firmu/posao, sa `pdv_nacoporez='S'` i `br_obr<>0`:

```text
PDV = zbir (pdv + pdv8) za tip I
    − zbir (pdv + pdv8) za ostale tipove
```

SQL sabiranje koristi izvorni izraz `pdv+pdv8`; **NULL komponenta se ne pretvara
pojedinačno u nulu**. Ako agregat nema iznos, preuzima se nula.

**Izbor PDV obračuna** određuje se iz najmanjeg i najvećeg meseca knjiženja `47900` sa
`duguje<>0`, unutar traženog intervala, **za celu firmu**:

| Korak | Pravilo |
|---|---|
| Donja granica | Prvi mesec **minus jedan** |
| Gornja granica | Poslednji mesec **minus jedan** |
| Granica 0 | Pretvara se u **−1** |
| Ako je prvi mesec 1 | Uključuje se i **`br_obr=12` prethodne godine** |
| Nema utvrđenih meseci | Granice se postavljaju na **−1** |

**Primeri [P]:** uplata u avgustu bira obračun 7; samo januar bira decembar prethodne
godine; januar–mart bira januar/februar tekuće i decembar prethodne godine.

Dobijeni PDV dodaje se na `47900` kao **duguje**, potražuje 0, sa **datumom kraja izabranog
perioda**. Negativan PDV ostaje negativan odliv.

#### Zamene obaveza troškovima [P]

Primenjuju se **redom**. Uklanjaju se navedene obaveze iz radnog skupa i dodaju izvorne
stavke troškovnog konta iz perioda, sa **izvornim duguje** i **potražuje postavljenim na 0**:

| Uklonjena konta | Dodato konto |
|---|---|
| `46520, 48923, 48900, 48903` | `52400` |
| `46510, 48920, 48981` | `52300` |
| `46500, 48921, 48980` | `52200` |
| `46400, 48960` | `52600` |

> **[P]** Dodavanje zamenskih troškova **nije ograničeno na naloge tipa NT**. Zato takav
> odliv **ne treba tumačiti kao stvarno plaćenu pojedinačnu obavezu u periodu**.

#### Zarade u obračunu toka [P]

**Uklanjaju se:** `45000, 45100, 45200, 45220, 45210, 45310, 45312, 45314`.

**Dodaju se** izvorne stavke na kontima `element.knt_troska` iz baze zarada, **osim `52024`
i `52026`**, uz dodatno konto **`52100`**. Za dodate stavke koristi se **duguje**, dok je
potražuje 0.

Upit šifarnika `element` bira različita konta **bez dodatnog filtera preduzeća**; knjiženja
koja se dodaju i dalje su ograničena na traženu firmu, posao i period.

> **[P]** Ovo pravilo novčanog toka **nije** obračun pojedinačnih zarada zaposlenih niti
> konačan pokazatelj ukupnog troška zarada centra.

#### Refundacije [P]

**Uklanjaju se:** `45400, 45410, 45420, 45503, 45600, 22500, 22510, 22520, 23837`.

**Dodaju se** izvorne stavke sa `22500, 22510, 22520, 23837`, sa:

```text
duguje   = 0
potražuje = izvorno potražuje − izvorno duguje
```

Potrebna je postojeća šifra vrste naloga, ali **ne mora biti tip NT**. Negativna
refundacija **umanjuje priliv**.

#### Završni izbor i sabiranje [P]

Posle transformacija uklanjaju se:

- svi redovi čiji konto počinje sa **`241`**;
- redovi **bez konta u šifarniku**;
- redovi čiji **mesec datuma nije aktivan** za posao u `posao_mes` (`aktivan='D'`).

```text
I = zbir završnog potražuje
O = zbir završnog duguje
Neto gotovina = I − O
```

Priliv i odliv se **zasebno** zaokružuju na dve decimale sa `ROUND_HALF_UP`, pa se
oduzimaju. Na ekranu je odliv `−O`.

> **[P]** Operacije su niz uklanjanja i dodavanja; **ne radi se završna deduplikacija** po
> originalnom ključu knjiženja. Dodate troškovne stavke **ne znače „sve jedinstvene
> bankovne transakcije“**.

**Ilustracija [P]:** priliv kupca 900, refundacija 20, odliv dobavljača 300, obračunati PDV
40 i dodati trošak zarada 100 daju `I = 920`, `O = 440`, neto `480`.

#### Dostupnost i godišnje razlike [P]

| Slučaj | Ponašanje |
|---|---|
| Bez aktivne mesečne evidencije šifre | Prikazuje se **nedostupan podatak** |
| Aktivni samo neki meseci perioda | Iznos ima **oznaku nepotpunosti** |
| Duplirana mesečna evidencija | Obračun **nije pouzdan** |

PDV red nosi **datum kraja perioda**. Ako završni mesec nije aktivan za šifru, taj red
**otpada** pri završnom filtriranju.

> **[P] Zbog ove i drugih periodnih operacija, obračun cele godine ne mora biti jednak
> zbiru odvojeno pokrenutih meseci.** Posebno je značajno kod izbora **cele tekuće godine**
> sa budućim/neaktivnim mesecima.

Zbirna tabela kroz više godina sabira zasebne godišnje obračune; nedostupna godina sprečava
prikaz ukupnog iznosa kao potpunog. Grupno učitavanje za više šifara koristi **istu**
računsku funkciju kao pojedinačni detalj.

#### Konta upisana u obračun toka gotovine

Ovo je **opis onoga što kod radi**; problem koji iz toga proizlazi vodi se kao
[P-42](#p-42--konta-i-pravila-toka-gotovine-upisani-su-u-kod).

U `services/cash_flow.py` su upisani spiskovi konta [P]:

| Namena | Konta |
|---|---|
| Dodatni `ON` nalozi | `61420, 61300, 61520, 52901, 52991, 52610, 52620, 57910, 53011, 61211, 61421, 61521` |
| Zamena obaveza troškovima | `46520/48923/48900/48903 → 52400`, `46510/48920/48981 → 52300`, `46500/48921/48980 → 52200`, `46400/48960 → 52600` |
| Zarade — uklanja se | `45000, 45100, 45200, 45220, 45210, 45310, 45312, 45314` |
| Zarade — dodaje se | `element.knt_troska` osim `52024`, `52026`, plus `52100` |
| Refundacije — uklanja se | `45400, 45410, 45420, 45503, 45600, 22500, 22510, 22520, 23837` |
| Refundacije — dodaje se | `22500, 22510, 22520, 23837` |
| PDV | `47900` |
| Završno isključenje | sve što počinje sa `241` |

Isto važi i za konta u prihodima i rashodima: `59900`, `69900`, `20400`, `20500`,
`61420`, `61421`, `61521`, `64002`. [P]

> **[P]** Ista konta postoje i u izvornim procedurama `SPFINizv52/52nt`, pa je kod
> **verna kopija** postojećeg poslovnog pravila — nije izmišljeno u aplikaciji.

---

### 6.1.8. Grafikoni, učešća i rangiranje

Finansijski pregled prikazuje **centre, zatim poslove**. Za isti red prikazuje `P`, `R` i
rezultat `P−R`, **bez dodatnog ZT**.

> **[P] Pažnja:** prikazani rashod u ovim grafikonima je **obračunski `R`**, a ne promenjeni
> znak `−R` iz tabele šifara.

```text
Učešće u prihodima      = prihod reda   / ukupan prihod dostupnog perioda   × 100
Učešće u rashodima      = rashod reda   / ukupan rashod dostupnog perioda   × 100
Učešće u neto rezultatu = rezultat reda / ukupan rezultat dostupnog perioda × 100
```

| Pravilo | Ponašanje |
|---|---|
| Imenilac je nula | Procenat je **crtica** |
| Značenje procenta | Učešće u **ukupnom**, ne prema najvećem redu |
| Podloga stubića | Predstavlja **100%** odgovarajuće kolone |
| Popunjenost | `min(abs(procenat), 100)%` |
| Procenat iznad 100% | **Ostaje ispisan**, a na stubiću se pojavljuje oznaka **`»`** |
| Boja negativne vrednosti | Određuje se **znakom iznosa**, ne samo znakom procenta |

**Primer [P]:** jedan centar ima rezultat 120, ostali zbirno −20. Ukupno je 100, pa je
učešće prvog centra **120%**. To samo po sebi **nije greška**. Ako je ukupan rezultat
negativan, znak procenta treba čitati zajedno sa znakom iznosa.

#### Redosled i rangiranje [P]

Redovi su poređani po `P−R` **opadajuće**; kod istog rezultata po šifri. Svi centri su
vidljivi, a kod poslova **prvih osam** redova uz proširenje ostalih.

Rangiranje daje **tri najbolja i tri najgora posla**, odnosno **po jedan** najbolji i
najgori centar. Uslov je **neprazna šifra i nenulti prihod ili rashod**.

| Napomena | |
|---|---|
| Poslovi/centri **bez šifre** | Ulaze u zbir i grafikone, ali **ne u rangiranje** |
| Mali broj poslova | Liste najboljih i najgorih mogu se **preklapati** |
| „Najgori“ | Znači **najmanji rezultat u skupu** — ne mora značiti gubitak |

---

### 6.1.9. Fakture IF i interne ON

#### Izdate fakture IF [P]

Biraju se **aktivna, korisniku dostupna** lokalna knjiženja tačne šifre posla sa
`journal_type='IF'` i **tačnim kontima `20400` ili `20500`**, prema **datumu dokumenta**,
u izabranom mesecu/godini. Izvorna godina knjiženja **takođe mora odgovarati** izabranoj
godini — nijedna godina nije fiksno upisana u aplikaciju. U bazi se polje konta zove `knt`.

| Element | Pravilo |
|---|---|
| **Jedan red** | Godina + broj naloga + veza dokumenta + grupa partnera + šifra partnera |
| Naziv partnera | Agregat **MAX** |
| Datum | **MIN** datuma uključenih stavki; kod više različitih ispisuje se i **poslednji** datum grupe |
| **Kolona iznosa** | **Zbir `duguje − potražuje`** na navedenim kontima potraživanja |

> **[P]** Ne koristi se klasa 6 i **ne dodaje se PDV zasebno** — preuzima se proknjižen
> iznos potraživanja. Kod fakture podeljene na više poslova ovo je **samo deo na izabranoj
> šifri**. Storna zadržavaju znak. **Neproknjižene fakture nisu obuhvaćene.**

Podnožje je zbir **svih** takvih iznosa izabranog perioda — ne samo vidljive strane ili
rezultata pretrage. **Broj redova predstavlja grupe naloga/dokumenata/partnera; nije
garantovano broj jedinstvenih originalnih faktura** iz prodajnog sistema.

> **[P] Iznos IF nije pokazatelj prihoda ni preostalog duga.** Bira samo IF, bez naknadnih
> uplata drugih vrsta naloga. Od glavnog prihoda razlikuje se po kontima, PDV-u u
> proknjiženom potraživanju, datumu dokumenta naspram knjiženja i drugim vrstama naloga.
> **Tabela ne prikazuje iznos naplaćen po svakoj fakturi.**

#### Interne fakture ON [P]

Prema pravilu potvrđenom 18.09.2026., zaseban tab prikazuje `sif_vrs='ON'` i **tačna konta
`61420`, `61421`, `61521`, `64002`**. Koristi iste granice datuma dokumenta, izvornu godinu,
šifru posla, aktivna lokalna knjiženja i prava kao IF. Grupisanje je isto kao kod IF.

```text
Iznos ON = Σ(potražuje − duguje) na ta četiri konta
```

Podnožje sabira ceo izabrani skup. **Negativno potražuje ostaje negativan iznos** — ne
koristi se apsolutna vrednost. Ostala `ON` knjiženja **ne ulaze** u ovaj tab.

> **[P]** Prikaz internih faktura **ne dodaje njihov zbir još jednom prihodu** —
> odgovarajuća knjiženja već učestvuju u P/R. Tab se učitava preko AJAX-a u pozadini,
> nezavisno od otvaranja kartice, sa numeričkim i datumskim sortiranjem.

---

### 6.1.10. Struktura rashoda po kontima

U tabu **Rashodi** detalja posla koristi se `knt3 = prva tri znaka konta`. Biraju se
knjiženja klase 5 u periodu prema **datumu knjiženja**, uz isključenja ZAT/59900/69900. [P]

```text
R_knt3            = zbir (duguje − potražuje) za isti knt3
Prikaz rashoda    = −R_knt3
Učešće knt3       = R_knt3 / ukupan R posla u periodu × 100
```

| Slučaj | Ponašanje |
|---|---|
| Ukupan `R` je nula | Učešće je **crtica** |
| Korekcije | Mogu dati **negativno učešće** ili **učešće iznad 100%** |
| „Broj knjiženja“ | Broj **uključenih stavki**, a ne broj faktura |

Link **Knjiženja** prenosi posao, isti period, prefiks konta i vrstu rashoda.

> **[P]** Izvor je lokalna kopija `nalog_z`; **ne pokreće se** zaseban bruto bilans po OJ.
> Konto se grupiše **po šifri posla**, a ne automatski po `nalog_z.oj`. Zbirni izveštaj
> „po kontima“ koristi **puno konto** — to treba razlikovati od `knt3` taba. Stavka
> „Struktura rashoda“ uklonjena je iz menija, ali detalj konta ostaje dostupan.

---

### 6.1.11. Zaposleni i zarade

Iz `Zarada` biraju se firma, godina, meseci i **tačna šifra posla**. Potrebno je [P]:

- da je `dinara` **ili** `rekol` različito od nule; **NULL se tretira kao nula**;
- da postoji odgovarajući `PomLD` za firmu/godinu/mesec/broj obračuna sa **`status_obr='Z'`**.

Ime se povezuje iz `Radnik` po firmi i `rasif`. **Nedostajuće ime ne izbacuje zaposlenog** —
prikazuje se obaveštenje da ime nije dostupno.

| Kolona / zbir | Pravilo |
|---|---|
| Mesec obračuna | Mesec iz `Zarada`; za sortiranje prvi dan tog meseca |
| Šifra zaposlenog | `rasif` |
| Ime | **MAX** skraćenog `Radnik.ranaz` unutar grupe |
| Broj zaključenih obračuna | **`COUNT(DISTINCT br_obr)`** po zaposlenom i mesecu |
| Ukupan broj zaposlenih u periodu | Broj **različitih `rasif`** iz rezultata, **jednom za ceo period** |

> **[P]** Više elemenata zarade **ne umnožava** zaposlenog. Zaposleni prisutan u šest meseci
> ima **šest mesečnih redova**, ali u godišnjem ukupnom broju doprinosi **sa jedan**.
> Koriste se **svi** odgovarajući zaključeni obračuni, ne samo obračun sa najvećim brojem.

> **[P] Šta ovo jeste, a šta nije:** evidencija **zaposlenih u obračunima na šifri**.
> **Nije** dokaz prisustva na radu, obračun punih radnih angažovanja iz sati, ni kompletan
> kadrovski spisak centra.

| Slučaj | Ponašanje |
|---|---|
| Nema nijednog zaključenog obračuna u periodu | Ukupan broj je **crtica** |
| Ima zaključenih obračuna, ali nema zapisa za posao | Broj evidentiranih zaposlenih može biti **0** |
| Otvoreni obračuni (`O`) | Posebno označeni i **izuzeti** |

> Postojanje bar jednog zaključenog obračuna u mesecu **ne potvrđuje** da su svi obračuni
> tog meseca zaključeni. [P]

**Još nije izračunato [P]:** istorijski spisak i broj svih zaposlenih centra, njihov ukupan
trošak zarada i kompletan spisak stvarnog rada po poslu. Za to su potrebna potvrđena
pravila pripadnosti centru i raspodele svih elemenata/doprinosa. `Zarada.dinara` **se ne
prikazuje** kao proizvoljno sabran konačni trošak.

> **Zamka [P]:** lokalno `Employee.job_code` označava **zanimanje**, a ne poslovnu šifru
> posla.

---

### 6.1.12. Vozila, zaduženja i putni nalozi

#### Vozila na šifri posla [P]

Koristi se istorija `JobCode`: vozilo, poslovna organizaciona jedinica i datum dodele.

> **Dodela važi od svog datuma do dana pre naredne dodele istog vozila**, uključujući
> prelazak na drugi posao. Bez naredne dodele tretira se kao **otvorena** do kraja traženog
> intervala.

```text
U periodu od = max(početak analize, datum dodele)
U periodu do = min(kraj analize, dan pre naredne dodele)
```

Prikazuje se **samo neprazan presek**. Vozilo koje se vrati na istu šifru može imati više
redova — **broj redova zato nije broj različitih automobila**.

Registracija je **poslednja evidentirana `TrafficCard.registration_number`** sa datumom
izdavanja do kraja perioda — ne nužno registracija na prvi dan dodele. Ako takve kartice
nema, prikazuje se **broj šasije**. Naziv je marka + model.

> **[P]** U ovom tabu **nije izračunat novčani trošak vozila**. Otvorena dodela opisuje
> **poslednje evidentirano stanje**, ne potvrdu da promene koje nisu unete nisu postojale.

#### Zaduženja vozila po zaposlenom [P]

Izvor je `VehicleTravelOrder`, sa pravilima pristupa te evidencije. Zaduženje se povezuje sa
poslom **preko istorijskih dodela vozila**.

```text
Na šifri od = max(početak analize, početak dodele, datum zaduženja)
Na šifri do = min(kraj analize, kraj dodele, datum razduženja ako postoji)
```

Prikazuju se samo intervali gde je **početak ≤ kraj**. Datumi su uključivi.

> **[P]** Evidencija koristi **datume bez sata**, pa se preuzimanje i razduženje **istog
> dana ne razdvajaju po časovima**.

Kolone: izvorni datum zaduženja, broj `rbz` (ili PN broj ako ga nema), registracija/šasija,
vozilo, šifra i ime zaposlenog, izvorni datum razduženja, presek na poslu i status.

> **[P] Status je trenutno evidentiran:** „Zatvoreno“ ako postoji `closed_at`, inače
> „Otvoreno“. **Nije rekonstruisan istorijski status** na poslednji dan izabranog meseca.
> Povratak vozila na posao može dati više redova istog zaduženja. **Kilometraža i troškovi
> ne raspoređuju se proporcionalno danima.**

#### Putni nalozi [P]

Biraju se `PutniNalog` za tačnu poslovnu šifru, sa **datumom putovanja** u periodu, **bez
storniranih**. Važe postojeća prava za centre putnih naloga.

Prikazuju se datum putovanja, broj naloga, zaposleni, mesto, vozilo/prevoz i broj dana. Ako
nema povezanog zaposlenog ili vozila, koristi se slobodno uneti naziv iz naloga.

> **[P] Broj dana je izvorno polje `number_of_days`**, a ne preračunat broj dana unutar
> izabranog meseca. Put koji **počne u periodu** ulazi sa **celim** evidentiranim brojem
> dana; put koji je počeo **pre** perioda **ne uključuje se** samo zato što se nastavio.

> **[P]** Ovaj tab **ne računa** dnevnice, avanse, konačan obračun putovanja ni trošak
> goriva. `PutniNalog` je **druga evidencija** od `VehicleTravelOrder` (lična zaduženja).
> Ranije provere **nisu potvrdile** potpunu istoriju službenih putovanja za 2025 — **prazan
> spisak nije dokaz da putovanja nije bilo.**

---

### 6.1.13. Potraživanja na detalju posla

Tab „Potraživanja“ preuzima lokalni **objavljeni snimak** preko
`potrazivanja.services.reports.job_balances`, za tačnu šifru i dozvoljeni obuhvat
Potraživanja. **Pri otvaranju nema upita prema staroj Naplati niti udaljenim pogledima.** [P]

Iznosi su zbirovi `ReceivablePosition.balance` (`duguje − potražuje`):

| Prikaz | Razred iz datuma dospeća na datum snimka |
|---|---|
| Nedospelo / bez datuma | `0.1` — dospeće na dan snimka ili kasnije, **ili datum nedostaje** |
| Do 30 dana | `30` |
| 31–45 dana | `45` |
| 46–60 dana | `60` |
| 61–90 dana | `90` |
| 91–180 dana | `180` |
| Preko 180 dana | `181` |
| **Dospelo** | Sve sa `baket != 0.1` |
| **Ukupno** | Zbir svih saldo vrednosti izabranog skupa |

Za dospele stavke broj dana kašnjenja je `snapshot.as_of_date − due_date`. Granice su
**uključive**. Koristi se **ista funkcija razvrstavanja** kao u Potraživanjima — vidi
[6.8](#68-potraživanja--obračuni).

Grupisanje je po **identitetu partnera i porodici konta (`204`/`205`)**. Partner sa domaćim
i inostranim stavkama može imati **dva reda**. Oznaka važnog kupca **ne zavisi od napomena**
i **ne menja iznos**. Link partnera otvara Potraživanja na istom snimku. [P]

Svaka lokalna stavka ulazi u **tačno jedan** od sedam razreda. „Dospelo“ je zbir šest
razreda kašnjenja; „Ukupno“ uključuje i nedospele stavke i stavke bez datuma.

> **[P] Nedostajući datum dospeća zadržava razred `0.1` i nije dokaz da potraživanje nije
> dospelo** — vidi [P-35](#p-35--nepoznato-dospeće-prikazuje-se-kao-nedospelo).

> **[P]** Prikazuje se **poslednji uspešan lokalni snimak**, **bez preseka na kraj izabranog
> meseca**. Prikazani su datum stanja (`as_of_date`) i vreme preuzimanja
> (`source_observed_at`). Bez objavljenog snimka podaci su označeni kao **nedostupni**, a ne
> kao nulti dug.

> **[P] Ukupan dug nije prihod perioda, priliv ni iznos naplaćen u mesecu.** Negativan saldo
> zadržava znak; aplikacija ga **ne preklasifikuje** u avans. **Nije implementirano**
> pouzdano povezivanje „ova IF faktura je naplaćena ovom uplatom“ niti poseban spisak
> plaćenih računa dobavljača.

---

### 6.1.14. Knjiženja, grupisanja i broj redova

Knjiženja prikazuju datum knjiženja, identitet naloga/stavke, centar, posao, OJ knjiženja,
konto, partnera, vezu/opis dokumenta, datum dokumenta i izvorne iznose duguje/potražuje. [P]

> **[P]** Duguje i potražuje u ovoj tabeli zadržavaju **izvorni znak** — redovan iznos
> duguje **nije** automatski prikazan kao rashod sa minusom. **Trošak se određuje formulom
> prema kontu**, a ne nazivom strane knjiženja.

| Pravilo | Ponašanje |
|---|---|
| Filter „Sva knjiženja“ | Uključuje i **zatvaranja**, dok P/R pokazatelji **i tada** primenjuju isključenja |
| Ukupan promet iznad tabele | Sabira **sve** stavke koje prolaze filtere — **promet nije jednak prihodu/rashodu** |
| „Broj knjiženja“ u grupama | **`COUNT` stavki**, ne broj različitih dokumenata |

Grupisani izveštaji koriste **iste P/R izraze**: centar; šifra posla uz naziv/centar; puno
konto uz naziv; kalendarska godina/mesec datuma knjiženja.

Tabela **Šifre posla** ima **11 kolona**: šifra, naziv, centar i osam finansijskih
pokazatelja. Početno prikazuje **100 redova**. Dugme sa šifrom otvara detalj.

> **[P]** **Nije uveden dodatni zbir nepoznatih ZT/tokova** koji bi nedostajuće podatke
> tretirao kao nulu.

> **[P]** Promena strane ili tekstualna pretraga DataTables tabele **ne menja osnovni period
> obračuna** — zbirovi izračunati za period ostaju zbirovi perioda. Knjiženja i istorija
> sinhronizacije pretražuju/sortiraju **na serveru**; ostale finansijske tabele obrađuju
> preuzet skup **u pregledaču**.

**Excel [P]:** za zbir šifara koristi iste znakove i iznose osam pokazatelja, napomenu o
nedostupnosti/nepotpunosti i link na detalj. Izvoz Knjiženja čuva izvorno duguje/potražuje.

> **Excel nije istorijski arhiviran snimak izvora** samo zato što je izabran istorijski
> period. [P]

---

### 6.1.15. Nule, nedostajući podaci, znakovi i sortiranje

| Oznaka | Značenje |
|---|---|
| `0,00` / `0.00` | Izračunat iznos je **nula** u dostupnom skupu |
| **Crtica** ili „Nema podataka“ | Iznos **nije potvrđen/dostupan** — **nije zamena za nulu** |
| **Zvezdica** uz iznos | Iznos postoji, ali obračun ima **nepotpunu mesečnu pokrivenost** |
| Upozorenje o godinama | Nema potvrđenog uspešnog preuzimanja za deo intervala |
| Prazna tabela | Nema odgovarajućih zapisa; **ne dokazuje odsustvo aktivnosti** |

U detalju posla finansijski pokazatelji traže **uspešnu sinhronizaciju koja pokriva izabranu
godinu**. U zbirnoj tabeli proveravaju se **sve godine intervala**; nepoznat deo sprečava da
ukupan broj bude predstavljen kao potpun. [P]

#### Boje i znakovi [P]

| Znak | Prikaz |
|---|---|
| Pozitivan | Svetlozelena pozadina, taman podebljan tekst, `+` |
| Negativan | Crvena pozadina, beli tekst, `−` |
| Nula | Neutralna siva |

> **[P] Boja znači znak iznosa, ne „dobro“ ili „loše“** — pozitivan dug kupca i pozitivan
> prihod imaju **različito** poslovno značenje.

#### Zaokruživanje i sortiranje [P]

Novčana polja čuvaju se kao decimalni iznosi sa **dve decimale**. Pri uvozu se primenjuje
`quantize(0.01)`; ZT i tokovi na kraju eksplicitno koriste **`ROUND_HALF_UP`**. Procenti se
računaju iz iznosa, a ispisuju na dve decimale.

> **Zbir zaokruženih pojedinačnih procenata zato može biti 99,99% ili 100,01%.** [P]

Numeričko sortiranje koristi **sirovu vrednost sa znakom**, nezavisno od boje, oznake i
lokalizovanog teksta:

```text
rastuće:  −1.000, −100, −2, 0, 2, 100
opadajuće: obrnuto
```

**Nedostajući brojevi ostaju na kraju u oba smera.** Datumi se sortiraju po izvornoj
datumskoj/ISO vrednosti, **a ne po tekstu `DD.MM.GGGG`**. [P]

---

### 6.1.16. Sinhronizacija, istorija i procedure

#### Šta radi preuzimanje [P]

`sync_ledger(year_from, year_to, company)` čita **sve** stavke izabranih godina. **Nema
pouzdanog izvornog vremena izmene** koje bi omogućilo preuzimanje samo novih redova.

| Osobina | Vrednost |
|---|---|
| Obuhvat | Firma `FINANSIJE_COMPANY` (1), godine **od 2025.** |
| Identitet stavke | firma + godina + vrsta naloga + broj naloga + stavka |
| Način | **Ceo opseg pri svakom prolazu** |
| Novi stabilni ključ | **Dodaje se** |
| Izmenjen sadržaj | **Ažurira se** |
| Nestala stavka | **`active = False`** — **ne briše se fizički** |
| Ponovo pojavljena | Vraća se **pod istim lokalnim ID-em** |
| **Kontrola pre i posle objave** | **Broj stavki, zbir duguje i zbir potražuje po godini i kontu** |
| Nepoklapanje kontrole | **Poništava lokalnu objavu** |
| Zaključavanje | SQL Server `sp_getapplock` — pokriva i komandnu liniju |
| Prazan izvor | **Ne može** automatski deaktivirati postojeći neprazan obuhvat |

Lokalni upis i uspešan zapis istorije su **jedna transakcija**. Šifarnici se osvežavaju u
istom postupku.

> **[P] Granica pouzdanosti:** izvorni podaci se čitaju **bez `NOLOCK`**, ali kontrolni
> zbirovi **nisu garancija jednog transakcijskog snimka** udaljene baze. Istovremene promene
> koje zadrže iste kontrolne zbirove mogu ostati za sledeći prolaz.

#### Značenje kolona istorije [P]

| Kolona | Značenje |
|---|---|
| Početak / završetak | Vreme početka i kraja pokušaja, u vremenskoj zoni aplikacije |
| Godine | Zatraženi raspon izvornih godina |
| Status | U toku, uspešno ili neuspešno |
| **Preuzeto** | Broj stavki u uspešno objavljenom preuzetom skupu |
| Novo | Broj novih lokalnih knjiženja |
| Izmenjeno | Broj ažuriranih ili **ponovo aktiviranih** knjiženja |
| Nepromenjeno | Aktivna knjiženja istog sadržaja |
| Uklonjeno | Ranije aktivne stavke kojih više nema u obuhvatu, sada neaktivne |

> **Za uspešan prolaz važi `preuzeto = novo + izmenjeno + nepromenjeno`.** „Uklonjeno“ se
> **ne dodaje** preuzetom broju. Promene šifarnika nisu stavke tog brojača. [P]

> **[P]** Kod neuspeha **ne treba tumačiti početne nulte brojače kao potvrdu praznog
> izvora** — merodavni su status i greška.

#### Ručno pokretanje i Celery [P]

Dugme u Sinhronizaciji **direktno poziva** funkciju `sync_ledger` — **ne šalje Celery
zadatak**. I Celery i komandna linija koriste **istu** funkciju, kontrolu i zaključavanje.
Izbor je tekuća godina ili sve godine od 2025.

Registrovane Celery ulazne tačke: `sync_ledger_task`, `sync_current_year`, `sync_all_years`,
red `sync`. Predviđen raspored: **tekuća godina svakog sata u :20**, **sve godine dnevno u
03:50**. Osvežavanje `nalog_z` procedure: **10:00 i 11:00**.

> **[P]** To je **definicija rasporeda**, a ne tvrdnja da su periodični zadaci na svakom
> okruženju aktivni — aktivnost se proverava u konfiguraciji Celery Beat-a.

**Otvaranje pregleda ne pokreće sinhronizaciju.** Uspeh se prijavljuje **nakon kontrolnih
zbirova**. Neuspeh zadržava prethodno uspešno objavljeno stanje. [P]

#### Odnos prema poslovnim procedurama [P]

Aplikacija **može** preko Django veze izvršiti SQL proceduru, ali postojeći finansijski
prikazi koriste **`SELECT` upite i računsku logiku**, bez izvršavanja izvornih poslovnih
procedura:

| Obračun / procedura | Uloga u sadašnjoj aplikaciji |
|---|---|
| **52 / 53** | Pravila kriterijuma, centara i prosečnih koeficijenata **primenjena u ZT** |
| **52nt** | Pravila izbora i transformacija **primenjena u novčanim tokovima** |
| `SPLdKnjizenje` | **Nije pokrenuta** iz prikaza; složenost raspodele zarada razlog je što se ukupan trošak zarada ne izmišlja prostim zbirom |

> **[P] Zašto se sačuvani rezultati procedura ne čitaju:** utvrđeno je da **52 i 52nt
> upisuju zajednička polja `posao_mes`**, a **53 menja koeficijente `posao`**. Čitanje
> njihovih sačuvanih rezultata **bez poznavanja poslednjeg izvršavanja nije pouzdan izvor**.

Lokalni izuzetak su sistemske procedure `sp_getapplock` / `sp_releaseapplock` za
zaključavanje sinhronizacije — to **nisu** obračunske procedure izvornog poslovanja.

---

### 6.1.17. Kontrolni postupak

Za proveru konkretnog iznosa pratiti ovaj redosled [P]:

| # | Korak |
|---|---|
| 1 | Zapisati **firmu, tačnu šifru, centar, datume i korisnikov obuhvat pristupa** |
| 2 | Proveriti obuhvat **poslednjih uspešnih sinhronizacija** — ne pretpostaviti da su sve godine jednako sveže |
| 3 | `P` i `R` proveriti na knjiženjima klasa **6** i **5**, bez `ZAT`/`59900`/`69900` |
| 4 | Potvrditi da se rashod prikazuje **sa suprotnim znakom** i proveriti `P−R` |
| 5 | Za ZT proveriti **tri osnovice firme**, mesečne kriterijume, centar, **tri koeficijenta centra**, aktivne profitne koeficijente posla i **imenilac `M`** |
| 6 | Za tokove proveriti **ceo redosled 52nt** — naročito period PDV-a, dodate troškove, refundacije i **aktivnost završnog meseca** |
| 7 | IF proveriti kao `duguje − potražuje` na `20400`/`20500`; ON kao `potražuje − duguje` na četiri potvrđena konta — uz **istu izvornu godinu, datum dokumenta i šifru posla** |
| 8 | Potraživanja tumačiti kao **stanje izvora**, zaposlene kao **evidenciju zaključenih obračuna**, vozila/zaduženja kao **intervale** |
| 9 | **Uskladiti period** pri otvaranju detalja. Godišnji ZT i tokove **ne proveravati zbirom 12 nezavisnih mesečnih obračuna** |

#### Brze provere

| Provera | Kako |
|---|---|
| Rezultat reda | `prihod + prikazani rashod + prikazani ZT` |
| Neto gotovina | `prikazani priliv + prikazani odliv` |
| Prihodi/rashodi prema izvoru | Nezavisan upit nad `nalog_z` povezan sa `posao`, uz ista isključenja |
| Potpunost sinhronizacije | Ekran sinhronizacije: brojači i kontrolni zbirovi po godini i kontu |
| Zbirna tabela naspram detalja | **Najpre uskladiti periode** |

#### Zabeleženi kontrolni iznosi [P]

Iz provere 18.09.2026., šifra `413111`:

| Pokazatelj | Period | Iznos |
|---|---|---|
| Zajednički troškovi | avgust 2026. | **1.797.391,32 RSD** |
| Priliv | avgust 2026. | **53.087.225,36 RSD** |
| Odliv | avgust 2026. | **4.501.917,06 RSD** |
| Neto gotovina | avgust 2026. | **48.585.308,30 RSD** |

Potvrđeni poređenjem sa izvornim računskim delom procedure `52nt`.

> **[P]** Posle korekcije IF/ON od 18.09.2026. skup testova `finansije core naplata`
> prolazi sa **138 testova**.

---

### 6.1.18. Šta Finansije ne rade

| Ne radi | Objašnjenje |
|---|---|
| Ne pokreće poslovne procedure | Otvaranje ekrana **ne izvršava** `SPFINizv52/53/55` ni `SPLdKnjizenje` |
| Ne menja poslovne podatke | Koriste se **samo `SELECT` upiti** nad izvorom |
| Ne preračunava devizne iznose | `deviza` se čuva, ali se **ne preračunava po kursu** |
| Ne koristi polje `placeno` | Preuzima se, ali **ne ulazi** u obračun naplaćenog ni priliva |
| Ne povezuje fakturu sa uplatom | Tok gotovine je obračun po pravilima, ne evidencija naplate |
| Ne daje ukupan trošak zarada centra | Čeka potvrdu izvora i pravila raspodele |
| Ne vodi istoriju pripadnosti posla centru | Vidi **P-44** |

**Poslovne stavke koje su jasno odvojene i nisu nadomeštene nulama ni pretpostavljenim
formulama [P]:**

1. Istorijski kadrovski spisak centra.
2. Potvrđen ukupan trošak zarada centra.
3. Istorijski mesečni presek Potraživanja.
4. Povezivanje pojedinačnih faktura sa konkretnim uplatama/isplatama.

---

### 6.1.19. Problemi iz ovog poglavlja

Nalazi koje postojeća metodologija **nije navodila kao probleme**. Pun opis, posledice i
predlog rešenja su u [registru problema](#10-poznati-problemi-i-ograničenja).

| # | Opis | Ozbiljnost |
|---|---|---|
| [**P-42**](#p-42--konta-i-pravila-toka-gotovine-upisani-su-u-kod) | Preko 40 broja konta i pravila toka gotovine **upisani su u kod**. Izmena kontnog plana traži novu verziju aplikacije, a isto pravilo postoji i u procedurama `SPFINizv52/52nt` — promena na jednom mestu ne odražava se na drugo. | Srednja |
| [**P-43**](#p-43--mogući-dvostruki-obuhvat-zajedničkih-troškova) | Ako se raspodela zajedničkih troškova počne knjižiti na poslove, ista stavka ulazi **i u `R` i u `ZT`**, pa je rezultat `P − R − ZT` dvostruko umanjen. Metodologija je to sama navodila kao stvar koju treba pratiti. | Srednja |
| [**P-44**](#p-44--promena-centra-pregrupiše-celu-istoriju-finansija) | Centar posla se uzima iz **aktuelnog** šifarnika `posao.blok`, bez istorije. Promena centra pregrupiše sva ranija knjiženja pri sledećoj sinhronizaciji. Isti obrazac kao [P-05](#p-05--centar-se-uzima-iz-poslednje-dodele-a-ne-istorijske) u Floti, gde istorijska dodela **postoji**. | Srednja |

---

### 6.1.20. Otvorena pitanja

| # | Pitanje | Izvor |
|---|---|---|
| **Q41** | Da li se raspodela zajedničkih troškova **knjiži** u izvoru na klasu 5? Ako se to uvede, nastao bi dvostruki obuhvat (**P-43**). | Ovaj pregled |
| **Q42** | Da li je potrebna **istorija pripadnosti posla centru**, da izveštaji za prošle periode ostanu nepromenjeni (**P-44**)? | Ovaj pregled |
| **Q43** | Ako se promeni kontni plan ili pravila procedure `52nt`, ko obaveštava da treba izmeniti i kod (**P-42**)? | Ovaj pregled |
| Q3 | Kako se rezultati Finansija koriste u knjiženju i ko ih preuzima? | Opšte |

---

### Mapa izvornog koda

| Oblast | Izvor implementacije |
|---|---|
| Formule P/R, grupisanja, isključenja | [`finansije/services/reports.py`](../finansije/services/reports.py) |
| Grafikoni, procenti, rang-liste | [`finansije/services/charts.py`](../finansije/services/charts.py) |
| Raspodela ZT | [`finansije/services/shared_costs.py`](../finansije/services/shared_costs.py) |
| Tokovi 52nt | [`finansije/services/cash_flow.py`](../finansije/services/cash_flow.py) |
| Osam kolona i sabiranje godina | [`finansije/services/job_overview.py`](../finansije/services/job_overview.py) |
| IF, `knt3`, dodele i zaduženja | [`finansije/services/job_card.py`](../finansije/services/job_card.py) |
| Zaposleni iz obračuna | [`finansije/services/job_people.py`](../finansije/services/job_people.py) |
| Kolone detalja, znaci, podnožja, upozorenja | [`finansije/services/job_tables.py`](../finansije/services/job_tables.py) |
| Potraživanja po šifri | [`potrazivanja/services/reports.py`](../potrazivanja/services/reports.py) |
| Pristup, periodi i rute | [`finansije/access.py`](../finansije/access.py), [`forms.py`](../finansije/forms.py), [`views.py`](../finansije/views.py) |
| Preuzimanje i kontrole izvora | [`finansije/services/source.py`](../finansije/services/source.py), [`sync.py`](../finansije/services/sync.py) |
| Modeli i identitet stavke | [`finansije/models.py`](../finansije/models.py) |
| Celery ulazne tačke i raspored | [`finansije/tasks.py`](../finansije/tasks.py), [`sync_celery_periodic_tasks.py`](../core/management/commands/sync_celery_periodic_tasks.py) |
| Serversko sortiranje knjiženja/istorije | [`finansije/services/datatables.py`](../finansije/services/datatables.py) |
| Numeričko sortiranje, AJAX i tabovi | [`finansije/static/finansije/tables.js`](../finansije/static/finansije/tables.js) |
| Brojevi, boje, dugmad, aktivan meni | [`finansije/templatetags/finance.py`](../finansije/templatetags/finance.py) |

> **Pri promeni formule, izvora, datuma filtriranja, pravila dostupnosti ili znaka prikaza
> potrebno je ažurirati odgovarajući odeljak ovog poglavlja i odgovarajuće testove.**

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [3.3. Finansije](#33-finansijska-analitika) | Modul iz ugla korisnika — ekrani i uloge |
| [`finansije/README.md`](../finansije/README.md) | Tehničko uputstvo i istorija faza |
| [6.8. Potraživanja](#68-potraživanja--obračuni) | Tab „Potraživanja“ na detalju posla |
| [4. Baza podataka](#46-finansijska-analitika--finansije) | `LedgerEntry` i prateće tabele |
| [Prilog B — DDL nasleđenih pogleda](#prilog-b--ddl-nasleđenih-sql-pogleda) | Definicije pogleda Naplate iz baze |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema |


### Dodatne analize po šifri posla — dopuna 21.09.2026.

Nova kartica **Dodatne analize** na postojećem izveštaju `group=job` prikazuje
24 kolone: šifru, naziv, centar, postojećih osam finansijskih iznosa, četiri
relativna pokazatelja, prosečan broj ljudi i osam iznosa po čoveku. Period,
centar i dostupne šifre isti su kao na kartici **Finansijski rezultati**.
Osnovni obračuni prihoda, rashoda, ZT i tokova gotovine nisu promenjeni.

| Pokazatelj | Formula |
|---|---|
| Rezultat bez ZT / prihodi % | (P − R) / P × 100 |
| Rezultat posle ZT / prihodi % | (P − R − ZT) / P × 100 |
| Rashodi / prihodi % | R / P × 100 |
| ZT / prihodi % | ZT / P × 100 |
| Prosečan broj ljudi | Zbir mesečnih brojeva ljudi na šifri / broj dostupnih zaključenih meseci |
| Svaki iznos / čoveku | Postojeći iznos za ceo izabrani period / prosečan broj ljudi |

Broj ljudi čita se zbirno iz `PUTGEO-SERVER.bazaldims.dbo.Zarada`, za firmu,
godinu, mesece i samo korisniku dostupne šifre. Uslovi su isti kao za
postojeći spisak zaposlenih na šifri: iznos ili količina različiti od nule
plus odgovarajući `PomLD.status_obr='Z'`. Broji se `COUNT(DISTINCT rasif)` po
šifri i mesecu, tako da više elemenata ili zaključenih obračuna ne duplira
čoveka. Imena, pojedinačne zarade i radni sati se ne preuzimaju.

Zaključen mesec bez stavki za šifru ulazi kao nula. Mesec bez zaključenog
obračuna ne pretpostavlja se kao nula: prosek koristi dostupne mesece, ali
broj ljudi i izvedeni iznosi nose oznaku nepotpunosti `*` i broj pokrivenih
meseci. Otvoreni obračuni, nedostupan izvor i delimično izabrani meseci
isto označavaju nepotpunost. Kod delimičnog meseca ljudi se odnose na ceo
mesec, a finansijski iznosi na izabrane dane. Više godina obrađuje se
odvojeno, pa se mesečni brojevi združuju pre računanja proseka.

Isti čovek može biti evidentiran na više šifara; ovo nije FTE niti raspodela
prema radnim satima i brojevi se ne sabiraju kao ukupan broj zaposlenih IMS.
Za nulte ili negativne prihode nema procenta. Bez pozitivnog broja ljudi
nema iznosa po čoveku. Nedostajući izvorni iznos daje crtu samo u zavisnim
pokazateljima; ne menja se u nulu. Znak rashoda, ZT i odliva po čoveku ostaje
minus kao u osnovnoj tabeli; procenti rashoda i ZT prikazuju opterećenje sa
pozitivnim znakom (storno zadržava suprotan znak).

**Kontrolni primer:** P=100, R=40, ZT=10; broj ljudi januar=2, februar=4.
Prosek je 3; rezultat pre ZT 60%, posle ZT 50%; rashodi 40%, ZT 10%.
ZT po čoveku prikazuje −10/3 = **−3,33 RSD**. Dva meseca po 2 čoveka daju
prosek 2, a ne zbir 4. Ako je januar 4, a februar zaključen bez zaposlenih,
prosek je 2; ako februar nije zaključen, prosek je 4 uz oznaku nepotpunosti.

Implementacija: `services/job_additional.py`, `services/job_people.py`.
Koriste se postojeće rute `jobs_data` i `export`, sa `analysis=additional`.
Zadržane su dozvole finansija i provera dostupnih šifara, a broj ljudi i
pokazatelji po čoveku zahtevaju postojeću dozvolu `employee_list`. Bez nje
ostaju dostupni finansijski iznosi i relativni pokazatelji. Ne uvodi se nova
ruta, migracija ili poslovna SQL procedura. Upiti su isključivo SELECT.

Kartice se učitavaju na zahtev pri otvaranju, sortiraju po sirovim brojevima
i imaju horizontalni skrol. Promena filtera zadržava izabranu karticu;
Excel prati aktivnu karticu, sa istim numeričkim vrednostima i napomenama
o nepotpunosti. Testovi: `test_job_additional.py`, `test_job_people.py`,
uz regresije postojećeg `test_job_overview.py`.

### 6.1.21. Banke po računima

Implementacija: `finansije/services/banks.py`, testovi: `finansije/test_banks.py`.
Ovo je zaseban pregled konta 23/24. Ne menja obračun 52nt, ZT, zarade ni knjiženja.

**Obuhvat:** podešena firma, aktivni lokalni redovi iz finansijske sinhronizacije,
jedna knjigovodstvena godina i datum knjiženja `booking_date`. Vrsta `ZAT` se
isključuje. Svaki red ide tačno jednom u banku, nepovezane stavke ili kontrolu
blagajni/prelaznih računa. Izvorna veza `(firma, grupa=11, šifra partnera)` ima
prednost; pravilo konta primenjuje se samo kada nema izvornog partnera.

Za izabrani period `[od, do]`:

- Stanje pre perioda = `Σ(D−C)` za POC i redove od 1. januara pre datuma `od`.
- Povećanje/prilivi u periodu = `ΣD`, smanjenje/odlivi = `ΣC`, bez POC.
- Ukupan promet = `ΣD + ΣC`, sa izvornim znacima storna, bez POC i ZAT.
- Saldo na kraju = `Σ(D−C)` od 1. januara zaključno sa `do`, sa POC.
- Kontrola: `stanje pre perioda + prilivi − odlivi = saldo na kraju`.
- Posebne godišnje kolone povećanja/smanjenja čitaju 1. januar do danas za tekuću
  godinu, a celu godinu za ranije godine. Izbor užeg perioda ih ne skraćuje.

Na kontima tekućih/deviznih računa duguje označava knjiženi priliv, potražuje odliv.
Na depozitima su to povećanje/smanjenje plasmana. Uključeni su interni prenosi i
knjigovodstvene korekcije, pa zbir svih konta nije konsolidovani eksterni tok gotovine.
Nedostatak potvrđenog uvoza godine označava se i glavni finansijski iznosi su crtica.

**Valute:** `DIN` se prikazuje kao `RSD`. Duguje/potražuje su knjigovodstveni RSD;
`foreign_amount` se raspoređuje po oznaci `d_p` u zasebne kolone izvorne valute.
Negativno RSD storno sa pozitivnom devizom koriguje i devizni znak. Nedostajući iznos
ili nepoznat smer označava devizni zbir kao nepotpun; različite valute se ne sabiraju.

**Kontrolni primer:** POC duguje 100; priliv 50 i odliv 20 daju početno 100,
promet 70 i saldo 130. POC se ne računa kao priliv. Za EUR, priliv 100, odliv 20
i storno priliva 10 daju devizno stanje 70 EUR, nezavisno od USD računa.

**Ograničenje:** saldo depozita za garanciju nije iznos garancije. Vanbilansna
konta 88610/89610 i dugoročni depoziti 03/04 ostaju izvan traženog obuhvata 23/24.
Broj ugovora, nominalni iznos, kamata i rok oročenja ne izmišljaju se iz knjiženja.

---

## 6.2. Flota — obračuni goriva

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
>
> Zajednička implementacija svih obračuna u ovom poglavlju:
> [`fleet/support/fuel.py`](../fleet/support/fuel.py).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [V-03](#v-03--neto-iznos-goriva-iz-bruto-iznosa) | Neto iznos goriva iz bruto iznosa | — |
| [V-04](#v-04--iznosi-omv-transakcije) | Iznosi OMV transakcije | — |
| [V-05](#v-05--iznosi-nis-transakcije) | Iznosi NIS transakcije | — |
| [V-06](#v-06--prečišćavanje-omv-transakcija) | Prečišćavanje OMV transakcija (duplikati i odjeci računa) | — |
| [V-01](#v-01--prosečna-potrošnja-goriva-poslednjih-10-točenja) | Prosečna potrošnja goriva (poslednjih 10 točenja) | ~~P-02~~ |
| [V-02](#v-02--prosečna-potrošnja-goriva-za-ceo-vek-vozila) | Prosečna potrošnja goriva za ceo vek vozila | — |
| [V-21](#v-21--gorivo-po-šifri-posla) | Gorivo po šifri posla | — |
| [V-23](#v-23--obračun-goriva-na-putnom-nalogu-vozila) | Obračun goriva na putnom nalogu vozila | — |
| [V-24](#v-24--potrošnja-goriva-u-detalju-vozila) | Potrošnja goriva u detalju vozila | Procena prema točenjima |

Registar problema: [10. Poznati problemi](#10-poznati-problemi-i-ograničenja).

---

### Zajednička osnova: šta se uopšte smatra gorivom

Pre svakog obračuna sistem odbacuje stavke koje nisu gorivo. Prepoznavanje ide
**po nazivu proizvoda**, ne po šifri. [P]

Ključne reči (`FUEL_PRODUCT_KEYWORDS`), traže se **bilo gde u nazivu, bez obzira na velika
i mala slova** [P]:

```
dizel, diesel, benzin, petrol, maxxmotion, maxxm, bmb,
lpg, autogas, cng, tng, ngv, adblue, ad blue
```

| Polje koje se proverava | Izvor |
|---|---|
| `product_inv` | OMV (`fleet_transactionomv`) |
| `naziv_proizvoda` | NIS (`fleet_transactionnis`) |

**AdBlue je poseban slučaj [P]:** računa se kao „proizvod goriva“ u opštim pregledima,
ali se **izuzima** iz obračuna na putnom nalogu vozila (V-23) i nove kartice potrošnje (V-24), jer nije gorivo koje
učestvuje u potrošnji po 100 km.

| Funkcija | Uključuje AdBlue |
|---|---|
| `filter_omv_fuel_queryset` / `filter_nis_fuel_queryset` | Da |
| `filter_omv_travel_order_fuel_queryset` / `filter_nis_travel_order_fuel_queryset` | **Ne** |

> **Rizik [Z]:** proizvod čiji naziv ne sadrži nijednu ključnu reč **neće biti prepoznat
> kao gorivo** i tiho će ispasti iz svih obračuna. Novi naziv proizvoda kod dobavljača
> zahteva dopunu liste u kodu.

---

### V-03 — Neto iznos goriva iz bruto iznosa

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Iznos neto“ / „Neto“ |
| Tehnički naziv | `net_amount_from_gross_and_vat()` |
| Putanja | [`fleet/support/fuel.py:65`](../fleet/support/fuel.py#L65) |

#### 2. Poslovna svrha

Fakture dobavljača goriva iskazuju **bruto** iznos (sa PDV-om). Za poređenje troškova
među vozilima, centrima i šiframa posla potreban je **neto** iznos, jer je PDV za
Institut odbitna stavka i ne predstavlja stvarni trošak.

#### 3. Korisnici rezultata

Služba voznog parka (izveštaji o gorivu), rukovodioci centara, uprava.
Neto iznos ulazi u obračun **troška po kilometru** (V-07) i u **izveštaj goriva po
šifri posla** (V-21).

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | JM | Obavezno | Ko unosi | Izvor |
|---|---|---|---|---|---|---|---|
| Bruto iznos (OMV) | Bruto | `fleet_transactionomv.gross_cc` | `decimal(10,2)` | RSD | Ne | Niko — automatski | OMV portal |
| PDV (OMV) | PDV | `fleet_transactionomv.vat` | `decimal(10,2)` | RSD | Ne | Niko — automatski | OMV portal |
| Bruto iznos (NIS) | Bruto | `fleet_transactionnis.total` | `decimal(12,2)` | RSD | Da | Niko — automatski | NIS portal |

#### 5. Poreklo podataka

```
OMV portal (fleet.omv.com)  ──Selenium──► CSV ──► fleet_transactionomv.gross_cc, .vat
NIS portal (cards.nis.rs)   ──Selenium──► CSV ──► fleet_transactionnis.total
                                                          │
                                                          ▼
                                          net_amount_from_gross_and_vat()
                                                          │
                                                          ▼
                             ekran „Fakture goriva“, izveštaji, trošak po km
```

#### 6. Tačan postupak obračuna

Postoje **dva puta**, u zavisnosti od toga da li je PDV poznat. [P]

**Slučaj A — PDV je poznat (nije NULL):**

> neto = bruto − PDV

**Slučaj B — PDV nije poznat (NULL):**

> neto = bruto × 5 / 6

Konstante u kodu: `VAT_NET_NUMERATOR = 5`, `VAT_NET_DENOMINATOR = 6`. [P]

**Zašto 5/6 [Z]:** pri stopi PDV-a od 20%, bruto = neto × 1,20, pa je
neto = bruto / 1,20 = bruto × 5/6 ≈ bruto × 0,8333.

> **Ograničenje [Z]:** koeficijent 5/6 je **tvrdo upisan u kod**. Stavka sa drugom
> poreskom stopom (npr. 10%) bila bi pogrešno preračunata. Promena opšte stope PDV-a
> zahteva izmenu koda.

**Zaokruživanje [P]:** rezultat se kvantizuje na **2 decimale, `ROUND_HALF_UP`**
(pola naviše). Isto važi i za bruto iznos.

**NULL i nedostajuće vrednosti [P]:**

| Situacija | Rezultat |
|---|---|
| Bruto je NULL | **`None`** — ne 0 |
| Bruto je `NaN` | **`None`** |
| Bruto nije pretvoriv u broj | **`None`** |
| PDV je NULL | Primenjuje se slučaj B (× 5/6) |

Razlika između „nema podatka“ (`None`) i „iznos je nula“ je namerno očuvana. [P]

**U SQL upitima** se ista logika izražava kroz `Case`/`When`
(`_amount_minus_vat_or_without_vat_expression`), gde se NULL prvo zamenjuje nulom
(`Coalesce`) — pa se u agregacijama ponaša kao 0. [P]

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/fuel.py` |
| Funkcije | `net_amount_from_gross_and_vat()`, `_amount_for_decimal()`, `_quantize_money()` |
| SQL varijanta | `_amount_minus_expression()`, `_amount_without_vat_expression()`, `_amount_minus_vat_or_without_vat_expression()` |
| Tip rezultata | `DecimalField(max_digits=14, decimal_places=2)` |
| Ekrani | `/fuel-transactions/`, `/izvestaji/gorivo-sifra-posla/*`, detalj vozila |

#### 8. Primer obračuna

> Ilustrativni primer sa zaokruženim brojevima.

**Slučaj A — PDV poznat (OMV):**

| Korak | Vrednost |
|---|---|
| Bruto (`gross_cc`) | 12.000,00 RSD |
| PDV (`vat`) | 2.000,00 RSD |
| Neto = 12.000,00 − 2.000,00 | **10.000,00 RSD** |

**Slučaj B — PDV nepoznat (NIS):**

| Korak | Vrednost |
|---|---|
| Bruto (`total`) | 12.000,00 RSD |
| PDV | nije u izvoru |
| Neto = 12.000,00 × 5 / 6 = 10.000,000000 | **10.000,00 RSD** |

**Slučaj B sa zaokruživanjem:**

| Korak | Vrednost |
|---|---|
| Bruto | 7.499,99 RSD |
| 7.499,99 × 5 / 6 = 6.249,991666… | |
| `ROUND_HALF_UP` na 2 decimale | **6.249,99 RSD** |

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Iznos bez PDV-a za jednu transakciju goriva |
| Format | Decimalan broj, 2 decimale, RSD |
| Gde se čuva | **Nigde** — računa se u trenutku prikaza |
| Kada se ponovo računa | Pri svakom otvaranju ekrana ili izveštaja |
| Može li korisnik da ga izmeni | Ne |
| Istorija promene | Ne postoji — menja se samo ako se promeni izvorni iznos |

> **Napomena [P]:** postoji i tabela `fleet_fuelconsumption` sa kolonama `cost_bruto`
> i `cost_neto` koje **jesu** sačuvane. Njih puni sinhronizacija, a **trošak po kilometru
> (V-07) koristi `cost_bruto` iz te tabele**, ne ovaj izračunati neto iznos.
> Vidi upozorenje u V-07.

#### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Ekran „Fakture goriva“ | Kolona „Neto“, zbir po računu |
| Izveštaj gorivo po šifri posla (V-21) | Kolona „neto“, zbir po šifri i polumesecu |
| Detalj vozila | Lista transakcija |
| Excel izvoz | Ista vrednost |

> **[N] Q3:** nije potvrđeno da li računovodstvo preuzima ovaj iznos i za koji dokument.
> Sistem ga ne knjiži i ne prenosi automatski.

#### 11. Kontrola i ručna provera

**Kontrolna formula:**

- Kada je PDV poznat: `neto + PDV = bruto` — mora važiti tačno.
- Kada PDV nije poznat: `neto × 1,2 = bruto` sa odstupanjem do 0,01 RSD zbog zaokruživanja.

**Dozvoljeno odstupanje:** ±0,01 RSD po stavci (zaokruživanje).
Pri zbiru od N stavki odstupanje može narasti do ±0,01 × N.

**Tipični uzroci razlike:**

| Uzrok | Kako se prepoznaje |
|---|---|
| Stavka sa stopom PDV-a različitom od 20% | `neto × 1,2 ≠ bruto` za pojedinačnu stavku |
| Prazan bruto iznos | Neto je prazan, ne nula |
| Zbir uključuje stavke koje nisu gorivo | Uporediti sa filterom naziva proizvoda |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje sistema |
|---|---|
| Bruto je NULL | Vraća `None`; u agregacijama se ponaša kao 0 |
| Bruto je `NaN` | Vraća `None` |
| PDV veći od bruto iznosa | **Daje negativan neto** — sistem to ne sprečava |
| Stopa PDV-a nije 20% | **Pogrešan rezultat** u slučaju B |
| Bruto je 0 | Neto je 0,00 (nije `None`) |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Neto = bruto − PDV kada je PDV poznat | Potvrđeno | `fuel.py:65-72` | — |
| Neto = bruto × 5/6 kada PDV nije poznat | Potvrđeno | `fuel.py:72` | — |
| Zaokruživanje `ROUND_HALF_UP` na 2 decimale | Potvrđeno | `fuel.py:59-62` | — |
| Koeficijent 5/6 odgovara stopi PDV-a od 20% | **Zaključeno** | Matematika, nije komentarisano u kodu | Potvrditi da su sve stavke goriva po stopi 20% |
| Rezultat se nigde ne čuva | Potvrđeno | Nema upisa u modele | — |
| Računovodstvo preuzima ovaj iznos | **Nepotvrđeno** | — | **Q3** |

---

### V-04 — Iznosi OMV transakcije

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Bruto“ i „Neto“ u listama OMV transakcija |
| Tehnički naziv | `omv_charged_gross_net_amounts()` |
| Putanja | [`fleet/support/fuel.py:75`](../fleet/support/fuel.py#L75) |

#### 2. Poslovna svrha

Vraća par (bruto, neto) za jednu OMV transakciju, iz onoga što je OMV stvarno naplatio.

#### 3. Korisnici rezultata

Isti kao V-03.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | JM |
|---|---|---|
| Naplaćeni bruto iznos | `fleet_transactionomv.gross_cc` | RSD |
| PDV | `fleet_transactionomv.vat` | RSD |

> **[P] Važno:** koristi se `gross_cc` („Gross CC“ iz izvora), **ne** kolona `amount`.
> Tabela sadrži i `amount`, `discount`, `surcharge`, `cost_1`, `cost_2`, `amount_other` —
> nijedna od njih **ne ulazi** u ovaj obračun.

#### 5. Poreklo podataka

OMV Fleet portal → Selenium preuzimanje → CSV → `fleet_transactionomv`.
Dnevno u 05:10 (putnička) i 06:10 (teretna vozila). [P]

#### 6. Tačan postupak obračuna

1. Ako je `gross_cc` prazan ili nije broj → vraća `(None, None)`.
2. Bruto = `gross_cc`, zaokruženo na 2 decimale `ROUND_HALF_UP`.
3. Neto = rezultat obračuna **V-03** nad `gross_cc` i `vat`.

#### 7. Tehnička implementacija

`fleet/support/fuel.py: omv_charged_gross_net_amounts()`.
Poziva se iz `get_fuel_invoice_lines()`, `get_vehicle_fuel_transaction_rows()`,
`_detail_from_omv()` i detalja putnog naloga vozila. [P]

#### 8. Primer obračuna

| Korak | Vrednost |
|---|---|
| `gross_cc` | 9.600,00 RSD |
| `vat` | 1.600,00 RSD |
| Bruto | **9.600,00 RSD** |
| Neto = 9.600,00 − 1.600,00 | **8.000,00 RSD** |

#### 9–13.

Isto kao V-03. Dodatna razlika:

| Slučaj | Ponašanje |
|---|---|
| `gross_cc` prazan, ali `amount` popunjen | Vraća `(None, None)` — **`amount` se ne koristi kao zamena** u ovom obračunu |

> **[P] Izuzetak:** u detalju **putnog naloga vozila** (V-23) koristi se drugačije
> pravilo — tamo je iznos `gross_cc or amount`. To je jedina tačka u sistemu gde
> `amount` služi kao rezerva.

---

### V-05 — Iznosi NIS transakcije

#### 1. Naziv

| | |
|---|---|
| Tehnički naziv | `nis_charged_gross_net_amounts()` |
| Putanja | [`fleet/support/fuel.py:82`](../fleet/support/fuel.py#L82) |

#### 2–5.

Isto kao V-04, ali za NIS. Izvor: NIS portal `cards.nis.rs`, dnevno u 04:20. [P]

| Poslovni naziv | Tabela i kolona |
|---|---|
| Ukupan iznos | `fleet_transactionnis.total` |

> **[P]** NIS izvor **nema kolonu PDV**. Tabela ima `total` i `total_sa_kase`;
> koristi se **`total`**.

#### 6. Tačan postupak obračuna

1. Ako je `total` prazan ili nije broj → `(None, None)`.
2. Bruto = `total`, zaokruženo na 2 decimale.
3. Neto = **uvek** po slučaju B: `total × 5 / 6`, jer PDV nije dostupan.

#### 8. Primer obračuna

| Korak | Vrednost |
|---|---|
| `total` | 6.000,00 RSD |
| Bruto | **6.000,00 RSD** |
| Neto = 6.000,00 × 5 / 6 | **5.000,00 RSD** |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| NIS stavka po stopi različitoj od 20% | **Pogrešan neto** — nema načina da se prepozna |
| Razlika `total` i `total_sa_kase` | Zanemaruje se; koristi se `total` |
| Popust (`popust`) | Nije posebno obrađen — pretpostavka je da je već u `total` [Z] |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Pitanje |
|---|---|---|
| NIS neto se uvek računa kao × 5/6 | Potvrđeno | — |
| Koristi se `total`, ne `total_sa_kase` | Potvrđeno | — |
| Popust je već sadržan u `total` | **Zaključeno** | Potvrditi sa NIS-om ili poređenjem sa fakturom |

---

### V-06 — Prečišćavanje OMV transakcija

> **Ovo je najvažniji obračun u poglavlju.** Bez njega su svi zbirovi goriva pogrešni.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Nema — radi nevidljivo, u pozadini svih OMV pregleda |
| Tehnički naziv | `filter_omv_fuel_queryset()` |
| Putanja | [`fleet/support/fuel.py:239`](../fleet/support/fuel.py#L239) |

#### 2. Poslovna svrha

OMV izvor **sadrži istu transakciju više puta**, u različitim stanjima obrade
(pre i posle fakturisanja, sa ispravljenim datumom fakture). Sirovo sabiranje daje
**dvostruko ili višestruko uvećan trošak goriva**.

Ovaj korak bira **tačno jedan merodavan red** po stvarnom točenju.

#### 3. Korisnici rezultata

Svi korisnici izveštaja o gorivu. Greška ovde direktno kvari trošak po kilometru,
izveštaje za upravu i obračun na putnom nalogu.

#### 4. Ulazni podaci

Ceo skup `fleet_transactionomv`, filtriran na proizvode goriva.

| Kolona | Uloga u prečišćavanju |
|---|---|
| `license_plate_no`, `transaction_date`, `product_inv`, `voucher`, `quantity` | **Identitet točenja** |
| `invoice_date`, `transaction_date` | Provera ispravnosti datuma fakture |
| `invoiced` | Da li je red fakturisan |
| `invoice_no` | Broj fakture |
| `gross_cc`, `amount`, `mileage` | Poređenje identičnosti kod „odjeka“ |

#### 5. Poreklo podataka

OMV Fleet portal → Selenium → CSV → `fleet_transactionomv`.
Jedinstveni ključ u bazi je
`(license_plate_no, transaction_date, product_inv, voucher, quantity)` — ali izvor
i dalje isporučuje **više redova sa različitim stanjem fakturisanja**, koji se razlikuju
po ostalim kolonama, pa ključ ne sprečava višestruke zapise istog točenja. [Z]

#### 6. Tačan postupak obračuna

Tri koraka, tim redom [P]:

```
  svi OMV redovi sa proizvodom goriva
              │
              ▼
  KORAK 1  Izbaci redove sa neispravnim datumom fakture
              │      (invoice_date < datum transakcije)
              ▼
  KORAK 2  Za svako točenje zadrži samo JEDAN red
              │      (najbolji po prioritetu)
              ▼
  KORAK 3  Izbaci „odjeke“ računa
              │      (nefakturisani blizanci fakturisanog reda)
              ▼
      merodavan skup za sve obračune
```

##### Korak 1 — neispravan datum fakture

Izbacuje se svaki red gde je **datum fakture pre datuma transakcije**:

> `invoice_date < DATE(transaction_date)` → red se odbacuje

Funkcija: `_exclude_omv_stale_invoice_dates()` / `is_omv_invoice_date_stale()`. [P]

**Obrazloženje [Z]:** faktura ne može biti izdata pre nego što je gorivo natočeno;
takav red je zaostatak ranije obrade.

##### Korak 2 — jedan red po točenju

Redovi se grupišu po identitetu točenja:

> `(license_plate_no, transaction_date, product_inv, voucher, quantity)`

**Prazna polja se izjednačavaju** [P]: `product_inv` i `voucher` bez vrednosti računaju se
kao prazan tekst, a `quantity` bez vrednosti kao dogovorena zamena. Bez toga poređenje
`NULL = NULL` u SQL-u nije tačno, pa red bez vaučera ne bi našao ni samog sebe i **tiho bi
ispao iz svih pregleda goriva**.

> **Ispravljeno 18.09.2026.** — pre toga je svaka OMV transakcija bez vaučera ili bez
> količine nestajala sa svih ekrana goriva, bez ikakvog upozorenja. Zbog ispravke
> **iznosi goriva mogu biti veći nego ranije**; koliko — zavisi od toga koliko takvih
> zapisa ima u bazi. Videti [P-46](#10-poznati-problemi-i-ograničenja).

Unutar grupe bira se **prvi** red po redosledu [P]:

| Prioritet | Kriterijum | Smisao |
|---|---|---|
| 1 | `invoiced` opadajuće | Fakturisan red ima prednost nad nefakturisanim |
| 2 | `invoice_date` opadajuće | Novija faktura ima prednost |
| 3 | `id` opadajuće | Poslednji upisan red |

Funkcija: `_dedupe_omv_transaction_lines()`. [P]

> **[P] Bitno:** i ovaj izbor se pravi **nad skupom već očišćenim u koraku 1** —
> red sa neispravnim datumom fakture ne može biti izabran kao merodavan.

> **[P] Šta ključ NE obuhvata:** **iznos** (`gross_cc`, `amount`) ni **valutu**
> (`supplier_currency`). Dva reda koja se razlikuju **samo** po iznosu smatraju se istim
> točenjem, a koji preživljava odlučuje stanje fakturisanja — nikad iznos. Nije potvrđeno
> da takvi parovi postoje u stvarnim podacima; videti
> [P-47](#10-poznati-problemi-i-ograničenja), koji traži proveru nad bazom.

##### Korak 3 — „odjeci“ računa

Izbacuje se red koji ispunjava **sva tri** uslova [P]:

1. Postoji **drugi** red sa istim vrednostima
   `license_plate_no`, `product_inv`, `voucher`, `quantity`, `gross_cc`, `amount`,
   `mileage`, `invoice_date`, koji je `invoiced = True`, ima popunjen `invoice_no`
   različit od `voucher`, i nije isti red.
2. Posmatrani red **nije fakturisan** (`invoiced = False` ili NULL).
3. Kod posmatranog reda je **`invoice_no` jednak `voucher`**.

Funkcija: `_exclude_omv_receipt_echoes()`. [P]

**Poslovno objašnjenje [Z]:** dok račun nije fakturisan, OMV kao „broj fakture“ prikazuje
broj bona (`voucher`). Kada stigne prava faktura, pojavi se novi red sa stvarnim brojem
fakture. Stari red ostaje u izvoru kao **odjek** i mora se izbaciti.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/fuel.py` |
| Ulazna tačka | `filter_omv_fuel_queryset()` — filter goriva **+** tri koraka čišćenja |
| Samo čišćenje, bez filtera goriva | `deduplicate_omv_transactions()` — koristi ga izveštaj za upravu, koji sam razvrstava proizvode |
| Koraci | `_exclude_omv_stale_invoice_dates()`, `_dedupe_omv_transaction_lines()`, `_exclude_omv_receipt_echoes()` |
| Varijanta za putni nalog | `filter_omv_travel_order_fuel_queryset()` — dodatno izbacuje AdBlue |
| Srodno čišćenje u bazi | [`fleet/support/fuel_cleanup.py: cleanup_omv_fuel_data()`](../fleet/support/fuel_cleanup.py) |

> **[P] Dva različita mehanizma:** `filter_omv_fuel_queryset()` samo **filtrira pri
> čitanju** (ne menja podatke). `cleanup_omv_fuel_data()` je zasebna komanda koja
> **stvarno briše** duplikate iz baze i pokreće se ručno
> (`manage.py cleanup_omv_fuel_duplicates`).

**NIS nema ovaj problem [P]:** `filter_nis_fuel_queryset()` radi samo filter naziva proizvoda.

#### 8. Primer obračuna

> Ilustrativni primer.

Izvor sadrži četiri reda za isto točenje (tablica `BG123-AA`, 40 l dizela, 12.000 RSD):

| # | `transaction_date` | `voucher` | `invoice_no` | `invoiced` | `invoice_date` | Ishod |
|---|---|---|---|---|---|---|
| 1 | 05.03.2026. | `V-777` | `V-777` | Ne | 01.03.2026. | **Izbačen u koraku 1** — faktura pre transakcije |
| 2 | 05.03.2026. | `V-777` | `V-777` | Ne | 31.03.2026. | Izbačen u koraku 3 — odjek reda 3 |
| 3 | 05.03.2026. | `V-777` | `F-12345` | Da | 31.03.2026. | **Zadržan** |
| 4 | 05.03.2026. | `V-777` | `F-12345` | Da | 20.03.2026. | Izbačen u koraku 2 — stariji `invoice_date` |

**Rezultat:** jedan red, 12.000 RSD bruto.
**Bez prečišćavanja:** 4 × 12.000 = 48.000 RSD — **četvorostruko uvećan trošak**.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Skup merodavnih OMV transakcija |
| Gde se čuva | Nigde — filter se primenjuje pri svakom čitanju |
| Kada se ponovo računa | Pri svakom otvaranju ekrana ili izveštaja |
| Može li korisnik da ga izmeni | Ne |

#### 10. Upotreba rezultata

**Svaki** OMV obračun u sistemu polazi od ovog filtera: V-01, V-02, V-07, V-21, V-23,
izveštaji za upravu, detalj vozila, ekran „Fakture goriva“. [P]

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Broj redova pre i posle filtera | Uporediti `TransactionOMV.objects.count()` sa brojem posle `filter_omv_fuel_queryset()` |
| Sumnja na duplikat | Na ekranu „Fakture goriva“ proveriti da li se isti bon (`voucher`) pojavljuje dvaput |
| Poređenje sa fakturom dobavljača | Zbir bruto iznosa po broju fakture mora odgovarati iznosu na papirnoj fakturi OMV-a |

**Najpouzdanija kontrola [Z]:** zbir po broju fakture (`invoice_no`) uporediti sa
stvarnom fakturom OMV-a za taj mesec.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Rizik |
|---|---|---|
| Isto točenje sa **različitom količinom** u dva reda | Tretiraju se kao **dva različita točenja** | **Dupliranje ostaje** |
| Isto točenje sa različitim `voucher` | Tretiraju se kao dva točenja | Dupliranje ostaje |
| Nefakturisan red bez fakturisanog parnjaka | Zadržava se | Ispravno |
| Fakturisan red kod koga je `invoice_no = voucher` | **Ne** izbacuje se (uslov 3 koraka 3 traži nefakturisan red) | Ispravno |
| Svi redovi imaju neispravan datum fakture | **Točenje potpuno nestaje** iz obračuna | **Tiho gubljenje podatka** |
| Proizvod nije prepoznat kao gorivo | Ne ulazi ni u jedan obračun | Tiho gubljenje podatka |

> **Najveći rizik [Z]:** ako izvor promeni količinu ili broj bona između dva preuzimanja,
> mehanizam **neće** prepoznati duplikat. Zato postoji i zasebna komanda za čišćenje baze.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Tri koraka i njihov redosled | Potvrđeno | `fuel.py:226-240` | — |
| Identitet točenja je petorka kolona | Potvrđeno | `fuel.py:164-175` | — |
| Prioritet izbora: `invoiced`, `invoice_date`, `id` | Potvrđeno | `fuel.py:190` | — |
| Uslovi za „odjek“ računa | Potvrđeno | `fuel.py:194-219` | — |
| Prazna polja se izjednačavaju pri poređenju | Potvrđeno | `fuel.py:159-175` | Rešeno, **P-46** |
| **Iznos i valuta nisu deo ključa** | **Potvrđeno** | `fuel.py:164-175` | **P-47** |
| `voucher` je broj bona pre fakturisanja | **Zaključeno** | Iz logike filtera, nije dokumentovano | Potvrditi sa OMV-om |
| Filter ne menja podatke u bazi | Potvrđeno | Samo `filter`/`exclude` | — |

---

### V-01 — Prosečna potrošnja goriva (poslednjih 10 točenja)

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Prosečna potrošnja“ (l/100 km) |
| Tehnički naziv | `calculate_average_fuel_consumption()` |
| Putanja | [`fleet/support/fuel.py:320`](../fleet/support/fuel.py#L320) |

#### 2. Poslovna svrha

Pokazuje **skorašnju** potrošnju vozila, radi uočavanja kvara, nepravilne vožnje ili
nepravilnog evidentiranja goriva.

#### 3. Korisnici rezultata

Služba voznog parka, garaža, rukovodioci centara.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | JM | Obavezno |
|---|---|---|---|
| Datum točenja | `fleet_fuelconsumption.date` | — | Da |
| Količina | `fleet_fuelconsumption.amount` | litar | Da |
| Kilometraža | `fleet_fuelconsumption.mileage` | km | Da (ali može biti 0) |

> **[P]** Obračun čita **`fleet_fuelconsumption`**, a ne sirove OMV/NIS tabele.

#### 5. Poreklo podataka

```
OMV / NIS portal ──► fleet_transactionomv / fleet_transactionnis
                              │  (sinhronizacija)
                              ▼
                     fleet_fuelconsumption  (date, amount, mileage)
                              │
                              ▼
                  calculate_average_fuel_consumption()
```

#### 6. Tačan postupak obračuna

1. Uzmi **poslednjih 10 točenja** vozila, sortirano po datumu **opadajuće**
   (indeks 0 = najnovije, indeks 9 = najstarije).
2. **Ako ih ima manje od 10 → rezultat je `None`** (ne prikazuje se ništa). [P]
3. Pronađi **`k`** — najmanji indeks od 0 do 8 na kome je `mileage > 0`,
   tj. **najnovije točenje sa unetom kilometražom**. [P]
4. Ako `k` nije pronađen ili je **`k > 4`** → rezultat je `None`. [P]
5. Inače se posmatra **simetričan prozor `[k, 9−k]`**:
   - ukupna količina = zbir `amount` za točenja sa indeksima od `k` do `9−k` (uključivo);
   - pređeni put = `mileage[k] − mileage[9−k]`;
   - ako je pređeni put > 0:

> **potrošnja (l/100 km) = ukupna količina / pređeni put × 100**

6. Inače → `None`.

**Kako nastaje uslov `k > 4` [P]:** kod traži `k` dvaput istom petljom, jednom
dodeljujući granicu `[9−k]`, drugi put `[k]`, pa proverava `9−k ≥ k`. To je ispunjeno
samo za `k ≤ 4`.

**Praktično značenje [Z]:** ako **pet ili više najnovijih** točenja nema unetu
kilometražu, prosečna potrošnja se **uopšte ne prikazuje**.

**Zaokruživanje [P]:** funkcija **ne zaokružuje** — vraća pun rezultat deljenja.
Zaokruživanje radi šablon pri prikazu.

**NULL i nula [P]:** točenja sa `mileage = 0` se ne mogu koristiti kao **novija**
granica, ali njihova količina **ulazi u zbir** ako se nalaze u prozoru.

> **Ispravljeno 19.09.2026..** Opis niže odnosi se na **ranije** stanje; sada se obe granice
> traže među točenjima sa `mileage > 0`, uz dva dodatna uslova: novija granica mora biti
> stvarno novija, a njena kilometraža veća od starije. Kad to nije ispunjeno, na ekranu
> **nema broja** umesto izmišljenog.
>
> **[P] Raniji nedostatak — starija granica se nije proveravala.**
> Kod proverava `mileage > 0` samo pri traženju **novije** granice (indeks `k`).
> **Starija granica `[9−k]` se uzima bez ikakve provere.** Ako to točenje ima
> kilometražu 0, pređeni put postaje `mileage[k] − 0`, tj. **cela kilometraža vozila**,
> pa je izračunata potrošnja **drastično premala**, bez ijednog upozorenja.
>
> Primer: `k = 2`, `mileage[2] = 128.000`, `mileage[7] = 0` → pređeni put = 128.000 km
> umesto stvarnih ~1.500 km. Umesto ~6 l/100 km dobija se ~0,07 l/100 km.
>
> Vodilo se kao problem **[P-02](#p-02--prosečna-potrošnja-ne-proverava-stariju-granicu)**.
> **Rešeno 19.09.2026.**, uz testove u `fleet/test_cost_fixes.py`.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl i funkcija | `fleet/support/fuel.py: calculate_average_fuel_consumption()` |
| Ulazni podatak | `vehicle.fuel_consumptions` (povratna veza ka `FuelConsumption`) |
| Ekran | Detalj vozila |
| Testovi | `fleet/tests.py` |

#### 8. Primer obračuna

> Ilustrativni primer, svih 10 točenja ima ispravnu kilometražu.

| Točenje (od najnovijeg) | Datum | Količina (l) | Kilometraža |
|---|---|---|---|
| 1 | 20.03. | 45 | 128.000 |
| 2–9 | … | ukupno 360 | … |
| 10 | 05.01. | 40 | 118.000 |

| Korak | Vrednost |
|---|---|
| Ukupna količina (10 točenja) | 445 l |
| Pređeni put = 128.000 − 118.000 | 10.000 km |
| Potrošnja = 445 / 10.000 × 100 | **4,45 l/100 km** |

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Prosečna potrošnja u litrima na 100 km, za period poslednjih 10 točenja |
| Format | Decimalan broj, l/100 km |
| Gde se čuva | Nigde — računa se pri prikazu |
| Može li korisnik da ga izmeni | Ne |
| Istorija | Ne postoji |

#### 10. Upotreba rezultata

Prikaz na detalju vozila. **Ne ulazi** ni u jedan drugi obračun i **ne prenosi se**
u druge module. [P]

#### 11. Kontrola i ručna provera

**Kontrolna formula:** zbir litara između dva očitavanja podeljen sa razlikom
kilometraže, puta 100.

| Provera | Kako |
|---|---|
| Vrednost izgleda previsoka | Proveriti da li je neko točenje pogrešno pripisano vozilu |
| Vrednost izgleda preniska | Proveriti da li nedostaju točenja u periodu |
| Nema vrednosti | Vozilo ima manje od 10 evidentiranih točenja |

**Dozvoljeno odstupanje [Z]:** rezultat je procena — očitavanja kilometraže na pumpi
unosi vozač i podložna su grešci. Odstupanje od deklarisane potrošnje do 20% nije
samo po sebi znak greške.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Manje od 10 točenja | `None` — ništa se ne prikazuje |
| Sva točenja sa `mileage = 0` | `None` |
| Pet ili više najnovijih točenja bez kilometraže (`k > 4`) | `None` |
| **Starije granično točenje ima `mileage = 0`** | **Potrošnja drastično premala, bez upozorenja** |
| Kilometraža opada (zamena brojača) | Pređeni put ≤ 0 → `None` |
| Točenje pripisano pogrešnom vozilu | **Pogrešan rezultat, bez upozorenja** |
| AdBlue među točenjima | **Ulazi u količinu** — uvećava potrošnju |

> **Rizik [Z]:** `fleet_fuelconsumption` **ne razdvaja AdBlue od goriva**. Za vozila
> koja koriste AdBlue prosečna potrošnja je zato precenjena.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Koristi tačno poslednjih 10 točenja | Potvrđeno | `fuel.py:321` | — |
| Manje od 10 točenja → nema rezultata | Potvrđeno | `fuel.py:323-324` | — |
| Formula količina / put × 100 | Potvrđeno | `fuel.py:346` | — |
| Prozor je simetričan `[k, 9−k]`, uslov `k ≤ 4` | Potvrđeno | `fuel.py:326-342` | — |
| Obe granice se traže među točenjima sa `mileage > 0` | Potvrđeno | `fuel.py` — `newest_index` / `oldest_index` | Rešeno, **P-02** |
| Novija granica mora imati **veću** kilometražu | Potvrđeno | `fuel.py` — `total_mileage > 0` | Rešeno, **P-02** |
| Kad uslovi nisu ispunjeni, vraća se `None` | Potvrđeno | `fleet/test_cost_fixes.py` | Rešeno, **P-02** |
| Da li je pogrešan rezultat ikada viđen u radu | **Nepotvrđeno** | — | **Q13** |
| AdBlue ulazi u količinu | **Zaključeno** | `FuelConsumption` nema vrstu proizvoda | Potvrditi da li je to željeno |

---

### V-02 — Prosečna potrošnja goriva za ceo vek vozila

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Prosečna potrošnja (ukupno)“ |
| Tehnički naziv | `calculate_average_fuel_consumption_ever()` |
| Putanja | [`fleet/support/fuel.py:350`](../fleet/support/fuel.py#L350) |

#### 2. Poslovna svrha

Dugoročni prosek potrošnje vozila, za poređenje vozila istog tipa i za procenu
isplativosti zadržavanja vozila u floti.

#### 3–5.

Isti izvori i korisnici kao V-01.

#### 6. Tačan postupak obračuna

1. Prebroj sva točenja vozila. **Ako ih je manje od 2 → `None`.** [P]
2. Uzmi sva točenja sortirana po datumu **opadajuće**.
3. `first_entry` = **prvo** točenje (od najnovijeg) sa `mileage > 0`.
4. `last_entry` = **poslednje** točenje (od najstarijeg) sa `mileage > 0`.
5. Ako su obe pronađene i međusobno različite:
   - ukupna količina = zbir `amount` svih točenja u rasponu datuma
     `last_entry.date ≤ date ≤ first_entry.date`;
   - pređeni put = `first_entry.mileage − last_entry.mileage`;
   - ako je pređeni put > 0:

> **potrošnja (l/100 km) = ukupna količina / pređeni put × 100**

6. Inače → `None`.

**Razlike u odnosu na V-01 [P]:**

| | V-01 (poslednjih 10) | V-02 (ceo vek) |
|---|---|---|
| Obuhvat | Poslednjih 10 točenja | Sva točenja |
| Najmanji broj točenja | 10 | 2 |
| **Provera `mileage > 0` na novijoj granici** | Da | Da |
| **Provera `mileage > 0` na starijoj granici** | **Ne — nedostatak** | **Da — ispravno** |

> **[P]** V-02 je u ovom pogledu **ispravno** izveden: obe granice se biraju samo među
> točenjima sa kilometražom većom od nule. Nedostatak opisan u V-01 ovde **ne postoji**.

#### 8. Primer obračuna

| Korak | Vrednost |
|---|---|
| Najnovije točenje sa kilometražom > 0 | 20.03.2026., 128.000 km |
| Najstarije točenje sa kilometražom > 0 | 10.02.2023., 18.000 km |
| Zbir količine u tom rasponu | 7.150 l |
| Pređeni put = 128.000 − 18.000 | 110.000 km |
| Potrošnja = 7.150 / 110.000 × 100 | **6,50 l/100 km** |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Manje od 2 točenja | `None` |
| Zamena brojača tokom veka vozila | **Pređeni put je pogrešan** — rezultat je besmislen |
| Vozilo preuzeto od drugog vlasnika | Početna kilometraža nije 0 — to je uzeto u obzir, koristi se razlika |
| AdBlue | Ulazi u količinu (isto kao V-01) |

> **Najveći rizik [Z]:** zamena brojača kilometraže. V-02 ne proverava da li kilometraža
> monotono raste, za razliku od obračuna kilometraže (V-13) koji to **proverava i
> prijavljuje**.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Najmanje 2 točenja | Potvrđeno | `fuel.py:353-354` |
| Granice su najnovije i najstarije točenje sa kilometražom > 0 | Potvrđeno | `fuel.py:360-368` |
| Zbir količine se ograničava rasponom datuma granica | Potvrđeno | `fuel.py:371` |
| Ne proverava se pad kilometraže | Potvrđeno | Nema takve provere |

---

### V-21 — Gorivo po šifri posla

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Gorivo po šifri posla“ — četiri ekrana: OMV/NIS × putnička/teretna |
| Tehnički naziv | `fuel_job_code_report()` |
| Putanja | [`fleet/support/fuel_reports.py:202`](../fleet/support/fuel_reports.py#L202) |
| Adrese | `/izvestaji/gorivo-sifra-posla/omv-putnicka/`, `…/omv-teretna/`, `…/nis-putnicka/`, `…/nis-teretna/` |

#### 2. Poslovna svrha

Raspoređuje trošak goriva na **šifru posla koja je vozilu bila dodeljena na dan točenja**,
radi kontrole i prenosa troška na nosioce posla.

#### 3. Korisnici rezultata

Služba voznog parka, računovodstvo, rukovodioci centara.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona |
|---|---|---|
| Godina | Godina | filter (`godina`) |
| Mesec | Mesec | filter (`mesec`) |
| Polovina meseca | Polovina | filter (`polovina`: 1 ili 2) |
| Transakcije OMV | — | `fleet_transactionomv` |
| Transakcije NIS | — | `fleet_transactionnis` |
| Istorijska dodela | — | `fleet_jobcode.assigned_date`, `organizational_unit` |
| Kategorija vozila | — | `fleet_vehicle.category` |

#### 5. Poreklo podataka

```
 OMV/NIS transakcija  ──► prečišćavanje (V-06)  ──► samo vozila sa vezom
                                                          │
       fleet_jobcode (dodela ≤ datum transakcije)  ────────┤
                                                          ▼
                              grupisanje: šifra × godina × mesec × polovina
                                                          │
                                                          ▼
                                       zbirni pregled + detalj po šifri
```

#### 6. Tačan postupak obračuna

1. **Izbor izvora:** OMV ili NIS, prema pozvanoj adresi.
2. **Filter goriva:** `filter_omv_fuel_queryset()` (uključuje prečišćavanje V-06) ili
   `filter_nis_fuel_queryset()`. [P]
3. **Samo povezana vozila:** `vehicle__isnull=False` — transakcije bez prepoznatog
   vozila **ispadaju iz izveštaja**. [P]
4. **Filter kategorije vozila:**
   - „putnička“ → `category = putnicko`;
   - „teretna“ → `category = teretno`.
   **Priključna vozila nikada nisu obuhvaćena.** [P]
5. **Filter perioda** (svi su opcioni):
   - godina → `godina(datum) = godina`;
   - mesec → `mesec(datum) = mesec`;
   - polovina `1` → dan ≤ 15; polovina `2` → dan > 15.
6. **Istorijska šifra posla** — za svaku transakciju se traži poslednja dodela
   sa `assigned_date <= datum transakcije`, sortirano `-assigned_date, -id`. [P]
   Uzimaju se šifra, naziv i **datum dodele**.
7. **Iznosi po stavci:** bruto i neto po V-04 (OMV) odnosno V-05 (NIS).
8. **Grupisanje** po petorki: `(šifra posla, naziv šifre, godina, mesec, polovina)`.
   Za svaku grupu: broj transakcija, zbir količine, zbir bruto, zbir neto.
9. **Prazna šifra** se prikazuje kao **`"Bez sifre"`**. [P]
10. **Sortiranje:** godina, mesec, polovina, šifra posla — sve rastuće. [P]

**Zaokruživanje [P]:** zbirovi se sabiraju iz već zaokruženih iznosa po stavci
(2 decimale), pa dodatnog zaokruživanja nema.

**NULL vrednosti [P]:** prazna količina, bruto ili neto se u zbiru računaju kao `0,00`.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/fuel_reports.py` |
| Ulazna tačka | `fuel_job_code_report(form, supplier, vehicle_type, sifpos)` |
| Istorijska šifra | `_historical_job_code_subqueries()` |
| Polumesec | `_half_month_case()` |
| Detalj | `_detail_from_omv()`, `_detail_from_nis()` |
| View-ovi | `fleet/views/reports.py: fuel_job_code_*_view` |

> **[Z] Napomena o izvedbi:** `fuel_job_code_report()` uvek prvo napravi **pun detaljni
> spisak** svih transakcija, pa tek onda grupiše i filtrira po šifri. Za velike periode
> to znači učitavanje celog skupa u memoriju.

#### 8. Primer obračuna

> Ilustrativni primer, OMV, putnička vozila, mart 2026.

Tri transakcije istog vozila:

| Datum | Šifra posla vozila na taj dan | Količina | Bruto | Neto |
|---|---|---|---|---|
| 05.03.2026. | 413111 | 40 l | 9.600,00 | 8.000,00 |
| 12.03.2026. | 413111 | 38 l | 9.120,00 | 7.600,00 |
| 22.03.2026. | 413222 *(dodela od 15.03.)* | 42 l | 10.080,00 | 8.400,00 |

**Rezultat — tri grupe:**

| Šifra | Godina | Mesec | Polovina | Broj | Količina | Bruto | Neto |
|---|---|---|---|---|---|---|---|
| 413111 | 2026 | 3 | 1 | 2 | 78 l | 18.720,00 | 15.600,00 |
| 413222 | 2026 | 3 | 2 | 1 | 42 l | 10.080,00 | 8.400,00 |

> Ključno: treće točenje ide na **novu** šifru, jer je dodela promenjena 15.03.,
> a ne na trenutnu šifru vozila.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Trošak i količina goriva po šifri posla i polumesecu |
| Format | Tabela; količina u litrima, iznosi u RSD |
| Gde se čuva | Nigde — računa se pri otvaranju |
| Kada se ponovo računa | Pri svakom otvaranju, sa tekućim stanjem transakcija |
| Može li korisnik da ga izmeni | Ne — ali može promeniti dodelu šifre posla, što menja rezultat |
| Istorija | Ne postoji |

#### 10. Upotreba rezultata

| Korisnik | Šta preuzima | Sa kog ekrana | Za šta |
|---|---|---|---|
| Služba voznog parka | Zbir po šifri | `/izvestaji/gorivo-sifra-posla/*` | Kontrola raspodele |
| Računovodstvo | **[N]** | **[N]** | **[N] Q3** |

> **[N] Q3:** nije potvrđeno da li se ovaj izveštaj koristi kao osnov za knjiženje
> raspodele goriva po nosiocima. Konta nisu navedena jer nisu u kodu.

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Ukupan zbir | Zbir svih šifara = zbir bruto iznosa svih OMV/NIS transakcija u periodu za tu kategoriju vozila |
| Pojedinačna šifra | Otvoriti detalj šifre — spisak pojedinačnih transakcija mora se sabrati u zbirni red |
| „Bez sifre“ | Označava vozila bez ijedne dodele pre datuma točenja — proveriti u `/sifre-poslova/` |
| Neslaganje sa fakturom dobavljača | Izveštaj obuhvata samo **povezana** vozila i **jednu** kategoriju — zbir je uvek ≤ faktura |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Posledica |
|---|---|---|
| Transakcija bez prepoznatog vozila | **Ispada iz izveštaja** | Trošak nedostaje, bez upozorenja |
| Priključno vozilo | Nikad nije u izveštaju | Namerno |
| Vozilo bez ijedne dodele pre datuma | Grupa „Bez sifre“ | Vidljivo |
| Dodela unesena naknadno, sa ranijim datumom | **Menja ranije izveštaje** | Izveštaj nije zamrznut |
| Vozilo promenilo šifru usred meseca | Trošak se deli na dve šifre po datumu | Namerno i ispravno |
| AdBlue | **Ulazi** u izveštaj | Uvećava količinu i iznos |

> **Najveći rizik [Z]:** izveštaj se **uvek računa iz tekućeg stanja**. Naknadna izmena
> dodele šifre posla menja i već odštampane izveštaje za prošle mesece.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Koristi se istorijska dodela na datum točenja | Potvrđeno | `fuel_reports.py:55-64` | — |
| Priključna vozila su isključena | Potvrđeno | `fuel_reports.py:29-32` | — |
| Transakcije bez vozila ispadaju | Potvrđeno | `fuel_reports.py:101, 108` | — |
| Polovina meseca je granica 15. dana | Potvrđeno | `fuel_reports.py:48-50, 75-80` | — |
| OMV prolazi kroz prečišćavanje V-06 | Potvrđeno | `fuel_reports.py:100` | — |
| Izveštaj se koristi za knjiženje | **Nepotvrđeno** | — | **Q3** |
| Da li AdBlue treba da bude u izveštaju | **Nepotvrđeno** | — | **Q14** |

---

### V-23 — Obračun goriva na putnom nalogu vozila

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Obračun“ na putnom nalogu vozila |
| Tehnički naziv | `VehicleTravelOrderDetailView.get_context_data()` |
| Putanja | [`fleet/views/vehicle_travel_orders.py:289`](../fleet/views/vehicle_travel_orders.py#L289) |
| Adresa | `/garaza/putni-nalozi-vozila/<pk>/obracun/` |

#### 2. Poslovna svrha

Za jedno zaduženje vozila prikazuje **koliko je goriva natočeno, koliko je pređeno
kilometara i kolika je potrošnja** — osnov za pravdanje zaduženja i za kontrolu vozača.

#### 3. Korisnici rezultata

Garaža, služba voznog parka, sam zaposleni koji je zadužio vozilo.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Ko unosi |
|---|---|---|---|
| Datum otvaranja | Datum otvaranja naloga | `fleet_vehicletravelorder.created_at` | Zaposleni / garaža |
| Datum zatvaranja | Datum zatvaranja naloga | `fleet_vehicletravelorder.closed_at` | Garaža |
| Početna kilometraža | Početna kilometraža | `fleet_vehicletravelorder.start_mileage` | Zaposleni |
| Krajnja kilometraža | Krajnja kilometraža | `fleet_vehicletravelorder.end_mileage` | Zaposleni / garaža |
| Transakcije goriva | — | `fleet_transactionomv`, `fleet_transactionnis` | Automatski |

#### 5. Poreklo podataka

```
 Zaduženje vozila (period: created_at → closed_at ili danas)
            │
            ├─► OMV transakcije u periodu  (bez AdBlue, prečišćene V-06)
            └─► NIS transakcije u periodu  (bez AdBlue)
                          │
                          ▼
              ukupno litara, ukupan iznos
                          │
         start_mileage, end_mileage ──► pređeni put
                          │
                          ▼
                   potrošnja l/100 km
```

#### 6. Tačan postupak obračuna

**Korak 1 — period:**

> od = `created_at` (00:00:00) · do = `closed_at` ili **današnji dan** (23:59:59.999999)

Otvoren nalog se obračunava **do danas**. [P]

**Korak 2 — pronalaženje transakcija.** Vozilo se traži na **dva načina istovremeno** [P]:

> `vehicle = vozilo naloga` **ILI** `registarska oznaka = poslednja tablica vozila`

Poslednja tablica je iz `traffic_cards` sortirano `-issue_date, -id`. [P]

> **[P] Važno:** ovo je **jedini** obračun u sistemu koji hvata i transakcije koje
> **nisu povezane sa vozilom**, preko registarske oznake. Razlog je što nalog mora
> obuhvatiti i tek preuzete transakcije koje sinhronizacija još nije povezala. [Z]

**Korak 3 — filter goriva bez AdBlue:**
`filter_omv_travel_order_fuel_queryset()` i `filter_nis_travel_order_fuel_queryset()`. [P]

**Korak 4 — iznos po stavci** (razlikuje se od V-04!) [P]:

| Izvor | Količina | Iznos | Jedinična cena |
|---|---|---|---|
| OMV | `quantity` | **`gross_cc` ili, ako je prazan, `amount`** | `unit_price`, ili iznos / količina |
| NIS | `kolicina` | `total` | `cena`, ili iznos / količina |

> **[P] Odstupanje:** ovde se koristi **bruto** iznos, **bez** preračuna u neto,
> i `amount` služi kao rezerva za `gross_cc`. To je jedino mesto u sistemu sa tim pravilom.

**Korak 5 — zbirovi:**

> ukupno litara = Σ količina · ukupan iznos = Σ iznos

**Korak 6 — pređeni put:** samo ako su **obe** kilometraže unete:

> pređeni put = krajnja kilometraža − početna kilometraža

**Korak 7 — potrošnja:** samo ako je pređeni put > 0:

> **potrošnja (l/100 km) = ukupno litara / pređeni put × 100**

**NULL vrednosti [P]:**

| Situacija | Rezultat |
|---|---|
| Nedostaje početna ili krajnja kilometraža | Pređeni put i potrošnja su **prazni** |
| Pređeni put ≤ 0 | Potrošnja je **prazna** |
| Nema transakcija u periodu | Ukupno litara = 0, iznos = 0, potrošnja = 0 (ako je put > 0) |

**Zaokruživanje [P]:** funkcija **ne zaokružuje**; prikaz zaokružuje šablon.

**Priprema za štampu [P]:** redovi se dele na stranice od po 30; prva stranica se
dopunjava praznim redovima do 30, druga obuhvata redove 31–60.
**Transakcije preko 60 se ne štampaju.**

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/views/vehicle_travel_orders.py` |
| Klasa | `VehicleTravelOrderDetailView` (obračun), `VehicleTravelOrderFuelReportView` (štampa) |
| Redovi | `_row_from_omv()`, `_row_from_nis()` |
| Šablon | `fleet/vehicle_travel_order_fuel_report.html` |
| Dozvole | `vehicle_travel_order_detail`, `vehicle_travel_order_fuel_report` |

**Zatvaranje prethodnog naloga [P]:** pri otvaranju novog naloga za isto vozilo,
svi raniji otvoreni nalozi se **automatski zatvaraju** na datum novog naloga, a njihova
krajnja kilometraža se postavlja na **početnu kilometražu novog naloga**
(`VehicleTravelOrderCreateView.form_valid`).

#### 8. Primer obračuna

> Ilustrativni primer.

| Podatak | Vrednost |
|---|---|
| Nalog otvoren | 01.03.2026. |
| Nalog zatvoren | 31.03.2026. |
| Početna kilometraža | 120.000 km |
| Krajnja kilometraža | 122.500 km |

Transakcije u periodu (bez AdBlue):

| Datum | Izvor | Količina | Iznos (bruto) |
|---|---|---|---|
| 05.03. | OMV | 40 l | 9.600,00 |
| 18.03. | NIS | 45 l | 10.800,00 |
| 27.03. | OMV | 38 l | 9.120,00 |

| Korak | Vrednost |
|---|---|
| Ukupno litara | 40 + 45 + 38 = **123 l** |
| Ukupan iznos | 9.600 + 10.800 + 9.120 = **29.520,00 RSD** |
| Pređeni put = 122.500 − 120.000 | **2.500 km** |
| Potrošnja = 123 / 2.500 × 100 | **4,92 l/100 km** |

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Gorivo, put i potrošnja za jedno zaduženje vozila |
| Format | Ekran i obrazac za štampu |
| Gde se čuva | **Nigde** — samo `start_mileage` i `end_mileage` su sačuvani |
| Kada se ponovo računa | Pri svakom otvaranju |
| Može li korisnik da ga izmeni | Posredno — izmenom kilometraže na nalogu |
| Ko može da potvrdi | Garaža, zatvaranjem naloga |
| Istorija | Ne postoji; izmena zatvorenog naloga dozvoljena je **samo superuseru** [P] |

#### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Štampani obračun uz putni nalog | Prilog za pravdanje zaduženja |
| Kontrola vozača | Poređenje sa očekivanom potrošnjom vozila (V-01) |

> **[N] Q3:** nije potvrđeno da li se ovaj obračun prilaže uz neki knjigovodstveni dokument.

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Broj transakcija | Uporediti sa spiskom na ekranu „Fakture goriva“ za isto vozilo i period |
| Pređeni put | Uporediti sa očitanjima na ekranu kilometraže vozila (V-13) |
| Potrošnja | Uporediti sa V-01 za isto vozilo; velika razlika ukazuje na grešku unosa |
| Nedostaju transakcije | Proveriti da li je vozilu promenjena registarska oznaka u periodu |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Posledica |
|---|---|---|
| Nalog nije zatvoren | Period ide **do danas** | Rezultat se menja svakog dana |
| Vozilo je promenilo tablice u periodu | Hvata se **samo poslednja** tablica | **Transakcije sa stare tablice mogu nedostajati** |
| Ista tablica kod drugog vozila u istoriji | Moguće **preuzimanje tuđih transakcija** | Rizik |
| Više od 60 transakcija | Štampa se **samo prvih 60** | Tihi gubitak na papiru |
| AdBlue | Izuzet | Namerno |
| `gross_cc` prazan, `amount` popunjen | Koristi se `amount` | Odstupanje od V-04 |
| Preklapajuća zaduženja istog vozila | Ista transakcija ulazi u **oba** naloga | Dvostruko računanje |

> **Najveći rizik [Z]:** hvatanje po registarskoj oznaci. Ako je tablica nekada pripadala
> drugom vozilu, mogu se povući tuđe transakcije. Kontrolna tabla flote zato ima
> upozorenje „Više istovremenih zaduženja“.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Period je `created_at` → `closed_at` ili danas | Potvrđeno | `vehicle_travel_orders.py:293-294` | — |
| Transakcije se hvataju i po vozilu i po tablici | Potvrđeno | `…:311-316` | — |
| AdBlue je izuzet | Potvrđeno | `…:318-323`, `fuel.py:247-252` | — |
| Iznos je bruto, sa `amount` kao rezervom | Potvrđeno | `…:261` | — |
| Potrošnja = litri / put × 100 | Potvrđeno | `…:336` | — |
| Štampa najviše 60 transakcija | Potvrđeno | `…:341-348` | — |
| Zašto se hvata i po tablici | **Zaključeno** | Nije komentarisano | Potvrditi namenu |
| Da li je dvostruko računanje kod preklapanja prihvatljivo | **Nepotvrđeno** | — | **Q15** |

---

### Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q13** | Obračun V-01 je ispravljen 19.09.2026.. Ostaje pitanje **koliko je vozila ranije prikazivalo besmisleno nisku potrošnju** — to pokazuje da li se problem javljao u radu. Uz to: da li zbir goriva treba da uključi i najstarije točenje prozora, ili tek ona posle njega? Sada uključuje, kao i ranije i kao `calculate_average_fuel_consumption_ever()`. |
| **Q14** | Da li AdBlue treba da ulazi u izveštaj „Gorivo po šifri posla“ (V-21) i u prosečnu potrošnju (V-01, V-02)? Trenutno ulazi u sve osim u obračun putnog naloga. |
| **Q15** | Kod preklapajućih zaduženja istog vozila ista transakcija goriva ulazi u obračun oba naloga. Da li je to prihvatljivo? |
| **Q16** | Da li su sve stavke goriva po stopi PDV-a od 20%? Preračun neto iznosa iz bruto (kada PDV nije poznat) pretpostavlja upravo tu stopu. |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.3. Flota — troškovi](#63-flota--troškovi-vozila) | Trošak po kilometru, pragovi, crvena zona |
| [6.5. Flota — izveštaji](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji) | Kilometraža, održavanje, presek flote |
| [4. Baza podataka](#444-gorivo) | Tabele goriva |
| [7. Integracije](#7-integracije) | Kako se preuzimaju NIS i OMV podaci |


### V-24 — Potrošnja goriva u detalju vozila

Dodato 21.09.2026. po zahtevu korisnika. Kartica **Potrošnja goriva** zamenjuje
karticu Kilometraža. Implementacija: `fleet/support/vehicle_consumption.py`,
`fleet/support/vehicle_mileage.py`, šablon `_vehicle_consumption.html`.

Filter bira period; podrazumevani period je isti kao početni period troškova
(poslednjih 12 kalendarskih meseci do danas). Korisnik može posebno promeniti
period potrošnje. Neispravan filter prikazuje grešku i nema obračuna.

Za granice se usvajaju najbliži stvarni datumi točenja ili zaduženja, prema
E-01.6. Prikazuju se usvojeni datumi, stanja i odstupanja. Očitavanja mogu
biti izvan traženog perioda, pa se i gorivo uzima iz tog usvojenog raspona.

**Procenjena potrošnja = litri posle početnog datuma do krajnjeg datuma
uključivo / razlika kilometara × 100.** Sva točenja na početni dan isključena
su iz količine. Periodi od približno 30 dana dele zajedničko granično očitanje,
a točenje na toj granici ulazi samo u prethodni period. Ukupan prosek je
zbir litara / ukupan put × 100, a ne prosek pojedinačnih stopa.

NIS/OMV se prečišćavaju postojećim servisom, uključujući uklanjanje OMV
ponavljanja i odjeka. Izvor se bira po profilu koji važi na datum točenja;
bez profila koristi se NIS/OMV. Ranija evidencija ne sabira se sa direktnim
izvorom. AdBlue se prikazuje odvojeno i ne ulazi u l/100 km. Neprepoznati
proizvodi i CNG/NGV izostavljaju se iz litarskog obračuna. Količine CNG/NGV
ne preračunavaju se proizvoljno iz mase u zapreminu.

Prazna evidencija nije nulta potrošnja. Bez pozitivne razlike km, uz pad
brojača, nedostajuću ili negativnu količinu goriva, stopa se ne računa i
prikazuje se razlog. Zbir poznatih količina ostaje vidljiv kao nepotpun kada
nedostaje količina. OMV korigovano stanje koristi se kada je pozitivno.

**Kontrolni primer:** 01.01: 1.000 km i 60 l; 15.01: 1.500 km i 30 l;
31.01: 2.000 km i 40 l, uz dodatnih 10 l AdBlue. Obračun je
(30 + 40) / (2.000 − 1.000) × 100 = **7,00 l/100 km**. Prvih 60 l se ne
sabira; AdBlue je zasebnih 10 l. Duplikat poslednjeg OMV reda ne menja zbir.

**Ograničenje:** nivo rezervoara na granicama nije evidentiran, tako da je
rezultat procena iz točenja, a ne merenje stvarno sagorelog goriva. Delimična
točenja naročito utiču na kratke periode. Postojeći obračuni V-01/V-02/V-23
nisu promenjeni. Regresije: `fleet/test_vehicle_consumption.py`.

---

## 6.3. Flota — troškovi vozila

> **Promena 19.09.2026:** nova `/analitika/` i analitika na detalju vozila koriste
> [metodologiju IMS-FLOTA-2.0](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa). Opisi V-07–V-12 u ovom
> poglavlju dokumentuju nasleđene funkcije; pragovi po masi više nisu kriterijum
> nove analitike. Detalj vozila zadržava pregled evidentiranih stavki, uz zajednički
> prošireni obračun, profile i sačuvane procene opisane u novom poglavlju.

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
>
> Uočeni problemi u ovom poglavlju vode se u
> [Registru problema za rešavanje](#10-poznati-problemi-i-ograničenja).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [V-08](#v-08--procena-pređene-kilometraže-u-periodu) | Procena pređene kilometraže u periodu | **P-03**, ~~P-04~~ |
| [V-07](#v-07--trošak-po-kilometru-po-vozilu) | Trošak po kilometru po vozilu | ~~P-05~~ ~~P-06~~ ~~P-07~~ **P-08** ~~P-09~~ ~~P-10~~ |
| [V-11](#v-11--pragovi-fiksnog-troška-po-kilometru) | Pragovi fiksnog troška po kilometru | P-11 |
| [V-12](#v-12--status-vozila-prema-trošku-po-kilometru) | Status vozila prema trošku po kilometru | — |
| [V-09](#v-09--analiza-troška-po-km-kroz-više-perioda) | Analiza troška po km kroz više perioda | P-12 |
| [V-10](#v-10--neto-trošak-održavanja) | Neto trošak održavanja | — |
| [V-15](#v-15--analitika-evidentiranih-troškova-na-detalju-vozila) | Analitika evidentiranih troškova na detalju vozila | — |
| [V-24](#v-24--statistika-po-centrima) | Statistika po centrima | P-13, P-14 |

---

### V-08 — Procena pređene kilometraže u periodu

> Ovaj obračun je **imenilac** troška po kilometru. Ako je on pogrešan, pogrešan je
> i ceo trošak po km. Zato se dokumentuje prvi.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kilometraža“ uz oznaku izvora, npr. „Točenja (okvirno)“ |
| Tehnički naziv | `_estimate_period_mileage()` |
| Putanja | [`fleet/support/dashboard.py:68`](../fleet/support/dashboard.py#L68) |

#### 2. Poslovna svrha

Sistem **nema pouzdan podatak o pređenoj kilometraži po periodu** — brojač se očitava
samo prilikom točenja goriva i pri otvaranju/zatvaranju zaduženja vozila. Ovaj obračun
iz tih raštrkanih očitavanja pravi **procenu** kilometraže za traženi period.

#### 3. Korisnici rezultata

Služba voznog parka, rukovodioci centara, uprava — posredno, kroz trošak po kilometru.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | JM | Obavezno | Ko unosi |
|---|---|---|---|---|---|---|
| Datum točenja | — | `fleet_fuelconsumption.date` | datum i vreme | — | Da | Automatski |
| Kilometraža na točenju | Kilometraža | `fleet_fuelconsumption.mileage` | ceo broj | km | Ne | Vozač na pumpi |
| Datum otvaranja zaduženja | Datum otvaranja naloga | `fleet_vehicletravelorder.created_at` | datum | — | Da | Zaposleni |
| Datum zatvaranja zaduženja | Datum zatvaranja naloga | `fleet_vehicletravelorder.closed_at` | datum | — | Ne | Garaža |
| Početna kilometraža | Početna kilometraža | `fleet_vehicletravelorder.start_mileage` | ceo broj | km | Ne | Zaposleni |
| Krajnja kilometraža | Krajnja kilometraža | `fleet_vehicletravelorder.end_mileage` | ceo broj | km | Ne | Zaposleni / garaža |
| Početak perioda | Od | parametar ekrana | datum | — | Da | Korisnik |
| Kraj perioda | Do | parametar ekrana | datum | — | Ne (podrazumevano danas) | Korisnik |

#### 5. Poreklo podataka

```
 OMV/NIS portal ──► fleet_fuelconsumption (date, mileage)   ─┐
                                                             │
 Zaposleni ──► fleet_vehicletravelorder                       ├─► spisak očitavanja
              (created_at + start_mileage)                    │
              (closed_at  + end_mileage)                     ─┘
                                                             │
                                              izbor najboljeg para očitavanja
                                                             │
                                                             ▼
                                              procena kilometraže za period
```

#### 6. Tačan postupak obračuna

**Korak 1 — prikupljanje očitavanja** (`_mileage_readings`) [P]:

| Izvor | Datum | Vrednost | Uslov |
|---|---|---|---|
| Točenje goriva | `date` | `mileage` | `mileage > 0` |
| Zaduženje — početak | `created_at` | `start_mileage` | `start_mileage > 0` |
| Zaduženje — kraj | `closed_at` | `end_mileage` | `end_mileage > 0` |

Očitavanja sa vrednošću **0 ili manjom se odbacuju** i broje kao neispravna. [P]
Spisak se sortira po datumu, pa po kilometraži, rastuće. [P]

**Korak 2 — provera dovoljnosti:**
Ako ima **manje od 2** očitavanja → rezultat je:

| Polje | Vrednost |
|---|---|
| `km` | **0** |
| `source` | „Nema podatka“ |
| `requires_driver_warning` | **Da** |

**Korak 3 — izbor najboljeg para** [P]:

Prolazi se kroz **sve moguće parove** očitavanja (svako sa svakim). Par je upotrebljiv
samo ako:

> broj dana između očitavanja **> 0**  **i**  razlika kilometraže **> 0**

Za svaki upotrebljiv par računa se **ocena udaljenosti od traženog perioda**:

> ocena = |datum početnog očitavanja − početak perioda| + |datum krajnjeg očitavanja − kraj perioda|

Bira se par sa **najmanjom ocenom** — dakle par čiji su datumi najbliži granicama perioda.

**Korak 4 — preračun na dužinu perioda:**

> **procenjena kilometraža = (razlika kilometraže / broj dana između očitavanja) × broj dana perioda**

gde je `broj dana perioda = max((kraj − početak).days, 1)`. [P]

**Korak 5 — oznaka izvora** [P]:

| Oba očitavanja iz | Oznaka |
|---|---|
| Točenja | „Točenja (okvirno)“ |
| Zaduženja | „Zaduženja (okvirno)“ |
| Mešovito | „Točenja/zaduženja (okvirno)“ |

**Zaokruživanje [P]:** nema — vraća se decimalan rezultat deljenja.

**NULL vrednosti [P]:** očitavanje bez datuma se odbacuje; očitavanje bez kilometraže
ili sa nulom se odbacuje i broji u `invalid_fuel_count`, o čemu se korisnik obaveštava
tekstom *„Točenja sa kilometražom 0 su ignorisana.“*

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/dashboard.py` |
| Funkcije | `_mileage_readings()`, `_estimate_period_mileage()`, `_valid_number()` |
| Poziva je | `vehicle_cost_per_km_rows()` (V-07) |
| Ekrani | Kontrolna tabla, analitika flote, statistika centra |
| Testovi | `fleet/test_vehicle_mileage.py` (11 testova — za srodni prikaz V-13) |

#### 8. Primer obračuna

> Ilustrativni primer. Traženi period: **01.03.2026. – 31.03.2026.** (30 dana).

Dostupna očitavanja:

| Datum | Kilometraža | Izvor |
|---|---|---|
| 25.02.2026. | 120.000 | Točenje |
| 10.03.2026. | 121.200 | Točenje |
| 02.04.2026. | 122.700 | Točenje |

Ocene parova (bira se najmanja):

| Par | Razlika km | Dana | Ocena | |
|---|---|---|---|---|
| 25.02. → 02.04. | 2.700 | 36 | \|25.02.−01.03.\| + \|02.04.−31.03.\| = 4 + 2 = **6** | **izabran** |
| 25.02. → 10.03. | 1.200 | 13 | 4 + 21 = 25 | |
| 10.03. → 02.04. | 1.500 | 23 | 9 + 2 = 11 | |

| Korak | Vrednost |
|---|---|
| Razlika kilometraže | 2.700 km |
| Broj dana između očitavanja | 36 |
| Dnevni prosek = 2.700 / 36 | 75 km/dan |
| Dana u periodu | 30 |
| **Procena = 75 × 30** | **2.250 km** |
| Izvor | „Točenja (okvirno)“ |

> Uočite: **nijedno od dva izabrana očitavanja nije unutar traženog perioda.**
> To je dozvoljeno i namerno — vidi problem **P-03**.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | **Procenu**, ne izmerenu kilometražu |
| Format | Decimalan broj, km |
| Gde se čuva | Nigde — računa se pri prikazu |
| Kada se ponovo računa | Pri svakom otvaranju ekrana |
| Može li korisnik da ga izmeni | Posredno — unosom kilometraže na zaduženju |
| Istorija | Ne postoji |

Uz rezultat se uvek vraća i **objašnjenje** (`issue`) sa datumima i brojem dana
korišćenih očitavanja, koje se prikazuje korisniku. [P]

#### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Trošak po kilometru (V-07) | **Imenilac** — deli se ukupan trošak |
| Analiza kroz više perioda (V-09) | Posredno, kroz V-07 |
| Kontrolna tabla i analitika flote | Prikaz kolone „Kilometraža“ sa oznakom izvora |

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Da li je procena razumna | Uporediti sa ekranom kilometraže vozila (V-13), gde se vide stvarna očitavanja u intervalima od ~30 dana |
| Iz kojih očitavanja je izvedena | Tekst objašnjenja navodi oba datuma i broj dana |
| Da li su očitavanja unutar perioda | **Proveriti ručno** — sistem to ne garantuje |
| Nema procene | Vozilo ima manje od dva ispravna očitavanja — proveriti da li vozači unose kilometražu |

**Kontrolna formula:**

> procena = (km₂ − km₁) / (dan₂ − dan₁) × dana u periodu

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Ozbiljnost |
|---|---|---|
| Manje od 2 ispravna očitavanja | `km = 0`, upozorenje „Nema podatka“ | Vidljivo |
| **Sva očitavanja izvan perioda** | **Procena se ipak pravi** | **P-03** |
| **Očitavanja veoma udaljena od perioda** | Procena se pravi bez ograničenja udaljenosti | **P-03** |
| Kilometraža opada (zamena brojača) | Takav par se odbacuje (razlika ≤ 0); koristi se drugi par | Ispravno |
| Sva očitavanja istog dana | Nijedan par nema dana > 0 → „Nema podatka“ | Ispravno |
| Očitavanje sa kilometražom 0 | Odbacuje se, korisnik se obaveštava | Ispravno |
| Složenost izbora para | **Linearno-logaritamska** (`_best_reading_pair`) | Rešeno 19.09.2026., **P-04** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Očitavanja iz točenja i zaduženja | Potvrđeno | `dashboard.py:38-65` | — |
| Vrednosti ≤ 0 se odbacuju | Potvrđeno | `dashboard.py:30-36` | — |
| Bira se par najbliži granicama perioda | Potvrđeno | `dashboard.py:89-101` | — |
| Preračun dnevni prosek × dana perioda | Potvrđeno | `dashboard.py:107` | — |
| **Par nije ograničen na period** | **Potvrđeno — problem** | `dashboard.py` — `_best_reading_pair()` | **P-03** |
| Izbor para daje isti rezultat kao ranija petlja | Potvrđeno | `fleet/test_cost_fixes.py` — poređenje sa starom petljom | Rešeno, **P-04** |
| Rezultat je procena, ne merenje | Potvrđeno | Oznaka „okvirno“ u izvoru | — |

---

### V-07 — Trošak po kilometru po vozilu

> **Najsloženiji obračun u modulu Flota.** Objedinjuje šest vrsta troška i deli ih
> procenjenom kilometražom.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Trošak po km“ / „Cena po kilometru“ |
| Tehnički naziv | `vehicle_cost_per_km_rows()` |
| Putanja | [`fleet/support/dashboard.py:135`](../fleet/support/dashboard.py#L135) |
| Ekrani | `/analitika/` (Analitika flote), `/` (Kontrolna tabla), `/center_statistics/<centar>/` |

#### 2. Poslovna svrha

Pokazuje **koliko stvarno košta jedan pređeni kilometar** svakog vozila, radi:

- poređenja vozila međusobno i sa pragovima po klasi mase;
- prepoznavanja vozila koja više ne isplati zadržavati;
- odluke o zameni, prodaji ili otpisu vozila.

#### 3. Korisnici rezultata

Uprava, rukovodioci centara, služba voznog parka.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | JM | Napomena |
|---|---|---|---|
| Trošak goriva | `fleet_fuelconsumption.cost_bruto` | RSD | **Bruto, sa PDV-om** |
| Količina goriva | `fleet_fuelconsumption.amount` | litar | Samo za prikaz |
| Trošak servisa | `fleet_servicetransaction.potrazuje` | RSD | |
| Trošak trebovanja | `fleet_requisition.vrednost_nab` | RSD | |
| Naknada osiguranja | `fleet_insurance.potrazuje` (uz `kola = True`) | RSD | **Odbija se** |
| Premija polise | `fleet_policy.premium_amount` | RSD | |
| Kamata finansijskog lizinga | `fleet_leaseinterest.interest_amount` | RSD | |
| Rata operativnog/dugoročnog | `fleet_lease.current_payment_amount` | RSD | |
| Nabavna vrednost | `fleet_vehicle.purchase_value` | RSD | Za amortizaciju |
| Knjigovodstvena vrednost | `fleet_vehicle.value` | RSD | Za amortizaciju |
| Datum nabavke | `fleet_vehicle.purchase_date` | — | Osnov amortizacije |
| Datum prve registracije | `fleet_vehicle.first_registration_date` | — | Rezerva za osnov |
| Maks. dozvoljena masa | `fleet_vehicle.maximum_permissible_weight` | kg | Za prag (V-11) |
| Procenjena kilometraža | izračunato — **V-08** | km | **Imenilac** |

#### 5. Poreklo podataka

```
 fleet_fuelconsumption.cost_bruto        ──┐
 fleet_servicetransaction.potrazuje      ──┤
 fleet_requisition.vrednost_nab          ──┤
 fleet_policy.premium_amount             ──┼──►  UKUPAN TROŠAK
 amortizacija (izračunata)               ──┤
 lizing / najam (izračunat)              ──┤
 fleet_insurance.potrazuje  (oduzima se) ──┘
                                              │
 V-08 procena kilometraže ────────────────────┤
                                              ▼
                                    TROŠAK PO KILOMETRU
                                              │
                              V-11 prag po masi vozila
                                              ▼
                                   V-12 status vozila
```

#### 6. Tačan postupak obračuna

##### Korak 1 — koja vozila ulaze [P]

| Uslov | Vrednost |
|---|---|
| `otpis` | `False` — otpisana vozila se ne prikazuju |
| `category` | **`putnicko` ili `teretno`** — priključna vozila su isključena |

##### Korak 2 — troškovi u periodu

| Trošak | Filter perioda | Napomena |
|---|---|---|
| Gorivo | `date >= početak 00:00` i `date < kraj+1 dan 00:00` | Zbir `cost_bruto` |
| Servisi | `datum` između početka i kraja (uključivo) | Zbir `potrazuje` |
| Trebovanja | `datum_trebovanja` između početka i kraja | Zbir `vrednost_nab` |
| Naknada osiguranja | `datum` između početka i kraja, `kola = True` | Zbir `potrazuje` |
| **Polise** | `start_date <= kraj perioda` **i** `end_date >= početak perioda` | **Zbir cele premije** |
| **Kamata fin. lizinga** | `lease_type = finansijski`, `lease.end_date >= početak`, `year` u opsegu godina perioda | **Zbir cele godišnje kamate** |

> **[P] Dva troška se NE dele srazmerno periodu:** premija polise i kamata finansijskog
> lizinga ulaze **u punom iznosu** čim se period bilo kako preklopi sa njihovim važenjem.
> **Ispravljeno 19.09.2026.** — vidi **P-06** i **P-07**. Premija polise i godišnja kamata
> lizinga sada ulaze **srazmerno danima**, a ne u punom iznosu.

##### Korak 3 — lizing i najam (osim finansijskog)

Uzimaju se ugovori koji se **preklapaju** sa periodom
(`start_date <= kraj` i `end_date >= početak`), isključujući `finansijski`. [P]

**Preklapanje:**

> početak preklapanja = max(početak ugovora, početak perioda)
> kraj preklapanja = min(kraj ugovora, kraj perioda)

**A) Dugoročni najam** (`dugorocni`, `dugoročni`, `dugoročnI`) [P]:

`current_payment_amount` se tretira kao **mesečna rata** i deli po danima svakog meseca:

> za svaki mesec u preklapanju:
> deo = mesečna rata × (broj dana u tom mesecu unutar preklapanja) / (broj dana tog meseca)

Zbir svih delova je trošak najma. Kraj preklapanja se pomera za jedan dan da bi bio
isključiv. [P]

**B) Operativni lizing** [P]:

> trošak = `current_payment_amount` × (dana preklapanja) / (ukupno dana trajanja ugovora)

> **[P] Različita pravila:** kod dugoročnog najma iznos je **mesečna rata**, a kod
> operativnog lizinga se **ista kolona** razmazuje preko **celog trajanja ugovora**.
> Vidi problem **P-08**.

**C) Finansijski lizing** [P]: ne ulazi ovde — ulazi kroz kamatu (korak 2),
jer je glavnica već sadržana u amortizaciji.

##### Korak 4 — amortizacija

Računa se **samo** ako su popunjeni `purchase_value`, `value` i osnovni datum. [P]

> osnovni datum = `purchase_date`, a ako je prazan → `first_registration_date`
> dana u upotrebi = **max((kraj perioda − osnovni datum).days, 365)**
> ukupna amortizacija = **max(nabavna vrednost − knjigovodstvena vrednost, 0)**
> **amortizacija za period = ukupna amortizacija / dana u upotrebi × dana perioda**

> **[P]** `max(..., 365)` znači da se za vozilo mlađe od godinu dana amortizacija
> **razmazuje kao da je staro godinu dana** — inače bi bila nerealno velika.

##### Korak 5 — ukupan trošak

> **ukupan trošak = gorivo + servisi + trebovanja + polise + amortizacija + lizing − naknada osiguranja**

##### Korak 6 — isključivanje vozila

> **Ako je ukupan trošak ≤ 0, vozilo se potpuno izostavlja iz rezultata.** [P]

> **Ispravljeno 19.09.2026.** — vozilo bez troška **ostaje** na spisku, sa oznakom
> „Nema evidentiranog troška u periodu“ ili „Naknade osiguranja su veće od evidentiranih
> troškova u periodu“. Cena po km ostaje nepoznata, pa vozilo ne ulazi u proseke, pragove
> ni u crvenu zonu. Vidi **P-09**.

##### Korak 7 — trošak po kilometru

> **trošak po km = ukupan trošak / procenjena kilometraža**  (ako je kilometraža > 0)
> inače: **prazno** (`None`)

##### Korak 8 — napomena o maloj kilometraži

Kilometraža perioda se **svodi na godišnji nivo** (`km × 365 / dana perioda`) i tek se
ta vrednost poredi sa pragom. Ako je **> 0 i < 15.000**, uz red se prikazuje napomena:

> *„Vozilo se malo vozi (… km < 15000 km godišnje). Cena po km može biti iskrivljena
> jer se fiksni troškovi (osiguranje, doprinosi) raspoređuju na manju kilometražu.“*

U poruci stoji **preračunata godišnja** kilometraža, ista ona koja je poređena sa pragom.
Dostupna je i u redu tabele kao `annualized_km`. [P]

> **Ispravljeno 18.09.2026.** — ranije se sa godišnjim pragom poredila kilometraža
> **perioda**, pa je za jednomesečni pregled napomenu dobijalo gotovo svako vozilo.
> Videti [P-10](#10-poznati-problemi-i-ograničenja).

##### Korak 9 — sortiranje

Opadajuće po trošku po kilometru; prazne vrednosti se tretiraju kao 0. [P]

##### Zaokruživanje i NULL [P]

| Pravilo | Vrednost |
|---|---|
| Zaokruživanje | **Nema** — svi iznosi su `float`, zaokružuje šablon |
| Prazan iznos troška | Tretira se kao **0** (`number()` funkcija) |
| Prazna kilometraža | Trošak po km je **prazan**, ne 0 |
| Prazna masa vozila | Nema praga → status „Nema praga“ (V-12) |

> **[P] Napomena o tipovima:** obračun radi sa `float`, ne `Decimal`. Za poređenje
> vozila je to dovoljno, ali zbir nije knjigovodstveno tačan na paru.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/dashboard.py` |
| Glavna funkcija | `vehicle_cost_per_km_rows(period_start_date, period_end_date, limit, vehicle_ids)` |
| Pomoćna | `monthly_cost_for_overlap()` (unutar funkcije) |
| Kilometraža | `_estimate_period_mileage()` — V-08 |
| Pragovi | `fleet/support/analytics.py` — V-11, V-12 |
| Ekrani | `fleet/views/analytics.py: fleet_analytics`, `fleet/views/dashboard.py`, `fleet/views/center_statistics.py` |

**Centar vozila [P]:** uzima se **poslednja** dodela (`-assigned_date`), **bez
ograničenja na period**. Razlikuje se od izveštaja goriva po šifri posla (V-21),
koji koristi **istorijsku** dodelu na datum troška.

> **Ispravljeno 19.09.2026.:** V-07 sada uzima dodelu koja je važila **na kraju izabranog
> perioda**, pa se izveštaji za prošle periode više ne menjaju kad se vozilo kasnije
> prebaci. Vozilo koje je centar promenilo **usred** perioda i dalje nosi ceo trošak u
> centar sa kraja perioda, ali red nosi oznaku `center_changed_in_period`. Vidi **P-05**.

#### 8. Primer obračuna

> Ilustrativni primer. Putničko vozilo, period **01.01.2026. – 31.03.2026.** (89 dana).

**Ulazni podaci:**

| Stavka | Vrednost |
|---|---|
| Gorivo (bruto) u periodu | 180.000,00 RSD |
| Servisi u periodu | 45.000,00 RSD |
| Trebovanja u periodu | 12.000,00 RSD |
| Naknada osiguranja u periodu | 30.000,00 RSD |
| Polisa: 01.07.2025.–30.06.2026., premija | 60.000,00 RSD |
| Nabavna vrednost | 2.400.000,00 RSD |
| Knjigovodstvena vrednost | 1.200.000,00 RSD |
| Datum nabavke | 01.01.2021. |
| Lizing | nema |
| Procenjena kilometraža (V-08) | 6.000 km |
| Maks. dozvoljena masa | 2.000 kg |

**Obračun:**

| Korak | Račun | Vrednost |
|---|---|---|
| Gorivo | | 180.000,00 |
| Servisi | | 45.000,00 |
| Trebovanja | | 12.000,00 |
| **Polisa** | preklapa se sa periodom → **cela premija** | 60.000,00 |
| Amortizacija — dana u upotrebi | (31.03.2026. − 01.01.2021.) = 1.915 dana | 1.915 |
| Amortizacija — ukupna | 2.400.000 − 1.200.000 | 1.200.000,00 |
| Amortizacija — za period | 1.200.000 / 1.915 × 89 | 55.770,23 |
| Lizing | | 0,00 |
| Naknada osiguranja | oduzima se | −30.000,00 |
| **Ukupan trošak** | 180.000 + 45.000 + 12.000 + 60.000 + 55.770,23 + 0 − 30.000 | **322.770,23 RSD** |
| **Trošak po km** | 322.770,23 / 6.000 | **53,80 RSD/km** |
| Prag za masu 2.000 kg | Putnička do 3,5 t: dobro ≤ 25, praćenje ≤ 40, rizično ≤ 60 | |
| **Status** | 53,80 je između 40 i 60 | **„Rizično“** |
| Napomena | 6.000 km < 15.000 km | Prikazuje se upozorenje o maloj kilometraži |

> Uočite: cela godišnja premija polise (60.000,00) ušla je u tromesečni period.
> Srazmerno (89 od 365 dana) bilo bi **14.630,14 RSD** — razlika je **+310%**.
> **Ispravljeno 19.09.2026.** — vidi **P-06**.
>
> Da je premija ušla srazmerno, ukupan trošak bio bi 277.400,37 RSD, a trošak po
> kilometru **46,23 RSD/km** umesto 53,80 — i status bi bio **„Rizično“** u oba slučaja,
> ali kod vozila blizu granice ovakva razlika menja ocenu.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Procenu troška po pređenom kilometru u periodu |
| Format | Decimalan broj, RSD/km |
| Gde se čuva | **Nigde** — računa se pri svakom otvaranju |
| Kada se ponovo računa | Pri svakom otvaranju ekrana |
| Može li korisnik da ga izmeni | Ne |
| Ko može da ga potvrdi | Nema postupka potvrde |
| Istorija promene | **Ne postoji** |
| Audit trag | Ne postoji za sam rezultat; otvaranje ekrana se beleži u `ActivityLog` |

#### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Analitika flote | Tabela vozila sa statusom i pragom |
| Kontrolna tabla | Najskuplja vozila |
| Statistika centra | Vozila centra |
| Analiza kroz više perioda (V-09) | Trajno neisplativa vozila |
| Odluka uprave | Zamena, prodaja ili otpis vozila |

> **[N] Q3:** rezultat se **ne knjiži** i ne prenosi u druge module. Služi kao
> podloga za odluku. Nije potvrđeno da li se prilaže uz neki dokument.

#### 11. Kontrola i ručna provera

**Kontrolna formula:**

> (gorivo + servisi + trebovanja + polise + amortizacija + lizing − naknade) / kilometraža

| Provera | Kako |
|---|---|
| Gorivo | Uporediti sa ekranom „Fakture goriva“ za isto vozilo i period (**pažnja:** ovde je bruto) |
| Servisi | `/service-transactions/` filtrirano po vozilu i periodu |
| Trebovanja | `/requisitions/` filtrirano po vozilu |
| Polise | `/polise/` — proveriti da li polisa pokriva ceo period ili samo deo |
| Amortizacija | Ručno: (nabavna − knjigovodstvena) / dana u upotrebi × dana perioda |
| Kilometraža | Objašnjenje uz red navodi datume korišćenih očitavanja |

**Tipični uzroci razlike:**

| Uzrok | Objašnjenje |
|---|---|
| Trošak manji nego ranije za kratke periode | Polisa i kamata se od 19.09.2026. dele po danima (~~P-06~~, ~~P-07~~) |
| Trošak po km neuobičajeno visok | Procena kilometraže premala (**P-03**) |
| Vozilo bez cene po km | Ukupan trošak ≤ 0; red ostaje, uz objašnjenje (~~P-09~~) |
| Vozilo u pogrešnom centru | Uzima se dodela sa **kraja perioda**; promena usred perioda je označena (~~P-05~~) |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Otpisano vozilo | Izostavljeno | Namerno |
| Priključno vozilo | Izostavljeno | Namerno |
| Ukupan trošak = 0 | Red ostaje; RSD/km je crtica, uz „Nema evidentiranog troška u periodu“ | Ispravljeno, **P-09** |
| Ukupan trošak < 0 | Red ostaje; „Naknade osiguranja su veće od evidentiranih troškova u periodu“ | Ispravljeno, **P-09** |
| Kilometraža = 0 | Trošak po km prazan; vozilo **ostaje** u spisku | Vidljivo |
| Nema nabavne ili knjigovodstvene vrednosti | Amortizacija = 0, bez upozorenja | **P-09** |
| Knjigovodstvena vrednost veća od nabavne | Amortizacija = 0 (`max(..., 0)`) | Ispravno |
| Vozilo mlađe od godinu dana | Amortizacija razmazana na 365 dana | Namerno |
| Polisa važi jedan dan u periodu | Ulazi **jedan dan** premije | Ispravljeno, **P-06** |
| Polisa bez datuma početka ili kraja | **Ne ulazi** u trošak | Ispravljeno, **P-06** |
| Finansijski lizing, period od mesec dana | Ulazi **srazmeran deo** godišnje kamate | Ispravljeno, **P-07** |
| Prestupna godina | Imenilac kamate je **366 dana** | Ispravljeno, **P-07** |
| Vozilo promenilo centar u periodu | Trošak ide na centar sa **kraja perioda**, red je označen | Delimično, **P-05** |
| Period kraći od godinu dana | Kilometraža se **svodi na godišnji nivo** pre poređenja sa pragom od 15.000 km | Ispravljeno, **P-10** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje / problem |
|---|---|---|---|
| Ulaze samo neotpisana putnička i teretna vozila | Potvrđeno | `dashboard.py:150-153` | — |
| Gorivo se uzima kao **bruto** (`cost_bruto`) | Potvrđeno | `dashboard.py:166` | Potvrditi da je bruto željen |
| Formula ukupnog troška | Potvrđeno | `dashboard.py:314-322` | — |
| Amortizacija po danima, najmanje 365 | Potvrđeno | `dashboard.py:307-312` | — |
| Dugoročni najam se deli po mesecima | Potvrđeno | `dashboard.py:274-278` | — |
| Operativni lizing se deli preko celog ugovora | Potvrđeno | `dashboard.py:280-285` | **P-08** |
| Polisa ulazi srazmerno danima preklapanja | Potvrđeno | `dashboard.py` — `policy_cost_by_vehicle` | Rešeno, **P-06** |
| Kamata ulazi srazmerno danima u godini | Potvrđeno | `dashboard.py` — `financial_interest_by_vehicle` | Rešeno, **P-07** |
| Vozila sa troškom ≤ 0 ostaju na spisku | Potvrđeno | `dashboard.py` — `has_cost`, `no_cost_note` | Rešeno, **P-09** |
| Kilometraža se svodi na godišnji nivo pre poređenja sa pragom | Potvrđeno | `dashboard.py:331-333` | Rešeno, **P-10** |
| Centar je onaj sa **kraja perioda** | Potvrđeno | `dashboard.py` — `center_at_period_end` | Rešeno, **P-05** |
| Promena centra unutar perioda je označena | Potvrđeno | `dashboard.py` — `center_changed_in_period` | Rešeno, **P-05** |
| Da li je bruto gorivo ispravan izbor | **Nepotvrđeno** | — | **Q17** |

---

### V-11 — Pragovi fiksnog troška po kilometru

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Prag“, „Klasa vozila“ |
| Tehnički naziv | `fixed_cost_per_km_threshold()`, `fixed_cost_per_km_ranges()` |
| Putanja | [`fleet/support/analytics.py:14`](../fleet/support/analytics.py#L14) |

#### 2. Poslovna svrha

Trošak po kilometru nije uporediv između putničkog automobila i kamiona. Pragovi
definišu **šta je prihvatljivo za koju klasu vozila**, prema maksimalnoj dozvoljenoj masi.

#### 3. Korisnici rezultata

Uprava, rukovodioci centara, služba voznog parka.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | JM |
|---|---|---|---|
| Maksimalna dozvoljena masa | Maksimalna dozvoljena masa (kg) | `fleet_vehicle.maximum_permissible_weight` | kg |

#### 5. Poreklo podataka

Ručni unos u obrascu vozila, sa saobraćajne dozvole. **Nema sinhronizacije** — ako
podatak nije unet, prag se ne može odrediti. [P]

#### 6. Tačan postupak obračuna

**Pragovi su fiksni i upisani u kod** (`_WEIGHT_CLASS_THRESHOLDS`). Nisu u bazi i ne
mogu se menjati kroz interfejs. [P]

| Klasa vozila | Masa (kg) | Dobro ≤ | Za praćenje ≤ | Rizično ≤ | Iznad = |
|---|---|---|---|---|---|
| Putnička vozila (do 3.5t) | do 3.500 | **25** | **40** | **60** | Neisplativo |
| Laka teretna (3.5t – 7.5t) | 3.501 – 7.500 | **45** | **70** | **100** | Neisplativo |
| Srednja teretna (7.5t – 12t) | 7.501 – 12.000 | **70** | **110** | **140** | Neisplativo |
| Teška teretna (preko 12t) | preko 12.000 | **120** | **150** | **175** | Neisplativo |

*(svi pragovi u RSD po kilometru)*

**Postupak izbora:**

1. Ako je masa **prazna ili ≤ 0** → **nema praga** (`None`). [P]
2. Inače se uzima **prva klasa** čija gornja granica nije manja od mase vozila.

> **[P] Mrtav kod:** funkcija ima i rezervnu vrednost „Nepoznato“ (60/100/150), ali je
> **nedostižna**, jer poslednja klasa ima gornju granicu `beskonačno`.

**Grupna statistika** (`cost_per_km_thresholds`) [P]: za prikaz u tabeli, vozila se
grupišu po klasi mase i računa se **prosek troška po km** te klase i broj vozila.
Vozila bez praga se **izostavljaju** iz grupne statistike.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/analytics.py` |
| Konstanta | `_WEIGHT_CLASS_THRESHOLDS` (linija 14) |
| Funkcije | `fixed_cost_per_km_ranges()`, `fixed_cost_per_km_threshold()`, `cost_per_km_thresholds()` |

#### 8. Primer

| Vozilo | Masa | Klasa | Dobro | Praćenje | Rizično |
|---|---|---|---|---|---|
| Putnički automobil | 1.800 kg | Putnička do 3,5 t | ≤ 25 | ≤ 40 | ≤ 60 |
| Kombi | 3.500 kg | **Putnička do 3,5 t** | ≤ 25 | ≤ 40 | ≤ 60 |
| Kombi | 3.501 kg | Laka teretna | ≤ 45 | ≤ 70 | ≤ 100 |
| Kamion | 18.000 kg | Teška teretna | ≤ 120 | ≤ 150 | ≤ 175 |
| Vozilo bez unete mase | — | **Nema praga** | — | — | — |

> Granica 3.500 kg pripada **putničkoj** klasi (uslov je `masa <= 3500`). [P]

#### 9–10. Rezultat i upotreba

Prag nije samostalan rezultat — koristi ga isključivo V-12 za određivanje statusa vozila
i tabela grupne statistike po klasama.

#### 11. Kontrola i ručna provera

Uporediti masu vozila sa saobraćajnom dozvolom. Ako vozilo ima status „Nema praga“,
proveriti polje „Maksimalna dozvoljena masa“ u obrascu vozila.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Masa nije uneta | **Nema praga** — vozilo bez ocene | **P-11** |
| Masa je 0 | Isto kao da nije uneta | **P-11** |
| **Pragovi zastareli** | Nema mehanizma za izmenu bez izmene koda | **P-11** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Četiri klase i njihove granice | Potvrđeno | `analytics.py:14-19` | — |
| Vrednosti pragova u RSD/km | Potvrđeno | Komentar u kodu | — |
| Bez mase nema praga | Potvrđeno | `analytics.py:41-42` | — |
| **Poreklo i osnov pragova** | **Nepotvrđeno** | Nema izvora u kodu | **Q18** |
| Da li su pragovi još važeći | **Nepotvrđeno** | — | **Q18** |

---

### V-12 — Status vozila prema trošku po kilometru

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Status“ — „Dobro“, „Za praćenje“, „Rizično“, „Neisplativo“, „Opomena“, „Nema praga“ |
| Tehnički naziv | `cost_per_km_status()`, `is_red_zone()` |
| Putanja | [`fleet/support/analytics.py:79`](../fleet/support/analytics.py#L79) |

#### 2. Poslovna svrha

Pretvara broj (RSD/km) u **jasnu ocenu** koju netehnički korisnik odmah razume.

#### 6. Tačan postupak obračuna

##### A) Status prema trošku po kilometru [P]

| Uslov | Status |
|---|---|
| Trošak po km je **prazan** | **„Opomena“** |
| Vozilo **nema prag** (nije uneta masa) | **„Nema praga“** |
| trošak ≤ prag „dobro“ | **„Dobro“** |
| trošak ≤ prag „za praćenje“ | **„Za praćenje“** |
| trošak ≤ prag „rizično“ | **„Rizično“** |
| trošak > prag „rizično“ | **„Neisplativo“** |

> **[Z] Pažnja na naziv:** status **„Opomena“** ne znači da je vozilo problematično —
> znači da **nema podatka o kilometraži**, pa se trošak po km nije mogao izračunati.
> Naziv je obmanjujuć; vidi pitanje **Q19**.

##### B) „Crvena zona“ — zaseban pokazatelj [P]

Koristi se na statistici centra (V-24), **nezavisno** od pragova po masi:

> vozilo je u crvenoj zoni ako:
> **nije** u dugoročnom najmu **i** knjigovodstvena vrednost **> 0**
> **i** neto trošak održavanja **>** knjigovodstvena vrednost

Poslovno značenje [Z]: u vozilo je uloženo više nego što ono vredi.

Dugoročni najam je izuzet jer vozilo nije u vlasništvu, pa poređenje sa
knjigovodstvenom vrednošću nema smisla. [Z]

#### 8. Primer

| Vozilo | Masa | Trošak/km | Prag „dobro“ | Prag „praćenje“ | Prag „rizično“ | Status |
|---|---|---|---|---|---|---|
| Automobil A | 1.800 kg | 22,00 | 25 | 40 | 60 | **Dobro** |
| Automobil B | 1.800 kg | 38,50 | 25 | 40 | 60 | **Za praćenje** |
| Automobil C | 1.800 kg | 53,80 | 25 | 40 | 60 | **Rizično** |
| Automobil D | 1.800 kg | 72,00 | 25 | 40 | 60 | **Neisplativo** |
| Kamion E | 18.000 kg | 130,00 | 120 | 150 | 175 | **Za praćenje** |
| Vozilo F | — | 45,00 | — | — | — | **Nema praga** |
| Vozilo G | 1.800 kg | prazno | 25 | 40 | 60 | **Opomena** |

> Kamion sa 130 RSD/km je „Za praćenje“, dok je automobil sa 72 RSD/km „Neisplativo“ —
> upravo zato pragovi zavise od klase vozila.

#### 9–11. Rezultat, upotreba i kontrola

Status se prikazuje uz svako vozilo u analitici flote i ulazi u V-09
(trajno neisplativa vozila). Kontrola: uporediti trošak po km sa tabelom pragova (V-11).

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Šest mogućih statusa i njihovi uslovi | Potvrđeno | `analytics.py:79-90` | — |
| Definicija crvene zone | Potvrđeno | `analytics.py:8-9` | — |
| Dugoročni najam izuzet iz crvene zone | Potvrđeno | `analytics.py:9` | — |
| **Naziv „Opomena“ za nedostatak podatka** | Potvrđeno | `analytics.py:80-81` | **Q19** |

---

### V-09 — Analiza troška po km kroz više perioda

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Trajno neisplativa vozila“ |
| Tehnički naziv | `cost_per_km_period_analysis()` |
| Putanja | [`fleet/support/dashboard.py:371`](../fleet/support/dashboard.py#L371) |

#### 2. Poslovna svrha

Jedan loš period može biti posledica velikog servisa. Ovaj obračun izdvaja vozila koja
su **neisplativa u svim posmatranim periodima** — kod njih nije reč o slučajnosti.

#### 6. Tačan postupak obračuna

1. Za **svaki** period se izvrši ceo obračun V-07. [P]
2. Svakom redu se dodeli status po V-12.
3. Redovi se grupišu po vozilu.
4. Vozilo ulazi u rezultat **samo ako** se pojavljuje u **svim** periodima
   **i** ima status **„Neisplativo“ u svima**. [P]
5. Za takvo vozilo uzima se red iz **prvog** perioda i dodaje poređenje sa **drugim**:

> **promena (%) = (trošak/km u prvom periodu − trošak/km u drugom periodu) / trošak/km u drugom periodu × 100**

Ako je trošak u drugom periodu 0 → promena je **0**. [P]

6. Sortiranje: opadajuće po trošku po kilometru prvog perioda. [P]

> **[P] Zahtev:** funkcija koristi `periods[0]` i `periods[1]`, pa **zahteva najmanje
> dva perioda**. Sa jednim periodom prekida se greškom. Vidi problem **P-12**.

#### 8. Primer

> Periodi: „Tekuća godina“ (prvi) i „Prethodna godina“ (drugi).

| Vozilo | Tekuća godina | Status | Prethodna godina | Status | U rezultatu |
|---|---|---|---|---|---|
| A | 72,00 | Neisplativo | 68,00 | Neisplativo | **Da** |
| B | 72,00 | Neisplativo | 35,00 | Za praćenje | Ne |
| C | 80,00 | Neisplativo | — (nema podataka) | — | Ne |

Za vozilo A: promena = (72,00 − 68,00) / 68,00 × 100 = **+5,88%**.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Vozilo nema podatke u jednom periodu | **Ne ulazi** u rezultat | Namerno |
| Prosleđen samo jedan period | **Greška u izvršavanju** | **P-12** |
| Više od dva perioda | Poređenje se pravi **samo sa drugim** | Vidljivo |
| Trošak u drugom periodu = 0 | Promena je 0, ne beskonačno | Ispravno |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Vozilo mora biti „Neisplativo“ u svim periodima | Potvrđeno | `dashboard.py:396-398` | — |
| Poređenje ide sa drugim periodom | Potvrđeno | `dashboard.py:401-403` | — |
| **Zahteva najmanje dva perioda** | **Potvrđeno** | `dashboard.py:401` | **P-12** |

---

### V-10 — Neto trošak održavanja

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Neto trošak održavanja“ |
| Tehnički naziv | `net_maintenance_cost()` |
| Putanja | [`fleet/support/analytics.py:4`](../fleet/support/analytics.py#L4) |

#### 2. Poslovna svrha

Stvarni trošak održavanja vozila **umanjen za ono što je osiguranje nadoknadilo**.
Bez tog umanjenja vozilo posle saobraćajne nezgode izgleda mnogo skuplje nego što jeste.

#### 6. Tačan postupak obračuna

> **neto trošak održavanja = trošak servisa + trošak trebovanja − naknada osiguranja**

Prazne vrednosti se tretiraju kao **0**. [P]

| Sastojak | Tabela i kolona | Uslov |
|---|---|---|
| Trošak servisa | `fleet_servicetransaction.potrazuje` | — |
| Trošak trebovanja | `fleet_requisition.vrednost_nab` | — |
| Naknada osiguranja | `fleet_insurance.potrazuje` | **`kola = True`** |

> **[P]** Uslov `kola = True` znači „knjiženje se odnosi na automobil“. Naknade koje
> nisu obeležene tako se **ne odbijaju**.

#### 8. Primer

| Stavka | Vrednost |
|---|---|
| Servisi | 145.000,00 RSD |
| Trebovanja | 38.000,00 RSD |
| Naknada osiguranja | −90.000,00 RSD |
| **Neto trošak održavanja** | **93.000,00 RSD** |

#### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Statistika centra (V-24) | Zbir po centru i po vozilu |
| Crvena zona (V-12) | Poredi se sa knjigovodstvenom vrednošću |
| Detalj vozila (V-15) | Prikaz uz ukupne iznose |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Naknada veća od troška | **Negativan rezultat** — dozvoljeno, znači da je nadoknađeno više nego što je potrošeno |
| Naknada nije obeležena sa `kola = True` | Ne odbija se |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Formula servisi + trebovanja − naknade | Potvrđeno | `analytics.py:5` |
| Prazne vrednosti kao 0 | Potvrđeno | `analytics.py:5` |
| Uslov `kola = True` za naknade | Potvrđeno | `dashboard.py:205`, `center_statistics.py:97` |

---

### V-15 — Analitika evidentiranih troškova na detalju vozila

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Kartica „Analitika“ na detalju vozila |
| Tehnički naziv | `recorded_analytics()` |
| Putanja | [`fleet/support/vehicle_detail.py:35`](../fleet/support/vehicle_detail.py#L35) |

#### 2. Poslovna svrha

Za **jedno vozilo i izabrani period** prikazuje **samo evidentirane iznose** — bez
procena, bez amortizacije, bez preračuna. Namerno se razlikuje od V-07.

> **[P] Izričita namera iz koda:** *„Period-based, recorded amounts for the vehicle
> dossier (no TCO estimates)“* — evidentirani iznosi, bez procene ukupnog troška vlasništva.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Datum po kome se filtrira |
|---|---|---|
| Gorivo | `fleet_fuelconsumption.cost_bruto` | `date` |
| Servisi | `fleet_servicetransaction.potrazuje` | `datum` |
| Trebovanja | `fleet_requisition.vrednost_nab` | `datum_trebovanja` |
| Naknade osiguranja | `fleet_insurance.potrazuje` | `datum` |
| Kategorija popravke | `fleet_servicetype.name` preko `popravka_kategorija` | — |

**Ograničenja perioda** (`VehiclePeriodForm`) [P]:

| Pravilo | Poruka |
|---|---|
| Početak mora biti pre kraja | „Početak perioda mora biti pre kraja perioda.“ |
| **Najviše 1.096 dana (3 godine)** | „Izaberite period do tri godine.“ |
| **Kraj ne sme biti u budućnosti** | „Analitika evidentiranih troškova ne obuhvata buduće datume.“ |

#### 6. Tačan postupak obračuna

1. Napravi se **mesečni raster** od početka do kraja perioda; svaki mesec počinje
   praznim vrednostima (`None`), **ne nulama**. [P]
2. Za svaku od četiri vrste troška prolazi se kroz stavke; stavka ulazi samo ako
   ima datum **unutar perioda** i iznos koji nije prazan.
3. Za svaku stavku: uvećava se ukupan zbir, broj stavki i iznos odgovarajućeg meseca.
4. Servisi i trebovanja dodatno se zbrajaju **po kategoriji popravke**;
   stavka bez kategorije ide u **„Nerazvrstano“**. [P]
5. Izvedene veličine:

> **održavanje = servisi + trebovanja**
> **neto održavanje = održavanje − naknade osiguranja**

6. **Kilometraža** se računa **samo iz točenja goriva** (ne iz zaduženja):
   - po danu se uzimaju najmanja i najveća vrednost kilometraže;
   - potrebne su **najmanje dve** tačke;
   - ako bilo gde vrednost **opada**, prikazuje se upozorenje
     *„Očitanja kilometraže opadaju; proveriti unose ili zamenu brojača.“* i kilometraža
     se **ne prikazuje**;
   - inače: **kilometraža = najveća vrednost poslednjeg dana − najmanja vrednost prvog dana**.

7. Za grafički prikaz kategorija računa se širina trake:

> širina (%) = |iznos kategorije| / najveći apsolutni iznos × 100

**Znak iznosa [P]:** iznosi zadržavaju **izvorni knjigovodstveni znak** — storna i
ispravke ostaju negativne.

**Prazno naspram nule [P]:** mesec bez ijedne stavke ima `None`, ne `0`. Razlika je
namerna i vidljiva na ekranu.

#### 8. Primer

> Vozilo, period 01.01.2026. – 31.03.2026.

| Mesec | Gorivo | Servisi | Trebovanja | Održavanje | Naknade |
|---|---|---|---|---|---|
| Januar | 60.000,00 | — | — | 0,00 | — |
| Februar | 58.000,00 | 45.000,00 | 12.000,00 | 57.000,00 | −30.000,00 |
| Mart | 62.000,00 | — | — | 0,00 | — |
| **Ukupno** | **180.000,00** | **45.000,00** | **12.000,00** | **57.000,00** | **−30.000,00** |

| Izvedeno | Vrednost |
|---|---|
| Održavanje | 45.000 + 12.000 = **57.000,00** |
| Neto održavanje | 57.000 − 30.000 = **27.000,00** |

Kilometraža iz točenja: prvi dan 120.000, poslednji dan 126.000 → **6.000 km**.

#### 9–11. Rezultat, upotreba i kontrola

Rezultat se prikazuje samo na detalju vozila; nigde se ne čuva i ne prenosi.
Kontrola: zbir mesečnih iznosa mora biti jednak ukupnom iznosu; ukupan iznos goriva
mora odgovarati ekranu „Fakture goriva“ za isto vozilo i period (bruto).

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Period duži od 3 godine | Obrazac odbija unos |
| Kraj u budućnosti | Obrazac odbija unos |
| Kilometraža opada | Upozorenje, kilometraža se ne prikazuje |
| Manje od 2 dana sa očitavanjem | Kilometraža se ne prikazuje |
| Mesec bez stavki | Prazno, ne nula |
| Servis bez kategorije | „Nerazvrstano“ |

> **[P] Razlika prema V-07:** ova analitika **ne uključuje** amortizaciju, lizing i
> polise, i kilometražu računa **samo iz točenja**. Zbog toga se iznosi na detalju
> vozila i u analitici flote **legitimno razlikuju** — to nije greška.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Samo evidentirani iznosi, bez procena | Potvrđeno | `vehicle_detail.py:1, 35` |
| Prazno se razlikuje od nule | Potvrđeno | `vehicle_detail.py:40` |
| Znak iznosa se čuva | Potvrđeno | `vehicle_detail.py:35` |
| Kilometraža samo iz točenja | Potvrđeno | `vehicle_detail.py:66-70` |
| Ograničenje perioda na 3 godine | Potvrđeno | `vehicle_detail.py:22-23` |

---

### V-24 — Statistika po centrima

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Statistika centra“ |
| Tehnički naziv | `center_statistics()` |
| Putanja | [`fleet/views/center_statistics.py:57`](../fleet/views/center_statistics.py#L57) |
| Adresa | `/center_statistics/<sifra_centra>/` |

#### 2. Poslovna svrha

Zbirna slika voznog parka jednog centra: broj vozila, vrednost, starost, troškovi,
potrošnja goriva i spisak vozila u **crvenoj zoni**.

#### 3. Korisnici rezultata

Rukovodilac centra, uprava.

#### 4. Ulazni podaci

Isti izvori kao V-07 i V-10, ali **bez ograničenja perioda**.

#### 6. Tačan postupak obračuna

**Korak 1 — kontrola pristupa** [P]:

> Pristup je dozvoljen ako je korisnik **superuser** ili ako ima taj centar
> u `allowed_centers`. [P]

> **Ispravljeno 18.09.2026.** — ranije provera nije izuzimala `is_superuser`, pa je
> administrator bez upisanih centara dobijao **403 Zabranjeno**.
> Videti [P-13](#10-poznati-problemi-i-ograničenja).

**Korak 2 — vozila centra:** sva vozila čija je **poslednja** dodela u tom centru,
**bez otpisanih** (`otpis=False`). [P]

> **Ispravljeno 18.09.2026.** — otpisana vozila su ranije ulazila u broj vozila,
> vrednost i troškove centra. Zbog toga **iznosi centra od sada mogu biti manji nego
> ranije**. Videti [P-14 A](#10-poznati-problemi-i-ograničenja).

**Korak 3 — zbirovi po vozilu, bez filtera perioda** [P]:

| Pokazatelj | Izvor | Period |
|---|---|---|
| Trošak servisa | `potrazuje` | **Sve vreme** |
| Trošak trebovanja | `vrednost_nab` | **Sve vreme** |
| Količina goriva | `amount` | **Sve vreme** |
| Trošak goriva | `cost_bruto` | **Sve vreme** |
| Naknada osiguranja | `potrazuje`, `kola = True` | **Sve vreme** |
| Dugoročni najam | postoji li takav ugovor | — |

**Korak 4 — zbirni pokazatelji centra:**

| Pokazatelj | Formula |
|---|---|
| Broj vozila | broj vozila centra |
| Ukupna vrednost | Σ knjigovodstvena vrednost |
| Prosečna vrednost | ukupna vrednost / broj vozila |
| **Prosečna starost** | tekuća godina − (Σ godina proizvodnje / broj vozila **sa poznatom godinom**) |
| Ukupan neto trošak održavanja | Σ V-10 po vozilu |
| Odnos održavanja i vrednosti | ukupno neto održavanje / ukupna vrednost × 100 |
| Broj vozila u crvenoj zoni | broj vozila po V-12 B |

> **[P]** U prosečnu starost ulaze **samo vozila sa godinom proizvodnje između 1886. i
> tekuće**, isto kao u preseku stanja flote. Ako nijedno vozilo nema unetu godinu,
> prikazuje se `—`, a ne broj. Ekran uz pokazatelj prikazuje i **za koliko vozila je
> godište poznato** (`poznato godište X/Y`), da prosek ne bi obmanuo kada je poznat za
> mali deo voznog parka.
>
> **Ispravljeno 18.09.2026.** — ranije je vozilo bez godine ulazilo kao **0**, pa je
> „prosečna starost“ znala da bude i preko hiljadu godina.
> Videti [P-14 B](#10-poznati-problemi-i-ograničenja).

**Korak 5 — po vozilu:**

| Pokazatelj | Formula |
|---|---|
| Neto trošak održavanja | V-10 |
| Odnos ulaganja i vrednosti | neto održavanje / knjigovodstvena vrednost × 100 |
| Razlika do vrednosti | neto održavanje − knjigovodstvena vrednost |
| Crvena zona | V-12 B |

Vozila u crvenoj zoni sortiraju se opadajuće po razlici do vrednosti. [P]

**Korak 6 — mesečni pregled** [P]: gorivo (količina i iznos), servisi razvrstani po
kategoriji popravke, i premije polisa.

Razvrstavanje ide u dva koraka: nazivi svih kategorija iz `ServiceType` se prvo
**normalizuju** (mala slova, uklonjeni dijakritici, sređeni razmaci), pa se po ključnoj
reči dobije spisak šifara; iznosi se zatim filtriraju **po šifri kategorije**. [P]

| Kolona | Ključna reč u normalizovanom nazivu |
|---|---|
| Gume | `gume` |
| Redovan servis | `redovan servis` |
| Tehnički pregled | `tehnicki pregled` |
| Registracija | `registracija` |

Mesečni pregled prikazuje šest iznosa: količinu i trošak goriva, gume, redovan servis,
tehnički pregled i registraciju, uz premije polisa — svaki sa zbirom i mesečnim
prosekom. [P]

> **Ispravljeno 18.09.2026.** — ranije se poređenje radilo nad **sirovim** nazivom, pa
> kategorija „Tehnički pregled“ (sa „č“) nije bila prepoznata. Uz to se taj iznos, iako
> izračunat, **nigde nije prikazivao** — nije bio ni u zbirovima ni u tabeli. Zato je
> dodata i **kolona „Trošak Tehnički Pregled (Din)“**.
> Videti [P-14 C](#10-poznati-problemi-i-ograničenja).

**Korak 7 — proseci:** ukupan iznos podeljen **brojem meseci koji imaju bilo kakav
zapis** — ne brojem meseci u kalendaru. [P]

#### 8. Primer

> Ilustrativni primer, centar sa 3 vozila.

| Vozilo | Knjig. vrednost | Servisi | Trebovanja | Naknade | Neto održavanje | Crvena zona |
|---|---|---|---|---|---|---|
| A | 1.200.000 | 145.000 | 38.000 | 90.000 | 93.000 | Ne |
| B | 300.000 | 420.000 | 55.000 | 0 | 475.000 | **Da** (475.000 > 300.000) |
| C | 0 | 80.000 | 10.000 | 0 | 90.000 | Ne (vrednost nije > 0) |

| Pokazatelj centra | Vrednost |
|---|---|
| Ukupna vrednost | 1.500.000,00 |
| Ukupno neto održavanje | 658.000,00 |
| Odnos održavanja i vrednosti | 658.000 / 1.500.000 × 100 = **43,87%** |
| Vozila u crvenoj zoni | **1** (vozilo B) |

#### 9–11. Rezultat, upotreba i kontrola

Rezultat se prikazuje na ekranu i nigde ne čuva. Kontrola: zbir po vozilima mora biti
jednak zbiru centra; spisak vozila u crvenoj zoni mora se slagati sa ručnim poređenjem
neto održavanja i knjigovodstvene vrednosti.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Superuser bez dozvoljenih centara | Pristup dozvoljen | Ispravljeno, **P-13** |
| Otpisana vozila | Isključena iz statistike | Ispravljeno, **P-14 A** |
| Vozilo bez godine proizvodnje | Ne ulazi u prosečnu starost; ekran prikazuje `poznato godište X/Y` | Ispravljeno, **P-14 B** |
| Nijedno vozilo nema godinu | Prosečna starost se prikazuje kao `—` | Ispravljeno, **P-14 B** |
| Kategorija sa dijakriticima | Prepoznaje se — nazivi se normalizuju pre poređenja | Ispravljeno, **P-14 C** |
| Vozilo bez knjigovodstvene vrednosti | Ne može biti u crvenoj zoni | Namerno |
| Vozilo u dugoročnom najmu | Ne može biti u crvenoj zoni | Namerno |
| Svi iznosi su **za ceo vek vozila** | Nema izbora perioda | Namerno, ali nije naznačeno na ekranu |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Iznosi su za ceo vek vozila, bez perioda | Potvrđeno | `center_statistics.py:72-101` | **P-14 D** |
| Centar je poslednja dodela | Potvrđeno | `center_statistics.py:65-67` | **P-05** |
| Superuser ima pristup | Potvrđeno | `center_statistics.py` — provera `is_superuser` | Rešeno, **P-13** |
| Otpisana vozila su isključena | Potvrđeno | `center_statistics.py` — `otpis=False` | Rešeno, **P-14 A** |
| Prosečna starost samo iz poznatih godišta | Potvrđeno | `center_statistics.py` — opseg 1886 … tekuća | Rešeno, **P-14 B** |
| Kategorije se prepoznaju bez obzira na dijakritike | Potvrđeno | `center_statistics.py` — `service_type_ids_by_keyword()` | Rešeno, **P-14 C** |
| Iznosi su za ceo vek vozila i to nije naznačeno na ekranu | Potvrđeno | `center_statistics.py` | **P-14 D — ostaje** |

---

### Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q17** | Trošak po kilometru koristi **bruto** iznos goriva (`cost_bruto`, sa PDV-om), dok izveštaji po šifri posla prikazuju i neto. Da li je bruto željeni osnov za poređenje vozila? |
| **Q18** | Odakle potiču pragovi troška po kilometru (25/40/60 za putnička, 120/150/175 za teška teretna)? Da li su još važeći i da li treba da budu izmenljivi kroz interfejs umesto u kodu? |
| **Q19** | Status **„Opomena“** dodeljuje se vozilu kod koga **nema podatka o kilometraži**, što korisnika navodi da pomisli da je vozilo problematično. Može li se preimenovati u „Nema kilometraže“? |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.2. Flota — gorivo](#62-flota--obračuni-goriva) | Prečišćavanje transakcija, potrošnja, gorivo po šifri posla |
| [6.4. Flota — ugovori i polise](#64-flota--polise-lizing-i-servisi) | Mesečni troškovi polisa, lizinga i servisa |
| [6.5. Flota — izveštaji](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji) | Kilometraža, održavanje, presek flote, izveštaji za upravu |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema P-03 … P-14 |

---

## 6.4. Flota — polise, lizing i servisi

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](#10-poznati-problemi-i-ograničenja).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [V-17](#v-17--mesečni-troškovi-polisa) | Mesečni troškovi polisa | — |
| [V-18](#v-18--polise-pred-istekom-i-neobnovljene-polise) | Polise pred istekom i neobnovljene polise | — |
| [V-19](#v-19--mesečni-troškovi-lizinga) | Mesečni troškovi lizinga | **P-23, P-24, P-25** |
| [V-20](#v-20--mesečni-troškovi-servisa) | Mesečni troškovi servisa | — |

---

### Zajednička osnova: istorijska šifra posla

Tri od četiri obračuna u ovom poglavlju raspoređuju trošak na **šifru posla koja je
vozilu bila dodeljena na datum dokumenta** — ne na trenutnu. [P]

```
JobCode.objects.filter(
    vehicle = vozilo,
    assigned_date <= datum dokumenta        ← ključni uslov
).order_by("-assigned_date")[:1]
```

| Obračun | Datum po kome se traži dodela | Istorijski |
|---|---|---|
| V-17 Polise | `issue_date` (datum izdavanja polise) | **Da** |
| V-19 Lizing | — | **Ne** — koristi poslednju dodelu |
| V-20 Servisi | `datum` (datum knjiženja servisa) | **Da** |

> **[P]** V-19 odstupa od ostalih — vidi problem **P-24**.

---

### V-17 — Mesečni troškovi polisa

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Mesečni troškovi polisa“ |
| Tehnički naziv | `policies_monthly_costs_qs()` |
| Putanja | [`fleet/support/policy_queries.py:16`](../fleet/support/policy_queries.py#L16) |
| Adrese | `/izvestaji/policies-monthly-costs/`, izvoz `/izvestaji/policies-monthly-costs.csv` |

#### 2. Poslovna svrha

Pokazuje **koliko je osiguranje vozila koštalo po mesecu, centru, šifri posla i vrsti
osiguranja** — za planiranje i za raspodelu troška na nosioce posla.

#### 3. Korisnici rezultata

Služba voznog parka, rukovodioci centara, finansije.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | JM | Obavezno | Ko unosi |
|---|---|---|---|---|---|---|
| Datum izdavanja polise | Datum izdavanja | `fleet_policy.issue_date` | datum | — | Ne | Automatski / ručno |
| Iznos premije | Iznos premije | `fleet_policy.premium_amount` | `decimal(10,2)` | RSD | Ne | Automatski / ručno |
| Tip osiguranja | Tip osiguranja | `fleet_policy.insurance_type` | tekst | — | Ne | Automatski / ručno |
| Vozilo | Vozilo | `fleet_policy.vehicle_id` | veza | — | Ne | Ručno (dopuna) |
| Dodela šifre posla | — | `fleet_jobcode.assigned_date`, `organizational_unit` | veza | — | Da | Sinhronizacija |

**Filteri ekrana** (svi opcioni) [P]: godina, mesec, centar, organizaciona jedinica, vrsta.

#### 5. Poreklo podataka

```
 Faktura osiguranja (nabavka, EUF)
        │  sinhronizacija polisa, dnevno u 02:00
        ▼
 fleet_policy (issue_date, premium_amount, insurance_type, vehicle)
        │
        ├── fleet_jobcode: dodela važeća na issue_date ──► šifra posla, naziv, centar
        │
        ▼
 grupisanje: godina × mesec × centar × OJ × vrsta  →  zbir premija
```

> **[P]** Polise se ne unose ručno u redovnom radu — puni ih sinhronizacija iz faktura
> dobavljača osiguranja (`fleet/sync/external.py: fetch_policy_data`), koja prepoznaje
> partnera po nazivu koji sadrži **„osiguranje“** ili **„ddor“**.

#### 6. Tačan postupak obračuna

**Korak 1 — izvedene kolone po polisi** [P]:

| Kolona | Kako se dobija |
|---|---|
| `year` | Godina iz `issue_date` |
| `month` | Mesec iz `issue_date` |
| `oj_id`, `oj_name`, `job_code`, `center` | Iz dodele važeće **na datum izdavanja polise** |
| `vrsta` | Normalizovan tip osiguranja (vidi korak 2) |

**Korak 2 — normalizacija vrste osiguranja** [P]:

| Vrednost u bazi (bez obzira na velika/mala slova) | Prikazana vrsta |
|---|---|
| `kasko` | **`kasko`** |
| `autoodgovornost` | **`autoodgovornost`** |
| bilo šta drugo | **prepisuje se doslovno** |

> **[P]** Poređenje je **tačno jednako** (`iexact`), ne „sadrži“. Vrednost
> „Kasko osiguranje“ **neće** biti svedena na `kasko` — prikazaće se doslovno i
> činiti **zasebnu grupu**.

**Korak 3 — grupisanje i zbir:**

> grupa = (godina, mesec, centar, OJ, šifra posla, vrsta)
> **iznos = zbir `premium_amount` svih polisa u grupi**

**Korak 4 — sortiranje:** godina, mesec, centar, OJ, šifra posla, vrsta — sve rastuće. [P]

**Zaokruživanje [P]:** nema — zbrajaju se izvorni decimalni iznosi.

**NULL vrednosti [P]:**

| Situacija | Posledica |
|---|---|
| `issue_date` je prazan | Godina i mesec su **prazni** — red se svrstava u grupu bez perioda |
| `premium_amount` je prazan | Ne uvećava zbir (`SUM` preskače NULL) |
| Vozilo nije povezano | Nema dodele → šifra posla, OJ i centar su **prazni** |
| Nema dodele pre datuma polise | Isto — prazna šifra posla |

> **[P] Obuhvat:** obračun uzima **sve** polise, uključujući **nedovršene**
> (one koje ne prolaze `Policy.is_complete()`). Filter potpunosti ovde se **ne primenjuje**
> — za razliku od V-18.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/policy_queries.py` |
| Funkcije | `policies_monthly_costs_qs()`, `_filtered_qs()` |
| Istorijska dodela | konstanta `_latest_jc` (linija 10) |
| View | `fleet/views/policy.py: PoliciesMonthlyCostsView`, `policies_monthly_costs_csv` |
| Dozvole | `policies_monthly_costs`, `policies_monthly_costs_csv` |

#### 8. Primer obračuna

> Ilustrativni primer.

| Polisa | Datum izdavanja | Vozilo | Šifra posla na taj dan | Vrsta | Premija |
|---|---|---|---|---|---|
| 1 | 15.03.2026. | A | 413111 | AUTOODGOVORNOST | 18.000,00 |
| 2 | 20.03.2026. | B | 413111 | autoodgovornost | 22.000,00 |
| 3 | 22.03.2026. | C | 413111 | Kasko osiguranje | 95.000,00 |
| 4 | 05.04.2026. | A | 413222 | KASKO | 88.000,00 |

**Rezultat:**

| Godina | Mesec | Centar | Šifra posla | Vrsta | Iznos |
|---|---|---|---|---|---|
| 2026 | 3 | 43 | 413111 | `autoodgovornost` | **40.000,00** |
| 2026 | 3 | 43 | 413111 | `Kasko osiguranje` | **95.000,00** |
| 2026 | 4 | 43 | 413222 | `kasko` | **88.000,00** |

> Polise 1 i 2 su objedinjene jer se „AUTOODGOVORNOST“ i „autoodgovornost“ svode na istu
> vrstu. Polisa 3 **ostaje zasebno** jer „Kasko osiguranje“ nije tačno jednako „kasko“ —
> zato se u izveštaju vide dve različite kasko grupe.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Zbir premija po mesecu, centru, šifri posla i vrsti |
| Format | Tabela i CSV izvoz; iznosi u RSD |
| Gde se čuva | Nigde — računa se pri otvaranju |
| Kada se ponovo računa | Pri svakom otvaranju |
| Može li korisnik da ga izmeni | Posredno — izmenom polise ili dodele šifre posla |
| Istorija | Ne postoji |

#### 10. Upotreba rezultata

| Korisnik | Šta preuzima | Odakle |
|---|---|---|
| Služba voznog parka | Zbir po mesecima | Ekran |
| Rukovodilac centra | Trošak osiguranja svog centra | Ekran, filtriran po centru |
| Finansije | CSV izvoz | `/izvestaji/policies-monthly-costs.csv` |

> **[N] Q3:** nije potvrđeno da li se CSV koristi kao osnov za knjiženje raspodele.

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Zbir svih grupa | Mora biti jednak zbiru `premium_amount` svih polisa u periodu |
| Nedostaje šifra posla | Vozilo nema dodelu pre datuma izdavanja polise — proveriti `/sifre-poslova/` |
| Dve grupe iste vrste | Tip osiguranja je upisan različito — proveriti `/polise/` |
| Polisa nije u izveštaju | Proveriti da li ima `issue_date` |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Nedovršena polisa | **Ulazi** u izveštaj |
| Polisa bez vozila | Ulazi, ali bez šifre posla i centra |
| Tip osiguranja upisan drugačije | **Zasebna grupa** — deli iznos na dve vrste |
| Polisa bez datuma izdavanja | Grupiše se bez godine i meseca |
| Izveštaj prati **datum izdavanja**, ne period važenja | Polisa za celu 2026. prikazuje se **samo u mesecu izdavanja** |

> **[P] Bitna razlika u odnosu na V-07:** ovaj izveštaj raspoređuje premiju po **datumu
> izdavanja**, a trošak po kilometru po **periodu važenja**. Zbog toga se iznosi iz
> dva ekrana ne slažu — to nije greška, nego različita pitanja.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Grupiše se po datumu izdavanja | Potvrđeno | `policy_queries.py:18-19` | — |
| Šifra posla je istorijska, na datum izdavanja | Potvrđeno | `policy_queries.py:10-13` | — |
| Normalizacija samo za tačno `kasko` i `autoodgovornost` | Potvrđeno | `policy_queries.py:26-31` | — |
| Nedovršene polise ulaze | Potvrđeno | Nema filtera potpunosti | Potvrditi da je željeno |
| Upotreba u knjiženju | **Nepotvrđeno** | — | **Q3** |

---

### V-18 — Polise pred istekom i neobnovljene polise

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Polise pred istekom i neobnovljene“ |
| Tehnički naziv | `expiring_policy_qs()`, `expired_unrenewed_policy_qs()` |
| Putanja | [`fleet/support/policy_queries.py:47`](../fleet/support/policy_queries.py#L47) |
| Adresa | `/polise/istek/` |

#### 2. Poslovna svrha

Sprečava da vozilo ostane **bez važećeg osiguranja**. Dva odvojena spiska:

| Spisak | Značenje |
|---|---|
| **Pred istekom** | Polisa ističe u narednih 30 dana, treba je obnoviti |
| **Neobnovljene** | Polisa je već istekla, a nova nije evidentirana |

#### 3. Korisnici rezultata

Služba voznog parka — operativno, svakodnevno.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona |
|---|---|
| Datum početka | `fleet_policy.start_date` |
| Datum završetka | `fleet_policy.end_date` |
| Tip osiguranja | `fleet_policy.insurance_type` |
| Da li se obnavlja | `fleet_policy.is_renewable` |
| Vozilo | `fleet_policy.vehicle_id` |
| Svih 13 polja potpunosti | vidi `Policy.incomplete_q()` |

#### 5. Poreklo podataka

Polise iz sinhronizacije faktura osiguranja, dopunjene ručno na ekranu
`/polise/nedovrseno/`.

#### 6. Tačan postupak obračuna

**Korak 0 — samo potpune polise** [P]

Oba spiska rade **isključivo nad potpunim polisama** — onima kod kojih je popunjeno
**svih 13 polja**:

> vozilo, PIB partnera, naziv partnera, broj fakture, datum izdavanja, tip osiguranja,
> broj polise, iznos premije, datum početka, datum završetka, iznos prve rate,
> iznos ostalih rata, broj rata

Nedovršena polisa **nikada** ne ulazi u upozorenja. [P]

> **[Z] Posledica:** vozilo sa nedovršenom polisom **neće** dobiti upozorenje o isteku.
> Zato postoji zaseban ekran `/polise/nedovrseno/` i upozorenje na kontrolnoj tabli.

**Korak 1 — „najnovija polisa“ po vozilu i vrsti** [P]

Za svaku polisu se traži **najkasniji datum završetka** među polisama **istog vozila
i iste vrste osiguranja**:

```
najnovija = potpune polise
            .filter(vehicle = isto vozilo, insurance_type = ista vrsta)
            .order_by("-end_date")[:1]
```

> **[P]** Grupisanje je po **tačnoj vrednosti** `insurance_type`. „KASKO“ i „Kasko“ se
> tretiraju kao **različite vrste** i ne obnavljaju jedna drugu.

**Korak 2A — polise pred istekom:**

Polisa ulazi ako **sve** važi:

| Uslov | Objašnjenje |
|---|---|
| `end_date >= danas` | Još nije istekla |
| `end_date <= danas + 30 dana` | Ističe u narednih 30 dana |
| `end_date` = najkasniji datum za to vozilo i vrstu | **Nije zamenjena novijom polisom** |
| najnovija polisa ima `is_renewable = True` | Obnavlja se |

Broj dana je podesiv parametar, podrazumevano **30**. [P]

**Korak 2B — neobnovljene polise:**

Polisa ulazi ako **sve** važi:

| Uslov | Objašnjenje |
|---|---|
| `end_date < danas` | Već je istekla |
| **ne postoji** polisa istog vozila i vrste sa **kasnijim `start_date`** | Nije obnovljena |
| najnovija polisa ima `is_renewable = True` | Trebalo je da se obnovi |

> **[P] Razlika u pravilu:** korak 2A gleda **najkasniji datum završetka**, a korak 2B
> **postojanje polise sa kasnijim datumom početka**. To su dva različita pravila, oba
> namerna: nova polisa obično počinje posle isteka stare.

**NULL vrednosti [P]:** polisa bez `start_date` ili `end_date` je **nedovršena** i
uopšte ne ulazi u obračun.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/policy_queries.py` |
| Funkcije | `complete_policy_qs()`, `expiring_policy_qs()`, `expired_unrenewed_policy_qs()` |
| Uslov potpunosti | `fleet/models.py: Policy.incomplete_q()` |
| View | `fleet/views/policy.py: ExpiringAndNotRenewedPolicyView` |
| Srodno | Kontrolna tabla flote (`fleet_snapshot`) ima **svoju**, drugačiju proveru |

> **[P] Dva različita pravila u sistemu:** kontrolna tabla
> (`fleet/support/fleet_snapshot.py:72-78`) koristi strože pravilo — traži da postoji
> polisa **iste vrste** koja počinje **najkasnije dan posle** isteka i traje duže,
> dakle **bez prekida pokrića**. Ekran `/polise/istek/` to ne proverava.
> Zato se dva spiska mogu razlikovati. Vidi pitanje **Q20**.

#### 8. Primer obračuna

> Današnji dan: **20.03.2026.**

| Polisa | Vozilo | Vrsta | Početak | Kraj | Obnavlja se | Potpuna |
|---|---|---|---|---|---|---|
| 1 | A | AUTOODGOVORNOST | 01.04.2025. | **05.04.2026.** | Da | Da |
| 2 | B | AUTOODGOVORNOST | 01.02.2025. | **31.01.2026.** | Da | Da |
| 3 | B | AUTOODGOVORNOST | 01.02.2026. | 31.01.2027. | Da | Da |
| 4 | C | KASKO | 01.03.2025. | **28.02.2026.** | Da | Da |
| 5 | D | AUTOODGOVORNOST | 01.03.2025. | 15.03.2026. | Da | **Ne** (nema broja polise) |

**Rezultat:**

| Spisak | Polise | Obrazloženje |
|---|---|---|
| **Pred istekom** | Polisa 1 | Ističe 05.04.2026., u roku od 30 dana, nema novije |
| **Neobnovljene** | Polisa 4 | Istekla 28.02.2026., nema polise sa kasnijim početkom |
| Ni u jednom | Polisa 2 | Zamenjena polisom 3 (kasniji početak) |
| Ni u jednom | Polisa 3 | Ističe tek 31.01.2027. |
| Ni u jednom | **Polisa 5** | **Nedovršena — ne ulazi ni u jedno upozorenje** |

> Vozilo D je **bez upozorenja**, iako mu polisa ističe za 5 dana. Razlog je nepotpun
> unos. To je namerno ponašanje, ali je rizik — zato kontrolna tabla ima zaseban
> pokazatelj „Polise za dopunu“.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Dva spiska polisa koje traže radnju |
| Format | Tabela na ekranu |
| Gde se čuva | Nigde |
| Kada se ponovo računa | Pri svakom otvaranju, uvek u odnosu na **današnji dan** |
| Ko postupa | Služba voznog parka |

#### 10. Upotreba rezultata

Operativni spisak za obnovu osiguranja. **Ne ulazi** ni u jedan drugi obračun.

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Vozilo nije u spisku, a trebalo bi | Proveriti da li je polisa **potpuna** (`/polise/nedovrseno/`) |
| Polisa je obnovljena, a i dalje je u spisku | Proveriti da li je **tip osiguranja** upisan isto u obe polise |
| Spisak se razlikuje od kontrolne table | Različita pravila — vidi 7. i pitanje **Q20** |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Rizik |
|---|---|---|
| **Nedovršena polisa** | Ne ulazi ni u jedno upozorenje | **Vozilo ostane bez upozorenja** |
| Tip osiguranja upisan različito | Nova polisa ne „pokriva“ staru | Lažno upozorenje |
| `is_renewable = False` | Polisa se ne prikazuje ni u jednom spisku | Namerno |
| Polisa obnovljena sa prekidom pokrića | `/polise/istek/` je **ne prikazuje**, kontrolna tabla **prikazuje** | Neusklađenost |
| Vozilo otpisano | **Nema filtera otpisa** — otpisano vozilo može biti u spisku | Nepotrebno upozorenje |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Samo potpune polise ulaze | Potvrđeno | `policy_queries.py:42-44, 50, 69` | — |
| Rok je 30 dana, podesiv | Potvrđeno | `policy_queries.py:47` | — |
| Grupisanje po tačnoj vrednosti tipa | Potvrđeno | `policy_queries.py:52-53` | — |
| Dva različita pravila obnove (ekran i kontrolna tabla) | Potvrđeno | `policy_queries.py` naspram `fleet_snapshot.py:72-78` | **Q20** |
| Otpisana vozila nisu isključena | Potvrđeno | Nema filtera | Potvrditi da li smeta |

---

### V-19 — Mesečni troškovi lizinga

> **Ovaj obračun ima tri utvrđena nedostatka.** Pre oslanjanja na njegove rezultate
> pročitati poglavlje 12 i probleme P-23, P-24 i P-25.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Mesečni troškovi lizinga“ |
| Tehnički naziv | `lease_monthly_costs_rows()` |
| Putanja | [`fleet/support/lease_queries.py:7`](../fleet/support/lease_queries.py#L7) |
| Adresa | `/izvestaji/lease-monthly-costs/` |

#### 2. Poslovna svrha

Namera je da prikaže **trošak lizinga po mesecu, centru i organizacionoj jedinici**,
uz „prateće troškove“ (servisi i gorivo) vozila te jedinice.

#### 3. Korisnici rezultata

Služba voznog parka, finansije.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Napomena |
|---|---|---|
| Datum početka ugovora | `fleet_lease.start_date` | **Određuje mesec u izveštaju** |
| Rata / iznos otplate | `fleet_lease.current_payment_amount` | |
| Vrsta lizinga | `fleet_lease.lease_type` | |
| Šifra posla (tekst) | `fleet_lease.job_code` | Tekstualno polje ugovora |
| Dodela vozila | `fleet_jobcode` | **Poslednja**, ne istorijska |
| Trošak servisa | `fleet_servicetransaction.potrazuje` | „Prateći trošak“ |
| Trošak goriva | `fleet_fuelconsumption.cost_bruto` | „Prateći trošak“ |

#### 6. Tačan postupak obračuna

**Korak 1 — grupisanje ugovora** [P]:

> grupa = (godina početka, mesec početka, centar, OJ, šifra posla, vrsta lizinga)
> **iznos lizinga = zbir `current_payment_amount` ugovora u grupi**

Centar i OJ se uzimaju iz **poslednje** dodele vozila (`-assigned_date`, bez datumskog
ograničenja). [P]

> **[P] Problem P-23:** ugovor se pojavljuje **samo u mesecu u kome je počeo**.
> Ugovor koji traje tri godine prikazan je **jednom**, a ne u svakom mesecu trajanja.

**Korak 2 — filteri** (godina, mesec, centar, OJ, vrsta) primenjuju se **u Pythonu**,
nad već učitanim skupom. [P]

**Korak 3 — „prateći troškovi“** [P]:

Za svaku grupu:

1. Pronađu se **sva vozila čija je poslednja dodela ta OJ** — ne samo vozila iz ugovora.
2. Za tu godinu i mesec saberu se:
   - servisi tih vozila (`potrazuje`);
   - gorivo tih vozila (`cost_bruto`).
3. `accompanying_total` = servisi + gorivo
4. `accompanying_per_vehicle` = ukupno / broj vozila

> **[P] Problem P-25:** prateći troškovi se odnose na **sva vozila organizacione
> jedinice**, a ne na vozila pod lizingom. Prikazani su uz red lizinga, pa korisnik
> lako zaključi da pripadaju lizing vozilima.

**Korak 4 — sortiranje:** godina, mesec, centar, OJ. [P]

**NULL vrednosti [P]:** prazan zbir servisa ili goriva se tretira kao 0;
`accompanying_per_vehicle` je **prazan** kada nema vozila u OJ.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/lease_queries.py` |
| Funkcija | `lease_monthly_costs_rows(request)` |
| View | `fleet/views/lease.py: LeaseMonthlyCostsView` |

> **[P] Problem P-24 (izvedba):** za **svaku grupu** izvršavaju se **tri odvojena upita**
> — spisak vozila OJ, zbir servisa i zbir goriva. Kod većeg broja grupa ekran postaje spor.

#### 8. Primer obračuna

> Ilustrativni primer.

Ugovori:

| Ugovor | Vozilo | Početak | Kraj | Vrsta | Rata |
|---|---|---|---|---|---|
| L1 | A | 15.01.2024. | 15.01.2027. | operativni | 50.000,00 |
| L2 | B | 01.03.2026. | 01.03.2029. | dugorocni | 65.000,00 |

**Rezultat izveštaja:**

| Godina | Mesec | OJ | Vrsta | Iznos lizinga |
|---|---|---|---|---|
| 2024 | 1 | 413111 | operativni | 50.000,00 |
| 2026 | 3 | 413111 | dugorocni | 65.000,00 |

> Ugovor L1 pojavljuje se **samo u januaru 2024**, iako traje do 2027. Za mart 2026,
> kada obe rate stvarno terete troškove, izveštaj prikazuje **samo L2**.
> To je problem **P-23**.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Zbir rata ugovora **po mesecu početka ugovora** |
| Format | Tabela |
| Gde se čuva | Nigde |
| Može li korisnik da ga izmeni | Ne |

#### 10. Upotreba rezultata

Pregled na ekranu. **Ne ulazi** u trošak po kilometru — V-07 računa lizing **potpuno
nezavisno i ispravnije**, sa deljenjem po danima preklapanja.

> **[Z] Preporuka:** za stvarni mesečni trošak lizinga pouzdaniji je obračun iz V-07
> nego ovaj izveštaj.

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Ugovor nedostaje u mesecu | Očekivano — vidi **P-23**; proveriti `/zakupi/` za datum početka |
| Prateći troškovi deluju preveliko | Odnose se na **sva** vozila OJ — vidi **P-25** |
| Zbir lizinga | Uporediti sa `/zakupi/` filtrirano po mesecu početka |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Ugovor traje više meseci** | Prikazan **samo u mesecu početka** | **P-23** |
| **Centar i OJ iz poslednje dodele** | Istorija se zanemaruje | **P-24** / P-05 |
| **Prateći troškovi cele OJ** | Ne odnose se na lizing vozila | **P-25** |
| Vozilo bez dodele | `oj_id` je prazan → nema pratećih troškova, broj vozila 0 | Vidljivo |
| Ugovor bez datuma početka | Godina i mesec prazni | Vidljivo |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Grupisanje po **datumu početka** ugovora | Potvrđeno | `lease_queries.py:13-14` | **P-23** |
| Centar i OJ iz poslednje dodele | Potvrđeno | `lease_queries.py:8-10` | **P-24** |
| Prateći troškovi obuhvataju sva vozila OJ | Potvrđeno | `lease_queries.py:49-72` | **P-25** |
| Filteri se primenjuju u Pythonu | Potvrđeno | `lease_queries.py:30-39` | — |
| Da li je izveštaj u upotrebi | **Nepotvrđeno** | — | **Q21** |

---

### V-20 — Mesečni troškovi servisa

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Mesečni troškovi servisa“ |
| Tehnički naziv | `service_monthly_costs_rows()` |
| Putanja | [`fleet/support/service_queries.py:31`](../fleet/support/service_queries.py#L31) |
| Adrese | `/reports/service-monthly-costs/`, izvoz `/reports/services/monthly.csv` |

#### 2. Poslovna svrha

Prikazuje **trošak servisa vozila po mesecu, centru i šifri posla**, za praćenje
troškova održavanja po nosiocima.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | JM |
|---|---|---|
| Datum knjiženja servisa | `fleet_servicetransaction.datum` | — |
| Iznos | `fleet_servicetransaction.potrazuje` | RSD |
| Vozilo | `fleet_servicetransaction.vehicle_id` | — |
| Dodela šifre posla | `fleet_jobcode` (na datum servisa) | — |

#### 5. Poreklo podataka

```
 dbo.fleet_servisi  ──sinhronizacija dnevno u 03:15──►  fleet_servicetransaction
                                                              │
                     fleet_jobcode: dodela važeća na datum ────┤
                                                              ▼
                              grupisanje: godina × mesec × OJ × centar → zbir
```

#### 6. Tačan postupak obračuna

**Korak 1 — izvedene kolone po stavci** [P]:

| Kolona | Kako se dobija |
|---|---|
| `service_year` | Godina iz `datum` |
| `service_month` | Mesec iz `datum` |
| `oj_code_txt` | Šifra OJ iz dodele važeće **na datum servisa** |
| `center_code_txt` | Centar iz iste dodele |

Šifra i centar se pretvaraju u tekst, a prazna vrednost u **prazan string**
(`Coalesce(Cast(...), Value(""))`) — nikada u NULL. [P]

**Korak 2 — grupisanje i zbir:**

> grupa = (godina, mesec, šifra OJ, šifra centra)
> **iznos = zbir `potrazuje`**, a ako nema nijedne stavke → **0,00**

**Korak 3 — sortiranje:** godina opadajuće, mesec opadajuće, centar rastuće,
šifra OJ rastuće. [P] Najnoviji mesec je prvi.

**Tip rezultata [P]:** `decimal(18,2)`.

**NULL vrednosti [P]:**

| Situacija | Posledica |
|---|---|
| Vozilo nema dodelu pre datuma servisa | Šifra i centar su **prazan string**, red je vidljiv |
| Stavka bez vozila | Isto — grupa sa praznom šifrom |
| Prazan `potrazuje` | Ne uvećava zbir |

> **[P] Ispravno rešeno:** za razliku od V-19, ovde se koristi **istorijska** dodela,
> i prazna vrednost se prikazuje kao prazna grupa umesto da se red izgubi.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/service_queries.py` |
| Funkcije | `_service_base_qs()`, `service_monthly_costs_rows()` |
| View | `fleet/views/services.py: ServiceMonthlyCostsView`, `service_monthly_costs_csv` |
| Dozvole | `reports_service_monthly_costs`, `reports_service_monthly_costs_csv` |

#### 8. Primer obračuna

| Servis | Datum | Vozilo | Šifra posla na taj dan | Centar | Iznos |
|---|---|---|---|---|---|
| 1 | 10.03.2026. | A | 413111 | 43 | 45.000,00 |
| 2 | 18.03.2026. | B | 413111 | 43 | 12.000,00 |
| 3 | 25.03.2026. | A | 413222 | 12 | 33.000,00 |
| 4 | 05.04.2026. | C | — (nema dodele) | — | 8.000,00 |

**Rezultat:**

| Godina | Mesec | Centar | Šifra OJ | Iznos |
|---|---|---|---|---|
| 2026 | 4 | *(prazno)* | *(prazno)* | **8.000,00** |
| 2026 | 3 | 12 | 413222 | **33.000,00** |
| 2026 | 3 | 43 | 413111 | **57.000,00** |

> Servis 3 ide na **novu** šifru jer je vozilo A promenilo dodelu pre 25.03.
> Servis 4 je vidljiv sa praznom šifrom — ne gubi se.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde |
| Upotreba | Ekran i CSV izvoz |
| Kontrola | Zbir svih grupa = zbir `potrazuje` svih servisnih knjiženja u periodu |
| Prazna grupa | Označava vozila bez dodele — proveriti `/sifre-poslova/` |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Vozilo bez dodele | Prazna šifra i centar, red **ostaje vidljiv** |
| Vozilo promenilo šifru u mesecu | Trošak se deli na dve šifre po datumu |
| Naknadna izmena dodele | **Menja i ranije mesece** — izveštaj nije zamrznut |
| Storno servisa | Zadržava izvorni znak, umanjuje zbir |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Šifra posla je istorijska, na datum servisa | Potvrđeno | `service_queries.py:10-13` |
| Prazna šifra se prikazuje kao prazan string | Potvrđeno | `service_queries.py:25-26` |
| Zbir `potrazuje`, tip `decimal(18,2)` | Potvrđeno | `service_queries.py:36-42` |
| Sortiranje: najnoviji mesec prvi | Potvrđeno | `service_queries.py:52` |

---

### Novi problemi iz ovog poglavlja

Uneti u [Registar problema](#10-poznati-problemi-i-ograničenja):

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-23** | Izveštaj mesečnih troškova lizinga prikazuje ugovor **samo u mesecu početka**, a ne u svakom mesecu trajanja. Mesečni pregled zato ne pokazuje stvarni mesečni trošak lizinga. | **Visoka** |
| **P-24** | Isti izveštaj uzima centar i OJ iz **poslednje** dodele vozila, umesto istorijske — nedosledno sa V-17 i V-20. | Srednja |
| **P-25** | „Prateći troškovi“ u istom izveštaju obuhvataju **sva vozila organizacione jedinice**, ne samo vozila pod lizingom, pa navode na pogrešan zaključak. | Srednja |

### Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q20** | Ekran „Polise pred istekom“ i kontrolna tabla flote koriste **različita pravila** za ocenu da li je polisa obnovljena (kontrolna tabla traži pokriće bez prekida, ekran ne). Koje pravilo je ispravno? |
| **Q21** | Da li se izveštaj „Mesečni troškovi lizinga“ uopšte koristi u radu? Ima tri nedostatka (P-23, P-24, P-25) i preklapa se sa obračunom lizinga u trošku po kilometru. |
| **Q22** | Da li nedovršene polise treba da ulaze u izveštaj mesečnih troškova (V-17)? Sada ulaze, dok su iz upozorenja o isteku (V-18) izuzete. |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.2. Flota — gorivo](#62-flota--obračuni-goriva) | Obračuni goriva |
| [6.3. Flota — troškovi](#63-flota--troškovi-vozila) | Trošak po kilometru i pragovi |
| [6.5. Flota — izveštaji](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji) | Kilometraža, održavanje, presek flote |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema |

---

## 6.5. Flota — kilometraža, održavanje, presek stanja i izveštaji

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](#10-poznati-problemi-i-ograničenja).

**Sadržaj:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [V-13](#v-13--kilometraža-vozila--posmatrana-vremenska-linija) | Kilometraža vozila — posmatrana vremenska linija | — |
| [V-14](#v-14--održavanje-vozila-i-servisni-interval) | Održavanje vozila i servisni interval | — |
| [V-16](#v-16--presek-stanja-flote-kontrolna-tabla) | Presek stanja flote (kontrolna tabla) | — |
| [V-22](#v-22--izveštaji-za-upravu) | Izveštaji za upravu (4 izveštaja) | **P-26** |
| [Poglavlje 6.5.5](#655-izveštaji-nad-nasleđenim-pogledima) | 11 izveštaja nad nasleđenim pogledima | **P-27** |

---

### V-13 — Kilometraža vozila — posmatrana vremenska linija

> Ovo je **najpažljivije napisan obračun u modulu Flota**. Za razliku od procene
> kilometraže (V-08), ovaj prikazuje **samo ono što je stvarno očitano** i izričito
> odbija da prikaže kilometražu kada podaci nisu pouzdani.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kilometraža“ na detalju vozila |
| Tehnički naziv | `vehicle_mileage()`, `observed_timeline()` |
| Putanja | [`fleet/support/vehicle_mileage.py:55`](../fleet/support/vehicle_mileage.py#L55) |
| Namera iz koda | *„Observed odometer readings and non-overlapping intervals near 30 days“* |

#### 2. Poslovna svrha

Prikazuje **sva očitavanja brojača** jednog vozila kroz vreme, razvrstana u intervale
od približno 30 dana, i **jasno označava mesta gde kilometraža opada** — što ukazuje na
grešku unosa ili zamenu brojača.

#### 3. Korisnici rezultata

Služba voznog parka, garaža — za kontrolu kvaliteta unosa i za proveru stvarne
pređene kilometraže.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Oznaka izvora na ekranu | Dozvoljena nula |
|---|---|---|---|
| Kilometraža NIS točenja | `fleet_transactionnis.kilometraza` (`datum_transakcije`) | „NIS — točenje“ | Ne |
| Kilometraža OMV točenja | `fleet_transactionomv.mileage` (`transaction_date`) | „OMV — točenje“ | Ne |
| **Ispravljena kilometraža OMV** | `fleet_transactionomv.corrected_mileage` | „OMV — korigovano u izvoru“ | Ne |
| Ranija evidencija goriva | `fleet_fuelconsumption.mileage` (`date`) | „Ranija evidencija goriva“ | Ne |
| Početna kilometraža zaduženja | `fleet_vehicletravelorder.start_mileage` (`created_at`) | „Nalog vozila — početak“ | **Da** |
| Krajnja kilometraža zaduženja | `fleet_vehicletravelorder.end_mileage` (`closed_at`) | „Nalog vozila — završetak“ | **Da** |

**Filteri ekrana** (`MileagePeriodForm`) [P]: „Očitavanja od“ i „Očitavanja do“.
Početak ne sme biti posle završetka.

#### 5. Poreklo podataka

```
 NIS transakcije   ──┐
 OMV transakcije   ──┤  (ispravljena kilometraža ima prednost)
                     ├──► spisak očitavanja  ──► dnevni maksimum i minimum
 Evidencija goriva ──┤     (samo za dane koje                    │
 Zaduženja vozila  ──┘      NIS/OMV ne pokrivaju)                 ▼
                                                    intervali od ~30 dana
                                                                 │
                                                    provera pada kilometraže
                                                                 ▼
                                               prikaz sa oznakom pouzdanosti
```

#### 6. Tačan postupak obračuna

##### Korak 1 — prikupljanje očitavanja [P]

Očitavanje se **odbacuje** ako:

| Uslov | Objašnjenje |
|---|---|
| Nema datuma | — |
| **Datum je u budućnosti** | `day > danas` |
| Vrednost nije broj ili nije konačna | |
| Vrednost je negativna | |
| Vrednost je **0**, a izvor ne dozvoljava nulu | Dozvoljena je samo kod zaduženja vozila |

Svako odbačeno očitavanje se broji i prikazuje korisniku kao broj izuzetih. [P]

**OMV — ispravljena kilometraža [P]:** ako je `corrected_mileage` popunjena i veća od 0,
koristi se **ona**, uz oznaku „OMV — korigovano u izvoru“. Izvorna vrednost se pamti
i prikazuje ako se razlikuje.

**Evidencija goriva — samo dopunski [P]:** `fleet_fuelconsumption` se koristi **samo za
dane koje nijedna NIS ili OMV transakcija ne pokriva**, da se isto točenje ne bi pojavilo
dvaput iz dva izvora.

##### Korak 2 — dnevni sažetak [P]

Za svaki dan sa očitavanjima:

| Veličina | Značenje |
|---|---|
| `value` | **Najveća** kilometraža tog dana — merodavna vrednost |
| `minimum` | **Najmanja** kilometraža tog dana — služi za proveru pada |
| `source` | Izvori koji su dali najveću vrednost |
| `count` | Broj očitavanja tog dana |

##### Korak 3 — intervali od približno 30 dana [P]

Postupak je lančani, bez preklapanja:

1. Početak (`anchor`) je **prvi** dan sa očitavanjem.
2. Cilj je `datum početka + 30 dana`.
3. Za kraj intervala bira se dan koji je **najbliži cilju**
   (pri jednakoj udaljenosti — raniji datum).
4. Interval se upisuje, a **kraj postaje početak sledećeg intervala**.
5. Ponavlja se do kraja spiska.

**Pređena kilometraža intervala:**

> **km = najveća vrednost poslednjeg dana − najveća vrednost prvog dana**

**ali samo ako u intervalu nema pada.** [P]

##### Korak 4 — prepoznavanje pada kilometraže [P]

Unutar intervala se za svaki dan proverava:

> **`minimum` tog dana < `value` prethodnog dana**  →  **pad**

Ako je pad pronađen bilo gde u intervalu:

> **km intervala = prazno** (`None`), a datumi padova se prikazuju kao problem

##### Korak 5 — ukupna kilometraža [P]

> **ukupno = zbir km svih intervala — ali samo ako nijedan interval nema pad**
> U suprotnom: **prazno**

> **[P] Ovo je namerno strogo pravilo.** Sistem radije **ne prikaže ništa** nego da
> prikaže zbir koji zna da je pogrešan.

##### Korak 6 — trenutno stanje [P]

Poslednji dan sa očitavanjem prikazuje se zasebno, sa oznakom `needs_check` ako je
njegov minimum manji od vrednosti prethodnog dana.

**Trenutno stanje se računa iz *svih* očitavanja**, nezavisno od izabranog perioda. [P]

##### Sortiranje i prikaz [P]

Intervali se prikazuju **obrnutim redosledom** — najnoviji prvi.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/vehicle_mileage.py` |
| Funkcije | `vehicle_mileage()`, `observed_timeline()` |
| Obrazac | `MileagePeriodForm` |
| Ekran | Od 21.09.2026. podloga kartice „Potrošnja goriva“ i obračuna RSD/km; zasebna kartica „Kilometraža“ zamenjena je potrošnjom |
| Testovi | `fleet/test_vehicle_mileage.py` — 11 testova |

#### 8. Primer obračuna

> Ilustrativni primer.

**Očitavanja:**

| Datum | Vrednost | Izvor |
|---|---|---|
| 05.01.2026. | 120.000 | OMV — točenje |
| 05.01.2026. | 120.050 | Nalog vozila — početak |
| 03.02.2026. | 121.400 | NIS — točenje |
| 06.03.2026. | 122.900 | OMV — točenje |
| 06.03.2026. | 118.000 | Nalog vozila — završetak |

**Dnevni sažetak:**

| Datum | Minimum | Vrednost (maksimum) |
|---|---|---|
| 05.01. | 120.000 | **120.050** |
| 03.02. | 121.400 | **121.400** |
| 06.03. | **118.000** | 122.900 |

**Intervali:**

| Interval | Dana | Od | Do | Pad? | km |
|---|---|---|---|---|---|
| 05.01. → 03.02. | 29 | 120.050 | 121.400 | Ne | **1.350** |
| 03.02. → 06.03. | 31 | 121.400 | 122.900 | **Da** — 06.03. minimum 118.000 < 121.400 | **prazno** |

| Rezultat | Vrednost |
|---|---|
| Ukupna kilometraža | **prazno** — jer jedan interval ima pad |
| Broj problema | 1 |
| Trenutno stanje | 122.900, uz oznaku „potrebna provera“ |

> Sistem **ne prikazuje** zbir od 2.850 km, iako bi ga mogao izračunati — jer bi taj
> broj bio neproverljiv. Korisniku se prikazuje tačan datum problema (06.03.) i on
> proverava unos zaduženja.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Spisak očitavanja, intervali od ~30 dana i ukupna kilometraža |
| Format | Tabela na ekranu |
| Gde se čuva | Nigde |
| Kada se ponovo računa | Pri svakom otvaranju |
| Može li korisnik da ga izmeni | Posredno — ispravkom kilometraže na zaduženju |

#### 10. Upotreba rezultata

Kontrola kvaliteta unosa i provera procene iz V-08. **Ne ulazi** ni u jedan drugi
obračun — V-07 koristi svoju, jednostavniju procenu.

> **[Z] Nedoslednost koja nije greška:** V-13 odbija da prikaže kilometražu kada
> primeti pad, a V-08 u istoj situaciji **tiho** bira drugi par očitavanja i ipak daje
> procenu. Dva ekrana zato mogu pokazati različitu sliku istog vozila.

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Ukupno je prazno | Postoji pad — pronaći datum u koloni problema i proveriti unos |
| Nedostaje očitavanje | Proveriti broj izuzetih očitavanja ispod tabele |
| Vrednost izgleda pogrešno | Proveriti izvor u koloni „Izvor“ — zaduženje unosi zaposleni, točenje dolazi iz izvora |
| OMV korigovana vrednost | Oznaka „korigovano u izvoru“ znači da je dobavljač sam ispravio kilometražu |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Datum u budućnosti | Očitavanje se odbacuje i broji kao izuzeto |
| Kilometraža 0 na točenju | Odbacuje se |
| Kilometraža 0 na zaduženju | **Prihvata se** — novo vozilo može imati 0 km |
| Dva očitavanja istog dana sa različitim vrednostima | Uzima se najveća; najmanja služi za proveru pada |
| Zamena brojača | Prepoznaje se kao pad, kilometraža se ne prikazuje |
| Manje od dva dana sa očitavanjem | Nema intervala, nema ukupne kilometraže |
| Isto točenje u dva izvora | Sprečeno — evidencija goriva se koristi samo za nepokrivene dane |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Budući datumi i nule se odbacuju | Potvrđeno | `vehicle_mileage.py:68-70` |
| Ispravljena OMV kilometraža ima prednost | Potvrđeno | `vehicle_mileage.py:76-80` |
| Evidencija goriva samo za nepokrivene dane | Potvrđeno | `vehicle_mileage.py:81-85` |
| Dnevni maksimum je merodavan, minimum za proveru | Potvrđeno | `vehicle_mileage.py:32-35` |
| Intervali ciljaju 30 dana, bez preklapanja | Potvrđeno | `vehicle_mileage.py:37-45` |
| Pad kilometraže poništava km intervala | Potvrđeno | `vehicle_mileage.py:42, 45` |
| Ukupno je prazno ako ijedan interval ima pad | Potvrđeno | `vehicle_mileage.py:52` |

---

### V-14 — Održavanje vozila i servisni interval

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Održavanje“ na detalju vozila |
| Tehnički naziv | `vehicle_maintenance()` |
| Putanja | [`fleet/support/vehicle_maintenance.py:25`](../fleet/support/vehicle_maintenance.py#L25) |
| Namera iz koda | *„Vehicle maintenance evidence using explicit links and document dates only“* |

#### 2. Poslovna svrha

Objedinjuje **sve dokaze o održavanju jednog vozila** — naloge garaže, zahteve nabavke,
fakture i trebovanja — i odgovara na pitanje: **kada je poslednji put rađen mali,
a kada veliki servis?**

#### 3. Korisnici rezultata

Garaža, služba voznog parka.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela | Uloga |
|---|---|---|
| Nalog garaže (prijava kvara) | `fleet_kvar` | **Nalog** |
| Predmet nabavke | `nabavka_procurement_case` | **Nalog** |
| Veza fakture i predmeta | `nabavka_invoice_link` | Dokument |
| EUF faktura | `nabavka_invoice` | Dokument |
| UF faktura | `nabavka_uf_invoice_snapshot` | Dokument |
| UF stavka | `nabavka_euf_item_snapshot` | Dokument |
| Trebovanje | `fleet_requisition` | Dokument |
| Kategorija popravke | `fleet_servicetype.name` | Razvrstavanje |

#### 6. Tačan postupak obračuna

##### Korak 1 — nalozi [P]

| Izvor | Oznaka | Vrsta intervencije |
|---|---|---|
| `fleet_kvar` | `rbz` ili `PK <id>` | `work_type` kvara |
| `nabavka_procurement_case` | `case_number` | `work_type` predmeta, a ako je prazan — `work_type` povezanog naloga garaže **istog vozila** |

Predmeti nabavke se uzimaju i kada su vezani **za vozilo**, i kada su vezani **za nalog
garaže tog vozila** bez sopstvene veze ka vozilu. [P]

##### Korak 2 — dokumenti [P]

Iz svakog predmeta se skupljaju fakture i UF stavke. Ključno pravilo:

> **Dokument izričito dodeljen drugom vozilu nije dokaz za ovo vozilo** —
> faktura sa `vehicle_id` različitim od posmatranog vozila se **preskače**.

Isto pravilo se primenjuje i naknadno: ako se faktura kasnije dodeli drugom vozilu,
ona se **uklanja** iz spiska. [P]

##### Korak 3 — razvrstavanje kategorije popravke [P]

Funkcija `service_category()` normalizuje naziv kategorije:

1. Sve u mala slova, donje crte u razmake, višestruki razmaci u jedan.
2. Uklanjaju se nastavci **„ van ims“** i **„ u ims“**.
3. Mapiranje:

| Normalizovan naziv | Vrsta |
|---|---|
| `mali servis` | `mali_servis` |
| `veliki servis` | `veliki_servis` |
| **`мали сервис`** (ćirilica) | `mali_servis` |
| **`велики сервис`** (ćirilica) | `veliki_servis` |
| `popravka` | `popravka` |
| bilo šta drugo | prazno („Nije razvrstano“) |

> **[P] Ispravno rešeno:** ovo je jedino mesto u sistemu koje prepoznaje i **ćirilične**
> nazive kategorija. Statistika centra (V-24) od 18.09.2026. takođe normalizuje nazive,
> ali samo latinične — videti [P-14 C](#10-poznati-problemi-i-ograničenja).

##### Korak 4 — sukob podataka [P]

Dokument dobija oznaku **„Proveriti kategoriju / datum“** ako:

| Uslov | Objašnjenje |
|---|---|
| Ima **više od jedne** vrste intervencije | Isti dokument je vezan za nalog malog i velikog servisa |
| Ima **različite datume** iz različitih izvora | Faktura ima jedan datum u vezi, drugi u zaglavlju |

Otkazani predmeti (`cancelled`) **ne prenose** svoju vrstu intervencije na dokument. [P]

##### Korak 5 — prenos veza sa predmeta na nalog garaže [P]

Ako je predmet nabavke vezan za nalog garaže, **svi njegovi dokumenti se pripisuju i
tom nalogu** — da bi nalog garaže prikazao kompletan trag. Otkazani predmeti se izuzimaju.

##### Korak 6 — sažetak po vrsti servisa [P]

Za `mali_servis` i `veliki_servis` posebno:

> uzimaju se dokumenti koji imaju **tačno tu vrstu**, **nemaju sukob**,
> imaju datum i taj datum **nije u budućnosti**

| Podatak | Značenje |
|---|---|
| **Poslednji** | Najnoviji takav dokument |
| **Broj** | Ukupan broj takvih dokumenata |

Dokumenti su sortirani opadajuće po datumu, pa je prvi ujedno i najnoviji. [P]

> **[P] Važno:** dokument sa sukobom kategorije **ne ulazi** u sažetak. Zato broj
> u sažetku može biti manji od broja dokumenata u spisku.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `fleet/support/vehicle_maintenance.py` |
| Funkcije | `vehicle_maintenance()`, `service_category()` |
| Ekran | Detalj vozila, kartica „Održavanje“ |
| Testovi | `fleet/test_vehicle_maintenance.py` — 12 testova |

> **[P] Šta se NE koristi:** servisni interval iz `fleet_vehicle.service_interval`
> (podrazumevano 15.000 km) **ne ulazi** u ovaj obračun. Sistem prikazuje **kada je
> servis rađen**, ali **ne računa kada sledeći dospeva**. Vidi pitanje **Q23**.

#### 8. Primer

| Dokument | Datum | Vrsta iz naloga | Sukob | U sažetku „mali servis“ |
|---|---|---|---|---|
| Faktura F-100 | 10.01.2026. | mali servis | Ne | **Da** |
| Faktura F-220 | 15.03.2026. | mali servis | Ne | **Da — poslednji** |
| Trebovanje 45/2026 | 20.03.2026. | mali servis + veliki servis | **Da** | Ne |
| Faktura F-300 | 05.05.2026. *(budući datum)* | mali servis | Ne | Ne |

**Sažetak „Mali servis“:** poslednji **15.03.2026.**, broj **2**.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde |
| Upotreba | Prikaz na detalju vozila |
| Kontrola | Otvoriti povezani nalog ili fakturu — svaki red ima vezu ka izvornom dokumentu |
| Sukob kategorije | Otvoriti dokument i proveriti kojim je nalozima vezan |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Dokument vezan za dva naloga različite vrste | Oznaka sukoba, izuzet iz sažetka |
| Dokument sa različitim datumima iz dva izvora | Oznaka sukoba |
| Otkazan predmet nabavke | Ne prenosi vrstu, ne prenosi veze |
| Faktura dodeljena drugom vozilu | Uklanja se iz spiska |
| Dokument sa budućim datumom | Vidljiv u spisku, **izuzet iz sažetka** |
| Kategorija nepoznatog naziva | „Nije razvrstano“ |
| **Servisni interval u km** | **Ne koristi se** — nema upozorenja o dospeću servisa |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Dokument drugog vozila se isključuje | Potvrđeno | `vehicle_maintenance.py:75-77, 95-97` | — |
| Ćirilični nazivi kategorija se prepoznaju | Potvrđeno | `vehicle_maintenance.py:21` | — |
| Sukob vrste ili datuma isključuje iz sažetka | Potvrđeno | `vehicle_maintenance.py:130, 140-141` | — |
| Budući datumi se izuzimaju iz sažetka | Potvrđeno | `vehicle_maintenance.py:141` | — |
| **Servisni interval se ne koristi** | Potvrđeno | Nema upotrebe `service_interval` | **Q23** |

---

### V-16 — Presek stanja flote (kontrolna tabla)

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kontrolna tabla flote“ |
| Tehnički naziv | `fleet_snapshot()` |
| Putanja | [`fleet/support/fleet_snapshot.py:13`](../fleet/support/fleet_snapshot.py#L13) |
| Adresa | `/` (početna strana) |
| Namera iz koda | *„Current fleet inventory. All center totals use the same scoped vehicle set.“* |

#### 2. Poslovna svrha

Jedinstvena početna slika: **koliko vozila imamo, gde su, koliko vrede i šta traži hitnu
radnju.**

#### 3. Korisnici rezultata

Služba voznog parka (svakodnevno), rukovodioci centara, uprava.

#### 4. Ulazni podaci

| Podatak | Tabela i kolona | Datum |
|---|---|---|
| Vozila | `fleet_vehicle` | — |
| Trenutni centar, OJ, šifra posla | `fleet_jobcode` | Dodela `<= danas` |
| Registarska oznaka i rok registracije | `fleet_trafficcard` | Izdata `<= danas` |
| Polise | `fleet_policy` | Sve |
| Otvorena zaduženja | `fleet_vehicletravelorder` | Otvoreno `<= danas`, zatvoreno prazno ili `> danas` |
| Nedovršene evidencije | `fleet_policy`, `fleet_draftservicetransaction`, `fleet_requisition`, `fleet_draftinsurance` | — |

#### 6. Tačan postupak obračuna

##### Korak 1 — obuhvat po centrima [P]

> Ako korisnik ima upisane `allowed_centers`, prikazuju se **samo vozila čiji je
> trenutni centar u toj listi**. Prazna lista znači **pun obuhvat**.

##### Korak 2 — razdvajanje otpisanih [P]

| Skup | Uslov |
|---|---|
| Prikazana vozila | `otpis = False` |
| Brojač arhiviranih | `otpis = True` — prikazuje se samo kao broj |

##### Korak 3 — statistika (ista funkcija za centar i za ukupno) [P]

| Pokazatelj | Postupak |
|---|---|
| Broj vozila | Broj redova |
| Putnička / teretna / priključna / ostalo | Po `category` |
| **Prosečna starost** | `tekuća godina − (zbir godina / broj)` — **samo za vozila sa godinom između 1886. i tekuće** |
| Poznata godišta | Broj vozila sa ispravnom godinom |
| Knjigovodstvena vrednost | Zbir `value`, **samo za vozila sa unetom vrednošću** |
| Poznate vrednosti | Broj vozila sa unetom vrednošću |
| Zadužena vozila | Broj vozila sa bar jednim otvorenim zaduženjem |
| Vozila sa važećom AO | Broj vozila sa aktivnom polisom autoodgovornosti |

> **[P] Ispravno rešeno:** prosečna starost računa **samo vozila sa ispravnom godinom**,
> i uz nju se prikazuje **koliko je godišta poznato**. Statistika centra (V-24) je
> 18.09.2026. preuzela isti način računanja — videti
> [P-14 B](#10-poznati-problemi-i-ograničenja).

##### Korak 4 — važeća polisa autoodgovornosti [P]

> polisa je aktivna ako: ima početak i kraj **i** `početak <= danas <= kraj`
> polisa je AO ako naziv tipa **sadrži** `AUTOODGOVORNOST` (velikim slovima)

> **[P]** Ovde je uslov **„sadrži“**, za razliku od mesečnih troškova polisa (V-17)
> gde je uslov **„tačno jednako“**. Zato „Autoodgovornost — obavezno“ ovde **jeste**
> prepoznata, a tamo **nije**.

##### Korak 5 — upozorenja [P]

Osam grupa, po redosledu prikaza:

| # | Grupa | Uslov | Ton |
|---|---|---|---|
| 1 | **Registracija je istekla** | `registration_valid_until < danas` | Opasnost |
| 2 | **Registracija ističe u 30 dana** | `danas <= rok <= danas + 30` | Upozorenje |
| 3 | **Nedostaje rok registracije** | Rok nije unet | Obaveštenje |
| 4 | **Nema važeće AO polise** | Vozilo nema aktivnu AO polisu | Upozorenje |
| 5 | **Polise pred istekom bez nastavka pokrića** | vidi ispod | Upozorenje |
| 6 | **Vozila bez trenutnog centra** | Nema dodele | Obaveštenje |
| 7 | **Više istovremenih zaduženja** | Vozilo ima 2+ otvorenih zaduženja | Upozorenje |
| 8 | **Evidencije za dopunu** | Brojači nedovršenih zapisa | Obaveštenje |

**Grupa 5 — pravilo nastavka pokrića [P]:**

Aktivna polisa ulazi u upozorenje ako:

| Uslov | |
|---|---|
| `end_date <= danas + 30` | Ističe uskoro |
| `is_renewable = True` | Obnavlja se |
| **ne postoji „produžetak“** | vidi ispod |

Produžetak postoji ako postoji **druga polisa istog vozila i iste vrste** (poređenje po
tipu u velikim slovima, bez suvišnih razmaka) koja:

> počinje **najkasnije dan posle** isteka posmatrane polise **i** traje **duže** od nje

> **[P]** Ovo je **strože i tačnije** pravilo od onog na ekranu `/polise/istek/` (V-18),
> koje ne proverava neprekidnost pokrića. Vidi pitanje **Q20**.

**Grupa 8 — evidencije za dopunu [P]:**

| Stavka | Uslov | Vidi je |
|---|---|---|
| Polise za dopunu | `Policy.incomplete_q()` | Svi |
| Spoljne usluge za povezivanje | `DraftServiceTransaction` — sve | **Samo korisnici bez ograničenja centara** |
| Trebovanja bez vozila | `Requisition` sa `nije_garaza = False` i bez vozila | Samo bez ograničenja |
| Naknade osiguranja za povezivanje | `DraftInsurance` — sve | Samo bez ograničenja |

Za korisnika sa ograničenim centrima broje se **samo polise njegovih vozila**; za korisnika
bez ograničenja broje se i **polise bez vozila**. [P]

##### Korak 6 — pregled po centrima [P]

Vozila se grupišu po trenutnom centru; centar bez šifre prikazuje se kao **„Bez centra“**
i sortira **poslednji**.

> **učešće centra (%) = broj vozila centra / ukupan broj vozila × 100**

#### 8. Primer

> Ilustrativni primer, korisnik bez ograničenja centara, 12 vozila.

| Pokazatelj | Vrednost |
|---|---|
| Vozila u upotrebi | 12 |
| Arhivirano (otpisano) | 3 |
| Putnička / teretna / priključna | 8 / 3 / 1 |
| Poznata godišta | 11 od 12 |
| Prosečna starost | 2026 − (2015,4) = **10,6 godina** |
| Knjigovodstvena vrednost | 14.500.000,00 RSD (poznato za 10 vozila) |
| Zadužena vozila | 4 |
| Vozila sa važećom AO | 11 |

**Upozorenja:**

| Grupa | Broj |
|---|---|
| Registracija je istekla | 1 |
| Nema važeće AO polise | 1 |
| Više istovremenih zaduženja | 1 |
| Evidencije za dopunu | 3 vrste |

> Vozilo sa nepoznatim godištem **ne obara** prosečnu starost — prikazano je da je
> poznato 11 od 12 godišta.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde |
| Kada se računa | Pri svakom otvaranju početne strane, uvek u odnosu na **današnji dan** |
| Upotreba | Svakodnevni operativni pregled |
| Kontrola | Svako upozorenje ima vezu ka konkretnom vozilu ili polisi |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Vozilo bez dodele | Grupa „Bez centra“, zasebno upozorenje |
| Korisnik sa ograničenim centrima | Vidi manje vozila i **manje vrsta** nedovršenih evidencija |
| Vozilo bez godine proizvodnje | **Ne ulazi** u prosečnu starost; prikazuje se broj poznatih godišta |
| Vozilo bez knjigovodstvene vrednosti | Ne ulazi u zbir; prikazuje se broj poznatih vrednosti |
| Polisa bez vozila | Broji se u „Polise za dopunu“ samo za korisnike bez ograničenja |
| Rok registracije nije unet | Zasebna grupa — **datum AO polise se ne prepisuje automatski kao rok registracije** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Obuhvat po `allowed_centers`; prazna lista = pun obuhvat | Potvrđeno | `fleet_snapshot.py:25-27` |
| Otpisana vozila su odvojena i samo prebrojana | Potvrđeno | `fleet_snapshot.py:28-29` |
| Prosečna starost samo za ispravna godišta | Potvrđeno | `fleet_snapshot.py:45, 51` |
| AO se prepoznaje po **sadržaju** naziva tipa | Potvrđeno | `fleet_snapshot.py:34` |
| Pravilo nastavka pokrića polise | Potvrđeno | `fleet_snapshot.py:73-78` |
| Brojač zaduženih vozila broji vozilo jednom | Potvrđeno | `fleet_snapshot.py:36, 52` |

---

### V-22 — Izveštaji za upravu

Četiri izveštaja sa zajedničkim okvirom: filteri, tabela, pokazatelji, napomene o
obuhvatu i **izvoz u Excel sa zasebnim listom „Obuhvat“**. [P]

| Izveštaj | Adresa | Dozvola |
|---|---|---|
| Kasko — vozila starija od 7 godina | `/izvestaji/osiguranje/kasko/` | `vehicle_list` |
| Auto osiguranje — vlasništvo IMS | `/izvestaji/osiguranje/ims/` | `vehicle_list` |
| Gorivo IMS — NIS i OMV | `/izvestaji/gorivo-ims/` | `fuel_transactions_list` |
| Kupljeni delovi — dobavljač | `/izvestaji/delovi-dobavljaca/` | `nabavka:euf_invoice_list` |

**Zajedničko pravilo bezbednosti [P]:** pri izvozu u Excel, tekst iz spoljnih izvora koji
počinje sa `=`, `+`, `-` ili `@` dobija apostrof ispred, da ga Excel **ne protumači kao
formulu**.

**Obuhvat po centrima** (`allowed_centers`) [P]:

> superuser → **prazan skup = bez ograničenja**
> ostali → unija `allowed_center_codes` (razdvojeno zarezom ili tačkom-zarezom)
> i `allowed_centers.center`

> **[P]** Ovo je **jedino** mesto u sistemu koje koristi **oba** mehanizma za centre.
> Vidi problem **P-19**.

---

#### V-22.1 — Kasko i auto osiguranje

##### Postupak [P]

**Korak 1 — presek na datum.** Svi podaci se biraju **na izabrani datum preseka**
(`as_of`): dodela šifre posla, saobraćajna dozvola, osnov raspolaganja i važeći lizing.

**Korak 2 — obuhvat:** samo **trenutno neotpisana** vozila.

> **[P] Izričita napomena u izveštaju:** *„ovaj pregled ne rekonstruiše raniji status
> otpisa“* — otpis se gleda **danas**, ostalo na datum preseka.

**Korak 3 — vozilo nabavljeno posle datuma preseka se preskače**
(`purchase_date > as_of`).

**Korak 4 — određivanje vlasništva:**

> **vlasništvo IMS** ako je osnov `owned`
> **ili** ako **nema** evidentiranog osnova **i nema** važećeg lizinga/najma na taj dan

| Slučaj | Oznaka na izveštaju |
|---|---|
| Osnov je `owned` | „Evidentirano vlasništvo IMS“ |
| Nema osnova ni lizinga | **„Vlasništvo IMS — podrazumevano pravilo“** |
| Ostalo | „Korišćenje po ugovoru“ |

**Korak 5 — razlike između dva izveštaja:**

| | Auto osiguranje (IMS) | Kasko |
|---|---|---|
| Vozila po ugovoru | **Isključena** (broje se zasebno) | **Uključena** |
| Filter „vlasništvo“ | Postoji (`confirmed` / `all`) | **Ne postoji** |
| Uslov starosti | Nema | **`godina preseka − godište > 7`** |
| Nepoznato godište | Ulazi | **Isključeno** |

> **[P] Tačan uslov kaska:** *„Vozilo staro tačno 7 godina nije uključeno“* —
> uslov je `age > 7`, ne `>= 7`. Izričito napisano i u napomeni izveštaja.
> **Nema uslova visoke vrednosti** — svi osnovi raspolaganja ulaze.

**Pokazatelji [P]:** broj vozila u pregledu, broj sa podrazumevanim osnovom
(`assumed`), broj sa nepoznatim godištem.

##### Primer

> Datum preseka: 31.12.2026.

| Vozilo | Godište | Starost | Osnov | Kasko | Auto osiguranje IMS |
|---|---|---|---|---|---|
| A | 2015 | 11 | `owned` | **Da** | **Da** (evidentirano) |
| B | 2019 | **7** | `owned` | **Ne** (nije > 7) | **Da** |
| C | 2010 | 16 | `contract` (lizing) | **Da** | **Ne** (isključeno) |
| D | — | — | nema osnova, nema lizinga | **Ne** (nepoznato godište) | **Da** (podrazumevano) |

##### Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Vozilo bez evidentiranog osnova | **Pretpostavlja se vlasništvo IMS** — izričito označeno |
| Vozilo bez godišta | Broji se zasebno, izuzeto iz kaska |
| Vozilo nabavljeno posle preseka | Izostavljeno |
| Vozilo otpisano danas, a bilo aktivno na datum preseka | **Izostavljeno** — izričita napomena |

---

#### V-22.2 — Gorivo IMS (NIS i OMV)

##### Postupak [P]

**Korak 1 — period:** `date_from` 00:00 do `date_to + 1 dan` 00:00 (isključivo).

**Korak 2 — istorijska šifra posla i centar:** prema dodeli važećoj **na dan transakcije**
(`TruncDate` datuma transakcije).

**Korak 3 — razvrstavanje proizvoda** (`fuel_kind`) [P]:

| Ako naziv sadrži | Vrsta |
|---|---|
| `adblue`, `ad blue` | **AdBlue** |
| `cng`, `ngv` | CNG |
| `lpg`, `tng`, `autogas` | TNG / LPG |
| `dizel`, `diesel`, `ed maxx`, `edmaxx` | Dizel |
| `benzin`, `petrol`, `bmb` | Benzin |
| bilo šta drugo | **Ostalo / nerazvrstano** |

> **[P] Redosled provere je bitan:** AdBlue se proverava **prvi**, pa proizvod
> „AdBlue dizel“ ne bi bio svrstan u dizel.

**Korak 4 — izbor vrste** (`fuel_type`) [P]:

| Izbor | Šta ulazi |
|---|---|
| **`fuel`** (podrazumevano) | Samo dizel, benzin, LPG i CNG — **bez AdBlue i bez „Ostalo“** |
| `all` | Sve |
| pojedinačna vrsta | Samo ta vrsta |

**Korak 5 — normalizacija valute** [P]: `DIN`, `DINAR` i `RSD` se svode na **`RSD`**;
prazna valuta postaje **„Nije uneta“**.

**Korak 6 — grupisanje** [P]. Šest načina: mesec, centar, šifra posla, proizvod,
mesec+centar, mesec+centar+šifra. Uz izabrane kolone, **proizvod i valuta ostaju uvek
odvojeni**:

> ključ grupe = izabrane kolone + vrsta goriva + **proizvod** + **valuta**

> **[P] Izričito objašnjenje iz koda:** *„Products and currencies always stay separate;
> quantities may use different source units.“* — količine različitih proizvoda se
> **ne sabiraju** u jedan pokazatelj.

**Korak 7 — zbirovi:** broj transakcija, zbir količine, zbir bruto iznosa i
**broj stavki bez iznosa** (`missing_amount`). Prazan iznos **nije nula** i broji se
posebno. [P]

**Iznos [P]:** NIS `total`, OMV `gross_cc` — **bruto terećenje posle popusta**.
Neto se u ovom izveštaju **ne računa**.

##### Prečišćavanje OMV transakcija [P]

OMV transakcije prolaze kroz **uklanjanje duplikata** iz V-06 — zastareli datumi fakture,
ponovljeni redovi iste transakcije i „odjeci“ računa. NIS transakcije se ne prečišćavaju,
jer za njih takav postupak ne postoji.

Primenjuje se `deduplicate_omv_transactions()`, a **ne** ceo `filter_omv_fuel_queryset()`.
Razlika je bitna: `filter_omv_fuel_queryset()` uz uklanjanje duplikata i **ograničava skup
samo na goriva**, pa bi opcije „AdBlue“, „ostalo“ i „sve“ u polju `fuel_type` prestale da
prikazuju bilo šta. Ovaj izveštaj sam razvrstava proizvode, pa mu treba samo prvi deo. [P]

> **Ispravljeno 18.09.2026.** — izveštaj je ranije čitao `TransactionOMV` **direktno**.
> U praksi obično nije smetalo, jer se `cleanup_omv_fuel_data(apply=True)` pokreće pri
> svakom uvozu (`fleet/sync/selenium.py:212`) i duplikate **fizički briše iz baze**.
> Smetalo bi kada uvoz prekine greška pre čišćenja ili kada se podaci unesu zaobilazeći
> redovan uvoz. Videti [P-26](#10-poznati-problemi-i-ograničenja).

##### Pokazatelji [P]

| Pokazatelj | Značenje |
|---|---|
| Transakcije | Broj stavki |
| Bruto · *valuta* | Zbir po svakoj valuti posebno |
| **Bez povezanog vozila** | Broj stavki kod kojih vozilo nije prepoznato |
| **Bez šifre posla** | Broj stavki bez istorijske dodele |
| **Bez iznosa** | Broj stavki sa praznim iznosom |

> **[P] Dobro rešeno:** za razliku od izveštaja goriva po šifri posla (V-21), koji
> transakcije bez vozila **tiho izostavlja**, ovaj izveštaj ih **uključuje i prebrojava**.

---

#### V-22.3 — Kupljeni delovi po dobavljaču

##### Postupak [P]

**Izbor izvora** — dva odvojena, nikad zajedno:

| Izvor | Tabela | Identifikator dobavljača | Vrednost |
|---|---|---|---|
| `uf` (ulazne fakture) | `nabavka_euf_item_snapshot` | `partner_pib` | `value` |
| `goods` (roba) | `nabavka_goods_snapshot` | `partner_code` | `debit` |

> **[P] Izričito objašnjenje:** *„Izvori se biraju odvojeno da se faktura i robni promet
> ne saberu dvaput.“*

**Filteri:** dobavljač (obavezan — bez njega je spisak **prazan**), period po
`document_date`, deo naziva artikla.

**Automatski izbor dobavljača [P]:** ako korisnik nije izabrao dobavljača, sistem
pokušava da pronađe „AutoDeki“ — ali **samo ako postoji tačno jedno poklapanje**.
Ako ih je više ili nijedno, prikazuje se napomena:

> *„AutoDeki nije nedvosmisleno identifikovan u izvoru… prazan pregled ne znači da
> nije bilo kupovine.“*

**Napomene o obuhvatu [P]:**

> *„Kupovina dela ne potvrđuje ugradnju u vozilo.“*
> *„Storna i negativne stavke nisu uklonjeni.“*

---

### 6.5.5. Izveštaji nad nasleđenim pogledima

Jedanaest izveštaja koji se **ne računaju u aplikaciji** — cela formula je u pogledu
u bazi. Aplikacija samo izvršava `SELECT` i prikazuje rezultat. [P]

| Izveštaj | Adresa | Pogled | Kolone koje se čitaju |
|---|---|---|---|
| Kasko rate | `/izvestaji/kasko_rate/` | `dbo.kasko_rate` | `SELECT *` |
| Magacin | `/izvestaji/magacin/` | `dbo.fleet_magacin_rez` | `sif_pred, god, oj, sif_mag, sif_art, kolul, koliz, popkol, vrulnab, vriznab, vrulvp, vrizvp, revalzal, razliz, mag_cena, kolpon, cenapon, naz_art, sif_vrsart, naz_vrsart` |
| Otpis | `/izvestaji/otpis/` | `dbo.fleet_otpis` | 40 kolona osnovnih sredstava |
| Trošak goriva po mesecima | `/izvestaji/tro_gorivo_mesec/` | `dbo.fleet_tro_goriva_m` | `god, mesec, kategorija, iznos` |
| Svi troškovi | `/izvestaji/troskovi_svi/` | `dbo.fleet_tro_svi` | `god, sif_vrs, datum, br_naloga, stavka, oj, knt, naz_knt, duguje, sif_pos` |
| Troškovi praćenja vozila | `/izvestaji/tro_pracenja_vozila/` | `dbo.fleet_tro_pracenje` | `PartnerPIB, PartnerIme, ID, BrojFakture, issuedate, ZaPlacanje, Konto_tro` |
| Troškovi tahografa | `/izvestaji/troskovi_tahograf/` | `dbo.fleet_tro_taho` | `SELECT *` |
| Troškovi zarada | `/izvestaji/tro_zarade/` | `dbo.tro_zarade` | `oj, god, mesec, rasif, ranaz, neto, bruto, bruto2` |
| Troškovi parkinga | `/izvestaji/tro_parking/` | `dbo.fleet_tro_parking` | `PartnerPIB, PartnerIme, ID, BrojFakture, issuedate, note, naziv, ZaPlacanje` |
| Po dobavljačima | `/izvestaji/po_dobavljacima/` | `dbo.fleet_dobavljaci` | 24 kolone knjiženja |

*(Deseti i jedanaesti izveštaj — `kasko_rate` se pojavljuje i kao Django model
`KaskoRate` sa `managed = False`.)*

#### Zajednički postupak [P]

| Element | Vrednost |
|---|---|
| Fajl sa upitima | [`fleet/support/report_queries.py`](../fleet/support/report_queries.py) |
| Izvršavanje | `fleet/support/report_helpers.py: get_data_from_secondary_db()` |
| Konekcija | **`server_db`** |
| Filteri | Dodaju se kao `WHERE` uslovi preko `report_period_filtered_query()` i `date_period_filtered_query()` |
| Ekrani | `fleet/views/reports.py` |

#### Problem P-27 — formula je izvan projekta

> **[P]** Za ovih 11 izveštaja **u repozitorijumu ne postoji nijedan podatak o tome
> kako se iznosi računaju**. Poznata su samo imena kolona koje aplikacija čita.

**Posledice [Z]:**

1. Ne može se odgovoriti na pitanje **„odakle ovaj iznos“** bez pristupa bazi.
2. Promena pogleda u bazi menja rezultat na ekranu **bez ijedne izmene u aplikaciji**
   i bez traga u istoriji verzija.
3. Dokumentacija ovih izveštaja **ne može biti završena** dok se ne dobiju definicije.

**Status [P]:** definicije (DDL) su zatražene i očekuju se.
Do tada su ovi izveštaji dokumentovani **samo do nivoa naziva kolona**.

#### Šta se ipak može reći o sadržaju [Z]

Na osnovu naziva kolona, uz napomenu da je **zaključeno, ne potvrđeno**:

| Pogled | Verovatan sadržaj |
|---|---|
| `fleet_tro_svi` | Knjiženja troškova vozila po nalogu, kontu i šifri posla (`duguje`) |
| `fleet_tro_goriva_m` | Zbir troška goriva po godini, mesecu i kategoriji |
| `fleet_tro_pracenje` | Fakture za GPS praćenje vozila (`ZaPlacanje`) |
| `fleet_tro_taho` | Fakture za tahografe |
| `fleet_tro_parking` | Fakture za parking, sa nazivom i napomenom |
| `tro_zarade` | Zarade po OJ i mesecu: neto, bruto, bruto 2 |
| `fleet_dobavljaci` | Knjiženja po dobavljačima — ista struktura kao `nalog_z` |
| `fleet_magacin_rez` | Stanje i promet magacina: ulaz, izlaz, nabavne i veleprodajne vrednosti |
| `fleet_otpis` | Osnovna sredstva: nabavna vrednost, osnovica, otpis, amortizacione stope |

> **Ne oslanjati se na ovu tabelu za poslovne odluke** dok se ne dobiju definicije pogleda.

---

### Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-26** | ~~Izveštaj „Gorivo IMS“ za upravu čita OMV transakcije **bez prečišćavanja duplikata pri čitanju**.~~ **Rešeno 18.09.2026.** | Srednja |
| **P-46** | Ključ za prepoznavanje duplikata OMV transakcija **ne podnosi prazna polja**, pa zapis bez vaučera ili količine tiho nestaje sa **svih** ekrana goriva. Otkriveno pri rešavanju P-26. **Rešeno 18.09.2026.** | **Visoka** |
| **P-47** | Isti ključ **ne obuhvata iznos ni valutu**, pa se dva zapisa koja se razlikuju samo po iznosu spajaju u jedan. Nije potvrđeno da takvi parovi postoje u stvarnim podacima. | Srednja |
| **P-27** | Za 11 izveštaja nad nasleđenim pogledima **formula nije poznata** — nalazi se isključivo u bazi. Rezultat se može promeniti bez ijedne izmene u aplikaciji. | Srednja |

### Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q23** | Vozilo ima polje „Servisni interval (km)“ sa podrazumevanih 15.000, ali se **nigde ne koristi**. Da li je predviđeno upozorenje o dospelom servisu (kilometraža od poslednjeg servisa ≥ interval)? |
| **Q24** | Izveštaj za upravu prepoznaje AO polisu po **sadržaju** naziva tipa, a mesečni troškovi polisa po **tačnoj vrednosti**. Da li tipove osiguranja treba svesti na šifarnik umesto slobodnog teksta? |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.2. Flota — gorivo](#62-flota--obračuni-goriva) | Obračuni goriva |
| [6.3. Flota — troškovi](#63-flota--troškovi-vozila) | Trošak po kilometru |
| [6.4. Flota — polise i lizing](#64-flota--polise-lizing-i-servisi) | Mesečni troškovi |
| [4. Baza podataka](#412-nasleđeni-objekti-baze-dbo) | Nasleđeni pogledi |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema |

---

## 6.6. Kadrovi — obračuni

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](#10-poznati-problemi-i-ograničenja).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [K-01](#k-01--dnevni-sati-rada-iz-evidencije-prolazaka) | Dnevni sati rada iz evidencije prolazaka | **P-28** |
| [K-02](#k-02--dnevni-sati-iz-obračunatih-parova-drugi-postupak) | Dnevni sati iz obračunatih parova (drugi postupak) | **P-28** |
| [K-03](#k-03--problemi-u-parovima-prolazaka) | Problemi u parovima prolazaka | — |
| [K-04](#k-04-i-k-05--sati-radne-liste) | Ukupni sati po redu radne liste | — |
| [K-05](#k-04-i-k-05--sati-radne-liste) | Ukupni sati radne liste | — |
| [K-06](#k-06--godišnji-odmori--dodele-i-rešenja) | Godišnji odmori — dodele i rešenja | — |
| [K-07](#k-07--bolovanja--uvoz-rfzo-i-povezivanje) | Bolovanja — uvoz RFZO i povezivanje | **P-29** |
| [K-08](#k-08--ocenjivanje-zaposlenih--stimulacija-i-lični-koeficijent) | **Ocenjivanje — stimulacija i lični koeficijent** | — |
| [K-09](#k-09--tok-saglasnosti-na-ocenu) | Tok saglasnosti na ocenu | — |
| [K-10](#k-10--rešenja-zaposlenih--izrada-teksta-dokumenta) | **Rešenja zaposlenih — izrada teksta dokumenta** | — |
| [K-11](#k-11--predlog-popunjavanja-radne-liste) | **Predlog popunjavanja radne liste („meko popunjavanje“)** | — |

---

### Zajednička osnova: odakle dolaze kadrovski podaci

```
┌─ INFORMATIKA23.ID ──────────────┐   sistem kontrole pristupa (čitači kartica)
│  Radnici                        │
│  C_Prolasci_Radnika             │ ← pojedinačni prolasci (K-01)
│  C_Tasteri                      │ ← šifarnik tastera
│  c_parovi_radnika_detalji       │ ← već uparena trajanja (K-02)
└─────────────────────────────────┘
┌─ SERFIN.bazaldims ──────────────┐
│  radnik                         │ ← OJ i ime uz parove (K-02)
└─────────────────────────────────┘
┌─ PUTGEO-SERVER.BazaLDIMS ───────┐   obračun zarada
│  Godmor                         │ ← dodele godišnjeg odmora (K-06)
│  GodmorKor                      │ ← rešenja o korišćenju (K-06)
└─────────────────────────────────┘
┌─ IMS_ERP ───────────────────────┐
│  dbo.hr_employee                │ ← zaposleni (dnevna sinhronizacija u 01:10)
└─────────────────────────────────┘
        RFZO Excel izvoz  ─────────► bolovanja (ručni uvoz, K-07)
```

> **[P]** Kadrovski moduli zavise od **tri udaljena servera**. Ako bilo koji nije
> dostupan, radna lista se otvara, ali **bez podataka o prolascima**, uz poruku
> *„Izvor prolazaka trenutno nije dostupan. Bolovanja i putni nalozi prikazani su
> iz aplikacije.“*

---

### K-01 — Dnevni sati rada iz evidencije prolazaka

> **Ovo je obračun koji zaposleni vidi na svojoj radnoj listi.**

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Sati“ i „Decimalno“ u koloni evidencije prolazaka |
| Tehnički naziv | `calculate_daily_hours_from_clock_events()` |
| Putanja | [`hr/services/attendance.py:313`](../hr/services/attendance.py#L313) |
| Ekran | `/hr/radna-lista/` |

#### 2. Poslovna svrha

Iz pojedinačnih prolazaka kroz čitač kartica računa **koliko je sati zaposleni proveo
na poslu svakog dana**, kao **predlog i kontrolu** pri popunjavanju radne liste.

> **[P] Važno:** ovo **nije** automatsko popunjavanje radne liste. Sati iz prolazaka
> se prikazuju **uporedo** sa radnom listom, ali se **ne prepisuju** u nju — zaposleni
> sam unosi sate po šiframa posla.

#### 3. Korisnici rezultata

Zaposleni (svoja radna lista), kadrovska služba, superuser (tuđe radne liste).

#### 4. Ulazni podaci

| Poslovni naziv | Izvor | Kolona | Obavezno |
|---|---|---|---|
| Vreme prolaska | `INFORMATIKA23.ID.dbo.C_Prolasci_Radnika` | `Vreme` | Da |
| Taster | ista tabela | — | Da |
| Šifra radnika | `INFORMATIKA23.ID.dbo.Radnici` | `Sifra` | Da |
| Ime i prezime | ista tabela | — | Ne |

#### 5. Poreklo podataka

Zaposleni prislanja karticu na čitač i bira taster. Zapis nastaje u sistemu kontrole
pristupa, a IMS ERP ga **samo čita** preko povezanog servera. [P]

#### 6. Tačan postupak obračuna

##### Šifarnik tastera [P]

| Taster | Značenje | Uloga u obračunu |
|---|---|---|
| **1** | Ulazak 1 | **Ulaz** |
| **3** | Ulazak 2 | **Ulaz** |
| **5** | Ulazak 3 | **Ulaz** |
| **7** | Ulazak u posebnu smenu | **Ulaz** |
| **2** | Izlazak radnika | **Izlaz** |
| **4** | Službeni izlazak | **Izlaz, po posebnom pravilu** |
| **11** | Poništavanje prolaska radnika | **Za pregled** — ne ulazi u obračun |
| **12** | Pauza | **Za pregled** — ne ulazi u obračun |
| ostalo | — | **Nepoznat taster** — prijavljuje se kao problem |

Opisi tastera se mogu dopuniti iz tabele `C_Tasteri`; podrazumevani spisak je u kodu. [P]

##### Uparivanje [P]

Prolasci se grupišu **po danu** i sortiraju po vremenu. Zatim se redom obrađuju:

```
 taster = ULAZ   ──► ako već postoji otvoren ulaz → PROBLEM „Dupli ulaz bez izlaza“
                     inače → zapamti ulaz

 taster = IZLAZ  ──► ako nema otvorenog ulaza → PROBLEM „… bez prethodnog ulaza“
                     ako je izlaz pre ili u trenutku ulaza → PROBLEM „… nije posle ulaza“
                     inače → saberi trajanje, zatvori par

 taster = 11/12  ──► PROBLEM „… nije automatski uključen u obračun“

 ostalo          ──► PROBLEM „Nepoznat taster“

 na kraju dana, ostao otvoren ulaz ──► PROBLEM „… bez izlaza“
```

##### Službeni izlazak — posebno pravilo [P]

> Kod tastera **4 (Službeni izlazak)** vreme izlaska se **ne uzima stvarno**, nego se
> **postavlja na 16:00** istog dana.

Uz taj par se upisuje napomena *„Sluzbeni izlazak - racunato do 16:00.“*, koja se
**ne broji kao problem** (`is_problem = False`). [P]

> **[Z] Poslovno objašnjenje:** zaposleni koji izađe službeno ne vraća se da odjavi
> izlazak, pa se radni dan računa do kraja radnog vremena.
>
> **[P] Vreme 16:00 je upisano u kod** (`DEFAULT_OFFICIAL_EXIT_END_TIME`) i nije podesivo
> kroz interfejs.

##### Zbir [P]

> **trajanje para = ceo broj minuta između ulaza i izlaza** (sekunde se odbacuju)
> **ukupno dnevno = zbir trajanja svih parova**

| Prikaz | Način |
|---|---|
| Sati i minuti | `ukupno // 60` : `ukupno % 60`, dvocifreno |
| Decimalno | `ukupno / 60`, zaokruženo na **2 decimale** |

##### Status dana na ekranu [P]

| Uslov (redom) | Status |
|---|---|
| Dan ima bar jedan **problem** | **„Problem“** |
| Dan ima bar jedan zatvoren par | **„OK“** |
| Zaposleni je tog dana na **bolovanju** i nema problema ni parova | **„Bolovanje“** |
| Izvor prolazaka nije dostupan | **„Nije učitano“** |
| Inače | **„Nema prolaza“** |

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `hr/services/attendance.py` |
| Funkcije | `get_clock_events()`, `calculate_daily_hours_from_clock_events()` |
| Ekran | `hr/views.py: MyWorkTimeSheetView.build_clock_attendance_context()` |
| Šablon | `hr/templates/hr/work_time_sheet.html` |
| Zaštita od pada izvora | `except DatabaseError` — ekran se otvara i bez prolazaka |

**Dodatno na istom ekranu [P]:** uz svaki dan se prikazuju i **putni nalozi**
(`_travel_orders_by_day`) i **bolovanja** (`sick_leaves_by_day`), koji dolaze iz
same aplikacije i **ne zavise** od udaljenog servera.

Putni nalog se prikazuje na **svakom danu svog trajanja**:
od `travel_date` do `travel_date + broj dana − 1`; stornirani nalozi se izuzimaju. [P]

#### 8. Primer obračuna

> Ilustrativni primer, jedan dan.

| Vreme | Taster | Značenje | Obrada |
|---|---|---|---|
| 07:32 | 1 | Ulazak 1 | Otvoren ulaz |
| 11:05 | 12 | Pauza | **Problem** — ne ulazi u obračun |
| 11:40 | 2 | Izlazak radnika | Par 07:32–11:40 = **248 min** |
| 12:15 | 3 | Ulazak 2 | Otvoren ulaz |
| 14:50 | 4 | **Službeni izlazak** | Par 12:15–**16:00** = **225 min** |

| Rezultat | Vrednost |
|---|---|
| Ukupno minuta | 248 + 225 = **473** |
| Sati i minuti | **7:53** |
| Decimalno | 473 / 60 = **7,88** |
| Broj parova | 2 |
| Broj problema | **1** (pauza) |
| Status dana | **„Problem“** |

> Uočite: službeni izlazak u 14:50 računa se **do 16:00**, što daje 70 minuta više nego
> stvarno provedeno vreme. To je pravilo, ne greška.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Predlog i kontrolu sati po danu |
| Format | `H:MM` i decimalno sa 2 decimale |
| Gde se čuva | **Nigde** — čita se iz izvora pri svakom otvaranju |
| Može li korisnik da ga izmeni | **Ne** — ispravka se radi u sistemu kontrole pristupa |
| Istorija | Ne postoji |

#### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Radna lista | Prikaz uz svaki dan, kao kontrola |
| Kadrovska služba | Provera prisustva |

> **[P]** Rezultat **ne ulazi** u radnu listu automatski i **ne prenosi se** u obračun
> zarada. Zaposleni sate unosi ručno, po šiframa posla.

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Sati ne odgovaraju | Otvoriti spisak napomena uz dan — vidi se svaki prolazak i razlog |
| „Nema prolaza“ a bio je na poslu | Zaposleni nije prislonio karticu ili je izabrao pogrešan taster |
| Dan ima problem | Napomena navodi tačno vreme i opis |
| Ceo mesec prikazuje „—“ | Izvor prolazaka nije dostupan — nije greška podataka |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Posledica |
|---|---|---|
| Zaboravljen izlazak | Problem „bez izlaza“, **par se ne računa** | Sati manji od stvarnih |
| Zaboravljen ulazak | Problem „bez prethodnog ulaza“, par se ne računa | Sati manji od stvarnih |
| Dva ulaza zaredom | Prvi se zadržava, drugi je problem | Moguće veće trajanje |
| **Prolazak preko ponoći** | Grupisanje je **po danu prolaska** — ulaz u 22:00 i izlaz u 06:00 **ne čine par** | **P-28** |
| Službeni izlazak posle 16:00 | Izlaz se postavlja na 16:00 → **izlaz pre ulaza** → problem | Par se gubi |
| Pauza (taster 12) | Uvek problem, čak i kada je pravilno korišćena | Svaki dan sa pauzom ima status „Problem“ |
| Nepoznat taster | Problem | Vidljivo |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Ulazni tasteri su 1, 3, 5, 7 | Potvrđeno | `attendance.py:89` | — |
| Izlazni taster je 2, službeni 4 | Potvrđeno | `attendance.py:90-91` | — |
| Službeni izlazak se računa do 16:00 | Potvrđeno | `attendance.py:93, 391` | Potvrditi poslovno pravilo |
| Tasteri 11 i 12 se prijavljuju kao problem | Potvrđeno | `attendance.py:423-434` | **Q25** |
| Trajanje u celim minutima | Potvrđeno | `attendance.py:407` | — |
| Sati se ne prepisuju u radnu listu | Potvrđeno | Nema takvog upisa | — |
| **Prolasci preko ponoći** | **Potvrđeno — problem** | `attendance.py:337, 342` | **P-28** |

---

### K-02 — Dnevni sati iz obračunatih parova (drugi postupak)

> **U sistemu postoje DVA različita obračuna sati.** Ovaj se **ne prikazuje zaposlenom**
> — koristi ga samo upravljačka komanda. Daje **drugačiji rezultat** od K-01.

#### 1. Naziv

| | |
|---|---|
| Tehnički naziv | `get_daily_work_hours()`, `get_month_daily_work_hours()` |
| Putanja | [`hr/services/attendance.py:474`](../hr/services/attendance.py#L474) |
| Gde se koristi | Upravljačka komanda `manage.py hr_attendance_summary` |

#### 2. Poslovna svrha

Čita **već uparena trajanja** iz sistema kontrole pristupa
(`c_parovi_radnika_detalji`), umesto da sam upa­ruje prolaske.

#### 6. Tačan postupak obračuna

Sve se izvršava **jednim SQL upitom** nad povezanim serverima. [P]

**Izvor:**

> `INFORMATIKA23.ID.dbo.c_parovi_radnika_detalji`
> spojeno sa `SERFIN.bazaldims.dbo.radnik` preko `Radnik = rasif`

**Isključenje neispravnih zapisa [P]:**

> uzimaju se samo redovi gde je `Trajanje_1` prazno **ili manje od 20**

> **[Z]** Prag od 20 sati služi da se izuzmu zapisi sa besmisleno dugim trajanjem
> (npr. zaboravljena odjava). Prag je upisan u upit i nije podesiv.

**Formula dnevnog zbira [P]:**

> **ukupno sati = `Trajanje_1` + `Trajanje_2` + `Trajanje_3`
> + `Trajanje_Posebna` + `Trajanje_Sluzbeno`
> + min(`trajanje_pauza`, 0,5)**

Prazne vrednosti se računaju kao **0** (`COALESCE`).

> **[P] Pauza se priznaje najviše 30 minuta.** Ako je pauza trajala duže, u radno vreme
> ulazi samo 0,5 sata. Ako je kraća, ulazi u punom trajanju.

**Grupisanje:** po danu, šifri radnika, organizacionoj jedinici i imenu. [P]

**Prikaz [P]:**

| Kolona | Formula |
|---|---|
| Sati | `FLOOR(ukupno)` |
| Minuti | `ROUND((ukupno − FLOOR(ukupno)) × 60, 0)` |
| Ukupno | `CAST(ukupno AS decimal(10,2))` |

**Čišćenje imena [P]:** znakovi **Ć** (`NCHAR(262)`) i **Č** (`NCHAR(268)`) zamenjuju se
sa **C** već u upitu.

#### 8. Primer

| Kolona izvora | Vrednost |
|---|---|
| `Trajanje_1` | 3,50 |
| `Trajanje_2` | 4,00 |
| `Trajanje_Sluzbeno` | 0,00 |
| `trajanje_pauza` | **0,75** |

> ukupno = 3,50 + 4,00 + 0,00 + **0,50** (pauza ograničena) = **8,00 sati**
> Prikaz: sati **8**, minuti **0**, ukupno **8,00**

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| `Trajanje_1 >= 20` | **Ceo red se izuzima** |
| Pauza duža od 30 minuta | Priznaje se samo 0,5 sata |
| Radnik nije u `SERFIN.bazaldims.dbo.radnik` | **Red se gubi** — spajanje je `INNER JOIN` |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Formula zbira pet trajanja plus ograničena pauza | Potvrđeno | `attendance.py:497-506` | — |
| Prag isključenja `Trajanje_1 < 20` | Potvrđeno | `attendance.py:512` | Potvrditi značenje praga |
| Pauza ograničena na 0,5 sata | Potvrđeno | `attendance.py:502-505` | — |
| Radnik bez zapisa u `radnik` se gubi | Potvrđeno | `INNER JOIN`, linija 508 | — |
| **Dva različita obračuna sati u sistemu** | **Potvrđeno — problem** | K-01 naspram K-02 | **P-28** |

---

### K-03 — Problemi u parovima prolazaka

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Napomene uz dan, status „Problem“ |
| Tehnički naziv | `ClockPairIssue` |
| Putanja | [`hr/services/attendance.py:68`](../hr/services/attendance.py#L68) |

#### 2. Poslovna svrha

Umesto da tiho preskoči neupariv prolazak, sistem **imenuje tačan problem** i prikazuje
ga uz dan, da bi zaposleni znao šta da ispravi.

#### 6. Spisak prepoznatih problema [P]

| Poruka | Kada nastaje | Broji se kao problem |
|---|---|---|
| „Dupli ulaz bez izlaza izmedju (*taster*).“ | Dva ulaza bez izlaza između | Da |
| „*Taster* bez prethodnog ulaza.“ | Izlaz bez otvorenog ulaza | Da |
| „*Taster* nije posle ulaza.“ | Izlaz pre ili u trenutku ulaza | Da |
| „*Taster* bez izlaza.“ | Ulaz ostao otvoren do kraja dana | Da |
| „*Taster* nije automatski ukljucen u obracun.“ | Tasteri 11 i 12 | Da |
| „Nepoznat taster: *N*.“ | Taster izvan šifarnika | Da |
| **„Sluzbeni izlazak - racunato do 16:00.“** | Taster 4 uspešno uparen | **Ne** — obaveštenje |

Svaki zapis nosi datum, šifru zaposlenog, **tačno vreme** i taster. [P]

#### 9–11. Rezultat i upotreba

Prikazuje se uz dan u obliku `HH:MM - poruka`. U zaglavlju meseca prikazuje se
**ukupan broj problema** (bez obaveštenja o službenom izlasku). [P]

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Sedam vrsta poruka | Potvrđeno | `attendance.py:357-458` |
| Službeni izlazak nije problem | Potvrđeno | `attendance.py:418` |
| Brojač problema izuzima obaveštenja | Potvrđeno | `hr/views.py:561` |

---

### K-04 i K-05 — Sati radne liste

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Ukupno“ po redu i „Ukupno“ radne liste |
| Tehnički naziv | `WorkTimeSheetLine.total_hours`, `WorkTimeSheet.total_hours` |
| Putanja | [`hr/models.py:255`](../hr/models.py#L255), [`hr/models.py:189`](../hr/models.py#L189) |

#### 2. Poslovna svrha

Radna lista je mesečna evidencija u kojoj zaposleni raspoređuje svoje sate **po šiframa
posla**. Zbir po redu pokazuje koliko je sati utrošeno na jednu šifru, a zbir liste
ukupan mesečni fond.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Ograničenje | Ko unosi |
|---|---|---|---|---|
| Šifra posla | Šifra posla | `hr_worktimesheetline.organizational_unit_id` | — | **Zaposleni** |
| Sati po danu | Kolone 1–31 | `day_1` … `day_31` | **ceo broj 0–24** | **Zaposleni** |
| Vrsta rada / odsustva | Napomena | `work_category_id` | Samo aktivne i „zaposleni bira“ | Zaposleni |
| Topli obrok — dana | Topli obrok | `hr_worktimesheet.meal_days` | 0–31 | Zaposleni |
| Topli obrok — šifra posla | Topli obrok, šifra | `meal_organizational_unit_id` | — | Zaposleni |
| Terenski dodatak — dana | Terenski dodatak | `field_allowance_days` | 0–31 | Zaposleni |

> **[P] Sati su celobrojni.** Polje je `PositiveSmallIntegerField` sa najvećom vrednošću
> **24** — polovine sata se **ne mogu uneti**.

#### 6. Tačan postupak obračuna

> **ukupno po redu = `day_1` + `day_2` + … + `day_31`**, gde se prazno računa kao **0**
> **ukupno radne liste = zbir „ukupno“ svih redova**

**Čišćenje dana izvan meseca [P]:** pri čuvanju se svim danima **iznad broja dana u
mesecu** postavlja prazno. Februar tako ne može zadržati sate u poljima 30. i 31.

**Broj redova [P]:** radna lista se pri otvaranju automatski dopunjava do
`WORK_TIME_SHEET_LINE_COUNT` redova — prazni redovi postoje unapred.

#### 6.1. Status radne liste [P]

| Status | Značenje | Kako se postiže |
|---|---|---|
| `draft` — „Popunjava se“ | Radna verzija | Podrazumevano |
| `submitted` — „Predato“ | Zaposleni je predao | Dugme „Predaj i štampaj“ |
| `approved` — „Odobreno“ | Odobreno | **[N] Nije pronađena radnja koja postavlja ovaj status** |

> **[N] Q26:** status „Odobreno“ postoji u modelu, ali u kodu **nije pronađena** radnja
> koja ga postavlja. Da li je odobravanje predviđeno, a nije izvedeno?

#### 6.2. Ko čiju listu vidi [P]

| Korisnik | Pristup |
|---|---|
| Zaposleni | **Samo svoju** radnu listu |
| Superuser | Radnu listu bilo kog zaposlenog (`/hr/zaposleni/<id>/radna-lista/`) |
| Korisnik bez povezanog zaposlenog | **Zabranjen pristup** — *„Korisnicki nalog nije povezan sa zaposlenim.“* |

> **[P]** Tuđu radnu listu može otvoriti **isključivo superuser** — ne postoji uloga
> koja to dozvoljava kadrovskoj službi.

#### 8. Primer

| Red | Šifra posla | 1. | 2. | 3. | … | Ukupno |
|---|---|---|---|---|---|---|
| 1 | 413111 | 8 | 8 | — | … | **160** |
| 2 | 413222 | — | — | 8 | … | **16** |
| 3 | *(prazan)* | — | — | — | … | **0** |
| | | | | | **Ukupno liste** | **176** |

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | **Sati se čuvaju** u `hr_worktimesheetline`; zbirovi se računaju pri prikazu |
| Ko menja | Zaposleni, dok je status `draft` |
| Trag | `created_by`, `updated_by`, `created_at`, `updated_at` |
| Kontrola | Uporediti zbir liste sa satima iz prolazaka (K-01) prikazanim na istom ekranu |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Sati uneti u dan koji ne postoji u mesecu | Brišu se pri čuvanju |
| Prazno polje | Računa se kao 0 |
| Više od 24 sata u danu | Obrazac odbija unos |
| Polovina sata | **Nije moguće uneti** |
| Predata lista | Status se menja, ali **izmena i dalje ostaje moguća** [Z] |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Sati su celi brojevi 0–24 | Potvrđeno | `hr/models.py:213-243` | — |
| Zbir po redu i po listi | Potvrđeno | `hr/models.py:189-191, 255-260` | — |
| Dani izvan meseca se brišu | Potvrđeno | `hr/views.py:653-654` | — |
| Tuđu listu otvara samo superuser | Potvrđeno | `hr/views.py:433-434` | — |
| **Status „Odobreno“ se nigde ne postavlja** | **Nepotvrđeno** | Nema takve radnje | **Q26** |

---

### K-06 — Godišnji odmori — dodele i rešenja

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Godišnji odmori“ |
| Tehnički naziv | `sync_annual_leave()` |
| Putanja | [`hr/services/annual_leave.py:135`](../hr/services/annual_leave.py#L135) |
| Adrese | `/hr/godisnji-odmori/`, sinhronizacija `/hr/godisnji-odmori/sinhronizacija/` |

#### 2. Poslovna svrha

Preuzima iz obračuna zarada **koliko je dana odmora zaposlenom dodeljeno** i
**koja rešenja o korišćenju su izdata**, da bi kadrovska služba imala pregled na
jednom mestu.

> **[P] Izričita namera iz koda:** *„Read-only import… without payroll calculations“* —
> sistem **ne računa** pravo na odmor, samo preuzima ono što je obračun zarada utvrdio.

#### 4. Ulazni podaci

| Izvor | Tabela | Kolone |
|---|---|---|
| **Dodele** | `[putgeo-server].[BazaLDIMS].[dbo].[Godmor]` | `sif_pred, god, rasif, dana1…dana6, dana, ostalo, ranaz` |
| **Rešenja** | `[putgeo-server].[BazaLDIMS].[dbo].[GodmorKor]` | `sif_pred, god, rasif, od_datuma, do_datuma, dana, komentar` |

Obuhvat: **firma 1**, opciono jedna godina. [P]

#### 6. Tačan postupak obračuna

**Korak 1 — zaključavanje** [P]: pre čitanja izvora uzima se SQL zaključavanje
`sp_getapplock` na resursu `hr:annual_leave_sync`, vezano za **transakciju**.
Ako je već zauzeto: *„Sinhronizacija godišnjih odmora je već u toku.“*

> Zaključavanje pokriva **sve ulazne tačke** — ekran, komandu i zadatak.

**Korak 2 — provera ispravnosti (sve pre bilo kakvog upisa)** [P]:

| Provera | Poruka pri neuspehu |
|---|---|
| Firma mora biti 1 | „Godmor, red *N*: neispravna ili duplirana dodela.“ |
| Godina između 1900. i 2100. | isto |
| Šifra zaposlenog ≥ 0 | isto |
| Broj dana ≥ 0 | isto |
| Ime do 255 znakova | isto |
| Ključ se ne sme ponavljati | isto |
| Rešenje: početak ≤ kraj | „GodmorKor, red *N*: neispravno ili duplirano rešenje.“ |
| Komentar do 255 znakova | isto |

> **[P] Sve ili ništa:** jedan neispravan red **zaustavlja ceo prenos** uz poruku
> *„Ništa nije sinhronizovano.“*

**Korak 3 — ključ zapisa** [P]:

| Zapis | Ključ |
|---|---|
| Dodela | (firma, godina, šifra zaposlenog) |
| Rešenje | (firma, godina, šifra zaposlenog, **`source_start_key`**) |

`source_start_key` je početni datum i vreme iz izvora, zapisan kao tekst sa
**mikrosekundama** (`isoformat(timespec='microseconds')`).

> **[P] Zašto tako:** izvorni ključ nosi vremensku komponentu. Da se rešenja ne bi
> duplirala ili gubila zbog prikaza i vremenskih zona, čuva se **tačan tekst**.
> Zapis sa vremenskom zonom se **odbija**.

**Korak 4 — povezivanje sa zaposlenim** [P]:

> šifra zaposlenog **0** znači „nema identiteta“ u nasleđenom izvoru — takav zapis se
> **čuva, ali ne povezuje** sa zaposlenim

Nepovezani zapisi se broje u `unlinked`.

**Korak 5 — upis i povlačenje** [P]:

| Situacija | Postupak | Brojač |
|---|---|---|
| Ključ ne postoji lokalno | Novi zapis | `created` |
| Ključ postoji, sadržaj promenjen | Ažuriranje | `updated` |
| Ključ postoji, sadržaj isti | Ništa | `unchanged` |
| **Ključ više nije u izvoru** | **`source_present = False`** — zapis se **ne briše** | `withdrawn` |

> **[P] Izričito objašnjenje iz koda:** *„A changed source PK is a new decision;
> retain its previous local record as withdrawn.“* — izmenjeno rešenje u izvoru dobija
> novi ključ, a staro ostaje kao povučeno.

**Korak 6 — istorija:** svaki prenos upisuje `AnnualLeaveSync` sa brojačima. [P]

**Probni prolaz [P]:** `dry_run=True` izvrši ceo postupak pa **poništi transakciju** —
brojači se prikazuju, podaci se ne menjaju.

#### 8. Primer

> Sinhronizacija za 2026.

| Izvor | Ključ | Ishod |
|---|---|---|
| Godmor | (1, 2026, 1234) — 20 dana | **Novo** |
| Godmor | (1, 2026, 1235) — 25 dana, bilo 24 | **Ažurirano** |
| Godmor | (1, 2026, **0**) — 18 dana | Novo, **nepovezano** |
| GodmorKor | (1, 2026, 1234, `2026-07-01T00:00:00.000000`) | **Novo** |
| *lokalno postoji* | (1, 2026, 1236) — nema ga više u izvoru | **Povučeno** (`source_present = False`) |

**Brojači:** dodele — novo 2, ažurirano 1, nepovezano 1, povučeno 1.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `hr_annualleaveallowance`, `hr_annualleavedecision` |
| Kada se osvežava | **Ručno** — nije u rasporedu zakazanih poslova |
| Istorija | `hr_annualleavesync` sa brojačima po prolazu |
| Kontrola | Uporediti brojače sa očekivanim brojem zaposlenih; „nepovezano“ ukazuje na zapise sa šifrom 0 |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Jedan neispravan red | **Ceo prenos se prekida** |
| Izvor prazan za obuhvat | Greška: *„Lokalni podaci nisu izmenjeni.“* |
| Šifra zaposlenog 0 | Zapis se čuva nepovezan |
| Zaposleni ne postoji lokalno | Zapis se čuva nepovezan |
| Rešenje uklonjeno iz izvora | Označeno kao povučeno, **ne briše se** |
| Dva istovremena pokretanja | Drugo se odbija |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Izvor su `Godmor` i `GodmorKor` na `PUTGEO-SERVER.BazaLDIMS` | Potvrđeno | `annual_leave.py:12, 23-26` |
| Obuhvat je firma 1 | Potvrđeno | `annual_leave.py:13, 41` |
| Sve ili ništa pri grešci | Potvrđeno | `annual_leave.py:71-72, 90-91` |
| Ključ rešenja nosi mikrosekunde | Potvrđeno | `annual_leave.py:81` |
| Šifra 0 se ne povezuje | Potvrđeno | `annual_leave.py:107` |
| Nestali zapis se označava, ne briše | Potvrđeno | `annual_leave.py:128-130` |
| Zaključavanje pokriva sve ulazne tačke | Potvrđeno | `annual_leave.py:144-151` |
| Sinhronizacija nije zakazana | Potvrđeno | Nije u `EXPECTED_PERIODIC_TASKS` |

---

### K-07 — Bolovanja — uvoz RFZO i povezivanje

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Bolovanja“ i „Uvoz bolovanja“ |
| Tehnički naziv | `parse_rfzo_workbook()`, `import_rfzo_workbook()` |
| Putanja | [`hr/services/sick_leave.py:77`](../hr/services/sick_leave.py#L77) |
| Adrese | `/hr/bolovanja/`, `/hr/bolovanja/uvoz/` |

#### 2. Poslovna svrha

Preuzima spisak bolovanja iz **RFZO Excel izvoza** i povezuje ga sa zaposlenima,
da bi kadrovska služba imala pregled odsustava i da bi se bolovanja videla na radnoj listi.

> **[P] Izričita namera iz koda:** *„…without payroll calculations“* — sistem **ne računa**
> naknadu za bolovanje.

#### 4. Ulazni podaci

Kolone se prepoznaju po nazivu, **na ćirilici ili latinici** [P]:

| Podatak | Prihvaćeni nazivi kolone | Obavezno |
|---|---|---|
| RFZO ID | `Ид`, `Id`, `RFZO ID` | Da |
| JMBG | `ЈМБГ`, `JMBG` | Da |
| Status | `Статус`, `Status` | Da |
| Početak bolovanja | `Датум почетка боловања`, `Datum početka bolovanja`, `Datum pocetka bolovanja` | Da |
| Zaključenje | `Датум закључења боловања`, `Datum zaključenja bolovanja`, `Datum zakljucenja bolovanja` | Ne |
| Ukupno dana | `Укупно дана`, `Ukupno dana` | Ne |

Zaglavlje se traži u **prvih 20 redova**; ako se ne pronađe — greška. [P]

#### 6. Tačan postupak obračuna

##### Ograničenja datoteke [P]

| Ograničenje | Vrednost |
|---|---|
| Veličina datoteke | najviše **10 MB** |
| Raspakovan sadržaj | najviše **50 MB** |
| Broj redova | najviše **50.000** |
| Format | `.xlsx` |

> **[Z]** Provera raspakovane veličine štiti od namerno pripremljene datoteke koja je
> mala, a raspakuje se u ogroman sadržaj.

##### Normalizacija JMBG-a [P]

| Ulaz | Rezultat |
|---|---|
| Tekst od 13 cifara | Prihvata se |
| **12 cifara** | **Dodaje se vodeća nula** — Excel je „pojeo“ nulu u brojčanoj ćeliji |
| Broj sa decimalama | Odbija se |
| Tekst sa vodećim apostrofom | Apostrof se uklanja |
| Bilo šta drugo | Odbija se |

##### Status [P]

| Vrednost u datoteci (ćirilica ili latinica, bez obzira na veličinu slova) | Status |
|---|---|
| `aktivno`, `активно` | **Aktivno** |
| `zaključeno`, `zakljuceno`, `закључено` | **Zaključeno** |
| `stornirano`, `сторнирано` | **Stornirano** |
| `poništeno`, `ponisteno`, `поништено` | **Poništeno** |
| bilo šta drugo | **Greška** |

##### Provere po redu [P]

| Provera | Uslov |
|---|---|
| RFZO ID | Nije prazan, najviše 64 znaka |
| Početak | Postoji, godina između 1900. i 2100. |
| Kraj | Ako postoji: nije pre početka, godina do 2100. |
| **Status „Zaključeno“** | **Mora imati datum zaključenja** |
| Ukupno dana | Ceo broj, najviše 100.000 |
| Isti RFZO ID u datoteci | Dozvoljen **samo ako su podaci identični** |

**Podržani formati datuma:** Excel broj, `GGGG-MM-DD`, `DD.MM.GGGG`, `DD.MM.GGGG.`, `DD/MM/GGGG`. [P]

> **[P] Sve ili ništa:** svaka greška prekida uvoz uz poruku
> *„Nijedan red nije uvezen.“*

##### Provere pri upisu [P]

| Provera | Poruka |
|---|---|
| Isti RFZO ID već postoji uz **drugi JMBG** | *„RFZO ID već postoji uz drugi JMBG. Uvoz nije izvršen.“* |
| **Datum izvoza stariji** od već evidentiranog | *„Datoteka je starija od već evidentiranih podataka.“* |

> **[P]** Druga provera sprečava da stariji izvoz pregazi novije podatke.

##### Povezivanje sa zaposlenim [P]

Traži se zaposleni sa **istim normalizovanim JMBG-om**:

| Broj pronađenih | Povezivanje | Napomena |
|---|---|---|
| **Tačno jedan** | Poveže se | prazno |
| Više | **Ne povezuje se** | „Više zaposlenih sa istim JMBG-om“ |
| Nijedan | **Ne povezuje se** | „Zaposleni nije pronađen po JMBG-u“ |

Nepovezani se broje u `unlinked_count`.

##### Brojači uvoza [P]

`row_count`, `created_count`, `updated_count`, `unchanged_count`, `unlinked_count` —
čuvaju se u `hr_sickleaveimport` zajedno sa **SHA-256 otiskom datoteke**.

**Probni prolaz [P]:** `dry_run=True` vraća brojače bez ijednog upisa.

##### Prikaz bolovanja po danima (radna lista) [P]

Funkcija `sick_leaves_by_day()`:

> uzimaju se bolovanja zaposlenog koja počinju **pre kraja meseca**
> i koja se **završavaju u mesecu ili kasnije**, odnosno **otvorena** bolovanja
> čiji je datum izvoza u mesecu ili kasnije
>
> **isključuju se statusi „Stornirano“ i „Poništeno“**

Za **otvoreno** bolovanje (bez datuma zaključenja) kao kraj se uzima **datum RFZO izvoza**.

#### 8. Primer

> Uvoz datoteke sa datumom izvoza **10.09.2026.**

| RFZO ID | JMBG u datoteci | Status | Početak | Kraj | Ishod |
|---|---|---|---|---|---|
| 100001 | `0101990710012` (13) | Zaključeno | 01.08. | 15.08. | **Novo, povezano** |
| 100002 | `101990710013` (**12**) | Aktivno | 20.08. | — | Novo, povezano (dodata nula) |
| 100003 | `0101990710099` | Aktivno | 25.08. | — | Novo, **nepovezano** — nema zaposlenog |
| 100004 | `0101990710012` | **Zaključeno** | 01.09. | **—** | **GREŠKA — ceo uvoz se prekida** |

Bez reda 100004: `row_count=3, created=3, unlinked=1`.

Na radnoj listi za avgust: bolovanje 100002 prikazuje se od 20.08. do **10.09.**
(datum izvoza), odnosno do kraja avgusta u avgustovskoj listi.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `hr_sickleave`, istorija u `hr_sickleaveimport` |
| Kada se osvežava | **Ručno** — kadrovska služba uvozi RFZO datoteku |
| JMBG na ekranu | **Maskiran** — prikazuju se samo poslednje 4 cifre |
| Kontrola | Brojač „nepovezano“ ukazuje na zaposlene čiji JMBG ne odgovara izvoru |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Jedan neispravan red | Ceo uvoz se prekida | Namerno |
| Ista datoteka uvezena dvaput | Svi redovi „nepromenjeni“, otisak se pamti | Ispravno |
| Stariji izvoz posle novijeg | Odbija se | Ispravno |
| Više zaposlenih sa istim JMBG-om | Ne povezuje se, uz napomenu | Vidljivo |
| **Otvoreno bolovanje** | Kraj se pretpostavlja kao **datum izvoza** | **P-29** |
| Storno i poništenje | Ne prikazuju se na radnoj listi, ali **ostaju u bazi** | Ispravno |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Kolone se prepoznaju i ćirilicom i latinicom | Potvrđeno | `sick_leave.py:20-27` | — |
| JMBG od 12 cifara dobija vodeću nulu | Potvrđeno | `sick_leave.py:39-40` | — |
| Sve ili ništa pri grešci | Potvrđeno | `sick_leave.py:127, 129` | — |
| Stariji izvoz se odbija | Potvrđeno | `sick_leave.py:160-161` | — |
| Povezivanje samo pri jednom poklapanju | Potvrđeno | `sick_leave.py:162-164` | — |
| Storno i poništenje se izuzimaju iz kalendara | Potvrđeno | `sick_leave.py:191` | — |
| **Otvoreno bolovanje se prikazuje do datuma izvoza** | **Potvrđeno** | `sick_leave.py:194` | **P-29** |

---

### K-08 — Ocenjivanje zaposlenih — stimulacija i lični koeficijent

> **Ovo je obračun čiji rezultat ide u obračun zarada.**

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Ocenjivanje“, „Koeficijent stimulacije“, „Lični koeficijent“ |
| Tehnički naziv | `build_snapshot()`, `save_evaluation()` |
| Putanja | [`hr/services/evaluations.py:136`](../hr/services/evaluations.py#L136) |
| Adrese | `/hr/ocenjivanje/`, `/hr/ocenjivanje/novo/`, štampa `/hr/ocenjivanje/<id>/stampa/` |

#### 2. Poslovna svrha

Mesečna ocena zaposlenog po **šest merila**, koja daje **lični koeficijent (K4)** —
množilac koji ulazi u obračun zarade.

#### 3. Korisnici rezultata

Neposredni rukovodilac, direktor centra, generalni direktor, **obračun zarada**.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Ko unosi |
|---|---|---|---|
| Zaposleni | Zaposleni | `hr_employeeevaluation.employee_id` | Rukovodilac |
| Godina i mesec | Period | `year`, `month` | Rukovodilac |
| Grupa za ocenjivanje | Grupa | `hr_evaluationemployeesetup.group_id` | Šifarnik |
| **Bodovi po merilu** | 0–4 po svakom merilu | u `snapshot` | **Rukovodilac** |
| Komentar po merilu | Napomena | u `snapshot` | Rukovodilac |
| Ocenjivači | Tri nivoa | `hr_evaluationunitsetup` | Šifarnik po OJ |

**Šifarnik [P]:** 2 grupe × 6 merila × 5 nivoa bodova (0–4) = **60 kombinacija**.
Uvozi se iz Excel datoteke (`import_evaluation_catalog`), koja **mora** imati tačno
60 kombinacija.

#### 5. Poreklo podataka

```
 Excel šifarnik ocenjivanja ──► EvaluationGroup, EvaluationCriterion, EvaluationScale
                                                     │
 Zaposleni (org_unit_code) ──► EvaluationUnitSetup ──┤ (tri ocenjivača za OJ)
                                                     ▼
                                        potpisani snimak obrasca
                                                     │
                            rukovodilac bira bodove po merilima
                                                     ▼
                              stimulacija = zbir koeficijenata
                              lični koeficijent = 1 + stimulacija
```

#### 6. Tačan postupak obračuna

##### Korak 1 — priprema obrasca (snimak) [P]

Za izabranu grupu se učitavaju **aktivna merila** i njihove **aktivne skale**.

**Obavezna provera:** svako merilo mora imati bar jednu opciju sa koeficijentom **0**
(neutralna vrednost). Inače: *„Merilo *N* nema aktivnu skalu sa neutralnom vrednošću 0.“*

Podrazumevani izbor je neutralna opcija — po pravilu ona sa **1 bod i koeficijentom 0**.

**Granice obrasca** se računaju odmah i **upisuju u snimak** [P]:

> **minimum = 1 + zbir najmanjih koeficijenata svih merila**
> **maksimum = 1 + zbir najvećih koeficijenata svih merila**

##### Korak 2 — potpisivanje obrasca [P]

Snimak se **kriptografski potpisuje** (`django.core.signing`) zajedno sa:

| Podatak | Svrha |
|---|---|
| `user` | Obrazac važi samo za korisnika koji ga je otvorio |
| `nonce` (UUID) | **Sprečava dvostruki upis** iste ocene |
| `source_id` | Veza na prethodnu reviziju |

**Rok važenja: 24 sata.** Posle toga: *„Obrazac je istekao ili nije važeći.“*

##### Korak 3 — obračun pri čuvanju [P]

Za svako merilo se uzimaju izabrani bodovi i pronalazi odgovarajuća opcija
**u sačuvanom snimku** — ne u tekućem šifarniku:

> **stimulacija = Σ koeficijent izabrane opcije, po svim merilima**
> **lični koeficijent (K4) = 1 + stimulacija**

Pravilo je izričito upisano u snimak: `'rule': 'K4 = 1 + sum(stimulation)'`. [P]

> **[P] Ključna zaštita:** ako izabrani bodovi ne postoje u sačuvanoj skali:
> *„Izabrani bodovi ne pripadaju sačuvanoj skali.“* Izmena šifarnika posle otvaranja
> obrasca **ne može** promeniti rezultat.

**Tip i preciznost [P]:** koeficijenti su `decimal(10,5)` — **pet decimala**.

##### Korak 4 — revizija [P]

> **revizija = najveća postojeća revizija za (zaposleni, godina, mesec) + 1**

Ocena je **nepromenljiva**. Ispravka se pravi kao **nova revizija** koja pokazuje na izvornu.

##### Korak 5 — ko koga sme da ocenjuje [P]

| Korisnik | Koga može da oceni |
|---|---|
| Sa dozvolom `hr:evaluation_view_all` | **Sve zaposlene** |
| Neposredni rukovodilac | Samo zaposlene **svojih organizacionih jedinica** (`EvaluationUnitSetup.supervisor`) |
| Bez dozvole `hr:evaluation_create` | **Nikoga** |

Pri čuvanju se zaposleni **zaključava** (`select_for_update`). [P]

##### Pismo [P]

Nazivi merila, opisi i imena čuvaju se **preslovljeni na latinicu** funkcijom `latin()`,
koja pokriva celu ćiriličnu azbuku uključujući `Љ`, `Њ`, `Џ`.

> **[P] Napomena:** funkcija `cyrillic()` je **identična** funkciji `latin()` — obe
> preslovljavaju **na latinicu**. Naziv `cyrillic` je obmanjujuć.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `hr/services/evaluations.py` |
| Funkcije | `build_snapshot()`, `sign_snapshot()`, `read_snapshot()`, `save_evaluation()` |
| Tabela | `hr_employeeevaluation` — `snapshot` (JSON), `stimulation`, `personal_coefficient` |
| Uvoz šifarnika | `manage.py import_evaluation_catalog` |
| Testovi | `hr/test_evaluations.py` — 15 testova |
| Ekran za štampu | `/hr/ocenjivanje/<id>/stampa/` |

#### 8. Primer obračuna

> Ilustrativni primer, grupa „Ostali zaposleni“, šest merila.

| Merilo | Izabrani bodovi | Koeficijent |
|---|---|---|
| 1. Kvalitet rada | 3 | **0,04000** |
| 2. Obim posla | 4 | **0,06000** |
| 3. Samostalnost | 2 | **0,02000** |
| 4. Odnos prema radu | 1 | **0,00000** |
| 5. Saradnja | 3 | **0,04000** |
| 6. Poštovanje rokova | 0 | **−0,03000** |

| Korak | Račun | Rezultat |
|---|---|---|
| **Stimulacija** | 0,04 + 0,06 + 0,02 + 0,00 + 0,04 − 0,03 | **0,13000** |
| **Lični koeficijent K4** | 1 + 0,13000 | **1,13000** |
| Minimum obrasca | 1 + zbir najmanjih | npr. 0,82000 |
| Maksimum obrasca | 1 + zbir najvećih | npr. 1,36000 |

> Koeficijent 1,13000 je unutar granica, pa ga viši nivo može potvrditi ili korigovati
> samo u rasponu 0,82000–1,36000.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Množilac za obračun zarade za jedan mesec |
| Format | `decimal(10,5)` — pet decimala |
| Gde se čuva | `hr_employeeevaluation.stimulation` i `.personal_coefficient`, uz **pun JSON snimak** |
| Kada se ponovo računa | **Nikada** — vrednost je zamrznuta |
| Može li korisnik da ga izmeni | **Ne** — samo nova revizija ili korekcija pri saglasnosti (K-09) |
| Istorija | **Potpuna** — svaka revizija ostaje, sa vezom na izvornu |
| Audit trag | `created_by`, `created_at`, `request_key`, plus saglasnosti |

#### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Obrazac za štampu | Potpisuju ga tri nivoa |
| **Obračun zarada** | **[N] način prenosa nije potvrđen — Q3** |

> **[N] Q3:** nije potvrđeno kako lični koeficijent stiže u obračun zarada — ručnim
> prepisivanjem sa odštampanog obrasca ili nekim prenosom. U kodu nema izvoza ni veze
> ka sistemu zarada.

#### 11. Kontrola i ručna provera

**Kontrolna formula:**

> lični koeficijent = 1 + zbir koeficijenata izabranih bodova po svih šest merila

| Provera | Kako |
|---|---|
| Koeficijent uz svako merilo | Vidljiv na obrascu i u štampi, uz opis osnove bodovanja |
| Granice | Minimum i maksimum su upisani u snimak i prikazani |
| Da li je šifarnik u međuvremenu menjan | Snimak čuva vrednosti **iz trenutka ocenjivanja** |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Obrazac otvoren pre više od 24 sata | Odbija se, traži ponovno otvaranje |
| Dvostruko slanje istog obrasca | **Vraća se postojeća ocena** — `request_key` sprečava duplikat |
| Merilo bez neutralne opcije (koeficijent 0) | Obrazac se **ne može otvoriti** |
| Šifarnik izmenjen posle otvaranja obrasca | Rezultat se računa iz **snimka** |
| Ocena za isti mesec već postoji | Stvara se **nova revizija** |
| Zaposleni izvan nadležnosti rukovodioca | Pristup zabranjen |
| Uvoz šifarnika sa manje od 60 kombinacija | Odbija se |
| Ponovni uvoz šifarnika | Postojeći zapisi se **čuvaju** (`preserved`), ne prepisuju |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| **K4 = 1 + zbir koeficijenata** | Potvrđeno | `evaluations.py:153, 203-204` | — |
| Pet decimala | Potvrđeno | `evaluations.py:60`, model | — |
| Snimak zamrzava skalu i nazive | Potvrđeno | `evaluations.py:183, 197-199` | — |
| Obrazac važi 24 sata | Potvrđeno | `evaluations.py:173` | — |
| `request_key` sprečava dvostruki upis | Potvrđeno | `evaluations.py:188-190` | — |
| Ocena je nepromenljiva, ispravka je nova revizija | Potvrđeno | `evaluations.py:205-210` | — |
| Šifarnik ima tačno 60 kombinacija | Potvrđeno | `evaluations.py:89-90` | — |
| **Kako rezultat stiže u obračun zarada** | **Nepotvrđeno** | — | **Q3** |
| Poreklo koeficijenata u šifarniku | **Nepotvrđeno** | Excel datoteka | **Q6** |

---

### K-09 — Tok saglasnosti na ocenu

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Saglasnost“ |
| Tehnički naziv | `approve_evaluation()`, `approval_state()` |
| Putanja | [`hr/services/evaluations.py:220`](../hr/services/evaluations.py#L220) |
| Adrese | `/hr/ocenjivanje/<id>/saglasnost/`, grupno `/hr/ocenjivanje/saglasnost/` |

#### 2. Poslovna svrha

Ocena postaje važeća tek kada je potvrde **tri nivoa rukovođenja**. Svaki viši nivo može
**korigovati** koeficijent, uz obavezno obrazloženje.

#### 6. Tačan postupak obračuna

##### Redosled nivoa [P]

```
 1. supervisor        Neposredni rukovodilac
 2. director          Direktor centra
 3. general_director  Generalni direktor
```

Nivo se **ne može preskočiti**: *„Prethodni nivo ocenjivanja još nije potvrdio obrazac.“*

##### Ko sme da potvrdi [P]

| Provera | Poruka pri neuspehu |
|---|---|
| Dozvola `hr:evaluation_approve` | Zabranjen pristup |
| **Korisnik mora biti baš taj ocenjivač** sa svog naloga | *„Saglasnost daje samo imenovani ocenjivač sa svog naloga.“* |
| Saglasnost tog nivoa ne sme već postojati | *„Ova saglasnost je već sačuvana.“* |
| Ne sme postojati **novija revizija** | *„Postoji novija verzija obrasca. Potvrdite novu verziju.“* |

##### Koeficijent pri saglasnosti [P]

**Polazna vrednost** je koeficijent **poslednjeg potvrđenog nivoa**, a ako ga nema —
lični koeficijent iz ocene.

| Pravilo | Objašnjenje |
|---|---|
| **Neposredni rukovodilac ne sme menjati koeficijent** | *„Za korekciju merila sačuvajte novu verziju obrasca.“* |
| Viši nivoi smeju menjati | Uz obavezne uslove ispod |
| Nova vrednost mora biti **između minimuma i maksimuma iz snimka** | *„Koeficijent je izvan granica sačuvanog šifrarnika.“* |
| Svaka izmena traži **obrazloženje** | *„Za korekciju koeficijenta unesite obrazloženje.“* |

**Merodavan koeficijent [P]:** vrednost **poslednjeg** potvrđenog nivoa. Ako nema
nijedne saglasnosti — lični koeficijent iz ocene.

##### Zaključavanje [P]

Pri potvrdi se zaključavaju i zaposleni i sama ocena (`select_for_update`).

##### Šta se beleži [P]

| Polje | Sadržaj |
|---|---|
| `stage` | Nivo |
| `actor` | Korisnik koji je potvrdio |
| **`actor_name`** | **Ime u trenutku potvrde** — ne menja se kasnije |
| `document_date` | Datum dokumenta |
| `coefficient` | Potvrđen ili korigovan koeficijent |
| `comment` | Obrazloženje |
| `created_at` | Vreme |

Jedinstveno: **jedna saglasnost po nivou za istu ocenu** (kontrola u bazi). [P]

#### 8. Primer

| Nivo | Radnja | Koeficijent | Obrazloženje |
|---|---|---|---|
| Neposredni rukovodilac | Potvrdio | **1,13000** | — |
| Direktor centra | **Korigovao** | **1,10000** | „Smanjeno zbog kašnjenja na projektu X“ |
| Generalni direktor | Potvrdio | **1,10000** | — |

**Merodavan koeficijent: 1,10000** — vrednost poslednjeg nivoa.

> Da je direktor pokušao 1,40000, bilo bi odbijeno jer prelazi maksimum obrasca (1,36000).
> Da je promenio vrednost bez obrazloženja, takođe bi bilo odbijeno.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `hr_evaluationapproval` |
| Istorija | Potpuna — svaka saglasnost ostaje |
| Kontrola | Na detalju ocene vide se sva tri nivoa, sa datumom, imenom i obrazloženjem |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Pokušaj preskakanja nivoa | Odbija se |
| Pokušaj potvrde tuđe ocene | Odbija se |
| Dvostruka potvrda istog nivoa | Odbija se |
| Nova revizija posle potvrde | Starija ocena se **ne može** dalje potvrđivati |
| Korekcija izvan granica | Odbija se |
| Korekcija bez obrazloženja | Odbija se |
| Rukovodilac menja koeficijent | Odbija se — mora nova revizija |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Tri nivoa u tačnom redosledu | Potvrđeno | `evaluations.py:18, 232-233` |
| Potvrđuje samo imenovani ocenjivač | Potvrđeno | `evaluations.py:223-224` |
| Novija revizija blokira staru | Potvrđeno | `evaluations.py:227-228` |
| Rukovodilac ne sme menjati koeficijent | Potvrđeno | `evaluations.py:235-236` |
| Korekcija mora biti u granicama snimka | Potvrđeno | `evaluations.py:237-238` |
| Korekcija zahteva obrazloženje | Potvrđeno | `evaluations.py:239-240` |
| Merodavan je koeficijent poslednjeg nivoa | Potvrđeno | `evaluations.py:213-216` |

---

### K-10 — Rešenja zaposlenih — izrada teksta dokumenta

> **Ovo nije brojčani obračun.** Rezultat je tekst rešenja koje potpisuje generalni
> direktor, pa se pravila vode ovde, uz ostale kadrovske postupke.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Rešenja“, „Novo rešenje“, „Grupno izdavanje“ |
| Tehnički naziv | `build_document()`, `izdaj_resenje()` |
| Putanja | [`hr/services/resenja.py`](../hr/services/resenja.py) |
| Adrese | `/hr/resenja/`, `/hr/resenja/novo/`, `/hr/resenja/grupno/`, štampa `/hr/resenja/<id>/stampa/` |

#### 2. Poslovna svrha

Zamenjuje Word obrasce kadrovske službe za sedam vrsta rešenja: noćni rad, prekovremeni
rad, prekovremeni rad i rad vikendom, rad na državni i verski praznik, rad vikendom,
prekovremeni rad sa radom vikendom i u smenama, i plaćeno odsustvo za davanje krvi.

#### 3. Korisnici rezultata

Kadrovska služba, zaposleni, referent obračuna zarada, dosije zaposlenog.

#### 4. Ulazni podaci

| Poslovni naziv | Odakle | Ko unosi |
|---|---|---|
| Vrsta rešenja, tekstovi obrasca | `hr_vrstaresenja` | Uprava (šifarnik) |
| Broj rešenja | Podbroj obavezno povezanog zahteva (`43-17/1`); jedan zahtev može imati samo jedno rešenje | **Sistem** |
| Datum rešenja, period ili dani | Zahtev, ekran rešenja | Kadrovik |
| Broj i datum zahteva | `hr_zahtev` | **Sistem, iz zahteva** |
| Razlog zahteva, podnosilac | `hr_zahtev` | Kadrovik, pri unosu zahteva |
| Dodatna polja (npr. poslovi kod zamene) | Zahtev, ekran rešenja | Kadrovik |
| Ime, organizaciona jedinica, radno mesto | `fleet_employee`, `fleet_organizationalunit` | **Predlaže sistem, kadrovik ispravlja** |
| Pol | `fleet_employee.gender` | HR sinhronizacija |
| Potpisnik i funkcija | `hr_potpisnik`, po datumu rešenja | Uprava (šifarnik) |

#### 5. Poreklo podataka

Svi podaci su lokalni. Nijedan povezani server ne učestvuje, pa izrada rešenja radi
i kada `PUTGEO-SERVER` ili `INFORMATIKA23` nisu dostupni.

#### 6. Tačan postupak obračuna

##### Pismo — jedan smer preslovljavanja [P]

Tekstovi u šifarniku se čuvaju **ćirilicom**. Rešenje koje se štampa latinicom nastaje
funkcijom `latin()` iz `hr/services/evaluations.py`.

> **Zašto baš tako:** ćirilica → latinica je jednoznačna, a latinica → ćirilica nije,
> jer se `lj`, `nj` i `dž` ne razlikuju od `l+j`, `n+j` i `d+ž` (na primer „injekcija“).
> Zato obrnuti smer (`to_cyrillic()`) služi **samo kao predlog u formi**, nikada kao
> konačan tekst dokumenta.

Ime zaposlenog ćirilicom uzima se ovim redom [P]:

1. `fleet_employee.full_name_cyrillic` — ručno uneto polje, ima prednost;
2. automatsko preslovljavanje latiničnog imena, kada polje nije popunjeno.

##### Rod — oblici po polu [P]

Word obrasci pišu „запослен-а“ i „дужан-на“ jer papir ne zna pol. Šifarnik umesto toga
koristi čuvar mesta `{rod:дужан|дужна}`, koji se razrešava iz `Employee.gender`:

| Pol | Rezultat |
|---|---|
| `M` | prvi oblik |
| `F` | drugi oblik |
| prazno | oba oblika, odvojena kosom crtom |

##### Uslovni delovi teksta [P]

Segment `[[ime|tekst]]` opstaje samo kada vrednost `ime` nije prazna. Tako jedan obrazac
pokriva i rešenje samo za državni praznik i ono za državni i verski:

```
ради[[dani_drzavni| {dani_drzavni} на дан државног празника]][[dani_verski| и {dani_verski} на дан верског празника]]
```

Red koji se posle razrešavanja isprazni **ne ostavlja praznu tačku** u dispozitivu.

##### Opis perioda [P]

| Uneto | Tekst u rešenju |
|---|---|
| `datum_od` i `datum_do` | „у периоду од 01.02.2026. до 28.02.2026. године“ |
| `datum_od` i „do završetka posla“ | „почев од 23.06.2016. до завршетка посла“ |
| pojedinačni dani | „20.06.2026. и 21.06.2026. године“ |

##### Potpisnik po datumu rešenja [P]

`Potpisnik.za_datum()` bira onog čiji period važenja pokriva datum rešenja
(`vazi_od` uključivo, `vazi_do` isključivo). Zato rešenje iz 2016. godine i danas
nosi tadašnjeg potpisnika, a ne sadašnjeg.

##### Snimak dokumenta [P]

Dok je rešenje **nacrt**, tekst se računa iz trenutnih podataka pri svakom otvaranju.
Pri **izdavanju** se ceo razrešen dokument upisuje u `hr_resenje.dokument` (JSON) i
status prelazi u `izdato`. Od tog trenutka:

- izmena šifarnika, naziva OJ ili potpisnika **ne menja** izdato rešenje;
- rešenje se više ne otvara za izmenu — ispravka ide preko **storniranja** i novog rešenja.

Isti obrazac koristi ocenjivanje (K-08), iz istog razloga.

##### Zahtev i broj rešenja [P]

Zahtev (`hr_zahtev`) dobija broj pri prvom čuvanju: `{centar}-{redni broj}`, gde je
centar šifra centra zaposlenog, a redni broj sledeći broj iz `hr_brojaczahteva` za godinu
datuma zahteva. Red brojača se zaključava (`select_for_update`) do kraja transakcije, pa dva
istovremena unosa ne dobijaju isti broj. Broj je jedinstven u godini.

Rešenje iz zahteva (`napravi_resenje()`) dobija broj `{broj zahteva}/{podbroj}`. Podbroj
se čuva na zahtevu (`poslednji_podbroj`) i samo raste, pa ni obrisan nacrt ne vraća broj.
Rešenje preuzima zaposlenog, pismo, pol, OJ, period, vreme, dane i dodatne podatke iz
zahteva; ime u tekstu rešenja se računa iznova (padež u zahtevu može biti drugačiji).

Tekst zahteva se pravi istim pravilima kao tekst rešenja (pismo, rod, uslovni delovi,
opis perioda). Obrasci stavljaju ime zaposlenog iza dvotačke, u nominativu, da bi tekst bio
ispravan i kada se isti zahtev pravi za više zaposlenih. Ako „ko odobrava“ nije unet,
uzima se potpisnik rešenja koji važi na datum zahteva.

Novi čuvari mesta u obrascima rešenja: `{razlog_zahteva}`, `{podnosilac}`,
`{podnosilac_funkcija}` i dodatna polja vrste.

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajlovi | `hr/resenja_models.py`, `hr/services/resenja.py`, `hr/resenja_views.py`, `hr/resenja_forms.py` |
| Funkcije | `build_document()`, `razresi()`, `opis_perioda()`, `pripremi_resenje()`, `izdaj_resenje()` |
| Tabele | `hr_vrstaresenja`, `hr_potpisnik`, `hr_resenje`, `hr_resenjedan` |
| Početni šifarnik | Migracije `hr/migrations/0014_resenja_sifrarnik_i_dozvole.py` i `0017_zahtevi_sifrarnik_i_dozvole.py` |
| Zahtevi | `hr/zahtevi_models.py`, `hr/services/zahtevi.py` — `dodeli_broj()`, `build_zahtev_document()`, `napravi_resenje()` |
| Testovi | `hr/test_resenja.py`, `hr/test_zahtevi.py` |
| Štampa | HTML strana A4 sa dugmetom „Štampaj / Sačuvaj PDF“, bez dodatnih biblioteka |

#### 8. Primer

> Rešenje za rad na državni i verski praznik, muškarac, ćirilica.

Ulaz: zaposleni Лазар Живановић (OJ 430, centar 43), dani 01.01.2025. i 02.01.2025.
kao državni praznik, 07.01.2025. kao verski, zahtev br. 43-15238 od 27.12.2024.

Tačka 1 dispozitiva:

```
ЛАЗАР ЖИВАНОВИЋ запослен у Институту за испитивање материјала а.д. Београд,
распоређен у ЦЕНТАР ЗА ПУТЕВЕ И ГЕОТЕХНИКУ, дужан је да ради 01.01.2025. и
02.01.2025. на дан државног празника и 07.01.2025. на дан верског празника.
```

Isto rešenje za ženu daje „запослена … распоређена … дужна“, bez ijedne ručne izmene.

#### 9. Rezultat

| Izlaz | Gde |
|---|---|
| Nacrt rešenja | `/hr/resenja/<id>/` |
| Izdato rešenje sa snimkom | `hr_resenje.dokument` |
| Štampa jednog ili više rešenja | `/hr/resenja/<id>/stampa/`, `/hr/resenja/stampa/` |

#### 10. Upotreba rezultata

Odštampano rešenje potpisuje generalni direktor; primerci idu zaposlenom, referentu
obračuna, centru i u dosije. Dani upisani u `hr_resenjedan` ostaju kao osnov za
proveru prekovremenih i prazničnih sati u radnoj listi.

#### 11. Kontrola i ručna provera

- Broj rešenja je **jedinstven po datumu** — duplikat iz delovodnika se odbija pri unosu.
- Broj zahteva je **jedinstven u godini**; brojač se ne može vratiti ispod najvećeg
  postojećeg rednog broja.
- Zahtev sa rešenjem koje nije stornirano ne može da se stornira.
- Pre izdavanja se ceo tekst vidi na ekranu detalja, u konačnom obliku.
- Vrsta koja traži dane ne prolazi bez ijednog unetog dana.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Zaposleni bez unetog pola | Tekst dobija oba oblika („дужан/дужна“) — vidljivo pri pregledu |
| Automatsko preslovljavanje pogreši digraf | Ispravlja se poljem „Ime i prezime (ćirilica)“ na zaposlenom |
| Potreban drugi padež (plaćeno odsustvo traži dativ) | Polje „Zaposleni u tekstu rešenja“ se menja ručno |
| Nema potpisnika za datum rešenja | Izdavanje se odbija uz poruku |
| Zaposleni nema OJ u `fleet_organizationalunit` | Naziv jedinice i centar ostaju prazni; unose se ručno |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Dokaz |
|---|---|---|
| Šifarnik se čuva ćirilicom, latinica nastaje preslovljavanjem | Potvrđeno | `resenja.py: u_pismu()` |
| Ručno uneto ćirilično ime ima prednost | Potvrđeno | `resenja.py: ime_zaposlenog()` |
| Rod se razrešava iz `Employee.gender` | Potvrđeno | `resenja.py: razresi()` |
| Prazan uslovni segment ne ostavlja praznu tačku | Potvrđeno | `resenja.py: _neprazni()` |
| Izdato rešenje se ne menja izmenom šifarnika | Potvrđeno | `test_resenja.py: test_izmena_sifrarnika_ne_menja_vec_izdato_resenje` |
| Potpisnik se bira po datumu rešenja | Potvrđeno | `resenja_models.py: Potpisnik.za_datum()` |

---

### K-11 — Predlog popunjavanja radne liste

> **Predlog, ne obračun.** Ništa se ne upisuje u bazu dok zaposleni ili kadrovik ne klikne
> „Sacuvaj“. Predlog ide **samo u prazna polja** i nikad ne prepisuje uneto.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Predlog popunjavanja“ na radnoj listi, dugmad „Popuni prazna polja“ i „Poništi predlog“ |
| Tehnički naziv | `hr.services.work_time_prefill.predlog()`, `hr.services.praznici.neradni_praznici()` |
| Adresa | `/hr/radna-lista/`, `/hr/zaposleni/<id>/radna-lista/` |

#### 2. Ulazni podaci i poreklo

| Podatak | Odakle |
|---|---|
| Dnevni sati iz prolazaka | K-01 (`INFORMATIKA23`, isti upit kao „Evidencija prolaza“) |
| Dani na putnom nalogu | `fleet_putninalog` (datum puta + broj dana, bez storniranih) |
| Dani bolovanja | `hr_sickleave` (uvoz RFZO, K-07) |
| Neradni praznici | Izračunato po Zakonu o državnim i drugim praznicima (bez spoljnog izvora) |
| Datum slave | `fleet_employee.slava_datum` (dan i mesec); ako nije upisan, predlog iz naziva slave |
| Podrazumevana šifra posla | `fleet_organizationalunit` sa šifrom = OJ zaposlenog (`org_unit_code`, pa `department_code`) |
| Dozvoljene vrste rada | `hr_worktimeelement` za vrstu primaoca zaposlenog (isto kao forma radne liste) |

#### 3. Postupak [P]

Za svaki **radni dan** (ponedeljak–petak) važi prvo pravilo koje se poklapa:

| # | Uslov | Predlog |
|---|---|---|
| 1 | Bolovanje | 8 h, „Bolovanje“ |
| 2 | Neradni praznik | 8 h, „Državni i verski praznik“ |
| 3 | Krsna slava zaposlenog | 8 h, „Državni i verski praznik“ |
| 4 | Prolazi (bar jedan par ulaz–izlaz) | **8 h, pun dan**, bez obzira na stvarno trajanje, „Redovan rad“ |
| 5 | Putni nalog bez prolazaka | 8 h, „Redovan rad“ |

- **Terenski dodatak** = broj dana u mesecu pokrivenih putnim nalogom, i vikendom.
- Svi redovi dobijaju podrazumevanu šifru posla; ako je nema u šifarniku, šifra ostaje prazna.
- **Vikend i rad na praznik se ne predlažu** (za njih treba rešenje); navode se u napomenama.
- Vrsta koja nije dozvoljena za vrstu primaoca zaposlenog se ne predlaže (napomena). Za redovan
  rad bez dozvoljene vrste red ostaje bez oznake vrste.
- Dan sa bolovanjem i prolazima dobija napomenu.

**Neradni praznici:** 1. i 2. januar, 7. januar (Božić), 15. i 16. februar, 1. i 2. maj,
11. novembar i Veliki petak do Vaskrsnog ponedeljka po pravoslavnom Vaskrsu (računa se za
svaku godinu). Kada državni praznik padne u nedelju, ne radi se prvi naredni radni dan
(npr. 17.02.2026). Verski praznici drugih zajednica se ne predlažu — unose se ručno.

**Slava:** datum iz naziva se predlaže samo za slave sa stalnim datumom (Sv. Nikola 19.12,
Sv. Jovan 20.01, Đurđevdan 06.05, Aranđelovdan 21.11 …). Pokretne slave i nazivi koji ne
određuju jedan datum (Sv. Grigorije, Sv. Kliment, Bajram) traže ručni unos datuma.

#### 4. Primena na ekranu

- **Prazna radna lista u statusu „Popunjava se“** dobija predlog odmah pri otvaranju.
- Inače se predlog primenjuje dugmetom **„Popuni prazna polja“**.
- Predložena polja su obojena plavo dok ih korisnik ne izmeni; **„Poništi predlog“** briše samo
  ono što je predlog upisao.
- **„Poništi sve“** prazni celu radnu listu u formi: sate, šifre posla, vrste rada, uslove rada,
  topli obrok i terenski dodatak. Kao i predlog, u bazu se upisuje tek na „Sacuvaj“.
- Red za predlog je prvi red sa istom šifrom i vrstom, ili prvi potpuno prazan red.

#### 5. Status pouzdanosti

| Tvrdnja | Status | Dokaz |
|---|---|---|
| Predlog ne menja bazu | Potvrđeno | `test_work_time_prefill.py: test_prazna_lista_dobija_predlog_odmah` |
| Pravoslavni Vaskrs 2024–2026 i prenos sa nedelje | Potvrđeno | `PrazniciTests` |
| Redosled pravila po danu | Potvrđeno | `PredlogTests.test_pravila_po_danima`, `test_bolovanje_ima_prednost_nad_prolazima` |
| Slava se plaća kao verski praznik | **[N] za potvrdu** | Pravilo je uzeto kao predlog; treba potvrda kadrovske i obračuna zarada |
| Dan sa prolazima = pun dan od 8 h | **[N] za potvrdu** | Pravilo predloga, ne obračun zarade; kraći dan se ispravlja ručno |

---

### Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-28** | U sistemu postoje **dva različita obračuna dnevnih sati** iz iste evidencije prolazaka, sa različitim pravilima (K-01 uparuje prolaske i računa službeni izlazak do 16:00; K-02 čita gotova trajanja i ograničava pauzu na 30 minuta). Daju različite rezultate za isti dan. Dodatno, K-01 **ne ume da upari smenu preko ponoći**. | **Visoka** |
| **P-29** | Otvoreno bolovanje (bez datuma zaključenja) prikazuje se na radnoj listi **do datuma RFZO izvoza**. Ako izvoz nije skoro rađen, bolovanje koje još traje prestaje da se prikazuje. | Srednja |

### Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q25** | Taster **12 (Pauza)** uvek se prijavljuje kao **problem**, pa svaki dan u kome je zaposleni koristio pauzu dobija status „Problem“. Da li pauzu treba obračunati (kao u K-02, ograničeno na 30 minuta) ili je dovoljno da ne bude označena kao problem? |
| **Q26** | Radna lista ima status **„Odobreno“**, ali u kodu nije pronađena radnja koja ga postavlja. Da li je odobravanje radne liste predviđeno? |
| **Q27** | Službeni izlazak se računa **do 16:00**, što je upisano u kod. Da li je to i zvanično radno vreme i treba li da bude podesivo? |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.7. Mobilna telefonija](#67-mobilna-telefonija--obračuni) | Obustave iz zarada |
| [6.10. Isplate](#610-isplate--virmani) | Virmani |
| [4. Baza podataka](#45-kadrovi--hr) | Kadrovske tabele |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema |

---

## 6.7. Mobilna telefonija — obračuni

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](#10-poznati-problemi-i-ograničenja).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [M-04](#m-04--povezivanje-broja-telefona-sa-zaposlenim) | Povezivanje broja telefona sa zaposlenim | — |
| [M-02](#m-02--izuzeci-od-parkinga) | Izuzeci od parkinga | — |
| [M-01](#m-01--obustava-po-zaposlenom) | **Obustava po zaposlenom** | **P-30, P-31** |
| [M-03](#m-03--razvrstavanje-zaposleni--bivši--nezaposleni) | Razvrstavanje zaposleni / bivši / nezaposleni | **P-32** |

> **Ovo je jedan od tri obračuna u sistemu čiji rezultat ide u obračun zarada.**
> Ostali su ocenjivanje ([K-08](#k-08--ocenjivanje-zaposlenih--stimulacija-i-lični-koeficijent))
> i radna lista ([K-04](#k-04-i-k-05--sati-radne-liste)).

---

### Zajednička osnova: četiri evidencije

Modul radi nad četiri odvojene evidencije koje se **mesečno uvoze iz Excel datoteka**
dobijenih od operatera:

| Evidencija | Tabela | Jedinstveno po | Uvoz |
|---|---|---|---|
| **Paketi** | `mobilni_mobilepackage` | partner + naziv + važi od | Bez perioda |
| **Korisnici** | `mobilni_mobileuser` | šifra radnika | Bez perioda |
| **Dodele** | `mobilni_mobileassignment` | **godina + mesec + broj** | **Po mesecu** |
| **Potrošnja** | `mobilni_mobileusage` | **godina + mesec + broj** | **Po mesecu** |

Svaki uvoz se beleži u `mobilni_mobileimportlog` i posle svakog uvoza se automatski
pokreće povezivanje sa zaposlenima (`sync_employee_links`). [P]

```
 Excel operatera ──► Paketi        (naziv, neto iznos, period važenja)
                 ──► Korisnici     (šifra radnika, ime, JMBG)
                 ──► Dodele        (koji broj kome pripada, po mesecu)
                 ──► Potrošnja     (osnovica PDV, parking, NZRD, ukupno, po mesecu)
                                            │
                        povezivanje broja sa zaposlenim (M-04)
                                            │
                                    OBUSTAVA (M-01)
                                            │
                                    CSV ──► obračun zarada
```

---

### M-04 — Povezivanje broja telefona sa zaposlenim

> Ovo je **preduslov** za obustavu. Ako broj nije povezan sa zaposlenim, obustava se
> ne može pripisati nikome.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Zaposleni“ uz dodelu; „Status veze“ kod korisnika |
| Tehnički naziv | `MobileAssignment.linked_employee`, `assignment_linked_employee()` |
| Putanja | [`mobilni/models.py:155`](../mobilni/models.py#L155), [`mobilni/withholdings.py:130`](../mobilni/withholdings.py#L130) |

#### 2. Poslovna svrha

Broj telefona u izvoru operatera nosi **šifru radnika i ime**, ali ne i vezu sa
kadrovskom evidencijom IMS-a. Ovaj korak uspostavlja tu vezu i **jasno označava**
slučajeve u kojima veza nije pouzdana.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona |
|---|---|
| Šifra radnika iz izvora | `mobilni_mobileuser.employee_code` |
| Status veze | `mobilni_mobileuser.link_status` |
| Zaposleni (veza) | `mobilni_mobileuser.employee_id` |
| Šifra iz dodele | `mobilni_mobileassignment.source_employee_code` |
| Ime iz dodele | `mobilni_mobileassignment.source_full_name` |
| Zaposleni na dodeli | `mobilni_mobileassignment.employee_id` |

#### 6. Tačan postupak

##### Statusi veze korisnika [P]

| Status | Značenje |
|---|---|
| `auto` | Automatski povezan |
| `manual` | Ručno povezan |
| `unmatched` | **Nije povezan** |
| **`non_employee`** | **Namerno označen kao nezaposleni** — ne povezuje se |
| `ambiguous` | Više mogućih zaposlenih |

##### Razrešavanje zaposlenog [P]

Redosled provere je strog:

```
 1. Dodela ima korisnika mobilnog?
       DA  ──► status je "non_employee"?  ──► NEMA zaposlenog (namerno)
            └─► korisnik ima vezu ka zaposlenom? ──► TAJ zaposleni
                                                └─► NEMA zaposlenog
 2. Dodela ima direktnu vezu ka zaposlenom? ──► TAJ zaposleni
 3. Inače ──► NEMA zaposlenog
```

> **[P] Bitno:** ako dodela ima korisnika mobilnog, **direktna veza `employee` na dodeli
> se ne gleda uopšte**. Korisnik mobilnog je merodavan.

##### Prikaz kada zaposleni nije pronađen [P]

| Podatak | Redosled traženja |
|---|---|
| Šifra | zaposleni → `source_employee_code` → `mobile_user.employee_code` |
| Ime | zaposleni → `mobile_user.full_name` → `source_full_name` |
| JMBG | zaposleni → `mobile_user.personal_number` → prazno |

> **[Z]** Podaci iz izvora se čuvaju i prikazuju čak i kada veza ne postoji, da se
> ne izgubi trag o tome kome je broj bio dodeljen.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Pet statusa veze | Potvrđeno | `mobilni/models.py:50-55` |
| `non_employee` sprečava povezivanje | Potvrđeno | `withholdings.py:134-135` |
| Korisnik mobilnog ima prednost nad direktnom vezom | Potvrđeno | `withholdings.py:132-137` |
| Podaci iz izvora se čuvaju kao rezerva | Potvrđeno | `withholdings.py:101-122` |

---

### M-02 — Izuzeci od parkinga

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Parking izuzeci“, kolona „Parking izuzet“ |
| Tehnički naziv | `parking_exempt_phone_numbers()`, `is_parking_exempt()` |
| Putanja | [`mobilni/withholdings.py:50`](../mobilni/withholdings.py#L50) |
| Adresa | `/mobilni/parking-izuzeci/` |

#### 2. Poslovna svrha

Nekim zaposlenima parking plaća poslodavac. Za njihove brojeve se **iznos parkinga ne
obustavlja**, iako se pojavljuje na računu operatera.

#### 6. Tačan postupak

**Normalizacija broja [P]:** pre poređenja, broj se svodi na same cifre:

| Ulaz | Rezultat |
|---|---|
| `381641234567` | `381641234567` |
| `381641234567.0` | `381641234567` — uklanja se `.0` iz Excel brojčane ćelije |
| `+381 64 123-4567` | `381641234567` |
| tekst bez cifara | ostaje kako jeste |

Ista normalizacija se primenjuje i pri upisu izuzetka (`MobileParkingExemption.save()`). [P]

**Provera [P]:**

> broj je izuzet ako se njegov normalizovan oblik nalazi u spisku izuzetaka

> **[P] Izuzetak nema period važenja.** Spisak je jedinstven po broju telefona i
> **važi za sve mesece**, uključujući i prošle obračune. Funkcija prima godinu i mesec,
> **ali ih ne koristi**. Vidi problem **P-30**.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Normalizacija na same cifre | Potvrđeno | `withholdings.py:43-47` | — |
| Izuzetak je jedinstven po broju | Potvrđeno | `mobilni/models.py:273` | — |
| **Izuzetak nema period važenja** | **Potvrđeno** | `withholdings.py:50-51` | **P-30** |

---

### M-01 — Obustava po zaposlenom

> **Ovo je najvažniji obračun modula.** Njegov rezultat ulazi u obračun zarada.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Iznos obustave“ |
| Tehnički naziv | `calculate_withholding()` |
| Putanja | [`mobilni/withholdings.py:154`](../mobilni/withholdings.py#L154) |
| Adrese | `/mobilni/obustave/`, `/mobilni/obustave/zaposleni/`, izvoz `/mobilni/potrosnja/obracunski-mesec.csv` |

#### 2. Poslovna svrha

Zaposleni dobija službeni broj telefona sa paketom koji plaća poslodavac.
**Sve iznad paketa zaposleni plaća sam** — taj iznos se obustavlja od zarade.

#### 3. Korisnici rezultata

Administracija (priprema), **obračun zarada** (preuzima iznos), zaposleni (uvid).

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | JM | Obavezno | Ko unosi |
|---|---|---|---|---|---|---|
| Osnovica za PDV | Osnovica za PDV | `mobilni_mobileusage.vat_base` | `decimal(12,2)` | RSD | Da (podrazumevano 0) | Uvoz iz Excel-a |
| Parking | Parking | `mobilni_mobileusage.parking` | `decimal(12,2)` | RSD | Da (podrazumevano 0) | Uvoz iz Excel-a |
| NZRD | NZRD | `mobilni_mobileusage.nzrd` | `decimal(12,2)` | RSD | Da (podrazumevano 0) | Uvoz iz Excel-a |
| **Neto iznos paketa** | Paket neto | `mobilni_mobilepackage.net_amount` | `decimal(12,2)` | RSD | **Ne** | Uvoz iz Excel-a |
| Dodela broja | Paket, Korisnik | `mobilni_mobileassignment` | veza | — | Da | Uvoz iz Excel-a |
| Izuzeće od parkinga | Parking izuzet | `mobilni_mobileparkingexemption` | veza | — | Ne | **Administracija, ručno** |

> **[P] Šta se NE koristi:** kolona `total` („Ukupno za naplatu“) **ne ulazi** u obračun,
> iako je to iznos koji operater naplaćuje. Obustava se računa iz **osnovice za PDV**,
> parkinga i NZRD-a.

#### 5. Poreklo podataka

```
 Excel operatera (potrošnja)  ──► mobilni_mobileusage
                                     vat_base, parking, nzrd
                                          │
 Excel operatera (dodele)     ──► mobilni_mobileassignment ──► paket ──► net_amount
                                          │
 Administracija (ručno)       ──► izuzeci od parkinga
                                          ▼
                                  OBUSTAVA (RSD)
                                          │
                                     CSV izvoz
                                          ▼
                                  obračun zarada
```

#### 6. Tačan postupak obračuna

##### Korak 1 — koje stavke potrošnje uopšte ulaze [P]

Uzimaju se **samo** stavke potrošnje koje imaju dodelu sa **istim** periodom i brojem:

> potrošnja mora imati dodelu **i**
> `potrošnja.godina = dodela.godina` **i**
> `potrošnja.mesec = dodela.mesec` **i**
> `potrošnja.broj = dodela.broj`

> **[P] Posledica:** potrošnja za mesec u kome **nije uvezena dodela** potpuno
> **ispada iz obračuna**, bez upozorenja. Vidi problem **P-31**.

##### Korak 2 — parking [P]

> ako je broj u spisku izuzetaka → **parking = 0**
> inače → parking = `usage.parking`

##### Korak 3 — odbitak paketa [P]

| Slučaj | Odbitak |
|---|---|
| Broj je **`381637781481`** | **0** — paket se **ne odbija** |
| Paket nema neto iznos (`net_amount` prazan) | **Obustava se ne računa** → rezultat je **prazan** |
| Inače | Neto iznos paketa |

> **[P] Poseban broj upisan u kod:** `SPECIAL_PHONE_NUMBER = "381637781481"`.
> Za taj broj se **ceo iznos obustavlja**, bez odbitka paketa.
>
> **⚠ Potvrđeno kao greška (naručilac, 18.09.2026.):** broj **ne sme biti u kodu** —
> ovakav izuzetak pripada **bazi**, kao oznaka uz dodelu ili broj telefona.
> Vodi se kao problem **[P-34](#p-34--poseban-broj-telefona-upisan-u-kod-umesto-u-bazi)**.

##### Korak 4 — formula [P]

> **obustava = osnovica za PDV − neto iznos paketa + parking + NZRD**

Za poseban broj:

> **obustava = osnovica za PDV + parking + NZRD**

**Zaokruživanje [P]:** obračun **ne zaokružuje** — radi se sa punom decimalnom vrednošću.
Zaokruživanje se primenjuje **tek pri CSV izvozu**, na **ceo dinar**, `ROUND_HALF_UP`.

**Prazne vrednosti [P]:**

| Situacija | Rezultat |
|---|---|
| Nema dodele | Obustava je **prazna** (`None`) |
| Paket nema neto iznos | Obustava je **prazna** (`None`) |
| Nema paketa na dodeli | Obustava je **prazna** (`None`) |
| Osnovica, parking ili NZRD prazni | **Ne može se desiti** — podrazumevana vrednost je 0 |

> **[P] Prazno nije nula.** Razlika je namerna: prazno znači „nije obračunato“,
> a nula znači „nema šta da se obustavi“.

##### Korak 5 — zbir na ekranu [P]

> ukupno = zbir svih obustava koje **nisu prazne**

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `mobilni/withholdings.py` |
| Funkcije | `calculate_withholding()`, `withholding_amount_expression()`, `get_withholding_rows()` |
| SQL varijanta | `withholding_amount_expression()` — ista formula kao `Case`/`When` izraz |
| Ekran | `mobilni/views/mobile.py: MobileWithholdingReportView` |
| CSV izvoz | `export_employee_withholdings_csv()` |
| Testovi | `mobilni/tests.py` — 40 testova |

> **[P] Dve implementacije iste formule:** `calculate_withholding()` radi u Pythonu,
> `withholding_amount_expression()` isto u SQL-u. Obe moraju ostati usklađene.

#### 8. Primer obračuna

> Ilustrativni primer, obračunski mesec **avgust 2026**.

| Broj | Osnovica PDV | Parking | NZRD | Paket | Neto paketa | Izuzet parking |
|---|---|---|---|---|---|---|
| 381641111111 | 2.400,00 | 300,00 | 0,00 | Biznis 1 | 1.800,00 | Ne |
| 381642222222 | 1.500,00 | 250,00 | 0,00 | Biznis 1 | 1.800,00 | **Da** |
| **381637781481** | 3.100,00 | 400,00 | 120,00 | Biznis 2 | 2.500,00 | Ne |
| 381643333333 | 2.000,00 | 0,00 | 0,00 | *(bez paketa)* | — | Ne |

**Obračun:**

| Broj | Račun | Obustava |
|---|---|---|
| 381641111111 | 2.400,00 − 1.800,00 + 300,00 + 0,00 | **900,00** |
| 381642222222 | 1.500,00 − 1.800,00 + **0,00** + 0,00 | **−300,00** |
| 381637781481 | 3.100,00 − **0,00** + 400,00 + 120,00 | **3.620,00** |
| 381643333333 | nema neto iznosa paketa | **prazno** |

**U CSV izvoz ulaze [P]:**

| Godina | Mesec | Šifra radnika | Iznos obustave |
|---|---|---|---|
| 2026 | 8 | 1234 | **900** |
| 2026 | 8 | 1235 | **−300** |
| 2026 | 8 | 1240 | **3620** |

> Red sa praznom obustavom **ne ulazi** u izvoz.
> Negativna obustava **ulazi** — vidi problem **P-31**.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Iznos koji se obustavlja od zarade zaposlenog za jedan mesec |
| Format na ekranu | Decimalan broj, RSD, pune decimale |
| **Format u izvozu** | **Ceo dinar**, `ROUND_HALF_UP` |
| Gde se čuva | **Nigde** — računa se pri svakom otvaranju |
| Kada se ponovo računa | Pri svakom otvaranju ekrana ili izvoza |
| Može li korisnik da ga izmeni | Posredno — izmenom dodele, paketa ili izuzetka od parkinga |
| Istorija | **Ne postoji** — izmena paketa menja i ranije obračunate mesece |

> **[Z] Rizik bez istorije:** ako se posle prenosa u zarade promeni neto iznos paketa,
> ekran će za isti mesec pokazati **drugi iznos** nego što je prosleđen. Nema traga
> o tome šta je prosleđeno.

#### 10. Upotreba rezultata

| Korisnik | Šta preuzima | Odakle | Format |
|---|---|---|---|
| **Obračun zarada** | Šifra radnika i iznos | `/mobilni/potrosnja/obracunski-mesec.csv` | CSV: `Godina;Mesec;Šifra radnika;Iznos obustave` |
| Administracija | Detaljni pregled | `/mobilni/obustave/` | Ekran |

**Oblik CSV datoteke [P]:**

| Osobina | Vrednost |
|---|---|
| Razdvajač | **tačka-zarez** `;` |
| Kodiranje | **UTF-8 sa BOM** oznakom |
| Prelom reda | `CRLF` |
| Zaglavlje | `Godina;Mesec;Šifra radnika;Iznos obustave` |
| Obuhvat | **samo aktivni zaposleni** (izveštaj „Obustave zaposlenih“) |
| Izostavljeni redovi | Prazna obustava **i obustava jednaka nuli** |
| Iznos | Ceo dinar |

> **[N] Q3:** nije potvrđeno kako se CSV datoteka dalje unosi u obračun zarada —
> uvozom ili ručnim prepisivanjem — niti koja konta se koriste.

#### 11. Kontrola i ručna provera

**Kontrolna formula:**

> obustava = osnovica za PDV − neto iznos paketa + parking + NZRD

| Provera | Kako |
|---|---|
| Iznos ne odgovara | Otvoriti detalj broja `/mobilni/brojevi/<broj>/` — vide se sve četiri veličine |
| Obustava je prazna | Proveriti da li dodela ima paket i da li paket ima neto iznos |
| Parking nije odbijen | Proveriti `/mobilni/parking-izuzeci/` |
| Zaposleni nedostaje u izvozu | Proveriti da li je aktivan i da li je broj povezan (M-04) |
| Zbir se ne slaže sa računom operatera | **Očekivano** — obustava nije ukupan račun, nego deo iznad paketa |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Potrošnja bez dodele za isti mesec | **Tiho ispada iz obračuna** | **P-31** |
| Paket bez neto iznosa | Obustava prazna, red se ne izvozi | Vidljivo |
| **Negativna obustava** | **Izvozi se kao negativan iznos** | **P-31** |
| Obustava tačno nula | **Ne izvozi se** | Namerno |
| Poseban broj `381637781481` | Paket se ne odbija | **P-34** |
| Izmena paketa posle prenosa u zarade | Ekran menja iznos za prošli mesec | Nema istorije |
| Zaposleni nije aktivan | Ne ulazi u izvoz za zarade | Namerno — vidi M-03 |
| Broj povezan sa `non_employee` | Ne ulazi u izvoz za zarade | Namerno |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje / problem |
|---|---|---|---|
| **Formula: osnovica PDV − paket + parking + NZRD** | Potvrđeno | `withholdings.py:169` | — |
| Kolona `total` se ne koristi | Potvrđeno | Nema upotrebe u `withholdings.py` | Potvrditi da je željeno |
| Poseban broj bez odbitka paketa | Potvrđeno | `withholdings.py:16, 161-162` | **P-34 — greška** |
| Prazan paket → prazna obustava | Potvrđeno | `withholdings.py:163-164` | — |
| Zaokruživanje tek pri izvozu, na ceo dinar | Potvrđeno | `views/mobile.py:925` | — |
| Nula se ne izvozi | Potvrđeno | `views/mobile.py:923` | — |
| **Potrošnja bez dodele ispada** | **Potvrđeno — problem** | `withholdings.py:55-60` | **P-31** |
| **Rezultat se nigde ne čuva** | Potvrđeno | Nema modela za obračun | **P-31** |
| Način prenosa u zarade | **Nepotvrđeno** | — | **Q3** |

---

### M-03 — Razvrstavanje zaposleni / bivši / nezaposleni

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Četiri izveštaja: „Detaljni“, „Zaposlenih“, „Bivših zaposlenih“, „Nezaposlenih“ |
| Tehnički naziv | `get_withholding_rows()`, `_is_former_employee_for_period()` |
| Putanja | [`mobilni/withholdings.py:252`](../mobilni/withholdings.py#L252) |

#### 2. Poslovna svrha

Obustava se od zarade može naplatiti **samo aktivnom zaposlenom**. Za bivše zaposlene i
lica koja nisu u radnom odnosu naplata ide drugim putem, pa se izveštaji razdvajaju.

#### 6. Tačan postupak

| Izveštaj | Uslov | Adresa |
|---|---|---|
| **Sve** | Bez filtera | `/mobilni/obustave/` |
| **Zaposleni** | Broj povezan sa zaposlenim **i zaposleni je aktivan** | `/mobilni/obustave/zaposleni/` |
| **Bivši zaposleni** | vidi pravilo ispod | `/mobilni/obustave/bivsi-zaposleni/` |
| **Nezaposleni** | Broj **nije** povezan ni sa jednim zaposlenim | `/mobilni/obustave/nezaposleni/` |

**Pravilo „bivši zaposleni“ [P]:**

```
 zaposleni ne postoji ILI je aktivan  ──► NIJE bivši
 inače:
    pronađi korisnika mobilnog (sa dodele, ili poslednjeg po ID-u za tog zaposlenog)
    ima li datum odlaska?
        DA  ──► bivši je ako je datum odlaska PRE prvog dana obračunskog meseca
        NE  ──► SMATRA SE BIVŠIM
```

> **[P]** Neaktivan zaposleni **bez** unetog datuma odlaska uvek se svrstava u bivše.
> Vidi problem **P-32**.

**Obuhvat izvoza za zarade [P]:** CSV se pravi **isključivo** iz izveštaja
„Obustave zaposlenih“ — dakle samo za **aktivne** zaposlene.

#### 8. Primer

> Obračunski mesec: **avgust 2026** (prvi dan 01.08.2026.)

| Broj | Zaposleni | Aktivan | Datum odlaska | Izveštaj |
|---|---|---|---|---|
| …111 | Petrović | Da | — | **Zaposleni** |
| …222 | Jovanović | Ne | **15.07.2026.** | **Bivši** (odlazak pre 01.08.) |
| …333 | Nikolić | Ne | **20.08.2026.** | **Nije bivši** — odlazak u toku meseca |
| …444 | Marković | Ne | — | **Bivši** (nema datuma odlaska) |
| …555 | *(nije povezan)* | — | — | **Nezaposleni** |

> Red …333 nije ni u jednom od tri izveštaja osim „Sve“: nije aktivan zaposleni,
> a nije ni bivši po ovom pravilu. Vidi **P-32**.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Neaktivan, odlazak u toku obračunskog meseca** | **Nije ni u jednom pojedinačnom izveštaju** | **P-32** |
| Neaktivan bez datuma odlaska | Svrstan u bivše | **P-32** |
| Korisnik označen kao `non_employee` | Svrstan u nezaposlene | Namerno |
| Zaposleni ima više korisnika mobilnog | Uzima se **poslednji po ID-u** | **P-32** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Četiri izveštaja i njihovi uslovi | Potvrđeno | `withholdings.py:280-285` | — |
| Bivši: odlazak pre prvog dana meseca | Potvrđeno | `withholdings.py:246-248` | — |
| Bez datuma odlaska → bivši | Potvrđeno | `withholdings.py:249` | **P-32** |
| Izvoz za zarade samo za aktivne | Potvrđeno | `views/mobile.py:910` | — |

---

### Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-30** | Izuzeće od parkinga **nema period važenja** — jednom upisan izuzetak menja i **već obračunate prošle mesece**. Funkcija prima godinu i mesec, ali ih ne koristi. | Srednja |
| **P-31** | Obustava se **nigde ne čuva** i računa se iznova pri svakom otvaranju. Nema traga o tome koji je iznos stvarno prosleđen u zarade. Uz to, potrošnja bez dodele za isti mesec **tiho ispada**, a negativna obustava se izvozi bez upozorenja. | **Visoka** |
| **P-32** | Razvrstavanje na bivše zaposlene ima tri rupe: neaktivan zaposleni sa datumom odlaska **u toku obračunskog meseca** ne ulazi ni u jedan pojedinačni izveštaj; neaktivan **bez** datuma odlaska uvek se smatra bivšim; kod više korisnika mobilnog uzima se poslednji po ID-u. | Srednja |
| **P-34** | **Poseban broj telefona upisan je u kod** umesto u bazu. Naručilac je potvrdio da je to greška: izuzetak od odbitka paketa mora biti **oznaka u evidenciji**, koju administracija održava bez izmene koda. | **Visoka** |

### Nova pitanja iz ovog poglavlja

| # | Pitanje | Status |
|---|---|---|
| **Q8** | Poseban tretman broja **381637781481** upisan je u kod. | ✔ **Rešeno (18.09.2026.):** to je **greška**. Izuzetak mora biti **u bazi**, ne u kodu. Vodi se kao problem **P-34**. |
| **Q28** | Obustava se računa iz **osnovice za PDV**, a ne iz kolone „Ukupno za naplatu“ (`total`). | ✔ **Potvrđeno ispravnim (18.09.2026.).** Formula `osnovica PDV − neto paketa + parking + NZRD` je željena. |
| **Q29** | Da li **negativna obustava** (kada je paket veći od potrošnje) treba da se prosleđuje u zarade kao potraživanje zaposlenog, ili da se tretira kao nula? | Otvoreno |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.6. Kadrovi](#66-kadrovi--obračuni) | Ocenjivanje i radne liste |
| [6.10. Isplate](#610-isplate--virmani) | Virmani |
| [4. Baza podataka](#411-mobilna-telefonija--mobilni) | Tabele mobilne telefonije |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema |

---

## 6.8. Potraživanja — obračuni

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](#10-poznati-problemi-i-ograničenja).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [PT-01](#pt-01--starosni-razredi-baketi) | Starosni razredi (baketi) | **P-35** |
| [PT-02](#pt-02--saldo-stavke) | Saldo stavke | — |
| [PT-03](#pt-03--objavljivanje-snimka-stanja) | Objavljivanje snimka stanja | — |
| [PT-04](#pt-04--kontrolni-zbirovi-i-provera-izvora) | **Kontrolni zbirovi i provera izvora** | — |
| [PT-05](#pt-05--saldo-po-šiframa-posla) | Saldo po šiframa posla | — |
| [PT-06](#pt-06--normalizacija-nasleđenih-kontakata) | Normalizacija nasleđenih kontakata | — |

> **Oznake su `PT-`, a ne `P-`**, jer je prefiks `P-` rezervisan za registar problema.

---

### Zajednička osnova: zašto Potraživanja postoje

Nasleđena Naplata čita **direktno nasleđene poglede** pri svakom otvaranju ekrana —
sporo i bez ikakve istorije. Potraživanja umesto toga:

1. **Preuzimaju ceo izvor** u lokalne Django tabele.
2. **Proveravaju** da li se preneto poklapa sa izvorom — kroz šest kontrola.
3. **Objavljuju snimak stanja** na određeni datum.
4. Svi ekrani zatim čitaju **objavljeni snimak**, ne izvor.

```
 dbo pogledi (partneri, baza, ispravke, dodela_baketa, posao)
            │  puno preuzimanje, jedan zaključan prolaz
            ▼
  nepromenljiv snimak izvora (SourceDataset + SourceRow)
            │
            ├──► FinancePartnerIdentity   (partneri)
            ├──► ReceivablePosting        (knjiženja)
            ├──► InvoiceDocument          (fakture IF)
            │
            ▼
   ŠEST KONTROLA  ──── razlika ──► NIŠTA SE NE OBJAVLJUJE
            │
            ▼
  BalanceSnapshot (objavljen) + ReceivablePosition
            │
            ▼
  CollectionState.current_snapshot  ──► svi ekrani i Finansije
```

> **[P] Načelo iz koda:** *„Full, serialized and atomic publication of the legacy
> collections contract.“* — ceo prenos je **jedna transakcija**; ili prođe sve, ili ništa.

#### Zaključavanje [P]

| Baza | Mehanizam |
|---|---|
| SQL Server | `sp_getapplock` na resursu `potrazivanja.full.sync`, vezan za **sesiju** |
| SQLite (testovi) | Zaključavanje u procesu |
| Bilo šta drugo | **Odbija se** — *„Sinhronizacija zahteva SQL Server.“* |

Prethodno pokretanje koje je ostalo u statusu „U toku“, a zaključavanje je slobodno,
automatski se označava kao **neuspešno**. [P]

---

### PT-01 — Starosni razredi (baketi)

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Baket“, „Starosna struktura“, „Nedospelo“, „Dospelo 30/45/60/90/180/181+“ |
| Tehnički naziv | `bucket()` |
| Putanja | [`potrazivanja/services/sync.py:76`](../potrazivanja/services/sync.py#L76) |

#### 2. Poslovna svrha

Razvrstava svako potraživanje po **starosti duga** — koliko je dana prošlo od dospeća —
da bi služba naplate znala **čime prvo da se bavi** i koji su dugovi najrizičniji.

#### 3. Korisnici rezultata

Služba naplate, pravna služba, finansije, uprava.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | Tip | Obavezno |
|---|---|---|---|---|
| Datum dospeća | Dospeće | `potrazivanja_receivableposition.due_date` | datum | **Ne** |
| Datum snimka | Stanje na dan | `potrazivanja_balancesnapshot.as_of_date` | datum | Da |

##### Odakle dolazi datum dospeća [P]

Dospeće se **ne računa u aplikaciji** — preuzima se iz pogleda `dodela_baketa`, koji ga
sastavlja iz dva skupa:

| Skup | Sadržaj |
|---|---|
| `dupli` | Sve iz `v_duplikati` |
| `bez_duplih` | Iz `v_if`, **samo ono čega nema u `v_duplikati`**, sa **`MIN(dpo)`** |

Skupovi se spajaju `UNION ALL` i tek onda **`LEFT OUTER JOIN`**-uju na `baza`.

> **[P] Posledica `LEFT OUTER JOIN`-a:** stavka koja **ne nađe par** dobija `dpo = NULL` →
> razred **`0.1`**. Nepoznato dospeće tako nastaje i kada dokument postoji, ali mu se par
> ne pronađe.

Raniji opis pravila kaže da se za partnera/vezu koja postoji **u više godina** bira
**`MAX`** dospeća, a za ostale **`MIN`** iz `v_if`. **`MAX` se u preuzetom DDL-u ne vidi**
— vidi napomenu o sumnjivoj definiciji `v_duplikati` u
[3.5 §17](#35-potraživanja). [N]

> **[P] Dospeća se ne sužavaju na ista dva konta kao saldo.** `baza` filtrira `20400%` i
> `20500%`, ali `v_if` **nema filter po kontu** (`sif_vrs='IF'`, `sif_par > 0`,
> `god >= 2025`). To je namerno — dokazi dospeća dolaze iz svih IF stavki.

#### 6. Tačan postupak obračuna

```
 dospeće nije poznato   ILI   dospeće >= datum snimka   ──►  razred "0.1"
 inače:
     dana = datum snimka − dospeće
     dana <= 30   ──►  razred "30"
     dana <= 45   ──►  razred "45"
     dana <= 60   ──►  razred "60"
     dana <= 90   ──►  razred "90"
     dana <= 180  ──►  razred "180"
     inače        ──►  razred "181"
```

**Sedam razreda [P]:**

| Razred | Značenje | Dana od dospeća |
|---|---|---|
| **`0.1`** | **Nedospelo** *(i nepoznato dospeće)* | dospeće u budućnosti ili nepoznato |
| `30` | Dospelo — baket 1 | 1–30 |
| `45` | Dospelo — baket 2 | 31–45 |
| `60` | Dospelo — baket 3 | 46–60 |
| `90` | Dospelo — baket 4 | 61–90 |
| `180` | Dospelo — baket 5 | 91–180 |
| `181` | Dospelo — baket 6 | **preko 180** |

> **[P] Razred `0.1` objedinjuje dva različita slučaja:** potraživanje koje **još nije
> dospelo** i potraživanje **kome se ne zna datum dospeća**. U kodu je to izričito
> zabeleženo kao namerno preuzimanje nasleđenog pravila:
> *„Deliberately preserves legacy unknown-date bucket.“*
>
> Sistem ipak **broji** stavke bez dospeća (`unknown_due_count`) i uz svaku poziciju
> beleži oznaku `unknown_due`. Vidi problem **P-35**.

**Granice su „uključivo“ [P]:** dug star tačno 30 dana pripada razredu `30`,
a star 31 dan razredu `45`.

**Provera prema izvoru [P]:** pri objavljivanju snimka sistem **za svaku stavku** poredi
sopstveni izračunat razred sa razredom iz izvora (`dodela_baketa.baket`). Razlika
prekida ceo prenos: *„Baket izvora ne odgovara datumu snimka.“*

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `potrazivanja/services/sync.py` |
| Funkcija | `bucket(due, as_of)` |
| Koristi je | `publish_positions()`, `job_balances()` (PT-05) |
| Bojenje na ekranu | `potrazivanja/services/reports.py:12-13` — pet nivoa crvene |

#### 8. Primer obračuna

> Datum snimka: **18.09.2026.**

| Faktura | Dospeće | Dana | Razred | Prikaz |
|---|---|---|---|---|
| IF-100 | 30.09.2026. | — | **`0.1`** | Nedospelo |
| IF-101 | 18.09.2026. | 0 | **`0.1`** | Nedospelo *(dospeva danas)* |
| IF-102 | 25.08.2026. | 24 | **`30`** | Dospelo — baket 1 |
| IF-103 | 19.08.2026. | 30 | **`30`** | Dospelo — baket 1 |
| IF-104 | 18.08.2026. | 31 | **`45`** | Dospelo — baket 2 |
| IF-105 | 20.03.2026. | 182 | **`181`** | Dospelo — baket 6 |
| IF-106 | **nepoznato** | — | **`0.1`** | **Nedospelo** — iako možda jeste dospelo |

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Starosni razred jednog potraživanja na datum snimka |
| Gde se čuva | U `resolution_details` pozicije, kao `bucket` |
| Kada se ponovo računa | **Pri svakom novom snimku** — razred se menja kako dug stari |
| Može li korisnik da ga izmeni | Ne |

#### 10. Upotreba rezultata

| Gde | Kako |
|---|---|
| Kontrolna tabla Potraživanja | Starosna struktura po partnerima |
| Saldo po šiframa posla (PT-05) | Sedam kolona po razredima |
| Finansijska analitika | Tab „Potraživanja“ na detalju šifre posla |
| Opomene i pravni postupci | Osnov za odluku o daljem postupku |

#### 11. Kontrola i ručna provera

**Kontrolna formula:**

> dana = datum snimka − datum dospeća, pa se uporedi sa granicama 30/45/60/90/180

| Provera | Kako |
|---|---|
| Razred deluje pogrešno | Proveriti **datum snimka** — nije današnji dan, nego dan preuzimanja |
| Dug u „Nedospelo“, a star je | Verovatno **nema datuma dospeća** — proveriti `unknown_due` |
| Razlika prema Naplati | Snimci su iz različitih trenutaka |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Nepoznato dospeće** | Svrstava se u **„Nedospelo“** | **P-35** |
| **Isti red je i „dospeo“ i „nedospeo“** | Vidi niže | **P-35** |
| Dospeće u budućnosti | Nedospelo | Ispravno |
| Razred izvora ne odgovara | **Ceo prenos se prekida** | Ispravno |
| Snimak star nekoliko dana | Razredi su **na dan snimka**, ne na danas | Vidljivo — datum je prikazan |

##### Nesaglasnost `baket` i `kategorija` kod praznog dospeća [P]

Pogled `dodela_baketa` računa **dve** oznake, i one se **ne slažu** kada dospeće nedostaje:

```sql
CASE WHEN DATEDIFF(DAY, dpo, GETDATE()) <= 0 THEN 0 ELSE 1 END AS kategorija
```

Sa `dpo = NULL` poređenje je `UNKNOWN`, pa red pada u `ELSE` → **`kategorija = 1`
(dospelo)**. Istovremeno `baket` ide u **`0.1` (nedospelo)**.

> **Ista stavka je „dospela“ po jednoj koloni i „nedospela“ po drugoj.** [P]

Aplikacija **čuva obe vrednosti** i beleži da je dospeće nepoznato:

```python
resolution_details = {"bucket": ..., "category": integer(row.get("kategorija")),
                      "unknown_due": due is None}
```

> To je konkretan dokaz uz [P-35](#p-35--nepoznato-dospeće-prikazuje-se-kao-nedospelo):
> nesaglasnost postoji **na izvoru**, ne u Django kodu.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Sedam razreda i njihove granice | Potvrđeno | `sync.py:76-83` | — |
| Granice su uključive | Potvrđeno | `sync.py:81` | — |
| **Nepoznato dospeće ide u „Nedospelo“** | **Potvrđeno — namerno preuzeto iz nasleđenog** | `sync.py:78` | **P-35** |
| Razred se proverava prema izvoru | Potvrđeno | `sync.py:276-277` | — |
| Broj stavki bez dospeća se beleži | Potvrđeno | `sync.py:315` | — |

---

### PT-02 — Saldo stavke

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Saldo“ |
| Tehnički naziv | `ReceivablePosition.balance` |
| Putanja | [`potrazivanja/models.py:260`](../potrazivanja/models.py#L260) |

#### 2. Poslovna svrha

Koliko partner **stvarno duguje** po jednom dokumentu, posle svih uplata i ispravki.

#### 6. Tačan postupak obračuna

> **saldo = duguje − potražuje**

**Tri nezavisne provere iste formule [P]:**

| # | Gde | Šta proverava |
|---|---|---|
| 1 | Pri čitanju izvora | `saldo` iz `dodela_baketa` mora biti jednak `duguje − potražuje` |
| 2 | Posle upisa pozicija | Par (`duguje`, `potražuje`) mora ostati nepromenjen |
| 3 | **U samoj bazi** | `CheckConstraint`: `balance = ROUND(debit − credit, 2)` |

> **[P] Treća provera je u bazi**, pa je **nemoguće** upisati poziciju sa netačnim saldom
> — ni kroz aplikaciju, ni ručnim upisom.

**Zaokruživanje [P]:** na **2 decimale**, kako nalaže `CheckConstraint`.

**Grupisanje pozicije [P]:** jedna pozicija je jedinstvena po:

> (snimak, partner, veza dokumenta, šifra posla, grupa konta)

**Grupa konta** (`account_family`) je **tri znaka** [P]:

| Izvor | Kako se dobija |
|---|---|
| `dodela_baketa` | `204` ako je `ino = 0`, inače `205` |
| `baza` (kontrola) | prva **tri znaka** konta (`knt[:3]`) |

> **[Z]** `204` su domaći kupci, `205` inostrani — kontrola upravo poredi da li se te
> dve podele poklapaju.

#### 8. Primer

| Dokument | Duguje | Potražuje | Saldo |
|---|---|---|---|
| IF-100 | 120.000,00 | 0,00 | **120.000,00** |
| IF-101 | 80.000,00 | 80.000,00 | **0,00** |
| IF-102 | 50.000,00 | 65.000,00 | **−15.000,00** — pretplata |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Saldo izvora ≠ duguje − potražuje | **Ceo prenos se prekida** |
| Negativan saldo | **Zadržava se** — ne pretvara se u nulu i ne uklanja kao greška |
| **Saldo tačno nula** | Pogled ima `HAVING SUM(dug) - SUM(pot) <> 0` — **zatvorena pozicija se uopšte ne pojavljuje** kao otvorena stavka. Njeni dokumenti i aktivnosti ostaju |
| Dva reda za isti ključ pozicije | **Prekida se** — *„potrebno razrešiti izvor, bez tihog spajanja“* |
| Devizni iznosi | **Ne sabiraju se** preko valuta — iznos i valuta se čuvaju odvojeno |

> **[P] „Domaći / inostrani“ je podela po kontu, ne po valuti.** Pogled računa
> `CASE WHEN LEFT(knt,3) = N'204' THEN 0 ELSE 1 END AS ino`. Stavka na kontu `205` vodi se
> kao inostrana **bez obzira na valutu knjiženja**, i obrnuto.

> **[P] „Potražuje“ nije dokazano „naplaćeno“.** U izvornom prikazu `potražuje` može
> sadržati i **preknjiženja i druga zatvaranja**, ne samo bankarske uplate. Bez potvrđenih
> vrsta knjiženja i povezivanja **taj zbir se ne sme zvati „naplaćeno“**.

> **[P] Isti broj dokumenta može se ponoviti u različitim godinama.** `POC`/uplata sa
> `vez_dok` **nije automatski dokument godine knjiženja**. Nejasne veze ostaju
> nerazrešene — bez izmišljene raspodele.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Saldo = duguje − potražuje | Potvrđeno | `models.py:268`, `sync.py:279-280` |
| Kontrola u bazi, ne samo u kodu | Potvrđeno | `models.py:268` |
| Tri nezavisne provere | Potvrđeno | `sync.py:279, 300, models.py:268` |
| Duplikat ključa prekida prenos | Potvrđeno | `sync.py:272-273` |

---

### PT-03 — Objavljivanje snimka stanja

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Stanje na dan“, „Sinhronizacija“ |
| Tehnički naziv | `publish_positions()`, `sync_collections()` |
| Putanja | [`potrazivanja/services/sync.py:260`](../potrazivanja/services/sync.py#L260) |
| Adresa | `/potrazivanja/sinhronizacija/` |

#### 2. Poslovna svrha

Umesto da svaki ekran čita izvor u svom trenutku, sistem pravi **jedan snimak stanja**
na tačno određeni datum, proveri ga i **objavi**. Svi ekrani zatim vide **istu sliku**.

#### 6. Tačan postupak

**Korak 1 — preuzimanje** [P]: čitav izvor se čita odjednom, uz zabeležen **trenutak
posmatranja** (`observed`). Datum snimka je datum tog trenutka.

**Korak 2 — provera osnovnog obuhvata** [P]:

> ako su `partneri` **ili** `baza` prazni →
> *„Prazan osnovni izvor; postojeći podaci ostaju objavljeni.“*

Prazan izvor **ne može** obrisati postojeće stanje.

**Korak 3 — šifarnik centara** [P]: iz `posao` se pravi mapa šifra → centar.
Duplirana ili prazna šifra prekida prenos.

**Korak 4 — arhiviranje izvora** [P]: svaki skup se čuva kao **nepromenljiv snimak**
(`SourceDataset`), sa otiskom sadržaja:

| Situacija | Postupak |
|---|---|
| Isti otisak već postoji | Snimak se **ponovo koristi**, ne dupliraju se redovi |
| Novi otisak | Upisuju se svi redovi, pa se **pročitaju nazad** i otisak ponovo izračuna |

> **[P] Provera upisa:** posle upisa se čita nazad i poredi otisak.
> *„Kontrola kompletnog sadržaja izvora … nije prošla.“* prekida prenos.

**Korak 5 — partneri** [P]: obuhvat je **firma 1, grupa 1**.

| Situacija | Postupak |
|---|---|
| Nov partner | Upisuje se |
| Promenjen (drugi otisak) | Ažurira se |
| Nestao iz šifarnika | **`active = False`** — ne briše se |
| **Partner postoji u finansijskim podacima, a nema ga u šifarniku** | Upisuje se kao **neaktivan**, uz zabeležen problem `missing_partner` |

> **[P] Načelo iz koda:** *„Preserve the confirmed company/group from baza; do not guess
> the identity of orphan operational data.“*

**Korak 6 — knjiženja i fakture** [P]:

Izvorni ključ knjiženja: **(godina, vrsta naloga, broj naloga, stavka)**.
Duplikat ili nepotpun ključ prekida prenos. Knjiženje bez datuma knjiženja takođe.

**Faktura (IF dokument)** se pravi grupisanjem knjiženja po:

> (godina, broj naloga, partner, veza dokumenta) — **samo za vrstu `IF` iz `baza`**

| Polje fakture | Kako se dobija |
|---|---|
| Datum dokumenta | **Najraniji** među stavkama |
| Datum dospeća | **Najraniji** među stavkama |
| **Iznos** | **Zbir (duguje − potražuje)** svih stavki |

> **[P] Izričito upozorenje iz koda:** *„v_if.saldo is deliberately NOT used as invoice
> amount.“* — iznos fakture se **ne preuzima** iz nasleđenog pogleda, nego se računa iz
> stavki knjiženja.

**Korak 7 — pozicije** [P]: prave se iz `dodela_baketa`, uz proveru razreda i salda
(vidi PT-01 i PT-02).

**Korak 8 — kontrole** [P]: šest kontrola (vidi PT-04). Svaka razlika prekida prenos.

**Korak 9 — objava** [P]:

```
 snimak: status = "published", published_at = sada
 CollectionState.current_snapshot = ovaj snimak
```

> **[P] Kontrola u bazi:** `CollectionState` ne dozvoljava da aktivno stanje bude
> snimak koji **nije objavljen** ili pripada **drugoj firmi**.

**Sve u jednoj transakciji [P]:** koraci 4–9 su u `transaction.atomic()`.
Greška bilo gde znači da **ništa** nije upisano, a prethodni snimak ostaje objavljen.

#### 8. Primer

| Korak | Ishod |
|---|---|
| Preuzeto | partneri 1.240, baza 18.500, ispravke 320, dodela_baketa 4.100, posao 860 |
| Arhivirano | 5 snimaka izvora; 2 ponovo iskorišćena (isti sadržaj) |
| Partneri | 12 novih, 35 ažuriranih, 4 neaktivna, **2 problema `missing_partner`** |
| Knjiženja | 480 novih, 210 ažuriranih, 15 neaktivnih |
| Fakture | 96 novih dokumenata |
| Pozicije | 4.100 |
| Kontrole | 6 kontrola, **0 razlika** |
| **Objavljeno** | Snimak na dan **18.09.2026.** |

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Proveren snimak stanja potraživanja na određeni datum |
| Gde se čuva | `potrazivanja_balancesnapshot` + `potrazivanja_receivableposition` |
| Kada se ponovo računa | Pri svakoj sinhronizaciji — **novi snimak, stari ostaje** |
| Može li korisnik da ga izmeni | Ne |
| **Istorija** | **Potpuna** — svi raniji snimci ostaju |
| Audit trag | `CollectionSyncRun`, `CollectionSyncStep`, `ImportIssue` |

> **[P] Prednost nad nasleđenom Naplatom:** moguće je pogledati stanje **kako je izgledalo
> na raniji datum**, što Naplata ne omogućava.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Prazan osnovni izvor | Prenos se prekida, staro stanje ostaje objavljeno |
| Bilo koja kontrola ne prođe | **Ništa se ne upisuje**, staro stanje ostaje |
| Dva istovremena pokretanja | Drugo se preskače |
| Prekinut prethodni prolaz | Automatski se označava kao neuspešan |
| Partner nestao iz šifarnika | Označava se neaktivnim, ne briše |
| Knjiženje nestalo iz izvora | `active = False`, uz napomenu *„Van tekućeg obuhvata view-a; nije dokaz brisanja iz ERP-a.“* |
| Ponovni uvoz nasleđenih operativnih podataka posle osamostaljenja | **Odbija se** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Ceo prenos je jedna transakcija | Potvrđeno | `sync.py:350-362` |
| Prazan izvor ne briše podatke | Potvrđeno | `sync.py:338-339` |
| Iznos fakture se računa iz stavki, ne iz `v_if.saldo` | Potvrđeno | `sync.py:203-215` |
| Nestali zapisi se označavaju, ne brišu | Potvrđeno | `sync.py:143-146, 196-198` |
| Objavljen snimak postaje aktivno stanje | Potvrđeno | `sync.py:317-320` |
| Kontrola aktivnog stanja u bazi | Potvrđeno | `models.py:244-247` |

---

### PT-04 — Kontrolni zbirovi i provera izvora

> **Ovo je najvažnija zaštita modula.** Bez nje bi tiha greška u prenosu ostala neprimećena.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kontrolni zbirovi“ u istoriji sinhronizacije |
| Tehnički naziv | `compare_maps()`, `validate_postings()` |
| Putanja | [`potrazivanja/services/sync.py:232`](../potrazivanja/services/sync.py#L232) |

#### 2. Poslovna svrha

Dokazuje da je **sve što je preneto jednako onome što je u izvoru** — pre nego što se
podaci objave i pre nego što ih iko vidi.

#### 6. Šest kontrola [P]

| # | Naziv | Šta poredi | Poruka pri razlici |
|---|---|---|---|
| 1 | **knjiženja → otvorene pozicije** | Zbir `duguje − potražuje` iz `baza` po ključu pozicije naspram salda iz `dodela_baketa` | *„Kontrola knjiženja → otvorene pozicije: N razlika. Snimak nije objavljen.“* |
| 2 | **pozicije** | Očekivani saldo naspram **stvarno upisanog** u bazi | *„Kontrola pozicije: N razlika.“* |
| 3 | **partner/posao/baket** | Zbirovi grupisani po partneru, šifri posla, grupi konta i razredu | *„Kontrola partner/posao/baket: N razlika.“* |
| 4 | **dospeća** | Datum dospeća posle upisa naspram izvora | *„Razlika u datumima dospeća posle prenosa.“* |
| 5 | **duguje/potražuje** | Par iznosa posle upisa naspram izvora | *„Razlika duguje/potražuje nakon prenosa pozicija.“* |
| 6 | **knjiženja** | **Osam polja svakog knjiženja** naspram izvora | *„Kontrola prenetih knjiženja: N razlika.“* |

**Kontrola 6 poredi po knjiženju [P]:** partner, konto, šifra posla, veza dokumenta,
datum knjiženja, datum dospeća, duguje i potražuje — za **svako** aktivno knjiženje.

#### Još dve kontrole: da se izvor nije promenio tokom čitanja [P]

| # | Naziv | Šta radi | Poruka |
|---|---|---|---|
| 7 | **Ponovno čitanje** | Posle čitanja svih izvora, `baza`, `ispravke` i `dodela_baketa` se **čitaju ponovo** i porede po otisku (`fingerprint`) | *„Izvor {naziv} se promenio tokom čitanja. Ponovite sinhronizaciju.“* |
| 8 | **Datum izvora** | Ponovo se uzima `GETDATE()` i poredi sa prvim | *„Datum izvora promenjen tokom čitanja; ponovite sinhronizaciju.“* |

> **[P]** Otisak **namerno izostavlja kolonu `danasnji_datum`** — ona je metapodatak
> snimanja, a ne sadržaj. Bez toga bi se svako čitanje razlikovalo.

Ove dve kontrole rešavaju ono što kontrolni zbirovi sami ne mogu: izvor se čita **bez
`NOLOCK`**, ali u više upita, pa promena između njih ne bi bila vidljiva.

#### Ključ poređenja i nasleđeno upoređivanje teksta [P]

Ključ pozicije je:

> (šifra partnera, **fold**(veza dokumenta), **fold**(šifra posla), grupa konta)

Funkcija `fold()` oponaša nasleđeno SQL upoređivanje `Latin1_General_CI_AI`:

| Postupak | Primer |
|---|---|
| Uklanja **prateće razmake** | `"IF-100  "` → `"if-100"` |
| Svodi na **mala slova** | `"IF-100"` → `"if-100"` |
| Uklanja **dijakritike** | `"Čačak"` → `"cacak"` |

> **[P] Zašto je to neophodno:** nasleđena baza koristi upoređivanje neosetljivo na
> velika slova, dijakritike i prateće razmake. Bez `fold()` bi `"IF-100"` i `"if-100 "`
> bili različiti ključevi, pa bi kontrola prijavila lažne razlike.

#### Zbirni pokazatelji snimka [P]

Uz kontrole se u snimak upisuju i:

| Pokazatelj | Značenje |
|---|---|
| `positions` | Broj pozicija |
| `partners` | Broj različitih partnera |
| `balance` | **Ukupan saldo** |
| `debit`, `credit` | Ukupno duguje i potražuje |
| **`unknown_due_count`** | **Broj pozicija bez datuma dospeća** |

#### 8. Primer

> Sinhronizacija koja **ne prolazi**.

| Kontrola | Grupa | Očekivano | Stvarno |
|---|---|---|---|
| knjiženja → pozicije | partner 1234, IF-100, posao 413111, 204 | 120.000,00 | **118.000,00** |

Ishod: `ValueError: Kontrola knjiženja → otvorene pozicije: 1 razlika. Snimak nije objavljen.`

| Posledica | |
|---|---|
| Transakcija | **Poništena** — ništa nije upisano |
| Prethodni snimak | **Ostaje objavljen** |
| Prolaz | Status **„Neuspešno“**, sa punim tekstom greške |
| Korisnik | Vidi grešku na ekranu sinhronizacije |

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `BalanceSnapshot.totals` i `CollectionSyncRun.control_totals` (JSON) |
| Upotreba | Dokaz ispravnosti snimka; osnov za poređenje sa Naplatom pri prelasku |
| Kontrola | Broj razlika mora biti **0** u svih šest kontrola |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Bilo koja razlika | **Snimak se ne objavljuje** |
| Razlika u zapisu teksta (velika slova, razmaci) | **Ne stvara lažnu razliku** — `fold()` |
| Partner u finansijskim podacima bez šifarnika | Zabeležen kao problem, **ne prekida** prenos |
| Stavke bez dospeća | Prebrojane, **ne prekidaju** prenos |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Šest kontrola pre objave | Potvrđeno | `sync.py:289, 304-310` |
| Svaka razlika prekida objavu | Potvrđeno | `sync.py:255-256, 243-244` |
| `fold()` oponaša `Latin1_General_CI_AI` | Potvrđeno | `sync.py:70-73` |
| Kontrola knjiženja poredi osam polja | Potvrđeno | `sync.py:236-241` |
| Kontrolni zbirovi se čuvaju uz snimak | Potvrđeno | `sync.py:311-316` |

---

### PT-05 — Saldo po šiframa posla

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Tab „Potraživanja“ na detalju šifre posla |
| Tehnički naziv | `job_balances()` |
| Putanja | [`potrazivanja/services/reports.py:16`](../potrazivanja/services/reports.py#L16) |

#### 2. Poslovna svrha

Pokazuje **koliko kupci duguju po jednoj šifri posla**, razvrstano po starosnim razredima —
da rukovodilac posla vidi **koliko duga stoji i koliko je star**.

> **[P] Ovo nije „koliko je naplaćeno“.** Saldo je `duguje − potražuje`, a `potražuje` u
> izvoru može sadržati i preknjiženja i druga zatvaranja, ne samo uplate — vidi
> [PT-02 §12](#12-izuzeci-i-rizični-slučajevi). Iznos naplaćen po pojedinačnoj fakturi
> **sistem ne zna**.

#### 3. Korisnici rezultata

Rukovodioci poslova i centara, finansije, uprava — kroz Finansijsku analitiku.

#### 6. Tačan postupak

**Korak 1 — provera prava** [P]: *„Šifra posla nije dostupna u Potraživanjima.“*
ako korisnik nema pristup toj šifri.

**Korak 2 — aktivno stanje** [P]: uzima se `CollectionState.current_snapshot`.
Ako ga nema ili nije objavljen → **prazan rezultat**, ne greška.

**Korak 3 — pozicije** [P]: pozicije snimka za tu šifru posla, dodatno ograničene
pravima korisnika (`scoped`).

**Korak 4 — grupisanje:**

> grupa = (partner, grupa konta)

**Korak 5 — devet iznosa po grupi [P]:**

| # | Kolona | Sadržaj |
|---|---|---|
| 1 | Nedospelo | razred `0.1` |
| 2 | Dospelo — baket 1 | razred `30` |
| 3 | Dospelo — baket 2 | razred `45` |
| 4 | Dospelo — baket 3 | razred `60` |
| 5 | Dospelo — baket 4 | razred `90` |
| 6 | Dospelo — baket 5 | razred `180` |
| 7 | Dospelo — baket 6 | razred `181` |
| 8 | **Dospelo ukupno** | **zbir kolona 2–7** |
| 9 | **Ukupno** | **zbir kolona 1–7** |

**Sortiranje:** po šifri partnera, pa po grupi konta. [P]

**Bojenje [P]:** pet nivoa crvene, po razredu:

| Razred | `0.1` | `30` | `45` | `60` | `90` | `180` | `181` | Dospelo | Ukupno |
|---|---|---|---|---|---|---|---|---|---|
| Nivo | 1 | 2 | 2 | 3 | 3 | 4 | **5** | 4 | 3 |

#### 8. Primer

> Šifra posla **413111**, snimak na **18.09.2026.**

| Partner | Grupa | Nedospelo | 30 | 45 | 60 | 90 | 180 | 181+ | **Dospelo** | **Ukupno** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1234 Kupac A | 204 | 200.000 | 50.000 | 0 | 0 | 0 | 0 | 0 | **50.000** | **250.000** |
| 5678 Kupac B | 204 | 0 | 0 | 0 | 0 | 0 | 0 | 480.000 | **480.000** | **480.000** |
| 9012 Kupac C | 205 | 120.000 | 0 | 0 | 30.000 | 0 | 0 | 0 | **30.000** | **150.000** |

> Kupac B ima ceo dug stariji od 180 dana — najviši nivo bojenja.
> Kupac C je inostrani (grupa 205).

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde — računa se iz objavljenog snimka |
| Datum stanja | **Uvek se prikazuje** uz tabelu |
| Upotreba | Detalj šifre posla u Finansijama; veza partnera vodi u Potraživanja |
| Kontrola | Zbir svih partnera po šifri mora odgovarati zbiru pozicija te šifre u snimku |

> **[P]** Finansijska analitika **ne čita** nasleđene poglede Naplate — koristi
> isključivo objavljeni snimak Potraživanja i njegova prava pristupa.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Nema objavljenog snimka | Prazan rezultat, bez greške |
| Korisnik nema pravo na šifru | Zabranjen pristup |
| Partner bez naziva | Prikazuje se šifra |
| **Nema istorijskog mesečnog preseka** | Prikazuje se **samo tekuće stanje** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Devet iznosa: sedam razreda + dospelo + ukupno | Potvrđeno | `reports.py:36-37` |
| Grupisanje po partneru i grupi konta | Potvrđeno | `reports.py:27-31` |
| Bez objavljenog snimka — prazan rezultat | Potvrđeno | `reports.py:21-22` |
| Prava pristupa se primenjuju dvaput | Potvrđeno | `reports.py:17-18, 24` |

---

### PT-06 — Normalizacija nasleđenih kontakata

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Kontakti“, oznaka „Potrebna provera“ |
| Tehnički naziv | `normalize_contacts()`, `parse_contact()` |
| Putanja | [`potrazivanja/services/contacts.py:70`](../potrazivanja/services/contacts.py#L70) |

#### 2. Poslovna svrha

U nasleđenoj Naplati je kontakt bio **jedno tekstualno polje** u koje se upisivalo sve —
više imena, više telefona, više adresa e-pošte. Ovaj postupak taj tekst **razdvaja na
pojedinačne osobe i kanale**, a da **ništa ne izgubi**.

> **[P] Načelo iz koda:** *„Conservative, lossless conversion of legacy contact text into
> people and channels.“* — kada nije siguran, sistem **ne pogađa**, nego označava
> za proveru.

#### 6. Tačan postupak

**Korak 1 — adrese e-pošte** [P]: traže se u oba polja (`email` i `name`), proveravaju
Django validatorom, svode na mala slova i **uklanjaju duplikati**.

**Korak 2 — razdvajanje na delove** [P]: polje imena se deli po **zarezu, tački-zarezu
i prelomu reda**.

**Korak 3 — telefoni** [P]: u svakom delu se traže brojevi, pa se čiste:

| Provera | Pravilo |
|---|---|
| Dozvoljeni znakovi | cifre, `+`, razmak, `()`, `/`, `.`, `-` |
| **Broj cifara** | **od 7 do 15** |
| Poseban slučaj | `+ 381 (0)` → `+381` |
| **Datum se ne prihvata** | Oblik `0D.MM.GGGG` se odbacuje |
| Domaći broj | Ako počinje nulom, mora imati **9 ili 10 cifara** |

**Korak 4 — prepoznavanje osobe** [P]. Deo je **osoba** samo ako **sve** važi:

| Uslov |
|---|
| Ima **tačno jedan** telefon |
| Preostali tekst ima **1 do 3 reči** |
| Svaka reč je **slovo po slovo** i počinje **velikim slovom** |
| Nijedna reč nije **oznaka funkcije** |

**Oznake funkcije** (`ROLE_WORDS`) [P]: `direktor`, `dir`, `knjigovodstvo`,
`racunovodstvo`, `računovodstvo`, `finansije`, `office`, `fax`, `faks`, `telefon`,
`tel`, `mobilni`, `knjig`, `agencija`.

**Korak 5 — šta postaje šta** [P]:

| Prepoznato | Ishod |
|---|---|
| Osoba | **Novi kontakt** sa imenom, prezimenom i telefonom, vezan za izvorni (`import_parent`) |
| Ostali telefoni | Kanali na **opštem kontaktu** |
| Adrese e-pošte | Kanali na opštem kontaktu |
| **Nerazrešeno** | Upisuje se u `original_data.unresolved` |

Izvorni zapis postaje **„Opšti kontakt“**, a **ceo izvorni tekst se čuva** u
`original_data`. [P]

**Korak 6 — oznaka za proveru** [P]. Kontakt se označava sa `needs_review` ako:

> ima nerazrešenih delova **ili** je iz njega izdvojena bar jedna osoba
> **ili** nije povezan sa partnerom

> **[Z]** Oznaka se stavlja i kada je razdvajanje uspelo — da čovek potvrdi rezultat.

**Idempotentnost [P]:** obrađuju se samo kontakti koji **još nisu normalizovani**
(`normalized_at` prazan) i koji **nisu nastali razdvajanjem** (`import_parent` prazan).
Ponovno pokretanje ne menja već obrađene.

**Kanali [P]:** `ContactPoint` je jedinstven po (kontakt, vrsta, vrednost) — isti broj
se ne upisuje dvaput.

#### 8. Primer

**Izvorni zapis iz Naplate:**

| Polje | Vrednost |
|---|---|
| `name` | `Marko Marković 0641234567, računovodstvo 011/2345-678; Ana Anić 0651112223` |
| `email` | `office@primer.rs, ana@primer.rs` |

**Rezultat:**

| Nastalo | Vrsta | Sadržaj |
|---|---|---|
| **Opšti kontakt** (izvorni zapis) | — | Funkcija: „Opšti kontakt“ |
| — kanal | telefon | `0112345678` *(iz dela „računovodstvo“ — oznaka funkcije, nije osoba)* |
| — kanal | e-pošta | `office@primer.rs` |
| — kanal | e-pošta | `ana@primer.rs` |
| **Novi kontakt** | osoba | Marko Marković, `0641234567` |
| **Novi kontakt** | osoba | Ana Anić, `0651112223` |
| Oznaka | — | **„Potrebna provera“** — izdvojene su osobe |

Ceo izvorni tekst ostaje u `original_data`.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `potrazivanja_collectioncontact`, `potrazivanja_contactpoint` |
| Kada se pokreće | Jednom, pri osamostaljivanju operativnih podataka |
| Trag izvornog | `original_data` — **ceo izvorni zapis** |
| Kontrola | Pregledati kontakte sa oznakom „Potrebna provera“ |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Ime i telefon u jednom delu | Postaje osoba |
| Dva telefona u istom delu | **Nije osoba** — telefoni idu na opšti kontakt |
| „Direktor 0641234567“ | **Nije osoba** — `direktor` je oznaka funkcije |
| Datum umesto telefona | Prepoznaje se i odbacuje |
| Neispravna adresa e-pošte | Preskače se, deo ide u nerazrešeno |
| Ista osoba dvaput | Spaja se u **jedan** kontakt, oba telefona kao kanali |
| Ponovno pokretanje | Već obrađeni se **preskaču** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Ceo izvorni tekst se čuva | Potvrđeno | `contacts.py:73, 76` |
| Osoba samo uz tačno jedan telefon i 1–3 reči | Potvrđeno | `contacts.py:58-60` |
| Oznake funkcije sprečavaju prepoznavanje osobe | Potvrđeno | `contacts.py:10, 60` |
| Telefon mora imati 7–15 cifara | Potvrđeno | `contacts.py:19-20` |
| Datumi se ne pretvaraju u telefone | Potvrđeno | `contacts.py:51-52` |
| Ponovno pokretanje je bezbedno | Potvrđeno | `contacts.py:72` |

---

### Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-35** | Starosni razred **`0.1` („Nedospelo“) objedinjuje dva različita slučaja**: potraživanje koje još nije dospelo i potraživanje **kome se ne zna datum dospeća**. Dug star godinu dana bez unetog dospeća prikazuje se kao **nedospeo**. Pravilo je namerno preuzeto iz nasleđene Naplate. | Srednja |

### Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q33** | Da li potraživanja **bez datuma dospeća** treba i dalje prikazivati kao „Nedospelo“ (nasleđeno pravilo), ili ih izdvojiti u zaseban razred „Nepoznato dospeće“? Sistem ih već broji zasebno (`unknown_due_count`). |
| **Q34** | Postoji li planirani datum kada Potraživanja preuzimaju **sve** funkcije Naplate, uključujući pravnu službu, i kada se meni Naplate uklanja? |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.1. Finansijska analitika](#61-finansijska-analitika--obračuni) | Prihodi, rashodi, tok gotovine |
| [6.9. Nabavka](#69-nabavka--obračuni-i-analize) | Predmeti nabavke i fakture |
| [4. Baza podataka](#48-potraživanja--potrazivanja) | Tabele Potraživanja |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema |

---

## 6.9. Nabavka — obračuni i analize

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](#10-poznati-problemi-i-ograničenja).

**Analize u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [B-01](#b-01--procenjena-vrednost-stavke-i-predmeta) | Procenjena vrednost stavke i predmeta | **P-38** |
| [B-03](#b-03--ključ-euf-fakture) | Ključ EUF fakture | **P-39** |
| [B-02](#b-02--grupisanje-uf-stavki-u-uf-fakture) | Grupisanje UF stavki u UF fakture | **P-37** |
| [B-04](#b-04--razlike-verzija-plana-javnih-nabavki) | Razlike verzija plana javnih nabavki | — |
| [B-05](#b-05--provera-šifre-posla-partnera) | Provera šifre posla partnera | — |
| [B-06](#b-06--izveštaji-i-alarmi-nabavke) | Izveštaji i alarmi nabavke | ~~P-36~~ |
| [B-07](#b-07--poklapanje-robe-sa-uf-ili-euf-fakturom) | Poklapanje robe sa UF ili EUF fakturom | — |

---

### Zajednička osnova: tri izvora i tri snimka

Nabavka radi nad **sopstvenim evidencijama** (predmeti, stavke, narudžbenice) i nad
**tri snimka nasleđenih izvora**:

| Snimak | Django tabela | Izvor | Zadatak |
|---|---|---|---|
| Snimak | Django tabela | Izvor | Zadatak | **Najviše redova po prolazu** |
|---|---|---|---|---|
| **EUF fakture** | `nabavka_invoice` | `dbo.nbv_preuzete_EUF` | Dnevno u 02:20 | **2.000** |
| **UF stavke** | `nabavka_euf_item_snapshot` | `dbo.nbv_EUF_stavke` | Dnevno u 02:45 | **20.000** |
| **Roba** | `nabavka_goods_snapshot` | `dbo.nbv_roba` | Dnevno u 07:10 | **20.000** |
| *UF fakture* | `nabavka_uf_invoice_snapshot` | **izvedeno iz UF stavki** | Uz sinhronizaciju stavki | — |

```
 dbo.nbv_preuzete_EUF ──► EUF fakture (nabavka_invoice)
                              │
 dbo.nbv_EUF_stavke   ──► UF stavke ──grupisanje──► UF fakture
                              │
 dbo.nbv_roba         ──► Roba
                              │
              povezivanje sa stavkom predmeta nabavke
                              ▼
                  predmet ── faktura ── šifra posla
```

> **[P] Načelo:** stavka predmeta nabavke povezuje se sa **tačno jednim** izvorom
> (`euf`, `uf` ili `goods`). Provera je u `ProcurementItem.clean()`.

#### Granice preuzimanja [P]

EUF fakture se čitaju sa `SELECT TOP (limit)` uz `ORDER BY TRY_CONVERT(date, datum) DESC`,
a zadatak poziva sa `limit=2000`. **Preuzima se samo najnovijih 2.000 faktura po prolazu.**
Tvrdi maksimum je takođe 2.000.

Za UF stavke i Robu podrazumevano je 10.000, a tvrdi maksimum **20.000**.

> **[Z] Šta to znači:** ako izvor u jednom danu ima više od toga, **višak se ne preuzima** i
> nema upozorenja. Kod EUF faktura granica je najuža, a `get_euf_invoice()` traži ključ
> **linearno** kroz listu od 2.000 redova.

Svaki od tri zadatka ima **singleton zaključavanje**: TTL 2 sata za EUF fakture, 3 sata za
UF stavke i Robu. [P]

#### Dva odvojena mehanizma povezivanja [P]

Ovo se lako pomeša, a razlika menja iznose u izveštajima:

| Odakle se povezuje | Šta se upisuje | Ulazi u „Ukupan iznos faktura“ ([B-06](#b-06--izveštaji-i-alarmi-nabavke)) |
|---|---|---|
| **Sa detalja predmeta** | `ProcurementItem.source_type` + jedan FK (`euf_invoice` / `uf_invoice` / `goods_item`) | **Ne** |
| **Sa detalja EUF fakture** | Red u `nabavka_item_invoice_link` (`ProcurementItemInvoiceLink`) | **Da** |

> **[P]** Samo drugi način stvara vezu koja se broji u zbiru faktura i u koloni „povezane
> stavke“ na fakturi. Veza je **jedan na jedan prema stavci** (`OneToOneField`) — jedna
> stavka ima najviše jednu fakturu, ali **jedna faktura može imati više stavki i više
> predmeta**.

Pri povezivanju sa fakture nude se **samo** stavke bez već postojeće veze
(`invoice_link__isnull=True`) i predmeti čiji status **nije** `Završeno`, sortirano po
`-procurement_case__created_at`. [P]

> **[P] Automatska promena statusa:** kada se **novom** vezom stavka poveže sa EUF fakturom
> i predmet je u statusu **`Čeka fakturu`**, status predmeta se automatski menja u
> **`Faktura povezana`**.

---

### B-01 — Procenjena vrednost stavke i predmeta

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Procenjena vrednost“ |
| Tehnički naziv | `ProcurementItem.estimated_total`, `ProcurementCase.estimated_value` |
| Putanja | [`nabavka/models.py:306`](../nabavka/models.py#L306) |

#### 2. Poslovna svrha

Pokazuje **koliko se očekuje da će nabavka koštati**, pre nego što stigne faktura —
osnov za odobravanje i za praćenje plana javnih nabavki.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona | JM | Ko unosi |
|---|---|---|---|---|
| Količina | Količina | `nabavka_procurement_item.quantity` | prema JM | Podnosilac zahteva |
| Procenjena cena | Procenjena cena | `nabavka_procurement_item.estimated_unit_price` | RSD | Podnosilac zahteva |
| **Procenjena vrednost predmeta** | Procenjena vrednost | `nabavka_procurement_case.estimated_value` | prema valuti | **Podnosilac zahteva, ručno** |
| Valuta | Valuta | `nabavka_procurement_case.currency` | RSD/EUR/USD/CHF | Podnosilac zahteva |

#### 6. Tačan postupak obračuna

**Po stavci [P]:**

> **procenjena vrednost stavke = procenjena cena × količina**
> ako **bilo koja** od dve vrednosti nedostaje → **prazno** (`None`)

**Po predmetu [P]:**

> **procenjena vrednost predmeta se NE računa iz stavki** — unosi se **ručno**,
> kao zaseban podatak na predmetu

> **[P] Problem P-38:** predmet ima sopstveno polje „Procenjena vrednost“, nezavisno od
> zbira stavki. Sistem **nigde ne poredi** to dvoje, pa se mogu razlikovati bez upozorenja.

**Zaokruživanje [P]:** nema — množe se decimalni brojevi kakvi jesu.

**Valuta [P]:** valuta postoji **samo na predmetu**, ne na stavci. Procenjena cena stavke
se **podrazumeva u valuti predmeta**. [Z]

#### 8. Primer

| Stavka | Količina | JM | Procenjena cena | Procenjena vrednost |
|---|---|---|---|---|
| Ulje motorno 5W30 | 40,00 | l | 1.250,00 | **50.000,00** |
| Filter ulja | 10,00 | kom | 1.800,00 | **18.000,00** |
| Rad servisera | 6,00 | h | *(nije uneta)* | **prazno** |
| | | | **Zbir stavki** | **68.000,00** |
| | | | **Uneto na predmetu** | **75.000,00** |

> Razlika od 7.000,00 RSD ostaje **neprimećena** — sistem je ne prijavljuje.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Stavka: računa se pri prikazu. Predmet: **čuva se** kao uneta vrednost |
| Upotreba | Odobravanje predmeta, poređenje sa planom javnih nabavki |
| Kontrola | **Ručno** sabrati stavke i uporediti sa vrednošću predmeta |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Nema procenjene cene | Vrednost stavke prazna | Vidljivo |
| **Zbir stavki ≠ vrednost predmeta** | **Nema upozorenja** | **P-38** |
| Različite valute | Nemoguće — valuta je samo na predmetu | — |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Vrednost stavke = cena × količina | Potvrđeno | `models.py:306-310` | — |
| Prazno kad nedostaje podatak | Potvrđeno | `models.py:308-309` | — |
| **Vrednost predmeta se unosi ručno** | **Potvrđeno** | `models.py:110-116` | **P-38** |
| Valuta samo na predmetu | Potvrđeno | `models.py:117-122` | — |

---

### B-03 — Ključ EUF fakture

> Ovo nije obračun iznosa, nego **obračun identiteta** — određuje šta je „ista faktura“.
> Od njega zavisi da li će se veza sa predmetom nabavke sačuvati ili izgubiti.

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Ne prikazuje se |
| Tehnički naziv | `make_euf_key()` |
| Putanja | [`nabavka/services/euf.py:49`](../nabavka/services/euf.py#L49) |

#### 2. Poslovna svrha

Nasleđeni pogled `dbo.nbv_preuzete_EUF` **nema stabilan identifikator** fakture.
Sistem ga pravi sam, iz sadržaja reda, da bi pri svakom preuzimanju prepoznao
**istu fakturu**.

#### 6. Tačan postupak obračuna

> **ključ = SHA-256 od:** `datum` **|** `naziv partnera` **|** `broj fakture` **|** `iznos`

| Sastojak | Kako se priprema |
|---|---|
| `datum` | **Izvorni tekst**, samo očišćen od razmaka — **ne** pretvoren u datum |
| `naziv partnera` | Očišćen od razmaka |
| `broj fakture` | Očišćen od razmaka |
| `iznos` | Zaokružen na **2 decimale**; prazan iznos → **prazan tekst** |

Razdvajač je uspravna crta `|`. [P]

> **[P] Zašto se koristi izvorni tekst datuma:** isti datum može stići u različitim
> oblicima (`2026-03-15`, `15.03.2026`). Ključ koristi **izvorni zapis**, pa bi promena
> oblika u izvoru promenila ključ. Poseban obrađen datum (`datum`) se čuva **odvojeno**.

**Prepoznati oblici datuma** (za polje `datum`, ne za ključ) [P]:
`GGGG-MM-DD`, `DD.MM.GGGG`, `DD/MM/GGGG`, `MMM DD GGGG`.

**Jedinstvenost [P]:** `nabavka_invoice` je jedinstvena po (`source`, `euf_key`).

#### 8. Primer

| Polje | Vrednost |
|---|---|
| datum | `15.03.2026` |
| naziv partnera | `AUTODEKI DOO` |
| broj fakture | `2026-1234` |
| iznos | `45000.00` |

> Tekst za heširanje: `15.03.2026|AUTODEKI DOO|2026-1234|45000.00`
> Ključ: `a3f2…` (64 heksadecimalna znaka)

**Šta se dešava kada se izvor promeni:**

| Promena u izvoru | Novi ključ? | Posledica |
|---|---|---|
| Ispravljen iznos sa 45.000,00 na 45.600,00 | **Da** | **Nova faktura**; stara ostaje sa vezama |
| Ispravljen naziv partnera | **Da** | Isto |
| Promenjen oblik datuma | **Da** | Isto |
| Promenjen centar ili magacin | Ne | Ista faktura, ažuriraju se polja |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Ispravka iznosa, partnera ili datuma u izvoru** | **Nastaje nova faktura**, stara ostaje | **P-39** |
| Dve različite fakture sa istim datumom, partnerom, brojem i iznosom | **Isti ključ** — spajaju se u jednu | **P-39** |
| Prazan iznos | Ulazi u ključ kao prazan tekst | Vidljivo |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Ključ je SHA-256 četiri polja | Potvrđeno | `euf.py:49-57` | — |
| Datum ulazi kao **izvorni tekst** | Potvrđeno | `euf.py:52, 61` | — |
| Iznos se zaokružuje na 2 decimale | Potvrđeno | `euf.py:50` | — |
| **Ispravka u izvoru pravi novu fakturu** | **Potvrđeno** | `euf.py:49-57` | **P-39** |

---

### B-02 — Grupisanje UF stavki u UF fakture

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „UF fakture“ |
| Tehnički naziv | `rebuild_uf_invoice_snapshots()` |
| Putanja | [`nabavka/services/source_snapshots.py:192`](../nabavka/services/source_snapshots.py#L192) |
| Adresa | `/nabavka/uf-stavke/`, detalj `/nabavka/uf-stavke/<id>/` |

#### 2. Poslovna svrha

Izvor isporučuje **pojedinačne stavke** ulaznih faktura, bez zaglavlja fakture.
Ovaj postupak stavke **grupiše u fakture**, da bi korisnik video dokument, a ne samo redove.

#### 6. Tačan postupak obračuna

**Ključ grupisanja [P]:**

> **SHA-256 od:** (broj fakture **ili** rezerva) **|** (PIB **ili** matični broj **ili** naziv partnera)

| Deo | Redosled traženja |
|---|---|
| Identifikator fakture | `invoice_number` → ako je prazan: `purchase_invoice_id` → `source_key` |
| Identifikator partnera | `partner_pib` → `partner_mb` → `partner_name` |

**Vrednosti fakture — tri različita pravila [P]:**

| Polje | Pravilo |
|---|---|
| `purchase_invoice_id`, `invoice_number`, `partner_pib`, `partner_mb`, `partner_name`, `accounts` | **Prva neprazna** vrednost među stavkama |
| `document_date`, `creation_date`, `due_date` | **Najkasniji** datum među stavkama |
| `total`, `base_amount`, `payment_amount` | **Prva vrednost koja nije prazna** |
| **`item_value_total`** | **Zbir `value` svih stavki** |
| `item_count` | Broj stavki |
| `accounts` | **Sva različita konta**, sortirana, razdvojena zarezom |

> **[P] Dva iznosa, dva značenja:**
> **`total`** je iznos **iz zaglavlja** izvora (ponovljen na svakoj stavci),
> a **`item_value_total`** je **zbir stavki**. Ako se razlikuju, izvor je nedosledan —
> to je korisna kontrola.

**Povezivanje [P]:** posle grupisanja se svakoj stavci upisuje veza ka fakturi, a
stavkama predmeta nabavke koje imaju vezu ka **stavci**, a nemaju ka **fakturi**,
dopunjava se veza ka fakturi.

**Brisanje viška [P]:**

> `UfInvoiceSnapshot.objects.exclude(pk__in=invoice_ids).delete()`

Sve UF fakture koje se nisu pojavile u ovom prolazu se **brišu**.

> **[P] Problem P-37:** veza `ProcurementItem.uf_invoice` je `SET_NULL`, pa brisanje
> fakture **tiho uklanja vezu** sa stavke predmeta nabavke — bez upozorenja i bez traga.

Ceo postupak je u **jednoj transakciji**. [P]

#### 8. Primer

**UF stavke iz izvora:**

| Stavka | Broj fakture | PIB | Datum dokumenta | Vrednost | Konto |
|---|---|---|---|---|---|
| 1 | `2026-1234` | `100123456` | 15.03.2026. | 30.000,00 | `51300` |
| 2 | `2026-1234` | `100123456` | **20.03.2026.** | 18.000,00 | `51300` |
| 3 | `2026-1234` | `100123456` | 15.03.2026. | 12.000,00 | `52400` |

**Nastala UF faktura:**

| Polje | Vrednost | Pravilo |
|---|---|---|
| Broj fakture | `2026-1234` | prva neprazna |
| PIB | `100123456` | prva neprazna |
| **Datum dokumenta** | **20.03.2026.** | **najkasniji** |
| `item_value_total` | **60.000,00** | zbir stavki |
| `item_count` | 3 | |
| `accounts` | `51300, 52400` | sva različita, sortirana |

> Uočite: datum dokumenta je **najkasniji**, ne najraniji. Ako izvor ima grešku u datumu
> jedne stavke, cela faktura dobija taj datum.

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Stavka bez broja fakture | Koristi se `purchase_invoice_id` ili `source_key` — **svaka takva stavka postaje zasebna faktura** | Vidljivo |
| Isti broj fakture kod dva partnera | **Različite fakture** — partner je u ključu | Ispravno |
| **Faktura nestala iz izvora** | **Briše se, veza sa predmetom tiho nestaje** | **P-37** |
| Neslaganje `total` i `item_value_total` | Oba se prikazuju, bez upozorenja | Korisna kontrola |
| Različiti datumi na stavkama | Uzima se najkasniji | Vidljivo |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Ključ je broj fakture + identifikator partnera | Potvrđeno | `source_snapshots.py:164-168` | — |
| Datumi: najkasniji | Potvrđeno | `source_snapshots.py:171-173` | — |
| Iznosi zaglavlja: prva neprazna vrednost | Potvrđeno | `source_snapshots.py:184-188` | — |
| `item_value_total` je zbir stavki | Potvrđeno | `source_snapshots.py:215` | — |
| **Višak faktura se briše** | **Potvrđeno** | `source_snapshots.py:229-232` | **P-37** |
| Ceo postupak je jedna transakcija | Potvrđeno | `source_snapshots.py:191` | — |

---

### B-04 — Razlike verzija plana javnih nabavki

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Plan javnih nabavki“, kolona „Status razlike“ |
| Tehnički naziv | `import_public_procurement_plan()` |
| Putanja | [`nabavka/services/public_procurements.py:392`](../nabavka/services/public_procurements.py#L392) |
| Adrese | `/nabavka/javne-nabavke/`, uvoz `/nabavka/javne-nabavke/uvoz/` |

#### 2. Poslovna svrha

Plan javnih nabavki se tokom godine **više puta menja**. Ovaj postupak pri svakom uvozu
pravi **novu verziju** i jasno pokazuje **šta je dodato, izmenjeno i uklonjeno** u odnosu
na prethodnu.

#### 3. Korisnici rezultata

Služba nabavke, uprava, pravna služba.

#### 4. Ulazni podaci

Excel datoteka plana. Zaglavlje se **prepoznaje samo po nazivima kolona**. [P]

**Dve vrste plana** se razlikuju po prisutnim kolonama [P]:

| Ako list ima kolonu | Vrsta plana |
|---|---|
| „Osnov izuzeća“ ili „Način procene vrednosti“ | **Nabavka bez primene ZJN** (`exempt`) |
| inače | **Javna nabavka** (`public`) |

#### 6. Tačan postupak obračuna

##### Korak 1 — stabilni ključ stavke [P]

Ključ mora ostati isti između verzija, da bi se stavka prepoznala.

**Ako stavka ima redni broj** (vodeće nule se uklanjaju):

| Dostupno | Ključ |
|---|---|
| Odeljak **i** kategorija | `vrsta:list:odeljak:kategorija:broj` |
| Samo odeljak | `vrsta:list:odeljak:broj` |
| Ništa od toga | `vrsta:list:broj` |

**Ako stavka nema redni broj:**

> `vrsta:list:title:` + prvih **24 znaka** SHA-256 otiska **preslovljenog naslova**

Naziv lista se skraćuje na 30, odeljak i kategorija na 40 znakova. [P]

##### Korak 2 — otisak sadržaja [P]

> otisak = SHA-256 svih polja stavke, **osim broja reda u Excel-u**

> **[P] Zašto se broj reda izuzima:** pomeranje stavke gore-dole u Excel-u **ne sme**
> da je označi kao izmenjenu.

##### Korak 3 — poređenje sa prethodnom verzijom [P]

Uzima se **poslednja verzija za tu godinu**, **bez** stavki označenih kao uklonjene.

| Uslov | Status |
|---|---|
| Ključ ne postoji u prethodnoj verziji | **Dodato** |
| Ključ postoji, **isti otisak** | **Bez izmene** |
| Ključ postoji, **drugi otisak** | **Izmenjeno** |
| Ključ postojao, a nema ga u novoj | **Uklonjeno** |

##### Korak 4 — prenošenje uklonjenih [P]

Uklonjena stavka se **prepisuje u novu verziju** sa statusom „Uklonjeno“, sa svim
podacima iz prethodne verzije.

> **[Z] Posledica:** svaka verzija je **potpuna slika** — sadrži i ono što je uklonjeno.

> **[P] Ograničenje:** stavka uklonjena u v2 pa ponovo uvedena u v3 dobija status
> **„Dodato“**, jer se pri poređenju uklonjene stavke izostavljaju. Veza sa izvornom
> stavkom se gubi.

##### Korak 5 — brojači verzije [P]

Upisuju se `total_rows`, `added_count`, `changed_count`, `unchanged_count`, `removed_count`.

##### Ostala pravila [P]

| Pravilo | Opis |
|---|---|
| Broj verzije | `najveći za tu godinu + 1` |
| Zbirni redovi | Naslovi koji počinju sa **„ukupno“** ili **„svega“** se **preskaču** |
| Listovi bez prepoznatog zaglavlja | Preskaču se i **prijavljuju** korisniku |
| Duplirani ključevi | Prijavljuju se korisniku |
| Prazan rezultat | *„Excel ne sadrzi prepoznate stavke plana javnih nabavki.“* |
| Izvorni red | Ceo se čuva u `raw_data` |
| Upis | **Red po red**, ne paketno — zbog mešanih JSON i decimalnih vrednosti na SQL Serveru |
| Transakcija | Ceo uvoz je jedna transakcija |

#### 8. Primer

> Plan za 2026, verzija 2.

| Stavka u v1 | Stavka u v2 | Otisak | Status u v2 |
|---|---|---|---|
| 1. Kancelarijski materijal, 500.000 | 1. Kancelarijski materijal, 500.000 | isti | **Bez izmene** |
| 2. Gorivo, 8.000.000 | 2. Gorivo, **9.500.000** | drugi | **Izmenjeno** |
| 3. Računari, 1.200.000 | *(nema)* | — | **Uklonjeno** *(prepisano iz v1)* |
| *(nema)* | 4. Softverske licence, 700.000 | — | **Dodato** |

**Brojači verzije 2:** ukupno 4 — dodato 1, izmenjeno 1, bez izmene 1, uklonjeno 1.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `nabavka_public_procurement_plan_version` i `…_item` |
| **Istorija** | **Potpuna** — sve verzije ostaju |
| Upotreba | Praćenje izmena plana, poređenje sa stvarnim nabavkama |
| Kontrola | Brojači verzije; svaka stavka nosi vezu na prethodnu (`previous_item`) |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Izmenjen naslov stavke bez rednog broja | **Nov ključ** → „Dodato“ + „Uklonjeno“ umesto „Izmenjeno“ |
| Preimenovan list u Excel-u | **Nov ključ** za sve stavke tog lista |
| Stavka uklonjena pa vraćena | „Dodato“, bez veze sa izvornom |
| Pomerena stavka u Excel-u | **Bez izmene** — broj reda nije u otisku |
| Zbirni red („Ukupno“) | Preskače se |
| List bez prepoznatog zaglavlja | Preskače se, prijavljuje se |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Stabilni ključ i njegovi oblici | Potvrđeno | `public_procurements.py:211-231` |
| Broj reda se izuzima iz otiska | Potvrđeno | `public_procurements.py:235` |
| Četiri statusa razlike | Potvrđeno | `public_procurements.py:357-363` |
| Uklonjene stavke se prepisuju | Potvrđeno | `public_procurements.py:329-354, 437-439` |
| Uklonjene se izuzimaju pri poređenju | Potvrđeno | `public_procurements.py:416-418` |
| Vrsta plana se prepoznaje po kolonama | Potvrđeno | `public_procurements.py:205-208` |
| Zbirni redovi se preskaču | Potvrđeno | `public_procurements.py:240-242` |

---

### B-05 — Provera šifre posla partnera

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Provera sifre posla za partnera“ |
| Tehnički naziv | `fetch_partner_job_code_rows()` |
| Putanja | [`nabavka/views/reports.py:18`](../nabavka/views/reports.py#L18) |
| Adresa | `/nabavka/izvestaji/provera-sifre-posla-partnera/` |

#### 2. Poslovna svrha

Pokazuje **koje šifre posla su vezane za kog partnera** u nasleđenom izvoru, radi
provere pre povezivanja fakture sa šifrom posla.

#### 6. Tačan postupak

**Nema obračuna** — čita se nasleđeni pogled i prikazuje kako jeste. [P]

| Element | Vrednost |
|---|---|
| Izvor | `dbo.nbv_sif_pos_par` |
| Kolone | `sif_par`, `naz_par`, `sif_pos` |
| Filter | Deo naziva partnera (opciono) |
| **Ograničenje** | **Najviše 2.000 redova** (`TOP`) |
| Sortiranje | Po nazivu partnera, pa po šifri posla |

> **[P] Bez filtera se prikazuje samo prvih 2.000 redova**, bez oznake da je spisak
> odsečen. Korisnik ne zna da li vidi sve.

**Dozvola [P]:** `nabavka:reports` — ista kao za opšte izveštaje.

#### 12–13. Izuzeci i pouzdanost

| Tvrdnja | Status | Izvor |
|---|---|---|
| Čisto čitanje, bez obrade | Potvrđeno | `reports.py:26-44` |
| Ograničenje 2.000 redova | Potvrđeno | `reports.py:27` |
| **Sadržaj pogleda nije poznat** | **Nepotvrđeno** | Čeka DDL — **P-27** |

---

### B-06 — Izveštaji i alarmi nabavke

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Izveštaji nabavke“, „Alarmi nabavke“ |
| Tehnički naziv | `ReportsView`, `AlertsView` |
| Putanja | [`nabavka/views/reports.py:47`](../nabavka/views/reports.py#L47), [`nabavka/views/alerts.py:10`](../nabavka/views/alerts.py#L10) |
| Adrese | `/nabavka/izvestaji/`, `/nabavka/alarmi/` |

#### 2. Poslovna svrha

Brz pregled stanja nabavke: koliko predmeta je u kom statusu i koje vrste, ukupan iznos
povezanih faktura i narudžbenica, i spisak predmeta koji **čekaju fakturu**.

#### 6. Tačan postupak

##### Izveštaji nabavke — četiri pokazatelja [P]

| Pokazatelj | Postupak |
|---|---|
| **Po statusu** | Broj predmeta po svakom od sedam statusa |
| **Po tipu** | Broj predmeta po tipu (nabavka / usluga / oprema) |
| **Ukupan iznos faktura** | Zbir `amount` faktura **koje imaju bar jednu povezanu stavku** |
| **Ukupan iznos narudžbenica** | Zbir `amount` **svih** narudžbenica |

Ukupan iznos faktura sabira se nad skupom **bez ponavljanja** [P]:

```python
ProcurementInvoice.objects.filter(
    pk__in=ProcurementItemInvoiceLink.objects.values("invoice_id")
).aggregate(total=Sum("amount"))["total"]
```

> **Ispravljeno 18.09.2026.** — raniji upit je filtrirao po `item_links`, što pravi
> **spoj sa tabelom veza**, pa se faktura pojavljivala **onoliko puta koliko ima
> povezanih stavki**; `distinct()` na to nije uticao jer se primenjuje na spoljni
> `SELECT`, a ne na sabiranje. Faktura od 100.000 RSD sa tri stavke ulazila je kao
> **300.000 RSD**.
>
> **Prikazani iznos će zato biti manji nego ranije. Raniji je bio pogrešan.**
> Videti [P-36](#10-poznati-problemi-i-ograničenja).

##### Alarmi nabavke [P]

> prikazuju se **samo** predmeti sa statusom **„Čeka fakturu“** (`waiting_invoice`)

Nema nijednog drugog alarma — **nema upozorenja** na osnovu datuma zahteva (`needed_by`),
prekoračenja procenjene vrednosti ni starosti predmeta. [P]

#### 8. Primer

> Tri fakture povezane sa predmetima.

| Faktura | Iznos | Broj povezanih stavki |
|---|---|---|
| F-100 | 100.000,00 | **3** |
| F-200 | 50.000,00 | **1** |
| F-300 | 20.000,00 | **2** |

| Pokazatelj | Tačno | **Prikazano** |
|---|---|---|
| Ukupan iznos faktura | 170.000,00 | **390.000,00** *(3×100.000 + 1×50.000 + 2×20.000)* |

> Prikazan iznos je **2,3 puta veći** od stvarnog.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | Nigde |
| Upotreba | Pregled stanja nabavke |
| **Kontrola** | **Ukupan iznos faktura uporediti sa spiskom** `/nabavka/euf-fakture/` — zbir tamo je tačan |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Faktura sa više povezanih stavki | Iznos ulazi u zbir **jednom** | Ispravljeno, **P-36** |
| Faktura bez povezanih stavki | Ne ulazi u zbir | Namerno |
| Narudžbenica bez iznosa | Ne uvećava zbir | Vidljivo |
| Predmet zaglavljen mesecima | **Nema alarma** | Ograničenje |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Brojači po statusu i tipu | Potvrđeno | `reports.py:55-56` | — |
| Zbir faktura broji svaku fakturu jednom | Potvrđeno | `reports.py` — podupit `pk__in` | Rešeno, **P-36** |
| Zbir narudžbenica obuhvata sve | Potvrđeno | `reports.py:61` | — |
| Alarm je samo „Čeka fakturu“ | Potvrđeno | `alerts.py:18-20` | — |

---

### B-07 — Poklapanje robe sa UF ili EUF fakturom

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Oznaka `UF` / `EUF` uz vezni dokument na spisku robe |
| Tehnički naziv | `_goods_invoice_match_badges()` |
| Putanja | [`nabavka/views/source_snapshots.py`](../nabavka/views/source_snapshots.py) |

#### 2. Poslovna svrha

Roba u izvoru **nema trajnu vezu sa fakturom**. Zato postoje **dva nivoa povezivanja** [P]:

| Nivo | Šta radi |
|---|---|
| **Tvrdo povezivanje** | Korisnik **sam izabere** tačan zapis i poveže ga sa stavkom zahteva |
| **Meko poklapanje** | Sistem **samo naglasi** da roba verovatno pripada nekoj UF ili EUF fakturi |

**Zašto nema automatske trajne veze [P]:**

1. Ista roba može biti deo UF fakture.
2. Ista ili slična roba može biti vidljiva i kroz EUF.
3. Neke robe su iz ranijih perioda i **nemaju učitanu fakturu**.
4. Ponekad postoji **samo robni trag**, bez jasne fakture u lokalnom snimku.

> Meko poklapanje je **pomoć pri radu, a ne evidencija**. Ne upisuje se u bazu i ne menja
> nijedan iznos. [P]

#### 6. Tačan postupak

**Korak 1 — koja roba se uopšte proverava** [P]: samo redovi koji imaju **i** `linked_document`
**i** naziv partnera. Roba bez jednog od toga se preskače.

**Korak 2 — poklapanje broja dokumenta** [P]:

| Vrsta | Poklapa se sa |
|---|---|
| **UF** | `UfInvoiceSnapshot.invoice_number` **ili** `purchase_invoice_id` |
| **EUF** | `ProcurementInvoice.invoice_number` |

Broj se pre poređenja **normalizuje**: `" ".join(str(value).split()).casefold()` — dakle
sređeni razmaci i mala slova.

**Korak 3 — poklapanje firme** [P]. Naziv partnera se svodi na tokene:

1. uklone se dijakritici;
2. sve što nije `a-z0-9` postaje razmak;
3. izbacuju se pravni oblici **`doo`, `ad`, `szr`, `pr`** — i razbijeni oblici `d o o`, `a d`.

Poklapanje je **tačno ili prefiksno po tokenima**: kraći niz tokena mora biti **početak**
dužeg. Tako se „AUTO DEKI DOO“ i „Auto Deki d.o.o. Beograd“ prepoznaju kao ista firma.

**Korak 4 — prikaz oznake** [P]: oznaka se prikazuje **samo kada postoji tačno jedno**
poklapanje te vrste. Oznaka je **link na tu fakturu**, a tooltip glasi
*„Potvrdjeno brojem fakture i firmom“*.

#### 8. Primer

| Roba | `linked_document` | Partner | Rezultat |
|---|---|---|---|
| Filter ulja | `TEST-UF-001/2026` | `AUTO DEKI DOO` | Jedna UF sa tim brojem i firmom → oznaka **`UF`** |
| Guma | `12345` | `Auto Deki d.o.o.` | Dve UF fakture sa istim brojem → **nema oznake** |
| Akumulator | *(prazno)* | `AUTO DEKI DOO` | Nema veznog dokumenta → **ne proverava se** |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Više od jednog poklapanja iste vrste | **Nema oznake** — izvor nije jednoznačan |
| **Poklapa se i sa UF i sa EUF** | Prikazuje se **`UF`**, sa tooltipom *„Potvrdjeno brojem fakture i firmom. Postoji i EUF, ali roba se prikazuje kao UF jer UF ima stavke.“* [P] |
| Roba bez `linked_document` ili bez partnera | Preskače se bez traga |
| Firma se razlikuje samo po pravnom obliku | **Poklapa se** — pravni oblici se izbacuju |
| Firma je prefiks druge firme | **Poklapa se** — prefiksno pravilo može spojiti „Auto Deki“ i „Auto Deki Plus“ [Z] |

> **[Z] Granica prefiksnog pravila:** dve stvarno različite firme čiji je naziv jedne
> početak druge biće prepoznate kao ista. Uz obavezno poklapanje broja fakture to je malo
> verovatno, ali **nije nemoguće**.

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Dva nivoa povezivanja, meko se ne upisuje | Potvrđeno | `source_snapshots.py` |
| Normalizacija broja i naziva firme | Potvrđeno | `_company_matches()` |
| Oznaka samo kod tačno jednog poklapanja | Potvrđeno | `_goods_invoice_match_badges()` |
| Kod dvostrukog poklapanja prikazuje se **UF** | Potvrđeno | `nabavka/tests.py` — `assertIn(">UF</a>")`, `assertNotIn(">EUF</a>")` |

> **Ispravka ranije dokumentacije [P]:** stariji dokument
> `nabavka-modeli-zahtevi-euf-uf-roba.md` tvrdio je da se kod poklapanja i sa UF i sa EUF
> **oznaka ne prikazuje**. **To više ne važi** — prikazuje se UF, jer UF ima stavke.

---

### Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-36** | ~~**Ukupan iznos faktura na izveštaju Nabavke je višestruko uvećan.**~~ **Rešeno 18.09.2026.** | **Visoka** |
| **P-37** | Pri obnavljanju UF faktura se **brišu** one koje se nisu pojavile u prolazu. Veza sa stavkom predmeta nabavke je `SET_NULL`, pa **tiho nestaje**, bez upozorenja i bez traga. | **Srednja** |
| **P-38** | Predmet nabavke ima **ručno unetu** procenjenu vrednost, nezavisnu od zbira stavki. Sistem ih **nigde ne poredi**, pa razlika ostaje neprimećena. | Srednja |
| **P-39** | Ključ EUF fakture se pravi iz **datuma, partnera, broja i iznosa**. Svaka ispravka bilo kog od ta četiri podatka u izvoru stvara **novu fakturu**, dok stara ostaje sa svim vezama. Dve stvarno različite fakture sa istim vrednostima dobijaju **isti ključ**. | **Srednja** |

### Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q35** | Da li se ispravke iznosa ili naziva partnera u izvoru EUF faktura dešavaju u praksi? Ako da, koliko često se pojavljuju „dvojnici“ faktura (**P-39**)? |
| **Q36** | Treba li sistem da upozori kada se **zbir stavki** predmeta nabavke razlikuje od **ručno unete** procenjene vrednosti (**P-38**)? |
| **Q37** | Da li su potrebni dodatni alarmi u Nabavci — npr. predmet stariji od N dana bez fakture, ili prekoračenje procenjene vrednosti? |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.8. Potraživanja](#68-potraživanja--obračuni) | Dugovanja kupaca |
| [6.11. Ugovori i menice](#611-ugovori-i-menice--analize) | Partneri, ugovori, menice |
| [4. Baza podataka](#47-nabavka--nabavka) | Tabele Nabavke |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema |

---

## 6.10. Isplate — virmani

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](#10-poznati-problemi-i-ograničenja).

**Obračuni u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [I-02](#i-02--kontrole-naloga-pre-virmana) | Kontrole naloga pre virmana | — |
| [I-01](#i-01--generisanje-datoteke-virmana) | **Generisanje datoteke virmana** | **P-33** |
| [I-03](#i-03--konverzija-virmana-u-json) | Konverzija virmana u JSON | — |

> **Ovo je jedini obračun u sistemu čiji rezultat ide direktno u banku.**
> Greška ovde znači pogrešnu isplatu.

---

### Zajednička osnova

Modul **nema nijednu sopstvenu tabelu**. [P] Radi isključivo nad putnim nalozima
(`fleet_putninalog`) i proizvodi **datoteku za elektronsko bankarstvo**.

```
 Putni nalozi (akontacija, RSD, nisu stornirani, nije rađen virman)
                          │
                   kontrole ispravnosti (I-02)
                          │
              datoteka fiksne širine 180 znakova (I-01)
                          │
                   preuzimanje i slanje u banku
                          │
              oznaka „virman odrađen“ na nalogu
```

#### Podaci platioca upisani u kod [P]

| Podatak | Vrednost |
|---|---|
| Račun platioca | `205000000001445485` |
| Naziv platioca | `Institut IMS a.d.` |
| Mesto platioca | `Beograd` |
| Svrha plaćanja | `NEOPOREZIVA PRIMANJA ZAPOSLENIH` |
| Šifra plaćanja | `241` |
| Model | `000` |
| Oznaka zaglavlja | `Multi E_BANK0` |

> **[P]** Sve navedeno je upisano u `isplate/services/virman.py` i **ne može se menjati
> kroz interfejs**. Promena računa ili naziva firme zahteva izmenu koda.

---

### I-02 — Kontrole naloga pre virmana

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | Poruke o greškama pri pokušaju generisanja |
| Tehnički naziv | `validate_order_for_virman()` |
| Putanja | [`isplate/services/virman.py:126`](../isplate/services/virman.py#L126) |

#### 2. Poslovna svrha

Sprečava da u banku ode nalog sa **pogrešnim ili nepotpunim podacima** — pogrešan broj
računa znači isplatu pogrešnom licu, a duplirani virman dvostruku isplatu.

#### 4. Ulazni podaci

| Poslovni naziv | Polje na ekranu | Tabela i kolona |
|---|---|---|
| Broj naloga | Broj naloga | `fleet_putninalog.order_number` |
| Storniran | Storniran | `fleet_putninalog.storniran` |
| Virman odrađen | Virman odrađen | `fleet_putninalog.virman_generated` |
| Valuta akontacije | Valuta akontacije | `fleet_putninalog.advance_payment_currency` |
| Zaposleni | Zaposleni | `fleet_putninalog.employee_id` |
| **Partija (tekući račun)** | Partija | `fleet_employee.account_number` |
| Iznos akontacije | Isplata/Akontacija | `fleet_putninalog.advance_payment` |

#### 6. Tačan postupak

Sve provere se izvršavaju, pa se **sve greške prijavljuju zajedno** — korisnik ne mora
da ispravlja jednu po jednu. [P]

| # | Provera | Poruka |
|---|---|---|
| 1 | Nalog **nije storniran** | *„<broj>: nalog je storniran.“* |
| 2 | Virman **nije već odrađen** (osim uz izričito ponovno generisanje) | *„<broj>: virman je vec odradjen.“* |
| 3 | Valuta je **RSD** | *„<broj>: valuta mora biti RSD.“* |
| 4 | Nalog ima **IMS zaposlenog** (ne spoljno lice) | *„<broj>: nalog nema IMS zaposlenog.“* |
| 5 | Zaposleni ima **račun** | *„<broj>: zaposlenom nedostaje racun.“* |
| 6 | Račun ima **tačno 18 cifara** | *„<broj>: racun mora imati 18 cifara.“* |
| 7 | Iznos je **veći od nule** | *„Iznos mora biti veci od nule.“* |
| 8 | Broj naloga ima **redni broj posle crtice** | *„<broj>: nedostaje broj putnog naloga.“* |
| 9 | Redni broj nije duži od **21 znaka** | *„<broj>: redni broj putnog naloga je duzi od 21 karaktera.“* |

> **[P] Provere 5 i 6 se isključuju međusobno** — ako računa nema, ne proverava se dužina.

**Obuhvat spiska na ekranu [P]:** prikazuju se samo nalozi koji **nisu stornirani**,
imaju **akontaciju veću od nule** i valutu **RSD**. Filter „status“ razdvaja naloge
za koje virman **nije** rađen od onih za koje **jeste**.

#### 8. Primer

| Nalog | Storniran | Virman | Valuta | Zaposleni | Račun | Iznos | Ishod |
|---|---|---|---|---|---|---|---|
| 43/2026-17 | Ne | Ne | RSD | Petrović | 18 cifara | 12.000,00 | **Prolazi** |
| 43/2026-18 | **Da** | Ne | RSD | Jovanović | 18 cifara | 8.000,00 | Odbijen — storniran |
| 43/2026-19 | Ne | Ne | **EUR** | Nikolić | 18 cifara | 300,00 | Odbijen — valuta |
| 43/2026-20 | Ne | Ne | RSD | *(spoljno lice)* | — | 5.000,00 | Odbijen — nema IMS zaposlenog |
| 43/2026-21 | Ne | Ne | RSD | Marković | **16 cifara** | 9.000,00 | Odbijen — račun nije 18 cifara |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Devet provera, sve greške zajedno | Potvrđeno | `virman.py:126-148` |
| Račun mora imati tačno 18 cifara | Potvrđeno | `virman.py:139-140` |
| Samo RSD | Potvrđeno | `virman.py:133-134` |
| Spoljna lica se ne isplaćuju virmanom | Potvrđeno | `virman.py:135-136` |

---

### I-01 — Generisanje datoteke virmana

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Isplata neoporezivih primanja“ |
| Tehnički naziv | `build_virman_file()` |
| Putanja | [`isplate/services/virman.py:195`](../isplate/services/virman.py#L195) |
| Adresa | `/isplate/` |
| Dozvola | Uloga **Blagajna** |

#### 2. Poslovna svrha

Pravi datoteku koju blagajna učitava u elektronsko bankarstvo, da se akontacije za
službena putovanja isplate zaposlenima **bez ručnog kucanja naloga**.

#### 3. Korisnici rezultata

Blagajna. Posredno: banka i zaposleni.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Uloga u datoteci |
|---|---|---|
| Broj računa zaposlenog | `fleet_employee.account_number` | Račun primaoca |
| Ime i prezime | `fleet_employee.original_full_name` ili prikazno ime | Naziv primaoca |
| **Opština boravka** | `fleet_employee.residence_municipality` | Mesto primaoca |
| Iznos akontacije | `fleet_putninalog.advance_payment` | Iznos |
| Broj naloga | `fleet_putninalog.order_number` | Poziv na broj |
| **Datum virmana** | bira korisnik | Datum plaćanja |

#### 5. Poreklo podataka

```
 Sekretarijat ──► putni nalog (akontacija, zaposleni, broj naloga)
 Kadrovska    ──► zaposleni (partija, opština boravka)
 Blagajna     ──► izbor naloga + datum virmana
                          ▼
                 datoteka .txt (cp1250)
                          ▼
                  elektronsko bankarstvo
```

#### 6. Tačan postupak obračuna

##### Oblik datoteke [P]

| Osobina | Vrednost |
|---|---|
| Dužina svakog reda | **tačno 180 znakova** |
| Kodiranje | **cp1250** (neprevodivi znakovi se zamenjuju) |
| Prelom reda | `CRLF`, i na poslednjem redu |
| Zaglavlje | **dva reda** |
| Detalj | jedan red po nalogu |
| Naziv datoteke | `Virman-putni-nalozi-GGGGMMDD-HHMMSS.txt` |

##### Prvi red zaglavlja [P]

| Pozicija | Širina | Sadržaj |
|---|---|---|
| 1 | 18 | Račun platioca |
| 19 | 35 | Naziv platioca |
| 54 | 10 | Mesto platioca |
| 64 | 6 | **Datum virmana** u obliku `DDMMGG` |
| 168 | 13 | `Multi E_BANK0` |

##### Drugi red zaglavlja [P]

| Pozicija | Širina | Sadržaj |
|---|---|---|
| 1 | 18 | Račun platioca |
| 19 | 35 | Naziv platioca |
| 54 | 10 | Mesto platioca |
| 64 | 15 | **Ukupan iznos u parama**, 15 cifara sa vodećim nulama |
| 79 | 5 | **Broj naloga**, 5 cifara sa vodećim nulama |
| 180 | 1 | `9` |

##### Detaljni red [P]

| Pozicija | Širina | Sadržaj |
|---|---|---|
| 1 | 18 | **Račun primaoca** — samo cifre |
| 19 | 35 | **Naziv primaoca** — velikim slovima, bez dijakritika |
| 54 | 10 | **Mesto primaoca** — opština boravka, velikim slovima |
| 64 | 25 | Model `000` |
| 89 | 35 | `NEOPOREZIVA PRIMANJA ZAPOSLENIH` |
| 125 | 5 | Kontrola `00000` |
| 131 | 3 | Šifra plaćanja `241` |
| 136 | 34 | **Poziv na broj** (vidi ispod) |
| 173 | 8 | **Datum plaćanja** u obliku `DDMMGG01` |

##### Poziv na broj — posebno pravilo [P]

Poziv na broj je spoj dve vrednosti, ukupno 34 znaka:

> **13 znakova:** iznos **u parama**, sa vodećim nulama
> **21 znak:** **redni broj putnog naloga**, poravnat **udesno**

Redni broj se dobija iz broja naloga — **deo posle poslednje crtice**:

| Broj naloga | Redni broj u pozivu |
|---|---|
| `43/2026-17` | `17` |
| `12/2026-235` | `235` |

> **[Z] Zašto je iznos i u pozivu na broj:** banka tako može da uporedi iznos naloga sa
> iznosom u pozivu na broj kao dodatnu kontrolu.

##### Pretvaranje iznosa [P]

> iznos u parama = iznos zaokružen na **2 decimale** (`ROUND_HALF_UP`) × 100, kao **ceo broj**

| Iznos | U parama |
|---|---|
| 12.000,00 | `1200000` |
| 12.345,67 | `1234567` |
| 12.345,675 | `1234568` — zaokruženo naviše |

Pojedinačan iznos mora biti **veći od nule**; ukupan iznos ne sme biti negativan. [P]

##### Čišćenje teksta [P]

Naziv i mesto primaoca prolaze kroz:

1. Sažimanje razmaka u jedan.
2. Zamenu srpskih slova: `č`→`c`, `ć`→`c`, `š`→`s`, `ž`→`z`, `đ`→`dj`
   (i velika slova, `Đ`→`DJ`).
3. Uklanjanje svih preostalih znakova koji nisu ASCII.
4. Prevođenje u **velika slova** (samo naziv primaoca).

> **[P]** Mesto primaoca se takođe prevodi u velika slova, ali **posle** čišćenja.
> Ako zaposleni nema unetu opštinu boravka, koristi se **`Beograd`**.

##### Skraćivanje [P]

Svaka vrednost duža od svoje širine se **skraćuje bez upozorenja**.
Naziv primaoca duži od 35 znakova biće odsečen.

##### Posle generisanja [P]

Na svakom obuhvaćenom nalogu se upisuje:

| Polje | Vrednost |
|---|---|
| `virman_generated` | `True` |
| `virman_generated_at` | Trenutak generisanja |
| `virman_generated_by` | Korisnik |

**Ponovno generisanje** je moguće samo uz izričit izbor („Dozvoli ponovno generisanje“). [P]

#### 7. Tehnička implementacija

| Element | Vrednost |
|---|---|
| Fajl | `isplate/services/virman.py` |
| Funkcije | `build_virman_file()`, `build_header_lines()`, `build_detail_line()`, `validate_order_for_virman()` |
| Provera dužine | `_record_to_string()` — prekida ako red nije tačno 180 znakova |
| Ekran | `isplate/views.py: IsplataNeoporezovanihView` |
| Testovi | `isplate/tests.py` — 20 testova |

#### 8. Primer obračuna

> Ilustrativni primer. Datum virmana **15.09.2026.**, dva naloga.

| Nalog | Zaposleni | Račun | Opština | Iznos |
|---|---|---|---|---|
| 43/2026-17 | Petrović Miloš | `160000012345678901` | Novi Beograd | 12.000,00 |
| 43/2026-18 | Đurić Željka | `205000098765432109` | Čukarica | 8.500,50 |

**Ukupno:** 20.500,50 RSD = **2050050 para**, **2 naloga**.

**Prvi red zaglavlja** (skraćeno):

```
205000000001445485Institut IMS a.d.                  Beograd   150926 …  Multi E_BANK0
```

**Drugi red zaglavlja** (skraćeno):

```
205000000001445485Institut IMS a.d.                  Beograd   00000000205005000002 …9
                                                               └──15 cifara──┘└─5─┘
```

**Detaljni red za prvi nalog** (delovi):

| Pozicija | Vrednost |
|---|---|
| 1–18 | `160000012345678901` |
| 19–53 | `PETROVIC MILOS` (dopunjeno razmacima) |
| 54–63 | `Novi Beogr` — **skraćeno na 10 znakova** |
| 89–123 | `NEOPOREZIVA PRIMANJA ZAPOSLENIH` |
| 131–133 | `241` |
| 136–169 | `0001200000` + `000` + 19 razmaka + `17` |
| 173–180 | `15092601` |

**Detaljni red za drugi nalog:**

| Pozicija | Vrednost |
|---|---|
| 19–53 | `DJURIC ZELJKA` — `Đ`→`DJ`, `Ž`→`Z` |
| 54–63 | `Cukarica` — `Č`→`C` |
| 136–169 | `0000850050` + … + `18` |

> Uočite: mesto „Novi Beograd“ ima 12 znakova i **skraćuje se na „Novi Beogr“**,
> bez ikakvog upozorenja. Vidi problem **P-33**.

#### 9. Rezultat

| | |
|---|---|
| Šta predstavlja | Nalog banci za isplatu akontacija |
| Format | `.txt`, fiksna širina, cp1250 |
| Gde se čuva | **Datoteka se ne čuva** — preuzima je korisnik |
| Trag u sistemu | Na svakom nalogu: da je virman rađen, kada i ko |
| Može li se ponoviti | Da, uz izričit izbor |
| Istorija sadržaja | **Ne postoji** — ne čuva se šta je tačno poslato |

> **[Z] Rizik:** ako se datoteka izgubi ili se posle generisanja promeni iznos na nalogu,
> ne postoji način da se utvrdi šta je poslato banci. Postoji samo oznaka **da jeste**.

#### 10. Upotreba rezultata

| Korak | Ko | Šta |
|---|---|---|
| 1 | Blagajna | Bira naloge i datum virmana, preuzima datoteku |
| 2 | Blagajna | Učitava datoteku u elektronsko bankarstvo |
| 3 | Banka | Izvršava plaćanja |
| 4 | Zaposleni | Prima akontaciju na tekući račun |

> **[N] Q3:** nije potvrđeno da li se isplata posle vraća u sistem. Postoji zaseban
> zadatak koji u 12:30 puni polje **„Isplaćeno“** iz `dbo.fleet_zatvoren_putni`, ali
> veza sa ovim virmanom nije uspostavljena u kodu. [P]

#### 11. Kontrola i ručna provera

| Provera | Kako |
|---|---|
| Ukupan iznos | Drugi red zaglavlja, pozicije 64–78, u parama — podeliti sa 100 |
| Broj naloga | Drugi red zaglavlja, pozicije 79–83 |
| Broj redova u datoteci | Mora biti `2 + broj naloga` |
| Dužina reda | **Svaki** red mora imati tačno 180 znakova |
| Iznos pojedinačnog naloga | Pozicije 136–148, u parama |
| Redni broj naloga | Pozicije 149–169, poravnat udesno |
| Račun primaoca | Pozicije 1–18, uporediti sa partijom zaposlenog |

**Kontrolna formula:**

> zbir iznosa iz svih detaljnih redova (pozicije 136–148) = iznos iz zaglavlja (64–78)

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| Nijedan nalog nije izabran | *„Izaberi bar jedan putni nalog.“* | Ispravno |
| Datum virmana nije izabran | *„Izaberi datum virmana.“* | Ispravno |
| **Naziv primaoca duži od 35 znakova** | **Skraćuje se bez upozorenja** | **P-33** |
| **Mesto duže od 10 znakova** | **Skraćuje se bez upozorenja** | **P-33** |
| Zaposleni bez opštine boravka | Koristi se `Beograd` | **P-33** |
| Iznos nula ili negativan | Odbija se | Ispravno |
| Red nije tačno 180 znakova | **Prekida se greškom** pre nastanka datoteke | Ispravno |
| Ponovno generisanje | Moguće uz izričit izbor | Ispravno |
| Znak van cp1250 | Zamenjuje se | Ispravno |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje / problem |
|---|---|---|---|
| Red je tačno 180 znakova | Potvrđeno | `virman.py:10, 64-66` | — |
| Kodiranje cp1250 | Potvrđeno | `virman.py:49` | — |
| Dva reda zaglavlja i njihove pozicije | Potvrđeno | `virman.py:151-169` | — |
| Pozicije detaljnog reda | Potvrđeno | `virman.py:182-192` | — |
| Poziv na broj: 13 cifara iznosa + 21 znak rednog broja | Potvrđeno | `virman.py:97-111` | — |
| Iznos u parama, `ROUND_HALF_UP` | Potvrđeno | `virman.py:83-87` | — |
| Preslovljavanje srpskih slova | Potvrđeno | `virman.py:26-39, 70-76` | — |
| Podrazumevano mesto je Beograd | Potvrđeno | `virman.py:120-124` | — |
| **Skraćivanje bez upozorenja** | **Potvrđeno — problem** | `virman.py:56-60` | **P-33** |
| **Sadržaj datoteke se ne čuva** | **Potvrđeno** | Nema modela | **P-33** |
| Podaci platioca upisani u kod | Potvrđeno | `virman.py:12-23` | **Q30** |

---

### I-03 — Konverzija virmana u JSON

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Konverter“ |
| Tehnički naziv | `convert_virman_txt_to_internal_json()` |
| Putanja | [`isplate/services/converters.py:123`](../isplate/services/converters.py#L123) |
| Adresa | `/isplate/konverter/` |

#### 2. Poslovna svrha

Pretvara **postojeću virman datoteku** (fiksna širina, 180 znakova) u **JSON** oblik,
za sistem koji očekuje takav zapis.

> **[N] Q31:** nije potvrđeno koji sistem koristi ovaj JSON. Nazivi polja
> (`DebtorBankAccount`, `CreditorCodeModel`, `UrgentPayment`) upućuju na drugo
> bankarsko rešenje, ali to nije zabeleženo u kodu.

#### 4. Ulazni podaci

Datoteka `.txt` u jednom od kodiranja: **cp1250**, **UTF-8 sa BOM** ili **UTF-16**.
Redosled provere je upravo takav. [P]

#### 6. Tačan postupak

**Provere [P]:**

| Provera | Poruka |
|---|---|
| Kodiranje je prepoznatljivo | *„TXT fajl nije u podrzanom encoding-u.“* |
| Ima bar 3 reda (2 zaglavlja + 1 detalj) | *„TXT mora imati dva header reda i bar jedan detaljni red.“* |
| **Svaki** red ima tačno 180 znakova | *„Svi redovi moraju imati 180 karaktera. Neispravni redovi: …“* (nabraja prvih 10) |
| Zaglavlje sadrži račun od 18 cifara | *„Header ne sadrzi ispravan racun duznika.“* |
| Poziv na broj ima bar 15 znakova | *„Poziv na broj je prekratak.“* |

Prazni redovi se izostavljaju pre provere. [P]

**Preslikavanje polja [P]:**

| Polje u JSON-u | Izvor — pozicije u redu |
|---|---|
| `CreditorBankAccount` | 1–18, samo cifre |
| `CreditorName` | 19–53 |
| `CreditorAddress` | 54–63 |
| `DebtorCode` | 67–88 |
| `PaymentBasis` | 89–123 |
| `PaymentCode` | 131–133, kao ceo broj |
| `Amount` | poziv na broj, prvih 13 znakova, **podeljeno sa 100** |
| `CreditorCodeModel` | poziv na broj, znakovi 14–15, kao ceo broj |
| `CreditorCode` | poziv na broj, od 16. znaka |
| `ExpectedPaymentDate` | 173–180, `DDMMGG` → **`GGGG-MM-DD`** |
| `DebtorBankAccount` | **iz prvog reda zaglavlja**, pozicije 1–18 |
| `UrgentPayment` | **uvek `True`** |
| `DebtorCodeModel`, `ExternalId`, `UserGroupName` | uvek prazno |
| `UserTags`, `Comment` | uvek prazan tekst |

**Pretvaranje iznosa [P]:** vrednost u parama deli se sa 100; ako je rezultat ceo broj,
zapisuje se kao **ceo broj**, inače kao **decimalan**.

**Godina [P]:** dvocifrena godina se tumači kao **2000 + GG**.

**Naziv izlazne datoteke [P]:** naziv ulazne, sa nastavkom `.json`.

#### 8. Primer

**Ulaz — detaljni red** (delovi):

| Pozicije | Vrednost |
|---|---|
| 1–18 | `160000012345678901` |
| 19–53 | `PETROVIC MILOS` |
| 131–133 | `241` |
| 136–169 | `0001200000` + `97` + `1234567` |
| 173–180 | `15092601` |

**Izlaz:**

```json
{
    "PaymentBasis": "NEOPOREZIVA PRIMANJA ZAPOSLENIH",
    "PaymentCode": 241,
    "Amount": 12000,
    "DebtorBankAccount": "205000000001445485",
    "CreditorName": "PETROVIC MILOS",
    "CreditorBankAccount": "160000012345678901",
    "CreditorCodeModel": 97,
    "CreditorCode": "1234567",
    "UrgentPayment": true,
    "ExpectedPaymentDate": "2026-09-15"
}
```

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Red nije 180 znakova | Prekida se, nabraja prvih 10 neispravnih redova |
| Nepoznato kodiranje | Prekida se |
| **Sve konverzije su „hitne“** | `UrgentPayment` je **uvek `True`** |
| Iznos u pozivu na broj nije broj | *„Neispravan iznos u pozivu na broj: …“* |
| Neispravan datum | *„Neispravan datum placanja: …“* |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Pitanje |
|---|---|---|---|
| Tri podržana kodiranja, tim redom | Potvrđeno | `converters.py:30` | — |
| Preslikavanje pozicija u polja | Potvrđeno | `converters.py:102-120` | — |
| `UrgentPayment` je uvek `True` | Potvrđeno | `converters.py:114` | Potvrditi da je željeno |
| Godina se tumači kao 2000 + GG | Potvrđeno | `converters.py:72` | — |
| **Koji sistem koristi ovaj JSON** | **Nepotvrđeno** | — | **Q31** |

---

### Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-33** | Virman datoteka **skraćuje predugačke vrednosti bez upozorenja** (naziv primaoca preko 35, mesto preko 10 znakova), a **sadržaj poslate datoteke se nigde ne čuva**. Ako se posle generisanja promeni iznos na nalogu, ne postoji način da se utvrdi šta je poslato banci. | **Visoka** |

### Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q30** | Račun platioca, naziv firme i šifra plaćanja **upisani su u kod**. Da li treba da budu podesivi, imajući u vidu da promena računa firme zahteva izmenu i isporuku koda? |
| **Q31** | Koji sistem koristi JSON iz konvertera i da li je `UrgentPayment = true` za **sve** naloge ispravno? |
| **Q32** | Zadatak u 12:30 puni polje „Isplaćeno“ iz `dbo.fleet_zatvoren_putni`, ali nema veze sa generisanim virmanom. Da li se isplata po virmanu negde potvrđuje u sistemu? |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.6. Kadrovi](#66-kadrovi--obračuni) | Ocenjivanje i radne liste |
| [6.7. Mobilna telefonija](#67-mobilna-telefonija--obračuni) | Obustave |
| [4. Baza podataka](#446-putni-nalozi) | Putni nalozi |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema |

---

## 6.11. Ugovori i menice — analize

> Deo poglavlja [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](#10-poznati-problemi-i-ograničenja).

**Analize u ovom poglavlju:**

| Oznaka | Naziv | Problemi |
|---|---|---|
| [U-02](#u-02--sinhronizacija-partnera-iz-finansija) | Sinhronizacija partnera iz finansija | — |
| [U-01](#u-01--provera-statusa-partnera-u-apr-u) | Provera statusa partnera u APR-u | **P-40** |
| [U-03](#u-03--preuzimanje-menica-iz-registra-nbs) | Preuzimanje menica iz registra NBS | **P-41** |
| [U-04](#u-04--povezivanje-menica-i-garancija-sa-ugovorima) | Povezivanje menica i garancija sa ugovorima | — |

---

### U-02 — Sinhronizacija partnera iz finansija

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Sinhronizacija partnera iz Finansija“ |
| Tehnički naziv | `fetch_finance_partners()`, `partner_defaults_from_finance()` |
| Putanja | [`ugovori/services.py:123`](../ugovori/services.py#L123) |
| Adrese | `/ugovori/partneri/sync-finansije/` i paketna obrada |

#### 2. Poslovna svrha

Partneri postoje u **nasleđenom finansijskom šifarniku** (`dbo.partneri`). Ovaj postupak
ih prenosi u evidenciju Ugovora, da bi se ugovori i nabavke vezivali za **isti** partner.

#### 3. Korisnici rezultata

Pravna služba, služba nabavke, komercijala.

#### 4. Ulazni podaci

| Poslovni naziv | Izvorna kolona | Polje u evidenciji |
|---|---|---|
| Šifra partnera | `sif_par` | `external_sif_par` |
| Naziv | `naz_par` | `name` |
| **Grupa** | `grupa` | određuje **tip partnera** |
| Naziv grupe | `naz_grup` | — |
| Ulica | `ulica_par` | `address` |
| Mesto | `mesto_par` | `city` |
| Matični broj | `mb` | `maticni_broj` |
| PIB | `pib` | `pib` |
| Zemlja | `zemlja` | `country`, određuje **rezidentnost** |
| Telefon, e-pošta, kontakt osoba | `telefon`, `email`, `lice` | odgovarajuća polja |

#### 6. Tačan postupak

##### Korak 1 — jedan red po šifri partnera [P]

Isti partner se u izvoru može pojaviti u **više grupa**. Upit bira **jedan** red po šifri,
po redosledu prvenstva grupa:

| Prvenstvo | Grupa | Značenje |
|---|---|---|
| **1** | `1` | Kupci i dobavljači |
| **2** | `10` | Fizička lica |
| **3** | `11`, `13`, `14` | Banke |
| 4 | ostale | Ostalo |

Unutar istog prvenstva bira se **manji broj grupe**. [P]

##### Korak 2 — tip partnera iz grupe [P]

| Grupa | Tip partnera |
|---|---|
| `10` | **Fizičko lice** |
| `11`, `13`, `14` | **Banka** |
| ostale | **Pravno lice** |

##### Korak 3 — rezidentnost [P]

Izvodi se iz polja `zemlja` (`residency_from_country`).

##### Korak 4 — upis

Partner se prepoznaje po **`external_sif_par`** — šifri iz starog sistema. [P]

**Paketna obrada [P]:** prenos ide u delovima (`OFFSET … FETCH NEXT`), sa brojačem
ukupnog broja partnera (`count_finance_partners`), da veliki šifarnik ne blokira ekran.

#### 8. Primer

**Izvor — isti partner u dve grupe:**

| `sif_par` | `grupa` | `naz_par` |
|---|---|---|
| 1234 | **5** | `AUTODEKI DOO` |
| 1234 | **1** | `AUTODEKI DOO BEOGRAD` |

> Bira se red sa grupom **1** (prvenstvo 1) → naziv `AUTODEKI DOO BEOGRAD`,
> tip **Pravno lice**.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `ugovori_partner` |
| Veza sa izvorom | `external_sif_par` |
| Upotreba | Ugovori, ponude, zahtevi, predmeti nabavke, narudžbenice |
| Kontrola | Uporediti broj partnera sa `count_finance_partners()` |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Partner u više grupa | Uzima se red po prvenstvu |
| Partner bez naziva | Naziv postaje `Partner <šifra>` |
| Partner bez šifre | **Ne ulazi** — upit traži `sif_par IS NOT NULL` |
| Partner obrisan iz izvora | **Ostaje** u evidenciji Ugovora |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Jedan red po šifri, po prvenstvu grupa | Potvrđeno | `services.py:155-165` |
| Tip partnera iz grupe | Potvrđeno | `services.py:103-109` |
| Veza je `external_sif_par` | Potvrđeno | `models.py:40-45` |
| Partneri se ne brišu | Potvrđeno | Nema brisanja |

---

### U-01 — Provera statusa partnera u APR-u

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „APR status“, „APR provera“ |
| Tehnički naziv | `update_partners_from_apr()`, `is_active_apr_status()` |
| Putanja | [`ugovori/apr_openapi.py:34`](../ugovori/apr_openapi.py#L34) |
| Adrese | `/ugovori/partneri/<id>/apr-update/`, paketna obrada `/ugovori/partneri/sync-apr/` |

#### 2. Poslovna svrha

Proverava u **javnom registru APR-a** da li je partner i dalje **aktivan** privredni
subjekt, i preuzima zvanično poslovno ime — pre zaključenja ugovora i pre plaćanja.

#### 3. Korisnici rezultata

Pravna služba, služba nabavke, finansije.

#### 4. Ulazni podaci

| Poslovni naziv | Tabela i kolona | Uloga |
|---|---|---|
| **Matični broj** | `ugovori_partner.maticni_broj` | **Jedini osnov povezivanja** |

**Izvor:** `https://openapi.apr.gov.rs/api/opendata/companies` — javni skup podataka,
bez prijave. [P]

#### 6. Tačan postupak

##### Korak 1 — preuzimanje [P]

| Osobina | Vrednost |
|---|---|
| Način | `GET`, odgovor u JSON obliku |
| Kodiranje | `utf-8-sig` |
| Rok | 60 sekundi |
| Koren odgovora | ključ **`Podaci`** |

> **[P] Problem P-40 — zaobilaženje provere potvrde:** ako veza ne uspe zbog SSL greške,
> kod **ponavlja zahtev sa isključenom proverom potvrde** (`verify=False`), uz gašenje
> upozorenja.

##### Korak 2 — normalizacija matičnog broja [P]

> uklone se svi znakovi osim cifara; ako ostane **manje od 8 cifara**, dopuni se
> **vodećim nulama do 8**

| Ulaz | Rezultat |
|---|---|
| `12345678` | `12345678` |
| `1234567` | `01234567` |
| `MB 12345678` | `12345678` |
| prazno | prazno — partner se **preskače** |

##### Korak 3 — određivanje aktivnosti [P]

> partner je aktivan ako je `NazivStatus` **tačno** jednak reči **`активан`**
> (ćirilicom), bez obzira na velika i mala slova

> **[P] Poređenje je tačno, ne „sadrži“.** Status „Активан — у ликвидацији“ ili
> latinično „Aktivan“ **ne bi** bio prepoznat kao aktivan.

##### Korak 4 — šta se upisuje [P]

| Polje | Vrednost |
|---|---|
| `name` | `PoslovnoIme` iz APR-a; ako je prazno — **zadržava se postojeći naziv** |
| `is_active` | Rezultat provere statusa |
| `apr_status` | Izvorni tekst statusa |
| `apr_checked_at` | Trenutak provere |
| `data_source` | `apr_openapi` |
| `data_validated` | **`True`** |
| `data_validated_at` | Trenutak provere |

Upisuju se **samo stvarno promenjena polja**. [P]

##### Korak 5 — brojači [P]

| Brojač | Značenje |
|---|---|
| `checked` | Ukupno provereno |
| `updated` | Nešto je promenjeno |
| `unchanged` | Sve isto |
| `missing_maticni_broj` | **Partner nema matični broj** — preskočen |
| `not_found` | **Nije pronađen u APR-u** |

#### 8. Primer

| Partner | Matični broj | APR `NazivStatus` | `is_active` | Brojač |
|---|---|---|---|---|
| AUTODEKI DOO | `20123456` | `Активан` | **Da** | `updated` / `unchanged` |
| STARI DOBAVLJAČ | `07654321` | `Брисан` | **Ne** | `updated` |
| FIZIČKO LICE | *(prazno)* | — | nepromenjeno | `missing_maticni_broj` |
| NOVI PARTNER | `21999999` | *(nema ga)* | nepromenjeno | `not_found` |

> Za partnere u kategorijama `missing_maticni_broj` i `not_found` **ništa se ne menja** —
> `is_active` ostaje kakav je bio. To je namerno: odsustvo u APR-u nije dokaz gašenja.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `ugovori_partner`: `is_active`, `apr_status`, `apr_checked_at`, `data_validated` |
| Kada se osvežava | **Ručno** — nije u rasporedu zakazanih poslova |
| Kontrola | `apr_checked_at` pokazuje kada je partner poslednji put proveren |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **SSL greška** | **Ponavlja se bez provere potvrde** | **P-40** |
| Partner bez matičnog broja | Preskače se, broji se zasebno | Ispravno |
| Partner nije u APR-u | Ništa se ne menja | Ispravno |
| Status napisan drugačije | **Tretira se kao neaktivan** | **P-40** |
| APR nedostupan | Ceo prenos ne uspeva | Vidljivo |
| Fizičko lice | Nema matični broj — nikad se ne proverava | Očekivano |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Osnov povezivanja je matični broj | Potvrđeno | `apr_openapi.py:84` | — |
| Dopuna vodećim nulama do 8 cifara | Potvrđeno | `apr_openapi.py:31` | — |
| Aktivan samo za tačno `активан` | Potvrđeno | `apr_openapi.py:35` | **P-40** |
| Prazan naziv ne briše postojeći | Potvrđeno | `apr_openapi.py:58` | — |
| **Zaobilaženje provere potvrde pri SSL grešci** | **Potvrđeno** | `apr_openapi.py:40-43` | **P-40** |
| Provera nije zakazana | Potvrđeno | Nije u `EXPECTED_PERIODIC_TASKS` | — |

---

### U-03 — Preuzimanje menica iz registra NBS

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Ažuriraj izlazne menice“ |
| Tehnički naziv | `sync_izlazne_menice()`, `scrape()` |
| Putanja | [`menice/services.py:164`](../menice/services.py#L164), [`menice/scraper.py`](../menice/scraper.py) |
| Adresa | `/menice/izlazna/azuriraj/` |

#### 2. Poslovna svrha

Preuzima podatke o **menicama koje je IMS izdao** iz **Registra menica i ovlašćenja
Narodne banke Srbije**, da bi finansije imale pregled obaveza po menicama bez ručnog
prepisivanja.

#### 3. Korisnici rezultata

Finansije, pravna služba.

#### 4. Ulazni podaci

| Podatak | Podrazumevana vrednost | Napomena |
|---|---|---|
| **Poreski broj (PIB)** | **`100223617`** | PIB Instituta IMS |
| Matični broj | prazno | opciono |
| Serijski broj menice | prazno | opciono |
| Datum registracije | prazno | opciono |
| Veličina strane | 100 | |
| Preuzimanje avalista | **uključeno** | |
| Najviše strana | bez ograničenja | |
| Rok | 30 sekundi | |

**Izvor:** `https://webappcenter.nbs.rs/PnWebApp` — javna pretraga registra menica,
čita se **razlaganjem HTML stranice** (`BeautifulSoup`). [P]

#### 6. Tačan postupak

##### Korak 1 — preuzimanje [P]

Pretraga registra po PIB-u dužnika, strana po strana. Za svaku menicu se opciono
preuzimaju i **avalisti**, sa zasebne adrese.

##### Korak 2 — normalizacija zapisa [P]

Dvadeset polja iz registra se preslikava u evidenciju. Pretvaranje vrednosti:

| Vrsta | Polja | Pravilo |
|---|---|---|
| **Datumi** | datum izdavanja, dospeća, registracije | Oblici `DD.MM.GGGG`, `DD/MM/GGGG`, `GGGG-MM-DD`; prateća tačka se uklanja |
| **Iznosi** | iznos menice, iznos iz osnova | Prepoznaje **oba zapisa decimale** (vidi ispod) |
| **Celi brojevi** | strana rezultata, redni broj, broj avalista | Preko `float`, pa u ceo broj |
| Ostalo | tekst | Očišćen od razmaka; prazno → prazno |

**Prepoznavanje decimalnog zapisa [P]:**

| Ulaz | Tumačenje | Rezultat |
|---|---|---|
| `1.234.567,89` | zarez je poslednji → **evropski** | `1234567.89` |
| `1,234,567.89` | tačka je poslednja → **engleski** | `1234567.89` |
| `1234,89` | samo zarez | `1234.89` |
| `1234.89` | samo tačka | `1234.89` |

##### Korak 3 — prepoznavanje postojeće menice [P]

> **serijski broj** + **datum registracije** *(+ redni broj, ako postoji)*

| Situacija | Postupak |
|---|---|
| Nema serijskog broja **ili** datuma registracije | **Preskače se** (`skipped`) |
| Menica pronađena | Ažuriraju se **samo polja iz registra** |
| Menica nije pronađena | Upisuje se nova |

> **[P] Ključna zaštita:** ažuriraju se **samo polja iz NBS registra** (`NBS_FIELDS`).
> Ručno uneti podaci — **broj ugovora, datum ugovora, OJ, fizička lokacija, napomena,
> interni status** — **ostaju netaknuti**.

##### Korak 4 — brojači [P]

`fetched`, `created`, `updated`, `unchanged`, `skipped`.

#### 8. Primer

| Serijski broj | Datum registracije | Redni broj | Ishod |
|---|---|---|---|
| `AA1234567` | 15.03.2026. | 1 | **Nova** |
| `AA1234567` | 15.03.2026. | 1 | **Bez izmene** *(drugi prolaz)* |
| `AA1234567` | 15.03.2026. | 1, iznos promenjen | **Ažurirano** — ručna polja ostaju |
| *(bez serijskog broja)* | 20.03.2026. | — | **Preskočeno** |

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `menica` (tabela bez prefiksa aplikacije) |
| Kada se osvežava | **Ručno** — nije u rasporedu zakazanih poslova |
| Upotreba | Pregled menica, povezivanje sa ugovorima (U-04) |
| Kontrola | Brojači prolaza; `skipped` ukazuje na nepotpune zapise u registru |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Promena izgleda stranice NBS-a** | **Preuzimanje prestaje da radi** | **P-41** |
| Zapis bez serijskog broja ili datuma registracije | Preskače se | Ispravno |
| Dve menice sa istim ključem | Uzima se **prva po ID-u** | Vidljivo |
| Ručno uneti podaci | **Ne prepisuju se** | Ispravno |
| Menica uklonjena iz registra | **Ostaje** u evidenciji | Namerno — `interni_status` |
| PIB nije zadat | Koristi se **podrazumevani PIB IMS-a iz koda** | **P-41** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor | Problem |
|---|---|---|---|
| Ključ je serijski broj + datum registracije (+ redni broj) | Potvrđeno | `services.py:152-161` | — |
| Ažuriraju se samo polja iz registra | Potvrđeno | `services.py:203`, `NBS_FIELDS` | — |
| Prepoznaju se oba decimalna zapisa | Potvrđeno | `services.py:94-100` | — |
| Nepotpuni zapisi se preskaču | Potvrđeno | `services.py:197-199` | — |
| **PIB IMS-a upisan kao podrazumevana vrednost** | **Potvrđeno** | `services.py:166` | **P-41** |
| **Preuzimanje zavisi od izgleda stranice NBS-a** | **Potvrđeno** | `menice/scraper.py` | **P-41** |

---

### U-04 — Povezivanje menica i garancija sa ugovorima

#### 1. Naziv

| | |
|---|---|
| Naziv na ekranu | „Menice uz ugovor“, „Garancije uz ugovor“ |
| Tehnički naziv | `ContractMenicaLink`, `ContractGuarantee` |
| Putanja | [`ugovori/models.py:738`](../ugovori/models.py#L738), [`ugovori/models.py:816`](../ugovori/models.py#L816) |

#### 2. Poslovna svrha

Ugovor često ima **sredstva obezbeđenja** — menice ili bankarske garancije.
Ova veza pokazuje **koja menica pokriva koji ugovor**, da bi se pri isteku ugovora
znalo šta treba vratiti.

#### 6. Tačan postupak

##### Veza sa menicom [P]

Jedna veza pokazuje na **tačno jednu** menicu, i to na **jednu od dve vrste**:

| Polje | Vrsta menice |
|---|---|
| `menica` | Menica iz registra NBS (izlazna ili ulazna) |
| `ulazna_menica` | Ulazna menica iz sopstvene evidencije |

> **[P] Kontrola:** *„Izaberite tacno jednu menicu.“* — ne sme biti ni nijedna ni obe.

**Prikaz veze [P]** se prilagođava vrsti:

| Podatak | Ako je `menica` | Ako je `ulazna_menica` |
|---|---|---|
| Oznaka | Serijski broj ili `Menica <id>` | Serijski broj |
| Vrsta | Izlazna / ulazna menica | „Ulazna menica“ |
| Partner | Naziv dužnika ili izdavalac | Naziv pravnog lica |
| **Iznos** | `iznos_menice` + valuta | `procenat_iznos` + **jedinica vrednosti** |

> **[P] Pažnja na iznos ulazne menice:** jedinica vrednosti može biti **`RSD`, `EUR`
> ili `PROCENAT`**. Kada je `PROCENAT`, vrednost **nije novčani iznos** nego procenat
> vrednosti ugovora. Sabiranje te kolone bez provere jedinice daje besmislen zbir.

Brisanje menice je **zabranjeno** dok postoji veza (`PROTECT`). [P]

##### Garancija uz ugovor [P]

| Polje | Sadržaj |
|---|---|
| `guarantee_number` | Broj garancije |
| `issuer` | Izdavalac / banka |
| `beneficiary` | Korisnik garancije |
| `amount`, `currency` | Iznos i valuta |
| `valid_from`, `valid_to` | Period važenja |
| `status` | **Aktivna / Vraćena / Istekla / Stornirana** |

**Kontrola [P]:** *„Datum 'Vazi do' ne sme biti pre datuma 'Vazi od'.“*

##### Oznake na ugovoru [P]

Ugovor ima tri zasebne oznake: `has_incoming_menice`, `has_outgoing_menice`,
`has_guarantees`.

> **[Z]** To su **ručne oznake**, nezavisne od stvarno povezanih zapisa. Sistem ih
> **ne usklađuje automatski** — ugovor može imati povezanu menicu, a oznaku isključenu.

#### 8. Primer

| Ugovor | Veza | Vrsta | Partner | Iznos |
|---|---|---|---|---|
| U-2026/15 | Menica `AA1234567` | Izlazna menica | AUTODEKI DOO | 500.000,00 RSD |
| U-2026/15 | Ulazna menica `BB7654321` | Ulazna menica | GRADNJA DOO | **10,00 Procenat** |
| U-2026/15 | Garancija `G-2026-7` | — | Banka Poštanska | 1.000.000,00 RSD, do 31.12.2026. |

> Druga stavka je **10% vrednosti ugovora**, ne 10 dinara.

#### 9–11. Rezultat, upotreba i kontrola

| | |
|---|---|
| Gde se čuva | `ugovori_contract_menica_link`, `ugovori_contract_guarantee` |
| Trag | Ko je i kada uspostavio vezu |
| Upotreba | Detalj ugovora; pregled pri isteku ugovora |
| Kontrola | Uporediti oznake na ugovoru sa stvarnim vezama |

#### 12. Izuzeci i rizični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Izabrane obe vrste menice ili nijedna | Odbija se |
| Brisanje povezane menice | **Zabranjeno** |
| Ista menica na više ugovora | **Dozvoljeno** — nema zabrane |
| Iznos u procentima | Prikazuje se sa jedinicom, **ne sme se sabirati sa dinarima** |
| Oznake na ugovoru netačne | **Nema provere** |

#### 13. Status pouzdanosti

| Tvrdnja | Status | Izvor |
|---|---|---|
| Tačno jedna menica po vezi | Potvrđeno | `models.py:780-782` |
| Brisanje povezane menice je zabranjeno | Potvrđeno | `models.py:745-760` (`PROTECT`) |
| Jedinica vrednosti može biti procenat | Potvrđeno | `menice/models.py:96-102`, `models.py:808-812` |
| Kontrola perioda garancije | Potvrđeno | `models.py:888-890` |
| **Oznake na ugovoru su ručne** | **Zaključeno** | Nema usklađivanja u kodu |

---

### Novi problemi iz ovog poglavlja

| # | Opis | Ozbiljnost |
|---|---|---|
| **P-40** | Provera partnera u APR-u **zaobilazi proveru SSL potvrde** kada prvi pokušaj ne uspe (`verify=False`), i prepoznaje kao aktivan **samo tačan tekst `активан`** — svaki drugi zapis statusa vodi u `is_active = False`. | **Srednja** |
| **P-41** | Preuzimanje menica zavisi od **izgleda HTML stranice NBS-a** i koristi **PIB Instituta upisan u kod** kao podrazumevanu vrednost. Promena stranice zaustavlja preuzimanje bez jasne poruke. | **Srednja** |

### Nova pitanja iz ovog poglavlja

| # | Pitanje |
|---|---|
| **Q38** | Koje sve vrednosti `NazivStatus` vraća APR? Ako postoje oblici poput „Активан — у ликвидацији“, sadašnja provera bi ih označila kao **neaktivne**. |
| **Q39** | Treba li preuzimanje menica iz NBS-a i provera partnera u APR-u da budu **zakazani poslovi**, umesto ručnog pokretanja? |
| **Q40** | Da li oznake „Ima ulazne menice / izlazne menice / garancije“ na ugovoru treba da se **usklađuju automatski** sa stvarno povezanim zapisima? |

---

### Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.9. Nabavka](#69-nabavka--obračuni-i-analize) | Predmeti nabavke i fakture |
| [4. Baza podataka](#49-ugovori--ugovori) | Tabele Ugovora i Menica |
| [7. Integracije](#7-integracije) | APR i NBS |
| [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) | Registar problema |

---

## 6.12. Flota — analitika namene, raspolaganja i ekonomskih alternativa

> Metodologija **IMS-FLOTA-2.1**, 21.09.2026.
> Korisnik je pisano odobrio: trošak prati šifru posla vozila, vlasništvo je
> podrazumevano bez važećeg ugovora, namena može biti procena, iznos se vodi na
> samom lizingu/najmu uz razliku mesečni/ukupni, a zastoji nisu potreban ulaz.
> Pravila 2.1 zamenjuju prethodnu raspodelu prema poslu putnog naloga i obaveznu
> istoriju VehicleHolding / odvojene periode LeaseChargePeriod.

### E-01 — Zajednička analitika flote i vozila

#### E-01.1. Naziv i prikaz

Ekrani `/analitika/`, statistika centra i kartica **Troškovi** na detalju vozila
koriste isti `fleet.services.economics.period_analysis()`.
Naziv zbira je **Obuhvaćeni troškovi**, ne ukupan trošak vlasništva.

Kartica Troškovi ima tri celine: rezultat obračuna; ugovori lizinga/najma;
izvorne stavke. Izbor perioda nudi ovaj mesec, poslednja tri meseca, poslednjih
12 meseci, ovu i prošlu godinu, kao i proizvoljne datume. Upozorenja su vidljiva.
Razrada po poslovima i mesecima i pojedinačne stavke otvaraju se po potrebi.
Metodologija se prikazuje na jednoj stranici `/analitika/metodologija/`.

Ekran **Namena i kriterijumi** sadrži procenu namene, obrazac za potvrđen profil,
istoriјu dodela šifre posla i veze na postojeće ugovore. Nema dodatnog obrasca
za ugovornu naknadu, posao putnog naloga ili neupotrebljivost.
Pregled ulaza ima šest stavki: namena, raspolaganje, ugovorni iznos/kamata,
kilometraža, šifra posla vozila i opcion kontrolni prag. Procena namene je
posebno označena i ne blokira obračun.

Ugovor prikazuje zasebno **mesečni iznos** i **ukupno za ugovor**. Ako je unet
mesečni iznos, ukupno je izvedeno po kalendarskim danima važenja. Ukupni iznos
se ne predstavlja kao mesečna rata. Preostala obaveza računa se za preostali
period ugovora, uključujući različite dužine meseci; nije dug jer se uplate
ne prate. Iznos se uređuje neposredno na ekranu postojećeg ugovora.

#### E-01.2. Poslovna svrha

Prikazati evidentirane troškove i pripisati ih šifri posla na koju se vozilo
vodilo na odgovarajući datum. Posebna procena E-02 poredi buduće alternative.

#### E-01.3. Korisnici i dozvole

Uprava, služba voznog parka i korisnici sa dozvolama za odgovarajuće rute.
Nove rute nisu dodate. Koriste se `fleet_analytics`, `center_statistics`,
`vehicle_analysis_settings`, `vehicle_assessment_create` i
`vehicle_assessment_detail`; unos ugovora koristi `lease_create` / `lease_update`.
`sync_permission_codes` izvodi dozvole analitike iz postojećih dozvola za
pregled i izmenu vozila. Kontrola centra na analitici prati sadašnje zaduženje;
prikaz istorijskog centra uzima dodelu na kraju izabranog perioda.

#### E-01.4. Ulazni podaci

| Ulaz | Izvor | Pravilo |
|---|---|---|
| Šifra posla vozila | JobCode + OrganizationalUnit | Poslednja dodela čiji datum nije posle obračunskog dana |
| Raspolaganje | Lease | Jedan važeći ugovor za dan; bez ugovora vlasništvo IMS |
| Naknada lizinga/najma | Lease.current_payment_amount + payment_basis | monthly ili total, za period samog ugovora |
| Kamata finansijskog lizinga | LeaseInterest | Godišnji iznos, samo za dane važećeg ugovora |
| Namena | VehicleAnalysisProfile ili početna procena | Potvrđen profil ima prednost |
| Gorivo | NIS/OMV ili izabrani FuelConsumption | Samo jedan izvor po datumu |
| Održavanje | ServiceTransaction + Requisition | Iznosi na datum dokumenta, uključujući storna |
| Premije | Policy | Premija i oba datuma važenja |
| Naknade osiguranja | Insurance, kola=True | Poseban priliv |
| Kilometraža / korišćenje | Gorivo + VehicleTravelOrder | Očitavanja i administrativni dani naloga |

VehicleHolding, LeaseChargePeriod i VehicleDowntime ostaju sačuvani radi
istorije, ali ne određuju obračun 2.1. `VehicleTravelOrder.job_code` takođe
ne određuje pripadnost troška vozila. U analitici se ne traži popunjavanje tih
podataka. Postojeći zapisi se ne brišu.

#### E-01.5. Poreklo i početna procena

NIS/OMV koriste postojeće filtere proizvoda i OMV duplikata preko
`get_vehicle_fuel_transaction_rows()`. Bez profila izvor goriva je NIS/OMV.
Nabavka služi kao dokaz; njene fakture ne sabiraju se ponovo sa servisima.

Početna namena se izvodi pri prikazu, bez masovnog upisa potvrđenih profila:
priključna kategorija daje priključno vozilo; opis i naziv dodeljene šifre posla
mogu predložiti laboratorijski prevoz, nadzor, upravu, transport, bušenje ili
vuču. Bez posebnog signala početna procena je nadzor i terenski rad.
Procena je označena na detalju i listi i može se promeniti unosom profila.
Težina vozila i ime zaposlenog nisu dokaz namene. Procena ne stvara kontrolne
pragove i ne predstavlja potvrdu istorijske namene.

Migracija `0078_lease_payment_basis` dodaje značenje iznosa na Lease i
razvrstava postojeće operativne ugovore kao ukupni iznos, a dugoročne najmove
kao mesečni, prema postojećim uputstvima unosa i dogovoru 21.09.2026.
Postojeći novčani iznosi i datumi se ne menjaju. Finansijski iznosi ostaju bez
pretpostavljenog značenja, a obračun i dalje koristi samo zasebnu kamatu.

#### E-01.6. Tačan postupak

Period je zatvoren interval, oba krajnja datuma uključena, bez budućnosti i
najviše 1096 dana razlike. Neispravan filter se ne zamenjuje drugim periodom.

**Obuhvaćeni troškovi:**

`gorivo + servisi + trebovanja + premije perioda + naknade perioda + kamata perioda`

Nabavna vrednost, glavnica, amortizacija i kreditna kamata nisu automatski u
zbiru. Naknade osiguranja prikazuju se zasebno; dodatni saldo je zbir minus
naknade. Negativan saldo nije profit vozila. Gorivo je bruto, ostalo je u
poreskoj osnovi izvora.

**Raspolaganje po danu:** važeći Lease određuje finansijski/operativni lizing
ili najam. Ako ga nema, dan je vlasništvo IMS, uključujući dane pre i posle
ugovora. Više važećih ugovora je konflikt: naknade za te dane se ne sabiraju,
a konflikt je prikazan. Poseban unos osnova vlasništva nije potreban.

**Mesečna naknada:** `iznos / broj dana konkretnog kalendarskog meseca` za svaki
obuhvaćeni dan ugovora. **Ukupni iznos:** `iznos / broj dana ugovora`.
Polisa: `premija / broj dana polise` za svaki dan preklapanja.
Finansijska kamata: `godišnja kamata / 365 ili 366`, samo tokom ugovora.
Nedostajući iznos ili značenje iznosa ne zamenjuje se nulom. Poznata nula ostaje nula.

**Raspodela na poslove:** gorivo, servis i trebovanje pripadaju šifri posla
vozila na datum dokumenta. Dnevni deo polise, ugovorne naknade i kamate pripada
šifri važećoj tog dana. Nova dodela važi od svog datuma, prethodna do dana pre
nje. Buduća dodela se ne primenjuje unazad. Prazna dodela ne vraća prethodnu.
Bez dodele, trošak tog dana ostaje neraspoređen. Troškovi se više ne dele
ravnomerno na sve dane celog izabranog perioda. Putni nalozi, njihovi poslovi,
otvaranje/zatvaranje i preklapanja ne menjaju raspodelu. Ovo je analitička
raspodela, bez izmene izvornog knjiženja.

**Kilometraža (dopuna 21.09.2026):** za početak i kraj perioda usvajaju se
najbliži stvarni datumi očitavanja iz NIS/OMV i naloga zaduženja, uključujući
datume van perioda. Ranija evidencija goriva dopunjava dane bez direktnog
očitanja; izbor izvora troška ne ograničava izbor očitanja. Pozitivno OMV
korigovano stanje ima prednost. Na isti dan koristi se najveće stanje.
Kod jednake udaljenosti bira se raniji početak i kasniji kraj. Nema
interpolacije, ekstrapolacije ni skrivenog ograničenja udaljenosti; stvarni
datumi, stanja, izvori i odstupanje u danima prikazani su uz rezultat.
`nearest_period` bira granice, a `observed_timeline` proverava padove između
njih. Dva različita datuma su obavezna; za jednodnevni zahtev nema razlike km.
RSD/km postoji uz pozitivnu razliku bez pada brojača. Ako granice odstupaju,
rezultat je označen kao približan. Troškovi ostaju isključivo u traženom periodu.
Dani naloga su unija dana administrativnog zaduženja; nisu produktivnost.
Dan primopredaje pripada novom nalogu. RSD/dan po nalogu je trošak celog
perioda podeljen jedinstvenim danima naloga. Ovi pokazatelji su odvojeni od
pripadnosti troška. Evidencija neupotrebljivosti se ne prikazuje niti traži.

Sve operacije koriste Decimal; prikaz je na dve decimale. Zbir poslova i
neraspoređenog dela kontroliše se pre prikaznog zaokruživanja.
Ponderisani RSD/km flote koristi vozila sa obračunatim RSD/km i može biti približan.

#### E-01.7. Implementacija

- Obračun: `fleet/services/economics.py`.
- Podrazumevana namena i raspolaganje: `fleet/support/analysis_defaults.py`.
- Dnevni iznos i suma perioda ugovora: `fleet/support/lease_costs.py`.
- Unos iznosa: postojeći LeaseForm i forma prvog unosa vozila.
- Regresije: `fleet/test_economics.py`, `fleet/test_analysis_defaults.py`.

#### E-01.8. Kontrolni primer

01–31.01.2026: gorivo 1.000 RSD 1. januara i 2.100 RSD 31. januara.
Šifra P1 važi od 1. januara, P2 od 16. januara. Bez ijednog putnog naloga:
P1 dobija **1.000**, P2 **2.100**, neraspoređeno **0 RSD**.

Ako uz to postoji mesečna naknada 31.000 RSD za ceo januar, P1 dobija još
**15.000**, P2 još **16.000 RSD**. Samo naknada ugovora koji počinje
16. januara iznosi **16.000 RSD**, a 31. januar pojedinačno **1.000 RSD**.

Naknada 31.000 RSD mesečno od 16.01. do 15.03.2024: 16.000 + 31.000 +
15.000 = **62.000 RSD**, uključujući prestupni februar. Ukupna ugovorna
naknada 31.000 RSD za 01–31.01.2026 daje isti dnevni iznos 1.000 RSD.

Kilometraža za januar: očitavanja 31.12.2025 = 1.000 km, 15.01.2026 =
1.500 km, 01.02.2026 = 2.000 km. Usvajaju se 31.12. i 01.02, razlika je
**1.000 km**, približno za januar. Ako su računi 9.000, 100 i 8.000 RSD na
tim datumima, januarski trošak ostaje **100 RSD**, približni RSD/km **0,10**.

#### E-01.9. Rezultat

Istorijska analitika se računa iz tekuće evidencije; korekcija izvora menja
rezultat. Potvrđeni profili imaju datume važenja. Procene E-02 čuvaju snimak.

#### E-01.10. Kriterijumi

Prag je opcion i traži pisan osnov i uporedivo raspolaganje. Ne primenjuje se
na procenjenu namenu bez profila, mešovite profile, konfliktne ugovore ili
nepotpun ugovorni iznos. Prekoračenje je signal za pregled, ne automatski otpis.
Bušeći sklop i prikolica nemaju RSD/km kao merodavan kriterijum opravdanosti.

#### E-01.11. Kontrola

1. Isti period na floti i vozilu daje isti zbir.
2. Zbir meseci odgovara periodu.
3. Zbir poslova i neraspoređenog dela odgovara periodu.
4. Promena posla na datum dokumenta prebacuje taj trošak na novu šifru.
5. Ugovor bez istorije raspolaganja i bez posebne naknade radi neposredno.
6. Dva ugovora za isti dan se ne sabiraju.
7. Proveriti da usluge uključene u najam nisu ponovljene u servisima/polisama.

#### E-01.12. Ograničenja

Podrazumevano vlasništvo je dogovoreno pravilo analitike, ne rekonstrukcija
pravnog sticanja. Datum otpisa nema istoriju. Izostanak evidentiranog troška
nije dokaz da troška nije bilo. Nema automatske procene prihoda posla,
produktivnih sati, tržišne vrednosti ili troška posebne mašine/ekipe.
Ograničenja centara prate današnje zaduženje; vozilo bez dodele ostaje vidljivo.
Izbor centra prikazuje vozila dodeljena centru na kraju izabranog perioda,
a raspodela poslova tih vozila i dalje prati stvarne istorijske dodele.

#### E-01.13. Status pouzdanosti

Pravila 2.1 potvrđena su korisnikom 21.09.2026. Računanje je pokriveno
kontrolnim primerima i testovima; potpunost poslovnih izvora time nije potvrđena.
Procena namene je jasno odvojena od potvrđenog profila i ne upisuje se kao
potvrđen istorijski podatak.

### E-02 — Sačuvano poređenje budućih alternativa

Procena ima jedan datum, horizont 1–20 godina, realnu diskontnu stopu, planirane km
i dane, isti obuhvat posla i navedene izvore. Unose se najmanje dve alternative,
od kojih je tačno jedna zadržavanje. Izvodljivost svake alternative potvrđuje korisnik.

Vrste: zadržavanje, kupovina/zamena, lizing/najam i spoljna usluga. Finansijski lizing
se za ekonomsku procenu modeluje kroz uporedivu nabavku sredstva, a njegov plan
plaćanja ostaje zasebno pitanje likvidnosti.

Za svaku alternativu unose se `C0` (početna vrednost/izdatak), `A` (isti godišnji
trošak u današnjim cenama) i `S` (neto preostala vrednost na kraju).
Kod zadržavanja `C0` je današnja tržišna vrednost, ne istorijska nabavna vrednost.
Nema sabiranja pune nabavke, amortizacije i otplate iste glavnice.

Za `n` godina i realnu diskontnu stopu `r`:

```
faktor = zbir [1 / (1 + r)^t], t = 1 ... n
PV = C0 + A × faktor − S / (1 + r)^n
EAC = PV / faktor
```

Pri r = 0 faktor je n. Godišnji izdaci i preostala vrednost pripadaju kraju godine.
Model ne raspoređuje zasebne vanredne izdatke po godinama i ne obračunava inflaciju,
poreske štitove ili kurs. Korisnik usaglašava obuhvat i osnovu iznosa svih alternativa.
Nije plan otplate kredita ili finansijskog lizinga.

Rangiraju se samo izvodljive alternative. Bez izvodljivog zadržavanja i najmanje
još jedne izvodljive alternative nema preporuke zamene. EAC/km i EAC/dan koriste
isti planirani godišnji obim za sve opcije. Razlika prema zadržavanju nije garantovana
ušteda; važi samo pod navedenim pretpostavkama.

**Kontrolni primer:** 5 godina, r=0. Zadržavanje: C0=1.000.000, A=300.000,
S=200.000 RSD. PV=2.300.000, EAC=460.000 RSD/god.
Najam: C0=0, A=400.000, S=0. PV=2.000.000, EAC=400.000 RSD/god.
Razlika je **60.000 RSD/god.** u korist najma ako je on izvodljiv i istog obuhvata.

`VehicleEconomicAssessment.snapshot` čuva sve ulaze scenarija, formule/metodologiju,
rezultat, verziju i preporuku. Naknadne izmene vozila ne menjaju sačuvani rezultat.
Za osetljivost na manji/veći obim rada pravi se nova procena sa izmenjenim ulazima.
Preporuka ne menja `Vehicle.otpis` i ne izvršava poslovne procedure.

### Uvođenje i prelaz sa ranije analitike

1. Isporučiti kod i primeniti migraciju `0077_vehicletravelorder_job_code_leasechargeperiod_and_more` u planiranom okruženju.
2. Pokrenuti `sync_permission_codes`: nove rute nasleđuju odgovarajuće dozvole pregleda/izmene vozila.
3. Za svako vozilo potvrditi istoriju raspolaganja, namenu i izbor izvora goriva.
4. Potvrditi periode i značenje naknada ugovora; ništa se ne izvodi iz nejasne stare rate.
5. Dopuniti šifre posla na nalozima i početi evidenciju stvarnih zastoja.
6. Pripremiti tržišne procene i uporedive ponude za E-02.

Nasleđene funkcije `vehicle_cost_per_km_rows()` i pragovi po masi ostaju radi
kompatibilnosti postojećeg koda/testova; nova `/analitika/`, statistika centra i
analitika na vozilu ih ne koriste. Statistika centra sada prikazuje isti obračun
sa filtrom istorijske dodele na kraju izabranog perioda i dozvolom `center_statistics`.

---

## 7. Integracije

> **Za koga je ovo poglavlje:** programeri i održavanje.
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 7.1. Pregled

IMS ERP razmenjuje podatke sa **devet spoljnih sistema**, na **pet različitih načina**:

| Način | Sistemi | Rizik |
|---|---|---|
| **Povezani server (SQL)** | `PUTGEO-SERVER` (dve baze), `INFORMATIKA23`, `SERFIN` | Nedostupnost servera zaustavlja modul |
| **Automatsko preuzimanje sa portala (Selenium)** | NIS, OMV | **Promena izgleda stranice zaustavlja preuzimanje** |
| **Čitanje web stranice (HTTP + HTML)** | Registar menica NBS | Isti rizik |
| **Programski interfejs (HTTP + JSON)** | APR OpenAPI | Najstabilnije |
| **Ručni uvoz datoteka** | RFZO, operater mobilne telefonije, Excel planovi | Zavisi od oblika datoteke |
| **Izvoz datoteke** | Banka | — |

```
 ┌── ULAZ ─────────────────────────────────────────────────────┐
 │                                                             │
 │  cards.nis.rs ──────────Selenium───────┐                    │
 │  fleet.omv.com ─────────Selenium───────┤                    │
 │  webappcenter.nbs.rs ───HTTP+HTML──────┤                    │
 │  openapi.apr.gov.rs ────HTTP+JSON──────┼──► IMS ERP         │
 │  RFZO Excel ────────────ručni uvoz─────┤                    │
 │  Operater Excel ────────ručni uvoz─────┤                    │
 │  Excel planovi ─────────ručni uvoz─────┘                    │
 │                                                             │
 │  PUTGEO-SERVER.bazaims ────┐                                │
 │  PUTGEO-SERVER.bazaldims ──┼── SQL (povezani server)        │
 │  INFORMATIKA23.ID ─────────┤                                │
 │  SERFIN.bazaldims ─────────┘                                │
 └─────────────────────────────────────────────────────────────┘
                              │
 ┌── IZLAZ ─────────────────────────────────────────────────────┐
 │  Banka ◄──── datoteka virmana (180 znakova, cp1250)          │
 │  Obračun zarada ◄──── CSV obustava mobilnih                  │
 └──────────────────────────────────────────────────────────────┘
```

---

### 7.2. Povezani serveri (SQL)

> **Najvažnija zavisnost sistema.** Finansije i Kadrovi **ne rade** bez njih.

#### 7.2.1. `PUTGEO-SERVER` — knjigovodstvo i zarade

| Baza | Objekti | Ko čita | Kada |
|---|---|---|---|
| **`bazaims`** | `nalog_z`, `posao`, `konto`, `ob_jedin`, `partner` | `finansije/services/source.py` | Svaki sat u :20, dnevno 03:50 |
| `bazaims` | `posao_mes`, `blokraspodela`, `tipnal`, `vrsta_naloga`, `pdv_arhiva` | `finansije/services/shared_costs.py`, `cash_flow.py` | **Pri otvaranju ekrana** |
| `bazaims` | `posao` | `potrazivanja/services/source.py` | Uz sinhronizaciju |
| **`bazaldims`** | `element` | `finansije/services/cash_flow.py` | Pri otvaranju |
| `bazaldims` | `Zarada`, `PomLD`, `Radnik` | `finansije/services/job_people.py` | Pri otvaranju |
| **`BazaLDIMS`** | `Godmor`, `GodmorKor` | `hr/services/annual_leave.py` | **Ručno** |

> **[P] Samo `SELECT` upiti.** Nijedan modul ne piše u ove baze.

#### 7.2.2. `INFORMATIKA23.ID` — sistem kontrole pristupa

| Objekat | Sadržaj | Ko čita |
|---|---|---|
| `Radnici` | Radnici u sistemu kontrole pristupa | `hr/services/attendance.py` |
| **`C_Prolasci_Radnika`** | **Pojedinačni prolasci** | Radna lista |
| `C_Tasteri` | Šifarnik tastera | Radna lista |
| `c_parovi_radnika_detalji` | Već uparena trajanja | Komanda `hr_attendance_summary` |

Čita se **pri svakom otvaranju radne liste**. [P]

#### 7.2.3. `SERFIN.bazaldims` — kadrovska

| Objekat | Sadržaj |
|---|---|
| `radnik` | OJ i ime, uz uparena trajanja |

#### 7.2.4. Šta se dešava kada server nije dostupan [P]

| Modul | Ponašanje |
|---|---|
| **Kadrovi — radna lista** | Ekran radi; sati prikazani kao „—“, uz poruku *„Izvor prolazaka trenutno nije dostupan.“* |
| **Kadrovi — godišnji odmori** | Sinhronizacija ne uspeva; postojeći podaci ostaju |
| **Finansije — prihodi i rashodi** | **Rade** — čitaju lokalnu kopiju |
| **Finansije — ZT, tok gotovine, zaposleni** | **Ne rade** — greška na tom delu ekrana |
| **Finansije — sinhronizacija** | Ne uspeva; postojeći podaci ostaju |

> **[P] Dobro rešeno:** greška jednog izvora na kartici posla **ne uklanja** pokazatelje
> iz drugih izvora — svaki tab se učitava zasebno i nudi ponovni pokušaj.

---

### 7.3. Nasleđeni pogledi u bazi `IMS_ERP`

**37 objekata**, čitaju se preko aliasa `server_db`.
Potpun spisak: [4.12. Nasleđeni objekti baze](#412-nasleđeni-objekti-baze-dbo).

> **[P]** Deo tih pogleda **interno prelazi na `PUTGEO-SERVER`**, pa „lokalno“ ne znači
> ni brzo ni nezavisno.

#### Procedura `IMS_ERP.dbo.sp_AzurirajNalogZ` [P]

Jedina procedura koju sistem pokreće. Detaljno:
[4.12.4](#4124-procedura-ims_erpdbosp_azurirajnalogz).

| Osobina | Vrednost |
|---|---|
| Pokreće je | `finansije/services/nalog_z.py` |
| Kada | 10:00 i 11:00 (`Europe/Belgrade`), ili ručno |
| Zaštita | `sp_getapplock` u **istoj sesiji** koja pokreće proceduru |
| Rok | 900 s (`FINANSIJE_NALOG_Z_TIMEOUT`) |
| Istorija | `finansije_nalogzrefreshrun` |

**Procedure koje se NE pokreću [P]:** `SPFINizv52`, `53`, `55`, `52nt`, `SPLdKnjizenje`.
Njihova pravila su **prepisana u Python**.

---

### 7.4. NIS i OMV — gorivo (Selenium)

#### 7.4.1. Kako radi [P]

```
 1. Prijava na internu mrežu    https://control.ims.rs:4081
 2. Pokretanje pregledača       Chrome (chrome-for-testing)
 3. Prijava na portal           cards.nis.rs  /  fleet.omv.com
 4. Preuzimanje datoteke        CSV / Excel u lokalni direktorijum
 5. Obrada datoteke             pandas / openpyxl
 6. Upis                        TransactionNIS / TransactionOMV + FuelConsumption
 7. Čišćenje duplikata          cleanup_omv_fuel_data(apply=True)   ← samo OMV
```

| Portal | Adresa | Zadatak | Vreme | Red |
|---|---|---|---|---|
| **NIS** | `https://cards.nis.rs` | `fleet.tasks.run_nis_command` | 04:20 | `selenium` |
| **OMV putnička** | `https://fleet.omv.com/FleetServicesProduction` | `fleet.tasks.run_omv_putnicka_command` | 05:10 | `selenium` |
| **OMV teretna** | isti | `fleet.tasks.run_omv_teretna_command` | 06:10 | `selenium` |

**Zaključavanje:** Redis, **4 sata**. [P]

#### 7.4.2. Ručni uvoz kao zamena [P]

Ako automatsko preuzimanje ne uspe, datoteka se može uvesti ručno:

| Ekran | Šta prima |
|---|---|
| `/import-nis-excel/` | NIS Excel |
| `/import-omv-putnicka-csv/` | OMV CSV, putnička |
| `/import-omv-teretna-csv/` | OMV CSV, teretna |

#### 7.4.3. Rizici [P]

| Rizik | Opis |
|---|---|
| **Promena izgleda stranice** | Selenium traži elemente po izgledu — promena zaustavlja preuzimanje |
| **Isticanje lozinke** | Prijava ne uspeva; posao pada uz grešku u `TaskHistory` |
| **Mrežni portal** | Bez prijave na `control.ims.rs` nema pristupa internetu |
| **Chrome verzija** | Mora odgovarati upravljaču (`chrome-for-testing` u projektu) |
| **Duplikati OMV** | Rešeno čišćenjem pri uvozu i filterom pri čitanju — vidi [V-06](#62-flota--obračuni-goriva) |

> **[N] Q7:** gde se čuvaju pristupni podaci za portale i ko ih obnavlja nije zabeleženo.

---

### 7.5. Registar menica NBS

| | |
|---|---|
| Adresa | `https://webappcenter.nbs.rs/PnWebApp` |
| Način | `requests` + `BeautifulSoup` — **čitanje HTML stranice** |
| Pokretanje | **Ručno**, sa ekrana `/menice/izlazna/azuriraj/` |
| Pretraga po | PIB dužnika (podrazumevano **PIB IMS-a, upisan u kod**) |
| Preuzima | 20 polja o menici + **avalisti** sa zasebne adrese |
| Rok | 30 s |

**Rizik [P]:** promena izgleda stranice zaustavlja preuzimanje — [P-41](#10-poznati-problemi-i-ograničenja).

---

### 7.6. APR OpenAPI

| | |
|---|---|
| Adresa | `https://openapi.apr.gov.rs/api/opendata/companies` |
| Način | `GET`, odgovor u JSON obliku, kodiranje `utf-8-sig` |
| Prijava | **Nije potrebna** — javni skup podataka |
| Pokretanje | **Ručno**, pojedinačno ili paketno |
| Osnov povezivanja | **Matični broj**, dopunjen vodećim nulama do 8 cifara |
| Preuzima | `PoslovnoIme`, `NazivStatus` |
| Rok | 60 s |

**Rizici [P]:**

| Rizik | Opis |
|---|---|
| **Zaobilaženje SSL provere** | Pri SSL grešci zahtev se ponavlja sa `verify=False` — [P-40](#10-poznati-problemi-i-ograničenja) |
| **Uzak uslov statusa** | Aktivan samo za **tačno** `активан` — svaki drugi zapis daje „neaktivan“ |

---

### 7.7. Ručni uvoz datoteka

| Izvor | Oblik | Ekran / komanda | Učestalost |
|---|---|---|---|
| **RFZO — bolovanja** | `.xlsx` | `/hr/bolovanja/uvoz/` | Mesečno |
| **Operater — paketi** | Excel | `/mobilni/import/` | Po potrebi |
| **Operater — korisnici** | Excel | isto | Po potrebi |
| **Operater — dodele** | Excel, **uz godinu i mesec** | isto | Mesečno |
| **Operater — potrošnja** | Excel, **uz godinu i mesec** | isto | Mesečno |
| **Plan javnih nabavki** | `.xlsx` | `/nabavka/javne-nabavke/uvoz/` | Pri izmeni plana |
| Garažni zahtevi | Excel | `import_garage_requests_excel` | Jednokratno |
| Ugovori | Excel | `import_contracts_excel` | Jednokratno |
| Menice (ulazne i izlazne) | Excel | `import_*_menice_excel` | Jednokratno |
| Šifarnik ocenjivanja | Excel | `import_evaluation_catalog` | Po izmeni |
| Šifarnik elemenata radne liste | Excel | `import_work_time_catalog` | Po izmeni |
| Opomene (Potraživanja) | Excel | `/potrazivanja/uvoz-opomena/` | Po potrebi |
| Gorivo NIS / OMV | Excel / CSV | Ekrani uvoza | Kada Selenium ne uspe |

#### Zajedničke zaštite pri uvozu [P]

| Zaštita | Gde |
|---|---|
| **Najveća veličina datoteke** | RFZO: 10 MB; raspakovano najviše 50 MB |
| **Najveći broj redova** | RFZO: 50.000 |
| **Otisak datoteke** | RFZO i Potraživanja — sprečava dvostruki uvoz |
| **Sve ili ništa** | RFZO, godišnji odmori, plan javnih nabavki |
| Dnevnik uvoza | Mobilni (`MobileImportLog`), RFZO (`SickLeaveImport`) |

---

### 7.8. Izlaz iz sistema

#### 7.8.1. Banka — virman

| | |
|---|---|
| Oblik | Tekstualna datoteka, **180 znakova po redu**, `cp1250`, `CRLF` |
| Sadržaj | Dva reda zaglavlja + jedan red po nalogu |
| Naziv | `Virman-putni-nalozi-GGGGMMDD-HHMMSS.txt` |
| Prenos | **Ručno** — blagajna preuzima i učitava u elektronsko bankarstvo |

Detaljno: [6.10. Isplate](#610-isplate--virmani).

#### 7.8.2. Obračun zarada — obustave mobilnih

| | |
|---|---|
| Oblik | CSV, razdvajač `;`, UTF-8 **sa BOM**, `CRLF` |
| Kolone | `Godina;Mesec;Šifra radnika;Iznos obustave` |
| Obuhvat | Samo **aktivni zaposleni**; iznos u **celom dinaru** |
| Prenos | **[N] Nije potvrđeno** — uvozom ili ručno |

#### 7.8.3. Ostali izvozi

Excel i CSV izvozi u Floti, Nabavci, Ugovorima, Mobilnom, Potraživanjima i Finansijama —
namenjeni **čoveku**, ne drugom sistemu. [Z]

---

### 7.9. Šta sistem NE radi

| Ne radi | Napomena |
|---|---|
| **Nema REST API** | `djangorestframework` je u zavisnostima, ali se ne koristi |
| **Ne šalje na SEF** | Statuse sa SEF-a samo čita, kroz Potraživanja |
| **Ne knjiži** | Sve knjiženje ostaje u nasleđenom ERP-u |
| **Ne šalje e-poštu** | Nema podešenog slanja pošte |
| **Ne prima podatke spolja programski** | Svaki ulaz je sinhronizacija ili ručni uvoz |

---

### 7.10. Pregled rizika integracija

| Integracija | Rizik | Ozbiljnost | Šta se dešava |
|---|---|---|---|
| NIS / OMV (Selenium) | Promena stranice, lozinka | **Visoka** | Nema novih podataka o gorivu |
| NBS registar menica | Promena stranice | Srednja | Nema novih menica |
| APR OpenAPI | Promena odgovora, SSL | Srednja | Status partnera se ne osvežava |
| `PUTGEO-SERVER` | Nedostupnost | **Visoka** | Finansije i odmori ne rade |
| `INFORMATIKA23` | Nedostupnost | Srednja | Radna lista bez prolazaka |
| Nasleđeni pogledi | **Izmena definicije** | **Visoka** | **Rezultat se menja bez traga** — [P-27](#10-poznati-problemi-i-ograničenja) |
| Ručni uvoz | Promena oblika datoteke | Srednja | Uvoz ne prolazi, uz poruku |

---

### 7.11. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kada se šta pokreće? | [9. Održavanje](#9-održavanje) |
| Koje tabele se pune? | [4. Baza podataka](#4-baza-podataka) |
| Kako se obrađuju preuzeti podaci? | [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj) |
| Šta je uočeno kao problem? | [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) |

---

## 8. Instalacija i pokretanje

> **Za koga je ovo poglavlje:** programeri i osoba koja održava server.
> Status tvrdnji: **[P]** potvrđeno kodom/konfiguracijom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 8.1. Šta je potrebno

| Stavka | Verzija | Napomena |
|---|---|---|
| Python | **3.12** | |
| **ODBC Driver 17 for SQL Server** | — | **Bez njega ništa ne radi** |
| Microsoft SQL Server | — | Baza `IMS_ERP` |
| Redis | — | Broker i zaključavanje poslova |
| Google Chrome | Uz odgovarajući upravljač | Samo za preuzimanje goriva |
| NSSM | — | Samo na produkciji, za Windows servise |

Sve biblioteke su u [`requirements.txt`](../requirements.txt) — **68 paketa**. [P]

---

### 8.2. Razvojno okruženje

```powershell
# 1. Virtuelno okruženje
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Provera ODBC upravljača
Get-OdbcDriver -Name "ODBC Driver 17 for SQL Server"

# 3. Migracije
.\.venv\Scripts\python.exe manage.py migrate

# 4. Server
.\.venv\Scripts\python.exe manage.py runserver
```

> **⚠ Upozorenje [P]:** `manage.py` podrazumevano koristi `ims_erp.settings.development`,
> a to je **prava SQL Server baza** `IMS_ERP` na `SMS-SERVER` — **ne** lokalna kopija.
> Migracije i komande pokrenute bez razmišljanja menjaju produkcione podatke.

#### Bezbedan način rada

```powershell
.\.venv\Scripts\python.exe manage.py <komanda> --settings=ims_erp.settings.testing
```

`testing` koristi **SQLite u memoriji**, bez SQL Servera, Redisa i e-pošte. [P]

---

### 8.3. Postavke po okruženjima

| Fajl | Baza | `ALLOWED_HOSTS` | Namena |
|---|---|---|---|
| `base.py` | — | — | Zajedničko; `DEBUG = True`, `SECRET_KEY` |
| `development.py` | **Pravi SQL Server** | `127.0.0.1` | Razvoj |
| `production.py` | Isti SQL Server + nekorišćeni `local` | `ims-flota`, `ims.portal`, `192.168.6.7`, `127.0.0.1`, `localhost` | Produkcija |
| `testing.py` | **SQLite u memoriji** | `testserver`, `localhost`, `127.0.0.1` | Testovi |

**Podrazumevano [P]:** `manage.py` → `development`; `ims_erp/celery.py` → `production`.

#### Promenljive okruženja [P]

| Promenljiva | Podrazumevano | Namena |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `ims_erp.settings.development` | Izbor postavki |
| `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` | Redis |
| `CELERY_WORKER_CONCURRENCY` | 2 | **Nema dejstva uz `-P solo`** |
| `MSSQL_DRIVER` | `ODBC Driver 17 for SQL Server` | |
| `MSSQL_QUERY_TIMEOUT` | 90 s | |
| `MSSQL_CONN_MAX_AGE` | 300 s | |
| `FINANSIJE_NALOG_Z_TIMEOUT` | 900 s | Rok za proceduru |
| `MAX_CONTRACT_UPLOAD_SIZE` | 50 MB | Najveći dokument |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | 60 MB | |

> **[P] Bezbednosni nalaz:** lozinke baze i `SECRET_KEY` su **upisani u kod**, ne u
> promenljive okruženja. `python-dotenv` je u zavisnostima, ali se ne koristi.
> Vidi [P-01](#10-poznati-problemi-i-ograničenja).

---

### 8.4. Testovi

```powershell
# Svi testovi
.\.venv\Scripts\python.exe manage.py test --settings=ims_erp.settings.testing

# Jedan modul
.\.venv\Scripts\python.exe manage.py test finansije core --settings=ims_erp.settings.testing
```

**550 testova** u 31 fajlu. Izvršavaju se na SQLite bazi u memoriji. [P]

| Modul | Testova |
|---|---|
| `fleet` | 153 |
| `finansije` | 121 |
| `hr` | 97 |
| `potrazivanja` | 59 |
| `mobilni` | 40 |
| `core` | 28 |
| `isplate` | 20 |
| `nabavka` | 19 |
| `ugovori`, `naplata`, `menice` | 13 |

> **[P] Poznat pad testa:** `nabavka.tests.ProcurementInvoiceJobCodeLinkTests.`
> `test_primary_invoice_job_code_cannot_be_added_as_additional` — zabeležen u
> `finansije/README.md` kao postojeći pre uvođenja Finansija.

---

### 8.5. Produkciono okruženje

| Stavka | Putanja |
|---|---|
| Aplikacija | `C:\DjangoApps\ims_erp` |
| Virtuelno okruženje | `C:\DjangoApps\venv` |
| Dnevnici | `C:\DjangoApps\logs` |
| Redis | `C:\Redis\redis-server.exe` |
| NSSM | `C:\nssm\nssm.exe` |
| Postavke | `ims_erp.settings.production` |

#### Tri Windows servisa [P]

| Servis | Komanda |
|---|---|
| `IMS_Fleet_Redis` | `redis-server.exe redis.windows.conf` |
| `IMS_Fleet_Celery_Worker` | `celery -A ims_erp worker -l info -P solo -Q default,sync,selenium` |
| `IMS_Fleet_Celery_Beat` | `celery -A ims_erp beat --scheduler django_celery_beat.schedulers:DatabaseScheduler -l info` |

Instalacija: `nssm.bat`. Podešeno: samopokretanje, ponovno pokretanje posle 5 s,
rotacija dnevnika na 10 MB. [P]

> **[N] Web server nije zabeležen.** `wsgi.py` postoji, ali u projektu nema
> konfiguracije IIS-a ni drugog servera. Treba dopuniti.

---

### 8.6. Prvo puštanje u rad

```powershell
# 1. Baza i struktura
.\.venv\Scripts\python.exe manage.py migrate

# 2. Šifarnik organizacionih jedinica
.\.venv\Scripts\python.exe manage.py fetch_job_codes

# 3. Zaposleni
.\.venv\Scripts\python.exe manage.py sync_hr_employees

# 4. Dozvole i uloge
.\.venv\Scripts\python.exe manage.py sync_permission_codes

# 5. Korisnički nalozi za zaposlene
.\.venv\Scripts\python.exe manage.py create_employee_users

# 6. Raspored poslova
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks

# 7. Finansije
.\.venv\Scripts\python.exe manage.py configure_finansije
.\.venv\Scripts\python.exe manage.py sync_finansije

# 8. Potraživanja
.\.venv\Scripts\python.exe manage.py initialize_potrazivanja
.\.venv\Scripts\python.exe manage.py configure_potrazivanja

# 9. Šifarnici
.\.venv\Scripts\python.exe manage.py import_work_time_catalog <putanja>
.\.venv\Scripts\python.exe manage.py import_evaluation_catalog <putanja>
.\.venv\Scripts\python.exe manage.py load_konta_vozila

# 10. Servisi
.\nssm.bat
```

> **⚠ Korak koji će zakazati [P]:** aplikacija **`menice` nema migracije**, pa korak 1
> **neće stvoriti** tabele `menica` i `ulazna_menica`. Vidi [P-45](#10-poznati-problemi-i-ograničenja).

---

### 8.7. Struktura projekta

```
ims_erp/          Konfiguracija (settings, urls, celery, wsgi)
core/             Korisnici, uloge, dozvole, evidencija rada
fleet/            Vozni park + korenske rute
hr/               Kadrovi
finansije/        Finansijska analitika
nabavka/          Nabavka
potrazivanja/     Potraživanja
ugovori/          Partneri i ugovori
menice/           Menice  ← bez migracija
mobilni/          Mobilna telefonija
isplate/          Virmani (bez tabela)
naplata/          NASLEĐENO — u gašenju
templates/        Globalni šabloni i bočni meniji
media/            Otpremljeni fajlovi
logs/             Dnevnici
dokumentacija/    Dokumentacija
chrome-for-testing/  Chrome za Selenium
```

---

### 8.8. Provera da sve radi

| # | Provera | Očekivano |
|---|---|---|
| 1 | Otvoriti `/login/` | Ekran za prijavu |
| 2 | Prijaviti se | Kontrolna tabla flote |
| 3 | Otvoriti `/administracija/task-history/` | Spisak poslova |
| 4 | Otvoriti `/finansije/sinhronizacija/` | Istorija i kontrolni zbirovi |
| 5 | `Get-Service IMS_Fleet_*` | Tri servisa rade |
| 6 | Pokrenuti lak posao ručno | Status **Uspešan** u istoriji |
| 7 | Otvoriti `/potrazivanja/` | Datum poslednjeg objavljenog snimka |

---

### 8.9. Šta treba dopuniti u ovoj dokumentaciji

| # | Nedostaje | Potrebno od |
|---|---|---|
| 1 | **Konfiguracija web servera** (IIS ili drugi) | Održavanje |
| 2 | **Postupak izrade rezervne kopije** baze i direktorijuma `media/` | Održavanje |
| 3 | Gde se čuvaju pristupni podaci za NIS i OMV portale | **Q7** |
| 4 | Ko i kako obnavlja lozinke portala | **Q7** |
| 5 | Postupak vraćanja na prethodnu verziju koda | Održavanje |

---

### 8.10. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako se sistem održava iz dana u dan? | [9. Održavanje](#9-održavanje) |
| Kako je sastavljen? | [2. Arhitektura](#2-arhitektura) |
| Šta je poznato kao problem? | [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) |
| Pravila za programere | [AGENTS.md](../AGENTS.md) |

---

## 9. Održavanje

> **Za koga je ovo poglavlje:** osoba koja održava sistem i dežurni administrator.
> Status tvrdnji: **[P]** potvrđeno kodom/konfiguracijom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 9.1. Šta se svakodnevno dešava samo od sebe

```
 01:00  Dozvole i uloge
 01:10  Zaposleni iz kadrovske baze
 01:20  Provera otpisanih vozila
 01:30  Šifre poslova i organizacione jedinice   ← stara organizacija
 01:40  Registar organizacije i poređenje      ← nova, paralelno sa starom
 01:45  Trebovanja
 02:00  Polise osiguranja
 02:20  EUF fakture (Nabavka)
 02:45  UF stavke (Nabavka)
 03:15  Servisi vozila
 03:35  Knjiženja osiguranja DDOR
 03:50  Finansije — sve godine od 2025.
 04:20  Gorivo NIS                    ← Selenium, do 4 h
 05:10  Gorivo OMV putnička            ← Selenium, do 4 h
 06:10  Gorivo OMV teretna             ← Selenium, do 4 h
 07:10  Roba (Nabavka)
 ────────────────── radni dan ──────────────────
 10:00  Osvežavanje lokalnog nalog_z
 11:00  Osvežavanje lokalnog nalog_z
 12:30  Isplaćeni iznosi po putnim nalozima
 :20    Svakog sata — Finansije, tekuća godina
```

**Ukupno 19 zakazanih poslova.** [P]

---

### 9.2. Tabela zakazanih poslova

| Vreme | Naziv | Task | Red | Zaključavanje |
|---|---|---|---|---|
| 01:00 | Administracija — sinhronizacija dozvola | `core.tasks.sync_permission_codes_task` | `sync` | — |
| 01:10 | Kadrovi — sinhronizacija zaposlenih | `fleet.tasks.sync_hr_employees_task` | `sync` | 90 min |
| 01:20 | Flota — provera otpisa vozila | `fleet.tasks.proveri_otpis` | `sync` | 60 min |
| 01:30 | Flota — šifre poslova i OJ | `fleet.tasks.fetch_job_codes` | `sync` | 60 min |
| 01:40 | Organizacija — registar i poređenje sa starom | `organizacija.tasks.sync_organizacija_task` | `sync` | 90 min |
| 01:45 | Flota — trebovanja | `fleet.tasks.fetch_requisition_data_task` | `sync` | 90 min |
| 02:00 | Flota — polise | `fleet.tasks.fetch_policy_data_task` | `sync` | 90 min |
| 02:20 | Nabavka — EUF fakture | `nabavka.tasks.sync_euf_invoices_task` | `sync` | — |
| 02:45 | Nabavka — UF stavke | `nabavka.tasks.sync_uf_items_task` | `sync` | — |
| 03:15 | Flota — servisi | `fleet.tasks.fetch_service_data_task` | `sync` | 90 min |
| 03:35 | Flota — DDOR osiguranja | `fleet.tasks.fetch_ddor_data_task` | `sync` | 90 min |
| 03:50 | Finansije — sve godine | `finansije.tasks.sync_all_years` | `sync` | SQL lock |
| **04:20** | **Gorivo — NIS** | `fleet.tasks.run_nis_command` | **`selenium`** | **4 h** |
| **05:10** | **Gorivo — OMV putnička** | `fleet.tasks.run_omv_putnicka_command` | **`selenium`** | **4 h** |
| **06:10** | **Gorivo — OMV teretna** | `fleet.tasks.run_omv_teretna_command` | **`selenium`** | **4 h** |
| 07:10 | Nabavka — roba | `nabavka.tasks.sync_goods_task` | `sync` | — |
| **10:00 i 11:00** | **Finansije — osvežavanje `nalog_z`** | `finansije.tasks.refresh_nalog_z_task` | `sync` | SQL lock |
| 12:30 | Putni nalozi — isplaćeno | `fleet.tasks.sync_putni_nalozi_isplaceno_task` | `sync` | 90 min |
| svaki sat u :20 | Finansije — tekuća godina | `finansije.tasks.sync_current_year` | `sync` | SQL lock |

> **[P] Vremenska zona:** `nalog_z` izričito koristi `Europe/Belgrade`; ostali koriste
> `CELERY_TIMEZONE = CET`.

#### Poslovi koji NISU zakazani, a postoje [P]

| Posao | Pokreće se |
|---|---|
| Sinhronizacija godišnjih odmora | Ručno, sa ekrana |
| Sinhronizacija Potraživanja | Ručno (zadatak postoji, ali nije u rasporedu) |
| Preuzimanje menica iz NBS-a | Ručno |
| APR provera partnera | Ručno |
| Sinhronizacija partnera iz Finansija | Ručno |
| Knjigovodstvena vrednost vozila | Ručno |
| Kamate lizinga | Ručno |
| Čišćenje duplikata goriva | Automatski **uz svaki uvoz OMV podataka** |
| Samo povezivanje Flote sa registrom (`povezi_flotu`) | Ručno; inače je deo zadatka u 01:40, a novi zapisi se povezuju sami pri čuvanju |

---

### 9.3. Kako proveriti da je sve prošlo

#### Prvi korak — istorija zadataka [P]

> **`/administracija/task-history/`**

| Status | Značenje | Šta uraditi |
|---|---|---|
| **Uspešan** | Prošlo | Ništa |
| **Preskočen** | Prethodno izvršavanje još traje | **Nije greška.** Proveriti da se ne ponavlja svaki dan |
| **Neuspešan** | Greška | Pogledati poruku i dnevnik |
| **Pokrenut** *(a prošlo je puno vremena)* | Posao je prekinut bez zapisa | Proveriti da li proces radi |

Uz svaki posao se vide **trajanje**, **rezultat** i **tekst greške**. [P]

#### Drugi korak — po modulima

| Modul | Gde se proverava |
|---|---|
| **Finansije** | `/finansije/sinhronizacija/` — brojači i **kontrolni zbirovi** |
| **Potraživanja** | `/potrazivanja/sinhronizacija/` — koraci, kontrole, problemi prenosa |
| **Mobilni** | `/mobilni/import/` — dnevnik uvoza |
| **Kadrovi — bolovanja** | `/hr/bolovanja/uvoz/` — brojači |
| **Flota — nedovršeno** | Kontrolna tabla, grupa „Evidencije za dopunu“ |

#### Treći korak — dnevnici

```
C:\DjangoApps\logs\celery-worker.stdout.log
C:\DjangoApps\logs\celery-worker.stderr.log
C:\DjangoApps\logs\celery-beat.stdout.log
C:\DjangoApps\logs\redis.stdout.log
```

Dnevnici se **rotiraju na 10 MB** (NSSM). [P]

Korisne oznake u dnevniku [P]: `TASK_START`, `TASK_DONE`, `TASK_FAIL`,
`CELERY_TASK_START`, `CELERY_TASK_FINISH`, `CELERY_TASK_FAILURE`, `SKIP:`.

---

### 9.4. Windows servisi

| Servis | Šta radi |
|---|---|
| `IMS_Fleet_Redis` | Redis — broker i zaključavanje |
| `IMS_Fleet_Celery_Worker` | Izvršava poslove |
| `IMS_Fleet_Celery_Beat` | Pokreće poslove po rasporedu |

```powershell
Get-Service IMS_Fleet_*
Restart-Service IMS_Fleet_Celery_Worker
```

Instalacija: `nssm.bat`. Podešavanja se menjaju kroz `nssm edit <servis>`.

#### Ozbiljno ograničenje [P]

Radnik se pokreće sa **`-P solo`** — **jedan zadatak u jednom trenutku**.
Postavka `CELERY_WORKER_CONCURRENCY = 2` u tom režimu **nema dejstva**.

**Posledica:** Selenium posao koji traje sat vremena **blokira i lake sinhronizacije**.
Vidi [P-15](#10-poznati-problemi-i-ograničenja).

---

### 9.5. Posle isporuke novog koda

> **Redosled je bitan.** [Z]

```powershell
# 1. Migracije
.\.venv\Scripts\python.exe manage.py migrate

# 2. Dozvole — ako su dodate nove rute
.\.venv\Scripts\python.exe manage.py sync_permission_codes

# 3. Raspored — ako su dodati novi zadaci (prvo provera)
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks --dry-run
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks

# 4. Restart radnika — OBAVEZNO ako je dodat novi zadatak
Restart-Service IMS_Fleet_Celery_Worker
Restart-Service IMS_Fleet_Celery_Beat
```

> **[P] Zašto restart:** stari radnik **odbacuje nepoznat zadatak**. Ako se raspored
> aktivira pre restarta, zadaci se gube.

Za ciljanu dopunu novih ekrana Pravne službe i rešenja zaposlenih:

```powershell
.\.venv\Scripts\python.exe manage.py sync_pravna_resenja_permissions --dry-run
.\.venv\Scripts\python.exe manage.py sync_pravna_resenja_permissions
```

Komanda dodaje sve rute `pravna:*` ulozi **Pravna služba**, operativne dozvole
`hr:resenje_*` ulozi **Sekretarijat**, a ove kodove **Upravi**. Uloga **Kadrovi**
zamenjuje **Kadrovik — rešenja** i dobija funkcije celog kadrovskog modula, uključujući
šifarnike, uz ograničenje podataka po dodeljenom obuhvatu. Posebne dozvole za sve centre
ne dodaju se ulozi Kadrovi.
Postojeće dozvole i članstva korisnika ostaju sačuvani. Ista dopuna je uključena
u redovni `sync_permission_codes`.

Za ekran upravljanja korisničkim pristupom od 24.09.2026. primeniti migraciju
`fleet.0081_customuser_allowed_hr_unit_codes`, pa ciljanu komandu:

```powershell
.\.venv\Scripts\python.exe manage.py migrate fleet 0081
.\.venv\Scripts\python.exe manage.py sync_user_access_permissions --dry-run
.\.venv\Scripts\python.exe manage.py sync_user_access_permissions
```

Ona usklađuje samo ulogu Kadrovi i kodove administracije korisnika, bez redovnog
prepisivanja dozvola drugih standardnih uloga. Posle isporuke koda restartovati web
proces i radnike koji učitavaju `core.permissions`, da stari kod ne bi vratio staru ulogu.

Disciplinski postupci od 24.09.2026. koriste migraciju
`pravna.0002_disciplinskipostupak_mera_vrsta`: zatvaranje traži datum i jednu od četiri
mere iz člana 77 dostavljenog pravilnika (pisana opomena, udaljenje bez naknade
1–15 radnih dana, novčana kazna do 20% osnovne zarade do tri meseca, prestanak radnog
odnosa). Stari zatvoreni postupci ostaju zatvoreni; nedostajuća mera dopunjava se na
detalju, bez nagađanja na osnovu datuma ili zaposlenog. Raniji slobodan opis se čuva.
Centar u formi je izbor iz spiska, predložen iz OJ zaposlenog postojećim pravilom
najdužeg prefiksa centra; izabrani drugi centar se čuva. „Arhivirano“ je uklonjeno iz
forme unosa/izmene, dok zasebna akcija arhiviranja i postojeća arhiva ostaju dostupne.

---

### 9.6. Česti problemi i šta uraditi

| Simptom | Verovatan uzrok | Šta uraditi |
|---|---|---|
| **Nema novih podataka o gorivu** | Selenium ne uspeva | Pogledati `TaskHistory`; proveriti prijavu na portal i verziju Chrome-a; **uvesti datoteku ručno** |
| **Finansije prazne za godinu** | Sinhronizacija nije prošla | `/finansije/sinhronizacija/` — pokrenuti ručno; proveriti `PUTGEO-SERVER` |
| **Radna lista bez sati** | `INFORMATIKA23` nedostupan | Poruka to kaže; podaci se vraćaju kada server proradi |
| **Zadatak stalno „Preskočen“** | Prethodni je ostao zaključan | Proveriti da li proces radi; zaključavanje ističe posle 4 h / 90 min |
| **Novi ekran niko ne vidi** | Dozvola nije generisana | `sync_permission_codes`, pa dodeliti ulozi |
| **Novi zadatak se ne izvršava** | Radnik ga ne poznaje | Restart radnika |
| **`nalog_z` — „Ishod nepoznat“** | Proces je pao tokom procedure | **Proveriti stanje u bazi** pre ponovnog pokretanja |
| **Sinhronizacija Potraživanja ne prolazi** | Kontrolni zbirovi se ne slažu | Poruka navodi koja kontrola; **prethodni snimak ostaje objavljen** |
| **Vozilo nema šifru posla** | Nema dodele pre datuma | `/sifre-poslova/` |
| **Polisa nije u upozorenjima** | Polisa je **nedovršena** | `/polise/nedovrseno/` |
| **Redis ne radi** | Servis stao | Poslovi se **ipak izvršavaju**, bez zaštite — [P-16](#10-poznati-problemi-i-ograničenja) |

---

### 9.7. Redovne provere

#### Svakodnevno

| Provera | Gde |
|---|---|
| Da li su noćni poslovi prošli | `/administracija/task-history/` |
| Upozorenja o vozilima | Kontrolna tabla `/` |

#### Nedeljno

| Provera | Gde |
|---|---|
| Nedovršene evidencije | Kontrolna tabla, „Evidencije za dopunu“ |
| Problemi prenosa Potraživanja | `/potrazivanja/sinhronizacija/` |
| Veličina dnevnika | `C:\DjangoApps\logs` |

#### Mesečno

| Provera | Gde |
|---|---|
| Uvoz bolovanja (RFZO) | `/hr/bolovanja/uvoz/` |
| Uvoz podataka operatera | `/mobilni/import/` |
| **Obustave pre slanja u zarade** | `/mobilni/obustave/zaposleni/` |
| Kontrolni zbirovi Finansija | `/finansije/sinhronizacija/` |

#### Godišnje

| Provera | Napomena |
|---|---|
| Početni brojevi putnih naloga po centrima | Bez njih se nalog **ne može otvoriti** za novu godinu |
| Plan javnih nabavki | Nova verzija |
| Pragovi troška po kilometru | Upisani u kod — [P-11](#10-poznati-problemi-i-ograničenja) |

---

### 9.8. Ručno pokretanje poslova

```powershell
# Finansije
.\.venv\Scripts\python.exe manage.py sync_finansije
.\.venv\Scripts\python.exe manage.py sync_finansije --year-from 2026 --year-to 2026

# Potraživanja
.\.venv\Scripts\python.exe manage.py sync_potrazivanja

# Kadrovi
.\.venv\Scripts\python.exe manage.py sync_hr_employees
.\.venv\Scripts\python.exe manage.py sync_annual_leave
.\.venv\Scripts\python.exe manage.py import_rfzo_sick_leave <putanja>

# Flota
.\.venv\Scripts\python.exe manage.py fetch_job_codes
.\.venv\Scripts\python.exe manage.py otpis
.\.venv\Scripts\python.exe manage.py nis_command
.\.venv\Scripts\python.exe manage.py omv_command_putnicka
.\.venv\Scripts\python.exe manage.py omv_command_teretna
.\.venv\Scripts\python.exe manage.py cleanup_omv_fuel_duplicates          # pregled
.\.venv\Scripts\python.exe manage.py cleanup_omv_fuel_duplicates --apply  # brisanje

# Registar organizacije (nova sinhronizacija, paralelno sa fetch_job_codes)
.\.venv\Scripts\python.exe manage.py sync_organizacija                 # isto što i zadatak u 01:40
.\.venv\Scripts\python.exe manage.py uvezi_organizaciju
.\.venv\Scripts\python.exe manage.py povezi_flotu --proba --izvestaj   # pregled, bez upisa
.\.venv\Scripts\python.exe manage.py povezi_flotu                      # popunjava org_node u paketima

# Dozvole i raspored
.\.venv\Scripts\python.exe manage.py sync_permission_codes
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks --dry-run
```

**Ukupno 54 upravljačke komande.** Spisak: `manage.py help`. [P]

> **[P] Zaštita:** ručno pokretanje koristi **isto zaključavanje** kao zakazani posao —
> ne mogu se preklopiti.

---

### 9.9. Šta ne raditi

| Ne raditi | Zašto |
|---|---|
| **Ne pokretati poslovne procedure ručno** (`SPFINizv52/53/55`, `SPLdKnjizenje`) | Menjaju poslovne podatke u produkciji |
| **Ne pisati u nasleđene `dbo.*` poglede** | Vlasnik im je stari ERP |
| **Ne menjati nasleđene poglede bez dogovora** | Menja rezultat na ekranu bez traga — [P-27](#10-poznati-problemi-i-ograničenja) |
| **Ne brisati zapise iz `TaskHistory` i `ActivityLog`** | To je jedini trag rada sistema |
| **Ne pokretati `makemigrations` za `menice`** bez provere | Nema migracija — [P-45](#10-poznati-problemi-i-ograničenja) |
| **Ne uključivati `DEBUG = False`** bez rešavanja medija | Slike i dokumenti prestaju da se prikazuju — [P-01](#10-poznati-problemi-i-ograničenja) |
| **Ne menjati vreme Selenium poslova** da se preklope | Jedan radnik, `-P solo` |

---

### 9.10. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako se sistem instalira? | [8. Instalacija i pokretanje](#8-instalacija-i-pokretanje) |
| Odakle dolaze podaci? | [7. Integracije](#7-integracije) |
| Šta je poznato kao problem? | [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) |
| Kako rade dozvole? | [2.6](#26-kontrola-pristupa) |

---

## 10. Poznati problemi i ograničenja

> **Za koga je ovo poglavlje:** programeri, održavanje, uprava (poglavlje 10.1 i 10.5).
>
> Ovde se vodi **registar svega što je uočeno tokom dokumentovanja sistema**, sa
> opisom posledice i predlogom rešenja.
>
> **Dana 18.09.2026. ispravljena je prva grupa problema** — oni kod kojih je uzrok bio
> nedvosmislen i ispravka kratka. Označeni su statusom **Rešeno** i za svaki piše šta je
> tačno promenjeno.
>
> **Dana 21.09.2026. registar je prvi put provereno nad produkcionom bazom.** Do tada su
> svi nalazi bili iz koda i iz razvojne baze. Provera je zatvorila dva problema
> ([P-27](#p-27--formule-11-izveštaja-nisu-u-projektu),
> [P-47](#p-47--ključ-za-duplikate-ne-obuhvata-iznos-ni-valutu)) i otvorila dva nova
> ([P-51](#p-51--tri-šifre-dozvole-ne-postoje-na-produkciji),
> [P-52](#p-52--ulazni-podaci-ekonomike-su-prazni-na-produkciji)) koja se **nisu mogla
> videti bez pristupa stvarnim podacima**.
>
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 10.1. Kako čitati registar

| Ozbiljnost | Značenje |
|---|---|
| **Visoka** | Daje pogrešan poslovni rezultat ili ugrožava bezbednost podataka. Rešiti prvo. |
| **Srednja** | Daje rezultat koji zbunjuje ili nije uporediv; radi se, ali pogrešno se tumači. |
| **Niska** | Smeta u radu ili održavanju, ne kvari rezultat. |

| Status | Značenje |
|---|---|
| **Za rešavanje** | Potvrđeno, čeka odluku i ispravku |
| **Za proveru** | Potrebna potvrda korisnika pre bilo kakve izmene |
| **Prihvaćeno** | Poznato ograničenje, svesno se ne menja |
| **Zatvoreno** | Provereno nad stvarnim podacima i ne javlja se; opis ostaje radi ponovne provere |
| **Rešeno** | Ispravljeno; u opisu stoji šta je promenjeno i kada |

---

### 10.2. Zbirni pregled

| # | Oblast | Kratak opis | Ozbiljnost | Status |
|---|---|---|---|---|
| [P-01](#p-01--tajne-i-debug-u-repozitorijumu) | Konfiguracija | Lozinke baze, `SECRET_KEY` i `DEBUG=True` u repozitorijumu | **Visoka** | **Rešeno** 19.09. — *istorija* |
| [P-02](#p-02--prosečna-potrošnja-ne-proverava-stariju-granicu) | Flota / gorivo | Prosečna potrošnja može biti desetostruko premala | **Visoka** | **Rešeno** 19.09. |
| [P-03](#p-03--procena-kilometraže-koristi-očitavanja-izvan-perioda) | Flota / troškovi | Kilometraža se procenjuje iz očitavanja izvan perioda | **Visoka** | **Rešeno** 19.09. |
| [P-04](#p-04--kvadratna-složenost-izbora-para-očitavanja) | Flota / troškovi | Spor obračun kod vozila sa mnogo očitavanja | Niska | **Rešeno** 19.09. |
| [P-05](#p-05--centar-se-uzima-iz-poslednje-dodele-a-ne-istorijske) | Flota / troškovi | Trošak ide na trenutni, a ne na tadašnji centar | **Srednja** | **Rešeno** 19.09. — *V-07* |
| [P-06](#p-06--cela-premija-polise-ulazi-u-svaki-period) | Flota / troškovi | Cela godišnja premija ulazi i u jednomesečni period | **Visoka** | **Rešeno** 19.09. |
| [P-07](#p-07--cela-godišnja-kamata-lizinga-ulazi-u-svaki-period) | Flota / troškovi | Cela godišnja kamata ulazi i u jednomesečni period | **Visoka** | **Rešeno** 19.09. |
| [P-08](#p-08--operativni-lizing-se-deli-drugačije-od-dugoročnog-najma) | Flota / troškovi | Ista kolona se tumači na dva načina | **Srednja** | **Rešeno** 19.09. |
| [P-09](#p-09--vozila-sa-troškom-nula-ili-manjim-nestaju-iz-spiska) | Flota / troškovi | Vozilo bez troška se ne prikazuje, bez objašnjenja | **Srednja** | **Rešeno** 19.09. |
| [P-10](#p-10--napomena-o-maloj-kilometraži-poredi-period-sa-godinom) | Flota / troškovi | Upozorenje se pojavljuje i kada ne treba | Niska | **Rešeno** 18.09. |
| [P-11](#p-11--pragovi-troška-po-km-su-upisani-u-kod) | Flota / troškovi | Pragovi se ne mogu menjati bez izmene koda | **Srednja** | **Rešeno** 19.09. |
| [P-12](#p-12--analiza-kroz-više-perioda-zahteva-najmanje-dva-perioda) | Flota / troškovi | Greška ako se prosledi jedan period | Niska | Otpalo 19.09. |
| [P-13](#p-13--superuser-ne-može-da-otvori-statistiku-centra) | Flota / pristup | Superuser dobija 403 | **Srednja** | **Rešeno** 18.09. |
| [P-14](#p-14--statistika-centra--četiri-odvojena-nedostatka) | Flota / centri | Otpisana vozila, prosečna starost, dijakritici | **Srednja** | **Rešeno** A i D; B i C otpali |
| [P-15](#p-15--jedan-celery-radnik-poništava-razdvajanje-redova) | Infrastruktura | `-P solo` blokira lake poslove | **Srednja** | Za proveru |
| [P-16](#p-16--zaključavanje-poslova-popušta-kada-redis-nije-dostupan) | Infrastruktura | Dva ista posla mogu raditi istovremeno | **Srednja** | Za proveru |
| [P-17](#p-17--procedura-sp_azurirajnalogz-ne-briše-obrisane-redove) | Finansije | Lokalna kopija nije jednaka izvoru | **Srednja** | Prihvaćeno |
| [P-18](#p-18--naplata-i-potraživanja-rade-paralelno) | Naplata | Dva sistema nad istim poslom | **Srednja** | Za rešavanje |
| [P-19](#p-19--dva-mehanizma-za-ograničenje-po-centrima) | Pristup | Nije jasno koji je merodavan | **Srednja** | Za proveru |
| [P-20](#p-20--model-naplate-navodi-nepostojeći-pogled) | Naplata | `dodela_bucketa` naspram `dodela_baketa` | Niska | Prihvaćeno |
| [P-21](#p-21--radni-fajlovi-u-repozitorijumu) | Repozitorijum | Baza, dnevnici i privremeni fajlovi u projektu | Niska | **Rešeno** 18.09. |
| [P-22](#p-22--nekorišćene-zavisnosti) | Repozitorijum | `djangorestframework`, `psycopg2` | Niska | **Rešeno** 18.09. |
| [P-23](#p-23--lizing-se-prikazuje-samo-u-mesecu-početka-ugovora) | Flota / lizing | Mesečni izveštaj prikazuje ugovor samo jednom | **Visoka** | Za rešavanje |
| [P-24](#p-24--izveštaj-lizinga-koristi-poslednju-dodelu-vozila) | Flota / lizing | Nedosledno sa ostalim mesečnim izveštajima | **Srednja** | Za rešavanje |
| [P-25](#p-25--prateći-troškovi-lizinga-obuhvataju-sva-vozila-jedinice) | Flota / lizing | Troškovi koji ne pripadaju lizing vozilima | **Srednja** | Za rešavanje |
| [P-26](#p-26--izveštaj-goriva-za-upravu-nema-zaštitu-pri-čitanju) | Flota / izveštaji | Nema prečišćavanja OMV pri čitanju | **Srednja** | **Rešeno** 18.09. |
| [P-27](#p-27--formule-11-izveštaja-nisu-u-projektu) | Flota / izveštaji | Formule 11 izveštaja postoje samo u bazi | **Srednja** | **Većim delom rešeno** 21.09. |
| [P-28](#p-28--dva-različita-obračuna-dnevnih-sati) | Kadrovi | Dva obračuna sati iz iste evidencije | **Visoka** | Za proveru |
| [P-29](#p-29--otvoreno-bolovanje-nestaje-sa-radne-liste) | Kadrovi | Otvoreno bolovanje se prikazuje do datuma izvoza | **Srednja** | Za rešavanje |
| [P-30](#p-30--izuzeće-od-parkinga-nema-period-važenja) | Mobilni | Izuzetak menja i prošle obračune | **Srednja** | Za rešavanje |
| [P-31](#p-31--obustava-se-nigde-ne-čuva) | Mobilni | Nema traga šta je prosleđeno u zarade | **Visoka** | Za rešavanje |
| [P-32](#p-32--rupe-u-razvrstavanju-bivših-zaposlenih) | Mobilni | Neki zaposleni nisu ni u jednom izveštaju | **Srednja** | Za rešavanje |
| [P-33](#p-33--virman-skraćuje-podatke-i-ne-čuva-poslatu-datoteku) | Isplate | Tiho skraćivanje i bez traga o poslatom | **Visoka** | Za rešavanje |
| [P-34](#p-34--poseban-broj-telefona-upisan-u-kod-umesto-u-bazi) | Mobilni | Poslovni izuzetak upisan u kod | **Visoka** | **Potvrđena greška** |
| [P-35](#p-35--nepoznato-dospeće-prikazuje-se-kao-nedospelo) | Potraživanja | Dug bez dospeća izgleda kao nedospeo | **Srednja** | Za proveru |
| [P-36](#p-36--ukupan-iznos-faktura-na-izveštaju-nabavke-je-višestruko-uvećan) | Nabavka | Zbir sabira fakturu više puta | **Visoka** | **Rešeno** 18.09. |
| [P-37](#p-37--brisanje-uf-faktura-tiho-kida-veze) | Nabavka | Veza sa predmetom nestaje bez traga | **Srednja** | Za rešavanje |
| [P-38](#p-38--procenjena-vrednost-predmeta-se-ne-poredi-sa-stavkama) | Nabavka | Dve nezavisne vrednosti, bez provere | Srednja | Za proveru |
| [P-39](#p-39--ispravka-u-izvoru-stvara-dvojnika-euf-fakture) | Nabavka | Ispravka u izvoru pravi novu fakturu | **Srednja** | Za proveru |
| [P-40](#p-40--apr-provera-zaobilazi-ssl-i-prepoznaje-samo-jedan-status) | Ugovori | Zaobilaženje SSL i uzak uslov statusa | **Srednja** | Za rešavanje |
| [P-41](#p-41--preuzimanje-menica-zavisi-od-izgleda-stranice-nbs-a) | Menice | Krhka integracija i PIB u kodu | **Srednja** | Za rešavanje |
| [P-42](#p-42--konta-i-pravila-toka-gotovine-upisani-su-u-kod) | Finansije | Kontni plan i pravila u kodu | **Srednja** | Za proveru |
| [P-43](#p-43--mogući-dvostruki-obuhvat-zajedničkih-troškova) | Finansije | Rizik dvostrukog obuhvata ZT | **Srednja** | Za proveru |
| [P-44](#p-44--promena-centra-pregrupiše-celu-istoriju-finansija) | Finansije | Prošli izveštaji se menjaju | **Srednja** | Za proveru |
| [P-45](#p-45--modul-menice-nema-migracije) | Menice | Tabele se ne mogu stvoriti migracijom | **Visoka** | Za rešavanje |
| [P-46](#p-46--ključ-za-duplikate-ne-podnosi-prazna-polja) | Flota / gorivo | Zapis bez vaučera ili količine nestaje sa ekrana | **Visoka** | **Rešeno** 18.09. |
| [P-47](#p-47--ključ-za-duplikate-ne-obuhvata-iznos-ni-valutu) | Flota / gorivo | Dva iznosa iste transakcije se spajaju u jedan | **Srednja** | **Zatvoreno** 21.09. — ne javlja se |
| [P-48](#p-48--lični-podaci-i-brojevi-računa-329-osoba-u-repozitorijumu) | Bezbednost | Imena, adrese i brojevi računa u git istoriji | **Visoka** | Delimično rešeno — **istorija ostaje** |
| [P-49](#p-49--procedura-osvežava-tekuću-godinu-a-ispravke-čitaju-prethodnu) | Potraživanja | Posle aprila ispravke čitaju godinu koja se ne osvežava | **Srednja** | **Za proveru** |
| [P-50](#p-50--pregled-novog-modula-ekonomike-flote) | Flota / ekonomika | 14 nalaza u novom modulu, pre isporuke | **Visoka** | **Rešeno** 19.09. |
| [P-51](#p-51--tri-šifre-dozvole-ne-postoje-na-produkciji) | Ovlašćenja | Ekrani ekonomike dostupni samo superkorisniku | **Visoka** | **Za rešavanje** — potrebna izmena na produkciji |
| [P-52](#p-52--ulazni-podaci-ekonomike-su-prazni-na-produkciji) | Flota / ekonomika | Modul radi, ali nema šta da računa | **Visoka** | **Za rešavanje** — unos podataka |

---

### 10.3. Bezbednost i konfiguracija

#### P-01 — Tajne i DEBUG u repozitorijumu

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (19.09.2026.) — **tajne ostaju u istoriji** |
| **Gde** | `ims_erp/settings/base.py`, `development.py`, `production.py` |

**Šta je zatečeno [P]:**

| Stavka | Gde | Vrednost |
|---|---|---|
| `SECRET_KEY` | `base.py:70` | Upisan u kod |
| `DEBUG = True` | `base.py:73` | **Produkcija ga ne isključuje** |
| Korisnik i lozinka baze | `development.py:11-13`, `production.py:14-17` | Upisani u kod |
| Ime servera i baze | oba fajla | Upisani u kod |

**Posledice [Z]:**

1. Svako ko ima pristup repozitorijumu ima i pristupne podatke za bazu `IMS_ERP`.
2. Sa `DEBUG = True` Django pri grešci prikazuje **pun ispis stanja**, uključujući
   delove konfiguracije i vrednosti promenljivih.
3. Poznat `SECRET_KEY` omogućava falsifikovanje sesija i CSRF tokena.
4. Mediji se opslužuju preko Djanga, jer `MEDIA_URL` radi samo uz `DEBUG=True`
   — isključivanje `DEBUG`-a zahteva i podešavanje opsluživanja medija.

**Predlog rešenja [Z]:**

1. Preseliti sve tajne u promenljive okruženja (`python-dotenv` je već u zavisnostima).
2. Postaviti `DEBUG = False` u `production.py` i podesiti opsluživanje `media/`
   preko web servera.
3. Promeniti `SECRET_KEY` i lozinku baze **posle** preseljenja.
4. Ukloniti istoriju tajni iz repozitorijuma ili prihvatiti da su kompromitovane
   i rotirati ih.

> **Redosled je bitan [Z]:** isključivanje `DEBUG`-a bez rešavanja medija prekida
> prikaz slika vozila i dokumenata.


**Šta je urađeno (19.09.2026.) [P]:**

| Korak | Stanje |
|---|---|
| 1. Tajne u promenljive okruženja | **Urađeno.** `SECRET_KEY`, korisnik, lozinka, server i ime baze čitaju se iz `.env`, koji je u `.gitignore`. Uzor je `.env.example`. |
| 2. `DEBUG` iz okruženja | **Urađeno.** `DJANGO_DEBUG`; podrazumevano **`False`**, a `.env` za razvoj postavlja `True`. |
| 3. Nov `SECRET_KEY` | **Urađeno.** Generisan je nov ključ; stari više nigde ne stoji. |
| 4. Nova lozinka baze | **Nije urađeno** — menja se na serveru, pa se upiše u `.env`. |
| 5. Prepisivanje istorije | **Nije urađeno** |

Uvedene su i dve pomoćne funkcije u `ims_erp/settings/base.py` [P]:

| Funkcija | Šta radi |
|---|---|
| `env_required(name)` | Diže `ImproperlyConfigured` sa jasnom porukom ako promenljiva nedostaje — umesto tihog pada na podrazumevanu vrednost |
| `database_credentials()` | Jedno mesto za pristupne podatke, koje koriste i `development.py` i `production.py` |

> ⚠ **Dve stvari koje i dalje stoje:**
>
> 1. **Stari `SECRET_KEY` i lozinka `Rajo123` ostaju u git istoriji.** Dok se istorija ne
>    prepiše, treba ih smatrati kompromitovanim — **lozinku baze promeniti na serveru**.
> 2. **Promena `SECRET_KEY`-a poništava sve prijave.** Pri prvom restartu svi korisnici
>    se odjavljuju i moraju ponovo da se prijave. To je jednokratno.

> **[P] `DEBUG = False` i dalje prekida prikaz slika.** `ims_erp/urls.py` opslužuje `media/`
> samo kada je `DEBUG=True`. Pre prebacivanja produkcije na `False` treba podesiti
> opsluživanje `media/` preko web servera.

---

#### P-48 — Lični podaci i brojevi računa 329 osoba u repozitorijumu

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Delimično rešeno 18.09.2026. — **podaci ostaju u istoriji** |
| **Gde** | `internal.txt.json`, `Virman-165-B5-2.TXT`, `Virman-165-B4-4 primer.TXT.20260520104653` |
| **Otkriveno** | 18.09.2026., pri čišćenju repozitorijuma |

**Šta je zatečeno [P]:** tri datoteke u korenu projekta sadrže **stvarne podatke o
isplatama fizičkim licima**, i sve tri su **u git istoriji**.

| Datoteka | Sadržaj | U istoriji od |
|---|---|---|
| `internal.txt.json` (437 KB) | **329 zapisa, 329 različitih imena i 329 različitih brojeva računa**, adrese, iznosi, ukupno 3.290.000,00, datum 29.04.2022. | `cfee1f6` |
| `Virman-165-B5-2.TXT` | 21 red — imena, brojevi računa, „Upl.zarade“ | `458498a` |
| `Virman-165-B4-4 primer.TXT.20260520104653` | 4 reda istog oblika | `458498a` |

Polja u `internal.txt.json` [P]: `CreditorName`, `CreditorAddress`, `CreditorBankAccount`,
`Amount`, `PaymentBasis` („Prihodi van radnog odnosa“), `DebtorBankAccount`.

**Posledica [Z]:** svako ko ima pristup repozitorijumu — ili bilo kojoj njegovoj kopiji —
ima **imena, adrese, brojeve tekućih računa i iznose isplata 329 osoba**. Ovo je ista
vrsta problema kao [P-01](#p-01--tajne-i-debug-u-repozitorijumu), ali se tiče **podataka o
ljudima**, a ne pristupa sistemu.

**Zašto se ne rešava prostim brisanjem [P]:** datoteke su **komitovane**. Brisanje iz
radnog direktorijuma ih uklanja iz zatečenog stanja, ali **ostaju u istoriji svakog klona**.
Stvarno uklanjanje traži prepisivanje istorije (`git filter-repo`) i usaglašavanje sa svima
koji imaju kopiju.

**Dodatna zapetljanost [P]:** `Virman-165-B5-2.TXT` **koristе dva testa** —
`isplate/tests.py:161` i `:410`. Ne može se samo obrisati; treba ga **zameniti izmišljenim
podacima** istog oblika (180 znakova, cp1250), pa tek onda ukloniti original.

**Predlog koraka [Z]:**

1. Potvrditi sa odgovornim licem za zaštitu podataka da su to stvarni podaci.
2. Napraviti sintetički uzorak za `isplate/tests.py` i prevezati testove na njega.
3. Ukloniti sve tri datoteke iz zatečenog stanja i dodati pravilo u `.gitignore`.
4. Odlučiti o prepisivanju istorije — zajedno sa [P-01](#p-01--tajne-i-debug-u-repozitorijumu),
   jer se i tajne uklanjaju istim postupkom.

**Šta je urađeno (18.09.2026.) [P]:**

| Korak | Stanje |
|---|---|
| 1. Potvrda da su podaci stvarni | **Nije urađeno** — traži potvrdu odgovornog lica |
| 2. Sintetički uzorak za testove | **Urađeno.** `isplate/test_data/virman-uzorak.TXT` — 19 stavki sa izmišljenim imenima i brojevima računa, isti oblik (180 znakova, cp1250). Oba testa prevezana i prolaze. |
| 3. Uklanjanje datoteka iz zatečenog stanja | **Urađeno.** Sve tri su obrisane. |
| 4. Prepisivanje istorije | **Nije urađeno** |

> ⚠ **Problem nije rešen.** Datoteke više nisu u radnom direktorijumu, ali su **i dalje u
> svakoj kopiji repozitorijuma**, u izmenama `cfee1f6` i `458498a`. Dok se istorija ne
> prepiše (`git filter-repo`), imena, adrese i brojevi računa 329 osoba ostaju dostupni
> svakome ko ima klon. To se radi **zajedno sa** [P-01](#p-01--tajne-i-debug-u-repozitorijumu),
> jer se tajne uklanjaju istim postupkom, i traži usaglašavanje sa svima koji imaju kopiju.

**Šta je time dobijeno [P]:** projektu **više nisu potrebni stvarni podaci** — testovi rade
nad izmišljenim uzorkom. Prepisivanje istorije zato više ništa ne lomi.

---

### 10.4. Obračuni — Flota

#### P-02 — Prosečna potrošnja ne proverava stariju granicu

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/fuel.py:320-347`, funkcija `calculate_average_fuel_consumption()` |
| **Obračun** | [V-01](#v-01--prosečna-potrošnja-goriva-poslednjih-10-točenja) |
| **Pitanje** | Q13 |

**Šta je zatečeno [P]:** obračun bira prozor točenja `[k, 9−k]`, gde je `k` najnovije
točenje sa `mileage > 0`. **Novija granica se proverava, starija (`9−k`) ne.**

**Posledica [P]:** ako starije granično točenje ima kilometražu 0, pređeni put postaje
cela kilometraža vozila:

| | Stvarno | Prikazano |
|---|---|---|
| Pređeni put | ~1.500 km | 128.000 km |
| Potrošnja | ~6 l/100 km | **~0,07 l/100 km** |

Bez ijednog upozorenja na ekranu.

**Predlog rešenja [Z]:** primeniti isto pravilo kao u
`calculate_average_fuel_consumption_ever()`, koji **jeste** ispravan — obe granice tražiti
među točenjima sa `mileage > 0`.

**Pre ispravke proveriti [Z]:** koliko vozila trenutno prikazuje besmisleno nisku
potrošnju — to je i provera da li se problem stvarno javlja u radu.


**Šta je urađeno (19.09.2026.) [P]:** obe granice prozora se sada traže među točenjima sa
`mileage > 0`, po istom postupku kao u `calculate_average_fuel_consumption_ever()`:

```python
newest_index = next((i for i, entry in enumerate(last_10_consumptions) if entry.mileage > 0), None)
oldest_index = next((i for i in range(len(last_10_consumptions) - 1, -1, -1)
                     if last_10_consumptions[i].mileage > 0), None)
if newest_index is None or oldest_index is None or newest_index >= oldest_index:
    return None
```

Dodata su i **dva uslova zdravog razuma** [P]:

1. Novija granica mora biti **stvarno novija** od starije (`newest_index < oldest_index`).
2. **Kilometraža novije granice mora biti veća** od starije (`total_mileage > 0`).

Kada nijedan od uslova nije ispunjen, vraća se `None` — na ekranu **nema broja**, umesto
izmišljenog. To je bolje nego prikazati 0,07 l/100 km.

**Testovi [P]:** `fleet/test_cost_fixes.py: AverageFuelConsumptionTests` — tri slučaja:
nula na starijoj granici, kilometraža koja ne raste, i samo jedno točenje sa kilometražom.

---

#### P-03 — Procena kilometraže koristi očitavanja izvan perioda

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (19.09.2026.) — novim modulom |
| **Gde** | `fleet/support/dashboard.py:89-101`, `_estimate_period_mileage()` |
| **Obračun** | [V-08](#v-08--procena-pređene-kilometraže-u-periodu) |

**Šta je zatečeno [P]:** pri izboru para očitavanja prolaze se **sva** očitavanja vozila,
bez ograničenja na traženi period. Bira se par sa najmanjim zbirom udaljenosti od granica
perioda, ali **udaljenost nije ograničena**.

**Posledica [Z]:** za vozilo koje u periodu nema nijedno očitavanje, kilometraža se ipak
procenjuje — iz očitavanja starih mesecima ili godinama. Ta procena zatim postaje
imenilac troška po kilometru (V-07).

**Primer [Z]:** vozilo sa očitavanjima samo iz 2024. dobiće procenu i za mart 2026,
kao da se vozilo i dalje kreće istim tempom.

**Predlog rešenja [Z]:** uvesti gornju granicu udaljenosti očitavanja od perioda
(npr. 90 dana), a izvan nje vratiti „Nema podatka“ umesto procene.

> **Pre izmene potrebna potvrda [N]:** moguće je da je ovakvo ponašanje namerno, da bi
> se izbeglo da vozila bez skorašnjih očitavanja nestanu iz analitike. Vidi **P-09**.


**Zašto je ovo problem — dopuna (19.09.2026.) [Z]:**

Izbor para očitavanja gleda **sva** očitavanja vozila i bira ono koje je **najbliže**
granicama perioda. Reč „najbliže“ tu nema gornju granicu — ako je najbliže očitavanje
staro dve godine, ono se svejedno uzima.

| Šta korisnik vidi | Šta se zapravo dogodilo |
|---|---|
| Kolona „Kilometraža“ pokazuje npr. **2.480 km** za mart 2026. | Vozilo u martu 2026. **nema nijedno očitavanje**. Uzet je dnevni prosek iz 2024. i pomnožen brojem dana u martu. |
| Kolona „RSD/km“ pokazuje npr. **41,20** | Imenilac je taj izmišljeni broj, pa je i cena po km izmišljena. |
| Kolona „Izvor“ pokazuje „Točenja (okvirno)“ | To je jedini nagoveštaj, i lako se previdi. |

**Suština [Z]:** broj ne izgleda kao procena. Stoji u istoj koloni, istim formatom, pored
vozila koja **imaju** stvarna očitavanja. Rukovodilac ih poredi kao da su ista vrsta
podatka — a jedan je izmeren, drugi izveden iz podataka od pre dve godine.

> **Zašto možda i nije greška [N]:** bez te procene vozila bez skorašnjih očitavanja
> dobila bi „Nema podatka“. Ranije su takva vozila, ako uz to nisu imala ni trošak,
> **potpuno nestajala** sa spiska — vidi [P-09](#p-09--vozila-sa-troškom-nula-ili-manjim-nestaju-iz-spiska),
> koji je rešen 19.09.2026.. Sada vozilo ostaje na spisku i kada nema podataka, pa „Nema podatka“
> više ne znači da vozilo nestaje.

**Šta treba odlučiti [N]:** dokle unazad očitavanje sme da posluži kao osnova procene.
Predlog je **90 dana** od granice perioda; izvan toga prikazati „Nema podatka“. Tačan broj
dana je poslovna odluka.


**Šta je urađeno (19.09.2026.) [P]:** novi modul ekonomike **ne ekstrapolira kilometražu**.

```python
distance = observed if points and points[0]['date'] == start and points[-1]['date'] == end and start < end else None
```

RSD/km se računa **samo kada očitavanja postoje na oba granična datuma**. Inače stoji
upozorenje *„Nema usklađenih očitanja za oba granična datuma; RSD/km se ne računa.“*

**Time je odgovoreno i na pitanje „šta ako vozilo stoji“ [Z]:** ako se svako točenje
evidentira, **odsustvo točenja znači da vozilo nije radilo**. Ranija logika je iz toga
izvlačila suprotan zaključak — posegnula bi za očitavanjem od pre dve godine i prikazala
kilometražu koje nije bilo. Vozilo koje košta a ne radi tako je izgledalo **najzdravije u
floti**, jer se trošak delio izmišljenim brojem kilometara.

> **[P] Nasleđena `vehicle_cost_per_km_rows()` i dalje ekstrapolira**, ali je **ne koristi
> nijedan ekran** — ostala je radi kompatibilnosti postojećih testova.

> **Dopuna 21.09.2026. — usvojeno po zahtevu korisnika:** prethodni strogi
> uslov je zamenjen najbližim stvarnim očitavanjem za svaku granicu, iz točenja
> ili naloga zaduženja. Mogu se usvojiti i datumi van perioda; prikazuju se
> oba stanja, datumi, izvori i odstupanje u danima. RSD/km je tada približan,
> dok troškovi ostaju u traženom periodu. Nema ekstrapolacije; jedan datum
> ili pad brojača ne daje obračun. Nije uveden proizvoljan limit od 90 dana.
> Odsustvo točenja samo po sebi ne dokazuje da vozilo nije radilo.

---

#### P-04 — Kvadratna složenost izbora para očitavanja

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:91-101` |

**Šta je zatečeno [P]:** dvostruka petlja „svako sa svakim“ preko svih očitavanja vozila.
Vozilo sa 1.000 očitavanja daje milion poređenja, i to **za svako vozilo** pri svakom
otvaranju analitike flote.

**Posledica [Z]:** sporo otvaranje ekrana analitike, rastuće sa starošću sistema.

**Predlog rešenja [Z]:** pošto su očitavanja sortirana po datumu, dovoljno je posmatrati
samo očitavanja najbliža granicama perioda — složenost pada na linearnu.


**Šta je urađeno (19.09.2026.) [P]:** dvostruka petlja zamenjena je funkcijom
`_best_reading_pair()`, koja očitavanja obilazi **jednom**, po datumu.

| | Ranije | Sada |
|---|---|---|
| Složenost | `O(n²)` | **`O(n log n)`** |
| Vozilo sa 1.000 očitavanja | ~1.000.000 poređenja | ~10.000 koraka |

Najbolji kandidat za početak para pamti se u **Fenwick stablu** po rangu kilometraže, pa
upit „najbolji početak sa manjom kilometražom“ traje logaritamski.

> **[P] Rezultat je isti, uključujući i izbor pri izjednačenju.** Kada više parova ima isti
> zbir udaljenosti, bira se isti par koji bi našla i ranija petlja — najmanji indeks
> početka, pa najmanji indeks kraja.

**Test [P]:** `fleet/test_cost_fixes.py: BestReadingPairTests` poredi novi postupak sa
**doslovnom starom dvostrukom petljom** na 40 nasumičnih skupova očitavanja, uključujući i
padove kilometraže. Rezultati se poklapaju u svim slučajevima.

---

#### P-05 — Centar se uzima iz poslednje dodele, a ne istorijske

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** za V-07 (19.09.2026.); **V-24 nema period** |
| **Gde** | `fleet/support/dashboard.py:143-145`, `fleet/views/center_statistics.py:65-67` |
| **Obračun** | [V-07](#v-07--trošak-po-kilometru-po-vozilu), [V-24](#v-24--statistika-po-centrima) |

**Šta je zatečeno [P]:** trošak po kilometru i statistika centra koriste **poslednju**
dodelu vozila (`-assigned_date`, bez datumskog ograničenja).

**Nedoslednost [P]:** izveštaj goriva po šifri posla (V-21) i mesečni troškovi servisa
koriste **istorijsku** dodelu — onu koja je važila **na dan troška**.

**Posledica [Z]:** vozilo prebačeno iz centra 43 u centar 12 nosi **ceo istorijski trošak**
u centar 12, iako je trošak nastao u centru 43. Zbirovi po centrima iz dva različita
ekrana se ne slažu.

**Predlog rešenja [Z]:** uskladiti sa V-21 — koristiti dodelu koja je važila na datum
troška. To zahteva razlaganje troška po intervalima dodele unutar perioda.

> **Potrebna odluka [N]:** moguće je da je za analitiku flote namerno izabrana
> trenutna pripadnost, jer rukovodilac gleda „svoja“ vozila. Tada ostaje da se ta
> razlika **jasno napiše na ekranu**.


**Šta je urađeno (19.09.2026.) [P]:** trošak po kilometru (V-07) više ne koristi **trenutnu**
dodelu, nego onu koja je **važila na kraju izabranog perioda**:

```python
center_at_period_end = JobCode.objects.filter(
    vehicle=OuterRef('pk'),
    assigned_date__lte=period_end_date,
).order_by('-assigned_date', '-pk').values('organizational_unit__center')[:1]
```

**Šta to rešava [P]:** izveštaj za prošli period **više se ne menja** kada se vozilo kasnije
prebaci u drugi centar. Ranije je svaka promena centra retroaktivno menjala i već
pogledane izveštaje.

Dodata je i oznaka `center_changed_in_period` [P] — tačna kada je vozilo **unutar perioda**
dobilo novu dodelu. Time se vidi kod kojih redova pripadnost nije bila ista celog perioda.

> **[P] Šta i dalje nije rešeno:** vozilo koje je centar promenilo **usred** perioda i dalje
> nosi **ceo** trošak perioda u centar u kojem je bilo na kraju. Potpuna ispravka traži
> razlaganje svakog troška po intervalima dodele, što menja i strukturu reda (jedan red po
> vozilu i centru). Oznaka `center_changed_in_period` bar pokazuje gde se to dešava.

> **[P] Statistika centra (V-24) nije menjana** — ona nema izabrani period, prikazuje iznose
> **za ceo vek vozila**. Tamo je „poslednja dodela“ jedini mogući izbor. Vidi
> [P-14 D](#p-14--statistika-centra--četiri-odvojena-nedostatka).


> **Dopuna (19.09.2026.) [P]:** obračun se od tada izvodi u **novom modulu ekonomike**
> ([E-01](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa)), a ne u `vehicle_cost_per_km_rows()`.
> Statistika centra sada bira centar po dodeli **na kraju izabranog perioda** (`assigned_date__lte=end`), pa se ponaša isto kao analitika flote. Nasleđena funkcija zadržava ispravku, ali je **ne koristi nijedan ekran**.

---

#### P-06 — Cela premija polise ulazi u svaki period

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:214-223` |
| **Obračun** | [V-07](#v-07--trošak-po-kilometru-po-vozilu) |

**Šta je zatečeno [P]:** polisa ulazi u trošak ako se **bilo kako** preklapa sa periodom:

```
start_date <= kraj perioda  I  end_date >= početak perioda
```

Uzima se **ceo iznos premije**, bez deljenja po danima.

**Posledica [P]:** godišnja premija od 60.000 RSD ulazi u punom iznosu i u
jednomesečni period, gde bi srazmerno bilo oko 5.000 RSD. Trošak po kilometru je
**višestruko uvećan** za kratke periode.

Za godišnju premiju od 60.000 RSD (polisa važi 365 dana):

| Period | Dana | Srazmerno | Sistem računa | Odstupanje |
|---|---|---|---|---|
| Godina dana | 365 | 60.000,00 | 60.000,00 | 0 |
| Tri meseca (01.01.–31.03.) | 89 | 14.630,14 | **60.000,00** | **+310%** |
| Mesec dana (mart) | 30 | 4.931,51 | **60.000,00** | **+1.117%** |

**Predlog rešenja [Z]:** primeniti isti postupak kao kod dugoročnog najma —
deliti premiju po danima preklapanja sa važenjem polise:

> deo premije = premija × (dana preklapanja) / (dana važenja polise)


**Šta je urađeno (19.09.2026.) [P]:** premija se deli srazmerno danima preklapanja:

```python
policy_days = (policy['end_date'] - policy['start_date']).days + 1
days = days_of_overlap(policy['start_date'], policy['end_date'],
                       period_start_date, period_end_date)
policy_cost_by_vehicle[policy['vehicle_id']] += (
    float(policy['premium_amount'] or 0) * days / policy_days
)
```

Obračun je premešten iz SQL podupita u Python, jer deljenje po danima traži datume svake
polise posebno. Polise bez datuma početka ili kraja se **ne uzimaju** — ranije su ulazile u
punom iznosu. [P]

**Provera na primeru iz opisa [P]** — godišnja premija 60.000 RSD:

| Period | Dana | Ranije | Sada |
|---|---|---|---|
| Godina dana | 365 | 60.000,00 | **60.000,00** |
| Mart (31 dan) | 31 | 60.000,00 | **5.095,89** |

> **Posledica za korisnika [Z]:** trošak po kilometru za kratke periode **biće znatno
> manji nego ranije**. Raniji je bio uvećan i do jedanaest puta.

**Testovi [P]:** `fleet/test_cost_fixes.py` — jedan za jednomesečni period, jedan za celu
godinu (gde ceo iznos i dalje ulazi).


> **Dopuna (19.09.2026.) [P]:** obračun se od tada izvodi u **novom modulu ekonomike**
> ([E-01](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa)), a ne u `vehicle_cost_per_km_rows()`.
> Novi modul deli premiju **dan po dan** (`premium_amount / broj dana polise`), što je tačnije od deljenja srazmerno periodu. Nasleđena funkcija zadržava ispravku, ali je **ne koristi nijedan ekran**.

---

#### P-07 — Cela godišnja kamata lizinga ulazi u svaki period

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:224-234` |
| **Obračun** | [V-07](#v-07--trošak-po-kilometru-po-vozilu) |

**Šta je zatečeno [P]:** kamata finansijskog lizinga se uzima za **sve godine koje period
dodiruje** (`year in range(početna godina, krajnja godina + 1)`), u **punom godišnjem
iznosu**.

**Posledica [Z]:** period od 01.12.2025. do 31.01.2026. povlači **dve pune godišnje
kamate** (2025. i 2026.) za dva meseca troška.

**Predlog rešenja [Z]:** deliti godišnju kamatu po danima preklapanja perioda sa tom
kalendarskom godinom.


**Šta je urađeno (19.09.2026.) [P]:** godišnja kamata se deli srazmerno danima preklapanja
perioda sa **tom kalendarskom godinom**:

```python
days = days_of_overlap(date(year, 1, 1), date(year, 12, 31),
                       period_start_date, period_end_date)
days_in_year = 366 if calendar.isleap(year) else 365
financial_interest_by_vehicle[interest['lease__vehicle_id']] += (
    float(interest['interest_amount'] or 0) * days / days_in_year
)
```

**Prestupna godina se poštuje** — imenilac je 366 dana kada treba. [P]

**Provera na primeru iz opisa [P]** — kamata 36.500 RSD za 2025. i isto toliko za 2026.,
period 01.12.2025.–31.01.2026.:

| | Ranije | Sada |
|---|---|---|
| Ulazi u trošak | 73.000,00 (dve pune godine) | **6.200,00** (31 + 31 dan) |

**Test [P]:** `fleet/test_cost_fixes.py: test_financial_lease_interest_is_split_per_calendar_year`.


> **Dopuna (19.09.2026.) [P]:** obračun se od tada izvodi u **novom modulu ekonomike**
> ([E-01](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa)), a ne u `vehicle_cost_per_km_rows()`.
> Novi modul deli kamatu **dan po dan** (`amount / 365 ili 366`), i to samo dok traje ugovorno raspolaganje. Nasleđena funkcija zadržava ispravku, ali je **ne koristi nijedan ekran**.

---

#### P-08 — Operativni lizing se deli drugačije od dugoročnog najma

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** (19.09.2026.) — novom kolonom |
| **Gde** | `fleet/support/dashboard.py:274-285` |

**Šta je zatečeno [P]:** ista kolona `current_payment_amount` („Trenutna rata / iznos
otplate“) tumači se na dva načina:

| Vrsta | Tumačenje | Formula |
|---|---|---|
| Dugoročni najam | **Mesečna rata** | Deli se po danima svakog meseca |
| Operativni lizing | **Ukupan iznos** | rata × dana preklapanja / ukupno dana ugovora |

**Posledica [Z]:** za operativni lizing sa mesečnom ratom od 50.000 RSD i ugovorom od
tri godine, u mesec dana ulazi samo ~1.370 RSD umesto ~50.000 RSD. Trošak operativnog
lizinga je **drastično potcenjen**.

**Predlog rešenja [Z]:** potvrditi šta kolona stvarno sadrži za operativni lizing,
pa primeniti isto pravilo kao kod dugoročnog najma ako je reč o mesečnoj rati.

> **Potrebna potvrda [N]:** verovatno je reč o grešci, ali je moguće da se kod
> operativnog lizinga u ovu kolonu unosi ukupan iznos ugovora. To se mora proveriti
> u podacima pre bilo kakve izmene.


**Kako ovo rešiti — predlog (19.09.2026.) [Z]:**

Problem nije u kodu nego u **značenju kolone**. Ista kolona `current_payment_amount` ne može
istovremeno biti mesečna rata i ukupan iznos ugovora. Zato ispravka **ne sme** početi od
koda.

**Korak 1 — utvrditi šta kolona sadrži.** Upit koji to pokazuje bez ikakve izmene podataka:

```sql
SELECT lease_type,
       COUNT(*)                                   AS ugovora,
       AVG(current_payment_amount)                AS prosecan_iznos,
       AVG(DATEDIFF(month, start_date, end_date)) AS prosecno_meseci,
       AVG(current_payment_amount /
           NULLIF(DATEDIFF(month, start_date, end_date), 0)) AS iznos_po_mesecu
FROM fleet_lease
WHERE lease_type <> 'finansijski'
GROUP BY lease_type;
```

**Kako pročitati rezultat [Z]:**

| Nalaz | Zaključak |
|---|---|
| `prosecan_iznos` operativnog lizinga je **istog reda veličine** kao kod dugoročnog najma | Kolona je **mesečna rata** → greška u kodu, primeniti isto pravilo kao za najam |
| `prosecan_iznos` je **desetinama puta veći** (npr. 1.800.000 naspram 50.000) | Kolona je **ukupan iznos ugovora** → kod je ispravan, ali naziv kolone obmanjuje |
| Nalazi se **mešaju** unutar iste vrste | Podaci su neujednačeni — treba ih **razdvojiti pre** bilo kakve izmene koda |

**Korak 2 — po nalazu:**

- Ako je mesečna rata: izbaciti poseban slučaj i pustiti operativni lizing kroz
  `monthly_cost_for_overlap()`, isto kao dugoročni najam. Izmena je **tri reda**.
- Ako je ukupan iznos: kod ostaje, ali se **preimenuje polje na ekranu** u
  „Ukupan iznos ugovora“ za operativni lizing, i doda napomena u ovo poglavlje.
- Ako je mešano: prvo razdvojiti u dve kolone ili uvesti oznaku šta iznos znači.

> **Zašto ne odmah ispraviti [Z]:** ako je kolona ukupan iznos, „ispravka“ bi trošak
> operativnog lizinga uvećala **36 puta** za trogodišnji ugovor. Pogrešna pretpostavka
> ovde je skuplja od čekanja na proveru.

**Q45:** kakav je stvarni sadržaj kolone „Trenutna rata / iznos otplate“ za operativni
lizing — mesečna rata ili ukupan iznos ugovora?


**Šta je urađeno (19.09.2026.) [P]:** umesto da se pogađa šta dvosmislena kolona znači, uveden je
**nov podatak kod kojeg se zna** — `LeaseChargePeriod`:

| Polje | Značenje |
|---|---|
| `amount` | Potvrđen iznos |
| **`basis`** | **`monthly`** (mesečni iznos) ili **`total`** (ukupan iznos perioda) |
| `start`, `end` | Period na koji se iznos odnosi |
| dokument | Osnov iz kojeg je iznos preuzet |

Obračun po tome deli iznos:

```python
divisor = calendar.monthrange(day.year, day.month)[1] if c.basis == 'monthly' \
          else (c.end - c.start).days + 1
```

> **[P] Stara kolona `current_payment_amount` se u novom obračunu više ne čita.**
> Metodologija izričito kaže da se iz nje ništa ne izvodi. Time **Q45 otpada** za novi
> obračun — pitanje ostaje samo ako neko bude tumačio istorijske podatke.

Ovo je bio i vaš predlog: dodati kolone i tačno definisati šta je šta.

---

#### P-09 — Vozila sa troškom nula ili manjim nestaju iz spiska

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:323-324` |

**Šta je zatečeno [P]:**

```python
if total_cost <= 0:
    continue
```

**Posledica [Z]:** vozilo bez ijednog evidentiranog troška u periodu, ili vozilo kod
koga je naknada osiguranja veća od troškova, **potpuno nestaje** iz analitike flote.
Korisnik ne dobija nikakvo objašnjenje i može zaključiti da vozilo ne postoji.

**Predlog rešenja [Z]:** prikazati vozilo sa oznakom „Nema evidentiranog troška u
periodu“ umesto izostavljanja, ili barem prikazati broj izostavljenih vozila.


**Šta je urađeno (19.09.2026.) [P]:** vozilo ostaje na spisku, sa jasnom oznakom zašto nema
cenu po kilometru:

```python
has_cost = total_cost > 0
cost_per_km = total_cost / annual_km if has_cost and annual_km > 0 else None
no_cost_note = None
if not has_cost:
    no_cost_note = ("Nema evidentiranog troška u periodu" if total_cost == 0
                    else "Naknade osiguranja su veće od evidentiranih troškova u periodu")
```

Razlikuju se **dva različita slučaja** koja su ranije oba završavala tako što vozilo
nestane [P]:

| Slučaj | Poruka |
|---|---|
| `total_cost == 0` | „Nema evidentiranog troška u periodu“ |
| `total_cost < 0` | „Naknade osiguranja su veće od evidentiranih troškova u periodu“ |

Na ekranu se u koloni RSD/km prikazuje **crtica** sa objašnjenjem u opisu, umesto praznog
polja. [P]

> **[P] Takvo vozilo ne kvari ostale pokazatelje:** `cost_per_km` je `None`, pa vozilo
> **ne ulazi** u proseke i pragove po klasi mase, niti može biti proglašeno „Neisplativim“
> u analizi kroz više perioda.

**Testovi [P]:** `fleet/test_cost_fixes.py` — vozilo bez ijednog troška i vozilo kod koga
je naknada osiguranja veća od troškova.


> **Dopuna (19.09.2026.) [P]:** obračun se od tada izvodi u **novom modulu ekonomike**
> ([E-01](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa)), a ne u `vehicle_cost_per_km_rows()`.
> U novom modulu vozilo bez troška ostaje u rezultatu, a svi iznosi su `None` (`has_cost`), pa ne ulaze ni u zbirove ni u pondere. Nasleđena funkcija zadržava ispravku, ali je **ne koristi nijedan ekran**.

---

#### P-10 — Napomena o maloj kilometraži poredi period sa godinom

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `fleet/support/dashboard.py:328-339` |

**Šta je zatečeno [P]:** prag od 15.000 km poredi se sa **procenjenom kilometražom
perioda**, a poruka govori o **godišnjoj** kilometraži:

> *„Vozilo se malo vozi (… km < 15000 km godišnje).“*

**Posledica [Z]:** za jednomesečni period gotovo **svako** vozilo dobija to upozorenje,
pa ono gubi smisao.

**Predlog rešenja [Z]:** preračunati kilometražu na godišnji nivo pre poređenja
(`km × 365 / dana perioda`), ili prag skalirati dužinom perioda.


**Šta je urađeno (18.09.2026.) [P]:** u `fleet/support/dashboard.py` kilometraža se pre
poređenja svodi na godišnji nivo, a poruka prikazuje **tu preračunatu vrednost**:

```python
annualized_km = annual_km / period_days * 365 if annual_km > 0 else 0
below_mileage_threshold = 0 < annualized_km < low_mileage_threshold
```

Preračunata vrednost je dodata i u red tabele kao `annualized_km`, da bi bila dostupna
ekranima. Prag od 15.000 km nije menjan — i dalje je upisan u kod, videti
[P-11](#p-11--pragovi-troška-po-km-su-upisani-u-kod).

---

#### P-11 — Pragovi troška po km su upisani u kod

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** (19.09.2026.) — prag se unosi |
| **Gde** | `fleet/support/analytics.py:14-19` |
| **Pitanje** | Q18 |

**Šta je zatečeno [P]:** četiri klase mase i po tri praga upisani su u konstantu
`_WEIGHT_CLASS_THRESHOLDS`. Nema ih u bazi i ne mogu se menjati kroz interfejs.

**Posledice [Z]:**

1. Promena pragova zahteva izmenu koda i isporuku nove verzije.
2. Nigde nije zabeleženo **odakle pragovi potiču** ni kada su poslednji put provereni.
3. Vozilo **bez unete maksimalne dozvoljene mase nema prag** i ostaje bez ocene,
   bez upozorenja da nedostaje podatak.

**Predlog rešenja [Z]:** preseliti pragove u šifarnik u bazi sa ekranom za održavanje,
i dodati upozorenje za vozila bez unete mase.


**Šta je urađeno (19.09.2026.) [P]:** pragovi po klasi mase više se ne koriste. Kontrolni prag se
**unosi po vozilu**, u `VehicleAnalysisProfile`:

| Polje | Uloga |
|---|---|
| `cost_limit_km`, `cost_limit_day` | Prag, opcion |
| `criterion_source` | **Obavezan pisani osnov** — izvor, datum, obuhvat |
| `criterion_basis` | Način raspolaganja na koji se prag odnosi |

Provere u modelu [P]: prag bez osnova i bez izabranog raspolaganja se **ne prima**; za
bušeću mašinu i priključno vozilo RSD/km se **ne može uneti** kao merilo opravdanosti.
Prag se ne primenjuje kada period obuhvata više profila.

> **Prekoračenje znači pregled kriterijuma, ne automatsku zamenu.** [P]

> **[P]** Nasleđeni pragovi po masi (`_WEIGHT_CLASS_THRESHOLDS`) ostali su u
> `fleet/support/analytics.py` radi postojećih testova, ali ih **ne koristi nijedan ekran**.

> **[N] Predlog dorade:** prag nema svoj datum važenja (deli ga sa profilom), nema donjeg
> praga uzorka ispod kojeg se ne primenjuje, i daje samo „preko / ispod“ bez međunivoa.

---

#### P-12 — Analiza kroz više perioda zahteva najmanje dva perioda

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | **Otpalo** (19.09.2026.) — ekran uklonjen |
| **Gde** | `fleet/support/dashboard.py:401-403` |

**Šta je zatečeno [P]:** funkcija bez provere koristi `periods[1]`. Poziv sa jednim
periodom prekida se greškom.

**Predlog rešenja [Z]:** proveriti broj perioda i vratiti prazan spisak trajno
neisplativih vozila ako ih je manje od dva.


**Stanje od 19.09.2026. [P]:** ekran analize kroz više perioda **više ne postoji**. Funkcija
`cost_per_km_period_analysis()` ostala je u `fleet/support/dashboard.py`, ali je **ne poziva
nijedna ruta** — samo se ponovo izvozi u `fleet/views/__init__.py`.

> **Ovo nije ispravka nego nestanak.** Ako se višeperiodno poređenje vrati, uslov od
> najmanje dva perioda treba rešiti pre povratka. Novi modul poređenje alternativa rešava
> drugačije — kroz sačuvanu procenu [E-02](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa).

---

#### P-13 — Superuser ne može da otvori statistiku centra

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `fleet/views/center_statistics.py:58-59` |

**Šta je zatečeno [P]:**

```python
if not request.user.allowed_centers.filter(center=center_code).exists():
    return HttpResponseForbidden("Nemate pristup ovim podacima.")
```

Provera **ne izuzima `is_superuser`**, za razliku od svih ostalih provera u sistemu
(`core/mixins.py`).

**Posledica [P]:** administrator sistema koji nema izričito upisane dozvoljene centre
dobija **403 Zabranjeno** na ekranu statistike centra.

**Predlog rešenja [Z]:** dodati izuzeće za `is_superuser`, kao u
`RolePermissionRequiredMixin`.


**Šta je urađeno (18.09.2026.) [P]:** provera je usklađena sa
`RolePermissionRequiredMixin`:

```python
if not request.user.is_superuser and not request.user.allowed_centers.filter(center=center_code).exists():
    return HttpResponseForbidden("Nemate pristup ovim podacima.")
```

---

#### P-14 — Statistika centra — četiri odvojena nedostatka

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** A i D; **B i C otpali** (19.09.2026.) |
| **Gde** | `fleet/views/center_statistics.py` |

**A) Otpisana vozila ulaze u statistiku [P]** (linija 61)

Za razliku od analitike flote i preseka stanja, ovde **nema filtera `otpis=False`**.
Otpisano vozilo i dalje uvećava broj vozila, vrednost i troškove centra.

**B) Prosečna starost računa i vozila bez godine proizvodnje [P]** (linije 75-79)

```python
sum((vehicle.year_of_manufacture or 0) for vehicle in center_vehicles) / center_vehicle_count
```

Vozilo bez unete godine ulazi kao **0**, pa prosečna godina pada, a „prosečna starost“
(tekuća godina − prosek) postaje **besmisleno velika**.

> Primer: dva vozila, jedno iz 2020, jedno bez godine → prosek = 1010 →
> prikazana prosečna starost **1.016 godina**.

Presek stanja flote (`fleet_snapshot`) isti problem **rešava ispravno** — tamo se
računaju samo vozila sa godinom između 1886. i tekuće. [P]

**C) Kategorije popravki se traže bez dijakritika [P]** (linije 132-135)

Mesečni pregled traži nazive `gume`, `redovan servis`, `tehnicki pregled`, `registracija`.
Kategorija nazvana **„Tehnički pregled“** (sa „č“) **neće biti prepoznata** i njen iznos
neće se pojaviti ni u jednoj koloni.

**D) Iznosi su za ceo vek vozila, bez izbora perioda [P]**

Svi zbirovi (servisi, trebovanja, gorivo, naknade) idu **bez filtera datuma**.
Na ekranu to nije naznačeno, pa korisnik lako pomisli da gleda tekuću godinu.

**Predlog rešenja [Z]:**

1. Dodati `otpis=False`.
2. Preuzeti način računanja starosti iz `fleet_snapshot`.
3. Kategorije prepoznavati preko `ServiceType` šifre umesto po nazivu, ili normalizovati
   dijakritike kao u `fleet/support/vehicle_maintenance.py: service_category()`,
   koji to **već radi ispravno**.
4. Dodati izbor perioda ili jasno napisati „za ceo vek vozila“.


**Šta je urađeno (18.09.2026.) [P]:**

| | Ispravka |
|---|---|
| **A** | Dodat `otpis=False` u izbor vozila centra. |
| **B** | Prosečna starost se računa **samo iz vozila sa godinom između 1886. i tekuće**, kao u `fleet_snapshot`. Kad nijedno vozilo nema godinu, prikazuje se `—` umesto broja. Ekran uz to prikazuje i **koliko vozila ima poznato godište** (`poznato godište X/Y`), da prosek ne bi obmanuo kad je poznat za mali deo voznog parka. |
| **C** | Kategorije se više ne traže po nazivu. Nazivi iz `ServiceType` se **normalizuju** (mala slova, uklonjeni dijakritici) i po tome se dobija spisak šifara, pa se filtrira po šifri. „Tehnički pregled“ i „Tehnicki pregled“ od sada ulaze u isti zbir. |
| **C — dopuna** | Pri ispravci je utvrđeno da se iznos za **tehnički pregled uopšte nije prikazivao**: računao se, upisivao u podatke ekrana, ali nije bio ni u zbirovima (`numeric_fields`) ni u tabeli u šablonu. Bez toga bi ispravka prepoznavanja ostala nevidljiva, pa je **dodata kolona „Trošak Tehnički Pregled (Din)“** u mesečni pregled, sa zbirom i mesečnim prosekom. |

> **Očekivana promena na ekranu [Z]:** u mesečnom pregledu se pojavljuje **nova kolona**
> za tehnički pregled, a ukupni iznosi centra mogu **pasti** jer su otpisana vozila izašla
> iz obračuna. Oba pomaka su ispravka, ne greška.

**D nije menjano.** Iznosi su i dalje za ceo vek vozila i to na ekranu nije naznačeno —
za to je potrebna odluka da li dodati izbor perioda ili samo napisati napomenu.


**Stanje posle prepravke statistike centra (19.09.2026.) [P]:** ekran više ne računa ništa sam —
`center_statistics` je sveden na 18 redova i prosleđuje sve `render_fleet_analysis()`.

| | Stanje |
|---|---|
| **A** — otpisana vozila | **Rešeno.** Uključivanje otpisanih je sada **izbor korisnika** (`include_retired`), ne prećutno |
| **B** — prosečna starost | **Pokazatelj je uklonjen** sa tog ekrana. Ispravan obračun i dalje postoji u preseku stanja flote (`fleet_snapshot.py`), odakle je i preuzet |
| **C** — kategorije popravki | **Pokazatelj je uklonjen.** Mesečni pregled po kategorijama više ne postoji; nestala je i kolona za tehnički pregled dodata 18.09. |
| **D** — iznosi za ceo vek vozila | **Rešeno.** Ekran sada ima **izbor perioda**, isti kao analitika flote |

> **[Z] Pošteno rečeno:** B i C nisu ispravljeni nego su **otpali sa uklanjanjem
> pokazatelja**. Ako se prosečna starost i pregled po kategorijama vrate, treba ih preuzeti
> iz `fleet_snapshot.py`, odnosno normalizovati nazive kategorija — ne pisati iznova.

---

#### P-23 — Lizing se prikazuje samo u mesecu početka ugovora

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za rešavanje |
| **Gde** | `fleet/support/lease_queries.py:13-14` |
| **Obračun** | [V-19](#v-19--mesečni-troškovi-lizinga) |

**Šta je zatečeno [P]:** izveštaj grupiše ugovore po `TruncYear`/`TruncMonth` nad
poljem **`start_date`** — datumom početka ugovora.

**Posledica [P]:** ugovor koji traje tri godine pojavljuje se u izveštaju **jednom**,
u mesecu u kome je potpisan. Za bilo koji kasniji mesec izveštaj **ne prikazuje** njegovu
ratu, iako ona i dalje tereti troškove.

> Izveštaj se zove „Mesečni troškovi lizinga“, ali **ne prikazuje mesečni trošak** —
> prikazuje **kada su ugovori počeli**.

**Predlog rešenja [Z]:** razložiti svaki ugovor na mesece njegovog trajanja, kao što
to već radi trošak po kilometru (`monthly_cost_for_overlap()` u
`fleet/support/dashboard.py:239`), pa grupisati po tim mesecima.

> **Napomena [Z]:** ispravan postupak **već postoji u kodu**, u drugom modulu —
> može se preuzeti bez izmišljanja novog pravila.

---

#### P-24 — Izveštaj lizinga koristi poslednju dodelu vozila

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `fleet/support/lease_queries.py:8-10` |

**Šta je zatečeno [P]:** centar i organizaciona jedinica uzimaju se iz **poslednje**
dodele vozila, bez datumskog ograničenja.

**Nedoslednost [P]:** ostala dva mesečna izveštaja u istom modulu koriste **istorijsku**
dodelu:

| Izveštaj | Dodela |
|---|---|
| V-17 Mesečni troškovi polisa | Istorijska, na datum izdavanja polise |
| V-20 Mesečni troškovi servisa | Istorijska, na datum servisa |
| **V-19 Mesečni troškovi lizinga** | **Poslednja** |

**Posledica [Z]:** zbirovi po centrima iz tri izveštaja istog modula ne mogu se
međusobno sabrati niti uporediti.

**Predlog rešenja [Z]:** uskladiti sa V-17 i V-20 — koristiti dodelu važeću na datum
koji izveštaj prikazuje.

---

#### P-25 — Prateći troškovi lizinga obuhvataju sva vozila jedinice

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `fleet/support/lease_queries.py:49-75` |

**Šta je zatečeno [P]:** kolone „prateći troškovi“ i „prateći troškovi po vozilu“
računaju se iz servisa i goriva **svih vozila čija je poslednja dodela ta organizaciona
jedinica** — a ne vozila obuhvaćenih lizing ugovorima iz tog reda.

**Posledica [Z]:** u redu koji prikazuje jedan lizing ugovor stoje troškovi desetak
vozila koja sa tim ugovorom nemaju veze. Korisnik prirodno zaključuje da su to troškovi
lizing vozila.

**Predlog rešenja [Z]:** ili ograničiti prateće troškove na vozila iz ugovora u tom redu,
ili preimenovati kolone tako da jasno kažu da se odnose na celu organizacionu jedinicu.

**Dodatno [P]:** za svaku grupu izvršavaju se tri odvojena upita u petlji — spisak vozila,
zbir servisa i zbir goriva. Kod većeg broja grupa ekran postaje spor.

---

#### P-26 — Izveštaj goriva za upravu nema zaštitu pri čitanju

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `fleet/support/management_reports.py:102-106` |
| **Obračun** | [V-22.2](#v-222--gorivo-ims-nis-i-omv) |

**Šta je zatečeno [P]:** izveštaj „Gorivo IMS — NIS i OMV“ čita `TransactionOMV`
**direktno**, bez `filter_omv_fuel_queryset()`:

```python
qs = model.objects.filter(**{date_field+'__gte': start, date_field+'__lt': end})
```

Svi ostali ekrani goriva (V-01, V-02, V-21, V-23, „Fakture goriva“, detalj vozila)
prolaze kroz prečišćavanje iz [V-06](#v-06--prečišćavanje-omv-transakcija).

**Zašto u praksi obično ne smeta [P]:** `cleanup_omv_fuel_data(apply=True)` pokreće se
**automatski pri svakom uvozu OMV podataka** (`fleet/sync/selenium.py:212`), pa se
duplikati i „odjeci“ računa **fizički brišu iz baze**.

**Kada smeta [Z]:**

1. Ako uvoz prekine grešku pre koraka čišćenja.
2. Ako se podaci unesu zaobilazeći redovni uvoz.
3. Ako se `import_omv_csv_data` pozove sa `cleanup=False`.

U tim slučajevima **izveštaj za upravu prikazuje uvećane iznose**, dok ostali ekrani
goriva ostaju tačni — što je najgori mogući oblik greške, jer se ne primeti poređenjem
sa drugim ekranima.

**Predlog rešenja [Z]:** primeniti `filter_omv_fuel_queryset()` i u ovom izveštaju.

**Šta je urađeno (18.09.2026.) [P]:** prečišćavanje je primenjeno, ali **ne celo**.
`filter_omv_fuel_queryset()` radi **dve odvojene stvari**:

1. izbacuje duplikate (zastareli datumi fakture, ponovljeni redovi, odjeci računa);
2. **ograničava skup samo na goriva** (`FUEL_PRODUCT_KEYWORDS`).

Izveštaj za upravu ima **sopstvenu podelu proizvoda** (`fuel_type`: gorivo, AdBlue,
ostalo, sve). Da je primenjen ceo filter, opcije „AdBlue“, „ostalo“ i „sve“ **prestale bi
da prikazuju bilo šta**. Zato je prvi deo izdvojen u novu funkciju:

```python
def deduplicate_omv_transactions(queryset):
    return _exclude_omv_receipt_echoes(
        _dedupe_omv_transaction_lines(_exclude_omv_stale_invoice_dates(queryset))
    )


def filter_omv_fuel_queryset(queryset):
    return deduplicate_omv_transactions(queryset.filter(_fuel_product_filter("product_inv")))
```

Izveštaj za upravu poziva `deduplicate_omv_transactions()` samo za OMV
(`fleet/support/management_reports.py`). Ponašanje `filter_omv_fuel_queryset()`
i svih ekrana koji ga koriste **ostalo je nepromenjeno** — redosled koraka je isti.

> **Ispravka ranije tvrdnje:** gore je pisalo da „dvostruka zaštita ne smeta, jer filter
> nad već očišćenim podacima ništa ne uklanja“. **To nije tačno** i utvrđeno je tek pri
> ispravci — videti [P-46](#p-46--ključ-za-duplikate-ne-podnosi-prazna-polja) i
> [P-47](#p-47--ključ-za-duplikate-ne-obuhvata-iznos-ni-valutu).

---

#### P-46 — Ključ za duplikate ne podnosi prazna polja

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `fleet/support/fuel.py` — `_dedupe_omv_transaction_lines()` |
| **Obračun** | [V-06](#v-06--prečišćavanje-omv-transakcija) |

**Kako je otkriveno [P]:** pri ispravci [P-26](#p-26--izveštaj-goriva-za-upravu-nema-zaštitu-pri-čitanju)
tri postojeća testa izveštaja za upravu prestala su da vraćaju bilo koji red.

**Šta je zatečeno [P]:** prečišćavanje bira „pravi“ red transakcije tako što traži
podudaranje po pet polja:

```python
license_plate_no=OuterRef("license_plate_no"),
transaction_date=OuterRef("transaction_date"),
product_inv=OuterRef("product_inv"),
voucher=OuterRef("voucher"),
quantity=OuterRef("quantity"),
```

Tri od tih pet polja **smeju da budu prazna** u bazi (`product_inv`, `voucher`,
`quantity`). U SQL-u poređenje `NULL = NULL` **nije tačno**, pa red sa praznim vaučerom
**ne pronalazi ni samog sebe**. Posledica: `filter(id=Subquery(...))` ga izostavlja.

**Posledica [P]:** svaka OMV transakcija **bez broja vaučera ili bez količine tiho
nestaje** sa svih ekrana goriva koji koriste `filter_omv_fuel_queryset()` — pregled
goriva, fakture goriva, detalj vozila, trošak po kilometru. Ne prikazuje se nikakvo
upozorenje; iznos jednostavno nije u zbiru.

> Ovo **nije** bilo unedeno ispravkom P-26 — postojalo je i ranije, a ispravka ga je
> samo učinila vidljivim.

**Šta je urađeno (18.09.2026.) [P]:** podudaranje je učinjeno otpornim na prazna polja.
Prazna tekstualna polja izjednačavaju se sa `""`, prazna količina sa dogovorenom
zamenom, i to **samo unutar podupita** — spoljni upit se ne dira, da se ne pokvari
nijedno postojeće grupisanje:

```python
.filter(
    license_plate_no=OuterRef("license_plate_no"),
    transaction_date=OuterRef("transaction_date"),
    _key_product=Coalesce(OuterRef("product_inv"), DEDUPE_NO_TEXT),
    _key_voucher=Coalesce(OuterRef("voucher"), DEDUPE_NO_TEXT),
    _key_quantity=Coalesce(OuterRef("quantity"), DEDUPE_NO_QUANTITY, ...),
)
```

> **Posledica za korisnika [Z]:** na ekranima goriva mogu se pojaviti transakcije kojih
> ranije nije bilo, pa **iznosi mogu porasti**. Koliko — zavisi od toga koliko zapisa u
> bazi nema vaučer ili količinu, što treba **prebrojati na stvarnim podacima**.

---

#### P-47 — Ključ za duplikate ne obuhvata iznos ni valutu

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Zatvoreno kao „prihvaćeno“** (21.09.2026.) |
| **Gde** | `fleet/support/fuel.py` — `_dedupe_omv_transaction_lines()` |
| **Obračun** | [V-06](#v-06--prečišćavanje-omv-transakcija) |

**Šta je zatečeno [P]:** dva reda se smatraju **istom transakcijom** ako im se poklope
tablica, vreme, proizvod, vaučer i količina. **Iznos (`gross_cc`, `amount`) i valuta
(`supplier_currency`) ne ulaze u to poređenje.** Koji red preživljava bira se po
`-invoiced`, `-invoice_date`, `-id` — dakle **po stanju fakturisanja, nikada po iznosu**.

**Posledica [Z]:** ako se dva zapisa razlikuju **samo** po iznosu ili valuti, jedan će
biti odbačen, a koji — zavisi od redosleda upisa. Prikazani iznos tada nije zbir već
izbor.

**Zašto je status „za proveru“ [Z]:** nije potvrđeno da takvi parovi **postoje u stvarnim
podacima**. Moguće je i da je ovo namerno, jer se isti račun preuzima u dve faze
(predračun bez iznosa, pa konačan račun). Bez uvida u podatke se ne može zaključiti.

**Šta proveriti pre bilo kakve izmene [Z]:** prebrojati u `TransactionOMV` grupe sa
istom tablicom, vremenom, proizvodom, vaučerom i količinom, a **različitim** `gross_cc`
ili `supplier_currency`. Ako takvih grupa nema — ponašanje je bezopasno i ovo se zatvara
kao „prihvaćeno“. Ako ih ima, treba odlučiti da li su to duplikati ili zasebne stavke.

**Provera nad produkcionom bazom (21.09.2026.) [P]:** brojanje je izvršeno. U
`TransactionOMV` **nema nijedne grupe** (tablica + vreme + proizvod + vaučer + količina)
koja sadrži više od jednog reda — dakle ni jedne koja bi se razlikovala po iznosu ili
valuti. Ključ za duplikate **u stvarnim podacima ništa ne spaja**.

**Zaključak [P]:** opisano ponašanje je moguće po kodu, ali se **ne dešava**. Problem se
zatvara kao prihvaćen, bez izmene koda. Ako se način preuzimanja OMV podataka promeni,
ovo brojanje treba ponoviti — zato opis ostaje u registru.

---

#### P-27 — Formule 11 izveštaja nisu u projektu

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Većim delom rešeno** (21.09.2026.) |
| **Gde** | `fleet/support/report_queries.py` |
| **Obračun** | [6.5.5](#655-izveštaji-nad-nasleđenim-pogledima) |

**Šta je zatečeno [P]:** jedanaest izveštaja Flote se **ne računaju u aplikaciji** —
cela formula je u pogledu u bazi (`dbo.fleet_tro_svi`, `fleet_tro_goriva_m`,
`fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`, `tro_zarade`,
`fleet_dobavljaci`, `fleet_magacin_rez`, `fleet_otpis`, `kasko_rate`).
Aplikacija izvršava `SELECT` i prikazuje rezultat.

**Posledice [Z]:**

1. Na pitanje **„odakle ovaj iznos“** ne može se odgovoriti iz koda.
2. Promena pogleda u bazi menja rezultat na ekranu **bez ijedne izmene u aplikaciji**
   i **bez traga u istoriji verzija**.
3. Izveštaji za upravu zavise od objekata koje niko ne održava zajedno sa aplikacijom.

**Predlog rešenja [Z]:**

1. Preuzeti definicije (DDL) svih 11 pogleda — **već zatraženo**.
2. Smestiti ih u `dokumentacija/sql/` da budu pod kontrolom verzija.
3. Dokumentovati formulu svakog izveštaja u poglavlju 6.5.5.
4. Odrediti vlasnika koji odobrava izmene tih pogleda.


**Delimično razrešeno (18.09.2026.) [P]:** pri čišćenju repozitorijuma nađene su tri
datoteke sa **stvarnim definicijama pogleda** i premeštene u
[`dokumentacija/ddl-nasledjenih-pogleda/`](#prilog-b--ddl-nasleđenih-sql-pogleda):

| Datoteka | Sadrži |
|---|---|
| `naplata-pogledi.sql` | Sedam pogleda Naplate: `baza`, `v_if`, `v_duplikati`, `ispravke`, `tuzeni`, `dodela bucketa`, šifarnik partnera |
| `fleet_trebovanja.sql` | `CREATE view [dbo].[fleet_trebovanja]`, uključujući zakomentarisanu prethodnu verziju |
| `nbv_roba.sql` | `CREATE view [dbo].[nbv_roba]` |

Dve od njih (`fleet_trebovanja.sql`, `nbv_roba.sql`) **nisu bile u kontroli verzija**.

**Preuzeto iz produkcione baze (21.09.2026.) [P]:** po povezivanju na produkciju
definicije su pročitane iz `sys.sql_modules` i snimljene u isti direktorijum:

| Datoteka | Pogled |
|---|---|
| `fleet_tro_svi.sql` | `dbo.fleet_tro_svi` |
| `fleet_tro_goriva_m.sql` | `dbo.fleet_tro_goriva_m` |
| `fleet_tro_pracenje.sql` | `dbo.fleet_tro_pracenje` |
| `fleet_tro_taho.sql` | `dbo.fleet_tro_taho` |
| `fleet_tro_parking.sql` | `dbo.fleet_tro_parking` |
| `fleet_dobavljaci.sql` | `dbo.fleet_dobavljaci` |
| `fleet_magacin_rez.sql` | `dbo.fleet_magacin_rez` |
| `fleet_otpis.sql` | `dbo.fleet_otpis` |
| `v_neodobreneIF.sql` | `dbo.v_neodobreneIF` |

**Šta preostaje [P]:** `tro_zarade` i `kasko_rate` **ne postoje u bazi** — provera nad
`sys.objects` ne vraća nijedan red ni pod jednom šemom. Treba utvrditi da li su
obrisani, preimenovani ili se izveštaj koji ih pominje više ne koristi. Dok se to ne
utvrdi, ta dva izveštaja se ne mogu dokumentovati **niti se zna da li uopšte rade**.

**Šta i dalje stoji [Z]:** to što su definicije sada u projektu **ne znači da su pod
kontrolom** — one i dalje žive u bazi i izmena u bazi i dalje menja rezultat na ekranu
bez traga u istoriji verzija. Tačke 3 i 4 predloga (dokumentovati formulu svakog
izveštaja; odrediti vlasnika koji odobrava izmene) **nisu urađene**.

**Šta je time odgovoreno [P]:** formula za `vrednost_nab` (`kol * cena`), granica
„304“ u pogledima Naplate, razredi starosti duga i razlika između stare i nove verzije
pogleda `fleet_trebovanja` (godina 2024 → 2026, vrste artikala `REZ`/`GOR` → sve).

**Šta i dalje nedostaje [P]:** DDL za **11 izveštaja Flote** — `fleet_tro_svi`,
`fleet_tro_goriva_m`, `fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`,
`tro_zarade`, `fleet_dobavljaci`, `fleet_magacin_rez`, `fleet_otpis`, `kasko_rate`.
Za njih se na pitanje „odakle ovaj iznos“ i dalje **ne može odgovoriti iz projekta**.

---

#### P-50 — Pregled novog modula ekonomike flote

| | |
|---|---|
| **Ozbiljnost** | **Visoka** (dve stavke), ostalo srednje i nisko |
| **Status** | **Rešeno** (19.09.2026.) |
| **Gde** | `fleet/services/economics.py`, `fleet/views/analytics.py`, `fleet/forms/`, `core/permissions.py` |
| **Obračun** | [E-01](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa) |

**Povod [P]:** modul ekonomike flote (metodologija **IMS-FLOTA-2.0**) donosi 1.394 reda novog
koda i menja obračun na tri ekrana. Pregledan je pre isporuke. Kod **nije bio u produkciji**,
pa nijedan od nalaza nije dao pogrešan poslovni broj korisniku.

**Pet nalaza koji bi se videli odmah po isporuci [P]:**

| # | Nalaz | Posledica |
|---|---|---|
| 1 | `visible_vehicles` filtrira `access_center__in`, a `NULL IN (...)` nije tačno | Vozilo **bez ijedne dodele** nestaje sa spiska i daje **404** na detalju, svakom korisniku sa ograničenim centrima. Ranija provera je prazan centar **izričito propuštala**. |
| 2 | `_active` uzima `closed_at` uključivo, a pri predaji se postavlja na `created_at` sledećeg naloga | **Svaki uredan dan primopredaje** broji se kao preklapanje: lažno upozorenje, vozilo ide u „Potrebna provera“, a kod različitih šifara posla trošak tog dana ostaje **neraspoređen**. |
| 3 | Suženje izbora šifre posla po centru **ne vraća postojeću vrednost** naloga | Korisnik iz centra 01 otvori nalog sa šifrom centra 02 → pri snimanju se **veza sa poslom tiho briše**. Ekran za potvrdu šifre posla pritom javlja „Evidencija za analitiku je sačuvana.“ |
| 4 | Dozvole se dodeljuju pod nazivom rute, a pogledi traže `vehicle_update` / `vehicle_detail` | Dodele su **mrtve**; ko dobije kod nazvan po ruti i dalje dobija zabranu. Krši pravilo iz `AGENTS.md` da je kod dozvole naziv rute. |
| 5 | `fleet_analytics` i `center_statistics` dobili zabranu bez dodele prava | Ekrani koji su ranije bili otvoreni (analitika svakom prijavljenom, statistika po pripadnosti centru) **ostaju zaključani** svima osim superusera i uloge Uprava. |

**Devet sitnijih [P]:** `?order=abc` daje **500** umesto 404; `unallocated` se sabira u petlji
pa se prepiše — mrtav račun; `visible_vehicles(as_of=…)` prima parametar koji nikad ne čita;
kod ranije evidencije goriva nedostaju `cost_neto` i `price_per_liter`, pa su dve kolone
prazne; **cela tabela metodologije se upisuje u svaki snimak procene**; `Policy` se učitava
bez donje granice perioda; `dashboard_center.html` ostao kao mrtav jednoredni fajl; mrtav
uvoz u `vehicles.py`.

**Šta je urađeno (19.09.2026.) [P]:** svih 14 ispravljeno, uz **14 novih testova**.

| Ispravka | Način |
|---|---|
| 1 | `Q(access_center__in=centers) | Q(access_center__isnull=True)`; test potvrđuje i da tuđi centar **ostaje** skriven |
| 2 | Nova `_active_orders()` — **dan primopredaje pripada nalogu koji tog dana počinje**. Stvarno preklapanje se i dalje prijavljuje; jednodnevni nalog i nalog bez naslednika zadržavaju svoj dan |
| 3 | Postojeća šifra se vraća u izbor (`limited | queryset.filter(pk=current_id)`), kao što polje `employee` već radi |
| 4 | Pogledi traže kodove po nazivu rute. **Propagacija u `sync_permission_codes` je time dobila smisao** — postojala je, ali je nikad ništa nije čitalo |
| 5 | Oba koda dodata u propagaciju iz `vehicle_detail`; test `test_new_fleet_routes_inherit_permissions` to proverava |

> **[P] Pri isporuci obavezno pokrenuti `sync_permission_codes`** — bez toga nove dozvole
> ne postoje i ekrani ostaju zaključani.

> **[Z] Ocena modula:** metodologija je disciplinovana — dosledno razdvaja potvrđeno od
> nepotvrđenog, odbija da nepoznato prikaže kao nulu, a `period_analysis()` koriste i flota
> i detalj vozila, pa isti period daje isti broj na oba ekrana. Nalazi su bili **greške
> izvedbe, ne greške zamisli**.


#### P-51 — Tri šifre dozvole ne postoje na produkciji

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Za rešavanje** — traži izmenu na produkcionoj bazi |
| **Gde** | `core/permissions.py`, tabela dozvola u bazi |
| **Obračun** | [E-01](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa) |

**Šta je zatečeno [P]:** provera nad produkcionom bazom (21.09.2026.) pokazuje da tri
šifre dozvole **uopšte ne postoje**, pa nemaju nijednu dodelu ulozi:

| Šifra | Ekran | Dodela ulogama |
|---|---|---|
| `vehicle_analysis_settings` | „Namena, kriterijumi i evidencija“ — **ekran na kom se unose podaci ekonomike** | **0** |
| `vehicle_assessment_create` | „Uporedi buduće opcije“ | **0** |
| `vehicle_assessment_detail` | Prikaz sačuvane procene | **0** |

Za poređenje, šifre koje **postoje**: `fleet_analytics` (2 uloge), `center_statistics`
(3 uloge). [P]

**Posledica [P]:** dozvola se u ovom sistemu izvodi iz **imena rute**; ako šifra ne postoji,
nijedna uloga je nema. Ta tri ekrana su zato dostupna **samo superkorisniku**. Dugmad
„Evidencija za analitiku“ i „Unesi naknadu“ na kartici *Troškovi* ostalim korisnicima se
**ne prikazuju** (`can_edit_analysis` je netačno).

**Zašto je ovo prvo po redu [Z]:** ekran koji nedostaje je upravo onaj kojim se rešava
[P-52](#p-52--ulazni-podaci-ekonomike-su-prazni-na-produkciji). Dok se šifre ne kreiraju,
podatke ekonomike **ne može uneti niko osim superkorisnika**.

**Rešenje [P]:** pokrenuti `sync_permission_codes` nad produkcijom — komanda izvodi šifre
iz imena ruta i propagira dodele. **To je upis u produkcionu bazu i traži odobrenje.**
Posle toga treba **dodeliti** te tri šifre ulogama koje smeju da unose podatke — koje su
to uloge, **nije potvrđeno** [N] i o tome odlučuje naručilac.

---

#### P-52 — Ulazni podaci ekonomike su prazni na produkciji

> **Ažuriranje 21.09.2026 — metodologija 2.1:** korisnik je odobrio da trošak
> prati istoriju šifre posla vozila, da bez važećeg lizinga/najma važi vlasništvo
> IMS i da namena može biti jasno označena početna procena. Posebna naknada,
> posao naloga i zastoji više nisu obavezni ulazi. Migracija 0078 primenjena je
> na IMS_ERP: 12 dugoročnih najmova označeno je mesečnim, 4 operativna lizinga
> ukupnim iznosom, bez promene iznosa i datuma. Sedam finansijskih lizinga
> i dalje zahteva zasebnu kamatu. Opis ispod je istorijski nalaz za 2.0;
> prazne tabele profila/raspolaganja/zastoja same po sebi više ne blokiraju
> analitiku. Važeća pravila i kontrolni primeri su u [E-01](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa).

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Za rešavanje** — unos podataka, ne izmena koda |
| **Gde** | Produkciona baza — tabele modula ekonomike |
| **Obračun** | [E-01](#612-flota--analitika-namene-raspolaganja-i-ekonomskih-alternativa) |

**Šta je zatečeno [P]:** migracija
`0077_vehicletravelorder_job_code_leasechargeperiod_and_more` **jeste primenjena** na
produkciji — tabele postoje. Ali su **prazne**:

| Podatak | Zapisa |
|---|---|
| `LeaseChargePeriod` — potvrđene naknade lizinga/najma | **0** |
| `LeaseInterest` — kamata finansijskog lizinga | **0** |
| `VehicleAnalysisProfile` — namena i kontrolni pragovi | **0** |
| `VehicleDowntime` — evidentirani zastoji | **0** |
| `VehicleEconomicAssessment` — sačuvane procene | **0** |

Uz to [P]:

| Podatak | Stanje |
|---|---|
| Nalozi sa upisanom šifrom posla | **0 od 241** |
| Vozila bez ijednog osnova raspolaganja (`VehicleHolding`) | **149 od 172** |

Postojeći podaci nisu problem — ima 172 vozila, 23 ugovora lizinga, 647 polisa,
1.342 servisa, 2.980 trebovanja, 16.118 zapisa o gorivu. [P]

**Posledica [P]:** kartica *Troškovi* radi, ali za skoro svako vozilo prikazuje
„nedostaje“:

- red **„Potvrđene naknade lizinga / najma“** je prazan za **sva 23 vozila na lizingu** —
  nijedan ugovor nema potvrđenu naknadu, pa po pravilu modula ne ulazi u obračun;
- red **„Kamata finansijskog lizinga“** je prazan svuda;
- **raspodela na šifre posla** ne daje ništa — ceo iznos pada u „neraspoređeno“;
- **kriterijumi** se ne prikazuju jer nema unetog praga ni namene;
- kod 149 vozila **ne zna se osnov raspolaganja**, pa se ugovorne naknade ne mogu
  rasporediti ni kada se unesu.

> **Ovo nije greška u obračunu.** Modul namerno ne procenjuje ono što nije uneto — prazno
> polje nije potvrđena nula. Prikaz je tačan: podataka nema.

**Rešenje [Z]:** unos podataka, redosledom koji nalaže sam ekran
(`_vehicle_cost_readiness.html`) — prvo osnov raspolaganja, pa naknada sa periodom i
značenjem iznosa, pa kamata, pa namena i pragovi. Preduslov je
[P-51](#p-51--tri-šifre-dozvole-ne-postoje-na-produkciji).

**Otvoreno pitanje za naručioca [N]:** ko unosi ove podatke i po kom dokumentu se
potvrđuje iznos naknade. Bez odgovora na to, unos se **ne sme** raditi pogađanjem — staro
polje „Trenutna rata / iznos otplate“ se upravo zato ne koristi u obračunu
([P-08](#p-08--operativni-lizing-se-deli-drugačije-od-dugoročnog-najma)).

---

### 10.4.1. Obračuni — Kadrovi

#### P-28 — Dva različita obračuna dnevnih sati

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za proveru |
| **Gde** | `hr/services/attendance.py:313` i `:474` |
| **Obračuni** | [K-01](#k-01--dnevni-sati-rada-iz-evidencije-prolazaka), [K-02](#k-02--dnevni-sati-iz-obračunatih-parova-drugi-postupak) |

**Šta je zatečeno [P]:** iz **iste** evidencije prolazaka sistem računa sate na
**dva različita načina**, sa različitim pravilima:

| | K-01 `calculate_daily_hours_from_clock_events` | K-02 `get_daily_work_hours` |
|---|---|---|
| Izvor | `C_Prolasci_Radnika` — pojedinačni prolasci | `c_parovi_radnika_detalji` — gotovi parovi |
| Uparivanje | Sam upa­ruje po tasterima | Preuzima uparena trajanja |
| Službeni izlazak | **Računa do 16:00** | Uzima `Trajanje_Sluzbeno` iz izvora |
| Pauza | **Prijavljuje kao problem, ne računa** | **Računa, najviše 30 minuta** |
| Neispravno dug zapis | Nema provere | **Izuzima `Trajanje_1 >= 20`** |
| **Gde se prikazuje** | **Radna lista zaposlenog** | Samo `manage.py hr_attendance_summary` |

**Posledica [Z]:** za isti dan i istog zaposlenog dva postupka daju **različit broj sati**.
Zaposleni na radnoj listi vidi jedan broj, a komanda za pregled prisustva drugi. Nije
zabeleženo koji je merodavan.

**Dodatni nedostatak K-01 [P]:** prolasci se grupišu **po datumu prolaska**
(`attendance.py:337`), pa **smena preko ponoći ne može biti uparena** — ulaz u 22:00
ostaje „bez izlaza“, a izlaz u 06:00 „bez prethodnog ulaza“. Dan dobija dva problema,
a **sati se ne računaju uopšte**.

**Predlog rešenja [Z]:**

1. Odrediti koji je postupak merodavan i drugi ukloniti ili jasno označiti kao pomoćni.
2. Ako ostaje K-01, dodati uparivanje preko ponoći (otvoren ulaz prenosi se u sledeći dan).
3. Uskladiti postupanje sa pauzom — vidi pitanje **Q25**.

> **Pre izmene potrebna potvrda [N]:** moguće je da je K-02 ostatak ranije faze, a K-01
> trenutno rešenje. Treba proveriti da li se komanda `hr_attendance_summary` uopšte koristi.

---

#### P-29 — Otvoreno bolovanje nestaje sa radne liste

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `hr/services/sick_leave.py:194` |
| **Obračun** | [K-07](#k-07--bolovanja--uvoz-rfzo-i-povezivanje) |

**Šta je zatečeno [P]:** za bolovanje bez datuma zaključenja (status „Aktivno“) kao
kraj se uzima **datum RFZO izvoza**:

```python
end = min(last, leave.end_date or leave.source_date)
```

**Posledica [Z]:** bolovanje koje i dalje traje prikazuje se na radnoj listi **samo do
dana poslednjeg uvoza**. Ako se RFZO datoteka ne uveze mesec dana, poslednjih mesec dana
bolovanja **nestaje sa radne liste**, iako zaposleni i dalje odsustvuje.

**Predlog rešenja [Z]:** za otvoreno bolovanje prikazivati odsustvo **do kraja meseca
koji se gleda** (ili do današnjeg dana), uz jasnu oznaku *„otvoreno — poslednji izvoz
od <datum>“*, umesto tihog prekidanja.

---

### 10.4.2. Obračuni — Mobilna telefonija

#### P-30 — Izuzeće od parkinga nema period važenja

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `mobilni/withholdings.py:50-51`, `mobilni/models.py:272-287` |
| **Obračun** | [M-02](#m-02--izuzeci-od-parkinga) |

**Šta je zatečeno [P]:** tabela izuzetaka ima **samo broj telefona**, bez perioda:

```python
def parking_exempt_phone_numbers(year=None, month=None):
    return {normalize_phone_number(item.phone_number) for item in MobileParkingExemption.objects.all()}
```

Funkcija **prima godinu i mesec, ali ih ne koristi**.

**Posledica [Z]:** izuzetak upisan danas menja i **već obračunate prošle mesece**.
Ako je obustava za avgust već prosleđena u zarade, a u septembru se doda izuzetak,
avgustovski ekran će prikazati **drugi iznos** nego što je prosleđen — bez traga o
tome šta je bilo.

**Predlog rešenja [Z]:** dodati polja „važi od“ i „važi do“ na izuzetak i filtrirati
po obračunskom mesecu. Postojeći izuzeci bi dobili „važi od“ sa datumom upisa.

---

#### P-31 — Obustava se nigde ne čuva

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za rešavanje |
| **Gde** | `mobilni/withholdings.py`, `mobilni/views/mobile.py:903` |
| **Obračun** | [M-01](#m-01--obustava-po-zaposlenom) |

**Šta je zatečeno [P]:** obustava se **računa pri svakom otvaranju ekrana ili izvoza**
i **nigde se ne čuva**. Ne postoji model koji beleži obračunatu obustavu.

**Posledica [Z]:** ne postoji odgovor na pitanje **„koji je iznos stvarno prosleđen u
zarade za avgust“**. Svaka naknadna izmena paketa, dodele ili izuzetka menja i prikaz
za prošle mesece. Rezultat koji ulazi u zaradu zaposlenog nema ni istoriju ni revizorski trag.

**Tri prateća nedostatka [P]:**

1. **Potrošnja bez dodele tiho ispada.** U obračun ulaze samo stavke potrošnje koje imaju
   dodelu sa **istim** periodom i brojem. Ako dodele za taj mesec nisu uvezene, cela
   potrošnja **nestaje iz obračuna**, bez upozorenja i bez brojača.
2. **Negativna obustava se izvozi.** Kada je neto iznos paketa veći od potrošnje,
   obustava je negativna i takva ulazi u CSV za zarade — vidi pitanje **Q29**.
3. **Obustava jednaka nuli se ne izvozi**, dok se negativna izvozi. Pravilo nije dosledno.

**Predlog rešenja [Z]:**

1. Uvesti tabelu obračunatih obustava po mesecu, sa trenutkom obračuna i korisnikom,
   koja se **zaključava** pri izvozu u zarade.
2. Prikazati broj stavki potrošnje **bez odgovarajuće dodele** kao upozorenje na ekranu.
3. Odlučiti šta sa negativnom obustavom (**Q29**).

---

#### P-32 — Rupe u razvrstavanju bivših zaposlenih

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `mobilni/withholdings.py:238-249` |
| **Obračun** | [M-03](#m-03--razvrstavanje-zaposleni--bivši--nezaposleni) |

**Tri odvojena nedostatka [P]:**

**A) Zaposleni koji je otišao u toku obračunskog meseca nije nigde.**
Uslov za „bivšeg“ je `datum odlaska < prvi dan meseca`. Neaktivan zaposleni sa datumom
odlaska 20.08. **nije** u izveštaju „Zaposleni“ (nije aktivan) ni u „Bivši“
(odlazak nije pre 01.08.). Pojavljuje se samo u zbirnom izveštaju „Sve“ — i **ne ulazi
u izvoz za zarade**, iako je deo meseca radio.

**B) Neaktivan bez datuma odlaska uvek je „bivši“.**
Ako datum odlaska nije unet, sistem pretpostavlja da je zaposleni otišao. Zaposleni koji
je privremeno označen kao neaktivan zbog greške u podacima završava među bivšima.

**C) Kod više korisnika mobilnog uzima se poslednji po ID-u.**
Ako zaposleni ima više zapisa u evidenciji korisnika, uzima se onaj sa najvećim ID-em
(`order_by("-id").first()`), a ne onaj sa odgovarajućim datumom.

**Predlog rešenja [Z]:** uvesti pravilo „zaposlen bar jedan dan u obračunskom mesecu“
umesto poređenja sa prvim danom, i tražiti izričitu potvrdu kada datum odlaska nedostaje.

---

#### P-34 — Poseban broj telefona upisan u kod umesto u bazi

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Potvrđena greška** — naručilac, 18.09.2026. |
| **Gde** | `mobilni/withholdings.py:16, 94, 161-162` |
| **Obračun** | [M-01](#m-01--obustava-po-zaposlenom) |

**Šta je zatečeno [P]:**

```python
SPECIAL_PHONE_NUMBER = "381637781481"
```

Za taj broj se u obračunu obustave **ne odbija neto iznos paketa**, pa se zaposlenom
obustavlja **ceo iznos**:

> obično: `osnovica PDV − neto paketa + parking + NZRD`
> za taj broj: `osnovica PDV + parking + NZRD`

Pravilo postoji na **dva mesta** — u Python funkciji `calculate_withholding()` i u SQL
izrazu `withholding_amount_expression()`. Oba moraju ostati usklađena.

**Odluka naručioca [P]:** ovo je **greška**. Poslovni izuzetak ne sme biti u kodu —
**mora se čuvati u bazi**.

**Posledice postojećeg stanja [Z]:**

1. Dodavanje ili uklanjanje takvog broja zahteva **izmenu koda i isporuku nove verzije**.
2. Administracija ne može sama da održava spisak.
3. Nema **istorije** — ne zna se od kada pravilo važi za taj broj.
4. Nema **obrazloženja** — ni u kodu ni u bazi ne piše zašto je taj broj izuzet.
5. Ako se broj prenese drugom zaposlenom, pravilo **ostaje uz broj**, ne uz lice.

**Predlog rešenja [Z]:**

| Korak | Opis |
|---|---|
| 1 | Dodati oznaku u evidenciju — na **dodelu broja** (`MobileAssignment`) ili na zaseban šifarnik izuzetaka, po ugledu na postojeći `MobileParkingExemption` |
| 2 | Predvideti **period važenja** i **obrazloženje**, da se izbegne isti nedostatak kao kod izuzetka za parking (**P-30**) |
| 3 | Preneti postojeći broj u bazu i **ukloniti konstantu iz koda**, na **oba** mesta (Python i SQL izraz) |
| 4 | Dopuniti testove — postojeći testovi se oslanjaju na konstantu |

> **Napomena [Z]:** rešenje je slično već postojećem obrascu `MobileParkingExemption`,
> pa se može preuzeti njegova struktura — ali sa periodom važenja, koji tamo nedostaje.

---

### 10.4.3. Obračuni — Isplate

#### P-33 — Virman skraćuje podatke i ne čuva poslatu datoteku

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za rešavanje |
| **Gde** | `isplate/services/virman.py:56-60, 195-213` |
| **Obračun** | [I-01](#i-01--generisanje-datoteke-virmana) |

**A) Tiho skraćivanje [P]**

Funkcija upisa u red seče svaku vrednost na širinu polja, **bez ijedne provere**:

```python
def _write(record, start, width, value, align="left"):
    text = text[:width]
```

| Polje | Širina | Šta se dešava |
|---|---|---|
| Naziv primaoca | 35 | Duže ime se odseca |
| **Mesto primaoca** | **10** | „Novi Beograd“ (12) postaje **„Novi Beogr“** |
| Naziv platioca | 35 | Odseca se |

Posledica [Z]: banka dobija **nepotpun naziv mesta**, a korisnik ne zna da se to desilo.
Za naziv primaoca to može značiti i **neprepoznavanje primaoca**.

**B) Bez opštine boravka koristi se „Beograd“ [P]**

Ako zaposleni nema unetu opštinu boravka, upisuje se `Beograd` — **bez upozorenja**,
i za zaposlene koji tamo ne žive.

**C) Sadržaj poslate datoteke se ne čuva [P]**

Na nalogu se beleži **samo da je virman rađen**, kada i ko. Sama datoteka se **ne čuva**.

Posledica [Z]: ako se posle generisanja promeni iznos akontacije ili račun zaposlenog,
**ne postoji način** da se utvrdi šta je poslato banci. Kod neslaganja sa izvodom nema
dokaza o poslatom nalogu.

**Predlog rešenja [Z]:**

1. Pri skraćivanju prijaviti grešku ili upozorenje umesto tihog sečenja — naročito za
   naziv primaoca i mesto.
2. Tražiti izričitu potvrdu kada opština boravka nedostaje, umesto podrazumevanog Beograda.
3. Uvesti tabelu generisanih virmana koja čuva **sadržaj datoteke ili njen otisak**,
   spisak obuhvaćenih naloga, ukupan iznos, datum i korisnika.

---

### 10.4.4. Obračuni — Potraživanja

#### P-35 — Nepoznato dospeće prikazuje se kao „Nedospelo“

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `potrazivanja/services/sync.py:76-78` |
| **Obračun** | [PT-01](#pt-01--starosni-razredi-baketi) |
| **Pitanje** | Q33 |

**Šta je zatečeno [P]:**

```python
def bucket(due, as_of):
    if due is None or due >= as_of:
        return "0.1"  # Deliberately preserves legacy unknown-date bucket.
```

Razred `0.1` („Nedospelo“) objedinjuje **dva različita poslovna slučaja**:

| Slučaj | Poslovno značenje |
|---|---|
| `due >= as_of` | Potraživanje **još nije dospelo** — uredno je |
| `due is None` | **Ne zna se** kada dospeva — može biti i nekoliko godina staro |

**Posledica [Z]:** dug star godinu dana kome nije unet datum dospeća prikazuje se u koloni
**„Nedospelo“**, zajedno sa urednim potraživanjima. Služba naplate ga ne vidi kao problem.

**Dokaz sa izvora [P]:** pogled `dodela_baketa` računa **dve** oznake koje se kod praznog
dospeća **ne slažu**:

```sql
CASE WHEN DATEDIFF(DAY, dpo, GETDATE()) <= 0 THEN 0 ELSE 1 END AS kategorija
```

Sa `dpo = NULL` poređenje je `UNKNOWN`, pa red pada u `ELSE` → **`kategorija = 1`
(dospelo)**, dok `baket` istovremeno ide u **`0.1` (nedospelo)**.

> **Ista stavka je „dospela“ po jednoj koloni i „nedospela“ po drugoj — već u izvoru.**

Django kod obe vrednosti **čuva i označava**:

```python
resolution_details = {"bucket": ..., "category": integer(row.get("kategorija")),
                      "unknown_due": due is None}
```

**Koliko ih ima [P]:** pri prenosu je zatečeno **9 otvorenih stavki bez dospeća**, ukupnog
salda **−310.678,54 RSD**. Zbirna kartica ih **prikazuje zasebno**, a u tabeli ostaju u
razredu `0.1` radi uporedivosti sa Naplatom.

**Olakšavajuće okolnosti [P]:**

1. Pravilo je **namerno preuzeto** iz nasleđene Naplate, da se snimci mogu porediti
   tokom prelaska — izričito zabeleženo u komentaru koda.
2. Sistem **broji** stavke bez dospeća (`unknown_due_count` u zbirnim pokazateljima snimka).
3. Svaka pozicija nosi oznaku `unknown_due` u `resolution_details`.
4. Beleži se i **način utvrđivanja dospeća** (`due_date_method`).

**Predlog rešenja [Z]:** posle završenog prelaska sa Naplate uvesti **osmi razred**
„Nepoznato dospeće“ i prikazati ga zasebnom kolonom. Podaci za to **već postoje**.

> **Pre izmene potrebna potvrda [N]:** dok Naplata i Potraživanja rade paralelno,
> promena pravila bi **onemogućila poređenje** dva sistema. Vidi **P-18**.


**Potvrda sa izvora (18.09.2026.) [P]:** DDL nasleđenog pogleda `dodela bucketa`
nađen je u projektu i premešten u
[`ddl-nasledjenih-pogleda/naplata-pogledi.sql`](#razredi-starosti-duga--dodela-bucketa).
On **potvrđuje da pravilo dolazi iz baze**, a ne iz Django koda:

```sql
CASE WHEN DATEDIFF(DAY, dpo, GETDATE()) BETWEEN 1 AND 30 THEN 30
     ...
     ELSE 0.1 END AS baket
```

`DATEDIFF` sa praznim `dpo` vraća `NULL`, nijedan `WHEN` nije tačan i stavka pada u
`ELSE 0.1`. Django kod je to **verno preslikao**.

**Šta to menja [Z]:** ispravka u Djangu razdvojila bi razrede **samo u Potraživanjima**,
dok bi nasleđeni pogled i dalje vraćao staro. Dok Naplata radi paralelno
([P-18](#p-18--naplata-i-potraživanja-rade-paralelno)), dva ekrana bi pokazivala različite
brojeve za isti dug. **Odluku donositi zajedno sa gašenjem Naplate.**

---

### 10.4.5. Obračuni — Nabavka

#### P-36 — Ukupan iznos faktura na izveštaju Nabavke je višestruko uvećan

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | **Rešeno** (18.09.2026.) |
| **Gde** | `nabavka/views/reports.py:57-60` |
| **Obračun** | [B-06](#b-06--izveštaji-i-alarmi-nabavke) |

**Šta je zatečeno [P]:**

```python
"invoice_total": ProcurementInvoice.objects
    .filter(item_links__isnull=False)
    .distinct()
    .aggregate(total=Sum("amount"))["total"]
```

Filter po `item_links` pravi **spoj sa tabelom veza stavki i faktura**. Faktura se u
rezultatu pojavljuje **onoliko puta koliko ima povezanih stavki**.

`distinct()` **ne pomaže**: Django ga primenjuje na spoljni `SELECT`
(`SELECT DISTINCT SUM(...)`), a ne na skup redova koji se sabiraju. Pošto agregat vraća
jedan red, `DISTINCT` nema nikakvo dejstvo.

**Posledica [P]:** faktura od 100.000 RSD povezana sa tri stavke ulazi u zbir kao
**300.000 RSD**.

| Faktura | Iznos | Veza stavki | Ulazi u zbir kao |
|---|---|---|---|
| F-100 | 100.000,00 | 3 | 300.000,00 |
| F-200 | 50.000,00 | 1 | 50.000,00 |
| F-300 | 20.000,00 | 2 | 40.000,00 |
| **Tačno** | **170.000,00** | | **Prikazano: 390.000,00** |

**Predlog rešenja [Z]:** sabirati nad skupom bez ponavljanja, na primer:

```python
ProcurementInvoice.objects.filter(
    pk__in=ProcurementItemInvoiceLink.objects.values("invoice_id")
).aggregate(total=Sum("amount"))["total"]
```

> **Napomena [Z]:** isti obrazac (`filter` po vezi ka više redova + `Sum`) treba proveriti
> i na drugim mestima. U pregledanim modulima drugih pojava nije nađeno.


**Šta je urađeno (18.09.2026.) [P]:** primenjeno je predloženo rešenje — zbir ide nad
skupom faktura bez ponavljanja (`nabavka/views/reports.py`):

```python
# Svaka faktura se broji jednom; spoj preko item_links ponovio bi iznos za svaku stavku.
"invoice_total": ProcurementInvoice.objects.filter(
    pk__in=ProcurementItemInvoiceLink.objects.values("invoice_id")
).aggregate(total=Sum("amount"))["total"],
```

> **Posledica za korisnika [Z]:** prikazani „ukupan iznos faktura“ na izveštaju Nabavke
> **biće manji nego ranije**. Raniji iznos je bio pogrešan.

---

#### P-37 — Brisanje UF faktura tiho kida veze

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `nabavka/services/source_snapshots.py:229-232`, `nabavka/models.py:229-236` |
| **Obračun** | [B-02](#b-02--grupisanje-uf-stavki-u-uf-fakture) |

**Šta je zatečeno [P]:** posle obnavljanja UF faktura se **briše sve što se nije pojavilo**
u tom prolazu:

```python
UfInvoiceSnapshot.objects.exclude(pk__in=invoice_ids).delete()
```

Veza `ProcurementItem.uf_invoice` je `on_delete=SET_NULL`, pa se pri brisanju
**tiho prazni** — stavka predmeta nabavke ostaje bez fakture.

**Posledica [Z]:** ako se u izvoru promeni broj fakture ili identifikator partnera, menja
se ključ grupisanja, stara faktura se briše i **veza koju je korisnik ručno uspostavio
nestaje** — bez poruke, bez zapisa u istoriji i bez mogućnosti da se sazna šta je bilo
povezano.

**Predlog rešenja [Z]:**

1. Umesto brisanja, označiti fakturu kao neaktivnu (kao što rade Finansije i Potraživanja).
2. Ako brisanje ostaje, **prebrojati i prijaviti** koliko je veza prekinuto.
3. Zabraniti brisanje fakture koja ima povezane stavke predmeta (`PROTECT`).

---

#### P-38 — Procenjena vrednost predmeta se ne poredi sa stavkama

| | |
|---|---|
| **Ozbiljnost** | Srednja |
| **Status** | Za proveru |
| **Gde** | `nabavka/models.py:110-116, 306-310` |
| **Obračun** | [B-01](#b-01--procenjena-vrednost-stavke-i-predmeta) |
| **Pitanje** | Q36 |

**Šta je zatečeno [P]:** predmet nabavke ima **ručno uneto** polje „Procenjena vrednost“,
a stavke imaju svoju procenjenu vrednost (cena × količina). Sistem ih **nigde ne poredi**.

**Posledica [Z]:** vrednost po kojoj se predmet odobrava može se razlikovati od zbira
onoga što je stvarno traženo, a da niko ne primeti.

**Predlog rešenja [Z]:** prikazati zbir stavki uz unetu vrednost i istaći razliku.
Ne menjati automatski uneti podatak — vrednost predmeta može legitimno biti veća
(rezerva, troškovi dostave).

---

#### P-39 — Ispravka u izvoru stvara dvojnika EUF fakture

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `nabavka/services/euf.py:49-57` |
| **Obračun** | [B-03](#b-03--ključ-euf-fakture) |
| **Pitanje** | Q35 |

**Šta je zatečeno [P]:** identitet EUF fakture je otisak četiri polja:

> `datum` (izvorni tekst) **|** `naziv partnera` **|** `broj fakture` **|** `iznos`

Nasleđeni pogled nema stabilan identifikator, pa je ovo jedino rešenje bez izmene izvora. [Z]

**Dve posledice [Z]:**

**A) Ispravka u izvoru pravi novu fakturu.** Ako se ispravi iznos, naziv partnera ili
oblik datuma, nastaje **nov ključ**, pa sistem upisuje **novu fakturu**. Stara ostaje,
sa svim vezama ka predmetima nabavke i šiframa posla. Na spisku se pojavljuju **dve**
fakture za isti dokument.

**B) Dve stvarno različite fakture mogu dobiti isti ključ**, ako imaju isti datum,
partnera, broj i iznos. Tada se **spajaju u jednu**.

**Predlog rešenja [Z]:** proveriti da li izvor ima neki stabilan identifikator koji bi
mogao ući u ključ (npr. interni ID dokumenta). Ako nema — prikazati upozorenje kada se
pojave dve fakture istog partnera i broja sa različitim ključem.

---

#### P-49 — Procedura osvežava tekuću godinu, a ispravke čitaju prethodnu

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | **Za proveru** |
| **Gde** | `sp_AzurirajNalogZ` (baza) + pogledi `ispravke`, `v_duplikati`, `tuzeni` |
| **Obračun** | [PT-03](#pt-03--objavljivanje-snimka-stanja) |

**Šta je zatečeno [P]:** posle **30. aprila** pogledi se razilaze po godini koju čitaju:

| Pogled | Posle 30.04. čita |
|---|---|
| `baza` | **Tekuću** godinu |
| `ispravke`, `v_duplikati`, `tuzeni` | **Prethodnu** godinu |

To je **potvrđeno poslovno pravilo**, ne greška — vidi
[Prilog B](#prilog-b--ddl-nasleđenih-sql-pogleda).

Istovremeno, procedura `sp_AzurirajNalogZ`, koja puni lokalni `nalog_z`, posle 30. aprila
osvežava **samo tekuću godinu**.

**Posledica [Z]:** posle aprila `ispravke` čitaju godinu koju procedura **više ne
osvežava**. Lokalna kopija prethodne godine tada je **stara koliko i poslednje aprilsko
osvežavanje** — a to se nigde ne vidi. Postojanje podataka **nije dokaz svežine**.

**Šta proveriti [Z]:**

1. Da li se prethodna godina osvežava nekim drugim putem.
2. Ako ne — da li se ispravke uopšte menjaju posle zaključenja godine. Ako se ne menjaju,
   problem ne postoji u praksi i zatvara se kao „prihvaćeno“.

**Predlog rešenja ako se menjaju [Z]:** proširiti proceduru da posle aprila osvežava i
prethodnu godinu, ili uvesti zaseban prolaz za nju — uz dogovor sa vlasnikom baze.

---

### 10.4.6. Obračuni — Ugovori i menice

#### P-40 — APR provera zaobilazi SSL i prepoznaje samo jedan status

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `ugovori/apr_openapi.py:34-45` |
| **Obračun** | [U-01](#u-01--provera-statusa-partnera-u-apr-u) |
| **Pitanje** | Q38 |

**A) Zaobilaženje provere SSL potvrde [P]**

```python
try:
    response = requests.get(url, timeout=timeout)
except SSLError:
    urllib3.disable_warnings(InsecureRequestWarning)
    response = requests.get(url, timeout=timeout, verify=False)
```

Pri SSL grešci zahtev se **ponavlja bez provere potvrde**, uz gašenje upozorenja.

**Posledica [Z]:** podatak o statusu partnera — koji se koristi pri odlukama o ugovaranju
i plaćanju — može doći od **neprovereno g izvora**. Greška u potvrdi je upravo signal koji
ne bi trebalo zaobići.

**Predlog rešenja [Z]:** prekinuti sa jasnom porukom umesto zaobilaženja. Ako je problem
u zastarelim korenskim potvrdama na serveru, rešiti to na serveru (`certifi` je već u
zavisnostima).

**B) Prepoznaje se samo tačan tekst `активан` [P]**

```python
str(status or "").strip().casefold() == "активан".casefold()
```

Poređenje je **tačno**, ne „sadrži“, i traži **ćirilični** zapis.

**Posledica [Z]:** svaki drugi zapis statusa — `Активан у ликвидацији`, latinično
`Aktivan`, status sa dodatnim razmakom unutar reči — daje **`is_active = False`**,
pa partner izgleda kao ugašen iako nije.

**Predlog rešenja [Z]:** popisati sve vrednosti koje APR vraća (**Q38**) i uskladiti
uslov; do tada, kod nepoznatog statusa **ne menjati** `is_active`, nego samo upisati
`apr_status` i označiti za proveru.

---

#### P-41 — Preuzimanje menica zavisi od izgleda stranice NBS-a

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |
| **Gde** | `menice/scraper.py`, `menice/services.py:164-174` |
| **Obračun** | [U-03](#u-03--preuzimanje-menica-iz-registra-nbs) |

**A) Krhka integracija [P]:** podaci se preuzimaju **razlaganjem HTML stranice**
registra NBS (`BeautifulSoup`), a ne kroz programski interfejs. Promena izgleda stranice
zaustavlja preuzimanje.

**B) PIB Instituta upisan u kod [P]:**

```python
def sync_izlazne_menice(*, tax_code="100223617", ...):
```

Podrazumevani PIB je upisan kao podrazumevana vrednost parametra.

> **Napomena [Z]:** ovo je blaži slučaj od **P-34** — vrednost se **može** proslediti
> spolja, pa nije neophodna izmena koda. Ipak, podatak o firmi pripada konfiguraciji.

**Predlog rešenja [Z]:**

1. Preseliti PIB u konfiguraciju (isto rešenje kao za podatke platioca u virmanu, **P-33**).
2. Dodati proveru da je preuzimanje vratilo očekivanu strukturu i **jasnu poruku** kada nije.
3. Beležiti svaki prolaz u istoriju, kao što to rade Finansije i Potraživanja.

> **Slična krhka integracija [Z]:** Selenium preuzimanje goriva sa portala NIS i OMV
> (vidi [7. Integracije](#7-integracije)) ima isti rizik.

---

### 10.4.7. Obračuni — Finansijska analitika

#### P-42 — Konta i pravila toka gotovine upisani su u kod

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `finansije/services/cash_flow.py`, `reports.py` |
| **Obračun** | [F-07 … F-12](#611-registar-obračuna) |
| **Pitanje** | Q43 |

**Šta je zatečeno [P]:** obračun toka gotovine sadrži **više od 40 broja konta** upisanih
u kod — spiskove za dodatne `ON` naloge, zamene obaveza troškovima, zarade, refundacije,
PDV i završna isključenja. Isto važi i za isključenja u prihodima i rashodima
(`59900`, `69900`) i za konta faktura (`20400`, `20500`, `61420`, `61421`, `61521`, `64002`).

**Posledica [Z]:**

1. Izmena kontnog plana zahteva **izmenu koda i isporuku nove verzije**.
2. Nigde u bazi ne postoji zapis o tome koja pravila važe niti od kada.
3. **Pravilo je udvostručeno** — isto postoji i u izvornim procedurama `SPFINizv52/52nt`.
   Promena procedure **ne bi se odrazila** na aplikaciju, i obrnuto.

> **Olakšavajuća okolnost [P]:** kod je **verna kopija** postojeće poslovne metodologije.
> Svi spiskovi konta **navedeni su poimence** u
> [6.1.4](#konta-upisana-u-obračun-toka-gotovine), pa nisu
> skriveni.

**Predlog rešenja [Z]:** dogovoriti ko obaveštava o izmeni kontnog plana ili procedura,
i uvesti proveru koja upozorava kada se u izvoru pojavi konto koji pravila ne pokrivaju.

---

#### P-43 — Mogući dvostruki obuhvat zajedničkih troškova

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `finansije/services/reports.py`, `shared_costs.py` |
| **Obračun** | [F-02, F-05, F-06](#611-registar-obračuna) |
| **Pitanje** | Q41 |

**Šta je zatečeno [P]:** postojeća metodologija to sama navodi:

> *„Osnovni `R` već sadrži sve odgovarajuće proknjižene stavke klase 5, uključujući
> eventualna knjiženja zajedničkih troškova u izvoru. Aplikacija nema zasebno pravilo
> koje iz klase 5 uklanja ranije proknjiženu raspodelu.“*

**Posledica [Z]:** ako se u knjigovodstvu uvede knjiženje raspodele zajedničkih troškova
na pojedinačne poslove, ista stavka bi ušla **i u rashode `R` i u raspodeljeni `ZT`**,
pa bi konačni rezultat `P − R − ZT` bio **dvostruko umanjen**.

**Trenutno stanje [Z]:** nije problem, jer se raspodela ne knjiži na taj način.
Ali to je pretpostavka koju aplikacija **ne proverava**.

**Predlog rešenja [Z]:** potvrditi sa knjigovodstvom da se raspodela ne knjiži na klasu 5,
i uvesti proveru koja upozorava ako se takva knjiženja pojave.

---

#### P-44 — Promena centra pregrupiše celu istoriju Finansija

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `finansije/services/source.py:95-97` |
| **Obračun** | [F-01, F-02, F-13](#611-registar-obračuna) |
| **Pitanje** | Q42 |

**Šta je zatečeno [P]:** centar posla se uzima iz **aktuelnog** šifarnika (`posao.blok`)
pri svakoj sinhronizaciji. Ne postoji istorija pripadnosti posla centru po datumima.

**Posledica [P]:** ako se poslu promeni centar, **sva njegova ranija knjiženja** se pri
sledećoj sinhronizaciji pripišu novom centru. Izveštaj po centrima za **prošlu godinu**
može se promeniti, iako se nijedno knjiženje nije promenilo.

**Isti obrazac u Floti [P]:** vidi **P-05**. Flota za deo izveštaja **već ima** istorijsku
dodelu (`JobCode.assigned_date`), pa se isto rešenje može primeniti i ovde.

**Predlog rešenja [Z]:** uvesti istoriju pripadnosti posla centru sa datumima važenja,
i pri sinhronizaciji upisivati centar **koji je važio na datum knjiženja**.

> **Napomena [P]:** postojeća dokumentacija ovo **navodi kao svesno ograničenje**, ne kao
> grešku. Ovde se vodi zato što menja već objavljene izveštaje.

---

### 10.4.8. Struktura baze

#### P-45 — Modul Menice nema migracije

| | |
|---|---|
| **Ozbiljnost** | **Visoka** |
| **Status** | Za rešavanje |
| **Gde** | Aplikacija `menice` |
| **Modul** | [3.7. Menice](#37-menice) |
| **Pitanje** | Q44 |

**Šta je zatečeno [P]:** aplikacija `menice` **uopšte nema direktorijum `migrations/`**.
Ostale aplikacije ih imaju:

| Aplikacija | Migracija |
|---|---|
| `fleet` | 77 |
| `nabavka` | 20 |
| `hr`, `ugovori` | po 12 |
| `mobilni` | 8 |
| `potrazivanja` | 7 |
| `naplata` | 6 |
| `finansije` | 3 |
| `core` | 1 |
| **`menice`** | **0 — nema ni direktorijuma** |

Modeli `Menica` i `UlaznaMenica` **nisu** označeni sa `managed = False`, pa Django
očekuje da njima upravlja.

**Posledice [Z]:**

1. **`manage.py migrate` ne stvara tabele `menica` i `ulazna_menica`.** Na novom
   okruženju modul ne bi radio.
2. Pokretanje `makemigrations menice` napravilo bi **početnu migraciju sa `CREATE TABLE`**,
   koja bi na postojećoj bazi **pukla** — tabele već postoje.
3. **Nijedna izmena modela ne može se preneti** uobičajenim putem; svaka bi tražila ručnu
   izmenu u bazi.
4. Istorija strukture ovih tabela **ne postoji** u projektu.

> **Zašto testovi ipak prolaze [Z]:** Django za aplikacije bez migracija stvara tabele
> direktno iz modela pri pripremi test baze. Zato 2 testa modula prolaze, iako bi
> `migrate` na pravoj bazi zakazao.

**Predlog rešenja [Z]:**

1. Napraviti početnu migraciju: `manage.py makemigrations menice`.
2. Uporediti je sa **stvarnom strukturom** tabela u bazi i uskladiti razlike.
3. Označiti je kao već primenjenu: `manage.py migrate menice --fake-initial`.
4. Proveriti da posle toga `migrate` prolazi bez izmena.

> **Pre izmene [N]:** utvrditi kako su tabele prvobitno nastale (**Q44**) — ako su
> pravljene ručnim SQL-om, njihova struktura može odstupati od modela.

---

### 10.5. Infrastruktura

#### P-15 — Jedan Celery radnik poništava razdvajanje redova

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `nssm.bat:31`, `ims_erp/settings/base.py:212` |

**Šta je zatečeno [P]:** produkcioni radnik se pokreće sa

```
celery -A ims_erp worker -l info -P solo -Q default,sync,selenium
```

`-P solo` znači **jedan zadatak u jednom trenutku**. Postavka
`CELERY_WORKER_CONCURRENCY = 2` u tom režimu **nema dejstva**.

**Posledica [Z]:** razdvajanje redova `sync` i `selenium`, uvedeno upravo zato da teški
Selenium poslovi ne blokiraju lake sinhronizacije, **ne daje nikakav efekat** dok radi
samo jedan radnik. Preuzimanje goriva koje traje sat vremena zaustavlja sve ostalo.

**Predlog rešenja [Z]:** pokrenuti **drugi Windows servis** — radnika vezanog samo za
red `sync`, a postojećeg ograničiti na `selenium`.

> **Potrebna potvrda [N]:** `-P solo` je verovatno izabran zbog poznatih teškoća
> Celery-ja na Windows-u. Pre izmene proveriti da li je to bio razlog.

---

#### P-16 — Zaključavanje poslova popušta kada Redis nije dostupan

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `fleet/tasks.py:72-85` |

**Šta je zatečeno [P]:** ako Redis nije dostupan, zaključavanje se preskače i
**posao se ipak izvršava** (`fail-open`).

**Posledica [Z]:** pri ispadu Redisa dva ista posla mogu raditi istovremeno — na primer
dva Selenium preuzimanja goriva ili dve sinhronizacije servisa. Rezultat mogu biti
duplirani zapisi ili međusobno gaženje.

**Predlog rešenja [Z]:** za poslove koji upisuju podatke prekinuti izvršavanje kada
zaključavanje nije moguće (`fail-closed`), i zabeležiti to u istoriji kao „Preskočen“.

> **Napomena [P]:** Finansije ovo **već rešavaju bolje** — koriste SQL Server
> `sp_getapplock` u istoj sesiji, pa zaštita ne zavisi od Redisa.

---

#### P-17 — Procedura `sp_AzurirajNalogZ` ne briše obrisane redove

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Prihvaćeno |
| **Gde** | `IMS_ERP.dbo.sp_AzurirajNalogZ` |

**Šta je zatečeno [P]:** procedura ažurira postojeće i dodaje nove redove, ali
**ne uklanja** redove koji su u međuvremenu obrisani u izvoru.

**Posledica [P]:** uspešno izvršavanje procedure **ne znači** da je lokalna kopija
`IMS_ERP.dbo.nalog_z` jednaka izvoru.

Dodatno, `BrojAzuriranihRedova` broji **sve** redove obuhvaćene naredbom `UPDATE`,
ne samo one čiji se sadržaj stvarno promenio — veliki broj ne znači veliku promenu. [P]

**Zašto je prihvaćeno [Z]:** procedura je poslovni objekat van aplikacije. Aplikacija je
**ne menja**, samo je pokreće. Finansijska analitika ovaj problem **zaobilazi** tako što
čita **udaljeni izvor**, a ne lokalnu kopiju.

**Za dalji rad [Z]:** pre eventualnog prelaska Naplate na lokalnu kopiju, ovo mora
biti rešeno — opisano u `naplata-lokalni-izvor-plan.md`, poglavlje 5 (dokument uklonjen 18.09.2026., u git istoriji `06f60c2`).

---

### 10.6. Podaci i moduli

#### P-18 — Naplata i Potraživanja rade paralelno

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za rešavanje |

**Šta je zatečeno [P]:** dva modula pokrivaju isti posao:

| | Naplata (`naplata`) | Potraživanja (`potrazivanja`) |
|---|---|---|
| Izvor | Nasleđeni `dbo.*` pogledi | Sopstvene Django tabele uz sinhronizaciju |
| Brzina | Spora | Brza |
| Istorija stanja | Nema | Objavljeni snimci |
| Revizorski trag | Nema | `CollectionAudit` |
| Status | **Nasleđeno, gasi se** | Zamenjuje Naplatu |

**Posledica [Z]:** dok oba rade, isti podatak se može videti na dva mesta sa različitim
vrednostima, jer se čitaju različiti izvori u različito vreme.

**Odluka naručioca (18.09.2026.) [P]:** Naplata se **ne dokumentuje**; sav novi rad
ide u Potraživanja.

**Za dalji rad [Z]:** odrediti datum gašenja Naplate i ukloniti njen meni iz interfejsa
kada Potraživanja preuzmu sve funkcije, uključujući pravnu službu.

---

#### P-19 — Dva mehanizma za ograničenje po centrima

| | |
|---|---|
| **Ozbiljnost** | **Srednja** |
| **Status** | Za proveru |
| **Gde** | `core/models.py:78-90` |
| **Pitanje** | Q5 |

**Šta je zatečeno [P]:**

| Polje | Tip |
|---|---|
| `CustomUser.allowed_centers` | Veza više-prema-više ka `OrganizationalUnit` |
| `CustomUser.allowed_center_codes` | Tekst, šifre odvojene zarezima |

Oba postoje istovremeno. Različiti moduli koriste različito:

| Modul | Koristi |
|---|---|
| `fleet/support/management_reports.py: allowed_centers()` | **Oba, sabrano** |
| `fleet/support/fleet_snapshot.py` | Samo `allowed_centers` |
| `fleet/views/center_statistics.py` | Samo `allowed_centers` |

**Posledica [Z]:** korisnik kome je upisana šifra centra samo u tekstualno polje
vidiće izveštaje za upravu, ali **neće** videti presek stanja flote za taj centar.
Pravo pristupa zavisi od ekrana, što je teško objasniti korisniku.

**Predlog rešenja [Z]:** odrediti jedan merodavan mehanizam, preseliti podatke i ukloniti
drugi. Veza ka `OrganizationalUnit` je pouzdanija jer se oslanja na šifarnik.

---

#### P-20 — Model Naplate navodi nepostojeći pogled

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | Prihvaćeno |
| **Gde** | `naplata/models.py:163` naspram `naplata/queries.py:32` |

Model navodi tabelu `dodela_bucketa`, dok stvarni upiti koriste **`dodela_baketa`**.

**Za dalji rad [Z]:** **ne preimenovati aktivni pogled** na osnovu modela — model je taj
koji je pogrešan. Pošto se Naplata gasi, ispravka nema svrhu.

---

### 10.7. Repozitorijum

#### P-21 — Radni fajlovi u repozitorijumu

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | **Rešeno** (18.09.2026.) |

| Šta | Veličina | Napomena |
|---|---|---|
| `db.sqlite3` | 6,7 MB | Naveden u `.gitignore`, ali je u projektu |
| `ims-flota-worker-err.log` | 9,8 MB | Dnevnik rada |
| `ims-flota-worker-out.log` | 7,8 MB | Dnevnik rada |
| `tmp*.csv` | ~1,6 MB | Privremeni izvozi |
| `~$*.docx` | — | Privremeni Word fajlovi |
| Word i Excel analize u korenu | ~4 MB | Radni materijal, ne deo aplikacije |

**Predlog rešenja [Z]:** premestiti radni materijal u `dokumentacija/`, obrisati
privremene fajlove i dnevnike iz projekta, proveriti da li su zaista izvan kontrole
verzija.

**Šta je urađeno (18.09.2026.) [P]:** uklonjeno je samo ono kod čega nema dileme.

| Uklonjeno iz repozitorijuma | Šta je bilo |
|---|---|
| `tmp1192810480842213795.csv`, `tmp729760060394745781.csv` | Preuzimanja OMV transakcija koja ostavlja Selenium; ušla su u repozitorijum sa izmenom `361b81d`. |
| `~$*.docx` (4 fajla) | Word fajlovi zaključavanja otvorenog dokumenta, po 162 bajta. |

U `.gitignore` su dodata pravila `tmp*.csv` i `~$*`, da se isto ne ponovi.

**Drugi krug, po odluci korisnika (18.09.2026.) [P]:** uklonjeno je još **95 fajlova**.

| Grupa | Broj | Veličina | Napomena |
|---|---|---|---|
| `dokumentacija/arhiva/` | 42 | 20,7 MB | Međuverzije Word dokumenata koje su generatori pravili pre svake izmene. Direktorijum više ne postoji. |
| Snimci ekrana | 22 | 1,7 MB | 16 se nije pominjalo nigde, 6 samo u skriptama koje su takođe uklonjene. **Zadržana su tri** koja koristi `unos-vozila-carobnjak.md`. |
| Jednokratne `.py` skripte | 14 | 0,1 MB | Generatori Word dokumenata (`generisi_*`, `dopuni_*`) i provere (`provera_*`, `proveri_*`). |
| Word analize u korenu | 10 | 1,7 MB | Presek stanja (3), Kadrovi (4), Analiza aplikacije, Garaža IMS, Procena prenosa. Sadržaj je prešao u `docs/`. |
| Excel izvozi i planovi | 7 | 1,6 MB | Jednokratni izvozi i evidencije nabavke. |
| Dnevnici Celery-ja | 3 | 16,9 MB | **Bili izvan kontrole verzija — brisanje je trajno.** |
| `celerybeat-schedule.{bak,dat,dir}` | 3 | 1,7 KB | Stanje Celery beat-a od 02.12.2024.; beat ga sam pravi. |

Svi osim dnevnika bili su u gitu, pa ih **istorija i dalje čuva**.

**Šta je spaseno pre brisanja [P]:** tri datoteke koje su izgledale kao radni otpad
sadržale su **definicije nasleđenih SQL pogleda**. Premeštene su u
[`dokumentacija/ddl-nasledjenih-pogleda/`](#prilog-b--ddl-nasleđenih-sql-pogleda), uz opis
šta koji pogled radi. Dve od njih **nisu bile u gitu** — brisanje bi bilo nepovratno.
Videti [P-27](#p-27--formule-11-izveštaja-nisu-u-projektu).

**Šta namerno nije dirano [P]:**

| | Zašto |
|---|---|
| `db.sqlite3` (6,7 MB) | Izvan kontrole verzija, a **trenutno je razvojna baza** — brisanje bi uništilo lokalne podatke. |
| `IZ 055 Radna lista.xlsx`, `IZ 073 Zahtev za put.doc`, `Obrazac za ocenjivanje.xlsx` | Originalni obrasci koje reprodukuju štampani šabloni u kodu (`work_time_sheet_print.html`, `putni_nalog_print_foreign.html`). |
| `izvestaji/backup_*.json` | Rezervne kopije podataka o dodelama vozila, unosu vozila i fotografijama. |

**Posledica na kod [P]:** komanda `import_garage_requests_excel` imala je podrazumevanu
putanju `"Pracenje nabavke za garazu.xlsx"`, koja sada ne postoji. Putanja je **postala
obavezan argument**, da komanda odmah javi grešku umesto da traži nepostojeći fajl.

---

#### P-22 — Nekorišćene zavisnosti

| | |
|---|---|
| **Ozbiljnost** | Niska |
| **Status** | **Rešeno** (18.09.2026.) |

| Biblioteka | Stanje |
|---|---|
| `djangorestframework` 3.15.2 | Nije u `INSTALLED_APPS`, ne koristi se nigde u kodu |
| `psycopg2-binary` 2.9.9 | Nijedna konfiguracija ne koristi PostgreSQL |

**Posledica [Z]:** nepotrebno održavanje i bezbednosno praćenje biblioteka koje sistem
ne koristi.


**Šta je urađeno (18.09.2026.) [P]:** oba reda su uklonjena iz `requirements.txt`.
Pre uklanjanja provereno je pretragom celog projekta da se `rest_framework` i `psycopg2`
**nigde ne uvoze** i da nisu u `INSTALLED_APPS`. Kodiranje datoteke (UTF-16LE sa BOM)
zadržano je nepromenjeno.

---

### 10.8. Ograničenja koja nisu greške

Ovo su svesna ograničenja sistema, navedena da bi se izbeglo pogrešno tumačenje.

| Ograničenje | Objašnjenje |
|---|---|
| **Podaci nisu u realnom vremenu** | Većina se osvežava jednom dnevno, noću. Korisnik ujutru vidi stanje od sinoć. |
| **Zavisnost od tri udaljena servera** | Finansije i Kadrovi ne rade ako `PUTGEO-SERVER`, `INFORMATIKA23` ili `SERFIN` nisu dostupni. |
| **Zavisnost od portala dobavljača goriva** | Promena izgleda stranice NIS-a ili OMV-a zaustavlja automatsko preuzimanje. |
| **Definicije nasleđenih pogleda nisu u projektu** | Promena pogleda u bazi menja rezultat na ekranu bez ijedne izmene u aplikaciji. |
| **Nema povratne veze ka knjigovodstvu** | Sistem čita knjiženja; ne knjiži. Jedini izlaz je datoteka virmana. |
| **Rezultati obračuna se ne čuvaju** | Skoro svi obračuni se rade u trenutku prikaza. Izveštaj otvoren danas i za mesec dana može dati različit rezultat za isti period, ako su se ulazni podaci promenili. |
| **Prosečna potrošnja ne razdvaja AdBlue** | `fleet_fuelconsumption` ne čuva vrstu proizvoda. Vozila koja koriste AdBlue imaju precenjenu potrošnju. |
| **Finansije izuzimaju zatvaranja** | Vrsta `ZAT` i konta `59900`/`69900` se namerno izostavljaju. Zbir svih stavki klase 5/6 posle zatvaranja godine je nula — to nije greška. |

---

### 10.9. Šta je proveravano i **nije** problem

Da bi se izbeglo ponovno ispitivanje istog:

| Provereno | Nalaz |
|---|---|
| `calculate_average_fuel_consumption_ever()` | **Ispravno** — obe granice se proveravaju na `mileage > 0` |
| `fleet_snapshot()` prosečna starost | **Ispravno** — računa samo vozila sa godinom između 1886. i tekuće |
| `service_category()` u `vehicle_maintenance.py` | **Ispravno** — normalizuje dijakritike i ćirilicu |
| `TrafficCard.for_plate()` | **Ispravno** — namerno odbija da pogađa kada tablica pripada većem broju vozila |
| Prečišćavanje OMV transakcija (V-06) | **Ispravno** i neophodno — bez njega su zbirovi višestruko uvećani |
| Kontrolni zbirovi pri sinhronizaciji Finansija | **Ispravno** — neslaganje zaustavlja objavu |
| `ReceivablePosition.balance` | **Ispravno** — proverava ga sama baza (`CheckConstraint`) |
| Zaštita od preklapanja u Finansijama | **Ispravno** — `sp_getapplock` u istoj sesiji |

---

### 10.10. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Detaljan opis pogođenih obračuna | [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj) |
| Plan daljeg razvoja | [11. Plan razvoja](#11-plan-razvoja) |
| Održavanje i zakazani poslovi | [9. Održavanje](#9-održavanje) |
| Sva otvorena pitanja za korisnika | [Inventar, poglavlje 14](00-inventar-i-plan-dokumentacije.md) |

---

## 11. Plan razvoja

> **Za koga je ovo poglavlje:** uprava i programeri.
> Sadrži **postojeće planove** i **predloge koji proizlaze iz ovog pregleda**.
> Status tvrdnji: **[P]** potvrđeno, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

### 11.1. Šta je već isplanirano

U projektu postoje tri razrađena plana, nastala pre ove dokumentacije:

| Plan | Dokument | Stanje |
|---|---|---|
| **Centralna organizacija i dozvole (V2)** | [`plan-organizacije-i-dozvola-v2.md`](plan-organizacije-i-dozvola-v2.md) | **Aktuelan plan za realizaciju** |
| Centralizacija organizacije i šifara posla | [`plan-centralizacije-organizacije.md`](plan-centralizacije-organizacije.md) | Prethodna verzija, poslovna pravila i dalje važe |
| Prelazak Naplate na lokalni izvor | `naplata-lokalni-izvor-plan.md` (uklonjen, git `06f60c2`) | Delimično izvedeno |
| Nova Naplata — Potraživanja | `naplata-nova-aplikacija-plan.md` (uklonjen, git `06f60c2`) | **Izvedeno**, u paralelnom radu |

---

### 11.2. Centralna organizacija i dozvole (V2)

**Najveći planirani zahvat.** Puni tekst:
[`plan-organizacije-i-dozvola-v2.md`](plan-organizacije-i-dozvola-v2.md).

#### Zašto [Z]

Danas se organizaciona pripadnost i prava pristupa vode na **nedosledan način**:

| Nedostatak | Posledica | Problem |
|---|---|---|
| Dva mehanizma za centre | Pravo pristupa zavisi od ekrana | [P-19](#10-poznati-problemi-i-ograničenja) |
| Nema istorije pripadnosti posla centru | Prošli izveštaji se menjaju | [P-44](#10-poznati-problemi-i-ograničenja) |
| Flota mestimično koristi poslednju umesto istorijske dodele | Zbirovi po centrima se ne slažu | [P-05](#10-poznati-problemi-i-ograničenja), [P-24](#10-poznati-problemi-i-ograničenja) |

#### Šta plan uvodi [P]

| Tema | Sadržaj |
|---|---|
| **Tri nivoa organizacije** | Centar → organizaciona jedinica → šifra posla |
| **Uloga zajedno sa obuhvatom** | Dozvola se dodeljuje **uz centar, OJ ili posao**, ne globalno |
| **Stalni identitet i istorija** | Šifra posla zadržava identitet i kroz promene naziva i centra |
| **Snimak na dokumentu** | Dokument pamti pripadnost **u trenutku nastanka** |
| **Sistematizacija** | Ko koga vodi i ko koga ocenjuje |
| **Poslovni Admin panel** | Dodela prava bez Django admina |
| **Efektivni pristup** | Ekran koji pokazuje **šta korisnik stvarno vidi** i zašto |
| **Deset koraka prelaska** | Sa kontrolom postojećih prava i mogućnošću povratka |

#### Uticaj na postojeće obračune [Z]

Uvođenje istorije pripadnosti rešava **četiri zabeležena problema odjednom**:
P-05, P-24, P-44 i deo P-19.

#### Stanje realizacije registra [P]

Razrada: [`plan-registra-sifara-posla.md`](plan-registra-sifara-posla.md).

| Faza | Stanje |
|---|---|
| Faza 1 — registar (`organizacija`), uvoz, stablo, kontrolni izveštaj | Izvedeno; otvorena pitanja o šiframa `111111`, `432`, `vranj`, `vranjs` i `960001` |
| Faza 2, Flota — koraci 1–3 (veza `org_node`, popunjavanje, uporedni izveštaj) | Izvedeno 25.09.2026. **Čitanje iz registra (korak 4) nije uključeno** |
| Nova sinhronizacija (01:40) | Radi paralelno sa starom (`fetch_job_codes`, 01:30): osvežava registar, povezuje Flotu i poredi staro i novo. Staru ne menja |
| Faza 2, ostali moduli | Nije počelo |

**Redosled gašenja [Z]:** stara i nova sinhronizacija rade zajedno sve vreme. Moduli prelaze
na čitanje iz registra **jedan po jedan**, svaki tek kad mu uporedni izveštaj prođe. Stara
sinhronizacija i `OrganizationalUnit` gase se **poslednji**, kad nijedan modul više ne čita
staro polje — do tada na njih pokazuju strani ključevi putnih naloga, dodela i nabavke.

**Odluke 25.09.2026.:** centri poslovnog i naučnog bloka su `2` i `3` (knjiženja ih vode kao
jedinice `20` i `30`); naučna šifra je `3` + šifra radnika iz Kadrova + broj projekta i **deo
je bloka 3** (naučni projekat je jedinica, šifra je učešće radnika, radnik je povezan sa Kadrovima); nazivi centara i jedinica su po Pravilniku o
organizaciji od 18.04.2024. (latinicom). Uporedni izveštaj Flote na produkcionim podacima
(proba) se poklapa do dinara u svih 9 centara, bez ijednog nepovezanog zapisa.

---

### 11.3. Gašenje nasleđene Naplate

#### Stanje [P]

| | Naplata (nasleđeno) | Potraživanja |
|---|---|---|
| Izvor | Nasleđeni pogledi, pri svakom otvaranju | Lokalne tabele uz sinhronizaciju |
| Brzina | Spora | Brza |
| Istorija stanja | **Nema** | Objavljeni snimci |
| Kontrole | Nema | **Šest kontrolnih zbirova** |
| Revizorski trag | Nema | `CollectionAudit` |
| Status | **Gasi se** | Zamenjuje je |

**Odluka naručioca (18.09.2026.) [P]:** Naplata se **ne dokumentuje**; sav novi rad ide
u Potraživanja.

#### Šta ostaje da se uradi [Z]

| # | Korak |
|---|---|
| 1 | Potvrditi da su **sve** funkcije Naplate pokrivene, uključujući **pravnu službu** ([Q12](00-inventar-i-plan-dokumentacije.md)) |
| 2 | Odrediti **datum gašenja** ([Q34](#68-potraživanja--obračuni)) |
| 3 | Uporediti saldo dva sistema na isti datum — dok oba rade |
| 4 | Ukloniti meni Naplate iz interfejsa |
| 5 | Ukloniti aplikaciju `naplata` iz `INSTALLED_APPS` i njene rute |
| 6 | Odlučiti šta sa nasleđenim pogledima koje je koristila samo Naplata |

> **[P] Do gašenja ne menjati pravilo starosnih razreda** — promena bi onemogućila
> poređenje dva sistema. Vidi [P-35](#10-poznati-problemi-i-ograničenja).

---

### 11.4. Preuzimanje definicija nasleđenih pogleda

**Dogovoreno (18.09.2026.):** DDL stiže **od ponedeljka**. [P]

#### Zašto je važno [Z]

**37 objekata baze** čita se bez ijednog podatka o tome kako su napravljeni.
Za **11 izveštaja Flote** formula postoji **isključivo u bazi** — [P-27](#10-poznati-problemi-i-ograničenja).

#### Redosled preuzimanja [Z]

| Prioritet | Objekti | Zašto |
|---|---|---|
| **1** | `fleet_tro_svi`, `fleet_tro_goriva_m`, `fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`, `tro_zarade`, `fleet_dobavljaci`, `fleet_magacin_rez`, `kasko_rate` | Izveštaji koji idu upravi, formula potpuno u bazi |
| **2** | `fleet_servisi`, `fleet_trebovanja`, `fleet_potrazivanje_ddor`, `fleet_zatvoren_putni`, `vrednost_vozila`, `lizing_kamate`, `sif_pos_trenutno`, `v_organizationalunit`, `fleet_otpis` | Izvori sinhronizacija Flote |
| **3** | `nbv_preuzete_EUF`, `nbv_EUF_stavke`, `nbv_roba`, `nbv_sif_pos_par` | Nabavka |
| **4** | `hr_employee` | Kadrovi |
| **5** | `posao` (na `PUTGEO-SERVER`) | Potraživanja i Finansije |

#### Šta uraditi kada stigne [Z]

1. Smestiti DDL u `dokumentacija/sql/` — **pod kontrolu verzija**.
2. Dopuniti poglavlje [6.5.5](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji) stvarnim formulama.
3. Dopuniti [4.12](#412-nasleđeni-objekti-baze-dbo).
4. **Odrediti vlasnika** koji odobrava izmene tih pogleda.

---

### 11.5. Prioriteti iz registra problema

**50 uočenih problema, od toga 20 rešeno (18–19.09.2026.). U Floti je od 21 problema rešeno 16.**

| Dan | Rešeno |
|---|---|
| 18.09. | P-10, P-13, P-14 A-C, P-21, P-22, P-26, P-36, P-46 |
| 19.09. | **P-01** (tajne), **P-02** (prosečna potrošnja), **P-04** (brzina), **P-05** (centar, za V-07), **P-06** (premija polise), **P-07** (kamata lizinga), **P-09** (vozila bez troška) |

Predlog redosleda za ostale — po tome **šta daje pogrešan broj**:

#### Prvo — pogrešan poslovni rezultat

| # | Problem | Zašto prvo |
|---|---|---|
| [P-23](#10-poznati-problemi-i-ograničenja) | Lizing samo u mesecu početka | Izveštaj ne pokazuje mesečni trošak |
| [P-08](#10-poznati-problemi-i-ograničenja) | Operativni lizing razmazan | Rata od 50.000 ulazi kao 1.370. **Traži proveru podataka pre izmene koda** — vidi **Q45** |
| [P-31](#10-poznati-problemi-i-ograničenja) | Obustava mobilnih se nigde ne čuva | Nema traga šta je prosleđeno u zarade |
| [P-33](#10-poznati-problemi-i-ograničenja) | Virman skraćuje podatke i ne čuva poslatu datoteku | Tiho skraćivanje iznosa i naziva |

> **[Z] Olakšica:** za P-23 **ispravno rešenje već postoji u kodu**, u drugom modulu —
> isti postupak koji je 19.09.2026. primenjen na P-06 i P-07.

> **Rešeno 19.09.2026.:** ~~P-02~~ (prosečna potrošnja), ~~P-06~~ (premija polise),
> ~~P-07~~ (kamata lizinga). Sva tri su davala **pogrešan poslovni broj**.

#### Drugo — bezbednost i trag

| # | Problem |
|---|---|
| [P-01](#10-poznati-problemi-i-ograničenja) | Lozinke, `SECRET_KEY` i `DEBUG = True` u repozitorijumu |
| [P-48](#10-poznati-problemi-i-ograničenja) | **Imena, adrese i brojevi računa 329 osoba u git istoriji** — rešava se istim postupkom kao P-01 |
| [P-34](#10-poznati-problemi-i-ograničenja) | **Poslovni izuzetak upisan u kod** — potvrđena greška |
| [P-31](#10-poznati-problemi-i-ograničenja) | Obustava mobilnih se nigde ne čuva |
| [P-33](#10-poznati-problemi-i-ograničenja) | Virman skraćuje podatke i ne čuva poslatu datoteku |
| [P-45](#10-poznati-problemi-i-ograničenja) | Modul Menice nema migracije |

#### Treće — doslednost

P-05, P-24, P-44 (istorijska pripadnost — rešava ih **plan V2**),
P-19 (dva mehanizma za centre), P-28 (dva obračuna sati).

#### Četvrto — infrastruktura i održavanje

P-15 (jedan radnik), P-16 (zaključavanje popušta), P-27 (DDL 11 izveštaja Flote — prvi
deo preuzet 18.09.2026., videti [`ddl-nasledjenih-pogleda/`](#prilog-b--ddl-nasleđenih-sql-pogleda)).

#### Rešeno 18.09.2026.

| # | Šta je bilo |
|---|---|
| [P-36](#10-poznati-problemi-i-ograničenja) | Zbir faktura Nabavke sabirao je fakturu jednom po stavci |
| [P-46](#10-poznati-problemi-i-ograničenja) | Zapis goriva bez vaučera ili količine nestajao je sa **svih** ekrana goriva |
| [P-13](#10-poznati-problemi-i-ograničenja) | Superuser je dobijao 403 na statistici centra |
| [P-14](#10-poznati-problemi-i-ograničenja) | Otpisana vozila, prosečna starost i dijakritici u kategorijama (A, B, C; **D ostaje**) |
| [P-26](#10-poznati-problemi-i-ograničenja) | Izveštaj goriva za upravu čitao je OMV bez prečišćavanja |
| [P-10](#10-poznati-problemi-i-ograničenja) | Napomena o maloj kilometraži poredila je period sa godišnjim pragom |
| [P-22](#10-poznati-problemi-i-ograničenja) | Nekorišćene zavisnosti u `requirements.txt` |
| [P-21](#10-poznati-problemi-i-ograničenja) | 95 radnih fajlova u repozitorijumu (arhiva, snimci ekrana, jednokratne skripte, dnevnici) |

**Novo otkriveno pri ispravkama:** [P-47](#10-poznati-problemi-i-ograničenja) — ključ za duplikate
OMV transakcija ne obuhvata iznos ni valutu. **Za proveru nad stvarnim podacima.**

---

### 11.6. Predlozi koji proizlaze iz ovog pregleda

Ovo **nisu** obaveze — predlozi za razmatranje. [Z]

#### A) Poslovna pravila u bazu, ne u kod

| Sada u kodu | Predlog |
|---|---|
| Poseban broj telefona | Oznaka u evidenciji — **potvrđeno kao greška** ([P-34](#10-poznati-problemi-i-ograničenja)) |
| Pragovi troška po kilometru | Šifarnik sa ekranom za održavanje ([P-11](#10-poznati-problemi-i-ograničenja)) |
| Konta toka gotovine | Šifarnik ili barem provera pokrivenosti ([P-42](#10-poznati-problemi-i-ograničenja)) |
| Podaci platioca u virmanu | Konfiguracija ([P-33](#10-poznati-problemi-i-ograničenja)) |
| PIB za pretragu registra menica | Konfiguracija ([P-41](#10-poznati-problemi-i-ograničenja)) |
| Vreme 16:00 za službeni izlazak | Podešavanje ([Q27](#66-kadrovi--obračuni)) |

#### B) Čuvati ono što je poslato

Tri rezultata idu izvan sistema, a **nijedan se ne čuva** [Z]:

| Rezultat | Predlog |
|---|---|
| **Virman** | Tabela generisanih virmana sa sadržajem ili otiskom, iznosom i spiskom naloga |
| **Obustave mobilnih** | Tabela obračunatih obustava po mesecu, **zaključana** pri izvozu |
| Ocena zaposlenog | **Već rešeno** — nepromenljiv snimak sa revizijama |

> **[Z] Obrazac za preuzimanje:** ocenjivanje i Potraživanja to rade ispravno —
> nepromenljiv snimak, revizije, revizorski trag.

#### C) Tiho gubljenje podataka

Nekoliko mesta **tiho izostavlja** podatke [Z]:

| Gde | Šta se gubi | Predlog |
|---|---|---|
| Izveštaj goriva po šifri posla | Transakcije bez vozila | Prikazati broj izostavljenih |
| Trošak po kilometru | Vozila sa troškom ≤ 0 | Prikazati sa oznakom ([P-09](#10-poznati-problemi-i-ograničenja)) |
| Obustave mobilnih | Potrošnja bez dodele | Upozorenje ([P-31](#10-poznati-problemi-i-ograničenja)) |
| Virman | Skraćeni nazivi | Greška umesto sečenja ([P-33](#10-poznati-problemi-i-ograničenja)) |
| UF fakture | Prekinute veze | Prebrojati i prijaviti ([P-37](#10-poznati-problemi-i-ograničenja)) |

> **[Z] Dobar uzor:** izveštaj „Gorivo IMS“ za upravu **prebrojava** stavke bez vozila,
> bez šifre posla i bez iznosa. Isti pristup vredi primeniti svuda.

#### D) Paralelnost pozadinskih poslova

Drugi Windows servis vezan samo za red `sync`, a postojeći ograničen na `selenium`
([P-15](#10-poznati-problemi-i-ograničenja)). [Z]

#### E) Upozorenja kojih nema

| Nedostaje | Osnov |
|---|---|
| Dospeo servis po kilometraži | `service_interval` postoji, **ne koristi se** ([Q23](#65-flota--kilometraža-održavanje-presek-stanja-i-izveštaji)) |
| Predmet nabavke zaglavljen bez fakture | ([Q37](#69-nabavka--obračuni-i-analize)) |
| Razlika zbira stavki i vrednosti predmeta | ([Q36](#69-nabavka--obračuni-i-analize)) |
| Ugovor pred istekom | Postoji za polise, ne i za ugovore |

---

### 11.7. Otvorena pitanja koja čekaju odgovor

**45 pitanja** iz celog pregleda. Najvažnija:

| # | Pitanje | Bez odgovora ne može |
|---|---|---|
| **Q1** | DDL nasleđenih pogleda | Dokumentovati 11 izveštaja |
| **Q2** | Ko je odgovoran za koji modul | Potvrditi korisnike u dokumentaciji |
| **Q3** | **Kako rezultati ulaze u knjiženje i koja konta** | Opisati upotrebu rezultata |
| Q5 | Koji mehanizam za centre je merodavan | Rešiti P-19 |
| Q13 | Da li je primećena besmislena prosečna potrošnja | Odlučiti o ispravci P-02 |
| Q18 | Poreklo pragova troška po km | Potvrditi ili izmeniti |
| Q28 | Osnovica obustave mobilnih | ✔ **Potvrđeno ispravnim** |
| Q8 | Poseban broj telefona | ✔ **Potvrđeno kao greška** |
| Q34 | Datum gašenja Naplate | Planirati prelazak |
| Q44 | Kako su nastale tabele Menica | Rešiti P-45 |

Potpun spisak: uz svako poglavlje obračuna i u
[inventaru, poglavlje 14](00-inventar-i-plan-dokumentacije.md).

---

### 11.8. Šta NE treba menjati

> Zabeleženo da se dobra rešenja ne bi slučajno pokvarila. [Z]

| Rešenje | Zašto valja |
|---|---|
| **Prečišćavanje OMV transakcija** | Bez njega su zbirovi višestruko uvećani |
| **Kontrolni zbirovi Finansija i Potraživanja** | Otkrivaju nepotpuno čitanje pre objave |
| **Nepromenljiva ocena sa revizijama** | Uzor za sve što ide u zarade |
| **Objavljeni snimci Potraživanja** | Omogućavaju uvid u ranije stanje |
| **`TrafficCard.for_plate()`** | Namerno odbija da pogađa |
| **Označavanje umesto brisanja** | Nestali zapis se ne gubi |
| **Prazno se razlikuje od nule** | Sprečava pogrešno tumačenje |
| **Izuzimanje zatvaranja u Finansijama** | Namerno i objašnjeno |

---

### 11.9. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Šta je tačno uočeno? | [10. Poznati problemi](#10-poznati-problemi-i-ograničenja) |
| Kako sistem sada radi? | [2. Arhitektura](#2-arhitektura) |
| Kratak pregled za upravu | [Pregled IMS ERP-a](#prilog-a--pregled-za-upravu) |
| Postojeći plan organizacije | [`plan-organizacije-i-dozvola-v2.md`](plan-organizacije-i-dozvola-v2.md) |

---

## 12. Rečnik pojmova i mapiranje naziva

> **Za koga je ovo poglavlje:** za sve.
> Sadrži **objašnjenja pojmova** i **tabelu preslikavanja** naziva sa ekrana u nazive
> u kodu i bazi — jer se često razlikuju.

---

### 12.1. Poslovni pojmovi

#### Organizacija

| Pojam | Značenje |
|---|---|
| **Centar** | Najviši nivo organizacije. U bazi: `OrganizationalUnit.center`, u izvoru `posao.blok`. Određuje **šta korisnik sme da vidi**. |
| **Organizaciona jedinica (OJ)** | Sinonim za **šifru posla** u ovom sistemu. Tabela `fleet_organizationalunit`. |
| **Šifra posla** | Oznaka nosioca troška i prihoda. Isti podatak kao OJ. U izvoru `sif_pos`. |
| **OJ knjiženja** | **Različit pojam!** Organizaciona jedinica upisana na knjiženju (`nalog_z.oj`). **Nije** isto što i centar. |
| **Blok** | Naziv za centar u nasleđenom šifarniku (`posao.blok`). |
| **Profitni posao** | Posao sa oznakom `profitni = 'P'` — učestvuje u raspodeli zajedničkih troškova. |

#### Vozni park

| Pojam | Značenje |
|---|---|
| **Osnov raspolaganja** | Po čemu IMS koristi vozilo: **vlasništvo IMS** ili **korišćenje po ugovoru**. Tabela `fleet_vehicleholding`. |
| **Dodela šifre posla** | Istorijski zapis kojoj OJ vozilo pripada od kog datuma. Tabela `fleet_jobcode`. |
| **Otpis** | Vozilo izuzeto iz upotrebe. Polje `otpis`, puni ga sinhronizacija — **ne unosi se ručno**. |
| **Kvar (PK)** | Prijava kvara u garaži. Broj `PK-<id>/<godina>`. |
| **GZN** | Zahtev za nabavku iz garaže. Broj `GZN-<id>/<godina>`. |
| **Trebovanje** | Zahtev za materijal iz magacina. |
| **Putni nalog (PN)** | **Dva različita pojma:** *putni nalog vozila* = zaduženje vozila; *putni nalog* = službeno putovanje zaposlenog sa akontacijom. |
| **Zaduženje vozila** | Period u kome zaposleni koristi vozilo, sa početnom i krajnjom kilometražom. |
| **Crvena zona** | Vozilo u koje je uloženo više nego što vredi. |
| **Prag troška po km** | Granica prihvatljivog troška, po klasi mase vozila. |

#### Gorivo

| Pojam | Značenje |
|---|---|
| **Bon (voucher)** | Broj potvrde sa pumpe. Kod OMV-a služi kao „broj fakture“ dok faktura ne stigne. |
| **Odjek računa** | Zaostali nefakturisani red u OMV izvoru, koji ponavlja isto točenje. **Mora se ukloniti.** |
| **AdBlue** | Dodatak za dizel motore. Računa se kao proizvod goriva, ali **ne ulazi** u obračun putnog naloga. |
| **Polumesec** | Prva (dani 1–15) ili druga (16–31) polovina meseca. |

#### Finansije

| Pojam | Značenje |
|---|---|
| **P − R** | Prihod minus rashod, **pre** raspodele zajedničkih troškova. |
| **ZT** | Zajednički trošak raspoređen na posao. |
| **P − R − ZT** | Konačni rezultat posla, **pre poreza na dobit**. |
| **Priliv / odliv** | Obračun novčanog toka po pravilima procedure — **nije promet bankovnog računa**. |
| **Neto gotovina** | Priliv minus odliv. |
| **IF** | Izdata faktura. Konta potraživanja `20400` / `20500`. |
| **ON** | Interna faktura ili nalog. |
| **ZAT** | Vrsta naloga za **zatvaranje godine** — namerno izuzeta iz analitike. |
| **`nalog_z`** | Tabela knjiženja u nasleđenom sistemu. **Postoji dvaput** — udaljeni izvor i lokalna kopija. |
| **Kriterijum (1/2/3)** | Osnovica po kojoj se raspoređuje zajednički trošak. |
| **Koeficijent posla / centra** | Procenat učešća u raspodeli. |

#### Potraživanja

| Pojam | Značenje |
|---|---|
| **Baket** | Starosni razred duga. Sedam razreda: nedospelo, 30, 45, 60, 90, 180, 181+. |
| **Nedospelo (`0.1`)** | Dug koji još nije dospeo — **ali i dug bez unetog datuma dospeća**. |
| **Snimak stanja** | Provereno i objavljeno stanje potraživanja na određeni datum. |
| **Pozicija** | Jedna otvorena stavka duga: partner + dokument + šifra posla + grupa konta. |
| **Grupa konta** | Prva tri znaka konta: `204` domaći kupci, `205` inostrani. |
| **Ino** | Oznaka inostranog partnera. |
| **Opomena / pozivno pismo** | Dokumenti kojima se traži plaćanje. |
| **UPPR** | Unapred pripremljen plan reorganizacije. |

#### Nabavka

| Pojam | Značenje |
|---|---|
| **Predmet nabavke** | Zahtev sa stavkama, od podnošenja do fakture. |
| **ZN / ZU / PLN** | Zahtev za nabavku / za uslugu / predlog za opremu. Sa **G** na kraju = garažni. |
| **EUF** | Elektronska ulazna faktura. |
| **UF** | Ulazna faktura — u sistemu su **stavke** i izvedene **fakture**. |
| **Roba** | Robni promet iz nasleđenog sistema. |
| **Snimak izvora** | Lokalna kopija nasleđenog skupa, sa stabilnim ključem. |
| **Vraćeno** | Oznaka da je faktura vraćena sa šifre posla. |
| **Verzija plana** | Svaki uvoz plana javnih nabavki pravi novu verziju sa razlikama. |

#### Kadrovi

| Pojam | Značenje |
|---|---|
| **Radna lista** | Mesečna evidencija sati po šiframa posla. Sati su **celi brojevi**. |
| **Element radne liste** | Šifra za obračun zarada (`elsif`, `elnaz`), vezana za vrstu primaoca. |
| **Vrsta primaoca** | Kategorija zaposlenog; određuje koje elemente može birati. |
| **Prolazak** | Zapis o prislanjanju kartice na čitač. |
| **Službeni izlazak** | Taster 4 — radno vreme se računa **do 16:00**. |
| **Merilo** | Jedno od šest merila ocenjivanja. |
| **Stimulacija** | Zbir koeficijenata izabranih bodova. |
| **Lični koeficijent (K4)** | **`1 + stimulacija`** — množilac za zaradu. |
| **Revizija ocene** | Ispravka se pravi kao **nova revizija**; izvorna ostaje. |

#### Mobilna telefonija

| Pojam | Značenje |
|---|---|
| **Paket** | Iznos koji plaća poslodavac. |
| **Obustava** | Iznos koji se obustavlja od zarade: `osnovica PDV − neto paketa + parking + NZRD`. |
| **NZRD** | Stavka sa računa operatera koja **ulazi u obustavu**. **[N]** Puno značenje nije potvrđeno. |
| **Osnovica za PDV** | Polje sa računa; **osnov obračuna obustave** — potvrđeno ispravnim. |
| **Dodela** | Koji broj kome pripada u kom mesecu. |

#### Ugovori i menice

| Pojam | Značenje |
|---|---|
| **Aneks** | Izmena ugovora; mora imati glavni ugovor. |
| **Tip vrednosti** | Fiksna, po satu, mesečno, čovek mesec, po jedinici, bez definisane vrednosti. |
| **Izlazna menica** | Menica koju je **IMS izdao** — obaveza IMS-a. |
| **Ulazna menica** | Menica **primljena od partnera** — obezbeđenje za IMS. |
| **Avalista** | Lice koje jemči za menicu. |
| **Jedinica vrednosti** | Kod ulazne menice: `RSD`, `EUR` ili **`PROCENAT`** — u trećem slučaju iznos **nije novčani**. |
| **APR status** | Status privrednog subjekta; aktivan **samo** za tačno `активан`. |

#### Tehnički pojmovi

| Pojam | Značenje |
|---|---|
| **Povezani server** | Udaljeni SQL Server dostupan kroz upit — `PUTGEO-SERVER`, `INFORMATIKA23`, `SERFIN`. |
| **Nasleđeni pogled** | `dbo.*` objekat starog ERP-a koji sistem samo čita. |
| **Draft (nedovršeno)** | Podatak preuzet spolja koji čeka dopunu korisnika. |
| **Snimak (snapshot)** | Lokalna kopija spoljnog skupa po stabilnom ključu. |
| **Stabilni ključ** | Identitet zapisa koji **ne zavisi** od iznosa i opisa. |
| **Kontrolni zbirovi** | Poređenje prenetog sa izvorom **pre** objave. |
| **Zaključavanje poslova** | Sprečava da dva ista posla rade istovremeno. |
| **Preskočen** | Posao nije pokrenut jer prethodni još radi — **nije greška**. |

---

### 12.2. Naziv na ekranu ↔ u kodu ↔ u bazi

> Najčešći uzrok nesporazuma. [P]

#### Vozni park

| Na ekranu | U kodu | U bazi |
|---|---|---|
| Vozilo | `Vehicle` | `fleet_vehicle` |
| Broj šasije | `chassis_number` | isto |
| Inventarski broj | `inventory_number` | isto |
| Knjigovodstvena vrednost | `value` | isto |
| Nabavna vrednost | `purchase_value` | isto |
| Otpis | `otpis` | isto |
| Saobraćajna dozvola | `TrafficCard` | `fleet_trafficcard` |
| Registracioni broj | `registration_number` | isto |
| Šifra posla (dodela) | `JobCode` | `fleet_jobcode` |
| Osnov raspolaganja | `VehicleHolding` | `fleet_vehicleholding` |
| Lizing / najam | `Lease` | `fleet_lease` |
| Polisa | `Policy` | `fleet_policy` |
| Osiguranje (knjiženje) | `Insurance` | `fleet_insurance` |
| Potrošnja goriva | `FuelConsumption` | `fleet_fuelconsumption` |
| Kvar | `Kvar` | `fleet_kvar` |
| Trebovanje | `Requisition` | `fleet_requisition` |
| Putni nalog (zaposleni) | `PutniNalog` | `fleet_putninalog` |
| Putni nalog vozila | `VehicleTravelOrder` | `fleet_vehicletravelorder` |
| Troškovi idu na teret | `job_code` | `job_code_id` |
| Isplaćeno | `isplaceno` | isto |

#### Kadrovi — **pažnja na prefiks**

| Na ekranu | U kodu | U bazi |
|---|---|---|
| **Zaposleni** | `hr.models.Employee` | **`fleet_employee`** |
| **CV stavka** | `EmployeeCVItem` | **`fleet_employeecvitem`** |
| Radna lista | `WorkTimeSheet` | `hr_worktimesheet` |
| Red radne liste | `WorkTimeSheetLine` | `hr_worktimesheetline` |
| Partija | `account_number` | isto |
| Opština boravka | `residence_municipality` | isto |
| Šifra zaposlenog | `employee_code` | isto |
| Vrsta primaoca | `RecipientType` | `hr_recipienttype` |
| Bolovanje | `SickLeave` | `hr_sickleave` |
| Ocena | `EmployeeEvaluation` | `hr_employeeevaluation` |
| Stimulacija | `stimulation` | isto |
| Lični koeficijent | `personal_coefficient` | isto |

#### Administracija — **pažnja na prefiks**

| Na ekranu | U kodu | U bazi |
|---|---|---|
| **Korisnik** | `core.models.CustomUser` | **`fleet_customuser`** |
| **Uloga** | `Role` | **`fleet_role`** |
| **Dozvola** | `PermissionCode` | **`fleet_permissioncode`** |
| **Organizaciona jedinica** | `OrganizationalUnit` | **`fleet_organizationalunit`** |
| **Evidencija rada** | `ActivityLog` | **`fleet_activity_log`** |
| **Istorija zadataka** | `TaskHistory` | **`fleet_task_history`** |

#### Finansije

| Na ekranu | U kodu | U izvoru |
|---|---|---|
| Knjiženje | `LedgerEntry` | `nalog_z` |
| Datum knjiženja | `booking_date` | `dat_naloga` |
| Datum dokumenta | `document_date` | `datum` |
| Vrsta naloga | `journal_type` | `sif_vrs` |
| Broj naloga | `journal_number` | `br_naloga` |
| Stavka | `line_number` | `stavka` |
| Konto | `account` | `knt` |
| Duguje / potražuje | `debit` / `credit` | `duguje` / `potrazuje` |
| Šifra posla | `job_code` | `sif_pos` |
| Centar | `center` | `posao.blok` |
| OJ knjiženja | `organizational_unit` | `oj` |
| Veza dokumenta | `document_reference` | `vez_dok` |
| Dospeće | `due_date` | `dpo` |

#### Potraživanja

| Na ekranu | U kodu | U bazi |
|---|---|---|
| Partner | `FinancePartnerIdentity` | `potrazivanja_financepartneridentity` |
| Faktura | `InvoiceDocument` | `potrazivanja_invoicedocument` |
| Knjiženje | `ReceivablePosting` | `potrazivanja_receivableposting` |
| Snimak stanja | `BalanceSnapshot` | `potrazivanja_balancesnapshot` |
| Pozicija | `ReceivablePosition` | `potrazivanja_receivableposition` |
| Baket | `bucket()` | `resolution_details.bucket` |
| Opomena | `CollectionNotice` | `potrazivanja_collectionnotice` |
| Pravni postupak | `CollectionLegalCase` | `potrazivanja_collectionlegalcase` |

#### Nabavka i Ugovori

| Na ekranu | U kodu | U bazi |
|---|---|---|
| Predmet nabavke | `ProcurementCase` | `nabavka_procurement_case` |
| Stavka | `ProcurementItem` | `nabavka_procurement_item` |
| EUF faktura | `ProcurementInvoice` | `nabavka_invoice` |
| UF stavka | `EufItemSnapshot` | `nabavka_euf_item_snapshot` |
| UF faktura | `UfInvoiceSnapshot` | `nabavka_uf_invoice_snapshot` |
| Roba | `GoodsSnapshot` | `nabavka_goods_snapshot` |
| Narudžbenica | `PurchaseOrder` | `nabavka_purchase_order` |
| Partner | `Partner` | `ugovori_partner` |
| Ugovor | `Contract` | `ugovori_contract` |
| Garancija | `ContractGuarantee` | `ugovori_contract_guarantee` |
| **Menica** | `Menica` | **`menica`** *(bez prefiksa)* |
| **Ulazna menica** | `UlaznaMenica` | **`ulazna_menica`** *(bez prefiksa)* |

---

### 12.3. Skraćenice

| Skraćenica | Značenje |
|---|---|
| **OJ** | Organizaciona jedinica |
| **ZT** | Zajednički trošak |
| **P / R** | Prihod / rashod |
| **IF / ON / ZAT / NT** | Vrste naloga |
| **EUF / UF** | Elektronska ulazna faktura / ulazna faktura |
| **ZN / ZU / PLN / ZNG / ZUG** | Vrste predmeta nabavke |
| **GZN** | Garažni zahtev za nabavku |
| **PK** | Prijava kvara |
| **PN** | Putni nalog |
| **AO** | Autoodgovornost |
| **JMBG / MB / PIB** | Matični broj građana / matični broj / poreski identifikacioni broj |
| **RFZO** | Republički fond za zdravstveno osiguranje |
| **APR** | Agencija za privredne registre |
| **NBS** | Narodna banka Srbije |
| **SEF** | Sistem elektronskih faktura |
| **UPPR** | Unapred pripremljen plan reorganizacije |
| **ZJN** | Zakon o javnim nabavkama |
| **CPV / NSTJ** | Šifarnici u planu javnih nabavki |
| **NZRD** | Stavka računa operatera — **[N]** značenje nije potvrđeno |

---

### 12.4. Pojmovi koje treba razlikovati

> Najčešći uzrok pogrešnog tumačenja. [Z]

| Slično zvuči | Ali nije isto |
|---|---|
| **Centar** naspram **OJ knjiženja** | Centar je iz šifarnika posla; OJ knjiženja je polje na knjiženju |
| **Datum knjiženja** naspram **datuma dokumenta** | Prihodi po prvom, fakture po drugom |
| **Putni nalog** naspram **putnog naloga vozila** | Službeno putovanje naspram zaduženja vozila |
| **P − R** naspram **P − R − ZT** | Pre i posle raspodele zajedničkih troškova |
| **Priliv** naspram **naplate** | Priliv je obračun po pravilima, ne evidencija uplata |
| **Neto gotovina** naspram **stanja na računu** | Obračunska veličina, ne stanje |
| **Bruto** naspram **neto** iznosa goriva | Sa PDV-om i bez njega |
| **`nalog_z` udaljeni** naspram **lokalnog** | Finansije čitaju udaljeni; procedura puni lokalni |
| **„Nedospelo“** naspram **„nepoznato dospeće“** | U istom baketu, iako su različite stvari |
| **„Opomena“** (status vozila) | Znači **nema podatka o kilometraži**, ne da je vozilo problematično |
| **„Preskočen“** (posao) | Prethodni još radi — **nije greška** |
| **Prazno** naspram **nule** | „Nema podatka“ naspram „iznos je nula“ |

---

### 12.5. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Šta radi pojedini modul? | [3. Moduli](#3-moduli--sadržaj-i-veze) |
| Koje tabele postoje? | [4. Baza podataka](#4-baza-podataka) |
| Kako se računa iznos? | [6. Analize i obračuni](#6-analize-i-obračuni--sadržaj) |

---

## Prilog A — Pregled za upravu

**Datum:** 18.09.2026.
**Obuhvat:** stanje sistema utvrđeno pregledom izvornog koda i baze podataka

---

### 1. Šta je IMS ERP

IMS ERP je **interna aplikacija Instituta IMS** koja na jednom mestu objedinjuje
evidencije i analize iz deset poslovnih oblasti. Zaposleni joj pristupaju pregledačem,
sa jednom prijavom, a svako vidi samo ono za šta ima ovlašćenje.

Sistem je nastao postepeno, iz potrebe da se podaci koji su ranije vođeni u
**Excel tabelama i papirnim evidencijama** objedine i povežu sa postojećim
knjigovodstvenim sistemom.

#### Šta sistem radi

1. **Vodi evidencije** kojih ranije nije bilo — vozni park, garaža, ugovori, menice,
   mobilni telefoni, ocenjivanje zaposlenih.
2. **Preuzima podatke** iz postojećih sistema i sa portala dobavljača, automatski,
   svake noći.
3. **Računa i prikazuje** rezultate poslovanja, troškove i dugovanja.
4. **Kontroliše** ispravnost podataka i upozorava na ono što traži radnju.

#### Šta sistem ne radi

| Ne radi | Ko to radi |
|---|---|
| Ne knjiži | Postojeći knjigovodstveni sistem |
| Ne obračunava zarade | Postojeći sistem za zarade |
| Ne izdaje fakture | Postojeći poslovni sistem |
| Ne vodi magacin | Postojeći poslovni sistem |

**IMS ERP pre svega čita, povezuje, kontroliše i analizira** podatke koji nastaju drugde.

---

### 2. Šta je realizovano

#### Deset modula u radu

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

#### Sistem u brojkama

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

### 3. Koje poslove aplikacija podržava

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

### 4. Šta se automatizovalo

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

### 5. Šta aplikacija računa

Sistem izvodi **74 obračuna**. Najvažniji, po poslovnom značaju:

#### Za upravu i rukovodioce

| Obračun | Odgovara na pitanje |
|---|---|
| **Rezultat po šifri posla i centru** | Koliko je koji posao zaradio ili izgubio |
| **Zajednički troškovi** | Koliko opštih troškova pada na koji posao |
| **Tok gotovine** | Koliko je novca ušlo i izašlo |
| **Trošak po kilometru** | Koliko stvarno košta svako vozilo |
| **Ocena isplativosti vozila** | Koja vozila više ne isplati zadržavati |
| **Presek stanja flote** | Koliko vozila imamo, gde su, koliko vrede, šta traži radnju |
| **Starosna struktura dugovanja** | Ko duguje i koliko dugo |

#### Za obračun zarada

| Obračun | Šta daje |
|---|---|
| **Lični koeficijent** | Množilac za zaradu, iz mesečne ocene sa tri potpisa |
| **Obustave za mobilne telefone** | Iznos koji zaposleni plaća iznad paketa |
| **Radna lista** | Sati po šiframa posla |

#### Za operativu

Prosečna potrošnja goriva, gorivo po šifri posla, mesečni troškovi polisa, lizinga i
servisa, kilometraža vozila, evidencija održavanja, i **20 izveštaja Flote**.

---

### 6. Ko koristi sistem

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

### 7. Veza sa drugim sistemima

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

### 8. Kontrole i sledljivost

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

### 9. Šta je Institut dobio

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

### 10. Trenutna ograničenja

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

### 11. Utvrđeni rizici

Pregledom je utvrđeno **45 stavki** koje treba rešiti. Ovde su navedene samo one sa
poslovnim uticajem.

#### Rizici koji daju pogrešan broj

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

#### Rizici u vezi sa tragom i bezbednošću

| # | Šta je utvrđeno | Posledica |
|---|---|---|
| 6 | **Lozinke baze podataka nalaze se u projektnoj dokumentaciji koda** | Svako ko ima pristup kodu ima pristup i podacima |
| 7 | **Iznos obustave za mobilne se nigde ne čuva** | Ne postoji odgovor na pitanje koji je iznos prosleđen u zarade |
| 8 | **Sadržaj naloga poslatog banci se ne čuva** | Kod neslaganja sa izvodom nema dokaza šta je poslato |
| 9 | **Jedno poslovno pravilo upisano je u kod** umesto u evidenciju | Potvrđeno kao greška; izmena traži programera |

#### Rizici u vezi sa doslednošću

| # | Šta je utvrđeno | Posledica |
|---|---|---|
| 10 | **Promena centra menja i prošle izveštaje** | Izveštaj za prošlu godinu može se promeniti bez ijedne izmene u knjiženjima |
| 11 | **Dva različita obračuna radnih sati** iz iste evidencije prolazaka | Zaposleni i pregled prisustva mogu pokazati različit broj sati |
| 12 | **Formule 11 izveštaja postoje samo u bazi** | Rezultat se može promeniti bez traga u sistemu |

---

### 12. Preporuke

#### Odmah

| # | Preporuka | Zašto |
|---|---|---|
| 1 | **Ispraviti pet obračuna koji daju pogrešan broj** | Rešenje već postoji u sistemu; zahvat je mali, a uticaj velik |
| 2 | **Premestiti lozinke iz koda** i isključiti razvojni režim | Bezbednost podataka |
| 3 | **Preuzeti i sačuvati definicije 11 izveštaja iz baze** | Dogovoreno; bez toga se ne može objasniti odakle iznos |

#### U narednom periodu

| # | Preporuka | Zašto |
|---|---|---|
| 4 | **Sačuvati ono što se šalje** — nalog banci i obustave | Da postoji dokaz šta je i kada prosleđeno |
| 5 | **Preseliti poslovna pravila iz koda u evidencije** | Da ih menja služba, a ne programer |
| 6 | **Sprovesti planiranu centralizaciju organizacije i ovlašćenja** | Rešava četiri utvrđena problema odjednom |
| 7 | **Odrediti datum gašenja starog sistema naplate** | Dva sistema uporedo su trošak i rizik |

#### Trajno

| # | Preporuka | Zašto |
|---|---|---|
| 8 | **Odrediti vlasnika svakog podatka** — ko odobrava izmene u bazi | Izmena pogleda danas menja izveštaje bez traga |
| 9 | **Potvrditi kako rezultati ulaze u knjiženje** | Nije zabeleženo ni u jednom dokumentu |
| 10 | **Odrediti odgovorne osobe po modulima** | Da se zna kome se obratiti |

---

### 13. Zaključak

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

### Prilozi

| Dokument | Za koga |
|---|---|
| [Pregled sistema](#1-pregled-sistema) | Svi |
| [Moduli](#3-moduli--sadržaj-i-veze) | Poslovni korisnici |
| [Poslovni procesi](#5-poslovni-procesi) | Poslovni korisnici |
| [Analize i obračuni](#6-analize-i-obračuni--sadržaj) | Svi — kako se svaki iznos računa |
| [Registar problema](#10-poznati-problemi-i-ograničenja) | Programeri i uprava |
| [Plan razvoja](#11-plan-razvoja) | Uprava |
| [Rečnik pojmova](#12-rečnik-pojmova-i-mapiranje-naziva) | Svi |

---

## Prilog B — DDL nasleđenih SQL pogleda

Ovde se čuvaju **stvarne definicije pogleda iz baze** — formule koje aplikacija samo
izvršava i prikazuje, a koje se ne vide nigde u Python kodu.

> Status tvrdnji: **[P]** pročitano iz priloženog SQL-a, **[Z]** zaključeno, **[N]** nepotvrđeno.
>
> Sve što piše niže **pročitano je iz samih definicija u ovom direktorijumu**. Namena
> rezultata i način knjiženja **nisu** pretpostavljani.

Ovo je odgovor na problem
[P-27](#p-27--formule-11-izveštaja-nisu-u-projektu) —
„formule 11 izveštaja nisu u projektu“.

> **21.09.2026. — preuzeto iz produkcione baze.** Definicije su pročitane iz
> `sys.sql_modules` i snimljene ovde. Time su **dve ranije ograde ovog dokumenta
> razrešene** (vidi „Šta je provera u bazi pokazala“), a više tvrdnji koje su bile
> **[N] nepotvrđene** postalo je **[P] potvrđeno**.

---

### Šta je gde

| Datoteka | Sadrži | Odakle je |
|---|---|---|
| `naplata-pogledi.sql` | **7 pogleda Naplate** | Ranije `naplata.txt` u korenu projekta |
| `fleet_trebovanja.sql` | `CREATE view [dbo].[fleet_trebovanja]` | Ranije `izvestaji/procena_fleet_trebovanja_20260911.sql` |
| `nbv_roba.sql` | `CREATE view [dbo].[nbv_roba]` | Ranije `izvestaji/procena_nbv_roba_20260911.sql` |
| `naplata-baza.sql`, `naplata-ispravke.sql`, `naplata-v_duplikati.sql`, `naplata-v_if.sql`, `naplata-v_neodobreneif.sql` | **Prave definicije 5 pogleda Naplate** | Produkciona baza, `sys.sql_modules`, 21.09.2026. |
| `fleet_tro_svi.sql`, `fleet_tro_goriva_m.sql`, `fleet_tro_pracenje.sql`, `fleet_tro_taho.sql`, `fleet_tro_parking.sql`, `fleet_dobavljaci.sql`, `fleet_magacin_rez.sql`, `fleet_otpis.sql` | **8 pogleda izveštaja Flote** | Produkciona baza, 21.09.2026. |
| `v_neodobreneIF.sql` | `dbo.v_neodobreneIF` | Produkciona baza, 21.09.2026. |

> **Kada dve datoteke opisuju isti pogled, merodavna je ona preuzeta iz baze**
> (`naplata-*.sql`), a ne ispis u `naplata-pogledi.sql`. Razlog je niže.

---

### Šta je provera u bazi pokazala (21.09.2026.)

#### 1. Sumnja na `v_duplikati` bila je opravdana [P]

Ispis u `naplata-pogledi.sql` dao je `ispravke` i `v_duplikati` **doslovno isti tekst**.
U bazi **nisu isti**: `ispravke` ima 2.157 znakova, `v_duplikati` **929**. Ispis je bio
pogrešan ili zastareo.

Prava definicija `v_duplikati` (`naplata-v_duplikati.sql`) **potpuno se razlikuje** od
onoga što je stajalo u ispisu. Ona [P]:

- čita **samo `sif_vrs = 'IF'`**, `sif_par > 0` — dakle izlazne fakture, **ne konta
  ispravki i tužbi** `2048%/2058%/2049%/2059%` kako je ispis tvrdio;
- **nema uslov `Granica304`** ni bilo kakvo ograničenje godine — uzima **sve godine**;
- spaja to sa tabelom **`dbo.duplikati18`** kroz `UNION ALL`;
- grupiše po partneru i vezi dokumenta i zadržava **samo one koji se javljaju u više od
  jedne godine**: `HAVING COUNT(DISTINCT god) > 1`;
- vraća `MAX(dpo)` — **najkasnije** dospeće.

> **[P] Šta je ovde „duplikat“:** ista veza dokumenta kod istog partnera koja se pojavljuje
> u **dve ili više godina**. To je i objašnjenje zašto je pri prenosu u Potraživanja
> `v_duplikati` dao **2.580**, a `ispravke` **2.395** redova — to su dva sasvim različita
> upita, a ne isti upit sa dva rezultata.

Time se ranije upozorenje „**1. `ispravke` i `v_duplikati` imaju doslovno isti tekst**“
**zatvara**: greška je bila u ispisu, ne u bazi. Opis iz ranijeg plana Naplate
(„IF iz svih godina spojen sa `duplikati18`, uz `MAX` dospeća“) bio je **tačan** i sada je
potvrđen na izvoru — prelazi iz [Z] u **[P]**.

#### 2. `v_neodobreneIF` je preuzet — ranije [N] tvrdnje su potvrđene [P]

Definicija je sada u `naplata-v_neodobreneif.sql`. Sve što je ranije stajalo kao
**nepotvrđeno** pokazalo se tačnim:

| Ranija tvrdnja [N] | Stvarno u pogledu [P] |
|---|---|
| datum dokumenta **od 2025.** | `YEAR(datumdok) > 2024` |
| `sif_dok = 50` | `sif_dok = 50` |
| `StatusIz = 20` | `d.StatusIz = 20`, uz komentar `--- ovo pokazuje samo poslate fakture` |
| status različit od `Approved` | `status <> 'Approved…'` |
| prikaz `SUBSTRING(EID,5,20)` nije pouzdan ključ | `SUBSTRING(eid, 5, 20) as faktura` — izvedena kolona, pravi ključ je `EDok.ID` |

> **[P] Poređenje statusa ide sa dopunom razmacima:** u kodu stoji
> `status <> 'Approved' + 45 razmaka`. Radi jer je kolona `char` fiksne dužine, ali je
> **krto** — promena dužine kolone tiho bi obesmislila uslov.

#### 3. `tuzeni` **ne postoji u bazi** [P]

Provera nad `sys.objects` ne vraća nijedan red ni pod jednom šemom. Pogled opisan u
`naplata-pogledi.sql` (i u tabeli razilaženja posle 30. aprila) **danas ne postoji**.
Nepotvrđeno je [N] da li je obrisan, preimenovan ili ga je ispis pogrešno pripisao ovoj
bazi. **Sve što ovaj dokument tvrdi o `tuzeni` odnosi se na ispis, ne na bazu.**

#### 4. `tro_zarade` i `kasko_rate` ne postoje u bazi [P]

Ista provera, isti rezultat — nema ih. Njihovi izveštaji se zato **ne mogu dokumentovati
niti se zna da li rade**.

`naplata-pogledi.sql` **nije izvršiv skript** — to je ispis sadržaja pogleda, sa naslovom
iznad svakog (`view baza`, `view tuzeni`, …), bez `CREATE VIEW` zaglavlja. [P]

#### ⚠ Dve granice ovog ispisa — **obe razrešene 21.09.2026.**

> Odeljak se zadržava da se vidi kako je zaključeno. **Za sadržaj pogleda merodavne su
> datoteke `naplata-*.sql` preuzete iz baze**, ne ono što piše niže.

**1. ~~`ispravke` i `v_duplikati` imaju doslovno isti tekst.~~ Razrešeno — greška ispisa.** [P] Poređenje znak po znak
pokazuje da se dve definicije u ovoj datoteci **ne razlikuju ni u čemu**.

To **ne može biti tačno**: pri prenosu u Potraživanja `ispravke` je dalo **2.395**, a
`v_duplikati` **2.580** redova. Isti upit ne može dati različit broj redova. [Z]

Opis iz ranijeg plana Naplate kaže da `v_duplikati` treba da čita **IF iz svih godina
spojen sa `duplikati18`, uz `MAX` dospeća** — što je sasvim drugačije od onoga što ovde
piše. **Definicija `v_duplikati` u ovoj datoteci je najverovatnije stara ili pogrešno
kopirana i treba je ponovo preuzeti iz baze.** [Z]

**2. ~~Nedostaje osmi pogled — `v_neodobreneIF`.~~ Razrešeno — preuzet iz baze.** [P] Ovde ih je sedam. Aplikacija čita i
`v_neodobreneIF` (ekran „Neodobrene IF“). Njegova pravila poznata su samo posredno, iz
ranijeg plana: datum dokumenta **od 2025.**, `sif_dok=50`, `StatusIz=20` i status različit
od `Approved`. Pravi primarni ključ izvora je **`EDok.ID`**; izvedeni prikaz
`SUBSTRING(EID,5,20)` **nije pouzdan identifikator**. [N]

---

### Pogledi Naplate — šta koji radi

Svi čitaju **nalog_z sa povezanog servera** `[PUTGEO-SERVER].bazaims.dbo`. [P]

#### Zajednički uslov: granica 304

Šest od sedam pogleda počinje istim izrazom [P]:

```sql
WITH Granica AS (
  SELECT DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0) AS PocetakGodine,
         DATEADD(DAY, 119, DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0)) AS Granica304
)
```

`Granica304` je **119. dan tekuće godine**, dakle **30. april** (29. u prestupnoj). [P]

Do tog dana svi pogledi obuhvataju **tekuću i prethodnu** godinu. **Posle tog dana pogledi
se razilaze** [P]:

| Pogled | Posle 30. aprila | Red u datoteci |
|---|---|---|
| **baza** | `god = YEAR(GETDATE())` — **tekuća godina** | 12 |
| **tuzeni** | `god = YEAR(GETDATE()) - 1` — **prethodna godina** | 53 |
| **ispravke** | `god = YEAR(GETDATE()) - 1` — **prethodna godina** | 73 |
| **v_duplikati** | ~~`god = YEAR(GETDATE()) - 1`~~ — **u bazi nema uslov godine uopšte** | 94 |

> **[P] Ovo je potvrđeno poslovno pravilo, ne greška.** Posle roka za zaključenje prethodne
> godine saldo se gleda u tekućoj godini, a **ispravke i utuženja i dalje u prethodnoj**.
> Modul Potraživanja to i beleži odvojeno — `run.scope["baza_years"]` i
> `run.scope["ispravke_years"]`.

> **[Z] Rizik svežine:** procedura `sp_AzurirajNalogZ` posle aprila osvežava **tekuću**
> godinu, a `ispravke` tada čitaju **prethodnu**. Ako se prethodna godina ne osvežava
> zasebno, stara kopija **nije dokaz svežine**. Vidi
> [3.5 Potraživanja](#35-potraživanja).

> **[N] Zašto baš 119 dana:** `DATEADD(DAY, 119, početak godine)` poredi se sa `GETDATE()`
> **sa vremenom**, što nije potpuno isto kao uključivo kalendarski 30. april u svim
> godinama i satima. Tačno ponašanje granice i prestupne godine **nije potvrđeno testom**.

#### Spisak pogleda

| Pogled | Šta bira | Konta | Grupisanje |
|---|---|---|---|
| **baza** | Sve stavke naloga, red po red | `20400%`, `20500%` | Nema — sirove stavke |
| **v_if** | Samo izlazne fakture (`sif_vrs = 'IF'`), od **2025.** naviše, `sif_par > 0` | Sva | Godina, mesec, partner, OJ, šifra posla, veza dokumenta, datum |
| **v_duplikati** | ~~Stavke sa kontima ispravki i tužbi~~ — **netačno, vidi `naplata-v_duplikati.sql`**: izlazne fakture iz **svih godina** + `duplikati18`, samo one u **više od jedne godine** | Sva | Partner, veza dokumenta |
| **ispravke** | Stavke sa kontima ispravki i tužbi | `2048%`, `2058%`, `2049%`, `2059%` | Nema |
| **tuzeni** | Samo `promena = 'O'` — **pogled ne postoji u bazi** | `2048%`, `2058%` | Godina, partner, datum, konto |
| **dodela bucketa** | Saldo po partneru i vezi dokumenta, **razvrstan po starosti** | Iz `baza` | Partner, naziv, veza dokumenta, šifra posla, prve 3 cifre konta, dospeće |
| *(bez naslova)* | Šifarnik partnera sa povezanog servera, `grupa = 1` | — | Nema |

Svi imaju i stalne uslove `sif_pred = 1`, `god < 2100`, `grupa = 1`, a oni koji gledaju
tekuću godinu izuzimaju početno stanje (`sif_vrs <> 'POC'`). [P]

#### Razredi starosti duga — `dodela bucketa`

Ovo je **izvor starosnih razreda** koje preuzima modul Potraživanja. [P]

```sql
CASE WHEN DATEDIFF(DAY, dpo, GETDATE()) BETWEEN   1 AND  30 THEN 30
     WHEN DATEDIFF(DAY, dpo, GETDATE()) BETWEEN  31 AND  45 THEN 45
     WHEN DATEDIFF(DAY, dpo, GETDATE()) BETWEEN  46 AND  60 THEN 60
     WHEN DATEDIFF(DAY, dpo, GETDATE()) BETWEEN  61 AND  90 THEN 90
     WHEN DATEDIFF(DAY, dpo, GETDATE()) BETWEEN  91 AND 180 THEN 180
     WHEN DATEDIFF(DAY, dpo, GETDATE()) >  180              THEN 181
     ELSE 0.1 END AS baket
```

| Oznaka | Značenje |
|---|---|
| `0.1` | **Nedospelo** — ili `dpo` u budućnosti, ili **`dpo` nije poznat** |
| `30`, `45`, `60`, `90`, `180` | Dospelo toliko dana |
| `181` | Dospelo **preko 180 dana** |

> **[P] Zašto je `0.1` važno:** `DATEDIFF` sa `NULL` datumom dospeća vraća `NULL`, pa nijedan
> `WHEN` nije tačan i stavka pada u `ELSE` — dakle **dug bez poznatog dospeća prikazuje se
> kao nedospeo**. To je problem
> [P-35](#p-35--nepoznato-dospeće-prikazuje-se-kao-nedospelo),
> i ovaj DDL ga **potvrđuje na izvoru**.

Dve dodatne oznake u istom pogledu [P]:

| Kolona | Pravilo |
|---|---|
| `kategorija` | `0` ako `DATEDIFF(dpo, danas) <= 0`, inače `1` |
| `ino` | `0` ako konto počinje sa `204`, inače `1` — **domaći vs. inostrani kupci** |

Uzimaju se samo stavke sa **saldom različitim od nule** (`HAVING SUM(dug) - SUM(pot) <> 0`). [P]

#### Kako se izbegava dvostruko brojanje

`dodela bucketa` datum dospeća sastavlja iz dva skupa [P]:

1. `dupli` — sve iz `v_duplikati`;
2. `bez_duplih` — iz `v_if`, **samo ono čega nema u `v_duplikati`**, sa `MIN(dpo)`.

Spajaju se kroz `UNION ALL` i tek se onda povezuju sa `baza`. Poređenje ide uz
`COLLATE Latin1_General_CI_AI`, dakle **bez obzira na velika/mala slova i dijakritike**. [P]

---

### `fleet_trebovanja` — trebovanja Flote

Izvor: `arhiva_dok` spojen sa `trans` i `artikal`, sve sa povezanog servera
`[putgeo-server].[BazaIMS].[dbo]`. [P]

**Uslovi koje pogled postavlja** [P]:

| Uslov | Značenje |
|---|---|
| `a.sif_dok = 40` | Samo jedna vrsta dokumenta |
| `a.god >= 2026` | **Samo od 2026. godine naviše** |
| `sif_mag1 = 14` | Samo jedan magacin |
| `br_dok_pp NOT LIKE 'TREB%'` i `NOT LIKE 'M%'` | Izbacuje dve grupe brojeva dokumenta |
| `a.br_dok_pp IS NOT NULL` | Mora postojati broj dokumenta |

**Šta postaje šta u aplikaciji** [P]:

| Kolona pogleda | Izraz u SQL-u |
|---|---|
| `vrednost_nab` | `t.kol * t.cena` |
| `datum_trebovanja` | `a.dat_dok_pp` |
| `registracija` | `a.br_dok_pp` |
| `napomena` | Uvek prazan tekst |

> **[P] Registarska oznaka je broj dokumenta.** Kolona `registracija` nije zasebno polje —
> to je `br_dok_pp`, broj prateće dokumentacije. Zato filtri izbacuju brojeve koji počinju
> sa `TREB` i `M`: to su dokumenti kod kojih to **nije** registarska oznaka. [Z]

U datoteci je, u komentaru, zadržana i **prethodna verzija pogleda**. Razlike koje se
vide [P]: stara je uzimala `god >= 2024`, samo artikle vrste `REZ` i `GOR`, imala gotovu
kolonu `vrednost_nab` u izvoru, i izbacivala već prenete redove kroz
`left join [dbo].[fleet_requisition] … where tr.sif_pred is null`.

> **[Z] Šta to znači za podatke:** prelaskom na novu verziju **promenjena je i godina od
> koje se čita (2024 → 2026) i skup vrsta artikala**. Poređenje trebovanja preko te
> granice nije uporedivo. **Nepotvrđeno [N]** je da li je promena bila namerna.

Kolona `vrednost_nab` je ista ona koju Flota koristi za trošak trebovanja po vozilu —
videti [V-10](#v-10--neto-trošak-održavanja). [P]

---

### `nbv_roba` — roba za Nabavku

Spaja dva skupa [P]:

| Skup | Izvor | Uslovi |
|---|---|---|
| `trans_data` | `trans` + `artikal` | `sif_dok = 10`, `god >= 2025` |
| `nalog_data` | `nalog_z` + `partneri` | `sif_vrs = 'KA'`, `god > 2024`, `knt IN (43500, 43600)`, `potrazuje > 0` |

Veza je `RIGHT JOIN` sa strane `trans_data`, po `god` i `br_dok`. [P]
Broj dokumenta na strani naloga **ne postoji kao polje** — vadi se iz teksta:
`CAST(SUBSTRING(n.kom, 4, 5) AS INT)`. [P]

> **[P] Dve posledice `RIGHT JOIN`-a i vađenja broja iz teksta:**
>
> 1. Stavka robe ostaje u rezultatu i kada joj **nema odgovarajućeg naloga** — tada su
>    sve kolone naloga (partner, datum, iznos) prazne.
> 2. Ako `n.kom` nema očekivani oblik, `SUBSTRING(n.kom, 4, 5)` daje pogrešan broj ili
>    pada na `CAST`. Veza tada **tiho izostane**.
>
> `sif_vrs` je ograničen na `'KA'`; u izvornom kodu stoji zakomentarisano `'EUF'`, dakle
> EUF fakture su nekada bile obuhvaćene, pa su isključene. **Razlog nije zabeležen [N].**

---

### Šta još nedostaje

Za ovih 11 izveštaja Flote DDL **još nije preuzet iz baze**: `fleet_tro_svi`,
`fleet_tro_goriva_m`, `fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`,
`tro_zarade`, `fleet_dobavljaci`, `fleet_magacin_rez`, `fleet_otpis`, `kasko_rate`. [P]

Dok ne stignu, na pitanje **„odakle ovaj iznos“** za te izveštaje se ne može odgovoriti
iz projekta.
