"""Curated navigation and processes. Model inventories are extracted from source."""

MODULES = {
 'fleet': ('Flota', 'Vozila, garaža, gorivo, putni nalozi i ekonomika', '#277b75', [
   ('vozila','Vozila i dodele','Vehicle|TrafficCard|JobCode|Incident', ['VehicleAnalysis','VehicleEconomic','VehicleDowntime','VehicleEvidence','VehicleTravel','VehicleHolding']),
   ('gorivo','Gorivo i potrošnja','Fuel|TransactionOMV|TransactionNIS',[]),
   ('garaza','Garaža i održavanje','Service|Kvar|Requisition|Procurement',[]),
   ('ugovori','Zakup i osiguranje','Lease|Policy|Insurance|Holding|Kasko|Konta',[]),
   ('nalozi','Putni nalozi','PutniNalog|VehicleTravelOrder',[]),
   ('analitika','Ekonomske analize','VehicleAnalysis|VehicleEconomic|VehicleDowntime|VehicleEvidence',[])]),
 'hr': ('Kadrovi', 'Zaposleni, radno vreme, odsustva, zahtevi i rešenja', '#3778a3', [
   ('zaposleni','Zaposleni','^Employee$|EmployeeCVItem|RecipientType',[]),
   ('dokumenti','Zahtevi i rešenja','Zahtev|Resenje|Potpisnik',[]),
   ('rad','Radno vreme','WorkTime',[]),
   ('odsustva','Odmori i bolovanja','AnnualLeave|SickLeave',[]),
   ('ocene','Ocenjivanje','Evaluation',[])]),
 'finansije': ('Finansije', 'Analitika poslova, knjiženja, tok gotovine i banke', '#277b75', [
   ('knjizenja','Poslovi i knjiženja','FinanceJob|LedgerEntry',[]),
   ('sinhronizacija','Sinhronizacije','SyncRun|NalogZ',[]),
   ('banke','Banke i plasmani','Bank',[])]),
 'nabavka': ('Nabavka', 'Predmeti, stavke, fakture, narudžbenice i plan nabavki', '#277b75', [
   ('predmeti','Predmeti i narudžbenice','ProcurementCase|ProcurementItem$|PurchaseOrder|StatusLog',[]),
   ('fakture','Fakture i povezivanje','Invoice|ContractLink', ['Snapshot']),
   ('izvori','Snimci izvora','Snapshot',[]),
   ('plan','Plan javnih nabavki','PublicProcurement',[])]),
 'potrazivanja': ('Potraživanja', 'Dugovanja, dospeća, kontakti, opomene i pravni predmeti', '#8a6933', [
   ('dugovanja','Dokumenti i salda','FinancePartner|InvoiceDocument|Receivable|DueDate|Balance|CollectionState|Aging|ElectronicInvoice',[]),
   ('naplata','Operativna naplata','CollectionProfile|CollectionContact|ContactPoint|CollectionActivity|CollectionNotice',[]),
   ('predmeti','Pravni predmeti','Legal',[]),
   ('uvoz','Uvoz i revizija','Sync|Import|Source|Audit|Timestamped|UserTracked',[])]),
 'pravna': ('Pravna služba', 'Pravni i disciplinski postupci, tok i mere', '#8a6933', [
   ('pravni','Pravni postupci','^Postupak$|PromenaPostupka',[]),
   ('disciplinski','Disciplinski postupci','Disciplinski|TokPostupka',[])]),
 'ugovori': ('Ugovori', 'Partneri, zahtevi, ponude, ugovori, dokumenti i garancije', '#8a6933', [
   ('partneri','Partneri, zahtevi i ponude','Partner|BusinessRequest|Offer',[]),
   ('ugovori','Ugovori i strane','^Contract$|ContractType|ContractParty',[]),
   ('dokumenti','Dokumenti i obezbeđenja','ContractDocument|ContractMenica|ContractGuarantee',[])]),
 'menice': ('Menice', 'Ulazne i izlazne menice i registar NBS', '#8a6933', [
   ('izlazne','Izlazne menice','^Menica$',[]),('ulazne','Ulazne menice','Ulazna',[])]),
 'mobilni': ('Mobilna telefonija', 'Paketi, korisnici, zaduženja, potrošnja i obustave', '#3778a3', [
   ('evidencija','Paketi i zaduženja','Package|User|Assignment',[]),
   ('potrosnja','Potrošnja i uvoz','Usage|Exemption|ImportLog',[])]),
 'isplate': ('Isplate', 'Virmani i konverzije bankarskih datoteka', '#277b75', [
   ('podaci','Podaci iz drugih modula','',[])]),
 'core': ('Administracija', 'Korisnici, uloge, dozvole, organizacione šifre i istorija', '#526687', [
   ('pristup','Korisnici i dozvole','CustomUser|Role|Permission',[]),
   ('evidencija','Šifre i istorija','OrganizationalUnit|ActivityLog|TaskHistory',[])]),
 'organizacija': ('Organizacija', 'Registar centara, OJ i poslova, verzije i obuhvat prava', '#526687', [
   ('registar','Čvorovi, verzije i putanje','OrgNode|OrgPutanja|JobActivityReview',[]),
   ('prava','Dodele uloga','DodelaUloge',[]),
   ('uvoz','Mapiranja i uvoz','Mapping|Legacy|Import|Unresolved',[])]),
 'naplata': ('Nasleđena naplata', 'Postojeće evidencije; novi razvoj ide u Potraživanja', '#8b7770', [
   ('evidencija','Kontakti i akcije','Kontakti|Napomene|Opomene|Poziv|Tuzbe|Avans',[]),
   ('izvori','Nasleđeni izvori i šifre','Baza|Dodela|Ispravke|Partneri|Sif',[])])
}

# Activity nodes: (id, label, model link or empty, optional shape).
def chain(module, slug, title, labels, sources, note=''):
    nodes=[('start','Početak','','circle')]
    nodes += [(str(i), label, model, 'box') for i,(label,model) in enumerate(labels)]
    nodes += [('end','Kraj','','doublecircle')]
    return dict(module=module, slug=slug,title=title,nodes=nodes,
                edges=[(nodes[i][0],nodes[i+1][0],'') for i in range(len(nodes)-1)],sources=sources,note=note)

FLOWS = [
 chain('hr','zahtev-resenje','Od zahteva do izdatog rešenja',[
   ('Unos zaposlenog, vrste i podataka zahteva','hr.Zahtev'),
   ('Sačuvaj zahtev; pripremi broj i dokument','hr.Zahtev'),
   ('Dodaj rešenje iz postojećeg zahteva','hr.Resenje'),
   ('Proveri zahtev i jedinstvenost veze','hr.Resenje'),
   ('Dopuni nacrt rešenja i potpisnika','hr.Potpisnik'),
   ('Validacija izdavanja i čuvanje dokumenta','hr.Resenje'),
   ('Pregled i štampa izdatog rešenja','hr.Resenje')],
   ['hr/services/zahtevi.py','hr/services/resenja.py','hr/resenja_views.py'],
   'Sažet uspešan tok. Storniran zahtev i zauzeta veza sprečavaju novo rešenje; potpisnik se proverava pri izdavanju.'),
 chain('hr','radna-lista','Radna lista zaposlenog',[
   ('Izbor perioda i dozvoljenih zaposlenih','hr.Employee'),
   ('Čitanje izvora prolazaka i radnih evidencija','hr.WorkTimeSheet'),
   ('Priprema podataka za radnu listu','hr.WorkTimeSheetLine'),
   ('Pregled i dopuna evidencije u okviru dozvola','hr.WorkTimeSheet')],
   ['hr/services/attendance.py','hr/services/work_time_prefill.py','hr/views.py'],
   'Izvor kontrole pristupa je spoljni sistem. Nedostajući prolasci nisu isto što i nula radnih sati.'),
 chain('fleet','zaduzenje','Zaduženje i zatvaranje putnog naloga vozila',[
   ('Izaberi vozilo, zaposlenog i datum','fleet.VehicleTravelOrder'),
   ('Provera datuma i postojećih naloga','fleet.VehicleTravelOrder'),
   ('Sačuvaj novi nalog i njegov broj','fleet.VehicleTravelOrder'),
   ('Zatvori ranije otvorene naloge istog vozila','fleet.VehicleTravelOrder'),
   ('Korišćenje vozila; ručno zatvaranje po potrebi','fleet.VehicleTravelOrder'),
   ('Gorivo za vozilo / tablicu i period, obračun i štampa','fleet.TransactionOMV')],
   ['fleet/views/vehicle_travel_orders.py','fleet/forms/putni_nalozi.py','fleet/support/fuel.py'],
   'Novi nalog zatvara ranije otvorene datumom svog početka; prenosi kilometražu ako je uneta. Gorivo nema FK na nalog.'),
 chain('fleet','gorivo','Uvoz goriva i priprema potrošnje',[
   ('Preuzimanje NIS / OMV izveštaja','fleet.TransactionNIS'),
   ('Normalizuj tablicu i razreši vozilo','fleet.TrafficCard'),
   ('Odredi šifru posla na datum točenja','fleet.JobCode'),
   ('Sačuvaj odgovarajuću evidenciju goriva','fleet.FuelConsumption'),
   ('Filter proizvoda i OMV duplikata pri čitanju','fleet.TransactionOMV'),
   ('Potrošnja i izveštaji po vozilu','fleet.Vehicle')],
   ['fleet/sync/selenium.py','fleet/support/assignments.py','fleet/support/fuel.py'],
   'Ne pogađa se vozilo za nejednoznačnu tablicu. Profil ekonomike bira transactions ili legacy izvor; evidencije se ne sabiraju dvostruko.'),
 chain('finansije','sinhronizacija','Od izvora knjiženja do finansijskog pregleda',[
   ('Izbor firme i perioda sinhronizacije','finansije.SyncRun'),
   ('Čitanje udaljenog izvora i poslova','finansije.FinanceJob'),
   ('Usklađivanje lokalnih stavki i kontrolnih zbirova','finansije.LedgerEntry'),
   ('Zabeleži rezultat sinhronizacije','finansije.SyncRun'),
   ('Izbor posla, centra i perioda za analitiku','finansije.FinanceJob'),
   ('Prikaz prihoda, rashoda i povezanih analiza','finansije.LedgerEntry')],
   ['finansije/services/source.py','finansije/services/sync.py','finansije/services/reports.py'],
   'Deo analiza čita udaljene izvore pri otvaranju. Osvežavanje lokalnog nalog_z je poseban, kontrolisan servis.'),
 chain('nabavka','predmet','Predmet nabavke, stavke i fakture',[
   ('Unos predmeta, šifre posla i odgovornih podataka','nabavka.ProcurementCase'),
   ('Dodavanje stavki predmeta','nabavka.ProcurementItem'),
   ('Priprema narudžbenice prema predmetu','nabavka.PurchaseOrder'),
   ('Uvoz / izbor fakture i povezivanje','nabavka.ProcurementInvoice'),
   ('Veze stavki, šifri posla i ugovora prema potrebi','nabavka.ProcurementItemInvoiceLink'),
   ('Praćenje predmeta i istorije promena statusa','nabavka.ProcurementStatusLog')],
   ['nabavka/models.py','nabavka/views','nabavka/services/source_snapshots.py'],
   'Tipičan poslovni put, ne obavezni redosled svih ekrana niti automat svih statusa. Ugovori i garaža su opcione veze.'),
 chain('potrazivanja','naplata','Od salda do aktivnosti naplate',[
   ('Sinhronizuj dokumente i knjiženja','potrazivanja.CollectionSyncRun'),
   ('Razreši identitet partnera i dospeće','potrazivanja.FinancePartnerIdentity'),
   ('Pripremi snimak salda i pozicije','potrazivanja.BalanceSnapshot'),
   ('Pregledaj partnera i otvorene pozicije','potrazivanja.ReceivablePosition'),
   ('Evidentiraj kontakt / aktivnost po potrebi','potrazivanja.CollectionActivity'),
   ('Pripremi opomenu i izabrane stavke','potrazivanja.CollectionNotice'),
   ('Prati dalji rad i revizioni trag','potrazivanja.CollectionAudit')],
   ['potrazivanja/services/sync.py','potrazivanja/services/operations.py','potrazivanja/services/partner_detail.py'],
   'Aktivnosti i opomene su operativni koraci; nisu automatska posledica sinhronizacije salda.'),
 chain('pravna','disciplinski','Tok disciplinskog postupka i mera',[
   ('Unos zaposlenog, podnosioca, datuma i centra','pravna.DisciplinskiPostupak'),
   ('Pregled detalja otvorenog postupka','pravna.DisciplinskiPostupak'),
   ('Dodavanje promena u tok postupka','pravna.TokPostupka'),
   ('Zatvaranje: izbor mere i datuma','pravna.DisciplinskiPostupak'),
   ('Čuvanje i pregled zatvorenog postupka','pravna.DisciplinskiPostupak')],
   ['pravna/views_disciplinski.py','pravna/forms.py','pravna/models.py'],
   'Mera i datum se validiraju u formi. Postupci ovog modula nisu isti model kao CollectionLegalCase u Potraživanjima.'),
 chain('ugovori','ugovor','Evidentiranje ugovora i povezanih dokumenata',[
   ('Izbor / unos partnera; APR provera po potrebi','ugovori.Partner'),
   ('Unos ugovora, vrste i perioda','ugovori.Contract'),
   ('Povezivanje ugovornih strana','ugovori.ContractParty'),
   ('Dodavanje priloga i dokumenata','ugovori.ContractDocument'),
   ('Povezivanje menica / garancija po potrebi','ugovori.ContractMenicaLink'),
   ('Pregled ugovora iz povezanih modula','ugovori.Contract')],
   ['ugovori/views.py','ugovori/models.py','ugovori/apr_openapi.py'],
   'BusinessRequest i Offer postoje kao posebne evidencije. Ovaj tok ne pretpostavlja automatsko pretvaranje ponude u ugovor.'),
 chain('menice','registar','Registar menica i povezivanje',[
   ('Preuzimanje podataka iz NBS registra','menice.Menica'),
   ('Pregled evidentiranih menica','menice.Menica'),
   ('Dopuna internih podataka i lokacije','menice.Menica'),
   ('Povezivanje sa ugovorom po potrebi','ugovori.ContractMenicaLink'),
   ('Pregled veze / bankarskog plasmana','finansije.BankBillPlacement')],
   ['menice/scraper.py','menice/views.py','ugovori/models.py','finansije/models.py'],
   'UlaznaMenica je zasebna evidencija. Povezivanje ugovora i banke predstavlja naknadni operativni korak.'),
 chain('mobilni','obustave','Mesečni uvoz i obustave',[
   ('Uvoz korisnika, paketa i zaduženja','mobilni.MobileAssignment'),
   ('Povezivanje sa zaposlenima','mobilni.MobileUser'),
   ('Uvoz obračuna potrošnje operatera','mobilni.MobileUsage'),
   ('Pregled uvoza, potrošnje i izuzetaka','mobilni.MobileImportLog'),
   ('Obračun obustava i izvoz CSV za zarade','mobilni.MobileUsage')],
   ['mobilni/views/mobile.py','mobilni/withholdings.py','mobilni/models.py'],
   'Broj telefona i period učestvuju u uparivanju. Obračun zadržava postojeća pravila i izuzetke.'),
 chain('isplate','virman','Priprema bankarske datoteke za putne naloge',[
   ('Izbor službenih putnih naloga i datuma','fleet.PutniNalog'),
   ('Proveri status, RSD, iznos i račun zaposlenog','hr.Employee'),
   ('Generiši zaglavlje i stavke virmana','fleet.PutniNalog'),
   ('Preuzmi bankarsku TXT datoteku',''),
   ('Ručni uvoz u bankarski sistem, van aplikacije','')],
   ['isplate/services/virman.py','isplate/views.py','fleet/services/putni_nalozi_payments.py'],
   'Isplate nema sopstvene Django modele. Generisanje datoteke nije slanje novca banci. Račun se proverava na 18 cifara.'),
 chain('organizacija','obuhvat','Od dodele uloge do obuhvata podataka',[
   ('Korisnik, uloga, čvor / cela firma i period','organizacija.DodelaUloge'),
   ('Izbor aktivnih dodela i aktivnih uloga','organizacija.DodelaUloge'),
   ('Odredi obuhvat na relevantni datum','organizacija.OrgNode'),
   ('Razreši poslove preko organizacione putanje','organizacija.OrgPutanja'),
   ('Ograniči podatke u modulu koji koristi registar','organizacija.OrgNode')],
   ['organizacija/services/prava.py','organizacija/services/putanja.py','organizacija/models.py'],
   'Primena novog registra zavisi od modula i postavki. Postojeća ograničenja centara i OJ još postoje.'),
 chain('naplata','nasledjeni-pregled','Pregled nasleđenih evidencija naplate',[
   ('Otvaranje postojećeg pregleda partnera','naplata.Partneri'),
   ('Čitanje nasleđenog salda / kategorije','naplata.DodelaBucketa'),
   ('Pregled postojećih kontakata i opomena','naplata.Opomene'),
   ('Novi razvoj i operativni pregled u Potraživanjima','potrazivanja.FinancePartnerIdentity')],
   ['naplata/models.py','naplata/urls.py','potrazivanja/models.py'],
   'Prelaz ka Potraživanjima je smer razvoja, ne automatsko prebacivanje podataka. Stvarni pogled je dodela_baketa; stari model navodi dodela_bucketa.'),
]

FLOWS.append(dict(module='core',slug='pristup',title='Provera pristupa ruti',
 nodes=[('start','Otvaranje rute','','circle'),('auth','Prijavljen korisnik?','core.CustomUser','diamond'),
        ('deny','Pristup nije odobren','','box'),('super','Superuser?','core.CustomUser','diamond'),
        ('role','Aktivna uloga ima kod rute?','core.RolePermission','diamond'),
        ('scope','Provera obuhvata u konkretnom modulu','organizacija.DodelaUloge','box'),
        ('end','Dozvoljeni podaci','','doublecircle')],
 edges=[('start','auth',''),('auth','deny','ne'),('auth','super','da'),('super','scope','da'),
        ('super','role','ne'),('role','deny','ne'),('role','scope','da'),('scope','end','')],
 sources=['core/mixins.py','core/permissions.py','organizacija/services/prava.py'],
 note='RolePermissionRequiredMixin: eksplicitni kod ili resolver_match.view_name. Obuhvat i superuser izuzeci na nivou podataka zavise od konkretnog modula.'))

for f in FLOWS:
    f['id']=f['module']+'/'+f['slug']

REFERENCED_MODELS = {'isplate':['fleet.PutniNalog','hr.Employee','core.OrganizationalUnit']}
