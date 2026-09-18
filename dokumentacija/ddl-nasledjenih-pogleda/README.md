# DDL nasleđenih SQL pogleda

Ovde se čuvaju **stvarne definicije pogleda iz baze** — formule koje aplikacija samo
izvršava i prikazuje, a koje se ne vide nigde u Python kodu.

> Status tvrdnji: **[P]** pročitano iz priloženog SQL-a, **[Z]** zaključeno, **[N]** nepotvrđeno.
>
> Sve što piše niže **pročitano je iz samih definicija u ovom direktorijumu**. Namena
> rezultata i način knjiženja **nisu** pretpostavljani.

Ovo je prvi deo odgovora na problem
[P-27](../docs/10-poznati-problemi.md#p-27--formule-11-izveštaja-nisu-u-projektu) —
„formule 11 izveštaja nisu u projektu“. Ostatak DDL-a tek treba preuzeti iz baze.

---

## Šta je gde

| Datoteka | Sadrži | Odakle je |
|---|---|---|
| `naplata-pogledi.sql` | **7 pogleda Naplate** | Ranije `naplata.txt` u korenu projekta |
| `fleet_trebovanja.sql` | `CREATE view [dbo].[fleet_trebovanja]` | Ranije `izvestaji/procena_fleet_trebovanja_20260911.sql` |
| `nbv_roba.sql` | `CREATE view [dbo].[nbv_roba]` | Ranije `izvestaji/procena_nbv_roba_20260911.sql` |

`naplata-pogledi.sql` **nije izvršiv skript** — to je ispis sadržaja pogleda, sa naslovom
iznad svakog (`view baza`, `view tuzeni`, …), bez `CREATE VIEW` zaglavlja. [P]

### ⚠ Dve granice ovog ispisa

**1. `ispravke` i `v_duplikati` imaju doslovno isti tekst.** [P] Poređenje znak po znak
pokazuje da se dve definicije u ovoj datoteci **ne razlikuju ni u čemu**.

To **ne može biti tačno**: pri prenosu u Potraživanja `ispravke` je dalo **2.395**, a
`v_duplikati` **2.580** redova. Isti upit ne može dati različit broj redova. [Z]

Opis iz ranijeg plana Naplate kaže da `v_duplikati` treba da čita **IF iz svih godina
spojen sa `duplikati18`, uz `MAX` dospeća** — što je sasvim drugačije od onoga što ovde
piše. **Definicija `v_duplikati` u ovoj datoteci je najverovatnije stara ili pogrešno
kopirana i treba je ponovo preuzeti iz baze.** [Z]

**2. Nedostaje osmi pogled — `v_neodobreneIF`.** [P] Ovde ih je sedam. Aplikacija čita i
`v_neodobreneIF` (ekran „Neodobrene IF“). Njegova pravila poznata su samo posredno, iz
ranijeg plana: datum dokumenta **od 2025.**, `sif_dok=50`, `StatusIz=20` i status različit
od `Approved`. Pravi primarni ključ izvora je **`EDok.ID`**; izvedeni prikaz
`SUBSTRING(EID,5,20)` **nije pouzdan identifikator**. [N]

---

## Pogledi Naplate — šta koji radi

Svi čitaju **nalog_z sa povezanog servera** `[PUTGEO-SERVER].bazaims.dbo`. [P]

### Zajednički uslov: granica 304

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
| **v_duplikati** | `god = YEAR(GETDATE()) - 1` — **prethodna godina** | 94 |

> **[P] Ovo je potvrđeno poslovno pravilo, ne greška.** Posle roka za zaključenje prethodne
> godine saldo se gleda u tekućoj godini, a **ispravke i utuženja i dalje u prethodnoj**.
> Modul Potraživanja to i beleži odvojeno — `run.scope["baza_years"]` i
> `run.scope["ispravke_years"]`.

> **[Z] Rizik svežine:** procedura `sp_AzurirajNalogZ` posle aprila osvežava **tekuću**
> godinu, a `ispravke` tada čitaju **prethodnu**. Ako se prethodna godina ne osvežava
> zasebno, stara kopija **nije dokaz svežine**. Vidi
> [3.5 Potraživanja](../docs/moduli/03-05-potrazivanja.md).

> **[N] Zašto baš 119 dana:** `DATEADD(DAY, 119, početak godine)` poredi se sa `GETDATE()`
> **sa vremenom**, što nije potpuno isto kao uključivo kalendarski 30. april u svim
> godinama i satima. Tačno ponašanje granice i prestupne godine **nije potvrđeno testom**.

### Spisak pogleda

| Pogled | Šta bira | Konta | Grupisanje |
|---|---|---|---|
| **baza** | Sve stavke naloga, red po red | `20400%`, `20500%` | Nema — sirove stavke |
| **v_if** | Samo izlazne fakture (`sif_vrs = 'IF'`), od **2025.** naviše, `sif_par > 0` | Sva | Godina, mesec, partner, OJ, šifra posla, veza dokumenta, datum |
| **v_duplikati** | Stavke sa kontima ispravki i tužbi | `2048%`, `2058%`, `2049%`, `2059%` | Nema |
| **ispravke** | **Doslovno isti tekst** kao `v_duplikati` u ovoj datoteci — vidi upozorenje niže | `2048%`, `2058%`, `2049%`, `2059%` | Nema |
| **tuzeni** | Samo `promena = 'O'` | `2048%`, `2058%` | Godina, partner, datum, konto |
| **dodela bucketa** | Saldo po partneru i vezi dokumenta, **razvrstan po starosti** | Iz `baza` | Partner, naziv, veza dokumenta, šifra posla, prve 3 cifre konta, dospeće |
| *(bez naslova)* | Šifarnik partnera sa povezanog servera, `grupa = 1` | — | Nema |

Svi imaju i stalne uslove `sif_pred = 1`, `god < 2100`, `grupa = 1`, a oni koji gledaju
tekuću godinu izuzimaju početno stanje (`sif_vrs <> 'POC'`). [P]

### Razredi starosti duga — `dodela bucketa`

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
> [P-35](../docs/10-poznati-problemi.md#p-35--nepoznato-dospeće-prikazuje-se-kao-nedospelo),
> i ovaj DDL ga **potvrđuje na izvoru**.

Dve dodatne oznake u istom pogledu [P]:

| Kolona | Pravilo |
|---|---|
| `kategorija` | `0` ako `DATEDIFF(dpo, danas) <= 0`, inače `1` |
| `ino` | `0` ako konto počinje sa `204`, inače `1` — **domaći vs. inostrani kupci** |

Uzimaju se samo stavke sa **saldom različitim od nule** (`HAVING SUM(dug) - SUM(pot) <> 0`). [P]

### Kako se izbegava dvostruko brojanje

`dodela bucketa` datum dospeća sastavlja iz dva skupa [P]:

1. `dupli` — sve iz `v_duplikati`;
2. `bez_duplih` — iz `v_if`, **samo ono čega nema u `v_duplikati`**, sa `MIN(dpo)`.

Spajaju se kroz `UNION ALL` i tek se onda povezuju sa `baza`. Poređenje ide uz
`COLLATE Latin1_General_CI_AI`, dakle **bez obzira na velika/mala slova i dijakritike**. [P]

---

## `fleet_trebovanja` — trebovanja Flote

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
videti [V-10](../docs/obracuni/06-03-flota-troskovi.md#v-10--neto-trošak-održavanja). [P]

---

## `nbv_roba` — roba za Nabavku

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

## Šta još nedostaje

Za ovih 11 izveštaja Flote DDL **još nije preuzet iz baze**: `fleet_tro_svi`,
`fleet_tro_goriva_m`, `fleet_tro_pracenje`, `fleet_tro_taho`, `fleet_tro_parking`,
`tro_zarade`, `fleet_dobavljaci`, `fleet_magacin_rez`, `fleet_otpis`, `kasko_rate`. [P]

Dok ne stignu, na pitanje **„odakle ovaj iznos“** za te izveštaje se ne može odgovoriti
iz projekta.
