# TASK-R1-001 — Esqueleto de backend, frontend y docker compose

- **WP:** WP-R1-1
- **Requisitos:** RNF-R1-07
- **Estado:** pendiente
- **Rama:** feature/TASK-R1-001

## Objetivo

`docker compose up -d` levanta nginx + backend FastAPI (con `/healthz`) + PostgreSQL + frontend estático de bienvenida, sobre los esqueletos de proyecto definitivos (`backend/` con SQLAlchemy/Alembic/pytest configurados; `frontend/` con Vite/React/TS/Vitest).

## Contexto y decisiones

- Stack según [ADR-001](../../specs/adr/ADR-001-stack-tecnologico.md).
- Imágenes con usuario no root desde el primer Dockerfile; los endurecimientos restantes (read-only FS, healthchecks) llegan en TASK posteriores del WP-R1-1.
- El servicio `worker` y `certbot` pueden quedar declarados pero mínimos; TLS real se aborda en la tarea de nginx/TLS.

## Definition of Done

- [ ] Código con docstring `Implementa: RNF-R1-07` donde aplique
- [ ] Test de humo: `/healthz` responde 200 dentro de compose
- [ ] Cobertura ≥ 80 % en el código tocado
- [ ] Revisión de seguridad (sin secretos en el repo; `.env.example` sin valores reales)
- [ ] `python tools/traceability.py --check` en verde
- [ ] Commits con prefijo `[TASK-R1-001]`
