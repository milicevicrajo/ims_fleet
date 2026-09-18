# Detalj vozila — 10.09.2026.

Poslednja dopuna: Raspolaganje/OJ/ugovori/polise sada koriste mini liste umesto tabela. Prve tri stavke su vidljive, a ostatak je u elementu `details` (Još N). Uklonjena je prečica Poslednjih 12 meseci. Novi unos ima opcionu sliku u prvom koraku (JPG/PNG/WebP do 5 MB), koja se po potvrdi prikazuje na detalju. Dodato je polje `Vehicle.photo` i primenjena migracija 0075; postojeće vrednosti 172 vozila su poređene i očuvane. Slika i dokumenti imaju odvojene privremene datoteke i zajedničko čišćenje pri neuspehu završnog upisa. Poslednje provere: 39/39 testova unosa/detalja, širi paket 131/133 sa ista dva poznata pada; Chrome provera lista, otvaranja dodatnih zapisa i izbora/zadržavanja slike prolazi. Ova dopuna ima prednost nad ranijim opisom tabela i ranijim brojem testova ispod.

Dosije ima pet tabova unutar jedne kartice: Podaci, Raspolaganje i polise, Troškovi, Korišćenje i Dokumenti. Unutrašnje kartice Podaci i Raspolaganje u istom redu imaju iste visine. Stanje registracije, trenutni osnov raspolaganja, OJ i polise prikazuju se na današnji dan, nezavisno od izabranog perioda troškova.

Po naknadnom izričitom pravilu korisnika, bez tekućeg VehicleHolding zapisa i važećeg Lease ugovora prikazuje se **Vlasništvo IMS**. Postojeći tekući zapis ima prednost; inače važeći Lease određuje ugovorno raspolaganje. Ovo je pravilo prikaza na detalju, ne migracija datuma vlasništva niti promena svih zbirnih izveštaja.

Ako eksplicitni rok registracije nedostaje, zaglavlje prikazuje datum poslednje započete polise autoodgovornosti (`insurance_type` sadrži AUTOODGOVORNOST), uz oznaku AO i izvora. Kasko nije izvor registracije. Datum polise nije automatski upisan u saobraćajnu. U Dokumentima se aktuelna saobraćajna prikazuje jednom, a istorija samo ako ima prethodnih dokumenata.

`fleet/support/vehicle_detail.py` validira period i računa evidentirane iznose. Podrazumevani interval pokriva prethodnih 11 i tekući kalendarski mesec do danas; granice su uključene, maksimum je 1096 dana. Nevalidan interval ne prikazuje finansijske rezultate.

- Gorivo/AdBlue: postojeći zajednički izvor NIS/OMV, bruto iznos. Dodat je naziv proizvoda u redovima izvora.
- Održavanje: `ServiceTransaction.potrazuje` po `datum` + `Requisition.vrednost_nab` po `datum_trebovanja`.
- Naknade: `Insurance.potrazuje`, samo `kola=True`, po `datum`; prikazane zasebno.
- Mesečne kolone razlikuju odsutne stavke i evidentiranu nulu. Kategorije uključuju oba izvora održavanja i nisu ograničene na prvih osam.
- Kilometraža je razlika očitanja sa računa uz navedene datume pokrivenosti; opadanje između dana blokira rezultat. Nema godišnje ekstrapolacije.

Nije implementiran kompletan TCO: gorivo je bruto, dok su ostali iznosi u izvornoj evidenciji; premije, finansiranje, amortizacija i praćenje nisu periodizovani. Uklonjeni su nepouzdana ocena isplativosti i procenjena cena/km sa ovog detalja. Ostali zbirni ekrani analitike nisu prepravljeni ovom iteracijom.

Za novi detalj nema dodatnih migracija. Prethodno izvedene migracije 0073/0074 bile su opisane u uklonjenom `unos-vozila-carobnjak.md`.

Datumski filter koristi `data-native-date` kako ga zajednički Flatpickr inicijalizator ne bi protumačio kao tekstualni datum drugog formata. Tabovi koriste API koji postoji u instaliranom Bootstrap 5.0.0-beta1. Tabele imaju posebne identifikatore kako zajednički skript ne bi ponovo inicijalizovao DataTables. Inicijalizacija lokalnih tabela uključuje pretragu i straničenje; redovi se i dalje učitavaju iz izabranog perioda na serveru.

Zajednički `global_datatables.js` dodatno proverava da DatatableServiceDetail nije već inicijalizovan, a njegova verzija u base.html je osvežena. Tabele korišćenja koriste sopstvene ID-jeve, prikazuju d.m.Y, a sortiraju datume preko `data-order` (najnovije prvo). Koristi se naziv Zaduženja vozila. Dugmad dodavanja saobraćajne i ZIP preuzimanja uklonjena su iz zaglavlja; nova saobraćajna se dodaje kroz Dokumente.

Provere: 11 novih testova detalja + 25 prethodnih testova unosa/modela prolaze. Širi paket 128/130, sa ista dva prethodno potvrđena pada u pretrazi naloga bez korisničkih prava i dodatnoj vezi fakture sa šifrom posla. Chrome provera na privremenoj bazi: pet kartica, datumi očuvani nakon potvrde, tabela goriva sa proizvodom, prazne DataTables tabele, sortiranje zaduženja, jednake visine kartica i širine desktopa 1440/1920/2560. Snimci `detalj_vozila_*.png` koriste demonstracione podatke. Po zahtevu korisnika nema daljeg rada na mobilnom prikazu; uklonjen je limit širine od 1600 px da bi sadržaj koristio raspoloživu širinu desktopa i pri zoom-out prikazu.

Korisnikov radni dokument bio je `Presek stanja - primedbe i odgovori.docx` (33 primedbe, odgovori i status svake tačke). Taj dokument je, zajedno sa direktorijumom `dokumentacija/arhiva/`, uklonjen iz repozitorijuma 18.09.2026.; sadržaj je prešao u objedinjenu dokumentaciju u [`docs/`](docs/), a stare verzije ostaju dostupne kroz git istoriju.
