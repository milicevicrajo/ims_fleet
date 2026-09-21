# 6.12. Flota — analitika namene, raspolaganja i ekonomskih alternativa

> Metodologija **IMS-FLOTA-2.1**, 21.09.2026.
> Korisnik je pisano odobrio: trošak prati šifru posla vozila, vlasništvo je
> podrazumevano bez važećeg ugovora, namena može biti procena, iznos se vodi na
> samom lizingu/najmu uz razliku mesečni/ukupni, a zastoji nisu potreban ulaz.
> Pravila 2.1 zamenjuju prethodnu raspodelu prema poslu putnog naloga i obaveznu
> istoriju VehicleHolding / odvojene periode LeaseChargePeriod.

## E-01 — Zajednička analitika flote i vozila

### E-01.1. Naziv i prikaz

Ekrani `/analitika/`, statistika centra i kartica **Troškovi** na detalju vozila
koriste isti `fleet.services.economics.period_analysis()`.
Naziv zbira je **Obuhvaćeni troškovi**, ne ukupan trošak vlasništva.

Kartica Troškovi ima tri celine: rezultat obračuna; ugovori lizinga/najma;
izvorne stavke. Izbor perioda nudi ovaj mesec, poslednja tri meseca, poslednjih
12 meseci, ovu i prošlu godinu, kao i proizvoljne datume. Upozorenja su vidljiva.
Razrada po poslovima i mesecima i pojedinačne stavke otvaraju se po potrebi.
Metodologija se prikazuje na jednoj stranici `/analitika/metodologija/`.

Ekran **Namena i kriterijumi** sadrži procenu namene, obrazac za potvrđen profil,
istoriјu dodela šifre posla i veze na postojeće ugovore. Nema dodatnog obrasca
za ugovornu naknadu, posao putnog naloga ili neupotrebljivost.
Pregled ulaza ima šest stavki: namena, raspolaganje, ugovorni iznos/kamata,
kilometraža, šifra posla vozila i opcion kontrolni prag. Procena namene je
posebno označena i ne blokira obračun.

Ugovor prikazuje zasebno **mesečni iznos** i **ukupno za ugovor**. Ako je unet
mesečni iznos, ukupno je izvedeno po kalendarskim danima važenja. Ukupni iznos
se ne predstavlja kao mesečna rata. Preostala obaveza računa se za preostali
period ugovora, uključujući različite dužine meseci; nije dug jer se uplate
ne prate. Iznos se uređuje neposredno na ekranu postojećeg ugovora.

### E-01.2. Poslovna svrha

Prikazati evidentirane troškove i pripisati ih šifri posla na koju se vozilo
vodilo na odgovarajući datum. Posebna procena E-02 poredi buduće alternative.

### E-01.3. Korisnici i dozvole

Uprava, služba voznog parka i korisnici sa dozvolama za odgovarajuće rute.
Nove rute nisu dodate. Koriste se `fleet_analytics`, `center_statistics`,
`vehicle_analysis_settings`, `vehicle_assessment_create` i
`vehicle_assessment_detail`; unos ugovora koristi `lease_create` / `lease_update`.
`sync_permission_codes` izvodi dozvole analitike iz postojećih dozvola za
pregled i izmenu vozila. Kontrola centra na analitici prati sadašnje zaduženje;
prikaz istorijskog centra uzima dodelu na kraju izabranog perioda.

### E-01.4. Ulazni podaci

| Ulaz | Izvor | Pravilo |
|---|---|---|
| Šifra posla vozila | JobCode + OrganizationalUnit | Poslednja dodela čiji datum nije posle obračunskog dana |
| Raspolaganje | Lease | Jedan važeći ugovor za dan; bez ugovora vlasništvo IMS |
| Naknada lizinga/najma | Lease.current_payment_amount + payment_basis | monthly ili total, za period samog ugovora |
| Kamata finansijskog lizinga | LeaseInterest | Godišnji iznos, samo za dane važećeg ugovora |
| Namena | VehicleAnalysisProfile ili početna procena | Potvrđen profil ima prednost |
| Gorivo | NIS/OMV ili izabrani FuelConsumption | Samo jedan izvor po datumu |
| Održavanje | ServiceTransaction + Requisition | Iznosi na datum dokumenta, uključujući storna |
| Premije | Policy | Premija i oba datuma važenja |
| Naknade osiguranja | Insurance, kola=True | Poseban priliv |
| Kilometraža / korišćenje | Gorivo + VehicleTravelOrder | Očitavanja i administrativni dani naloga |

VehicleHolding, LeaseChargePeriod i VehicleDowntime ostaju sačuvani radi
istorije, ali ne određuju obračun 2.1. `VehicleTravelOrder.job_code` takođe
ne određuje pripadnost troška vozila. U analitici se ne traži popunjavanje tih
podataka. Postojeći zapisi se ne brišu.

### E-01.5. Poreklo i početna procena

NIS/OMV koriste postojeće filtere proizvoda i OMV duplikata preko
`get_vehicle_fuel_transaction_rows()`. Bez profila izvor goriva je NIS/OMV.
Nabavka služi kao dokaz; njene fakture ne sabiraju se ponovo sa servisima.

Početna namena se izvodi pri prikazu, bez masovnog upisa potvrđenih profila:
priključna kategorija daje priključno vozilo; opis i naziv dodeljene šifre posla
mogu predložiti laboratorijski prevoz, nadzor, upravu, transport, bušenje ili
vuču. Bez posebnog signala početna procena je nadzor i terenski rad.
Procena je označena na detalju i listi i može se promeniti unosom profila.
Težina vozila i ime zaposlenog nisu dokaz namene. Procena ne stvara kontrolne
pragove i ne predstavlja potvrdu istorijske namene.

Migracija `0078_lease_payment_basis` dodaje značenje iznosa na Lease i
razvrstava postojeće operativne ugovore kao ukupni iznos, a dugoročne najmove
kao mesečni, prema postojećim uputstvima unosa i dogovoru 21.09.2026.
Postojeći novčani iznosi i datumi se ne menjaju. Finansijski iznosi ostaju bez
pretpostavljenog značenja, a obračun i dalje koristi samo zasebnu kamatu.

### E-01.6. Tačan postupak

Period je zatvoren interval, oba krajnja datuma uključena, bez budućnosti i
najviše 1096 dana razlike. Neispravan filter se ne zamenjuje drugim periodom.

**Obuhvaćeni troškovi:**

`gorivo + servisi + trebovanja + premije perioda + naknade perioda + kamata perioda`

Nabavna vrednost, glavnica, amortizacija i kreditna kamata nisu automatski u
zbiru. Naknade osiguranja prikazuju se zasebno; dodatni saldo je zbir minus
naknade. Negativan saldo nije profit vozila. Gorivo je bruto, ostalo je u
poreskoj osnovi izvora.

**Raspolaganje po danu:** važeći Lease određuje finansijski/operativni lizing
ili najam. Ako ga nema, dan je vlasništvo IMS, uključujući dane pre i posle
ugovora. Više važećih ugovora je konflikt: naknade za te dane se ne sabiraju,
a konflikt je prikazan. Poseban unos osnova vlasništva nije potreban.

**Mesečna naknada:** `iznos / broj dana konkretnog kalendarskog meseca` za svaki
obuhvaćeni dan ugovora. **Ukupni iznos:** `iznos / broj dana ugovora`.
Polisa: `premija / broj dana polise` za svaki dan preklapanja.
Finansijska kamata: `godišnja kamata / 365 ili 366`, samo tokom ugovora.
Nedostajući iznos ili značenje iznosa ne zamenjuje se nulom. Poznata nula ostaje nula.

**Raspodela na poslove:** gorivo, servis i trebovanje pripadaju šifri posla
vozila na datum dokumenta. Dnevni deo polise, ugovorne naknade i kamate pripada
šifri važećoj tog dana. Nova dodela važi od svog datuma, prethodna do dana pre
nje. Buduća dodela se ne primenjuje unazad. Prazna dodela ne vraća prethodnu.
Bez dodele, trošak tog dana ostaje neraspoređen. Troškovi se više ne dele
ravnomerno na sve dane celog izabranog perioda. Putni nalozi, njihovi poslovi,
otvaranje/zatvaranje i preklapanja ne menjaju raspodelu. Ovo je analitička
raspodela, bez izmene izvornog knjiženja.

**Kilometraža (dopuna 21.09.2026):** za početak i kraj perioda usvajaju se
najbliži stvarni datumi očitavanja iz NIS/OMV i naloga zaduženja, uključujući
datume van perioda. Ranija evidencija goriva dopunjava dane bez direktnog
očitanja; izbor izvora troška ne ograničava izbor očitanja. Pozitivno OMV
korigovano stanje ima prednost. Na isti dan koristi se najveće stanje.
Kod jednake udaljenosti bira se raniji početak i kasniji kraj. Nema
interpolacije, ekstrapolacije ni skrivenog ograničenja udaljenosti; stvarni
datumi, stanja, izvori i odstupanje u danima prikazani su uz rezultat.
`nearest_period` bira granice, a `observed_timeline` proverava padove između
njih. Dva različita datuma su obavezna; za jednodnevni zahtev nema razlike km.
RSD/km postoji uz pozitivnu razliku bez pada brojača. Ako granice odstupaju,
rezultat je označen kao približan. Troškovi ostaju isključivo u traženom periodu.
Dani naloga su unija dana administrativnog zaduženja; nisu produktivnost.
Dan primopredaje pripada novom nalogu. RSD/dan po nalogu je trošak celog
perioda podeljen jedinstvenim danima naloga. Ovi pokazatelji su odvojeni od
pripadnosti troška. Evidencija neupotrebljivosti se ne prikazuje niti traži.

Sve operacije koriste Decimal; prikaz je na dve decimale. Zbir poslova i
neraspoređenog dela kontroliše se pre prikaznog zaokruživanja.
Ponderisani RSD/km flote koristi vozila sa obračunatim RSD/km i može biti približan.

### E-01.7. Implementacija

- Obračun: `fleet/services/economics.py`.
- Podrazumevana namena i raspolaganje: `fleet/support/analysis_defaults.py`.
- Dnevni iznos i suma perioda ugovora: `fleet/support/lease_costs.py`.
- Unos iznosa: postojeći LeaseForm i forma prvog unosa vozila.
- Regresije: `fleet/test_economics.py`, `fleet/test_analysis_defaults.py`.

### E-01.8. Kontrolni primer

01–31.01.2026: gorivo 1.000 RSD 1. januara i 2.100 RSD 31. januara.
Šifra P1 važi od 1. januara, P2 od 16. januara. Bez ijednog putnog naloga:
P1 dobija **1.000**, P2 **2.100**, neraspoređeno **0 RSD**.

Ako uz to postoji mesečna naknada 31.000 RSD za ceo januar, P1 dobija još
**15.000**, P2 još **16.000 RSD**. Samo naknada ugovora koji počinje
16. januara iznosi **16.000 RSD**, a 31. januar pojedinačno **1.000 RSD**.

Naknada 31.000 RSD mesečno od 16.01. do 15.03.2024: 16.000 + 31.000 +
15.000 = **62.000 RSD**, uključujući prestupni februar. Ukupna ugovorna
naknada 31.000 RSD za 01–31.01.2026 daje isti dnevni iznos 1.000 RSD.

Kilometraža za januar: očitavanja 31.12.2025 = 1.000 km, 15.01.2026 =
1.500 km, 01.02.2026 = 2.000 km. Usvajaju se 31.12. i 01.02, razlika je
**1.000 km**, približno za januar. Ako su računi 9.000, 100 i 8.000 RSD na
tim datumima, januarski trošak ostaje **100 RSD**, približni RSD/km **0,10**.

### E-01.9. Rezultat

Istorijska analitika se računa iz tekuće evidencije; korekcija izvora menja
rezultat. Potvrđeni profili imaju datume važenja. Procene E-02 čuvaju snimak.

### E-01.10. Kriterijumi

Prag je opcion i traži pisan osnov i uporedivo raspolaganje. Ne primenjuje se
na procenjenu namenu bez profila, mešovite profile, konfliktne ugovore ili
nepotpun ugovorni iznos. Prekoračenje je signal za pregled, ne automatski otpis.
Bušeći sklop i prikolica nemaju RSD/km kao merodavan kriterijum opravdanosti.

### E-01.11. Kontrola

1. Isti period na floti i vozilu daje isti zbir.
2. Zbir meseci odgovara periodu.
3. Zbir poslova i neraspoređenog dela odgovara periodu.
4. Promena posla na datum dokumenta prebacuje taj trošak na novu šifru.
5. Ugovor bez istorije raspolaganja i bez posebne naknade radi neposredno.
6. Dva ugovora za isti dan se ne sabiraju.
7. Proveriti da usluge uključene u najam nisu ponovljene u servisima/polisama.

### E-01.12. Ograničenja

Podrazumevano vlasništvo je dogovoreno pravilo analitike, ne rekonstrukcija
pravnog sticanja. Datum otpisa nema istoriju. Izostanak evidentiranog troška
nije dokaz da troška nije bilo. Nema automatske procene prihoda posla,
produktivnih sati, tržišne vrednosti ili troška posebne mašine/ekipe.
Ograničenja centara prate današnje zaduženje; vozilo bez dodele ostaje vidljivo.
Izbor centra prikazuje vozila dodeljena centru na kraju izabranog perioda,
a raspodela poslova tih vozila i dalje prati stvarne istorijske dodele.

### E-01.13. Status pouzdanosti

Pravila 2.1 potvrđena su korisnikom 21.09.2026. Računanje je pokriveno
kontrolnim primerima i testovima; potpunost poslovnih izvora time nije potvrđena.
Procena namene je jasno odvojena od potvrđenog profila i ne upisuje se kao
potvrđen istorijski podatak.

## E-02 — Sačuvano poređenje budućih alternativa

Procena ima jedan datum, horizont 1–20 godina, realnu diskontnu stopu, planirane km
i dane, isti obuhvat posla i navedene izvore. Unose se najmanje dve alternative,
od kojih je tačno jedna zadržavanje. Izvodljivost svake alternative potvrđuje korisnik.

Vrste: zadržavanje, kupovina/zamena, lizing/najam i spoljna usluga. Finansijski lizing
se za ekonomsku procenu modeluje kroz uporedivu nabavku sredstva, a njegov plan
plaćanja ostaje zasebno pitanje likvidnosti.

Za svaku alternativu unose se `C0` (početna vrednost/izdatak), `A` (isti godišnji
trošak u današnjim cenama) i `S` (neto preostala vrednost na kraju).
Kod zadržavanja `C0` je današnja tržišna vrednost, ne istorijska nabavna vrednost.
Nema sabiranja pune nabavke, amortizacije i otplate iste glavnice.

Za `n` godina i realnu diskontnu stopu `r`:

```
faktor = zbir [1 / (1 + r)^t], t = 1 ... n
PV = C0 + A × faktor − S / (1 + r)^n
EAC = PV / faktor
```

Pri r = 0 faktor je n. Godišnji izdaci i preostala vrednost pripadaju kraju godine.
Model ne raspoređuje zasebne vanredne izdatke po godinama i ne obračunava inflaciju,
poreske štitove ili kurs. Korisnik usaglašava obuhvat i osnovu iznosa svih alternativa.
Nije plan otplate kredita ili finansijskog lizinga.

Rangiraju se samo izvodljive alternative. Bez izvodljivog zadržavanja i najmanje
još jedne izvodljive alternative nema preporuke zamene. EAC/km i EAC/dan koriste
isti planirani godišnji obim za sve opcije. Razlika prema zadržavanju nije garantovana
ušteda; važi samo pod navedenim pretpostavkama.

**Kontrolni primer:** 5 godina, r=0. Zadržavanje: C0=1.000.000, A=300.000,
S=200.000 RSD. PV=2.300.000, EAC=460.000 RSD/god.
Najam: C0=0, A=400.000, S=0. PV=2.000.000, EAC=400.000 RSD/god.
Razlika je **60.000 RSD/god.** u korist najma ako je on izvodljiv i istog obuhvata.

`VehicleEconomicAssessment.snapshot` čuva sve ulaze scenarija, formule/metodologiju,
rezultat, verziju i preporuku. Naknadne izmene vozila ne menjaju sačuvani rezultat.
Za osetljivost na manji/veći obim rada pravi se nova procena sa izmenjenim ulazima.
Preporuka ne menja `Vehicle.otpis` i ne izvršava poslovne procedure.

## Uvođenje i prelaz sa ranije analitike

1. Isporučiti kod i primeniti migraciju `0077_vehicletravelorder_job_code_leasechargeperiod_and_more` u planiranom okruženju.
2. Pokrenuti `sync_permission_codes`: nove rute nasleđuju odgovarajuće dozvole pregleda/izmene vozila.
3. Za svako vozilo potvrditi istoriju raspolaganja, namenu i izbor izvora goriva.
4. Potvrditi periode i značenje naknada ugovora; ništa se ne izvodi iz nejasne stare rate.
5. Dopuniti šifre posla na nalozima i početi evidenciju stvarnih zastoja.
6. Pripremiti tržišne procene i uporedive ponude za E-02.

Nasleđene funkcije `vehicle_cost_per_km_rows()` i pragovi po masi ostaju radi
kompatibilnosti postojećeg koda/testova; nova `/analitika/`, statistika centra i
analitika na vozilu ih ne koriste. Statistika centra sada prikazuje isti obračun
sa filtrom istorijske dodele na kraju izabranog perioda i dozvolom `center_statistics`.
