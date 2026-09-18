# IMS ERP

Interni poslovni informacioni sistem **Instituta IMS a.d.** Objedinjuje vozni park,
kadrove, finansijsku analitiku, nabavku, potraživanja, ugovore, menice, mobilnu telefoniju
i isplate u jednu web aplikaciju.

| | |
|---|---|
| **Tehnologija** | Python 3.12, Django 5.0, Microsoft SQL Server, Celery 5.4, Redis |
| **Vrsta** | Interna web aplikacija (server-side Django templates) |
| **Okruženje** | Windows server, tri Windows servisa (Redis, Celery worker, Celery beat) |
| **Obim** | 10 poslovnih modula, ~195 stranica, 74 obračuna i analize, 18 zakazanih poslova |

---

## Dokumentacija

| Dokument | Za koga |
|---|---|
| [**AGENTS.md**](AGENTS.md) | Programeri i AI agenti — brzi uvod, pravila, zamke |
| [Pregled sistema](dokumentacija/docs/01-pregled-sistema.md) | Svi — šta sistem radi i ko ga koristi |
| [Arhitektura](dokumentacija/docs/02-arhitektura.md) | Programeri — slojevi, tok podataka, obrasci |
| [Moduli](dokumentacija/docs/03-moduli.md) | Poslovni korisnici i programeri |
| [Baza podataka](dokumentacija/docs/04-baza-podataka.md) | Programeri, DBA |
| [Poslovni procesi](dokumentacija/docs/05-poslovni-procesi.md) | Poslovni korisnici |
| [**Analize i obračuni**](dokumentacija/docs/06-analize-i-obracuni.md) | Svi — kako se svaki iznos računa |
| [Integracije](dokumentacija/docs/07-integracije.md) | Programeri, održavanje |
| [Instalacija i pokretanje](dokumentacija/docs/08-instalacija-i-pokretanje.md) | Programeri, održavanje |
| [Održavanje](dokumentacija/docs/09-odrzavanje.md) | Održavanje |
| [Poznati problemi](dokumentacija/docs/10-poznati-problemi.md) | Svi |
| [Plan razvoja](dokumentacija/docs/11-plan-razvoja.md) | Uprava, programeri |
| [Rečnik pojmova](dokumentacija/docs/12-recnik-poslovnih-pojmova.md) | Svi |
| [**Pregled za upravu**](dokumentacija/docs/uprava/pregled-ims-erp-a.md) | Uprava — netehnički sažetak |

Inventar celog sistema sa statusima pouzdanosti:
[`dokumentacija/00-inventar-i-plan-dokumentacije.md`](dokumentacija/00-inventar-i-plan-dokumentacije.md).

---

## Moduli

| Modul | Adresa | Šta radi |
|---|---|---|
| **Flota** | `/` | Vozila, saobraćajne, lizing, polise, gorivo, servisi, garaža, putni nalozi |
| **Kadrovi** | `/hr/` | Zaposleni, radne liste, godišnji odmori, bolovanja, ocenjivanje |
| **Finansijska analitika** | `/finansije/` | Prihodi, rashodi, zajednički troškovi, tok gotovine po šiframa posla |
| **Nabavka** | `/nabavka/` | Zahtevi, EUF/UF fakture, roba, javne nabavke, narudžbenice |
| **Potraživanja** | `/potrazivanja/` | Dugovanja kupaca, starosna struktura, opomene, pravni postupci |
| **Ugovori** | `/ugovori/` | Partneri, zahtevi, ponude, ugovori, aneksi, garancije |
| **Menice** | `/menice/` | Ulazne i izlazne menice, preuzimanje iz registra NBS |
| **Mobilna telefonija** | `/mobilni/` | Paketi, dodele brojeva, potrošnja, obustave iz zarada |
| **Isplate** | `/isplate/` | Virmani za neoporeziva primanja |
| **Administracija** | `/administracija/` | Korisnici, uloge, log rada, istorija zakazanih poslova |

> **Napomena:** modul `naplata` je nasleđeni sistem koji zamenjuju **Potraživanja**.
> Nije obuhvaćen dokumentacijom; novi rad se ne oslanja na njega.

---

## Pokretanje razvojnog okruženja

```powershell
# 1. Virtuelno okruženje
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. ODBC Driver 17 for SQL Server mora biti instaliran

# 3. Migracije (povezuje se na pravi SQL Server — vidi upozorenje ispod)
.\.venv\Scripts\python.exe manage.py migrate

# 4. Server
.\.venv\Scripts\python.exe manage.py runserver
```

> **Upozorenje:** `manage.py` podrazumevano koristi `ims_erp.settings.development`,
> što je **prava SQL Server baza** `IMS_ERP` na `SMS-SERVER`, a ne lokalna kopija.
> Za testiranje i eksperimente uvek dodaj `--settings=ims_erp.settings.testing`.

## Testovi

```powershell
.\.venv\Scripts\python.exe manage.py test --settings=ims_erp.settings.testing
```

550 testova, izvršavaju se na SQLite bazi u memoriji, bez SQL Servera i Redisa.

## Pozadinski poslovi

```powershell
# Worker (mora poznavati sve redove)
celery -A ims_erp worker -l info -P solo -Q default,sync,selenium

# Raspored
celery -A ims_erp beat --scheduler django_celery_beat.schedulers:DatabaseScheduler -l info

# Upis/ažuriranje rasporeda u bazi
.\.venv\Scripts\python.exe manage.py sync_celery_periodic_tasks
```

Na produkciji ovo rade Windows servisi `IMS_Fleet_Celery_Worker` i `IMS_Fleet_Celery_Beat`
(instalacija: `nssm.bat`).

---

## Struktura projekta

```
ims_erp/          Konfiguracija (settings, urls, celery)
core/             Korisnici, uloge, dozvole, log rada, istorija zadataka
fleet/            Vozni park + korenske rute aplikacije
hr/               Kadrovi
finansije/        Finansijska analitika
nabavka/          Nabavka
potrazivanja/     Potraživanja (zamenjuje naplatu)
ugovori/          Partneri i ugovori
menice/           Menice
mobilni/          Mobilna telefonija
isplate/          Virmani
naplata/          NASLEĐENO — u gašenju
templates/        Globalni šabloni i bočni meniji
dokumentacija/    Dokumentacija projekta
```

Detaljan opis: [Arhitektura](dokumentacija/docs/02-arhitektura.md).
