#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analisis.json — margen y recuperacion real por proveedor y por orden de compra.

Se corre DESPUES de bajar los datos de Shopify y ANTES de build_precios.py.
Lee de SCRATCH:  ventas_2026.jsonl (detalle de pedidos del anio, del bulk)
                 devoluciones.json (ShopifyQL: returns y net por SKU)
                 vp_0*.json        (catalogo, para el proveedor de respaldo)
Lee del repo:    datos/precios/*.json, scripts/costs.json, scripts/transit_base.json

COMO SE ATRIBUYE UNA VENTA A UN PROVEEDOR  (Reyna, 5 oct 2026)
El campo 'vendor' de Shopify NO sirve: guarda un solo proveedor por producto, el
ultimo que alguien escribio. Cuando un SKU se le compra a dos proveedores (paso con
DONGAI, que entro sobre productos de HAIFENG y CYNTHIA) ese campo le acredita a uno
lo que pago el otro.

Se usa FIFO por lote: cada linea de cada ODC es un lote con proveedor y fecha de
llegada; las ventas consumen los lotes en el orden en que llegaron. Primero que
entra, primero que sale, igual que la bodega.

Cuando una venta no alcanza lote (stock anterior a enero, o un SKU que no esta en
ningun ODC) se baja en cascada:
  nivel 1  lote exacto                    -> cuenta en la ORDEN y en el PROVEEDOR
  nivel 2  mismo SKU en otro ODC          -> solo en el PROVEEDOR (no se sabe que orden)
  nivel 3  costo historico de costs.json  -> solo en el PROVEEDOR, costo estimado
  nivel 4  solo el vendor de Shopify      -> entra al ingreso, SIN costo
  nivel 5  ni costo ni proveedor          -> queda fuera y se reporta aparte
El nivel 2 NUNCA se le carga a una orden: inflaria ordenes que ni han llegado.
"""
import json, re, os, glob, datetime, collections

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = os.environ.get('OC_SCRATCH') or os.path.join(REPO, '.scratch')
DATOS = os.path.join(REPO, 'datos', 'precios')
HOY = (datetime.date.fromisoformat(os.environ['OC_HOY'])
       if os.environ.get('OC_HOY') else datetime.date.today())
DIAS_PARADO = 60   # sin una sola venta en 60 dias = parado de verdad
LAG = 30          # dias estimados entre la fecha del ODC y la entrada a bodega
TC = 20.0
FLETE_HIST = 1.10 # el costo historico viene sin flete ni aduana; se le pone 10%

ALIAS = {'CYNTHIA': 'CYNTHIA CAO', 'NANCY': 'NANCY VIP', 'M0LLY': 'MOLLY',
         'COCO MA': 'COCOMA', 'COCO ZHANG': 'COCOZHANG'}
def prov_norm(p):
    p = (p or '').strip().upper()
    return ALIAS.get(p, p)

PREFIJO = [('HAIFENG','HAIFENG'), ('ZOEY','ZOEY'), ('CYNTHIA','CYNTHIA CAO'),
           ('NANCY','NANCY VIP'), ('DINADU','DINA DU'), ('COCOMA','COCOMA'),
           ('MOLLY','MOLLY'), ('DONGAI','DONGAI')]
def prov_de_orden(k):
    for a, b in PREFIJO:
        if k.startswith(a):
            return b
    return None

def fecha_de_orden(k):
    m = re.search(r'(\d{2})(\d{2})(\d{2})$', k)
    if not m:
        return None
    try:
        return datetime.date(2000 + int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None

# ---- ventas reales del anio, linea por linea ----
fechas, ventas = {}, []
for ln in open(os.path.join(SCRATCH, 'ventas_2026.jsonl')):
    d = json.loads(ln)
    if 'createdAt' in d:
        fechas[d['id']] = d['createdAt'][:10]
    else:
        sk = (d.get('sku') or '').strip()
        if sk:
            p = ((d.get('discountedUnitPriceSet') or {}).get('shopMoney') or {}).get('amount')
            ventas.append({'sku': sk, 'q': d.get('quantity') or 0,
                           'p': float(p or 0), 'pid': d.get('__parentId')})
for v in ventas:
    v['f'] = fechas.get(v['pid'], '')
ventas = [v for v in ventas if v['f'] and v['q'] > 0]
ventas.sort(key=lambda v: v['f'])

# ---- devoluciones: factor por SKU para descontarlas ----
q_li, m_li = collections.Counter(), collections.Counter()
for v in ventas:
    q_li[v['sku']] += v['q']; m_li[v['sku']] += v['q'] * v['p']
fac_q, fac_m = {}, {}
for r in json.load(open(os.path.join(SCRATCH, 'devoluciones.json')))['rows']:
    sk = (r[0] or '').strip()
    if not sk:
        continue
    if q_li.get(sk): fac_q[sk] = max(0.0, min(1.0, float(r[5] or 0) / q_li[sk]))
    if m_li.get(sk): fac_m[sk] = max(0.0, min(1.0, float(r[4] or 0) / m_li[sk]))

# ---- lotes: cada linea de cada ODC ----
ordenes = {}
for k, v in json.load(open(os.path.join(DATOS, 'zoey_ordenes.json'))).items():
    ordenes[k] = dict(v, proveedor='ZOEY')
ordenes.update(json.load(open(os.path.join(DATOS, 'otros_ordenes.json'))))
inf = json.load(open(os.path.join(DATOS, 'informe_2026.json')))
for k, o in ordenes.items():
    n = inf['sc'].get(k)
    if n is not None:
        o['sc'] = n

lotes = collections.defaultdict(list)
ult_compra = {}          # SKU -> (costo, llegada, orden, proveedor) de la ultima compra
meta = {}
for k, o in ordenes.items():
    f = fecha_de_orden(k)
    if not f:
        continue
    lleg = (f + datetime.timedelta(days=LAG)).isoformat()
    pct = o['shipping'] / o['costo'] if o['costo'] else 0
    I = []
    for l in o['lineas']:
        F = l['cu'] * l['cant']; G = F * pct
        I.append(F + G + (F + G) * 0.03)
    tot = sum(I) or 1
    meta[k] = {'prov': prov_de_orden(k) or (o.get('proveedor') or '?'),
               'fecha': f.isoformat(), 'lleg': lleg,
               'pzs': sum(l['cant'] for l in o['lineas'])}
    for l, Ii in zip(o['lineas'], I):
        if not l['sku'] or l['cant'] <= 0:
            continue
        M = (Ii * TC + o['sc'] * (Ii / tot)) / l['cant']
        lotes[l['sku']].append({'orden': k, 'prov': meta[k]['prov'], 'lleg': lleg,
                                'rest': l['cant'], 'q': l['cant'], 'M': M,
                                'prod': l['prod'], 'var': l['var'], 'pact': l.get('pact')})
        if l['sku'] not in ult_compra or lleg > ult_compra[l['sku']][1]:
            ult_compra[l['sku']] = (M, lleg, k, meta[k]['prov'])
for sk in lotes:
    lotes[sk].sort(key=lambda x: x['lleg'])

costs = json.load(open(os.path.join(REPO, 'scripts', 'costs.json')))['costs']
# El precio de venta de hoy se jala del catalogo, igual que en build_precios.py:
# las lineas del ODC no lo traen, lo pone Shopify.
vendor, precio = {}, {}
for fn in sorted(glob.glob(os.path.join(SCRATCH, 'vp_0*.json'))):
    for n in json.load(open(fn))['data']['productVariants']['nodes']:
        sk = (n.get('sku') or '').strip()
        if sk:
            vendor[sk] = n['product']['vendor']
            try:
                precio[sk] = float(n['price'] or 0)
            except (TypeError, ValueError):
                pass
_ov = os.path.join(DATOS, 'precios_override.json')
if os.path.isfile(_ov):
    for _k, _v in json.load(open(_ov)).items():
        precio[_k] = float(_v)

# Precios bajados de Shopify hoy mismo (bulkOperationRunQuery sobre productVariants
# { sku price }, 3,722 variantes). Van al final porque son el dato mas fresco: el
# catalogo vp_0*.json es del corte anterior y precios_override.json era el parche
# que se usaba cuando no se podian bajar. Reyna, 5 oct 2026.
_ph = os.path.join(DATOS, 'precios_shopify.json')
if os.path.isfile(_ph):
    for _k, _v in json.load(open(_ph)).items():
        precio[_k] = float(_v)
for _sk, L in lotes.items():
    for _lot in L:
        _lot['pact'] = precio.get(_sk) or None

# ---- FIFO + cascada ----
P = collections.defaultdict(lambda: {'q': 0.0, 'ing': 0.0, 'costo': 0.0,
                                     'q_sc': 0.0, 'ing_sc': 0.0})
O = collections.defaultdict(lambda: {'q': 0.0, 'ing': 0.0, 'costo': 0.0})
ult_venta = {}
niveles = collections.Counter()
perdido = {'q': 0.0, 'ing': 0.0}
for v in ventas:
    q = v['q'] * fac_q.get(v['sku'], 1.0)
    pu = v['p'] * fac_m.get(v['sku'], 1.0)
    if q <= 0:
        continue
    ult_venta[v['sku']] = max(ult_venta.get(v['sku'], ''), v['f'])
    pend = q
    for lot in lotes.get(v['sku'], []):
        if pend <= 0:
            break
        if lot['lleg'] > v['f']:
            continue
        t = min(pend, lot['rest'])
        if t <= 0:
            continue
        lot['rest'] -= t; pend -= t; niveles[1] += t
        for d in (P[lot['prov']], O[lot['orden']]):
            d['q'] += t; d['ing'] += t * pu; d['costo'] += t * lot['M']
    if pend <= 0:
        continue
    if v['sku'] in ult_compra:                                   # nivel 2
        M, _, _, pr = ult_compra[v['sku']]
        d = P[pr]; d['q'] += pend; d['ing'] += pend * pu; d['costo'] += pend * M
        niveles[2] += pend
    elif v['sku'] in costs and (costs[v['sku']].get('best') or costs[v['sku']].get('last')):
        c = costs[v['sku']]
        M = (c.get('best') or c.get('last')) * TC * FLETE_HIST
        d = P[prov_norm(c.get('prov'))]
        d['q'] += pend; d['ing'] += pend * pu; d['costo'] += pend * M
        niveles[3] += pend
    elif vendor.get(v['sku']):                                   # nivel 4
        d = P[prov_norm(vendor[v['sku']])]
        d['q_sc'] += pend; d['ing_sc'] += pend * pu
        niveles[4] += pend
    else:
        perdido['q'] += pend; perdido['ing'] += pend * pu; niveles[5] += pend

# ---- armado ----
EN_CAMINO = {x['base'] for x in json.load(open(os.path.join(REPO, 'scripts', 'transit_base.json')))}
def banda(x):
    return '<2' if x < 2 else ('2-3' if x < 3 else ('3-3.5' if x < 3.5 else '>3.5'))

prov_out = {}
peores = []
for pr in sorted(P):
    d = P[pr]
    ords, parado_q, parado_mxn, bajo3, bandas = [], 0.0, 0.0, [], collections.Counter()
    vistos = set()
    for k, m in sorted(meta.items(), key=lambda x: x[1]['fecha'], reverse=True):
        if m['prov'] != pr:
            continue
        inv = inf['inv'].get(k, {}).get('mxn', 0) + ordenes[k]['sc']
        dd = O[k]
        est, rq, rm = [], 0.0, 0.0
        for sk, L in lotes.items():
            for lot in L:
                if lot['orden'] != k:
                    continue
                x = (lot['pact'] / lot['M']) if (lot['pact'] and lot['M']) else None
                if x is not None and (lot['prod'], lot['var']) not in vistos:
                    vistos.add((lot['prod'], lot['var'])); bandas[banda(x)] += 1
                    if x < 3:
                        bajo3.append({'prod': lot['prod'], 'var': lot['var'], 'sku': sk,
                                      'x': round(x, 2), 'M': round(lot['M']), 'p': lot['pact'],
                                      'orden': k})
                    if x < 2:
                        peores.append({'prod': lot['prod'], 'var': lot['var'], 'sku': sk,
                                       'prov': pr, 'x': round(x, 2), 'M': round(lot['M']),
                                       'p': lot['pact']})
                if lot['rest'] > 0:
                    rq += lot['rest']; rm += lot['rest'] * lot['M']
                    _dl = (HOY - datetime.date.fromisoformat(lot['lleg'])).days
                    if _dl < 0:
                        continue          # todavia viene en camino: no esta parado
                    uv = ult_venta.get(sk)
                    # Dias sin venta del PRODUCTO, no dias desde que llego la caja.
                    # Antes 'nunca' se marcaba cuando la ultima venta era anterior a
                    # la llegada del lote, y por eso el BOLSO CC 22 SILVER salia como
                    # "nunca se ha vendido" aunque llevaba 10 piezas vendidas en el
                    # anio: el lote ZOEY100926 no habia llegado. Reyna, 5 oct 2026.
                    _dsv = (HOY - datetime.date.fromisoformat(uv)).days if uv else None
                    # Para el que nunca ha vendido, el tiempo sin vender son los dias
                    # que lleva en bodega: asi uno que llego hace 3 semanas no se
                    # cuenta como parado nomas por no haber vendido todavia.
                    _sv = _dsv if _dsv is not None else _dl
                    # El resto es fraccionario por el descuento de devoluciones.
                    # Si redondea a cero no queda pieza parada y no va en la lista.
                    _r = int(round(lot['rest']))
                    if _r < 1:
                        continue
                    est.append({'prod': lot['prod'], 'var': lot['var'], 'sku': sk,
                                'rest': _r, 'q': lot['q'], 'M': round(lot['M']),
                                'mxn': round(_r * lot['M']),
                                'nunca': uv is None, 'uv': uv or '',
                                'dsv': _dsv, 'sv': _sv, 'quieto': _sv >= DIAS_PARADO,
                                'dias': _dl})
        # Parado de verdad = ya llego Y el producto no se ha vendido en DIAS_PARADO
        # dias. Lo que queda de algo que se sigue vendiendo es inventario, no estorbo.
        for _e in est:
            if _e['quieto']:
                parado_q += _e['rest']; parado_mxn += _e['rest'] * _e['M']
        # En la lista solo va lo que esta parado de verdad. Lo que queda de un
        # producto que se sigue vendiendo es inventario, y meterlo aqui era lo
        # que hacia ver estancado al BOLSO CC 22 SILVER.
        est = [e for e in est if e['quieto']]
        est.sort(key=lambda e: (-e['sv'], -e['mxn']))
        ords.append({'orden': k, 'fecha': m['fecha'], 'inv': round(inv),
                     'ing': round(dd['ing']), 'q': round(dd['q']), 'pzs': m['pzs'],
                     'pct': round(100 * dd['ing'] / inv, 1) if inv else None,
                     'rest': round(rq), 'rest_mxn': round(rm),
                     'dias': (HOY - datetime.date.fromisoformat(m['lleg'])).days,
                     'camino': k in EN_CAMINO,
                     'nunca': sum(1 for e in est if e['nunca']),
                     'quietos': sum(1 for e in est if e['quieto']),
                     'quieto_mxn': round(sum(e['mxn'] for e in est if e['quieto'])),
                     'est': est, 'est_total': len(est)})
    mg = d['ing'] - d['costo']
    prov_out[pr] = {
        'q': round(d['q']), 'ing': round(d['ing']), 'costo': round(d['costo']),
        'margen': round(mg), 'pct': round(100 * mg / d['ing'], 1) if d['ing'] else 0,
        'mult': round(d['ing'] / d['costo'], 2) if d['costo'] else 0,
        'q_sc': round(d['q_sc']), 'ing_sc': round(d['ing_sc']),
        'inv': round(sum(o['inv'] for o in ords)),
        'parado_q': round(parado_q), 'parado_mxn': round(parado_mxn),
        'bandas': dict(bandas), 'bajo3': sorted(bajo3, key=lambda x: x['x']),
        'ordenes': ords}

peores.sort(key=lambda x: x['x'])
out = {'generado': HOY.isoformat(), 'lag': LAG,
       'niveles': {str(k): round(v) for k, v in sorted(niveles.items())},
       'perdido': {'q': round(perdido['q']), 'ing': round(perdido['ing'])},
       'peores': peores[:5], 'prov': prov_out}
json.dump(out, open(os.path.join(DATOS, 'analisis.json'), 'w'), ensure_ascii=False)
tq = sum(p['q'] for p in prov_out.values()); ti = sum(p['ing'] for p in prov_out.values())
tc = sum(p['costo'] for p in prov_out.values())
print('analisis.json: %d proveedores | %d pzs | ingreso $%s | margen %.0f%% | %.2fx'
      % (len(prov_out), tq, format(ti, ',.0f'), 100 * (ti - tc) / ti, ti / tc))
print('  niveles:', dict(out['niveles']), '| sin nada:', out['perdido'])
