# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

**Bitácora**: blog de viajes personal autoalojado, privado por defecto (login obligatorio salvo fotos marcadas públicas). Se desarrolla con **Spec Driven Development por releases**: el código se deriva de especificaciones versionadas y todo cambio es trazable en ambos sentidos entre requisito ↔ tarea ↔ commit ↔ test.

- Idioma: documentación, specs y UI en **español**; identificadores de código en inglés.
- Stack (ADR-001): FastAPI + SQLAlchemy 2 + Alembic (backend), React 18 + Vite + TS + TipTap (frontend), PostgreSQL 16, libvips, nginx + certbot, Docker Compose. Worker de imágenes con cola en PostgreSQL (sin Redis).

## Flujo SDD — leer antes de implementar nada

1. El **qué** vive en `specs/SPEC-Rn.md` (requisitos `RF-Rn-nn` / `RNF-Rn-nn`); la visión completa en `specs/SPEC-MASTER.md`. Las specs congeladas no se editan sin subir versión y anotar changelog.
2. El **cómo** vive en `plan/PLAN-Rn.md` (paquetes `WP-Rn-n`).
3. El trabajo ejecutable vive en `tasks/Rn/TASK-Rn-nnn.md` (plantilla en `tasks/TEMPLATE.md`). Toda implementación debe partir de una TASK existente; si no la hay, créala primero referenciando su WP y sus RF/RNF.
4. Decisiones de arquitectura: `specs/adr/` (inmutables; se sustituyen con un ADR nuevo).

## Trazabilidad (obligatoria, verificada en CI)

- **Commits:** prefijo `[TASK-Rn-nnn] ` obligatorio. Excepción `[SDD] ` solo para commits que únicamente tocan `specs/`, `plan/`, `tasks/`, `docs/`, `tools/`. Hook: `git config core.hooksPath tools/hooks`.
- **Código:** módulos/funciones que materializan un requisito lo declaran en su docstring: `"""Implementa: RF-R1-03, RNF-R1-02."""`
- **Tests backend:** `@pytest.mark.spec("RF-R1-03")`.
- **Tests e2e:** `test.info().annotations.push({ type: "spec", description: "RF-R1-03" })`.
- **Verificación:** `python tools/traceability.py --check --release R1` — regenera `docs/TRACEABILITY.md` (no editarlo a mano) y falla si hay requisitos sin test, tareas cerradas sin commits o commits sin tarea.
- Ramas: `feature/TASK-Rn-nnn`.

## Comandos

```bash
python tools/traceability.py --check    # matriz de trazabilidad + validación
git config core.hooksPath tools/hooks   # activar hook de commit (una vez por clon)
```

`backend/` y `frontend/` aún no están inicializados (TASK-R1-001). Cuando existan, añadir aquí sus comandos de test/lint/build.

## Puertas de calidad (todas bloqueantes en CI)

- Cobertura ≥ 80 % de líneas **y ramas** por paquete (backend y frontend).
- Seguridad: bandit, semgrep, pip-audit/npm audit, trivy, gitleaks — sin hallazgos altos/críticos. Desarrollo bajo OWASP Top 10 / ASVS L2.
- Trazabilidad completa (ver arriba).

## Reglas de seguridad no negociables del producto

- Privado por defecto: cualquier endpoint o imagen nuevos requieren autenticación salvo que un RF diga lo contrario; la autorización de fotos privadas se comprueba en cada petición.
- Los mensajes de login nunca revelan si un usuario existe (RF-R1-04).
- El HTML del editor siempre se sanitiza en servidor con lista blanca (RF-R1-18); nunca `dangerouslySetInnerHTML` sin sanitizar.
- Logs sin contraseñas, tokens ni cookies (RNF-R1-08). Sin secretos en el repo (usar `.env`, nunca comitearlo).
- Los originales de fotos en `media/originals/` no se modifican ni se sirven jamás; solo se sirven variantes de `derived/`.
- La CLI de rescate (`bitacora-cli`) nunca se expone por HTTP.
