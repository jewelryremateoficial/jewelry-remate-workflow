#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF de los productos parados de un proveedor, para pasarselo a marketing.

Reyna, 5 oct 2026: "necesito un documento en PDF donde salgan esos productos
que dices que estan parados, para darselos a marketing y haga algo con ellos".

Lleva foto, porque marketing necesita ver que producto es, y lleva el costo y
el precio de hoy para que sepan hasta donde pueden bajarle sin perder: la
columna "piso 2x" es el precio mas bajo al que todavia se duplica el costo.

Mismo criterio que scripts/doc_parado.py: el lote ya llego y el producto lleva
60 dias o mas sin vender una sola pieza.

  python3 scripts/pdf_parado.py ZOEY "CYNTHIA CAO" HAIFENG "NANCY VIP" "DINA DU"

Necesita:
  .scratch/img_sku.json   {sku: url de la foto}  (bulk de Shopify)
  .scratch/pimg/          las fotos ya bajadas (las baja este script)
Convierte con Google Chrome en modo headless.
"""
import json, os, sys, subprocess, hashlib, html as H

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = os.path.join(REPO, '.scratch')
OUT = os.path.join(REPO, 'informes')
IMGDIR = os.path.join(SCR, 'pimg')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
A = json.load(open(os.path.join(REPO, 'datos', 'precios', 'analisis.json')))
IMG = json.load(open(os.path.join(SCR, 'img_sku.json'))) if \
    os.path.isfile(os.path.join(SCR, 'img_sku.json')) else {}
PRECIO = json.load(open(os.path.join(REPO, 'datos', 'precios', 'precios_shopify.json')))


def m(x):
    return '{:,.0f}'.format(x)


def local(sku):
    """Ruta local de la foto; la baja chica si todavia no esta."""
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


def filas_de(pr):
    d = A['prov'][pr]
    f = [dict(e, orden=o['orden'], fecha=o['fecha'])
         for o in d['ordenes'] for e in o['est']]
    return d, f


def tabla(filas, con_ultima):
    th = ('<tr><th class="f">Foto</th><th>Producto</th><th>Orden</th>'
          '<th class="n">Quedan</th><th class="n">Precio hoy</th>'
          '<th class="n">Costo</th><th class="n">Piso 2×</th>'
          + ('<th>Última venta</th>' if con_ultima else '')
          + '<th class="n">Sin vender</th><th class="n">Detenido</th></tr>')
    tr = []
    for x in filas:
        im = local(x['sku'])
        foto = ('<img src="%s">' % im) if im else '<span class="sf">sin foto</span>'
        p = PRECIO.get(x['sku'])
        piso = x['M'] * 2
        tr.append(
            '<tr><td class="f">%s</td>'
            '<td><b>%s</b>%s<span class="sku">%s</span></td>'
            '<td class="o">%s</td><td class="n">%d<span class="de"> de %d</span></td>'
            '<td class="n">%s</td><td class="n">$%s</td><td class="n piso">$%s</td>'
            '%s<td class="n dv">%s</td><td class="n det">$%s</td></tr>'
            % (foto, H.escape(x['prod']),
               ('<i>%s</i>' % H.escape(x['var'])) if x['var'] else '',
               H.escape(x['sku']), x['orden'], x['rest'], x['q'],
               ('$' + m(p)) if p else '—', m(x['M']), m(piso),
               ('<td class="o">%s</td>' % x['uv']) if con_ultima else '',
               ('%d d' % x['sv']), m(x['mxn'])))
    return '<table>%s%s</table>' % (th, ''.join(tr))


CSS = """
@page{size:letter landscape;margin:11mm 9mm 13mm}
*{box-sizing:border-box}
body{font:10px/1.35 -apple-system,"Helvetica Neue",Arial,sans-serif;color:#15181f;margin:0}
h1{font-size:19px;margin:0 0 2px}
h2{font-size:13px;margin:16px 0 6px;padding-bottom:4px;border-bottom:2px solid #15181f;
   page-break-after:avoid}
.sub{color:#6b7280;font-size:10px;margin:0 0 10px}
.caja{border:1px solid #d7dae0;border-radius:6px;padding:8px 10px;margin:0 0 12px;
  background:#f7f8fa;font-size:9.5px;line-height:1.5}
.caja b{color:#15181f}
.res{display:flex;gap:9px;margin:0 0 12px}
.res div{flex:1;border:1px solid #d7dae0;border-radius:6px;padding:7px 9px}
.res span{display:block;color:#6b7280;font-size:8.5px;text-transform:uppercase;
  letter-spacing:.05em}
.res b{font-size:16px}
table{width:100%;border-collapse:collapse;font-size:9px}
th{background:#15181f;color:#fff;text-align:left;padding:5px 6px;font-size:8.5px;
   text-transform:uppercase;letter-spacing:.04em}
td{border-bottom:1px solid #e6e8ec;padding:4px 6px;vertical-align:middle}
tr{page-break-inside:avoid}
thead{display:table-header-group}
td.f,th.f{width:62px;text-align:center}
td.f img{width:54px;height:54px;object-fit:cover;border-radius:5px;border:1px solid #e6e8ec}
.n{width:74px}
.o{width:96px}
td.o+td.o,th:nth-child(8){width:78px}
.sf{color:#b9bec7;font-size:7.5px}
td b{font-size:9.5px}
td i{display:block;font-style:normal;color:#6b7280;font-size:8.5px}
.sku{display:block;color:#aeb4bf;font-size:7.5px;font-variant-numeric:tabular-nums}
.o{font-size:8.5px;color:#4b5563;white-space:nowrap}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.de{color:#9aa1ad;font-size:8px}
.piso{color:#047857;font-weight:700}
.dv{font-weight:700;color:#b42318}
.det{font-weight:700}
.pie{margin-top:14px;color:#9aa1ad;font-size:8px}
"""


def doc(pr):
    d, filas = filas_de(pr)
    nunca = sorted((x for x in filas if x['nunca']), key=lambda x: -x['dias'])
    tarde = sorted((x for x in filas if not x['nunca']), key=lambda x: -x['sv'])
    tot = sum(x['mxn'] for x in filas)
    return """<!doctype html><html lang="es"><meta charset="utf-8">
<title>Parado %s</title><style>%s</style>
<h1>%s — productos parados</h1>
<p class="sub">Corte al %s · para marketing</p>
<div class="caja"><b>Qué es esta lista.</b> Productos que ya llegaron a bodega y que
llevan <b>60 días o más sin vender una sola pieza</b>. Si alguna vez se vendieron, se
cuenta desde su última venta; si nunca se han vendido, desde el día que llegaron. Lo que
sobra de un producto que se sigue vendiendo no está aquí.<br>
<b>Piso 2×</b> es el precio más bajo al que todavía se duplica el costo: hasta ahí se le
puede bajar sin dejar de ganar. <b>Detenido</b> es el dinero parado en esas piezas.</div>
<div class="res">
<div><span>Productos parados</span><b>%d</b></div>
<div><span>Dinero detenido</span><b>$%s</b></div>
<div><span>Sin una sola venta</span><b>%d</b></div>
<div><span>Vendieron y ya no</span><b>%d</b></div>
</div>
<h2>Sin una sola venta — %d productos · $%s</h2>
%s
<h2>Vendieron, pero ya no — %d productos · $%s</h2>
%s
<p class="pie">Jewelry Remate MX · generado con scripts/pdf_parado.py</p>
</html>""" % (
        H.escape(pr), CSS, H.escape(pr), A['generado'],
        len(filas), m(tot), len(nunca), len(tarde),
        len(nunca), m(sum(x['mxn'] for x in nunca)), tabla(nunca, False),
        len(tarde), m(sum(x['mxn'] for x in tarde)), tabla(tarde, True))


if __name__ == '__main__':
    provs = sys.argv[1:]
    if not provs:
        sys.exit('dime los proveedores. Hay: %s' % ', '.join(sorted(A['prov'])))
    os.makedirs(OUT, exist_ok=True)
    for pr in provs:
        if pr not in A['prov']:
            print('  no existe %r, me lo salto' % pr); continue
        base = 'PARADO_' + pr.replace(' ', '_')
        htm = os.path.join(SCR, base + '.html')
        open(htm, 'w').write(doc(pr))
        pdf = os.path.join(OUT, base + '.pdf')
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        '--virtual-time-budget=25000', '--print-to-pdf=' + pdf,
                        'file://' + htm],
                       check=False, capture_output=True)
        kb = os.path.getsize(pdf) // 1024 if os.path.isfile(pdf) else 0
        n = len(filas_de(pr)[1])
        print('informes/%s.pdf  %d productos  %d KB' % (base, n, kb))
