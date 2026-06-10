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

Todo el código (HTML, CSS y JavaScript) vive en `index.html`. Para cambios:

1. Edita `index.html`.
2. Prueba abriéndolo en el navegador.
3. Haz commit y push:
   ```bash
   git add index.html
   git commit -m "Describe tu cambio"
   git push
   ```

## 📦 Estructura

```
.
├── index.html      # La aplicación completa (UI + lógica)
└── README.md       # Este archivo
```

## 🗺️ Ideas a futuro

- [ ] Exportar / importar el workflow a un archivo JSON.
- [ ] Guardado en la nube (sincronización entre dispositivos).
- [ ] Modo colaboración multiusuario.
- [ ] Versión instalable (PWA).

---

Hecho con cariño para Jewelry Remate 💎
