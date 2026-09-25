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
| **Korisnici** | Spisak, uređivanje pristupa, povezivanje sa zaposlenim, stvaranje naloga iz kadrovske evidencije |
| **Uloge i dozvole** | Izbor uloga za korisnika i pregled pripadajućih dozvola; dozvole se generišu iz ruta |
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
I stariji `RoleRequiredMixin`, koji proverava slug uloge, od 24.09.2026. isključuje
neaktivne uloge. Spisak korisnika sada traži dozvolu `user_list`.

**Generisanje [P]:** `sync_permission_codes` obilazi `urlpatterns` svih aplikacija.
Nova ruta = nova dozvola, ali tek posle pokretanja komande ili noćnog zadatka u 01:00.

**Uloge koje se usklađuju** (višak dozvola se briše) [P]:
`nabavka`, `menice`, `blagajna`, `mobilni`, `pregled-naplate`, `zahtev`.

**Uloge koje se samo dopunjavaju** [P]: `pravna`, `sekretarijat`, `zaposleni`, `uprava`.

> **[P]** Uloga **`uprava`** pri svakoj sinhronizaciji dobija **sve** dozvole u sistemu.

### Glavne predefinisane uloge [P]

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

### Upravljanje pristupom kroz aplikaciju

U **Administracija → Korisnici → Uloge i dozvole**, superuser bira uloge,
centre iz pretraživih spiskova. Tu se menjaju ime, prezime,
e-pošta i aktivnost naloga. Pregled dozvola prati izabrane uloge, a primena je
tek nakon **Sačuvaj pristup**. Pristup listi traži `user_list`; izmene naloga su
i dalje samo za superuser, uključujući direktan POST. Nije moguće ugasiti sopstveni
nalog niti kroz ovu formu dodeliti `is_superuser` ili `is_staff`.

Centri se čuvaju u `allowed_center_codes`. Izbor pojedinačnih kadrovskih OJ
(`allowed_hr_unit_codes`) **uklonjen je 25.09.2026.** — nijedan korisnik ga nije imao.
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

### Dodele uloga sa obuhvatom (od 25.09.2026.) [P]

**Organizacija → Dodele uloga** (`/organizacija/dodele/`) je ekran novog modela prava iz plana
prelaska na registar (korak 3). Za svaku ulogu korisnika određuje se **obuhvat** u stablu
organizacije: cela firma, centar, jedinica ili šifra posla, sa periodom važenja. Obuhvat centra
pokriva njegove jedinice i šifre; obuhvat šifre ne daje ceo centar.

| Radnja | Šta radi |
|---|---|
| Spisak | Korisnici sa brojem dodela u nacrtu i odobrenih; filter „Ima nacrt / Odobreni / Bez dodela”; **Proveri razlike (senka)** poredi sve korisnike (traje ~10 s) |
| Kartica korisnika | Sve dodele sa istorijom, stara prava koja danas odlučuju i senka samo za tog korisnika |
| **Odobri nacrt** | Nacrt iz prevoda starih prava postaje odobren; beleži se ko i kada. Odobrenog korisnika prevod (`prava_u_senci`) više ne menja |
| **Nova dodela** | Ručna dodela, odmah odobrena; nude se samo uloge koje korisnik već ima i samo **aktivne** šifre; ista uloga sa istim obuhvatom u preklopljenom periodu se odbija |
| **Opozovi** | Odobrena dodela prestaje da važi od danas i ostaje u istoriji sa imenom onoga ko ju je opozvao; neodobren nacrt se briše |

Dozvole: `organizacija:dodele`, `organizacija:dodele_korisnika`, `organizacija:dodele_odobri`,
`organizacija:dodela_opozovi` — dobija ih uloga Uprava. **Dodele još ne odlučuju o pristupu**:
moduli rade po starim pravima (`allowed_center_codes`, `allowed_centers`) do pilota Finansija i
Potraživanja. Uloga Uprava dobija celu firmu kao običnu dodelu, ne kao izuzetak u proveri.

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
| Superuser | Sve, uključujući Django admin i upravljanje pristupom korisnika kroz aplikaciju |

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
