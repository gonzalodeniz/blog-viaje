# TASK-R1-004 — Sistema de ficheros de solo lectura en los contenedores

- **WP:** WP-R1-1
- **Requisitos:** RNF-R1-07
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-004

## Objetivo

Los contenedores `backend` y `nginx` corren con `read_only: true` en `docker-compose.yml`, montando únicamente los `tmpfs` estrictamente necesarios para sus directorios de escritura en caliente, sin perder funcionalidad ni healthchecks.

## Contexto y decisiones

- TASK-R1-001 ya dejó usuario no root en ambos Dockerfiles y aplazó explícitamente "read-only FS, healthchecks" a una tarea posterior del WP-R1-1 (ver `tasks/R1/TASK-R1-001.md`); esta tarea cierra esa deuda.
- `postgres` y `certbot` quedan fuera de alcance: la imagen oficial de `postgres:16-alpine` necesita escritura continua en `PGDATA` (ya aislado en el volumen `pgdata`, no en el FS de la imagen) y `certbot` escribe certificados en el volumen `letsencrypt`; forzar `read_only` en ambos no aporta superficie de ataque adicional relevante y complica la renovación. Se puede revisar en una tarea futura si aparece necesidad concreta.
- `backend`: solo necesita `/tmp` en `tmpfs` (ficheros temporales de subida/proceso puntual); se añade `PYTHONDONTWRITEBYTECODE=1` para que no intente escribir `.pyc` en el árbol de la imagen (que ahora es de solo lectura).
- `nginx`: necesita `tmpfs` en `/var/cache/nginx`, `/var/run` (pid), `/tmp` y `/etc/nginx/conf.d`. Este último no era obvio: el `docker-entrypoint.d` oficial de la imagen hace `envsubst` de la plantilla y escribe `default.conf` ahí en cada arranque; sin ese `tmpfs` el contenedor fallaba (`Exited (1)`, "Read-only file system") — se detectó en la verificación manual, no en el diseño inicial.
- Verificado manualmente con `docker compose --env-file .env -f deploy/docker-compose.yml up -d` (postgres + backend, y nginx con un certificado autofirmado como en TASK-R1-003): los tres contenedores quedan `healthy`/`Up`, `curl -k https://localhost/healthz` devuelve 200 con las cinco cabeceras, `curl http://localhost/` responde 301, y se confirmó por `exec ... touch` que backend y nginx rechazan escritura fuera de sus `tmpfs` (`Read-only file system`) tanto en `/app` como en los estáticos servidos (`/usr/share/nginx/html`).

## Definition of Done

- [x] Código con docstring/comentario `Implementa: RNF-R1-07` en `deploy/docker-compose.yml`
- [x] Test de humo: `docker compose up -d` con `read_only: true` activo → healthchecks de `backend` y `nginx` en verde, `curl -k https://localhost/healthz` devuelve 200
- [x] Cobertura ≥ 80 % en el código tocado (no aplica: cambio de infraestructura sin código Python/TS; sin regresión en la cobertura existente)
- [x] Revisión de seguridad (superficie de escritura minimizada a los `tmpfs` estrictamente necesarios; sin secretos ni datos persistentes en los `tmpfs`)
- [ ] `python tools/traceability.py --check --release R1` en verde — sigue en rojo (ver TASK-R1-002/003): quedan RF/RNF de otros WPs de R1 sin test, incluyendo RNF-R1-04 (TASK-R1-003, sin test de spec propio por ser TLS de infraestructura) y RNF-R1-07 (esta tarea, hardening de infraestructura sin test de spec propio); nada de esto es atribuible a TASK-R1-004
- [x] Commits con prefijo `[TASK-R1-004]`

## Notas de implementación

- `deploy/docker-compose.yml`: `read_only: true` + `tmpfs` en los servicios `backend` y `nginx`; sin cambios en `postgres` ni `certbot`.
- `nginx` necesita `/etc/nginx/conf.d` también en `tmpfs` (ver nota de verificación arriba), no solo `/var/cache/nginx`, `/var/run` y `/tmp`.
