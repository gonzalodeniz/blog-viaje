# Bitácora

Blog de viajes personal, autoalojado y **privado por defecto**: la portada pública es un collage de fotos elegidas explícitamente como públicas y todo lo demás exige autenticación. Textos ricos, muchas fotografías y sencillez operativa (`docker compose up -d`).

**Estado:** fase de especificación. La release R1 «Cimientos» está especificada y planificada; la implementación no ha comenzado.

## Metodología

Spec Driven Development por releases: los requisitos (`specs/`), la planificación (`plan/`) y las tareas (`tasks/`) están versionados y enlazados por IDs estables, con trazabilidad bidireccional requisito ↔ tarea ↔ commit ↔ test verificada en CI (`tools/traceability.py`). Empieza por [specs/SPEC-MASTER.md](specs/SPEC-MASTER.md).

| Carpeta | Contenido |
|---|---|
| `specs/` | Qué se construye: SPEC-MASTER, SPEC-R1/R2/R3, ADRs |
| `plan/` | Cómo y cuándo: paquetes de trabajo por release |
| `tasks/` | Trabajo ejecutable, una tarea por fichero |
| `tools/` | Trazabilidad y hooks de git |
| `backend/` · `frontend/` · `deploy/` · `tests/e2e/` | Implementación (pendiente, ver TASK-R1-001) |
| `docs/` | Artefactos generados (matriz de trazabilidad) |

## Releases

| Release | Nombre | Resultado |
|---|---|---|
| R1 | Cimientos | Blog funcional privado: autenticación con bloqueo y CLI de rescate, editor rico, lectura |
| R2 | Fotografía | Pipeline de imágenes, collage público, lightbox, biblioteca de fotos |
| R3 | Descubrimiento | Búsqueda full-text en español, filtros, archivo, PWA, backups y observabilidad |

## Desarrollo

```bash
git config core.hooksPath tools/hooks     # commits con prefijo [TASK-Rn-nnn] obligatorio
python tools/traceability.py --check      # valida la trazabilidad
```

Convenciones completas en [CLAUDE.md](CLAUDE.md) y SPEC-MASTER §3.
