# TASK-R1-014 — Revocar todas las sesiones de un usuario desde el panel de administración

- **WP:** WP-R1-2
- **Requisitos:** RF-R1-06
- **Estado:** pendiente <!-- pendiente | en curso | cerrada -->
- **Rama:** feature/TASK-R1-014

## Objetivo

Existe `POST /api/admin/users/{username}/sessions/revoke`, que revoca todas las sesiones activas de un usuario distinto del que hace la petición (un admin puede cerrar de golpe todas las sesiones de cualquier cuenta, no solo la propia). El "cierre de sesión manual" de la propia sesión ya existe (`POST /api/auth/logout`, TASK-R1-007); esta tarea es la mitad que faltaba de RF-R1-06.

## Contexto y decisiones

- **Reutiliza lógica ya escrita:** `app.services.rescue_cli.revoke_sessions(db, username)` (TASK-R1-011) ya hace exactamente esto para `bitacora-cli sessions-revoke`. El endpoint HTTP es una capa fina sobre la misma función — no se duplica la lógica de negocio, solo se le da una segunda entrada además de la CLI.
- **Autorización:** requiere `require_admin` (RF-R1-07) + CSRF (`require_csrf`, mismo patrón que el resto de `/api/admin/*`).
- **Diferencia con `sessions-revoke` de la CLI:** el endpoint HTTP también debería registrar auditoría, pero con `actor` distinto — `f"user:{admin.id}"` (siguiendo el formato ya documentado en `app/models/audit_log.py`: `"user:<id>"` o `"cli"`), no `actor="cli"`. Esto implica que `revoke_sessions` necesita aceptar el `actor` como parámetro en vez de tenerlo hardcodeado, o bien duplicar el registro de auditoría en el endpoint — a decidir al implementar, documentando la elección aquí si cambia.
- **Usuario inexistente:** 404, igual que el resto de endpoints admin (`admin_topics`/`admin_trips`).
- **No revoca la sesión del propio admin que hace la petición si coincide con el username objetivo** — es un caso borde poco probable (un admin revocándose a sí mismo desde el panel) pero no hay que impedirlo explícitamente: si un admin se revoca a sí mismo, su próxima petición devolverá 401 igual que cualquier sesión revocada, sin necesitar lógica especial.
- **Fuera de alcance:** UI del panel que llame a este endpoint (WP-R1-5), vista de sesiones activas por usuario (no lo pide RF-R1-06, solo "revocación de todas").

## Definition of Done

- [ ] Código con docstring `Implementa: RF-R1-06` en los módulos que materializan el requisito
- [ ] Tests con `@pytest.mark.spec("RF-R1-06")`: revoca sesiones activas de otro usuario, requiere rol admin (403 para lector), requiere CSRF, usuario inexistente devuelve 404, queda registrado en `audit_log` — contra PostgreSQL real
- [ ] Cobertura ≥ 80 % en el código tocado
- [ ] Revisión de seguridad (checklist OWASP)
- [ ] `python tools/traceability.py --check` en verde
- [ ] Commits con prefijo `[TASK-R1-014]`
