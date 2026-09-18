# 3.10. Administracija

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

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

## 2. Poslovna namena

Vodi **ko sme šta da radi u sistemu i šta je ko uradio**:

1. **Korisnici** i njihova veza sa zaposlenima.
2. **Uloge i dozvole** — ko vidi koji ekran.
3. **Organizacione jedinice i centri** — osnova svih evidencija i ograničenja pristupa.
4. **Evidencija rada** — trag svake radnje u sistemu.
5. **Istorija pozadinskih poslova** — da li su noćne sinhronizacije prošle.

---

## 3. Korisnici modula

| Korisnik | Šta radi |
|---|---|
| **Administrator sistema** | Vodi korisnike, dodeljuje uloge i centre, prati rad sistema |
| **Uprava** | Uvid u evidenciju rada |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Korisnici** | Spisak, povezivanje sa zaposlenim, stvaranje naloga iz kadrovske evidencije |
| **Uloge i dozvole** | 11 predefinisanih uloga; dozvole se generišu iz ruta |
| **Organizacione jedinice** | Šifra, naziv, **centar** |
| **Evidencija rada** | Ko, kada, koji ekran, koji zapis, sa koje IP adrese |
| **Istorija zadataka** | Status, trajanje, rezultat i greška svakog pozadinskog posla |
| **Prebacivanje modula** | Izbor bočnog menija, pamti se u sesiji |
| **Obavezna promena lozinke** | Za naloge sa oznakom `must_change_password` |

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Korisnici** | `/users/` |
| Povezivanje korisnika sa zaposlenim | `/users/link-employee/` |
| **Stvaranje naloga za zaposlene** | `/users/create-missing-profiles/`, `/users/create-profile/<id>/` |
| **Evidencija rada** | `/administracija/activity-log/` |
| **Istorija zadataka** | `/administracija/task-history/` |
| Organizacione jedinice | `/organizacione-jedinice` |
| Prijava / odjava | `/login/`, `/logout/` |
| Obavezna promena lozinke | `/moj-profil/promena-lozinke/` |
| Django admin | `/admin/` |

---

## 6. Podaci koje korisnik unosi

| Podatak | Ko unosi |
|---|---|
| Korisnički nalog: korisničko ime, lozinka | Administrator |
| **Veza korisnika sa zaposlenim** | Administrator |
| **Uloge** korisnika | Administrator |
| **Dozvoljeni centri** (veza i/ili tekstualna lista) | Administrator |
| Oznaka „mora promeniti lozinku“ | Administrator |
| Organizaciona jedinica (ručno) | Administrator |

---

## 7. Podaci koje sistem preuzima automatski

| Podatak | Izvor | Kada |
|---|---|---|
| **Organizacione jedinice i centri** | `dbo.v_organizationalunit` | Dnevno 01:30 |
| **Kodovi dozvola** | Automatski iz `urlpatterns` svih aplikacija | Dnevno 01:00 |
| Evidencija rada | Sam sistem, kroz `ActivityLogMiddleware` | Pri svakom zahtevu |
| Istorija zadataka | Celery signali | Pri svakom zadatku |

---

## 8. Tabele i kolone

Detaljno: [4.3. Zajedničke osnove](../04-baza-podataka.md#43-zajedničke-osnove--core-tabele-u-fleet_).
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

## 9. Kako rade dozvole

```
 CustomUser ──M2M──► Role ──RolePermission──► PermissionCode
                      │                            │
                  is_active                 code = IME URL RUTE
```

**Provera [P]:** korisnik ima pristup ako ijedna njegova **aktivna** uloga sadrži kod
jednak imenu rute koja se otvara. `is_superuser` prolazi svuda.

**Generisanje [P]:** `sync_permission_codes` obilazi `urlpatterns` svih aplikacija.
Nova ruta = nova dozvola, ali tek posle pokretanja komande ili noćnog zadatka u 01:00.

**Uloge koje se usklađuju** (višak dozvola se briše) [P]:
`nabavka`, `menice`, `blagajna`, `mobilni`, `pregled-naplate`, `zahtev`.

**Uloge koje se samo dopunjavaju** [P]: `pravna`, `sekretarijat`, `zaposleni`, `uprava`.

> **[P]** Uloga **`uprava`** pri svakoj sinhronizaciji dobija **sve** dozvole u sistemu.

### Jedanaest predefinisanih uloga [P]

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
| `zaposleni` | Zaposleni |

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| Modeli | [`core/models.py`](../../../core/models.py) |
| **Generisanje dozvola** | [`core/permissions.py`](../../../core/permissions.py) |
| **Provera dozvola** | [`core/mixins.py`](../../../core/mixins.py) |
| Evidencija rada | [`core/middleware.py`](../../../core/middleware.py), [`core/activity.py`](../../../core/activity.py) |
| Prebacivanje modula | [`core/context_processors.py`](../../../core/context_processors.py), [`core/views.py`](../../../core/views.py) |
| Ekrani korisnika i logova | [`fleet/views/users.py`](../../../fleet/views/users.py) |
| **Raspored pozadinskih poslova** | [`core/management/commands/sync_celery_periodic_tasks.py`](../../../core/management/commands/sync_celery_periodic_tasks.py) |
| Istorija zadataka | [`ims_erp/celery.py`](../../../ims_erp/celery.py) — signali |

---

## 11–12. Ulaz, izlaz i veze

| Modul | Veza |
|---|---|
| **Svi moduli** | Organizaciona jedinica i centar; dozvole |
| **Kadrovi** | `CustomUser.employee` → `fleet_employee` |

---

## 13. Izveštaji i analize

Modul nema obračune. Ima dva pregleda:

| Pregled | Sadržaj |
|---|---|
| **Evidencija rada** | Prijave, odjave, **neuspešne prijave**, pojedinačne radnje |
| **Istorija zadataka** | Status (`Pokrenut`, `Uspešan`, **`Preskočen`**, `Neuspešan`), trajanje, poruka |

---

## 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `uprava` | Sve |
| Superuser | Sve, uključujući Django admin i tuđe radne liste |

> **Ranija zamka, ispravljena 18.09.2026.:** statistiku centra u Floti ni superuser nije
> mogao da otvori bez upisanih dozvoljenih centara — [P-13](../10-poznati-problemi.md).
> Provera je usklađena sa `RolePermissionRequiredMixin`.

---

## 15. Validacije i kontrole

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

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje |
|---|---|
| Nova ruta bez pokretanja sinhronizacije dozvola | Vide je **samo superuser i Uprava** |
| **Dva mehanizma za centre** | `allowed_centers` i `allowed_center_codes` rade paralelno — [P-19](../10-poznati-problemi.md) |
| Korisnik bez povezanog zaposlenog | Ne može otvoriti radnu listu ni svoj profil |
| Zadatak preskočen | Status **„Preskočen“** — prethodni je još radio, **nije greška** |
| Redis nedostupan | Zadatak se **ipak izvršava**, bez zaštite — [P-16](../10-poznati-problemi.md) |
| Brisanje korisnika | Evidencija rada **zadržava** korisničko ime i ime |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | **Koji mehanizam za centre je merodavan** | **Q5** / [P-19](../10-poznati-problemi.md) |
| 2 | Ko je odgovoran za dodelu uloga i po kom pravilu | **Q2** |
| 3 | Koliko dugo se čuva evidencija rada i da li se briše | **[N]** |
| 4 | Sadržaj pogleda `dbo.v_organizationalunit` | DDL |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [2.6. Kontrola pristupa](../02-arhitektura.md#26-kontrola-pristupa) | Kako rade dozvole |
| [9. Održavanje](../09-odrzavanje.md) | Zakazani poslovi i praćenje |
| [4.3](../04-baza-podataka.md#43-zajedničke-osnove--core-tabele-u-fleet_) | Tabele |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-13, P-16, P-19 |
