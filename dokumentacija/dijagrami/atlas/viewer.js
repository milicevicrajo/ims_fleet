'use strict';
(() => {
  const A=window.IMS_ATLAS, $=id=>document.getElementById(id);
  if(!A){$('description').textContent='Podaci nisu dostupni. Pokrenite build_atlas.py.';return;}
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const link=(route,label,small='')=>`<a href="#${esc(route)}">${esc(label)}${small?`<small>${esc(small)}</small>`:''}</a>`;
  const normalize=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,'dj').toLowerCase();
  const view=$('viewport'),stage=$('stage'),mem=new Map();
  let current='',currentDiagram='',x=0,y=0,z=1,width=100,height=100,fitted=true,drag=null,suppressClick=false;
  let renders=0;const historyRoutes=[];
  $('module-count').textContent=Object.keys(A.modules).length;
  $('inventory-count').textContent=`${A.stats.models} definicije · ${A.stats.relations} veza`;
  $('build-date').textContent='Stanje koda: '+A.date;
  $('module-nav').innerHTML=Object.values(A.modules).map(m=>`<a href="#module/${m.id}"><span class="dot" style="background:${m.color}"></span>${esc(m.name)}<span class="count">${m.owned}</span></a>`).join('');
  if(matchMedia('(max-width:900px)').matches)$('inspector').hidden=true;
  function route(){try{return decodeURIComponent(location.hash.slice(1))||'system';}catch{return 'system';}}
  function selectDiagram(raw){
    const [base,query='']=raw.split('?'),fields=new URLSearchParams(query).get('fields')==='1';
    let id=base;
    if(fields){if(base==='all-models')id='all-fields';else if(base.startsWith('models/'))id=base.replace('models/','fields/');else if(base.startsWith('area/'))id=base.replace('area/','area-fields/');}
    return {base,fields,id,diagram:A.diagrams[id]};
  }
  function routeModule(base){
    const p=base.split('/');
    if(p[0]==='model')return A.models[p[1]]?.module;
    if(['module','models','area','flow','flows'].includes(p[0]))return A.modules[p[1]]?p[1]:null;
    return null;
  }
  function apply(){stage.style.transform=`translate(${x}px,${y}px) scale(${z})`;$('zoom').textContent=Math.round(z*100)+'%';$('zoom-in').disabled=z>=3;$('zoom-out').disabled=z<=.005;}
  function fit(){fitted=true;z=Math.max(.005,Math.min((view.clientWidth-40)/width,(view.clientHeight-40)/height,1));x=(view.clientWidth-width*z)/2;y=(view.clientHeight-height*z)/2;apply();}
  function zoom(value,cx=view.clientWidth/2,cy=view.clientHeight/2){const next=Math.min(3,Math.max(.005,value));x=cx-(cx-x)*next/z;y=cy-(cy-y)*next/z;z=next;fitted=false;apply();}
  function crumbs(base,module,title){
    const pieces=[link('system','IMS ERP')];
    if(module)pieces.push(link('module/'+module,A.modules[module].name));
    if(base.startsWith('model/'))pieces.push(link('models/'+module,'Modeli'));
    if(base.startsWith('area/'))pieces.push(link('models/'+module,'Modeli'));
    if(base.startsWith('flow/'))pieces.push(link('flows/'+module,'Tokovi rada'));
    if(base!=='system'&&!base.startsWith('module/'))pieces.push(`<span aria-current="page">${esc(title)}</span>`);
    $('breadcrumbs').innerHTML=pieces.join('<span class="separator">›</span>');
  }
  function sources(paths){return `<h3>Izvori u repozitorijumu</h3><div class="links">${[...new Set(paths)].map(p=>`<a href="../../${esc(p)}" target="_blank" rel="noopener">${esc(p)}</a>`).join('')}</div>`;}
  function modelInfo(key){
    const m=A.models[key],out=A.edges.filter(e=>e.source===key),incoming=A.edges.filter(e=>e.target===key),flows=A.flows.filter(f=>f.nodes.some(n=>n[2]===key));
    let html=`<h2>${esc(m.name)}</h2>${link('module/'+m.module,A.modules[m.module].name)}<div><span class="badge">${m.abstract?'Apstraktni model':m.managed?'Django model':'Nasleđeni model'}</span><span class="badge">${m.fields.length} polja</span></div>`;
    if(m.table)html+=`<p>Tabela prema modelu: <span class="code">${esc(m.table)}</span>${m.table_explicit?'':' (izveden naziv)'}</p>`;
    html+=`<p>Izvor: ${esc(m.source)}:${m.line}</p>`;
    if(m.parents.length)html+=`<h3>Nasleđuje</h3><div class="links">${m.parents.map(k=>link('model/'+k,A.models[k].name)).join('')}</div>`;
    for(const note of m.notes)html+=`<p class="note">${esc(note)}</p>`;
    html+=`<h3>Polja i tipovi</h3><table class="field-list"><tbody>`;
    if(m.implicit_pk)html+='<tr><td>id<small>Implicitno Django polje</small></td><td>Primarni ključ</td></tr>';
    for(const f of m.fields){
      const flags=[f.primary?'PK':'',f.unique?'UNIQUE':'',f.type==='ManyToManyField'?'M2M':f.null?'NULL':'NOT NULL',f.blank?'blank=True':''].filter(Boolean).join(' · ');
      html+=`<tr><td>${esc(f.name)}<small>${esc(flags)}</small>${f.declared_in!==key?`<small>Nasleđeno: ${esc(f.declared_in)}</small>`:''}</td><td>${esc(f.type)}${f.target?'<br>'+link('model/'+f.target,A.models[f.target].name):''}${f.on_delete?`<small>${esc(f.on_delete)}</small>`:''}${f.through_model?`<small>through: ${link('model/'+f.through_model,A.models[f.through_model].name)}</small>`:''}</td></tr>`;
    }
    html+='</tbody></table>';
    function relationList(edges,reverse){return `<div class="links">${edges.map(e=>link('model/'+(reverse?e.source:e.target),`${reverse?'←':'→'} ${e.field} · ${A.models[reverse?e.source:e.target].name}`,`${e.type} · ${e.left} : ${e.right}`)).join('')}</div>`;}
    html+=`<h3>Izlazne veze (${out.length})</h3>`+relationList(out,false)+`<h3>Ko koristi ovaj model (${incoming.length})</h3>`+relationList(incoming,true);
    if(m.constraints.length)html+='<h3>Ograničenja iz koda</h3>'+m.constraints.map(c=>`<div class="constraint"><b>${esc(c.name||c.kind)}</b><br>${esc(c.definition)}</div>`).join('');
    const enums=Object.entries(m.enums);
    if(enums.length)html+='<h3>Definisane vrednosti (nisu prelazi stanja)</h3>'+enums.map(([name,choices])=>`<p><b>${esc(name)}</b><br>${choices.map(([code,label])=>esc(code)+' · '+esc(label)).join('<br>')}</p>`).join('');
    if(flows.length)html+='<h3>Povezani tokovi</h3><div class="links">'+flows.map(f=>link('flow/'+f.id,f.title)).join('')+'</div>';
    return html+sources([m.source]);
  }
  function overviewInfo(base,module,diagram){
    let html='';
    if(module){const m=A.modules[module];html=`<h2>${esc(m.name)}</h2><p>${esc(m.description)}</p><div class="stats"><div><strong>${m.owned}</strong><span>sopstvenih definicija</span></div><div><strong>${A.flows.filter(f=>f.module===module).length}</strong><span>tokova rada</span></div></div>`;
      if(!m.owned)html+='<p class="note">Modul nema svoje tabele. Prikazani su modeli iz drugih modula koje koristi.</p>';
      html+='<h3>Oblasti modula</h3><div class="links">'+m.areas.filter(a=>a.models.length).map(a=>link('area/'+module+'/'+a.id,a.title,a.models.length+' definicija modela')).join('')+'</div>';
    }else{html=`<h2>Od celine do detalja</h2><p>Otvorite modul, izaberite oblast ili modele, pa pratite veze do sledećeg modela.</p><div class="stats"><div><strong>${A.stats.models}</strong><span>definicije modela</span></div><div><strong>${A.stats.relations}</strong><span>FK / M2M veza</span></div></div><p>${A.stats.abstract} definicija su apstraktne osnove i nemaju sopstvenu tabelu.</p><div class="links">${link('all-models','Kompletan model aplikacije')}${link('flows','Pregled svih poslovnih tokova')}${link('infrastructure','Servisi i spoljni izvori')}</div>`;}
    if(base.startsWith('flow/')){const f=A.flows.find(f=>'flow/'+f.id===base);if(f)html=`<h2>Dijagram aktivnosti</h2><p>${esc(f.note)}</p><h3>Povezani modeli</h3><div class="links">${[...new Set(f.nodes.map(n=>n[2]).filter(Boolean))].map(k=>link('model/'+k,A.models[k].name,A.modules[A.models[k].module].name)).join('')}</div>`;}
    html+='<h3>Kako čitati prikaz</h3><p>Klik na element otvara povezani prikaz. Prelazak mišem ili fokus tastature ističe neposredne veze.</p>';
    html+=base==='system'?'<p>Kartice predstavljaju module koda. Zajedničke funkcije i nasleđeni modul izdvojeni su u donji red.</p>'+link('dependencies','Zavisnosti između modula'):base==='dependencies'?'<p>Veze između modula predstavljaju broj FK / M2M polja. Servisna veza Isplata je isprekidana.</p>':base.startsWith('flow')?'<p>Strelice pokazuju redosled obrade. Romb označava odluku. Klikabilni koraci vode na modele.</p>':'<p>Strelica ide od vlasnika polja do ciljnog modela. 1 = jedan; 0..1 = opciono / jedinstveno; 0..* = više zapisa. Zlatne veze prelaze granicu modula.</p><p>FK veze su iz koda. Kompozitna i uslovna ograničenja nalaze se u detalju modela. Jednaki poslovni kodovi nisu automatski strani ključevi.</p>';
    return html+sources(diagram.sources);
  }
  function highlight(key){
    const related=new Set([key]);
    stage.querySelectorAll('.edge').forEach(e=>{const active=e.dataset.from===key||e.dataset.to===key;if(active){related.add(e.dataset.from);related.add(e.dataset.to);}e.classList.toggle('faded',!active);e.classList.toggle('active',active);});
    stage.querySelectorAll('.node').forEach(n=>{n.classList.toggle('faded',!related.has(n.dataset.key));n.classList.toggle('active',n.dataset.key===key);});
  }
  function clearHighlight(){stage.querySelectorAll('.faded,.active').forEach(e=>e.classList.remove('faded','active'));}
  function render(){
    if(current)mem.set(current,{x,y,z,fitted});
    const raw=route(),selection=selectDiagram(raw),{base,fields}=selection;
    let diagram=selection.diagram;
    if(!diagram){$('title').textContent='Prikaz nije pronađen';$('description').textContent='Vratite se na mapu ili izaberite modul.';stage.replaceChildren();$('inspector').innerHTML=link('system','Mapa aplikacije');$('svg-link').removeAttribute('href');current=raw;return;}
    current=raw;currentDiagram=selection.id;renders++;historyRoutes.push(raw);
    const module=routeModule(base);
    $('title').textContent=diagram.title;$('description').textContent=diagram.description;document.title=diagram.title+' · IMS Atlas';
    crumbs(base,module,diagram.title);
    const tabs=module?[['module/'+module,'Organizacija'],['models/'+module,'Modeli'],['flows/'+module,'Tokovi rada']]:[['system','Mapa aplikacije'],['dependencies','Zavisnosti modula'],['all-models','Svi modeli'],['flows','Tokovi rada'],['infrastructure','Infrastruktura']];
    $('tabs').innerHTML=tabs.map(([href,label])=>`<a href="#${href}"${base===href||href.startsWith('models/')&&(base.startsWith('model/')||base.startsWith('area/'))||href.startsWith('flows/')&&base.startsWith('flow/')?' aria-current="page"':''}>${label}</a>`).join('');
    document.querySelectorAll('#module-nav a,.global-nav a').forEach(a=>{const target=a.hash.slice(1);if(target===base||module&&target==='module/'+module)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
    $('fields-control').hidden=!(base==='all-models'||base.startsWith('models/')||base.startsWith('area/'));$('fields').checked=fields;
    $('svg-link').href=diagram.file;
    $('inspector').innerHTML=base.startsWith('model/')?modelInfo(base.slice(6)):overviewInfo(base,module,diagram);
    $('inspector').scrollTop=0;
    stage.innerHTML=diagram.svg;
    const svg=stage.querySelector('svg'),box=svg.viewBox.baseVal;width=box.width;height=box.height;
    svg.setAttribute('width',width);svg.setAttribute('height',height);svg.style.width=width+'px';svg.style.height=height+'px';
    stage.querySelectorAll('.node').forEach(node=>{
      node.addEventListener('mouseenter',()=>highlight(node.dataset.key));node.addEventListener('mouseleave',clearHighlight);
      node.addEventListener('focusin',()=>highlight(node.dataset.key));node.addEventListener('focusout',clearHighlight);
    });
    const previous=mem.get(raw);if(previous){({x,y,z,fitted}=previous);if(fitted)fit();else apply();}else fit();
    $('back').disabled=renders<2;
    $('results').hidden=true;document.body.classList.remove('nav-open');$('menu').setAttribute('aria-expanded','false');
  }
  stage.addEventListener('click',event=>{
    const a=event.target.closest('a');if(!a)return;
    event.preventDefault();if(suppressClick)return;
    const target=a.getAttribute('href')||a.getAttributeNS('http://www.w3.org/1999/xlink','href');
    if(target?.includes('#'))location.hash=target.split('#').slice(1).join('#');
  });
  $('fields').addEventListener('change',()=>{location.hash=current.split('?')[0]+($('fields').checked?'?fields=1':'');});
  $('zoom-in').onclick=()=>zoom(z*1.25);$('zoom-out').onclick=()=>zoom(z/1.25);$('actual').onclick=()=>zoom(1);$('fit').onclick=fit;
  $('back').onclick=()=>history.back();
  $('info-toggle').onclick=()=>{$('inspector').hidden=!$('inspector').hidden;$('info-toggle').setAttribute('aria-expanded',String(!$('inspector').hidden));if(fitted)fit();};
  $('info-toggle').setAttribute('aria-expanded',String(!$('inspector').hidden));
  $('menu').onclick=()=>{document.body.classList.toggle('nav-open');$('menu').setAttribute('aria-expanded',String(document.body.classList.contains('nav-open')));};
  view.addEventListener('wheel',event=>{event.preventDefault();if(event.ctrlKey){const r=view.getBoundingClientRect();zoom(z*(event.deltaY<0?1.14:1/1.14),event.clientX-r.left,event.clientY-r.top);}else{x-=event.deltaX;y-=event.deltaY;fitted=false;apply();}},{passive:false});
  view.addEventListener('pointerdown',event=>{if(event.button!==0)return;drag={id:event.pointerId,x:event.clientX,y:event.clientY,startX:x,startY:y,moved:false};suppressClick=false;});
  view.addEventListener('pointermove',event=>{if(!drag||drag.id!==event.pointerId)return;const dx=event.clientX-drag.x,dy=event.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>5){drag.moved=true;view.setPointerCapture(event.pointerId);view.classList.add('dragging');}if(drag.moved){x=drag.startX+dx;y=drag.startY+dy;fitted=false;apply();}});
  function release(){if(drag)suppressClick=drag.moved;drag=null;view.classList.remove('dragging');setTimeout(()=>{suppressClick=false;},0);}
  view.addEventListener('pointerup',release);view.addEventListener('pointercancel',release);view.addEventListener('lostpointercapture',release);
  view.addEventListener('keydown',event=>{if(['+','=','-','0','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)){event.preventDefault();if(event.key==='+'||event.key==='=')zoom(z*1.25);else if(event.key==='-')zoom(z/1.25);else if(event.key==='0')fit();else{x+=event.key==='ArrowLeft'?60:event.key==='ArrowRight'?-60:0;y+=event.key==='ArrowUp'?60:event.key==='ArrowDown'?-60:0;fitted=false;apply();}}});
  new ResizeObserver(()=>{if(fitted)fit();}).observe(view);
  const index=[...Object.values(A.modules).map(m=>({route:'module/'+m.id,label:m.name,context:'Modul · '+m.description})),
    ...Object.values(A.models).map(m=>({route:'model/'+m.id,label:m.name,context:A.modules[m.module].name+' · '+m.module})),
    ...A.flows.map(f=>({route:'flow/'+f.id,label:f.title,context:'Tok rada · '+A.modules[f.module].name}))];
  $('search').addEventListener('input',()=>{const term=normalize($('search').value.trim());$('results').hidden=!term;if(!term)return;const matches=index.filter(i=>normalize(i.label+' '+i.context).includes(term)).sort((a,b)=>Number(normalize(b.label).startsWith(term))-Number(normalize(a.label).startsWith(term))).slice(0,35);$('results').innerHTML=matches.length?matches.map(i=>link(i.route,i.label,i.context)).join(''):'<p>Nema rezultata. Probajte naziv modela ili modula.</p>';});
  $('search').addEventListener('keydown',event=>{if(event.key==='Enter'){const a=$('results').querySelector('a');if(a){location.hash=a.hash;$('results').hidden=true;$('search').blur();}}if(event.key==='Escape')$('results').hidden=true;if(event.key==='ArrowDown'){$('results').querySelector('a')?.focus();event.preventDefault();}});
  addEventListener('hashchange',render);render();
  // Read-only diagnostics support offline validation without a Django process.
  window.atlasStatus=()=>({route:current,diagram:currentDiagram,zoom:z,x,y,renders,svg:!!stage.querySelector('svg')});
})();
