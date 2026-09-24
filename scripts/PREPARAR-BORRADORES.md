# PREPARAR BORRADORES NUEVOS — etiquetas, colecciones y descripción

> Proceso fijo de Eduardo. Se corre cuando él dice algo como **"tengo productos nuevos
> en borrador, ponles etiqueta, colección y descripción"**. Hecho por primera vez en
> agosto 2026 y repetido el 24 sep 2026 (113 productos). NO cambiar el formato.

## Qué hace

A cada producto **nuevo** que está en borrador (sin etiquetas, sin descripción) se le pone:

1. **Etiquetas** (exactamente estas 4; la primera según la primera palabra del título):

   | Título empieza con | Etiqueta de categoría | Tipo de producto |
   |---|---|---|
   | ARETES | `aretes` | Aretes y Arracadas |
   | ARRACADAS | `arracadas` | Aretes y Arracadas |
   | ANILLO | `anillo` | Anillos |
   | PULSERA | `pulsera` | Brazaletes y Pulseras |
   | BRAZALETE | `brazalete` | Brazaletes y Pulseras |
   | COLLAR | `collares` | Cadenas y Collares |
   | BOLSO / BOLSA | `bolso` | Bolsos |
   | MOCHILA | `bolso` + `mochila` | Bolsos |
   | CARTERA | `cartera` | Carteras |
   | TARJETERO | `Tarjetero` | Tarjeteros |
   | MONEDERO | `Monedero` | Monederos |
   | SANDALIAS / TENIS / BALLERINAS | `Calzado` | Calzado |
   | CAMISETA / BLUSA / ABRIGO (ropa) | `ropa` | Ropa |
   | RELOJ | `reloj` | Relojes |
   | LENTES | `lentes` | lentes de sol |

   más `FALTA-INFO`, `New` y `new arrivals`. **Nada más**: no se inventan etiquetas de
   marca, color, género, etc. Eso lo completa Eduardo o su equipo.

2. **Tipo de producto** según la tabla.

3. **Descripción** con los datos que Eduardo llena marcados como POR COMPLETAR
   (HTML exacto, el título en mayúsculas tal cual está en Shopify):

   ```html
   <p><strong>TÍTULO DEL PRODUCTO</strong></p><p><strong>Material:</strong> POR COMPLETAR</p><p><strong>Medidas:</strong> POR COMPLETAR</p><p><strong>Cambios y Devoluciones Disponibles.</strong><br><strong>(Excepto en promociones y en casos donde se apliquen políticas específicas).</strong></p>
   ```

4. **Colecciones**: NO se agregan a mano. Las colecciones de la tienda son
   automáticas por etiqueta (ARETES, ANILLOS, PULSERAS, COLLARES, BOLSOS,
   CARTERAS/TARJETEROS, CALZADO, ROPA, NEW ARRIVALS, MUJER, etc.), así que con las
   etiquetas de arriba el producto entra solo. Shopify tarda unos minutos en reindexar.

## Qué NO se toca

- Precio, fotos, inventario, SKU, nombre de variante ("NOMBRE AQUI"): los llena Eduardo.
- Borradores viejos (los ~600 que están en borrador por decisión de Eduardo). Solo los
  **nuevos**: filtrar por `status:draft AND created_at:>'<fecha>'` y confirmar que
  tengan `tags: []` y descripción vacía antes de tocarlos.
- Productos activos.

## Cómo se hace (con el conector de Shopify en claude.ai)

1. Listar los borradores nuevos: `search_products` con
   `status:draft AND created_at:>'AAAA-MM-DD'`, 50 por página, paginar hasta el final.
   Verificar que tengan etiquetas vacías y descripción vacía.
2. Escribir un archivo `productos.txt` con una línea por producto:
   `id_numerico|TÍTULO|proveedor|variantes` y correr `scripts/preparar_borradores.py`
   (genera `batchN.json` de 20 productos cada uno: query + variables).
3. Validar la mutación con `validate_graphql_codeblocks` y ejecutarla con
   `graphql_mutation` (`productUpdate` con alias `u0..u19`, input `ProductUpdateInput`
   con `id`, `tags`, `productType`, `descriptionHtml`). Un lote de prueba primero;
   si `userErrors` sale vacío, mandar el resto en paralelo.
4. Verificar: `search_products` con `tag:"FALTA-INFO"` y `search_collections` con
   `product_id:<id>` para un par de productos.
5. Reportar a Eduardo: cuántos por categoría, y **posibles duplicados** (mismo
   título dos veces, handle terminado en `-1`, sin SKU).

## Cómo lo termina Eduardo

Filtra en el admin por etiqueta `FALTA-INFO`, llena material, medidas, precio,
fotos y variante; al terminar cada uno le quita `FALTA-INFO` y lo activa.
