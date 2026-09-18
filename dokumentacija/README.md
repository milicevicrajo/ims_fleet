# Dokumentacija

Ovaj folder sadrži funkcionalnu i tehničku dokumentaciju projekta `ims_erp`.

## Sadrzaj

1. `celery-sta-je-uradjeno.md`
Opis konkretnih izmena koje su uradjene u projektu radi stabilnijeg rada Celery-ja na Windows serveru.

2. `celery-taskovi-opsti-vodic.md`
Opsti vodic za arhitekturu, podesavanja, task scheduling i operativu Celery taskova.

3. `opravdanost_radnog_mesta_flota.md`
Obrazlozenje poslovne opravdanosti za osobu koja operativno vodi flotu kroz IMS Fleet aplikaciju.

4. `nabavka-funkcionalnosti-i-povezivanja.md`
Pregled implementiranih funkcionalnosti aplikacije Nabavka, nacina povezivanja zahteva, stavki, EUF faktura, ugovora i narudzbenica, kao i predlog daljih faza razvoja.

5. `nabavka-modeli-zahtevi-euf-uf-roba.md`
Detaljan opis nacina funkcionisanja cetiri osnovne evidencije u Nabavci: zahtevi, EUF fakture, UF fakture i roba, ukljucujuci tvrdo povezivanje i meko poklapanje robe sa UF/EUF fakturama.

6. [Finansijska analitika — metodologija svih prikazanih podataka](finansije-metodologija-obracuna.md)
Izvori, datumi i formule prihoda, rashoda, ZT, rezultata, priliva, odliva i neto gotovine;
grafikoni i procenti; fakture, konta, zaposleni, vozila, zaduženja, putni nalozi i Naplata;
nedostajući podaci, sinhronizacija, kontrolni primeri i veze ka implementaciji.

7. [Plan centralizacije organizacije i šifara posla](plan-centralizacije-organizacije.md)
Tri nivoa organizacije, profitnost i aktivnost, istorija šifara i naziva, snimci na dokumentima,
mapiranje postojećih modula, sinhronizacija i fazni prelazak sa kontrolama i povratkom.

8. [Fakture i prelazak Naplate na lokalni izvor](naplata-lokalni-izvor-plan.md)
Potvrđeni IF/ON filteri, pregled sp_AzurirajNalogZ i zavisnosti Naplate, plan rasporeda
u 10:00 i 11:00, ručno pokretanje, migracija view-ova i osvežavanje šifarnika.

9. [Nova Naplata — Django tabele, sinhronizacija i UI](naplata-nova-aplikacija-plan.md)
Pregled osam stvarnih view-ova i operativnih evidencija, predlog povezanih modela,
nalazi kvaliteta podataka, potvrđena pravila ispravki i važnih kupaca, sinhronizacija,
novi UI, veze sa drugim modulima i postepeni prelazak.
Word izdanje: [Naplata — plan razvoja i struktura podataka](<Naplata - plan i struktura tabela.docx>).
Početna struktura: [potrazivanja README](../potrazivanja/README.md), 19 novih Django tabela
i sedam početnih starosnih razreda; migracije primenjene 18.09.2026, 169 testova prolazi.

- [Potraživanja: paralelni rad i kontrola stvarnog prenosa (18.09.2026.)](potrazivanja-paralelni-prenos-2026-09-18.md) — aktiviranje pored Naplate, obuhvat pune sinhronizacije, iznosi i nepovezani zapisi.
- [Potraživanja: samostalan rad i završni prenos](potrazivanja-samostalan-rad.md) — novi unosi, strukturirani kontakti, pravni postupci, Excel uvoz/izvoz i provera brzine.
