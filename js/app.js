/* ===================== CONSTANTS ===================== */
const CX=600, CY=410, R=300, NW=190, NH=78, HUBW=170, HUBH=92, CARDW=172, CARDH=66;
const STORE='jr_workflow_v3';
const CAT={
  compra:{c:'#c8a86b',n:'Compra / Proveedor'},
  inventario:{c:'#8fa8b2',n:'Inventario'},
  calidad:{c:'#b58db0',n:'Calidad'},
  finanzas:{c:'#9cb58d',n:'Finanzas'},
  cliente:{c:'#c99b86',n:'Cliente / Venta'},
  reporte:{c:'#bfb69b',n:'Reporte / Dirección'}
};

/* ===================== DEFAULT GRAPH ===================== */
function defaultGraph(){
  const nodes=[
   {id:'compras',title:'Compras',person:'Reyna',kicker:'Proveedores · Inversión',cat:'compra',files:[],
    resp:['Identificar y negociar proveedores en Alibaba (precio y ~16% de shipping)','Generar y pagar órdenes de compra según necesidades de inventario','Registrar pagos en el informe de inversión y en Notion','Correo a Shop & Cross con la información de pago de cada OC','Crecer la inversión ~20% cada mes y supervisar las demás áreas'],
    start:'Tras analizar las necesidades de inventario con base en ventas, o cuando Inventario avisa que un producto se agotó.',
    end:'Cuando la mercancía llega a Monterrey, se traslada a Hermosillo y se recibe en Jewelry Remate; o cuando se genera la OC.'},
   {id:'logistica',title:'Compras / Logística',person:'Celeste',kicker:'Guías · Órdenes · SKU',cat:'compra',files:[],
    resp:['Crear las guías de envío diarias y cargar inventario en Shopify','Generar OC de reabastecimiento y de producto nuevo; dar seguimiento al proveedor','Crear nombres, SKU y variantes (talla, color) y etiquetar productos','Seguimiento de guías Laredo → Hermosillo y devolución de rechazados','Mantener el reporte operativo y registrar pagos en Notion'],
    start:'Flujo de compra: arma la tabla en Excel con el detalle de la OC. Flujo de logística: contando los pedidos por realizar.',
    end:'Compras: cuando el proveedor envía la guía de rastreo. Logística: cuando el pedido en Shopify pasa a "entregado".'},
   {id:'calidad',title:'Control de Calidad',person:'Gisel',kicker:'Inspección · Outlet',cat:'calidad',files:[],
    resp:['Inspeccionar la calidad de productos y pedidos antes del envío','Verificar la ficha web: imágenes, medidas, color, ficha técnica y proveedor','Clasificar piezas como outlet o rechazadas (removiéndolas de la variante normal)','Adherir las guías de envío a los paquetes','Registrar rechazados con fotos en Drive y enlazarlos al reporte operativo'],
    start:'Flujo 1: cuando el producto recién llegado fue inventariado por Compras. Flujo 2: cuando los pedidos están listos para revisión.',
    end:'Flujo 1: los productos revisados pasan a Inventario. Flujo 2: tras adherir las guías, los pedidos quedan listos para despacho.'},
   {id:'almacen',title:'Almacén / Inventario',person:'',kicker:'Stock · Preparación',cat:'inventario',files:[],
    resp:['Verificar que la mercancía recibida coincida con compras y con Shopify','Guardar y organizar el almacén por colección','Preparar y procesar los pedidos de los clientes','Confirmar ficha completa: colección, costo, descripción, proveedor y ≥3 fotos','Elaborar reportes de inventario y detectar productos vencidos o sin etiquetar'],
    start:'Cuando recibe mercancía o cuando llega un pedido.',
    end:'Cuando el pedido está empacado o cuando guarda la mercancía en almacén.'},
   {id:'analisis',title:'Análisis de Datos',person:'',kicker:'Precios · Reportes',cat:'reporte',files:[],
    resp:['Elaborar las tablas de precios de cada orden de compra','Generar reportes diarios, semanales, mensuales y trimestrales','Mantener bases de datos de análisis y finanzas y el reporte operativo','Analizar la inversión en guías de envío','Actualizar precios en Shopify y apoyar en la generación de pedidos'],
    start:'Parte 1: revisar métricas en Shopify para los reportes. Parte 2: Compras envía la OC completada para revisión.',
    end:'Parte 1: presentación del reporte diario al CEO/gerencia. Parte 2: aprobación y, de ser necesario, ajustes a la OC.'},
   {id:'atencion',title:'Atención a Cliente',person:'Danahe',kicker:'Ventas · Postventa',cat:'cliente',files:[],
    resp:['Responder Instagram, WhatsApp, Messenger y Gmail y resolver dudas','Gestionar ventas y dar seguimiento a clientes potenciales','Resolver contracargos en PayPal y MercadoPago','Procesar ajustes por sobrepeso en Envia y rastrear paquetes con Estafeta','Confirmar con Almacén la disponibilidad de producto'],
    start:'Al recibir un mensaje del cliente por Instagram, WhatsApp, Messenger o Gmail.',
    end:'Cuando se respondieron todos los mensajes, se resolvió la inquietud o se completó la venta.'},
   {id:'ceo',title:'CEO / Gerencia',person:'',kicker:'Decisiones · Inversión',cat:'reporte',hub:true,files:[],
    resp:['Recibe el reporte diario, el reporte operativo y el informe de inversión','Aprueba las órdenes de compra y los ajustes de precio','Decide la estrategia de inversión (~20% mensual) y prioridades','Interviene en problemáticas de cualquier departamento'],
    start:'Cuando un área entrega un reporte o solicita una decisión / aprobación.',
    end:'Cuando se aprueba la inversión, se ajusta la OC o se resuelve la problemática.'}
  ];
  const edges=[
   {id:'f1',from:'almacen',to:'compras',cat:'inventario',files:[],name:'Aviso de Agotamiento',purpose:'Inventario notifica a Compras qué productos se agotaron, junto al reporte de inventario y los niveles de stock en Shopify.',decision:'¿Qué producto reabastecer y cuándo abrir una nueva orden de compra?'},
   {id:'f2',from:'compras',to:'logistica',cat:'compra',files:[],name:'Necesidades de Inventario',purpose:'Compras define el listado de piezas y cantidades a pedir con base en ventas y agotamientos para que Logística arme la OC.',decision:'¿Qué incluir en la orden de compra y con qué proveedor?'},
   {id:'f3',from:'logistica',to:'analisis',cat:'compra',files:[],name:'Orden de Compra (OC)',purpose:'Tabla en Excel con producto, cantidades, costo y shipping (~16%). Logística la envía a Análisis para revisión.',decision:'¿La inversión y los costos están bien? ¿Se aprueba o se ajusta la OC?'},
   {id:'f4',from:'analisis',to:'compras',cat:'compra',files:[],name:'Tabla de Precios + Aprobación',purpose:'Análisis devuelve la tabla de precios por pieza y el visto bueno de la OC para que Compras ejecute el pago.',decision:'Precio de venta / margen por pieza y autorización de pago al proveedor.'},
   {id:'f5',from:'compras',to:'ceo',cat:'finanzas',files:[],name:'Informe de Inversión',purpose:'Registro de pagos a proveedores y a Shop & Cross consolidado para Gerencia.',decision:'¿Estamos cumpliendo el crecimiento de inversión de ~20% mensual?'},
   {id:'f6',from:'logistica',to:'calidad',cat:'inventario',files:[],name:'Lote Recibido + Guías 2026',purpose:'Seguimiento de la guía de rastreo (Laredo → Hermosillo) en la Tabla de Guías 2026; al llegar, el lote pasa a inspección.',decision:'¿Cuándo llega la mercancía y qué lote entra a control de calidad?'},
   {id:'f7',from:'calidad',to:'almacen',cat:'calidad',files:[],name:'Producto Aprobado + Ficha Shopify',purpose:'Pieza que pasó calidad con su ficha completa: SKU, colección, costo, proveedor, descripción y ≥3 fotos.',decision:'¿El producto se publica en la web y se almacena por colección?'},
   {id:'f8',from:'calidad',to:'ceo',cat:'calidad',files:[],name:'Registro de Rechazados / Outlet',purpose:'Captura de piezas con defecto, fotos en Drive y enlace en el reporte operativo con su evaluación de calidad.',decision:'¿La pieza va a outlet, se rechaza o se devuelve al proveedor?'},
   {id:'f9',from:'almacen',to:'analisis',cat:'inventario',files:[],name:'Reporte de Inventario / Métricas',purpose:'Existencias y métricas de Shopify que Almacén entrega a Análisis para alimentar reportes y precios.',decision:'¿Qué se está moviendo y qué hay que reabastecer?'},
   {id:'f10',from:'analisis',to:'ceo',cat:'reporte',files:[],name:'Reportes D/S/M/Trimestral',purpose:'Reportes diario, semanal, mensual y trimestral de operaciones y ventas para la dirección.',decision:'Estrategia general, prioridades y necesidades de inventario.'},
   {id:'f11',from:'analisis',to:'atencion',cat:'cliente',files:[],name:'Precios y Disponibilidad',purpose:'Precios actualizados en Shopify e información de stock que Atención usa para cotizar y vender.',decision:'¿Qué ofrecer al cliente y a qué precio?'},
   {id:'f12',from:'atencion',to:'almacen',cat:'cliente',files:[],name:'Pedido de Cliente',purpose:'Venta confirmada que pasa a Almacén para preparación, previa confirmación de disponibilidad.',decision:'¿Hay stock? ¿Se prepara y empaca el pedido?'},
   {id:'f13',from:'almacen',to:'calidad',cat:'inventario',files:[],name:'Pedido Empacado (a revisión)',purpose:'Pedido preparado que se entrega a Calidad para la inspección final antes del despacho.',decision:'¿El pedido cumple calidad y puede enviarse?'},
   {id:'f14',from:'calidad',to:'atencion',cat:'cliente',files:[],name:'Guía de Envío / Pedido Listo',purpose:'Guía adherida al paquete y pedido listo; Atención da seguimiento al envío y al cliente.',decision:'Despacho del pedido y seguimiento de la entrega.'},
   {id:'f15',from:'atencion',to:'ceo',cat:'finanzas',files:[],name:'Contracargos y Ajustes',purpose:'Contracargos de PayPal / MercadoPago y ajustes por sobrepeso en Envia que requieren resolución.',decision:'¿Cómo se resuelve la disputa o el cobro adicional?'},
   {id:'f16',from:'logistica',to:'ceo',cat:'finanzas',files:[],name:'Registros en Notion',purpose:'Registro de pagos de envíos, servicios de transporte, compras y gastos de suministros en Notion.',decision:'Control de gasto y salud financiera de la operación.'}
  ];
  const cards=[];
  return {nodes,edges,cards};
}

/* ===================== STATE ===================== */
let G=loadGraph();
let pos={};
let view={tx:0,ty:0,k:1};
let selFmt=null, selArea=null, selCard=null;
let labelsOn=true, connectMode=false, pickFirst=null;

function loadGraph(){
  try{const raw=localStorage.getItem(STORE);if(raw){const g=JSON.parse(raw);if(g&&g.nodes&&g.edges){if(!g.cards)g.cards=[];g.nodes.forEach(n=>{if(!n.files)n.files=[];});g.edges.forEach(e=>{if(!e.files)e.files=[];});g.cards.forEach(c=>{if(!c.files)c.files=[];if(!c.links)c.links=[];});return g;}}}catch(e){}
  return defaultGraph();
}
function persist(){try{localStorage.setItem(STORE,JSON.stringify(G));}catch(e){showHint('⚠ Guardado automático lleno (archivos grandes). Usa Exportar para respaldar.');}}

/* ===================== HELPERS ===================== */
const svg=document.getElementById('wf');
const viewport=document.getElementById('viewport');
const gLinks=document.getElementById('gLinks');
const gEdges=document.getElementById('gEdges');
const gLabels=document.getElementById('gLabels');
const gNodes=document.getElementById('gNodes');
const findNode=id=>G.nodes.find(n=>n.id===id);
const findCard=id=>(G.cards||[]).find(c=>c.id===id);
const isCard=id=>!!findCard(id);
function dims(id){if(isCard(id))return{w:CARDW,h:CARDH};const n=findNode(id);return n&&n.hub?{w:HUBW,h:HUBH}:{w:NW,h:NH};}

function resizeVB(){const r=svg.getBoundingClientRect();svg.setAttribute('viewBox',`0 0 ${r.width} ${r.height}`);}
function applyView(){viewport.setAttribute('transform',`translate(${view.tx},${view.ty}) scale(${view.k})`);document.getElementById('zLbl').textContent=Math.round(view.k*100)+'%';}

function circleLayout(){
  const ring=G.nodes.filter(n=>!n.hub);const hub=G.nodes.find(n=>n.hub);
  const step=360/Math.max(ring.length,1);
  ring.forEach((n,i)=>{const ang=(-90+i*step)*Math.PI/180;pos[n.id]={x:CX+R*Math.cos(ang),y:CY+R*Math.sin(ang)};});
  if(hub) pos[hub.id]={x:CX,y:CY};
}
function ensurePositions(){
  const anyStored=G.nodes.some(n=>n.x!=null);
  if(!anyStored){circleLayout();}
  else{G.nodes.forEach(n=>{pos[n.id]=(n.x!=null&&n.y!=null)?{x:n.x,y:n.y}:{x:CX,y:CY};});}
  (G.cards||[]).forEach(c=>{pos[c.id]={x:c.x!=null?c.x:CX,y:c.y!=null?c.y:CY};});
}
function savePositions(){
  G.nodes.forEach(n=>{if(pos[n.id]){n.x=pos[n.id].x;n.y=pos[n.id].y;}});
  (G.cards||[]).forEach(c=>{if(pos[c.id]){c.x=pos[c.id].x;c.y=pos[c.id].y;}});
  persist();
}

function borderPoint(id,tx,ty){
  const p=pos[id],{w,h}=dims(id);const dx=tx-p.x,dy=ty-p.y;
  if(dx===0&&dy===0)return{x:p.x,y:p.y};
  const hw=w/2+6,hh=h/2+6;
  const sx=dx!==0?hw/Math.abs(dx):Infinity, sy=dy!==0?hh/Math.abs(dy):Infinity;
  const s=Math.min(sx,sy);return{x:p.x+dx*s,y:p.y+dy*s};
}
function curve(fromId,toId){
  const a=pos[fromId],b=pos[toId];if(!a||!b)return{d:'',lx:0,ly:0};
  const p1=borderPoint(fromId,b.x,b.y),p2=borderPoint(toId,a.x,a.y);
  const mx=(p1.x+p2.x)/2,my=(p1.y+p2.y)/2;
  const dx=p2.x-p1.x,dy=p2.y-p1.y,len=Math.hypot(dx,dy)||1;
  const nx=-dy/len,ny=dx/len,bow=Math.min(60,len*0.16);
  const sign=(nx*(CX-mx)+ny*(CY-my))>0?-1:1;
  const cx=mx+nx*bow*sign,cy=my+ny*bow*sign;
  return{d:`M${p1.x},${p1.y} Q${cx},${cy} ${p2.x},${p2.y}`,lx:(p1.x+2*cx+p2.x)/4,ly:(p1.y+2*cy+p2.y)/4};
}
const NS='http://www.w3.org/2000/svg';
const el=(t,a)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;};
function toStage(evt){const pt=svg.createSVGPoint();pt.x=evt.clientX;pt.y=evt.clientY;return pt.matrixTransform(svg.getScreenCTM().inverse());}
function stageToWorld(s){return{x:(s.x-view.tx)/view.k,y:(s.y-view.ty)/view.k};}
function toWorld(evt){return stageToWorld(toStage(evt));}

/* ===================== RENDER ===================== */
function renderNodes(){
  gNodes.innerHTML='';
  G.nodes.forEach(n=>{
    const p=pos[n.id];if(!p)return;const{w,h}=dims(n.id);
    const g=el('g',{class:'node-card'+(n.hub?' hub':'')+(selArea===n.id?' sel':'')+(pickFirst===n.id?' pick':''),'data-id':n.id,transform:`translate(${p.x},${p.y})`});
    g.appendChild(el('rect',{class:'node-rect',x:-w/2,y:-h/2,width:w,height:h,rx:16,stroke:(n.hub||selArea===n.id)?'#c8a86b':'#2a2a30'}));
    g.appendChild(el('rect',{x:-w/2,y:-h/2,width:5,height:h,rx:2,fill:CAT[n.cat]?CAT[n.cat].c:'#c8a86b'}));
    const title=el('text',{class:'node-title',y:n.person?-4:5,fill:n.hub?'#c8a86b':'#f4f1ea'});title.textContent=n.title;g.appendChild(title);
    if(n.person){const per=el('text',{class:'node-person',y:15});per.textContent=n.person;g.appendChild(per);}
    const k=el('text',{class:'node-kicker',y:n.person?30:24});k.textContent=n.kicker||'';g.appendChild(k);
    if(n.files&&n.files.length){const c=el('text',{class:'node-clip',x:w/2-16,y:-h/2+18,'text-anchor':'middle'});c.textContent='📎'+n.files.length;g.appendChild(c);}
    gNodes.appendChild(g);
  });
  (G.cards||[]).forEach(c=>{
    const p=pos[c.id];if(!p)return;const w=CARDW,h=CARDH;
    const g=el('g',{class:'node-card card-node'+(selCard===c.id?' sel':''),'data-id':c.id,transform:`translate(${p.x},${p.y})`});
    g.appendChild(el('rect',{class:'node-rect',x:-w/2,y:-h/2,width:w,height:h,rx:12,stroke:selCard===c.id?'#c8a86b':'#2a2a30'}));
    g.appendChild(el('rect',{x:-w/2,y:-h/2,width:5,height:h,rx:2,fill:CAT[c.cat]?CAT[c.cat].c:'#c8a86b'}));
    const icon=el('text',{class:'node-clip',x:-w/2+16,y:-h/2+19,'text-anchor':'middle'});icon.textContent='📄';g.appendChild(icon);
    const title=el('text',{class:'card-title',y:2});title.textContent=clip(c.name,22);g.appendChild(title);
    const k=el('text',{class:'card-kicker',y:17});k.textContent='FORMATO';g.appendChild(k);
    if(c.files&&c.files.length){const fc=el('text',{class:'node-clip',x:w/2-16,y:-h/2+19,'text-anchor':'middle'});fc.textContent='📎'+c.files.length;g.appendChild(fc);}
    gNodes.appendChild(g);
  });
}
function clip(s,n){s=s||'';return s.length>n?s.slice(0,n-1)+'…':s;}
function renderEdges(){
  gEdges.innerHTML='';gLabels.innerHTML='';gLinks.innerHTML='';
  /* card links (dashed, behind) */
  (G.cards||[]).forEach(c=>{
    (c.links||[]).forEach(aid=>{
      if(!pos[c.id]||!pos[aid])return;
      const geo=curve(c.id,aid);
      gLinks.appendChild(el('path',{class:'cardlink'+(selCard===c.id?' hi':''),d:geo.d}));
    });
  });
  /* edges */
  G.edges.forEach(e=>{
    if(!pos[e.from]||!pos[e.to])return;
    const geo=curve(e.from,e.to);const hi=selFmt===e.id;
    gEdges.appendChild(el('path',{class:'edge'+(hi?' hi':''),d:geo.d,'marker-end':hi?'url(#arrowHi)':'url(#arrow)'}));
    const hit=el('path',{class:'edge-hit',d:geo.d});gEdges.appendChild(hit);
    hit.addEventListener('click',()=>selectFormat(e.id));
    if(labelsOn){
      const clipc=(e.files&&e.files.length)?' 📎':'';const txt=e.name+clipc;
      const tw=Math.max(70,txt.length*5.7)+18;
      const ox=e.labelDx||0, oy=e.labelDy||0, lxp=geo.lx+ox, lyp=geo.ly+oy;
      if(Math.abs(ox)>14||Math.abs(oy)>14){gLabels.appendChild(el('line',{x1:geo.lx,y1:geo.ly,x2:lxp,y2:lyp,stroke:'rgba(200,168,107,.28)','stroke-width':1,'stroke-dasharray':'3 3'}));}
      const lg=el('g',{class:'lbl-g'+(hi?' hi':''),'data-id':e.id,transform:`translate(${lxp},${lyp})`});
      lg.appendChild(el('rect',{class:'lbl-bg',x:-tw/2,y:-12,width:tw,height:24,rx:12}));
      lg.appendChild(el('circle',{cx:-tw/2+11,cy:0,r:3.2,fill:CAT[e.cat]?CAT[e.cat].c:'#c8a86b'}));
      const tx=el('text',{class:'lbl-tx',x:6,y:3.5});tx.textContent=txt;lg.appendChild(tx);
      gLabels.appendChild(lg);
    }
  });
}
function renderAll(){renderEdges();renderNodes();}

/* ===================== PAN / DRAG / ZOOM ===================== */
let drag=null, pan=null, labelDrag=null;
svg.addEventListener('pointerdown',e=>{
  const g=e.target.closest('.node-card');
  if(g){
    const id=g.dataset.id;
    if(connectMode){if(isCard(id)){showHint('“Conectar” es solo entre áreas; enlaza la tarjeta desde su editor');return;}handlePick(id);return;}
    const w=toWorld(e);drag={id,dx:w.x-pos[id].x,dy:w.y-pos[id].y,moved:false};
    try{svg.setPointerCapture(e.pointerId);}catch(err){}return;
  }
  const lg=e.target.closest('.lbl-g');
  if(lg){
    if(connectMode)return;
    const id=lg.dataset.id;const ed=G.edges.find(x=>x.id===id);if(!ed)return;
    const w=toWorld(e);labelDrag={id,sx:w.x,sy:w.y,dx0:ed.labelDx||0,dy0:ed.labelDy||0,moved:false};
    try{svg.setPointerCapture(e.pointerId);}catch(err){}return;
  }
  if(e.target.closest('.edge-hit')||e.target.closest('.edge'))return;
  const s=toStage(e);pan={sx:s.x,sy:s.y,tx0:view.tx,ty0:view.ty};svg.classList.add('panning');
  try{svg.setPointerCapture(e.pointerId);}catch(err){}
});
svg.addEventListener('pointermove',e=>{
  if(labelDrag){const w=toWorld(e);const ed=G.edges.find(x=>x.id===labelDrag.id);if(ed){ed.labelDx=labelDrag.dx0+(w.x-labelDrag.sx);ed.labelDy=labelDrag.dy0+(w.y-labelDrag.sy);labelDrag.moved=true;renderEdges();}return;}
  if(drag){const w=toWorld(e);pos[drag.id]={x:w.x-drag.dx,y:w.y-drag.dy};drag.moved=true;renderAll();return;}
  if(pan){const s=toStage(e);view.tx=pan.tx0+(s.x-pan.sx);view.ty=pan.ty0+(s.y-pan.sy);applyView();}
});
svg.addEventListener('pointerup',()=>{
  if(labelDrag){if(!labelDrag.moved)selectFormat(labelDrag.id);else persist();labelDrag=null;return;}
  if(drag){if(!drag.moved&&!connectMode){isCard(drag.id)?selectCard(drag.id):selectArea(drag.id);}else if(drag.moved)savePositions();drag=null;}
  if(pan){pan=null;svg.classList.remove('panning');}
});
svg.addEventListener('wheel',e=>{
  e.preventDefault();const s=toStage(e);const wpt=stageToWorld(s);
  const d=Math.max(-60,Math.min(60,e.deltaY));
  const factor=Math.exp(-d*0.0016);let k=Math.min(3,Math.max(0.3,view.k*factor));
  view.tx=s.x-k*wpt.x;view.ty=s.y-k*wpt.y;view.k=k;applyView();
},{passive:false});
function zoomBy(f){const r=svg.getBoundingClientRect();const cx=r.width/2,cy=r.height/2;
  const wpt={x:(cx-view.tx)/view.k,y:(cy-view.ty)/view.k};let k=Math.min(3,Math.max(0.3,view.k*f));
  view.tx=cx-k*wpt.x;view.ty=cy-k*wpt.y;view.k=k;applyView();}
function fitView(){
  const items=[...G.nodes,...(G.cards||[])];if(!items.length){view={tx:0,ty:0,k:1};applyView();return;}
  let minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;
  items.forEach(o=>{const p=pos[o.id];if(!p)return;const{w,h}=dims(o.id);
    minx=Math.min(minx,p.x-w/2);maxx=Math.max(maxx,p.x+w/2);miny=Math.min(miny,p.y-h/2);maxy=Math.max(maxy,p.y+h/2);});
  const r=svg.getBoundingClientRect();const pad=70;
  const k=Math.min(2.2,Math.min((r.width-pad*2)/(maxx-minx||1),(r.height-pad*2)/(maxy-miny||1)));
  view.k=Math.max(0.35,k);view.tx=(r.width-(minx+maxx)*view.k)/2;view.ty=(r.height-(miny+maxy)*view.k)/2;applyView();
}
function handlePick(id){
  if(!pickFirst){pickFirst=id;showHint('Ahora elige el área DESTINO…');renderNodes();return;}
  if(pickFirst===id){pickFirst=null;showHint('Selecciona el área de origen');renderNodes();return;}
  const e={id:'u'+Date.now(),from:pickFirst,to:id,cat:'reporte',files:[],name:'Nuevo formato',purpose:'',decision:''};
  G.edges.push(e);pickFirst=null;persist();renderAll();buildLists();selectFormat(e.id);showHint('Formato creado — complétalo en el panel');
}

/* ===================== LISTS ===================== */
const tabs=document.querySelectorAll('.tab');
tabs.forEach(t=>t.addEventListener('click',()=>{tabs.forEach(x=>x.classList.remove('active'));t.classList.add('active');showList(t.dataset.tab);}));
function hideEditors(){['editFormato','editCard','editArea'].forEach(i=>document.getElementById(i).classList.remove('show'));}
function showList(which){
  hideEditors();
  document.getElementById('listFormatos').classList.toggle('hidden',which!=='formatos');
  document.getElementById('listAreas').classList.toggle('hidden',which!=='areas');
  if(which==='formatos'){selArea=null;}else{selFmt=null;selCard=null;}
  renderAll();
}
function buildLists(){
  const lg=document.getElementById('legend');lg.innerHTML='';
  Object.values(CAT).forEach(c=>lg.innerHTML+=`<span><i style="background:${c.c}"></i>${c.n}</span>`);
  const fi=document.getElementById('fmtItems');fi.innerHTML='';
  G.edges.forEach(e=>{
    const f=findNode(e.from),t=findNode(e.to);const fc=(e.files&&e.files.length)?` <span class="clip">📎${e.files.length}</span>`:'';
    const d=document.createElement('div');d.className='item'+(selFmt===e.id?' sel':'');
    d.innerHTML=`<span class="dot" style="background:${CAT[e.cat]?CAT[e.cat].c:'#c8a86b'}"></span><span class="tag">línea</span>
      <div class="nm">${esc(e.name)}${fc}</div><div class="rt"><b>${f?esc(f.title):'?'}</b> → <b>${t?esc(t.title):'?'}</b></div>`;
    d.addEventListener('click',()=>selectFormat(e.id));fi.appendChild(d);
  });
  if(G.cards&&G.cards.length){
    G.cards.forEach(c=>{
      const fc=(c.files&&c.files.length)?` <span class="clip">📎${c.files.length}</span>`:'';
      const lk=(c.links&&c.links.length)?c.links.map(id=>{const n=findNode(id);return n?esc(n.title):'';}).filter(Boolean).join(', '):'sin enlazar';
      const d=document.createElement('div');d.className='item'+(selCard===c.id?' sel':'');
      d.innerHTML=`<span class="dot" style="background:${CAT[c.cat]?CAT[c.cat].c:'#c8a86b'}"></span><span class="tag">tarjeta</span>
        <div class="nm">${esc(c.name)}${fc}</div><div class="rt">${esc(lk)}</div>`;
      d.addEventListener('click',()=>selectCard(c.id));fi.appendChild(d);
    });
  }
  const ai=document.getElementById('areaItems');ai.innerHTML='';
  G.nodes.forEach(n=>{
    const fc=(n.files&&n.files.length)?` <span class="clip">📎${n.files.length}</span>`:'';
    const d=document.createElement('div');d.className='item'+(selArea===n.id?' sel':'');
    d.innerHTML=`<span class="dot" style="background:${CAT[n.cat]?CAT[n.cat].c:'#c8a86b'}"></span>
      <div class="nm">${esc(n.title)}${n.hub?' ★':''}${fc}</div><div class="rt">${n.person?esc(n.person):'—'}</div>`;
    d.addEventListener('click',()=>selectArea(n.id));ai.appendChild(d);
  });
}
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function fillCatSelect(sel){sel.innerHTML='';for(const k in CAT){const o=document.createElement('option');o.value=k;o.textContent=CAT[k].n;sel.appendChild(o);}}
function fillNodeSelect(sel){sel.innerHTML='';G.nodes.forEach(n=>{const o=document.createElement('option');o.value=n.id;o.textContent=n.title;sel.appendChild(o);});}

/* ===================== FILES ===================== */
function renderFileList(containerId, owner){
  const box=document.getElementById(containerId);box.innerHTML='';
  if(!owner.files||!owner.files.length){box.innerHTML='<div class="fileempty">Sin archivos. Adjunta plantillas, ejemplos o documentos de referencia.</div>';return;}
  owner.files.forEach((f,i)=>{
    const row=document.createElement('div');row.className='file-row';
    row.innerHTML=`<span class="fn" title="${esc(f.name)}">${esc(f.name)}</span>
      <span class="fa" data-i="${i}" data-act="dl" title="Descargar / abrir">⬇</span>
      <span class="fa del" data-i="${i}" data-act="rm" title="Quitar">✕</span>`;
    box.appendChild(row);
  });
  box.querySelectorAll('.fa').forEach(a=>a.addEventListener('click',()=>{
    const i=+a.dataset.i;
    if(a.dataset.act==='dl'){const f=owner.files[i];const l=document.createElement('a');l.href=f.data;l.download=f.name;document.body.appendChild(l);l.click();l.remove();}
    else{owner.files.splice(i,1);persist();renderFileList(containerId,owner);renderAll();buildLists();}
  }));
}
function attachFiles(fileList, owner, containerId){
  const arr=Array.from(fileList);let pending=arr.length;
  arr.forEach(file=>{const r=new FileReader();
    r.onload=()=>{owner.files.push({name:file.name,type:file.type,data:r.result});if(--pending===0){persist();renderFileList(containerId,owner);renderAll();buildLists();showHint('Archivo adjuntado');}};
    r.onerror=()=>{if(--pending===0){renderFileList(containerId,owner);}};
    r.readAsDataURL(file);});
}

/* ===================== EDIT FORMATO (LÍNEA) ===================== */
function selectFormat(id){
  selFmt=id;selArea=null;selCard=null;
  const e=G.edges.find(x=>x.id===id);if(!e)return;
  tabs.forEach(x=>x.classList.toggle('active',x.dataset.tab==='formatos'));
  document.getElementById('listFormatos').classList.add('hidden');document.getElementById('listAreas').classList.add('hidden');
  hideEditors();document.getElementById('editFormato').classList.add('show');
  document.getElementById('ef_name').value=e.name;
  fillNodeSelect(document.getElementById('ef_from'));document.getElementById('ef_from').value=e.from;
  fillNodeSelect(document.getElementById('ef_to'));document.getElementById('ef_to').value=e.to;
  fillCatSelect(document.getElementById('ef_cat'));document.getElementById('ef_cat').value=e.cat;
  document.getElementById('ef_purpose').value=e.purpose||'';document.getElementById('ef_decision').value=e.decision||'';
  if(!e.files)e.files=[];renderFileList('ef_files',e);
  renderAll();buildLists();
}
function bindFmt(){
  const map={ef_name:'name',ef_from:'from',ef_to:'to',ef_cat:'cat',ef_purpose:'purpose',ef_decision:'decision'};
  Object.keys(map).forEach(domId=>document.getElementById(domId).addEventListener('input',()=>{
    const e=G.edges.find(x=>x.id===selFmt);if(!e)return;e[map[domId]]=document.getElementById(domId).value;persist();renderAll();buildLists();flash('ef_saved');}));
  document.getElementById('ef_addFile').addEventListener('click',()=>document.getElementById('ef_fileInput').click());
  document.getElementById('ef_fileInput').addEventListener('change',ev=>{const e=G.edges.find(x=>x.id===selFmt);if(e&&ev.target.files.length)attachFiles(ev.target.files,e,'ef_files');ev.target.value='';});
  document.getElementById('ef_delete').addEventListener('click',()=>{G.edges=G.edges.filter(x=>x.id!==selFmt);selFmt=null;persist();renderAll();buildLists();showList('formatos');});
  document.getElementById('backF').addEventListener('click',()=>{selFmt=null;showList('formatos');buildLists();});
}

/* ===================== EDIT FORMATO (TARJETA) ===================== */
function selectCard(id){
  selCard=id;selArea=null;selFmt=null;
  const c=findCard(id);if(!c)return;
  tabs.forEach(x=>x.classList.toggle('active',x.dataset.tab==='formatos'));
  document.getElementById('listFormatos').classList.add('hidden');document.getElementById('listAreas').classList.add('hidden');
  hideEditors();document.getElementById('editCard').classList.add('show');
  document.getElementById('ec_name').value=c.name;
  fillCatSelect(document.getElementById('ec_cat'));document.getElementById('ec_cat').value=c.cat;
  document.getElementById('ec_purpose').value=c.purpose||'';document.getElementById('ec_decision').value=c.decision||'';
  const lb=document.getElementById('ec_links');lb.innerHTML='';
  G.nodes.forEach(n=>{
    const checked=(c.links||[]).includes(n.id)?'checked':'';
    const row=document.createElement('label');row.className='linkrow';
    row.innerHTML=`<input type="checkbox" data-id="${n.id}" ${checked}> ${esc(n.title)}`;
    lb.appendChild(row);
  });
  lb.querySelectorAll('input').forEach(inp=>inp.addEventListener('change',()=>{
    const cc=findCard(selCard);if(!cc)return;if(!cc.links)cc.links=[];
    const nid=inp.dataset.id;
    if(inp.checked){if(!cc.links.includes(nid))cc.links.push(nid);}else{cc.links=cc.links.filter(x=>x!==nid);}
    persist();renderAll();buildLists();flash('ec_saved');
  }));
  if(!c.files)c.files=[];renderFileList('ec_files',c);
  renderAll();buildLists();
}
function bindCard(){
  const map={ec_name:'name',ec_cat:'cat',ec_purpose:'purpose',ec_decision:'decision'};
  Object.keys(map).forEach(domId=>document.getElementById(domId).addEventListener('input',()=>{
    const c=findCard(selCard);if(!c)return;c[map[domId]]=document.getElementById(domId).value;persist();renderAll();buildLists();flash('ec_saved');}));
  document.getElementById('ec_addFile').addEventListener('click',()=>document.getElementById('ec_fileInput').click());
  document.getElementById('ec_fileInput').addEventListener('change',ev=>{const c=findCard(selCard);if(c&&ev.target.files.length)attachFiles(ev.target.files,c,'ec_files');ev.target.value='';});
  document.getElementById('ec_delete').addEventListener('click',()=>{G.cards=G.cards.filter(x=>x.id!==selCard);delete pos[selCard];selCard=null;persist();renderAll();buildLists();showList('formatos');});
  document.getElementById('backC').addEventListener('click',()=>{selCard=null;showList('formatos');buildLists();});
}

/* ===================== EDIT AREA ===================== */
function selectArea(id){
  selArea=id;selFmt=null;selCard=null;
  const n=findNode(id);if(!n)return;
  tabs.forEach(x=>x.classList.toggle('active',x.dataset.tab==='areas'));
  document.getElementById('listFormatos').classList.add('hidden');document.getElementById('listAreas').classList.add('hidden');
  hideEditors();document.getElementById('editArea').classList.add('show');
  document.getElementById('ea_title').value=n.title;document.getElementById('ea_person').value=n.person||'';document.getElementById('ea_kicker').value=n.kicker||'';
  fillCatSelect(document.getElementById('ea_cat'));document.getElementById('ea_cat').value=n.cat;
  document.getElementById('ea_resp').value=(n.resp||[]).join('\n');
  document.getElementById('ea_start').value=n.start||'';document.getElementById('ea_end').value=n.end||'';
  if(!n.files)n.files=[];renderFileList('ea_files',n);
  document.getElementById('ea_delete').style.display=n.hub?'none':'block';
  renderAll();buildLists();
}
function bindArea(){
  const simple={ea_title:'title',ea_person:'person',ea_kicker:'kicker',ea_cat:'cat',ea_start:'start',ea_end:'end'};
  Object.keys(simple).forEach(domId=>document.getElementById(domId).addEventListener('input',()=>{
    const n=findNode(selArea);if(!n)return;n[simple[domId]]=document.getElementById(domId).value;persist();renderAll();buildLists();flash('ea_saved');}));
  document.getElementById('ea_resp').addEventListener('input',()=>{const n=findNode(selArea);if(!n)return;n.resp=document.getElementById('ea_resp').value.split('\n').map(s=>s.trim()).filter(Boolean);persist();flash('ea_saved');});
  document.getElementById('ea_addFile').addEventListener('click',()=>document.getElementById('ea_fileInput').click());
  document.getElementById('ea_fileInput').addEventListener('change',ev=>{const n=findNode(selArea);if(n&&ev.target.files.length)attachFiles(ev.target.files,n,'ea_files');ev.target.value='';});
  document.getElementById('ea_delete').addEventListener('click',()=>{
    const n=findNode(selArea);if(!n||n.hub)return;
    G.nodes=G.nodes.filter(x=>x.id!==selArea);G.edges=G.edges.filter(e=>e.from!==selArea&&e.to!==selArea);
    (G.cards||[]).forEach(c=>{if(c.links)c.links=c.links.filter(x=>x!==selArea);});
    delete pos[selArea];selArea=null;persist();renderAll();buildLists();showList('areas');
  });
  document.getElementById('backA').addEventListener('click',()=>{selArea=null;showList('areas');buildLists();});
}

/* ===================== ADD ===================== */
function viewCenterWorld(){const r=svg.getBoundingClientRect();return stageToWorld({x:r.width/2,y:r.height/2});}
function addArea(){
  const id='n'+Date.now();const c=viewCenterWorld();
  const n={id,title:'Nueva área',person:'',kicker:'',cat:'reporte',resp:[],start:'',end:'',files:[],x:c.x+(Math.random()*80-40),y:c.y+(Math.random()*80-40)};
  G.nodes.push(n);pos[id]={x:n.x,y:n.y};persist();renderAll();buildLists();selectArea(id);showHint('Área creada — edítala y arrástrala');
}
function addCard(){
  const id='c'+Date.now();const c=viewCenterWorld();
  const card={id,name:'Nuevo formato',cat:'reporte',purpose:'',decision:'',links:[],files:[],x:c.x+(Math.random()*80-40),y:c.y+(Math.random()*80-40)};
  if(!G.cards)G.cards=[];G.cards.push(card);pos[id]={x:card.x,y:card.y};persist();renderAll();buildLists();selectCard(id);showHint('Formato (tarjeta) creado — arrástralo y enlázalo a las áreas que lo usan');
}
function addFmtLine(){
  if(G.nodes.length<2){showHint('Crea al menos dos áreas primero');return;}
  const a=G.nodes[0].id,b=G.nodes[1].id;
  const e={id:'u'+Date.now(),from:a,to:b,cat:'reporte',files:[],name:'Nuevo formato',purpose:'',decision:''};
  G.edges.push(e);persist();renderAll();buildLists();selectFormat(e.id);showHint('Formato de línea creado — elige Desde/Hacia');
}
document.getElementById('addArea').addEventListener('click',addArea);
document.getElementById('addFmtCard').addEventListener('click',addCard);
document.getElementById('addFmtLine').addEventListener('click',addFmtLine);
document.getElementById('btnAddNode').addEventListener('click',addArea);
document.getElementById('btnAddCard').addEventListener('click',addCard);

/* ===================== TOOLBAR ===================== */
const btnConnect=document.getElementById('btnConnect');
btnConnect.addEventListener('click',()=>{connectMode=!connectMode;pickFirst=null;btnConnect.classList.toggle('active',connectMode);
  showHint(connectMode?'Modo conexión: clic en ORIGEN y luego en DESTINO (solo áreas)':'Modo conexión desactivado');renderNodes();});
const btnLabels=document.getElementById('btnLabels');
btnLabels.addEventListener('click',()=>{labelsOn=!labelsOn;btnLabels.classList.toggle('active',labelsOn);renderAll();});
document.getElementById('btnRecircle').addEventListener('click',()=>{circleLayout();G.nodes.forEach(n=>{if(pos[n.id]){n.x=pos[n.id].x;n.y=pos[n.id].y;}});persist();renderAll();fitView();showHint('Áreas reacomodadas en círculo');});
document.getElementById('zIn').addEventListener('click',()=>zoomBy(1.1));
document.getElementById('zOut').addEventListener('click',()=>zoomBy(1/1.1));
document.getElementById('zFit').addEventListener('click',fitView);
document.getElementById('btnExport').addEventListener('click',()=>{savePositions();
  const blob=new Blob([JSON.stringify(G,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='workflow_jewelry_remate.json';a.click();showHint('Archivo exportado (incluye adjuntos)');});
document.getElementById('btnImport').addEventListener('click',()=>document.getElementById('fileInput').click());
document.getElementById('fileInput').addEventListener('change',ev=>{const f=ev.target.files[0];if(!f)return;const r=new FileReader();
  r.onload=()=>{try{const g=JSON.parse(r.result);if(g.nodes&&g.edges){if(!g.cards)g.cards=[];g.nodes.forEach(n=>{if(!n.files)n.files=[];});g.edges.forEach(e=>{if(!e.files)e.files=[];});g.cards.forEach(c=>{if(!c.files)c.files=[];if(!c.links)c.links=[];});G=g;pos={};ensurePositions();persist();renderAll();buildLists();showList('formatos');fitView();showHint('Workflow importado');}else showHint('Archivo no válido');}catch(e){showHint('No se pudo leer el archivo');}};
  r.readAsText(f);ev.target.value='';});
document.getElementById('btnReset').addEventListener('click',()=>{if(confirm('¿Volver al workflow original? Se perderán tus cambios actuales.')){G=defaultGraph();pos={};circleLayout();G.nodes.forEach(n=>{n.x=pos[n.id].x;n.y=pos[n.id].y;});persist();renderAll();buildLists();showList('formatos');fitView();showHint('Workflow restaurado');}});

let hintT;function showHint(m){const h=document.getElementById('hint');h.textContent=m;h.classList.add('show');clearTimeout(hintT);hintT=setTimeout(()=>h.classList.remove('show'),2800);}
const flashT={};function flash(id){const e=document.getElementById(id);e.classList.add('show');clearTimeout(flashT[id]);flashT[id]=setTimeout(()=>e.classList.remove('show'),1000);}

/* ===================== INIT ===================== */
resizeVB();ensurePositions();bindFmt();bindCard();bindArea();renderAll();buildLists();applyView();fitView();
window.addEventListener('resize',resizeVB);
setTimeout(()=>showHint('Agrega formatos como línea entre áreas o como tarjeta independiente · se guarda solo'),500);
