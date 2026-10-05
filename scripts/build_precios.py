#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""precios.html — Tablas de precios por orden de compra (reglas de Eduardo, 20 ago 2026):

- Se replica TAL CUAL la tabla del Drive, columna por columna.
- Tipo de cambio FIJO 20. Comision de Alibaba FIJA 3%. SIN descuento (los costos se
  homogenizan: el descuento varia por orden y contaminaria el costo real).
- Formula, identica a la que Eduardo usa en Drive (verificada contra sus hojas):
      F = costo_unitario * cantidad
      G = F * (shipping_orden / costo_orden)
      H = (F + G) * 3%
      I = F + G + H
      J = I * 20
      K = I / suma(I)                      <- peso del SKU en la orden
      L = shop_and_cross_orden * K         <- aduana prorrateada POR VALOR
      M = (J + L) / cantidad               <- COSTO REAL POR PIEZA
      N/O/P = M*3, M*3.5, M*4              <- ROAS
- El PRECIO ACTUAL se jala de Shopify por SKU (no se teclea a mano).
- El Shop and Cross sale del INFORME DE INVERSION 2026, no de la tabla: el informe
  esta desglosado por guia con montos reales; la tabla traia numeros tecleados
  (se detectaron dos errores: ZOEY200416 con el valor copiado de ZOEY200126, y
  ZOEY080626 descuadrado por 1,602.63).
"""
import json, glob, os, datetime, html

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = os.environ.get('OC_SCRATCH') or os.path.join(REPO, '.scratch')
DATOS = os.environ.get('OC_PRECIOS') or os.path.join(REPO, 'datos', 'precios')

TC = 20.0          # tipo de cambio fijo
ALIBABA = 0.03     # comision fija
ROAS = (3, 3.5, 4)
# REDONDEO de precios de venta: Eduardo los cierra en ...99 (5,899 / 2,999 / 999).
# Se sube al siguiente ...99, nunca se baja.
def redondea99(x):
    import math
    return math.ceil((x - 99) / 100) * 100 + 99

HOY = (datetime.date.fromisoformat(os.environ['OC_HOY'])
       if os.environ.get('OC_HOY') else datetime.date.today())
_MESES_L = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
            'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

# ---- precio de venta actual, desde el catalogo de Shopify ----
precio_shopify, titulo_shopify = {}, {}
for f in sorted(glob.glob(SCRATCH + '/vp_0*.json')):
    for n in json.load(open(f))['data']['productVariants']['nodes']:
        sk = str(n.get('sku') or '').strip()
        if not sk:
            continue
        try:
            precio_shopify[sk] = float(n['price'] or 0)
        except (TypeError, ValueError):
            pass
        titulo_shopify[sk] = (n['product']['title'] or '').strip()

# Precios cambiados en Shopify DESPUES del ultimo corte del catalogo. Sin esto la
# pagina seguiria mostrando el precio viejo hasta la siguiente bajada de datos.
_ov = os.path.join(DATOS, 'precios_override.json')
if os.path.isfile(_ov):
    for _k, _v in json.load(open(_ov)).items():
        precio_shopify[_k] = float(_v)

# Precios bajados de Shopify hoy mismo (bulkOperationRunQuery sobre productVariants
# { sku price }, 3,722 variantes). Van al final porque son el dato mas fresco: el
# catalogo vp_0*.json es del corte anterior y precios_override.json era el parche
# que se usaba cuando no se podian bajar. Reyna, 5 oct 2026.
_ph = os.path.join(DATOS, 'precios_shopify.json')
if os.path.isfile(_ph):
    for _k, _v in json.load(open(_ph)).items():
        precio_shopify[_k] = float(_v)

import re as _re
ordenes = {}
for k, v in json.load(open(os.path.join(DATOS, 'zoey_ordenes.json'))).items():
    ordenes[k] = dict(v, proveedor='ZOEY')
ordenes.update(json.load(open(os.path.join(DATOS, 'otros_ordenes.json'))))

_inf = json.load(open(os.path.join(DATOS, 'informe_2026.json')))

# El Shop and Cross de cada orden se toma SIEMPRE del informe, que es lo que de verdad se ha
# pagado. Antes se guardaba a mano en el archivo de la orden y se quedaba atras: ZOEY260826 se
# quedo en 0 aunque ya se habia pagado la aduana (Eduardo, 10 sep 2026).
_sc_cambios = []
for _k, _o in ordenes.items():
    _n = _inf['sc'].get(_k)
    if _n is not None and abs(_n - _o.get('sc', 0.0)) >= 0.01:
        _sc_cambios.append((_k, _o.get('sc', 0.0), _n))
        _o['sc'] = _n
for _k, _a, _n in _sc_cambios:
    print('  Shop and Cross %-16s %10.2f -> %10.2f' % (_k, _a, _n))

def _norm(x):
    return _re.sub(r'[^A-Z0-9]', '', x.upper())
inversion = {}
for k, v in _inf['inv'].items():
    inversion[k] = {'total_usd': v['usd'], 'total_mxn': v['mxn'],
                    'pagos': v['pagos'], 'mes': v['mes']}

ORDEN_PROV = ['HAIFENG', 'ZOEY', 'CYNTHIA CAO', 'NANCY VIP', 'DINA DU', 'COCOMA', 'MOLLY']

# Aduana estimada (Eduardo, 10 sep 2026). La Shop and Cross se paga caja por caja conforme van
# llegando, asi que una orden a medio pagar muestra un costo por pieza mas barato de lo real y
# lleva a ponerle precio bajo. Mientras la orden siga EN CAMINO se usa este porcentaje sobre la
# compra en pesos; cuando ya llego, manda lo que de verdad se pago.
# Los porcentajes los fijo Eduardo a partir del historico: HAIFENG pesa poco (joyeria chica) y
# el resto se maneja parejo al 4%.
PCT_ADUANA = {'HAIFENG': 0.03, 'ZOEY': 0.04, 'CYNTHIA CAO': 0.04,
              'NANCY VIP': 0.04, 'DINA DU': 0.04, 'COCOMA': 0.04, 'MOLLY': 0.04}
PCT_ADUANA_DEF = 0.04

# Nunca se usa el estimado por debajo de lo ya pagado: si una orden lleva pagado mas, manda lo real.
_tb = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transit_base.json')
EN_CAMINO = set()
if os.path.exists(_tb):
    for _t in json.load(open(_tb)):
        _m = _re.match(r'[A-Z]+\d+', _t['name'])
        if _m and any(not _l.get('arrived') for _l in _t['lines']):
            EN_CAMINO.add(_m.group(0))


CAJA_USD = 10.0     # lo que cuesta la caja del reloj (Eduardo, 21 ago 2026)

def con_caja(l):
    """El dato viene en el nombre de la variante: 'RELOJ CON CAJA' / 'sin caja'.

    Los $10 son LA CAJA DEL RELOJ, nada mas (Reyna, 5 oct 2026). Antes bastaba
    con que el texto dijera 'CON CAJA' y se le cobraban a lentes y carteras que
    tambien vienen en su caja pero no cuestan eso.
    """
    txt = ((l.get('var') or '') + ' ' + (l.get('prod') or '')).upper()
    if 'SIN CAJA' in txt:
        return False
    return 'CON CAJA' in txt and 'RELOJ' in txt


def calcula(o):
    """Aplica la formula de Eduardo a una orden completa."""
    costo, ship, sc = o['costo'], o['shipping'], o['sc']
    pct_ship = ship / costo if costo else 0
    filas = []
    for l in o['lineas']:
        # La caja va AL COSTO, no al precio: tambien paga flete, comision e importacion.
        cu = l['cu'] + (CAJA_USD if con_caja(l) else 0)
        l = dict(l, cu=cu, caja=1 if con_caja(l) else 0)
        F = l['cu'] * l['cant']
        G = F * pct_ship
        H = (F + G) * ALIBABA
        I = F + G + H
        filas.append(dict(l, F=F, G=G, H=H, I=I))
    tot_I = sum(f['I'] for f in filas) or 1
    for f in filas:
        f['J'] = f['I'] * TC
        f['K'] = f['I'] / tot_I
        f['L'] = sc * f['K']
        f['M'] = (f['J'] + f['L']) / f['cant'] if f['cant'] else 0
        f['pact'] = precio_shopify.get(f['sku'])
        f['en_shopify'] = f['sku'] in precio_shopify
    return filas, tot_I


def money(v, dec=2):
    return '—' if v is None else '{:,.{}f}'.format(v, dec)


def clave_pin(orden, i, f):
    """Clave con la que se guarda el precio capturado a mano.

    Normalmente es el SKU. Pero en los ODC vienen renglones SIN SKU (productos que
    todavia no se dan de alta en Shopify) y esos tambien llevan cuadrito para capturar
    precio. Si todos compartieran la clave vacia, lo que se escribe en uno aparecería
    en todos. Por eso se les arma una clave propia con la orden y el numero de renglon.
    """
    return f['sku'] or 'SINSKU:%s:%d' % (orden, i)


def semaforo(f):
    """Que tan sano es el precio de venta contra el costo real."""
    if not f['pact'] or not f['M']:
        return '', ''
    r = f['pact'] / f['M']
    if r < 2.5:
        return 'critico', 'Vende a %.1f× el costo — muy bajo' % r
    if r < 3:
        return 'bajo', 'Vende a %.1f× el costo' % r
    if r < 3.5:
        return 'ok', 'Vende a %.1f× el costo' % r
    return 'bueno', 'Vende a %.1f× el costo' % r


from collections import defaultdict
por_prov = defaultdict(lambda: {'tarjetas': [], 'bloques': [], 'inv': 0.0,
                                'ordenes': 0, 'lineas': 0, 'pzs': 0})
datos_js = {}          # datos crudos por orden, para armar el Excel con formulas
tot_inv_mxn = 0.0

def _clave(k):
    d = k[-6:]
    return (d[4:6], d[2:4], d[0:2]) if d.isdigit() else ('99', '99', k)

for nombre in sorted(ordenes, key=_clave):
    o = ordenes[nombre]
    prov = o.get('proveedor', 'ZOEY')
    P = por_prov[prov]
    filas, tot_I = calcula(o)
    # ---- ADUANA: lo pagado + lo que falta de las cajas sin pagar ----
    # La Shop and Cross se paga caja por caja. Lo que manda NO es si la mercancia ya llego, sino
    # si ya se pagaron todas las cajas (Eduardo, 10 sep 2026: ZOEY300726 llego a medias pero su
    # aduana ya estaba pagada completa, y el estimado la inflaba).
    #   1. Todas las cajas pagadas  -> lo pagado, sin estimar.
    #   2. Faltan cajas y ya hay pagadas -> pagado + promedio de SUS PROPIAS cajas x las que faltan.
    #   3. Ninguna pagada -> el porcentaje del proveedor, que es lo unico que hay.
    o['sc_estimado'] = False
    o['sc_pagado'] = o['sc']
    _base = sum(f['J'] for f in filas)
    _cajas = o.get('cajas')
    _pag = _inf.get('sc_cajas', {}).get(nombre, 0)
    _est = None
    _por = ''
    # 'aduana_completa' lo pone Eduardo cuando ya se pagaron todas las cajas de una orden que
    # sigue en camino: el estimado ya no aplica aunque la mercancia no haya llegado.
    _completa = o.get('aduana_completa') or (bool(_cajas) and _pag >= _cajas)
    # Solo se estima en ordenes ABIERTAS: las que siguen en camino y aun no pagan todas sus cajas.
    # Las viejas ya cerraron con lo que se pago (varias nunca tuvieron aduana) y no se tocan.
    if _completa or nombre not in EN_CAMINO:
        _est = None
    elif _cajas and _pag > 0:
        _prom = o['sc'] / _pag
        _est = o['sc'] + _prom * (_cajas - _pag)
        _por = '%d de %d cajas pagadas, las %d que faltan a $%s c/u' % (
            _pag, _cajas, _cajas - _pag, money(_prom))
    elif _pag == 0:
        _est = _base * PCT_ADUANA.get(prov, PCT_ADUANA_DEF)
        _por = 'ninguna caja pagada todavia, %s al %.0f%%' % (
            prov, PCT_ADUANA.get(prov, PCT_ADUANA_DEF) * 100)
    if _est and _est > o['sc']:
        o['sc'] = _est
        o['sc_estimado'] = True
        o['sc_porque'] = _por
        filas, tot_I = calcula(o)      # se rehace la tabla ya con la aduana estimada
        print('  Aduana estimada %-16s pagado %9.2f -> %9.2f   (%s)'
              % (nombre, o['sc_pagado'], _est, _por))
    inv = inversion.get(_norm(nombre), {})
    inv_mxn = inv.get('total_mxn') or None
    if inv_mxn:
        P['inv'] += inv_mxn

    pzs = sum(f['cant'] for f in filas)
    compra_mxn = sum(f['J'] for f in filas)          # J6 de la hoja de Eduardo
    costo_total_mxn = compra_mxn + o['sc']
    pct_ship = o['shipping'] / o['costo'] if o['costo'] else 0
    pct_sc = o['sc'] / compra_mxn if compra_mxn else 0     # J3 = L6/J6
    datos_js[nombre] = {
        'costo': round(o['costo'], 2), 'shipping': round(o['shipping'], 2),
        'sc': round(o['sc'], 2), 'tc': TC, 'alibaba': ALIBABA,
        'lineas': [{'sku': f['sku'], 'prod': f['prod'], 'var': f['var'],
                    'cant': f['cant'], 'cu': round(f['cu'], 4),
                    'pact': round(f['pact'], 2) if f['pact'] else None,
                    'pant': round(f['pant'], 2) if f['pant'] else None} for f in filas]}
    sin_sku = sum(1 for f in filas if not f['en_shopify'])

    P['ordenes'] += 1
    P['lineas'] += len(filas)
    P['pzs'] += pzs
    P['tarjetas'].append(
        '<button class="ocard" data-ir="%s"><b>%s</b>'
        '<span>%d líneas · %d pzs</span>'
        '<span class="mx">$%s MXN invertidos</span></button>'
        % (nombre, nombre, len(filas), pzs, money(inv_mxn, 0) if inv_mxn else '—'))

    trs = []
    for i, f in enumerate(filas, 1):
        cls, tip = semaforo(f)
        trs.append(
            '<tr data-b="%s">'
            '<td class="n">%d</td><td class="sku">%s</td><td>%s</td><td>%s</td>'
            '<td class="n">%d</td><td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%s</td><td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%s</td><td class="n">%s</td><td class="n">%s</td>'
            '<td class="n destacado">%s</td>'
            '<td class="n roas">%s</td><td class="n roas">%s</td><td class="n roas">%s</td>'
            '<td class="n pact %s" title="%s" data-sku="%s" data-m="%.2f">%s</td>'
            '<td class="n">%s</td></tr>'
            % (html.escape((f['prod'] + ' ' + f['sku'] + ' ' + f['var']).upper()),
               i, html.escape(f['sku']) or '—', html.escape(f['prod']), html.escape(f['var']),
               f['cant'], money(f['cu']), money(f['F']), money(f['G']), money(f['H']),
               money(f['I']), money(f['J']), '%.4f%%' % (f['K'] * 100), money(f['L']),
               money(f['M']),
               money(f['M'] * ROAS[0]), money(f['M'] * ROAS[1]), money(f['M'] * ROAS[2]),
               cls, html.escape(tip), html.escape(clave_pin(nombre, i, f)), f['M'],
               ('<input class="pin" value="%s" inputmode="decimal">' % money(f['pact'], 0))
               if f['pact'] else
               # Producto nuevo: todavia no tiene precio en Shopify, pero Eduardo necesita poder
               # capturarlo aqui mismo (10 sep 2026). Se deja el campo vacio y se marca "nuevo".
               # Las lineas SIN SKU tambien llevan cuadrito: en el ODC vienen productos que aun
               # no se dan de alta y hay que poderles capturar el precio (Reyna, 24 sep 2026).
               '<input class="pin nuevo" value="" placeholder="—" inputmode="decimal">',
               money(f['pant'])))

    aviso = ''
    if o.get('sc_estimado'):
        _pg = o.get('sc_pagado', 0.0)
        aviso = ('<div class="aviso">📦 <b>Aduana estimada.</b> La Shop and Cross se paga caja por '
                 'caja: %s. Llevas <b>$%s MXN</b> pagados y la tabla usa <b>$%s MXN</b> para que el '
                 'costo por pieza no te salga barato. En cuanto se paguen todas las cajas, se '
                 'cambia solo por lo real.</div>'
                 % (o.get('sc_porque', ''), money(_pg), money(o['sc'])))
    elif not o['sc']:
        aviso = ('<div class="aviso">⚠️ Esta orden todavía no tiene Shop and Cross pagado. '
                 'El costo por pieza está <b>incompleto</b> — le falta la aduana.</div>')
    elif sin_sku:
        aviso = ('<div class="aviso leve">%d producto%s de esta orden no está%s en Shopify. '
                 'Su casilla de precio viene vacía y en amarillo: escríbele el precio ahí mismo y '
                 'se guarda en la lista de pendientes.</div>'
                 % (sin_sku, 's' if sin_sku > 1 else '', 'n' if sin_sku > 1 else ''))

    P['bloques'].append("""
<section class="orden cerrada" id="%s">
  <div class="cab">
    <h2>%s</h2>
    <div class="acciones">
      <button class="btn desc" data-csv="%s">⬇ Descargar Excel</button>
      <button class="btn toggle">Ver tabla</button>
    </div>
  </div>
  <div class="resumen">
    <div class="dato"><span>Costo de la orden</span><b>$%s <i>US</i></b></div>
    <div class="dato"><span>Shipping</span><b>$%s <i>US</i></b></div>
    <div class="dato pct"><span>%% de shipping</span><b>%.2f%%</b><i class="sub">shipping ÷ costo</i></div>
    <div class="dato"><span>Comisión Alibaba</span><b>3%%</b></div>
    <div class="dato"><span>Shop and Cross%s</span><b>$%s <i>MXN</i></b>%s</div>
    <div class="dato pct"><span>%% Shop and Cross</span><b>%.2f%%</b><i class="sub">aduana ÷ compra en pesos</i></div>
    <div class="dato"><span>Tipo de cambio</span><b>%.0f</b></div>
    <div class="dato fuerte"><span>Costo total puesto</span><b>$%s <i>MXN</i></b></div>
    <div class="dato inv"><span>Lo que realmente se pagó</span><b>$%s <i>MXN</i></b><i class="sub">%s pagos a Alibaba</i></div>
  </div>
  %s
  <div class="plegable"><div class="tblwrap"><table>
    <thead><tr>
      <th>#</th><th>SKU</th><th>PRODUCTO</th><th>VARIANTE</th><th>CANT</th>
      <th>COSTO UNIT<br><i>US</i></th><th>COSTO TOTAL<br><i>US</i></th>
      <th>CON ENVÍO<br><i>US</i></th><th>3%% ALIBABA<br><i>US</i></th>
      <th>COMPRA ALIBABA<br><i>US</i></th><th>COMPRA<br><i>MXN</i></th>
      <th>%% DEL COSTO</th><th>SHOP AND CROSS<br><i>MXN</i></th>
      <th>COSTO UNIT TOTAL<br><i>MXN</i></th>
      <th>ROAS 3</th><th>ROAS 3.5</th><th>ROAS 4</th>
      <th>PRECIO ACTUAL<br><i>Shopify</i></th><th>PRECIO ANTIGUO</th>
    </tr></thead>
    <tbody>%s</tbody>
  </table></div></div>
</section>""" % (nombre, nombre, nombre, money(o['costo']), money(o['shipping']),
                 pct_ship * 100,
                 (' <i class="sub">estimada</i>' if o.get('sc_estimado') else ''),
                 money(o['sc']),
                 ('<i class="sub">pagados $%s</i>' % money(o.get('sc_pagado', 0.0))) if o.get('sc_estimado') else '',
                 pct_sc * 100, TC, money(costo_total_mxn, 0),
                 money(inv_mxn, 0) if inv_mxn else '—', inv.get('pagos', '—'),
                 aviso, ''.join(trs)))

CORTE = '%d de %s de %d' % (HOY.day, _MESES_L[HOY.month - 1], HOY.year)


# ══════════════════════════════════════════════════════════════
#  PANEL DE INVERSION 2026 (pedido de Eduardo, 20 ago 2026)
#  Lo realmente pagado: Alibaba (producto + comision) + aduana.
#  Color: slots 1 y 2 del palette de referencia, en su orden documentado.
# ══════════════════════════════════════════════════════════════
_MES_CORTO = {'01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun',
              '07': 'Jul', '08': 'Ago', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic'}

def _prov_de(o):
    # 'HAIFEN' sin G y RITA/ISLA/COCOZHANG faltaban, y por eso 4 ordenes del
    # INFORME ($144,550.80) no entraban al panel de inversion. Reyna, 5 oct 2026.
    for k, v in (('HAIFENG', 'HAIFENG'), ('HAIFEN', 'HAIFENG'), ('ZOEY', 'ZOEY'),
                 ('CYNTHIA', 'CYNTHIA CAO'), ('NANCY', 'NANCY VIP'), ('DINADU', 'DINA DU'),
                 ('COCOMA', 'COCOMA'), ('COCOZHANG', 'COCO ZHANG'), ('MOLLY', 'MOLLY'),
                 ('DONGAI', 'DONGAI'), ('RITA', 'RITA'), ('ISLA', 'ISLA')):
        if o.startswith(k):
            return v
    return None

por_mes = defaultdict(lambda: {'ali': 0.0, 'adu': 0.0, 'ord': set()})
por_prov_inv = defaultdict(lambda: {'ali': 0.0, 'adu': 0.0, 'ord': set()})
detalle = []
for _o, _v in _inf['inv'].items():
    _p = _prov_de(_o)
    if not _p or not _v['mxn']:
        continue
    _m = (_v['mes'] or '')[:7]
    _adu = _inf['sc'].get(_o, 0.0)
    por_mes[_m]['ali'] += _v['mxn']; por_mes[_m]['adu'] += _adu
    por_mes[_m]['ord'].add(_o)
    por_prov_inv[_p]['ali'] += _v['mxn']; por_prov_inv[_p]['adu'] += _adu
    por_prov_inv[_p]['ord'].add(_o)
    detalle.append((_o, _p, _m, _v['mxn'], _adu, _v['pagos']))

# El mes de cada pago sale del INFORME del Drive (datos/precios/inversion_mes.json,
# que escribe scripts/dump_inversion_mes.py), no del nombre de la orden: NANCY220826
# se siguio pagando en septiembre y HAIFENG290926 ya cayo en octubre, y por eso
# septiembre salia en $753 mil cuando fueron mas de $900 mil. Reyna, 5 oct 2026.
# Ahi tambien entra la aduana de las ordenes viejas que no tienen inversion
# registrada. Si el archivo no esta, se cae al mes del nombre de la orden.
_invmes = os.path.join(DATOS, 'inversion_mes.json')
if os.path.isfile(_invmes):
    _IM = json.load(open(_invmes))
    por_mes = {k: {'ali': v['ali'], 'adu': v['adu'], 'ord': v['ordenes']}
               for k, v in _IM['mes'].items()}

INV_TOTAL = sum(v['ali'] + v['adu'] for v in por_mes.values())
INV_ALI = sum(v['ali'] for v in por_mes.values())
INV_ADU = sum(v['adu'] for v in por_mes.values())
N_ORD = len(detalle)

_meses = sorted(m for m in por_mes if m)
_topmes = max((por_mes[m]['ali'] + por_mes[m]['adu']) for m in _meses) or 1
_barras = []
for _m in _meses:
    _d = por_mes[_m]; _t = _d['ali'] + _d['adu']
    _h = _t / _topmes * 100
    _ha = _d['ali'] / _t * 100 if _t else 0
    _barras.append(
        '<div class="bcol" tabindex="0" aria-label="' + _MES_CORTO[_m[5:7]] + ': $' + money(_t, 0) + ' MXN">'
        '<b class="bval">' + money(_t / 1000, 0) + 'k</b>'
        '<div class="bwrap"><div class="bar" style="height:' + '%.1f' % _h + '%">'
        '<div class="seg s2" style="height:' + '%.1f' % (100 - _ha) + '%"></div>'
        '<div class="seg s1" style="height:' + '%.1f' % _ha + '%"></div></div></div>'
        '<span class="blab">' + _MES_CORTO[_m[5:7]] + '</span>'
        '<div class="btip">' + _MES_CORTO[_m[5:7]] + ' 2026<br>'
        '<i>Alibaba</i> $' + money(_d['ali'], 0) + '<br>'
        '<i>Aduana</i> $' + money(_d['adu'], 0) + '<br>'
        '<b>Total</b> $' + money(_t, 0) + ' · '
        + str(_d['ord'] if isinstance(_d['ord'], int) else len(_d['ord'])) + ' órdenes</div></div>')

_provs_inv = sorted(por_prov_inv, key=lambda k: -(por_prov_inv[k]['ali'] + por_prov_inv[k]['adu']))
_topprov = max((por_prov_inv[p]['ali'] + por_prov_inv[p]['adu']) for p in _provs_inv) or 1
_hbar = []
for _p in _provs_inv:
    _d = por_prov_inv[_p]; _t = _d['ali'] + _d['adu']
    _hbar.append(
        '<div class="hrow"><span class="hlab">' + _p + '</span>'
        '<div class="htrack"><div class="hbar s1" style="width:' + '%.1f' % (_d['ali'] / _topprov * 100) + '%"></div>'
        '<div class="hbar s2" style="width:' + '%.1f' % (_d['adu'] / _topprov * 100) + '%"></div></div>'
        '<b class="hval">$' + money(_t, 0) + '</b>'
        '<span class="hord">' + str(len(_d['ord'])) + ' órd.</span></div>')

detalle.sort(key=lambda x: -(x[3] + x[4]))
_filas_inv = ''.join(
    '<tr><td><b>' + o + '</b></td><td>' + p + '</td><td>' + (_MES_CORTO[m[5:7]] + ' ' + m[:4] if m else '—') +
    '</td><td class="n">' + money(a, 0) + '</td><td class="n">' + (money(d, 0) if d else '<i>pendiente</i>') +
    '</td><td class="n destacado">' + money(a + d, 0) + '</td><td class="n">' + str(pg) + '</td></tr>'
    for o, p, m, a, d, pg in detalle)

PANEL = ('<div class="prov" data-p="__INV__">'
  '<div class="hero"><span>Invertido en 2026</span><b>$' + money(INV_TOTAL, 0) + '</b>'
  '<i>pesos mexicanos, realmente pagados</i></div>'
  '<div class="tiles">'
  '<div class="tile"><span>Pagado a proveedores</span><b>$' + money(INV_ALI, 0) + '</b>'
  '<i>producto + 3% de Alibaba</i></div>'
  '<div class="tile"><span>Importación</span><b>$' + money(INV_ADU, 0) + '</b>'
  '<i>Shop and Cross</i></div>'
  '<div class="tile"><span>Órdenes pagadas</span><b>' + str(N_ORD) + '</b>'
  '<i>en ' + str(len(_provs_inv)) + ' proveedores</i></div>'
  '<div class="tile"><span>Promedio por orden</span><b>$' + money(INV_TOTAL / N_ORD if N_ORD else 0, 0) + '</b>'
  '<i>todo incluido</i></div></div>'
  '<div class="leyenda2"><span><i class="sw s1"></i> Pagado a proveedores</span>'
  '<span><i class="sw s2"></i> Importación</span></div>'
  '<div class="panel"><h3>Mes con mes</h3><div class="bars">' + ''.join(_barras) + '</div></div>'
  '<div class="panel"><h3>Por proveedor</h3><div class="hbars">' + ''.join(_hbar) + '</div></div>'
  '<div class="panel"><h3>Orden por orden</h3><div class="tblwrap"><table>'
  '<thead><tr><th>ORDEN</th><th>PROVEEDOR</th><th>MES DE LA ORDEN</th>'
  '<th>PAGADO AL PROVEEDOR</th><th>IMPORTACIÓN</th><th>TOTAL REAL</th><th>PAGOS</th></tr></thead>'
  '<tbody>' + _filas_inv + '</tbody></table></div></div></div>')


# ══════════════════════════════════════════════════════════════
#  TABLERO (Reyna, 5 oct 2026): margen real y recuperacion por orden.
#  Los numeros los calcula scripts/build_analisis.py y llegan en analisis.json;
#  aqui solo se pintan. Si el archivo no existe, la pestana no aparece y la
#  pagina queda exactamente igual que antes.
# ══════════════════════════════════════════════════════════════
TABLERO = ''
_an = os.path.join(DATOS, 'analisis.json')
if os.path.isfile(_an):
    A = json.load(open(_an))

    def _pill(txt, cls=''):
        return '<span class="pill %s">%s</span>' % (cls, txt)

    _pe = ''.join(
        '<tr><td>%s</td><td class="muted">%s</td><td class="n">$%s</td>'
        '<td class="n">$%s</td><td class="n mal">%.2f×</td></tr>'
        % (html.escape(x['prod']), html.escape(x['prov']), money(x['M'], 0),
           money(x['p'], 0), x['x'])
        for x in A['peores'])

    # Tarjetas en vez de tabla de 7 columnas: Reyna pidio menos texto y mas
    # visual (5 oct 2026). La barra se mide contra 4x, el ROAS mas alto que usamos.
    def _cls_mult(m):
        return 'ok' if m >= 3.5 else ('mal' if m < 3 else 'warn')

    _res = ''.join(
        '<div class="pk"><b class="pknom">%s</b>'
        '<div class="pkx %s">%.2f×</div>'
        '<div class="barra ancha"><i class="%s" style="width:%d%%"></i></div>'
        '<div class="pkpie"><span>Ingreso<b>$%s</b></span>'
        '<span>Margen<b>%.0f%%</b></span>'
        '<span>Parado<b class="%s">$%s</b></span></div></div>'
        % (html.escape(p_), _cls_mult(d['mult']), d['mult'], _cls_mult(d['mult']),
           min(100, int(d['mult'] / 4 * 100)), money(d['ing'], 0), d['pct'],
           'mal' if d['parado_mxn'] > 150000 else '', money(d['parado_mxn'], 0))
        for p_, d in sorted(A['prov'].items(), key=lambda x: -x[1]['ing']) if d['q'])

    _bloques = []
    for p_, d in sorted(A['prov'].items(), key=lambda x: -x[1]['ing']):
        if not d['ordenes']:
            continue
        _ords = []
        for o in d['ordenes']:
            if o['camino']:
                av = _pill('en camino')
                cls = 'muted'
            elif o['pct'] is None:
                av = _pill('sin inversión registrada', 'mal')
                cls = 'muted'
            else:
                cls = 'ok' if o['pct'] >= 100 else 'mal'
                av = ('<div class="barra"><i class="%s" style="width:%d%%"></i></div>'
                      '<b class="%s">%.0f%%</b>' % (cls, min(100, int(o['pct'])), cls, o['pct']))
            _dt = ('llega en %d días' % -o['dias']) if o['dias'] < 0 else ('%d días' % o['dias'])
            _ords.append(
                '<tr><td>%s<br><span class="muted">%s · %s</span></td>'
                '<td class="n">$%s</td><td class="n">$%s</td><td class="av">%s</td>'
                '<td class="n">%d<span class="muted">/%d</span></td>'
                '<td class="n">%d</td><td class="n %s">$%s</td></tr>'
                % (o['orden'], o['fecha'], _dt, money(o['inv'], 0), money(o['ing'], 0),
                   av, o['q'], o['pzs'], o['nunca'],
                   'mal' if o['rest_mxn'] > 150000 else '', money(o['rest_mxn'], 0)))
        _b3 = ''
        if d['bajo3']:
            _b3 = ('<div class="panel malpanel"><h3>Se venden por debajo de 3× — hay que subirles el precio'
                   ' <i>%d</i></h3><div class="tblwrap"><table><thead><tr><th>Producto</th>'
                   '<th>Orden</th><th class="n">Cuesta</th><th class="n">Vende</th>'
                   '<th class="n">Debería (3×)</th><th class="n">×</th></tr></thead><tbody>%s'
                   '</tbody></table></div></div>'
                   % (len(d['bajo3']), ''.join(
                       '<tr><td><a class="irprod" data-prov="%s" data-ir="%s" data-sku="%s">%s'
                       ' <span class="muted">%s</span></a></td><td class="muted">%s</td>'
                       '<td class="n">$%s</td><td class="n mal">$%s</td><td class="n ok">$%s</td>'
                       '<td class="n mal">%.2f×</td></tr>'
                       % (html.escape(p_), x['orden'], html.escape(x['sku'] or ''),
                          html.escape(x['prod']), html.escape(x['var'] or ''), x['orden'],
                          money(x['M'], 0), money(x['p'], 0), money(redondea99(x['M'] * 3), 0), x['x'])
                       for x in d['bajo3'])))
        _est = []
        for o in d['ordenes']:
            for e in o['est']:
                _est.append((e['mxn'], o['orden'], e))
        _est.sort(reverse=True, key=lambda x: x[0])
        _estht = ''
        if _est:
            _estht = ('<section class="orden cerrada"><div class="ohead"><h3>Parado de verdad '
                      '<i>%d productos · $%s MXN · ya llegaron y no venden una pieza desde hace '
                      '60 días o más</i></h3><button class="btn toggle">Ver tabla</button></div>'
                      '<div class="plegable"><div class="tblwrap"><table><thead><tr><th>Producto</th>'
                      '<th>Orden</th><th class="n">Quedan</th><th class="n">De</th>'
                      '<th class="n">Costo c/u</th><th class="n">Parado</th>'
                      '<th class="n">Sin vender</th></tr></thead><tbody>%s</tbody></table></div>'
                      '</div></section>'
                      % (len(_est), money(sum(x[0] for x in _est), 0), ''.join(
                          '<tr><td><a class="irprod" data-prov="%s" data-ir="%s" data-sku="%s">%s'
                          ' <span class="muted">%s</span></a>%s</td><td class="muted">%s</td>'
                          '<td class="n">%d</td><td class="n muted">%d</td><td class="n">$%s</td>'
                          '<td class="n">$%s</td><td class="n %s">%s</td></tr>'
                          % (html.escape(p_), k2, html.escape(e['sku'] or ''),
                             html.escape(e['prod']), html.escape(e['var'] or ''),
                             ' ' + _pill('ni una venta en el año', 'mal') if e['nunca'] else '',
                             k2, e['rest'], e['q'], money(e['M'], 0), money(e['mxn'], 0),
                             'mal' if (e['dsv'] is None or e['dsv'] >= 90) else 'warn',
                             'nunca' if e['dsv'] is None else ('%d d' % e['dsv']))
                          for _m, k2, e in _est[:60])))
        _sc = ''
        if d['q_sc']:
            _sc = ('<p class="nota">%d piezas por $%s MXN entraron al ingreso pero <b>sin costo</b>: '
                   'son SKU que no aparecen en ningún ODC. No cuentan para el margen.</p>'
                   % (d['q_sc'], money(d['ing_sc'], 0)))
        _rec = (d['ing'] / d['inv'] * 100) if d['inv'] else 0
        _bloques.append(
            '<details class="panel pdet"><summary>'
            '<span class="sgn">%s</span>'
            '<span class="sdat"><i>Recuperado</i><b class="%s">%.0f%%</b></span>'
            '<span class="sdat"><i>Múltiplo</i><b class="%s">%.2f×</b></span>'
            '<span class="sdat"><i>Órdenes</i><b>%d</b></span>'
            '<span class="sdat"><i>Bajo 3×</i><b class="%s">%d</b></span>'
            '<span class="sdat"><i>Parado</i><b class="%s">$%s</b></span></summary>'
            '<div class="tiles">'
            '<div class="tile"><span>Invertido</span><b>$%s</b></div>'
            '<div class="tile"><span>Ingreso</span><b>$%s</b></div>'
            '<div class="tile ok"><span>Margen</span><b>$%s</b><span>%.1f%%</span></div>'
            '<div class="tile %s"><span>Múltiplo</span><b>%.2f×</b></div>'
            '<div class="tile warn"><span>Parado</span><b>$%s</b><span>%d pzs</span></div>'
            '</div>'
            '<div class="tblwrap"><table><thead><tr><th>Orden</th><th class="n">Invertido</th>'
            '<th class="n">Recuperado</th><th>Avance</th><th class="n">Vendidas</th>'
            '<th class="n">Sin vender</th><th class="n">Parado</th></tr></thead>'
            '<tbody>%s</tbody></table></div>%s%s%s</details>'
            % (html.escape(p_),
               'ok' if _rec >= 100 else 'mal', _rec,
               _cls_mult(d['mult']), d['mult'], len(d['ordenes']),
               'mal' if d['bajo3'] else '', len(d['bajo3']),
               'mal' if d['parado_mxn'] > 150000 else '', money(d['parado_mxn'], 0),
               money(d['inv'], 0), money(d['ing'], 0), money(d['margen'], 0),
               d['pct'], _cls_mult(d['mult']),
               d['mult'], money(d['parado_mxn'], 0), d['parado_q'],
               ''.join(_ords), _sc, _b3, _estht))

    TABLERO = (
        '<div class="prov" data-p="__DASH__">'
        '<h2>Tablero · qué tanto se está vendiendo y con cuánto margen</h2>'
        '<p class="nota">Cada venta se le acredita al <b>lote</b> que la surtió, no al proveedor que '
        'diga Shopify: primero que entra, primero que sale. Ya con devoluciones descontadas. '
        'Es <b>margen bruto de mercancía</b> — no trae publicidad, envíos ni comisiones. '
        'Corte al %s.</p>'
        '<div class="panel malpanel"><h3>Los 5 peores de toda la tienda</h3>'
        '<div class="tblwrap"><table><thead><tr><th>Producto</th><th>Proveedor</th>'
        '<th class="n">Cuesta</th><th class="n">Vende</th><th class="n">×</th></tr></thead>'
        '<tbody>%s</tbody></table></div></div>'
        '<div class="panel"><h3>Proveedor por proveedor'
        ' <i>cuántas veces el costo se está vendiendo · la barra llena es 4×</i></h3>'
        '<div class="pkgrid">%s</div></div>'
        '<p class="nota">Cada proveedor viene cerrado. Ábrelo para ver orden por orden, '
        'los productos bajo 3× y lo que lleva parado en bodega.</p>'
        '%s</div>' % (A['generado'], _pe, _res, ''.join(_bloques)))

provs = [p for p in ORDEN_PROV if p in por_prov] + \
        [p for p in sorted(por_prov) if p not in ORDEN_PROV]
tot_inv_mxn = sum(por_prov[p]['inv'] for p in provs)
tot_ord = sum(por_prov[p]['ordenes'] for p in provs)
tot_lin = sum(por_prov[p]['lineas'] for p in provs)

botones = ['<button class="ptab on" data-p="__INV__">📊 Inversión 2026</button>']
secciones = [PANEL.replace('class="prov" data-p="__INV__"', 'class="prov on" data-p="__INV__"')]
if TABLERO:
    botones.append('<button class="ptab" data-p="__DASH__">📈 Tablero</button>')
    secciones.append(TABLERO)
for i, p in enumerate(provs):
    P = por_prov[p]
    botones.append('<button class="ptab" data-p="%s">%s <i>%d</i></button>'
                   % (p, p, P['ordenes']))
    secciones.append(
        '<div class="prov" data-p="%s">'
        '<h2>%s · %d órdenes · %d productos · $%s MXN invertidos en 2026</h2>'
        '<div class="cards">%s</div>%s</div>'
        % (p, p, P['ordenes'], P['lineas'],
           money(P['inv'], 0), ''.join(P['tarjetas']), ''.join(P['bloques'])))

HTML = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jewelry Remate MX — Tablas de precios</title><style>
:root{--bg:#f6f7fb;--card:#fff;--ink:#15192b;--muted:#6b7285;--line:#e4e7f0;--a:#c0392b;--a-bg:#fdecea;
--ok:#1e7d46;--ok-bg:#e8f5ee;--warn:#b26a00;--warn-bg:#fdf3e0;--blue:#20508c;--blue-bg:#e8effa;
--gray-bg:#f0f1f5;--reb:#8a2be2;--reb-bg:#f3eafe}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.nav{background:#0d1226;padding:0 18px}
.navin{max-width:1600px;margin:0 auto;display:flex;gap:4px;flex-wrap:wrap}
.nl{display:block;padding:9px 14px;font-size:13px;font-weight:600;text-decoration:none;
color:#9aa3c0;border-bottom:2px solid transparent}
.nl:hover{color:#fff}
.nl.on{color:#fff;border-bottom-color:#e8b93c}
.top{background:#141a33;color:#fff;padding:0 18px;position:sticky;top:0;z-index:30}
.in{max-width:1600px;margin:0 auto;display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.brand{padding:12px 0;font-weight:700}.brand small{display:block;font-weight:400;font-size:11px;color:#9aa3c0}
.wrap{max-width:1600px;margin:0 auto;padding:18px}
h2{font-size:19px;margin:0 0 10px}
.intro{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:16px}
.intro p{margin:0 0 6px;color:var(--muted);font-size:13px;max-width:105ch}
.intro b{color:var(--ink)}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;align-items:center}
input[type=search]{flex:1;min-width:240px;font:inherit;padding:9px 12px;border:1.5px solid var(--line);border-radius:9px}

/* ── panel de inversion ── */
.viz{--s1:#2a78d6;--s2:#eb6834}
.hero{background:#141a33;color:#fff;border-radius:14px;padding:22px 26px;margin-bottom:14px}
.hero span{display:block;font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:#9aa3c0}
.hero b{display:block;font-size:clamp(30px,6vw,46px);line-height:1.1;font-variant-numeric:tabular-nums;margin:4px 0}
.hero i{font-style:normal;font-size:13px;color:#9aa3c0}
.tiles{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));margin-bottom:14px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:12px 14px}
.tile span{display:block;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.tile b{display:block;font-size:22px;font-variant-numeric:tabular-nums;margin:2px 0}
.tile i{font-style:normal;font-size:12px;color:var(--muted)}
.leyenda2{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-bottom:12px}
.sw{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:-1px;margin-right:5px}
.sw.s1,.seg.s1,.hbar.s1{background:#2a78d6}
.sw.s2,.seg.s2,.hbar.s2{background:#eb6834}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.panel h3{margin:0 0 14px;font-size:15px}
.bars{display:flex;gap:10px;align-items:flex-end;height:230px}
.bcol{flex:1;display:flex;flex-direction:column;align-items:center;gap:5px;position:relative;
min-width:0;height:100%;justify-content:flex-end;cursor:default}
.bcol:focus{outline:2px solid var(--blue);outline-offset:3px;border-radius:6px}
.bval{font-size:11.5px;font-variant-numeric:tabular-nums;color:var(--muted)}
.bwrap{width:100%;flex:1;display:flex;align-items:flex-end}
.bar{width:100%;display:flex;flex-direction:column;border-radius:4px 4px 0 0;overflow:hidden;gap:2px}
.seg{width:100%}
.blab{font-size:12px;color:var(--muted)}
.btip{display:none;position:absolute;bottom:100%;left:50%;transform:translateX(-50%);
background:#141a33;color:#fff;font-size:12px;line-height:1.55;padding:9px 12px;border-radius:9px;
white-space:nowrap;z-index:5;box-shadow:0 6px 20px rgba(0,0,0,.22)}
.btip i{font-style:normal;color:#9aa3c0;display:inline-block;min-width:64px}
.bcol:hover .btip,.bcol:focus .btip{display:block}
.hbars{display:flex;flex-direction:column;gap:9px}
.hrow{display:grid;grid-template-columns:110px 1fr auto 58px;gap:11px;align-items:center}
.hlab{font-size:13px;font-weight:600}
.htrack{display:flex;gap:2px;height:22px;background:var(--gray-bg);border-radius:4px;overflow:hidden}
.hbar{height:100%}
.hval{font-size:13px;font-variant-numeric:tabular-nums;font-weight:700}
.hord{font-size:11.5px;color:var(--muted);text-align:right}
@media(max-width:620px){.hrow{grid-template-columns:88px 1fr auto}.hord{display:none}}
.ptabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
.ptab{font:inherit;font-size:13px;font-weight:700;padding:9px 15px;border-radius:10px;cursor:pointer;
border:1.5px solid var(--line);background:var(--card);color:var(--muted)}
.ptab i{font-style:normal;font-weight:500;opacity:.7}
.ptab:hover{border-color:var(--blue)}
.ptab.on{background:#141a33;border-color:#141a33;color:#fff}
.prov{display:none}.prov.on{display:block}
.cards{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));margin-bottom:20px}
.ocard{text-align:left;background:var(--card);border:1px solid var(--line);border-radius:11px;
padding:11px 13px;cursor:pointer;font:inherit;display:flex;flex-direction:column;gap:2px}
.ocard:hover{border-color:var(--blue)}
.ocard b{font-size:14px}.ocard span{font-size:12px;color:var(--muted)}
.ocard .mx{color:var(--ok);font-weight:600}
.orden{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.cab{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:10px}
.cab h2{margin:0}
.acciones{display:flex;gap:8px}
.btn{font:inherit;font-size:13px;font-weight:600;padding:7px 13px;border-radius:9px;cursor:pointer;
border:1.5px solid var(--line);background:var(--card);color:var(--ink)}
.btn:hover{border-color:var(--blue);color:var(--blue)}
.btn.desc{background:var(--ok-bg);border-color:transparent;color:var(--ok)}
.btn.desc:hover{filter:brightness(.95)}
.orden.cerrada .plegable{display:none}
.orden.cerrada{padding-bottom:12px}
.resumen{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));margin-bottom:12px}
.dato{background:var(--gray-bg);border-radius:9px;padding:9px 11px;display:flex;flex-direction:column}
.dato span{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.dato b{font-size:16px;font-variant-numeric:tabular-nums}
.dato i{font-style:normal;font-size:11px;color:var(--muted)}
.dato b i{font-size:11px}
.dato.fuerte{background:var(--blue-bg)}.dato.fuerte b{color:var(--blue)}
.dato.inv{background:var(--ok-bg)}.dato.inv b{color:var(--ok)}
.dato.pct{background:var(--reb-bg)}.dato.pct b{color:var(--reb)}
.pin{width:78px;font:inherit;font-size:12.5px;font-weight:700;text-align:right;padding:3px 5px;
border:1.5px solid transparent;border-radius:6px;background:transparent;color:inherit;
font-variant-numeric:tabular-nums}
.pin:hover{border-color:var(--line);background:#fff}
.pin:focus{outline:none;border-color:var(--blue);background:#fff}
.pin.nuevo{border-color:#c9a227;background:#fffdf2}
.pin.nuevo::placeholder{color:#b08900;font-weight:700}
td.pact.sinprecio::after{content:"nuevo — ponle precio";display:block;font-size:9.5px;font-weight:600;color:#b08900;line-height:1.1;margin-top:1px}
td.pact.pend{background:var(--warn-bg)!important}
td.pact.pend .pin{color:var(--warn)}
td.pact.pend::after{content:"pendiente";display:block;font-size:9.5px;font-weight:600;
letter-spacing:.04em;text-transform:uppercase;color:var(--warn);margin-top:1px}
.aplicado{background:var(--ok-bg);color:var(--ok);border:1px solid rgba(30,125,70,.25);
border-radius:10px;padding:11px 14px;margin-bottom:14px;font-size:13.5px;transition:opacity .8s}
.barra{position:fixed;left:0;right:0;bottom:0;background:#141a33;color:#fff;padding:11px 18px;
display:none;z-index:60;box-shadow:0 -4px 20px rgba(0,0,0,.2)}
.barra.on{display:block}
.barrain{max-width:1600px;margin:0 auto;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.barra b{font-size:15px}
.barra .sec2{color:#9aa3c0;font-size:13px;flex:1;min-width:180px}
.barra button{font:inherit;font-size:13px;font-weight:600;padding:8px 14px;border-radius:9px;
cursor:pointer;border:0;background:#e8b93c;color:#141a33}
.barra button.gris{background:#39406b;color:#fff}
.lista{max-width:1600px;margin:10px auto 0;background:#0d1226;border-radius:10px;padding:12px 14px;
font-family:ui-monospace,Menlo,monospace;font-size:12px;line-height:1.7;color:#c3cadf;
max-height:190px;overflow:auto;display:none;white-space:pre}
.lista.on{display:block}
.aviso{background:var(--a-bg);color:var(--a);border-radius:9px;padding:9px 12px;font-size:13px;margin-bottom:10px}
.aviso.leve{background:var(--warn-bg);color:var(--warn)}
.tblwrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:12.5px;min-width:1500px}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}
thead th{background:#fafbfe;position:sticky;top:0;font-size:11px;text-transform:uppercase;
letter-spacing:.03em;color:var(--muted);vertical-align:bottom;z-index:2}
thead th i{font-style:normal;font-weight:400;text-transform:none;letter-spacing:0}
td.n{text-align:right;font-variant-numeric:tabular-nums}
td.sku{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:var(--muted)}
tbody tr:hover{background:#fafbff}
td.destacado{font-weight:700;background:var(--blue-bg);color:var(--blue)}
td.roas{color:var(--muted)}
td.pact{font-weight:700}
td.pact.critico{background:var(--a-bg);color:var(--a)}
td.pact.bajo{background:var(--warn-bg);color:var(--warn)}
td.pact.ok{background:var(--gray-bg)}
td.pact.bueno{background:var(--ok-bg);color:var(--ok)}
.nota{font-size:12.5px;color:var(--muted);line-height:1.6;margin:0 0 14px}
.malpanel{border-color:var(--a)}
.malpanel h3{color:var(--a)}
.panel h3 i{font-style:normal;font-weight:400;color:var(--muted);font-size:12.5px}
td.muted,span.muted{color:var(--muted)}
td.ok,b.ok{color:var(--ok)}
td.mal,b.mal{color:var(--a)}
td.warn{color:var(--warn)}
.pill{display:inline-block;font-size:11px;padding:1px 7px;border-radius:999px;
  border:1px solid var(--line);color:var(--muted);white-space:nowrap}
.pill.mal{border-color:var(--a);color:var(--a);background:var(--a-bg)}
td.av{min-width:150px}
.barra{display:inline-block;width:88px;height:7px;border-radius:999px;background:var(--gray-bg);
  overflow:hidden;vertical-align:middle;margin-right:7px}
.barra i{display:block;height:100%;background:var(--ok)}
/* ── Tablero: tarjetas de proveedor y bloques plegados (Reyna, 5 oct 2026) ── */
.barra.ancha{width:100%;height:9px;margin:0 0 11px}
.barra i.mal{background:var(--a)}
.barra i.warn{background:var(--warn)}
.pkgrid{display:grid;gap:11px;grid-template-columns:repeat(auto-fill,minmax(188px,1fr))}
.pk{border:1px solid var(--line);border-radius:13px;padding:13px 14px 11px;background:var(--card)}
.pknom{display:block;font-size:12px;letter-spacing:.04em;text-transform:uppercase;
  color:var(--muted);margin:0 0 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pkx{font-size:27px;font-weight:800;line-height:1.1;margin:0 0 8px;font-variant-numeric:tabular-nums}
.pkx.ok{color:var(--ok)} .pkx.warn{color:var(--warn)} .pkx.mal{color:var(--a)}
.pkpie{display:flex;justify-content:space-between;gap:8px;font-size:10.5px;color:var(--muted)}
.pkpie span{display:flex;flex-direction:column;gap:2px;min-width:0}
.pkpie b{font-size:12.5px;color:var(--fg);font-weight:700;white-space:nowrap}
.pkpie b.mal{color:var(--a)}
.pdet{padding:0}
.pdet>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:18px;
  flex-wrap:wrap;padding:14px 18px}
.pdet>summary::-webkit-details-marker{display:none}
.pdet>summary::after{content:'▸';margin-left:auto;color:var(--muted);font-size:14px}
.pdet[open]>summary::after{content:'▾'}
.pdet[open]>summary{border-bottom:1px solid var(--line)}
.pdet>summary:hover{background:var(--gray-bg)}
.sgn{font-size:15px;font-weight:800;min-width:132px}
.sdat{display:flex;flex-direction:column;gap:1px;font-size:10.5px;color:var(--muted)}
.sdat i{font-style:normal;letter-spacing:.03em;text-transform:uppercase}
.sdat b{font-size:14px;color:var(--fg);font-variant-numeric:tabular-nums}
.sdat b.ok{color:var(--ok)} .sdat b.warn{color:var(--warn)} .sdat b.mal{color:var(--a)}
.pdet>.tiles,.pdet>.tblwrap,.pdet>.nota,.pdet>div.panel,.pdet>section{margin:14px 18px}
.pdet>.tblwrap{margin-bottom:18px}
a.irprod{color:inherit;text-decoration:none;border-bottom:1px dotted var(--muted);cursor:pointer}
a.irprod:hover{color:var(--blue);border-bottom-color:var(--blue)}
tr.resalta>td{background:var(--warn-bg);box-shadow:inset 0 0 0 1px var(--warn)}
tr.resalta>td:first-child{box-shadow:inset 1px 0 0 var(--warn),inset 0 1px 0 var(--warn),inset 0 -1px 0 var(--warn)}
@media(max-width:620px){
  .pdet>summary{gap:12px;padding:12px 13px}
  .sgn{min-width:100%}
  .pdet>.tiles,.pdet>.tblwrap,.pdet>.nota,.pdet>div.panel,.pdet>section{margin:11px 13px}
}
.barra i.mal{background:var(--a)}
.leyenda{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:10px 0 0}
.leyenda i{font-style:normal;padding:2px 7px;border-radius:5px}
.foot{color:var(--muted);font-size:12px;padding:18px 0;text-align:center}
</style></head><body>
<div class="nav"><div class="navin">
  <a class="nl" href="ordenes.html">🚦 Órdenes de compra</a>
  <a class="nl on" href="precios.html">💲 Tablas de precios</a>
</div></div>
<div class="top"><div class="in"><div class="brand">Jewelry Remate MX
<small>Tablas de precios por orden de compra</small></div></div></div>
<div class="wrap viz">

<div class="intro">
<p><b>Qué es esto:</b> el costo real de cada producto puesto en Hermosillo, y a cuánto se está
vendiendo hoy en la tienda. El <b>PRECIO ACTUAL</b> se jala solo de Shopify, así que nunca se queda viejo.</p>
<p><b>Cómo se calcula el costo:</b> costo del producto + su parte del envío + 3% de comisión de Alibaba,
convertido a pesos al tipo de cambio <b>20</b>, más su parte del Shop and Cross (la aduana).
El envío y la aduana se reparten <b>por valor</b>: lo que cuesta más carga más. <b>Sin descuentos</b>,
para que el costo sea siempre comparable entre órdenes.</p>
<p><b>El color del precio</b> te dice si se está vendiendo sano respecto a lo que costó.</p>
<div class="leyenda">
  <span><i style="background:var(--a-bg);color:var(--a)">rojo</i> menos de 2.5× el costo</span>
  <span><i style="background:var(--warn-bg);color:var(--warn)">ámbar</i> entre 2.5× y 3×</span>
  <span><i style="background:var(--gray-bg)">gris</i> entre 3× y 3.5×</span>
  <span><i style="background:var(--ok-bg);color:var(--ok)">verde</i> 3.5× o más</span>
</div>
</div>

<div class="controls">
  <input type="search" id="q" placeholder="Buscar producto o SKU en todas las órdenes…">
</div>

<div class="ptabs">__BOTONES__</div>
__SECCIONES__

<div class="barra" id="barra"><div class="barrain">
  <b id="bnum">0 precios pendientes</b>
  <span class="sec2">Se guardan en este navegador. Dile a Claude «aplica los precios» y los manda a Shopify.</span>
  <button id="bver">Ver lista</button>
  <button id="bcopy">📋 Copiar</button>
  <button class="gris" id="bdesc">Descartar</button>
</div><pre class="lista" id="blista"></pre></div>

<div class="foot">Datos al __CORTE__ · Precios de venta tomados de Shopify ·
Shop and Cross tomado del Informe de Inversión 2026</div>
</div>
<script src="exceljs.min.js"></script>
<script>var ORD=__DATOS__;</script>
<script>
var q=document.getElementById('q');
q.oninput=function(){
  var t=q.value.trim().toUpperCase();
  document.querySelectorAll('tr[data-b]').forEach(function(tr){
    tr.style.display=(!t||tr.dataset.b.indexOf(t)>=0)?'':'none';});
  document.querySelectorAll('.prov').forEach(function(p){
    p.classList.toggle('on', !t ? p.dataset.p===document.querySelector('.ptab.on').dataset.p : true);});
  document.querySelectorAll('.orden').forEach(function(s){
    var vis=[].some.call(s.querySelectorAll('tr[data-b]'),function(tr){return tr.style.display!=='none'});
    s.style.display=(!t||vis)?'':'none';
    if(t&&vis)s.classList.remove('cerrada');});
};

// ── PRECIO EDITABLE (Eduardo, 21 ago 2026) ──
// Quien revisa calidad escribe el precio aqui mismo. Se guarda en este navegador y
// queda marcado como PENDIENTE hasta que Claude lo mande a Shopify.
var PKEY='precios_pend_v1';
var pend={}; try{pend=JSON.parse(localStorage.getItem(PKEY))||{}}catch(e){}
var aplicados=0;   // cuantos pendientes resultaron ya aplicados en Shopify
function fmt(n){return n.toLocaleString('en-US',{minimumFractionDigits:0,maximumFractionDigits:0})}
function num(x){return parseFloat(String(x).replace(/[^0-9.]/g,''))||0}
function pinta(td){
  var sku=td.dataset.sku, M=parseFloat(td.dataset.m)||0;
  var inp=td.querySelector('.pin'); if(!inp)return;
  var v=num(inp.value);
  td.classList.remove('critico','bajo','ok','bueno','pend');
  // pendiente solo si difiere del precio que ya trae Shopify (comparado como numero)
  if(pend[sku]!=null&&pend[sku]!==num(td.dataset.orig))td.classList.add('pend');
  if(!v||!M)return;
  var r=v/M;
  td.classList.add(r<2.5?'critico':(r<3?'bajo':(r<3.5?'ok':'bueno')));
  td.title='Vende a '+r.toFixed(1)+'× el costo'+(td.classList.contains('pend')?' · pendiente de aplicar':'');
}
function barra(){
  var n=Object.keys(pend).length, b=document.getElementById('barra');
  b.classList.toggle('on',n>0);
  document.getElementById('bnum').textContent=n+(n===1?' precio pendiente':' precios pendientes');
}
document.querySelectorAll('td.pact[data-sku]').forEach(function(td){
  var inp=td.querySelector('.pin'); if(!inp)return;
  td.dataset.orig=inp.value;
  // Producto que todavia no existe en Shopify: se marca mientras no tenga precio capturado.
  var sku=td.dataset.sku;
  // Si el precio pendiente ya es el que trae Shopify, es que YA SE APLICO: se limpia solo.
  if(pend[sku]!=null&&pend[sku]===num(td.dataset.orig)){delete pend[sku];aplicados++}
  if(pend[sku]!=null)inp.value=fmt(pend[sku]);
  if(inp.classList.contains('nuevo'))td.classList.toggle('sinprecio',!num(inp.value));
  pinta(td);
  inp.onfocus=function(){inp.select()};
  inp.oninput=function(){
    var v=num(inp.value), orig=num(td.dataset.orig);
    if(inp.classList.contains('nuevo'))td.classList.toggle('sinprecio',!v);
    if(!v||v===orig){delete pend[sku]}else{pend[sku]=v}
    localStorage.setItem(PKEY,JSON.stringify(pend));
    pinta(td); barra();
  };
  inp.onblur=function(){var v=num(inp.value); if(v)inp.value=fmt(v); pinta(td)};
  inp.onkeydown=function(e){if(e.key==='Enter')inp.blur()};
});
function textoLista(){
  var L=[];
  document.querySelectorAll('td.pact.pend[data-sku]').forEach(function(td){
    var tr=td.closest('tr'), sec=td.closest('.orden');
    var nom=tr.children[2].textContent.trim(), va=tr.children[3].textContent.trim();
    L.push(td.dataset.sku+'  '+fmt(pend[td.dataset.sku])+'   '+nom+(va?' · '+va:'')+
           '   ['+(sec?sec.id:'')+']');
  });
  return L.join('\n');
}
document.getElementById('bver').onclick=function(){
  var l=document.getElementById('blista');
  l.textContent=textoLista(); l.classList.toggle('on');
  this.textContent=l.classList.contains('on')?'Ocultar lista':'Ver lista';
};
document.getElementById('bcopy').onclick=function(){
  var b=this, t=textoLista();
  navigator.clipboard.writeText(t).then(function(){
    b.textContent='✓ Copiado'; setTimeout(function(){b.textContent='📋 Copiar'},1600);
  },function(){ b.textContent='No se pudo'; });
};
document.getElementById('bdesc').onclick=function(){
  if(!confirm('Vas a descartar '+Object.keys(pend).length+' precios pendientes. ¿Seguro?'))return;
  pend={}; localStorage.removeItem(PKEY);
  document.querySelectorAll('td.pact[data-sku]').forEach(function(td){
    var inp=td.querySelector('.pin'); if(inp)inp.value=td.dataset.orig; pinta(td)});
  document.getElementById('blista').classList.remove('on'); barra();
};
if(aplicados){
  localStorage.setItem(PKEY,JSON.stringify(pend));   // sin esto se quedarian guardados de a gratis
  var av=document.createElement('div');
  av.className='aplicado';
  av.innerHTML='\u2705 <b>'+aplicados+'</b> precio'+(aplicados>1?'s':'')+
    ' que estaban pendientes ya se aplicaron en Shopify. Se quitaron de la lista solos.';
  var w=document.querySelector('.wrap'), pt=document.querySelector('.ptabs');
  if(w&&pt)w.insertBefore(av,pt);
  setTimeout(function(){av.style.opacity='0'},9000);
}
barra();

document.querySelectorAll('.ptab').forEach(function(b){
  b.onclick=function(){
    document.querySelectorAll('.ptab').forEach(function(x){x.classList.toggle('on',x===b)});
    document.querySelectorAll('.prov').forEach(function(s){
      s.classList.toggle('on',s.dataset.p===b.dataset.p)});
    if(q.value)q.oninput();
  };
});
document.querySelectorAll('.toggle').forEach(function(b){
  b.onclick=function(){
    var s=b.closest('.orden');
    s.classList.toggle('cerrada');
    b.textContent=s.classList.contains('cerrada')?'Ver tabla':'Ocultar tabla';
  };
});
// Excel CON FORMULAS, igual que la hoja del Drive: los datos van arriba en el
// encabezado y cada columna se calcula jalando de ahi. Si Eduardo cambia el
// costo, el shipping o el Shop and Cross, TODA la tabla se recalcula sola.
document.querySelectorAll('.desc').forEach(function(b){
  b.onclick=async function(){
    var nom=b.dataset.csv, d=ORD[nom];
    if(!d){alert('No encontr\u00e9 los datos de esa orden.');return}
    var txt=b.textContent; b.disabled=true; b.textContent='Generando\u2026';
    try{
      var wb=new ExcelJS.Workbook(), ws=wb.addWorksheet(nom);
      var n=d.lineas.length, ini=8, fin=ini+n-1;   // los productos van de la fila 8 en adelante

      ws.columns=[{width:20},{width:44},{width:20},{width:9},{width:13},{width:13},
                  {width:15},{width:13},{width:16},{width:16},{width:14},{width:16},
                  {width:17},{width:12},{width:12},{width:12},{width:13},{width:13}];

      // \u2500\u2500 encabezado: aqui viven los datos de los que jala todo lo demas
      ws.getCell('A2').value='JEWELRY REMATE';
      ws.getCell('E2').value='COSTO ORDEN';        ws.getCell('F2').value=d.costo;
      ws.getCell('G2').value='% DE SHIPPING';      ws.getCell('H2').value={formula:'F3/F2'};
      ws.getCell('I2').value='% ALIBABA';          ws.getCell('J2').value=d.alibaba;
      ws.getCell('A3').value='TABLA DE PRECIOS AL CLIENTE';
      ws.getCell('E3').value='SHIPPING';           ws.getCell('F3').value=d.shipping;
      ws.getCell('G3').value='COSTO TOTAL DE ORDEN'; ws.getCell('H3').value={formula:'F2+F3+H6'};
      ws.getCell('I3').value='% SHOP AND CROSS';   ws.getCell('J3').value={formula:'L6/J6'};
      ws.getCell('A4').value='DESGLOSE DE COSTO INCLUYENDO SHIPPING Y PAGO DE ALIBABA';
      ws.getCell('G4').value='DOLLAR';             ws.getCell('H4').value=d.tc;
      ws.getCell('A6').value='ORDEN DE COMPRA:';   ws.getCell('B6').value=nom;
      ['D','E','F','G','H','I','J','K','M'].forEach(function(c){
        ws.getCell(c+'6').value={formula:'SUM('+c+ini+':'+c+fin+')'};});
      ws.getCell('L6').value=d.sc;                 // el Shop and Cross de la orden
      [ 'H2','J2','J3' ].forEach(function(c){ws.getCell(c).numFmt='0.00%'});
      ['A2','A3','A4','A6','E2','E3','G2','G3','G4','I2','I3'].forEach(function(c){
        ws.getCell(c).font={bold:true}});

      ws.getRow(7).values=['SKU','PRODUCTO','VARIANTE','CANTIDAD','COSTO UNITARIO (US)',
        'COSTO TOTAL (US)','COSTO CON ENVIO X TOTAL PCS (US)','% ALIBABA (US)',
        'COSTO DE COMPRA ALIBABA (US)','COSTO DE COMPRA (MXN) TC=20','% SOBRE EL COSTO TOTAL (US)',
        'SHOP AND CROSS (MXN)','COSTO UNIT TOTAL (MXN)','ROAS 3','ROAS 3.5','ROAS 4',
        'PRECIO ACTUAL','PRECIO ANTIGUO'];
      ws.getRow(7).font={bold:true};
      ws.getRow(7).alignment={wrapText:true,vertical:'middle'};
      ws.getRow(7).height=34;

      // \u2500\u2500 productos: puros datos base + formulas, iguales a las del Drive
      d.lineas.forEach(function(l,i){
        var r=ini+i, row=ws.getRow(r);
        row.getCell(1).value=l.sku||'';
        row.getCell(2).value=l.prod||'';
        row.getCell(3).value=l.var||'';
        row.getCell(4).value=l.cant;
        row.getCell(5).value=l.cu;
        row.getCell(6).value={formula:'E'+r+'*D'+r};
        row.getCell(7).value={formula:'F'+r+'*$H$2'};
        row.getCell(8).value={formula:'(F'+r+'+G'+r+')*$J$2'};
        row.getCell(9).value={formula:'SUM(F'+r+':H'+r+')'};
        row.getCell(10).value={formula:'I'+r+'*$H$4'};
        row.getCell(11).value={formula:'I'+r+'/$I$6'};
        row.getCell(12).value={formula:'$L$6*K'+r};
        row.getCell(13).value={formula:'(J'+r+'+L'+r+')/D'+r};
        row.getCell(14).value={formula:'M'+r+'*3'};
        row.getCell(15).value={formula:'M'+r+'*3.5'};
        row.getCell(16).value={formula:'M'+r+'*4'};
        if(l.pact!=null)row.getCell(17).value=l.pact;
        if(l.pant!=null)row.getCell(18).value=l.pant;
        [5,6,7,8,9,10,12,13,14,15,16,17,18].forEach(function(c){
          row.getCell(c).numFmt='#,##0.00'});
        row.getCell(11).numFmt='0.0000%';
      });
      ws.views=[{state:'frozen',ySplit:7}];

      var buf=await wb.xlsx.writeBuffer();
      var a=document.createElement('a');
      a.href=URL.createObjectURL(new Blob([buf],
        {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
      a.download='TABLA PRECIOS '+nom+'.xlsx';
      a.click();
    }catch(e){alert('No se pudo generar el Excel: '+e.message);}
    b.disabled=false; b.textContent=txt;
  };
});
document.querySelectorAll('.ocard').forEach(function(b){
  b.onclick=function(){var el=document.getElementById(b.dataset.ir);
    if(el)el.scrollIntoView({behavior:'smooth',block:'start'});};});

// ── DEL TABLERO A LA ORDEN (Reyna, 5 oct 2026) ──
// En "se venden por debajo de 3x" y en "parado en bodega", picar el producto
// lleva a la orden donde se pidio, abre la tabla y deja el renglon marcado,
// para ver de donde salio ese precio sin andarlo buscando.
document.querySelectorAll('a.irprod').forEach(function(a){
  a.onclick=function(ev){
    ev.preventDefault();
    var tab=document.querySelector('.ptab[data-p="'+a.dataset.prov+'"]');
    if(tab)tab.click();
    var sec=document.getElementById(a.dataset.ir);
    if(!sec){alert('Esa orden todavía no tiene tabla de precios en esta página.');return}
    sec.classList.remove('cerrada');
    var bt=sec.querySelector('.toggle'); if(bt)bt.textContent='Ocultar tabla';
    var td=null, sku=a.dataset.sku;
    if(sku)sec.querySelectorAll('td.pact[data-sku]').forEach(function(x){
      if(!td&&x.dataset.sku===sku)td=x;});
    var fila=td?td.closest('tr'):null;
    (fila||sec).scrollIntoView({behavior:'smooth',block:fila?'center':'start'});
    document.querySelectorAll('tr.resalta').forEach(function(t){t.classList.remove('resalta')});
    if(fila){fila.classList.add('resalta');
      setTimeout(function(){fila.classList.remove('resalta')},4000);}
  };});
</script></body></html>"""
HTML = (HTML.replace('__BOTONES__', ''.join(botones))
            .replace('__SECCIONES__', ''.join(secciones))
            .replace('__CORTE__', CORTE)
            .replace('__DATOS__', json.dumps(datos_js, ensure_ascii=False, separators=(',', ':'))))

open(os.path.join(REPO, 'precios.html'), 'w', encoding='utf-8').write(HTML)
print('precios.html: %d bytes | %d ordenes | %d lineas | invertido $%s MXN'
      % (len(HTML), len(ordenes), sum(len(o['lineas']) for o in ordenes.values()),
         money(tot_inv_mxn, 2)))
