# TASK-R1-015 — Cambio de contraseña propio y flujo forzado tras reset

- **WP:** WP-R1-2
- **Requisitos:** RF-R1-20
- **Estado:** pendiente <!-- pendiente | en curso | cerrada -->
- **Rama:** feature/TASK-R1-015

## Objetivo

Existe `POST /api/auth/change-password` (requiere sesión válida, contraseña actual y nueva), y `must_change_password=True` (ya lo pone `bitacora-cli reset-password`, TASK-R1-011) bloquea cualquier otro endpoint autenticado hasta que el usuario cambie su contraseña. El cambio de contraseña revoca el resto de sesiones del usuario (deja viva solo la que hizo el cambio).

## Contexto y decisiones

- **La mitad ya existe:** `must_change_password` está en `User` desde TASK-R1-007 y `reset_password()` (TASK-R1-011) ya lo activa; lo que falta es (a) el endpoint que permite cambiarla y (b) que ese flag realmente bloquee algo — hoy no lo comprueba nadie, un usuario con `must_change_password=True` puede seguir usando la sesión con la contraseña temporal indefinidamente.
- **Verificación de contraseña actual:** usa `verify_password` (ya existe en `app/core/security.py`); si no coincide, 401 (mensaje genérico, no hace falta el cuidado de timing de RF-R1-04 aquí — ya hay sesión válida, no es un intento de login que pueda enumerar usuarios).
- **Política de contraseña:** `validate_password_policy` (ya existe) aplica a la nueva contraseña.
- **Bloqueo por `must_change_password`:** se añade una comprobación en `get_current_user` (`app/api/deps.py`) — si el usuario tiene el flag activo, cualquier endpoint que no sea `POST /api/auth/change-password` ni `POST /api/auth/logout` devuelve 403 con un código/mensaje reconocible (p. ej. `{"detail": "changePasswordRequired"}`) para que el frontend (WP-R1-5, fuera de esta tarea) pueda mostrar la pantalla intermedia obligatoria que pide RF-R1-20. Sin frontend en R1 todavía, esta tarea deja el backend listo y lo cubre con tests de API.
- **Revocación del resto de sesiones tras el cambio:** reutiliza el mismo patrón que `rescue_cli.revoke_sessions`, pero conservando viva la sesión actual (la que acaba de autenticar el cambio) — a diferencia de la CLI, que revoca todas sin excepción porque no hay "sesión actual" en una shell.
- **Fuera de alcance:** pantalla de UI del flujo forzado (WP-R1-5).

## Definition of Done

- [ ] Código con docstring `Implementa: RF-R1-20` en los módulos que materializan el requisito
- [ ] Tests con `@pytest.mark.spec("RF-R1-20")`: cambio correcto revoca el resto de sesiones y mantiene la actual, contraseña actual incorrecta devuelve 401, nueva contraseña que incumple la política devuelve 400, `must_change_password=True` bloquea otros endpoints hasta cambiarla, tras cambiarla el flag pasa a `False` — contra PostgreSQL real
- [ ] Cobertura ≥ 80 % en el código tocado
- [ ] Revisión de seguridad (checklist OWASP)
- [ ] `python tools/traceability.py --check` en verde
- [ ] Commits con prefijo `[TASK-R1-015]`
