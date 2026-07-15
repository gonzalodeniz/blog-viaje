# TODO

Estado de avance de Bitácora. Fuente de verdad detallada: `specs/`, `plan/`, `tasks/`; este fichero es un resumen de trabajo, no sustituye a la matriz de trazabilidad (`docs/TRACEABILITY.md`).

## Especificación y andamiaje SDD

- [x] `specs/SPEC-MASTER.md` v1.1 (visión, alcance, arquitectura, seguridad completos)
- [x] `specs/SPEC-R1.md` (congelada), `specs/SPEC-R2.md` y `specs/SPEC-R3.md` (borrador)
- [x] `specs/adr/ADR-001-stack-tecnologico.md`
- [x] `plan/PLAN-R1.md` con los 6 paquetes de trabajo (WP-R1-1…6)
- [x] `tasks/TEMPLATE.md` y primera tarea ejecutable (`TASK-R1-001`)
- [x] `tools/traceability.py` (genera y valida `docs/TRACEABILITY.md`) y hook `commit-msg`
- [x] `CLAUDE.md`, `README.md`, `.gitignore`, `.env.example`
- [ ] `plan/PLAN-R2.md` y `plan/PLAN-R3.md` (paquetes de trabajo de R2/R3)

## Release R1 — Cimientos

### WP-R1-1 — Infraestructura, CI y despliegue

- [x] `TASK-R1-001`: esqueleto de backend (FastAPI/SQLAlchemy/Alembic/pytest), frontend (Vite/React 18/TS/Vitest) y `docker-compose.yml` (nginx + backend + postgres); `/healthz`; verificado extremo a extremo
- [x] `TASK-R1-002`: pipeline de CI (`.github/workflows/ci.yml`) — cobertura ≥ 80 % bloqueante en backend/frontend, bandit/semgrep/pip-audit/npm audit/trivy/gitleaks, `traceability.py --check --release R1` (bloqueante; en rojo hasta que el resto de WPs de R1 cierren su trazabilidad)
- [x] `TASK-R1-003`: TLS (Let's Encrypt/certbot con `deploy/scripts/init-letsencrypt.sh`), cabeceras de seguridad (CSP, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy — RNF-R1-03/04), rate limiting de `/api/auth/*`; verificado con certificado autofirmado (sin dominio real disponible en este entorno)
- [ ] Imágenes con sistema de archivos de solo lectura donde sea posible (RNF-R1-07)

### WP-R1-2 — Autenticación, sesiones y bloqueo

- [ ] Modelo `users` / `sessions` / `login_attempts` / `account_locks` (Alembic)
- [ ] Login/logout, cookies de sesión (RF-R1-02), Argon2id (RNF-R1-02)
- [ ] Bloqueo temporal con backoff exponencial (RF-R1-03/04)
- [ ] Registro de intentos de login (RF-R1-05)
- [ ] Roles `admin`/`lector` (RF-R1-07)
- [ ] Cambio de contraseña propio y flujo forzado (RF-R1-20)
- [ ] CSRF en mutaciones (RNF-R1-03)
- [ ] Job de purga de sesiones/intentos (RNF-R1-08)

### WP-R1-3 — CLI de rescate

- [ ] `bitacora-cli reset-password` (RF-R1-09)
- [ ] `bitacora-cli create-user` (RF-R1-10)
- [ ] `bitacora-cli unlock` / `list-users` (RF-R1-11)
- [ ] `bitacora-cli disable` / `enable` / `sessions-revoke`
- [ ] Auditoría de acciones de la CLI (RF-R1-12)

### WP-R1-4 — Modelo de datos y API de contenido

- [ ] Migraciones Alembic de `topics`, `trips`, `photos` (básico), `tags`, `audit_log`
- [ ] Endpoints de lectura: listado y artículo (RF-R1-13/14)
- [ ] CRUD admin de viajes y temas (RF-R1-15/16)
- [ ] Sanitización servidor del HTML del editor (RF-R1-18)
- [ ] Subida simple de fotos (original + versión web)

### WP-R1-5 — Panel de administración y editor

- [ ] UI de gestión de temas y viajes (RF-R1-15/16)
- [ ] Editor TipTap con la barra completa (RF-R1-17)
- [ ] Autoguardado de borradores (RF-R1-19)
- [ ] Vista de intentos de login y revocación de sesiones (RF-R1-05/06)
- [ ] Pantalla de cambio forzado de contraseña (RF-R1-20)

### WP-R1-6 — Vista de lectura

- [ ] Listado cronológico de viajes (RF-R1-13)
- [ ] Página de artículo con HTML sanitizado y fotos (RF-R1-14)
- [ ] Portada limpia con login (sin collage, llega en R2)

## Release R2 — Fotografía (borrador, sin planificar)

- [ ] `plan/PLAN-R2.md`
- [ ] Collage público en portada/login (RF-R2-01…04)
- [ ] Lightbox y lazy loading (RF-R2-05/06)
- [ ] Inserción y redimensionado de fotos en el editor (RF-R2-07)
- [ ] Subida masiva y biblioteca de fotos (RF-R2-08…10)
- [ ] Pipeline de imágenes: variantes, EXIF, deduplicación, estructura de carpetas (RF-R2-11…15)
- [ ] `bitacora-cli regenerate-derived`

## Release R3 — Descubrimiento (borrador, sin planificar)

- [ ] `plan/PLAN-R3.md`
- [ ] Búsqueda full-text en español (RF-R3-01)
- [ ] Filtros por tema/año/etiqueta y archivo cronológico (RF-R3-02)
- [ ] Viajes relacionados (RF-R3-03) y mapa opcional (RF-R3-04)
- [ ] Accesibilidad WCAG 2.1 AA (RNF-R3-01)
- [ ] Backups automatizados y restauración ensayada (RNF-R3-03)
- [ ] Observabilidad: `/healthz`/`/readyz`, logs JSON, métricas (RNF-R3-04)
- [ ] PWA
