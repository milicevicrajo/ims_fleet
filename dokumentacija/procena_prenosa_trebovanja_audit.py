"""Read-only migration assessment. Writes aggregate evidence, never business rows."""
import os
import sys
import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_erp.settings.development')
import django
django.setup()
from django.db import connections
from fleet.models import Requisition
from nabavka.models import GoodsSnapshot, ProcurementItem

stamp = datetime.now().strftime('%Y%m%d')
result = {'checked_at': datetime.now().isoformat(timespec='seconds'), 'read_only': True,
          'method': 'Exact trimmed source-key candidates; not proof of business identity or financial equivalence.',
          'database_checks': {}}
for alias in ('default', 'server_db'):
    if alias not in connections:
        result['database_checks'][alias] = {'status': 'not_configured'}
        continue
    db = connections[alias]
    db.settings_dict.setdefault('OPTIONS', {}).update(connection_timeout=5, query_timeout=20)
    try:
        with db.cursor() as cur:
            cur.execute('SELECT 1')
            cur.fetchone()
        result['database_checks'][alias] = {'status': 'available'}
    except Exception as exc:
        result['database_checks'][alias] = {'status': 'unavailable', 'error_class': type(exc).__name__}

def clean(v):
    return '' if v is None else str(v).strip()

def group_key(row, fields):
    return tuple(clean(row[f]) for f in fields)

if result['database_checks'].get('default', {}).get('status') == 'available':
    req = list(Requisition.objects.order_by().values())
    goods = list(GoodsSnapshot.objects.order_by().values())
    rf = ('sif_pred','god','br_dok','sif_vrsart','stavka')
    gf = ('subject_code','year','document_number','article_type','line_number')
    index = defaultdict(list)
    for g in goods:
        index[group_key(g, gf)].append(g)
    matching = [r for r in req if group_key(r, rf) in index]
    unique = [r for r in matching if len(index[group_key(r,rf)]) == 1]
    comparisons = [('sif_art','article_code'), ('kol','quantity'), ('cena','price'), ('datum_trebovanja','document_date')]
    same = [r for r in unique if all(clean(r[a]) == clean(index[group_key(r,rf)][0][b]) for a,b in comparisons)]
    result['local'] = {
        'requisition_rows':len(req), 'goods_rows':len(goods),
        'requisition_documents_by_subject_year_number':len({group_key(r,('sif_pred','god','br_dok')) for r in req}),
        'requisition_years':dict(Counter(str(r['god']) for r in req)),
        'goods_years':dict(Counter(str(g['year']) for g in goods)),
        'goods_document_types':dict(Counter(str(g['document_type']) for g in goods)),
        'requisition_value_by_year':{y:str(sum((r['vrednost_nab'] for r in req if str(r['god'])==y),Decimal('0'))) for y in sorted({str(r['god']) for r in req})},
        'missing_vehicle':sum(r['vehicle_id'] is None for r in req),
        'linked_garage_order':sum(r['kvar_id'] is not None for r in req),
        'has_category':sum(r['popravka_kategorija_id'] is not None for r in req),
        'has_mileage':sum(r['kilometraza'] is not None for r in req),
        'has_note':sum(bool(clean(r['napomena'])) for r in req),
        'not_garage':sum(bool(r['nije_garaza']) for r in req),
        'negative_quantity':sum(r['kol'] < 0 for r in req),
        'value_differs_from_quantity_times_price':sum(r['vrednost_nab'] != (r['kol']*r['cena']).quantize(Decimal('0.01')) for r in req),
        'non_numeric_document_numbers':sum(not clean(r['br_dok']).isdigit() for r in req),
        'article_name_longer_than_goods_max80':sum(len(r['naz_art'])>80 for r in req),
        'goods_linked_request_items':ProcurementItem.objects.filter(goods_item__isnull=False).count(),
        'candidate_key_fields':list(rf), 'candidate_rows':len(matching),
        'unambiguous_candidate_rows':len(unique), 'same_article_quantity_price_date':len(same),
        'unmatched_rows':len(req)-len(matching),
    }

if result['database_checks'].get('server_db', {}).get('status') == 'available':
    result['source_views'] = {}
    for view in ('fleet_trebovanja', 'nbv_roba'):
        try:
            with connections['server_db'].cursor() as cur:
                cur.execute('SELECT COUNT_BIG(*) FROM dbo.' + view)
                count = cur.fetchone()[0]
                cur.execute('SELECT name FROM sys.columns WHERE object_id=OBJECT_ID(%s) ORDER BY column_id',['dbo.'+view])
                columns = [r[0] for r in cur.fetchall()]
                cur.execute('SELECT OBJECT_DEFINITION(OBJECT_ID(%s))', ['dbo.'+view])
                definition = cur.fetchone()[0]
            result['source_views'][view] = {'row_count':count, 'columns':columns, 'definition_available':bool(definition)}
            if definition:
                (ROOT/'izvestaji'/f'procena_{view}_{stamp}.sql').write_text(definition,encoding='utf-8')
        except Exception as exc:
            result['source_views'][view] = {'status':'query_failed','error_class':type(exc).__name__}

    if result.get('local'):
        try:
            with connections['server_db'].cursor() as cur:
                cur.execute('SELECT sif_pred,god,br_dok,sif_vrsart,stavka,sif_art,kol,cena,vrednost_nab,datum_trebovanja FROM dbo.fleet_trebovanja')
                source_rows = [dict(zip(('sif_pred','god','br_dok','sif_vrsart','stavka','sif_art','kol','cena','vrednost_nab','datum_trebovanja'), r)) for r in cur.fetchall()]
            local_index = {group_key(r,rf):r for r in req}
            source_keys = Counter(group_key(r,rf) for r in source_rows)
            present = [r for r in source_rows if group_key(r,rf) in local_index]
            differences = Counter()
            for r in present:
                old = local_index[group_key(r,rf)]
                for field in ('sif_art','kol','cena','vrednost_nab','datum_trebovanja'):
                    a,b = r[field],old[field]
                    if hasattr(a,'date'):
                        a=a.date()
                    if a != b and clean(a) != clean(b):
                        differences[field]+=1
            result['same_requisition_source_comparison'] = {
                'source_rows':len(source_rows),'source_unique_keys':len(source_keys),
                'duplicate_source_key_groups':sum(v>1 for v in source_keys.values()),
                'source_keys_missing_locally':sum(k not in local_index for k in source_keys),
                'local_keys_absent_from_current_source':sum(k not in source_keys for k in local_index),
                'source_rows_matching_local_key':len(present),'field_differences':dict(differences),
            }
        except Exception as exc:
            result['same_requisition_source_comparison'] = {'status':'query_failed','error_class':type(exc).__name__}

target = ROOT/'izvestaji'/f'procena_prenosa_trebovanja_{stamp}.json'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
connections.close_all()
