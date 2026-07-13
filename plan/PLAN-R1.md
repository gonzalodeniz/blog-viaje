# PLAN-R1 — Release 1 «Cimientos»

Versión 1.0 · 13 de julio de 2026
Especificación de referencia: [SPEC-R1.md](../specs/SPEC-R1.md) v1.0

## 1. Paquetes de trabajo

| WP | Nombre | Requisitos que desarrolla | Depende de | Tamaño |
|---|---|---|---|---|
| WP-R1-1 | Infraestructura, CI y despliegue | RNF-R1-01, RNF-R1-03 (cabeceras), RNF-R1-04, RNF-R1-05 (puertas CI), RNF-R1-06, RNF-R1-07 | — | L |
| WP-R1-2 | Autenticación, sesiones y bloqueo | RF-R1-01, RF-R1-02, RF-R1-03, RF-R1-04, RF-R1-05, RF-R1-06, RF-R1-07, RF-R1-20, RNF-R1-02, RNF-R1-03 (CSRF), RNF-R1-08 | WP-R1-4 (tablas de auth) | L |
| WP-R1-3 | CLI de rescate | RF-R1-08, RF-R1-09, RF-R1-10, RF-R1-11, RF-R1-12 | WP-R1-2 | M |
| WP-R1-4 | Modelo de datos y API de contenido | RF-R1-13, RF-R1-14, RF-R1-15, RF-R1-16, RF-R1-18 (sanitización servidor) | WP-R1-1 (esqueleto) | L |
| WP-R1-5 | Panel de administración y editor | RF-R1-05 (vista de intentos), RF-R1-06 (UI), RF-R1-15, RF-R1-16, RF-R1-17, RF-R1-18, RF-R1-19 (UI) | WP-R1-2, WP-R1-4 | L |
| WP-R1-6 | Vista de lectura | RF-R1-13, RF-R1-14 (UI) | WP-R1-2, WP-R1-4 | M |

Tamaños: S (≤ 2 días) · M (≤ 1 semana) · L (1–2 semanas). Estimación orientativa para una persona.

## 2. Descripción de los paquetes

### WP-R1-1 — Infraestructura, CI y despliegue

Esqueletos de `backend/` (FastAPI + SQLAlchemy + Alembic + pytest) y `frontend/` (Vite + React + TS + Vitest); `deploy/` con `docker-compose.yml` (nginx, backend, worker, postgres, certbot), configuración nginx (TLS, cabeceras RNF-R1-03, rate limiting de `/api/auth/*`), imágenes no root; pipeline de CI con todas las puertas bloqueantes (tests, cobertura ≥ 80 %, bandit/semgrep/pip-audit/npm audit/trivy/gitleaks, `traceability.py --check`); hook `commit-msg` activado (`git config core.hooksPath tools/hooks`); `/healthz` básico.

**Entregable:** `docker compose up -d` sirve un "hola mundo" autenticable por HTTPS y la CI está en verde con todas las puertas activas.

### WP-R1-2 — Autenticación, sesiones y bloqueo

Modelo `users`/`sessions`/`login_attempts`/`account_locks`; Argon2id (RNF-R1-02) con lista local de contraseñas filtradas; login/logout con cookie de sesión (RF-R1-02) y rotación de token; bloqueo con backoff (RF-R1-03/04) con mensajes que no revelan existencia de usuarios; registro de intentos (RF-R1-05); roles (RF-R1-07); cambio de contraseña propio y flujo forzado (RF-R1-20); CSRF (RNF-R1-03); job de purga de sesiones e intentos (RNF-R1-08).

**Entregable:** flujo de autenticación completo verificado por tests unitarios, de integración y e2e (incluido el bloqueo con reloj simulado).

### WP-R1-3 — CLI de rescate

`bitacora-cli` con Typer dentro de la imagen del backend: `reset-password`, `create-user`, `unlock`, `disable`/`enable`, `list-users`, `sessions-revoke`; auditoría con origen `cli` (RF-R1-12); tests de integración que ejercitan los comandos contra PostgreSQL real.

**Entregable:** recuperación total del sistema desde una shell del servidor, demostrada por el e2e `cli-reset`.

### WP-R1-4 — Modelo de datos y API de contenido

Migraciones Alembic del esquema completo de R1 (`topics`, `trips`, `photos` básico, `tags`, `audit_log`); endpoints de lectura (RF-R1-13/14) y CRUD admin de viajes y temas (RF-R1-15/16); sanitización servidor del HTML del editor con lista blanca (RF-R1-18); subida simple de fotos (original + versión web) sobre la estructura de medios de SPEC-MASTER §7.5 para no migrar rutas en R2; autorización por rol en cada endpoint.

**Entregable:** API completa de R1 documentada (OpenAPI) y cubierta por tests de integración.

### WP-R1-5 — Panel de administración y editor

UI del panel: gestión de temas y viajes (RF-R1-15/16), editor TipTap con la barra completa de RF-R1-17, autoguardado (RF-R1-19), vista de intentos de login (RF-R1-05) y revocación de sesiones (RF-R1-06); pantalla de cambio forzado de contraseña (RF-R1-20).

**Entregable:** puedo crear un tema, escribir un viaje con formato completo y publicarlo desde el navegador.

### WP-R1-6 — Vista de lectura

Listado cronológico de viajes y página de artículo con el HTML sanitizado y sus fotos (RF-R1-13/14); diseño responsive; portada limpia con login (sin collage, que llega en R2).

**Entregable:** experiencia de lectura completa tras autenticarse.

## 3. Orden de ejecución y hitos

```
WP-R1-1 ──> WP-R1-4 ──> WP-R1-2 ──> WP-R1-3
                └───────────┴──> WP-R1-5 ──┐
                            └──> WP-R1-6 ──┴──> Hito: release v1.0.0
```

| Hito | Criterio |
|---|---|
| H1 | CI completa en verde sobre esqueletos desplegables (fin WP-R1-1) |
| H2 | Autenticación + CLI de rescate cerradas con e2e (fin WP-R1-3) |
| H3 | Contenido de extremo a extremo: crear, escribir, publicar, leer (fin WP-R1-6) |
| H4 | DoD de SPEC-R1 §5 completo → tag `v1.0.0` |

## 4. Riesgos

| Riesgo | Mitigación |
|---|---|
| La CSP estricta sin `unsafe-inline` choca con los estilos inline que genera TipTap | Sanitizar a clases/atributos permitidos en servidor y decidir pronto (spike en WP-R1-4); si hay que relajar CSP, documentarlo en un ADR |
| Cobertura ≥ 80 % en ramas difícil en el frontend del editor | Diseñar el editor como extensiones TipTap pequeñas y testeables con Vitest desde el principio |
| El bloqueo con backoff depende de tiempo | Reloj inyectable en el servicio de auth; tests con tiempo simulado, no con sleeps |
