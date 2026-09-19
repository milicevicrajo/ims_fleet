# 6.12. Flota — analitika namene, raspolaganja i ekonomskih alternativa

> Metodologija **IMS-FLOTA-2.0**, 19.09.2026. Implementacija u radnoj kopiji;
> primena u produkciji zahteva migraciju i isporuku koda.
> Korisnik je odobrio doradu obračuna i potvrdio: **jedan nalog vozila pripada jednom poslu**.
> Značenje ranijeg polja rate operativnog lizinga nije potvrđeno; zato se ne pretpostavlja.

## E-01 — Zajednička analitika flote i vozila

### E-01.1. Naziv

Ekrani: `/analitika/`, statistika centra i kartica **Troškovi** na detalju vozila.
Oba koriste [`period_analysis()`](../../../fleet/services/economics.py).
Oznaka zbira je **Obuhvaćeni troškovi**, ne ukupan trošak vlasništva.

### E-01.2. Poslovna svrha

Uskladiti prikaz istog vozila u istom periodu na oba ekrana, prikazati poslovnu
namenu i raspolaganje, upozoriti na nedostajuće podatke i omogućiti proverljivu
internu raspodelu na poslove. Posebna procena E-02 poredi buduće alternative.

### E-01.3. Korisnici

Uprava, služba voznog parka i korisnici sa dozvolama za odgovarajuće ekrane.
Prikaz flote zahteva `fleet_analytics`; uređivanje ulaza i izrada procene
`vehicle_update`; pregled sačuvane procene `vehicle_detail`.
Ograničenja centara se primenjuju i na direktne URL adrese.

### E-01.4. Ulazni podaci

| Ulaz | Model / izvor | Pravilo |
|---|---|---|
| Poslovna namena, kriterijumi, izvor goriva | `VehicleAnalysisProfile` | Važi od datuma do sledećeg profila; ne izvodi se iz mase |
| Osnov raspolaganja | `VehicleHolding` | Gleda se svaki dan perioda, ne samo današnje stanje |
| Naknade najma i operativnog lizinga | `LeaseChargePeriod` | Potvrđen iznos, period, mesečni ili ukupni osnov, dokument |
| Kamata finansijskog lizinga | `LeaseInterest` | Godišnji iznos, raspodela samo dok važi ugovorno raspolaganje |
| Gorivo | `TransactionNIS` / `TransactionOMV` ili `FuelConsumption` | Jedan izabrani izvor za svaki datum; nema sabiranja dve evidencije |
| Servisi / trebovanja | `ServiceTransaction` / `Requisition` | Potpisani evidentirani iznosi, uključujući storna |
| Polise | `Policy` | Iznos premije i oba datuma važenja |
| Naknade osiguranja | `Insurance`, `kola=True` | Zaseban priliv, može biti povezan sa ranijom štetom |
| Nalozi i kilometraža | `VehicleTravelOrder` | Otvaranje, zatvaranje, očitanja; novo `job_code` |
| Zastoji | `VehicleDowntime` | Stvarni period neupotrebljivosti, opciona veza sa prijavom |

Poslovne namene su: laboratorijski prevoz; nadzor; uprava; transport mašina i
kontejnera; vozilo sa bušećom mašinom; prevoz/vuča SPT i druge opreme; priključno vozilo.
Tehnička kategorija `Vehicle.category` ostaje zaseban podatak.

### E-01.5. Poreklo podataka

NIS/OMV prolaze postojeće filtere proizvoda i OMV duplikata.
Za OMV kilometražu prednost ima pozitivno korigovano očitanje kada je dostupno.
Zajednički izvor je `get_vehicle_fuel_transaction_rows()`, proširen periodom i skupom
vozila radi grupnog učitavanja. Kada profil izričito bira raniju evidenciju, čita se
`FuelConsumption`. Nepostojeći profil koristi NIS/OMV i prikazuje upozorenje.

Nabavka ostaje dokaz o održavanju. Njene fakture se ne dodaju ponovo servisnim
knjiženjima: to bi moglo duplirati isti trošak. Nasleđeni objekti se ne menjaju.

### E-01.6. Tačan postupak

Period je zatvoren interval, oba krajnja datuma uključena. Dozvoljen je period do
1096 dana razlike, bez budućih datuma. Pogrešan filter ne zamenjuje se podrazumevanim.

**Obuhvaćeni troškovi:**

`gorivo + servisi + trebovanja + premije perioda + potvrđene naknade + kamata perioda`

Nabavna vrednost, glavnica i procenjena knjigovodstvena amortizacija nisu u ovom
zbiru. Trošak kapitala je odvojen u E-02. Gorivo je bruto, a ostali iznosi ostaju u
poreskoj osnovi izvora; nema pretpostavljenog preračuna povrativosti PDV-a.

**Polisa:** `premija × broj dana preklapanja / ukupan broj dana polise`.

**Mesečna naknada:** za svaki dan `mesečni iznos / broj dana tog kalendarskog meseca`.
**Ukupan iznos naknade:** `ukupan iznos / broj dana potvrđenog perioda naknade`.
Naknada ulazi samo tokom odgovarajućeg `VehicleHolding` perioda. Nepokrivena ili
preklopljena istorija raspolaganja ne rešava se nagađanjem.

**Kamata:** `godišnji iznos / 365 ili 366`, za obuhvaćene dane finansijskog lizinga.
Nedostajuća kamata nije potvrđena nula. Kamate kredita nisu automatski obuhvaćene.

**Naknade osiguranja:** prikazane zasebno; dodatni saldo je
`obuhvaćeni troškovi − naknade`. Negativan saldo nije dokaz profitabilnosti vozila.

**Kilometraža:** koristi postojeću logiku opaženih očitanja (`observed_timeline`),
bez ekstrapolacije. RSD/km se prikazuje samo ako očitanja pokrivaju oba granična
datuma, nema pada brojača i razlika je pozitivna. Očitavanja su dnevna; nisu dokaz
tačnog vremena prelaska obračunske granice. Jednodnevni period nema RSD/km.

**Dani po nalogu:** unija kalendarskih dana naloga u periodu. Otvoren nalog se
ograničava krajem izabranog perioda. Ovo je administrativna zauzetost, ne produktivnost.

`RSD/dan po nalogu = obuhvaćeni troškovi celog perioda / jedinstveni dani po nalogu`.
`RSD/kalendarskom danu = obuhvaćeni troškovi / svi dani perioda`.

**Raspodela po poslovima:** interna aproksimacija po vremenu. Trošak perioda se
ravnomerno deli na sve kalendarske dane. Dnevni deo pripada jedinoj potvrđenoj šifri
aktivnog naloga; bez šifre, bez naloga ili pri sukobu poslova ostaje neraspoređen.
Preklapanje naloga sa istim poslom ne duplira trošak. Ova raspodela ne menja knjiženja
i nije tvrdnja da je konkretan posao izazvao trošak popravke.

**Zastoji:** unija evidentiranih dana neupotrebljivosti. Bez evidencije prikazuje se
„nisu evidentirani”, a ne nula ili 100% raspoloživosti.

**Flota / grupa:** zbir iznosa poznatih vozila, sa brojem obuhvaćenih vozila.
Ponderisani RSD/km je `zbir troškova / zbir km` samo vozila sa usklađenim granicama.
Nije aritmetička sredina pojedinačnih stopa. Priključna vozila su uključena.

Sve operacije koriste `Decimal`; za prikaz se zaokružuje na dve decimale. Zbir
poslova i neraspoređenog dela se kontroliše pre prikaznog zaokruživanja.

### E-01.7. Implementacija

| Sloj | Fajl |
|---|---|
| Novi modeli | `fleet/economics_models.py`, uvezeni iz `fleet/models.py` |
| Obračuni / metodologija | `fleet/services/economics.py` |
| Forme | `fleet/forms/economics.py` |
| Flota, ulazi i procene | `fleet/views/analytics.py` |
| Detalj vozila | `fleet/views/vehicles.py` |
| Zajednički prikaz metodologije | `fleet/templates/fleet/_analysis_methodology.html` |
| Testovi | `fleet/test_economics.py`, postojeći testovi Flote |

### E-01.8. Kontrolni primer

Period 01–31.01.2026, troškovi 3.100 RSD, očitanja 10.000 i 11.000 km na granične
datume. Jedan nalog sa potvrđenim poslom pokriva svih 31 dan.

- RSD/km = 3.100 / 1.000 = **3,10**.
- RSD/dan po nalogu = 3.100 / 31 = **100**.
- Raspodela poslu = **3.100**, neraspoređeno = **0**.
- Ako drugi posao ima preklopljeni nalog od 20. januara, **1.200 RSD** ostaje
  neraspoređeno zbog sukoba; prvom poslu pripada **1.900 RSD**.

Za naknadu 31.000 RSD mesečno i raspolaganje po tom ugovoru od 16. do 31. januara,
naknada perioda je **16.000 RSD**. Samo 31. januar daje **1.000 RSD**.

### E-01.9. Rezultat

Istorijska analitika se računa pri prikazu iz tekuće evidencije i nije zamrznuto
knjigovodstvo. Korekcija izvora menja rezultat. Istorija profila čuva promene namene
i kriterijuma. Ekonomska procena E-02 čuva zamrznute ulaze i rezultat.

### E-01.10. Kriterijumi i upotreba

Kontrolni prag je opcion i zahteva tekstualni osnov, datum/izvor, uporediv obuhvat
i izabran način raspolaganja na koji se odnosi. Važi samo za tu kombinaciju namene
i raspolaganja; kod drugačijeg/mešovitog raspolaganja ili nedostajućeg ugovornog
obračuna ne primenjuje se.
Prekoračenje znači **pregled kriterijuma**, ne automatsku zamenu.
Negativan zbir/storno i dokumenti bez iznosa zahtevaju proveru; prag se tada ne primenjuje.
Prag se ne primenjuje kada period obuhvata više profila. Za bušeći sklop i prikolicu
RSD/km se ne može uneti kao merodavan kriterijum opravdanosti.

Operativni profil i ugovorni osnov kombinuju se u matrici na nivou flote. U mešovitom
periodu prikazuje se namena na kraju perioda uz upozorenje; raspolaganje navodi sve
potvrđene osnove perioda.

### E-01.11. Kontrola

1. Izabrati identičan period na floti i vozilu: zbir mora biti jednak.
2. Mesečni zbir mora odgovarati zbiru perioda.
3. Zbir raspodele po poslovima i neraspoređenog dela mora odgovarati ukupnom zbiru.
4. Proveriti dnevno pokriće polise, raspolaganja i ugovorne naknade.
5. Proveriti da faktura za uslugu uključenu u najam nije još jednom uključena u servise.

### E-01.12. Ograničenja

- Nepoznati podaci nisu potvrđene nule; poznata evidentirana nula ostaje nula.
- Potpunost svih ekonomskih troškova nije potvrđena automatskim postojanjem zapisa.
- Posebna mašina/SPT i ekipa nisu automatski uključeni u trošak vozila. Za ceo sklop
  u E-02 moraju biti obuhvaćeni uporedivim ručno obrazloženim scenarijima.
- Ne postoji automatski obračun profita posla: potreban je prihod i svi ostali troškovi.
- Nema pouzdane mere produktivnih sati iz trajanja naloga.
- Stari nalozi nemaju automatski dodeljenu šifru posla. Korisnik potvrđuje vezu.
- Kontrola pristupa prati današnju odgovornost za vozilo. Prikaz istorijskog centra
  koristi dodelu na kraju izabranog perioda.
- `otpis` nema istorijski datum; korisnik može uključiti trenutno otpisana vozila.

### E-01.13. Status pouzdanosti

| Tvrdnja | Status | Dokaz |
|---|---|---|
| Jedan nalog pripada jednom poslu | Potvrđeno korisnikom | Nova direktna veza `job_code` |
| Zbir i periodi usklađeni na oba ekrana | Potvrđeno testovima | Kontrolni primer i testovi prikaza |
| Značenje stare rate operativnog lizinga | Nepotvrđeno | Potreban unos `LeaseChargePeriod` |
| Potpunost produkcionih podataka | Nepotvrđeno | Nije vršena provera baze |
| Stvarni rad mašine i zastoji unazad | Nepotvrđeno | Nema automatskog rekonstruisanja |

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
