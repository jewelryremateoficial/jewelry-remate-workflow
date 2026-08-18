# Actualización diaria de ordenes.html — proceso fijo

REGLA CERO: NO cambiar diseño, lógica, secciones ni fórmulas de ordenes.html. Esta rutina SOLO
refresca datos de Shopify (ventas, stock, rebajas) y hace push. Las reglas fijas de Eduardo están
en la memoria (reglas-centro-ordenes) y en el encabezado de scripts/build_ordenes.py.

## Datos a refrescar (vía MCP de Shopify) → guardar en un directorio de trabajo (SCRATCH):

1. **Ventas 60 días** (2 consultas ShopifyQL, guardar el resultado JSON tal cual):
   - `FROM sales SHOW net_items_sold, gross_sales, discounts, net_sales GROUP BY product_variant_sku, product_title, product_variant_title WHERE product_vendor = 'HAIFENG' SINCE -60d UNTIL today ORDER BY net_items_sold DESC LIMIT 1000` → `sales_HAIFENG.json`
   - Igual pero `WHERE product_vendor != 'HAIFENG'` y con `product_vendor` en el GROUP BY → `sales_OTROS.json`
2. **Ventas 90 días**: mismas dos consultas con `SINCE -90d` → `sales90_HAIFENG.json`, `sales90_OTROS.json`
3. **Catálogo completo** (paginado de 250 en 250 hasta hasNextPage=false) → `vp_001.json`, `vp_002.json`, …:
   `query($after:String){ productVariants(first:250, after:$after){ pageInfo{hasNextPage endCursor} nodes{ id title sku price compareAtPrice inventoryQuantity product{ id title vendor status featuredImage{ url(transform:{maxWidth:120,maxHeight:120}) } } } } }`
   (si la última página llega inline, repetirla agregando campos barcode/createdAt/updatedAt/handle para forzar el guardado a archivo)
4. **Línea por línea 60d para rebaja** (bulk): mutación `bulkOperationRunQuery` con
   `{ orders(query:"created_at:>=<HOY-60d>") { edges { node { id createdAt lineItems { edges { node { sku quantity originalUnitPriceSet{shopMoney{amount}} discountedUnitPriceSet{shopMoney{amount}} } } } } } } }`
   → esperar COMPLETED, descargar el url con curl → `lineitems60.jsonl`
5. **Productos nuevos (edad)**: `products(query:"created_at:>=<HOY-90d>")` con id/createdAt/publishedAt/status → `newprods_1.json` (y _2 si hay más páginas; los ACTIVE son los importantes)
6. **Costos**: correr `scripts/dump_costs.py` (lee los Excel de ~/Downloads/TABLAS DE PRECIOS y el historial). Si los Excel no están disponibles, usar el `scripts/costs.json` guardado (los costos no cambian a diario). Igual `transit_base.json`.

## Generar y publicar:

7. Ajustar en `scripts/build_ordenes.py`: SCRATCH (directorio con los archivos), CORTE y HOY (fecha del día).
8. `python3 scripts/build_ordenes.py` → escribe `ordenes.html` en la raíz del repo.
9. Verificar que el HTML generado pese ~1.2 MB y abra sin errores.
10. `git add ordenes.html && git commit -m "Actualización diaria de datos <fecha>" && git push origin main`

Notas: el vendor `M0LLY` se normaliza a MOLLY. COCO ZHANG no es proveedor activo. Las órdenes en
camino que Eduardo sube viven en su navegador (localStorage) — no se tocan con la actualización.
