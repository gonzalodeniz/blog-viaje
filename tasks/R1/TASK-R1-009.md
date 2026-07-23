# TASK-R1-009 — CRUD admin de temas y viajes

- **WP:** WP-R1-4
- **Requisitos:** RF-R1-15, RF-R1-16, RF-R1-18 (aplicado)
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-009

## Objetivo

Existen los endpoints CRUD de `/api/admin/topics` y `/api/admin/trips` (crear, listar, obtener, actualizar, borrar; despublicar es un caso particular de actualizar `status`). El endpoint de actualización de un viaje es el primer punto donde `content_json` se sanitiza de verdad con `render_content_html()` (TASK-R1-006) para rellenar `content_html`.

## Contexto y decisiones

- **Autorización por rol, aplicada por primera vez:** estos son los primeros endpoints mutables y de administración; se protegen con `get_current_user` + un nuevo `require_admin` (403 si `role != "admin"`), además de `require_csrf` en toda mutación. Es la primera vez que se usa de verdad la columna `users.role` que TASK-R1-007 creó pero no aplicaba.
- **Slug de viajes autogenerado, no editable por el cliente:** RF-R1-15 lista los campos del CRUD de viajes (título, tema, fechas, etiquetas, lugar, foto de portada, estado) y `slug` no está entre ellos — es un detalle de URL, no un campo de negocio. Se deriva del título al crear (minúsculas, sin acentos, guiones) y, si colisiona, se le añade un sufijo numérico. No se puede editar tras crear (evita romper URLs ya compartidas; si hiciera falta, es una tarea aparte).
- **Slug de temas, en cambio, sí es editable:** RF-R1-16 lo lista explícitamente como campo del CRUD (nombre, slug, descripción, color), así que el cliente lo envía y se valida como cualquier otro campo (único, igual que `name`).
- **Etiquetas:** el CRUD de viajes acepta una lista de nombres de etiqueta (`tag_names`); las que no existen se crean sobre la marcha (no hay un CRUD de tags propio pedido por ningún RF de R1).
- **Borrar un tema referenciado por viajes falla con 409, no con 500:** la FK es `RESTRICT` (TASK-R1-005); se captura el `IntegrityError` y se traduce a un error legible en vez de dejar pasar un 500.
- **"Despublicar" no es un endpoint aparte:** es el mismo `PUT /api/admin/trips/{id}` cambiando `status` a `"draft"`. Añadir una ruta específica solo para eso sería una abstracción sin necesidad — RF-R1-15 dice literalmente "estado borrador/publicado, despublicar", es decir, el mismo campo en las dos direcciones.
- **Listar borradores es cosa del panel, no de la vista de lectura:** `GET /api/admin/trips` devuelve todos los viajes (borrador y publicado); es un endpoint distinto de `GET /api/trips` (TASK-R1-008), que sigue mostrando solo publicados.
- **`audit_log` no se escribe todavía desde estos endpoints:** RF-R1-12 ("toda acción de la CLI...") habla específicamente de la CLI de rescate (WP-R1-3); no hay ningún RF de R1 que pida auditar las acciones del panel web. Se deja fuera para no inventar un requisito.
- **Fuera de alcance:** subida de fotos (siguiente y última pieza de WP-R1-4); rol `lector` real (no hay forma de crear uno todavía — sigue bloqueado por WP-R1-3); UI de panel (WP-R1-5); revocación de sesiones desde el panel (RF-R1-06, WP-R1-2/5).

## Definition of Done

- [x] Código con docstring `Implementa: RF-R1-15, RF-R1-16, RF-R1-18` en los módulos afectados
- [x] Tests con `@pytest.mark.spec("...")`: CRUD completo de temas y viajes; 401 sin sesión y 403 sin rol admin y sin CSRF; borrar tema referenciado devuelve 409; actualizar `content_json` sanitiza y rellena `content_html`; publicar/despublicar; slugs autogenerados y sin colisión (30 tests nuevos, 134 en total)
- [x] Cobertura ≥ 80 % en el código tocado (`admin_topics.py` 100 %, `admin_trips.py` 99 %; 98.36 % total)
- [x] Revisión de seguridad: mutaciones detrás de auth + rol admin + CSRF; sin SQL crudo; `content_html` nunca se acepta directamente del cliente (siempre se deriva de `content_json` sanitizado vía `render_content_html`); bandit sin hallazgos
- [x] `python tools/traceability.py --check --release R1` — sigue en rojo (quedan otros WPs sin test), no bloquea esta tarea
- [x] Commits con prefijo `[TASK-R1-009]`

## Notas de implementación

- `backend/app/api/deps.py`: nuevo `require_admin`.
- `backend/app/core/slugify.py`: utilidad de generación de slugs.
- `backend/app/api/admin_topics.py`, `backend/app/api/admin_trips.py`.
