# TASK-R1-010 — Subida simple de fotos (original + versión web)

- **WP:** WP-R1-4
- **Requisitos:** RF-R1-14 (aplicado), RF-R1-15 (foto de portada, ya podía referenciarse; ahora se puede subir)
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-010

## Objetivo

Existe `POST /api/admin/trips/{trip_id}/photos` (subida multiparte en lote) que guarda el original intacto y genera una única versión web razonable con `pyvips` (ADR-001), y `GET /api/photos/{photo_id}/file`, que sirve esa versión web a cualquier sesión autenticada. El artículo (`GET /api/trips/{slug}`, TASK-R1-008) ya puede enlazar una URL real por foto en vez de solo metadatos.

## Contexto y decisiones

- **"Simple" según `specs/SPEC-R1.md` línea 10:** original + **una** versión web razonable; nada de `thumb`/`large`/AVIF/SSIM adaptativo/deduplicación con aviso/EXIF→GPS — eso es RF-R2-12/13/14 (R2). Se genera un único `PhotoVariant` de `kind="medium"`, redimensionado al lado mayor a 1600 px, WebP, calidad 82 (mismos números que describe SPEC-MASTER §9 para consistencia, aunque el resto del pipeline de esa sección es R2).
- **Validación por firma binaria, no por extensión (SPEC-MASTER §8):** se comprueban los primeros bytes del archivo contra las firmas conocidas de JPEG/PNG/WebP; una extensión `.jpg` con contenido que no sea ninguna de ellas se rechaza con 400, aunque el `Content-Type` declarado diga lo contrario.
- **Límite de tamaño:** 25 MB por archivo (razonable para fotos de cámara/móvil sin ser una API de subida de vídeo); configurable si hace falta, no se expone en el spec un valor concreto para R1.
- **Deduplicación mínima, no la de RF-R2-14:** la constraint `UNIQUE(trip_id, content_hash)` (TASK-R1-005) ya existe en BD; si se sube el mismo contenido dos veces al mismo viaje, esta tarea devuelve 409 en vez de silenciarlo o avisar de forma elaborada — el "aviso y no duplicар almacenamiento" fino es RF-R2-14.
- **Nombre de archivos y estructura de carpetas:** se sigue el boceto de `SPEC-MASTER §7.5` (`media/originals/{tema-slug}/{año}-{viaje-slug}/...`, `media/derived/...`) porque ya está documentado y no cuesta más seguirlo ahora que inventar uno propio para luego migrarlo en R2.
- **Servido de la variante web:** `GET /api/photos/{photo_id}/file` exige `get_current_user` (como todo en R1: no hay collage público ni fotos públicas servibles todavía — RF-R2-11). Sirve el fichero de `derived/`, nunca el original (regla no negociable de CLAUDE.md); si la foto no tiene variante generada, 404. `X-Accel-Redirect` (RNF-R2-02) es una optimización de R2; en R1 el propio backend sirve los bytes.
- **`taken_at`/GPS:** se dejan `NULL`; la extracción EXIF es RF-R2-13. `width`/`height` sí se rellenan (vienen gratis del propio `pyvips.Image.new_from_buffer` al abrir el original).
- **Volumen de medios en `docker-compose`:** no existía ningún volumen para `backend`; se añade `media:/app/media` (con `MEDIA_ROOT` configurable por si un despliegue quiere otra ruta). `backend` sigue con `read_only: true`; escribir en un volumen declarado explícitamente no lo contradice.
- **`libvips` en el `Dockerfile`:** se añade `libvips42`/`libvips-dev` vía `apt-get`. No se puede probar `pyvips` en el entorno de desarrollo de esta sesión (sandbox sin `libvips` instalado y sin privilegios para instalarlo); los tests de esta tarea se ejecutan dentro de un contenedor Docker construido con el `Dockerfile` real, no en el intérprete local.
- **Fuera de alcance:** biblioteca de fotos del panel (RF-R2-10), papelera (RF-R2-10), cambiar visibilidad pública/privada de una foto ya subida vía endpoint propio (el campo existe, pero no hay UI/endpoint de biblioteca en R1), `X-Accel-Redirect`, EXIF/GPS, AVIF/JPEG de fallback, `regenerate-derived` (CLI, WP-R1-3).

## Definition of Done

- [x] Código con docstring `Implementa: RF-R1-14, RF-R1-15` en los módulos afectados
- [x] Tests con `@pytest.mark.spec("...")` ejecutados dentro de un contenedor Docker con `libvips` (153 tests en total, todos en verde): subida válida crea `Photo` + `PhotoVariant` con dimensiones correctas; firma binaria inválida rechazada (no por extensión); archivo demasiado grande rechazado; hash duplicado en el mismo viaje rechazado; servir la variante exige sesión (401) y devuelve 404 sin variante generada; normalización de slugs con intento de path traversal
- [x] Cobertura ≥ 80 % en el código tocado (`photo_storage.py` 100 %; 98.06 % total)
- [x] Revisión de seguridad: firma binaria (no extensión ni `Content-Type`); límite de tamaño; nombres de archivo generados por el servidor; slugs re-normalizados antes de usarlos como componente de ruta (defensa en profundidad contra path traversal vía `topics.slug`, que es texto de cliente); originales nunca servidos (verificado manualmente: `GET /api/photos/{id}/file` solo lee `PhotoVariant`, nunca `Photo.original_path`); mutación protegida por auth + rol admin + CSRF; bandit sin hallazgos
- [x] `python tools/traceability.py --check --release R1` — sigue en rojo (quedan otros WPs sin test), no bloquea esta tarea
- [x] Commits con prefijo `[TASK-R1-010]`
- [x] Verificado manualmente de extremo a extremo contra la imagen Docker real (multi-stage, `libvips` en runtime): `docker build` limpio, `/healthz` en verde contra Postgres real, login → crear tema/viaje → publicar con `content_html` sanitizado de verdad → subir una foto JPEG real → servida como WebP con las dimensiones correctas → 401 sin sesión → estructura de `media/originals/` y `media/derived/` en disco coincide con SPEC-MASTER §7.5

## Notas de implementación

- `backend/app/services/photo_storage.py`: firma binaria, hash SHA-256, rutas de `originals/`/`derived/`, generación de la variante web con `pyvips`.
- `backend/app/api/admin_photos.py`: `POST /api/admin/trips/{trip_id}/photos`.
- `backend/app/api/photos.py`: `GET /api/photos/{photo_id}/file`.
- `backend/app/api/trips.py` (TASK-R1-008): `PhotoSummary` gana un campo `url`.
- `backend/Dockerfile`: `libvips42`, `libvips-dev`. `deploy/docker-compose.yml`: volumen `media` en `backend`.
