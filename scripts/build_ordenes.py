#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ordenes.html v2 — reglas fijas de Eduardo (14 ago 2026):
- Ventas 60d para cantidades; métricas/movimiento 90d.
- Estancado real: 0 ventas en 90d ajustado a la edad del producto (desde que se activó).
- Rebaja: SOLO por precio de comparación, pieza por pieza (rebaja/normal/código).
- Borradores/archivados: apartado propio por proveedor, marcando ventas estando activo.
- Export .xlsx con foto incrustada: #, FOTO, PRODUCTO, VARIANTE, SKU, PEDIR, COSTO US, TOTAL US, MATERIAL, OBS.
"""
import json, glob, re, unicodedata, datetime, os
from collections import defaultdict

# Rutas portables: funcionan en cualquier compu sin editar el archivo.
#   REPO    = la raiz del repo (se deduce de la ubicacion de este script)
#   SCRATCH = OC_SCRATCH si esta definido; si no, <REPO>/.scratch
#   HOY     = OC_HOY (AAAA-MM-DD) si esta definido; si no, la fecha de hoy
#   CORTE   = se arma solo a partir de HOY (ej. "15 ago 2026")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = os.environ.get('OC_SCRATCH') or os.path.join(REPO, '.scratch')
HOY = (datetime.date.fromisoformat(os.environ['OC_HOY'])
       if os.environ.get('OC_HOY') else datetime.date.today())
_MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
CORTE = '%d %s %d' % (HOY.day, _MESES[HOY.month - 1], HOY.year)

# Sello de actualizacion (pedido de Eduardo, 17 ago 2026): dia Y hora en que se corrio.
# OC_HORA (HH:MM) permite fijarla; si no, se toma la hora del momento en que corre.
_MESES_L = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
            'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
if os.environ.get('OC_HORA'):
    _hh, _mm = (int(x) for x in os.environ['OC_HORA'].split(':'))
else:
    _n = datetime.datetime.now()
    _hh, _mm = _n.hour, _n.minute
_ampm = 'AM' if _hh < 12 else 'PM'
_h12 = _hh % 12 or 12
ACTUALIZADO = '%d de %s de %d, %s %d:%02d %s' % (
    HOY.day, _MESES_L[HOY.month - 1], HOY.year,
    'a la' if _h12 == 1 else 'a las', _h12, _mm, _ampm)

def norm_sku(v):
    s = str(v or '').strip()
    if s.endswith('.0'): s = s[:-2]
    return s

def norm_t(s):
    s = unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).strip().upper()

# ---- productos (derivados de las paginas combinadas vp_*) ----
prods = {}
for f in sorted(glob.glob(SCRATCH + '/vp_0*.json')):
    for n in json.load(open(f))['data']['productVariants']['nodes']:
        pr = n['product']
        pid = pr['id'].rsplit('/', 1)[1]
        if pid not in prods:
            prods[pid] = {'vendor': (pr['vendor'] or '').strip(), 'status': pr['status'],
                          'title': pr['title'], 'img': (pr.get('featuredImage') or {}).get('url') or ''}

# edad (dias activo) de productos recientes; los no listados son viejos (>=90)
age = {}
for f in ['newprods_1.json', 'newprods_2.json']:
    d = json.load(open(SCRATCH + '/' + f))
    nodes = d['data']['products']['nodes'] if 'data' in d else d['nodes']
    for n in nodes:
        pid = n['id'].rsplit('/', 1)[1]
        ref = n.get('publishedAt') or n.get('createdAt')
        if ref:
            dt = datetime.date.fromisoformat(ref[:10])
            age[pid] = max(0, (HOY - dt).days)

# ---- variantes (incluye compareAtPrice) ----
variants = []
seen = set()
for f in sorted(glob.glob(SCRATCH + '/vp_0*.json')):
    for n in json.load(open(f))['data']['productVariants']['nodes']:
        vid = n['id'].rsplit('/', 1)[1]
        if vid in seen: continue
        seen.add(vid)
        variants.append({'vid': vid, 'sku': norm_sku(n.get('sku')),
                         # nombre de la variante DESDE EL CATALOGO. Antes solo venia de los datos
                         # de ventas, asi que los productos sin ventas salian sin variante.
                         'vtitle': (n.get('title') or '').strip(),
                         'price': float(n['price'] or 0),
                         'cap': float(n['compareAtPrice'] or 0) if n.get('compareAtPrice') else 0,
                         'inv': n.get('inventoryQuantity') or 0,
                         'pid': n['product']['id'].rsplit('/', 1)[1], 'title': n['product']['title']})

# ---- ventas 60d y 90d ----
def load_sales(path, sku_i, t_i, vt_i, u_i):
    out = {}
    d = json.load(open(path))
    for r in d['rows']:
        k = norm_sku(r[sku_i])
        u = int(r[u_i])
        if k:
            e = out.setdefault(k, {'u': 0, 'vt': r[vt_i], 't': r[t_i]})
            e['u'] += u
    return out
s60 = load_sales(SCRATCH + '/sales_HAIFENG.json', 0, 1, 2, 3)
for k, v in load_sales(SCRATCH + '/sales_OTROS.json', 1, 2, 3, 4).items():
    e = s60.setdefault(k, v);
    if e is not v: e['u'] += v['u']
s90 = load_sales(SCRATCH + '/sales90_HAIFENG.json', 0, 1, 2, 3)
for k, v in load_sales(SCRATCH + '/sales90_OTROS.json', 1, 2, 3, 4).items():
    e = s90.setdefault(k, v)
    if e is not v: e['u'] += v['u']

# ---- rebaja pieza por pieza (60d) ----
cap_by_sku = {}
for v in variants:
    if v['sku'] and v['cap'] > 0: cap_by_sku[v['sku']] = v['cap']
reb = defaultdict(lambda: {'r': 0, 'n': 0, 'c': 0})
with open(SCRATCH + '/lineitems60.jsonl') as f:
    for line in f:
        o = json.loads(line)
        if '__parentId' not in o: continue
        sku = norm_sku(o.get('sku'))
        if not sku: continue
        q = int(o.get('quantity') or 0)
        if q <= 0: continue
        orig = float(o['originalUnitPriceSet']['shopMoney']['amount'])
        disc = float(o['discountedUnitPriceSet']['shopMoney']['amount'])
        cap = cap_by_sku.get(sku, 0)
        if cap > 0 and orig <= 0.72 * cap:
            reb[sku]['r'] += q
        elif orig > 0 and disc < orig and (orig - disc) / orig >= 0.28:
            reb[sku]['c'] += q
        else:
            reb[sku]['n'] += q

# ---- dias desde la ultima venta por SKU (del detalle de 60d) ----
order_date = {}
last_sale = {}
with open(SCRATCH + '/lineitems60.jsonl') as f:
    for line in f:
        o = json.loads(line)
        if '__parentId' not in o:
            order_date[o['id']] = o.get('createdAt', '')[:10]
        else:
            sku = norm_sku(o.get('sku'))
            if not sku: continue
            d = order_date.get(o['__parentId'], '')
            if d and (sku not in last_sale or d > last_sale[sku]):
                last_sale[sku] = d

def dsl_for(sku, u60, u90):
    if sku in last_sale:
        return (HOY - datetime.date.fromisoformat(last_sale[sku])).days
    if u90 > 0:
        return 61   # vendio en 90d pero no en 60d -> minimo 60+ dias sin venta
    return 999

# ---- costos, material ----
cj = json.load(open(SCRATCH + '/costs.json'))
costs, material = cj['costs'], cj['material']
PROV_MAP = {'CYNTHIA': 'CYNTHIA CAO', 'NANCY': 'NANCY VIP', 'COCO ZHANG': 'COCOZHANG'}
ACTIVE_VENDORS = ['HAIFENG', 'ZOEY', 'CYNTHIA CAO', 'NANCY VIP', 'DINA DU', 'COCOMA', 'MOLLY']

# ---- duplicados entre ACTIVOS ----
tc = defaultdict(set)
for pid, p in prods.items():
    if p['status'] == 'ACTIVE': tc[norm_t(p['title'])].add(pid)
dups = {t for t, pids in tc.items() if len(pids) > 1}

# ---- filas ----
imgs, img_idx = [], {}
def img_i(url):
    if not url: return -1
    if url not in img_idx: img_idx[url] = len(imgs); imgs.append(url)
    return img_idx[url]

rows = []
for v in variants:
    p = prods.get(v['pid'])
    if not p: continue
    status = p['status']
    st = '' if status == 'ACTIVE' else ('D' if status == 'DRAFT' else 'A')
    vendor = p['vendor'].strip().upper()
    if vendor == 'M0LLY': vendor = 'MOLLY'
    sku = v['sku']
    e60 = s60.get(sku); e90 = s90.get(sku)
    # El catalogo manda; las ventas solo rellenan si el catalogo no trajo el titulo.
    vt = v.get('vtitle') or (e60 or e90 or {}).get('vt') or ''
    c = costs.get(sku)
    rb = reb.get(sku, {'r': 0, 'n': 0, 'c': 0})
    a = age.get(v['pid'], 999)
    ra = 1 if (v['cap'] > 0 and v['price'] > 0 and v['price'] <= 0.705 * v['cap']) else 0
    rows.append({
        # La llave 'k' identifica la fila y es con la que se guarda el borrador. Los productos
        # SIN SKU en Shopify (82 al 18 ago 2026) compartian la llave vacia: escribir una cantidad
        # en uno se la ponia a TODOS. Por eso, si no hay SKU se usa el id de variante.
        'k': sku or ('SINSKU-' + str(v['vid'])), 'ns': 0 if sku else 1,
        't': v['title'], 'vt': vt if vt != 'Default Title' else '',
        'v': vendor or 'OTROS', 'st': st, 'q': v['inv'], 'p': v['price'], 'cap': v['cap'],
        'i': img_i(p['img']), 'u': (e60 or {}).get('u', 0), 'u9': (e90 or {}).get('u', 0),
        'a': a, 'rb': rb['r'], 'pn': rb['n'], 'cd': rb['c'], 'ra': ra,
        'dsl': dsl_for(sku, (e60 or {}).get('u', 0), (e90 or {}).get('u', 0)),
        'c': round(c['best'], 2) if c else None, 'm': material.get(sku, ''),
        'dup': 1 if (st == '' and norm_t(v['title']) in dups) else 0,
    })

print('variantes:', len(rows), '| activas:', sum(1 for r in rows if r['st']==''),
      '| con rebaja vendida:', sum(1 for r in rows if r['rb']>0),
      '| rebaja activa hoy:', sum(1 for r in rows if r['ra'] and r['st']=='')),
print('| estancadas reales (90+d alta, 0 ventas 90d):', sum(1 for r in rows if r['st']=='' and r['u9']==0 and r['a']>=90 and r['q']>0),
      '| nuevas sin venta (<90d alta):', sum(1 for r in rows if r['st']=='' and r['u9']==0 and r['a']<90 and r['q']>0),
      '| lentas (40+d sin venta):', sum(1 for r in rows if r['st']=='' and r['q']>0 and not (r['u9']==0 and r['a']>=90) and ((r['u']>0 and r['dsl']>=40) or (r['u']==0 and r['u9']>0))))

DATA_JSON = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
IMGS_JSON = json.dumps(imgs, ensure_ascii=False, separators=(',', ':'))
VEND_JSON = json.dumps(ACTIVE_VENDORS, ensure_ascii=False)
# REGLA FIJA: "ya llego" SOLO si la fila esta 100% en verde en el Excel de la orden.
# Ninguna inferencia por stock. Los flags arrived vienen tal cual del parseo de los Excel.
# El "en camino" bueno (3 ordenes con cantidades) vive en scripts/transit_base.json y es la fuente
# de verdad. Solo se usa una copia del SCRATCH si existe (para pruebas); si no, la del repo.
_tb_scratch = SCRATCH + '/transit_base.json'
_tb_path = _tb_scratch if os.path.isfile(_tb_scratch) else REPO + '/scripts/transit_base.json'
tb = json.load(open(_tb_path))
TBASE_JSON = json.dumps(tb, ensure_ascii=False)

cv = open(REPO + '/centro-variantes.html', encoding='utf-8').read()
XLSX_LIB = re.search(r'(<script>/\*! xlsx\.js.*?</script>)', cv, re.S).group(1)

HTML = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jewelry Remate MX — Centro de órdenes de compra</title><style>
:root{--bg:#f6f7fb;--card:#fff;--ink:#15192b;--muted:#6b7285;--line:#e4e7f0;--a:#c0392b;--a-bg:#fdecea;
--ok:#1e7d46;--ok-bg:#e8f5ee;--warn:#b26a00;--warn-bg:#fdf3e0;--blue:#20508c;--blue-bg:#e8effa;--gray-bg:#f0f1f5;--reb:#8a2be2;--reb-bg:#f3eafe}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.nav{background:#0d1226;padding:0 18px}
.navin{max-width:1280px;margin:0 auto;display:flex;gap:4px;flex-wrap:wrap}
.nl{display:block;padding:9px 14px;font-size:13px;font-weight:600;text-decoration:none;
color:#9aa3c0;border-bottom:2px solid transparent}
.nl:hover{color:#fff}
.nl.on{color:#fff;border-bottom-color:#e8b93c}
.top{background:#141a33;color:#fff;padding:0 18px;position:sticky;top:0;z-index:30}
.in{max-width:1280px;margin:0 auto;display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.brand{padding:12px 0;font-weight:700}.brand small{display:block;font-weight:400;font-size:11px;color:#9aa3c0}
.tabs{display:flex;gap:4px;flex-wrap:wrap}
.tab{background:none;border:0;color:#c3cadf;padding:14px 13px;font:inherit;font-weight:600;cursor:pointer;border-bottom:3px solid transparent}
.tab[aria-selected="true"]{color:#fff;border-color:#e8b93c}
.wrap{max-width:1280px;margin:0 auto;padding:20px 18px 90px}
h2{margin:6px 0 4px;font-size:21px}
.note{color:var(--muted);font-size:13px;margin:2px 0 14px;max-width:100ch}
.note.upd{margin:2px 0 6px}.note.upd b{color:var(--ink)}
.pane{display:none}.pane.on{display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;cursor:pointer;border-left:6px solid var(--line)}
.card:hover{box-shadow:0 4px 14px rgba(20,26,51,.08)}
.card.rojo{border-left-color:var(--a)}.card.amarillo{border-left-color:#e8b93c}.card.verde{border-left-color:var(--ok)}
.card h3{margin:0 0 6px;font-size:16px}.card .sem{font-weight:700;font-size:12px}
.card.rojo .sem{color:var(--a)}.card.amarillo .sem{color:var(--warn)}.card.verde .sem{color:var(--ok)}
.card ul{margin:8px 0 0;padding:0;list-style:none;font-size:12.5px;color:var(--muted)}
.card li b{color:var(--ink)}
.controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}
select,input[type=search]{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff}
button.act{font:inherit;font-weight:600;padding:8px 14px;border:0;border-radius:8px;background:#141a33;color:#fff;cursor:pointer}
button.act.sec{background:#fff;color:#141a33;border:1px solid var(--line)}
button.act:disabled{opacity:.5}
.sec{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:14px 0;overflow:hidden}
.sec>h3{margin:0;padding:12px 16px;font-size:14.5px;border-bottom:1px solid var(--line)}
.sec>h3.a{color:var(--a);background:var(--a-bg)}.sec>h3.ok{color:var(--ok);background:var(--ok-bg)}
.sec>h3.warn{color:var(--warn);background:var(--warn-bg)}.sec>h3.gray{color:var(--muted);background:var(--gray-bg)}
.sec>h3.reb{color:var(--reb);background:var(--reb-bg)}
.sec .exp{padding:8px 16px 0;font-size:12.5px;color:var(--muted)}
.tblwrap{overflow-x:auto}table{border-collapse:collapse;width:100%}
th{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap;background:#fafbfe;position:sticky;top:0}
td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:middle;font-size:13px}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pname{font-weight:600;display:block}.vsub{display:block;font-size:11px;color:var(--muted)}
img.th{width:44px;height:44px;object-fit:cover;border-radius:8px;background:#eee;display:block}
.chip{display:inline-block;font-size:11px;font-weight:700;padding:1px 8px;border-radius:99px;white-space:nowrap;margin:1px 0}
.chip.agotado{color:var(--a);background:var(--a-bg)}.chip.critico{color:var(--warn);background:var(--warn-bg)}
.chip.bajo{color:var(--blue);background:var(--blue-bg)}.chip.ok{color:var(--ok);background:var(--ok-bg)}
.chip.top{color:#7a4bd6;background:#f0eafc}.chip.gris{color:var(--muted);background:var(--gray-bg)}
.chip.reb{color:var(--reb);background:var(--reb-bg)}.chip.dup{color:#8a2be2;background:#f3eafe}
.chip.nuevo{color:#0b7285;background:#e3fafc}
.pill{font-size:11px;font-weight:600}
.pill .r{color:var(--reb)}.pill .n{color:var(--ok)}.pill .c{color:var(--warn)}
input.q{width:64px;font:inherit;font-weight:700;text-align:right;padding:6px;border:1.5px solid var(--line);border-radius:8px}
input.q:disabled{background:var(--gray-bg);color:var(--muted);border-style:dashed;cursor:not-allowed;font-weight:400}
input.q.hot{border-color:var(--a);color:var(--a)}
input.q.edited{border-color:var(--blue);box-shadow:0 0 0 2px var(--blue-bg)}
tr.gris td{background:#fafafa}
.kpis{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 4px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 16px}
.kpi .l{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.kpi .v{font-size:20px;font-weight:750}
.drop{border:2px dashed #b9c0d4;border-radius:12px;padding:22px;text-align:center;color:var(--muted);cursor:pointer;background:var(--card)}
.drop.hot{border-color:var(--blue);background:var(--blue-bg)}
.uprow{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:800px){.uprow{grid-template-columns:1fr}}
.foot{max-width:1280px;margin:0 auto;padding:10px 18px 30px;color:var(--muted);font-size:12px}
.transitem{display:flex;justify-content:space-between;align-items:center;padding:8px 16px;border-bottom:1px solid var(--line);font-size:13px}
.transitem button{border:0;background:none;color:var(--a);font-weight:700;cursor:pointer}
</style></head><body>
<div class="nav"><div class="navin">
  <a class="nl on" href="ordenes.html">🚦 Órdenes de compra</a>
  <a class="nl" href="precios.html">💲 Tablas de precios</a>
</div></div>
<div class="top"><div class="in">
  <div class="brand"><small>Centro de órdenes de compra</small>Jewelry Remate MX</div>
  <div class="tabs" role="tablist">
    <button class="tab" data-p="semaforo" aria-selected="true">🚦 Semáforo</button>
    <button class="tab" data-p="orden" aria-selected="false">🧾 Orden sugerida</button>
    <button class="tab" data-p="camino" aria-selected="false">🚚 En camino</button>
    <button class="tab" data-p="mov" aria-selected="false">📈 Movimiento</button>
  </div>
</div></div>
<div class="wrap">

<div class="pane on" id="semaforo">
  <h2>¿A qué proveedor le toca orden?</h2>
  <p class="note">Datos de Shopify al <b>__CORTE__</b> · cantidades con ventas de <b>60 días</b> · movimiento y estancados con <b>90 días</b> (ajustado a la edad real del SKU) · fórmula: pzs/semana × 10 semanas (6 de viaje + 4 de colchón) − stock − en camino · +20% top · pares · <b>rebaja = solo precio de comparación con 30%+, pieza por pieza</b> (los códigos de descuento no cuentan como rebaja).</p>
  <div class="kpis" id="kpis"></div>
  <div class="cards" id="semcards"></div>
</div>

<div class="pane" id="orden">
  <h2>Orden sugerida por proveedor</h2>
  <p class="note upd">🕐 Actualizado el <b>__ACTUALIZADO__</b></p>
  <p class="note">Ajusta <b>PEDIR</b> a tu criterio. Las secciones de rebaja, borradores y estancados no traen cantidad sugerida — son tu decisión. La descarga es un <b>Excel con las fotos incrustadas</b>.</p>
  <div class="controls">
    <select id="vsel"></select>
    <input type="search" id="oq" placeholder="Buscar producto o SKU…">
    <button class="act" id="xlsx">⬇ Descargar orden (Excel)</button>
    <button class="act sec" id="reset">🗑 Descartar borrador y volver a sugeridos</button>
  </div>
  <p class="note" id="osum"></p>
  <p class="note" id="draft" style="background:var(--blue-bg);border-radius:8px;padding:8px 12px;color:var(--blue)"></p>
  <div id="ocont"></div>
</div>

<div class="pane" id="camino">
  <h2>Órdenes en camino</h2>
  <p class="note">Ya vienen precargadas con cantidades reales: <b>NANCY 09/07</b>, <b>CYNTHIA 07/07 (tu Excel ACT2)</b> y <b>HAIFENG 11/07 (tu Excel)</b>. Cada línea viene clasificada como 🔄 <b>Restock</b> (SKU con historial) o 🆕 <b>Nueva</b> (SKU nuevo o recién dado de alta). Si subiste alguna de estas órdenes manualmente, quítala con ✕ para no contarla doble. Arrastra el Excel de cada orden que mandes: una fila cuenta como "ya llegó" SOLO si <b>toda la fila está en verde</b> (una sola celda verde no cuenta — los colores agrupan guías); el resto se descuenta de lo sugerido. Se guarda en este navegador.</p>
  <div class="uprow">
    <div class="drop" id="dropT"><b>Arrastra o haz clic</b><br><small>Puedes subir varias órdenes, una por una</small><input type="file" id="fileT" accept=".xlsx,.xls,.csv" hidden></div>
    <div class="sec" style="margin:0"><h3 class="ok">Órdenes cargadas</h3><div id="tlist"></div></div>
  </div>
  <div id="tdetail"></div>
</div>

<div class="pane" id="mov">
  <h2>Movimiento — qué se vende y qué se acaba</h2>
  <p class="note">Variantes activas con ventas en 90 días: mucho / más o menos / poco, con su velocidad y días de stock restantes.</p>
  <div class="controls">
    <select id="mvsel"><option value="">Todos los proveedores</option></select>
    <input type="search" id="mq" placeholder="Buscar…">
    <select id="msel"><option value="">Todo</option><option value="agotado">Agotados</option><option value="critico">Críticos (&lt;14 días)</option><option value="bajo">Bajos (&lt;30 días)</option></select>
  </div>
  <p class="note" id="msum"></p>
  <div class="sec"><div class="tblwrap"><table id="mt"><thead><tr><th></th><th>Producto · variante</th><th>Proveedor</th><th class="num">Vendió 90d</th><th class="num">Vendió 60d</th><th class="num">Pzs/semana</th><th class="num">Stock</th><th class="num">Días de stock</th><th>Movimiento</th><th>Estado</th></tr></thead><tbody></tbody></table></div></div>
</div>

</div>
<div class="foot">Jewelry Remate MX · Centro de órdenes de compra · datos al __CORTE__ · Para actualizar: dile a Claude «actualiza órdenes».</div>
__XLSX_LIB__
<script src="exceljs.min.js"></script>
<script>
var DATA=__DATA__;
var IMGS=__IMGS__;
var VENDORS=__VENDORS__;
var TBASE=__TBASE__;
var WEEKS=10, TOP_U=10, TOP_MULT=1.2;
function usd(n){return n==null?'—':'$'+Number(n).toFixed(2)}
function normSku(s){s=String(s==null?'':s).trim();if(s.slice(-2)==='.0')s=s.slice(0,-2);return s}
function normT(s){return String(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/\s+/g,' ').trim().toUpperCase()}
function img(i){return i>=0?'<img class="th" loading="lazy" src="'+IMGS[i]+'">':'<div class="th"></div>'}

// ---- en camino ----
var TKEY='oc_transit_v1',RKEY='oc_transit_rm_v1';
function tload(){try{return JSON.parse(localStorage.getItem(TKEY))||[]}catch(e){return []}}
function tsave(o){localStorage.setItem(TKEY,JSON.stringify(o))}
function trm(){try{return JSON.parse(localStorage.getItem(RKEY))||[]}catch(e){return []}}
function trmsave(o){localStorage.setItem(RKEY,JSON.stringify(o))}
function allT(){var rm=trm();return TBASE.filter(function(o){return rm.indexOf(o.name)<0}).concat(tload())}
function transitMap(){var m={},a={};allT().forEach(function(o){o.lines.forEach(function(l){var k=l.sku||normT(l.title)+'|'+normT(l.variant);if(!l.arrived){m[k]=(m[k]||0)+(l.qty||0);a[k]=1}})});m.__any=a;return m}
function inTransit(r,tm){return tm[r.k]||tm[normT(r.t)+'|'+normT(r.vt)]||0}
function inTAny(r,tm){return tm.__any[r.k]||tm.__any[normT(r.t)+'|'+normT(r.vt)]||0}

// ---- clasificacion ----
function isEst(r){return r.st===''&&r.u9===0&&r.a>=90&&r.q>0}
function isLento(r){return r.st===''&&r.q>0&&!isEst(r)&&((r.u>0&&r.dsl>=40)||(r.u===0&&r.u9>0))}
function isReb(r){return r.st===''&&(r.rb>0||r.ra===1)}
// OUTLET: la marca vive en el nombre de la variante. No se piden ni se editan (Eduardo, 18 ago 2026).
// La marca OUTLET aparece en la variante Y a veces pegada al final del SKU (13096811034113OUTLET).
function isOutlet(r){return /OUTLET/i.test(r.vt||'')||/OUTLET/i.test(r.k||'')||/OUTLET/i.test(r.t||'')}
// Orden alfabetico: primero por nombre de producto, la variante solo desempata (Eduardo, 18 ago 2026).
function byName(a,b){var n=(a.t||'').localeCompare(b.t||'','es',{numeric:true,sensitivity:'base'});
 return n||(a.vt||'').localeCompare(b.vt||'','es',{numeric:true,sensitivity:'base'})}
function movLabel(r){var d=Math.min(r.a,90);if(d<=0)d=1;var vel=r.u9/d*7;
 if(r.u9===0)return r.a<30?['nuevo','Nuevo ('+r.a+'d)']:['gris','Nada'];
 if(vel>=2)return ['top','Mucho'];if(vel>=0.7)return ['ok','Más o menos'];return ['bajo','Poco']}
function sug(r,tm){
  var t=inTransit(r,tm);
  if(r.u>0){var vel=r.u/60*7,need=vel*WEEKS;if(r.u>TOP_U)need*=TOP_MULT;
    var s=Math.ceil(need-r.q-t);if(s<=0)return 0;return Math.ceil(s/2)*2}
  if(r.q<=0&&t<=0)return 2;
  return 0;
}
function cobertura(r){if(r.u9<=0)return r.q>0?9999:0;return Math.round(r.q/(r.u9/Math.min(r.a,90)))}
function urg(r){if(r.q<=0)return 'agotado';var c=cobertura(r);if(c<14)return 'critico';if(c<30)return 'bajo';return 'ok'}
var CH={agotado:'Agotado',critico:'Crítico',bajo:'Bajo',ok:'OK'};
function piezasHTML(r){
  if(r.rb===0&&r.cd===0)return '';
  var p=[];if(r.rb>0)p.push('<span class="r">🏷️'+r.rb+' rebaja</span>');
  if(r.pn>0)p.push('<span class="n">💵'+r.pn+' normal</span>');
  if(r.cd>0)p.push('<span class="c">🎟️'+r.cd+' por código (no rebaja)</span>');
  return '<span class="pill vsub">'+p.join(' · ')+'</span>';
}

// ---- tabs ----
var tabs=document.querySelectorAll('.tab');
tabs.forEach(function(t){t.onclick=function(){tabs.forEach(function(x){x.setAttribute('aria-selected','false')});t.setAttribute('aria-selected','true');
document.querySelectorAll('.pane').forEach(function(p){p.classList.remove('on')});document.getElementById(t.dataset.p).classList.add('on');window.scrollTo(0,0)}});

// ---- semaforo ----
function vendRows(v){return DATA.filter(function(r){return r.v===v})}
function renderSem(){
  var tm=transitMap();var totalPz=0,totalUS=0,html='';
  var cards=VENDORS.map(function(v){
    var rs=vendRows(v).filter(function(r){return r.st===''});
    var urgN=rs.filter(function(r){return r.q<=0&&r.u>0&&inTransit(r,tm)<=0&&!isReb(r)}).length;
    var crit=rs.filter(function(r){return r.u9>0&&r.q>0&&cobertura(r)<14}).length;
    var rebN=rs.filter(function(r){return isReb(r)}).length;
    var pz=0,us=0,ln=0;
    rs.forEach(function(r){if(isReb(r)||isEst(r))return;var s=sug(r,tm);if(s>0){pz+=s;ln++;if(r.c)us+=s*r.c}});
    totalPz+=pz;totalUS+=us;
    var cls=urgN>=5?'rojo':(urgN>0||crit>=5?'amarillo':'verde');
    return {v:v,cls:cls,lab:cls==='rojo'?'🔴 PEDIR YA':(cls==='amarillo'?'🟡 PRONTO':'🟢 OK'),urgN:urgN,crit:crit,rebN:rebN,pz:pz,us:us,ln:ln};
  }).sort(function(a,b){return b.urgN-a.urgN||b.crit-a.crit});
  cards.forEach(function(c){
    html+='<div class="card '+c.cls+'" onclick="goOrden(\''+c.v+'\')"><h3>'+c.v+'</h3><div class="sem">'+c.lab+'</div><ul>'+
    '<li><b>'+c.urgN+'</b> agotadas que sí venden (sin pedir)</li>'+
    '<li><b>'+c.crit+'</b> críticas (&lt;14 días de stock)</li>'+
    '<li><b>'+c.rebN+'</b> en rebaja 30%+ (tu criterio)</li>'+
    '<li>Sugerido: <b>'+c.pz+'</b> pzs / <b>'+c.ln+'</b> líneas ≈ <b>'+usd(c.us)+' USD</b></li></ul></div>';
  });
  document.getElementById('semcards').innerHTML=html;
  var act=DATA.filter(function(r){return r.st===''});
  document.getElementById('kpis').innerHTML=
   '<div class="kpi"><div class="l">Variantes activas</div><div class="v">'+act.length.toLocaleString()+'</div></div>'+
   '<div class="kpi"><div class="l">Con ventas 60d</div><div class="v">'+act.filter(function(r){return r.u>0}).length.toLocaleString()+'</div></div>'+
   '<div class="kpi"><div class="l">Pzs sugeridas</div><div class="v">'+totalPz.toLocaleString()+'</div></div>'+
   '<div class="kpi"><div class="l">Costo estimado</div><div class="v">'+usd(totalUS)+' <span style="font-size:12px">USD</span></div></div>';
}
function goOrden(v){document.querySelector('.tab[data-p="orden"]').click();document.getElementById('vsel').value=v;renderOrden()}

// ---- orden ----
var vsel=document.getElementById('vsel');
VENDORS.forEach(function(v){var o=document.createElement('option');o.value=o.textContent=v;vsel.appendChild(o)});
var EKEY='oc_edits_v1',ETKEY='oc_edits_ts';
var edits={};try{edits=JSON.parse(localStorage.getItem(EKEY))||{}}catch(e){}
function esave(){localStorage.setItem(EKEY,JSON.stringify(edits));localStorage.setItem(ETKEY,new Date().toLocaleString('es-MX',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}))}
function draftbar(){var n=Object.keys(edits).length;var el=document.getElementById('draft');
 if(!n){el.innerHTML='';return}
 el.innerHTML='💾 <b>Borrador guardado automáticamente</b> — '+n+' cantidad'+(n>1?'es':'')+' editada'+(n>1?'s':'')+' por ti · última edición: '+(localStorage.getItem(ETKEY)||'')+' · tus cambios se conservan aunque cierres la página o se actualicen los datos.';}
function rowHTML(r,tm,noSug){
  var out=isOutlet(r);
  var s=out?0:(edits[r.k]!=null?edits[r.k]:(noSug?0:sug(r,tm)));
  var t=inTransit(r,tm);
  var chips='';var u=urg(r);
  if(out)chips+=' <span class="chip gris" style="color:var(--a);background:var(--a-bg)">🚫 OUTLET — no se pide</span>';
  if(r.st===''&&r.u>0&&(u==='agotado'||u==='critico'))chips+=' <span class="chip '+u+'">'+CH[u]+'</span>';
  if(r.u>TOP_U)chips+=' <span class="chip top">TOP +20%</span>';
  if(r.ra)chips+=' <span class="chip reb">Rebaja activa hoy −'+Math.round((1-r.p/r.cap)*100)+'%</span>';
  if(r.dup)chips+=' <span class="chip dup">Duplicado</span>';
  if(r.st==='D')chips+=' <span class="chip gris">Borrador</span>';
  if(r.st==='A')chips+=' <span class="chip gris">Archivado</span>';
  if(r.st!==''&&r.u>0)chips+=' <span class="chip warn" style="color:var(--warn);background:var(--warn-bg)">vendió '+r.u+' pzs estando activo</span>';
  if(isEst(r))chips+=' <span class="chip gris">Estancado real: 90+ días de alta y 0 ventas en 90d</span>';
  if(isLento(r))chips+=' <span class="chip bajo">🐢 Lento — '+(r.dsl>=90?'90+':r.dsl)+' días sin venta</span>';
  if(r.a<90&&r.a>=0&&r.st==='')chips+=' <span class="chip nuevo">'+r.a+' días activo</span>';
  var obs=[];
  if(r.u===0&&r.q<=0&&r.st==='')obs.push('agotado sin venta reciente — prueba');
  if(r.ns)obs.push('SIN SKU en Shopify — conviene ponérselo');
  if(r.dup)obs.push('nombre duplicado, revisar cuál pedir');
  if(r.c==null)obs.push('SIN COSTO en historial');
  return '<tr'+(noSug?' class="gris"':'')+' data-k="'+r.k+'">'+
   '<td>'+img(r.i)+'</td>'+
   '<td><span class="pname">'+r.t+'</span><span class="vsub">'+(r.vt||'')+' · SKU '+(r.ns?'—':r.k)+(r.m?' · '+r.m:'')+'</span></td>'+
   '<td class="num">'+r.u+piezasHTML(r)+'</td><td class="num">'+(r.u/60*7).toFixed(1)+'</td>'+
   '<td class="num">'+r.q+'</td><td class="num">'+(t||'—')+'</td>'+
   '<td class="num"><input class="q'+(s>0?' hot':'')+(!out&&edits[r.k]!=null?' edited':'')+'" type="number" min="0" step="1" value="'+s+'"'+(out?' disabled title="Los OUTLET no se piden"':'')+'></td>'+
   '<td class="num">'+usd(r.c)+'</td><td class="num" data-tot>'+(r.c?usd(s*r.c):'—')+'</td>'+
   '<td>'+chips+(obs.length?'<span class="vsub">'+obs.join(' · ')+'</span>':'')+'</td></tr>';
}
var THEAD='<thead><tr><th></th><th>Producto · variante</th><th class="num">Vendió 60d (pzas)</th><th class="num">Pzs/semana</th><th class="num">Stock</th><th class="num">En camino</th><th class="num">PEDIR</th><th class="num">Costo (US)</th><th class="num">Total (US)</th><th>Notas</th></tr></thead>';
function renderOrden(){
  var v=vsel.value,tm=transitMap(),q=normT(document.getElementById('oq').value);
  var rs=vendRows(v).filter(function(r){return !q||normT(r.t).indexOf(q)>=0||r.k.indexOf(q)>=0});
  var act=rs.filter(function(r){return r.st===''});
  // SECCIONES EXCLUYENTES (Eduardo, 18 ago 2026): un SKU vive en UNA sola seccion.
  // Si vendio (60d o 90d) va en PEDIR; si nunca vendio va en PRUEBA; si trae rebaja va
  // SOLO en REBAJA. Antes, los que vendieron en 90d pero no en 60d salian en PEDIR y en
  // PRUEBA a la vez: se contaban doble en el total y salian dos veces en el Excel.
  // PEDIR = SOLO lo que vendio en los ultimos 60 dias (Eduardo, 18 ago 2026: "no me pongas
  // productos sin venta en el area de se venden"). Lo que vendio hace mas de 60 dias se va
  // a AGOTADOS si esta en cero, o a LENTOS si todavia tiene stock.
  var pedir=act.filter(function(r){return r.u>0&&!isReb(r)&&!isEst(r)}).sort(byName);
  var prueba=act.filter(function(r){return r.u===0&&r.q<=0&&!isReb(r)&&sug(r,tm)>0}).sort(byName);
  var lentos=act.filter(function(r){return r.u===0&&r.u9>0&&r.q>0&&!isReb(r)&&!isEst(r)}).sort(byName);
  var rebL=act.filter(function(r){return isReb(r)}).sort(byName);
  var est=act.filter(function(r){return isEst(r)&&!isReb(r)}).sort(byName);
  var drafts=rs.filter(function(r){return r.st!==''}).sort(byName);
  function tbl(list,g){return '<div class="tblwrap"><table>'+THEAD+'<tbody>'+list.map(function(r){return rowHTML(r,tm,g)}).join('')+'</tbody></table></div>'}
  var H='';
  H+='<div class="sec"><h3 class="ok">✅ PEDIR — se venden y hay que resurtir ('+pedir.length+')</h3>'+(pedir.length?tbl(pedir,false):'<div class="exp" style="padding-bottom:12px">Nada pendiente.</div>')+'</div>';
  H+='<div class="sec"><h3 class="warn">🧪 AGOTADOS SIN VENTA RECIENTE — 2 pzs de prueba ('+prueba.length+')</h3><div class="exp">Activos, en cero y sin venta en 60 días. Ordenados por movimiento 90d y por lo más nuevo.</div>'+(prueba.length?tbl(prueba,false):'<div class="exp" style="padding-bottom:12px">Ninguno.</div>')+'</div>';
  H+='<div class="sec"><h3 class="bajo">🐢 LENTOS CON STOCK — vendieron hace más de 60 días ('+lentos.length+')</h3><div class="exp">Sin ventas en los últimos 60 días pero con historial en 90 y con existencia. No traen cantidad sugerida: ya tienes producto. Si quieres resurtir alguno, la cantidad la pones tú.</div>'+(lentos.length?tbl(lentos,true):'<div class="exp" style="padding-bottom:12px">Ninguno.</div>')+'</div>';
  H+='<div class="sec"><h3 class="reb">🏷️ REBAJA 30%+ (precio de comparación) — tu criterio ('+rebL.length+')</h3><div class="exp">Pieza por pieza en 60 días: 🏷️ vendidas con rebaja · 💵 a precio normal · 🎟️ por código de descuento (NO cuenta como rebaja). También los que están rebajados 30%+ ahorita. Sin cantidad sugerida.</div>'+(rebL.length?tbl(rebL,true):'<div class="exp" style="padding-bottom:12px">Ninguno.</div>')+'</div>';
  H+='<div class="sec"><h3 class="gray">📝 EN BORRADOR / ARCHIVADOS de este proveedor ('+drafts.length+')</h3><div class="exp">No se piden por default (tu criterio del porqué están en borrador). Si uno vendió estando activo, viene marcado.</div>'+(drafts.length?tbl(drafts,true):'<div class="exp" style="padding-bottom:12px">Ninguno.</div>')+'</div>';
  H+='<div class="sec"><h3 class="gray">⚖️ ESTANCADOS REALES — 0 ventas en 90 días, con stock ('+est.length+')</h3><div class="exp">Solo productos con <b>90+ días desde su alta</b> y <b>0 ventas en 90 días</b>. Los dados de alta hace poco NO aparecen aquí — son nuevos, no estancados. Los 🐢 lentos (40+ días sin venta) sí se pueden pedir y van marcados en su sección.</div>'+(est.length?tbl(est,true):'<div class="exp" style="padding-bottom:12px">Ninguno.</div>')+'</div>';
  document.getElementById('ocont').innerHTML=H;
  document.querySelectorAll('#ocont input.q').forEach(function(inp){
    inp.oninput=function(){var tr=inp.closest('tr');var k=tr.dataset.k;var val=parseInt(inp.value)||0;edits[k]=val;esave();
      var r=DATA.find(function(x){return x.k===k});inp.classList.toggle('hot',val>0);inp.classList.add('edited');
      tr.querySelector('[data-tot]').textContent=r&&r.c?usd(val*r.c):'—';sum();draftbar()};
  });
  sum();
  function sum(){
    var pz=0,us=0,ln=0,vistos={};
    document.querySelectorAll('#ocont tr[data-k]').forEach(function(tr){
      var k=tr.dataset.k;
      if(vistos[k])return;            // mismo SKU repetido en el catalogo: se cuenta UNA vez
      var val=parseInt(tr.querySelector('input.q').value)||0;
      if(val>0){vistos[k]=1;pz+=val;ln++;var r=DATA.find(function(x){return x.k===k});if(r&&r.c)us+=val*r.c}});
    document.getElementById('osum').innerHTML='Orden <b>'+v+'</b>: <b>'+ln+'</b> líneas · <b>'+pz+'</b> piezas · costo estimado <b>'+usd(us)+' USD</b> (mejor precio histórico).';
  }
}
vsel.onchange=renderOrden;
document.getElementById('oq').oninput=renderOrden;
document.getElementById('reset').onclick=function(){
 var n=Object.keys(edits).length;
 if(n&&!confirm('Vas a borrar tu borrador ('+n+' cantidades editadas) y volver a las sugeridas. ¿Seguro?'))return;
 edits={};localStorage.removeItem(EKEY);localStorage.removeItem(ETKEY);renderOrden();draftbar()};

// ---- export EXCEL con fotos incrustadas ----
document.getElementById('xlsx').onclick=async function(){
  var btn=this;btn.disabled=true;btn.textContent='Generando Excel…';
  try{
    var v=vsel.value;var items=[];var vistos={};
    document.querySelectorAll('#ocont tr[data-k]').forEach(function(tr){
      var k=tr.dataset.k;
      if(vistos[k])return;            // un SKU sale UNA sola vez en el Excel, nunca duplicado
      var val=parseInt(tr.querySelector('input.q').value)||0;if(val<=0)return;
      var r=DATA.find(function(x){return x.k===k});if(!r)return;
      vistos[k]=1;
      var obs=[];if(r.dup)obs.push('DUPLICADO');if(r.rb>0)obs.push(r.rb+' pzs con rebaja 30%+');if(r.ra)obs.push('rebaja activa hoy');
      if(r.cd>0)obs.push(r.cd+' pzs por código (no rebaja)');if(isEst(r))obs.push('estancado');if(r.st!=='')obs.push(r.st==='D'?'BORRADOR':'ARCHIVADO');
      if(r.u===0&&r.q<=0&&r.st==='')obs.push('prueba');
      items.push({r:r,val:val,obs:obs.join(' / ')});
    });
    if(!items.length){alert('No hay líneas con PEDIR > 0.');return}
    var wb=new ExcelJS.Workbook();var ws=wb.addWorksheet('ORDEN '+v);
    ws.columns=[{header:'#',width:5},{header:'FOTO',width:19},{header:'PRODUCTO',width:44},{header:'VARIANTE',width:20},
      {header:'SKU',width:18},{header:'PEDIR',width:8},{header:'COSTO UNIT (US)',width:14},{header:'TOTAL (US)',width:12},
      {header:'MATERIAL',width:18},{header:'OBSERVACIONES',width:30}];
    ws.getRow(1).font={bold:true};ws.getRow(1).alignment={horizontal:'center'};
    for(var i=0;i<items.length;i++){
      var it=items[i],r=it.r,rowN=i+2;
      var row=ws.addRow([i+1,'',r.t,r.vt||'',r.ns?'':r.k,it.val,r.c!=null?r.c:'',r.c!=null?+(it.val*r.c).toFixed(2):'',r.m||'',it.obs]);
      row.height=44;row.alignment={vertical:'middle',wrapText:true};
      row.getCell(7).numFmt='$#,##0.00';row.getCell(8).numFmt='$#,##0.00';
    }
    // fotos
    // FOTOS EN HD Y RECORTADAS AL PRODUCTO (Eduardo, 18 ago 2026).
    // La pagina usa miniaturas de 120x120 para ir ligera; el CDN de Shopify sirve el mismo
    // archivo en grande cambiando el sufijo del nombre, asi que para el Excel se pide 1024.
    function hdURL(u){return u.replace(/_\d+x\d+(?=\.[a-z]+)/i,'_1024x1024')}
    // Quita el fondo blanco sobrante para que el producto llene el cuadro.
    async function recorta(blob){
      var bmp=await createImageBitmap(blob);
      var W=bmp.width,H=bmp.height;
      var c=document.createElement('canvas');c.width=W;c.height=H;
      var g=c.getContext('2d',{willReadFrequently:true});g.drawImage(bmp,0,0);
      var d;try{d=g.getImageData(0,0,W,H).data}catch(e){return blob}
      function px(i,j){var o=(j*W+i)*4;return [d[o],d[o+1],d[o+2]]}
      var esq=[px(0,0),px(W-1,0),px(0,H-1),px(W-1,H-1)];
      var bg=[0,1,2].map(function(k){return (esq[0][k]+esq[1][k]+esq[2][k]+esq[3][k])/4});
      var TOL=28,minX=W,minY=H,maxX=-1,maxY=-1;
      for(var j=0;j<H;j++){for(var i=0;i<W;i++){
        var o=(j*W+i)*4;
        if(d[o+3]<16)continue;
        if(Math.abs(d[o]-bg[0])+Math.abs(d[o+1]-bg[1])+Math.abs(d[o+2]-bg[2])>TOL){
          if(i<minX)minX=i; if(i>maxX)maxX=i; if(j<minY)minY=j; if(j>maxY)maxY=j;}
      }}
      // si no encontro producto, o ya venia ajustada, se deja igual
      if(maxX<0||(maxX-minX)<W*0.04||(maxY-minY)<H*0.04)return {blob:blob,w:W,h:H};
      var pad=Math.round(Math.max(maxX-minX,maxY-minY)*0.04);
      minX=Math.max(0,minX-pad); minY=Math.max(0,minY-pad);
      maxX=Math.min(W-1,maxX+pad); maxY=Math.min(H-1,maxY+pad);
      // Se respeta la forma real del producto: nada de cuadrar con blanco, porque un anillo
      // ancho y bajito quedaba diminuto en medio de una celda enorme.
      var cw=maxX-minX+1, ch=maxY-minY+1;
      var esc=Math.min(1,560/Math.max(cw,ch));   // nitido sin inflar el archivo
      var ow=Math.max(1,Math.round(cw*esc)), oh=Math.max(1,Math.round(ch*esc));
      var o2=document.createElement('canvas');o2.width=ow;o2.height=oh;
      var g2=o2.getContext('2d');
      g2.imageSmoothingQuality='high';
      g2.fillStyle='#ffffff';g2.fillRect(0,0,ow,oh);
      g2.drawImage(bmp,minX,minY,cw,ch,0,0,ow,oh);
      var b2=await new Promise(function(res){o2.toBlob(function(b){res(b)},'image/jpeg',0.92)});
      return {blob:b2||blob,w:ow,h:oh};
    }
    var imgResults=await Promise.all(items.map(async function(it){
      if(it.r.i<0)return null;
      try{
        var url=IMGS[it.r.i];
        var resp=await fetch(hdURL(url));
        if(!resp.ok)resp=await fetch(url);       // si no existe el grande, la miniatura
        if(!resp.ok)return null;
        var blob=await resp.blob();
        var r={blob:blob,w:0,h:0};
        try{r=await recorta(blob)}catch(e){var bm=await createImageBitmap(blob);r={blob:blob,w:bm.width,h:bm.height}}
        var buf=await r.blob.arrayBuffer();
        var ext=(r.blob.type||'').indexOf('png')>=0?'png':'jpeg';
        return {buf:buf,ext:ext,w:r.w,h:r.h};
      }catch(e){return null}
    }));
    // Cada fila se ajusta a la altura de SU foto, con un margencito blanco (Eduardo, 18 ago 2026:
    // "que esté un poquito más alta que la imagen del producto, pero no mucho").
    var FOTO_COL_PX=138, FOTO_CAJA=120, MARGEN=16;   // 16 px = 8 arriba y 8 abajo
    imgResults.forEach(function(im,i){
      if(!im)return;
      var id=wb.addImage({buffer:im.buf,extension:im.ext});
      // La foto conserva su proporcion, se ajusta a la caja y se centra en la celda.
      var esc=Math.min(FOTO_CAJA/(im.w||FOTO_CAJA),FOTO_CAJA/(im.h||FOTO_CAJA));
      var aw=Math.round((im.w||FOTO_CAJA)*esc), ah=Math.round((im.h||FOTO_CAJA)*esc);
      var filaPx=ah+MARGEN;
      ws.getRow(i+2).height=Math.max(34,Math.round(filaPx*0.75));   // px -> puntos
      ws.addImage(id,{tl:{col:1+Math.max(0,(FOTO_COL_PX-aw)/2)/FOTO_COL_PX,
                          row:i+1+(MARGEN/2)/filaPx},
                      ext:{width:aw,height:ah},editAs:'oneCell'});
    });
    var out=await wb.xlsx.writeBuffer();
    var blob=new Blob([out],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
    var a=document.createElement('a');a.href=URL.createObjectURL(blob);
    a.download='ORDEN_'+v.replace(/\s+/g,'')+'_'+'__FECHA__'+'.xlsx';a.click();
  }catch(err){alert('Error generando el Excel: '+err)}
  finally{btn.disabled=false;btn.textContent='⬇ Descargar orden (Excel)'}
};

// ---- en camino: carga de excels ----
function isGreen(rgb){if(!rgb)return false;var h=String(rgb);if(h.length>6)h=h.slice(h.length-6);var R=parseInt(h.slice(0,2),16),G=parseInt(h.slice(2,4),16),B=parseInt(h.slice(4,6),16);if(isNaN(R)||isNaN(G)||isNaN(B))return false;return G>R+15&&G>B+15&&G>80}
function greenRow(ws,i){
 // "Ya llego" SOLO si TODA la fila esta en verde: cada celda con contenido debe tener
 // relleno verde. Una sola celda verde NO cuenta (los colores agrupan guias de envio).
 if(!ws||i==null)return false;
 var greens=0,badVals=0;
 for(var c=0;c<25;c++){
   var cell=ws[XLSX.utils.encode_cell({r:i,c:c})];
   if(!cell)continue;
   var g=cell.s&&cell.s.fgColor&&isGreen(cell.s.fgColor.rgb);
   var hasVal=cell.v!==undefined&&String(cell.v).trim()!=='';
   if(g)greens++;else if(hasVal)badVals++;
 }
 return greens>=3&&badVals===0;
}
function findCols(aoa){for(var i=0;i<Math.min(aoa.length,25);i++){var row=aoa[i].map(function(c){return String(c).toUpperCase()});
 var hasSku=row.some(function(c){return c.indexOf('SKU')>=0});var hasProd=row.some(function(c){return c.indexOf('PRODUCTO')>=0})||row.some(function(c){return c.indexOf('PEDIR')>=0});
 if(hasSku&&hasProd){var col=function(name){for(var j=0;j<row.length;j++){if(row[j].indexOf(name)>=0)return j}return -1};
 return {hdr:i,prod:col('PRODUCTO'),vari:col('VARIANTE'),sku:col('SKU'),qty:col('PEDIR')>=0?col('PEDIR'):col('CANT')}}}return null}
var dT=document.getElementById('dropT'),fT=document.getElementById('fileT');
dT.onclick=function(){fT.click()};fT.onchange=function(){if(fT.files[0])onT(fT.files[0]);fT.value=''};
['dragover','dragenter'].forEach(function(ev){dT.addEventListener(ev,function(e){e.preventDefault();dT.classList.add('hot')})});
['dragleave','drop'].forEach(function(ev){dT.addEventListener(ev,function(e){e.preventDefault();dT.classList.remove('hot')})});
dT.addEventListener('drop',function(e){if(e.dataTransfer.files[0])onT(e.dataTransfer.files[0])});
function onT(file){var rd=new FileReader();rd.onload=function(e){try{
  var wb=XLSX.read(e.target.result,{type:'array',cellStyles:true});var best=null,bestws=null,bestn=-1;
  wb.SheetNames.forEach(function(n){var ws=wb.Sheets[n];var aoa=XLSX.utils.sheet_to_json(ws,{header:1,defval:''});var c=findCols(aoa);if(!c)return;
   var cnt=0;for(var i=c.hdr+1;i<aoa.length;i++){var p=c.prod>=0?aoa[i][c.prod]:'';if(p&&String(p).trim())cnt++}
   if(cnt>bestn){bestn=cnt;best=aoa;bestws=ws}});
  if(!best){alert('No encontré columnas PRODUCTO/SKU en ese Excel.');return}
  var c=findCols(best);var lines=[];
  for(var i=c.hdr+1;i<best.length;i++){var r=best[i];var prod=c.prod>=0?r[c.prod]:'';if(!prod||!String(prod).trim())continue;
   lines.push({title:String(prod).trim(),variant:c.vari>=0?String(r[c.vari]||'').trim():'',sku:normSku(c.sku>=0?r[c.sku]:''),
    qty:c.qty>=0?(parseFloat(r[c.qty])||0):0,arrived:greenRow(bestws,i)})}
  var os=tload();os.push({name:file.name,date:new Date().toISOString().slice(0,10),lines:lines});tsave(os);
  renderT();renderSem();renderOrden();
 }catch(err){alert('No pude leer el archivo: '+err)}};
 rd.readAsArrayBuffer(file)}
function tipoLinea(l){
  if(!l.sku)return ['nuevo','🆕 Nuevo — sin SKU en Shopify'];
  var r=null;for(var i=0;i<DATA.length;i++){if(DATA[i].k===l.sku){r=DATA[i];break}}
  if(!r)return ['nuevo','🆕 Nuevo — no está en Shopify'];
  if(r.a<90)return ['nuevo','🆕 Nuevo 2026 ('+r.a+' días de alta)'];
  return ['restock','🔄 Restock'];
}
function renderT(){
  var os=allT();var h='',det='';
  if(!os.length)h='<div class="transitem" style="color:var(--muted)">Ninguna todavía.</div>';
  os.forEach(function(o,ix){
   var ped=0,lleg=0,pzR=0,pzN=0,lnR=0,lnN=0;
   o.lines.forEach(function(l){ped+=l.qty||0;if(l.arrived)lleg+=l.qty||0;
     var t=tipoLinea(l);if(t[0]==='restock'){pzR+=l.qty||0;lnR++}else{pzN+=l.qty||0;lnN++}});
   var com=ped-lleg;
   h+='<div class="transitem"><span><b>'+o.name+'</b>'+(o.base?' <span class="chip bajo">de tus tablas</span>':'')+' · '+o.date+
     '<span class="vsub"><b>'+ped+'</b> pzs pedidas · 🚚 <b>'+com+'</b> en camino · 🟢 <b>'+lleg+'</b> llegadas · 🔄 '+lnR+' líneas restock ('+pzR+' pzs) · 🆕 '+lnN+' nuevas ('+pzN+' pzs)</span></span><button onclick="delT('+ix+')">✕ quitar</button></div>';
   det+='<div class="sec"><h3 class="ok">🚚 '+o.name+' — '+ped+' pzs pedidas · '+com+' en camino · '+lleg+' llegadas</h3><div class="tblwrap"><table><thead><tr><th>Estado</th><th>Tipo</th><th class="num">Cant pedida</th><th>Producto · variante</th><th>SKU</th></tr></thead><tbody>'+
    o.lines.map(function(l){var t=tipoLinea(l);
     return '<tr'+(l.arrived?' style="background:var(--ok-bg)"':'')+'><td>'+(l.arrived?'🟢 Ya llegó':'🚚 En camino')+'</td><td><span class="chip '+(t[0]==='restock'?'ok':'nuevo')+'">'+t[1]+'</span></td><td class="num"><b>'+(l.qty||'—')+'</b></td><td>'+l.title+'<span class="vsub">'+(l.variant||'')+'</span></td><td>'+(l.sku||'—')+'</td></tr>'}).join('')+
    '</tbody></table></div></div>';
  });
  document.getElementById('tlist').innerHTML=h;document.getElementById('tdetail').innerHTML=det;
}
function delT(ix){var os=allT();var o=os[ix];
 if(o.base){var rm=trm();rm.push(o.name);trmsave(rm)}
 else{var us=tload();for(var i=0;i<us.length;i++){if(us[i].name===o.name&&us[i].date===o.date){us.splice(i,1);break}}tsave(us)}
 renderT();renderSem();renderOrden()}

// ---- movimiento ----
var mvsel=document.getElementById('mvsel');
Array.from(new Set(DATA.filter(function(r){return r.st===''}).map(function(r){return r.v}))).sort().forEach(function(v){var o=document.createElement('option');o.value=o.textContent=v;mvsel.appendChild(o)});
function renderMov(){
  var q=normT(document.getElementById('mq').value),fu=document.getElementById('msel').value,fv=mvsel.value;
  var rs=DATA.filter(function(r){return r.st===''&&r.u9>0&&(!fv||r.v===fv)&&(!fu||urg(r)===fu)&&(!q||normT(r.t).indexOf(q)>=0||r.k.indexOf(q)>=0)})
    .sort(function(a,b){return b.u9-a.u9});
  document.getElementById('msum').innerHTML='<b>'+rs.length+'</b> variantes · <b>'+rs.reduce(function(s,r){return s+r.u9},0)+'</b> pzs vendidas en 90 días';
  document.querySelector('#mt tbody').innerHTML=rs.slice(0,600).map(function(r){var u=urg(r);var c=cobertura(r);var ml=movLabel(r);
   return '<tr><td>'+img(r.i)+'</td><td><span class="pname">'+r.t+'</span><span class="vsub">'+(r.vt||'')+' · SKU '+(r.k||'—')+'</span>'+piezasHTML(r)+'</td><td>'+r.v+'</td><td class="num">'+r.u9+'</td><td class="num">'+r.u+'</td><td class="num">'+(r.u/60*7).toFixed(1)+'</td><td class="num">'+r.q+'</td><td class="num">'+(c===9999?'∞':c)+'</td><td><span class="chip '+ml[0]+'">'+ml[1]+'</span></td><td><span class="chip '+u+'">'+CH[u]+'</span></td></tr>'}).join('');
}
document.getElementById('mq').oninput=renderMov;document.getElementById('msel').onchange=renderMov;mvsel.onchange=renderMov;

renderSem();renderOrden();renderT();renderMov();draftbar();
</script></body></html>'''

HTML = HTML.replace('__CORTE__', CORTE).replace('__ACTUALIZADO__', ACTUALIZADO).replace('__XLSX_LIB__', XLSX_LIB).replace('__FECHA__', HOY.isoformat())
HTML = HTML.replace('__DATA__', DATA_JSON).replace('__IMGS__', IMGS_JSON).replace('__VENDORS__', VEND_JSON).replace('__TBASE__', TBASE_JSON)
open(REPO + '/ordenes.html', 'w', encoding='utf-8').write(HTML)
print('ordenes.html v2:', len(HTML), 'bytes | imgs:', len(imgs))
