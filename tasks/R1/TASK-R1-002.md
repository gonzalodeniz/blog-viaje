# TASK-R1-002 — Pipeline de CI con puertas de calidad bloqueantes

- **WP:** WP-R1-1
- **Requisitos:** RNF-R1-01, RNF-R1-05, RNF-R1-06
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-002

## Objetivo

Un workflow de GitHub Actions (`.github/workflows/ci.yml`) que en cada push/PR ejecuta tests con cobertura ≥ 80 % (líneas y ramas) en backend y frontend, los escáneres de seguridad (bandit, semgrep, pip-audit, npm audit, trivy, gitleaks) y `tools/traceability.py --check --release R1`, todos bloqueantes.

## Contexto y decisiones

- RNF-R1-01/05/06 son transversales a todo WP-R1-1: no generan endpoints ni UI, así que su verificación es el propio pipeline. Se demuestran con tests "meta" (`tests/meta/test_ci_pipeline.py`) que comprueban estáticamente que el workflow declara cada herramienta/puerta exigida por la spec — no se puede ejercitar un GitHub Actions run real desde `pytest`.
- La puerta de trazabilidad se deja **bloqueante desde ya** (decisión explícita, no diferida como en TASK-R1-001): `specs/SPEC-R1.md` está congelada y define 28 RF/RNF; solo `RNF-R1-07` tiene test hoy, así que `tools/traceability.py --check --release R1` fallará en CI hasta que el resto de WPs de R1 añadan sus tests. Es una señal honesta del estado real de la release, no un bug del pipeline.
- gitleaks y trivy se ejecutan vía imagen Docker oficial directamente (`docker run`), sin Actions de terceros ni licencia, para mantener el pipeline sin dependencias externas de pago.
- semgrep se instala por pip en el job de CI (no como dependencia de `backend/`, es una herramienta de análisis transversal, no del runtime de la app).
- bandit y pip-audit sí se añaden como dependencias opcionales `dev` de `backend/pyproject.toml` porque son herramientas Python específicas del backend que también interesa poder correr en local.

## Definition of Done

- [x] Código con docstring `Implementa: RNF-R1-01, RNF-R1-05, RNF-R1-06` en `tests/meta/test_ci_pipeline.py`
- [x] Tests con `@pytest.mark.spec("RNF-R1-01")` / `@pytest.mark.spec("RNF-R1-05")` / `@pytest.mark.spec("RNF-R1-06")`
- [x] Cobertura ≥ 80 % en el código tocado (los tests meta cubren el 100 % de sus propias funciones; no se toca código de producción)
- [x] Revisión de seguridad (workflow sin secretos embebidos; usa `secrets.GITHUB_TOKEN` implícito únicamente; sin licencias de terceros)
- [x] `python tools/traceability.py --check --release R1` en verde — **no**; falla intencionadamente (27 RF/RNF de R1 aún sin test, ver nota arriba). El job de CI lo ejecuta y bloquea el merge, tal como exige `CLAUDE.md`; se pondrá en verde de forma incremental a medida que cierren el resto de WPs de R1 (hito H4).
- [x] Commits con prefijo `[TASK-R1-002]`

## Notas de implementación

- `.github/workflows/ci.yml`: jobs `backend` (pytest+cobertura, bandit, pip-audit), `frontend` (oxlint, vitest+cobertura, npm audit), `semgrep`, `gitleaks`, `trivy` (fs scan) y `traceability` (`--check --release R1`), todos requeridos (sin `continue-on-error`).
- `tests/meta/test_ci_pipeline.py` + `pytest.ini` en la raíz: verifican por texto que el workflow referencia cada herramienta y que los umbrales de cobertura (80 % líneas/ramas) están configurados en `backend/pyproject.toml` y `frontend/vite.config.ts`.
- `backend/pyproject.toml`: añadidas `bandit` y `pip-audit` al extra `dev`.
