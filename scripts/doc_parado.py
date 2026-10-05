#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Documento de lo que de verdad esta parado, proveedor por proveedor.

Nace de un reclamo con razon de Reyna (5 oct 2026): la pagina ponia el
BOLSO CC 22 SILVER como estancado y "nunca se ha vendido" cuando llevaba
10 piezas vendidas en el anio y la ultima hacia 15 dias. El error era que
"parado" se medía por DIAS DESDE QUE LLEGO LA CAJA y se marcaba sobre el
LOTE, no sobre el producto: el lote ZOEY100926 todavia no habia llegado,
asi que ninguna venta podia ser posterior a su llegada.

Lo que cuenta aqui como parado:
  1. el lote YA LLEGO (lo que viene en camino no esta parado), y
  2. el PRODUCTO no ha vendido ni una pieza en 60 dias o mas,
     contados desde su ultima venta real, no desde que llego la caja.

Lo que queda de un producto que se sigue vendiendo es inventario y no
aparece aqui.

  python3 scripts/doc_parado.py ZOEY
  python3 scripts/doc_parado.py            # todos los proveedores
"""
import json, os, sys, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = json.load(open(os.path.join(REPO, 'datos', 'precios', 'analisis.json')))


def money(x):
    return '{:,.0f}'.format(x)


def doc(pr):
    d = A['prov'].get(pr)
    if not d:
        sys.exit('no hay proveedor %r. Hay: %s' % (pr, ', '.join(sorted(A['prov']))))
    filas = [dict(e, orden=o['orden'], fecha=o['fecha'])
             for o in d['ordenes'] for e in o['est']]
    nunca = [f for f in filas if f['nunca']]
    tarde = sorted((f for f in filas if not f['nunca']), key=lambda f: -f['dsv'])
    L = []
    L.append('# %s — lo que de verdad está parado' % pr)
    L.append('')
    L.append('Corte al %s.' % A['generado'])
    L.append('')
    L.append('## En qué me baso')
    L.append('')
    L.append('Un producto entra aquí **solo si se cumplen las dos cosas**:')
    L.append('')
    L.append('1. **El lote ya llegó.** Lo que viene en camino no está parado.')
    L.append('2. **Lleva 60 días o más sin vender una sola pieza.** Si alguna vez vendió,')
    L.append('   se cuenta desde su última venta de verdad; si nunca ha vendido, desde el')
    L.append('   día que llegó. Así uno que llegó hace tres semanas no se cuenta como')
    L.append('   parado nomás por no haber vendido todavía.')
    L.append('')
    L.append('Si de un producto sobran piezas pero se sigue vendiendo, **no** es parado:')
    L.append('es inventario, y no aparece en esta lista.')
    L.append('')
    L.append('> Antes esto estaba mal medido. El "parado" se contaba por los días que')
    L.append('> llevaba la caja en bodega y la marca de "nunca se ha vendido" se ponía')
    L.append('> cuando la última venta era anterior a la llegada de **ese lote**. Por eso')
    L.append('> el BOLSO CC 22 SILVER salía como estancado y sin ventas, cuando lleva 10')
    L.append('> piezas vendidas en el año y la última fue el 20 de septiembre: el lote')
    L.append('> ZOEY100926 todavía no ha llegado, así que ninguna venta podía ser')
    L.append('> posterior. Ya quedó corregido.')
    L.append('')
    L.append('## Resumen')
    L.append('')
    L.append('| | Productos | Dinero detenido |')
    L.append('|---|---:|---:|')
    L.append('| **Sin una sola venta en el año** | %d | $%s |'
             % (len(nunca), money(sum(f['mxn'] for f in nunca))))
    L.append('| **Vendieron, pero ya no** | %d | $%s |'
             % (len(tarde), money(sum(f['mxn'] for f in tarde))))
    L.append('| **Total parado** | %d | $%s |'
             % (len(filas), money(sum(f['mxn'] for f in filas))))
    L.append('')
    L.append('Para comparar: %s tiene **%s piezas vendidas** por **$%s** de ingreso, con'
             ' un margen de **%.1f%%** y un múltiplo de **%.2f×**.'
             % (pr, money(d['q']), money(d['ing']), d['pct'], d['mult']))
    L.append('')
    L.append('## Por orden de compra')
    L.append('')
    L.append('| Orden | Fecha | Productos parados | Dinero detenido |')
    L.append('|---|---|---:|---:|')
    for o in d['ordenes']:
        if o['quietos']:
            L.append('| %s | %s | %d | $%s |'
                     % (o['orden'], o['fecha'], o['quietos'], money(o['quieto_mxn'])))
    L.append('')
    L.append('## Sin una sola venta en el año (%d)' % len(nunca))
    L.append('')
    L.append('Estos nunca se han vendido. Son los primeros para rebajar o rematar.')
    L.append('')
    L.append('| Producto | Variante | Orden | Quedan | De | Costo c/u | Detenido | Días en bodega |')
    L.append('|---|---|---|---:|---:|---:|---:|---:|')
    for f in sorted(nunca, key=lambda f: -f['dias']):
        L.append('| %s | %s | %s | %d | %d | $%s | $%s | %d |'
                 % (f['prod'], f['var'] or '—', f['orden'], f['rest'], f['q'],
                    money(f['M']), money(f['mxn']), f['dias']))
    L.append('')
    L.append('## Vendieron, pero ya no (%d)' % len(tarde))
    L.append('')
    L.append('Estos sí se vendieron alguna vez. La columna dice cuándo fue la última.')
    L.append('')
    L.append('| Producto | Variante | Orden | Quedan | De | Costo c/u | Detenido | Última venta | Sin vender |')
    L.append('|---|---|---|---:|---:|---:|---:|---|---:|')
    for f in tarde:
        L.append('| %s | %s | %s | %d | %d | $%s | $%s | %s | %d días |'
                 % (f['prod'], f['var'] or '—', f['orden'], f['rest'], f['q'],
                    money(f['M']), money(f['mxn']), f['uv'], f['dsv']))
    L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    provs = sys.argv[1:] or sorted(A['prov'])
    for pr in provs:
        if not A['prov'].get(pr, {}).get('ordenes'):
            continue
        nom = 'PARADO_%s.md' % pr.replace(' ', '_')
        ruta = os.path.join(REPO, 'informes', nom)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        open(ruta, 'w').write(doc(pr))
        print('escrito informes/%s' % nom)
