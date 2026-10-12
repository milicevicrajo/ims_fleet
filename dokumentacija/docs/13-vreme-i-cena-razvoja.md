# 13. Vreme i cena razvoja

> **Za koga je ovo poglavlje:** uprava.
> Sadrži **koliko je trajao razvoj**, **koliki je obim urađenog posla** i **koliko bi
> koštalo da se isti sistem naruči spolja**.
> Status tvrdnji: **[P]** potvrđeno (izmereno iz koda i git istorije), **[Z]** zaključeno
> (procena na osnovu izmerenog), **[N]** nepotvrđeno (pretpostavka koju treba zameniti
> stvarnim podatkom).
>
> Stanje: **10.10.2026.**

---

## 13.1. Ukratko

| Pitanje | Odgovor |
|---|---|
| Koliko je trajao razvoj? | **26 meseci** — od 19.08.2024. do danas, i dalje traje [P] |
| Ko je razvijao? | **Jedan programer** [P] |
| Koliki je obim? | **≈ 72.500 linija Pythona**, 37.400 linija šablona, 1.430 automatskih testova [P] |
| Koliko bi trajalo sa spoljnim timom? | **15–18 meseci** sa timom od 5 ljudi [Z] |
| Koliko bi koštalo spolja? | **≈ 400.000–700.000 EUR** kod domaće softverske kuće [Z] |
| Koliko je stvarno koštalo? | **≈ 80.000–130.000 EUR** rada jednog programera, zavisno od zarade [Z][N] |

Razlika između poslednja dva reda — **tri do pet puta** — jeste vrednost koju je Institut
dobio razvojem u kući. Objašnjenje je u odeljku 13.6.

---

## 13.2. Vremenska linija

Razvoj je počeo **19.08.2024.** kao aplikacija za vozni park. Do 09.10.2026. napravljeno
je **418 izmena (commit-ova)** u **159 različitih radnih dana**. [P]

| Faza | Period | Trajanje | Izmena | Šta je urađeno |
|---|---|---|---|---|
| **1. Vozni park** | 08/2024 – 08/2025 | 13 meseci | 93 | Vozila, gorivo (NIS, OMV), Kerio, servisi, polise, prvi izveštaji, Naplata |
| **2. Proširenje** | 09/2025 – 04/2026 | 8 meseci | 111 | Kadrovi, trebovanja, putni nalozi, avansi, prelazak na bazu `IMS_ERP` |
| **3. ERP** | 05/2026 – 10/2026 | 5,5 meseci | 214 | Preimenovanje u IMS ERP i preuređenje koda; Ugovori, Menice, Nabavka, Isplate, Mobilni, Finansije, Potraživanja, Organizacija, Pravna služba, Arhiva, Knjiženje; dokumentacija |

**Polovina svih izmena nastala je u poslednjih pet i po meseci.** [P] Tada je sistem od
aplikacije za flotu postao ERP sa dvanaest modula.

Izmene po mesecima (gušće = više rada):

```
2024  08 ▏  3   09 ▍ 13   11 ▏  7   12 ▏  5
2025  01 ▏  6   02 ▋ 22   03 ▍ 17   04 ▏  3   05 ▏  7   06 ▏  3
      07 ▏  7   09 ▏  8   10 ▍ 12   12 ▍ 17
2026  01 ▍ 10   02 ▋ 24   03 ▏  6   04 █ 34   05 ██▌ 75   06 ▍ 15
      07 ▋ 25   08 ▍ 15   09 █▋ 54  10 █ 30 (do 09.10.)
```

---

## 13.3. Šta je napravljeno — obim

| Pokazatelj | Vrednost |
|---|---|
| Python kod aplikacije (bez testova i migracija) | **≈ 72.500 linija** |
| Automatski testovi | **≈ 23.000 linija, 1.430 testova** |
| HTML šabloni (ekrani) | **≈ 37.400 linija** |
| Sopstveni JavaScript i CSS | ≈ 4.800 linija |
| Modeli (tabele) | 156 |
| Rute (ekrani i radnje) | 572 |
| Migracije baze | 220 |
| Celery zadaci (pozadinski i noćni poslovi) | 26 |
| Komande za održavanje | 63 |
| Dokumentacija | ≈ 28.000 linija |
| Spoljni sistemi | 3 povezana SQL servera, NIS i OMV portali, NBS, APR, SEF, Kerio, banka |

Sve vrednosti su izmerene iz repozitorijuma 10.10.2026. [P] Biblioteke trećih strana
(Bootstrap, DataTables i sl.) **nisu uračunate**.

---

## 13.4. Procena napora — koliko rada je sadržano u sistemu

Napor se meri u **čovek-mesecima** (ČM): jedan čovek-mesec je mesec dana punog rada
jednog stručnjaka, oko 160 sati.

### Procena po modulima [Z]

Procena polazi od obima i složenosti svakog modula. Uračunati su analiza, programiranje,
testiranje i puštanje u rad.

| Modul | Python (sa testovima) | Napor | Šta ga čini složenim |
|---|---:|---:|---|
| Vozni park (Flota) | 26.800 | 18 ČM | Selenium preuzimanje goriva, čišćenje OMV duplikata, putni nalozi, ekonomika vozila |
| Kadrovi | 15.300 | 10 ČM | Radne liste iz kontrole pristupa, odmori, bolovanja, ocenjivanje, rešenja |
| Organizacija, dozvole, osnova | 10.400 | 7 ČM | Registar organizacije sa istorijom, uloge po čvoru, prava po registru |
| Finansijska analitika | 9.300 | 8 ČM | Čitanje knjiženja sa povezanih servera, rezultat po poslu i centru, tok gotovine |
| Nabavka | 8.600 | 6 ČM | Zahtevi, fakture, plan javnih nabavki, snimci izvora |
| Potraživanja i Naplata | 5.900 | 4,5 ČM | Starost dugovanja, opomene, sinhronizacija |
| Ugovori | 4.700 | 3,5 ČM | Partneri, ponude, aneksi, garancije, APR |
| Mobilna telefonija | 4.250 | 2,5 ČM | Obustave iz zarada |
| Menice i Pravna služba | 3.850 | 3 ČM | Registar NBS, pravni i disciplinski postupci |
| Isplate i Knjiženje | 3.000 | 3 ČM | Virmani za banku, fiskalni računi |
| Arhiva | 1.600 | 1 ČM | Delovodnik |
| Dokumentacija | — | 3 ČM | 13 poglavlja, obračuni sa kontrolnim primerima |
| **Zbir razvoja** | **≈ 94.000** | **69,5 ČM** | |
| Analiza zahteva, vođenje projekta, uvođenje i obuka (+20 %) | | 14 ČM | Kod spoljnog izvođača ovo je obavezan trošak |
| **Ukupno** | | **≈ 83 ČM** | **≈ 7 čovek-godina** |

Realan raspon je **70–95 ČM**, zavisno od toga koliko je izvođaču poznat posao Instituta.

### Provera drugim metodom [Z]

Klasični model **COCOMO** (osnovni, za timove koji poznaju domen) za 72.500 linija koda
daje **≈ 215 ČM** i rok od 19 meseci. Taj model je baždaren na starije programske jezike i
**precenjuje** napor za Python i Django, gde okvir sam daje prijavu, bazu, administraciju
i obrasce. Zato se uzima samo kao **gornja granica**.

Procena po modulima odgovara učinku od oko **1.100 linija Pythona po čovek-mesecu**
(sa testovima), što je u uobičajenom rasponu za poslovne aplikacije.

---

## 13.5. Cena — da je sistem naručen spolja

### Koliko bi trajalo [Z]

Spoljni tim od **5 ljudi** (dva programera za server, jedan za ekrane, analitičar-tester,
delimično vođa projekta) napravio bi 83 ČM za **15–18 meseci**, računajući i usaglašavanje
zahteva sa službama Instituta.

### Koliko bi koštalo [Z][N]

Cene čovek-meseca su **tržišne pretpostavke** za 2026. godinu, bez PDV-a:

| Izvođač | Cena sata | Cena ČM (160 h) | 83 ČM | Raspon (70–95 ČM) |
|---|---:|---:|---:|---:|
| Interni tim (zaposleni, bruto 2) | — | ≈ 4.000 EUR | **≈ 332.000 EUR** | 280.000–380.000 EUR |
| Domaća softverska kuća | 35–45 EUR | 5.600–7.200 EUR | **≈ 530.000 EUR** | 390.000–685.000 EUR |
| Strani izvođač (EU) | 70–90 EUR | 11.200–14.400 EUR | **≈ 1.060.000 EUR** | 780.000–1.370.000 EUR |

**Preporučena vrednost za upravu: ≈ 400.000–700.000 EUR** — cena kod domaće softverske
kuće, koja bi bila realna alternativa.

Licence se ne plaćaju posebno: Django, Celery, Redis i Selenium su besplatni, a SQL Server
i Windows server Institut već ima. [P]

---

## 13.6. Stvarna cena — razvoj u kući

### Stvarni utrošak [Z][N]

Sistem je razvio **jedan programer za 26 meseci**. Najviše je, dakle, utrošeno
**26 čovek-meseci** — i to samo ako je ceo radni dan bio posvećen ovom sistemu.

| Mesečni trošak programera (bruto 2) | 26 meseci punog rada |
|---:|---:|
| 3.000 EUR | **78.000 EUR** |
| 4.000 EUR | **104.000 EUR** |
| 5.000 EUR | **130.000 EUR** |

> **[N] Ovaj iznos treba potvrditi.** Za tačan broj upisati stvarni bruto 2 iz obračuna
> zarada i udeo radnog vremena koji je stvarno išao na IMS ERP (programer je radio i druge
> poslove). Formula: **meseci × bruto 2 × udeo vremena**.

Pored rada programera postoje i manji troškovi: pretplate na alate za programiranje
i vreme zaposlenih iz službi koji su objašnjavali posao i proveravali rezultate. Ovo
drugo nije mereno, a kod spoljnog izvođača bi bilo **veće**, ne manje.

### Zašto je stvarna cena niža [Z]

| Razlog | Uticaj |
|---|---|
| **Programer je i analitičar** | Nema prenošenja zahteva kroz više ljudi, nema pisanja ugovornih specifikacija |
| **Poznavanje posla iznutra** | Nema perioda upoznavanja sa Institutom, knjigovodstvom i starim ERP-om |
| **Isporuka po delovima** | Svaki modul je ušao u rad čim je bio upotrebljiv, pa su greške u zahtevima otkrivane rano |
| **Django** | Okvir daje gotovu prijavu, bazu, migracije i administraciju |
| **Alati veštačke inteligencije u programiranju** | U poslednjoj fazi ubrzali pisanje koda, testova i dokumentacije — repozitorijum ima i uputstvo za njih ([`AGENTS.md`](../../AGENTS.md)) |

### Odnos

| | Napor | Rok | Cena |
|---|---:|---:|---:|
| Spoljni izvođač (domaći) | 70–95 ČM | 15–18 meseci | 390.000–685.000 EUR |
| Razvoj u kući | ≤ 26 ČM | 26 meseci | 78.000–130.000 EUR |

Razvoj u kući je trajao **duže po kalendaru** (jedan čovek umesto tima), ali je koštao
**tri do pet puta manje**. [Z]

---

## 13.7. Trošak održavanja [Z]

Sistem zavisi od starog ERP-a, tri povezana servera i portala dobavljača — kad se bilo šta
od toga promeni, sistem mora da se prilagodi. Uobičajeno je da održavanje i manja
proširenja godišnje traže **15–20 % vrednosti razvoja**.

| Način | Godišnje |
|---|---:|
| Interni programer, pola do celo radno vreme | ≈ 24.000–48.000 EUR |
| Ugovor o održavanju sa spoljnim izvođačem | ≈ 80.000–120.000 EUR |

**Rizik:** celo znanje o sistemu je kod jednog čoveka. Ova dokumentacija i
[`AGENTS.md`](../../AGENTS.md) postoje da bi taj rizik smanjili, ali ga ne uklanjaju.
Vidi i [Plan razvoja](11-plan-razvoja.md).

---

## 13.8. Ograničenja procene

| Ograničenje | Posledica |
|---|---|
| Sati rada nisu vođeni | Stvarni napor je procenjen iz trajanja, ne izmeren |
| Izmena (commit) nije mera rada | Jedna izmena može biti sat ili nedelja posla; broj služi samo da pokaže ritam |
| Rad pre 19.08.2024. nije u istoriji | Prvobitna analiza i priprema nisu uračunate |
| Cene sata su tržišne pretpostavke | Za ponudu treba tražiti stvarne ponude izvođača |
| Kurs i cene se menjaju | Iznosi važe za 10/2026 |

---

## 13.9. Kako osvežiti brojke

Iz korena projekta, u Git Bash-u:

```bash
# Trajanje i broj izmena
git log --reverse --format=%ad --date=short | head -1     # prva izmena
git rev-list --count HEAD                                 # broj izmena
git log --format=%ad --date=short | sort -u | wc -l       # radnih dana sa izmenama
git log --format=%ad --date=format:%Y-%m | sort | uniq -c # izmene po mesecima

# Obim koda (bez migracija i testova)
git ls-files '*.py' | grep -v migrations | grep -vE '(^|/)tests?(/|\.py|_)' | xargs cat | wc -l
# Testovi
git ls-files '*.py' | xargs grep -hE '^\s+def test_' | wc -l
# Šabloni (bez static/)
git ls-files '*.html' | grep -v static/ | xargs cat | wc -l
```

Posle izmene pokrenuti `python dokumentacija/spoji-dokumentaciju.py`.
