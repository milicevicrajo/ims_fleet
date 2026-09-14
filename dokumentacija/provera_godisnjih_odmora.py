"""Aggregate source audit; no employee names, IDs or individual leave periods are printed."""
import os
import sys
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_erp.settings.development')
import django
django.setup()
from django.db import connection

result = {}
with connection.cursor() as cursor:
    for table in ('Godmor', 'GodmorKor'):
        cursor.execute(f'SELECT * FROM [putgeo-server].[BazaLDIMS].[dbo].[{table}]')
        columns = [item[0] for item in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        key_columns = ['sif_pred', 'god', 'rasif'] + (['od_datuma'] if table == 'GodmorKor' else [])
        keys = Counter(tuple(row[key] for key in key_columns) for row in rows)
        result[table] = {
            'columns': columns, 'rows': len(rows),
            'years': sorted(Counter(str(row['god']).strip() for row in rows).items()),
            'duplicate_candidate_keys': sum(count-1 for count in keys.values() if count > 1),
            'null_identity': sum(any(row[key] is None for key in key_columns) for row in rows),
            'missing_days': sum(row['dana'] is None for row in rows),
            'negative_days': sum(row['dana'] is not None and row['dana'] < 0 for row in rows),
        }
        if table == 'GodmorKor':
            dates = Counter((row['sif_pred'], row['god'], row['rasif'], row['od_datuma'], row['do_datuma']) for row in rows)
            result[table].update(
                duplicate_period_keys=sum(count-1 for count in dates.values() if count > 1),
                invalid_periods=sum(row['od_datuma'] is None or row['do_datuma'] is None or row['od_datuma'] > row['do_datuma'] for row in rows),
                max_comment_length=max(len(str(row['komentar'] or '')) for row in rows),
            )
        cursor.execute('''SELECT kc.name, c.name, ic.key_ordinal
            FROM [putgeo-server].[BazaLDIMS].sys.key_constraints kc
            JOIN [putgeo-server].[BazaLDIMS].sys.tables t ON t.object_id=kc.parent_object_id
            JOIN [putgeo-server].[BazaLDIMS].sys.index_columns ic ON ic.object_id=t.object_id AND ic.index_id=kc.unique_index_id
            JOIN [putgeo-server].[BazaLDIMS].sys.columns c ON c.object_id=t.object_id AND c.column_id=ic.column_id
            WHERE t.name=%s ORDER BY kc.name, ic.key_ordinal''', [table])
        result[table]['keys'] = [list(row) for row in cursor.fetchall()]
print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
(ROOT/'izvestaji/provera_godisnjih_odmora_20260911.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
