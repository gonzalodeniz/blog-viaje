# SPEC-R2 — Release 2 «Fotografía»

Versión 0.1 · 13 de julio de 2026 · Estado: **borrador** (se congela al iniciar la release)
Deriva de [SPEC-MASTER.md](SPEC-MASTER.md) v1.1.

## 1. Objetivo de la release

El blog luce: portada pública con collage de fotos públicas y lectura con fotos grandes, rápidas y bien organizadas. Pipeline de imágenes de primera clase.

## 2. Requisitos funcionales

### 2.1 Portada pública / página de login

| ID | Requisito | Prioridad |
|---|---|---|
| RF-R2-01 | Collage responsive de fotos **públicas** en la página de inicio/login, selección aleatoria en cada carga con caché corta. | M |
| RF-R2-02 | El collage solo sirve variantes optimizadas (nunca originales), sin metadatos EXIF (sin GPS ni datos de cámara). | M |
| RF-R2-03 | Sin fotos públicas, la portada muestra diseño limpio con nombre del blog y formulario de login. | M |
| RF-R2-04 | Marcar/desmarcar fotos como públicas individualmente o en lote, con previsualización de la portada. | S |

### 2.2 Lectura con fotos

| ID | Requisito | Prioridad |
|---|---|---|
| RF-R2-05 | Lightbox a pantalla completa en ventana/visor separado: navegación anterior/siguiente, zoom y descarga de la variante grande. | M |
| RF-R2-06 | Lazy loading con placeholder blur-up/LQIP; lectura fluida con decenas de fotos. | M |

### 2.3 Editor e imágenes en el texto

| ID | Requisito | Prioridad |
|---|---|---|
| RF-R2-07 | Insertar fotos en cualquier punto del texto (drag&drop, pegar, biblioteca); tamaño libre: presets 25/50/75/100 %, píxeles con tiradores, alineación con o sin texto alrededor; pie de foto y alt por imagen. | M |
| RF-R2-08 | Subida masiva (multi-selección, arrastrar carpeta) con cola, progreso por archivo y reintentos; sin límite artificial. | M |
| RF-R2-09 | En la subida se asigna/confirma el tema del viaje y el sistema archiva las fotos en la estructura de carpetas de ese tema/viaje. | M |
| RF-R2-10 | Biblioteca de fotos: navegación por tema y viaje, búsqueda por nombre/fecha, cambio de visibilidad, edición de pie/alt, papelera con retención de 30 días. | M |

### 2.4 Gestión y organización de fotografías

| ID | Requisito | Prioridad |
|---|---|---|
| RF-R2-11 | Visibilidad `privada` (defecto) o `pública` por foto; autorización comprobada en **cada** petición de imagen. | M |
| RF-R2-12 | Original intacto + variantes visualmente sin pérdidas (SSIM ≥ 0,98): `thumb` ~400 px, `medium` ~1280 px, `large` ~2560 px en WebP con fallback JPEG y AVIF opcional; `large` nítida en monitores 2K. | M |
| RF-R2-13 | Corrección de orientación EXIF; extracción de fecha de captura y GPS a BD; eliminación de metadatos en todas las variantes servidas. | M |
| RF-R2-14 | Deduplicación por hash de contenido dentro del mismo viaje, con aviso. | S |
| RF-R2-15 | Estructura de carpetas legible por tema y viaje en el volumen de medios (SPEC-MASTER §7.5), comprensible en un backup por sí sola. | M |

## 3. Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF-R2-01 | LCP < 2,5 s en portada y en artículos con 50 fotos (4G simulada); `medium` ≤ 350 KB de mediana; procesado de una foto de 24 MP < 3 s. |
| RNF-R2-02 | Caché inmutable con huella en el nombre de archivo vía nginx; privadas mediante `X-Accel-Redirect` tras autorización del backend. |

## 4. Referencias de diseño

- Pipeline de imágenes: SPEC-MASTER §9.
- Estructura de medios: SPEC-MASTER §7.5.
- Criterios Gherkin: SPEC-MASTER §12 (RF-R2-01/05/11).
- `bitacora-cli regenerate-derived` se implementa en esta release (SPEC-MASTER §10).
