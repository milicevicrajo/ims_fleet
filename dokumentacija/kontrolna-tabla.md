# Kontrolna tabla — 10.09.2026.

Trenutni operativni pregled iz `fleet/support/fleet_snapshot.py`. Datum je `timezone.localdate()`. Aktivna vozila (`otpis=False`) dobijaju poslednju dodelu OJ sa datumom do danas, po datumu i ID-u. Svi brojači i redovi centara računaju se iz iste liste vozila. Dozvoljeni centri korisnika ograničavaju taj skup. Bez dodele postoji red Bez centra; arhivirana vozila su odvojena.

Prikazuju se kategorije, jedinstvena zadužena vozila, važeća AO, prosek validnih godišta i zbir unetih knjigovodstvenih vrednosti uz obuhvat. Nema pretpostavljanja računovodstvenog preseka ili zamene nepoznatog nulom. Budući AO i kasko nisu trenutna AO. Više istovremenih zaduženja daje jedno vozilo u brojaču i upozorenje. Zaduženje zatvoreno na današnji datum ne smatra se otvorenim.

Upozorenja se otvaraju ispod zaglavlja. Registracija se proverava samo iz eksplicitnog roka najnovije izdate saobraćajne. Razlikuju se nedostajući rok, istek i rok u 30 dana. Evidentirano produženje polise bez prekida pokrića uklanja upozorenje o isteku te polise. Broj kategorija upozorenja nije zbir vozila; mogu se preklapati.

Uklonjena je crvena zona sa kontrolne table. Istorijski troškovi više se ne pripisuju trenutnom centru na ovom ekranu. Posebni raniji analitički ekrani nisu prepisani ovom promenom. Otvaranje centra na novoj tabli prikazuje aktuelna vozila i OJ u istom ekranu.

Nezavisna SQL provera raspodele: 164 aktivna vozila, 9 centara, 112 putničkih, 49 teretnih, 3 priključna; 8 otpisanih. Sačuvano u `izvestaji/provera_kontrolne_table_20260910.json`. Zbir centara odgovara zbirnim brojačima. Podaci su provereni prema evidenciji, ne kroz fizički popis ili finansijsko usaglašavanje.

Provere: 45/45 testova kontrolne table, unosa i detalja; širi paket 137/139 sa dva prethodno poznata pada. Chrome provera sklopivih upozorenja, centara i nove forme prolazi. Nema novih migracija. Word presek sadrži dopunu 10 sa metodologijom i slikama.
