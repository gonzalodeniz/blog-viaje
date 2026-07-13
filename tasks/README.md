# Tareas

Trabajo ejecutable, una tarea por fichero, agrupadas por release (`R1/`, `R2/`, …). Cada tarea se crea a partir de [TEMPLATE.md](TEMPLATE.md) cuando su WP entra en ejecución — no se generan todas por adelantado.

Reglas:

- El nombre del fichero es el ID: `TASK-R1-014.md`. Los números son consecutivos dentro de la release y no se reutilizan.
- Toda tarea referencia su WP (de `plan/PLAN-Rn.md`) y los RF/RNF que desarrolla (de `specs/SPEC-Rn.md`).
- El campo **Estado** (`pendiente` / `en curso` / `cerrada`) lo lee `tools/traceability.py`: una tarea `cerrada` sin commits `[TASK-…]` asociados hace fallar la CI.
- Rama de trabajo: `feature/TASK-Rn-nnn`; los commits llevan el prefijo `[TASK-Rn-nnn]`.
