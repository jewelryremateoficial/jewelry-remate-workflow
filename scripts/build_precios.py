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

ordenes = json.load(open(os.path.join(DATOS, 'zoey_ordenes.json')))
inversion = json.load(open(os.path.join(DATOS, 'zoey_inversion.json')))


def calcula(o):
    """Aplica la formula de Eduardo a una orden completa."""
    costo, ship, sc = o['costo'], o['shipping'], o['sc']
    pct_ship = ship / costo if costo else 0
    filas = []
    for l in o['lineas']:
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


bloques, tarjetas = [], []
tot_inv_mxn = 0.0

for nombre in sorted(ordenes, key=lambda k: (k[-2:], k[-4:-2])):
    o = ordenes[nombre]
    filas, tot_I = calcula(o)
    inv = inversion.get(nombre, {})
    inv_mxn = inv.get('total_mxn')
    if inv_mxn:
        tot_inv_mxn += inv_mxn

    pzs = sum(f['cant'] for f in filas)
    costo_total_mxn = sum(f['J'] for f in filas) + o['sc']
    sin_sku = sum(1 for f in filas if not f['en_shopify'])

    tarjetas.append(
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
            '<td class="n pact %s" title="%s">%s</td>'
            '<td class="n">%s</td></tr>'
            % (html.escape((f['prod'] + ' ' + f['sku'] + ' ' + f['var']).upper()),
               i, html.escape(f['sku']) or '—', html.escape(f['prod']), html.escape(f['var']),
               f['cant'], money(f['cu']), money(f['F']), money(f['G']), money(f['H']),
               money(f['I']), money(f['J']), '%.4f%%' % (f['K'] * 100), money(f['L']),
               money(f['M']),
               money(f['M'] * ROAS[0]), money(f['M'] * ROAS[1]), money(f['M'] * ROAS[2]),
               cls, html.escape(tip),
               money(f['pact']) if f['pact'] else ('sin SKU' if not f['sku'] else 'no está'),
               money(f['pant'])))

    aviso = ''
    if not o['sc']:
        aviso = ('<div class="aviso">⚠️ Esta orden todavía no tiene Shop and Cross pagado. '
                 'El costo por pieza está <b>incompleto</b> — le falta la aduana.</div>')
    elif sin_sku:
        aviso = ('<div class="aviso leve">%d producto%s de esta orden ya no está%s en Shopify, '
                 'así que no tienen precio de venta que mostrar.</div>'
                 % (sin_sku, 's' if sin_sku > 1 else '', 'n' if sin_sku > 1 else ''))

    bloques.append("""
<section class="orden" id="%s">
  <h2>%s</h2>
  <div class="resumen">
    <div class="dato"><span>Costo de la orden</span><b>$%s <i>US</i></b></div>
    <div class="dato"><span>Shipping</span><b>$%s <i>US</i></b><i class="sub">%.2f%% del costo</i></div>
    <div class="dato"><span>Comisión Alibaba</span><b>3%%</b></div>
    <div class="dato"><span>Shop and Cross</span><b>$%s <i>MXN</i></b></div>
    <div class="dato"><span>Tipo de cambio</span><b>%.0f</b></div>
    <div class="dato fuerte"><span>Costo total puesto</span><b>$%s <i>MXN</i></b></div>
    <div class="dato inv"><span>Lo que realmente se pagó</span><b>$%s <i>MXN</i></b><i class="sub">%s pagos a Alibaba</i></div>
  </div>
  %s
  <div class="tblwrap"><table>
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
  </table></div>
</section>""" % (nombre, nombre, money(o['costo']), money(o['shipping']),
                 o['shipping'] / o['costo'] * 100 if o['costo'] else 0,
                 money(o['sc']), TC, money(costo_total_mxn, 0),
                 money(inv_mxn, 0) if inv_mxn else '—', inv.get('pagos', '—'),
                 aviso, ''.join(trs)))

CORTE = '%d de %s de %d' % (HOY.day, _MESES_L[HOY.month - 1], HOY.year)

HTML = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jewelry Remate MX — Tablas de precios</title><style>
:root{--bg:#f6f7fb;--card:#fff;--ink:#15192b;--muted:#6b7285;--line:#e4e7f0;--a:#c0392b;--a-bg:#fdecea;
--ok:#1e7d46;--ok-bg:#e8f5ee;--warn:#b26a00;--warn-bg:#fdf3e0;--blue:#20508c;--blue-bg:#e8effa;
--gray-bg:#f0f1f5;--reb:#8a2be2;--reb-bg:#f3eafe}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
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
.cards{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));margin-bottom:20px}
.ocard{text-align:left;background:var(--card);border:1px solid var(--line);border-radius:11px;
padding:11px 13px;cursor:pointer;font:inherit;display:flex;flex-direction:column;gap:2px}
.ocard:hover{border-color:var(--blue)}
.ocard b{font-size:14px}.ocard span{font-size:12px;color:var(--muted)}
.ocard .mx{color:var(--ok);font-weight:600}
.orden{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:22px}
.resumen{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));margin-bottom:12px}
.dato{background:var(--gray-bg);border-radius:9px;padding:9px 11px;display:flex;flex-direction:column}
.dato span{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.dato b{font-size:16px;font-variant-numeric:tabular-nums}
.dato i{font-style:normal;font-size:11px;color:var(--muted)}
.dato b i{font-size:11px}
.dato.fuerte{background:var(--blue-bg)}.dato.fuerte b{color:var(--blue)}
.dato.inv{background:var(--ok-bg)}.dato.inv b{color:var(--ok)}
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
.leyenda{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:10px 0 0}
.leyenda i{font-style:normal;padding:2px 7px;border-radius:5px}
.foot{color:var(--muted);font-size:12px;padding:18px 0;text-align:center}
</style></head><body>
<div class="top"><div class="in"><div class="brand">Jewelry Remate MX
<small>Tablas de precios por orden de compra</small></div></div></div>
<div class="wrap">

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

<h2>ZOEY · __NORD__ órdenes · $__TOTINV__ MXN invertidos en 2026</h2>
<div class="cards">__TARJETAS__</div>

__BLOQUES__

<div class="foot">Datos al __CORTE__ · Precios de venta tomados de Shopify ·
Shop and Cross tomado del Informe de Inversión 2026</div>
</div>
<script>
var q=document.getElementById('q');
q.oninput=function(){
  var t=q.value.trim().toUpperCase();
  document.querySelectorAll('tr[data-b]').forEach(function(tr){
    tr.style.display=(!t||tr.dataset.b.indexOf(t)>=0)?'':'none';});
  document.querySelectorAll('.orden').forEach(function(s){
    var vis=[].some.call(s.querySelectorAll('tr[data-b]'),function(tr){return tr.style.display!=='none'});
    s.style.display=(!t||vis)?'':'none';});
};
document.querySelectorAll('.ocard').forEach(function(b){
  b.onclick=function(){var el=document.getElementById(b.dataset.ir);
    if(el)el.scrollIntoView({behavior:'smooth',block:'start'});};});
</script></body></html>"""
HTML = (HTML.replace('__NORD__', str(len(ordenes)))
            .replace('__TOTINV__', money(tot_inv_mxn, 0))
            .replace('__TARJETAS__', ''.join(tarjetas))
            .replace('__BLOQUES__', ''.join(bloques))
            .replace('__CORTE__', CORTE))

open(os.path.join(REPO, 'precios.html'), 'w', encoding='utf-8').write(HTML)
print('precios.html: %d bytes | %d ordenes | %d lineas | invertido $%s MXN'
      % (len(HTML), len(ordenes), sum(len(o['lineas']) for o in ordenes.values()),
         money(tot_inv_mxn, 2)))
