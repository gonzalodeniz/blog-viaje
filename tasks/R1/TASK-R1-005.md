# TASK-R1-005 — Modelo de datos de contenido (temas, viajes, fotos, etiquetas)

- **WP:** WP-R1-4
- **Requisitos:** RF-R1-13, RF-R1-14, RF-R1-15, RF-R1-16, RF-R1-18
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-005

## Objetivo

Existen los modelos SQLAlchemy y la migración Alembic de `topics`, `trips`, `tags`/`trip_tags`, `photos`, `photo_variants` y `audit_log` (esquema esencial de SPEC-MASTER §7.3, sin `users`/`sessions`/`login_attempts`/`account_locks`, que llegan con WP-R1-2). No incluye endpoints ni lógica de negocio: es la base sobre la que TASK-R1-006+ construirán la API de lectura, el CRUD admin y la sanitización HTML.

## Contexto y decisiones

- **Alcance deliberadamente reducido dentro de WP-R1-4:** el paquete completo (migraciones + API de lectura + CRUD admin + sanitización + subida de fotos) es demasiado grande para una sola tarea trazable; se divide en slices verticales, empezando por el modelo de datos porque todo lo demás depende de él. Precedente: WP-R1-1 se dividió en TASK-R1-001..004.
- **`content_json` / `content_html` (RF-R1-18):** esta tarea solo crea las columnas (`content_json JSONB`, `content_html TEXT`). La sanitización servidor con lista blanca que rellena `content_html` a partir del JSON de ProseMirror es lógica de aplicación y llega en la tarea que implemente el CRUD admin de viajes (WP-R1-5 depende de ella).
- **`users`/`FK` de auditoría:** `audit_log.actor` se modela como texto libre (`"user:<id>"` o `"cli"`) en vez de FK a `users`, porque `users` no existe todavía (WP-R1-2 va después según el orden del plan) y no se quiere bloquear esta tarea por esa dependencia cruzada. Se documenta como decisión temporal; si WP-R1-2 lo justifica, se puede migrar a FK con un ADR o una migración posterior.
- **`cover_photo_id` en `trips`:** FK nullable a `photos.id`; como `photos.trip_id` también referencia a `trips`, se crea `trips` primero sin la FK, se crea `photos`, y una segunda migración (o `ALTER TABLE` al final de la misma) añade la FK de `cover_photo_id` para evitar el ciclo de creación.
- **`search_vector` (búsqueda, RF-R1-13 filtros):** se crea la columna `tsvector` y el índice GIN ya en esta migración (coste marginal), aunque el endpoint de búsqueda con `query=` no es parte de esta tarea — evita una migración adicional solo para eso.
- **Fuera de alcance:** `users`, `sessions`, `login_attempts`, `account_locks` (WP-R1-2); endpoints REST; sanitización HTML; subida de fotos y `libvips`; `photo_variants` se modela pero no se genera nada — no hay worker todavía.

## Definition of Done

- [x] Código con docstring `Implementa: RF-R1-13, RF-R1-14, RF-R1-15, RF-R1-16, RF-R1-18` en los modelos SQLAlchemy afectados
- [x] Tests con `@pytest.mark.spec("...")` que verifiquen constraints clave (UNIQUE de slugs, `UNIQUE(trip_id, content_hash)` en fotos, cascade/restrict de FKs) contra PostgreSQL real (`backend/tests/test_models.py` + `backend/tests/conftest.py`, que aplican la migración de Alembic y aíslan cada test por SAVEPOINT); requirió añadir un servicio `postgres` al job `backend` de CI, que antes no tenía base de datos real
- [x] Cobertura ≥ 80 % en el código tocado (98.82 % en `app/models/*`)
- [x] Revisión de seguridad (sin SQL crudo interpolado; `content_html` nunca se rellena en esta tarea; sin datos sensibles en `audit_log.detail`; bandit sin hallazgos)
- [x] `python tools/traceability.py --check --release R1` — sigue en rojo (quedan endpoints y otros WPs sin test), no bloquea esta tarea
- [x] Commits con prefijo `[TASK-R1-005]`

## Notas de implementación

- `backend/app/models/`: nuevos módulos `topic.py`, `trip.py`, `tag.py`, `photo.py`, `audit_log.py`, importados desde `app/models/__init__.py` para que Alembic los detecte vía `app.db.base.Base.metadata`.
- `backend/alembic/versions/`: una migración (o dos si el ciclo `trips.cover_photo_id` ↔ `photos.trip_id` lo exige) generada con `alembic revision --autogenerate` y revisada a mano.
- **Bug detectado al escribir los tests:** `use_alter=True` en la `ForeignKeyConstraint` de `cover_photo_id` dentro de `create_table('trips', ...)` solo le indica a SQLAlchemy que la omita del `CREATE TABLE`; no emite el `ALTER TABLE` diferido dentro de una migración de Alembic. La FK nunca se creaba (confirmado contra Postgres real vía `pg_constraint`). Corregido añadiendo `op.create_foreign_key(...)` explícito tras crear `photos`, con su `drop_constraint` simétrico en `downgrade()`.
