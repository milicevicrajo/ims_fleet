# 3.11. Arhiva — pisarnica i delovodnik

> **Za koga je ovo poglavlje:** arhivska služba, pisarnica i programeri.
> Status tvrdnji: **[P]** potvrđeno kodom, **[Z]** zaključeno, **[N]** nepotvrđeno.
> Plan celog modula (overa, čuvanje, izlučivanje): [`plan-arhive-overe-i-cuvanja.md`](../../plan-arhive-overe-i-cuvanja.md).

---

## 1. Šta postoji (od 01.10.2026.) [P]

Prvi deo plana, **faza 1**: šifarnik Liste kategorija i delovodnik sa pisarnicom. Modul radi
**uporedo** sa sadašnjim programom za delovodnik, kao probni rad. Prelazak je predviđen za
01.01.2027. (plan, odeljak 12).

| Ekran | Adresa | Šta radi |
|---|---|---|
| **Pisarnica** | `/arhiva/pisarnica/` | Brzi unos ulazne, izlazne i interne pošte. Posle upisa forma ostaje otvorena sa istim smerom i OJ, a broj se prikazuje u poruci i u spisku današnjih upisa. |
| **Delovodnik** | `/arhiva/` | Upisi za godinu, pretraga (broj, predmet, pošiljalac, broj akta pošiljaoca), filteri po smeru i statusu, 50 po strani. Stornirani upisi ostaju vidljivi. |
| Detalj predmeta | `/arhiva/predmeti/<id>/` | Podaci iz delovodnika, akti sa podbrojevima, novi akt, storno |
| **Lista kategorija** | `/arhiva/kategorije/` | Šifarnik sa rokovima čuvanja, po verziji. Filteri po grupi i vrsti roka. Duplikati su označeni i ne nude se pri izboru. |

Dozvole su imena ruta (`arhiva:delovodnik`, `arhiva:pisarnica`, `arhiva:predmet_detail`,
`arhiva:akt_add`, `arhiva:predmet_storniraj`, `arhiva:kategorije`). Postaju stvarne posle
`manage.py sync_permission_codes`, a Uprava ih dobija automatski.

---

## 2. Delovodni broj [P]

| Pravilo | Kako radi |
|---|---|
| Ko daje broj | Samo `arhiva/services/delovodnik.py: zavedi()`. Forma samo prikuplja podatke. |
| Format | Iz podešavanja: `ARHIVA_FORMAT_BROJA = "{centar}-{broj}"`, `ARHIVA_FORMAT_PODBROJA = "{osnovni}/{podbroj}"` (`ims_erp/settings/base.py`). Podrazumevano `43-15238` i `43-15238/2`, kao brojevi zahteva u Kadrovima. Format je još otvorena odluka (plan, O-1); promena je samo u podešavanjima. |
| Niz | Jedan niz za ceo Institut, za kalendarsku godinu (`EvidencionaKnjiga` + `BrojacKnjige`). Nova godina počinje od 1. |
| Centar u broju | Oznaka centra glavne OJ predmeta, iz registra organizacije: centar daje svoju šifru, OJ šifru nadređenog centra. Na šifru posla se ne zavodi. Oznaka se pamti na predmetu (`oznaka_centra`). |
| Istovremeni upis | Red brojača se zaključava (`select_for_update`, na SQL Serveru UPDLOCK). Unique ograničenje na (knjiga, osnovni broj) i (knjiga, delovodni broj) je druga linija zaštite. **Ne koristi se `MAX()+1`.** |
| Podbroj | Osnovni akt je podbroj 1 i nosi broj predmeta. Odgovori i dopisi su `/2`, `/3` … Predmet se zaključava dok se računa podbroj. |
| Storno | Pogrešan upis se ne briše: status „Storniran", razlog, ko i kada. Broj se ne koristi ponovo. U storniran predmet se ne upisuju novi akti. |
| Zaključenje knjige | `zakljuci_knjigu()` upisuje broj upisa i službenu zabelešku. Posle toga upis nije moguć. Knjiga uvezena iz ranijeg programa (`istorijska`) je samo za čitanje. Ekran za zaključenje još ne postoji. |

---

## 3. Obuhvat [P]

Arhiva je **na registru organizacije od prvog dana** (`PRAVA_PO_REGISTRU["arhiva"] = True`,
`arhiva/access.py`). Predmet pripada centru ili OJ, a ne šifri posla, pa se ne koristi provera
preko putanja šifara posla.

- Predmet se vidi kada mu je **glavna ili dodatna OJ** u obuhvatu odobrene dodele uloge sa nekom dozvolom
  `arhiva:`. Dodeljen centar obuhvata i sve njegove OJ.
- **Zaduženi referent** i onaj ko je predmet **zaveo** uvek ga vide.
- Pisarnica i arhivista dobijaju dodelu **cele firme**.
- `allowed_center_codes` / `allowed_centers` se ne čitaju.

U testovima je prekidač isključen (`testing.py`), a novi put se proverava sa `override_settings`.

---

## 4. Lista kategorija [P]

Uvoz: `manage.py import_lista_kategorija <fajl>` (`arhiva/services/lista.py`).

| Tema | Pravilo |
|---|---|
| Ulaz | Word `.docx` (tabela: redni broj, klasifikaciona oznaka, kategorija, rok) ili Excel sa istim kolonama, npr. očišćena lista od arhiviste. Stari `.doc` se prvo sačuva kao `.docx`. Red bez rednog broja je **grupa** i nosi klasifikacionu oznaku. |
| Rok | „Trajno", „Trajno operativno", „N godina", i „N godina" uz događaj od kog rok teče (prestanak važenja, istek zakupa, okončanje postupka…). Rok koji ne može da se izračuna (npr. „70 godina osim Trajno kod istaknutih ličnosti") dobija „određuje se pojedinačno". |
| Verzije | Svaki uvoz pravi novu verziju. Stare se ne menjaju. Aktivna (`--aktivna`) je samo jedna i samo se ona nudi pri zavođenju. |
| Duplikati | Ista stavka u istoj grupi sa istim rokom označava se kao duplikat prve i ne nudi se pri izboru. Ista stavka sa različitim rokom se ne označava, nego ide arhivisti na odluku. |
| Izveštaj | `--izvestaj sporne.xlsx` (uz `--samo-izvestaj` bez upisa u bazu). List „Sporne stavke" je poređan po važnosti: isti naziv sa različitim rokom; isti dokument sa različitim rokom (ulazni/izlazni računi 10 i 5 godina); duplikati; neobična klasifikaciona oznaka (426); nejasan rok; rok koji teče od događaja; „trajno operativno"; isti naziv u više grupa; pravopis roka. List „Sve kategorije" prikazuje kako je pročitana svaka stavka. |
| Nalaz za Listu od 10.03.2023. | 454 kategorije u 23 grupe, **33 sporne stavke**. Izveštaj je predat arhivskoj službi (`aRhiva-docs/Lista kategorija - sporne stavke za odluku.xlsx`). |

---

## 5. Šta još ne postoji

Dostavne knjige i potvrda prijema, Moji predmeti, završetak predmeta sa obaveznom
kategorijom, otprema (P-3), skenovi i prilozi, veze sa dokumentima drugih modula, prelazak
brojača zahteva iz Kadrova na arhivu, elektronska overa, arhiva, izlučivanje, uvoz starog
delovodnika i ekran za zaključenje knjige. Redosled je u planu (odeljak 12).

---

## 6. Fajlovi

| Šta | Gde |
|---|---|
| Modeli | `arhiva/models.py`: `VerzijaListe`, `GrupaKategorija`, `Kategorija`, `EvidencionaKnjiga`, `BrojacKnjige`, `Predmet`, `Akt` (tabele `arhiva_*`) |
| Broj, podbroj, storno, zaključenje | `arhiva/services/delovodnik.py` |
| Lista: čitanje, provera, uvoz, izveštaj | `arhiva/services/lista.py`, komanda `import_lista_kategorija` |
| Obuhvat | `arhiva/access.py` |
| Ekrani | `arhiva/views.py`, `arhiva/templates/arhiva/`, meni `templates/sidebar_arhiva.html` |
| Testovi | `arhiva/tests.py` |
