#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Un solo PDF, todos los proveedores: los que NO han vendido ni una pieza.

Reyna, 6 oct 2026: "dame los que realmente estan parados, sin una sola venta,
en un PDF donde salgan los diferentes proveedores, para poderlo imprimir todo
junto".

Y una advertencia suya que cambia el resultado: antes, cuando un producto tenia
la variante "Default Title" y se le agregaba otra variante, el SKU cambiaba y la
historia de venta se quedaba con el SKU viejo. Asi que un producto podia salir
como "nunca vendido" nomas porque le cambiaron el SKU.

Por eso aqui cada candidato se revisa dos veces contra datos/precios/
historial_skus.json (ventas desde 2025, bajadas de Shopify con el product id):

  1. ese SKU no vendio ni una pieza, en 2025 ni en 2026, y
  2. el PRODUCTO al que pertenece tampoco vendio con ningun otro SKU.

Si cualquiera de las dos falla, el producto NO entra: se va a la lista de
revisar, que se imprime al final con el motivo.

  python3 scripts/pdf_sin_ventas.py
"""
import json, os, sys, subprocess, hashlib, html as H

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = os.path.join(REPO, '.scratch')
OUT = os.path.join(REPO, 'informes')
IMGDIR = os.path.join(SCR, 'pimg')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
DATOS = os.path.join(REPO, 'datos', 'precios')

A = json.load(open(os.path.join(DATOS, 'analisis.json')))
HIST = json.load(open(os.path.join(DATOS, 'historial_skus.json')))
PRECIO = json.load(open(os.path.join(DATOS, 'precios_shopify.json')))
IMG = json.load(open(os.path.join(SCR, 'img_sku.json')))
PROVS = ['ZOEY', 'CYNTHIA CAO', 'HAIFENG', 'NANCY VIP', 'DINA DU']


def m(x):
    return '{:,.0f}'.format(x)


def local(sku):
    u = IMG.get(sku)
    if not u:
        return None
    fn = hashlib.md5(u.encode()).hexdigest() + '.jpg'
    ruta = os.path.join(IMGDIR, fn)
    if not os.path.isfile(ruta):
        os.makedirs(IMGDIR, exist_ok=True)
        sep = '&' if '?' in u else '?'
        subprocess.run(['curl', '-sL', '--max-time', '20', u + sep + 'width=220',
                        '-o', ruta], check=False)
    if not os.path.isfile(ruta) or os.path.getsize(ruta) < 500:
        return None
    return 'pimg/' + fn


def revisa(e):
    """None si de verdad no ha vendido nada; si no, el motivo de la duda."""
    h = HIST.get(e['sku'])
    if not h:
        return None
    if h['q']:
        return 'este SKU vendió %d pza en %s' % (h['q'], h['f'][:7])
    if h['qp']:
        return 'el producto vendió %d pza con otro SKU (última %s)' % (h['qp'], h['fp'][:7])
    return None


def junta():
    limpios, dudas = {}, []
    for pr in PROVS:
        L = []
        for o in A['prov'][pr]['ordenes']:
            for e in o['est']:
                if not e['nunca']:
                    continue
                x = dict(e, orden=o['orden'])
                mot = revisa(e)
                if mot:
                    dudas.append(dict(x, prov=pr, motivo=mot))
                else:
                    L.append(x)
        limpios[pr] = sorted(L, key=lambda x: -x['dias'])
    return limpios, dudas


def tabla(filas):
    th = ('<tr><th class="f">Foto</th><th>Producto</th><th>Orden</th>'
          '<th class="n">Piezas</th><th class="n">Precio hoy</th><th class="n">Costo</th>'
          '<th class="n">Piso 2×</th><th class="n">En bodega</th>'
          '<th class="n">Detenido</th></tr>')
    tr = []
    for x in filas:
        im = local(x['sku'])
        foto = ('<img src="%s">' % im) if im else '<span class="sf">sin foto</span>'
        p = PRECIO.get(x['sku'])
        tr.append(
            '<tr><td class="f">%s</td>'
            '<td><b>%s</b>%s<span class="sku">%s</span></td>'
            '<td class="o">%s</td><td class="n">%d</td>'
            '<td class="n">%s</td><td class="n">$%s</td><td class="n piso">$%s</td>'
            '<td class="n dv">%d d</td><td class="n det">$%s</td></tr>'
            % (foto, H.escape(x['prod']),
               ('<i>%s</i>' % H.escape(x['var'])) if x['var'] else '',
               H.escape(x['sku']), x['orden'], x['rest'],
               ('$' + m(p)) if p else '—', m(x['M']), m(x['M'] * 2),
               x['dias'], m(x['mxn'])))
    return '<table>%s%s</table>' % (th, ''.join(tr))


CSS = """
@page{size:letter landscape;margin:11mm 9mm 13mm}
*{box-sizing:border-box}
body{font:10px/1.35 -apple-system,"Helvetica Neue",Arial,sans-serif;color:#15181f;margin:0}
h1{font-size:21px;margin:0 0 2px}
h2{font-size:14px;margin:0 0 7px;padding:6px 9px;background:#15181f;color:#fff;
   border-radius:5px;page-break-after:avoid}
h2 span{float:right;font-weight:400;font-size:11px;opacity:.85}
.sub{color:#6b7280;font-size:10px;margin:0 0 11px}
.caja{border:1px solid #d7dae0;border-radius:6px;padding:9px 11px;margin:0 0 13px;
  background:#f7f8fa;font-size:9.5px;line-height:1.55}
.res{display:flex;gap:9px;margin:0 0 13px}
.res div{flex:1;border:1px solid #d7dae0;border-radius:6px;padding:7px 9px}
.res span{display:block;color:#6b7280;font-size:8.5px;text-transform:uppercase;
  letter-spacing:.05em}
.res b{font-size:17px}
table{width:100%;border-collapse:collapse;font-size:9px;margin:0 0 4px}
th{background:#3c4452;color:#fff;text-align:left;padding:5px 6px;font-size:8.5px;
   text-transform:uppercase;letter-spacing:.04em}
td{border-bottom:1px solid #e6e8ec;padding:4px 6px;vertical-align:middle}
tr{page-break-inside:avoid}
thead{display:table-header-group}
td.f,th.f{width:62px;text-align:center}
td.f img{width:54px;height:54px;object-fit:cover;border-radius:5px;border:1px solid #e6e8ec}
.sf{color:#b9bec7;font-size:7.5px}
td b{font-size:9.5px}
td i{display:block;font-style:normal;color:#6b7280;font-size:8.5px}
.sku{display:block;color:#aeb4bf;font-size:7.5px;font-variant-numeric:tabular-nums}
.o{font-size:8.5px;color:#4b5563;white-space:nowrap;width:96px}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;width:74px}
.piso{color:#047857;font-weight:700}
.dv{font-weight:700;color:#b42318}
.det{font-weight:700}
.prov{page-break-before:always}
.prov:first-of-type{page-break-before:avoid}
.pie{margin-top:12px;color:#9aa1ad;font-size:8px}
.mot{font-size:8.5px;color:#92400e}
table.duda th{background:#92400e}
"""


def doc():
    limpios, dudas = junta()
    tot = sum(len(v) for v in limpios.values())
    din = sum(x['mxn'] for v in limpios.values() for x in v)
    res = ''.join(
        '<div><span>%s</span><b>%d</b></div>' % (H.escape(p), len(limpios[p]))
        for p in PROVS)
    cuerpo = ''.join(
        '<div class="prov"><h2>%s<span>%d productos · $%s detenidos</span></h2>%s</div>'
        % (H.escape(p), len(limpios[p]), m(sum(x['mxn'] for x in limpios[p])),
           tabla(limpios[p]))
        for p in PROVS if limpios[p])
    dud = ''
    if dudas:
        dud = ('<div class="prov"><h2>Para revisar a mano<span>%d productos</span></h2>'
               '<div class="caja">Estos salían como "sin una sola venta", pero al buscar '
               'en el historial desde 2025 sí aparece movimiento: o el SKU vendió antes, '
               'o el producto vendió con otro SKU porque se le agregó una variante y el '
               'SKU cambió. <b>No están en las listas de arriba.</b></div>'
               '<table class="duda"><tr><th>Proveedor</th><th>Producto</th><th>Orden</th>'
               '<th class="n">Piezas</th><th>Qué se encontró</th></tr>%s</table></div>'
               % (len(dudas), ''.join(
                   '<tr><td class="o">%s</td><td><b>%s</b>%s<span class="sku">%s</span></td>'
                   '<td class="o">%s</td><td class="n">%d</td><td class="mot">%s</td></tr>'
                   % (H.escape(d['prov']), H.escape(d['prod']),
                      ('<i>%s</i>' % H.escape(d['var'])) if d['var'] else '',
                      H.escape(d['sku']), d['orden'], d['rest'], H.escape(d['motivo']))
                   for d in sorted(dudas, key=lambda d: (d['prov'], d['prod'])))))
    return """<!doctype html><html lang="es"><meta charset="utf-8">
<title>Sin una sola venta</title><style>%s</style>
<h1>Productos sin una sola venta</h1>
<p class="sub">Todos los proveedores · corte al %s · para marketing</p>
<div class="caja"><b>Qué es esta lista.</b> Productos que ya llegaron a bodega y que
<b>no han vendido ni una sola pieza</b>, ni este año ni el pasado.<br>
<b>Cómo se comprobó.</b> De cada uno se revisaron dos cosas en el historial de ventas
desde 2025: que el SKU no haya vendido nunca, <b>y</b> que el producto tampoco haya
vendido con otro SKU. Esto último importa porque antes, al agregarle una variante a un
producto que estaba en "Default Title", el SKU cambiaba y la historia de venta se
quedaba con el viejo. Los %d que no pasaron esa prueba salieron de la lista y van al
final, para revisarlos a mano.<br>
<b>Piso 2×</b> es el precio más bajo al que todavía se duplica el costo: hasta ahí se le
puede bajar sin dejar de ganar.</div>
<div class="res"><div><span>Total sin vender</span><b>%d</b></div>
<div><span>Dinero detenido</span><b>$%s</b></div>%s</div>
%s%s
<p class="pie">Jewelry Remate MX · generado con scripts/pdf_sin_ventas.py</p>
</html>""" % (CSS, A['generado'], len(dudas), tot, m(din), res, cuerpo, dud)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    htm = os.path.join(SCR, 'SIN_VENTAS.html')
    open(htm, 'w').write(doc())
    pdf = os.path.join(OUT, 'SIN_UNA_SOLA_VENTA.pdf')
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                    '--virtual-time-budget=40000', '--print-to-pdf=' + pdf, 'file://' + htm],
                   check=False, capture_output=True)
    limpios, dudas = junta()
    for p in PROVS:
        print('  %-13s %3d sin una sola venta' % (p, len(limpios[p])))
    print('  %-13s %3d (salieron: si tienen historia)' % ('para revisar', len(dudas)))
    print('informes/SIN_UNA_SOLA_VENTA.pdf  %d KB'
          % (os.path.getsize(pdf) // 1024 if os.path.isfile(pdf) else 0))
