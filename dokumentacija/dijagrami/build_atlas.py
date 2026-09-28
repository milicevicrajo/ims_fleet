"""Generate the offline, linked SVG atlas from source. No Django / SQL access.

Usage: python dokumentacija/dijagrami/build_atlas.py [--dot PATH]
Only SVG, HTML, JavaScript and JSON are produced. Graphviz is required.
"""
import argparse
from collections import Counter
from datetime import date
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'atlas'))
from catalog import MODULES,FLOWS,REFERENCED_MODELS
from models import inspect_sources

SVG_NS='http://www.w3.org/2000/svg'
XLINK='http://www.w3.org/1999/xlink'
ET.register_namespace('',SVG_NS);ET.register_namespace('xlink',XLINK)

def q(value):return json.dumps(str(value),ensure_ascii=False)
def h(value):return html.escape(str(value),quote=True)
def slug(value):return re.sub(r'[^A-Za-z0-9_.-]','--',value)
def url(route):return '../../index.html#'+route

class Atlas:
    def __init__(self,dot):
        self.dot=dot;self.models,self.edges=inspect_sources(ROOT,MODULES)
        self.diagrams={};self.modules={};self.out=HERE/'atlas/svg';self.out.mkdir(parents=True,exist_ok=True)
        for key,(name,description,color,groups) in MODULES.items():
            ids=[k for k,m in self.models.items() if m['module']==key]
            if key in REFERENCED_MODELS:ids=REFERENCED_MODELS[key]
            remaining=set(ids);areas=[]
            for aid,title,pattern,excludes in groups:
                selected=[m for m in ids if m in remaining and (not pattern or re.search(pattern,self.models[m]['name'])) and not any(x in self.models[m]['name'] for x in excludes)]
                remaining.difference_update(selected)
                areas.append(dict(id=aid,title=title,models=selected))
            if remaining:areas.append(dict(id='ostalo',title='Pomoćne evidencije',models=sorted(remaining)))
            self.modules[key]=dict(id=key,name=name,description=description,color=color,models=ids,areas=areas,
                                  sources=self.source_paths(key),owned=sum(m['module']==key for m in self.models.values()))
        for f in FLOWS:
            for source in f['sources']:
                if not (ROOT/source).exists():raise ValueError('Unknown flow source: '+source)
            for _,_,model,_ in f['nodes']:
                if model and model not in self.models:raise ValueError('Unknown flow model: '+model)
        self.relations={key:[] for key in self.models}
        for edge in self.edges:
            self.relations[edge['source']].append(edge)
            if edge['source']!=edge['target']:self.relations[edge['target']].append(edge)

    def source_paths(self,module):
        paths=[]
        for suffix in ['urls.py','models.py','views.py','views','services','support','sync']:
            path=ROOT/module/suffix
            if path.exists():paths.append(path.relative_to(ROOT).as_posix())
        return paths

    def graph(self,key,title,description,nodes,edges,*,clusters=False,rankdir='LR',sources=None):
        # nodes: key, label (HTML or text), route, color, shape, model.
        lines=['digraph G {',f'graph [rankdir={rankdir}, bgcolor="transparent", pad="0.3", nodesep="0.32", ranksep="0.8", fontname="Segoe UI", fontsize=16, compound=true];',
               'node [shape=box, style="rounded,filled", fillcolor="#f3f8fb", color="#9db7c7", fontname="Segoe UI", fontsize=14, margin="0.15,0.12"];',
               'edge [color="#8b9ead", arrowsize=0.7, fontname="Segoe UI", fontsize=11];']
        ids={n['key']:'n'+str(i) for i,n in enumerate(nodes)}
        groups={}
        for node in nodes:groups.setdefault(node.get('group',''),[]).append(node)
        for group,items in groups.items():
            if clusters and group:
                mod=self.modules[group]
                lines.append(f'subgraph cluster_{slug(group)} {{ label={q(mod["name"])}; color="#d3e1e8"; style="rounded";')
            for node in items:
                label='<'+node['label']+'>' if node.get('html') else q(node['label'])
                attrs=[f'id={q("node-"+slug(node["key"]))}',f'label={label}',f'shape={q(node.get("shape","box"))}',f'color={q(node.get("color","#6b8c9f"))}']
                if node.get('shape') in ('circle','doublecircle'):
                    attrs += ['label=""',f'xlabel={q(node["label"])}','fixedsize=true','width=0.22','height=0.22',f'fillcolor={q(node.get("color","#193c50"))}']
                if node.get('route'):attrs += [f'URL={q(url(node["route"]))}', 'target="_top"',f'tooltip={q(node.get("tip",title))}']
                lines.append(f'{ids[node["key"]]} [{", ".join(attrs)}];')
            if clusters and group:lines.append('}')
        for i,edge in enumerate(edges):
            if edge['source'] not in ids or edge['target'] not in ids:continue
            attrs=[f'id={q("edge-"+str(i))}',f'label={q(edge.get("label",""))}',f'color={q(edge.get("color","#8b9ead"))}',f'tooltip={q(edge.get("tip",edge.get("label","")))}']
            if edge.get('style'):attrs.append(f'style={q(edge["style"])}')
            if edge.get('left'):attrs += [f'taillabel={q(edge["left"])}',f'headlabel={q(edge["right"])}', 'labeldistance=1.5']
            lines.append(f'{ids[edge["source"]]} -> {ids[edge["target"]]} [{", ".join(attrs)}];')
        lines.append('}')
        dot='\n'.join(lines)
        filename=slug(key)+'.svg';path=self.out/filename
        digest=hashlib.sha256(dot.encode()).hexdigest()
        cache=path.with_suffix('.sha256')
        if path.exists() and cache.exists() and cache.read_text()==digest:
            raw=path.read_text(encoding='utf-8')
        else:
            result=subprocess.run([self.dot,'-Tsvg'],input=dot,encoding='utf-8',capture_output=True,check=True,timeout=120)
            svg=ET.fromstring(result.stdout)
            svg.set('role','img');svg.set('aria-label',title)
            style=ET.Element(f'{{{SVG_NS}}}style')
            style.text='.node:hover polygon,.node:hover path{stroke-width:2.5}.node a:focus{outline:2px solid #287b75}text{font-family:"Segoe UI",Arial,sans-serif}'
            svg.insert(0,style)
            for node in nodes:
                element=next((x for x in svg.iter() if x.get('id')=='node-'+slug(node['key'])),None)
                if element is not None:
                    element.set('data-key',node['key'])
                    if node.get('route'):element.set('data-route',node['route'])
            for i,edge in enumerate(edges):
                element=next((x for x in svg.iter() if x.get('id')=='edge-'+str(i)),None)
                if element is not None:
                    element.set('data-from',edge['source']);element.set('data-to',edge['target'])
            raw=ET.tostring(svg,encoding='unicode')
            path.write_text(raw,encoding='utf-8');cache.write_text(digest)
        self.diagrams[key]=dict(id=key,title=title,description=description,file='atlas/svg/'+filename,svg=raw,sources=sources or [])

    def model_label(self,key,fields=False,external=False):
        model=self.models[key];color=self.modules[model['module']]['color']
        parts=[f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">',
               f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="11" COLOR="{color}">{h(model["module"])}'+(' · abstraktno' if model['abstract'] else '')+'</FONT></TD></TR>',
               f'<TR><TD ALIGN="LEFT"><B>{h(model["name"])}</B></TD></TR>']
        if fields:
            if model['implicit_pk']:parts.append('<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="11">id : PK (Django)</FONT></TD></TR>')
            for field in model['fields']:
                flags=(' [PK]' if field['primary'] else '')+(' [UQ]' if field['unique'] else '')+(' ?' if field['null'] else '')
                typ=self.models[field['target']]['name'] if field.get('target') else field['type'].removesuffix('Field')
                text=f'{field["name"]} : {typ}{flags}'
                parts.append(f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="11">{h(text)}</FONT></TD></TR>')
        else:
            parts.append(f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="11" COLOR="#5c7282">{len(model["fields"])} polja'+(' · povezani model' if external else '')+'</FONT></TD></TR>')
        parts.append('</TABLE>');return ''.join(parts)

    def model_graph(self,key,title,selected,full=False,neighbors=False,global_graph=False):
        selected=set(selected);visible=set(selected)
        if neighbors:
            for e in self.edges:
                if e['source'] in selected or e['target'] in selected:visible.update([e['source'],e['target']])
        nodes=[dict(key=k,label=self.model_label(k,full and k in selected,k not in selected),html=True,
                    route='model/'+k,group=self.models[k]['module'],color=self.modules[self.models[k]['module']]['color'],tip=k) for k in sorted(visible)]
        edges=[]
        for e in self.edges:
            if e['source'] in visible and e['target'] in visible and (not neighbors or e['source'] in selected or e['target'] in selected):
                cross=self.models[e['source']]['module']!=self.models[e['target']]['module']
                edges.append(dict(source=e['source'],target=e['target'],label=e['field'] if not global_graph else '',
                                  left=e['left'] if not global_graph else '',right=e['right'],color='#a27631' if cross else '#7297ab',
                                  tip=f'{e["source"]}.{e["field"]} → {e["target"]} | {e["type"]} | {e["left"]} : {e["right"]}'))
        if not nodes:
            nodes=[dict(key='empty',label='Ova oblast nema sopstvene modele.\nPogledajte povezane modele i tokove rada.',route='flows')]
        self.graph(key,title,'Puna strelica: polje vlasnika → ciljni model. Zlatno: veza između modula. ? = NULL; UQ = jedinstveno. Nasleđena lokalna polja su uključena.',
                   nodes,edges,clusters=global_graph,sources=sorted({self.models[k]['source'] for k in selected}))

    def system_map(self):
        """Readable entry map; actual dependency edges have their own diagram."""
        svg=ET.Element(f'{{{SVG_NS}}}svg',dict(viewBox='0 0 1080 640',width='1080',height='640',role='img',**{'aria-label':'Cela aplikacija'}))
        def element(tag,parent=svg,text=None,**attrs):
            item=ET.SubElement(parent,f'{{{SVG_NS}}}{tag}',{k.replace('_','-'):str(v) for k,v in attrs.items()})
            if text is not None:item.text=text
            return item
        element('style',text='text{font-family:"Segoe UI",Arial,sans-serif}a{cursor:pointer}.node:hover rect,.node a:focus rect{stroke-width:3;fill:#eaf5f3}')
        element('text',text='IMS ERP',x=24,y=35,font_size=26,font_weight=700,fill='#193c50')
        element('text',text='Poslovni moduli · izaberite modul za oblasti, modele i tokove rada',x=24,y=65,font_size=17,fill='#607786')
        business=[k for k in self.modules if k not in ('core','organizacija','naplata')]
        support=['core','organizacija','naplata']
        for index,key in enumerate(business+support):
            mod=self.modules[key]
            if key in support:
                x=24+support.index(key)*348;y=490;w=332
            else:
                x=24+(index%4)*261;y=90+(index//4)*117;w=245
            group=element('g',**{'class':'node','data-key':key,'data-route':'module/'+key})
            a=element('a',parent=group,href=url('module/'+key),target='_top')
            element('title',parent=a,text=mod['description'])
            element('rect',parent=a,x=x,y=y,width=w,height=100,rx=10,fill='#f4f9fb',stroke=mod['color'],stroke_width=1.5)
            element('rect',parent=a,x=x,y=y+17,width=5,height=65,rx=2,fill=mod['color'])
            element('text',parent=a,text=mod['name'],x=x+17,y=y+33,font_size=19,font_weight=650,fill='#193c50')
            element('text',parent=a,text=f'{mod["owned"]} definicija modela',x=x+17,y=y+57,font_size=15,fill='#607786')
            element('text',parent=a,text='Otvori modul →',x=x+17,y=y+82,font_size=14,fill=mod['color'])
        element('line',x1=24,y1=444,x2=1052,y2=444,stroke='#cbdce4')
        element('text',text='Zajedničke funkcije i nasleđeni deo sistema',x=24,y=474,font_size=17,fill='#607786')
        element('text',text='Pregled organizacije · stvarne FK / M2M veze pogledajte u „Zavisnosti modula“ ili „Svi modeli“.',x=24,y=622,font_size=15,fill='#607786')
        raw=ET.tostring(svg,encoding='unicode');filename='atlas/svg/system.svg'
        (HERE/filename).write_text(raw,encoding='utf-8')
        self.diagrams['system']=dict(id='system',title='Cela aplikacija',description='Od celine do detalja: modul → oblast → model → povezani model. Izaberite karticu za početak.',file=filename,svg=raw,sources=['ims_erp/urls.py'])

    def build(self):
        # Navigable overview: actual inter-module model dependencies, with shared foundations separated.
        nodes=[dict(key=k,label=f'{v["name"]}\n{v["owned"]} definicija modela\n{v["description"]}',route='module/'+k,color=v['color']) for k,v in self.modules.items()]
        counts=Counter((self.models[e['source']]['module'],self.models[e['target']]['module']) for e in self.edges if self.models[e['source']]['module']!=self.models[e['target']]['module'])
        deps=[dict(source=a,target=b,label=str(n)+' veza',tip=f'{MODULES[a][0]} → {MODULES[b][0]}: {n} FK / M2M polja') for (a,b),n in counts.items()]
        deps.append(dict(source='isplate',target='fleet',label='službeni nalozi',style='dashed',tip='Servis koristi postojeći PutniNalog; Isplate nema svoje tabele.'))
        self.system_map()
        self.graph('dependencies','Zavisnosti modula','Kliknite modul. Pune veze su agregirane FK / M2M zavisnosti modela iz koda; isprekidano je servisna zavisnost.',nodes,deps,rankdir='LR',sources=['ims_erp/urls.py'])
        self.model_graph('all-models','Svi modeli aplikacije',self.models,global_graph=True)
        self.model_graph('all-fields','Svi modeli i sva lokalno definisana polja',self.models,full=True,global_graph=True)
        for key,mod in self.modules.items():
            print('Module:',key,flush=True)
            areas=[a for a in mod['areas'] if a['models']]
            ns=[dict(key=key,label=mod['name'],route='models/'+key,color=mod['color'])]
            ns += [dict(key=a['id'],label=a['title']+'\n'+str(len(a['models']))+' modela',route='area/'+key+'/'+a['id'],color=mod['color']) for a in areas]
            ns += [dict(key='flows',label='Tokovi rada\nPoslovni procesi',route='flows/'+key,color=mod['color'])]
            es=[dict(source=key,target=a['id'],label='') for a in areas]+[dict(source=key,target='flows',label='')]
            self.graph('module/'+key,mod['name']+' · organizacija',mod['description'],ns,es,sources=mod['sources'])
            self.model_graph('models/'+key,mod['name']+' · modeli',mod['models'],neighbors=True)
            self.model_graph('fields/'+key,mod['name']+' · modeli i polja',mod['models'],full=True,neighbors=True)
            for area in areas:
                self.model_graph('area/'+key+'/'+area['id'],mod['name']+' · '+area['title'],area['models'],neighbors=True)
                self.model_graph('area-fields/'+key+'/'+area['id'],mod['name']+' · '+area['title']+' · polja',area['models'],full=True,neighbors=True)
        for key in self.models:
            self.model_graph('model/'+key,self.models[key]['name']+' · neposredne veze',[key],full=True,neighbors=True)
        for f in FLOWS:
            nodes=[dict(key=n,label=label,route='model/'+model if model else '',shape=shape,
                        color=self.modules[f['module']]['color'],tip=model or label) for n,label,model,shape in f['nodes']]
            edges=[dict(source=a,target=b,label=label) for a,b,label in f['edges']]
            self.graph('flow/'+f['id'],f['title'],'Dijagram aktivnosti. '+f['note'],nodes,edges,rankdir='TB',sources=f['sources'])
        for module in ['',*self.modules]:
            fs=[f for f in FLOWS if not module or f['module']==module]
            nodes=[dict(key=f['id'],label=f['title']+'\n'+self.modules[f['module']]['name'],route='flow/'+f['id'],color=self.modules[f['module']]['color']) for f in fs]
            self.graph('flows'+('/'+module if module else ''),'Tokovi rada'+(' · '+self.modules[module]['name'] if module else ''),
                       'Izaberite proces. Klikabilni koraci vode na povezane modele.',nodes,[],rankdir='TB')
        # Reuse the reviewed infrastructure SVG, without generating a raster image.
        path=HERE/'svg/03-serveri-i-podaci.svg'
        svg=ET.tostring(ET.fromstring(path.read_text(encoding='utf-8')),encoding='unicode')
        self.diagrams['infrastructure']=dict(id='infrastructure',title='Servisi i izvori podataka',
            description='Dokumentovana konfiguracija; živi servisi nisu proveravani.',file='svg/03-serveri-i-podaci.svg',svg=svg,sources=['ims_erp/celery.py','nssm.bat'])
        data=dict(version=1,date=date.today().isoformat(),modules=self.modules,models=self.models,edges=self.edges,
                  flows=FLOWS,diagrams=self.diagrams,stats=dict(models=len(self.models),abstract=sum(m['abstract'] for m in self.models.values()),relations=len(self.edges)))
        # Script embedding works with file://; there is no fetch(), CDN or app server dependency.
        serialized=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</',r'<\/').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
        (HERE/'atlas/data.js').write_text('window.IMS_ATLAS = '+serialized+';\n',encoding='utf-8')
        manifest={k:{a:b for a,b in v.items() if a!='svg'} for k,v in self.diagrams.items()}
        (HERE/'atlas/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        shutil.copyfile(HERE/'atlas/viewer.html',HERE/'index.html')
        print(f'OK: {len(self.diagrams)} views, {len(self.models)} model definitions, {len(self.edges)} model relations. SVG only.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dot',default=shutil.which('dot') or 'C:/Program Files (x86)/Graphviz/bin/dot.exe')
    args=parser.parse_args();Atlas(args.dot).build()

if __name__=='__main__':main()
