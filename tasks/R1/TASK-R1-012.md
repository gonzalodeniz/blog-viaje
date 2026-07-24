# TASK-R1-012 — Bloqueo temporal por intentos fallidos y registro de intentos de login

- **WP:** WP-R1-2
- **Requisitos:** RF-R1-03, RF-R1-04, RF-R1-05
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-012

## Objetivo

`app.services.auth.authenticate` bloquea una cuenta tras 5 fallos consecutivos en 15 minutos (backoff exponencial 15→30→60 min), el endpoint `POST /api/auth/login` informa del tiempo restante de bloqueo sin revelar si el usuario existe, y cada intento (éxito, fallo, bloqueo) queda registrado en una tabla `login_attempts` consultable después desde el panel de administración (RF-R1-05; el propio panel es WP-R1-5, fuera de esta tarea).

## Contexto y decisiones

- **Ya existe la mitad del terreno:** `app.models.account_lock.AccountLock` (TASK-R1-011) ya tiene el esquema exacto que describe SPEC-MASTER §8 (`username`, `locked_until`, `consecutive_locks`) y `bitacora-cli unlock` ya sabe borrar sus filas. Esta tarea es la que por fin **escribe** en esa tabla desde el flujo de login real; hasta ahora estaba vacía en producción.
- **Falta crear `login_attempts`** (no existe todavía): columnas mínimas de SPEC-MASTER §7.3 — `id`, `username_claimed`, `succeeded`, `ip`, `user_agent`, `created_at`. Es el escritor de RF-R1-05; el lector (vista de panel) es WP-R1-5.
- **Dónde vive la lógica:** `authenticate()` en `app/services/auth.py` es el único punto que ya decide éxito/fracaso; ahí se añade la comprobación de bloqueo (antes de verificar contraseña) y el registro del intento (después). Mantiene la invariante de RF-R1-04: tiempo de respuesta equivalente ya cubierto por `verify_dummy_password()` para usuario inexistente — el bloqueo no debe reintroducir una fuga de timing (comprobar `account_locks` es una consulta indexada por `username`, coste comparable exista o no la cuenta).
- **RF-R1-04 completo:** el mensaje de bloqueo sigue siendo genérico en cuanto a "por qué" (no dice si el usuario existe), pero **sí** puede incluir el tiempo restante (`locked_until`), porque eso no revela nada sobre la existencia de la cuenta — cualquier `username_claimed`, exista o no, puede acumular intentos y bloquearse igual (los intentos se cuentan por username declarado, no por usuario real).
- **Reinicio del contador:** un login correcto pone `consecutive_locks` a 0 (se borra la fila de `account_locks`, igual que hace `unlock`); la ventana de 15 min expira sola por `locked_until`.
- **Rate limiting de nginx por IP** (mencionado en SPEC-MASTER §8 como defensa complementaria) ya está cubierto por TASK-R1-003 (WP-R1-1) — no se toca aquí.
- **Fuera de alcance:** vista de panel para consultar `login_attempts`/intentos (WP-R1-5), purga automática de `login_attempts` por retención (RNF-R1-08, TASK-R1-016 — necesita el worker).
- **`login_attempts.result` es un enum de 3 valores (`success`/`failure`/`locked`), no un booleano `succeeded`** como se anticipaba al formalizar la tarea: RF-R1-05 pide distinguir explícitamente "éxito, fallo, bloqueo", y un booleano no puede representar el tercer estado.
- **El contador de fallos consecutivos se cuenta directamente sobre `login_attempts`** (no sobre un campo aparte), filtrando por ventana de 15 min y, si hubo un éxito previo, estrictamente posterior a él — tal y como describe SPEC-MASTER §8 ("el contador se evalúa sobre login_attempts").
- **Bug real encontrado al verificar de extremo a extremo con la sesión de BD real (no la fixture de test):** `authenticate()` solo hacía `flush()` al registrar el intento fallido y actualizar `account_locks`; el endpoint de login lanza `HTTPException(401)` justo después, que FastAPI propaga a través de la dependencia `get_db` — cuyo `except Exception: db.rollback()` deshacía ambos cambios. En producción, **el bloqueo nunca habría llegado a activarse**: cada intento fallido se registraba y se revertía en la misma petición. Corregido con un `db.commit()` explícito en las ramas de fallo/bloqueo de `authenticate()` (el registro de auditoría debe sobrevivir a la petición que falla), cubierto con un test de regresión que usa `SessionLocal`/`TestClient` reales, sin overrides.

## Definition of Done

- [x] Código con docstring `Implementa: RF-R1-03, RF-R1-04, RF-R1-05` en los módulos que materializan los requisitos
- [x] Migración Alembic para `login_attempts`
- [x] Tests con `@pytest.mark.spec("...")`: backoff exponencial (15→30→60, tope), reinicio de contador con login correcto, expiración de ventana de 15 min, mensaje de bloqueo sin revelar existencia de usuario, registro de éxito/fallo/bloqueo en `login_attempts` con IP y user-agent, regresión de la sesión real — contra PostgreSQL real (180 tests en total, todos en verde)
- [x] Cobertura ≥ 80 % en el código tocado (`app/services/auth.py` 98 %; suite completa 98.68 %)
- [x] Revisión de seguridad: `bandit` sin hallazgos; verificado que el mensaje de bloqueo no revela existencia de usuario (mismo 401 genérico salvo el tiempo restante) ni reintroduce fuga de timing (la comprobación de `account_locks` ocurre antes de saber si el usuario existe, para ambas ramas)
- [x] `python tools/traceability.py --check` en verde para RF-R1-03/04/05 específicamente (el comando global sigue en rojo por el resto de huecos ya documentados: RF-R1-06/17/19/20, RNF-R1-04/08, y el `Initial commit`)
- [x] Commits con prefijo `[TASK-R1-012]`
