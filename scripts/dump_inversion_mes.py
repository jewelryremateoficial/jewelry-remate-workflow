#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Saca la inversion MES POR MES del INFORME DE INVERSION 2026 del Drive.

Por que existe: el panel "Inversión 2026" de precios.html sacaba el mes del
NOMBRE de la orden, no de la fecha del pago. Por eso septiembre 2026 aparecia
con $753 mil cuando de verdad fueron mas de $900 mil: NANCY220826 y ZOEY260826
se siguieron pagando en septiembre, y HAIFENG290926 ya cayo en octubre.
(Reyna, 5 oct 2026.)

Como se usa:
  1. Leer el archivo del Drive "INFORME DE INVERSION 2026"
     (id 11prWt5jLEhzro3hS1xD9-erN3I5LC9KEJl_cTpi8hU0) con get_file_metadata
     y snippetVerbosity MAX_ALLOWED, y guardar el contentSnippet en un .txt.
  2. python3 scripts/dump_inversion_mes.py <ese .txt>
  3. python3 scripts/build_precios.py

Escribe datos/precios/inversion_mes.json. Si ese archivo no existe,
build_precios.py se cae al mes del nombre de la orden, como antes.
"""
import re, sys, json, os, collections, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(REPO, 'datos', 'precios', 'inversion_mes.json')
ENTRADA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, '.scratch', 'informe.txt')

NM = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7,
      'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}
# "abril2026" va sin espacio en la hoja, de ahi el \s*
MES = re.compile(r'^(%s)\s*(\d{4}),' % '|'.join(NM))
# El de pesos va PRIMERO y con los miles bien delimitados: si no, un "$7,508,94"
# (coma en vez de punto, error de dedo en la hoja) se come el monto que le sigue.
MONTO = re.compile(r'\$\d{1,3}(?:,\d{3})*[.,]\d{2}|\d{1,3}(?:,\d{3})*\.\d{2}USD')
# error de dedo en la hoja SHOP AND CROSS: la orden es HAIFENG120826
TYPO = {'HAIFENG120827': 'HAIFENG120826'}


def num(x):
    x = x.replace('$', '').replace('USD', '')
    if re.search(r',\d{2}$', x) and '.' not in x:      # $7,508,94 -> 7508.94
        x = x[::-1].replace(',', '.', 1)[::-1]
    return float(x.replace(',', ''))


def main():
    s = open(ENTRADA).read()

    def hoja(n):
        m = re.search(r'^# ' + re.escape(n) + r'\n\n```(.*?)```', s, re.S | re.M)
        if not m:
            sys.exit('no encuentro la hoja %r en %s' % (n, ENTRADA))
        return m.group(1)

    # Alibaba: exacto, enlace por enlace. Los 6 primeros montos de cada renglon son
    # INV USD, INV MXN, 3% USD, 3% MXN, TOTAL X ENLACE USD, TOTAL X ENLACE MXN.
    ali = collections.defaultdict(lambda: {'mxn': 0.0, 'usd': 0.0, 'enlaces': 0, 'ord': set()})
    pend = []
    for ln in hoja('INVERSION PROVEEDORES').split('\n'):
        m = MES.match(ln)
        if not m:
            continue
        mo = MONTO.findall(ln)
        if len(mo) < 6:                       # renglon capturado pero todavia sin pagar
            pend.append(ln.split(',')[2])
            continue
        k = '%s-%02d' % (m.group(2), NM[m.group(1)])
        ali[k]['mxn'] += num(mo[5]); ali[k]['usd'] += num(mo[4])
        ali[k]['enlaces'] += 1; ali[k]['ord'].add(ln.split(',')[1].strip())

    # Aduana: en esa hoja no se puede leer guia por guia sin ambiguedad (las celdas
    # combinadas repiten el total de la orden), asi que el total por orden -- que si
    # es exacto y vive en informe_2026.json -- se reparte entre los meses en que la
    # hoja registra esa orden. El gran total queda intacto.
    om = collections.defaultdict(set)
    for ln in hoja('SHOP AND CROSS 2026').split('\n'):
        m = MES.match(ln)
        if m:
            o = ln.split(',')[1].strip()
            om[TYPO.get(o, o)].add('%s-%02d' % (m.group(2), NM[m.group(1)]))
    sc = json.load(open(os.path.join(REPO, 'datos', 'precios', 'informe_2026.json')))['sc']
    adu = collections.defaultdict(float); sinmes = []
    for o, v in sc.items():
        ms = sorted(om.get(TYPO.get(o, o)) or [])
        if not ms:
            sinmes.append(o); continue
        for k in ms:
            adu[k] += v / len(ms)

    meses = sorted(set(ali) | set(adu))
    out = {
        'generado': datetime.date.today().isoformat(),
        'fuente': 'INFORME DE INVERSION 2026 — hojas INVERSION PROVEEDORES y SHOP AND CROSS 2026',
        'nota': 'El mes es el mes en que se PAGO, no el del nombre de la orden. Alibaba sale '
                'enlace por enlace. La aduana de cada orden se reparte entre los meses en que '
                'la hoja la registra.',
        'mes': {k: {'ali': round(ali[k]['mxn'], 2), 'adu': round(adu.get(k, 0.0), 2),
                    'usd': round(ali[k]['usd'], 2), 'enlaces': ali[k]['enlaces'],
                    'ordenes': len(ali[k]['ord'])} for k in meses},
    }
    json.dump(out, open(SALIDA, 'w'), ensure_ascii=False, indent=1)

    A = sum(d['ali'] for d in out['mes'].values())
    D = sum(d['adu'] for d in out['mes'].values())
    print('inversion_mes.json: %d meses | Alibaba $%s | aduana $%s | total $%s'
          % (len(meses), '{:,.2f}'.format(A), '{:,.2f}'.format(D), '{:,.2f}'.format(A + D)))
    for k in meses:
        d = out['mes'][k]
        print('  %s  $%14s  (%d enlaces, %d ordenes)'
              % (k, '{:,.2f}'.format(d['ali'] + d['adu']), d['enlaces'], d['ordenes']))
    if pend:
        print('  renglones capturados sin pagar todavia:', ', '.join(pend))
    if sinmes:
        print('  ordenes con aduana pero sin mes en la hoja:', ', '.join(sinmes))


if __name__ == '__main__':
    main()
