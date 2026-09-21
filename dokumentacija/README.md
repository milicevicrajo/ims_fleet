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
| [3. Moduli](docs/03-moduli.md) | Poslovni korisnici i programeri — **10 modula** |
| [4. Baza podataka](docs/04-baza-podataka.md) | Programeri — 118 tabela + 37 nasleđenih objekata |
| [5. Poslovni procesi](docs/05-poslovni-procesi.md) | Poslovni korisnici — **9 procesa od početka do kraja** |
| [**6. Analize i obračuni**](docs/06-analize-i-obracuni.md) | Svi — **svih 74 obračuna**, sa formulama i primerima |
| [7. Integracije](docs/07-integracije.md) | Programeri i održavanje — 9 spoljnih sistema |
| [8. Instalacija i pokretanje](docs/08-instalacija-i-pokretanje.md) | Programeri |
| [9. Održavanje](docs/09-odrzavanje.md) | Održavanje — 18 zakazanih poslova, česti problemi |
| [**10. Poznati problemi**](docs/10-poznati-problemi.md) | **Registar 50 uočenih problema — 20 rešeno (18–19.09.2026.)** |
| [11. Plan razvoja](docs/11-plan-razvoja.md) | Uprava i programeri |
| [12. Rečnik pojmova](docs/12-recnik-poslovnih-pojmova.md) | Svi — pojmovi i mapiranje ekran ↔ kod ↔ baza |
| [**Pregled za upravu**](docs/uprava/pregled-ims-erp-a.md) | **Uprava — netehnički sažetak** |

Uz njih, u korenu projekta:
[`README.md`](../README.md) i [`AGENTS.md`](../AGENTS.md) — uputstvo za programere i AI agente.

---

## Objedinjeno izdanje — jedan dokument

[**`IMS-ERP-dokumentacija.md`**](IMS-ERP-dokumentacija.md) sadrži **svih 35 poglavlja u
jednom fajlu** — 18.343 reda, sadržaj od 465 stavki. Za štampu, slanje i arhiviranje.

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

To je prvi deo odgovora na [P-27](docs/10-poznati-problemi.md). DDL za 11 izveštaja Flote
tek treba preuzeti iz baze.

---

## Raniji dokumenti

Dokumenti nastali pre objedinjene dokumentacije.

> **Uklonjeni iz repozitorijuma 18.09.2026.** Sadržaj je prešao u
> [`docs/`](docs/), a sami dokumenti ostaju u git istoriji. Vraćaju se sa:
>
> ```
> git show 06f60c2:dokumentacija/<naziv-fajla> > <naziv-fajla>
> ```

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

**Zadržani su:**

| Dokument | Šta sadrži |
|---|---|
| [`celery-sta-je-uradjeno.md`](celery-sta-je-uradjeno.md) | Izmene radi stabilnijeg rada Celery-ja na Windows serveru |
| [`celery-taskovi-opsti-vodic.md`](celery-taskovi-opsti-vodic.md) | Arhitektura, podešavanja, raspored i operativa Celery zadataka |
| [`plan-centralizacije-organizacije.md`](plan-centralizacije-organizacije.md) | Tri nivoa organizacije, istorija šifara, fazni prelazak |
| [`plan-organizacije-i-dozvola-v2.md`](plan-organizacije-i-dozvola-v2.md) | **Novi plan:** uloge po centru, OJ i poslu; poslovni Admin panel |
| [`popis-sifara-posla-korak-0.md`](popis-sifara-posla-korak-0.md) | **Merenje nad produkcijom:** 415 sifara, tri porodice, sta se poklapa |
| [`plan-registra-sifara-posla.md`](plan-registra-sifara-posla.md) | **Za realizaciju:** registar paralelno, pa modul po modul |
| [`plan_migracije_naplata_u_ims_erp.md`](plan_migracije_naplata_u_ims_erp.md) | Rani plan prelaska Naplate |
| [`Analiza aplikacije i procedure rada - IMS flota.md`](<Analiza aplikacije i procedure rada - IMS flota.md>) | Izvor za poglavlje Flote |
| [`Procena prenosa trebovanja u Nabavku.md`](<Procena prenosa trebovanja u Nabavku.md>) | Procena prenosa trebovanja |
| [`detalj-vozila.md`](detalj-vozila.md) | Detalj vozila — pet kartica |
| [`00-inventar-i-plan-dokumentacije.md`](00-inventar-i-plan-dokumentacije.md) | Inventar sistema, 45 pitanja i plan rada |
