# 3.9. Isplate

> Deo poglavlja [3. Moduli](../03-moduli.md).
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.

---

## 1. Naziv modula

| | |
|---|---|
| Naziv na ekranu | **Isplate** / „Isplata neoporezivih primanja“ |
| Tehnički naziv | Django aplikacija `isplate` |
| Adresa | `/isplate/` |
| Bočni meni | `sidebar_isplate.html` |

> **[P] Modul nema nijednu sopstvenu tabelu.** Radi isključivo nad putnim nalozima
> Flote i proizvodi datoteku.

---

## 2. Poslovna namena

Pretvara **akontacije sa putnih naloga** u **datoteku za elektronsko bankarstvo**, da
blagajna ne bi ručno kucala naloge za plaćanje.

> **Ovo je jedini modul čiji rezultat ide direktno u banku.**
> Greška ovde znači pogrešnu isplatu.

---

## 3. Korisnici modula

| Korisnik | Šta radi | Uloga |
|---|---|---|
| **Blagajna** | Bira naloge, zadaje datum virmana, preuzima datoteku, učitava je u banku | `blagajna` |

---

## 4. Glavne funkcionalnosti

| Celina | Šta obuhvata |
|---|---|
| **Spisak putnih naloga za isplatu** | Filteri: status virmana, centar, godina, mesec, pretraga |
| **Generisanje virmana** | Izabrani nalozi ili svi filtrirani; datum virmana |
| **Ponovno generisanje** | Uz izričit izbor |
| **Konverter** | Postojeća virman datoteka → JSON |

---

## 5. Glavni korisnički ekrani

| Ekran | Adresa |
|---|---|
| **Isplata neoporezivih primanja** | `/isplate/` |
| **Konverter** | `/isplate/konverter/` |
| **Putni nalozi – pravdanje** (od 02.10.2026.) | `/isplate/putni-nalozi/` |
| **Putni nalozi – Fiskalni računi** (od 02.10.2026.) | `/isplate/fiskalni-racuni/` |

### Putni nalozi – Fiskalni računi (od 02.10.2026.) [P]

Fiskalni računi se dodaju **pri pravdanju putnog naloga** (Isplate → Putni nalozi – pravdanje: dugme
„Dodaj račun" otvara prozor sa računima naloga i poljem za čitač QR koda; „Opravdaj" zaključava nalog)
ili **odmah u toku isplate** — isto dugme i isti prozor postoje u svakom redu tabele Nalozi za isplatu
(Isplata neoporezovanih), kolona „Fiskalni računi". Dugme pokazuje broj i zbir računa naloga i osvežava se
odmah posle skeniranja, bez ponovnog učitavanja strane (izbor naloga za virman ostaje).
Račun se čuva gde i ostali fiskalni računi (`nabavka.FiskalniRacun`), samo je vezan za putni nalog
(`putni_nalog`). Knjigovodstvo ih vidi i označava na ekranu Putni nalozi – Fiskalni računi.

| Tema | Pravilo |
|---|---|
| Šta se vidi | Samo računi vezani za putni nalog. Računi koji su učitani samo u Nabavci se ne prikazuju. |
| Kolone | Vreme, prodavac i PIB, broj računa (veza na detalj u Nabavci), iznos, PDV, kupac (IMS / drugi kupac / fizičko lice), putni nalog (zaposleni, mesto, datum, oznaka storniranog naloga), šifra posla, ko je učitao, **Proknjiženo** |
| Filteri | Knjiženje (podrazumevano neproknjiženi), kupac, period i pretraga tabele; primenjuju se odmah. Zbir i PDV u zaglavlju prate filtere i pretragu; izvoz u Excel takođe. |
| Tabela | Oba spiska (pravdanje i knjiženje) su DataTables tabele sa stranom sa servera — isti URL uz parametar `draw` vraća JSON (`isplate/tabela.py`), pa nema posebne dozvole za podatke. |
| Proknjiženo | Polje za štikliranje čuva se odmah i pamti ko je i kada označio (`proknjizeno`, `proknjizio`, `proknjizeno_at`). Ne upisuje ništa u knjigovodstvo. Poništavanje oznake traži potvrdu i beleži se u evidenciji rada. |
| Zaključavanje | Proknjižen račun se u Nabavci ne briše i ne menja (obrada, šifre posla), niti se skida sa putnog naloga. |
| Pravdanje | Spisak putnih naloga (podrazumevano neopravdani; pretraga, period putovanja) sa brojem i zbirom računa. Opravdan nalog je **zaključan**: računi se više ne dodaju ni skidaju. „Opravdaj" je isto što i u Floti. |
| Dodavanje računa | Novi račun dobija **šifru posla putnog naloga**. Račun koji je već učitan u Nabavci se samo **veže** za nalog i zadržava svoju šifru. Račun vezan za drugi nalog se ne prevezuje; na storniran nalog se računi ne dodaju (postojeći ostaju, uz oznaku). Pogrešno skeniran račun se skida sa naloga dok nije proknjižen, a ostaje u evidenciji Nabavke. |
| Obuhvat | Isplate rade po starim pravima: oba ekrana pokazuju sve putne naloge i sve račune sa njih, kao ekran isplate akontacija. |
| Dozvole | Pravdanje: `isplate:putni_nalozi_pravdanje`, `isplate:putni_nalog_racuni`, `isplate:putni_nalog_racun_dodaj`, `isplate:putni_nalog_racun_ukloni`, `isplate:putni_nalog_opravdaj`. Knjiženje: `isplate:fiskalni_putni_nalozi`, `isplate:fiskalni_proknjizi`, `isplate:fiskalni_izvoz`. Uloga Blagajna ih dobija automatski. |

---

## 6. Podaci koje korisnik unosi

| Podatak | Napomena |
|---|---|
| **Datum virmana** | Obavezan — *„Izaberi datum virmana.“* |
| Izbor naloga | Pojedinačno ili svi filtrirani |
| Dozvoli ponovno generisanje | Izričit izbor |
| Datoteka za konverziju | `.txt` u konverteru |

> **[P] Modul ne unosi nijedan poslovni podatak** — svi dolaze sa putnog naloga i
> iz kadrovske evidencije.

---

## 7. Podaci koje sistem preuzima

| Podatak | Odakle |
|---|---|
| Broj naloga, iznos akontacije, valuta, status storna | `fleet_putninalog` |
| **Partija (tekući račun)** | `fleet_employee.account_number` |
| Ime i prezime | `fleet_employee.original_full_name` |
| **Opština boravka** | `fleet_employee.residence_municipality` |

**Podaci platioca su upisani u kod** [P]:

| Podatak | Vrednost |
|---|---|
| Račun platioca | `205000000001445485` |
| Naziv | `Institut IMS a.d.` |
| Mesto | `Beograd` |
| Svrha | `NEOPOREZIVA PRIMANJA ZAPOSLENIH` |
| Šifra plaćanja | `241` |

---

## 8. Tabele i kolone

**Modul nema sopstvenih tabela.** [P]

Upisuje u `fleet_putninalog`:

| Kolona | Kada |
|---|---|
| `virman_generated` | Postaje `True` posle generisanja |
| `virman_generated_at` | Trenutak generisanja |
| `virman_generated_by` | Korisnik |

---

## 9. Spoljni izvori

| Izvor | Smer | Oblik |
|---|---|---|
| **Banka (elektronsko bankarstvo)** | **Izlaz** | Datoteka fiksne širine, **180 znakova**, `cp1250`, `CRLF` |

---

## 10. Glavne klase, funkcije i fajlovi

| Šta | Gde |
|---|---|
| **Generisanje virmana** | [`isplate/services/virman.py`](../../../isplate/services/virman.py) |
| **Konverter u JSON** | [`isplate/services/converters.py`](../../../isplate/services/converters.py) |
| Ekrani | [`isplate/views.py`](../../../isplate/views.py) |

Testovi: **20 testova**. [P]

---

## 11–12. Ulaz, izlaz i veze

| Modul | Veza |
|---|---|
| **Flota** | Putni nalozi sa akontacijom — jedini izvor |
| **Kadrovi** | Partija i opština boravka zaposlenog |

**Tok [Z]:**

```
 Sekretarijat izdaje putni nalog sa akontacijom
            │
 Blagajna bira naloge i datum virmana
            │
 Sistem pravi datoteku (180 znakova po redu)
            │
 Blagajna učitava datoteku u elektronsko bankarstvo
            │
 Banka izvršava plaćanja → zaposleni prima akontaciju
            │
 Zadatak u 12:30 puni polje „Isplaćeno“ iz dbo.fleet_zatvoren_putni
```

> **[N] Q32:** poslednji korak **nije povezan** sa generisanim virmanom u kodu.
> Nije potvrđeno da li se isplata po virmanu igde potvrđuje u sistemu.

---

## 13. Izveštaji i analize

**3 obračuna.** Detaljno: [6.10. Isplate](../obracuni/06-10-isplate.md).

| Oznaka | Naziv |
|---|---|
| I-01 | **Generisanje datoteke virmana** — [P-33](../10-poznati-problemi.md) |
| I-02 | Kontrole naloga pre virmana |
| I-03 | Konverzija virmana u JSON |

---

## 14. Uloge i prava pristupa

| Uloga | Šta može |
|---|---|
| `blagajna` | **Sve funkcije modula** — usklađuje se automatski |
| `uprava` | Sve |

---

## 15. Validacije i kontrole

**Devet provera pre generisanja, sve greške se prijavljuju zajedno** [P]:

| # | Provera |
|---|---|
| 1 | Nalog nije storniran |
| 2 | Virman nije već odrađen (osim uz izričito ponovno generisanje) |
| 3 | **Valuta je RSD** |
| 4 | **Nalog ima IMS zaposlenog** — ne spoljno lice |
| 5 | Zaposleni ima račun |
| 6 | **Račun ima tačno 18 cifara** |
| 7 | Iznos je veći od nule |
| 8 | Broj naloga ima redni broj posle crtice |
| 9 | Redni broj nije duži od 21 znaka |

**Dodatna kontrola [P]:** svaki red se proverava na **tačno 180 znakova**;
neispravan red **prekida** nastanak datoteke.

---

## 16. Poznati izuzeci i granični slučajevi

| Slučaj | Ponašanje | Problem |
|---|---|---|
| **Naziv primaoca duži od 35 znakova** | **Skraćuje se bez upozorenja** | [P-33](../10-poznati-problemi.md) |
| **Mesto duže od 10 znakova** | **Skraćuje se** — „Novi Beograd“ → „Novi Beogr“ | [P-33](../10-poznati-problemi.md) |
| Zaposleni bez opštine boravka | Upisuje se **`Beograd`** | [P-33](../10-poznati-problemi.md) |
| **Sadržaj poslate datoteke** | **Ne čuva se** | [P-33](../10-poznati-problemi.md) |
| Srpska slova | Preslovljavaju se: `đ`→`dj`, `č`/`ć`→`c`, `š`→`s`, `ž`→`z` |  |
| Znak van `cp1250` | Zamenjuje se | — |
| Konverter: svi nalozi | `UrgentPayment` je **uvek `true`** | — |

---

## 17. Šta nije moguće objasniti bez dodatnih podataka

| # | Nejasnoća | Pitanje |
|---|---|---|
| 1 | Treba li da podaci platioca budu podesivi umesto u kodu | **Q30** |
| 2 | Koji sistem koristi JSON iz konvertera | **Q31** |
| 3 | Da li se isplata po virmanu potvrđuje u sistemu | **Q32** |
| 4 | Koja se banka koristi i da li je oblik datoteke njen standard | **[N]** |

---

## Gde dalje

| Poglavlje | Sadržaj |
|---|---|
| [6.10](../obracuni/06-10-isplate.md) | Sva 3 obračuna, sa opisom svakog polja datoteke |
| [3.1. Flota](03-01-flota.md) | Putni nalozi |
| [10. Poznati problemi](../10-poznati-problemi.md) | P-33 |
