# TASK-R1-013 — Corregir trazabilidad de RF-R1-07 (roles): ya implementado, mal etiquetado

- **WP:** WP-R1-2
- **Requisitos:** RF-R1-07
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-013

## Objetivo

`RF-R1-07` deja de aparecer como hueco en `docs/TRACEABILITY.md`. No hace falta escribir ninguna funcionalidad nueva: `app.api.deps.require_admin` ya comprueba `role == "admin"` desde TASK-R1-007/008 y los tres routers admin (`admin_topics`, `admin_trips`, `admin_photos`) ya tienen un test que verifica el 403 con rol `lector` — simplemente ninguno llevaba el marker `@pytest.mark.spec("RF-R1-07")`, así que `tools/traceability.py --check` no los veía.

## Contexto y decisiones

- **Cómo se descubrió:** al planificar TASK-R1-011 se asumió (incorrectamente, en la conversación con el usuario) que RF-R1-07 era funcionalidad pendiente de WP-R1-2, al mismo nivel que el bloqueo (RF-R1-03) o el registro de intentos (RF-R1-05). Revisando el código antes de crear esa tarea se vio que `require_admin` (`backend/app/api/deps.py`) ya hace exactamente lo que pide RF-R1-07, y que `test_crear_tema_sin_rol_admin_devuelve_403`, `test_crear_viaje_sin_rol_admin_devuelve_403` y `test_subir_foto_sin_rol_admin_devuelve_403` ya lo cubren — solo estaban marcados con el RF principal de cada fichero (RF-R1-16, RF-R1-15) en vez de (además) con RF-R1-07.
- **Cambio:** añadir `@pytest.mark.spec("RF-R1-07")` a esos tres tests (no se quita el marker existente: cada test verifica dos cosas a la vez — el CRUD del recurso y el control de acceso por rol — así que le corresponden ambos RF) y añadir `RF-R1-07` al docstring `Implementa:` de `app/api/deps.py`.
- **Por qué no hace falta más:** RF-R1-07 son dos frases — "roles admin/lector" (ya existe la columna y `require_admin` desde hace varias tareas) y "el primer usuario creado es admin" (ya lo decide quien ejecuta `bitacora-cli create-user`, es una decisión operativa del primer despliegue, no algo que el sistema deba inferir automáticamente; SPEC-R1 no pide que se infiera). No hay código de producción que cambiar.
- **Fuera de alcance:** cualquier UI que oculte acciones de escritura para `lector` (WP-R1-5) — el backend ya deniega con 403 aunque el frontend mostrara el botón.

## Definition of Done

- [x] Código con docstring `Implementa: RF-R1-07` (añadido a `app/api/deps.py`, junto a los RF que ya tenía)
- [x] Tests con `@pytest.mark.spec("RF-R1-07")` en los tres tests de 403 por rol ya existentes (`test_api_admin_topics.py`, `test_api_admin_trips.py`, `test_api_admin_photos.py`)
- [x] Cobertura ≥ 80 % (sin cambios de comportamiento, no aplica cobertura nueva)
- [x] Revisión de seguridad: no aplica (sin cambio de comportamiento; el control de acceso ya estaba en producción, solo se corrige su trazabilidad)
- [ ] `python tools/traceability.py --check` en verde para RF-R1-07 específicamente (el comando global sigue en rojo por el resto de huecos de WP-R1-2/WP-R1-5, ver TASK-R1-011)
- [ ] Commits con prefijo `[TASK-R1-013]`
