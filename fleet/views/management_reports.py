from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse

from core.exporting import create_xlsx_workbook, style_header_row, autofit_columns, workbook_response
from core.mixins import role_permission_required
from fleet.forms.management_reports import VehicleInsuranceReportForm, FleetFuelReportForm, SupplierPartsReportForm
from fleet.support.management_reports import vehicle_insurance_rows, fuel_report_rows, group_fuel_rows, supplier_choices, supplier_parts_rows, FUEL_GROUPS, allowed_centers


def _sr_number(value):
    return format(value, ',.2f').replace(',', '_').replace('.', ',').replace('_', '.')


def _cell(key, value, row):
    numeric = isinstance(value, (Decimal, int, float)) and not isinstance(value, bool)
    sort = value.isoformat() if isinstance(value, (date, datetime)) else (str(value) if value is not None else '')
    display = '—' if value is None or value == '' else value
    if isinstance(value, Decimal):
        display = _sr_number(value)
    elif isinstance(value, (date, datetime)):
        display = value.strftime('%d.%m.%Y')
    return dict(display=display, sort=sort, numeric=numeric, url=reverse('vehicle_detail', args=[row['id']]) if key == 'plate' and row.get('id') else None)


def _report(request, *, title, description, form, headers, rows, notes, metrics=(), filename='izvestaj'):
    valid = form.is_valid()
    if request.GET.get('export') == 'xlsx' and valid:
        book, sheet = create_xlsx_workbook('Pregled')
        sheet.append([label for key,label in headers])
        for row in rows:
            values=[]
            for key, label in headers:
                value=row.get(key)
                # External invoice/article text is data, never an Excel formula.
                if isinstance(value,str) and value.lstrip().startswith(('=', '+', '-', '@')):
                    value="'"+value
                values.append(value)
            sheet.append(values)
            for cell in sheet[sheet.max_row]:
                if isinstance(cell.value,Decimal): cell.number_format='#,##0.00'
                elif isinstance(cell.value,date): cell.number_format='dd.mm.yyyy'
        style_header_row(sheet)
        sheet.freeze_panes='A2'; sheet.auto_filter.ref=sheet.dimensions
        autofit_columns(sheet)
        context=book.create_sheet('Obuhvat')
        context.append([title]); context.append([description])
        for field in form: context.append([field.label, str(form.cleaned_data.get(field.name) or '')])
        for note in notes: context.append([note])
        for row in context:
            for cell in row:
                if isinstance(cell.value, str): cell.data_type = 's'
        return workbook_response(book,filename+'.xlsx')
    export=request.GET.copy()
    # Defaults must travel to the export too.
    for key,value in form.data.items(): export[key]=value
    export['export']='xlsx'
    return render(request,'fleet/reports/management_report.html',dict(title=title,description=description,form=form,
        headers=[label for key,label in headers],table_rows=[[_cell(key,row.get(key),row) for key,label in headers] for row in rows],
        notes=notes,metrics=metrics,export_query=export.urlencode(),valid=valid,row_count=len(rows),
        numeric_columns=[i for i,(key,label) in enumerate(headers) if any(isinstance(r.get(key),(Decimal,int,float)) for r in rows)]),status=200 if valid else 400)


VEHICLE_HEADERS=[('plate','Tablice'),('vin','Broj šasije'),('inventory','Inventarski broj'),('brand','Marka'),('model','Model'),('category','Kategorija'),('year','Godište'),('age','Starost (god.)'),('center','Centar'),('job','Šifra posla'),('unit','OJ'),('ownership','Osnov raspolaganja'),('registration','Rok registracije'),('first_registration','Prva registracija'),('color','Boja'),('fuel','Gorivo'),('engine_volume','Zapremina cm³'),('power','Snaga kW'),('seats','Sedišta'),('weight','Najveća masa kg'),('purchase_value','Nabavna vrednost'),('book_value','Knjigovodstvena vrednost')]


def _insurance_report(request, casco):
    params=request.GET.copy()
    if not params: params.update(as_of=timezone.localdate().isoformat(),ownership='all')
    form=VehicleInsuranceReportForm(params)
    if casco: form.fields.pop('ownership')
    rows,stats=vehicle_insurance_rows(request.user,form.cleaned_data,casco=casco) if form.is_valid() else ([],{})
    notes=['Obuhvat čine trenutno neotpisana vozila. Dokumenti, raspored i raspolaganje biraju se na datum preseka; ovaj pregled ne rekonstruiše raniji status otpisa.',
           'Podrazumevano vlasništvo IMS primenjuje se kada nema tekućeg evidentiranog osnova ni važećeg lizinga/najma. Izvor osnova je naveden uz svako vozilo.',
           'Novčane vrednosti su postojeće nabavne i knjigovodstvene vrednosti; nisu procena osigurane vrednosti.']
    if casco: notes.insert(0,'Uslov: godina preseka − godina proizvodnje > 7. Vozilo staro tačno 7 godina nije uključeno. Nema uslova visoke vrednosti; uključeni su svi osnovi raspolaganja.')
    if stats.get('unknown_year'): notes.append(f'Vozila sa nepoznatim/neispravnim godištem: {stats["unknown_year"]}. U kasko izbor ulaze samo potvrđena godišta.')
    return _report(request,title='Kasko — vozila starija od 7 godina' if casco else 'Auto osiguranje — vlasništvo IMS',description='Pregled podataka za pripremu osiguranja i izvoz u Excel.',form=form,headers=VEHICLE_HEADERS,rows=rows,notes=notes,
        metrics=[('Vozila u pregledu',len(rows)),('Podrazumevani osnov',stats.get('assumed',0)),('Nepoznato godište',stats.get('unknown_year',0))],filename='kasko_vozila' if casco else 'osiguranje_ims')


@login_required
@role_permission_required('vehicle_list')
def casco_report(request): return _insurance_report(request,True)


@login_required
@role_permission_required('vehicle_list')
def owned_insurance_report(request): return _insurance_report(request,False)


def _period_defaults(request, **extras):
    params=request.GET.copy()
    if not params:
        today=timezone.localdate()
        params.update(date_from=date(today.year,1,1).isoformat(),date_to=today.isoformat(),**extras)
    return params


@login_required
@role_permission_required('fuel_transactions_list')
def fleet_fuel_report(request):
    form=FleetFuelReportForm(_period_defaults(request,fuel_type='fuel',group_by='month'))
    raw=fuel_report_rows(request.user,form.cleaned_data) if form.is_valid() else []
    labels={'month':'Mesec','center':'Centar','job':'Šifra posla','product':'Proizvod'}
    mode=form.cleaned_data.get('group_by','month') if form.is_valid() else 'month'
    if mode=='detail':
        rows=raw
        headers=[('date','Datum'),('supplier','Dobavljač'),('plate','Tablice'),('center','Centar'),('job','Šifra posla'),('fuel_type','Vrsta'),('product','Proizvod'),('quantity','Količina iz izvora'),('gross','Bruto iznos'),('currency','Valuta')]
        # Transaction IDs are not vehicle IDs; don't link plate using them.
        rows=[{**row,'id':row['vehicle_id']} for row in raw]
    else:
        rows=group_fuel_rows(raw,mode)
        fields=FUEL_GROUPS[mode]
        headers=[(f,labels[f]) for f in fields]+[('fuel_type','Vrsta')]+([] if 'product' in fields else [('product','Proizvod')])+[('count','Transakcije'),('quantity','Količina iz izvora'),('gross','Bruto iznos'),('currency','Valuta'),('missing_amount','Bez iznosa')]
    notes=['Izvor: NIS/OMV transakcije, bruto terećenje posle popusta (NIS Total / OMV Gross CC). Period prati datum transakcije, a centar i šifra posla poslednju dodelu koja važi tog dana.',
        'Ovo je detaljni pregled kartičnih kupovina NIS/OMV. Gorivo iz magacina i preko zaposlenih obuhvaćeno je zasebnim pregledom Knjiženi troškovi goriva po mesecima; nema pouzdane raspodele tih stavki po proizvodu u ovom izvoru.',
        'Količine su točenja/kupovine iz izvora, ne izmerena potrošnja u motoru. Proizvodi i valute ostaju odvojeni; količine različitih proizvoda se ne sabiraju u jedan pokazatelj.',
        'AdBlue i ostale kupovine nisu deo početnog izbora Gorivo. Izaberite vrstu ili Svi proizvodi za njihov prikaz. Prazan iznos nije nula.']
    if allowed_centers(request.user): notes.append('Prikaz je ograničen na dozvoljene centre; stavke bez istorijskog centra nisu u ovom korisničkom obuhvatu.')
    amounts={}
    for row in raw:
        if row['gross'] is not None: amounts[row['currency']]=amounts.get(row['currency'],Decimal('0'))+row['gross']
    return _report(request,title='Gorivo IMS — NIS i OMV',description='Filteri po vrsti proizvoda, mesecu, centru i šifri posla, sa pojedinačnim transakcijama.',form=form,headers=headers,rows=rows,notes=notes,
        metrics=[('Transakcije',len(raw)),*[(f'Bruto · {currency}',_sr_number(value)) for currency,value in sorted(amounts.items())],('Bez povezanog vozila',sum(r['vehicle_id'] is None for r in raw)),('Bez šifre posla',sum(r['job']=='Bez šifre' for r in raw)),('Bez iznosa',sum(r['gross'] is None for r in raw))],filename='gorivo_ims')


@login_required
@role_permission_required('nabavka:euf_invoice_list')
def supplier_parts_report(request):
    params=_period_defaults(request,source='uf')
    choices=supplier_choices(params.get('source','uf'))
    # Select AutoDeki only when the identity is unambiguous in the source.
    matches=[key for key,label in choices if 'autodeki' in ''.join(c for c in label.casefold() if c.isalnum())]
    if not params.get('supplier') and len(matches)==1: params['supplier']=matches[0]
    form=SupplierPartsReportForm(params,supplier_choices=choices)
    rows=supplier_parts_rows(form.cleaned_data) if form.is_valid() else []
    goods=params.get('source')=='goods'
    notes=['Prikazuju se postojeće stavke Nabavke za izabranog dobavljača i period. Izvori se biraju odvojeno da se faktura i robni promet ne saberu dvaput.',
        'Kupovina dela ne potvrđuje ugradnju u vozilo. Naziv stavke i izvorni dokument ostaju vidljivi; storna i negativne stavke nisu uklonjeni.',
        'Robne stavke prikazuju izvorni promet i vrstu dokumenta; to nije automatski spisak samo ulaznih nabavki.' if goods else 'Vrednost stavke je izvorno polje Vrednost, bez mešanja sa ponovljenim ukupnim iznosom zaglavlja fakture.']
    if not params.get('supplier'): notes.insert(0,'AutoDeki nije nedvosmisleno identifikovan u izvoru. Izaberite odgovarajućeg dobavljača po nazivu i PIB-u/šifri; prazan pregled ne znači da nije bilo kupovine.')
    return _report(request,title='Kupljeni delovi — AutoDeki / dobavljač',description='Specifikacija iz Nabavke sa izborom dobavljača i izvornog dokumenta.',form=form,
        headers=[('date','Datum'),('supplier','Dobavljač'),('supplier_id','PIB / šifra'),('invoice','Faktura / veza'),('document_type','Vrsta dokumenta'),('code','Šifra artikla' if goods else 'Konto'),('article','Deo / stavka'),('quantity','Količina'),('unit','JM'),('price','Cena'),('value','Izvorni promet' if goods else 'Vrednost stavke'),('currency','Valuta'),('synced','Osveženo')],rows=rows,notes=notes,
        metrics=[('Stavke',len(rows)),('Bez vrednosti',sum(r['value'] is None for r in rows))],filename='delovi_dobavljaca')
