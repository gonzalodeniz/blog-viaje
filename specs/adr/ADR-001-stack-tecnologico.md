# ADR-001 — Stack tecnológico

Fecha: 2026-07-13 · Estado: **aceptada**

## Contexto

Bitácora es un producto autoalojado, mantenido por una sola persona, con tres exigencias dominantes: pipeline de imágenes de primera clase, editor rico con imágenes redimensionables y sencillez operativa (un `docker compose up -d`, mínimo número de servicios que operar).

## Decisión

| Capa | Tecnología | Justificación |
|---|---|---|
| Backend / API | Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic + Pydantic | Tipado, rendimiento async, ecosistema de testing maduro, afinidad del mantenedor con Python |
| Frontend | React 18 + Vite + TypeScript, TanStack Query, TipTap (ProseMirror) | Editor rico extensible con imágenes redimensionables; build estático servido por nginx |
| Base de datos | PostgreSQL 16 | Requisito; búsqueda full-text en español (`tsvector` + `unaccent` + `pg_trgm`) sin motor adicional |
| Imágenes | libvips (pyvips) | Procesado muy rápido y con poca memoria; WebP/AVIF |
| Proxy / TLS | nginx + certbot | Requisito; terminación HTTPS, caché de estáticos, `X-Accel-Redirect` para medios privados |
| Trabajos en segundo plano | Cola ligera en PostgreSQL con worker propio | Evita Redis/broker: una dependencia menos que operar |
| CLI de rescate | Typer, dentro de la imagen del backend | Comparte modelos y configuración; fuera de la superficie de ataque web |
| Contenedores | Docker Compose | Requisito; despliegue de un solo comando |

## Alternativas descartadas

- **Next.js/SSR monolítico:** acopla frontend y backend; el build estático tras nginx es más simple de operar y cachear.
- **Celery + Redis** para el worker: sobredimensionado para un solo usuario; la cola en PostgreSQL elimina un servicio.
- **Motor de búsqueda dedicado (Meilisearch/Elastic):** PostgreSQL cubre RNF-R3-02 con 500 artículos; un servicio menos.
- **Pillow** para imágenes: libvips es un orden de magnitud más eficiente en memoria/CPU para lotes grandes (RNF-R2-01).

## Consecuencias

- Un único lenguaje de backend (Python) para API, worker y CLI.
- La búsqueda con erratas depende de `pg_trgm`; si la calidad no bastara en R3, se abriría un ADR para un motor dedicado.
- AVIF queda opcional porque su coste de codificación en libvips puede violar el presupuesto de 3 s por foto (RNF-R2-01); se decidirá con medición en R2.
