# TASK-R1-008 — Endpoints de lectura: listado y artículo de un viaje

- **WP:** WP-R1-4
- **Requisitos:** RF-R1-13, RF-R1-14, RF-R1-01 (aplicado)
- **Estado:** en curso
- **Rama:** feature/TASK-R1-008

## Objetivo

Existen dos endpoints HTTP autenticados: `GET /api/trips` (listado cronológico de viajes publicados) y `GET /api/trips/{slug}` (artículo completo con su HTML sanitizado y sus fotos). Es la primera pieza de WP-R1-4 que expone datos por HTTP, apoyándose en `get_current_user` de TASK-R1-007.

## Contexto y decisiones

- **Solo viajes publicados:** `status == "published"`; los borradores son cosa del panel de administración (WP-R1-5), que todavía no existe. Un slug de un borrador (o inexistente) devuelve 404 igual que un slug que nunca existió, para no filtrar por respuesta qué viajes están en borrador.
- **Todo requiere sesión, sin excepción (RF-R1-01):** en R1 no hay portada pública ni fotos marcadas como públicas servibles (`specs/SPEC-R1.md` línea 10: "la subida de fotos en R1 es simple... visibilidad pública por foto... queda en R2"). Por tanto ambos endpoints exigen `get_current_user`; sin sesión válida, 401 y ningún dato del viaje, tal como pide el criterio de aceptación de RF-R1-01 en `specs/SPEC-R1.md`.
- **Orden cronológico:** por `trip_start` descendente (viaje más reciente primero), con `created_at` descendente como desempate para viajes sin fecha de inicio.
- **Sin filtros (`query=`, `topic=`, `year=`, `tag=`) todavía:** el resumen de API de SPEC-MASTER §7.4 los sugiere, pero RF-R1-13 en R1 solo pide "listado... ordenado cronológicamente"; la búsqueda de texto completo es RF-R3-01 (R3). Añadir filtros no pedidos ahora sería diseñar para un requisito que no existe todavía.
- **Fotos sin URL servible todavía:** no existe endpoint de medios (`GET /media/...` con autorización, RNF-R2-02) ni la tarea de subida de fotos (siguiente pieza de WP-R1-4). El artículo devuelve los metadatos de cada foto (`id`, `caption`, `alt_text`, `width`, `height`, `taken_at`) pero no una URL; la tarea de subida/servido de fotos fijará el esquema de rutas y añadirá el campo de URL entonces, en vez de inventarlo aquí sin saber cómo se van a servir.
- **Sin paginación:** con el volumen esperado (blog personal) una lista completa es razonable; se añadirá si hace falta, no antes.
- **Fuera de alcance:** CRUD admin (RF-R1-15/16, siguiente tarea de WP-R1-4), subida/servido de fotos, autorización por rol (RF-R1-07 no implementado todavía — cualquier usuario autenticado puede leer, no hay rol `lector` aplicado porque no hay lógica de roles todavía), collage público y visibilidad por foto (R2).

## Definition of Done

- [ ] Código con docstring `Implementa: RF-R1-13, RF-R1-14` en los módulos afectados
- [ ] Tests con `@pytest.mark.spec("...")`: listado ordenado, solo publicados, 401 sin sesión (criterio de aceptación exacto de RF-R1-01), artículo con contenido y fotos (públicas y privadas incluidas), 404 en slug inexistente o en borrador
- [ ] Cobertura ≥ 80 % en el código tocado
- [ ] Revisión de seguridad: ambos endpoints detrás de `get_current_user`; sin fuga de metadatos de borradores por código de estado
- [ ] `python tools/traceability.py --check --release R1` — sigue en rojo (quedan otros WPs sin test), no bloquea esta tarea
- [ ] Commits con prefijo `[TASK-R1-008]`

## Notas de implementación

- `backend/app/api/trips.py`: `GET /api/trips`, `GET /api/trips/{slug}`.
- Modelos de respuesta Pydantic definidos en el propio módulo (no hay todavía un paquete `app/schemas/`; se crea si una tarea futura lo justifica).
