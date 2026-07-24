# TASK-R1-011 — CLI de rescate: alta, reset y gestión de usuarios

- **WP:** WP-R1-3
- **Requisitos:** RF-R1-08, RF-R1-09, RF-R1-10, RF-R1-11, RF-R1-12
- **Estado:** pendiente <!-- pendiente | en curso | cerrada -->
- **Rama:** feature/TASK-R1-011

## Objetivo

`bitacora-cli` (ya existe como esqueleto Typer, `backend/app/cli/main.py`) gana los comandos `create-user`, `reset-password`, `unlock`, `disable`/`enable`, `list-users` y `sessions-revoke`, cada uno registrando su acción en `audit_log` con `actor="cli"`. Con esto, un operador con shell en el servidor (`docker compose exec backend bitacora-cli <cmd>`) puede recuperar el control total del sistema sin pasar por HTTP, incluso si las credenciales de admin se han perdido.

## Contexto y decisiones

- **Alcance exacto por requisito:**
  - RF-R1-08: ya se cumple por construcción (la CLI vive dentro de la imagen del backend, sin exponerse por HTTP); esta tarea no añade nada nuevo para él, solo lo mantiene.
  - RF-R1-09 `reset-password <usuario>`: genera una contraseña temporal aleatoria segura (usa `secrets.token_urlsafe` o equivalente, no un PRNG débil), la muestra **una única vez** por stdout, la hashea con `hash_password` (Argon2id, ya existe en `app/core/security.py`) y pone `must_change_password=True`. Si el usuario no existe, error claro por stderr y código de salida distinto de 0 (aquí sí se puede revelar la existencia del usuario: es una herramienta de servidor con shell, no la superficie web de RF-R1-04).
  - RF-R1-10 `create-user <usuario> [--admin]`: si el usuario no existe, lo crea; si existe pero está `disabled`, lo rehabilita (`disabled=False`). Contraseña interactiva (`typer.prompt(..., hide_input=True, confirmation_prompt=True)`), validada con `validate_password_policy` (ya existe). Rol `admin` si se pasa `--admin`, si no `lector`.
  - RF-R1-11 `unlock <usuario>` y `list-users`: ver nota siguiente sobre `account_locks`, es la parte no trivial de esta tarea.
  - RF-R1-12: cada comando que muta estado (`create-user`, `reset-password`, `unlock`, `disable`, `enable`, `sessions-revoke`) escribe una fila en `audit_log` (`actor="cli"`, `action="<comando>"`, `entity="user"`, `entity_id=<username o id>`) usando el modelo ya existente (`app/models/audit_log.py`). `list-users` es de solo lectura y no audita.

- **`account_locks` no existe todavía — decisión de diseño clave de esta tarea.** RF-R1-03 (bloqueo temporal tras 5 fallos) y RF-R1-05 (registro de intentos) se dejaron explícitamente fuera de TASK-R1-007 ("no dejar tablas sin lógica que las use") y siguen sin implementarse: no hay tabla `account_locks` ni `login_attempts`, y el flujo de login (`app/services/auth.py`) no bloquea nada todavía. RF-R1-11 exige un comando `unlock` y que `list-users` muestre el estado de bloqueo, así que esta tarea **sí crea la tabla `account_locks`** (migración Alembic, esquema mínimo de SPEC-MASTER §7.3: `id`, `username`, `locked_until`, `consecutive_locks`, `created_at`) porque es el único escritor/lector que la necesita por ahora. El *enforcement* real del bloqueo en el login (RF-R1-03/04 completo, incrementar `consecutive_locks` tras 5 fallos, backoff exponencial) queda fuera de esta tarea — es WP-R1-2 y necesita su propia TASK. `unlock` simplemente borra/expira cualquier fila de `account_locks` para ese usuario (operación idempotente: no falla si no había bloqueo). Esto es una limitación conocida y documentada: hasta que exista esa tarea de WP-R1-2, `account_locks` nunca tendrá filas en producción y `unlock`/el estado "bloqueado" de `list-users` no tendrán nada que hacer — pero la CLI queda lista para cuando la tenga.
- **`disable <usuario>` / `enable <usuario>`:** no están en la tabla de requisitos de `SPEC-R1.md` (que solo lista `unlock`/`list-users` para RF-R1-11) pero sí en el listado de comandos de `SPEC-MASTER §10` y en el entregable de WP-R1-3 (`plan/PLAN-R1.md`). Se implementan aquí como parte natural de RF-R1-11 (gestión de usuarios): togglean `User.disabled`.
- **`sessions-revoke <usuario>`:** tampoco en la tabla RF de `SPEC-R1.md` pero sí en `SPEC-MASTER §10`/plan; marca `revoked=True` en todas las sesiones activas (`Session`, ya existe) del usuario. Útil como parte del "control total" del objetivo de WP-R1-3 (p. ej. tras un `reset-password` de emergencia, cerrar cualquier sesión que pudiera estar comprometida).
- **`list-users`:** tabla por stdout (usuario, rol, `disabled`, bloqueado hasta si aplica, `last_login_at`). Sin paginación ni filtros: para R1 el número de usuarios es pequeño (blog personal/familiar).
- **Contraseña temporal nunca en logs ni en `audit_log.detail`:** el registro de auditoría de `reset-password` no incluye la contraseña generada, solo que se generó una (RNF-R1-08, CLAUDE.md — logs sin contraseñas).
- **Tests de integración contra PostgreSQL real** (como marca el entregable de WP-R1-3 en `plan/PLAN-R1.md`), usando `CliRunner` de Typer + la misma fixture de BD que ya usan `backend/tests/test_api_auth.py` / `test_auth_service.py`. No se puede probar de extremo a extremo con Docker en esta sesión igual que en TASK-R1-010 (pyvips); aquí no hace falta: la CLI no depende de `libvips`, así que sí se puede ejecutar y testear directamente en el entorno de desarrollo local.
- **Fuera de alcance:** `regenerate-derived` (CLI de R2, depende del pipeline de imágenes avanzado), enforcement real del bloqueo en el login (RF-R1-03/04, WP-R1-2), registro de intentos de login (RF-R1-05, WP-R1-2), purga periódica de sesiones expiradas (RNF-R1-08, worker).

## Definition of Done

- [ ] Código con docstring `Implementa: RF-R1-08, RF-R1-09, RF-R1-10, RF-R1-11, RF-R1-12` en los módulos que materializan los requisitos
- [ ] Migración Alembic para `account_locks`
- [ ] Tests con `@pytest.mark.spec("...")` para cada comando (alta, rehabilitación, reset con contraseña de un solo uso, unlock idempotente, disable/enable, sessions-revoke, list-users, y que cada mutación deja fila en `audit_log` con `actor="cli"`) contra PostgreSQL real
- [ ] Cobertura ≥ 80 % en el código tocado
- [ ] Revisión de seguridad (checklist OWASP aplicable al cambio; verificar que la contraseña temporal no queda en logs/auditoría)
- [ ] `python tools/traceability.py --check` en verde
- [ ] Commits con prefijo `[TASK-R1-011]`
