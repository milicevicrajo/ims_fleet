"""Static Django model inventory. No Django import and no database access."""
import ast
from copy import deepcopy
from pathlib import Path

RELATIONS={'ForeignKey','OneToOneField','ManyToManyField'}

def literal(node, default=None):
    try:return ast.literal_eval(node)
    except (ValueError,TypeError):return default

def expression(node):
    return ast.unparse(node) if node is not None else ''

def inspect_sources(root, modules):
    classes={}
    for module in modules:
        for path in sorted((root/module).glob('*models.py')):
            for cls in ast.parse(path.read_text(encoding='utf-8-sig')).body:
                if not isinstance(cls,ast.ClassDef):continue
                bases=[expression(base) for base in cls.bases]
                if any(b.endswith(('TextChoices','IntegerChoices')) for b in bases):continue
                key=module+'.'+cls.name
                fields=[]; constraints=[]; meta={}; enums={}
                for stmt in cls.body:
                    if isinstance(stmt,ast.ClassDef):
                        if stmt.name=='Meta':
                            for assign in stmt.body:
                                if isinstance(assign,ast.Assign):
                                    prop=expression(assign.targets[0]);value=assign.value
                                    meta[prop]=literal(value,expression(value))
                                    if prop=='constraints':
                                        for call in ast.walk(value):
                                            if isinstance(call,ast.Call) and expression(call.func).endswith('Constraint'):
                                                options={kw.arg:kw.value for kw in call.keywords}
                                                constraints.append(dict(kind=expression(call.func).split('.')[-1],
                                                    name=literal(options.get('name'),'') if options.get('name') else '',
                                                    fields=literal(options.get('fields'),[]) if options.get('fields') else [],
                                                    condition=expression(options.get('condition')),
                                                    definition=expression(call)))
                        elif any(expression(b).endswith(('TextChoices','IntegerChoices')) for b in stmt.bases):
                            choices=[]
                            for assign in stmt.body:
                                if isinstance(assign,ast.Assign):
                                    val=assign.value
                                    if isinstance(val,ast.Tuple) and val.elts:
                                        raw=literal(val.elts[0],expression(val.elts[0]))
                                        label=val.elts[1] if len(val.elts)>1 else val.elts[0]
                                        if isinstance(label,ast.Call) and label.args:label=label.args[0]
                                        choices.append([str(raw),str(literal(label,expression(label)))])
                            enums[stmt.name]=choices
                        continue
                    if not isinstance(stmt,ast.Assign) or not isinstance(stmt.value,ast.Call):continue
                    call=stmt.value;typ=expression(call.func).split('.')[-1]
                    if not (typ.endswith('Field') or typ in RELATIONS):continue
                    options={kw.arg:kw.value for kw in call.keywords};name=expression(stmt.targets[0])
                    fields.append(dict(name=name,type=typ,null=literal(options.get('null'),False),
                        blank=literal(options.get('blank'),False),primary=literal(options.get('primary_key'),False),
                        unique=literal(options.get('unique'),False),target_raw=expression(call.args[0]).strip('"\'') if typ in RELATIONS and call.args else '',
                        through=expression(options.get('through')).strip('"\''),
                        on_delete=expression(options.get('on_delete')).replace('models.',''),
                        choices_expr=expression(options.get('choices')),default=expression(options.get('default')),
                        source=path.relative_to(root).as_posix(),line=stmt.lineno,declared_in=key))
                if not fields and not any(b.endswith('Model') for b in bases):continue
                classes[key]=dict(id=key,name=cls.name,module=module,bases=bases,own_fields=fields,
                    constraints=constraints,meta=meta,enums=enums,source=path.relative_to(root).as_posix(),line=cls.lineno)
    aliases={}
    for key,m in classes.items():
        aliases[m['meta'].get('app_label',m['module'])+'.'+m['name']]=key
    aliases['settings.AUTH_USER_MODEL']='core.CustomUser'

    def resolve(raw,model):
        if raw=='self':return model['id']
        if raw in classes:return raw
        if raw in aliases:return aliases[raw]
        local=model['module']+'.'+raw
        if local in classes:return local
        names=[k for k in classes if k.endswith('.'+raw)]
        return names[0] if len(names)==1 else None

    def populate(key,seen=None):
        m=classes[key]
        if 'fields' in m:return
        seen=(seen or set())|{key};fields={};parents=[]
        for base in m['bases']:
            parent=resolve(base,m)
            if parent and parent not in seen:
                populate(parent,seen);parents.append(parent)
                fields.update({f['name']:deepcopy(f) for f in classes[parent]['fields']})
        fields.update({f['name']:deepcopy(f) for f in m['own_fields']})
        m['parents']=parents;m['abstract']=m['meta'].get('abstract',False) is True
        m['managed']=m['meta'].get('managed',True) is not False
        m['app_label']=m['meta'].get('app_label',m['module'])
        m['table']=None if m['abstract'] else m['meta'].get('db_table',m['app_label']+'_'+m['name'].lower())
        m['table_explicit']='db_table' in m['meta']
        for constraint in m['constraints']:
            if constraint['kind']=='UniqueConstraint' and len(constraint['fields'])==1 and not constraint['condition']:
                field=fields.get(constraint['fields'][0])
                if field:field['unique']=True
        for f in fields.values():
            if f['target_raw']:
                declared=classes[f['declared_in']]
                f['target']=resolve(f['target_raw'],declared)
                if not f['target']:raise ValueError(f"Unresolved model: {key}.{f['name']} -> {f['target_raw']}")
                if f['through']:f['through_model']=resolve(f['through'],declared)
            expr=f['choices_expr']
            enum=expr.removesuffix('.choices')
            f['choices']=m['enums'].get(enum,[])
        m['fields']=list(fields.values())
        m['implicit_pk']=not m['abstract'] and not any(f['primary'] for f in fields.values())
        m['framework_base']='AbstractUser' if 'AbstractUser' in m['bases'] else ''
        m['notes']=[]
        if m['framework_base']:m['notes'].append('Nasleđuje Django AbstractUser: username, password, email, is_active, is_staff, is_superuser i druga framework polja nisu ponovljena u ovoj listi.')
        if m['implicit_pk']:m['notes'].append('Django dodaje primarni ključ id; tip zavisi od DEFAULT_AUTO_FIELD / AppConfig postavki.')
        if key=='naplata.DodelaBucketa':m['notes'].append('Poznato odstupanje: model navodi dodela_bucketa; stvarni nasleđeni pogled je dodela_baketa. Prikaz ne menja izvor.')
        if not m['managed']:m['notes'].append('managed=False: Django ne upravlja ovom tabelom / pogledom migracijama.')
        m.pop('own_fields',None)
    for key in classes:populate(key)
    edges=[]
    for key,m in classes.items():
        for f in m['fields']:
            if f.get('target'):
                many=f['type']=='ManyToManyField'
                edges.append(dict(source=key,target=f['target'],field=f['name'],type=f['type'],
                    left='0..1' if f['unique'] or f['type']=='OneToOneField' else '0..*',
                    right='0..*' if many else ('0..1' if f['null'] else '1'),
                    inherited=f['declared_in']!=key,through=f.get('through_model'),on_delete=f['on_delete']))
    return classes,edges
