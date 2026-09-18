# Finansijska analitika — metodologija svih prikazanih podataka

**Stanje implementacije: 18.09.2026.**

Dopuna od 18.09: IF koristi konta potraživanja 20400/20500, a interne ON fakture imaju zaseban prikaz po potvrđenom izboru četiri konta. Ranije izdat Word od 17.09.2026. predstavlja prethodnu verziju metodologije.

Dokument opisuje ono što aplikacija trenutno računa i prikazuje, prema izvornom kodu. Namenjen je korisnicima finansijske analitike i održavanju aplikacije. Razdvaja knjigovodstveni rezultat, raspodelu zajedničkih troškova, obračun novčanih tokova i povezane evidencije.

Primeri sa manjim iznosima u ovom dokumentu su ilustracije formula, a ne poslovni podaci preduzeća. Dokumentovanje ne pokreće sinhronizaciju, obračunske procedure niti menja podatke.

## Sadržaj

1. [Pregled pokazatelja i osnovne formule](#1-pregled-pokazatelja-i-osnovne-formule)
2. [Izvori, preuzimanje i svežina podataka](#2-izvori-preuzimanje-i-svežina-podataka)
3. [Period, centar, šifra posla i obuhvat pristupa](#3-period-centar-šifra-posla-i-obuhvat-pristupa)
4. [Prihodi, rashodi i rezultat bez ZT](#4-prihodi-rashodi-i-rezultat-bez-zt)
5. [Zajednički troškovi i rezultat posle raspodele](#5-zajednički-troškovi-i-rezultat-posle-raspodele)
6. [Priliv, odliv i neto gotovina](#6-priliv-odliv-i-neto-gotovina)
7. [Grafikoni, učešća i rangiranje](#7-grafikoni-učešća-i-rangiranje)
8. [Izdate fakture IF](#8-izdate-fakture-if)
9. [Interne fakture ON](#9-interne-fakture-on)
10. [Struktura rashoda po kontima](#10-struktura-rashoda-po-kontima)
11. [Zaposleni i zarade](#11-zaposleni-i-zarade)
12. [Vozila na šifri posla](#12-vozila-na-šifri-posla)
13. [Zaduženja vozila po zaposlenom](#13-zaduženja-vozila-po-zaposlenom)
14. [Putni nalozi](#14-putni-nalozi)
15. [Naplata i starosna struktura dugovanja](#15-naplata-i-starosna-struktura-dugovanja)
16. [Knjiženja, grupisanja i broj redova](#16-knjiženja-grupisanja-i-broj-redova)
17. [Nule, nedostajući podaci, znakovi i sortiranje](#17-nule-nedostajući-podaci-znakovi-i-sortiranje)
18. [Sinhronizacija, istorija i procedure](#18-sinhronizacija-istorija-i-procedure)
19. [Kontrolni postupak i poznate granice](#19-kontrolni-postupak-i-poznate-granice)
20. [Mapa izvornog koda](#20-mapa-izvornog-koda)

## 1. Pregled pokazatelja i osnovne formule

Oznake u formulama:

- `P` — prihod.
- `R` — rashod kao obračunska veličina; redovan rashod je pozitivan pre promene znaka za prikaz.
- `ZT` — raspoređeni zajednički trošak; redovan trošak je pozitivan pre promene znaka za prikaz.
- `I` — priliv prema obračunu novčanih tokova.
- `O` — odliv kao obračunska veličina; redovan odliv je pozitivan pre promene znaka za prikaz.
- `D` / `C` — izvorno duguje / potražuje.

| Pokazatelj | Obračunska formula | Prikaz u tabeli Šifre posla i detalju |
|---|---|---|
| Prihodi | `P = Σ(C − D)` na klasi 6, uz isključenja iz odeljka 4 | `P` |
| Rashodi | `R = Σ(D − C)` na klasi 5, uz ista isključenja | `−R` |
| Rezultat bez ZT | `P − R` | `P − R` |
| Zajednički troškovi | Raspodela iz odeljka 5 | `−ZT` |
| Rezultat P − R − ZT | `P − R − ZT` | Isti iznos |
| Priliv | Zbir potražuje posle transformacija iz odeljka 6 | `I` |
| Odliv | Zbir duguje posle istih transformacija | `−O` |
| Neto gotovina | `I − O` | Isti iznos |

Pošto su rashodi, ZT i odliv na ekranu već negativni, rezultat se može proveriti sabiranjem prikazanih vrednosti: **prihod + prikazani rashod + prikazani ZT**, odnosno **prikazani priliv + prikazani odliv**. Ne treba još jednom oduzimati već negativan prikazani trošak.

Primer: `P=1.000`, `R=600`, `ZT=80`, `I=700`, `O=650`. Ekran prikazuje `+1.000`, `−600`, rezultat bez ZT `+400`, ZT `−80`, rezultat posle ZT `+320`, priliv `+700`, odliv `−650`, neto gotovinu `+50`.

**Neto rezultat na Finansijskom pregledu i rang-listama znači `P−R`, pre dodatne raspodele ZT i pre poreza na dobit.** Konačni rezultat posle raspodele posebno je označen kao `P−R−ZT` na šifri posla. Nijedan od ta dva rezultata ne znači stanje novca na računu.

## 2. Izvori, preuzimanje i svežina podataka

Podrazumevano preduzeće je `FINANSIJE_COMPANY=1`. Finansijska analitika počinje od 2025. godine.

| Skup podataka | Izvor | Način čitanja |
|---|---|---|
| Knjiženja, prihodi, rashodi, IF, konta, grafikoni | `[PUTGEO-SERVER].[bazaims].dbo.nalog_z` i prateći šifarnici | Sinhronizovano u lokalni `LedgerEntry` |
| Šifre posla, naziv, centar, aktivnost, tip posla | `bazaims.dbo.posao` | Lokalni `FinanceJob`, a deo obračuna čita i izvorni šifarnik |
| Kriterijumi i koeficijenti ZT | `bazaims.dbo.posao_mes`, `blokraspodela`, `posao` | Direktan SELECT pri obračunu |
| Osnovice raspodele ZT | Lokalni `LedgerEntry` | Sinhronizovana knjiženja cele firme |
| Priliv i odliv | Izvorni `nalog_z`, `konto`, `vrsta_naloga`, `tipnal`, `pdv_arhiva`, `posao_mes`; `bazaldims.dbo.element` | Direktni SELECT upiti pri obračunu |
| Zaposleni evidentirani na poslu | `bazaldims.dbo.Zarada`, `PomLD`, `Radnik` | Direktni SELECT upiti |
| Vozila i istorija dodela | Lokalni `Vehicle`, `JobCode`, `TrafficCard`, `OrganizationalUnit` | Postojeća evidencija Flote |
| Lična zaduženja | Lokalni `VehicleTravelOrder` i prethodne dodele | Postojeća evidencija Flote |
| Službena putovanja | Lokalni `PutniNalog` | Postojeća evidencija putnih naloga |
| Dugovanja i starosni razredi | Lokalni objavljeni `BalanceSnapshot` i `ReceivablePosition` | `potrazivanja.services.reports.job_balances` |

Važna posledica: **ceo ekran nije jedan zajednički vremenski snimak svih baza**. Prihodi i rashodi odražavaju poslednju uspešnu sinhronizaciju za odgovarajuće godine; tokovi, koeficijenti i zaposleni mogu biti noviji. Potraživanja koriste svoj poslednji objavljeni snimak sa prikazanim datumom stanja i vremenom preuzimanja. Različite godine mogu biti sinhronizovane u različito vreme. Izabrani period određuje obuhvat, a ne trenutak osvežavanja izvora.

Glavna veza sa izvorom knjiženja:

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

Nazivi se dopunjavaju iz `posao`, `konto`, `ob_jedin` po godini/OJ i `partner` po grupi/šifri partnera. Identitet knjiženja je **firma + godina + vrsta naloga + broj naloga + stavka**.

Iznosi pokazatelja koriste duguje/potražuje u RSD. Aplikacija ovde ne preračunava `deviza` po kursu. Polje `placeno` se preuzima, ali se **ne koristi** za izračunavanje naplaćenog niti priliva.

## 3. Period, centar, šifra posla i obuhvat pristupa

### 3.1. Koji datum odlučuje da li zapis pripada periodu

| Podatak | Datum / period koji se koristi |
|---|---|
| Prihodi, rashodi, ZT osnovice, struktura konta, grafikoni, knjiženja | Datum knjiženja `dat_naloga` |
| IF i interne ON fakture | Datum dokumenta `datum`, uz izabranu izvornu godinu `god` |
| Tokovi 52nt | Datum naloga uz godinu izvora; PDV ima posebno pomeranje iz odeljka 6 |
| Zaposleni iz obračuna | `Zarada.god`, `Zarada.mesec` |
| Vozila | Presek perioda sa istorijom dodela |
| Zaduženja vozila | Presek perioda, dodele i zaduženja |
| Putni nalozi | Datum putovanja `travel_date` |
| Potraživanja | Poslednji objavljeni lokalni snimak; izabrani mesec ga ne menja |

Granice datuma su uključive. Mesečni detalj uzima prvi i poslednji dan meseca. Izbor **Cela godina**, odnosno `month=`, uzima 01.01–31.12, uključujući i deo tekuće godine koji još nije protekao. Nedostajući parametar meseca bira tekući mesec; nije isto što i prazan parametar.

Početni Finansijski pregled i zbirni pregled šifara podrazumevano uzimaju 01.01. tekuće godine do današnjeg datuma. Datumi se unose kao `DD.MM.GGGG`, a prihvaćeni su i završna tačka i ISO format `YYYY-MM-DD`.

Tabela **Šifre posla** ima samo filtere od/do i centar. Raniji URL parametri konto, šifra, vrsta knjiženja, tačno konto i OJ knjiženja ne filtriraju ovu tabelu. Ona uvek prikazuje i prihode i rashode i uključuje dostupne šifre bez prometa. Prikaz šifarnika nije ograničen samo na trenutno aktivne poslove.

Ostali izveštaji i Knjiženja zadržavaju svoje filtre. Učešća i zbirovi uvek zavise od tih primenjenih filtera.

### 3.2. Centar nije isto polje kao OJ knjiženja

Centar posla dolazi iz `posao.blok`. OJ knjiženja dolazi iz `nalog_z.oj`. To su odvojene dimenzije.

Pri sinhronizaciji se koristi **aktuelni šifarnik poslova**. Promena centra u šifarniku može posle osvežavanja pregrupisati ranija knjiženja. Nije implementiran zaseban istorijski šifarnik pripadnosti posla centru po datumima.

ZT za posao takođe koristi aktuelni `posao.blok`, uz koeficijente raspodele za izabranu godinu. Lokalni P/R mogu odražavati starije stanje centra ako sinhronizacija još nije preuzela promenu.

### 3.3. Prava pristupa utiču na vidljiv skup

Uz `finansije:view_all` korisnik vidi ceo obuhvat firme. Ostali korisnici vide uniju dozvoljenih centara i izričito dozvoljenih šifara posla. Prazan spisak dozvola nije globalan pristup.

Ukupni iznosi i procenti na pregledima računaju se iz korisniku dostupnog skupa. Zato dva korisnika sa različitim obuhvatom mogu videti različite ukupne iznose i procente.

Za ZT su osnovice cele firme potrebne za pravilnu raspodelu, ali se korisniku vraća samo rezultat za dostupne poslove. Vozila, zaduženja, zaposleni, putni nalozi i Potraživanja dodatno poštuju dozvole njihovih modula. Bez tih prava nema prikaza njihovih podataka.

### 3.4. Period prilikom prelaska na detalj

Iz zbirnih prikaza klik otvara detalj za **poslednji mesec izabranog perioda**. Iz nove tabele Šifre posla izbor tačno cele kalendarske godine otvara celu godinu. Klik iz pojedinačnog knjiženja prenosi mesec tog knjiženja.

Proizvoljan opseg od više meseci se ne prenosi kao proizvoljan opseg u detalj. Zbog toga se zbirna tabela za januar–septembar ne poredi direktno sa detaljem koji je otvoren samo za septembar: najpre treba uskladiti periode.

## 4. Prihodi, rashodi i rezultat bez ZT

Osnov su aktivna lokalna knjiženja (`LedgerEntry.active=True`) odgovarajuće firme, perioda i vidljivog posla/centra.

```text
P = zbir (potražuje − duguje), kada konto počinje sa 6
R = zbir (duguje − potražuje), kada konto počinje sa 5
Rezultat bez dodatne raspodele ZT = P − R
```

Iz sva tri obračuna isključuju se:

- sva knjiženja vrste `ZAT`;
- konto `59900`;
- konto `69900`.

Ova knjiženja zatvaraju/prenose rezultat i ne treba da ponište redovno poslovanje u analitičkom prikazu. Isključenje je logičko **ILI**: dovoljno je da stavka ispuni bilo koji od tri uslova.

Redovni `ON` nalozi ostaju uključeni. Korekcije na `59120`/`69120` nisu posebno izbačene. Storna i korekcije zadržavaju izvorni znak; ne koristi se apsolutna vrednost.

Ako je `R` negativan zbog korekcija, prikaz `−R` biće pozitivan. To označava smanjenje rashoda. Isto pravilo važi za korekcije ZT i odliva.

Naziv „bez ZT” znači **bez dodatne raspodele ZT koju ova aplikacija računa**. Osnovni `R` već sadrži sve odgovarajuće proknjižene stavke klase 5, uključujući eventualna knjiženja zajedničkih troškova u izvoru. Aplikacija nema zasebno pravilo koje iz klase 5 uklanja ranije proknjiženu raspodelu. To treba proveriti ako se način knjiženja promeni, kako dodatna raspodela ne bi bila duplirana.

## 5. Zajednički troškovi i rezultat posle raspodele

### 5.1. Šta se čita

Iz `posao_mes` uzimaju se firma, godina, šifra posla, mesec, `kriterijum`, `koef`, `koef2`, `koef3`, `profitni`; samo redovi sa `aktivan='D'` za mesece koji ulaze u izabrani period. Posao mora postojati u izvornom šifarniku.

Koeficijenti centra `koef1/koef2/koef3` čitaju se iz `blokraspodela` za godinu i centar aktuelnog posla. Polja `posao_mes.prihod`, `trosak`, `iznos` **nisu osnovica**: procedure 52 i 52nt mogu u njih upisati različite vrste rezultata.

### 5.2. Osnovice cele firme

Za svaki posao i mesec u izabranom intervalu računa se lokalni `P−R`, sa isključenjima iz odeljka 4. Prema mesečnom kriterijumu posla rezultat ulazi u jednu od tri osnovice:

```text
B1 = zbir (P − R) za posao/mesec sa kriterijumom 1
B2 = zbir (P − R) za posao/mesec sa kriterijumom 2
B3 = zbir (P − R) za posao/mesec sa kriterijumom 3
```

To su osnovice **cele firme**, ne samo trenutno prikazanog centra. Posao/mesec bez odgovarajućeg aktivnog pravila ne doprinosi osnovici. Za osnovice se proverava kriterijum, a ne zahteva se da izvorni posao ima `profitni='P'`.

### 5.3. Koeficijent posla i konačna formula

Za ciljni posao koriste se samo njegovi aktivni mesečni redovi sa `profitni='P'`. Neka je `M` broj kalendarskih meseci koje zahvata izabrani period unutar godine:

```text
M = završni_mesec − početni_mesec + 1
Kj = zbir koeficijenata ciljnog posla za kriterijum j / M
Cj = koeficijent centra za kriterijum j
Aj = Bj × Cj / 100 × Kj / 100
ZT = −(A1 + A2 + A3)
Rezultat posle raspodele = P − R − ZT
```

Nedostajući pojedinačni koeficijent tretira se kao nula. Izračunati ZT zaokružuje se na dve decimale metodom `ROUND_HALF_UP`.

Primer: osnovica `B1=−1.000`, centar dobija 40%, posao dobija 25% centra. Alokacija rezultata je `−100`, pa je `ZT=100`. Na ekranu je ZT `−100`, a rezultat posla umanjuje se za 100.

Ako osnovica ima pozitivan rezultat, raspoređeni ZT može biti negativan. Tada je njegov prikaz pozitivan i povećava rezultat posla.

### 5.4. Godina, nepotpuni meseci i nedostajuća pravila

Godišnji ZT je **osnovica godišnjeg perioda × prosečni koeficijent posla**, a ne zbir 12 zasebno izračunatih mesečnih ZT. Primer sa centrom 50%: osnovice januar `−1.000`, februar `−2.000`, koeficijenti posla 20% i 40%. Obračun za oba meseca daje `3.000 × 50% × 30% = 450`; zbir samostalnih meseci je `100 + 400 = 500`. Razlika proizlazi iz periodnog pravila 53.

Za proizvoljne datume osnovica uzima samo knjiženja unutar tih datuma, ali broj meseci i koeficijenti računaju se po zahvaćenim kalendarskim mesecima. Nema proporcionalnog umanjenja koeficijenta po broju dana.

Ako postoji pravilo za 10 od 12 meseci, imenilac ostaje 12. Iznos se prikazuje kao nepotpun, sa upozorenjem/zvezdicom. „Nepotpun” nije isto što i „nula”.

ZT nije dostupan kada nema tačno jedne raspodele centra/godine, kada postoje duplirana pravila posao/mesec, ili kada ciljni posao nema aktivno profitno pravilo. Tada ni rezultat posle ZT nije potvrđen. Direktni rezultat `P−R` može i dalje biti dostupan.

U zbirnoj tabeli period kroz više godina razdvaja se po kalendarskim godinama. Svaka godina ima svoje koeficijente i zaokružen ZT; iznosi se sabiraju. Ako je neka godišnja komponenta nedostupna, ukupan ZT nije prikazan kao poznat iznos.

## 6. Priliv, odliv i neto gotovina

Ovo je obračun po pravilima pripreme `SPFINizv52nt`. **Nije prost zbir prometa bankovnog računa, niti automatska evidencija koja povezuje svaku fakturu sa uplatom.** Originalna poslovna procedura se ne izvršava prilikom prikaza.

### 6.1. Ulazni skup i početni izbor

Čita se izvorni `nalog_z` za firmu, izvornu godinu `god`, datum naloga u intervalu i posao. Stavke se sabiraju po kontu, datumu i vrsti naloga. Prazna ili NULL šifra posla pripisuje se `111111`, prema metodologiji procedure. Kod P/R se prazna šifra ne preimenuje automatski na ovaj način.

Proveravaju se šifarnici konta i vrste naloga. U početni skup ulaze:

1. Nalozi čiji povezani tip `tipnal.sif_tipnal` ima oznaku `NT`, na kontima gde `konto.nt` nije NULL i nije `NT`.
2. Dodatno, nalozi `ON` na sledećim kontima: `61420, 61300, 61520, 52901, 52991, 52610, 52620, 57910, 53011, 61211, 61421, 61521`.

Za oba izbora potrebne su odgovarajuće šifre konta i vrste naloga. Ne primenjuje se automatski filter zatvaranja iz P/R: 52nt ima sopstvena pravila odabira i zamene.

### 6.2. Zamena PDV-a

Iz radnog skupa uklanjaju se redovi na `47900`. Zamenjuje ih obračun iz `pdv_arhiva` za firmu/posao, sa `pdv_nacoporez='S'` i `br_obr<>0`:

```text
PDV = zbir (pdv + pdv8) za tip I
    − zbir (pdv + pdv8) za ostale tipove
```

SQL sabiranje koristi izvorni izraz `pdv+pdv8`; NULL komponenta ne pretvara se pojedinačno u nulu. Ako agregat nema iznos, preuzima se nula.

Izbor PDV obračuna određuje se iz najmanjeg i najvećeg meseca knjiženja `47900` sa `duguje<>0`, unutar traženog intervala, **za celu firmu**:

- donja granica je prvi mesec minus jedan;
- gornja granica je poslednji mesec minus jedan;
- dobijena granica 0 pretvara se u −1;
- ako je prvi mesec 1, uključuje se i `br_obr=12` prethodne godine;
- kada nema utvrđenih meseci, granice se postavljaju na −1, prema postojećem algoritmu.

Primeri za redovne pozitivne brojeve obračuna: uplata u avgustu bira obračun 7; samo januar bira decembar prethodne godine; januar–mart bira januar/februar tekuće i decembar prethodne godine.

Dobijeni PDV dodaje se na `47900` kao duguje, potražuje 0, sa **datumom kraja izabranog perioda**. Negativan PDV ostaje negativan odliv.

### 6.3. Zamene obaveza troškovima

Sledeće operacije primenjuju se redom. Uklanjaju se navedene obaveze iz radnog skupa i dodaju izvorne stavke troškovnog konta iz perioda, sa izvornim duguje i potražuje postavljenim na 0:

| Uklonjena konta | Dodato konto |
|---|---|
| `46520, 48923, 48900, 48903` | `52400` |
| `46510, 48920, 48981` | `52300` |
| `46500, 48921, 48980` | `52200` |
| `46400, 48960` | `52600` |

Dodavanje zamenskih troškova nije ograničeno na naloge tipa NT. Zato takav odliv ne treba automatski tumačiti kao stvarno plaćenu pojedinačnu obavezu u periodu.

### 6.4. Zarade u obračunu toka

Uklanjaju se `45000, 45100, 45200, 45220, 45210, 45310, 45312, 45314`.

Dodaju se izvorne stavke na kontima `element.knt_troska` iz baze zarada, osim `52024` i `52026`, uz dodatno konto `52100`. Za dodate stavke koristi se duguje, dok je potražuje 0. Trenutni upit šifarnika `element` bira različita konta bez dodatnog filtera preduzeća; knjiženja koja se dodaju i dalje su ograničena na traženu firmu, posao i period.

Ovo pravilo novčanog toka nije obračun pojedinačnih zarada zaposlenih niti konačan zaseban pokazatelj ukupnog troška zarada centra.

### 6.5. Refundacije

Iz radnog skupa uklanjaju se `45400, 45410, 45420, 45503, 45600, 22500, 22510, 22520, 23837`.

Zatim se dodaju izvorne stavke sa `22500, 22510, 22520, 23837`, sa:

```text
duguje = 0
potražuje = izvorno potražuje − izvorno duguje
```

Potrebna je postojeća šifra vrste naloga, ali ne mora biti tip NT. Negativna refundacija umanjuje priliv.

### 6.6. Završni izbor i sabiranje

Posle transformacija uklanjaju se svi redovi čiji konto počinje sa `241`, redovi bez konta u šifarniku i redovi čiji mesec datuma nije aktivan za posao u `posao_mes` (`aktivan='D'`).

```text
I = zbir završnog potražuje
O = zbir završnog duguje
Neto gotovina = I − O
```

Priliv i odliv se zasebno zaokružuju na dve decimale sa `ROUND_HALF_UP`, pa se oduzimaju. Na ekranu je odliv `−O`.

Operacije su niz uklanjanja i dodavanja, prema kodu; ne radi se završna deduplikacija po originalnom ključu knjiženja. Dodate troškovne stavke ne znače „sve jedinstvene bankovne transakcije”.

Ilustracija završnog skupa: priliv kupca 900, refundacija 20, odliv dobavljača 300, obračunati PDV 40 i dodati trošak zarada 100 daju `I=920`, `O=440`, neto `480`.

### 6.7. Dostupnost i godišnje razlike

Bez aktivne mesečne evidencije šifre prikazuje se nedostupan podatak. Ako su aktivni samo neki meseci perioda, iznos ima oznaku nepotpunosti. Duplirana mesečna evidencija ne daje pouzdan obračun.

PDV red nosi datum kraja perioda. Ako završni mesec nije aktivan za šifru, taj red otpada pri završnom filtriranju. Zbog ove i drugih periodnih operacija, **obračun cele godine ne mora biti jednak zbiru odvojeno pokrenutih meseci**. To je posebno značajno kod izbora cele tekuće godine sa budućim/neaktivnim mesecima.

Zbirna tabela kroz više godina sabira zasebne godišnje obračune. Nedostupna godina sprečava prikaz ukupnog iznosa kao potpunog. Grupno učitavanje za više šifara koristi istu računsku funkciju kao pojedinačni detalj.

## 7. Grafikoni, učešća i rangiranje

Finansijski pregled prikazuje centre, zatim poslove. Za isti red prikazuje P, R i rezultat `P−R`, bez dodatnog ZT. Prikazani rashod u ovim grafikonima je obračunski `R`, a ne promenjeni znak `−R` iz tabele šifara.

```text
Učešće u prihodima = prihod reda / ukupan prihod dostupnog perioda × 100
Učešće u rashodima = rashod reda / ukupan rashod dostupnog perioda × 100
Učešće u neto rezultatu = rezultat reda / ukupan rezultat dostupnog perioda × 100
```

Ako je imenilac nula, procenat je crtica. Procenat nije učešće prema najvećem redu.

Cela podloga stubića predstavlja 100% odgovarajuće kolone. Popunjenost je `min(abs(procenat), 100)%`. Procenat iznad 100% ostaje ispisan, a na stubiću se pojavljuje oznaka `»`. Boja negativne vrednosti određuje se znakom iznosa, ne samo znakom procenta.

Primer: jedan centar ima rezultat 120, ostali zbirno −20. Ukupno je 100, pa je učešće prvog centra 120%. To samo po sebi nije greška. Ako je ukupan rezultat negativan, znak procenta takođe treba čitati zajedno sa znakom iznosa.

Redovi su poređani po `P−R` opadajuće; kod istog rezultata po šifri. Svi centri su vidljivi, a kod poslova prvih osam redova, uz proširenje ostalih.

Rangiranje daje tri najbolja i tri najgora posla, odnosno po jedan najbolji i najgori centar. Uslov je neprazna šifra i nenulti prihod ili rashod. Poslovi/centri bez šifre ulaze u zbir i grafikone, ali ne u rangiranje stvarnih entiteta. Kod malog broja poslova liste mogu da se preklapaju. „Najgori” znači najmanji rezultat u skupu i ne mora značiti gubitak.

## 8. Izdate fakture IF

Biraju se aktivna, korisniku dostupna lokalna knjiženja tačne šifre posla sa `journal_type='IF'` i tačnim kontima `20400` ili `20500`, prema **datumu dokumenta**, u izabranom mesecu/godini. Izvorna godina knjiženja takođe mora odgovarati izabranoj godini; 2026. nije fiksno upisana u aplikaciju. U bazi se polje konta zove `knt`.

Jedan red tabele definiše kombinacija: godina, broj naloga, veza dokumenta, grupa partnera i šifra partnera. Naziv partnera uzima se agregatom MAX; datum je MIN datuma uključenih stavki, a kod više različitih datuma ispisuje se i poslednji datum iz te grupe.

Kolona iznosa je **zbir duguje − potražuje na navedenim kontima potraživanja**. Ne koristi se klasa 6 i ne dodaje se PDV zasebno: preuzima se proknjižen iznos potraživanja. Kod fakture podeljene na više poslova ovo je samo deo na izabranoj šifri. Storna zadržavaju znak. Neproknjižene fakture nisu obuhvaćene ovim izvorom.

Podnožje je zbir svih takvih iznosa IF dokumenata izabranog perioda, ne samo trenutno vidljive strane ili rezultata tekstualne pretrage. Broj redova predstavlja grupe naloga/dokumenata/partnera; nije garantovano broj jedinstvenih originalnih faktura iz prodajnog sistema.

Iznos IF nije pokazatelj prihoda ili preostalog duga: bira samo IF, bez naknadnih uplata drugih vrsta naloga. Od glavnog prihoda razlikuje se i po kontima, PDV-u u proknjiženom potraživanju, datumu dokumenta naspram knjiženja i drugim vrstama naloga. Tabela ne prikazuje iznos naplaćen po svakoj fakturi.

## 9. Interne fakture ON

Prema pravilu potvrđenom 18.09.2026, zaseban tab prikazuje `sif_vrs='ON'` i tačna konta `61420`, `61421`, `61521`, `64002`. Koristi iste granice datuma dokumenta, izvornu godinu, šifru posla, aktivna lokalna knjiženja i prava kao IF. Grupisanje je godina + broj naloga + veza dokumenta + grupa i šifra partnera.

Iznos je `Σ(potražuje − duguje)` na ova četiri konta. Podnožje sabira ceo izabrani skup. Negativno potražuje ostaje negativan iznos; ne koristi se apsolutna vrednost. Ostala ON knjiženja ne ulaze u ovaj tab. Dodatna pomoćna tabela nije potrebna za potvrđeni izbor.

Prikaz internih faktura ne dodaje njihov zbir još jednom prihodu: odgovarajuća knjiženja već učestvuju u P/R po postojećim pravilima. Tab se učitava preko AJAX-a u pozadini, nezavisno od otvaranja kartice, sa numeričkim i datumskim sortiranjem.

## 10. Struktura rashoda po kontima

U tabu Rashodi detalja posla koristi se `knt3 = prva tri znaka konta`. Biraju se knjiženja klase 5 u periodu prema datumu knjiženja, uz isključenja ZAT/59900/69900.

```text
R_knt3 = zbir (duguje − potražuje) za isti knt3
Prikaz rashoda knt3 = −R_knt3
Učešće knt3 = R_knt3 / ukupan R posla u periodu × 100
```

Ako je ukupan R nula, učešće je crtica. Korekcije mogu dati negativno učešće ili učešće iznad 100%. Broj knjiženja je broj uključenih stavki, a ne broj faktura. Link Knjiženja prenosi posao, isti period, prefiks konta i vrstu rashoda.

Izvor je lokalna kopija `nalog_z`; ne pokreće se zaseban bruto bilans po OJ. Konto se grupiše po šifri posla, a ne automatski po `nalog_z.oj`. Zbirni izveštaj „po kontima” koristi puno konto; to treba razlikovati od knt3 taba. Posebna stavka „Struktura rashoda” uklonjena je iz menija, ali detalj konta ostaje dostupan.

## 11. Zaposleni i zarade

Iz `Zarada` biraju se firma, godina, meseci i tačna šifra posla. Potrebno je:

- da je `dinara` ili `rekol` različito od nule; NULL se u tom uslovu tretira kao nula;
- da postoji odgovarajući `PomLD` za firmu/godinu/mesec/broj obračuna sa `status_obr='Z'`.

Ime se povezuje iz `Radnik` po firmi i `rasif`. Nedostajuće ime ne izbacuje zaposlenog; prikazuje se obaveštenje da ime nije dostupno.

| Kolona / zbir | Pravilo |
|---|---|
| Mesec obračuna | Mesec iz Zarada; za sortiranje prvi dan tog meseca |
| Šifra zaposlenog | `rasif` |
| Ime | MAX skraćenog `Radnik.ranaz` unutar grupe |
| Broj zaključenih obračuna | `COUNT(DISTINCT br_obr)` po zaposlenom i mesecu |
| Ukupan broj zaposlenih u periodu | Broj različitih `rasif` iz rezultata, jednom za ceo period |

Više elemenata zarade ne umnožava zaposlenog. Zaposleni prisutan u šest meseci ima šest mesečnih redova, ali u godišnjem ukupnom broju doprinosi sa jedan. Koriste se svi odgovarajući zaključeni obračuni, ne samo obračun sa najvećim brojem.

Ovo je **evidencija zaposlenih u obračunima na šifri**, a ne dokaz prisustva na radu, obračun punih radnih angažovanja iz sati ili kompletan kadrovski spisak centra.

Dostupnost obračuna proverava se po firmi/godini/mesecu. Ako nema nijednog zaključenog obračuna u periodu, ukupan broj je crtica. Ako postoje zaključeni obračuni, ali nema odgovarajućih zapisa za posao, broj evidentiranih zaposlenih može biti 0. Postojanje bar jednog zaključenog obračuna u mesecu ne potvrđuje da su svi obračuni tog meseca zaključeni; otvoreni `O` posebno su označeni i izuzeti.

**Još nisu izračunati:** istorijski spisak i broj svih zaposlenih centra, njihov ukupan trošak zarada i kompletan spisak stvarnog rada po poslu. Za to su potrebna potvrđena pravila pripadnosti centru i raspodele svih elemenata/doprinosa. `Zarada.dinara` se ne prikazuje kao proizvoljno sabran konačni trošak. Lokalno `Employee.job_code` označava zanimanje, a ne poslovnu šifru posla.

## 12. Vozila na šifri posla

Koristi se istorija `JobCode`: vozilo, poslovna organizaciona jedinica i datum dodele. Dodela važi od svog datuma do **dana pre naredne dodele istog vozila**, uključujući prelazak na drugi posao. Bez naredne dodele tretira se kao otvorena do kraja traženog intervala.

Za svaku dodelu odgovarajućeg posla:

```text
U periodu od = max(početak analize, datum dodele)
U periodu do = min(kraj analize, dan pre naredne dodele)
```

Prikazuje se samo neprazan presek. Vozilo koje se vrati na istu šifru može imati više redova; broj redova zato nije automatski broj različitih automobila.

Registracija je poslednja evidentirana `TrafficCard.registration_number` sa datumom izdavanja do kraja perioda, a ne nužno registracija na prvi dan dodele. Ako takve kartice nema, prikazuje se broj šasije. Naziv je marka + model.

Nije izračunat novčani trošak vozila u ovom tabu. Otvorena dodela opisuje poslednje evidentirano stanje, ne potvrdu da promene koje nisu unete u sistem nisu postojale.

## 13. Zaduženja vozila po zaposlenom

Izvor je `VehicleTravelOrder`, sa postojećim pravilima pristupa toj evidenciji. Zaduženje se povezuje sa poslom preko istorijskih dodela vozila iz prethodnog odeljka.

```text
Na šifri od = max(početak analize, početak dodele, datum zaduženja)
Na šifri do = min(kraj analize, kraj dodele, datum razduženja ako postoji)
```

Prikazuju se samo intervali gde je početak manji ili jednak kraju. Datumi su uključivi. Pošto evidencija koristi datume bez sata, preuzimanje i razduženje istog dana ne razdvajaju se po časovima.

Kolone daju izvorni datum zaduženja, broj `rbz` (ili PN broj ako ga nema), registraciju/šasiju, vozilo, šifru i ime zaposlenog, izvorni datum razduženja, presek na poslu i status.

Status je **trenutno evidentiran**: „Zatvoreno” ako postoji `closed_at`, inače „Otvoreno”. Nije rekonstruisan istorijski status na poslednji dan izabranog meseca. Povratak vozila na posao može dati više redova istog zaduženja. Kilometraža i troškovi ne raspoređuju se proporcionalno danima.

## 14. Putni nalozi

Biraju se `PutniNalog` za tačnu poslovnu šifru, sa datumom putovanja u periodu, bez storniranih naloga. Dodatno važe postojeća prava za centre putnih naloga.

Prikazuju se datum putovanja, broj naloga, zaposleni, mesto, vozilo/prevoz i broj dana. Ako nema povezanog zaposlenog ili vozila, koristi se slobodno uneti naziv iz naloga.

Broj dana je izvorno polje `number_of_days`, a ne preračunat broj dana unutar izabranog meseca. Put koji počne u periodu ulazi sa celim evidentiranim brojem dana; put koji počne pre perioda ne uključuje se samo zato što se nastavio u periodu.

Ovaj tab ne računa dnevnice, avanse, konačan obračun putovanja ili trošak goriva. Evidencija `PutniNalog` razlikuje se od `VehicleTravelOrder`, koji se koristi za lična zaduženja vozila. Ranije provere nisu potvrdile potpunu istoriju službenih putovanja za 2025; prazan spisak nije dokaz da putovanja nije bilo.

## 15. Naplata i starosna struktura dugovanja

Tab se zove „Potraživanja”. Preuzima lokalni objavljeni snimak preko `potrazivanja.services.reports.job_balances`, za tačnu šifru i dozvoljeni obuhvat Potraživanja. Pri otvaranju nema upita prema staroj Naplati niti udaljenim view-ovima. Iznosi su zbirovi `ReceivablePosition.balance` (duguje − potražuje):

| Prikaz | Razred iz datuma dospeća na datum snimka |
|---|---|
| Nedospelo / bez datuma | `0.1`: datum dospeća na dan snimka ili kasnije, ili datum nedostaje |
| Do 30 dana | `30` |
| 31–45 dana | `45` |
| 46–60 dana | `60` |
| 61–90 dana | `90` |
| 91–180 dana | `180` |
| Preko 180 dana | `181` |
| Dospelo | Sve sa `baket != 0.1` |
| Ukupno | Zbir svih saldo vrednosti iz izabranog skupa |

Za dospele stavke broj dana kašnjenja je `snapshot.as_of_date − due_date`. Granice su uključive: 1–30, 31–45, 46–60, 61–90, 91–180 i preko 180 dana. Koristi se ista funkcija razvrstavanja kao u Potraživanjima.

Grupisanje je po identitetu partnera i porodici konta (`204`/`205`), kao u novoj aplikaciji. Partner sa domaćim i inostranim stavkama može imati dva reda. Oznaka važnog kupca više ne zavisi od napomena i ne menja iznos. Link partnera otvara Potraživanja na istom snimku.

Svaka lokalna stavka ulazi u tačno jedan od sedam razreda. Dospelo je zbir šest razreda kašnjenja; Ukupno uključuje i nedospele stavke/stavke bez datuma. Nedostajući datum zadržava ranije pravilo razreda `0.1` i nije dokaz da potraživanje nije dospelo.

**Potraživanja prikazuju poslednji uspešan lokalni snimak**, bez preseka na kraj izabranog meseca. Prikazani su datum stanja (`as_of_date`) i vreme preuzimanja (`source_observed_at`). Bez objavljenog snimka podaci su označeni kao nedostupni, a ne kao nulti dug.

Ukupan dug nije prihod perioda, priliv ili iznos naplaćen u mesecu. Negativan saldo zadržava znak; aplikacija ne preklasifikuje ga automatski u posebnu kategoriju avansa. Nije implementirano pouzdano povezivanje „ova IF faktura je naplaćena ovom uplatom” niti poseban spisak plaćenih računa dobavljača.

## 16. Knjiženja, grupisanja i broj redova

Knjiženja prikazuju datum knjiženja, identitet naloga/stavke, centar, posao, OJ knjiženja, konto, partnera, vezu/opis dokumenta, datum dokumenta i izvorne iznose duguje/potražuje.

Duguje i potražuje u ovoj tabeli zadržavaju izvorni znak; redovan iznos duguje nije automatski obojen/prikazan kao rashod sa minusom. Trošak se određuje formulom prema kontu, a ne samim nazivom strane knjiženja.

Filter „Sva knjiženja” uključuje i zatvaranja, dok P/R pokazatelji i tada primenjuju isključenja. Ukupan promet duguje/potražuje iznad tabele sabira sve stavke koje prolaze izabrane filtere. Zato promet nije nužno jednak prihodu/rashodu.

Grupisani izveštaji koriste iste P/R izraze: centar; šifra posla uz naziv/centar; puno konto uz naziv; kalendarska godina/mesec datuma knjiženja. Broj knjiženja je `COUNT` stavki u grupi, ne broj različitih dokumenata.

Tabela Šifre posla ima 11 kolona: šifra, naziv, centar i osam finansijskih pokazatelja. Početno prikazuje 100 redova. Dugme sa šifrom otvara detalj i njegove evidencije. Nije uveden dodatni zbir nepoznatih ZT/tokova koji bi nedostajuće podatke tretirao kao nulu.

Promena strane ili tekstualna pretraga DataTables tabele ne menja osnovni period obračuna. Zbirovi koji su izračunati za period ostaju zbirovi perioda. Knjiženja i istorija sinhronizacije pretražuju/sortiraju na serveru; ostale finansijske tabele obrađuju preuzet skup u pregledaču.

Excel za zbir šifara koristi iste znakove i iznose osam pokazatelja, napomenu o nedostupnosti/nepotpunosti i link na detalj. Za ostale izveštaje izvoz prati njihov izvorni obračunski prikaz; izvoz Knjiženja čuva izvorno duguje/potražuje. Excel ne predstavlja istorijski arhiviran snimak izvora samo zato što je korisnik izabrao istorijski period.

## 17. Nule, nedostajući podaci, znakovi i sortiranje

| Oznaka | Značenje |
|---|---|
| `0,00` / `0.00` prema lokalizaciji | Izračunat iznos je nula u dostupnom skupu |
| Crtica ili „Nema podataka” | Iznos nije potvrđen/dostupan; nije zamena za nulu |
| Zvezdica uz iznos | Iznos postoji, ali obračun ima nepotpunu mesečnu pokrivenost |
| Upozorenje o godinama | Nema potvrđenog uspešnog preuzimanja za deo intervala |
| Prazna tabela | Nema odgovarajućih dostupnih zapisa; sama po sebi ne dokazuje odsustvo aktivnosti |

U detalju posla finansijski pokazatelji traže uspešnu sinhronizaciju koja pokriva izabranu godinu. U novoj zbirnoj tabeli proveravaju se sve godine intervala; nepoznat deo sprečava da ukupan broj bude predstavljen kao potpun. Stariji opšti pregledi prikazuju dostupne lokalne zbirove uz obaveštenja o nedostajućim godinama, pa upozorenje treba pročitati pre tumačenja iznosa.

Pozitivni iznosi imaju svetlozelenu pozadinu, taman podebljan tekst i „+”; negativni crvenu pozadinu, beli tekst i „−”; nule neutralnu sivu. Boja znači **znak iznosa**, ne uvek „dobro” ili „loše” — pozitivan dug kupca i pozitivan prihod imaju različito poslovno značenje.

Novčana polja čuvaju se kao decimalni iznosi sa dve decimale. Pri uvozu se primenjuje decimalni `quantize(0.01)`; ZT i tokovi na kraju eksplicitno koriste `ROUND_HALF_UP`. Procenti se računaju iz iznosa, a ispisuju na dve decimale. Zbir zaokruženih pojedinačnih procenata zato može biti npr. 99,99% ili 100,01%.

Numeričko sortiranje koristi sirovu vrednost sa znakom, nezavisno od boje, oznake i lokalizovanog teksta. Rastući redosled je npr. `−1.000, −100, −2, 0, 2, 100`; opadajući je obrnut. Nedostajući brojevi ostaju na kraju u oba smera. Datumi se sortiraju po izvornoj datumskoj/ISO vrednosti, a ne po tekstu `DD.MM.GGGG`.

## 18. Sinhronizacija, istorija i procedure

### 18.1. Šta radi preuzimanje

`sync_ledger(year_from, year_to, company)` čita sve stavke izabranih godina. Nema pouzdanog izvornog vremena izmene koje bi omogućilo samo preuzimanje novih redova.

Novi stabilni ključevi se dodaju, izmenjeni sadržaj ažurira, nepromenjeni ostaje isti. Lokalna stavka koja nestane iz preuzetog izvora označava se neaktivnom; ne briše se fizički. Ponovo pojavljen zapis se aktivira pod istim lokalnim ID-em. Šifarnici se osvežavaju u istom postupku.

Pre i posle objave kontrolišu se **broj stavki, zbir duguje i zbir potražuje po godini i kontu**. Nepoklapanje poništava lokalnu objavu. Potpuno prazan izvor ne može automatski deaktivirati postojeći neprazan obuhvat.

Lokalni upis i uspešan zapis istorije su jedna transakcija. SQL Server aplikaciono zaključavanje sprečava paralelne uvoze. Izvorni podaci se čitaju bez `NOLOCK`, ali kontrolni zbirovi nisu garancija jednog transakcijskog snimka udaljene baze; istovremene promene koje zadrže iste kontrolne zbirove mogu ostati za sledeći prolaz.

### 18.2. Značenje kolona istorije

| Kolona | Značenje |
|---|---|
| Početak / završetak | Vreme početka i kraja pokušaja; lokalizovano na vremensku zonu aplikacije |
| Godine | Zatraženi raspon izvornih godina |
| Status | U toku, uspešno ili neuspešno |
| Preuzeto | Broj stavki u uspešno objavljenom preuzetom skupu |
| Novo | Broj novih lokalnih knjiženja |
| Izmenjeno | Broj ažuriranih ili ponovo aktiviranih knjiženja |
| Nepromenjeno | Aktivna knjiženja istog sadržaja |
| Uklonjeno | Ranije aktivne stavke kojih više nema u preuzetom obuhvatu, sada neaktivne |

Za uspešan prolaz važi `preuzeto = novo + izmenjeno + nepromenjeno`. Uklonjeno se ne dodaje preuzetom broju. Promene šifarnika nisu posebne stavke tog brojača. Kod neuspeha ne treba tumačiti početne nulte brojače kao potvrdu praznog izvora; merodavni su status i greška.

### 18.3. Ručno pokretanje i Celery

Dugme u Sinhronizaciji direktno poziva funkciju `sync_ledger`; ne šalje Celery zadatak. I Celery i komandna linija koriste istu funkciju, kontrolu i zaključavanje. Izbor je tekuća godina ili sve godine od 2025.

Registrovane Celery ulazne tačke: `sync_ledger_task`, `sync_current_year`, `sync_all_years`, red `sync`. Predviđen raspored je tekuća godina svakog sata u :20, a sve godine dnevno u 03:50, u vremenskoj zoni projekta. To je definicija rasporeda, a ne tvrdnja da su periodični zadaci na svakom okruženju aktivni; aktivnost se proverava u konfiguraciji Celery Beat-a.

Otvaranje pregleda ne pokreće sinhronizaciju. Uspeh se prijavljuje nakon kontrolnih zbirova. Neuspeh zadržava prethodno uspešno objavljeno stanje.

### 18.4. Odnos prema poslovnim procedurama

Aplikacija može preko Django veze izvršiti SQL proceduru, ali postojeći finansijski prikazi koriste SELECT upite i računsku logiku bez izvršavanja izvornih poslovnih procedura:

| Obračun / procedura | Uloga u sadašnjoj aplikaciji |
|---|---|
| 52/53 | Pravila kriterijuma, centara i prosečnih koeficijenata primenjena u ZT |
| 52nt | Pravila izbora i transformacija primenjena u novčanim tokovima |
| `SPLdKnjizenje` | Nije pokrenuta iz prikaza; složenost raspodele zarada razlog je da se ukupan trošak zarada ne izmisli prostim zbirom |

Ranijim pregledom utvrđeno je da 52 i 52nt upisuju zajednička polja `posao_mes`, a 53 menja koeficijente `posao`. Zato čitanje njihovih sačuvanih rezultata bez poznavanja poslednjeg izvršavanja nije pouzdan izvor za sve pokazatelje. Lokalni izuzetak su sistemske procedure `sp_getapplock`/`sp_releaseapplock` za zaključavanje sinhronizacije; to nisu obračunske procedure izvornog poslovanja.

## 19. Kontrolni postupak i poznate granice

Za proveru konkretnog iznosa pratiti sledeći redosled:

1. Zapisati firmu, tačnu šifru, centar, datume i korisnikov obuhvat pristupa.
2. Proveriti obuhvat poslednjih uspešnih sinhronizacija; ne pretpostaviti da su sve godine jednako sveže.
3. P i R proveriti na odgovarajućim knjiženjima klasa 6 i 5, bez ZAT/59900/69900.
4. Potvrditi da se iznos rashoda na ekranu prikazuje sa suprotnim znakom i proveriti `P−R`.
5. Za ZT proveriti firmine tri osnovice, mesečne kriterijume, centar, tri koeficijenta centra, aktivne profitne koeficijente posla i imenilac M.
6. Za tokove proveriti ceo redosled 52nt, naročito period PDV-a, dodate troškove, refundacije i aktivnost završnog meseca.
7. IF proveriti kao duguje − potražuje na 20400/20500, ON kao potražuje − duguje na četiri potvrđena konta, uz istu izvornu godinu, datum dokumenta i šifru posla.
8. Naplatu tumačiti kao stanje izvora, zaposlene kao evidenciju zaključenih obračuna, a vozila/zaduženja kao intervale.
9. Uskladiti period pri otvaranju detalja. Godišnji ZT i tokove ne proveravati automatski zbirom 12 nezavisnih mesečnih obračuna.

Preostale poslovne stavke su jasno odvojene: istorijski kadrovski spisak centra; potvrđen ukupan trošak zarada centra; istorijski mesečni presek Naplate; povezivanje pojedinačnih faktura sa konkretnim uplatama/isplatama. One nisu nadomeštene nulama ili pretpostavljenim formulama.

Ranije izvršene provere uključuju grupni naspram pojedinačnog obračuna ZT/tokova, kontrolu 52nt računskog dela bez trajnih poslovnih izmena, mesečne/godišnje periode, znakove, prava i nedostajuće podatke. Posle korekcije IF/ON od 18.09.2026. skup `finansije core naplata` prolazi sa 138 testova. Sam dokument nije potvrda nove sinhronizacije ili vizuelne provere svih ekrana.

## 20. Mapa izvornog koda

Putanje su relativne u odnosu na ovaj dokument.

| Oblast | Izvor implementacije |
|---|---|
| Formule P/R, grupisanja, isključenja | [reports.py](../finansije/services/reports.py) |
| Grafikoni, procenti, rang-liste | [charts.py](../finansije/services/charts.py) |
| Raspodela ZT | [shared_costs.py](../finansije/services/shared_costs.py) |
| Tokovi 52nt | [cash_flow.py](../finansije/services/cash_flow.py) |
| Osam kolona i sabiranje godina | [job_overview.py](../finansije/services/job_overview.py) |
| IF, knt3, dodele i zaduženja | [job_card.py](../finansije/services/job_card.py) |
| Zaposleni iz obračuna | [job_people.py](../finansije/services/job_people.py) |
| Kolone detalja, znaci, podnožja i upozorenja | [job_tables.py](../finansije/services/job_tables.py) |
| Potraživanja po šifri | [reports.py](../potrazivanja/services/reports.py) |
| Pristup, periodi i rute | [access.py](../finansije/access.py), [forms.py](../finansije/forms.py), [views.py](../finansije/views.py) |
| Preuzimanje i kontrole izvora | [source.py](../finansije/services/source.py), [sync.py](../finansije/services/sync.py) |
| Modeli finansija i identitet stavke | [models.py](../finansije/models.py) |
| Celery ulazne tačke i definicije rasporeda | [tasks.py](../finansije/tasks.py), [sync_celery_periodic_tasks.py](../core/management/commands/sync_celery_periodic_tasks.py) |
| Serversko sortiranje knjiženja/istorije | [datatables.py](../finansije/services/datatables.py) |
| Numeričko sortiranje, AJAX i tabovi | [tables.js](../finansije/static/finansije/tables.js) |
| Brojevi, boje, dugmad, aktivan meni | [finance.py](../finansije/templatetags/finance.py), [finance.css](../finansije/static/finansije/finance.css) |

Pri promeni formule, izvora, datuma filtriranja, pravila dostupnosti ili znaka prikaza potrebno je ažurirati odgovarajući odeljak ovog dokumenta i odgovarajuće testove.
