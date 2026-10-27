# Dokumentacija

Ovaj folder sadrži funkcionalnu i tehničku dokumentaciju projekta `ims_erp`.

---

## ⭐ Kompletna dokumentacija sistema — `docs/`

Od 18.09.2026. postoji **objedinjena dokumentacija celog sistema** u direktorijumu
[`docs/`](docs/). Ona je polazna tačka za sva pitanja.

| Dokument | Za koga |
|---|---|
| [**Inventar i plan**](00-inventar-i-plan-dokumentacije.md) | Šta je sve pronađeno u sistemu i kojim redom je dokumentovano |
| [1. Pregled sistema](docs/01-pregled-sistema.md) | Svi |
| [2. Arhitektura](docs/02-arhitektura.md) | Programeri |
| [3. Moduli](docs/03-moduli.md) | Poslovni korisnici i programeri — **12 modula** |
| [4. Baza podataka](docs/04-baza-podataka.md) | Programeri — Django tabele i nasleđeni objekti |
| [5. Poslovni procesi](docs/05-poslovni-procesi.md) | Poslovni korisnici — procesi od početka do kraja |
| [**6. Analize i obračuni**](docs/06-analize-i-obracuni.md) | Svi — svi obračuni, sa formulama i primerima |
| [7. Integracije](docs/07-integracije.md) | Programeri i održavanje — spoljni sistemi |
| [8. Instalacija i pokretanje](docs/08-instalacija-i-pokretanje.md) | Programeri |
| [9. Održavanje](docs/09-odrzavanje.md) | Održavanje — 23 zakazana posla, Celery, česti problemi |
| [**10. Poznati problemi**](docs/10-poznati-problemi.md) | Registar uočenih problema i njihov status |
| [11. Plan razvoja](docs/11-plan-razvoja.md) | Uprava i programeri |
| [12. Rečnik pojmova](docs/12-recnik-poslovnih-pojmova.md) | Svi — pojmovi i mapiranje ekran ↔ kod ↔ baza |
| [13. Vreme i cena razvoja](docs/13-vreme-i-cena-razvoja.md) | Uprava — trajanje, obim, procena tržišne i stvarne cene |
| [**Pregled za upravu**](docs/uprava/pregled-ims-erp-a.md) | **Uprava — netehnički sažetak** |

Uz njih, u korenu projekta:
[`README.md`](../README.md) i [`AGENTS.md`](../AGENTS.md) — uputstvo za programere i AI agente.

---

## Objedinjeno izdanje — jedan dokument

[**`IMS-ERP-dokumentacija.md`**](IMS-ERP-dokumentacija.md) sadrži **sva poglavlja iz `docs/` u
jednom fajlu**, sa sadržajem. Za štampu, slanje i arhiviranje.

> ⚠ **Ne uređuje se ručno.** Uređuju se pojedinačna poglavlja u [`docs/`](docs/), pa se
> dokument pravi ponovo:
>
> ```
> python dokumentacija/spoji-dokumentaciju.py
> ```
>
> Skripta spušta naslove za jedan nivo, veze među poglavljima pretvara u sidra, veze ka
> kodu preračunava iz novog položaja i pravi sadržaj. Na kraju ispisuje **upozorenja** ako
> neka veza ne može da se razreši.

---

## Definicije nasleđenih SQL pogleda — `ddl-nasledjenih-pogleda/`

[`ddl-nasledjenih-pogleda/`](ddl-nasledjenih-pogleda/README.md) čuva **stvarne definicije
pogleda iz baze** — formule koje aplikacija samo izvršava, a koje se ne vide u Python kodu.

| Datoteka | Sadrži |
|---|---|
| `naplata-pogledi.sql` | Sedam pogleda Naplate, uključujući razrede starosti duga |
| `fleet_trebovanja.sql` | Trebovanja Flote, sa `kol * cena AS vrednost_nab` |
| `nbv_roba.sql` | Roba za Nabavku |

> ⚠ `.gitignore` isključuje `*.sql`. U repozitorijumu je samo `naplata-pogledi.sql`;
> ostale datoteke iz ovog foldera postoje samo lokalno dok se ne dodaju sa `git add -f`.

To je prvi deo odgovora na [P-27](docs/10-poznati-problemi.md).

---

## Moduli u pripremi — Arhiva i BZR

### Arhiva

| Dokument | Status |
|---|---|
| [`docs/moduli/03-11-arhiva-plan.md`](docs/moduli/03-11-arhiva-plan.md) | **Važeći plan** (11.10.2026.) — jedini plan po kom se radi. Odeljak 1.1a: šta je otvoreno za faze 0–2 |
| [`docs/moduli/03-11-arhiva.md`](docs/moduli/03-11-arhiva.md) | Šta je u aplikaciji već urađeno |
| [**`Arhiva - pitanja za arhivu.docx`**](<Arhiva - pitanja za arhivu.docx>) | **Aktuelna pitanja arhivskoj službi** (11.10.2026.), oznake A–F: Kancelarko i slanje Državnom arhivu, sporne stavke Liste kategorija, rok čuvanja, delovodnik i probni rad, kretanje predmeta. Rok za A, B, D: **31.10.2026.**; za C, E: 15.11.2026. |
| [`Arhiva - pitanja i izmene za upravu.docx`](<Arhiva - pitanja i izmene za upravu.docx>) | Aktuelna pitanja upravi i pravnoj službi (11.10.2026.), oznake U1–U7: potvrde odluka, izmene pravilnika član po član, akti koji nedostaju |
| [`Obilazak sluzbi - Arhiva i BZR.docx`](<Obilazak sluzbi - Arhiva i BZR.docx>) | Radni podsetnik od 07.10.2026. **Deo o Arhivi je zamenjen** dokumentima od 11.10.2026. (odluke su donete, rokovi 15.10. i 20.10. su prošli); deo o BZR je i dalje podsetnik za razgovor sa službom BZR |

### BZR

| Dokument | Status |
|---|---|
| [`plan-bzr.md`](plan-bzr.md) | Plan modula BZR (05.10.2026.) |
| [`bzr/oprema-za-rad-2019.xlsx`](bzr/oprema-za-rad-2019.xlsx) | Početni popis opreme za rad (tačka 11 plana) |

---

## Organizacija i dozvole — završeni planovi

Prelazak na registar organizacije je **završen 28.09.2026.** Ovi planovi su istorija odluka;
na `plan-registra-sifara-posla.md` i `popis-sifara-posla-korak-0.md` pozivaju se i kod i testovi
u `organizacija/`, pa se ne brišu.

| Dokument | Šta sadrži |
|---|---|
| [`plan-centralizacije-organizacije.md`](plan-centralizacije-organizacije.md) | Tri nivoa organizacije, istorija šifara — poslovna pravila registra |
| [`plan-organizacije-i-dozvola-v2.md`](plan-organizacije-i-dozvola-v2.md) | Uloge po centru, OJ i poslu; poslovni Admin panel |
| [`popis-sifara-posla-korak-0.md`](popis-sifara-posla-korak-0.md) | Merenje nad produkcijom: 415 šifara, tri porodice |
| [`plan-registra-sifara-posla.md`](plan-registra-sifara-posla.md) | Registar, uvoz, stablo i nalaz o obrtu |
| [`plan-prelaska-na-registar.md`](plan-prelaska-na-registar.md) | Čitanje, prava i gašenje stare organizacije — svi koraci izvedeni 28.09.2026. |
| [`SERFIN-provere-nakon-gasenja.docx`](SERFIN-provere-nakon-gasenja.docx) | Provere posle prelaska sa SERFIN-a na `PUTGEO-SERVER.bazaldims` (28.09.2026.) |

---

## Ostali zadržani dokumenti

| Dokument | Šta sadrži |
|---|---|
| [`Analiza aplikacije i procedure rada - IMS flota.md`](<Analiza aplikacije i procedure rada - IMS flota.md>) | Izvor za poglavlje Flote; na njega se poziva [10. Poznati problemi](docs/10-poznati-problemi.md) |
| [`Procena prenosa trebovanja u Nabavku.md`](<Procena prenosa trebovanja u Nabavku.md>) | Procena prenosa trebovanja; na nju se poziva [10. Poznati problemi](docs/10-poznati-problemi.md) |
| [`dijagrami/`](dijagrami/index.html) | PlantUML dijagrami, PNG/SVG i atlas modela |

---

## Uklonjeni dokumenti

Sadržaj je prešao u [`docs/`](docs/) ili je posao završen. Dokumenti ostaju u git istoriji i
vraćaju se sa:

```
git show <commit>:dokumentacija/<naziv-fajla> > <naziv-fajla>
```

**Uklonjeni 20.10.2026.** (vraćaju se iz commita `3c9b2f0`):

| Dokument | Zašto |
|---|---|
| `celery-sta-je-uradjeno.md`, `celery-taskovi-opsti-vodic.md` | Beleške iz aprila 2026.; zaključavanje, redovi i `-P solo` su u [2. Arhitektura](docs/02-arhitektura.md) i [9. Održavanje](docs/09-odrzavanje.md) |
| `plan_migracije_naplata_u_ims_erp.md` | Plan iz aprila 2026. je izvršen — Naplata je u `IMS_ERP`, bez posebne konekcije, a modul se gasi u korist Potraživanja |
| `plan-povezivanja-i-dozvola.md` | Zamenio ga je `plan-prelaska-na-registar.md`, koji je izveden 28.09.2026. |
| `Plan centralizacije organizacije i sifara posla.docx` | Word izdanje `plan-centralizacije-organizacije.md` od 18.09.2026. |
| `detalj-vozila.md` | Beleška od 10.09.2026., delimično zastarela (osnov raspolaganja je od 05.10.2026. samo kroz ugovore); detalj vozila je opisan u [3.1. Flota](docs/moduli/03-01-flota.md) |

**Uklonjeni 18.09.2026.** (vraćaju se iz commita `06f60c2`):

| Dokument | Šta je sadržao | Gde je sadržaj sada |
|---|---|---|
| `finansije-metodologija-obracuna.md` (584 reda) | **Puna metodologija Finansija** — izvori, datumi i formule prihoda, rashoda, ZT, rezultata, priliva, odliva i neto gotovine; kontrolni primeri | [6.1. Finansije](docs/obracuni/06-01-finansije.md) — **samo sažetak**, vidi napomenu u tom poglavlju |
| `naplata-nova-aplikacija-plan.md` (374 reda) | Osam nasleđenih pogleda, predlog modela, nalazi kvaliteta podataka | [3.5. Potraživanja](docs/moduli/03-05-potrazivanja.md), [6.8.](docs/obracuni/06-08-potrazivanja.md) |
| `nabavka-modeli-zahtevi-euf-uf-roba.md` (450 redova) | Četiri evidencije Nabavke, tvrdo povezivanje i meko poklapanje | [3.4. Nabavka](docs/moduli/03-04-nabavka.md), [6.9.](docs/obracuni/06-09-nabavka.md) |
| `naplata-lokalni-izvor-plan.md` (114 redova) | IF/ON filteri, `sp_AzurirajNalogZ`, plan rasporeda | [4. Baza](docs/04-baza-podataka.md), [9. Održavanje](docs/09-odrzavanje.md) |
| `nabavka-funkcionalnosti-i-povezivanja.md` | Pregled funkcionalnosti Nabavke i dalje faze | [3.4. Nabavka](docs/moduli/03-04-nabavka.md) |
| `potrazivanja-paralelni-prenos-2026-09-18.md`, `potrazivanja-samostalan-rad.md` | Paralelan rad sa Naplatom, novi unosi, pravni postupci | [3.5. Potraživanja](docs/moduli/03-05-potrazivanja.md) |
| `kontrolna-tabla.md`, `unos-vozila-carobnjak.md` | Kontrolna tabla i čarobnjak za unos vozila | [3.1. Flota](docs/moduli/03-01-flota.md) |
| `opravdanost_radnog_mesta_*.md`, `procena_*.md` | Poslovne procene (radno mesto, server, vrednost aplikacije) | Nisu tehnička dokumentacija; nisu prenošeni |
