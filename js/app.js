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
let undoStack=[], redoStack=[], histTimer=null, restoringHistory=false;
let searchQuery='';
let layoutMode=localStorage.getItem('jr_layout')||'flow';

function loadGraph(){
  try{const raw=localStorage.getItem(STORE);if(raw){const g=JSON.parse(raw);if(g&&g.nodes&&g.edges){if(!g.cards)g.cards=[];g.nodes.forEach(n=>{if(!n.files)n.files=[];});g.edges.forEach(e=>{if(!e.files)e.files=[];});g.cards.forEach(c=>{if(!c.files)c.files=[];if(!c.links)c.links=[];});return g;}}}catch(e){}
  return defaultGraph();
}
function persistRaw(){try{localStorage.setItem(STORE,JSON.stringify(G));}catch(e){showHint('⚠ Guardado automático lleno (archivos grandes). Usa Exportar para respaldar.');}}
function persist(){persistRaw();if(!restoringHistory)scheduleHistory();}

/* ===================== HISTORY (deshacer / rehacer) ===================== */
function histInit(){undoStack=[JSON.stringify(G)];redoStack=[];updateHistButtons();}
function scheduleHistory(){clearTimeout(histTimer);histTimer=setTimeout(commitHistory,500);}
function commitHistory(){
  clearTimeout(histTimer);histTimer=null;
  const s=JSON.stringify(G);
  if(undoStack.length&&undoStack[undoStack.length-1]===s)return;
  undoStack.push(s);if(undoStack.length>60)undoStack.shift();
  redoStack=[];updateHistButtons();
}
function restoreState(s){
  restoringHistory=true;
  G=JSON.parse(s);pos={};ensurePositions();
  selFmt=selArea=selCard=null;
  const at=document.querySelector('.tab.active');
  showList(at?at.dataset.tab:'formatos');
  persistRaw();buildLists();
  restoringHistory=false;
}
function undo(){
  commitHistory();
  if(undoStack.length<2)return;
  redoStack.push(undoStack.pop());
  restoreState(undoStack[undoStack.length-1]);
  updateHistButtons();showHint('↶ Deshacer');
}
function redo(){
  if(!redoStack.length)return;
  const s=redoStack.pop();undoStack.push(s);
  restoreState(s);
  updateHistButtons();showHint('↷ Rehacer');
}
function updateHistButtons(){
  const u=document.getElementById('btnUndo'),r=document.getElementById('btnRedo');
  if(u)u.disabled=undoStack.length<2;
  if(r)r.disabled=redoStack.length===0;
}

/* ===================== HELPERS ===================== */
const svg=document.getElementById('wf');
const viewport=document.getElementById('viewport');
const gLinks=document.getElementById('gLinks');
const gEdges=document.getElementById('gEdges');
const gLabels=document.getElementById('gLabels');
const gNodes=document.getElementById('gNodes');
const gZones=document.getElementById('gZones');
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
  if(!anyStored){ applyLayout(layoutMode); }
  else{G.nodes.forEach(n=>{pos[n.id]=(n.x!=null&&n.y!=null)?{x:n.x,y:n.y}:{x:CX,y:CY};});}
  (G.cards||[]).forEach(c=>{pos[c.id]={x:c.x!=null?c.x:CX,y:c.y!=null?c.y:CY};});
}

/* ===================== LAYOUT POR FLUJO (capas izq→der) ===================== */
/* Separa la "dirección/reportes" (banda superior) del flujo operativo. */
function classifyBands(){
  const outDeg={}, inDeg={};
  G.nodes.forEach(n=>{outDeg[n.id]=0;inDeg[n.id]=0;});
  G.edges.forEach(e=>{if(outDeg[e.from]!=null)outDeg[e.from]++;if(inDeg[e.to]!=null)inDeg[e.to]++;});
  const isMgmt=n=> n.hub || n.cat==='reporte' || (outDeg[n.id]===0 && inDeg[n.id]>=2);
  let mgmt=G.nodes.filter(isMgmt), ops=G.nodes.filter(n=>!isMgmt(n));
  if(!ops.length){ops=G.nodes.slice();mgmt=[];}
  return {mgmt,ops};
}
/* Estructura por capas compartida por las vistas Flujo y Jerárquico. */
function computeFlowStructure(){
  const {mgmt,ops}=classifyBands();
  const opIds=new Set(ops.map(n=>n.id));
  const fwd={}, incList={};
  ops.forEach(n=>{fwd[n.id]=[];incList[n.id]=[];});
  G.edges.forEach(e=>{if(opIds.has(e.from)&&opIds.has(e.to)&&e.from!==e.to){fwd[e.from].push(e.to);incList[e.to].push(e.from);}});
  /* romper ciclos: las aristas hacia un nodo en la pila (back-edge) se ignoran */
  const state={}, keep={};
  ops.forEach(n=>keep[n.id]=[]);
  function dfs(u){state[u]=1;fwd[u].forEach(v=>{if(state[v]===1)return;keep[u].push(v);if(!state[v])dfs(v);});state[u]=2;}
  ops.forEach(n=>{if(!state[n.id])dfs(n.id);});
  /* asignar capa = camino más largo desde las fuentes (sin ciclos) */
  const layer={}, indeg={};
  ops.forEach(n=>{layer[n.id]=0;indeg[n.id]=0;});
  ops.forEach(n=>keep[n.id].forEach(v=>indeg[v]++));
  let q=ops.filter(n=>indeg[n.id]===0).map(n=>n.id);
  while(q.length){const u=q.shift();keep[u].forEach(v=>{if(layer[v]<layer[u]+1)layer[v]=layer[u]+1;if(--indeg[v]===0)q.push(v);});}
  let maxL=0;ops.forEach(n=>{if(layer[n.id]>maxL)maxL=layer[n.id];});
  const cols=[];for(let i=0;i<=maxL;i++)cols.push([]);
  ops.forEach(n=>cols[layer[n.id]].push(n));
  /* ordenar dentro de cada capa por baricentro (reduce cruces) */
  function pmap(col){const m={};col.forEach((n,i)=>m[n.id]=i);return m;}
  function bc(n,map,pm){const ks=(map[n.id]||[]).filter(x=>pm[x]!=null);if(!ks.length)return 9999;return ks.reduce((s,x)=>s+pm[x],0)/ks.length;}
  for(let s=0;s<5;s++){
    for(let i=1;i<cols.length;i++){const pm=pmap(cols[i-1]);cols[i].sort((a,b)=>bc(a,incList,pm)-bc(b,incList,pm));}
    for(let i=cols.length-2;i>=0;i--){const pm=pmap(cols[i+1]);cols[i].sort((a,b)=>bc(a,fwd,pm)-bc(b,fwd,pm));}
  }
  return {mgmt,cols};
}
function syncPos(){G.nodes.forEach(n=>{if(pos[n.id]){n.x=pos[n.id].x;n.y=pos[n.id].y;}});}

/* VISTA: Flujo por etapas (izquierda → derecha) */
function flowLayout(){
  const {mgmt,cols}=computeFlowStructure();
  const COLW=380, ROWH=178, maxL=cols.length-1;
  const span=maxL*COLW, startX=CX-span/2, opCY=CY+90;
  cols.forEach((col,i)=>{const x=startX+i*COLW;const h=(col.length-1)*ROWH;col.forEach((n,j)=>{pos[n.id]={x,y:opCY-h/2+j*ROWH};});});
  if(mgmt.length){const topY=CY-170, cx0=startX+span/2, step=Math.max(320,(span||COLW)/Math.max(mgmt.length,1));
    mgmt.forEach((n,k)=>{pos[n.id]={x:cx0+(k-(mgmt.length-1)/2)*step,y:topY};});}
  syncPos();(G.cards||[]).forEach(c=>{if(pos[c.id]==null)pos[c.id]={x:CX,y:opCY+230};});
}
/* VISTA: Jerárquico (dirección arriba, niveles hacia abajo) */
function hierLayout(){
  const {mgmt,cols}=computeFlowStructure();
  const COLW=280, ROWGAP=200, topY=CY-340;
  if(mgmt.length){const w=(mgmt.length-1)*COLW;mgmt.forEach((n,k)=>{pos[n.id]={x:CX-w/2+k*COLW,y:topY};});}
  const startY=topY+(mgmt.length?ROWGAP:0);
  cols.forEach((col,i)=>{const y=startY+i*ROWGAP;const w=(col.length-1)*COLW;col.forEach((n,j)=>{pos[n.id]={x:CX-w/2+j*COLW,y};});});
  syncPos();(G.cards||[]).forEach((c,ci)=>{if(pos[c.id]==null)pos[c.id]={x:CX+ci*40,y:startY+cols.length*ROWGAP+40};});
}
/* VISTA: Por departamento (una columna por categoría/tipo) */
function deptGroups(){
  return Object.keys(CAT).map(k=>({cat:k,nodes:G.nodes.filter(n=>n.cat===k)})).filter(g=>g.nodes.length);
}
function deptLayout(){
  const groups=deptGroups();
  const COLW=300, ROWH=168, span=(groups.length-1)*COLW, startX=CX-span/2;
  groups.forEach((g,i)=>{const x=startX+i*COLW;const h=(g.nodes.length-1)*ROWH;g.nodes.forEach((n,j)=>{pos[n.id]={x,y:CY-h/2+j*ROWH};});});
  syncPos();(G.cards||[]).forEach(c=>{if(pos[c.id]==null)pos[c.id]={x:CX,y:CY+280};});
}
function applyLayout(mode){
  if(mode==='circle')circleLayout();
  else if(mode==='hier')hierLayout();
  else if(mode==='dept')deptLayout();
  else flowLayout();
}
/* Reorganiza una sola vez al estrenar las vistas (respeta arrastres después). */
function maybeAutoLayout(){
  if(!localStorage.getItem('jr_layout_v2')){applyLayout(layoutMode);savePositions();}
  try{localStorage.setItem('jr_layout_v2','1');}catch(e){}
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
function anchor(id,side){
  const p=pos[id],{w,h}=dims(id);
  if(side==='r')return{x:p.x+w/2,y:p.y};
  if(side==='l')return{x:p.x-w/2,y:p.y};
  if(side==='t')return{x:p.x,y:p.y-h/2};
  return{x:p.x,y:p.y+h/2};
}
/* Conector estilo diagrama: sale por el lado dominante con curva suave (cúbica). */
function curve(fromId,toId){
  const a=pos[fromId],b=pos[toId];if(!a||!b)return{d:'',lx:0,ly:0};
  const dx=b.x-a.x, dy=b.y-a.y, horiz=Math.abs(dx)>=Math.abs(dy);
  let s,e;
  if(horiz){s=anchor(fromId,dx>=0?'r':'l');e=anchor(toId,dx>=0?'l':'r');}
  else{s=anchor(fromId,dy>=0?'b':'t');e=anchor(toId,dy>=0?'t':'b');}
  let c1,c2;
  if(horiz){const k=Math.max(38,Math.abs(e.x-s.x)*0.45);c1={x:s.x+(dx>=0?k:-k),y:s.y};c2={x:e.x+(dx>=0?-k:k),y:e.y};}
  else{const k=Math.max(38,Math.abs(e.y-s.y)*0.45);c1={x:s.x,y:s.y+(dy>=0?k:-k)};c2={x:e.x,y:e.y+(dy>=0?-k:k)};}
  const d=`M${s.x},${s.y} C${c1.x},${c1.y} ${c2.x},${c2.y} ${e.x},${e.y}`;
  const lx=0.125*s.x+0.375*c1.x+0.375*c2.x+0.125*e.x;
  const ly=0.125*s.y+0.375*c1.y+0.375*c2.y+0.125*e.y;
  return{d,lx,ly};
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
    const g=el('g',{class:'node-card'+(n.hub?' hub':'')+(selArea===n.id?' sel':'')+(pickFirst===n.id?' pick':'')+(searchQuery&&!nodeMatches(n,searchQuery)?' dim':''),'data-id':n.id,transform:`translate(${p.x},${p.y})`});
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
    const g=el('g',{class:'node-card card-node'+(selCard===c.id?' sel':'')+(searchQuery&&!cardMatches(c,searchQuery)?' dim':''),'data-id':c.id,transform:`translate(${p.x},${p.y})`});
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
      gLinks.appendChild(el('path',{class:'cardlink'+(selCard===c.id?' hi':'')+(searchQuery&&!cardMatches(c,searchQuery)?' dim':''),d:geo.d}));
    });
  });
  /* edges (líneas y flechas) */
  const labelData=[];
  G.edges.forEach(e=>{
    if(!pos[e.from]||!pos[e.to])return;
    const geo=curve(e.from,e.to);const hi=selFmt===e.id;
    const edim=(searchQuery&&!edgeMatches(e,searchQuery))?' dim':'';
    gEdges.appendChild(el('path',{class:'edge'+(hi?' hi':'')+edim,d:geo.d,'marker-end':hi?'url(#arrowHi)':'url(#arrow)'}));
    const hit=el('path',{class:'edge-hit',d:geo.d});gEdges.appendChild(hit);
    hit.addEventListener('click',()=>selectFormat(e.id));
    if(labelsOn){
      const fcount=(e.files&&e.files.length)||0;
      const txt=clip(e.name,30);
      const tw=Math.max(140,txt.length*7.1+72);
      const ox=e.labelDx||0, oy=e.labelDy||0;
      labelData.push({e,hi,edim,txt,tw,fcount,lx:geo.lx,ly:geo.ly,ox,oy,manual:(Math.abs(ox)>1||Math.abs(oy)>1)});
    }
  });
  /* separar tarjetas de formato que se encimen (las arrastradas a mano quedan fijas) */
  if(labelsOn){
    labelsDecollide(labelData);
    const CH=42;
    labelData.forEach(L=>{
      const lxp=L.lx+L.ox, lyp=L.ly+L.oy;
      if(Math.abs(L.ox)>16||Math.abs(L.oy)>16){gLabels.appendChild(el('line',{class:'lbl-leader',x1:L.lx,y1:L.ly,x2:lxp,y2:lyp}));}
      const col=CAT[L.e.cat]?CAT[L.e.cat].c:'#c8a86b';
      const lg=el('g',{class:'lbl-g'+(L.hi?' hi':'')+L.edim,'data-id':L.e.id,transform:`translate(${lxp},${lyp})`});
      lg.appendChild(el('rect',{class:'lbl-bg',x:-L.tw/2,y:-CH/2,width:L.tw,height:CH,rx:13}));
      lg.appendChild(el('rect',{class:'lbl-strip',x:-L.tw/2,y:-CH/2,width:7,height:CH,rx:3.5,fill:col}));
      const ico=el('text',{class:'lbl-ico',x:-L.tw/2+26,y:5.5,'text-anchor':'middle'});ico.textContent='📄';lg.appendChild(ico);
      const tx=el('text',{class:'lbl-tx',x:-L.tw/2+44,y:5});tx.textContent=L.txt;lg.appendChild(tx);
      if(L.fcount){const fc=el('text',{class:'lbl-clip',x:L.tw/2-15,y:5,'text-anchor':'middle'});fc.textContent='📎'+L.fcount;lg.appendChild(fc);}
      gLabels.appendChild(lg);
    });
  }
}
/* Empuja verticalmente las etiquetas que chocan (con otras etiquetas o nodos). */
function labelsDecollide(items){
  const H=46,GAP=6;
  const box=(cx,cy,w)=>({x1:cx-w/2-GAP,y1:cy-H/2-GAP,x2:cx+w/2+GAP,y2:cy+H/2+GAP});
  const hit=(a,b)=>!(a.x2<b.x1||a.x1>b.x2||a.y2<b.y1||a.y1>b.y2);
  const placed=[];
  G.nodes.forEach(n=>{const p=pos[n.id];if(!p)return;const{w,h}=dims(n.id);placed.push({x1:p.x-w/2,y1:p.y-h/2,x2:p.x+w/2,y2:p.y+h/2});});
  items.filter(L=>L.manual).forEach(L=>placed.push(box(L.lx+L.ox,L.ly+L.oy,L.tw)));
  /* candidatos en anillos: prueba vertical, luego horizontal y diagonal, del más cercano al más lejano */
  const cand=[[0,0]];
  for(let r=1;r<=14;r++){const d=r*18;cand.push([0,d],[0,-d],[d,0],[-d,0],[d,d],[-d,d],[d,-d],[-d,-d]);}
  items.filter(L=>!L.manual).sort((a,b)=>(a.ly-b.ly)||(a.lx-b.lx)).forEach(L=>{
    let cx=0,cy=0;
    for(const o of cand){if(!placed.some(p=>hit(p,box(L.lx+o[0],L.ly+o[1],L.tw)))){cx=o[0];cy=o[1];break;}}
    L.ox+=cx;L.oy+=cy;placed.push(box(L.lx+L.ox,L.ly+L.oy,L.tw));
  });
}
function bboxOf(nodes){
  let minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9,any=false;
  nodes.forEach(n=>{const p=pos[n.id];if(!p)return;any=true;const{w,h}=dims(n.id);
    minx=Math.min(minx,p.x-w/2);maxx=Math.max(maxx,p.x+w/2);miny=Math.min(miny,p.y-h/2);maxy=Math.max(maxy,p.y+h/2);});
  return any?{minx,miny,maxx,maxy}:null;
}
function drawZone(b,label,color){
  const padX=30,padTop=34,padBot=22;
  const x=b.minx-padX, y=b.miny-padTop, w=(b.maxx-b.minx)+padX*2, h=(b.maxy-b.miny)+padTop+padBot;
  gZones.appendChild(el('rect',{class:'zone-band',x,y,width:w,height:h,rx:20}));
  let tx=x+18;
  if(color){gZones.appendChild(el('circle',{cx:x+15,cy:y+15,r:3.4,fill:color}));tx=x+26;}
  const t=el('text',{class:'zone-label',x:tx,y:y+18});t.textContent=label;gZones.appendChild(t);
}
function renderZones(){
  if(!gZones)return;
  gZones.innerHTML='';
  if(layoutMode==='dept'){
    deptGroups().forEach(g=>{const b=bboxOf(g.nodes);if(b)drawZone(b,CAT[g.cat].n,CAT[g.cat].c);});
    return;
  }
  if(layoutMode==='flow'||layoutMode==='hier'){
    const {mgmt}=classifyBands();
    const b=bboxOf(mgmt);
    if(b)drawZone(b,'Dirección · Reportes',null);
  }
}
function renderAll(){renderZones();renderEdges();renderNodes();}

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
/* ---- coincidencias de búsqueda ---- */
function _matches(q,...parts){return parts.some(p=>(p==null?'':String(p)).toLowerCase().includes(q));}
function nodeMatches(n,q){return _matches(q,n.title,n.person,n.kicker,n.start,n.end,(n.resp||[]).join(' '),CAT[n.cat]&&CAT[n.cat].n);}
function edgeMatches(e,q){const f=findNode(e.from),t=findNode(e.to);return _matches(q,e.name,e.purpose,e.decision,f&&f.title,t&&t.title,CAT[e.cat]&&CAT[e.cat].n);}
function cardMatches(c,q){return _matches(q,c.name,c.purpose,c.decision,CAT[c.cat]&&CAT[c.cat].n);}

function buildLists(){
  const q=searchQuery;
  const lg=document.getElementById('legend');lg.innerHTML='';
  Object.values(CAT).forEach(c=>lg.innerHTML+=`<span><i style="background:${c.c}"></i>${c.n}</span>`);
  const fi=document.getElementById('fmtItems');fi.innerHTML='';let fmtCount=0;
  G.edges.forEach(e=>{
    if(q&&!edgeMatches(e,q))return;fmtCount++;
    const f=findNode(e.from),t=findNode(e.to);const fc=(e.files&&e.files.length)?` <span class="clip">📎${e.files.length}</span>`:'';
    const d=document.createElement('div');d.className='item'+(selFmt===e.id?' sel':'');
    d.innerHTML=`<span class="dot" style="background:${CAT[e.cat]?CAT[e.cat].c:'#c8a86b'}"></span><span class="tag">línea</span>
      <div class="nm">${esc(e.name)}${fc}</div><div class="rt"><b>${f?esc(f.title):'?'}</b> → <b>${t?esc(t.title):'?'}</b></div>`;
    d.addEventListener('click',()=>selectFormat(e.id));fi.appendChild(d);
  });
  if(G.cards&&G.cards.length){
    G.cards.forEach(c=>{
      if(q&&!cardMatches(c,q))return;fmtCount++;
      const fc=(c.files&&c.files.length)?` <span class="clip">📎${c.files.length}</span>`:'';
      const lk=(c.links&&c.links.length)?c.links.map(id=>{const n=findNode(id);return n?esc(n.title):'';}).filter(Boolean).join(', '):'sin enlazar';
      const d=document.createElement('div');d.className='item'+(selCard===c.id?' sel':'');
      d.innerHTML=`<span class="dot" style="background:${CAT[c.cat]?CAT[c.cat].c:'#c8a86b'}"></span><span class="tag">tarjeta</span>
        <div class="nm">${esc(c.name)}${fc}</div><div class="rt">${esc(lk)}</div>`;
      d.addEventListener('click',()=>selectCard(c.id));fi.appendChild(d);
    });
  }
  if(q&&fmtCount===0)fi.innerHTML=`<div class="noresults">Sin formatos para “${esc(q)}”.</div>`;
  const ai=document.getElementById('areaItems');ai.innerHTML='';let areaCount=0;
  G.nodes.forEach(n=>{
    if(q&&!nodeMatches(n,q))return;areaCount++;
    const fc=(n.files&&n.files.length)?` <span class="clip">📎${n.files.length}</span>`:'';
    const d=document.createElement('div');d.className='item'+(selArea===n.id?' sel':'');
    d.innerHTML=`<span class="dot" style="background:${CAT[n.cat]?CAT[n.cat].c:'#c8a86b'}"></span>
      <div class="nm">${esc(n.title)}${n.hub?' ★':''}${fc}</div><div class="rt">${n.person?esc(n.person):'—'}</div>`;
    d.addEventListener('click',()=>selectArea(n.id));ai.appendChild(d);
  });
  if(q&&areaCount===0)ai.innerHTML=`<div class="noresults">Sin áreas para “${esc(q)}”.</div>`;
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
const VIEW_NAMES={flow:'Flujo por etapas',hier:'Jerárquico',dept:'Por departamento',circle:'Círculo'};
function setView(mode){
  if(!VIEW_NAMES[mode])mode='flow';
  layoutMode=mode;localStorage.setItem('jr_layout',mode);
  applyLayout(mode);savePositions();renderAll();fitView();
  const vs=document.getElementById('viewSelect');if(vs)vs.value=mode;
  showHint('Vista: '+VIEW_NAMES[mode]);
}
const viewSelect=document.getElementById('viewSelect');
if(viewSelect){viewSelect.value=layoutMode;viewSelect.addEventListener('change',()=>setView(viewSelect.value));}
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

/* ===================== UNDO / REDO + BÚSQUEDA ===================== */
document.getElementById('btnUndo').addEventListener('click',undo);
document.getElementById('btnRedo').addEventListener('click',redo);
window.addEventListener('keydown',e=>{
  if(!(e.metaKey||e.ctrlKey))return;
  const k=e.key.toLowerCase();
  if(k!=='z'&&k!=='y')return;
  const tag=((document.activeElement&&document.activeElement.tagName)||'').toLowerCase();
  if(tag==='input'||tag==='textarea'||tag==='select')return; /* dejar el deshacer nativo del campo */
  e.preventDefault();
  if(k==='y'||(k==='z'&&e.shiftKey))redo();else undo();
});

const searchInput=document.getElementById('searchInput');
const searchBar=document.querySelector('.searchbar');
function applySearch(){searchQuery=searchInput.value.trim().toLowerCase();
  searchBar.classList.toggle('has-text',!!searchInput.value);buildLists();renderAll();}
searchInput.addEventListener('input',applySearch);
searchInput.addEventListener('keydown',e=>{if(e.key==='Escape'){searchInput.value='';applySearch();}});
document.getElementById('searchClear').addEventListener('click',()=>{searchInput.value='';applySearch();searchInput.focus();});

let hintT;function showHint(m){const h=document.getElementById('hint');h.textContent=m;h.classList.add('show');clearTimeout(hintT);hintT=setTimeout(()=>h.classList.remove('show'),2800);}
const flashT={};function flash(id){const e=document.getElementById(id);e.classList.add('show');clearTimeout(flashT[id]);flashT[id]=setTimeout(()=>e.classList.remove('show'),1000);}

/* ===================== INIT ===================== */
resizeVB();ensurePositions();maybeAutoLayout();bindFmt();bindCard();bindArea();renderAll();buildLists();applyView();fitView();histInit();
window.addEventListener('resize',resizeVB);
setTimeout(()=>showHint('Agrega formatos como línea entre áreas o como tarjeta independiente · se guarda solo'),500);
