# 6.1. Finansijska analitika — obračuni

> Deo poglavlja [6. Analize i obračuni](../06-analize-i-obracuni.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Problemi se vode u [Registru problema](../10-poznati-problemi.md).

---

## 6.1.0. Šta ovo poglavlje pokriva

Finansijska analitika je **jedini modul koji je bio detaljno dokumentovan pre ovog posla**.
Ta metodologija (`finansije-metodologija-obracuna.md`, 584 reda u 20 poglavlja) uklonjena je
iz repozitorijuma 18.09.2026., a **njen sadržaj je prenet ovde**. Ovo poglavlje je od tada
**samostalno** — za pitanje „kako je tačno izračunat ovaj iznos“ ne treba nijedan drugi
dokument.

> Izvorna metodologija ostaje u git istoriji:
> `git show 06f60c2:dokumentacija/finansije-metodologija-obracuna.md`

Uz nju postoji i tehničko uputstvo: [`finansije/README.md`](../../../finansije/README.md).

**Šta se ovde opisuje:** ono što aplikacija računa i prikazuje, prema izvornom kodu.
Razdvojeni su knjigovodstveni rezultat, raspodela zajedničkih troškova, obračun novčanih
tokova i povezane evidencije.

> **Svi brojčani primeri u ovom poglavlju su ilustracije formula, ne poslovni podaci
> preduzeća** — osim iznosa izričito označenih kao kontrolni u
> [6.1.17](#6117-kontrolni-postupak). [P]

---

## 6.1.1. Registar obračuna

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

### Oznake u formulama [P]

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

## 6.1.2. Sedam pravila koja objašnjavaju većinu nedoumica

### 1. Prikazani znak nije obračunski znak [P]

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

### 2. Dva različita datuma [P]

| Podatak | Datum |
|---|---|
| Prihodi, rashodi, ZT, konta, grafikoni, knjiženja | **Datum knjiženja** (`dat_naloga`) |
| Fakture IF i interne ON | **Datum dokumenta** (`datum`), uz izabranu izvornu godinu `god` |
| Tokovi 52nt | Datum naloga uz godinu izvora; PDV ima posebno pomeranje |
| Zaposleni iz obračuna | `Zarada.god`, `Zarada.mesec` |
| Vozila i zaduženja | Presek perioda sa istorijom dodela |
| Putni nalozi | Datum putovanja (`travel_date`) |
| Potraživanja | **Poslednji objavljeni snimak** — izabrani mesec ga ne menja |

### 3. Centar nije OJ knjiženja [P]

`posao.blok` (centar posla) i `nalog_z.oj` (OJ knjiženja) su **odvojene dimenzije**.

### 4. Zatvaranja su namerno isključena [P]

Iz prihoda i rashoda izuzimaju se: vrsta naloga **`ZAT`**, konto **`59900`**, konto **`69900`**.

> Zbog toga zbir svih stavki klasa 5 i 6 posle zatvaranja godine **nije nula** u ovom
> prikazu — to nije greška, nego namera.

### 5. Godišnji ZT nije zbir mesečnih [P]

> `Kj = zbir koeficijenata posla za kriterijum j / broj meseci perioda`

Koeficijent je **prosek**, pa godišnji obračun po pravilu procedure 53 daje drugačiji
iznos od zbira dvanaest zasebnih mesečnih obračuna. Isto važi i za tokove.

### 6. Tok gotovine nije promet računa [P]

Priliv i odliv nastaju po pravilima procedure `SPFINizv52nt` — uz zamenu PDV-a, zamenu
obaveza troškovima, zamenu zarada i refundacije. **Nije zbir prometa bankovnog računa** i
**ne povezuje fakturu sa uplatom**. Originalna poslovna procedura se pri prikazu **ne
izvršava**.

### 7. Ekran nije jedan vremenski snimak [P]

Prihodi i rashodi dolaze iz **poslednje uspešne sinhronizacije**, tokovi i koeficijenti se
čitaju **u trenutku otvaranja**, a Potraživanja iz **svog objavljenog snimka**.
Različite godine mogu biti osvežene u različito vreme. **Izabrani period određuje obuhvat,
a ne trenutak osvežavanja izvora.**

---

## 6.1.3. Period, centar i obuhvat pristupa

### Granice perioda [P]

| Pravilo | Ponašanje |
|---|---|
| Granice datuma | **Uključive** |
| Mesečni detalj | Prvi i poslednji dan meseca |
| „Cela godina“ (`month=`) | **01.01–31.12**, uključujući i deo tekuće godine koji još nije protekao |
| **Nedostajući** parametar meseca | Bira **tekući mesec** — nije isto što i prazan parametar |
| Početni Finansijski pregled i zbirni pregled šifara | 01.01. tekuće godine **do današnjeg datuma** |
| Format unosa | `DD.MM.GGGG`; prihvataju se i završna tačka i ISO `YYYY-MM-DD` |

### Filteri tabele Šifre posla [P]

Tabela **Šifre posla** ima **samo** filtere od/do i centar. Raniji URL parametri konto,
šifra, vrsta knjiženja, tačno konto i OJ knjiženja **ne filtriraju** ovu tabelu.

Ona uvek prikazuje **i prihode i rashode** i uključuje dostupne šifre **bez prometa**.
Prikaz šifarnika nije ograničen samo na trenutno aktivne poslove.

Ostali izveštaji i Knjiženja zadržavaju svoje filtere. **Učešća i zbirovi uvek zavise od
primenjenih filtera.**

### Centar nije OJ knjiženja [P]

Centar posla dolazi iz `posao.blok`, OJ knjiženja iz `nalog_z.oj`.

Pri sinhronizaciji se koristi **aktuelni šifarnik poslova**. Promena centra u šifarniku
može posle osvežavanja **pregrupisati ranija knjiženja** — vidi
[P-44](../10-poznati-problemi.md#p-44--promena-centra-pregrupiše-celu-istoriju-finansija).
ZT za posao takođe koristi aktuelni `posao.blok`, uz koeficijente za izabranu godinu.
Lokalni P/R mogu odražavati **starije** stanje centra ako sinhronizacija još nije preuzela
promenu.

### Prava pristupa menjaju i ukupne iznose [P]

Uz `finansije:view_all` korisnik vidi ceo obuhvat firme. Ostali vide **uniju** dozvoljenih
centara i izričito dozvoljenih šifara posla. **Prazan spisak dozvola nije globalan pristup.**

> **[P] Bitno:** ukupni iznosi i procenti računaju se **iz korisniku dostupnog skupa**.
> Zato **dva korisnika sa različitim obuhvatom vide različite ukupne iznose i procente**
> na istom ekranu, za isti period. To nije greška.

Za ZT su osnovice **cele firme** potrebne za pravilnu raspodelu, ali se korisniku vraća
samo rezultat za dostupne poslove. Vozila, zaduženja, zaposleni, putni nalozi i
Potraživanja dodatno poštuju dozvole **svojih** modula.

### Period pri prelasku na detalj [P]

Iz zbirnih prikaza klik otvara detalj za **poslednji mesec izabranog perioda**. Iz tabele
Šifre posla izbor tačno cele kalendarske godine otvara celu godinu. Klik iz pojedinačnog
knjiženja prenosi mesec tog knjiženja.

> **Proizvoljan opseg od više meseci se ne prenosi u detalj.** Zbirna tabela za
> januar–septembar **ne poredi se direktno** sa detaljem otvorenim samo za septembar —
> najpre treba uskladiti periode.

---

## 6.1.4. Odakle Finansije čitaju

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

### Mapiranje polja knjiženja [P]

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

## 6.1.5. Prihodi, rashodi i rezultat bez ZT

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
> [P-43](../10-poznati-problemi.md#p-43--mogući-dvostruki-obuhvat-zajedničkih-troškova).

---

## 6.1.6. Zajednički troškovi i rezultat posle raspodele

### Šta se čita [P]

Iz `posao_mes` uzimaju se firma, godina, šifra posla, mesec, `kriterijum`, `koef`, `koef2`,
`koef3`, `profitni` — **samo redovi sa `aktivan='D'`** za mesece koji ulaze u izabrani
period. Posao mora postojati u izvornom šifarniku.

Koeficijenti centra `koef1/koef2/koef3` čitaju se iz `blokraspodela` za godinu i centar
aktuelnog posla.

> **[P] Šta NIJE osnovica:** polja `posao_mes.prihod`, `trosak` i `iznos`. Procedure 52 i
> 52nt mogu u njih upisati **različite vrste rezultata**, pa se ne koriste.

### Osnovice cele firme [P]

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

### Koeficijent posla i konačna formula [P]

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

### Zašto godišnji ZT nije zbir mesečnih [P]

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

### Nepotpuni meseci i nedostupnost [P]

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

## 6.1.7. Priliv, odliv i neto gotovina

Ovo je obračun po pravilima pripreme **`SPFINizv52nt`**.

> **[P] Nije prost zbir prometa bankovnog računa, niti evidencija koja povezuje svaku
> fakturu sa uplatom.** Originalna poslovna procedura se pri prikazu **ne izvršava** —
> primenjena su njena pravila.

### Ulazni skup i početni izbor [P]

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

### Zamena PDV-a [P]

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

### Zamene obaveza troškovima [P]

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

### Zarade u obračunu toka [P]

**Uklanjaju se:** `45000, 45100, 45200, 45220, 45210, 45310, 45312, 45314`.

**Dodaju se** izvorne stavke na kontima `element.knt_troska` iz baze zarada, **osim `52024`
i `52026`**, uz dodatno konto **`52100`**. Za dodate stavke koristi se **duguje**, dok je
potražuje 0.

Upit šifarnika `element` bira različita konta **bez dodatnog filtera preduzeća**; knjiženja
koja se dodaju i dalje su ograničena na traženu firmu, posao i period.

> **[P]** Ovo pravilo novčanog toka **nije** obračun pojedinačnih zarada zaposlenih niti
> konačan pokazatelj ukupnog troška zarada centra.

### Refundacije [P]

**Uklanjaju se:** `45400, 45410, 45420, 45503, 45600, 22500, 22510, 22520, 23837`.

**Dodaju se** izvorne stavke sa `22500, 22510, 22520, 23837`, sa:

```text
duguje   = 0
potražuje = izvorno potražuje − izvorno duguje
```

Potrebna je postojeća šifra vrste naloga, ali **ne mora biti tip NT**. Negativna
refundacija **umanjuje priliv**.

### Završni izbor i sabiranje [P]

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

### Dostupnost i godišnje razlike [P]

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

### Konta upisana u obračun toka gotovine

Ovo je **opis onoga što kod radi**; problem koji iz toga proizlazi vodi se kao
[P-42](../10-poznati-problemi.md#p-42--konta-i-pravila-toka-gotovine-upisani-su-u-kod).

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

## 6.1.8. Grafikoni, učešća i rangiranje

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

### Redosled i rangiranje [P]

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

## 6.1.9. Fakture IF i interne ON

### Izdate fakture IF [P]

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

### Interne fakture ON [P]

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

## 6.1.10. Struktura rashoda po kontima

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

## 6.1.11. Zaposleni i zarade

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

## 6.1.12. Vozila, zaduženja i putni nalozi

### Vozila na šifri posla [P]

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

### Zaduženja vozila po zaposlenom [P]

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

### Putni nalozi [P]

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

## 6.1.13. Potraživanja na detalju posla

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
[6.8](06-08-potrazivanja.md).

Grupisanje je po **identitetu partnera i porodici konta (`204`/`205`)**. Partner sa domaćim
i inostranim stavkama može imati **dva reda**. Oznaka važnog kupca **ne zavisi od napomena**
i **ne menja iznos**. Link partnera otvara Potraživanja na istom snimku. [P]

Svaka lokalna stavka ulazi u **tačno jedan** od sedam razreda. „Dospelo“ je zbir šest
razreda kašnjenja; „Ukupno“ uključuje i nedospele stavke i stavke bez datuma.

> **[P] Nedostajući datum dospeća zadržava razred `0.1` i nije dokaz da potraživanje nije
> dospelo** — vidi [P-35](../10-poznati-problemi.md#p-35--nepoznato-dospeće-prikazuje-se-kao-nedospelo).

> **[P]** Prikazuje se **poslednji uspešan lokalni snimak**, **bez preseka na kraj izabranog
> meseca**. Prikazani su datum stanja (`as_of_date`) i vreme preuzimanja
> (`source_observed_at`). Bez objavljenog snimka podaci su označeni kao **nedostupni**, a ne
> kao nulti dug.

> **[P] Ukupan dug nije prihod perioda, priliv ni iznos naplaćen u mesecu.** Negativan saldo
> zadržava znak; aplikacija ga **ne preklasifikuje** u avans. **Nije implementirano**
> pouzdano povezivanje „ova IF faktura je naplaćena ovom uplatom“ niti poseban spisak
> plaćenih računa dobavljača.

---

## 6.1.14. Knjiženja, grupisanja i broj redova

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

## 6.1.15. Nule, nedostajući podaci, znakovi i sortiranje

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

### Boje i znakovi [P]

| Znak | Prikaz |
|---|---|
| Pozitivan | Svetlozelena pozadina, taman podebljan tekst, `+` |
| Negativan | Crvena pozadina, beli tekst, `−` |
| Nula | Neutralna siva |

> **[P] Boja znači znak iznosa, ne „dobro“ ili „loše“** — pozitivan dug kupca i pozitivan
> prihod imaju **različito** poslovno značenje.

### Zaokruživanje i sortiranje [P]

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

## 6.1.16. Sinhronizacija, istorija i procedure

### Šta radi preuzimanje [P]

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

### Značenje kolona istorije [P]

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

### Ručno pokretanje i Celery [P]

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

### Odnos prema poslovnim procedurama [P]

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

## 6.1.17. Kontrolni postupak

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

### Brze provere

| Provera | Kako |
|---|---|
| Rezultat reda | `prihod + prikazani rashod + prikazani ZT` |
| Neto gotovina | `prikazani priliv + prikazani odliv` |
| Prihodi/rashodi prema izvoru | Nezavisan upit nad `nalog_z` povezan sa `posao`, uz ista isključenja |
| Potpunost sinhronizacije | Ekran sinhronizacije: brojači i kontrolni zbirovi po godini i kontu |
| Zbirna tabela naspram detalja | **Najpre uskladiti periode** |

### Zabeleženi kontrolni iznosi [P]

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

## 6.1.18. Šta Finansije ne rade

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

## 6.1.19. Problemi iz ovog poglavlja

Nalazi koje postojeća metodologija **nije navodila kao probleme**. Pun opis, posledice i
predlog rešenja su u [registru problema](../10-poznati-problemi.md).

| # | Opis | Ozbiljnost |
|---|---|---|
| [**P-42**](../10-poznati-problemi.md#p-42--konta-i-pravila-toka-gotovine-upisani-su-u-kod) | Preko 40 broja konta i pravila toka gotovine **upisani su u kod**. Izmena kontnog plana traži novu verziju aplikacije, a isto pravilo postoji i u procedurama `SPFINizv52/52nt` — promena na jednom mestu ne odražava se na drugo. | Srednja |
| [**P-43**](../10-poznati-problemi.md#p-43--mogući-dvostruki-obuhvat-zajedničkih-troškova) | Ako se raspodela zajedničkih troškova počne knjižiti na poslove, ista stavka ulazi **i u `R` i u `ZT`**, pa je rezultat `P − R − ZT` dvostruko umanjen. Metodologija je to sama navodila kao stvar koju treba pratiti. | Srednja |
| [**P-44**](../10-poznati-problemi.md#p-44--promena-centra-pregrupiše-celu-istoriju-finansija) | Centar posla se uzima iz **aktuelnog** šifarnika `posao.blok`, bez istorije. Promena centra pregrupiše sva ranija knjiženja pri sledećoj sinhronizaciji. Isti obrazac kao [P-05](../10-poznati-problemi.md#p-05--centar-se-uzima-iz-poslednje-dodele-a-ne-istorijske) u Floti, gde istorijska dodela **postoji**. | Srednja |

---

## 6.1.20. Otvorena pitanja

| # | Pitanje | Izvor |
|---|---|---|
| **Q41** | Da li se raspodela zajedničkih troškova **knjiži** u izvoru na klasu 5? Ako se to uvede, nastao bi dvostruki obuhvat (**P-43**). | Ovaj pregled |
| **Q42** | Da li je potrebna **istorija pripadnosti posla centru**, da izveštaji za prošle periode ostanu nepromenjeni (**P-44**)? | Ovaj pregled |
| **Q43** | Ako se promeni kontni plan ili pravila procedure `52nt`, ko obaveštava da treba izmeniti i kod (**P-42**)? | Ovaj pregled |
| Q3 | Kako se rezultati Finansija koriste u knjiženju i ko ih preuzima? | Opšte |

---

## Mapa izvornog koda

| Oblast | Izvor implementacije |
|---|---|
| Formule P/R, grupisanja, isključenja | [`finansije/services/reports.py`](../../../finansije/services/reports.py) |
| Grafikoni, procenti, rang-liste | [`finansije/services/charts.py`](../../../finansije/services/charts.py) |
| Raspodela ZT | [`finansije/services/shared_costs.py`](../../../finansije/services/shared_costs.py) |
| Tokovi 52nt | [`finansije/services/cash_flow.py`](../../../finansije/services/cash_flow.py) |
| Osam kolona i sabiranje godina | [`finansije/services/job_overview.py`](../../../finansije/services/job_overview.py) |
| IF, `knt3`, dodele i zaduženja | [`finansije/services/job_card.py`](../../../finansije/services/job_card.py) |
| Zaposleni iz obračuna | [`finansije/services/job_people.py`](../../../finansije/services/job_people.py) |
| Kolone detalja, znaci, podnožja, upozorenja | [`finansije/services/job_tables.py`](../../../finansije/services/job_tables.py) |
| Potraživanja po šifri | [`potrazivanja/services/reports.py`](../../../potrazivanja/services/reports.py) |
| Pristup, periodi i rute | [`finansije/access.py`](../../../finansije/access.py), [`forms.py`](../../../finansije/forms.py), [`views.py`](../../../finansije/views.py) |
| Preuzimanje i kontrole izvora | [`finansije/services/source.py`](../../../finansije/services/source.py), [`sync.py`](../../../finansije/services/sync.py) |
| Modeli i identitet stavke | [`finansije/models.py`](../../../finansije/models.py) |
| Celery ulazne tačke i raspored | [`finansije/tasks.py`](../../../finansije/tasks.py), [`sync_celery_periodic_tasks.py`](../../../core/management/commands/sync_celery_periodic_tasks.py) |
| Serversko sortiranje knjiženja/istorije | [`finansije/services/datatables.py`](../../../finansije/services/datatables.py) |
| Numeričko sortiranje, AJAX i tabovi | [`finansije/static/finansije/tables.js`](../../../finansije/static/finansije/tables.js) |
| Brojevi, boje, dugmad, aktivan meni | [`finansije/templatetags/finance.py`](../../../finansije/templatetags/finance.py) |

> **Pri promeni formule, izvora, datuma filtriranja, pravila dostupnosti ili znaka prikaza
> potrebno je ažurirati odgovarajući odeljak ovog poglavlja i odgovarajuće testove.**

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [3.3. Finansije](../moduli/03-03-finansije.md) | Modul iz ugla korisnika — ekrani i uloge |
| [`finansije/README.md`](../../../finansije/README.md) | Tehničko uputstvo i istorija faza |
| [6.8. Potraživanja](06-08-potrazivanja.md) | Tab „Potraživanja“ na detalju posla |
| [4. Baza podataka](../04-baza-podataka.md#46-finansijska-analitika--finansije) | `LedgerEntry` i prateće tabele |
| [Prilog B — DDL nasleđenih pogleda](../../ddl-nasledjenih-pogleda/README.md) | Definicije pogleda Naplate iz baze |
| [10. Poznati problemi](../10-poznati-problemi.md) | Registar problema |
