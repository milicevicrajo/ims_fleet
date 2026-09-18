# 3. Moduli — sadržaj i veze

> **Za koga je ovo poglavlje:** poslovni korisnici i programeri.
> Ovde je pregled svih modula i **kako su povezani**. Detaljan opis svakog modula je u
> zasebnom dokumentu.
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 3.0.1. Sadržaj

| # | Modul | Adresa | Dokument |
|---|---|---|---|
| 1 | **Vozni park (Flota)** | `/` | [03-01-flota.md](moduli/03-01-flota.md) |
| 2 | **Kadrovi** | `/hr/` | [03-02-kadrovi.md](moduli/03-02-kadrovi.md) |
| 3 | **Finansijska analitika** | `/finansije/` | [03-03-finansije.md](moduli/03-03-finansije.md) |
| 4 | **Nabavka** | `/nabavka/` | [03-04-nabavka.md](moduli/03-04-nabavka.md) |
| 5 | **Potraživanja** | `/potrazivanja/` | [03-05-potrazivanja.md](moduli/03-05-potrazivanja.md) |
| 6 | **Ugovori i partneri** | `/ugovori/` | [03-06-ugovori.md](moduli/03-06-ugovori.md) |
| 7 | **Menice** | `/menice/` | [03-07-menice.md](moduli/03-07-menice.md) |
| 8 | **Mobilna telefonija** | `/mobilni/` | [03-08-mobilni.md](moduli/03-08-mobilni.md) |
| 9 | **Isplate** | `/isplate/` | [03-09-isplate.md](moduli/03-09-isplate.md) |
| 10 | **Administracija** | `/administracija/` | [03-10-administracija.md](moduli/03-10-administracija.md) |

> Modul **Naplata** (`/naplata/`) je nasleđen i **nije obuhvaćen dokumentacijom**.
> Zamenjuju ga Potraživanja. Vidi [10. Poznati problemi, P-18](10-poznati-problemi.md).

---

## 3.0.2. Šta koji modul radi — u jednoj rečenici

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

## 3.0.3. Mapa veza između modula

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

### Veze — tabelarno [P]

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

## 3.0.4. Ko koristi koji modul

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

## 3.0.5. Broj ekrana i tabela po modulu [P]

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

## 3.0.6. Gde nastaje, a gde se samo čita

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

## 3.0.7. Zajednička pravila svih modula

### Pristup [P]

Svaki ekran ima dozvolu koja se zove **isto kao ruta**. Vidi
[2.6. Kontrola pristupa](02-arhitektura.md#26-kontrola-pristupa).

### Evidencija rada [P]

Svaki zahtev se beleži u `fleet_activity_log` — ko, kada, koji ekran, koji zapis.
Ekran: `/administracija/activity-log/`.

### Prebacivanje između modula [P]

Bočni meni se bira preko `switch-app`, a izbor se pamti u sesiji.
Postoji 12 menija, među njima i **`pravna`** i **`kadrovi`**, koji nisu zasebne
Django aplikacije.

### Izvoz [P]

| Vrsta | Moduli |
|---|---|
| Excel (`.xlsx`) | Flota, Nabavka, Ugovori, Mobilni, Potraživanja, Finansije |
| CSV | Flota, Mobilni |
| Štampa (HTML) | Flota, Kadrovi, Nabavka, Ugovori, Potraživanja |
| Datoteka za banku | Isplate |

Pri izvozu u Excel tekst iz spoljnih izvora koji počinje sa `=`, `+`, `-` ili `@`
dobija apostrof ispred, da ga Excel **ne protumači kao formulu**. [P]

---

## 3.0.8. Gde dalje

| Pitanje | Poglavlje |
|---|---|
| Kako teče posao od početka do kraja? | [5. Poslovni procesi](05-poslovni-procesi.md) |
| Kako se računa neki iznos? | [6. Analize i obračuni](06-analize-i-obracuni.md) |
| Koje tabele koristi modul? | [4. Baza podataka](04-baza-podataka.md) |
| Odakle dolaze podaci spolja? | [7. Integracije](07-integracije.md) |
