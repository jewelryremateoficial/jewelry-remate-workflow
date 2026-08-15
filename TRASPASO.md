# TRASPASO COMPLETO — Centro de Órdenes de Compra · Jewelry Remate MX

> **Para el Claude de la otra compu:** Lee este documento COMPLETO antes de hacer nada.
> Aquí está todo lo trabajado con Eduardo (12–15 ago 2026). Guarda las REGLAS FIJAS en tu
> memoria persistente tal cual, respétalas siempre, y continúa desde los PENDIENTES.

---

## 1. QUÉ ES ESTE PROYECTO

Eduardo Zayas dirige **Jewelry Remate MX** (tienda Shopify: jewelryrematemx.com, dominio admin `tzy5fi-mh.myshopify.com`, conectada vía conector MCP de Shopify en claude.ai). Este repo (`jewelryremateoficial/jewelry-remate-workflow`, GitHub Pages) contiene sus herramientas operativas:

| Página | URL | Qué es |
|---|---|---|
| **Centro de órdenes de compra** | jewelryremateoficial.github.io/jewelry-remate-workflow/**ordenes.html** | LA herramienta principal de este chat: semáforo por proveedor, orden sugerida, en camino, movimiento |
| Centro de inventario (por variante) | …/centro-variantes.html | Dashboard anterior: estancados, para rematar, super stars, analizador de órdenes |
| Workflow editor | …/index.html | Editor de flujo del equipo |

**Proveedores activos:** HAIFENG, ZOEY, CYNTHIA CAO, NANCY VIP, DINA DU, COCOMA, MOLLY (en Shopify a veces "M0LLY" con cero — normalizar a MOLLY). **COCO ZHANG inactivo** (su stock se sigue mostrando). El proveedor de cada producto está en el campo `vendor` de Shopify.

---

## 2. REGLAS FIJAS DE EDUARDO — GRABAR EN MEMORIA, NUNCA CAMBIAR

**REGLA CERO:** NO hacer NINGÚN cambio a ordenes.html (diseño, lógica, secciones, fórmulas, columnas — nada) a menos que Eduardo lo pida explícitamente. La ÚNICA operación permitida sin pedirla es la **actualización diaria de datos** (misma lógica, datos frescos de Shopify, git push). Todo lo que Eduardo pida queda fijo PARA SIEMPRE — no revertirlo ni "mejorarlo" después. Siempre analizar con lógica y, ante cualquier duda, PREGUNTARLE antes de actuar.

**Ventanas de tiempo:**
- Ventas para generar/filtrar la orden: **60 días**.
- Métricas/historial del SKU (movimiento): **90 días**.
- **ESTANCADO REAL** = el producto debe tener **90+ días desde su alta** Y **0 ventas en 90 días**. Un producto dado de alta hace poco (ej. 29 jul, 5 ago) sin ventas NO es estancado — es NUEVO.
- **🐢 LENTO** = 40+ días sin vender (con historial); sí se puede pedir pero va marcado.

**Fórmula de cantidad sugerida:** pzs/semana (ventas 60d ÷ 60 × 7) × **10 semanas** (6 de viaje —la mercancía tarda ~1.5 meses en llegar de China— + 4 de colchón) − stock − en camino. **+20% a los top** (>10 pzs en 60d). Cantidades **SIEMPRE pares**. Agotados activos sin venta reciente: **2 pzs de prueba** (solo si no vienen en camino).

**REBAJA:** SOLO cuenta la venta con **precio de comparación** (compareAtPrice) y ~30%+ de descuento vs ese precio. Los **códigos de descuento de Shopify NO son rebaja** (se indican aparte: "🎟️ por código"). NUNCA usar promedios: contar **PIEZA POR PIEZA** ("5 pzs en rebaja · 2 a precio normal"). Apartado propio para SKUs activos AHORITA con 30%+ de rebaja vigente. Todo esto porque si algo solo se vende rebajado, significa que NO se vende — pedir menos o no pedir.

**EN CAMINO:** Se manejan DOS órdenes en la revisión: la orden A REVISAR y la que VIENE EN CAMINO; cada producto de la primera se cruza contra la segunda por SKU. Una fila del Excel cuenta como "ya llegó" **SOLO si TODA la fila está en verde** (cada celda con contenido). Una sola celda verde NO cuenta — los colores agrupan **guías de envío** (verdes una guía, morados otra, azules otra). Sin inferencias por stock. En la columna EN CAMINO: si no se pidió en la otra orden → **"—" (cero)**, nunca un chip "pedido". Cada línea en camino se clasifica **🔄 Restock** (SKU con historial) o **🆕 Nueva** (SKU nuevo o <90 días de alta), con totales de piezas por orden.

**Otras reglas:**
- Solo productos ACTIVOS generan orden; **borradores/archivados van en apartado propio** por proveedor (sin sugerencia — criterio de Eduardo), marcando "vendió X pzs estando activo" si tuvieron ventas.
- TODO por VARIANTE (SKU exacto) — cada talla/color es un producto aparte. NUNCA a nivel producto.
- Duplicados de nombre entre activos: marcar; si ambos venden, anotarlo en observaciones.
- Costo unitario **USD = MEJOR precio histórico** del consolidado de proveedores; sin costo → celda vacía + "SIN COSTO" (Eduardo los completa y los regresa).
- Revisión de una orden usa ventas de 90 días ajustadas a los días reales del producto en inventario (mucho / más o menos / poco / nada); faltan super stars → agregar; sobran lentos/muertos → señalar.
- **Export de orden (.xlsx con FOTO INCRUSTADA en la celda, filas altas)**: SOLO columnas #, FOTO, PRODUCTO, VARIANTE, SKU, PEDIR, COSTO UNITARIO (US), TOTAL (US), MATERIAL, OBSERVACIONES.
- Costos de proveedor visibles en la página: OK (decisión de Eduardo).
- **Borrador con guardado automático**: cada cantidad editada en PEDIR se guarda al instante (localStorage) y se restaura al volver, con barra "💾 Borrador guardado automáticamente" y botón de descartar con confirmación. Nunca quitar.
- Actualización de datos **día con día al término del día** (~11 PM Hermosillo).

---

## 3. TODO LO QUE SE HIZO EN ESTE CHAT (12–15 ago 2026)

1. **Excel consolidado de precios de proveedores** → `~/Downloads/HISTORIAL_PRECIOS_PROVEEDORES_2024-JUL2026.xlsx`. Une las 12 tablas mensuales (may 2025–jul 2026, 26 órdenes, ~5,150 líneas) + historial viejo. Una hoja por proveedor (costo por orden, MEJOR, ÚLTIMA, MXN a TC editable en RESUMEN!B4), hoja TODAS LAS ORDENES, y hoja **ALERTA ROAS**: 2,191 SKUs cruzados con Shopify → 40 CRÍTICOS (precio < 2.5× costo) y 194 en PELIGRO (2.5–3.5×). De febrero se usó el archivo "(1)" (trae COCO ZHANG). Se rescataron datos que solo estaban en el historial: CYNTHIA 07/07/26, ZOEY dic 25, DINA DU orden 1046 (dic 24/ene 25) y materiales.
2. **ordenes.html — Centro de órdenes de compra** (todo lo de la sección 2 implementado y verificado). Números al 14 ago: 3,384 variantes (2,775 activas), 1,448 con ventas 60d, 59 con rebaja vendida, 202 con rebaja activa hoy, 538 estancadas reales, 86 nuevas sin venta (excluidas de estancados), 380 lentas, 609 en borrador (4 vendieron estando activas).
3. **En camino precargado** (en `scripts/transit_base.json`): NANCY 09/07 (225 pzs, de la tabla de julio), CYNTHIA 07/07 ACT2 (1,088 pzs — del Excel de Eduardo, 117 líneas restock + 13 nuevas con 563 pzs), HAIFENG 11/07 (2,427 pzs — 197 restock + 43 nuevas con 1,524 pzs). CERO filas verdes en ambos Excel → todo en camino, nada llegado.
4. **Análisis de faltantes de junio**: ZOEY 08/06 tiene **17 variantes** pedidas hace ~9 semanas con stock 0 y 0 ventas (posible caja perdida o no ingresada): RELOJ TANK CR BLACK GOLD ×7, RELOJ C BAIGNOIRE ×5, RELOJ RX OYSTER BLACK (con caja) ×4, RELOJ SANTOS SILVER 34mm ×3 y 39mm ×3, BOLSO LADY D CHAROL OFF WHITE ×3, etc. HAIFENG 16/06: 2. Además ~30 SKUs de esos Excel no existen en Shopify. **Eduardo no ha confirmado qué hacer con esto.**
5. **Rutina diaria** "actualizar-ordenes-diario" (scheduled task LOCAL de la compu original, 11 PM). En la compu nueva NO existe — habría que recrearla ahí (o dejarla solo en la original). Proceso completo en `scripts/ACTUALIZAR.md` + generador `scripts/build_ordenes.py` + `scripts/dump_costs.py` (lee los Excel de ~/Downloads/TABLAS DE PRECIOS — están en la compu original).
6. **Excel con fotos**: la descarga usa ExcelJS (`exceljs.min.js` en el repo) e incrusta las fotos del CDN de Shopify en la celda.
7. Datos técnicos útiles: ventas por variante vía ShopifyQL (`GROUP BY product_variant_sku`); catálogo vía GraphQL `productVariants` paginado (250/pág, ~14 págs); detalle pieza por pieza vía `bulkOperationRunQuery` de orders con lineItems (JSONL); edad del producto = publishedAt/createdAt (products con `query:"created_at:>=…"`); los reportes guardados del admin de Shopify NO son accesibles por API, pero sus métricas se reproducen con ShopifyQL.

---

## 4. PENDIENTES (continuar aquí)

1. **Conectar Supabase** para que el borrador y las órdenes en camino se compartan entre dispositivos (Eduardo ya dijo que SÍ). Estado: existe `supabase/schema.sql` (del workflow editor, con auth) pero NO hay proyecto/URL/anon key configurados en el repo. Se intentó ver su dashboard vía su Chrome ("Eduardo ex compu") y quedó interrumpido. Siguiente paso: obtener URL del proyecto + anon key (o crear proyecto), crear una tabla simple de estado compartido, y sincronizar `oc_edits_v1`/`oc_transit_v1`/`oc_transit_rm_v1` de localStorage ↔ Supabase.
2. **Faltantes de ZOEY 08/06** (punto 3.4): preguntar a Eduardo si los reclama al proveedor; puede pedir la lista en Excel.
3. Si Eduardo comparte nuevas órdenes en camino (dijo que las pondrá en Drive), actualizar `scripts/transit_base.json` con el parser de fila-100%-verde.
4. Rutina diaria en esta compu nueva: decidir si se recrea aquí o se queda en la original (no debe correr doble).

## 5. CÓMO OPERAR EN LA COMPU NUEVA

1. Clonar el repo: `git clone https://github.com/jewelryremateoficial/jewelry-remate-workflow.git`
2. Conectar el conector de **Shopify** en claude.ai (Configuración → Conectores) — sin él no hay datos.
3. Cuando Eduardo diga **"actualiza órdenes"**: seguir `scripts/ACTUALIZAR.md` al pie de la letra (solo datos, cero cambios de lógica).
4. Guardar la sección 2 de este documento en la memoria persistente como reglas tipo feedback (nombre sugerido: `reglas-centro-ordenes`) y la sección 1 como contexto de proyecto.
5. Los archivos fuente de costos (TABLAS DE PRECIOS, historial) están en `~/Downloads` de la compu ORIGINAL; si no están aquí, usar `scripts/costs.json` (los costos no cambian a diario).
