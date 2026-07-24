# TASK-R1-016 — Worker mínimo: purga periódica de sesiones y login_attempts

- **WP:** WP-R1-2
- **Requisitos:** RNF-R1-08
- **Estado:** pendiente <!-- pendiente | en curso | cerrada -->
- **Rama:** feature/TASK-R1-016
- **Depende de:** TASK-R1-012 (crea `login_attempts`, sin la cual no hay nada que purgar)

## Objetivo

Existe un servicio `worker` en `deploy/docker-compose.yml` (imagen del backend, mismo código, sin exponer puerto) que cada cierto intervalo borra sesiones expiradas/revocadas y purga `login_attempts` más antiguos que `login_attempts_retention_days` (ya existe en `Settings`, sin usar todavía). Es el primer uso real del contenedor `worker` que el plan de WP-R1-1 ya reservaba en el diagrama de arquitectura pero que ninguna tarea había creado hasta ahora.

## Contexto y decisiones

- **Gap descubierto al planificar esta tarea:** `plan/PLAN-R1.md` y `specs/SPEC-MASTER.md` mencionan un servicio `worker` en `docker-compose.yml` desde el diseño de WP-R1-1, pero `deploy/docker-compose.yml` (TASK-R1-001..004) solo define `postgres`, `backend`, `nginx`, `certbot` — nunca se llegó a añadir. Esta tarea es la primera que necesita que exista, así que lo crea aquí en vez de abrir una tarea de infraestructura separada solo para el esqueleto vacío.
- **Alcance deliberadamente mínimo:** un único proceso Python de larga duración (`app.worker.main`, mismo entrypoint style que `app.cli.main`) con un bucle `while True: purge(); sleep(intervalo)`. **No** es la cola de trabajos en PostgreSQL de SPEC-MASTER §"Trabajos en segundo plano" (esa cola es para el pipeline de variantes de imagen, RF-R2-12/13, y se construye en R2 cuando haga falta encolar de verdad). Para una purga periódica no hace falta cola: es un job programado, no trabajo bajo demanda.
- **Qué purga exactamente:**
  - `sessions` con `revoked=True` o `expires_at`/`absolute_expires_at` en el pasado (limpieza de basura; no afecta a RF-R1-02, que ya trata esas sesiones como inválidas aunque sigan en la tabla).
  - `login_attempts` con `created_at` más antiguo que `login_attempts_retention_days` (ya configurable en `Settings`, RNF-R1-08 exige retención ≥ 90 días).
  - `audit_log` **no se purga nunca** — RNF-R1-08 dice explícitamente "permanente".
- **Intervalo:** una vez al día es suficiente (no es una tabla de alto volumen en un blog personal); configurable por variable de entorno con un valor por defecto razonable, sin exponerlo como requisito de spec.
- **`docker-compose.yml`:** el nuevo servicio `worker` reutiliza la misma imagen que `backend` (mismo `Dockerfile`), `read_only: true` igual que el resto, sin puertos publicados, con las mismas variables de entorno de conexión a PostgreSQL.
- **Fuera de alcance:** cola de trabajos en PostgreSQL para el pipeline de imágenes (R2), cualquier UI que muestre el estado del worker.

## Definition of Done

- [ ] Código con docstring `Implementa: RNF-R1-08` en los módulos que materializan el requisito
- [ ] Servicio `worker` añadido a `deploy/docker-compose.yml`
- [ ] Tests con `@pytest.mark.spec("RNF-R1-08")`: purga sesiones expiradas/revocadas, purga `login_attempts` por retención, no toca `audit_log`, no purga sesiones/intentos dentro de la ventana de retención — contra PostgreSQL real
- [ ] Cobertura ≥ 80 % en el código tocado
- [ ] Revisión de seguridad (checklist OWASP; confirmar que el worker no expone ningún puerto ni endpoint)
- [ ] `python tools/traceability.py --check` en verde
- [ ] Commits con prefijo `[TASK-R1-016]`
