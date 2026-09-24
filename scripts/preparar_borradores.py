#!/usr/bin/env python3
"""Genera los lotes de productUpdate para preparar borradores nuevos en Shopify.

Uso:
  1. Crear productos.txt con una línea por producto: id_numerico|TÍTULO|proveedor|variantes
  2. python3 scripts/preparar_borradores.py productos.txt
  3. Ejecutar cada batchN.json con graphql_mutation del conector de Shopify.

Ver scripts/PREPARAR-BORRADORES.md para el proceso completo y las reglas fijas.
"""
import html, json, sys
from collections import Counter

# primera palabra del título -> (etiqueta de categoría, tipo de producto)
CAT = {
    'ARETES': ('aretes', 'Aretes y Arracadas'), 'ARRACADAS': ('arracadas', 'Aretes y Arracadas'),
    'ANILLO': ('anillo', 'Anillos'), 'PULSERA': ('pulsera', 'Brazaletes y Pulseras'),
    'BRAZALETE': ('brazalete', 'Brazaletes y Pulseras'), 'COLLAR': ('collares', 'Cadenas y Collares'),
    'BOLSO': ('bolso', 'Bolsos'), 'BOLSA': ('bolso', 'Bolsos'), 'MOCHILA': ('bolso', 'Bolsos'),
    'CARTERA': ('cartera', 'Carteras'), 'TARJETERO': ('Tarjetero', 'Tarjeteros'),
    'MONEDERO': ('Monedero', 'Monederos'),
    'SANDALIAS': ('Calzado', 'Calzado'), 'TENIS': ('Calzado', 'Calzado'), 'BALLERINAS': ('Calzado', 'Calzado'),
    'CAMISETA': ('ropa', 'Ropa'), 'BLUSA': ('ropa', 'Ropa'), 'ABRIGO': ('ropa', 'Ropa'),
    'RELOJ': ('reloj', 'Relojes'), 'LENTES': ('lentes', 'lentes de sol'),
}
BATCH = 20


def desc(title):
    t = html.escape(title)
    return (f"<p><strong>{t}</strong></p>"
            f"<p><strong>Material:</strong> POR COMPLETAR</p>"
            f"<p><strong>Medidas:</strong> POR COMPLETAR</p>"
            f"<p><strong>Cambios y Devoluciones Disponibles.</strong><br>"
            f"<strong>(Excepto en promociones y en casos donde se apliquen políticas específicas).</strong></p>")


def main(path):
    rows = [l.rstrip('\n').split('|') for l in open(path, encoding='utf-8') if l.strip()]
    ids = [r[0] for r in rows]
    dup = [i for i, c in Counter(ids).items() if c > 1]
    if dup:
        sys.exit(f"IDs repetidos en {path}: {dup}")
    updates, cats = [], Counter()
    for pid, title, *_ in rows:
        first = title.split()[0]
        if first not in CAT:
            sys.exit(f"Categoría desconocida para '{title}': agrega '{first}' a CAT")
        tag, ptype = CAT[first]
        tags = [tag, 'FALTA-INFO', 'New', 'new arrivals']
        if first == 'MOCHILA':
            tags.insert(1, 'mochila')
        cats[tag] += 1
        updates.append({'id': f'gid://shopify/Product/{pid}', 'tags': tags,
                        'productType': ptype, 'descriptionHtml': desc(title)})
    for n, start in enumerate(range(0, len(updates), BATCH), 1):
        b = updates[start:start + BATCH]
        q = "mutation(" + ", ".join(f"$p{i}: ProductUpdateInput!" for i in range(len(b))) + ") { " + " ".join(
            f"u{i}: productUpdate(product: $p{i}) {{ product {{ id title tags productType }} "
            f"userErrors {{ field message }} }}" for i in range(len(b))) + " }"
        json.dump({'query': q, 'variables': {f"p{i}": u for i, u in enumerate(b)}},
                  open(f'batch{n}.json', 'w', encoding='utf-8'), ensure_ascii=False)
        print(f"batch{n}.json: {len(b)} productos")
    print(f"{len(updates)} productos en total:", dict(cats))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'productos.txt')
