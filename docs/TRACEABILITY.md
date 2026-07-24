# Matriz de trazabilidad

**Generado por `tools/traceability.py` — no editar a mano.**

## R1

| Requisito | WP | Tareas | Commits | Código | Tests |
|---|---|---|---|---|---|
| RF-R1-01 | WP-R1-2 | TASK-R1-007, TASK-R1-008 | 1e30691, a3cb88a, b94ca9b, 635a4bd | backend/app/api/auth.py, backend/app/api/deps.py, backend/app/models/user.py, backend/app/services/auth.py, backend/tests/test_api_auth.py, backend/tests/test_auth_service.py | backend/tests/test_api_auth.py, backend/tests/test_api_trips.py, backend/tests/test_auth_service.py |
| RF-R1-02 | WP-R1-2 | TASK-R1-007, TASK-R1-016 | 1e30691, a3cb88a | backend/app/api/auth.py, backend/app/models/session.py, backend/app/models/user.py, backend/app/services/auth.py, backend/tests/test_api_auth.py, backend/tests/test_auth_service.py | backend/tests/test_api_auth.py, backend/tests/test_auth_service.py |
| RF-R1-03 | WP-R1-2 | TASK-R1-007, TASK-R1-012, TASK-R1-013 | 1e30691, a3cb88a | — | — |
| RF-R1-04 | WP-R1-2 | TASK-R1-007, TASK-R1-012, TASK-R1-015 | 1e30691, a3cb88a | backend/app/api/auth.py, backend/app/services/auth.py, backend/tests/test_api_auth.py, backend/tests/test_auth_service.py | backend/tests/test_api_auth.py, backend/tests/test_auth_service.py |
| RF-R1-05 | WP-R1-2, WP-R1-5 | TASK-R1-007, TASK-R1-012, TASK-R1-013 | 1e30691, a3cb88a | — | — |
| RF-R1-06 | WP-R1-2, WP-R1-5 | TASK-R1-007, TASK-R1-009, TASK-R1-014 | 1e30691, a3cb88a, 361a3c7, 388a392 | — | — |
| RF-R1-07 | WP-R1-2 | TASK-R1-007, TASK-R1-008, TASK-R1-013, TASK-R1-014 | 1e30691, a3cb88a, b94ca9b, 635a4bd | backend/app/api/deps.py | backend/tests/test_api_admin_photos.py, backend/tests/test_api_admin_topics.py, backend/tests/test_api_admin_trips.py |
| RF-R1-08 | WP-R1-3 | — | — | — | — |
| RF-R1-09 | WP-R1-3 | — | — | — | — |
| RF-R1-10 | WP-R1-3 | TASK-R1-007 | 1e30691, a3cb88a | — | — |
| RF-R1-11 | WP-R1-3 | — | — | — | — |
| RF-R1-12 | WP-R1-3 | TASK-R1-009 | 361a3c7, 388a392 | — | — |
| RF-R1-13 | WP-R1-4, WP-R1-6 | TASK-R1-005, TASK-R1-008 | e1e3299, 7563c2f, b94ca9b, 635a4bd | backend/app/api/trips.py, backend/app/models/trip.py, backend/tests/test_api_trips.py, backend/tests/test_models.py | backend/tests/test_api_trips.py, backend/tests/test_models.py |
| RF-R1-14 | WP-R1-4, WP-R1-6 | TASK-R1-005, TASK-R1-008, TASK-R1-010 | e1e3299, 7563c2f, b94ca9b, 635a4bd, 2bd830d, 586befc | backend/app/api/admin_photos.py, backend/app/api/photos.py, backend/app/api/trips.py, backend/app/models/photo.py, backend/app/models/trip.py, backend/app/services/photo_storage.py, backend/tests/test_api_admin_photos.py, backend/tests/test_api_photos.py, backend/tests/test_api_trips.py, backend/tests/test_models.py, backend/tests/test_photo_storage.py | backend/tests/test_api_admin_photos.py, backend/tests/test_api_photos.py, backend/tests/test_api_trips.py, backend/tests/test_models.py |
| RF-R1-15 | WP-R1-4, WP-R1-5 | TASK-R1-005, TASK-R1-008, TASK-R1-009, TASK-R1-010, TASK-R1-013 | e1e3299, 7563c2f, b94ca9b, 635a4bd, 361a3c7, 388a392, 2bd830d, 586befc | backend/app/api/admin_photos.py, backend/app/api/admin_trips.py, backend/app/models/audit_log.py, backend/app/models/photo.py, backend/app/models/tag.py, backend/app/models/trip.py, backend/app/services/photo_storage.py, backend/tests/test_api_admin_photos.py, backend/tests/test_api_admin_trips.py, backend/tests/test_models.py, backend/tests/test_photo_storage.py | backend/tests/test_api_admin_photos.py, backend/tests/test_api_admin_trips.py, backend/tests/test_models.py, backend/tests/test_photo_storage.py |
| RF-R1-16 | WP-R1-4, WP-R1-5 | TASK-R1-005, TASK-R1-009, TASK-R1-013 | e1e3299, 7563c2f, 361a3c7, 388a392 | backend/app/api/admin_topics.py, backend/app/models/audit_log.py, backend/app/models/topic.py, backend/tests/test_api_admin_topics.py, backend/tests/test_models.py | backend/tests/test_api_admin_topics.py, backend/tests/test_models.py |
| RF-R1-17 | WP-R1-5 | TASK-R1-006 | ff36b54, 00d86fc | — | — |
| RF-R1-18 | WP-R1-4, WP-R1-5 | TASK-R1-005, TASK-R1-006, TASK-R1-009 | e1e3299, 7563c2f, ff36b54, 00d86fc, 361a3c7, 388a392 | backend/app/api/admin_trips.py, backend/app/models/trip.py, backend/app/services/html_sanitizer.py, backend/tests/test_api_admin_trips.py, backend/tests/test_html_sanitizer.py, backend/tests/test_models.py | backend/tests/test_api_admin_trips.py, backend/tests/test_html_sanitizer.py |
| RF-R1-19 | WP-R1-5 | — | — | — | — |
| RF-R1-20 | WP-R1-2 | TASK-R1-007, TASK-R1-015 | 1e30691, a3cb88a | — | — |
| RNF-R1-01 | WP-R1-1 | TASK-R1-002 | 9b515b4 | — | tests/meta/test_ci_pipeline.py |
| RNF-R1-02 | WP-R1-2 | TASK-R1-007 | 1e30691, a3cb88a | backend/app/core/security.py, backend/tests/test_security.py | backend/tests/test_security.py |
| RNF-R1-03 | WP-R1-1, WP-R1-2 | TASK-R1-003, TASK-R1-006, TASK-R1-007 | d9417e0, ff36b54, 00d86fc, 1e30691, a3cb88a | backend/app/api/auth.py, backend/app/api/deps.py, backend/app/core/csrf.py, backend/tests/test_api_auth.py, backend/tests/test_csrf.py | backend/tests/test_api_auth.py, backend/tests/test_csrf.py |
| RNF-R1-04 | WP-R1-1 | TASK-R1-003, TASK-R1-004 | d9417e0, 49c9646, b8503d2, 311267a | — | — |
| RNF-R1-05 | WP-R1-1 | TASK-R1-002 | 9b515b4 | — | tests/meta/test_ci_pipeline.py |
| RNF-R1-06 | WP-R1-1 | TASK-R1-002 | 9b515b4 | tools/traceability.py | tests/meta/test_ci_pipeline.py |
| RNF-R1-07 | WP-R1-1 | TASK-R1-001, TASK-R1-002, TASK-R1-004 | 8a4073b, 9b515b4, 49c9646, b8503d2, 311267a | backend/app/api/health.py | backend/tests/test_cli.py, backend/tests/test_config.py, backend/tests/test_db.py, backend/tests/test_health.py |
| RNF-R1-08 | WP-R1-2 | TASK-R1-007, TASK-R1-012, TASK-R1-016 | 1e30691, a3cb88a | — | — |

## R2

| Requisito | WP | Tareas | Commits | Código | Tests |
|---|---|---|---|---|---|
| RF-R2-01 | — | — | — | — | — |
| RF-R2-02 | — | — | — | — | — |
| RF-R2-03 | — | — | — | — | — |
| RF-R2-04 | — | — | — | — | — |
| RF-R2-05 | — | — | — | — | — |
| RF-R2-06 | — | — | — | — | — |
| RF-R2-07 | — | — | — | — | — |
| RF-R2-08 | — | — | — | — | — |
| RF-R2-09 | — | — | — | — | — |
| RF-R2-10 | — | TASK-R1-010 | 2bd830d, 586befc | — | — |
| RF-R2-11 | — | TASK-R1-010 | 2bd830d, 586befc | — | — |
| RF-R2-12 | — | TASK-R1-010, TASK-R1-016 | 2bd830d, 586befc | — | — |
| RF-R2-13 | — | TASK-R1-010 | 2bd830d, 586befc | — | — |
| RF-R2-14 | — | TASK-R1-010 | 2bd830d, 586befc | — | — |
| RF-R2-15 | — | — | — | — | — |
| RNF-R2-01 | — | — | — | — | — |
| RNF-R2-02 | — | TASK-R1-008, TASK-R1-010 | b94ca9b, 635a4bd, 2bd830d, 586befc | — | — |

## R3

| Requisito | WP | Tareas | Commits | Código | Tests |
|---|---|---|---|---|---|
| RF-R3-01 | — | TASK-R1-008 | b94ca9b, 635a4bd | — | — |
| RF-R3-02 | — | — | — | — | — |
| RF-R3-03 | — | — | — | — | — |
| RF-R3-04 | — | — | — | — | — |
| RNF-R3-01 | — | — | — | — | — |
| RNF-R3-02 | — | — | — | — | — |
| RNF-R3-03 | — | — | — | — | — |
| RNF-R3-04 | — | — | — | — | — |

## Commits sin tarea

- `6624336 Initial commit`
