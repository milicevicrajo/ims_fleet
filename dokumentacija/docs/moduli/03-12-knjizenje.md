# 3.12. Knjiženje

> **Za koga je ovo poglavlje:** knjigovodstvo, Isplate i programeri.
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Šta postoji (od 07.10.2026.) [P]

Modul u kome se prikazuju dokumenti poslati na knjiženje, radi knjiženje i pamte podaci o knjiženju.
Za sada samo **fiskalni računi iz Isplata**: računi sa putnih naloga i ostali fiskalni računi (gotovinski obračun).
Isplate račun šalju; Knjiženje ga proknjižava ili vraća na doradu. U knjigovodstvo starog ERP-a
(`nalog_z`, `bazaims`) **ništa se ne upisuje** — modul pamti ko je, kada i pod kojim nalogom za knjiženje proknjižio račun.

> **Od 08.10.2026. nema ručnog knjiženja.** Račun se knjiži u drugom programu, pa ga ovde **štampa proknjižava**:
> račun koji čeka knjiženje dobija datum knjiženja danas, korisnika koji štampa i napomenu „Proknjiženo štampom”.
> Proknjižen račun se može ponovo štampati (broji se, knjiženje se ne menja); vraćen na doradu se ne štampa.

| Ekran | Adresa | Šta radi |
|---|---|---|
| **Fiskalni računi** | `/knjizenje/` | Pločice (čeka knjiženje, vraćeno na doradu, proknjiženo ovog meseca), filteri (status, vrsta računa, period računa, period knjiženja), pretraga (i po broju naloga za knjiženje), DataTables sa stranom sa servera. Kolona **Putni nalog / vrsta** (broj naloga, zaposleni, mesto i datum putovanja) i **Šifra posla** sa nazivom — za račun bez šifre šifra putnog naloga, označena „sa putnog naloga”. Označeni računi se **štampaju zajedno** (nova kartica, svaki na svojoj A4 strani). Excel izvoz prati filtere. |
| Detalj računa | `/knjizenje/racun/<id>/` | Potpuni podaci o računu, isti kao u Isplatama i Nabavci (od 08.10.2026., zajednički `nabavka/_fiskalni_*`): upozorenja (nije na IMS, refundacija, zbir stavki), prodavac, prodajno mesto i adresa, ID kupca, brojač, kasir i ESIR, stavke sa osnovicom i PDV-om, tekst računa; podaci iz Isplata (šifra posla, putni nalog sa vozilom i šifrom naloga ili interni broj i napomena), **Štampaj i proknjiži** / **Štampaj ponovo**, vraćanje na doradu, poništavanje knjiženja i istorija (i štampe). |
| **Štampa** | `/knjizenje/stampa/?racuni=…` | A4, zaglavlje kao u rešenjima (logo, Institut, adresa, broj računa, vreme štampe); **šifra posla** krupno sa ukupnim iznosom i PDV-om; upozorenja; podaci sa računa; putni nalog (broj, zaposleni, putovanje, vozilo, šifra naloga) ili napomena; stavke; tekst računa; tok — **učitao, poslao na knjiženje, proknjiženo, štampao** — i mesto za potpis. Ova stranica ništa ne menja; knjiži `POST /knjizenje/stampaj/`. |

## 2. Tok [P]

```
Isplate: Pošalji ──► Čeka knjiženje ──► Proknjiženo
                        │   ▲                │
       Vrati na doradu  ▼   │ Pošalji ponovo │ Poništi knjiženje (razlog)
                     Vraćeno na doradu       └──► Čeka knjiženje
```

| Korak | Pravilo |
|---|---|
| Slanje | Isplate (`isplate:fiskalni_posalji`). Poslat račun se u Isplatama ne menja i ne skida sa putnog naloga. Povlačenja nema. |
| Knjiženje (štampa) | Od 08.10.2026. samo štampom (`stampaj`): račun koji čeka knjiženje dobija datum knjiženja danas; broja naloga nema (knjiži se u drugom programu). Postavlja i `FiskalniRacun.proknjizeno` (zaključava račun i u Nabavci). Ponovna štampa samo uvećava broj štampanja. |
| Vraćanje na doradu | Samo račun koji čeka knjiženje, uz **obavezan razlog** — Isplate ga vide na spisku i detalju, ispravljaju račun i šalju ponovo. Beleži se i u evidenciji rada. |
| Poništavanje | Samo proknjižen račun, uz obavezan razlog. Račun ponovo **čeka knjiženje** (ne vraća se Isplatama); podaci o knjiženju se brišu, a istorija ostaje. Beleži se u evidenciji rada. |
| Raniji računi | Račun označen kao proknjižen u Isplatama pre 07.10.2026. nema zapis; vidi se kao proknjižen, bez istorije, i može se poništiti. |

## 3. Podaci [P]

| Tabela | Sadržaj |
|---|---|
| `knjizenje_knjizenjeracuna` (`KnjizenjeRacuna`) | Jedan red po računu: status (`poslato`, `vraceno`, `proknjizeno`), ko je i kada poslao, datum knjiženja, broj naloga za knjiženje, napomena, ko je i kada proknjižio, razlog vraćanja, ko je i kada vratio; od 08.10.2026. i ko je i kada poslednji štampao i broj štampanja. |
| `knjizenje_dogadjajknjizenja` (`DogadjajKnjizenja`) | Istorija: poslato, vraćeno na doradu, proknjiženo, poništeno knjiženje, odštampano — korisnik, vreme, napomena. |
| `nabavka_fiskalniracun` | `proknjizeno`, `proknjizio`, `proknjizeno_at` ostaju oznaka zaključavanja; drži ih usklađenim servis. `interni_broj` upisuju Isplate. |

Logika je u `knjizenje/services.py` (`posalji`, `vrati_na_doradu`, `stampaj`, `proknjizi`, `ponisti`, `stanje`,
`sifra_posla`, `zakljucan_u_isplatama`); `knjizenje/views.py` samo prikazuje i poziva servis.

## 4. Uloge i dozvole [P]

| Uloga | Šta može |
|---|---|
| `knjizenje` (**Knjiženje**) | Sve u modulu: `knjizenje:racuni`, `knjizenje:racun`, `knjizenje:stampaj`, `knjizenje:stampa`, `knjizenje:vrati`, `knjizenje:ponisti`, `knjizenje:izvoz` (od 08.10.2026. `knjizenje:proknjizi` više ne postoji) i **izveštaje o gorivu** iz Flote (`knjizenje/gorivo.py`: NIS i OMV putnička i teretna po šifri posla, kontrola faktura goriva, Gorivo IMS, knjiženi troškovi goriva, transakcije goriva). `sync_permission_codes` joj daje **samo** te kodove. |
| `uprava` | Sve |
| `blagajna` | Nema pristup modulu — samo šalje račune iz Isplata. |

Modul se u zaglavlju i na početnoj strani vidi samo sa dozvolom `knjizenje:racuni`. Obuhvat po registru
organizacije se ne primenjuje: Knjiženje vidi sve poslate račune.

**Meni „Gorivo — izveštaji”** (od 08.10.2026.): svaka stavka se vidi uz svoju dozvolu. To su ekrani Flote, pa im
podatke ograničava obuhvat Flote — korisniku uloge Knjiženje treba dodela uloge **cela firma** (Organizacija → Dodele
uloga), inače izveštaji koji filtriraju po obuhvatu ostaju prazni.
