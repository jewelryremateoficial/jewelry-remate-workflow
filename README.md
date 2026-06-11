# Jewelry Remate · Workflow Editor

Editor visual de flujos de trabajo (workflow) para **Jewelry Remate**. Es una
aplicación web de un solo archivo (`index.html`) que corre 100% en el navegador,
sin servidor ni base de datos: todo se guarda localmente en el navegador
(`localStorage`).

## ✨ Funcionalidades

- **Áreas / nodos**: crear, editar y conectar etapas del proceso.
- **Formatos / tarjetas**: documentos y formatos asociados a cada área.
- **Conexiones (edges)**: definir el flujo entre áreas con propósito y decisión.
- **Archivos adjuntos**: subir archivos a cada área o formato.
- **Guardado automático** en el navegador (no se pierde al cerrar la pestaña).
- **Deshacer / Rehacer** (`Ctrl/Cmd+Z` y `Ctrl/Cmd+Shift+Z`).
- **Búsqueda**: filtra áreas y formatos y resalta en el diagrama.
- **4 vistas/perspectivas** (selector "Vista"): **Flujo por etapas**, **Jerárquico**
  (dirección arriba), **Por departamento** (zonas por tipo) y **Círculo**.
- **Formatos como tarjetas de documento** grandes y legibles: icono, color por
  categoría, nombre y **"Área origen → Área destino"** para ver cómo viaja cada
  formato. Se auto-separan para nunca encimarse.
- **Modo enfoque**: al hacer clic en un formato, un banner muestra
  `Área A → [Formato] → Área B` + la decisión, se resalta la ruta y se atenúa el
  resto. Al pasar el mouse se previsualiza la ruta.
- **Lienzo navegable**: abre a tamaño legible y se navega con arrastre + zoom
  (espacio "infinito"); el botón ⊡ muestra todo de un vistazo.

## 🚀 Cómo usarlo

### Opción A — Abrir directamente
Descarga el repositorio y abre `index.html` con doble clic. Funciona sin internet.

### Opción B — Publicarlo en la web (GitHub Pages)
Una vez en GitHub, activa **Settings → Pages → Branch: `main` / root**.
Quedará disponible en:

```
https://<tu-usuario>.github.io/<nombre-del-repo>/
```

## 🛠️ Editar y mejorar

El código está separado por responsabilidad. Para cambios:

1. Edita el archivo correspondiente (estructura abajo).
2. Pruébalo en el navegador (ver nota de previsualización local).
3. Haz commit y push:
   ```bash
   git add -A
   git commit -m "Describe tu cambio"
   git push
   ```

## 📦 Estructura

```
.
├── index.html        # Estructura (HTML) de la página
├── css/
│   └── styles.css    # Estilos / apariencia
├── js/
│   └── app.js        # Lógica de la aplicación
└── README.md         # Este archivo
```

> **Previsualización local:** como el código está en archivos separados, abrir
> `index.html` con doble clic puede no cargar el JS por seguridad del navegador.
> Para verlo en local, levanta un servidor simple en la carpeta:
> ```bash
> python3 -m http.server 8000
> ```
> y abre `http://localhost:8000`. En la web (GitHub Pages) funciona sin esto.

## 🗺️ Ideas a futuro

- [ ] Exportar / importar el workflow a un archivo JSON.
- [ ] Guardado en la nube (sincronización entre dispositivos).
- [ ] Modo colaboración multiusuario.
- [ ] Versión instalable (PWA).

---

Hecho con cariño para Jewelry Remate 💎
