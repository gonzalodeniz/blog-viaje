# TASK-R1-007 — Autenticación mínima: login/logout con sesión de cookie

- **WP:** WP-R1-2
- **Requisitos:** RF-R1-01, RF-R1-02, RF-R1-04 (parcial), RNF-R1-02 (parcial), RNF-R1-03 (CSRF, parcial)
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-007

## Objetivo

Existe un mecanismo real de autenticación (usuario/contraseña → cookie de sesión) que los endpoints de WP-R1-4 pueden exigir vía una dependencia `get_current_user`. No es el WP-R1-2 completo: es el corte mínimo necesario para no violar la regla de "privado por defecto" de CLAUDE.md al construir los endpoints de lectura/CRUD/subida de fotos que quedan en WP-R1-4.

## Contexto y decisiones

- **Por qué esto ahora y no WP-R1-4 completo directamente:** `plan/PLAN-R1.md` ordena `WP-R1-1 → WP-R1-4 → WP-R1-2`, pero WP-R1-4 solo puede completar su parte de modelo de datos y sanitización sin auth (TASK-R1-005/006). Los endpoints que quedan de WP-R1-4 (lectura, CRUD admin, subida de fotos) exigen autenticación real por regla no negociable del proyecto ("cualquier endpoint... requiere autenticación salvo que un RF diga lo contrario"). En vez de construirlos sin auth (inseguro) o esperar a WP-R1-2 completo (bloquea todo WP-R1-4 indefinidamente), se adelanta este slice mínimo, documentado como tarea de WP-R1-2 (no de WP-R1-4) para mantener la trazabilidad correcta.
- **Esquema de `users`/`sessions`:** se crean con el esquema completo ya fijado por SPEC-MASTER §7.3 (`users(id, username UNIQUE, password_hash, role, must_change_password, disabled, created_at, last_login_at)`, `sessions(id, user_id, token_hash, expires_at, absolute_expires_at, last_seen_at, revoked, created_at, ip)`), igual que TASK-R1-005 creó `trips`/`photos` con todas las columnas del esquema aunque no toda la lógica estuviera implementada todavía. `role` y `must_change_password` existen como columnas pero **no se aplican** en este slice (RF-R1-07 y RF-R1-20 llegan en una tarea posterior de WP-R1-2).
- **`login_attempts` / `account_locks`: fuera de alcance.** El bloqueo con backoff (RF-R1-03) y el registro de intentos (RF-R1-05) necesitan sus propias tablas y su propia tarea; no se crean aquí para no dejar tablas sin lógica que las use.
- **RF-R1-04 (mensajes que no revelan existencia de usuario): cubierto parcialmente.** El endpoint de login devuelve siempre el mismo mensaje genérico y el mismo código de estado tanto si el usuario no existe como si la contraseña es incorrecta o la cuenta está deshabilitada, incluyendo un tiempo de respuesta equivalente (se ejecuta una verificación Argon2id contra un hash señuelo cuando el usuario no existe, para no filtrar la diferencia por timing). Lo que queda fuera es la parte de "tiempo restante de bloqueo" (RF-R1-03/04 completo), porque no hay bloqueo todavía.
- **RNF-R1-02 (Argon2id): cubierto parcialmente.** Se implementa Argon2id con los parámetros mínimos de la spec (≥ 19 MiB, 2 iteraciones, paralelismo 1) y la longitud mínima de 12 caracteres. La comprobación contra una lista local de contraseñas filtradas se deja para la tarea que implemente el cambio de contraseña (RF-R1-20) o la creación de usuarios por CLI (RF-R1-10, WP-R1-3), que es donde de verdad se fijan contraseñas nuevas.
- **RNF-R1-03 (CSRF): cubierto parcialmente.** Patrón de cookie de doble envío (`csrf_token` no-`HttpOnly` + cabecera `X-CSRF-Token`) para las mutaciones que dependen de la cookie de sesión; se aplica a `/api/auth/logout` y queda lista para que la reutilicen los endpoints de CRUD admin de WP-R1-4. El login no requiere CSRF (no hay sesión previa que proteger). Las cabeceras de seguridad de nginx (CSP, HSTS...) ya están cubiertas por WP-R1-1/RNF-R1-03 y no cambian aquí.
- **`sessions.remember` (columna añadida, no está en el boceto de SPEC-MASTER §7.3):** el boceto de esquema no incluye una columna para recordar si el login se hizo con "remember me". Sin ella, la renovación deslizante de `expires_at` en cada petición no podría saber si usar el TTL corto (24 h) o el largo (30 días, configurable), y una sesión sin "remember me" se comportaría como si lo tuviera tras la primera renovación. Se añade `remember BOOLEAN` a `sessions` para que la renovación use el TTL correcto; es un detalle de implementación, no cambia ningún RF.
- **Sin forma de crear un usuario todavía:** `bitacora-cli create-user` es RF-R1-10, asignado a WP-R1-3 (que depende de WP-R1-2). Hasta que exista, la única manera de tener un usuario es insertarlo directamente en BD (así lo hacen los tests, vía fixture). Se documenta como limitación conocida: no se puede desplegar login en producción hasta WP-R1-3.
- **Bug corregido en `app/db/session.py`:** `get_db()` no hacía `commit()` al final de la petición, así que ningún endpoint que escribiera datos a través de esta dependencia los habría persistido de verdad (la sesión se cerraba y el `rollback` implícito de SQLAlchemy deshacía los cambios). No se había detectado porque hasta ahora ningún endpoint escribía en BD. Se corrige aquí porque login/logout son los primeros que sí lo hacen.
- **Fuera de alcance:** bloqueo/backoff (RF-R1-03), registro de intentos (RF-R1-05), revocación de todas las sesiones de un usuario desde panel (RF-R1-06), roles/autorización (RF-R1-07), cambio de contraseña propio y flujo forzado (RF-R1-20), CLI de rescate (WP-R1-3), purga periódica de sesiones expiradas (RNF-R1-08, necesita el worker).

## Definition of Done

- [x] Código con docstring `Implementa: RF-R1-01, RF-R1-02, RF-R1-04, RNF-R1-02, RNF-R1-03` en los módulos afectados
- [x] Tests con `@pytest.mark.spec("...")`: constraints de `users`/`sessions` contra PostgreSQL real; hashing/política de contraseña; expiración deslizante y absoluta de sesión; login/logout de extremo a extremo vía `TestClient` (credenciales correctas/incorrectas/usuario inexistente/cuenta deshabilitada, todas con la misma respuesta); cookies con los flags correctos; CSRF exigido en logout (94 tests en total, todos en verde)
- [x] Cobertura ≥ 80 % en el código tocado (97.73 % total del backend)
- [x] Revisión de seguridad: sin contraseñas/tokens en logs; token de sesión de 256 bits, hasheado (SHA-256) en BD, nunca en claro; cookies `HttpOnly`/`Secure`/`SameSite=Lax`; mensaje de login genérico y de tiempo equivalente (verificado con test de timing no estricto); bandit sin hallazgos
- [x] `python tools/traceability.py --check --release R1` — sigue en rojo (quedan endpoints y otros WPs sin test, más el commit "Initial commit" de la LICENSE inicial del repo, anterior a la convención SDD), no bloquea esta tarea
- [x] Commits con prefijo `[TASK-R1-007]`

## Notas de implementación

- `backend/app/models/user.py`, `backend/app/models/session.py`.
- `backend/app/core/security.py`: `hash_password`/`verify_password` (Argon2id), `validate_password_policy`.
- `backend/app/core/csrf.py`: generación/verificación del token de doble envío.
- `backend/app/services/auth.py`: `authenticate`, `create_session`, `resolve_session`, `revoke_session`.
- `backend/app/api/deps.py`: `get_current_user`, `require_csrf`.
- `backend/app/api/auth.py`: `POST /api/auth/login`, `POST /api/auth/logout`.
