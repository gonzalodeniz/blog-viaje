# TASK-R1-001 — Esqueleto de backend, frontend y docker compose

- **WP:** WP-R1-1
- **Requisitos:** RNF-R1-07
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-001

## Objetivo

`docker compose up -d` levanta nginx + backend FastAPI (con `/healthz`) + PostgreSQL + frontend estático de bienvenida, sobre los esqueletos de proyecto definitivos (`backend/` con SQLAlchemy/Alembic/pytest configurados; `frontend/` con Vite/React/TS/Vitest).

## Contexto y decisiones

- Stack según [ADR-001](../../specs/adr/ADR-001-stack-tecnologico.md).
- Imágenes con usuario no root desde el primer Dockerfile; los endurecimientos restantes (read-only FS, healthchecks) llegan en TASK posteriores del WP-R1-1.
- El servicio `worker` y `certbot` pueden quedar declarados pero mínimos; TLS real se aborda en la tarea de nginx/TLS.

## Definition of Done

- [x] Código con docstring `Implementa: RNF-R1-07` donde aplique
- [x] Test de humo: `/healthz` responde 200 dentro de compose (verificado manualmente vía `curl` sobre `docker compose up -d`)
- [x] Cobertura ≥ 80 % en el código tocado (backend 96 %, frontend 100 % sobre lo existente)
- [x] Revisión de seguridad (sin secretos en el repo; `.env.example` sin valores reales; `npm audit` en 0 vulnerabilidades tras fijar `vitest@^4`)
- [ ] `python tools/traceability.py --check` en verde — pendiente hasta que WP-R1-1 cierre el resto de RNF de la release; RNF-R1-07 ya tiene test asociado
- [x] Commits con prefijo `[TASK-R1-001]`

## Notas de implementación

- Backend: FastAPI + SQLAlchemy 2 + Alembic + pytest, instalable como paquete editable, con `/healthz`, esqueleto de `bitacora-cli` (Typer) y suite de tests con marker `@pytest.mark.spec`.
- Frontend: Vite + React 18 (fijado según ADR-001; el scaffold instala React 19 por defecto) + TypeScript + Vitest + Testing Library, página de bienvenida propia (sin el boilerplate de create-vite).
- `docker-compose.yml` en la raíz usa `include:` para delegar en `deploy/docker-compose.yml`, de modo que `docker compose up -d` funciona desde la raíz sin `cd deploy/` y sigue leyendo `.env` de la raíz.
- nginx construye el frontend en una etapa de build (contexto = raíz del repo) y sirve el `dist/` resultante; proxy de `/api/` y `/healthz` al backend. Sin TLS/cabeceras de seguridad/rate limiting todavía: eso es una tarea posterior de WP-R1-1 (no hay dominio/certificado real que probar en este entorno).
- `worker` y `certbot` no se declaran aún en compose: no habría nada real que ejecutar hasta R2 (worker) y hasta la tarea de TLS (certbot); se añaden cuando tengan una responsabilidad real, evitando servicios placeholder sin comportamiento.
- Verificado manualmente de extremo a extremo: `docker compose up -d --build` levanta postgres/backend (healthy) y nginx; `curl http://localhost/healthz` → `{"status":"ok"}`; `curl http://localhost/` sirve la portada de bienvenida con `<title>Bitácora</title>`.
